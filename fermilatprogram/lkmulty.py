import os 
import numpy as np
from fermipy.gtanalysis import GTAnalysis
import astropy.io.fits as pyfits
import matplotlib.pyplot as plt
import pandas as pd
import threading
import concurrent.futures
from queue import Queue
import time
from datetime import datetime
import logging
import argparse
import sys
from astropy.coordinates import SkyCoord
import astropy.units as u
from Generate_gconfig import parse_grb_info as parse_grb_info_from_module
# 导入photon_analyzer模块中的函数
from photon_analyzer import find_highest_prob_photon, save_all_photons
from cleandir import clean_results_directory
from Generate_gconfig import create_config
# 配置参数
BASE_DIR = "/home/mxr/lee/data/fermilat"
TEMPLATE_CONFIG = "/home/mxr/lee/config.yaml"  # 标准配置文件模板
GRB_DATA_DIR = os.path.join(BASE_DIR, "grb_data")
RESULTS_DIR = os.path.join(BASE_DIR, "resultsPL")

# 多线程配置
MAX_WORKERS = 4  # 最大并行线程数
THREAD_TIMEOUT = 3600  # 单个任务超时时间（秒）

# 设置多线程日志
def setup_logging():
    """设置多线程安全的日志系统"""
    log_format = '%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(os.path.join(RESULTS_DIR, 'analysis.log')),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# 线程安全的结果收集器
class ResultCollector:
    def __init__(self):
        self._lock = threading.Lock()
        self._results = {}
        self._errors = {}
    
    def add_result(self, grb_name, result):
        with self._lock:
            self._results[grb_name] = result
            logger.info(f"✅ {grb_name} 分析完成")
    
    def add_error(self, grb_name, error):
        with self._lock:
            self._errors[grb_name] = str(error)
            logger.error(f"❌ {grb_name} 分析失败: {error}")
    
    def get_results(self):
        with self._lock:
            return self._results.copy(), self._errors.copy()
    
    def get_summary(self):
        with self._lock:
            return len(self._results), len(self._errors)

def parse_grb_info(grb_dir):
    """解析GRB信息文件（调用Generate_gconfig模块）"""
    grb_name = os.path.basename(grb_dir)
    return parse_grb_info_from_module(grb_name, RESULTS_DIR)

def analyze_grb_worker(grb_name, result_collector):
    """执行单个GRB的分析流程（线程安全版本）"""
    thread_id = threading.current_thread().name
    start_time = time.time()
    
    try:
        logger.info(f"[{thread_id}] {'='*40}")
        logger.info(f"[{thread_id}] 开始分析: {grb_name}")
        logger.info(f"[{thread_id}] {'='*40}")
        
        grb_params = parse_grb_info(os.path.join(GRB_DATA_DIR, grb_name))

        config_path = os.path.join(RESULTS_DIR, grb_name, "config.yaml")
        # 3. 设置分析环境
        try:
            gta = GTAnalysis(config_path, logging={'verbosity': 1})  # 降低日志级别避免冲突
            gta.setup()
            logger.info(f"[{thread_id}] {grb_name} FermiPy 环境初始化成功")
        except Exception as e:
            raise Exception(f"初始化失败: {str(e)}")
        
        # 5. 打印初始ROI模型
        try:
            gta.print_roi()
            logger.info(f"[{thread_id}] {grb_name} ROI模型打印完成")
        except Exception as e:
            logger.warning(f"[{thread_id}] {grb_name} 打印ROI失败: {str(e)}")
        
        # 6. 设置拟合参数
        try:
            # 释放附近源
            gta.optimize()
            gta.free_sources(distance=2.5, pars='norm')
            
            # 释放弥散背景
            gta.free_source('galdiff')
            gta.free_source('isodiff')
            
            # 释放目标GRB
            gta.free_source(grb_name)
            logger.info(f"[{thread_id}] {grb_name} 拟合参数设置完成")
        except Exception as e:
            logger.warning(f"[{thread_id}] {grb_name} 设置拟合参数失败: {str(e)}")
        
        # 7. 执行拟合
        try:
            fit_results = gta.fit()
            logger.info(f"[{thread_id}] {grb_name} 拟合结果:")
            logger.info(f"[{thread_id}] {grb_name} Fit Quality: {fit_results['fit_quality']}")
            logger.info(f"[{thread_id}] {grb_name} 目标源信息: {gta.roi[grb_name]}")
            
        except Exception as e:
            raise Exception(f"拟合失败: {str(e)}")
        # 8. TSMAP and residmap
        output_base = os.path.join(RESULTS_DIR, grb_name, "fit0")
        gta.write_roi(output_base, make_plots=True)
        fit_npy_path = os.path.join(RESULTS_DIR, grb_name, "fit0.npy")
        try:
            c = np.load(fit_npy_path, allow_pickle=True).flat[0]
        except Exception as e:
            logger.warning(f"[{thread_id}] {grb_name} 加载拟合结果npy失败: {str(e)}")

        # 8. 执行SED分析
        try:
            from sed_plotter import plot_sed, save_sed_plot
            # 绘制SED图像
            sed = gta.sed(f'{grb_name}',loge_bins=np.linspace(2, 5, num=6),use_local_index=True)
            plot_sed(c, sed, f'{grb_name}')
            # 保存图像到各个GRB分析文件夹
            grb_result_dir = os.path.join(RESULTS_DIR, grb_name)
            sed_image_path = os.path.join(grb_result_dir, f'{grb_name}_sed.png')
            save_sed_plot(c, sed, f'{grb_name}', sed_image_path)
        except Exception as e:
            logger.warning(f"[{thread_id}] {grb_name} SED分析失败: {str(e)}")

        # 9. 获取最高能高概率光子信息（在拟合后进行）
        highest_photon = find_highest_prob_photon(gta, grb_name, grb_params, RESULTS_DIR)
        # 10. 保存拟合结果（包含最高能光子信息和分析摘要）
        if fit_results:
            try:
                result_path = os.path.join(RESULTS_DIR, grb_name, f"{grb_name}_fit_results.txt")
                analysis_time = time.time() - start_time
                
                with open(result_path, 'w') as f:
                    f.write(f"GRB Analysis Results for {grb_name}\n")
                    f.write("="*50 + "\n")
                    f.write(f"分析目录: {BASE_DIR}\n")
                    f.write(f"分析时间: {pd.Timestamp.now()}\n")
                    f.write(f"分析耗时: {analysis_time:.2f}s\n")
                    f.write("\n")
                    
                    # 添加GRB基本参数信息（包含T0, T1）
                    f.write("GRB Parameters:\n")
                    f.write("-"*20 + "\n")
                    f.write(f"RA: {grb_params['ra']:.4f} deg\n")
                    f.write(f"Dec: {grb_params['dec']:.4f} deg\n")
                    f.write(f"Trigger MET: {grb_params['trigger_met']:.2f} s\n")
                    f.write(f"T0: {grb_params['T0']:.2f} s\n")
                    f.write(f"T1: {grb_params['T1']:.2f} s\n")
                    f.write(f"Time Range (tmin-tmax): {grb_params['tmin']:.2f} - {grb_params['tmax']:.2f} s\n")
                    if 'PIndex' in grb_params:
                        f.write(f"PIndex: {grb_params['PIndex']}\n")
                    f.write("\n")
                    
                    # 添加拟合结果信息
                    f.write("Fit Results:\n")
                    f.write("-"*20 + "\n")
                    f.write(f"Fit Quality: {fit_results['fit_quality']}\n")
                    f.write(f"Log-Likelihood: {fit_results['loglike']:.2f}\n")
                    f.write(f"Target Source: {gta.roi[grb_name]}\n\n")
                                       
                    # 添加最高能高概率光子信息
                    f.write("Highest Energy Photon Analysis:\n")
                    f.write("-"*30 + "\n")
                    if highest_photon:
                        f.write("Highest Energy Photon (Probability > 0.9):\n")
                        f.write(f"  Energy: {highest_photon['energy']:.2f} MeV\n")
                        f.write(f"  Probability: {highest_photon['probability']:.4f}\n")
                        f.write(f"  Time (MET): {highest_photon['time']:.2f} s\n")
                        f.write(f"  Relative Time: {highest_photon['relative_time']:.2f} s\n")
                        f.write(f"  RA: {highest_photon['ra']:.4f} deg\n")
                        f.write(f"  Dec: {highest_photon['dec']:.4f} deg\n")
                        f.write(f"  Angular Separation: {highest_photon['angular_separation']:.4f} deg\n")
                        f.write(f"  Total High Prob Photons: {highest_photon['total_high_prob_photons']}\n")
                        f.write(f"  Event Class: {highest_photon['event_class']}\n")
                        f.write(f"  Event Type: {highest_photon['event_type']}\n")
                    else:
                        f.write("Highest Energy Photon: Not found with probability > 0.9\n")
                    
                    f.write("\n")
                    f.write("="*50 + "\n")
                    f.write(f"Analysis completed at: {pd.Timestamp.now()}\n")
                
                logger.info(f"[{thread_id}] {grb_name} 拟合结果已保存: {result_path}")
                
                # 将最高能光子信息添加到返回结果中
                if highest_photon:
                    fit_results['highest_photon'] = highest_photon
                    
            except Exception as e:
                logger.warning(f"[{thread_id}] {grb_name} 保存拟合结果失败: {str(e)}")
        
        # 11. 保存最终模型和图表
        try:
            output_base = os.path.join(RESULTS_DIR, grb_name, "final_model")
            gta.write_roi(output_base, make_plots=True)
            logger.info(f"[{thread_id}] {grb_name} 最终模型和图表已保存: {output_base}.*")
        except Exception as e:
            logger.warning(f"[{thread_id}] {grb_name} 保存最终模型失败: {str(e)}")
        
        # 收集结果
        if fit_results:
            analysis_result = {
                'fit_results': fit_results,
                'grb_params': grb_params,
                'analysis_time': time.time() - start_time
            }
            result_collector.add_result(grb_name, analysis_result)
        else:
            result_collector.add_error(grb_name, "拟合失败")
    
    except Exception as e:
        result_collector.add_error(grb_name, str(e))
        logger.error(f"[{thread_id}] {grb_name} 分析异常: {str(e)}")

def get_grb_list():
    """获取待分析的GRB列表"""
    grb_dirs = [d for d in os.listdir(GRB_DATA_DIR) 
                if os.path.isdir(os.path.join(GRB_DATA_DIR, d))
                and d.startswith('GRB')]
    return grb_dirs

def analyze_grb_multithread(grb_list=None, max_workers=MAX_WORKERS):
    """多线程分析多个GRB"""
    
    if grb_list is None:
        grb_list = get_grb_list()
    
    if not grb_list:
        logger.warning("未找到待分析的GRB文件")
        return None, None
    
    logger.info(f"🎯 准备分析 {len(grb_list)} 个GRB文件")
    logger.info(f"📋 GRB列表: {', '.join(grb_list)}")
    logger.info(f"🔧 使用 {max_workers} 个线程")
    
    result_collector = ResultCollector()
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers, 
                                               thread_name_prefix="GRB-Worker") as executor:
        
        future_to_grb = {}
        for grb_name in grb_list:
            future = executor.submit(analyze_grb_worker, grb_name, result_collector)
            future_to_grb[future] = grb_name
        
        completed = 0
        total = len(grb_list)
        
        for future in concurrent.futures.as_completed(future_to_grb, timeout=THREAD_TIMEOUT):
            grb_name = future_to_grb[future]
            completed += 1
            
            try:
                future.result()
                success_count, error_count = result_collector.get_summary()
                logger.info(f"📊 进度: {completed}/{total} | 成功: {success_count} | 失败: {error_count}")
                
            except concurrent.futures.TimeoutError:
                logger.error(f"⏰ {grb_name} 分析超时")
                result_collector.add_error(grb_name, "分析超时")
            except Exception as e:
                logger.error(f"💥 {grb_name} 线程异常: {str(e)}")
    
    results, errors = result_collector.get_results()
    total_time = time.time() - start_time
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🎉 多线程分析完成!")
    logger.info(f"⏱️  总耗时: {total_time:.2f} 秒")
    logger.info(f"✅ 成功: {len(results)} 个")
    logger.info(f"❌ 失败: {len(errors)} 个")
    
    if errors:
        logger.info(f"\n失败的GRB:")
        for grb_name, error in errors.items():
            logger.info(f"  - {grb_name}: {error}")
    
    logger.info(f"{'='*60}")
    
    return results, errors

# =====================
# 主程序
# =====================

def analyze_single_grb(grb_name):
    """分析单个指定的GRB事件"""
    logger.info(f"🎯 开始分析单个GRB: {grb_name}")
    
    # 检查GRB是否存在
    grb_path = os.path.join(GRB_DATA_DIR, grb_name)
    if not os.path.exists(grb_path):
        logger.error(f"❌ GRB目录不存在: {grb_path}")
        available_grbs = get_grb_list()
        if available_grbs:
            logger.info(f"📋 可用的GRB列表: {', '.join(available_grbs)}")
        return None, {grb_name: "GRB目录不存在"}
    
    # 创建结果收集器
    result_collector = ResultCollector()
    start_time = time.time()
    
    # 执行分析
    analyze_grb_worker(grb_name, result_collector)
    
    # 获取结果
    results, errors = result_collector.get_results()
    total_time = time.time() - start_time
    
    # 输出结果摘要
    logger.info(f"\n{'='*60}")
    logger.info(f"🎉 单个GRB分析完成!")
    logger.info(f"⏱️  总耗时: {total_time:.2f} 秒")
    if results:
        logger.info(f"✅ 分析成功: {grb_name}")
    if errors:
        logger.info(f"❌ 分析失败: {grb_name} - {errors[grb_name]}")
    logger.info(f"{'='*60}")
    
    return results, errors

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='GRB数据分析工具 - 支持多线程批量分析或单个GRB分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""使用示例:
  python lkmulty.py                    # 分析所有GRB（多线程）
  python lkmulty.py --grb GRB090510    # 分析指定的单个GRB
  python lkmulty.py --list             # 列出所有可用的GRB
  python lkmulty.py --workers 8        # 使用8个线程进行批量分析"""
    )
    
    parser.add_argument(
        '--grb', 
        type=str, 
        help='指定要分析的单个GRB事件名称（例如：GRB090510）'
    )
    
    parser.add_argument(
        '--list', 
        action='store_true', 
        help='列出所有可用的GRB事件'
    )
    
    parser.add_argument(
        '--workers', 
        type=int, 
        default=MAX_WORKERS,
        help=f'多线程分析时的线程数量（默认：{MAX_WORKERS}）'
    )
    
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    clean_results_directory(target_dir=RESULTS_DIR)
    grb_name = args.grb
    if grb_name:
        grb_params = parse_grb_info_from_module(grb_name)
        output_dir = os.path.join(RESULTS_DIR, grb_name)
        create_config(grb_name, grb_params, output_dir=output_dir)

    try:
        # 如果请求列出GRB列表
        if args.list:
            grb_list = get_grb_list()
            if grb_list:
                logger.info(f"📋 发现 {len(grb_list)} 个可用的GRB事件:")
                for i, grb in enumerate(sorted(grb_list), 1):
                    logger.info(f"  {i:2d}. {grb}")
            else:
                logger.warning(f"❌ 在目录 {GRB_DATA_DIR} 中未找到任何GRB数据")
            return
        
        # 如果指定了单个GRB
        if args.grb:
            results, errors = analyze_single_grb(args.grb)
        else:
            # 开始多线程分析所有GRB
            logger.info(f"🔧 使用 {args.workers} 个线程进行批量分析")
            results, errors = analyze_grb_multithread(max_workers=args.workers)
        
        if results:
            # 生成汇总报告（使用新的结果格式）
            if args.grb:
                # 单个GRB分析报告
                summary_path = os.path.join(RESULTS_DIR, f"{args.grb}_analysis_summary.txt")
                report_title = f"GRB单个事件分析报告: {args.grb}"
            else:
                # 多线程批量分析报告
                summary_path = os.path.join(RESULTS_DIR, "analysis_summary.txt")
                report_title = "GRB多线程分析汇总报告"
            
            with open(summary_path, 'w') as f:
                f.write(f"{report_title}\n")
                f.write("="*50 + "\n")
                f.write(f"分析目录: {BASE_DIR}\n")
                f.write(f"分析时间: {pd.Timestamp.now()}\n")
                f.write(f"成功分析: {len(results)} 个GRB\n")
                f.write(f"失败分析: {len(errors)} 个GRB\n\n")
                
                for grb, result_data in results.items():
                    fit_results = result_data['fit_results']
                    grb_params = result_data['grb_params']
                    f.write(f"{grb}:\n")
                    f.write("="*30 + "\n")
                    f.write(f"  分析时间: {result_data['analysis_time']:.2f}s\n")
                    f.write(f"  Fit Quality: {fit_results.get('fit_quality', 'N/A')}\n")
                    f.write(f"  Log-Likelihood: {fit_results.get('loglike', 'N/A')}\n")
                    
                    # 添加GRB基本参数信息
                    f.write("  GRB参数:\n")
                    f.write(f"    RA: {grb_params['ra']:.4f} deg\n")
                    f.write(f"    Dec: {grb_params['dec']:.4f} deg\n")
                    f.write(f"    Trigger MET: {grb_params['trigger_met']:.2f} s\n")
                    f.write(f"    T0: {grb_params['T0']:.2f} s\n")
                    f.write(f"    T1: {grb_params['T1']:.2f} s\n")
                    f.write(f"    Time Range: {grb_params['tmin']:.2f} - {grb_params['tmax']:.2f} s\n")
                    if 'PIndex' in grb_params:
                        f.write(f"    PIndex: {grb_params['PIndex']}\n")
                                     
                    if 'highest_photon' in fit_results and fit_results['highest_photon']:
                        hp = fit_results['highest_photon']
                        f.write("  最高能光子信息:\n")
                        f.write(f"    能量: {hp['energy']:.2f} MeV\n")
                        f.write(f"    概率: {hp['probability']:.4f}\n")
                        f.write(f"    相对时间: {hp['relative_time']:.2f} s\n")
                        f.write(f"    RA: {hp['ra']:.4f} deg\n")
                        f.write(f"    Dec: {hp['dec']:.4f} deg\n")
                        f.write(f"    角分离: {hp['angular_separation']:.4f} deg\n")
                        f.write(f"    高概率光子总数: {hp['total_high_prob_photons']}\n")
                        f.write(f"    事件类型: {hp['event_class']}, {hp['event_type']}\n")
                    else:
                        f.write("  最高能光子: 未找到概率>0.9的光子\n")
                    
                    # 尝试从详细结果文件中读取更多信息
                    try:
                        result_file_path = os.path.join(RESULTS_DIR, grb, f"{grb}_fit_results.txt")
                        if os.path.exists(result_file_path):
                            f.write("  详细分析结果:\n")
                            with open(result_file_path, 'r') as detail_file:
                                lines = detail_file.readlines()
                                # 查找目标源信息
                                for i, line in enumerate(lines):
                                    if "Target Source:" in line:
                                        f.write(f"    目标源信息: {line.split('Target Source:')[1].strip()}\n")
                                        break
                    except Exception as e:
                        f.write(f"  详细信息读取失败: {str(e)}\n")
                    
                    f.write("\n")
                
                if errors:
                    f.write("失败的GRB:\n")
                    for grb, error in errors.items():
                        f.write(f"  {grb}: {error}\n")
            
            logger.info(f"汇总报告已保存: {summary_path}")
            
            # 生成光子信息的汇总报告
            try:
                all_photons_summary = []
                for grb, result_data in results.items():
                    grb_dir = os.path.join(RESULTS_DIR, grb)
                    all_photons_file = os.path.join(grb_dir, f"{grb}_all_photons.csv")
                    if os.path.exists(all_photons_file):
                        df = pd.read_csv(all_photons_file)
                        df['GRB'] = grb  # 添加GRB名称列
                        all_photons_summary.append(df)
                
                if all_photons_summary:
                    # 合并所有GRB的光子信息
                    combined_df = pd.concat(all_photons_summary, ignore_index=True)
                    
                    if args.grb:
                        # 单个GRB的光子信息
                        combined_path = os.path.join(RESULTS_DIR, f"{args.grb}_photons.csv")
                        logger.info(f"单个GRB的光子信息已保存: {combined_path}")
                    else:
                        # 所有GRB的光子信息汇总
                        combined_path = os.path.join(RESULTS_DIR, "all_grbs_photons.csv")
                        logger.info(f"所有GRB的光子信息汇总已保存: {combined_path}")
                    
                    combined_df.to_csv(combined_path, index=False)
            except Exception as e:
                logger.error(f"生成光子信息汇总报告失败: {str(e)}")
        
    except KeyboardInterrupt:
        logger.info("用户中断分析")
    except Exception as e:
        logger.error(f"主程序异常: {str(e)}")

if __name__ == "__main__":
    main()
import os
import time
import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime

# 需要修改save_dir
# excel路径
# sheetname
# 中间申请timesleep需要修改，如果申请的时间很长
# emin='30', emax='300000', radius='20'都是可以修改
# excel_file 需要修改

# 配置参数
MAX_WORKERS = 3  # 最大并发线程数，避免对服务器造成过大压力
thread_lock = threading.Lock()  # 线程锁，用于安全打印

def thread_safe_print(message):
    """线程安全的打印函数"""
    with thread_lock:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

def download_file(url, save_dir="/home/mxr/lee/data/fermilat", filename=None, headers=None, retries=3):
    """
    通用文件下载函数
    :param url: 文件下载地址
    :param save_dir: 保存目录（默认当前目录）
    :param filename: 自定义文件名（默认从URL提取）
    :param headers: 请求头设置
    :param retries: 失败重试次数
    """
    # 创建保存目录
    os.makedirs(save_dir, exist_ok=True)
    
    # 生成安全文件名
    filename = filename or os.path.basename(url.split("?")[0])
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)  # 过滤非法字符
    
    filepath = os.path.join(save_dir, filename)
    
    # 重试机制
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # 显示下载进度
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = downloaded / total_size * 100
                            # 使用线程安全打印，避免进度条混乱
                            if downloaded == total_size or downloaded % (total_size // 10) == 0:
                                thread_safe_print(f"下载 {filename}: {progress:.1f}%")
            
            thread_safe_print(f"文件已保存到: {os.path.abspath(filepath)}")
            return True
            
        except Exception as e:
            thread_safe_print(f"下载失败 (尝试 {attempt+1}/{retries}): {str(e)}")
            time.sleep(5)
    
    return False

def query_and_download_fermi_data(trigger_met, T0, T1, ra, dec, emin='100', emax='300000', radius='20', save_dir="fermi_data"):
    """
    Fermi LAT数据查询与下载主函数
    :param save_dir: 数据保存目录（默认fermi_data）
    """
    url = "https://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi"
    tstart, tstop = trigger_met + T0 - 1000, trigger_met + T1 + 2000
    
    # 构造查询参数
    payload = {
        'coordfield': f'{ra},{dec}',
        'coordsystem': 'J2000',
        'shapefield': radius,
        'radius': radius,
        'timefield': f'{tstart},{tstop}',
        'timetype': 'MET',
        'energyfield': f'{emin},{emax}',
        'photonOrExtendedOrNone': 'Photon',
        'spacecraft': 'on',
        'destination': 'query',
        'submit': 'Start Search'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    try:
        # 提交查询请求
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        
        # 提取结果页面URL
        match = re.search(
            r'https://fermi\.gsfc\.nasa\.gov/cgi-bin/ssc/LAT/QueryResults\.cgi\?id=L[\dA-F]+', 
            response.text
        )
        if not match:
            raise ValueError("未找到查询结果链接")
        
        download_url = match.group(0)
        thread_safe_print(f"结果页面: {download_url}")
        
        # 等待数据处理完成
        thread_safe_print("等待服务器处理数据...")
        time.sleep(10)
        
        # 获取结果页面
        result_response = requests.get(download_url, headers=headers)
        result_response.raise_for_status()
        
        # 解析下载链接
        wget_pattern = r'wget\s+(https://fermi\.gsfc\.nasa\.gov/FTP/fermi/data/lat/queries/\S+\.fits)'
        wget_links = re.findall(wget_pattern, result_response.text)
        
        if not wget_links:
            raise ValueError("未找到有效的下载链接")
        
        # 下载所有文件
        success_count = 0
        for file_url in wget_links:
            thread_safe_print(f"正在下载文件: {os.path.basename(file_url)}")
            if download_file(file_url, save_dir=save_dir, headers=headers):
                success_count += 1
        
        thread_safe_print(f"下载完成: {success_count}/{len(wget_links)} 个文件成功下载")
    
    except Exception as e:
        thread_safe_print(f"处理失败: {str(e)}")
        return False
    
    return success_count == len(wget_links)

def process_single_grb(row_data, base_save_dir):
    """
    处理单个GRB数据下载的函数（用于多线程）
    :param row_data: 包含GRB信息的元组 (idx, row)
    :param base_save_dir: 基础保存目录
    :return: (gcn_name, success_status)
    """
    idx, row = row_data
    
    try:
        gcn_name = str(row['gcn_name'])
        trigger_met = float(row['trigger_met'])
        
        # 解析合并的ra,dec坐标
        ra_dec = str(row['ra,dec']).strip()
        ra_dec_parts = ra_dec.split(',')
        if len(ra_dec_parts) != 2:
            thread_safe_print(f"警告: {gcn_name} 的ra,dec格式不正确: '{ra_dec}'，跳过此条")
            return gcn_name, False
            
        ra = float(ra_dec_parts[0].strip())
        dec = float(ra_dec_parts[1].strip())
        
        T0 = float(row['T0'])
        T1 = float(row['T1'])
        
        # 创建保存目录
        save_dir = os.path.join(base_save_dir, f"grb_data/{gcn_name}")
        
        thread_safe_print(f"[线程-{threading.current_thread().name}] 开始处理 {gcn_name}")
        thread_safe_print(f"参数: trigger_met={trigger_met}, ra={ra}, dec={dec}, T0={T0}, T1={T1}")
        thread_safe_print(f"保存目录: {save_dir}")
        
        # 执行查询和下载
        success = query_and_download_fermi_data(
            trigger_met=trigger_met,
            T0=T0,
            T1=T1,
            ra=ra,
            dec=dec,
            save_dir=save_dir
        )
        
        if success:
            thread_safe_print(f"✓ {gcn_name} 处理完成")
        else:
            thread_safe_print(f"✗ {gcn_name} 处理失败")
            
        return gcn_name, success
        
    except Exception as e:
        thread_safe_print(f"处理 {gcn_name} 时出错: {str(e)}")
        return gcn_name, False

def process_excel_and_download(excel_path, base_save_dir="/home/mxr/lee/data/fermilat", max_workers=MAX_WORKERS):
    """
    处理Excel表格并为每个条目多线程下载Fermi LAT数据
    :param excel_path: Excel文件路径
    :param base_save_dir: 基础保存目录
    :param max_workers: 最大并发线程数
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_path, sheet_name='Sheet1')
        thread_safe_print(f"成功读取Excel文件，共有{len(df)}条记录")
        
        # 确保所需列存在
        required_columns = ['gcn_name', 'trigger_met', 'ra,dec', 'T0', 'T1']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Excel表格缺少以下列: {', '.join(missing_columns)}")
        
        # 准备任务数据
        tasks = [(idx, row) for idx, row in df.iterrows()]
        
        # 使用线程池执行多线程下载
        thread_safe_print(f"开始多线程下载，使用 {max_workers} 个线程")
        
        success_count = 0
        failed_grbs = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(process_single_grb, task, base_save_dir): task 
                for task in tasks
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_task):
                try:
                    gcn_name, success = future.result()
                    if success:
                        success_count += 1
                    else:
                        failed_grbs.append(gcn_name)
                        
                except Exception as e:
                    task = future_to_task[future]
                    thread_safe_print(f"任务执行异常: {str(e)}")
                    failed_grbs.append(f"Task-{task[0]}")
        
        # 输出最终统计
        thread_safe_print(f"\n=== 下载完成统计 ===")
        thread_safe_print(f"总任务数: {len(df)}")
        thread_safe_print(f"成功下载: {success_count}")
        thread_safe_print(f"失败任务: {len(failed_grbs)}")
        
        if failed_grbs:
            thread_safe_print(f"失败的GRB: {', '.join(failed_grbs)}")
        
        thread_safe_print("所有数据处理完成!")
        return success_count == len(df)
        
    except Exception as e:
        thread_safe_print(f"处理Excel文件时出错: {str(e)}")
        return False

def main():
    """主函数，支持命令行参数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fermi LAT GRB数据下载工具')
    parser.add_argument('--excel', '-e', 
                       default='/home/mxr/lee/fermilat-grb.xls',
                       help='Excel文件路径（默认：/home/mxr/lee/fermilat-grb.xls）')
    parser.add_argument('--output', '-o',
                       default='/home/mxr/lee/data/fermilat',
                       help='输出目录（默认：/home/mxr/lee/data/fermilat）')
    parser.add_argument('--workers', '-w',
                       type=int, default=3,
                       help='并发线程数（默认：3）')
    
    args = parser.parse_args()
    
    thread_safe_print("开始批量多线程下载Fermi LAT数据...")
    thread_safe_print(f"Excel文件: {args.excel}")
    thread_safe_print(f"输出目录: {args.output}")
    thread_safe_print(f"并发线程数: {args.workers}")
    
    start_time = time.time()
    
    success = process_excel_and_download(args.excel, args.output, args.workers)
    
    end_time = time.time()
    thread_safe_print(f"总耗时: {end_time - start_time:.2f} 秒")
    
    if success:
        thread_safe_print("所有任务执行成功!")
    else:
        thread_safe_print("部分任务执行失败，请检查日志")

if __name__ == "__main__":
    main()
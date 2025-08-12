#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生成GRB分析的config.yaml配置文件
"""

import os
import yaml
import argparse

# =====================
# 配置参数
# =====================
BASE_DIR = "/home/mxr/lee/data/fermilat"
TEMPLATE_CONFIG = "/home/mxr/lee/config.yaml"  # 标准配置文件模板
GRB_DATA_DIR = os.path.join(BASE_DIR, "grb_data")
RESULTS_DIR = os.path.join(BASE_DIR, "resultsPL2")


def parse_grb_info(grb_name, results_dir=None):
    """解析GRB信息文件
    
    参数:
        grb_name (str): GRB名称
        results_dir (str, optional): 结果目录路径，默认为全局RESULTS_DIR
        
    返回:
        dict: 包含GRB参数的字典
    """
    if results_dir is None:
        results_dir = RESULTS_DIR
        
    info_file = os.path.join(results_dir, grb_name, f"{grb_name}.txt")
    
    if not os.path.exists(info_file):
        raise FileNotFoundError(f"信息文件不存在: {info_file}")
    
    params = {}
    with open(info_file, 'r') as f:
        for line in f:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # 尝试转换为数字
                try:
                    value = float(value) if '.' in value else int(value)
                except ValueError:
                    pass
                
                params[key] = value
    
    required_keys = ['trigger_met', 'T0', 'T1', 'ra', 'dec']
    missing = [k for k in required_keys if k not in params]
    if missing:
        raise ValueError(f"信息文件缺少必要参数: {', '.join(missing)}")
    
    # 计算时间范围
    params['tmin'] = params['trigger_met'] + params['T0'] - 200
    params['tmax'] = params['trigger_met'] + params['T1'] + 200
    
    return params


def create_config(grb_name, grb_params, output_dir=None, template_config=None, grb_data_dir=None):
    """为指定GRB创建配置文件
    
    参数:
        grb_name (str): GRB名称
        grb_params (dict): GRB参数字典
        output_dir (str, optional): 输出目录，默认为RESULTS_DIR/grb_name
        template_config (str, optional): 模板配置文件路径，默认为TEMPLATE_CONFIG
        grb_data_dir (str, optional): GRB数据目录，默认为GRB_DATA_DIR
        
    返回:
        str: 生成的配置文件路径
    """
    # 设置默认值
    if template_config is None:
        template_config = TEMPLATE_CONFIG
    if grb_data_dir is None:
        grb_data_dir = GRB_DATA_DIR
    if output_dir is None:
        output_dir = os.path.join(RESULTS_DIR, grb_name)
    
    # 读取模板配置
    with open(template_config, 'r') as f:
        config = yaml.safe_load(f)
    
    # 清除模板中的sources数据
    if 'model' in config and 'sources' in config['model']:
        config['model']['sources'] = []
        print("已清除配置模板中的sources数据")
    
    # 更新数据文件路径
    config['data']['evfile'] = os.path.join(grb_data_dir, grb_name, "ft1.fits")
    config['data']['scfile'] = os.path.join(grb_data_dir, grb_name, "ft2.fits")
    
    # 更新选择参数
    config['selection']['ra'] = grb_params['ra']
    config['selection']['dec'] = grb_params['dec']
    config['selection']['tmin'] = grb_params['tmin']
    config['selection']['tmax'] = grb_params['tmax']
    
    # 更新模型参数
    # 确保源模型存在
    if 'sources' not in config['model']:
        config['model']['sources'] = []
    
    # 添加GRB源（由于已清除sources，直接添加）
    config['model']['sources'].append({
        'name': grb_name,
        'ra': grb_params['ra'],
        'dec': grb_params['dec'],
        'SpectrumType': 'PowerLaw2',
        'SpatialModel': 'PointSource'
    })
    
    # 保存新配置文件
    os.makedirs(output_dir, exist_ok=True)
    config_path = os.path.join(output_dir, "config.yaml")
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, sort_keys=False)
    
    print(f"配置文件已创建: {config_path}")
    return config_path


def process_all_grbs(results_dir=None, template_config=None, grb_data_dir=None):
    """处理所有GRB目录，为每个GRB生成配置文件
    
    参数:
        results_dir (str, optional): 结果目录路径，默认为全局RESULTS_DIR
        template_config (str, optional): 模板配置文件路径，默认为TEMPLATE_CONFIG
        grb_data_dir (str, optional): GRB数据目录，默认为GRB_DATA_DIR
        
    返回:
        tuple: (成功数量, 失败数量, 失败列表)
    """
    # 设置默认值
    if results_dir is None:
        results_dir = RESULTS_DIR
    if template_config is None:
        template_config = TEMPLATE_CONFIG
    if grb_data_dir is None:
        grb_data_dir = GRB_DATA_DIR
    
    # 获取所有GRB目录
    grb_dirs = []
    for item in os.listdir(results_dir):
        item_path = os.path.join(results_dir, item)
        if os.path.isdir(item_path) and item.lower().startswith('grb'):
            grb_dirs.append(item)
    
    print(f"找到 {len(grb_dirs)} 个GRB目录")
    
    # 处理每个GRB
    success_count = 0
    failed_count = 0
    failed_grbs = []
    
    for grb_name in sorted(grb_dirs):
        try:
            print(f"\n处理 {grb_name}...")
            # 解析GRB信息
            grb_params = parse_grb_info(grb_name, results_dir)
            print(f"  成功解析GRB信息: {grb_name}")
            print(f"  RA: {grb_params['ra']}")
            print(f"  DEC: {grb_params['dec']}")
            print(f"  时间范围: {grb_params['tmin']} - {grb_params['tmax']}")
            
            # 创建配置文件
            config_path = create_config(
                grb_name, 
                grb_params, 
                os.path.join(results_dir, grb_name), 
                template_config, 
                grb_data_dir
            )
            
            print(f"  配置文件生成成功: {config_path}")
            success_count += 1
            
        except Exception as e:
            print(f"  错误: {str(e)}")
            failed_count += 1
            failed_grbs.append((grb_name, str(e)))
    
    # 打印汇总信息
    print(f"\n处理完成: 成功 {success_count} 个, 失败 {failed_count} 个")
    if failed_count > 0:
        print("失败的GRB列表:")
        for grb_name, error in failed_grbs:
            print(f"  {grb_name}: {error}")
    
    return success_count, failed_count, failed_grbs


def main():
    """主函数，处理命令行参数并执行配置文件生成"""
    parser = argparse.ArgumentParser(description='为GRB事件生成config.yaml配置文件')
    parser.add_argument('grb_name', nargs='?', help='GRB名称，例如GRB250320B。如果不提供，将处理所有GRB目录')
    parser.add_argument('--all', action='store_true', help='处理所有GRB目录')
    parser.add_argument('--results-dir', help='结果目录路径，默认为全局RESULTS_DIR')
    parser.add_argument('--template', help='模板配置文件路径，默认为全局TEMPLATE_CONFIG')
    parser.add_argument('--data-dir', help='GRB数据目录，默认为全局GRB_DATA_DIR')
    parser.add_argument('--output-dir', help='输出目录，默认为RESULTS_DIR/grb_name')
    
    args = parser.parse_args()
    
    # 处理所有GRB
    if args.all or args.grb_name is None:
        print("开始处理所有GRB目录...")
        success_count, failed_count, _ = process_all_grbs(
            args.results_dir,
            args.template,
            args.data_dir
        )
        
        if failed_count > 0:
            return 1
        return 0
    
    # 处理单个GRB
    try:
        grb_params = parse_grb_info(args.grb_name, args.results_dir)
        print(f"成功解析GRB信息: {args.grb_name}")
        print(f"  RA: {grb_params['ra']}")
        print(f"  DEC: {grb_params['dec']}")
        print(f"  时间范围: {grb_params['tmin']} - {grb_params['tmax']}")
        
        # 创建配置文件
        config_path = create_config(
            args.grb_name, 
            grb_params, 
            args.output_dir, 
            args.template, 
            args.data_dir
        )
        
        print(f"配置文件生成成功: {config_path}")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
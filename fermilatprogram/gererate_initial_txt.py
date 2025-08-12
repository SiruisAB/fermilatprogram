#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pandas as pd
import re

def format_grb_name(gcn_name):
    """
    格式化GRB名称，将检测到的GRB*变成标准的GRB*格式
    :param gcn_name: 原始GRB名称
    :return: 格式化后的GRB名称
    """
    # 去除前后空格
    gcn_name = str(gcn_name).strip()
    
    # 如果名称中包含特殊字符或格式不规范，进行标准化
    # 例如：GRB 220617A -> GRB220617A, grb220617a -> GRB220617A
    
    # 使用正则表达式提取GRB后面的数字和字母部分
    match = re.search(r'grb\s*(\d{6}[a-zA-Z])', gcn_name, re.IGNORECASE)
    if match:
        # 提取数字和字母部分，转换为标准格式
        grb_suffix = match.group(1).upper()
        formatted_name = f"GRB{grb_suffix}"
        return formatted_name
    
    # 如果已经是标准格式，直接返回（去除多余空格）
    if gcn_name.upper().startswith('GRB'):
        # 去除GRB和后续内容之间的空格
        formatted_name = re.sub(r'GRB\s+', 'GRB', gcn_name.upper())
        return formatted_name
    
    # 如果格式无法识别，返回原名称
    print(f"警告: 无法识别的GRB名称格式: {gcn_name}")
    return gcn_name

def write_grb_info_to_text(excel_path, sheet_name="GCN", base_dir="/home/mxr/lee/data/fermilat/resultsPL2"):
    """
    读取Excel表格，为每个GRB生成标准化的文件夹和文本信息
    :param excel_path: Excel文件路径
    :param sheet_name: 工作表名称
    :param base_dir: 基础目录路径
    """
    # 读取Excel表格
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    
    print(f"开始处理 {len(df)} 个GRB条目...")
    
    processed_count = 0
    skipped_count = 0

    for idx, row in df.iterrows():
        try:
            # 获取原始GRB名称并格式化
            original_gcn_name = str(row['gcn_name']).strip()
            formatted_gcn_name = format_grb_name(original_gcn_name)
            
            # 如果名称发生了变化，显示转换信息
            if original_gcn_name != formatted_gcn_name:
                print(f"[格式化] {original_gcn_name} -> {formatted_gcn_name}")
            
            trigger_met = row['trigger_met']
            T0 = row['T0']
            T1 = row['T1']
            ra_dec = str(row['ra,dec']).strip()
            ra_dec_parts = ra_dec.split(',')
            
            if len(ra_dec_parts) != 2:
                print(f"警告: {formatted_gcn_name} 的ra,dec格式不正确: '{ra_dec}'，跳过此条")
                skipped_count += 1
                continue
                    
            ra = float(ra_dec_parts[0].strip())
            dec = float(ra_dec_parts[1].strip())
            pindex = row.get('PIndex', 'N/A')  # 有些可能缺失

            # 使用格式化后的名称创建文件夹
            folder_path = os.path.join(base_dir, formatted_gcn_name)
            os.makedirs(folder_path, exist_ok=True)

            # 创建文本文件
            txt_path = os.path.join(folder_path, f"{formatted_gcn_name}.txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"# GRB信息文件\n")
                f.write(f"# 原始名称: {original_gcn_name}\n")
                f.write(f"# 标准化名称: {formatted_gcn_name}\n")
                f.write(f"# 生成时间: {pd.Timestamp.now()}\n\n")
                f.write(f"trigger_met: {trigger_met}\n")
                f.write(f"ra: {ra}\n")
                f.write(f"dec: {dec}\n")
                f.write(f"PIndex: {pindex}\n")
                f.write(f"T0: {T0}\n")
                f.write(f"T1: {T1}\n")
                
            print(f"[✓] 第{idx+1}条: {formatted_gcn_name} -> {txt_path}")
            processed_count += 1
            
        except Exception as e:
            print(f"[✗] 处理第{idx+1}条记录时出错: {str(e)}")
            skipped_count += 1
            continue

    # 输出处理统计
    print(f"\n=== 处理完成统计 ===")
    print(f"总条目数: {len(df)}")
    print(f"成功处理: {processed_count}")
    print(f"跳过条目: {skipped_count}")
    print(f"所有GRB信息文本文件已生成到: {base_dir}")

def list_generated_folders(base_dir="/home/mxr/lee/data/fermilat/resultsPL2"):
    """
    列出生成的所有GRB文件夹
    :param base_dir: 基础目录路径
    """
    if not os.path.exists(base_dir):
        print(f"目录不存在: {base_dir}")
        return
        
    grb_folders = []
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path) and item.startswith('GRB'):
            grb_folders.append(item)
    
    grb_folders.sort()
    print(f"\n在 {base_dir} 中找到 {len(grb_folders)} 个GRB文件夹:")
    for folder in grb_folders:
        txt_file = os.path.join(base_dir, folder, f"{folder}.txt")
        status = "✓" if os.path.exists(txt_file) else "✗"
        print(f"  {status} {folder}")

# 示例调用
if __name__ == "__main__":
    excel_file = "/home/mxr/lee/fermilat-grb.xls"
    
    print("开始生成GRB信息文件...")
    write_grb_info_to_text(excel_file)
    
    print("\n列出生成的文件夹:")
    list_generated_folders()
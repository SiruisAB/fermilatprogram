#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fermi LAT Program 基本使用示例

这个示例展示了如何使用fermilatprogram包进行GRB数据分析。
"""

import os
import sys

# 添加包路径（如果需要）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import fermilatprogram
    from fermilatprogram import lkmulty
    print(f"成功导入fermilatprogram包，版本: {fermilatprogram.__version__}")
except ImportError as e:
    print(f"导入失败: {e}")
    sys.exit(1)

def example_list_grbs():
    """示例：列出所有可用的GRB事件"""
    print("\n=== 列出所有可用的GRB事件 ===")
    try:
        grb_list = lkmulty.get_grb_list()
        print(f"找到 {len(grb_list)} 个GRB事件:")
        for i, grb in enumerate(grb_list[:10], 1):  # 只显示前10个
            print(f"  {i:2d}. {grb}")
        if len(grb_list) > 10:
            print(f"  ... 还有 {len(grb_list) - 10} 个GRB")
    except Exception as e:
        print(f"获取GRB列表失败: {e}")

def example_single_grb_analysis():
    """示例：分析单个GRB事件"""
    print("\n=== 单个GRB分析示例 ===")
    
    # 获取可用的GRB列表
    try:
        grb_list = lkmulty.get_grb_list()
        if not grb_list:
            print("没有找到可用的GRB事件")
            return
        
        # 选择第一个GRB进行分析
        test_grb = grb_list[0]
        print(f"准备分析GRB: {test_grb}")
        print("注意：这只是一个示例，实际分析需要确保数据文件存在")
        
        # 这里只是展示如何调用，实际运行需要数据文件
        # result = lkmulty.analyze_single_grb(test_grb)
        # print(f"分析结果: {result}")
        
    except Exception as e:
        print(f"单个GRB分析示例失败: {e}")

def example_package_info():
    """示例：显示包信息"""
    print("\n=== 包信息 ===")
    print(f"包名: {fermilatprogram.__name__}")
    print(f"版本: {fermilatprogram.__version__}")
    print(f"作者: {fermilatprogram.__author__}")
    print(f"描述: {fermilatprogram.__description__}")
    
    print("\n可用模块:")
    for module in fermilatprogram.__all__:
        print(f"  - {module}")

def main():
    """主函数"""
    print("Fermi LAT Program 使用示例")
    print("=" * 50)
    
    # 显示包信息
    example_package_info()
    
    # 列出GRB事件
    example_list_grbs()
    
    # 单个GRB分析示例
    example_single_grb_analysis()
    
    print("\n=== 命令行工具使用提示 ===")
    print("安装包后，可以使用以下命令行工具:")
    print("  grb-analyze --help     # GRB数据分析工具")
    print("  grb-download --help    # 数据下载工具")
    print("  grb-config --help      # 配置文件生成工具")
    
    print("\n示例命令:")
    print("  grb-analyze --list                    # 列出所有GRB")
    print("  grb-analyze --grb GRB250320B          # 分析单个GRB")
    print("  grb-download -e data.xls -o ./output  # 下载数据")

if __name__ == "__main__":
    main()
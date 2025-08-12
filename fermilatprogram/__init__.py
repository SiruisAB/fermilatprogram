#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fermi-LAT GRB数据分析工具包

这是一个用于分析Fermi-LAT伽马射线暴(GRB)数据的Python工具包。
主要功能包括：
- GRB数据下载和预处理
- 多线程批量分析
- 高概率光子识别
- SED(谱能分布)分析
- 结果可视化和报告生成

主要模块：
- lkmulty: 主分析程序，支持单个或批量GRB分析
- photon_analyzer: 高概率光子分析模块
- Generate_gconfig: 配置文件生成模块
- download: 数据下载模块
- cleandir: 结果目录清理模块
"""

__version__ = "1.0.0"
__author__ = "GRB Analysis Team"
__email__ = "grb@example.com"
__description__ = "Fermi-LAT GRB数据分析工具包"

# 导入主要模块和函数
try:
    from . import lkmulty
    from . import photon_analyzer
    from . import Generate_gconfig
    from . import download
    from . import cleandir
    from . import gererate_initial_txt
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import lkmulty
    import photon_analyzer
    import Generate_gconfig
    import download
    import cleandir
    import gererate_initial_txt

# 导出主要函数
__all__ = [
    'lkmulty',
    'photon_analyzer', 
    'Generate_gconfig',
    'download',
    'cleandir',
    'gererate_initial_txt',
]
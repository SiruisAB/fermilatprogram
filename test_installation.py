#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fermi LAT Program 安装测试脚本

这个脚本用于验证fermilatprogram包是否正确安装并且基本功能正常工作。
运行此脚本可以快速检查包的状态。
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path

def print_header(title):
    """打印测试标题"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def print_result(test_name, success, message=""):
    """打印测试结果"""
    status = "✅ 通过" if success else "❌ 失败"
    print(f"{test_name:<30} {status}")
    if message:
        print(f"   详情: {message}")

def test_python_version():
    """测试Python版本"""
    print_header("Python环境检查")
    
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    # 检查Python版本是否满足要求
    required_version = (3, 7)
    version_ok = version >= required_version
    print_result("Python版本检查", version_ok, 
                f"需要 >= {required_version[0]}.{required_version[1]}, 当前: {version.major}.{version.minor}")
    
    return version_ok

def test_package_import():
    """测试包导入"""
    print_header("包导入测试")
    
    results = []
    
    # 测试主包导入
    try:
        import fermilatprogram
        print_result("主包导入", True, f"版本: {fermilatprogram.__version__}")
        results.append(True)
    except ImportError as e:
        print_result("主包导入", False, str(e))
        results.append(False)
        return False  # 主包导入失败，后续测试无意义
    
    # 测试子模块导入
    modules = [
        ('lkmulty', 'GRB分析主模块'),
        ('photon_analyzer', '光子分析模块'),
        ('Generate_gconfig', '配置生成模块'),
        ('download', '数据下载模块'),
        ('cleandir', '目录清理模块')
    ]
    
    for module_name, description in modules:
        try:
            module = importlib.import_module(f'fermilatprogram.{module_name}')
            print_result(f"{module_name}模块导入", True, description)
            results.append(True)
        except ImportError as e:
            print_result(f"{module_name}模块导入", False, str(e))
            results.append(False)
    
    return all(results)

def test_dependencies():
    """测试依赖包"""
    print_header("依赖包检查")
    
    dependencies = [
        ('numpy', 'NumPy数值计算库'),
        ('pandas', 'Pandas数据处理库'),
        ('scipy', 'SciPy科学计算库'),
        ('astropy', 'Astropy天文学库'),
        ('matplotlib', 'Matplotlib绘图库'),
        ('yaml', 'PyYAML配置文件库'),
        ('h5py', 'HDF5文件处理库')
    ]
    
    results = []
    
    for dep_name, description in dependencies:
        try:
            module = importlib.import_module(dep_name)
            version = getattr(module, '__version__', '未知版本')
            print_result(f"{dep_name}依赖", True, f"{description} (v{version})")
            results.append(True)
        except ImportError:
            print_result(f"{dep_name}依赖", False, f"{description} - 未安装")
            results.append(False)
    
    # 特殊检查fermipy（可能不是必需的）
    try:
        import fermipy
        version = getattr(fermipy, '__version__', '未知版本')
        print_result("fermipy依赖", True, f"FermiPy分析库 (v{version})")
    except ImportError:
        print_result("fermipy依赖", False, "FermiPy分析库 - 未安装（可选）")
    
    return all(results)

def test_command_line_tools():
    """测试命令行工具"""
    print_header("命令行工具测试")
    
    tools = [
        ('grb-analyze', 'GRB数据分析工具'),
        ('grb-download', '数据下载工具'),
        ('grb-config', '配置文件生成工具')
    ]
    
    results = []
    
    for tool_name, description in tools:
        try:
            # 尝试运行 --help 命令
            result = subprocess.run([tool_name, '--help'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            if result.returncode == 0:
                print_result(f"{tool_name}命令", True, description)
                results.append(True)
            else:
                print_result(f"{tool_name}命令", False, f"退出码: {result.returncode}")
                results.append(False)
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print_result(f"{tool_name}命令", False, f"命令不可用: {str(e)}")
            results.append(False)
    
    return all(results)

def test_basic_functionality():
    """测试基本功能"""
    print_header("基本功能测试")
    
    results = []
    
    try:
        from fermilatprogram import lkmulty
        
        # 测试获取GRB列表功能
        try:
            grb_list = lkmulty.get_grb_list()
            if isinstance(grb_list, list):
                print_result("GRB列表获取", True, f"找到 {len(grb_list)} 个GRB事件")
                results.append(True)
            else:
                print_result("GRB列表获取", False, "返回值不是列表类型")
                results.append(False)
        except Exception as e:
            print_result("GRB列表获取", False, str(e))
            results.append(False)
        
        # 测试配置解析功能
        try:
            from fermilatprogram.Generate_gconfig import parse_grb_info
            print_result("配置解析功能", True, "parse_grb_info函数可用")
            results.append(True)
        except Exception as e:
            print_result("配置解析功能", False, str(e))
            results.append(False)
            
    except ImportError as e:
        print_result("基本功能测试", False, f"模块导入失败: {str(e)}")
        results.append(False)
    
    return all(results)

def test_file_structure():
    """测试文件结构"""
    print_header("文件结构检查")
    
    # 获取包的安装路径
    try:
        import fermilatprogram
        package_path = Path(fermilatprogram.__file__).parent
        print(f"包安装路径: {package_path}")
        
        # 检查关键文件
        key_files = [
            '__init__.py',
            'lkmulty.py',
            'photon_analyzer.py',
            'Generate_gconfig.py',
            'download.py',
            'cleandir.py'
        ]
        
        results = []
        for filename in key_files:
            file_path = package_path / filename
            exists = file_path.exists()
            print_result(f"{filename}文件", exists, f"路径: {file_path}")
            results.append(exists)
        
        return all(results)
        
    except Exception as e:
        print_result("文件结构检查", False, str(e))
        return False

def main():
    """主测试函数"""
    print("🧪 Fermi LAT Program 安装测试")
    print(f"测试时间: {os.popen('date').read().strip()}")
    
    # 运行所有测试
    test_results = {
        "Python环境": test_python_version(),
        "包导入": test_package_import(),
        "依赖包": test_dependencies(),
        "命令行工具": test_command_line_tools(),
        "基本功能": test_basic_functionality(),
        "文件结构": test_file_structure()
    }
    
    # 汇总结果
    print_header("测试结果汇总")
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<15} {status}")
        if result:
            passed_tests += 1
    
    print(f"\n📊 测试统计: {passed_tests}/{total_tests} 项测试通过")
    
    # 最终结论
    if passed_tests == total_tests:
        print("\n🎉 恭喜！fermilatprogram包安装完成且功能正常！")
        print("\n📋 下一步操作:")
        print("   1. 运行 'grb-analyze --list' 查看可用的GRB事件")
        print("   2. 运行 'grb-analyze --grb GRB250320B' 分析单个GRB")
        print("   3. 查看 examples/basic_usage.py 了解更多用法")
        return True
    else:
        print(f"\n⚠️  警告：{total_tests - passed_tests} 项测试失败")
        print("\n🔧 建议操作:")
        print("   1. 检查Python环境和依赖包安装")
        print("   2. 重新安装包: pip install -e .")
        print("   3. 查看错误信息并修复相关问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
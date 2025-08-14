import os
import shutil
import argparse
import datetime
import fnmatch
import threading
import time
import uuid

# 配置参数
BASE_DIR = "/home/mxr/lee/data/fermilat"
RESULTS_DIR = os.path.join(BASE_DIR, "resultsPL2")

# 线程锁，用于同步备份操作
backup_lock = threading.Lock()

def clean_results_directory(backup=False, target_dir=None, keep_patterns=None):
    """清理结果目录，只保留指定模式的文件
    
    参数:
        backup (bool): 是否在清理前创建备份
        target_dir (str): 指定要清理的目录，默认为RESULTS_DIR
        keep_patterns (list): 要保留的文件模式列表，默认为['GRB*.txt']
    """
    # 设置默认保留模式
    if keep_patterns is None:
        keep_patterns = ['GRB*.txt']
    # 如果指定了目标目录，则使用指定的目录
    results_dir = target_dir if target_dir else RESULTS_DIR
    print(f"正在清理结果目录: {results_dir}...")
    
    # 如果需要备份，创建备份（线程安全）
    if backup:
        with backup_lock:  # 使用线程锁确保只有一个线程创建备份
            # 生成唯一的备份目录名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            thread_id = threading.current_thread().name
            unique_id = str(uuid.uuid4())[:8]  # 添加唯一标识符
            backup_dir = f"{results_dir}_backup_{timestamp}_{thread_id}_{unique_id}"
            
            # 检查是否已经有其他线程创建了备份
            existing_backups = [d for d in os.listdir(os.path.dirname(results_dir)) 
                              if d.startswith(f"{os.path.basename(results_dir)}_backup_{timestamp}")]
            
            if existing_backups:
                print(f"发现已存在的备份: {existing_backups[0]}，跳过备份创建")
            elif os.path.exists(results_dir):
                try:
                    print(f"创建备份: {backup_dir}")
                    shutil.copytree(results_dir, backup_dir)
                    print(f"备份创建成功: {backup_dir}")
                except FileExistsError:
                    print(f"备份目录已存在，跳过: {backup_dir}")
                except Exception as e:
                    print(f"创建备份失败: {str(e)}")
    
    if not os.path.exists(results_dir):
        os.makedirs(results_dir, exist_ok=True)
        print(f"创建结果目录: {results_dir}")
        return
    
    # 遍历结果目录中的所有子目录和文件
    for item in os.listdir(results_dir):
        item_path = os.path.join(results_dir, item)
        
        if os.path.isdir(item_path):
            # 处理子目录（如results/GRB250313A/）
            grb_name = os.path.basename(item_path)
            grb_info_file = os.path.join(item_path, f"{grb_name}.txt")
            
            # 备份GRB基础数据文件
            grb_info_backup = None
            if os.path.exists(grb_info_file):
                with open(grb_info_file, 'r') as f:
                    grb_info_backup = f.read()
                print(f"备份GRB基础数据文件: {grb_info_file}")
            
            # 删除整个子目录
            shutil.rmtree(item_path)
            print(f"删除目录: {item_path}")
            
            # 重新创建目录并恢复GRB基础数据文件
            os.makedirs(item_path, exist_ok=True)
            if grb_info_backup:
                with open(grb_info_file, 'w') as f:
                    f.write(grb_info_backup)
                print(f"恢复GRB基础数据文件: {grb_info_file}")
        
        elif os.path.isfile(item_path):
            # 检查文件是否匹配任何保留模式
            should_keep = False
            for pattern in keep_patterns:
                if fnmatch.fnmatch(item, pattern):
                    should_keep = True
                    break
            
            # 根据匹配结果决定是否保留文件
            if should_keep:
                print(f"保留文件: {item_path}")
            else:
                os.remove(item_path)
                print(f"删除文件: {item_path}")
    
    print("结果目录清理完成")

def main():
    """主函数，用于命令行调用"""
    parser = argparse.ArgumentParser(description='清理FermiPy分析结果目录')
    parser.add_argument('--backup', action='store_true', help='清理前创建备份')
    parser.add_argument('--target-dir', type=str, help='指定要清理的目录')
    parser.add_argument('--keep-patterns', nargs='+', default=['GRB*.txt'], 
                       help='要保留的文件模式列表')
    
    args = parser.parse_args()
    
    clean_results_directory(
        backup=args.backup,
        target_dir=args.target_dir,
        keep_patterns=args.keep_patterns,
        RESULTS_DIR = RESULTS_DIR
    )

if __name__ == "__main__":
    main()
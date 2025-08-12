# Fermi-LAT GRB数据分析工具包

一个用于分析Fermi-LAT伽马射线暴(GRB)数据的Python工具包，提供完整的数据处理、分析和可视化功能。

## 🌟 主要功能

- **多线程批量分析**: 支持同时分析多个GRB事件，提高处理效率
- **单个GRB分析**: 支持指定特定GRB事件进行详细分析
- **高概率光子识别**: 自动识别和分析高概率伽马射线光子
- **SED分析**: 生成谱能分布(Spectral Energy Distribution)图像
- **配置文件生成**: 自动生成FermiPy分析所需的配置文件
- **结果可视化**: 生成专业的分析图表和报告
- **数据下载**: 自动下载Fermi-LAT观测数据

## 📦 安装

### 从源码安装

```bash
# 克隆项目
git clone https://github.com/yourusername/fermilatprogram.git
cd fermilatprogram

# 安装依赖
pip install -r requirements.txt

# 安装项目
pip install -e .
```

### 使用pip安装

```bash
pip install fermilatprogram
```

## 🚀 快速开始

### 命令行使用

```bash
# 列出所有可用的GRB事件
grb-analyze --list

# 分析单个GRB事件
grb-analyze --grb GRB250320B

# 批量分析所有GRB（使用4个线程）
grb-analyze --workers 4

# 查看帮助信息
grb-analyze --help
```

### Python API使用

```python
import fermilatprogram as flp

# 获取可用的GRB列表
grb_list = flp.get_grb_list()
print(f"发现 {len(grb_list)} 个GRB事件")

# 分析单个GRB
results, errors = flp.analyze_single_grb('GRB250320B')

# 批量分析
results, errors = flp.analyze_grb_multithread(max_workers=4)

# 高概率光子分析
from fermilatprogram import photon_analyzer
highest_photon = photon_analyzer.find_highest_prob_photon(gta, grb_name, grb_params)
```

## 📁 项目结构

```
fermilatprogram/
├── __init__.py              # 包初始化文件
├── lkmulty.py              # 主分析程序
├── photon_analyzer.py      # 高概率光子分析模块
├── Generate_gconfig.py     # 配置文件生成模块
├── download.py             # 数据下载模块
├── cleandir.py             # 结果目录清理模块
├── gererate_initial_txt.py # 初始文件生成
├── setup.py                # 项目安装配置
├── requirements.txt        # 依赖包列表
└── README.md              # 项目说明文档
```

## 🔧 配置要求

### 系统要求
- Python 3.7+
- Linux/macOS (推荐)
- 至少8GB内存
- 充足的磁盘空间用于存储数据和结果

### 依赖包
- **fermipy**: Fermi-LAT数据分析框架
- **astropy**: 天文学Python库
- **numpy/pandas**: 数据处理
- **matplotlib**: 数据可视化
- **PyYAML**: 配置文件处理

## 📊 输出结果

分析完成后，程序会生成以下文件：

- **分析报告**: `{GRB_NAME}_analysis_summary.txt`
- **光子数据**: `{GRB_NAME}_photons.csv`
- **SED图像**: `{GRB_NAME}_sed.png`
- **拟合结果**: `{GRB_NAME}_fit_results.txt`
- **模型文件**: `final_model.*`

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

如有问题或建议，请联系：
- Email: grb@example.com
- GitHub Issues: [项目Issues页面](https://github.com/yourusername/fermilatprogram/issues)

## 🙏 致谢

感谢Fermi-LAT团队提供的优秀数据和工具，以及所有为这个项目做出贡献的开发者。
# Changelog

本文档记录了fermilatprogram项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2025-01-XX

### 新增
- 🎉 首次发布fermilatprogram Python包
- ✨ 多线程批量GRB数据分析功能
- ✨ 单个GRB事件分析功能
- ✨ 高概率光子识别和分析
- ✨ SED（谱能量分布）分析和可视化
- ✨ 自动配置文件生成
- ✨ Fermi LAT数据下载工具
- ✨ 结果可视化和报告生成
- 🔧 命令行工具支持：
  - `grb-analyze`: GRB数据分析工具
  - `grb-download`: 数据下载工具
  - `grb-config`: 配置文件生成工具

### 功能特性
- 📊 支持多种分析模式（批量/单个GRB）
- 🚀 多线程并行处理，提高分析效率
- 📈 自动生成分析报告和统计信息
- 🎯 高概率光子筛选和保存
- 📋 Excel格式结果导出
- 🔍 详细的日志记录和错误处理
- ⚙️ 灵活的配置参数设置

### 技术实现
- 🏗️ 基于FermiPy和Astropy的科学计算框架
- 📦 标准Python包结构，支持pip安装
- 🧪 完整的项目配置（pyproject.toml, setup.py等）
- 📚 详细的文档和使用示例
- 🔒 MIT开源许可证

### 依赖项
- Python >= 3.7
- numpy >= 1.19.0
- pandas >= 1.3.0
- scipy >= 1.7.0
- astropy >= 4.0
- fermipy >= 1.0.0
- matplotlib >= 3.3.0
- seaborn >= 0.11.0
- PyYAML >= 5.4.0
- h5py >= 3.1.0

### 文档
- 📖 完整的README.md使用指南
- 💡 基本使用示例（examples/basic_usage.py）
- 🔧 安装和配置说明
- 📋 API文档和函数说明

---

## 版本说明

### 版本号格式
本项目使用语义化版本号：`主版本号.次版本号.修订号`

- **主版本号**：不兼容的API修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 变更类型
- `新增` - 新功能
- `变更` - 对现有功能的变更
- `弃用` - 即将移除的功能
- `移除` - 已移除的功能
- `修复` - 问题修复
- `安全` - 安全相关的修复

---

## 贡献指南

如果您想为本项目做出贡献，请：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

---

## 联系方式

- 项目主页: https://github.com/yourusername/fermilatprogram
- 问题反馈: https://github.com/yourusername/fermilatprogram/issues
- 邮箱: grb@example.com
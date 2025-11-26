# README.md 编写规范

## 基本结构

一个完整的 README.md 应包含以下部分：

```markdown
# 项目名称

项目的简短描述（一句话说明项目是什么）

## 功能特性

- 功能点 1
- 功能点 2
- 功能点 3

## 快速开始

### 环境要求

- Python 3.x
- 其他依赖

### 安装

\`\`\`bash
# 克隆项目
git clone <repository-url>

# 安装依赖
pip install -r requirements.txt
\`\`\`

### 使用示例

\`\`\`python
# 简单的使用示例
from module import function

result = function()
\`\`\`

## 项目结构

\`\`\`
project/
├── src/           # 源代码
├── tests/         # 测试文件
├── docs/          # 文档
└── README.md      # 项目说明
\`\`\`

## 开发指南

### 本地开发

\`\`\`bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest
\`\`\`

### 代码规范

- 遵循 PEP 8 规范
- 使用类型注解
- 编写单元测试

## API 文档

（如果适用）详细的 API 使用说明

## 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m '添加某个功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 [MIT] 许可证

## 联系方式

- 作者：[姓名]
- 邮箱：[email]
- 项目链接：[GitHub URL]
\`\`\`

## 各部分详细说明

### 1. 项目标题和描述

- **标题**：使用一级标题，清晰的项目名称
- **描述**：一到两句话说明项目的核心功能和价值

```markdown
# 数据分析工具

一个用于快速处理和可视化大规模数据集的 Python 工具库。
```

### 2. 功能特性

- 使用列表形式
- 突出核心功能
- 简洁明了

```markdown
## 功能特性

- 🚀 高性能数据处理
- 📊 丰富的可视化选项
- 🔧 灵活的配置系统
- 📝 完整的类型注解
```

### 3. 快速开始

#### 环境要求
明确列出所需的环境和依赖版本

```markdown
### 环境要求

- Python 3.9+
- pip 或 uv
- （可选）虚拟环境工具
```

#### 安装步骤
提供清晰的安装命令

```markdown
### 安装

使用 pip：
\`\`\`bash
pip install your-package
\`\`\`

使用 uv：
\`\`\`bash
uv pip install your-package
\`\`\`

从源码安装：
\`\`\`bash
git clone https://github.com/username/project.git
cd project
pip install -e .
\`\`\`
```

#### 使用示例
提供最简单的使用示例，让用户快速上手

```markdown
### 使用示例

\`\`\`python
from your_package import main_function

# 基本使用
result = main_function(data)
print(result)

# 高级用法
result = main_function(
    data,
    option1=True,
    option2="custom"
)
\`\`\`
```

### 4. 项目结构

使用树形结构展示项目组织

```markdown
## 项目结构

\`\`\`
project/
├── src/
│   ├── core/          # 核心功能模块
│   ├── utils/         # 工具函数
│   └── api/           # API 接口
├── tests/             # 测试文件
│   ├── unit/          # 单元测试
│   └── integration/   # 集成测试
├── docs/              # 文档
├── examples/          # 示例代码
├── pyproject.toml     # 项目配置
└── README.md          # 项目说明
\`\`\`
```

### 5. 开发指南

为贡献者提供开发环境设置指南

```markdown
## 开发指南

### 设置开发环境

\`\`\`bash
# 克隆项目
git clone <repository-url>
cd project

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\\Scripts\\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"
\`\`\`

### 运行测试

\`\`\`bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_specific.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
\`\`\`

### 代码检查

\`\`\`bash
# 格式化代码
black src tests

# 类型检查
mypy src

# 代码质量检查
ruff check src
\`\`\`
```

### 6. API 文档

如果项目提供 API，详细说明使用方法

```markdown
## API 文档

### 核心函数

#### `process_data(data, options)`

处理输入数据并返回结果。

**参数：**
- `data` (list): 输入数据列表
- `options` (dict): 配置选项
  - `mode` (str): 处理模式，可选 'fast' 或 'accurate'
  - `verbose` (bool): 是否输出详细信息

**返回：**
- `dict`: 处理结果

**示例：**
\`\`\`python
result = process_data(
    data=[1, 2, 3],
    options={'mode': 'fast', 'verbose': True}
)
\`\`\`
```

### 7. 徽章（可选）

在标题下方添加项目状态徽章

```markdown
# 项目名称

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)
```

## 编写原则

1. **清晰简洁**：使用简单直接的语言
2. **结构化**：使用标题和列表组织内容
3. **示例驱动**：提供实际可运行的代码示例
4. **保持更新**：随项目发展更新文档
5. **用户视角**：从使用者角度编写，而非开发者
6. **中文表达**：使用自然流畅的中文
7. **代码块格式**：正确使用语法高亮

## 常见错误

❌ **避免**：
- 过于简单，缺少关键信息
- 过于复杂，信息过载
- 缺少使用示例
- 安装步骤不清晰
- 过时的信息

✅ **推荐**：
- 提供完整但简洁的信息
- 包含可运行的示例
- 清晰的安装和使用步骤
- 定期更新维护
- 考虑不同用户群体的需求

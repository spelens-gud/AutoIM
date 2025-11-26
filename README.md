# 旺旺RPA自动化系统

一个基于 Python 和 Selenium 的 RPA（机器人流程自动化）工具，用于自动化处理 1688 旺旺聊天消息，实现消息的自动接收、智能回复和会话管理。

## 功能特性

- 🤖 **自动消息监控**：实时监控 1688 旺旺消息，每3秒检查一次新消息
- 💬 **智能自动回复**：基于关键词匹配规则，自动回复常见问题
- 📊 **会话管理**：管理多个聊天会话，跟踪会话状态和活跃度
- 🔐 **登录状态保持**：通过浏览器数据目录持久化登录状态，无需重复登录
- 📝 **完整日志记录**：记录所有关键操作和错误信息，便于问题排查
- ⚙️ **灵活配置**：通过 YAML 配置文件自定义系统行为
- 🎯 **消息去重**：自动识别并过滤已处理的消息
- 🔄 **失败重试**：消息发送失败时自动重试，提高可靠性

## 快速开始

### 环境要求

- Python 3.12+
- Chrome 浏览器
- pip 或 uv 包管理器

### 安装

#### 使用 pip

```bash
# 克隆项目
git clone <repository-url>
cd wangwang-rpa

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .
```

#### 使用 uv（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd wangwang-rpa

# 使用 uv 安装依赖
uv pip install -e .
```

### 首次使用 - 登录流程

首次运行系统时，需要手动完成 1688 旺旺登录：

1. **启动系统**：
   ```bash
   python main.py
   ```

2. **等待浏览器打开**：系统会自动启动 Chrome 浏览器并导航到 1688 旺旺聊天页面

3. **手动登录**：
   - 在打开的浏览器窗口中，使用您的 1688 账号密码完成登录
   - 完成任何必要的验证步骤（如扫码、验证码等）

4. **确认登录成功**：
   - 登录成功后，系统会自动检测到登录状态
   - 系统会保存登录状态到浏览器数据目录
   - 控制台会显示"登录成功"的提示信息

5. **后续使用**：
   - 下次启动时，系统会自动加载保存的登录状态
   - 无需重复登录，直接进入消息监控状态

### 基本使用

```bash
# 启动 RPA 系统（有头模式，可以看到浏览器）
python main.py

# 启动无头模式（后台运行，不显示浏览器窗口）
python main.py --headless

# 指定配置文件
python main.py --config config/custom_config.yaml

# 停止系统
# 按 Ctrl+C 优雅退出
```

## 配置说明

### 系统配置文件

系统配置文件位于 `config/config.yaml`，包含以下配置项：

```yaml
# 浏览器配置
browser:
  headless: false              # 是否使用无头模式
  user_data_dir: "./browser_data"  # 浏览器数据目录

# 旺旺配置
wangwang:
  url: "https://amos.alicdn.com/msg.aw"  # 1688旺旺聊天地址
  check_interval: 3            # 消息检查间隔（秒）

# 消息配置
message:
  retry_times: 2               # 发送失败重试次数
  retry_delay: 1               # 重试延迟（秒）

# 会话配置
session:
  inactive_timeout: 1800       # 会话超时时间（秒，默认30分钟）

# 自动回复配置
auto_reply:
  enabled: true                # 是否启用自动回复
  rules_file: "config/auto_reply_rules.yaml"  # 回复规则文件路径

# 日志配置
logging:
  level: "INFO"                # 日志级别：DEBUG, INFO, WARNING, ERROR
  file: "logs/wangwang_rpa.log"  # 日志文件路径
  max_bytes: 10485760          # 单个日志文件最大大小（10MB）
  backup_count: 5              # 保留的日志文件数量
```

### 自动回复规则配置

自动回复规则文件位于 `config/auto_reply_rules.yaml`，用于配置关键词匹配和自动回复内容：

```yaml
rules:
  # 价格咨询
  - keywords: ["价格", "多少钱", "报价", "批发价"]
    reply: "您好，具体价格请查看商品详情页。批量采购可享受更优惠价格，欢迎咨询。"
  
  # 起订量问题
  - keywords: ["起订", "最少", "起批", "多少起"]
    reply: "您好，商品详情页有标注起订量信息。大批量采购可以联系我们获取更优惠的价格。"
  
  # 发货咨询
  - keywords: ["发货", "什么时候发", "几天发货"]
    reply: "您好，现货一般48小时内发货，定制产品根据数量3-7天发货，具体请咨询客服。"
  
  # 样品问题
  - keywords: ["样品", "打样", "寄样"]
    reply: "您好，我们支持寄送样品，样品费用和运费请联系客服确认。批量采购可退还样品费。"
  
  # 定制问题
  - keywords: ["定制", "定做", "OEM"]
    reply: "您好，我们支持定制服务，可根据您的需求定制产品。具体定制方案和价格请联系客服详谈。"
```

#### 规则配置说明

- **keywords**：关键词列表，消息中包含任一关键词即匹配
- **reply**：匹配成功后自动发送的回复内容
- 规则按顺序匹配，返回第一个匹配的回复
- 不匹配任何规则的消息会被标记为需要人工处理

#### 添加自定义规则

1. 打开 `config/auto_reply_rules.yaml` 文件
2. 按照上述格式添加新的规则
3. 保存文件后重启系统即可生效

示例：

```yaml
rules:
  # 添加新规则 - 合作方式
  - keywords: ["合作", "代理", "加盟", "经销"]
    reply: "您好，我们欢迎各地客户合作。关于代理加盟政策，请联系我们的商务经理详谈。"
```

## 项目结构

```
wangwang-rpa/
├── src/
│   ├── core/                  # 核心功能模块
│   │   ├── browser_controller.py    # 浏览器控制器
│   │   ├── message_handler.py       # 消息处理器
│   │   ├── session_manager.py       # 会话管理器
│   │   └── auto_reply_engine.py     # 自动回复引擎
│   ├── models/                # 数据模型
│   │   ├── message.py         # 消息模型
│   │   ├── session.py         # 会话模型
│   │   ├── config.py          # 配置模型
│   │   └── auto_reply_rule.py # 自动回复规则模型
│   ├── utils/                 # 工具模块
│   │   ├── config_manager.py  # 配置管理器
│   │   ├── logger.py          # 日志工具
│   │   └── exceptions.py      # 异常定义
│   └── rpa.py                 # RPA主控制器
├── config/                    # 配置文件目录
│   ├── config.yaml            # 系统配置
│   └── auto_reply_rules.yaml  # 自动回复规则
├── logs/                      # 日志文件目录
├── tests/                     # 测试文件
├── main.py                    # 程序入口
├── pyproject.toml             # 项目配置
└── README.md                  # 项目说明
```

## 开发指南

### 设置开发环境

```bash
# 克隆项目
git clone <repository-url>
cd wangwang-rpa

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# 安装开发依赖
pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_message_handler.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html  # Mac
# 或
xdg-open htmlcov/index.html  # Linux
```

### 代码检查

```bash
# 格式化代码
black src tests

# 排序导入
isort src tests

# 代码质量检查
ruff check src tests

# 类型检查
mypy src
```

## 使用示例

### 示例1：基本使用

```bash
# 启动系统
python main.py

# 系统会自动：
# 1. 加载配置文件
# 2. 启动浏览器
# 3. 检查登录状态
# 4. 开始监控消息
# 5. 根据规则自动回复
```

### 示例2：自定义配置

```bash
# 使用自定义配置文件
python main.py --config config/production_config.yaml

# 使用无头模式（适合服务器部署）
python main.py --headless
```

### 示例3：查看日志

```bash
# 实时查看日志
tail -f logs/wangwang_rpa.log

# 查看最近的错误日志
grep "ERROR" logs/wangwang_rpa.log
```

## 常见问题

### 1. 浏览器启动失败

**问题**：系统提示无法启动浏览器

**解决方案**：
- 确保已安装 Chrome 浏览器
- 检查 Chrome 版本是否与 Selenium 兼容
- 尝试更新 Selenium：`pip install --upgrade selenium`

### 2. 登录状态丢失

**问题**：每次启动都需要重新登录

**解决方案**：
- 检查 `browser_data` 目录是否有写入权限
- 确保浏览器数据目录未被删除
- 检查 1688 是否更新了登录机制

### 3. 消息发送失败

**问题**：自动回复消息发送失败

**解决方案**：
- 检查网络连接
- 确认旺旺页面元素选择器是否变化
- 查看日志文件获取详细错误信息
- 系统会自动重试2次

### 4. 自动回复不生效

**问题**：配置了规则但没有自动回复

**解决方案**：
- 检查 `config/config.yaml` 中 `auto_reply.enabled` 是否为 `true`
- 确认 `auto_reply_rules.yaml` 文件格式正确
- 检查关键词是否匹配（区分大小写）
- 查看日志确认规则是否加载成功

## 注意事项

1. **账号安全**：
   - 请妥善保管 `browser_data` 目录，其中包含登录凭证
   - 不要在公共环境运行系统
   - 定期更改密码

2. **使用限制**：
   - 遵守 1688 平台的使用规则
   - 避免频繁操作导致账号异常
   - 建议在测试环境先验证功能

3. **性能优化**：
   - 无头模式性能更好，适合长期运行
   - 定期清理日志文件避免占用过多磁盘空间
   - 根据实际需求调整消息检查间隔

4. **维护建议**：
   - 定期查看日志文件
   - 及时更新依赖包
   - 备份配置文件和自动回复规则

## 技术架构

系统采用模块化设计，主要组件包括：

- **浏览器控制器**：基于 Selenium WebDriver，负责浏览器操作
- **消息处理器**：处理消息的接收、解析和发送
- **会话管理器**：管理多个聊天会话的状态
- **自动回复引擎**：基于关键词匹配的智能回复系统
- **配置管理器**：统一管理系统配置
- **日志系统**：完整的日志记录和管理

## 许可证

本项目采用 MIT 许可证

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m '添加某个功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 提交 Issue
- 发起 Pull Request
- 项目链接：[GitHub URL]

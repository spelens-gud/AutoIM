# Changelog

All notable changes to this project will be documented in this file. See [conventional commits](https://www.conventionalcommits.org/) for commit guidelines.

---
## [unreleased]

### Features

- **消息处理**: 新增获取聊天记录功能
  - 添加 `get_chat_messages()` 方法，支持获取与指定联系人的历史聊天消息
  - 添加 `_parse_chat_message_element()` 内部方法，用于解析聊天记录中的消息元素
  - 支持自动滚动加载历史消息
  - 支持限制获取的消息数量（1-500条）
  - 自动识别消息方向（发送/接收）和消息类型（文本/图片/系统）

- **API 接口**: 新增获取聊天记录 API
  - 添加 `GET /api/message/history/<contact_id>` 接口
  - 支持通过 URL 参数指定最大消息数量
  - 返回完整的消息列表，包含时间戳、发送者、内容等信息
  - 完善的错误处理和参数验证

### Documentation

- 添加获取聊天消息功能说明文档
- 更新 API 文档，添加聊天记录接口说明
- 添加 API 使用指南 - 获取聊天记录
- 提供 Python、JavaScript、Shell 等多种语言的使用示例

### Tests

- 添加 `get_chat_messages()` 方法的单元测试
- 添加 `_parse_chat_message_element()` 方法的单元测试
- 测试覆盖成功场景、空消息列表、消息数量限制等多种情况

### Other

- init - ([af6ce0f](https://github.com/Anniext/demo/commit/af6ce0f1de8a767a86622e5b85d3500924234ecb)) - xt
- init - ([7bbe972](https://github.com/Anniext/demo/commit/7bbe97256eef23e3bb54fa9412aaf26bcb75cb39)) - xt



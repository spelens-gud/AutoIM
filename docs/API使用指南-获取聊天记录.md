# API 使用指南 - 获取聊天记录

## 概述

本文档介绍如何使用 API 接口获取与指定联系人的聊天记录。

## 接口信息

**接口地址**: `GET /api/message/history/<contact_id>`

**功能**: 获取与指定联系人的历史聊天消息

**参数**:
- `contact_id` (路径参数): 联系人ID或联系人名称
- `max_messages` (查询参数): 最多获取的消息数量，范围 1-500，默认 100

## 快速开始

### 1. 启动 API 服务

```bash
# 启动 API 服务并自动启动 RPA 系统
python api_server.py --auto-start

# 或者使用无头模式
python api_server.py --auto-start --headless
```

服务将在 `http://localhost:5001` 启动。

### 2. 使用 curl 测试

```bash
# 获取默认数量（100条）的聊天记录
curl "http://localhost:5001/api/message/history/某某旗舰店"

# 获取最近50条聊天记录
curl "http://localhost:5001/api/message/history/某某旗舰店?max_messages=50"

# 使用 URL 编码的联系人名称
curl "http://localhost:5001/api/message/history/%E6%9F%90%E6%9F%90%E6%97%97%E8%88%B0%E5%BA%97"
```

### 3. 使用 Python 测试脚本

```bash
# 运行交互式测试脚本
python test_api_chat_history.py

# 查看 curl 命令示例
python test_api_chat_history.py --curl
```

## 响应格式

### 成功响应

```json
{
  "success": true,
  "data": {
    "contact_id": "某某旗舰店",
    "count": 15,
    "messages": [
      {
        "message_id": "msg_001",
        "contact_id": "shop_123",
        "contact_name": "某某旗舰店",
        "content": "你好，请问有货吗？",
        "message_type": "text",
        "timestamp": "2025-11-26T18:50:00",
        "is_sent": true,
        "is_auto_reply": false
      },
      {
        "message_id": "msg_002",
        "contact_id": "shop_123",
        "contact_name": "某某旗舰店",
        "content": "您好，有货的",
        "message_type": "text",
        "timestamp": "2025-11-26T18:51:00",
        "is_sent": false,
        "is_auto_reply": false
      }
    ]
  }
}
```

### 错误响应

```json
{
  "success": false,
  "message": "RPA系统未启动"
}
```

## 使用示例

### Python 示例

```python
import requests
from urllib.parse import quote

BASE_URL = "http://localhost:5001"

# 联系人名称（需要 URL 编码）
contact_id = "某某旗舰店"
encoded_contact_id = quote(contact_id)

# 获取聊天记录
response = requests.get(
    f"{BASE_URL}/api/message/history/{encoded_contact_id}",
    params={"max_messages": 50}
)

data = response.json()

if data["success"]:
    messages = data["data"]["messages"]
    print(f"获取到 {len(messages)} 条消息")
    
    for msg in messages:
        sender = "我" if msg["is_sent"] else msg["contact_name"]
        print(f"{sender}: {msg['content']}")
else:
    print(f"错误: {data['message']}")
```

### JavaScript 示例

```javascript
const BASE_URL = "http://localhost:5001";

// 联系人名称（需要 URL 编码）
const contactId = "某某旗舰店";
const encodedContactId = encodeURIComponent(contactId);

// 获取聊天记录
fetch(`${BASE_URL}/api/message/history/${encodedContactId}?max_messages=50`)
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      const messages = data.data.messages;
      console.log(`获取到 ${messages.length} 条消息`);
      
      messages.forEach(msg => {
        const sender = msg.is_sent ? "我" : msg.contact_name;
        console.log(`${sender}: ${msg.content}`);
      });
    } else {
      console.error(`错误: ${data.message}`);
    }
  });
```

### Shell 脚本示例

```bash
#!/bin/bash

# 配置
BASE_URL="http://localhost:5001"
CONTACT_ID="某某旗舰店"
MAX_MESSAGES=50

# URL 编码联系人名称
ENCODED_CONTACT_ID=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$CONTACT_ID'))")

# 获取聊天记录
curl -s "${BASE_URL}/api/message/history/${ENCODED_CONTACT_ID}?max_messages=${MAX_MESSAGES}" \
  | jq -r '.data.messages[] | "\(.is_sent | if . then "我" else .contact_name end): \(.content)"'
```

## 注意事项

1. **联系人名称编码**: 如果联系人名称包含中文或特殊字符，需要进行 URL 编码

2. **消息数量限制**: `max_messages` 参数范围为 1-500，超出范围会返回错误

3. **执行时间**: 获取大量历史消息可能需要较长时间（10-30秒），建议设置合理的超时时间

4. **RPA 状态**: 调用此接口前，确保 RPA 系统已启动并登录成功

5. **浏览器切换**: 该接口会切换到指定联系人的聊天窗口，可能会影响其他正在进行的操作

6. **消息顺序**: 返回的消息按时间顺序排列（从旧到新）

## 错误处理

### 常见错误

| 错误信息 | 原因 | 解决方法 |
|---------|------|---------|
| RPA系统未启动 | RPA 系统未运行 | 先调用 `/api/rpa/start` 启动系统 |
| 无法切换到聊天iframe | 页面结构变化或加载失败 | 检查网络连接，重启 RPA 系统 |
| 无法切换到联系人的聊天窗口 | 联系人不存在或名称错误 | 确认联系人名称正确 |
| max_messages 参数必须在 1-500 之间 | 参数超出范围 | 调整参数值 |

### 错误处理示例

```python
import requests
from urllib.parse import quote

def get_chat_history(contact_id, max_messages=50):
    """获取聊天记录，包含错误处理。"""
    try:
        encoded_contact_id = quote(contact_id)
        url = f"http://localhost:5001/api/message/history/{encoded_contact_id}"
        
        response = requests.get(
            url,
            params={"max_messages": max_messages},
            timeout=60  # 设置超时时间
        )
        
        data = response.json()
        
        if data["success"]:
            return data["data"]["messages"]
        else:
            print(f"获取失败: {data['message']}")
            return None
            
    except requests.exceptions.Timeout:
        print("请求超时，请稍后重试")
        return None
    except requests.exceptions.ConnectionError:
        print("无法连接到 API 服务，请确保服务已启动")
        return None
    except Exception as e:
        print(f"发生错误: {e}")
        return None

# 使用示例
messages = get_chat_history("某某旗舰店", max_messages=50)
if messages:
    print(f"成功获取 {len(messages)} 条消息")
```

## 性能优化建议

1. **合理设置消息数量**: 根据实际需求设置 `max_messages`，避免获取过多消息

2. **缓存结果**: 对于不经常变化的历史消息，可以在客户端缓存结果

3. **异步调用**: 在前端应用中使用异步调用，避免阻塞用户界面

4. **批量处理**: 如需获取多个联系人的聊天记录，建议串行处理，避免并发请求

## 完整工作流程

```python
import requests
import time

BASE_URL = "http://localhost:5001"

# 1. 检查服务状态
response = requests.get(f"{BASE_URL}/api/health")
print("服务状态:", response.json())

# 2. 启动 RPA 系统（如果未启动）
response = requests.get(f"{BASE_URL}/api/rpa/status")
if not response.json()["data"]["is_running"]:
    print("启动 RPA 系统...")
    requests.post(f"{BASE_URL}/api/rpa/start")
    time.sleep(5)  # 等待启动完成

# 3. 获取会话列表
response = requests.get(f"{BASE_URL}/api/session/list?active_only=true")
sessions = response.json()["data"]["sessions"]
print(f"活跃会话数: {len(sessions)}")

# 4. 获取第一个会话的聊天记录
if sessions:
    contact_id = sessions[0]["contact_name"]
    print(f"获取 {contact_id} 的聊天记录...")
    
    response = requests.get(
        f"{BASE_URL}/api/message/history/{contact_id}",
        params={"max_messages": 50}
    )
    
    messages = response.json()["data"]["messages"]
    print(f"获取到 {len(messages)} 条消息")
    
    # 显示最近5条消息
    for msg in messages[-5:]:
        sender = "我" if msg["is_sent"] else msg["contact_name"]
        print(f"{sender}: {msg['content']}")
```

## 相关文档

- [API 完整文档](../API.md)
- [获取聊天消息功能说明](./获取聊天消息功能说明.md)
- [消息处理器文档](../src/core/message_handler.py)

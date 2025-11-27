# 旺旺RPA Web API 文档

## 概述

旺旺RPA系统提供 RESTful API 接口，方便通过 HTTP 请求控制和使用系统功能。

**基础URL**: `http://localhost:5000`

**响应格式**: JSON

## API 接口列表

### 1. 健康检查

检查API服务是否正常运行。

**接口**: `GET /api/health`

**响应示例**:
```json
{
  "status": "ok",
  "timestamp": "2025-11-26T19:00:00",
  "service": "旺旺RPA API"
}
```

---

### 2. 启动RPA系统

启动旺旺RPA系统，开始监控消息。

**接口**: `POST /api/rpa/start`

**请求体**:
```json
{
  "config_path": "config/config.yaml",  // 可选，配置文件路径
  "headless": false                      // 可选，是否使用无头模式
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "RPA系统启动成功",
  "config": {
    "config_path": "config/config.yaml",
    "headless": false
  }
}
```

**curl 示例**:
```bash
curl -X POST http://localhost:5000/api/rpa/start \
  -H "Content-Type: application/json" \
  -d '{"headless": false}'
```

---

### 3. 停止RPA系统

停止旺旺RPA系统。

**接口**: `POST /api/rpa/stop`

**响应示例**:
```json
{
  "success": true,
  "message": "RPA系统已停止"
}
```

**curl 示例**:
```bash
curl -X POST http://localhost:5000/api/rpa/stop
```

---

### 4. 获取系统状态

获取RPA系统当前运行状态。

**接口**: `GET /api/rpa/status`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "is_running": true,
    "total_sessions": 5,
    "active_sessions": 3
  }
}
```

**curl 示例**:
```bash
curl http://localhost:5000/api/rpa/status
```

---

### 5. 发送消息

向指定联系人或店铺发送消息。

**接口**: `POST /api/message/send`

**请求体**:
```json
{
  "contact_id": "店铺名称或联系人ID",
  "content": "消息内容",
  "retry_times": 2,    // 可选，重试次数，默认2
  "retry_delay": 1     // 可选，重试延迟（秒），默认1
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "消息发送成功",
  "data": {
    "contact_id": "某某旗舰店",
    "content": "你好，请问有货吗？",
    "timestamp": "2025-11-26T19:00:00"
  }
}
```

**curl 示例**:
```bash
curl -X POST http://localhost:5000/api/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "某某旗舰店",
    "content": "你好，请问有货吗？"
  }'
```

---

### 6. 检查新消息

检查是否有新消息到达。

**接口**: `GET /api/message/check`

**响应示例**:
```json
{
  "success": true,
  "data": {
    "count": 2,
    "messages": [
      {
        "message_id": "msg_001",
        "contact_id": "shop_123",
        "contact_name": "某某旗舰店",
        "content": "您好，有货的",
        "message_type": "text",
        "timestamp": "2025-11-26T19:00:00",
        "is_sent": false
      }
    ]
  }
}
```

**curl 示例**:
```bash
curl http://localhost:5000/api/message/check
```

---

### 7. 获取聊天记录

获取与指定联系人的聊天记录。

**接口**: `GET /api/message/history/<contact_id>`

**路径参数**:
- `contact_id`: 联系人ID或联系人名称

**查询参数**:
- `max_messages`: 最多获取的消息数量（1-500），默认100

**响应示例**:
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
        "is_sent": true
      },
      {
        "message_id": "msg_002",
        "contact_id": "shop_123",
        "contact_name": "某某旗舰店",
        "content": "您好，有货的",
        "message_type": "text",
        "timestamp": "2025-11-26T18:51:00",
        "is_sent": false
      }
    ]
  }
}
```

**curl 示例**:
```bash
# 获取默认数量（100条）的聊天记录
curl http://localhost:5000/api/message/history/某某旗舰店

# 获取最近50条聊天记录
curl "http://localhost:5000/api/message/history/某某旗舰店?max_messages=50"

# URL编码的联系人名称
curl http://localhost:5000/api/message/history/%E6%9F%90%E6%9F%90%E6%97%97%E8%88%B0%E5%BA%97
```

**注意事项**:
- 消息按时间顺序排列（从旧到新）
- 如果联系人名称包含特殊字符，需要进行URL编码
- 该接口会切换到指定联系人的聊天窗口并获取消息
- 获取大量历史消息可能需要较长时间

---

### 8. 获取会话列表

获取所有会话或仅活跃会话。

**接口**: `GET /api/session/list`

**查询参数**:
- `active_only`: 是否只返回活跃会话（true/false），默认false

**响应示例**:
```json
{
  "success": true,
  "data": {
    "count": 3,
    "sessions": [
      {
        "contact_id": "shop_123",
        "contact_name": "某某旗舰店",
        "last_message_time": "2025-11-26T19:00:00",
        "last_activity_time": "2025-11-26T19:05:00",
        "message_count": 10,
        "is_active": true
      }
    ]
  }
}
```

**curl 示例**:
```bash
# 获取所有会话
curl http://localhost:5000/api/session/list

# 只获取活跃会话
curl http://localhost:5000/api/session/list?active_only=true
```

---

### 8. 获取自动回复规则

## 错误响应

所有接口在发生错误时返回统一格式：

```json
{
  "success": false,
  "message": "错误描述信息"
}
```

**常见HTTP状态码**:
- `200`: 成功
- `400`: 请求参数错误
- `404`: 接口不存在
- `500`: 服务器内部错误

---

## 使用示例

### Python 示例

```python
import requests

# 基础URL
BASE_URL = "http://localhost:5000"

# 1. 启动RPA系统
response = requests.post(f"{BASE_URL}/api/rpa/start", json={
    "headless": False
})
print(response.json())

# 2. 发送消息
response = requests.post(f"{BASE_URL}/api/message/send", json={
    "contact_id": "某某旗舰店",
    "content": "你好，请问有货吗？"
})
print(response.json())

# 3. 检查新消息
response = requests.get(f"{BASE_URL}/api/message/check")
print(response.json())

# 4. 获取聊天记录
response = requests.get(f"{BASE_URL}/api/message/history/某某旗舰店", params={
    "max_messages": 50
})
print(response.json())

# 5. 获取系统状态
response = requests.get(f"{BASE_URL}/api/rpa/status")
print(response.json())

# 6. 停止RPA系统
response = requests.post(f"{BASE_URL}/api/rpa/stop")
print(response.json())
```

### JavaScript 示例

```javascript
const BASE_URL = "http://localhost:5000";

// 1. 启动RPA系统
fetch(`${BASE_URL}/api/rpa/start`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ headless: false })
})
.then(res => res.json())
.then(data => console.log(data));

// 2. 发送消息
fetch(`${BASE_URL}/api/message/send`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    contact_id: "某某旗舰店",
    content: "你好，请问有货吗？"
  })
})
.then(res => res.json())
.then(data => console.log(data));

// 3. 检查新消息
fetch(`${BASE_URL}/api/message/check`)
.then(res => res.json())
.then(data => console.log(data));
```

---

## 启动API服务

```bash
# 安装依赖
pip install flask flask-cors

# 启动服务
python api_server.py
```

服务将在 `http://localhost:5000` 启动。

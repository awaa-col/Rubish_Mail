[English](en/APIDocumentation.md)

# API 完整文档

## WebSocket API

### 端点

```
ws://your-server:8000/ws/monitor
```

生产环境请使用 WSS (WebSocket Secure):
```
wss://your-server:8000/ws/monitor
```

---

## 连接流程

```
客户端                                服务端
  |                                     |
  |------ 1. WebSocket连接请求 -------->|
  |                                     |
  |<----- 2. 连接建立(101 Switching) ---|
  |                                     |
  |------ 3. 发送MonitorRequest ------->|
  |                                     |
  |       4. 验证API_KEY               |
  |       5. 验证邮箱域名               |
  |       6. 启动IMAP监控               |
  |                                     |
  |<----- 7. MonitorStartMessage -------|
  |                                     |
  |       8. 等待邮件...                |
  |                                     |
  |<----- 9. EmailReceivedMessage ------|  (匹配到邮件时)
  |                                     |
  |<----- 10. HeartbeatMessage ---------|  (每30秒)
  |                                     |
  |------ 11. 断开连接 ---------------->|
  |                                     |
```

---

## 请求格式

### MonitorRequest

客户端连接后需发送的JSON:

```json
{
  "api_key": "your-secret-api-key",
  "email": "user@example.com",
  "rules": [
    {
      "type": "keyword",
      "patterns": ["验证码", "verification"],
      "search_in": ["subject", "body"]
    }
  ]
}
```

#### 字段详解

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `api_key` | string | ✅ | API密钥,用于身份验证 |
| `email` | string | ✅ | 要监控的邮箱地址,必须是EmailStr格式 |
| `rules` | array | ✅ | 匹配规则数组,至少包含1个规则 |

#### Rule对象

| 字段 | 类型 | 可选值 | 必填 | 说明 |
|------|------|--------|------|------|
| `type` | string | `keyword`, `regex` | ✅ | 匹配类型 |
| `patterns` | string[] | - | ✅ | 匹配模式列表,至少1个 |
| `search_in` | string[] | `sender`, `subject`, `body` | ❌ | 搜索范围,默认全部 |

---

## 响应消息

服务端会推送以下4种消息:

### 1. MonitorStartMessage

监控启动确认

```json
{
  "type": "monitor_start",
  "data": {
    "message": "监控已启动",
    "email": "user@example.com",
    "rules_count": 2
  }
}
```

**字段说明**:
- `message`: 状态消息
- `email`: 正在监控的邮箱
- `rules_count`: 规则数量

---

### 2. EmailReceivedMessage

收到匹配的邮件

```json
{
  "type": "email_received",
  "data": {
    "sender": "noreply@github.com",
    "sender_name": "GitHub",
    "subject": "Your verification code",
    "body": "Your code is: 123456\n\nPlease enter this code...",
    "html_body": "<html><body>Your code is: 123456...</body></html>",
    "received_time": "2025-10-08T10:30:45.123456",
    "matched_rule": "关键词 'verification' 匹配于主题"
  }
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `sender` | string | 发件人邮箱地址 |
| `sender_name` | string \| null | 发件人姓名(如果有) |
| `subject` | string | 邮件主题 |
| `body` | string | 邮件正文(纯文本) |
| `html_body` | string \| null | HTML格式正文(如果有) |
| `received_time` | string | 接收时间(ISO 8601格式) |
| `matched_rule` | string | 匹配的规则描述 |

---

### 3. ErrorMessage

错误通知

```json
{
  "type": "error",
  "data": {
    "code": "INVALID_DOMAIN",
    "message": "不支持的邮箱域名,仅支持: example.com"
  }
}
```

**错误代码**:

| Code | 说明 | HTTP状态码 |
|------|------|-----------|
| `INVALID_REQUEST` | 请求格式错误 | 1003 |
| `UNAUTHORIZED` | API密钥无效 | 1008 |
| `INVALID_DOMAIN` | 邮箱域名不匹配 | 1008 |
| `TOO_MANY_CONNECTIONS` | 超过最大连接数 | 1008 |
| `SERVER_ERROR` | 服务器内部错误 | 1011 |

---

### 4. HeartbeatMessage

心跳保活

```json
{
  "type": "heartbeat",
  "data": {
    "timestamp": "2025-10-08T10:31:00.000000"
  }
}
```

**说明**: 
- 每30秒发送一次(如果期间没有其他消息)
- 客户端收到后无需响应
- 用于检测连接状态

---

## 匹配规则详解

### 关键词匹配 (keyword)

**特点**:
- 不区分大小写
- 精确子串匹配
- OR逻辑(任意一个匹配即可)

**示例1**: 匹配包含"验证码"或"code"

```json
{
  "type": "keyword",
  "patterns": ["验证码", "code"],
  "search_in": ["subject", "body"]
}
```

匹配:
- ✅ "您的验证码是123456"
- ✅ "Your verification code is 123456"
- ✅ "CODE: ABC123"
- ❌ "Please verify your account" (没有"验证码"或"code")

**示例2**: 只在主题中搜索

```json
{
  "type": "keyword",
  "patterns": ["重要通知"],
  "search_in": ["subject"]
}
```

---

### 正则表达式匹配 (regex)

**特点**:
- 支持完整的Python正则语法
- 默认不区分大小写
- OR逻辑(任意一个匹配即可)

**示例1**: 匹配6位数字验证码

```json
{
  "type": "regex",
  "patterns": ["\\d{6}"],
  "search_in": ["body"]
}
```

匹配:
- ✅ "您的验证码: 123456"
- ✅ "code is 987654 please"
- ❌ "code is 12345" (只有5位)

**示例2**: 匹配特定格式的验证码

```json
{
  "type": "regex",
  "patterns": ["验证码[^\\d]*(\\d{6})", "code:\\s*([A-Z0-9]{6})"],
  "search_in": ["body"]
}
```

匹配:
- ✅ "验证码: 123456"
- ✅ "验证码是 789012"
- ✅ "code: ABC123"
- ✅ "code:XYZ789"

**示例3**: 匹配特定发件人域名

```json
{
  "type": "regex",
  "patterns": ["@github\\.com$", "@gitlab\\.com$"],
  "search_in": ["sender"]
}
```

匹配:
- ✅ "noreply@github.com"
- ✅ "support@gitlab.com"
- ❌ "admin@example.com"

**注意**: 正则中的反斜杠需要转义 `\\`

---

### 搜索范围 (search_in)

可选值:
- `sender`: 发件人邮箱地址
- `subject`: 邮件主题
- `body`: 邮件正文(纯文本)

**示例**: 组合搜索

```json
{
  "type": "keyword",
  "patterns": ["urgent"],
  "search_in": ["subject", "sender"]
}
```

匹配:
- ✅ 主题: "URGENT: Please verify"
- ✅ 发件人: "urgent-support@example.com"
- ❌ 正文包含"urgent"但主题和发件人不包含

---

### 多规则组合

可以定义多个规则,只要**任意一个**规则匹配即可(OR逻辑):

```json
{
  "api_key": "...",
  "email": "...",
  "rules": [
    {
      "type": "keyword",
      "patterns": ["验证码"],
      "search_in": ["subject"]
    },
    {
      "type": "regex",
      "patterns": ["\\d{6}"],
      "search_in": ["body"]
    }
  ]
}
```

**逻辑**: `(主题包含"验证码") OR (正文包含6位数字)`

---

## 高级用例

### 用例1: 提取验证码

```python
import re

def extract_code(email_body):
    # 尝试多种验证码格式
    patterns = [
        r'验证码[^\d]*(\d{6})',
        r'verification code[^\w]*([A-Z0-9]{6})',
        r'code:\s*(\d{4,6})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, email_body, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

# 使用
async for message in websocket:
    data = json.loads(message)
    if data["type"] == "email_received":
        code = extract_code(data["data"]["body"])
        print(f"验证码: {code}")
```

---

### 用例2: 超时处理

```python
import asyncio

async def wait_for_email(timeout=60):
    try:
        async with websockets.connect("...") as ws:
            await ws.send(json.dumps(request))
            
            async with asyncio.timeout(timeout):  # Python 3.11+
                async for message in ws:
                    data = json.loads(message)
                    if data["type"] == "email_received":
                        return data["data"]
    except asyncio.TimeoutError:
        print("等待超时,未收到邮件")
        return None
```

---

### 用例3: 重连机制

```python
async def monitor_with_retry(max_retries=3):
    for attempt in range(max_retries):
        try:
            async with websockets.connect("...") as ws:
                await ws.send(json.dumps(request))
                async for message in ws:
                    # 处理消息...
                    pass
        except websockets.ConnectionClosed:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避
                continue
            else:
                raise
```

---

### 用例4: 过滤特定发件人

```python
# 只接收GitHub的邮件
request = {
    "api_key": "...",
    "email": "...",
    "rules": [{
        "type": "regex",
        "patterns": ["@github\\.com$"],
        "search_in": ["sender"]
    }]
}
```

---

## HTTP API

### GET /

健康检查端点

**请求**:
```
GET / HTTP/1.1
Host: localhost:8000
```

**响应**:
```json
{
  "service": "Rubbish Mail",
  "version": "2.0.0",
  "status": "running",
  "smtp": {
    "host": "0.0.0.0",
    "port": 8025,
    "domain": "example.com"
  },
  "connections": {
    "active": 3,
    "max": 10,
    "monitored_emails": ["test@example.com"]
  },
  "timestamp": "2025-10-08T10:30:00.123456"
}
```

**状态码**: `200 OK`

---

## 黑名单管理 API

> **认证要求**: 所有黑名单API都需要Bearer Token认证

在请求头中添加:
```
Authorization: Bearer YOUR_API_KEY
```

### GET /api/blacklist

获取黑名单统计信息

**请求**:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/blacklist
```

**响应**:
```json
{
  "blocked_ips_count": 3,
  "blocked_domains_count": 5,
  "whitelist_domains_count": 10,
  "blocked_ips": ["91.92.242.57", "78.153.140.207", "1.2.3.4"],
  "blocked_domains": ["test.com", "spam.com"],
  "whitelist_domains": ["mailgun.co", "mg.replit.com", "github.com"]
}
```

**状态码**:
- `200 OK`: 成功
- `401 Unauthorized`: API密钥无效

---

### GET /api/blacklist/detail

获取详细黑名单列表(包含拦截原因、时间、计数)

**请求**:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/blacklist/detail
```

**响应**:
```json
{
  "blocked_ips": {
    "91.92.242.57": {
      "reason": "垃圾邮件发送者",
      "added_at": "2025-10-10T10:58:08.072000",
      "count": 5
    },
    "1.2.3.4": {
      "reason": "发送超大邮件 (15.23MB)",
      "added_at": "2025-10-10T11:20:30.123456",
      "count": 1
    }
  },
  "blocked_domains": {
    "test.com": {
      "reason": "未授权域名",
      "added_at": "2025-10-10T10:58:08.072000",
      "count": 8
    },
    "spam.com": {
      "reason": "垃圾邮件域名",
      "added_at": "2025-10-10T12:00:00.000000",
      "count": 3
    }
  },
  "whitelist_domains": ["mailgun.co", "mg.replit.com"]
}
```

**字段说明**:
- `reason`: 拉黑原因
- `added_at`: 添加到黑名单的时间(ISO 8601格式)
- `count`: 拦截次数(每次尝试连接/发送都会增加)

**状态码**:
- `200 OK`: 成功
- `401 Unauthorized`: API密钥无效

---

### POST /api/blacklist/ip/{ip}

添加IP到黑名单

**请求**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8000/api/blacklist/ip/1.2.3.4?reason=垃圾邮件发送者"
```

**URL参数**:
- `ip` (路径参数): 要拉黑的IP地址
- `reason` (查询参数,可选): 拉黑原因,默认为"手动添加"

**响应** (首次添加):
```json
{
  "success": true,
  "message": "已添加IP到黑名单: 1.2.3.4",
  "ip": "1.2.3.4",
  "reason": "垃圾邮件发送者"
}
```

**响应** (已存在):
```json
{
  "success": false,
  "message": "IP已在黑名单中: 1.2.3.4",
  "ip": "1.2.3.4"
}
```

**状态码**:
- `200 OK`: 成功(无论是否已存在)
- `401 Unauthorized`: API密钥无效

---

### DELETE /api/blacklist/ip/{ip}

从黑名单移除IP

**请求**:
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/blacklist/ip/1.2.3.4
```

**URL参数**:
- `ip` (路径参数): 要移除的IP地址

**响应** (成功):
```json
{
  "success": true,
  "message": "已从黑名单移除IP: 1.2.3.4",
  "ip": "1.2.3.4"
}
```

**状态码**:
- `200 OK`: 成功移除
- `404 Not Found`: IP不在黑名单中
- `401 Unauthorized`: API密钥无效

---

### POST /api/blacklist/domain/{domain}

添加域名到黑名单

**请求**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8000/api/blacklist/domain/spam.com?reason=垃圾邮件域名"
```

**URL参数**:
- `domain` (路径参数): 要拉黑的域名
- `reason` (查询参数,可选): 拉黑原因,默认为"手动添加"

**响应** (首次添加):
```json
{
  "success": true,
  "message": "已添加域名到黑名单: spam.com",
  "domain": "spam.com",
  "reason": "垃圾邮件域名"
}
```

**响应** (已存在):
```json
{
  "success": false,
  "message": "域名已在黑名单中: spam.com",
  "domain": "spam.com"
}
```

**状态码**:
- `200 OK`: 成功(无论是否已存在)
- `401 Unauthorized`: API密钥无效

---

### DELETE /api/blacklist/domain/{domain}

从黑名单移除域名

**请求**:
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/blacklist/domain/spam.com
```

**URL参数**:
- `domain` (路径参数): 要移除的域名

**响应** (成功):
```json
{
  "success": true,
  "message": "已从黑名单移除域名: spam.com",
  "domain": "spam.com"
}
```

**状态码**:
- `200 OK`: 成功移除
- `404 Not Found`: 域名不在黑名单中
- `401 Unauthorized`: API密钥无效

---

## 黑名单工作原理

### 自动拉黑机制

当启用 `blacklist.auto_block: true` 时,系统会自动拉黑陌生发送者:

```
1. 用户监控邮箱 test@example.com
2. 用户设置规则匹配来自 github.com 的邮件
3. 系统学习白名单: github.com ✓
4. 陌生邮件到达 (来自 spam.com)
5. 没有监控连接 → 自动拉黑 spam.com + 发送者IP
6. 下次 spam.com 发邮件 → 554 Sender domain blocked
```

### 白名单学习

系统会自动学习合法域名,不会误拦:

- 当邮件匹配用户规则时,发件人域名会被加入白名单
- 白名单域名的邮件永远不会被自动拉黑
- 可通过 `/api/blacklist` 查看学习到的白名单

### 邮件大小限制

默认10MB限制,超过会自动拉黑:

```
1. 收到15MB邮件
2. 超过限制 → 拒绝: "552 Message too large"
3. 自动拉黑发送者IP
4. 日志: "🚫 拒绝超大邮件: 15.00MB from spam@test.com (1.2.3.4)"
```

### Python示例

```python
import requests

API_BASE = "http://localhost:8000"
API_KEY = "your-api-key"
headers = {"Authorization": f"Bearer {API_KEY}"}

# 1. 查看黑名单统计
response = requests.get(f"{API_BASE}/api/blacklist", headers=headers)
stats = response.json()
print(f"已拉黑 {stats['blocked_ips_count']} 个IP")
print(f"已拉黑 {stats['blocked_domains_count']} 个域名")

# 2. 手动拉黑IP
requests.post(
    f"{API_BASE}/api/blacklist/ip/1.2.3.4",
    params={"reason": "垃圾邮件发送者"},
    headers=headers
)

# 3. 手动拉黑域名
requests.post(
    f"{API_BASE}/api/blacklist/domain/spam.com",
    params={"reason": "垃圾邮件域名"},
    headers=headers
)

# 4. 查看详细信息
response = requests.get(f"{API_BASE}/api/blacklist/detail", headers=headers)
details = response.json()

for ip, info in details['blocked_ips'].items():
    print(f"IP {ip}: {info['reason']} (拦截{info['count']}次)")

# 5. 移除拉黑
requests.delete(f"{API_BASE}/api/blacklist/ip/1.2.3.4", headers=headers)
```

---

## 限制与配额

| 项目 | 默认值 | 配置项 |
|------|--------|--------|
| 最大并发连接数 | 10 | `monitor.max_connections` |
| WebSocket超时 | 300秒 | `monitor.timeout` |
| 邮件大小限制 | 10MB | `smtp.max_message_size` |
| 日志保留天数 | 7天 | `logging.rotation.keep_days` |
| 日志文件大小 | 100MB | `logging.rotation.max_size_mb` |
| 心跳间隔 | 30秒 | 硬编码 |

---

## 错误处理

### 客户端最佳实践

```python
async def robust_monitor():
    try:
        async with websockets.connect(url) as ws:
            # 发送请求
            await ws.send(json.dumps(request))
            
            # 处理消息
            async for message in ws:
                try:
                    data = json.loads(message)
                    
                    if data["type"] == "error":
                        print(f"服务端错误: {data['data']['message']}")
                        break
                    
                    elif data["type"] == "email_received":
                        # 处理邮件...
                        pass
                
                except json.JSONDecodeError:
                    print("消息格式错误")
                    continue
    
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"连接被拒绝: {e.status_code}")
    
    except websockets.exceptions.ConnectionClosed:
        print("连接已关闭")
    
    except Exception as e:
        print(f"未知错误: {e}")
```

---

## 性能考虑

### 推荐配置

**自用场景** (1-5个监控):
```yaml
monitor:
  max_connections: 10
  timeout: 300

smtp:
  max_message_size: 10

blacklist:
  auto_block: true

logging:
  rotation:
    keep_days: 7
    max_size_mb: 100
```

**多用户场景** (10+个监控):
```yaml
monitor:
  max_connections: 50
  timeout: 600

smtp:
  max_message_size: 5  # 更严格的限制

blacklist:
  auto_block: true

logging:
  rotation:
    keep_days: 14
    max_size_mb: 200
```

**开发/测试场景**:
```yaml
monitor:
  max_connections: 5
  timeout: 60

smtp:
  max_message_size: 50  # 允许更大的邮件

blacklist:
  auto_block: false  # 关闭自动拉黑

logging:
  level: "DEBUG"
  rotation:
    keep_days: 3
```

---

## 安全建议

### 1. 使用强API密钥

❌ 弱密钥:
```
API_KEY=123456
```

✅ 强密钥:
```
API_KEY=7f9a2b4e6d8c1a3f5b9e8d7c6a4b2e1f
```

生成方法:
```python
import secrets
print(secrets.token_hex(32))
```

### 2. 使用WSS加密

生产环境配置Nginx反向代理:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /ws/monitor {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

客户端使用:
```python
ws_url = "wss://your-domain.com/ws/monitor"
```

### 3. IP白名单

在防火墙或Nginx中限制访问:

```nginx
location /ws/monitor {
    allow 192.168.1.0/24;
    deny all;
    ...
}
```

---

## 调试技巧

### 开启DEBUG日志

```yaml
logging:
  level: "DEBUG"
```

### 查看详细日志

```bash
# 实时查看日志
tail -f logs/rubbish_mail.log

# 查看黑名单相关日志
tail -f logs/rubbish_mail.log | grep "🚫\|拉黑\|blocked"

# 查看邮件接收日志
tail -f logs/rubbish_mail.log | grep "收到邮件\|匹配成功"
```

### 使用WebSocket测试工具

推荐工具:
- [Postman](https://www.postman.com/) - 支持WebSocket
- [wscat](https://github.com/websockets/wscat) - 命令行工具

示例:
```bash
npm install -g wscat
wscat -c ws://localhost:8000/ws/monitor
```

然后发送JSON请求。

### 测试黑名单API

```bash
# 查看黑名单
curl -H "Authorization: Bearer YOUR_KEY" http://localhost:8000/api/blacklist

# 测试添加IP
curl -X POST -H "Authorization: Bearer YOUR_KEY" \
  "http://localhost:8000/api/blacklist/ip/1.2.3.4?reason=测试"

# 检查是否生效
cat data/blacklist.json | jq .

# 清理测试数据
curl -X DELETE -H "Authorization: Bearer YOUR_KEY" \
  http://localhost:8000/api/blacklist/ip/1.2.3.4
```

### 常见问题排查

**问题1: 黑名单不生效**
```bash
# 1. 检查黑名单文件
cat data/blacklist.json

# 2. 检查配置
cat config.yml | grep -A 2 "blacklist"

# 3. 重启服务
python main.py
```

**问题2: 合法邮件被拦截**
```bash
# 1. 查看详细黑名单
curl -H "Authorization: Bearer YOUR_KEY" \
  http://localhost:8000/api/blacklist/detail | jq .

# 2. 移除误拦的域名
curl -X DELETE -H "Authorization: Bearer YOUR_KEY" \
  http://localhost:8000/api/blacklist/domain/example.com

# 3. 或关闭自动拉黑
# 编辑 config.yml: blacklist.auto_block: false
```

**问题3: 日志文件过大**
```bash
# 查看日志文件大小
du -sh logs/

# 手动清理
rm logs/*.log.*

# 或触发日志轮转(修改文件时间)
touch logs/rubbish_mail.log
```



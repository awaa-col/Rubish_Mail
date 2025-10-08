[中文](../API文档.md)

# Complete API Documentation

## WebSocket API

### Endpoint

```
ws://your-server:8000/ws/monitor
```

In a production environment, please use WSS (WebSocket Secure):
```
wss://your-server:8000/ws/monitor
```

---

## Connection Flow

```
Client                                Server
  |                                     |
  |------ 1. WebSocket Connection Request ------>|
  |                                     |
  |<----- 2. Connection Established (101 Switching) ---|
  |                                     |
  |------ 3. Send MonitorRequest ------->|
  |                                     |
  |       4. Validate API_KEY               |
  |       5. Validate Email Domain          |
  |       6. Start IMAP Monitoring          |
  |                                     |
  |<----- 7. MonitorStartMessage -------|
  |                                     |
  |       8. Waiting for email...           |
  |                                     |
  |<----- 9. EmailReceivedMessage ------|  (When a matching email is found)
  |                                     |
  |<----- 10. HeartbeatMessage ---------|  (Every 30 seconds)
  |                                     |
  |------ 11. Disconnect ---------------->|
  |                                     |
```

---

## Request Format

### MonitorRequest

JSON to be sent by the client after connection:

```json
{
  "api_key": "your-secret-api-key",
  "email": "user@example.com",
  "rules": [
    {
      "type": "keyword",
      "patterns": ["verification code", "verification"],
      "search_in": ["subject", "body"]
    }
  ]
}
```

#### Field Details

| Field     | Type   | Required | Description                               |
|-----------|--------|----------|-------------------------------------------|
| `api_key` | string | ✅       | API key for authentication                |
| `email`   | string | ✅       | Email address to monitor, must be EmailStr format |
| `rules`   | array  | ✅       | Array of matching rules, at least 1 rule  |

#### Rule Object

| Field       | Type     | Possible Values          | Required | Description                             |
|-------------|----------|--------------------------|----------|-----------------------------------------|
| `type`      | string   | `keyword`, `regex`       | ✅       | Matching type                           |
| `patterns`  | string[] | -                        | ✅       | List of matching patterns, at least 1 |
| `search_in` | string[] | `sender`, `subject`, `body` | ❌       | Search scope, defaults to all           |

---

## Response Messages

The server will push the following 4 types of messages:

### 1. MonitorStartMessage

Confirmation that monitoring has started.

```json
{
  "type": "monitor_start",
  "data": {
    "message": "Monitoring has started",
    "email": "user@example.com",
    "rules_count": 2
  }
}
```

**Field Description**:
- `message`: Status message
- `email`: The email being monitored
- `rules_count`: Number of rules

---

### 2. EmailReceivedMessage

Received a matching email.

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
    "matched_rule": "Keyword 'verification' matched in subject"
  }
}
```

**Field Description**:

| Field           | Type         | Description                       |
|-----------------|--------------|-----------------------------------|
| `sender`        | string       | Sender's email address            |
| `sender_name`   | string \| null | Sender's name (if available)      |
| `subject`       | string       | Email subject                     |
| `body`          | string       | Email body (plain text)           |
| `html_body`     | string \| null | HTML format body (if available)   |
| `received_time` | string       | Time received (ISO 8601 format)   |
| `matched_rule`  | string       | Description of the matched rule   |

---

### 3. ErrorMessage

Error notification.

```json
{
  "type": "error",
  "data": {
    "code": "INVALID_DOMAIN",
    "message": "Unsupported email domain, only example.com is supported"
  }
}
```

**Error Codes**:

| Code                   | Description                | HTTP Status Code |
|------------------------|----------------------------|------------------|
| `INVALID_REQUEST`      | Invalid request format     | 1003             |
| `UNAUTHORIZED`         | Invalid API key            | 1008             |
| `INVALID_DOMAIN`       | Email domain does not match| 1008             |
| `TOO_MANY_CONNECTIONS` | Exceeded max connections   | 1008             |
| `SERVER_ERROR`         | Internal server error      | 1011             |

---

### 4. HeartbeatMessage

Keep-alive heartbeat.

```json
{
  "type": "heartbeat",
  "data": {
    "timestamp": "2025-10-08T10:31:00.000000"
  }
}
```

**Description**:
- Sent every 30 seconds (if no other messages are sent)
- Client does not need to respond
- Used to check connection status

---

## Detailed Matching Rules

### Keyword Matching (keyword)

**Features**:
- Case-insensitive
- Exact substring matching
- OR logic (any one match is sufficient)

**Example 1**: Match containing "verification code" or "code"

```json
{
  "type": "keyword",
  "patterns": ["verification code", "code"],
  "search_in": ["subject", "body"]
}
```

Matches:
- ✅ "Your verification code is 123456"
- ✅ "Your verification CODE is 123456"
- ✅ "CODE: ABC123"
- ❌ "Please verify your account" (no "verification code" or "code")

**Example 2**: Search only in the subject

```json
{
  "type": "keyword",
  "patterns": ["Important Notice"],
  "search_in": ["subject"]
}
```

---

### Regular Expression Matching (regex)

**Features**:
- Supports full Python regex syntax
- Case-insensitive by default
- OR logic (any one match is sufficient)

**Example 1**: Match a 6-digit verification code

```json
{
  "type": "regex",
  "patterns": ["\\d{6}"],
  "search_in": ["body"]
}
```

Matches:
- ✅ "Your verification code: 123456"
- ✅ "code is 987654 please"
- ❌ "code is 12345" (only 5 digits)

**Example 2**: Match a verification code in a specific format

```json
{
  "type": "regex",
  "patterns": ["verification code[^\\d]*(\\d{6})", "code:\\s*([A-Z0-9]{6})"],
  "search_in": ["body"]
}
```

Matches:
- ✅ "verification code: 123456"
- ✅ "verification code is 789012"
- ✅ "code: ABC123"
- ✅ "code:XYZ789"

**Example 3**: Match a specific sender domain

```json
{
  "type": "regex",
  "patterns": ["@github\\.com$", "@gitlab\\.com$"],
  "search_in": ["sender"]
}
```

Matches:
- ✅ "noreply@github.com"
- ✅ "support@gitlab.com"
- ❌ "admin@example.com"

**Note**: Backslashes in regex need to be escaped `\\`

---

### Search Scope (search_in)

Possible values:
- `sender`: Sender's email address
- `subject`: Email subject
- `body`: Email body (plain text)

**Example**: Combined search

```json
{
  "type": "keyword",
  "patterns": ["urgent"],
  "search_in": ["subject", "sender"]
}
```

Matches:
- ✅ Subject: "URGENT: Please verify"
- ✅ Sender: "urgent-support@example.com"
- ❌ Body contains "urgent" but subject and sender do not

---

### Multiple Rule Combination

You can define multiple rules. As long as **any one** rule matches, it is considered a match (OR logic):

```json
{
  "api_key": "...",
  "email": "...",
  "rules": [
    {
      "type": "keyword",
      "patterns": ["verification code"],
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

**Logic**: `(subject contains "verification code") OR (body contains 6 digits)`

---

## Advanced Use Cases

### Use Case 1: Extracting Verification Codes

```python
import re

def extract_code(email_body):
    # Try multiple verification code formats
    patterns = [
        r'verification code[^\d]*(\d{6})',
        r'verification code[^\w]*([A-Z0-9]{6})',
        r'code:\s*(\d{4,6})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, email_body, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

# Usage
async for message in websocket:
    data = json.loads(message)
    if data["type"] == "email_received":
        code = extract_code(data["data"]["body"])
        print(f"Verification code: {code}")
```

---

### Use Case 2: Timeout Handling

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
        print("Timeout waiting for email")
        return None
```

---

### Use Case 3: Reconnection Mechanism

```python
import asyncio

async def monitor_with_retry(max_retries=3):
    for attempt in range(max_retries):
        try:
            async with websockets.connect("...") as ws:
                await ws.send(json.dumps(request))
                async for message in ws:
                    # Process message...
                    pass
        except websockets.ConnectionClosed:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                raise
```

---

### Use Case 4: Filtering Specific Senders

```python
# Only receive emails from GitHub
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

Health check endpoint.

**Request**:
```
GET / HTTP/1.1
Host: localhost:8000
```

**Response**:
```json
{
  "service": "Rubbish Mail",
  "status": "running",
  "active_connections": 3,
  "timestamp": "2025-10-08T10:30:00.123456"
}
```

**Status Code**: `200 OK`

---

## Limits and Quotas

| Item                  | Default Value | Configuration Item        |
|-----------------------|---------------|---------------------------|
| Max concurrent connections | 10            | `monitor.max_connections` |
| Email check interval  | 5 seconds     | `monitor.check_interval`  |
| WebSocket timeout     | 300 seconds   | `monitor.timeout`         |
| Heartbeat interval    | 30 seconds    | Hardcoded                 |

---

## Error Handling

### Client Best Practices

```python
async def robust_monitor():
    try:
        async with websockets.connect(url) as ws:
            # Send request
            await ws.send(json.dumps(request))
            
            # Process messages
            async for message in ws:
                try:
                    data = json.loads(message)
                    
                    if data["type"] == "error":
                        print(f"Server error: {data['data']['message']}")
                        break
                    
                    elif data["type"] == "email_received":
                        # Process email...
                        pass
                
                except json.JSONDecodeError:
                    print("Invalid message format")
                    continue
    
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"Connection refused: {e.status_code}")
    
    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")
    
    except Exception as e:
        print(f"Unknown error: {e}")
```

---

## Performance Considerations

### Recommended Configurations

**Personal Use** (1-5 monitors):
```yaml
monitor:
  check_interval: 5
  max_connections: 10
```

**Multi-user Scenario** (10+ monitors):
```yaml
monitor:
  check_interval: 10
  max_connections: 50
```

**High Real-time Scenario**:
```yaml
monitor:
  check_interval: 2  # Note the pressure on the IMAP server
  max_connections: 20
```

---

## Security Recommendations

### 1. Use Strong API Keys

❌ Weak key:
```
API_KEY=123456
```

✅ Strong key:
```
API_KEY=7f9a2b4e6d8c1a3f5b9e8d7c6a4b2e1f
```

Generation method:
```python
import secrets
print(secrets.token_hex(32))
```

### 2. Use WSS Encryption

Configure Nginx reverse proxy in a production environment:

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

Client usage:
```python
ws_url = "wss://your-domain.com/ws/monitor"
```

### 3. IP Whitelisting

Restrict access in your firewall or Nginx:

```nginx
location /ws/monitor {
    allow 192.168.1.0/24;
    deny all;
    ...
}
```

---

## Debugging Tips

### Enable DEBUG Logging

```yaml
logging:
  level: "DEBUG"
```

### View Detailed Logs

```bash
tail -f logs/rubbish_mail.log
```

### Use WebSocket Testing Tools

Recommended tools:
- [Postman](https://www.postman.com/) - Supports WebSocket
- [wscat](https://github.com/websockets/wscat) - Command-line tool

Example:
```bash
npm install -g wscat
wscat -c ws://localhost:8000/ws/monitor
```

Then send the JSON request.

---

Master, the API documentation is complete! If you have any questions, feel free to ask me~ ヾ(≧▽≦*)o

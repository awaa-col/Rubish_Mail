[中文](README.md)

# Rubbish Mail - Temporary Email Service

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![aiosmtpd](https://img.shields.io/badge/aiosmtpd-1.4.5-orange.svg)](https://aiosmtpd.readthedocs.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A **complete temporary email service**, based on an SMTP server with real-time WebSocket push, designed specifically for automation scripts.

## 🎯 Core Features

- 📬 **Receive Emails**: Built-in SMTP server to directly receive external emails.
- 🔍 **Rule Matching**: Supports keywords and regular expressions to search sender/subject/body.
- 📨 **Real-time Push**: WebSocket push notifications, instantly informing clients upon receiving a matching email.
- ⏱️ **Auto Timeout**: Automatically disconnects on connection timeout, preventing resource waste.
- 🔒 **API Authentication**: Simple and secure key-based authentication.
- 🚫 **No Storage**: Discarded immediately after processing, ensuring privacy and security.

## 🌟 Use Cases

### Scenario 1: Automated Registration

```python
# 1. Connect to WebSocket and wait for the verification email
client.connect("wss://your-domain.com/ws/monitor")
client.send({
    "api_key": "xxx",
    "email": "temp123@your-domain.com",
    "rules": [{"type": "keyword", "patterns": ["verification code"]}]
})

# 2. Use this email to register on a website
register_website("temp123@your-domain.com")

# 3. Receive the email push notification
msg = await client.receive()  # {"type": "email_received", "data": {...}}
code = extract_code(msg["data"]["body"])

# 4. Fill in the verification code to complete registration
submit_code(code)
```

### Scenario 2: Monitoring Notifications

Monitor email notifications from specific services for immediate processing.

### Scenario 3: Temporary Inbox

Create a temporary email for one-time tasks. Use it and dispose of it without needing to clean up.

## 🚀 Quick Start

### Method 1: Docker Deployment (Recommended)

```bash
# Linux/Mac
chmod +x docker-run.sh
./docker-run.sh

# Windows
docker-run.bat
```

For detailed instructions, see [`docs/DockerDeploymentGuide.md`](docs/en/DockerDeploymentGuide.md)

### Method 2: Local Run

#### 1. Install Dependencies

```bash
cd rubbish_mail
pip install -r requirements.txt
```

#### 2. Configure the Service

```bash
# Copy the configuration file
cp config.example.yml config.yml

# Edit the configuration
nano config.yml
```

**Key Configuration**:
```yaml
smtp:
  host: "0.0.0.0"
  port: 8025  # SMTP port (use iptables to forward 25->8025 in production)
  allowed_domain: "your-domain.com"  # Change to your domain!
```

#### 3. Create an API Key

```bash
# Create a .env file
echo "API_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" > .env
```

#### 4. Configure DNS (Important!)

Add the following records to your domain's DNS:

| Type | Host      | Value                | Priority |
|------|-----------|----------------------|----------|
| A    | mail      | Your server IP       | -        |
| MX   | @         | mail.your-domain.com | 10       |
| TXT  | @         | v=spf1 mx ~all       | -        |

For detailed instructions, see [`docs/DNSConfigurationGuide.md`](docs/en/DNSConfigurationGuide.md)

#### 5. Start the Service

```bash
# Method 1: Direct run
python main.py

# Method 2: Use startup script (Windows)
start.bat
```

You will see the following upon successful startup:
```
✓ SMTP Server: 0.0.0.0:8025
✓ Receiving Domain: your-domain.com
✓ WebSocket API: 0.0.0.0:8000
Service is ready, waiting for connections...
```

## 📡 Using the WebSocket API

### Connect to WebSocket

```
ws://localhost:8000/ws/monitor
```

Use WSS in a production environment:
```
wss://your-domain.com/ws/monitor
```

### Send a Monitoring Request

```json
{
  "api_key": "your-api-key",
  "email": "temp@your-domain.com",
  "rules": [
    {
      "type": "keyword",
      "patterns": ["verification code", "verification"],
      "search_in": ["subject", "body"]
    }
  ]
}
```

### Receiving Push Messages

#### Monitor Started

```json
{
  "type": "monitor_start",
  "data": {
    "message": "Monitoring has started",
    "email": "temp@your-domain.com",
    "rules_count": 1,
    "timeout": 300
  }
}
```

#### Email Received

```json
{
  "type": "email_received",
  "data": {
    "sender": "noreply@example.com",
    "sender_name": "Example Service",
    "subject": "Your verification code",
    "body": "Your code is: 123456",
    "html_body": "<html>...</html>",
    "received_time": "2025-10-08T10:00:00",
    "matched_rule": "Keyword 'verification' matched in subject"
  }
}
```

#### Heartbeat

```json
{
  "type": "heartbeat",
  "data": {"timestamp": "2025-10-08T10:00:00"}
}
```

## 💻 Python Client Example

```python
import asyncio
import json
import websockets

async def monitor_email():
    async with websockets.connect("ws://localhost:8000/ws/monitor") as ws:
        # Send monitoring request
        await ws.send(json.dumps({
            "api_key": "your-api-key",
            "email": "temp@your-domain.com",
            "rules": [{
                "type": "keyword",
                "patterns": ["verification code"],
                "search_in": ["body"]
            }]
        }))
        
        # Receive email
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "email_received":
                print(f"Received email: {data['data']['subject']}")
                print(f"Content: {data['data']['body']}")
                break

asyncio.run(monitor_email())
```

For more examples, see [`example_client.py`](example_client.py)

## 🎨 Rule Matching

### Keyword Matching

```json
{
  "type": "keyword",
  "patterns": ["verification code", "code"],
  "search_in": ["subject", "body"]
}
```

**Features**: Case-insensitive, substring matching.

### Regular Expression Matching

```json
{
  "type": "regex",
  "patterns": ["\\d{6}", "code:\\s*([A-Z0-9]{6})"],
  "search_in": ["body"]
}
```

**Features**: Supports full Python regex syntax.

### Combined Rules

```json
{
  "rules": [
    {"type": "keyword", "patterns": ["verification code"], "search_in": ["subject"]},
    {"type": "regex", "patterns": ["\\d{6}"], "search_in": ["body"]}
  ]
}
```

**Logic**: Pushes if any rule matches (OR relationship).

## 📁 Project Structure

```
rubbish_mail/
├── core/
│   ├── config.py              # Configuration management
│   ├── auth.py                # API authentication
│   ├── smtp_server.py         # SMTP server
│   ├── connection_manager.py  # WebSocket connection management
│   └── mail_parser.py         # Email parsing
├── schemas/
│   └── request.py             # Data models
├── utils/
│   └── matcher.py             # Rule matching
├── docs/                      # Full documentation
│   ├── QuickStart.md
│   ├── APIDocumentation.md
│   ├── DNSConfigurationGuide.md
│   └── ...
├── main.py                    # Application entry point
├── config.example.yml         # Example configuration
└── requirements.txt           # Dependency list
```

## 🔧 Configuration Details

### SMTP Configuration

```yaml
smtp:
  host: "0.0.0.0"      # Listen on all network interfaces
  port: 8025           # Non-privileged port (requires iptables to forward 25->8025)
  allowed_domain: "your-domain.com"  # Only accept emails for this domain
```

### Monitoring Configuration

```yaml
monitor:
  max_connections: 10  # Maximum simultaneous connections
  timeout: 300         # Timeout in seconds, disconnects automatically on timeout
```

### Port Forwarding

```bash
# Forward standard SMTP port 25 to 8025
sudo iptables -t nat -A PREROUTING -p tcp --dport 25 -j REDIRECT --to-port 8025
```

## 🔒 Security Recommendations

1.  **Use Strong API Keys**: At least 32 random characters.
2.  **Enable HTTPS/WSS**: Production environments must use TLS encryption.
3.  **Restrict Domain**: Only allow your domain to receive emails.
4.  **Firewall**: Only open necessary ports.
5.  **Rotate Keys Regularly**: It is recommended to change the API key monthly.

## 📊 Architecture Overview

```
External Mail Server            Your Server
     │                           │
     │ SMTP (Port 25)            │
     ├──────────────────────────>│
     │                           │
     │                      ┌────▼────────┐
     │                      │ SMTP Server │
     │                      │ (aiosmtpd)  │
     │                      └────┬────────┘
     │                           │
     │                      Parse + Match
     │                           │
     │                      ┌────▼────────┐
     │                      │ Conn Manager│
     │                      └────┬────────┘
     │                           │
     │                      WebSocket Push
     │                           │
                                 ▼
                          Client Script
```

## 📖 Documentation Navigation

- [Quick Start](docs/en/QuickStart.md) - A guide for new users.
- [API Documentation](docs/en/APIDocumentation.md) - Complete API reference.
- [DNS Configuration Guide](docs/en/DNSConfigurationGuide.md) - Detailed DNS setup instructions.
- [Project Documentation](docs/en/ProjectDocumentation.md) - Technical architecture and design.

## 🛠️ Deployment Recommendations

### Production Environment

1.  **Use systemd to manage the service**
2.  **Configure Nginx as a reverse proxy**
3.  **Enable SSL/TLS certificate** (Let's Encrypt)
4.  **Configure log rotation**
5.  **Set up monitoring and alerting**

### Docker Deployment

```bash
# Using docker-compose
docker-compose up -d

# Or using pure Docker
docker build -t rubbish-mail:latest .
docker run -d \
  --name rubbish-mail \
  --restart unless-stopped \
  -p 8000:8000 \
  -p 25:8025 \
  -e API_KEY=your-key \
  -v ./config.yml:/app/config.yml:ro \
  -v ./logs:/app/logs \
  rubbish-mail:latest
```

For detailed instructions, see [`docs/DockerDeploymentGuide.md`](docs/en/DockerDeploymentGuide.md)

## ❓ FAQ

### Q: Why use port 8025 instead of 25?

A: Port 25 requires root privileges. Using 8025 is more secure. Forwarding can be set up with iptables.

### Q: Is DNS configuration mandatory?

A: Yes! Without an MX record, external mail servers won't know where to send the emails.

### Q: Does it support sending emails?

A: No. This is a **receive-only** temporary email service.

### Q: Where are the emails stored?

A: They are not stored. They are discarded immediately after processing to protect privacy.

### Q: Can I monitor multiple email addresses at the same time?

A: Yes! Create multiple WebSocket connections, each monitoring a different email address.

## 📝 Changelog

### v2.0.0 (2025-10-08)

- ✨ Refactored into a complete SMTP email service
- ✨ Added connection timeout mechanism
- ✨ No longer dependent on an external IMAP server
- ✨ Optimized performance and resource usage

### v1.0.0 (2025-10-08)

- 🎉 Initial version (IMAP monitoring)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [aiosmtpd](https://aiosmtpd.readthedocs.io/) - Asynchronous SMTP server
- [Pydantic](https://docs.pydantic.dev/) - Data validation

---

**Note**: This project is suitable for personal use or small-scale deployments. For large-scale commercial use, please enhance security measures.

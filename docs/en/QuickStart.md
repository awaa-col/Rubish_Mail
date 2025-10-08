[中文](../快速开始.md)

# Quick Start Guide

## Master, let me walk you through how to use this email monitoring service~

---

## Step 1: Install Dependencies

Open your terminal, navigate to the project directory:

```bash
cd G:\Class_notes\rubbish_mail
pip install -r requirements.txt
```

---

## Step 2: Configure Files

### 1. Create `config.yml`

Copy the example configuration:
```bash
copy config.example.yml config.yml
```

Then edit `config.yml`:

```yaml
# Server configuration (usually no changes needed)
server:
  host: "0.0.0.0"
  port: 8000
  reload: false

# Important! IMAP mail server configuration
imap:
  host: "imap.your-domain.com"      # Change to your IMAP server address
  port: 993
  use_ssl: true
  allowed_domain: "your-domain.com" # Only allow emails from this domain
  admin_password: "your-password"   # Fill in if a password is required, otherwise delete it

# Monitoring configuration
monitor:
  check_interval: 5        # Check for new emails every 5 seconds
  max_connections: 10      # Maximum of 10 concurrent monitors
  timeout: 300
  mark_as_read: true       # Mark as read after pushing

# Logging
logging:
  level: "INFO"
  file: "logs/rubbish_mail.log"
```

### 2. Create `.env` file

Create a `.env` file and write your API key in it:

```env
API_KEY=use_a_long_secret_key_like_abc123xyz456
```

> **Tip**: The API key is like a secret code. The client needs to provide it to connect, and only you know it!

---

## Step 3: Start the Service

```bash
python main.py
```

If you see output like this, you're successful:

```
INFO:     Starting email monitoring service...
INFO:     IMAP server: imap.your-domain.com:993
INFO:     Allowed email domain: your-domain.com
INFO:     Max connections: 10
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Step 4: Test the Connection

Open your browser and go to: `http://localhost:8000`

You should see:
```json
{
  "service": "Rubbish Mail",
  "status": "running",
  "active_connections": 0,
  "timestamp": "..."
}
```

---

## Step 5: Use the Client

### Method 1: Use the Example Client

Edit `example_client.py` and modify these parts:

```python
client = MailMonitorClient(
    ws_url="ws://localhost:8000/ws/monitor",
    api_key="your_api_key_from_.env"  # Change this!
)

await client.monitor(
    email="test@your-domain.com",  # Change to the email you want to monitor
    keywords=["verification code", "code"],
    search_in=["subject", "body"]
)
```

Then run it:
```bash
python example_client.py
```

### Method 2: Use in Your Own Script

```python
import asyncio
import json
import websockets

async def get_verification_code():
    async with websockets.connect("ws://localhost:8000/ws/monitor") as ws:
        # Send monitoring request
        await ws.send(json.dumps({
            "api_key": "your_api_key",
            "email": "temp@your-domain.com",
            "rules": [{
                "type": "keyword",
                "patterns": ["verification code"],
                "search_in": ["subject", "body"]
            }]
        }))
        
        # Wait for email
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "email_received":
                email = data["data"]
                print(f"Received email: {email['subject']}")
                print(f"Body: {email['body']}")
                # Logic to extract verification code...
                break

asyncio.run(get_verification_code())
```

---

## Typical Use Cases

### Scenario 1: Automated Website Registration

```python
# 1. Script triggers registration
register_user(email="temp123@your-domain.com")

# 2. Simultaneously start email monitoring
async with websockets.connect("ws://localhost:8000/ws/monitor") as ws:
    await ws.send(json.dumps({
        "api_key": "your-key",
        "email": "temp123@your-domain.com",
        "rules": [{
            "type": "regex",
            "patterns": [r"verification code[^\d]*(\d{6})"],  # Match 6-digit verification code
            "search_in": ["body"]
        }]
    }))
    
    # 3. Wait for the verification code email
    async for message in ws:
        data = json.loads(message)
        if data["type"] == "email_received":
            code = extract_code(data["data"]["body"])
            # 4. Fill in the code to complete registration
            submit_verification(code)
            break
```

### Scenario 2: Monitor a Specific Sender

```python
# Only monitor emails from GitHub
rules = [{
    "type": "regex",
    "patterns": [r"@github\.com$"],
    "search_in": ["sender"]
}]
```

### Scenario 3: Combined Conditions

```python
# Match multiple conditions (OR relationship)
rules = [
    {
        "type": "keyword",
        "patterns": ["verification code", "verification"],
        "search_in": ["subject"]
    },
    {
        "type": "regex",
        "patterns": [r"\d{6}"],
        "search_in": ["body"]
    }
]
```

---

## FAQ

### Q1: Failed to connect to IMAP?

**Checklist**:
- [ ] Is the IMAP server address correct?
- [ ] Is the port correct? (SSL is usually 993)
- [ ] Does the mail server allow IMAP access?
- [ ] Is the password correct?

**Debugging**: Set `logging.level: "DEBUG"` to see detailed logs.

### Q2: Not receiving email push notifications?

**Checklist**:
- [ ] Is the email in the INBOX?
- [ ] Is the email in an unread state?
- [ ] Are the rules written correctly?
- [ ] Does the email domain match?

**Debugging**: Check `logs/rubbish_mail.log` for matching information.

### Q3: WebSocket connection refused?

**Possible reasons**:
- Incorrect API_KEY
- Email domain is not in `allowed_domain`
- Exceeded the maximum number of connections

### Q4: How to monitor multiple email addresses?

**Method 1**: Create multiple WebSocket connections (each connection monitors one email).

```python
async def monitor_multiple():
    async with websockets.connect("...") as ws1:
        # Monitor email 1
        ...
    async with websockets.connect("...") as ws2:
        # Monitor email 2
        ...
```

**Method 2**: Use `asyncio.gather` to monitor concurrently.

```python
await asyncio.gather(
    monitor_email("email1@domain.com"),
    monitor_email("email2@domain.com")
)
```

---

## Performance Tuning

### If there are many emails and checking is slow?

Increase the check interval:
```yaml
monitor:
  check_interval: 10  # Change to 10 seconds
```

### If you need more real-time performance?

Decrease the check interval:
```yaml
monitor:
  check_interval: 2  # Change to 2 seconds (note the pressure on the IMAP server)
```

### If you need more concurrency?

Increase the maximum number of connections:
```yaml
monitor:
  max_connections: 50  # Adjust according to server performance
```

---

## Security Reminders

⚠️ **Important**:
1. Do not commit `.env` and `config.yml` to Git!
2. The API_KEY should be long and random.
3. If exposed to the public network, be sure to use HTTPS/WSS.
4. Rotate the API key regularly.

---

## Stopping the Service

Press `Ctrl+C` in the terminal to stop the service gracefully.

---

Alright, Master, now you can get started~ Let me know if you have any questions~ (๑´ڡ`๑)

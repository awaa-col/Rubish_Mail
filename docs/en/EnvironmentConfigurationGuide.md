[中文](../环境配置说明.md)

# Environment Configuration Guide

## Required Files

The project requires the following configuration files to run:

### 1. config.yml

**How to create**:
```bash
copy config.example.yml config.yml
```

**Configuration that must be modified**:

```yaml
imap:
  host: "imap.your-domain.com"      # ← Change to your IMAP server
  allowed_domain: "your-domain.com" # ← Change to your email domain
  admin_password: "your-password"   # ← Fill in if a password is required
```

**Detailed Configuration**:

#### Server Configuration
```yaml
server:
  host: "0.0.0.0"     # Listening address, 0.0.0.0 means all network interfaces
  port: 8000          # Listening port
  reload: false       # Can be set to true for development, false for production
```

#### IMAP Configuration
```yaml
imap:
  host: "imap.example.com"    # IMAP server address
  port: 993                   # IMAP port (usually 993 for SSL)
  use_ssl: true               # Whether to use SSL encryption
  
  allowed_domain: "example.com"  # Only allow emails from this domain to be monitored
  
  # If IMAP authentication is required (optional)
  admin_user: "admin@example.com"
  admin_password: "password123"
```

**How to get IMAP server details**:

- **Gmail**: `imap.gmail.com:993`
  - You need to enable "Less secure app access" or use an app-specific password.

- **Outlook/Hotmail**: `imap-mail.outlook.com:993`

- **QQ Mail**: `imap.qq.com:993`
  - You need to enable IMAP in settings and get an authorization code.

- **163 Mail**: `imap.163.com:993`

- **Self-hosted mail server**: Consult your administrator.

#### Monitoring Configuration
```yaml
monitor:
  check_interval: 5      # Interval for checking new emails (seconds)
                        # Recommended: 2-10 seconds
                        # Too short will increase server load
                        # Too long will reduce real-time performance
  
  max_connections: 10    # Maximum number of concurrent monitoring connections
                        # Recommended: Set according to actual needs
                        # Personal use: 5-10
                        # Multi-user: 20-50
  
  timeout: 300          # WebSocket timeout (seconds)
                        # Recommended: 300-600
  
  mark_as_read: true    # Whether to mark as read after pushing
                        # true: Avoids duplicate pushes, recommended
                        # false: Can receive the same email multiple times
```

#### Logging Configuration
```yaml
logging:
  level: "INFO"                      # Log level
                                    # DEBUG: Detailed debug information
                                    # INFO: General information (recommended)
                                    # WARNING: Warnings
                                    # ERROR: Only errors
  
  file: "logs/rubbish_mail.log"    # Log file path
```

---

### 2. .env File

**How to create**:
Create a `.env` file in the project root directory.

**Example content**:
```env
# API Key (required)
API_KEY=your-secret-api-key-here

# Optional: Multiple API keys (comma-separated)
# API_KEYS=key1,key2,key3
```

**Generate a strong API key**:

Method 1 - Python:
```python
import secrets
print(secrets.token_hex(32))
# Output: 7f9a2b4e6d8c1a3f5b9e8d7c6a4b2e1f...
```

Method 2 - PowerShell:
```powershell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
```

Method 3 - Online Generators:
- https://randomkeygen.com/
- https://www.uuidgenerator.net/

**Security Recommendations**:
- ✅ At least 32 characters
- ✅ Include uppercase, lowercase letters, and numbers
- ✅ Rotate regularly
- ❌ Do not use easily guessable information like birthdays or names
- ❌ Do not commit to a Git repository

---

## Directory Structure

Ensure the following directories exist:

```
rubbish_mail/
├── logs/              ← Log directory (auto-created)
├── core/              ← Core code
├── schemas/           ← Data models
├── utils/             ← Utility functions
├── 白岚/              ← Project documentation
├── config.yml         ← Configuration file (needs to be created)
├── .env               ← Environment variables (needs to be created)
└── ...
```

If the `logs` directory does not exist, it will be created automatically at runtime.

---

## Environment Variable Priority

If both `API_KEY` and `API_KEYS` are configured:

```env
API_KEY=main-key
API_KEYS=key1,key2,key3
```

The effective keys will be: `[main-key, key1, key2, key3]` (after deduplication).

**Use Cases**:
- `API_KEY`: Main key, always valid
- `API_KEYS`: Additional keys, can be used for different clients

---

## Common Configuration Scenarios

### Scenario 1: Local Development

```yaml
# config.yml
server:
  host: "127.0.0.1"  # Only allow local access
  port: 8000
  reload: true       # Auto-reload on code changes

imap:
  host: "imap.gmail.com"
  allowed_domain: "gmail.com"
  admin_password: "your-app-password"

monitor:
  check_interval: 5
  max_connections: 5
  mark_as_read: false  # Allows for repeated testing during development

logging:
  level: "DEBUG"  # Detailed logs
```

### Scenario 2: Production Deployment

```yaml
# config.yml
server:
  host: "0.0.0.0"    # Allow external access
  port: 8000
  reload: false      # Disable hot reload

imap:
  host: "imap.your-domain.com"
  allowed_domain: "your-domain.com"
  admin_password: "${IMAP_PASSWORD}"  # Read from environment variable

monitor:
  check_interval: 10  # Reduce server load
  max_connections: 50
  mark_as_read: true

logging:
  level: "INFO"  # Only log important information
```

### Scenario 3: High Real-time Requirements

```yaml
# config.yml
monitor:
  check_interval: 2   # Check every 2 seconds (note the pressure on the IMAP server!)
  max_connections: 20
  mark_as_read: true
```

---

## Verifying Configuration

### 1. Check Configuration File Syntax

```bash
python -c "import yaml; yaml.safe_load(open('config.yml'))"
```

If there is no output, the syntax is correct.

### 2. Test IMAP Connection

```python
import asyncio
import aioimaplib

async def test_imap():
    client = aioimaplib.IMAP4_SSL(host="imap.example.com", port=993)
    await client.wait_hello_from_server()
    result = await client.login("user@example.com", "password")
    print(result)
    await client.logout()

asyncio.run(test_imap())
```

### 3. Start Service Check

```bash
python main.py
```

Seeing the following output indicates the configuration is correct:
```
INFO:     Starting email monitoring service...
INFO:     IMAP server: imap.example.com:993
INFO:     Allowed email domain: example.com
INFO:     Max connections: 10
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Troubleshooting

### Problem 1: "Configuration file not found"

**Error**:
```
FileNotFoundError: Configuration file not found: config.yml
Please copy config.example.yml to config.yml and fill in the configuration
```

**Solution**:
```bash
copy config.example.yml config.yml
# Then edit config.yml
```

---

### Problem 2: "API_KEY environment variable not found"

**Error**:
```
ValueError: API_KEY environment variable not found
Please create a .env file and set: API_KEY=your-secret-key
```

**Solution**:
Create a `.env` file:
```env
API_KEY=your-key-here
```

---

### Problem 3: "IMAP login failed"

**Error**:
```
ConnectionError: IMAP login failed: ...
```

**Checklist**:
- [ ] Is the IMAP server address correct?
- [ ] Is the port correct? (993 for SSL, 143 for non-SSL)
- [ ] Is the email username correct?
- [ ] Is the password correct? (Some email providers require an app-specific password)
- [ ] Is IMAP enabled on the mail server?

**Gmail Specifics**:
1. Enable 2-Step Verification.
2. Generate an app password: https://myaccount.google.com/apppasswords
3. Use the app password instead of your account password.

---

### Problem 4: "YAML parsing error"

**Error**:
```
yaml.YAMLError: ...
```

**Common causes**:
- Incorrect indentation (YAML uses spaces, not tabs)
- No space after a colon
- Mismatched quotes

**Correct format**:
```yaml
imap:
  host: "imap.example.com"  # ← Space after the colon
  port: 993                 # ← Indented with 2 spaces
```

---

## Configuration Backup

**Important**: The configuration files contain sensitive information, please keep them safe!

**Backup method**:
```bash
# Backup configuration
copy config.yml config.yml.backup
copy .env .env.backup

# Encrypted backup (recommended)
7z a -p config_backup.7z config.yml .env
```

**Do not**:
- ❌ Commit to a public Git repository
- ❌ Send via chat software
- ❌ Share screenshots

---

Master, the configuration guide is complete! If you follow this step by step, you won't go wrong~
If you still have problems, it must be because you didn't read the document carefully! Hmph! (╯‵□′)╯︵┻━┻

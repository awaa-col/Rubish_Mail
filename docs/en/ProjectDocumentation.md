[中文](../项目文档.md)

# Rubbish Mail - Complete Project Documentation

## Project Overview

**Project Name**: Rubbish Mail - Temporary Email Monitoring Service
**Tech Stack**: Python 3.9+ | FastAPI | WebSocket | aioimaplib | Pydantic
**Core Functionality**: Asynchronously monitor specified mailboxes, match emails based on rules, and push them to clients in real-time.

## Architectural Design

### Technology Choices Rationale

1.  **FastAPI**: A modern asynchronous framework with native WebSocket support and excellent performance.
2.  **aioimaplib**: An asynchronous IMAP client that supports concurrent monitoring of multiple mailboxes.
3.  **WebSocket**: For bidirectional real-time communication, suitable for message pushing scenarios.
4.  **Pydantic**: For data validation, ensuring type safety.

### Project Structure

```
rubbish_mail/
├── core/                  # Core business logic
│   ├── config.py         # Configuration management
│   ├── auth.py           # Authentication system
│   └── imap_monitor.py   # IMAP monitoring
├── schemas/              # Data models
│   └── request.py        # Request/response models
├── utils/                # Utility functions
│   └── matcher.py        # Rule matcher
├── logs/                 # Log files
├── main.py               # Application entry point
├── example_client.py     # Client example
└── 白岚/                 # Project documentation
```

---

## Core Module Details

## 1. Configuration Management Module (core/config.py)

### Responsibilities
- Load service configuration from `config.yml`.
- Load sensitive information (API keys) from `.env`.
- Provide a global configuration access interface.

### Classes and Functions

#### `ServerConfig`
**Purpose**: Server configuration.
**Fields**:
- `host: str` - Listening address
- `port: int` - Listening port
- `reload: bool` - Hot reload switch

#### `IMAPConfig`
**Purpose**: IMAP server configuration.
**Fields**:
- `host: str` - IMAP server address
- `port: int` - IMAP port (default 993)
- `use_ssl: bool` - Whether to use SSL
- `allowed_domain: str` - Allowed email domain
- `admin_user: str` - Admin account (optional)
- `admin_password: str` - Admin password (optional)

#### `MonitorConfig`
**Purpose**: Monitoring behavior configuration.
**Fields**:
- `check_interval: int` - Email check interval (seconds)
- `max_connections: int` - Maximum concurrent connections
- `timeout: int` - WebSocket timeout (seconds)
- `mark_as_read: bool` - Whether to mark as read

#### `LoggingConfig`
**Purpose**: Logging configuration.
**Fields**:
- `level: str` - Log level (INFO/DEBUG/...)
- `file: str` - Log file path

#### `Settings`
**Purpose**: Global configuration aggregation.
**Fields**:
- `api_key: str` - Main API key
- `api_keys: List[str]` - List of additional API keys
- `server: ServerConfig`
- `imap: IMAPConfig`
- `monitor: MonitorConfig`
- `logging: LoggingConfig`

**Methods**:
- `get_valid_api_keys() -> List[str]`
  - **Input**: None
  - **Output**: A deduplicated list of all valid API keys.
  - **Purpose**: To merge the main key and additional keys.

#### `load_config(config_path: str = "config.yml") -> Settings`
**Purpose**: Load and parse the configuration file.
**Input**:
- `config_path: str` - Path to the configuration file.
**Output**: `Settings` object.
**Exceptions**:
- `FileNotFoundError` - If the configuration file does not exist.
- `ValueError` - If the API_KEY environment variable is missing.
- `yaml.YAMLError` - If the YAML format is incorrect.

#### `get_settings() -> Settings`
**Purpose**: Get the global configuration instance (singleton pattern).
**Input**: None.
**Output**: `Settings` object.

---

## 2. Data Models Module (schemas/request.py)

### Responsibilities
- Define data structures for all requests/responses.
- Use Pydantic for automatic validation.
- Ensure type safety.

### Data Models

#### `MatchRule`
**Purpose**: Email matching rule.
**Fields**:
- `type: Literal["keyword", "regex"]` - Matching type.
- `patterns: List[str]` - List of matching patterns (OR relationship).
- `search_in: List[str]` - Search scope (sender/subject/body).

**Validators**:
- `validate_patterns()` - Ensures patterns are not empty and strips whitespace.

#### `MonitorRequest`
**Purpose**: Client monitoring request.
**Fields**:
- `api_key: str` - API key.
- `email: EmailStr` - Email address to monitor.
- `rules: List[MatchRule]` - List of matching rules.

**Validators**:
- `validate_email_format()` - Validates email format and converts to lowercase.

#### `EmailContent`
**Purpose**: Email content (pushed to the client).
**Fields**:
- `sender: str` - Sender's email.
- `sender_name: str | None` - Sender's name.
- `subject: str` - Email subject.
- `body: str` - Body (plain text).
- `html_body: str | None` - HTML body.
- `received_time: str` - Time received (ISO format).
- `matched_rule: str` - Description of the matched rule.

#### `WebSocketMessage`
**Purpose**: Base class for WebSocket messages.
**Fields**:
- `type: str` - Message type.
- `data: dict | None` - Message data.

#### `MonitorStartMessage`
**Purpose**: Monitoring start confirmation message.
**Inherits**: `WebSocketMessage`.
**Fields**:
- `type = "monitor_start"`
- `data: dict` - Contains monitoring status information.

#### `EmailReceivedMessage`
**Purpose**: Email received notification.
**Inherits**: `WebSocketMessage`.
**Fields**:
- `type = "email_received"`
- `data: EmailContent` - Email content.

#### `ErrorMessage`
**Purpose**: Error notification.
**Inherits**: `WebSocketMessage`.
**Fields**:
- `type = "error"`
- `data: dict` - Contains code and message.

#### `HeartbeatMessage`
**Purpose**: Keep-alive heartbeat.
**Inherits**: `WebSocketMessage`.
**Fields**:
- `type = "heartbeat"`
- `data: dict` - Contains a timestamp.

---

## 3. Rule Matching Module (utils/matcher.py)

### Responsibilities
- Match email content based on rules.
- Support keywords and regular expressions.
- Return matching results and descriptions.

### Classes and Functions

#### `EmailMatcher`
**Purpose**: Email matcher (static method class).

##### `match(rule: MatchRule, email_data: Dict) -> Tuple[bool, str]`
**Purpose**: Check if an email matches a single rule.
**Input**:
- `rule: MatchRule` - The matching rule.
- `email_data: Dict` - Email data, including sender/subject/body.
**Output**: `(bool, str)` - `(is_match, description)`.
- Match example: `(True, "Keyword 'verification' matched in subject")`.
- No match: `(False, "")`.

**Call Chain**: `match -> _match_keyword | _match_regex`.

##### `_match_keyword(patterns: List[str], search_contents: Dict) -> Tuple[bool, str]`
**Purpose**: Keyword matching (case-insensitive).
**Input**:
- `patterns: List[str]` - List of keywords.
- `search_contents: Dict[str, str]` - `{field_name: content}`.
**Output**: `(bool, str)` - `(is_match, description)`.
**Logic**: Iterates through all fields and patterns, returns True if any match is found.

##### `_match_regex(patterns: List[str], search_contents: Dict) -> Tuple[bool, str]`
**Purpose**: Regular expression matching.
**Input**:
- `patterns: List[str]` - List of regular expressions.
- `search_contents: Dict[str, str]` - `{field_name: content}`.
**Output**: `(bool, str)` - `(is_match, description)`.
**Error Handling**: Catches regex errors and returns an error description.

##### `match_any(rules: List[MatchRule], email_data: Dict) -> Tuple[bool, str]`
**Purpose**: Check if an email matches any of the rules (OR logic).
**Input**:
- `rules: List[MatchRule]` - List of rules.
- `email_data: Dict` - Email data.
**Output**: `(bool, str)` - `(is_match, description of the first match)`.

**Call Chain**: `match_any -> match -> _match_keyword | _match_regex`.

---

## 4. Authentication Module (core/auth.py)

### Responsibilities
- Validate client API keys.
- Provide a global authentication instance.

### Classes and Functions

#### `APIKeyAuth`
**Purpose**: API key authenticator.

##### `__init__(valid_keys: List[str])`
**Input**: `valid_keys` - A list of valid keys.
**Purpose**: Initializes the authenticator, storing keys in a set for efficient lookup.

##### `verify(api_key: str) -> bool`
**Purpose**: Verify an API key.
**Input**: `api_key: str` - The key to verify.
**Output**: `True` if valid, `False` otherwise.

##### `verify_or_raise(api_key: str) -> None`
**Purpose**: Verify a key, raising an HTTP exception on failure.
**Input**: `api_key: str`.
**Exception**: `HTTPException(401)` - On authentication failure.

#### `init_auth(valid_keys: List[str]) -> None`
**Purpose**: Initialize the global authenticator instance.
**Input**: `valid_keys` - A list of valid keys.
**Called**: On application startup.

#### `get_auth() -> APIKeyAuth`
**Purpose**: Get the global authenticator instance.
**Output**: `APIKeyAuth` instance.
**Exception**: `RuntimeError` - If the authenticator is not initialized.

---

## 5. IMAP Monitoring Core (core/imap_monitor.py)

### Responsibilities
- Connect to the IMAP server.
- Asynchronously monitor mailboxes for new emails.
- Parse email content.
- Match rules and push notifications.

### Classes and Functions

#### `EmailMonitor`
**Purpose**: Email monitor (one instance created per WebSocket connection).

##### `__init__(...)`
**Input**:
- `imap_host: str`, `imap_port: int`, `use_ssl: bool`
- `email_address: str`, `email_password: str`
- `rules: List[MatchRule]`
- `callback: Callable` - Callback function for pushing emails.
- `check_interval: int`, `mark_as_read: bool`
**Purpose**: Initialize monitor parameters.

##### `async start() -> None`
**Purpose**: Start monitoring.
**Call Chain**: `start -> wait_hello -> login -> select -> _monitor_loop`.
**Exception**: `ConnectionError` - On connection/login failure.
**Execution Flow**:
1. Connect to the IMAP server (SSL/non-SSL).
2. Wait for server's HELLO.
3. Log in to the mailbox.
4. Select INBOX.
5. Start the monitoring loop.

##### `async stop() -> None`
**Purpose**: Stop monitoring and clean up resources.
**Call Chain**: `stop -> cancel(monitor_task) -> logout`.

##### `async _monitor_loop() -> None`
**Purpose**: The monitoring loop, periodically checks for new emails.
**Call Chain**: `_monitor_loop -> _check_new_emails -> sleep -> _monitor_loop`.
**Logic**:
- Checks every `check_interval` seconds.
- Catches exceptions and continues running.
- Exits when `is_running` becomes `False`.

##### `async _check_new_emails() -> None`
**Purpose**: Check for new emails.
**Call Chain**: `_check_new_emails -> search(UNSEEN) -> _process_email`.
**Logic**:
1. Search for unseen emails (UNSEEN).
2. Parse the list of UIDs.
3. Filter out already processed UIDs.
4. Process new emails one by one.

##### `async _process_email(uid: str) -> None`
**Purpose**: Process a single email.
**Call Chain**: `_process_email -> fetch -> _parse_email -> EmailMatcher.match_any -> callback -> _mark_as_read`.
**Execution Flow**:
1. Fetch the full email content (RFC822).
2. Parse the email (call `_parse_email`).
3. Match rules (call `EmailMatcher.match_any`).
4. If matched:
   - Construct an `EmailContent` object.
   - Call the callback to push to the client.
   - Mark as read (if enabled).

##### `async _mark_as_read(uid: str) -> None`
**Purpose**: Mark an email as read.
**Input**: `uid: str` - The email's UID.
**Call Chain**: `_mark_as_read -> store(uid, +FLAGS, \\Seen)`.

##### `_parse_email(lines: List[bytes]) -> Optional[Dict]`
**Purpose**: Parse email content.
**Input**: `lines: List[bytes]` - Data returned from IMAP FETCH.
**Output**: A dictionary containing sender/subject/body, etc.
**Call Chain**: `_parse_email -> _decode_header_value -> _get_email_body`.
**Parsed Content**:
- From: Extracts email and name.
- Subject: Decodes MIME encoding.
- Body: Parses text/plain and text/html.
- Date: Converts to ISO format.

##### `_decode_header_value(value: str) -> str`
**Purpose**: Decode email headers (MIME encoding).
**Input**: `value: str` - The raw header value.
**Output**: The decoded UTF-8 string.

##### `_get_email_body(msg) -> str`
**Purpose**: Extract the body from an email object.
**Input**: `msg: email.message.Message`.
**Output**: The body string (UTF-8).

---

## 6. FastAPI Application (main.py)

### Responsibilities
- Provide the WebSocket endpoint.
- Manage the lifecycle of monitoring tasks.
- Handle client connections and messages.

### Global Variables

#### `active_monitors: Dict[str, EmailMonitor]`
**Purpose**: Store all active monitoring tasks.
**Structure**: `{connection_id: EmailMonitor instance}`.

### Lifecycle

#### `async lifespan(app: FastAPI)`
**Purpose**: Initialization/cleanup on application startup and shutdown.
**On Startup**:
1. Load configuration (`get_settings()`).
2. Initialize authentication (`init_auth()`).
3. Print configuration information.
**On Shutdown**:
1. Stop all monitoring tasks.
2. Clear `active_monitors`.

### Routes

#### `GET /`
**Purpose**: Health check.
**Output**:
```json
{
  "service": "Rubbish Mail",
  "status": "running",
  "active_connections": 0,
  "timestamp": "2025-10-08T10:00:00"
}
```

#### `WebSocket /ws/monitor`
**Purpose**: Email monitoring endpoint.
**Call Chain**: `websocket_endpoint -> receive_json -> verify -> EmailMonitor.start -> keep_alive -> stop`.
**Execution Flow**:
1.  **Accept connection**: `await websocket.accept()`.
2.  **Receive request**: `await websocket.receive_json()`.
    -   Parse into `MonitorRequest`.
    -   Validate data format.
3.  **Verify API key**:
    -   Call `get_auth().verify(api_key)`.
    -   Return 401 error on failure.
4.  **Verify email domain**:
    -   Check if the email domain is in `allowed_domain`.
    -   Return an error message on failure.
5.  **Check connection limit**:
    -   If `len(active_monitors) >= max_connections`, refuse the connection.
6.  **Create monitor**:
    -   Generate a `connection_id`.
    -   Create an `EmailMonitor` instance.
    -   Define a `push_callback` function.
7.  **Start monitoring**:
    -   Call `monitor.start()`.
    -   Add to `active_monitors`.
    -   Send `MonitorStartMessage`.
8.  **Keep connection alive**:
    -   Loop waiting for client messages (30-second timeout).
    -   Send `HeartbeatMessage` on timeout.
    -   Exit on exception or disconnection.
9.  **Clean up resources**:
    -   Remove from `active_monitors`.
    -   Call `monitor.stop()`.
    -   Close the WebSocket connection.

---

## 7. Client Example (example_client.py)

### Responsibilities
- Demonstrate how to use the monitoring service.
- Provide examples for various scenarios.
- Automatically extract verification codes.

### Classes and Functions

#### `MailMonitorClient`
**Purpose**: A client wrapper for the email monitor.

##### `__init__(ws_url: str, api_key: str)`
**Input**:
- `ws_url: str` - The WebSocket service address.
- `api_key: str` - The API key.

##### `async monitor(...)`
**Purpose**: Start monitoring an email address.
**Input**:
- `email: str` - The email to monitor.
- `keywords: List[str]`, `regex_patterns: List[str]`, `search_in: List[str]`.
**Call Chain**: `monitor -> connect -> send(request) -> _handle_message`.

##### `async _handle_message(message: str)`
**Purpose**: Handle messages from the server.
**Call Chain**: `_handle_message -> json.loads -> _extract_verification_code`.
**Message Types Handled**:
- `monitor_start`: Display monitoring status.
- `email_received`: Display email content and extract verification code.
- `error`: Display error message.
- `heartbeat`: Silently handle.

##### `_extract_verification_code(email_data: dict)`
**Purpose**: Extract a verification code from an email.
**Input**: `email_data: dict` - The email data.
**Output**: Verification code string or `None`.
**Supported Formats**:
- 6-digit number: `\d{6}`
- 4-digit number: `\d{4}`
- 6-character alphanumeric: `[A-Z0-9]{6}`
- Formatted codes: `Verification code: 123456`, `code: ABC123`.

---

## Complete Call Chain

### Main Flow: WebSocket Connection → Monitor Email → Push

```
Client Connects
    ↓
main.websocket_endpoint()
    ↓
Receive MonitorRequest
    ↓
get_auth().verify(api_key)  [Verify API Key]
    ↓
Check Email Domain
    ↓
Create EmailMonitor instance
    ↓
EmailMonitor.start()
    ├─ Connect to IMAP server
    ├─ Log in to mailbox
    ├─ Select INBOX
    └─ Start _monitor_loop()
        ↓
    _check_new_emails()  [Periodic execution]
        ├─ search("UNSEEN")  [Search for unread emails]
        └─ _process_email(uid)  [Process each email]
            ├─ fetch(uid, RFC822)  [Get email content]
            ├─ _parse_email()  [Parse email]
            │   ├─ _decode_header_value()  [Decode header]
            │   └─ _get_email_body()  [Extract body]
            ├─ EmailMatcher.match_any(rules, email_data)  [Match rules]
            │   └─ EmailMatcher.match(rule, email_data)
            │       ├─ _match_keyword()  [Keyword match]
            │       └─ _match_regex()  [Regex match]
            ├─ callback(EmailContent)  [Push to client]
            │   └─ websocket.send_json(EmailReceivedMessage)
            └─ _mark_as_read(uid)  [Mark as read]
```

### Configuration Loading Flow

```
main.py starts
    ↓
lifespan(app) startup
    ↓
get_settings()
    ├─ load_config("config.yml")
    │   ├─ Read config.yml
    │   ├─ Read API_KEY from .env
    │   └─ Create Settings instance
    └─ Return global configuration
        ↓
init_auth(settings.get_valid_api_keys())
    └─ Create global APIKeyAuth instance
```

### Client Usage Flow

```
MailMonitorClient.monitor()
    ↓
websockets.connect(ws_url)
    ↓
Send MonitorRequest JSON
    ↓
Server processes...
    ↓
Receive MonitorStartMessage
    ↓
Loop to receive messages
    ├─ HeartbeatMessage → Ignore
    ├─ ErrorMessage → Display error
    └─ EmailReceivedMessage → Display email
        └─ _extract_verification_code()
```

---

## Data Flow

```
Mail Server
    ↓ IMAP Protocol
EmailMonitor
    ├─ Periodically checks for unread emails
    ├─ Parses email content
    ├─ Matches rules
    └─ If matched → EmailContent
        ↓ WebSocket
Client
    └─ Receives and processes
```

---

## Key Design Decisions

### 1. Why choose WebSocket over polling?

**Advantages**:
- **Real-time**: Pushes immediately after an email arrives, no polling delay.
- **Efficiency**: Reuses a long-lived connection, reducing handshake overhead.
- **Bidirectional**: Supports keep-alive heartbeats, detects disconnections promptly.

### 2. Why create a separate EmailMonitor for each connection?

**Advantages**:
- **Isolation**: Each client monitors independently without interference.
- **Flexibility**: Different clients can monitor different mailboxes with different rules.
- **Resource Management**: Resources are released immediately upon disconnection.

### 3. Why mark emails as read?

**Advantages**:
- **Avoids duplicate pushes** of the same email.
- **Reduces server load**.
- **User-configurable** (`mark_as_read`).

### 4. Why use both regex and keyword modes?

**Advantages**:
- **Keywords**: Simple and easy to use, suitable for most scenarios.
- **Regex**: Flexible and powerful, suitable for complex matching needs.
- **Combined use**: Meets a variety of requirements.

---

## Performance Considerations

### 1. Concurrent Connection Limit

**Configuration**: `monitor.max_connections`.
**Reason**:
- Each IMAP connection consumes server resources.
- Prevents resource exhaustion.
- A large number of concurrent connections is usually not needed for personal use.

### 2. Check Interval

**Configuration**: `monitor.check_interval`.
**Trade-off**:
- Too short: High pressure on the IMAP server.
- Too long: Poor real-time performance.
- Recommended: 5-10 seconds.

### 3. Processed Email Cache

**Implementation**: `EmailMonitor._processed_uids: set`.
**Purpose**: To avoid processing the same email repeatedly.
**Limitation**: Memory usage grows with the number of emails.

### 4. Asynchronous I/O

**Technology**: `asyncio` + `aioimaplib`.
**Advantages**:
- High concurrency with a single thread.
- Low resource consumption.
- Excellent performance.

---

## Security

### 1. API Key Authentication

**Implementation**: `core/auth.py`.
**Advantage**: Simple and effective, suitable for personal use.
**Recommendation**: Use a strong random key (32+ characters).

### 2. Domain Restriction

**Configuration**: `imap.allowed_domain`.
**Purpose**: To prevent monitoring of unauthorized mailboxes.

### 3. Connection Limit

**Configuration**: `monitor.max_connections`.
**Purpose**: To prevent resource exhaustion attacks.

### 4. Sensitive Information Protection

**Implementation**:
- API key stored in `.env` (not committed to version control).
- Email password stored in `config.yml` (not committed).
- `.gitignore` ignores sensitive files.

---

## Error Handling

### 1. IMAP Connection Errors

**Location**: `EmailMonitor.start()`.
**Handling**:
- Catch `ConnectionError`.
- Log the error.
- Send an error message to the client.
- Clean up resources.

### 2. Email Parsing Errors

**Location**: `EmailMonitor._parse_email()`.
**Handling**:
- Catch exceptions.
- Log a warning.
- Skip the email and continue with the next one.

### 3. Regular Expression Errors

**Location**: `EmailMatcher._match_regex()`.
**Handling**:
- Catch `re.error`.
- Return an error description.
- Does not affect other rules.

### 4. WebSocket Disconnections

**Location**: `main.websocket_endpoint()`.
**Handling**:
- Catch `WebSocketDisconnect`.
- Stop the monitoring task.
- Clean up resources.
- Log the event.

---

## Extensibility

### Future Possible Extensions

1.  **Multi-account support**:
    -   Support multiple email accounts in the configuration file.
    -   Allow clients to specify which account to use when requesting.
2.  **Webhook push**:
    -   Support HTTP POST push in addition to WebSocket.
    -   Suitable for scenarios that cannot maintain a long-lived connection.
3.  **Email attachment download**:
    -   Parse attachments and provide download links.
    -   Or push attachments directly as Base64.
4.  **Persistent rules**:
    -   Support saving frequently used rules to a database.
    -   Allow clients to reuse rules.
5.  **Web admin panel**:
    -   Visually manage monitoring tasks.
    -   View historical emails.
    -   Statistical analysis.

---

## Testing Recommendations

### Unit Tests

1.  **EmailMatcher tests**:
    -   Keyword matching (Chinese/English/case-insensitivity).
    -   Regex matching (various patterns).
    -   Edge cases (empty patterns/content).
2.  **Configuration loading tests**:
    -   Normal configuration.
    -   Missing fields.
    -   Format errors.
3.  **Authentication tests**:
    -   Correct key.
    -   Incorrect key.
    -   Multiple keys.

### Integration Tests

1.  **IMAP connection tests**:
    -   Successful connection.
    -   Connection failure.
    -   Timeout.
2.  **Email parsing tests**:
    -   Plain text emails.
    -   HTML emails.
    -   Multipart emails.
    -   Special encodings.
3.  **WebSocket tests**:
    -   Connection/disconnection.
    -   Message sending/receiving.
    -   Error handling.

---

## Summary

This project uses a modern asynchronous architecture to implement an **efficient, flexible, and easy-to-use** email monitoring service.

**Core Advantages**:
- ⚡ Asynchronous high performance
- 🎯 Flexible rule matching
- 📨 Real-time push
- 🔒 Secure and controllable
- 📦 Out-of-the-box

**Applicable Scenarios**:
- Automated script email verification
- Email notification monitoring
- Temporary email service

**Code Quality**:
- ✅ Type safety (Pydantic)
- ✅ Complete comments (input/output/purpose)
- ✅ Comprehensive error handling
- ✅ Detailed logging
- ✅ Clear, modular structure

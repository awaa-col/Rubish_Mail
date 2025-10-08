[中文](../DNS配置指南.md)

# DNS Configuration Guide


---

## Why is DNS Configuration Necessary?

When another mail server wants to send an email to `user@your-domain.com`:
1. It queries the **MX record** for `your-domain.com`.
2. It finds the mail server's address.
3. It connects to port 25 of that server.
4. It sends the email.

Therefore, you must configure an MX record to tell the world: "Send all emails for my domain to this server!"

---

## Required DNS Records

Assuming:
- Your domain: `your-domain.com`
- Your server IP: `1.2.3.4`

### 1. A Record (Required)

```
Type: A
Host: mail
Value: 1.2.3.4
TTL: 600
```

**Purpose**: To point `mail.your-domain.com` to your server's IP.

---

### 2. MX Record (Required)

```
Type: MX
Host: @
Value: mail.your-domain.com
Priority: 10
TTL: 600
```

**Purpose**: To tell everyone, "Send emails for @your-domain.com to mail.your-domain.com".

---

### 3. SPF Record (Strongly Recommended)

```
Type: TXT
Host: @
Value: v=spf1 mx ~all
TTL: 600
```

**Purpose**: To prevent others from forging your domain to send spam, improving the success rate of receiving emails.

---

### 4. PTR Reverse DNS (Optional, but Recommended)

This needs to be set up with your VPS provider, not in your domain's DNS:

```
IP: 1.2.3.4  →  mail.your-domain.com
```

**Purpose**: To make other mail servers trust you, preventing your emails from being marked as spam.

---

## Configuration Examples for Common Domain Registrars

### Alibaba Cloud (HiChina)

1. Log in to the [Alibaba Cloud DNS Console](https://dns.console.aliyun.com/).
2. Select your domain → DNS Settings.
3. Add records:

| Record Type | Host Record | Record Value         | Priority | TTL |
|-------------|-------------|----------------------|----------|-----|
| A           | mail        | 1.2.3.4              | -        | 600 |
| MX          | @           | mail.your-domain.com | 10       | 600 |
| TXT         | @           | v=spf1 mx ~all       | -        | 600 |

---

### Tencent Cloud (DNSPod)

1. Log in to the [DNSPod Console](https://console.dnspod.cn/).
2. My Domains → Select domain → Record Management.
3. Add records (same as the table above).

---

### Cloudflare

1. Log in to [Cloudflare](https://dash.cloudflare.com/).
2. Select domain → DNS → Records.
3. Add record:

| Type | Name | Content              | Priority | Proxy Status  |
|------|------|----------------------|----------|---------------|
| A    | mail | 1.2.3.4              | -        | ❌ (DNS only) |
| MX   | @    | mail.your-domain.com | 10       | -             |
| TXT  | @    | v=spf1 mx ~all       | -        | -             |

**Note**: The Proxy status for the A record must be turned off (DNS only). MX records do not support CDN!

---

### Namesilo / GoDaddy / Namecheap

The basic process is the same:
1. Go to the DNS management page.
2. Add A, MX, and TXT records.
3. Save.

---

## Verifying DNS Configuration

### Method 1: Using the `dig` command (Linux/Mac)

```bash
# Check A record
dig mail.your-domain.com

# Check MX record
dig MX your-domain.com

# Check TXT record
dig TXT your-domain.com
```

### Method 2: Using `nslookup` (Windows)

```powershell
# Check A record
nslookup mail.your-domain.com

# Check MX record
nslookup -type=MX your-domain.com
```

### Method 3: Online Tools

- [MXToolbox](https://mxtoolbox.com/)
- [DNSChecker](https://dnschecker.org/)

---

## Server Port Configuration

After setting up DNS, you also need to ensure the server ports are open:

### 1. Open SMTP Port

```bash
# Check if the port is open
sudo netstat -tulnp | grep 8025

# If using firewall-cmd (CentOS/RHEL)
sudo firewall-cmd --zone=public --add-port=8025/tcp --permanent
sudo firewall-cmd --reload

# If using ufw (Ubuntu/Debian)
sudo ufw allow 8025/tcp
sudo ufw reload

# If using iptables
sudo iptables -A INPUT -p tcp --dport 8025 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

### 2. Port Forwarding (25 → 8025)

Since we are using the non-privileged port 8025, we need to forward the standard SMTP port 25:

```bash
# Using iptables for forwarding
sudo iptables -t nat -A PREROUTING -p tcp --dport 25 -j REDIRECT --to-port 8025
sudo iptables-save > /etc/iptables/rules.v4

# Or using rinetd (simpler)
sudo apt install rinetd
echo "0.0.0.0 25 0.0.0.0 8025" | sudo tee -a /etc/rinetd.conf
sudo service rinetd restart
```

**Why not use port 25 directly?**
Because port 25 requires root privileges, using 8025 is more secure. Forwarding can be easily set up.

---

## Cloud Server Considerations

### Alibaba Cloud ECS

Port 25 is **blocked by default**! You need to:
1. Submit a ticket to request unblocking port 25.
2. Or use port 465 (SMTPS).

### Tencent Cloud CVM

Port 25 is also blocked by default and requires an application to unblock.

### AWS EC2

Port 25 is restricted by default. You need to fill out a form to request the removal of the restriction.

### Oracle Cloud / Other VPS

Port 25 is generally not blocked and can be used directly.

---

## Testing Email Reception

### 1. Send a Test Email

Send an email from Gmail/QQ Mail to `test@your-domain.com`.

### 2. Check the Logs

```bash
tail -f logs/rubbish_mail.log
```

You should see:
```
INFO - Email received: sender=xxx@gmail.com, recipients=['test@your-domain.com']
INFO - Email subject: Test Email
```

### 3. If Not Received

Checklist:
- [ ] Has the DNS propagated? (Wait 10-60 minutes)
- [ ] Is server port 25 open?
- [ ] Is the port forwarding configured correctly?
- [ ] Is the service running correctly? (`python main.py`)
- [ ] Is there a WebSocket connection monitoring this email address?

---

## Complete Configuration Example

### Domain DNS Settings

| Type | Host Record | Record Value         | Priority |
|------|-------------|----------------------|----------|
| A    | mail        | 123.45.67.89         | -        |
| MX   | @           | mail.your-domain.com | 10       |
| TXT  | @           | v=spf1 mx ~all       | -        |

### Server Configuration

```yaml
# config.yml
smtp:
  host: "0.0.0.0"
  port: 8025
  allowed_domain: "your-domain.com"
```

### iptables Forwarding

```bash
sudo iptables -t nat -A PREROUTING -p tcp --dport 25 -j REDIRECT --to-port 8025
```

### Start the Service

```bash
python main.py
```

---

## FAQ

### Q: How long does it take for DNS changes to take effect?

A: Generally 10-60 minutes, but it can take up to 24 hours. Use the `dig` command to check.

### Q: Why am I not receiving emails sent to me?

A: Common reasons:
1. DNS has not yet propagated.
2. Port 25 is not open.
3. The service is not running.
4. The cloud server has blocked port 25.

### Q: I received an email, but did not get a push notification.

A: Check:
1. Is there a WebSocket connection monitoring this email address?
2. Are the rules written correctly?
3. Check the logs `logs/rubbish_mail.log`.

### Q: Can I skip DNS configuration?

A: No! Without an MX record, external mail servers do not know where to send emails.


[中文](../Docker部署指南.md)

# Docker Deployment Guide


---

## 🐳 Why Use Docker?

- ✅ **One-Click Deployment**: No need to worry about dependency issues.
- ✅ **Environment Isolation**: Does not pollute the host environment.
- ✅ **Easy Migration**: Can be run on any server that supports Docker after being packaged.
- ✅ **Convenient Management**: Easy to start/stop/restart.
- ✅ **Resource Limiting**: Can limit CPU and memory usage.

---

## 📋 Prerequisites

### Install Docker

**Linux (Ubuntu/Debian)**:
```bash
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER
```

**CentOS/RHEL**:
```bash
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
```

**Windows/Mac**:
Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop).

**Verify Installation**:
```bash
docker --version
docker-compose --version
```

---

## 🚀 Quick Deployment

### Method 1: Using Startup Scripts (Recommended)

#### Linux/Mac:
```bash
# Grant execution permissions
chmod +x docker-run.sh

# Run the script
./docker-run.sh
```

#### Windows:
```bash
# Double-click to run
docker-run.bat

# Or in PowerShell
.\docker-run.bat
```

The script will automatically:
1. Check if Docker is installed.
2. Create `config.yml` (if it doesn't exist).
3. Generate an API key.
4. Build the image.
5. Start the container.

---

### Method 2: Using docker-compose

#### 1. Prepare Configuration

```bash
# Copy the configuration file
cp config.example.yml config.yml

# Edit the configuration
nano config.yml
# Modify smtp.allowed_domain to your domain

# Create .env file
echo "API_KEY=$(openssl rand -hex 32)" > .env
```

#### 2. Start the Service

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

---

### Method 3: Pure Docker Commands

#### 1. Build the Image

```bash
docker build -t rubbish-mail:latest .
```

#### 2. Run the Container

```bash
docker run -d \
  --name rubbish-mail \
  --restart unless-stopped \
  -p 8000:8000 \
  -p 25:8025 \
  -e API_KEY="your-api-key" \
  -e TZ="Asia/Shanghai" \
  -v ./config.yml:/app/config.yml:ro \
  -v ./logs:/app/logs \
  rubbish-mail:latest
```

---

## 🔧 Configuration Details

### Port Mapping

| Host Port | Container Port | Description     |
|-----------|----------------|-----------------|
| 8000      | 8000           | WebSocket API   |
| 25        | 8025           | SMTP Server     |

**Note**: Host port 25 requires root privileges or iptables forwarding.

### Environment Variables

| Variable  | Required | Default Value | Description |
|-----------|----------|---------------|-------------|
| `API_KEY` | ✅       | -             | API Key     |
| `TZ`      | ❌       | UTC           | Timezone    |

### Volume Mounts

| Host Path      | Container Path    | Description              |
|----------------|-------------------|--------------------------|
| `./config.yml` | `/app/config.yml` | Configuration file (read-only) |
| `./logs`       | `/app/logs`       | Log directory            |

---

## 📊 Container Management

### Check Status

```bash
# Check running status
docker ps

# Check all containers
docker ps -a

# Check resource usage
docker stats rubbish-mail
```

### View Logs

```bash
# Real-time view
docker logs -f rubbish-mail

# View the last 100 lines
docker logs --tail 100 rubbish-mail

# View logs from a specific time
docker logs --since 30m rubbish-mail
```

### Stop/Start

```bash
# Stop
docker stop rubbish-mail

# Start
docker start rubbish-mail

# Restart
docker restart rubbish-mail
```

### Update Service

```bash
# 1. Stop and remove the old container
docker stop rubbish-mail
docker rm rubbish-mail

# 2. Rebuild the image
docker build -t rubbish-mail:latest .

# 3. Start the new container
docker run -d \
  --name rubbish-mail \
  --restart unless-stopped \
  -p 8000:8000 \
  -p 25:8025 \
  -e API_KEY="your-api-key" \
  -v ./config.yml:/app/config.yml:ro \
  -v ./logs:/app/logs \
  rubbish-mail:latest
```

---

## 🌐 Production Environment Deployment

### 1. Configure Reverse Proxy (Nginx)

```nginx
# /etc/nginx/sites-available/rubbish-mail

# WebSocket
upstream rubbish_websocket {
    server localhost:8000;
}

server {
    listen 443 ssl http2;
    server_name mail-api.your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # WebSocket
    location /ws/ {
        proxy_pass http://rubbish_websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }
    
    # API
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable configuration:
```bash
sudo ln -s /etc/nginx/sites-available/rubbish-mail /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. Configure SSL (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain a certificate
sudo certbot --nginx -d mail-api.your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 3. Configure systemd (Startup on Boot)

The Docker container is already configured with `--restart unless-stopped`, so it will restart automatically.

For more fine-grained control, you can create a systemd service:

```bash
# /etc/systemd/system/rubbish-mail.service
[Unit]
Description=Rubbish Mail Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/rubbish-mail
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=root

[Install]
WantedBy=multi-user.target
```

Enable the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rubbish-mail
sudo systemctl start rubbish-mail
```

### 4. Configure Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 25/tcp

# Firewalld (CentOS)
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=25/tcp
sudo firewall-cmd --reload
```

---

## 🔒 Security Recommendations

### 1. Use Strong API Keys

```bash
# Generate a 64-character random key
openssl rand -hex 32
```

### 2. Limit Resource Usage

In `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
```

### 3. Log Rotation

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 4. Expose Only Necessary Ports

```bash
# If using Nginx reverse proxy, do not expose port 8000 to the public network
docker run -d \
  -p 127.0.0.1:8000:8000 \  # Listen only locally
  -p 25:8025 \
  ...
```

---

## 📈 Monitoring and Maintenance

### 1. Health Checks

Docker is already configured with health checks:
```bash
docker inspect --format='{{.State.Health.Status}}' rubbish-mail
```

### 2. Performance Monitoring

```bash
# Real-time monitoring
docker stats rubbish-mail

# Export metrics
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" rubbish-mail
```

### 3. Backup Configuration

```bash
# Backup configuration and logs
tar -czf rubbish-mail-backup-$(date +%Y%m%d).tar.gz \
  config.yml .env logs/
```

### 4. Clean Up Old Images

```bash
# Remove unused images
docker image prune -a

# Clean up all unused resources
docker system prune -a
```

---

## 🐛 Troubleshooting

### Container Fails to Start?

```bash
# Check error logs
docker logs rubbish-mail

# Check configuration file
docker run --rm -it \
  -v ./config.yml:/app/config.yml:ro \
  rubbish-mail:latest \
  python -c "from core.config import load_config; load_config()"
```

### Port Conflict?

```bash
# Check port usage
netstat -tuln | grep -E '8000|25'

# Modify port mapping
docker run -p 8001:8000 -p 2525:8025 ...
```

### Unable to Receive Emails?

```bash
# Check SMTP port
telnet localhost 25

# Check container logs
docker logs -f rubbish-mail | grep SMTP

# Debug inside the container
docker exec -it rubbish-mail bash
```

---

## 📦 Pushing Images (Optional)

### Push to Docker Hub

```bash
# Log in
docker login

# Tag
docker tag rubbish-mail:latest your-username/rubbish-mail:latest
docker tag rubbish-mail:latest your-username/rubbish-mail:2.0.0

# Push
docker push your-username/rubbish-mail:latest
docker push your-username/rubbish-mail:2.0.0
```

### Push to a Private Registry

```bash
# Tag
docker tag rubbish-mail:latest registry.your-domain.com/rubbish-mail:latest

# Push
docker push registry.your-domain.com/rubbish-mail:latest
```

---

## 🎯 Complete Deployment Example

### Cloud Server Deployment Flow

```bash
# 1. Connect to the server
ssh user@your-server

# 2. Install Docker
curl -fsSL https://get.docker.com | bash

# 3. Clone/upload the project
git clone https://github.com/your-repo/rubbish-mail.git
cd rubbish-mail

# 4. Configure
cp config.example.yml config.yml
nano config.yml  # Modify allowed_domain

echo "API_KEY=$(openssl rand -hex 32)" > .env

# 5. Build and start
docker-compose up -d

# 6. Configure DNS (in your domain management panel)
# MX: @ -> mail.your-domain.com (priority 10)
# A:  mail -> your server IP

# 7. Configure Nginx reverse proxy + SSL
sudo apt install nginx certbot python3-certbot-nginx
# ... (refer to the Nginx configuration above)

# 8. Verify
curl http://localhost:8000
docker logs -f rubbish-mail
```

---


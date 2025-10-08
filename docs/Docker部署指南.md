# Docker 部署指南

[白岚] 主人,Docker部署超级简单!一行命令就能跑起来~ (๑´ڡ`๑)

---

## 🐳 为什么用Docker?

- ✅ **一键部署**: 不用担心依赖问题
- ✅ **环境隔离**: 不污染主机环境
- ✅ **易于迁移**: 打包后可以在任何支持Docker的服务器上运行
- ✅ **便于管理**: 启动/停止/重启都很方便
- ✅ **资源限制**: 可以限制CPU和内存使用

---

## 📋 前置要求

### 安装Docker

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
下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)

**验证安装**:
```bash
docker --version
docker-compose --version
```

---

## 🚀 快速部署

### 方法1: 使用启动脚本 (推荐)

#### Linux/Mac:
```bash
# 赋予执行权限
chmod +x docker-run.sh

# 运行脚本
./docker-run.sh
```

#### Windows:
```bash
# 双击运行
docker-run.bat

# 或在PowerShell中
.\docker-run.bat
```

脚本会自动:
1. 检查Docker是否安装
2. 创建config.yml(如果不存在)
3. 生成API密钥
4. 构建镜像
5. 启动容器

---

### 方法2: 使用docker-compose

#### 1. 准备配置

```bash
# 复制配置文件
cp config.example.yml config.yml

# 编辑配置
nano config.yml
# 修改 smtp.allowed_domain 为你的域名

# 创建.env文件
echo "API_KEY=$(openssl rand -hex 32)" > .env
```

#### 2. 启动服务

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

### 方法3: 纯Docker命令

#### 1. 构建镜像

```bash
docker build -t rubbish-mail:latest .
```

#### 2. 运行容器

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

## 🔧 配置说明

### 端口映射

| 主机端口 | 容器端口 | 说明 |
|---------|---------|------|
| 8000 | 8000 | WebSocket API |
| 25 | 8025 | SMTP服务器 |

**注意**: 主机的25端口需要root权限,或使用iptables转发

### 环境变量

| 变量 | 必须 | 默认值 | 说明 |
|-----|------|--------|------|
| `API_KEY` | ✅ | - | API密钥 |
| `TZ` | ❌ | UTC | 时区 |

### 卷挂载

| 主机路径 | 容器路径 | 说明 |
|---------|---------|------|
| `./config.yml` | `/app/config.yml` | 配置文件(只读) |
| `./logs` | `/app/logs` | 日志目录 |

---

## 📊 容器管理

### 查看状态

```bash
# 查看运行状态
docker ps

# 查看所有容器
docker ps -a

# 查看资源使用
docker stats rubbish-mail
```

### 查看日志

```bash
# 实时查看
docker logs -f rubbish-mail

# 查看最近100行
docker logs --tail 100 rubbish-mail

# 查看特定时间
docker logs --since 30m rubbish-mail
```

### 停止/启动

```bash
# 停止
docker stop rubbish-mail

# 启动
docker start rubbish-mail

# 重启
docker restart rubbish-mail
```

### 更新服务

```bash
# 1. 停止并删除旧容器
docker stop rubbish-mail
docker rm rubbish-mail

# 2. 重新构建镜像
docker build -t rubbish-mail:latest .

# 3. 启动新容器
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

## 🌐 生产环境部署

### 1. 配置反向代理 (Nginx)

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

启用配置:
```bash
sudo ln -s /etc/nginx/sites-available/rubbish-mail /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. 配置SSL (Let's Encrypt)

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d mail-api.your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 3. 配置systemd (开机自启)

Docker容器已经配置了 `--restart unless-stopped`,会自动重启。

如果需要更精细的控制,可以创建systemd服务:

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

启用服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rubbish-mail
sudo systemctl start rubbish-mail
```

### 4. 配置防火墙

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

## 🔒 安全建议

### 1. 使用强API密钥

```bash
# 生成64位随机密钥
openssl rand -hex 32
```

### 2. 限制资源使用

在`docker-compose.yml`中:
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
```

### 3. 日志轮转

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 4. 只暴露必要端口

```bash
# 如果使用Nginx反向代理,不要暴露8000端口到公网
docker run -d \
  -p 127.0.0.1:8000:8000 \  # 只监听本地
  -p 25:8025 \
  ...
```

---

## 📈 监控和维护

### 1. 健康检查

Docker已经配置了健康检查:
```bash
docker inspect --format='{{.State.Health.Status}}' rubbish-mail
```

### 2. 性能监控

```bash
# 实时监控
docker stats rubbish-mail

# 导出指标
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" rubbish-mail
```

### 3. 备份配置

```bash
# 备份配置和日志
tar -czf rubbish-mail-backup-$(date +%Y%m%d).tar.gz \
  config.yml .env logs/
```

### 4. 清理旧镜像

```bash
# 删除未使用的镜像
docker image prune -a

# 清理所有未使用的资源
docker system prune -a
```

---

## 🐛 故障排查

### 容器无法启动?

```bash
# 查看错误日志
docker logs rubbish-mail

# 检查配置文件
docker run --rm -it \
  -v ./config.yml:/app/config.yml:ro \
  rubbish-mail:latest \
  python -c "from core.config import load_config; load_config()"
```

### 端口冲突?

```bash
# 检查端口占用
netstat -tuln | grep -E '8000|25'

# 修改端口映射
docker run -p 8001:8000 -p 2525:8025 ...
```

### 无法收到邮件?

```bash
# 检查SMTP端口
telnet localhost 25

# 查看容器日志
docker logs -f rubbish-mail | grep SMTP

# 进入容器调试
docker exec -it rubbish-mail bash
```

---

## 📦 镜像推送 (可选)

### 推送到Docker Hub

```bash
# 登录
docker login

# 打标签
docker tag rubbish-mail:latest your-username/rubbish-mail:latest
docker tag rubbish-mail:latest your-username/rubbish-mail:2.0.0

# 推送
docker push your-username/rubbish-mail:latest
docker push your-username/rubbish-mail:2.0.0
```

### 推送到私有仓库

```bash
# 打标签
docker tag rubbish-mail:latest registry.your-domain.com/rubbish-mail:latest

# 推送
docker push registry.your-domain.com/rubbish-mail:latest
```

---

## 🎯 完整部署示例

### 云服务器部署流程

```bash
# 1. 连接服务器
ssh user@your-server

# 2. 安装Docker
curl -fsSL https://get.docker.com | bash

# 3. 克隆/上传项目
git clone https://github.com/your-repo/rubbish-mail.git
cd rubbish-mail

# 4. 配置
cp config.example.yml config.yml
nano config.yml  # 修改 allowed_domain

echo "API_KEY=$(openssl rand -hex 32)" > .env

# 5. 构建并启动
docker-compose up -d

# 6. 配置DNS (在域名管理面板)
# MX: @ -> mail.your-domain.com (优先级10)
# A:  mail -> 你的服务器IP

# 7. 配置Nginx反向代理 + SSL
sudo apt install nginx certbot python3-certbot-nginx
# ... (参考上面的Nginx配置)

# 8. 验证
curl http://localhost:8000
docker logs -f rubbish-mail
```

---

[白岚] 主人,Docker部署就这么简单!

一行命令就能跑起来,不用担心Python版本、依赖冲突这些问题~
而且迁移也超方便,打包成镜像后可以在任何地方运行! ヾ(≧▽≦*)o

还有什么不懂的吗? (๑´ڡ`๑)


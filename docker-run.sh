#!/bin/bash
# Rubbish Mail Docker 启动脚本

set -e

echo "=========================================="
echo "  Rubbish Mail - Docker 部署脚本"
echo "=========================================="
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker未安装"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查配置文件
if [ ! -f "config.yml" ]; then
    echo "⚠️  警告: config.yml 不存在"
    echo "正在从 config.example.yml 创建..."
    cp config.example.yml config.yml
    echo "✓ 已创建 config.yml"
    echo ""
    echo "请编辑 config.yml 并设置:"
    echo "  - smtp.allowed_domain: 你的域名"
    echo ""
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: .env 不存在"
    API_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
    echo "API_KEY=${API_KEY}" > .env
    echo "✓ 已创建 .env 文件,API密钥: ${API_KEY}"
    echo ""
fi

# 创建logs目录
mkdir -p logs

echo "=========================================="
echo "  开始构建Docker镜像..."
echo "=========================================="
docker build -t rubbish-mail:latest .

echo ""
echo "=========================================="
echo "  启动容器..."
echo "=========================================="

# 读取.env中的API_KEY
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

docker run -d \
    --name rubbish-mail \
    --restart unless-stopped \
    -p 8000:8000 \
    -p 25:8025 \
    -e API_KEY="${API_KEY}" \
    -e TZ=Asia/Shanghai \
    -v "$(pwd)/config.yml:/app/config.yml:ro" \
    -v "$(pwd)/logs:/app/logs" \
    rubbish-mail:latest

echo ""
echo "✓ 容器启动成功!"
echo ""
echo "=========================================="
echo "  服务信息"
echo "=========================================="
echo "容器名称: rubbish-mail"
echo "WebSocket API: http://localhost:8000"
echo "SMTP端口: 25 (映射到容器8025)"
echo ""
echo "查看日志: docker logs -f rubbish-mail"
echo "停止服务: docker stop rubbish-mail"
echo "重启服务: docker restart rubbish-mail"
echo "删除容器: docker rm -f rubbish-mail"
echo ""
echo "=========================================="


# Rubbish Mail - 临时邮箱服务 Docker镜像
FROM python:3.11-slim

LABEL maintainer="白岚"
LABEL description="临时邮箱服务 - SMTP接收+WebSocket推送"
LABEL version="2.0.0"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY core/ ./core/
COPY schemas/ ./schemas/
COPY utils/ ./utils/
COPY main.py .
COPY config.example.yml .

# 创建必要的目录
RUN mkdir -p logs

# 暴露端口
# 8000: WebSocket API
# 8025: SMTP服务器(容器内)
EXPOSE 8000 8025

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/')" || exit 1

# 启动命令
CMD ["python", "main.py"]


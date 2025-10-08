@echo off
REM Rubbish Mail Docker 启动脚本 (Windows)
chcp 65001 >nul

echo ==========================================
echo   Rubbish Mail - Docker 部署脚本
echo ==========================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Docker未安装
    echo 请先安装Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM 检查配置文件
if not exist "config.yml" (
    echo ⚠️  警告: config.yml 不存在
    echo 正在从 config.example.yml 创建...
    copy config.example.yml config.yml >nul
    echo ✓ 已创建 config.yml
    echo.
    echo 请编辑 config.yml 并设置:
    echo   - smtp.allowed_domain: 你的域名
    echo.
)

REM 检查.env文件
if not exist ".env" (
    echo ⚠️  警告: .env 不存在
    powershell -Command "$key = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_}); 'API_KEY=' + $key | Out-File -Encoding ASCII .env"
    echo ✓ 已创建 .env 文件
    echo.
)

REM 创建logs目录
if not exist "logs" mkdir logs

echo ==========================================
echo   开始构建Docker镜像...
echo ==========================================
docker build -t rubbish-mail:latest .
if errorlevel 1 (
    echo ❌ 构建失败
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   启动容器...
echo ==========================================

REM 读取API_KEY
for /f "tokens=2 delims==" %%a in ('findstr "API_KEY" .env') do set API_KEY=%%a

REM 停止并删除旧容器
docker stop rubbish-mail >nul 2>&1
docker rm rubbish-mail >nul 2>&1

REM 启动新容器
docker run -d ^
    --name rubbish-mail ^
    --restart unless-stopped ^
    -p 8000:8000 ^
    -p 25:8025 ^
    -e API_KEY=%API_KEY% ^
    -e TZ=Asia/Shanghai ^
    -v "%cd%\config.yml:/app/config.yml:ro" ^
    -v "%cd%\logs:/app/logs" ^
    rubbish-mail:latest

if errorlevel 1 (
    echo ❌ 启动失败
    pause
    exit /b 1
)

echo.
echo ✓ 容器启动成功!
echo.
echo ==========================================
echo   服务信息
echo ==========================================
echo 容器名称: rubbish-mail
echo WebSocket API: http://localhost:8000
echo SMTP端口: 25 (映射到容器8025)
echo.
echo 查看日志: docker logs -f rubbish-mail
echo 停止服务: docker stop rubbish-mail
echo 重启服务: docker restart rubbish-mail
echo 删除容器: docker rm -f rubbish-mail
echo.
echo ==========================================

pause


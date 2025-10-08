@echo off
chcp 65001 >nul
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║          Rubbish Mail - 本地启动脚本                      ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查.env文件
if not exist ".env" (
    echo [创建] 正在创建 .env 文件...
    echo API_KEY=test-local-key-123456 > .env
    echo [OK] .env 文件已创建
    echo.
)

REM 检查config.yml
if not exist "config.yml" (
    echo [创建] 正在创建 config.yml...
    copy config.example.yml config.yml >nul
    echo [OK] config.yml 已创建
    echo.
)

REM 检查logs目录
if not exist "logs" (
    mkdir logs
    echo [OK] logs 目录已创建
    echo.
)

REM 检查依赖
echo [检查] 检查Python依赖...
python -c "import aiosmtpd" 2>nul
if errorlevel 1 (
    echo [安装] 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo [OK] 依赖安装完成
    echo.
)

echo.
echo ============================================================
echo   启动服务
echo ============================================================
echo.
echo 服务信息:
echo   - WebSocket API: http://localhost:8000
echo   - SMTP端口: 8025
echo   - 日志文件: logs\rubbish_mail.log
echo.
echo 按 Ctrl+C 停止服务
echo ============================================================
echo.

REM 设置UTF-8编码
set PYTHONUTF8=1

REM 启动服务
python main.py

pause


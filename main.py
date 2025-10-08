"""
临时邮箱服务主应用

功能:
    - SMTP服务器接收外部邮件
    - WebSocket API供客户端监控邮箱
    - 实时匹配规则并推送邮件
    - 不存储邮件,处理完即丢弃

架构:
    外部邮件 → SMTP服务器 → 解析 → 匹配规则 → WebSocket推送
    
调用链:
    main → app.startup → 启动SMTP服务器
    websocket_endpoint → ConnectionManager.add_connection
    SMTP收到邮件 → ConnectionManager.push_email

启动:
    python main.py
    或
    uvicorn main:app --host 0.0.0.0 --port 8000
"""
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import uvicorn

from core.config import get_settings
from core.auth import init_auth, get_auth
from core.smtp_server import SMTPServer
from core.connection_manager import get_connection_manager
from schemas.request import (
    MonitorRequest,
    MonitorStartMessage,
    ErrorMessage,
    HeartbeatMessage
)


# 配置日志
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rubbish_mail.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# 设置控制台编码为UTF-8（Windows）
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)


# SMTP服务器实例
smtp_server: SMTPServer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global smtp_server
    
    # 启动时
    logger.info("="*60)
    logger.info("启动 Rubbish Mail - 临时邮箱服务")
    logger.info("="*60)
    
    # 加载配置
    settings = get_settings()
    
    # 初始化认证
    init_auth(settings.get_valid_api_keys())
    logger.info("[OK] API认证已初始化")
    
    # 启动SMTP服务器
    # Windows上使用localhost代替0.0.0.0
    smtp_host = settings.smtp.host
    if smtp_host == "0.0.0.0" and sys.platform == 'win32':
        smtp_host = "localhost"
        logger.info("[提示] Windows系统,SMTP地址自动改为localhost")
    
    smtp_server = SMTPServer(
        host=smtp_host,
        port=settings.smtp.port,
        allowed_domain=settings.smtp.allowed_domain
    )
    smtp_server.start()
    logger.info(f"[OK] SMTP服务器: {smtp_host}:{settings.smtp.port}")
    logger.info(f"[OK] 接收域名: {settings.smtp.allowed_domain}")
    
    # WebSocket配置
    logger.info(f"[OK] WebSocket API: {settings.server.host}:{settings.server.port}")
    logger.info(f"[OK] 最大连接数: {settings.monitor.max_connections}")
    logger.info(f"[OK] 连接超时: {settings.monitor.timeout}秒")
    
    logger.info("="*60)
    logger.info("服务已就绪,等待连接...")
    logger.info("="*60)
    
    yield
    
    # 关闭时
    logger.info("="*60)
    logger.info("关闭服务...")
    
    # 停止SMTP服务器
    if smtp_server:
        smtp_server.stop()
    
    logger.info("服务已关闭")
    logger.info("="*60)


app = FastAPI(
    title="Rubbish Mail - 临时邮箱服务",
    description="接收邮件并通过WebSocket实时推送的临时邮箱服务",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """健康检查和状态查询"""
    manager = get_connection_manager()
    settings = get_settings()
    
    return JSONResponse({
        "service": "Rubbish Mail",
        "version": "2.0.0",
        "status": "running",
        "smtp": {
            "host": settings.smtp.host,
            "port": settings.smtp.port,
            "domain": settings.smtp.allowed_domain
        },
        "connections": {
            "active": manager.get_active_count(),
            "max": settings.monitor.max_connections,
            "monitored_emails": manager.get_monitored_emails()
        },
        "timestamp": datetime.now().isoformat()
    })


@app.websocket("/ws/monitor")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket监控端点
    
    客户端连接后需发送MonitorRequest JSON:
    {
        "api_key": "your-api-key",
        "email": "temp@your-domain.com",
        "rules": [
            {
                "type": "keyword",
                "patterns": ["验证码", "code"],
                "search_in": ["subject", "body"]
            }
        ]
    }
    
    服务器会推送以下消息:
    - monitor_start: 监控已启动
    - email_received: 收到匹配的邮件
    - error: 错误信息
    - heartbeat: 心跳(每30秒)
    """
    await websocket.accept()
    
    connection_id = None
    manager = get_connection_manager()
    
    try:
        # 接收监控请求
        data = await websocket.receive_json()
        
        # 验证请求数据
        try:
            request = MonitorRequest(**data)
        except Exception as e:
            await websocket.send_json(
                ErrorMessage(
                    data={"code": "INVALID_REQUEST", "message": f"请求格式错误: {str(e)}"}
                ).model_dump()
            )
            await websocket.close(code=1003)
            return
        
        # 验证API密钥
        auth = get_auth()
        if not auth.verify(request.api_key):
            await websocket.send_json(
                ErrorMessage(
                    data={"code": "UNAUTHORIZED", "message": "API密钥无效"}
                ).model_dump()
            )
            await websocket.close(code=1008)
            return
        
        # 验证邮箱域名
        settings = get_settings()
        email_domain = request.email.split("@")[1]
        if email_domain != settings.smtp.allowed_domain:
            await websocket.send_json(
                ErrorMessage(
                    data={
                        "code": "INVALID_DOMAIN",
                        "message": f"不支持的邮箱域名,仅支持: {settings.smtp.allowed_domain}"
                    }
                ).model_dump()
            )
            await websocket.close(code=1008)
            return
        
        # 检查连接数限制
        if manager.get_active_count() >= settings.monitor.max_connections:
            await websocket.send_json(
                ErrorMessage(
                    data={"code": "TOO_MANY_CONNECTIONS", "message": "连接数已达上限"}
                ).model_dump()
            )
            await websocket.close(code=1008)
            return
        
        # 添加到连接管理器
        connection_id = await manager.add_connection(
            websocket=websocket,
            email=request.email,
            rules=request.rules,
            timeout=settings.monitor.timeout
        )
        
        logger.info(f"新监控: {connection_id} -> {request.email}")
        
        # 发送监控开始消息
        await websocket.send_json(
            MonitorStartMessage(
                data={
                    "message": "监控已启动",
                    "email": request.email,
                    "rules_count": len(request.rules),
                    "timeout": settings.monitor.timeout
                }
            ).model_dump()
        )
        
        # 保持连接,定期发送心跳
        while True:
            try:
                # 等待客户端消息或超时
                await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30秒超时
                )
            except asyncio.TimeoutError:
                # 超时,发送心跳
                try:
                    await websocket.send_json(
                        HeartbeatMessage(
                            data={"timestamp": datetime.now().isoformat()}
                        ).model_dump()
                    )
                except:
                    # 发送失败,连接可能已断开
                    break
    
    except WebSocketDisconnect:
        logger.info(f"客户端断开连接: {connection_id}")
    
    except Exception as e:
        logger.error(f"WebSocket错误: {e}", exc_info=True)
        try:
            await websocket.send_json(
                ErrorMessage(
                    data={"code": "SERVER_ERROR", "message": str(e)}
                ).model_dump()
            )
        except:
            pass
    
    finally:
        # 清理连接
        if connection_id:
            await manager.remove_connection(connection_id)
            logger.info(f"清理连接: {connection_id}")


if __name__ == "__main__":
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        log_level=settings.logging.level.lower()
    )

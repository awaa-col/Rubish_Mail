"""
SMTP服务器模块

功能:
    - 使用aiosmtpd接收外部邮件
    - 解析邮件内容
    - 匹配规则并推送给监听的WebSocket连接
    - 不存储邮件,处理完即丢弃

调用链:
    外部邮件 -> SMTPHandler.handle_DATA -> 解析 -> 匹配规则 -> ConnectionManager.push_email

输入: 外部SMTP连接和邮件数据
输出: 通过ConnectionManager推送给客户端
"""
import asyncio
import logging
from typing import Optional
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP, Envelope, Session

from core.mail_parser import MailParser
from core.connection_manager import get_connection_manager
from utils.matcher import EmailMatcher
from schemas.request import EmailContent


logger = logging.getLogger(__name__)


class RubbishMailHandler:
    """SMTP邮件处理器"""
    
    def __init__(self, allowed_domain: str):
        """
        初始化处理器
        
        输入:
            allowed_domain: 允许的邮箱域名(只接收该域名的邮件)
        """
        self.allowed_domain = allowed_domain.lower()
        self.connection_manager = get_connection_manager()
    
    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope):
        """
        处理接收到的邮件数据
        
        输入:
            server: SMTP服务器实例
            session: SMTP会话
            envelope: 邮件信封(包含发件人、收件人、邮件内容)
            
        输出:
            "250 OK": 接受邮件
            "550 Error": 拒绝邮件
        """
        try:
            # 获取收件人列表
            recipients = envelope.rcpt_tos
            
            logger.info(f"收到邮件: 发件人={envelope.mail_from}, 收件人={recipients}")
            
            # 解析邮件内容
            email_data = MailParser.parse_from_bytes(envelope.content)
            
            if not email_data:
                logger.warning("邮件解析失败,丢弃")
                return "250 OK"  # 返回OK但丢弃邮件
            
            logger.debug(f"邮件主题: {email_data.get('subject')}")
            
            # 处理每个收件人
            for recipient in recipients:
                await self._process_recipient(recipient, email_data)
            
            return "250 OK"
            
        except Exception as e:
            logger.error(f"处理邮件时出错: {e}", exc_info=True)
            return "250 OK"  # 即使出错也返回OK,避免发件方重试
    
    async def _process_recipient(self, recipient: str, email_data: dict):
        """
        处理单个收件人
        
        输入:
            recipient: 收件人邮箱地址
            email_data: 解析后的邮件数据
        """
        try:
            # 提取纯邮箱地址
            recipient_email = MailParser.extract_recipient(recipient).lower()
            
            logger.debug(f"处理收件人: {recipient_email}")
            
            # 检查域名
            if "@" not in recipient_email:
                logger.warning(f"无效的收件人地址: {recipient_email}")
                return
            
            domain = recipient_email.split("@")[1]
            if domain != self.allowed_domain:
                logger.info(f"域名不匹配,丢弃邮件: {recipient_email} (允许: {self.allowed_domain})")
                return
            
            # 查找监听该邮箱的连接
            manager = get_connection_manager()
            
            # 获取所有监控该邮箱的连接
            connection_ids = manager.email_to_connections.get(recipient_email, set()).copy()
            
            if not connection_ids:
                logger.info(f"没有连接监控邮箱 {recipient_email},丢弃邮件")
                return
            
            logger.info(f"找到 {len(connection_ids)} 个连接监控 {recipient_email}")
            
            # 对每个连接进行规则匹配
            for conn_id in connection_ids:
                conn = manager.get_connection(conn_id)
                if not conn:
                    continue
                
                # 匹配规则
                matched, match_description = EmailMatcher.match_any(
                    conn.rules,
                    email_data
                )
                
                if matched:
                    logger.info(f"规则匹配成功 [{conn_id}]: {match_description}")
                    
                    # 构造EmailContent对象
                    email_content = EmailContent(
                        sender=email_data.get("sender", ""),
                        sender_name=email_data.get("sender_name"),
                        subject=email_data.get("subject", ""),
                        body=email_data.get("body", ""),
                        html_body=email_data.get("html_body"),
                        received_time=email_data.get("received_time", ""),
                        matched_rule=match_description
                    )
                    
                    # 推送给客户端
                    await conn.send_email(email_content)
                else:
                    logger.debug(f"规则不匹配 [{conn_id}],不推送")
        
        except Exception as e:
            logger.error(f"处理收件人 {recipient} 时出错: {e}", exc_info=True)


class SMTPServer:
    """SMTP服务器控制器"""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8025,
        allowed_domain: str = "example.com"
    ):
        """
        初始化SMTP服务器
        
        输入:
            host: 监听地址
            port: 监听端口(建议非特权端口8025,生产环境用iptables转发25->8025)
            allowed_domain: 允许的邮箱域名
        """
        self.host = host
        self.port = port
        self.allowed_domain = allowed_domain
        
        # 创建处理器
        self.handler = RubbishMailHandler(allowed_domain)
        
        # 创建控制器
        self.controller = Controller(
            self.handler,
            hostname=host,
            port=port,
            ready_timeout=30  # 增加启动超时时间到30秒
        )
    
    def start(self):
        """
        启动SMTP服务器(同步方法,在新线程中运行)
        
        注意: aiosmtpd的Controller.start()会在新线程中启动事件循环
        """
        logger.info(f"启动SMTP服务器: {self.host}:{self.port}")
        logger.info(f"允许的域名: {self.allowed_domain}")
        self.controller.start()
        logger.info("SMTP服务器已启动")
    
    def stop(self):
        """
        停止SMTP服务器
        """
        logger.info("停止SMTP服务器...")
        self.controller.stop()
        logger.info("SMTP服务器已停止")


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
from core.blacklist import get_blacklist
from utils.matcher import EmailMatcher
from schemas.request import EmailContent


logger = logging.getLogger(__name__)


class RubbishMailHandler:
    """SMTP邮件处理器"""
    
    def __init__(self, allowed_domain: str, max_message_size: int = 10 * 1024 * 1024):
        """
        初始化处理器
        
        输入:
            allowed_domain: 允许的邮箱域名(只接收该域名的邮件)
            max_message_size: 最大邮件大小(字节),默认10MB
        """
        self.allowed_domain = allowed_domain.lower()
        self.max_message_size = max_message_size
        self.connection_manager = get_connection_manager()
        self.blacklist = get_blacklist()
    
    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope):
        """
        处理接收到的邮件数据
        
        输入:
            server: SMTP服务器实例
            session: SMTP会话
            envelope: 邮件信封(包含发件人、收件人、邮件内容)
            
        输出:
            "250 OK": 接受邮件
            "552 Error": 邮件过大
            "554 Error": IP/域名被拉黑
        """
        try:
            # 获取客户端IP
            client_ip = session.peer[0] if session.peer else "unknown"
            
            # 1. 检查IP黑名单
            if await self.blacklist.is_ip_blocked(client_ip):
                logger.warning(f"🚫 拒绝黑名单IP: {client_ip}")
                return "554 IP blocked"
            
            # 2. 检查邮件大小
            message_size = len(envelope.content)
            if message_size > self.max_message_size:
                logger.warning(
                    f"🚫 拒绝超大邮件: {message_size / 1024 / 1024:.2f}MB "
                    f"from {envelope.mail_from} ({client_ip})"
                )
                # 自动拉黑发送超大邮件的IP
                await self.blacklist.add_ip(
                    client_ip, 
                    f"发送超大邮件 ({message_size / 1024 / 1024:.2f}MB)"
                )
                return f"552 Message too large ({message_size / 1024 / 1024:.2f}MB > {self.max_message_size / 1024 / 1024}MB)"
            
            # 3. 检查发件人域名黑名单
            if await self.blacklist.is_sender_blocked(envelope.mail_from):
                logger.warning(f"🚫 拒绝黑名单域名: {envelope.mail_from} ({client_ip})")
                return "554 Sender domain blocked"
            
            # 获取收件人列表
            recipients = envelope.rcpt_tos
            
            logger.info(f"收到邮件: 发件人={envelope.mail_from}, 收件人={recipients}, IP={client_ip}")
            
            # 解析邮件内容
            email_data = MailParser.parse_from_bytes(envelope.content)
            
            if not email_data:
                logger.warning("邮件解析失败,丢弃")
                return "250 OK"  # 返回OK但丢弃邮件
            
            logger.debug(f"邮件主题: {email_data.get('subject')}")
            
            # 处理每个收件人
            has_valid_recipient = False
            for recipient in recipients:
                if await self._process_recipient(recipient, email_data, client_ip, envelope.mail_from):
                    has_valid_recipient = True
            
            # 如果没有任何有效收件人,可能是垃圾邮件,自动拉黑
            if not has_valid_recipient:
                await self.blacklist.auto_block_stranger(client_ip, envelope.mail_from)
            
            return "250 OK"
            
        except Exception as e:
            logger.error(f"处理邮件时出错: {e}", exc_info=True)
            return "250 OK"  # 即使出错也返回OK,避免发件方重试
    
    async def _process_recipient(
        self, 
        recipient: str, 
        email_data: dict, 
        client_ip: str, 
        sender: str
    ) -> bool:
        """
        处理单个收件人
        
        输入:
            recipient: 收件人邮箱地址
            email_data: 解析后的邮件数据
            client_ip: 客户端IP
            sender: 发件人邮箱
            
        输出:
            True: 成功处理(有监控的连接), False: 无监控或域名不匹配
        """
        try:
            # 提取纯邮箱地址
            recipient_email = MailParser.extract_recipient(recipient).lower()
            
            logger.debug(f"处理收件人: {recipient_email}")
            
            # 检查域名
            if "@" not in recipient_email:
                logger.warning(f"无效的收件人地址: {recipient_email}")
                return False
            
            domain = recipient_email.split("@")[1]
            if domain != self.allowed_domain:
                logger.info(f"域名不匹配,丢弃邮件: {recipient_email} (允许: {self.allowed_domain})")
                return False
            
            # 查找监听该邮箱的连接
            manager = get_connection_manager()
            
            # 获取所有监控该邮箱的连接
            connection_ids = manager.email_to_connections.get(recipient_email, set()).copy()
            
            if not connection_ids:
                logger.info(f"没有连接监控邮箱 {recipient_email},丢弃邮件")
                return False
            
            logger.info(f"找到 {len(connection_ids)} 个连接监控 {recipient_email}")
            
            # 有监控连接,说明这是合法收件人
            # 对每个连接进行规则匹配
            matched_any = False
            for conn_id in connection_ids:
                conn = manager.get_connection(conn_id)
                if not conn:
                    continue
                
                # 学习发件人域名到白名单(从用户规则中提取)
                if '@' in sender:
                    sender_domain = sender.split('@')[1].lower()
                    await self.blacklist.learn_whitelist_domain(sender_domain)
                
                # 匹配规则
                matched, match_description = EmailMatcher.match_any(
                    conn.rules,
                    email_data
                )
                
                if matched:
                    matched_any = True
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
            
            return True  # 有监控连接,返回True
        
        except Exception as e:
            logger.error(f"处理收件人 {recipient} 时出错: {e}", exc_info=True)
            return False


class SMTPServer:
    """SMTP服务器控制器"""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8025,
        allowed_domain: str = "example.com",
        max_message_size: int = 10 * 1024 * 1024
    ):
        """
        初始化SMTP服务器
        
        输入:
            host: 监听地址
            port: 监听端口(建议非特权端口8025,生产环境用iptables转发25->8025)
            allowed_domain: 允许的邮箱域名
            max_message_size: 最大邮件大小(字节),默认10MB
        """
        self.host = host
        self.port = port
        self.allowed_domain = allowed_domain
        self.max_message_size = max_message_size
        
        # 创建处理器
        self.handler = RubbishMailHandler(allowed_domain, max_message_size)
        
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


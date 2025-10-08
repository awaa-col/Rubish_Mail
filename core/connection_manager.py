"""
WebSocket连接管理器

功能:
    - 管理所有活跃的WebSocket连接
    - 维护邮箱地址到连接的映射关系
    - 提供邮件推送接口

调用链:
    main.py -> ConnectionManager.add/remove
    smtp_server.py -> ConnectionManager.push_email

输入/输出: 见各方法说明
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime

from fastapi import WebSocket
from schemas.request import MatchRule, EmailContent, EmailReceivedMessage


logger = logging.getLogger(__name__)


class Connection:
    """单个WebSocket连接信息"""
    
    def __init__(
        self,
        websocket: WebSocket,
        email: str,
        rules: List[MatchRule],
        timeout: int = 300
    ):
        """
        初始化连接
        
        输入:
            websocket: WebSocket连接对象
            email: 监控的邮箱地址
            rules: 匹配规则列表
            timeout: 超时时间(秒)
        """
        self.websocket = websocket
        self.email = email.lower()  # 统一转小写
        self.rules = rules
        self.timeout = timeout
        self.created_at = datetime.now()
        self.connection_id = f"{self.email}_{self.created_at.timestamp()}"
        self.timeout_task: Optional[asyncio.Task] = None
    
    async def send_email(self, email_content: EmailContent) -> bool:
        """
        推送邮件给客户端
        
        输入:
            email_content: 邮件内容对象
            
        输出:
            True: 推送成功
            False: 推送失败
        """
        try:
            message = EmailReceivedMessage(data=email_content)
            await self.websocket.send_json(message.model_dump())
            logger.info(f"推送邮件到 {self.connection_id}: {email_content.subject}")
            return True
        except Exception as e:
            logger.error(f"推送邮件失败 {self.connection_id}: {e}")
            return False
    
    def start_timeout(self, callback):
        """
        启动超时检测
        
        输入:
            callback: 超时回调函数
        """
        async def timeout_handler():
            await asyncio.sleep(self.timeout)
            logger.info(f"连接超时: {self.connection_id}")
            await callback(self.connection_id)
        
        self.timeout_task = asyncio.create_task(timeout_handler())
    
    def cancel_timeout(self):
        """取消超时检测"""
        if self.timeout_task:
            self.timeout_task.cancel()


class ConnectionManager:
    """WebSocket连接管理器(单例)"""
    
    def __init__(self):
        """
        初始化管理器
        """
        # 所有连接: {connection_id: Connection}
        self.connections: Dict[str, Connection] = {}
        
        # 邮箱到连接的映射: {email: Set[connection_id]}
        self.email_to_connections: Dict[str, Set[str]] = {}
        
        self._lock = asyncio.Lock()
    
    async def add_connection(
        self,
        websocket: WebSocket,
        email: str,
        rules: List[MatchRule],
        timeout: int = 300
    ) -> str:
        """
        添加新连接
        
        输入:
            websocket: WebSocket对象
            email: 监控的邮箱地址
            rules: 匹配规则
            timeout: 超时时间(秒)
            
        输出:
            connection_id: 连接ID
        """
        async with self._lock:
            email = email.lower()
            
            # 创建连接对象
            conn = Connection(websocket, email, rules, timeout)
            
            # 添加到连接表
            self.connections[conn.connection_id] = conn
            
            # 添加到邮箱映射
            if email not in self.email_to_connections:
                self.email_to_connections[email] = set()
            self.email_to_connections[email].add(conn.connection_id)
            
            logger.info(
                f"新连接: {conn.connection_id}, "
                f"监控: {email}, "
                f"规则数: {len(rules)}, "
                f"当前总连接数: {len(self.connections)}"
            )
            
            # 启动超时检测
            conn.start_timeout(self.remove_connection)
            
            return conn.connection_id
    
    async def remove_connection(self, connection_id: str) -> bool:
        """
        移除连接
        
        输入:
            connection_id: 连接ID
            
        输出:
            True: 移除成功
            False: 连接不存在
        """
        async with self._lock:
            if connection_id not in self.connections:
                return False
            
            conn = self.connections[connection_id]
            
            # 取消超时任务
            conn.cancel_timeout()
            
            # 从邮箱映射中移除
            if conn.email in self.email_to_connections:
                self.email_to_connections[conn.email].discard(connection_id)
                if not self.email_to_connections[conn.email]:
                    del self.email_to_connections[conn.email]
            
            # 从连接表中移除
            del self.connections[connection_id]
            
            logger.info(
                f"移除连接: {connection_id}, "
                f"当前总连接数: {len(self.connections)}"
            )
            
            return True
    
    async def push_email_to_address(
        self,
        email_address: str,
        email_content: EmailContent
    ) -> int:
        """
        推送邮件到监控指定邮箱的所有连接
        
        输入:
            email_address: 邮箱地址
            email_content: 邮件内容
            
        输出:
            成功推送的连接数
        """
        email_address = email_address.lower()
        
        # 查找监控该邮箱的连接
        connection_ids = self.email_to_connections.get(email_address, set()).copy()
        
        if not connection_ids:
            logger.debug(f"没有连接监控邮箱: {email_address}")
            return 0
        
        logger.info(f"找到 {len(connection_ids)} 个连接监控 {email_address}")
        
        success_count = 0
        failed_connections = []
        
        # 推送到所有监控该邮箱的连接
        for conn_id in connection_ids:
            conn = self.connections.get(conn_id)
            if not conn:
                continue
            
            success = await conn.send_email(email_content)
            if success:
                success_count += 1
            else:
                failed_connections.append(conn_id)
        
        # 清理推送失败的连接
        for conn_id in failed_connections:
            await self.remove_connection(conn_id)
        
        return success_count
    
    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """
        获取连接对象
        
        输入:
            connection_id: 连接ID
            
        输出:
            Connection对象或None
        """
        return self.connections.get(connection_id)
    
    def get_active_count(self) -> int:
        """
        获取当前活跃连接数
        
        输出:
            连接数
        """
        return len(self.connections)
    
    def get_monitored_emails(self) -> List[str]:
        """
        获取所有被监控的邮箱地址
        
        输出:
            邮箱地址列表
        """
        return list(self.email_to_connections.keys())


# 全局连接管理器实例
_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """
    获取全局连接管理器实例
    
    输出:
        ConnectionManager实例
    """
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


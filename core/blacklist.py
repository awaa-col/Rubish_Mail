"""
黑名单管理模块

功能:
    - 管理IP黑名单和域名黑名单
    - 自动记录垃圾邮件发送者
    - 持久化存储黑名单
    - 提供查询和管理接口

输入: IP地址、域名、发件人邮箱
输出: 是否在黑名单中
"""
import json
import logging
from typing import Set, Dict, Optional
from pathlib import Path
from datetime import datetime
import asyncio


logger = logging.getLogger(__name__)


class Blacklist:
    """黑名单管理器"""
    
    def __init__(self, storage_path: str = "data/blacklist.json"):
        """
        初始化黑名单管理器
        
        输入:
            storage_path: 黑名单存储文件路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # IP黑名单: {ip: {"reason": str, "added_at": str, "count": int}}
        self.blocked_ips: Dict[str, Dict] = {}
        
        # 域名黑名单: {domain: {"reason": str, "added_at": str, "count": int}}
        self.blocked_domains: Dict[str, Dict] = {}
        
        # 白名单域名(用户规则中的合法域名,自动学习)
        self.whitelist_domains: Set[str] = set()
        
        self._lock = asyncio.Lock()
        
        # 加载黑名单
        self._load()
    
    def _load(self):
        """从文件加载黑名单"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.blocked_ips = data.get('blocked_ips', {})
                    self.blocked_domains = data.get('blocked_domains', {})
                    self.whitelist_domains = set(data.get('whitelist_domains', []))
                    logger.info(
                        f"已加载黑名单: {len(self.blocked_ips)}个IP, "
                        f"{len(self.blocked_domains)}个域名, "
                        f"{len(self.whitelist_domains)}个白名单域名"
                    )
        except Exception as e:
            logger.error(f"加载黑名单失败: {e}")
    
    def _save(self):
        """保存黑名单到文件"""
        try:
            data = {
                'blocked_ips': self.blocked_ips,
                'blocked_domains': self.blocked_domains,
                'whitelist_domains': list(self.whitelist_domains),
                'updated_at': datetime.now().isoformat()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存黑名单失败: {e}")
    
    async def is_ip_blocked(self, ip: str) -> bool:
        """
        检查IP是否在黑名单中
        
        输入:
            ip: IP地址
            
        输出:
            True: 已拉黑, False: 未拉黑
        """
        return ip in self.blocked_ips
    
    async def is_domain_blocked(self, domain: str) -> bool:
        """
        检查域名是否在黑名单中
        
        输入:
            domain: 域名
            
        输出:
            True: 已拉黑, False: 未拉黑
        """
        domain = domain.lower()
        return domain in self.blocked_domains
    
    async def is_sender_blocked(self, sender_email: str) -> bool:
        """
        检查发件人是否在黑名单中(检查域名)
        
        输入:
            sender_email: 发件人邮箱
            
        输出:
            True: 已拉黑, False: 未拉黑
        """
        if '@' not in sender_email:
            return False
        
        domain = sender_email.split('@')[1].lower()
        return await self.is_domain_blocked(domain)
    
    async def add_ip(
        self, 
        ip: str, 
        reason: str = "垃圾邮件发送者",
        save: bool = True
    ) -> bool:
        """
        添加IP到黑名单
        
        输入:
            ip: IP地址
            reason: 拉黑原因
            save: 是否立即保存
            
        输出:
            True: 添加成功, False: 已存在
        """
        async with self._lock:
            if ip in self.blocked_ips:
                # 已存在,增加计数
                self.blocked_ips[ip]['count'] += 1
                if save:
                    self._save()
                return False
            
            self.blocked_ips[ip] = {
                'reason': reason,
                'added_at': datetime.now().isoformat(),
                'count': 1
            }
            
            logger.warning(f"🚫 拉黑IP: {ip} (原因: {reason})")
            
            if save:
                self._save()
            
            return True
    
    async def add_domain(
        self, 
        domain: str, 
        reason: str = "垃圾邮件域名",
        save: bool = True
    ) -> bool:
        """
        添加域名到黑名单
        
        输入:
            domain: 域名
            reason: 拉黑原因
            save: 是否立即保存
            
        输出:
            True: 添加成功, False: 已存在
        """
        async with self._lock:
            domain = domain.lower()
            
            if domain in self.blocked_domains:
                # 已存在,增加计数
                self.blocked_domains[domain]['count'] += 1
                if save:
                    self._save()
                return False
            
            self.blocked_domains[domain] = {
                'reason': reason,
                'added_at': datetime.now().isoformat(),
                'count': 1
            }
            
            logger.warning(f"🚫 拉黑域名: {domain} (原因: {reason})")
            
            if save:
                self._save()
            
            return True
    
    async def remove_ip(self, ip: str) -> bool:
        """
        从黑名单移除IP
        
        输入:
            ip: IP地址
            
        输出:
            True: 移除成功, False: 不存在
        """
        async with self._lock:
            if ip in self.blocked_ips:
                del self.blocked_ips[ip]
                self._save()
                logger.info(f"✓ 移除IP黑名单: {ip}")
                return True
            return False
    
    async def remove_domain(self, domain: str) -> bool:
        """
        从黑名单移除域名
        
        输入:
            domain: 域名
            
        输出:
            True: 移除成功, False: 不存在
        """
        async with self._lock:
            domain = domain.lower()
            if domain in self.blocked_domains:
                del self.blocked_domains[domain]
                self._save()
                logger.info(f"✓ 移除域名黑名单: {domain}")
                return True
            return False
    
    async def learn_whitelist_domain(self, domain: str):
        """
        学习白名单域名(从用户规则中提取)
        
        输入:
            domain: 域名
        """
        async with self._lock:
            domain = domain.lower()
            if domain not in self.whitelist_domains:
                self.whitelist_domains.add(domain)
                self._save()
                logger.info(f"✓ 学习白名单域名: {domain}")
    
    async def auto_block_stranger(
        self, 
        ip: str, 
        sender_email: str
    ) -> bool:
        """
        自动拉黑陌生发件人(不在白名单中的域名)
        
        输入:
            ip: 发件人IP
            sender_email: 发件人邮箱
            
        输出:
            True: 已拉黑, False: 未拉黑(在白名单中)
        """
        if '@' not in sender_email:
            return False
        
        domain = sender_email.split('@')[1].lower()
        
        # 检查是否在白名单中
        if domain in self.whitelist_domains:
            return False
        
        # 拉黑IP和域名
        await self.add_ip(ip, f"未授权域名发件: {domain}", save=False)
        await self.add_domain(domain, "未授权域名", save=False)
        
        # 批量保存
        self._save()
        
        return True
    
    def get_stats(self) -> Dict:
        """
        获取黑名单统计信息
        
        输出:
            统计信息字典
        """
        return {
            'blocked_ips_count': len(self.blocked_ips),
            'blocked_domains_count': len(self.blocked_domains),
            'whitelist_domains_count': len(self.whitelist_domains),
            'blocked_ips': list(self.blocked_ips.keys()),
            'blocked_domains': list(self.blocked_domains.keys()),
            'whitelist_domains': list(self.whitelist_domains)
        }
    
    def get_detailed_list(self) -> Dict:
        """
        获取详细黑名单列表
        
        输出:
            详细黑名单字典
        """
        return {
            'blocked_ips': self.blocked_ips,
            'blocked_domains': self.blocked_domains,
            'whitelist_domains': list(self.whitelist_domains)
        }


# 全局黑名单实例
_blacklist: Optional[Blacklist] = None


def get_blacklist() -> Blacklist:
    """
    获取全局黑名单实例
    
    输出:
        Blacklist实例
    """
    global _blacklist
    if _blacklist is None:
        _blacklist = Blacklist()
    return _blacklist


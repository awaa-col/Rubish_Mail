"""
API认证模块

功能:
    - 验证客户端提供的API密钥
    - 提供FastAPI依赖注入接口

输入: API密钥字符串
输出: 验证结果(成功/失败)
"""
from typing import List
from fastapi import HTTPException, status


class APIKeyAuth:
    """API密钥认证器"""
    
    def __init__(self, valid_keys: List[str]):
        """
        初始化认证器
        
        输入:
            valid_keys: 有效的API密钥列表
        """
        self.valid_keys = set(valid_keys)  # 使用set提高查找效率
    
    def verify(self, api_key: str) -> bool:
        """
        验证API密钥
        
        输入:
            api_key: 要验证的API密钥
            
        输出:
            True: 验证成功
            False: 验证失败
        """
        return api_key in self.valid_keys
    
    def verify_or_raise(self, api_key: str) -> None:
        """
        验证API密钥,失败则抛出HTTP异常
        
        输入:
            api_key: 要验证的API密钥
            
        异常:
            HTTPException: 认证失败时抛出401错误
        """
        if not self.verify(api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )


# 全局认证器实例(由main.py初始化)
_auth_instance: APIKeyAuth = None


def init_auth(valid_keys: List[str]) -> None:
    """
    初始化全局认证器
    
    输入:
        valid_keys: 有效的API密钥列表
    """
    global _auth_instance
    _auth_instance = APIKeyAuth(valid_keys)


def get_auth() -> APIKeyAuth:
    """
    获取全局认证器实例
    
    输出:
        APIKeyAuth实例
        
    异常:
        RuntimeError: 认证器未初始化
    """
    if _auth_instance is None:
        raise RuntimeError("Auth not initialized. Call init_auth() first.")
    return _auth_instance


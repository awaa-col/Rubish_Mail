"""
配置加载模块

功能:
    - 从config.yml读取邮箱服务器配置
    - 从环境变量读取API密钥
    - 提供全局配置访问接口

输入: config.yml文件, .env环境变量
输出: Settings配置对象
"""
import os
from typing import List, Optional
from pathlib import Path

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


# 加载.env文件
load_dotenv()


class ServerConfig(BaseSettings):
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False


class SMTPConfig(BaseSettings):
    """SMTP服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8025
    allowed_domain: str
    max_message_size: int = 10  # MB


class MonitorConfig(BaseSettings):
    """监控配置"""
    max_connections: int = 10
    timeout: int = 300  # 秒


class BlacklistConfig(BaseSettings):
    """黑名单配置"""
    storage: str = "data/blacklist.json"
    auto_block: bool = True


class LogRotationConfig(BaseSettings):
    """日志轮转配置"""
    keep_days: int = 7
    max_size_mb: int = 100
    check_interval: int = 3600


class LoggingConfig(BaseSettings):
    """日志配置"""
    level: str = "INFO"
    file: str = "logs/rubbish_mail.log"
    rotation: LogRotationConfig = LogRotationConfig()


class Settings(BaseSettings):
    """全局配置"""
    # API密钥(从环境变量读取)
    api_key: str = Field(alias="API_KEY")
    api_keys: Optional[List[str]] = Field(default=None, alias="API_KEYS")
    
    # 各模块配置
    server: ServerConfig
    smtp: SMTPConfig
    monitor: MonitorConfig
    blacklist: BlacklistConfig
    logging: LoggingConfig
    
    @field_validator("api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, v):
        """解析多个API密钥(逗号分隔)"""
        if v is None:
            return None
        if isinstance(v, str):
            return [key.strip() for key in v.split(",") if key.strip()]
        return v
    
    def get_valid_api_keys(self) -> List[str]:
        """
        获取所有有效的API密钥
        
        输出: 包含所有有效API密钥的列表
        """
        keys = [self.api_key]
        if self.api_keys:
            keys.extend(self.api_keys)
        return list(set(keys))  # 去重
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # 允许额外字段


def load_config(config_path: str = "config.yml") -> Settings:
    """
    加载配置文件
    
    输入:
        config_path: 配置文件路径,默认为config.yml
        
    输出:
        Settings: 配置对象
        
    异常:
        FileNotFoundError: 配置文件不存在
        yaml.YAMLError: YAML解析错误
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(
            f"配置文件不存在: {config_path}\n"
            f"请复制 config.example.yml 为 config.yml 并填写配置"
        )
    
    with open(config_file, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    
    # 从环境变量获取API密钥
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError(
            "未找到API_KEY环境变量\n"
            "请创建.env文件并设置: API_KEY=your-secret-key"
        )
    
    api_keys = os.getenv("API_KEYS")
    
    # 创建配置对象
    # 注意: api_key 和 api_keys 会自动从环境变量读取(.env文件)
    
    # 处理logging配置中的rotation子配置
    logging_config = config_data.get("logging", {})
    rotation_data = logging_config.get("rotation", {})
    logging_config["rotation"] = LogRotationConfig(**rotation_data)
    
    return Settings(
        server=ServerConfig(**config_data.get("server", {})),
        smtp=SMTPConfig(**config_data.get("smtp", {})),
        monitor=MonitorConfig(**config_data.get("monitor", {})),
        blacklist=BlacklistConfig(**config_data.get("blacklist", {})),
        logging=LoggingConfig(**logging_config)
    )


# 全局配置实例(延迟加载)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    获取全局配置实例
    
    输出: Settings配置对象
    """
    global _settings
    if _settings is None:
        _settings = load_config()
    return _settings


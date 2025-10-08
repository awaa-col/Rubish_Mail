"""
请求和响应数据模型

功能:
    - 定义WebSocket请求/响应的数据结构
    - 使用Pydantic进行数据验证
    - 提供类型安全的数据访问

输入/输出: 见各个Schema的字段说明
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator, EmailStr


class MatchRule(BaseModel):
    """
    邮件匹配规则
    
    字段:
        type: 匹配类型,支持 "keyword"(关键词) 或 "regex"(正则表达式)
        patterns: 匹配模式列表,多个模式之间为OR关系
        search_in: 搜索范围,支持 "sender"(发件人), "subject"(主题), "body"(正文)
    """
    type: Literal["keyword", "regex"] = Field(
        description="匹配类型: keyword=关键词匹配, regex=正则表达式匹配"
    )
    patterns: List[str] = Field(
        min_length=1,
        description="匹配模式列表,至少包含一个模式"
    )
    search_in: List[Literal["sender", "subject", "body"]] = Field(
        default=["sender", "subject", "body"],
        description="搜索范围: sender=发件人, subject=主题, body=正文"
    )
    
    @field_validator("patterns")
    @classmethod
    def validate_patterns(cls, v):
        """验证模式列表非空"""
        if not v or all(not p.strip() for p in v):
            raise ValueError("patterns不能为空")
        return [p.strip() for p in v if p.strip()]


class MonitorRequest(BaseModel):
    """
    监控请求(客户端发送到服务端)
    
    字段:
        api_key: API密钥,用于身份验证
        email: 要监控的邮箱地址(必须属于allowed_domain)
        rules: 匹配规则列表,只要有一个规则匹配就推送
    """
    api_key: str = Field(
        min_length=1,
        description="API密钥"
    )
    email: EmailStr = Field(
        description="要监控的邮箱地址,例如: user@example.com"
    )
    rules: List[MatchRule] = Field(
        min_length=1,
        description="匹配规则列表,至少包含一个规则"
    )
    
    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v):
        """验证邮箱格式"""
        if not v or "@" not in v:
            raise ValueError("邮箱格式不正确")
        return v.lower()


class EmailContent(BaseModel):
    """
    邮件内容(服务端推送给客户端)
    
    字段:
        sender: 发件人邮箱
        sender_name: 发件人姓名(如果有)
        subject: 邮件主题
        body: 邮件正文(纯文本)
        html_body: 邮件正文(HTML格式,如果有)
        received_time: 收到时间(ISO格式)
        matched_rule: 匹配的规则描述
    """
    sender: str = Field(description="发件人邮箱")
    sender_name: Optional[str] = Field(default=None, description="发件人姓名")
    subject: str = Field(description="邮件主题")
    body: str = Field(description="邮件正文(纯文本)")
    html_body: Optional[str] = Field(default=None, description="邮件正文(HTML)")
    received_time: str = Field(description="收到时间(ISO格式)")
    matched_rule: str = Field(description="匹配的规则描述")


class WebSocketMessage(BaseModel):
    """
    WebSocket消息基类
    
    字段:
        type: 消息类型
        data: 消息数据(根据type不同而不同)
    """
    type: str = Field(description="消息类型")
    data: Optional[dict] = Field(default=None, description="消息数据")


class MonitorStartMessage(WebSocketMessage):
    """监控开始消息"""
    type: Literal["monitor_start"] = "monitor_start"
    data: dict = Field(
        default={"message": "监控已启动"},
        description="包含监控状态信息"
    )


class EmailReceivedMessage(WebSocketMessage):
    """邮件接收消息"""
    type: Literal["email_received"] = "email_received"
    data: EmailContent = Field(description="邮件内容")


class ErrorMessage(WebSocketMessage):
    """错误消息"""
    type: Literal["error"] = "error"
    data: dict = Field(description="错误信息,包含code和message字段")


class HeartbeatMessage(WebSocketMessage):
    """心跳消息"""
    type: Literal["heartbeat"] = "heartbeat"
    data: dict = Field(
        default={"timestamp": ""},
        description="心跳时间戳"
    )


"""
邮件解析模块

功能:
    - 从原始邮件数据解析邮件内容
    - 提取发件人、主题、正文
    - 处理MIME编码和多种字符集

输入: 原始邮件字节流或Message对象
输出: 解析后的邮件数据字典
"""
import email
from email.header import decode_header
from email.message import Message
from typing import Optional, Dict, Any
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class MailParser:
    """邮件解析器"""
    
    @staticmethod
    def parse_from_bytes(email_bytes: bytes) -> Optional[Dict[str, Any]]:
        """
        从字节流解析邮件
        
        输入:
            email_bytes: 原始邮件字节流
            
        输出:
            包含sender, subject, body等字段的字典
            解析失败返回None
        """
        try:
            msg = email.message_from_bytes(email_bytes)
            return MailParser.parse_message(msg)
        except Exception as e:
            logger.error(f"从字节流解析邮件失败: {e}")
            return None
    
    @staticmethod
    def parse_from_string(email_str: str) -> Optional[Dict[str, Any]]:
        """
        从字符串解析邮件
        
        输入:
            email_str: 原始邮件字符串
            
        输出:
            包含sender, subject, body等字段的字典
            解析失败返回None
        """
        try:
            msg = email.message_from_string(email_str)
            return MailParser.parse_message(msg)
        except Exception as e:
            logger.error(f"从字符串解析邮件失败: {e}")
            return None
    
    @staticmethod
    def parse_message(msg: Message) -> Optional[Dict[str, Any]]:
        """
        解析email.message.Message对象
        
        输入:
            msg: email.message.Message对象
            
        输出:
            包含以下字段的字典:
            - sender: str - 发件人邮箱
            - sender_name: str | None - 发件人姓名
            - subject: str - 邮件主题
            - body: str - 纯文本正文
            - html_body: str | None - HTML正文
            - received_time: str - 接收时间(ISO格式)
        """
        try:
            # 解析发件人
            sender = MailParser._decode_header_value(msg.get("From", ""))
            sender_name = None
            
            # 提取邮箱地址和姓名
            if "<" in sender and ">" in sender:
                sender_name = sender.split("<")[0].strip().strip('"')
                sender = sender.split("<")[1].split(">")[0]
            
            # 解析主题
            subject = MailParser._decode_header_value(msg.get("Subject", ""))
            
            # 解析正文
            body = ""
            html_body = None
            
            if msg.is_multipart():
                # 多部分邮件
                for part in msg.walk():
                    content_type = part.get_content_type()
                    
                    if content_type == "text/plain" and not body:
                        body = MailParser._get_email_body(part)
                    elif content_type == "text/html" and not html_body:
                        html_body = MailParser._get_email_body(part)
            else:
                # 单部分邮件
                content_type = msg.get_content_type()
                if content_type == "text/plain":
                    body = MailParser._get_email_body(msg)
                elif content_type == "text/html":
                    html_body = MailParser._get_email_body(msg)
                    body = html_body  # 如果只有HTML,也给body赋值
            
            # 解析时间
            date_str = msg.get("Date", "")
            received_time = datetime.now().isoformat()  # 默认当前时间
            
            # TODO: 可以尝试解析Date字段为datetime
            
            return {
                "sender": sender,
                "sender_name": sender_name,
                "subject": subject,
                "body": body,
                "html_body": html_body,
                "received_time": received_time
            }
            
        except Exception as e:
            logger.error(f"解析Message对象失败: {e}")
            return None
    
    @staticmethod
    def _decode_header_value(value: str) -> str:
        """
        解码邮件头部值(处理MIME编码)
        
        输入:
            value: 邮件头部原始值
            
        输出:
            解码后的字符串
        """
        if not value:
            return ""
        
        decoded_parts = decode_header(value)
        result = []
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    # 尝试使用指定编码
                    result.append(part.decode(encoding or "utf-8"))
                except:
                    # 失败则尝试UTF-8,忽略错误
                    try:
                        result.append(part.decode("utf-8", errors="ignore"))
                    except:
                        # 再失败则尝试GBK
                        try:
                            result.append(part.decode("gbk", errors="ignore"))
                        except:
                            result.append(str(part))
            else:
                result.append(str(part))
        
        return " ".join(result)
    
    @staticmethod
    def _get_email_body(msg: Message) -> str:
        """
        获取邮件正文
        
        输入:
            msg: email.message.Message对象
            
        输出:
            正文字符串
        """
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                try:
                    return payload.decode(charset, errors="ignore")
                except:
                    # 如果指定字符集失败,尝试常见字符集
                    for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
                        try:
                            return payload.decode(enc, errors="ignore")
                        except:
                            continue
                    # 都失败则返回空
                    return ""
        except Exception as e:
            logger.warning(f"获取邮件正文失败: {e}")
        
        return ""
    
    @staticmethod
    def extract_recipient(mail_to: str) -> str:
        """
        从To字段提取收件人邮箱地址
        
        输入:
            mail_to: To字段原始值,如 "Name <user@example.com>"
            
        输出:
            纯邮箱地址,如 "user@example.com"
        """
        if not mail_to:
            return ""
        
        # 移除空白
        mail_to = mail_to.strip()
        
        # 如果包含<>,提取其中的地址
        if "<" in mail_to and ">" in mail_to:
            start = mail_to.index("<") + 1
            end = mail_to.index(">")
            return mail_to[start:end].strip().lower()
        
        # 否则直接返回(可能就是纯地址)
        return mail_to.lower()


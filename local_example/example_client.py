"""
客户端示例代码

演示如何使用邮箱监控服务:
1. 连接WebSocket
2. 发送监控请求
3. 接收邮件推送
4. 处理验证码等信息

使用:
    python example_client.py
"""
import asyncio
import json
import re
from typing import Optional, List
from html.parser import HTMLParser

import websockets


class LinkExtractor(HTMLParser):
    """从HTML中提取链接"""
    
    def __init__(self):
        super().__init__()
        self.links: List[tuple] = []  # [(url, text), ...]
        self.current_link = None
        self.current_text = []
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href':
                    self.current_link = value
                    self.current_text = []
                    break
    
    def handle_endtag(self, tag):
        if tag == 'a' and self.current_link:
            text = ''.join(self.current_text).strip()
            self.links.append((self.current_link, text or self.current_link))
            self.current_link = None
            self.current_text = []
    
    def handle_data(self, data):
        if self.current_link is not None:
            self.current_text.append(data)


class MailMonitorClient:
    """邮箱监控客户端"""
    
    def __init__(self, ws_url: str, api_key: str):
        """
        初始化客户端
        
        参数:
            ws_url: WebSocket服务地址,例如 "ws://localhost:8000/ws/monitor"
            api_key: API密钥
        """
        self.ws_url = ws_url
        self.api_key = api_key
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
    
    async def monitor(
        self,
        email: str,
        keywords: list[str] = None,
        regex_patterns: list[str] = None,
        search_in: list[str] = None,
        auto_disconnect: bool = True  # 收到邮件后是否自动断开
    ):
        """
        开始监控邮箱
        
        参数:
            email: 要监控的邮箱地址
            keywords: 关键词列表(与regex_patterns二选一或同时使用)
            regex_patterns: 正则表达式列表
            search_in: 搜索范围,默认["sender", "subject", "body"]
            auto_disconnect: 收到邮件后是否自动断开(默认True)
        """
        if search_in is None:
            search_in = ["sender", "subject", "body"]
        
        # 构建监控请求
        rules = []
        
        if keywords:
            rules.append({
                "type": "keyword",
                "patterns": keywords,
                "search_in": search_in
            })
        
        if regex_patterns:
            rules.append({
                "type": "regex",
                "patterns": regex_patterns,
                "search_in": search_in
            })
        
        if not rules:
            raise ValueError("必须提供keywords或regex_patterns")
        
        request = {
            "api_key": self.api_key,
            "email": email,
            "rules": rules
        }
        
        # 连接WebSocket
        async with websockets.connect(self.ws_url) as websocket:
            self.websocket = websocket
            
            # 发送监控请求
            await websocket.send(json.dumps(request))
            print(f"✓ 已发送监控请求: {email}")
            
            # 接收消息
            async for message in websocket:
                should_disconnect = await self._handle_message(message, auto_disconnect)
                if should_disconnect:
                    print("\n✓ 已收到邮件,主动断开连接")
                    break
    
    async def _handle_message(self, message: str, auto_disconnect: bool = True):
        """
        处理服务端消息
        
        返回:
            bool: 是否应该断开连接
        """
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            msg_data = data.get("data", {})
            
            if msg_type == "monitor_start":
                print(f"✓ {msg_data.get('message')}")
                print(f"  监控邮箱: {msg_data.get('email')}")
                print(f"  规则数量: {msg_data.get('rules_count')}")
                print("  等待邮件中...\n")
            
            elif msg_type == "email_received":
                print("=" * 60)
                print("📧 收到新邮件!")
                print(f"发件人: {msg_data.get('sender')}")
                if msg_data.get('sender_name'):
                    print(f"发件人姓名: {msg_data.get('sender_name')}")
                print(f"主题: {msg_data.get('subject')}")
                print(f"匹配规则: {msg_data.get('matched_rule')}")
                print(f"时间: {msg_data.get('received_time')}")
                print("-" * 60)
                print("正文:")
                print(msg_data.get('body')[:500])  # 只显示前500字符
                if len(msg_data.get('body', '')) > 500:
                    print("... (内容过长,已截断)")
                
                # 提取并显示HTML中的链接
                html_body = msg_data.get('html_body')
                if html_body:
                    links = self._extract_links_from_html(html_body)
                    if links:
                        print("-" * 60)
                        print("🔗 邮件中的链接:")
                        for i, (url, text) in enumerate(links, 1):
                            print(f"  [{i}] {text}")
                            print(f"      {url}")
                
                print("=" * 60)
                print()
                
                # 尝试提取验证码
                self._extract_verification_code(msg_data)
                
                # 收到邮件后返回True表示可以断开
                if auto_disconnect:
                    return True
            
            elif msg_type == "error":
                print(f"❌ 错误: {msg_data.get('message')}")
                print(f"   错误代码: {msg_data.get('code')}")
            
            elif msg_type == "heartbeat":
                # 心跳消息,静默处理
                pass
            
            else:
                print(f"⚠ 未知消息类型: {msg_type}")
        
        except json.JSONDecodeError as e:
            print(f"❌ 解析消息失败: {e}")
        except Exception as e:
            print(f"❌ 处理消息时出错: {e}")
        
        return False  # 默认不断开
    
    def _extract_links_from_html(self, html_content: str) -> List[tuple]:
        """
        从HTML中提取所有链接
        
        输入:
            html_content: HTML内容字符串
            
        输出:
            [(url, text), ...] 链接列表
        """
        try:
            extractor = LinkExtractor()
            extractor.feed(html_content)
            return extractor.links
        except Exception as e:
            print(f"⚠ 提取链接失败: {e}")
            return []
    
    def _extract_verification_code(self, email_data: dict):
        """
        尝试从邮件中提取验证码
        
        常见验证码格式:
        - 6位数字
        - 4位数字
        - 6位字母数字混合
        """
        body = email_data.get('body', '')
        subject = email_data.get('subject', '')
        
        # 常见验证码正则
        patterns = [
            (r'验证码[^\d]*(\d{6})', "6位数字验证码"),
            (r'code[^\w]*([A-Z0-9]{6})', "6位验证码"),
            (r'验证码[^\d]*(\d{4})', "4位数字验证码"),
            (r'(\d{6})', "6位数字"),
            (r'([A-Z0-9]{6})', "6位字符"),
        ]
        
        for pattern, desc in patterns:
            # 先在主题中查找
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                print(f"🔑 提取到{desc} (主题): {match.group(1)}")
                return match.group(1)
            
            # 再在正文中查找
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                print(f"🔑 提取到{desc} (正文): {match.group(1)}")
                return match.group(1)
        
        return None


async def example_1_keyword_monitor():
    """
    示例1: 使用关键词监控
    
    场景: 监控包含"验证码"关键词的邮件
    """
    print("示例1: 关键词监控")
    print("-" * 60)
    
    client = MailMonitorClient(
        ws_url="ws://localhost:7000/ws/monitor",
        api_key="test-local-key-123456"  # 替换为你的API密钥
    )
    
    await client.monitor(
        email="test@example.com",  # 替换为你的邮箱
        keywords=["验证码", "verification", "code"],
        search_in=["subject", "body"],
        auto_disconnect=True  # 收到邮件后自动断开
    )


async def example_2_regex_monitor():
    """
    示例2: 使用正则表达式监控
    
    场景: 监控包含6位数字的邮件
    """
    print("示例2: 正则表达式监控")
    print("-" * 60)
    
    client = MailMonitorClient(
        ws_url="ws://localhost:8000/ws/monitor",
        api_key="your-api-key-here"
    )
    
    await client.monitor(
        email="test@example.com",
        regex_patterns=[r"\d{6}"],  # 匹配6位数字
        search_in=["body"]
    )


async def example_3_combined_monitor():
    """
    示例3: 组合监控
    
    场景: 同时使用关键词和正则表达式
    """
    print("示例3: 组合监控")
    print("-" * 60)
    
    client = MailMonitorClient(
        ws_url="ws://localhost:8000/ws/monitor",
        api_key="your-api-key-here"
    )
    
    await client.monitor(
        email="test@example.com",
        keywords=["验证码"],
        regex_patterns=[r"code:\s*([A-Z0-9]{6})"],
        search_in=["subject", "body"]
    )


async def example_4_sender_monitor():
    """
    示例4: 监控特定发件人
    
    场景: 只监控来自特定域名的邮件
    """
    print("示例4: 监控特定发件人")
    print("-" * 60)
    
    client = MailMonitorClient(
        ws_url="ws://localhost:8000/ws/monitor",
        api_key="your-api-key-here"
    )
    
    await client.monitor(
        email="test@example.com",
        regex_patterns=[r"@github\.com$"],  # 只监控GitHub的邮件
        search_in=["sender"]
    )


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║          Rubbish Mail - 邮箱监控客户端示例                ║
╚════════════════════════════════════════════════════════════╝

请先配置:
1. 在 .env 中设置 API_KEY
2. 在 config.yml 中配置IMAP服务器
3. 启动服务: python main.py
4. 修改下面的示例代码,填入你的邮箱和API密钥
5. 运行此文件

""")
    
    # 运行示例(选择一个)
    try:
        asyncio.run(example_1_keyword_monitor())
        # asyncio.run(example_2_regex_monitor())
        # asyncio.run(example_3_combined_monitor())
        # asyncio.run(example_4_sender_monitor())
    except KeyboardInterrupt:
        print("\n\n✓ 已停止监控")
    except Exception as e:
        print(f"\n❌ 错误: {e}")


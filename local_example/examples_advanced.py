"""
高级规则示例

展示如何使用发件人、主题、正文规则
"""
import asyncio
import json
import websockets


WS_URL = "ws://localhost:8000/ws/monitor"
API_KEY = "your-api-key"  # 改成你的密钥


async def example_1_filter_by_sender():
    """
    示例1: 只接收GitHub的邮件
    
    场景: 只关心来自GitHub的通知
    """
    print("示例1: 只监控GitHub的邮件")
    print("=" * 60)
    
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({
            "api_key": API_KEY,
            "email": "temp@your-domain.com",
            "rules": [
                {
                    "type": "regex",
                    "patterns": ["@github\\.com$"],  # 发件人以@github.com结尾
                    "search_in": ["sender"]
                }
            ]
        }))
        
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "email_received":
                email = data["data"]
                print(f"✓ 收到GitHub邮件")
                print(f"  发件人: {email['sender']}")
                print(f"  主题: {email['subject']}")
                break


async def example_2_subject_keyword():
    """
    示例2: 主题包含特定关键词
    
    场景: 只要主题包含"验证"、"verification"、"code"之一
    """
    print("示例2: 主题关键词匹配")
    print("=" * 60)
    
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({
            "api_key": API_KEY,
            "email": "temp@your-domain.com",
            "rules": [
                {
                    "type": "keyword",
                    "patterns": ["验证", "verification", "code"],
                    "search_in": ["subject"]  # 只搜索主题
                }
            ]
        }))
        
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "email_received":
                email = data["data"]
                print(f"✓ 主题匹配!")
                print(f"  主题: {email['subject']}")
                print(f"  匹配规则: {email['matched_rule']}")
                break


async def example_3_body_verification_code():
    """
    示例3: 正文包含6位验证码
    
    场景: 提取正文中的6位数字验证码
    """
    print("示例3: 提取6位验证码")
    print("=" * 60)
    
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({
            "api_key": API_KEY,
            "email": "temp@your-domain.com",
            "rules": [
                {
                    "type": "regex",
                    "patterns": ["\\d{6}"],  # 6位数字
                    "search_in": ["body"]
                }
            ]
        }))
        
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "email_received":
                email = data["data"]
                
                # 提取验证码
                import re
                match = re.search(r'\d{6}', email['body'])
                if match:
                    code = match.group()
                    print(f"✓ 提取到验证码: {code}")
                    print(f"  完整正文: {email['body'][:100]}...")
                break


async def example_4_multiple_senders():
    """
    示例4: 监控多个特定发件人
    
    场景: 只接收来自GitHub、GitLab、Bitbucket的邮件
    """
    print("示例4: 监控多个发件人")
    print("=" * 60)
    
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({
            "api_key": API_KEY,
            "email": "temp@your-domain.com",
            "rules": [
                {
                    "type": "regex",
                    "patterns": [
                        "@github\\.com$",
                        "@gitlab\\.com$",
                        "@bitbucket\\.org$"
                    ],
                    "search_in": ["sender"]
                }
            ]
        }))
        
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "email_received":
                email = data["data"]
                print(f"✓ 收到代码托管平台邮件")
                print(f"  发件人: {email['sender']}")
                print(f"  主题: {email['subject']}")
                break


async def example_5_combined_rules():
    """
    示例5: 组合规则 - 发件人+主题+正文
    
    场景: 
    - 来自特定域名
    - 或主题包含"重要"
    - 或正文包含链接
    """
    print("示例5: 组合规则")
    print("=" * 60)
    
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({
            "api_key": API_KEY,
            "email": "temp@your-domain.com",
            "rules": [
                # 规则1: 来自example.com
                {
                    "type": "regex",
                    "patterns": ["@example\\.com$"],
                    "search_in": ["sender"]
                },
                # 规则2: 主题包含"重要"或"urgent"
                {
                    "type": "keyword",
                    "patterns": ["重要", "urgent"],
                    "search_in": ["subject"]
                },
                # 规则3: 正文包含HTTP链接
                {
                    "type": "regex",
                    "patterns": ["https?://[^\\s]+"],
                    "search_in": ["body"]
                }
            ]
        }))
        
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "email_received":
                email = data["data"]
                print(f"✓ 匹配到邮件!")
                print(f"  发件人: {email['sender']}")
                print(f"  主题: {email['subject']}")
                print(f"  匹配规则: {email['matched_rule']}")
                break


async def example_6_advanced_verification():
    """
    示例6: 高级验证码提取
    
    场景: 匹配多种验证码格式
    """
    print("示例6: 高级验证码提取")
    print("=" * 60)
    
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({
            "api_key": API_KEY,
            "email": "temp@your-domain.com",
            "rules": [
                {
                    "type": "regex",
                    "patterns": [
                        "验证码[^\\d]*(\\d{4,6})",           # 中文验证码
                        "verification code[^\\w]*([A-Z0-9]{4,6})",  # 英文
                        "code:\\s*([A-Z0-9]{4,6})",        # code: 格式
                        "OTP[^\\w]*([0-9]{6})",            # OTP
                        "PIN[^\\d]*(\\d{4,6})"             # PIN
                    ],
                    "search_in": ["body"]
                }
            ]
        }))
        
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "email_received":
                email = data["data"]
                print(f"✓ 收到验证邮件!")
                print(f"  正文预览: {email['body'][:200]}...")
                print(f"  匹配规则: {email['matched_rule']}")
                
                # 提取验证码
                import re
                for pattern in [
                    r'验证码[^\d]*(\d{4,6})',
                    r'verification code[^\w]*([A-Z0-9]{4,6})',
                    r'code:\s*([A-Z0-9]{4,6})',
                    r'OTP[^\w]*([0-9]{6})',
                    r'PIN[^\d]*(\d{4,6})'
                ]:
                    match = re.search(pattern, email['body'], re.IGNORECASE)
                    if match:
                        print(f"  提取验证码: {match.group(1)}")
                        break
                break


async def example_7_exclude_pattern():
    """
    示例7: 排除特定发件人(使用负向断言)
    
    场景: 接收所有邮件,除了来自spam.com的
    """
    print("示例7: 排除特定发件人")
    print("=" * 60)
    
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({
            "api_key": API_KEY,
            "email": "temp@your-domain.com",
            "rules": [
                {
                    "type": "regex",
                    "patterns": [
                        "^(?!.*@spam\\.com$).*@.*\\.com$"  # 不是@spam.com的.com邮箱
                    ],
                    "search_in": ["sender"]
                }
            ]
        }))
        
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "email_received":
                email = data["data"]
                print(f"✓ 收到邮件(非spam.com)")
                print(f"  发件人: {email['sender']}")
                break


async def example_8_multi_field_search():
    """
    示例8: 多字段搜索
    
    场景: 发件人、主题、正文任意位置包含"urgent"
    """
    print("示例8: 多字段搜索")
    print("=" * 60)
    
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({
            "api_key": API_KEY,
            "email": "temp@your-domain.com",
            "rules": [
                {
                    "type": "keyword",
                    "patterns": ["urgent", "紧急", "重要"],
                    "search_in": ["sender", "subject", "body"]  # 搜索所有字段
                }
            ]
        }))
        
        async for msg in ws:
            data = json.loads(msg)
            if data["type"] == "email_received":
                email = data["data"]
                print(f"✓ 发现紧急邮件!")
                print(f"  匹配位置: {email['matched_rule']}")
                break


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║          Rubbish Mail - 高级规则示例                      ║
╚════════════════════════════════════════════════════════════╝

请先:
1. 启动服务: python main.py
2. 修改此文件的 API_KEY 和邮箱地址
3. 运行示例

选择要运行的示例:
""")
    
    examples = {
        "1": ("只监控GitHub邮件", example_1_filter_by_sender),
        "2": ("主题关键词匹配", example_2_subject_keyword),
        "3": ("提取6位验证码", example_3_body_verification_code),
        "4": ("监控多个发件人", example_4_multiple_senders),
        "5": ("组合规则", example_5_combined_rules),
        "6": ("高级验证码提取", example_6_advanced_verification),
        "7": ("排除特定发件人", example_7_exclude_pattern),
        "8": ("多字段搜索", example_8_multi_field_search),
    }
    
    for key, (desc, _) in examples.items():
        print(f"{key}. {desc}")
    
    choice = input("\n请选择(1-8): ").strip()
    
    if choice in examples:
        try:
            asyncio.run(examples[choice][1]())
        except KeyboardInterrupt:
            print("\n\n✓ 已停止")
        except Exception as e:
            print(f"\n❌ 错误: {e}")
    else:
        print("无效选择")


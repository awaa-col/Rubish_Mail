"""
本地测试 - 模拟发送邮件到SMTP服务器

使用方法:
1. 启动服务: python main.py
2. 运行此脚本: python test_send_email.py
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time


def send_test_email(
    to_email: str,
    subject: str,
    body: str,
    from_email: str = "test@example.com",
    smtp_host: str = "localhost",
    smtp_port: int = 8025
):
    """
    发送测试邮件到本地SMTP服务器
    
    参数:
        to_email: 收件人邮箱
        subject: 邮件主题
        body: 邮件正文
        from_email: 发件人邮箱
        smtp_host: SMTP服务器地址
        smtp_port: SMTP服务器端口
    """
    print(f"发送测试邮件...")
    print(f"  收件人: {to_email}")
    print(f"  主题: {subject}")
    print(f"  正文: {body[:50]}...")
    
    # 创建邮件
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # 添加正文
    msg.attach(MIMEText(body, 'plain'))
    
    # 发送邮件
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.sendmail(from_email, [to_email], msg.as_string())
            print(f"✓ 邮件发送成功!")
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        raise


def test_scenario_1_verification_code():
    """
    测试场景1: 验证码邮件
    """
    print("\n" + "="*60)
    print("测试场景1: 验证码邮件")
    print("="*60)
    
    send_test_email(
        to_email="test@example.com",  # 改成你配置的域名
        subject="邮箱验证 - 请确认您的账户",
        body="""
您好!

感谢您注册我们的服务。

您的验证码是: 123456

此验证码将在15分钟后过期。

如果这不是您本人的操作,请忽略此邮件。

祝好!
        """,
        from_email="noreply@example.com"
    )


def test_scenario_2_github_notification():
    """
    测试场景2: GitHub通知
    """
    print("\n" + "="*60)
    print("测试场景2: GitHub通知")
    print("="*60)
    
    send_test_email(
        to_email="test@example.com",
        subject="[GitHub] New issue opened",
        body="""
A new issue has been opened in your repository.

Issue #123: Bug in email parser

Click here to view: https://github.com/user/repo/issues/123
        """,
        from_email="notifications@github.com"
    )


def test_scenario_3_html_email():
    """
    测试场景3: HTML邮件
    """
    print("\n" + "="*60)
    print("测试场景3: HTML邮件")
    print("="*60)
    
    msg = MIMEMultipart('alternative')
    msg['From'] = "service@example.com"
    msg['To'] = "test@example.com"
    msg['Subject'] = "欢迎使用我们的服务"
    
    # 纯文本版本
    text = """
您好!

您的验证码是: 654321

请在10分钟内使用此验证码完成注册。
    """
    
    # HTML版本
    html = """
    <html>
    <body>
        <h2>欢迎!</h2>
        <p>您的验证码是: <strong style="color: red;">654321</strong></p>
        <p>请在10分钟内使用此验证码完成注册。</p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP("localhost", 8025) as server:
            server.sendmail(
                "service@example.com",
                ["test@example.com"],
                msg.as_string()
            )
            print(f"✓ HTML邮件发送成功!")
    except Exception as e:
        print(f"❌ 发送失败: {e}")


def test_scenario_4_multiple_patterns():
    """
    测试场景4: 多种验证码格式
    """
    print("\n" + "="*60)
    print("测试场景4: 多种验证码格式")
    print("="*60)
    
    test_cases = [
        ("中文验证码", "您的验证码: 123456"),
        ("英文验证码", "Your verification code is 789012"),
        ("code格式", "Please use this code: ABC123"),
        ("OTP格式", "Your OTP: 456789"),
        ("PIN格式", "Your PIN is: 9876"),
    ]
    
    for name, body in test_cases:
        print(f"\n发送: {name}")
        send_test_email(
            to_email="test@example.com",
            subject=f"测试: {name}",
            body=body,
            from_email="test@example.com"
        )
        time.sleep(0.5)  # 稍微延迟避免太快


def test_scenario_5_sender_filter():
    """
    测试场景5: 测试发件人过滤
    """
    print("\n" + "="*60)
    print("测试场景5: 发件人过滤")
    print("="*60)
    
    senders = [
        ("GitHub", "notifications@github.com"),
        ("GitLab", "noreply@gitlab.com"),
        ("其他服务", "info@random.com"),
    ]
    
    for name, sender in senders:
        print(f"\n发送来自: {name} ({sender})")
        send_test_email(
            to_email="test@example.com",
            subject=f"来自{name}的通知",
            body=f"这是来自 {name} 的测试邮件",
            from_email=sender
        )
        time.sleep(0.5)


def batch_send_test():
    """
    批量发送测试邮件
    """
    print("\n" + "="*60)
    print("批量测试")
    print("="*60)
    
    for i in range(5):
        print(f"\n发送第 {i+1} 封邮件...")
        send_test_email(
            to_email="test@example.com",
            subject=f"测试邮件 #{i+1}",
            body=f"这是第 {i+1} 封测试邮件,验证码: {100000 + i}",
            from_email=f"test{i}@example.com"
        )
        time.sleep(1)


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║          Rubbish Mail - 本地测试工具                      ║
╚════════════════════════════════════════════════════════════╝

本工具用于本地测试SMTP服务器和WebSocket推送功能

使用步骤:
1. 启动服务: python main.py
2. 启动客户端监听(另一个终端): python example_client.py
3. 运行此脚本发送测试邮件

注意: 修改邮件中的收件人地址为你配置的域名!
""")
    
    print("\n请选择测试场景:")
    print("1. 验证码邮件")
    print("2. GitHub通知")
    print("3. HTML邮件")
    print("4. 多种验证码格式")
    print("5. 发件人过滤")
    print("6. 批量测试")
    print("0. 全部测试")
    
    choice = input("\n请选择(0-6): ").strip()
    
    scenarios = {
        "1": test_scenario_1_verification_code,
        "2": test_scenario_2_github_notification,
        "3": test_scenario_3_html_email,
        "4": test_scenario_4_multiple_patterns,
        "5": test_scenario_5_sender_filter,
        "6": batch_send_test,
    }
    
    try:
        if choice == "0":
            # 运行所有测试
            for func in scenarios.values():
                func()
                time.sleep(2)
        elif choice in scenarios:
            scenarios[choice]()
        else:
            print("无效选择")
            
        print("\n" + "="*60)
        print("✓ 测试完成!")
        print("="*60)
        print("\n检查客户端是否收到邮件推送~")
        
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


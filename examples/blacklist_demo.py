"""
黑名单API使用示例

演示如何通过API管理黑名单
"""
import requests
import json

# 配置
API_BASE = "http://localhost:8000"
API_KEY = "your-api-key-here"  # 替换为你的API密钥

headers = {
    "Authorization": f"Bearer {API_KEY}"
}


def get_blacklist_stats():
    """获取黑名单统计"""
    print("=" * 60)
    print("📊 黑名单统计")
    print("=" * 60)
    
    response = requests.get(f"{API_BASE}/api/blacklist", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 拉黑IP数量: {data['blocked_ips_count']}")
        print(f"✓ 拉黑域名数量: {data['blocked_domains_count']}")
        print(f"✓ 白名单域名数量: {data['whitelist_domains_count']}")
        print()
        
        if data['blocked_ips']:
            print("拉黑的IP:")
            for ip in data['blocked_ips']:
                print(f"  - {ip}")
        
        if data['blocked_domains']:
            print("\n拉黑的域名:")
            for domain in data['blocked_domains']:
                print(f"  - {domain}")
        
        if data['whitelist_domains']:
            print("\n白名单域名:")
            for domain in data['whitelist_domains']:
                print(f"  - {domain}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        print(response.text)
    
    print()


def get_blacklist_detail():
    """获取详细黑名单"""
    print("=" * 60)
    print("📋 详细黑名单")
    print("=" * 60)
    
    response = requests.get(f"{API_BASE}/api/blacklist/detail", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        print("拉黑的IP (详细):")
        for ip, info in data['blocked_ips'].items():
            print(f"  {ip}:")
            print(f"    原因: {info['reason']}")
            print(f"    添加时间: {info['added_at']}")
            print(f"    拦截次数: {info['count']}")
        
        print("\n拉黑的域名 (详细):")
        for domain, info in data['blocked_domains'].items():
            print(f"  {domain}:")
            print(f"    原因: {info['reason']}")
            print(f"    添加时间: {info['added_at']}")
            print(f"    拦截次数: {info['count']}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
    
    print()


def add_ip_to_blacklist(ip: str, reason: str = "手动添加"):
    """添加IP到黑名单"""
    print(f"➕ 添加IP到黑名单: {ip}")
    
    response = requests.post(
        f"{API_BASE}/api/blacklist/ip/{ip}",
        params={"reason": reason},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print(f"✓ {data['message']}")
        else:
            print(f"⚠ {data['message']}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
    
    print()


def remove_ip_from_blacklist(ip: str):
    """从黑名单移除IP"""
    print(f"➖ 从黑名单移除IP: {ip}")
    
    response = requests.delete(
        f"{API_BASE}/api/blacklist/ip/{ip}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ {data['message']}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        print(response.text)
    
    print()


def add_domain_to_blacklist(domain: str, reason: str = "手动添加"):
    """添加域名到黑名单"""
    print(f"➕ 添加域名到黑名单: {domain}")
    
    response = requests.post(
        f"{API_BASE}/api/blacklist/domain/{domain}",
        params={"reason": reason},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print(f"✓ {data['message']}")
        else:
            print(f"⚠ {data['message']}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
    
    print()


def remove_domain_from_blacklist(domain: str):
    """从黑名单移除域名"""
    print(f"➖ 从黑名单移除域名: {domain}")
    
    response = requests.delete(
        f"{API_BASE}/api/blacklist/domain/{domain}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ {data['message']}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        print(response.text)
    
    print()


def main():
    """主函数"""
    print("\n黑名单管理示例\n")
    
    try:
        # 1. 查看当前黑名单统计
        get_blacklist_stats()
        
        # 2. 添加IP到黑名单
        add_ip_to_blacklist("1.2.3.4", "测试IP")
        
        # 3. 添加域名到黑名单
        add_domain_to_blacklist("spam.com", "垃圾邮件域名")
        
        # 4. 再次查看统计
        get_blacklist_stats()
        
        # 5. 查看详细信息
        get_blacklist_detail()
        
        # 6. 移除测试条目
        remove_ip_from_blacklist("1.2.3.4")
        remove_domain_from_blacklist("spam.com")
        
        # 7. 最终统计
        get_blacklist_stats()
        
        print("✓ 演示完成!")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器,请确保服务已启动")
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()


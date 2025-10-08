# DNS配置指南

主人,部署临时邮箱服务,**DNS配置是必须的**!不然外部邮件发不进来哦~

---

## 为什么需要配置DNS?

当其他邮件服务器要给 `user@your-domain.com` 发邮件时:
1. 查询 `your-domain.com` 的 **MX记录**
2. 找到邮件服务器地址
3. 连接该服务器的25端口
4. 发送邮件

所以你必须配置MX记录,告诉全世界:"发给我域名的邮件,都发到这台服务器!"

---

## 必需的DNS记录

假设:
- 你的域名: `your-domain.com`
- 你的服务器IP: `1.2.3.4`

### 1. A记录 (必须)

```
类型: A
主机记录: mail
记录值: 1.2.3.4
TTL: 600
```

**作用**: 让 `mail.your-domain.com` 指向你的服务器IP

---

### 2. MX记录 (必须)

```
类型: MX
主机记录: @
记录值: mail.your-domain.com
优先级: 10
TTL: 600
```

**作用**: 告诉所有人,"发给 @your-domain.com 的邮件,发到 mail.your-domain.com"

---

### 3. SPF记录 (强烈推荐)

```
类型: TXT
主机记录: @
记录值: v=spf1 mx ~all
TTL: 600
```

**作用**: 防止别人伪造你的域名发垃圾邮件,提高收信成功率

---

### 4. PTR反向解析 (可选,但推荐)

这个需要在你的VPS提供商那里设置,不是在域名DNS:

```
IP: 1.2.3.4  →  mail.your-domain.com
```

**作用**: 让其他邮件服务器信任你,防止被当成垃圾邮件

---

## 常见域名注册商配置示例

### 阿里云(万网)

1. 登录 [阿里云DNS控制台](https://dns.console.aliyun.com/)
2. 选择你的域名 → 解析设置
3. 添加记录:

| 记录类型 | 主机记录 | 记录值 | 优先级 | TTL |
|---------|---------|--------|--------|-----|
| A       | mail    | 1.2.3.4 | -     | 600 |
| MX      | @       | mail.your-domain.com | 10 | 600 |
| TXT     | @       | v=spf1 mx ~all | - | 600 |

---

### 腾讯云DNSPod

1. 登录 [DNSPod控制台](https://console.dnspod.cn/)
2. 我的域名 → 选择域名 → 记录管理
3. 添加记录(同上表)

---

### Cloudflare

1. 登录 [Cloudflare](https://dash.cloudflare.com/)
2. 选择域名 → DNS → Records
3. Add record:

| Type | Name | Content | Priority | Proxy |
|------|------|---------|----------|-------|
| A    | mail | 1.2.3.4 | -        | ❌ (DNS only) |
| MX   | @    | mail.your-domain.com | 10 | - |
| TXT  | @    | v=spf1 mx ~all | - | - |

**注意**: A记录的Proxy必须关闭(DNS only),MX记录不支持CDN!

---

### Namesilo / GoDaddy / Namecheap

基本流程相同:
1. 进入DNS管理页面
2. 添加A记录、MX记录、TXT记录
3. 保存

---

## 验证DNS配置

### 方法1: 使用dig命令(Linux/Mac)

```bash
# 检查A记录
dig mail.your-domain.com

# 检查MX记录
dig MX your-domain.com

# 检查TXT记录
dig TXT your-domain.com
```

### 方法2: 使用nslookup(Windows)

```powershell
# 检查A记录
nslookup mail.your-domain.com

# 检查MX记录
nslookup -type=MX your-domain.com
```

### 方法3: 在线工具

- [MXToolbox](https://mxtoolbox.com/)
- [DNSChecker](https://dnschecker.org/)

---

## 服务器端口配置

DNS配好后,还需要确保服务器端口开放:

### 1. 开放SMTP端口

```bash
# 检查端口是否开放
sudo netstat -tulnp | grep 8025

# 如果使用firewall(CentOS/RHEL)
sudo firewall-cmd --zone=public --add-port=8025/tcp --permanent
sudo firewall-cmd --reload

# 如果使用ufw(Ubuntu/Debian)
sudo ufw allow 8025/tcp
sudo ufw reload

# 如果使用iptables
sudo iptables -A INPUT -p tcp --dport 8025 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

### 2. 端口转发(25 → 8025)

因为我们用非特权端口8025,需要转发标准SMTP端口25:

```bash
# 使用iptables转发
sudo iptables -t nat -A PREROUTING -p tcp --dport 25 -j REDIRECT --to-port 8025
sudo iptables-save > /etc/iptables/rules.v4

# 或使用rinetd(更简单)
sudo apt install rinetd
echo "0.0.0.0 25 0.0.0.0 8025" | sudo tee -a /etc/rinetd.conf
sudo service rinetd restart
```

**为什么不直接用25?**  
因为25端口需要root权限,使用8025更安全,通过转发即可。

---

## 云服务器注意事项

### 阿里云ECS

默认**封禁25端口**!你需要:
1. 提交工单申请解封25端口
2. 或使用465端口(SMTPS)

### 腾讯云CVM

同样默认封禁25端口,需要申请解封。

### AWS EC2

默认限制25端口,需要填表申请移除限制。

### 甲骨云 / 其他VPS

一般不封25端口,可以直接使用。

---

## 测试邮件收发

### 1. 发送测试邮件

从Gmail/QQ邮箱发送一封邮件到 `test@your-domain.com`

### 2. 查看日志

```bash
tail -f logs/rubbish_mail.log
```

应该看到:
```
INFO - 收到邮件: 发件人=xxx@gmail.com, 收件人=['test@your-domain.com']
INFO - 邮件主题: Test Email
```

### 3. 如果没收到

检查清单:
- [ ] DNS生效了吗?(等待10-60分钟)
- [ ] 服务器25端口开放了吗?
- [ ] 端口转发配置正确吗?
- [ ] 服务正常运行吗?(`python main.py`)
- [ ] 有WebSocket连接监控该邮箱吗?

---

## 完整配置示例

### 域名DNS设置

| 类型 | 主机记录 | 记录值 | 优先级 |
|------|---------|--------|--------|
| A    | mail    | 123.45.67.89 | - |
| MX   | @       | mail.your-domain.com | 10 |
| TXT  | @       | v=spf1 mx ~all | - |

### 服务器配置

```yaml
# config.yml
smtp:
  host: "0.0.0.0"
  port: 8025
  allowed_domain: "your-domain.com"
```

### iptables转发

```bash
sudo iptables -t nat -A PREROUTING -p tcp --dport 25 -j REDIRECT --to-port 8025
```

### 启动服务

```bash
python main.py
```

---

## 常见问题

### Q: DNS修改后多久生效?

A: 一般10-60分钟,最多24小时。用 `dig` 命令检查。

### Q: 为什么别人发邮件给我收不到?

A: 常见原因:
1. DNS还没生效
2. 25端口没开
3. 服务没启动
4. 云服务器封了25端口

### Q: 收到邮件但没推送?

A: 检查:
1. 有WebSocket连接监控该邮箱吗?
2. 规则写对了吗?
3. 查看日志 `logs/rubbish_mail.log`

### Q: 可以不配置DNS吗?

A: 不行!没有MX记录,外部邮件服务器不知道往哪发邮件。

---

[白岚] 主人,DNS配置虽然看起来麻烦,但其实就是添加几条记录而已~

按照上面的步骤一步步来,肯定能配好的!
如果遇到问题,记得查日志哦~ (๑•̀ㅂ•́)و✧


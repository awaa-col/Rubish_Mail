# 贡献指南

感谢你考虑为 Rubbish Mail 做贡献! 🎉

---

## 🤝 如何贡献

### 报告Bug

如果你发现了bug，请[创建一个Issue](../../issues/new)并包含:

1. **描述**: 清楚地描述问题
2. **重现步骤**: 如何重现这个bug
3. **期望行为**: 你期望发生什么
4. **实际行为**: 实际发生了什么
5. **环境信息**:
   - 操作系统(Windows/Linux/macOS)
   - Python版本
   - 是否使用Docker
6. **日志**: 相关的错误日志

### 提出新功能

如果你有新功能的想法:

1. 先搜索[现有Issues](../../issues)，确保没有重复
2. [创建一个Issue](../../issues/new)说明:
   - 功能描述
   - 使用场景
   - 可能的实现方式

### 提交代码

1. **Fork 仓库**
   ```bash
   # 在GitHub上点击Fork按钮
   git clone https://github.com/YOUR-USERNAME/rubbish_mail.git
   cd rubbish_mail
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **开发**
   - 编写代码
   - 遵循现有代码风格
   - 添加必要的注释
   - 更新相关文档

4. **测试**
   ```bash
   # 本地测试
   python test_full_workflow.py
   
   # 如果添加了新功能,请添加测试
   ```

5. **提交**
   ```bash
   git add .
   git commit -m "feat: 添加XXX功能"
   # 或
   git commit -m "fix: 修复XXX问题"
   ```

6. **推送**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建 Pull Request**
   - 在GitHub上创建PR
   - 填写PR模板
   - 等待审核

---

## 📝 代码规范

### Python代码风格

遵循 [PEP 8](https://pep8.org/):

```python
# 好 ✅
async def send_email(
    recipient: str,
    subject: str,
    body: str
) -> bool:
    """
    发送邮件
    
    参数:
        recipient: 收件人邮箱
        subject: 邮件主题
        body: 邮件正文
    
    返回:
        bool: 是否发送成功
    """
    pass

# 不好 ❌
async def sendEmail(recipient,subject,body):
    pass
```

### 提交信息规范

使用[约定式提交](https://www.conventionalcommits.org/zh-hans/):

```bash
# 格式
<类型>: <描述>

[可选的正文]

[可选的脚注]

# 类型
feat:     新功能
fix:      Bug修复
docs:     文档更新
style:    代码格式(不影响功能)
refactor: 重构(不是新功能也不是Bug修复)
perf:     性能优化
test:     测试相关
chore:    构建/工具相关

# 示例
feat: 添加邮件附件支持
fix: 修复WebSocket断开后资源未释放的问题
docs: 更新Docker部署指南
refactor: 重构连接管理器代码
```

### 文档规范

- 所有公共API必须有docstring
- 复杂逻辑添加注释
- 更新相关的.md文档

---

## 🧪 测试

### 运行测试

```bash
# 单元测试(如果有)
pytest

# 集成测试
python test_full_workflow.py

# 手动测试
python example_client.py
python test_send_email.py
```

### 添加测试

如果你添加了新功能,请添加相应的测试:

```python
# tests/test_your_feature.py
import pytest
from core.your_module import your_function

def test_your_function():
    """测试你的功能"""
    result = your_function()
    assert result == expected_value
```

---

## 📁 项目结构

```
rubbish_mail/
├── core/              # 核心模块
│   ├── smtp_server.py      # SMTP服务器
│   ├── connection_manager.py  # 连接管理
│   ├── mail_parser.py      # 邮件解析
│   └── config.py           # 配置管理
├── schemas/           # 数据模型
├── utils/             # 工具函数
├── 白岚/              # 中文文档
├── main.py            # 主程序
└── tests/             # 测试文件
```

### 添加新模块

如果你要添加新模块:

1. 在`core/`或`utils/`下创建新文件
2. 在`__init__.py`中导出
3. 添加docstring和类型提示
4. 更新相关文档

---

## 🌍 国际化

目前项目主要支持中文，如果你想添加其他语言:

1. 在`i18n/`目录下添加翻译文件(如果没有此目录请创建)
2. 更新README添加其他语言版本
3. 翻译`白岚/`下的文档

---

## 🐛 调试技巧

### 启用DEBUG日志

```yaml
# config.yml
logging:
  level: "DEBUG"
```

### 查看详细日志

```bash
# Windows
Get-Content logs\rubbish_mail.log -Wait -Tail 50

# Linux/Mac
tail -f logs/rubbish_mail.log
```

### 使用Python调试器

```python
import pdb; pdb.set_trace()
# 或
import ipdb; ipdb.set_trace()
```

---

## 📋 Pull Request 检查清单

提交PR前确保:

- [ ] 代码遵循项目代码风格
- [ ] 添加了必要的docstring和注释
- [ ] 更新了相关文档
- [ ] 测试通过
- [ ] 提交信息遵循规范
- [ ] PR描述清晰完整

---

## 🎯 优先级

我们目前最需要的贡献:

### 高优先级
- 🐛 Bug修复
- 📝 文档改进
- 🧪 测试覆盖

### 中优先级
- ✨ 新功能
- 🎨 代码优化
- 🚀 性能提升

### 低优先级
- 🌍 国际化
- 📊 监控面板
- 🔐 高级认证

---

## 💬 联系方式

- **Issues**: [GitHub Issues](../../issues)
- **Discussions**: [GitHub Discussions](../../discussions)

---

## 📄 许可证

贡献的代码将遵循 [MIT License](LICENSE)。

---

**感谢你的贡献!** 🙏

每一个Issue、PR和建议都让项目变得更好! ❤️


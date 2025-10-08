"""
规则匹配器

功能:
    - 支持关键词匹配(不区分大小写)
    - 支持正则表达式匹配
    - 在指定字段(发件人/主题/正文)中搜索

输入:
    rule: MatchRule对象
    email_data: 包含sender, subject, body的字典
    
输出:
    (bool, str): (是否匹配, 匹配描述)
"""
import re
from typing import Tuple, Dict, Any
from schemas.request import MatchRule


class EmailMatcher:
    """邮件匹配器"""
    
    @staticmethod
    def match(rule: MatchRule, email_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        检查邮件是否匹配规则
        
        输入:
            rule: 匹配规则对象
            email_data: 邮件数据字典,包含:
                - sender: 发件人 (str)
                - subject: 主题 (str)
                - body: 正文 (str)
        
        输出:
            (是否匹配, 匹配描述)
            - 匹配: (True, "关键词 'xxx' 匹配于主题")
            - 不匹配: (False, "")
        """
        # 获取要搜索的字段内容
        search_contents = {}
        if "sender" in rule.search_in:
            search_contents["发件人"] = email_data.get("sender", "")
        if "subject" in rule.search_in:
            search_contents["主题"] = email_data.get("subject", "")
        if "body" in rule.search_in:
            search_contents["正文"] = email_data.get("body", "")
        
        # 根据匹配类型执行匹配
        if rule.type == "keyword":
            return EmailMatcher._match_keyword(rule.patterns, search_contents)
        elif rule.type == "regex":
            return EmailMatcher._match_regex(rule.patterns, search_contents)
        else:
            return False, f"未知的匹配类型: {rule.type}"
    
    @staticmethod
    def _match_keyword(patterns: list[str], search_contents: Dict[str, str]) -> Tuple[bool, str]:
        """
        关键词匹配(不区分大小写)
        
        输入:
            patterns: 关键词列表
            search_contents: 要搜索的内容字典 {字段名: 内容}
            
        输出:
            (是否匹配, 匹配描述)
        """
        for field_name, content in search_contents.items():
            content_lower = content.lower()
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if pattern_lower in content_lower:
                    return True, f"关键词 '{pattern}' 匹配于{field_name}"
        
        return False, ""
    
    @staticmethod
    def _match_regex(patterns: list[str], search_contents: Dict[str, str]) -> Tuple[bool, str]:
        """
        正则表达式匹配
        
        输入:
            patterns: 正则表达式列表
            search_contents: 要搜索的内容字典 {字段名: 内容}
            
        输出:
            (是否匹配, 匹配描述)
        """
        for field_name, content in search_contents.items():
            for pattern in patterns:
                try:
                    if re.search(pattern, content, re.IGNORECASE):
                        return True, f"正则 '{pattern}' 匹配于{field_name}"
                except re.error as e:
                    # 正则表达式格式错误
                    return False, f"正则表达式错误: {e}"
        
        return False, ""
    
    @staticmethod
    def match_any(rules: list[MatchRule], email_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        检查邮件是否匹配任意一个规则(OR逻辑)
        
        输入:
            rules: 规则列表
            email_data: 邮件数据
            
        输出:
            (是否匹配, 第一个匹配的规则描述)
        """
        for rule in rules:
            matched, description = EmailMatcher.match(rule, email_data)
            if matched:
                return True, description
        
        return False, ""


"""自动回复规则数据模型。

定义自动回复规则的数据结构，用于关键词匹配和自动回复。
"""

from dataclasses import dataclass
from typing import List


@dataclass
class AutoReplyRule:
    """自动回复规则数据模型。
    
    Attributes:
        keywords: 触发回复的关键词列表
        reply: 回复内容
    """
    
    keywords: List[str]
    reply: str
    
    def __post_init__(self):
        """验证规则的有效性。"""
        if not self.keywords:
            raise ValueError("关键词列表不能为空")
        if not self.reply:
            raise ValueError("回复内容不能为空")
        
        # 确保关键词列表中没有空字符串
        if any(not keyword.strip() for keyword in self.keywords):
            raise ValueError("关键词不能为空字符串")

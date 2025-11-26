"""会话数据模型。

定义聊天会话的数据结构，用于管理多个聊天会话的状态。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Session:
    """会话数据模型。
    
    Attributes:
        contact_id: 联系人ID（会话的唯一标识）
        contact_name: 联系人名称
        last_message_time: 最后一条消息的时间
        last_activity_time: 最后活跃时间
        message_count: 消息总数
        is_active: 会话是否活跃
    """
    
    contact_id: str
    contact_name: str
    last_message_time: datetime
    last_activity_time: datetime
    message_count: int
    is_active: bool = True
    
    def __post_init__(self):
        """验证数据的有效性。"""
        if self.message_count < 0:
            raise ValueError("消息计数不能为负数")

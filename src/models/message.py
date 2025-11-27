"""消息数据模型。

定义旺旺消息的数据结构，包含消息的所有关键信息。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    """消息数据模型。
    
    Attributes:
        message_id: 消息的唯一标识符
        contact_id: 联系人ID
        contact_name: 联系人名称
        content: 消息内容
        message_type: 消息类型（text/image/system）
        timestamp: 消息时间戳
        is_sent: 是否为发送的消息（True表示发送，False表示接收）
    """
    
    message_id: str
    contact_id: str
    contact_name: str
    content: str
    message_type: str  # "text", "image", "system"
    timestamp: datetime
    is_sent: bool
    
    def __post_init__(self):
        """验证消息类型的有效性。"""
        valid_types = ["text", "image", "system"]
        if self.message_type not in valid_types:
            raise ValueError(f"消息类型必须是 {valid_types} 之一")

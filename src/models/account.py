"""账号数据模型。

定义多账号管理所需的账号数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum


class AccountStatus(Enum):
    """账号状态枚举。"""
    IDLE = "idle"  # 空闲
    STARTING = "starting"  # 启动中
    RUNNING = "running"  # 运行中
    STOPPING = "stopping"  # 停止中
    STOPPED = "stopped"  # 已停止
    ERROR = "error"  # 错误状态


@dataclass
class Account:
    """账号数据模型。
    
    Attributes:
        account_id: 账号唯一标识
        account_name: 账号名称（用于显示）
        cookie_file: Cookie文件路径
        user_data_dir: 浏览器用户数据目录
        cookies: Cookie列表（可选，用于手动配置）
        enabled: 是否启用该账号
        status: 账号当前状态
        process_id: 进程ID（多进程模式下使用）
        last_active_time: 最后活跃时间
        message_count: 处理的消息总数
        error_count: 错误次数
        last_error: 最后一次错误信息
        metadata: 额外的元数据
    """
    
    account_id: str
    account_name: str
    cookie_file: str
    user_data_dir: str
    cookies: Optional[List[Dict]] = None
    enabled: bool = True
    status: AccountStatus = AccountStatus.IDLE
    process_id: Optional[int] = None
    last_active_time: Optional[datetime] = None
    message_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """验证数据的有效性。"""
        if not self.account_id:
            raise ValueError("账号ID不能为空")
        if not self.account_name:
            raise ValueError("账号名称不能为空")
        if not self.user_data_dir:
            raise ValueError("用户数据目录不能为空")
    
    def to_dict(self) -> Dict:
        """转换为字典格式。
        
        Returns:
            账号信息字典
        """
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "cookie_file": self.cookie_file,
            "user_data_dir": self.user_data_dir,
            "enabled": self.enabled,
            "status": self.status.value,
            "process_id": self.process_id,
            "last_active_time": self.last_active_time.isoformat() if self.last_active_time else None,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "metadata": self.metadata
        }

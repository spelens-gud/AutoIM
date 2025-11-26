"""会话管理器。

负责管理多个聊天会话的状态，包括添加、查询、更新和清理会话。
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.models.session import Session
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """会话管理器类。
    
    管理所有活跃的聊天会话，提供会话的增删改查功能。
    
    Attributes:
        _sessions: 存储会话的字典，以contact_id为键
    """
    
    def __init__(self):
        """初始化会话管理器。"""
        self._sessions: Dict[str, Session] = {}
        logger.info("会话管理器初始化完成")
    
    def add_session(self, session: Session) -> None:
        """添加新会话到管理器。
        
        如果会话已存在，则更新现有会话。
        
        Args:
            session: 要添加的会话对象
            
        Examples:
            >>> manager = SessionManager()
            >>> session = Session(
            ...     contact_id="user123",
            ...     contact_name="张三",
            ...     last_message_time=datetime.now(),
            ...     last_activity_time=datetime.now(),
            ...     message_count=1
            ... )
            >>> manager.add_session(session)
        """
        self._sessions[session.contact_id] = session
        logger.info(f"添加会话: {session.contact_name} (ID: {session.contact_id})")
    
    def get_session(self, contact_id: str) -> Optional[Session]:
        """根据联系人ID获取会话。
        
        Args:
            contact_id: 联系人ID
            
        Returns:
            找到的会话对象，如果不存在则返回None
            
        Examples:
            >>> manager = SessionManager()
            >>> session = manager.get_session("user123")
        """
        session = self._sessions.get(contact_id)
        if session:
            logger.debug(f"获取会话: {session.contact_name} (ID: {contact_id})")
        else:
            logger.debug(f"会话不存在: ID={contact_id}")
        return session
    
    def get_active_sessions(self) -> List[Session]:
        """获取所有活跃会话列表。
        
        Returns:
            所有is_active为True的会话列表
            
        Examples:
            >>> manager = SessionManager()
            >>> active_sessions = manager.get_active_sessions()
            >>> print(f"活跃会话数: {len(active_sessions)}")
        """
        active_sessions = [
            session for session in self._sessions.values()
            if session.is_active
        ]
        logger.debug(f"当前活跃会话数: {len(active_sessions)}")
        return active_sessions
    
    def update_session_activity(self, contact_id: str) -> None:
        """更新会话的最后活跃时间。
        
        将指定会话的last_activity_time更新为当前时间，
        并确保会话状态为活跃。
        
        Args:
            contact_id: 联系人ID
            
        Raises:
            ValueError: 如果会话不存在
            
        Examples:
            >>> manager = SessionManager()
            >>> manager.update_session_activity("user123")
        """
        session = self._sessions.get(contact_id)
        if not session:
            error_msg = f"无法更新活跃时间: 会话不存在 (ID: {contact_id})"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        session.last_activity_time = datetime.now()
        session.is_active = True
        logger.debug(f"更新会话活跃时间: {session.contact_name} (ID: {contact_id})")
    
    def cleanup_inactive_sessions(self, timeout: int = 1800) -> int:
        """清理超过指定时间无活动的会话。
        
        将超过timeout秒无活动的会话标记为非活跃状态。
        默认超时时间为1800秒（30分钟）。
        
        Args:
            timeout: 超时时间（秒），默认1800秒（30分钟）
            
        Returns:
            被清理的会话数量
            
        Examples:
            >>> manager = SessionManager()
            >>> cleaned_count = manager.cleanup_inactive_sessions(1800)
            >>> print(f"清理了 {cleaned_count} 个非活跃会话")
        """
        now = datetime.now()
        timeout_delta = timedelta(seconds=timeout)
        cleaned_count = 0
        
        for session in self._sessions.values():
            if session.is_active:
                time_since_activity = now - session.last_activity_time
                if time_since_activity > timeout_delta:
                    session.is_active = False
                    cleaned_count += 1
                    logger.info(
                        f"会话已标记为非活跃: {session.contact_name} "
                        f"(ID: {session.contact_id}), "
                        f"无活动时间: {time_since_activity.total_seconds():.0f}秒"
                    )
        
        if cleaned_count > 0:
            logger.info(f"清理完成，共标记 {cleaned_count} 个会话为非活跃")
        else:
            logger.debug("没有需要清理的非活跃会话")
        
        return cleaned_count
    
    def get_session_count(self) -> int:
        """获取会话总数。
        
        Returns:
            当前管理的会话总数
        """
        return len(self._sessions)
    
    def remove_session(self, contact_id: str) -> bool:
        """从管理器中移除会话。
        
        Args:
            contact_id: 联系人ID
            
        Returns:
            如果成功移除返回True，会话不存在返回False
        """
        if contact_id in self._sessions:
            session = self._sessions.pop(contact_id)
            logger.info(f"移除会话: {session.contact_name} (ID: {contact_id})")
            return True
        else:
            logger.warning(f"尝试移除不存在的会话: ID={contact_id}")
            return False

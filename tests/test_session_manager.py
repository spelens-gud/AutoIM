"""
会话管理器测试模块。

测试SessionManager类的会话管理功能。
"""

from datetime import datetime, timedelta

import pytest

from src.core.session_manager import SessionManager
from src.models.session import Session


class TestSessionManager:
    """测试SessionManager类的所有功能。"""
    
    def test_add_session(self):
        """测试添加新会话。"""
        manager = SessionManager()
        session = Session(
            contact_id="user123",
            contact_name="张三",
            last_message_time=datetime.now(),
            last_activity_time=datetime.now(),
            message_count=1
        )
        
        manager.add_session(session)
        
        # 验证会话已添加
        assert manager.get_session_count() == 1
        retrieved_session = manager.get_session("user123")
        assert retrieved_session is not None
        assert retrieved_session.contact_name == "张三"
    
    def test_add_session_updates_existing(self):
        """测试添加已存在的会话会更新现有会话。"""
        manager = SessionManager()
        
        # 添加第一个会话
        session1 = Session(
            contact_id="user123",
            contact_name="张三",
            last_message_time=datetime.now(),
            last_activity_time=datetime.now(),
            message_count=1
        )
        manager.add_session(session1)
        
        # 添加相同ID的会话（更新）
        session2 = Session(
            contact_id="user123",
            contact_name="张三（更新）",
            last_message_time=datetime.now(),
            last_activity_time=datetime.now(),
            message_count=5
        )
        manager.add_session(session2)
        
        # 验证会话已更新
        assert manager.get_session_count() == 1
        retrieved_session = manager.get_session("user123")
        assert retrieved_session.contact_name == "张三（更新）"
        assert retrieved_session.message_count == 5
    
    def test_get_session_exists(self):
        """测试获取存在的会话。"""
        manager = SessionManager()
        session = Session(
            contact_id="user456",
            contact_name="李四",
            last_message_time=datetime.now(),
            last_activity_time=datetime.now(),
            message_count=3
        )
        manager.add_session(session)
        
        # 获取会话
        retrieved_session = manager.get_session("user456")
        
        assert retrieved_session is not None
        assert retrieved_session.contact_id == "user456"
        assert retrieved_session.contact_name == "李四"
        assert retrieved_session.message_count == 3
    
    def test_get_session_not_exists(self):
        """测试获取不存在的会话。"""
        manager = SessionManager()
        
        # 获取不存在的会话
        retrieved_session = manager.get_session("nonexistent")
        
        assert retrieved_session is None
    
    def test_get_active_sessions(self):
        """测试获取所有活跃会话。"""
        manager = SessionManager()
        
        # 添加多个会话
        session1 = Session(
            contact_id="user1",
            contact_name="用户1",
            last_message_time=datetime.now(),
            last_activity_time=datetime.now(),
            message_count=1,
            is_active=True
        )
        session2 = Session(
            contact_id="user2",
            contact_name="用户2",
            last_message_time=datetime.now(),
            last_activity_time=datetime.now(),
            message_count=2,
            is_active=True
        )
        session3 = Session(
            contact_id="user3",
            contact_name="用户3",
            last_message_time=datetime.now(),
            last_activity_time=datetime.now(),
            message_count=3,
            is_active=False
        )
        
        manager.add_session(session1)
        manager.add_session(session2)
        manager.add_session(session3)
        
        # 获取活跃会话
        active_sessions = manager.get_active_sessions()
        
        assert len(active_sessions) == 2
        assert all(session.is_active for session in active_sessions)
        contact_ids = [s.contact_id for s in active_sessions]
        assert "user1" in contact_ids
        assert "user2" in contact_ids
        assert "user3" not in contact_ids
    
    def test_get_active_sessions_empty(self):
        """测试获取活跃会话（无活跃会话）。"""
        manager = SessionManager()
        
        # 获取活跃会话（空列表）
        active_sessions = manager.get_active_sessions()
        
        assert len(active_sessions) == 0
        assert isinstance(active_sessions, list)
    
    def test_update_session_activity(self):
        """测试更新会话活跃时间。"""
        manager = SessionManager()
        
        # 添加会话
        old_time = datetime.now() - timedelta(minutes=10)
        session = Session(
            contact_id="user789",
            contact_name="王五",
            last_message_time=old_time,
            last_activity_time=old_time,
            message_count=1
        )
        manager.add_session(session)
        
        # 更新活跃时间
        manager.update_session_activity("user789")
        
        # 验证活跃时间已更新
        updated_session = manager.get_session("user789")
        assert updated_session.last_activity_time > old_time
        assert updated_session.is_active is True
    
    def test_update_session_activity_not_exists(self):
        """测试更新不存在的会话活跃时间。"""
        manager = SessionManager()
        
        # 尝试更新不存在的会话
        with pytest.raises(ValueError, match="会话不存在"):
            manager.update_session_activity("nonexistent")
    
    def test_cleanup_inactive_sessions(self):
        """测试清理非活跃会话。"""
        manager = SessionManager()
        
        # 添加活跃会话
        active_session = Session(
            contact_id="active_user",
            contact_name="活跃用户",
            last_message_time=datetime.now(),
            last_activity_time=datetime.now(),
            message_count=1,
            is_active=True
        )
        
        # 添加超时会话
        inactive_time = datetime.now() - timedelta(minutes=35)
        inactive_session = Session(
            contact_id="inactive_user",
            contact_name="非活跃用户",
            last_message_time=inactive_time,
            last_activity_time=inactive_time,
            message_count=1,
            is_active=True
        )
        
        manager.add_session(active_session)
        manager.add_session(inactive_session)
        
        # 清理非活跃会话（30分钟超时）
        cleaned_count = manager.cleanup_inactive_sessions(timeout=1800)
        
        # 验证清理结果
        assert cleaned_count == 1
        
        # 验证活跃会话仍然活跃
        active = manager.get_session("active_user")
        assert active.is_active is True
        
        # 验证非活跃会话已标记为非活跃
        inactive = manager.get_session("inactive_user")
        assert inactive.is_active is False
    
    def test_cleanup_inactive_sessions_custom_timeout(self):
        """测试使用自定义超时时间清理会话。"""
        manager = SessionManager()
        
        # 添加5分钟前活跃的会话
        old_time = datetime.now() - timedelta(minutes=5)
        session = Session(
            contact_id="user_custom",
            contact_name="自定义超时用户",
            last_message_time=old_time,
            last_activity_time=old_time,
            message_count=1,
            is_active=True
        )
        manager.add_session(session)
        
        # 使用3分钟超时清理
        cleaned_count = manager.cleanup_inactive_sessions(timeout=180)
        
        # 验证会话已被清理
        assert cleaned_count == 1
        retrieved_session = manager.get_session("user_custom")
        assert retrieved_session.is_active is False
    
    def test_cleanup_inactive_sessions_no_cleanup_needed(self):
        """测试清理会话（无需清理）。"""
        manager = SessionManager()
        
        # 添加活跃会话
        session = Session(
            contact_id="recent_user",
            contact_name="最近活跃用户",
            last_message_time=datetime.now(),
            last_activity_time=datetime.now(),
            message_count=1,
            is_active=True
        )
        manager.add_session(session)
        
        # 清理非活跃会话
        cleaned_count = manager.cleanup_inactive_sessions(timeout=1800)
        
        # 验证没有会话被清理
        assert cleaned_count == 0
        retrieved_session = manager.get_session("recent_user")
        assert retrieved_session.is_active is True
    
    def test_get_session_count(self):
        """测试获取会话总数。"""
        manager = SessionManager()
        
        # 初始为0
        assert manager.get_session_count() == 0
        
        # 添加会话
        for i in range(5):
            session = Session(
                contact_id=f"user{i}",
                contact_name=f"用户{i}",
                last_message_time=datetime.now(),
                last_activity_time=datetime.now(),
                message_count=1
            )
            manager.add_session(session)
        
        # 验证数量
        assert manager.get_session_count() == 5
    
    def test_remove_session(self):
        """测试移除会话。"""
        manager = SessionManager()
        
        # 添加会话
        session = Session(
            contact_id="user_remove",
            contact_name="待移除用户",
            last_message_time=datetime.now(),
            last_activity_time=datetime.now(),
            message_count=1
        )
        manager.add_session(session)
        
        # 移除会话
        result = manager.remove_session("user_remove")
        
        # 验证移除成功
        assert result is True
        assert manager.get_session_count() == 0
        assert manager.get_session("user_remove") is None
    
    def test_remove_session_not_exists(self):
        """测试移除不存在的会话。"""
        manager = SessionManager()
        
        # 尝试移除不存在的会话
        result = manager.remove_session("nonexistent")
        
        # 验证返回False
        assert result is False

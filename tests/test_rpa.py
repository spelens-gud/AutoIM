"""RPA主控制器测试。

测试WangWangRPA类的核心功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.rpa import WangWangRPA
from src.models.message import Message
from src.models.session import Session
from src.utils.exceptions import WangWangRPAException


class TestWangWangRPAInit:
    """测试WangWangRPA初始化。"""
    
    @patch('src.rpa.ConfigManager')
    @patch('src.rpa.BrowserController')
    @patch('src.rpa.MessageHandler')
    @patch('src.rpa.SessionManager')
    @patch('src.rpa.AutoReplyEngine')
    @patch('src.rpa.signal.signal')
    def test_init_success(
        self, 
        mock_signal,
        mock_auto_reply,
        mock_session_manager,
        mock_message_handler,
        mock_browser,
        mock_config_manager
    ):
        """测试成功初始化RPA系统。"""
        # 模拟配置
        mock_config = Mock()
        mock_config.browser_headless = False
        mock_config.browser_user_data_dir = "./browser_data"
        mock_config.auto_reply_enabled = True
        mock_config.auto_reply_rules_file = "config/auto_reply_rules.yaml"
        
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_manager.return_value = mock_config_instance
        
        # 模拟自动回复引擎
        mock_engine = Mock()
        mock_engine.get_rules_count.return_value = 5
        mock_auto_reply.return_value = mock_engine
        
        # 初始化RPA
        rpa = WangWangRPA()
        
        assert rpa.config == mock_config
        assert rpa.browser is not None
        assert rpa.message_handler is not None
        assert rpa.session_manager is not None
        assert rpa.auto_reply_engine is not None
        assert rpa.is_running is False
    
    @patch('src.rpa.ConfigManager')
    def test_init_config_failure(self, mock_config_manager):
        """测试配置加载失败时的初始化。"""
        mock_config_manager.return_value.load_config.side_effect = Exception("配置加载失败")
        
        with pytest.raises(WangWangRPAException, match="RPA系统初始化失败"):
            WangWangRPA()


class TestWangWangRPAStart:
    """测试RPA系统启动功能。"""
    
    @patch('src.rpa.ConfigManager')
    @patch('src.rpa.BrowserController')
    @patch('src.rpa.MessageHandler')
    @patch('src.rpa.SessionManager')
    @patch('src.rpa.signal.signal')
    def test_start_success_already_logged_in(
        self,
        mock_signal,
        mock_session_manager,
        mock_message_handler,
        mock_browser_class,
        mock_config_manager
    ):
        """测试已登录状态下成功启动。"""
        # 模拟配置
        mock_config = Mock()
        mock_config.browser_headless = False
        mock_config.browser_user_data_dir = "./browser_data"
        mock_config.wangwang_url = "https://wangwang.taobao.com"
        mock_config.auto_reply_enabled = False
        
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_manager.return_value = mock_config_instance
        
        # 模拟浏览器
        mock_browser = Mock()
        mock_browser.is_logged_in.return_value = True
        mock_browser_class.return_value = mock_browser
        
        # 初始化并启动
        rpa = WangWangRPA()
        rpa.start()
        
        mock_browser.start.assert_called_once()
        mock_browser.navigate_to.assert_called_once_with(mock_config.wangwang_url)
        mock_browser.is_logged_in.assert_called_once()


class TestWangWangRPAProcessMessage:
    """测试消息处理功能。"""
    
    @patch('src.rpa.ConfigManager')
    @patch('src.rpa.BrowserController')
    @patch('src.rpa.MessageHandler')
    @patch('src.rpa.SessionManager')
    @patch('src.rpa.AutoReplyEngine')
    @patch('src.rpa.signal.signal')
    def test_process_message_with_auto_reply(
        self,
        mock_signal,
        mock_auto_reply_class,
        mock_session_manager_class,
        mock_message_handler_class,
        mock_browser,
        mock_config_manager
    ):
        """测试处理消息并自动回复。"""
        # 模拟配置
        mock_config = Mock()
        mock_config.browser_headless = False
        mock_config.browser_user_data_dir = "./browser_data"
        mock_config.auto_reply_enabled = True
        mock_config.auto_reply_rules_file = "config/auto_reply_rules.yaml"
        mock_config.retry_times = 2
        mock_config.retry_delay = 1
        
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_manager.return_value = mock_config_instance
        
        # 模拟自动回复引擎
        mock_engine = Mock()
        mock_engine.match_rule.return_value = "这是自动回复"
        mock_engine.get_rules_count.return_value = 5
        mock_auto_reply_class.return_value = mock_engine
        
        # 模拟消息处理器
        mock_handler = Mock()
        mock_handler.send_message.return_value = True
        mock_message_handler_class.return_value = mock_handler
        
        # 模拟会话管理器
        mock_session_manager = Mock()
        mock_session_manager.get_session.return_value = None
        mock_session_manager_class.return_value = mock_session_manager
        
        # 创建测试消息
        message = Message(
            message_id="msg123",
            contact_id="user123",
            contact_name="测试用户",
            content="你好，请问价格是多少？",
            message_type="text",
            timestamp=datetime.now(),
            is_sent=False,
            is_auto_reply=False
        )
        
        # 初始化RPA并处理消息
        rpa = WangWangRPA()
        rpa._process_message(message)
        
        # 验证自动回复被调用
        mock_engine.match_rule.assert_called_once_with(message.content)
        mock_handler.send_message.assert_called_once()
    
    @patch('src.rpa.ConfigManager')
    @patch('src.rpa.BrowserController')
    @patch('src.rpa.MessageHandler')
    @patch('src.rpa.SessionManager')
    @patch('src.rpa.signal.signal')
    def test_process_message_skip_sent_message(
        self,
        mock_signal,
        mock_session_manager_class,
        mock_message_handler,
        mock_browser,
        mock_config_manager
    ):
        """测试跳过自己发送的消息。"""
        # 模拟配置
        mock_config = Mock()
        mock_config.browser_headless = False
        mock_config.browser_user_data_dir = "./browser_data"
        mock_config.auto_reply_enabled = False
        
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_manager.return_value = mock_config_instance
        
        # 创建已发送的消息
        message = Message(
            message_id="msg123",
            contact_id="user123",
            contact_name="测试用户",
            content="这是我发送的消息",
            message_type="text",
            timestamp=datetime.now(),
            is_sent=True,  # 标记为已发送
            is_auto_reply=False
        )
        
        # 初始化RPA并处理消息
        rpa = WangWangRPA()
        mock_session_manager = Mock()
        rpa.session_manager = mock_session_manager
        
        rpa._process_message(message)
        
        # 验证会话管理器未被调用（消息被跳过）
        mock_session_manager.get_session.assert_not_called()


class TestWangWangRPAStop:
    """测试RPA系统停止功能。"""
    
    @patch('src.rpa.ConfigManager')
    @patch('src.rpa.BrowserController')
    @patch('src.rpa.MessageHandler')
    @patch('src.rpa.SessionManager')
    @patch('src.rpa.signal.signal')
    def test_stop_success(
        self,
        mock_signal,
        mock_session_manager_class,
        mock_message_handler,
        mock_browser_class,
        mock_config_manager
    ):
        """测试成功停止RPA系统。"""
        # 模拟配置
        mock_config = Mock()
        mock_config.browser_headless = False
        mock_config.browser_user_data_dir = "./browser_data"
        mock_config.auto_reply_enabled = False
        
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_manager.return_value = mock_config_instance
        
        # 模拟浏览器
        mock_browser = Mock()
        mock_browser_class.return_value = mock_browser
        
        # 模拟会话管理器
        mock_session_manager = Mock()
        mock_session_manager.get_session_count.return_value = 5
        mock_session_manager.get_active_sessions.return_value = [Mock(), Mock()]
        mock_session_manager_class.return_value = mock_session_manager
        
        # 初始化并停止
        rpa = WangWangRPA()
        rpa.is_running = True
        rpa.stop()
        
        assert rpa.is_running is False
        mock_browser.stop.assert_called_once()


class TestWangWangRPAGetStatus:
    """测试获取系统状态功能。"""
    
    @patch('src.rpa.ConfigManager')
    @patch('src.rpa.BrowserController')
    @patch('src.rpa.MessageHandler')
    @patch('src.rpa.SessionManager')
    @patch('src.rpa.AutoReplyEngine')
    @patch('src.rpa.signal.signal')
    def test_get_status(
        self,
        mock_signal,
        mock_auto_reply_class,
        mock_session_manager_class,
        mock_message_handler,
        mock_browser,
        mock_config_manager
    ):
        """测试获取系统状态。"""
        # 模拟配置
        mock_config = Mock()
        mock_config.browser_headless = False
        mock_config.browser_user_data_dir = "./browser_data"
        mock_config.auto_reply_enabled = True
        mock_config.auto_reply_rules_file = "config/auto_reply_rules.yaml"
        
        mock_config_instance = Mock()
        mock_config_instance.load_config.return_value = mock_config
        mock_config_manager.return_value = mock_config_instance
        
        # 模拟会话管理器
        mock_session_manager = Mock()
        mock_session_manager.get_session_count.return_value = 10
        mock_session_manager.get_active_sessions.return_value = [Mock()] * 5
        mock_session_manager_class.return_value = mock_session_manager
        
        # 模拟自动回复引擎
        mock_engine = Mock()
        mock_engine.get_rules_count.return_value = 8
        mock_auto_reply_class.return_value = mock_engine
        
        # 初始化并获取状态
        rpa = WangWangRPA()
        rpa.is_running = True
        
        status = rpa.get_status()
        
        assert status["is_running"] is True
        assert status["auto_reply_enabled"] is True
        assert status["total_sessions"] == 10
        assert status["active_sessions"] == 5
        assert status["auto_reply_rules"] == 8

"""消息处理器测试。

测试MessageHandler类的核心功能。
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.core.message_handler import MessageHandler
from src.core.browser_controller import BrowserController
from src.models.message import Message
from src.utils.exceptions import MessageException


class TestMessageHandlerInit:
    """测试MessageHandler初始化。"""
    
    def test_init_success(self):
        """测试成功初始化消息处理器。"""
        mock_browser = Mock(spec=BrowserController)
        handler = MessageHandler(mock_browser)
        
        assert handler.browser == mock_browser
        assert isinstance(handler.processed_message_ids, set)
        assert len(handler.processed_message_ids) == 0


class TestMessageHandlerGetMessageList:
    """测试获取消息列表功能。"""
    
    def test_get_message_list_success(self):
        """测试成功获取消息列表。"""
        mock_browser = Mock(spec=BrowserController)
        mock_elements = [Mock(), Mock(), Mock()]
        mock_browser.find_elements.return_value = mock_elements
        
        handler = MessageHandler(mock_browser)
        result = handler.get_message_list()
        
        assert len(result) == 3
        assert result == mock_elements
    
    def test_get_message_list_empty(self):
        """测试获取空消息列表。"""
        mock_browser = Mock(spec=BrowserController)
        mock_browser.find_elements.return_value = []
        
        handler = MessageHandler(mock_browser)
        result = handler.get_message_list()
        
        assert result == []
    
    def test_get_message_list_tries_multiple_selectors(self):
        """测试尝试多个选择器获取消息列表。"""
        mock_browser = Mock(spec=BrowserController)
        # 第一个选择器返回空，第二个返回元素
        mock_browser.find_elements.side_effect = [[], [Mock(), Mock()]]
        
        handler = MessageHandler(mock_browser)
        result = handler.get_message_list()
        
        assert len(result) == 2


class TestMessageHandlerParseMessageElement:
    """测试消息元素解析功能。"""
    
    def test_parse_message_element_basic(self):
        """测试解析基本消息元素。"""
        mock_browser = Mock(spec=BrowserController)
        handler = MessageHandler(mock_browser)
        
        # 创建模拟的消息元素
        mock_element = Mock()
        mock_element.get_attribute.side_effect = lambda attr: {
            "data-message-id": "msg123",
            "class": "message-item received"
        }.get(attr, "")
        mock_element.text = "测试消息内容"
        
        # 模拟内容元素
        mock_content = Mock()
        mock_content.text = "测试消息内容"
        
        # 模拟发送者元素
        mock_sender = Mock()
        mock_sender.text = "测试用户"
        mock_sender.get_attribute.return_value = "user123"
        
        mock_element.find_element.side_effect = lambda by, selector: {
            ".message-content": mock_content,
            ".sender-name": mock_sender,
        }.get(selector, Mock())
        
        mock_element.find_elements.return_value = []
        
        result = handler.parse_message_element(mock_element)
        
        assert isinstance(result, Message)
        assert result.message_id == "msg123"
        assert result.content == "测试消息内容"
        assert result.is_sent is False


class TestMessageHandlerCheckNewMessages:
    """测试检查新消息功能。"""
    
    def test_check_new_messages_with_new_messages(self):
        """测试检查到新消息。"""
        mock_browser = Mock(spec=BrowserController)
        handler = MessageHandler(mock_browser)
        
        # 模拟消息元素
        mock_element = Mock()
        mock_element.get_attribute.side_effect = lambda attr: {
            "data-message-id": "msg123",
            "class": "message-item",
            "id": "msg123"
        }.get(attr, "")
        mock_element.text = "测试消息"
        
        # 模拟内容元素
        mock_content = Mock()
        mock_content.text = "测试消息"
        
        # 设置find_element返回内容元素
        mock_element.find_element.return_value = mock_content
        mock_element.find_elements.return_value = []
        
        mock_browser.find_elements.return_value = [mock_element]
        
        result = handler.check_new_messages()
        
        assert len(result) == 1
        assert isinstance(result[0], Message)
        assert "msg123" in handler.processed_message_ids
    
    def test_check_new_messages_no_duplicates(self):
        """测试消息去重功能。"""
        mock_browser = Mock(spec=BrowserController)
        handler = MessageHandler(mock_browser)
        
        # 模拟相同的消息元素
        mock_element = Mock()
        mock_element.get_attribute.side_effect = lambda attr: {
            "data-message-id": "msg123",
            "class": "message-item",
            "id": "msg123"
        }.get(attr, "")
        mock_element.text = "测试消息"
        
        # 模拟内容元素
        mock_content = Mock()
        mock_content.text = "测试消息"
        
        mock_element.find_element.return_value = mock_content
        mock_element.find_elements.return_value = []
        
        mock_browser.find_elements.return_value = [mock_element]
        
        # 第一次检查
        result1 = handler.check_new_messages()
        assert len(result1) == 1
        
        # 第二次检查相同消息
        result2 = handler.check_new_messages()
        assert len(result2) == 0  # 应该被去重
    
    def test_check_new_messages_empty(self):
        """测试没有新消息的情况。"""
        mock_browser = Mock(spec=BrowserController)
        mock_browser.find_elements.return_value = []
        
        handler = MessageHandler(mock_browser)
        result = handler.check_new_messages()
        
        assert result == []


class TestMessageHandlerSwitchToChat:
    """测试切换聊天窗口功能。"""
    
    def test_switch_to_chat_success(self):
        """测试成功切换到聊天窗口。"""
        mock_browser = Mock(spec=BrowserController)
        mock_contact_element = Mock()
        mock_browser.wait_for_element.return_value = mock_contact_element
        
        handler = MessageHandler(mock_browser)
        result = handler.switch_to_chat("user123")
        
        assert result is True
        mock_contact_element.click.assert_called_once()
    
    def test_switch_to_chat_not_found(self):
        """测试联系人未找到的情况。"""
        mock_browser = Mock(spec=BrowserController)
        mock_browser.wait_for_element.side_effect = Exception("未找到")
        
        handler = MessageHandler(mock_browser)
        result = handler.switch_to_chat("user123")
        
        assert result is False


class TestMessageHandlerSendMessage:
    """测试发送消息功能。"""
    
    def test_send_message_success(self):
        """测试成功发送消息。"""
        mock_browser = Mock(spec=BrowserController)
        
        # 模拟输入框
        mock_input = Mock()
        mock_input.is_displayed.return_value = True
        
        # 模拟发送按钮
        mock_send_button = Mock()
        mock_send_button.is_displayed.return_value = True
        
        mock_browser.wait_for_element.return_value = mock_input
        mock_browser.find_element.return_value = mock_send_button
        
        handler = MessageHandler(mock_browser)
        handler.switch_to_chat = Mock(return_value=True)
        
        result = handler.send_message("user123", "测试消息")
        
        assert result is True
        mock_input.clear.assert_called_once()
        mock_input.send_keys.assert_called()
        mock_send_button.click.assert_called_once()
    
    def test_send_message_with_retry(self):
        """测试发送消息失败后重试。"""
        mock_browser = Mock(spec=BrowserController)
        
        # 第一次失败，第二次成功
        mock_input = Mock()
        mock_send_button = Mock()
        mock_send_button.is_displayed.return_value = True
        
        call_count = [0]
        
        def wait_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("第一次失败")
            return mock_input
        
        mock_browser.wait_for_element.side_effect = wait_side_effect
        mock_browser.find_element.return_value = mock_send_button
        
        handler = MessageHandler(mock_browser)
        handler.switch_to_chat = Mock(return_value=True)
        
        result = handler.send_message("user123", "测试消息", retry_times=2)
        
        assert result is True
    
    def test_send_message_failure_after_retries(self):
        """测试重试次数用尽后发送失败。"""
        mock_browser = Mock(spec=BrowserController)
        mock_browser.wait_for_element.side_effect = Exception("输入框未找到")
        
        handler = MessageHandler(mock_browser)
        handler.switch_to_chat = Mock(return_value=True)
        
        with pytest.raises(MessageException, match="发送消息失败"):
            handler.send_message("user123", "测试消息", retry_times=1)
    
    def test_send_message_without_send_button(self):
        """测试没有发送按钮时使用回车键发送。"""
        mock_browser = Mock(spec=BrowserController)
        
        mock_input = Mock()
        mock_browser.wait_for_element.return_value = mock_input
        mock_browser.find_element.side_effect = Exception("未找到发送按钮")
        
        handler = MessageHandler(mock_browser)
        handler.switch_to_chat = Mock(return_value=True)
        
        result = handler.send_message("user123", "测试消息")
        
        assert result is True
        mock_input.send_keys.assert_called()

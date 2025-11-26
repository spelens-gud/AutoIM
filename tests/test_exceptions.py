"""
测试自定义异常类。
"""

import pytest
from src.utils.exceptions import (
    WangWangRPAException,
    BrowserException,
    MessageException,
    ConfigException,
)


class TestWangWangRPAException:
    """测试基础异常类。"""

    def test_exception_message(self):
        """测试异常消息是否正确设置。"""
        message = "测试异常消息"
        exception = WangWangRPAException(message)
        assert exception.message == message
        assert str(exception) == message

    def test_exception_inheritance(self):
        """测试异常继承关系。"""
        exception = WangWangRPAException("测试")
        assert isinstance(exception, Exception)


class TestBrowserException:
    """测试浏览器异常类。"""

    def test_browser_exception_creation(self):
        """测试浏览器异常创建。"""
        message = "浏览器启动失败"
        exception = BrowserException(message)
        assert exception.message == message
        assert isinstance(exception, WangWangRPAException)

    def test_browser_exception_raise(self):
        """测试浏览器异常抛出。"""
        with pytest.raises(BrowserException, match="浏览器错误"):
            raise BrowserException("浏览器错误")


class TestMessageException:
    """测试消息异常类。"""

    def test_message_exception_creation(self):
        """测试消息异常创建。"""
        message = "消息发送失败"
        exception = MessageException(message)
        assert exception.message == message
        assert isinstance(exception, WangWangRPAException)

    def test_message_exception_raise(self):
        """测试消息异常抛出。"""
        with pytest.raises(MessageException, match="消息错误"):
            raise MessageException("消息错误")


class TestConfigException:
    """测试配置异常类。"""

    def test_config_exception_creation(self):
        """测试配置异常创建。"""
        message = "配置文件格式错误"
        exception = ConfigException(message)
        assert exception.message == message
        assert isinstance(exception, WangWangRPAException)

    def test_config_exception_raise(self):
        """测试配置异常抛出。"""
        with pytest.raises(ConfigException, match="配置错误"):
            raise ConfigException("配置错误")

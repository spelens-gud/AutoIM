"""浏览器控制器测试。

测试BrowserController类的核心功能。
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.core.browser_controller import BrowserController
from src.utils.exceptions import BrowserException


class TestBrowserControllerInit:
    """测试BrowserController初始化。"""
    
    def test_init_default_params(self):
        """测试使用默认参数初始化。"""
        controller = BrowserController()
        
        assert controller.headless is False
        assert controller.user_data_dir is None
        assert controller.driver is None
    
    def test_init_with_headless(self):
        """测试使用无头模式初始化。"""
        controller = BrowserController(headless=True)
        
        assert controller.headless is True
    
    def test_init_with_user_data_dir(self):
        """测试使用用户数据目录初始化。"""
        data_dir = "./test_browser_data"
        controller = BrowserController(user_data_dir=data_dir)
        
        assert controller.user_data_dir == data_dir


class TestBrowserControllerStart:
    """测试浏览器启动功能。"""
    
    @patch('src.core.browser_controller.webdriver.Chrome')
    def test_start_success(self, mock_chrome):
        """测试成功启动浏览器。"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        controller = BrowserController()
        controller.start()
        
        assert controller.driver is not None
        mock_chrome.assert_called_once()
        mock_driver.maximize_window.assert_called_once()
    
    @patch('src.core.browser_controller.webdriver.Chrome')
    def test_start_with_headless(self, mock_chrome):
        """测试使用无头模式启动浏览器。"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        controller = BrowserController(headless=True)
        controller.start()
        
        assert controller.driver is not None
        # 验证Chrome被调用时传入了options参数
        mock_chrome.assert_called_once()
    
    @patch('src.core.browser_controller.webdriver.Chrome')
    def test_start_failure(self, mock_chrome):
        """测试浏览器启动失败。"""
        mock_chrome.side_effect = Exception("启动失败")
        
        controller = BrowserController()
        
        with pytest.raises(BrowserException, match="浏览器启动时发生未知错误"):
            controller.start()


class TestBrowserControllerStop:
    """测试浏览器关闭功能。"""
    
    def test_stop_with_running_browser(self):
        """测试关闭正在运行的浏览器。"""
        controller = BrowserController()
        mock_driver = Mock()
        controller.driver = mock_driver
        
        controller.stop()
        
        mock_driver.quit.assert_called_once()
        assert controller.driver is None
    
    def test_stop_without_browser(self):
        """测试关闭未启动的浏览器。"""
        controller = BrowserController()
        
        # 不应该抛出异常
        controller.stop()
        
        assert controller.driver is None


class TestBrowserControllerNavigate:
    """测试浏览器导航功能。"""
    
    def test_navigate_success(self):
        """测试成功导航到URL。"""
        controller = BrowserController()
        mock_driver = Mock()
        controller.driver = mock_driver
        
        url = "https://example.com"
        controller.navigate_to(url)
        
        mock_driver.get.assert_called_once_with(url)
    
    def test_navigate_without_browser(self):
        """测试在浏览器未启动时导航。"""
        controller = BrowserController()
        
        with pytest.raises(BrowserException, match="浏览器未启动"):
            controller.navigate_to("https://example.com")
    
    def test_navigate_failure(self):
        """测试导航失败。"""
        controller = BrowserController()
        mock_driver = Mock()
        mock_driver.get.side_effect = Exception("导航失败")
        controller.driver = mock_driver
        
        with pytest.raises(BrowserException, match="导航到.*失败"):
            controller.navigate_to("https://example.com")


class TestBrowserControllerFindElement:
    """测试元素查找功能。"""
    
    def test_find_element_by_css(self):
        """测试使用CSS选择器查找元素。"""
        controller = BrowserController()
        mock_driver = Mock()
        mock_element = Mock()
        mock_driver.find_element.return_value = mock_element
        controller.driver = mock_driver
        
        result = controller.find_element(".test-class")
        
        assert result == mock_element
        mock_driver.find_element.assert_called_once()
    
    def test_find_element_by_xpath(self):
        """测试使用XPath查找元素。"""
        controller = BrowserController()
        mock_driver = Mock()
        mock_element = Mock()
        mock_driver.find_element.return_value = mock_element
        controller.driver = mock_driver
        
        result = controller.find_element("//div[@class='test']", by="xpath")
        
        assert result == mock_element
        mock_driver.find_element.assert_called_once()
    
    def test_find_element_without_browser(self):
        """测试在浏览器未启动时查找元素。"""
        controller = BrowserController()
        
        with pytest.raises(BrowserException, match="浏览器未启动"):
            controller.find_element(".test")


class TestBrowserControllerFindElements:
    """测试多元素查找功能。"""
    
    def test_find_elements_success(self):
        """测试成功查找多个元素。"""
        controller = BrowserController()
        mock_driver = Mock()
        mock_elements = [Mock(), Mock(), Mock()]
        mock_driver.find_elements.return_value = mock_elements
        controller.driver = mock_driver
        
        result = controller.find_elements(".test-class")
        
        assert len(result) == 3
        assert result == mock_elements
    
    def test_find_elements_empty(self):
        """测试查找不存在的元素返回空列表。"""
        controller = BrowserController()
        mock_driver = Mock()
        mock_driver.find_elements.return_value = []
        controller.driver = mock_driver
        
        result = controller.find_elements(".not-exist")
        
        assert result == []


class TestBrowserControllerCookies:
    """测试Cookie管理功能。"""
    
    def test_save_cookies(self, tmp_path):
        """测试保存Cookie。"""
        controller = BrowserController()
        mock_driver = Mock()
        mock_cookies = [
            {"name": "session", "value": "abc123"},
            {"name": "token", "value": "xyz789"}
        ]
        mock_driver.get_cookies.return_value = mock_cookies
        controller.driver = mock_driver
        
        cookie_file = tmp_path / "cookies.pkl"
        controller.save_cookies(str(cookie_file))
        
        assert cookie_file.exists()
    
    def test_save_cookies_without_browser(self):
        """测试在浏览器未启动时保存Cookie。"""
        controller = BrowserController()
        
        with pytest.raises(BrowserException, match="浏览器未启动"):
            controller.save_cookies("cookies.pkl")
    
    def test_load_cookies_file_not_exist(self):
        """测试加载不存在的Cookie文件。"""
        controller = BrowserController()
        mock_driver = Mock()
        controller.driver = mock_driver
        
        # 不应该抛出异常，只是记录警告
        controller.load_cookies("not_exist.pkl")
    
    def test_load_cookies_without_browser(self):
        """测试在浏览器未启动时加载Cookie。"""
        controller = BrowserController()
        
        with pytest.raises(BrowserException, match="浏览器未启动"):
            controller.load_cookies("cookies.pkl")


class TestBrowserControllerIsLoggedIn:
    """测试登录状态检查功能。"""
    
    def test_is_logged_in_with_auth_cookie(self):
        """测试存在认证Cookie时返回已登录。"""
        controller = BrowserController()
        mock_driver = Mock()
        mock_driver.get_cookies.return_value = [
            {"name": "token", "value": "abc123"}
        ]
        controller.driver = mock_driver
        
        result = controller.is_logged_in()
        
        assert result is True
    
    def test_is_logged_in_on_login_page(self):
        """测试在登录页面时返回未登录。"""
        controller = BrowserController()
        mock_driver = Mock()
        mock_driver.get_cookies.return_value = []
        mock_driver.current_url = "https://example.com/login"
        controller.driver = mock_driver
        
        result = controller.is_logged_in()
        
        assert result is False
    
    def test_is_logged_in_without_browser(self):
        """测试在浏览器未启动时检查登录状态。"""
        controller = BrowserController()
        
        with pytest.raises(BrowserException, match="浏览器未启动"):
            controller.is_logged_in()

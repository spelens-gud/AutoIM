"""浏览器控制器模块。

提供浏览器自动化控制功能，包括启动、关闭、导航、元素定位等操作。
"""

import json
import pickle
from pathlib import Path
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

from src.utils.exceptions import BrowserException
from src.utils.logger import get_logger


logger = get_logger(__name__)


class BrowserController:
    """浏览器控制器类。
    
    负责管理浏览器的生命周期和提供网页操作接口。
    
    Attributes:
        headless: 是否使用无头模式
        user_data_dir: 浏览器用户数据目录
        driver: Selenium WebDriver实例
    """
    
    def __init__(self, headless: bool = False, user_data_dir: Optional[str] = None):
        """初始化浏览器控制器。
        
        Args:
            headless: 是否使用无头模式，默认False
            user_data_dir: 浏览器用户数据目录路径，用于保存浏览器状态
        """
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.driver: Optional[webdriver.Chrome] = None
        
        logger.info(f"初始化浏览器控制器 - 无头模式: {headless}, 数据目录: {user_data_dir}")
    
    def start(self) -> None:
        """启动Chrome浏览器。
        
        根据配置启动浏览器，支持有头和无头模式。
        
        Raises:
            BrowserException: 当浏览器启动失败时抛出
        """
        try:
            logger.info("正在启动Chrome浏览器...")
            
            # 配置Chrome选项
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                logger.info("使用无头模式启动浏览器")
            
            # 其他常用选项
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # 设置窗口大小
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")
            
            # 启动浏览器
            # 尝试使用 webdriver-manager 自动管理驱动
            if WEBDRIVER_MANAGER_AVAILABLE:
                logger.info("使用 webdriver-manager 自动管理 ChromeDriver")
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                logger.info("使用 Selenium 内置驱动管理")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.maximize_window()
            
            logger.info("浏览器启动成功")
            
        except WebDriverException as e:
            error_msg = f"浏览器启动失败: {str(e)}"
            logger.error(error_msg)
            raise BrowserException(error_msg) from e
        except Exception as e:
            error_msg = f"浏览器启动时发生未知错误: {str(e)}"
            logger.error(error_msg)
            raise BrowserException(error_msg) from e
    
    def stop(self) -> None:
        """关闭浏览器并清理资源。
        
        安全地关闭浏览器实例并释放相关资源。
        """
        if self.driver:
            try:
                logger.info("正在关闭浏览器...")
                self.driver.quit()
                self.driver = None
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器时发生错误: {str(e)}")
        else:
            logger.warning("浏览器未启动，无需关闭")
    
    def navigate_to(self, url: str) -> None:
        """导航到指定URL。
        
        Args:
            url: 目标URL地址
            
        Raises:
            BrowserException: 当浏览器未启动或导航失败时抛出
        """
        if not self.driver:
            raise BrowserException("浏览器未启动，无法导航")
        
        try:
            logger.info(f"导航到: {url}")
            self.driver.get(url)
            logger.info("导航成功")
        except Exception as e:
            error_msg = f"导航到 {url} 失败: {str(e)}"
            logger.error(error_msg)
            raise BrowserException(error_msg) from e

    def find_element(self, selector: str, by: str = "css") -> WebElement:
        """查找单个元素。
        
        Args:
            selector: 元素选择器
            by: 定位方式，支持 "css" 或 "xpath"，默认为 "css"
            
        Returns:
            找到的WebElement元素
            
        Raises:
            BrowserException: 当浏览器未启动或元素未找到时抛出
        """
        if not self.driver:
            raise BrowserException("浏览器未启动，无法查找元素")
        
        try:
            by_type = By.CSS_SELECTOR if by == "css" else By.XPATH
            logger.debug(f"查找元素: {selector} (方式: {by})")
            element = self.driver.find_element(by_type, selector)
            return element
        except NoSuchElementException as e:
            error_msg = f"未找到元素: {selector}"
            logger.error(error_msg)
            raise BrowserException(error_msg) from e
        except Exception as e:
            error_msg = f"查找元素时发生错误: {str(e)}"
            logger.error(error_msg)
            raise BrowserException(error_msg) from e
    
    def find_elements(self, selector: str, by: str = "css") -> List[WebElement]:
        """查找多个元素。
        
        Args:
            selector: 元素选择器
            by: 定位方式，支持 "css" 或 "xpath"，默认为 "css"
            
        Returns:
            找到的WebElement元素列表，如果没有找到则返回空列表
            
        Raises:
            BrowserException: 当浏览器未启动时抛出
        """
        if not self.driver:
            raise BrowserException("浏览器未启动，无法查找元素")
        
        try:
            by_type = By.CSS_SELECTOR if by == "css" else By.XPATH
            logger.debug(f"查找多个元素: {selector} (方式: {by})")
            elements = self.driver.find_elements(by_type, selector)
            logger.debug(f"找到 {len(elements)} 个元素")
            return elements
        except Exception as e:
            error_msg = f"查找元素时发生错误: {str(e)}"
            logger.error(error_msg)
            raise BrowserException(error_msg) from e
    
    def wait_for_element(
        self, 
        selector: str, 
        by: str = "css", 
        timeout: int = 10
    ) -> WebElement:
        """等待元素出现并返回。
        
        使用显式等待确保元素加载完成。
        
        Args:
            selector: 元素选择器
            by: 定位方式，支持 "css" 或 "xpath"，默认为 "css"
            timeout: 超时时间（秒），默认10秒
            
        Returns:
            找到的WebElement元素
            
        Raises:
            BrowserException: 当浏览器未启动或等待超时时抛出
        """
        if not self.driver:
            raise BrowserException("浏览器未启动，无法等待元素")
        
        try:
            by_type = By.CSS_SELECTOR if by == "css" else By.XPATH
            logger.debug(f"等待元素出现: {selector} (超时: {timeout}秒)")
            
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(
                EC.presence_of_element_located((by_type, selector))
            )
            
            logger.debug("元素已出现")
            return element
        except TimeoutException as e:
            error_msg = f"等待元素超时: {selector} (超时时间: {timeout}秒)"
            logger.error(error_msg)
            raise BrowserException(error_msg) from e
        except Exception as e:
            error_msg = f"等待元素时发生错误: {str(e)}"
            logger.error(error_msg)
            raise BrowserException(error_msg) from e
    
    def save_cookies(self, filepath: str) -> None:
        """保存浏览器Cookie到文件。
        
        用于持久化登录状态。
        
        Args:
            filepath: Cookie保存路径
            
        Raises:
            BrowserException: 当浏览器未启动或保存失败时抛出
        """
        if not self.driver:
            raise BrowserException("浏览器未启动，无法保存Cookie")
        
        try:
            logger.info(f"保存Cookie到: {filepath}")
            
            # 确保目录存在
            cookie_path = Path(filepath)
            cookie_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 获取并保存Cookie
            cookies = self.driver.get_cookies()
            with open(filepath, "wb") as f:
                pickle.dump(cookies, f)
            
            logger.info(f"成功保存 {len(cookies)} 个Cookie")
        except Exception as e:
            error_msg = f"保存Cookie失败: {str(e)}"
            logger.error(error_msg)
            raise BrowserException(error_msg) from e
    
    def load_cookies(self, filepath: str) -> None:
        """从文件加载Cookie到浏览器。
        
        用于恢复登录状态。
        
        Args:
            filepath: Cookie文件路径
            
        Raises:
            BrowserException: 当浏览器未启动或加载失败时抛出
        """
        if not self.driver:
            raise BrowserException("浏览器未启动，无法加载Cookie")
        
        try:
            cookie_path = Path(filepath)
            if not cookie_path.exists():
                logger.warning(f"Cookie文件不存在: {filepath}")
                return
            
            logger.info(f"从文件加载Cookie: {filepath}")
            
            # 加载并设置Cookie
            with open(filepath, "rb") as f:
                cookies = pickle.load(f)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"添加Cookie失败: {cookie.get('name', 'unknown')} - {str(e)}")
            
            logger.info(f"成功加载 {len(cookies)} 个Cookie")
            
            # 刷新页面以应用Cookie
            self.driver.refresh()
            
        except Exception as e:
            error_msg = f"加载Cookie失败: {str(e)}"
            logger.error(error_msg)
            raise BrowserException(error_msg) from e
    
    def is_logged_in(self) -> bool:
        """检查当前是否已登录。
        
        通过检查特定元素或Cookie来判断登录状态。
        针对 1688 旺旺网页版进行优化。
        
        Returns:
            True表示已登录，False表示未登录
            
        Raises:
            BrowserException: 当浏览器未启动时抛出
        """
        if not self.driver:
            raise BrowserException("浏览器未启动，无法检查登录状态")
        
        try:
            logger.debug("检查登录状态...")
            
            # 方法1: 检查当前URL是否包含登录页面特征
            current_url = self.driver.current_url
            if "login" in current_url.lower():
                logger.info("当前在登录页面，未登录")
                return False
            
            # 方法2: 检查是否存在 1688 登录相关的Cookie
            cookies = self.driver.get_cookies()
            cookie_names = [cookie.get("name", "") for cookie in cookies]
            
            # 1688 常见的登录 Cookie
            auth_cookies = ["_tb_token_", "cookie2", "t", "unb", "uc1", "lgc"]
            has_auth_cookie = any(name in cookie_names for name in auth_cookies)
            
            if has_auth_cookie:
                logger.info("检测到 1688 登录Cookie，已登录")
                return True
            
            # 方法3: 尝试查找登录后才有的元素
            try:
                # 1688 IM 页面登录后的常见元素
                # 可能的选择器：会话列表、聊天窗口等
                elements_to_check = [
                    ".chat-list",
                    ".message-list", 
                    ".contact-list",
                    "#app",
                    ".im-container"
                ]
                
                for selector in elements_to_check:
                    try:
                        self.wait_for_element(selector, timeout=2)
                        logger.info(f"找到登录后的元素 {selector}，已登录")
                        return True
                    except BrowserException:
                        continue
                
                logger.info("未找到登录后的元素，可能未登录")
                return False
                
            except Exception as e:
                logger.debug(f"检查页面元素时出错: {str(e)}")
                return False
                
        except Exception as e:
            logger.warning(f"检查登录状态时发生错误: {str(e)}")
            # 发生错误时默认返回False，让系统等待用户登录
            return False

"""浏览器控制器模块。

提供浏览器自动化控制功能，包括启动、关闭、导航、元素定位等操作。
"""

import pickle
from pathlib import Path
from typing import List, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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
            # logger.debug(f"等待元素出现: {selector} (超时: {timeout}秒)")

            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(
                EC.presence_of_element_located((by_type, selector))
            )

            # logger.debug("元素已出现")
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

            # 获取当前页面域名
            current_url = self.driver.current_url
            logger.debug(f"当前页面URL: {current_url}")

            # 加载Cookie
            with open(filepath, "rb") as f:
                cookies = pickle.load(f)

            logger.info(f"从文件读取到 {len(cookies)} 个Cookie")

            # 统计成功和失败的Cookie数量
            success_count = 0
            fail_count = 0

            for cookie in cookies:
                try:
                    # 检查Cookie是否有必需的字段
                    if 'name' not in cookie or 'value' not in cookie:
                        logger.warning(f"Cookie缺少必需字段: {cookie}")
                        fail_count += 1
                        continue

                    # 尝试添加Cookie
                    self.driver.add_cookie(cookie)
                    success_count += 1
                    logger.debug(f"✓ 成功添加Cookie: {cookie.get('name')} (domain: {cookie.get('domain', 'N/A')})")
                except Exception as e:
                    fail_count += 1
                    logger.debug(f"✗ 添加Cookie失败: {cookie.get('name', 'unknown')} - {str(e)}")

            if success_count > 0:
                logger.info(f"Cookie加载完成 - 成功: {success_count}, 失败: {fail_count}, 总数: {len(cookies)}")
            else:
                logger.warning(f"所有Cookie加载失败！可能是域名不匹配或Cookie格式错误")

            # 注意：不在这里刷新页面，让调用者决定何时刷新
            # 这样可以避免在错误的时机刷新导致Cookie失效

        except Exception as e:
            error_msg = f"加载Cookie失败: {str(e)}"
            logger.error(error_msg)
            raise BrowserException(error_msg) from e

    def load_cookies_via_cdp(self, cookies: List[dict]) -> None:
        """使用 Chrome DevTools Protocol 加载 Cookie。
        
        CDP 方式比 add_cookie 更可靠，可以在任何时候设置任何域名的 Cookie。
        
        Args:
            cookies: Cookie字典列表
            
        Raises:
            BrowserException: 当浏览器未启动或加载失败时抛出
        """
        if not self.driver:
            raise BrowserException("浏览器未启动，无法加载Cookie")

        try:
            logger.info(f"使用 CDP 加载 {len(cookies)} 个 Cookie")

            success_count = 0
            fail_count = 0

            for cookie in cookies:
                try:
                    # 检查Cookie是否有必需的字段
                    if 'name' not in cookie or 'value' not in cookie:
                        logger.warning(f"Cookie缺少必需字段: {cookie}")
                        fail_count += 1
                        continue

                    # 确保Cookie有domain字段
                    if 'domain' not in cookie:
                        cookie['domain'] = '.1688.com'
                    
                    # 使用 CDP 命令设置 Cookie
                    self.driver.execute_cdp_cmd('Network.setCookie', {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie['domain'],
                        'path': cookie.get('path', '/'),
                        'secure': cookie.get('secure', True),
                        'httpOnly': cookie.get('httpOnly', False),
                    })
                    success_count += 1
                    logger.debug(f"✓ 成功添加Cookie: {cookie.get('name')} (domain: {cookie.get('domain')})")
                except Exception as e:
                    fail_count += 1
                    logger.debug(f"✗ 添加Cookie失败: {cookie.get('name', 'unknown')} - {str(e)}")

            logger.info(f"CDP Cookie加载完成 - 成功: {success_count}, 失败: {fail_count}, 总数: {len(cookies)}")

        except Exception as e:
            error_msg = f"使用CDP加载Cookie失败: {str(e)}"
            logger.error(error_msg)
            raise BrowserException(error_msg) from e

    def load_cookies_from_dict(self, cookies: List[dict]) -> None:
        """从字典列表加载Cookie到浏览器。
        
        用于手动配置Cookie恢复登录状态。
        由于Selenium的限制，需要先访问对应的域名才能设置该域名的Cookie。
        
        Args:
            cookies: Cookie字典列表，每个字典至少包含 name 和 value 字段
            
        Raises:
            BrowserException: 当浏览器未启动或加载失败时抛出
            
        Examples:
            >>> cookies = [
            ...     {"name": "_tb_token_", "value": "xxx", "domain": ".1688.com"},
            ...     {"name": "cookie2", "value": "yyy", "domain": ".1688.com"}
            ... ]
            >>> browser.load_cookies_from_dict(cookies)
        """
        if not self.driver:
            raise BrowserException("浏览器未启动，无法加载Cookie")

        try:
            logger.info(f"从字典加载 {len(cookies)} 个Cookie")

            # 按域名分组Cookie
            cookies_by_domain = {}
            for cookie in cookies:
                # 检查Cookie是否有必需的字段
                if 'name' not in cookie or 'value' not in cookie:
                    logger.warning(f"Cookie缺少必需字段: {cookie}")
                    continue

                # 确保Cookie有domain字段
                if 'domain' not in cookie:
                    cookie['domain'] = '.1688.com'
                
                # 确保Cookie有path字段
                if 'path' not in cookie:
                    cookie['path'] = '/'
                
                domain = cookie['domain']
                if domain not in cookies_by_domain:
                    cookies_by_domain[domain] = []
                cookies_by_domain[domain].append(cookie)
            
            logger.info(f"Cookie按域名分组: {list(cookies_by_domain.keys())}")
            
            # 统计成功和失败的Cookie数量
            total_success = 0
            total_fail = 0
            
            # 为每个域名访问对应的页面并设置Cookie
            domain_url_mapping = {
                '.1688.com': 'https://www.1688.com',
                '1688.com': 'https://www.1688.com',
                '.taobao.com': 'https://www.taobao.com',
                'taobao.com': 'https://www.taobao.com',
                '.alibaba.com': 'https://www.alibaba.com',
                'alibaba.com': 'https://www.alibaba.com',
            }
            
            for domain, domain_cookies in cookies_by_domain.items():
                # 找到对应的URL
                url = None
                for domain_pattern, domain_url in domain_url_mapping.items():
                    if domain_pattern in domain:
                        url = domain_url
                        break
                
                if not url:
                    # 尝试构造URL
                    clean_domain = domain.lstrip('.')
                    url = f"https://{clean_domain}"
                
                try:
                    logger.info(f"访问 {url} 以设置 {len(domain_cookies)} 个 {domain} 域名的Cookie")
                    self.driver.get(url)
                    
                    # 等待页面加载
                    import time
                    time.sleep(1)
                    
                    # 添加该域名的所有Cookie
                    success_count = 0
                    fail_count = 0
                    
                    for cookie in domain_cookies:
                        try:
                            # Selenium对Cookie域名有严格要求
                            # 如果当前在 www.1688.com，可以设置 .1688.com 或 www.1688.com 的Cookie
                            # 但需要确保域名格式正确
                            
                            # 创建Cookie副本以避免修改原始数据
                            cookie_to_add = cookie.copy()
                            
                            # 如果域名以点开头，Selenium可能会拒绝
                            # 尝试移除前导点
                            if cookie_to_add['domain'].startswith('.'):
                                # 先尝试不带点的域名
                                cookie_to_add['domain'] = cookie_to_add['domain'].lstrip('.')
                            
                            self.driver.add_cookie(cookie_to_add)
                            success_count += 1
                            logger.debug(f"✓ 成功添加Cookie: {cookie.get('name')} (domain: {cookie_to_add['domain']})")
                        except Exception as e:
                            # 如果失败，尝试使用原始域名（带点）
                            try:
                                self.driver.add_cookie(cookie)
                                success_count += 1
                                logger.debug(f"✓ 成功添加Cookie（第二次尝试）: {cookie.get('name')} (domain: {cookie['domain']})")
                            except Exception as e2:
                                fail_count += 1
                                # 打印第一个失败的Cookie的详细错误信息
                                if fail_count == 1:
                                    logger.warning(f"✗ 添加Cookie失败示例: {cookie.get('name')} (domain: {cookie['domain']})")
                                    logger.warning(f"   Cookie内容: {cookie}")
                                    logger.warning(f"   错误信息: {str(e2)}")
                                else:
                                    logger.debug(f"✗ 添加Cookie失败: {cookie.get('name')} (domain: {cookie['domain']}) - {str(e2)}")
                    
                    total_success += success_count
                    total_fail += fail_count
                    logger.info(f"{domain} 域名Cookie加载完成 - 成功: {success_count}, 失败: {fail_count}")
                    
                except Exception as e:
                    logger.warning(f"访问 {url} 失败: {str(e)}")
                    total_fail += len(domain_cookies)
            
            logger.info(f"所有Cookie加载完成 - 总成功: {total_success}, 总失败: {total_fail}, 总数: {len(cookies)}")

        except Exception as e:
            error_msg = f"从字典加载Cookie失败: {str(e)}"
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

            # 方法1: 检查当前URL是否包含登录页面或错误页面特征
            current_url = self.driver.current_url
            logger.debug(f"当前URL: {current_url}")

            # 检查是否在登录页面（包括淘宝登录和1688登录）
            login_indicators = [
                "login.taobao.com",
                "login.1688.com",
                "/login"
            ]
            if any(indicator in current_url.lower() for indicator in login_indicators):
                logger.info(f"当前在登录页面: {current_url}，未登录")
                return False

            # 检查是否在1688的404错误页面
            # https://page.1688.com/shtml/static/wrongpage.html 是1688的标准404页面
            error_indicators = [
                "page.1688.com/shtml/static/wrongpage.html",
                "wrongpage.html",
                "/wrongpage"
            ]
            if any(indicator in current_url.lower() for indicator in error_indicators):
                logger.warning(f"当前在1688错误页面(404): {current_url}，判定为未登录或无权限访问")
                return False

            # 方法2: 检查是否存在 1688 登录相关的Cookie（最重要的判断依据）
            cookies = self.driver.get_cookies()
            cookie_names = [cookie.get("name", "") for cookie in cookies]

            # 1688/淘宝最关键的登录 Cookie
            # _tb_token_ 和 cookie2 是最重要的认证Cookie
            critical_cookies = ["_tb_token_", "cookie2"]
            has_critical_cookies = all(name in cookie_names for name in critical_cookies)

            # 其他辅助登录 Cookie
            auth_cookies = ["t", "unb", "uc1", "lgc"]
            has_auth_cookie = any(name in cookie_names for name in auth_cookies)

            logger.debug(f"Cookie检查 - 关键Cookie: {has_critical_cookies}, 辅助Cookie: {has_auth_cookie}")
            logger.debug(f"当前Cookie列表: {cookie_names}")

            # 如果有关键Cookie，说明已登录
            if has_critical_cookies:
                logger.info("✓ 检测到关键登录Cookie (_tb_token_, cookie2)，已登录")
                return True

            # 如果有辅助Cookie但没有关键Cookie，可能是Cookie不完整
            if has_auth_cookie:
                logger.warning("检测到部分登录Cookie，但缺少关键Cookie，可能未完全登录")
                return False

            # 方法3: 检查页面标题
            try:
                page_title = self.driver.title
                logger.debug(f"页面标题: {page_title}")

                # 如果页面标题包含"登录"，说明未登录
                if "登录" in page_title:
                    logger.info(f"页面标题包含'登录': {page_title}，未登录")
                    return False

                # 如果页面标题包含"旺旺"或"消息"，说明已登录到聊天页面
                if "旺旺" in page_title or "消息" in page_title or "IM" in page_title:
                    logger.info(f"页面标题显示已登录: {page_title}")
                    return True
            except Exception as e:
                logger.debug(f"检查页面标题时出错: {str(e)}")

            # 默认返回False，需要登录
            logger.info("未检测到明确的登录标识，判定为未登录")
            return False

        except Exception as e:
            logger.warning(f"检查登录状态时发生错误: {str(e)}")
            # 发生错误时默认返回False，让系统等待用户登录
            return False

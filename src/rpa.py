"""旺旺RPA主控制器。

协调各个组件，实现旺旺消息的自动监控和回复功能。
"""

import time
import signal
import sys
from datetime import datetime
from typing import Optional

from src.core.browser_controller import BrowserController
from src.core.message_handler import MessageHandler
from src.core.session_manager import SessionManager
from src.utils.config_manager import ConfigManager
from src.models.config import Config
from src.models.session import Session
from src.utils.exceptions import WangWangRPAException, BrowserException, MessageException
from src.utils.logger import get_logger


logger = get_logger(__name__)


class WangWangRPA:
    """旺旺RPA主控制器类。
    
    负责协调浏览器控制器、消息处理器、会话管理器和自动回复引擎，
    实现旺旺消息的自动监控和回复功能。
    
    Attributes:
        config: 系统配置对象
        browser: 浏览器控制器
        message_handler: 消息处理器
        session_manager: 会话管理器
        is_running: 系统运行状态标志
    """
    
    def __init__(self, config_path: str = "config/config.yaml", cookies: Optional[list] = None):
        """初始化RPA主控制器。
        
        加载配置并初始化各个组件。
        
        Args:
            config_path: 配置文件路径
            cookies: 可选的Cookie列表，用于手动配置登录状态。
                    每个Cookie应为字典，至少包含 name 和 value 字段。
                    示例: [{"name": "_tb_token_", "value": "xxx", "domain": ".1688.com"}]
            
        Raises:
            WangWangRPAException: 初始化失败时抛出
        """
        logger.info("=" * 60)
        logger.info("旺旺RPA系统初始化开始")
        logger.info("=" * 60)
        
        try:
            # 加载配置
            logger.info("正在加载配置...")
            config_manager = ConfigManager(config_path)
            self.config = config_manager.load_config()
            logger.info("配置加载完成")
            
            # 初始化浏览器控制器
            logger.info("正在初始化浏览器控制器...")
            self.browser = BrowserController(
                headless=self.config.browser_headless,
                user_data_dir=self.config.browser_user_data_dir
            )
            logger.info("浏览器控制器初始化完成")
            
            # 初始化消息处理器
            logger.info("正在初始化消息处理器...")
            self.message_handler = MessageHandler(self.browser)
            logger.info("消息处理器初始化完成")
            
            # 初始化会话管理器
            logger.info("正在初始化会话管理器...")
            self.session_manager = SessionManager()
            logger.info("会话管理器初始化完成")
            
            # 运行状态标志
            self.is_running = False
            
            # 保存手动配置的Cookie
            self.manual_cookies = cookies
            
            # 注册信号处理器，用于优雅退出（仅在主线程中注册）
            try:
                import threading
                if threading.current_thread() is threading.main_thread():
                    signal.signal(signal.SIGINT, self._signal_handler)
                    signal.signal(signal.SIGTERM, self._signal_handler)
                    logger.debug("信号处理器已注册")
                else:
                    logger.debug("非主线程，跳过信号处理器注册")
            except Exception as e:
                logger.debug(f"注册信号处理器失败（这在非主线程中是正常的）: {e}")
            
            logger.info("=" * 60)
            logger.info("旺旺RPA系统初始化完成")
            logger.info("=" * 60)
            
        except Exception as e:
            error_msg = f"RPA系统初始化失败: {str(e)}"
            logger.error(error_msg)
            raise WangWangRPAException(error_msg) from e

    def _signal_handler(self, signum, frame):
        """信号处理器，用于优雅退出。
        
        Args:
            signum: 信号编号
            frame: 当前栈帧
        """
        logger.info(f"接收到退出信号 ({signum})，正在停止系统...")
        self.stop()
        sys.exit(0)
    
    def start(self) -> None:
        """启动RPA系统。
        
        启动浏览器、检查登录状态、导航到旺旺聊天页面。
        
        Raises:
            WangWangRPAException: 启动失败时抛出
        """
        try:
            logger.info("正在启动RPA系统...")
            
            # 启动浏览器
            logger.info("正在启动浏览器...")
            self.browser.start()
            logger.info("浏览器启动成功")
            
            # 先导航到1688首页
            logger.info(f"正在导航到1688首页: {self.config.wangwang_home_url}")
            self.browser.navigate_to(self.config.wangwang_home_url)
            logger.info("导航成功")
            
            # 等待页面加载
            time.sleep(2)
            
            # 优先使用手动配置的Cookie
            cookie_loaded_successfully = False
            import os
            
            if self.manual_cookies:
                try:
                    logger.info(f"使用手动配置的Cookie（共 {len(self.manual_cookies)} 个）")
                    
                    # 使用 CDP 方式加载 Cookie（更可靠）
                    try:
                        self.browser.load_cookies_via_cdp(self.manual_cookies)
                        logger.info("使用 CDP 方式加载 Cookie 成功")
                    except Exception as cdp_error:
                        logger.warning(f"CDP 方式失败，尝试传统方式: {cdp_error}")
                        self.browser.load_cookies_from_dict(self.manual_cookies)
                    
                    logger.info("手动配置的Cookie已加载到浏览器")
                    
                    # 导航到1688首页以应用Cookie
                    logger.info("导航到1688首页以应用Cookie...")
                    self.browser.navigate_to(self.config.wangwang_home_url)
                    time.sleep(3)  # 等待页面加载
                    
                    # 检查登录状态
                    logger.info("验证Cookie是否有效...")
                    if self.browser.is_logged_in():
                        logger.info("✓ 手动配置的Cookie有效，已自动登录1688账号")
                        cookie_loaded_successfully = True
                        
                        # 保存有效的Cookie到文件，方便下次使用
                        try:
                            cookie_file = f"{self.config.browser_user_data_dir}/cookies.pkl"
                            os.makedirs(self.config.browser_user_data_dir, exist_ok=True)
                            self.browser.save_cookies(cookie_file)
                            logger.info(f"已将有效的Cookie保存到: {cookie_file}")
                        except Exception as e:
                            logger.warning(f"保存Cookie到文件失败: {e}")
                    else:
                        logger.warning("✗ 手动配置的Cookie已过期或无效，需要重新登录")
                        
                except Exception as e:
                    logger.warning(f"加载手动配置的Cookie时出错: {e}")
            
            # 如果没有手动配置Cookie或手动Cookie无效，尝试从文件加载
            cookie_file = f"{self.config.browser_user_data_dir}/cookies.pkl"
            if not cookie_loaded_successfully and os.path.exists(cookie_file):
                try:
                    logger.info(f"发现已保存的Cookie文件: {cookie_file}")
                    
                    # 检查Cookie文件的修改时间
                    import datetime
                    cookie_mtime = os.path.getmtime(cookie_file)
                    cookie_age = time.time() - cookie_mtime
                    cookie_age_hours = cookie_age / 3600
                    logger.info(f"Cookie文件创建于 {cookie_age_hours:.1f} 小时前")
                    
                    # 如果Cookie超过24小时，可能已过期
                    if cookie_age_hours > 24:
                        logger.warning(f"Cookie文件已超过24小时，可能已过期")
                    
                    # 加载Cookie
                    self.browser.load_cookies(cookie_file)
                    logger.info("Cookie已加载到浏览器")
                    
                    # 不要立即刷新，而是导航到一个新页面让Cookie生效
                    # 这样可以避免某些安全检查
                    logger.info("导航到1688首页以应用Cookie...")
                    self.browser.navigate_to(self.config.wangwang_home_url)
                    time.sleep(3)  # 等待页面加载
                    
                    # 检查登录状态
                    logger.info("验证Cookie是否有效...")
                    if self.browser.is_logged_in():
                        logger.info("✓ Cookie有效，已自动登录1688账号")
                        cookie_loaded_successfully = True
                    else:
                        logger.warning("✗ Cookie已过期或无效，需要重新登录")
                        # 删除无效的Cookie文件
                        try:
                            os.remove(cookie_file)
                            logger.info("已删除无效的Cookie文件")
                        except:
                            pass
                        
                except Exception as e:
                    logger.warning(f"加载Cookie时出错: {e}")
            else:
                logger.info("未找到已保存的Cookie文件，需要首次登录")
            
            # 如果Cookie无效或不存在，需要登录
            if not cookie_loaded_successfully:
                logger.info("正在检查登录状态...")
                if not self.browser.is_logged_in():
                    logger.warning("检测到未登录状态，需要先登录")
                    self._wait_for_login()
                else:
                    logger.info("已登录1688账号")
            
            # 登录成功后，导航到旺旺聊天页面
            logger.info(f"正在导航到旺旺聊天页面: {self.config.wangwang_chat_url}")
            self.browser.navigate_to(self.config.wangwang_chat_url)
            
            # 等待SPA应用加载完成（AIR应用需要更长的加载时间）
            logger.info("等待旺旺聊天页面加载...")
            time.sleep(5)  # 等待聊天页面加载
            
            # 检查是否成功进入聊天页面
            current_url = self.browser.driver.current_url
            logger.info(f"当前页面URL: {current_url}")
            
            # 检查是否遇到1688的404错误页面
            error_indicators = [
                "page.1688.com/shtml/static/wrongpage.html",
                "wrongpage.html"
            ]
            is_error_page = any(indicator in current_url.lower() for indicator in error_indicators)
            
            if is_error_page:
                logger.warning(f"配置的聊天页面URL无法访问(404): {self.config.wangwang_chat_url}")
                logger.info("尝试使用备用URL...")
                
                # 尝试备用URL列表
                backup_urls = [
                    "https://air.1688.com/app/ocms-fusion-components-1688/def_cbu_web_im/index.html#/",  # AIR旺旺IM
                    "https://work.1688.com/home/message.htm",  # 工作台消息中心
                    "https://message.1688.com/",  # 消息中心
                    "https://www.1688.com/"  # 首页（作为最后备选）
                ]
                
                success = False
                for backup_url in backup_urls:
                    try:
                        logger.info(f"尝试访问: {backup_url}")
                        self.browser.navigate_to(backup_url)
                        time.sleep(5)  # 等待页面加载
                        
                        current_url = self.browser.driver.current_url
                        # 检查是否还是404页面
                        if not any(indicator in current_url.lower() for indicator in error_indicators):
                            logger.info(f"成功访问: {current_url}")
                            success = True
                            break
                        else:
                            logger.warning(f"该URL也无法访问: {backup_url}")
                    except Exception as e:
                        logger.warning(f"访问 {backup_url} 失败: {e}")
                        continue
                
                if not success:
                    error_msg = "无法找到可用的旺旺聊天页面，所有URL都返回404"
                    logger.error(error_msg)
                    raise WangWangRPAException(error_msg)
            
            # 检查页面标题，确认是否成功加载
            try:
                page_title = self.browser.driver.title
                logger.info(f"聊天页面标题: {page_title}")
            except Exception as e:
                logger.warning(f"无法获取页面标题: {e}")
            
            logger.info("RPA系统启动完成，已进入旺旺聊天页面")
            
        except BrowserException as e:
            error_msg = f"浏览器启动失败: {str(e)}"
            logger.error(error_msg)
            raise WangWangRPAException(error_msg) from e
        except Exception as e:
            error_msg = f"RPA系统启动失败: {str(e)}"
            logger.error(error_msg)
            raise WangWangRPAException(error_msg) from e
    
    def _wait_for_login(self) -> None:
        """等待用户手动登录并保存Cookie。
        
        当检测到未登录状态时，导航到登录页面，等待用户手动完成登录操作，
        然后保存登录凭证。
        
        Raises:
            WangWangRPAException: 等待登录超时时抛出
        """
        logger.info("=" * 60)
        logger.info("检测到未登录状态，正在跳转到登录页面...")
        logger.info("=" * 60)
        
        try:
            # 导航到登录页面
            logger.info(f"正在导航到登录页面: {self.config.wangwang_login_url}")
            self.browser.navigate_to(self.config.wangwang_login_url)
            time.sleep(3)  # 等待页面加载
            
            logger.info("=" * 60)
            logger.info("请在浏览器中手动完成登录操作")
            logger.info("支持扫码登录或账号密码登录")
            logger.info("登录完成后，系统将自动保存登录状态")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.warning(f"导航到登录页面失败: {e}")
            raise WangWangRPAException(f"无法打开登录页面: {e}")
        
        # 等待用户登录
        max_wait_time = 300  # 最多等待5分钟
        wait_interval = 5  # 每5秒检查一次
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            time.sleep(wait_interval)
            elapsed_time += wait_interval
            
            try:
                if self.browser.is_logged_in():
                    logger.info("检测到登录成功！")
                    
                    # 等待一下确保登录状态稳定
                    time.sleep(2)
                    
                    # 保存Cookie
                    cookie_file = f"{self.config.browser_user_data_dir}/cookies.pkl"
                    try:
                        # 确保目录存在
                        import os
                        os.makedirs(self.config.browser_user_data_dir, exist_ok=True)
                        
                        self.browser.save_cookies(cookie_file)
                        logger.info(f"登录状态已保存到: {cookie_file}")
                        
                        # 验证Cookie文件是否创建成功
                        if os.path.exists(cookie_file):
                            file_size = os.path.getsize(cookie_file)
                            logger.info(f"Cookie文件大小: {file_size} 字节")
                        else:
                            logger.warning("Cookie文件未成功创建")
                    except Exception as e:
                        logger.warning(f"保存Cookie失败: {e}")
                    
                    logger.info("登录流程完成")
                    return
                else:
                    logger.debug(f"等待登录中... ({elapsed_time}/{max_wait_time}秒)")
            except Exception as e:
                logger.debug(f"检查登录状态时出错: {e}")
        
        # 超时仍未登录
        error_msg = f"等待登录超时（{max_wait_time}秒）"
        logger.error(error_msg)
        raise WangWangRPAException(error_msg)
    
    def run(self) -> None:
        """运行RPA系统主循环。
        
        进入消息监控循环，定期检查新消息并处理。
        集成自动回复逻辑：检查新消息 -> 匹配规则 -> 自动回复或标记为待处理。
        
        Raises:
            WangWangRPAException: 运行过程中发生错误时抛出
        """
        logger.info("=" * 60)
        logger.info("开始监控旺旺消息")
        logger.info(f"检查间隔: {self.config.check_interval}秒")
        logger.info("按 Ctrl+C 停止监控")
        logger.info("=" * 60)
        
        self.is_running = True
        message_check_count = 0
        last_cleanup_time = datetime.now()
        
        try:
            while self.is_running:
                try:
                    message_check_count += 1
                    logger.debug(f"第 {message_check_count} 次检查消息...")
                    
                    # 检查新消息
                    new_messages = self.message_handler.check_new_messages()
                    
                    if new_messages:
                        logger.info(f"收到 {len(new_messages)} 条新消息")
                        
                        # 处理每条新消息
                        for message in new_messages:
                            try:
                                self._process_message(message)
                            except Exception as e:
                                logger.error(f"处理消息失败: {str(e)}")
                                continue
                    
                    # 定期清理非活跃会话（每10分钟）
                    now = datetime.now()
                    if (now - last_cleanup_time).total_seconds() >= 600:
                        logger.info("开始清理非活跃会话...")
                        cleaned_count = self.session_manager.cleanup_inactive_sessions(
                            self.config.session_timeout
                        )
                        logger.info(f"清理完成，共清理 {cleaned_count} 个非活跃会话")
                        last_cleanup_time = now
                    
                    # 等待下一次检查
                    time.sleep(self.config.check_interval)
                    
                except MessageException as e:
                    logger.error(f"消息处理错误: {str(e)}")
                    # 继续运行，不中断监控
                    time.sleep(self.config.check_interval)
                    continue
                    
                except Exception as e:
                    logger.error(f"运行时错误: {str(e)}", exc_info=True)
                    # 继续运行，不中断监控
                    time.sleep(self.config.check_interval)
                    continue
        
        except KeyboardInterrupt:
            logger.info("接收到中断信号，正在停止...")
        except Exception as e:
            error_msg = f"RPA系统运行失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise WangWangRPAException(error_msg) from e
        finally:
            self.is_running = False
            logger.info("消息监控已停止")

    def _process_message(self, message) -> None:
        """处理单条消息。
        
        更新会话状态，尝试匹配自动回复规则，发送回复或标记为待处理。
        
        Args:
            message: 要处理的消息对象
        """
        logger.info(f"处理消息 - 来自: {message.contact_name}, 内容: {message.content[:50]}...")
        
        # 跳过自己发送的消息
        if message.is_sent:
            logger.debug("跳过自己发送的消息")
            return
        
        # 跳过系统消息
        if message.message_type == "system":
            logger.debug("跳过系统消息")
            return
        
        # 更新或创建会话
        session = self.session_manager.get_session(message.contact_id)
        if session:
            # 更新现有会话
            session.last_message_time = message.timestamp
            session.message_count += 1
            self.session_manager.update_session_activity(message.contact_id)
            logger.debug(f"更新会话: {message.contact_name}, 消息数: {session.message_count}")
        else:
            # 创建新会话
            session = Session(
                contact_id=message.contact_id,
                contact_name=message.contact_name,
                last_message_time=message.timestamp,
                last_activity_time=datetime.now(),
                message_count=1,
                is_active=True
            )
            self.session_manager.add_session(session)
            logger.info(f"创建新会话: {message.contact_name}")
        
        # 记录消息，标记为待人工处理
        logger.info(f"消息已记录，等待人工处理: {message.content[:50]}...")
    
    def stop(self) -> None:
        """停止RPA系统并清理资源。
        
        停止消息监控循环，关闭浏览器，清理所有资源。
        """
        logger.info("正在停止RPA系统...")
        
        # 停止运行循环
        self.is_running = False
        
        # 关闭浏览器
        if self.browser:
            try:
                self.browser.stop()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器时出错: {str(e)}")
        
        # 输出统计信息
        if self.session_manager:
            total_sessions = self.session_manager.get_session_count()
            active_sessions = len(self.session_manager.get_active_sessions())
            logger.info(f"会话统计 - 总数: {total_sessions}, 活跃: {active_sessions}")
        
        logger.info("=" * 60)
        logger.info("旺旺RPA系统已停止")
        logger.info("=" * 60)
    
    def get_status(self) -> dict:
        """获取系统运行状态。
        
        Returns:
            包含系统状态信息的字典
        """
        return {
            "is_running": self.is_running,
            "total_sessions": self.session_manager.get_session_count() if self.session_manager else 0,
            "active_sessions": len(self.session_manager.get_active_sessions()) if self.session_manager else 0,
        }

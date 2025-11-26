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
from src.core.auto_reply_engine import AutoReplyEngine
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
        auto_reply_engine: 自动回复引擎
        is_running: 系统运行状态标志
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化RPA主控制器。
        
        加载配置并初始化各个组件。
        
        Args:
            config_path: 配置文件路径
            
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
            
            # 初始化自动回复引擎
            if self.config.auto_reply_enabled:
                logger.info("正在初始化自动回复引擎...")
                self.auto_reply_engine = AutoReplyEngine(
                    self.config.auto_reply_rules_file
                )
                try:
                    self.auto_reply_engine.load_rules()
                    logger.info(f"自动回复引擎初始化完成，加载了 {self.auto_reply_engine.get_rules_count()} 条规则")
                except Exception as e:
                    logger.warning(f"加载自动回复规则失败: {e}，自动回复功能将被禁用")
                    self.config.auto_reply_enabled = False
                    self.auto_reply_engine = None
            else:
                logger.info("自动回复功能已禁用")
                self.auto_reply_engine = None
            
            # 运行状态标志
            self.is_running = False
            
            # 注册信号处理器，用于优雅退出
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
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
        
        启动浏览器、导航到旺旺页面、检查登录状态。
        
        Raises:
            WangWangRPAException: 启动失败时抛出
        """
        try:
            logger.info("正在启动RPA系统...")
            
            # 启动浏览器
            logger.info("正在启动浏览器...")
            self.browser.start()
            logger.info("浏览器启动成功")
            
            # 导航到旺旺页面
            logger.info(f"正在导航到旺旺页面: {self.config.wangwang_url}")
            self.browser.navigate_to(self.config.wangwang_url)
            logger.info("导航成功")
            
            # 等待页面加载
            time.sleep(3)
            
            # 检查登录状态
            logger.info("正在检查登录状态...")
            if not self.browser.is_logged_in():
                logger.warning("检测到未登录状态")
                self._wait_for_login()
            else:
                logger.info("已登录，可以开始监控消息")
            
            logger.info("RPA系统启动完成")
            
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
        
        当检测到未登录状态时，等待用户手动完成登录操作，
        然后保存登录凭证。
        """
        logger.info("=" * 60)
        logger.info("请在浏览器中手动完成登录操作")
        logger.info("登录完成后，系统将自动保存登录状态")
        logger.info("=" * 60)
        
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
                    
                    # 保存Cookie
                    cookie_file = f"{self.config.browser_user_data_dir}/cookies.pkl"
                    try:
                        self.browser.save_cookies(cookie_file)
                        logger.info(f"登录状态已保存到: {cookie_file}")
                    except Exception as e:
                        logger.warning(f"保存Cookie失败: {e}")
                    
                    return
                else:
                    logger.debug(f"等待登录中... ({elapsed_time}/{max_wait_time}秒)")
            except Exception as e:
                logger.debug(f"检查登录状态时出错: {e}")
        
        # 超时仍未登录
        logger.warning(f"等待登录超时（{max_wait_time}秒），请重新启动系统")
        raise WangWangRPAException("等待用户登录超时")
    
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
        logger.info(f"自动回复: {'启用' if self.config.auto_reply_enabled else '禁用'}")
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
        
        # 尝试自动回复
        if self.config.auto_reply_enabled and self.auto_reply_engine:
            try:
                reply_content = self.auto_reply_engine.match_rule(message.content)
                
                if reply_content:
                    logger.info(f"匹配到自动回复规则，准备发送回复...")
                    
                    # 发送自动回复
                    success = self.message_handler.send_message(
                        contact_id=message.contact_id,
                        content=reply_content,
                        retry_times=self.config.retry_times,
                        retry_delay=self.config.retry_delay
                    )
                    
                    if success:
                        logger.info(f"自动回复发送成功: {reply_content[:50]}...")
                        # 更新会话活跃时间
                        self.session_manager.update_session_activity(message.contact_id)
                    else:
                        logger.warning("自动回复发送失败")
                else:
                    logger.info("消息未匹配任何自动回复规则，标记为待人工处理")
                    
            except Exception as e:
                logger.error(f"自动回复处理失败: {str(e)}")
        else:
            logger.debug("自动回复功能未启用，消息标记为待人工处理")
    
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
            "auto_reply_enabled": self.config.auto_reply_enabled,
            "total_sessions": self.session_manager.get_session_count() if self.session_manager else 0,
            "active_sessions": len(self.session_manager.get_active_sessions()) if self.session_manager else 0,
            "auto_reply_rules": self.auto_reply_engine.get_rules_count() if self.auto_reply_engine else 0,
        }

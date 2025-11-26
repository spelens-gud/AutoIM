"""消息处理器模块。

负责处理旺旺消息的接收、发送和解析功能。
"""

import time
from datetime import datetime
from typing import List, Optional, Set
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)

from src.core.browser_controller import BrowserController
from src.models.message import Message
from src.utils.exceptions import MessageException
from src.utils.logger import get_logger


logger = get_logger(__name__)


class MessageHandler:
    """消息处理器类。
    
    负责处理消息的接收、发送、解析等操作。
    
    Attributes:
        browser: 浏览器控制器实例
        processed_message_ids: 已处理的消息ID集合，用于去重
    """
    
    def __init__(self, browser: BrowserController):
        """初始化消息处理器。
        
        Args:
            browser: 浏览器控制器实例
        """
        self.browser = browser
        self.processed_message_ids: Set[str] = set()
        
        logger.info("消息处理器初始化完成")
    
    def check_new_messages(self) -> List[Message]:
        """检查并返回新消息列表。
        
        轮询检查是否有新消息到达，并返回未处理的消息列表。
        
        Returns:
            新消息列表，如果没有新消息则返回空列表
            
        Raises:
            MessageException: 当检查消息失败时抛出
        """
        try:
            logger.debug("检查新消息...")
            
            # 获取当前页面的消息元素列表
            message_elements = self.get_message_list()
            
            if not message_elements:
                logger.debug("未找到消息元素")
                return []
            
            new_messages = []
            
            # 解析每个消息元素
            for element in message_elements:
                try:
                    message = self.parse_message_element(element)
                    
                    # 检查是否已处理过该消息
                    if message.message_id not in self.processed_message_ids:
                        new_messages.append(message)
                        self.processed_message_ids.add(message.message_id)
                        logger.info(
                            f"发现新消息 - ID: {message.message_id}, "
                            f"来自: {message.contact_name}, 内容: {message.content[:20]}..."
                        )
                except Exception as e:
                    logger.warning(f"解析消息元素失败: {str(e)}")
                    continue
            
            if new_messages:
                logger.info(f"检查到 {len(new_messages)} 条新消息")
            else:
                logger.debug("没有新消息")
            
            return new_messages
            
        except Exception as e:
            error_msg = f"检查新消息失败: {str(e)}"
            logger.error(error_msg)
            raise MessageException(error_msg) from e

    def get_message_list(self) -> List[WebElement]:
        """获取当前页面的消息元素列表。
        
        Returns:
            消息元素列表，如果没有找到则返回空列表
            
        Raises:
            MessageException: 当获取消息列表失败时抛出
        """
        try:
            logger.debug("获取消息元素列表...")
            
            # 尝试多个可能的选择器
            # 这些选择器需要根据实际的旺旺网页版DOM结构调整
            selectors = [
                ".message-list .message-item",
                ".chat-message-list .message",
                "[class*='message-item']",
                "[class*='chat-message']",
            ]
            
            for selector in selectors:
                try:
                    elements = self.browser.find_elements(selector)
                    if elements:
                        logger.debug(f"使用选择器 '{selector}' 找到 {len(elements)} 个消息元素")
                        return elements
                except Exception as e:
                    logger.debug(f"选择器 '{selector}' 未找到元素: {str(e)}")
                    continue
            
            logger.debug("未找到任何消息元素")
            return []
            
        except Exception as e:
            error_msg = f"获取消息列表失败: {str(e)}"
            logger.error(error_msg)
            raise MessageException(error_msg) from e
    
    def parse_message_element(self, element: WebElement) -> Message:
        """从DOM元素中提取消息信息。
        
        解析消息元素，提取消息内容、发送者、时间戳、类型等信息。
        
        Args:
            element: 消息DOM元素
            
        Returns:
            解析后的Message对象
            
        Raises:
            MessageException: 当解析失败时抛出
        """
        try:
            # 生成消息ID（使用时间戳和内容的组合）
            # 实际应用中可能需要从元素属性中获取真实的消息ID
            message_id = element.get_attribute("data-message-id")
            if not message_id:
                # 如果没有消息ID属性，使用元素的其他属性生成唯一ID
                message_id = f"{element.get_attribute('id') or ''}{element.text[:20]}{int(time.time() * 1000)}"
            
            # 提取消息内容
            # 尝试多个可能的选择器
            content = ""
            content_selectors = [
                ".message-content",
                ".msg-content",
                "[class*='content']",
            ]
            
            for selector in content_selectors:
                try:
                    content_element = element.find_element("css selector", selector)
                    content = content_element.text.strip()
                    if content:
                        break
                except NoSuchElementException:
                    continue
            
            # 如果没有找到内容元素，使用整个元素的文本
            if not content:
                content = element.text.strip()
            
            # 提取发送者信息
            contact_name = "未知用户"
            contact_id = "unknown"
            sender_selectors = [
                ".sender-name",
                ".user-name",
                "[class*='sender']",
                "[class*='username']",
            ]
            
            for selector in sender_selectors:
                try:
                    sender_element = element.find_element("css selector", selector)
                    contact_name = sender_element.text.strip()
                    contact_id = sender_element.get_attribute("data-user-id") or contact_name
                    if contact_name:
                        break
                except NoSuchElementException:
                    continue
            
            # 提取时间戳
            timestamp = datetime.now()
            time_selectors = [
                ".message-time",
                ".msg-time",
                "[class*='time']",
                "[class*='timestamp']",
            ]
            
            for selector in time_selectors:
                try:
                    time_element = element.find_element("css selector", selector)
                    time_text = time_element.text.strip()
                    # 这里简化处理，实际应用中需要解析时间字符串
                    # 例如: "10:30", "昨天 15:20" 等格式
                    logger.debug(f"消息时间文本: {time_text}")
                    break
                except NoSuchElementException:
                    continue
            
            # 判断消息类型
            message_type = "text"
            if element.find_elements("css selector", "img, [class*='image']"):
                message_type = "image"
            elif "系统消息" in content or element.get_attribute("class") and "system" in element.get_attribute("class"):
                message_type = "system"
            
            # 判断是否为发送的消息（通常通过CSS类名判断）
            is_sent = False
            element_class = element.get_attribute("class") or ""
            if any(keyword in element_class.lower() for keyword in ["sent", "self", "own", "outgoing"]):
                is_sent = True
            
            message = Message(
                message_id=message_id,
                contact_id=contact_id,
                contact_name=contact_name,
                content=content,
                message_type=message_type,
                timestamp=timestamp,
                is_sent=is_sent,
                is_auto_reply=False,
            )
            
            logger.debug(f"成功解析消息: {message.message_id}")
            return message
            
        except Exception as e:
            error_msg = f"解析消息元素失败: {str(e)}"
            logger.error(error_msg)
            raise MessageException(error_msg) from e

    def switch_to_chat(self, contact_id: str) -> bool:
        """切换到指定联系人的聊天窗口。
        
        Args:
            contact_id: 联系人ID
            
        Returns:
            True表示切换成功，False表示切换失败
            
        Raises:
            MessageException: 当切换失败时抛出
        """
        try:
            logger.info(f"切换到联系人聊天窗口: {contact_id}")
            
            # 尝试多个可能的选择器来定位联系人列表项
            selectors = [
                f"[data-contact-id='{contact_id}']",
                f"[data-user-id='{contact_id}']",
                f".contact-item[data-id='{contact_id}']",
            ]
            
            for selector in selectors:
                try:
                    # 等待联系人元素出现
                    contact_element = self.browser.wait_for_element(selector, timeout=5)
                    
                    # 点击联系人切换到聊天窗口
                    contact_element.click()
                    
                    logger.info(f"成功切换到联系人 {contact_id} 的聊天窗口")
                    
                    # 等待聊天窗口加载
                    time.sleep(1)
                    
                    return True
                    
                except Exception as e:
                    logger.debug(f"选择器 '{selector}' 未找到联系人: {str(e)}")
                    continue
            
            # 如果所有选择器都失败，尝试通过联系人名称查找
            logger.warning(f"无法通过ID找到联系人 {contact_id}，尝试其他方法")
            return False
            
        except Exception as e:
            error_msg = f"切换到聊天窗口失败: {str(e)}"
            logger.error(error_msg)
            raise MessageException(error_msg) from e
    
    def send_message(
        self, 
        contact_id: str, 
        content: str, 
        retry_times: int = 2,
        retry_delay: int = 1
    ) -> bool:
        """发送消息到指定联系人。
        
        实现消息发送功能，包含重试机制。
        
        Args:
            contact_id: 联系人ID
            content: 消息内容
            retry_times: 失败时的重试次数，默认2次
            retry_delay: 重试间隔（秒），默认1秒
            
        Returns:
            True表示发送成功，False表示发送失败
            
        Raises:
            MessageException: 当发送失败且重试次数用尽时抛出
        """
        logger.info(f"准备发送消息到联系人 {contact_id}: {content[:50]}...")
        
        # 尝试发送消息，包含重试机制
        for attempt in range(retry_times + 1):
            try:
                if attempt > 0:
                    logger.warning(f"第 {attempt} 次重试发送消息...")
                    time.sleep(retry_delay)
                
                # 切换到目标聊天窗口
                if not self.switch_to_chat(contact_id):
                    logger.warning(f"无法切换到联系人 {contact_id} 的聊天窗口")
                    # 如果无法切换，继续尝试发送（可能已经在正确的窗口）
                
                # 定位输入框
                input_selectors = [
                    "#chat-input",
                    ".chat-input",
                    "[class*='input']",
                    "textarea[placeholder*='消息']",
                    "input[type='text'][class*='chat']",
                ]
                
                input_element = None
                for selector in input_selectors:
                    try:
                        input_element = self.browser.wait_for_element(selector, timeout=5)
                        if input_element:
                            logger.debug(f"找到输入框: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"选择器 '{selector}' 未找到输入框: {str(e)}")
                        continue
                
                if not input_element:
                    raise MessageException("未找到消息输入框")
                
                # 清空输入框并输入消息内容
                input_element.clear()
                input_element.send_keys(content)
                
                logger.debug("消息内容已输入")
                
                # 等待一小段时间确保内容输入完成
                time.sleep(0.5)
                
                # 定位并点击发送按钮
                send_button_selectors = [
                    ".send-button",
                    "button[class*='send']",
                    "[class*='btn-send']",
                    "button:contains('发送')",
                ]
                
                send_button = None
                for selector in send_button_selectors:
                    try:
                        send_button = self.browser.find_element(selector)
                        if send_button and send_button.is_displayed():
                            logger.debug(f"找到发送按钮: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"选择器 '{selector}' 未找到发送按钮: {str(e)}")
                        continue
                
                if not send_button:
                    # 如果没有找到发送按钮，尝试使用回车键发送
                    logger.debug("未找到发送按钮，尝试使用回车键发送")
                    from selenium.webdriver.common.keys import Keys
                    input_element.send_keys(Keys.RETURN)
                else:
                    # 点击发送按钮
                    send_button.click()
                
                logger.info(f"消息发送成功: {content[:50]}...")
                
                # 等待消息发送完成
                time.sleep(1)
                
                return True
                
            except Exception as e:
                logger.warning(f"发送消息失败 (尝试 {attempt + 1}/{retry_times + 1}): {str(e)}")
                
                # 如果是最后一次尝试，抛出异常
                if attempt >= retry_times:
                    error_msg = f"发送消息失败，已重试 {retry_times} 次: {str(e)}"
                    logger.error(error_msg)
                    raise MessageException(error_msg) from e
        
        return False

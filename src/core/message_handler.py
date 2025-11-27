"""消息处理器模块。

负责处理旺旺消息的接收、发送和解析功能。
"""

import time
from datetime import datetime
from typing import List, Set

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.remote.webelement import WebElement

from src.core.browser_controller import BrowserController
from src.models.message import Message
from src.utils.captcha_handler import CaptchaHandler
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
        self.captcha_handler = CaptchaHandler(browser)

        logger.info("消息处理器初始化完成")

    def check_new_messages(self) -> List[Message]:
        """检查并返回新消息列表。
        
        轮询检查是否有新消息到达，并返回未处理的消息列表。
        
        Returns:
            新消息列表，如果没有新消息则返回空列表
            
        Raises:
            MessageException: 当检查消息失败时抛出
        """
        logger.debug("检查新消息...")

        # 获取当前页面的消息元素列表
        message_elements = self.get_message_list()

        if not message_elements:
            logger.debug("未找到消息元素")
            return []

        new_messages = []

        # 解析每个消息元素
        for element in message_elements:
            message = self.parse_message_element(element)

            # 检查是否已处理过该消息
            if message.message_id not in self.processed_message_ids:
                new_messages.append(message)
                self.processed_message_ids.add(message.message_id)
            else:
                continue
        return new_messages

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
            )

            logger.debug(f"成功解析消息: {message.message_id}")
            return message

        except Exception as e:
            error_msg = f"解析消息元素失败: {str(e)}"
            logger.error(error_msg)
            raise MessageException(error_msg) from e

    def debug_contact_list(self) -> None:
        """调试方法：打印当前页面的联系人列表结构。
        
        用于帮助开发者了解实际的DOM结构，以便调整选择器。
        """
        try:
            logger.info("=== 开始调试联系人列表结构 ===")

            # 等待页面加载
            logger.info("等待页面加载...")
            time.sleep(2)

            # 检查是否有iframe
            logger.info("\n检查页面iframe结构:")
            try:
                iframes = self.browser.find_elements("iframe")
                logger.info(f"找到 {len(iframes)} 个iframe")

                for i, iframe in enumerate(iframes):
                    iframe_src = iframe.get_attribute("src") or "无src"
                    iframe_id = iframe.get_attribute("id") or "无ID"
                    logger.info(f"  [{i + 1}] iframe: id={iframe_id}, src={iframe_src[:100]}")

                    # 如果是旺旺聊天的iframe，切换进去
                    if "1688" in iframe_src and "im" in iframe_src.lower():
                        logger.info(f"  ✓ 找到旺旺聊天iframe，尝试切换...")
                        try:
                            self.browser.driver.switch_to.frame(iframe)
                            logger.info("  ✓ 成功切换到iframe")
                            time.sleep(1)
                            break
                        except Exception as e:
                            logger.warning(f"  ✗ 切换iframe失败: {str(e)}")
                            continue
            except Exception as e:
                logger.debug(f"检查iframe失败: {str(e)}")

            # 首先尝试查找旺旺特定的.conversation-item元素
            logger.info("\n检查旺旺会话列表 (.conversation-item):")
            try:
                # 等待元素出现，最多等待10秒
                max_wait = 10
                conversation_items = []

                for i in range(max_wait):
                    conversation_items = self.browser.find_elements(".conversation-item")
                    if conversation_items:
                        break
                    logger.info(f"  等待联系人列表加载... ({i + 1}/{max_wait}秒)")
                    time.sleep(1)

                if conversation_items:
                    logger.info(f"✓ 找到 {len(conversation_items)} 个会话项 (.conversation-item)")

                    # 打印前5个会话项的详细信息
                    for i, item in enumerate(conversation_items[:5]):
                        try:
                            item_id = item.get_attribute("id") or "无ID"
                            item_class = item.get_attribute("class") or "无class"

                            # 查找.name元素
                            try:
                                name_elem = item.find_element("css selector", ".name")
                                name_text = name_elem.text.strip()
                            except NoSuchElementException:
                                name_text = "未找到.name元素"

                            # 查找.desc元素
                            try:
                                desc_elem = item.find_element("css selector", ".desc")
                                desc_text = desc_elem.text.strip()[:30]
                            except NoSuchElementException:
                                desc_text = "无描述"

                            logger.info(f"\n  [{i + 1}] 会话项:")
                            logger.info(f"      ID: {item_id}")
                            logger.info(f"      联系人名称: {name_text}")
                            logger.info(f"      最后消息: {desc_text}")

                        except Exception as e:
                            logger.debug(f"  [{i + 1}] 无法获取会话项信息: {str(e)}")

                    logger.info("\n" + "=" * 60)
                    # 切换回主文档
                    self.browser.driver.switch_to.default_content()
                    return  # 找到了旺旺结构，直接返回
                else:
                    logger.info("未找到.conversation-item元素")
            except Exception as e:
                logger.debug(f"查找.conversation-item失败: {str(e)}")

            # 如果没有找到旺旺特定结构，尝试通用的联系人列表选择器
            logger.info("\n检查通用联系人列表结构:")
            list_selectors = [
                ".contact-list",
                ".user-list",
                ".session-list",
                "[class*='contact-list']",
                "[class*='user-list']",
                "[class*='session-list']",
                "[class*='conversation']",
                "ul[class*='list']",
            ]

            for selector in list_selectors:
                try:
                    elements = self.browser.find_elements(selector)
                    if elements:
                        logger.info(f"\n✓ 找到列表容器: {selector} (数量: {len(elements)})")

                        # 获取第一个列表的子元素
                        list_element = elements[0]
                        children = list_element.find_elements("css selector", "*")
                        logger.info(f"  列表包含 {len(children)} 个子元素")

                        # 打印前5个子元素的信息
                        for i, child in enumerate(children[:5]):
                            try:
                                tag = child.tag_name
                                classes = child.get_attribute("class") or "无class"
                                elem_id = child.get_attribute("id") or "无ID"
                                text = child.text.strip()[:50] or "无文本"
                                data_attrs = []

                                # 检查常见的data属性
                                for attr in ["data-id", "data-user-id", "data-contact-id", "data-userid", "data-nick"]:
                                    value = child.get_attribute(attr)
                                    if value:
                                        data_attrs.append(f"{attr}={value}")

                                logger.info(f"\n  [{i + 1}] <{tag}>")
                                logger.info(f"      class: {classes}")
                                logger.info(f"      id: {elem_id}")
                                logger.info(f"      text: {text}")
                                if data_attrs:
                                    logger.info(f"      data属性: {', '.join(data_attrs)}")
                            except Exception as e:
                                logger.debug(f"  [{i + 1}] 无法获取元素信息: {str(e)}")

                        break
                except Exception as e:
                    logger.debug(f"选择器 '{selector}' 未找到列表: {str(e)}")
                    continue

            logger.info("\n" + "=" * 60)
            logger.info("联系人列表结构调试完成")
            logger.info("=" * 60)

            # 切换回主文档
            try:
                self.browser.driver.switch_to.default_content()
            except Exception:
                pass

        except Exception as e:
            logger.error(f"调试联系人列表时出错: {str(e)}")
            # 确保切换回主文档
            try:
                self.browser.driver.switch_to.default_content()
            except Exception:
                pass

    def switch_to_chat(self, contact_id: str) -> bool:
        """切换到指定联系人的聊天窗口。
        
        Args:
            contact_id: 联系人ID或联系人名称
            
        Returns:
            True表示切换成功，False表示切换失败
            
        Raises:
            MessageException: 当切换失败时抛出
        """
        try:
            iframes = self.browser.find_elements("iframe")
            for iframe in iframes:
                iframe_src = iframe.get_attribute("src") or ""
                # 查找旺旺聊天的iframe
                if "1688" in iframe_src and "im" in iframe_src.lower():
                    logger.debug(f"找到旺旺iframe，切换进入: {iframe_src[:100]}")
                    self.browser.driver.switch_to.frame(iframe)
                    time.sleep(1)
                    break
            logger.debug(f"遍历所有会话项查找联系人")
            conversation_items = self.browser.find_elements(".conversation-item")
            if conversation_items:
                for idx, item in enumerate(conversation_items):
                    try:
                        # 使用 XPath 在当前 item 下查找 .name 元素
                        name_element = item.find_element("xpath", ".//div[@class='name']")
                        name_text = name_element.text.strip()

                        if name_text == contact_id:
                            # 滚动到元素可见
                            self.browser.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});",
                                                               item)
                            time.sleep(0.5)

                            # 点击整个会话项
                            item.click()
                            logger.info(f"成功切换到联系人 {contact_id}")
                            # time.sleep(1)
                            return True
                    except NoSuchElementException:
                        logger.debug(f"  [{idx + 1}] 未找到 .name 元素")
                        continue
                    except StaleElementReferenceException:
                        logger.debug(f"  [{idx + 1}] 元素已过期，跳过")
                        continue
                    except Exception as e:
                        logger.debug(f"  [{idx + 1}] 处理失败: {str(e)}")
                        continue
            else:
                logger.warning("未找到任何 .conversation-item 元素")

            # 所有策略都失败
            logger.info("提示: 请确保联系人在当前页面可见，或者检查联系人ID/名称是否正确")

            # 切换回主文档
            self.browser.driver.switch_to.default_content()
            return False

        except Exception as e:
            error_msg = f"切换到聊天窗口失败: {str(e)}"
            logger.error(error_msg)

            # 确保切换回主文档
            self.browser.driver.switch_to.default_content()
            raise MessageException(error_msg) from e

    def get_chat_messages(self, contact_id: str, max_messages: int = 100) -> List[Message]:
        """获取与指定联系人的所有聊天消息。
        
        切换到指定联系人的聊天窗口，并获取聊天记录中的所有消息。
        
        Args:
            contact_id: 联系人ID或联系人名称
            max_messages: 最多获取的消息数量，默认100条
            
        Returns:
            消息列表，按时间顺序排列（从旧到新）
            
        Raises:
            MessageException: 当获取消息失败时抛出
        """
        try:
            logger.info(f"开始获取联系人 {contact_id} 的聊天消息...")

            # 切换到聊天iframe
            logger.debug("切换到聊天iframe...")
            try:
                self.browser.driver.switch_to.default_content()
                iframe_selector = "iframe[src*='def_cbu_web_im_core']"
                chat_iframe = self.browser.wait_for_element(iframe_selector, timeout=5)

                if chat_iframe:
                    self.browser.driver.switch_to.frame(chat_iframe)
                    logger.debug("✓ 成功切换到聊天iframe")
                    time.sleep(1)
                else:
                    logger.warning("未找到聊天iframe")
            except Exception as e:
                logger.warning(f"切换到iframe失败: {str(e)}")
                raise MessageException("无法切换到聊天iframe") from e

            # 切换到目标联系人的聊天窗口
            logger.debug(f"切换到联系人 {contact_id} 的聊天窗口...")
            if not self.switch_to_chat(contact_id):
                self.browser.driver.switch_to.default_content()
                raise MessageException(f"无法切换到联系人 {contact_id} 的聊天窗口")

            # 等待聊天消息加载
            logger.debug("等待聊天消息加载...")
            time.sleep(2)

            # 尝试滚动到顶部加载更多历史消息
            logger.debug("尝试滚动加载历史消息...")
            try:
                # 查找消息容器
                message_container_selectors = [
                    ".message-list",
                    ".chat-message-list",
                    "[class*='message-list']",
                    "[class*='chat-content']",
                    ".chat-content",
                ]

                message_container = None
                for selector in message_container_selectors:
                    try:
                        containers = self.browser.find_elements(selector)
                        if containers:
                            message_container = containers[0]
                            logger.debug(f"找到消息容器: {selector}")
                            break
                    except Exception:
                        continue

                # 滚动到顶部加载历史消息
                if message_container:
                    for _ in range(3):  # 滚动3次尝试加载更多历史消息
                        self.browser.driver.execute_script(
                            "arguments[0].scrollTop = 0;",
                            message_container
                        )
                        time.sleep(1)
                    logger.debug("✓ 完成历史消息滚动加载")
            except Exception as e:
                logger.debug(f"滚动加载历史消息失败: {str(e)}")

            # 获取所有消息元素
            logger.debug("获取消息元素...")
            message_elements = []

            # 尝试多个可能的消息选择器
            message_selectors = [
                ".message-item",
                ".chat-message",
                "[class*='message-item']",
                "[class*='chat-message']",
                ".message",
                "[class*='message']",
            ]

            for selector in message_selectors:
                try:
                    elements = self.browser.find_elements(selector)
                    if elements:
                        # 过滤掉非消息元素（如系统提示等）
                        message_elements = [
                            elem for elem in elements
                            if elem.is_displayed()
                        ]
                        if message_elements:
                            logger.debug(f"使用选择器 '{selector}' 找到 {len(message_elements)} 个消息元素")
                            break
                except Exception as e:
                    logger.debug(f"选择器 '{selector}' 查找失败: {str(e)}")
                    continue

            if not message_elements:
                logger.warning(f"未找到联系人 {contact_id} 的任何消息")
                self.browser.driver.switch_to.default_content()
                return []

            # 限制消息数量
            if len(message_elements) > max_messages:
                logger.debug(
                    f"消息数量 ({len(message_elements)}) 超过限制 ({max_messages})，只获取最新的 {max_messages} 条")
                message_elements = message_elements[-max_messages:]

            # 解析每个消息元素
            messages = []
            logger.debug(f"开始解析 {len(message_elements)} 条消息...")

            for idx, element in enumerate(message_elements):
                try:
                    message = self._parse_chat_message_element(element, contact_id)
                    messages.append(message)
                    logger.debug(f"  [{idx + 1}/{len(message_elements)}] 解析成功: {message.content[:30]}...")
                except Exception as e:
                    logger.warning(f"  [{idx + 1}/{len(message_elements)}] 解析失败: {str(e)}")
                    continue

            logger.info(f"✓ 成功获取 {len(messages)} 条聊天消息")

            # 切换回主文档
            self.browser.driver.switch_to.default_content()

            return messages

        except Exception as e:
            error_msg = f"获取聊天消息失败: {str(e)}"
            logger.error(error_msg)

            # 确保切换回主文档
            try:
                self.browser.driver.switch_to.default_content()
            except Exception:
                pass

            raise MessageException(error_msg) from e

    def _parse_chat_message_element(self, element: WebElement, contact_id: str) -> Message:
        """解析聊天消息元素（内部方法）。
        
        从聊天记录的消息元素中提取消息信息。
        与 parse_message_element 类似，但针对聊天记录的DOM结构优化。
        
        Args:
            element: 消息DOM元素
            contact_id: 当前聊天的联系人ID
            
        Returns:
            解析后的Message对象
            
        Raises:
            MessageException: 当解析失败时抛出
        """
        try:
            # 生成消息ID
            message_id = element.get_attribute("data-message-id")
            if not message_id:
                # 使用元素的其他属性生成唯一ID
                message_id = f"{element.get_attribute('id') or ''}{element.text[:20]}{int(time.time() * 1000000)}"

            # 提取消息内容
            content = ""
            content_selectors = [
                ".message-content",
                ".msg-content",
                ".content",
                "[class*='content']",
                "[class*='text']",
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

            # 判断是否为发送的消息
            is_sent = False
            element_class = element.get_attribute("class") or ""

            # 通过CSS类名判断消息方向
            sent_keywords = ["sent", "self", "own", "outgoing", "right", "me"]
            received_keywords = ["received", "other", "incoming", "left"]

            element_class_lower = element_class.lower()
            if any(keyword in element_class_lower for keyword in sent_keywords):
                is_sent = True
            elif any(keyword in element_class_lower for keyword in received_keywords):
                is_sent = False
            else:
                # 如果无法从类名判断，尝试通过元素位置判断
                try:
                    # 检查元素的对齐方式
                    text_align = element.value_of_css_property("text-align")
                    float_prop = element.value_of_css_property("float")

                    if text_align == "right" or float_prop == "right":
                        is_sent = True
                except Exception:
                    pass

            # 提取发送者信息
            if is_sent:
                # 发送的消息，发送者是当前用户
                contact_name = "我"
                sender_id = "self"
            else:
                # 接收的消息，发送者是联系人
                contact_name = contact_id
                sender_id = contact_id

                # 尝试从元素中提取发送者名称
                sender_selectors = [
                    ".sender-name",
                    ".user-name",
                    ".name",
                    "[class*='sender']",
                    "[class*='username']",
                    "[class*='name']",
                ]

                for selector in sender_selectors:
                    try:
                        sender_element = element.find_element("css selector", selector)
                        sender_name = sender_element.text.strip()
                        if sender_name:
                            contact_name = sender_name
                            break
                    except NoSuchElementException:
                        continue

            # 提取时间戳
            timestamp = datetime.now()
            time_selectors = [
                ".message-time",
                ".msg-time",
                ".time",
                "[class*='time']",
                "[class*='timestamp']",
            ]

            for selector in time_selectors:
                try:
                    time_element = element.find_element("css selector", selector)
                    time_text = time_element.text.strip()
                    if time_text:
                        # 这里简化处理，实际应用中需要解析时间字符串
                        # 例如: "10:30", "昨天 15:20" 等格式
                        logger.debug(f"消息时间文本: {time_text}")
                        # TODO: 实现时间字符串解析
                        break
                except NoSuchElementException:
                    continue

            # 判断消息类型
            message_type = "text"
            try:
                if element.find_elements("css selector", "img, [class*='image']"):
                    message_type = "image"
                elif "系统消息" in content or "system" in element_class_lower:
                    message_type = "system"
            except Exception:
                pass

            message = Message(
                message_id=message_id,
                contact_id=sender_id,
                contact_name=contact_name,
                content=content,
                message_type=message_type,
                timestamp=timestamp,
                is_sent=is_sent,
            )

            return message

        except Exception as e:
            error_msg = f"解析聊天消息元素失败: {str(e)}"
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
        修复了iframe切换和输入框定位问题。
        
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
        # 尝试发送消息，包含重试机制
        for attempt in range(retry_times + 1):
            try:
                if attempt > 0:
                    logger.warning(f"第 {attempt} 次重试发送消息...")
                    time.sleep(retry_delay)

                iframe_switched = False
                self.browser.driver.switch_to.default_content()

                iframe_selector = "iframe[src*='def_cbu_web_im_core']"

                chat_iframe = self.browser.wait_for_element(iframe_selector, timeout=5)

                if chat_iframe:
                    self.browser.driver.switch_to.frame(chat_iframe)
                    iframe_switched = True
                else:
                    logger.warning("未找到聊天iframe，尝试在主文档中查找输入框")

                if not iframe_switched:
                    logger.error("未能切换到聊天iframe，消息发送可能失败")
                    self.browser.driver.switch_to.default_content()

                logger.debug("切换到目标联系人...")
                if not self.switch_to_chat(contact_id):
                    logger.warning(f"无法切换到联系人 {contact_id} 的聊天窗口")
                    # if attempt == 0:
                    # logger.info("尝试调试联系人列表结构...")
                    # self.debug_contact_list()
                else:
                    logger.info(f"✓ 已切换到联系人 {contact_id}")

                time.sleep(1)

                # 检测并处理滑动验证码
                if self.captcha_handler.detect_slider_captcha():
                    logger.warning("检测到滑动验证码，开始处理...")
                    if not self.captcha_handler.handle_slider_captcha():
                        logger.error("滑动验证码处理失败")
                        if attempt < retry_times:
                            continue
                        else:
                            self.browser.driver.switch_to.default_content()
                            raise MessageException("滑动验证码处理失败，无法发送消息")
                    logger.info("✓ 滑动验证码处理成功")
                    time.sleep(1)

                input_selectors = [
                    "[contenteditable='true']",
                    "input[type='text']",
                ]

                # 搜索框关键字（用于排除）
                search_keywords = ["搜索", "联系人", "你好", "在吗", "search", "contact"]

                input_element = None
                for selector in input_selectors:
                    try:
                        elements = self.browser.find_elements(selector)

                        for idx, elem in enumerate(elements):
                            try:
                                is_displayed = elem.is_displayed()
                                is_enabled = elem.is_enabled()
                                placeholder = elem.get_attribute("placeholder") or ""

                                is_search_box = any(kw in placeholder for kw in search_keywords)
                                if is_search_box:
                                    continue

                                # 优先选择明确的消息输入框
                                if is_displayed and is_enabled:
                                    if "请输入消息" in placeholder or (
                                            "Enter" in placeholder and "发送" in placeholder):
                                        input_element = elem
                                        break
                                    elif not input_element:
                                        # 暂存作为候选
                                        input_element = elem

                            except Exception as e:
                                logger.debug(f"  元素[{idx}] 检查失败: {e}")
                                continue

                        # 如果找到了明确的消息输入框，停止搜索
                        if input_element:
                            ph = input_element.get_attribute("placeholder") or ""
                            if "请输入消息" in ph:
                                logger.info("✓ 确认找到消息输入框，停止搜索")
                                break
                    except Exception:
                        continue
                    try:
                        all_inputs = self.browser.find_elements("input")
                        all_textareas = self.browser.find_elements("textarea")
                        all_contenteditable = self.browser.find_elements("[contenteditable='true']")

                        for i, elem in enumerate(all_inputs + all_textareas + all_contenteditable):
                            try:
                                ph = elem.get_attribute("placeholder") or ""
                                cls = elem.get_attribute("class") or ""
                                vis = elem.is_displayed()
                                ena = elem.is_enabled()
                                if vis and ena:
                                    # 排除搜索框
                                    if not any(kw in ph for kw in search_keywords) and not any(
                                            kw in cls.lower() for kw in ["search"]):
                                        input_element = elem
                                        break
                            except Exception as e:
                                logger.debug(f"  [{i}] 检查失败: {e}")
                                continue
                    except Exception as e:
                        logger.error(f"重试失败: {e}")

                    if not input_element:
                        self.browser.driver.switch_to.default_content()
                        raise MessageException("未找到消息输入框，请查看日志中的调试信息")

                # 获取输入框类型
                is_contenteditable = input_element.get_attribute("contenteditable") == "true"

                if is_contenteditable:
                    self.browser.driver.execute_script("arguments[0].innerHTML = '';", input_element)
                    self.browser.driver.execute_script("arguments[0].textContent = '';", input_element)
                else:
                    input_element.clear()

                time.sleep(1)

                try:
                    input_element.click()  # 先点击获得焦点
                    time.sleep(0.3)
                    input_element.send_keys(content)

                    # 验证内容是否输入成功
                    time.sleep(0.5)
                    if is_contenteditable:
                        current_value = input_element.text or input_element.get_attribute("textContent") or ""
                    else:
                        current_value = input_element.get_attribute("value") or ""

                    logger.debug(f"输入后的内容: {current_value[:50]}...")

                    if content in current_value or current_value.strip():
                        input_success = True
                        logger.debug("✓ 方式1 (send_keys) 输入成功")
                except Exception as e:
                    logger.warning(f"(send_keys) 输入失败: {str(e)}")

                # 定位并点击发送按钮
                send_button_selectors = [
                    "button[class*='send']",
                    ".send-button",
                    "[class*='btn-send']",
                    "button[type='submit']",
                    "span[class*='send']",
                    "div[class*='send']",
                ]

                send_button = None
                for selector in send_button_selectors:
                    elements = self.browser.find_elements(selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            send_button = elem
                            break

                    if send_button:
                        break
                if not send_button:
                    from selenium.webdriver.common.keys import Keys
                    input_element.send_keys(Keys.RETURN)
                else:
                    send_button.click()

                # 等待一下，检查是否出现验证码
                time.sleep(1)

                # 检测并处理发送后可能出现的验证码
                if self.captcha_handler.detect_slider_captcha():
                    logger.warning("发送消息后出现滑动验证码，开始处理...")
                    if not self.captcha_handler.handle_slider_captcha():
                        logger.error("滑动验证码处理失败")
                        if attempt < retry_times:
                            self.browser.driver.switch_to.default_content()
                            continue
                        else:
                            self.browser.driver.switch_to.default_content()
                            raise MessageException("滑动验证码处理失败，消息可能未发送成功")
                    logger.info("✓ 滑动验证码处理成功")
                    time.sleep(1)

                logger.info(f"✓ 消息发送成功: {content[:50]}...")

                self.browser.driver.switch_to.default_content()

                return True

            except Exception as e:
                self.browser.driver.switch_to.default_content()
                if attempt >= retry_times:
                    error_msg = f"发送消息失败，已重试 {retry_times} 次: {str(e)}"
                    logger.error(error_msg)
                    raise MessageException(error_msg) from e

        return False

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
            logger.info(f"切换到联系人聊天窗口: {contact_id}")

            # 等待页面加载完成 - 旺旺是SPA应用，需要等待
            logger.debug("等待联系人列表加载...")
            time.sleep(3)  # 增加等待时间，确保页面完全加载

            # 首先尝试切换到iframe（如果存在）
            logger.debug("检查是否需要切换到iframe...")
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
            except Exception as e:
                logger.debug(f"切换iframe失败或不需要切换: {str(e)}")

            # 策略1: 使用更精确的 XPath 直接定位
            # 实际DOM: <div class="conversation-item"><div class="content"><div class="conversation"><div class="name">富友1688</div></div></div></div>
            logger.debug(f"策略1: 使用精确XPath直接定位联系人")
            try:
                # 使用 XPath 查找包含指定文本的 .name 元素，然后找到其祖先 .conversation-item
                xpath = f"//div[@class='conversation-item']//div[@class='name' and normalize-space(text())='{contact_id}']"

                # 等待元素出现
                max_wait = 15  # 增加等待时间
                wait_interval = 1
                name_elements = []

                for i in range(max_wait):
                    name_elements = self.browser.find_elements(xpath, by="xpath")
                    if name_elements:
                        logger.debug(f"找到 {len(name_elements)} 个匹配的联系人")
                        break
                    logger.debug(f"等待联系人元素出现... ({i + 1}/{max_wait})")
                    time.sleep(wait_interval)

                if name_elements:
                    # 找到 .name 元素的祖先 .conversation-item 并点击
                    name_element = name_elements[0]
                    # 使用 XPath 向上查找 .conversation-item
                    conversation_item = name_element.find_element("xpath",
                                                                  "./ancestor::div[@class='conversation-item' or contains(@class, 'conversation-item')]")

                    logger.info(f"✓ 找到联系人元素: {contact_id}")

                    # 滚动到元素可见
                    self.browser.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});",
                                                       conversation_item)
                    time.sleep(0.5)

                    # 点击会话项
                    conversation_item.click()
                    logger.info(f"✓ 成功切换到联系人 {contact_id}")
                    time.sleep(1)
                    return True
                else:
                    logger.warning(f"未找到联系人: {contact_id}")

            except Exception as e:
                logger.debug(f"策略1失败: {str(e)}")

            # 策略2: 遍历所有 conversation-item 查找匹配的联系人
            logger.debug(f"策略2: 遍历所有会话项查找联系人")
            try:
                conversation_items = self.browser.find_elements(".conversation-item")

                if conversation_items:
                    logger.debug(f"找到 {len(conversation_items)} 个会话项，开始遍历...")

                    for idx, item in enumerate(conversation_items):
                        try:
                            # 使用 XPath 在当前 item 下查找 .name 元素
                            name_element = item.find_element("xpath", ".//div[@class='name']")
                            name_text = name_element.text.strip()

                            logger.debug(f"  [{idx + 1}] 联系人: {name_text}")

                            if name_text == contact_id:
                                logger.info(f"✓ 找到匹配的联系人: {name_text}")

                                # 滚动到元素可见
                                self.browser.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});",
                                                                   item)
                                time.sleep(0.5)

                                # 点击整个会话项
                                item.click()
                                logger.info(f"✓ 成功切换到联系人 {contact_id}")
                                time.sleep(1)
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

            except Exception as e:
                logger.debug(f"策略2失败: {str(e)}")

            # 策略3: 通过 ID 属性查找（根据你提供的 DOM，ID 包含联系人信息）
            logger.debug(f"策略3: 通过 ID 属性查找")
            try:
                # 你的 DOM 显示 id="2847488761.1-2081385427.1#11152@cntaobao"
                # 尝试通过 ID 包含联系人名称来查找
                all_items = self.browser.find_elements(".conversation-item")

                for item in all_items:
                    try:
                        item_id = item.get_attribute("id")
                        if item_id:
                            logger.debug(f"检查会话项 ID: {item_id}")
                            # 检查 ID 中是否包含联系人信息
                            # 或者直接点击并检查内容
                            name_element = item.find_element("xpath", ".//div[@class='name']")
                            name_text = name_element.text.strip()

                            if name_text == contact_id:
                                logger.info(f"✓ 通过 ID 属性找到联系人: {name_text} (ID: {item_id})")

                                # 滚动到元素可见
                                self.browser.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});",
                                                                   item)
                                time.sleep(0.5)

                                item.click()
                                logger.info(f"✓ 成功切换到联系人 {contact_id}")
                                time.sleep(1)
                                return True
                    except Exception as e:
                        continue

            except Exception as e:
                logger.debug(f"策略3失败: {str(e)}")

            # 策略4: 通过部分文本匹配（模糊匹配）
            logger.debug(f"策略4: 通过部分文本匹配查找")
            try:
                xpath = f"//div[@class='name' and contains(text(), '{contact_id}')]"
                name_elements = self.browser.find_elements(xpath, by="xpath")

                if name_elements:
                    logger.debug(f"找到 {len(name_elements)} 个部分匹配的元素")
                    name_element = name_elements[0]
                    conversation_item = name_element.find_element("xpath",
                                                                  "./ancestor::div[@class='conversation-item' or contains(@class, 'conversation-item')]")

                    # 滚动到元素可见
                    self.browser.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});",
                                                       conversation_item)
                    time.sleep(0.5)

                    conversation_item.click()
                    logger.info(f"✓ 通过部分匹配成功切换到联系人")
                    time.sleep(1)
                    return True
            except Exception as e:
                logger.debug(f"策略4失败: {str(e)}")

            # 策略5: 尝试通过data属性定位联系人（兼容其他可能的DOM结构）
            logger.debug(f"策略5: 通过data属性查找")
            data_selectors = [
                f"[data-contact-id='{contact_id}']",
                f"[data-user-id='{contact_id}']",
                f"[data-id='{contact_id}']",
                f"[data-userid='{contact_id}']",
                f"[data-nick='{contact_id}']",
            ]

            for selector in data_selectors:
                try:
                    contact_element = self.browser.wait_for_element(selector, timeout=2)

                    # 滚动到元素可见
                    self.browser.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});",
                                                       contact_element)
                    time.sleep(0.5)

                    contact_element.click()
                    logger.info(f"✓ 通过选择器 '{selector}' 成功切换到联系人")
                    time.sleep(1)
                    return True
                except Exception:
                    continue

            # 策略6: 通过通用选择器和文本匹配
            logger.debug(f"策略6: 通过通用选择器查找")
            generic_selectors = [
                ".contact-item",
                ".contact-list-item",
                ".user-item",
                "[class*='conversation']",
                "[class*='contact']",
                "li[class*='item']",
            ]

            for selector in generic_selectors:
                try:
                    elements = self.browser.find_elements(selector)
                    if not elements:
                        continue

                    logger.debug(f"找到 {len(elements)} 个元素 (选择器: {selector})")

                    for element in elements:
                        try:
                            element_text = element.text.strip()
                            if contact_id in element_text:
                                logger.debug(f"找到匹配的元素，文本: {element_text[:50]}")
                                element.click()
                                logger.info(f"✓ 通过通用选择器成功切换到联系人")
                                time.sleep(1)
                                return True
                        except (StaleElementReferenceException, Exception):
                            continue

                except Exception:
                    continue

            # 所有策略都失败
            logger.warning(f"✗ 无法找到联系人 {contact_id}，所有查找策略均失败")
            logger.info("提示: 请确保联系人在当前页面可见，或者检查联系人ID/名称是否正确")

            # 切换回主文档
            try:
                self.browser.driver.switch_to.default_content()
            except Exception:
                pass

            return False

        except Exception as e:
            error_msg = f"切换到聊天窗口失败: {str(e)}"
            logger.error(error_msg)

            # 确保切换回主文档
            try:
                self.browser.driver.switch_to.default_content()
            except Exception:
                pass

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
                logger.debug(f"消息数量 ({len(message_elements)}) 超过限制 ({max_messages})，只获取最新的 {max_messages} 条")
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
                is_auto_reply=False,
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
        logger.info(f"准备发送消息到联系人 {contact_id}: {content[:50]}...")

        # 尝试发送消息，包含重试机制
        for attempt in range(retry_times + 1):
            try:
                if attempt > 0:
                    logger.warning(f"第 {attempt} 次重试发送消息...")
                    time.sleep(retry_delay)

                # 关键修复：先切换到聊天iframe
                logger.debug("步骤1: 切换到聊天iframe...")
                iframe_switched = False
                try:
                    # 先切换回主文档
                    self.browser.driver.switch_to.default_content()
                    logger.debug("已切换回主文档")

                    # 查找聊天iframe - 根据DOM结构，使用精确选择器
                    iframe_selector = "iframe[src*='def_cbu_web_im_core']"
                    logger.debug(f"查找iframe: {iframe_selector}")
                    
                    chat_iframe = self.browser.wait_for_element(iframe_selector, timeout=5)

                    if chat_iframe:
                        iframe_src = chat_iframe.get_attribute("src")
                        logger.debug(f"找到聊天iframe: {iframe_src}")
                        
                        self.browser.driver.switch_to.frame(chat_iframe)
                        iframe_switched = True
                        logger.info("✓ 成功切换到聊天iframe")
                        time.sleep(2)  # 等待iframe内容加载
                        
                        # 验证是否真的切换成功
                        try:
                            current_url = self.browser.driver.execute_script("return window.location.href;")
                            logger.debug(f"当前iframe URL: {current_url}")
                        except Exception as e:
                            logger.debug(f"无法获取iframe URL: {str(e)}")
                    else:
                        logger.warning("未找到聊天iframe，尝试在主文档中查找输入框")
                except Exception as e:
                    logger.warning(f"切换到iframe失败: {str(e)}，尝试在主文档中查找")
                    
                if not iframe_switched:
                    logger.error("未能切换到聊天iframe，消息发送可能失败")
                    # 切换回主文档
                    try:
                        self.browser.driver.switch_to.default_content()
                    except:
                        pass
                    raise MessageException("无法切换到聊天iframe")

                # 步骤2: 切换到目标联系人（这会加载聊天界面和输入框）
                logger.debug("步骤2: 切换到目标联系人...")
                if not self.switch_to_chat(contact_id):
                    logger.warning(f"无法切换到联系人 {contact_id} 的聊天窗口")
                    if attempt == 0:
                        logger.info("尝试调试联系人列表结构...")
                        self.debug_contact_list()
                else:
                    logger.info(f"✓ 已切换到联系人 {contact_id}")
                    # 等待聊天界面加载
                    time.sleep(2)

                # 步骤3: 定位输入框 - 精确定位消息输入框，排除搜索框
                logger.info("步骤3: 查找消息输入框...")
                
                # 搜索框特征：placeholder="搜索联系人"
                # 消息输入框特征：可能是 textarea、input 或 contenteditable div
                input_selectors = [
                    # 优先查找 textarea（最常见）
                    "textarea",
                    # contenteditable div（富文本编辑器）
                    "div[contenteditable='true']",
                    "div[contenteditable]",
                    "[contenteditable='true']",
                    # 匹配消息相关的 placeholder
                    "input[placeholder*='请输入']",
                    "textarea[placeholder*='请输入']",
                    "input[placeholder*='消息']",
                    "textarea[placeholder*='消息']",
                    "input[placeholder*='Enter']",
                    "textarea[placeholder*='Enter']",
                    # 通过 class 匹配
                    "textarea[class*='input']",
                    "div[class*='input'][contenteditable]",
                    "textarea[class*='message']",
                    "div[class*='message'][contenteditable]",
                    # 最后尝试所有 text input（会过滤）
                    "input[type='text']",
                ]
                
                # 搜索框关键字（用于排除）
                search_keywords = ["搜索", "联系人", "你好", "在吗", "search", "contact"]

                input_element = None
                for selector in input_selectors:
                    try:
                        elements = self.browser.find_elements(selector)
                        logger.debug(f"选择器 '{selector}' 找到 {len(elements)} 个元素")
                        
                        for idx, elem in enumerate(elements):
                            try:
                                is_displayed = elem.is_displayed()
                                is_enabled = elem.is_enabled()
                                tag_name = elem.tag_name
                                elem_class = elem.get_attribute("class") or ""
                                elem_id = elem.get_attribute("id") or ""
                                placeholder = elem.get_attribute("placeholder") or ""
                                
                                logger.debug(f"  元素[{idx}]: tag={tag_name}, placeholder='{placeholder[:50]}', displayed={is_displayed}, enabled={is_enabled}")
                                
                                # 排除搜索框
                                is_search_box = any(kw in placeholder for kw in search_keywords)
                                if is_search_box:
                                    logger.debug(f"  元素[{idx}] 是搜索框（placeholder包含搜索关键字），跳过")
                                    continue
                                
                                # 优先选择明确的消息输入框
                                if is_displayed and is_enabled:
                                    if "请输入消息" in placeholder or ("Enter" in placeholder and "发送" in placeholder):
                                        input_element = elem
                                        logger.info(f"✓ 找到消息输入框: placeholder='{placeholder}'")
                                        break
                                    elif not input_element:
                                        # 暂存作为候选
                                        input_element = elem
                                        logger.debug(f"  暂存元素[{idx}]作为候选")
                                        
                            except Exception as e:
                                logger.debug(f"  元素[{idx}] 检查失败: {str(e)}")
                                continue

                        # 如果找到了明确的消息输入框，停止搜索
                        if input_element:
                            ph = input_element.get_attribute("placeholder") or ""
                            if "请输入消息" in ph:
                                logger.info("✓ 确认找到消息输入框，停止搜索")
                                break
                    except Exception as e:
                        logger.debug(f"选择器 '{selector}' 查找失败: {str(e)}")
                        continue

                if not input_element:
                    logger.error("未找到任何可用的消息输入框")
                    # 详细调试：打印所有输入元素
                    try:
                        all_inputs = self.browser.find_elements("input")
                        all_textareas = self.browser.find_elements("textarea")
                        all_contenteditable = self.browser.find_elements("div[contenteditable='true']")
                        
                        logger.error(f"iframe内共有: {len(all_inputs)} 个 input, {len(all_textareas)} 个 textarea, {len(all_contenteditable)} 个 contenteditable")
                        
                        logger.error("=== 所有 input 元素详情 ===")
                        for i, inp in enumerate(all_inputs[:15]):
                            try:
                                ph = inp.get_attribute("placeholder") or ""
                                vis = inp.is_displayed()
                                enabled = inp.is_enabled()
                                inp_type = inp.get_attribute("type") or ""
                                inp_class = inp.get_attribute("class") or ""
                                logger.error(f"  input[{i}]: type='{inp_type}', placeholder='{ph}', class='{inp_class[:40]}', visible={vis}, enabled={enabled}")
                            except Exception as e:
                                logger.error(f"  input[{i}]: 无法获取信息 - {str(e)}")
                        
                        if all_textareas:
                            logger.error("=== 所有 textarea 元素详情 ===")
                            for i, ta in enumerate(all_textareas[:10]):
                                try:
                                    ph = ta.get_attribute("placeholder") or ""
                                    vis = ta.is_displayed()
                                    enabled = ta.is_enabled()
                                    ta_class = ta.get_attribute("class") or ""
                                    logger.error(f"  textarea[{i}]: placeholder='{ph}', class='{ta_class[:40]}', visible={vis}, enabled={enabled}")
                                except Exception as e:
                                    logger.error(f"  textarea[{i}]: 无法获取信息 - {str(e)}")
                        
                        if all_contenteditable:
                            logger.error("=== 所有 contenteditable 元素详情 ===")
                            for i, ce in enumerate(all_contenteditable[:10]):
                                try:
                                    vis = ce.is_displayed()
                                    enabled = ce.is_enabled()
                                    ce_class = ce.get_attribute("class") or ""
                                    logger.error(f"  contenteditable[{i}]: class='{ce_class[:40]}', visible={vis}, enabled={enabled}")
                                except Exception as e:
                                    logger.error(f"  contenteditable[{i}]: 无法获取信息 - {str(e)}")
                    except Exception as e:
                        logger.error(f"调试信息获取失败: {str(e)}")
                    
                    
                    # 尝试等待更长时间后再次查找
                    logger.warning("未找到输入框，等待5秒后重试...")
                    time.sleep(5)
                    
                    # 重试：查找所有可能的输入元素
                    try:
                        logger.info("重试：查找所有输入元素...")
                        all_inputs = self.browser.find_elements("input")
                        all_textareas = self.browser.find_elements("textarea")
                        all_contenteditable = self.browser.find_elements("[contenteditable='true']")
                        
                        logger.info(f"重试发现: {len(all_inputs)} 个 input, {len(all_textareas)} 个 textarea, {len(all_contenteditable)} 个 contenteditable")
                        
                        # 打印所有元素详情
                        for i, elem in enumerate(all_inputs + all_textareas + all_contenteditable):
                            try:
                                tag = elem.tag_name
                                ph = elem.get_attribute("placeholder") or ""
                                cls = elem.get_attribute("class") or ""
                                vis = elem.is_displayed()
                                ena = elem.is_enabled()
                                logger.info(f"  [{i}] {tag}: placeholder='{ph}', class='{cls[:30]}', visible={vis}, enabled={ena}")
                                
                                # 尝试使用这个元素
                                if vis and ena:
                                    # 排除搜索框
                                    if not any(kw in ph for kw in search_keywords) and not any(kw in cls.lower() for kw in ["search"]):
                                        input_element = elem
                                        logger.info(f"✓ 重试成功，使用元素[{i}]: {tag}, placeholder='{ph}'")
                                        break
                            except Exception as e:
                                logger.debug(f"  [{i}] 检查失败: {str(e)}")
                                continue
                    except Exception as e:
                        logger.error(f"重试失败: {str(e)}")
                    
                    if not input_element:
                        # 切换回主文档
                        self.browser.driver.switch_to.default_content()
                        raise MessageException("未找到消息输入框，请查看日志中的调试信息")

                # 清空输入框并输入消息内容
                logger.debug("清空输入框...")
                
                # 获取输入框类型
                tag_name = input_element.tag_name.lower()
                is_contenteditable = input_element.get_attribute("contenteditable") == "true"
                
                logger.debug(f"输入框类型: {tag_name}, contenteditable: {is_contenteditable}")
                
                # 清空输入框
                try:
                    if is_contenteditable:
                        # contenteditable元素使用JavaScript清空
                        self.browser.driver.execute_script("arguments[0].innerHTML = '';", input_element)
                        self.browser.driver.execute_script("arguments[0].textContent = '';", input_element)
                    else:
                        # 普通输入框使用clear()
                        input_element.clear()
                except Exception as e:
                    logger.warning(f"清空输入框失败: {str(e)}")

                time.sleep(0.3)

                logger.debug(f"输入消息内容: {content[:50]}...")
                
                # 尝试多种输入方式
                input_success = False
                
                # 方式1: 使用 send_keys
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
                    logger.warning(f"方式1 (send_keys) 输入失败: {str(e)}")
                
                # 方式2: 如果方式1失败，使用JavaScript直接设置值
                if not input_success:
                    try:
                        logger.debug("尝试方式2: 使用JavaScript设置内容")
                        if is_contenteditable:
                            # contenteditable使用innerHTML或textContent
                            self.browser.driver.execute_script(
                                "arguments[0].textContent = arguments[1];", 
                                input_element, 
                                content
                            )
                            # 触发input事件
                            self.browser.driver.execute_script(
                                "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                                input_element
                            )
                        else:
                            # 普通输入框使用value
                            self.browser.driver.execute_script(
                                "arguments[0].value = arguments[1];", 
                                input_element, 
                                content
                            )
                            # 触发input和change事件
                            self.browser.driver.execute_script(
                                "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));"
                                "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                                input_element
                            )
                        
                        # 验证内容
                        time.sleep(0.5)
                        if is_contenteditable:
                            current_value = input_element.text or input_element.get_attribute("textContent") or ""
                        else:
                            current_value = input_element.get_attribute("value") or ""
                        
                        logger.debug(f"JavaScript设置后的内容: {current_value[:50]}...")
                        
                        if content in current_value or current_value.strip():
                            input_success = True
                            logger.debug("✓ 方式2 (JavaScript) 输入成功")
                    except Exception as e:
                        logger.warning(f"方式2 (JavaScript) 输入失败: {str(e)}")
                
                # 方式3: 如果前两种方式都失败，尝试组合方式
                if not input_success:
                    try:
                        logger.debug("尝试方式3: 组合方式（点击+聚焦+JavaScript+事件）")
                        # 先点击并聚焦
                        input_element.click()
                        time.sleep(0.2)
                        
                        # 使用JavaScript设置焦点
                        self.browser.driver.execute_script("arguments[0].focus();", input_element)
                        time.sleep(0.2)
                        
                        # 使用JavaScript设置值
                        if is_contenteditable:
                            self.browser.driver.execute_script(
                                "arguments[0].innerHTML = arguments[1];"
                                "arguments[0].textContent = arguments[1];",
                                input_element,
                                content
                            )
                        else:
                            self.browser.driver.execute_script(
                                "arguments[0].value = arguments[1];",
                                input_element,
                                content
                            )
                        
                        # 触发多个事件确保框架检测到变化
                        self.browser.driver.execute_script("""
                            var element = arguments[0];
                            element.dispatchEvent(new Event('focus', { bubbles: true }));
                            element.dispatchEvent(new Event('input', { bubbles: true }));
                            element.dispatchEvent(new Event('change', { bubbles: true }));
                            element.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true }));
                            element.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
                        """, input_element)
                        
                        # 验证内容
                        time.sleep(0.5)
                        if is_contenteditable:
                            current_value = input_element.text or input_element.get_attribute("textContent") or ""
                        else:
                            current_value = input_element.get_attribute("value") or ""
                        
                        logger.debug(f"组合方式设置后的内容: {current_value[:50]}...")
                        
                        if content in current_value or current_value.strip():
                            input_success = True
                            logger.debug("✓ 方式3 (组合方式) 输入成功")
                    except Exception as e:
                        logger.warning(f"方式3 (组合方式) 输入失败: {str(e)}")
                
                if not input_success:
                    logger.error("所有输入方式都失败，内容可能为空")
                    # 切换回主文档
                    self.browser.driver.switch_to.default_content()
                    raise MessageException("无法输入消息内容到输入框")

                logger.debug("消息内容已成功输入")

                # 等待更长时间确保内容输入完成并被框架识别
                time.sleep(1)

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
                    try:
                        elements = self.browser.find_elements(selector)
                        for elem in elements:
                            try:
                                if elem.is_displayed() and elem.is_enabled():
                                    send_button = elem
                                    logger.debug(f"找到发送按钮: {selector}")
                                    break
                            except:
                                continue

                        if send_button:
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
                    logger.debug("点击发送按钮...")
                    send_button.click()

                logger.info(f"✓ 消息发送成功: {content[:50]}...")

                # 等待消息发送完成
                time.sleep(1)

                # 切换回主文档
                self.browser.driver.switch_to.default_content()

                return True

            except Exception as e:
                logger.warning(f"发送消息失败 (尝试 {attempt + 1}/{retry_times + 1}): {str(e)}")

                # 确保切换回主文档
                try:
                    self.browser.driver.switch_to.default_content()
                except Exception:
                    pass

                # 如果是最后一次尝试，抛出异常
                if attempt >= retry_times:
                    error_msg = f"发送消息失败，已重试 {retry_times} 次: {str(e)}"
                    logger.error(error_msg)
                    raise MessageException(error_msg) from e

        return False

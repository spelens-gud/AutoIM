"""验证码处理模块。

处理各种类型的验证码，包括滑动验证、图片验证等。
"""

import time
import random
from typing import Optional

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from src.utils.logger import get_logger
from src.utils.exceptions import BrowserException

logger = get_logger(__name__)


class CaptchaHandler:
    """验证码处理器类。
    
    提供各种验证码的识别和处理功能。
    
    Attributes:
        browser: 浏览器控制器实例
    """

    def __init__(self, browser):
        """初始化验证码处理器。
        
        Args:
            browser: BrowserController实例
        """
        self.browser = browser
        logger.info("验证码处理器初始化完成")

    def detect_slider_captcha(self, check_iframes: bool = True) -> bool:
        """检测是否出现滑动验证码。
        
        Args:
            check_iframes: 是否检查iframe中的验证码，默认True
        
        Returns:
            True表示检测到滑动验证码，False表示未检测到
        """
        try:
            captcha_selectors = [
                # 通用滑动验证码
                ".nc_wrapper",  # 阿里系滑动验证
                ".nc-container",
                "[class*='slider']",
                "[class*='captcha']",
                "div[class*='nc']",  # 更宽泛的nc相关元素
                "span[class*='nc']",
                # 文本特征
                "//div[contains(text(), '请拖动下方滑块')]",
                "//div[contains(text(), '拖动到最右边')]",
                "//div[contains(text(), '滑动验证')]",
                "//span[contains(text(), '请按住滑块')]",
                "//div[contains(@class, 'nc')]",
            ]

            # 先在当前上下文中检测
            for selector in captcha_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.browser.find_elements(selector, by="xpath")
                    else:
                        elements = self.browser.find_elements(selector)

                    if elements:
                        visible_elements = [elem for elem in elements if elem.is_displayed()]
                        if visible_elements:
                            logger.info(f"✓ 检测到滑动验证码: {selector} (找到 {len(visible_elements)} 个可见元素)")
                            try:
                                first_elem = visible_elements[0]
                                elem_class = first_elem.get_attribute('class') or ''
                                elem_id = first_elem.get_attribute('id') or ''
                                logger.debug(f"验证码元素详情: class='{elem_class}', id='{elem_id}'")
                            except Exception:
                                pass
                            return True
                except Exception as e:
                    logger.debug(f"选择器 {selector} 检测失败: {str(e)}")
                    continue

            # 如果当前上下文没找到，且允许检查iframe，则递归检查所有iframe
            if check_iframes:
                logger.debug("当前上下文未找到验证码，开始检查iframe...")
                if self._detect_captcha_in_iframes():
                    return True

            logger.debug("未检测到滑动验证码")
            return False

        except Exception as e:
            logger.debug(f"检测滑动验证码时出错: {str(e)}")
            return False

    def _detect_captcha_in_iframes(self, max_depth: int = 3, current_depth: int = 0) -> bool:
        """递归检测iframe中的验证码。
        
        Args:
            max_depth: 最大递归深度
            current_depth: 当前递归深度
            
        Returns:
            True表示在某个iframe中找到验证码，False表示未找到
        """
        if current_depth >= max_depth:
            return False
            
        try:
            # 保存当前上下文
            original_context = self.browser.driver.current_frame
            
            # 查找所有iframe
            iframes = self.browser.driver.find_elements("tag name", "iframe")
            logger.debug(f"在深度 {current_depth} 找到 {len(iframes)} 个iframe")
            
            for idx, iframe in enumerate(iframes):
                try:
                    # 切换到iframe
                    self.browser.driver.switch_to.frame(iframe)
                    logger.debug(f"切换到iframe {idx + 1}/{len(iframes)} (深度 {current_depth})")
                    
                    # 在当前iframe中检测验证码（不递归）
                    if self.detect_slider_captcha(check_iframes=False):
                        logger.info(f"✓ 在iframe {idx + 1} (深度 {current_depth}) 中找到验证码")
                        # 找到验证码后保持在这个iframe上下文中
                        return True
                    
                    # 递归检查嵌套的iframe
                    if self._detect_captcha_in_iframes(max_depth, current_depth + 1):
                        return True
                    
                    # 切回父级
                    self.browser.driver.switch_to.parent_frame()
                    
                except Exception as e:
                    logger.debug(f"检查iframe {idx + 1} 时出错: {str(e)}")
                    # 出错时尝试切回父级
                    try:
                        self.browser.driver.switch_to.parent_frame()
                    except Exception:
                        pass
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"检测iframe中的验证码时出错: {str(e)}")
            return False

    def handle_slider_captcha(self, max_attempts: int = 3) -> bool:
        """处理滑动验证码。
        
        模拟人类行为，将滑块拖动到正确位置。
        支持自动检测并切换到包含验证码的iframe。
        
        Args:
            max_attempts: 最大尝试次数，默认3次
            
        Returns:
            True表示验证成功，False表示验证失败
        """
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    logger.info(f"第 {attempt + 1} 次尝试处理滑动验证码...")
                    time.sleep(1)
                else:
                    logger.info("开始处理滑动验证码...")

                # 切换到默认内容（主页面）
                self.browser.driver.switch_to.default_content()
                
                # 查找并切换到包含验证码的iframe
                captcha_found = self._switch_to_captcha_iframe()
                if not captcha_found:
                    logger.warning("未找到包含验证码的iframe")
                    # 尝试在主页面处理
                    pass

                # 关闭可能存在的多余验证码窗口
                self._close_duplicate_captcha_windows()
                
                # 等待验证码加载
                time.sleep(1)

                # 查找滑块元素
                slider = self._find_slider_element()
                if not slider:
                    logger.warning("未找到滑块元素")
                    # 切回主页面
                    self.browser.driver.switch_to.default_content()
                    continue

                # 获取滑块和滑轨信息
                slider_width = slider.size['width']
                slider_height = slider.size['height']
                logger.debug(f"滑块尺寸: {slider_width}x{slider_height}")

                # 查找滑轨
                track = self._find_track_element()
                if track:
                    track_width = track.size['width']
                    logger.debug(f"滑轨宽度: {track_width}")
                    # 计算需要移动的距离（滑轨宽度 - 滑块宽度）
                    distance = track_width - slider_width
                else:
                    # 如果找不到滑轨，使用默认距离
                    distance = 300
                    logger.debug(f"未找到滑轨，使用默认距离: {distance}")

                # 执行滑动
                success = self._perform_slide(slider, distance)

                if success:
                    # 等待验证结果
                    time.sleep(1)

                    # 检查是否验证成功（在当前iframe上下文中）
                    if not self.detect_slider_captcha(check_iframes=False):
                        logger.info("✓ 滑动验证成功")
                        # 切回主页面
                        self.browser.driver.switch_to.default_content()
                        return True
                    else:
                        logger.warning("滑动验证失败，验证码仍然存在")

                # 切回主页面准备下次尝试
                self.browser.driver.switch_to.default_content()

            except Exception as e:
                logger.warning(f"处理滑动验证码时出错 (尝试 {attempt + 1}/{max_attempts}): {str(e)}")
                # 确保切回主页面
                try:
                    self.browser.driver.switch_to.default_content()
                except Exception:
                    pass
                continue

        logger.error(f"滑动验证失败，已尝试 {max_attempts} 次")
        # 确保最后切回主页面
        try:
            self.browser.driver.switch_to.default_content()
        except Exception:
            pass
        return False

    def _switch_to_captcha_iframe(self, max_depth: int = 3, current_depth: int = 0) -> bool:
        """切换到包含验证码的iframe。
        
        递归查找所有iframe，找到包含验证码的iframe后切换到该iframe。
        
        Args:
            max_depth: 最大递归深度
            current_depth: 当前递归深度
            
        Returns:
            True表示成功切换到包含验证码的iframe，False表示未找到
        """
        if current_depth >= max_depth:
            return False
            
        try:
            # 查找所有iframe
            iframes = self.browser.driver.find_elements("tag name", "iframe")
            logger.debug(f"在深度 {current_depth} 找到 {len(iframes)} 个iframe")
            
            for idx, iframe in enumerate(iframes):
                try:
                    # 切换到iframe
                    self.browser.driver.switch_to.frame(iframe)
                    logger.debug(f"检查iframe {idx + 1}/{len(iframes)} (深度 {current_depth})")
                    
                    # 在当前iframe中检测验证码
                    if self.detect_slider_captcha(check_iframes=False):
                        logger.info(f"✓ 在iframe {idx + 1} (深度 {current_depth}) 中找到验证码，已切换到该iframe")
                        return True
                    
                    # 递归检查嵌套的iframe
                    if self._switch_to_captcha_iframe(max_depth, current_depth + 1):
                        return True
                    
                    # 切回父级继续查找
                    self.browser.driver.switch_to.parent_frame()
                    
                except Exception as e:
                    logger.debug(f"检查iframe {idx + 1} 时出错: {str(e)}")
                    try:
                        self.browser.driver.switch_to.parent_frame()
                    except Exception:
                        pass
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"切换到验证码iframe时出错: {str(e)}")
            return False

    def _find_slider_element(self) -> Optional[WebElement]:
        """查找滑块元素。
        
        Returns:
            滑块元素，如果未找到则返回None
        """
        # 常见的滑块选择器
        slider_selectors = [
            ".nc_iconfont",  # 阿里系滑块图标
            ".nc-lang-cnt",
            "span.nc_iconfont",
            ".slidetounlock span",
            "[class*='slider-button']",
            "[class*='slide-button']",
            "[class*='slider-btn']",
            # 通过文本查找
            "//span[contains(@class, 'nc_iconfont')]",
            "//div[contains(@class, 'nc')]//span[contains(@class, 'btn_slide')]",
            "//span[contains(text(), '>>')]",
            "//div[contains(text(), '请按住滑块')]/..//span",
            # 更通用的选择器
            ".nc_wrapper span",
            ".nc-container span",
            "#nc_1_n1z",  # 阿里验证码的ID
        ]

        for selector in slider_selectors:
            try:
                if selector.startswith("//"):
                    elements = self.browser.find_elements(selector, by="xpath")
                else:
                    elements = self.browser.find_elements(selector)

                for elem in elements:
                    try:
                        if elem.is_displayed() and elem.is_enabled():
                            # 检查元素是否可交互
                            size = elem.size
                            if size['width'] > 0 and size['height'] > 0:
                                # 检查是否包含滑块特征
                                elem_class = elem.get_attribute('class') or ''
                                elem_id = elem.get_attribute('id') or ''
                                elem_text = elem.text or ''
                                
                                # 滑块通常包含这些特征
                                if ('nc_' in elem_class or 'nc_' in elem_id or 
                                    'slide' in elem_class.lower() or 
                                    '>>' in elem_text or
                                    'btn' in elem_class.lower()):
                                    logger.debug(f"找到滑块元素: {selector}, 尺寸: {size}, class: {elem_class}")
                                    return elem
                    except Exception:
                        continue
            except Exception as e:
                logger.debug(f"选择器 {selector} 查找失败: {str(e)}")
                continue

        # 如果上面都没找到，尝试通过父容器查找
        try:
            logger.debug("尝试通过父容器查找滑块...")
            nc_wrapper = self.browser.find_elements(".nc_wrapper")
            if nc_wrapper:
                # 在nc_wrapper内查找所有span
                spans = nc_wrapper[0].find_elements("css selector", "span")
                for span in spans:
                    try:
                        if span.is_displayed() and span.size['width'] > 20:
                            span_class = span.get_attribute('class') or ''
                            logger.debug(f"检查span: class={span_class}, size={span.size}")
                            # 查找可拖动的span
                            if 'nc_' in span_class or 'btn' in span_class.lower():
                                logger.debug(f"通过父容器找到滑块: {span_class}")
                                return span
                    except Exception:
                        continue
        except Exception as e:
            logger.debug(f"通过父容器查找失败: {str(e)}")

        return None

    def _find_track_element(self) -> Optional[WebElement]:
        """查找滑轨元素。
        
        Returns:
            滑轨元素，如果未找到则返回None
        """
        track_selectors = [
            ".nc_wrapper",
            ".nc-container",
            "[class*='slider-track']",
            "[class*='slide-track']",
            ".slidetounlock",
            "#nc_1__scale_text",  # 阿里验证码滑轨
            "[id*='nc_'][id*='scale_text']",
        ]

        for selector in track_selectors:
            try:
                elements = self.browser.find_elements(selector)
                for elem in elements:
                    if elem.is_displayed():
                        size = elem.size
                        logger.debug(f"找到滑轨元素: {selector}, 宽度: {size['width']}px")
                        return elem
            except Exception:
                continue

        return None

    def _perform_slide(self, slider: WebElement, distance: int) -> bool:
        """执行滑动操作。
        
        使用模拟人类行为的方式进行滑动，包括：
        - 非匀速移动
        - 随机停顿
        - 轻微抖动
        
        Args:
            slider: 滑块元素
            distance: 需要移动的距离（像素）
            
        Returns:
            True表示滑动执行成功，False表示失败
        """
        try:
            logger.info(f"开始滑动，目标距离: {distance}px")

            # 获取滑块初始位置
            start_location = slider.location
            logger.debug(f"滑块初始位置: {start_location}")

            # 创建动作链
            actions = ActionChains(self.browser.driver)

            # 移动到滑块中心（极速）
            actions.move_to_element(slider).perform()
            time.sleep(0.05)  # 固定延迟，不使用随机

            # 点击并按住滑块（极速）
            actions.click_and_hold(slider).perform()
            time.sleep(0.05)  # 固定延迟，不使用随机

            # 生成滑动轨迹
            tracks = self._generate_tracks(distance)
            logger.debug(f"生成轨迹点数: {len(tracks)}, 总距离: {sum(tracks)}px")

            # 按照轨迹移动（极速，几乎无延迟）
            for i, track in enumerate(tracks):
                try:
                    actions.move_by_offset(track, 0).perform()
                    # 不添加延迟，直接连续移动
                except Exception as e:
                    logger.debug(f"轨迹点 {i} 移动失败: {str(e)}")
                    continue

            # 不添加抖动，直接释放
            # 释放滑块
            time.sleep(0.05)  # 极短停顿
            actions.release().perform()
            time.sleep(0.3)  # 等待验证结果

            # 验证滑动距离
            try:
                end_location = slider.location
                actual_distance = end_location['x'] - start_location['x']
                logger.debug(f"滑块最终位置: {end_location}, 实际移动距离: {actual_distance}px")
                
                if actual_distance < distance * 0.8:
                    logger.warning(f"滑动距离不足: 目标{distance}px, 实际{actual_distance}px")
            except Exception as e:
                logger.debug(f"无法验证滑动距离: {str(e)}")

            logger.info("✓ 滑动操作执行完成")
            return True

        except Exception as e:
            logger.error(f"执行滑动操作失败: {str(e)}")
            # 尝试释放鼠标（防止卡住）
            try:
                ActionChains(self.browser.driver).release().perform()
            except Exception:
                pass
            return False

    def _generate_tracks(self, distance: int) -> list:
        """生成滑动轨迹。
        
        使用简化的轨迹生成，提升速度。
        
        Args:
            distance: 总距离
            
        Returns:
            轨迹列表，每个元素表示一次移动的距离
        """
        tracks = []
        current = 0
        
        # 使用更简单的轨迹：快速移动大部分距离，最后微调
        # 前90%快速移动
        fast_distance = int(distance * 0.9)
        # 后10%慢速微调
        slow_distance = distance - fast_distance
        
        # 快速阶段：大步移动
        step_size = 10  # 每次移动10px
        while current < fast_distance:
            move = min(step_size, fast_distance - current)
            if move > 0:
                tracks.append(move)
                current += move
        
        # 慢速阶段：小步微调
        step_size = 3  # 每次移动3px
        while current < distance:
            move = min(step_size, distance - current)
            if move > 0:
                tracks.append(move)
                current += move
        
        # 确保总距离达到目标
        total = sum(tracks)
        if total < distance:
            remaining = distance - total
            logger.debug(f"补充剩余距离: {remaining}px")
            tracks.append(remaining)
        
        logger.debug(f"生成轨迹: {len(tracks)}个点, 总距离: {sum(tracks)}px")
        return tracks

    def wait_for_captcha_disappear(self, timeout: int = 10) -> bool:
        """等待验证码消失。
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            True表示验证码已消失，False表示超时
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if not self.detect_slider_captcha():
                logger.info("验证码已消失")
                return True
            time.sleep(0.5)

        logger.warning(f"等待验证码消失超时 ({timeout}秒)")
        return False

    def _close_duplicate_captcha_windows(self) -> None:
        """关闭重复的验证码窗口。
        
        当页面上出现多个验证码窗口叠加时，关闭多余的窗口，
        只保留最上层的一个验证码窗口进行处理。
        """
        try:
            # 查找所有验证码容器
            captcha_containers = []
            container_selectors = [
                ".nc_wrapper",
                ".nc-container",
                "[class*='captcha']",
                "[id*='nc_']",
            ]
            
            for selector in container_selectors:
                try:
                    elements = self.browser.find_elements(selector)
                    for elem in elements:
                        if elem.is_displayed():
                            captcha_containers.append(elem)
                except Exception:
                    continue
            
            # 如果只有一个或没有验证码窗口，不需要处理
            if len(captcha_containers) <= 1:
                logger.debug(f"验证码窗口数量正常: {len(captcha_containers)}")
                return
            
            logger.warning(f"检测到 {len(captcha_containers)} 个验证码窗口，尝试关闭多余窗口...")
            
            # 按z-index排序，找出最上层的窗口
            containers_with_zindex = []
            for container in captcha_containers:
                try:
                    z_index = container.value_of_css_property("z-index")
                    # 将z-index转换为数字，如果是auto则设为0
                    z_value = 0
                    if z_index and z_index != "auto":
                        try:
                            z_value = int(z_index)
                        except ValueError:
                            z_value = 0
                    containers_with_zindex.append((container, z_value))
                except Exception:
                    containers_with_zindex.append((container, 0))
            
            # 按z-index降序排序
            containers_with_zindex.sort(key=lambda x: x[1], reverse=True)
            
            # 保留最上层的窗口，隐藏其他窗口
            for idx, (container, z_index) in enumerate(containers_with_zindex):
                if idx == 0:
                    # 保留第一个（最上层）
                    logger.debug(f"保留最上层验证码窗口 (z-index: {z_index})")
                    continue
                
                try:
                    # 隐藏多余的验证码窗口
                    self.browser.driver.execute_script(
                        "arguments[0].style.display = 'none';",
                        container
                    )
                    logger.debug(f"隐藏多余验证码窗口 {idx} (z-index: {z_index})")
                except Exception as e:
                    logger.debug(f"隐藏验证码窗口失败: {str(e)}")
            
            logger.info(f"✓ 已处理重复验证码窗口，保留1个，隐藏{len(captcha_containers)-1}个")
            
        except Exception as e:
            logger.debug(f"关闭重复验证码窗口时出错: {str(e)}")

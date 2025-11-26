"""自动回复引擎。

根据预设规则自动匹配消息内容并生成回复。
"""

import yaml
from pathlib import Path
from typing import List, Optional
from src.models.auto_reply_rule import AutoReplyRule
from src.utils.logger import get_logger
from src.utils.exceptions import ConfigException


logger = get_logger(__name__)


class AutoReplyEngine:
    """自动回复引擎类。
    
    负责加载、管理和匹配自动回复规则。
    
    Attributes:
        rules_file: 规则配置文件路径
        rules: 自动回复规则列表
    """
    
    def __init__(self, rules_file: str):
        """初始化自动回复引擎。
        
        Args:
            rules_file: 规则配置文件路径
        """
        self.rules_file = Path(rules_file)
        self.rules: List[AutoReplyRule] = []
        logger.info(f"初始化自动回复引擎，规则文件: {rules_file}")
    
    def load_rules(self) -> None:
        """从YAML文件加载自动回复规则。
        
        Raises:
            ConfigException: 当配置文件不存在或格式错误时
        """
        if not self.rules_file.exists():
            logger.warning(f"规则文件不存在: {self.rules_file}")
            raise ConfigException(f"规则文件不存在: {self.rules_file}")
        
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data or 'rules' not in data:
                logger.warning("规则文件格式错误，缺少 'rules' 字段")
                raise ConfigException("规则文件格式错误，缺少 'rules' 字段")
            
            self.rules.clear()
            for rule_data in data['rules']:
                try:
                    rule = AutoReplyRule(
                        keywords=rule_data.get('keywords', []),
                        reply=rule_data.get('reply', '')
                    )
                    self.rules.append(rule)
                except (ValueError, KeyError) as e:
                    logger.warning(f"跳过无效规则: {rule_data}, 错误: {e}")
                    continue
            
            logger.info(f"成功加载 {len(self.rules)} 条自动回复规则")
            
        except yaml.YAMLError as e:
            logger.error(f"解析YAML文件失败: {e}")
            raise ConfigException(f"解析YAML文件失败: {e}")
        except Exception as e:
            logger.error(f"加载规则文件失败: {e}")
            raise ConfigException(f"加载规则文件失败: {e}")
    
    def match_rule(self, message: str) -> Optional[str]:
        """根据消息内容匹配回复规则。
        
        使用简单的关键词匹配策略，按规则顺序匹配，返回第一个匹配的回复。
        
        Args:
            message: 消息内容
            
        Returns:
            匹配到的回复内容，如果没有匹配则返回None
        """
        if not message:
            return None
        
        message_lower = message.lower()
        
        for rule in self.rules:
            # 检查消息中是否包含任一关键词
            for keyword in rule.keywords:
                if keyword.lower() in message_lower:
                    logger.info(f"消息匹配规则，关键词: '{keyword}', 回复: '{rule.reply[:20]}...'")
                    return rule.reply
        
        logger.debug(f"消息未匹配任何规则: '{message[:50]}...'")
        return None
    
    def add_rule(self, keywords: List[str], reply: str) -> None:
        """动态添加新的回复规则。
        
        Args:
            keywords: 关键词列表
            reply: 回复内容
            
        Raises:
            ValueError: 当参数无效时
        """
        try:
            rule = AutoReplyRule(keywords=keywords, reply=reply)
            self.rules.append(rule)
            logger.info(f"添加新规则，关键词: {keywords}, 回复: '{reply[:20]}...'")
        except ValueError as e:
            logger.error(f"添加规则失败: {e}")
            raise
    
    def get_rules_count(self) -> int:
        """获取当前规则数量。
        
        Returns:
            规则数量
        """
        return len(self.rules)
    
    def clear_rules(self) -> None:
        """清空所有规则。"""
        self.rules.clear()
        logger.info("已清空所有自动回复规则")

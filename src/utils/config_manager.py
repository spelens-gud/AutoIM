"""
配置管理器模块。

提供配置文件的加载、验证和默认配置创建功能。
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml

from src.models.config import Config
from src.utils.exceptions import ConfigException
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """配置管理器类。
    
    负责从YAML文件加载配置、验证配置有效性，以及创建默认配置文件。
    
    Attributes:
        config_path: 配置文件路径
        config: 加载的配置对象
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化配置管理器。
        
        Args:
            config_path: 配置文件路径，默认为 config/config.yaml
        """
        self.config_path = Path(config_path)
        self.config: Optional[Config] = None
    
    def load_config(self) -> Config:
        """从YAML文件加载配置。
        
        如果配置文件不存在，则创建默认配置文件。
        如果配置文件格式错误，则抛出异常。
        
        Returns:
            加载的配置对象
            
        Raises:
            ConfigException: 配置文件格式错误或加载失败
        """
        # 如果配置文件不存在，创建默认配置
        if not self.config_path.exists():
            logger.warning(f"配置文件不存在: {self.config_path}，将创建默认配置")
            self.create_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data:
                raise ConfigException("配置文件为空")
            
            # 创建Config对象
            self.config = Config(
                browser_headless=config_data.get('browser', {}).get('headless', False),
                browser_user_data_dir=config_data.get('browser', {}).get('user_data_dir', './browser_data'),
                wangwang_home_url=config_data.get('wangwang', {}).get('home_url', 'https://www.1688.com/'),
                wangwang_chat_url=config_data.get('wangwang', {}).get('chat_url', 'https://amos.1688.com/msg/message.htm'),
                wangwang_login_url=config_data.get('wangwang', {}).get('login_url', 'https://login.taobao.com/?redirect_url=https%3A%2F%2Fwww.1688.com%2F'),
                check_interval=config_data.get('wangwang', {}).get('check_interval', 3),
                retry_times=config_data.get('message', {}).get('retry_times', 2),
                retry_delay=config_data.get('message', {}).get('retry_delay', 1),
                session_timeout=config_data.get('session', {}).get('inactive_timeout', 1800),
                log_level=config_data.get('logging', {}).get('level', 'INFO'),
                log_file=config_data.get('logging', {}).get('file', 'logs/wangwang_rpa.log'),
                log_max_bytes=config_data.get('logging', {}).get('max_bytes', 10485760),
                log_backup_count=config_data.get('logging', {}).get('backup_count', 5)
            )
            
            # 验证配置
            if not self.validate_config():
                raise ConfigException("配置验证失败")
            
            logger.info(f"成功加载配置文件: {self.config_path}")
            return self.config
            
        except yaml.YAMLError as e:
            raise ConfigException(f"配置文件格式错误: {e}")
        except Exception as e:
            raise ConfigException(f"加载配置文件失败: {e}")
    
    def validate_config(self) -> bool:
        """验证配置参数的有效性。
        
        检查配置参数是否在合理范围内。
        
        Returns:
            配置有效返回True，否则返回False
        """
        if not self.config:
            logger.error("配置对象为空，无法验证")
            return False
        
        # 验证检查间隔（1-60秒）
        if not (1 <= self.config.check_interval <= 60):
            logger.error(f"检查间隔无效: {self.config.check_interval}，应在1-60秒之间")
            return False
        
        # 验证重试次数（0-5次）
        if not (0 <= self.config.retry_times <= 5):
            logger.error(f"重试次数无效: {self.config.retry_times}，应在0-5次之间")
            return False
        
        # 验证重试延迟（0-10秒）
        if not (0 <= self.config.retry_delay <= 10):
            logger.error(f"重试延迟无效: {self.config.retry_delay}，应在0-10秒之间")
            return False
        
        # 验证会话超时（60-7200秒，即1分钟到2小时）
        if not (60 <= self.config.session_timeout <= 7200):
            logger.error(f"会话超时无效: {self.config.session_timeout}，应在60-7200秒之间")
            return False
        
        # 验证日志级别
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.config.log_level not in valid_log_levels:
            logger.error(f"日志级别无效: {self.config.log_level}，应为 {valid_log_levels} 之一")
            return False
        
        # 验证URL格式
        if not self.config.wangwang_home_url.startswith(('http://', 'https://')):
            logger.error(f"1688首页URL格式无效: {self.config.wangwang_home_url}")
            return False
        
        if not self.config.wangwang_chat_url.startswith(('http://', 'https://')):
            logger.error(f"旺旺聊天URL格式无效: {self.config.wangwang_chat_url}")
            return False
        
        logger.info("配置验证通过")
        return True
    
    def create_default_config(self) -> None:
        """创建默认配置文件。
        
        当配置文件不存在时，创建包含默认值的配置文件模板。
        
        Raises:
            ConfigException: 创建配置文件失败
        """
        default_config = {
            'browser': {
                'headless': False,
                'user_data_dir': './browser_data'
            },
            'wangwang': {
                'home_url': 'https://www.1688.com/',
                'chat_url': 'https://air.1688.com/app/ocms-fusion-components-1688/def_cbu_web_im/index.html#/',
                'login_url': 'https://login.1688.com/member/signin.htm?Done=https://www.1688.com/',
                'check_interval': 3
            },
            'message': {
                'retry_times': 2,
                'retry_delay': 1
            },
            'session': {
                'inactive_timeout': 1800
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/wangwang_rpa.log',
                'max_bytes': 10485760,
                'backup_count': 5
            }
        }
        
        try:
            # 确保配置目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入默认配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
            logger.info(f"成功创建默认配置文件: {self.config_path}")
            
        except Exception as e:
            raise ConfigException(f"创建默认配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项的值。
        
        Args:
            key: 配置项的键名
            default: 默认值
            
        Returns:
            配置项的值，如果不存在则返回默认值
        """
        if not self.config:
            return default
        
        return getattr(self.config, key, default)

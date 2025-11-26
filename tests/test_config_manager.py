"""
配置管理器测试模块。

测试ConfigManager类的配置加载、验证和默认配置创建功能。
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.models.config import Config
from src.utils.config_manager import ConfigManager
from src.utils.exceptions import ConfigException


class TestConfigManager:
    """测试ConfigManager类的所有功能。"""
    
    def test_create_default_config(self, tmp_path):
        """测试创建默认配置文件。"""
        config_path = tmp_path / "config.yaml"
        manager = ConfigManager(str(config_path))
        
        # 创建默认配置
        manager.create_default_config()
        
        # 验证文件已创建
        assert config_path.exists()
        
        # 验证配置内容
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        assert 'browser' in config_data
        assert 'wangwang' in config_data
        assert 'message' in config_data
        assert 'session' in config_data
        assert 'auto_reply' in config_data
        assert 'logging' in config_data
    
    def test_load_config_creates_default_if_not_exists(self, tmp_path):
        """测试当配置文件不存在时自动创建默认配置。"""
        config_path = tmp_path / "config.yaml"
        manager = ConfigManager(str(config_path))
        
        # 加载配置（文件不存在，应自动创建）
        config = manager.load_config()
        
        # 验证配置对象
        assert isinstance(config, Config)
        assert config.browser_headless is False
        assert config.check_interval == 3
        assert config.retry_times == 2
    
    def test_load_config_from_existing_file(self, tmp_path):
        """测试从现有配置文件加载配置。"""
        config_path = tmp_path / "config.yaml"
        
        # 创建测试配置文件
        test_config = {
            'browser': {'headless': True, 'user_data_dir': './test_data'},
            'wangwang': {'url': 'https://test.com', 'check_interval': 5},
            'message': {'retry_times': 3, 'retry_delay': 2},
            'session': {'inactive_timeout': 3600},
            'auto_reply': {'enabled': False, 'rules_file': 'test_rules.yaml'},
            'logging': {
                'level': 'DEBUG',
                'file': 'test.log',
                'max_bytes': 1000000,
                'backup_count': 3
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f)
        
        # 加载配置
        manager = ConfigManager(str(config_path))
        config = manager.load_config()
        
        # 验证配置值
        assert config.browser_headless is True
        assert config.wangwang_url == 'https://test.com'
        assert config.check_interval == 5
        assert config.retry_times == 3
        assert config.auto_reply_enabled is False
        assert config.log_level == 'DEBUG'
    
    def test_validate_config_valid(self, tmp_path):
        """测试验证有效配置。"""
        config_path = tmp_path / "config.yaml"
        manager = ConfigManager(str(config_path))
        manager.create_default_config()
        manager.load_config()
        
        # 验证配置
        assert manager.validate_config() is True
    
    def test_validate_config_invalid_check_interval(self, tmp_path):
        """测试验证无效的检查间隔。"""
        config_path = tmp_path / "config.yaml"
        
        # 创建无效配置（检查间隔超出范围）
        invalid_config = {
            'browser': {'headless': False, 'user_data_dir': './data'},
            'wangwang': {'url': 'https://test.com', 'check_interval': 100},
            'message': {'retry_times': 2, 'retry_delay': 1},
            'session': {'inactive_timeout': 1800},
            'auto_reply': {'enabled': True, 'rules_file': 'rules.yaml'},
            'logging': {
                'level': 'INFO',
                'file': 'test.log',
                'max_bytes': 1000000,
                'backup_count': 3
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(invalid_config, f)
        
        manager = ConfigManager(str(config_path))
        
        # 加载配置应该失败
        with pytest.raises(ConfigException):
            manager.load_config()
    
    def test_validate_config_invalid_log_level(self, tmp_path):
        """测试验证无效的日志级别。"""
        config_path = tmp_path / "config.yaml"
        
        # 创建无效配置（日志级别无效）
        invalid_config = {
            'browser': {'headless': False, 'user_data_dir': './data'},
            'wangwang': {'url': 'https://test.com', 'check_interval': 3},
            'message': {'retry_times': 2, 'retry_delay': 1},
            'session': {'inactive_timeout': 1800},
            'auto_reply': {'enabled': True, 'rules_file': 'rules.yaml'},
            'logging': {
                'level': 'INVALID',
                'file': 'test.log',
                'max_bytes': 1000000,
                'backup_count': 3
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(invalid_config, f)
        
        manager = ConfigManager(str(config_path))
        
        # 加载配置应该失败
        with pytest.raises(ConfigException):
            manager.load_config()
    
    def test_get_config_value(self, tmp_path):
        """测试获取配置项的值。"""
        config_path = tmp_path / "config.yaml"
        manager = ConfigManager(str(config_path))
        manager.create_default_config()
        manager.load_config()
        
        # 获取存在的配置项
        assert manager.get('check_interval') == 3
        assert manager.get('browser_headless') is False
        
        # 获取不存在的配置项（返回默认值）
        assert manager.get('non_existent', 'default') == 'default'
    
    def test_load_config_empty_file(self, tmp_path):
        """测试加载空配置文件。"""
        config_path = tmp_path / "config.yaml"
        
        # 创建空文件
        config_path.touch()
        
        manager = ConfigManager(str(config_path))
        
        # 加载空配置应该失败
        with pytest.raises(ConfigException, match="配置文件为空"):
            manager.load_config()
    
    def test_load_config_invalid_yaml(self, tmp_path):
        """测试加载格式错误的YAML文件。"""
        config_path = tmp_path / "config.yaml"
        
        # 创建格式错误的YAML文件
        with open(config_path, 'w') as f:
            f.write("invalid: yaml: content:\n  - broken")
        
        manager = ConfigManager(str(config_path))
        
        # 加载配置应该失败
        with pytest.raises(ConfigException, match="配置文件格式错误"):
            manager.load_config()

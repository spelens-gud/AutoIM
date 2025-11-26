"""测试主入口模块。"""

import sys
from unittest.mock import Mock, patch, MagicMock
import pytest

# 导入要测试的函数
from main import parse_arguments, print_welcome, check_environment


class TestParseArguments:
    """测试命令行参数解析功能。"""
    
    def test_default_arguments(self):
        """测试默认参数。"""
        with patch('sys.argv', ['main.py']):
            args = parse_arguments()
            assert args.headless is False
            assert args.config == "config/config.yaml"
            assert args.log_level is None
    
    def test_headless_argument(self):
        """测试无头模式参数。"""
        with patch('sys.argv', ['main.py', '--headless']):
            args = parse_arguments()
            assert args.headless is True
    
    def test_config_argument(self):
        """测试配置文件参数。"""
        with patch('sys.argv', ['main.py', '--config', 'custom.yaml']):
            args = parse_arguments()
            assert args.config == "custom.yaml"
    
    def test_log_level_argument(self):
        """测试日志级别参数。"""
        with patch('sys.argv', ['main.py', '--log-level', 'DEBUG']):
            args = parse_arguments()
            assert args.log_level == "DEBUG"
    
    def test_combined_arguments(self):
        """测试组合参数。"""
        with patch('sys.argv', ['main.py', '--headless', '--config', 'test.yaml', '--log-level', 'ERROR']):
            args = parse_arguments()
            assert args.headless is True
            assert args.config == "test.yaml"
            assert args.log_level == "ERROR"


class TestPrintWelcome:
    """测试欢迎信息打印功能。"""
    
    def test_print_welcome(self, capsys):
        """测试打印欢迎信息。"""
        print_welcome()
        captured = capsys.readouterr()
        assert "旺旺RPA自动化系统" in captured.out
        assert "v1.0.0" in captured.out


class TestCheckEnvironment:
    """测试环境检查功能。"""
    
    def test_check_environment_creates_directories(self, tmp_path, monkeypatch):
        """测试环境检查创建必要目录。"""
        # 切换到临时目录
        monkeypatch.chdir(tmp_path)
        
        # 执行环境检查
        check_environment()
        
        # 验证目录已创建
        assert (tmp_path / "config").exists()
        assert (tmp_path / "logs").exists()
        assert (tmp_path / "browser_data").exists()

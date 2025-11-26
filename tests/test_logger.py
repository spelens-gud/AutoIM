"""
测试日志配置工具。
"""

import logging
import os
from pathlib import Path
import pytest
from src.utils.logger import setup_logger, get_logger


class TestSetupLogger:
    """测试日志配置功能。"""

    def test_setup_logger_basic(self):
        """测试基本日志配置。"""
        logger = setup_logger("test_basic")
        assert logger.name == "test_basic"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_setup_logger_with_level(self):
        """测试设置日志级别。"""
        logger = setup_logger("test_level", log_level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_logger_with_file(self, tmp_path):
        """测试文件输出配置。"""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_file", log_file=str(log_file))
        
        # 验证日志文件处理器已添加
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(file_handlers) > 0
        
        # 写入日志并验证
        logger.info("测试日志消息")
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "测试日志消息" in content

    def test_setup_logger_no_console(self):
        """测试禁用控制台输出。"""
        logger = setup_logger("test_no_console", console_output=False)
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(console_handlers) == 0

    def test_setup_logger_creates_directory(self, tmp_path):
        """测试自动创建日志目录。"""
        log_file = tmp_path / "subdir" / "test.log"
        logger = setup_logger("test_dir", log_file=str(log_file))
        
        logger.info("测试")
        assert log_file.parent.exists()
        assert log_file.exists()


class TestGetLogger:
    """测试获取日志记录器功能。"""

    def test_get_logger_default(self):
        """测试获取默认日志记录器。"""
        logger = get_logger()
        assert logger.name == "wangwang_rpa"
        assert len(logger.handlers) > 0

    def test_get_logger_custom_name(self):
        """测试获取自定义名称的日志记录器。"""
        logger = get_logger("custom_logger")
        assert logger.name == "custom_logger"

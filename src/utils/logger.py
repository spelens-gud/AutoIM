"""
日志配置工具。

提供统一的日志配置功能，支持控制台和文件输出，包含日志轮转功能。
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "wangwang_rpa",
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True,
) -> logging.Logger:
    """配置并返回日志记录器。
    
    创建一个配置好的日志记录器，支持控制台和文件输出，
    文件输出使用日志轮转功能避免日志文件过大。
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别，可选值：DEBUG、INFO、WARNING、ERROR、CRITICAL
        log_file: 日志文件路径，如果为None则不输出到文件
        max_bytes: 单个日志文件最大字节数，默认10MB
        backup_count: 保留的日志文件备份数量，默认5个
        console_output: 是否输出到控制台，默认True
        
    Returns:
        配置好的日志记录器实例
        
    Examples:
        >>> logger = setup_logger("my_app", "DEBUG", "logs/app.log")
        >>> logger.info("应用启动")
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # 定义日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 添加控制台处理器
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 添加文件处理器（带日志轮转）
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建轮转文件处理器
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 防止日志向上传播到根日志记录器
    logger.propagate = False
    
    return logger


def setup_logging(level: Optional[str] = None) -> None:
    """设置全局日志配置。
    
    从配置文件或使用默认值设置日志系统。
    
    Args:
        level: 日志级别，如果指定则覆盖配置文件中的设置
    """
    # 尝试从配置文件加载日志配置
    try:
        from src.utils.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        log_level = level if level else config.log_level
        log_file = config.log_file
        max_bytes = config.log_max_bytes
        backup_count = config.log_backup_count
    except Exception:
        # 如果加载配置失败，使用默认值
        log_level = level if level else "INFO"
        log_file = "logs/wangwang_rpa.log"
        max_bytes = 10 * 1024 * 1024
        backup_count = 5
    
    # 设置根日志记录器
    setup_logger(
        name="wangwang_rpa",
        log_level=log_level,
        log_file=log_file,
        max_bytes=max_bytes,
        backup_count=backup_count,
        console_output=True
    )


def get_logger(name: str = "wangwang_rpa") -> logging.Logger:
    """获取已配置的日志记录器。
    
    如果日志记录器尚未配置，则使用默认配置创建。
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
        
    Examples:
        >>> logger = get_logger()
        >>> logger.info("这是一条日志")
    """
    logger = logging.getLogger(name)
    
    # 如果日志记录器未配置，使用默认配置
    if not logger.handlers:
        return setup_logger(name)
    
    return logger

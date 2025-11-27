"""配置数据模型。

定义系统配置的数据结构，包含所有可配置的参数。
"""

from dataclasses import dataclass


@dataclass
class Config:
    """系统配置数据模型。
    
    Attributes:
        browser_headless: 浏览器是否使用无头模式
        browser_user_data_dir: 浏览器用户数据目录
        wangwang_home_url: 1688首页URL（用于登录）
        wangwang_chat_url: 旺旺聊天页面URL
        wangwang_login_url: 1688登录页面URL
        check_interval: 消息检查间隔（秒）
        retry_times: 消息发送重试次数
        retry_delay: 重试延迟时间（秒）
        session_timeout: 会话超时时间（秒）
        log_level: 日志级别
        log_file: 日志文件路径
        log_max_bytes: 日志文件最大字节数
        log_backup_count: 日志文件备份数量
    """
    
    browser_headless: bool
    browser_user_data_dir: str
    wangwang_home_url: str
    wangwang_chat_url: str
    wangwang_login_url: str
    check_interval: int
    retry_times: int
    retry_delay: int
    session_timeout: int
    log_level: str
    log_file: str
    log_max_bytes: int
    log_backup_count: int
    
    def __post_init__(self):
        """验证配置参数的有效性。"""
        if self.check_interval <= 0:
            raise ValueError("检查间隔必须大于0")
        if self.retry_times < 0:
            raise ValueError("重试次数不能为负数")
        if self.retry_delay < 0:
            raise ValueError("重试延迟不能为负数")
        if self.session_timeout <= 0:
            raise ValueError("会话超时时间必须大于0")
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"日志级别必须是 {valid_log_levels} 之一")

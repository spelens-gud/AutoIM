"""
自定义异常类定义。

定义旺旺RPA系统中使用的所有自定义异常类型。
"""


class WangWangRPAException(Exception):
    """RPA系统基础异常类。
    
    所有自定义异常的基类，用于统一异常处理。
    """
    
    def __init__(self, message: str):
        """初始化异常。
        
        Args:
            message: 异常信息描述
        """
        self.message = message
        super().__init__(self.message)


class BrowserException(WangWangRPAException):
    """浏览器相关异常。
    
    当浏览器启动、操作或关闭过程中发生错误时抛出。
    
    Examples:
        >>> raise BrowserException("浏览器启动失败")
    """
    pass


class MessageException(WangWangRPAException):
    """消息处理异常。
    
    当消息接收、解析或发送过程中发生错误时抛出。
    
    Examples:
        >>> raise MessageException("消息发送失败")
    """
    pass


class ConfigException(WangWangRPAException):
    """配置相关异常。
    
    当配置文件加载、解析或验证失败时抛出。
    
    Examples:
        >>> raise ConfigException("配置文件格式错误")
    """
    pass

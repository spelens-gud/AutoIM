"""Cookie解析工具。

提供Cookie字符串解析功能，将浏览器Cookie字符串转换为Selenium可用的格式。
"""

from typing import List, Dict
from src.utils.logger import get_logger

logger = get_logger(__name__)


def parse_cookie_string(cookie_string: str, domain: str = ".1688.com") -> List[Dict]:
    """解析Cookie字符串为Selenium可用的Cookie列表。
    
    将浏览器Cookie字符串（如从请求头中获取的）转换为Selenium WebDriver
    可以使用的Cookie字典列表格式。
    
    Args:
        cookie_string: Cookie字符串，格式如 "name1=value1; name2=value2"
        domain: Cookie的域名，默认为 ".1688.com"
        
    Returns:
        Cookie字典列表，每个字典包含 name, value, domain 等字段
        
    Examples:
        >>> cookie_str = "cookie2=abc123; t=xyz789; _tb_token_=token123"
        >>> cookies = parse_cookie_string(cookie_str)
        >>> print(len(cookies))
        3
    """
    try:
        cookies = []
        
        # 清理Cookie字符串（移除首尾空白和换行符）
        cookie_string = cookie_string.strip().replace('\n', '').replace('\r', '')
        
        # 按分号分割Cookie字符串
        cookie_pairs = cookie_string.split(';')
        
        # 特殊Cookie的域名映射（某些Cookie需要特定域名）
        domain_mapping = {
            'cna': '.taobao.com',
            'isg': '.taobao.com',
            'l': '.taobao.com',
            'thw': '.taobao.com',
            '_m_h5_tk': '.1688.com',
            '_m_h5_tk_enc': '.1688.com',
            'xlly_s': '.1688.com',
            'tfstk': '.1688.com',
        }
        
        for pair in cookie_pairs:
            pair = pair.strip()
            if not pair:
                continue
            
            # 分割name和value
            if '=' in pair:
                name, value = pair.split('=', 1)
                name = name.strip()
                value = value.strip()
                
                # 跳过空值Cookie
                if not value:
                    logger.debug(f"跳过空值Cookie: {name}")
                    continue
                
                # 根据Cookie名称选择合适的域名
                cookie_domain = domain_mapping.get(name, domain)
                
                # 构造Cookie字典
                cookie = {
                    'name': name,
                    'value': value,
                    'domain': cookie_domain,
                    'path': '/',
                    'secure': True,  # 1688使用HTTPS
                    'httpOnly': False
                }
                
                cookies.append(cookie)
                logger.debug(f"解析Cookie: {name} = {value[:20]}... (domain: {cookie_domain})")
        
        logger.info(f"成功解析 {len(cookies)} 个Cookie")
        return cookies
        
    except Exception as e:
        logger.error(f"解析Cookie字符串失败: {str(e)}")
        raise ValueError(f"Cookie字符串格式不正确: {str(e)}")


def validate_cookies(cookies: List[Dict]) -> bool:
    """验证Cookie列表的有效性。
    
    检查Cookie列表是否包含必要的字段和关键的认证Cookie。
    
    Args:
        cookies: Cookie字典列表
        
    Returns:
        True表示Cookie有效，False表示无效
    """
    if not cookies or not isinstance(cookies, list):
        logger.warning("Cookie列表为空或格式不正确")
        return False
    
    # 检查是否包含关键的认证Cookie
    cookie_names = [cookie.get('name', '') for cookie in cookies]
    
    # 1688/淘宝最关键的登录Cookie
    critical_cookies = ['_tb_token_', 'cookie2']
    has_critical = all(name in cookie_names for name in critical_cookies)
    
    if not has_critical:
        logger.warning(f"缺少关键Cookie: {critical_cookies}")
        logger.warning(f"当前Cookie列表: {cookie_names}")
        return False
    
    # 检查每个Cookie是否有必需的字段
    for cookie in cookies:
        if 'name' not in cookie or 'value' not in cookie:
            logger.warning(f"Cookie缺少必需字段: {cookie}")
            return False
    
    logger.info("Cookie验证通过")
    return True

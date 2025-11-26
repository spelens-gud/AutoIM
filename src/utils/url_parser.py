"""URL 解析工具模块。

提供 1688 等电商平台跟踪链接的解析功能。
"""

from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs, unquote
from dataclasses import dataclass

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TrackingUrlInfo:
    """跟踪链接信息。
    
    Attributes:
        domain: 域名
        path: 路径
        gad_campaignid: Google Ads 活动 ID
        gclid: Google Click ID
        clickid: 联盟点击 ID
        target_url: 目标重定向 URL
        tracelog: 跟踪日志类型
        cbu_cps_trace_flag: CPS 跟踪标记
        all_params: 所有查询参数
    """
    domain: str
    path: str
    gad_campaignid: Optional[str] = None
    gclid: Optional[str] = None
    clickid: Optional[str] = None
    target_url: Optional[str] = None
    tracelog: Optional[str] = None
    cbu_cps_trace_flag: Optional[str] = None
    all_params: Optional[Dict] = None


def parse_1688_tracking_url(url: str) -> TrackingUrlInfo:
    """解析 1688 跟踪链接。
    
    Args:
        url: 完整的跟踪 URL
        
    Returns:
        TrackingUrlInfo 对象，包含解析后的信息
        
    Raises:
        ValueError: URL 格式无效时抛出
        
    Examples:
        >>> url = "https://air.1688.com/kapp/channel-fe/cps-4c-pc/home?clickid=abc123"
        >>> info = parse_1688_tracking_url(url)
        >>> print(info.clickid)
        abc123
    """
    try:
        # 解析 URL
        parsed = urlparse(url)
        
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("无效的 URL 格式")
        
        # 解析查询参数
        params = parse_qs(parsed.query)
        
        # 提取单个值（parse_qs 返回列表）
        def get_param(key: str) -> Optional[str]:
            values = params.get(key, [])
            return values[0] if values else None
        
        # 解码目标 URL
        target_url = get_param('targetUrl')
        if target_url:
            target_url = unquote(target_url)
        
        # 构建结果对象
        info = TrackingUrlInfo(
            domain=parsed.netloc,
            path=parsed.path,
            gad_campaignid=get_param('gad_campaignid'),
            gclid=get_param('gclid'),
            clickid=get_param('clickid'),
            target_url=target_url,
            tracelog=get_param('tracelog'),
            cbu_cps_trace_flag=get_param('cbu_cps_trace_flag'),
            all_params={k: v[0] if len(v) == 1 else v for k, v in params.items()}
        )
        
        logger.debug(f"解析 URL 成功: {parsed.netloc}{parsed.path}")
        return info
        
    except Exception as e:
        logger.error(f"解析 URL 失败: {str(e)}")
        raise ValueError(f"URL 解析错误: {str(e)}")


def extract_final_url(tracking_url: str) -> Optional[str]:
    """从跟踪链接中提取最终目标 URL。
    
    Args:
        tracking_url: 跟踪链接
        
    Returns:
        最终目标 URL，如果不存在则返回 None
        
    Examples:
        >>> url = "https://air.1688.com/...?targetUrl=https%3A%2F%2Fs.click.1688.com%2F..."
        >>> final_url = extract_final_url(url)
        >>> print(final_url)
        https://s.click.1688.com/...
    """
    try:
        info = parse_1688_tracking_url(tracking_url)
        return info.target_url
    except Exception as e:
        logger.error(f"提取目标 URL 失败: {str(e)}")
        return None


def get_tracking_params(url: str) -> Dict[str, str]:
    """获取 URL 中的所有跟踪参数。
    
    Args:
        url: 跟踪链接
        
    Returns:
        包含跟踪参数的字典
        
    Examples:
        >>> url = "https://air.1688.com/...?clickid=abc&tracelog=cps"
        >>> params = get_tracking_params(url)
        >>> print(params['clickid'])
        abc
    """
    try:
        info = parse_1688_tracking_url(url)
        
        # 提取跟踪相关参数
        tracking_params = {}
        
        if info.gad_campaignid:
            tracking_params['gad_campaignid'] = info.gad_campaignid
        if info.gclid:
            tracking_params['gclid'] = info.gclid
        if info.clickid:
            tracking_params['clickid'] = info.clickid
        if info.tracelog:
            tracking_params['tracelog'] = info.tracelog
        if info.cbu_cps_trace_flag:
            tracking_params['cbu_cps_trace_flag'] = info.cbu_cps_trace_flag
            
        return tracking_params
        
    except Exception as e:
        logger.error(f"获取跟踪参数失败: {str(e)}")
        return {}


def is_1688_tracking_url(url: str) -> bool:
    """判断是否为 1688 跟踪链接。
    
    Args:
        url: 待检查的 URL
        
    Returns:
        如果是 1688 跟踪链接返回 True，否则返回 False
        
    Examples:
        >>> is_1688_tracking_url("https://air.1688.com/kapp/channel-fe/cps-4c-pc/home")
        True
        >>> is_1688_tracking_url("https://www.google.com")
        False
    """
    try:
        parsed = urlparse(url)
        # 检查是否为 1688 域名
        return '1688.com' in parsed.netloc
    except Exception:
        return False


def clean_tracking_url(url: str, keep_params: Optional[list] = None) -> str:
    """清理跟踪链接，移除跟踪参数。
    
    Args:
        url: 原始 URL
        keep_params: 要保留的参数列表，如果为 None 则移除所有跟踪参数
        
    Returns:
        清理后的 URL
        
    Examples:
        >>> url = "https://air.1688.com/home?clickid=abc&page=1"
        >>> clean_url = clean_tracking_url(url, keep_params=['page'])
        >>> print(clean_url)
        https://air.1688.com/home?page=1
    """
    try:
        parsed = urlparse(url)
        
        # 检查 URL 是否有效
        if not parsed.scheme or not parsed.netloc:
            return url
        
        params = parse_qs(parsed.query)
        
        # 定义跟踪参数列表
        tracking_param_keys = {
            'gad_source', 'gad_campaignid', 'gclid',
            'clickid', 'tracelog', 'cbu_cps_trace_flag',
            'targetUrl'
        }
        
        # 过滤参数
        if keep_params is None:
            # 移除所有跟踪参数
            filtered_params = {
                k: v for k, v in params.items()
                if k not in tracking_param_keys
            }
        else:
            # 只保留指定参数
            filtered_params = {
                k: v for k, v in params.items()
                if k in keep_params
            }
        
        # 重建查询字符串
        if filtered_params:
            query_parts = []
            for key, values in filtered_params.items():
                for value in values:
                    query_parts.append(f"{key}={value}")
            query_string = "&".join(query_parts)
        else:
            query_string = ""
        
        # 重建 URL
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if query_string:
            clean_url += f"?{query_string}"
            
        return clean_url
        
    except Exception as e:
        logger.error(f"清理 URL 失败: {str(e)}")
        return url

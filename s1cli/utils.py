"""工具函数"""
import time
import random
from typing import Optional
from functools import wraps


def rate_limit(min_delay: float = 0.5, max_delay: float = 2.0):
    """请求频率限制装饰器
    
    Args:
        min_delay: 最小延迟（秒）
        max_delay: 最大延迟（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 随机延迟，避免被识别为机器人
            delay = random.uniform(min_delay, max_delay)
            time.sleep(delay)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def strip_html_tags(html: str) -> str:
    """移除 HTML 标签，保留纯文本
    
    Args:
        html: HTML 字符串
        
    Returns:
        纯文本字符串
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')
    return soup.get_text(strip=True)


def format_number(num: int) -> str:
    """格式化数字（如 1234 -> 1.2K）
    
    Args:
        num: 数字
        
    Returns:
        格式化后的字符串
    """
    if num >= 1000000:
        return f"{num / 1000000:.1f}M"
    elif num >= 1000:
        return f"{num / 1000:.1f}K"
    else:
        return str(num)


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


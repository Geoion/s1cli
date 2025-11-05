"""重试机制"""
import time
from functools import wraps
from typing import Type, Tuple, Callable, Any

from s1cli.api.exceptions import NetworkError, RateLimitError


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (NetworkError, RateLimitError, ConnectionError)
):
    """重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟倍数（指数退避）
        exceptions: 需要重试的异常类型
    
    Example:
        @retry_on_error(max_retries=3, delay=1.0)
        def fetch_data():
            # 可能失败的网络请求
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        print(f"⚠️  {func.__name__} 失败，{current_delay:.1f}秒后重试... "
                              f"({attempt + 1}/{max_retries})")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        print(f"❌ {func.__name__} 失败，已达最大重试次数")
                except Exception as e:
                    # 其他异常直接抛出，不重试
                    raise e
            
            # 所有重试都失败，抛出最后一个异常
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def with_error_handling(error_message: str = "操作失败", 
                        default_return: Any = None,
                        log_error: bool = True):
    """错误处理装饰器
    
    捕获异常并返回默认值，避免程序崩溃
    
    Args:
        error_message: 错误提示信息
        default_return: 发生错误时的默认返回值
        log_error: 是否打印错误信息
    
    Example:
        @with_error_handling(error_message="获取数据失败", default_return=[])
        def get_data():
            # 可能抛出异常的操作
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    print(f"❌ {error_message}: {str(e)}")
                return default_return
        return wrapper
    return decorator





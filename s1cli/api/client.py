"""Stage1st HTTP 客户端"""
import httpx
import time
import random
from typing import Dict, Any, Optional
from s1cli.config import Config


class S1Client:
    """Stage1st HTTP 客户端
    
    模拟真实浏览器访问，包含：
    - Chrome User Agent
    - 完整的浏览器 headers
    - 请求频率限制
    - Cookie 管理
    """
    
    BASE_URL = "https://stage1st.com/2b"
    
    # 模拟 Chrome User Agent
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    def __init__(self, config: Config):
        """初始化客户端
        
        Args:
            config: 配置对象
        """
        self.config = config
        self._last_request_time = 0
        
        # 初始化 httpx 客户端
        self._client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers=self._get_default_headers()
        )
        
        # 加载已保存的 cookies
        self._load_cookies()
    
    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头
        
        Returns:
            请求头字典
        """
        return {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
    
    def _load_cookies(self):
        """从配置加载 cookies"""
        cookies = self.config.load_cookies()
        for name, value in cookies.items():
            self._client.cookies.set(name, value, domain=".stage1st.com")
    
    def _save_cookies(self):
        """保存 cookies 到配置"""
        cookies = {}
        for cookie in self._client.cookies.jar:
            if "stage1st.com" in cookie.domain:
                cookies[cookie.name] = cookie.value
        self.config.save_cookies(cookies)
    
    def _rate_limit(self, min_delay: float = 0.5, max_delay: float = 2.0):
        """请求频率限制
        
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
        """
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        # 如果距离上次请求时间太短，则等待
        if time_since_last_request < min_delay:
            delay = random.uniform(min_delay, max_delay)
            time.sleep(delay)
        
        self._last_request_time = time.time()
    
    def get(
        self, 
        path: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        rate_limit: bool = True
    ) -> httpx.Response:
        """发送 GET 请求
        
        Args:
            path: 请求路径
            params: 查询参数
            headers: 额外的请求头
            rate_limit: 是否启用请求频率限制
            
        Returns:
            响应对象
        """
        if rate_limit:
            self._rate_limit()
        
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        
        # 合并请求头
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)
        
        # 添加 Referer
        request_headers["Referer"] = self.BASE_URL
        
        response = self._client.get(url, params=params, headers=request_headers)
        
        # 保存 cookies
        self._save_cookies()
        
        return response
    
    def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        rate_limit: bool = True
    ) -> httpx.Response:
        """发送 POST 请求
        
        Args:
            path: 请求路径
            data: 表单数据
            json: JSON 数据
            headers: 额外的请求头
            rate_limit: 是否启用请求频率限制
            
        Returns:
            响应对象
        """
        if rate_limit:
            self._rate_limit()
        
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        
        # 合并请求头
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)
        
        # 添加 Referer 和 Origin
        request_headers["Referer"] = self.BASE_URL
        request_headers["Origin"] = self.BASE_URL
        
        if data is not None:
            request_headers["Content-Type"] = "application/x-www-form-urlencoded"
            response = self._client.post(url, data=data, headers=request_headers)
        elif json is not None:
            request_headers["Content-Type"] = "application/json"
            response = self._client.post(url, json=json, headers=request_headers)
        else:
            response = self._client.post(url, headers=request_headers)
        
        # 保存 cookies
        self._save_cookies()
        
        return response
    
    def close(self):
        """关闭客户端"""
        self._client.close()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


"""用户数据模型"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """用户信息"""
    
    username: str
    uid: Optional[str] = None
    email: Optional[str] = None
    credits: int = 0
    posts_count: int = 0
    threads_count: int = 0
    last_login: Optional[datetime] = None
    register_date: Optional[datetime] = None
    avatar_url: Optional[str] = None
    signature: Optional[str] = None
    group: Optional[str] = None  # 用户组
    
    def __str__(self) -> str:
        return f"{self.username} (UID: {self.uid})"




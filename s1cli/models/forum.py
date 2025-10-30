"""论坛版块数据模型"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Forum:
    """论坛版块"""
    
    id: str
    name: str
    description: Optional[str] = None
    threads_count: int = 0
    posts_count: int = 0
    new_posts: int = 0  # 新帖数
    url: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.name} (主题: {self.threads_count})"


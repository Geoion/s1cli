"""帖子相关数据模型"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class Thread:
    """帖子/主题"""
    
    id: str
    title: str
    author: str
    author_id: Optional[str] = None
    forum: Optional[str] = None
    forum_id: Optional[str] = None
    content: Optional[str] = None
    views: int = 0
    replies: int = 0
    created_at: Optional[datetime] = None
    last_reply_time: Optional[datetime] = None
    last_reply_author: Optional[str] = None
    is_sticky: bool = False
    is_locked: bool = False
    is_digest: bool = False
    posts: List['Post'] = field(default_factory=list)
    current_page: int = 1
    total_pages: int = 1
    
    def __str__(self) -> str:
        return f"[{self.id}] {self.title} by {self.author}"


@dataclass
class Post:
    """帖子回复"""
    
    id: str
    thread_id: str
    floor: int  # 楼层号
    author: str
    author_id: Optional[str] = None
    content: str = ""
    post_time: Optional[datetime] = None
    quote_post_id: Optional[str] = None  # 引用的回复ID
    
    def __str__(self) -> str:
        return f"#{self.floor} {self.author}: {self.content[:50]}..."


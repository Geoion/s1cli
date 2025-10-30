"""数据模型模块"""

from s1cli.models.forum import Forum
from s1cli.models.thread import Thread, Post
from s1cli.models.user import User

__all__ = ['Forum', 'Thread', 'Post', 'User']


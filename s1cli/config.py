"""配置文件和会话管理"""
import os
import toml
import base64
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class Config:
    """配置管理器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_dir: 配置目录路径，默认为 ~/.config/s1cli/
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".config" / "s1cli"
        
        self.config_file = self.config_dir / "config.toml"
        self.session_file = self.config_dir / "session.toml"
        self.cache_dir = self.config_dir / "cache"
        
        # 确保配置目录存在
        self._ensure_config_dir()
        
        # 加载配置
        self._config = self._load_config()
        self._session = self._load_session()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                return toml.load(self.config_file)
            except Exception as e:
                print(f"警告：加载配置文件失败：{e}")
                return self._default_config()
        else:
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "preferences": {
                "theme": "dark",
                "posts_per_page": 20,
                "auto_login": True,
            }
        }
    
    def _load_session(self) -> Dict[str, Any]:
        """加载会话信息"""
        if self.session_file.exists():
            try:
                session = toml.load(self.session_file)
                # 检查会话是否过期
                if self._is_session_expired(session):
                    print("会话已过期")
                    return {}
                return session
            except Exception as e:
                print(f"警告：加载会话文件失败：{e}")
                return {}
        else:
            return {}
    
    def _is_session_expired(self, session: Dict[str, Any]) -> bool:
        """检查会话是否过期
        
        Args:
            session: 会话信息
            
        Returns:
            是否过期
        """
        if "created_at" not in session:
            return True
        
        try:
            created_at = datetime.fromisoformat(session["created_at"])
            # 默认 7 天过期
            expires_in = session.get("expires_in", 7 * 24 * 3600)
            expiry_time = created_at + timedelta(seconds=expires_in)
            return datetime.now() > expiry_time
        except Exception:
            return True
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                toml.dump(self._config, f)
        except Exception as e:
            print(f"错误：保存配置文件失败：{e}")
    
    def save_session(self):
        """保存会话到文件"""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                toml.dump(self._session, f)
        except Exception as e:
            print(f"错误：保存会话文件失败：{e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置键（支持点号分隔，如 "preferences.theme"）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置项
        
        Args:
            key: 配置键（支持点号分隔）
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 导航到最后一级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        self.save_config()
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def get_session(self, key: str = None) -> Any:
        """获取会话信息
        
        Args:
            key: 会话键，如果为 None 则返回全部
            
        Returns:
            会话值
        """
        if key is None:
            return self._session.copy()
        return self._session.get(key)
    
    def set_session(self, key: str, value: Any):
        """设置会话信息
        
        Args:
            key: 会话键
            value: 会话值
        """
        self._session[key] = value
        self.save_session()
    
    def save_cookies(self, cookies: Dict[str, str]):
        """保存 cookies
        
        Args:
            cookies: cookies 字典
        """
        # 使用 base64 编码存储
        cookies_json = json.dumps(cookies)
        cookies_encoded = base64.b64encode(cookies_json.encode()).decode()
        
        self._session["cookies"] = cookies_encoded
        self._session["created_at"] = datetime.now().isoformat()
        self._session["expires_in"] = 7 * 24 * 3600  # 7 天
        self.save_session()
    
    def load_cookies(self) -> Dict[str, str]:
        """加载 cookies
        
        Returns:
            cookies 字典
        """
        cookies_encoded = self._session.get("cookies")
        if not cookies_encoded:
            return {}
        
        try:
            cookies_json = base64.b64decode(cookies_encoded).decode()
            return json.loads(cookies_json)
        except Exception as e:
            print(f"警告：解析 cookies 失败：{e}")
            return {}
    
    def set_user_info(self, username: str, uid: Optional[str] = None):
        """保存用户信息
        
        Args:
            username: 用户名
            uid: 用户 ID
        """
        if "user" not in self._session:
            self._session["user"] = {}
        
        self._session["user"]["username"] = username
        if uid:
            self._session["user"]["uid"] = uid
        self._session["user"]["last_login"] = datetime.now().isoformat()
        self.save_session()
    
    def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息
        
        Returns:
            用户信息字典
        """
        return self._session.get("user", {})
    
    def is_logged_in(self) -> bool:
        """检查是否已登录
        
        Returns:
            是否已登录
        """
        return bool(self._session.get("cookies") and self._session.get("user"))
    
    def clear_session(self):
        """清除会话信息"""
        self._session = {}
        if self.session_file.exists():
            self.session_file.unlink()
    
    def get_cache_path(self, cache_name: str) -> Path:
        """获取缓存文件路径
        
        Args:
            cache_name: 缓存文件名
            
        Returns:
            缓存文件路径
        """
        return self.cache_dir / cache_name
    
    def save_forum_list(self, forums: list):
        """保存版块列表到缓存
        
        Args:
            forums: 版块列表
        """
        try:
            cache_file = self.cache_dir / "forums.json"
            import json
            with open(cache_file, 'w', encoding='utf-8') as f:
                # 将 Forum 对象转换为字典
                forums_data = [
                    {
                        'id': f.id,
                        'name': f.name,
                        'description': f.description,
                        'threads_count': f.threads_count,
                        'posts_count': f.posts_count,
                        'new_posts': f.new_posts,
                        'url': f.url
                    }
                    for f in forums
                ]
                json.dump(forums_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"警告：保存版块列表失败：{e}")
    
    def load_forum_list(self):
        """从缓存加载版块列表
        
        Returns:
            版块列表或 None
        """
        try:
            cache_file = self.cache_dir / "forums.json"
            if not cache_file.exists():
                return None
            
            import json
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"警告：加载版块列表失败：{e}")
            return None
    
    def save_thread_list(self, threads: list, forum_name: str):
        """保存帖子列表到缓存
        
        Args:
            threads: 帖子列表
            forum_name: 版块名称（用于区分不同版块的缓存）
        """
        try:
            cache_file = self.cache_dir / "threads.json"
            import json
            # 将 Thread 对象转换为字典
            threads_data = {
                'forum': forum_name,
                'threads': [
                    {
                        'id': t.id,
                        'title': t.title,
                        'author': t.author,
                        'forum': t.forum,
                        'forum_id': t.forum_id,
                        'replies': t.replies,
                        'views': t.views,
                        'is_sticky': t.is_sticky,
                        'is_digest': t.is_digest
                    }
                    for t in threads
                ]
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(threads_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"警告：保存帖子列表失败：{e}")
    
    def load_thread_list(self):
        """从缓存加载帖子列表
        
        Returns:
            帖子列表数据或 None
        """
        try:
            cache_file = self.cache_dir / "threads.json"
            if not cache_file.exists():
                return None
            
            import json
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"警告：加载帖子列表失败：{e}")
            return None


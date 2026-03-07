"""S1CLI Textual 主应用"""
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button
from textual.binding import Binding

from s1cli.config import Config
from s1cli.api.client import S1Client


class S1App(App):
    """Stage1st CLI TUI 应用"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #sidebar {
        width: 30;
        background: $panel;
        border-right: solid $primary;
    }
    
    #content {
        width: 1fr;
    }
    
    .welcome {
        height: 100%;
        align: center middle;
    }
    
    .welcome-text {
        text-align: center;
        width: 60;
    }
    
    Button {
        margin: 1 2;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "退出", priority=True),
        Binding("l", "login", "登录"),
        Binding("h", "help", "帮助"),
        Binding("s", "search", "搜索"),
    ]
    
    TITLE = "S1CLI - Stage1st 论坛客户端"
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.client = S1Client(self.config)
    
    def compose(self) -> ComposeResult:
        """组装界面"""
        yield Header()
        
        with Horizontal():
            # 左侧导航栏
            with Vertical(id="sidebar"):
                yield Static("📋 论坛版块", classes="sidebar-title")
                yield Button("🎮 游戏论坛", id="btn-forum-game")
                yield Button("📺 动漫论坛", id="btn-forum-anime")
                yield Button("🎬 影视论坛", id="btn-forum-movie")
                yield Button("💻 数码论坛", id="btn-forum-digital")
                yield Button("🎲 手游页游", id="btn-forum-mobile")
                yield Static("---")
                yield Button("🔍 搜索", id="btn-search")
                yield Button("👤 个人中心", id="btn-profile")
                yield Button("⚙️  设置", id="btn-settings")
            
            # 右侧内容区
            with Container(id="content"):
                yield self._get_welcome_screen()
        
        yield Footer()
    
    def _get_welcome_screen(self) -> Container:
        """欢迎界面"""
        welcome = Container(classes="welcome")
        
        # 检查登录状态
        if self.config.is_logged_in():
            user_info = self.config.get_user_info()
            username = user_info.get('username', '用户')
            content = f"""
[bold cyan]欢迎回来，{username}！[/bold cyan]

请从左侧选择论坛版块开始浏览。

快捷键：
  [bold]↑/↓ 或 j/k[/bold] - 上下导航
  [bold]Enter[/bold] - 进入选中项
  [bold]Esc[/bold] - 返回上级
  [bold]s[/bold] - 搜索
  [bold]l[/bold] - 登录/登出
  [bold]h[/bold] - 帮助
  [bold]q[/bold] - 退出
"""
        else:
            content = """
[bold cyan]欢迎使用 S1CLI！[/bold cyan]

Stage1st 论坛命令行客户端

请先登录以使用完整功能。
按 [bold]l[/bold] 键登录，或从左侧浏览论坛。

快捷键：
  [bold]l[/bold] - 登录
  [bold]h[/bold] - 帮助
  [bold]q[/bold] - 退出
"""
        
        welcome.compose_add_child(Static(content, classes="welcome-text"))
        return welcome
    
    def action_login(self) -> None:
        """登录操作"""
        from s1cli.ui.screens.login import LoginScreen
        
        def handle_login(success):
            if success:
                self.notify("✅ 登录成功！", severity="information")
                # 刷新主界面
                self.refresh()
            else:
                self.notify("已取消登录", severity="warning")
        
        self.push_screen(LoginScreen(self.client, self.config), handle_login)
    
    def action_help(self) -> None:
        """帮助操作"""
        help_text = """
S1CLI 快捷键：

  q - 退出当前界面/退出程序
  ↑/↓ 或 j/k - 上下导航
  Enter - 进入选中项
  Esc - 返回上级
  n - 发新帖
  r - 回复
  s - 搜索
  l - 登录/登出
  h - 帮助
"""
        self.notify(help_text, title="帮助", timeout=10)
    
    def action_search(self) -> None:
        """搜索操作"""
        from s1cli.ui.screens.search import SearchScreen
        self.push_screen(SearchScreen(self.client, self.config))
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        button_id = event.button.id
        
        if button_id == "btn-search":
            self.action_search()
        elif button_id == "btn-profile":
            self.notify("个人中心开发中...")
        elif button_id == "btn-settings":
            self.notify("设置功能开发中...")
        elif button_id and button_id.startswith("btn-forum-"):
            # 论坛版块按钮
            from s1cli.ui.screens.thread_list import ThreadListScreen
            # 将 label 转换为字符串
            label_text = str(event.button.label).strip() if event.button.label else ""
            # 移除 emoji
            forum_name = label_text.split()[-1] if label_text else "论坛"
            self.push_screen(ThreadListScreen(self.client, self.config, forum_name))
    
    def on_mount(self) -> None:
        """应用挂载时"""
        if self.config.session_expired:
            self.notify(
                "登录会话已过期，请按 'l' 重新登录",
                title="会话过期",
                severity="warning",
                timeout=8,
            )
        elif self.config.is_logged_in():
            user_info = self.config.get_user_info()
            username = user_info.get('username', '用户')
            self.notify(f"欢迎回来，{username}！", severity="information")
        else:
            self.notify("欢迎使用 S1CLI！按 'l' 登录", severity="information")


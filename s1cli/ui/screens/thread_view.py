"""帖子详情查看界面"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Footer, Header, RichLog
from textual.binding import Binding
from textual.containers import Container, Vertical, ScrollableContainer

from s1cli.api.thread import ThreadAPI
from s1cli.utils import strip_html_tags



class ThreadViewScreen(Screen):
    """帖子详情查看界面"""
    
    CSS = """
    ThreadViewScreen {
        background: $surface;
    }
    
    #thread-title {
        height: auto;
        background: $primary;
        color: $text;
        padding: 1;
        text-align: center;
        text-style: bold;
    }
    
    #thread-info {
        height: 2;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
    }
    
    #content-container {
        height: 1fr;
        background: $surface;
    }
    
    .post-item {
        margin: 1;
        padding: 1;
        border: solid $primary-darken-1;
        background: $panel;
    }
    
    .post-header {
        color: $primary;
        text-style: bold;
        padding-bottom: 1;
    }
    
    .post-content {
        color: $text;
        padding: 1 0;
    }
    
    .post-footer {
        color: $text-muted;
        text-style: italic;
        padding-top: 1;
        border-top: solid $surface;
    }
    
    .status-bar {
        height: 1;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "back", "返回", priority=True),
        Binding("r", "refresh", "刷新"),
        Binding("n", "next_page", "下一页"),
        Binding("p", "prev_page", "上一页"),
        Binding("j", "scroll_down", "向下"),
        Binding("k", "scroll_up", "向上"),
    ]
    
    def __init__(self, client, config, thread_id: str, page: int = 1):
        super().__init__()
        self.client = client
        self.config = config
        self.thread_api = ThreadAPI(client)
        self.thread_id = thread_id
        self.page = page
        self.thread = None
    
    def compose(self) -> ComposeResult:
        """组装界面"""
        yield Header()
        yield Static("", id="thread-title")
        yield Static("", id="thread-info")
        with ScrollableContainer(id="content-container"):
            yield RichLog(id="content-log", wrap=True, highlight=True)
        yield Static("", classes="status-bar", id="status-bar")
        yield Footer()
    
    def on_mount(self) -> None:
        """界面挂载时"""
        self.load_thread()
    
    def load_thread(self) -> None:
        """触发后台加载帖子详情"""
        self.query_one("#status-bar", Static).update("🔄 正在加载帖子...")
        self.run_worker(self._fetch_thread, exclusive=True, thread=True)

    def _fetch_thread(self) -> None:
        """在后台线程中执行网络请求"""
        try:
            thread = self.thread_api.get_thread(self.thread_id, self.page)
        except Exception as e:
            self.app.call_from_thread(self._on_thread_error, str(e))
            return
        self.app.call_from_thread(self._on_thread_loaded, thread)

    def _on_thread_loaded(self, thread) -> None:
        self.thread = thread
        status = self.query_one("#status-bar", Static)

        self.query_one("#thread-title", Static).update(f"📖 {thread.title}")
        self.query_one("#thread-info", Static).update(
            f"作者：{thread.author} | 查看：{thread.views} | "
            f"回复：{thread.replies} | 第{self.page}页"
        )

        content_log = self.query_one("#content-log", RichLog)
        content_log.clear()
        content_log.write("[bold cyan]━━━ 楼主 ━━━[/bold cyan]")
        content_log.write(f"[bold]{thread.author}[/bold]")
        content_log.write("")
        clean_content = strip_html_tags(thread.content) if thread.content else "（无内容）"
        content_log.write(clean_content)
        content_log.write("")

        for post in thread.posts:
            content_log.write(f"[bold cyan]━━━ {post.floor}楼 ━━━[/bold cyan]")
            content_log.write(f"[bold]{post.author}[/bold]")
            content_log.write("")
            clean_post = strip_html_tags(post.content) if post.content else "（无内容）"
            content_log.write(clean_post)
            content_log.write("")

        status.update(
            f"✅ 已加载 {len(thread.posts)} 条回复 | "
            f"第{self.page}页 | [n]下一页 [p]上一页 [r]刷新 [j/k]滚动"
        )

    def _on_thread_error(self, error: str) -> None:
        self.query_one("#status-bar", Static).update(f"❌ 加载失败：{error}")
    
    def action_back(self) -> None:
        """返回"""
        self.dismiss()
    
    def action_refresh(self) -> None:
        """刷新"""
        self.load_thread()
    
    def action_next_page(self) -> None:
        """下一页"""
        self.page += 1
        self.load_thread()
    
    def action_prev_page(self) -> None:
        """上一页"""
        if self.page > 1:
            self.page -= 1
            self.load_thread()
    
    def action_scroll_down(self) -> None:
        """向下滚动"""
        container = self.query_one("#content-container", ScrollableContainer)
        container.scroll_down()
    
    def action_scroll_up(self) -> None:
        """向上滚动"""
        container = self.query_one("#content-container", ScrollableContainer)
        container.scroll_up()





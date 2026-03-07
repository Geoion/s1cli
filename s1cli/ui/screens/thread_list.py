"""帖子列表界面"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Static, Footer, Header
from textual.binding import Binding
from textual.containers import Container

from s1cli.api.forum import ForumAPI


class ThreadListScreen(Screen):
    """帖子列表界面"""
    
    CSS = """
    ThreadListScreen {
        background: $surface;
    }
    
    #thread-header {
        height: 3;
        background: $primary;
        color: $text;
        padding: 1;
        text-align: center;
        text-style: bold;
    }
    
    DataTable {
        height: 1fr;
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
        Binding("enter", "view_thread", "查看帖子"),
    ]
    
    def __init__(self, client, config, forum_name: str, page: int = 1):
        super().__init__()
        self.client = client
        self.config = config
        self.forum_api = ForumAPI(client)
        self.forum_name = forum_name
        self.page = page
        self.threads = []
    
    def compose(self) -> ComposeResult:
        """组装界面"""
        yield Header()
        yield Static(f"📋 {self.forum_name} - 第{self.page}页", id="thread-header")
        yield DataTable(id="thread-table", cursor_type="row")
        yield Static("", classes="status-bar", id="status-bar")
        yield Footer()
    
    def on_mount(self) -> None:
        """界面挂载时"""
        table = self.query_one("#thread-table", DataTable)
        
        # 添加列
        table.add_columns("ID", "标题", "作者", "回复", "查看")
        
        # 加载数据
        self.load_threads()
    
    def load_threads(self) -> None:
        """触发后台加载帖子列表"""
        self.query_one("#status-bar", Static).update(f"🔄 正在加载第{self.page}页...")
        self.run_worker(self._fetch_threads, exclusive=True, thread=True)

    def _fetch_threads(self) -> None:
        """在后台线程中执行网络请求，完成后回到主线程更新 UI"""
        page = self.page
        forum_name = self.forum_name
        try:
            threads = self.forum_api.get_thread_list(forum_name, page)
        except Exception as e:
            self.app.call_from_thread(self._on_threads_error, str(e))
            return
        self.app.call_from_thread(self._on_threads_loaded, threads)

    def _on_threads_loaded(self, threads) -> None:
        self.threads = threads
        table = self.query_one("#thread-table", DataTable)
        status = self.query_one("#status-bar", Static)
        table.clear()

        if not threads:
            status.update("❌ 没有找到帖子")
            return

        for thread in threads:
            title = thread.title
            if thread.is_sticky:
                title = f"📌 {title}"
            if thread.is_digest:
                title = f"💎 {title}"
            table.add_row(
                thread.id,
                title[:50],
                thread.author,
                str(thread.replies),
                str(thread.views),
            )
        status.update(
            f"✅ 已加载 {len(threads)} 个帖子 | 第{self.page}页 | "
            "[n]下一页 [p]上一页 [r]刷新 [Enter]查看"
        )

    def _on_threads_error(self, error: str) -> None:
        self.query_one("#status-bar", Static).update(f"❌ 加载失败：{error}")
    
    def action_back(self) -> None:
        """返回"""
        self.dismiss()
    
    def action_refresh(self) -> None:
        """刷新"""
        self.load_threads()
    
    def action_next_page(self) -> None:
        """下一页"""
        self.page += 1
        header = self.query_one("#thread-header", Static)
        header.update(f"📋 {self.forum_name} - 第{self.page}页")
        self.load_threads()
    
    def action_prev_page(self) -> None:
        """上一页"""
        if self.page > 1:
            self.page -= 1
            header = self.query_one("#thread-header", Static)
            header.update(f"📋 {self.forum_name} - 第{self.page}页")
            self.load_threads()
    
    def action_view_thread(self) -> None:
        """查看选中的帖子"""
        table = self.query_one("#thread-table", DataTable)
        
        if table.cursor_row is not None and self.threads:
            try:
                # 获取选中的行
                row_index = table.cursor_row
                if row_index < len(self.threads):
                    thread = self.threads[row_index]
                    # 这里可以跳转到帖子详情界面
                    # self.app.push_screen(ThreadViewScreen(...))
                    self.notify(f"正在查看帖子：{thread.title}")
            except Exception as e:
                self.notify(f"错误：{str(e)}", severity="error")





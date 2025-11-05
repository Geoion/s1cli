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
        """加载帖子列表"""
        status = self.query_one("#status-bar", Static)
        status.update(f"🔄 正在加载第{self.page}页...")
        
        try:
            self.threads = self.forum_api.get_thread_list(self.forum_name, self.page)
            
            table = self.query_one("#thread-table", DataTable)
            table.clear()
            
            if not self.threads:
                status.update(f"❌ 没有找到帖子")
                return
            
            # 添加数据行
            for thread in self.threads:
                # 添加标记
                title = thread.title
                if thread.is_sticky:
                    title = f"📌 {title}"
                if thread.is_digest:
                    title = f"💎 {title}"
                
                table.add_row(
                    thread.id,
                    title[:50],  # 限制标题长度
                    thread.author,
                    str(thread.replies),
                    str(thread.views)
                )
            
            status.update(f"✅ 已加载 {len(self.threads)} 个帖子 | 第{self.page}页 | "
                         f"[n]下一页 [p]上一页 [r]刷新 [Enter]查看")
            
        except Exception as e:
            status.update(f"❌ 加载失败：{str(e)}")
    
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





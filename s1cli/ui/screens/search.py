"""搜索界面"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Input, DataTable, Static, Footer, Header, Button
from textual.binding import Binding
from textual.containers import Container, Horizontal

from s1cli.api.search import SearchAPI


class SearchScreen(Screen):
    """搜索界面"""
    
    CSS = """
    SearchScreen {
        background: $surface;
    }
    
    #search-header {
        height: auto;
        background: $primary;
        color: $text;
        padding: 1;
        text-align: center;
        text-style: bold;
    }
    
    #search-input-container {
        height: auto;
        background: $panel;
        padding: 1;
    }
    
    Input {
        width: 1fr;
    }
    
    Button {
        width: auto;
        margin-left: 1;
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
        Binding("enter", "view_thread", "查看帖子"),
        Binding("ctrl+f", "focus_search", "聚焦搜索框"),
    ]
    
    def __init__(self, client, config):
        super().__init__()
        self.client = client
        self.config = config
        self.search_api = SearchAPI(client)
        self.results = []
    
    def compose(self) -> ComposeResult:
        """组装界面"""
        yield Header()
        yield Static("🔍 搜索帖子", id="search-header")
        with Container(id="search-input-container"):
            with Horizontal():
                yield Input(placeholder="输入搜索关键词...", id="search-input")
                yield Button("搜索", variant="primary", id="search-btn")
        yield DataTable(id="results-table", cursor_type="row")
        yield Static("", classes="status-bar", id="status-bar")
        yield Footer()
    
    def on_mount(self) -> None:
        """界面挂载时"""
        # 添加表格列
        table = self.query_one("#results-table", DataTable)
        table.add_columns("ID", "标题", "版块", "作者", "回复")
        
        # 聚焦到搜索框
        self.query_one("#search-input", Input).focus()
        
        # 更新状态栏
        status = self.query_one("#status-bar", Static)
        status.update("💡 输入关键词后按回车或点击搜索按钮")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        if event.button.id == "search-btn":
            self.action_search()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """处理输入框回车"""
        if event.input.id == "search-input":
            self.action_search()
    
    def action_search(self) -> None:
        """触发后台搜索"""
        search_input = self.query_one("#search-input", Input)
        keyword = search_input.value.strip()

        if not keyword:
            self.notify("请输入搜索关键词", severity="warning")
            return

        self._pending_keyword = keyword
        self.query_one("#status-bar", Static).update(f"🔄 正在搜索：{keyword}")
        self.run_worker(self._fetch_search, exclusive=True, thread=True)

    def _fetch_search(self) -> None:
        keyword = self._pending_keyword
        try:
            results = self.search_api.search(keyword)
        except Exception as e:
            self.app.call_from_thread(self._on_search_error, str(e))
            return
        self.app.call_from_thread(self._on_search_done, results)

    def _on_search_done(self, results) -> None:
        self.results = results
        table = self.query_one("#results-table", DataTable)
        status = self.query_one("#status-bar", Static)
        table.clear()

        if not results:
            status.update("❌ 没有找到相关结果")
            return

        for result in results:
            table.add_row(
                result.id,
                result.title[:50],
                result.forum or "未知",
                result.author,
                str(result.replies),
            )
        status.update(f"✅ 找到 {len(results)} 个结果 | [Enter]查看帖子")

    def _on_search_error(self, error: str) -> None:
        self.query_one("#status-bar", Static).update(f"❌ 搜索失败：{error}")
    
    def action_back(self) -> None:
        """返回"""
        self.dismiss()
    
    def action_focus_search(self) -> None:
        """聚焦搜索框"""
        self.query_one("#search-input", Input).focus()
    
    def action_view_thread(self) -> None:
        """查看选中的帖子"""
        table = self.query_one("#results-table", DataTable)
        
        if table.cursor_row is not None and self.results:
            try:
                row_index = table.cursor_row
                if row_index < len(self.results):
                    result = self.results[row_index]
                    self.notify(f"正在查看帖子：{result.title}")
                    # 这里可以跳转到帖子详情界面
            except Exception as e:
                self.notify(f"错误：{str(e)}", severity="error")





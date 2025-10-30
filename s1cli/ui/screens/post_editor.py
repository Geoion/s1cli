"""发帖和回帖编辑器"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Input, TextArea, Button, Static, Footer, Header
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal

from s1cli.api.thread import ThreadAPI


class PostEditorScreen(Screen):
    """发帖编辑器"""
    
    CSS = """
    PostEditorScreen {
        align: center middle;
    }
    
    #editor-container {
        width: 80;
        height: auto;
        border: solid $primary;
        padding: 2;
        background: $surface;
    }
    
    .editor-title {
        text-align: center;
        width: 100%;
        color: $primary;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .input-label {
        margin-top: 1;
        color: $text;
    }
    
    Input {
        width: 100%;
        margin-bottom: 1;
    }
    
    TextArea {
        width: 100%;
        height: 15;
        margin-bottom: 1;
    }
    
    .button-container {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    
    Button {
        margin: 0 1;
    }
    
    .status-message {
        text-align: center;
        height: 2;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "取消", priority=True),
        Binding("ctrl+s", "submit", "提交"),
    ]
    
    def __init__(self, client, config, forum_name: str):
        super().__init__()
        self.client = client
        self.config = config
        self.thread_api = ThreadAPI(client)
        self.forum_name = forum_name
    
    def compose(self) -> ComposeResult:
        """组装界面"""
        with Container(id="editor-container"):
            yield Static(f"📝 发帖到：{self.forum_name}", classes="editor-title")
            yield Static("标题:", classes="input-label")
            yield Input(placeholder="请输入帖子标题", id="title-input")
            yield Static("内容:", classes="input-label")
            yield TextArea(id="content-input")
            yield Static("", id="status-message", classes="status-message")
            with Horizontal(classes="button-container"):
                yield Button("发布", variant="primary", id="submit-btn")
                yield Button("取消", variant="default", id="cancel-btn")
        yield Footer()
    
    def on_mount(self) -> None:
        """界面挂载时，聚焦到标题输入框"""
        self.query_one("#title-input", Input).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        if event.button.id == "submit-btn":
            self.action_submit()
        elif event.button.id == "cancel-btn":
            self.action_cancel()
    
    def action_submit(self) -> None:
        """提交发帖"""
        title_input = self.query_one("#title-input", Input)
        content_input = self.query_one("#content-input", TextArea)
        message = self.query_one("#status-message", Static)
        
        title = title_input.value.strip()
        content = content_input.text.strip()
        
        # 验证输入
        if not title:
            message.update("❌ 请输入标题")
            title_input.focus()
            return
        
        if not content:
            message.update("❌ 请输入内容")
            content_input.focus()
            return
        
        # 显示发布中
        message.update("🔄 正在发布...")
        
        # 禁用按钮防止重复点击
        submit_btn = self.query_one("#submit-btn", Button)
        submit_btn.disabled = True
        
        try:
            # 执行发帖（这里需要论坛ID，简化处理使用名称）
            thread_id = self.thread_api.create_thread(
                self.forum_name, 
                title, 
                content
            )
            
            if thread_id:
                message.update(f"✅ 发帖成功！帖子ID：{thread_id}")
                # 延迟关闭
                self.set_timer(1.5, lambda: self.dismiss(thread_id))
            else:
                message.update("❌ 发帖失败")
                submit_btn.disabled = False
        except Exception as e:
            message.update(f"❌ 发帖出错：{str(e)}")
            submit_btn.disabled = False
    
    def action_cancel(self) -> None:
        """取消发帖"""
        self.dismiss(None)


class ReplyEditorScreen(Screen):
    """回帖编辑器"""
    
    CSS = """
    ReplyEditorScreen {
        align: center middle;
    }
    
    #editor-container {
        width: 80;
        height: auto;
        border: solid $primary;
        padding: 2;
        background: $surface;
    }
    
    .editor-title {
        text-align: center;
        width: 100%;
        color: $primary;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .input-label {
        margin-top: 1;
        color: $text;
    }
    
    TextArea {
        width: 100%;
        height: 15;
        margin-bottom: 1;
    }
    
    .button-container {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    
    Button {
        margin: 0 1;
    }
    
    .status-message {
        text-align: center;
        height: 2;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "取消", priority=True),
        Binding("ctrl+s", "submit", "提交"),
    ]
    
    def __init__(self, client, config, thread_id: str, thread_title: str):
        super().__init__()
        self.client = client
        self.config = config
        self.thread_api = ThreadAPI(client)
        self.thread_id = thread_id
        self.thread_title = thread_title
    
    def compose(self) -> ComposeResult:
        """组装界面"""
        with Container(id="editor-container"):
            yield Static(f"💬 回复：{self.thread_title}", classes="editor-title")
            yield Static("回复内容:", classes="input-label")
            yield TextArea(id="content-input")
            yield Static("", id="status-message", classes="status-message")
            with Horizontal(classes="button-container"):
                yield Button("发布", variant="primary", id="submit-btn")
                yield Button("取消", variant="default", id="cancel-btn")
        yield Footer()
    
    def on_mount(self) -> None:
        """界面挂载时，聚焦到内容输入框"""
        self.query_one("#content-input", TextArea).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        if event.button.id == "submit-btn":
            self.action_submit()
        elif event.button.id == "cancel-btn":
            self.action_cancel()
    
    def action_submit(self) -> None:
        """提交回复"""
        content_input = self.query_one("#content-input", TextArea)
        message = self.query_one("#status-message", Static)
        
        content = content_input.text.strip()
        
        # 验证输入
        if not content:
            message.update("❌ 请输入回复内容")
            content_input.focus()
            return
        
        # 显示发布中
        message.update("🔄 正在发布...")
        
        # 禁用按钮防止重复点击
        submit_btn = self.query_one("#submit-btn", Button)
        submit_btn.disabled = True
        
        try:
            # 执行回复
            post_id = self.thread_api.reply_thread(self.thread_id, content)
            
            if post_id:
                message.update(f"✅ 回复成功！")
                # 延迟关闭
                self.set_timer(1.5, lambda: self.dismiss(post_id))
            else:
                message.update("❌ 回复失败")
                submit_btn.disabled = False
        except Exception as e:
            message.update(f"❌ 回复出错：{str(e)}")
            submit_btn.disabled = False
    
    def action_cancel(self) -> None:
        """取消回复"""
        self.dismiss(None)


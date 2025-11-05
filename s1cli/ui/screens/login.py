"""登录界面"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Input, Button, Static, Label
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding

from s1cli.api.auth import AuthAPI


class LoginScreen(Screen):
    """登录界面"""
    
    CSS = """
    LoginScreen {
        align: center middle;
    }
    
    #login-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 2;
        background: $surface;
    }
    
    .login-title {
        text-align: center;
        width: 100%;
        color: $primary;
        text-style: bold;
    }
    
    .input-label {
        margin-top: 1;
        color: $text;
    }
    
    Input {
        width: 100%;
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
    
    .error-message {
        color: $error;
        text-align: center;
        height: 2;
    }
    
    .success-message {
        color: $success;
        text-align: center;
        height: 2;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "取消", priority=True),
    ]
    
    def __init__(self, client, config):
        super().__init__()
        self.client = client
        self.config = config
        self.auth = AuthAPI(client)
    
    def compose(self) -> ComposeResult:
        """组装界面"""
        with Container(id="login-container"):
            yield Static("🔐 登录 Stage1st", classes="login-title")
            yield Static("用户名:", classes="input-label")
            yield Input(placeholder="请输入用户名", id="username-input")
            yield Static("密码:", classes="input-label")
            yield Input(placeholder="请输入密码", password=True, id="password-input")
            yield Static("", id="message", classes="error-message")
            with Horizontal(classes="button-container"):
                yield Button("登录", variant="primary", id="login-btn")
                yield Button("取消", variant="default", id="cancel-btn")
    
    def on_mount(self) -> None:
        """界面挂载时，聚焦到用户名输入框"""
        self.query_one("#username-input", Input).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        if event.button.id == "login-btn":
            self.action_submit()
        elif event.button.id == "cancel-btn":
            self.action_cancel()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """处理输入框回车"""
        # 如果在用户名框按回车，跳到密码框
        if event.input.id == "username-input":
            self.query_one("#password-input", Input).focus()
        # 如果在密码框按回车，提交登录
        elif event.input.id == "password-input":
            self.action_submit()
    
    def action_submit(self) -> None:
        """提交登录"""
        username_input = self.query_one("#username-input", Input)
        password_input = self.query_one("#password-input", Input)
        message = self.query_one("#message", Static)
        
        username = username_input.value.strip()
        password = password_input.value.strip()
        
        # 验证输入
        if not username:
            message.update("❌ 请输入用户名")
            message.classes = "error-message"
            username_input.focus()
            return
        
        if not password:
            message.update("❌ 请输入密码")
            message.classes = "error-message"
            password_input.focus()
            return
        
        # 显示登录中
        message.update("🔄 正在登录...")
        message.classes = "success-message"
        
        # 禁用按钮防止重复点击
        login_btn = self.query_one("#login-btn", Button)
        login_btn.disabled = True
        
        try:
            # 执行登录
            success = self.auth.login(username, password)
            
            if success:
                message.update("✅ 登录成功！")
                message.classes = "success-message"
                # 延迟关闭，让用户看到成功消息
                self.set_timer(1.0, self.dismiss_success)
            else:
                message.update("❌ 登录失败，请检查用户名和密码")
                message.classes = "error-message"
                login_btn.disabled = False
                password_input.value = ""
                password_input.focus()
        except Exception as e:
            message.update(f"❌ 登录出错：{str(e)}")
            message.classes = "error-message"
            login_btn.disabled = False
    
    def dismiss_success(self) -> None:
        """登录成功后关闭界面"""
        self.dismiss(True)
    
    def action_cancel(self) -> None:
        """取消登录"""
        self.dismiss(False)





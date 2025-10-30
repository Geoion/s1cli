"""S1CLI 主入口"""
import sys
import click
from rich.console import Console

from s1cli.config import Config

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="0.1.0")
def cli(ctx):
    """S1CLI - Stage1st 论坛命令行工具
    
    一个功能完整的 Stage1st 论坛命令行客户端。
    
    \b
    常用命令示例：
    
    \b
    # 查看所有版块（带ID）
    s1cli list
    
    \b
    # 查看版块4（游戏论坛）的帖子
    s1cli list 4
    
    \b
    # 查看版块4的第2页
    s1cli list 4 -p 2
    
    \b
    # 查看帖子内容
    s1cli thread 2265995
    
    \b
    # 查看帖子的第2页回复
    s1cli thread 2265995 -p 2
    
    \b
    # 登录账号
    s1cli login
    
    \b
    # 发布新帖
    s1cli post -f 游戏论坛 -t "标题" -c "内容"
    
    \b
    # 回复帖子
    s1cli reply 2265995 -c "回复内容"
    
    \b
    # 搜索帖子
    s1cli search 宝可梦
    
    \b
    # 在指定版块内搜索
    s1cli search 塞尔达 -f 游戏论坛
    
    \b
    # 查看个人信息
    s1cli profile
    
    \b
    使用 's1cli <命令> --help' 查看具体命令的详细说明
    """
    if ctx.invoked_subcommand is None:
        # 不带参数时显示帮助信息
        click.echo(ctx.get_help())


@cli.command()
def tui():
    """启动图形界面"""
    from s1cli.ui.app import S1App
    
    console.print("[bold green]正在启动 S1CLI...[/bold green]")
    app = S1App()
    app.run()


@cli.command()
@click.option('--username', '-u', default=None, help='Stage1st 用户名')
@click.option('--password', '-p', default=None, help='密码')
def login(username, password):
    """登录 Stage1st 账号\n    -u 用户名\n    -p 密码"""
    from s1cli.api.auth import AuthAPI
    from s1cli.api.client import S1Client
    
    # 如果没有提供用户名，提示输入
    if not username:
        username = click.prompt('用户名', type=str)
    
    # 如果没有提供密码，提示输入
    if not password:
        password = click.prompt('密码', type=str, hide_input=True)
    
    console.print(f"[cyan]正在登录用户：{username}[/cyan]")
    
    config = Config()
    client = S1Client(config)
    auth = AuthAPI(client)
    
    try:
        if auth.login(username, password):
            console.print("[bold green]✓ 登录成功！[/bold green]")
        else:
            console.print("[bold red]✗ 登录失败，请检查用户名和密码[/bold red]")
            sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗ 登录出错：{e}[/bold red]")
        sys.exit(1)


@cli.command()
def logout():
    """登出并清除本地会话"""
    from s1cli.config import Config
    
    config = Config()
    config.clear_session()
    console.print("[bold green]✓ 已登出[/bold green]")


@cli.command()
@click.argument('forum_id_or_name', required=False)
@click.option('--page', '-p', default=1, help='页码（默认为第1页）')
@click.option('--json', 'output_json', is_flag=True, help='以 JSON 格式输出')
def list(forum_id_or_name, page, output_json):
    """列出版块（带ID）或帖子\n    -p 页码\n    --json JSON格式"""
    from s1cli.api.forum import ForumAPI
    from s1cli.api.client import S1Client
    from rich.table import Table
    import json
    
    config = Config()
    client = S1Client(config)
    forum_api = ForumAPI(client)
    
    if forum_id_or_name:
        # 判断是版块ID还是版块名
        forum_name = None
        
        if forum_id_or_name.isdigit():
            # 是版块ID，从缓存中查找对应的版块名
            forum_id = forum_id_or_name
            cached_forums = config.load_forum_list()
            
            if cached_forums:
                # 在缓存中查找匹配的版块ID
                for forum_data in cached_forums:
                    if forum_data['id'] == forum_id:
                        forum_name = forum_data['name']
                        console.print(f"[cyan]正在加载版块：[ID:{forum_id}] {forum_name} (第{page}页)[/cyan]")
                        break
                
                if not forum_name:
                    # 缓存中没找到，直接用ID尝试
                    forum_name = forum_id
                    console.print(f"[cyan]正在加载版块 ID：{forum_id} (第{page}页)[/cyan]")
            else:
                # 没有缓存，直接用ID
                forum_name = forum_id
                console.print(f"[cyan]正在加载版块 ID：{forum_id} (第{page}页)[/cyan]")
        else:
            # 是版块名称
            forum_name = forum_id_or_name
            console.print(f"[cyan]正在加载版块：{forum_name} (第{page}页)[/cyan]")
        
        # 列出指定版块的帖子
        threads = forum_api.get_thread_list(forum_name, page)
        
        if output_json:
            click.echo(json.dumps([t.__dict__ for t in threads], ensure_ascii=False, indent=2))
        else:
            table = Table(title=f"{forum_name} - 第{page}页")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("标题", style="white")
            table.add_column("作者", style="green", no_wrap=True)
            table.add_column("回复", style="yellow", justify="right", no_wrap=True)
            table.add_column("查看", style="blue", justify="right", no_wrap=True)
            table.add_column("最后回复者", style="magenta", no_wrap=True)
            table.add_column("最后回复时间", style="dim", no_wrap=True)
            
            def format_time(time_str):
                """格式化时间为 YYMMDD hh:mm"""
                if not time_str:
                    return "-"
                try:
                    # 解析时间格式 "2025-10-28 10:06"
                    from datetime import datetime
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    return dt.strftime("%y%m%d %H:%M")
                except:
                    # 如果解析失败，返回原始时间或简化版本
                    if len(time_str) >= 16:
                        # 尝试简单截取 "2025-10-28 10:06" -> "251028 10:06"
                        try:
                            parts = time_str.split()
                            if len(parts) >= 2:
                                date_part = parts[0].replace('-', '')[2:]  # "2025-10-28" -> "251028"
                                time_part = parts[1][:5]  # "10:06"
                                return f"{date_part} {time_part}"
                        except:
                            pass
                    return time_str[:13] if len(time_str) > 13 else time_str
            
            for thread in threads:
                table.add_row(
                    str(thread.id),
                    thread.title,
                    thread.author,
                    str(thread.replies),
                    f"{thread.views:,}" if thread.views > 0 else "-",
                    thread.last_reply_author or "-",
                    format_time(thread.last_reply_time)
                )
            
            console.print(table)
            console.print("\n[dim]提示：使用 's1cli thread <ID>' 查看该帖子[/dim]")
    else:
        # 列出所有版块
        console.print("[cyan]正在加载版块列表...[/cyan]")
        forums = forum_api.get_forum_list()
        
        # 保存到缓存
        config.save_forum_list(forums)
        
        if output_json:
            click.echo(json.dumps([f.__dict__ for f in forums], ensure_ascii=False, indent=2))
        else:
            table = Table(title="Stage1st 论坛版块")
            table.add_column("ID", style="yellow", justify="right", no_wrap=True)
            table.add_column("版块名称", style="cyan", no_wrap=True)
            table.add_column("主题数", style="white", justify="right")
            table.add_column("帖子数", style="white", justify="right")
            table.add_column("新帖", style="bold red", justify="right")
            
            for f in forums:
                # 格式化主题数和帖子数
                threads_str = f"{f.threads_count:,}" if f.threads_count > 0 else "-"
                posts_str = f"{f.posts_count:,}" if f.posts_count > 0 else "-"
                new_posts_str = f"[bold red]{f.new_posts}[/bold red]" if f.new_posts > 0 else "-"
                
                table.add_row(f.id, f.name, threads_str, posts_str, new_posts_str)
            
            console.print(table)
            console.print("\n[dim]提示：使用 's1cli list <ID>' 查看该版块的帖子列表[/dim]")


@cli.command()
@click.argument('thread_id')
@click.option('--page', '-p', default=1, help='页码')
def thread(thread_id, page):
    """查看帖子内容和回复\n    -p 页码"""
    from s1cli.api.thread import ThreadAPI
    from s1cli.api.client import S1Client
    from rich.panel import Panel
    from rich.rule import Rule
    
    config = Config()
    client = S1Client(config)
    thread_api = ThreadAPI(client)
    
    console.print(f"[cyan]正在加载帖子：{thread_id} (第{page}页)[/cyan]")
    thread = thread_api.get_thread(thread_id, page)
    
    # 检查页码是否超出范围
    if thread.current_page > thread.total_pages:
        console.print(f"[bold yellow]⚠ 警告：请求的页码（{thread.current_page}）超出总页数（{thread.total_pages}），显示的是第{thread.total_pages}页的内容[/bold yellow]\n")
    
    # 显示帖子标题和内容
    post_time_str = f" | 发帖时间：{thread.created_at}" if thread.created_at else ""
    page_info_str = f" | 第{thread.current_page}/{thread.total_pages}页" if thread.total_pages > 1 else ""
    console.print(Panel(
        f"[bold]{thread.title}[/bold]\n"
        f"作者：{thread.author}{post_time_str} | 查看：{thread.views} | 回复：{thread.replies}{page_info_str}",
        title="帖子信息"
    ))
    
    # 显示楼主内容
    console.print(Panel(thread.content, title="楼主", border_style="green"))
    
    # 显示回复
    if thread.posts:
        console.print()  # 空行
        for i, post in enumerate(thread.posts):
            console.print(f"[bold cyan]#{post.floor}楼[/bold cyan] [dim]{post.author} @ {post.post_time}[/dim]")
            console.print(post.content)
            if i < len(thread.posts) - 1:  # 不是最后一个回复
                console.print(Rule(style="dim"))  # 分割线，自动适应窗口宽度
    
    # 在底部显示分页提示
    if thread.total_pages > 1:
        nav_hint = ""
        if thread.current_page < thread.total_pages:
            nav_hint = f"[dim]下一页：s1cli thread {thread_id} -p {thread.current_page + 1}[/dim]"
        elif thread.current_page == thread.total_pages:
            nav_hint = f"[dim]已是最后一页[/dim]"
        if nav_hint:
            console.print(f"\n{nav_hint}")


@cli.command()
@click.argument('thread_id')
@click.option('--page', '-p', default=1, help='页码')
def view(thread_id, page):
    """查看帖子（旧命令，推荐使用 s1cli thread）"""
    from s1cli.api.thread import ThreadAPI
    from s1cli.api.client import S1Client
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.rule import Rule
    
    config = Config()
    client = S1Client(config)
    thread_api = ThreadAPI(client)
    
    console.print(f"[cyan]正在加载帖子：{thread_id} (第{page}页)[/cyan]")
    thread = thread_api.get_thread(thread_id, page)
    
    # 检查页码是否超出范围
    if thread.current_page > thread.total_pages:
        console.print(f"[bold yellow]⚠ 警告：请求的页码（{thread.current_page}）超出总页数（{thread.total_pages}），显示的是第{thread.total_pages}页的内容[/bold yellow]\n")
    
    # 显示帖子标题和内容
    post_time_str = f" | 发帖时间：{thread.created_at}" if thread.created_at else ""
    page_info_str = f" | 第{thread.current_page}/{thread.total_pages}页" if thread.total_pages > 1 else ""
    console.print(Panel(
        f"[bold]{thread.title}[/bold]\n"
        f"作者：{thread.author}{post_time_str} | 查看：{thread.views} | 回复：{thread.replies}{page_info_str}",
        title="帖子信息"
    ))
    
    # 显示楼主内容
    console.print(Panel(thread.content, title="楼主", border_style="green"))
    
    # 显示回复
    if thread.posts:
        console.print()  # 空行
        for i, post in enumerate(thread.posts):
            console.print(f"[bold cyan]#{post.floor}楼[/bold cyan] [dim]{post.author} @ {post.post_time}[/dim]")
            console.print(post.content)
            if i < len(thread.posts) - 1:  # 不是最后一个回复
                console.print(Rule(style="dim"))  # 分割线，自动适应窗口宽度
    
    # 在底部显示分页提示
    if thread.total_pages > 1:
        nav_hint = ""
        if thread.current_page < thread.total_pages:
            nav_hint = f"[dim]下一页：s1cli thread {thread_id} -p {thread.current_page + 1}[/dim]"
        elif thread.current_page == thread.total_pages:
            nav_hint = f"[dim]已是最后一页[/dim]"
        if nav_hint:
            console.print(f"\n{nav_hint}")


@cli.command()
@click.option('--forum', '-f', required=True, help='论坛版块名称')
@click.option('--title', '-t', required=True, help='帖子标题')
@click.option('--content', '-c', required=True, help='帖子内容')
def post(forum, title, content):
    """发布新帖\n    -f 版块名\n    -t 标题\n    -c 内容"""
    from s1cli.api.thread import ThreadAPI
    from s1cli.api.client import S1Client
    
    config = Config()
    client = S1Client(config)
    thread_api = ThreadAPI(client)
    
    console.print(f"[cyan]正在发布帖子到：{forum}[/cyan]")
    
    try:
        thread_id = thread_api.create_thread(forum, title, content)
        console.print(f"[bold green]✓ 发帖成功！帖子ID：{thread_id}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]✗ 发帖失败：{e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.argument('thread_id')
@click.option('--content', '-c', required=True, help='回复内容')
def reply(thread_id, content):
    """回复帖子\n    -c 回复内容"""
    from s1cli.api.thread import ThreadAPI
    from s1cli.api.client import S1Client
    
    config = Config()
    client = S1Client(config)
    thread_api = ThreadAPI(client)
    
    console.print(f"[cyan]正在回复帖子：{thread_id}[/cyan]")
    
    try:
        post_id = thread_api.reply_thread(thread_id, content)
        console.print(f"[bold green]✓ 回复成功！回复ID：{post_id}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]✗ 回复失败：{e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.argument('keyword')
@click.option('--forum', '-f', help='限定搜索的版块')
def search(keyword, forum):
    """搜索帖子\n    -f 限定版块（可选）"""
    from s1cli.api.search import SearchAPI
    from s1cli.api.client import S1Client
    from rich.table import Table
    
    config = Config()
    client = S1Client(config)
    search_api = SearchAPI(client)
    
    console.print(f"[cyan]正在搜索：{keyword}[/cyan]")
    results = search_api.search(keyword, forum)
    
    table = Table(title=f"搜索结果：{keyword}")
    table.add_column("ID", style="cyan")
    table.add_column("标题", style="white")
    table.add_column("版块", style="green")
    table.add_column("作者", style="yellow")
    
    for result in results:
        table.add_row(
            str(result.id),
            result.title,
            result.forum or "",
            result.author
        )
    
    console.print(table)


@cli.command()
@click.option('--ua', is_flag=True, help='显示 User Agent 信息')
@click.option('-e', '--expire', 'show_expire', is_flag=True, help='显示会话过期信息')
def debug(ua, show_expire):
    """调试信息\n    --ua 查看UA\n    -e 查看过期时间"""
    from s1cli.api.client import S1Client
    from rich.panel import Panel
    from datetime import datetime, timedelta
    
    config = Config()
    
    if ua:
        # 显示 User Agent 信息
        client = S1Client(config)
        console.print(Panel(
            f"[bold cyan]User Agent:[/bold cyan]\n{client.USER_AGENT}\n\n"
            f"[bold cyan]Base URL:[/bold cyan]\n{client.BASE_URL}",
            title="User Agent 信息",
            border_style="cyan"
        ))
    
    if show_expire:
        # 显示会话过期信息
        session = config.get_session()
        
        if not session or not session.get('cookies'):
            console.print(Panel(
                "[yellow]当前未登录，无会话信息[/yellow]",
                title="会话信息",
                border_style="yellow"
            ))
        else:
            user_info = session.get('user', {})
            username = user_info.get('username', '未知')
            created_at = session.get('created_at', '未知')
            expires_in = session.get('expires_in', 7 * 24 * 3600)
            
            # 计算过期时间
            try:
                created_dt = datetime.fromisoformat(created_at)
                expire_dt = created_dt + timedelta(seconds=expires_in)
                now = datetime.now()
                remaining = expire_dt - now
                
                if remaining.total_seconds() > 0:
                    days = remaining.days
                    hours = remaining.seconds // 3600
                    status = f"[green]有效（剩余 {days}天 {hours}小时）[/green]"
                else:
                    status = "[red]已过期[/red]"
                
                expire_str = expire_dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                expire_str = "解析失败"
                status = "[yellow]未知[/yellow]"
            
            console.print(Panel(
                f"[bold cyan]用户名:[/bold cyan] {username}\n"
                f"[bold cyan]登录时间:[/bold cyan] {created_at}\n"
                f"[bold cyan]过期时间:[/bold cyan] {expire_str}\n"
                f"[bold cyan]状态:[/bold cyan] {status}",
                title="会话信息",
                border_style="cyan"
            ))
    
    if not ua and not show_expire:
        # 如果没有指定参数，显示所有信息
        console.print("[yellow]请使用 --ua 或 -e 参数查看调试信息[/yellow]")
        console.print("[dim]示例：s1cli debug --ua  或  s1cli debug -e[/dim]")


@cli.command()
def checkin():
    """每日签到"""
    from s1cli.api.client import S1Client
    
    config = Config()
    client = S1Client(config)
    
    console.print("[cyan]正在签到...[/cyan]")
    # TODO: 实现签到功能
    console.print("[bold yellow]签到功能开发中...[/bold yellow]")


@cli.command()
def profile():
    """查看个人信息"""
    from s1cli.api.auth import AuthAPI
    from s1cli.api.client import S1Client
    from rich.panel import Panel
    
    config = Config()
    client = S1Client(config)
    auth = AuthAPI(client)
    
    if not auth.check_login():
        console.print("[bold red]✗ 未登录，请先使用 's1cli login' 登录[/bold red]")
        sys.exit(1)
    
    user_info = auth.get_user_info()
    
    console.print(Panel(
        f"[bold]用户名：[/bold]{user_info.get('username', 'N/A')}\n"
        f"[bold]UID：[/bold]{user_info.get('uid', 'N/A')}\n"
        f"[bold]积分：[/bold]{user_info.get('credits', 'N/A')}",
        title="个人信息"
    ))


@cli.group()
def config():
    """配置管理"""
    pass


@config.command('show')
def config_show():
    """显示当前配置"""
    from s1cli.config import Config
    import json
    
    cfg = Config()
    console.print(json.dumps(cfg.get_all(), ensure_ascii=False, indent=2))


@config.command('set')
@click.argument('key_value')
def config_set(key_value):
    """设置配置项（格式：key=value）"""
    from s1cli.config import Config
    
    if '=' not in key_value:
        console.print("[bold red]✗ 格式错误，请使用：key=value[/bold red]")
        sys.exit(1)
    
    key, value = key_value.split('=', 1)
    cfg = Config()
    cfg.set(key, value)
    console.print(f"[bold green]✓ 已设置 {key} = {value}[/bold green]")


def main():
    """主入口函数"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]已取消[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]错误：{e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()


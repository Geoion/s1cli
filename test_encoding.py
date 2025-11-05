#!/usr/bin/env python3
"""测试 Windows 编码支持"""
import sys
import os

# 应用与 __main__.py 相同的编码设置
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        os.system('chcp 65001 > nul 2>&1')
    except:
        pass
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from rich.console import Console

console = Console()

def test_encoding():
    """测试各种中文字符的显示"""
    
    print("\n" + "="*60)
    print("S1CLI Windows 编码测试")
    print("="*60 + "\n")
    
    # 测试 1: 普通 print
    print("✅ 测试 1 - 标准 print 输出:")
    print("  中文字符: 你好，世界！")
    print("  特殊符号: ✓ ✗ → ← ↑ ↓")
    print("  Emoji: 🎮 🎯 📱 💻")
    print()
    
    # 测试 2: Rich Console
    console.print("✅ 测试 2 - Rich Console 输出:")
    console.print("  [bold green]绿色粗体中文[/bold green]")
    console.print("  [cyan]青色中文字符[/cyan]")
    console.print("  [yellow]黄色警告信息[/yellow]")
    console.print()
    
    # 测试 3: 模拟论坛内容
    console.print("✅ 测试 3 - 模拟论坛内容:")
    console.print("  标题: [bold]关于《塞尔达传说：王国之泪》的讨论[/bold]")
    console.print("  作者: [cyan]测试用户[/cyan]")
    console.print("  内容: 这是一段包含中文的测试内容。包括标点符号：，。！？；：""''")
    console.print()
    
    # 测试 4: 系统信息
    console.print("✅ 测试 4 - 系统信息:")
    console.print(f"  平台: {sys.platform}")
    console.print(f"  Python 版本: {sys.version.split()[0]}")
    console.print(f"  默认编码: {sys.getdefaultencoding()}")
    console.print(f"  文件系统编码: {sys.getfilesystemencoding()}")
    if hasattr(sys.stdout, 'encoding'):
        console.print(f"  stdout 编码: {sys.stdout.encoding}")
    if hasattr(sys.stderr, 'encoding'):
        console.print(f"  stderr 编码: {sys.stderr.encoding}")
    console.print()
    
    # 测试 5: 表格显示
    from rich.table import Table
    
    table = Table(title="测试表格 - 论坛版块")
    table.add_column("版块名称", style="cyan")
    table.add_column("帖子数", style="magenta")
    table.add_column("状态", style="green")
    
    table.add_row("游戏论坛", "12,345", "✓ 正常")
    table.add_row("动漫论坛", "8,901", "✓ 正常")
    table.add_row("技术讨论", "5,678", "✓ 正常")
    
    console.print("✅ 测试 5 - 表格显示:")
    console.print(table)
    console.print()
    
    # 总结
    console.print("[bold green]✅ 所有测试完成！[/bold green]")
    console.print("[yellow]如果您能看到上面所有的中文字符、特殊符号和表格，说明编码配置成功！[/yellow]")
    console.print()
    
    if sys.platform == 'win32':
        console.print("[cyan]Windows 用户提示:[/cyan]")
        console.print("  1. 如果看到乱码，请确保使用 Windows Terminal 或新版 PowerShell")
        console.print("  2. 避免使用旧版 CMD（不支持 UTF-8）")
        console.print("  3. Windows 10 1903+ 可在 '区域设置' 中启用 'UTF-8 全球语言支持'")
        console.print()

if __name__ == "__main__":
    try:
        test_encoding()
    except Exception as e:
        console.print(f"[bold red]测试失败: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)



"""
交互式 API 诊断 CLI

启动后在终端中输入 API 信息，实时获得诊断结果
"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src import APIDiagnosisSystem
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.syntax import Syntax

console = Console()


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔════════════════════════════════════════════════════════════════╗
║║                                                              ║
║║  🚀 API Bug 智能诊断系统 v1.0                                ║
║║                                                              ║
║║  基于 LangChain 的多 Agent 系统                                   ║
║║  - 语义分析 │ 根因诊断 │ 修复建议 │ 测试生成              ║
║║                                                              ║
╚════════════════════════════════════════════════════════════════╝

输入 'help' 查看帮助 | 输入 'exit' 退出
"""
    console.print(banner)


def print_help():
    """打印帮助信息"""
    help_table = Table(title="使用帮助")
    help_table.add_column("命令", style="cyan", width=15)
    help_table.add_column("说明", style="green")

    help_table.add_row("start", "开始输入 API 数据进行诊断")
    help_table.add_row("example", "查看示例输入格式")
    help_table.add_row("config", "查看/修改配置")
    help_table.add_row("history", "查看历史诊断记录")
    help_table.add_row("clear", "清屏")
    help_table.add_row("exit", "退出程序")
    help_table.add_row("quit", "退出程序")

    console.print(help_table)


def print_example():
    """打印示例格式"""
    example = """{
  "request": {
    "method": "POST",
    "url": "https://api.example.com/users",
    "headers": {
      "Content-Type": "application/json"
    },
    "body": {
      "name": "John",
      "email": "john@example.com"
    }
  },
  "response": {
    "status_code": 500,
    "body": {
      "error": "Internal Server Error",
      "message": "Database connection failed"
    }
  },
  "log": "[ERROR] Database connection timeout..."
}"""
    console.print(Panel(
        Syntax(example, "json"),
        title="JSON 输入格式示例",
        border_style="blue"
    ))


async def interactive_diagnosis():
    """交互式诊断主循环"""

    print_banner()

    # 初始化诊断系统
    try:
        console.print("[green]正在初始化诊断系统...[/green]")
        system = APIDiagnosisSystem()
        console.print("[green]✓ 系统初始化完成[/green]\n")
    except Exception as e:
        console.print(f"[red]✗ 系统初始化失败: {e}[/red]")
        return

    # 诊断历史
    history = []

    while True:
        try:
            # 显示提示符
            user_input = console.input(
                "[bold cyan]api-diagnosis[/bold cyan] > ",
                password=False
            ).strip()

            # 处理空输入
            if not user_input:
                continue

            # 处理命令
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("[yellow]感谢使用，再见！[/yellow]")
                break

            elif user_input.lower() == 'help':
                print_help()
                continue

            elif user_input.lower() == 'example':
                print_example()
                continue

            elif user_input.lower() == 'clear':
                if sys.platform == 'win32':
                    os.system('cls')
                else:
                    os.system('clear')
                print_banner()
                continue

            elif user_input.lower() == 'history':
                if not history:
                    console.print("[yellow]暂无历史记录[/yellow]")
                else:
                    history_table = Table(title="诊断历史")
                    history_table.add_column("序号", width=5)
                    history_table.add_column("时间", width=20)
                    history_table.add_column("状态码", width=10)
                    history_table.add_column("错误类别", width=15)

                    for i, h in enumerate(history, 1):
                        history_table.add_row(
                            str(i),
                            h['time'].split('.')[0],
                            str(h.get('status_code', 'N/A')),
                            str(h.get('error_category', 'N/A'))
                        )
                    console.print(history_table)
                continue

            # 尝试解析为 JSON
            try:
                api_data = json.loads(user_input)
            except json.JSONDecodeError:
                console.print("[red]✗ 输入格式错误，请使用 JSON 格式[/red]")
                console.print("[yellow]输入 'example' 查看格式示例[/yellow]")
                continue

            # 执行诊断
            console.print("\n[blue]🔍 开始分析...[/blue]")

            try:
                with console.status("[bold]正在诊断中...[/bold]"):
                    report = await system.diagnose(api_data)

                # 诊断成功，显示结果
                console.print("\n[green]✓ 诊断完成[/green]\n")

                # 创建结果表格
                result_table = Table()
                result_table.add_column("项目", style="cyan", width=20)
                result_table.add_column("结果")

                # 基本信息
                result_table.add_row(
                    "报告 ID",
                    f"[yellow]{report.report_id}[/yellow]"
                )
                result_table.add_row(
                    "错误类别",
                    str(report.semantic_analysis.error_category)
                )
                result_table.add_row(
                    "严重程度",
                    f"[red]{report.overall_severity}[/red]" if 'CRITICAL' in str(report.overall_severity) or 'HIGH' in str(report.overall_severity) else f"[yellow]{report.overall_severity}[/yellow]"
                )

                console.print(Panel(result_table, title="诊断摘要"))

                # 根因分析
                console.print(f"\n[bold]🎯 根因分析:[/bold]")
                console.print(f"   {report.root_cause_analysis.root_cause_description}")

                console.print(f"\n[bold]🔧 修复建议:[/bold]")
                for i, suggestion in enumerate(report.fix_strategy.suggestions, 1):
                    console.print(f"   {i}. {suggestion}")

                console.print(f"\n[bold]✅ 测试用例:[/bold]")
                console.print(f"   生成了 {len(report.test_suite.test_cases)} 个测试用例")

                # 添加到历史
                history.append({
                    'time': str(report.timestamp),
                    'status_code': api_data.get('response', {}).get('status_code'),
                    'error_category': report.semantic_analysis.error_category
                })

                console.print("\n[green]" + "="*50 + "[/green]\n")

            except Exception as e:
                console.print(f"[red]✗ 诊断失败: {e}[/red]")
                continue

        except KeyboardInterrupt:
            console.print("\n[yellow]已中断操作[/yellow]")
            continue
        except EOFError:
            console.print("\n[yellow]感谢使用，再见！[/yellow]")
            break


def main():
    """主函数"""
    try:
        asyncio.run(interactive_diagnosis())
    except Exception as e:
        console.print(f"[red]程序错误: {e}[/red]")


if __name__ == "__main__":
    main()

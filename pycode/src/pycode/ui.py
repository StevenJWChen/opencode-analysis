"""
Terminal UI Module

Provides rich terminal UI components for enhanced user experience:
- Progress indicators for tool execution
- Syntax highlighting for code output
- Formatted panels and displays
- Status indicators
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.live import Live
from rich.markdown import Markdown
from rich import box
import time


console = Console()


class TerminalUI:
    """Enhanced terminal UI for PyCode"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.console = console
        self.current_progress: Optional[Progress] = None
        self.current_task = None

    def print_header(self, agent_name: str, tool_count: int, user_request: str):
        """Print session header"""
        if not self.verbose:
            return

        # Create header panel
        header_content = f"""
[bold cyan]Agent:[/bold cyan] {agent_name}
[bold cyan]Available Tools:[/bold cyan] {tool_count}
[bold cyan]Request:[/bold cyan] {user_request}
"""

        panel = Panel(
            header_content.strip(),
            title="[bold]🚀 PyCode Session Started[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )

        self.console.print("\n")
        self.console.print(panel)
        self.console.print()

    def print_iteration(self, iteration: int):
        """Print iteration marker"""
        if not self.verbose:
            return

        self.console.print(f"\n[bold yellow]{'─' * 60}[/bold yellow]")
        self.console.print(f"[bold yellow]Iteration {iteration}[/bold yellow]")
        self.console.print(f"[bold yellow]{'─' * 60}[/bold yellow]\n")

    def print_tool_calls(self, count: int):
        """Print tool call notification"""
        if not self.verbose:
            return

        self.console.print(f"\n[bold blue]🔧 LLM requested {count} tool call(s)[/bold blue]\n")

    def print_tool_execution(self, tool_name: str, tool_args: dict):
        """Print tool execution start"""
        if not self.verbose:
            return

        # Create a nice display of the tool call
        table = Table(
            show_header=False,
            box=box.SIMPLE,
            padding=(0, 1),
            border_style="blue"
        )

        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Tool", f"[bold]{tool_name}[/bold]")

        # Add arguments
        for key, value in tool_args.items():
            # Truncate long values
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."

            table.add_row(f"  {key}", value_str)

        panel = Panel(
            table,
            title="[bold blue]🔧 Executing Tool[/bold blue]",
            border_style="blue",
            box=box.ROUNDED,
        )

        self.console.print(panel)

    def print_tool_result(self, title: str, output: Optional[str], error: Optional[str]):
        """Print tool execution result"""
        if not self.verbose:
            return

        if error:
            # Error result
            self.console.print(f"[bold red]❌ Error:[/bold red] {error}\n")
        else:
            # Success result
            self.console.print(f"[bold green]✅ {title}[/bold green]")

            if output:
                # Show output with potential syntax highlighting
                preview = output[:300]
                if len(output) > 300:
                    preview += "\n..."

                # Try to detect if it's code
                if self._looks_like_code(preview):
                    # Syntax highlight
                    syntax = Syntax(
                        preview,
                        self._guess_language(preview),
                        theme="monokai",
                        line_numbers=False,
                        word_wrap=True,
                    )
                    self.console.print(Panel(
                        syntax,
                        title="Output",
                        border_style="green",
                        box=box.ROUNDED,
                    ))
                else:
                    # Regular text
                    self.console.print(f"[dim]{preview}[/dim]")

            self.console.print()

    def print_completion(self, iteration_count: int):
        """Print task completion"""
        if not self.verbose:
            return

        panel = Panel(
            f"[bold green]Task completed successfully after {iteration_count} iteration(s)[/bold green]",
            title="[bold]✅ Success[/bold]",
            border_style="green",
            box=box.ROUNDED,
        )

        self.console.print("\n")
        self.console.print(panel)
        self.console.print()

    def print_doom_loop(self, tool_name: str):
        """Print doom loop warning"""
        warning_text = f"""
[bold red]⚠️  DOOM LOOP DETECTED![/bold red]

The agent is repeating the same action: [bold]{tool_name}[/bold]

This usually means the current approach isn't working.
Breaking the loop to prevent infinite execution.
"""

        panel = Panel(
            warning_text.strip(),
            title="[bold red]⚠️  Warning[/bold red]",
            border_style="red",
            box=box.DOUBLE,
        )

        self.console.print("\n")
        self.console.print(panel)
        self.console.print()

    def print_max_iterations(self, max_iterations: int):
        """Print max iterations warning"""
        panel = Panel(
            f"[bold yellow]Reached maximum iterations ({max_iterations})[/bold yellow]",
            title="[bold]⚠️  Limit Reached[/bold]",
            border_style="yellow",
            box=box.ROUNDED,
        )

        self.console.print("\n")
        self.console.print(panel)
        self.console.print()

    def print_llm_error(self, error: str):
        """Print LLM error"""
        panel = Panel(
            f"[bold red]Error:[/bold red] {error}",
            title="[bold red]❌ LLM Error[/bold red]",
            border_style="red",
            box=box.ROUNDED,
        )

        self.console.print("\n")
        self.console.print(panel)
        self.console.print()

    def print_code(self, code: str, language: str = "python", title: str = "Code"):
        """Print syntax-highlighted code"""
        syntax = Syntax(
            code,
            language,
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )

        panel = Panel(
            syntax,
            title=f"[bold]{title}[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )

        self.console.print(panel)

    def print_markdown(self, md_text: str):
        """Print formatted markdown"""
        md = Markdown(md_text)
        self.console.print(md)

    def create_progress(self, description: str = "Processing...") -> Progress:
        """Create a progress indicator"""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        )
        return progress

    def start_spinner(self, description: str = "Working..."):
        """Start a spinner for indeterminate progress"""
        self.current_progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=self.console,
            transient=True,
        )
        self.current_progress.start()
        self.current_task = self.current_progress.add_task(description, total=None)

    def stop_spinner(self):
        """Stop the current spinner"""
        if self.current_progress:
            self.current_progress.stop()
            self.current_progress = None
            self.current_task = None

    def print_table(self, title: str, headers: list[str], rows: list[list[str]]):
        """Print a formatted table"""
        table = Table(
            title=title,
            box=box.ROUNDED,
            border_style="cyan",
        )

        for header in headers:
            table.add_column(header, style="cyan")

        for row in rows:
            table.add_row(*row)

        self.console.print(table)

    def _looks_like_code(self, text: str) -> bool:
        """Heuristic to detect if text looks like code"""
        code_indicators = [
            "def ", "class ", "import ", "from ",  # Python
            "function ", "const ", "let ", "var ",  # JavaScript
            "public ", "private ", "void ", "int ",  # Java/C++
            "{", "}", "=>", "->",  # General code symbols
            "if (", "for (", "while (",  # Control structures
        ]

        return any(indicator in text for indicator in code_indicators)

    def _guess_language(self, text: str) -> str:
        """Guess programming language from code text"""
        if "def " in text or "import " in text:
            return "python"
        elif "function " in text or "const " in text:
            return "javascript"
        elif "public class" in text or "void " in text:
            return "java"
        elif "#include" in text:
            return "cpp"
        elif "package " in text and "func " in text:
            return "go"
        else:
            return "python"  # Default

    def print_status(self, status: str, style: str = "green"):
        """Print a status message"""
        self.console.print(f"[{style}]{status}[/{style}]")

    def print_separator(self):
        """Print a visual separator"""
        self.console.print(f"\n[dim]{'─' * 80}[/dim]\n")


# Global UI instance
ui = TerminalUI()


def get_ui(verbose: bool = True) -> TerminalUI:
    """Get or create UI instance"""
    global ui
    ui.verbose = verbose
    return ui

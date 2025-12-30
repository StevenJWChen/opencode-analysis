"""Main CLI entry point"""

import click
import asyncio
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


@click.group(invoke_without_command=True)
@click.option("--agent", default="build", help="Agent to use (build/plan)")
@click.option("--model", help="Model to use (provider/model)")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx, agent, model, debug):
    """PyCode - AI Coding Agent in Python

    A Python implementation of an AI coding agent inspired by OpenCode.
    """
    ctx.ensure_object(dict)
    ctx.obj["agent"] = agent
    ctx.obj["model"] = model
    ctx.obj["debug"] = debug

    if ctx.invoked_subcommand is None:
        # Interactive mode
        console.print(
            Panel.fit(
                "[bold blue]PyCode[/bold blue] - AI Coding Agent\n"
                "Type your request or use --help for options",
                border_style="blue",
            )
        )


@cli.command()
@click.argument("message", nargs=-1)
@click.pass_context
def run(ctx, message):
    """Run PyCode with a message"""
    message_text = " ".join(message)

    if not message_text:
        console.print("[yellow]No message provided. Use: pycode run \"your message\"[/yellow]")
        return

    console.print(f"\n[bold]User:[/bold] {message_text}\n")

    # This is a placeholder - full implementation would involve:
    # 1. Load agent configuration
    # 2. Initialize provider
    # 3. Create session
    # 4. Stream LLM response
    # 5. Execute tools
    # 6. Display results

    console.print(
        "[yellow]PyCode implementation is a working prototype. "
        "Full streaming and tool execution requires additional integration.[/yellow]\n"
    )

    console.print(
        Markdown(
            """
### Example Usage

```bash
# Start interactive session
pycode

# Run with a message
pycode run "Help me understand this codebase"

# Use plan agent
pycode --agent plan run "Analyze the project structure"

# Use specific model
pycode --model anthropic/claude-3-7-sonnet run "Refactor this code"
```

### Architecture

The implementation includes:
- ✅ Core data structures (Session, Message, Identifier)
- ✅ Agent system (Build, Plan agents)
- ✅ Tool system (Bash, Read, Edit, Grep)
- ✅ Provider integrations (Anthropic, OpenAI)
- ✅ Storage layer (file-based JSON)
- ⚠️  CLI interface (basic implementation)
- ⚠️  Streaming processor (needs integration)

### Next Steps

To complete the implementation:
1. Implement LLM streaming processor
2. Integrate tool execution loop
3. Add permission dialogs
4. Build interactive TUI with Rich
5. Add configuration management
"""
        )
    )


@cli.command()
def models():
    """List available models"""
    console.print("[bold]Available Models:[/bold]\n")

    console.print("[cyan]Anthropic:[/cyan]")
    console.print("  - claude-3-7-sonnet-20250219")
    console.print("  - claude-3-5-sonnet-20241022")
    console.print("  - claude-3-5-haiku-20241022\n")

    console.print("[cyan]OpenAI:[/cyan]")
    console.print("  - gpt-4o")
    console.print("  - gpt-4o-mini")
    console.print("  - gpt-4-turbo\n")


@cli.command()
def version():
    """Show version information"""
    from pycode import __version__

    console.print(f"[bold]PyCode[/bold] version {__version__}")
    console.print("A Python implementation inspired by OpenCode")


def main():
    """Entry point for CLI"""
    cli(obj={})


if __name__ == "__main__":
    main()

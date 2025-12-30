"""
CLI Commands

Implements PyCode command-line interface commands.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from ..config import ConfigManager, load_config
from ..session_manager import SessionManager
from ..history import MessageHistory
from ..storage import Storage
from ..core import Session
from ..agents import BuildAgent, PlanAgent
from ..tools import ToolRegistry
from ..runner import AgentRunner, RunConfig


console = Console()


class Commands:
    """PyCode CLI commands"""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.storage = Storage()
        self.session_manager = SessionManager(self.storage)
        self.history = MessageHistory(self.storage)

    async def list_sessions(self, project_id: str | None = None, limit: int = 20) -> None:
        """List all sessions

        Args:
            project_id: Optional project ID filter
            limit: Maximum number of sessions to show
        """
        console.print("\n[bold cyan]PyCode Sessions[/bold cyan]\n")

        sessions = await self.session_manager.list_sessions(project_id, limit)

        if not sessions:
            console.print("[yellow]No sessions found.[/yellow]")
            console.print("\nCreate a new session with:")
            console.print("  [green]pycode run \"your request\"[/green]")
            return

        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Session ID", style="cyan", no_wrap=True)
        table.add_column("Project", style="green")
        table.add_column("Title", style="white")
        table.add_column("Messages", justify="right", style="blue")
        table.add_column("Last Activity", style="yellow")

        for session in sessions:
            # Truncate session ID for display
            session_id_short = session["session_id"][:20] + "..."
            table.add_row(
                session_id_short,
                session["project_id"],
                session["title"],
                str(session["message_count"]),
                session["last_activity"][:19],  # Just date and time
            )

        console.print(table)
        console.print(f"\n[dim]Showing {len(sessions)} sessions[/dim]")
        console.print("\nResume a session with:")
        console.print("  [green]pycode resume <session-id>[/green]")

    async def resume_session(self, session_id: str, request: str | None = None) -> None:
        """Resume an existing session

        Args:
            session_id: Session ID to resume
            request: Optional new request to add to the session
        """
        # Load session
        session = await self.session_manager.load_session(session_id)
        if not session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            return

        console.print(f"\n[bold cyan]Resuming Session[/bold cyan]")
        console.print(f"  Project: [green]{session.project_id}[/green]")
        console.print(f"  Title: [white]{session.title}[/white]")
        console.print(f"  Directory: [blue]{session.directory}[/blue]")

        # Load conversation history
        messages = await self.history.load_messages(session.id, limit=10)
        console.print(f"  Messages: [yellow]{len(messages)}[/yellow]")

        # Show last few messages
        if messages:
            console.print("\n[bold]Recent conversation:[/bold]")
            for msg in messages[-3:]:
                role = "🧑 User" if msg.role == "user" else "🤖 Assistant"
                # Get first text part
                text = ""
                for part in msg.parts:
                    if part.type == "text":
                        text = part.text[:100] + ("..." if len(part.text) > 100 else "")
                        break
                console.print(f"  {role}: [dim]{text}[/dim]")

        # Get new request if not provided
        if not request:
            console.print("\n")
            request = Prompt.ask("[bold green]Enter your request (or press Enter to just view)[/bold green]")

        if not request:
            console.print("\n[yellow]No request provided. Session loaded but not continued.[/yellow]")
            return

        # Continue session
        await self._run_session(session, request)

    async def clear_session(self, session_id: str) -> None:
        """Clear session history

        Args:
            session_id: Session ID to clear
        """
        # Load session first
        session = await self.session_manager.load_session(session_id)
        if not session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            return

        # Confirm
        console.print(f"\n[yellow]Clear history for session:[/yellow]")
        console.print(f"  Project: {session.project_id}")
        console.print(f"  Title: {session.title}")

        if not Confirm.ask("\nAre you sure? This cannot be undone"):
            console.print("[dim]Cancelled[/dim]")
            return

        # Clear history
        await self.history.clear_history(session.id)
        console.print(f"\n[green]✓[/green] Session history cleared: {session_id}")

    async def delete_session(self, session_id: str) -> None:
        """Delete a session completely

        Args:
            session_id: Session ID to delete
        """
        # Load session first
        session = await self.session_manager.load_session(session_id)
        if not session:
            console.print(f"[red]Session not found: {session_id}[/red]")
            return

        # Confirm
        console.print(f"\n[red]Delete session:[/red]")
        console.print(f"  Project: {session.project_id}")
        console.print(f"  Title: {session.title}")

        if not Confirm.ask("\nAre you sure? This will delete all history"):
            console.print("[dim]Cancelled[/dim]")
            return

        # Delete
        await self.session_manager.delete_session(session.id, session.project_id)
        console.print(f"\n[green]✓[/green] Session deleted: {session_id}")

    async def run_new_session(
        self,
        request: str,
        project_id: str | None = None,
        directory: str | None = None,
        agent_name: str = "build",
    ) -> None:
        """Run a new session

        Args:
            request: User request
            project_id: Optional project ID (defaults to "default")
            directory: Optional working directory (defaults to current)
            agent_name: Agent to use (defaults to "build")
        """
        # Use defaults if not provided
        project_id = project_id or "default"
        directory = directory or str(Path.cwd())

        # Create session
        session = await self.session_manager.create_session(
            project_id=project_id,
            directory=directory,
            title=request[:50] + ("..." if len(request) > 50 else ""),
        )

        console.print(f"\n[bold cyan]New Session Created[/bold cyan]")
        console.print(f"  Session ID: [green]{session.id}[/green]")
        console.print(f"  Project: [blue]{session.project_id}[/blue]")
        console.print(f"  Directory: [yellow]{session.directory}[/yellow]")

        # Run session
        await self._run_session(session, request, agent_name)

    async def _run_session(
        self,
        session: Session,
        request: str,
        agent_name: str = "build",
    ) -> None:
        """Internal: Run a session with agent

        Args:
            session: Session to run
            request: User request
            agent_name: Agent to use
        """
        # Load config
        config = load_config()

        # Get agent
        if agent_name == "build":
            agent = BuildAgent()
        elif agent_name == "plan":
            agent = PlanAgent()
        else:
            console.print(f"[red]Unknown agent: {agent_name}[/red]")
            return

        # Setup provider
        from ..providers import AnthropicProvider, ProviderConfig

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            console.print("\n[red]Error: ANTHROPIC_API_KEY not set[/red]")
            console.print("\nSet your API key:")
            console.print("  [green]export ANTHROPIC_API_KEY=\"sk-ant-...\"[/green]")
            console.print("\nOr run the setup:")
            console.print("  [green]python setup_api_key.py[/green]")
            return

        provider_config = ProviderConfig(api_key=api_key)
        provider = AnthropicProvider(provider_config)

        # Setup tools
        from ..tools import (
            WriteTool,
            ReadTool,
            EditTool,
            BashTool,
            GrepTool,
            GlobTool,
            LsTool,
            GitTool,
            WebFetchTool,
            MultiEditTool,
            SnapshotTool,
        )

        registry = ToolRegistry()
        registry.register(WriteTool())
        registry.register(ReadTool())
        registry.register(EditTool())
        registry.register(BashTool())
        registry.register(GrepTool())
        registry.register(GlobTool())
        registry.register(LsTool())
        registry.register(GitTool())
        registry.register(WebFetchTool())
        registry.register(MultiEditTool())
        registry.register(SnapshotTool())

        # Create runner with config
        run_config = RunConfig(
            max_iterations=config.runtime.max_iterations,
            verbose=config.runtime.verbose,
            auto_approve_tools=config.runtime.auto_approve_tools,
        )

        runner = AgentRunner(
            session=session,
            agent=agent,
            provider=provider,
            registry=registry,
            config=run_config,
        )

        # Run!
        console.print("\n" + "=" * 70)
        console.print(f"[bold green]🚀 Running...[/bold green]")
        console.print("=" * 70 + "\n")

        try:
            async for chunk in runner.run(request):
                console.print(chunk, end="")

            console.print("\n\n" + "=" * 70)
            console.print("[bold green]✓ Complete![/bold green]")
            console.print("=" * 70 + "\n")

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted by user[/yellow]")
        except Exception as e:
            console.print(f"\n\n[red]Error: {e}[/red]")
            import traceback
            traceback.print_exc()

    async def show_config(self) -> None:
        """Show current configuration"""
        config = load_config()

        console.print("\n[bold cyan]PyCode Configuration[/bold cyan]\n")

        # Runtime
        console.print("[bold]Runtime:[/bold]")
        console.print(f"  Verbose: {config.runtime.verbose}")
        console.print(f"  Auto-approve tools: {config.runtime.auto_approve_tools}")
        console.print(f"  Max iterations: {config.runtime.max_iterations}")
        console.print(f"  Doom loop detection: {config.runtime.doom_loop_detection}")
        console.print(f"  Doom loop threshold: {config.runtime.doom_loop_threshold}")

        # Model
        console.print("\n[bold]Default Model:[/bold]")
        console.print(f"  Provider: {config.default_model.provider}")
        console.print(f"  Model ID: {config.default_model.model_id}")
        console.print(f"  Temperature: {config.default_model.temperature}")

        # Agents
        console.print("\n[bold]Agents:[/bold]")
        for name, agent_config in config.agents.items():
            console.print(f"  {name}:")
            console.print(f"    Model: {agent_config.model.model_id}")
            console.print(f"    Tools: {len(agent_config.enabled_tools)}")
            console.print(f"    Edit permission: {agent_config.edit_permission}")

        # Storage
        console.print(f"\n[bold]Storage:[/bold] {config.storage_path}")

        # Show config file location
        config_file = self.config_manager._find_config_file()
        if config_file:
            console.print(f"\n[dim]Config file: {config_file}[/dim]")
        else:
            console.print("\n[dim]Using default configuration (no config file found)[/dim]")
            console.print("[dim]Create one with: pycode config init[/dim]")

    async def init_config(self) -> None:
        """Initialize configuration file"""
        console.print("\n[bold cyan]Initialize PyCode Configuration[/bold cyan]\n")

        # Check if config already exists
        config_file = self.config_manager._find_config_file()
        if config_file:
            console.print(f"[yellow]Config file already exists: {config_file}[/yellow]")
            if not Confirm.ask("Overwrite?"):
                console.print("[dim]Cancelled[/dim]")
                return

        # Create default config
        self.config_manager.create_default_config()
        console.print("\n[green]✓[/green] Configuration initialized!")
        console.print("\nEdit the file to customize PyCode behavior.")

    async def show_stats(self) -> None:
        """Show PyCode statistics"""
        console.print("\n[bold cyan]PyCode Statistics[/bold cyan]\n")

        # Count sessions
        sessions = await self.session_manager.list_sessions(limit=1000)
        total_sessions = len(sessions)

        # Count messages
        total_messages = sum(s["message_count"] for s in sessions)

        # Projects
        projects = set(s["project_id"] for s in sessions)

        console.print(f"  Total sessions: [green]{total_sessions}[/green]")
        console.print(f"  Total messages: [blue]{total_messages}[/blue]")
        console.print(f"  Projects: [yellow]{len(projects)}[/yellow]")

        if projects:
            console.print("\n[bold]Projects:[/bold]")
            for project in sorted(projects):
                project_sessions = [s for s in sessions if s["project_id"] == project]
                console.print(f"  {project}: {len(project_sessions)} sessions")

        console.print()

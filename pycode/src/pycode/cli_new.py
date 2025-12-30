"""
PyCode CLI

Comprehensive command-line interface for PyCode.
Supports running agents, managing sessions, configuration, and more.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from .core import Session
from .agents import BuildAgent, PlanAgent
from .tools import ToolRegistry
from .runner import AgentRunner, RunConfig
from .config import ConfigManager, load_config
from .session_manager import SessionManager
from .storage import Storage
from .logging import configure_logging, LogLevel, get_logger
from .provider_aliases import resolve_provider, resolve_model, get_default_model
from .ui import get_ui
from . import __version__


class PyCodeCLI:
    """Main CLI application"""

    def __init__(self):
        self.parser = self._create_parser()
        self.logger = get_logger()
        self.ui = get_ui()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            prog="pycode",
            description="PyCode - AI Coding Agent in Python",
            epilog="For more information, visit: https://github.com/yourusername/pycode"
        )

        parser.add_argument(
            "--version",
            action="version",
            version=f"PyCode {__version__}"
        )

        parser.add_argument(
            "--config",
            type=Path,
            help="Path to config file"
        )

        parser.add_argument(
            "--log-level",
            choices=["quiet", "normal", "verbose", "debug"],
            default="normal",
            help="Logging level (default: normal)"
        )

        parser.add_argument(
            "--log-file",
            type=Path,
            help="Write logs to file"
        )

        # Create subparsers for commands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Run command
        run_parser = subparsers.add_parser(
            "run",
            help="Run PyCode with a message"
        )
        run_parser.add_argument(
            "message",
            nargs="+",
            help="Your request to the AI"
        )
        run_parser.add_argument(
            "--agent",
            choices=["build", "plan"],
            default="build",
            help="Agent to use (default: build)"
        )
        run_parser.add_argument(
            "--provider",
            help="Provider to use (e.g., anthropic, openai, ollama)"
        )
        run_parser.add_argument(
            "--model",
            help="Model to use (e.g., sonnet, gpt-4, llama3.2)"
        )
        run_parser.add_argument(
            "--directory",
            type=Path,
            default=Path.cwd(),
            help="Working directory (default: current directory)"
        )
        run_parser.add_argument(
            "--max-iterations",
            type=int,
            help="Maximum iterations"
        )
        run_parser.add_argument(
            "--auto-approve",
            action="store_true",
            help="Auto-approve all tool calls"
        )
        run_parser.add_argument(
            "--session",
            help="Resume existing session by ID"
        )

        # Session commands
        session_parser = subparsers.add_parser(
            "session",
            help="Manage sessions"
        )
        session_subparsers = session_parser.add_subparsers(dest="session_command")

        session_subparsers.add_parser(
            "list",
            help="List all sessions"
        )

        resume_parser = session_subparsers.add_parser(
            "resume",
            help="Resume a session"
        )
        resume_parser.add_argument("session_id", help="Session ID to resume")

        delete_parser = session_subparsers.add_parser(
            "delete",
            help="Delete a session"
        )
        delete_parser.add_argument("session_id", help="Session ID to delete")

        clean_parser = session_subparsers.add_parser(
            "clean",
            help="Clean old sessions"
        )
        clean_parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Delete sessions older than N days"
        )

        # Config commands
        config_parser = subparsers.add_parser(
            "config",
            help="Manage configuration"
        )
        config_subparsers = config_parser.add_subparsers(dest="config_command")

        config_subparsers.add_parser(
            "show",
            help="Show current configuration"
        )

        config_subparsers.add_parser(
            "init",
            help="Create default configuration file"
        )

        config_subparsers.add_parser(
            "path",
            help="Show config file path"
        )

        # Provider commands
        provider_parser = subparsers.add_parser(
            "providers",
            help="List available providers"
        )
        provider_parser.add_argument(
            "--aliases",
            action="store_true",
            help="Show provider aliases"
        )

        # Models command
        models_parser = subparsers.add_parser(
            "models",
            help="List available models"
        )
        models_parser.add_argument(
            "--provider",
            help="Filter by provider"
        )

        # Interactive REPL
        subparsers.add_parser(
            "repl",
            help="Start interactive REPL mode"
        )

        return parser

    async def run_agent(self, args: argparse.Namespace) -> int:
        """Run the agent with a message"""
        # Load config
        config_manager = ConfigManager(args.config)
        config = config_manager.load()

        # Setup logging
        log_level = LogLevel(args.log_level)
        configure_logging(
            level=log_level,
            log_file=args.log_file
        )

        # Resolve provider and model
        provider_name = args.provider
        model_id = args.model

        if not provider_name and not model_id:
            # Use defaults from config
            provider_name = config.default_model.provider
            model_id = config.default_model.model_id
        elif model_id and not provider_name:
            # Resolve from model spec
            provider_name, model_id = resolve_model(model_id)
        elif provider_name and not model_id:
            # Use default model for provider
            provider_name = resolve_provider(provider_name)
            model_id = get_default_model(provider_name)
        else:
            # Both specified
            provider_name = resolve_provider(provider_name)

        self.logger.info(
            "Starting agent",
            agent=args.agent,
            provider=provider_name,
            model=model_id
        )

        # Create or load session
        storage = Storage()
        session_manager = SessionManager(storage)

        if args.session:
            # Resume existing session
            session = await session_manager.load_session(args.session)
            if not session:
                self.logger.error("Session not found", session_id=args.session)
                return 1
            self.logger.info("Resumed session", session_id=session.id)
        else:
            # Create new session
            session = Session(directory=str(args.directory))
            await session_manager.save_session(session)
            self.logger.info("Created session", session_id=session.id)

        # Create agent
        if args.agent == "build":
            agent = BuildAgent()
        elif args.agent == "plan":
            agent = PlanAgent()
        else:
            self.logger.error("Unknown agent", agent=args.agent)
            return 1

        # Create provider
        provider_settings = config.providers.get(provider_name, {})
        api_key = getattr(provider_settings, 'api_key', None) or os.getenv(
            f"{provider_name.upper()}_API_KEY"
        )

        try:
            # Import and create provider
            if provider_name == "anthropic":
                from .providers import AnthropicProvider, ProviderConfig
                provider = AnthropicProvider(ProviderConfig(
                    name=provider_name,
                    api_key=api_key
                ))
            elif provider_name == "openai":
                from .providers import OpenAIProvider, ProviderConfig
                provider = OpenAIProvider(ProviderConfig(
                    name=provider_name,
                    api_key=api_key
                ))
            elif provider_name == "ollama":
                from .providers import OllamaProvider, ProviderConfig
                base_url = getattr(provider_settings, 'base_url', None) or "http://localhost:11434"
                provider = OllamaProvider(ProviderConfig(
                    name=provider_name,
                    base_url=base_url
                ))
            elif provider_name == "gemini":
                from .providers import GeminiProvider, ProviderConfig
                provider = GeminiProvider(ProviderConfig(
                    name=provider_name,
                    api_key=api_key
                ))
            elif provider_name == "mistral":
                from .providers import MistralProvider, ProviderConfig
                provider = MistralProvider(ProviderConfig(
                    name=provider_name,
                    api_key=api_key
                ))
            elif provider_name == "cohere":
                from .providers import CohereProvider, ProviderConfig
                provider = CohereProvider(ProviderConfig(
                    name=provider_name,
                    api_key=api_key
                ))
            else:
                self.logger.error("Unknown provider", provider=provider_name)
                return 1

        except Exception as e:
            self.logger.error("Failed to create provider", provider=provider_name, error=str(e))
            return 1

        # Create runner
        run_config = RunConfig(
            max_iterations=args.max_iterations or config.runtime.max_iterations,
            auto_approve_tools=args.auto_approve or config.runtime.auto_approve_tools,
            doom_loop_detection=config.runtime.doom_loop_detection,
            doom_loop_threshold=config.runtime.doom_loop_threshold,
            verbose=log_level != LogLevel.QUIET
        )

        runner = AgentRunner(
            session=session,
            agent=agent,
            provider=provider,
            registry=ToolRegistry(),
            config=run_config,
            storage=storage
        )

        # Run with message
        message = " ".join(args.message)

        try:
            async for chunk in runner.run(message):
                print(chunk, end="", flush=True)

            print()  # Final newline
            return 0

        except KeyboardInterrupt:
            self.logger.warning("Interrupted by user")
            return 130
        except Exception as e:
            self.logger.error("Agent execution failed", error=str(e))
            return 1

    async def list_sessions(self) -> int:
        """List all sessions"""
        storage = Storage()
        session_manager = SessionManager(storage)

        sessions = await session_manager.list_sessions()

        if not sessions:
            self.ui.print_status("No sessions found", style="yellow")
            return 0

        # Build table data
        headers = ["ID", "Directory", "Created", "Updated", "Messages"]
        rows = []

        for session in sessions:
            # Get message count
            from .history import MessageHistory
            history = MessageHistory(storage)
            messages = await history.list_messages(session.id)

            rows.append([
                session.id[:8] + "...",
                session.directory,
                session.created_at.strftime("%Y-%m-%d %H:%M"),
                session.updated_at.strftime("%Y-%m-%d %H:%M"),
                str(len(messages))
            ])

        self.ui.print_table("Sessions", headers, rows)
        return 0

    async def show_config(self, args: argparse.Namespace) -> int:
        """Show current configuration"""
        config_manager = ConfigManager(args.config)
        config = config_manager.load()

        import yaml
        config_dict = config.model_dump(exclude_none=True)
        yaml_str = yaml.safe_dump(config_dict, default_flow_style=False, sort_keys=False)

        self.ui.print_code(yaml_str, language="yaml", title="Configuration")
        return 0

    async def init_config(self, args: argparse.Namespace) -> int:
        """Initialize default configuration"""
        config_manager = ConfigManager(args.config)
        config_manager.create_default_config()
        return 0

    def show_config_path(self, args: argparse.Namespace) -> int:
        """Show config file path"""
        config_manager = ConfigManager(args.config)
        config_file = config_manager.config_path or config_manager._find_config_file()

        if config_file:
            print(f"Config file: {config_file}")
            print(f"Exists: {config_file.exists()}")
        else:
            print("No config file found")
            print("\nDefault locations:")
            for path in config_manager.DEFAULT_CONFIG_LOCATIONS:
                print(f"  - {path}")

        return 0

    def list_providers(self, args: argparse.Namespace) -> int:
        """List available providers"""
        from .provider_aliases import PROVIDER_ALIASES, get_resolver

        if args.aliases:
            # Show aliases
            headers = ["Alias", "Provider"]
            rows = [[alias, provider] for alias, provider in PROVIDER_ALIASES.items()]
            self.ui.print_table("Provider Aliases", headers, rows)
        else:
            # Show providers
            providers = [
                ["anthropic", "Anthropic (Claude)", "✅"],
                ["openai", "OpenAI (GPT)", "⚠️ Requires package"],
                ["ollama", "Ollama (Local)", "✅"],
                ["gemini", "Google (Gemini)", "✅"],
                ["mistral", "Mistral AI", "✅"],
                ["cohere", "Cohere", "✅"],
            ]

            self.ui.print_table(
                "Available Providers",
                ["Name", "Description", "Status"],
                providers
            )

        return 0

    def list_models(self, args: argparse.Namespace) -> int:
        """List available models"""
        from .provider_aliases import MODEL_ALIASES

        if args.provider:
            provider = resolve_provider(args.provider)
            # Filter by provider
            rows = [
                [alias, model]
                for alias, (p, model) in MODEL_ALIASES.items()
                if p == provider
            ]
            title = f"Models for {provider}"
        else:
            # All models
            rows = [
                [alias, f"{provider}/{model}"]
                for alias, (provider, model) in MODEL_ALIASES.items()
            ]
            title = "All Model Aliases"

        self.ui.print_table(title, ["Alias", "Model"], rows)
        return 0

    async def run_repl(self, args: argparse.Namespace) -> int:
        """Start interactive REPL"""
        self.logger.info("Starting REPL mode")

        print("\nPyCode Interactive REPL")
        print("Type 'exit' or 'quit' to exit")
        print("Type 'help' for available commands\n")

        while True:
            try:
                user_input = input(">>> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break

                if user_input.lower() == "help":
                    print("\nAvailable commands:")
                    print("  exit, quit, q - Exit REPL")
                    print("  help - Show this message")
                    print("  Or type any message for the AI\n")
                    continue

                # Run the agent with the message
                # Create a namespace with default args
                run_args = argparse.Namespace(
                    message=user_input.split(),
                    agent="build",
                    provider=None,
                    model=None,
                    directory=Path.cwd(),
                    max_iterations=None,
                    auto_approve=False,
                    session=None,
                    config=args.config,
                    log_level=args.log_level,
                    log_file=args.log_file
                )

                await self.run_agent(run_args)
                print()

            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break
            except Exception as e:
                self.logger.error("REPL error", error=str(e))

        return 0

    async def run(self, argv: Optional[list[str]] = None) -> int:
        """Main entry point"""
        args = self.parser.parse_args(argv)

        # Configure logging
        log_level = LogLevel(args.log_level)
        configure_logging(
            level=log_level,
            log_file=args.log_file
        )

        # Handle commands
        if not args.command:
            # No command - show help
            self.parser.print_help()
            return 0

        if args.command == "run":
            return await self.run_agent(args)

        elif args.command == "session":
            if args.session_command == "list":
                return await self.list_sessions()
            elif args.session_command == "resume":
                # Set session ID and run
                args.message = input("Message: ").split()
                args.session = args.session_id
                return await self.run_agent(args)
            else:
                print("Session command not implemented yet")
                return 1

        elif args.command == "config":
            if args.config_command == "show":
                return await self.show_config(args)
            elif args.config_command == "init":
                return await self.init_config(args)
            elif args.config_command == "path":
                return self.show_config_path(args)

        elif args.command == "providers":
            return self.list_providers(args)

        elif args.command == "models":
            return self.list_models(args)

        elif args.command == "repl":
            return await self.run_repl(args)

        return 0


def main(argv: Optional[list[str]] = None):
    """Entry point for CLI"""
    import os

    cli = PyCodeCLI()

    # Add import for os module at the top of run_agent method
    # (This is needed for the os.getenv call)

    try:
        exit_code = asyncio.run(cli.run(argv))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

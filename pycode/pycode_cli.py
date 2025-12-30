#!/usr/bin/env python3
"""
PyCode CLI Entry Point

Main command-line interface for PyCode.

Commands:
  list      - List all sessions
  resume    - Resume a session
  run       - Run a new session
  clear     - Clear session history
  delete    - Delete a session
  config    - Show or initialize configuration
  stats     - Show PyCode statistics
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pycode.cli import Commands


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        prog="pycode",
        description="PyCode - AI-powered coding assistant with vibe coding support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # list command
    list_parser = subparsers.add_parser("list", help="List all sessions")
    list_parser.add_argument(
        "-p", "--project", help="Filter by project ID", default=None
    )
    list_parser.add_argument(
        "-l", "--limit", help="Maximum number of sessions", type=int, default=20
    )

    # resume command
    resume_parser = subparsers.add_parser("resume", help="Resume a session")
    resume_parser.add_argument("session_id", help="Session ID to resume")
    resume_parser.add_argument(
        "-r", "--request", help="New request to add", default=None
    )

    # run command
    run_parser = subparsers.add_parser("run", help="Run a new session")
    run_parser.add_argument("request", help="Request to run")
    run_parser.add_argument(
        "-p", "--project", help="Project ID", default="default"
    )
    run_parser.add_argument(
        "-d", "--directory", help="Working directory", default=None
    )
    run_parser.add_argument(
        "-a", "--agent", help="Agent to use", default="build", choices=["build", "plan"]
    )

    # clear command
    clear_parser = subparsers.add_parser("clear", help="Clear session history")
    clear_parser.add_argument("session_id", help="Session ID to clear")

    # delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a session")
    delete_parser.add_argument("session_id", help="Session ID to delete")

    # config command
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="config_command")
    config_subparsers.add_parser("show", help="Show current configuration")
    config_subparsers.add_parser("init", help="Initialize configuration file")

    # stats command
    subparsers.add_parser("stats", help="Show PyCode statistics")

    return parser


async def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = Commands()

    try:
        if args.command == "list":
            await commands.list_sessions(args.project, args.limit)

        elif args.command == "resume":
            await commands.resume_session(args.session_id, args.request)

        elif args.command == "run":
            await commands.run_new_session(
                args.request,
                args.project,
                args.directory,
                args.agent,
            )

        elif args.command == "clear":
            await commands.clear_session(args.session_id)

        elif args.command == "delete":
            await commands.delete_session(args.session_id)

        elif args.command == "config":
            if args.config_command == "show" or not args.config_command:
                await commands.show_config()
            elif args.config_command == "init":
                await commands.init_config()

        elif args.command == "stats":
            await commands.show_stats()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

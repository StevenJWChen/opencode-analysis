#!/usr/bin/env python3
"""
Comprehensive PyCode Demo

Demonstrates all new features:
- Configuration system
- Session management
- Message history
- Doom loop detection
- CLI commands
- Vibe coding workflow
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from pycode.config import load_config, ConfigManager
from pycode.session_manager import SessionManager
from pycode.history import MessageHistory
from pycode.storage import Storage
from pycode.core import Session
from pycode.agents import BuildAgent
from pycode.tools import (
    ToolRegistry,
    WriteTool,
    ReadTool,
    EditTool,
    BashTool,
    GrepTool,
    GlobTool,
)
from pycode.runner import AgentRunner, RunConfig
from pycode.providers import AnthropicProvider, ProviderConfig


def print_banner():
    """Print banner"""
    print("\n" + "=" * 70)
    print("  PyCode Comprehensive Demo - All Features")
    print("=" * 70)
    print()


def print_section(title: str):
    """Print section header"""
    print("\n" + "-" * 70)
    print(f"  {title}")
    print("-" * 70 + "\n")


async def demo_config_system():
    """Demonstrate configuration system"""
    print_section("1. Configuration System")

    config_manager = ConfigManager()
    config = load_config()

    print(f"✅ Configuration loaded")
    print(f"   Runtime:")
    print(f"     - Max iterations: {config.runtime.max_iterations}")
    print(f"     - Doom loop detection: {config.runtime.doom_loop_detection}")
    print(f"     - Doom loop threshold: {config.runtime.doom_loop_threshold}")
    print(f"   Default model: {config.default_model.model_id}")
    print(f"   Storage path: {config.storage_path}")
    print(f"   Enabled tools: {len(config.enabled_tools)}")


async def demo_session_management():
    """Demonstrate session management"""
    print_section("2. Session Management")

    storage = Storage()
    session_manager = SessionManager(storage)

    # Create a test session
    session = await session_manager.create_session(
        project_id="demo-project",
        directory=str(Path.cwd()),
        title="Comprehensive Demo Session"
    )

    print(f"✅ Session created")
    print(f"   Session ID: {session.id}")
    print(f"   Project: {session.project_id}")
    print(f"   Title: {session.title}")

    # List sessions
    sessions = await session_manager.list_sessions(limit=5)
    print(f"\n✅ Found {len(sessions)} total sessions")

    # Get stats
    stats = await session_manager.get_session_stats(session.id, session.project_id)
    print(f"\n✅ Session stats:")
    print(f"   Created: {stats.get('created')}")
    print(f"   Message count: {stats.get('message_count')}")

    return session


async def demo_message_history(session: Session):
    """Demonstrate message history"""
    print_section("3. Message History")

    storage = Storage()
    history = MessageHistory(storage)

    # The session would have messages from running agent
    # For demo, just show capabilities
    print(f"✅ Message history system ready")
    print(f"   Session: {session.id}")
    print(f"   Capabilities:")
    print(f"     - Save/load messages")
    print(f"     - Build conversation for LLM")
    print(f"     - Context management")
    print(f"     - Token limit handling")


async def demo_vibe_coding(session: Session):
    """Demonstrate vibe coding workflow"""
    print_section("4. Vibe Coding Workflow")

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set")
        print("   Skipping vibe coding demo")
        print("   Run 'python setup_api_key.py' to set up API key")
        return

    print("✅ API key found - running vibe coding demo")

    # Load config
    config = load_config()

    # Setup agent
    agent = BuildAgent()

    # Setup provider
    provider_config = ProviderConfig(api_key=api_key)
    provider = AnthropicProvider(provider_config)

    # Setup tools
    registry = ToolRegistry()
    registry.register(WriteTool())
    registry.register(ReadTool())
    registry.register(EditTool())
    registry.register(BashTool())
    registry.register(GrepTool())
    registry.register(GlobTool())

    # Create runner with new features
    storage = Storage()
    run_config = RunConfig(
        max_iterations=config.runtime.max_iterations,
        verbose=True,
        auto_approve_tools=True,
        doom_loop_detection=config.runtime.doom_loop_detection,
        doom_loop_threshold=config.runtime.doom_loop_threshold,
    )

    runner = AgentRunner(
        session=session,
        agent=agent,
        provider=provider,
        registry=registry,
        config=run_config,
        storage=storage,  # NEW: Pass storage for history management
    )

    # Simple request
    request = "Write a Python function that reverses a string and test it with 'PyCode'"

    print(f"\n🎯 Request: {request}")
    print("\n" + "=" * 70)

    try:
        async for chunk in runner.run(request):
            print(chunk, end="", flush=True)

        print("\n" + "=" * 70)
        print("✅ Vibe coding demo complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")


async def demo_doom_loop_detection():
    """Explain doom loop detection"""
    print_section("5. Doom Loop Detection")

    print("✅ Doom loop detection is active in AgentRunner")
    print()
    print("What it does:")
    print("  • Tracks all tool calls and their parameters")
    print("  • Detects when the same tool is called repeatedly")
    print("  • Detects alternating patterns (A-B-A-B...)")
    print("  • Breaks execution to prevent infinite loops")
    print()
    print("Configuration:")
    config = load_config()
    print(f"  • Enabled: {config.runtime.doom_loop_detection}")
    print(f"  • Threshold: {config.runtime.doom_loop_threshold} identical calls")
    print()
    print("This prevents the AI from getting stuck and wasting API credits!")


async def main():
    """Run comprehensive demo"""
    print_banner()

    print("This demo showcases all new PyCode features:")
    print("  1. Configuration System (YAML)")
    print("  2. Session Management")
    print("  3. Message History")
    print("  4. Vibe Coding Workflow")
    print("  5. Doom Loop Detection")
    print()

    # Demo 1: Config
    await demo_config_system()

    # Demo 2: Sessions
    session = await demo_session_management()

    # Demo 3: History
    await demo_message_history(session)

    # Demo 4: Vibe coding (optional - requires API key)
    await demo_vibe_coding(session)

    # Demo 5: Doom loop
    await demo_doom_loop_detection()

    # Summary
    print("\n" + "=" * 70)
    print("  Summary: What's New in PyCode")
    print("=" * 70)
    print()
    print("✅ Configuration System")
    print("   - YAML-based configuration")
    print("   - Customize agents, tools, models")
    print("   - Runtime settings (max iterations, doom loop, etc.)")
    print()
    print("✅ Session Management")
    print("   - Create, list, resume, delete sessions")
    print("   - Multi-project support")
    print("   - Session metadata and statistics")
    print()
    print("✅ Message History")
    print("   - Persistent conversation storage")
    print("   - Resume sessions from any point")
    print("   - Context management and token limits")
    print()
    print("✅ Vibe Coding Workflow")
    print("   - Integrated with history and sessions")
    print("   - Automatic message persistence")
    print("   - Full write-run-fix loop")
    print()
    print("✅ Doom Loop Detection")
    print("   - Prevents infinite loops")
    print("   - Detects repeated and alternating patterns")
    print("   - Configurable threshold")
    print()
    print("=" * 70)
    print("  Try the CLI!")
    print("=" * 70)
    print()
    print("PyCode now has a full CLI:")
    print("  python pycode_cli.py list         - List all sessions")
    print("  python pycode_cli.py run \"...\"     - Run a new session")
    print("  python pycode_cli.py resume <id>  - Resume a session")
    print("  python pycode_cli.py config show  - Show configuration")
    print("  python pycode_cli.py stats        - Show statistics")
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted")
        sys.exit(0)

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

# Fix Windows console encoding issues
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 > nul 2>&1')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

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
from pycode.providers import OllamaProvider, ProviderConfig
from pycode.config import ProviderSettings


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


class StreamEvent:
    """Mock event object for provider streaming"""
    def __init__(self, event_type: str, data: dict):
        self.type = event_type
        self.data = data


class MockProvider:
    """Mock LLM provider for demo - simulates realistic vibe coding responses"""

    def __init__(self):
        self.iteration = 0

    async def stream(self, model: str, messages: list, system: str, tools: list):
        """Simulate LLM streaming responses with tool calls"""
        self.iteration += 1

        # Show what the agent sees
        print(f"\n📋 Agent System Prompt: {system[:100]}...")
        print(f"📋 Available Tools: {len(tools)} tools")
        print(f"📋 Conversation Messages: {len(messages)} messages")
        print()

        if self.iteration == 1:
            # First iteration: Write the code
            yield StreamEvent("text_delta", {"text": "I'll create a Python function to reverse a string and test it.\n\n"})

            # Simulate tool call for write
            yield StreamEvent("tool_use", {
                "id": "call_001",
                "name": "write",
                "arguments": {
                    "file_path": "/tmp/reverse_string.py",
                    "content": '''def reverse_string(text):
    """Reverse a string"""
    return text[::-1]

if __name__ == "__main__":
    test_input = "PyCode"
    result = reverse_string(test_input)
    print(f"Input: {test_input}")
    print(f"Reversed: {result}")
'''
                }
            })

        elif self.iteration == 2:
            # Second iteration: Run the code
            yield StreamEvent("text_delta", {"text": "Now let me run the code to verify it works.\n\n"})

            # Simulate tool call for bash
            yield StreamEvent("tool_use", {
                "id": "call_002",
                "name": "bash",
                "arguments": {
                    "command": "python /tmp/reverse_string.py"
                }
            })

        else:
            # Third iteration: Verify and complete
            yield StreamEvent("text_delta", {"text": "Perfect! The function works correctly. It reverses 'PyCode' to 'edoCyP'.\n\n"})
            yield StreamEvent("text_delta", {"text": "✅ Task complete - created reverse_string() function and verified it works!"})


async def demo_vibe_coding(session: Session):
    """Demonstrate vibe coding workflow with real agent and tools"""
    print_section("4. Vibe Coding Workflow (Mock LLM)")

    print("🎯 Running realistic vibe coding demo")
    print("   ✅ Real BuildAgent with system prompt")
    print("   ✅ Real ToolRegistry with 6 tools")
    print("   ✅ Real tool execution (write, bash, etc.)")
    print("   ✅ Real message history and session persistence")
    print("   🎭 Mock LLM responses (simulated)")
    print()

    # Load config
    config = load_config()

    # Setup REAL agent
    agent = BuildAgent()

    # Get and show agent's system prompt
    system_prompt = await agent.get_system_prompt()
    print(f"📝 Agent System Prompt ({len(system_prompt)} chars):")
    print(f"   {system_prompt[:150]}...")
    print()

    # Setup REAL tools
    registry = ToolRegistry()
    registry.register(WriteTool())
    registry.register(ReadTool())
    registry.register(EditTool())
    registry.register(BashTool())
    registry.register(GrepTool())
    registry.register(GlobTool())

    print(f"🔧 Registered {len(registry.get_all())} real tools:")
    for tool_name in registry.get_all().keys():
        print(f"   • {tool_name}")
    print()

    # Setup MOCK provider (only simulates LLM responses)
    provider = MockProvider()

    # Create REAL runner with new features
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
        storage=storage,  # Real storage for history management
    )

    # Realistic request
    request = "Write a Python function that reverses a string and test it with 'PyCode'"

    print(f"💬 User Request: \"{request}\"")
    print("\n" + "=" * 70)
    print("🚀 Starting Vibe Coding Loop...")
    print("=" * 70)

    try:
        async for chunk in runner.run(request):
            print(chunk, end="", flush=True)

        print("\n" + "=" * 70)
        print("✅ Vibe Coding Demo Complete!")
        print("=" * 70)

        # Show what was persisted
        print("\n📊 What happened:")
        print("   ✅ User message saved to history")
        print("   ✅ Agent messages saved with tool calls")
        print("   ✅ Session timestamp updated")
        print("   ✅ Real tools executed (write file, run bash)")
        print("   ✅ File created: /tmp/reverse_string.py")
        print("   ✅ Code executed and output captured")

        # Verify file was actually created
        if Path("/tmp/reverse_string.py").exists():
            print("\n📄 Actual file created:")
            with open("/tmp/reverse_string.py") as f:
                content = f.read()
            print("   " + "\n   ".join(content.split("\n")[:5]))
            print("   ...")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


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

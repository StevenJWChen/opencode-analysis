"""
Simple PyCode demonstration without external dependencies
"""

import asyncio
import sys
sys.path.insert(0, 'src')

from pathlib import Path
from pycode.core import Session, Message, TextPart, Identifier
from pycode.agents import BuildAgent, PlanAgent
from pycode.tools import ToolRegistry, BashTool, ReadTool, ToolContext
from pycode.storage import Storage


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


async def demo_session():
    """Demonstrate session management"""
    print_section("Session Management")

    # Create a session
    session = Session(
        project_id="demo-project",
        directory=str(Path.cwd()),
        title="PyCode Demo Session",
    )

    print(f"✓ Created session: {session.id}")
    print(f"  Project ID: {session.project_id}")
    print(f"  Directory: {session.directory}")
    print(f"  Title: {session.title}")
    print(f"  Created: {session.time_created}")

    # Create a user message
    user_message = Message(
        session_id=session.id,
        role="user",
    )
    user_message.add_part(TextPart(
        session_id=session.id,
        message_id=user_message.id,
        text="Help me understand the PyCode architecture"
    ))

    print(f"\n✓ Created user message: {user_message.id}")
    print(f"  Content: {user_message.get_text_content()}")

    # Create an assistant message
    assistant_message = Message(
        session_id=session.id,
        role="assistant",
        agent="build",
        model_id="example-model",
        provider_id="example-provider"
    )
    assistant_message.add_part(TextPart(
        session_id=session.id,
        message_id=assistant_message.id,
        text="I'd be happy to help! PyCode has a modular architecture with:\n" +
             "- Core data structures (Session, Message, Identifier)\n" +
             "- Agent system (Build, Plan)\n" +
             "- Tool system (Bash, Read, Edit, Grep)\n" +
             "- Provider integration (Anthropic, OpenAI)\n" +
             "- Storage layer (file-based JSON)"
    ))

    print(f"\n✓ Created assistant message: {assistant_message.id}")
    print(f"  Agent: {assistant_message.agent}")
    print(f"  Response: {assistant_message.get_text_content()[:100]}...")

    return session


async def demo_agents():
    """Demonstrate agent system"""
    print_section("Agent System")

    # Build agent
    build_agent = BuildAgent()
    print("✓ Build Agent")
    print(f"  Name: {build_agent.name}")
    print(f"  Description: {build_agent.description}")
    print(f"  Edit Permission: {build_agent.config.edit_permission}")
    print(f"  Max Steps: {build_agent.config.max_steps}")

    # Test bash permissions
    print("\n  Bash Permissions:")
    commands = ["git status", "ls -la", "rm -rf /", "npm install"]
    for cmd in commands:
        perm = build_agent.config.check_bash_permission(cmd)
        icon = "✓" if perm == "allow" else "⚠" if perm == "ask" else "✗"
        print(f"    {icon} '{cmd}' → {perm}")

    # Plan agent
    print("\n✓ Plan Agent")
    plan_agent = PlanAgent()
    print(f"  Name: {plan_agent.name}")
    print(f"  Description: {plan_agent.description}")
    print(f"  Edit Permission: {plan_agent.config.edit_permission}")

    print("\n  Bash Permissions:")
    for cmd in commands:
        perm = plan_agent.config.check_bash_permission(cmd)
        icon = "✓" if perm == "allow" else "⚠" if perm == "ask" else "✗"
        print(f"    {icon} '{cmd}' → {perm}")

    # Tool configuration
    print(f"\n  Tools:")
    print(f"    Edit tool enabled: {plan_agent.config.is_tool_enabled('edit')}")
    print(f"    Read tool enabled: {plan_agent.config.is_tool_enabled('read')}")
    print(f"    Bash tool enabled: {plan_agent.config.is_tool_enabled('bash')}")


async def demo_tools():
    """Demonstrate tool system"""
    print_section("Tool System")

    # Create registry
    registry = ToolRegistry()

    # Register tools
    bash_tool = BashTool()
    read_tool = ReadTool()

    registry.register(bash_tool)
    registry.register(read_tool)

    print(f"✓ Registered {len(registry.get_all())} tools:")
    for name, tool in registry.get_all().items():
        print(f"  - {name}: {tool.description[:60]}...")

    # Create context
    context = ToolContext(
        session_id="demo_session",
        message_id="demo_message",
        agent_name="build",
        working_directory=str(Path.cwd()),
    )

    # Execute bash tool
    print("\n✓ Executing BashTool:")
    print("  Command: echo 'Hello from PyCode!'")
    result = await registry.execute(
        "bash",
        {
            "command": "echo 'Hello from PyCode!'",
            "description": "Print greeting"
        },
        context
    )
    print(f"  Result: {result.title}")
    print(f"  Output: {result.output.strip()}")

    # Execute read tool (read this demo file)
    print("\n✓ Executing ReadTool:")
    print(f"  File: demo.py (first 5 lines)")
    result = await registry.execute(
        "read",
        {
            "file_path": str(Path(__file__).absolute()),
            "offset": 0,
            "limit": 5
        },
        context
    )
    print(f"  Result: {result.title}")
    print("  Preview:")
    for line in result.output.split("\n")[:5]:
        print(f"    {line}")


async def demo_storage():
    """Demonstrate storage system"""
    print_section("Storage System")

    # Create storage
    storage = Storage(base_path=Path.cwd() / ".pycode_demo" / "storage")
    print(f"✓ Storage initialized")
    print(f"  Base path: {storage.base_path}")

    # Create test data
    session = Session(
        project_id="demo-project",
        directory=str(Path.cwd()),
        title="Demo Storage Session",
    )

    # Write session
    await storage.write(["sessions", "demo-project", session.id], session)
    print(f"\n✓ Saved session: {session.id}")

    # Read session
    loaded = await storage.read(["sessions", "demo-project", session.id])
    print(f"✓ Loaded session: {loaded['id']}")
    print(f"  Title: {loaded['title']}")
    print(f"  Directory: {loaded['directory']}")

    # List sessions
    sessions = await storage.list_keys(["sessions", "demo-project"])
    print(f"\n✓ Sessions in project: {len(sessions)}")
    for s in sessions:
        print(f"  - {s}")


async def demo_identifiers():
    """Demonstrate identifier system"""
    print_section("Identifier System")

    print("✓ Ascending IDs (chronological):")
    ids = [Identifier.ascending("message") for _ in range(3)]
    for i, id in enumerate(ids, 1):
        print(f"  {i}. {id}")
    print(f"  → IDs increase over time: {ids[0] < ids[1] < ids[2]}")

    print("\n✓ Descending IDs (reverse chronological):")
    ids = [Identifier.descending("session") for _ in range(3)]
    for i, id in enumerate(ids, 1):
        print(f"  {i}. {id}")
    print(f"  → IDs decrease over time: {ids[0] > ids[1] > ids[2]}")

    print("\n✓ Identifier comparison:")
    id1 = Identifier.ascending("message")
    id2 = Identifier.ascending("message")
    print(f"  ID1: {id1}")
    print(f"  ID2: {id2}")
    print(f"  Compare: {Identifier.compare(id1, id2)} (1 = id1 > id2)")


async def main():
    """Run all demonstrations"""
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + " " * 15 + "PyCode Demonstration" + " " * 23 + "█")
    print("█" + " " * 10 + "Python AI Coding Agent Implementation" + " " * 11 + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60)

    try:
        await demo_identifiers()
        await demo_session()
        await demo_agents()
        await demo_tools()
        await demo_storage()

        print_section("Summary")
        print("✓ All demonstrations completed successfully!")
        print("\n📚 Core Components Demonstrated:")
        print("  ✓ Identifier system (ULID-based IDs)")
        print("  ✓ Session management")
        print("  ✓ Message system with parts")
        print("  ✓ Agent system (Build & Plan)")
        print("  ✓ Tool system (Bash & Read)")
        print("  ✓ Storage layer (file-based)")

        print("\n🎯 Architecture Highlights:")
        print("  • Type-safe with Pydantic models")
        print("  • Async/await for concurrency")
        print("  • Modular and extensible design")
        print("  • ~1,350 lines of Python code")

        print("\n📖 Next Steps:")
        print("  1. Explore the code in src/pycode/")
        print("  2. Add custom tools or agents")
        print("  3. Integrate with LLM providers")
        print("  4. Build your own AI coding assistant!")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

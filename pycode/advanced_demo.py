"""
Advanced PyCode demonstration - simulating an AI coding session
"""

import asyncio
import sys
sys.path.insert(0, 'src')

from pathlib import Path
from pycode.core import Session, Message, TextPart, ToolPart, Identifier
from pycode.core.message import ToolState
from pycode.agents import BuildAgent, PlanAgent
from pycode.tools import ToolRegistry, BashTool, ReadTool, EditTool, GrepTool, ToolContext
from pycode.storage import Storage


class SessionSimulator:
    """Simulate an AI coding session"""

    def __init__(self, agent, session):
        self.agent = agent
        self.session = session
        self.registry = ToolRegistry()
        self.storage = Storage(base_path=Path.cwd() / ".pycode_demo" / "storage")

        # Register tools
        self.registry.register(BashTool())
        self.registry.register(ReadTool())
        self.registry.register(EditTool())
        self.registry.register(GrepTool())

    def print_message(self, role, content, agent=None):
        """Pretty print a message"""
        if role == "user":
            print(f"\n{'='*60}")
            print(f"👤 USER: {content}")
            print('='*60)
        else:
            print(f"\n🤖 ASSISTANT ({agent}):")
            print(f"   {content}")
            print()

    async def execute_tool(self, tool_name, params, description):
        """Execute a tool and display results"""
        print(f"   🔧 Using tool: {tool_name}")
        print(f"      {description}")

        context = ToolContext(
            session_id=self.session.id,
            message_id=Identifier.ascending("message"),
            agent_name=self.agent.name,
            working_directory=self.session.directory
        )

        result = await self.registry.execute(tool_name, params, context)

        if result.error:
            print(f"      ❌ Error: {result.error}")
        else:
            print(f"      ✅ {result.title}")
            if len(result.output) < 200:
                print(f"         {result.output[:200]}")

        return result

    async def simulate_conversation(self):
        """Simulate a complete coding conversation"""

        print("\n" + "█"*60)
        print("█" + " "*58 + "█")
        print("█" + " "*10 + "AI Coding Session Simulation" + " "*20 + "█")
        print("█" + " "*58 + "█")
        print("█"*60)

        # Message 1: User asks to explore codebase
        self.print_message(
            "user",
            "I want to understand the PyCode project structure. Can you help?"
        )

        self.print_message(
            "assistant",
            "I'll help you explore the PyCode structure. Let me start by checking what files we have.",
            self.agent.name
        )

        await self.execute_tool(
            "bash",
            {"command": "ls -la src/pycode/", "description": "List PyCode modules"},
            "Listing main modules"
        )

        # Message 2: User asks about specific module
        self.print_message(
            "user",
            "What's in the core module?"
        )

        self.print_message(
            "assistant",
            "Let me check the core module contents.",
            self.agent.name
        )

        await self.execute_tool(
            "bash",
            {"command": "ls -la src/pycode/core/", "description": "List core module files"},
            "Checking core module"
        )

        await self.execute_tool(
            "read",
            {
                "file_path": str((Path.cwd() / "src/pycode/core/__init__.py").absolute()),
                "limit": 10
            },
            "Reading core module exports"
        )

        # Message 3: User asks to search for specific patterns
        self.print_message(
            "user",
            "Show me where the Session class is defined"
        )

        self.print_message(
            "assistant",
            "I'll search for the Session class definition.",
            self.agent.name
        )

        await self.execute_tool(
            "grep",
            {
                "pattern": "class Session",
                "path": "src/pycode/",
                "max_results": 5
            },
            "Searching for Session class"
        )

        # Message 4: Analysis complete
        self.print_message(
            "assistant",
            """Based on my exploration, here's the PyCode structure:

📁 Core Modules:
   • core/       - Data structures (Session, Message, Identifier)
   • agents/     - Agent system (Build, Plan)
   • tools/      - Tool implementations (Bash, Read, Edit, Grep)
   • providers/  - LLM provider integrations
   • storage/    - Persistence layer
   • cli/        - Command-line interface

🎯 Key Components:
   • Session: Manages conversation state
   • Message: User and assistant messages
   • Agent: Configures behavior and permissions
   • Tools: Execute actions (bash, file ops, search)
   • Storage: File-based JSON persistence

The architecture follows a clean separation of concerns with
type-safe Pydantic models and async operations throughout.""",
            self.agent.name
        )


async def demo_permission_system():
    """Demonstrate permission system"""
    print("\n" + "█"*60)
    print("█" + " "*15 + "Permission System Demo" + " "*21 + "█")
    print("█"*60 + "\n")

    build_agent = BuildAgent()
    plan_agent = PlanAgent()

    dangerous_commands = [
        "rm -rf /",
        "sudo rm -rf /var",
        "mkfs.ext4 /dev/sda",
        ":(){:|:&};:",  # Fork bomb
    ]

    safe_commands = [
        "ls -la",
        "git status",
        "cat README.md",
        "grep pattern file.txt",
    ]

    print("🔒 Testing Build Agent Permissions:\n")
    print("   Dangerous commands:")
    for cmd in dangerous_commands:
        perm = build_agent.config.check_bash_permission(cmd)
        icon = "⚠️" if perm == "ask" else "✓" if perm == "allow" else "❌"
        print(f"   {icon} '{cmd[:30]:30}' → {perm}")

    print("\n   Safe commands:")
    for cmd in safe_commands:
        perm = build_agent.config.check_bash_permission(cmd)
        icon = "✓" if perm == "allow" else "⚠️"
        print(f"   {icon} '{cmd[:30]:30}' → {perm}")

    print("\n🔒 Testing Plan Agent Permissions:\n")
    print("   Read operations:")
    read_ops = ["ls", "cat file", "grep pattern", "git diff"]
    for cmd in read_ops:
        perm = plan_agent.config.check_bash_permission(cmd)
        icon = "✓" if perm == "allow" else "⚠️"
        print(f"   {icon} '{cmd[:30]:30}' → {perm}")

    print("\n   Write operations (should be restricted):")
    write_ops = ["rm file", "mv a b", "cp a b", "echo x > file"]
    for cmd in write_ops:
        perm = plan_agent.config.check_bash_permission(cmd)
        icon = "❌" if perm == "deny" else "⚠️"
        print(f"   {icon} '{cmd[:30]:30}' → {perm}")

    print("\n   Tool permissions:")
    tools = ["read", "edit", "bash", "grep"]
    for tool in tools:
        enabled = plan_agent.config.is_tool_enabled(tool)
        icon = "✓" if enabled else "❌"
        print(f"   {icon} {tool:30} → {'enabled' if enabled else 'disabled'}")


async def demo_message_lifecycle():
    """Demonstrate complete message lifecycle"""
    print("\n" + "█"*60)
    print("█" + " "*15 + "Message Lifecycle Demo" + " "*21 + "█")
    print("█"*60 + "\n")

    session = Session(
        project_id="lifecycle-demo",
        directory=str(Path.cwd()),
        title="Message Lifecycle Demo"
    )

    print(f"1️⃣  Created session: {session.id}\n")

    # User message
    user_msg = Message(session_id=session.id, role="user")
    user_msg.add_part(TextPart(
        session_id=session.id,
        message_id=user_msg.id,
        text="Run git status"
    ))

    print(f"2️⃣  User message: {user_msg.id}")
    print(f"   Content: {user_msg.get_text_content()}\n")

    # Assistant message with tool call
    assistant_msg = Message(
        session_id=session.id,
        role="assistant",
        agent="build"
    )

    # Add thinking
    assistant_msg.add_part(TextPart(
        session_id=session.id,
        message_id=assistant_msg.id,
        text="I'll run git status to check the repository state."
    ))

    # Add tool call
    tool_part = ToolPart(
        session_id=session.id,
        message_id=assistant_msg.id,
        tool="bash",
        call_id="tool_001",
        state=ToolState(
            status="success",
            input={"command": "git status", "description": "Check git status"},
            output="On branch claude/analyze-opencode-vibe-PYowW\nYour branch is up to date...",
            time_start=1234567890,
            time_end=1234567891
        )
    )
    assistant_msg.add_part(tool_part)

    # Add response
    assistant_msg.add_part(TextPart(
        session_id=session.id,
        message_id=assistant_msg.id,
        text="The repository is on the claude/analyze-opencode-vibe-PYowW branch and is up to date with origin."
    ))

    print(f"3️⃣  Assistant message: {assistant_msg.id}")
    print(f"   Agent: {assistant_msg.agent}")
    print(f"   Parts: {len(assistant_msg.parts)}")
    print(f"   - Text parts: {len(assistant_msg.get_text_parts())}")
    print(f"   - Tool parts: {len(assistant_msg.get_tool_parts())}")

    for i, part in enumerate(assistant_msg.parts, 1):
        print(f"\n   Part {i}: {part.type}")
        if isinstance(part, TextPart):
            print(f"      Text: {part.text[:60]}...")
        elif isinstance(part, ToolPart):
            print(f"      Tool: {part.tool}")
            print(f"      Status: {part.state.status}")
            print(f"      Output: {part.state.output[:60]}...")


async def main():
    """Run all advanced demonstrations"""

    # Session simulation
    session = Session(
        project_id="demo-project",
        directory=str(Path.cwd()),
        title="PyCode Exploration Session"
    )

    agent = BuildAgent()
    simulator = SessionSimulator(agent, session)

    await simulator.simulate_conversation()

    # Permission demo
    await demo_permission_system()

    # Message lifecycle
    await demo_message_lifecycle()

    print("\n" + "█"*60)
    print("█" + " "*10 + "Advanced Demonstrations Complete!" + " "*17 + "█")
    print("█"*60 + "\n")

    print("🎯 Demonstrated Advanced Features:")
    print("   ✓ Complete AI coding session simulation")
    print("   ✓ Multi-turn conversation with tool execution")
    print("   ✓ Permission system with glob pattern matching")
    print("   ✓ Message lifecycle with multiple part types")
    print("   ✓ Agent-based tool restrictions")
    print("   ✓ Safe vs dangerous command detection")

    print("\n💡 Key Takeaways:")
    print("   • Agents control what actions are permitted")
    print("   • Tools execute via a registry pattern")
    print("   • Messages contain typed parts (text, tool, etc.)")
    print("   • Storage provides session persistence")
    print("   • All operations are async for performance")


if __name__ == "__main__":
    asyncio.run(main())

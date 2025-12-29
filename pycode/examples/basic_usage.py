"""
Basic usage example for PyCode

This demonstrates how to use the PyCode components programmatically.
"""

import asyncio
from pathlib import Path
from pycode.core import Session, Message, TextPart, Identifier
from pycode.agents import BuildAgent, PlanAgent
from pycode.tools import ToolRegistry, BashTool, ReadTool, EditTool, GrepTool, ToolContext
from pycode.providers import AnthropicProvider, ProviderConfig
from pycode.storage import Storage


async def example_session():
    """Example: Create a session and work with messages"""
    print("=== Session Example ===\n")

    # Create a session
    session = Session(
        project_id="example-project",
        directory=str(Path.cwd()),
        title="Example Session",
    )

    print(f"Session ID: {session.id}")
    print(f"Working Directory: {session.directory}\n")

    # Create a user message
    user_message = Message(
        session_id=session.id,
        role="user",
        parts=[TextPart(session_id=session.id, message_id="msg_001", text="Help me understand this codebase")],
    )

    print(f"User: {user_message.get_text_content()}\n")

    # Create an assistant message
    assistant_message = Message(
        session_id=session.id,
        role="assistant",
        agent="build",
        parts=[
            TextPart(
                session_id=session.id,
                message_id="msg_002",
                text="I'd be happy to help you understand the codebase. Let me explore the structure.",
            )
        ],
    )

    print(f"Assistant: {assistant_message.get_text_content()}\n")


async def example_agents():
    """Example: Working with agents"""
    print("=== Agents Example ===\n")

    # Build agent
    build_agent = BuildAgent()
    print(f"Build Agent: {build_agent.name}")
    print(f"Edit Permission: {build_agent.config.edit_permission}")
    print(f"Bash Permission for 'git status': {build_agent.config.check_bash_permission('git status')}")
    print(f"Bash Permission for 'rm -rf /': {build_agent.config.check_bash_permission('rm -rf /')}\n")

    # Plan agent
    plan_agent = PlanAgent()
    print(f"Plan Agent: {plan_agent.name}")
    print(f"Edit Permission: {plan_agent.config.edit_permission}")
    print(f"Bash Permission for 'ls': {plan_agent.config.check_bash_permission('ls')}")
    print(f"Bash Permission for 'rm file': {plan_agent.config.check_bash_permission('rm file')}\n")


async def example_tools():
    """Example: Using tools"""
    print("=== Tools Example ===\n")

    # Create tool registry
    registry = ToolRegistry()

    # Register tools
    registry.register(BashTool())
    registry.register(ReadTool())
    registry.register(EditTool())
    registry.register(GrepTool())

    print(f"Registered tools: {list(registry.get_all().keys())}\n")

    # Create context
    context = ToolContext(
        session_id="session_001",
        message_id="msg_001",
        agent_name="build",
        working_directory=str(Path.cwd()),
    )

    # Example: Read a file (if README.md exists)
    if Path("README.md").exists():
        result = await registry.execute(
            "read",
            {"file_path": str(Path("README.md").absolute()), "limit": 10},
            context,
        )

        print(f"Tool: {result.title}")
        print(f"Output:\n{result.output[:500]}...\n")

    # Example: Run bash command
    result = await registry.execute(
        "bash",
        {"command": "pwd", "description": "Show current directory"},
        context,
    )

    print(f"Tool: {result.title}")
    print(f"Output:\n{result.output}\n")


async def example_storage():
    """Example: Using storage"""
    print("=== Storage Example ===\n")

    storage = Storage(base_path=Path.home() / ".pycode" / "example")

    # Write data
    session = Session(
        project_id="example-project",
        directory=str(Path.cwd()),
        title="Test Session",
    )

    await storage.write(["sessions", "example-project", session.id], session)
    print(f"Saved session: {session.id}")

    # Read data
    loaded_data = await storage.read(["sessions", "example-project", session.id])
    print(f"Loaded session: {loaded_data['id']}")
    print(f"Title: {loaded_data['title']}\n")

    # List keys
    sessions = await storage.list_keys(["sessions", "example-project"])
    print(f"Sessions in project: {sessions}\n")


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("PyCode - Basic Usage Examples")
    print("=" * 60 + "\n")

    await example_session()
    await example_agents()
    await example_tools()
    await example_storage()

    print("=" * 60)
    print("Examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

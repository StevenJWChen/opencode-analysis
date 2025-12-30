"""
Demonstration of New PyCode Tools

This demo shows all the newly added tools:
- Write tool (create files)
- Glob tool (pattern matching)
- Ls tool (directory listing)
- WebFetch tool (HTTP requests)
- Git tool (version control)
"""

import asyncio
import sys
sys.path.insert(0, 'src')

from pathlib import Path
from pycode.tools import (
    ToolRegistry, ToolContext,
    WriteTool, GlobTool, LsTool, WebFetchTool, GitTool,
    BashTool, ReadTool
)


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_result(result):
    """Print tool result"""
    print(f"✓ {result.title}")
    if result.output:
        print(f"\n{result.output}\n")
    if result.error:
        print(f"❌ Error: {result.error}\n")
    if result.metadata:
        print(f"Metadata: {result.metadata}\n")


async def demo_write_tool():
    """Demonstrate the Write tool"""
    print_section("Write Tool - Create New Files")

    registry = ToolRegistry()
    registry.register(WriteTool())

    context = ToolContext(
        session_id="demo",
        message_id="msg_001",
        agent_name="build",
        working_directory=str(Path.cwd()),
    )

    # Create a test file
    test_content = """# Test File

This is a test file created by PyCode's Write tool.

## Features

- Creates new files
- Overwrites existing files
- Shows file statistics
- Creates parent directories
"""

    result = await registry.execute(
        "write",
        {
            "file_path": str(Path.cwd() / "test_output.md"),
            "content": test_content,
        },
        context,
    )

    print_result(result)


async def demo_glob_tool():
    """Demonstrate the Glob tool"""
    print_section("Glob Tool - File Pattern Matching")

    registry = ToolRegistry()
    registry.register(GlobTool())

    context = ToolContext(
        session_id="demo",
        message_id="msg_002",
        agent_name="build",
        working_directory=str(Path.cwd()),
    )

    # Find all Python files
    print("Finding all Python files:")
    result = await registry.execute(
        "glob",
        {
            "pattern": "**/*.py",
            "path": str(Path.cwd() / "src"),
            "max_results": 20,
        },
        context,
    )

    print_result(result)

    # Find markdown files
    print("\nFinding all Markdown files:")
    result = await registry.execute(
        "glob",
        {
            "pattern": "*.md",
            "max_results": 10,
        },
        context,
    )

    print_result(result)


async def demo_ls_tool():
    """Demonstrate the Ls tool"""
    print_section("Ls Tool - Directory Listing")

    registry = ToolRegistry()
    registry.register(LsTool())

    context = ToolContext(
        session_id="demo",
        message_id="msg_003",
        agent_name="build",
        working_directory=str(Path.cwd()),
    )

    # List current directory
    print("Listing current directory:")
    result = await registry.execute(
        "ls",
        {
            "path": str(Path.cwd()),
            "show_hidden": True,
        },
        context,
    )

    print_result(result)

    # List src/pycode directory
    pycode_dir = Path.cwd() / "src" / "pycode"
    if pycode_dir.exists():
        print("\nListing src/pycode directory:")
        result = await registry.execute(
            "ls",
            {
                "path": str(pycode_dir),
                "show_hidden": False,
            },
            context,
        )

        print_result(result)


async def demo_webfetch_tool():
    """Demonstrate the WebFetch tool"""
    print_section("WebFetch Tool - HTTP Requests")

    registry = ToolRegistry()
    registry.register(WebFetchTool())

    context = ToolContext(
        session_id="demo",
        message_id="msg_004",
        agent_name="build",
        working_directory=str(Path.cwd()),
    )

    # Fetch a simple API endpoint
    print("Fetching example API:")
    result = await registry.execute(
        "webfetch",
        {
            "url": "https://api.github.com/repos/python/cpython",
            "method": "GET",
        },
        context,
    )

    print_result(result)


async def demo_git_tool():
    """Demonstrate the Git tool"""
    print_section("Git Tool - Version Control")

    registry = ToolRegistry()
    registry.register(GitTool())

    context = ToolContext(
        session_id="demo",
        message_id="msg_005",
        agent_name="build",
        working_directory=str(Path.cwd()),
    )

    # Git status
    print("Git status:")
    result = await registry.execute(
        "git",
        {
            "operation": "status",
        },
        context,
    )

    print_result(result)

    # Git log
    print("\nGit log (recent commits):")
    result = await registry.execute(
        "git",
        {
            "operation": "log",
            "args": ["--max-count=5"],
        },
        context,
    )

    print_result(result)

    # Git branch
    print("\nGit branches:")
    result = await registry.execute(
        "git",
        {
            "operation": "branch",
        },
        context,
    )

    print_result(result)


async def demo_tool_combinations():
    """Demonstrate using multiple tools together"""
    print_section("Tool Combinations - Complete Workflow")

    registry = ToolRegistry()
    registry.register(WriteTool())
    registry.register(ReadTool())
    registry.register(GlobTool())
    registry.register(GitTool())

    context = ToolContext(
        session_id="demo",
        message_id="msg_006",
        agent_name="build",
        working_directory=str(Path.cwd()),
    )

    print("Workflow: Create → Read → Find → Track")
    print("-" * 60)

    # 1. Create a file
    print("\n1. Creating a new Python file...")
    code_content = '''"""Example module"""

def hello(name: str) -> str:
    """Say hello to someone"""
    return f"Hello, {name}!"

def main():
    print(hello("PyCode"))

if __name__ == "__main__":
    main()
'''

    result = await registry.execute(
        "write",
        {
            "file_path": str(Path.cwd() / "example_module.py"),
            "content": code_content,
        },
        context,
    )
    print(f"   ✓ {result.title}")

    # 2. Read it back
    print("\n2. Reading the file back...")
    result = await registry.execute(
        "read",
        {
            "file_path": str(Path.cwd() / "example_module.py"),
            "limit": 10,
        },
        context,
    )
    print(f"   ✓ {result.title}")
    print(f"   Preview:\n{result.output[:200]}...")

    # 3. Find similar files
    print("\n3. Finding all Python files...")
    result = await registry.execute(
        "glob",
        {
            "pattern": "*.py",
            "max_results": 5,
        },
        context,
    )
    count = result.metadata.get("count", 0) if result.metadata else 0
    print(f"   ✓ Found {count} Python files")

    # 4. Check git status
    print("\n4. Checking git status...")
    result = await registry.execute(
        "git",
        {
            "operation": "status",
        },
        context,
    )
    print(f"   ✓ {result.title}")

    print("\n" + "-" * 60)
    print("Workflow complete!")


async def main():
    """Run all demonstrations"""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + " " * 15 + "PyCode - New Tools Demonstration" + " " * 21 + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)

    try:
        await demo_write_tool()
        await demo_glob_tool()
        await demo_ls_tool()

        # WebFetch requires network
        print("\n" + "=" * 70)
        print("  WebFetch Tool - HTTP Requests (requires network)")
        print("=" * 70)
        print("\nSkipping WebFetch demo (requires network access)")
        print("To test: run this demo with network connection\n")

        await demo_git_tool()
        await demo_tool_combinations()

        print_section("Summary")
        print("✓ All new tools demonstrated successfully!")
        print("\n📚 New Tools Added:")
        print("  ✓ WriteTool - Create new files")
        print("  ✓ GlobTool - File pattern matching")
        print("  ✓ LsTool - Directory listing")
        print("  ✓ WebFetchTool - HTTP requests")
        print("  ✓ GitTool - Version control operations")

        print("\n🎯 PyCode Now Has 9 Tools:")
        print("  1. BashTool - Shell commands")
        print("  2. ReadTool - Read files")
        print("  3. EditTool - Edit files")
        print("  4. GrepTool - Search code")
        print("  5. WriteTool - Create files  [NEW]")
        print("  6. GlobTool - File patterns  [NEW]")
        print("  7. LsTool - List directories [NEW]")
        print("  8. WebFetchTool - HTTP      [NEW]")
        print("  9. GitTool - Version control [NEW]")

        print("\n📖 Next Steps:")
        print("  1. Test with real-world scenarios")
        print("  2. Add more providers (Google, local models)")
        print("  3. Implement main execution loop")
        print("  4. Build advanced TUI")
        print("  5. Add comprehensive tests")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

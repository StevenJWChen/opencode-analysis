"""
Vibe Coding Demo - Iterative Write-Run-Fix Workflow

This demonstrates the core feature of vibe coding:
1. AI writes code using tools
2. Code is executed
3. AI sees the output/errors
4. AI fixes issues
5. Repeat until working

This is what makes vibe coding powerful!
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from pathlib import Path
from pycode.core import Session
from pycode.agents import BuildAgent
from pycode.tools import (
    ToolRegistry,
    BashTool,
    ReadTool,
    WriteTool,
    EditTool,
    GrepTool,
)

# Try to import runner and provider, but it's okay if they fail
try:
    from pycode.runner import AgentRunner, RunConfig
    from pycode.providers import AnthropicProvider, ProviderConfig
    HAS_RUNNER = True
except ImportError as e:
    HAS_RUNNER = False
    print(f"Note: Runner not available ({e})")


async def demo_write_run_fix():
    """
    Demonstrate the complete vibe coding workflow:
    Write → Run → Fix → Success
    """

    print("\n" + "=" * 70)
    print("  VIBE CODING DEMO - Write-Run-Fix Workflow")
    print("=" * 70)
    print()
    print("This demo shows how PyCode enables iterative development:")
    print("  1. User asks for a Python script")
    print("  2. AI writes the code (using WriteTool)")
    print("  3. AI runs it (using BashTool)")
    print("  4. If errors occur, AI sees them and fixes the code")
    print("  5. Repeat until it works!")
    print()
    print("=" * 70)
    print()

    # Check if we can run with real LLM
    if not HAS_RUNNER or not os.getenv("ANTHROPIC_API_KEY"):
        if not HAS_RUNNER:
            print("\n⚠️  AgentRunner not available - using mock demo instead\n")
        else:
            print("\n⚠️  ANTHROPIC_API_KEY not set - using mock demo instead\n")
        await demo_mock_workflow()
        return

    # Setup
    print("Setting up...")

    # Create session
    session = Session(
        project_id="vibe-demo",
        directory=str(Path.cwd() / "vibe_demo_workspace"),
        title="Vibe Coding Demo Session"
    )

    # Create workspace directory
    workspace = Path(session.directory)
    workspace.mkdir(parents=True, exist_ok=True)

    # Setup agent
    agent = BuildAgent()

    # Setup provider
    api_key = os.getenv("ANTHROPIC_API_KEY")

    provider_config = ProviderConfig(api_key=api_key)
    provider = AnthropicProvider(provider_config)

    # Setup tools
    registry = ToolRegistry()
    registry.register(WriteTool())
    registry.register(BashTool())
    registry.register(ReadTool())
    registry.register(EditTool())
    registry.register(GrepTool())

    # Create runner
    config = RunConfig(
        max_iterations=10,
        verbose=True,
        auto_approve_tools=True  # For demo
    )

    runner = AgentRunner(
        session=session,
        agent=agent,
        provider=provider,
        registry=registry,
        config=config
    )

    # User request
    user_request = """
Write a Python script called 'fibonacci.py' that:
1. Defines a fibonacci function that takes n and returns the nth fibonacci number
2. Has a main() function that prints the first 10 fibonacci numbers
3. Run the script to verify it works

Make sure to handle edge cases and run it to show me the output.
"""

    print("🎯 User Request:")
    print(user_request)
    print()
    print("=" * 70)
    print()

    # Run the vibe coding loop!
    print("🚀 Starting vibe coding loop...\n")

    try:
        async for chunk in runner.run(user_request):
            # Stream output to console
            print(chunk, end="", flush=True)

        print("\n\n" + "=" * 70)
        print("✅ Demo Complete!")
        print("=" * 70)

    except Exception as e:
        print(f"\n\n❌ Error: {e}")


async def demo_mock_workflow():
    """
    Mock demonstration showing the workflow without actual LLM calls
    """

    print("🎭 MOCK DEMO - Showing the workflow\n")

    workspace = Path("vibe_demo_workspace")
    workspace.mkdir(parents=True, exist_ok=True)

    # Simulated workflow
    steps = [
        ("💭 AI Thinking", "I'll write a fibonacci script..."),
        ("🔧 Tool: write", "Creating fibonacci.py..."),
        (
            "📝 Code Written",
            """def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)

def main():
    for i in range(10):
        print(f"F({i}) = {fibonacci(i)}")

if __name__ == "__main__":
    main()""",
        ),
        ("🔧 Tool: bash", "Running: python fibonacci.py"),
        (
            "📤 Output",
            """F(0) = 0
F(1) = 1
F(2) = 1
F(3) = 2
F(4) = 3
F(5) = 5
F(6) = 8
F(7) = 13
F(8) = 21
F(9) = 34""",
        ),
        ("✅ Success", "The script works correctly!"),
    ]

    for step_name, step_content in steps:
        print(f"\n{step_name}:")
        print("-" * 60)
        print(step_content)
        await asyncio.sleep(0.5)  # Simulate processing

    print("\n\n" + "=" * 70)
    print("This is what happens in a real vibe coding session:")
    print("=" * 70)
    print()
    print("1. ✅ AI writes code (using WriteTool)")
    print("2. ✅ AI runs it (using BashTool)")
    print("3. ✅ AI sees output/errors")
    print("4. ✅ If errors: AI fixes code (using EditTool)")
    print("5. ✅ Repeats until success")
    print()
    print("To see this with a real LLM, set ANTHROPIC_API_KEY and run again!")
    print()


async def demo_error_fix_workflow():
    """
    Demo showing how AI fixes errors in the code
    """

    print("\n\n" + "=" * 70)
    print("  ERROR-FIX WORKFLOW DEMO")
    print("=" * 70)
    print()

    # Simulated workflow with an error
    steps = [
        ("💭 AI", "Let me write a script to calculate factorials..."),
        ("🔧 write", "Creating factorial.py..."),
        (
            "📝 Code",
            """def factorial(n):
    result = 1
    for i in range(n):  # BUG: Should be range(1, n+1)
        result *= i
    return result

print(factorial(5))""",
        ),
        ("🔧 bash", "python factorial.py"),
        ("❌ Error", "0  # Wrong! Should be 120"),
        ("💭 AI", "I see the issue - range should start from 1, not 0"),
        ("🔧 edit", "Fixing the range..."),
        (
            "📝 Fixed",
            """def factorial(n):
    result = 1
    for i in range(1, n+1):  # Fixed!
        result *= i
    return result

print(factorial(5))""",
        ),
        ("🔧 bash", "python factorial.py"),
        ("✅ Output", "120  # Correct!"),
    ]

    for step_name, step_content in steps:
        print(f"\n{step_name}:")
        print("-" * 60)
        print(step_content)
        await asyncio.sleep(0.5)

    print("\n\n" + "=" * 70)
    print("This demonstrates the power of vibe coding:")
    print("  ✅ AI writes code")
    print("  ✅ AI runs it immediately")
    print("  ✅ AI sees the error")
    print("  ✅ AI fixes the bug")
    print("  ✅ AI verifies the fix")
    print()
    print("All automatically, in one conversation!")
    print("=" * 70)
    print()


async def main():
    """Run all demonstrations"""

    print("\n\n")
    print("█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + " " * 20 + "PYCODE - VIBE CODING DEMO" + " " * 23 + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)

    # Demo 1: Basic write-run-fix
    await demo_write_run_fix()

    # Demo 2: Error fixing
    await demo_error_fix_workflow()

    print("\n\n")
    print("=" * 70)
    print("  KEY TAKEAWAY")
    print("=" * 70)
    print()
    print("Vibe coding is all about the iterative loop:")
    print()
    print("  ┌─────────────────────────────────────┐")
    print("  │  1. AI Writes Code (WriteTool)      │")
    print("  │         ↓                            │")
    print("  │  2. AI Runs Code (BashTool)          │")
    print("  │         ↓                            │")
    print("  │  3. AI Sees Output/Errors            │")
    print("  │         ↓                            │")
    print("  │  4. AI Fixes Issues (EditTool)       │")
    print("  │         ↓                            │")
    print("  └─────────┴──────> Repeat until ✅     │")
    print()
    print("PyCode NOW supports this complete workflow!")
    print()
    print("With the AgentRunner, PyCode can:")
    print("  ✅ Write code")
    print("  ✅ Run it immediately")
    print("  ✅ See results and errors")
    print("  ✅ Fix issues automatically")
    print("  ✅ Iterate until success")
    print()
    print("This is the essence of vibe coding!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Run PyCode Vibe Coding Demo with Real LLM

This script runs the complete vibe coding demo using a real LLM.
It will load the API key from .env file or environment variables.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

# Load .env file if it exists
env_file = Path(".env")
if env_file.exists():
    print("📁 Loading API key from .env file...")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value
                print(f"   ✅ Set {key}")
    print()

from pycode.runner import AgentRunner, RunConfig
from pycode.core import Session
from pycode.agents import BuildAgent
from pycode.tools import (
    ToolRegistry,
    WriteTool,
    BashTool,
    ReadTool,
    EditTool,
    GrepTool,
)
from pycode.providers import AnthropicProvider, ProviderConfig


async def run_vibe_coding_demo():
    """
    Run a real vibe coding demo with LLM integration
    """

    print("\n" + "=" * 70)
    print("  PyCode Vibe Coding Demo - WITH REAL LLM!")
    print("=" * 70)
    print()

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ No API key found!")
        print()
        print("Please set up your API key first:")
        print("  python setup_api_key.py")
        print()
        print("Or set it manually:")
        print('  export ANTHROPIC_API_KEY="sk-ant-your-key-here"')
        print()
        return

    print("✅ API key found!")
    print()

    # Setup
    print("Setting up PyCode environment...")

    # Create session
    session = Session(
        project_id="vibe-demo",
        directory=str(Path.cwd() / "vibe_demo_workspace"),
        title="Vibe Coding Demo Session"
    )

    # Create workspace
    workspace = Path(session.directory)
    workspace.mkdir(parents=True, exist_ok=True)
    print(f"   Workspace: {workspace}")

    # Setup agent
    agent = BuildAgent()
    print(f"   Agent: {agent.name}")

    # Setup provider
    provider_config = ProviderConfig(api_key=api_key)
    provider = AnthropicProvider(provider_config)
    print(f"   Provider: Anthropic (Claude)")

    # Setup tools
    registry = ToolRegistry()
    registry.register(WriteTool())
    registry.register(BashTool())
    registry.register(ReadTool())
    registry.register(EditTool())
    registry.register(GrepTool())
    print(f"   Tools: {len(registry.get_all())} registered")

    # Create runner
    config = RunConfig(
        max_iterations=10,
        verbose=True,
        auto_approve_tools=True
    )
    runner = AgentRunner(session, agent, provider, registry, config)

    print()
    print("=" * 70)
    print()

    # Example requests - user can choose
    examples = [
        "Write a Python script that calculates the first 10 fibonacci numbers and prints them",
        "Create a simple calculator that adds two numbers, test it with 5 and 3",
        "Write a function that reverses a string and test it with 'Hello World'",
        "Create a script that counts words in a text file (create sample file first)",
    ]

    print("Choose a demo request:")
    for i, example in enumerate(examples, 1):
        print(f"  {i}. {example}")
    print(f"  5. Custom request")
    print()

    choice = input("Enter choice (1-5): ").strip()

    if choice == "5":
        user_request = input("\nEnter your custom request: ").strip()
    elif choice in ["1", "2", "3", "4"]:
        user_request = examples[int(choice) - 1]
    else:
        print("Invalid choice. Using default...")
        user_request = examples[0]

    print()
    print("=" * 70)
    print(f"🎯 Request: {user_request}")
    print("=" * 70)
    print()

    # Run the vibe coding loop!
    print("🚀 Starting vibe coding loop...\n")

    try:
        async for chunk in runner.run(user_request):
            print(chunk, end="", flush=True)

        print("\n\n" + "=" * 70)
        print("✅ Demo Complete!")
        print("=" * 70)
        print()
        print(f"Check the workspace for generated files: {workspace}")
        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n\n")
    print("█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + " " * 15 + "PyCode - REAL Vibe Coding Demo" + " " * 23 + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)

    asyncio.run(run_vibe_coding_demo())

    print("\n\n" + "=" * 70)
    print("  What Just Happened?")
    print("=" * 70)
    print()
    print("You just witnessed REAL vibe coding:")
    print()
    print("  1. ✅ Claude (real LLM) received your request")
    print("  2. ✅ Claude decided what code to write")
    print("  3. ✅ Claude used WriteTool to create the file")
    print("  4. ✅ Claude used BashTool to run it")
    print("  5. ✅ Claude saw the actual output")
    print("  6. ✅ If errors: Claude fixed them automatically")
    print("  7. ✅ Claude verified it works")
    print()
    print("This is the power of vibe coding!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Exiting...")
        sys.exit(0)

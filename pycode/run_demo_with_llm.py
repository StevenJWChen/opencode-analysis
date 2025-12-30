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
from pycode.provider_factory import ProviderFactory
from pycode.config import ModelConfig, ProviderSettings
from pycode.storage import Storage
from pycode.config import load_config


async def run_vibe_coding_demo():
    """
    Run a real vibe coding demo with LLM integration
    """

    print("\n" + "=" * 70)
    print("  PyCode Vibe Coding Demo - WITH REAL LLM!")
    print("=" * 70)
    print()

    # Check for Ollama (no API key needed!)
    print("Checking for Ollama...")
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/version", timeout=2)
        ollama_available = response.status_code == 200
    except:
        ollama_available = False

    if not ollama_available:
        print("❌ Ollama not running!")
        print()
        print("To use this demo with Ollama:")
        print("  1. Install Ollama from https://ollama.com/download")
        print("  2. Run: ollama serve")
        print("  3. Pull a model: ollama pull llama3.2")
        print()
        print("Then run this script again!")
        print()
        return

    print("✅ Ollama is running!")
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
    # Override model_id to use Ollama
    agent.config.model_id = "llama3.2:latest"
    print(f"   Agent: {agent.name}")

    # Setup Ollama provider (no API key needed!)
    model_config = ModelConfig(
        provider="ollama",
        model_id="llama3.2:latest",
        temperature=0.7,
        max_tokens=4096
    )
    provider_settings = ProviderSettings(
        base_url="http://localhost:11434",
        timeout=120
    )
    provider = ProviderFactory.create_provider(
        provider_type="ollama",
        model_config=model_config,
        provider_settings=provider_settings
    )
    print(f"   Provider: Ollama (Local LLM)")

    # Setup tools
    registry = ToolRegistry()
    registry.register(WriteTool())
    registry.register(BashTool())
    registry.register(ReadTool())
    registry.register(EditTool())
    registry.register(GrepTool())
    print(f"   Tools: {len(registry.get_all())} registered")

    # Load configuration
    pycode_config = load_config()

    # Create storage for history management
    storage = Storage()

    # Create runner with new features
    config = RunConfig(
        max_iterations=pycode_config.runtime.max_iterations,
        verbose=True,
        auto_approve_tools=True,
        doom_loop_detection=pycode_config.runtime.doom_loop_detection,
        doom_loop_threshold=pycode_config.runtime.doom_loop_threshold,
    )
    runner = AgentRunner(session, agent, provider, registry, config, storage)

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
    print("You just witnessed REAL vibe coding with NEW features:")
    print()
    print("  1. ✅ Ollama (local LLM) received your request")
    print("  2. ✅ Ollama decided what code to write")
    print("  3. ✅ Ollama used WriteTool to create the file")
    print("  4. ✅ Ollama used BashTool to run it")
    print("  5. ✅ Ollama saw the actual output")
    print("  6. ✅ If errors: Ollama fixed them automatically")
    print("  7. ✅ Ollama verified it works")
    print()
    print("Benefits of using Ollama:")
    print("  🎉 Runs locally - no internet needed")
    print("  🎉 No API key required - completely free")
    print("  🎉 Private - your code never leaves your machine")
    print("  🎉 Session was saved - you can resume it later!")
    print("  🎉 Message history was persisted to storage")
    print("  🎉 Doom loop detection prevented infinite loops")
    print("  🎉 Configuration loaded from config file")
    print()
    print("This is the power of vibe coding with local LLMs!")
    print("=" * 70)
    print()
    print("Try the new CLI commands:")
    print("  python pycode_cli.py list         - See all sessions")
    print("  python pycode_cli.py resume <id>  - Resume this session")
    print("  python pycode_cli.py stats        - View statistics")
    print("=" * 70)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Exiting...")
        sys.exit(0)

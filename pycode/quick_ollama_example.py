#!/usr/bin/env python3
"""
Quick example of using PyCode with Ollama

This example uses the configuration system for easy provider management.
You can switch to any other provider by updating pycode.yaml!

Prerequisites for Ollama:
1. Install Ollama: https://ollama.com/download
2. Start Ollama: ollama serve
3. Pull a model: ollama pull llama3.2
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

sys.path.insert(0, 'src')

from pycode.config import load_config, ModelConfig, ProviderSettings
from pycode.provider_factory import ProviderFactory
from pycode.runner import AgentRunner, RunConfig
from pycode.agents.base import Agent, AgentConfig
from pycode.tools import ToolRegistry
from pycode.core import Session
from pycode.logging import configure_logging, LogLevel


async def main():
    """Main function"""
    print("🦙 PyCode with Ollama Example\n")

    # Configure logging
    configure_logging(level=LogLevel.NORMAL)
    
    # 1. Configure Ollama provider
    print("📡 Connecting to Ollama at http://localhost:11434...")
    config = ProviderConfig(
        name="ollama",
        base_url="http://localhost:11434",
        extra={"timeout": 120}
    )

    provider = OllamaProvider(config)
    
    # 2. Create session
    session = Session(
        project_id="ollama-demo",
        directory=str(Path.cwd()),
        title="Ollama Demo"
    )

    # Create agent with Ollama model
    print(f"\n🤖 Creating agent with model: {model_config.model_id}...")
    agent_config = AgentConfig(
        name="build",
        description="Full-access development agent for Ollama",
        mode="primary",
        model_id=model_config.model_id,
        edit_permission="allow",
        bash_permissions={"*": "allow"},
        skill_permissions={"*": "allow"},
        webfetch_permission="allow",
    )

    class OllamaBuildAgent(Agent):
        async def get_system_prompt(self) -> str:
            return """You are a helpful AI coding assistant with full access to the codebase.

You have the following capabilities:
- Read and edit files
- Execute bash commands
- Search code
- Analyze the project structure
- Make changes to implement features and fix bugs

When working on tasks:
1. Understand the request thoroughly
2. Read relevant files to understand context
3. Make targeted, precise changes
4. Test your changes when possible
5. Explain what you did and why

Use your tools effectively to accomplish the task. Be proactive but careful with file changes and bash commands.
"""

    agent = OllamaBuildAgent(agent_config)
    registry = ToolRegistry()

    # Configure runner
    run_config = RunConfig(
        verbose=True,
        max_iterations=5,
        auto_approve_tools=True,  # For demo only
        doom_loop_detection=True
    )

    runner = AgentRunner(
        session=session,
        agent=agent,
        provider=provider,
        registry=registry,
        config=run_config
    )

    # Run a simple task
    print("\n🚀 Running task: Create a hello world Python script\n")
    print("=" * 60)

    try:
        async for chunk in runner.run("Create a Python script called hello.py that prints 'Hello from PyCode + Ollama!'"):
            print(chunk, end="", flush=True)

        print("\n" + "=" * 60)
        print("\n✅ Task completed successfully!")
        print("\n💡 Benefits of Ollama:")
        print("   ✓ Runs locally - no internet needed")
        print("   ✓ Free - no API costs")
        print("   ✓ Private - your code never leaves your machine")
        print("   ✓ Fast - optimized for local inference")
        print("\n💡 Try other Ollama models:")
        print("   ollama pull codellama      # Optimized for code")
        print("   ollama pull mistral        # Good general model")
        print("   ollama pull llama3.2:70b   # Larger, more capable")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is Ollama running? (ollama serve)")
        print("  2. Is the model downloaded? (ollama pull llama3.2)")
        print("  3. Check connection: curl http://localhost:11434/api/version")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  PyCode + Ollama Quick Example")
    print("=" * 60 + "\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

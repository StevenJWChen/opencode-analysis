#!/usr/bin/env python3
"""
Quick Start Example - Works with ANY provider!

This example demonstrates how to use PyCode with any provider through simple configuration.
No code changes needed to switch between providers - just update the config file!

Supported providers:
  - Anthropic (Claude) - API key required
  - Ollama (local) - Free, runs locally
  - OpenAI (GPT) - API key required
  - Gemini (Google) - API key required
  - Mistral - API key required
  - Cohere - API key required

Quick start:
  1. Copy pycode.yaml.example to pycode.yaml
  2. Configure your preferred provider
  3. Run this script!
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

from pycode.config import load_config, ConfigManager
from pycode.provider_factory import ProviderFactory
from pycode.runner import AgentRunner, RunConfig
from pycode.agents.base import Agent, AgentConfig
from pycode.tools import ToolRegistry
from pycode.core import Session
from pycode.logging import configure_logging, LogLevel


async def main():
    """Main example function"""

    print("=" * 70)
    print("  PyCode Quick Start - Works with ANY Provider!")
    print("=" * 70)

    # Configure logging
    configure_logging(level=LogLevel.NORMAL)

    # Load configuration
    print("\n📋 Loading configuration...")
    try:
        config = load_config()
        print(f"   ✓ Configuration loaded")
    except Exception as e:
        print(f"   ⚠ Could not load config: {e}")
        print("   ℹ Using default configuration (Ollama)")
        config = None

    # Determine which provider and model to use
    if config:
        provider_name = config.default_model.provider
        model_id = config.default_model.model_id
        provider_settings = config.providers.get(provider_name)
    else:
        # Fallback defaults - using Ollama (free, local, no API key needed)
        provider_name = "ollama"
        model_id = "llama3.2:latest"
        from pycode.config import ProviderSettings
        provider_settings = ProviderSettings(
            base_url="http://localhost:11434",
            timeout=120
        )

    print(f"\n🤖 Provider: {provider_name}")
    print(f"   Model: {model_id}")

    # Create provider using factory
    print(f"\n📡 Connecting to {provider_name}...")
    try:
        provider = ProviderFactory.create_provider(
            provider_type=provider_name,
            model_config=config.default_model if config else None,
            provider_settings=provider_settings,
        )
        print(f"   ✓ Connected to {provider_name}")
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        print("\nTroubleshooting:")
        if provider_name == "ollama":
            print("  1. Is Ollama running? (ollama serve)")
            print("  2. Is a model installed? (ollama pull llama3.2)")
            print("  3. Check: curl http://localhost:11434/api/version")
            print("  4. Install Ollama from: https://ollama.com/download")
        else:
            print(f"  1. Is your {provider_name.upper()}_API_KEY set?")
            print(f"  2. Check your internet connection")
        sys.exit(1)

    # Create session
    session = Session(
        project_id="quickstart",
        directory=str(Path.cwd()),
        title="Quick Start Demo"
    )

    # Create agent
    print(f"\n🔧 Creating agent...")
    agent_config = AgentConfig(
        name="build",
        description=f"Build agent using {provider_name}",
        mode="primary",
        model_id=model_id,
        edit_permission="allow",
        bash_permissions={"*": "allow"},
        skill_permissions={"*": "allow"},
        webfetch_permission="allow",
    )

    class BuildAgent(Agent):
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

    agent = BuildAgent(agent_config)
    registry = ToolRegistry()

    # Configure runner
    run_config = RunConfig(
        verbose=True,
        max_iterations=5,
        auto_approve_tools=True,  # For demo only - set to False for production
        doom_loop_detection=True
    )

    runner = AgentRunner(
        session=session,
        agent=agent,
        provider=provider,
        registry=registry,
        config=run_config
    )

    # Run task
    print(f"\n🚀 Running task...")
    print("=" * 70)

    task = "Create a Python script called hello.py that prints 'Hello from PyCode!'"

    try:
        async for chunk in runner.run(task):
            print(chunk, end="", flush=True)

        print("\n" + "=" * 70)
        print("\n✅ Task completed successfully!")
        print("\n💡 Pro tip: Change the provider in pycode.yaml to try different models!")
        print("   Examples: anthropic, ollama, openai, gemini, mistral, cohere")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your provider configuration in pycode.yaml")
        print("  2. Ensure API keys are set (if needed)")
        print("  3. For Ollama: make sure it's running locally")


def print_config_help():
    """Print help for configuration"""
    print("\n" + "=" * 70)
    print("  Configuration Help")
    print("=" * 70)
    print("\nNo configuration file found. To get started:")
    print("\n1. Copy the example config:")
    print("   cp pycode.yaml.example pycode.yaml")
    print("\n2. Edit pycode.yaml and set your preferred provider:")
    print("\n   # For Ollama (local, free, no API key) - RECOMMENDED:")
    print("   default_model:")
    print("     provider: ollama")
    print("     model_id: llama3.2:latest")
    print("\n   # For Anthropic (Claude):")
    print("   default_model:")
    print("     provider: anthropic")
    print("     model_id: claude-3-5-sonnet-20241022")
    print("\n   # For OpenAI (GPT):")
    print("   default_model:")
    print("     provider: openai")
    print("     model_id: gpt-4-turbo-preview")
    print("\n3. For Ollama: Install and start:")
    print("   - Install from https://ollama.com/download")
    print("   - Run: ollama serve")
    print("   - Pull model: ollama pull llama3.2")
    print("\n4. For cloud providers, set API keys:")
    print("   export ANTHROPIC_API_KEY=sk-ant-...")
    print("   export OPENAI_API_KEY=sk-...")
    print("   export GEMINI_API_KEY=...")
    print("\n5. Run this script again!")
    print("=" * 70)


if __name__ == "__main__":
    # Check if config exists, if not show help
    config_manager = ConfigManager()
    if not config_manager._find_config_file() and not Path("pycode.yaml.example").exists():
        print("⚠️  Warning: No configuration file or example found")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

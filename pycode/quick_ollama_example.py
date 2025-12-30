#!/usr/bin/env python3
"""
Quick example of using PyCode with Ollama

Prerequisites:
1. Install Ollama: https://ollama.com/download
2. Start Ollama: ollama serve
3. Pull a model: ollama pull llama3.2
"""

import asyncio
import sys
sys.path.insert(0, 'src')

from pycode.providers.ollama_provider import OllamaProvider
from pycode.providers.base import ProviderConfig
from pycode.runner import AgentRunner, RunConfig
from pycode.agents import BuildAgent
from pycode.tools import ToolRegistry
from pycode.core import Session
from pycode.logging import configure_logging, LogLevel


async def main():
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
        id="ollama-demo",
        project_id="demo",
        directory="."
    )
    
    # 3. Create agent and tools
    agent = BuildAgent()
    registry = ToolRegistry()
    
    # 4. Configure runner
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
    
    # 5. Run a simple task
    print("\n🚀 Running task: Create a hello world Python script\n")
    print("=" * 60)
    
    try:
        async for chunk in runner.run("Create a Python script called hello.py that prints 'Hello from PyCode + Ollama!'"):
            print(chunk, end="", flush=True)
        
        print("\n" + "=" * 60)
        print("\n✅ Task completed successfully!")
        
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
        sys.exit(1)

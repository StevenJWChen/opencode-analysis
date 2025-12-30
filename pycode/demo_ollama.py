#!/usr/bin/env python3
"""
Ollama Provider Demo

Demonstrates PyCode with local Ollama models.

Prerequisites:
1. Install Ollama: https://ollama.ai/download
2. Start Ollama: ollama serve
3. Pull a model: ollama pull llama3.2
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from pycode.providers import OllamaProvider, ProviderConfig
from pycode.core import Session
from pycode.agents import BuildAgent
from pycode.tools import (
    ToolRegistry,
    WriteTool,
    ReadTool,
    BashTool,
    GrepTool,
)
from pycode.runner import AgentRunner, RunConfig
from pycode.storage import Storage


async def check_ollama_available():
    """Check if Ollama is running and has models"""
    print("🔍 Checking Ollama availability...")

    config = ProviderConfig(base_url="http://localhost:11434")
    provider = OllamaProvider(config)

    try:
        # List available models
        models = await provider.list_models()

        if not models:
            print("\n❌ No Ollama models found!")
            print("\nTo install models:")
            print("  ollama pull llama3.2        # Smaller, faster")
            print("  ollama pull llama3.2:70b    # Larger, better")
            print("  ollama pull mistral         # Alternative")
            print("  ollama pull codellama       # Code-focused")
            await provider.close()
            return None

        print(f"\n✅ Ollama is running!")
        print(f"   Found {len(models)} models:\n")
        for model in models:
            print(f"   • {model}")

        await provider.close()
        return models

    except Exception as e:
        print(f"\n❌ Cannot connect to Ollama: {e}")
        print("\nMake sure Ollama is running:")
        print("  1. Install: https://ollama.ai/download")
        print("  2. Start: ollama serve")
        print("  3. Pull model: ollama pull llama3.2")
        return None


async def demo_ollama_basic():
    """Basic Ollama streaming demo"""
    print("\n" + "="*70)
    print("  Demo 1: Basic Ollama Streaming")
    print("="*70 + "\n")

    config = ProviderConfig(base_url="http://localhost:11434")
    provider = OllamaProvider(config)

    print("💬 Request: Explain what vibe coding is in one sentence\n")
    print("🤖 Response: ", end="", flush=True)

    try:
        async for event in provider.stream(
            model="llama3.2",
            messages=[{"role": "user", "content": "Explain what vibe coding is in one sentence"}],
            temperature=0.7,
            max_tokens=100,
        ):
            if event.type == "text_delta":
                print(event.data.get("text", ""), end="", flush=True)

        print("\n")
        await provider.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        await provider.close()


async def demo_ollama_vibe_coding():
    """Full vibe coding demo with Ollama"""
    print("\n" + "="*70)
    print("  Demo 2: Vibe Coding with Ollama")
    print("="*70 + "\n")

    # Setup
    storage = Storage()
    session = Session(
        project_id="ollama-demo",
        directory="/tmp",
        title="Ollama Vibe Coding Demo"
    )

    agent = BuildAgent()

    # Use Ollama provider
    config = ProviderConfig(base_url="http://localhost:11434")
    provider = OllamaProvider(config)

    # Setup tools
    registry = ToolRegistry()
    registry.register(WriteTool())
    registry.register(ReadTool())
    registry.register(BashTool())
    registry.register(GrepTool())

    print(f"🤖 Using: Ollama (llama3.2)")
    print(f"🔧 Tools: {len(registry.get_all())} tools")
    print(f"📁 Session: {session.id}\n")

    # Create runner
    run_config = RunConfig(
        max_iterations=5,
        verbose=True,
        auto_approve_tools=True,
    )

    runner = AgentRunner(
        session=session,
        agent=agent,
        provider=provider,
        registry=registry,
        config=run_config,
        storage=storage,
    )

    # Run request
    request = "Write a Python function that calculates fibonacci numbers and test it with n=10"

    print(f"💬 Request: {request}")
    print("\n" + "="*70)
    print("🚀 Running with local Ollama model...")
    print("="*70 + "\n")

    try:
        async for chunk in runner.run(request):
            print(chunk, end="", flush=True)

        print("\n" + "="*70)
        print("✅ Vibe Coding Complete!")
        print("="*70 + "\n")

        print("📊 What happened:")
        print("   ✅ Local LLM (no API key needed!)")
        print("   ✅ No internet required")
        print("   ✅ No API costs")
        print("   ✅ Complete privacy")
        print("   ✅ Real tools executed")
        print("   ✅ Code written and tested")

    except Exception as e:
        print(f"\n❌ Error: {e}")

    finally:
        await provider.close()


async def demo_ollama_function_calling():
    """Demo function calling with Ollama"""
    print("\n" + "="*70)
    print("  Demo 3: Function Calling with Ollama")
    print("="*70 + "\n")

    config = ProviderConfig(base_url="http://localhost:11434")
    provider = OllamaProvider(config)

    # Define tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    print("💬 Request: What's the weather in San Francisco?\n")
    print("🤖 Response:\n")

    try:
        async for event in provider.stream(
            model="llama3.2",
            messages=[{"role": "user", "content": "What's the weather in San Francisco?"}],
            tools=tools,
            temperature=0.7,
        ):
            if event.type == "text_delta":
                print(event.data.get("text", ""), end="", flush=True)
            elif event.type == "tool_use":
                print(f"\n\n🔧 Tool Call:")
                print(f"   Name: {event.data.get('name')}")
                print(f"   Args: {event.data.get('arguments')}")

        print("\n")
        await provider.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        await provider.close()


async def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("  PyCode + Ollama - Local LLM Demo")
    print("="*70)

    # Check if Ollama is available
    models = await check_ollama_available()
    if not models:
        print("\n❌ Ollama is not available. Exiting.")
        return

    # Ask which demo to run
    print("\n" + "-"*70)
    print("Select demo:")
    print("  1. Basic streaming")
    print("  2. Full vibe coding (write-run-fix)")
    print("  3. Function calling")
    print("  4. All demos")
    print("-"*70)

    choice = input("\nChoice [1-4]: ").strip()

    if choice == "1":
        await demo_ollama_basic()
    elif choice == "2":
        await demo_ollama_vibe_coding()
    elif choice == "3":
        await demo_ollama_function_calling()
    elif choice == "4":
        await demo_ollama_basic()
        await demo_ollama_vibe_coding()
        await demo_ollama_function_calling()
    else:
        print("Invalid choice. Running all demos...")
        await demo_ollama_basic()
        await demo_ollama_vibe_coding()
        await demo_ollama_function_calling()

    print("\n" + "="*70)
    print("  Demo Complete!")
    print("="*70)
    print("\n🎉 You just ran vibe coding with a LOCAL model!")
    print("   • No API key needed")
    print("   • No internet required")
    print("   • No costs")
    print("   • Complete privacy")
    print("\nTry other models:")
    print("  ollama pull mistral")
    print("  ollama pull codellama")
    print("  ollama pull llama3.2:70b")
    print("\nThen use them in PyCode:")
    print("  python pycode_cli.py run --model mistral \"your request\"")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

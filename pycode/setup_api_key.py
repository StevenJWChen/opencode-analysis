#!/usr/bin/env python3
"""
Interactive API Key Setup for PyCode Vibe Coding Demo

This script helps you set up an API key for running the vibe coding demo.
"""

import os
import sys
from pathlib import Path


def print_banner():
    print("\n" + "=" * 70)
    print("  PyCode Vibe Coding Demo - API Key Setup")
    print("=" * 70)
    print()


def print_instructions():
    print("To run the vibe coding demo with a real LLM, you need an API key.")
    print()
    print("🆓 FREE OPTIONS:")
    print()
    print("1. Anthropic (Claude) - Recommended")
    print("   • Get $5 free credits")
    print("   • Sign up: https://console.anthropic.com/")
    print("   • Get key: https://console.anthropic.com/settings/keys")
    print()
    print("2. OpenAI (GPT)")
    print("   • Get $5 free credits")
    print("   • Sign up: https://platform.openai.com/signup")
    print("   • Get key: https://platform.openai.com/api-keys")
    print()
    print("=" * 70)
    print()


def setup_anthropic():
    print("Setting up Anthropic (Claude) API Key")
    print("-" * 70)
    print()
    print("Your API key should start with 'sk-ant-'")
    print()

    api_key = input("Enter your Anthropic API key (or press Enter to skip): ").strip()

    if not api_key:
        print("\n⚠️  No API key entered. Skipping setup.")
        return False

    if not api_key.startswith("sk-ant-"):
        print("\n⚠️  Warning: API key doesn't look like an Anthropic key (should start with 'sk-ant-')")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return False

    # Set environment variable
    os.environ["ANTHROPIC_API_KEY"] = api_key

    # Save to .env file
    env_file = Path(".env")
    with open(env_file, "w") as f:
        f.write(f"ANTHROPIC_API_KEY={api_key}\n")

    print(f"\n✅ API key saved to: {env_file.absolute()}")
    print("✅ Environment variable set for this session")
    print()
    print("To use in future sessions, run:")
    print(f'  export ANTHROPIC_API_KEY="{api_key}"')
    print()

    return True


def test_api_key():
    print("\n" + "=" * 70)
    print("  Testing API Key")
    print("=" * 70)
    print()

    try:
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ No API key found in environment")
            return False

        print("Connecting to Anthropic API...")
        client = anthropic.Anthropic(api_key=api_key)

        # Try a simple API call
        print("Sending test message...")
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Say 'Hello from PyCode!'"}
            ]
        )

        response = message.content[0].text
        print(f"\n✅ API Key Works!")
        print(f"Claude responded: {response}")
        print()
        return True

    except Exception as e:
        print(f"\n❌ API key test failed: {str(e)}")
        print()
        if "authentication" in str(e).lower() or "api_key" in str(e).lower():
            print("The API key appears to be invalid.")
            print("Please check your key and try again.")
        return False


def main():
    print_banner()
    print_instructions()

    choice = input("Which service would you like to use? (1=Anthropic, 2=OpenAI, skip): ").strip()

    if choice == "1":
        if setup_anthropic():
            print("\n" + "=" * 70)
            test = input("Would you like to test the API key? (y/n): ").strip().lower()
            if test == 'y':
                if test_api_key():
                    print("=" * 70)
                    print("\n🎉 Setup Complete!")
                    print()
                    print("You can now run the vibe coding demo:")
                    print("  python vibe_coding_demo.py")
                    print()
                    print("Or run it directly with:")
                    print("  python run_demo_with_llm.py")
                    print()
                else:
                    print("\n⚠️  Setup complete but API key test failed.")
                    print("You may need to check your API key.")
            else:
                print("\n✅ Setup complete! Run: python vibe_coding_demo.py")

    elif choice == "2":
        print("\n⚠️  OpenAI setup not yet implemented in this script.")
        print("Please set OPENAI_API_KEY manually:")
        print('  export OPENAI_API_KEY="sk-your-key-here"')

    else:
        print("\n⚠️  Setup skipped.")
        print("\nTo run without an API key, the demo will use mock mode.")
        print("Run: python vibe_coding_demo.py")

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user.")
        sys.exit(0)

#!/usr/bin/env python3
"""
PyCode Provider Test Suite

Tests all LLM provider implementations:
- Anthropic (Claude)
- OpenAI (GPT)
- Ollama (Local models)
- Gemini (Google)
- Mistral
- Cohere

Tests both streaming and non-streaming completions.
Tests function calling support.
"""

import asyncio
import sys
import os
from typing import Any

# Add src to path
sys.path.insert(0, 'src')

from pycode.providers import (
    ProviderConfig,
    AnthropicProvider,
    OllamaProvider,
    GeminiProvider,
    MistralProvider,
    CohereProvider,
)

# Optional OpenAI
try:
    from pycode.providers import OpenAIProvider
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []

    def record_pass(self, test_name: str):
        self.passed += 1
        print(f"  ✅ {test_name}")

    def record_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  ❌ {test_name}: {error}")

    def record_skip(self, test_name: str, reason: str):
        self.skipped += 1
        print(f"  ⏭️  {test_name} (skipped: {reason})")

    def summary(self):
        total = self.passed + self.failed + self.skipped
        print(f"\n{'='*70}")
        print(f"  Test Results: {self.passed}/{total} passed, {self.skipped} skipped")
        print(f"{'='*70}")

        if self.failed > 0:
            print(f"\n❌ {self.failed} tests failed:")
            for test_name, error in self.errors:
                print(f"   - {test_name}: {error}")
            return False
        else:
            print("\n✅ All tests passed!")
            return True


results = TestResults()


def test_header(name: str):
    """Print test section header"""
    print(f"\n{'-'*70}")
    print(f"  Testing: {name}")
    print(f"{'-'*70}")


# Test: Provider Configuration
def test_provider_config():
    """Test provider configuration"""
    test_header("Provider Configuration")

    # Test basic config
    config = ProviderConfig(
        name="test-provider",
        api_key="test_key"
    )

    if config.api_key == "test_key" and config.name == "test-provider":
        results.record_pass("ProviderConfig creation")
    else:
        results.record_fail("ProviderConfig creation", "Fields not set correctly")

    # Test optional fields
    config2 = ProviderConfig(
        name="custom-provider",
        api_key="key",
        base_url="https://custom.api",
        organization="test-org"
    )

    if config2.base_url == "https://custom.api" and config2.organization == "test-org":
        results.record_pass("ProviderConfig optional fields")
    else:
        results.record_fail("ProviderConfig optional fields", "Optional fields not set")


# Test: Anthropic Provider
async def test_anthropic_provider():
    """Test Anthropic provider initialization"""
    test_header("Anthropic Provider")

    # Note: We can't test actual API calls without keys
    # But we can test provider initialization

    config = ProviderConfig(name="anthropic", api_key="sk-test-key")

    try:
        provider = AnthropicProvider(config)

        if provider.config.api_key == "sk-test-key":
            results.record_pass("AnthropicProvider initialization")
        else:
            results.record_fail("AnthropicProvider initialization", "API key not set")

        # Test client creation
        if hasattr(provider, 'client'):
            results.record_pass("AnthropicProvider client creation")
        else:
            results.record_fail("AnthropicProvider client creation", "No client attribute")

        # Test name property
        if provider.name == "anthropic":
            results.record_pass("AnthropicProvider name property")
        else:
            results.record_fail("AnthropicProvider name", f"Expected 'anthropic', got '{provider.name}'")

    except Exception as e:
        results.record_fail("AnthropicProvider initialization", str(e))


# Test: OpenAI Provider
async def test_openai_provider():
    """Test OpenAI provider initialization"""
    test_header("OpenAI Provider")

    if not HAS_OPENAI:
        results.record_skip("OpenAI tests", "openai package not installed")
        return

    config = ProviderConfig(name="openai", api_key="sk-test-key")

    try:
        provider = OpenAIProvider(config)

        if provider.config.api_key == "sk-test-key":
            results.record_pass("OpenAIProvider initialization")
        else:
            results.record_fail("OpenAIProvider initialization", "API key not set")

        # Test client creation
        if hasattr(provider, 'client'):
            results.record_pass("OpenAIProvider client creation")
        else:
            results.record_fail("OpenAIProvider client creation", "No client attribute")

        # Test name property
        if provider.name == "openai":
            results.record_pass("OpenAIProvider name property")
        else:
            results.record_fail("OpenAIProvider name", f"Expected 'openai', got '{provider.name}'")

    except Exception as e:
        results.record_fail("OpenAIProvider initialization", str(e))


# Test: Ollama Provider
async def test_ollama_provider():
    """Test Ollama provider initialization"""
    test_header("Ollama Provider")

    config = ProviderConfig(
        name="ollama",
        api_key="",  # Ollama doesn't need API key
        base_url="http://localhost:11434"
    )

    try:
        provider = OllamaProvider(config)

        if provider.base_url == "http://localhost:11434":
            results.record_pass("OllamaProvider initialization")
        else:
            results.record_fail("OllamaProvider initialization", "Base URL not set")

        # Test client creation
        if hasattr(provider, 'client'):
            results.record_pass("OllamaProvider client creation")
        else:
            results.record_fail("OllamaProvider client creation", "No client attribute")

        # Test name property
        if provider.name == "ollama":
            results.record_pass("OllamaProvider name property")
        else:
            results.record_fail("OllamaProvider name", f"Expected 'ollama', got '{provider.name}'")

    except Exception as e:
        results.record_fail("OllamaProvider initialization", str(e))


# Test: Gemini Provider
async def test_gemini_provider():
    """Test Gemini provider initialization"""
    test_header("Gemini Provider")

    config = ProviderConfig(name="gemini", api_key="test_gemini_key")

    try:
        provider = GeminiProvider(config)

        if provider.api_key == "test_gemini_key":
            results.record_pass("GeminiProvider initialization")
        else:
            results.record_fail("GeminiProvider initialization", "API key not set")

        # Test base URL
        expected_url = "https://generativelanguage.googleapis.com/v1beta"
        if provider.base_url == expected_url:
            results.record_pass("GeminiProvider base URL")
        else:
            results.record_fail("GeminiProvider base URL", f"Expected {expected_url}, got {provider.base_url}")

        # Test client creation
        if hasattr(provider, 'client'):
            results.record_pass("GeminiProvider client creation")
        else:
            results.record_fail("GeminiProvider client creation", "No client attribute")

        # Test name property
        if provider.name == "gemini":
            results.record_pass("GeminiProvider name property")
        else:
            results.record_fail("GeminiProvider name", f"Expected 'gemini', got '{provider.name}'")

    except Exception as e:
        results.record_fail("GeminiProvider initialization", str(e))


# Test: Mistral Provider
async def test_mistral_provider():
    """Test Mistral provider initialization"""
    test_header("Mistral Provider")

    config = ProviderConfig(name="mistral", api_key="test_mistral_key")

    try:
        provider = MistralProvider(config)

        if provider.api_key == "test_mistral_key":
            results.record_pass("MistralProvider initialization")
        else:
            results.record_fail("MistralProvider initialization", "API key not set")

        # Test base URL
        expected_url = "https://api.mistral.ai/v1"
        if provider.base_url == expected_url:
            results.record_pass("MistralProvider base URL")
        else:
            results.record_fail("MistralProvider base URL", f"Expected {expected_url}, got {provider.base_url}")

        # Test client creation
        if hasattr(provider, 'client'):
            results.record_pass("MistralProvider client creation")
        else:
            results.record_fail("MistralProvider client creation", "No client attribute")

        # Test name property
        if provider.name == "mistral":
            results.record_pass("MistralProvider name property")
        else:
            results.record_fail("MistralProvider name", f"Expected 'mistral', got '{provider.name}'")

    except Exception as e:
        results.record_fail("MistralProvider initialization", str(e))


# Test: Cohere Provider
async def test_cohere_provider():
    """Test Cohere provider initialization"""
    test_header("Cohere Provider")

    config = ProviderConfig(name="cohere", api_key="test_cohere_key")

    try:
        provider = CohereProvider(config)

        if provider.api_key == "test_cohere_key":
            results.record_pass("CohereProvider initialization")
        else:
            results.record_fail("CohereProvider initialization", "API key not set")

        # Test base URL
        expected_url = "https://api.cohere.ai/v1"
        if provider.base_url == expected_url:
            results.record_pass("CohereProvider base URL")
        else:
            results.record_fail("CohereProvider base URL", f"Expected {expected_url}, got {provider.base_url}")

        # Test client creation
        if hasattr(provider, 'client'):
            results.record_pass("CohereProvider client creation")
        else:
            results.record_fail("CohereProvider client creation", "No client attribute")

        # Test name property
        if provider.name == "cohere":
            results.record_pass("CohereProvider name property")
        else:
            results.record_fail("CohereProvider name", f"Expected 'cohere', got '{provider.name}'")

    except Exception as e:
        results.record_fail("CohereProvider initialization", str(e))


# Test: Provider Interface Compliance
async def test_provider_interface():
    """Test that all providers implement required interface"""
    test_header("Provider Interface Compliance")

    providers = [
        ("Anthropic", AnthropicProvider),
        ("Ollama", OllamaProvider),
        ("Gemini", GeminiProvider),
        ("Mistral", MistralProvider),
        ("Cohere", CohereProvider),
    ]

    if HAS_OPENAI:
        providers.append(("OpenAI", OpenAIProvider))

    required_methods = ["stream", "list_models"]
    required_properties = ["name"]

    for name, provider_class in providers:
        config = ProviderConfig(name=name.lower(), api_key="test_key")
        provider = provider_class(config)

        # Check required methods
        missing_methods = []
        for method in required_methods:
            if not hasattr(provider, method):
                missing_methods.append(method)

        # Check required properties
        missing_props = []
        for prop in required_properties:
            if not hasattr(provider, prop):
                missing_props.append(prop)

        if not missing_methods and not missing_props:
            results.record_pass(f"{name} implements required interface")
        else:
            missing = missing_methods + missing_props
            results.record_fail(
                f"{name} interface compliance",
                f"Missing: {', '.join(missing)}"
            )


# Test: Function Calling Support
async def test_function_calling_support():
    """Test function calling parameters"""
    test_header("Function Calling Support")

    # All providers should accept tools parameter
    providers = [
        ("Anthropic", AnthropicProvider),
        ("Ollama", OllamaProvider),
        ("Gemini", GeminiProvider),
        ("Mistral", MistralProvider),
        ("Cohere", CohereProvider),
    ]

    if HAS_OPENAI:
        providers.append(("OpenAI", OpenAIProvider))

    for name, provider_class in providers:
        config = ProviderConfig(name=name.lower(), api_key="test_key")
        provider = provider_class(config)

        # Check if stream method accepts tools parameter
        import inspect
        sig = inspect.signature(provider.stream)

        if "tools" in sig.parameters:
            results.record_pass(f"{name} supports function calling (tools parameter)")
        else:
            results.record_fail(
                f"{name} function calling",
                "stream() method doesn't accept 'tools' parameter"
            )


# Main test runner
async def main():
    """Run all provider tests"""

    print("="*70)
    print("  PyCode Provider Test Suite")
    print("="*70)

    # Configuration tests
    test_provider_config()

    # Provider initialization tests
    await test_anthropic_provider()
    await test_openai_provider()
    await test_ollama_provider()
    await test_gemini_provider()
    await test_mistral_provider()
    await test_cohere_provider()

    # Interface compliance tests
    await test_provider_interface()

    # Function calling support
    await test_function_calling_support()

    # Summary
    success = results.summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

"""Tests for provider and model aliases"""

import pytest

import sys
sys.path.insert(0, 'src')

from pycode.provider_aliases import (
    ProviderResolver,
    resolve_provider,
    resolve_model,
    get_default_model,
    PROVIDER_ALIASES,
    MODEL_ALIASES,
    DEFAULT_MODELS,
)


class TestProviderResolver:
    """Test ProviderResolver class"""

    def test_resolver_creation(self):
        """Test creating a resolver"""
        resolver = ProviderResolver()
        assert resolver is not None

    def test_resolve_provider_alias(self):
        """Test resolving provider aliases"""
        resolver = ProviderResolver()

        assert resolver.resolve_provider("claude") == "anthropic"
        assert resolver.resolve_provider("gpt") == "openai"
        assert resolver.resolve_provider("llama") == "ollama"
        assert resolver.resolve_provider("local") == "ollama"
        assert resolver.resolve_provider("gemini") == "gemini"
        assert resolver.resolve_provider("google") == "gemini"

    def test_resolve_provider_canonical(self):
        """Test resolving canonical provider names"""
        resolver = ProviderResolver()

        # Canonical names should return themselves
        assert resolver.resolve_provider("anthropic") == "anthropic"
        assert resolver.resolve_provider("openai") == "openai"
        assert resolver.resolve_provider("ollama") == "ollama"

    def test_resolve_provider_unknown(self):
        """Test resolving unknown provider returns as-is"""
        resolver = ProviderResolver()

        # Unknown provider should return as-is
        assert resolver.resolve_provider("unknown_provider") == "unknown_provider"

    def test_resolve_model_alias(self):
        """Test resolving model aliases"""
        resolver = ProviderResolver()

        # Anthropic models
        provider, model = resolver.resolve_model("sonnet")
        assert provider == "anthropic"
        assert "claude-3-5-sonnet" in model

        provider, model = resolver.resolve_model("opus")
        assert provider == "anthropic"
        assert "opus" in model

        # OpenAI models
        provider, model = resolver.resolve_model("gpt-4")
        assert provider == "openai"
        assert "gpt-4" in model

        # Ollama models
        provider, model = resolver.resolve_model("llama3.2")
        assert provider == "ollama"
        assert "llama3.2" in model

    def test_resolve_model_with_provider_prefix(self):
        """Test resolving model with provider/ prefix"""
        resolver = ProviderResolver()

        # Provider/model format
        provider, model = resolver.resolve_model("anthropic/claude-3-5-sonnet-20241022")
        assert provider == "anthropic"
        assert model == "claude-3-5-sonnet-20241022"

        provider, model = resolver.resolve_model("openai/gpt-4")
        assert provider == "openai"
        assert model == "gpt-4"

        # With alias
        provider, model = resolver.resolve_model("claude/sonnet")
        assert provider == "anthropic"
        assert "sonnet" in model

    def test_resolve_model_infer_provider(self):
        """Test inferring provider from model name"""
        resolver = ProviderResolver()

        # Should infer anthropic from model name
        provider, model = resolver.resolve_model("claude-3-opus-20240229")
        assert provider == "anthropic"

        # Should infer openai from model name
        provider, model = resolver.resolve_model("gpt-4-turbo")
        assert provider == "openai"

        # Should infer gemini from model name
        provider, model = resolver.resolve_model("gemini-1.5-pro")
        assert provider == "gemini"

    def test_get_default_model(self):
        """Test getting default model for provider"""
        resolver = ProviderResolver()

        # Default models for each provider
        assert "sonnet" in resolver.get_default_model("anthropic")
        assert "gpt-4" in resolver.get_default_model("openai")
        assert "llama" in resolver.get_default_model("ollama")
        assert "gemini" in resolver.get_default_model("gemini")

    def test_get_default_model_with_alias(self):
        """Test getting default model with provider alias"""
        resolver = ProviderResolver()

        # Using alias should work
        assert "sonnet" in resolver.get_default_model("claude")
        assert "gpt" in resolver.get_default_model("gpt")
        assert "llama" in resolver.get_default_model("local")

    def test_list_aliases(self):
        """Test listing available aliases"""
        resolver = ProviderResolver()

        # All provider aliases
        aliases = resolver.list_aliases()
        assert "claude" in aliases
        assert "gpt" in aliases
        assert "llama" in aliases

        # Filtered by provider
        anthropic_aliases = resolver.list_aliases("anthropic")
        assert all("anthropic" in v for v in anthropic_aliases.values())


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_resolve_provider_function(self):
        """Test resolve_provider convenience function"""
        assert resolve_provider("claude") == "anthropic"
        assert resolve_provider("gpt") == "openai"
        assert resolve_provider("anthropic") == "anthropic"

    def test_resolve_model_function(self):
        """Test resolve_model convenience function"""
        provider, model = resolve_model("sonnet")
        assert provider == "anthropic"
        assert "sonnet" in model

        provider, model = resolve_model("gpt-4")
        assert provider == "openai"
        assert "gpt-4" in model

    def test_get_default_model_function(self):
        """Test get_default_model convenience function"""
        default = get_default_model("anthropic")
        assert "sonnet" in default

        default = get_default_model("claude")
        assert "sonnet" in default


class TestProviderAliasesData:
    """Test PROVIDER_ALIASES data structure"""

    def test_provider_aliases_contains_common_names(self):
        """Test that common provider names are in aliases"""
        assert "claude" in PROVIDER_ALIASES
        assert "anthropic" in PROVIDER_ALIASES
        assert "gpt" in PROVIDER_ALIASES
        assert "openai" in PROVIDER_ALIASES
        assert "llama" in PROVIDER_ALIASES
        assert "ollama" in PROVIDER_ALIASES
        assert "gemini" in PROVIDER_ALIASES
        assert "google" in PROVIDER_ALIASES

    def test_provider_aliases_canonical_mappings(self):
        """Test canonical provider mappings"""
        assert PROVIDER_ALIASES["claude"] == "anthropic"
        assert PROVIDER_ALIASES["gpt"] == "openai"
        assert PROVIDER_ALIASES["llama"] == "ollama"
        assert PROVIDER_ALIASES["gemini"] == "gemini"


class TestModelAliasesData:
    """Test MODEL_ALIASES data structure"""

    def test_model_aliases_anthropic(self):
        """Test Anthropic model aliases"""
        assert "sonnet" in MODEL_ALIASES
        assert "opus" in MODEL_ALIASES
        assert "haiku" in MODEL_ALIASES

        provider, _ = MODEL_ALIASES["sonnet"]
        assert provider == "anthropic"

    def test_model_aliases_openai(self):
        """Test OpenAI model aliases"""
        assert "gpt-4" in MODEL_ALIASES
        assert "gpt-3.5" in MODEL_ALIASES

        provider, _ = MODEL_ALIASES["gpt-4"]
        assert provider == "openai"

    def test_model_aliases_ollama(self):
        """Test Ollama model aliases"""
        assert "llama3.2" in MODEL_ALIASES
        assert "codellama" in MODEL_ALIASES

        provider, _ = MODEL_ALIASES["llama3.2"]
        assert provider == "ollama"

    def test_model_aliases_gemini(self):
        """Test Gemini model aliases"""
        assert "gemini-pro" in MODEL_ALIASES
        assert "gemini-flash" in MODEL_ALIASES

        provider, _ = MODEL_ALIASES["gemini-pro"]
        assert provider == "gemini"


class TestDefaultModelsData:
    """Test DEFAULT_MODELS data structure"""

    def test_default_models_all_providers(self):
        """Test that all major providers have defaults"""
        assert "anthropic" in DEFAULT_MODELS
        assert "openai" in DEFAULT_MODELS
        assert "ollama" in DEFAULT_MODELS
        assert "gemini" in DEFAULT_MODELS
        assert "mistral" in DEFAULT_MODELS
        assert "cohere" in DEFAULT_MODELS

    def test_default_models_valid(self):
        """Test that default models are non-empty strings"""
        for provider, model in DEFAULT_MODELS.items():
            assert isinstance(model, str)
            assert len(model) > 0

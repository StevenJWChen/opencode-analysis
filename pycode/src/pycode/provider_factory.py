"""
Provider Factory

Creates provider instances from configuration.
Supports all built-in providers: Anthropic, Ollama, Gemini, Mistral, Cohere, OpenAI.
"""

import os
from typing import Literal
from .providers import (
    Provider,
    ProviderConfig,
    AnthropicProvider,
    OllamaProvider,
    GeminiProvider,
    MistralProvider,
    CohereProvider,
)
from .config import ProviderSettings, ModelConfig
from .logging import get_logger

# Try to import OpenAI provider
try:
    from .providers.openai_provider import OpenAIProvider
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


ProviderType = Literal["anthropic", "ollama", "gemini", "mistral", "cohere", "openai"]


class ProviderFactory:
    """Factory for creating provider instances from configuration"""

    @staticmethod
    def create_provider(
        provider_type: str,
        model_config: ModelConfig | None = None,
        provider_settings: ProviderSettings | None = None,
    ) -> Provider:
        """Create a provider instance from configuration

        Args:
            provider_type: Type of provider (e.g., "anthropic", "ollama")
            model_config: Optional model configuration
            provider_settings: Optional provider-specific settings

        Returns:
            Provider instance

        Raises:
            ValueError: If provider type is unsupported
        """
        logger = get_logger()

        # Default settings if none provided
        if provider_settings is None:
            provider_settings = ProviderSettings()

        # Create provider config
        config_kwargs = {
            "name": provider_type,
        }

        # Add base URL if specified
        if provider_settings.base_url:
            config_kwargs["base_url"] = provider_settings.base_url

        # Add API key if specified
        if provider_settings.api_key:
            config_kwargs["api_key"] = provider_settings.api_key

        # Add timeout and other extras
        config_kwargs["extra"] = {
            "timeout": provider_settings.timeout,
        }

        provider_config = ProviderConfig(**config_kwargs)

        # Create provider based on type
        provider_lower = provider_type.lower()

        if provider_lower == "anthropic":
            # Try to get API key from env if not in config
            if not provider_config.api_key:
                provider_config.api_key = os.getenv("ANTHROPIC_API_KEY")
                if not provider_config.api_key:
                    logger.warning(
                        "No Anthropic API key found",
                        hint="Set ANTHROPIC_API_KEY environment variable"
                    )
            return AnthropicProvider(provider_config)

        elif provider_lower == "ollama":
            # Default Ollama to localhost if no base URL
            if not provider_config.base_url:
                provider_config.base_url = "http://localhost:11434"
            return OllamaProvider(provider_config)

        elif provider_lower == "openai":
            if not HAS_OPENAI:
                raise ValueError(
                    "OpenAI provider not available. Install with: pip install openai"
                )
            # Try to get API key from env if not in config
            if not provider_config.api_key:
                provider_config.api_key = os.getenv("OPENAI_API_KEY")
                if not provider_config.api_key:
                    logger.warning(
                        "No OpenAI API key found",
                        hint="Set OPENAI_API_KEY environment variable"
                    )
            return OpenAIProvider(provider_config)

        elif provider_lower == "gemini":
            # Try to get API key from env if not in config
            if not provider_config.api_key:
                provider_config.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                if not provider_config.api_key:
                    logger.warning(
                        "No Gemini API key found",
                        hint="Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable"
                    )
            return GeminiProvider(provider_config)

        elif provider_lower == "mistral":
            # Try to get API key from env if not in config
            if not provider_config.api_key:
                provider_config.api_key = os.getenv("MISTRAL_API_KEY")
                if not provider_config.api_key:
                    logger.warning(
                        "No Mistral API key found",
                        hint="Set MISTRAL_API_KEY environment variable"
                    )
            return MistralProvider(provider_config)

        elif provider_lower == "cohere":
            # Try to get API key from env if not in config
            if not provider_config.api_key:
                provider_config.api_key = os.getenv("COHERE_API_KEY")
                if not provider_config.api_key:
                    logger.warning(
                        "No Cohere API key found",
                        hint="Set COHERE_API_KEY environment variable"
                    )
            return CohereProvider(provider_config)

        else:
            raise ValueError(
                f"Unsupported provider: {provider_type}. "
                f"Supported providers: anthropic, ollama, openai, gemini, mistral, cohere"
            )

    @staticmethod
    def create_from_model_config(model_config: ModelConfig) -> Provider:
        """Create a provider from ModelConfig

        Args:
            model_config: Model configuration

        Returns:
            Provider instance
        """
        return ProviderFactory.create_provider(
            provider_type=model_config.provider,
            model_config=model_config,
        )

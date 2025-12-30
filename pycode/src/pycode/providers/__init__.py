"""Provider integrations for LLM APIs"""

from .base import Provider, ProviderConfig
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider
from .gemini_provider import GeminiProvider
from .mistral_provider import MistralProvider
from .cohere_provider import CohereProvider

# Optional import for OpenAI
try:
    from .openai_provider import OpenAIProvider
    __all__ = [
        "Provider",
        "ProviderConfig",
        "AnthropicProvider",
        "OllamaProvider",
        "GeminiProvider",
        "MistralProvider",
        "CohereProvider",
        "OpenAIProvider",
    ]
except ImportError:
    __all__ = [
        "Provider",
        "ProviderConfig",
        "AnthropicProvider",
        "OllamaProvider",
        "GeminiProvider",
        "MistralProvider",
        "CohereProvider",
    ]

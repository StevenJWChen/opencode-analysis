"""
Provider Aliases

Friendly shortcuts for provider and model names.
Makes it easier to specify providers without remembering exact names.
"""

from typing import Dict, Tuple, Optional
from .logging import get_logger


# Provider name aliases
PROVIDER_ALIASES: Dict[str, str] = {
    # Anthropic
    "claude": "anthropic",
    "anthropic": "anthropic",

    # OpenAI
    "gpt": "openai",
    "openai": "openai",
    "chatgpt": "openai",

    # Ollama
    "ollama": "ollama",
    "local": "ollama",
    "llama": "ollama",

    # Google
    "gemini": "gemini",
    "google": "gemini",
    "bard": "gemini",

    # Mistral
    "mistral": "mistral",

    # Cohere
    "cohere": "cohere",
    "command": "cohere",
}


# Model aliases (provider, model_id)
MODEL_ALIASES: Dict[str, Tuple[str, str]] = {
    # Anthropic
    "claude-3.5-sonnet": ("anthropic", "claude-3-5-sonnet-20241022"),
    "claude-3-sonnet": ("anthropic", "claude-3-sonnet-20240229"),
    "claude-3-opus": ("anthropic", "claude-3-opus-20240229"),
    "claude-3-haiku": ("anthropic", "claude-3-haiku-20240307"),
    "sonnet": ("anthropic", "claude-3-5-sonnet-20241022"),
    "opus": ("anthropic", "claude-3-opus-20240229"),
    "haiku": ("anthropic", "claude-3-haiku-20240307"),

    # OpenAI
    "gpt-4": ("openai", "gpt-4"),
    "gpt-4-turbo": ("openai", "gpt-4-turbo-preview"),
    "gpt-3.5": ("openai", "gpt-3.5-turbo"),
    "gpt4": ("openai", "gpt-4"),

    # Ollama (common models)
    "llama3.2": ("ollama", "llama3.2:latest"),
    "llama3": ("ollama", "llama3:latest"),
    "codellama": ("ollama", "codellama:latest"),
    "mistral": ("ollama", "mistral:latest"),
    "qwen-coder": ("ollama", "qwen2.5-coder:latest"),

    # Gemini
    "gemini-pro": ("gemini", "gemini-1.5-pro"),
    "gemini-flash": ("gemini", "gemini-1.5-flash"),

    # Mistral
    "mistral-large": ("mistral", "mistral-large"),
    "mistral-small": ("mistral", "mistral-small"),

    # Cohere
    "command-r": ("cohere", "command-r-plus"),
}


# Default models for each provider
DEFAULT_MODELS: Dict[str, str] = {
    "anthropic": "claude-3-5-sonnet-20241022",
    "openai": "gpt-4-turbo-preview",
    "ollama": "llama3.2:latest",
    "gemini": "gemini-1.5-pro",
    "mistral": "mistral-large",
    "cohere": "command-r-plus",
}


class ProviderResolver:
    """Resolves provider and model aliases to canonical names"""

    def __init__(self):
        self.logger = get_logger()

    def resolve_provider(self, alias: str) -> str:
        """Resolve a provider alias to canonical name

        Args:
            alias: Provider alias (e.g., "claude", "gpt", "llama")

        Returns:
            Canonical provider name (e.g., "anthropic", "openai", "ollama")

        Examples:
            >>> resolver = ProviderResolver()
            >>> resolver.resolve_provider("claude")
            'anthropic'
            >>> resolver.resolve_provider("gpt")
            'openai'
            >>> resolver.resolve_provider("llama")
            'ollama'
        """
        alias_lower = alias.lower()

        if alias_lower in PROVIDER_ALIASES:
            canonical = PROVIDER_ALIASES[alias_lower]
            if alias_lower != canonical:
                self.logger.debug(
                    f"Resolved provider alias",
                    alias=alias,
                    provider=canonical
                )
            return canonical

        # If not found, return as-is (might be a valid provider name)
        self.logger.debug(f"Using provider name as-is", provider=alias)
        return alias

    def resolve_model(
        self,
        model_spec: str,
        default_provider: Optional[str] = None
    ) -> Tuple[str, str]:
        """Resolve a model specification to (provider, model_id)

        Supports several formats:
        - Model alias: "sonnet" -> ("anthropic", "claude-3-5-sonnet-20241022")
        - Provider/model: "anthropic/claude-3-5-sonnet-20241022"
        - Full model ID: "claude-3-5-sonnet-20241022"

        Args:
            model_spec: Model specification
            default_provider: Default provider if not specified

        Returns:
            Tuple of (provider, model_id)

        Examples:
            >>> resolver = ProviderResolver()
            >>> resolver.resolve_model("sonnet")
            ('anthropic', 'claude-3-5-sonnet-20241022')
            >>> resolver.resolve_model("anthropic/claude-3-5-sonnet")
            ('anthropic', 'claude-3-5-sonnet-20241022')
            >>> resolver.resolve_model("gpt-4")
            ('openai', 'gpt-4')
        """
        # Check if it's a known alias
        if model_spec in MODEL_ALIASES:
            provider, model_id = MODEL_ALIASES[model_spec]
            self.logger.debug(
                "Resolved model alias",
                alias=model_spec,
                provider=provider,
                model=model_id
            )
            return (provider, model_id)

        # Check if it's provider/model format
        if "/" in model_spec:
            parts = model_spec.split("/", 1)
            provider = self.resolve_provider(parts[0])
            model_id = parts[1]

            # Try to resolve model alias
            if model_id in MODEL_ALIASES:
                _, model_id = MODEL_ALIASES[model_id]

            self.logger.debug(
                "Parsed provider/model",
                spec=model_spec,
                provider=provider,
                model=model_id
            )
            return (provider, model_id)

        # Use default provider if specified
        if default_provider:
            provider = self.resolve_provider(default_provider)
            self.logger.debug(
                "Using default provider",
                model=model_spec,
                provider=provider
            )
            return (provider, model_spec)

        # Try to infer provider from model name
        model_lower = model_spec.lower()

        if "claude" in model_lower or "sonnet" in model_lower or "opus" in model_lower:
            return ("anthropic", model_spec)
        elif "gpt" in model_lower:
            return ("openai", model_spec)
        elif "gemini" in model_lower:
            return ("gemini", model_spec)
        elif "mistral" in model_lower:
            return ("mistral", model_spec)
        elif "command" in model_lower:
            return ("cohere", model_spec)
        elif "llama" in model_lower or "codellama" in model_lower:
            return ("ollama", model_spec)

        # Default to first provider if can't determine
        self.logger.warning(
            "Could not determine provider for model",
            model=model_spec
        )
        return ("anthropic", model_spec)

    def get_default_model(self, provider: str) -> str:
        """Get default model for a provider

        Args:
            provider: Provider name (canonical or alias)

        Returns:
            Default model ID for the provider

        Examples:
            >>> resolver = ProviderResolver()
            >>> resolver.get_default_model("anthropic")
            'claude-3-5-sonnet-20241022'
            >>> resolver.get_default_model("claude")
            'claude-3-5-sonnet-20241022'
        """
        canonical_provider = self.resolve_provider(provider)

        if canonical_provider in DEFAULT_MODELS:
            return DEFAULT_MODELS[canonical_provider]

        # Fallback
        self.logger.warning(
            f"No default model for provider",
            provider=canonical_provider
        )
        return "default"

    def list_aliases(self, provider: Optional[str] = None) -> Dict[str, str]:
        """List available aliases

        Args:
            provider: Optional provider to filter by

        Returns:
            Dict of alias -> canonical_name
        """
        if provider:
            canonical = self.resolve_provider(provider)
            # Filter model aliases for this provider
            return {
                alias: f"{p}/{m}"
                for alias, (p, m) in MODEL_ALIASES.items()
                if p == canonical
            }
        else:
            return PROVIDER_ALIASES.copy()


# Global resolver instance
_resolver: Optional[ProviderResolver] = None


def get_resolver() -> ProviderResolver:
    """Get global resolver instance"""
    global _resolver
    if _resolver is None:
        _resolver = ProviderResolver()
    return _resolver


# Convenience functions
def resolve_provider(alias: str) -> str:
    """Resolve provider alias"""
    return get_resolver().resolve_provider(alias)


def resolve_model(model_spec: str, default_provider: Optional[str] = None) -> Tuple[str, str]:
    """Resolve model specification"""
    return get_resolver().resolve_model(model_spec, default_provider)


def get_default_model(provider: str) -> str:
    """Get default model for provider"""
    return get_resolver().get_default_model(provider)

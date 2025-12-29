"""Base provider classes"""

from __future__ import annotations
from typing import Any, AsyncIterator
from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict
from dataclasses import dataclass


class ProviderConfig(BaseModel):
    """Configuration for a provider"""

    model_config = ConfigDict(extra="forbid")

    name: str
    api_key: str | None = None
    base_url: str | None = None
    organization: str | None = None
    extra: dict[str, Any] = {}


@dataclass
class StreamEvent:
    """Event emitted during streaming"""

    type: str  # "start", "text", "tool_call", "finish", etc.
    data: dict[str, Any]


class Provider(ABC):
    """Base class for LLM providers"""

    def __init__(self, config: ProviderConfig):
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass

    @abstractmethod
    async def stream(
        self,
        model: str,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        """Stream responses from the LLM"""
        pass

    @abstractmethod
    async def list_models(self) -> list[str]:
        """List available models"""
        pass

"""OpenAI provider"""

from typing import Any, AsyncIterator
import openai
from .base import Provider, ProviderConfig, StreamEvent


class OpenAIProvider(Provider):
    """OpenAI GPT provider implementation"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(api_key=config.api_key)

    @property
    def name(self) -> str:
        return "openai"

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
        """Stream responses from OpenAI"""

        # Add system message if provided
        openai_messages = []
        if system:
            openai_messages.append({"role": "system", "content": system})

        openai_messages.extend(messages)

        # Prepare request
        request_params: dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "stream": True,
        }

        if temperature is not None:
            request_params["temperature"] = temperature

        if max_tokens:
            request_params["max_tokens"] = max_tokens

        if tools:
            request_params["tools"] = tools

        # Stream response
        stream = await self.client.chat.completions.create(**request_params)

        yield StreamEvent(type="start", data={})

        async for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if delta.content:
                yield StreamEvent(type="text_delta", data={"text": delta.content})

            if delta.tool_calls:
                for tool_call in delta.tool_calls:
                    yield StreamEvent(
                        type="tool_call",
                        data={
                            "tool_call_id": tool_call.id,
                            "tool_name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    )

            if chunk.choices[0].finish_reason:
                yield StreamEvent(
                    type="finish",
                    data={"finish_reason": chunk.choices[0].finish_reason},
                )

    async def list_models(self) -> list[str]:
        """List available OpenAI models"""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]

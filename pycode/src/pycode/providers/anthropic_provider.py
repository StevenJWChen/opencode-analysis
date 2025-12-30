"""Anthropic Claude provider"""

from typing import Any, AsyncIterator
import anthropic
from .base import Provider, ProviderConfig, StreamEvent


class AnthropicProvider(Provider):
    """Anthropic Claude provider implementation"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = anthropic.AsyncAnthropic(api_key=config.api_key)

    @property
    def name(self) -> str:
        return "anthropic"

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
        """Stream responses from Claude"""

        # Convert messages to Anthropic format
        anthropic_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            # Simple conversion (can be enhanced for multi-part content)
            anthropic_messages.append({"role": role, "content": content})

        # Prepare request
        request_params: dict[str, Any] = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or 8192,
            "stream": True,
        }

        if system:
            request_params["system"] = system

        if temperature is not None:
            request_params["temperature"] = temperature

        if tools:
            request_params["tools"] = tools

        # Stream response
        async with self.client.messages.stream(**request_params) as stream:
            yield StreamEvent(type="start", data={})

            async for event in stream:
                if event.type == "content_block_start":
                    continue

                elif event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        yield StreamEvent(
                            type="text_delta",
                            data={"text": event.delta.text},
                        )

                    elif hasattr(event.delta, "type") and event.delta.type == "input_json_delta":
                        # Tool input streaming
                        continue

                elif event.type == "message_stop":
                    yield StreamEvent(type="finish", data={"finish_reason": "stop"})

        final_message = await stream.get_final_message()
        yield StreamEvent(
            type="usage",
            data={
                "prompt_tokens": final_message.usage.input_tokens,
                "completion_tokens": final_message.usage.output_tokens,
                "total_tokens": final_message.usage.input_tokens + final_message.usage.output_tokens,
            },
        )

    async def list_models(self) -> list[str]:
        """List available Claude models"""
        return [
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
        ]

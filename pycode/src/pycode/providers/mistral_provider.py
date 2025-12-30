"""
Mistral Provider

Provides integration with Mistral AI's API.
Supports Mistral Small, Medium, and Large models.
"""

import json
from typing import Any, AsyncIterator
import httpx

from .base import Provider, ProviderConfig, StreamEvent
from ..retry import retry_api_call
from ..logging import get_logger


class MistralProvider(Provider):
    """Provider for Mistral AI models

    Supports:
    - mistral-tiny (fast, economical)
    - mistral-small (balanced)
    - mistral-medium (powerful)
    - mistral-large (most capable)

    Example usage:
        config = ProviderConfig(
            api_key="YOUR_MISTRAL_API_KEY",
            model="mistral-large"
        )
        provider = MistralProvider(config)
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://api.mistral.ai/v1"
        self.timeout = config.extra.get("timeout", 60)
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        self.logger = get_logger()

    @property
    def name(self) -> str:
        return "mistral"

    @retry_api_call
    async def stream(
        self,
        model: str,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamEvent]:
        """
        Stream responses from Mistral

        Args:
            model: Model name (e.g., "mistral-large", "mistral-small")
            messages: List of message dicts
            system: Optional system prompt
            tools: Optional tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            StreamEvent objects
        """

        self.logger.debug(
            "Streaming from Mistral",
            model=model,
            base_url=self.base_url,
            messages=len(messages),
            tools=len(tools) if tools else 0
        )

        # Build messages for Mistral
        mistral_messages = []

        # Add system message if provided
        if system:
            mistral_messages.append({
                "role": "system",
                "content": system
            })

        # Add conversation messages
        for msg in messages:
            mistral_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        # Build request
        request_data = {
            "model": model,
            "messages": mistral_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        # Add tools if provided
        if tools:
            mistral_tools = []
            for tool in tools:
                if "function" in tool:
                    mistral_tools.append({
                        "type": "function",
                        "function": tool["function"]
                    })

            if mistral_tools:
                request_data["tools"] = mistral_tools
                request_data["tool_choice"] = "auto"

        # Stream from Mistral
        url = f"{self.base_url}/chat/completions"

        try:
            async with self.client.stream("POST", url, json=request_data) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    # Remove "data: " prefix
                    json_str = line[6:]

                    if json_str == "[DONE]":
                        break

                    try:
                        chunk = json.loads(json_str)

                        # Extract delta
                        choices = chunk.get("choices", [])
                        if not choices:
                            continue

                        delta = choices[0].get("delta", {})

                        # Text content
                        if "content" in delta and delta["content"]:
                            yield StreamEvent(
                                type="text_delta",
                                data={"text": delta["content"]}
                            )

                        # Tool calls
                        if "tool_calls" in delta:
                            for tool_call in delta["tool_calls"]:
                                function = tool_call.get("function", {})
                                if function.get("name"):
                                    # Parse arguments if present
                                    args = {}
                                    if function.get("arguments"):
                                        try:
                                            args = json.loads(function["arguments"])
                                        except:
                                            args = {}

                                    yield StreamEvent(
                                        type="tool_use",
                                        data={
                                            "id": tool_call.get("id", "call_mistral"),
                                            "name": function.get("name"),
                                            "arguments": args
                                        }
                                    )

                    except json.JSONDecodeError:
                        continue

        except httpx.HTTPStatusError as e:
            error_msg = f"Mistral API error: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail.get('message', '')}"
            except:
                pass
            raise Exception(error_msg)

        except Exception as e:
            raise Exception(f"Mistral streaming error: {str(e)}")

    async def complete(
        self,
        model: str,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """
        Non-streaming completion from Mistral

        Returns:
            Response dict with content and tool_calls
        """

        response_text = ""
        tool_calls = []

        async for event in self.stream(
            model=model,
            messages=messages,
            system=system,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            if event.type == "text_delta":
                response_text += event.data.get("text", "")
            elif event.type == "tool_use":
                tool_calls.append(event.data)

        return {
            "content": response_text,
            "tool_calls": tool_calls if tool_calls else None,
        }

    async def list_models(self) -> list[str]:
        """List available Mistral models"""
        return [
            "mistral-tiny",
            "mistral-small",
            "mistral-medium",
            "mistral-large",
        ]

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    def __del__(self):
        """Cleanup"""
        try:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.client.aclose())
                else:
                    loop.run_until_complete(self.client.aclose())
            except:
                pass
        except:
            pass

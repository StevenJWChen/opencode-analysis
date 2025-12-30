"""
Cohere Provider

Provides integration with Cohere's API.
Supports Command and Command-R models.
"""

import json
from typing import Any, AsyncIterator
import httpx

from .base import Provider, ProviderConfig, StreamEvent


class CohereProvider(Provider):
    """Provider for Cohere models

    Supports:
    - command (general purpose)
    - command-light (faster, economical)
    - command-r (RAG optimized)
    - command-r-plus (most capable)

    Example usage:
        config = ProviderConfig(
            api_key="YOUR_COHERE_API_KEY",
            model="command-r-plus"
        )
        provider = CohereProvider(config)
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://api.cohere.ai/v1"
        self.timeout = config.timeout or 60
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

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
        Stream responses from Cohere

        Args:
            model: Model name (e.g., "command-r-plus", "command")
            messages: List of message dicts
            system: Optional system prompt (preamble)
            tools: Optional tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            StreamEvent objects
        """

        # Build chat history for Cohere
        chat_history = []
        current_message = ""

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                # Last user message becomes the message parameter
                current_message = content
            else:
                # Previous messages go into chat_history
                if role == "assistant":
                    chat_history.append({
                        "role": "CHATBOT",
                        "message": content
                    })

        # Build request
        request_data = {
            "model": model,
            "message": current_message,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        # Add preamble (system prompt) if provided
        if system:
            request_data["preamble"] = system

        # Add chat history if exists
        if chat_history:
            request_data["chat_history"] = chat_history

        # Add tools if provided
        if tools:
            cohere_tools = []
            for tool in tools:
                if "function" in tool:
                    func = tool["function"]
                    # Convert to Cohere tool format
                    cohere_tools.append({
                        "name": func.get("name"),
                        "description": func.get("description"),
                        "parameter_definitions": func.get("parameters", {}).get("properties", {})
                    })

            if cohere_tools:
                request_data["tools"] = cohere_tools

        # Stream from Cohere
        url = f"{self.base_url}/chat"

        try:
            async with self.client.stream("POST", url, json=request_data) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        event = json.loads(line)

                        event_type = event.get("event_type")

                        # Text generation
                        if event_type == "text-generation":
                            text = event.get("text", "")
                            if text:
                                yield StreamEvent(
                                    type="text_delta",
                                    data={"text": text}
                                )

                        # Tool calls
                        elif event_type == "tool-calls-generation":
                            tool_calls = event.get("tool_calls", [])
                            for tool_call in tool_calls:
                                yield StreamEvent(
                                    type="tool_use",
                                    data={
                                        "id": f"call_{tool_call.get('name')}",
                                        "name": tool_call.get("name"),
                                        "arguments": tool_call.get("parameters", {})
                                    }
                                )

                        # Stream end
                        elif event_type == "stream-end":
                            break

                    except json.JSONDecodeError:
                        continue

        except httpx.HTTPStatusError as e:
            error_msg = f"Cohere API error: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail.get('message', '')}"
            except:
                pass
            raise Exception(error_msg)

        except Exception as e:
            raise Exception(f"Cohere streaming error: {str(e)}")

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
        Non-streaming completion from Cohere

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

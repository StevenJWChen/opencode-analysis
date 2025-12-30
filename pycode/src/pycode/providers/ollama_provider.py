"""
Ollama Provider

Provides integration with Ollama for local LLM inference.
Supports streaming and function calling.
"""

import json
from typing import Any, AsyncIterator
import httpx

from .base import Provider, ProviderConfig, StreamEvent


class OllamaProvider(Provider):
    """Provider for Ollama local models

    Ollama must be running locally (default: http://localhost:11434)

    Example usage:
        config = ProviderConfig(
            base_url="http://localhost:11434",
            model="llama3.2:latest"
        )
        provider = OllamaProvider(config)
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
        self.timeout = config.extra.get("timeout", 120)
        self.client = httpx.AsyncClient(timeout=self.timeout)

    @property
    def name(self) -> str:
        return "ollama"

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
        Stream responses from Ollama

        Args:
            model: Model name (e.g., "llama3.2:latest", "mistral:latest")
            messages: List of message dicts with role and content
            system: Optional system prompt
            tools: Optional list of tool definitions
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Yields:
            StreamEvent objects with type and data
        """

        # Build messages for Ollama
        ollama_messages = []

        # Add system message if provided
        if system:
            ollama_messages.append({
                "role": "system",
                "content": system
            })

        # Add conversation messages
        for msg in messages:
            ollama_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })

        # Build request payload
        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        # Add tools if provided (Ollama function calling)
        if tools:
            # Convert tools to Ollama format
            ollama_tools = []
            for tool in tools:
                if "function" in tool:
                    func = tool["function"]
                    ollama_tools.append({
                        "type": "function",
                        "function": {
                            "name": func.get("name"),
                            "description": func.get("description"),
                            "parameters": func.get("parameters", {})
                        }
                    })

            if ollama_tools:
                payload["tools"] = ollama_tools

        # Stream from Ollama
        url = f"{self.base_url}/api/chat"

        try:
            async with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()

                accumulated_text = ""
                tool_calls = []

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        chunk = json.loads(line)

                        # Handle message chunk
                        if "message" in chunk:
                            message = chunk["message"]

                            # Text content
                            if "content" in message and message["content"]:
                                text = message["content"]
                                accumulated_text += text
                                yield StreamEvent(
                                    type="text_delta",
                                    data={"text": text}
                                )

                            # Tool calls
                            if "tool_calls" in message:
                                for tool_call in message["tool_calls"]:
                                    function = tool_call.get("function", {})
                                    tool_calls.append({
                                        "id": tool_call.get("id", "call_ollama"),
                                        "name": function.get("name"),
                                        "arguments": function.get("arguments", {})
                                    })

                        # Check if done
                        if chunk.get("done", False):
                            # Yield any accumulated tool calls
                            for tool_call in tool_calls:
                                yield StreamEvent(
                                    type="tool_use",
                                    data=tool_call
                                )
                            break

                    except json.JSONDecodeError:
                        continue

        except httpx.HTTPStatusError as e:
            error_msg = f"Ollama API error: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail.get('error', '')}"
            except:
                pass
            raise Exception(error_msg)

        except httpx.ConnectError:
            raise Exception(
                "Cannot connect to Ollama. Make sure Ollama is running:\n"
                "  Start Ollama: ollama serve\n"
                "  Install models: ollama pull llama3.2"
            )

        except Exception as e:
            raise Exception(f"Ollama streaming error: {str(e)}")

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
        Non-streaming completion from Ollama

        Args:
            model: Model name
            messages: List of message dicts
            system: Optional system prompt
            tools: Optional tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Response dict with content and optionally tool_calls
        """

        # Collect all streaming events
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
        """
        List available Ollama models

        Returns:
            List of model names
        """
        url = f"{self.base_url}/api/tags"

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            models = []
            for model in data.get("models", []):
                models.append(model.get("name", ""))

            return models

        except httpx.ConnectError:
            raise Exception("Cannot connect to Ollama. Make sure it's running.")
        except Exception as e:
            raise Exception(f"Failed to list models: {str(e)}")

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    def __del__(self):
        """Cleanup on deletion"""
        try:
            # Try to close client if event loop is available
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

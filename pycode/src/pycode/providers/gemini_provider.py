"""
Gemini Provider

Provides integration with Google's Gemini API.
Supports Gemini 1.5 Pro, Gemini 1.5 Flash, and other models.
"""

import json
from typing import Any, AsyncIterator
import httpx

from .base import Provider, ProviderConfig, StreamEvent


class GeminiProvider(Provider):
    """Provider for Google Gemini models

    Supports:
    - gemini-1.5-pro
    - gemini-1.5-flash
    - gemini-1.0-pro

    Example usage:
        config = ProviderConfig(
            api_key="YOUR_GEMINI_API_KEY",
            model="gemini-1.5-pro"
        )
        provider = GeminiProvider(config)
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.base_url = config.base_url or "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = config.timeout or 60
        self.client = httpx.AsyncClient(timeout=self.timeout)

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
        Stream responses from Gemini

        Args:
            model: Model name (e.g., "gemini-1.5-pro", "gemini-1.5-flash")
            messages: List of message dicts
            system: Optional system instruction
            tools: Optional tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            StreamEvent objects
        """

        # Build contents for Gemini
        contents = []

        # Add messages
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Gemini uses "user" and "model" roles
            gemini_role = "model" if role == "assistant" else "user"

            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })

        # Build request
        request_data = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        # Add system instruction if provided
        if system:
            request_data["systemInstruction"] = {
                "parts": [{"text": system}]
            }

        # Add tools if provided
        if tools:
            gemini_tools = []
            for tool in tools:
                if "function" in tool:
                    func = tool["function"]
                    gemini_tools.append({
                        "functionDeclarations": [{
                            "name": func.get("name"),
                            "description": func.get("description"),
                            "parameters": func.get("parameters", {})
                        }]
                    })

            if gemini_tools:
                request_data["tools"] = gemini_tools

        # Stream from Gemini
        url = f"{self.base_url}/models/{model}:streamGenerateContent"
        params = {"key": self.api_key, "alt": "sse"}

        try:
            async with self.client.stream(
                "POST",
                url,
                params=params,
                json=request_data,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    # Remove "data: " prefix
                    json_str = line[6:]

                    try:
                        chunk = json.loads(json_str)

                        # Extract candidates
                        candidates = chunk.get("candidates", [])
                        if not candidates:
                            continue

                        candidate = candidates[0]
                        content = candidate.get("content", {})
                        parts = content.get("parts", [])

                        for part in parts:
                            # Text content
                            if "text" in part:
                                yield StreamEvent(
                                    type="text_delta",
                                    data={"text": part["text"]}
                                )

                            # Function call
                            if "functionCall" in part:
                                func_call = part["functionCall"]
                                yield StreamEvent(
                                    type="tool_use",
                                    data={
                                        "id": f"call_{func_call.get('name')}",
                                        "name": func_call.get("name"),
                                        "arguments": func_call.get("args", {})
                                    }
                                )

                    except json.JSONDecodeError:
                        continue

        except httpx.HTTPStatusError as e:
            error_msg = f"Gemini API error: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail.get('error', {}).get('message', '')}"
            except:
                pass
            raise Exception(error_msg)

        except Exception as e:
            raise Exception(f"Gemini streaming error: {str(e)}")

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
        Non-streaming completion from Gemini

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

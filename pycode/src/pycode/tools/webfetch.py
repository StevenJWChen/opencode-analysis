"""Web fetching tool for HTTP requests"""

import httpx
from .base import Tool, ToolContext, ToolResult


class WebFetchTool(Tool):
    """Fetch content from web URLs"""

    # Maximum response size (10 MB)
    MAX_RESPONSE_SIZE = 10 * 1024 * 1024

    # Request timeout in seconds
    REQUEST_TIMEOUT = 30

    @property
    def name(self) -> str:
        return "webfetch"

    @property
    def description(self) -> str:
        return """Fetch content from web URLs via HTTP/HTTPS.

Use this tool to:
- Fetch API responses
- Download web page content
- Read documentation from URLs
- Access public data sources
- Test HTTP endpoints

Supports:
- GET and POST requests
- Custom headers
- Query parameters
- JSON responses
- HTML content
- Automatic redirects

IMPORTANT:
- Only use for public, accessible URLs
- Respects 30-second timeout
- Response limited to 10 MB
- Use for legitimate purposes only
- Be mindful of rate limits
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to fetch (must start with http:// or https://)",
                },
                "method": {
                    "type": "string",
                    "description": "HTTP method (GET or POST, default: GET)",
                    "enum": ["GET", "POST"],
                },
                "headers": {
                    "type": "object",
                    "description": "Custom headers to send (optional)",
                },
                "body": {
                    "type": "string",
                    "description": "Request body for POST requests (optional)",
                },
                "follow_redirects": {
                    "type": "boolean",
                    "description": "Follow HTTP redirects (default: true)",
                },
            },
            "required": ["url"],
        }

    def _format_headers(self, headers: dict) -> str:
        """Format headers for display"""
        lines = []
        for key, value in headers.items():
            # Truncate long header values
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."
            lines.append(f"  {key}: {value_str}")
        return "\n".join(lines)

    def _truncate_content(self, content: str, max_length: int = 5000) -> tuple[str, bool]:
        """Truncate content if too long"""
        if len(content) <= max_length:
            return content, False
        return content[:max_length], True

    async def execute(self, parameters: dict, context: ToolContext) -> ToolResult:
        url = parameters["url"]
        method = parameters.get("method", "GET").upper()
        headers = parameters.get("headers", {})
        body = parameters.get("body")
        follow_redirects = parameters.get("follow_redirects", True)

        # Validate URL
        if not url.startswith(("http://", "https://")):
            return ToolResult(
                title="WebFetch",
                output="",
                error="URL must start with http:// or https://",
            )

        # Validate method
        if method not in ["GET", "POST"]:
            return ToolResult(
                title="WebFetch",
                output="",
                error=f"Unsupported HTTP method: {method}",
            )

        try:
            # Create client with timeout and size limits
            async with httpx.AsyncClient(
                timeout=self.REQUEST_TIMEOUT,
                follow_redirects=follow_redirects,
                limits=httpx.Limits(max_connections=1, max_keepalive_connections=0),
            ) as client:
                # Prepare request
                request_kwargs = {
                    "method": method,
                    "url": url,
                    "headers": headers,
                }

                if method == "POST" and body:
                    request_kwargs["content"] = body

                # Make request
                response = await client.request(**request_kwargs)

                # Check response size
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self.MAX_RESPONSE_SIZE:
                    return ToolResult(
                        title=f"WebFetch: {url}",
                        output="",
                        error=f"Response too large: {content_length} bytes (max: {self.MAX_RESPONSE_SIZE})",
                    )

                # Get response content
                try:
                    # Try to decode as text
                    content = response.text

                    # Check if content is too large
                    if len(content.encode("utf-8")) > self.MAX_RESPONSE_SIZE:
                        return ToolResult(
                            title=f"WebFetch: {url}",
                            output="",
                            error=f"Response too large (max: {self.MAX_RESPONSE_SIZE} bytes)",
                        )

                except Exception:
                    # Binary content
                    content = f"<binary content, {len(response.content)} bytes>"

                # Truncate if needed
                content_display, was_truncated = self._truncate_content(content)

                # Format output
                output_lines = []
                output_lines.append(f"URL: {url}")
                output_lines.append(f"Method: {method}")
                output_lines.append(f"Status: {response.status_code} {response.reason_phrase}")
                output_lines.append(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
                output_lines.append(f"Content-Length: {len(content)} characters")
                output_lines.append("")

                # Show response headers
                output_lines.append("Response Headers:")
                output_lines.append(self._format_headers(dict(response.headers)))
                output_lines.append("")

                # Show content
                output_lines.append("Content:")
                output_lines.append("-" * 60)
                output_lines.append(content_display)

                if was_truncated:
                    output_lines.append("-" * 60)
                    output_lines.append(f"(truncated, showing first 5000 characters of {len(content)})")

                output = "\n".join(output_lines)

                # Determine if request was successful
                is_success = 200 <= response.status_code < 300

                return ToolResult(
                    title=f"WebFetch: {response.status_code}",
                    output=output,
                    error=None if is_success else f"HTTP {response.status_code}: {response.reason_phrase}",
                    metadata={
                        "url": url,
                        "method": method,
                        "status_code": response.status_code,
                        "content_type": response.headers.get("content-type"),
                        "content_length": len(content),
                        "truncated": was_truncated,
                    },
                )

        except httpx.TimeoutException:
            return ToolResult(
                title=f"WebFetch: {url}",
                output="",
                error=f"Request timed out after {self.REQUEST_TIMEOUT} seconds",
            )
        except httpx.ConnectError as e:
            return ToolResult(
                title=f"WebFetch: {url}",
                output="",
                error=f"Connection failed: {str(e)}",
            )
        except httpx.HTTPError as e:
            return ToolResult(
                title=f"WebFetch: {url}",
                output="",
                error=f"HTTP error: {str(e)}",
            )
        except Exception as e:
            return ToolResult(
                title=f"WebFetch: {url}",
                output="",
                error=f"Failed to fetch URL: {str(e)}",
            )

"""Message and Part data structures"""

from __future__ import annotations
from typing import Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from .identifier import Identifier


class MessagePart(BaseModel):
    """Base class for message parts"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: Identifier.ascending("part"))
    session_id: str
    message_id: str
    type: str


class TextPart(MessagePart):
    """Text content part"""

    type: Literal["text"] = "text"
    text: str
    synthetic: bool = False  # Auto-generated vs user-provided
    ignored: bool = False  # Excluded from context
    metadata: dict[str, Any] = Field(default_factory=dict)


class FilePart(MessagePart):
    """File attachment part"""

    type: Literal["file"] = "file"
    mime: str
    filename: str | None = None
    url: str  # data: URL or file path
    source: dict[str, Any] | None = None  # Where file came from


class AgentPart(MessagePart):
    """Agent invocation part"""

    type: Literal["agent"] = "agent"
    name: str  # Agent to invoke
    source: dict[str, Any] | None = None


class ToolPart(MessagePart):
    """Tool execution part"""

    type: Literal["tool"] = "tool"
    tool: str  # Tool name
    call_id: str
    state: ToolState


class ToolState(BaseModel):
    """State of tool execution"""

    status: Literal["pending", "running", "success", "error", "rejected"]
    input: dict[str, Any] = Field(default_factory=dict)
    output: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    time_start: int | None = None
    time_end: int | None = None


class ReasoningPart(MessagePart):
    """Extended thinking part (e.g., Claude reasoning)"""

    type: Literal["reasoning"] = "reasoning"
    text: str
    time_start: int
    time_end: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """
    Message in a conversation.
    Can be user or assistant role.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: Identifier.ascending("message"))
    session_id: str
    role: Literal["user", "assistant"]
    parts: list[MessagePart] = Field(default_factory=list)

    # Assistant-specific fields
    agent: str | None = None  # Which agent generated this
    model_id: str | None = None
    provider_id: str | None = None
    usage: dict[str, int] | None = None  # Token counts
    error: dict[str, Any] | None = None

    # User-specific fields
    system: str | None = None  # Custom system prompt override

    # Timestamps
    time_created: int = Field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    time_updated: int = Field(default_factory=lambda: int(datetime.now().timestamp() * 1000))

    def add_part(self, part: MessagePart) -> None:
        """Add a part to this message"""
        self.parts.append(part)
        self.time_updated = int(datetime.now().timestamp() * 1000)

    def get_text_parts(self) -> list[TextPart]:
        """Get all text parts"""
        return [p for p in self.parts if isinstance(p, TextPart)]

    def get_tool_parts(self) -> list[ToolPart]:
        """Get all tool parts"""
        return [p for p in self.parts if isinstance(p, ToolPart)]

    def get_text_content(self) -> str:
        """Get combined text from all text parts"""
        return "\n".join(p.text for p in self.get_text_parts() if not p.ignored)

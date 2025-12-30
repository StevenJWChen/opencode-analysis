"""Session management"""

from __future__ import annotations
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from .identifier import Identifier
from .message import Message


class Session(BaseModel):
    """
    A conversation session with persistent state.
    Contains messages, configuration, and metadata.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: Identifier.descending("session"))
    project_id: str
    directory: str  # Working directory
    parent_id: str | None = None  # For forked sessions
    title: str = "New session"

    # Metadata
    version: str = "0.1.0"
    time_created: int = Field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    time_updated: int = Field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    time_archived: int | None = None

    # Summary statistics
    summary: SessionSummary | None = None

    # Sharing
    share: SessionShare | None = None

    # Revert state
    revert: SessionRevert | None = None

    def touch(self) -> None:
        """Update the last-activity timestamp"""
        self.time_updated = int(datetime.now().timestamp() * 1000)

    def archive(self) -> None:
        """Mark session as archived (soft delete)"""
        self.time_archived = int(datetime.now().timestamp() * 1000)

    def is_archived(self) -> bool:
        """Check if session is archived"""
        return self.time_archived is not None


class SessionSummary(BaseModel):
    """Summary of code changes in session"""

    additions: int = 0
    deletions: int = 0
    files: int = 0
    diffs: list[dict[str, Any]] = Field(default_factory=list)


class SessionShare(BaseModel):
    """Session sharing configuration"""

    url: str
    secret: str | None = None


class SessionRevert(BaseModel):
    """Revert/undo state"""

    message_id: str
    part_id: str | None = None
    snapshot: str | None = None
    diff: str | None = None

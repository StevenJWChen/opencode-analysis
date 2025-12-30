"""
Session Manager

Handles listing, creating, resuming, and deleting sessions.
Essential for managing multiple projects.
"""

from pathlib import Path
from typing import Any
from datetime import datetime
from .core import Session
from .storage import Storage
from .history import MessageHistory


class SessionManager:
    """Manages coding sessions"""

    def __init__(self, storage: Storage | None = None):
        self.storage = storage or Storage()
        self.history = MessageHistory(self.storage)

    async def create_session(
        self, project_id: str, directory: str, title: str | None = None
    ) -> Session:
        """Create a new session"""
        session = Session(
            project_id=project_id,
            directory=directory,
            title=title or "New Session",
        )

        # Save session
        await self.save_session(session)

        return session

    async def save_session(self, session: Session) -> None:
        """Save session to storage"""
        session_key = ["sessions", session.project_id, session.id]
        await self.storage.write(session_key, session.model_dump())

    async def load_session(self, session_id: str, project_id: str | None = None) -> Session | None:
        """Load session from storage"""
        # Try to find session
        if project_id:
            session_key = ["sessions", project_id, session_id]
            try:
                session_data = await self.storage.read(session_key)
                return Session.model_validate(session_data)
            except Exception:
                return None

        # Search all projects
        sessions_dir = self.storage.base_path / "sessions"
        if not sessions_dir.exists():
            return None

        for project_dir in sessions_dir.iterdir():
            if not project_dir.is_dir():
                continue

            session_file = project_dir / f"{session_id}.json"
            if session_file.exists():
                import json

                with open(session_file, "r") as f:
                    session_data = json.load(f)
                    return Session.model_validate(session_data)

        return None

    async def list_sessions(
        self, project_id: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        List sessions with metadata

        Returns list of dicts with session info + message count
        """
        sessions_dir = self.storage.base_path / "sessions"
        if not sessions_dir.exists():
            return []

        sessions_info = []

        # Get projects to search
        if project_id:
            project_dirs = [sessions_dir / project_id]
        else:
            project_dirs = [d for d in sessions_dir.iterdir() if d.is_dir()]

        for project_dir in project_dirs:
            if not project_dir.exists():
                continue

            # Load all session files
            for session_file in project_dir.glob("*.json"):
                try:
                    import json

                    with open(session_file, "r") as f:
                        session_data = json.load(f)
                        session = Session.model_validate(session_data)

                    # Get message count
                    msg_count = await self.history.get_message_count(session.id)

                    # Get last message time
                    last_msg = await self.history.get_last_message(session.id)
                    last_activity = (
                        datetime.fromtimestamp(last_msg.time_created / 1000).isoformat()
                        if last_msg
                        else datetime.fromtimestamp(session.time_created / 1000).isoformat()
                    )

                    sessions_info.append(
                        {
                            "session_id": session.id,
                            "project_id": session.project_id,
                            "title": session.title,
                            "directory": session.directory,
                            "created": datetime.fromtimestamp(session.time_created / 1000).isoformat(),
                            "updated": datetime.fromtimestamp(session.time_updated / 1000).isoformat(),
                            "last_activity": last_activity,
                            "message_count": msg_count,
                        }
                    )
                except Exception:
                    # Skip corrupted sessions
                    continue

        # Sort by last activity (most recent first)
        sessions_info.sort(key=lambda x: x["last_activity"], reverse=True)

        # Apply limit
        return sessions_info[:limit]

    async def delete_session(self, session_id: str, project_id: str) -> bool:
        """Delete a session and its history"""
        # Delete session file
        session_file = self.storage.base_path / "sessions" / project_id / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()

        # Delete message history
        await self.history.clear_history(session_id)

        return True

    async def get_recent_session(self, project_id: str | None = None) -> Session | None:
        """Get the most recently active session"""
        sessions = await self.list_sessions(project_id, limit=1)
        if not sessions:
            return None

        return await self.load_session(sessions[0]["session_id"], sessions[0]["project_id"])

    async def update_session_title(self, session_id: str, project_id: str, title: str) -> bool:
        """Update session title"""
        session = await self.load_session(session_id, project_id)
        if not session:
            return False

        session.title = title
        session.touch()
        await self.save_session(session)
        return True

    async def get_session_stats(self, session_id: str, project_id: str) -> dict[str, Any]:
        """Get session statistics"""
        session = await self.load_session(session_id, project_id)
        if not session:
            return {}

        msg_count = await self.history.get_message_count(session_id)
        last_msg = await self.history.get_last_message(session_id)

        return {
            "session_id": session.id,
            "title": session.title,
            "project_id": session.project_id,
            "created": datetime.fromtimestamp(session.time_created / 1000).isoformat(),
            "updated": datetime.fromtimestamp(session.time_updated / 1000).isoformat(),
            "message_count": msg_count,
            "last_message_time": (
                datetime.fromtimestamp(last_msg.time_created / 1000).isoformat() if last_msg else None
            ),
        }

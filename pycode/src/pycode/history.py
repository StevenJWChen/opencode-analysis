"""
Message History Management

Handles loading, saving, and managing conversation history.
Critical for resuming sessions and maintaining context.
"""

import json
from pathlib import Path
from typing import Any
from .core import Message, Session
from .storage import Storage


class MessageHistory:
    """Manages message history for sessions"""

    def __init__(self, storage: Storage | None = None):
        self.storage = storage or Storage()

    async def save_message(self, session_id: str, message: Message) -> None:
        """Save a message to history"""
        # Create messages directory for session
        messages_key = ["sessions", session_id.replace("session_", ""), "messages", message.id]

        # Save message
        await self.storage.write(messages_key, message.model_dump())

    async def load_messages(self, session_id: str, limit: int | None = None) -> list[Message]:
        """Load messages for a session"""
        session_dir = self.storage.base_path / "sessions" / session_id.replace("session_", "") / "messages"

        if not session_dir.exists():
            return []

        # Get all message files
        message_files = sorted(session_dir.glob("*.json"))

        # Apply limit
        if limit:
            message_files = message_files[-limit:]

        # Load messages
        messages = []
        for msg_file in message_files:
            try:
                with open(msg_file, "r") as f:
                    msg_data = json.load(f)
                    messages.append(Message.model_validate(msg_data))
            except Exception:
                # Skip corrupted messages
                continue

        return messages

    async def get_conversation_for_llm(
        self, session_id: str, max_messages: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get conversation history formatted for LLM

        Returns list of {role: "user"|"assistant", content: str} dicts
        """
        messages = await self.load_messages(session_id, limit=max_messages)

        conversation = []
        for msg in messages:
            # Convert message to LLM format
            if msg.role == "user":
                # User message - combine all text parts
                text_parts = [p.text for p in msg.parts if hasattr(p, "text")]
                if text_parts:
                    conversation.append({"role": "user", "content": " ".join(text_parts)})

            elif msg.role == "assistant":
                # Assistant message - handle text and tool calls
                content_blocks = []

                for part in msg.parts:
                    if hasattr(part, "text"):
                        # Text part
                        content_blocks.append({"type": "text", "text": part.text})

                    elif hasattr(part, "tool"):
                        # Tool part
                        content_blocks.append(
                            {
                                "type": "tool_use",
                                "id": part.call_id,
                                "name": part.tool,
                                "input": part.state.input,
                            }
                        )

                if content_blocks:
                    conversation.append({"role": "assistant", "content": content_blocks})

                # Add tool results as user message
                tool_results = []
                for part in msg.parts:
                    if hasattr(part, "tool"):
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": part.call_id,
                                "content": part.state.output or part.state.error or "",
                                "is_error": part.state.status == "error",
                            }
                        )

                if tool_results:
                    conversation.append({"role": "user", "content": tool_results})

        return conversation

    async def get_message_count(self, session_id: str) -> int:
        """Get total message count for session"""
        messages = await self.load_messages(session_id)
        return len(messages)

    async def clear_history(self, session_id: str) -> None:
        """Clear all messages for a session"""
        session_dir = self.storage.base_path / "sessions" / session_id.replace("session_", "") / "messages"

        if session_dir.exists():
            import shutil

            shutil.rmtree(session_dir)

    async def get_last_message(self, session_id: str) -> Message | None:
        """Get the most recent message"""
        messages = await self.load_messages(session_id, limit=1)
        return messages[0] if messages else None


class ContextManager:
    """Manages context and token limits"""

    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens

    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimate
        ~4 characters per token for English
        """
        return len(text) // 4

    def prune_conversation(
        self, conversation: list[dict[str, Any]], target_tokens: int
    ) -> list[dict[str, Any]]:
        """
        Prune conversation to fit within token limit

        Strategy:
        1. Always keep first message (initial context)
        2. Always keep last 5 messages (recent context)
        3. Remove middle messages if needed
        """
        if not conversation:
            return []

        # Estimate current token count
        conv_text = json.dumps(conversation)
        current_tokens = self.estimate_tokens(conv_text)

        if current_tokens <= target_tokens:
            return conversation

        # Keep first and last messages
        if len(conversation) <= 6:
            # Too short to prune
            return conversation

        # Keep first message and last 5
        pruned = [conversation[0]] + conversation[-5:]

        # Add summary message
        removed_count = len(conversation) - len(pruned)
        summary = {
            "role": "user",
            "content": f"[{removed_count} messages removed to save context]",
        }

        return [conversation[0], summary] + conversation[-5:]

    async def compress_history(
        self, history: MessageHistory, session_id: str, max_tokens: int | None = None
    ) -> list[dict[str, Any]]:
        """Get compressed conversation history"""
        max_tokens = max_tokens or self.max_tokens

        # Load conversation
        conversation = await history.get_conversation_for_llm(session_id)

        # Prune if needed
        return self.prune_conversation(conversation, max_tokens)

"""Identifier generation system using ULIDs"""

import time
from typing import Literal
from ulid import ULID


class Identifier:
    """
    Generate sortable unique identifiers.

    - Ascending: Sortable, incremental (for parts, messages within session)
    - Descending: Reverse chronological (for sessions)
    """

    @staticmethod
    def ascending(prefix: Literal["message", "part", "tool"] = "message") -> str:
        """Generate ascending (forward-chronological) ID"""
        ulid = ULID()
        return f"{prefix}_{ulid}"

    @staticmethod
    def descending(prefix: Literal["session"] = "session", custom_id: str | None = None) -> str:
        """Generate descending (reverse-chronological) ID"""
        if custom_id:
            return f"{prefix}_{custom_id}"

        # Invert timestamp for reverse chronological sorting
        timestamp_ms = int(time.time() * 1000)
        inverted_timestamp = 0xFFFFFFFFFFFF - (timestamp_ms & 0xFFFFFFFFFFFF)

        # Create ULID with inverted timestamp
        ulid = ULID.from_timestamp(inverted_timestamp / 1000)
        return f"{prefix}_{ulid}"

    @staticmethod
    def extract_timestamp(identifier: str) -> int:
        """Extract timestamp from identifier"""
        parts = identifier.split("_", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid identifier format: {identifier}")

        ulid_str = parts[1]
        ulid = ULID.from_str(ulid_str)
        return int(ulid.timestamp().timestamp() * 1000)

    @staticmethod
    def compare(id1: str, id2: str) -> int:
        """
        Compare two identifiers.
        Returns: -1 if id1 < id2, 0 if equal, 1 if id1 > id2
        """
        if id1 == id2:
            return 0
        return -1 if id1 < id2 else 1

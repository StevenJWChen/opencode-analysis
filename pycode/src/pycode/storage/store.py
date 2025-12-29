"""File-based JSON storage"""

import json
import aiofiles
from pathlib import Path
from typing import Any


class Storage:
    """
    File-based hierarchical storage.
    Similar to OpenCode's storage system.
    """

    def __init__(self, base_path: Path | None = None):
        if base_path is None:
            base_path = Path.home() / ".pycode" / "storage"

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: list[str]) -> Path:
        """Convert hierarchical key to file path"""
        # key like ["session", "project123", "session456"]
        # becomes: ~/.pycode/storage/session/project123/session456.json

        path = self.base_path
        for part in key[:-1]:
            path = path / part

        filename = key[-1] + ".json"
        return path / filename

    async def write(self, key: list[str], data: Any) -> None:
        """Write data to storage"""
        file_path = self._get_file_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert Pydantic models to dict
        if hasattr(data, "model_dump"):
            data = data.model_dump()

        async with aiofiles.open(file_path, "w") as f:
            await f.write(json.dumps(data, indent=2))

    async def read(self, key: list[str]) -> Any | None:
        """Read data from storage"""
        file_path = self._get_file_path(key)

        if not file_path.exists():
            return None

        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
            return json.loads(content)

    async def delete(self, key: list[str]) -> None:
        """Delete data from storage"""
        file_path = self._get_file_path(key)

        if file_path.exists():
            file_path.unlink()

    async def list_keys(self, prefix: list[str]) -> list[str]:
        """List keys with given prefix"""
        path = self.base_path
        for part in prefix:
            path = path / part

        if not path.exists():
            return []

        # List JSON files
        keys = []
        for file in path.glob("*.json"):
            keys.append(file.stem)  # filename without .json

        return keys

    async def exists(self, key: list[str]) -> bool:
        """Check if key exists"""
        file_path = self._get_file_path(key)
        return file_path.exists()

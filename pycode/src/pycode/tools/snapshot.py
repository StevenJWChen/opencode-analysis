"""Code snapshot tool for creating point-in-time code saves"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any
from .base import Tool, ToolContext, ToolResult


class SnapshotTool(Tool):
    """Create snapshots of code for versioning and comparison"""

    @property
    def name(self) -> str:
        return "snapshot"

    @property
    def description(self) -> str:
        return """Create snapshots of code files for version tracking and comparison.

Use this tool to:
- Save current state before major changes
- Create checkpoints during refactoring
- Track code evolution within a session
- Compare different versions
- Rollback to previous states

Features:
- Saves file content and metadata
- Stores snapshots in session directory
- Supports single files or multiple files
- Includes timestamp and description
- Enables rollback and comparison

Snapshots are stored in: .pycode/snapshots/

IMPORTANT:
- Snapshots are session-specific
- Files must exist to snapshot
- Use with patch tool for restoration
- Snapshots include full file content
- Metadata includes timestamp, file path, size
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File paths to snapshot (required)",
                },
                "description": {
                    "type": "string",
                    "description": "Description of this snapshot (optional)",
                },
                "snapshot_dir": {
                    "type": "string",
                    "description": "Directory to store snapshots (default: .pycode/snapshots)",
                },
            },
            "required": ["files"],
        }

    def _create_snapshot_data(self, file_path: Path) -> dict[str, Any]:
        """Create snapshot data for a single file"""
        stats = file_path.stat()

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "file_path": str(file_path.absolute()),
            "file_name": file_path.name,
            "content": content,
            "size": stats.st_size,
            "mtime": stats.st_mtime,
            "mtime_formatted": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "lines": len(content.splitlines()),
            "snapshot_time": datetime.now().isoformat(),
        }

    async def execute(self, parameters: dict[str, Any], context: ToolContext) -> ToolResult:
        files = parameters["files"]
        description = parameters.get("description", "Code snapshot")
        snapshot_dir_str = parameters.get("snapshot_dir", ".pycode/snapshots")

        if not files:
            return ToolResult(
                title="Snapshot",
                output="",
                error="No files provided for snapshot",
            )

        # Create snapshot directory
        snapshot_dir = Path(snapshot_dir_str)
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Generate snapshot ID
        snapshot_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = snapshot_dir / f"snapshot_{snapshot_id}.json"

        # Process all files
        snapshots = []
        errors = []
        total_size = 0
        total_lines = 0

        for file_path_str in files:
            file_path = Path(file_path_str)

            if not file_path.exists():
                errors.append(f"File not found: {file_path}")
                continue

            if not file_path.is_file():
                errors.append(f"Not a file: {file_path}")
                continue

            try:
                snapshot_data = self._create_snapshot_data(file_path)
                snapshots.append(snapshot_data)
                total_size += snapshot_data["size"]
                total_lines += snapshot_data["lines"]
            except Exception as e:
                errors.append(f"Failed to snapshot {file_path.name}: {str(e)}")

        if not snapshots and errors:
            return ToolResult(
                title="Snapshot",
                output="",
                error=f"No files could be snapshotted. Errors:\n" + "\n".join(errors),
            )

        # Create snapshot metadata
        snapshot_metadata = {
            "snapshot_id": snapshot_id,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "session_id": context.session_id,
            "total_files": len(snapshots),
            "total_size": total_size,
            "total_lines": total_lines,
            "files": snapshots,
            "errors": errors if errors else None,
        }

        # Save snapshot
        try:
            with open(snapshot_file, "w", encoding="utf-8") as f:
                json.dump(snapshot_metadata, f, indent=2)
        except Exception as e:
            return ToolResult(
                title="Snapshot",
                output="",
                error=f"Failed to save snapshot: {str(e)}",
            )

        # Format output
        output_lines = []
        output_lines.append(f"Snapshot ID: {snapshot_id}")
        output_lines.append(f"Description: {description}")
        output_lines.append(f"Saved to: {snapshot_file}")
        output_lines.append(f"\nSnapshot Summary:")
        output_lines.append(f"  Files: {len(snapshots)}")
        output_lines.append(f"  Total Lines: {total_lines:,}")
        output_lines.append(f"  Total Size: {total_size:,} bytes")
        output_lines.append(f"\nFiles Snapshotted:")

        for i, snap in enumerate(snapshots, 1):
            output_lines.append(f"  {i}. {snap['file_name']} ({snap['lines']} lines, {snap['size']} bytes)")

        if errors:
            output_lines.append(f"\n⚠️  Errors ({len(errors)}):")
            for error in errors:
                output_lines.append(f"  - {error}")

        output_lines.append(f"\n📝 Restore with:")
        output_lines.append(f"   patch tool using snapshot file: {snapshot_file}")

        output = "\n".join(output_lines)

        return ToolResult(
            title=f"Snapshot: {snapshot_id}",
            output=output,
            metadata={
                "snapshot_id": snapshot_id,
                "snapshot_file": str(snapshot_file),
                "files_count": len(snapshots),
                "total_lines": total_lines,
                "total_size": total_size,
                "errors_count": len(errors),
            },
        )

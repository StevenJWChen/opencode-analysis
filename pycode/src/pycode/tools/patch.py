"""Patch tool for applying code patches and restoring snapshots"""

import json
from pathlib import Path
from typing import Any
from difflib import unified_diff
from .base import Tool, ToolContext, ToolResult


class PatchTool(Tool):
    """Apply patches or restore from snapshots"""

    @property
    def name(self) -> str:
        return "patch"

    @property
    def description(self) -> str:
        return """Apply patches or restore files from snapshots.

Use this tool to:
- Restore files from snapshots
- Apply unified diff patches
- Rollback to previous states
- Revert changes

Supports:
- Snapshot restoration (from snapshot tool)
- Unified diff patches
- Selective file restoration
- Dry-run mode to preview changes

IMPORTANT:
- Use snapshot tool first to create snapshots
- Dry-run recommended before applying
- Creates backup before applying
- Shows diff of changes
- Supports partial restoration
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "snapshot_file": {
                    "type": "string",
                    "description": "Path to snapshot JSON file",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific files to restore (optional, defaults to all)",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview changes without applying (default: false)",
                },
                "create_backup": {
                    "type": "boolean",
                    "description": "Create backup before applying (default: true)",
                },
            },
            "required": ["snapshot_file"],
        }

    def _generate_diff(self, file_path: Path, old_content: str, new_content: str) -> str:
        """Generate unified diff"""
        diff_lines = list(
            unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{file_path.name}",
                tofile=f"b/{file_path.name}",
                lineterm="",
            )
        )
        return "".join(diff_lines)

    async def execute(self, parameters: dict[str, Any], context: ToolContext) -> ToolResult:
        snapshot_file_str = parameters["snapshot_file"]
        selected_files = parameters.get("files")
        dry_run = parameters.get("dry_run", False)
        create_backup = parameters.get("create_backup", True)

        snapshot_file = Path(snapshot_file_str)

        # Check snapshot file exists
        if not snapshot_file.exists():
            return ToolResult(
                title="Patch",
                output="",
                error=f"Snapshot file not found: {snapshot_file}",
            )

        # Load snapshot
        try:
            with open(snapshot_file, "r", encoding="utf-8") as f:
                snapshot_data = json.load(f)
        except json.JSONDecodeError as e:
            return ToolResult(
                title="Patch",
                output="",
                error=f"Invalid snapshot file format: {str(e)}",
            )
        except Exception as e:
            return ToolResult(
                title="Patch",
                output="",
                error=f"Failed to read snapshot: {str(e)}",
            )

        # Get files from snapshot
        snapshot_files = snapshot_data.get("files", [])
        if not snapshot_files:
            return ToolResult(
                title="Patch",
                output="",
                error="No files found in snapshot",
            )

        # Filter files if specific ones requested
        if selected_files:
            selected_set = set(selected_files)
            snapshot_files = [
                f
                for f in snapshot_files
                if Path(f["file_path"]).name in selected_set or f["file_path"] in selected_set
            ]

            if not snapshot_files:
                return ToolResult(
                    title="Patch",
                    output="",
                    error=f"None of the specified files found in snapshot: {selected_files}",
                )

        # Create backup directory if needed
        backup_dir = None
        if create_backup and not dry_run:
            from datetime import datetime

            backup_dir = Path(".pycode/backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)

        # Process files
        changes = []
        errors = []
        backed_up = []

        for file_data in snapshot_files:
            file_path = Path(file_data["file_path"])
            snapshot_content = file_data["content"]

            try:
                # Read current content if file exists
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        current_content = f.read()

                    # Check if content is different
                    if current_content == snapshot_content:
                        continue  # No changes needed

                    # Generate diff
                    diff = self._generate_diff(file_path, current_content, snapshot_content)

                    # Create backup if not dry run
                    if backup_dir and create_backup:
                        backup_file = backup_dir / file_path.name
                        with open(backup_file, "w", encoding="utf-8") as f:
                            f.write(current_content)
                        backed_up.append(str(backup_file))
                else:
                    # File doesn't exist - will be created
                    current_content = ""
                    diff = f"New file: {file_path}\n{snapshot_content[:500]}..."

                # Apply changes if not dry run
                if not dry_run:
                    # Create parent directories if needed
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(snapshot_content)

                changes.append(
                    {
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "diff": diff,
                        "existed": file_path.exists() if dry_run else True,
                    }
                )

            except Exception as e:
                errors.append(f"Failed to restore {file_path.name}: {str(e)}")

        # Format output
        output_lines = []
        mode = "DRY RUN - " if dry_run else ""
        output_lines.append(f"{mode}Patch from snapshot: {snapshot_data.get('snapshot_id', 'unknown')}")
        output_lines.append(f"Description: {snapshot_data.get('description', 'N/A')}")
        output_lines.append(f"\nFiles to restore: {len(changes)}")

        if backup_dir and backed_up:
            output_lines.append(f"Backups created in: {backup_dir}")
            output_lines.append(f"Files backed up: {len(backed_up)}")

        for i, change in enumerate(changes, 1):
            output_lines.append(f"\n{'=' * 60}")
            output_lines.append(f"File {i}/{len(changes)}: {change['file_name']}")
            output_lines.append("=" * 60)
            output_lines.append("\nChanges:")
            output_lines.append(change["diff"][:1000])  # Limit diff length
            if len(change["diff"]) > 1000:
                output_lines.append("\n... (diff truncated)")

        if errors:
            output_lines.append(f"\n⚠️  Errors ({len(errors)}):")
            for error in errors:
                output_lines.append(f"  - {error}")

        if dry_run:
            output_lines.append(f"\n{'=' * 60}")
            output_lines.append("DRY RUN - No files were modified")
            output_lines.append("Remove dry_run=true to apply changes")
            output_lines.append("=" * 60)

        if not changes and not errors:
            output_lines.append("\n✅ All files already match snapshot - no changes needed")

        output = "\n".join(output_lines)

        return ToolResult(
            title=f"{mode}Patch: {len(changes)} files",
            output=output,
            metadata={
                "snapshot_id": snapshot_data.get("snapshot_id"),
                "files_restored": len(changes),
                "backups_created": len(backed_up),
                "errors_count": len(errors),
                "dry_run": dry_run,
                "backup_dir": str(backup_dir) if backup_dir else None,
            },
        )

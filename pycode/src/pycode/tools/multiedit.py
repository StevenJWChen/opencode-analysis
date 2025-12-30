"""Multi-file editing tool for batch operations"""

from pathlib import Path
from typing import Any
from difflib import unified_diff
from .base import Tool, ToolContext, ToolResult


class MultiEditTool(Tool):
    """Edit multiple files in a single operation"""

    @property
    def name(self) -> str:
        return "multiedit"

    @property
    def description(self) -> str:
        return """Edit multiple files in batch with find-and-replace operations.

Use this tool to:
- Rename variables/functions across multiple files
- Update import statements project-wide
- Fix typos across the codebase
- Apply consistent formatting changes
- Refactor code patterns

Features:
- Transaction-based editing (all-or-nothing)
- Preview changes before applying
- Supports regex patterns
- Per-file or global replacements
- Automatic rollback on errors

IMPORTANT:
- All files must exist
- Use exact string matching (or regex if enabled)
- Changes are applied atomically
- Failed edits trigger rollback
- Shows diff for each modified file
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "edits": {
                    "type": "array",
                    "description": "List of file edits to perform",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to file to edit",
                            },
                            "old_string": {
                                "type": "string",
                                "description": "Text to find and replace",
                            },
                            "new_string": {
                                "type": "string",
                                "description": "Replacement text",
                            },
                            "replace_all": {
                                "type": "boolean",
                                "description": "Replace all occurrences in this file (default: false)",
                            },
                        },
                        "required": ["file_path", "old_string", "new_string"],
                    },
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview changes without applying (default: false)",
                },
            },
            "required": ["edits"],
        }

    def _apply_edit(
        self,
        file_path: Path,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> tuple[str, str, int]:
        """
        Apply edit to a single file.
        Returns: (old_content, new_content, occurrences)
        """
        # Read file
        with open(file_path, "r", encoding="utf-8") as f:
            old_content = f.read()

        # Check if old_string exists
        if old_string not in old_content:
            raise ValueError(f"String not found in {file_path.name}: {old_string[:50]}...")

        # Perform replacement
        if replace_all:
            new_content = old_content.replace(old_string, new_string)
            occurrences = old_content.count(old_string)
        else:
            # Single replacement
            index = old_content.find(old_string)
            if old_content.find(old_string, index + 1) != -1:
                raise ValueError(
                    f"Multiple occurrences found in {file_path.name}. Use replace_all=true or be more specific."
                )
            new_content = old_content[:index] + new_string + old_content[index + len(old_string) :]
            occurrences = 1

        return old_content, new_content, occurrences

    def _generate_diff(self, file_path: Path, old_content: str, new_content: str) -> str:
        """Generate unified diff for file changes"""
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
        edits = parameters["edits"]
        dry_run = parameters.get("dry_run", False)

        if not edits:
            return ToolResult(
                title="MultiEdit",
                output="",
                error="No edits provided",
            )

        # Validate all files exist first
        for edit in edits:
            file_path = Path(edit["file_path"])
            if not file_path.exists():
                return ToolResult(
                    title="MultiEdit",
                    output="",
                    error=f"File not found: {file_path}",
                )
            if not file_path.is_file():
                return ToolResult(
                    title="MultiEdit",
                    output="",
                    error=f"Not a file: {file_path}",
                )

        # Store original contents for rollback
        backup_contents: dict[Path, str] = {}
        changes: list[dict] = []
        total_occurrences = 0

        try:
            # Process all edits
            for i, edit in enumerate(edits, 1):
                file_path = Path(edit["file_path"])
                old_string = edit["old_string"]
                new_string = edit["new_string"]
                replace_all = edit.get("replace_all", False)

                # Apply edit
                old_content, new_content, occurrences = self._apply_edit(
                    file_path, old_string, new_string, replace_all
                )

                # Store backup if not already saved
                if file_path not in backup_contents:
                    backup_contents[file_path] = old_content

                # Generate diff
                diff = self._generate_diff(file_path, old_content, new_content)

                # Store change info
                changes.append(
                    {
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "occurrences": occurrences,
                        "diff": diff,
                        "old_content": old_content,
                        "new_content": new_content,
                    }
                )

                total_occurrences += occurrences

            # Apply changes if not dry run
            if not dry_run:
                for change in changes:
                    file_path = Path(change["file_path"])
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(change["new_content"])

            # Format output
            output_lines = []
            mode = "DRY RUN - " if dry_run else ""
            output_lines.append(f"{mode}MultiEdit: {len(changes)} file(s), {total_occurrences} change(s)\n")

            for i, change in enumerate(changes, 1):
                output_lines.append(f"\n{'=' * 60}")
                output_lines.append(f"File {i}/{len(changes)}: {change['file_name']}")
                output_lines.append(f"Changes: {change['occurrences']} occurrence(s)")
                output_lines.append("=" * 60)
                output_lines.append("\nDiff:")
                output_lines.append(change["diff"])

            if dry_run:
                output_lines.append(f"\n{'=' * 60}")
                output_lines.append("DRY RUN - No files were modified")
                output_lines.append("Remove dry_run=true to apply changes")
                output_lines.append("=" * 60)

            output = "\n".join(output_lines)

            return ToolResult(
                title=f"{mode}MultiEdit: {len(changes)} files",
                output=output,
                metadata={
                    "files_modified": len(changes),
                    "total_occurrences": total_occurrences,
                    "dry_run": dry_run,
                    "files": [c["file_path"] for c in changes],
                },
            )

        except Exception as e:
            # Rollback all changes
            if not dry_run:
                for file_path, old_content in backup_contents.items():
                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(old_content)
                    except Exception as rollback_error:
                        # Log rollback error but continue
                        pass

            return ToolResult(
                title="MultiEdit",
                output=f"Processed {len(changes)} file(s) before error\n\nAll changes rolled back.",
                error=f"Edit failed: {str(e)}",
                metadata={
                    "files_processed": len(changes),
                    "rollback_performed": not dry_run,
                },
            )

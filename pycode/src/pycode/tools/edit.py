"""File editing tool"""

from pathlib import Path
from difflib import unified_diff
from .base import Tool, ToolContext, ToolResult


class EditTool(Tool):
    """Edit files using exact string replacement"""

    @property
    def name(self) -> str:
        return "edit"

    @property
    def description(self) -> str:
        return """Edit files by replacing exact string matches.

Use this tool to:
- Modify existing code
- Fix bugs
- Implement features
- Update configuration

IMPORTANT:
- oldString must match EXACTLY (including whitespace)
- Set replaceAll=true to replace all occurrences
- Read the file first to see exact content
- The tool will show a diff of changes made
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the file to edit"},
                "old_string": {"type": "string", "description": "Exact text to replace"},
                "new_string": {
                    "type": "string",
                    "description": "Text to replace with (must differ from old_string)",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences (default: false)",
                },
            },
            "required": ["file_path", "old_string", "new_string"],
        }

    async def execute(self, parameters: dict, context: ToolContext) -> ToolResult:
        file_path_str = parameters["file_path"]
        old_string = parameters["old_string"]
        new_string = parameters["new_string"]
        replace_all = parameters.get("replace_all", False)

        file_path = Path(file_path_str)

        # Validate strings are different
        if old_string == new_string:
            return ToolResult(
                title=f"Edit {file_path.name}",
                output="",
                error="old_string and new_string must be different",
            )

        # Check file exists
        if not file_path.exists():
            return ToolResult(
                title=f"Edit {file_path.name}",
                output="",
                error=f"File not found: {file_path}",
            )

        try:
            # Read current content
            with open(file_path, "r", encoding="utf-8") as f:
                content_old = f.read()

            # Perform replacement
            if replace_all:
                content_new = content_old.replace(old_string, new_string)
                occurrences = content_old.count(old_string)

                if occurrences == 0:
                    return ToolResult(
                        title=f"Edit {file_path.name}",
                        output="",
                        error="old_string not found in file",
                    )

            else:
                # Single replacement
                index = content_old.find(old_string)

                if index == -1:
                    return ToolResult(
                        title=f"Edit {file_path.name}",
                        output="",
                        error="old_string not found in file",
                    )

                # Check uniqueness
                if content_old.find(old_string, index + 1) != -1:
                    return ToolResult(
                        title=f"Edit {file_path.name}",
                        output="",
                        error="old_string appears multiple times; use replace_all=true",
                    )

                content_new = content_old[:index] + new_string + content_old[index + len(old_string) :]
                occurrences = 1

            # Generate diff
            diff_lines = list(
                unified_diff(
                    content_old.splitlines(keepends=True),
                    content_new.splitlines(keepends=True),
                    fromfile=f"a/{file_path.name}",
                    tofile=f"b/{file_path.name}",
                    lineterm="",
                )
            )

            diff = "".join(diff_lines)

            # Write new content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content_new)

            return ToolResult(
                title=f"Edited {file_path.name}",
                output=f"Replaced {occurrences} occurrence(s)\n\n{diff}",
                metadata={
                    "file_path": str(file_path),
                    "occurrences": occurrences,
                    "lines_added": diff.count("\n+"),
                    "lines_removed": diff.count("\n-"),
                },
            )

        except Exception as e:
            return ToolResult(
                title=f"Edit {file_path.name}", output="", error=f"Failed to edit file: {str(e)}"
            )

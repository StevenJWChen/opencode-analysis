"""File reading tool"""

from pathlib import Path
from .base import Tool, ToolContext, ToolResult


class ReadTool(Tool):
    """Read file contents with optional line range"""

    @property
    def name(self) -> str:
        return "read"

    @property
    def description(self) -> str:
        return """Read file contents from the local filesystem.

Use this tool to:
- Read source code files
- Read configuration files
- Read documentation
- Inspect file contents before editing

The output includes line numbers for easier reference.
You can optionally specify a line range to read a portion of the file.
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the file to read"},
                "offset": {
                    "type": "number",
                    "description": "Line number to start reading from (0-indexed)",
                },
                "limit": {"type": "number", "description": "Number of lines to read"},
            },
            "required": ["file_path"],
        }

    async def execute(self, parameters: dict, context: ToolContext) -> ToolResult:
        file_path_str = parameters["file_path"]
        offset = parameters.get("offset", 0)
        limit = parameters.get("limit")

        file_path = Path(file_path_str)

        # Validate file exists
        if not file_path.exists():
            return ToolResult(
                title=f"Read {file_path.name}",
                output="",
                error=f"File not found: {file_path}",
            )

        if not file_path.is_file():
            return ToolResult(
                title=f"Read {file_path.name}",
                output="",
                error=f"Path is not a file: {file_path}",
            )

        try:
            # Read file
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total_lines = len(lines)

            # Apply offset and limit
            start = offset
            end = start + limit if limit else total_lines

            selected_lines = lines[start:end]

            # Format with line numbers (1-indexed for display)
            numbered_lines = [f"{start + i + 1}\t{line.rstrip()}" for i, line in enumerate(selected_lines)]

            output = "\n".join(numbered_lines)

            return ToolResult(
                title=f"Read {file_path.name}",
                output=output,
                metadata={
                    "file_path": str(file_path),
                    "total_lines": total_lines,
                    "lines_read": len(selected_lines),
                    "offset": start,
                },
            )

        except Exception as e:
            return ToolResult(
                title=f"Read {file_path.name}", output="", error=f"Failed to read file: {str(e)}"
            )

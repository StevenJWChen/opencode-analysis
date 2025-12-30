"""File writing tool"""

from pathlib import Path
from .base import Tool, ToolContext, ToolResult


class WriteTool(Tool):
    """Write content to a new file or overwrite existing file"""

    @property
    def name(self) -> str:
        return "write"

    @property
    def description(self) -> str:
        return """Write content to a file (create new or overwrite existing).

Use this tool to:
- Create new files
- Write generated code
- Create configuration files
- Save output to files

IMPORTANT:
- This will overwrite existing files without warning
- Use 'read' first to check if file exists
- Use 'edit' for modifying existing files
- Parent directories will be created automatically
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
                "create_parents": {
                    "type": "boolean",
                    "description": "Create parent directories if they don't exist (default: true)",
                },
            },
            "required": ["file_path", "content"],
        }

    async def execute(self, parameters: dict, context: ToolContext) -> ToolResult:
        file_path_str = parameters["file_path"]
        content = parameters["content"]
        create_parents = parameters.get("create_parents", True)

        file_path = Path(file_path_str)

        try:
            # Check if we need to create parent directories
            if create_parents and not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if parent directory exists
            if not file_path.parent.exists():
                return ToolResult(
                    title=f"Write {file_path.name}",
                    output="",
                    error=f"Parent directory does not exist: {file_path.parent}",
                )

            # Check if file already exists
            file_existed = file_path.exists()
            if file_existed:
                # Read old content for comparison
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        old_content = f.read()
                    old_lines = len(old_content.splitlines())
                except:
                    old_lines = 0
            else:
                old_lines = 0

            # Write the file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Calculate statistics
            new_lines = len(content.splitlines())
            file_size = len(content.encode("utf-8"))

            # Format output message
            if file_existed:
                action = "Overwrote"
                stats = f"Changed from {old_lines} to {new_lines} lines"
            else:
                action = "Created"
                stats = f"{new_lines} lines, {file_size} bytes"

            return ToolResult(
                title=f"{action} {file_path.name}",
                output=f"{action} file: {file_path}\n{stats}\n\nPreview (first 10 lines):\n"
                + "\n".join(content.splitlines()[:10]),
                metadata={
                    "file_path": str(file_path),
                    "action": "overwrite" if file_existed else "create",
                    "lines": new_lines,
                    "bytes": file_size,
                },
            )

        except PermissionError:
            return ToolResult(
                title=f"Write {file_path.name}",
                output="",
                error=f"Permission denied: {file_path}",
            )
        except Exception as e:
            return ToolResult(
                title=f"Write {file_path.name}",
                output="",
                error=f"Failed to write file: {str(e)}",
            )

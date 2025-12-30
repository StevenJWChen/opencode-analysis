"""Directory listing tool"""

from pathlib import Path
from datetime import datetime
from .base import Tool, ToolContext, ToolResult


class LsTool(Tool):
    """List directory contents with detailed information"""

    @property
    def name(self) -> str:
        return "ls"

    @property
    def description(self) -> str:
        return """List directory contents (similar to 'ls -la').

Use this tool to:
- Explore directory structure
- Check file sizes and permissions
- See modification times
- Identify file types

Output includes:
- File type (file, directory, symlink)
- File size (human-readable)
- Modification time
- Permissions (basic)
- Hidden files

IMPORTANT:
- Shows all files including hidden (dotfiles)
- Sorts alphabetically with directories first
- Includes . and .. entries
- Use 'glob' for pattern matching
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list (default: current directory)",
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "Show hidden files (default: true)",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "List subdirectories recursively (default: false)",
                },
                "max_depth": {
                    "type": "number",
                    "description": "Maximum recursion depth (default: 1)",
                },
            },
            "required": [],
        }

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format"""
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f}K"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f}M"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f}G"

    def _format_permissions(self, path: Path) -> str:
        """Format basic permission string"""
        import stat

        mode = path.stat().st_mode
        perms = []

        # Owner permissions
        perms.append("r" if mode & stat.S_IRUSR else "-")
        perms.append("w" if mode & stat.S_IWUSR else "-")
        perms.append("x" if mode & stat.S_IXUSR else "-")

        # Group permissions
        perms.append("r" if mode & stat.S_IRGRP else "-")
        perms.append("w" if mode & stat.S_IWGRP else "-")
        perms.append("x" if mode & stat.S_IXGRP else "-")

        # Other permissions
        perms.append("r" if mode & stat.S_IROTH else "-")
        perms.append("w" if mode & stat.S_IWOTH else "-")
        perms.append("x" if mode & stat.S_IXOTH else "-")

        return "".join(perms)

    def _format_entry(self, path: Path, base_path: Path, indent: int = 0) -> str:
        """Format a single directory entry"""
        try:
            stats = path.stat()
            size = stats.st_size
            mtime = datetime.fromtimestamp(stats.st_mtime)

            # Determine type
            if path.is_symlink():
                type_char = "l"
                target = f" -> {path.readlink()}"
            elif path.is_dir():
                type_char = "d"
                target = ""
            else:
                type_char = "-"
                target = ""

            # Format name with indentation
            try:
                name = str(path.relative_to(base_path))
            except ValueError:
                name = path.name

            if indent > 0:
                name = "  " * indent + name

            if path.is_dir() and not path.is_symlink():
                name += "/"

            # Format permissions
            perms = self._format_permissions(path)

            # Format size (only for files)
            if path.is_file():
                size_str = self._format_size(size).rjust(8)
            else:
                size_str = "       -"

            # Format modification time
            time_str = mtime.strftime("%b %d %H:%M")

            return f"{type_char}{perms} {size_str}  {time_str}  {name}{target}"

        except (OSError, PermissionError) as e:
            return f"?????????? ????????  ??? ?? ??:??  {path.name} (error: {e})"

    def _list_directory(
        self, path: Path, base_path: Path, show_hidden: bool, recursive: bool, max_depth: int, current_depth: int = 0
    ) -> list[str]:
        """Recursively list directory contents"""
        entries = []

        try:
            # Get all items in directory
            items = list(path.iterdir())

            # Filter hidden files if needed
            if not show_hidden:
                items = [item for item in items if not item.name.startswith(".")]

            # Sort: directories first, then alphabetically
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

            # Format each entry
            for item in items:
                entries.append(self._format_entry(item, base_path, current_depth))

                # Recurse into directories if needed
                if recursive and item.is_dir() and not item.is_symlink() and current_depth < max_depth:
                    entries.extend(
                        self._list_directory(item, base_path, show_hidden, recursive, max_depth, current_depth + 1)
                    )

        except PermissionError:
            entries.append(f"{'  ' * current_depth}(permission denied)")

        return entries

    async def execute(self, parameters: dict, context: ToolContext) -> ToolResult:
        path_str = parameters.get("path", context.working_directory)
        show_hidden = parameters.get("show_hidden", True)
        recursive = parameters.get("recursive", False)
        max_depth = parameters.get("max_depth", 1)

        path = Path(path_str)

        if not path.exists():
            return ToolResult(
                title=f"ls: {path}",
                output="",
                error=f"Path does not exist: {path}",
            )

        try:
            # Handle single file
            if path.is_file():
                output = self._format_entry(path, path.parent)
                return ToolResult(
                    title=f"ls: {path.name}",
                    output=output,
                    metadata={
                        "path": str(path),
                        "type": "file",
                        "count": 1,
                    },
                )

            # Handle directory
            if not path.is_dir():
                return ToolResult(
                    title=f"ls: {path}",
                    output="",
                    error=f"Not a directory: {path}",
                )

            # List directory contents
            entries = self._list_directory(path, path, show_hidden, recursive, max_depth)

            if not entries:
                output = f"Directory is empty: {path}"
                count = 0
            else:
                header = f"Listing: {path}\n"
                if recursive:
                    header += f"(recursive, max depth: {max_depth})\n"
                header += "\n"

                output = header + "\n".join(entries)
                count = len(entries)

            return ToolResult(
                title=f"ls: {path.name if path.name else path}",
                output=output,
                metadata={
                    "path": str(path),
                    "type": "directory",
                    "count": count,
                    "recursive": recursive,
                },
            )

        except Exception as e:
            return ToolResult(
                title=f"ls: {path}",
                output="",
                error=f"Failed to list directory: {str(e)}",
            )

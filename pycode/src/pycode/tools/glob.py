"""File pattern matching tool"""

from pathlib import Path
from .base import Tool, ToolContext, ToolResult


class GlobTool(Tool):
    """Find files matching glob patterns"""

    @property
    def name(self) -> str:
        return "glob"

    @property
    def description(self) -> str:
        return """Find files using glob patterns.

Use this tool to:
- Find files by extension (*.py, *.ts, *.json)
- Search directories recursively (**/test_*.py)
- Find files matching patterns (src/**/*.tsx)
- List files in specific locations

Pattern Examples:
- "*.py" - All Python files in current directory
- "**/*.py" - All Python files recursively
- "src/**/*.{ts,tsx}" - TypeScript files in src/
- "test_*.py" - Files starting with test_
- "[!.]*.py" - Python files not starting with dot

IMPORTANT:
- Patterns are relative to the search path
- Use ** for recursive directory matching
- Results are sorted by modification time (newest first)
- Hidden files (starting with .) are excluded by default
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match (e.g., '*.py', '**/*.ts')",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (default: current directory)",
                },
                "max_results": {
                    "type": "number",
                    "description": "Maximum number of results to return (default: 100)",
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files (starting with .) (default: false)",
                },
                "files_only": {
                    "type": "boolean",
                    "description": "Only return files, not directories (default: true)",
                },
            },
            "required": ["pattern"],
        }

    async def execute(self, parameters: dict, context: ToolContext) -> ToolResult:
        pattern = parameters["pattern"]
        search_path_str = parameters.get("path", context.working_directory)
        max_results = parameters.get("max_results", 100)
        include_hidden = parameters.get("include_hidden", False)
        files_only = parameters.get("files_only", True)

        search_path = Path(search_path_str)

        if not search_path.exists():
            return ToolResult(
                title=f"Glob: {pattern}",
                output="",
                error=f"Search path does not exist: {search_path}",
            )

        if not search_path.is_dir():
            return ToolResult(
                title=f"Glob: {pattern}",
                output="",
                error=f"Search path is not a directory: {search_path}",
            )

        try:
            # Perform glob search
            matches = list(search_path.glob(pattern))

            # Filter hidden files if needed
            if not include_hidden:
                matches = [m for m in matches if not any(part.startswith(".") for part in m.parts)]

            # Filter to files only if needed
            if files_only:
                matches = [m for m in matches if m.is_file()]

            # Sort by modification time (newest first)
            matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            # Limit results
            total_matches = len(matches)
            matches = matches[:max_results]

            if not matches:
                return ToolResult(
                    title=f"Glob: {pattern}",
                    output=f"No files found matching pattern: {pattern}\nSearch path: {search_path}",
                    metadata={
                        "pattern": pattern,
                        "search_path": str(search_path),
                        "count": 0,
                    },
                )

            # Format output
            output_lines = []
            output_lines.append(f"Found {total_matches} file(s) matching '{pattern}'")

            if total_matches > max_results:
                output_lines.append(f"Showing first {max_results} results")

            output_lines.append(f"Search path: {search_path}\n")

            for match in matches:
                # Get relative path from search path
                try:
                    rel_path = match.relative_to(search_path)
                except ValueError:
                    rel_path = match

                # Get file stats
                stats = match.stat()
                size = stats.st_size

                # Format size
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f}KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f}MB"

                # Format entry
                if match.is_dir():
                    output_lines.append(f"  {rel_path}/ (directory)")
                else:
                    output_lines.append(f"  {rel_path} ({size_str})")

            output = "\n".join(output_lines)

            return ToolResult(
                title=f"Glob: {pattern}",
                output=output,
                metadata={
                    "pattern": pattern,
                    "search_path": str(search_path),
                    "count": len(matches),
                    "total_count": total_matches,
                    "files": [str(m) for m in matches],
                },
            )

        except Exception as e:
            return ToolResult(
                title=f"Glob: {pattern}",
                output="",
                error=f"Glob search failed: {str(e)}",
            )

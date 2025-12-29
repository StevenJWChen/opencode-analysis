"""Code search tool using grep/ripgrep"""

import asyncio
from pathlib import Path
from .base import Tool, ToolContext, ToolResult


class GrepTool(Tool):
    """Search code using grep (or ripgrep if available)"""

    @property
    def name(self) -> str:
        return "grep"

    @property
    def description(self) -> str:
        return """Search code using grep/ripgrep for pattern matching.

Use this tool to:
- Find function/class definitions
- Search for specific keywords
- Locate TODO/FIXME comments
- Find usage of variables or imports

The tool will use ripgrep (rg) if available, otherwise falls back to grep.
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Pattern to search for (regex)"},
                "path": {"type": "string", "description": "Directory or file to search in"},
                "case_insensitive": {
                    "type": "boolean",
                    "description": "Case-insensitive search",
                },
                "include": {"type": "string", "description": "File glob pattern to include (e.g., '*.py')"},
                "max_results": {"type": "number", "description": "Maximum number of results to return"},
            },
            "required": ["pattern"],
        }

    async def _check_command_exists(self, command: str) -> bool:
        """Check if a command exists"""
        try:
            process = await asyncio.create_subprocess_shell(
                f"which {command}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False

    async def execute(self, parameters: dict, context: ToolContext) -> ToolResult:
        pattern = parameters["pattern"]
        search_path = parameters.get("path", context.working_directory)
        case_insensitive = parameters.get("case_insensitive", False)
        include = parameters.get("include")
        max_results = parameters.get("max_results", 100)

        # Check if ripgrep is available
        use_rg = await self._check_command_exists("rg")

        # Build command
        if use_rg:
            cmd = ["rg", "--color", "never", "--line-number"]
            if case_insensitive:
                cmd.append("-i")
            if include:
                cmd.extend(["--glob", include])
            cmd.extend([pattern, search_path])
        else:
            cmd = ["grep", "-rn"]
            if case_insensitive:
                cmd.append("-i")
            if include:
                cmd.extend(["--include", include])
            cmd.extend([pattern, search_path])

        try:
            # Execute search
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)

            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            if process.returncode != 0 and not stdout_text:
                # No matches found
                return ToolResult(
                    title=f"Searched for '{pattern}'",
                    output="No matches found.",
                    metadata={"pattern": pattern, "path": search_path, "matches": 0},
                )

            # Limit results
            lines = stdout_text.splitlines()
            if len(lines) > max_results:
                lines = lines[:max_results]
                truncated_msg = f"\n\n... ({len(lines) - max_results} more results truncated)"
            else:
                truncated_msg = ""

            output = "\n".join(lines) + truncated_msg

            return ToolResult(
                title=f"Searched for '{pattern}'",
                output=output,
                metadata={
                    "pattern": pattern,
                    "path": search_path,
                    "matches": len(lines),
                    "tool": "ripgrep" if use_rg else "grep",
                },
            )

        except asyncio.TimeoutError:
            return ToolResult(
                title=f"Searched for '{pattern}'",
                output="",
                error="Search timed out after 30 seconds",
            )
        except Exception as e:
            return ToolResult(
                title=f"Searched for '{pattern}'",
                output="",
                error=f"Search failed: {str(e)}",
            )

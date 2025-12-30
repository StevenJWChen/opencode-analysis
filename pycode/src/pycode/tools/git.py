"""Git operations tool"""

import asyncio
from pathlib import Path
from .base import Tool, ToolContext, ToolResult


class GitTool(Tool):
    """Execute common git operations"""

    # Maximum output length
    MAX_OUTPUT_LENGTH = 30_000

    # Default timeout for git commands
    DEFAULT_TIMEOUT = 30

    @property
    def name(self) -> str:
        return "git"

    @property
    def description(self) -> str:
        return """Execute git commands for version control operations.

Use this tool to:
- Check repository status (git status)
- View commit history (git log)
- See changes (git diff)
- View file changes (git show)
- Check branches (git branch)
- Inspect commits (git log, git show)

Supported Operations:
- status: Show working tree status
- diff: Show changes between commits, commit and working tree, etc.
- log: Show commit logs
- show: Show commit details
- branch: List, create, or delete branches
- blame: Show what revision and author last modified each line

IMPORTANT:
- Read-only operations only (no commits, pushes, or destructive actions)
- Runs in repository directory
- Output limited to prevent overflow
- Use bash tool for complex git workflows
- Timeout: 30 seconds per operation
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Git operation to perform",
                    "enum": ["status", "diff", "log", "show", "branch", "blame"],
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Additional arguments for the git command (optional)",
                },
                "path": {
                    "type": "string",
                    "description": "Repository path (default: working directory)",
                },
            },
            "required": ["operation"],
        }

    def _build_git_command(self, operation: str, args: list[str]) -> list[str]:
        """Build the git command with arguments"""
        cmd = ["git", operation]

        # Add default arguments for common operations
        if operation == "status":
            cmd.extend(["--short", "--branch"])
        elif operation == "log":
            if not any(arg.startswith("-") for arg in args):
                cmd.extend(["--oneline", "--max-count=20"])
        elif operation == "diff":
            if not args:
                cmd.append("HEAD")
        elif operation == "branch":
            if not args:
                cmd.append("-v")

        # Add user-provided arguments
        cmd.extend(args)

        return cmd

    async def execute(self, parameters: dict, context: ToolContext) -> ToolResult:
        operation = parameters["operation"]
        args = parameters.get("args", [])
        repo_path_str = parameters.get("path", context.working_directory)

        repo_path = Path(repo_path_str)

        if not repo_path.exists():
            return ToolResult(
                title=f"Git {operation}",
                output="",
                error=f"Path does not exist: {repo_path}",
            )

        # Check if it's a git repository
        git_dir = repo_path / ".git"
        if not git_dir.exists():
            # Try to find git dir in parent directories
            current = repo_path
            found = False
            for _ in range(10):  # Check up to 10 parent directories
                if (current / ".git").exists():
                    repo_path = current
                    found = True
                    break
                if current.parent == current:  # Reached root
                    break
                current = current.parent

            if not found:
                return ToolResult(
                    title=f"Git {operation}",
                    output="",
                    error=f"Not a git repository: {repo_path}",
                )

        try:
            # Build git command
            cmd = self._build_git_command(operation, args)

            # Execute git command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(repo_path),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.DEFAULT_TIMEOUT,
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    title=f"Git {operation}",
                    output="",
                    error=f"Command timed out after {self.DEFAULT_TIMEOUT} seconds",
                )

            # Decode output
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            # Limit output length
            if len(stdout_str) > self.MAX_OUTPUT_LENGTH:
                stdout_str = stdout_str[: self.MAX_OUTPUT_LENGTH] + "\n\n... (output truncated)"

            # Combine output
            output_parts = []

            if stdout_str:
                output_parts.append(stdout_str)

            if stderr_str and process.returncode != 0:
                output_parts.append(f"\nErrors:\n{stderr_str}")

            output = "\n".join(output_parts) if output_parts else "(no output)"

            # Check exit code
            if process.returncode != 0:
                return ToolResult(
                    title=f"Git {operation}",
                    output=output,
                    error=f"Git command failed with exit code {process.returncode}",
                    metadata={
                        "operation": operation,
                        "args": args,
                        "exit_code": process.returncode,
                        "repo_path": str(repo_path),
                    },
                )

            return ToolResult(
                title=f"Git {operation}",
                output=output,
                metadata={
                    "operation": operation,
                    "args": args,
                    "exit_code": 0,
                    "repo_path": str(repo_path),
                },
            )

        except FileNotFoundError:
            return ToolResult(
                title=f"Git {operation}",
                output="",
                error="Git is not installed or not found in PATH",
            )
        except Exception as e:
            return ToolResult(
                title=f"Git {operation}",
                output="",
                error=f"Failed to execute git command: {str(e)}",
            )

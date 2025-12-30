"""Bash command execution tool"""

import asyncio
import subprocess
from pathlib import Path
from .base import Tool, ToolContext, ToolResult


class BashTool(Tool):
    """Execute bash commands in the working directory"""

    MAX_OUTPUT_LENGTH = 30_000
    DEFAULT_TIMEOUT = 120  # seconds

    @property
    def name(self) -> str:
        return "bash"

    @property
    def description(self) -> str:
        return """Execute bash commands to perform system operations.

Use this tool to:
- Run git commands
- Install packages
- Build and test code
- Manipulate files and directories
- Check system state

IMPORTANT:
- Always provide a clear description of what the command does
- Use absolute paths when possible
- Commands run with a timeout (default: 120 seconds)
- Output is limited to prevent context overflow
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to execute"},
                "description": {
                    "type": "string",
                    "description": "Clear description of what this command does (5-10 words)",
                },
                "timeout": {
                    "type": "number",
                    "description": "Optional timeout in seconds (default: 120)",
                },
                "workdir": {
                    "type": "string",
                    "description": "Working directory to run the command in",
                },
            },
            "required": ["command", "description"],
        }

    async def execute(self, parameters: dict, context: ToolContext) -> ToolResult:
        command = parameters["command"]
        description = parameters["description"]
        timeout = parameters.get("timeout", self.DEFAULT_TIMEOUT)
        workdir = parameters.get("workdir", context.working_directory)

        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    title=description,
                    output="",
                    error=f"Command timed out after {timeout} seconds",
                    metadata={"timeout": timeout, "command": command},
                )

            # Decode output
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Combine output
            output = f"Exit code: {process.returncode}\n"
            if stdout_text:
                output += f"\nStdout:\n{stdout_text}"
            if stderr_text:
                output += f"\nStderr:\n{stderr_text}"

            # Limit output length
            if len(output) > self.MAX_OUTPUT_LENGTH:
                output = output[: self.MAX_OUTPUT_LENGTH] + "\n... (output truncated)"

            return ToolResult(
                title=description,
                output=output,
                metadata={
                    "exit_code": process.returncode,
                    "cwd": workdir,
                    "timeout": timeout,
                },
            )

        except Exception as e:
            return ToolResult(
                title=description, output="", error=f"Failed to execute command: {str(e)}"
            )

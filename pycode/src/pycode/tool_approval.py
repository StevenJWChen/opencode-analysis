"""
Tool Approval System

Provides interactive approval for tool execution.
Allows users to review and approve/deny risky operations.
"""

from typing import Literal
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
import json


console = Console()


class ToolApprovalDecision:
    """Represents a user's approval decision"""

    def __init__(
        self,
        approved: bool,
        remember: bool = False,
        choice: Literal["allow", "deny", "always", "never"] = "allow"
    ):
        self.approved = approved
        self.remember = remember
        self.choice = choice


class ToolApprovalManager:
    """Manages interactive tool approval"""

    def __init__(self):
        # Store remembered decisions
        self.remembered_decisions: dict[str, dict[str, bool]] = {}
        # always_allow and always_deny per tool
        self.always_allow: set[str] = set()
        self.always_deny: set[str] = set()

    def should_approve(self, tool_name: str, tool_args: dict, auto_approve: bool = False) -> ToolApprovalDecision:
        """
        Ask user if they want to approve a tool call

        Args:
            tool_name: Name of the tool
            tool_args: Tool arguments
            auto_approve: If True, automatically approve

        Returns:
            ToolApprovalDecision with approval result
        """

        # Check if auto-approve is enabled
        if auto_approve:
            return ToolApprovalDecision(approved=True, choice="allow")

        # Check if tool is in always allow list
        if tool_name in self.always_allow:
            return ToolApprovalDecision(approved=True, remember=True, choice="always")

        # Check if tool is in always deny list
        if tool_name in self.always_deny:
            return ToolApprovalDecision(approved=False, remember=True, choice="never")

        # Check if we have a remembered decision for this specific call
        call_key = self._get_call_key(tool_name, tool_args)
        if call_key in self.remembered_decisions:
            decision = self.remembered_decisions[call_key]
            return ToolApprovalDecision(
                approved=decision["approved"],
                remember=True,
                choice="always" if decision["approved"] else "never"
            )

        # Ask user interactively
        return self._prompt_user(tool_name, tool_args)

    def _get_call_key(self, tool_name: str, tool_args: dict) -> str:
        """Generate a unique key for this tool call"""
        try:
            args_json = json.dumps(tool_args, sort_keys=True)
            return f"{tool_name}:{args_json}"
        except:
            return f"{tool_name}:unknown"

    def _prompt_user(self, tool_name: str, tool_args: dict) -> ToolApprovalDecision:
        """
        Prompt user for approval

        Returns:
            ToolApprovalDecision
        """

        # Determine risk level
        risk_level = self._assess_risk(tool_name, tool_args)

        # Build approval prompt
        self._display_tool_request(tool_name, tool_args, risk_level)

        # Get user choice
        choices = {
            "y": ("Approve once", True, False, "allow"),
            "n": ("Deny once", False, False, "deny"),
            "a": ("Always approve this tool", True, True, "always"),
            "d": ("Always deny this tool", False, True, "never"),
            "s": ("Approve this specific call", True, True, "always"),
        }

        console.print("\n[bold]Options:[/bold]")
        for key, (desc, _, _, _) in choices.items():
            console.print(f"  [{key}] {desc}")

        choice = Prompt.ask(
            "\nApprove",
            choices=list(choices.keys()),
            default="y"
        )

        desc, approved, remember, choice_type = choices[choice]

        # Store decision if remember is True
        if remember:
            if choice == "a":
                self.always_allow.add(tool_name)
            elif choice == "d":
                self.always_deny.add(tool_name)
            elif choice == "s":
                call_key = self._get_call_key(tool_name, tool_args)
                self.remembered_decisions[call_key] = {"approved": approved}

        return ToolApprovalDecision(
            approved=approved,
            remember=remember,
            choice=choice_type
        )

    def _display_tool_request(self, tool_name: str, tool_args: dict, risk_level: str):
        """Display the tool request to the user"""

        # Set color based on risk
        risk_colors = {
            "low": "green",
            "medium": "yellow",
            "high": "red",
        }
        color = risk_colors.get(risk_level, "yellow")

        # Create title
        title = f"🔧 Tool Request: [bold]{tool_name}[/bold]"

        # Build content
        content_parts = []
        content_parts.append(f"[{color}]Risk Level: {risk_level.upper()}[/{color}]\n")

        # Show arguments
        content_parts.append("\n[bold]Arguments:[/bold]")
        for key, value in tool_args.items():
            # Truncate long values
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."

            # Highlight dangerous values
            if self._is_dangerous_value(key, value_str):
                content_parts.append(f"  [red]{key}[/red]: [red]{value_str}[/red]")
            else:
                content_parts.append(f"  {key}: [cyan]{value_str}[/cyan]")

        # Show warning for risky operations
        if risk_level == "high":
            content_parts.append("\n[bold red]⚠️  WARNING: This is a potentially destructive operation![/bold red]")

        content = "\n".join(content_parts)

        # Display panel
        panel = Panel(
            content,
            title=title,
            border_style=color,
            expand=False
        )

        console.print("\n")
        console.print(panel)

    def _assess_risk(self, tool_name: str, tool_args: dict) -> Literal["low", "medium", "high"]:
        """
        Assess the risk level of a tool call

        Returns:
            "low", "medium", or "high"
        """

        # High risk tools
        high_risk_tools = {"bash", "edit", "multiedit"}

        # Medium risk tools
        medium_risk_tools = {"write", "git", "snapshot"}

        # Check tool type
        if tool_name in high_risk_tools:
            # Check for dangerous commands
            if tool_name == "bash":
                command = tool_args.get("command", "")
                if self._is_dangerous_command(command):
                    return "high"
                return "medium"

            # Edit operations are medium risk
            if tool_name in {"edit", "multiedit"}:
                return "medium"

        elif tool_name in medium_risk_tools:
            return "medium"

        # Default to low risk
        return "low"

    def _is_dangerous_command(self, command: str) -> bool:
        """Check if a bash command is dangerous"""

        dangerous_patterns = [
            "rm -rf",
            "rm -fr",
            "dd if=",
            "mkfs",
            "format",
            "> /dev/",
            "curl", # Can download and execute
            "wget", # Can download and execute
            "chmod +x",
            "sudo",
            "su ",
        ]

        command_lower = command.lower()
        return any(pattern in command_lower for pattern in dangerous_patterns)

    def _is_dangerous_value(self, key: str, value: str) -> bool:
        """Check if an argument value is dangerous"""

        # Check for system directories
        dangerous_paths = [
            "/bin", "/boot", "/dev", "/etc", "/lib", "/proc",
            "/root", "/sbin", "/sys", "/usr", "/var"
        ]

        value_lower = value.lower()

        # Check paths
        if "path" in key.lower() or "file" in key.lower() or "dir" in key.lower():
            return any(value_lower.startswith(path) for path in dangerous_paths)

        # Check commands
        if "command" in key.lower() or "cmd" in key.lower():
            return self._is_dangerous_command(value)

        return False

    def clear_remembered(self):
        """Clear all remembered decisions"""
        self.remembered_decisions.clear()
        self.always_allow.clear()
        self.always_deny.clear()

    def get_stats(self) -> dict:
        """Get statistics about remembered decisions"""
        return {
            "always_allow": list(self.always_allow),
            "always_deny": list(self.always_deny),
            "remembered_calls": len(self.remembered_decisions)
        }

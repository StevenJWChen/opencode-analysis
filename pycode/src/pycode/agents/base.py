"""Base agent classes and configuration"""

from __future__ import annotations
from typing import Literal, Any
from pydantic import BaseModel, Field, ConfigDict
from abc import ABC, abstractmethod


Permission = Literal["allow", "deny", "ask"]


class AgentConfig(BaseModel):
    """Configuration for an agent"""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None
    mode: Literal["subagent", "primary", "all"] = "primary"
    native: bool = True
    hidden: bool = False
    default: bool = False

    # LLM parameters
    temperature: float | None = None
    top_p: float | None = None
    model_id: str | None = None
    provider_id: str | None = None

    # Behavior
    prompt: str | None = None  # Custom system prompt
    max_steps: int = 50  # Maximum iterations

    # Tool configuration
    tools: dict[str, bool] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)

    # Permissions
    edit_permission: Permission = "allow"
    bash_permissions: dict[str, Permission] = Field(default_factory=lambda: {"*": "allow"})
    skill_permissions: dict[str, Permission] = Field(default_factory=lambda: {"*": "allow"})
    webfetch_permission: Permission = "allow"
    doom_loop_permission: Permission = "ask"
    external_directory_permission: Permission = "ask"

    def check_bash_permission(self, command: str) -> Permission:
        """
        Check permission for a bash command using glob matching.
        More specific patterns take precedence.
        """
        import fnmatch

        # Find all matching patterns
        matches: list[tuple[str, Permission]] = []
        for pattern, permission in self.bash_permissions.items():
            if fnmatch.fnmatch(command, pattern):
                matches.append((pattern, permission))

        if not matches:
            return "deny"

        # Sort by specificity (longer pattern = more specific)
        matches.sort(key=lambda x: len(x[0]), reverse=True)

        # Return most specific match
        return matches[0][1]

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a tool is enabled for this agent"""
        if tool_name in self.tools:
            return self.tools[tool_name]

        # Check wildcard
        if "*" in self.tools:
            return self.tools["*"]

        return True  # Default: enabled


class Agent(ABC):
    """Base class for all agents"""

    def __init__(self, config: AgentConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def description(self) -> str:
        return self.config.description or f"Agent: {self.name}"

    @abstractmethod
    async def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        pass

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if agent can use a specific tool"""
        return self.config.is_tool_enabled(tool_name)

    async def on_message(self, message: str) -> None:
        """Called when a new user message is received"""
        pass

    async def on_tool_call(self, tool_name: str, args: dict[str, Any]) -> None:
        """Called when a tool is about to be executed"""
        pass

    async def on_tool_result(self, tool_name: str, result: Any, error: str | None = None) -> None:
        """Called after a tool is executed"""
        pass

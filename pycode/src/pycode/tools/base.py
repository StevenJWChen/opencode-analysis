"""Base tool classes and registry"""

from __future__ import annotations
from typing import Any, Callable
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, ConfigDict
from dataclasses import dataclass


@dataclass
class ToolContext:
    """Context provided to tools during execution"""

    session_id: str
    message_id: str
    agent_name: str
    call_id: str | None = None
    working_directory: str = "."
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Result returned by tool execution"""

    model_config = ConfigDict(extra="forbid")

    title: str  # Short description of what was done
    output: str  # Text output for LLM
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class Tool(ABC):
    """Base class for all tools"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description for LLM to understand when to use this tool"""
        pass

    @property
    @abstractmethod
    def parameters_schema(self) -> dict[str, Any]:
        """JSON schema for tool parameters"""
        pass

    @abstractmethod
    async def execute(self, parameters: dict[str, Any], context: ToolContext) -> ToolResult:
        """Execute the tool with given parameters"""
        pass

    def validate_parameters(self, parameters: dict[str, Any]) -> None:
        """Validate parameters against schema (can be overridden)"""
        # Basic validation - can be enhanced with jsonschema
        required = self.parameters_schema.get("required", [])
        for field in required:
            if field not in parameters:
                raise ValueError(f"Missing required parameter: {field}")


class ToolRegistry:
    """Registry for managing available tools"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool"""
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool"""
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get(self, tool_name: str) -> Tool | None:
        """Get a tool by name"""
        return self._tools.get(tool_name)

    def get_all(self) -> dict[str, Tool]:
        """Get all registered tools"""
        return self._tools.copy()

    def get_enabled_for_agent(self, agent_config: Any) -> dict[str, Tool]:
        """Get tools enabled for a specific agent"""
        enabled = {}
        for name, tool in self._tools.items():
            if agent_config.is_tool_enabled(name):
                enabled[name] = tool
        return enabled

    async def execute(
        self, tool_name: str, parameters: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        """Execute a tool by name"""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                title=f"Unknown tool: {tool_name}",
                output="",
                error=f"Tool '{tool_name}' not found in registry",
            )

        try:
            tool.validate_parameters(parameters)
            return await tool.execute(parameters, context)
        except Exception as e:
            return ToolResult(
                title=f"Tool execution failed: {tool_name}", output="", error=str(e)
            )

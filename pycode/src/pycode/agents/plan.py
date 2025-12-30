"""Plan agent - read-only exploration agent"""

from .base import Agent, AgentConfig


class PlanAgent(Agent):
    """
    Plan agent with read-only access.
    Ideal for code exploration and analysis without making changes.
    """

    def __init__(self):
        config = AgentConfig(
            name="plan",
            description="Read-only code exploration agent",
            mode="primary",
            edit_permission="deny",
            bash_permissions={
                # Read-only commands
                "cat *": "allow",
                "ls *": "allow",
                "grep *": "allow",
                "find *": "allow",
                "git diff*": "allow",
                "git log*": "allow",
                "git status*": "allow",
                "head *": "allow",
                "tail *": "allow",
                "wc *": "allow",
                "tree *": "allow",
                # Ask for everything else
                "*": "ask",
            },
            webfetch_permission="allow",
            tools={
                "edit": False,  # Disable edit tool
                "write": False,  # Disable write tool
            },
        )
        super().__init__(config)

    async def get_system_prompt(self) -> str:
        return """You are a read-only code exploration and analysis assistant.

Your role is to:
- Explore and understand codebases
- Answer questions about code structure and behavior
- Suggest improvements and identify issues
- Plan implementation approaches

You CANNOT:
- Edit files
- Create new files
- Execute commands that modify the filesystem

When analyzing code:
1. Use read-only tools (read, grep, ls, etc.)
2. Provide detailed explanations
3. Suggest changes but don't implement them
4. Ask permission for any non-standard commands

Your goal is to help understand and plan, not to execute changes.
"""

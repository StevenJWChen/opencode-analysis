"""Build agent - full-access development agent"""

from .base import Agent, AgentConfig


class BuildAgent(Agent):
    """
    Build agent with full development access.
    Default agent for active development work.
    """

    def __init__(self):
        config = AgentConfig(
            name="build",
            description="Full-access development agent",
            mode="primary",
            default=True,
            edit_permission="allow",
            bash_permissions={"*": "allow"},
            skill_permissions={"*": "allow"},
            webfetch_permission="allow",
            doom_loop_permission="ask",
            external_directory_permission="ask",
        )
        super().__init__(config)

    async def get_system_prompt(self) -> str:
        return """You are a helpful AI coding assistant with full access to the codebase.

You have the following capabilities:
- Read and edit files
- Execute bash commands
- Search code
- Analyze the project structure
- Make changes to implement features and fix bugs

When working on tasks:
1. Understand the request thoroughly
2. Read relevant files to understand context
3. Make targeted, precise changes
4. Test your changes when possible
5. Explain what you did and why

Use your tools effectively to accomplish the task. Be proactive but careful with file changes and bash commands.
"""

"""
Agent Runner - Main execution loop for vibe coding

This is the core engine that enables the iterative write-run-fix workflow:
1. User provides request
2. LLM writes code using tools
3. Tools execute (write files, run code, etc.)
4. LLM sees results
5. LLM fixes issues if needed
6. Repeat until success
"""

import json
from pathlib import Path
from typing import Any, AsyncIterator
from dataclasses import dataclass

from .core import Session, Message, TextPart, ToolPart, ToolState
from .agents import Agent, BuildAgent
from .tools import ToolRegistry, ToolContext
from .providers import Provider


@dataclass
class RunConfig:
    """Configuration for agent run"""

    max_iterations: int = 50
    verbose: bool = True
    auto_approve_tools: bool = False  # If False, ask for approval
    auto_approve_destructive: bool = False  # For rm, dd, etc.


class AgentRunner:
    """Main execution loop for vibe coding workflows"""

    def __init__(
        self,
        session: Session,
        agent: Agent,
        provider: Provider,
        registry: ToolRegistry,
        config: RunConfig | None = None,
    ):
        self.session = session
        self.agent = agent
        self.provider = provider
        self.registry = registry
        self.config = config or RunConfig()

        self.current_message: Message | None = None
        self.iteration_count = 0

    def _build_tool_definitions(self) -> list[dict[str, Any]]:
        """Build tool definitions for LLM"""
        tool_defs = []

        for tool_name, tool in self.registry.get_all().items():
            # Check if agent has access to this tool
            if not self.agent.can_use_tool(tool_name):
                continue

            tool_def = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters_schema,
                },
            }
            tool_defs.append(tool_def)

        return tool_defs

    def _build_conversation_history(self) -> list[dict[str, Any]]:
        """Build conversation history for LLM"""
        # In a full implementation, this would load from storage
        # For now, we'll build from current session messages
        messages = []

        # Add existing messages
        # TODO: Load from storage based on session.id

        return messages

    async def _execute_tool_call(
        self, tool_name: str, tool_args: dict[str, Any], tool_call_id: str
    ) -> ToolPart:
        """Execute a tool call and return result part"""

        # Create tool part
        tool_part = ToolPart(
            tool=tool_name,
            call_id=tool_call_id,
            state=ToolState(
                status="pending",
                input=tool_args,
            ),
        )

        # Create tool context
        context = ToolContext(
            session_id=self.session.id,
            message_id=self.current_message.id if self.current_message else "unknown",
            agent_name=self.agent.name,
            working_directory=self.session.directory,
        )

        try:
            # Update status
            tool_part.state.status = "running"

            if self.config.verbose:
                print(f"\n🔧 Running tool: {tool_name}")
                print(f"   Arguments: {json.dumps(tool_args, indent=2)}")

            # Execute tool
            result = await self.registry.execute(tool_name, tool_args, context)

            # Update state with result
            if result.error:
                tool_part.state.status = "error"
                tool_part.state.error = result.error
                tool_part.state.output = result.output
            else:
                tool_part.state.status = "success"
                tool_part.state.output = result.output

            if self.config.verbose:
                print(f"   ✅ Result: {result.title}")
                if result.output:
                    # Show first 200 chars of output
                    output_preview = result.output[:200]
                    if len(result.output) > 200:
                        output_preview += "..."
                    print(f"   Output: {output_preview}")
                if result.error:
                    print(f"   ❌ Error: {result.error}")

        except Exception as e:
            tool_part.state.status = "error"
            tool_part.state.error = str(e)

            if self.config.verbose:
                print(f"   ❌ Tool execution failed: {e}")

        return tool_part

    async def run(self, user_input: str) -> AsyncIterator[str]:
        """
        Main execution loop - the heart of vibe coding!

        This implements the iterative workflow:
        1. Send user request + tool definitions to LLM
        2. LLM responds with text and/or tool calls
        3. Execute tool calls (write code, run it, etc.)
        4. Send results back to LLM
        5. LLM sees results and decides next step
        6. Repeat until task complete or max iterations
        """

        # Create user message
        user_message = Message(
            session_id=self.session.id,
            role="user",
        )
        user_message.add_part(TextPart(text=user_input))

        # Build conversation
        conversation = self._build_conversation_history()
        conversation.append({"role": "user", "content": user_input})

        # Get tool definitions
        tool_definitions = self._build_tool_definitions()

        # Get system prompt from agent
        system_prompt = await self.agent.get_system_prompt()

        if self.config.verbose:
            print(f"\n{'=' * 60}")
            print(f"Agent: {self.agent.name}")
            print(f"Available tools: {len(tool_definitions)}")
            print(f"User request: {user_input}")
            print(f"{'=' * 60}\n")

        # Main iteration loop
        while self.iteration_count < self.config.max_iterations:
            self.iteration_count += 1

            if self.config.verbose:
                print(f"\n--- Iteration {self.iteration_count} ---")

            # Create assistant message for this iteration
            self.current_message = Message(
                session_id=self.session.id,
                role="assistant",
                agent=self.agent.name,
            )

            # Stream from LLM
            accumulated_text = ""
            tool_calls = []

            # Determine model to use
            model_id = self.agent.config.model_id or "claude-3-5-sonnet-20241022"

            try:
                async for event in self.provider.stream(
                    model=model_id,
                    messages=conversation,
                    system=system_prompt,
                    tools=tool_definitions,
                ):
                    if event.type == "text_delta":
                        text = event.data.get("text", "")
                        accumulated_text += text
                        yield text  # Stream to user

                    elif event.type == "tool_use":
                        # LLM wants to use a tool
                        tool_calls.append(event.data)

            except Exception as e:
                error_msg = f"\n❌ LLM Error: {str(e)}\n"
                yield error_msg
                break

            # Add text part if we got any text
            if accumulated_text:
                self.current_message.add_part(TextPart(text=accumulated_text))

            # Execute tool calls if any
            if tool_calls:
                if self.config.verbose:
                    print(f"\n🔧 LLM requested {len(tool_calls)} tool call(s)")

                tool_results = []

                for tool_call in tool_calls:
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("arguments", {})
                    tool_call_id = tool_call.get("id", f"call_{self.iteration_count}")

                    # Execute the tool
                    tool_part = await self._execute_tool_call(tool_name, tool_args, tool_call_id)

                    # Add to message
                    self.current_message.add_part(tool_part)

                    # Build tool result for next LLM call
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_call_id,
                            "content": tool_part.state.output or tool_part.state.error or "",
                            "is_error": tool_part.state.status == "error",
                        }
                    )

                # Add assistant message with tool calls to conversation
                conversation.append(
                    {
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": accumulated_text} if accumulated_text else None,
                            *[
                                {
                                    "type": "tool_use",
                                    "id": tc.get("id"),
                                    "name": tc.get("name"),
                                    "input": tc.get("arguments"),
                                }
                                for tc in tool_calls
                            ],
                        ],
                    }
                )

                # Add tool results
                conversation.append({"role": "user", "content": tool_results})

                # Continue loop - LLM will see results and decide next step
                continue

            else:
                # No tool calls - LLM is done
                if self.config.verbose:
                    print(f"\n✅ Task complete after {self.iteration_count} iteration(s)")
                break

        if self.iteration_count >= self.config.max_iterations:
            warning = f"\n⚠️  Reached maximum iterations ({self.config.max_iterations})\n"
            yield warning

    async def run_simple(self, user_input: str) -> str:
        """Simple synchronous run - returns final response"""
        full_response = ""
        async for chunk in self.run(user_input):
            full_response += chunk
        return full_response

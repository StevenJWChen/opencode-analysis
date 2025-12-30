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
from .history import MessageHistory
from .session_manager import SessionManager
from .storage import Storage
from .tool_approval import ToolApprovalManager
from .ui import get_ui, TerminalUI


@dataclass
class RunConfig:
    """Configuration for agent run"""

    max_iterations: int = 50
    verbose: bool = True
    auto_approve_tools: bool = False  # If False, ask for approval
    auto_approve_destructive: bool = False  # For rm, dd, etc.
    doom_loop_detection: bool = True  # Enable doom loop detection
    doom_loop_threshold: int = 3  # Number of identical calls before triggering


class AgentRunner:
    """Main execution loop for vibe coding workflows"""

    def __init__(
        self,
        session: Session,
        agent: Agent,
        provider: Provider,
        registry: ToolRegistry,
        config: RunConfig | None = None,
        storage: Storage | None = None,
    ):
        self.session = session
        self.agent = agent
        self.provider = provider
        self.registry = registry
        self.config = config or RunConfig()

        # Storage and history management
        self.storage = storage or Storage()
        self.history = MessageHistory(self.storage)
        self.session_manager = SessionManager(self.storage)

        # Tool approval management
        self.approval_manager = ToolApprovalManager()

        # Terminal UI
        self.ui = get_ui(verbose=self.config.verbose)

        self.current_message: Message | None = None
        self.iteration_count = 0

        # Doom loop detection
        self.tool_call_history: list[tuple[str, dict]] = []  # (tool_name, args)

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

    async def _build_conversation_history(self) -> list[dict[str, Any]]:
        """Build conversation history for LLM"""
        # Load conversation history from storage
        try:
            conversation = await self.history.get_conversation_for_llm(
                self.session.id,
                max_messages=20  # Keep last 20 messages
            )
            return conversation
        except Exception as e:
            # If loading fails, return empty conversation
            if self.config.verbose:
                print(f"Warning: Could not load conversation history: {e}")
            return []

    def _detect_doom_loop(self, tool_name: str, tool_args: dict) -> bool:
        """
        Detect if we're in a doom loop (repeating the same action)

        Returns:
            True if doom loop detected, False otherwise
        """
        if not self.config.doom_loop_detection:
            return False

        # Normalize args for comparison (convert to JSON string)
        normalized_args = json.dumps(tool_args, sort_keys=True)

        # Add to history
        self.tool_call_history.append((tool_name, normalized_args))

        # Check for repeated identical calls
        if len(self.tool_call_history) >= self.config.doom_loop_threshold:
            # Look at last N calls
            recent_calls = self.tool_call_history[-self.config.doom_loop_threshold:]

            # Check if all recent calls are identical
            first_call = recent_calls[0]
            if all(call == first_call for call in recent_calls):
                return True

            # Check for alternating patterns (A-B-A-B...)
            if len(recent_calls) >= 4:
                # Check if we're alternating between two actions
                pattern_1 = [recent_calls[0], recent_calls[1]] * 2
                if recent_calls[-4:] == pattern_1:
                    return True

        return False

    async def _execute_tool_call(
        self, tool_name: str, tool_args: dict[str, Any], tool_call_id: str
    ) -> ToolPart:
        """Execute a tool call and return result part"""

        # Create tool part
        tool_part = ToolPart(
            session_id=self.session.id,
            message_id=self.current_message.id if self.current_message else "unknown",
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

            # Show tool execution start
            self.ui.print_tool_execution(tool_name, tool_args)

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

            # Show tool execution result
            self.ui.print_tool_result(result.title, result.output, result.error)

        except Exception as e:
            tool_part.state.status = "error"
            tool_part.state.error = str(e)

            self.ui.print_tool_result("Execution Failed", None, str(e))

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
        user_message.add_part(TextPart(
            session_id=self.session.id,
            message_id=user_message.id,
            text=user_input
        ))

        # Save user message to history
        await self.history.save_message(self.session.id, user_message)

        # Update session timestamp
        self.session.touch()
        await self.session_manager.save_session(self.session)

        # Build conversation
        conversation = await self._build_conversation_history()
        conversation.append({"role": "user", "content": user_input})

        # Get tool definitions
        tool_definitions = self._build_tool_definitions()

        # Get system prompt from agent
        system_prompt = await self.agent.get_system_prompt()

        # Print session header
        self.ui.print_header(self.agent.name, len(tool_definitions), user_input)

        # Main iteration loop
        while self.iteration_count < self.config.max_iterations:
            self.iteration_count += 1

            # Print iteration marker
            self.ui.print_iteration(self.iteration_count)

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
                self.ui.print_llm_error(str(e))
                yield f"\n❌ LLM Error: {str(e)}\n"
                break

            # Add text part if we got any text
            if accumulated_text:
                self.current_message.add_part(TextPart(
                    session_id=self.session.id,
                    message_id=self.current_message.id,
                    text=accumulated_text
                ))

            # Execute tool calls if any
            if tool_calls:
                self.ui.print_tool_calls(len(tool_calls))

                tool_results = []

                for tool_call in tool_calls:
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("arguments", {})
                    tool_call_id = tool_call.get("id", f"call_{self.iteration_count}")

                    # Check for doom loop
                    if self._detect_doom_loop(tool_name, tool_args):
                        self.ui.print_doom_loop(tool_name)

                        doom_msg = f"\n\n⚠️  DOOM LOOP DETECTED!\n"
                        doom_msg += f"The agent is repeating the same action: {tool_name}\n"
                        doom_msg += f"This usually means the approach isn't working.\n"
                        doom_msg += f"Breaking the loop to prevent infinite execution.\n\n"
                        yield doom_msg

                        # Stop execution
                        return

                    # Check tool approval (if not auto-approve)
                    decision = self.approval_manager.should_approve(
                        tool_name,
                        tool_args,
                        auto_approve=self.config.auto_approve_tools
                    )

                    if not decision.approved:
                        # Tool was denied
                        denial_msg = f"\n❌ Tool call denied by user: {tool_name}\n"
                        yield denial_msg

                        # Create error tool part
                        tool_part = ToolPart(
                            session_id=self.session.id,
                            message_id=self.current_message.id,
                            tool=tool_name,
                            call_id=tool_call_id,
                            state=ToolState(
                                status="rejected",
                                input=tool_args,
                                error="Tool call denied by user"
                            ),
                        )
                        self.current_message.add_part(tool_part)

                        # Add to tool results
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call_id,
                            "content": "Tool call was denied by user",
                            "is_error": True,
                        })
                        continue

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

                # Save assistant message with tool calls
                if self.current_message:
                    await self.history.save_message(self.session.id, self.current_message)
                    self.session.touch()
                    await self.session_manager.save_session(self.session)

                # Continue loop - LLM will see results and decide next step
                continue

            else:
                # No tool calls - LLM is done
                # Save the final message
                if self.current_message:
                    await self.history.save_message(self.session.id, self.current_message)
                    self.session.touch()
                    await self.session_manager.save_session(self.session)

                self.ui.print_completion(self.iteration_count)
                break

        if self.iteration_count >= self.config.max_iterations:
            self.ui.print_max_iterations(self.config.max_iterations)
            warning = f"\n⚠️  Reached maximum iterations ({self.config.max_iterations})\n"
            yield warning

    async def run_simple(self, user_input: str) -> str:
        """Simple synchronous run - returns final response"""
        full_response = ""
        async for chunk in self.run(user_input):
            full_response += chunk
        return full_response

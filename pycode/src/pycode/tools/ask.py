"""Ask tool for user interaction and confirmation"""

from typing import Any, Literal
from .base import Tool, ToolContext, ToolResult


class AskTool(Tool):
    """Ask the user for input, confirmation, or choices"""

    @property
    def name(self) -> str:
        return "ask"

    @property
    def description(self) -> str:
        return """Ask the user for input, confirmation, or make a choice.

Use this tool to:
- Get user confirmation before destructive operations
- Request additional information
- Present choices and get selection
- Gather user preferences
- Interactive decision making

Question Types:
- confirm: Yes/no question (returns boolean)
- input: Free-form text input (returns string)
- choice: Multiple choice selection (returns selected option)

IMPORTANT:
- Use for important decisions
- Provide clear question text
- For choices, provide clear options
- Returns user's response
- Blocks execution until answered
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Question to ask the user (required)",
                },
                "type": {
                    "type": "string",
                    "description": "Type of question",
                    "enum": ["confirm", "input", "choice"],
                },
                "choices": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Options for choice type (required for choice type)",
                },
                "default": {
                    "type": "string",
                    "description": "Default value if user skips (optional)",
                },
            },
            "required": ["question", "type"],
        }

    def _ask_confirm(self, question: str, default: str | None = None) -> bool:
        """Ask yes/no question"""
        default_hint = ""
        if default:
            default_hint = f" [{'Y/n' if default.lower() == 'yes' else 'y/N'}]"

        while True:
            response = input(f"\n❓ {question}{default_hint}: ").strip().lower()

            if not response and default:
                return default.lower() in ["yes", "y", "true"]

            if response in ["yes", "y", "true", "1"]:
                return True
            elif response in ["no", "n", "false", "0"]:
                return False
            else:
                print("Please answer yes or no (y/n)")

    def _ask_input(self, question: str, default: str | None = None) -> str:
        """Ask for text input"""
        default_hint = f" [{default}]" if default else ""
        response = input(f"\n❓ {question}{default_hint}: ").strip()

        if not response and default:
            return default

        return response

    def _ask_choice(self, question: str, choices: list[str], default: str | None = None) -> str:
        """Ask user to choose from options"""
        print(f"\n❓ {question}\n")

        for i, choice in enumerate(choices, 1):
            default_marker = " (default)" if default and choice == default else ""
            print(f"  {i}. {choice}{default_marker}")

        while True:
            response = input(f"\nChoice [1-{len(choices)}]: ").strip()

            # Handle default
            if not response and default:
                return default

            # Handle numeric choice
            try:
                choice_num = int(response)
                if 1 <= choice_num <= len(choices):
                    return choices[choice_num - 1]
                else:
                    print(f"Please enter a number between 1 and {len(choices)}")
            except ValueError:
                # Try matching text
                for choice in choices:
                    if response.lower() == choice.lower():
                        return choice
                print("Invalid choice. Please try again.")

    async def execute(self, parameters: dict[str, Any], context: ToolContext) -> ToolResult:
        question = parameters["question"]
        question_type: Literal["confirm", "input", "choice"] = parameters["type"]
        choices = parameters.get("choices")
        default = parameters.get("default")

        # Validate parameters
        if question_type == "choice" and not choices:
            return ToolResult(
                title="Ask",
                output="",
                error="Choice type requires 'choices' parameter",
            )

        try:
            # Note: In a real implementation, this would integrate with the
            # session's UI/TUI to present the question
            # For now, we use command-line input

            if question_type == "confirm":
                answer = self._ask_confirm(question, default)
                answer_str = "Yes" if answer else "No"
                answer_value = answer

            elif question_type == "input":
                answer = self._ask_input(question, default)
                answer_str = answer
                answer_value = answer

            elif question_type == "choice":
                answer = self._ask_choice(question, choices, default)
                answer_str = answer
                answer_value = answer

            else:
                return ToolResult(
                    title="Ask",
                    output="",
                    error=f"Unknown question type: {question_type}",
                )

            # Format output
            output_lines = []
            output_lines.append(f"Question: {question}")
            output_lines.append(f"Type: {question_type}")
            if choices:
                output_lines.append(f"Choices: {', '.join(choices)}")
            output_lines.append(f"\nUser Response: {answer_str}")

            return ToolResult(
                title=f"Ask: {question_type}",
                output="\n".join(output_lines),
                metadata={
                    "question": question,
                    "type": question_type,
                    "answer": answer_value,
                    "answer_str": answer_str,
                },
            )

        except KeyboardInterrupt:
            return ToolResult(
                title="Ask",
                output="User cancelled input (Ctrl+C)",
                error="Operation cancelled by user",
            )
        except Exception as e:
            return ToolResult(
                title="Ask",
                output="",
                error=f"Failed to get user input: {str(e)}",
            )

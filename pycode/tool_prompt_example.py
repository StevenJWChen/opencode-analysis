"""
Example: How Tool Prompts Are Sent to the LLM

This shows the complete flow of how tool descriptions get to the LLM.
"""

import asyncio
import sys
sys.path.insert(0, 'src')

from pycode.tools import ToolRegistry, BashTool, ReadTool, EditTool, GrepTool
from pycode.agents import BuildAgent


def build_tool_definitions(registry: ToolRegistry) -> list[dict]:
    """
    Convert tool registry to LLM tool definitions.
    This is what gets sent to the LLM API.
    """
    tool_definitions = []

    for tool_name, tool in registry.get_all().items():
        tool_def = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters_schema
            }
        }
        tool_definitions.append(tool_def)

    return tool_definitions


def build_system_prompt(agent: BuildAgent) -> str:
    """
    Build the system prompt that tells the LLM how to behave.
    This explains the agent's role and capabilities.
    """
    return f"""You are a helpful AI coding assistant with the following capabilities:

**Agent**: {agent.name}
**Description**: {agent.description}

**Your Role:**
- Understand user requests thoroughly
- Use available tools to accomplish tasks
- Provide clear explanations of your actions
- Write clean, maintainable code

**Guidelines:**
1. **Use Tools Effectively**: You have access to various tools for file operations,
   code search, and system commands. Use them appropriately.

2. **Be Precise**: When using tools, provide accurate parameters. For bash commands,
   always include a clear description of what the command does.

3. **Explain Your Work**: After using tools, explain what you found or what changes
   you made and why.

4. **Safety First**: Be careful with destructive operations. Think before executing
   commands that modify or delete files.

**Available Tools:**
The tools available to you are defined in the function calling interface. Each tool
has its own description and parameter schema that explains how to use it.

**Workflow:**
1. Understand the user's request
2. Plan your approach
3. Use tools as needed
4. Provide clear responses
5. Verify your work when possible

Let's help the user accomplish their coding tasks efficiently and safely!
"""


async def demonstrate_llm_prompt_construction():
    """
    Show exactly what would be sent to the LLM API
    """
    print("="*70)
    print("  HOW TOOL PROMPTS ARE SENT TO THE LLM")
    print("="*70)

    # Setup
    agent = BuildAgent()
    registry = ToolRegistry()
    registry.register(BashTool())
    registry.register(ReadTool())
    registry.register(EditTool())
    registry.register(GrepTool())

    # 1. Build system prompt
    system_prompt = build_system_prompt(agent)
    print("\n📝 SYSTEM PROMPT (tells LLM its role):\n")
    print(system_prompt)

    # 2. Build tool definitions
    tool_defs = build_tool_definitions(registry)
    print("\n" + "="*70)
    print("\n🔧 TOOL DEFINITIONS (tells LLM what tools are available):\n")

    import json
    for i, tool_def in enumerate(tool_defs, 1):
        print(f"\n--- Tool {i}: {tool_def['function']['name']} ---")
        print(json.dumps(tool_def, indent=2))

    # 3. Show how it would be called
    print("\n" + "="*70)
    print("\n🚀 HOW THIS GETS SENT TO THE LLM API:\n")

    example_call = """
# For Anthropic Claude:
response = await anthropic_client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=8192,
    system=system_prompt,  # ← System prompt with agent role
    tools=tool_definitions,  # ← All tool definitions
    messages=[
        {
            "role": "user",
            "content": "Help me understand the project structure"
        }
    ]
)

# For OpenAI GPT:
response = await openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": system_prompt  # ← System prompt
        },
        {
            "role": "user",
            "content": "Help me understand the project structure"
        }
    ],
    tools=tool_definitions,  # ← All tool definitions
    tool_choice="auto"
)
"""
    print(example_call)

    # 4. Show what LLM sees
    print("\n" + "="*70)
    print("\n👁️  WHAT THE LLM SEES:\n")

    print("""
The LLM receives:

1. **System Prompt**: Explains its role as a coding assistant
2. **Tool Definitions**: JSON schemas for each tool with:
   - Tool name (e.g., "bash", "read", "edit")
   - Description (what the tool does, when to use it)
   - Parameters schema (what arguments it accepts)
3. **Conversation History**: Previous messages
4. **User Request**: Current message to respond to

The LLM then decides:
- What to say in natural language
- Which tools to call (if any)
- What arguments to pass to each tool

Example LLM response:
{
  "role": "assistant",
  "content": "I'll check the project structure for you.",
  "tool_calls": [
    {
      "id": "call_123",
      "type": "function",
      "function": {
        "name": "bash",
        "arguments": {
          "command": "ls -la",
          "description": "List project files"
        }
      }
    }
  ]
}
""")

    # 5. Show individual tool prompts
    print("\n" + "="*70)
    print("\n📋 INDIVIDUAL TOOL DESCRIPTIONS:\n")

    for tool_name, tool in registry.get_all().items():
        print(f"\n🔧 {tool.name.upper()}")
        print("-" * 50)
        print(tool.description)
        print("\nParameters:")
        print(json.dumps(tool.parameters_schema, indent=2))


async def show_real_world_example():
    """
    Show a complete example of LLM conversation with tool use
    """
    print("\n\n" + "="*70)
    print("  REAL-WORLD EXAMPLE: LLM CONVERSATION WITH TOOLS")
    print("="*70 + "\n")

    print("""
USER MESSAGE:
"Help me find all TODO comments in the project"

↓

LLM RECEIVES:
- System prompt (agent role + instructions)
- Tool definitions (bash, read, edit, grep with full descriptions)
- User message

↓

LLM THINKS:
"I need to search for TODO comments. The 'grep' tool is perfect for this.
Looking at the grep tool definition, I need to provide:
- pattern: The search pattern
- path: Where to search
- max_results: Limit results

I'll search for 'TODO' in the current directory."

↓

LLM RESPONDS:
{
  "content": "I'll search for all TODO comments in the project.",
  "tool_calls": [
    {
      "function": {
        "name": "grep",
        "arguments": {
          "pattern": "TODO",
          "path": ".",
          "max_results": 50
        }
      }
    }
  ]
}

↓

PYCODE EXECUTES:
await registry.execute("grep", {"pattern": "TODO", "path": ".", ...})

↓

TOOL RESULT:
src/main.py:45:    # TODO: Add error handling
src/utils.py:12:   # TODO: Optimize this function
tests/test.py:8:   # TODO: Add more test cases

↓

RESULT SENT BACK TO LLM:
{
  "role": "tool",
  "tool_call_id": "call_123",
  "content": "src/main.py:45:    # TODO: Add error handling\\n..."
}

↓

LLM FINAL RESPONSE:
"I found 3 TODO comments in your project:
1. Line 45 in src/main.py - Add error handling
2. Line 12 in src/utils.py - Optimize this function
3. Line 8 in tests/test.py - Add more test cases

Would you like me to help you address any of these?"
""")


if __name__ == "__main__":
    asyncio.run(demonstrate_llm_prompt_construction())
    asyncio.run(show_real_world_example())

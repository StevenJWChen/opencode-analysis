# Python Implementation Guide

## Overview

This document describes the Python implementation of an AI coding agent inspired by OpenCode (vibe coding).

## What Was Implemented

### ✅ Completed Components

1. **Core Data Structures** (`src/pycode/core/`)
   - `Identifier` - ULID-based ID generation (ascending/descending)
   - `Message` - User and assistant messages with parts
   - `Session` - Conversation sessions with metadata
   - Part types: TextPart, ToolPart, FilePart, AgentPart, ReasoningPart

2. **Agent System** (`src/pycode/agents/`)
   - `Agent` base class with configuration
   - `BuildAgent` - Full-access development agent
   - `PlanAgent` - Read-only exploration agent
   - Permission system with glob-based command matching

3. **Tool System** (`src/pycode/tools/`)
   - `Tool` base class and `ToolRegistry`
   - `BashTool` - Execute shell commands
   - `ReadTool` - Read files with line ranges
   - `EditTool` - Edit files with exact string replacement
   - `GrepTool` - Search code with grep/ripgrep

4. **Provider Integration** (`src/pycode/providers/`)
   - `Provider` base class with streaming support
   - `AnthropicProvider` - Claude integration
   - `OpenAIProvider` - GPT integration
   - Async streaming with `StreamEvent`

5. **Storage Layer** (`src/pycode/storage/`)
   - `Storage` - File-based JSON storage
   - Hierarchical key-value structure
   - Async file I/O with aiofiles

6. **CLI Interface** (`src/pycode/cli/`)
   - Basic Click-based CLI
   - Commands: run, models, version
   - Rich console output

## Architecture Comparison

| Component | OpenCode (TypeScript) | PyCode (Python) |
|-----------|----------------------|-----------------|
| **Runtime** | Bun/Node.js | Python 3.10+ |
| **Type System** | TypeScript | Python + Pydantic |
| **Validation** | Zod | Pydantic |
| **Async** | async/await | asyncio |
| **UI** | SolidJS TUI | Rich (basic) |
| **AI SDK** | Vercel AI SDK | Native provider SDKs |
| **Storage** | File-based JSON | File-based JSON |
| **ID Generation** | ULID | python-ulid |

## Key Design Decisions

### 1. Pydantic for Data Validation

Used Pydantic instead of dataclasses for:
- Automatic validation
- JSON serialization/deserialization
- Type coercion
- Configuration management

```python
class Message(BaseModel):
    id: str
    session_id: str
    role: Literal["user", "assistant"]
    parts: list[MessagePart]
```

### 2. AsyncIO for Concurrency

All I/O operations are async:
- LLM streaming
- File operations
- Tool execution
- Storage access

```python
async def execute(self, parameters: dict, context: ToolContext) -> ToolResult:
    # Async tool execution
    pass
```

### 3. Protocol-Based Providers

Each provider implements streaming via AsyncIterator:

```python
async def stream(
    self, model: str, messages: list[dict], ...
) -> AsyncIterator[StreamEvent]:
    # Stream events
    yield StreamEvent(type="text_delta", data={"text": "..."})
```

### 4. File-Based Storage

Similar to OpenCode, using hierarchical JSON files:

```
~/.pycode/storage/
  sessions/
    project_id/
      session_id.json
```

## Installation and Usage

### Install Dependencies

```bash
cd pycode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Configuration

Create `~/.pycode/config.yaml`:

```yaml
providers:
  anthropic:
    api_key: "sk-ant-..."
  openai:
    api_key: "sk-..."

default_model:
  provider: anthropic
  model: claude-3-7-sonnet-20250219
```

### Run Examples

```bash
# Run basic examples
cd pycode
python examples/basic_usage.py

# CLI usage
pycode run "Help me understand this code"
pycode --agent plan run "Analyze the structure"
pycode models
```

## What's Missing (Future Work)

### 🔧 To Complete Full Implementation

1. **Streaming Processor** - Main execution loop
   - Integrate LLM streaming with tool execution
   - Handle tool calls from LLM responses
   - Manage conversation state

2. **Permission System** - User approval dialogs
   - Interactive permission prompts
   - Permission persistence
   - Doom loop detection

3. **Advanced TUI** - Rich terminal interface
   - Split-pane views
   - Real-time streaming display
   - Interactive session management

4. **Configuration Management**
   - YAML config loading
   - Environment variable support
   - Agent customization

5. **Additional Tools**
   - Write tool (create new files)
   - Glob tool (file pattern matching)
   - LSP integration
   - Git tools

6. **Context Management**
   - Message history building
   - Context compression
   - Snapshot/patch system

7. **Testing**
   - Unit tests for all components
   - Integration tests
   - Mock providers for testing

## Code Statistics

```
pycode/
├── src/pycode/
│   ├── core/          # ~200 lines
│   ├── agents/        # ~150 lines
│   ├── tools/         # ~400 lines
│   ├── providers/     # ~250 lines
│   ├── storage/       # ~80 lines
│   └── cli/           # ~120 lines
├── examples/          # ~150 lines
└── Total: ~1,350 lines of Python
```

## Example: How It Works

### 1. Create a Session

```python
from pycode.core import Session

session = Session(
    project_id="my-project",
    directory="/path/to/project",
    title="My Coding Session"
)
```

### 2. Setup Agent and Tools

```python
from pycode.agents import BuildAgent
from pycode.tools import ToolRegistry, BashTool, ReadTool

agent = BuildAgent()
registry = ToolRegistry()
registry.register(BashTool())
registry.register(ReadTool())
```

### 3. Execute Tools

```python
from pycode.tools import ToolContext

context = ToolContext(
    session_id=session.id,
    message_id="msg_001",
    agent_name=agent.name,
    working_directory=session.directory
)

result = await registry.execute(
    "bash",
    {"command": "git status", "description": "Check git status"},
    context
)

print(result.output)
```

### 4. Stream from LLM (Conceptual)

```python
from pycode.providers import AnthropicProvider, ProviderConfig

config = ProviderConfig(
    name="anthropic",
    api_key="your-key"
)
provider = AnthropicProvider(config)

async for event in provider.stream(
    model="claude-3-7-sonnet-20250219",
    messages=[{"role": "user", "content": "Hello!"}],
    system="You are a helpful assistant"
):
    if event.type == "text_delta":
        print(event.data["text"], end="", flush=True)
```

## Differences from OpenCode

### Simplified Areas

1. **No Bus System** - Direct function calls instead of event bus
2. **No Plugin System** - Core functionality only
3. **Simpler Streaming** - Basic async iteration vs complex state machine
4. **No Server** - CLI-only, no HTTP/WebSocket server
5. **Fewer Tools** - Core 4 tools vs 20+ in OpenCode

### Python Advantages

1. **Simpler Syntax** - More concise than TypeScript
2. **Built-in Async** - Native asyncio support
3. **Rich Ecosystem** - Extensive Python libraries
4. **Easier Testing** - pytest async support
5. **Data Science Integration** - Can integrate with pandas, numpy, etc.

### OpenCode Advantages

1. **Bun Performance** - Faster startup and execution
2. **Type Safety** - Stricter TypeScript types
3. **Full-Featured** - Complete implementation
4. **Web UI** - SolidJS-based interface
5. **Multi-Client** - Server/client architecture

## Extending the Implementation

### Add a New Tool

```python
from pycode.tools import Tool, ToolContext, ToolResult

class MyTool(Tool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "My custom tool"

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param": {"type": "string"}
            },
            "required": ["param"]
        }

    async def execute(self, parameters: dict, context: ToolContext) -> ToolResult:
        # Your logic here
        return ToolResult(
            title="Executed MyTool",
            output="Result",
            metadata={}
        )
```

### Add a New Provider

```python
from pycode.providers import Provider, ProviderConfig, StreamEvent
from typing import AsyncIterator

class MyProvider(Provider):
    @property
    def name(self) -> str:
        return "myprovider"

    async def stream(self, model: str, messages: list, **kwargs) -> AsyncIterator[StreamEvent]:
        # Implement streaming logic
        yield StreamEvent(type="text_delta", data={"text": "Hello"})

    async def list_models(self) -> list[str]:
        return ["my-model-1", "my-model-2"]
```

## Testing

```bash
# Run tests (when implemented)
pytest

# Type checking
mypy src/

# Formatting
black src/

# Linting
ruff check src/
```

## Conclusion

This Python implementation demonstrates the core concepts of OpenCode in a simpler, more approachable form:

- ✅ Clean architecture with clear separation of concerns
- ✅ Modern Python with type hints and Pydantic
- ✅ Async/await for concurrent operations
- ✅ Extensible design for tools and providers
- ✅ ~1,350 lines vs ~50,000 in full OpenCode

The implementation serves as:
1. **Educational resource** - Understanding AI coding agent architecture
2. **Prototyping platform** - Quick experimentation with new ideas
3. **Foundation** - Can be extended to full-featured system
4. **Python alternative** - For teams preferring Python over TypeScript

---

*This implementation was created as a learning exercise and demonstration of OpenCode's architecture in Python. For production use, consider the full OpenCode implementation.*

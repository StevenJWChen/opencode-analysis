# PyCode Features Guide

Comprehensive guide to all PyCode features and capabilities.

## Table of Contents

1. [Core Features](#core-features)
2. [LLM Provider Support](#llm-provider-support)
3. [Tool System](#tool-system)
4. [Interactive Features](#interactive-features)
5. [Terminal UI](#terminal-ui)
6. [Safety & Security](#safety--security)
7. [Configuration](#configuration)
8. [Examples](#examples)

---

## Core Features

### Vibe Coding Workflow

PyCode implements the complete **write-run-fix** iterative workflow:

1. **Write**: LLM writes code using tools
2. **Run**: Code executes automatically
3. **Fix**: LLM sees results and fixes issues
4. **Repeat**: Continues until success or max iterations

```python
from pycode import AgentRunner, BuildAgent, RunConfig
from pycode.providers import AnthropicProvider, ProviderConfig
from pycode.tools import ToolRegistry

# Create agent
agent = BuildAgent()

# Setup provider
provider = AnthropicProvider(ProviderConfig(
    name="anthropic",
    api_key="your-api-key"
))

# Create runner
runner = AgentRunner(
    session=session,
    agent=agent,
    provider=provider,
    registry=ToolRegistry(),
    config=RunConfig(max_iterations=50)
)

# Run with streaming
async for chunk in runner.run("Create a fibonacci calculator"):
    print(chunk, end="", flush=True)
```

### Session Management

- **Persistent sessions**: Resume work across restarts
- **Message history**: Full conversation tracking
- **Context management**: Automatic context windowing
- **Multi-session support**: Work on multiple projects

### Doom Loop Detection

Automatic detection of infinite loops:

```python
config = RunConfig(
    doom_loop_detection=True,    # Enable detection
    doom_loop_threshold=3         # Trigger after 3 identical calls
)
```

Detects:
- Identical repeated actions
- Alternating A-B-A-B patterns
- Stuck iteration cycles

---

## LLM Provider Support

PyCode supports **6 major LLM providers** with unified interface:

### 1. Anthropic (Claude)

```python
from pycode.providers import AnthropicProvider, ProviderConfig

provider = AnthropicProvider(ProviderConfig(
    name="anthropic",
    api_key="sk-ant-..."
))

# Use Claude 3.5 Sonnet
async for chunk in runner.run("Write a sorting algorithm"):
    print(chunk)
```

**Models**: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku

### 2. OpenAI (GPT)

```python
from pycode.providers import OpenAIProvider

provider = OpenAIProvider(ProviderConfig(
    name="openai",
    api_key="sk-..."
))
```

**Models**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo

### 3. Ollama (Local Models)

```python
from pycode.providers import OllamaProvider

provider = OllamaProvider(ProviderConfig(
    name="ollama",
    base_url="http://localhost:11434"
))

# List available models
models = await provider.list_models()
print(models)  # ['llama3.2:latest', 'codellama:latest', ...]
```

**Supported Models**:
- llama3.2 (3B, 1B)
- codellama (7B, 13B, 34B)
- mistral (7B)
- qwen2.5-coder (various sizes)

**Advantages**:
- ✅ Fully offline
- ✅ No API costs
- ✅ Complete privacy
- ✅ Fast local inference

### 4. Google Gemini

```python
from pycode.providers import GeminiProvider

provider = GeminiProvider(ProviderConfig(
    name="gemini",
    api_key="YOUR_GEMINI_API_KEY"
))
```

**Models**:
- gemini-1.5-pro (most capable)
- gemini-1.5-flash (fast)
- gemini-1.0-pro

### 5. Mistral AI

```python
from pycode.providers import MistralProvider

provider = MistralProvider(ProviderConfig(
    name="mistral",
    api_key="YOUR_MISTRAL_API_KEY"
))
```

**Models**:
- mistral-large (most capable)
- mistral-medium
- mistral-small
- mistral-tiny

### 6. Cohere

```python
from pycode.providers import CohereProvider

provider = CohereProvider(ProviderConfig(
    name="cohere",
    api_key="YOUR_COHERE_API_KEY"
))
```

**Models**:
- command-r-plus (most capable)
- command-r (RAG optimized)
- command
- command-light

### Provider Comparison

| Provider | Streaming | Function Calling | Local | Cost |
|----------|-----------|------------------|-------|------|
| Anthropic | ✅ | ✅ | ❌ | $$$ |
| OpenAI | ✅ | ✅ | ❌ | $$$ |
| Ollama | ✅ | ✅ | ✅ | Free |
| Gemini | ✅ | ✅ | ❌ | $$ |
| Mistral | ✅ | ✅ | ❌ | $$ |
| Cohere | ✅ | ✅ | ❌ | $$ |

---

## Tool System

PyCode provides **15 powerful tools** for code manipulation:

### File Operations

**write** - Create new files
```python
{
    "file_path": "/path/to/file.py",
    "content": "print('Hello, World!')"
}
```

**read** - Read file contents
```python
{
    "file_path": "/path/to/file.py",
    "offset": 0,      # Optional: start line
    "limit": 100      # Optional: max lines
}
```

**edit** - Modify files
```python
{
    "file_path": "/path/to/file.py",
    "old_string": "old code",
    "new_string": "new code"
}
```

**multiedit** - Multiple edits at once
```python
{
    "file_path": "/path/to/file.py",
    "edits": [
        {"old_string": "...", "new_string": "..."},
        {"old_string": "...", "new_string": "..."}
    ]
}
```

### Code Search

**grep** - Search code by pattern
```python
{
    "pattern": "def.*test",
    "path": "tests/",
    "case_sensitive": False,
    "context_lines": 3
}
```

**glob** - Find files by pattern
```python
{
    "pattern": "**/*.py",
    "path": "src/"
}
```

### Execution

**bash** - Run shell commands
```python
{
    "command": "python script.py",
    "working_directory": "/path/to/project"
}
```

**python** - Execute Python code
```python
{
    "code": "print(2 + 2)",
    "timeout": 30
}
```

### Version Control

**git** - Git operations
```python
{
    "command": "status",
    "args": []
}
```

Supported commands: status, add, commit, push, pull, diff, log

### Utility Tools

**ls** - List directory contents
**pwd** - Get current directory
**snapshot** - Save project state
**restore** - Restore from snapshot
**diff** - Compare files
**tree** - Directory structure

---

## Interactive Features

### Tool Approval System

Interactive approval for risky operations:

```python
config = RunConfig(
    auto_approve_tools=False,      # Require approval
    auto_approve_destructive=False # Extra confirmation for dangerous ops
)
```

**Risk Levels**:
- 🟢 **Low**: read, grep, glob (auto-approved)
- 🟡 **Medium**: write, edit, git (interactive prompt)
- 🔴 **High**: bash with dangerous commands (warning + confirmation)

**Approval Options**:
- `y` - Approve once
- `n` - Deny once
- `a` - Always approve this tool
- `d` - Always deny this tool
- `s` - Approve this specific call (remembers exact arguments)

**Example**:
```
🔧 Tool Request: bash

Risk Level: HIGH

Arguments:
  command: rm -rf /tmp/cache

⚠️  WARNING: This is a potentially destructive operation!

Options:
  [y] Approve once
  [n] Deny once
  [a] Always approve this tool
  [d] Always deny this tool
  [s] Approve this specific call

Approve [y/n/a/d/s]:
```

### Dangerous Pattern Detection

Automatically flags dangerous operations:
- `rm -rf` - Recursive deletion
- `dd if=` - Disk operations
- `mkfs` - Filesystem formatting
- `sudo` - Elevated privileges
- `curl | bash` - Pipe to shell
- System directory access (`/bin`, `/etc`, etc.)

---

## Terminal UI

PyCode features a **beautiful Rich-based terminal UI**:

### Features

✨ **Formatted Panels**
- Session headers with metadata
- Tool execution displays
- Result panels

🎨 **Syntax Highlighting**
- Automatic language detection
- Code output with line numbers
- Monokai theme

📊 **Progress Indicators**
- Spinners for indeterminate tasks
- Progress bars for long operations
- Real-time status updates

🎯 **Color Coding**
- Green: Success
- Red: Errors
- Yellow: Warnings
- Blue: Information
- Cyan: Tools

### Example Output

```
╭────────────────────────── 🚀 PyCode Session Started ───────────────────────────╮
│                                                                                 │
│ Agent: BuildAgent                                                               │
│ Available Tools: 15                                                             │
│ Request: Create a fibonacci calculator                                         │
│                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────╯

────────────────────────────────────────────────────────────────
Iteration 1
────────────────────────────────────────────────────────────────

🔧 LLM requested 1 tool call(s)

╭─────────────────────── 🔧 Executing Tool ───────────────────────╮
│                                                                  │
│ Tool      write                                                  │
│   file_path /tmp/fibonacci.py                                    │
│   content def fibonacci(n):...                                   │
│                                                                  │
╰──────────────────────────────────────────────────────────────────╯

✅ File written successfully
   Created /tmp/fibonacci.py (237 bytes)

╭──────────────────────── Code ─────────────────────────╮
│ 1  def fibonacci(n):                                   │
│ 2      '''Calculate nth fibonacci number'''           │
│ 3      if n <= 1:                                      │
│ 4          return n                                    │
│ 5      return fibonacci(n-1) + fibonacci(n-2)          │
╰────────────────────────────────────────────────────────╯
```

### UI Components

```python
from pycode.ui import get_ui

ui = get_ui(verbose=True)

# Print formatted code
ui.print_code(code, language="python", title="Implementation")

# Show markdown
ui.print_markdown("# Success\n\nTask completed!")

# Display table
ui.print_table(
    title="Results",
    headers=["File", "Lines", "Status"],
    rows=[["script.py", "42", "✅"]]
)

# Progress bar
with ui.create_progress("Processing...") as progress:
    task = progress.add_task("Working", total=100)
    for i in range(100):
        progress.update(task, advance=1)

# Spinner
ui.start_spinner("Analyzing...")
await long_operation()
ui.stop_spinner()
ui.print_status("✅ Complete!", style="green")
```

---

## Safety & Security

### Built-in Protections

1. **Tool Approval**: Interactive confirmation for risky operations
2. **Dangerous Pattern Detection**: Flags unsafe commands
3. **Doom Loop Prevention**: Stops infinite execution
4. **Sandboxing**: Isolated execution environments (configurable)
5. **Rate Limiting**: Configurable max iterations
6. **Session Isolation**: Separate working directories

### Best Practices

```python
# Recommended configuration
config = RunConfig(
    max_iterations=50,                 # Prevent runaway execution
    auto_approve_tools=False,          # Review tool calls
    auto_approve_destructive=False,    # Extra confirmation
    doom_loop_detection=True,          # Detect loops
    doom_loop_threshold=3              # Trigger early
)
```

### Security Tips

- ✅ Use read-only mode for code exploration
- ✅ Review tool calls before approval
- ✅ Use local models (Ollama) for sensitive code
- ✅ Enable doom loop detection
- ✅ Set reasonable iteration limits
- ❌ Don't auto-approve destructive operations
- ❌ Don't disable safety features in production

---

## Configuration

### Via Code

```python
from pycode.config import PyCodeConfig, ModelConfig

config = PyCodeConfig(
    default_model=ModelConfig(
        provider="anthropic",
        model="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=8192
    ),
    auto_approve_tools=False,
    max_iterations=50,
    storage_dir="~/.pycode",
    verbose=True
)
```

### Via YAML

```yaml
# .pycode.yaml
default_model:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  temperature: 0.7
  max_tokens: 8192

auto_approve_tools: false
max_iterations: 50
storage_dir: ~/.pycode
verbose: true

providers:
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
  ollama:
    base_url: http://localhost:11434
```

### Environment Variables

```bash
# Provider API keys
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="..."
export MISTRAL_API_KEY="..."
export COHERE_API_KEY="..."

# PyCode settings
export PYCODE_STORAGE_DIR="~/.pycode"
export PYCODE_MAX_ITERATIONS="50"
export PYCODE_VERBOSE="true"
```

---

## Examples

### Example 1: Build a Web Server

```python
async def build_web_server():
    runner = AgentRunner(...)

    async for chunk in runner.run("""
Create a Flask web server with the following:
1. A homepage that displays 'Hello, World!'
2. An API endpoint /api/time that returns current time
3. Proper error handling
4. Save it as server.py and test it
"""):
        print(chunk, end="", flush=True)
```

### Example 2: Analyze Code

```python
async def analyze_codebase():
    runner = AgentRunner(...)

    async for chunk in runner.run("""
Analyze the codebase in ./src:
1. Count total lines of code
2. Find all TODO comments
3. Identify potential bugs
4. Suggest improvements
5. Generate a report
"""):
        print(chunk, end="", flush=True)
```

### Example 3: Refactor Code

```python
async def refactor_code():
    runner = AgentRunner(...)

    async for chunk in runner.run("""
Refactor the legacy_code.py file:
1. Add type hints
2. Improve variable names
3. Extract functions from long methods
4. Add docstrings
5. Ensure all tests still pass
"""):
        print(chunk, end="", flush=True)
```

### Example 4: Local Development (Ollama)

```python
from pycode.providers import OllamaProvider

# Use local models - no API costs!
provider = OllamaProvider(ProviderConfig(
    name="ollama",
    base_url="http://localhost:11434"
))

runner = AgentRunner(
    session=session,
    agent=BuildAgent(),
    provider=provider,
    registry=ToolRegistry()
)

async for chunk in runner.run("Create a calculator"):
    print(chunk)
```

---

## Advanced Features

### Custom Tools

Create your own tools:

```python
from pycode.tools import Tool, ToolContext, ToolResult

class MyTool(Tool):
    name = "my_tool"
    description = "Does something useful"
    parameters_schema = {
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        },
        "required": ["input"]
    }

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        # Your implementation
        return ToolResult(
            title="Success",
            output="Result",
            error=None
        )

# Register it
registry = ToolRegistry()
registry.register(MyTool())
```

### Custom Agents

```python
from pycode.agents import Agent

class MyAgent(Agent):
    name = "my_agent"
    description = "Custom agent"

    async def get_system_prompt(self) -> str:
        return """You are a specialized agent for..."""

    def can_use_tool(self, tool_name: str) -> bool:
        # Define which tools this agent can use
        return tool_name in ["read", "write", "bash"]
```

### Message History

```python
from pycode.history import MessageHistory

history = MessageHistory(storage)

# Get conversation
messages = await history.get_conversation_for_llm(
    session_id="session-123",
    max_messages=20
)

# Save message
await history.save_message(session_id, message)
```

---

## Performance Tips

1. **Use Ollama for development**: Free, fast, local
2. **Enable context windowing**: Keep conversations manageable
3. **Set reasonable iteration limits**: Prevent runaway costs
4. **Use appropriate models**: Small models for simple tasks
5. **Batch operations**: Use multiedit instead of multiple edits

---

## Troubleshooting

### Provider Issues

**Anthropic API errors**:
```bash
# Check API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Test connection
python -c "import anthropic; print(anthropic.Anthropic().messages.create(...))"
```

**Ollama not responding**:
```bash
# Check Ollama is running
ollama list

# Start Ollama
ollama serve

# Pull a model
ollama pull llama3.2
```

### Tool Execution Errors

**Permission denied**:
- Check file permissions
- Ensure working directory is writable
- Review tool approval settings

**Timeout errors**:
- Increase timeout in config
- Use async operations
- Check system resources

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**PyCode** - Vibe Coding in Python! 🚀

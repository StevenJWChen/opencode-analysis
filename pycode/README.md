# PyCode - AI Coding Agent in Python

A Python implementation of an AI coding agent inspired by OpenCode, featuring **6 LLM providers**, **15 powerful tools**, **interactive tool approval**, and a **beautiful terminal UI**.

## ✨ Key Features

- 🤖 **Vibe Coding** - Complete write-run-fix iterative workflow
- 🌐 **6 LLM Providers** - Anthropic, OpenAI, Ollama (local!), Gemini, Mistral, Cohere
- 🔧 **15 Tools** - File ops, code search, execution, git, and more
- 🎨 **Rich Terminal UI** - Beautiful formatted output with syntax highlighting
- 🛡️ **Interactive Approval** - Review and approve risky operations
- 🔄 **Doom Loop Detection** - Automatic infinite loop prevention
- 💾 **Session Management** - Persistent conversations with context
- ⚡ **Async/Streaming** - Real-time LLM responses
- 🔓 **100% Local Option** - Run completely offline with Ollama

## Installation

```bash
# Install from source
cd pycode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## 🚀 Quick Start

### Basic Usage

```bash
# Start interactive session
pycode

# Run with a message
pycode run "Create a fibonacci calculator"

# Use specific agent
pycode --agent build "Create a web server"

# Use local models (Ollama)
pycode --provider ollama "Analyze this code"
```

### Python API

```python
from pycode import AgentRunner, BuildAgent, RunConfig
from pycode.providers import AnthropicProvider, ProviderConfig
from pycode.tools import ToolRegistry
from pycode.core import Session

# Setup
session = Session(directory="./project")
provider = AnthropicProvider(ProviderConfig(
    name="anthropic",
    api_key="your-api-key"
))

runner = AgentRunner(
    session=session,
    agent=BuildAgent(),
    provider=provider,
    registry=ToolRegistry(),
    config=RunConfig(auto_approve_tools=False)  # Interactive approval
)

# Run with streaming
async for chunk in runner.run("Create a calculator"):
    print(chunk, end="", flush=True)
```

### Local Development (No API Keys!)

```python
from pycode.providers import OllamaProvider

# Use Ollama - 100% free and local!
provider = OllamaProvider(ProviderConfig(
    name="ollama",
    base_url="http://localhost:11434"
))

# No API costs, complete privacy
async for chunk in runner.run("Build a todo app"):
    print(chunk)
```

See [FEATURES.md](FEATURES.md) for comprehensive feature documentation.

## Configuration

Create `~/.pycode/config.yaml`:

```yaml
providers:
  anthropic:
    api_key: "your-key"
  openai:
    api_key: "your-key"

default_model:
  provider: anthropic
  model: claude-3-7-sonnet-20250219

agents:
  build:
    permissions:
      edit: allow
      bash:
        "*": allow

  plan:
    permissions:
      edit: deny
      bash:
        "ls*": allow
        "grep*": allow
        "*": ask
```

## Architecture

```
pycode/
├── src/
│   └── pycode/
│       ├── core/           # Core data structures
│       │   ├── session.py
│       │   ├── message.py
│       │   └── identifier.py
│       ├── agents/         # Agent system
│       │   ├── base.py
│       │   ├── build.py
│       │   └── plan.py
│       ├── tools/          # Tool implementations
│       │   ├── base.py
│       │   ├── bash.py
│       │   ├── edit.py
│       │   └── read.py
│       ├── providers/      # LLM providers
│       │   ├── base.py
│       │   ├── anthropic.py
│       │   └── openai.py
│       ├── storage/        # Persistence
│       │   └── store.py
│       └── cli/            # Command-line interface
│           └── main.py
└── tests/
```

## Development

```bash
# Run tests
pytest

# Format code
black src/

# Lint
ruff check src/

# Type check
mypy src/
```

## 📊 Comparison with OpenCode

| Feature | OpenCode | PyCode |
|---------|----------|--------|
| **Language** | TypeScript/Bun | Python 3.10+ |
| **Runtime** | Bun/Node.js | Python |
| **UI** | SolidJS TUI | Rich TUI ✨ |
| **AI SDK** | Vercel AI SDK | Native provider SDKs |
| **Validation** | Zod | Pydantic |
| **Async** | async/await | asyncio |
| **Tools** | 20+ | 15 tools ✅ |
| **Providers** | 15+ | 6 providers (40%) ✅ |
| **Local Models** | ❌ | ✅ Ollama |
| **Tool Approval** | ❌ | ✅ Interactive |
| **Doom Loop Detection** | ✅ | ✅ |
| **Syntax Highlighting** | ❌ | ✅ |
| **Progress Indicators** | ❌ | ✅ |

### Provider Coverage

| Provider | OpenCode | PyCode |
|----------|----------|--------|
| Anthropic (Claude) | ✅ | ✅ |
| OpenAI (GPT) | ✅ | ✅ |
| Ollama (Local) | ❌ | ✅ |
| Google (Gemini) | ✅ | ✅ |
| Mistral | ✅ | ✅ |
| Cohere | ✅ | ✅ |
| DeepSeek | ✅ | ⏳ Planned |
| LocalAI | ✅ | ⏳ Planned |
| Azure OpenAI | ✅ | ⏳ Planned |

See [PYCODE_VS_OPENCODE_V2.md](PYCODE_VS_OPENCODE_V2.md) for detailed comparison.

## License

MIT

## Credits

Inspired by [OpenCode](https://github.com/sst/opencode) - The open source AI coding agent.

## Platform Support

PyCode works on:
- ✅ **Windows** 10/11 (PowerShell, CMD, Git Bash)
- ✅ **macOS** 10.15+ (Catalina and later)
- ✅ **Linux** (Ubuntu, Debian, Fedora, etc.)

See [WINDOWS_COMPATIBILITY.md](WINDOWS_COMPATIBILITY.md) for Windows-specific setup.

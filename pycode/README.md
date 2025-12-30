# PyCode - AI Coding Agent in Python

A Python implementation of an AI coding agent inspired by OpenCode, featuring multi-provider support, agent-based permissions, and extensible tool system.

## Features

- 🤖 **Multi-Agent System** - Build, Plan, and specialized agents
- 🔧 **Extensible Tools** - Bash, file editing, code search, and more
- 🌐 **Multi-Provider** - Anthropic Claude, OpenAI, and more
- 🔐 **Permission System** - Fine-grained control over agent actions
- 💾 **Session Management** - Persistent conversations with context
- 🎨 **Rich TUI** - Beautiful terminal interface with Rich
- ⚡ **Async/Streaming** - Real-time LLM responses

## Installation

```bash
# Install from source
cd pycode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Start interactive session
pycode

# Run with a message
pycode run "Help me refactor this code"

# Use specific agent
pycode --agent plan "Analyze the codebase"

# Use specific model
pycode --model anthropic/claude-3-7-sonnet
```

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

## Comparison with OpenCode

| Feature | OpenCode | PyCode |
|---------|----------|--------|
| **Language** | TypeScript/Bun | Python 3.10+ |
| **Runtime** | Bun/Node.js | Python |
| **UI** | SolidJS TUI | Rich TUI |
| **AI SDK** | Vercel AI SDK | Native provider SDKs |
| **Validation** | Zod | Pydantic |
| **Async** | async/await | asyncio |
| **Tools** | 20+ | Core subset |
| **Providers** | 15+ | Anthropic, OpenAI |

## License

MIT

## Credits

Inspired by [OpenCode](https://github.com/sst/opencode) - The open source AI coding agent.

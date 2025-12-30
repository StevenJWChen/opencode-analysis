# Ollama CLI Quick Start

Get started with PyCode and Ollama in 5 minutes!

## Step 1: Install and Start Ollama

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve
```

## Step 2: Pull a Model

```bash
# Pull llama3.2 (recommended, fast and capable)
ollama pull llama3.2

# Or try other models:
ollama pull codellama       # For coding tasks
ollama pull qwen2.5-coder   # Another code model
```

## Step 3: Configure PyCode (Optional)

Create `~/.pycode/config.yaml`:

```yaml
default_model:
  provider: ollama
  model_id: llama3.2:latest

providers:
  ollama:
    base_url: http://localhost:11434
```

## Step 4: Use PyCode CLI

```bash
# Basic usage (uses config defaults if set)
pycode run "Create a Python hello world script"

# Or specify model explicitly
pycode run "Create a Python hello world script" --model llama3.2

# Or specify provider and model
pycode run "Create a Python hello world script" --provider ollama --model llama3.2
```

## Common Commands

### Create Code
```bash
pycode run "Create a Flask REST API with CRUD operations" --model codellama
```

### Fix Bugs
```bash
pycode run "Fix the bug in main.py" --model llama3.2
```

### Refactor
```bash
pycode run "Refactor utils.py to add type hints" --model qwen2.5-coder
```

### Interactive Mode
```bash
pycode repl --model llama3.2

# Then interact:
> Create a test file
> Read it
> Modify it
> exit
```

## Verbosity Levels

```bash
# Quiet (errors only)
pycode run "request" --model llama3.2 --log-level quiet

# Normal (default)
pycode run "request" --model llama3.2

# Verbose (more details)
pycode run "request" --model llama3.2 --log-level verbose

# Debug (everything)
pycode run "request" --model llama3.2 --log-level debug
```

## Check Status

```bash
# List available models
pycode models

# List providers
pycode providers

# Show configuration
pycode config show

# Check Ollama is running
curl http://localhost:11434/api/version
```

## Troubleshooting

### "Connection refused"
```bash
# Start Ollama
ollama serve
```

### "Model not found"
```bash
# Pull the model
ollama pull llama3.2
```

### "Timeout"
```bash
# Use smaller model or increase timeout in config
providers:
  ollama:
    timeout: 300  # 5 minutes
```

## Next Steps

- See full documentation: `OLLAMA_USAGE.md`
- Try the Python example: `python quick_ollama_example.py`
- Explore features: `FEATURES.md`

## Model Recommendations

| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| llama3.2 | 3B | Fast ⚡⚡⚡ | General tasks, quick responses |
| codellama | 7B | Medium ⚡⚡ | Coding tasks |
| qwen2.5-coder | 7B | Medium ⚡⚡ | Code generation & refactoring |
| llama3.3 | 70B | Slow ⚡ | Complex reasoning, large projects |

Happy coding with PyCode + Ollama! 🦙

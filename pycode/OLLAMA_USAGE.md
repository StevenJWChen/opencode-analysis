# Using PyCode with Ollama

This guide shows you how to use PyCode with Ollama for local LLM models.

## Prerequisites

### 1. Install Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Or download from https://ollama.com/download
```

### 2. Start Ollama Service

```bash
# Start the Ollama service
ollama serve

# Or if already running as a service, check status
curl http://localhost:11434/api/version
```

### 3. Pull a Model

```bash
# Pull a recommended model (fast and capable)
ollama pull llama3.2

# Or other models:
ollama pull codellama        # Code-specialized
ollama pull qwen2.5-coder    # Another code model
ollama pull mistral          # General purpose
ollama pull llama3.3         # Larger, more capable

# List available models
ollama list
```

---

## Configuration

### Option 1: Using Config File (Recommended)

Create or edit `~/.pycode/config.yaml`:

```yaml
# Default model to use
default_model:
  provider: ollama
  model_id: llama3.2:latest
  temperature: 0.7
  max_tokens: 4096

# Provider configurations
providers:
  ollama:
    base_url: http://localhost:11434  # Default Ollama URL
    timeout: 120  # Longer timeout for local models

# Runtime settings
runtime:
  max_iterations: 10
  auto_approve_tools: false  # Recommend false for safety
  doom_loop_threshold: 3
  log_level: normal  # Options: quiet, normal, verbose, debug
```

### Option 2: Using Environment Variables

```bash
# Set Ollama base URL (optional, defaults to localhost:11434)
export OLLAMA_BASE_URL=http://localhost:11434

# Or in config.yaml, use environment variable substitution
providers:
  ollama:
    base_url: ${OLLAMA_BASE_URL:http://localhost:11434}
```

### Option 3: Using CLI Arguments

```bash
# Specify provider and model directly in CLI
pycode run "your request" --provider ollama --model llama3.2

# Or use friendly aliases
pycode run "your request" --model llama3.2  # Auto-detects ollama
```

---

## Using PyCode with Ollama

### Basic Usage

```bash
# Using config file defaults (if set to ollama)
pycode run "Create a Python script that prints hello world"

# Explicitly specify Ollama
pycode run "Create a Python script that prints hello world" --provider ollama --model llama3.2

# Using model alias (auto-detects provider)
pycode run "Create a Python script that prints hello world" --model llama3.2
```

### With Different Models

```bash
# Use CodeLlama for coding tasks
pycode run "Write a function to parse JSON" --model codellama

# Use Qwen2.5-Coder for code
pycode run "Refactor this code" --model qwen2.5-coder

# Use Mistral for general tasks
pycode run "Explain this algorithm" --model mistral
```

### With Verbosity Control

```bash
# Quiet mode (errors only)
pycode run "your request" --model llama3.2 --log-level quiet

# Normal mode (default)
pycode run "your request" --model llama3.2

# Verbose mode (more details)
pycode run "your request" --model llama3.2 --log-level verbose

# Debug mode (everything)
pycode run "your request" --model llama3.2 --log-level debug
```

### Interactive REPL Mode

```bash
# Start REPL with Ollama
pycode repl --model llama3.2

# In REPL:
> Create a test file
> Read the file
> Modify it
> exit
```

---

## Model Aliases

PyCode supports friendly aliases for Ollama models:

```bash
# These are equivalent:
pycode run "request" --model llama3.2
pycode run "request" --provider ollama --model llama3.2:latest

# Model aliases:
pycode run "request" --model codellama      # → ollama/codellama:latest
pycode run "request" --model llama3.3       # → ollama/llama3.3:latest
pycode run "request" --model qwen2.5-coder  # → ollama/qwen2.5-coder:latest
```

---

## Example Sessions

### Example 1: Create a Python Script

```bash
$ pycode run "Create a Python script that fetches weather data" --model llama3.2

# PyCode will:
# 1. Use Ollama's llama3.2 model
# 2. Generate the code
# 3. Write it to a file
# 4. Show you the result
```

### Example 2: Debug and Fix Code

```bash
$ pycode run "Fix the bug in main.py" --model codellama

# PyCode will:
# 1. Read main.py
# 2. Analyze the code
# 3. Identify the bug
# 4. Fix it
# 5. Show the changes
```

### Example 3: Refactor Code

```bash
$ pycode run "Refactor utils.py to use type hints" --model qwen2.5-coder --log-level verbose

# With verbose logging, you'll see:
# - Model being used
# - Tools being called
# - Retry attempts (if any)
# - Detailed progress
```

### Example 4: Multi-step Task

```bash
$ pycode run "Create a REST API with Flask, add error handling, and write tests" --model llama3.3

# PyCode will iteratively:
# 1. Create the Flask app
# 2. Add error handling
# 3. Write tests
# 4. Run tests to verify
# 5. Fix any issues
```

---

## Python API Usage

### Basic Usage

```python
import asyncio
from pycode.providers.ollama_provider import OllamaProvider
from pycode.providers.base import ProviderConfig
from pycode.runner import AgentRunner, RunConfig
from pycode.agents import BuildAgent
from pycode.tools import ToolRegistry
from pycode.core import Session

async def main():
    # Configure Ollama provider
    config = ProviderConfig(
        base_url="http://localhost:11434",
        extra={"timeout": 120}
    )

    provider = OllamaProvider(config)

    # Create session and agent
    session = Session(
        id="test-session",
        project_id="test-project",
        directory="."
    )

    agent = BuildAgent()
    registry = ToolRegistry()

    run_config = RunConfig(
        verbose=True,
        max_iterations=10
    )

    runner = AgentRunner(
        session=session,
        agent=agent,
        provider=provider,
        registry=registry,
        config=run_config
    )

    # Run task
    async for chunk in runner.run("Create a hello world script"):
        print(chunk, end="", flush=True)

asyncio.run(main())
```

### Using Model Aliases

```python
from pycode.provider_aliases import resolve_model

# Resolve model alias
provider_name, model_id = resolve_model("llama3.2")
print(f"Using: {provider_name}/{model_id}")
# Output: Using: ollama/llama3.2:latest

# With provider prefix
provider_name, model_id = resolve_model("ollama/codellama")
print(f"Using: {provider_name}/{model_id}")
# Output: Using: ollama/codellama
```

---

## Performance Tips

### 1. Model Selection

- **llama3.2** (3B): Fast, good for simple tasks
- **llama3.3** (70B): Slower but more capable
- **codellama** (7B/13B/34B): Specialized for coding
- **qwen2.5-coder** (7B/32B): Excellent for code

### 2. Timeout Settings

Local models can be slower than APIs:

```yaml
providers:
  ollama:
    timeout: 180  # 3 minutes for larger models
```

### 3. Hardware Recommendations

- **Minimum**: 8GB RAM, CPU only (small models like llama3.2)
- **Recommended**: 16GB RAM, GPU (medium models like codellama)
- **Optimal**: 32GB+ RAM, GPU (large models like llama3.3)

### 4. GPU Acceleration

Ollama automatically uses GPU if available. Check:

```bash
ollama ps  # Shows running models and GPU usage
```

---

## Troubleshooting

### Ollama Not Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# If not, start it:
ollama serve
```

### Connection Refused

```bash
# Check Ollama is listening on the right port
netstat -an | grep 11434

# Or specify custom URL in config:
providers:
  ollama:
    base_url: http://localhost:11434
```

### Model Not Found

```bash
# List available models
ollama list

# Pull the model you need
ollama pull llama3.2
```

### Slow Performance

```bash
# Use smaller model
pycode run "request" --model llama3.2  # Faster

# Or increase timeout in config:
providers:
  ollama:
    timeout: 300  # 5 minutes
```

### Out of Memory

```bash
# Use smaller model
ollama pull llama3.2  # 3B parameters

# Or stop other Ollama models
ollama ps  # List running models
ollama stop <model_name>
```

---

## Retry and Logging

PyCode automatically handles failures with Ollama:

### Automatic Retry

- **Network errors**: Automatically retried 3 times
- **Connection timeouts**: Exponential backoff
- **Transient failures**: Recovered automatically

### Logging

```bash
# See retry attempts and debugging info
pycode run "request" --model llama3.2 --log-level debug

# Example output:
# [DEBUG] Streaming from Ollama model=llama3.2 base_url=http://localhost:11434
# [DEBUG] Waiting 1.0s before retry attempt=1 max_attempts=3
# [INFO] Successfully connected to Ollama
```

---

## Best Practices

1. **Start Ollama First**: Always ensure `ollama serve` is running
2. **Pull Models**: Download models before using: `ollama pull llama3.2`
3. **Use Appropriate Models**: Small models for simple tasks, large for complex
4. **Set Timeouts**: Local models need longer timeouts than APIs
5. **Monitor Resources**: Check GPU/RAM usage with `ollama ps`
6. **Use Auto-Approval Carefully**: Review tool executions for safety

---

## Advanced Configuration

### Custom Ollama Server

```yaml
providers:
  ollama:
    base_url: http://custom-server:11434
    timeout: 180
    extra:
      num_ctx: 4096      # Context window size
      num_predict: 2048  # Max tokens to generate
```

### Multiple Ollama Instances

```yaml
providers:
  ollama_local:
    base_url: http://localhost:11434

  ollama_remote:
    base_url: http://remote-server:11434
```

### Model-Specific Settings

```python
# In Python code
config = ProviderConfig(
    base_url="http://localhost:11434",
    extra={
        "timeout": 120,
        "temperature": 0.7,
        "top_p": 0.9,
        "num_ctx": 4096
    }
)
```

---

## Examples

See the complete examples in:
- `demo_ollama.py` - Full demo with Ollama
- `examples/ollama_example.py` - Basic usage
- `OLLAMA_SETUP.md` - Detailed setup guide

---

## Getting Help

```bash
# View CLI help
pycode --help
pycode run --help

# List available models
pycode models

# List providers
pycode providers

# Check configuration
pycode config show
```

For more information, see:
- [QUICKSTART.md](./QUICKSTART.md)
- [FEATURES.md](./FEATURES.md)
- [OLLAMA_SETUP.md](./OLLAMA_SETUP.md)

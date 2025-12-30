# Ollama Setup Guide

Run PyCode with **local models** - no API keys, no internet, no costs!

---

## 🚀 Quick Start

### 1. Install Ollama

**macOS / Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from https://ollama.ai/download

**Manual Install:**
Visit https://ollama.ai/download for your platform

### 2. Start Ollama

```bash
ollama serve
```

Leave this running in a terminal.

### 3. Pull a Model

```bash
# Recommended: Fast and capable
ollama pull llama3.2

# Alternative models
ollama pull mistral        # Good alternative
ollama pull codellama      # Code-focused
ollama pull llama3.2:70b   # Larger, better (requires more RAM)
```

### 4. Run PyCode with Ollama

```bash
cd pycode
python demo_ollama.py
```

---

## 📚 Available Models

### Recommended for Vibe Coding

| Model | Size | RAM | Speed | Quality | Best For |
|-------|------|-----|-------|---------|----------|
| **llama3.2** | 3GB | 8GB | ⚡⚡⚡ | ⭐⭐⭐ | General coding |
| **codellama** | 4GB | 8GB | ⚡⚡ | ⭐⭐⭐⭐ | Code generation |
| **mistral** | 4GB | 8GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | General purpose |
| **llama3.2:70b** | 40GB | 64GB | ⚡ | ⭐⭐⭐⭐⭐ | Best quality |

### Pull Models

```bash
# See available models
ollama list

# Pull a model
ollama pull <model-name>

# Remove a model
ollama rm <model-name>
```

---

## 🔧 Configuration

### Option 1: Use in Code

```python
from pycode.providers import OllamaProvider, ProviderConfig

config = ProviderConfig(
    base_url="http://localhost:11434",
    model="llama3.2"
)
provider = OllamaProvider(config)
```

### Option 2: YAML Configuration

Edit `~/.pycode/config.yaml`:

```yaml
default_model:
  provider: ollama
  model_id: llama3.2
  temperature: 0.7
  max_tokens: 4096

providers:
  ollama:
    base_url: http://localhost:11434
    timeout: 120

agents:
  build:
    model:
      provider: ollama
      model_id: llama3.2
```

### Option 3: CLI

```bash
# Use Ollama with CLI
python pycode_cli.py run --provider ollama --model llama3.2 "Write a web server"
```

---

## 🎯 Usage Examples

### Example 1: Basic Streaming

```python
import asyncio
from pycode.providers import OllamaProvider, ProviderConfig

async def main():
    config = ProviderConfig(base_url="http://localhost:11434")
    provider = OllamaProvider(config)

    print("Response: ", end="", flush=True)

    async for event in provider.stream(
        model="llama3.2",
        messages=[{"role": "user", "content": "Explain Python generators"}],
    ):
        if event.type == "text_delta":
            print(event.data.get("text", ""), end="", flush=True)

    await provider.close()

asyncio.run(main())
```

### Example 2: Vibe Coding

```python
import asyncio
from pycode.providers import OllamaProvider, ProviderConfig
from pycode.core import Session
from pycode.agents import BuildAgent
from pycode.tools import ToolRegistry, WriteTool, BashTool
from pycode.runner import AgentRunner, RunConfig
from pycode.storage import Storage

async def main():
    # Setup
    session = Session(project_id="my-project", directory="/tmp")
    agent = BuildAgent()

    # Use Ollama
    config = ProviderConfig(base_url="http://localhost:11434")
    provider = OllamaProvider(config)

    # Setup tools
    registry = ToolRegistry()
    registry.register(WriteTool())
    registry.register(BashTool())

    # Create runner
    runner = AgentRunner(
        session=session,
        agent=agent,
        provider=provider,
        registry=registry,
        config=RunConfig(max_iterations=5, auto_approve_tools=True),
        storage=Storage(),
    )

    # Run!
    async for chunk in runner.run("Create a Python web server with Flask"):
        print(chunk, end="", flush=True)

    await provider.close()

asyncio.run(main())
```

### Example 3: Function Calling

```python
async def demo_function_calling():
    config = ProviderConfig(base_url="http://localhost:11434")
    provider = OllamaProvider(config)

    tools = [{
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform math calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                }
            }
        }
    }]

    async for event in provider.stream(
        model="llama3.2",
        messages=[{"role": "user", "content": "Calculate 15 * 7"}],
        tools=tools,
    ):
        if event.type == "tool_use":
            print(f"Tool: {event.data['name']}")
            print(f"Args: {event.data['arguments']}")

    await provider.close()
```

---

## 🔍 Troubleshooting

### "Cannot connect to Ollama"

**Problem:** PyCode can't reach Ollama

**Solutions:**
1. Make sure Ollama is running:
   ```bash
   ollama serve
   ```

2. Check if it's accessible:
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. Verify port (default: 11434):
   ```python
   config = ProviderConfig(base_url="http://localhost:11434")
   ```

### "No models found"

**Problem:** Ollama is running but no models installed

**Solution:**
```bash
# Install a model
ollama pull llama3.2

# Verify
ollama list
```

### Slow Responses

**Problem:** Model is slow to respond

**Solutions:**
1. Use a smaller model:
   ```bash
   ollama pull llama3.2  # Instead of llama3.2:70b
   ```

2. Check system resources (CPU/RAM usage)

3. Try a different model:
   ```bash
   ollama pull mistral
   ```

### Out of Memory

**Problem:** System runs out of RAM

**Solutions:**
1. Use a smaller model
2. Close other applications
3. Check model requirements:
   - llama3.2: 8GB RAM
   - llama3.2:70b: 64GB RAM

### Poor Quality Responses

**Problem:** Model gives low-quality answers

**Solutions:**
1. Try a larger model:
   ```bash
   ollama pull llama3.2:70b
   ```

2. Adjust temperature:
   ```python
   async for event in provider.stream(
       model="llama3.2",
       temperature=0.3,  # Lower = more focused
       ...
   )
   ```

3. Use a specialized model:
   ```bash
   ollama pull codellama  # For code
   ```

---

## 🎓 Model Comparison

### Performance vs Quality Trade-off

**Fast & Light (3-4GB):**
- llama3.2
- mistral
- ⚡⚡⚡ Speed
- ⭐⭐⭐ Quality
- 💻 8GB RAM

**Balanced (7-8GB):**
- codellama
- mistral:7b
- ⚡⚡ Speed
- ⭐⭐⭐⭐ Quality
- 💻 16GB RAM

**Best Quality (40GB+):**
- llama3.2:70b
- codellama:70b
- ⚡ Speed
- ⭐⭐⭐⭐⭐ Quality
- 💻 64GB RAM

### Specialized Models

**Code Generation:**
```bash
ollama pull codellama      # Best for code
ollama pull codellama:7b   # Balanced
ollama pull codellama:70b  # Highest quality
```

**General Purpose:**
```bash
ollama pull llama3.2       # Fast
ollama pull mistral        # Good balance
ollama pull llama3.2:70b   # Best
```

---

## 💡 Best Practices

### 1. **Choose the Right Model**
- Development: llama3.2 (fast iteration)
- Production: llama3.2:70b (best quality)
- Code tasks: codellama

### 2. **Manage Resources**
- Run one model at a time
- Monitor RAM usage
- Keep models you use frequently

### 3. **Optimize Performance**
- Use appropriate temperature (0.3-0.7 for code)
- Set reasonable max_tokens
- Enable streaming for better UX

### 4. **Model Management**
```bash
# List installed models
ollama list

# Remove unused models
ollama rm old-model

# Update models
ollama pull model-name
```

---

## 🆚 Ollama vs Cloud APIs

| Feature | Ollama | Cloud APIs |
|---------|--------|------------|
| **Cost** | Free | $$ per token |
| **Privacy** | 100% local | Data sent to servers |
| **Internet** | Not required | Required |
| **Speed** | Depends on hardware | Generally fast |
| **Quality** | Good-Excellent | Excellent |
| **Setup** | One-time install | API key needed |

### When to Use Ollama:
- ✅ Privacy is important
- ✅ No internet available
- ✅ High usage (no per-token costs)
- ✅ Learning and experimentation
- ✅ Sufficient local resources

### When to Use Cloud APIs:
- ✅ Need absolute best quality
- ✅ Limited local resources
- ✅ Occasional use
- ✅ Need specific models (GPT-4, Claude)

---

## 🎉 Benefits of Ollama

### 1. **No API Costs**
Run unlimited requests for free!

### 2. **Complete Privacy**
Your code never leaves your machine.

### 3. **Offline Capable**
Work without internet connection.

### 4. **Fast Iteration**
No rate limits, experiment freely.

### 5. **Learn ML**
Understand how models work locally.

---

## 📖 Additional Resources

- **Ollama Website:** https://ollama.ai
- **Ollama GitHub:** https://github.com/ollama/ollama
- **Model Library:** https://ollama.ai/library
- **Ollama Discord:** https://discord.gg/ollama

---

## 🚀 Next Steps

1. **Try the demo:**
   ```bash
   python demo_ollama.py
   ```

2. **Use in your projects:**
   ```python
   from pycode.providers import OllamaProvider
   ```

3. **Experiment with models:**
   ```bash
   ollama pull mistral
   ollama pull codellama
   ```

4. **Configure PyCode:**
   Edit `~/.pycode/config.yaml` to use Ollama by default

5. **Share your experience:**
   Let us know how Ollama works for you!

---

**Enjoy local, private, cost-free vibe coding with Ollama! 🎉**

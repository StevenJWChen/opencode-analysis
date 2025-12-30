# Provider Configuration Guide

PyCode supports multiple LLM providers through a unified configuration system. Switch between providers by simply updating your configuration file - no code changes needed!

## Table of Contents

- [Quick Start](#quick-start)
- [Supported Providers](#supported-providers)
- [Configuration File](#configuration-file)
- [Provider-Specific Setup](#provider-specific-setup)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Quick Start

1. **Copy the example configuration:**
   ```bash
   cp pycode.yaml.example pycode.yaml
   ```

2. **Edit `pycode.yaml`** and configure your preferred provider

3. **Set API keys** (if needed) as environment variables

4. **Run any PyCode program** - it will automatically use your configuration!
   ```bash
   python quick_start_example.py
   ```

## Supported Providers

| Provider | Type | Cost | Privacy | Setup Difficulty |
|----------|------|------|---------|------------------|
| **Ollama** | Local | Free | Complete | Easy |
| **Anthropic (Claude)** | Cloud API | Pay-per-use | Data sent to API | Easy |
| **OpenAI (GPT)** | Cloud API | Pay-per-use | Data sent to API | Easy |
| **Gemini (Google)** | Cloud API | Free tier available | Data sent to API | Easy |
| **Mistral** | Cloud API | Pay-per-use | Data sent to API | Easy |
| **Cohere** | Cloud API | Free tier available | Data sent to API | Easy |

## Configuration File

PyCode looks for configuration in these locations (in order):
1. `./pycode.yaml` (current directory)
2. `./.pycode.yaml` (current directory, hidden)
3. `~/.pycode/config.yaml` (user home directory)

### Configuration Structure

```yaml
# Default model to use
default_model:
  provider: anthropic  # Which provider to use
  model_id: claude-3-5-sonnet-20241022  # Which model
  temperature: 0.7
  max_tokens: 4096

# Provider settings (API keys, URLs, etc.)
providers:
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}  # Use environment variable
    timeout: 60

  ollama:
    base_url: http://localhost:11434
    timeout: 120

# Agent configurations
agents:
  build:
    model:
      provider: anthropic  # Can override per agent
      model_id: claude-3-5-sonnet-20241022
    enabled_tools:
      - write
      - read
      - edit
      - bash
```

## Provider-Specific Setup

### Ollama (Recommended for Local/Private Use)

**Advantages:**
- ✅ Completely free
- ✅ Runs locally - no internet needed
- ✅ Complete privacy - code never leaves your machine
- ✅ No API keys needed
- ✅ Fast inference on local hardware

**Setup:**

1. Install Ollama:
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.com/install.sh | sh

   # Windows: Download from https://ollama.com/download
   ```

2. Start Ollama:
   ```bash
   ollama serve
   ```

3. Pull a model:
   ```bash
   # Smaller, faster model (recommended for testing)
   ollama pull llama3.2

   # Larger, more capable model
   ollama pull llama3.2:70b

   # Code-optimized model
   ollama pull codellama
   ```

4. Configure PyCode:
   ```yaml
   default_model:
     provider: ollama
     model_id: llama3.2:latest
     temperature: 0.7
     max_tokens: 4096

   providers:
     ollama:
       base_url: http://localhost:11434
       timeout: 120
   ```

5. Run:
   ```bash
   python quick_ollama_example.py
   ```

### Anthropic (Claude)

**Advantages:**
- ✅ Excellent code understanding and generation
- ✅ Large context window
- ✅ High quality outputs

**Setup:**

1. Get API key from https://console.anthropic.com/

2. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

3. Configure PyCode:
   ```yaml
   default_model:
     provider: anthropic
     model_id: claude-3-5-sonnet-20241022
     temperature: 0.7
     max_tokens: 4096

   providers:
     anthropic:
       api_key: ${ANTHROPIC_API_KEY}
       timeout: 60
   ```

**Available Models:**
- `claude-3-5-sonnet-20241022` - Best balance of capability and speed
- `claude-3-opus-20240229` - Most capable, slower
- `claude-3-haiku-20240307` - Fast, efficient

### OpenAI (GPT)

**Setup:**

1. Get API key from https://platform.openai.com/

2. Set environment variable:
   ```bash
   export OPENAI_API_KEY=sk-...
   ```

3. Configure PyCode:
   ```yaml
   default_model:
     provider: openai
     model_id: gpt-4-turbo-preview
     temperature: 0.7
     max_tokens: 4096

   providers:
     openai:
       api_key: ${OPENAI_API_KEY}
       timeout: 60
   ```

**Available Models:**
- `gpt-4-turbo-preview` - Most capable
- `gpt-4` - Standard GPT-4
- `gpt-3.5-turbo` - Faster, cheaper

### Google Gemini

**Setup:**

1. Get API key from https://makersuite.google.com/app/apikey

2. Set environment variable:
   ```bash
   export GEMINI_API_KEY=...
   # or
   export GOOGLE_API_KEY=...
   ```

3. Configure PyCode:
   ```yaml
   default_model:
     provider: gemini
     model_id: gemini-pro
     temperature: 0.7
     max_tokens: 4096

   providers:
     gemini:
       api_key: ${GEMINI_API_KEY}
       timeout: 60
   ```

**Available Models:**
- `gemini-pro` - Standard model
- `gemini-pro-vision` - With vision capabilities

### Mistral

**Setup:**

1. Get API key from https://console.mistral.ai/

2. Set environment variable:
   ```bash
   export MISTRAL_API_KEY=...
   ```

3. Configure PyCode:
   ```yaml
   default_model:
     provider: mistral
     model_id: mistral-large-latest
     temperature: 0.7
     max_tokens: 4096

   providers:
     mistral:
       api_key: ${MISTRAL_API_KEY}
       timeout: 60
   ```

### Cohere

**Setup:**

1. Get API key from https://dashboard.cohere.com/

2. Set environment variable:
   ```bash
   export COHERE_API_KEY=...
   ```

3. Configure PyCode:
   ```yaml
   default_model:
     provider: cohere
     model_id: command-r-plus
     temperature: 0.7
     max_tokens: 4096

   providers:
     cohere:
       api_key: ${COHERE_API_KEY}
       timeout: 60
   ```

## Examples

### Example 1: Local Development with Ollama

Perfect for privacy-conscious development or working offline.

```yaml
default_model:
  provider: ollama
  model_id: llama3.2:latest
  temperature: 0.7
  max_tokens: 4096

providers:
  ollama:
    base_url: http://localhost:11434
    timeout: 120
```

### Example 2: Production with Claude

Best quality for production code generation.

```yaml
default_model:
  provider: anthropic
  model_id: claude-3-5-sonnet-20241022
  temperature: 0.7
  max_tokens: 4096

providers:
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    timeout: 60
```

### Example 3: Mixed Setup

Use different providers for different agents - local model for build, cloud for planning.

```yaml
default_model:
  provider: ollama
  model_id: codellama:latest

agents:
  build:
    model:
      provider: ollama
      model_id: codellama:latest  # Code-optimized local model

  plan:
    model:
      provider: anthropic
      model_id: claude-3-5-sonnet-20241022  # Cloud for planning

providers:
  ollama:
    base_url: http://localhost:11434
    timeout: 120
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    timeout: 60
```

### Example 4: Cost-Optimized

Use cheaper models where appropriate.

```yaml
default_model:
  provider: openai
  model_id: gpt-3.5-turbo  # Cheaper option
  temperature: 0.7
  max_tokens: 2048  # Lower token limit

providers:
  openai:
    api_key: ${OPENAI_API_KEY}
```

## Using in Your Code

### Method 1: Use the Configuration Directly

```python
from pycode.config import load_config
from pycode.provider_factory import ProviderFactory

# Load config
config = load_config()

# Create provider from config
provider = ProviderFactory.create_provider(
    provider_type=config.default_model.provider,
    model_config=config.default_model,
    provider_settings=config.providers.get(config.default_model.provider),
)

# Use the provider
async for event in provider.stream(
    model=config.default_model.model_id,
    messages=[{"role": "user", "content": "Hello!"}],
):
    print(event)
```

### Method 2: Quick Start Example

Just run the provided example - it handles everything:

```bash
python quick_start_example.py
```

## Troubleshooting

### "No configuration file found"

**Solution:** Copy the example config:
```bash
cp pycode.yaml.example pycode.yaml
```

### "API key not found"

**Solution:** Set the environment variable:
```bash
# For Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# For OpenAI
export OPENAI_API_KEY=sk-...

# For Gemini
export GEMINI_API_KEY=...
```

### "Cannot connect to Ollama"

**Solution:** Make sure Ollama is running:
```bash
# Start Ollama
ollama serve

# Verify it's running
curl http://localhost:11434/api/version

# Pull a model if needed
ollama pull llama3.2
```

### "Provider not supported"

**Supported providers:** anthropic, ollama, openai, gemini, mistral, cohere

Check your `pycode.yaml` and ensure the provider name is spelled correctly.

### "Model not found"

Different providers support different models. Check the provider-specific sections above for valid model IDs.

## Best Practices

1. **Start with Ollama** - Free, private, and easy to set up for testing
2. **Use environment variables** - Don't commit API keys to version control
3. **Set timeouts appropriately** - Local models (Ollama) need longer timeouts
4. **Test with small tasks first** - Verify your setup before complex operations
5. **Monitor costs** - Cloud providers charge per token
6. **Version control your config** - Commit `pycode.yaml.example`, not `pycode.yaml`

## Summary

PyCode's unified configuration system makes it easy to:
- ✅ Switch between providers without code changes
- ✅ Mix and match providers for different agents
- ✅ Keep API keys secure with environment variables
- ✅ Use local models for privacy
- ✅ Use cloud models for quality
- ✅ Optimize costs by choosing appropriate models

For more examples, see:
- `quick_start_example.py` - Works with any provider
- `quick_ollama_example.py` - Ollama-specific example
- `pycode.yaml.example` - Full configuration reference

# Getting an API Key for PyCode Vibe Coding Demo

## Quick Start: Anthropic (Claude) - FREE $5 Credits

### Step 1: Sign Up for Anthropic
1. Go to: https://console.anthropic.com/
2. Click "Sign Up"
3. Create account with email
4. Verify your email

### Step 2: Get Your API Key
1. Once logged in, go to: https://console.anthropic.com/settings/keys
2. Click "Create Key"
3. Give it a name (e.g., "PyCode Demo")
4. Copy the API key (starts with `sk-ant-`)

### Step 3: Set Up the API Key

**Option A: Environment Variable (Recommended)**
```bash
# Linux/Mac
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Windows CMD
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Option B: Create .env file**
```bash
cd /home/user/opencode-analysis/pycode
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env
```

### Step 4: Install Dependencies
```bash
pip install anthropic
```

### Step 5: Run the Demo!
```bash
python vibe_coding_demo.py
```

## Alternative: OpenAI (GPT)

If you prefer OpenAI:

1. Go to: https://platform.openai.com/signup
2. Get API key from: https://platform.openai.com/api-keys
3. New users get $5 free credits
4. Set: `export OPENAI_API_KEY="sk-your-key-here"`

Note: You'll need to modify the demo to use OpenAIProvider instead of AnthropicProvider.

## Free Tier Limits

**Anthropic Claude:**
- $5 free credits
- Enough for ~1-2 million tokens
- Perfect for testing PyCode!

**OpenAI GPT:**
- $5 free credits (for 3 months)
- Similar usage capacity

## What the Demo Will Do With Real LLM

Once you have an API key, the demo will:
1. Actually send your request to Claude
2. Claude will write real code
3. PyCode will execute it
4. Claude will see the results
5. Claude will fix any errors
6. Iterate until it works!

You'll see the REAL vibe coding workflow in action!

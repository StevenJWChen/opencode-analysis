# PyCode Vibe Coding - Quick Start Guide

Get started with PyCode's vibe coding demo in 3 easy steps!

---

## 🚀 Quick Start (3 Steps)

### Step 1: Get a FREE API Key (2 minutes)

**Anthropic (Recommended) - $5 Free Credits:**
1. Go to: https://console.anthropic.com/
2. Sign up with your email
3. Go to: https://console.anthropic.com/settings/keys
4. Click "Create Key"
5. Copy your API key (starts with `sk-ant-`)

**Alternative - OpenAI - $5 Free Credits:**
- Sign up: https://platform.openai.com/signup
- Get key: https://platform.openai.com/api-keys

### Step 2: Set Up API Key (1 minute)

**Interactive Setup (Easiest):**
```bash
cd /home/user/opencode-analysis/pycode
python setup_api_key.py
```

The script will:
- Ask for your API key
- Save it to `.env` file
- Test that it works
- Confirm everything is ready

**Manual Setup:**
```bash
# Create .env file
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env

# Or set environment variable
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### Step 3: Run the Demo! (1 minute)

```bash
python run_demo_with_llm.py
```

Choose from example requests or enter your own!

---

## 📺 What You'll See

When you run the demo, you'll see the **complete vibe coding workflow**:

```
🎯 Request: Write a fibonacci calculator

🚀 Starting vibe coding loop...

--- Iteration 1 ---
💭 I'll create a fibonacci calculator...

🔧 Running tool: write
   Arguments: {
     "file_path": "./vibe_demo_workspace/fibonacci.py",
     "content": "def fibonacci(n):..."
   }
   ✅ Result: Created fibonacci.py

--- Iteration 2 ---
💭 Now let me test it...

🔧 Running tool: bash
   Arguments: {
     "command": "python ./vibe_demo_workspace/fibonacci.py",
     "description": "Test fibonacci script"
   }
   ✅ Result: Exit code 0
   Output: F(0) = 0
          F(1) = 1
          F(2) = 1
          ...

✅ Task complete after 2 iteration(s)
```

---

## 🎯 Example Requests

Try these built-in examples:

1. **Fibonacci Calculator**
   - Writes the code
   - Runs it
   - Shows output

2. **Simple Calculator**
   - Creates calculator
   - Tests with 5 + 3
   - Verifies result is 8

3. **String Reverser**
   - Writes function
   - Tests with "Hello World"
   - Shows reversed output

4. **Word Counter**
   - Creates sample text file
   - Writes word counter
   - Runs and shows count

Or enter your own custom request!

---

## 🔍 What Happens Behind the Scenes

```
┌─────────────────────────────────────────┐
│  1. You: "Write a calculator"           │
│         ↓                                │
│  2. PyCode sends to Claude               │
│         ↓                                │
│  3. Claude: "I'll write calculator.py"   │
│         ↓                                │
│  4. Claude calls WriteTool               │
│         ↓                                │
│  5. PyCode creates the file              │
│         ↓                                │
│  6. PyCode sends result to Claude        │
│         ↓                                │
│  7. Claude: "Let me test it..."          │
│         ↓                                │
│  8. Claude calls BashTool                │
│         ↓                                │
│  9. PyCode runs: python calculator.py    │
│         ↓                                │
│  10. PyCode sends output to Claude       │
│         ↓                                │
│  11. Claude: "Works perfectly! Done."    │
│         ↓                                │
│  12. ✅ Complete!                         │
└─────────────────────────────────────────┘
```

---

## 💰 Cost Estimate

With **$5 free credits**, you can run:
- ~50-100 demo iterations
- Multiple complex projects
- Plenty for testing and learning!

Each demo typically uses:
- ~1,000-5,000 tokens per request
- $0.01-0.05 per demo run
- Your $5 goes a long way!

---

## 🛠️ Troubleshooting

### "No API key found"
```bash
# Make sure .env file exists
ls -la .env

# Or set environment variable
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### "API key test failed"
- Check your API key is correct
- Make sure you copied the full key
- Verify you have credits: https://console.anthropic.com/settings/billing

### "ModuleNotFoundError: anthropic"
```bash
pip install anthropic
```

### Demo runs but no real LLM
- The demo has two modes:
  - **Mock mode**: No API key (shows example workflow)
  - **Real mode**: With API key (uses actual Claude)
- Make sure your API key is set correctly

---

## 📚 Files Created

After running the demo, check:
```
vibe_demo_workspace/
├── fibonacci.py          # Code written by Claude
├── calculator.py         # Another example
└── ...                   # Whatever Claude creates!
```

All files are real, working code written by the AI!

---

## 🎓 What You're Learning

By running this demo, you're seeing:

1. **AI writes code** - Using WriteTool
2. **AI executes code** - Using BashTool
3. **AI sees results** - Real output/errors
4. **AI fixes bugs** - Using EditTool
5. **AI iterates** - Until it works!

This is **vibe coding** - the future of AI-assisted development!

---

## 🚀 Next Steps

Once you've run the demo:

1. Try custom requests
2. Modify the code it generates
3. Ask it to fix specific bugs
4. Build real projects!

PyCode has **15 tools** available:
- Write, Read, Edit, MultiEdit
- Bash, Git, Grep, CodeSearch
- Glob, Ls, WebFetch
- Snapshot, Patch, Todo, Ask

All ready for your development workflow!

---

## 📖 Additional Resources

- **API_KEY_SETUP.md** - Detailed setup instructions
- **ALL_TOOLS_SUMMARY.md** - Complete tool documentation
- **vibe_coding_demo.py** - Mock demo (no API key needed)
- **run_demo_with_llm.py** - Real LLM demo

---

## 🎉 Ready to Start?

```bash
# Step 1: Setup (if you haven't already)
python setup_api_key.py

# Step 2: Run!
python run_demo_with_llm.py

# Step 3: Watch the magic! ✨
```

**Have fun coding with AI!** 🚀

---

*PyCode - Making vibe coding accessible to everyone*

# PyCode - New Features

This document describes the essential features added to make PyCode production-ready.

## 🎉 What's New

PyCode now includes all essential features for a complete vibe coding experience:

1. **Configuration System** - Customize behavior with YAML
2. **Session Management** - Create, list, resume, and delete sessions
3. **Message History** - Persistent conversation storage
4. **Better CLI** - Full command-line interface
5. **Doom Loop Detection** - Prevent infinite loops
6. **Integrated Runner** - Everything works together seamlessly

---

## 1. Configuration System

### Overview
YAML-based configuration system for customizing PyCode behavior.

### Config File Locations
PyCode searches for config files in this order:
1. `~/.pycode/config.yaml` (global config)
2. `./.pycode.yaml` (project config)
3. `./pycode.yaml` (project config)

### Create Default Config
```bash
python pycode_cli.py config init
```

This creates `~/.pycode/config.yaml` with default settings.

### Example Configuration
```yaml
# Runtime settings
runtime:
  verbose: true
  auto_approve_tools: false
  max_iterations: 10
  doom_loop_detection: true
  doom_loop_threshold: 3
  context_window_tokens: 100000
  max_conversation_messages: 20

# Default model
default_model:
  provider: anthropic
  model_id: claude-3-5-sonnet-20241022
  temperature: 0.7
  max_tokens: 4096

# Agent configurations
agents:
  build:
    name: build
    enabled_tools:
      - write
      - read
      - edit
      - bash
      - grep
      - glob
    edit_permission: allow
    bash_permissions:
      "*": allow
    max_iterations: 10

  plan:
    name: plan
    enabled_tools:
      - read
      - grep
      - glob
      - ls
    edit_permission: deny
    bash_permissions:
      "*": deny
    max_iterations: 5

# Provider settings
providers:
  anthropic:
    api_key: null  # Load from ANTHROPIC_API_KEY env var
    timeout: 60

# Storage location
storage_path: ~/.pycode/storage

# Enabled tools (global)
enabled_tools:
  - write
  - read
  - edit
  - bash
  - grep
  - glob
  - ls
  - multiedit
  - git
  - webfetch
  - snapshot
  - patch
  - ask
  - todo
  - codesearch
```

### Configuration Options

#### Runtime Settings
- `verbose` - Show detailed output
- `auto_approve_tools` - Automatically approve all tool calls
- `max_iterations` - Maximum number of agent iterations
- `doom_loop_detection` - Enable doom loop detection
- `doom_loop_threshold` - Number of identical calls before triggering
- `context_window_tokens` - Maximum tokens in context window
- `max_conversation_messages` - Maximum messages to keep in context

#### Model Settings
- `provider` - LLM provider (anthropic, openai)
- `model_id` - Model identifier
- `temperature` - Sampling temperature (0.0-1.0)
- `max_tokens` - Maximum tokens in response

#### Agent Settings
- `name` - Agent name
- `enabled_tools` - List of tools the agent can use
- `edit_permission` - File editing permission (allow, deny, ask)
- `bash_permissions` - Bash command permissions (glob patterns)
- `max_iterations` - Agent-specific iteration limit

---

## 2. Session Management

### Overview
Create, list, resume, and delete coding sessions. Each session maintains its own conversation history and state.

### Key Features
- Multi-project support
- Session metadata (created, updated, last activity)
- Message counting
- Statistics and reporting

### Session Structure
```python
Session(
    id="session_...",           # Unique session ID (descending ULID)
    project_id="my-project",    # Project identifier
    directory="/path/to/dir",   # Working directory
    title="Session title",      # Human-readable title
    time_created=...,           # Timestamp (ms)
    time_updated=...,           # Timestamp (ms)
)
```

### CLI Commands

**List all sessions:**
```bash
python pycode_cli.py list
```

**List sessions for a project:**
```bash
python pycode_cli.py list --project my-project
```

**Create new session:**
```bash
python pycode_cli.py run "Write a Python web scraper"
```

**Resume a session:**
```bash
python pycode_cli.py resume session_01234567890
```

**Delete a session:**
```bash
python pycode_cli.py delete session_01234567890
```

**View statistics:**
```bash
python pycode_cli.py stats
```

### Programmatic Usage
```python
from pycode.session_manager import SessionManager
from pycode.storage import Storage

storage = Storage()
manager = SessionManager(storage)

# Create session
session = await manager.create_session(
    project_id="my-project",
    directory="/path/to/project",
    title="My coding session"
)

# List sessions
sessions = await manager.list_sessions(project_id="my-project", limit=10)

# Load session
session = await manager.load_session(session_id, project_id)

# Get statistics
stats = await manager.get_session_stats(session_id, project_id)

# Delete session
await manager.delete_session(session_id, project_id)
```

---

## 3. Message History

### Overview
Persistent storage and retrieval of conversation messages. Enables resuming sessions and managing long conversations.

### Key Features
- Save/load messages
- Build conversation for LLM
- Context management (token limits)
- Conversation pruning

### Message Structure
```python
Message(
    id="message_...",           # Unique message ID (ascending ULID)
    session_id="session_...",   # Parent session
    role="user" | "assistant",  # Speaker
    agent="build",              # Agent name (for assistant)
    parts=[...],                # Message parts (text, tool calls, etc.)
    time_created=...,           # Timestamp (ms)
)
```

### CLI Commands

**Clear session history:**
```bash
python pycode_cli.py clear session_01234567890
```

### Programmatic Usage
```python
from pycode.history import MessageHistory, ContextManager
from pycode.storage import Storage

storage = Storage()
history = MessageHistory(storage)

# Save message
await history.save_message(session_id, message)

# Load messages
messages = await history.load_messages(session_id, limit=20)

# Get conversation for LLM
conversation = await history.get_conversation_for_llm(session_id, max_messages=20)

# Get message count
count = await history.get_message_count(session_id)

# Clear history
await history.clear_history(session_id)
```

### Context Management
```python
context_manager = ContextManager()

# Prune conversation to fit token limit
pruned = context_manager.prune_conversation(conversation, target_tokens=50000)

# Estimate tokens
tokens = context_manager.estimate_tokens(text)
```

---

## 4. Better CLI

### Overview
Full command-line interface for all PyCode operations.

### Available Commands

**List sessions:**
```bash
python pycode_cli.py list [--project PROJECT] [--limit LIMIT]
```

**Run new session:**
```bash
python pycode_cli.py run "REQUEST" [--project PROJECT] [--directory DIR] [--agent AGENT]
```

**Resume session:**
```bash
python pycode_cli.py resume SESSION_ID [--request "NEW REQUEST"]
```

**Clear session history:**
```bash
python pycode_cli.py clear SESSION_ID
```

**Delete session:**
```bash
python pycode_cli.py delete SESSION_ID
```

**Show configuration:**
```bash
python pycode_cli.py config show
```

**Initialize configuration:**
```bash
python pycode_cli.py config init
```

**View statistics:**
```bash
python pycode_cli.py stats
```

### Examples

**Start a new coding session:**
```bash
python pycode_cli.py run "Create a Flask API with user authentication"
```

**List recent sessions:**
```bash
python pycode_cli.py list --limit 10
```

**Resume yesterday's work:**
```bash
python pycode_cli.py resume session_01JGK7MXYZ123
```

**Add to existing session:**
```bash
python pycode_cli.py resume session_01JGK7MXYZ123 --request "Add password reset"
```

**View project statistics:**
```bash
python pycode_cli.py stats
```

---

## 5. Doom Loop Detection

### Overview
Automatically detects and prevents infinite loops where the agent repeats the same action.

### How It Works
1. Tracks all tool calls and their parameters
2. Detects identical repeated calls (e.g., write → write → write)
3. Detects alternating patterns (e.g., write → read → write → read)
4. Breaks execution when threshold is reached

### Configuration
```yaml
runtime:
  doom_loop_detection: true    # Enable/disable
  doom_loop_threshold: 3       # Number of repeats before triggering
```

### Detection Patterns

**Identical Repeats:**
```
Tool: bash, Args: {"command": "python test.py"}
Tool: bash, Args: {"command": "python test.py"}
Tool: bash, Args: {"command": "python test.py"}
→ DOOM LOOP DETECTED!
```

**Alternating Pattern:**
```
Tool: write, Args: {"file": "test.py", ...}
Tool: bash, Args: {"command": "python test.py"}
Tool: write, Args: {"file": "test.py", ...}
Tool: bash, Args: {"command": "python test.py"}
→ DOOM LOOP DETECTED!
```

### When It Triggers
The agent will stop and display:
```
⚠️  DOOM LOOP DETECTED!
The agent is repeating the same action: bash
This usually means the approach isn't working.
Breaking the loop to prevent infinite execution.
```

This prevents:
- Wasting API credits
- Infinite retries on unsolvable problems
- Agent getting stuck in unproductive cycles

---

## 6. Integrated Runner

### Overview
AgentRunner now integrates all the new features seamlessly.

### Key Improvements
- Automatic message persistence
- Session management integration
- Conversation history loading
- Doom loop detection
- Configuration-driven behavior

### Usage
```python
from pycode.runner import AgentRunner, RunConfig
from pycode.storage import Storage
from pycode.config import load_config

# Load configuration
config = load_config()

# Create storage
storage = Storage()

# Create runner
run_config = RunConfig(
    max_iterations=config.runtime.max_iterations,
    verbose=config.runtime.verbose,
    auto_approve_tools=True,
    doom_loop_detection=config.runtime.doom_loop_detection,
    doom_loop_threshold=config.runtime.doom_loop_threshold,
)

runner = AgentRunner(
    session=session,
    agent=agent,
    provider=provider,
    registry=registry,
    config=run_config,
    storage=storage,  # NEW: Pass storage for history
)

# Run
async for chunk in runner.run(user_request):
    print(chunk, end="")
```

### What Happens Automatically
1. User message is saved to history
2. Conversation history is loaded from storage
3. Session timestamp is updated
4. Tool calls are tracked for doom loop detection
5. Assistant messages are saved after each iteration
6. Session is persisted after updates

---

## Migration Guide

### Updating Existing Code

**Before:**
```python
runner = AgentRunner(session, agent, provider, registry, config)
```

**After:**
```python
from pycode.storage import Storage

storage = Storage()
runner = AgentRunner(session, agent, provider, registry, config, storage)
```

### Configuration
1. Create default config: `python pycode_cli.py config init`
2. Customize `~/.pycode/config.yaml`
3. Restart PyCode

### CLI Migration
Replace manual session management with CLI commands:

**Before:**
```python
# Manual session creation
session = Session(...)
```

**After:**
```bash
python pycode_cli.py run "your request"
```

---

## Demos

### Run Comprehensive Demo
```bash
python comprehensive_demo.py
```

This demonstrates all new features:
- Configuration system
- Session management
- Message history
- Vibe coding workflow
- Doom loop detection

### Run Vibe Coding Demo
```bash
python run_demo_with_llm.py
```

Now includes:
- Session persistence
- Message history
- Doom loop protection
- Configuration loading

---

## File Locations

### Configuration
- `~/.pycode/config.yaml` - Global configuration
- `./.pycode.yaml` - Project configuration

### Storage
- `~/.pycode/storage/` - Default storage location
- `~/.pycode/storage/sessions/<project>/` - Session files
- `~/.pycode/storage/sessions/<project>/messages/<session>/` - Message history

### Logs
- Session metadata: `storage/sessions/<project>/<session_id>.json`
- Messages: `storage/sessions/<project>/messages/<session_id>/<message_id>.json`

---

## Performance Considerations

### Token Management
- Messages are limited to `max_conversation_messages` (default: 20)
- Context manager prunes old messages when approaching token limit
- Summaries are created for removed messages

### Storage
- File-based JSON storage (simple, portable)
- Asynchronous I/O for better performance
- Automatic directory creation

### Doom Loop Detection
- Minimal overhead (simple list tracking)
- Configurable threshold
- Can be disabled for debugging

---

## Troubleshooting

### Config Not Loading
- Check file location: `~/.pycode/config.yaml`
- Validate YAML syntax
- Run: `python pycode_cli.py config show`

### Session Not Found
- Check session ID
- List sessions: `python pycode_cli.py list`
- Verify storage path in config

### Doom Loop False Positives
- Increase threshold in config
- Disable temporarily: `doom_loop_detection: false`
- Check tool call patterns in verbose output

### API Key Issues
- Run: `python setup_api_key.py`
- Verify: `echo $ANTHROPIC_API_KEY`
- Check `.env` file

---

## Next Steps

1. **Try the demos:**
   ```bash
   python comprehensive_demo.py
   python run_demo_with_llm.py
   ```

2. **Explore the CLI:**
   ```bash
   python pycode_cli.py --help
   python pycode_cli.py list
   python pycode_cli.py stats
   ```

3. **Customize configuration:**
   ```bash
   python pycode_cli.py config init
   nano ~/.pycode/config.yaml
   ```

4. **Start a real session:**
   ```bash
   python pycode_cli.py run "Your coding request here"
   ```

---

## Summary

PyCode is now production-ready with:
- ✅ Configuration system (YAML)
- ✅ Session management (create, list, resume, delete)
- ✅ Message history (persistent storage)
- ✅ Better CLI (full command set)
- ✅ Doom loop detection (prevent infinite loops)
- ✅ Integrated runner (everything works together)

These features make PyCode a complete vibe coding platform, on par with OpenCode!

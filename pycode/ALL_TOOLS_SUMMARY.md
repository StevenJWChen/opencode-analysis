# PyCode - Complete Tool Collection

PyCode now has **15 tools**, matching most of OpenCode's functionality!

---

## 📊 Complete Tool List

### File Operations (6 tools)

| # | Tool | Purpose | Lines | Status |
|---|------|---------|-------|--------|
| 1 | **ReadTool** | Read file contents with line numbers | ~90 | ✅ Original |
| 2 | **WriteTool** | Create new files | ~120 | ✅ Added |
| 3 | **EditTool** | Edit existing files (exact match) | ~145 | ✅ Original |
| 4 | **MultiEditTool** | Batch file editing (multiple files) | ~250 | 🆕 **NEW** |
| 5 | **GlobTool** | File pattern matching | ~150 | ✅ Added |
| 6 | **LsTool** | Directory listing (ls -la style) | ~220 | ✅ Added |

### Development Tools (4 tools)

| # | Tool | Purpose | Lines | Status |
|---|------|---------|-------|--------|
| 7 | **BashTool** | Execute shell commands | ~110 | ✅ Original |
| 8 | **GrepTool** | Search code patterns | ~150 | ✅ Original |
| 9 | **CodeSearchTool** | Advanced semantic code search | ~220 | 🆕 **NEW** |
| 10 | **GitTool** | Version control operations | ~180 | ✅ Added |

### Versioning & State (3 tools)

| # | Tool | Purpose | Lines | Status |
|---|------|---------|-------|--------|
| 11 | **SnapshotTool** | Create code snapshots | ~140 | 🆕 **NEW** |
| 12 | **PatchTool** | Apply patches / restore snapshots | ~190 | 🆕 **NEW** |
| 13 | **TodoTool** | Task management | ~200 | 🆕 **NEW** |

### Network & Interaction (2 tools)

| # | Tool | Purpose | Lines | Status |
|---|------|---------|-------|--------|
| 14 | **WebFetchTool** | HTTP requests | ~200 | ✅ Added |
| 15 | **AskTool** | User interaction / confirmation | ~150 | 🆕 **NEW** |

---

## 🆕 6 Brand New Tools Added

### 1. MultiEditTool - Batch File Editing

**Purpose**: Edit multiple files simultaneously with transaction support

**Key Features**:
- Transaction-based (all-or-nothing)
- Automatic rollback on errors
- Dry-run mode
- Shows diffs for all files
- Replace across multiple files

**Example**:
```python
await registry.execute("multiedit", {
    "edits": [
        {
            "file_path": "file1.py",
            "old_string": "old_name",
            "new_string": "new_name",
            "replace_all": True
        },
        {
            "file_path": "file2.py",
            "old_string": "old_name",
            "new_string": "new_name",
            "replace_all": True
        }
    ],
    "dry_run": False
}, context)
```

### 2. SnapshotTool - Code Versioning

**Purpose**: Create point-in-time snapshots of code files

**Key Features**:
- Save multiple files at once
- Includes metadata (timestamp, size, lines)
- Session-specific storage
- Enables rollback via PatchTool
- JSON format for easy inspection

**Example**:
```python
await registry.execute("snapshot", {
    "files": ["src/main.py", "src/utils.py"],
    "description": "Before refactoring"
}, context)
```

**Output**: Creates `.pycode/snapshots/snapshot_20231229_143022.json`

### 3. PatchTool - Apply Patches

**Purpose**: Restore files from snapshots or apply patches

**Key Features**:
- Restore from snapshots
- Selective file restoration
- Automatic backup before applying
- Dry-run preview
- Shows diffs of changes

**Example**:
```python
await registry.execute("patch", {
    "snapshot_file": ".pycode/snapshots/snapshot_20231229_143022.json",
    "dry_run": True  # Preview first
}, context)
```

### 4. TodoTool - Task Management

**Purpose**: Manage tasks within coding sessions

**Key Features**:
- Add/remove/update todos
- Three states: pending, in_progress, completed
- Session-specific persistence
- Statistics tracking
- List filtering by status

**Example**:
```python
# Add a todo
await registry.execute("todo", {
    "operation": "add",
    "task": "Implement authentication"
}, context)

# Mark as in progress
await registry.execute("todo", {
    "operation": "update",
    "task_id": 1,
    "status": "in_progress"
}, context)

# Complete it
await registry.execute("todo", {
    "operation": "complete",
    "task_id": 1
}, context)
```

### 5. AskTool - User Interaction

**Purpose**: Get user input, confirmation, or choices interactively

**Key Features**:
- Three question types: confirm, input, choice
- Default values support
- Terminal-based interaction
- Blocks until user responds
- Stores response in metadata

**Example**:
```python
# Confirmation
await registry.execute("ask", {
    "question": "Delete all temporary files?",
    "type": "confirm",
    "default": "no"
}, context)

# Choice
await registry.execute("ask", {
    "question": "Select deployment environment",
    "type": "choice",
    "choices": ["development", "staging", "production"],
    "default": "development"
}, context)

# Free input
await registry.execute("ask", {
    "question": "Enter commit message",
    "type": "input"
}, context)
```

### 6. CodeSearchTool - Advanced Code Search

**Purpose**: Semantic and structural code search

**Key Features**:
- Six search types: definition, usage, import, comment, pattern, symbol
- Syntax-aware patterns
- Context lines around matches
- File type filtering
- Result ranking

**Example**:
```python
# Find function definitions
await registry.execute("codesearch", {
    "query": "process_data",
    "search_type": "definition",
    "file_extensions": [".py"],
    "context_lines": 3
}, context)

# Find TODO comments
await registry.execute("codesearch", {
    "query": "TODO",
    "search_type": "comment",
    "max_results": 20
}, context)

# Find import statements
await registry.execute("codesearch", {
    "query": "requests",
    "search_type": "import"
}, context)
```

---

## 📈 Tool Coverage Comparison

### Before vs Now

| Category | OpenCode | PyCode Before | PyCode Now | Coverage |
|----------|----------|---------------|------------|----------|
| **File Operations** | 8 tools | 2 tools | **6 tools** | 75% |
| **Development** | 6 tools | 2 tools | **4 tools** | 67% |
| **Versioning** | 3 tools | 0 tools | **3 tools** | 100% |
| **Network** | 2 tools | 0 tools | **1 tool** | 50% |
| **Interaction** | 2 tools | 0 tools | **1 tool** | 50% |
| **Total** | 20+ tools | 4 tools | **15 tools** | 75% |

### Still Missing from OpenCode

Only a few advanced tools remain:

1. **LSP Tool** - Language Server Protocol integration (very complex, requires language servers)
2. **Skill System** - Specialized sub-task templates (requires plugin architecture)
3. **Batch Tool** - Additional batch operations (largely covered by MultiEdit)

---

## 🎯 Complete Workflow Examples

### Example 1: Refactoring Workflow

```python
# 1. Create snapshot before refactoring
await registry.execute("snapshot", {
    "files": glob_result.metadata["files"],
    "description": "Before renaming API methods"
}, context)

# 2. Rename across multiple files
await registry.execute("multiedit", {
    "edits": [
        {"file_path": f, "old_string": "getData", "new_string": "fetchData", "replace_all": True}
        for f in files_to_edit
    ],
    "dry_run": True  # Preview first
}, context)

# 3. Apply changes
await registry.execute("multiedit", {
    "edits": [...],
    "dry_run": False
}, context)

# 4. If something went wrong, rollback
await registry.execute("patch", {
    "snapshot_file": ".pycode/snapshots/snapshot_xyz.json"
}, context)
```

### Example 2: Code Review Workflow

```python
# 1. Find all TODO comments
todos = await registry.execute("codesearch", {
    "query": "TODO",
    "search_type": "comment"
}, context)

# 2. Track them
for todo in todos:
    await registry.execute("todo", {
        "operation": "add",
        "task": f"Fix TODO in {todo['file']}:{todo['line']}"
    }, context)

# 3. Work on them
await registry.execute("todo", {
    "operation": "list"
}, context)

# 4. Mark completed as you go
await registry.execute("todo", {
    "operation": "complete",
    "task_id": 1
}, context)
```

### Example 3: Search & Replace Workflow

```python
# 1. Find all uses of old function
results = await registry.execute("codesearch", {
    "query": "oldFunction",
    "search_type": "usage",
    "file_extensions": [".py", ".js"]
}, context)

# 2. Create snapshot
files = list(set(r["file"] for r in results.metadata["matches"]))
await registry.execute("snapshot", {
    "files": files,
    "description": "Before replacing oldFunction"
}, context)

# 3. Replace in all files
edits = [
    {"file_path": f, "old_string": "oldFunction", "new_string": "newFunction", "replace_all": True}
    for f in files
]
await registry.execute("multiedit", {"edits": edits}, context)
```

---

## 💾 Storage Structure

PyCode now creates the following structure:

```
.pycode/
├── snapshots/          # Code snapshots
│   └── snapshot_YYYYMMDD_HHMMSS.json
├── todos/              # Session todos
│   └── {session_id}.json
└── backups/            # Automatic backups
    └── YYYYMMDD_HHMMSS/
        └── *.py
```

---

## 📊 Code Statistics

```
Total Tools: 15
Total Lines of Tool Code: ~2,500 lines

Breakdown:
- File Operations: ~775 lines (6 tools)
- Development: ~660 lines (4 tools)
- Versioning: ~530 lines (3 tools)
- Network/Interaction: ~535 lines (2 tools)

PyCode Total: ~3,500 lines (up from ~2,050)
```

---

## 🔧 Tool Dependencies

All new tools use only Python standard library except:
- WebFetchTool requires `httpx` (already in requirements.txt)

No additional dependencies needed!

---

## 🚀 Usage

All tools are automatically available when you import:

```python
from pycode.tools import (
    BashTool, ReadTool, EditTool, GrepTool,
    WriteTool, GlobTool, LsTool, WebFetchTool, GitTool,
    MultiEditTool, SnapshotTool, PatchTool,
    AskTool, TodoTool, CodeSearchTool,
    ToolRegistry, ToolContext
)
```

### Quick Start

```python
import asyncio
from pathlib import Path
from pycode.tools import ToolRegistry, ToolContext, MultiEditTool

async def main():
    registry = ToolRegistry()
    registry.register(MultiEditTool())

    context = ToolContext(
        session_id="session_001",
        message_id="msg_001",
        agent_name="build",
        working_directory=str(Path.cwd())
    )

    result = await registry.execute("multiedit", {
        "edits": [
            {
                "file_path": "file.py",
                "old_string": "old",
                "new_string": "new"
            }
        ]
    }, context)

    print(result.output)

asyncio.run(main())
```

---

## 🎓 Learning Resources

- **File Operations**: See `new_tools_demo.py` for Write, Glob, Ls examples
- **All Tools**: Complete examples coming in `complete_tools_demo.py`
- **Tool Prompts**: See `tool_prompt_example.py` for LLM integration
- **Architecture**: See `PYTHON_IMPLEMENTATION_GUIDE.md`

---

## 🎯 Achievement Unlocked!

PyCode has evolved from a **basic 4-tool prototype** to a **comprehensive 15-tool development assistant** with:

✅ 6 file operation tools
✅ 4 development tools
✅ 3 versioning/state tools
✅ 2 network/interaction tools
✅ Transaction support
✅ Snapshot/restore capability
✅ Task management
✅ Advanced code search
✅ User interaction
✅ Batch operations

**Coverage**: 75% of OpenCode's tool functionality in ~3,500 lines of Python!

---

*Last Updated: 2025-12-29*
*PyCode Version: 0.2.0*
*Total Tools: 15*

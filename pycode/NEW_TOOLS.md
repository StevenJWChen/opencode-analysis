# New PyCode Tools Documentation

This document describes the 5 new tools added to PyCode, bringing the total from 4 to 9 tools.

---

## Overview

PyCode now includes 9 tools for comprehensive development workflows:

| # | Tool | Purpose | Status |
|---|------|---------|--------|
| 1 | **BashTool** | Execute shell commands | ✅ Original |
| 2 | **ReadTool** | Read file contents | ✅ Original |
| 3 | **EditTool** | Edit existing files | ✅ Original |
| 4 | **GrepTool** | Search code patterns | ✅ Original |
| 5 | **WriteTool** | Create new files | 🆕 NEW |
| 6 | **GlobTool** | File pattern matching | 🆕 NEW |
| 7 | **LsTool** | Directory listing | 🆕 NEW |
| 8 | **WebFetchTool** | HTTP requests | 🆕 NEW |
| 9 | **GitTool** | Version control | 🆕 NEW |

---

## 🆕 New Tool #1: WriteTool

### Purpose
Create new files or overwrite existing files with content.

### Use Cases
- Generate new source files
- Create configuration files
- Write documentation
- Save output to files

### Parameters

```python
{
    "file_path": str,        # Absolute path to file (required)
    "content": str,          # Content to write (required)
    "create_parents": bool   # Create parent directories (default: true)
}
```

### Example Usage

```python
from pycode.tools import WriteTool, ToolContext, ToolRegistry

registry = ToolRegistry()
registry.register(WriteTool())

context = ToolContext(
    session_id="session_001",
    message_id="msg_001",
    agent_name="build",
    working_directory="/path/to/project"
)

result = await registry.execute(
    "write",
    {
        "file_path": "/path/to/project/new_file.py",
        "content": '''"""New module"""

def main():
    print("Hello from PyCode!")

if __name__ == "__main__":
    main()
'''
    },
    context
)

print(result.output)
# Output:
# Created file: /path/to/project/new_file.py
# 7 lines, 123 bytes
#
# Preview (first 10 lines):
# """New module"""
#
# def main():
#     print("Hello from PyCode!")
# ...
```

### Features
- ✅ Creates new files
- ✅ Overwrites existing files (with warning)
- ✅ Auto-creates parent directories
- ✅ Shows file statistics
- ✅ Preview of content
- ✅ Metadata tracking

### Notes
- **Warning**: This will overwrite existing files without confirmation
- Use `read` tool first to check if file exists
- Use `edit` tool for modifying existing files
- Parent directories are created automatically by default

---

## 🆕 New Tool #2: GlobTool

### Purpose
Find files matching glob patterns (wildcards).

### Use Cases
- Find all Python files: `**/*.py`
- Find test files: `test_*.py`
- Find TypeScript components: `src/**/*.tsx`
- Locate config files: `*.{json,yaml,yml}`

### Parameters

```python
{
    "pattern": str,          # Glob pattern (required)
    "path": str,             # Search directory (default: current)
    "max_results": int,      # Limit results (default: 100)
    "include_hidden": bool,  # Include dotfiles (default: false)
    "files_only": bool       # Only files, not dirs (default: true)
}
```

### Example Usage

```python
# Find all Python files recursively
result = await registry.execute(
    "glob",
    {
        "pattern": "**/*.py",
        "path": "/path/to/project/src",
        "max_results": 50
    },
    context
)

# Find all markdown files in current directory
result = await registry.execute(
    "glob",
    {
        "pattern": "*.md",
        "max_results": 20
    },
    context
)

# Find test files
result = await registry.execute(
    "glob",
    {
        "pattern": "**/test_*.py",
        "include_hidden": False
    },
    context
)
```

### Pattern Examples

| Pattern | Matches |
|---------|---------|
| `*.py` | Python files in current directory |
| `**/*.py` | All Python files recursively |
| `src/**/*.{ts,tsx}` | TypeScript files in src/ |
| `test_*.py` | Files starting with "test_" |
| `[!.]*.py` | Python files not starting with dot |
| `**/__pycache__/**` | All files in __pycache__ directories |

### Features
- ✅ Recursive pattern matching
- ✅ Sorted by modification time (newest first)
- ✅ File size display
- ✅ Hidden file filtering
- ✅ Result limiting
- ✅ Relative path display

### Notes
- Uses Python's `pathlib.glob()` for pattern matching
- Results are sorted by modification time (newest first)
- Hidden files (starting with `.`) are excluded by default
- Output includes file sizes in human-readable format

---

## 🆕 New Tool #3: LsTool

### Purpose
List directory contents with detailed information (similar to `ls -la`).

### Use Cases
- Explore directory structure
- Check file permissions
- See modification times
- Identify file types and sizes

### Parameters

```python
{
    "path": str,             # Directory to list (default: current)
    "show_hidden": bool,     # Show hidden files (default: true)
    "recursive": bool,       # List recursively (default: false)
    "max_depth": int         # Max recursion depth (default: 1)
}
```

### Example Usage

```python
# List current directory
result = await registry.execute(
    "ls",
    {
        "show_hidden": True
    },
    context
)

# List specific directory
result = await registry.execute(
    "ls",
    {
        "path": "/path/to/project/src",
        "show_hidden": False
    },
    context
)

# List recursively
result = await registry.execute(
    "ls",
    {
        "path": "/path/to/project",
        "recursive": True,
        "max_depth": 2
    },
    context
)
```

### Output Format

```
Listing: /path/to/project

drwxr-xr-x        -  Dec 29 23:24  src/
drwxr-xr-x        -  Dec 29 23:20  tests/
-rw-r--r--     1.2K  Dec 29 23:15  README.md
-rw-r--r--      82B  Dec 29 23:29  .gitignore
-rw-r--r--     3.0K  Dec 29 23:15  requirements.txt
```

### Features
- ✅ Detailed file information
- ✅ Permission display (rwxrwxrwx)
- ✅ File type indicators (d=dir, l=link, -=file)
- ✅ Human-readable file sizes
- ✅ Modification timestamps
- ✅ Recursive listing with indentation
- ✅ Hidden file support

### Notes
- Directories shown with trailing `/`
- Symlinks show target path
- Sizes displayed in B, K, M, G units
- Sorts directories first, then alphabetically
- Includes `.` and `..` entries when appropriate

---

## 🆕 New Tool #4: WebFetchTool

### Purpose
Fetch content from web URLs via HTTP/HTTPS requests.

### Use Cases
- Fetch API responses
- Download documentation
- Access public data sources
- Test HTTP endpoints
- Read web page content

### Parameters

```python
{
    "url": str,                  # URL to fetch (required)
    "method": str,               # HTTP method: GET or POST (default: GET)
    "headers": dict,             # Custom headers (optional)
    "body": str,                 # Request body for POST (optional)
    "follow_redirects": bool     # Follow redirects (default: true)
}
```

### Example Usage

```python
# GET request
result = await registry.execute(
    "webfetch",
    {
        "url": "https://api.github.com/repos/python/cpython"
    },
    context
)

# GET with custom headers
result = await registry.execute(
    "webfetch",
    {
        "url": "https://api.example.com/data",
        "method": "GET",
        "headers": {
            "Authorization": "Bearer token123",
            "Accept": "application/json"
        }
    },
    context
)

# POST request
result = await registry.execute(
    "webfetch",
    {
        "url": "https://api.example.com/create",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        },
        "body": '{"name": "test", "value": 123}'
    },
    context
)
```

### Features
- ✅ HTTP GET and POST methods
- ✅ Custom headers support
- ✅ Automatic redirect following
- ✅ Response size limiting (10 MB max)
- ✅ Timeout protection (30 seconds)
- ✅ Response headers display
- ✅ Content truncation for large responses

### Security Notes
- ⚠️ Only use for public, accessible URLs
- ⚠️ Respects 30-second timeout
- ⚠️ Response limited to 10 MB
- ⚠️ Use for legitimate purposes only
- ⚠️ Be mindful of API rate limits

### Dependencies
Requires `httpx` package:
```bash
pip install httpx
```

---

## 🆕 New Tool #5: GitTool

### Purpose
Execute common git operations for version control.

### Use Cases
- Check repository status
- View commit history
- See file changes
- Inspect branches
- View commit details

### Parameters

```python
{
    "operation": str,        # Git operation (required)
    "args": list[str],       # Additional arguments (optional)
    "path": str              # Repository path (default: current)
}
```

### Supported Operations

| Operation | Description | Example Args |
|-----------|-------------|--------------|
| `status` | Show working tree status | `[]` |
| `diff` | Show changes | `["HEAD", "main"]` |
| `log` | Show commit history | `["--max-count=10"]` |
| `show` | Show commit details | `["abc123"]` |
| `branch` | List/manage branches | `["-a"]` |
| `blame` | Show file annotations | `["file.py"]` |

### Example Usage

```python
# Git status
result = await registry.execute(
    "git",
    {
        "operation": "status"
    },
    context
)

# Git log (last 5 commits)
result = await registry.execute(
    "git",
    {
        "operation": "log",
        "args": ["--max-count=5", "--oneline"]
    },
    context
)

# Git diff
result = await registry.execute(
    "git",
    {
        "operation": "diff",
        "args": ["HEAD~1", "HEAD"]
    },
    context
)

# List branches
result = await registry.execute(
    "git",
    {
        "operation": "branch",
        "args": ["-v"]
    },
    context
)

# Show specific commit
result = await registry.execute(
    "git",
    {
        "operation": "show",
        "args": ["abc123def"]
    },
    context
)
```

### Features
- ✅ Common git operations
- ✅ Automatic repository detection
- ✅ Output formatting
- ✅ Error handling
- ✅ Timeout protection (30 seconds)
- ✅ Output limiting (30,000 chars)

### Default Arguments

The tool provides sensible defaults:

- `status`: Automatically adds `--short --branch`
- `log`: Adds `--oneline --max-count=20` if no args
- `diff`: Defaults to comparing with `HEAD`
- `branch`: Adds `-v` for verbose output

### Safety Notes
- ✅ **Read-only operations only**
- ❌ No commits, pushes, or destructive actions
- ✅ Runs in repository directory
- ✅ Output limited to prevent overflow
- ✅ Use bash tool for complex git workflows

---

## Comparison with OpenCode

| Feature | OpenCode | PyCode Before | PyCode Now |
|---------|----------|---------------|------------|
| **Total Tools** | 20+ | 4 | 9 |
| **File Operations** | 8 tools | 2 tools | 5 tools |
| **Development Tools** | 6 tools | 1 tool | 2 tools |
| **Web/Network** | 2 tools | 0 tools | 1 tool |
| **Version Control** | 3 tools | 0 tools | 1 tool |

### Still Missing from OpenCode

PyCode is still missing these advanced tools:

1. **MultiEdit Tool** - Batch file editing
2. **CodeSearch Tool** - Advanced code search
3. **LSP Tool** - Language Server Protocol integration
4. **Skill System** - Specialized sub-tasks
5. **Todo Tool** - Task management
6. **Batch Tool** - Batch operations
7. **Snapshot/Patch** - Code versioning

---

## Installation

The new tools are automatically available when you import PyCode:

```python
from pycode.tools import (
    WriteTool,
    GlobTool,
    LsTool,
    WebFetchTool,
    GitTool,
    ToolRegistry
)
```

### Dependencies

Make sure you have the required dependencies:

```bash
pip install httpx>=0.25.0  # For WebFetchTool
pip install pydantic>=2.0.0  # For all tools
pip install aiofiles>=23.0.0  # For async file operations
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage Examples

### Complete Workflow Example

```python
import asyncio
from pathlib import Path
from pycode.tools import (
    ToolRegistry, ToolContext,
    WriteTool, ReadTool, GlobTool, GitTool
)

async def complete_workflow():
    # Setup
    registry = ToolRegistry()
    registry.register(WriteTool())
    registry.register(ReadTool())
    registry.register(GlobTool())
    registry.register(GitTool())

    context = ToolContext(
        session_id="workflow_001",
        message_id="msg_001",
        agent_name="build",
        working_directory=str(Path.cwd())
    )

    # 1. Create a new file
    await registry.execute(
        "write",
        {
            "file_path": str(Path.cwd() / "new_module.py"),
            "content": "def hello(): return 'Hello!'"
        },
        context
    )

    # 2. Read it back
    result = await registry.execute(
        "read",
        {"file_path": str(Path.cwd() / "new_module.py")},
        context
    )
    print(result.output)

    # 3. Find all Python files
    result = await registry.execute(
        "glob",
        {"pattern": "*.py", "max_results": 10},
        context
    )
    print(f"Found {result.metadata['count']} Python files")

    # 4. Check git status
    result = await registry.execute(
        "git",
        {"operation": "status"},
        context
    )
    print(result.output)

asyncio.run(complete_workflow())
```

---

## Testing

Run the comprehensive demo:

```bash
cd pycode
python new_tools_demo.py
```

This will test all 5 new tools with various scenarios.

---

## Documentation

- **Main README**: `../README.md`
- **Implementation Guide**: `../PYTHON_IMPLEMENTATION_GUIDE.md`
- **Feature Comparison**: `../FEATURE_COMPARISON.md`
- **Tool Prompts**: `tool_prompt_example.py`

---

*Last Updated: 2025-12-29*
*PyCode Version: 0.1.0*

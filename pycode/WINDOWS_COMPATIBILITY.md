# PyCode Windows Compatibility Guide

## ✅ Yes, PyCode Can Run on Windows!

PyCode is designed to work cross-platform on Windows, macOS, and Linux.

## 📋 Requirements

### Python Installation
- **Python 3.10+** required
- Download from: https://www.python.org/downloads/
- **Important**: Check "Add Python to PATH" during installation

### Installing PyCode on Windows

```powershell
# Open PowerShell or Command Prompt

# Navigate to PyCode directory
cd C:\path\to\pycode

# Install PyCode
pip install -e .

# Verify installation
pycode --help
```

## 🔧 How Entry Points Work on Windows

### On Linux/Mac:
```bash
/usr/local/bin/pycode (shell script)
```

### On Windows:
```
C:\Python311\Scripts\pycode.exe (executable wrapper)
C:\Python311\Scripts\pycode-script.py (Python script)
```

Windows creates **two files**:
1. **pycode.exe** - A small executable that launches Python
2. **pycode-script.py** - The actual Python code

## 🚀 Usage on Windows

### Command Prompt
```cmd
pycode run "Create a Python script"
pycode repl
pycode --help
```

### PowerShell
```powershell
pycode run "Create a Python script"
pycode repl
pycode --help
```

### Git Bash (if installed)
```bash
pycode run "Create a Python script"
pycode repl
```

## ⚠️ Known Differences on Windows

### 1. Bash Tool Limitations

The `bash` tool won't work on Windows unless you have:
- WSL (Windows Subsystem for Linux)
- Git Bash
- Cygwin
- Or other bash implementation

**Solution**: PyCode will detect Windows and can:
- Use `cmd` or `powershell` instead
- Disable bash tool automatically
- Show appropriate error messages

### 2. File Paths

Windows uses backslashes `\` instead of forward slashes `/`:

```python
# PyCode handles both automatically
"/path/to/file"      # Works on Linux/Mac
"C:\\path\\to\\file" # Works on Windows
"C:/path/to/file"    # Also works on Windows (Python converts)
```

### 3. Line Endings

Windows uses `\r\n` (CRLF) vs Linux/Mac `\n` (LF):
- PyCode handles this automatically
- Git can be configured to handle this

## 🔍 Platform Detection

PyCode automatically detects the platform:

```python
import platform
import sys

if platform.system() == 'Windows':
    # Use Windows-specific code
    shell = 'powershell'
elif platform.system() == 'Darwin':
    # macOS
    shell = 'bash'
else:
    # Linux
    shell = 'bash'
```

## 📦 Dependencies Compatibility

All PyCode dependencies work on Windows:

| Dependency | Windows Support |
|------------|-----------------|
| click | ✅ Yes |
| pydantic | ✅ Yes |
| httpx | ✅ Yes |
| anthropic | ✅ Yes |
| openai | ✅ Yes |
| rich | ✅ Yes |
| prompt-toolkit | ✅ Yes |
| pyyaml | ✅ Yes |

## 🦙 Ollama on Windows

Ollama supports Windows:

```powershell
# Install Ollama for Windows
# Download from: https://ollama.com/download

# Start Ollama
ollama serve

# Pull a model
ollama pull llama3.2

# Use with PyCode
pycode run "Create a script" --model llama3.2
```

## 🎯 Installation Steps for Windows

### 1. Install Python

```powershell
# Download Python 3.11 or 3.12 from python.org
# Run installer and check "Add Python to PATH"

# Verify installation
python --version
pip --version
```

### 2. Install PyCode

```powershell
# Clone or download PyCode
git clone https://github.com/your-repo/pycode.git
cd pycode

# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\activate

# Install PyCode
pip install -e .
```

### 3. Configure (Optional)

```powershell
# Create config directory
mkdir $env:USERPROFILE\.pycode

# Create config file
notepad $env:USERPROFILE\.pycode\config.yaml
```

### 4. Use PyCode

```powershell
# Set API key (if using Anthropic)
$env:ANTHROPIC_API_KEY="your-key"

# Or add to PowerShell profile
Add-Content $PROFILE '$env:ANTHROPIC_API_KEY="your-key"'

# Run PyCode
pycode run "Create a hello world script"
```

## 🐛 Troubleshooting Windows Issues

### Issue: "pycode is not recognized"

**Solution**:
```powershell
# Check if Scripts directory is in PATH
$env:PATH -split ';' | Select-String Python

# Add to PATH if missing
$env:PATH += ";C:\Python311\Scripts"

# Or reinstall PyCode
pip install --force-reinstall -e .
```

### Issue: Permission denied

**Solution**:
```powershell
# Run PowerShell as Administrator
# Or change execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Bash tool doesn't work

**Solution**: Install Git Bash or use WSL:
```powershell
# Option 1: Install Git for Windows (includes Git Bash)
# https://git-scm.com/download/win

# Option 2: Use WSL
wsl --install
wsl -d Ubuntu
```

### Issue: File path errors

**Solution**: Use forward slashes or raw strings:
```python
# Use forward slashes (Python converts automatically)
path = "C:/Users/Name/file.txt"

# Or use raw strings
path = r"C:\Users\Name\file.txt"
```

## 📝 Config File Location on Windows

```
C:\Users\YourName\.pycode\config.yaml
```

Or:
```
%USERPROFILE%\.pycode\config.yaml
```

## 🎨 Windows Terminal Recommendations

For the best experience on Windows:

1. **Windows Terminal** (recommended)
   - Download from Microsoft Store
   - Better color support
   - Better Unicode support

2. **PowerShell 7+** (recommended)
   - More features than PowerShell 5.1
   - Better cross-platform compatibility

3. **Git Bash** (for Unix-like experience)
   - Comes with Git for Windows
   - Familiar to Linux/Mac users

## ✅ Testing on Windows

Run the test suite to verify everything works:

```powershell
# Run all tests
pytest tests/ -v

# Should see: 64 passed
```

## 🚀 Quick Start (Windows)

```powershell
# 1. Install Python 3.11+ from python.org

# 2. Open PowerShell

# 3. Clone PyCode
git clone https://github.com/your-repo/pycode.git
cd pycode

# 4. Install
pip install -e .

# 5. Test
pycode --help

# 6. Use with Ollama (if installed)
pycode run "Create a test script" --model llama3.2

# 7. Or use with API
$env:ANTHROPIC_API_KEY="your-key"
pycode run "Create a test script" --model sonnet
```

## 📊 Feature Support on Windows

| Feature | Windows | Linux | macOS |
|---------|---------|-------|-------|
| CLI Commands | ✅ | ✅ | ✅ |
| Logging | ✅ | ✅ | ✅ |
| Retry Logic | ✅ | ✅ | ✅ |
| Tool Validation | ✅ | ✅ | ✅ |
| Provider Aliases | ✅ | ✅ | ✅ |
| File Operations | ✅ | ✅ | ✅ |
| Bash Tool | ⚠️* | ✅ | ✅ |
| Ollama | ✅ | ✅ | ✅ |
| All API Providers | ✅ | ✅ | ✅ |

*Requires Git Bash, WSL, or similar

## 🎯 Summary

**Yes, PyCode fully supports Windows!**

- ✅ All Python features work
- ✅ Entry points create .exe wrappers
- ✅ All dependencies compatible
- ✅ CLI commands work in PowerShell/CMD
- ✅ Config files in standard Windows locations
- ✅ File paths handled automatically
- ⚠️ Bash tool requires Git Bash or WSL

The only limitation is the bash tool, which can be solved by:
1. Installing Git for Windows (recommended)
2. Using WSL (Windows Subsystem for Linux)
3. Disabling the bash tool in config

Everything else works identically to Linux/macOS! 🎉

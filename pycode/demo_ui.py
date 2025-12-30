"""
Enhanced UI Demo

Demonstrates PyCode's rich terminal UI features:
- Formatted panels and progress indicators
- Syntax-highlighted code display
- Color-coded tool execution
- Beautiful status messages
"""

import asyncio
from pycode.ui import get_ui


async def main():
    """Run UI feature demos"""

    ui = get_ui(verbose=True)

    print("\n" + "=" * 80)
    print("PyCode Enhanced Terminal UI Demo")
    print("=" * 80 + "\n")

    # Demo 1: Session Header
    print("\n[Demo 1: Session Header]\n")
    ui.print_header(
        agent_name="BuildAgent",
        tool_count=15,
        user_request="Create a Python script that calculates fibonacci numbers"
    )

    await asyncio.sleep(1)

    # Demo 2: Iteration Marker
    print("\n[Demo 2: Iteration Progress]\n")
    ui.print_iteration(1)

    await asyncio.sleep(0.5)

    # Demo 3: Tool Calls Notification
    print("\n[Demo 3: Tool Calls Notification]\n")
    ui.print_tool_calls(3)

    await asyncio.sleep(0.5)

    # Demo 4: Tool Execution - Write
    print("\n[Demo 4: Tool Execution Display]\n")
    ui.print_tool_execution(
        tool_name="write",
        tool_args={
            "file_path": "/tmp/fibonacci.py",
            "content": """def fibonacci(n):
    '''Calculate the nth fibonacci number'''
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test the function
for i in range(10):
    print(f'F({i}) = {fibonacci(i)}')
"""
        }
    )

    await asyncio.sleep(0.5)

    # Demo 5: Tool Result - Success
    print("\n[Demo 5: Tool Result - Success]\n")
    ui.print_tool_result(
        title="File written successfully",
        output="Created /tmp/fibonacci.py (237 bytes)",
        error=None
    )

    await asyncio.sleep(0.5)

    # Demo 6: Tool Execution - Bash
    print("\n[Demo 6: Tool Execution - Running Code]\n")
    ui.print_tool_execution(
        tool_name="bash",
        tool_args={
            "command": "python /tmp/fibonacci.py"
        }
    )

    await asyncio.sleep(0.5)

    # Demo 7: Tool Result with Code Output
    print("\n[Demo 7: Tool Result with Code Output]\n")
    code_output = """F(0) = 0
F(1) = 1
F(2) = 1
F(3) = 2
F(4) = 3
F(5) = 5
F(6) = 8
F(7) = 13
F(8) = 21
F(9) = 34"""

    ui.print_tool_result(
        title="Command executed successfully",
        output=code_output,
        error=None
    )

    await asyncio.sleep(0.5)

    # Demo 8: Syntax Highlighted Code
    print("\n[Demo 8: Syntax Highlighting]\n")
    python_code = """def merge_sort(arr):
    '''Implement merge sort algorithm'''
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result
"""

    ui.print_code(python_code, language="python", title="Merge Sort Implementation")

    await asyncio.sleep(0.5)

    # Demo 9: Error Result
    print("\n[Demo 9: Tool Result - Error]\n")
    ui.print_tool_result(
        title="Command failed",
        output=None,
        error="FileNotFoundError: [Errno 2] No such file or directory: '/nonexistent/file.py'"
    )

    await asyncio.sleep(0.5)

    # Demo 10: Doom Loop Warning
    print("\n[Demo 10: Doom Loop Detection]\n")
    ui.print_doom_loop("bash")

    await asyncio.sleep(0.5)

    # Demo 11: Completion
    print("\n[Demo 11: Task Completion]\n")
    ui.print_completion(iteration_count=3)

    await asyncio.sleep(0.5)

    # Demo 12: Max Iterations Warning
    print("\n[Demo 12: Max Iterations Warning]\n")
    ui.print_max_iterations(max_iterations=50)

    await asyncio.sleep(0.5)

    # Demo 13: LLM Error
    print("\n[Demo 13: LLM Error]\n")
    ui.print_llm_error("API Error: Rate limit exceeded (429)")

    await asyncio.sleep(0.5)

    # Demo 14: Table Display
    print("\n[Demo 14: Formatted Table]\n")
    ui.print_table(
        title="Available Tools",
        headers=["Tool", "Category", "Risk"],
        rows=[
            ["read", "File Operations", "Low"],
            ["write", "File Operations", "Medium"],
            ["bash", "Execution", "High"],
            ["grep", "Search", "Low"],
            ["edit", "File Operations", "Medium"],
        ]
    )

    await asyncio.sleep(0.5)

    # Demo 15: Markdown
    print("\n[Demo 15: Markdown Rendering]\n")
    markdown_text = """
# PyCode Features

PyCode now includes **enhanced terminal UI** with the following features:

1. **Rich Formatting**: Beautiful panels, tables, and syntax highlighting
2. **Progress Indicators**: Visual feedback for long-running operations
3. **Color Coding**: Risk-based color coding for tool operations
4. **Syntax Highlighting**: Automatic language detection and highlighting

## Code Example

```python
async def stream_response():
    async for chunk in provider.stream(...):
        yield chunk
```

> PyCode - Vibe coding in Python! 🚀
"""

    ui.print_markdown(markdown_text)

    await asyncio.sleep(0.5)

    # Demo 16: Progress Bar
    print("\n[Demo 16: Progress Indicator]\n")
    with ui.create_progress("Processing files...") as progress:
        task = progress.add_task("Processing", total=100)

        for i in range(100):
            await asyncio.sleep(0.02)
            progress.update(task, advance=1)

    await asyncio.sleep(0.5)

    # Demo 17: Spinner
    print("\n[Demo 17: Spinner for Indeterminate Progress]\n")
    ui.start_spinner("Analyzing code...")
    await asyncio.sleep(2)
    ui.stop_spinner()
    ui.print_status("✅ Analysis complete!", style="green")

    # Final message
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80 + "\n")

    ui.print_status(
        "✨ PyCode now has beautiful, informative terminal UI!",
        style="bold cyan"
    )


if __name__ == "__main__":
    asyncio.run(main())

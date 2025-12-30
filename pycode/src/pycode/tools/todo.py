"""Todo tool for task management within coding sessions"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Literal
from .base import Tool, ToolContext, ToolResult


class TodoTool(Tool):
    """Manage todos and tasks within a coding session"""

    @property
    def name(self) -> str:
        return "todo"

    @property
    def description(self) -> str:
        return """Manage todo items and track tasks during coding sessions.

Use this tool to:
- Create todo lists for complex tasks
- Track progress on multi-step operations
- Mark tasks as completed
- Review pending tasks
- Organize work systematically

Operations:
- list: Show all todos
- add: Add new todo item
- complete: Mark todo as done
- remove: Delete a todo
- clear: Clear all todos

Todo States:
- pending: Not started
- in_progress: Currently working on
- completed: Finished

Todos are session-specific and stored in .pycode/todos/

IMPORTANT:
- Todos persist across tool calls
- Use for complex multi-step tasks
- Mark tasks complete as you finish them
- Todos are stored per session
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Todo operation to perform",
                    "enum": ["list", "add", "complete", "remove", "clear", "update"],
                },
                "task": {
                    "type": "string",
                    "description": "Task description (for add operation)",
                },
                "task_id": {
                    "type": "number",
                    "description": "Task ID (for complete/remove/update operations)",
                },
                "status": {
                    "type": "string",
                    "description": "New status (for update operation)",
                    "enum": ["pending", "in_progress", "completed"],
                },
            },
            "required": ["operation"],
        }

    def _get_todo_file(self, session_id: str) -> Path:
        """Get path to todo file for session"""
        todo_dir = Path(".pycode/todos")
        todo_dir.mkdir(parents=True, exist_ok=True)
        return todo_dir / f"{session_id}.json"

    def _load_todos(self, session_id: str) -> list[dict]:
        """Load todos for session"""
        todo_file = self._get_todo_file(session_id)
        if not todo_file.exists():
            return []

        try:
            with open(todo_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("todos", [])
        except:
            return []

    def _save_todos(self, session_id: str, todos: list[dict]) -> None:
        """Save todos for session"""
        todo_file = self._get_todo_file(session_id)
        data = {
            "session_id": session_id,
            "updated_at": datetime.now().isoformat(),
            "todos": todos,
        }

        with open(todo_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _format_todo_list(self, todos: list[dict]) -> str:
        """Format todo list for display"""
        if not todos:
            return "No todos"

        lines = []
        pending = [t for t in todos if t["status"] == "pending"]
        in_progress = [t for t in todos if t["status"] == "in_progress"]
        completed = [t for t in todos if t["status"] == "completed"]

        if in_progress:
            lines.append("🔄 In Progress:")
            for todo in in_progress:
                lines.append(f"  [{todo['id']}] {todo['task']}")

        if pending:
            lines.append("\n📋 Pending:")
            for todo in pending:
                lines.append(f"  [{todo['id']}] {todo['task']}")

        if completed:
            lines.append("\n✅ Completed:")
            for todo in completed:
                lines.append(f"  [{todo['id']}] {todo['task']}")

        # Statistics
        lines.append(f"\nTotal: {len(todos)} tasks")
        lines.append(f"  Completed: {len(completed)}")
        lines.append(f"  In Progress: {len(in_progress)}")
        lines.append(f"  Pending: {len(pending)}")

        return "\n".join(lines)

    async def execute(self, parameters: dict[str, Any], context: ToolContext) -> ToolResult:
        operation: Literal["list", "add", "complete", "remove", "clear", "update"] = parameters["operation"]
        task = parameters.get("task")
        task_id = parameters.get("task_id")
        status = parameters.get("status")

        session_id = context.session_id
        todos = self._load_todos(session_id)

        try:
            if operation == "list":
                # List all todos
                output = self._format_todo_list(todos)
                return ToolResult(
                    title=f"Todos ({len(todos)})",
                    output=output,
                    metadata={
                        "total": len(todos),
                        "pending": len([t for t in todos if t["status"] == "pending"]),
                        "in_progress": len([t for t in todos if t["status"] == "in_progress"]),
                        "completed": len([t for t in todos if t["status"] == "completed"]),
                    },
                )

            elif operation == "add":
                # Add new todo
                if not task:
                    return ToolResult(title="Todo", output="", error="Task description required for add operation")

                next_id = max([t["id"] for t in todos], default=0) + 1
                new_todo = {
                    "id": next_id,
                    "task": task,
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                }

                todos.append(new_todo)
                self._save_todos(session_id, todos)

                return ToolResult(
                    title="Todo Added",
                    output=f"✅ Added task [{next_id}]: {task}",
                    metadata={"task_id": next_id, "task": task},
                )

            elif operation == "complete":
                # Mark todo as completed
                if task_id is None:
                    return ToolResult(
                        title="Todo", output="", error="Task ID required for complete operation"
                    )

                todo = next((t for t in todos if t["id"] == task_id), None)
                if not todo:
                    return ToolResult(title="Todo", output="", error=f"Task {task_id} not found")

                todo["status"] = "completed"
                todo["completed_at"] = datetime.now().isoformat()
                self._save_todos(session_id, todos)

                return ToolResult(
                    title="Todo Completed",
                    output=f"✅ Completed task [{task_id}]: {todo['task']}",
                    metadata={"task_id": task_id, "task": todo["task"]},
                )

            elif operation == "remove":
                # Remove todo
                if task_id is None:
                    return ToolResult(title="Todo", output="", error="Task ID required for remove operation")

                todo = next((t for t in todos if t["id"] == task_id), None)
                if not todo:
                    return ToolResult(title="Todo", output="", error=f"Task {task_id} not found")

                todos = [t for t in todos if t["id"] != task_id]
                self._save_todos(session_id, todos)

                return ToolResult(
                    title="Todo Removed",
                    output=f"🗑️  Removed task [{task_id}]: {todo['task']}",
                    metadata={"task_id": task_id, "task": todo["task"]},
                )

            elif operation == "update":
                # Update todo status
                if task_id is None:
                    return ToolResult(title="Todo", output="", error="Task ID required for update operation")

                if not status:
                    return ToolResult(title="Todo", output="", error="Status required for update operation")

                todo = next((t for t in todos if t["id"] == task_id), None)
                if not todo:
                    return ToolResult(title="Todo", output="", error=f"Task {task_id} not found")

                old_status = todo["status"]
                todo["status"] = status
                todo["updated_at"] = datetime.now().isoformat()
                self._save_todos(session_id, todos)

                status_icons = {"pending": "📋", "in_progress": "🔄", "completed": "✅"}
                icon = status_icons.get(status, "📝")

                return ToolResult(
                    title="Todo Updated",
                    output=f"{icon} Updated task [{task_id}]: {todo['task']}\n"
                    f"Status: {old_status} → {status}",
                    metadata={"task_id": task_id, "task": todo["task"], "old_status": old_status, "new_status": status},
                )

            elif operation == "clear":
                # Clear all todos
                todos_count = len(todos)
                todos = []
                self._save_todos(session_id, todos)

                return ToolResult(
                    title="Todos Cleared",
                    output=f"🗑️  Cleared {todos_count} todo(s)",
                    metadata={"cleared_count": todos_count},
                )

            else:
                return ToolResult(title="Todo", output="", error=f"Unknown operation: {operation}")

        except Exception as e:
            return ToolResult(title="Todo", output="", error=f"Failed to {operation} todo: {str(e)}")

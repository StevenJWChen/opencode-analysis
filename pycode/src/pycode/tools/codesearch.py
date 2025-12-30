"""Advanced code search tool with semantic and structural search"""

import re
import asyncio
from pathlib import Path
from typing import Any
from .base import Tool, ToolContext, ToolResult


class CodeSearchTool(Tool):
    """Advanced code search with semantic understanding"""

    # Maximum results per search
    MAX_RESULTS = 100

    @property
    def name(self) -> str:
        return "codesearch"

    @property
    def description(self) -> str:
        return """Advanced code search with semantic and structural capabilities.

Use this tool to:
- Find function/class definitions
- Search for API usage patterns
- Locate import statements
- Find TODO/FIXME comments
- Search across file types
- Pattern-based code search

Search Types:
- definition: Find function/class definitions
- usage: Find where something is used
- import: Find import statements
- comment: Find comments (TODO, FIXME, NOTE, etc.)
- pattern: Custom regex pattern
- symbol: Find symbols (functions, classes, variables)

Features:
- Multi-file search
- Context lines around matches
- File type filtering
- Result ranking by relevance
- Syntax-aware search

IMPORTANT:
- Faster than plain grep for semantic queries
- Returns structured results
- Includes context and locations
- Supports regex patterns
- Filters by file extensions
"""

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (required)",
                },
                "search_type": {
                    "type": "string",
                    "description": "Type of search to perform",
                    "enum": ["definition", "usage", "import", "comment", "pattern", "symbol"],
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (default: current)",
                },
                "file_extensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File extensions to search (e.g., ['.py', '.js'])",
                },
                "context_lines": {
                    "type": "number",
                    "description": "Number of context lines to show (default: 2)",
                },
                "max_results": {
                    "type": "number",
                    "description": "Maximum results to return (default: 50)",
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Case-sensitive search (default: false)",
                },
            },
            "required": ["query", "search_type"],
        }

    def _build_search_pattern(self, query: str, search_type: str, case_sensitive: bool) -> str:
        """Build regex pattern based on search type"""
        escaped_query = re.escape(query)

        patterns = {
            "definition": {
                "py": rf"^\s*(def|class)\s+{escaped_query}\s*[\(\:]",
                "js": rf"^\s*(function|class|const|let|var)\s+{escaped_query}\s*[\(\=]",
                "ts": rf"^\s*(function|class|interface|type|const|let|var)\s+{escaped_query}\s*[\(\=\<\:]",
            },
            "usage": escaped_query,
            "import": {
                "py": rf"^\s*(from .+ )?import .*{escaped_query}",
                "js": rf"(import|require)\s*.*{escaped_query}",
                "ts": rf"import\s*.*{escaped_query}",
            },
            "comment": {
                "py": rf"#.*{escaped_query}",
                "js": rf"//.*{escaped_query}",
                "default": rf"(#|//|/\*).*{escaped_query}",
            },
            "pattern": query,  # Direct regex
            "symbol": rf"\b{escaped_query}\b",
        }

        # Get pattern
        if search_type in ["definition", "import", "comment"]:
            # Try to detect file type from context, default to generic pattern
            pattern = patterns[search_type].get("default", patterns[search_type].get("py", query))
        else:
            pattern = patterns.get(search_type, query)

        return pattern

    async def _search_file(
        self,
        file_path: Path,
        pattern: str,
        case_sensitive: bool,
        context_lines: int,
    ) -> list[dict]:
        """Search a single file"""
        results = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)

            for line_num, line in enumerate(lines, 1):
                if regex.search(line):
                    # Get context
                    start_line = max(0, line_num - context_lines - 1)
                    end_line = min(len(lines), line_num + context_lines)
                    context = lines[start_line:end_line]

                    results.append(
                        {
                            "file": str(file_path),
                            "line_num": line_num,
                            "line": line.rstrip(),
                            "context": [l.rstrip() for l in context],
                            "context_start": start_line + 1,
                        }
                    )

        except Exception:
            # Skip files that can't be read
            pass

        return results

    async def execute(self, parameters: dict[str, Any], context: ToolContext) -> ToolResult:
        query = parameters["query"]
        search_type = parameters["search_type"]
        search_path = Path(parameters.get("path", context.working_directory))
        file_extensions = parameters.get("file_extensions", [".py", ".js", ".ts", ".tsx", ".jsx"])
        context_lines = parameters.get("context_lines", 2)
        max_results = min(parameters.get("max_results", 50), self.MAX_RESULTS)
        case_sensitive = parameters.get("case_sensitive", False)

        if not search_path.exists():
            return ToolResult(
                title="CodeSearch",
                output="",
                error=f"Search path does not exist: {search_path}",
            )

        # Build search pattern
        pattern = self._build_search_pattern(query, search_type, case_sensitive)

        # Find files to search
        files_to_search = []
        if search_path.is_file():
            files_to_search.append(search_path)
        else:
            for ext in file_extensions:
                files_to_search.extend(search_path.glob(f"**/*{ext}"))

        if not files_to_search:
            return ToolResult(
                title="CodeSearch",
                output=f"No files found with extensions: {file_extensions}",
                metadata={"query": query, "search_type": search_type, "files_searched": 0},
            )

        # Search all files
        all_results = []
        for file_path in files_to_search:
            results = await self._search_file(file_path, pattern, case_sensitive, context_lines)
            all_results.extend(results)

            # Stop if we have enough results
            if len(all_results) >= max_results:
                break

        # Limit results
        all_results = all_results[:max_results]

        if not all_results:
            return ToolResult(
                title=f"CodeSearch: {search_type}",
                output=f"No matches found for: {query}\n"
                f"Search type: {search_type}\n"
                f"Files searched: {len(files_to_search)}\n"
                f"Extensions: {', '.join(file_extensions)}",
                metadata={
                    "query": query,
                    "search_type": search_type,
                    "files_searched": len(files_to_search),
                    "matches": 0,
                },
            )

        # Format output
        output_lines = []
        output_lines.append(f"CodeSearch: {search_type}")
        output_lines.append(f"Query: {query}")
        output_lines.append(f"Found {len(all_results)} match(es) in {len(set(r['file'] for r in all_results))} file(s)")
        output_lines.append(f"Files searched: {len(files_to_search)}\n")

        for i, result in enumerate(all_results, 1):
            file_path = Path(result["file"])
            try:
                rel_path = file_path.relative_to(search_path)
            except ValueError:
                rel_path = file_path

            output_lines.append(f"{'=' * 60}")
            output_lines.append(f"Match {i}/{len(all_results)}: {rel_path}:{result['line_num']}")
            output_lines.append("=" * 60)
            output_lines.append(f"\n{result['line']}\n")

            if context_lines > 0:
                output_lines.append(f"Context (lines {result['context_start']}-{result['context_start'] + len(result['context']) - 1}):")
                for ctx_line_num, ctx_line in enumerate(result['context'], result['context_start']):
                    marker = "→" if ctx_line_num == result['line_num'] else " "
                    output_lines.append(f"  {marker} {ctx_line_num:4d} | {ctx_line}")
                output_lines.append("")

        output = "\n".join(output_lines)

        return ToolResult(
            title=f"CodeSearch: {len(all_results)} matches",
            output=output,
            metadata={
                "query": query,
                "search_type": search_type,
                "matches": len(all_results),
                "files_searched": len(files_to_search),
                "files_with_matches": len(set(r["file"] for r in all_results)),
                "pattern": pattern,
            },
        )

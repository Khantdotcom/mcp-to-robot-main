from __future__ import annotations

import json
import re
from pathlib import Path

from src.models import ToolCall
from src.parser.raw_parser import extract_playwright

_TOOL_RE = re.compile(r"🔧 MCP tools/call → (?P<name>\w+)\((?P<args>.*?)\)\s*\n\s*✅ Result:", re.DOTALL)


class ExecutionParser:
    """Parse human-readable MCP execution logs."""

    def parse(self, path: str | Path) -> list[ToolCall]:
        return self.parse_text(Path(path).read_text(encoding="utf-8"))

    def parse_text(self, text: str) -> list[ToolCall]:
        matches = list(_TOOL_RE.finditer(text))
        calls: list[ToolCall] = []
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            raw_args = match.group("args").strip()
            try:
                args = json.loads(raw_args) if raw_args else {}
            except json.JSONDecodeError:
                args = {}
            result = text[match.end() : end].strip()
            calls.append(
                ToolCall(
                    name=match.group("name"),
                    args=args,
                    result=result,
                    playwright=extract_playwright(result),
                )
            )
        return calls

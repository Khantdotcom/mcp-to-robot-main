from __future__ import annotations

import json
import re
from pathlib import Path

from src.models import ToolCall

_CALL_RE = re.compile(r"^\[(?P<ts>[^\]]+)\]\s+CALL\s+(?P<name>\w+)\s*$", re.MULTILINE)
_RESULT_RE = re.compile(r"^\[(?P<ts>[^\]]+)\]\s+RESULT\s+\(is_error=(?P<err>True|False)\)\s*$", re.MULTILINE)
_JS_BLOCK_RE = re.compile(r"```js\s*(.*?)\s*```", re.DOTALL)


def _extract_json_object(text: str, start: int) -> tuple[dict, int]:
    marker = "ARGS"
    args_at = text.find(marker, start)
    if args_at < 0:
        return {}, start
    brace_at = text.find("{", args_at)
    if brace_at < 0:
        return {}, args_at + len(marker)
    depth = 0
    in_string = False
    escape = False
    for idx in range(brace_at, len(text)):
        ch = text[idx]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                raw = text[brace_at : idx + 1]
                return json.loads(raw), idx + 1
    raise ValueError("Unterminated ARGS JSON object")


def extract_playwright(result: str) -> list[str]:
    statements: list[str] = []
    for block in _JS_BLOCK_RE.findall(result):
        for statement in block.splitlines():
            statement = statement.strip()
            if statement.startswith("await page."):
                statements.append(statement.rstrip(";"))
    return statements


class RawParser:
    """Parse RAW MCP Tool Calls logs into ordered tool calls."""

    def parse(self, path: str | Path) -> list[ToolCall]:
        text = Path(path).read_text(encoding="utf-8")
        return self.parse_text(text)

    def parse_text(self, text: str) -> list[ToolCall]:
        calls = list(_CALL_RE.finditer(text))
        parsed: list[ToolCall] = []
        for index, match in enumerate(calls):
            next_call_start = calls[index + 1].start() if index + 1 < len(calls) else len(text)
            args, args_end = _extract_json_object(text, match.end())
            result_match = _RESULT_RE.search(text, args_end, next_call_start)
            result = ""
            is_error = False
            if result_match:
                result_start = result_match.end()
                sep = text.find("------------------------------------------------------------", result_start, next_call_start)
                result_end = sep if sep >= 0 else next_call_start
                result = text[result_start:result_end].strip()
                is_error = result_match.group("err") == "True"
            parsed.append(
                ToolCall(
                    name=match.group("name"),
                    args=args,
                    timestamp=match.group("ts"),
                    result=result,
                    is_error=is_error,
                    playwright=extract_playwright(result),
                )
            )
        return parsed

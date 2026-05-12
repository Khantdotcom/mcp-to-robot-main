from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.models import Report, ScenarioMeta


class ReportParser:
    """Parse execution report JSON and expose scenario metadata."""

    def parse(self, path: str | Path) -> Report:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return self.parse_data(data)

    def parse_data(self, data: dict[str, Any]) -> Report:
        scenarios = [ScenarioMeta(**item) for item in data.get("scenarios", [])]
        return Report(
            test_set=data.get("test_set", ""),
            result=data.get("result", ""),
            scenarios=scenarios,
            timeline=data.get("timeline", []),
        )

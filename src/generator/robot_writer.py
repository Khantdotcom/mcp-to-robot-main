from __future__ import annotations

from pathlib import Path

from src.models import RobotSuite


class RobotWriter:
    """Render and write Robot Framework suites."""

    def render(self, suite: RobotSuite) -> str:
        lines = ["*** Settings ***", f"Library    {suite.library}", "", "*** Test Cases ***"]
        for index, test_case in enumerate(suite.test_cases):
            if index:
                lines.append("")
            lines.append(test_case.name)
            for step in test_case.steps:
                lines.append(step.render())
        return "\n".join(lines) + "\n"

    def write(self, suite: RobotSuite, output_dir: str | Path) -> Path:
        output_path = suite.output_path(Path(output_dir))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render(suite), encoding="utf-8")
        return output_path

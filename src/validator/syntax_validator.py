from __future__ import annotations

from pathlib import Path

from src.models import RobotStep, RobotSuite
from src.transformer.playwright_to_robot import normalize_selector

try:
    from robot.api import get_model
except ImportError:  # pragma: no cover - dependency is declared; fallback supports constrained envs.
    get_model = None


class SyntaxValidator:
    """Validate rendered Robot syntax and generated step quality."""

    def validate_robot_file(self, path: str | Path) -> list[str]:
        if get_model is None:
            text = Path(path).read_text(encoding="utf-8")
            required = ["*** Settings ***", "*** Test Cases ***"]
            return [f"Missing section {section}" for section in required if section not in text]
        errors = get_model(str(path)).errors
        return [str(error) for error in errors]

    def validate_suite(self, suite: RobotSuite) -> list[str]:
        issues: list[str] = []
        for test_case in suite.test_cases:
            seen: set[tuple[str, tuple[str, ...]]] = set()
            for step in test_case.steps:
                key = (step.keyword, tuple(step.args))
                if key in seen and step.keyword not in {"New Page"}:
                    issues.append(f"Duplicate step in {test_case.name}: {step.keyword} {step.args}")
                seen.add(key)
                issues.extend(self.validate_step(step))
        return issues

    def validate_step(self, step: RobotStep) -> list[str]:
        issues: list[str] = []
        if step.keyword in {"Fill Text", "Click", "Get Text", "Wait For Elements State"} and not step.args:
            issues.append(f"Missing selector for {step.keyword}")
        if step.args and step.keyword in {"Fill Text", "Click", "Get Text", "Wait For Elements State"}:
            selector = step.args[0]
            if selector.startswith("#"):
                issues.append(f"Unnormalized selector {selector}; use {normalize_selector(selector)}")
        return issues

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, get_args, get_origin

try:
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover - lets local tests run before dependencies are installed.
    _MISSING = object()

    def Field(default: Any = _MISSING, default_factory: Any = None) -> Any:  # noqa: N802
        if default_factory is not None:
            return default_factory()
        return None if default is _MISSING else default

    class BaseModel:
        def __init__(self, **data: Any) -> None:
            annotations = getattr(self, "__annotations__", {})
            for name, annotation in annotations.items():
                if name in data:
                    value = data[name]
                elif hasattr(self.__class__, name):
                    class_value = getattr(self.__class__, name)
                    value = class_value.copy() if isinstance(class_value, list | dict | set) else class_value
                else:
                    value = None
                setattr(self, name, self._coerce(annotation, value))
            for name, value in data.items():
                if name not in annotations:
                    setattr(self, name, value)

        @classmethod
        def _coerce(cls, annotation: Any, value: Any) -> Any:
            origin = get_origin(annotation)
            args = get_args(annotation)
            if origin is list and args and isinstance(value, list):
                subtype = args[0]
                if isinstance(subtype, type) and issubclass(subtype, BaseModel):
                    return [item if isinstance(item, subtype) else subtype(**item) for item in value]
            return value


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    timestamp: str | None = None
    result: str = ""
    is_error: bool = False
    playwright: list[str] = Field(default_factory=list)


class ScenarioMeta(BaseModel):
    id: str
    name: str
    passed: bool = False
    actions: int = 0
    errors: int = 0


class Report(BaseModel):
    test_set: str = ""
    result: str = ""
    scenarios: list[ScenarioMeta] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)


class RobotStepType(str, Enum):
    NEW_BROWSER = "New Browser"
    NEW_PAGE = "New Page"
    FILL_TEXT = "Fill Text"
    CLICK = "Click"
    WAIT_VISIBLE = "Wait For Elements State"
    GET_TEXT = "Get Text"
    CLOSE_BROWSER = "Close Browser"


class RobotStep(BaseModel):
    keyword: str
    args: list[str] = Field(default_factory=list)
    source: str = ""

    def render(self) -> str:
        if self.args:
            return "    " + self.keyword + "    " + "    ".join(self.args)
        return "    " + self.keyword


class RobotTestCase(BaseModel):
    name: str
    steps: list[RobotStep] = Field(default_factory=list)


class RobotSuite(BaseModel):
    name: str = "login_tests"
    library: str = "Browser"
    test_cases: list[RobotTestCase] = Field(default_factory=list)

    def output_path(self, output_dir: Path) -> Path:
        return output_dir / f"{self.name}.robot"

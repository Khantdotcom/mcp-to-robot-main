from __future__ import annotations

import re
from collections.abc import Iterable

from src.models import Report, RobotStep, RobotSuite, RobotTestCase, ToolCall

_GOTO_RE = re.compile(
    r"page\.goto\((?P<quote>['\"])(?P<url>.*?)(?P=quote)\)"
)

_LOCATOR_FILL_RE = re.compile(
    r"page\.locator\((?P<lq>['\"])(?P<selector>.*?)(?P=lq)\)"
    r"\.fill\((?P<vq>['\"])(?P<value>.*?)(?P=vq)\)"
)

_ROLE_CLICK_RE = re.compile(
    r"page\.getByRole\((?P<rq>['\"])(?P<role>.*?)(?P=rq),"
    r"\s*\{\s*name:\s*(?P<nq>['\"])(?P<name>.*?)(?P=nq)\s*}\)"
    r"\.click\("
)

_ROLE_FILL_RE = re.compile(
    r"page\.getByRole\((?P<rq>['\"])(?P<role>.*?)(?P=rq),"
    r"\s*\{\s*name:\s*(?P<nq>['\"])(?P<name>.*?)(?P=nq)\s*}\)"
    r"\.fill\((?P<vq>['\"])(?P<value>.*?)(?P=vq)\)"
)

# Map accessible labels to stable DOM ids
LABEL_TO_ID = {
    "Firstname: *": "first-name",
    "Lastname: *": "last-name",
}


class PlaywrightToRobotTransformer:
    """Convert parsed Playwright operations into Robot Framework Browser tests."""

    def transform(self, raw_calls: list[ToolCall], report: Report) -> RobotSuite:
        scenario_ids = [scenario.id for scenario in report.scenarios] or [
            "Generated Test"
        ]

        grouped_calls = self._group_calls(raw_calls, len(scenario_ids))

        suite = RobotSuite()

        for scenario_id, calls in zip(
            scenario_ids,
            grouped_calls,
            strict=False,
        ):
            steps = [
                RobotStep(
                    keyword="New Browser",
                    args=["chromium"],
                    source="setup",
                )
            ]

            for call in calls:
                for statement in call.playwright:
                    steps.extend(self.statement_to_steps(statement))

                steps.extend(self.result_to_assertions(call))

            steps.append(
                RobotStep(
                    keyword="Close Browser",
                    source="teardown",
                )
            )

            suite.test_cases.append(
                RobotTestCase(
                    name=scenario_id,
                    steps=self._dedupe_steps(steps),
                )
            )

        return suite

    def statement_to_steps(self, statement: str) -> list[RobotStep]:

        # page.goto(...)
        if match := _GOTO_RE.search(statement):
            return [
                RobotStep(
                    keyword="New Page",
                    args=[match.group("url")],
                    source=statement,
                )
            ]

        # page.locator(...).fill(...)
        if match := _LOCATOR_FILL_RE.search(statement):
            return [
                RobotStep(
                    keyword="Fill Text",
                    args=[
                        normalize_selector(match.group("selector")),
                        unescape_js(match.group("value")),
                    ],
                    source=statement,
                )
            ]

        # page.getByRole(...).fill(...)
        if match := _ROLE_FILL_RE.search(statement):

            label = match.group("name")

            selector = (
                f"id={LABEL_TO_ID[label]}"
                if label in LABEL_TO_ID
                else f"label={label}"
            )

            return [
                RobotStep(
                    keyword="Fill Text",
                    args=[
                        selector,
                        unescape_js(match.group("value")),
                    ],
                    source=statement,
                )
            ]

        # page.getByRole(...).click(...)
        if match := _ROLE_CLICK_RE.search(statement):
            return [
                RobotStep(
                    keyword="Click",
                    args=[f"text={match.group('name')}"],
                    source=statement,
                )
            ]

        return []

    def result_to_assertions(self, call: ToolCall) -> list[RobotStep]:

        result = call.result
        assertions: list[RobotStep] = []

        if (
            call.name == "browser_click"
            and "Page URL: https://automationplayground.github.io/playground/home.html"
            in result
        ):
            assertions.append(
                RobotStep(
                    keyword="Wait For Elements State",
                    args=[
                        "text=Personal Profile",
                        "visible",
                    ],
                    source="home page assertion",
                )
            )

        if "Invalid Login" in result:
            assertions.append(
                RobotStep(
                    keyword="Get Text",
                    args=["text=Invalid Login"],
                    source="invalid login assertion",
                )
            )

        return assertions

    def _group_calls(
        self,
        calls: list[ToolCall],
        expected_groups: int,
    ) -> list[list[ToolCall]]:

        groups: list[list[ToolCall]] = []
        current: list[ToolCall] = []

        for call in calls:

            starts_new = (
                call.name == "browser_navigate"
                and current
                and len(groups) < expected_groups - 1
            )

            if starts_new:
                groups.append(current)
                current = []

            if call.playwright or call.name.startswith("browser_"):
                current.append(call)

        if current:
            groups.append(current)

        while len(groups) < expected_groups:
            groups.append([])

        return groups[:expected_groups]

    def _dedupe_steps(
        self,
        steps: Iterable[RobotStep],
    ) -> list[RobotStep]:

        deduped: list[RobotStep] = []

        for step in steps:

            if (
                deduped
                and step.keyword == deduped[-1].keyword
                and step.args == deduped[-1].args
            ):
                continue

            deduped.append(step)

        return deduped


def normalize_selector(selector: str) -> str:

    if selector.startswith("#") and len(selector) > 1:
        return f"id={selector[1:]}"

    if selector.startswith(".") and len(selector) > 1:
        return f"css={selector}"

    return selector


def unescape_js(value: str) -> str:

    return (
        value.replace("\\'", "'")
        .replace('\\"', '"')
        .replace("\\n", "\n")
    )
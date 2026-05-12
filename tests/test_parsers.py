from pathlib import Path

from src.parser.execution_parser import ExecutionParser
from src.parser.raw_parser import RawParser
from src.parser.report_parser import ReportParser

FIXTURES = Path(__file__).parent / "fixtures"


def test_raw_parser_extracts_ordered_tool_calls_and_playwright() -> None:
    calls = RawParser().parse(FIXTURES / "mcp_raw.log")
    assert len(calls) == 9
    assert calls[0].name == "browser_navigate"
    assert calls[0].args["url"].endswith("login.html")
    assert calls[1].playwright == [
        "await page.locator('#inp_username').fill('username')",
        "await page.locator('#inp_password').fill('P@ssw0rd')",
    ]


def test_execution_parser_extracts_human_log_calls() -> None:
    calls = ExecutionParser().parse(FIXTURES / "mcp_execution.log")
    assert [call.name for call in calls] == ["browser_navigate", "browser_type"]
    assert calls[1].args["text"] == "username"
    assert calls[1].playwright == ["await page.locator('#inp_username').fill('username')"]


def test_report_parser_uses_report_scenarios() -> None:
    report = ReportParser().parse(FIXTURES / "report.json")
    assert report.result == "passed"
    assert [scenario.id for scenario in report.scenarios] == ["SCN_LOGIN_POS_00001", "SCN_LOGIN_NEG_00001"]

from pathlib import Path

from src.parser.raw_parser import RawParser
from src.parser.report_parser import ReportParser
from src.transformer.playwright_to_robot import PlaywrightToRobotTransformer, normalize_selector

FIXTURES = Path(__file__).parent / "fixtures"


def test_selector_normalization() -> None:
    assert normalize_selector("#inp_username") == "id=inp_username"
    assert normalize_selector(".primary") == "css=.primary"


def test_transformer_groups_positive_and_negative_scenarios() -> None:
    suite = PlaywrightToRobotTransformer().transform(
        RawParser().parse(FIXTURES / "mcp_raw.log"),
        ReportParser().parse(FIXTURES / "report.json"),
    )
    assert [case.name for case in suite.test_cases] == ["SCN_LOGIN_POS_00001", "SCN_LOGIN_NEG_00001"]
    positive_steps = [step.render() for step in suite.test_cases[0].steps]
    negative_steps = [step.render() for step in suite.test_cases[1].steps]
    assert "    Wait For Elements State    text=Personal Profile    visible" in positive_steps
    assert "    Fill Text    name=Lastname: *    Doe" in positive_steps
    assert "    Get Text    text=Invalid Login" in negative_steps

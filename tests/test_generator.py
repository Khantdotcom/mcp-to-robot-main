from src.generator.robot_writer import RobotWriter
from src.models import RobotStep, RobotSuite, RobotTestCase
from src.validator.syntax_validator import SyntaxValidator


def test_robot_writer_renders_valid_suite(tmp_path) -> None:
    suite = RobotSuite(test_cases=[RobotTestCase(name="Example", steps=[RobotStep(keyword="New Browser", args=["chromium"])])])
    writer = RobotWriter()
    output = writer.write(suite, tmp_path)
    assert output.read_text(encoding="utf-8") == "*** Settings ***\nLibrary    Browser\n\n*** Test Cases ***\nExample\n    New Browser    chromium\n"
    assert SyntaxValidator().validate_robot_file(output) == []


def test_validator_detects_duplicate_steps() -> None:
    suite = RobotSuite(test_cases=[RobotTestCase(name="Example", steps=[RobotStep(keyword="Click", args=["text=Save"]), RobotStep(keyword="Click", args=["text=Save"])])])
    assert SyntaxValidator().validate_suite(suite) == ["Duplicate step in Example: Click ['text=Save']"]

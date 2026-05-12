import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_convert_generates_expected_robot(tmp_path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.cli",
            "convert",
            "--execution", str(FIXTURES / "mcp_execution.log"),
            "--raw", str(FIXTURES / "mcp_raw.log"),
            "--report", str(FIXTURES / "report.json"),
            "--output", str(tmp_path),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    actual = (tmp_path / "login_tests.robot").read_text(encoding="utf-8")
    expected = (FIXTURES / "expected_login_tests.robot").read_text(encoding="utf-8")
    assert actual == expected

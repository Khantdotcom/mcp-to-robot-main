from __future__ import annotations

import argparse
from pathlib import Path

try:
    import typer
except ImportError:  # pragma: no cover - dependency is declared; argparse fallback supports constrained envs.
    typer = None

from src.generator.robot_writer import RobotWriter
from src.parser.execution_parser import ExecutionParser
from src.parser.raw_parser import RawParser
from src.parser.report_parser import ReportParser
from src.transformer.playwright_to_robot import PlaywrightToRobotTransformer
from src.validator.syntax_validator import SyntaxValidator

if typer is not None:
    app = typer.Typer(help="Convert MCP Playwright artifacts into Robot Framework Browser suites.")
else:
    app = None


def convert_artifacts(execution: Path, raw: Path, report: Path, output: Path) -> Path:
    execution_calls = ExecutionParser().parse(execution)
    raw_calls = RawParser().parse(raw)
    report_model = ReportParser().parse(report)
    if not raw_calls and execution_calls:
        raw_calls = execution_calls

    suite = PlaywrightToRobotTransformer().transform(raw_calls, report_model)
    suite_issues = SyntaxValidator().validate_suite(suite)
    if suite_issues:
        raise ValueError("; ".join(suite_issues))

    path = RobotWriter().write(suite, output)
    syntax_errors = SyntaxValidator().validate_robot_file(path)
    if syntax_errors:
        raise ValueError("; ".join(syntax_errors))
    return path


if typer is not None:
    @app.command()
    def convert(
        execution: Path = typer.Option(..., "--execution", exists=True, readable=True, help="MCP execution log."),
        raw: Path = typer.Option(..., "--raw", exists=True, readable=True, help="Raw MCP tool call log."),
        report: Path = typer.Option(..., "--report", exists=True, readable=True, help="Execution report JSON."),
        output: Path = typer.Option(Path("generated"), "--output", help="Output directory for generated .robot files."),
    ) -> None:
        """Convert the three MCP artifact files into a Robot Framework suite."""
        try:
            path = convert_artifacts(execution, raw, report, output)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        typer.echo(f"Generated {path}")


def _argparse_main() -> None:
    parser = argparse.ArgumentParser(description="Convert MCP Playwright artifacts into Robot Framework Browser suites.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    convert_parser = subparsers.add_parser("convert")
    convert_parser.add_argument("--execution", required=True, type=Path)
    convert_parser.add_argument("--raw", required=True, type=Path)
    convert_parser.add_argument("--report", required=True, type=Path)
    convert_parser.add_argument("--output", default=Path("generated"), type=Path)
    args = parser.parse_args()
    path = convert_artifacts(args.execution, args.raw, args.report, args.output)
    print(f"Generated {path}")


def main() -> None:
    if typer is not None:
        app()
    else:
        _argparse_main()


if __name__ == "__main__":
    main()

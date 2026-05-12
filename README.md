# MCP to Robot

`mcp-to-robot` converts MCP Playwright execution artifacts into executable Robot Framework Browser test suites.

It consumes three files from an MCP run:

1. A human-readable MCP execution log.
2. A raw MCP tool-call log containing Playwright snippets.
3. A JSON execution report whose scenario list is the authoritative test-case grouping source.

The converter recognizes the sample login flow patterns and emits production-ready `.robot` suites using the Robot Framework `Browser` library.

## Features

- Parses MCP execution logs and raw tool-call logs.
- Extracts Playwright statements from fenced JavaScript result blocks.
- Converts supported Playwright operations into Robot Browser keywords:
  - `page.goto(...)` → `New Page`
  - `page.locator('#id').fill(...)` → `Fill Text    id=...`
  - `page.getByRole('textbox', { name: ... }).fill(...)` → `Fill Text    name=...`
  - `page.getByRole('button', { name: ... }).click()` → `Click    text=...`
- Uses report JSON scenario IDs such as `SCN_LOGIN_POS_00001` and `SCN_LOGIN_NEG_00001` for generated test names.
- Adds behavior-preserving assertions for the provided patterns:
  - successful login waits for `Personal Profile`
  - failed login verifies `Invalid Login`
- Validates Robot Framework syntax and duplicate generated steps.

## Requirements

- Python 3.12+
- Robot Framework
- Robot Framework Browser
- Node.js dependencies required by `robotframework-browser` for real browser execution

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
rfbrowser init
```

If you only want to run parser/generator unit tests and not real browsers, installing `requirements.txt` is sufficient:

```bash
pip install -r requirements.txt
```

## CLI Usage

```bash
mcp2robot convert \
  --execution tests/fixtures/mcp_execution.log \
  --raw tests/fixtures/mcp_raw.log \
  --report tests/fixtures/report.json \
  --output generated/
```

Equivalent module invocation:

```bash
python -m src.cli convert \
  --execution tests/fixtures/mcp_execution.log \
  --raw tests/fixtures/mcp_raw.log \
  --report tests/fixtures/report.json \
  --output generated/
```

Example terminal output:

```text
Generated generated/login_tests.robot
```

## Running Generated Tests

```bash
robot generated/login_tests.robot
```

The generated suite opens Chromium, reproduces the positive login scenario, verifies the profile page, fills the profile fields, then reproduces the negative login scenario and verifies `Invalid Login`.

## Sample Generated Output

See [`generated/login_tests.robot`](generated/login_tests.robot):

```robot
*** Settings ***
Library    Browser

*** Test Cases ***
SCN_LOGIN_POS_00001
    New Browser    chromium
    New Page    https://automationplayground.github.io/playground/login.html
    Fill Text    id=inp_username    username
    Fill Text    id=inp_password    P@ssw0rd
    Click    text=Sign In
    Wait For Elements State    text=Personal Profile    visible
    Fill Text    name=Firstname: *    John
    Fill Text    name=Lastname: *    Doe
    Close Browser

SCN_LOGIN_NEG_00001
    New Browser    chromium
    New Page    https://automationplayground.github.io/playground/login.html
    Fill Text    id=inp_username    username
    Fill Text    id=inp_password    WrongP@ss
    Click    text=Sign In
    Get Text    text=Invalid Login
    Close Browser
```

## Development

Run automated tests:

```bash
pytest
```

Run conversion smoke test:

```bash
python -m src.cli convert --execution tests/fixtures/mcp_execution.log --raw tests/fixtures/mcp_raw.log --report tests/fixtures/report.json --output generated/
```

Validate generated Robot syntax:

```bash
python - <<'PY'
from src.validator.syntax_validator import SyntaxValidator
print(SyntaxValidator().validate_robot_file('generated/login_tests.robot'))
PY
```

## Project Structure

```text
mcp-to-robot/
├── src/
│   ├── parser/
│   ├── transformer/
│   ├── generator/
│   ├── validator/
│   └── cli.py
├── tests/
│   ├── fixtures/
│   ├── test_parsers.py
│   ├── test_transformer.py
│   ├── test_generator.py
│   └── integration_test.py
├── generated/
├── requirements.txt
├── README.md
└── pyproject.toml
```

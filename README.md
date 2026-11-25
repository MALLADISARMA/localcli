# LocalCI

LocalCI is a free, offline-first command-line tool for running common CI checks
locally. Its long-term goal is to help developers run linting, tests, and build
verification for their projects from one command, without requiring a hosted
CI service.

This repository currently implements **Phase 1 (CLI foundation)** and
**Phase 2 (Pipeline Execution Engine)**. It provides working `init`, `run`, and
`clean` commands. Execution history (`status`) is planned for Phase 4 and
currently displays a placeholder notice.

LocalCI works completely offline and locally. It does not require AI, cloud
services, API keys, or network access.

## Technology stack

- **Language:** Python 3.10 or newer
- **Standard library modules:** `argparse`, `json`, `pathlib`, `shlex`,
  `subprocess`, `time`, and `unittest`
- **Runtime dependencies:** Python standard library only (zero third-party
  runtime dependencies)
- **Packaging:** `pyproject.toml` with a `localci` console entry point
- **Continuous integration:** GitHub Actions runs the unit tests on Python
  3.10–3.13 for pushes and pull requests targeting `main`

## Installation

From the repository root, install `localci` in editable mode:

```powershell
python -m pip install -e .
```

If you want to run `localci` inside a separate project's virtual environment,
activate that environment and install from this repository path:

```powershell
python -m pip install -e E:\pipeline-cli
```

## Commands

- `localci --help` displays help and available subcommands.
- `localci --version` displays `LocalCI version 0.1.0`.
- `localci init` creates `.localci.json` in the current directory using that
  directory's name as the project name. It never overwrites an existing file.
- `localci run` loads and validates `.localci.json`, runs configured stages
  sequentially, captures stdout/stderr, enforces timeouts, and prints a summary.
- `localci status` prints a Phase 4 placeholder notice (execution history is
  not implemented yet).
- `localci clean` asks for confirmation before deleting only `.localci.json`.
- `localci clean --yes` skips the confirmation prompt.

## Configuration format

LocalCI reads `.localci.json` from the current working directory. Because
project and language detection are not implemented yet, pipeline stages and
commands must be configured manually.

`localci init` creates a starter file with an empty `stages` list (`[]`), which
is valid and exits with `0` until you add stages:

```json
{
    "version": "1.0",
    "project": "my-project",
    "settings": {
        "stop_on_failure": true,
        "default_timeout": 300
    },
    "stages": [
        {
            "name": "Unit Tests",
            "command": [
                "python",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests"
            ]
        },
        {
            "name": "Build",
            "command": [
                "python",
                "-m",
                "compileall",
                "."
            ],
            "timeout": 120
        }
    ]
}
```

### Field rules

- `version`: non-empty string.
- `project`: non-empty string.
- `settings`: JSON object containing:
  - `stop_on_failure`: boolean (`true` or `false`).
  - `default_timeout`: positive integer in seconds (booleans are rejected).
- `stages`: list of stage objects (`[]` is valid). Each stage object requires:
  - `name`: non-empty string.
  - `command`: non-empty list of non-empty strings.
  - `timeout` (optional): positive integer in seconds overriding
    `default_timeout` for that stage (booleans are rejected).

Invalid JSON, missing required fields, wrong types, or invalid timeouts abort
execution before any stage runs.

## How local commands execute

- **No shell execution:** Commands run directly from the project's root
  directory using `subprocess.run(..., shell=False)`. Shell operators such as
  `&&`, `|`, and redirection (`>`) are not supported; pass commands as JSON
  argument arrays instead.
- **Timeouts:** If a stage exceeds its `timeout` (or `settings.default_timeout`),
  the subprocess is terminated, a timeout message is shown, and the stage is
  marked `FAILED`.
- **`stop_on_failure`:** When `true`, the first failing stage causes all
  remaining stages to be marked `SKIPPED`. When `false`, execution continues
  through every stage.
- **Virtual environments & Windows tips:**
  - If a target project uses its own virtual environment, point `"command"` to
    that environment's Python executable (e.g.
    `[".venv\\Scripts\\python.exe", "-m", "pytest"]` on Windows or
    `[".venv/bin/python", "-m", "pytest"]` on Linux/macOS).
  - If a project's `tests/` folder does not have `__init__.py`, prefer
    `["python", "-m", "pytest"]` or add `tests/__init__.py` when using
    `python -m unittest discover -s tests -t .`.
  - On Windows, batch-wrapped tools such as `npm` may need `.cmd`
    (`["npm.cmd", "test"]`) when run with `shell=False`.

## Exit codes

- `0`: All stages passed or no stages configured.
- `1`: At least one stage failed (or general filesystem/execution error).
- `2`: Invalid JSON or configuration validation error.
- `3`: Missing `.localci.json` or required executable not found.
- `130`: Operation interrupted by the user (`Ctrl+C`).

## Example workflow

```powershell
cd C:\path\to\your-project
localci init
# Edit .localci.json to add stages
localci run
localci clean
```

Example `localci run` output:

```text
========================================
            LOCALCI PIPELINE
========================================

Project: my-project
Total stages: 2

[1/2] Unit Tests
----------------------------------------
Command: python -m unittest discover -s tests
Executing command...

Status: PASSED
Duration: 0.12 seconds

[2/2] Build
----------------------------------------
Command: python -m compileall .
Executing command...

Status: PASSED
Duration: 0.08 seconds

========================================
            PIPELINE SUMMARY
========================================

Total stages : 2
Passed       : 2
Failed       : 0
Skipped      : 0

Overall Status: SUCCESS

========================================
```

## Project structure

```text
localci/
├── __init__.py          # Package version (0.1.0)
├── cli.py               # Argument parser and command dispatch
├── main.py              # Console entry point
├── commands/            # Subcommand handlers (init, run, status, clean)
├── core/
│   ├── config_loader.py # .localci.json loading and schema validation
│   ├── executor.py      # Safe subprocess execution (shell=False)
│   └── runner.py        # Sequential stage execution and summary output
└── utils/
    ├── constants.py     # Exit codes and config filename constant
    └── exceptions.py    # LocalCIError with exit code support
tests/                   # Standard-library unittest suite
```

## Current limitations and roadmap

- **Phase 1 (Complete):** CLI foundation (`init`, `clean`, `--help`, `--version`).
- **Phase 2 (Complete):** Pipeline execution engine (`run`, config validation,
  sequential stage execution, timeouts, failure handling, summary).
- **Not implemented yet:**
  - Project/language auto-detection (stages must be configured manually).
  - Execution history persistence (`localci status` remains a Phase 4
    placeholder).
  - Language-specific adapters, Git integration, reports, parallel execution,
    dependency graphs, Docker, and AI features.

## Tests

Run the standard-library unit tests with:

```powershell
python -m unittest discover -s tests -v
```

The test suite contains 39 unit tests covering CLI dispatch, `init`, `clean`,
configuration validation, command execution, and pipeline runner behavior.
GitHub Actions runs this suite on pushes and pull requests targeting `main`.

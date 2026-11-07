# LocalCI

LocalCI is a free, offline-first command-line tool for running common CI checks
locally. Its long-term goal is to help developers run linting, tests, and build
verification for their projects from one command, without requiring a hosted
CI service.

This repository currently contains **Phase 1: the CLI foundation**. It provides
the `init`, `run`, `status`, and `clean` commands. Pipeline execution and
execution history are not implemented yet: `run` and `status` print notices
about their planned phases.

LocalCI is designed to work locally and offline. It does not require AI, cloud
services, API keys, or network access to run its Phase 1 commands.

## Technology stack

- **Language:** Python 3.10 or newer
- **Command-line parsing:** `argparse`
- **Filesystem paths and configuration:** `pathlib` and `json`
- **Tests:** Python's built-in `unittest`
- **Runtime dependencies:** Python standard library only
- **Packaging:** `pyproject.toml` with a `localci` console entry point
- **Continuous integration:** GitHub Actions runs the unit tests on Python
  3.10–3.13 for pushes and pull requests targeting `main`

## Installation

From the repository root, install the command in editable mode:

```powershell
python -m pip install -e .
```

## Commands

- `localci --help` displays help.
- `localci --version` displays the installed version.
- `localci init` creates `.localci.json` in the current directory using that
  directory's name as the project name. It never replaces an existing file.
- `localci run` prints a placeholder; pipeline execution is planned for Phase 2.
- `localci status` prints a placeholder; execution history is planned for
  Phase 4.
- `localci clean` asks for confirmation before deleting only `.localci.json`.
- `localci clean --yes` skips the confirmation prompt.

## Example

Run commands from the project directory you want LocalCI to manage. For example:

```powershell
cd C:\path\to\your-project
localci init
Get-Content .localci.json
localci clean
```

The `init` command creates a starter configuration containing the project name,
settings, and an empty stages list. The `clean` command removes only that
configuration file; it leaves other project files untouched.

## Scope and future phases

Phase 1 does not run pipelines or record execution history. Future phases may
add those capabilities. Language detection, language-specific adapters, Git
integration, reports, parallel execution, dependency graphs, Docker, and AI
functionality are also outside the current scope.

## Tests

Run the standard-library unit tests with:

```powershell
python -m unittest discover -s tests -v
```

GitHub Actions runs this test suite on pushes and pull requests targeting
`main`. The workflow checks out the code and runs the tests; it does not publish
or deploy the package.

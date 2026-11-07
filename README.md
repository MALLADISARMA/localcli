# LocalCI

LocalCI is a free, offline-first CI/CD command-line tool. Its objective is to
help developers run local linting, tests, and build checks from one command.
Phase 1 provides the CLI foundation using Python 3.10+ and only the standard
library at runtime.

LocalCI does not make network requests and requires no AI, cloud service, API
key, or external runtime dependency.

## Installation

From the project directory, install the command in editable mode:

```powershell
python -m pip install -e .
```

## Commands

- `localci --help` displays help.
- `localci --version` displays the installed version.
- `localci init` creates `.localci.json` in the current directory using that
  directory's name as the project name. It does not replace an existing file.
- `localci run` displays a placeholder; pipeline execution is planned for Phase 2.
- `localci status` displays a placeholder; execution history is planned for
  Phase 4.
- `localci clean` asks before deleting only `.localci.json`.
- `localci clean --yes` skips the confirmation prompt.

## Example

Run commands from the project directory you want LocalCI to manage:

```powershell
cd C:\path\to\your-project
localci init
localci run
localci status
localci clean
```

## Future plans

Future phases may add local pipeline execution and execution history. They are
not part of Phase 1. Language detection, Git integration, reports, Docker,
parallel execution, dependency graphs, and AI functionality are not implemented.

## Tests

Run the standard-library unit tests with:

```powershell
python -m unittest discover -s tests -v
```

GitHub Actions runs this test suite on pushes and pull requests targeting
`main`, using Python 3.10 through 3.13. The workflow checks out the code and
runs the tests; it does not publish or deploy the package.

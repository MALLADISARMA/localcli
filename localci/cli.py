"""Argument parsing and command dispatch for LocalCI."""

import argparse
from collections.abc import Sequence

from localci import __version__
from localci.commands.clean import clean_command
from localci.commands.init import init_command
from localci.commands.run import run_command
from localci.commands.status import status_command
from localci.utils.constants import GENERAL_ERROR, INTERRUPTED, SUCCESS
from localci.utils.exceptions import LocalCIError


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser and describe all available commands."""
    parser = argparse.ArgumentParser(
        prog="localci",
        description="A free, offline-first CI/CD command-line tool.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"LocalCI version {__version__}",
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("init", help="Create a LocalCI configuration file.")
    commands.add_parser("run", help="Run the configured pipeline.")
    commands.add_parser("status", help="Show pipeline execution history.")

    clean_parser = commands.add_parser(
        "clean",
        help="Remove the LocalCI configuration file.",
    )
    clean_parser.add_argument(
        "--yes",
        action="store_true",
        help="Delete the configuration without asking for confirmation.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse command-line arguments and return the selected command's exit code."""
    parser = build_parser()
    arguments = parser.parse_args(argv)

    try:
        if arguments.command == "init":
            return init_command()
        if arguments.command == "run":
            return run_command()
        if arguments.command == "status":
            return status_command()
        if arguments.command == "clean":
            return clean_command(yes=arguments.yes)
        parser.print_help()
        return SUCCESS
    except LocalCIError as error:
        parser.exit(GENERAL_ERROR, f"localci: error: {error}\n")
    except KeyboardInterrupt:
        print("\nOperation interrupted.")
        return INTERRUPTED


if __name__ == "__main__":
    raise SystemExit(main())

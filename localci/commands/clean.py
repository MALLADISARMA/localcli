"""Implementation of the clean command."""

from pathlib import Path

from localci.utils.constants import CONFIG_FILENAME, SUCCESS
from localci.utils.exceptions import LocalCIError


def clean_command(yes: bool = False) -> int:
    """Remove only the LocalCI configuration after confirmation."""
    config_path = Path.cwd() / CONFIG_FILENAME

    try:
        config_exists = config_path.exists()
    except OSError as error:
        raise LocalCIError(f"could not check configuration: {error}") from error

    if not config_exists:
        print("No LocalCI configuration found.")
        return SUCCESS

    if not yes:
        try:
            answer = input(f"Delete {config_path.name}? [y/N] ")
        except EOFError:
            answer = ""
        if answer.strip().lower() not in {"y", "yes"}:
            print("Cleanup cancelled.")
            return SUCCESS

    try:
        config_path.unlink()
    except OSError as error:
        raise LocalCIError(f"could not delete configuration: {error}") from error

    print(f"Deleted {config_path.name}")
    return SUCCESS

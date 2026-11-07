"""Implementation of the init command."""

import json
from pathlib import Path

from localci.utils.constants import CONFIG_FILENAME, SUCCESS
from localci.utils.exceptions import LocalCIError


def init_command() -> int:
    """Create a project configuration without replacing an existing path."""
    working_directory = Path.cwd()
    config_path = working_directory / CONFIG_FILENAME
    configuration = {
        "version": "1.0",
        "project": working_directory.name,
        "settings": {
            "stop_on_failure": True,
            "default_timeout": 300,
        },
        "stages": [],
    }

    try:
        with config_path.open("x", encoding="utf-8") as config_file:
            json.dump(configuration, config_file, indent=4)
            config_file.write("\n")
    except FileExistsError:
        print(f"Configuration already exists: {config_path.name}")
        return SUCCESS
    except OSError as error:
        raise LocalCIError(f"could not create configuration: {error}") from error

    print(f"Created {config_path.name}")
    return SUCCESS

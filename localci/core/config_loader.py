"""Configuration loading and validation for LocalCI."""

import json
from pathlib import Path
from typing import Any

from localci.utils.constants import (
    CONFIG_ERROR,
    CONFIG_FILENAME,
    GENERAL_ERROR,
    PREREQUISITE_ERROR,
)
from localci.utils.exceptions import LocalCIError


def _is_non_empty_string(value: Any) -> bool:
    """Return True if value is a string containing non-whitespace text."""
    return isinstance(value, str) and value.strip() != ""


def _is_positive_int(value: Any) -> bool:
    """Return True if value is a strictly positive integer (excluding booleans)."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _validate_stage(stage: Any, index: int) -> None:
    """Validate a single pipeline stage dictionary."""
    if not isinstance(stage, dict):
        raise LocalCIError(
            f"stage {index} must be a JSON object",
            exit_code=CONFIG_ERROR,
        )

    if "name" not in stage or not _is_non_empty_string(stage["name"]):
        raise LocalCIError(
            f"stage {index} must have a non-empty 'name' string",
            exit_code=CONFIG_ERROR,
        )

    stage_name = stage["name"]

    if "command" not in stage:
        raise LocalCIError(
            f"stage '{stage_name}' must have a 'command' list",
            exit_code=CONFIG_ERROR,
        )

    command = stage["command"]
    if not isinstance(command, list) or len(command) == 0:
        raise LocalCIError(
            f"stage '{stage_name}' 'command' must be a non-empty list",
            exit_code=CONFIG_ERROR,
        )

    for arg_index, arg in enumerate(command, start=1):
        if not _is_non_empty_string(arg):
            raise LocalCIError(
                f"stage '{stage_name}' command argument {arg_index} must be a non-empty string",
                exit_code=CONFIG_ERROR,
            )

    if "timeout" in stage and not _is_positive_int(stage["timeout"]):
        raise LocalCIError(
            f"stage '{stage_name}' 'timeout' must be a positive integer",
            exit_code=CONFIG_ERROR,
        )


def validate_config(data: Any) -> dict[str, Any]:
    """Validate parsed LocalCI configuration data and return it unchanged."""
    if not isinstance(data, dict):
        raise LocalCIError(
            "configuration must be a JSON object",
            exit_code=CONFIG_ERROR,
        )

    if "version" not in data or not _is_non_empty_string(data["version"]):
        raise LocalCIError(
            "configuration 'version' must be a non-empty string",
            exit_code=CONFIG_ERROR,
        )

    if "project" not in data or not _is_non_empty_string(data["project"]):
        raise LocalCIError(
            "configuration 'project' must be a non-empty string",
            exit_code=CONFIG_ERROR,
        )

    if "settings" not in data or not isinstance(data["settings"], dict):
        raise LocalCIError(
            "configuration 'settings' must be a JSON object",
            exit_code=CONFIG_ERROR,
        )

    settings = data["settings"]
    if "stop_on_failure" not in settings or not isinstance(
        settings["stop_on_failure"], bool
    ):
        raise LocalCIError(
            "configuration 'settings.stop_on_failure' must be a boolean",
            exit_code=CONFIG_ERROR,
        )

    if "default_timeout" not in settings or not _is_positive_int(
        settings["default_timeout"]
    ):
        raise LocalCIError(
            "configuration 'settings.default_timeout' must be a positive integer",
            exit_code=CONFIG_ERROR,
        )

    if "stages" not in data or not isinstance(data["stages"], list):
        raise LocalCIError(
            "configuration 'stages' must be a list",
            exit_code=CONFIG_ERROR,
        )

    for index, stage in enumerate(data["stages"], start=1):
        _validate_stage(stage, index)

    return data


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load and validate the LocalCI configuration file."""
    target_path = config_path if config_path is not None else Path.cwd() / CONFIG_FILENAME

    try:
        exists = target_path.exists()
    except OSError as error:
        raise LocalCIError(
            f"could not access configuration {target_path.name}: {error}",
            exit_code=GENERAL_ERROR,
        ) from error

    if not exists:
        raise LocalCIError(
            f"configuration file not found: {target_path.name}. Run 'localci init' first.",
            exit_code=PREREQUISITE_ERROR,
        )

    if not target_path.is_file():
        raise LocalCIError(
            f"configuration path is not a file: {target_path.name}",
            exit_code=CONFIG_ERROR,
        )

    try:
        raw_content = target_path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise LocalCIError(
            f"configuration file not found: {target_path.name}. Run 'localci init' first.",
            exit_code=PREREQUISITE_ERROR,
        ) from error
    except UnicodeDecodeError as error:
        raise LocalCIError(
            f"configuration file is not valid UTF-8: {error}",
            exit_code=CONFIG_ERROR,
        ) from error
    except OSError as error:
        raise LocalCIError(
            f"could not read configuration {target_path.name}: {error}",
            exit_code=GENERAL_ERROR,
        ) from error

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as error:
        raise LocalCIError(
            f"invalid JSON in {target_path.name}: {error.msg} "
            f"(line {error.lineno}, column {error.colno})",
            exit_code=CONFIG_ERROR,
        ) from error

    return validate_config(parsed)

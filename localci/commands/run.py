"""Implementation of the run command."""

from pathlib import Path

from localci.core.config_loader import load_config
from localci.core.runner import run_pipeline
from localci.utils.constants import CONFIG_FILENAME


def run_command() -> int:
    """Load configuration and execute all configured pipeline stages."""
    working_directory = Path.cwd()
    config_path = working_directory / CONFIG_FILENAME
    configuration = load_config(config_path)
    summary = run_pipeline(configuration, working_directory=working_directory)
    return summary["exit_code"]

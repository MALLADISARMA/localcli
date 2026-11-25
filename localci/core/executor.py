"""Safe local command execution using subprocess without a shell."""

from collections.abc import Sequence
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from localci.utils.constants import GENERAL_ERROR, PREREQUISITE_ERROR


def _decode_output(output: str | bytes | None) -> str:
    """Convert subprocess output (bytes, str, or None) to a string."""
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output


def _display_output(stdout: str, stderr: str) -> None:
    """Write captured stdout and stderr to the standard streams."""
    if stdout:
        sys.stdout.write(stdout)
        if not stdout.endswith("\n"):
            sys.stdout.write("\n")
    if stderr:
        sys.stderr.write(stderr)
        if not stderr.endswith("\n"):
            sys.stderr.write("\n")


def execute_command(
    command: Sequence[str],
    cwd: Path,
    timeout: int,
) -> dict[str, Any]:
    """Execute a command argument list safely and return its execution result."""
    command_list = list(command)
    start_time = time.monotonic()

    try:
        completed = subprocess.run(
            command_list,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired as error:
        duration = time.monotonic() - start_time
        stdout = _decode_output(error.stdout)
        stderr = _decode_output(error.stderr)
        _display_output(stdout, stderr)
        return {
            "success": False,
            "exit_code": None,
            "duration": duration,
            "stdout": stdout,
            "stderr": stderr,
            "error": f"Command timed out after {timeout} seconds.",
            "missing_executable": False,
        }
    except FileNotFoundError:
        duration = time.monotonic() - start_time
        return {
            "success": False,
            "exit_code": PREREQUISITE_ERROR,
            "duration": duration,
            "stdout": "",
            "stderr": "",
            "error": f"Executable not found: {command_list[0]}",
            "missing_executable": True,
        }
    except PermissionError:
        duration = time.monotonic() - start_time
        return {
            "success": False,
            "exit_code": GENERAL_ERROR,
            "duration": duration,
            "stdout": "",
            "stderr": "",
            "error": f"Permission denied executing command: {command_list[0]}",
            "missing_executable": False,
        }
    except OSError as error:
        duration = time.monotonic() - start_time
        return {
            "success": False,
            "exit_code": GENERAL_ERROR,
            "duration": duration,
            "stdout": "",
            "stderr": "",
            "error": f"Failed to execute command: {error}",
            "missing_executable": False,
        }

    duration = time.monotonic() - start_time
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    _display_output(stdout, stderr)

    success = completed.returncode == 0
    error_message = None if success else f"Command exited with code {completed.returncode}."

    return {
        "success": success,
        "exit_code": completed.returncode,
        "duration": duration,
        "stdout": stdout,
        "stderr": stderr,
        "error": error_message,
        "missing_executable": False,
    }

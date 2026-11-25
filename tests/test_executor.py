"""Tests for safe local command execution."""

import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from localci.core.executor import execute_command
from localci.utils.constants import GENERAL_ERROR, PREREQUISITE_ERROR, SUCCESS


class ExecutorTests(unittest.TestCase):
    """Exercise execute_command with Python subprocesses and mocks."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.working_directory = Path(self.temporary_directory.name)

    def test_successful_command(self) -> None:
        """A zero-exit command succeeds and records duration."""
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = execute_command(
                [sys.executable, "-c", "print('ok')"],
                cwd=self.working_directory,
                timeout=10,
            )

        self.assertTrue(result["success"])
        self.assertEqual(result["exit_code"], SUCCESS)
        self.assertIsNone(result["error"])
        self.assertFalse(result["missing_executable"])
        self.assertGreaterEqual(result["duration"], 0.0)

    def test_failed_command(self) -> None:
        """A non-zero exit code marks the execution as failed."""
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = execute_command(
                [sys.executable, "-c", "import sys; sys.exit(4)"],
                cwd=self.working_directory,
                timeout=10,
            )

        self.assertFalse(result["success"])
        self.assertEqual(result["exit_code"], 4)
        self.assertIn("4", result["error"])
        self.assertFalse(result["missing_executable"])

    def test_missing_executable(self) -> None:
        """A missing executable sets missing_executable and PREREQUISITE_ERROR."""
        result = execute_command(
            ["definitely_nonexistent_localci_binary_12345"],
            cwd=self.working_directory,
            timeout=10,
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["exit_code"], PREREQUISITE_ERROR)
        self.assertTrue(result["missing_executable"])
        self.assertIn("Executable not found", result["error"])

    def test_timeout_expired(self) -> None:
        """A command exceeding timeout is terminated and marked failed."""
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = execute_command(
                [sys.executable, "-c", "import time; time.sleep(5)"],
                cwd=self.working_directory,
                timeout=1,
            )

        self.assertFalse(result["success"])
        self.assertIsNone(result["exit_code"])
        self.assertFalse(result["missing_executable"])
        self.assertIn("timed out", result["error"].lower())

    def test_timeout_decodes_partial_bytes_output(self) -> None:
        """Partial bytes output attached to TimeoutExpired is decoded cleanly."""
        timeout_exc = subprocess.TimeoutExpired(
            cmd=["python"],
            timeout=2,
            output=b"partial out\n",
            stderr=b"partial err\n",
        )
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        with patch("subprocess.run", side_effect=timeout_exc):
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                result = execute_command(
                    [sys.executable, "-c", "pass"],
                    cwd=self.working_directory,
                    timeout=2,
                )

        self.assertFalse(result["success"])
        self.assertEqual(result["stdout"], "partial out\n")
        self.assertEqual(result["stderr"], "partial err\n")
        self.assertEqual(stdout_buf.getvalue(), "partial out\n")
        self.assertEqual(stderr_buf.getvalue(), "partial err\n")

    def test_stdout_capture(self) -> None:
        """Stdout is captured in the result and written to stdout."""
        stdout_buf = io.StringIO()
        with redirect_stdout(stdout_buf), redirect_stderr(io.StringIO()):
            result = execute_command(
                [sys.executable, "-c", "print('hello stdout')"],
                cwd=self.working_directory,
                timeout=10,
            )

        self.assertIn("hello stdout", result["stdout"])
        self.assertIn("hello stdout", stdout_buf.getvalue())

    def test_stderr_capture(self) -> None:
        """Stderr is captured in the result and written to stderr."""
        stderr_buf = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(stderr_buf):
            result = execute_command(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.stderr.write('hello stderr\\n')",
                ],
                cwd=self.working_directory,
                timeout=10,
            )

        self.assertIn("hello stderr", result["stderr"])
        self.assertIn("hello stderr", stderr_buf.getvalue())

    def test_permission_error(self) -> None:
        """PermissionError while launching a process returns GENERAL_ERROR."""
        with patch("subprocess.run", side_effect=PermissionError("denied")):
            result = execute_command(
                [sys.executable, "--version"],
                cwd=self.working_directory,
                timeout=10,
            )

        self.assertFalse(result["success"])
        self.assertEqual(result["exit_code"], GENERAL_ERROR)
        self.assertIn("Permission denied", result["error"])


if __name__ == "__main__":
    unittest.main()

"""Tests for LocalCI CLI help, version, and command dispatch."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from localci.main import main
from localci.utils.constants import PREREQUISITE_ERROR, SUCCESS


class CLITests(unittest.TestCase):
    """Verify basic CLI output and behavior."""

    def test_help_lists_all_commands(self) -> None:
        """Help output includes each available command."""
        output = io.StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as result:
            main(["--help"])

        self.assertEqual(result.exception.code, SUCCESS)
        for command in ("init", "run", "status", "clean"):
            self.assertIn(command, output.getvalue())

    def test_version_has_exact_output(self) -> None:
        """Version output matches the required string."""
        output = io.StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as result:
            main(["--version"])

        self.assertEqual(result.exception.code, SUCCESS)
        self.assertEqual(output.getvalue(), "LocalCI version 0.1.0\n")

    def test_run_executes_pipeline_from_current_directory(self) -> None:
        """Run loads .localci.json and executes the configured pipeline."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            config = {
                "version": "1.0",
                "project": "cli-test",
                "settings": {"stop_on_failure": True, "default_timeout": 30},
                "stages": [],
            }
            (project_dir / ".localci.json").write_text(
                json.dumps(config), encoding="utf-8"
            )
            output = io.StringIO()
            with patch("pathlib.Path.cwd", return_value=project_dir):
                with redirect_stdout(output):
                    exit_code = main(["run"])

        self.assertEqual(exit_code, SUCCESS)
        self.assertIn("Project: cli-test", output.getvalue())

    def test_run_without_configuration_returns_prerequisite_error(self) -> None:
        """Run reports missing configuration with PREREQUISITE_ERROR."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)
            with patch("pathlib.Path.cwd", return_value=project_dir):
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
                    main(["run"])

        self.assertEqual(result.exception.code, PREREQUISITE_ERROR)

    def test_status_shows_phase_four_placeholder(self) -> None:
        """Status prints only its Phase 4 placeholder."""
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["status"])

        self.assertEqual(exit_code, SUCCESS)
        self.assertEqual(
            output.getvalue(),
            "Execution history is not implemented yet. "
            "It will be available in Phase 4.\n",
        )

    def test_keyboard_interrupt_returns_interrupted_exit_code(self) -> None:
        """Ctrl+C during a command returns the centralized interrupt code."""
        from unittest.mock import patch

        with patch("localci.cli.run_command", side_effect=KeyboardInterrupt):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["run"]), 130)


if __name__ == "__main__":
    unittest.main()

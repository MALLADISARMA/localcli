"""Tests for LocalCI help, version, and placeholder commands."""

import io
import unittest
from contextlib import redirect_stdout

from localci.main import main
from localci.utils.constants import SUCCESS


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

    def test_run_shows_phase_two_placeholder(self) -> None:
        """Run prints only its Phase 2 placeholder."""
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["run"])

        self.assertEqual(exit_code, SUCCESS)
        self.assertEqual(
            output.getvalue(),
            "Pipeline execution is not implemented yet. "
            "It will be available in Phase 2.\n",
        )

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

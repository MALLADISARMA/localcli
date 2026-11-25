"""Tests for sequential pipeline execution and summary generation."""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from localci.core.runner import run_pipeline
from localci.main import main
from localci.utils.constants import (
    CONFIG_ERROR,
    GENERAL_ERROR,
    PREREQUISITE_ERROR,
    SUCCESS,
)


def _make_config(stages: list[dict], stop_on_failure: bool = True) -> dict:
    """Create a valid pipeline configuration for runner tests."""
    return {
        "version": "1.0",
        "project": "runner-test",
        "settings": {
            "stop_on_failure": stop_on_failure,
            "default_timeout": 10,
        },
        "stages": stages,
    }


class RunnerTests(unittest.TestCase):
    """Verify sequential execution, failure rules, and summary output."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.project_directory = Path(self.temporary_directory.name)

    def test_multiple_sequential_stages(self) -> None:
        """All stages execute in sequence and produce SUCCESS summary."""
        marker_file = self.project_directory / "order.txt"
        config = _make_config(
            [
                {
                    "name": "Stage One",
                    "command": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path('order.txt').write_text('1')",
                    ],
                },
                {
                    "name": "Stage Two",
                    "command": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; p = Path('order.txt'); p.write_text(p.read_text() + '2')",
                    ],
                },
            ]
        )

        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(io.StringIO()):
            summary = run_pipeline(config, working_directory=self.project_directory)

        self.assertEqual(marker_file.read_text(encoding="utf-8"), "12")
        self.assertEqual(summary["exit_code"], SUCCESS)
        self.assertEqual(summary["overall_status"], "SUCCESS")
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["passed"], 2)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["skipped"], 0)
        self.assertIn("Overall Status: SUCCESS", output.getvalue())

    def test_stop_after_failure_when_enabled(self) -> None:
        """Remaining stages are skipped when stop_on_failure is True."""
        second_stage_marker = self.project_directory / "should_not_exist.txt"
        config = _make_config(
            [
                {
                    "name": "Failing Stage",
                    "command": [sys.executable, "-c", "import sys; sys.exit(1)"],
                },
                {
                    "name": "Second Stage",
                    "command": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path('should_not_exist.txt').write_text('ran')",
                    ],
                },
                {
                    "name": "Third Stage",
                    "command": [sys.executable, "-c", "print('third')"],
                },
            ],
            stop_on_failure=True,
        )

        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(io.StringIO()):
            summary = run_pipeline(config, working_directory=self.project_directory)

        self.assertFalse(second_stage_marker.exists())
        self.assertEqual(summary["exit_code"], GENERAL_ERROR)
        self.assertEqual(summary["overall_status"], "FAILED")
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["passed"], 0)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["skipped"], 2)
        self.assertEqual(
            [stage["status"] for stage in summary["stages"]],
            ["FAILED", "SKIPPED", "SKIPPED"],
        )
        self.assertIn("Overall Status: FAILED", output.getvalue())

    def test_continue_after_failure_when_disabled(self) -> None:
        """Remaining stages execute when stop_on_failure is False."""
        config = _make_config(
            [
                {
                    "name": "Failing Stage",
                    "command": [sys.executable, "-c", "import sys; sys.exit(2)"],
                },
                {
                    "name": "Passing Stage",
                    "command": [sys.executable, "-c", "print('still running')"],
                },
            ],
            stop_on_failure=False,
        )

        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(io.StringIO()):
            summary = run_pipeline(config, working_directory=self.project_directory)

        self.assertEqual(summary["exit_code"], GENERAL_ERROR)
        self.assertEqual(summary["overall_status"], "FAILED")
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["passed"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["skipped"], 0)
        self.assertEqual(
            [stage["status"] for stage in summary["stages"]],
            ["FAILED", "PASSED"],
        )

    def test_missing_executable_returns_prerequisite_error(self) -> None:
        """A stage with a missing executable reports PREREQUISITE_ERROR."""
        config = _make_config(
            [
                {
                    "name": "Missing Tool",
                    "command": ["missing_tool_for_localci_test"],
                },
                {
                    "name": "Follow-up",
                    "command": [sys.executable, "-c", "print('ok')"],
                },
            ],
            stop_on_failure=True,
        )

        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            summary = run_pipeline(config, working_directory=self.project_directory)

        self.assertEqual(summary["exit_code"], PREREQUISITE_ERROR)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["skipped"], 1)

    def test_empty_pipeline(self) -> None:
        """An empty stages list succeeds cleanly with a friendly notice."""
        config = _make_config([])

        output = io.StringIO()
        with redirect_stdout(output):
            summary = run_pipeline(config, working_directory=self.project_directory)

        self.assertEqual(summary["exit_code"], SUCCESS)
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["passed"], 0)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["skipped"], 0)
        self.assertIn("No pipeline stages configured", output.getvalue())

    def test_invalid_configuration_prevents_execution(self) -> None:
        """Invalid configuration exits with CONFIG_ERROR without running stages."""
        invalid_config = {
            "version": "1.0",
            "project": "broken",
            "settings": {"stop_on_failure": True, "default_timeout": 0},
            "stages": [{"name": "Should Not Run", "command": ["python", "-V"]}],
        }
        (self.project_directory / ".localci.json").write_text(
            json.dumps(invalid_config), encoding="utf-8"
        )

        with patch("pathlib.Path.cwd", return_value=self.project_directory):
            with patch("subprocess.run") as mocked_run:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
                    main(["run"])

        mocked_run.assert_not_called()
        self.assertEqual(result.exception.code, CONFIG_ERROR)


if __name__ == "__main__":
    unittest.main()

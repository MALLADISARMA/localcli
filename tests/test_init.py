"""Tests for the LocalCI init command."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from localci.main import main
from localci.utils.constants import SUCCESS


class InitTests(unittest.TestCase):
    """Exercise init using an isolated temporary working directory."""

    def setUp(self) -> None:
        """Set up a temporary project directory."""
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.project_directory = Path(self.temporary_directory.name)
        self.cwd_patch = patch("pathlib.Path.cwd", return_value=self.project_directory)
        self.cwd_patch.start()
        self.addCleanup(self.cwd_patch.stop)

    def test_init_creates_expected_configuration(self) -> None:
        """Init writes the requested starter configuration."""
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["init"])

        configuration = json.loads(
            (self.project_directory / ".localci.json").read_text(encoding="utf-8")
        )
        self.assertEqual(exit_code, SUCCESS)
        self.assertEqual(
            configuration,
            {
                "version": "1.0",
                "project": self.project_directory.name,
                "settings": {
                    "stop_on_failure": True,
                    "default_timeout": 300,
                },
                "stages": [],
            },
        )
        self.assertIn("Created .localci.json", output.getvalue())

    def test_init_does_not_overwrite_existing_configuration(self) -> None:
        """Init preserves a config that already exists."""
        config_path = self.project_directory / ".localci.json"
        original_contents = '{"project": "original"}'
        config_path.write_text(original_contents, encoding="utf-8")
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(["init"])

        self.assertEqual(exit_code, SUCCESS)
        self.assertEqual(config_path.read_text(encoding="utf-8"), original_contents)
        self.assertIn("already exists", output.getvalue())

    def test_init_uses_current_directory_name_as_project(self) -> None:
        """The project field is the working directory's name."""
        with redirect_stdout(io.StringIO()):
            main(["init"])

        config = json.loads(
            (self.project_directory / ".localci.json").read_text(encoding="utf-8")
        )
        self.assertEqual(config["project"], self.project_directory.name)

    def test_init_reports_filesystem_errors(self) -> None:
        """A filesystem failure is returned as a CLI error."""
        with patch("pathlib.Path.open", side_effect=PermissionError("denied")):
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
                main(["init"])

        self.assertEqual(result.exception.code, 1)


if __name__ == "__main__":
    unittest.main()

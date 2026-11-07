"""Tests for the LocalCI clean command."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from localci.main import main
from localci.utils.constants import SUCCESS


class CleanTests(unittest.TestCase):
    """Exercise clean using an isolated temporary working directory."""

    def setUp(self) -> None:
        """Set up a temporary project directory and config file."""
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.project_directory = Path(self.temporary_directory.name)
        self.cwd_patch = patch("pathlib.Path.cwd", return_value=self.project_directory)
        self.cwd_patch.start()
        self.addCleanup(self.cwd_patch.stop)
        self.config_path = self.project_directory / ".localci.json"
        self.config_path.write_text("{}", encoding="utf-8")

    def test_clean_asks_for_confirmation(self) -> None:
        """Clean prompts before deleting the configuration."""
        with patch("builtins.input", return_value="n") as mocked_input:
            with redirect_stdout(io.StringIO()):
                exit_code = main(["clean"])

        mocked_input.assert_called_once()
        self.assertEqual(exit_code, SUCCESS)
        self.assertTrue(self.config_path.exists())

    def test_clean_deletes_configuration_after_confirmation(self) -> None:
        """An affirmative confirmation deletes the config."""
        with patch("builtins.input", return_value="y"):
            with redirect_stdout(io.StringIO()):
                exit_code = main(["clean"])

        self.assertEqual(exit_code, SUCCESS)
        self.assertFalse(self.config_path.exists())

    def test_clean_yes_skips_confirmation(self) -> None:
        """The --yes option removes the config without prompting."""
        with patch("builtins.input", side_effect=AssertionError("unexpected prompt")):
            with redirect_stdout(io.StringIO()):
                exit_code = main(["clean", "--yes"])

        self.assertEqual(exit_code, SUCCESS)
        self.assertFalse(self.config_path.exists())

    def test_clean_preserves_unrelated_files(self) -> None:
        """Only the LocalCI config is removed."""
        unrelated_file = self.project_directory / "keep.txt"
        unrelated_file.write_text("keep", encoding="utf-8")

        with patch("builtins.input", return_value="yes"):
            with redirect_stdout(io.StringIO()):
                main(["clean"])

        self.assertFalse(self.config_path.exists())
        self.assertEqual(unrelated_file.read_text(encoding="utf-8"), "keep")

    def test_clean_decline_preserves_configuration(self) -> None:
        """Declining the confirmation leaves the config unchanged."""
        with patch("builtins.input", return_value="no"):
            with redirect_stdout(io.StringIO()):
                exit_code = main(["clean"])

        self.assertEqual(exit_code, SUCCESS)
        self.assertEqual(self.config_path.read_text(encoding="utf-8"), "{}")

    def test_clean_reports_filesystem_errors(self) -> None:
        """A filesystem failure is returned as a CLI error."""
        with patch.object(Path, "unlink", side_effect=PermissionError("denied")):
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
                main(["clean", "--yes"])

        self.assertEqual(result.exception.code, 1)
        self.assertTrue(self.config_path.exists())


if __name__ == "__main__":
    unittest.main()

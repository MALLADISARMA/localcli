"""Tests for LocalCI configuration loading and validation."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from localci.core.config_loader import load_config
from localci.utils.constants import CONFIG_ERROR, GENERAL_ERROR, PREREQUISITE_ERROR
from localci.utils.exceptions import LocalCIError


def _valid_config() -> dict:
    """Return a valid configuration dictionary for tests."""
    return {
        "version": "1.0",
        "project": "sample-project",
        "settings": {
            "stop_on_failure": True,
            "default_timeout": 300,
        },
        "stages": [
            {
                "name": "Unit Tests",
                "command": ["python", "-m", "unittest"],
            },
            {
                "name": "Compile Check",
                "command": ["python", "-m", "compileall", "."],
                "timeout": 120,
            },
        ],
    }


class ConfigLoaderTests(unittest.TestCase):
    """Verify validation and error handling for .localci.json."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.project_directory = Path(self.temporary_directory.name)
        self.config_path = self.project_directory / ".localci.json"

    def _write_config(self, data: object) -> None:
        self.config_path.write_text(json.dumps(data), encoding="utf-8")

    def test_valid_configuration(self) -> None:
        """A valid configuration is loaded and returned unchanged."""
        expected = _valid_config()
        self._write_config(expected)

        loaded = load_config(self.config_path)

        self.assertEqual(loaded, expected)

    def test_missing_configuration(self) -> None:
        """A missing configuration file raises PREREQUISITE_ERROR."""
        with self.assertRaises(LocalCIError) as context:
            load_config(self.config_path)

        self.assertEqual(context.exception.exit_code, PREREQUISITE_ERROR)

    def test_invalid_json(self) -> None:
        """Malformed JSON raises CONFIG_ERROR."""
        self.config_path.write_text("{invalid json", encoding="utf-8")

        with self.assertRaises(LocalCIError) as context:
            load_config(self.config_path)

        self.assertEqual(context.exception.exit_code, CONFIG_ERROR)

    def test_missing_required_fields(self) -> None:
        """Missing top-level, settings, or stage fields raise CONFIG_ERROR."""
        for key in ("version", "project", "settings", "stages"):
            config = _valid_config()
            del config[key]
            self._write_config(config)
            with self.subTest(missing_key=key):
                with self.assertRaises(LocalCIError) as context:
                    load_config(self.config_path)
                self.assertEqual(context.exception.exit_code, CONFIG_ERROR)

        for setting_key in ("stop_on_failure", "default_timeout"):
            config = _valid_config()
            del config["settings"][setting_key]
            self._write_config(config)
            with self.subTest(missing_setting=setting_key):
                with self.assertRaises(LocalCIError) as context:
                    load_config(self.config_path)
                self.assertEqual(context.exception.exit_code, CONFIG_ERROR)

        for stage_key in ("name", "command"):
            config = _valid_config()
            del config["stages"][0][stage_key]
            self._write_config(config)
            with self.subTest(missing_stage_key=stage_key):
                with self.assertRaises(LocalCIError) as context:
                    load_config(self.config_path)
                self.assertEqual(context.exception.exit_code, CONFIG_ERROR)

    def test_invalid_types_and_empty_strings(self) -> None:
        """Incorrect types or empty required strings raise CONFIG_ERROR."""
        invalid_configs = [
            [],
            {**_valid_config(), "version": ""},
            {**_valid_config(), "project": "   "},
            {**_valid_config(), "settings": "invalid"},
            {
                **_valid_config(),
                "settings": {"stop_on_failure": "true", "default_timeout": 60},
            },
            {**_valid_config(), "stages": "not-a-list"},
            {**_valid_config(), "stages": ["not-a-dict"]},
            {
                **_valid_config(),
                "stages": [{"name": " ", "command": ["python", "--version"]}],
            },
        ]

        for bad_config in invalid_configs:
            self._write_config(bad_config)
            with self.subTest(bad_config=bad_config):
                with self.assertRaises(LocalCIError) as context:
                    load_config(self.config_path)
                self.assertEqual(context.exception.exit_code, CONFIG_ERROR)

    def test_invalid_command(self) -> None:
        """Empty, non-list, or invalid command arguments raise CONFIG_ERROR."""
        bad_commands = [
            [],
            "python --version",
            [""],
            ["python", "   "],
            ["python", 123],
        ]

        for bad_command in bad_commands:
            config = _valid_config()
            config["stages"] = [{"name": "Bad Command", "command": bad_command}]
            self._write_config(config)
            with self.subTest(bad_command=bad_command):
                with self.assertRaises(LocalCIError) as context:
                    load_config(self.config_path)
                self.assertEqual(context.exception.exit_code, CONFIG_ERROR)

    def test_invalid_timeout(self) -> None:
        """Zero, negative, non-int, and boolean timeouts raise CONFIG_ERROR."""
        bad_timeouts = [0, -5, "10", 1.5, None, True, False]

        for bad_timeout in bad_timeouts:
            config = _valid_config()
            config["settings"]["default_timeout"] = bad_timeout
            self._write_config(config)
            with self.subTest(default_timeout=bad_timeout):
                with self.assertRaises(LocalCIError) as context:
                    load_config(self.config_path)
                self.assertEqual(context.exception.exit_code, CONFIG_ERROR)

            stage_config = _valid_config()
            stage_config["stages"][0]["timeout"] = bad_timeout
            self._write_config(stage_config)
            with self.subTest(stage_timeout=bad_timeout):
                with self.assertRaises(LocalCIError) as context:
                    load_config(self.config_path)
                self.assertEqual(context.exception.exit_code, CONFIG_ERROR)

    def test_empty_stages_is_valid(self) -> None:
        """An empty stages list is accepted as valid configuration."""
        config = _valid_config()
        config["stages"] = []
        self._write_config(config)

        loaded = load_config(self.config_path)

        self.assertEqual(loaded["stages"], [])

    def test_permission_error_reading_config(self) -> None:
        """Permission errors while reading config raise LocalCIError."""
        self._write_config(_valid_config())

        with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            with self.assertRaises(LocalCIError) as context:
                load_config(self.config_path)

        self.assertEqual(context.exception.exit_code, GENERAL_ERROR)


if __name__ == "__main__":
    unittest.main()

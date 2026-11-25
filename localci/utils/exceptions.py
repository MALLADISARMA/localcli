"""Exceptions used to report expected LocalCI errors."""

from localci.utils.constants import GENERAL_ERROR


class LocalCIError(Exception):
    """An expected error that can be presented clearly to a CLI user."""

    def __init__(self, message: str, exit_code: int = GENERAL_ERROR) -> None:
        super().__init__(message)
        self.exit_code = exit_code

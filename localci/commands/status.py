"""Implementation of the status command."""

from localci.utils.constants import SUCCESS


def status_command() -> int:
    """Display the Phase 1 execution history notice."""
    print(
        "Execution history is not implemented yet. "
        "It will be available in Phase 4."
    )
    return SUCCESS

"""Sequential pipeline runner and summary formatter."""

from pathlib import Path
import shlex
from typing import Any

from localci.core.executor import execute_command
from localci.utils.constants import GENERAL_ERROR, PREREQUISITE_ERROR, SUCCESS

DIVIDER = "=" * 40
STAGE_DIVIDER = "-" * 40


def _print_banner(title: str) -> None:
    """Print a centered section banner."""
    print(DIVIDER)
    print(f"{title:^40}")
    print(DIVIDER)


def run_pipeline(
    configuration: dict[str, Any],
    working_directory: Path | None = None,
) -> dict[str, Any]:
    """Execute configured pipeline stages sequentially and print a summary."""
    cwd = working_directory if working_directory is not None else Path.cwd()
    project_name = configuration["project"]
    settings = configuration["settings"]
    stop_on_failure = settings["stop_on_failure"]
    default_timeout = settings["default_timeout"]
    stages = configuration["stages"]
    total_stages = len(stages)

    _print_banner("LOCALCI PIPELINE")
    print()
    print(f"Project: {project_name}")
    print(f"Total stages: {total_stages}")
    print()

    if total_stages == 0:
        print("No pipeline stages configured. Add stages to .localci.json to run checks.")
        return {
            "project": project_name,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "overall_status": "SUCCESS",
            "exit_code": SUCCESS,
            "stages": [],
        }

    stage_results: list[dict[str, Any]] = []
    passed_count = 0
    failed_count = 0
    skipped_count = 0
    has_missing_executable = False
    halted = False

    for index, stage in enumerate(stages, start=1):
        stage_name = stage["name"]
        print(f"[{index}/{total_stages}] {stage_name}")
        print(STAGE_DIVIDER)

        if halted:
            reason = "Skipped due to previous stage failure."
            print("Status: SKIPPED")
            print(f"Reason: {reason}")
            print()
            skipped_count += 1
            stage_results.append(
                {
                    "name": stage_name,
                    "status": "SKIPPED",
                    "exit_code": None,
                    "duration": 0.0,
                    "error": reason,
                    "missing_executable": False,
                }
            )
            continue

        command = stage["command"]
        timeout = stage.get("timeout", default_timeout)
        print(f"Command: {shlex.join(command)}")
        print("Executing command...")
        print()

        exec_result = execute_command(command, cwd=cwd, timeout=timeout)

        if exec_result["success"]:
            status = "PASSED"
            passed_count += 1
        else:
            status = "FAILED"
            failed_count += 1
            if exec_result["missing_executable"]:
                has_missing_executable = True
            if stop_on_failure:
                halted = True

        print(f"Status: {status}")
        if not exec_result["success"] and exec_result["exit_code"] is not None:
            print(f"Exit Code: {exec_result['exit_code']}")
        print(f"Duration: {exec_result['duration']:.2f} seconds")
        if exec_result["error"]:
            print(f"Error: {exec_result['error']}")
        print()

        stage_results.append(
            {
                "name": stage_name,
                "status": status,
                "exit_code": exec_result["exit_code"],
                "duration": exec_result["duration"],
                "error": exec_result["error"],
                "missing_executable": exec_result["missing_executable"],
            }
        )

    if failed_count == 0:
        overall_status = "SUCCESS"
        exit_code = SUCCESS
    else:
        overall_status = "FAILED"
        exit_code = PREREQUISITE_ERROR if has_missing_executable else GENERAL_ERROR

    _print_banner("PIPELINE SUMMARY")
    print()
    print(f"Total stages : {total_stages}")
    print(f"Passed       : {passed_count}")
    print(f"Failed       : {failed_count}")
    print(f"Skipped      : {skipped_count}")
    print()
    print(f"Overall Status: {overall_status}")
    print()
    print(DIVIDER)

    return {
        "project": project_name,
        "total": total_stages,
        "passed": passed_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "overall_status": overall_status,
        "exit_code": exit_code,
        "stages": stage_results,
    }

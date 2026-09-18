"""Shared plumbing for the ``uav_service_restoration_v0`` command-line tools.

Kept deliberately small: repository path setup, one JSON writer that never silently
overwrites, and one error contract so every tool fails the same recognisable way.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


EXIT_OK = 0
EXIT_USAGE = 2
EXIT_DATA = 3
EXIT_RUNTIME = 4


class CliError(RuntimeError):
    """A reportable failure with a chosen exit code."""

    def __init__(self, message: str, exit_code: int = EXIT_DATA) -> None:
        super().__init__(message)
        self.exit_code = int(exit_code)


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(f"not JSON-serialisable: {type(value).__name__}")


def dumps(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=_jsonable)


def emit(payload: Any, output: str | None = None, *, force: bool = False) -> None:
    """Print the report, and additionally write it to ``output`` when given.

    An existing output file is refused unless ``force``: a report another step may
    already have consumed is never overwritten by accident.
    """

    text = dumps(payload)
    print(text)
    if output is None:
        return
    path = Path(output)
    if path.exists() and not force:
        raise CliError(
            f"{path} already exists; choose a new path or pass --force", EXIT_USAGE
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def require_existing_file(path: str, what: str) -> Path:
    resolved = Path(path)
    if not resolved.is_file():
        raise CliError(f"{what} not found: {resolved}", EXIT_DATA)
    return resolved


def require_existing_dir(path: str, what: str) -> Path:
    resolved = Path(path)
    if not resolved.is_dir():
        raise CliError(f"{what} not found: {resolved}", EXIT_DATA)
    return resolved


def run(main: Any, argv: list[str] | None = None) -> int:
    """Invoke ``main`` and convert the package's error types into exit codes."""

    from envs.uav_service_restoration.config import ConfigError
    from envs.uav_service_restoration.demand import DemandDataError, EpisodeSamplingError
    from envs.uav_service_restoration.observations import EntityLimitExceeded
    from envs.uav_service_restoration.preprocess_milan import PreprocessError
    from envs.uav_service_restoration.types import SchedulerError

    try:
        return int(main(argv))
    except CliError as error:
        print(f"error: {error}", file=sys.stderr)
        return error.exit_code
    except (ConfigError, EntityLimitExceeded) as error:
        print(f"configuration error: {error}", file=sys.stderr)
        return EXIT_USAGE
    except (DemandDataError, EpisodeSamplingError, PreprocessError) as error:
        print(f"data error: {error}", file=sys.stderr)
        return EXIT_DATA
    except SchedulerError as error:
        print(f"scheduler error: {error}", file=sys.stderr)
        return EXIT_RUNTIME

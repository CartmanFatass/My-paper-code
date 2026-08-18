"""Load repository observer configuration. Runtime identity stays external."""

from __future__ import annotations

import os
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 project interpreter
    import tomli as tomllib

from .models import ObserverConfig

KNOWN_KEYS = frozenset(
    {
        "schema_version",
        "client_name",
        "client_title",
        "client_version",
        "experimental_api",
        "initialize_timeout_seconds",
        "request_timeout_seconds",
        "reconcile_interval_seconds",
        "max_jsonl_line_bytes",
        "read_retry_attempts",
        "read_retry_base_seconds",
        "unexpected_server_request_policy",
    }
)
MIN_LINE_BYTES = 1_048_576
MAX_LINE_BYTES = 67_108_864
DEFAULT_CONFIG_REL = Path(".codex/app-server-observer.toml")
RUNTIME_HOME_ENV = "HMASD_CODEX_SUPERVISOR_HOME"


class ObserverConfigError(ValueError):
    """Raised when observer configuration is invalid."""


def default_runtime_home() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise ObserverConfigError("LOCALAPPDATA is required to resolve the observer runtime home")
    return Path(local) / "HMASD" / "codex-supervisor"


def resolve_runtime_home(repo_root: Path, runtime_home: Path | None = None) -> Path:
    if runtime_home is not None:
        home = Path(runtime_home)
    elif os.environ.get(RUNTIME_HOME_ENV):
        home = Path(os.environ[RUNTIME_HOME_ENV])
    else:
        home = default_runtime_home()
    home = home.resolve()
    root = Path(repo_root).resolve()
    try:
        home.relative_to(root)
    except ValueError:
        return home
    raise ObserverConfigError("observer runtime home must not live inside the repository")


def load_observer_config(repo_root: Path, runtime_home: Path | None = None) -> ObserverConfig:
    path = Path(repo_root) / DEFAULT_CONFIG_REL
    raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    unknown = sorted(set(raw) - KNOWN_KEYS)
    if unknown:
        raise ObserverConfigError(f"unknown configuration keys: {unknown}")
    timeouts = (
        float(raw["initialize_timeout_seconds"]),
        float(raw["request_timeout_seconds"]),
        float(raw["reconcile_interval_seconds"]),
        float(raw["read_retry_base_seconds"]),
    )
    if any(value <= 0 for value in timeouts) or int(raw["read_retry_attempts"]) <= 0:
        raise ObserverConfigError("timeouts and retry attempts must be positive")
    line_limit = int(raw["max_jsonl_line_bytes"])
    if line_limit < MIN_LINE_BYTES or line_limit > MAX_LINE_BYTES:
        raise ObserverConfigError("max_jsonl_line_bytes must be between 1 MiB and 64 MiB")
    policy = str(raw["unexpected_server_request_policy"])
    if policy != "terminate":
        raise ObserverConfigError("unexpected_server_request_policy must be terminate")
    return ObserverConfig(
        schema_version=int(raw["schema_version"]),
        client_name=str(raw["client_name"]),
        client_title=str(raw["client_title"]),
        client_version=str(raw["client_version"]),
        experimental_api=bool(raw["experimental_api"]),
        initialize_timeout_seconds=float(raw["initialize_timeout_seconds"]),
        request_timeout_seconds=float(raw["request_timeout_seconds"]),
        reconcile_interval_seconds=float(raw["reconcile_interval_seconds"]),
        max_jsonl_line_bytes=line_limit,
        read_retry_attempts=int(raw["read_retry_attempts"]),
        read_retry_base_seconds=float(raw["read_retry_base_seconds"]),
        unexpected_server_request_policy=policy,
        runtime_home=resolve_runtime_home(repo_root, runtime_home),
    )

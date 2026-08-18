from __future__ import annotations

import sys
from pathlib import Path

from tests.codex_supervisor import fake_app_server
from tools.codex_supervisor.models import ObserverConfig


def make_observer_config(tmp_path: Path, **overrides: object) -> ObserverConfig:
    values: dict[str, object] = {
        "schema_version": 1,
        "client_name": "hmasd-codex-app-server-observer",
        "client_title": "HMASD Codex App Server Observer",
        "client_version": "0.1.0",
        "experimental_api": False,
        "initialize_timeout_seconds": 15.0,
        "request_timeout_seconds": 30.0,
        "reconcile_interval_seconds": 60.0,
        "max_jsonl_line_bytes": 1_048_576,
        "read_retry_attempts": 5,
        "read_retry_base_seconds": 0.25,
        "unexpected_server_request_policy": "terminate",
        "runtime_home": tmp_path / "runtime",
    }
    values.update(overrides)
    return ObserverConfig(**values)  # type: ignore[arg-type]


def write_fake_codex(tmp_path: Path) -> Path:
    script = Path(fake_app_server.__file__).resolve()
    if sys.platform == "win32":
        binary = tmp_path / "codex.cmd"
        binary.write_text(
            f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n',
            encoding="utf-8",
        )
    else:
        binary = tmp_path / "codex"
        binary.write_text(
            f"#!/usr/bin/env bash\nexec '{sys.executable}' '{script}' \"$@\"\n",
            encoding="utf-8",
        )
        binary.chmod(0o755)
    return binary

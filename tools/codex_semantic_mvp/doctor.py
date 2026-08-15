"""Read-only checks for the Codex semantic MVP baseline."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def _file_baseline(path: Path, display_path: str) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "path": display_path,
    }


def collect_baseline(repo_root: Path) -> dict[str, dict[str, Any]]:
    """Return hashes, sizes, and paths for the live Codex config files."""
    root = Path(repo_root)
    config_path = root / ".codex" / "config.toml"
    hooks_path = root / ".codex" / "hooks.json"
    return {
        "config_toml": _file_baseline(config_path, ".codex/config.toml"),
        "hooks_json": _file_baseline(hooks_path, ".codex/hooks.json"),
    }

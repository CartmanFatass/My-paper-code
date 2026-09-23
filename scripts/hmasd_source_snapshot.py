"""Prepare one retained Git worktree for a new admitted operation.

The caller verifies publication before this function and retains the returned
path with the operation. After collection, hmasd_snapshot_gc.py can reclaim a
verified terminal snapshot while preserving its operation and external outputs.
"""
from __future__ import annotations

import os
from pathlib import Path
import uuid


def prepare(source: Path, common_dir: Path, sha: str, git) -> Path:
    parent = common_dir / "hmasd-launch-sources"
    parent.mkdir(exist_ok=True)
    if parent.resolve() != parent.absolute():
        raise ValueError("snapshot storage must not be redirected")
    target = parent / uuid.uuid4().hex
    # A linked worktree shares the original operation/claim store. Never clone.
    git(source, "worktree", "add", "--detach", "--lock", str(target), sha, timeout=120.0)
    return target.resolve(strict=True)


def environment() -> dict[str, str]:
    env = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE"):
        env.pop(key, None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Configured site packages (including editable installs) remain an explicit
    # environment dependency; a source worktree is not a same-user sandbox.
    return env

"""Resolve the installed Codex binary. Never prefer version-hashed Desktop dirs."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

KNOWN_ROOTS = (
    Path.home() / ".local" / "bin",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "codex",
    Path(os.environ.get("LOCALAPPDATA", "")) / "codex",
    Path("C:/Program Files/codex"),
    Path("C:/Program Files (x86)/codex"),
)


class CodexBinaryError(FileNotFoundError):
    """Raised when no usable Codex binary can be resolved."""


def _is_executable(path: Path) -> bool:
    if not path.is_file():
        return False
    suffix = path.suffix.lower()
    if os.name == "nt":
        return suffix in {".exe", ".cmd", ".bat", ""} or os.access(path, os.X_OK)
    return os.access(path, os.X_OK)


def resolve_codex_binary(explicit: str | Path | None = None) -> Path:
    if explicit:
        candidate = Path(explicit)
        if not _is_executable(candidate):
            raise CodexBinaryError(f"explicit Codex binary is not executable: {candidate}")
        return candidate.resolve()
    env = os.environ.get("CODEX_BIN")
    if env:
        candidate = Path(env)
        if not _is_executable(candidate):
            raise CodexBinaryError(f"CODEX_BIN is not executable: {candidate}")
        return candidate.resolve()
    found = shutil.which("codex")
    if found:
        candidate = Path(found)
        if _is_executable(candidate):
            return candidate.resolve()
    names = ("codex.exe", "codex") if os.name == "nt" else ("codex",)
    for root in KNOWN_ROOTS:
        if not root or not str(root).strip("\\/") or not root.is_dir():
            continue
        for name in names:
            candidate = root / name
            if _is_executable(candidate):
                return candidate.resolve()
    raise CodexBinaryError("no Codex binary found via --codex-bin, CODEX_BIN, PATH, or known install roots")


def read_codex_version(binary: Path) -> str:
    completed = subprocess.run(
        [str(binary), "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,
    )
    text = (completed.stdout or completed.stderr or "").strip()
    if not text:
        raise CodexBinaryError(f"{binary} --version produced no output")
    return text.splitlines()[0].strip()

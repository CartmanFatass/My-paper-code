"""Which interpreter a surface must run under, on **this** host.

``tests/AGENTS.md`` states the rule in terms of two roles, not two file names:

- *scientific* surfaces need Python 3.10 with torch
- *control-plane* surfaces need Python 3.11+ for ``tomllib`` and do not need torch

The same repository is worked on from Windows and from WSL2, so the file name that
fills each role depends on the host. Hard-coding the Windows conda path made every
recommended command unrunnable from a Linux checkout, and — worse — invited the
"obvious" repair of pointing a Linux checkout at ``/mnt/c/.../python.exe``, which
runs a *Windows* torch build against Linux paths and silently crosses an OS
boundary that nothing would record.

Resolution order, per role:

1. an explicit environment variable, so an unusual host needs no code change
2. the host node selected by ``.codex/hmasd-compute.toml``
3. nothing for an unsupported platform

There is no fallback to ``sys.executable``: a command that claims to run on the
scientific interpreter must either name it or say it is absent. Guessing would
produce a run whose interpreter identity is not what the record says.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 scientific runtime
    import tomli as tomllib  # type: ignore[no-redef]

#: Independent environment overrides for the two configured roles.
SCIENTIFIC_ENV_VAR = "HMASD_SCIENTIFIC_PYTHON"
CONTROL_PLANE_ENV_VAR = "HMASD_CONTROL_PLANE_PYTHON"

_CONFIG_PATH = Path(__file__).resolve().parents[2] / ".codex" / "hmasd-compute.toml"
_ROLE_KEYS = {"scientific": "python", "control_plane": "control_plane_python"}


def _platform_key() -> str:
    """The exact key into the compute file's platform table.

    WSL2 reports ``linux``; that is correct, because a WSL checkout must use the
    Linux interpreters and not reach across ``/mnt/c`` for a Windows build.
    """

    return sys.platform


def _configured_interpreter(role: str) -> str:
    platform = _platform_key()
    if platform not in {"win32", "linux"}:
        return ""
    try:
        with _CONFIG_PATH.open("rb") as stream:
            config = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"cannot read compute configuration {_CONFIG_PATH}: {exc}") from exc
    if config.get("status") != "active":
        raise ValueError(f"compute configuration {_CONFIG_PATH} is missing or inactive")
    by_platform = config.get("control_plane_by_platform")
    if not isinstance(by_platform, dict):
        raise ValueError("compute configuration lacks control_plane_by_platform table")
    node = by_platform.get(platform)
    if not isinstance(node, str) or not node:
        raise ValueError(f"compute configuration has no control-plane node for {platform}")
    nodes = config.get("nodes")
    entry = nodes.get(node) if isinstance(nodes, dict) else None
    if not isinstance(entry, dict):
        raise ValueError(f"compute configuration has no node {node!r}")
    if entry.get("enabled") is False:
        raise ValueError(f"compute node {node!r} is disabled")
    key = _ROLE_KEYS[role]
    path = entry.get(key)
    if not isinstance(path, str) or not path.strip():
        raise ValueError(f"compute node {node!r} lacks {key}")
    return path


def _resolve(role: str, env_var: str) -> str:
    override = os.environ.get(env_var)
    if override:
        return override
    return _configured_interpreter(role)


def scientific_interpreter() -> str:
    """Python 3.10 with torch. Never install into it."""

    return _resolve("scientific", SCIENTIFIC_ENV_VAR)


def control_plane_interpreter() -> str:
    """Python 3.11+ (``tomllib``), no torch."""

    return _resolve("control_plane", CONTROL_PLANE_ENV_VAR)


def interpreter_is_present(path: str) -> bool:
    """Whether the named interpreter exists on this host.

    An empty path is absent, not present: a role with no configured default for
    this platform has no interpreter, and saying otherwise would let a caller
    build a command out of an empty string.
    """

    return bool(path) and Path(path).exists()


def describe_host() -> dict[str, object]:
    """Interpreter resolution as evidence, for a report or a refusal message."""

    scientific = scientific_interpreter()
    control_plane = control_plane_interpreter()
    return {
        "sys_platform": sys.platform,
        "platform_key": _platform_key(),
        "scientific_interpreter": scientific,
        "scientific_interpreter_present": interpreter_is_present(scientific),
        "scientific_interpreter_source": (
            SCIENTIFIC_ENV_VAR
            if os.environ.get(SCIENTIFIC_ENV_VAR)
            else ("compute configuration for this platform" if scientific else "unsupported platform")
        ),
        "control_plane_interpreter": control_plane,
        "control_plane_interpreter_present": interpreter_is_present(control_plane),
        "control_plane_interpreter_source": (
            CONTROL_PLANE_ENV_VAR
            if os.environ.get(CONTROL_PLANE_ENV_VAR)
            else ("compute configuration for this platform" if control_plane else "unsupported platform")
        ),
    }

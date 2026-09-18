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
2. the documented default for this platform
3. nothing — the caller is told the path and can report it missing

There is no fallback to ``sys.executable``: a command that claims to run on the
scientific interpreter must either name it or say it is absent. Guessing would
produce a run whose interpreter identity is not what the record says.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

#: Environment variables that override the documented defaults, in that order.
SCIENTIFIC_ENV_VAR = "HMASD_SCIENTIFIC_PYTHON"
CONTROL_PLANE_ENV_VAR = "HMASD_CONTROL_PLANE_PYTHON"

#: Documented defaults, keyed by platform family. ``win32`` values come from
#: ``CLAUDE.md`` and ``tests/AGENTS.md``; ``linux`` values from ``environments/README.md``.
_DEFAULTS: dict[str, dict[str, str]] = {
    "win32": {
        "scientific": "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
        "control_plane": "C:/Users/fires/.conda/envs/hmasd-science-tools/python.exe",
    },
    "linux": {
        "scientific": "/home/fires/.venvs/hmasd-linux-cpu/bin/python",
        "control_plane": "/home/fires/.venvs/hmasd-linux-science-tools/bin/python",
    },
}


def _platform_key() -> str:
    """The key into :data:`_DEFAULTS` for the running host.

    WSL2 reports ``linux``; that is correct, because a WSL checkout must use the
    Linux interpreters and not reach across ``/mnt/c`` for a Windows build.
    """

    return "win32" if sys.platform == "win32" else "linux"


def _resolve(role: str, env_var: str) -> str:
    override = os.environ.get(env_var)
    if override:
        return override
    return _DEFAULTS.get(_platform_key(), {}).get(role, "")


def scientific_interpreter() -> str:
    """Python 3.10 with torch. Never install into it."""

    return _resolve("scientific", SCIENTIFIC_ENV_VAR)


def control_plane_interpreter() -> str:
    """Python 3.11+ (``tomllib``), no torch."""

    return _resolve("control_plane", CONTROL_PLANE_ENV_VAR)


def interpreter_is_present(path: str) -> bool:
    """Whether the named interpreter exists on this host.

    An empty path is absent, not present: a role with no documented default for
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
            else "documented default for this platform"
        ),
        "control_plane_interpreter": control_plane,
        "control_plane_interpreter_present": interpreter_is_present(control_plane),
        "control_plane_interpreter_source": (
            CONTROL_PLANE_ENV_VAR
            if os.environ.get(CONTROL_PLANE_ENV_VAR)
            else "documented default for this platform"
        ),
    }

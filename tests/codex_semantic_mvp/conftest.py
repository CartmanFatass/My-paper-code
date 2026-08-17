import shutil
from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    """Return the repository root used by the activation tests."""
    return Path(__file__).resolve().parents[2]


def powershell_executable() -> str:
    """Prefer pwsh, then Windows PowerShell, so activation tests run on this host."""
    for name in ("pwsh", "powershell"):
        resolved = shutil.which(name)
        if resolved:
            return resolved
    raise FileNotFoundError("neither pwsh nor powershell is on PATH")

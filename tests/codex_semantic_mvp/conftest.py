from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    """Return the repository root used by the activation tests."""
    return Path(__file__).resolve().parents[2]

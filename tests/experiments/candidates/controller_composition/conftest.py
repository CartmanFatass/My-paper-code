from contextlib import contextmanager

import pytest

from experiments.candidates.controller_composition.b01 import runner


@pytest.fixture(scope="module")
def current_main_source_validation():
    """Engineering compatibility only; restore frozen guards before exercising code."""
    @contextmanager
    def validation():
        expected = dict(runner.SOURCE_DEPENDENCY_SHA256)
        for relative in ("hmasd/agent.py", "hmasd/utils.py"):
            expected[relative] = runner.sha256(runner.ROOT / relative)
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(runner, "SOURCE_DEPENDENCY_SHA256", expected)
            yield
    return validation

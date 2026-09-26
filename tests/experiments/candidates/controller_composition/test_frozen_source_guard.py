from pathlib import Path

import pytest

from experiments.candidates.controller_composition.b01 import runner


@pytest.mark.parametrize("changed", ["hmasd/agent.py", "hmasd/utils.py"])
def test_changed_core_refused_before_checkpoint_loading(monkeypatch, changed):
    expected = dict(runner.SOURCE_DEPENDENCY_SHA256)

    def digest(path):
        relative = Path(path).relative_to(runner.ROOT).as_posix()
        return "0" * 64 if relative == changed else expected[relative]

    monkeypatch.setattr(runner, "sha256", digest)
    monkeypatch.setattr(runner.torch, "load", lambda *a, **k: pytest.fail("loaded before refusal"))
    with pytest.raises(ValueError, match=f"source dependency differs: {changed}"):
        runner.validate_sources({i: Path("unused.pt") for i in runner.SOURCE})
    assert runner.SOURCE_DEPENDENCY_SHA256 == expected

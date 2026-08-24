from pathlib import Path

import pytest

from tools.codex_supervisor.durability.effects import EffectJournal


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def current_kernel_claim_for_legacy_effect_fixtures(monkeypatch: pytest.MonkeyPatch):
    """Keep historical direct-claim fixtures behind the current DB fence.

    Production never receives this adapter. Tests that exercise a stale
    pre-v11 writer use raw transition SQL/the saved original method so they
    continue to prove the database rejection rather than this fixture path.
    """

    original = EffectJournal._claim_write

    def claim(self, effect_id: str, **kwargs):
        current = self.get(effect_id)
        if current.state == "PREPARED" and current.kernel_claim_marker is None:
            with self._tx():
                self.seal_effect(effect_id)
                self._arm_kernel_claim(effect_id)
                return original(self, effect_id, **kwargs)
        return original(self, effect_id, **kwargs)

    monkeypatch.setattr(EffectJournal, "_claim_write", claim)
    yield

"""Exercise the real effect-free scanner without launching or importing the consumer."""
import hashlib
import json
from pathlib import Path

import pytest

from scripts.hmasd_launch import LaunchRefusal, _validate_guard_contract


ROOT = Path(__file__).resolve().parents[5]
ENTRY = "experiments/candidates/typed_joint_skill_decision/b06_bank_consumer/run.py"
DIRECTION = "typed_joint_skill_decision"


def test_actual_consumer_matches_native_guard_contract():
    _validate_guard_contract(ROOT / ENTRY, DIRECTION)


def test_original_pinned_variable_declaration_is_refused(tmp_path):
    current = (ROOT / ENTRY).read_bytes()
    literal = b'direction="typed_joint_skill_decision"'
    assert current.count(literal) == 1
    original = current.replace(literal, b"direction=c.DIRECTION")
    prior_input = json.loads((ROOT / "docs/research/candidates/typed_joint_skill_decision/B07_CONSUMER_A02_INPUT.json").read_bytes())
    assert hashlib.sha256(original).hexdigest() == prior_input["executable_sources"][ENTRY]
    entry = tmp_path / "original_consumer.py"
    entry.write_bytes(original)
    with pytest.raises(LaunchRefusal, match="runner must contain exactly one require_admission") as failure:
        _validate_guard_contract(entry, DIRECTION)
    assert failure.value.exit_code == 4

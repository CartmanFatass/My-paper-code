"""Pure table checks: no tokenizer, weights, RNG, native host or model query."""
import copy

import pytest

from experiments.candidates.typed_joint_skill_decision.codec import parse_state, render_state
from experiments.candidates.typed_joint_skill_decision.contract import make_features


def record():
    precise = 1000.1234567890123
    return make_features(
        [[precise + i, 2000.0, 100.0] for i in range(6)],
        [[precise + i, 4000.9876543210987] for i in range(50)],
        [2500.0, 2500.0, 0.0],
        [{"construction_slot": slot, "kind": "subset_relay", "k": 4,
          "assigned_targets_xyz": [[precise + i + slot, 100.0 + slot, 100.0] for i in range(6)]}
         for slot in (0, 3, 7)])


def test_exact_record_and_sparse_slots_survive_table():
    original = record()
    assert parse_state(render_state(original)) == original
    assert [p["construction_slot"] for p in parse_state(render_state(original))["plans"]] == [0, 3, 7]
    # The actual binary64 value must survive, rather than a rounded display value.
    assert parse_state(render_state(original))["initial_uav_xyz"][0][0].hex() == original["initial_uav_xyz"][0][0].hex()


def test_reverse_only_changes_display_order():
    original = record()
    expected = copy.deepcopy(original)
    expected["display_order"].reverse()
    assert parse_state(render_state(original, reverse=True)) == expected


@pytest.mark.parametrize("hidden", ["Q", "world", "static_score", "source_file"])
def test_outcome_and_provenance_injection_refused(hidden):
    original = record()
    original[hidden] = 1
    with pytest.raises(ValueError):
        render_state(original)


def test_extra_or_missing_table_data_refused():
    text = render_state(record())
    with pytest.raises(ValueError):
        parse_state(text + "\nQ 1 2 3")
    with pytest.raises(ValueError):
        parse_state(text.rsplit(" ", 1)[0])
    with pytest.raises(ValueError):
        parse_state(text.replace("500", "501", 1) if "500" in text.splitlines()[0]
                    else "tampered header\n" + "\n".join(text.splitlines()[1:]))

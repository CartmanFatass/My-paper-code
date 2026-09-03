"""Tests for the ``UCOPE-B-EXPLORE-PAID-ACQUISITION-B01`` card.

The object is **not run and has no runner**. These tests cover only what the card freezes: the
loader introduced here, the frozen-constants table checked against the frozen code and against
the remedies runner it inherits its learner from, the competence-free branch statistic's exact
relation to the frozen ``acquisition_pass``, and the card's required structure (branch order,
empty deviations / could-not-verify sections, empty prediction slots).
"""

from __future__ import annotations

from fractions import Fraction
import importlib.util
from pathlib import Path
import re
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    BATCH_SIZE,
    CONTEXTS,
    K_EVAL,
    K_TRAIN,
    TARGET_CONTEXT_ID,
    context_id,
)
from experiments.candidates.ucope.competence_first_scout_r01.oracle import (  # noqa: E402
    build_oracle,
)

CARD = PROJECT_ROOT / "docs/research/candidates/ucope/UCOPE_PAID_ACQUISITION_B01_CARD_20260903.md"
OBJECT_ID = "UCOPE-B-EXPLORE-PAID-ACQUISITION-B01"

EXPECTED_KEYS = {
    "TARGET_CONTEXT_ID", "oracle_baseline_at_target", "oracle_probe_value_at_target",
    "oracle_direct_probe_at_target", "oracle_net_acquisition_at_target",
    "oracle_probe_context_count", "oracle_baseline_period", "held_out_support",
    "hinge_margin", "hinge_weight", "hinge_witness_pair", "tail_updates", "root_updates",
    "tail_rows_per_policy", "episodes_per_context", "learning_rate", "batch_size",
    "draw_offset", "tail_reproduction_tolerance", "eps_L", "majority_threshold",
    "policies", "thread_cap",
}


# --------------------------------------------------------------------------- the loader


def load_frozen_constants(card_path: Path = CARD) -> dict[str, str]:
    """Parse the card's 'Frozen constants' table into {name: literal}.

    The card is the authority for this object; the loader exists so the constants can be checked
    against the frozen code rather than retyped into a runner that does not exist yet.
    """
    text = card_path.read_text(encoding="utf-8")
    marker = "**Frozen constants**"
    if marker not in text:
        raise ValueError("the card has no frozen-constants table")
    block = text.split(marker, 1)[1]
    constants: dict[str, str] = {}
    for line in block.splitlines():
        match = re.fullmatch(r"\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|", line.strip())
        if match:
            constants[match.group(1)] = match.group(2)
        elif constants and line.strip() and not line.strip().startswith("|"):
            break
    if not constants:
        raise ValueError("the frozen-constants table parsed empty")
    return constants


@pytest.fixture(scope="module")
def constants():
    return load_frozen_constants()


@pytest.fixture(scope="module")
def card_text():
    return CARD.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def remedies():
    spec = importlib.util.spec_from_file_location(
        "ucope_tail_margin_remedies_r01",
        PROJECT_ROOT / "scripts/run_ucope_tail_margin_remedies_r01.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_loader_finds_exactly_the_expected_constants(constants):
    assert set(constants) == EXPECTED_KEYS
    assert all(value.strip() for value in constants.values())


def test_the_loader_refuses_a_document_without_the_table(tmp_path):
    empty = tmp_path / "no-table.md"
    empty.write_text("# nothing here\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no frozen-constants table"):
        load_frozen_constants(empty)
    headed = tmp_path / "empty-table.md"
    headed.write_text("**Frozen constants**\n\nnot a table at all\n", encoding="utf-8")
    with pytest.raises(ValueError, match="parsed empty"):
        load_frozen_constants(headed)


# --------------------------------------------------------------------------- oracle constants


def test_the_oracle_constants_are_the_frozen_ones(constants):
    oracle = build_oracle()
    target = oracle[TARGET_CONTEXT_ID]
    assert constants["TARGET_CONTEXT_ID"] == TARGET_CONTEXT_ID == "LINKED-p17_20-c9_100"
    assert Fraction(constants["oracle_baseline_at_target"]) == target["baseline"]
    assert Fraction(constants["oracle_probe_value_at_target"]) == target["probe_value"]
    assert Fraction(constants["oracle_direct_probe_at_target"]) == target["direct_probe"]
    assert Fraction(constants["oracle_net_acquisition_at_target"]) == target["net_acquisition"]
    assert int(constants["oracle_baseline_period"]) == target["baseline_period"]
    assert target["action"] == "PROBE"


def test_the_target_is_the_unique_context_where_paying_pays(constants):
    oracle = build_oracle()
    probe_cells = [context_id(c) for c in CONTEXTS if oracle[context_id(c)]["action"] == "PROBE"]
    positive = [context_id(c) for c in CONTEXTS
                if oracle[context_id(c)]["net_acquisition"] > 0]
    assert probe_cells == positive == [TARGET_CONTEXT_ID]
    assert int(constants["oracle_probe_context_count"]) == len(probe_cells) == 1
    assert len(CONTEXTS) == 8


def test_paying_is_always_a_real_cost():
    oracle = build_oracle()
    assert all(oracle[context_id(c)]["direct_probe"] < 0 for c in CONTEXTS)


def test_the_net_acquisition_is_the_recurring_regret_of_refusing_to_pay(constants):
    """+0.021437 is exactly what a policy loses by choosing IMMEDIATE at the target."""
    oracle = build_oracle()
    target = oracle[TARGET_CONTEXT_ID]
    net = Fraction(constants["oracle_net_acquisition_at_target"])
    assert net == target["probe_value"] - target["baseline"]
    assert float(net) == pytest.approx(0.021437, abs=5e-7)


# --------------------------------------------------------------------------- learner constants


def test_the_treatment_learner_constants_match_the_remedies_object(constants, remedies):
    margin_aware = remedies.ARMS["MARGIN-AWARE"]
    assert float(constants["hinge_margin"]) == remedies.HINGE_MARGIN == 0.024022
    assert float(constants["hinge_weight"]) == remedies.HINGE_WEIGHT == 1.0
    assert tuple(int(v) for v in constants["hinge_witness_pair"].split(",")) \
        == remedies.HINGE_WITNESS_PAIR == (5, 9)
    assert int(constants["tail_updates"]) == margin_aware["tail_updates"] == 1_600
    assert int(constants["root_updates"]) == remedies.ROOT_UPDATES == 3_200
    assert int(constants["episodes_per_context"]) == margin_aware["episodes_per_context"] == 40_960
    assert int(constants["tail_rows_per_policy"]) == 2 * margin_aware["episodes_per_context"]
    assert float(constants["learning_rate"]) == remedies.LEARNING_RATE == 3e-3
    assert int(constants["batch_size"]) == BATCH_SIZE == 256
    assert int(constants["draw_offset"]) == remedies.REMEDIES_OFFSET == 2_000_000
    assert float(constants["eps_L"]) == remedies.EPS_L == 0.10
    assert int(constants["majority_threshold"]) == remedies.MAJORITY == 4


def test_the_hinge_witness_stays_inside_the_training_support(constants):
    witness = tuple(int(v) for v in constants["hinge_witness_pair"].split(","))
    assert set(witness) <= set(K_TRAIN)
    assert not set(witness) & set(K_EVAL)
    assert tuple(int(v) for v in constants["held_out_support"].split(",")) == K_EVAL


def test_the_remaining_scalars_are_the_carded_ones(constants):
    assert float(constants["tail_reproduction_tolerance"]) == 1e-6
    assert int(constants["policies"]) == 6
    assert int(constants["thread_cap"]) == 1


def test_the_draw_offset_is_disjoint_from_every_published_range(constants):
    offset = int(constants["draw_offset"])
    episodes = int(constants["episodes_per_context"])
    assert offset % 20 == 0
    assert offset > 5_119 and offset > 319
    assert offset >= 1_000_000 + 81_920      # clear of the competence/root draw and its length
    assert offset + episodes <= 2_081_920    # the prefix the remedies object already generated


# ------------------------------------------------- A_paid against the frozen acquisition predicate


def test_a_paid_is_the_frozen_predicate_minus_its_competence_conjunct(card_text):
    source = (PROJECT_ROOT / "experiments/candidates/ucope/competence_first_scout_r01"
              / "evaluation.py").read_text(encoding="utf-8")
    frozen = source.split("acquisition = bool(", 1)[1].split(")\n", 1)[0]
    # The five conjuncts of the frozen predicate.
    assert "item.competence_pass" in frozen
    assert 'audit["root_actions"][TARGET_CONTEXT_ID] == "PROBE"' in frozen
    assert 'audit["target_delta_acquisition"] > 0' in frozen
    assert 'audit["direct_probe_component"] < 0' in frozen
    assert 'action == "IMMEDIATE" for cell, action in audit["root_actions"].items()' in frozen
    # The card keeps the four non-competence conjuncts and drops exactly one.
    definition = card_text.split("> **`A_paid`**", 1)[1].split("\n\n", 1)[0]
    assert '`root_action(TARGET) == "PROBE"`' in definition
    assert "`target_delta_acquisition > 0`" in definition
    assert "`direct_probe_component < 0`" in definition
    assert '`root_action(cell) == "IMMEDIATE"` for every other cell' in definition
    assert "competence_pass" not in definition
    assert "with its `competence_pass` conjunct removed and nothing else\nchanged" in card_text


def test_competence_is_recorded_and_never_gates(card_text):
    assert "competence recorded, not required" in card_text
    assert "**None of these fields appears in the reading rule of section 8.**" in card_text
    for field in ("c_even_count", "c_even_flags", "agreement_gate_count",
                  "agreement_gate_flags", "margin_sign_per_policy",
                  "frozen_conditional_acquisition"):
        assert f"`{field}`" in card_text


# --------------------------------------------------------------------------- card structure


def test_the_card_declares_the_object_and_that_it_is_not_run(card_text):
    assert OBJECT_ID in card_text
    assert "**Not run.**" in card_text
    assert "`A/RECON`" in card_text
    assert "`B/EXPLORE`" in card_text


def test_the_branch_names_appear_in_the_carded_order(card_text):
    names = ("PA-A", "PA-B", "PA-C", "PA-D", "PA-E")
    positions = [card_text.index(f"`{name} —") for name in names]
    assert positions == sorted(positions)
    labels = ("PAID_ACQUISITION_POSITIVE", "PAID_ACQUISITION_MAJORITY", "REFERENCE_ONLY",
              "REFERENCE_NOT_POSITIVE", "UNCLEAR")
    assert [card_text.index(label) for label in labels] == sorted(
        card_text.index(label) for label in labels)


def test_both_prediction_slots_are_present_and_recorded_before_launch(card_text):
    """The slots were written empty; the predictions were recorded into them before launch."""
    section = card_text.split("## 12. Predictions requested", 1)[1].split("## 13.", 1)[0]
    assert "**Owner (2026-09-03, before launch):**" in section
    assert "**Reviewer (2026-09-03, before launch):**" in section
    assert "_(empty — to be recorded before the run)_" not in section
    quotes = [line for line in section.splitlines() if line.startswith(">")]
    assert len(quotes) >= 2
    owner, reviewer = section.split("**Reviewer", 1)
    assert "`PA-B`" in owner and "`PA-B`" in reviewer


def test_deviations_and_could_not_verify_are_present_and_empty(card_text):
    deviations = card_text.split("## 13. Deviations", 1)[1].split("## 14.", 1)[0]
    could_not = card_text.split("## 14. Could not verify", 1)[1]
    assert deviations.strip().startswith("_(empty")
    assert could_not.strip().startswith("_(empty")
    assert "no run has taken place" in deviations
    assert "no run has taken place" in could_not


def test_the_three_witness_follow_up_is_mentioned_once_and_is_not_an_arm(card_text):
    assert card_text.count("three-witness") == 1
    section = card_text.split("## 11. Parallel follow-up", 1)[1].split("## 12.", 1)[0]
    assert "not an arm" in section
    arms = card_text.split("## 5. Arms", 1)[1].split("## 6.", 1)[0]
    assert "three-witness" not in arms
    assert "MARGIN-AWARE-TREATMENT" in arms and "EXACT-REFERENCE" in arms


def test_the_runner_is_the_single_one_the_card_names():
    """The card was written before the runner; the runner now exists and is unique."""
    runners = sorted((PROJECT_ROOT / "scripts").glob("run_ucope_paid_acquisition*.py"))
    assert [path.name for path in runners] == ["run_ucope_paid_acquisition_b01.py"]

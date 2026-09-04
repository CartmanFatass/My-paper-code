"""Tests for the ``UCOPE-B-EXPLORE-TAIL-MARGIN-REMEDIES-R01`` runner.

The load-bearing one is `test_the_hinge_never_touches_a_held_out_period`: the frozen §4
odd-training / even-held-out separation is what makes `MARGIN-AWARE` a legal object rather than
a leak, so it is asserted directly on the periods the hinge construction actually reads.
"""

from __future__ import annotations

from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

numpy = pytest.importorskip("numpy")
torch = pytest.importorskip("torch")

from experiments.candidates.ucope.competence_first_scout_r01 import training  # noqa: E402
from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    B1_SEEDS,
    CONTEXTS,
    K_EVAL,
    K_TRAIN,
)
from experiments.candidates.ucope.competence_first_scout_r01.model import (  # noqa: E402
    BellmanScorer,
    optimizer_for,
    tail_basis,
)


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = _load("ucope_tail_margin_remedies_r01", "run_ucope_tail_margin_remedies_r01.py")
RC = RUNNER.RC
CR = RUNNER.CR
SELECTION = CR._n_selection()

SMALL_LARGE = 640
SMALL_BASE = 320
SMALL_ARMS = {
    "LARGER-N": {"episodes_per_context": SMALL_LARGE, "tail_updates": 4, "hinge": False},
    "BUDGET-100X": {"episodes_per_context": SMALL_BASE, "tail_updates": 8, "hinge": False},
    "MARGIN-AWARE": {"episodes_per_context": SMALL_BASE, "tail_updates": 4, "hinge": True},
}


@pytest.fixture(scope="module")
def small_blocks():
    saved = SELECTION.OFFSET
    SELECTION.OFFSET = RUNNER.REMEDIES_OFFSET
    try:
        ordered, _labels = CR.canonical_order(
            SELECTION.generate_columns(B1_SEEDS[0], SMALL_BASE))
    finally:
        SELECTION.OFFSET = saved
    return ordered, CR.stage_designs(ordered, 0)


# --------------------------------------------------------------------------- frozen constants


def test_the_three_arms_are_the_carded_ones():
    assert RUNNER.OBJECT_ID == "UCOPE-B-EXPLORE-TAIL-MARGIN-REMEDIES-R01"
    assert RUNNER.EVIDENCE_CLASS == "B/EXPLORE"
    assert set(RUNNER.ARMS) == {"LARGER-N", "BUDGET-100X", "MARGIN-AWARE"}
    assert RUNNER.ARMS["LARGER-N"] == {
        "episodes_per_context": 81_920, "tail_updates": 1_600, "hinge": False}
    assert RUNNER.ARMS["BUDGET-100X"] == {
        "episodes_per_context": 40_960, "tail_updates": 16_000, "hinge": False}
    assert RUNNER.ARMS["MARGIN-AWARE"] == {
        "episodes_per_context": 40_960, "tail_updates": 1_600, "hinge": True}
    assert RUNNER.ROOT_UPDATES == 3_200
    assert RUNNER.LEARNING_RATE == 3e-3
    assert (RUNNER.HINGE_MARGIN, RUNNER.HINGE_WEIGHT) == (0.024022, 1.0)
    assert RUNNER.AGREEMENT_GATE == Fraction(19, 20)
    assert RUNNER.MAJORITY == 4
    assert RUNNER.BASELINE_AGREEMENT_COUNT == 3
    assert RUNNER.BASELINE_COUNT0_GAPS == (
        -0.000333, -0.006212, 0.023598, 0.011790, -0.009773, 0.007736)


def test_the_offset_is_fresh_and_disjoint():
    assert RUNNER.REMEDIES_OFFSET == 2_000_000
    assert RUNNER.REMEDIES_OFFSET % 20 == 0
    # Disjoint from 0..5,119 (B1, ladders, R02), 0..319 (ASSESS) and 1,000,000..1,081,919.
    assert RUNNER.REMEDIES_OFFSET > 1_000_000 + RUNNER.LARGEST_EPISODES_PER_CONTEXT


def test_the_offset_is_restored_even_when_the_run_refuses(tmp_path):
    saved = SELECTION.OFFSET
    (tmp_path / "taken").mkdir()
    with pytest.raises(RUNNER.LaunchRefusal, match="create-once"):
        RUNNER.run_object(tmp_path / "taken")
    assert SELECTION.OFFSET == saved


# ------------------------------------------------- the odd/even separation (the load-bearing one)


def test_the_hinge_never_touches_a_held_out_period(monkeypatch):
    """The frozen §4 separation, asserted on the periods the hinge construction reads."""
    seen: list[int] = []
    original = RUNNER.tail_basis

    def spy(*, belief, period):
        seen.append(int(period))
        return original(belief=belief, period=period)

    monkeypatch.setattr(RUNNER, "tail_basis", spy)
    RUNNER.hinge_directions([0.0, 0.25, 0.5, 0.75, 1.0])
    assert set(seen) == {5, 9}
    assert set(seen) <= set(K_TRAIN)
    assert not set(seen) & set(K_EVAL)
    assert RUNNER.HINGE_WITNESS_PAIR == (5, 9)
    assert RUNNER.HELD_OUT_DECISION_PAIR == (6, 8)


def test_a_witness_pair_outside_the_training_support_is_refused(monkeypatch):
    monkeypatch.setattr(RUNNER, "HINGE_WITNESS_PAIR", (6, 8))
    with pytest.raises(RUNNER.LaunchRefusal, match="K_TRAIN"):
        RUNNER.hinge_directions([0.5])


def test_the_training_rows_only_ever_carry_training_support_periods(small_blocks):
    ordered, _blocks = small_blocks
    assert set(int(value) for value in numpy.unique(ordered["period"])) == set(K_TRAIN)
    assert not set(int(value) for value in numpy.unique(ordered["period"])) & set(K_EVAL)


def test_the_hinge_direction_is_exactly_twice_the_held_out_direction():
    beliefs = [3e-05, 0.000969, 0.030201, 0.5, 0.969799, 0.99997]
    witness = RUNNER.hinge_directions(beliefs)
    for index, belief in enumerate(beliefs):
        held_out = (numpy.asarray(tail_basis(belief=belief, period=6))
                    - numpy.asarray(tail_basis(belief=belief, period=8)))
        assert witness[index] == pytest.approx(2.0 * held_out, abs=1e-15)


# --------------------------------------------------------------------------- the step


def test_the_step_without_a_hinge_is_the_frozen_step_bit_for_bit(small_blocks):
    _ordered, blocks = small_blocks
    x = blocks["tail"]["x"][:256]
    z = blocks["tail"]["z"][:256]
    y = blocks["tail"]["y"][:256]

    def run(step):
        model = BellmanScorer.build("tail", False, "step-parity|fold-0|BC")
        optimizer = optimizer_for(model, RUNNER.LEARNING_RATE)
        activity = CR._fresh_activity()
        for _ in range(3):
            step(model, optimizer, x, z, y, activity, "tail")
        return [float(v) for v in model.state_dict()["beta"].tolist()], activity

    frozen, frozen_activity = run(training._step)
    mine, mine_activity = run(lambda *args: RUNNER.step_with_hinge(*args, hinge_batch=None))
    assert mine == frozen
    assert mine_activity == frozen_activity


def test_the_hinge_is_inactive_once_its_margin_is_met_and_active_below_it():
    beta = torch.zeros(5, dtype=torch.float32)
    satisfied = torch.tensor([[RUNNER.HINGE_MARGIN * 10, 0.0, 0.0, 0.0, 0.0]], dtype=torch.float32)
    beta = beta.clone()
    beta[0] = 1.0
    assert float(RUNNER._hinge_loss(satisfied, beta)) == 0.0
    violating = torch.tensor([[0.0, 0.0, 0.0, 0.0, 0.0]], dtype=torch.float32)
    assert float(RUNNER._hinge_loss(violating, beta)) == pytest.approx(RUNNER.HINGE_MARGIN)


def test_the_hinge_changes_the_learned_vector(small_blocks):
    _ordered, blocks = small_blocks
    white = CR.whitening(blocks["tail"]["design64"], stage="tail")
    beliefs = blocks["tail"]["design64"][:, 1]
    hinge = RUNNER.hinge_directions(beliefs)
    plain, _init = RUNNER.train_tail(
        seed_id=B1_SEEDS[0], fold_id=0, blocks=blocks, white=white, updates=8,
        hinge_design=None, activity=CR._fresh_activity())
    hinged, _init2 = RUNNER.train_tail(
        seed_id=B1_SEEDS[0], fold_id=0, blocks=blocks, white=white, updates=8,
        hinge_design=hinge, activity=CR._fresh_activity())
    assert plain != hinged
    assert len(plain) == len(hinged) == 5


# --------------------------------------------------------------------------- margins


def test_the_margin_record_is_exact_linear_algebra():
    rng = numpy.random.default_rng(20260903)
    for _ in range(5):
        beta = numpy.asarray(RUNNER.BETA_STAR) + rng.normal(size=5) * 0.05
        record = RUNNER.margin_record(beta)
        for row in record["cells"].values():
            assert row["gap"] == pytest.approx(row["truth_gap"] + row["projection"], abs=1e-15)
            assert row["flipped"] is (row["gap"] < 0.0)
        assert record["count0_gap"] == record["cells"]["0"]["gap"]


def test_beta_star_itself_flips_nothing_and_matches_the_published_truth_gap():
    record = RUNNER.margin_record(RUNNER.BETA_STAR)
    assert record["counts_flipped"] == []
    assert record["count0_projection"] == 0.0
    assert record["count0_truth_gap"] == pytest.approx(0.008007, abs=5e-7)


def test_value_bias_is_zero_at_the_exact_solve(small_blocks):
    _ordered, blocks = small_blocks
    beta_star_policy = CR.exact_solve(blocks["tail"]["design64"], blocks["tail"]["targets64"])
    bias = RUNNER.value_bias(blocks, beta_star_policy, beta_star_policy)
    assert bias["excess_train_mse_over_exact_solve"] == pytest.approx(0.0, abs=1e-18)
    assert bias["excess_train_mse_ratio"] == pytest.approx(1.0)
    assert bias["max_abs_held_out_value_error_vs_beta_star"] >= 0.0


# --------------------------------------------------------------------------- the reading rule


def _policies(agreement, gaps, c_even=None):
    names = list(RUNNER.ARMS)
    rows = []
    for index in range(6):
        arms = {}
        for name in names:
            arms[name] = {
                "agreement_within_gate": agreement[name][index],
                "margin": {"count0_gap": gaps[name][index]},
                "competence": {"competence_pass": (
                    False if c_even is None else c_even[name][index])},
            }
        rows.append({"arms": arms})
    return rows


def _uniform(value):
    return {name: [value] * 6 for name in RUNNER.ARMS}


def _gaps(values):
    return {name: list(values) for name in RUNNER.ARMS}


def test_rule_m_a_when_an_arm_reaches_all_six():
    agreement = _uniform(False)
    agreement["MARGIN-AWARE"] = [True] * 6
    reading = RUNNER.apply_reading_rule(_policies(agreement, _gaps([0.02] * 6)))
    assert reading["branch"] == "M-A"
    assert reading["arms_at_all_six"] == ["MARGIN-AWARE"]


def test_rule_m_b_when_an_arm_reaches_the_majority_but_not_all():
    agreement = _uniform(False)
    agreement["BUDGET-100X"] = [True] * 5 + [False]
    reading = RUNNER.apply_reading_rule(_policies(agreement, _gaps([0.02] * 6)))
    assert reading["branch"] == "M-B"
    assert reading["arms_at_majority"] == ["BUDGET-100X"]


def test_rule_m_c_needs_every_negative_baseline_turned_positive():
    agreement = _uniform(False)
    agreement["MARGIN-AWARE"] = [True] * 3 + [False] * 3
    reading = RUNNER.apply_reading_rule(_policies(agreement, _gaps([0.01] * 6)))
    assert reading["branch"] == "M-C"
    assert reading["arms_improving"] == list(RUNNER.ARMS)


def test_rule_m_d_when_nothing_moves():
    gaps = _gaps(RUNNER.BASELINE_COUNT0_GAPS)
    reading = RUNNER.apply_reading_rule(_policies(_uniform(False), gaps))
    assert reading["branch"] == "M-D"


def test_rule_m_e_on_a_partial_improvement():
    gaps = _gaps(list(RUNNER.BASELINE_COUNT0_GAPS))
    for name in gaps:
        gaps[name][0] = 0.004      # one negative baseline turned positive, the other two not
    reading = RUNNER.apply_reading_rule(_policies(_uniform(False), gaps))
    assert reading["branch"] == "M-E"


def test_the_branch_order_is_the_carded_order():
    source = (PROJECT_ROOT / "scripts/run_ucope_tail_margin_remedies_r01.py").read_text(
        encoding="utf-8")
    positions = [source.index(f'"branch": "{name}"')
                 for name in ("M-A", "M-B", "M-C", "M-D", "M-E")]
    assert positions == sorted(positions)


def test_the_rule_carries_the_full_c_even_counts():
    c_even = _uniform(False)
    c_even["MARGIN-AWARE"] = [True] * 6
    agreement = _uniform(False)
    agreement["MARGIN-AWARE"] = [True] * 6
    reading = RUNNER.apply_reading_rule(
        _policies(agreement, _gaps([0.02] * 6), c_even=c_even))
    assert reading["numbers"]["c_even_counts"]["MARGIN-AWARE"] == 6
    assert reading["numbers"]["c_even_counts"]["LARGER-N"] == 0


# --------------------------------------------------------------------------- end to end


def test_a_miniature_run_produces_a_complete_record(tmp_path, monkeypatch):
    monkeypatch.setattr(RUNNER, "ROOT_UPDATES", 8)
    monkeypatch.setattr(CR, "_configure_topology", lambda cap: None)
    path = RUNNER.run_object(tmp_path / "mini", thread_cap=2,
                             largest_episodes_per_context=SMALL_LARGE, arms=SMALL_ARMS)
    record = json.loads(Path(path).read_text(encoding="utf-8"))

    assert record["complete"] is True
    assert record["object_id"] == "UCOPE-B-EXPLORE-TAIL-MARGIN-REMEDIES-R01"
    assert record["index_law"]["offset"] == 2_000_000
    assert record["odd_training_even_held_out_separation"][
        "held_out_periods_used_in_training"] == []
    assert record["odd_training_even_held_out_separation"][
        "hinge_witness_inside_training_support"] is True
    assert len(record["policies"]) == 6
    assert record["counts"]["environment_episodes"] == 3 * SMALL_LARGE * len(CONTEXTS)
    assert record["counts"]["hinge_rows_built"] == 6 * 2 * SMALL_BASE
    assert record["counts"]["nonfinite_events"] == 0
    assert record["reading_rule"]["branch"] in {"M-A", "M-B", "M-C", "M-D", "M-E"}
    assert record["admission"]["passed"] is True

    for policy in record["policies"]:
        assert set(policy["arms"]) == set(SMALL_ARMS)
        assert policy["arms"]["LARGER-N"]["tail_rows"] == 2 * SMALL_LARGE
        assert policy["arms"]["BUDGET-100X"]["tail_rows"] == 2 * SMALL_BASE
        assert policy["arms"]["MARGIN-AWARE"]["hinge"] is True
        assert policy["arms"]["LARGER-N"]["hinge"] is False
        for name, arm in policy["arms"].items():
            assert set(arm["margin"]["cells"]) == {str(i) for i in range(7)}
            assert set(arm["competence"]) >= {
                "all_finite", "all_unique", "oracle_root_match", "max_regret",
                "minimum_tail_agreement", "competence_pass"}
            assert arm["value_bias"]["tail_train_mse"] >= 0.0
            for stage in ("tail", "root"):
                check = arm["whitening"][stage]
                assert check["cholesky_reconstruction_max_abs"] <= 1e-10
                assert check["gram_smallest_eigenvalue"] > 1e-6
        # The three arms train different tails, so their agreements need not agree.
        assert policy["reference"]["MARGIN-AWARE"]["margin"]["count0_gap"] != 0.0

    exposure = record["exposure_line"]
    assert {row["arm"] for row in exposure["rows"]} == set(SMALL_ARMS)
    assert len(exposure["rows"]) == 6 * 3 * 2
    assert exposure["learner_can_move_in_its_budget"] is True
    assert SELECTION.OFFSET == 1_000_000

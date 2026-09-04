"""UCOPE-A-INSTRUMENTATION-TAIL-AGREEMENT-COMPETENCE-CHECK-R01.

These tests *are* the instrumentation check frozen by
``docs/research/candidates/ucope/UCOPE_INSTRUMENTATION_CHECK_R01_CARD_20260902.md``.
They are outcome-free: no scientific arm is trained at ladder scale, no polarity is
produced, and no published R01 record is modified.

Groups (see the card):

* ``M1`` tail agreement at known true values, on both ladder arms;
* ``M2`` the competence predicate's components (regret, tail agreement, oracle root vector);
* ``M3`` the per-coordinate Bellman displacement statistic (which tensors it reads for
  ``FT-XF-FLEX``; whether the residual is inside the aggregate and outside the beta line);
* ``M4`` the two recorded anomalies.

Rows named ``*_published_*`` read the untracked run directories of R01 rung 1 / rung 2 and
skip when those are absent. They read only fields that
``evaluation.validate_policy_evaluation`` and ``ladder.validate_complete`` already read.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from math import comb
from pathlib import Path
import importlib.util
import json
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.competence_first_scout_r01 import evaluation as evaluation_module  # noqa: E402
from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    ASSESS_SEEDS,
    B1_SEEDS,
    CONTEXTS,
    K_EVAL,
    LADDER_ARMS,
    RunBinding,
    ScoutConfig,
    context_id,
)
from experiments.candidates.ucope.competence_first_scout_r01.evaluation import (  # noqa: E402
    evaluate_policy,
    validate_policy_evaluation,
)
from experiments.candidates.ucope.competence_first_scout_r01.model import build_arm  # noqa: E402
from experiments.candidates.ucope.competence_first_scout_r01.oracle import (  # noqa: E402
    build_oracle,
    expected_tail,
    joint_count_probability,
    optimal_tail,
    posterior_short,
    tail_return,
)

RUN_ROOT = PROJECT_ROOT / "temp" / "directions" / "ucope" / "exp"
RUNGS = {
    "rung-1": RUN_ROOT / "exposure_ladder_r01_rung1_20260902" / "complete",
    "rung-2": RUN_ROOT / "exposure_ladder_r01_rung2_20260902" / "complete",
}
LADDER_SCRIPT = PROJECT_ROOT / "scripts" / "run_ucope_exposure_ladder_rung1.py"


def _load_ladder():
    spec = importlib.util.spec_from_file_location("ucope_exposure_ladder_check", LADDER_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Independent reference implementation.
#
# Written from the host's closed forms, not by calling ``audit_policy_choices`` or
# ``evaluate_policy``. ``test_reference_matches_frozen_oracle`` pins it to ``oracle.py``.
# ---------------------------------------------------------------------------


def ref_return(regime: str, period: int) -> Fraction:
    quadratic = Fraction(-11, 1000) * period * period
    if regime == "SHORT":
        return Fraction(91, 100) + Fraction(3, 100) * period + quadratic
    return Fraction(31, 100) + Fraction(15, 100) * period + quadratic


def ref_value(period: int, belief: Fraction) -> Fraction:
    return belief * ref_return("SHORT", period) + (1 - belief) * ref_return("LONG", period)


def ref_optimal(belief: Fraction) -> int:
    best_value = None
    best_period = None
    for period in K_EVAL:  # ascending, so a tie keeps the smaller period
        value = ref_value(period, belief)
        if best_value is None or value > best_value:
            best_value, best_period = value, period
    return best_period


def ref_mass(p: Fraction, count: int) -> Fraction:
    weight = Fraction(comb(6, count))
    short = p**count * (1 - p) ** (6 - count)
    long = (1 - p) ** count * p ** (6 - count)
    return weight * (short + long) / 2


def ref_belief(link: str, p: Fraction, count: int) -> Fraction:
    if link == "SEVERED":
        return Fraction(1, 2)
    short = p**count * (1 - p) ** (6 - count)
    long = (1 - p) ** count * p ** (6 - count)
    return short / (short + long)


def ref_agreement(context, tail_row) -> Fraction:
    link, p, _cost = context
    total = Fraction(0)
    for count in range(7):
        belief = ref_belief(link, p, count)
        total += ref_mass(p, count) * int(int(tail_row[str(count)]) == ref_optimal(belief))
    return total


def ref_informed(context) -> Fraction:
    link, p, _cost = context
    total = Fraction(0)
    for count in range(7):
        belief = ref_belief(link, p, count)
        total += ref_mass(p, count) * ref_value(ref_optimal(belief), belief)
    return total


def ref_baseline() -> Fraction:
    return ref_value(ref_optimal(Fraction(1, 2)), Fraction(1, 2))


def ref_probe_value(context) -> Fraction:
    _link, _p, cost = context
    return ref_informed(context) + Fraction(1, 25) - cost


def ref_oracle_action(context) -> str:
    return "PROBE" if ref_probe_value(context) > ref_baseline() else "IMMEDIATE"


def ref_learned_value(context, root_label: str, tail_row) -> Fraction:
    link, p, cost = context
    if root_label == "PROBE":
        total = Fraction(0)
        for count in range(7):
            belief = ref_belief(link, p, count)
            total += ref_mass(p, count) * ref_value(int(tail_row[str(count)]), belief)
        return total + Fraction(1, 25) - cost
    return ref_value(int(root_label.split(":")[1]), Fraction(1, 2))


def ref_summary(root_labels, tail_periods) -> dict:
    regrets = []
    agreements = []
    actions = {}
    for context in CONTEXTS:
        cell = context_id(context)
        label = root_labels[cell]
        actions[cell] = "PROBE" if label == "PROBE" else "IMMEDIATE"
        optimum = max(ref_baseline(), ref_probe_value(context))
        regrets.append(optimum - ref_learned_value(context, label, tail_periods[cell]))
        agreements.append(ref_agreement(context, tail_periods[cell]))
    oracle_match = actions == {context_id(context): ref_oracle_action(context) for context in CONTEXTS}
    return {
        "root_actions": actions,
        "oracle_root_match": oracle_match,
        "max_regret": max(regrets),
        "minimum_tail_agreement": min(agreements),
        "per_context_agreement": {context_id(context): agreement for context, agreement in zip(CONTEXTS, agreements)},
    }


# ---------------------------------------------------------------------------
# Synthetic policies: exact coefficient vectors for the frozen bases.
# ---------------------------------------------------------------------------

TAIL_BETAS = {
    # value = k -> argmax at k = 8/9 (period 8)
    "always-8": (0.0, 0.0, 1.0, 0.0, 0.0),
    # value = -k -> argmax at k = 2/9 (period 2)
    "always-2": (0.0, 0.0, -1.0, 0.0, 0.0),
    # value = -(k - 4/9)^2 -> argmax at period 4
    "always-4": (-(4.0 / 9.0) ** 2, 0.0, 2.0 * 4.0 / 9.0, 0.0, -1.0),
    # value = -(k - 6/9)^2 -> argmax at period 6
    "always-6": (-(6.0 / 9.0) ** 2, 0.0, 2.0 * 6.0 / 9.0, 0.0, -1.0),
    # value = the exact expected tail return, in the frozen 5-term basis
    "exact-oracle": (0.31, 0.60, 1.35, -1.08, -0.891),
    # a belief threshold that keeps period 6 at low belief and period 4 everywhere above it:
    # correct on SEVERED and on counts 0-3, wrong on counts 4-6 of both LINKED reliabilities
    "threshold-4-high": (0.31, 0.60, 1.135, -0.435, -0.891),
}

# root basis: (1, (1-a)k, (1-a)k^2, a, a*cost, a*linked, a*linked*reliability)
# value = -(k - 4/9)^2 for IMMEDIATE, a large negative constant for PROBE
ROOT_BETA_ALWAYS_IMMEDIATE_4 = (0.0, 2.0 * 4.0 / 9.0, -1.0, -10.0, 0.0, 0.0, 0.0)


def exact_root_beta() -> tuple[float, ...]:
    """Coefficients that make every root score equal the exact oracle value."""
    b0 = Fraction(61, 100)
    b1 = Fraction(81, 100)
    b2 = Fraction(-891, 1000)
    b4 = Fraction(-1)
    severed = next(context for context in CONTEXTS if context[0] == "SEVERED")
    b3 = ref_probe_value(severed) + severed[2] - b0  # probe value at zero cost, minus the constant
    linked = [context for context in CONTEXTS if context[0] == "LINKED" and context[2] == Fraction(9, 100)]
    linked.sort(key=lambda context: context[1])
    (p_low, i_low), (p_high, i_high) = [
        (context[1], ref_probe_value(context) + context[2] - b0 - b3) for context in linked
    ]
    b6 = (i_high - i_low) / (p_high - p_low)
    b5 = i_low - b6 * p_low
    return tuple(float(value) for value in (b0, b1, b2, b3, b4, b5, b6))


def _torch():
    import torch

    return torch


def set_beta(model, values) -> None:
    torch = _torch()
    with torch.no_grad():
        model.beta.copy_(torch.tensor(tuple(float(value) for value in values), dtype=torch.float32))


def zero_residual(model) -> None:
    torch = _torch()
    if model.residual is None:
        return
    with torch.no_grad():
        for parameter in model.residual.parameters():
            parameter.zero_()


def constant_residual(model, value: float) -> None:
    """Make the residual an exact constant function of x (weights zero, one bias set)."""
    torch = _torch()
    zero_residual(model)
    with torch.no_grad():
        model.residual[4].bias.fill_(float(value))


def build_synthetic(arm_id: str, *, tail_name: str, root_beta, residual_constant: float | None = None):
    root, tail = build_arm(arm_id, ASSESS_SEEDS[0], 0)
    for model in (root, tail):
        zero_residual(model)
    set_beta(root, root_beta)
    set_beta(tail, TAIL_BETAS[tail_name])
    if residual_constant is not None:
        constant_residual(root, residual_constant)
        constant_residual(tail, residual_constant)
    return root, tail


def evaluate_synthetic(arm_id: str, *, tail_name: str, root_beta, residual_constant: float | None = None, sampled_episodes: int = 1):
    root, tail = build_synthetic(arm_id, tail_name=tail_name, root_beta=root_beta, residual_constant=residual_constant)
    return evaluate_policy(
        root, tail, arm_id=arm_id, seed_id=ASSESS_SEEDS[0], fold_id=0, root_update=8,
        sampled_episodes=sampled_episodes,
    )


# ---------------------------------------------------------------------------
# Reference pinning
# ---------------------------------------------------------------------------


def test_reference_matches_frozen_oracle():
    """The independent reference reproduces oracle.py exactly (Fraction arithmetic)."""
    for period in range(1, 10):
        for regime in ("SHORT", "LONG"):
            assert ref_return(regime, period) == tail_return(regime, period)
    for context in CONTEXTS:
        link, p, _cost = context
        for count in range(7):
            assert ref_mass(p, count) == joint_count_probability("SHORT", p, count) + joint_count_probability("LONG", p, count)
            belief = ref_belief(link, p, count)
            assert belief == posterior_short(link, p, count)
            assert ref_value(4, belief) == expected_tail(4, belief)
            assert ref_optimal(belief) == optimal_tail(K_EVAL, belief)[0]
    oracle = build_oracle()
    for context in CONTEXTS:
        cell = context_id(context)
        assert ref_oracle_action(context) == oracle[cell]["action"]
        assert ref_probe_value(context) == oracle[cell]["probe_value"]
        assert ref_baseline() == oracle[cell]["baseline"]


# ---------------------------------------------------------------------------
# M1 - tail agreement at known true values, both arms
# ---------------------------------------------------------------------------

EXPECTED_CONSTANT_PERIOD_AGREEMENT = {
    # per-context true agreement of a policy that always selects `period`
    period: {
        context_id(context): ref_agreement(context, {str(count): period for count in range(7)})
        for context in CONTEXTS
    }
    for period in K_EVAL
}


@pytest.mark.parametrize("arm_id", LADDER_ARMS)
@pytest.mark.parametrize("tail_name,period", [("always-2", 2), ("always-4", 4), ("always-6", 6), ("always-8", 8)])
def test_m1_constant_period_tail_agreement(arm_id, tail_name, period):
    """Known-truth levels 0, 0.041453, 0.235491, 0.382255, 0.479273 and 1 on both arms."""
    item = evaluate_synthetic(arm_id, tail_name=tail_name, root_beta=ROOT_BETA_ALWAYS_IMMEDIATE_4)
    for context in CONTEXTS:
        cell = context_id(context)
        assert set(item.tail_periods[cell].values()) == {period}, (arm_id, cell, item.tail_periods[cell])
    expected = min(EXPECTED_CONSTANT_PERIOD_AGREEMENT[period].values())
    assert abs(item.minimum_tail_agreement - float(expected)) <= 1e-12
    reference = ref_summary(item.root_selected_labels, item.tail_periods)
    assert abs(item.minimum_tail_agreement - float(reference["minimum_tail_agreement"])) <= 1e-12


@pytest.mark.parametrize("arm_id", LADDER_ARMS)
def test_m1_agreement_zero_is_a_true_zero(arm_id):
    """Period 8 is never oracle-optimal, so the always-8 policy has true agreement 0."""
    item = evaluate_synthetic(arm_id, tail_name="always-8", root_beta=ROOT_BETA_ALWAYS_IMMEDIATE_4)
    reference = ref_summary(item.root_selected_labels, item.tail_periods)
    assert all(value == 0 for value in reference["per_context_agreement"].values())
    assert item.minimum_tail_agreement == 0.0


@pytest.mark.parametrize("arm_id", LADDER_ARMS)
def test_m1_intermediate_recorded_minimum(arm_id):
    """The closest recorded minimum to 1/2 that the frozen mass law allows: 0.520727."""
    item = evaluate_synthetic(arm_id, tail_name="threshold-4-high", root_beta=ROOT_BETA_ALWAYS_IMMEDIATE_4)
    expected = Fraction(66653020, 128000000)
    reference = ref_summary(item.root_selected_labels, item.tail_periods)
    assert reference["minimum_tail_agreement"] == expected
    assert abs(item.minimum_tail_agreement - float(expected)) <= 1e-12
    severed = {
        cell: value for cell, value in reference["per_context_agreement"].items() if cell.startswith("SEVERED")
    }
    assert set(severed.values()) == {Fraction(1)}
    assert reference["per_context_agreement"]["LINKED-p13_20-c9_100"] == Fraction(79071420, 128000000)


@pytest.mark.parametrize("arm_id", LADDER_ARMS)
def test_m1_agreement_one_is_reachable(arm_id):
    """The exact-oracle coefficients exist in the frozen 5-term basis and record 1.0."""
    item = evaluate_synthetic(arm_id, tail_name="exact-oracle", root_beta=ROOT_BETA_ALWAYS_IMMEDIATE_4)
    reference = ref_summary(item.root_selected_labels, item.tail_periods)
    assert all(value == 1 for value in reference["per_context_agreement"].values())
    assert item.minimum_tail_agreement == 1.0


def test_m1_exact_oracle_basis_reproduces_the_tail_value():
    """The BC tail basis represents the true expected tail return exactly (fp32 error only)."""
    torch = _torch()
    beta = torch.tensor(TAIL_BETAS["exact-oracle"], dtype=torch.float32)
    worst = 0.0
    for context in CONTEXTS:
        link, p, _cost = context
        for count in range(7):
            belief = ref_belief(link, p, count)
            for period in K_EVAL:
                k = period / 9.0
                z = torch.tensor((1.0, float(belief), k, float(belief) * k, k * k), dtype=torch.float32)
                worst = max(worst, abs(float((z * beta).sum()) - float(ref_value(period, belief))))
    assert worst < 1e-6, worst


def test_m1_exact_half_agreement_is_unattainable():
    """No subset of the seven count masses sums to 1/2, so a true 1/2 cannot be constructed."""
    for context in CONTEXTS:
        link, p, _cost = context
        if link != "LINKED":
            continue
        masses = [ref_mass(p, count) for count in range(7)]
        sums = set()
        for size in range(8):
            for subset in combinations(masses, size):
                sums.add(sum(subset, Fraction(0)))
        assert Fraction(1, 2) not in sums


# ---------------------------------------------------------------------------
# M2 - competence predicate components
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("arm_id", LADDER_ARMS)
def test_m2_exactly_optimal_policy_is_reported_competent(arm_id):
    """Positive control: the predicate can and does fire, on both arms."""
    item = evaluate_synthetic(arm_id, tail_name="exact-oracle", root_beta=exact_root_beta())
    assert item.all_finite and item.all_unique
    assert item.oracle_root_match is True
    assert item.max_regret == 0.0
    assert item.minimum_tail_agreement == 1.0
    assert item.competence_pass is True
    oracle = build_oracle()
    assert item.root_actions == {cell: row["action"] for cell, row in oracle.items()}


@pytest.mark.parametrize("arm_id", LADDER_ARMS)
def test_m2_exact_root_scores_equal_the_oracle_values(arm_id):
    """The synthetic root reproduces the oracle's own numbers, so regret 0 is a true zero."""
    item = evaluate_synthetic(arm_id, tail_name="exact-oracle", root_beta=exact_root_beta())
    oracle = build_oracle()
    for context in CONTEXTS:
        cell = context_id(context)
        assert abs(item.root_scores[cell]["PROBE"] - float(oracle[cell]["probe_value"])) < 1e-6
        for period in K_EVAL:
            expected = float(ref_value(period, Fraction(1, 2)))
            assert abs(item.root_scores[cell][f"IMMEDIATE:{period}"] - expected) < 1e-6


@pytest.mark.parametrize("arm_id", LADDER_ARMS)
@pytest.mark.parametrize("tail_name", sorted(TAIL_BETAS))
@pytest.mark.parametrize("root_kind", ["exact", "always-immediate-4"])
def test_m2_all_reported_components_equal_the_reference(arm_id, tail_name, root_kind):
    """Regret, agreement, oracle root vector and the predicate, against the reference."""
    root_beta = exact_root_beta() if root_kind == "exact" else ROOT_BETA_ALWAYS_IMMEDIATE_4
    item = evaluate_synthetic(arm_id, tail_name=tail_name, root_beta=root_beta)
    reference = ref_summary(item.root_selected_labels, item.tail_periods)
    assert item.root_actions == reference["root_actions"]
    assert item.oracle_root_match == reference["oracle_root_match"]
    assert abs(item.max_regret - float(reference["max_regret"])) <= 1e-12
    assert abs(item.minimum_tail_agreement - float(reference["minimum_tail_agreement"])) <= 1e-12
    expected_competence = bool(
        item.all_finite
        and item.all_unique
        and reference["oracle_root_match"]
        and reference["max_regret"] <= Fraction(1, 50)
        and reference["minimum_tail_agreement"] >= Fraction(19, 20)
    )
    assert item.competence_pass is expected_competence


@pytest.mark.parametrize("arm_id", LADDER_ARMS)
def test_m2_root_vector_alone_can_refuse_competence(arm_id):
    """Component isolation: perfect tail, wrong root -> only oracle_root_match flips."""
    item = evaluate_synthetic(arm_id, tail_name="exact-oracle", root_beta=ROOT_BETA_ALWAYS_IMMEDIATE_4)
    assert item.minimum_tail_agreement == 1.0
    assert item.oracle_root_match is False
    assert item.competence_pass is False
    target = "LINKED-p17_20-c9_100"
    oracle = build_oracle()
    expected_regret = float(oracle[target]["probe_value"] - oracle[target]["baseline"])
    assert abs(item.max_regret - expected_regret) <= 1e-12


@pytest.mark.parametrize("arm_id", LADDER_ARMS)
@pytest.mark.parametrize("tail_name", sorted(TAIL_BETAS))
def test_m2_exact_and_float_predicates_agree(arm_id, tail_name):
    """evaluate_policy compares Fractions; validate_policy_evaluation compares floats."""
    config = ScoutConfig.assess()
    item = evaluate_synthetic(
        arm_id, tail_name=tail_name, root_beta=exact_root_beta(),
        sampled_episodes=config.sampled_evaluation_episodes,
    )
    if arm_id not in config.arms:
        pytest.skip("arm outside the ASSESS validator inventory")
    validated = validate_policy_evaluation(item, config=config, acquisition_eligible=False)
    assert validated.competence_pass == item.competence_pass


def test_m2_both_arms_agree_when_the_residual_is_zero():
    """Zeroing the FLEX residual makes the two arms the same function; both must agree."""
    for tail_name in sorted(TAIL_BETAS):
        rows = [
            evaluate_synthetic(arm, tail_name=tail_name, root_beta=exact_root_beta())
            for arm in LADDER_ARMS
        ]
        assert rows[0].tail_periods == rows[1].tail_periods
        assert rows[0].root_selected_labels == rows[1].root_selected_labels
        assert rows[0].minimum_tail_agreement == rows[1].minimum_tail_agreement
        assert rows[0].max_regret == rows[1].max_regret
        assert rows[0].competence_pass == rows[1].competence_pass


def test_m2_flex_residual_is_read_but_a_constant_cannot_change_a_choice():
    """The FLEX path really evaluates the residual; a constant shift leaves argmax fixed."""
    plain = evaluate_synthetic("FT-XF-FLEX", tail_name="exact-oracle", root_beta=exact_root_beta())
    shifted = evaluate_synthetic(
        "FT-XF-FLEX", tail_name="exact-oracle", root_beta=exact_root_beta(), residual_constant=0.25
    )
    cell = context_id(CONTEXTS[0])
    assert abs(shifted.root_scores[cell]["PROBE"] - plain.root_scores[cell]["PROBE"] - 0.25) < 1e-5
    assert abs(shifted.tail_scores[cell]["0"]["4"] - plain.tail_scores[cell]["0"]["4"] - 0.25) < 1e-5
    assert shifted.tail_periods == plain.tail_periods
    assert shifted.minimum_tail_agreement == plain.minimum_tail_agreement
    assert shifted.competence_pass == plain.competence_pass


# ---------------------------------------------------------------------------
# M3 - the per-coordinate Bellman displacement statistic
# ---------------------------------------------------------------------------


def _patched_exposure_line(monkeypatch, mutate):
    """Run the runner's own exposure_line over synthetic final checkpoints."""
    torch = _torch()
    ladder = _load_ladder()
    config = ScoutConfig.ladder_rung_1()

    def fake_load_checkpoint(path):
        parts = Path(path).parts
        return {"arm_id": parts[-4], "seed_id": parts[-3], "fold_id": int(parts[-2].split("-")[1])}

    def fake_restore_checkpoint(payload):
        root, tail = build_arm(payload["arm_id"], payload["seed_id"], payload["fold_id"])
        with torch.no_grad():
            mutate(payload["arm_id"], "root", root)
            mutate(payload["arm_id"], "tail", tail)
        return root, tail, None, None

    monkeypatch.setattr(ladder, "load_checkpoint", fake_load_checkpoint)
    monkeypatch.setattr(ladder, "restore_checkpoint", fake_restore_checkpoint)
    return ladder.exposure_line(config, Path("synthetic")), config


def test_m3_beta_only_displacement_matches_hand_computation(monkeypatch):
    step = 0.125

    def mutate(_arm_id, _stage, model):
        model.beta.add_(step)

    line, config = _patched_exposure_line(monkeypatch, mutate)
    assert len(line["rows"]) == len(config.arms) * len(config.seed_ids) * 2 * 2
    for row in line["rows"]:
        init_root, init_tail = build_arm(row["arm_id"], row["seed_id"], row["fold_id"])
        model = init_root if row["stage"] == "root" else init_tail
        state = model.state_dict()
        # the same FP32 addition the synthetic final checkpoint performed
        moved = ((state["beta"] + step) - state["beta"]).double()
        expected_displacement = float((moved**2).sum()) ** 0.5
        expected_scale = sum(float((tensor.double() ** 2).sum()) for tensor in state.values()) ** 0.5
        expected_beta_scale = float((state["beta"].double() ** 2).sum()) ** 0.5
        assert abs(row["parameter_displacement_l2"] - expected_displacement) < 1e-12
        assert abs(row["initialisation_scale_l2"] - expected_scale) < 1e-12
        assert abs(row["displacement_over_initialisation_scale"] - expected_displacement / expected_scale) < 1e-12
        assert abs(row["beta_displacement_l2"] - expected_displacement) < 1e-12
        assert abs(row["beta_initialisation_l2"] - expected_beta_scale) < 1e-12
        assert abs(row["beta_max_abs_coordinate_move"] - float(moved.abs().max())) < 1e-12
        assert abs(row["beta_max_abs_coordinate_move"] - step) < 1e-6
    assert line["learner_can_move_in_its_budget"] is True
    assert line["learning_rate"] == config.learning_rate


def test_m3_residual_is_inside_the_aggregate_and_outside_the_beta_line(monkeypatch):
    """FLEX: only the residual moves. beta statistics must be exactly zero."""
    step = 0.5

    def mutate(arm_id, _stage, model):
        if arm_id == "FT-XF-FLEX":
            model.residual[4].bias.add_(step)

    line, _config = _patched_exposure_line(monkeypatch, mutate)
    flex = [row for row in line["rows"] if row["arm_id"] == "FT-XF-FLEX"]
    bc = [row for row in line["rows"] if row["arm_id"] == "FT-XF-BC"]
    assert flex and bc
    for row in flex:
        assert abs(row["parameter_displacement_l2"] - step) < 1e-6
        assert row["beta_displacement_l2"] == 0.0
        assert row["beta_max_abs_coordinate_move"] == 0.0
    for row in bc:
        assert row["parameter_displacement_l2"] == 0.0
        assert row["beta_displacement_l2"] == 0.0
    assert line["learner_can_move_in_its_budget"] is False


def test_m3_initialisation_scale_is_arm_dependent():
    """The denominator differs by arm, so a single cross-arm minimum is not comparable."""
    scales = {}
    for arm in LADDER_ARMS:
        root, tail = build_arm(arm, B1_SEEDS[0], 0)
        for stage, model in (("root", root), ("tail", tail)):
            state = model.state_dict()
            scales[(arm, stage)] = (
                sum(float((tensor.double() ** 2).sum()) for tensor in state.values()) ** 0.5,
                sum(tensor.numel() for tensor in state.values()),
            )
    flex_tail, flex_count = scales[("FT-XF-FLEX", "tail")]
    bc_tail, bc_count = scales[("FT-XF-BC", "tail")]
    assert bc_count == 5 and flex_count == 4870
    assert flex_tail / bc_tail > 5.0
    assert abs(flex_tail - 9.102437056195274) < 1e-9
    assert abs(bc_tail - 1.5502197353913905) < 1e-9


@pytest.mark.parametrize("rung", sorted(RUNGS))
def test_m3_published_exposure_line_recomputes(rung):
    """(D) Recompute the published exposure line from the published checkpoints."""
    complete = RUNGS[rung]
    record = complete / "run-record.json"
    if not record.is_file():
        pytest.skip(f"{rung} run directory absent")
    from experiments.candidates.ucope.competence_first_scout_r01.checkpoint import load_checkpoint

    published = json.loads(record.read_text(encoding="utf-8"))["exposure_line"]
    config = ScoutConfig.ladder_rung_1() if rung == "rung-1" else ScoutConfig.ladder_rung_2()
    for row in published["rows"]:
        path = (
            complete / "checkpoints" / row["arm_id"] / row["seed_id"]
            / f"fold-{row['fold_id']}" / f"root-{config.root_updates:04d}.pt"
        )
        payload = load_checkpoint(path)
        final_state = payload[f"{row['stage']}_state"]
        init_root, init_tail = build_arm(row["arm_id"], row["seed_id"], row["fold_id"])
        init_state = (init_root if row["stage"] == "root" else init_tail).state_dict()
        # the FP32 difference is taken first, exactly as exposure_line does, then widened
        displacement = sum(
            float((((final_state[name] - tensor).double()) ** 2).sum()) for name, tensor in init_state.items()
        ) ** 0.5
        scale = sum(float((tensor.double() ** 2).sum()) for tensor in init_state.values()) ** 0.5
        beta_delta = (final_state["beta"] - init_state["beta"]).double()
        assert abs(row["parameter_displacement_l2"] - displacement) < 1e-12
        assert abs(row["initialisation_scale_l2"] - scale) < 1e-12
        assert abs(row["beta_displacement_l2"] - float((beta_delta**2).sum() ** 0.5)) < 1e-12
        assert abs(row["beta_max_abs_coordinate_move"] - float(beta_delta.abs().max())) < 1e-12


# ---------------------------------------------------------------------------
# M4 - the two anomalies
# ---------------------------------------------------------------------------


def test_m4a_period_eight_is_never_oracle_optimal():
    """Anomaly (a), part 1: every belief this host can present prefers 2, 4 or 6."""
    beliefs = {Fraction(1, 2)}
    for context in CONTEXTS:
        link, p, _cost = context
        for count in range(7):
            beliefs.add(ref_belief(link, p, count))
    assert all(ref_optimal(belief) != 8 for belief in beliefs)
    # and, exactly: value(6, b) - value(8, b) = 1/125 + 6b/25 > 0 on [0, 1]
    for numerator in range(0, 101):
        belief = Fraction(numerator, 100)
        assert ref_value(6, belief) > ref_value(8, belief)


def test_m4a_severed_agreement_is_all_or_nothing():
    """Anomaly (a), part 2: SEVERED belief is 1/2 for every count, so agreement is 0 or 1."""
    for context in CONTEXTS:
        link, p, _cost = context
        if link != "SEVERED":
            continue
        assert {ref_belief(link, p, count) for count in range(7)} == {Fraction(1, 2)}
        assert ref_optimal(Fraction(1, 2)) == 4
        for period in K_EVAL:
            agreement = ref_agreement(context, {str(count): period for count in range(7)})
            assert agreement == (1 if period == 4 else 0)


@pytest.mark.parametrize("rung", sorted(RUNGS))
def test_m4_published_rows_recompute_from_recorded_choices(rung):
    """(D) The published agreement/regret/oracle fields equal the independent reference."""
    complete = RUNGS[rung]
    result = complete / "result.json"
    if not result.is_file():
        pytest.skip(f"{rung} run directory absent")
    rows = json.loads(result.read_text(encoding="utf-8"))["internal_result"]["evaluations"]
    assert rows
    for row in rows:
        reference = ref_summary(row["root_selected_labels"], row["tail_periods"])
        assert abs(row["minimum_tail_agreement"] - float(reference["minimum_tail_agreement"])) <= 1e-12
        assert abs(row["max_regret"] - float(reference["max_regret"])) <= 1e-12
        assert row["oracle_root_match"] == reference["oracle_root_match"]
        assert row["root_actions"] == reference["root_actions"]


@pytest.mark.parametrize("rung", sorted(RUNGS))
def test_m4b_published_tail_choices_are_constant_across_checkpoints(rung):
    """(D) Anomaly (b): within one FT policy, every checkpoint carries the same tail."""
    complete = RUNGS[rung]
    result = complete / "result.json"
    if not result.is_file():
        pytest.skip(f"{rung} run directory absent")
    rows = json.loads(result.read_text(encoding="utf-8"))["internal_result"]["evaluations"]
    grouped = {}
    for row in rows:
        grouped.setdefault((row["arm_id"], row["seed_id"], row["fold_id"]), []).append(row)
    assert grouped
    for key, group in grouped.items():
        assert len({json.dumps(row["tail_periods"], sort_keys=True) for row in group}) == 1, key
        assert len({row["minimum_tail_agreement"] for row in group}) == 1, key
        assert len({json.dumps(row["tail_scores"], sort_keys=True) for row in group}) == 1, key


@pytest.mark.parametrize("rung", sorted(RUNGS))
def test_m4a_published_bc_never_selects_an_optimal_period(rung):
    """(D) The recorded zero is a property of the BC policies, not of the instrument."""
    complete = RUNGS[rung]
    result = complete / "result.json"
    if not result.is_file():
        pytest.skip(f"{rung} run directory absent")
    rows = [
        row
        for row in json.loads(result.read_text(encoding="utf-8"))["internal_result"]["evaluations"]
        if row["arm_id"] == "FT-XF-BC"
    ]
    assert rows
    selected = {period for row in rows for cell in row["tail_periods"].values() for period in cell.values()}
    assert selected == {2, 8}
    for row in rows:
        reference = ref_summary(row["root_selected_labels"], row["tail_periods"])
        severed = {
            cell: value for cell, value in reference["per_context_agreement"].items() if cell.startswith("SEVERED")
        }
        assert set(severed.values()) == {Fraction(0)}
        assert row["minimum_tail_agreement"] == 0.0


@pytest.mark.parametrize("rung", sorted(RUNGS))
def test_m4a_published_bc_scores_are_the_five_term_model_far_from_the_oracle(rung):
    """(D) Why only endpoints appear: the recorded BC tail model, recovered from its own scores.

    Three claims, all from the rows a validator already reads:
    1. the recorded tail scores are exactly the frozen 5-term Bellman model (fp32 residual),
       so the instrument recorded the model it claims to have recorded;
    2. the learned coefficients are far from the exact-oracle coefficients that the same
       basis can represent -- a learning outcome, not a representational limit; and
    3. the argmax implied by the recovered coefficients is exactly the recorded
       ``tail_periods``, and it never lands on period 4 or 6.
    """
    import numpy

    complete = RUNGS[rung]
    result = complete / "result.json"
    if not result.is_file():
        pytest.skip(f"{rung} run directory absent")
    rows = [
        row
        for row in json.loads(result.read_text(encoding="utf-8"))["internal_result"]["evaluations"]
        if row["arm_id"] == "FT-XF-BC"
    ]
    assert rows
    truth = numpy.array(TAIL_BETAS["exact-oracle"], dtype=float)
    for row in rows:
        design = []
        observed = []
        keys = []
        for context in CONTEXTS:
            link, p, _cost = context
            cell = context_id(context)
            for count in range(7):
                belief = float(ref_belief(link, p, count))
                for period in K_EVAL:
                    k = period / 9.0
                    design.append([1.0, belief, k, belief * k, k * k])
                    observed.append(row["tail_scores"][cell][str(count)][str(period)])
                    keys.append((cell, count, period))
        design = numpy.array(design, dtype=float)
        observed = numpy.array(observed, dtype=float)
        beta, _residual, _rank, _sv = numpy.linalg.lstsq(design, observed, rcond=None)
        assert float(numpy.abs(design @ beta - observed).max()) < 1e-6
        assert float(numpy.abs(beta - truth).max()) > 0.5
        predicted = design @ beta
        for index in range(0, len(keys), len(K_EVAL)):
            block = predicted[index:index + len(K_EVAL)]
            best = int(K_EVAL[int(numpy.argmax(block))])
            cell, count, _period = keys[index]
            assert row["tail_periods"][cell][str(count)] == best
            assert best in (2, 8)


def test_m4b_frozen_tail_clock_is_structural(tmp_path):
    """Anomaly (b) at unit scale: FT checkpoints share one tail model; MT's do not."""
    from experiments.candidates.ucope.competence_first_scout_r01.host import generate_population
    from experiments.candidates.ucope.competence_first_scout_r01.training import train_policy

    config = ScoutConfig.assess()
    seed = ASSESS_SEEDS[0]
    binding = RunBinding.assess("0" * 64)
    population = generate_population(config, seed)
    observed = {}
    for arm_id in ("FT-XF-BC", "FT-XF-FLEX", "MT-XF-FLEX"):
        run = train_policy(
            config,
            population,
            arm_id=arm_id,
            seed_id=seed,
            fold_id=0,
            run_binding=binding,
            checkpoint_root=tmp_path / arm_id,
        )
        payloads = [
            json.dumps({name: tensor.tolist() for name, tensor in _load_state(path).items()}, sort_keys=True)
            for path in run.checkpoint_paths
        ]
        assert len(payloads) == len(config.evaluation_root_updates)
        observed[arm_id] = (len(set(payloads)), tuple(item.minimum_tail_agreement for item in run.evaluations))
    assert observed["FT-XF-BC"][0] == 1
    assert observed["FT-XF-FLEX"][0] == 1
    assert observed["MT-XF-FLEX"][0] > 1
    assert len(set(observed["FT-XF-BC"][1])) == 1
    assert len(set(observed["FT-XF-FLEX"][1])) == 1


def _load_state(path):
    from experiments.candidates.ucope.competence_first_scout_r01.checkpoint import load_checkpoint

    return load_checkpoint(path)["tail_state"]

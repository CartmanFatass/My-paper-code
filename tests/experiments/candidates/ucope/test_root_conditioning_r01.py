"""Tests for the ``UCOPE-B-EXPLORE-ROOT-CONDITIONING-R01`` runner.

They pin the object to its card: the fixed tail and its gating reproduction check, the single
shared root problem behind all three arms, the amended branch statistic ``C_root`` against the
frozen ``C_even``, the machine-generated per-context breakdown against
``evaluation.evaluate_policy``, and the amended reading rule in its stated order.
"""

from __future__ import annotations

from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

numpy = pytest.importorskip("numpy")
torch = pytest.importorskip("torch")

from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    B1_SEEDS,
    CONTEXTS,
)
from experiments.candidates.ucope.competence_first_scout_r01.evaluation import (  # noqa: E402
    evaluate_policy,
)


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = _load("ucope_root_conditioning_r01", "run_ucope_root_conditioning_r01.py")
CR = RUNNER.CR
SELECTION = CR._n_selection()

SMALL_EPISODES = 320
SMALL_TAIL_UPDATES = 4
SMALL_ROOT_UPDATES = 8


@pytest.fixture(scope="module")
def small_columns():
    ordered, _labels = CR.canonical_order(
        SELECTION.generate_columns(B1_SEEDS[0], SMALL_EPISODES))
    return ordered


# --------------------------------------------------------------------------- frozen constants


def test_the_object_inherits_the_competence_objects_frozen_constants():
    assert RUNNER.OBJECT_ID == "UCOPE-B-EXPLORE-ROOT-CONDITIONING-R01"
    assert RUNNER.EVIDENCE_CLASS == "B/EXPLORE"
    assert RUNNER.TAIL_ROWS_PER_POLICY == CR.TAIL_ROWS_PER_POLICY == 81_920
    assert RUNNER.EPISODES_PER_CONTEXT == 40_960
    assert (RUNNER.TAIL_UPDATES, RUNNER.ROOT_UPDATES) == (1_600, 3_200)
    assert RUNNER.LEARNING_RATE == 3e-3
    assert RUNNER.ARM_ID == "FT-XF-BC"
    assert (RUNNER.EPS_L, RUNNER.MAJORITY) == (0.10, 4)
    assert RUNNER.TAIL_REPRODUCTION_TOLERANCE == 1e-6
    assert (RUNNER.REGRET_GATE, RUNNER.AGREEMENT_GATE) == (Fraction(1, 50), Fraction(19, 20))
    assert RUNNER.TARGET_CONTEXT_ID == "LINKED-p17_20-c9_100"
    assert (RUNNER.RAW_ROOT, RUNNER.WHITENED_ROOT, RUNNER.EXACT_ROOT) == (
        "RAW-ROOT-10X", "WHITENED-ROOT-10X", "EXACT-ROOT-SOLVE")


def test_every_shared_path_comes_from_the_competence_runner():
    assert RUNNER.COMPETENCE_RUNNER.name == "run_ucope_competence_whitened_r01.py"
    for name in ("canonical_order", "stage_designs", "whitening", "exact_solve",
                 "root_targets_fp32", "root_targets_fp64", "train_stage", "_raw_modules",
                 "admit_memory", "source_status_record", "gradient_infinity_norm"):
        assert hasattr(CR, name), name


# --------------------------------------------------------------------------- the fixed tail


def test_the_tail_reproduction_reference_is_read_from_the_competence_run(tmp_path):
    payload = {
        "object_id": "UCOPE-B-EXPLORE-COMPETENCE-WHITENED-R01",
        "policies": [{"seed_id": "s", "fold_id": 0,
                      "arms": {"WHITENED-10X": {"beta_tail": [1.0, 2.0, 3.0, 4.0, 5.0]}}}],
    }
    path = tmp_path / "run-record.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert RUNNER.recorded_tail_vectors(path) == {("s", 0): [1.0, 2.0, 3.0, 4.0, 5.0]}


def test_a_missing_or_wrong_reference_refuses_the_launch(tmp_path):
    with pytest.raises(RUNNER.LaunchRefusal, match="reference missing"):
        RUNNER.recorded_tail_vectors(tmp_path / "absent.json")
    other = tmp_path / "other.json"
    other.write_text(json.dumps({"object_id": "SOMETHING-ELSE", "policies": []}), encoding="utf-8")
    with pytest.raises(RUNNER.LaunchRefusal, match="not the competence run record"):
        RUNNER.recorded_tail_vectors(other)


def test_the_whitened_tail_is_deterministic_and_recovers_to_raw_coordinates(small_columns,
                                                                            monkeypatch):
    monkeypatch.setattr(RUNNER, "TAIL_UPDATES", SMALL_TAIL_UPDATES)
    blocks = CR.stage_designs(small_columns, 0)
    white = CR.whitening(blocks["tail"]["design64"], stage="tail")
    first, initial = RUNNER.train_whitened_tail(
        seed_id=B1_SEEDS[0], fold_id=0, blocks=blocks, tail_white=white,
        activity=CR._fresh_activity())
    second, initial_again = RUNNER.train_whitened_tail(
        seed_id=B1_SEEDS[0], fold_id=0, blocks=blocks, tail_white=white,
        activity=CR._fresh_activity())
    assert first == second
    assert initial == initial_again
    assert len(first) == 5
    # A zero-update run must recover exactly the frozen raw initialisation.
    monkeypatch.setattr(RUNNER, "TAIL_UPDATES", 0)
    untrained, _initial = RUNNER.train_whitened_tail(
        seed_id=B1_SEEDS[0], fold_id=0, blocks=blocks, tail_white=white,
        activity=CR._fresh_activity())
    assert untrained == pytest.approx(initial, abs=1e-5)


# --------------------------------------------------------------------------- one root problem


def test_all_three_arms_solve_the_same_root_problem(small_columns, monkeypatch):
    monkeypatch.setattr(RUNNER, "TAIL_UPDATES", SMALL_TAIL_UPDATES)
    monkeypatch.setattr(RUNNER, "ROOT_UPDATES", SMALL_ROOT_UPDATES)
    blocks = CR.stage_designs(small_columns, 0)
    tail_white = CR.whitening(blocks["tail"]["design64"], stage="tail")
    root_white = CR.whitening(blocks["root"]["design64"], stage="root")
    beta_tail, _initial = RUNNER.train_whitened_tail(
        seed_id=B1_SEEDS[0], fold_id=0, blocks=blocks, tail_white=tail_white,
        activity=CR._fresh_activity())
    targets = CR.root_targets_fp32(blocks["root"], beta_tail)

    raw, raw_init = RUNNER.train_root(
        seed_id=B1_SEEDS[0], fold_id=0, blocks=blocks, targets=targets, whitened=False,
        root_white=root_white, activity=CR._fresh_activity())
    whitened, whitened_init = RUNNER.train_root(
        seed_id=B1_SEEDS[0], fold_id=0, blocks=blocks, targets=targets, whitened=True,
        root_white=root_white, activity=CR._fresh_activity())
    # Same problem, same initialisation, different coordinate system only.
    assert raw_init == whitened_init
    assert len(raw) == len(whitened) == 7
    assert raw != whitened

    # The ceiling on those same targets is the exact solve, and it is a stationary point.
    beta_star = CR.exact_solve(blocks["root"]["design64"], targets)
    assert CR.gradient_infinity_norm(blocks["root"]["design64"], targets, beta_star) < 1e-9


def test_the_root_gram_is_the_same_matrix_for_both_folds(small_columns):
    first = CR.whitening(CR.stage_designs(small_columns, 0)["root"]["design64"], stage="root")
    second = CR.whitening(CR.stage_designs(small_columns, 1)["root"]["design64"], stage="root")
    assert first["gram_condition_number"] == pytest.approx(
        second["gram_condition_number"], rel=1e-9)
    assert first["cholesky_reconstruction_max_abs"] <= CR.CHOLESKY_TOLERANCE
    assert first["gram_smallest_eigenvalue"] > CR.MINIMUM_GRAM_EIGENVALUE


# --------------------------------------------------------------------------- predicates


def _evaluation(**overrides):
    base = dict(all_finite=True, all_unique=True, oracle_root_match=True,
                max_regret=0.0, minimum_tail_agreement=1.0)
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.parametrize(
    "overrides,summary_ok,expected",
    [
        ({}, True, True),
        ({"all_finite": False}, True, False),
        ({"all_unique": False}, True, False),
        ({"oracle_root_match": False}, True, False),
        ({}, False, False),
        # The agreement gate is NOT part of C_root: a policy failing it still passes.
        ({"minimum_tail_agreement": 0.520727}, True, True),
    ],
)
def test_c_root_is_c_even_without_the_tail_only_agreement_gate(overrides, summary_ok, expected):
    assert RUNNER.c_root_pass(
        _evaluation(**overrides), {"max_regret_within_gate": summary_ok}) is expected


def test_the_per_context_breakdown_reproduces_the_frozen_evaluation(small_columns, monkeypatch):
    monkeypatch.setattr(RUNNER, "TAIL_UPDATES", SMALL_TAIL_UPDATES)
    monkeypatch.setattr(RUNNER, "ROOT_UPDATES", SMALL_ROOT_UPDATES)
    blocks = CR.stage_designs(small_columns, 0)
    tail_white = CR.whitening(blocks["tail"]["design64"], stage="tail")
    root_white = CR.whitening(blocks["root"]["design64"], stage="root")
    beta_tail, _init = RUNNER.train_whitened_tail(
        seed_id=B1_SEEDS[0], fold_id=0, blocks=blocks, tail_white=tail_white,
        activity=CR._fresh_activity())
    targets = CR.root_targets_fp32(blocks["root"], beta_tail)
    beta_root, _root_init = RUNNER.train_root(
        seed_id=B1_SEEDS[0], fold_id=0, blocks=blocks, targets=targets, whitened=True,
        root_white=root_white, activity=CR._fresh_activity())

    root_model, tail_model = CR._raw_modules(B1_SEEDS[0], 0, beta_root, beta_tail)
    rows, summary = RUNNER.per_context_breakdown(root_model, tail_model)
    item = evaluate_policy(root_model, tail_model, arm_id=RUNNER.ARM_ID, seed_id=B1_SEEDS[0],
                           fold_id=0, root_update=SMALL_ROOT_UPDATES, sampled_episodes=1)

    assert set(rows) == set(item.root_actions)
    assert len(rows) == len(CONTEXTS) == 8
    assert {cell: row["root_action"] for cell, row in rows.items()} == item.root_actions
    assert summary["max_regret"] == pytest.approx(item.max_regret, abs=1e-12)
    assert summary["min_tail_agreement"] == pytest.approx(item.minimum_tail_agreement, abs=1e-12)
    assert sum(row["is_target_context"] for row in rows.values()) == 1
    assert rows[RUNNER.TARGET_CONTEXT_ID]["is_target_context"] is True
    assert summary["max_regret_context"] in rows
    assert summary["min_tail_agreement_context"] in rows


# --------------------------------------------------------------------------- the amended rule


def _policies(whitened, raw, exact):
    return [
        {"arms": {
            RUNNER.WHITENED_ROOT: {"c_root_pass": w, "competence": {"competence_pass": False}},
            RUNNER.RAW_ROOT: {"c_root_pass": r, "competence": {"competence_pass": False}},
            RUNNER.EXACT_ROOT: {"c_root_pass": e, "competence": {"competence_pass": False}},
        }}
        for w, r, e in zip(whitened, raw, exact)
    ]


def test_rule_r_a_when_the_whitened_root_satisfies_c_root_in_all_six():
    reading = RUNNER.apply_reading_rule(_policies([True] * 6, [False] * 6, [False] * 6))
    assert reading["branch"] == "R'-A"
    assert reading["numbers"]["branch_statistic"] == "C_root"
    assert reading["numbers"]["whitened_root_competent"] == 6


def test_rule_r_b_needs_a_majority_and_a_clean_ceiling():
    reading = RUNNER.apply_reading_rule(
        _policies([True] * 4 + [False] * 2, [False] * 6, [True] * 6))
    assert reading["branch"] == "R'-B"
    assert reading["numbers"]["whitened_root_competent"] == 4


def test_rule_r_c_when_the_ceiling_is_clean_and_the_root_learner_is_not():
    reading = RUNNER.apply_reading_rule(
        _policies([True] * 3 + [False] * 3, [True] * 6, [True] * 6))
    assert reading["branch"] == "R'-C"


def test_rule_r_d_when_the_ceiling_itself_falls_short():
    reading = RUNNER.apply_reading_rule(
        _policies([True] * 5 + [False], [False] * 6, [True] * 5 + [False]))
    assert reading["branch"] == "R'-D"
    reading = RUNNER.apply_reading_rule(_policies([True] * 6, [False] * 6, [False] * 6))
    assert reading["branch"] == "R'-A", "R'-A precedes the ceiling test, by the stated order"


def test_the_branch_order_is_the_amended_order():
    source = (PROJECT_ROOT / "scripts/run_ucope_root_conditioning_r01.py").read_text(
        encoding="utf-8")
    positions = [source.index(f'"branch": "{name}"')
                 for name in ("R'-A", "R'-B", "R'-C", "R'-D", "R'-E")]
    assert positions == sorted(positions)


def test_the_rule_also_carries_the_full_c_even_flags():
    reading = RUNNER.apply_reading_rule(_policies([True] * 6, [False] * 6, [True] * 6))
    assert reading["numbers"]["c_even_whitened_root_flags"] == [False] * 6
    assert set(reading["numbers"]) >= {
        "c_even_whitened_root_flags", "c_even_raw_root_flags", "c_even_exact_root_flags"}


# --------------------------------------------------------------------------- end to end


def _miniature_reference(path: Path) -> Path:
    """Build a tail reference at the miniature scale, the way the real reference was built."""
    policies = []
    for seed in B1_SEEDS:
        ordered, _labels = CR.canonical_order(SELECTION.generate_columns(seed, SMALL_EPISODES))
        for fold in (0, 1):
            blocks = CR.stage_designs(ordered, fold)
            white = CR.whitening(blocks["tail"]["design64"], stage="tail")
            beta_tail, _init = RUNNER.train_whitened_tail(
                seed_id=seed, fold_id=fold, blocks=blocks, tail_white=white,
                activity=CR._fresh_activity())
            policies.append({"seed_id": seed, "fold_id": fold,
                             "arms": {"WHITENED-10X": {"beta_tail": beta_tail}}})
    path.write_text(json.dumps({
        "object_id": "UCOPE-B-EXPLORE-COMPETENCE-WHITENED-R01", "policies": policies,
    }), encoding="utf-8")
    return path


def test_a_miniature_run_produces_a_complete_record(tmp_path, monkeypatch):
    monkeypatch.setattr(RUNNER, "TAIL_UPDATES", SMALL_TAIL_UPDATES)
    monkeypatch.setattr(RUNNER, "ROOT_UPDATES", SMALL_ROOT_UPDATES)
    # torch.set_num_interop_threads cannot be called after parallel work has begun in a shared
    # process; the topology knob is recorded-not-gating, so it is neutralised for the test only.
    monkeypatch.setattr(CR, "_configure_topology", lambda cap: None)
    reference = _miniature_reference(tmp_path / "reference.json")

    path = RUNNER.run_object(tmp_path / "mini", thread_cap=2,
                             episodes_per_context=SMALL_EPISODES,
                             competence_record=reference)
    record = json.loads(Path(path).read_text(encoding="utf-8"))

    assert record["complete"] is True
    assert record["object_id"] == "UCOPE-B-EXPLORE-ROOT-CONDITIONING-R01"
    assert record["branch_statistic"] == "C_root"
    assert len(record["policies"]) == 6
    assert record["counts"]["environment_episodes"] == 3 * SMALL_EPISODES * len(CONTEXTS)
    assert record["counts"]["tail_rows"] == 6 * 2 * SMALL_EPISODES
    assert record["counts"]["root_rows"] == 6 * 4 * SMALL_EPISODES
    assert record["counts"]["tail_optimizer_updates"] == 6 * SMALL_TAIL_UPDATES
    assert record["counts"]["root_optimizer_updates"] == 6 * 2 * SMALL_ROOT_UPDATES
    assert record["counts"]["exact_solves"] == 6 * 3
    assert record["counts"]["nonfinite_events"] == 0
    assert record["reading_rule"]["branch"] in {"R'-A", "R'-B", "R'-C", "R'-D", "R'-E"}
    assert record["admission"]["passed"] is True

    for policy in record["policies"]:
        assert set(policy["arms"]) == {"RAW-ROOT-10X", "WHITENED-ROOT-10X", "EXACT-ROOT-SOLVE"}
        assert policy["fixed_tail"]["reproduction_pass"] is True
        assert policy["fixed_tail"]["reproduction_max_abs_difference"] <= 1e-6
        assert policy["arms"]["EXACT-ROOT-SOLVE"]["d_learned_root"] == 0.0
        assert policy["d_objective_root"] >= 0.0
        for arm in policy["arms"].values():
            assert set(arm["per_context"]) == set(policy["arms"]["RAW-ROOT-10X"]["per_context"])
            assert len(arm["per_context"]) == 8
            assert isinstance(arm["c_root_pass"], bool)
            assert set(arm["competence"]) >= {
                "all_finite", "all_unique", "oracle_root_match", "max_regret",
                "minimum_tail_agreement", "competence_pass"}
        # The tail is shared, so the tail-only agreement is identical across the three arms.
        agreements = {arm["competence"]["minimum_tail_agreement"]
                      for arm in policy["arms"].values()}
        assert len(agreements) == 1

    exposure = record["exposure_line"]
    assert {row["arm"] for row in exposure["rows"]} == {"RAW-ROOT-10X", "WHITENED-ROOT-10X"}
    assert len(exposure["rows"]) == 12
    assert exposure["learner_can_move_in_its_budget"] is True
    assert exposure["raw_per_coordinate_ceiling"] == pytest.approx(
        SMALL_ROOT_UPDATES * RUNNER.LEARNING_RATE)


def test_a_perturbed_tail_reference_quarantines_the_run(tmp_path, monkeypatch):
    monkeypatch.setattr(RUNNER, "TAIL_UPDATES", SMALL_TAIL_UPDATES)
    monkeypatch.setattr(RUNNER, "ROOT_UPDATES", SMALL_ROOT_UPDATES)
    monkeypatch.setattr(CR, "_configure_topology", lambda cap: None)
    reference = _miniature_reference(tmp_path / "reference.json")
    payload = json.loads(reference.read_text(encoding="utf-8"))
    payload["policies"][0]["arms"]["WHITENED-10X"]["beta_tail"][0] += 1e-3
    reference.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RUNNER.LaunchRefusal, match="tail-reproduction integrity item failed"):
        RUNNER.run_object(tmp_path / "mini2", thread_cap=2,
                          episodes_per_context=SMALL_EPISODES, competence_record=reference)
    quarantines = list((tmp_path / "mini2").glob("quarantine-*/failure.json"))
    assert len(quarantines) == 1
    failure = json.loads(quarantines[0].read_text(encoding="utf-8"))
    assert failure["quarantined"] is True
    assert failure["quarantine_rule"] == "MARL_EMPIRICAL_EVIDENCE_SPEC.md#6.2"


def test_the_output_root_is_create_once(tmp_path):
    (tmp_path / "taken").mkdir()
    with pytest.raises(RUNNER.LaunchRefusal, match="create-once"):
        RUNNER.run_object(tmp_path / "taken")

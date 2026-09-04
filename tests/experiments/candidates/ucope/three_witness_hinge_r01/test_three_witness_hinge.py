"""Focused semantics, reading-rule and toy smoke tests for the three-witness object."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

numpy = pytest.importorskip("numpy")
torch = pytest.importorskip("torch")

from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    B1_SEEDS,
    CONTEXTS,
    K_EVAL,
    K_TRAIN,
)
from experiments.candidates.ucope.three_witness_hinge_r01 import experiment as EXP  # noqa: E402


def test_project_cost_is_the_frozen_per_arm_law():
    result = EXP.project_cost()
    assert result["projected_arm_seconds"] == pytest.approx(185.481)
    assert result["machine_time_cap_seconds_per_arm"] == 600.0
    assert result["within_cap"] is True
    doubled = EXP.project_cost(environment_episodes=2 * 983_040)
    assert doubled["projected_arm_seconds"] == pytest.approx(2 * 185.481)


def test_project_cost_cli_emits_json_without_running_a_learner():
    completed = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts/run_ucope_three_witness_hinge_r01.py"),
         "project-cost"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True)
    assert json.loads(completed.stdout)["projected_arm_seconds"] == pytest.approx(185.481)


def test_signed_hinges_use_only_the_three_odd_support_witnesses(monkeypatch):
    seen = []
    original = EXP.tail_basis

    def spy(*, belief, period):
        seen.append(int(period))
        return original(belief=belief, period=period)

    monkeypatch.setattr(EXP, "tail_basis", spy)
    beliefs = numpy.linspace(0.0, 1.0, 11)
    signed = EXP.signed_witness_designs(beliefs)
    assert set(signed) == set(EXP.WITNESS_PAIRS)
    assert set(seen) == {1, 3, 5, 7, 9}
    assert set(seen) <= set(K_TRAIN)
    assert not set(seen) & set(K_EVAL)
    star = numpy.asarray(EXP.BETA_STAR)
    for rows in signed.values():
        assert numpy.all(rows @ star > 0.0)


def test_the_first_two_oracle_signs_really_reverse_with_belief():
    beliefs = numpy.linspace(0.0, 1.0, 101)
    star = numpy.asarray(EXP.BETA_STAR)
    for pair in ((1, 5), (3, 7)):
        raw = numpy.stack([
            numpy.asarray(EXP.tail_basis(belief=float(b), period=pair[0]))
            - numpy.asarray(EXP.tail_basis(belief=float(b), period=pair[1]))
            for b in beliefs])
        signs = numpy.sign(raw @ star)
        assert set(signs) == {-1.0, 1.0}


def test_comparator_is_exactly_three_times_one_witness_hinge():
    beta = torch.tensor(EXP.BETA_STAR, dtype=torch.float32)
    designs = {(5, 9): torch.zeros((7, 5), dtype=torch.float32)}
    one = EXP._hinge_loss(beta, designs, (((5, 9), 1.0),))
    comparator = EXP._hinge_loss(beta, designs, EXP.ARMS["DOSE-MATCHED-SINGLE"])
    assert float(comparator) == pytest.approx(3.0 * float(one))


def test_evaluation_gaps_cover_every_context_count_and_held_out_pair():
    rows = EXP.evaluation_gap_record(EXP.BETA_STAR)
    assert len(rows) == len(CONTEXTS) * 7 * 3
    assert {tuple(row["pair"]) for row in rows} == set(EXP.HELD_OUT_PAIRS)
    assert all(row["oracle_signed_gap"] > 0.0 for row in rows)
    assert all(row["learned_signed_gap"] == pytest.approx(row["oracle_signed_gap"])
               for row in rows)


def _policies(treatment, comparator, treatment_c_even=()):
    rows = []
    for index in range(6):
        rows.append({
            "seed_id": f"s{index // 2}", "fold_id": index % 2,
            "arms": {
                "THREE-WITNESS": {
                    "agreement_within_gate": index in treatment,
                    "competence": {"competence_pass": index in treatment_c_even},
                },
                "DOSE-MATCHED-SINGLE": {
                    "agreement_within_gate": index in comparator,
                    "competence": {"competence_pass": False},
                },
            },
        })
    return rows


@pytest.mark.parametrize(("rows", "branch"), [
    (_policies(range(6), range(5), range(6)), "TW-A"),
    (_policies(range(6), range(5), range(5)), "TW-B"),
    (_policies(range(6), range(6), range(6)), "TW-C"),
    (_policies(range(4), range(3), range(4)), "TW-D"),
    (_policies(range(3), range(3), range(3)), "TW-E"),
    (_policies((0, 1, 2), (1, 2, 3), (0, 1, 2)), "TW-F"),
])
def test_frozen_reading_rule(rows, branch):
    result = EXP.apply_reading_rule(rows)
    assert result["branch"] == branch
    assert result["numbers"]["N_T_minus_N_C"] == (
        result["numbers"]["N_T"] - result["numbers"]["N_C"])


def test_toy_run_is_paired_complete_and_under_sixty_seconds(tmp_path, monkeypatch):
    receipt = tmp_path / "admission.json"
    receipt.write_text(json.dumps({
        "passed": True, "physical_floor_pass": True, "effective_floor_pass": True,
        "available_physical_bytes": 8 << 30, "effective_available_bytes": 8 << 30,
    }), encoding="utf-8")
    monkeypatch.setattr(EXP.CR, "_configure_topology", lambda _threads: None)
    started = time.perf_counter()
    path = EXP.run_object(
        tmp_path / "run", admission_receipt=receipt, seeds=(B1_SEEDS[0],), folds=(0,),
        episodes_per_context=320, tail_updates=3, root_updates=3, sampled_episodes=4,
        require_full_seeds=False, argv=("toy-smoke",))
    elapsed = time.perf_counter() - started
    record = json.loads(path.read_text(encoding="utf-8"))

    assert elapsed < 60.0
    assert path.name == "summary.json"
    assert record["complete"] is True
    assert record["object_id"] == EXP.OBJECT_ID
    assert record["arm_order"] == ["DOSE-MATCHED-SINGLE", "THREE-WITNESS"]
    assert record["admission"]["passed"] is True
    assert record["counts"]["environment_transitions"] == 5 * record["counts"]["environment_episodes"]
    assert record["counts"]["tail_optimizer_updates"] == 6
    assert record["counts"]["root_optimizer_updates"] == 6
    assert record["counts"]["exact_policy_evaluations"] > 0
    assert record["resources"]["wall_seconds"] > 0.0
    assert record["reading_rule"]["branch"] in {"TW-A", "TW-B", "TW-C", "TW-D", "TW-E", "TW-F"}
    assert len(record["policies"]) == 1
    policy = record["policies"][0]
    assert set(policy["arms"]) == set(EXP.ARMS)
    assert policy["arms"]["DOSE-MATCHED-SINGLE"]["initial_beta_tail"] == (
        policy["arms"]["THREE-WITNESS"]["initial_beta_tail"])
    assert set(policy["arms"]["DOSE-MATCHED-SINGLE"]["witnesses"]) == {"5_9"}
    assert set(policy["arms"]["THREE-WITNESS"]["witnesses"]) == {"1_5", "3_7", "5_9"}
    for arm in policy["arms"].values():
        assert len(arm["evaluation_gaps"]) == len(CONTEXTS) * 7 * 3
        assert arm["training_mse"]["tail_train_mse"] >= 0.0
        assert set(arm["competence"]) >= {
            "all_finite", "all_unique", "oracle_root_match", "max_regret",
            "minimum_tail_agreement", "competence_pass", "root_actions"}
    exact = policy["exact_reference"]
    assert exact["competence"]["minimum_tail_agreement"] >= 0.0
    assert len(exact["evaluation_gaps"]) == len(CONTEXTS) * 7 * 3
    assert len(record["exposure_line"]["rows"]) == 4
    assert all(row["displacement_to_initialisation_scale"] > 0.0
               for row in record["exposure_line"]["rows"])

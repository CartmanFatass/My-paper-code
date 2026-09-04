"""Cost, rule, reconstruction, and toy smoke tests for the retained-root audit."""

from __future__ import annotations

import hashlib
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
pytest.importorskip("torch")

from experiments.candidates.ucope.root_target_vs_root_fit_audit_r01 import audit as AUD  # noqa: E402


def test_project_cost_is_frozen_and_cli_is_outcome_free():
    result = AUD.project_cost()
    assert result["projected_total_seconds"] == pytest.approx(185.481)
    assert result["total_machine_time_cap_seconds"] == pytest.approx(185.481)
    assert result["within_cap"] is True
    assert AUD.project_cost(replay_episodes=2 * 983_040)["projected_total_seconds"] == pytest.approx(
        2 * 185.481)
    completed = subprocess.run(
        [sys.executable,
         str(PROJECT_ROOT / "scripts/run_ucope_root_target_vs_root_fit_audit_r01.py"),
         "project-cost"],
        cwd=PROJECT_ROOT, check=True, capture_output=True, text=True)
    assert json.loads(completed.stdout) == result


def _rule_policy(seed_id, fold_id, treatment_exact, comparator_exact,
                 treatment_finite="PROBE", treatment_margin=1.0, comparator_margin=-1.0):
    def arm(exact, finite, margin):
        return {
            "exact_policy": {"root_actions": {AUD.FALSE_POSITIVE_CONTEXT: exact}},
            "retained_finite_root": {
                "root_actions": {AUD.FALSE_POSITIVE_CONTEXT: finite}},
            "target_margins": {
                AUD.FALSE_POSITIVE_CONTEXT: {"probe_minus_best_immediate": margin}},
        }

    return {
        "seed_id": seed_id, "fold_id": fold_id,
        "arms": {
            "THREE-WITNESS": arm(treatment_exact, treatment_finite, treatment_margin),
            "DOSE-MATCHED-SINGLE": arm(
                comparator_exact, "IMMEDIATE", comparator_margin),
        },
    }


@pytest.mark.parametrize(("treatment", "comparator", "finite", "branch"), [
    ("PROBE", "IMMEDIATE", "PROBE", "ROOT_TARGET_PIPELINE_SHIFT_SUPPORTED"),
    ("IMMEDIATE", "IMMEDIATE", "PROBE", "FINITE_ROOT_FIT_RESIDUAL_SUPPORTED"),
    ("PROBE", "PROBE", "PROBE", "MIXED_ROOT_CAUSE"),
])
def test_frozen_first_match_rule(treatment, comparator, finite, branch):
    rows = [_rule_policy(seed, fold, treatment, comparator, finite)
            for seed, fold in AUD.IMPLICATED]
    assert AUD.apply_result_rule(rows)["branch"] == branch
    assert AUD.apply_result_rule([], reconstruction_passed=False)["branch"] == (
        "RECONSTRUCTION_OR_BINDING_FAILURE_NO_SCIENCE")


def _toy_retained(seeds, episodes_per_context):
    selection = AUD.CR._n_selection()
    old_offset = selection.OFFSET
    selection.OFFSET = AUD.OFFSET
    policies = []
    try:
        for seed_index, seed in enumerate(seeds):
            columns, _labels = AUD.CR.canonical_order(
                selection.generate_columns(seed, episodes_per_context))
            for fold in (0, 1):
                blocks = AUD.CR.stage_designs(columns, fold)
                exact_tail = AUD.CR.exact_solve(
                    blocks["tail"]["design64"], blocks["tail"]["targets64"])
                exact_reference_root = AUD.CR.exact_solve(
                    blocks["root"]["design64"],
                    AUD.CR.root_targets_fp32(blocks["root"], exact_tail))
                policy = {
                    "seed_id": seed, "fold_id": fold, "arms": {},
                    "exact_reference": {
                        "beta_tail": [float(value) for value in exact_tail],
                        "beta_root": [float(value) for value in exact_reference_root],
                    },
                }
                for arm_index, arm in enumerate(AUD.ARMS):
                    delta = numpy.asarray([
                        0.002 * (seed_index + 1), -0.001 * (fold + 1),
                        0.0005 * (arm_index + 1), 0.0, -0.00025,
                    ])
                    beta_tail = exact_tail + delta
                    targets = AUD.CR.root_targets_fp32(blocks["root"], beta_tail)
                    beta_root_exact = AUD.CR.exact_solve(blocks["root"]["design64"], targets)
                    beta_root = beta_root_exact.copy()
                    beta_root[arm_index] += 0.0001 * (fold + 1)
                    d_root = AUD._max_abs(beta_root, beta_root_exact)
                    finite = AUD.evaluate_exact_policy(beta_root, beta_tail)
                    policy["arms"][arm] = {
                        "beta_tail": [float(value) for value in beta_tail],
                        "beta_root": [float(value) for value in beta_root],
                        "d_learned_root": d_root,
                        "c_root": finite["c_root"],
                        "competence": {
                            "root_actions": finite["root_actions"],
                            "oracle_root_match": finite["oracle_root_match"],
                            "max_regret": finite["maximum_regret"],
                        },
                        "per_context": finite["contexts"],
                    }
                policies.append(policy)
    finally:
        selection.OFFSET = old_offset
    return {
        "object_id": AUD.INPUT_OBJECT_ID,
        "complete": True,
        "launch_sha": "toy-non-production",
        "arm_order": list(AUD.ARMS),
        "paired_rows": {
            "offset": AUD.OFFSET,
            "episodes_per_context": episodes_per_context,
            "training_support": list(AUD.K_TRAIN),
            "evaluation_support": list(AUD.K_EVAL),
        },
        "policies": policies,
    }


def test_binding_rejects_any_byte_or_digest_mismatch(tmp_path):
    retained = tmp_path / "retained.json"
    retained.write_text("{}", encoding="utf-8")
    with pytest.raises(AUD.ReconstructionFailure, match="byte-count/SHA-256"):
        AUD.bind_retained_summary(retained)


def test_actual_wall_cap_is_a_no_science_failure(monkeypatch):
    monkeypatch.setattr(
        AUD.time, "perf_counter", lambda: AUD.TOTAL_CAP_SECONDS + 0.001)
    with pytest.raises(AUD.ReconstructionFailure, match="actual wall"):
        AUD.enforce_wall_cap(0.0, production=True)
    assert AUD.enforce_wall_cap(0.0, production=False) > AUD.TOTAL_CAP_SECONDS


def test_binding_failure_cli_is_incomplete_attributed_and_nonzero(tmp_path):
    retained = tmp_path / "wrong.json"
    retained.write_text("{}", encoding="utf-8")
    receipt = tmp_path / "admission.json"
    receipt.write_text(json.dumps({
        "passed": True, "physical_floor_pass": True, "effective_floor_pass": True,
    }), encoding="utf-8")
    output = tmp_path / "failed-run"
    completed = subprocess.run([
        sys.executable,
        str(PROJECT_ROOT / "scripts/run_ucope_root_target_vs_root_fit_audit_r01.py"),
        "run", "--retained-summary", str(retained), "--output-root", str(output),
        "--admission-receipt", str(receipt), "--thread-cap", "1",
    ], cwd=PROJECT_ROOT, capture_output=True, text=True)
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert completed.returncode == 6
    assert summary["complete"] is False
    assert summary["scientific_polarity"] is None
    assert summary["result_rule"]["branch"] == (
        "RECONSTRUCTION_OR_BINDING_FAILURE_NO_SCIENCE")
    assert summary["launch_sha"] == subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, check=True,
        capture_output=True, text=True).stdout.strip()
    assert summary["argv"][0].endswith("run_ucope_root_target_vs_root_fit_audit_r01.py")
    assert "peak_rss_bytes" in summary["resources"]


def test_toy_same_draw_audit_is_complete_read_only_and_under_sixty_seconds(
        tmp_path, monkeypatch):
    seeds = AUD.B1_SEEDS[:2]
    episodes = 320
    retained = tmp_path / "retained.json"
    retained.write_text(json.dumps(_toy_retained(seeds, episodes), sort_keys=True), encoding="utf-8")
    payload = retained.read_bytes()
    receipt = tmp_path / "admission.json"
    receipt.write_text(json.dumps({
        "passed": True, "physical_floor_pass": True, "effective_floor_pass": True,
        "available_physical_bytes": 8 << 30, "effective_available_bytes": 8 << 30,
    }), encoding="utf-8")

    generated = []
    selection = AUD.CR._n_selection()
    original_generate = selection.generate_columns

    def counted_generate(seed_id, count):
        generated.append(seed_id)
        return original_generate(seed_id, count)

    monkeypatch.setattr(selection, "generate_columns", counted_generate)
    monkeypatch.setattr(AUD.CR, "_n_selection", lambda: selection)
    monkeypatch.setattr(AUD.CR, "_configure_topology", lambda _threads: None)
    monkeypatch.setattr(AUD.TW, "build_arm", lambda *_args, **_kwargs: pytest.fail("model constructed"))
    monkeypatch.setattr(AUD.TW, "optimizer_for", lambda *_args, **_kwargs: pytest.fail("optimizer constructed"))
    started = time.perf_counter()
    path = AUD.run_audit(
        retained, tmp_path / "run", receipt,
        argv=("toy-smoke",), expected_bytes=len(payload),
        expected_sha256=hashlib.sha256(payload).hexdigest(), seeds=seeds,
        episodes_per_context=episodes, production=False)
    elapsed = time.perf_counter() - started
    summary = json.loads(path.read_text(encoding="utf-8"))

    assert elapsed < 60.0
    assert path.name == "summary.json"
    assert summary["complete"] is True
    assert summary["result_rule"]["branch"] in {
        "ROOT_TARGET_PIPELINE_SHIFT_SUPPORTED",
        "FINITE_ROOT_FIT_RESIDUAL_SUPPORTED",
        "MIXED_ROOT_CAUSE",
    }
    assert generated == list(seeds)
    assert len(summary["policies"]) == 4
    assert len(summary["reconstruction_checks"]) == 16
    assert all(check["passed"] for check in summary["reconstruction_checks"])
    assert summary["counts"] == {
        "replayed_environment_episodes": 2 * len(AUD.CONTEXTS) * episodes,
        "replayed_environment_transitions": 2 * len(AUD.CONTEXTS) * episodes * 5,
        "new_unique_draw_keys": 0,
        "new_seed_identities": 0,
        "new_draw_identities": 0,
        "new_independent_sample_units": 0,
        "learner_training_rows": 0,
        "root_blocks_reconstructed": 4,
        "live_arm_target_arrays_computed": 8,
        "live_arm_exact_root_solves": 8,
        "exact_policy_evaluations": 8,
        "mse_exact_tail_checks": 4,
        "mse_exact_root_checks": 4,
        "live_root_distance_checks": 8,
        "optimizer_constructions": 0,
        "optimizer_steps": 0,
        "parameter_updates": 0,
        "fresh_sampled_evaluation_episodes": 0,
    }
    for policy in summary["policies"]:
        for arm in policy["arms"].values():
            assert len(arm["live_root_target_array_fp32"]) == episodes * len(AUD.CONTEXTS) // 2
            assert len(arm["live_exact_beta_root"]) == 7
            assert set(arm["target_margins"]) == {
                AUD.context_id(context) for context in AUD.CONTEXTS}
            assert set(arm["retained_finite_root"]["root_score_readout"]) == set(
                arm["exact_policy"]["contexts"])
            assert arm["d_root_absolute_error"] <= AUD.ABS_TOL

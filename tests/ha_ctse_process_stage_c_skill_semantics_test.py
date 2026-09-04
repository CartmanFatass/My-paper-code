"""Synthetic contract tests for the Stage C checkpoint-local audit."""

from __future__ import annotations

import copy
from dataclasses import replace
import importlib.util
import json
import math
import os
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch


_ROOT = Path(__file__).parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


_SPEC = importlib.util.spec_from_file_location(
    "analyze_stage_c_skill_semantics",
    _ROOT / "tools" / "analysis" / "analyze_stage_c_skill_semantics.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_AUDIT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_AUDIT)
cluster_bootstrap_ci = _AUDIT.cluster_bootstrap_ci
decide_outcome = _AUDIT.decide_outcome
natural_segments = _AUDIT.natural_segments
reconstruct_context_rows = _AUDIT.reconstruct_context_rows
load_audit_inputs = _AUDIT.load_audit_inputs
run_audit = _AUDIT.run_audit


DELTA = 1.0 / 12.0
DELTA_STRATUM = 1.0 / 24.0


def _metrics(**overrides):
    values = {
        "validity_ok": True,
        "support_ok": True,
        "policy_lineage_ok": True,
        "all_pairs_exact_upper_below_delta": False,
        "all_pairs_forced_upper_below_delta": False,
        "frozen_pair_exact_ci": (DELTA, 0.2),
        "frozen_pair_forced_ci": (DELTA, 0.2),
        "stability_pooled_ci": (DELTA, 0.2),
        "stability_stratum_cis": [(DELTA_STRATUM, 0.2)] * 12,
        "natural_raw_ci": (DELTA, 0.2),
        "natural_nuisance_ci": (0.01, 0.2),
        "natural_matched_margin_ci": (0.01, 0.2),
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    ("metrics", "expected"),
    [
        (_metrics(all_pairs_exact_upper_below_delta=True, all_pairs_forced_upper_below_delta=True), "A_NO_MATERIAL_Z_DEPENDENCE"),
        (_metrics(frozen_pair_exact_ci=(0.0, 0.0)), "B_UNSTABLE_OR_NONPERSISTENT_Z_EFFECT"),
        (_metrics(stability_stratum_cis=[(0.0, 0.0)] + [(DELTA_STRATUM, 0.2)] * 11), "B_UNSTABLE_OR_NONPERSISTENT_Z_EFFECT"),
        (_metrics(natural_raw_ci=(0.0, 0.0)), "C_STABLE_FORCED_NO_NATURAL_OVERLAP"),
        (_metrics(natural_nuisance_ci=(0.0, 0.0)), "E_NUISANCE_SHORTCUT"),
        (_metrics(natural_matched_margin_ci=(0.0, 0.0)), "E_NUISANCE_SHORTCUT"),
        (_metrics(policy_lineage_ok=False), "F_UNDERPOWERED_OR_UNIDENTIFIABLE"),
        (_metrics(support_ok=False), "F_UNDERPOWERED_OR_UNIDENTIFIABLE"),
        (_metrics(), "D_STABLE_LOCAL_NATURAL_OVERLAP"),
    ],
)
def test_decide_outcome_follows_frozen_a_to_f_order(metrics, expected):
    assert decide_outcome(metrics) == expected


def test_decide_outcome_sends_crossing_ci_to_underpowered():
    assert decide_outcome(_metrics(frozen_pair_exact_ci=(0.0, 0.2))) == "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
    assert decide_outcome(_metrics(natural_nuisance_ci=(0.0, 0.2))) == "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
    assert decide_outcome(_metrics(natural_matched_margin_ci=(0.0, 0.2))) == "F_UNDERPOWERED_OR_UNIDENTIFIABLE"


def test_reconstruct_context_rows_reads_only_lifecycle_fields_and_preserves_rejoin_age():
    rows = [
        {"episode": 0, "lifecycle_key": "a", "membership_epoch": 0, "physical_time": 0, "skill": 1, "active_n": 2, "reward": 99},
        {"episode": 0, "lifecycle_key": "a", "membership_epoch": 0, "physical_time": 1, "skill": 1, "active_n": 2, "owner": 12},
        {"episode": 0, "lifecycle_key": "a", "membership_epoch": 1, "physical_time": 3, "skill": 1, "active_n": 2, "progress": 3},
        {"episode": 0, "lifecycle_key": "a", "membership_epoch": 1, "physical_time": 4, "skill": 2, "active_n": 2, "success": True},
    ]

    contexts = reconstruct_context_rows(rows)

    assert [row["active_age"] for row in contexts] == [0, 1, 2, 0]
    assert [row["entry"] for row in contexts] == [True, True, True, True]
    assert all("reward" not in row and "owner" not in row and "progress" not in row for row in contexts)


def test_natural_segments_caps_windows_and_weights_each_eligible_segment_once():
    rows = []
    for step in range(15):
        rows.append({"episode": 0, "lifecycle_key": "long", "membership_epoch": 0, "physical_time": step, "skill": 0, "active_n": 2, "observation": [step]})
    for step in range(12):
        rows.append({"episode": 1, "lifecycle_key": "exact", "membership_epoch": 0, "physical_time": step, "skill": 1, "active_n": 2, "observation": [100 + step]})
    rows.extend({"episode": 2, "lifecycle_key": "short", "membership_epoch": 0, "physical_time": step, "skill": 2, "active_n": 2, "observation": [200 + step]} for step in range(11))

    segments = natural_segments(rows)

    assert [(segment["episode"], len(segment["rows"])) for segment in segments] == [(0, 12), (1, 12)]
    assert all(segment["weight"] == 1.0 for segment in segments)


def test_cluster_bootstrap_uses_local_rng_without_mutating_global_rng_or_inputs():
    values = [
        {"episode": 0, "value": 0.1},
        {"episode": 0, "value": 0.3},
        {"episode": 1, "value": 0.8},
    ]
    original = copy.deepcopy(values)
    random.seed(91)
    np.random.seed(92)
    torch.manual_seed(93)
    python_before = random.getstate()
    numpy_before = copy.deepcopy(np.random.get_state())
    torch_before = torch.get_rng_state().clone()

    ci = cluster_bootstrap_ci(values, value_key="value", repetitions=100, seed=307057)

    assert len(ci) == 3
    assert values == original
    assert random.getstate() == python_before
    assert np.array_equal(np.random.get_state()[1], numpy_before[1])
    assert torch.equal(torch.get_rng_state(), torch_before)


def test_load_audit_inputs_reconstructs_final_actor_strictly_without_rng_mutation(tmp_path):
    from ha_ctse_process.variable_roster_event_models import EventLowActor

    actor = EventLowActor(obs_dim=3, n_skills=3, action_dim=3, hidden_dim=4)
    checkpoint_path = tmp_path / "checkpoint.pt"
    torch.save(
        {
            "event_architecture": {
                "architecture_state": {"obs_dim": 3, "n_skills": 3, "action_dim": 3, "low_hidden_dim": 4, "action_space_type": "discrete"},
                "low_actor_state": actor.state_dict(),
            }
        },
        checkpoint_path,
    )
    result_path = tmp_path / "result.json"
    result_path.write_text("{\"synthetic\": true}", encoding="utf-8")
    torch.manual_seed(94)
    before = torch.get_rng_state().clone()

    loaded = load_audit_inputs(result_path, checkpoint_path)

    assert isinstance(loaded["actor"], EventLowActor)
    assert all(torch.equal(loaded["actor"].state_dict()[key], value) for key, value in actor.state_dict().items())
    assert torch.equal(torch.get_rng_state(), before)


def _source_m0():
    return {
        "formal_contract_exact": True,
        "environment_steps_exact": True,
        "high_optimizer_steps_exact": True,
        "low_optimizer_steps_exact": True,
        "training_ledger_ids_exact": True,
        "zero_evaluation_exact": True,
        "final_evaluation_exact": True,
        "forced_audit_exact": True,
        "intrinsic_reward_and_count_zero": True,
        "sampling_replay_probability": True,
        "sampling_replay_value": True,
        "natural_probability_read_replay": True,
        "all_updates_finite": True,
        "final_parameters_finite": True,
        "parameter_update_nonzero": True,
        "strict_vector_schema3_resume": True,
        "f0_common_support_reduction": True,
    }


def _make_actor(seed: int, *, zero: bool):
    from ha_ctse_process.variable_roster_event_models import EventLowActor

    before = torch.get_rng_state().clone()
    try:
        torch.manual_seed(seed)
        actor = EventLowActor(
            obs_dim=3,
            n_skills=3,
            action_dim=3,
            hidden_dim=4,
            action_space_type="discrete",
            device="cpu",
        )
    finally:
        torch.set_rng_state(before)
    if zero:
        with torch.no_grad():
            for parameter in actor.parameters():
                parameter.zero_()
    actor.eval()
    return actor


def _stored_log_probabilities(actor):
    observation = torch.zeros(1, 3)
    hidden = torch.zeros(1, 4)
    values = {}
    with torch.no_grad():
        for skill in range(3):
            features = actor._features(observation, torch.tensor([skill]))
            features, _ = actor.actor_rnn(features, hidden, torch.ones(1, 1))
            probabilities = actor.actor_act.action_out(features).probs[0]
            for action in range(3):
                values[(skill, action)] = float(torch.log(probabilities[action]).item())
    return values


def _real_shaped_arm(arm: str, *, zero_actor: bool, lineage_shift: float = 0.0):
    from ha_ctse_process.variable_roster_event_types import LowTransitionRow

    actor = _make_actor(421 if arm == "f0" else 422, zero=zero_actor)
    stored_logp = _stored_log_probabilities(actor)
    runtime_payloads = []
    for environment_index in range(16):
        rows = []
        for row_index in range(320):
            skill = (environment_index + row_index) % 3
            action = (2 * environment_index + row_index) % 3
            rows.append(
                LowTransitionRow(
                    lifecycle_key=f"member-{environment_index}",
                    membership_epoch=row_index // 80,
                    policy_version=250,
                    physical_time=row_index,
                    observation=np.zeros(3, dtype=np.float32),
                    skill=skill,
                    action=np.asarray([action], dtype=np.int64),
                    old_log_probability=stored_logp[(skill, action)] - lineage_shift,
                    old_value=0.0,
                    actor_hidden_before=np.zeros(4, dtype=np.float32),
                    critic_hidden_before=np.zeros(4, dtype=np.float32),
                    critic_member_features=np.zeros(1, dtype=np.float32),
                    active_critic_member_features=np.zeros((1, 1), dtype=np.float32),
                    active_skills=np.asarray([skill], dtype=np.int64),
                    critic_global_features=np.zeros(1, dtype=np.float32),
                    focal_active_index=0,
                    critic_source_summary=np.zeros(1, dtype=np.float32),
                    reward={"prohibited": "ignored"},
                    bootstrap_value=float("nan"),
                )
            )
        runtime_payloads.append(
            {"environment_index": environment_index, "low_ledger": rows}
        )
    effects = np.zeros((128, 3, 2, 4), dtype=np.float64)
    effects[..., 0] = 0.2
    effects[..., 1] = 0.3
    effects[..., 2] = np.nan
    effects[..., 3] = -999.0
    timing_rows = [
        {
            "episode_id": episode,
            "physical_time": physical_time,
            "reward": {"prohibited": "ignored"},
            "owner": object(),
        }
        for episode in range(256)
        for physical_time in range(80)
    ]
    result = {
        "schema_version": 1,
        "stage": "stage_c_paired_f0_f1",
        "arm": arm,
        "implementation_valid": True,
        "m0": _source_m0(),
        "contract": {
            "num_envs": 16,
            "outer_updates": 250,
            "environment_transitions": 320_000,
            "latent_skills": 3,
        },
        "counts": {
            "environment_steps": 320_000,
            "high_optimizer_steps": 1_000,
            "low_optimizer_steps": 1_000,
            "training_ledger_ids": 4_000,
            "intrinsic_applied_count": 0,
        },
        "forced_audit": {"effects": effects.tolist()},
        "timing_rows": timing_rows,
    }
    checkpoint = {
        "checkpoint_schema_version": 3,
        "high_controller": "variable_roster_event",
        "event_architecture": {
            "architecture_mode": arm,
            "event_architecture_schema_version": 1,
            "vector_checkpoint_schema_version": 1,
            "num_envs": 16,
            "runtime_state_absent_for_fresh_eval": False,
            "architecture_state": {
                "obs_dim": 3,
                "n_skills": 3,
                "action_dim": 3,
                "low_hidden_dim": 4,
                "action_space_type": "discrete",
            },
            "low_actor_state": copy.deepcopy(actor.state_dict()),
            "runtime_payloads": runtime_payloads,
            "counters": {
                "total_steps": 320_000,
                "update_idx": 250,
                "high_optimizer_steps": 1_000,
                "low_optimizer_steps": 1_000,
                "next_episode_id": 4_000,
                "intrinsic_applied_count": 0,
            },
            "tensor_immutability_sentinel": torch.tensor([1.0, 2.0, 3.0]),
        },
    }
    return {
        "result": result,
        "checkpoint": checkpoint,
        "source_identity": f"synthetic-{arm}",
    }


def _tensor_snapshot(value):
    if isinstance(value, torch.Tensor):
        return value.detach().clone()
    if isinstance(value, dict):
        return {key: _tensor_snapshot(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_tensor_snapshot(item) for item in value]
    return None


def _assert_tensors_unchanged(value, snapshot):
    if isinstance(value, torch.Tensor):
        assert torch.equal(value, snapshot)
    elif isinstance(value, dict):
        for key, item in value.items():
            _assert_tensors_unchanged(item, snapshot[key])
    elif isinstance(value, (list, tuple)):
        for item, saved in zip(value, snapshot):
            _assert_tensors_unchanged(item, saved)


def test_run_audit_real_shaped_dataclass_package_derives_local_reads_and_fails_only_for_missing_estimands():
    f0 = _real_shaped_arm("f0", zero_actor=True, lineage_shift=math.log(1.3))
    f1 = _real_shaped_arm("f1", zero_actor=False)
    checkpoint_snapshots = {
        "f0": _tensor_snapshot(f0["checkpoint"]),
        "f1": _tensor_snapshot(f1["checkpoint"]),
    }
    random.seed(711)
    np.random.seed(712)
    torch.manual_seed(713)
    python_before = random.getstate()
    numpy_before = copy.deepcopy(np.random.get_state())
    torch_before = torch.get_rng_state().clone()
    cuda_before = (
        [state.clone() for state in torch.cuda.get_rng_state_all()]
        if torch.cuda.is_available()
        else []
    )

    payload = run_audit(f0, f1)

    assert payload["selector_arm"] == "f1"
    assert payload["f1_outcome"] == "F_UNDERPOWERED_OR_UNIDENTIFIABLE"
    assert payload["m0"]["f0"]["valid"] is True
    assert payload["m0"]["f1"]["valid"] is True
    assert payload["m0"]["f1"]["checks"]["global_python_numpy_cpu_cuda_rng_unchanged"] is True
    assert payload["m0"]["f1"]["checks"]["checkpoint_tensors_unchanged"] is True
    f0_diagnostics = payload["diagnostics"]["f0"]
    f1_diagnostics = payload["diagnostics"]["f1"]
    assert f0_diagnostics["diagnostics"]["policy_lineage_ok"] is False
    assert f1_diagnostics["diagnostics"]["policy_lineage_ok"] is True
    assert f1_diagnostics["diagnostics"]["policy_lineage_abs_delta_p95"] == pytest.approx(0.0, abs=1e-6)
    assert f1_diagnostics["diagnostics"]["policy_lineage_threshold"] == pytest.approx(math.log(1.2))
    assert f0_diagnostics["diagnostics"]["all_skill_tv_means"] != f1_diagnostics["diagnostics"]["all_skill_tv_means"]
    assert f1_diagnostics["diagnostics"]["all_skill_distribution_shape"] == [5_120, 3, 3]
    assert f1_diagnostics["diagnostics"]["runtime_payload_count"] == 16
    assert f1_diagnostics["diagnostics"]["runtime_low_row_count"] == 5_120
    availability = f1_diagnostics["evidence_availability"]
    assert availability == {
        "fixed_input_rows": True,
        "all_skill_categorical_distributions": True,
        "policy_lineage_final_log_probabilities": True,
        "forced_aggregate_action_signatures": True,
        "natural_observation": True,
        "natural_recurrent_state": True,
        "natural_lifecycle_context": True,
        "forced_snapshot_observation": False,
        "forced_snapshot_recurrent_state": False,
        "forced_snapshot_lifecycle_metadata": False,
        "forced_snapshot_legal_support": False,
        "forced_snapshot_source_episode": False,
        "forced_nuisance_strata": False,
        "forced_per_stratum_support": False,
        "natural_source_episode": False,
        "forced_natural_shared_key": False,
        "natural_forced_alignment": False,
        "natural_common_support": False,
        "natural_endpoint_window_support": False,
    }
    assert all(reason.startswith("missing:") for reason in f1_diagnostics["reasons"])
    assert not any(key in f1_diagnostics["diagnostics"] for key in ("episode", "stratum", "stability_ci", "natural_overlap_ci"))
    assert random.getstate() == python_before
    numpy_after = np.random.get_state()
    assert numpy_after[0] == numpy_before[0]
    assert np.array_equal(numpy_after[1], numpy_before[1])
    assert numpy_after[2:] == numpy_before[2:]
    assert torch.equal(torch.get_rng_state(), torch_before)
    if cuda_before:
        assert all(
            torch.equal(after, before)
            for after, before in zip(torch.cuda.get_rng_state_all(), cuda_before)
        )
    _assert_tensors_unchanged(f0["checkpoint"], checkpoint_snapshots["f0"])
    _assert_tensors_unchanged(f1["checkpoint"], checkpoint_snapshots["f1"])


def test_run_audit_classifies_malformed_f0_actor_and_rows_as_invalid():
    f0 = _real_shaped_arm("f0", zero_actor=True)
    f1 = _real_shaped_arm("f1", zero_actor=False)

    wrong_arm = {**f0, "result": {**f0["result"], "arm": "f1"}}
    assert run_audit(wrong_arm, f1)["f1_outcome"] == "INVALID_ITERATION3_AUDIT"

    actor_bundle = dict(f0["checkpoint"]["event_architecture"])
    actor_bundle.pop("low_actor_state")
    missing_actor = {
        **f0,
        "checkpoint": {**f0["checkpoint"], "event_architecture": actor_bundle},
    }
    assert run_audit(missing_actor, f1)["f1_outcome"] == "INVALID_ITERATION3_AUDIT"

    categorical_bundle = dict(f0["checkpoint"]["event_architecture"])
    categorical_state = copy.deepcopy(categorical_bundle["low_actor_state"])
    categorical_state["actor_act.action_out.linear.bias"] = torch.tensor(
        [1_000.0, -1_000.0, -1_000.0]
    )
    categorical_bundle["low_actor_state"] = categorical_state
    invalid_categorical = {
        **f0,
        "checkpoint": {
            **f0["checkpoint"],
            "event_architecture": categorical_bundle,
        },
    }
    categorical_payload = run_audit(invalid_categorical, f1)
    assert categorical_payload["f1_outcome"] == "INVALID_ITERATION3_AUDIT"
    assert categorical_payload["m0"]["f0"]["checks"]["all_z_categorical_shape_support_and_simplex"] is False

    row_bundle = dict(f0["checkpoint"]["event_architecture"])
    runtime_payloads = list(row_bundle["runtime_payloads"])
    first_runtime = dict(runtime_payloads[0])
    low_ledger = list(first_runtime["low_ledger"])
    low_ledger[0] = replace(low_ledger[0], action=np.asarray([3], dtype=np.int64))
    first_runtime["low_ledger"] = low_ledger
    runtime_payloads[0] = first_runtime
    row_bundle["runtime_payloads"] = runtime_payloads
    malformed_rows = {
        **f0,
        "checkpoint": {**f0["checkpoint"], "event_architecture": row_bundle},
    }
    assert run_audit(malformed_rows, f1)["f1_outcome"] == "INVALID_ITERATION3_AUDIT"

    malformed_forced = {
        **f0,
        "result": {
            **f0["result"],
            "forced_audit": {"effects": np.zeros((128, 3, 2, 3)).tolist()},
        },
    }
    assert run_audit(malformed_forced, f1)["f1_outcome"] == "INVALID_ITERATION3_AUDIT"

    malformed_timing = {
        **f0,
        "result": {**f0["result"], "timing_rows": f0["result"]["timing_rows"][:-1]},
    }
    assert run_audit(malformed_timing, f1)["f1_outcome"] == "INVALID_ITERATION3_AUDIT"


def test_run_audit_selects_f1_fails_closed_and_writes_one_json_safe_artifact(tmp_path):
    f0 = {"result": {"arm_mode": "f0", "source_valid": True}}
    f1 = {"result": {"arm_mode": "f1", "source_valid": False}}
    output_path = tmp_path / "audit.json"

    payload = run_audit(f0, f1, output_path=output_path)

    assert payload["selector_arm"] == "f1"
    assert payload["f1_outcome"] == "INVALID_ITERATION3_AUDIT"
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == __import__("json").dumps(payload, sort_keys=True, indent=2) + "\n"
    assert "actor" not in output_path.read_text(encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        run_audit(f0, f1, output_path=output_path)
    assert list(tmp_path.iterdir()) == [output_path]


def test_direct_script_execution_bootstraps_repo_root_for_checkpoint_dataclass_unpickling(
    tmp_path,
):
    from ha_ctse_process.variable_roster_event_types import LowTransitionRow

    arm_root = tmp_path / "arm"
    result_dir = arm_root / "result"
    checkpoint_dir = arm_root / "checkpoints"
    result_dir.mkdir(parents=True)
    checkpoint_dir.mkdir(parents=True)
    (result_dir / "stage_c_arm.json").write_text("{}\n", encoding="utf-8")
    row = LowTransitionRow(
        lifecycle_key="synthetic",
        membership_epoch=0,
        policy_version=0,
        physical_time=0,
        observation=np.zeros(1, dtype=np.float32),
        skill=0,
        action=np.zeros(1, dtype=np.int64),
        old_log_probability=0.0,
        old_value=0.0,
        actor_hidden_before=np.zeros(1, dtype=np.float32),
        critic_hidden_before=np.zeros(1, dtype=np.float32),
        critic_member_features=np.zeros(1, dtype=np.float32),
        active_critic_member_features=np.zeros((1, 1), dtype=np.float32),
        active_skills=np.zeros(1, dtype=np.int64),
        critic_global_features=np.zeros(1, dtype=np.float32),
        focal_active_index=0,
        critic_source_summary=np.zeros(1, dtype=np.float32),
    )
    torch.save(
        {"checkpoint_schema_version": 3, "event_architecture": {"probe": row}},
        checkpoint_dir / "update_250_live.pt",
    )
    empty_pythonpath = tmp_path / "empty_pythonpath"
    empty_pythonpath.mkdir()
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(empty_pythonpath)
    output_path = tmp_path / "audit.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(_ROOT / "tools" / "analysis" / "analyze_stage_c_skill_semantics.py"),
            "--f0",
            str(arm_root),
            "--f1",
            str(arm_root),
            "--output",
            str(output_path),
        ],
        cwd=_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "ModuleNotFoundError" not in completed.stderr
    assert json.loads(output_path.read_text(encoding="utf-8"))["f1_outcome"] == (
        "INVALID_ITERATION3_AUDIT"
    )

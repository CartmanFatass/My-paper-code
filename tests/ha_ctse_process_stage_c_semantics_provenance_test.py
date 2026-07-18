from copy import deepcopy
import importlib.util
import inspect
import json
import math
from pathlib import Path
import random
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from ha_ctse_process import train as process_train
from ha_ctse_process.dynamic_roster_testbed import (
    ACTION_COUNT,
    OBSERVATION_DIM,
    DynamicRosterEventEnv,
)
from ha_ctse_process.variable_roster_event import VariableRosterEventCore


_ROOT = Path(__file__).parents[1]
_RUNNER_PATH = _ROOT / "scripts" / "run_stage_c_semantics_provenance_audit.py"
_RUNNER_SPEC = importlib.util.spec_from_file_location(
    "run_stage_c_semantics_provenance_audit", _RUNNER_PATH
)
_RUNNER = None
if _RUNNER_PATH.is_file():
    assert _RUNNER_SPEC is not None and _RUNNER_SPEC.loader is not None
    _RUNNER = importlib.util.module_from_spec(_RUNNER_SPEC)
    _RUNNER_SPEC.loader.exec_module(_RUNNER)


NATURAL_FIELDS = {
    "arm",
    "task_master_seed",
    "episode_id",
    "physical_time",
    "lifecycle_key",
    "membership_epoch",
    "observation",
    "actor_hidden_before",
    "natural_skill",
    "natural_action",
    "natural_action_log_probability",
    "primitive_legal_support",
    "primitive_probabilities",
    "active_set_size",
}
FORCED_FIELDS = NATURAL_FIELDS | {
    "focal_index",
    "active_keys",
    "active_membership_epochs",
    "active_skills",
    "frontier",
    "membership_deltas",
    "source_rng_ledger",
    "source_rng_states",
    "forced_effects",
}
PROHIBITED_FIELDS = {
    "task_phase",
    "reward",
    "utility",
    "progress",
    "role",
    "contact",
    "owner",
    "success",
}


def _interfaces_present() -> bool:
    forced = inspect.signature(process_train._forced_event_snapshot_effects)
    evaluate = inspect.signature(process_train._evaluate_event_model)
    return "focal_key" in forced.parameters and (
        "capture_semantic_provenance" in evaluate.parameters
    )


PROVENANCE_INTERFACES_PRESENT = _interfaces_present()


def _model_owner(mode: str = "f1", *, seed: int = 17057):
    torch.manual_seed(seed)
    return VariableRosterEventCore(
        architecture_mode=mode,
        obs_dim=OBSERVATION_DIM,
        critic_member_dim=OBSERVATION_DIM,
        critic_global_dim=8,
        n_skills=3,
        action_dim=ACTION_COUNT,
        member_hidden_dim=12,
        high_hidden_dim=10,
        low_hidden_dim=8,
        skill_embedding_dim=5,
        gamma=0.99,
        gae_lambda=0.95,
        environment_index=-1,
        device="cpu",
    )


def _source_at_time_one(owner):
    environment = DynamicRosterEventEnv(task_master_seed=97_057)
    core = process_train._make_event_runtime(
        owner,
        environment_index=0,
        episode_id=0,
        event_master_seed=77_057,
        action_master_seed=87_057,
    )
    transaction = environment.reset_event_runtime(0)
    bound = core.bind_due_frontier(transaction)
    core.apply_transaction(bound, deterministic_policy=False)
    snapshot = bound.post_membership_pre_policy_snapshot
    actions, _logp, _values = core.low_step(snapshot, deterministic=False)
    routed = {
        key: int(actions[index].detach().cpu())
        for index, key in enumerate(snapshot.keys)
    }
    step = environment.step_event_runtime(routed)
    core.complete_primitive_transition(float(step.reward))
    assert not step.terminated and step.next_transaction is not None
    bound = core.bind_due_frontier(step.next_transaction)
    core.apply_transaction(bound, deterministic_policy=False)
    return core, environment, bound.post_membership_pre_policy_snapshot


def _shared_key(row):
    return (
        row["arm"],
        row["task_master_seed"],
        row["episode_id"],
        row["physical_time"],
        row["lifecycle_key"],
        row["membership_epoch"],
    )


def _assert_no_prohibited_fields(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            assert str(key).lower() not in PROHIBITED_FIELDS
            _assert_no_prohibited_fields(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _assert_no_prohibited_fields(nested)


def _global_rng_state():
    return {
        "python": random.getstate(),
        "numpy": deepcopy(np.random.get_state()),
        "torch": torch.random.get_rng_state().clone(),
        "cuda": (
            [state.clone() for state in torch.cuda.get_rng_state_all()]
            if torch.cuda.is_available()
            else []
        ),
    }


def _assert_global_rng_equal(left, right):
    assert left["python"] == right["python"]
    assert left["numpy"][0] == right["numpy"][0]
    assert np.array_equal(left["numpy"][1], right["numpy"][1])
    assert left["numpy"][2:] == right["numpy"][2:]
    assert torch.equal(left["torch"], right["torch"])
    assert len(left["cuda"]) == len(right["cuda"])
    for lhs, rhs in zip(left["cuda"], right["cuda"]):
        assert torch.equal(lhs, rhs)


def _model_state(owner):
    modules = (
        owner.commitment_model,
        owner.event_critic,
        owner.low_actor,
        owner.low_critic,
    )
    return {
        "tensors": [
            {key: value.detach().clone() for key, value in module.state_dict().items()}
            for module in modules
        ],
        "grads": [
            [
                None if parameter.grad is None else parameter.grad.detach().clone()
                for parameter in module.parameters()
            ]
            for module in modules
        ],
        "training": [module.training for module in modules],
    }


def _assert_model_state_equal(left, right):
    assert left["training"] == right["training"]
    for lhs_module, rhs_module in zip(left["tensors"], right["tensors"]):
        assert lhs_module.keys() == rhs_module.keys()
        for key in lhs_module:
            assert torch.equal(lhs_module[key], rhs_module[key])
    for lhs_module, rhs_module in zip(left["grads"], right["grads"]):
        for lhs, rhs in zip(lhs_module, rhs_module):
            if lhs is None or rhs is None:
                assert lhs is None and rhs is None
            else:
                assert torch.equal(lhs, rhs)


def test_frozen_provenance_interfaces_are_present_and_default_off():
    forced = inspect.signature(process_train._forced_event_snapshot_effects)
    evaluate = inspect.signature(process_train._evaluate_event_model)
    assert "focal_key" in forced.parameters
    assert forced.parameters["focal_key"].default is None
    assert "capture_semantic_provenance" in evaluate.parameters
    assert evaluate.parameters["capture_semantic_provenance"].default is False


@pytest.mark.skipif(
    not PROVENANCE_INTERFACES_PRESENT,
    reason="RED: frozen provenance signatures are not implemented yet",
)
def test_explicit_focal_key_matches_legacy_audit_index_selection():
    owner = _model_owner()
    core, environment, snapshot = _source_at_time_one(owner)
    focal_key = snapshot.keys[0]
    legacy = process_train._forced_event_snapshot_effects(
        model_owner=owner,
        core=core,
        environment=environment,
        snapshot=snapshot,
        episode_id=0,
        audit_index=0,
    )
    explicit = process_train._forced_event_snapshot_effects(
        model_owner=owner,
        core=core,
        environment=environment,
        snapshot=snapshot,
        episode_id=0,
        audit_index=0,
        focal_key=focal_key,
    )
    assert np.asarray(legacy).shape == (3, 2, 4)
    assert explicit == legacy


@pytest.fixture(scope="module")
def evaluation_pair():
    if not PROVENANCE_INTERFACES_PRESENT:
        pytest.skip("RED: frozen provenance signatures are not implemented yet")

    owner = _model_owner()
    modules = (
        owner.commitment_model,
        owner.event_critic,
        owner.low_actor,
        owner.low_critic,
    )
    modules[0].train(True)
    modules[1].train(False)
    modules[2].train(True)
    modules[3].train(False)
    for module_index, module in enumerate(modules):
        for parameter_index, parameter in enumerate(module.parameters()):
            if (module_index + parameter_index) % 3 == 0:
                parameter.grad = torch.full_like(parameter, 0.125)

    original_forced = process_train._forced_event_snapshot_effects
    focal_calls = []

    def fast_forced_effects(**kwargs):
        focal_calls.append(
            (
                int(kwargs["episode_id"]),
                int(kwargs["audit_index"]),
                kwargs.get("focal_key"),
            )
        )
        base = float(int(kwargs["audit_index"]) + 1) / 1000.0
        return np.full((3, 2, 4), base, dtype=np.float64).tolist()

    try:
        process_train._forced_event_snapshot_effects = fast_forced_effects
        before_model = _model_state(owner)
        before_rng = _global_rng_state()
        legacy = process_train._evaluate_event_model(
            owner,
            deterministic=False,
            capture_prefix=False,
            capture_forced_audit=False,
        )
        after_legacy_model = _model_state(owner)
        after_legacy_rng = _global_rng_state()
        enabled = process_train._evaluate_event_model(
            owner,
            deterministic=False,
            capture_prefix=False,
            capture_forced_audit=False,
            capture_semantic_provenance=True,
        )
        after_enabled_model = _model_state(owner)
        after_enabled_rng = _global_rng_state()
    finally:
        process_train._forced_event_snapshot_effects = original_forced

    return SimpleNamespace(
        owner=owner,
        legacy=legacy,
        enabled=enabled,
        focal_calls=focal_calls,
        before_model=before_model,
        after_legacy_model=after_legacy_model,
        after_enabled_model=after_enabled_model,
        before_rng=before_rng,
        after_legacy_rng=after_legacy_rng,
        after_enabled_rng=after_enabled_rng,
    )


@pytest.mark.skipif(
    not PROVENANCE_INTERFACES_PRESENT,
    reason="RED: frozen provenance signatures are not implemented yet",
)
def test_default_off_legacy_payload_and_source_continuation_are_unchanged(
    evaluation_pair,
):
    pair = evaluation_pair
    assert "semantic_provenance" not in pair.legacy
    enabled_legacy_view = dict(pair.enabled)
    del enabled_legacy_view["semantic_provenance"]
    assert enabled_legacy_view == pair.legacy
    _assert_model_state_equal(pair.before_model, pair.after_legacy_model)
    _assert_model_state_equal(pair.before_model, pair.after_enabled_model)
    _assert_global_rng_equal(pair.before_rng, pair.after_legacy_rng)
    _assert_global_rng_equal(pair.before_rng, pair.after_enabled_rng)


@pytest.mark.skipif(
    not PROVENANCE_INTERFACES_PRESENT,
    reason="RED: frozen provenance signatures are not implemented yet",
)
def test_provenance_has_one_natural_match_per_forced_key_and_allowed_shapes(
    evaluation_pair,
):
    provenance = evaluation_pair.enabled["semantic_provenance"]
    assert provenance["schema"] == 1
    natural_rows = provenance["natural_rows"]
    forced_sources = provenance["forced_sources"]
    assert len(forced_sources) == 128
    assert {row["episode_id"] for row in natural_rows} == set(range(32))
    assert {row["episode_id"] for row in forced_sources} == set(range(32))

    natural_by_key = {}
    for row in natural_rows:
        assert set(row) == NATURAL_FIELDS
        natural_by_key.setdefault(_shared_key(row), []).append(row)
        assert row["arm"] == "f1"
        assert row["task_master_seed"] == 97_057
        assert len(row["observation"]) == OBSERVATION_DIM
        assert len(row["actor_hidden_before"]) == evaluation_pair.owner.low_hidden_dim
        assert row["natural_action"] in (0, 1, 2)
        assert row["primitive_legal_support"] == [0, 1, 2]
        probabilities = np.asarray(row["primitive_probabilities"], dtype=np.float64)
        assert probabilities.shape == (3,)
        assert np.isfinite(probabilities).all()
        assert float(probabilities.sum()) == pytest.approx(1.0, abs=1e-6)
        assert float(np.log(probabilities[row["natural_action"]])) == pytest.approx(
            row["natural_action_log_probability"], abs=1e-5
        )
        assert row["active_set_size"] in (2, 4, 6)

    for audit_index, row in enumerate(forced_sources):
        assert set(row) == FORCED_FIELDS
        matches = natural_by_key[_shared_key(row)]
        assert len(matches) == 1
        natural = matches[0]
        for field in NATURAL_FIELDS:
            assert row[field] == natural[field]
        active_count = row["active_set_size"]
        assert len(row["active_keys"]) == active_count
        assert len(row["active_membership_epochs"]) == active_count
        assert len(row["active_skills"]) == active_count
        assert row["active_keys"][row["focal_index"]] == row["lifecycle_key"]
        assert (
            row["active_membership_epochs"][row["focal_index"]]
            == row["membership_epoch"]
        )
        assert np.asarray(row["forced_effects"], dtype=np.float64).shape == (3, 2, 4)
        assert row["source_rng_ledger"]["episode_id"] == row["episode_id"]
        assert set(row["source_rng_ledger"]) == {
            "episode_id",
            "opportunity",
            "frontier_order",
            "policy_action",
        }
        assert set(row["source_rng_states"]) == {
            "opportunity",
            "frontier_order",
            "policy_action",
        }
        assert row["forced_effects"] == np.full(
            (3, 2, 4), float(audit_index + 1) / 1000.0
        ).tolist()

    assert len({_shared_key(row) for row in forced_sources}) == 128
    assert len(evaluation_pair.focal_calls) == 128
    assert all(focal is not None for _episode, _index, focal in evaluation_pair.focal_calls)


@pytest.mark.skipif(
    not PROVENANCE_INTERFACES_PRESENT,
    reason="RED: frozen provenance signatures are not implemented yet",
)
def test_provenance_recursively_excludes_task_and_outcome_shortcuts(evaluation_pair):
    _assert_no_prohibited_fields(evaluation_pair.enabled["semantic_provenance"])


def _runner():
    assert _RUNNER is not None, (
        "RED: scripts/run_stage_c_semantics_provenance_audit.py and its frozen "
        "runner symbols are not implemented"
    )
    return _RUNNER


def _source_bundle(arm):
    result = {
        "schema_version": 1,
        "stage": "stage_c_paired_f0_f1",
        "arm": arm,
        "implementation_valid": True,
        "m0": {name: True for name in _runner().REQUIRED_SOURCE_M0},
        "contract": {
            "num_envs": 16,
            "horizon": 80,
            "outer_updates": 250,
            "environment_transitions": 320_000,
            "latent_skills": 3,
            "evaluation_episodes_per_mode": 256,
        },
        "counts": {
            "environment_steps": 320_000,
            "high_optimizer_steps": 1_000,
            "low_optimizer_steps": 1_000,
            "training_ledger_ids": 4_000,
            "intrinsic_applied_count": 0,
        },
    }
    checkpoint = {
        "checkpoint_schema_version": 3,
        "high_controller": "variable_roster_event",
        "event_architecture": {
            "architecture_mode": arm,
            "event_architecture_schema_version": 1,
            "k0": 10,
            "opportunity_schedule_name": "uniform_active_gap_v1",
            "snapshot_capability_name": "variable_roster_event_snapshot",
            "snapshot_capability_version": 1,
            "runtime_state_absent_for_fresh_eval": True,
            "total_steps": 320_000,
            "update_idx": 250,
            "architecture_state": {
                "obs_dim": OBSERVATION_DIM,
                "critic_member_dim": OBSERVATION_DIM,
                "critic_global_dim": 8,
                "n_skills": 3,
                "action_dim": 3,
                "member_hidden_dim": 64,
                "high_hidden_dim": 64,
                "low_hidden_dim": 64,
                "skill_embedding_dim": 16,
                "action_space_type": "discrete",
                "gamma": 0.99,
                "gae_lambda": 0.95,
                "age_reference_steps": 500,
            },
        },
    }
    status = {
        "state": "complete",
        "phase": "terminal",
        "mode": arm,
        "update": 250,
        "updates_total": 250,
        "steps": 320_000,
        "steps_total": 320_000,
        "high_optimizer_steps": 1_000,
        "low_optimizer_steps": 1_000,
        "implementation_valid": True,
    }
    return {"result": result, "checkpoint": checkpoint, "arm_status": status}


def _registered_evaluation():
    effects = np.arange(128 * 3 * 2 * 4, dtype=np.float64).reshape(128, 3, 2, 4)
    effects /= float(effects.size)
    stochastic = {
        "episode_ids": list(range(256)),
        "deterministic": False,
        "environment_steps": 256 * 80,
        "persistent": [float(index % 2) for index in range(256)],
        "short": [float((index + 1) % 3) / 2.0 for index in range(256)],
        "utility": [float(index % 5) / 4.0 for index in range(256)],
        "natural_skill_step_counts": [1_000, 2_000, 3_000],
    }
    registered = {
        "final": {"stochastic": deepcopy(stochastic)},
        "forced_audit": {"effects": effects.tolist()},
    }
    evaluation = {
        **deepcopy(stochastic),
        "forced_audit": {"effects": effects.tolist()},
    }
    return registered, evaluation


def _provenance_row(arm, episode, offset):
    physical_time = offset
    lifecycle_key = f"member-{episode}-{offset}"
    natural_skill = (episode + offset) % 3
    probabilities = [0.2, 0.3, 0.5]
    natural_action = natural_skill
    natural = {
        "arm": arm,
        "task_master_seed": 97_057,
        "episode_id": episode,
        "physical_time": physical_time,
        "lifecycle_key": lifecycle_key,
        "membership_epoch": 0,
        "observation": [float(episode), float(offset)],
        "actor_hidden_before": [0.0, 1.0],
        "natural_skill": natural_skill,
        "natural_action": natural_action,
        "natural_action_log_probability": float(math.log(probabilities[natural_action])),
        "primitive_legal_support": [0, 1, 2],
        "primitive_probabilities": probabilities,
        "active_set_size": 2,
    }
    forced = {
        **deepcopy(natural),
        "focal_index": 0,
        "active_keys": [lifecycle_key, f"peer-{episode}-{offset}"],
        "active_membership_epochs": [0, 0],
        "active_skills": [natural_skill, (natural_skill + 1) % 3],
        "frontier": [],
        "membership_deltas": [],
        "source_rng_ledger": {
            "episode_id": episode,
            "opportunity": {"master_seed": 77_057, "stream_id": 0},
            "frontier_order": {"master_seed": 77_057, "stream_id": 1},
            "policy_action": {"master_seed": 87_057, "stream_id": 2},
        },
        "source_rng_states": {
            "opportunity": {"bit_generator": "PCG64", "state": {"state": 1, "inc": 3}},
            "frontier_order": {"bit_generator": "PCG64", "state": {"state": 2, "inc": 5}},
            "policy_action": {"bit_generator": "PCG64", "state": {"state": 3, "inc": 7}},
        },
        "forced_effects": np.full((3, 2, 4), 0.1, dtype=np.float64).tolist(),
    }
    return natural, forced


def _synthetic_provenance(arm="f1"):
    natural_rows = []
    forced_sources = []
    for episode in range(32):
        for offset in range(4):
            natural, forced = _provenance_row(arm, episode, offset)
            natural_rows.append(natural)
            forced_sources.append(forced)
    return {"schema": 1, "natural_rows": natural_rows, "forced_sources": forced_sources}


def _decision_metrics(**overrides):
    delta = 1.0 / 12.0
    delta_stratum = 1.0 / 24.0
    values = {
        "validity_ok": True,
        "support_ok": True,
        "policy_lineage_ok": True,
        "all_pairs_exact_upper_below_delta": False,
        "all_pairs_forced_upper_below_delta": False,
        "frozen_pair_exact_ci": (delta, 0.2),
        "frozen_pair_forced_ci": (delta, 0.2),
        "stability_pooled_ci": (delta, 0.2),
        "stability_stratum_cis": [(delta_stratum, 0.2)] * 12,
        "natural_raw_ci": (delta, 0.2),
        "natural_nuisance_ci": (0.01, 0.2),
        "natural_matched_margin_ci": (0.01, 0.2),
    }
    values.update(overrides)
    return values


def test_runner_symbols_and_frozen_constants_are_present():
    runner = _runner()
    assert runner.DELTA == 1.0 / 12.0
    assert runner.DELTA_STRATUM == 1.0 / 24.0
    assert runner.LINEAGE_THRESHOLD == pytest.approx(math.log(1.2))
    assert runner.BOOTSTRAP_REPETITIONS == 10_000
    assert runner.REFERENCE_EPISODES == tuple(range(16))
    assert runner.INFERENCE_EPISODES == tuple(range(16, 32))
    assert runner.MIN_POOLED_EPISODES == 8
    assert runner.MIN_POOLED_FORCED_SNAPSHOTS == 24
    assert runner.MIN_STRATUM_EPISODES == 8
    assert runner.MIN_FORCED_SNAPSHOTS_PER_STRATUM == 8
    assert runner.MIN_EXACT_ROWS_PER_STRATUM == 32
    assert runner.MIN_NATURAL_WINDOWS_PER_SKILL == 24


def test_source_identity_requires_registered_headers_arm_update_and_terminal_manifest():
    runner = _runner()
    bundle = _source_bundle("f0")
    report = runner.validate_source_identity(bundle, "f0")
    assert report["valid"] is True
    assert all(report["checks"].values())

    wrong_arm = deepcopy(bundle)
    wrong_arm["checkpoint"]["event_architecture"]["architecture_mode"] = "f1"
    assert runner.validate_source_identity(wrong_arm, "f0")["valid"] is False
    wrong_update = deepcopy(bundle)
    wrong_update["checkpoint"]["event_architecture"]["update_idx"] = 249
    assert runner.validate_source_identity(wrong_update, "f0")["valid"] is False
    nonterminal = deepcopy(bundle)
    nonterminal["arm_status"]["state"] = "running"
    assert runner.validate_source_identity(nonterminal, "f0")["valid"] is False


def test_registered_parity_is_exact_and_any_mismatch_invalidates():
    runner = _runner()
    registered, evaluation = _registered_evaluation()
    report = runner.validate_registered_parity(registered, evaluation)
    assert report["valid"] is True
    assert all(report["checks"].values())

    mismatch = deepcopy(evaluation)
    mismatch["utility"][17] += 1e-12
    report = runner.validate_registered_parity(registered, mismatch)
    assert report["valid"] is False
    assert report["checks"]["stochastic_episode_outcomes_exact"] is False


def test_provenance_rejects_duplicate_missing_pair_and_source_tensor_mismatch():
    runner = _runner()
    provenance = _synthetic_provenance()
    assert runner.validate_provenance(provenance, "f1")["valid"] is True

    duplicate = deepcopy(provenance)
    duplicate["forced_sources"][-1] = deepcopy(duplicate["forced_sources"][0])
    report = runner.validate_provenance(duplicate, "f1")
    assert report["valid"] is False
    assert report["checks"]["forced_shared_keys_unique"] is False

    missing = deepcopy(provenance)
    missing["natural_rows"].pop()
    report = runner.validate_provenance(missing, "f1")
    assert report["valid"] is False
    assert report["checks"]["one_natural_match_per_forced_key"] is False

    mismatch = deepcopy(provenance)
    mismatch["forced_sources"][0]["actor_hidden_before"][0] = 99.0
    report = runner.validate_provenance(mismatch, "f1")
    assert report["valid"] is False
    assert report["checks"]["source_observation_and_hidden_exact"] is False


def test_reference_pair_selection_uses_only_episodes_zero_through_fifteen():
    runner = _runner()
    provenance = _synthetic_provenance()
    for row in provenance["forced_sources"]:
        effects = np.zeros((3, 2, 4), dtype=np.float64)
        if row["episode_id"] < 16:
            effects[1, :, 0] = 0.2
            effects[2, :, 0] = 0.9
        else:
            effects[0, :, 0] = 100.0
        row["forced_effects"] = effects.tolist()

    selected = runner.select_reference_pair(provenance["forced_sources"])

    assert selected["pair"] == [0, 2]
    assert selected["reference_episodes"] == list(range(16))
    assert selected["inference_episodes"] == list(range(16, 32))


def test_synthetic_analysis_derives_finite_metrics_and_fails_closed_on_support(
    monkeypatch,
):
    from ha_ctse_process.variable_roster_event import EventLowActor

    runner = _runner()
    provenance = _synthetic_provenance()
    for row in provenance["forced_sources"]:
        effects = np.zeros((3, 2, 4), dtype=np.float64)
        effects[1, :, 0] = 0.4
        effects[2, :, 1] = 0.4
        row["forced_effects"] = effects.tolist()
    monkeypatch.setattr(runner, "BOOTSTRAP_REPETITIONS", 50)
    actor = EventLowActor(
        obs_dim=2,
        n_skills=3,
        action_dim=3,
        hidden_dim=2,
        action_space_type="discrete",
        device="cpu",
    )
    actor.eval()

    analysis = runner.analyze_semantics(provenance, actor)

    assert analysis["reference_selection"]["pair"] == [1, 2]
    assert analysis["metrics"]["support_ok"] is False
    assert len(analysis["metrics"]["stability_stratum_cis"]) == 24
    assert runner._finite_json_values(analysis)


@pytest.mark.parametrize(
    ("metrics", "expected"),
    [
        (
            _decision_metrics(
                all_pairs_exact_upper_below_delta=True,
                all_pairs_forced_upper_below_delta=True,
            ),
            "A_NO_MATERIAL_Z_DEPENDENCE",
        ),
        (
            _decision_metrics(frozen_pair_exact_ci=(0.0, 0.0)),
            "B_UNSTABLE_OR_NONPERSISTENT_Z_EFFECT",
        ),
        (
            _decision_metrics(natural_raw_ci=(0.0, 0.0)),
            "C_STABLE_FORCED_NO_NATURAL_OVERLAP",
        ),
        (_decision_metrics(), "D_STABLE_LOCAL_NATURAL_OVERLAP"),
        (
            _decision_metrics(natural_nuisance_ci=(0.0, 0.0)),
            "E_NUISANCE_SHORTCUT",
        ),
        (
            _decision_metrics(support_ok=False),
            "F_UNDERPOWERED_OR_UNIDENTIFIABLE",
        ),
    ],
)
def test_frozen_outcome_supports_a_through_f_without_priority_changes(metrics, expected):
    assert _runner().frozen_outcome(metrics) == expected


def test_prohibited_field_is_rejected_recursively():
    runner = _runner()
    provenance = _synthetic_provenance()
    provenance["forced_sources"][0]["source_rng_states"]["reward"] = 1.0
    report = runner.validate_provenance(provenance, "f1")
    assert report["valid"] is False
    assert report["checks"]["prohibited_fields_absent"] is False


def test_create_new_outputs_write_only_four_registered_files_and_refuse_second_write(
    tmp_path,
):
    runner = _runner()
    output_root = tmp_path / "audit"
    raw = {
        "f0": {"schema": 1, "natural_rows": [], "forced_sources": []},
        "f1": {"schema": 1, "natural_rows": [], "forced_sources": []},
    }
    result = {"schema_version": 1, "outcome": "F_UNDERPOWERED_OR_UNIDENTIFIABLE"}

    runner.write_audit_outputs(output_root, raw, result)

    assert sorted(
        path.relative_to(output_root).as_posix()
        for path in output_root.rglob("*")
        if path.is_file()
    ) == [
        "raw/f0_provenance.pt",
        "raw/f1_provenance.pt",
        "result/iteration4_provenance_audit.json",
        "runner_status.txt",
    ]
    assert torch.load(
        output_root / "raw" / "f0_provenance.pt", weights_only=False
    ) == raw["f0"]
    assert json.loads(
        (output_root / "result" / "iteration4_provenance_audit.json").read_text(
            encoding="utf-8"
        )
    ) == result
    with pytest.raises(FileExistsError, match="output root already exists"):
        runner.write_audit_outputs(output_root, raw, result)


def test_guarded_evaluation_preserves_global_rng_model_tensors_grads_and_modes():
    runner = _runner()
    owner = SimpleNamespace(
        commitment_model=torch.nn.Linear(2, 2),
        event_critic=torch.nn.Linear(2, 1),
        low_actor=torch.nn.Linear(2, 3),
        low_critic=torch.nn.Linear(2, 1),
    )
    owner.commitment_model.train(False)
    owner.event_critic.train(True)
    owner.low_actor.train(False)
    owner.low_critic.train(True)
    for module in (
        owner.commitment_model,
        owner.event_critic,
        owner.low_actor,
        owner.low_critic,
    ):
        for parameter in module.parameters():
            parameter.grad = torch.full_like(parameter, 0.25)
    random.seed(801)
    np.random.seed(802)
    torch.manual_seed(803)
    before_rng = _global_rng_state()
    before_model = runner.model_state_snapshot(owner)

    payload, checks = runner.evaluate_with_guards(owner, lambda: {"finite": 1.0})

    assert payload == {"finite": 1.0}
    assert checks == {
        "model_tensors_unchanged": True,
        "model_grads_unchanged": True,
        "module_modes_unchanged": True,
        "global_python_numpy_torch_cuda_rng_unchanged": True,
    }
    runner.assert_model_state_equal(before_model, runner.model_state_snapshot(owner))
    _assert_global_rng_equal(before_rng, _global_rng_state())

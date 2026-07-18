from copy import deepcopy
import inspect
import random
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

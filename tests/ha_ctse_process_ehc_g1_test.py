from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import random

import numpy as np
import pytest
import torch

import ha_ctse_process.ehc_g1 as ehc_g1
from ha_ctse_process.ehc_g1 import (
    ACTION_VALUES,
    ACTOR_WIDTH,
    ARM_NAMES,
    CRITIC_WIDTH,
    HIDDEN_WIDTH,
    MAXIMUM_CAPACITY,
    RolloutBatch,
    SeedRegistry,
    collect_rollout,
    compute_gae,
    initialize_matched_arms,
    load_checkpoint,
    optimize_rollout,
    replay_rollout,
    save_checkpoint,
    validate_replay,
)
from ha_ctse_process.temporal_duty_g1 import make_episode_spec


def test_matched_models_have_exact_information_surfaces_and_ehc_only_treatment():
    states = initialize_matched_arms(replicate=2)
    assert tuple(states) == ARM_NAMES
    assert ACTION_VALUES == (-1, 0, 1)

    reference = states["OR"].model.state_dict()
    for state in states.values():
        assert state.model.actor_encoder.in_features == ACTOR_WIDTH == 6
        assert state.model.actor_encoder.out_features == HIDDEN_WIDTH == 32
        assert state.model.recurrent.input_size == HIDDEN_WIDTH
        assert state.model.recurrent.hidden_size == HIDDEN_WIDTH
        assert state.model.critic_encoder.in_features == CRITIC_WIDTH == 10
        assert set(state.model.state_dict()) == set(reference)
        for name, value in state.model.state_dict().items():
            assert torch.equal(value, reference[name])

    actor = torch.tensor([[1.0, 1.0, 1.0, 1.0, 0.0, 0.5]])
    hidden = torch.zeros(1, HIDDEN_WIDTH)
    held_mark = torch.tensor([1.0])
    base_logits, _ = states["OR"].model.primitive_logits(
        actor, hidden, held_mark, arm="OR"
    )
    dum_logits, _ = states["DUM"].model.primitive_logits(
        actor, hidden, held_mark, arm="DUM"
    )
    ehc_logits, _ = states["EHC"].model.primitive_logits(
        actor, hidden, held_mark, arm="EHC"
    )
    assert torch.equal(base_logits, dum_logits)
    assert torch.allclose(
        ehc_logits - base_logits, states["EHC"].model.mark_treatment, atol=1e-7
    )

    critic_a = torch.zeros(1, 4, CRITIC_WIDTH)
    critic_b = torch.ones(1, 4, CRITIC_WIDTH)
    mask = torch.tensor([[True, True, False, False]])
    logits_a, _ = states["EHC"].model.primitive_logits(
        actor, hidden, held_mark, arm="EHC"
    )
    states["EHC"].model.value(critic_a, mask)
    states["EHC"].model.value(critic_b, mask)
    logits_b, _ = states["EHC"].model.primitive_logits(
        actor, hidden, held_mark, arm="EHC"
    )
    assert torch.equal(logits_a, logits_b)


def test_rng_namespaces_are_equal_but_not_shared_and_or_has_no_event_optimizer():
    states = initialize_matched_arms(replicate=1)
    assert states["OR"].event_optimizer is None
    assert states["DUM"].event_optimizer is not None
    assert states["EHC"].event_optimizer is not None
    assert states["DUM"].event_optimizer is not states["EHC"].event_optimizer

    for namespace in ("primitive", "event", "mark"):
        generators = [state.generators[namespace] for state in states.values()]
        assert len({id(generator) for generator in generators}) == 3
        assert all(
            torch.equal(generators[0].get_state(), generator.get_state())
            for generator in generators[1:]
        )


def test_checkpoint_is_g1_only_atomic_and_restores_owned_and_runtime_rng(tmp_path):
    state = initialize_matched_arms(replicate=3)["EHC"]
    optimize_rollout(state, _synthetic_rollout(state))
    random.seed(91)
    np.random.seed(92)
    torch.manual_seed(93)
    _ = random.random(), np.random.random(), torch.rand(2)
    expected_python = deepcopy(random.getstate())
    expected_numpy = deepcopy(np.random.get_state())
    expected_torch = torch.get_rng_state().clone()
    expected_owned = {
        name: generator.get_state().clone()
        for name, generator in state.generators.items()
    }

    path = tmp_path / "update_1.pt"
    save_checkpoint(path, state)
    assert path.is_file()
    assert not list(tmp_path.glob("*.tmp"))

    random.seed(1)
    np.random.seed(2)
    torch.manual_seed(3)
    for generator in state.generators.values():
        generator.manual_seed(4)

    loaded = load_checkpoint(
        path, arm="EHC", replicate=3, backend="cpu", torch_threads=1
    )
    assert loaded.update == 1
    assert loaded.base_optimizer_steps == 4
    assert loaded.event_optimizer_steps == 4
    for name, parameter in state.model.state_dict().items():
        assert torch.equal(parameter, loaded.model.state_dict()[name])
    assert random.getstate() == expected_python
    np_actual = np.random.get_state()
    assert np_actual[0] == expected_numpy[0]
    assert np.array_equal(np_actual[1], expected_numpy[1])
    assert np_actual[2:] == expected_numpy[2:]
    assert torch.equal(torch.get_rng_state(), expected_torch)
    for name, generator in loaded.generators.items():
        assert torch.equal(generator.get_state(), expected_owned[name])

    payload = torch.load(path, map_location="cpu", weights_only=False)
    foreign = tmp_path / "foreign.pt"
    for key, value in (
        ("source_family", "EVENT_HELD_COMMITMENT_LINK_G0"),
        ("backend", "cuda"),
        ("torch_threads", 2),
        ("base_optimizer_steps", 3),
        ("event_optimizer_steps", 3),
    ):
        tampered = deepcopy(payload)
        tampered[key] = value
        torch.save(tampered, foreign)
        with pytest.raises(ValueError):
            load_checkpoint(
                foreign, arm="EHC", replicate=3, backend="cpu", torch_threads=1
            )

    with pytest.raises(ValueError):
        load_checkpoint(
            path, arm="DUM", replicate=3, backend="cpu", torch_threads=1
        )

    inconsistent_save = initialize_matched_arms(replicate=3)["DUM"]
    inconsistent_save.update = 1
    inconsistent_save.base_optimizer_steps = 3
    inconsistent_save.event_optimizer_steps = 4
    with pytest.raises(ValueError, match="optimizer exposure"):
        save_checkpoint(tmp_path / "bad_save.pt", inconsistent_save)

    or_state = initialize_matched_arms(replicate=3)["OR"]
    optimize_rollout(or_state, _synthetic_rollout(or_state))
    or_path = tmp_path / "or_update_1.pt"
    save_checkpoint(or_path, or_state)
    or_payload = torch.load(or_path, map_location="cpu", weights_only=False)
    or_payload["event_optimizer_steps"] = 1
    torch.save(or_payload, foreign)
    with pytest.raises(ValueError, match="optimizer exposure"):
        load_checkpoint(
            foreign, arm="OR", replicate=3, backend="cpu", torch_threads=1
        )


def test_checkpoint_replace_retries_transient_permission_error(tmp_path, monkeypatch):
    destination = tmp_path / "update_0.pt"
    state = initialize_matched_arms(replicate=0)["EHC"]
    real_replace = ehc_g1.os.replace
    calls = 0
    sleeps: list[float] = []

    def flaky_replace(source, target):
        nonlocal calls
        calls += 1
        if calls < 3:
            raise PermissionError("transient OneDrive lock")
        real_replace(source, target)

    monkeypatch.setattr(ehc_g1.os, "replace", flaky_replace)
    monkeypatch.setattr(ehc_g1.time, "sleep", sleeps.append)

    save_checkpoint(destination, state)

    assert calls == 3
    assert sleeps == [
        ehc_g1._ATOMIC_REPLACE_RETRY_DELAY_SECONDS,
        ehc_g1._ATOMIC_REPLACE_RETRY_DELAY_SECONDS,
    ]
    assert destination.is_file()
    assert not list(tmp_path.glob("*.tmp"))


def test_checkpoint_replace_exhaustion_reraises_and_cleans_temp(tmp_path, monkeypatch):
    destination = tmp_path / "update_0.pt"
    destination.write_bytes(b"prior checkpoint")
    state = initialize_matched_arms(replicate=0)["EHC"]
    calls = 0

    def locked_replace(_source, _target):
        nonlocal calls
        calls += 1
        raise PermissionError("persistent OneDrive lock")

    monkeypatch.setattr(ehc_g1.os, "replace", locked_replace)
    monkeypatch.setattr(ehc_g1.time, "sleep", lambda _seconds: None)

    with pytest.raises(PermissionError, match="persistent OneDrive lock"):
        save_checkpoint(destination, state)

    assert calls == ehc_g1._ATOMIC_REPLACE_ATTEMPTS
    assert destination.read_bytes() == b"prior checkpoint"
    assert not list(tmp_path.glob("*.tmp"))


def test_seed_registry_is_exact_and_rejects_mutated_registry():
    registry = SeedRegistry()
    assert registry.model == 158058
    assert registry.train_event == 172058
    assert registry.evaluation_primitive == 204058
    assert registry.replicate_offset == 1000
    with pytest.raises(ValueError):
        initialize_matched_arms(replicate=0, seed_registry={"model": 1})


def _synthetic_rollout(state) -> RolloutBatch:
    environments, horizon = 2, 3
    actor = torch.zeros(environments, horizon, MAXIMUM_CAPACITY, ACTOR_WIDTH)
    actor[:, :, 0] = torch.tensor(
        [
            [1.0, 1.0, 1.0, 1.0, 0.0, 0.5],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.5],
            [0.0, 0.0, 1.0, 0.0, 0.0, 0.5],
        ]
    )
    critic = torch.zeros(environments, horizon, MAXIMUM_CAPACITY, CRITIC_WIDTH)
    critic[..., :ACTOR_WIDTH] = actor
    active = torch.zeros(environments, horizon, MAXIMUM_CAPACITY, dtype=torch.bool)
    active[:, :, 0] = True
    reset = torch.zeros_like(active)
    reset[:, 0, 0] = True
    reset[:, 2, 0] = True
    held_mark = torch.zeros(environments, horizon, MAXIMUM_CAPACITY)
    if state.arm != "OR":
        held_mark[:, :, 0] = 1.0
    opportunity = torch.zeros(
        environments, horizon, MAXIMUM_CAPACITY, dtype=torch.long
    )
    if state.arm != "OR":
        opportunity[:, 0, 0] = 1  # CREATE
        opportunity[:, 1, 0] = 2  # natural RENEW
    actions = torch.full(
        (environments, horizon, MAXIMUM_CAPACITY), -1, dtype=torch.long
    )
    actions[:, :, 0] = torch.tensor([[0, 2, 0], [2, 0, 2]])
    events = torch.full_like(actions, -1)
    marks = torch.full_like(actions, -1)
    if state.arm != "OR":
        events[:, 1, 0] = 1
        marks[:, 0, 0] = 1
        marks[:, 1, 0] = 0
    zeros_member = torch.zeros(environments, horizon, MAXIMUM_CAPACITY)
    zeros_step = torch.zeros(environments, horizon)
    rewards = torch.tensor([[0.1, 0.2, 0.3], [0.0, 0.1, 0.2]])
    dones = torch.zeros(environments, horizon, dtype=torch.bool)
    dones[:, -1] = True
    batch = RolloutBatch(
        source_family="ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1",
        arm=state.arm,
        replicate=state.replicate,
        actor=actor,
        critic=critic,
        active_mask=active,
        reset_mask=reset,
        held_mark=held_mark,
        opportunity_kind=opportunity,
        actions=actions,
        events=events,
        marks=marks,
        old_primitive_logp=zeros_member,
        old_event_mark_logp=zeros_member.clone(),
        old_values=zeros_step,
        rewards=rewards,
        dones=dones,
        advantages=zeros_step.clone(),
        returns=zeros_step.clone(),
    )
    with torch.no_grad():
        replay = replay_rollout(state, batch)
        advantages, returns = compute_gae(rewards, replay.values, dones)
    return replace(
        batch,
        old_primitive_logp=replay.primitive_logp,
        old_event_mark_logp=replay.event_mark_logp,
        old_values=replay.values,
        advantages=advantages,
        returns=returns,
    )


def test_stored_draw_replay_uses_no_rng_and_corruption_fails_closed():
    state = initialize_matched_arms(replicate=0)["EHC"]
    batch = _synthetic_rollout(state)
    before = {
        name: generator.get_state().clone()
        for name, generator in state.generators.items()
    }
    assert validate_replay(state, batch) == {
        "primitive_error": 0.0,
        "event_error": 0.0,
        "value_error": 0.0,
    }
    for name, generator in state.generators.items():
        assert torch.equal(before[name], generator.get_state())

    corrupted_actions = batch.actions.clone()
    corrupted_actions[0, 0, 0] = 1
    with pytest.raises(ValueError, match="replay mismatch"):
        validate_replay(state, replace(batch, actions=corrupted_actions))


def test_four_full_rollout_passes_preserve_optimizer_ownership_and_exposure():
    states = initialize_matched_arms(replicate=4)
    before = {
        arm: {name: parameter.detach().clone() for name, parameter in state.model.named_parameters()}
        for arm, state in states.items()
    }
    for arm, state in states.items():
        metrics = optimize_rollout(state, _synthetic_rollout(state))
        assert metrics["base_optimizer_steps"] == 4
        assert metrics["event_optimizer_steps"] == (0 if arm == "OR" else 4)
        assert state.update == 1
        assert any(
            not torch.equal(parameter, before[arm][name])
            for name, parameter in state.model.named_parameters()
            if not name.startswith(("event_head.", "mark_head."))
        )
        event_changed = any(
            not torch.equal(parameter, before[arm][name])
            for name, parameter in state.model.named_parameters()
            if name.startswith(("event_head.", "mark_head."))
        )
        assert event_changed is (arm != "OR")
        if arm != "OR":
            base_ids = {
                id(parameter)
                for group in state.base_optimizer.param_groups
                for parameter in group["params"]
            }
            event_ids = {
                id(parameter)
                for group in state.event_optimizer.param_groups
                for parameter in group["params"]
            }
            assert base_ids.isdisjoint(event_ids)


def _episode_pair(
    registry: SeedRegistry, replicate: int = 0, profile: str = "train"
):
    offset = registry.replicate_offset * replicate
    evaluation = profile != "train"
    common = {
        "task_seed": (
            registry.evaluation_task if evaluation else registry.train_task
        ) + offset,
        "membership_seed": (
            registry.evaluation_membership
            if evaluation
            else registry.train_membership
        ) + offset,
        "duty_seed": (
            registry.evaluation_duty if evaluation else registry.train_duty
        ) + offset,
        "opportunity_seed": (
            registry.evaluation_opportunity
            if evaluation
            else registry.train_opportunity
        ) + offset,
    }
    return tuple(
        make_episode_spec(
            profile, base_id=0, sign_mate=sign_mate, **common
        )
        for sign_mate in (-1, 1)
    )


def test_collection_batches_lifecycles_and_matches_dum_ehc_event_exposure():
    states = initialize_matched_arms(replicate=0)
    specs = _episode_pair(states["OR"].seed_registry)
    or_event_before = states["OR"].generators["event"].get_state().clone()
    or_mark_before = states["OR"].generators["mark"].get_state().clone()

    batches = {
        arm: collect_rollout(state, specs)
        for arm, state in states.items()
    }
    or_batch, dum_batch, ehc_batch = (
        batches["OR"], batches["DUM"], batches["EHC"]
    )
    assert or_batch.actor.shape == (2, 80, MAXIMUM_CAPACITY, ACTOR_WIDTH)
    assert or_batch.critic.shape == (2, 80, MAXIMUM_CAPACITY, CRITIC_WIDTH)
    assert tuple((row["base_id"], row["sign_mate"]) for row in or_batch.provenance) == (
        (0, -1),
        (0, 1),
    )
    assert torch.count_nonzero(or_batch.opportunity_kind) == 0
    assert torch.equal(or_event_before, states["OR"].generators["event"].get_state())
    assert torch.equal(or_mark_before, states["OR"].generators["mark"].get_state())

    assert torch.equal(dum_batch.opportunity_kind, ehc_batch.opportunity_kind)
    assert torch.equal(dum_batch.events, ehc_batch.events)
    assert torch.equal(dum_batch.marks, ehc_batch.marks)
    assert dum_batch.exposure == ehc_batch.exposure
    assert dum_batch.exposure["create_opportunities"] > 0
    assert dum_batch.exposure["event_opportunities"] > 0
    assert len(dum_batch.natural_rows) == dum_batch.exposure["event_opportunities"]
    assert {
        row["event"] for row in dum_batch.natural_rows
    } <= {"KEEP", "RENEW"}
    assert all(
        row["source_family"] == "ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1"
        for row in dum_batch.natural_rows
    )
    for state in states.values():
        assert validate_replay(state, batches[state.arm])["value_error"] <= 1e-7

    metrics = optimize_rollout(states["DUM"], dum_batch)
    assert metrics["base_optimizer_steps"] == 4
    assert metrics["event_optimizer_steps"] == 4

    initial_or_new_segment = (
        (dum_batch.actor[..., 2] == 1.0)
        & (dum_batch.actor[..., 4] == 0.0)
        & dum_batch.active_mask
    )
    assert torch.all(dum_batch.reset_mask[initial_or_new_segment])
    assert all(outcome["reward_sum"] == outcome["utility"] for outcome in dum_batch.outcomes)


def test_deterministic_collection_consumes_no_owned_rng():
    state = initialize_matched_arms(replicate=0)["EHC"]
    before = {
        name: generator.get_state().clone()
        for name, generator in state.generators.items()
    }
    batch = collect_rollout(
        state, _episode_pair(state.seed_registry), deterministic=True
    )
    for name, generator in state.generators.items():
        assert torch.equal(before[name], generator.get_state())
    assert torch.isfinite(batch.old_primitive_logp[batch.active_mask]).all()
    assert set(batch.actions[batch.active_mask].tolist()) <= {0, 1, 2}


def test_evaluation_collection_uses_disjoint_policy_rng_namespaces():
    state = initialize_matched_arms(replicate=0)["EHC"]
    training_before = {
        name: state.generators[name].get_state().clone()
        for name in ("primitive", "event", "mark")
    }
    evaluation_before = {
        name: state.generators[f"evaluation_{name}"].get_state().clone()
        for name in ("primitive", "event", "mark")
    }
    collect_rollout(
        state,
        _episode_pair(state.seed_registry, profile="iid"),
        rng_namespace="evaluation",
    )
    for name, expected in training_before.items():
        assert torch.equal(expected, state.generators[name].get_state())
    assert all(
        not torch.equal(
            evaluation_before[name],
            state.generators[f"evaluation_{name}"].get_state(),
        )
        for name in ("primitive", "event", "mark")
    )
    with pytest.raises(ValueError, match="profile"):
        collect_rollout(
            state,
            _episode_pair(state.seed_registry),
            rng_namespace="evaluation",
        )

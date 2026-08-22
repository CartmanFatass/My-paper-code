from __future__ import annotations

import copy

import pytest
import torch

from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.model import (
    FoundationActorCritic,
    OrderActorCritic,
    TiedReversedController,
    clone_frozen_foundation_actor,
    frozen_foundation_digest,
    model_schema,
    shared_parameterization_contract,
    validate_static_model_contract,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.training import (
    DurationCorrectPPOTrainer,
    TrainingContractError,
    duration_correct_gae,
    freeze_update_batch,
    joint_ppo_loss_from_terms,
    registered_episode_schedule,
    registered_minibatch_plan,
    sample_actions_from_source,
    training_contract,
    validate_checkpoint_payload,
)


class _TestOnlyPermit:
    def __init__(self) -> None:
        self.materializations = []
        self.clones = []
        self.updates = []
        self.restores = []

    def require_model_materialization(
        self, *, card_revision, replicate, arm, initialization_source
    ):
        assert card_revision.endswith("20260821-02")
        self.materializations.append((replicate, arm, initialization_source))

    def require_foundation_clone(
        self, *, card_revision, replicate, arm, foundation_digest
    ):
        assert len(foundation_digest) == 64
        self.clones.append((replicate, arm, foundation_digest))

    def require_training_update(
        self, *, card_revision, replicate, arm, update, schedule
    ):
        self.updates.append((replicate, arm, update, schedule))

    def require_checkpoint_restore(
        self, *, card_revision, replicate, arm, completed_updates
    ):
        self.restores.append((replicate, arm, completed_updates))


class _TestOnlyUniforms:
    def __init__(self) -> None:
        self.calls = []

    def initialization_uniforms(
        self, *, replicate, arm, tensor_name, count
    ):
        self.calls.append((replicate, arm, tensor_name, count))
        # Exactly float32-representable, deterministic TEST-only values.
        return tuple(((index % 8) + 1) / 16.0 for index in range(count))


class _TestOnlyPermutations:
    def __init__(self) -> None:
        self.calls = []

    def permutation_indices(self, *, replicate, arm, update, epoch, count):
        self.calls.append((replicate, arm, update, epoch, count))
        values = tuple(range(count))
        shift = epoch % count
        return values[shift:] + values[:shift]


class _TestOnlyActionUniforms:
    def __init__(self, values):
        self.values = tuple(values)
        self.calls = []

    def action_uniform(
        self, *, replicate, domain, update, episode_slot, renewal
    ):
        self.calls.append((replicate, domain, update, episode_slot, renewal))
        return self.values[len(self.calls) - 1]


def _models():
    permit = _TestOnlyPermit()
    source = _TestOnlyUniforms()
    foundation = FoundationActorCritic(
        permit=permit, replicate=3, initialization_source=source
    )
    treat = OrderActorCritic(
        "TREAT",
        frozen_foundation=clone_frozen_foundation_actor(
            foundation, permit=permit, arm="TREAT"
        ),
        permit=permit,
        initialization_source=source,
    )
    free = OrderActorCritic(
        "FREE",
        frozen_foundation=clone_frozen_foundation_actor(
            foundation, permit=permit, arm="FREE"
        ),
        permit=permit,
        initialization_source=source,
    )
    set_free = OrderActorCritic(
        "SET",
        frozen_foundation=clone_frozen_foundation_actor(
            foundation, permit=permit, arm="SET"
        ),
        permit=permit,
        initialization_source=source,
    )
    return permit, source, foundation, treat, free, set_free


def _update_fixture(model, update=1):
    schedule = registered_episode_schedule(
        "FOUNDATION" if isinstance(model, FoundationActorCritic) else model.arm
    )
    count = 12
    observation = torch.linspace(-0.25, 0.25, count * 18, dtype=torch.float32).reshape(count, 18)
    announced_k = torch.tensor([slot.k for slot in schedule], dtype=torch.int64)
    q = None
    if isinstance(model, OrderActorCritic):
        q = torch.tensor([slot.q for slot in schedule], dtype=torch.float32)
    return freeze_update_batch(
        model,
        replicate=model.replicate,
        update=update,
        observation=observation,
        physical_q=q,
        announced_k=announced_k,
        actions=torch.tensor(tuple(index % 18 for index in range(count)), dtype=torch.int64),
        primitive_rewards=tuple(((index - 5) / 20.0,) for index in range(count)),
        nonterminal=torch.zeros(count, dtype=torch.bool),
        episode_offsets=tuple(range(13)),
    )


def test_exact_schemas_injected_initialization_and_shared_k_parameterization():
    assert validate_static_model_contract() == {
        "FOUNDATION": 24_115,
        "TREAT": 6_146,
        "FREE": 12_756,
        "SET": 12_756,
    }
    assert model_schema("FOUNDATION").parameter_count == 24_115
    assert model_schema("TREAT").parameter_count == 12_882 + 6_146
    assert shared_parameterization_contract() == {
        "train_k": (5, 11),
        "target_schedules": (7, 13, (7, 13), (13, 7)),
        "one_parameter_vector_across_k": True,
        "per_k_heads": 0,
        "per_k_initializers": 0,
        "per_k_optimizers": 0,
        "per_k_checkpoints": 0,
        "switch_resets": False,
        "recurrent_state": False,
    }

    permit, source, foundation, treat, free, set_free = _models()
    assert sum(parameter.numel() for parameter in foundation.actor.parameters()) == 12_882
    assert sum(parameter.numel() for parameter in foundation.critic.parameters()) == 11_233
    assert sum(parameter.numel() for parameter in treat.parameters() if parameter.requires_grad) == 6_146
    assert sum(parameter.numel() for parameter in free.parameters() if parameter.requires_grad) == 12_756
    assert sum(parameter.numel() for parameter in set_free.parameters() if parameter.requires_grad) == 12_756
    assert len({frozen_foundation_digest(model) for model in (treat, free, set_free)}) == 1
    assert all(not parameter.requires_grad for parameter in treat.foundation.parameters())
    assert not any(call[2].endswith("scale.layers.1.weight") for call in source.calls)
    assert not any(call[2].endswith("residual.layers.2.weight") for call in source.calls)

    observation = torch.zeros((4, 18), dtype=torch.float32)
    q = torch.tensor([0.0, 1.0, 0.0, 1.0], dtype=torch.float32)
    parameter_ids = tuple(id(parameter) for parameter in treat.parameters())
    for k_value in (5, 11, 7, 13):
        output = treat(observation, q, torch.full((4,), k_value, dtype=torch.int64))
        assert output.logits.shape == (4, 18) and output.value.shape == (4,)
        assert tuple(id(parameter) for parameter in treat.parameters()) == parameter_ids
    assert all(value == pytest.approx(0.001) for value in output.alpha.tolist())


def test_free_set_and_tied_reversed_compositors_preserve_exact_semantics():
    _, _, _, treat, free, set_free = _models()
    observation = torch.linspace(-0.1, 0.1, 36, dtype=torch.float32).reshape(2, 18)
    q = torch.tensor([0.0, 1.0], dtype=torch.float32)
    k = torch.tensor([5, 11], dtype=torch.int64)
    treat_output = treat(observation, q, k)
    free_output = free(observation, q, k)
    # Uniform provider gives TREAT and FREE byte-equal scale initializers;
    # FREE's residual output is exactly zero.
    assert torch.equal(treat_output.logits, free_output.logits)

    set_first = set_free(observation, q, k)
    set_second = set_free(observation, 1.0 - q, k)
    assert torch.equal(set_first.logits, set_second.logits)
    assert torch.equal(set_first.value, set_second.value)
    assert torch.equal(set_first.compositor_q, torch.full_like(q, 0.5))

    reversed_controller = TiedReversedController(treat)
    reversed_output = reversed_controller(observation, q, k)
    direct_other_graph = treat.forward_with_compositor(
        observation, q, k, compositor_q=1.0 - q
    )
    assert reversed_controller.treatment is treat
    assert torch.equal(reversed_output.logits, direct_other_graph.logits)
    assert torch.equal(reversed_output.physical_q, q)
    assert torch.equal(reversed_output.compositor_q, 1.0 - q)


def test_caller_owned_action_uniforms_and_three_distinct_epoch_permutations():
    logits = torch.zeros((2, 18), dtype=torch.float32)
    source = _TestOnlyActionUniforms((0.0, 1.0 - 2.0**-20))
    actions = sample_actions_from_source(
        logits,
        source=source,
        replicate=2,
        arm="FREE",
        update=7,
        episode_slot=5,
        renewal_indices=(0, 4),
    )
    assert actions.tolist() == [0, 17]
    assert source.calls == [
        (2, "ORDER_SHARED", 7, 5, 0),
        (2, "ORDER_SHARED", 7, 5, 4),
    ]
    foundation_source = _TestOnlyActionUniforms((0.0,))
    sample_actions_from_source(
        logits[:1],
        source=foundation_source,
        replicate=2,
        arm="FOUNDATION",
        update=7,
        episode_slot=5,
        renewal_indices=(0,),
    )
    assert foundation_source.calls[0][1] == "FOUNDATION"

    permutations = _TestOnlyPermutations()
    plans = registered_minibatch_plan(
        permutations, replicate=2, arm="SET", update=7, count=11
    )
    assert [row.epoch for row in plans] == [0, 1, 2]
    assert len({row.permutation for row in plans}) == 3
    assert all(tuple(map(len, row.minibatches)) == (3, 3, 3, 2) for row in plans)
    assert permutations.calls == [(2, "SET", 7, epoch, 11) for epoch in range(3)]


def test_duration_correct_gae_is_episode_local_and_joint_loss_is_exact():
    rewards = []
    values = []
    nonterminal = []
    offsets = [0]
    for episode in range(12):
        rewards.extend(((1.0, 2.0), (3.0,)))
        values.extend((0.5, 0.25))
        nonterminal.extend((True, False))
        offsets.append(len(rewards))
    targets = duration_correct_gae(
        primitive_rewards=rewards,
        old_values=torch.tensor(values, dtype=torch.float32),
        nonterminal=torch.tensor(nonterminal, dtype=torch.bool),
        episode_offsets=offsets,
    )
    delta_second = 3.0 - 0.25
    delta_first = 1.0 + 0.995 * 2.0 + 0.995**2 * 0.25 - 0.5
    expected_first = delta_first + (0.995 * 0.93) ** 2 * delta_second
    assert targets.raw_advantages[0] == pytest.approx(expected_first)
    assert targets.raw_advantages[2] == pytest.approx(expected_first)
    assert torch.mean(targets.normalized_advantages) == pytest.approx(0.0, abs=1e-6)

    loss = joint_ppo_loss_from_terms(
        current_log_probability=torch.log(torch.tensor([1.30, 0.70], dtype=torch.float32)),
        current_value=torch.tensor([1.5, -0.5], dtype=torch.float32),
        current_entropy=torch.tensor([0.4, 0.6], dtype=torch.float32),
        old_log_probability=torch.zeros(2, dtype=torch.float32),
        value_target=torch.tensor([1.0, 0.25], dtype=torch.float32),
        normalized_advantage=torch.tensor([2.0, -3.0], dtype=torch.float32),
    )
    ratio = torch.tensor([1.30, 0.70], dtype=torch.float32)
    policy = -torch.minimum(
        ratio * torch.tensor([2.0, -3.0]),
        torch.clamp(ratio, 0.80, 1.20) * torch.tensor([2.0, -3.0]),
    ).mean()
    value = 0.5 * torch.mean((torch.tensor([1.5, -0.5]) - torch.tensor([1.0, 0.25])) ** 2)
    assert loss.total == pytest.approx(policy + 0.50 * value - 0.010 * 0.5)


def test_exact_one_update_global_adamw_and_in_memory_checkpoint_validation():
    permit = _TestOnlyPermit()
    source = _TestOnlyUniforms()
    foundation = FoundationActorCritic(
        permit=permit, replicate=0, initialization_source=source
    )
    batch = _update_fixture(foundation)
    trainer = DurationCorrectPPOTrainer(foundation, permit=permit)
    permutations = _TestOnlyPermutations()
    receipt = trainer.train_update(batch, permutations=permutations)
    assert receipt.arm == "FOUNDATION" and receipt.update == 1
    assert receipt.optimizer_step == 12 and len(receipt.steps) == 12
    assert [(row.epoch, row.minibatch) for row in receipt.steps] == [
        (epoch, minibatch) for epoch in range(3) for minibatch in range(4)
    ]
    assert permit.updates == [(0, "FOUNDATION", 1, registered_episode_schedule("FOUNDATION"))]

    payload = trainer.checkpoint_payload(completed_updates=1)
    validation = validate_checkpoint_payload(payload, foundation, trainer.optimizer)
    assert validation.completed_updates == 1
    assert validation.optimizer_step == 12
    assert validation.final_checkpoint is False
    assert len(validation.parameter_digest) == len(validation.optimizer_digest) == 64
    assert not any(isinstance(value, str) and ("/" in value or "\\" in value) for value in payload.values())

    tampered = dict(payload)
    tampered["per_k_state"] = {5: "forbidden"}
    with pytest.raises(TrainingContractError, match="per-k"):
        validate_checkpoint_payload(tampered, foundation, trainer.optimizer)

    restored_model = FoundationActorCritic(
        permit=permit, replicate=0, initialization_source=_TestOnlyUniforms()
    )
    restored_trainer = DurationCorrectPPOTrainer(restored_model, permit=permit)
    restored = restored_trainer.restore_checkpoint(payload)
    assert restored.optimizer_step == 12
    assert restored_trainer.optimizer.step_index == 12
    assert permit.restores[-1] == (0, "FOUNDATION", 1)
    assert all(
        torch.equal(left, right)
        for left, right in zip(foundation.parameters(), restored_model.parameters())
    )


def test_order_training_updates_only_adapter_and_checkpoint_rejects_foundation_change():
    permit, _, _, _, free, _ = _models()
    before = frozen_foundation_digest(free)
    trainer = DurationCorrectPPOTrainer(free, permit=permit)
    trainer.train_update(_update_fixture(free), permutations=_TestOnlyPermutations())
    assert frozen_foundation_digest(free) == before
    assert all(parameter.grad is None for parameter in free.foundation.parameters())

    payload = trainer.checkpoint_payload(completed_updates=1)
    receipt = validate_checkpoint_payload(payload, free, trainer.optimizer)
    assert receipt.arm == "FREE" and receipt.frozen_foundation_digest == before
    tampered = copy.deepcopy(payload)
    parameters = tampered["parameters"]
    name = next(name for name in parameters if name.startswith("foundation."))
    parameters[name].reshape(-1)[0] += 1.0
    with pytest.raises(TrainingContractError, match="frozen foundation"):
        validate_checkpoint_payload(tampered, free, trainer.optimizer)


def test_static_training_contract_freezes_budgets_without_runner_or_file_activity():
    contract = training_contract()
    assert contract["foundation_updates"] == 160
    assert contract["order_updates"] == 96
    assert contract["episodes_per_update"] == 12
    assert contract["epochs_per_update"] == 3
    assert contract["minibatches_per_epoch"] == 4
    assert contract["optimizer_steps_per_update"] == 12
    assert contract["optimizer_steps"] == {
        "FOUNDATION": 1_920,
        "TREAT": 1_152,
        "FREE": 1_152,
        "SET": 1_152,
    }
    assert contract["shared_parameterization_across_k"] is True
    assert contract["per_k_heads_updates_or_checkpoints"] == 0
    assert tuple((slot.k, slot.q) for slot in registered_episode_schedule("FOUNDATION")) == (
        (5, 0), (5, 0), (5, 0), (5, 1), (5, 1), (5, 1),
        (11, 0), (11, 0), (11, 0), (11, 1), (11, 1), (11, 1),
    )

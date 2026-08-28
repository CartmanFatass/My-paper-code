from __future__ import annotations

import math
from pathlib import Path

import pytest
import torch

from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_contract import (
    ACTOR_PARAMETER_COUNT,
    CRITIC_PARAMETER_COUNT,
    FOUNDATION_PARAMETER_COUNT,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_network import (
    build_technical_foundation,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_identity import (
    FoundationMutationError,
    seal_technical_foundation,
    technical_replicate_identity,
    verify_immutability,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_optimizer import (
    PersistentStepClock,
    build_adamw,
    clip_global_gradients,
    duration_correct_batch,
    fisher_yates_fixture,
    partition_permutation,
    ppo_losses,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_acceptance import (
    EXACT_TEST_COMMAND,
    build_s1_acceptance,
    canonical_json_bytes,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.barriers import StageBarrier


ROOT = Path(__file__).resolve().parents[4]


def test_foundation_network_is_exact_float32_order_erased_architecture() -> None:
    foundation = build_technical_foundation()

    assert tuple(foundation.actor.widths) == (14, 80, 80, 27)
    assert tuple(foundation.critic.widths) == (14, 80, 80, 1)
    assert ACTOR_PARAMETER_COUNT == 9_867
    assert CRITIC_PARAMETER_COUNT == 7_761
    assert FOUNDATION_PARAMETER_COUNT == 17_628
    assert sum(parameter.numel() for parameter in foundation.actor.parameters()) == 9_867
    assert sum(parameter.numel() for parameter in foundation.critic.parameters()) == 7_761
    assert sum(parameter.numel() for parameter in foundation.parameters()) == 17_628
    assert all(parameter.dtype is torch.float32 for parameter in foundation.parameters())
    assert all(
        torch.count_nonzero(parameter) == 0
        for name, parameter in foundation.named_parameters()
        if name.endswith("bias")
    )

    first_weight = foundation.actor.layers[0].weight.detach().reshape(-1)
    xavier_bound = math.sqrt(6.0 / (14 + 80))
    assert first_weight[0].item() == pytest.approx(
        -xavier_bound + xavier_bound / first_weight.numel(), abs=1e-8
    )
    assert first_weight[-1].item() == pytest.approx(
        xavier_bound - xavier_bound / first_weight.numel(), abs=1e-8
    )
    assert foundation.actor(torch.zeros((3, 14), dtype=torch.float32)).shape == (3, 27)
    assert foundation.critic(torch.zeros((3, 14), dtype=torch.float32)).shape == (3,)
    with pytest.raises(ValueError, match="exactly 14 order-erased"):
        foundation.actor(torch.zeros((3, 15), dtype=torch.float32))


def test_technical_replicate_identity_is_nonregistered_and_byte_immutable() -> None:
    first = technical_replicate_identity(0)
    last = technical_replicate_identity(23)
    foundation = build_technical_foundation()

    witness = seal_technical_foundation(foundation, first)

    assert first != last
    assert first.namespace.endswith("/00000000")
    assert last.namespace.endswith("/00000023")
    assert first.registered is False
    assert first.eligible is False
    assert first.activity_authorized is False
    assert all(not parameter.requires_grad for parameter in foundation.parameters())
    verify_immutability(foundation, first, witness)
    with torch.no_grad():
        foundation.actor.layers[0].weight[0, 0].add_(1.0)
    with pytest.raises(FoundationMutationError, match="foundation bytes changed"):
        verify_immutability(foundation, first, witness)
    with pytest.raises(ValueError, match="replicate_index"):
        technical_replicate_identity(24)


def test_duration_correct_gae_and_ppo_match_worked_literals() -> None:
    old_values = torch.tensor([0.5, 0.25], dtype=torch.float32)
    old_log_prob = torch.tensor([-0.7, -0.9], dtype=torch.float32)
    batch = duration_correct_batch(
        primitive_rewards=(
            torch.tensor([1.0, 2.0], dtype=torch.float32),
            torch.tensor([3.0], dtype=torch.float32),
        ),
        nonterminal=torch.tensor([True, False]),
        old_values=old_values,
        next_old_values=torch.tensor([0.25, 0.0], dtype=torch.float32),
        old_log_prob=old_log_prob,
    )

    assert batch.discounted_rewards.tolist() == pytest.approx([2.992, 3.0])
    assert batch.raw_advantages.tolist() == pytest.approx(
        [5.1505036784, 2.75], abs=1e-6
    )
    assert batch.targets.tolist() == pytest.approx([5.6505036784, 3.0], abs=1e-6)
    assert batch.normalized_advantages.tolist() == pytest.approx([1.0, -1.0], abs=1e-6)
    old_values.add_(100.0)
    old_log_prob.add_(100.0)
    assert batch.old_values.tolist() == [0.5, 0.25]
    assert batch.old_log_prob.tolist() == pytest.approx([-0.7, -0.9])

    losses = ppo_losses(
        new_log_prob=torch.tensor([0.1, -0.2], dtype=torch.float32),
        old_log_prob=torch.tensor([0.0, -0.1], dtype=torch.float32),
        normalized_advantage=torch.tensor([1.0, -1.0], dtype=torch.float32),
        value=torch.tensor([0.4, 0.5], dtype=torch.float32),
        target=torch.tensor([0.3, 0.7], dtype=torch.float32),
        entropy=torch.tensor([0.8, 0.6], dtype=torch.float32),
    )
    assert losses.policy.item() == pytest.approx(-0.10016675, abs=1e-6)
    assert losses.value.item() == pytest.approx(0.0125, abs=1e-7)
    assert losses.entropy.item() == pytest.approx(0.7, abs=1e-7)
    assert losses.total.item() == pytest.approx(-0.10169175, abs=1e-6)


def test_optimizer_partition_clipping_and_persistent_step_clock_are_exact() -> None:
    permutation = fisher_yates_fixture(5, swap_indices=(0, 0, 0, 0))
    minibatches = partition_permutation(permutation)

    assert permutation == (1, 2, 3, 4, 0)
    assert minibatches == ((1, 2), (3,), (4,), (0,))
    assert sorted(item for batch in minibatches for item in batch) == list(range(5))
    assert max(map(len, minibatches)) - min(map(len, minibatches)) == 1

    foundation = build_technical_foundation()
    optimizer = build_adamw(foundation.parameters())
    group = optimizer.param_groups[0]
    assert group["lr"] == 2.5e-4
    assert group["betas"] == (0.9, 0.999)
    assert group["eps"] == 1e-8
    assert group["weight_decay"] == 2e-5
    assert optimizer.state == {}
    for parameter in foundation.parameters():
        parameter.grad = torch.ones_like(parameter)
    preclip = clip_global_gradients(foundation.parameters())
    postclip = torch.sqrt(
        sum(torch.sum(parameter.grad * parameter.grad) for parameter in foundation.parameters())
    )
    assert preclip.item() == pytest.approx(math.sqrt(17_628), rel=1e-6)
    assert postclip.item() == pytest.approx(0.9, rel=1e-5)

    clock = PersistentStepClock.initial()
    for _ in range(192):
        clock = clock.complete_update(epoch_minibatch_count=16)
    assert clock.completed_updates == 192
    assert clock.global_one_based_index == 3_072
    with pytest.raises(ValueError, match="192 updates"):
        clock.complete_update(epoch_minibatch_count=16)


def test_s1_acceptance_binds_current_bytes_and_keeps_firewall_closed() -> None:
    acceptance = build_s1_acceptance(
        repository_root=ROOT,
        measurements={
            "cpu_seconds": 1.0,
            "wall_seconds": 2.0,
            "peak_working_set_bytes": 3,
            "peak_tracemalloc_bytes": 4,
            "read_bytes": 5,
            "write_bytes": 6,
        },
        verification_sha256="a" * 64,
    )

    StageBarrier.s0().validate_payload(acceptance)
    paths = tuple(row["path"] for row in acceptance["source_refs"])
    assert paths == tuple(sorted(paths))
    assert len(paths) == 6
    assert paths[-1] == (
        "tests/experiments/candidates/scdmp_variable_k/"
        "test_native_fusion_r01_foundation.py"
    )
    assert acceptance["verification_command"] == EXACT_TEST_COMMAND
    assert acceptance["firewall"] == {
        "registered_identity_present": False,
        "eligible_artifact_present": False,
        "question_relevant_value_visible": False,
        "activity_authorized": False,
        "effect_refs": [],
    }
    assert acceptance["effect_refs"] == []
    assert acceptance["activity_authorized"] is False
    assert canonical_json_bytes(acceptance).endswith(b"\n")

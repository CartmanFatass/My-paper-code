from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.folr_core.owner_epoch_survivor_bit_host import (
    ARMS,
    COMPLETE_RESET,
    INERT_Q0_KEY,
    ONE_BIT_OWNER_EPOCH_LATCH,
    OWNER_EPOCH,
    OWNER_KEY,
    S03_KEEP,
    HostDimensions,
    OwnerEpochSurvivorBitHost,
)
from experiments.candidates.folr_core.owner_epoch_survivor_bit_learnability import (
    SurvivorBitActor,
    _episode_batch,
    analyze,
    build_frozen_manifest,
    evaluate,
    registered_config,
    technical_smoke_config,
    train,
    validate_evaluation,
    validate_result,
    validate_train,
)
from ha_ctse_process.variable_roster_event_types import MembershipTransaction


SOURCE_COMMIT = "a" * 40


def _activation(dim: int = 8) -> torch.Tensor:
    return torch.linspace(-0.8, 0.8, dim, dtype=torch.float32, requires_grad=True)


def test_host_applies_typed_atomic_replacement_without_changing_owner_epoch() -> None:
    host = OwnerEpochSurvivorBitHost(
        arm=S03_KEEP,
        root=17,
        dimensions=HostDimensions(memory_dim=8),
    )
    host.cue_transition(1, _activation())
    transaction = host.replacement_transaction()
    assert isinstance(transaction, MembershipTransaction)
    assert [(row.kind, row.lifecycle_key) for row in transaction.atomic_membership_delta] == [
        ("TERMINAL_LEAVE", "inert_q0"),
        ("JOIN", "inert_q1"),
    ]
    witness = host.apply_replacement(transaction)
    assert witness.typed_transaction and witness.exact_deltas
    assert witness.owner_status_before == witness.owner_status_after == "ACTIVE"
    assert witness.owner_epoch_before == witness.owner_epoch_after == OWNER_EPOCH
    assert witness.owner_s03_digest_before == witness.owner_s03_digest_after_commit
    assert host.records[INERT_Q0_KEY].status == "TERMINAL"


def test_manual_or_changed_epoch_transaction_fails_closed() -> None:
    host = OwnerEpochSurvivorBitHost(
        arm=S03_KEEP,
        root=17,
        dimensions=HostDimensions(memory_dim=8),
    )
    host.cue_transition(0, _activation())
    transaction = host.replacement_transaction()
    object.__setattr__(transaction.atomic_membership_delta[0], "expected_membership_epoch", 1)
    with pytest.raises(ValueError, match="frozen atomic deltas"):
        host.apply_replacement(transaction)


def test_backends_preserve_gradient_or_exactly_expire_minimal_latch() -> None:
    dimensions = HostDimensions(memory_dim=8)
    keep = OwnerEpochSurvivorBitHost(arm=S03_KEEP, root=2, dimensions=dimensions)
    activation = _activation()
    keep.cue_transition(1, activation)
    carrier_before_commit = keep.owner.high_hidden
    keep.apply_replacement(keep.replacement_transaction())
    assert keep.owner.high_hidden is carrier_before_commit
    assert keep.choice_memory() is keep.owner.high_hidden
    assert keep.owner.high_hidden.requires_grad
    assert not hasattr(keep, "_trainable_s03")
    keep.terminal_transition(action=1, bit=1)

    reset = OwnerEpochSurvivorBitHost(arm=COMPLETE_RESET, root=2, dimensions=dimensions)
    reset.cue_transition(1, _activation())
    reset.apply_replacement(reset.replacement_transaction())
    assert reset.choice_memory() is reset.owner.high_hidden
    assert torch.equal(reset.owner.high_hidden, torch.zeros(8))
    assert not hasattr(reset, "_trainable_s03")

    latch = OwnerEpochSurvivorBitHost(
        arm=ONE_BIT_OWNER_EPOCH_LATCH,
        root=2,
        dimensions=dimensions,
    )
    latch.cue_transition(1, _activation())
    assert set(vars(latch.latch)) == {"lifecycle_key", "membership_epoch", "bit"}
    latch.apply_replacement(latch.replacement_transaction())
    assert torch.equal(latch.choice_memory(), torch.ones(8))
    terminal = latch.terminal_transition(action=1, bit=1)
    assert terminal["latch_expired"] and latch.latch is None


def test_choice_reads_current_committed_s03_and_never_a_stale_activation() -> None:
    host = OwnerEpochSurvivorBitHost(
        arm=S03_KEEP,
        root=9,
        dimensions=HostDimensions(memory_dim=8),
    )
    original = _activation()
    host.cue_transition(0, original)
    witness = host.apply_replacement(host.replacement_transaction())
    assert witness.same_owner_record_through_commit
    assert witness.same_s03_carrier_through_commit
    assert witness.choice_reads_committed_registered_s03
    assert not witness.second_information_bearing_s03_carrier

    replacement = torch.full((8,), 0.375, dtype=torch.float32, requires_grad=True)
    host.owner.high_hidden = replacement
    readout = host.choice_memory()
    assert readout is replacement
    assert readout is host.owner.high_hidden
    assert readout is not original


def test_reward_gradient_crosses_committed_registered_s03_to_cue_encoder() -> None:
    actor = SurvivorBitActor(memory_dim=8, hidden_dim=16, initialization_seed=113)
    _wait, activations = actor.cue_policy_call(torch.tensor([1], dtype=torch.int64))
    cue_activation = activations[0]
    host = OwnerEpochSurvivorBitHost(
        arm=S03_KEEP,
        root=19,
        dimensions=HostDimensions(memory_dim=8),
    )
    host.cue_transition(1, cue_activation)
    host.apply_replacement(host.replacement_transaction())
    committed = host.owner.high_hidden
    assert committed is cue_activation
    logits = actor.choice_policy_call(host.choice_memory().reshape(1, -1))
    # Unit terminal reward for the correct action: ordinary REINFORCE term.
    reward_loss = -torch.log_softmax(logits, dim=-1)[0, 1]
    reward_loss.backward()
    gradient = actor.cue_encoder.weight.grad
    assert gradient is not None
    assert float(torch.linalg.vector_norm(gradient)) > 0.0


def test_latch_fails_closed_and_expires_on_owner_epoch_mismatch() -> None:
    host = OwnerEpochSurvivorBitHost(
        arm=ONE_BIT_OWNER_EPOCH_LATCH,
        root=23,
        dimensions=HostDimensions(memory_dim=8),
    )
    host.cue_transition(1, _activation())
    host.apply_replacement(host.replacement_transaction())
    host.owner.membership_epoch = 1
    with pytest.raises(RuntimeError, match="expired on owner/epoch mismatch"):
        host.choice_memory()
    assert host.latch is None


def test_actor_parameter_order_shape_and_initialization_match_across_arms() -> None:
    actors = [SurvivorBitActor(memory_dim=8, hidden_dim=16, initialization_seed=991) for _ in ARMS]
    schemas = [actor.parameter_schema() for actor in actors]
    assert schemas[0] == schemas[1] == schemas[2]
    states = [actor.state_dict() for actor in actors]
    assert all(torch.equal(states[0][name], state[name]) for state in states[1:] for name in states[0])
    assert [row["name"] for row in schemas[0]] == [
        "cue_encoder.weight",
        "cue_encoder.bias",
        "wait_head.weight",
        "wait_head.bias",
        "memory_reader.weight",
        "memory_reader.bias",
        "action_head.weight",
        "action_head.bias",
    ]


def test_manifest_is_balanced_separated_and_paired_across_arms() -> None:
    config = technical_smoke_config()
    manifest = build_frozen_manifest(
        config=config,
        source_commit=SOURCE_COMMIT,
        run_id="folr_b1_technical_manifest",
    )
    rows = manifest["training"][str(config.master_seeds[0])]
    assert all(sum(int(row["bit"]) == 0 for row in batch) == 4 for batch in rows)
    streams = manifest["rng_streams"][str(config.master_seeds[0])]
    assert len({entry["derived_seed"] for entry in streams.values()}) == len(streams)
    eval_rows = manifest["evaluation"][str(config.master_seeds[0])]
    grouped: dict[int, list[dict[str, object]]] = {}
    for row in eval_rows:
        grouped.setdefault(int(row["root"]), []).append(row)
    assert len(grouped) == config.eval_episodes // 2
    assert all({int(row["bit"]) for row in pair} == {0, 1} for pair in grouped.values())
    assert all(len({float(row["action_uniform"]) for row in pair}) == 1 for pair in grouped.values())


def test_reset_matched_bit_kernels_are_bitwise_equal_before_sampling() -> None:
    actor = SurvivorBitActor(memory_dim=8, hidden_dim=16, initialization_seed=72)
    rows = [
        {"master_seed": 1, "phase": "evaluate", "episode": bit, "batch": None, "root": 55, "bit": bit, "action_uniform": 0.23, "rng_identity": {}}
        for bit in (0, 1)
    ]
    with torch.no_grad():
        _, actions, _, evidence = _episode_batch(
            actor=actor,
            arm=COMPLETE_RESET,
            rows=rows,
            dimensions=HostDimensions(memory_dim=8),
        )
    assert json.dumps(evidence[0]["post_event_kernel"], sort_keys=True) == json.dumps(
        evidence[1]["post_event_kernel"], sort_keys=True
    )
    assert int(actions[0]) == int(actions[1])
    assert evidence[0]["membership_transaction"]["public_pre_digest"] == evidence[1]["membership_transaction"]["public_pre_digest"]
    assert evidence[0]["membership_transaction"]["public_post_digest"] == evidence[1]["membership_transaction"]["public_post_digest"]


def test_proof_sized_three_phase_smoke_is_non_scientific_and_exact(tmp_path: Path) -> None:
    root = tmp_path / "smoke"
    train_summary = train(
        output_root=root,
        source_commit=SOURCE_COMMIT,
        run_id="folr_b1_proof_smoke",
        technical_smoke=True,
    )
    assert train_summary["activity_counts"] == {
        "actor_runs": 3,
        "train_episodes": 48,
        "environment_transitions": 96,
        "policy_calls": 96,
        "learner_calls": 6,
        "trainer_calls": 6,
        "optimizer_updates": 6,
        "k_search": 0,
        "hypothetical_transitions": 0,
    }
    evaluation = evaluate(output_root=root)
    assert evaluation["activity_counts"] == {
        "eval_episodes": 48,
        "environment_transitions": 96,
        "policy_calls": 96,
        "learner_calls": 0,
        "trainer_calls": 0,
        "optimizer_updates": 0,
    }
    result = analyze(output_root=root)
    assert result["decision"] == "TECHNICAL_SMOKE_ONLY"
    assert result["technical_only"] is True
    assert result["scientific_terminal_admitted"] is False
    assert result["activity_counts"]["total_episodes"] == 96
    assert result["activity_counts"]["total_environment_transitions"] == 192
    assert result["activity_counts"]["total_policy_calls"] == 192
    validate_train(root, require_full=False)
    validate_evaluation(root, require_full=False)
    validate_result(root / "raw_result.json", require_full=False)


def test_full_validator_rejects_smoke_and_registered_counts_are_frozen(tmp_path: Path) -> None:
    config = registered_config()
    assert len(config.arms) * len(config.master_seeds) == 24
    assert 24 * config.batches * config.batch_size == 49152
    assert 24 * config.eval_episodes == 12288
    root = tmp_path / "smoke"
    train(output_root=root, source_commit=SOURCE_COMMIT, run_id="reject_smoke", technical_smoke=True)
    with pytest.raises(ValueError, match="registered configuration"):
        validate_train(root, require_full=True)

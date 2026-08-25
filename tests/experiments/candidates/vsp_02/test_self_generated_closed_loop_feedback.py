from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
import inspect
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import Callable

import pytest
import torch

from experiments.candidates.vsp_02 import learned_cue_conditioned_lifecycle_control_v2 as b1
from experiments.candidates.vsp_02 import vsp02_b3_lifecycle_credit_sign_bridge as b3
from experiments.candidates.vsp_02 import self_generated_closed_loop_feedback as b4
from scripts import run_vsp02_b4_self_generated_closed_loop_feedback as runner


@pytest.fixture(scope="module")
def manifest() -> dict[str, object]:
    return b4.build_manifest(source_revision="TECHNICAL-PROOF-ONLY", run_id="vsp02-b4-proof", technical_only=True)


@pytest.fixture(scope="module")
def preflight(manifest: dict[str, object]) -> dict[str, object]:
    return b4.preflight_report(manifest)


def _one_update_proof(unit_id: str, root: int) -> dict[str, object]:
    models, optimizers = b4._new_learners(unit_id, root)
    learner_states = {arm: deepcopy(b4._initial_carried_learner_state()) for arm in b4.B4_ARMS}
    base_rng = b4._initial_learner_rng_state(unit_id, root)
    rng_states = {arm: deepcopy(base_rng) for arm in b4.B4_ARMS}
    tape = b4.AddressTape(unit_id, root)
    schedule = b4._schedule(unit_id, root)
    rows = schedule[: b4.B4_BATCH_SIZE]
    state_before_collection = b4._state_hashes(models, optimizers, learner_states, rng_states)
    generator_batch, _ = b4._collect_batch(
        unit_id=unit_id, update_index=0, rows=rows,
        model=models["RL_ORIGINAL_GENERATOR"], tape=tape,
    )
    state_after_generator_collection = b4._state_hashes(models, optimizers, learner_states, rng_states)
    self_batch, _ = b4._collect_batch(
        unit_id=unit_id, update_index=0, rows=rows,
        model=models["CREDIT_SIGN_SELF_FEEDBACK"], tape=tape,
    )
    state_after_both_collections = b4._state_hashes(models, optimizers, learner_states, rng_states)
    order = b4._ranked_permutation(tape, "minibatch_order", 0, b4.B4_BATCH_SIZE)
    ordered_generator = [generator_batch[index] for index in order]
    ordered_self = [self_batch[index] for index in order]
    frozen_before = (b4.digest(generator_batch), b4.digest(self_batch), b4.digest(b4._update_tape_receipt(tape, 0)))
    states = [state_after_both_collections]
    updates: dict[str, dict[str, object]] = {}
    for arm, batch in (
        ("RL_ORIGINAL_GENERATOR", ordered_generator),
        ("CREDIT_SIGN_SHADOW", ordered_generator),
        ("CREDIT_SIGN_SELF_FEEDBACK", ordered_self),
    ):
        updates[arm] = b4._optimizer_step(arm, models[arm], optimizers[arm], batch)
        learner_states[arm] = b4._advance_carried_learner_state(
            learner_states[arm], update_index=0,
            batch_digest=b4.digest(generator_batch if arm != "CREDIT_SIGN_SELF_FEEDBACK" else self_batch),
            batch_order=order,
        )
        states.append(b4._state_hashes(models, optimizers, learner_states, rng_states))
    frozen_after = (
        b4.digest(generator_batch), b4.digest(self_batch),
        b4.digest(b4._update_tape_receipt(b4.AddressTape(unit_id, root), 0)),
    )
    return {
        "unit_id": unit_id,
        "root": root,
        "models": models,
        "optimizers": optimizers,
        "learner_states": learner_states,
        "rng_states": rng_states,
        "tape": tape,
        "schedule": schedule,
        "generator_batch": generator_batch,
        "self_batch": self_batch,
        "order": order,
        "state_before_collection": state_before_collection,
        "state_after_generator_collection": state_after_generator_collection,
        "state_after_both_collections": state_after_both_collections,
        "states": states,
        "updates": updates,
        "frozen_before": frozen_before,
        "frozen_after": frozen_after,
    }


@pytest.fixture(scope="module")
def five_unit_proofs() -> list[dict[str, object]]:
    return [_one_update_proof(unit_id, root) for unit_id, root in b4.B4_UNITS]


def test_fresh_seed_namespace_and_predecessor_collision_fail_closed(monkeypatch: pytest.MonkeyPatch, manifest: dict[str, object]) -> None:
    assert b4.B4_SEED_PREFIX == "VSP02-B4-V1\0"
    assert b4.B4_PHYSICAL_TAPE_PREFIX == f"{b4.B4_ASSIGNMENT_ID}/PHYSICAL"
    assert not b4.B4_PHYSICAL_TAPE_PREFIX.startswith(b3.B3_PHYSICAL_TAPE_PREFIX)
    report = b4.seed_and_tape_report()
    assert report["all_b4_roots_unique"] is True
    assert report["collision_with_predecessor_values"] == []
    assert report["identity_collision_with_predecessors"] is False
    assert report["silent_reseed_path"] is False
    assert len({value for streams in report["derived_roots"].values() for value in streams.values()}) == (
        len(b4.B4_UNITS) * (len(b4.B4_SEED_STREAMS) + len(b4.B4_TAPE_KINDS))
    )
    with pytest.raises(ValueError, match="unregistered B4 unit/root"):
        b4.b4_seed("VSP02-B3-U01", 22_030_001, "parameter_initialization")
    with pytest.raises(ValueError, match="unregistered B4 seed stream"):
        b4.b4_seed(*b4.B4_UNITS[0], "silent_reseed")

    collided = deepcopy(report)
    collided["collision_with_predecessor_values"] = [1]
    monkeypatch.setattr(b4, "seed_and_tape_report", lambda: collided)
    failed = b4.preflight_report(manifest)
    assert failed["gates"]["P1"]["passed"] is False
    assert "silent reseed forbidden" in failed["gates"]["P1"]["issues"][0]


def test_complete_three_arm_initialization_is_byte_identical(five_unit_proofs: list[dict[str, object]], preflight: dict[str, object]) -> None:
    assert b4.B4_ARMS == (
        "RL_ORIGINAL_GENERATOR", "CREDIT_SIGN_SHADOW", "CREDIT_SIGN_SELF_FEEDBACK",
    )
    complete_fields = {
        "actor_critic_recurrent_parameters", "optimizer", "recurrent_state", "initial_state",
        "carried_learner_state", "registered_learner_rng_state",
    }
    for proof in five_unit_proofs:
        models, optimizers = proof["models"], proof["optimizers"]
        # Recreate the initial bytes because the proof objects have already taken one update.
        fresh_models, fresh_optimizers = b4._new_learners(proof["unit_id"], proof["root"])
        rng = b4._initial_learner_rng_state(proof["unit_id"], proof["root"])
        payloads = {
            arm: b4._complete_state_payload(
                fresh_models[arm], fresh_optimizers[arm], b4._initial_carried_learner_state(), rng
            )
            for arm in b4.B4_ARMS
        }
        assert all(set(payload) == complete_fields for payload in payloads.values())
        assert len({b4.canonical_bytes(payload) for payload in payloads.values()}) == 1
        assert all(model.gru.input_size == 10 and model.gru.hidden_size == 16 for model in fresh_models.values())
        assert all(next(model.parameters()).dtype == torch.float64 for model in fresh_models.values())
        assert models and optimizers
    for field in (
        "initial_complete_state_hashes", "initial_parameter_hashes", "initial_optimizer_hashes",
        "initial_recurrent_and_state_hashes", "initial_carried_learner_state_hashes",
        "initial_registered_learner_rng_state_hashes",
    ):
        assert set(preflight[field]) == set(b4.B4_ARMS)
        assert len(set(preflight[field].values())) == 1


def test_address_tape_is_immutable_deterministic_and_stream_complete() -> None:
    unit_id, root = b4.B4_UNITS[0]
    tape = b4.AddressTape(unit_id, root)
    recreated = b4.AddressTape(unit_id, root)
    with pytest.raises(FrozenInstanceError):
        tape.decimal_root = root + 1  # type: ignore[misc]
    words = {(kind, address): tape.word(kind, *address) for kind in b4.B4_TAPE_KINDS for address in ((0, 0), (0, 1), (1, 0))}
    assert words == {(kind, address): recreated.word(kind, *address) for kind in b4.B4_TAPE_KINDS for address in ((0, 0), (0, 1), (1, 0))}
    assert len(set(words.values())) == len(words)
    assert set(b4.B4_TAPE_STREAM_BY_KIND) == set(b4.B4_TAPE_KINDS)
    assert set(b4.B4_TAPE_STREAM_BY_KIND.values()) <= set(b4.B4_SEED_STREAMS)
    assert set(b4.B4_SEED_STREAMS) == {
        "parameter_initialization", "optimizer_initialization", "training_address_tape",
        "learner_stochasticity", "minibatch_order", "evaluation_address_tape",
    }
    for kind in b4.B4_TAPE_KINDS:
        address = tape.address(kind, 3, 4)
        assert address == {
            "treatment": b4.B4_ASSIGNMENT_ID, "unit_id": unit_id, "decimal_root": root,
            "stream": b4.B4_TAPE_STREAM_BY_KIND[kind], "field": kind, "address": [3, 4],
        }
    with pytest.raises(ValueError, match="unregistered B4 tape kind"):
        tape.word("unlisted_rng", 0)
    with pytest.raises(ValueError, match="nonempty"):
        tape.word("cue_schedule")
    assert "random" not in inspect.getsource(b4.AddressTape).lower()


def test_dual_collection_freeze_barrier_and_batch_immutability(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    original_collect, original_step = b4._collect_batch, b4._optimizer_step

    def collect_spy(**kwargs: object) -> tuple[list[dict[str, object]], int]:
        result = original_collect(**kwargs)  # type: ignore[arg-type]
        events.append("COLLECT_COMPLETE")
        return result

    def step_spy(*args: object, **kwargs: object) -> dict[str, object]:
        events.append(f"UPDATE_{args[0]}")
        return original_step(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(b4, "_collect_batch", collect_spy)
    monkeypatch.setattr(b4, "_optimizer_step", step_spy)
    monkeypatch.setattr(b4, "B4_UPDATES_PER_UNIT", 1)
    monkeypatch.setattr(b4, "_schedule_contract", lambda rows: len(rows) == 8)
    result = b4._train_unit(*b4.B4_UNITS[0])
    assert events == [
        "COLLECT_COMPLETE", "COLLECT_COMPLETE", "UPDATE_RL_ORIGINAL_GENERATOR",
        "UPDATE_CREDIT_SIGN_SHADOW", "UPDATE_CREDIT_SIGN_SELF_FEEDBACK",
    ]
    receipt = result["training"]["barrier_receipts"][0]
    assert receipt["both_batches_frozen_before_any_update"] is True
    assert receipt["frozen_before_updates"] == receipt["frozen_after_updates"]
    rows = result["training"]["batch_records"][0]["generator_rows"]
    frozen_digest = b4.digest(rows)
    consumer_copy = deepcopy(rows)
    consumer_copy[0]["metadata"]["clone_id"] = "MUTATED-CONSUMER-COPY"
    assert b4.digest(rows) == frozen_digest
    assert b4.digest(consumer_copy) != frozen_digest


def test_first_collector_batches_are_byte_identical(five_unit_proofs: list[dict[str, object]]) -> None:
    for proof in five_unit_proofs:
        generator, own = proof["generator_batch"], proof["self_batch"]
        assert b4.canonical_bytes(generator) == b4.canonical_bytes(own)
        assert [b4.digest(row) for row in generator] == [b4.digest(row) for row in own]
        assert all(b4._immutable_row_contract(row) for row in generator)


def test_first_oracle_successors_have_complete_state_identity(five_unit_proofs: list[dict[str, object]]) -> None:
    manifest = b4.build_manifest(source_revision="PROOF", run_id="proof", technical_only=True)
    proof_receipt = b4.preflight_report(manifest)["dual_collector_barrier_proof"]
    assert proof_receipt["finite_actor_gradients"] is True
    assert "finite_nonzero_actor_gradients" not in proof_receipt
    for proof in five_unit_proofs:
        final_states = proof["states"][-1]
        assert final_states["CREDIT_SIGN_SHADOW"] == final_states["CREDIT_SIGN_SELF_FEEDBACK"]
        assert proof["updates"]["CREDIT_SIGN_SHADOW"]["parameters_after"] == proof["updates"]["CREDIT_SIGN_SELF_FEEDBACK"]["parameters_after"]
        assert proof["updates"]["CREDIT_SIGN_SHADOW"]["optimizer_after"] == proof["updates"]["CREDIT_SIGN_SELF_FEEDBACK"]["optimizer_after"]


def test_shadow_batch_bytes_and_order_match_generator_exactly(five_unit_proofs: list[dict[str, object]]) -> None:
    assert b4.FIXED_UPDATE_ORDER == b4.B4_ARMS
    for proof in five_unit_proofs:
        order = proof["order"]
        generator = proof["generator_batch"]
        ordered_bytes = [b4.canonical_bytes(generator[index]) for index in order]
        assert sorted(order) == list(range(b4.B4_BATCH_SIZE))
        assert ordered_bytes == [b4.canonical_bytes(proof["generator_batch"][index]) for index in order]
        assert proof["updates"]["RL_ORIGINAL_GENERATOR"]["parameters_before"] != proof["updates"]["RL_ORIGINAL_GENERATOR"]["parameters_after"]
        assert proof["updates"]["CREDIT_SIGN_SHADOW"]["parameters_before"] != proof["updates"]["CREDIT_SIGN_SHADOW"]["parameters_after"]
    train_source = inspect.getsource(b4._train_unit)
    assert '"RL_ORIGINAL_GENERATOR", models["RL_ORIGINAL_GENERATOR"], optimizers["RL_ORIGINAL_GENERATOR"], ordered_generator' in train_source
    assert '"CREDIT_SIGN_SHADOW", models["CREDIT_SIGN_SHADOW"], optimizers["CREDIT_SIGN_SHADOW"], ordered_generator' in train_source


def test_per_update_noninterference_receipts_preserve_all_other_arms(five_unit_proofs: list[dict[str, object]]) -> None:
    for proof in five_unit_proofs:
        assert proof["state_before_collection"] == proof["state_after_generator_collection"] == proof["state_after_both_collections"]
        pre, after_generator, after_shadow, after_self = proof["states"]
        assert all(after_generator[arm] == pre[arm] for arm in b4.B4_ARMS[1:])
        assert after_shadow["RL_ORIGINAL_GENERATOR"] == after_generator["RL_ORIGINAL_GENERATOR"]
        assert after_shadow["CREDIT_SIGN_SELF_FEEDBACK"] == after_generator["CREDIT_SIGN_SELF_FEEDBACK"]
        assert after_self["RL_ORIGINAL_GENERATOR"] == after_shadow["RL_ORIGINAL_GENERATOR"]
        assert after_self["CREDIT_SIGN_SHADOW"] == after_shadow["CREDIT_SIGN_SHADOW"]
        assert proof["frozen_before"] == proof["frozen_after"]


def test_every_unit_realizes_later_feedback_exposure_without_effect_threshold(five_unit_proofs: list[dict[str, object]]) -> None:
    for proof in five_unit_proofs:
        updates = proof["updates"]
        assert updates["RL_ORIGINAL_GENERATOR"]["parameters_after"] != updates["CREDIT_SIGN_SELF_FEEDBACK"]["parameters_after"]
        models, optimizers = proof["models"], proof["optimizers"]
        learner_states, rng_states = proof["learner_states"], proof["rng_states"]
        tape, schedule = proof["tape"], proof["schedule"]
        first_divergence = None
        for update_index in range(1, b4.B4_UPDATES_PER_UNIT):
            rows = schedule[update_index * 8 : (update_index + 1) * 8]
            before_collection = b4._state_hashes(models, optimizers, learner_states, rng_states)
            generator_batch, _ = b4._collect_batch(
                unit_id=proof["unit_id"], update_index=update_index, rows=rows,
                model=models["RL_ORIGINAL_GENERATOR"], tape=tape,
            )
            self_batch, _ = b4._collect_batch(
                unit_id=proof["unit_id"], update_index=update_index, rows=rows,
                model=models["CREDIT_SIGN_SELF_FEEDBACK"], tape=tape,
            )
            assert b4._state_hashes(models, optimizers, learner_states, rng_states) == before_collection
            for row_index, (generator_row, self_row) in enumerate(zip(generator_batch, self_batch)):
                if b4._batch_exposure_signature(generator_row) != b4._batch_exposure_signature(self_row):
                    first_divergence = (update_index, row_index)
                    break
            if first_divergence is not None:
                break
            order = b4._ranked_permutation(tape, "minibatch_order", update_index, 8)
            for arm, batch in (
                ("RL_ORIGINAL_GENERATOR", generator_batch),
                ("CREDIT_SIGN_SHADOW", generator_batch),
                ("CREDIT_SIGN_SELF_FEEDBACK", self_batch),
            ):
                ordered = [batch[index] for index in order]
                b4._optimizer_step(arm, models[arm], optimizers[arm], ordered)
                learner_states[arm] = b4._advance_carried_learner_state(
                    learner_states[arm], update_index=update_index,
                    batch_digest=b4.digest(batch), batch_order=order,
                )
        assert first_divergence is not None, f"inactive feedback edge for {proof['unit_id']}"
        assert 1 <= first_divergence[0] < 128


def test_b3_loss_firewall_and_evaluation_routes_are_preserved(five_unit_proofs: list[dict[str, object]], manifest: dict[str, object]) -> None:
    assert b4.ORIGINAL_ACTOR_ROUTE == b3.ORIGINAL_ACTOR_ROUTE
    assert b4.ORACLE_SIGN_ACTOR_ROUTE == b3.BRIDGE_ACTOR_ROUTE
    assert b4.CRITIC_ROUTE == b3.CRITIC_ROUTE
    assert b4._mixture_metrics_from_raw_q is b3._mixture_metrics_from_raw_q
    assert manifest["optimizer"] == {
        "name": "Adam", "learning_rate": 0.003, "betas": [0.9, 0.999], "epsilon": 1e-8,
        "weight_decay": 0.0, "amsgrad": False, "gradient_norm_clip": 1.0,
    }
    proof = five_unit_proofs[0]
    for row in proof["generator_batch"]:
        assert row["M_reset"] == [1, 0]
        assert row["M_active"] == [1, 1]
        assert row["M_valid"] == [0, 1]
        assert row["M_lifecycle"] == [0, 1]
        assert math.isclose(row["G"], sum(reward * b1.B1_GAMMA**i for i, reward in enumerate(row["R"])), abs_tol=1e-12)
    group = proof["optimizers"]["RL_ORIGINAL_GENERATOR"].param_groups[0]
    assert (group["lr"], group["betas"], group["eps"], group["weight_decay"], group["amsgrad"]) == (0.003, (0.9, 0.999), 1e-8, 0, False)
    source = inspect.getsource(b4._optimizer_step)
    assert source.index("loss.backward()") < source.index("clip_grad_norm_") < source.index("optimizer.step()")
    evaluation_source = inspect.getsource(b4._evaluate_arm_unit)
    assert "torch.no_grad()" in evaluation_source and "q_release > q_hold" in evaluation_source
    assert '"stochastic_action_draws": 0' in evaluation_source
    assert "sampling_uniform" not in evaluation_source
    panel = b4._evaluation_panel(*b4.B4_UNITS[0])
    assert len(panel) == 128
    assert {row["clone_id"] for row in panel}.isdisjoint({row["metadata"]["clone_id"] for row in proof["generator_batch"]})


@pytest.mark.parametrize(
    ("b3_arm", "b4_arm"),
    (("RL_ORIGINAL", "RL_ORIGINAL_GENERATOR"), ("CREDIT_SIGN_BRIDGE", "CREDIT_SIGN_SHADOW")),
)
def test_b3_actor_loss_reduction_gradients_and_one_step_successor_are_exact(
    b3_arm: str, b4_arm: str,
) -> None:
    unit_id, root = b4.B4_UNITS[0]
    initialized = b1.GRUActorCritic(init_seed=b4.b4_seed(unit_id, root, "parameter_initialization"))
    batch = b4._proof_batch(initialized)
    b3_model, b4_model = deepcopy(initialized), deepcopy(initialized)

    b3_loss, b3_route = b3._loss_terms(b3_arm, b3_model, batch)
    b4_loss, b4_route = b4._loss_terms(b4_arm, b4_model, batch)
    assert torch.equal(b3_loss, b4_loss)
    assert b3_route["actor_loss"] == b4_route["actor_loss"]
    assert b3_route["critic_loss"] == b4_route["critic_loss"]
    assert b3_route["advantages"] == b4_route["advantages"]
    assert b3_route["actor_coefficients"] == b4_route["actor_coefficients"]
    b3_gradients = torch.autograd.grad(b3_loss, tuple(b3_model.parameters()))
    b4_gradients = torch.autograd.grad(b4_loss, tuple(b4_model.parameters()))
    assert all(torch.equal(left, right) for left, right in zip(b3_gradients, b4_gradients))

    b3_step_model, b4_step_model = deepcopy(initialized), deepcopy(initialized)
    b3_optimizer = torch.optim.Adam(b3_step_model.parameters(), lr=0.003)
    b4_optimizer = torch.optim.Adam(b4_step_model.parameters(), lr=0.003)
    b3_update = b3._optimizer_step(b3_arm, b3_step_model, b3_optimizer, batch)
    b4_update = b4._optimizer_step(b4_arm, b4_step_model, b4_optimizer, batch)
    assert b3_update["parameters_after"] == b4_update["parameters_after"]
    assert b3_update["optimizer_after"] == b4_update["optimizer_after"]
    assert b4.canonical_bytes(b3.model_payload(b3_step_model)) == b4.canonical_bytes(b4.model_payload(b4_step_model))
    assert b4.canonical_bytes(b3.optimizer_payload(b3_optimizer)) == b4.canonical_bytes(b4.optimizer_payload(b4_optimizer))


def test_oracle_scalar_firewall_sign_and_magnitude_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    models, _ = b4._new_learners(*b4.B4_UNITS[0])
    batch = b4._proof_batch(models["RL_ORIGINAL_GENERATOR"])
    calls = 0
    original = b4.correctness_sign

    def counted(action: str, cue: int) -> float:
        nonlocal calls
        calls += 1
        return original(action, cue)

    monkeypatch.setattr(b4, "correctness_sign", counted)
    _, original_route = b4._loss_terms("RL_ORIGINAL_GENERATOR", models["RL_ORIGINAL_GENERATOR"], batch)
    assert calls == 0 and original_route["oracle_scalar_only"] is False
    _, oracle_route = b4._loss_terms("CREDIT_SIGN_SHADOW", models["CREDIT_SIGN_SHADOW"], batch)
    assert calls == 8 and oracle_route["oracle_scalar_only"] is True
    assert oracle_route["max_abs_magnitude_error"] == 0.0
    assert all(abs(coefficient) == abs(advantage) for coefficient, advantage in zip(oracle_route["actor_coefficients"], oracle_route["advantages"]))
    zero_batch = b4._proof_batch(models["CREDIT_SIGN_SELF_FEEDBACK"], zero_advantage=True)
    _, zero_route = b4._loss_terms("CREDIT_SIGN_SELF_FEEDBACK", models["CREDIT_SIGN_SELF_FEEDBACK"], zero_batch)
    assert zero_route["actor_coefficients"] == [0.0] * 8
    assert zero_route["zero_advantage_count"] == 8 and zero_route["nonzero_advantage_count"] == 0
    mutators: tuple[Callable[[dict[str, object]], None], ...] = (
        lambda row: row.pop("G"),
        lambda row: row.__setitem__("M_valid", [0, 0]),
        lambda row: row.__setitem__("M_lifecycle", [0, 0]),
        lambda row: row.__setitem__("G", float("nan")),
        lambda row: row.__setitem__("G", float("inf")),
    )
    for mutator in mutators:
        changed = deepcopy(batch)
        mutator(changed[0])
        with pytest.raises(ValueError, match="advantage|return"):
            b4._loss_terms("CREDIT_SIGN_SHADOW", models["CREDIT_SIGN_SHADOW"], changed)
    loss_source = inspect.getsource(b4._loss_terms)
    assert loss_source.index("_forward(model, observations)") < loss_source.index('metadata = row.get("metadata")')
    for forbidden_surface in (b4._collect_batch, b4._evaluate_arm_unit, b4.classify_b4):
        assert "correctness_sign" not in inspect.getsource(forbidden_surface)


def test_manifest_has_exact_counts_caps_and_no_extra_activity(manifest: dict[str, object]) -> None:
    assert b4.validate_manifest(manifest) == ()
    assert manifest["assignment_id"] == "VSP02-B4-SELF-GENERATED-CLOSED-LOOP-FEEDBACK"
    assert manifest["direction_id"] == "CAND-VSP-02"
    assert manifest["candidate"] == "CAND-VSP-02@adversarial-revision-v8"
    assert manifest["arms"] == list(b4.B4_ARMS)
    assert [(row["unit_id"], row["decimal_root"]) for row in manifest["units"]] == list(b4.B4_UNITS)
    assert manifest["training"] == {
        "updates_per_unit": 128, "episodes_per_collector_update": 8,
        "episodes_per_collector_unit": 1_024, "cue_count_per_collector_update": {"0": 4, "1": 4},
        "dual_collector_phase_barrier": True, "fixed_update_order": list(b4.B4_ARMS),
        "shadow_batch_source": "RL_ORIGINAL_GENERATOR", "self_feedback_batch_source": "CREDIT_SIGN_SELF_FEEDBACK",
        "first_collector_batches_byte_identical": True, "first_oracle_successor_complete_state_identical": True,
        "complete_state_fields": [
            "actor_critic_recurrent_parameters", "optimizer", "recurrent_state", "initial_state",
            "carried_learner_state", "registered_learner_rng_state",
        ],
    }
    assert manifest["evaluation"] == {
        "episodes_per_unit_arm": 128, "cue_counts": {"0": 64, "1": 64},
        "independently_recreated_common_panels": True, "checkpoints_per_arm_unit": 1,
        "checkpoints_total": 15, "stochastic_action_draws": 0,
    }
    assert manifest["expected_activity"] == {
        "real_training_episodes": 10_240, "optimizer_updates": 1_920,
        "evaluation_episodes": 1_920, "checkpoints_total": 15,
    }
    assert manifest["caps"] == b4.B4_CAPS == {
        "environment_transitions_total": 145_348, "real_training_episodes_total": 10_240,
        "evaluation_episodes_total": 1_920, "optimizer_updates_total": 1_920,
        "checkpoints_total": 15, "result_bearing_runs": 1, "pool_units": 1,
        "cpu_minutes": 30, "peak_memory_gib": 2,
    }
    assert manifest["result_bearing_runs"] == 0
    assert manifest["retry_rescue_sweep_extra_arm_seed_checkpoint"] == 0
    assert manifest["evidence_complexity"] == {"H": 4, "K_search": 0, "hypothetical_transitions": 0}


def test_branch_precedence_and_frozen_nonclaims(manifest: dict[str, object]) -> None:
    assert b4.B4_BRANCH_PRECEDENCE == (
        "B4_INCONCLUSIVE_OR_INVALID", "B4_FEEDBACK_LOCAL_SUFFICIENCY", "B4_FEEDBACK_LOCAL_INSUFFICIENT",
    )
    zero = {"exact_correct_units": 0, "mean_j_eval": 1.0, "mean_kappa": 0.0}
    positive = {"exact_correct_units": 5, "mean_j_eval": 1.051, "mean_kappa": 0.70}
    sufficient = {"RL_ORIGINAL_GENERATOR": zero, "CREDIT_SIGN_SHADOW": zero, "CREDIT_SIGN_SELF_FEEDBACK": positive}
    insufficient = {arm: zero for arm in b4.B4_ARMS}
    assert b4.classify_b4(valid=True, aggregates=sufficient, feedback_exposure_valid=True) == "B4_FEEDBACK_LOCAL_SUFFICIENCY"
    assert b4.classify_b4(valid=True, aggregates=insufficient, feedback_exposure_valid=True) == "B4_FEEDBACK_LOCAL_INSUFFICIENT"
    assert b4.classify_b4(valid=False, aggregates=sufficient, feedback_exposure_valid=True) == "B4_INCONCLUSIVE_OR_INVALID"
    assert b4.classify_b4(valid=True, aggregates=sufficient, feedback_exposure_valid=False) == "B4_INCONCLUSIVE_OR_INVALID"
    boundary = deepcopy(sufficient)
    boundary["CREDIT_SIGN_SELF_FEEDBACK"] = {
        "exact_correct_units": 5, "mean_j_eval": math.nextafter(1.05, 1.0), "mean_kappa": 0.70,
    }
    assert b4.classify_b4(valid=True, aggregates=boundary, feedback_exposure_valid=True) == "B4_INCONCLUSIVE_OR_INVALID"
    unexpected = deepcopy(insufficient)
    unexpected["CREDIT_SIGN_SHADOW"] = {"exact_correct_units": 1, "mean_j_eval": 1.0, "mean_kappa": 0.0}
    assert b4.classify_b4(valid=True, aggregates=unexpected, feedback_exposure_valid=True) == "B4_INCONCLUSIVE_OR_INVALID"
    assert manifest["nonclaims"] == [
        "not on-policy and not established as a standard policy-gradient objective",
        "mediator differences are descendants and are not separately identified causes",
        "no general actor-critic, recurrence, optimizer, MARL, transfer, promotion, retirement, or C-level claim",
        "no B3 reinterpretation, reopening, rerun, rescue, or successor authorization",
    ]


def test_mediator_records_and_nonclaims_cannot_expand_branch_meaning(manifest: dict[str, object]) -> None:
    zero = {"exact_correct_units": 0, "mean_j_eval": 1.0, "mean_kappa": 0.0}
    aggregates = {arm: deepcopy(zero) for arm in b4.B4_ARMS}
    baseline = b4.classify_b4(valid=True, aggregates=aggregates, feedback_exposure_valid=True)
    for arm in b4.B4_ARMS:
        aggregates[arm].update({"credit_density": 999.0, "advantage_variance": -1.0, "clip_rate": 1.0})
    assert b4.classify_b4(valid=True, aggregates=aggregates, feedback_exposure_valid=True) == baseline
    assert "mediator" not in inspect.getsource(b4.classify_b4).lower()
    assert "B3" not in inspect.getsource(b4.classify_b4)
    assert "mediators are logged but never branch conditions" not in " ".join(manifest["nonclaims"])
    assert manifest["nonclaims"][1] == "mediator differences are descendants and are not separately identified causes"


def _failed_construction_result(manifest: dict[str, object], preflight: dict[str, object]) -> dict[str, object]:
    failed = deepcopy(preflight)
    failed["gates"]["P0"] = {"passed": False, "issues": ["source mismatch"]}
    failed["all_passed"] = False
    failed.pop("evidence_digest")
    failed["evidence_digest"] = b4.digest(failed)
    result = {
        "artifact_kind": "vsp02_b4_result", "assignment_id": b4.B4_ASSIGNMENT_ID,
        "direction_id": b4.B4_DIRECTION_ID, "candidate": b4.B4_CANDIDATE,
        "manifest": manifest, "manifest_identity": b4.manifest_identity(manifest), "preflight": failed,
        "branch": "B4_INCONCLUSIVE_OR_INVALID", "activity": b4._zero_activity(),
        "activity_valid": False, "feedback_exposure_valid": False,
        "resource_usage": None, "runtime_contract": None, "units": [], "aggregates": None, "evaluation": None,
    }
    result["evidence_digest"] = b4.digest(result)
    return result


def test_retained_validation_is_pure_and_source_bound(monkeypatch: pytest.MonkeyPatch, manifest: dict[str, object], preflight: dict[str, object]) -> None:
    result = _failed_construction_result(manifest, preflight)

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("retained validation invoked runtime")

    for name in ("run_treatment", "B4LifecycleHost", "_new_learners", "_optimizer_step", "_evaluate_arm_unit"):
        monkeypatch.setattr(b4, name, forbidden)
    monkeypatch.setattr(torch.optim, "Adam", forbidden)
    rng_before = torch.get_rng_state().clone()
    assert b4.validate_result(manifest, result) == ()
    assert torch.equal(torch.get_rng_state(), rng_before)
    changed = deepcopy(result)
    changed["activity"]["optimizer_updates"] = 1
    assert "retained artifact mutation or evidence digest mismatch" in b4.validate_result(manifest, changed)
    assert "run_treatment(" not in inspect.getsource(b4.validate_result)
    assert all(token not in inspect.getsource(b4.validate_preflight_evidence) for token in ("_new_learners(", "_optimizer_step(", "_evaluate_arm_unit("))


def test_resource_caps_are_branch_bearing_and_retained_recomputed_without_full(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = b4.build_manifest(source_revision="BOUND", run_id=b4.B4_RUN_ID, technical_only=False)
    monkeypatch.setattr(b4, "preflight_report", lambda *args, **kwargs: {"all_passed": True})

    def fake_train(unit_id: str, root: int) -> dict[str, object]:
        return {
            "unit_id": unit_id,
            "decimal_root": root,
            "models": {arm: object() for arm in b4.B4_ARMS},
            "training": {
                "environment_transitions": 0,
                "updates": {arm: [] for arm in b4.B4_ARMS},
                "feedback_exposure": {
                    "post_first_update_collector_parameter_divergence": True,
                    "first_oracle_successor_complete_state_identity": True,
                    "later_action_or_environment_transition_row_divergence": True,
                },
            },
        }

    def fake_evaluate(*, unit_id: str, arm: str, model: object, panel: object) -> dict[str, object]:
        return {
            "unit_id": unit_id, "arm": arm, "episodes": 128, "environment_transitions": 0,
            "exact_correct_unit": False, "j_eval": 1.0, "kappa": 0.0,
        }

    monkeypatch.setattr(b4, "_train_unit", fake_train)
    monkeypatch.setattr(b4, "_evaluate_arm_unit", fake_evaluate)
    cases = (
        (1799.0, 2 * 1024**3, True, "B4_FEEDBACK_LOCAL_INSUFFICIENT"),
        (1800.000001, 2 * 1024**3, False, "B4_INCONCLUSIVE_OR_INVALID"),
        (1799.0, 2 * 1024**3 + 1, False, "B4_INCONCLUSIVE_OR_INVALID"),
    )
    results: list[dict[str, object]] = []
    for cpu_seconds, peak_rss, expected_valid, expected_branch in cases:
        clock = iter((100.0, 100.0 + cpu_seconds))
        rss = iter((peak_rss, peak_rss))
        monkeypatch.setattr(b4, "_cpu_time_seconds", lambda clock=clock: next(clock))
        monkeypatch.setattr(b4, "_peak_process_rss_bytes", lambda rss=rss: next(rss))
        result = b4.run_treatment(manifest)
        assert result["activity_valid"] is expected_valid
        assert result["branch"] == expected_branch
        assert result["resource_usage"]["all_resource_caps_passed"] is expected_valid
        results.append(result)

    retained = deepcopy(results[0]["resource_usage"])
    retained["cpu_minutes"] = 0.0
    recomputed = b4._resource_usage_evidence(
        cpu_start_seconds=float(retained["cpu_start_seconds"]),
        cpu_end_seconds=float(retained["cpu_end_seconds"]),
        peak_rss_samples_bytes=retained["peak_process_rss_samples_bytes"],
    )
    assert retained != recomputed
    assert recomputed["cpu_within_cap"] is True and recomputed["peak_memory_within_cap"] is True
    validation_source = inspect.getsource(b4.validate_result)
    assert "derived_resource_usage = _resource_usage_evidence(" in validation_source
    assert 'resource_usage != derived_resource_usage' in validation_source
    assert "and resource_caps_passed" in validation_source


def test_retained_evaluation_rows_recompute_every_projection_and_common_panel() -> None:
    unit_id, root = b4.B4_UNITS[0]
    models, _ = b4._new_learners(unit_id, root)
    panel = b4._evaluation_panel(unit_id, root)
    metric = b4._evaluate_arm_unit(
        unit_id=unit_id, arm="RL_ORIGINAL_GENERATOR",
        model=models["RL_ORIGINAL_GENERATOR"], panel=panel,
    )
    derived, issues, transitions, panel_digest, clone_ids = b4._derive_retained_evaluation_metric(
        unit_id=unit_id, root=root, arm="RL_ORIGINAL_GENERATOR", metric=metric,
        expected_final_hash=metric["final_model_hash"],
    )
    assert issues == [] and derived is not None
    assert transitions == sum(row["environment_transitions"] for row in metric["clone_records"])
    assert panel_digest == b4.digest(panel)
    assert len(clone_ids) == 128
    for key in (
        "argmax_ties", "cue_counts", "q_0", "q_1", "j_eval", "kappa",
        "exact_correct_unit", "environment_transitions", "panel_digest",
    ):
        changed = deepcopy(metric)
        value = changed[key]
        changed[key] = (not value) if isinstance(value, bool) else value + 1 if isinstance(value, (int, float)) else "tampered"
        _, changed_issues, _, _, _ = b4._derive_retained_evaluation_metric(
            unit_id=unit_id, root=root, arm="RL_ORIGINAL_GENERATOR", metric=changed,
            expected_final_hash=metric["final_model_hash"],
        )
        assert any(f"{key} projection mismatch" in issue for issue in changed_issues), key

    choice_changed = deepcopy(metric)
    choice_changed["clone_records"][0]["argmax_action"] = "NOT_THE_DERIVED_CHOICE"
    _, choice_issues, _, _, _ = b4._derive_retained_evaluation_metric(
        unit_id=unit_id, root=root, arm="RL_ORIGINAL_GENERATOR", metric=choice_changed,
        expected_final_hash=metric["final_model_hash"],
    )
    assert any("deterministic argmax mismatch" in issue for issue in choice_issues)

    cue_changed = deepcopy(metric)
    cue_changed["clone_records"][0]["true_cue"] = 1 - cue_changed["clone_records"][0]["true_cue"]
    _, cue_issues, _, _, _ = b4._derive_retained_evaluation_metric(
        unit_id=unit_id, root=root, arm="RL_ORIGINAL_GENERATOR", metric=cue_changed,
        expected_final_hash=metric["final_model_hash"],
    )
    assert any("evaluation row identity mismatch" in issue or "evaluation cue/row support mismatch" in issue for issue in cue_issues)

    common_digests: list[str] = []
    for arm in b4.B4_ARMS:
        arm_metric = deepcopy(metric)
        arm_metric["arm"] = arm
        arm_metric["checkpoint_id"] = f"{b4.B4_ASSIGNMENT_ID}/{unit_id}/{arm}/FINAL-128"
        _, arm_issues, _, arm_digest, _ = b4._derive_retained_evaluation_metric(
            unit_id=unit_id, root=root, arm=arm, metric=arm_metric,
            expected_final_hash=metric["final_model_hash"],
        )
        assert arm_issues == []
        common_digests.append(str(arm_digest))
    assert len(set(common_digests)) == 1
    noncommon = deepcopy(metric)
    noncommon["clone_records"][0]["clone_id"] = "TAMPERED-EVALUATION-CLONE"
    _, panel_issues, _, noncommon_digest, _ = b4._derive_retained_evaluation_metric(
        unit_id=unit_id, root=root, arm="RL_ORIGINAL_GENERATOR", metric=noncommon,
        expected_final_hash=metric["final_model_hash"],
    )
    assert panel_issues and noncommon_digest != common_digests[0]


def test_runner_is_write_once_source_bound_and_exclusive(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, manifest: dict[str, object]
) -> None:
    temporary = TemporaryDirectory(prefix="vsp02_b4_test_")
    request.addfinalizer(temporary.cleanup)
    tmp_path = Path(temporary.name)
    assert set(runner._parser()._subparsers._group_actions[0].choices) == {"manifest", "technical-proof", "registered-full", "validate"}
    runner._require_frozen_handoff()
    assert runner.FROZEN_HANDOFF_SHA256 == b4.B4_FREEZE_HANDOFF_SHA256
    assert runner.FROZEN_PUBLICATION_COMMIT == b4.B4_FREEZE_PUBLICATION_COMMIT == "de5f2427662de2dc28fe20793086c0763d725018"
    assert runner._require_root(runner.CANONICAL_RUN_ROOT) == runner.CANONICAL_RUN_ROOT
    with pytest.raises(ValueError, match="canonical assignment root"):
        runner._require_root(tmp_path / "sibling")
    with pytest.raises(ValueError, match="canonical assignment root"):
        runner._require_root(runner.CANONICAL_RUN_ROOT / "nested")
    artifact = tmp_path / "artifact.json"
    runner._write_once(artifact, {"value": 1})
    with pytest.raises(FileExistsError):
        runner._write_once(artifact, {"value": 2})
    claim = tmp_path / "claim.json"
    runner._exclusive_claim(claim, {"result_bearing_runs": 1})
    with pytest.raises(FileExistsError):
        runner._exclusive_claim(claim, {})
    monkeypatch.setattr(runner, "_source_revision", lambda: "BOUND")
    bound = b4.build_manifest(source_revision="BOUND", run_id="proof", technical_only=True)
    assert runner._require_bound_manifest(bound) == bound
    with pytest.raises(ValueError, match="source_revision"):
        runner._require_bound_manifest(manifest)

    runtime_paths = b4.B4_CLAIM_PATHS + b4.B4_DEPENDENCY_PATHS
    assert b4.B4_RUNTIME_PATHS == runtime_paths
    dirty_dependency = b4.B4_DEPENDENCY_PATHS[0]

    def fake_git(*arguments: str) -> str:
        if arguments[0] == "ls-files":
            assert tuple(arguments[2:]) == runtime_paths
            return "\n".join(runtime_paths)
        if arguments[0] == "status":
            assert tuple(arguments[4:]) == runtime_paths
            return f" M {dirty_dependency}"
        raise AssertionError(f"unexpected Git query: {arguments}")

    monkeypatch.setattr(runner, "_git", fake_git)
    with pytest.raises(ValueError, match="runtime dependency sources differ from HEAD"):
        runner._require_clean_claim_sources()

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        arguments = command[1:]
        if arguments == ["rev-parse", "HEAD"]:
            return SimpleNamespace(stdout="BOUND\n", returncode=0)
        if arguments[:2] == ["ls-files", "--"]:
            assert tuple(arguments[2:]) == runtime_paths
            return SimpleNamespace(stdout="\n".join(runtime_paths) + "\n", returncode=0)
        if arguments[:4] == ["status", "--porcelain=v1", "--untracked-files=all", "--"]:
            assert tuple(arguments[4:]) == runtime_paths
            return SimpleNamespace(stdout=f" M {dirty_dependency}\n", returncode=0)
        if arguments == ["cat-file", "-t", b4.B4_FREEZE_PUBLICATION_COMMIT]:
            return SimpleNamespace(stdout="commit\n", returncode=0)
        if arguments[:3] == ["merge-base", "--is-ancestor", b4.B4_IMPLEMENTATION_BASE]:
            assert arguments[3] == "BOUND"
            return SimpleNamespace(stdout="", returncode=0)
        if arguments[:3] == ["merge-base", "--is-ancestor", b4.B4_FREEZE_PUBLICATION_COMMIT]:
            assert arguments[3] == "BOUND"
            return SimpleNamespace(stdout="", returncode=0)
        raise AssertionError(f"unexpected Git subprocess: {arguments}")

    monkeypatch.setattr(b4.subprocess, "run", fake_run)
    assert "B4 claim or runtime dependency paths differ from HEAD" in b4._git_binding(Path.cwd(), "BOUND")
    source = inspect.getsource(runner._registered_full_command)
    assert source.count("run_treatment(") == 1
    assert source.index("_exclusive_claim") < source.index("run_treatment(")
    assert '"retry_rescue_sweep_extra_arm_seed_checkpoint": 0' in source
    assert "while " not in source and "except " not in source
    assert inspect.getsource(runner._technical_proof_command).count("run_treatment(") == 0


def test_runner_preflight_precedes_claim_and_failed_preflight_consumes_nothing(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest,
) -> None:
    temporary = TemporaryDirectory(prefix="vsp02_b4_runner_order_")
    request.addfinalizer(temporary.cleanup)
    root = Path(temporary.name).resolve()
    manifest_path = (root / runner.MANIFEST_NAME).resolve()
    manifest = b4.build_manifest(source_revision="BOUND", run_id=b4.B4_RUN_ID, technical_only=False)
    args = SimpleNamespace(manifest=manifest_path, run_root=root)
    events: list[str] = []

    monkeypatch.setattr(runner, "_require_frozen_handoff", lambda: None)
    monkeypatch.setattr(runner, "_require_root", lambda path: root)
    monkeypatch.setattr(runner, "_read_json", lambda path: manifest)
    monkeypatch.setattr(runner, "_require_bound_manifest", lambda payload: manifest)
    monkeypatch.setattr(runner, "_require_clean_claim_sources", lambda: None)
    monkeypatch.setattr(runner, "_require_publication_ancestry", lambda: None)

    def failed_preflight(*args: object, **kwargs: object) -> dict[str, object]:
        events.append("preflight")
        return {"all_passed": False}

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("failed preflight reached claim/run/write surface")

    monkeypatch.setattr(runner, "preflight_report", failed_preflight)
    monkeypatch.setattr(runner, "_exclusive_claim", forbidden)
    monkeypatch.setattr(runner, "run_treatment", forbidden)
    monkeypatch.setattr(runner, "_write_once", forbidden)
    with pytest.raises(ValueError, match="preflight failed before sole claim creation"):
        runner._registered_full_command(args)
    assert events == ["preflight"]
    assert not (root / runner.CLAIM_NAME).exists()
    assert not (root / runner.RESULT_NAME).exists()

    events.clear()

    def passed_preflight(*args: object, **kwargs: object) -> dict[str, object]:
        events.append("preflight")
        return {"all_passed": True}

    def claim(path: Path, payload: object) -> None:
        events.append("claim")

    def run(payload: object, **kwargs: object) -> dict[str, object]:
        events.append("run")
        return {"synthetic": True}

    def validate(*args: object, **kwargs: object) -> tuple[str, ...]:
        events.append("validate")
        return ()

    def write(path: Path, payload: object) -> None:
        events.append("write")

    monkeypatch.setattr(runner, "preflight_report", passed_preflight)
    monkeypatch.setattr(runner, "_exclusive_claim", claim)
    monkeypatch.setattr(runner, "run_treatment", run)
    monkeypatch.setattr(runner, "validate_result", validate)
    monkeypatch.setattr(runner, "_write_once", write)
    assert runner._registered_full_command(args) == 0
    assert events == ["preflight", "claim", "run", "validate", "write"]
    assert events.count("run") == 1

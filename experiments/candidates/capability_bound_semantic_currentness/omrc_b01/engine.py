"""Source-bound B0 recurrent-PPO engine for CBSC-OMRC-B01."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import time
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import torch

from . import addressing
from .adapters import (
    AdapterWorkReceipt,
    DerangedCurrentnessAdapter,
    PredictiveIndexAdapter,
    RawHistoryAdapter,
    StructCurrentnessAdapter,
)
from .artifact import B0_RUN_NAME
from .b0 import (
    ARMS,
    B0ArmRequest,
    B0ContractError,
    CHECKPOINT_IDENTITIES,
)
from .checkpoint import (
    capture_checkpoint,
    load_checkpoint,
    model_parameter_digest_from_state,
    restore_checkpoint,
    save_checkpoint,
)
from .contract import Action, EPISODE_TRANSITIONS, OPPORTUNITY_COUNT
from .host import DynamicHost
from .model import (
    INPUT_DIM,
    WAIT,
    CommonRecurrentActorCritic,
    greedy_action,
    masked_action,
    model_parameter_digest,
)
from .ppo import EpisodeRollout, RecurrentPPOTrainer, make_adam
from .tapes import EpisodeTape, build_b0_panel


AdapterFactory = Callable[[], Any]
_ADAPTERS: dict[str, AdapterFactory] = {
    "STRUCT-CURRENTNESS-GRU": StructCurrentnessAdapter,
    "RAW-GRU": RawHistoryAdapter,
    "PI-GRU": PredictiveIndexAdapter,
    "DERANGED-CURRENTNESS-GRU": DerangedCurrentnessAdapter,
}


def _json_digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _tape_primitive_digest(tapes: Sequence[EpisodeTape]) -> str:
    return _json_digest(
        [
            {
                "identity": vars(tape.identity),
                "primitive_digest": tape.primitive_digest,
            }
            for tape in tapes
        ]
    )


def _add_work(left: AdapterWorkReceipt, right: AdapterWorkReceipt) -> AdapterWorkReceipt:
    return left + right


def build_observations(
    tape: EpisodeTape, adapter_factory: AdapterFactory
) -> tuple[torch.Tensor, AdapterWorkReceipt]:
    """Project one tape using public bytes only and one fresh episode adapter."""

    adapter = adapter_factory()
    primitive = tape.learner_tokens()
    emissions = adapter.replay(tape.public_tokens)
    if len(primitive) != EPISODE_TRANSITIONS or len(emissions) != EPISODE_TRANSITIONS:
        raise B0ContractError("episode projection count differs from 152")
    rows = np.empty((EPISODE_TRANSITIONS, INPUT_DIM), dtype=np.float32)
    for index, (public, emission) in enumerate(zip(primitive, emissions, strict=True)):
        rows[index, :136] = public.float32_channels()
        rows[index, 136:] = emission.float32_channels()
    if not np.isfinite(rows).all():
        raise B0ContractError("learner observation contains nonfinite channels")
    return torch.from_numpy(rows), adapter.total_work


def _project_panel(
    tapes: Sequence[EpisodeTape], adapter_factory: AdapterFactory
) -> tuple[torch.Tensor, AdapterWorkReceipt]:
    observations: list[torch.Tensor] = []
    total = AdapterWorkReceipt()
    for tape in tapes:
        projected, work = build_observations(tape, adapter_factory)
        replayed, replay_work = build_observations(tape, adapter_factory)
        if not torch.equal(projected, replayed) or work != replay_work:
            raise B0ContractError("literal adapter replay is not deterministic")
        observations.append(projected)
        total = _add_work(total, work)
    return torch.stack(observations), total


def _decision_mask(episode_count: int) -> torch.Tensor:
    mask = torch.zeros((episode_count, EPISODE_TRANSITIONS), dtype=torch.bool)
    mask[:, 12::6] = True
    return mask


def decision_action_traces(
    tapes: Sequence[EpisodeTape], actions: torch.Tensor
) -> list[dict[str, Any]]:
    """Return identity-bound decision actions without evaluator truth or conclusions."""

    expected_shape = (len(tapes), EPISODE_TRANSITIONS)
    if actions.shape != expected_shape or actions.dtype != torch.int64:
        raise B0ContractError(
            f"action trace must have shape {expected_shape} and dtype int64"
        )
    traces: list[dict[str, Any]] = []
    for episode_index, tape in enumerate(tapes):
        names: list[str] = []
        for opportunity in range(OPPORTUNITY_COUNT):
            row = 12 + 6 * opportunity
            try:
                action = Action(int(actions[episode_index, row].item()))
            except ValueError as exc:
                raise B0ContractError("decision action is outside the frozen action set") from exc
            if action is Action.WAIT:
                raise B0ContractError("decision action trace contains illegal WAIT")
            names.append(action.name)
        traces.append(
            {
                "identity": asdict(tape.identity),
                "decision_actions": names,
            }
        )
    return traces


def reward_row_evidence(
    tapes: Sequence[EpisodeTape], rewards: torch.Tensor
) -> list[dict[str, Any]]:
    """Record every decision/settlement reward and any nonzero outside row."""

    expected_shape = (len(tapes), EPISODE_TRANSITIONS)
    if rewards.shape != expected_shape or rewards.dtype != torch.float32:
        raise B0ContractError(
            f"reward evidence must have shape {expected_shape} and dtype float32"
        )
    if not torch.isfinite(rewards).all().item():
        raise B0ContractError("reward evidence contains nonfinite values")
    allowed = torch.zeros(expected_shape, dtype=torch.bool, device=rewards.device)
    allowed[:, 12::6] = True
    allowed[:, 13::6] = True
    evidence: list[dict[str, Any]] = []
    for episode_index, tape in enumerate(tapes):
        outside = torch.nonzero(
            (rewards[episode_index] != 0) & ~allowed[episode_index], as_tuple=False
        ).flatten()
        evidence.append(
            {
                "identity": asdict(tape.identity),
                "decision_rewards": [
                    float(rewards[episode_index, 12 + 6 * opportunity].item())
                    for opportunity in range(OPPORTUNITY_COUNT)
                ],
                "settlement_rewards": [
                    float(rewards[episode_index, 13 + 6 * opportunity].item())
                    for opportunity in range(OPPORTUNITY_COUNT)
                ],
                "nonzero_outside_ledger_rows": [int(row.item()) for row in outside],
            }
        )
    return evidence


def assert_unchanged_state(before: str, after: str, *, label: str) -> None:
    """Refuse a held-out pass that mutates a persistent model/optimizer digest."""

    if not before or not after or before != after:
        raise B0ContractError(f"held-out evaluation changed {label} state")


def _training_action_uniforms(
    tapes: Sequence[EpisodeTape], run_name: str, seed: int
) -> tuple[torch.Tensor, str, list[dict[str, Any]]]:
    values: list[float] = []
    records: list[dict[str, Any]] = []
    for tape in tapes:
        for opportunity in range(OPPORTUNITY_COUNT):
            address = addressing.action_address(
                run_name, seed, tape.identity.episode_id, opportunity
            )
            raw = addressing.u64(address)
            values.append((raw + 0.5) / float(1 << 64))
            records.append(
                {
                    "episode_id": tape.identity.episode_id,
                    "opportunity_index": opportunity,
                    "address": list(address),
                    "u64": raw,
                }
            )
    return torch.tensor(values, dtype=torch.float64), _json_digest(records), records


def _rollout_from_panel(
    tapes: Sequence[EpisodeTape],
    observations: torch.Tensor,
    model: CommonRecurrentActorCritic,
    *,
    run_name: str,
    seed: int,
) -> tuple[EpisodeRollout, dict[str, Any], str]:
    decisions = _decision_mask(len(tapes))
    uniforms, uniform_digest, uniform_records = _training_action_uniforms(
        tapes, run_name, seed
    )
    with torch.no_grad():
        sequence = model.forward_episode(observations)
        selection = masked_action(
            sequence.logits.reshape(-1, 4),
            decisions.reshape(-1),
            uniforms=uniforms,
        )
    actions = selection.actions.reshape(len(tapes), EPISODE_TRANSITIONS)
    old_log_probabilities = selection.log_probabilities.reshape(
        len(tapes), EPISODE_TRANSITIONS
    )
    consumed = selection.consumed_uniform.reshape(len(tapes), EPISODE_TRANSITIONS)
    if not torch.equal(consumed, decisions):
        raise B0ContractError("action uniforms were not consumed at exactly the decision rows")
    if not torch.all(actions[~decisions] == WAIT).item():
        raise B0ContractError("forced WAIT path was not preserved")
    rewards = torch.zeros((len(tapes), EPISODE_TRANSITIONS), dtype=torch.float32)
    for episode_index, tape in enumerate(tapes):
        evaluator = tape.evaluator()
        for opportunity in range(OPPORTUNITY_COUNT):
            row = 12 + 6 * opportunity
            action = Action(int(actions[episode_index, row].item()))
            ledger = evaluator.ledger(opportunity, action)
            rewards[episode_index, row] = float(ledger.decision_reward)
            rewards[episode_index, row + 1] = float(ledger.settlement_reward)
    reward_evidence = reward_row_evidence(tapes, rewards)
    if any(record["nonzero_outside_ledger_rows"] for record in reward_evidence):
        raise B0ContractError("native ledger reward escaped decision/settlement rows")
    terminated = torch.zeros((len(tapes), EPISODE_TRANSITIONS), dtype=torch.bool)
    terminated[:, -1] = True
    rollout = EpisodeRollout(
        observations=observations,
        actions=actions,
        rewards=rewards,
        terminated=terminated,
        decision_mask=decisions,
        old_log_probabilities=old_log_probabilities,
        old_values=sequence.values.detach().clone(),
        episode_ids=torch.tensor(
            [tape.identity.episode_id for tape in tapes], dtype=torch.int64
        ),
    )
    observations_record = {
        "observation_shape": list(observations.shape),
        "actions": decision_action_traces(tapes, actions),
        "uniforms": uniform_records,
        "uniforms_consumed_rows": [
            [int(row.item()) for row in torch.nonzero(consumed[index], as_tuple=False).flatten()]
            for index in range(len(tapes))
        ],
        "forced_wait_rows": [
            [
                int(row.item())
                for row in torch.nonzero(actions[index] == WAIT, as_tuple=False).flatten()
            ]
            for index in range(len(tapes))
        ],
        "rewards": reward_evidence,
        "terminated_rows": [
            [int(row.item()) for row in torch.nonzero(terminated[index], as_tuple=False).flatten()]
            for index in range(len(tapes))
        ],
    }
    return rollout, observations_record, uniform_digest


def _optimizer_digest(trainer: RecurrentPPOTrainer) -> str:
    digest = hashlib.sha256()
    state = trainer.optimizer.state_dict()
    digest.update(_json_digest(state["param_groups"]).encode("ascii"))
    for key in sorted(state["state"]):
        digest.update(str(key).encode("ascii"))
        for name in sorted(state["state"][key]):
            value = state["state"][key][name]
            digest.update(name.encode("utf-8"))
            if isinstance(value, torch.Tensor):
                array = value.detach().cpu().contiguous().numpy()
                digest.update(str(array.dtype).encode("ascii"))
                digest.update(json.dumps(list(array.shape)).encode("ascii"))
                digest.update(array.tobytes())
            else:
                digest.update(repr(value).encode("utf-8"))
    return digest.hexdigest()


def _checkpoint_roundtrip(
    paths: Sequence[Path],
    *,
    arm: str,
    seed: int,
    tape_digest: str,
    action_digest: str,
) -> dict[str, Any]:
    verifier_model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
    verifier = RecurrentPPOTrainer(
        verifier_model,
        run_name=B0_RUN_NAME,
        seed=seed,
        optimizer=make_adam(verifier_model),
        address_u64=addressing.u64,
    )
    records: dict[str, Any] = {}
    for path in paths:
        before = path.read_bytes()
        payload = load_checkpoint(path)
        if path.read_bytes() != before:
            raise B0ContractError("checkpoint bytes changed while loading")
        restore_checkpoint(
            payload,
            verifier,
            expected_arm=arm,
            expected_training_tape_digest=tape_digest,
            expected_action_uniform_digest=action_digest,
        )
        expected_model = model_parameter_digest_from_state(payload["model_state"])
        if model_parameter_digest(verifier_model) != expected_model:
            raise B0ContractError("checkpoint model bytes changed during roundtrip")
        identity = dict(payload["identity"])
        checkpoint_id = f"update-{identity['completed_rollout_updates']}"
        records[checkpoint_id] = {
            "relative_path": path.name,
            "byte_count": len(before),
            "loaded_identity": identity,
            "loaded_counters": dict(payload["counters"]),
            "loaded_digests": dict(payload["digests"]),
            "loaded_model_parameter_digest": expected_model,
            "restored_model_parameter_digest": model_parameter_digest(verifier_model),
            "restored_optimizer_digest": _optimizer_digest(verifier),
        }
    if set(records) != set(CHECKPOINT_IDENTITIES):
        raise B0ContractError("checkpoint roundtrip identities differ from B0")
    return records


def _evaluate_heldout(
    tapes: Sequence[EpisodeTape],
    observations: torch.Tensor,
    model: CommonRecurrentActorCritic,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    before_model = model_parameter_digest(model)
    was_training = model.training
    consumed_uniform_rows: list[int] = []
    try:
        model.eval()
        with torch.no_grad():
            sequence = model.forward_episode(observations)
            decisions = _decision_mask(len(tapes))
            selection = greedy_action(
                sequence.logits.reshape(-1, 4), decisions.reshape(-1)
            )
        chosen = selection.actions.reshape(len(tapes), EPISODE_TRANSITIONS)
        consumed_uniform_rows = [
            int(row.item())
            for row in torch.nonzero(selection.consumed_uniform, as_tuple=False).flatten()
        ]
        if consumed_uniform_rows:
            raise B0ContractError("adaptation-free evaluation consumed an action uniform")
    finally:
        model.train(was_training)
    after_model = model_parameter_digest(model)
    assert_unchanged_state(before_model, after_model, label="model")
    return decision_action_traces(tapes, chosen), {
        "model_digest_before": before_model,
        "model_digest_after": after_model,
        "training_mode_before": was_training,
        "training_mode_after": model.training,
        "consumed_uniform_rows": consumed_uniform_rows,
    }


class LiteralB0Engine:
    """One-process, one-thread actual B0 environment/learner/evaluator engine."""

    worker_count = 1
    threads_per_worker = 1
    source_paths = (
        "docs/research/candidates/capability_bound_semantic_currentness/DIRECTION.md",
        "docs/research/candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_CM_IMPLEMENTATION_CONTRACT.md",
        "docs/research/candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_LITERAL_BINDING_SPEC.md",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/__init__.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/addressing.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/adapters.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/artifact.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b0.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/checkpoint.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/contract.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/engine.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/evaluator.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/host.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/ledger.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/model.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/ppo.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/state.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/tapes.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/telemetry.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/token.py",
        "scripts/run_cbsc_omrc_b01.py",
    )

    def run_arm(self, request: B0ArmRequest) -> Mapping[str, Any]:
        request.plan.validate()
        if (
            request.arm not in ARMS
            or request.seed != request.plan.seed
            or request.train_episode_ids != request.plan.train_episode_ids
            or request.eval_stochastic_ids != request.plan.eval_stochastic_ids
            or request.eval_motif_ids != request.plan.eval_motif_ids
        ):
            raise B0ContractError("B0 arm request differs from the frozen literal plan")
        if not request.admission_receipt_path.is_file():
            raise B0ContractError("arm-specific memory admission receipt is absent")
        adapter_factory = _ADAPTERS[request.arm]
        request.durable_root.mkdir(parents=True, exist_ok=True)
        original_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        try:
            host = DynamicHost(request.plan.run_name, request.seed)
            panel = build_b0_panel(host)
            train_start_wall = time.perf_counter()
            train_start_cpu = time.process_time()
            model = CommonRecurrentActorCritic(request.seed, address_u64=addressing.u64)
            optimizer = make_adam(model)
            trainer = RecurrentPPOTrainer(
                model,
                run_name=request.plan.run_name,
                seed=request.seed,
                optimizer=optimizer,
                address_u64=addressing.u64,
            )
            initial_parameter_digest = model_parameter_digest(model)
            train_observations, train_work = _project_panel(panel.train, adapter_factory)
            rollout, rollout_evidence, action_digest = _rollout_from_panel(
                panel.train,
                train_observations,
                model,
                run_name=request.plan.run_name,
                seed=request.seed,
            )
            training_tape_digest = _tape_primitive_digest(panel.train)
            checkpoint_zero = capture_checkpoint(
                trainer,
                arm=request.arm,
                training_tape_digest=training_tape_digest,
                action_uniform_digest=action_digest,
            )
            checkpoint_zero_path = request.durable_root / "update-0.pt"
            save_checkpoint(checkpoint_zero_path, checkpoint_zero)
            losses = trainer.train_rollout(rollout)
            if trainer.counters.adam_steps != 16 or len(losses) != 16:
                raise B0ContractError("B0 did not execute exactly 16 Adam steps")
            trained_parameter_digest = model_parameter_digest(model)
            if trained_parameter_digest == initial_parameter_digest:
                raise B0ContractError("B0 optimizer steps left all parameter bytes unchanged")
            checkpoint_one = capture_checkpoint(
                trainer,
                arm=request.arm,
                training_tape_digest=training_tape_digest,
                action_uniform_digest=action_digest,
            )
            checkpoint_one_path = request.durable_root / "update-1.pt"
            save_checkpoint(checkpoint_one_path, checkpoint_one)
            train_wall = time.perf_counter() - train_start_wall
            train_cpu = time.process_time() - train_start_cpu

            eval_start_wall = time.perf_counter()
            eval_start_cpu = time.process_time()
            heldout = (*panel.eval_stochastic, *panel.eval_motif)
            eval_observations, eval_work = _project_panel(heldout, adapter_factory)
            optimizer_before = _optimizer_digest(trainer)
            evaluation_actions, heldout_state = _evaluate_heldout(
                heldout, eval_observations, model
            )
            optimizer_after = _optimizer_digest(trainer)
            assert_unchanged_state(
                optimizer_before, optimizer_after, label="optimizer"
            )
            checkpoint_records = _checkpoint_roundtrip(
                (checkpoint_zero_path, checkpoint_one_path),
                arm=request.arm,
                seed=request.seed,
                tape_digest=training_tape_digest,
                action_digest=action_digest,
            )
            eval_wall = time.perf_counter() - eval_start_wall
            eval_cpu = time.process_time() - eval_start_cpu

            total_work = _add_work(train_work, eval_work)
            train_transitions = sum(tape.transition_count for tape in panel.train)
            evaluation_transitions = sum(tape.transition_count for tape in heldout)
            stage_measurements = [
                {
                    "stage": "train",
                    "wall_seconds": train_wall,
                    "cpu_seconds": train_cpu,
                    "transitions": train_transitions,
                    "transitions_per_second": train_transitions / train_wall,
                },
                {
                    "stage": "evaluate",
                    "wall_seconds": eval_wall,
                    "cpu_seconds": eval_cpu,
                    "transitions": evaluation_transitions,
                    "transitions_per_second": evaluation_transitions / eval_wall,
                },
            ]
            ppo_epochs = len({loss.ppo_epoch for loss in losses})
            minibatches_per_epoch = len({loss.minibatch for loss in losses})
            actual_counts = {
                "train_episodes": trainer.counters.train_episodes,
                "train_transitions": trainer.counters.train_transitions,
                "train_decisions": trainer.counters.train_decisions,
                "rollout_updates": trainer.counters.rollout_updates,
                "ppo_epochs": ppo_epochs,
                "minibatches_per_epoch": minibatches_per_epoch,
                "optimizer_steps": trainer.counters.adam_steps,
                "evaluation_episodes": len(heldout),
                "evaluation_transitions": evaluation_transitions,
                "evaluation_decisions": sum(tape.decision_count for tape in heldout),
            }
            trainer_observations = {
                "counters": asdict(trainer.counters),
                "initial_model_parameter_digest": initial_parameter_digest,
                "trained_model_parameter_digest": trained_parameter_digest,
                "minibatch_order_digest": trainer.minibatch_order_digest,
                "losses": [asdict(loss) for loss in losses],
            }
            records = {
                "train_tapes": [
                    {
                        "identity": asdict(tape.identity),
                        "primitive_digest_observed": tape.primitive_digest,
                        "draw_digest_observed": tape.generation_audit.draw_digest,
                        "draw_count_observed": tape.generation_audit.draw_count,
                    }
                    for tape in panel.train
                ],
                "evaluation_tapes": [
                    {
                        "identity": asdict(tape.identity),
                        "primitive_digest_observed": tape.primitive_digest,
                        "draw_digest_observed": tape.generation_audit.draw_digest,
                        "draw_count_observed": tape.generation_audit.draw_count,
                    }
                    for tape in heldout
                ],
                "rollout_observations": rollout_evidence,
                "training_actions": rollout_evidence["actions"],
                "trainer_observations": trainer_observations,
                "checkpoints": checkpoint_records,
                "evaluation_actions": evaluation_actions,
                "heldout_state_observations": {
                    **heldout_state,
                    "optimizer_digest_before": optimizer_before,
                    "optimizer_digest_after": optimizer_after,
                },
                "adapter_work_receipt": asdict(total_work),
                "checkpoint_binding_observations": {
                    "training_tape_digest": training_tape_digest,
                    "action_uniform_digest": action_digest,
                },
            }
            result = {
                "engine_evidence_schema": "cbsc_omrc_b01_engine_raw_evidence_v1",
                "arm": request.arm,
                "seed": request.seed,
                "run_name": request.plan.run_name,
                "counts": actual_counts,
                "checkpoint_identities": list(checkpoint_records),
                "scientific_branch": None,
                "stage_measurements": stage_measurements,
                "worker_count": self.worker_count,
                "threads_per_worker": self.threads_per_worker,
                "records": records,
            }
            return result
        finally:
            torch.set_num_threads(original_threads)


def b0_engine() -> LiteralB0Engine:
    """Factory used by the B0 CLI's ``module:factory`` binding."""

    return LiteralB0Engine()


__all__ = [
    "LiteralB0Engine",
    "assert_unchanged_state",
    "b0_engine",
    "build_observations",
    "decision_action_traces",
    "reward_row_evidence",
]

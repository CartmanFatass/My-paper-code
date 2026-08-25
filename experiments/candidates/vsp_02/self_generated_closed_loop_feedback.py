"""VSP02-B4 self-generated closed-loop feedback discriminator.

This module keeps the B3 learner, host, behavior-mixture, loss, optimizer, and
evaluation semantics fixed while changing exactly one edge: the parameter
source for future oracle-sign training batches.  It is deliberately not
described as on-policy.  Every exogenous value is a pure function of a tape
address; no collector shares or advances a mutable RNG.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Mapping, Sequence

import torch
from torch import Tensor

from experiments.candidates.vsp_02 import learned_cue_conditioned_lifecycle_control_v2 as b1
from experiments.candidates.vsp_02 import vsp02_b2_paired_shadow_learner_localization as b2
from experiments.candidates.vsp_02 import vsp02_b3_lifecycle_credit_sign_bridge as b3


B4_SCHEMA_VERSION = 1
B4_ASSIGNMENT_ID = "VSP02-B4-SELF-GENERATED-CLOSED-LOOP-FEEDBACK"
B4_RUN_ID = "VSP02-B4-REGISTERED-FULL-01"
B4_CANDIDATE = "CAND-VSP-02@adversarial-revision-v8"
B4_DIRECTION_ID = "CAND-VSP-02"
B4_HOST_ID = "VSP02-A2-PHYSICAL-LIFECYCLE-HOST-v1"
B4_RESOURCE_CLASS = "B_TOY_LIGHT"
B4_POOL_UNITS = 1
B4_IMPLEMENTATION_BASE = "6ab21eff68cce343da8ce57f0400faac7e685aa7"
B4_FREEZE_HANDOFF_SHA256 = "bd9aac55ec4f8aaa8adb88f8d20f3dc2fb2f45e7a0e17d01d7ef23caf63ac245"
B4_FREEZE_PUBLICATION_COMMIT = "de5f2427662de2dc28fe20793086c0763d725018"
B4_CANONICAL_RUN_ROOT = "temp/sessions/code_project_manager/vsp02_b4_self_generated_closed_loop_feedback/"
B4_OPERATOR_RECEIPT = "temp/sessions/code_project_manager/vsp02_b4_operator_receipt.json"
B4_PHYSICAL_TAPE_PREFIX = f"{B4_ASSIGNMENT_ID}/PHYSICAL"
B4_SEED_PREFIX = "VSP02-B4-V1\0"
B4_UNITS = tuple((f"VSP02-B4-U{index:02d}", 22_040_000 + index) for index in range(1, 6))
B4_ARMS = (
    "RL_ORIGINAL_GENERATOR",
    "CREDIT_SIGN_SHADOW",
    "CREDIT_SIGN_SELF_FEEDBACK",
)
B4_COLLECTORS = ("RL_ORIGINAL_GENERATOR", "CREDIT_SIGN_SELF_FEEDBACK")
B4_UPDATES_PER_UNIT = 128
B4_BATCH_SIZE = 8
B4_TRAIN_EPISODES_PER_COLLECTOR_UNIT = 1_024
B4_EVAL_EPISODES_PER_UNIT_ARM = 128
B4_TAPE_KINDS = (
    "cue_schedule",
    "environment_randomness",
    "behavior_mixture_coin",
    "sampling_uniform",
    "minibatch_order",
    "evaluation_cue_schedule",
    "evaluation_environment_randomness",
)
B4_SEED_STREAMS = (
    "parameter_initialization",
    "optimizer_initialization",
    "training_address_tape",
    "learner_stochasticity",
    "minibatch_order",
    "evaluation_address_tape",
)
B4_TAPE_STREAM_BY_KIND = {
    "cue_schedule": "training_address_tape",
    "environment_randomness": "training_address_tape",
    "behavior_mixture_coin": "training_address_tape",
    "sampling_uniform": "training_address_tape",
    "minibatch_order": "minibatch_order",
    "evaluation_cue_schedule": "evaluation_address_tape",
    "evaluation_environment_randomness": "evaluation_address_tape",
}
B4_BRANCH_PRECEDENCE = (
    "B4_INCONCLUSIVE_OR_INVALID",
    "B4_FEEDBACK_LOCAL_SUFFICIENCY",
    "B4_FEEDBACK_LOCAL_INSUFFICIENT",
)
B4_CAPS = {
    "environment_transitions_total": 145_348,
    "real_training_episodes_total": 10_240,
    "evaluation_episodes_total": 1_920,
    "optimizer_updates_total": 1_920,
    "checkpoints_total": 15,
    "result_bearing_runs": 1,
    "pool_units": 1,
    "cpu_minutes": 30,
    "peak_memory_gib": 2,
}
B4_CLAIM_PATHS = (
    "experiments/candidates/vsp_02/self_generated_closed_loop_feedback.py",
    "scripts/run_vsp02_b4_self_generated_closed_loop_feedback.py",
    "tests/experiments/candidates/vsp_02/test_self_generated_closed_loop_feedback.py",
    "docs/research/candidates/vsp_02/VSP02_B4_SELF_GENERATED_CLOSED_LOOP_FEEDBACK_CODE_SCIENCE_INDEX.md",
)
B4_DEPENDENCY_PATHS = (
    "experiments/candidates/vsp_02/vsp02_b3_lifecycle_credit_sign_bridge.py",
    "experiments/candidates/vsp_02/vsp02_b2_paired_shadow_learner_localization.py",
    "experiments/candidates/vsp_02/learned_cue_conditioned_lifecycle_control_v2.py",
    "experiments/candidates/vsp_02/owner_action_responsive_lifecycle.py",
)
B4_RUNTIME_PATHS = B4_CLAIM_PATHS + B4_DEPENDENCY_PATHS
ORIGINAL_ACTOR_ROUTE = b3.ORIGINAL_ACTOR_ROUTE
ORACLE_SIGN_ACTOR_ROUTE = b3.BRIDGE_ACTOR_ROUTE
CRITIC_ROUTE = b3.CRITIC_ROUTE
BEHAVIOR_MIXTURE_ROUTE = "coin<0.8:sample(raw_softmax);else:sample(Uniform(RELEASE,HOLD));likelihood=0.8*raw_softmax+0.1"
FIXED_UPDATE_ORDER = B4_ARMS


json_ready = b3.json_ready
canonical_bytes = b3.canonical_bytes
digest = b3.digest
model_payload = b3.model_payload
optimizer_payload = b3.optimizer_payload
_architecture_payload = b3._architecture_payload
_observation_firewall = b3._observation_firewall
_synthetic_history = b3._synthetic_history
_forward = b3._forward
_mixture_metrics_from_raw_q = b3._mixture_metrics_from_raw_q


def _cpu_time_seconds() -> float:
    """Injectable process CPU clock used only around registered train/evaluate work."""

    return time.process_time()


def _peak_process_rss_bytes() -> int:
    """Conservative injectable lifetime peak resident/working-set measurement."""

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        get_current_process = ctypes.windll.kernel32.GetCurrentProcess  # type: ignore[attr-defined]
        get_current_process.restype = ctypes.c_void_p
        get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo  # type: ignore[attr-defined]
        get_process_memory_info.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(ProcessMemoryCounters),
            wintypes.DWORD,
        )
        get_process_memory_info.restype = wintypes.BOOL
        if not get_process_memory_info(
            get_current_process(),
            ctypes.byref(counters),
            counters.cb,
        ):
            raise OSError("GetProcessMemoryInfo failed")
        return int(counters.PeakWorkingSetSize)
    import resource

    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak if sys.platform == "darwin" else peak * 1024


def _hash_int(*parts: object) -> int:
    material = B4_SEED_PREFIX + "\0".join(str(part) for part in parts)
    return int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:8], "big")


@dataclass(frozen=True)
class AddressTape:
    """Stateless immutable exogenous tape keyed by a full semantic address."""

    unit_id: str
    decimal_root: int

    def __post_init__(self) -> None:
        if (self.unit_id, self.decimal_root) not in B4_UNITS:
            raise ValueError(f"unregistered B4 unit/root: {self.unit_id}/{self.decimal_root}")

    def word(self, kind: str, *address: object) -> int:
        if kind not in B4_TAPE_KINDS:
            raise ValueError(f"unregistered B4 tape kind: {kind}")
        if not address:
            raise ValueError("tape address must be nonempty")
        stream = B4_TAPE_STREAM_BY_KIND[kind]
        return _hash_int(
            self.unit_id,
            self.decimal_root,
            stream,
            b4_seed(self.unit_id, self.decimal_root, stream),
            kind,
            *address,
        )

    def uniform(self, kind: str, *address: object) -> float:
        return (self.word(kind, *address) + 0.5) / float(2**64)

    def token(self, kind: str, *address: object) -> str:
        return f"{self.word(kind, *address):016x}"

    def identity(self) -> str:
        return digest({"assignment": B4_ASSIGNMENT_ID, "unit_id": self.unit_id, "decimal_root": self.decimal_root})

    def address(self, kind: str, *address: object) -> dict[str, object]:
        if kind not in B4_TAPE_KINDS or not address:
            raise ValueError("invalid tape address")
        return {
            "treatment": B4_ASSIGNMENT_ID,
            "unit_id": self.unit_id,
            "decimal_root": self.decimal_root,
            "stream": B4_TAPE_STREAM_BY_KIND[kind],
            "field": kind,
            "address": list(address),
        }


class B4LifecycleHost(b1.LifecycleHost):
    """The accepted B3 physical host with only a fresh B4 tape namespace."""

    def step(self, action: b1.Action, *, action_probabilities: Sequence[float]) -> dict[str, object]:
        if not self._open or self.escrow is not None:
            raise RuntimeError("episode action can be committed exactly once")
        probabilities = tuple(float(value) for value in action_probabilities)
        if len(probabilities) != 2 or any(not math.isfinite(value) or value < 0.0 for value in probabilities) or abs(sum(probabilities) - 1.0) > 1e-12:
            raise ValueError("invalid RELEASE/HOLD probability pair")
        escrow_id = hashlib.sha256(
            f"{B4_ASSIGNMENT_ID}/{self.lifecycle_id}/{self.owner_epoch}/{b1.B1_BEHAVIOR_VERSION}".encode()
        ).hexdigest()
        self.escrow = b1.ActionScoreEscrow(
            escrow_id=escrow_id,
            action=action.value,
            action_probabilities=probabilities,
            selected_likelihood=probabilities[action.index],
            owner_epoch=self.owner_epoch,
            behavior_version=b1.B1_BEHAVIOR_VERSION,
        )
        tape_id = f"{B4_PHYSICAL_TAPE_PREFIX}/{self.lifecycle_id}"
        self.tape_ids = [tape_id]
        first = b1.a1.apply_boundary(
            self.record,
            contract=b1.a1.candidate_contract(),
            action=b1.a1.OwnerAction(action.value),
            command_token=self.token,
            world=self.world,
            boundary_index=1,
            physical_clock=1,
            tape=b1.a1.PairedTape(tape_id=tape_id, primitive_action=b1.B1_PRIMITIVE),
            release_id=escrow_id,
        )
        self.record = first.record
        self.states.append(self.record.phase.value)
        self.environment_transitions += 1
        if action is b1.Action.RELEASE:
            self.rewards.append(1)
            if self.record.phase is not b1.a1.Phase.ENDED_RELEASE:
                raise AssertionError("authorized RELEASE did not stop")
        else:
            self.rewards.append(-1 if self.true_cue else 2)
            if self.record.phase is not b1.a1.Phase.ACTIVE:
                raise AssertionError("HOLD did not execute the frozen primitive")
            second = b1.a1.apply_boundary(
                self.record,
                contract=b1.a1.candidate_contract(),
                action=b1.a1.OwnerAction.HOLD,
                command_token=self.token,
                world=self.world,
                boundary_index=2,
                physical_clock=2,
                tape=b1.a1.PairedTape(tape_id=tape_id, natural=True, primitive_action=b1.B1_PRIMITIVE),
                release_id=escrow_id,
            )
            self.record = second.record
            self.states.append(self.record.phase.value)
            self.environment_transitions += 1
            self.rewards.append(0)
            if self.record.phase is not b1.a1.Phase.ENDED_NATURAL:
                raise AssertionError("HOLD did not naturally terminate")
        if self.record.end_cause is None or self.escrow.consumption_count != 0:
            raise AssertionError("invalid pre-close escrow state")
        self.escrow = replace(self.escrow, consumption_count=1)
        self.record = replace(
            self.record,
            phase=b1.a1.Phase.TARGET_CLOSED_TOMBSTONE,
            target_close_clock=self.record.physical_clock,
            tombstone_version=b1.B1_BEHAVIOR_VERSION,
            acknowledgements=self.record.acknowledgements + ("TARGET_CLOSED",),
        )
        self.states.append(self.record.phase.value)
        self.environment_transitions += 1
        self._open = False
        physical_return = sum(reward * (b1.B1_GAMMA**index) for index, reward in enumerate(self.rewards))
        return {
            "reward_sequence": list(self.rewards),
            "physical_return": physical_return,
            "physical_tape_ids": list(self.tape_ids),
            "environment_transitions": self.environment_transitions,
        }


def b4_seed(unit_id: str, decimal_root: int, stream_name: str) -> int:
    if (unit_id, decimal_root) not in B4_UNITS:
        raise ValueError(f"unregistered B4 unit/root: {unit_id}/{decimal_root}")
    if stream_name not in B4_SEED_STREAMS:
        raise ValueError(f"unregistered B4 seed stream: {stream_name}")
    return 1 + (_hash_int(unit_id, decimal_root, stream_name) % 2_147_483_646)


def seed_and_tape_report() -> dict[str, object]:
    derived: dict[str, dict[str, int]] = {}
    flat: list[int] = []
    for unit_id, root in B4_UNITS:
        tape = AddressTape(unit_id, root)
        values = {stream: b4_seed(unit_id, root, stream) for stream in B4_SEED_STREAMS}
        values.update({f"address_root/{kind}": tape.word(kind, "ROOT") for kind in B4_TAPE_KINDS})
        derived[unit_id] = values
        flat.extend(values.values())
    predecessor_values = {
        b1.stream_seed(seed_id, stream)
        for seed_id in b1.B1_SEED_IDS
        for stream in b1.B1_RNG_STREAMS
    }
    predecessor_values.update(
        b2.b2_seed(unit, root, stream)
        for unit, root in b2.B2_UNITS
        for stream in b2.B2_STREAMS
    )
    predecessor_values.update(
        b3.b3_seed(unit, root, stream)
        for unit, root in b3.B3_UNITS
        for stream in b3.B3_STREAMS
    )
    predecessor_units = set(b1.B1_SEED_IDS) | {unit for unit, _ in b2.B2_UNITS} | {unit for unit, _ in b3.B3_UNITS}
    return {
        "function": "SHA256(VSP02-B4-V1, unit_id, decimal_root, stream, field, full_address)",
        "seed_streams": list(B4_SEED_STREAMS),
        "tape_kinds": list(B4_TAPE_KINDS),
        "derived_roots": derived,
        "all_b4_roots_unique": len(flat) == len(set(flat)),
        "collision_with_predecessor_values": sorted(set(flat) & predecessor_values),
        "identity_collision_with_predecessors": any(unit in predecessor_units for unit, _ in B4_UNITS),
        "identity_families": {
            "run": B4_RUN_ID,
            "tape": B4_PHYSICAL_TAPE_PREFIX,
            "batch": f"{B4_ASSIGNMENT_ID}/<unit>/U<update>/<collector>/BATCH",
            "checkpoint": f"{B4_ASSIGNMENT_ID}/<unit>/<arm>/FINAL-128",
            "evaluation": f"{B4_ASSIGNMENT_ID}/<unit>/<arm>/EVAL/<episode>",
        },
        "identity_families_treatment_prefixed": True,
        "silent_reseed_path": False,
    }


def _initial_recurrent_state() -> dict[str, object]:
    return {"reset_each_episode": True, "hidden": [0.0] * b1.B1_HIDDEN_SIZE, "dtype": "torch.float64"}


def _initial_carried_learner_state() -> dict[str, object]:
    return {
        "next_update_index": 0,
        "optimizer_steps": 0,
        "batches_consumed": 0,
        "rows_consumed": 0,
        "last_batch_digest": None,
        "last_batch_order": None,
    }


def _initial_learner_rng_state(unit_id: str, root: int) -> dict[str, object]:
    return {
        "parameter_initialization_seed": b4_seed(unit_id, root, "parameter_initialization"),
        "optimizer_initialization_seed": b4_seed(unit_id, root, "optimizer_initialization"),
        "learner_stochasticity_seed": b4_seed(unit_id, root, "learner_stochasticity"),
        "learner_stochasticity_draw_count": 0,
        "minibatch_order_seed": b4_seed(unit_id, root, "minibatch_order"),
        "minibatch_order_is_address_indexed": True,
        "unlisted_rng_allowed": False,
    }


def _new_learners(unit_id: str, root: int) -> tuple[dict[str, b1.GRUActorCritic], dict[str, torch.optim.Optimizer]]:
    base = b1.GRUActorCritic(init_seed=b4_seed(unit_id, root, "parameter_initialization"))
    base_optimizer = torch.optim.Adam(base.parameters(), lr=0.003)
    empty_adam = deepcopy(base_optimizer.state_dict())
    models = {arm: deepcopy(base) for arm in B4_ARMS}
    optimizers: dict[str, torch.optim.Optimizer] = {}
    for arm in B4_ARMS:
        optimizer = torch.optim.Adam(models[arm].parameters(), lr=0.003)
        optimizer.load_state_dict(deepcopy(empty_adam))
        optimizers[arm] = optimizer
    return models, optimizers


def _complete_state_payload(
    model: b1.GRUActorCritic,
    optimizer: torch.optim.Optimizer,
    learner_state: Mapping[str, object] | None = None,
    learner_rng_state: Mapping[str, object] | None = None,
) -> dict[str, object]:
    return {
        "actor_critic_recurrent_parameters": model_payload(model),
        "optimizer": optimizer_payload(optimizer),
        "recurrent_state": _initial_recurrent_state(),
        "initial_state": _initial_recurrent_state(),
        "carried_learner_state": dict(learner_state or _initial_carried_learner_state()),
        "registered_learner_rng_state": dict(learner_rng_state or {}),
    }


def _complete_state_hash(
    model: b1.GRUActorCritic,
    optimizer: torch.optim.Optimizer,
    learner_state: Mapping[str, object] | None = None,
    learner_rng_state: Mapping[str, object] | None = None,
) -> str:
    return digest(_complete_state_payload(model, optimizer, learner_state, learner_rng_state))


def correctness_sign(action: str, cue: int) -> float:
    return b3.correctness_sign(action, cue)


def _require_advantage_row(row: Mapping[str, object]) -> None:
    b3._require_advantage_row(row)


def _gradient_norm(gradients: Sequence[Tensor | None]) -> float:
    norms = [torch.linalg.vector_norm(gradient, 2.0) for gradient in gradients if gradient is not None]
    return float(torch.linalg.vector_norm(torch.stack(norms), 2.0)) if norms else 0.0


def _loss_terms(arm: str, model: b1.GRUActorCritic, batch: Sequence[Mapping[str, object]]) -> tuple[Tensor, dict[str, object]]:
    if arm not in B4_ARMS or not batch:
        raise ValueError("unknown arm or empty batch")
    batch_before = digest(batch)
    actor_terms: list[Tensor] = []
    policy_actor_terms: list[Tensor] = []
    entropy_terms: list[Tensor] = []
    critic_terms: list[Tensor] = []
    coefficients: list[float] = []
    advantages: list[float] = []
    critic_targets: list[float] = []
    correctness_classes: Counter[int] = Counter()
    sign_changes = 0
    for row in batch:
        _require_advantage_row(row)
        observations = row.get("O")
        if not isinstance(observations, Sequence) or not _observation_firewall(observations):
            raise ValueError("observation firewall or history missing")
        _, _, probabilities, baseline, entropy = _forward(model, observations)
        target = torch.tensor(float(row["G"]), dtype=torch.float64)
        advantage = target - baseline
        if not torch.isfinite(advantage):
            raise ValueError("nonfinite lifecycle advantage")
        action_index = b1.Action(str(row.get("A_behavior"))).index
        if arm in B4_COLLECTORS:
            expected = row.get("behavior_probabilities")
            if not isinstance(expected, list) or len(expected) != 2 or any(
                not math.isclose(float(actual), float(bound), rel_tol=0.0, abs_tol=1e-12)
                for actual, bound in zip(probabilities.detach(), expected)
            ):
                raise RuntimeError("collector behavior probabilities changed before own update")
        if arm == "RL_ORIGINAL_GENERATOR":
            coefficient = advantage.detach()
        else:
            metadata = row.get("metadata")
            if not isinstance(metadata, Mapping) or "true_cue" not in metadata:
                raise ValueError("oracle-sign cue missing")
            sign = correctness_sign(str(row.get("A_behavior")), int(metadata["true_cue"]))
            coefficient = torch.tensor(sign, dtype=torch.float64) * advantage.detach().abs()
            correctness_classes[int(sign)] += 1
            if float(advantage.detach()) != 0.0 and math.copysign(1.0, float(advantage.detach())) != sign:
                sign_changes += 1
        if not torch.isfinite(coefficient):
            raise ValueError("nonfinite lifecycle actor coefficient")
        policy_term = -coefficient * torch.log(probabilities[action_index])
        entropy_term = -0.01 * entropy
        # Protected B3 route: assemble each row completely, then stack/mean.
        actor_terms.append(policy_term - 0.01 * entropy)
        policy_actor_terms.append(policy_term)
        entropy_terms.append(entropy_term)
        critic_terms.append(0.5 * advantage**2)
        coefficients.append(float(coefficient))
        advantages.append(float(advantage.detach()))
        critic_targets.append(float(target))
    if digest(batch) != batch_before:
        raise RuntimeError("loss route mutated immutable batch")
    policy_actor_loss = torch.stack(policy_actor_terms).mean()
    entropy_loss = torch.stack(entropy_terms).mean()
    actor_loss = torch.stack(actor_terms).mean()
    critic_loss = torch.stack(critic_terms).mean()
    parameters = tuple(model.parameters())
    actor_gradient_norm = _gradient_norm(torch.autograd.grad(policy_actor_loss, parameters, retain_graph=True, allow_unused=True))
    entropy_gradient_norm = _gradient_norm(torch.autograd.grad(entropy_loss, parameters, retain_graph=True, allow_unused=True))
    critic_gradient_norm = _gradient_norm(torch.autograd.grad(critic_loss, parameters, retain_graph=True, allow_unused=True))
    combined_gradient_norm = _gradient_norm(
        torch.autograd.grad(actor_loss + critic_loss, parameters, retain_graph=True, allow_unused=True)
    )
    if not all(math.isfinite(value) for value in (actor_gradient_norm, entropy_gradient_norm, critic_gradient_norm, combined_gradient_norm)):
        raise ValueError("nonfinite route-separated gradient")
    absolute = [abs(value) for value in advantages]
    abs_mean = sum(absolute) / len(absolute)
    abs_variance = sum((value - abs_mean) ** 2 for value in absolute) / len(absolute)
    target_mean = sum(critic_targets) / len(critic_targets)
    target_variance = sum((value - target_mean) ** 2 for value in critic_targets) / len(critic_targets)
    return actor_loss + critic_loss, {
        "actor_loss": float(actor_loss.detach()),
        "policy_actor_loss": float(policy_actor_loss.detach()),
        "entropy_loss": float(entropy_loss.detach()),
        "critic_loss": float(critic_loss.detach()),
        "actor_route": ORIGINAL_ACTOR_ROUTE if arm == "RL_ORIGINAL_GENERATOR" else ORACLE_SIGN_ACTOR_ROUTE,
        "critic_route": CRITIC_ROUTE,
        "advantages": advantages,
        "actor_coefficients": coefficients,
        "critic_targets": critic_targets,
        "action_occupancy": dict(Counter(str(row["A_behavior"]) for row in batch)),
        "history_occupancy": {
            "unique_history_count": len({digest(row["O"]) for row in batch}),
            "ordered_history_digests": [digest(row["O"]) for row in batch],
        },
        "advantage_count": len(advantages),
        "zero_advantage_count": sum(value == 0.0 for value in advantages),
        "nonzero_advantage_count": sum(value != 0.0 for value in advantages),
        "credit_density": sum(value != 0.0 for value in coefficients) / len(coefficients),
        "absolute_advantage_mean": abs_mean,
        "absolute_advantage_variance": abs_variance,
        "critic_target_mean": target_mean,
        "critic_target_variance": target_variance,
        "correctness_class_counts": {"-1": correctness_classes[-1], "+1": correctness_classes[1]},
        "actual_sign_change_count": sign_changes,
        "max_abs_magnitude_error": max(
            (abs(abs(coefficient) - abs(advantage)) for coefficient, advantage in zip(coefficients, advantages)),
            default=0.0,
        ) if arm != "RL_ORIGINAL_GENERATOR" else 0.0,
        "oracle_scalar_only": arm != "RL_ORIGINAL_GENERATOR",
        "batch_digest_before_after": batch_before,
        "actor_gradient_norm": actor_gradient_norm,
        "entropy_gradient_norm": entropy_gradient_norm,
        "critic_gradient_norm": critic_gradient_norm,
        "combined_gradient_norm": combined_gradient_norm,
    }


def _optimizer_step(arm: str, model: b1.GRUActorCritic, optimizer: torch.optim.Optimizer, batch: Sequence[Mapping[str, object]]) -> dict[str, object]:
    parameters_before = digest(model_payload(model))
    optimizer_before = digest(optimizer_payload(optimizer))
    optimizer.zero_grad(set_to_none=True)
    loss, route = _loss_terms(arm, model, batch)
    if not torch.isfinite(loss):
        raise ValueError("nonfinite loss")
    loss.backward()
    if any(parameter.grad is None or not torch.isfinite(parameter.grad).all() for parameter in model.parameters()):
        raise ValueError("missing or nonfinite gradient")
    pre_clip = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
    if not math.isfinite(pre_clip):
        raise ValueError("nonfinite pre-clip gradient norm")
    optimizer.step()
    return {
        "parameters_before": parameters_before,
        "parameters_after": digest(model_payload(model)),
        "optimizer_before": optimizer_before,
        "optimizer_after": digest(optimizer_payload(optimizer)),
        "loss": float(loss.detach()),
        "actor_loss": route["actor_loss"],
        "policy_actor_loss": route["policy_actor_loss"],
        "entropy_loss": route["entropy_loss"],
        "critic_loss": route["critic_loss"],
        "actor_route": route["actor_route"],
        "critic_route": route["critic_route"],
        "gradient_norm_before_clip": pre_clip,
        "combined_gradient_norm_before_clip": route["combined_gradient_norm"],
        "clip_threshold": 1.0,
        "clipped": pre_clip > 1.0,
        "clip_factor": min(1.0, 1.0 / pre_clip) if pre_clip > 0.0 else 1.0,
        **{key: route[key] for key in (
            "advantage_count", "zero_advantage_count", "nonzero_advantage_count", "credit_density",
            "absolute_advantage_mean", "absolute_advantage_variance", "critic_target_mean",
            "critic_target_variance", "correctness_class_counts", "actual_sign_change_count",
            "max_abs_magnitude_error", "oracle_scalar_only", "actor_gradient_norm", "entropy_gradient_norm",
            "critic_gradient_norm", "action_occupancy", "history_occupancy",
        )},
    }


def _advance_carried_learner_state(
    state: Mapping[str, object], *, update_index: int, batch_digest: str, batch_order: Sequence[int]
) -> dict[str, object]:
    if state.get("next_update_index") != update_index:
        raise RuntimeError("carried learner update index mismatch")
    return {
        "next_update_index": update_index + 1,
        "optimizer_steps": int(state["optimizer_steps"]) + 1,
        "batches_consumed": int(state["batches_consumed"]) + 1,
        "rows_consumed": int(state["rows_consumed"]) + B4_BATCH_SIZE,
        "last_batch_digest": batch_digest,
        "last_batch_order": list(batch_order),
    }


def _ranked_permutation(tape: AddressTape, kind: str, group: object, size: int) -> list[int]:
    return sorted(range(size), key=lambda index: (tape.word(kind, group, index), index))


def _schedule(unit_id: str, root: int) -> list[dict[str, object]]:
    tape = AddressTape(unit_id, root)
    rows: list[dict[str, object]] = []
    for update_index in range(B4_UPDATES_PER_UNIT):
        base_cues = [0] * 4 + [1] * 4
        cue_order = _ranked_permutation(tape, "cue_schedule", update_index, B4_BATCH_SIZE)
        cues = [base_cues[index] for index in cue_order]
        for within_update, cue in enumerate(cues):
            episode_index = update_index * B4_BATCH_SIZE + within_update
            rows.append({
                "unit_id": unit_id,
                "decimal_root": root,
                "update_index": update_index,
                "within_update": within_update,
                "episode_index": episode_index,
                "owner_epoch": f"{unit_id}-TR-{episode_index:04d}",
                "true_cue": cue,
                "cue_source_index": cue_order[within_update],
                "clone_id": f"{unit_id}/TRAIN/{episode_index:04d}",
            })
    return rows


def _schedule_contract(rows: Sequence[Mapping[str, object]]) -> bool:
    return (
        len(rows) == B4_TRAIN_EPISODES_PER_COLLECTOR_UNIT
        and Counter(int(row["true_cue"]) for row in rows) == Counter({0: 512, 1: 512})
        and all(
            Counter(int(row["true_cue"]) for row in rows[start : start + B4_BATCH_SIZE]) == Counter({0: 4, 1: 4})
            for start in range(0, len(rows), B4_BATCH_SIZE)
        )
    )


def _update_tape_receipt(tape: AddressTape, update_index: int) -> dict[str, object]:
    values = []
    for within in range(B4_BATCH_SIZE):
        values.append({
            "within_update": within,
            "environment_randomness": tape.token("environment_randomness", update_index, within),
            "behavior_mixture_coin": tape.uniform("behavior_mixture_coin", update_index, within),
            "sampling_uniform": tape.uniform("sampling_uniform", update_index, within),
            "addresses": {
                kind: tape.address(kind, update_index, within)
                for kind in ("environment_randomness", "behavior_mixture_coin", "sampling_uniform")
            },
        })
    receipt = {
        "tape_identity": tape.identity(),
        "update_index": update_index,
        "cue_permutation": _ranked_permutation(tape, "cue_schedule", update_index, B4_BATCH_SIZE),
        "minibatch_order": _ranked_permutation(tape, "minibatch_order", update_index, B4_BATCH_SIZE),
        "values": values,
    }
    return json.loads(canonical_bytes(receipt))


def _collect_batch(*, unit_id: str, update_index: int, rows: Sequence[Mapping[str, object]], model: b1.GRUActorCritic, tape: AddressTape) -> tuple[list[dict[str, object]], int]:
    if len(rows) != B4_BATCH_SIZE:
        raise ValueError("collector requires one complete eight-row batch")
    batch: list[dict[str, object]] = []
    transitions = 0
    for row in rows:
        within = int(row["within_update"])
        event_token = tape.token("environment_randomness", update_index, within)
        mixture_coin = tape.uniform("behavior_mixture_coin", update_index, within)
        sampling_uniform = tape.uniform("sampling_uniform", update_index, within)
        host = B4LifecycleHost()
        cue = int(row["true_cue"])
        cue_observation = host.reset(
            lifecycle_id=f"{B4_ASSIGNMENT_ID}/{unit_id}/TRAIN/{int(row['episode_index']):04d}/{event_token}",
            owner_epoch=str(row["owner_epoch"]),
            true_cue=cue,
            presented_cue=cue,
        )
        observations = [asdict(cue_observation), asdict(host.decision_observation())]
        if not _observation_firewall(observations):
            raise RuntimeError("training observation firewall mismatch")
        with torch.no_grad():
            _, raw_softmax, probabilities_tensor, _, _ = _forward(model, observations)
        raw = [float(value) for value in raw_softmax]
        probabilities = [float(value) for value in probabilities_tensor]
        policy_component = mixture_coin < 0.8
        release_threshold = raw[b1.Action.RELEASE.index] if policy_component else 0.5
        action = b1.Action.RELEASE if sampling_uniform < release_threshold else b1.Action.HOLD
        episode = host.step(action, action_probabilities=probabilities)
        immutable = {
            "O": observations,
            "H0": [0.0] * b1.B1_HIDDEN_SIZE,
            "M_reset": [1, 0],
            "M_active": [1, 1],
            "M_valid": [0, 1],
            "M_lifecycle": [0, 1],
            "A_behavior": action.value,
            "R": list(episode["reward_sequence"]),
            "Done": [False] * (len(episode["reward_sequence"]) - 1) + [True],
            "G": float(episode["physical_return"]),
            "raw_policy_probabilities": raw,
            "behavior_probabilities": probabilities,
            "environment_transitions": int(episode["environment_transitions"]),
            "metadata": {
                "unit_id": unit_id,
                "decimal_root": tape.decimal_root,
                "update_index": update_index,
                "within_update": within,
                "episode_index": int(row["episode_index"]),
                "owner_epoch": str(row["owner_epoch"]),
                "true_cue": cue,
                "clone_id": str(row["clone_id"]),
                "event_tape_token": event_token,
                "behavior_mixture_component": "POLICY_0.8" if policy_component else "UNIFORM_0.2",
                "behavior_mixture_coin": mixture_coin,
                "sampling_uniform": sampling_uniform,
                "tape_addresses": {
                    "cue_schedule": tape.address("cue_schedule", update_index, int(row["cue_source_index"])),
                    "environment_randomness": tape.address("environment_randomness", update_index, within),
                    "behavior_mixture_coin": tape.address("behavior_mixture_coin", update_index, within),
                    "sampling_uniform": tape.address("sampling_uniform", update_index, within),
                },
                "physical_tape_ids": list(episode["physical_tape_ids"]),
            },
        }
        frozen = json.loads(canonical_bytes(immutable))
        batch.append(frozen)
        transitions += int(episode["environment_transitions"])
    return batch, transitions


def _immutable_row_contract(row: Mapping[str, object]) -> bool:
    if set(row) != {
        "O", "H0", "M_reset", "M_active", "M_valid", "M_lifecycle", "A_behavior", "R", "Done", "G",
        "raw_policy_probabilities", "behavior_probabilities", "environment_transitions", "metadata",
    }:
        return False
    observations = row.get("O")
    if not isinstance(observations, Sequence) or not _observation_firewall(observations):
        return False
    try:
        _require_advantage_row(row)
    except (TypeError, ValueError):
        return False
    if row.get("H0") != [0.0] * b1.B1_HIDDEN_SIZE or row.get("M_reset") != [1, 0] or row.get("M_active") != [1, 1]:
        return False
    if row.get("A_behavior") not in {action.value for action in b1.Action}:
        return False
    rewards, done = row.get("R"), row.get("Done")
    if not isinstance(rewards, list) or not isinstance(done, list) or len(rewards) != len(done) or not done or done[-1] is not True or any(done[:-1]):
        return False
    if any(not math.isfinite(float(value)) for value in rewards):
        return False
    expected_return = sum(float(value) * b1.B1_GAMMA**index for index, value in enumerate(rewards))
    if not math.isclose(float(row["G"]), expected_return, rel_tol=0.0, abs_tol=1e-12):
        return False
    raw, mixture = row.get("raw_policy_probabilities"), row.get("behavior_probabilities")
    if not isinstance(raw, list) or not isinstance(mixture, list) or len(raw) != 2 or len(mixture) != 2:
        return False
    if any(not math.isfinite(float(value)) for value in (*raw, *mixture)):
        return False
    if not math.isclose(sum(float(value) for value in raw), 1.0, rel_tol=0.0, abs_tol=1e-12):
        return False
    if any(not math.isclose(float(mix), 0.8 * float(policy) + 0.1, rel_tol=0.0, abs_tol=1e-12) for mix, policy in zip(mixture, raw)):
        return False
    metadata = row.get("metadata")
    if not isinstance(metadata, Mapping) or metadata.get("true_cue") not in (0, 1):
        return False
    if not (0.0 < float(metadata.get("behavior_mixture_coin", -1.0)) < 1.0 and 0.0 < float(metadata.get("sampling_uniform", -1.0)) < 1.0):
        return False
    tapes = metadata.get("physical_tape_ids")
    try:
        unit_id = str(metadata["unit_id"])
        root = int(metadata["decimal_root"])
        update_index = int(metadata["update_index"])
        within = int(metadata["within_update"])
        tape = AddressTape(unit_id, root)
        addresses = metadata["tape_addresses"]
        if not isinstance(addresses, Mapping):
            return False
        cue_source = int(addresses["cue_schedule"]["address"][-1])  # type: ignore[index]
        expected_addresses = {
            "cue_schedule": tape.address("cue_schedule", update_index, cue_source),
            "environment_randomness": tape.address("environment_randomness", update_index, within),
            "behavior_mixture_coin": tape.address("behavior_mixture_coin", update_index, within),
            "sampling_uniform": tape.address("sampling_uniform", update_index, within),
        }
        if addresses != expected_addresses:
            return False
        if _ranked_permutation(tape, "cue_schedule", update_index, B4_BATCH_SIZE)[within] != cue_source:
            return False
        if int(metadata["true_cue"]) != ([0] * 4 + [1] * 4)[cue_source]:
            return False
        if metadata.get("event_tape_token") != tape.token("environment_randomness", update_index, within):
            return False
        if not math.isclose(float(metadata["behavior_mixture_coin"]), tape.uniform("behavior_mixture_coin", update_index, within), rel_tol=0.0, abs_tol=0.0):
            return False
        if not math.isclose(float(metadata["sampling_uniform"]), tape.uniform("sampling_uniform", update_index, within), rel_tol=0.0, abs_tol=0.0):
            return False
    except (KeyError, TypeError, ValueError, IndexError):
        return False
    return (
        row.get("environment_transitions") in (4, 5)
        and isinstance(tapes, list)
        and len(tapes) == 1
        and str(tapes[0]).startswith(f"{B4_PHYSICAL_TAPE_PREFIX}/")
        and not str(tapes[0]).startswith(f"{b3.B3_PHYSICAL_TAPE_PREFIX}/")
    )


def _proof_batch(model: b1.GRUActorCritic, *, zero_advantage: bool = False) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, cue in enumerate((0, 1, 0, 1, 0, 1, 0, 1)):
        observations = _synthetic_history(cue, owner_epoch=f"B4-PROOF-{index:02d}")
        with torch.no_grad():
            _, raw, probabilities, baseline, _ = _forward(model, observations)
        action = b1.Action.HOLD if index % 4 in (0, 1) else b1.Action.RELEASE
        rows.append({
            "O": observations,
            "H0": [0.0] * b1.B1_HIDDEN_SIZE,
            "M_reset": [1, 0],
            "M_active": [1, 1],
            "M_valid": [0, 1],
            "M_lifecycle": [0, 1],
            "A_behavior": action.value,
            "R": [0.0],
            "Done": [True],
            "G": float(baseline) if zero_advantage else float(baseline) + (-0.75 if index % 3 == 0 else 0.5),
            "raw_policy_probabilities": [float(value) for value in raw],
            "behavior_probabilities": [float(value) for value in probabilities],
            "environment_transitions": 4,
            "metadata": {"true_cue": cue, "clone_id": f"B4-PROOF/{index}"},
        })
    return json.loads(canonical_bytes(rows))


def _synthetic_barrier_proof(
    models: Mapping[str, b1.GRUActorCritic],
    optimizers: Mapping[str, torch.optim.Optimizer],
    learner_states: dict[str, dict[str, object]],
    learner_rng_states: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    generator_batch = _proof_batch(models["RL_ORIGINAL_GENERATOR"])
    self_batch = json.loads(canonical_bytes(generator_batch))
    order = list(range(B4_BATCH_SIZE))
    before = {
        arm: _complete_state_hash(models[arm], optimizers[arm], learner_states[arm], learner_rng_states[arm])
        for arm in B4_ARMS
    }
    generator_update = _optimizer_step("RL_ORIGINAL_GENERATOR", models["RL_ORIGINAL_GENERATOR"], optimizers["RL_ORIGINAL_GENERATOR"], generator_batch)
    shadow_update = _optimizer_step("CREDIT_SIGN_SHADOW", models["CREDIT_SIGN_SHADOW"], optimizers["CREDIT_SIGN_SHADOW"], generator_batch)
    self_update = _optimizer_step("CREDIT_SIGN_SELF_FEEDBACK", models["CREDIT_SIGN_SELF_FEEDBACK"], optimizers["CREDIT_SIGN_SELF_FEEDBACK"], self_batch)
    for arm, batch_value in (
        ("RL_ORIGINAL_GENERATOR", generator_batch),
        ("CREDIT_SIGN_SHADOW", generator_batch),
        ("CREDIT_SIGN_SELF_FEEDBACK", self_batch),
    ):
        learner_states[arm] = _advance_carried_learner_state(
            learner_states[arm], update_index=0, batch_digest=digest(batch_value), batch_order=order
        )
    after = {
        arm: _complete_state_hash(models[arm], optimizers[arm], learner_states[arm], learner_rng_states[arm])
        for arm in B4_ARMS
    }
    return {
        "synthetic_only": True,
        "complete_batches_frozen_before_updates": True,
        "generator_batch_digest": digest(generator_batch),
        "self_batch_digest": digest(self_batch),
        "first_batch_byte_identity": canonical_bytes(generator_batch) == canonical_bytes(self_batch),
        "ordered_row_digests": [digest(row) for row in generator_batch],
        "fixed_update_order": list(FIXED_UPDATE_ORDER),
        "batch_order": order,
        "initial_complete_state_hashes": before,
        "first_oracle_successor_hashes": {arm: after[arm] for arm in B4_ARMS[1:]},
        "first_oracle_successor_identity": after["CREDIT_SIGN_SHADOW"] == after["CREDIT_SIGN_SELF_FEEDBACK"],
        "post_first_collector_parameter_divergence": generator_update["parameters_after"] != self_update["parameters_after"],
        "finite_actor_gradients": all(
            math.isfinite(float(update["actor_gradient_norm"]))
            for update in (generator_update, shadow_update, self_update)
        ),
        "oracle_magnitude_identity": shadow_update["max_abs_magnitude_error"] == self_update["max_abs_magnitude_error"] == 0.0,
        "activity": _zero_activity(),
    }


def build_manifest(*, source_revision: str, run_id: str, technical_only: bool) -> dict[str, object]:
    return {
        "schema_version": B4_SCHEMA_VERSION,
        "artifact_kind": "vsp02_b4_manifest",
        "assignment_id": B4_ASSIGNMENT_ID,
        "direction_id": B4_DIRECTION_ID,
        "candidate": B4_CANDIDATE,
        "host_id": B4_HOST_ID,
        "evidence_level": "B_ORDINARY_NONFORMAL",
        "formal": False,
        "resource_class": B4_RESOURCE_CLASS,
        "pool_units": B4_POOL_UNITS,
        "accelerator": "CPU_ONLY_NO_GPU",
        "paid_service": False,
        "implementation_base": B4_IMPLEMENTATION_BASE,
        "scientific_freeze": {
            "handoff_sha256": B4_FREEZE_HANDOFF_SHA256,
            "publication_commit": B4_FREEZE_PUBLICATION_COMMIT,
        },
        "canonical_artifacts": {
            "run_root": B4_CANONICAL_RUN_ROOT,
            "operator_receipt": B4_OPERATOR_RECEIPT,
        },
        "source_revision": source_revision,
        "run_id": run_id,
        "technical_only": technical_only,
        "arms": list(B4_ARMS),
        "collectors": list(B4_COLLECTORS),
        "units": [{"unit_id": unit, "decimal_root": root} for unit, root in B4_UNITS],
        "tape": {
            "kind": "immutable_address_indexed_sha256",
            "kinds": list(B4_TAPE_KINDS),
            "shared_mutable_rng": False,
            "collision_policy": "FAIL_CLOSED_NO_RESEED",
        },
        "seed_streams": list(B4_SEED_STREAMS),
        "learner_rng_contract": {
            "one_initial_state_derived_then_cloned_to_all_arms": True,
            "per_arm_stochasticity_draws": 0,
            "per_arm_minibatch_order_receipts": True,
        },
        "unlisted_rng_forbidden": True,
        "training": {
            "updates_per_unit": 128,
            "episodes_per_collector_update": 8,
            "episodes_per_collector_unit": 1_024,
            "cue_count_per_collector_update": {"0": 4, "1": 4},
            "dual_collector_phase_barrier": True,
            "fixed_update_order": list(FIXED_UPDATE_ORDER),
            "shadow_batch_source": "RL_ORIGINAL_GENERATOR",
            "self_feedback_batch_source": "CREDIT_SIGN_SELF_FEEDBACK",
            "first_collector_batches_byte_identical": True,
            "first_oracle_successor_complete_state_identical": True,
            "complete_state_fields": [
                "actor_critic_recurrent_parameters", "optimizer", "recurrent_state", "initial_state",
                "carried_learner_state", "registered_learner_rng_state",
            ],
        },
        "evaluation": {
            "episodes_per_unit_arm": 128,
            "cue_counts": {"0": 64, "1": 64},
            "independently_recreated_common_panels": True,
            "checkpoints_per_arm_unit": 1,
            "checkpoints_total": 15,
            "stochastic_action_draws": 0,
        },
        "optimizer": {
            "name": "Adam", "learning_rate": 0.003, "betas": [0.9, 0.999], "epsilon": 1e-8,
            "weight_decay": 0.0, "amsgrad": False, "gradient_norm_clip": 1.0,
        },
        "behavior_mixture": BEHAVIOR_MIXTURE_ROUTE,
        "loss_contract": {
            "original_actor": ORIGINAL_ACTOR_ROUTE,
            "oracle_sign_actor": ORACLE_SIGN_ACTOR_ROUTE,
            "critic": CRITIC_ROUTE,
            "zero_advantage_credit": 0.0,
            "missing_masked_nonfinite_advantage": "INVALID",
            "oracle_access": "post-forward scalar correctness sign only",
        },
        "evidence_complexity": {"H": b1.B1_HORIZON, "K_search": 0, "hypothetical_transitions": 0},
        "expected_activity": {
            "real_training_episodes": 10_240,
            "optimizer_updates": 1_920,
            "evaluation_episodes": 1_920,
            "checkpoints_total": 15,
        },
        "caps": dict(B4_CAPS),
        "branches": list(B4_BRANCH_PRECEDENCE),
        "result_bearing_runs": 0 if technical_only else 1,
        "retry_rescue_sweep_extra_arm_seed_checkpoint": 0,
        "nonclaims": [
            "not on-policy and not established as a standard policy-gradient objective",
            "mediator differences are descendants and are not separately identified causes",
            "no general actor-critic, recurrence, optimizer, MARL, transfer, promotion, retirement, or C-level claim",
            "no B3 reinterpretation, reopening, rerun, rescue, or successor authorization",
        ],
    }


def manifest_identity(manifest: Mapping[str, object]) -> str:
    return digest(manifest)


def validate_manifest(manifest: object) -> tuple[str, ...]:
    if not isinstance(manifest, Mapping):
        return ("manifest is not an object",)
    expected = build_manifest(
        source_revision=str(manifest.get("source_revision", "")),
        run_id=str(manifest.get("run_id", "")),
        technical_only=bool(manifest.get("technical_only")),
    )
    issues = [f"manifest {key} mismatch" for key, value in expected.items() if manifest.get(key) != value]
    if not manifest.get("source_revision") or not manifest.get("run_id"):
        issues.append("source_revision and run_id must be nonempty")
    if manifest.get("technical_only") is False and manifest.get("run_id") != B4_RUN_ID:
        issues.append(f"registered full run_id must be {B4_RUN_ID}")
    return tuple(issues)


def _git_binding(repo_root: Path, source_revision: str) -> list[str]:
    issues: list[str] = []

    def git(*arguments: str) -> str:
        return subprocess.run(["git", *arguments], cwd=repo_root, check=True, capture_output=True, text=True).stdout.strip()

    try:
        actual = git("rev-parse", "HEAD")
        if actual != source_revision:
            issues.append(f"source revision {source_revision} != checkout HEAD {actual}")
        tracked = set(git("ls-files", "--", *B4_RUNTIME_PATHS).splitlines())
        if tracked != set(B4_RUNTIME_PATHS):
            issues.append("B4 claim and runtime dependency path set is not fully tracked")
        dirty = git("status", "--porcelain=v1", "--untracked-files=all", "--", *B4_RUNTIME_PATHS)
        if dirty:
            issues.append("B4 claim or runtime dependency paths differ from HEAD")
        if subprocess.run(
            ["git", "merge-base", "--is-ancestor", B4_IMPLEMENTATION_BASE, actual],
            cwd=repo_root,
            check=False,
            capture_output=True,
        ).returncode != 0:
            issues.append("implementation base is not an ancestor of checkout HEAD")
        publication_type = git("cat-file", "-t", B4_FREEZE_PUBLICATION_COMMIT)
        if publication_type != "commit":
            issues.append("scientific freeze publication anchor is not an exact Git commit object")
        if subprocess.run(
            ["git", "merge-base", "--is-ancestor", B4_FREEZE_PUBLICATION_COMMIT, actual],
            cwd=repo_root,
            check=False,
            capture_output=True,
        ).returncode != 0:
            issues.append("scientific freeze publication is not an ancestor of checkout HEAD")
    except (OSError, subprocess.CalledProcessError) as error:
        issues.append(f"Git source binding failed: {error}")
    return issues


def preflight_report(manifest: Mapping[str, object], *, repo_root: Path | None = None) -> dict[str, object]:
    gate_issues = {f"P{index}": [] for index in range(12)}
    gate_issues["P0"].extend(validate_manifest(manifest))
    if manifest.get("technical_only") is False:
        if repo_root is None:
            gate_issues["P0"].append("result-bearing preflight requires repo_root")
        else:
            gate_issues["P0"].extend(_git_binding(repo_root, str(manifest["source_revision"])))
    roots = seed_and_tape_report()
    if not roots["all_b4_roots_unique"] or roots["collision_with_predecessor_values"] or roots["identity_collision_with_predecessors"]:
        gate_issues["P1"].append("B4 seed/tape namespace collision; silent reseed forbidden")
    unit_id, root = B4_UNITS[0]
    models, optimizers = _new_learners(unit_id, root)
    learner_states = {arm: deepcopy(_initial_carried_learner_state()) for arm in B4_ARMS}
    base_learner_rng = _initial_learner_rng_state(unit_id, root)
    learner_rng_states = {arm: deepcopy(base_learner_rng) for arm in B4_ARMS}
    initial_complete = {
        arm: _complete_state_hash(models[arm], optimizers[arm], learner_states[arm], learner_rng_states[arm])
        for arm in B4_ARMS
    }
    initial_parameters = {arm: digest(model_payload(models[arm])) for arm in B4_ARMS}
    initial_optimizers = {arm: digest(optimizer_payload(optimizers[arm])) for arm in B4_ARMS}
    recurrent = {arm: digest(_initial_recurrent_state()) for arm in B4_ARMS}
    if any(len(set(mapping.values())) != 1 for mapping in (initial_complete, initial_parameters, initial_optimizers, recurrent)):
        gate_issues["P2"].append("initial complete states are not byte-identical")
    tape = AddressTape(unit_id, root)
    receipt = _update_tape_receipt(tape, 0)
    if receipt != _update_tape_receipt(AddressTape(unit_id, root), 0):
        gate_issues["P3"].append("address tape is not independently reproducible")
    proof = _synthetic_barrier_proof(models, optimizers, learner_states, learner_rng_states)
    if not proof["first_batch_byte_identity"] or not proof["first_oracle_successor_identity"] or not proof["post_first_collector_parameter_divergence"]:
        gate_issues["P4"].append("dual barrier/first successor proof failed")
    if not proof["finite_actor_gradients"] or not proof["oracle_magnitude_identity"]:
        gate_issues["P5"].append("finite activity or oracle coefficient proof failed")
    if not all(_observation_firewall(_synthetic_history(cue, owner_epoch=f"P6-{cue}")) for cue in (0, 1)):
        gate_issues["P6"].append("oracle observation firewall failed")
    if not all(_schedule_contract(_schedule(unit, decimal_root)) for unit, decimal_root in B4_UNITS):
        gate_issues["P7"].append("balanced 128x8 dual-collector schedule failed")
    if not b2._evaluator_sentinels()["valid"]:
        gate_issues["P8"].append("evaluator sentinel failed")
    if manifest.get("tape", {}).get("kinds") != list(B4_TAPE_KINDS):  # type: ignore[union-attr]
        gate_issues["P9"].append("tape allow-list mismatch")
    if manifest.get("evidence_complexity") != {"H": 4, "K_search": 0, "hypothetical_transitions": 0}:
        gate_issues["P10"].append("evidence complexity bound mismatch")
    if tuple(manifest.get("branches", ())) != B4_BRANCH_PRECEDENCE:
        gate_issues["P11"].append("branch literals or precedence mismatch")
    report = {
        "artifact_kind": "vsp02_b4_preflight",
        "assignment_id": B4_ASSIGNMENT_ID,
        "manifest_identity": manifest_identity(manifest),
        "gates": {gate: {"passed": not issues, "issues": issues} for gate, issues in gate_issues.items()},
        "all_passed": not any(gate_issues.values()),
        "initial_complete_state_hashes": initial_complete,
        "initial_parameter_hashes": initial_parameters,
        "initial_optimizer_hashes": initial_optimizers,
        "initial_recurrent_and_state_hashes": recurrent,
        "initial_carried_learner_state_hashes": {
            arm: digest(_initial_carried_learner_state()) for arm in B4_ARMS
        },
        "initial_registered_learner_rng_state_hashes": {
            arm: digest(base_learner_rng) for arm in B4_ARMS
        },
        "architectures": {arm: _architecture_payload(model) for arm, model in models.items()},
        "seed_and_tape": roots,
        "address_tape_recreation_receipt": receipt,
        "dual_collector_barrier_proof": proof,
        "oracle_firewall": True,
        "activity": _zero_activity(),
    }
    report["evidence_digest"] = digest(report)
    return report


def validate_preflight_evidence(manifest: Mapping[str, object], preflight: Mapping[str, object]) -> tuple[str, ...]:
    """Pure retained validation; constructs no model, host, optimizer, or evaluator."""
    issues: list[str] = []
    if preflight.get("artifact_kind") != "vsp02_b4_preflight" or preflight.get("assignment_id") != B4_ASSIGNMENT_ID:
        issues.append("preflight identity mismatch")
    if preflight.get("manifest_identity") != manifest_identity(manifest):
        issues.append("preflight manifest binding mismatch")
    unsigned = dict(preflight)
    retained_digest = unsigned.pop("evidence_digest", None)
    if retained_digest != digest(unsigned):
        issues.append("preflight artifact mutation or evidence digest mismatch")
    gates = preflight.get("gates")
    if not isinstance(gates, Mapping) or tuple(sorted(gates, key=lambda value: int(str(value)[1:]))) != tuple(f"P{i}" for i in range(12)):
        issues.append("P0-P11 gate set mismatch")
    else:
        passes: list[bool] = []
        for gate in (f"P{i}" for i in range(12)):
            evidence = gates[gate]
            if not isinstance(evidence, Mapping) or not isinstance(evidence.get("issues"), list):
                issues.append(f"{gate} schema mismatch")
                continue
            expected = not evidence["issues"]
            if evidence.get("passed") is not expected:
                issues.append(f"{gate} passed flag mismatch")
            passes.append(expected)
        if preflight.get("all_passed") is not all(passes):
            issues.append("preflight all_passed mismatch")
    for name in (
        "initial_complete_state_hashes", "initial_parameter_hashes", "initial_optimizer_hashes",
        "initial_recurrent_and_state_hashes", "initial_carried_learner_state_hashes",
        "initial_registered_learner_rng_state_hashes",
    ):
        mapping = preflight.get(name)
        if not isinstance(mapping, Mapping) or set(mapping) != set(B4_ARMS) or len(set(mapping.values())) != 1:
            issues.append(f"preflight {name} equality mismatch")
    proof = preflight.get("dual_collector_barrier_proof")
    if not isinstance(proof, Mapping) or any(proof.get(key) is not True for key in (
        "synthetic_only", "complete_batches_frozen_before_updates", "first_batch_byte_identity",
        "first_oracle_successor_identity", "post_first_collector_parameter_divergence",
        "finite_actor_gradients", "oracle_magnitude_identity",
    )):
        issues.append("preflight dual collector proof mismatch")
    if preflight.get("activity") != _zero_activity():
        issues.append("preflight has scientific activity")
    return tuple(issues)


def _batch_exposure_signature(row: Mapping[str, object]) -> str:
    return digest({
        "action": row.get("A_behavior"),
        "rewards": row.get("R"),
        "return": row.get("G"),
        "environment_transitions": row.get("environment_transitions"),
    })


def _state_hashes(
    models: Mapping[str, b1.GRUActorCritic],
    optimizers: Mapping[str, torch.optim.Optimizer],
    learner_states: Mapping[str, Mapping[str, object]],
    learner_rng_states: Mapping[str, Mapping[str, object]],
) -> dict[str, str]:
    return {
        arm: _complete_state_hash(models[arm], optimizers[arm], learner_states[arm], learner_rng_states[arm])
        for arm in B4_ARMS
    }


def _train_unit(unit_id: str, root: int) -> dict[str, object]:
    schedule = _schedule(unit_id, root)
    if not _schedule_contract(schedule):
        raise RuntimeError("schedule contract failed")
    tape = AddressTape(unit_id, root)
    models, optimizers = _new_learners(unit_id, root)
    learner_states = {arm: deepcopy(_initial_carried_learner_state()) for arm in B4_ARMS}
    base_learner_rng = _initial_learner_rng_state(unit_id, root)
    learner_rng_states = {arm: deepcopy(base_learner_rng) for arm in B4_ARMS}
    initial_complete = _state_hashes(models, optimizers, learner_states, learner_rng_states)
    initial_parameters = {arm: digest(model_payload(models[arm])) for arm in B4_ARMS}
    initial_optimizers = {arm: digest(optimizer_payload(optimizers[arm])) for arm in B4_ARMS}
    updates: dict[str, list[dict[str, object]]] = {arm: [] for arm in B4_ARMS}
    batch_records: list[dict[str, object]] = []
    barrier_receipts: list[dict[str, object]] = []
    transitions = 0
    first_later_row_divergence: dict[str, object] | None = None
    first_oracle_successor_identity = False
    post_first_collector_parameter_divergence = False
    for update_index in range(B4_UPDATES_PER_UNIT):
        scheduled_rows = schedule[update_index * B4_BATCH_SIZE : (update_index + 1) * B4_BATCH_SIZE]
        tape_receipt = _update_tape_receipt(tape, update_index)
        tape_digest_before = digest(tape_receipt)
        collector_state_before = _state_hashes(models, optimizers, learner_states, learner_rng_states)
        generator_batch, generator_transitions = _collect_batch(
            unit_id=unit_id, update_index=update_index, rows=scheduled_rows,
            model=models["RL_ORIGINAL_GENERATOR"], tape=tape,
        )
        state_after_generator_collection = _state_hashes(models, optimizers, learner_states, learner_rng_states)
        self_batch, self_transitions = _collect_batch(
            unit_id=unit_id, update_index=update_index, rows=scheduled_rows,
            model=models["CREDIT_SIGN_SELF_FEEDBACK"], tape=tape,
        )
        state_after_both_collections = _state_hashes(models, optimizers, learner_states, learner_rng_states)
        if collector_state_before != state_after_generator_collection or collector_state_before != state_after_both_collections:
            raise RuntimeError("collector mutated learner/optimizer/successor state")
        generator_digest, self_digest = digest(generator_batch), digest(self_batch)
        generator_rows = [digest(row) for row in generator_batch]
        self_rows = [digest(row) for row in self_batch]
        if update_index == 0 and canonical_bytes(generator_batch) != canonical_bytes(self_batch):
            raise RuntimeError("first collector batches are not byte-identical")
        if update_index > 0 and first_later_row_divergence is None:
            for row_index, (generator_row, own_row) in enumerate(zip(generator_batch, self_batch)):
                if _batch_exposure_signature(generator_row) != _batch_exposure_signature(own_row):
                    first_later_row_divergence = {
                        "update_index": update_index,
                        "row_index": row_index,
                        "generator_signature": _batch_exposure_signature(generator_row),
                        "self_feedback_signature": _batch_exposure_signature(own_row),
                        "action_diverged": generator_row["A_behavior"] != own_row["A_behavior"],
                        "environment_transition_row_diverged": any(
                            generator_row[field] != own_row[field]
                            for field in ("R", "G", "environment_transitions")
                        ),
                    }
                    break
        order = list(tape_receipt["minibatch_order"])
        ordered_generator = [generator_batch[index] for index in order]
        ordered_self = [self_batch[index] for index in order]
        frozen_before_updates = {
            "generator_batch": digest(generator_batch),
            "self_feedback_batch": digest(self_batch),
            "tape": tape_digest_before,
        }
        pre_update_states = _state_hashes(models, optimizers, learner_states, learner_rng_states)
        generator_update = _optimizer_step(
            "RL_ORIGINAL_GENERATOR", models["RL_ORIGINAL_GENERATOR"], optimizers["RL_ORIGINAL_GENERATOR"], ordered_generator
        )
        learner_states["RL_ORIGINAL_GENERATOR"] = _advance_carried_learner_state(
            learner_states["RL_ORIGINAL_GENERATOR"], update_index=update_index,
            batch_digest=generator_digest, batch_order=order,
        )
        after_generator_states = _state_hashes(models, optimizers, learner_states, learner_rng_states)
        if any(after_generator_states[arm] != pre_update_states[arm] for arm in B4_ARMS[1:]):
            raise RuntimeError("generator update contaminated an oracle-sign arm")
        shadow_update = _optimizer_step(
            "CREDIT_SIGN_SHADOW", models["CREDIT_SIGN_SHADOW"], optimizers["CREDIT_SIGN_SHADOW"], ordered_generator
        )
        learner_states["CREDIT_SIGN_SHADOW"] = _advance_carried_learner_state(
            learner_states["CREDIT_SIGN_SHADOW"], update_index=update_index,
            batch_digest=generator_digest, batch_order=order,
        )
        after_shadow_states = _state_hashes(models, optimizers, learner_states, learner_rng_states)
        if after_shadow_states["RL_ORIGINAL_GENERATOR"] != after_generator_states["RL_ORIGINAL_GENERATOR"] or after_shadow_states["CREDIT_SIGN_SELF_FEEDBACK"] != after_generator_states["CREDIT_SIGN_SELF_FEEDBACK"]:
            raise RuntimeError("shadow update contaminated generator or self-feedback arm")
        self_update = _optimizer_step(
            "CREDIT_SIGN_SELF_FEEDBACK", models["CREDIT_SIGN_SELF_FEEDBACK"], optimizers["CREDIT_SIGN_SELF_FEEDBACK"], ordered_self
        )
        learner_states["CREDIT_SIGN_SELF_FEEDBACK"] = _advance_carried_learner_state(
            learner_states["CREDIT_SIGN_SELF_FEEDBACK"], update_index=update_index,
            batch_digest=self_digest, batch_order=order,
        )
        after_self_states = _state_hashes(models, optimizers, learner_states, learner_rng_states)
        if after_self_states["RL_ORIGINAL_GENERATOR"] != after_shadow_states["RL_ORIGINAL_GENERATOR"] or after_self_states["CREDIT_SIGN_SHADOW"] != after_shadow_states["CREDIT_SIGN_SHADOW"]:
            raise RuntimeError("self-feedback update contaminated generator or shadow arm")
        frozen_after_updates = {
            "generator_batch": digest(generator_batch),
            "self_feedback_batch": digest(self_batch),
            "tape": digest(_update_tape_receipt(AddressTape(unit_id, root), update_index)),
        }
        if frozen_before_updates != frozen_after_updates:
            raise RuntimeError("batch or immutable address tape changed across update phase")
        for arm, update, batch_digest in (
            ("RL_ORIGINAL_GENERATOR", generator_update, generator_digest),
            ("CREDIT_SIGN_SHADOW", shadow_update, generator_digest),
            ("CREDIT_SIGN_SELF_FEEDBACK", self_update, self_digest),
        ):
            update.update({"update_index": update_index, "batch_digest": batch_digest, "batch_order": order})
            updates[arm].append(update)
        if update_index == 0:
            first_oracle_successor_identity = after_self_states["CREDIT_SIGN_SHADOW"] == after_self_states["CREDIT_SIGN_SELF_FEEDBACK"]
            post_first_collector_parameter_divergence = generator_update["parameters_after"] != self_update["parameters_after"]
            if not first_oracle_successor_identity:
                raise RuntimeError("oracle-sign first successor complete states differ")
            if not post_first_collector_parameter_divergence:
                raise RuntimeError("post-first-update collector parameters did not diverge")
        batch_records.append({
            "update_index": update_index,
            "generator_batch_id": f"{B4_ASSIGNMENT_ID}/{unit_id}/U{update_index:03d}/RL_ORIGINAL_GENERATOR/BATCH",
            "self_feedback_batch_id": f"{B4_ASSIGNMENT_ID}/{unit_id}/U{update_index:03d}/CREDIT_SIGN_SELF_FEEDBACK/BATCH",
            "generator_batch_digest": generator_digest,
            "self_feedback_batch_digest": self_digest,
            "generator_ordered_row_digests": generator_rows,
            "self_feedback_ordered_row_digests": self_rows,
            "first_batch_byte_identity": update_index == 0 and generator_digest == self_digest and generator_rows == self_rows,
            "generator_rows": generator_batch,
            "self_feedback_rows": self_batch,
            "generator_environment_transitions": generator_transitions,
            "self_feedback_environment_transitions": self_transitions,
        })
        barrier_receipts.append({
            "update_index": update_index,
            "phase_order": ["COLLECT_GENERATOR_COMPLETE", "COLLECT_SELF_COMPLETE", *[f"UPDATE_{arm}" for arm in FIXED_UPDATE_ORDER]],
            "both_batches_frozen_before_any_update": True,
            "collector_state_before": collector_state_before,
            "state_after_generator_collection": state_after_generator_collection,
            "state_after_both_collections": state_after_both_collections,
            "pre_update_states": pre_update_states,
            "after_generator_states": after_generator_states,
            "after_shadow_states": after_shadow_states,
            "after_self_states": after_self_states,
            "frozen_before_updates": frozen_before_updates,
            "frozen_after_updates": frozen_after_updates,
            "collector_optimizer_successor_noninterference": True,
            "rng_noninterference": "NO_MUTABLE_RNG_EXISTS",
            "tape_batch_noninterference": True,
        })
        transitions += generator_transitions + self_transitions
    exposure = {
        "post_first_update_collector_parameter_divergence": post_first_collector_parameter_divergence,
        "first_oracle_successor_complete_state_identity": first_oracle_successor_identity,
        "later_action_or_environment_transition_row_divergence": first_later_row_divergence is not None,
        "first_later_divergence": first_later_row_divergence,
    }
    return {
        "unit_id": unit_id,
        "decimal_root": root,
        "models": models,
        "training": {
            "real_training_episodes": 2 * len(schedule),
            "episodes_by_collector": {collector: len(schedule) for collector in B4_COLLECTORS},
            "environment_transitions": transitions,
            "cue_counts_by_collector": {collector: {"0": 512, "1": 512} for collector in B4_COLLECTORS},
            "updates_per_arm": {arm: len(updates[arm]) for arm in B4_ARMS},
            "initial_complete_state_hashes": initial_complete,
            "initial_parameter_hashes": initial_parameters,
            "initial_optimizer_hashes": initial_optimizers,
            "initial_recurrent_and_state_hashes": {arm: digest(_initial_recurrent_state()) for arm in B4_ARMS},
            "initial_carried_learner_state_hashes": {
                arm: digest(_initial_carried_learner_state()) for arm in B4_ARMS
            },
            "initial_registered_learner_rng_state_hashes": {
                arm: digest(base_learner_rng) for arm in B4_ARMS
            },
            "final_complete_state_hashes": _state_hashes(models, optimizers, learner_states, learner_rng_states),
            "final_parameter_hashes": {arm: digest(model_payload(models[arm])) for arm in B4_ARMS},
            "final_model_states": {arm: model_payload(models[arm]) for arm in B4_ARMS},
            "final_optimizer_states": {arm: optimizer_payload(optimizers[arm]) for arm in B4_ARMS},
            "final_carried_learner_states": learner_states,
            "final_registered_learner_rng_states": learner_rng_states,
            "batch_records": batch_records,
            "barrier_receipts": barrier_receipts,
            "feedback_exposure": exposure,
            "updates": updates,
            "tape_identity": tape.identity(),
            "mutable_rng_objects": 0,
            "learner_stochasticity_draw_counts": {arm: 0 for arm in B4_ARMS},
            "unlisted_rng_draws": 0,
            "behavior_mixture_route": BEHAVIOR_MIXTURE_ROUTE,
            "mediators_only": {
                "action_and_history_occupancy": True,
                "correctness_class_exposure": True,
                "credit_density": True,
                "absolute_advantage_mean_and_variance": True,
                "critic_targets": True,
                "route_separated_gradient_norms": True,
                "pre_clip_norm_clip_flag_and_factor": True,
                "adam_transitions": True,
            },
        },
    }


def _evaluation_panel(unit_id: str, root: int) -> list[dict[str, object]]:
    tape = AddressTape(unit_id, root)
    base_cues = [0] * 64 + [1] * 64
    order = _ranked_permutation(tape, "evaluation_cue_schedule", "FINAL", 128)
    cues = [base_cues[index] for index in order]
    return [
        {
            "clone_id": f"{unit_id}/EVAL/{index:03d}",
            "owner_epoch": f"{unit_id}-EV-{index:03d}",
            "true_cue": cue,
            "event_tape_token": tape.token("evaluation_environment_randomness", index),
        }
        for index, cue in enumerate(cues)
    ]


def _evaluate_arm_unit(*, unit_id: str, arm: str, model: b1.GRUActorCritic, panel: Sequence[Mapping[str, object]]) -> dict[str, object]:
    release_by_cue: dict[int, list[float]] = {0: [], 1: []}
    choices: dict[int, list[str | None]] = {0: [], 1: []}
    records: list[dict[str, object]] = []
    transitions = 0
    for index, row in enumerate(panel):
        cue = int(row["true_cue"])
        host = B4LifecycleHost()
        cue_observation = host.reset(
            lifecycle_id=f"{B4_ASSIGNMENT_ID}/{unit_id}/{arm}/EVAL/{index:03d}/{row['event_tape_token']}",
            owner_epoch=str(row["owner_epoch"]), true_cue=cue, presented_cue=cue,
        )
        observations = [asdict(cue_observation), asdict(host.decision_observation())]
        with torch.no_grad():
            logits, raw, probabilities, _, _ = _forward(model, observations)
        if not torch.isfinite(logits).all() or not torch.isfinite(raw).all() or not torch.isfinite(probabilities).all():
            raise RuntimeError("nonfinite evaluation")
        q_release, q_hold = (float(value) for value in raw)
        choice = b1.Action.RELEASE.value if q_release > q_hold else b1.Action.HOLD.value if q_hold > q_release else None
        release_by_cue[cue].append(q_release)
        choices[cue].append(choice)
        executed = b1.Action(choice) if choice is not None else b1.Action.HOLD
        episode = host.step(executed, action_probabilities=[float(value) for value in probabilities])
        transitions += int(episode["environment_transitions"])
        records.append({
            "clone_id": row["clone_id"], "owner_epoch": row["owner_epoch"],
            "event_tape_token": row["event_tape_token"], "true_cue": cue,
            "logits": [float(value) for value in logits],
            "raw_softmax": [float(value) for value in raw], "behavior_probabilities": [float(value) for value in probabilities],
            "argmax_action": choice, "environment_transitions": int(episode["environment_transitions"]),
        })
    q0, q1 = sum(release_by_cue[0]) / 64, sum(release_by_cue[1]) / 64
    ties = sum(value is None for values in choices.values() for value in values)
    exact = all(value == b1.Action.HOLD.value for value in choices[0]) and all(value == b1.Action.RELEASE.value for value in choices[1])
    return {
        "unit_id": unit_id,
        "arm": arm,
        "checkpoint_id": f"{B4_ASSIGNMENT_ID}/{unit_id}/{arm}/FINAL-128",
        "panel_digest": digest(panel),
        "episodes": 128,
        "cue_counts": {"0": 64, "1": 64},
        "environment_transitions": transitions,
        "finite_logits": True,
        "argmax_ties": ties,
        "exact_correct_unit": exact and ties == 0,
        "q_0": q0,
        "q_1": q1,
        **_mixture_metrics_from_raw_q(q0=q0, q1=q1),
        "evaluation_updates": 0,
        "stochastic_action_draws": 0,
        "clone_records": records,
        "final_model_hash": digest(model_payload(model)),
    }


def _arm_aggregate(metrics: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        "units": len(metrics),
        "exact_correct_units": sum(bool(metric["exact_correct_unit"]) for metric in metrics),
        "mean_j_eval": sum(float(metric["j_eval"]) for metric in metrics) / len(metrics),
        "mean_kappa": sum(float(metric["kappa"]) for metric in metrics) / len(metrics),
    }


def _derive_retained_evaluation_metric(
    *,
    unit_id: str,
    root: int,
    arm: str,
    metric: Mapping[str, object],
    expected_final_hash: object,
) -> tuple[dict[str, object] | None, list[str], int, str | None, set[str]]:
    """Purely derive every evaluation projection from retained clone rows."""

    issues: list[str] = []
    records = metric.get("clone_records")
    if not isinstance(records, list) or len(records) != B4_EVAL_EPISODES_PER_UNIT_ARM:
        return None, [f"{unit_id}/{arm} retained evaluation rows invalid"], 0, None, set()
    expected_panel = _evaluation_panel(unit_id, root)
    reconstructed_panel: list[dict[str, object]] = []
    release_by_cue: dict[int, list[float]] = {0: [], 1: []}
    choices: dict[int, list[str | None]] = {0: [], 1: []}
    clone_ids: set[str] = set()
    transitions = 0
    expected_record_keys = {
        "clone_id", "owner_epoch", "event_tape_token", "true_cue", "logits", "raw_softmax",
        "behavior_probabilities", "argmax_action", "environment_transitions",
    }
    for index, record in enumerate(records):
        if not isinstance(record, Mapping) or set(record) != expected_record_keys:
            issues.append(f"{unit_id}/{arm}/{index} evaluation row schema mismatch")
            continue
        try:
            cue = int(record["true_cue"])
            logits = [float(value) for value in record["logits"]]  # type: ignore[arg-type]
            raw = [float(value) for value in record["raw_softmax"]]  # type: ignore[arg-type]
            probabilities = [float(value) for value in record["behavior_probabilities"]]  # type: ignore[arg-type]
            row_transitions = int(record["environment_transitions"])
        except (TypeError, ValueError):
            issues.append(f"{unit_id}/{arm}/{index} evaluation row scalar mismatch")
            continue
        if cue not in (0, 1) or len(logits) != 2 or len(raw) != 2 or len(probabilities) != 2:
            issues.append(f"{unit_id}/{arm}/{index} evaluation row shape/cue mismatch")
            continue
        if any(not math.isfinite(value) for value in (*logits, *raw, *probabilities)):
            issues.append(f"{unit_id}/{arm}/{index} nonfinite evaluation value")
            continue
        maximum = max(logits)
        exponentials = [math.exp(value - maximum) for value in logits]
        normalizer = sum(exponentials)
        expected_raw = [value / normalizer for value in exponentials]
        if any(not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12) for actual, expected in zip(raw, expected_raw)):
            issues.append(f"{unit_id}/{arm}/{index} raw softmax projection mismatch")
        expected_probabilities = [0.8 * value + 0.1 for value in raw]
        if any(not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12) for actual, expected in zip(probabilities, expected_probabilities)):
            issues.append(f"{unit_id}/{arm}/{index} behavior mixture projection mismatch")
        choice = (
            b1.Action.RELEASE.value if raw[0] > raw[1]
            else b1.Action.HOLD.value if raw[1] > raw[0]
            else None
        )
        if record.get("argmax_action") != choice:
            issues.append(f"{unit_id}/{arm}/{index} deterministic argmax mismatch")
        expected_transitions = 4 if choice == b1.Action.RELEASE.value else 5
        if row_transitions != expected_transitions:
            issues.append(f"{unit_id}/{arm}/{index} evaluation transition mismatch")
        panel_row = {
            "clone_id": record["clone_id"],
            "owner_epoch": record["owner_epoch"],
            "true_cue": cue,
            "event_tape_token": record["event_tape_token"],
        }
        reconstructed_panel.append(panel_row)
        if panel_row != expected_panel[index]:
            issues.append(f"{unit_id}/{arm}/{index} evaluation row identity mismatch")
        clone_id = str(record["clone_id"])
        if clone_id in clone_ids:
            issues.append(f"{unit_id}/{arm}/{index} duplicate evaluation clone")
        clone_ids.add(clone_id)
        release_by_cue[cue].append(raw[0])
        choices[cue].append(choice)
        transitions += row_transitions
    if len(reconstructed_panel) != 128 or any(len(release_by_cue[cue]) != 64 for cue in (0, 1)):
        return None, issues + [f"{unit_id}/{arm} evaluation cue/row support mismatch"], transitions, None, clone_ids
    q0 = sum(release_by_cue[0]) / 64
    q1 = sum(release_by_cue[1]) / 64
    mixture = _mixture_metrics_from_raw_q(q0=q0, q1=q1)
    ties = sum(choice is None for values in choices.values() for choice in values)
    exact = (
        ties == 0
        and all(choice == b1.Action.HOLD.value for choice in choices[0])
        and all(choice == b1.Action.RELEASE.value for choice in choices[1])
    )
    panel_digest = digest(reconstructed_panel)
    derived = {
        "unit_id": unit_id,
        "arm": arm,
        "checkpoint_id": f"{B4_ASSIGNMENT_ID}/{unit_id}/{arm}/FINAL-128",
        "panel_digest": panel_digest,
        "episodes": len(records),
        "cue_counts": {"0": len(release_by_cue[0]), "1": len(release_by_cue[1])},
        "environment_transitions": transitions,
        "finite_logits": True,
        "argmax_ties": ties,
        "exact_correct_unit": exact,
        "q_0": q0,
        "q_1": q1,
        **mixture,
        "evaluation_updates": 0,
        "stochastic_action_draws": 0,
        "final_model_hash": expected_final_hash,
    }
    if set(metric) != set(derived) | {"clone_records"}:
        issues.append(f"{unit_id}/{arm} evaluation metric schema mismatch")
    for key, expected in derived.items():
        actual = metric.get(key)
        if isinstance(expected, float):
            if not math.isclose(float(actual) if isinstance(actual, (int, float)) else math.nan, expected, rel_tol=0.0, abs_tol=1e-12):
                issues.append(f"{unit_id}/{arm} {key} projection mismatch")
        elif actual != expected:
            issues.append(f"{unit_id}/{arm} {key} projection mismatch")
    return derived, issues, transitions, panel_digest, clone_ids


def classify_b4(*, valid: bool, aggregates: Mapping[str, Mapping[str, object]] | None, feedback_exposure_valid: bool) -> str:
    if not valid or aggregates is None:
        return "B4_INCONCLUSIVE_OR_INVALID"
    generator = aggregates["RL_ORIGINAL_GENERATOR"]
    shadow = aggregates["CREDIT_SIGN_SHADOW"]
    self_feedback = aggregates["CREDIT_SIGN_SELF_FEEDBACK"]
    if (
        self_feedback["exact_correct_units"] == 5
        and shadow["exact_correct_units"] == 0
        and generator["exact_correct_units"] == 0
        and float(self_feedback["mean_j_eval"]) - 1.0 > 0.05
        and float(self_feedback["mean_kappa"]) >= 0.70
        and feedback_exposure_valid
    ):
        return "B4_FEEDBACK_LOCAL_SUFFICIENCY"
    if all(aggregates[arm]["exact_correct_units"] == 0 for arm in B4_ARMS) and feedback_exposure_valid:
        return "B4_FEEDBACK_LOCAL_INSUFFICIENT"
    return "B4_INCONCLUSIVE_OR_INVALID"


def _zero_activity() -> dict[str, int]:
    return {
        "result_bearing_runs": 0, "real_training_episodes": 0, "evaluation_episodes": 0,
        "environment_transitions": 0, "optimizer_updates": 0, "checkpoints_total": 0,
        "retries_rescues_sweeps": 0,
    }


def _resource_usage_evidence(
    *, cpu_start_seconds: float, cpu_end_seconds: float, peak_rss_samples_bytes: Sequence[int]
) -> dict[str, object]:
    values = tuple(int(value) for value in peak_rss_samples_bytes)
    if (
        not math.isfinite(cpu_start_seconds)
        or not math.isfinite(cpu_end_seconds)
        or cpu_end_seconds < cpu_start_seconds
        or not values
        or any(value < 0 for value in values)
    ):
        raise ValueError("invalid process resource measurement")
    cpu_seconds = cpu_end_seconds - cpu_start_seconds
    cpu_minutes = cpu_seconds / 60.0
    peak_bytes = max(values)
    peak_gib = peak_bytes / float(1024**3)
    return {
        "measurement_scope": "registered train_and_evaluate process work only",
        "cpu_clock": "time.process_time",
        "peak_memory_measure": "lifetime process peak resident_or_working_set",
        "cpu_start_seconds": cpu_start_seconds,
        "cpu_end_seconds": cpu_end_seconds,
        "cpu_seconds": cpu_seconds,
        "cpu_minutes": cpu_minutes,
        "cpu_minutes_cap": B4_CAPS["cpu_minutes"],
        "peak_process_rss_samples_bytes": list(values),
        "peak_process_rss_bytes": peak_bytes,
        "peak_process_memory_gib": peak_gib,
        "peak_process_memory_gib_cap": B4_CAPS["peak_memory_gib"],
        "cpu_within_cap": cpu_minutes <= B4_CAPS["cpu_minutes"],
        "peak_memory_within_cap": peak_gib <= B4_CAPS["peak_memory_gib"],
        "all_resource_caps_passed": (
            cpu_minutes <= B4_CAPS["cpu_minutes"] and peak_gib <= B4_CAPS["peak_memory_gib"]
        ),
    }


def run_treatment(manifest: Mapping[str, object], *, repo_root: Path | None = None) -> dict[str, object]:
    preflight = preflight_report(manifest, repo_root=repo_root)
    base: dict[str, object] = {
        "artifact_kind": "vsp02_b4_result", "assignment_id": B4_ASSIGNMENT_ID,
        "direction_id": B4_DIRECTION_ID, "candidate": B4_CANDIDATE,
        "manifest": dict(manifest), "manifest_identity": manifest_identity(manifest), "preflight": preflight,
    }
    if not preflight["all_passed"]:
        result = {
            **base, "branch": "B4_INCONCLUSIVE_OR_INVALID", "activity": _zero_activity(),
            "activity_valid": False, "feedback_exposure_valid": False,
            "resource_usage": None, "runtime_contract": None, "units": [], "aggregates": None, "evaluation": None,
        }
        result["evidence_digest"] = digest(result)
        return result
    if manifest.get("technical_only") is not False or manifest.get("run_id") != B4_RUN_ID:
        raise ValueError("treatment requires the registered technical_only=false manifest")
    cpu_start = _cpu_time_seconds()
    peak_rss_start = _peak_process_rss_bytes()
    units = [_train_unit(unit, root) for unit, root in B4_UNITS]
    evaluations: dict[str, list[dict[str, object]]] = {arm: [] for arm in B4_ARMS}
    evaluation_transitions = 0
    for unit in units:
        unit_id, root = str(unit["unit_id"]), int(unit["decimal_root"])
        panel_digests: list[str] = []
        models = unit.pop("models")
        for arm in B4_ARMS:
            panel = _evaluation_panel(unit_id, root)  # independently recreated for every arm
            panel_digests.append(digest(panel))
            metric = _evaluate_arm_unit(unit_id=unit_id, arm=arm, model=models[arm], panel=panel)
            evaluations[arm].append(metric)
            evaluation_transitions += int(metric["environment_transitions"])
        if len(set(panel_digests)) != 1:
            raise RuntimeError("independently recreated common evaluation panels differ")
        unit["evaluation_panel_digests"] = panel_digests
    cpu_end = _cpu_time_seconds()
    peak_rss_end = _peak_process_rss_bytes()
    resource_usage = _resource_usage_evidence(
        cpu_start_seconds=cpu_start,
        cpu_end_seconds=cpu_end,
        peak_rss_samples_bytes=(peak_rss_start, peak_rss_end),
    )
    aggregates = {arm: _arm_aggregate(metrics) for arm, metrics in evaluations.items()}
    exposure_valid = all(
        unit["training"]["feedback_exposure"]["post_first_update_collector_parameter_divergence"]
        and unit["training"]["feedback_exposure"]["first_oracle_successor_complete_state_identity"]
        and unit["training"]["feedback_exposure"]["later_action_or_environment_transition_row_divergence"]
        for unit in units
    )
    training_transitions = sum(int(unit["training"]["environment_transitions"]) for unit in units)
    activity = {
        "result_bearing_runs": 1,
        "real_training_episodes": 10_240,
        "evaluation_episodes": 1_920,
        "environment_transitions": training_transitions + evaluation_transitions,
        "optimizer_updates": 1_920,
        "checkpoints_total": 15,
        "retries_rescues_sweeps": 0,
    }
    finite_activity = all(
        math.isfinite(float(update[field]))
        for unit in units
        for arm in B4_ARMS
        for update in unit["training"]["updates"][arm]
        for field in (
            "loss", "actor_loss", "policy_actor_loss", "entropy_loss", "critic_loss",
            "gradient_norm_before_clip", "combined_gradient_norm_before_clip", "actor_gradient_norm",
            "entropy_gradient_norm", "critic_gradient_norm",
        )
    )
    valid = (
        exposure_valid
        and finite_activity
        and activity["environment_transitions"] <= B4_CAPS["environment_transitions_total"]
        and activity["real_training_episodes"] == B4_CAPS["real_training_episodes_total"]
        and activity["evaluation_episodes"] == B4_CAPS["evaluation_episodes_total"]
        and activity["optimizer_updates"] == B4_CAPS["optimizer_updates_total"]
        and activity["checkpoints_total"] == B4_CAPS["checkpoints_total"]
        and activity["result_bearing_runs"] == B4_CAPS["result_bearing_runs"]
        and resource_usage["all_resource_caps_passed"] is True
    )
    result = {
        **base,
        "branch": classify_b4(valid=valid, aggregates=aggregates, feedback_exposure_valid=exposure_valid),
        "activity": activity,
        "resource_usage": resource_usage,
        "activity_valid": valid,
        "feedback_exposure_valid": exposure_valid,
        "runtime_contract": {
            "arms": list(B4_ARMS),
            "sole_intervention_edge": "oracle-sign learner parameters -> its future batch source",
            "not_on_policy": True,
            "dual_collector_phase_barrier": True,
            "fixed_update_order": list(FIXED_UPDATE_ORDER),
            "immutable_address_indexed_tape_no_mutable_rng": True,
            "first_batch_byte_identity": True,
            "first_oracle_successor_complete_state_identity": True,
            "shadow_exact_generator_batch_bytes_and_order": True,
            "collector_optimizer_rng_tape_batch_successor_noninterference": True,
            "oracle_scalar_only": True,
            "actor_critic_gru_entropy_adam_clip_mask_return_evaluation_invariant": True,
            "mediators_not_branch_conditions": True,
            "resource_caps_branch_bearing": True,
            "cpu_minutes_cap": 30,
            "peak_process_memory_gib_cap": 2,
        },
        "units": units,
        "aggregates": aggregates,
        "evaluation": evaluations,
        "nonclaims": list(manifest["nonclaims"]),
    }
    result["evidence_digest"] = digest(result)
    return result


def validate_result(manifest: object, result: object, *, repo_root: Path | None = None) -> tuple[str, ...]:
    """Validate retained rows and receipts without invoking any runtime surface."""
    issues = list(validate_manifest(manifest))
    if not isinstance(manifest, Mapping) or not isinstance(result, Mapping):
        return tuple(issues + ["manifest/result must be objects"])
    if result.get("artifact_kind") != "vsp02_b4_result" or result.get("assignment_id") != B4_ASSIGNMENT_ID or result.get("direction_id") != B4_DIRECTION_ID or result.get("candidate") != B4_CANDIDATE:
        issues.append("result identity mismatch")
    if result.get("manifest") != manifest or result.get("manifest_identity") != manifest_identity(manifest):
        issues.append("result manifest binding mismatch")
    unsigned = dict(result)
    retained_digest = unsigned.pop("evidence_digest", None)
    if retained_digest != digest(unsigned):
        issues.append("retained artifact mutation or evidence digest mismatch")
    preflight = result.get("preflight")
    if not isinstance(preflight, Mapping):
        return tuple(issues + ["preflight evidence missing"])
    issues.extend(validate_preflight_evidence(manifest, preflight))
    if preflight.get("all_passed") is False:
        if (
            result.get("branch") != "B4_INCONCLUSIVE_OR_INVALID" or result.get("activity") != _zero_activity()
            or result.get("activity_valid") is not False or result.get("feedback_exposure_valid") is not False
            or result.get("resource_usage") is not None or result.get("runtime_contract") is not None or result.get("units") != []
            or result.get("aggregates") is not None or result.get("evaluation") is not None
        ):
            issues.append("failed-construction result must be zero-activity B4_INCONCLUSIVE_OR_INVALID")
        return tuple(issues)
    if result.get("branch") not in B4_BRANCH_PRECEDENCE:
        issues.append("unknown B4 branch")
    if manifest.get("technical_only") is not False or manifest.get("run_id") != B4_RUN_ID:
        issues.append("runtime result requires exact registered full manifest")
        return tuple(issues)
    units = result.get("units")
    evaluations = result.get("evaluation")
    if not isinstance(units, list) or len(units) != 5:
        issues.append("exactly five fresh unit records required")
    if not isinstance(evaluations, Mapping) or set(evaluations) != set(B4_ARMS) or any(not isinstance(evaluations.get(arm), list) or len(evaluations[arm]) != 5 for arm in B4_ARMS):
        issues.append("exactly fifteen arm/unit evaluations required")
    training_transitions = 0
    exposure_by_unit: dict[str, bool] = {}
    final_hashes_by_unit: dict[str, Mapping[str, object]] = {}
    train_clone_ids_by_unit: dict[str, set[str]] = {}
    if isinstance(units, list):
        for index, expected in enumerate(B4_UNITS):
            if index >= len(units) or not isinstance(units[index], Mapping):
                continue
            unit = units[index]
            training = unit.get("training")
            if (unit.get("unit_id"), unit.get("decimal_root")) != expected or not isinstance(training, Mapping):
                issues.append(f"unit {index} identity/training mismatch")
                continue
            if training.get("real_training_episodes") != 2_048 or training.get("episodes_by_collector") != {collector: 1_024 for collector in B4_COLLECTORS} or training.get("updates_per_arm") != {arm: 128 for arm in B4_ARMS}:
                issues.append(f"{expected[0]} activity mismatch")
            for name in (
                "initial_complete_state_hashes", "initial_parameter_hashes", "initial_optimizer_hashes",
                "initial_recurrent_and_state_hashes", "initial_carried_learner_state_hashes",
                "initial_registered_learner_rng_state_hashes",
            ):
                mapping = training.get(name)
                if not isinstance(mapping, Mapping) or set(mapping) != set(B4_ARMS) or len(set(mapping.values())) != 1:
                    issues.append(f"{expected[0]} {name} mismatch")
            derived_first_later_divergence: dict[str, object] | None = None
            derived_first_oracle_successor_identity = False
            derived_post_first_parameter_divergence = False
            batches = training.get("batch_records")
            batch_digests: dict[str, list[str]] = {collector: [] for collector in B4_COLLECTORS}
            retained_train_clone_ids: set[str] = set()
            if not isinstance(batches, list) or len(batches) != 128:
                issues.append(f"{expected[0]} batch record count mismatch")
            else:
                for update_index, record in enumerate(batches):
                    if not isinstance(record, Mapping) or record.get("update_index") != update_index:
                        issues.append(f"{expected[0]}/{update_index} batch identity mismatch")
                        continue
                    generator_rows, self_rows = record.get("generator_rows"), record.get("self_feedback_rows")
                    if not isinstance(generator_rows, list) or not isinstance(self_rows, list) or len(generator_rows) != 8 or len(self_rows) != 8:
                        issues.append(f"{expected[0]}/{update_index} dual batch rows missing")
                        continue
                    if any(not isinstance(row, Mapping) or not _immutable_row_contract(row) for row in (*generator_rows, *self_rows)):
                        issues.append(f"{expected[0]}/{update_index} immutable row contract failed")
                    generator_digest, self_digest = digest(generator_rows), digest(self_rows)
                    batch_digests["RL_ORIGINAL_GENERATOR"].append(generator_digest)
                    batch_digests["CREDIT_SIGN_SELF_FEEDBACK"].append(self_digest)
                    if record.get("generator_batch_digest") != generator_digest or record.get("self_feedback_batch_digest") != self_digest:
                        issues.append(f"{expected[0]}/{update_index} batch digest mismatch")
                    if record.get("generator_ordered_row_digests") != [digest(row) for row in generator_rows] or record.get("self_feedback_ordered_row_digests") != [digest(row) for row in self_rows]:
                        issues.append(f"{expected[0]}/{update_index} ordered row digest mismatch")
                    if update_index == 0 and (record.get("first_batch_byte_identity") is not True or canonical_bytes(generator_rows) != canonical_bytes(self_rows)):
                        issues.append(f"{expected[0]} first collector batch identity failed")
                    if update_index > 0 and derived_first_later_divergence is None:
                        for row_index, (generator_row, own_row) in enumerate(zip(generator_rows, self_rows)):
                            if _batch_exposure_signature(generator_row) != _batch_exposure_signature(own_row):
                                derived_first_later_divergence = {
                                    "update_index": update_index,
                                    "row_index": row_index,
                                    "generator_signature": _batch_exposure_signature(generator_row),
                                    "self_feedback_signature": _batch_exposure_signature(own_row),
                                    "action_diverged": generator_row["A_behavior"] != own_row["A_behavior"],
                                    "environment_transition_row_diverged": any(
                                        generator_row[field] != own_row[field]
                                        for field in ("R", "G", "environment_transitions")
                                    ),
                                }
                                break
                    for rows in (generator_rows, self_rows):
                        if Counter(int(row["metadata"]["true_cue"]) for row in rows) != Counter({0: 4, 1: 4}):
                            issues.append(f"{expected[0]}/{update_index} cue balance mismatch")
                        retained_train_clone_ids.update(str(row["metadata"]["clone_id"]) for row in rows)
                    training_transitions += sum(int(row["environment_transitions"]) for row in (*generator_rows, *self_rows))
            receipts = training.get("barrier_receipts")
            if not isinstance(receipts, list) or len(receipts) != 128:
                issues.append(f"{expected[0]} barrier receipt count mismatch")
            else:
                for update_index, receipt in enumerate(receipts):
                    if not isinstance(receipt, Mapping) or receipt.get("update_index") != update_index or receipt.get("both_batches_frozen_before_any_update") is not True:
                        issues.append(f"{expected[0]}/{update_index} phase barrier mismatch")
                        continue
                    if receipt.get("collector_state_before") != receipt.get("state_after_generator_collection") or receipt.get("collector_state_before") != receipt.get("state_after_both_collections"):
                        issues.append(f"{expected[0]}/{update_index} collector noninterference mismatch")
                    if receipt.get("frozen_before_updates") != receipt.get("frozen_after_updates") or receipt.get("rng_noninterference") != "NO_MUTABLE_RNG_EXISTS" or receipt.get("tape_batch_noninterference") is not True:
                        issues.append(f"{expected[0]}/{update_index} tape/batch/RNG noninterference mismatch")
                    pre, after_gen, after_shadow, after_self = (receipt.get(name) for name in ("pre_update_states", "after_generator_states", "after_shadow_states", "after_self_states"))
                    if all(isinstance(value, Mapping) for value in (pre, after_gen, after_shadow, after_self)):
                        if any(after_gen[arm] != pre[arm] for arm in B4_ARMS[1:]):  # type: ignore[index]
                            issues.append(f"{expected[0]}/{update_index} generator cross-arm mutation")
                        if after_shadow["RL_ORIGINAL_GENERATOR"] != after_gen["RL_ORIGINAL_GENERATOR"] or after_shadow["CREDIT_SIGN_SELF_FEEDBACK"] != after_gen["CREDIT_SIGN_SELF_FEEDBACK"]:  # type: ignore[index]
                            issues.append(f"{expected[0]}/{update_index} shadow cross-arm mutation")
                        if after_self["RL_ORIGINAL_GENERATOR"] != after_shadow["RL_ORIGINAL_GENERATOR"] or after_self["CREDIT_SIGN_SHADOW"] != after_shadow["CREDIT_SIGN_SHADOW"]:  # type: ignore[index]
                            issues.append(f"{expected[0]}/{update_index} self-feedback cross-arm mutation")
                        if update_index == 0:
                            derived_first_oracle_successor_identity = after_self["CREDIT_SIGN_SHADOW"] == after_self["CREDIT_SIGN_SELF_FEEDBACK"]  # type: ignore[index]
            updates = training.get("updates")
            initial_parameters = training.get("initial_parameter_hashes")
            initial_optimizers = training.get("initial_optimizer_hashes")
            if not isinstance(updates, Mapping) or set(updates) != set(B4_ARMS):
                issues.append(f"{expected[0]} update arms mismatch")
            else:
                common_orders: list[list[int]] | None = None
                for arm in B4_ARMS:
                    arm_updates = updates.get(arm)
                    if not isinstance(arm_updates, list) or len(arm_updates) != 128:
                        issues.append(f"{expected[0]}/{arm} update count mismatch")
                        continue
                    previous_parameter = initial_parameters.get(arm) if isinstance(initial_parameters, Mapping) else None
                    previous_optimizer = initial_optimizers.get(arm) if isinstance(initial_optimizers, Mapping) else None
                    orders: list[list[int]] = []
                    for update_index, update in enumerate(arm_updates):
                        if not isinstance(update, Mapping):
                            continue
                        expected_route = ORIGINAL_ACTOR_ROUTE if arm == "RL_ORIGINAL_GENERATOR" else ORACLE_SIGN_ACTOR_ROUTE
                        expected_batch = batch_digests["CREDIT_SIGN_SELF_FEEDBACK" if arm == "CREDIT_SIGN_SELF_FEEDBACK" else "RL_ORIGINAL_GENERATOR"]
                        order = update.get("batch_order")
                        orders.append(order if isinstance(order, list) else [])
                        if update.get("update_index") != update_index or update.get("actor_route") != expected_route or update.get("critic_route") != CRITIC_ROUTE or update.get("advantage_count") != 8 or update.get("max_abs_magnitude_error") != 0.0:
                            issues.append(f"{expected[0]}/{arm}/{update_index} route mismatch")
                        if not isinstance(order, list) or sorted(order) != list(range(8)) or update_index >= len(expected_batch) or update.get("batch_digest") != expected_batch[update_index]:
                            issues.append(f"{expected[0]}/{arm}/{update_index} batch/order binding mismatch")
                        if update.get("parameters_before") != previous_parameter or update.get("optimizer_before") != previous_optimizer:
                            issues.append(f"{expected[0]}/{arm}/{update_index} parameter/Adam chain mismatch")
                        previous_parameter, previous_optimizer = update.get("parameters_after"), update.get("optimizer_after")
                        for field in (
                            "loss", "actor_loss", "policy_actor_loss", "entropy_loss", "critic_loss",
                            "gradient_norm_before_clip", "combined_gradient_norm_before_clip",
                            "actor_gradient_norm", "entropy_gradient_norm", "critic_gradient_norm",
                            "absolute_advantage_mean", "absolute_advantage_variance",
                            "critic_target_mean", "critic_target_variance",
                        ):
                            if not math.isfinite(float(update.get(field, math.nan))):
                                issues.append(f"{expected[0]}/{arm}/{update_index} nonfinite {field}")
                        if update.get("clip_threshold") != 1.0:
                            issues.append(f"{expected[0]}/{arm}/{update_index} clip mismatch")
                        if arm == "RL_ORIGINAL_GENERATOR" and update.get("correctness_class_counts") != {"-1": 0, "+1": 0}:
                            issues.append(f"{expected[0]}/{arm}/{update_index} oracle contamination")
                        if arm != "RL_ORIGINAL_GENERATOR" and (update.get("oracle_scalar_only") is not True or sum(int(update.get("correctness_class_counts", {}).get(key, -9)) for key in ("-1", "+1")) != 8):  # type: ignore[union-attr]
                            issues.append(f"{expected[0]}/{arm}/{update_index} oracle coefficient mismatch")
                    if common_orders is None:
                        common_orders = orders
                    elif orders != common_orders:
                        issues.append(f"{expected[0]} common minibatch order mismatch")
                generator_updates = updates.get("RL_ORIGINAL_GENERATOR")
                self_updates = updates.get("CREDIT_SIGN_SELF_FEEDBACK")
                if (
                    isinstance(generator_updates, list) and generator_updates
                    and isinstance(self_updates, list) and self_updates
                    and isinstance(generator_updates[0], Mapping) and isinstance(self_updates[0], Mapping)
                ):
                    derived_post_first_parameter_divergence = (
                        generator_updates[0].get("parameters_after") != self_updates[0].get("parameters_after")
                    )
            exposure = training.get("feedback_exposure")
            derived_exposure = {
                "post_first_update_collector_parameter_divergence": derived_post_first_parameter_divergence,
                "first_oracle_successor_complete_state_identity": derived_first_oracle_successor_identity,
                "later_action_or_environment_transition_row_divergence": derived_first_later_divergence is not None,
                "first_later_divergence": derived_first_later_divergence,
            }
            if exposure != derived_exposure:
                issues.append(f"{expected[0]} feedback exposure evidence mismatch")
            exposure_valid = all(
                derived_exposure[key] is True for key in (
                    "post_first_update_collector_parameter_divergence",
                    "first_oracle_successor_complete_state_identity",
                    "later_action_or_environment_transition_row_divergence",
                )
            )
            exposure_by_unit[expected[0]] = exposure_valid
            final_hashes_by_unit[expected[0]] = training.get("final_parameter_hashes") if isinstance(training.get("final_parameter_hashes"), Mapping) else {}
            train_clone_ids_by_unit[expected[0]] = retained_train_clone_ids
    derived_metrics: dict[str, list[Mapping[str, object]]] = {arm: [] for arm in B4_ARMS}
    evaluation_transitions = 0
    evaluation_episodes = 0
    checkpoints: set[str] = set()
    if isinstance(evaluations, Mapping) and set(evaluations) == set(B4_ARMS):
        for unit_index, (unit_id, root) in enumerate(B4_UNITS):
            panel_digests: list[str] = []
            for arm in B4_ARMS:
                metrics = evaluations.get(arm)
                if not isinstance(metrics, list) or unit_index >= len(metrics) or not isinstance(metrics[unit_index], Mapping):
                    continue
                metric = metrics[unit_index]
                derived, evaluation_issues, transitions, panel_digest, evaluation_clone_ids = _derive_retained_evaluation_metric(
                    unit_id=unit_id,
                    root=root,
                    arm=arm,
                    metric=metric,
                    expected_final_hash=final_hashes_by_unit.get(unit_id, {}).get(arm),
                )
                issues.extend(evaluation_issues)
                if derived is None:
                    continue
                derived_metrics[arm].append(derived)
                panel_digests.append(str(panel_digest))
                evaluation_transitions += transitions
                evaluation_episodes += int(derived["episodes"])
                checkpoints.add(str(derived["checkpoint_id"]))
                if evaluation_clone_ids & train_clone_ids_by_unit.get(unit_id, set()):
                    issues.append(f"{unit_id}/{arm} train/evaluation clone overlap")
            if len(panel_digests) != 3 or len(set(panel_digests)) != 1:
                issues.append(f"{unit_id} independently recreated common panel mismatch")
            if (
                not isinstance(units, list)
                or unit_index >= len(units)
                or not isinstance(units[unit_index], Mapping)
                or units[unit_index].get("evaluation_panel_digests") != panel_digests
            ):
                issues.append(f"{unit_id} unit panel-digest projection mismatch")
    derived_aggregates = {arm: _arm_aggregate(metrics) for arm, metrics in derived_metrics.items()} if all(len(metrics) == 5 for metrics in derived_metrics.values()) else None
    if result.get("aggregates") != derived_aggregates:
        issues.append("aggregate projection mismatch")
    feedback_exposure_valid = len(exposure_by_unit) == 5 and all(exposure_by_unit.values())
    if result.get("feedback_exposure_valid") is not feedback_exposure_valid:
        issues.append("feedback exposure projection mismatch")
    activity_projection = {
        "result_bearing_runs": 1,
        "real_training_episodes": 10_240,
        "evaluation_episodes": evaluation_episodes,
        "environment_transitions": training_transitions + evaluation_transitions,
        "optimizer_updates": 1_920,
        "checkpoints_total": len(checkpoints),
        "retries_rescues_sweeps": 0,
    }
    if result.get("activity") != activity_projection:
        issues.append("activity differs from retained records")
    resource_usage = result.get("resource_usage")
    resource_caps_passed = False
    if not isinstance(resource_usage, Mapping):
        issues.append("process resource evidence missing")
    else:
        try:
            derived_resource_usage = _resource_usage_evidence(
                cpu_start_seconds=float(resource_usage["cpu_start_seconds"]),
                cpu_end_seconds=float(resource_usage["cpu_end_seconds"]),
                peak_rss_samples_bytes=resource_usage["peak_process_rss_samples_bytes"],  # type: ignore[arg-type]
            )
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            issues.append(f"process resource evidence invalid: {error}")
        else:
            if resource_usage != derived_resource_usage:
                issues.append("process resource evidence projection mismatch")
            resource_caps_passed = derived_resource_usage["all_resource_caps_passed"] is True
    expected_runtime = {
        "arms": list(B4_ARMS),
        "sole_intervention_edge": "oracle-sign learner parameters -> its future batch source",
        "not_on_policy": True,
        "dual_collector_phase_barrier": True,
        "fixed_update_order": list(FIXED_UPDATE_ORDER),
        "immutable_address_indexed_tape_no_mutable_rng": True,
        "first_batch_byte_identity": True,
        "first_oracle_successor_complete_state_identity": True,
        "shadow_exact_generator_batch_bytes_and_order": True,
        "collector_optimizer_rng_tape_batch_successor_noninterference": True,
        "oracle_scalar_only": True,
        "actor_critic_gru_entropy_adam_clip_mask_return_evaluation_invariant": True,
        "mediators_not_branch_conditions": True,
        "resource_caps_branch_bearing": True,
        "cpu_minutes_cap": 30,
        "peak_process_memory_gib_cap": 2,
    }
    if result.get("runtime_contract") != expected_runtime:
        issues.append("runtime contract mismatch")
    derived_valid = (
        not issues
        and feedback_exposure_valid
        and activity_projection["real_training_episodes"] == 10_240
        and activity_projection["evaluation_episodes"] == 1_920
        and activity_projection["optimizer_updates"] == 1_920
        and activity_projection["checkpoints_total"] == 15
        and activity_projection["environment_transitions"] <= B4_CAPS["environment_transitions_total"]
        and resource_caps_passed
    )
    if result.get("activity_valid") is not derived_valid:
        issues.append("activity_valid projection mismatch")
    expected_branch = classify_b4(valid=derived_valid, aggregates=derived_aggregates, feedback_exposure_valid=feedback_exposure_valid)
    if result.get("branch") != expected_branch:
        issues.append(f"branch precedence mismatch: expected {expected_branch}")
    if repo_root is None:
        issues.append("runtime retained validation requires source-binding repo_root")
    else:
        issues.extend(_git_binding(repo_root, str(manifest["source_revision"])))
    return tuple(issues)

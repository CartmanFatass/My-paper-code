"""VSP02-B3 lifecycle credit-sign bridge.

``RL_ORIGINAL`` is the sole real-host episode/action/batch generator.  The
paired ``CREDIT_SIGN_BRIDGE`` learner consumes the same frozen rows in the same
order and changes only the lifecycle actor coefficient from ``detach(G-b)`` to
``correctness_sign(action, cue) * detach(abs(G-b))``.  The cue oracle is read
only after the forward pass and is used only to construct that scalar sign.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess
from typing import Mapping, Sequence

import torch
from torch import Tensor

from experiments.candidates.vsp_02 import (
    learned_cue_conditioned_lifecycle_control_v2 as b1,
)
from experiments.candidates.vsp_02 import (
    vsp02_b2_paired_shadow_learner_localization as b2,
)


B3_SCHEMA_VERSION = 1
B3_ASSIGNMENT_ID = "VSP02-B3-LIFECYCLE-CREDIT-SIGN-BRIDGE"
B3_CANDIDATE = "CAND-VSP-02@adversarial-revision-v8"
B3_HOST_ID = "VSP02-A2-PHYSICAL-LIFECYCLE-HOST-v1"
B3_RESOURCE_CLASS = "B_TOY_LIGHT"
B3_POOL_UNITS = 1
B3_PHYSICAL_TAPE_PREFIX = f"{B3_ASSIGNMENT_ID}/PHYSICAL"
B3_ACCEPTED_B2_SOURCE = "bd0da64f851718cf0b5d59b144d99a7006ff2a73"
B3_ACCEPTED_B2_PUBLICATION = "51aa863367b2f0f25ff6bf3606623496daca8d73"
B3_SEED_PREFIX = "VSP02-B3-V1\0"
B3_UNITS = tuple((f"VSP02-B3-U{index:02d}", 22_030_000 + index) for index in range(1, 6))
B3_STREAMS = b2.B2_STREAMS
B3_ARMS = ("RL_ORIGINAL", "CREDIT_SIGN_BRIDGE")
B3_UPDATES_PER_UNIT = 128
B3_BATCH_SIZE = 8
B3_TRAIN_EPISODES_PER_UNIT = 1_024
B3_EVAL_EPISODES_PER_UNIT_ARM = 128
B3_BRANCH_PRECEDENCE = (
    "B3_INCONCLUSIVE_OR_INVALID",
    "B3_SIGN_BRIDGE_LOCAL_SUFFICIENCY",
    "B3_SIGN_ONLY_INSUFFICIENT",
)
B3_CAPS = {
    "environment_transitions_total": 145_348,
    "real_training_episodes_total": 5_120,
    "evaluation_episodes_total": 1_280,
    "optimizer_updates_total": 1_280,
    "checkpoints_total": 10,
    "result_bearing_runs": 1,
    "pool_units": 1,
    "cpu_minutes": 30,
    "peak_memory_gib": 2,
}
B3_CLAIM_PATHS = (
    "experiments/candidates/vsp_02/vsp02_b3_lifecycle_credit_sign_bridge.py",
    "scripts/run_vsp02_b3_lifecycle_credit_sign_bridge.py",
    "tests/experiments/candidates/vsp_02/test_vsp02_b3_lifecycle_credit_sign_bridge.py",
    "docs/research/candidates/vsp_02/VSP02_B3_CODE_SCIENCE_INDEX.md",
)
B3_DEPENDENCY_PATHS = (
    "experiments/candidates/vsp_02/vsp02_b2_paired_shadow_learner_localization.py",
    "experiments/candidates/vsp_02/learned_cue_conditioned_lifecycle_control_v2.py",
    "experiments/candidates/vsp_02/owner_action_responsive_lifecycle.py",
)
B3_RUNTIME_PATHS = B3_CLAIM_PATHS + B3_DEPENDENCY_PATHS
ORIGINAL_ACTOR_ROUTE = "-detach(G-b)*log(mu(A_behavior|history))-0.01*entropy"
BRIDGE_ACTOR_ROUTE = "-correctness_sign(A_behavior,cue)*detach(abs(G-b))*log(mu(A_behavior|history))-0.01*entropy"
CRITIC_ROUTE = "mean(0.5*(G-b)^2)"


json_ready = b2.json_ready
canonical_bytes = b2.canonical_bytes
digest = b2.digest
model_payload = b2.model_payload
optimizer_payload = b2.optimizer_payload
rng_digest = b2.rng_digest
_tensor_payload = b2._tensor_payload
_architecture_payload = b2._architecture_payload
_observation_firewall = b2._observation_firewall
_synthetic_history = b2._synthetic_history
_forward = b2._forward
_mixture_metrics_from_raw_q = b2._mixture_metrics_from_raw_q


class B3LifecycleHost(b1.LifecycleHost):
    """Accepted physical host with a fresh B3-only tape namespace."""

    def step(
        self, action: b1.Action, *, action_probabilities: Sequence[float]
    ) -> dict[str, object]:
        if not self._open or self.escrow is not None:
            raise RuntimeError("episode action can be committed exactly once")
        probabilities = tuple(float(value) for value in action_probabilities)
        if (
            len(probabilities) != 2
            or any(not math.isfinite(value) or value < 0.0 for value in probabilities)
            or abs(sum(probabilities) - 1.0) > 1e-12
        ):
            raise ValueError("invalid RELEASE/HOLD probability pair")
        decide = self.decision_observation()
        escrow_id = hashlib.sha256(
            f"{B3_ASSIGNMENT_ID}/{self.lifecycle_id}/{self.owner_epoch}/{b1.B1_BEHAVIOR_VERSION}".encode()
        ).hexdigest()
        self.escrow = b1.ActionScoreEscrow(
            escrow_id=escrow_id,
            action=action.value,
            action_probabilities=probabilities,
            selected_likelihood=probabilities[action.index],
            owner_epoch=self.owner_epoch,
            behavior_version=b1.B1_BEHAVIOR_VERSION,
        )
        tape_id = f"{B3_PHYSICAL_TAPE_PREFIX}/{self.lifecycle_id}"
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
                tape=b1.a1.PairedTape(
                    tape_id=tape_id, natural=True, primitive_action=b1.B1_PRIMITIVE
                ),
                release_id=escrow_id,
            )
            self.record = second.record
            self.states.append(self.record.phase.value)
            self.environment_transitions += 1
            self.rewards.append(0)
            if self.record.phase is not b1.a1.Phase.ENDED_NATURAL:
                raise AssertionError("HOLD did not naturally terminate")
        end_cause = self.record.end_cause
        if end_cause is None or self.escrow.consumption_count != 0:
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
        physical_return = sum(
            reward * (b1.B1_GAMMA**index) for index, reward in enumerate(self.rewards)
        )
        return {
            "reward_sequence": list(self.rewards),
            "physical_return": physical_return,
            "physical_tape_ids": list(self.tape_ids),
            "environment_transitions": self.environment_transitions,
        }


def b3_seed(unit_id: str, decimal_root: int, stream_name: str) -> int:
    if (unit_id, decimal_root) not in B3_UNITS:
        raise ValueError(f"unregistered B3 unit/root: {unit_id}/{decimal_root}")
    if stream_name not in B3_STREAMS:
        raise ValueError(f"unregistered B3 RNG stream: {stream_name}")
    material = (
        B3_SEED_PREFIX + unit_id + "\0" + str(decimal_root) + "\0" + stream_name
    ).encode("utf-8")
    return 1 + (
        int.from_bytes(hashlib.sha256(material).digest()[:8], "big", signed=False)
        % 2_147_483_646
    )


def seed_report() -> dict[str, object]:
    derived = {
        unit_id: {stream: b3_seed(unit_id, root, stream) for stream in B3_STREAMS}
        for unit_id, root in B3_UNITS
    }
    flat = [seed for streams in derived.values() for seed in streams.values()]
    b1_values = {
        b1.stream_seed(seed_id, stream)
        for seed_id in b1.B1_SEED_IDS
        for stream in b1.B1_RNG_STREAMS
    }
    b2_values = {
        b2.b2_seed(unit_id, root, stream)
        for unit_id, root in b2.B2_UNITS
        for stream in b2.B2_STREAMS
    }
    return {
        "function": "SHA256(VSP02-B3-V1, unit_id, decimal_root, stream_name)",
        "streams": list(B3_STREAMS),
        "derived": derived,
        "all_b3_seeds_unique": len(flat) == len(set(flat)),
        "collision_with_b1v2_seed_values": sorted(set(flat) & b1_values),
        "collision_with_b2_seed_values": sorted(set(flat) & b2_values),
        "identity_collision_with_predecessors": (
            any(unit_id in b1.B1_SEED_IDS for unit_id, _ in B3_UNITS)
            or any(unit_id in {value[0] for value in b2.B2_UNITS} for unit_id, _ in B3_UNITS)
            or B3_PHYSICAL_TAPE_PREFIX.startswith(f"{b1.B1_ASSIGNMENT_ID}/")
            or B3_PHYSICAL_TAPE_PREFIX.startswith(f"{b2.B2_ASSIGNMENT_ID}/")
        ),
    }


def _new_learners(
    unit_id: str, root: int
) -> tuple[dict[str, b1.GRUActorCritic], dict[str, torch.optim.Optimizer]]:
    base = b1.GRUActorCritic(init_seed=b3_seed(unit_id, root, "parameter_initialization"))
    base_optimizer = torch.optim.Adam(base.parameters(), lr=0.003)
    initial_optimizer = deepcopy(base_optimizer.state_dict())
    models = {arm: deepcopy(base) for arm in B3_ARMS}
    optimizers: dict[str, torch.optim.Optimizer] = {}
    for arm in B3_ARMS:
        optimizer = torch.optim.Adam(models[arm].parameters(), lr=0.003)
        optimizer.load_state_dict(deepcopy(initial_optimizer))
        optimizers[arm] = optimizer
    return models, optimizers


def correctness_sign(action: str, cue: int) -> float:
    if cue not in (0, 1):
        raise ValueError("oracle cue must be binary")
    parsed = b1.Action(action)
    correct = b1.Action.HOLD if cue == 0 else b1.Action.RELEASE
    return 1.0 if parsed is correct else -1.0


def _require_advantage_row(row: Mapping[str, object]) -> None:
    if "G" not in row:
        raise ValueError("missing lifecycle advantage return")
    if row.get("M_valid") != [0, 1] or row.get("M_lifecycle") != [0, 1]:
        raise ValueError("missing or masked lifecycle advantage")
    if not math.isfinite(float(row["G"])):
        raise ValueError("nonfinite lifecycle return")


def _loss_terms(
    arm: str,
    model: b1.GRUActorCritic,
    batch: Sequence[Mapping[str, object]],
) -> tuple[Tensor, dict[str, object]]:
    if arm not in B3_ARMS or len(batch) == 0:
        raise ValueError("unknown arm or empty batch")
    batch_before = digest(batch)
    actor_terms: list[Tensor] = []
    critic_terms: list[Tensor] = []
    coefficients: list[float] = []
    advantages: list[float] = []
    correctness_classes: Counter[int] = Counter()
    sign_changes = 0
    for row in batch:
        _require_advantage_row(row)
        observations = row.get("O")
        if not isinstance(observations, Sequence) or not _observation_firewall(observations):
            raise ValueError("observation firewall or history missing")
        _, _, probabilities, baseline, entropy = _forward(model, observations)
        physical_return = torch.tensor(float(row["G"]), dtype=torch.float64)
        advantage = physical_return - baseline
        if not torch.isfinite(advantage):
            raise ValueError("nonfinite lifecycle advantage")
        action_index = b1.Action(str(row.get("A_behavior"))).index
        if arm == "RL_ORIGINAL":
            expected_probabilities = row.get("behavior_probabilities")
            if not isinstance(expected_probabilities, list) or len(expected_probabilities) != 2:
                raise ValueError("original behavior probability binding missing")
            if any(
                not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=1e-12)
                for actual, expected in zip(probabilities.detach(), expected_probabilities)
            ):
                raise RuntimeError("original behavior probabilities changed before update")
            coefficient = advantage.detach()
        else:
            # The oracle is deliberately first accessed here: after the entire
            # forward input, hidden state, baseline and return are fixed.
            metadata = row.get("metadata")
            if not isinstance(metadata, Mapping) or "true_cue" not in metadata:
                raise ValueError("bridge oracle cue missing")
            cue = int(metadata["true_cue"])
            sign = correctness_sign(str(row.get("A_behavior")), cue)
            coefficient = torch.tensor(sign, dtype=torch.float64) * advantage.detach().abs()
            correctness_classes[int(sign)] += 1
            if float(advantage.detach()) != 0.0 and math.copysign(1.0, float(advantage.detach())) != sign:
                sign_changes += 1
        if not torch.isfinite(coefficient):
            raise ValueError("nonfinite lifecycle actor coefficient")
        advantages.append(float(advantage.detach()))
        coefficients.append(float(coefficient))
        actor_terms.append(-coefficient * torch.log(probabilities[action_index]) - 0.01 * entropy)
        critic_terms.append(0.5 * advantage**2)
    if digest(batch) != batch_before:
        raise RuntimeError("loss route mutated immutable batch")
    actor_loss = torch.stack(actor_terms).mean()
    critic_loss = torch.stack(critic_terms).mean()
    actor_gradients = torch.autograd.grad(
        actor_loss, tuple(model.parameters()), retain_graph=True, allow_unused=True
    )
    actor_norms = [
        torch.linalg.vector_norm(gradient, 2.0)
        for gradient in actor_gradients
        if gradient is not None
    ]
    actor_gradient_norm = float(
        torch.linalg.vector_norm(torch.stack(actor_norms), 2.0)
    )
    if not math.isfinite(actor_gradient_norm):
        raise ValueError("nonfinite actor gradient")
    return actor_loss + critic_loss, {
        "actor_loss": float(actor_loss.detach()),
        "critic_loss": float(critic_loss.detach()),
        "actor_route": ORIGINAL_ACTOR_ROUTE if arm == "RL_ORIGINAL" else BRIDGE_ACTOR_ROUTE,
        "critic_route": CRITIC_ROUTE,
        "advantages": advantages,
        "actor_coefficients": coefficients,
        "advantage_count": len(advantages),
        "zero_advantage_count": sum(value == 0.0 for value in advantages),
        "nonzero_advantage_count": sum(value != 0.0 for value in advantages),
        "correctness_class_counts": {
            "-1": correctness_classes[-1],
            "+1": correctness_classes[1],
        },
        "actual_sign_change_count": sign_changes,
        "max_abs_magnitude_error": (
            max(abs(abs(coefficient) - abs(advantage)) for coefficient, advantage in zip(coefficients, advantages))
            if arm == "CREDIT_SIGN_BRIDGE"
            else 0.0
        ),
        "oracle_scalar_only": arm == "CREDIT_SIGN_BRIDGE",
        "batch_digest_before_after": batch_before,
        "actor_gradient_norm": actor_gradient_norm,
    }


def _optimizer_step(
    arm: str,
    model: b1.GRUActorCritic,
    optimizer: torch.optim.Optimizer,
    batch: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    before, optimizer_before = digest(model_payload(model)), digest(optimizer_payload(optimizer))
    optimizer.zero_grad(set_to_none=True)
    loss, route = _loss_terms(arm, model, batch)
    if not torch.isfinite(loss):
        raise ValueError("nonfinite loss")
    loss.backward()
    if any(parameter.grad is None or not torch.isfinite(parameter.grad).all() for parameter in model.parameters()):
        raise ValueError("missing or nonfinite gradient")
    gradient_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
    if not math.isfinite(gradient_norm):
        raise ValueError("nonfinite pre-clip gradient norm")
    optimizer.step()
    return {
        "parameters_before": before,
        "parameters_after": digest(model_payload(model)),
        "optimizer_before": optimizer_before,
        "optimizer_after": digest(optimizer_payload(optimizer)),
        "loss": float(loss.detach()),
        "actor_loss": route["actor_loss"],
        "critic_loss": route["critic_loss"],
        "actor_route": route["actor_route"],
        "critic_route": route["critic_route"],
        "gradient_norm_before_clip": gradient_norm,
        "clip_threshold": 1.0,
        "clipped": gradient_norm > 1.0,
        "advantage_count": route["advantage_count"],
        "zero_advantage_count": route["zero_advantage_count"],
        "nonzero_advantage_count": route["nonzero_advantage_count"],
        "correctness_class_counts": route["correctness_class_counts"],
        "actual_sign_change_count": route["actual_sign_change_count"],
        "max_abs_magnitude_error": route["max_abs_magnitude_error"],
        "oracle_scalar_only": route["oracle_scalar_only"],
        "actor_gradient_norm": route["actor_gradient_norm"],
    }


def _schedule_with_receipt(unit_id: str, root: int) -> tuple[list[dict[str, object]], str]:
    cue_rng = random.Random(b3_seed(unit_id, root, "train_owner_cue_clone"))
    rows: list[dict[str, object]] = []
    for update_index in range(B3_UPDATES_PER_UNIT):
        cues = [0] * 4 + [1] * 4
        cue_rng.shuffle(cues)
        for within_update, cue in enumerate(cues):
            episode_index = update_index * B3_BATCH_SIZE + within_update
            rows.append({
                "unit_id": unit_id,
                "decimal_root": root,
                "update_index": update_index,
                "within_update": within_update,
                "episode_index": episode_index,
                "owner_epoch": f"{unit_id}-TR-{episode_index:04d}",
                "true_cue": cue,
                "clone_id": f"{unit_id}/TRAIN/{episode_index:04d}",
            })
    return rows, rng_digest(cue_rng)


def _schedule_contract(rows: Sequence[Mapping[str, object]]) -> bool:
    return (
        len(rows) == B3_TRAIN_EPISODES_PER_UNIT
        and Counter(int(row["true_cue"]) for row in rows) == Counter({0: 512, 1: 512})
        and all(
            Counter(int(row["true_cue"]) for row in rows[start : start + B3_BATCH_SIZE]) == Counter({0: 4, 1: 4})
            for start in range(0, len(rows), B3_BATCH_SIZE)
        )
    )


def _proof_batch(model: b1.GRUActorCritic, *, zero_advantage: bool = False) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, cue in enumerate((0, 1, 0, 1, 0, 1, 0, 1)):
        observations = _synthetic_history(cue, owner_epoch=f"B3-PROOF-{index:02d}")
        with torch.no_grad():
            _, _, probabilities, baseline, _ = _forward(model, observations)
        # Two correct and two incorrect examples per four rows, without
        # changing the cue-balanced observation support.
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
            "behavior_probabilities": [float(value) for value in probabilities],
            "environment_transitions": 4,
            "metadata": {"true_cue": cue, "clone_id": f"B3-PROOF/{index}"},
        })
    return json.loads(canonical_bytes(rows))


def _gradient_and_noninterference_proof(
    models: Mapping[str, b1.GRUActorCritic],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    batch = _proof_batch(models["RL_ORIGINAL"])
    before = {
        "rl_parameters": digest(model_payload(models["RL_ORIGINAL"])),
        "rl_optimizer": digest(optimizer_payload(optimizers["RL_ORIGINAL"])),
        "rl_rng": digest("NO_RL_RNG_CONSUMPTION"),
        "rl_successor_state": digest("NO_SUCCESSOR_MUTATION"),
        "immutable_batch": digest(batch),
    }
    loss, route = _loss_terms("CREDIT_SIGN_BRIDGE", models["CREDIT_SIGN_BRIDGE"], batch)
    gradients = torch.autograd.grad(loss, tuple(models["CREDIT_SIGN_BRIDGE"].parameters()), allow_unused=True)
    after = {
        "rl_parameters": digest(model_payload(models["RL_ORIGINAL"])),
        "rl_optimizer": digest(optimizer_payload(optimizers["RL_ORIGINAL"])),
        "rl_rng": digest("NO_RL_RNG_CONSUMPTION"),
        "rl_successor_state": digest("NO_SUCCESSOR_MUTATION"),
        "immutable_batch": digest(batch),
    }
    return {
        "before": before,
        "after": after,
        "hash_identity": before == after,
        "finite_nonzero_actor_composite_gradient": all(
            gradient is not None and torch.isfinite(gradient).all() for gradient in gradients
        ) and any(float(torch.linalg.vector_norm(gradient)) > 0.0 for gradient in gradients if gradient is not None),
        "bridge_route": route,
        "activity": _zero_activity(),
    }


def build_manifest(*, source_revision: str, run_id: str, technical_only: bool) -> dict[str, object]:
    return {
        "schema_version": B3_SCHEMA_VERSION,
        "artifact_kind": "vsp02_b3_manifest",
        "assignment_id": B3_ASSIGNMENT_ID,
        "candidate": B3_CANDIDATE,
        "host_id": B3_HOST_ID,
        "resource_class": B3_RESOURCE_CLASS,
        "pool_units": B3_POOL_UNITS,
        "source_revision": source_revision,
        "run_id": run_id,
        "technical_only": technical_only,
        "accepted_b2_source": B3_ACCEPTED_B2_SOURCE,
        "accepted_b2_publication": B3_ACCEPTED_B2_PUBLICATION,
        "freshness": {
            "physical_tape_prefix": B3_PHYSICAL_TAPE_PREFIX,
            "predecessor_artifact_checkpoint_batch_tape_reuse": False,
            "parameter_state_derived_once_then_cloned": True,
            "optimizer_state_derived_once_then_cloned": True,
            "run_root_reuse": False,
        },
        "arms": list(B3_ARMS),
        "units": [{"unit_id": unit, "decimal_root": root} for unit, root in B3_UNITS],
        "rng_streams": list(B3_STREAMS),
        "training": {
            "updates_per_unit": 128,
            "episodes_per_update": 8,
            "episodes_per_unit": 1_024,
            "cue_count_per_update": {"0": 4, "1": 4},
            "sole_generator": "RL_ORIGINAL",
            "immutable_same_rows_and_order": True,
        },
        "evaluation": {
            "episodes_per_unit_arm": 128,
            "cue_counts": {"0": 64, "1": 64},
            "checkpoints_per_arm_unit": 1,
            "checkpoints_total": 10,
            "stochastic_action_draws": 0,
        },
        "optimizer": {
            "name": "Adam", "learning_rate": 0.003, "betas": [0.9, 0.999],
            "epsilon": 1e-8, "weight_decay": 0.0, "amsgrad": False,
            "gradient_norm_clip": 1.0,
        },
        "loss_contract": {
            "original_actor": ORIGINAL_ACTOR_ROUTE,
            "bridge_actor": BRIDGE_ACTOR_ROUTE,
            "critic": CRITIC_ROUTE,
            "zero_advantage_credit": 0.0,
            "missing_masked_nonfinite_advantage": "INVALID",
            "oracle_access": "post-forward scalar correctness sign only",
        },
        "expected_activity": {
            "real_training_episodes": 5_120,
            "optimizer_updates": 1_280,
            "evaluation_episodes": 1_280,
            "checkpoints_total": 10,
        },
        "caps": dict(B3_CAPS),
        "result_bearing_runs": 0 if technical_only else 1,
        "retry_rescue_sweep_extra_arm_seed_checkpoint": 0,
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
    return tuple(issues)


def _git_binding(repo_root: Path, source_revision: str) -> list[str]:
    issues: list[str] = []
    def git(*arguments: str) -> str:
        return subprocess.run(["git", *arguments], cwd=repo_root, check=True, capture_output=True, text=True).stdout.strip()
    try:
        actual = git("rev-parse", "HEAD")
        if actual != source_revision:
            issues.append(f"source revision {source_revision} != checkout HEAD {actual}")
        tracked = set(git("ls-files", "--", *B3_RUNTIME_PATHS).splitlines())
        if tracked != set(B3_RUNTIME_PATHS):
            issues.append("B3 claim and runtime dependency path set is not fully tracked")
        dirty = git("status", "--porcelain=v1", "--untracked-files=all", "--", *B3_RUNTIME_PATHS)
        if dirty:
            issues.append("B3 claim or runtime dependency paths differ from HEAD")
        if subprocess.run(["git", "merge-base", "--is-ancestor", B3_ACCEPTED_B2_SOURCE, actual], cwd=repo_root, check=False).returncode != 0:
            issues.append("accepted B2 source is not an ancestor")
    except (OSError, subprocess.CalledProcessError) as error:
        issues.append(f"Git source binding failed: {error}")
    return issues


def preflight_report(manifest: Mapping[str, object], *, repo_root: Path | None = None) -> dict[str, object]:
    gate_issues = {f"P{index}": [] for index in range(9)}
    gate_issues["P0"].extend(validate_manifest(manifest))
    if manifest.get("technical_only") is False:
        if repo_root is None:
            gate_issues["P0"].append("result-bearing preflight requires repo_root")
        else:
            gate_issues["P0"].extend(_git_binding(repo_root, str(manifest["source_revision"])))
    seeds = seed_report()
    if not seeds["all_b3_seeds_unique"] or seeds["collision_with_b1v2_seed_values"] or seeds["collision_with_b2_seed_values"] or seeds["identity_collision_with_predecessors"]:
        gate_issues["P1"].append("B3 RNG namespace is not fresh and collision-free")
    unit_id, root = B3_UNITS[0]
    models, optimizers = _new_learners(unit_id, root)
    parameter_hashes = {arm: digest(model_payload(model)) for arm, model in models.items()}
    optimizer_hashes = {arm: digest(optimizer_payload(opt)) for arm, opt in optimizers.items()}
    if len(set(parameter_hashes.values())) != 1 or len(set(optimizer_hashes.values())) != 1:
        gate_issues["P2"].append("initial parameter/Adam states differ")
    proof = _gradient_and_noninterference_proof(models, optimizers)
    if not proof["hash_identity"]:
        gate_issues["P3"].append("bridge mutated original generator state")
    route = proof["bridge_route"]
    if route["max_abs_magnitude_error"] != 0.0 or not proof["finite_nonzero_actor_composite_gradient"]:
        gate_issues["P4"].append("credit-sign magnitude/gradient proof failed")
    if not all(_observation_firewall(_synthetic_history(cue, owner_epoch=f"P5-{cue}")) for cue in (0, 1)):
        gate_issues["P5"].append("oracle observation firewall failed")
    if not all(_schedule_contract(_schedule_with_receipt(unit, decimal_root)[0]) for unit, decimal_root in B3_UNITS):
        gate_issues["P6"].append("balanced 128x8 schedule failed")
    if not b2._evaluator_sentinels()["valid"]:
        gate_issues["P7"].append("evaluator sentinel failed")
    if tuple(manifest.get("rng_streams", ())) != B3_STREAMS:
        gate_issues["P8"].append("RNG allow-list mismatch")
    report = {
        "artifact_kind": "vsp02_b3_preflight",
        "assignment_id": B3_ASSIGNMENT_ID,
        "manifest_identity": manifest_identity(manifest),
        "gates": {gate: {"passed": not issues, "issues": issues} for gate, issues in gate_issues.items()},
        "all_passed": not any(gate_issues.values()),
        "initial_parameter_hashes": parameter_hashes,
        "initial_optimizer_hashes": optimizer_hashes,
        "architectures": {arm: _architecture_payload(model) for arm, model in models.items()},
        "noninterference_and_bridge_route": proof,
        "oracle_firewall": True,
        "rng": seeds,
        "activity": _zero_activity(),
    }
    report["evidence_digest"] = digest(report)
    return report


def validate_preflight_evidence(manifest: Mapping[str, object], preflight: Mapping[str, object]) -> tuple[str, ...]:
    # Pure retained validation: no treatment, host, model, Adam, optimizer
    # step, learner, or evaluator object is constructed or invoked.
    issues: list[str] = []
    if preflight.get("artifact_kind") != "vsp02_b3_preflight" or preflight.get("assignment_id") != B3_ASSIGNMENT_ID:
        issues.append("preflight identity mismatch")
    if preflight.get("manifest_identity") != manifest_identity(manifest):
        issues.append("preflight manifest binding mismatch")
    unsigned = dict(preflight); retained_digest = unsigned.pop("evidence_digest", None)
    if retained_digest != digest(unsigned):
        issues.append("preflight artifact mutation or evidence digest mismatch")
    gates = preflight.get("gates")
    if not isinstance(gates, Mapping) or tuple(sorted(gates)) != tuple(f"P{i}" for i in range(9)):
        issues.append("P0-P8 gate set mismatch")
    else:
        passed: list[bool] = []
        for gate in (f"P{i}" for i in range(9)):
            evidence = gates[gate]
            if not isinstance(evidence, Mapping) or not isinstance(evidence.get("issues"), list):
                issues.append(f"{gate} schema mismatch"); continue
            expected_pass = not evidence["issues"]
            if evidence.get("passed") is not expected_pass:
                issues.append(f"{gate} passed flag mismatch")
            passed.append(expected_pass)
        if preflight.get("all_passed") is not all(passed):
            issues.append("preflight all_passed mismatch")
    seeds = preflight.get("rng")
    if not isinstance(seeds, Mapping) or seeds != seed_report():
        issues.append("preflight RNG evidence mismatch")
    parameters, optimizers = preflight.get("initial_parameter_hashes"), preflight.get("initial_optimizer_hashes")
    if not isinstance(parameters, Mapping) or set(parameters) != set(B3_ARMS) or len(set(parameters.values())) != 1:
        issues.append("preflight initial parameter equality mismatch")
    if not isinstance(optimizers, Mapping) or set(optimizers) != set(B3_ARMS) or len(set(optimizers.values())) != 1:
        issues.append("preflight initial Adam equality mismatch")
    if preflight.get("activity") != _zero_activity():
        issues.append("preflight has scientific activity")
    return tuple(issues)


def _collect_batch(
    *, unit_id: str, update_index: int, rows: Sequence[Mapping[str, object]],
    original_model: b1.GRUActorCritic, event_rng: random.Random, action_rng: random.Random,
) -> tuple[list[dict[str, object]], int]:
    batch: list[dict[str, object]] = []
    transitions = 0
    for row in rows:
        event_token = event_rng.getrandbits(64)
        host = B3LifecycleHost()
        cue = int(row["true_cue"])
        cue_observation = host.reset(
            lifecycle_id=f"{B3_ASSIGNMENT_ID}/{unit_id}/TRAIN/{int(row['episode_index']):04d}/{event_token:016x}",
            owner_epoch=str(row["owner_epoch"]), true_cue=cue, presented_cue=cue,
        )
        observations = [asdict(cue_observation), asdict(host.decision_observation())]
        if not _observation_firewall(observations):
            raise RuntimeError("training observation firewall mismatch")
        with torch.no_grad():
            _, _, probabilities_tensor, _, _ = _forward(original_model, observations)
        probabilities = [float(value) for value in probabilities_tensor]
        action = b1.Action.RELEASE if action_rng.random() < probabilities[b1.Action.RELEASE.index] else b1.Action.HOLD
        episode = host.step(action, action_probabilities=probabilities)
        immutable = {
            "O": observations, "H0": [0.0] * b1.B1_HIDDEN_SIZE,
            "M_reset": [1, 0], "M_active": [1, 1], "M_valid": [0, 1], "M_lifecycle": [0, 1],
            "A_behavior": action.value, "R": list(episode["reward_sequence"]),
            "Done": [False] * (len(episode["reward_sequence"]) - 1) + [True],
            "G": float(episode["physical_return"]), "behavior_probabilities": probabilities,
            "environment_transitions": int(episode["environment_transitions"]),
            "metadata": {
                "unit_id": unit_id, "update_index": update_index,
                "episode_index": int(row["episode_index"]), "owner_epoch": str(row["owner_epoch"]),
                "true_cue": cue, "clone_id": str(row["clone_id"]),
                "event_tape_token": f"{event_token:016x}", "physical_tape_ids": list(episode["physical_tape_ids"]),
            },
        }
        frozen = json.loads(canonical_bytes(immutable))
        batch.append(frozen)
        transitions += int(episode["environment_transitions"])
    return batch, transitions


def _immutable_row_contract(row: Mapping[str, object]) -> bool:
    if set(row) != {
        "O", "H0", "M_reset", "M_active", "M_valid", "M_lifecycle",
        "A_behavior", "R", "Done", "G", "behavior_probabilities",
        "environment_transitions", "metadata",
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
    probabilities = row.get("behavior_probabilities")
    if not isinstance(probabilities, list) or len(probabilities) != 2 or any(not math.isfinite(float(value)) for value in probabilities) or not math.isclose(sum(float(value) for value in probabilities), 1.0, rel_tol=0.0, abs_tol=1e-12):
        return False
    if row.get("environment_transitions") not in (4, 5):
        return False
    metadata = row.get("metadata")
    if not isinstance(metadata, Mapping) or metadata.get("true_cue") not in (0, 1):
        return False
    tapes = metadata.get("physical_tape_ids")
    return (
        isinstance(tapes, list) and len(tapes) == 1
        and str(tapes[0]).startswith(f"{B3_PHYSICAL_TAPE_PREFIX}/")
        and not str(tapes[0]).startswith(f"{b1.B1_ASSIGNMENT_ID}/")
        and not str(tapes[0]).startswith(f"{b2.B2_ASSIGNMENT_ID}/")
    )


def _rl_state_hashes(model: b1.GRUActorCritic, optimizer: torch.optim.Optimizer, action_rng: random.Random, successor: Mapping[str, object], batch: Sequence[Mapping[str, object]]) -> dict[str, str]:
    return {
        "rl_parameters": digest(model_payload(model)), "rl_optimizer": digest(optimizer_payload(optimizer)),
        "rl_rng": rng_digest(action_rng), "rl_successor_state": digest(successor), "immutable_batch": digest(batch),
    }


def _train_unit(unit_id: str, root: int) -> dict[str, object]:
    schedule, schedule_terminal = _schedule_with_receipt(unit_id, root)
    if not _schedule_contract(schedule):
        raise RuntimeError("schedule contract failed")
    models, optimizers = _new_learners(unit_id, root)
    event_rng = random.Random(b3_seed(unit_id, root, "train_environment_event"))
    action_rng = random.Random(b3_seed(unit_id, root, "train_action_uniform"))
    order_rngs = {arm: random.Random(b3_seed(unit_id, root, "train_minibatch_order")) for arm in B3_ARMS}
    stochastic_rngs = {arm: random.Random(b3_seed(unit_id, root, "train_stochastic_layer")) for arm in B3_ARMS}
    initial_models = {arm: digest(model_payload(model)) for arm, model in models.items()}
    initial_optimizers = {arm: digest(optimizer_payload(opt)) for arm, opt in optimizers.items()}
    updates = {arm: [] for arm in B3_ARMS}
    batches: list[dict[str, object]] = []
    receipts: list[dict[str, object]] = []
    transitions = 0
    for update_index in range(B3_UPDATES_PER_UNIT):
        batch, count = _collect_batch(
            unit_id=unit_id, update_index=update_index,
            rows=schedule[update_index * B3_BATCH_SIZE : (update_index + 1) * B3_BATCH_SIZE],
            original_model=models["RL_ORIGINAL"], event_rng=event_rng, action_rng=action_rng,
        )
        transitions += count
        frozen_digest = digest(batch)
        batches.append({"update_index": update_index, "batch_digest": frozen_digest, "rows": batch, "environment_transitions": count})
        orders = {}
        for arm in B3_ARMS:
            order = list(range(B3_BATCH_SIZE)); order_rngs[arm].shuffle(order); orders[arm] = order
        if len({tuple(order) for order in orders.values()}) != 1:
            raise RuntimeError("paired row order diverged")
        original_update = _optimizer_step("RL_ORIGINAL", models["RL_ORIGINAL"], optimizers["RL_ORIGINAL"], [batch[index] for index in orders["RL_ORIGINAL"]])
        original_update.update({"update_index": update_index, "batch_digest": frozen_digest, "batch_order": orders["RL_ORIGINAL"]})
        updates["RL_ORIGINAL"].append(original_update)
        successor = {"unit_id": unit_id, "next_update": update_index + 1, "event_rng": rng_digest(event_rng), "action_rng": rng_digest(action_rng)}
        before = _rl_state_hashes(models["RL_ORIGINAL"], optimizers["RL_ORIGINAL"], action_rng, successor, batch)
        bridge_update = _optimizer_step("CREDIT_SIGN_BRIDGE", models["CREDIT_SIGN_BRIDGE"], optimizers["CREDIT_SIGN_BRIDGE"], [batch[index] for index in orders["CREDIT_SIGN_BRIDGE"]])
        bridge_update.update({"update_index": update_index, "batch_digest": frozen_digest, "batch_order": orders["CREDIT_SIGN_BRIDGE"]})
        updates["CREDIT_SIGN_BRIDGE"].append(bridge_update)
        after = _rl_state_hashes(models["RL_ORIGINAL"], optimizers["RL_ORIGINAL"], action_rng, successor, batch)
        if before != after:
            raise RuntimeError("bridge contaminated original generator")
        receipts.append({"update_index": update_index, "batch_digest": frozen_digest, "before": before, "after": after, "hash_identity": True})
    return {
        "unit_id": unit_id, "decimal_root": root, "models": models,
        "training": {
            "real_original_generated_episodes": len(schedule), "environment_transitions": transitions,
            "cue_counts": {"0": 512, "1": 512}, "bridge_environment_episodes": 0,
            "updates_per_arm": {arm: len(updates[arm]) for arm in B3_ARMS},
            "initial_parameter_hashes": initial_models, "initial_optimizer_hashes": initial_optimizers,
            "final_parameter_hashes": {arm: digest(model_payload(model)) for arm, model in models.items()},
            "final_model_states": {arm: model_payload(model) for arm, model in models.items()},
            "final_optimizer_states": {arm: optimizer_payload(optimizers[arm]) for arm in B3_ARMS},
            "batch_records": batches, "batch_digests": [record["batch_digest"] for record in batches],
            "train_clone_ids": [str(row["clone_id"]) for row in schedule],
            "immutable_batch_identity_all_arms": True, "bridge_noninterference_all_updates": True,
            "bridge_noninterference_receipts": receipts, "updates": updates,
            "minibatch_rng_hashes": {arm: rng_digest(rng) for arm, rng in order_rngs.items()},
            "stochastic_rng_draw_counts": {arm: 0 for arm in B3_ARMS},
            "stochastic_rng_hashes": {arm: rng_digest(rng) for arm, rng in stochastic_rngs.items()},
            "terminal_rng_hashes": {
                "train_owner_cue_clone": schedule_terminal, "train_environment_event": rng_digest(event_rng),
                "train_action_uniform": rng_digest(action_rng),
            },
        },
    }


def _evaluation_panel_with_receipt(unit_id: str, root: int) -> tuple[list[dict[str, object]], dict[str, str]]:
    cue_rng = random.Random(b3_seed(unit_id, root, "evaluation_owner_cue_clone"))
    event_rng = random.Random(b3_seed(unit_id, root, "evaluation_environment_event"))
    cues = [0] * 64 + [1] * 64; cue_rng.shuffle(cues)
    panel = [{"clone_id": f"{unit_id}/EVAL/{index:03d}", "owner_epoch": f"{unit_id}-EV-{index:03d}", "true_cue": cue, "event_tape_token": f"{event_rng.getrandbits(64):016x}"} for index, cue in enumerate(cues)]
    return panel, {"evaluation_owner_cue_clone": rng_digest(cue_rng), "evaluation_environment_event": rng_digest(event_rng)}


def _evaluate_arm_unit(*, unit_id: str, arm: str, model: b1.GRUActorCritic, panel: Sequence[Mapping[str, object]], panel_rng_terminal_hashes: Mapping[str, str]) -> dict[str, object]:
    release_by_cue: dict[int, list[float]] = {0: [], 1: []}
    choices: dict[int, list[str | None]] = {0: [], 1: []}
    records: list[dict[str, object]] = []
    transitions = 0
    for index, row in enumerate(panel):
        cue = int(row["true_cue"])
        host = B3LifecycleHost()
        cue_observation = host.reset(
            lifecycle_id=f"{B3_ASSIGNMENT_ID}/{unit_id}/{arm}/EVAL/{index:03d}/{row['event_tape_token']}",
            owner_epoch=str(row["owner_epoch"]), true_cue=cue, presented_cue=cue,
        )
        observations = [asdict(cue_observation), asdict(host.decision_observation())]
        with torch.no_grad(): logits, raw, probabilities, _, _ = _forward(model, observations)
        if not torch.isfinite(logits).all() or not torch.isfinite(raw).all() or not torch.isfinite(probabilities).all():
            raise RuntimeError("nonfinite evaluation")
        q_release, q_hold = (float(value) for value in raw)
        choice = b1.Action.RELEASE.value if q_release > q_hold else b1.Action.HOLD.value if q_hold > q_release else None
        release_by_cue[cue].append(q_release); choices[cue].append(choice)
        executed = b1.Action(choice) if choice is not None else b1.Action.HOLD
        episode = host.step(executed, action_probabilities=[float(value) for value in probabilities])
        transitions += int(episode["environment_transitions"])
        records.append({"clone_id": row["clone_id"], "true_cue": cue, "logits": [float(value) for value in logits], "raw_softmax": [float(value) for value in raw], "behavior_probabilities": [float(value) for value in probabilities], "argmax_action": choice, "environment_transitions": int(episode["environment_transitions"])})
    q0, q1 = sum(release_by_cue[0]) / 64, sum(release_by_cue[1]) / 64
    correct = all(value == b1.Action.HOLD.value for value in choices[0]) and all(value == b1.Action.RELEASE.value for value in choices[1])
    ties = sum(value is None for values in choices.values() for value in values)
    return {
        "unit_id": unit_id, "arm": arm, "checkpoint_id": f"{unit_id}/{arm}/FINAL-128",
        "panel_digest": digest(panel), "panel_rng_terminal_hashes": dict(panel_rng_terminal_hashes),
        "episodes": 128, "cue_counts": {"0": 64, "1": 64}, "environment_transitions": transitions,
        "finite_logits": True, "argmax_ties": ties, "exact_correct_unit": correct and ties == 0,
        "q_0": q0, "q_1": q1, **_mixture_metrics_from_raw_q(q0=q0, q1=q1),
        "evaluation_updates": 0, "stochastic_action_draws": 0, "clone_records": records,
        "final_model_hash": digest(model_payload(model)),
    }


def _arm_aggregate(metrics: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        "units": len(metrics),
        "exact_correct_units": sum(bool(metric["exact_correct_unit"]) for metric in metrics),
        "mean_j_eval": sum(float(metric["j_eval"]) for metric in metrics) / len(metrics),
        "mean_kappa": sum(float(metric["kappa"]) for metric in metrics) / len(metrics),
    }


def classify_b3(*, valid: bool, aggregates: Mapping[str, Mapping[str, object]] | None, bridge_exposure_valid: bool) -> str:
    if not valid or aggregates is None:
        return "B3_INCONCLUSIVE_OR_INVALID"
    original, bridge = aggregates["RL_ORIGINAL"], aggregates["CREDIT_SIGN_BRIDGE"]
    if (
        bridge["exact_correct_units"] == 5 and original["exact_correct_units"] == 0
        and float(bridge["mean_j_eval"]) - 1.0 > 0.05 and float(bridge["mean_kappa"]) >= 0.70
        and bridge_exposure_valid
    ):
        return "B3_SIGN_BRIDGE_LOCAL_SUFFICIENCY"
    if bridge["exact_correct_units"] == 0 and original["exact_correct_units"] == 0 and bridge_exposure_valid:
        return "B3_SIGN_ONLY_INSUFFICIENT"
    return "B3_INCONCLUSIVE_OR_INVALID"


def _zero_activity() -> dict[str, int]:
    return {"result_bearing_runs": 0, "real_training_episodes": 0, "evaluation_episodes": 0, "environment_transitions": 0, "optimizer_updates": 0, "checkpoints_total": 0, "retries_rescues_sweeps": 0}


def run_treatment(manifest: Mapping[str, object], *, repo_root: Path | None = None) -> dict[str, object]:
    preflight = preflight_report(manifest, repo_root=repo_root)
    base: dict[str, object] = {
        "artifact_kind": "vsp02_b3_result", "assignment_id": B3_ASSIGNMENT_ID,
        "candidate": B3_CANDIDATE, "manifest": dict(manifest),
        "manifest_identity": manifest_identity(manifest), "preflight": preflight,
    }
    if not preflight["all_passed"]:
        result = {
            **base,
            "branch": "B3_INCONCLUSIVE_OR_INVALID",
            "activity": _zero_activity(),
            "activity_valid": False,
            "bridge_exposure_valid": False,
            "runtime_contract": None,
            "units": [],
            "aggregates": None,
            "evaluation": None,
        }
        result["evidence_digest"] = digest(result)
        return result
    if manifest.get("technical_only") is not False:
        raise ValueError("treatment requires registered technical_only=false manifest")
    units = [_train_unit(unit, root) for unit, root in B3_UNITS]
    evaluations: dict[str, list[dict[str, object]]] = {arm: [] for arm in B3_ARMS}
    evaluation_transitions = 0
    for unit in units:
        unit_id, root = str(unit["unit_id"]), int(unit["decimal_root"])
        panel, terminal = _evaluation_panel_with_receipt(unit_id, root)
        unit["evaluation_panel_digest"] = digest(panel)
        unit["evaluation_clone_ids"] = [str(row["clone_id"]) for row in panel]
        models = unit.pop("models")
        for arm in B3_ARMS:
            metric = _evaluate_arm_unit(unit_id=unit_id, arm=arm, model=models[arm], panel=panel, panel_rng_terminal_hashes=terminal)
            evaluations[arm].append(metric); evaluation_transitions += int(metric["environment_transitions"])
    aggregates = {arm: _arm_aggregate(metrics) for arm, metrics in evaluations.items()}
    exposure_valid = all(
        sum(update["correctness_class_counts"]["-1"] for update in unit["training"]["updates"]["CREDIT_SIGN_BRIDGE"]) > 0
        and sum(update["correctness_class_counts"]["+1"] for update in unit["training"]["updates"]["CREDIT_SIGN_BRIDGE"]) > 0
        and sum(update["actual_sign_change_count"] for update in unit["training"]["updates"]["CREDIT_SIGN_BRIDGE"]) > 0
        and all(
            math.isfinite(float(update["actor_gradient_norm"]))
            and float(update["actor_gradient_norm"]) > 0.0
            for update in unit["training"]["updates"]["CREDIT_SIGN_BRIDGE"]
        )
        for unit in units
    )
    training_transitions = sum(int(unit["training"]["environment_transitions"]) for unit in units)
    activity = {
        "result_bearing_runs": 1, "real_training_episodes": 5_120, "evaluation_episodes": 1_280,
        "environment_transitions": training_transitions + evaluation_transitions,
        "optimizer_updates": 1_280, "checkpoints_total": 10, "retries_rescues_sweeps": 0,
    }
    valid = activity["environment_transitions"] <= B3_CAPS["environment_transitions_total"] and exposure_valid
    result = {
        **base, "branch": classify_b3(valid=valid, aggregates=aggregates, bridge_exposure_valid=exposure_valid),
        "activity": activity, "activity_valid": valid, "bridge_exposure_valid": exposure_valid,
        "runtime_contract": {
            "arms": list(B3_ARMS), "sole_generator": "RL_ORIGINAL",
            "initial_parameter_optimizer_equality": True, "immutable_batch_identity_same_order": True,
            "bridge_noninterference": True, "oracle_scalar_only": True,
            "critic_entropy_optimizer_clip_evaluation_invariant": True,
        },
        "units": units, "aggregates": aggregates, "evaluation": evaluations,
        "nonclaims": ["privileged correctness sign may exceed return information", "off-policy bridge is conditional on original generator", "shared gradients, Adam and clipping may diverge after intervention", "no C-level, promotion, retirement, retry, rescue, or successor claim"],
    }
    result["evidence_digest"] = digest(result)
    return result


def validate_result(manifest: object, result: object, *, repo_root: Path | None = None) -> tuple[str, ...]:
    """Validate retained evidence without invoking host/model/trainer/evaluator runtime."""
    issues = list(validate_manifest(manifest))
    if not isinstance(manifest, Mapping) or not isinstance(result, Mapping):
        return tuple(issues + ["manifest/result must be objects"])
    if result.get("artifact_kind") != "vsp02_b3_result" or result.get("assignment_id") != B3_ASSIGNMENT_ID or result.get("candidate") != B3_CANDIDATE:
        issues.append("result identity mismatch")
    if result.get("manifest") != manifest or result.get("manifest_identity") != manifest_identity(manifest):
        issues.append("result manifest binding mismatch")
    unsigned = dict(result); retained_digest = unsigned.pop("evidence_digest", None)
    if retained_digest != digest(unsigned):
        issues.append("retained artifact mutation or evidence digest mismatch")
    preflight = result.get("preflight")
    if not isinstance(preflight, Mapping):
        return tuple(issues + ["preflight evidence missing"])
    issues.extend(validate_preflight_evidence(manifest, preflight))
    if preflight.get("all_passed") is False:
        if (
            result.get("branch") != "B3_INCONCLUSIVE_OR_INVALID"
            or result.get("activity") != _zero_activity()
            or result.get("activity_valid") is not False
            or result.get("bridge_exposure_valid") is not False
            or result.get("runtime_contract") is not None
            or result.get("units") != []
            or result.get("aggregates") is not None
            or result.get("evaluation") is not None
        ):
            issues.append("failed-construction result must be zero-activity B3_INCONCLUSIVE_OR_INVALID")
        return tuple(issues)
    if result.get("branch") not in B3_BRANCH_PRECEDENCE:
        issues.append("unknown B3 branch")
    if manifest.get("technical_only") is not False or manifest.get("result_bearing_runs") != 1:
        issues.append("runtime result requires registered full manifest")
        return tuple(issues)
    units, evaluations = result.get("units"), result.get("evaluation")
    if not isinstance(units, list) or len(units) != 5:
        issues.append("exactly five fresh unit records required")
    if not isinstance(evaluations, Mapping) or set(evaluations) != set(B3_ARMS) or any(not isinstance(evaluations.get(arm), list) or len(evaluations[arm]) != 5 for arm in B3_ARMS):
        issues.append("exactly ten arm/unit evaluations required")
    activity = result.get("activity")
    if not isinstance(activity, Mapping) or any(activity.get(key) != value for key, value in {"result_bearing_runs": 1, "real_training_episodes": 5_120, "evaluation_episodes": 1_280, "optimizer_updates": 1_280, "checkpoints_total": 10, "retries_rescues_sweeps": 0}.items()):
        issues.append("activity projection mismatch")
    if isinstance(activity, Mapping) and int(activity.get("environment_transitions", B3_CAPS["environment_transitions_total"] + 1)) > B3_CAPS["environment_transitions_total"]:
        issues.append("transition cap exceeded")
    training_transitions = 0
    exposure_by_unit: dict[str, bool] = {}
    final_hashes_by_unit: dict[str, Mapping[str, object]] = {}
    if isinstance(units, list):
        for index, expected in enumerate(B3_UNITS):
            if index >= len(units) or not isinstance(units[index], Mapping): continue
            unit = units[index]; training = unit.get("training")
            if (unit.get("unit_id"), unit.get("decimal_root")) != expected or not isinstance(training, Mapping):
                issues.append(f"unit {index} identity/training mismatch"); continue
            if training.get("updates_per_arm") != {arm: 128 for arm in B3_ARMS} or training.get("real_original_generated_episodes") != 1_024 or training.get("bridge_environment_episodes") != 0:
                issues.append(f"{expected[0]} activity mismatch")
            if training.get("cue_counts") != {"0": 512, "1": 512} or training.get("immutable_batch_identity_all_arms") is not True or training.get("bridge_noninterference_all_updates") is not True:
                issues.append(f"{expected[0]} support/noninterference mismatch")
            initial_parameters = training.get("initial_parameter_hashes")
            initial_optimizers = training.get("initial_optimizer_hashes")
            if not isinstance(initial_parameters, Mapping) or set(initial_parameters) != set(B3_ARMS) or len(set(initial_parameters.values())) != 1:
                issues.append(f"{expected[0]} initial parameter equality mismatch")
            if not isinstance(initial_optimizers, Mapping) or set(initial_optimizers) != set(B3_ARMS) or len(set(initial_optimizers.values())) != 1:
                issues.append(f"{expected[0]} initial Adam equality mismatch")
            batches = training.get("batch_records")
            batch_digests: list[str] = []
            if not isinstance(batches, list) or len(batches) != 128:
                issues.append(f"{expected[0]} batch record count mismatch")
            else:
                for update_index, record in enumerate(batches):
                    if not isinstance(record, Mapping) or record.get("update_index") != update_index:
                        issues.append(f"{expected[0]}/{update_index} batch identity mismatch"); continue
                    rows = record.get("rows")
                    if not isinstance(rows, list) or len(rows) != 8 or any(not isinstance(row, Mapping) or not _immutable_row_contract(row) for row in rows):
                        issues.append(f"{expected[0]}/{update_index} immutable rows invalid"); continue
                    batch_digest = digest(rows); batch_digests.append(batch_digest)
                    if record.get("batch_digest") != batch_digest:
                        issues.append(f"{expected[0]}/{update_index} batch digest mismatch")
                    if Counter(int(row["metadata"]["true_cue"]) for row in rows) != Counter({0: 4, 1: 4}):
                        issues.append(f"{expected[0]}/{update_index} cue balance mismatch")
                    projected_transitions = sum(int(row["environment_transitions"]) for row in rows)
                    if record.get("environment_transitions") != projected_transitions:
                        issues.append(f"{expected[0]}/{update_index} transition projection mismatch")
                    training_transitions += projected_transitions
            if training.get("batch_digests") != batch_digests:
                issues.append(f"{expected[0]} batch digest projection mismatch")
            updates = training.get("updates")
            if not isinstance(updates, Mapping) or set(updates) != set(B3_ARMS):
                issues.append(f"{expected[0]} update arms mismatch"); continue
            common_orders: list[list[int]] | None = None
            bridge_negative = bridge_positive = bridge_changes = 0
            bridge_actor_gradients_valid = True
            for arm in B3_ARMS:
                arm_updates = updates.get(arm)
                if not isinstance(arm_updates, list) or len(arm_updates) != 128:
                    issues.append(f"{expected[0]}/{arm} update count mismatch"); continue
                expected_route = ORIGINAL_ACTOR_ROUTE if arm == "RL_ORIGINAL" else BRIDGE_ACTOR_ROUTE
                orders: list[list[int]] = []
                previous_parameter = initial_parameters.get(arm) if isinstance(initial_parameters, Mapping) else None
                previous_optimizer = initial_optimizers.get(arm) if isinstance(initial_optimizers, Mapping) else None
                for update_index, update in enumerate(arm_updates):
                    if not isinstance(update, Mapping) or update.get("update_index") != update_index or update.get("actor_route") != expected_route or update.get("critic_route") != CRITIC_ROUTE or update.get("advantage_count") != 8 or update.get("max_abs_magnitude_error") != 0.0:
                        issues.append(f"{expected[0]}/{arm}/{update_index} route or advantage mismatch"); break
                    order = update.get("batch_order"); orders.append(order if isinstance(order, list) else [])
                    if not isinstance(order, list) or sorted(order) != list(range(8)) or update_index >= len(batch_digests) or update.get("batch_digest") != batch_digests[update_index]:
                        issues.append(f"{expected[0]}/{arm}/{update_index} batch/order binding mismatch")
                    if update.get("parameters_before") != previous_parameter or update.get("optimizer_before") != previous_optimizer:
                        issues.append(f"{expected[0]}/{arm}/{update_index} parameter/Adam chain mismatch")
                    previous_parameter, previous_optimizer = update.get("parameters_after"), update.get("optimizer_after")
                    for field in ("loss", "actor_loss", "critic_loss", "gradient_norm_before_clip", "actor_gradient_norm"):
                        if not math.isfinite(float(update.get(field, math.nan))):
                            issues.append(f"{expected[0]}/{arm}/{update_index} nonfinite {field}")
                    if update.get("clip_threshold") != 1.0:
                        issues.append(f"{expected[0]}/{arm}/{update_index} clip mismatch")
                    if arm == "RL_ORIGINAL" and update.get("correctness_class_counts") != {"-1": 0, "+1": 0}:
                        issues.append(f"{expected[0]}/{arm}/{update_index} oracle contamination")
                    if arm == "CREDIT_SIGN_BRIDGE":
                        counts = update.get("correctness_class_counts")
                        if not isinstance(counts, Mapping) or int(counts.get("-1", -1)) + int(counts.get("+1", -1)) != 8 or update.get("oracle_scalar_only") is not True:
                            issues.append(f"{expected[0]}/{arm}/{update_index} oracle/coefficient exposure mismatch")
                        else:
                            bridge_negative += int(counts["-1"]); bridge_positive += int(counts["+1"])
                        bridge_changes += int(update.get("actual_sign_change_count", 0))
                        bridge_actor_gradients_valid = bridge_actor_gradients_valid and float(update.get("actor_gradient_norm", 0.0)) > 0.0
                if common_orders is None:
                    common_orders = orders
                elif orders != common_orders:
                    issues.append(f"{expected[0]} paired row order mismatch")
                final_hashes = training.get("final_parameter_hashes")
                final_models = training.get("final_model_states")
                final_optimizers = training.get("final_optimizer_states")
                if not isinstance(final_hashes, Mapping) or final_hashes.get(arm) != previous_parameter or not isinstance(final_models, Mapping) or digest(final_models.get(arm)) != previous_parameter or not isinstance(final_optimizers, Mapping) or digest(final_optimizers.get(arm)) != previous_optimizer:
                    issues.append(f"{expected[0]}/{arm} final checkpoint/Adam binding mismatch")
            exposure_by_unit[expected[0]] = bridge_negative > 0 and bridge_positive > 0 and bridge_changes > 0 and bridge_actor_gradients_valid
            final_hashes_by_unit[expected[0]] = training.get("final_parameter_hashes") if isinstance(training.get("final_parameter_hashes"), Mapping) else {}
            receipts = training.get("bridge_noninterference_receipts")
            if not isinstance(receipts, list) or len(receipts) != 128 or any(not isinstance(receipt, Mapping) or receipt.get("before") != receipt.get("after") or receipt.get("hash_identity") is not True or receipt.get("batch_digest") not in batch_digests for receipt in receipts):
                issues.append(f"{expected[0]} generator noninterference receipt mismatch")
    derived_metrics: dict[str, list[Mapping[str, object]]] = {arm: [] for arm in B3_ARMS}
    evaluation_transitions = 0
    checkpoints: set[str] = set()
    if isinstance(evaluations, Mapping) and set(evaluations) == set(B3_ARMS):
        for unit_index, (unit_id, _) in enumerate(B3_UNITS):
            panel_digests: list[str] = []
            for arm in B3_ARMS:
                metrics = evaluations.get(arm)
                if not isinstance(metrics, list) or unit_index >= len(metrics) or not isinstance(metrics[unit_index], Mapping):
                    continue
                metric = metrics[unit_index]
                derived_metrics[arm].append(metric); panel_digests.append(str(metric.get("panel_digest", "")))
                records = metric.get("clone_records")
                if metric.get("unit_id") != unit_id or metric.get("arm") != arm or metric.get("episodes") != 128 or metric.get("cue_counts") != {"0": 64, "1": 64} or metric.get("evaluation_updates") != 0 or metric.get("stochastic_action_draws") != 0 or metric.get("finite_logits") is not True:
                    issues.append(f"{unit_id}/{arm} evaluation contract mismatch")
                if not isinstance(records, list) or len(records) != 128 or any(
                    not isinstance(record, Mapping)
                    or record.get("true_cue") not in (0, 1)
                    or not isinstance(record.get("logits"), list)
                    or len(record.get("logits", ())) != 2
                    or not isinstance(record.get("raw_softmax"), list)
                    or len(record.get("raw_softmax", ())) != 2
                    or not isinstance(record.get("behavior_probabilities"), list)
                    or len(record.get("behavior_probabilities", ())) != 2
                    or any(
                        not math.isfinite(float(value))
                        for value in (*record.get("logits", ()), *record.get("raw_softmax", ()), *record.get("behavior_probabilities", ()))
                    )
                    for record in records
                ):
                    issues.append(f"{unit_id}/{arm} retained evaluation rows invalid")
                else:
                    q_by_cue = {cue: [float(record["raw_softmax"][0]) for record in records if record.get("true_cue") == cue] for cue in (0, 1)}
                    if any(len(values) != 64 for values in q_by_cue.values()):
                        issues.append(f"{unit_id}/{arm} evaluation cue support mismatch")
                    else:
                        q0, q1 = sum(q_by_cue[0]) / 64, sum(q_by_cue[1]) / 64
                        expected_metrics = {"q_0": q0, "q_1": q1, **_mixture_metrics_from_raw_q(q0=q0, q1=q1)}
                        if any(not math.isclose(float(metric.get(field, math.nan)), value, rel_tol=0.0, abs_tol=1e-12) for field, value in expected_metrics.items()):
                            issues.append(f"{unit_id}/{arm} metric projection mismatch")
                        choices = {cue: [record.get("argmax_action") for record in records if record.get("true_cue") == cue] for cue in (0, 1)}
                        ties = sum(value is None for values in choices.values() for value in values)
                        exact = ties == 0 and all(value == b1.Action.HOLD.value for value in choices[0]) and all(value == b1.Action.RELEASE.value for value in choices[1])
                        if metric.get("argmax_ties") != ties or metric.get("exact_correct_unit") is not exact:
                            issues.append(f"{unit_id}/{arm} exact classification mismatch")
                if metric.get("final_model_hash") != final_hashes_by_unit.get(unit_id, {}).get(arm):
                    issues.append(f"{unit_id}/{arm} evaluation checkpoint binding mismatch")
                evaluation_transitions += int(metric.get("environment_transitions", 0)); checkpoints.add(str(metric.get("checkpoint_id", "")))
            if len(panel_digests) != 2 or len(set(panel_digests)) != 1:
                issues.append(f"{unit_id} common evaluation panel mismatch")
    derived_aggregates = {arm: _arm_aggregate(metrics) for arm, metrics in derived_metrics.items()} if all(len(metrics) == 5 for metrics in derived_metrics.values()) else None
    if result.get("aggregates") != derived_aggregates:
        issues.append("aggregate projection mismatch")
    exposure_valid = len(exposure_by_unit) == 5 and all(exposure_by_unit.values())
    if result.get("bridge_exposure_valid") is not exposure_valid:
        issues.append("bridge exposure projection mismatch")
    activity_projection = {
        "result_bearing_runs": 1, "real_training_episodes": 5_120,
        "evaluation_episodes": sum(int(metric.get("episodes", 0)) for metrics in derived_metrics.values() for metric in metrics),
        "environment_transitions": training_transitions + evaluation_transitions,
        "optimizer_updates": 1_280, "checkpoints_total": len(checkpoints), "retries_rescues_sweeps": 0,
    }
    if result.get("activity") != activity_projection:
        issues.append("activity differs from retained records")
    runtime_contract = {
        "arms": list(B3_ARMS), "sole_generator": "RL_ORIGINAL",
        "initial_parameter_optimizer_equality": True, "immutable_batch_identity_same_order": True,
        "bridge_noninterference": True, "oracle_scalar_only": True,
        "critic_entropy_optimizer_clip_evaluation_invariant": True,
    }
    if result.get("runtime_contract") != runtime_contract:
        issues.append("runtime contract mismatch")
    derived_valid = not issues and exposure_valid and activity_projection["environment_transitions"] <= B3_CAPS["environment_transitions_total"] and activity_projection["evaluation_episodes"] == 1_280 and len(checkpoints) == 10
    if result.get("activity_valid") is not derived_valid:
        issues.append("activity_valid projection mismatch")
    expected_branch = classify_b3(valid=derived_valid, aggregates=derived_aggregates, bridge_exposure_valid=exposure_valid)
    if result.get("branch") != expected_branch:
        issues.append(f"branch precedence mismatch: expected {expected_branch}")
    if repo_root is None:
        issues.append("runtime retained validation requires source-binding repo_root")
    else:
        issues.extend(_git_binding(repo_root, str(manifest["source_revision"])))
    return tuple(issues)

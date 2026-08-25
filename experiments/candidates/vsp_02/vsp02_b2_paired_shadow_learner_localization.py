"""VSP02-B2 paired shadow-learner localization.

RL_ORIGINAL is the only policy that acts in the training host.  Every update
freezes its eight real episodes before three independently owned learner clones
consume the same ordered batch.  The two supervised clones replace only the
lifecycle actor term; the accepted B1V2 critic route remains unchanged.
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
from typing import Iterable, Mapping, Sequence

import torch
from torch import Tensor, nn

from experiments.candidates.vsp_02 import (
    learned_cue_conditioned_lifecycle_control_v2 as b1,
)


B2_SCHEMA_VERSION = 1
B2_ASSIGNMENT_ID = "VSP02-B2-PAIRED-SHADOW-LEARNER-LOCALIZATION"
B2_CANDIDATE = "CAND-VSP-02@adversarial-revision-v8"
B2_HOST_ID = "VSP02-A2-PHYSICAL-LIFECYCLE-HOST-v1"
B2_RESOURCE_CLASS = "B_TOY_LIGHT"
B2_POOL_UNITS = 1
B2_PHYSICAL_TAPE_PREFIX = f"{B2_ASSIGNMENT_ID}/PHYSICAL"
B2_ACCEPTED_PRECURSOR_SOURCE = "89fe924883b3ee768e30126ed51cc49644dfcf72"
B2_ACCEPTED_PRECURSOR_PUBLICATION = "eb2cb349075f369c244f1ae33a434be28c0177e7"
B2_SEED_PREFIX = "VSP02-B2-V1\0"
B2_UNITS = tuple((f"VSP02-B2-U{index:02d}", 22_020_000 + index) for index in range(1, 6))
B2_STREAMS = (
    "parameter_initialization",
    "optimizer_initialization",
    "train_owner_cue_clone",
    "train_environment_event",
    "train_action_uniform",
    "train_minibatch_order",
    "train_stochastic_layer",
    "evaluation_owner_cue_clone",
    "evaluation_environment_event",
)
B2_ARMS = ("RL_ORIGINAL", "SUP_TRUE", "SUP_FLIP")
B2_UPDATES_PER_UNIT = 128
B2_BATCH_SIZE = 8
B2_TRAIN_EPISODES_PER_UNIT = 1_024
B2_EVAL_EPISODES_PER_UNIT_ARM = 128
B2_BRANCH_PRECEDENCE = (
    "B2_NO_CONSTRUCTION",
    "B2_INVALID_RUNTIME_CONTRACT",
    "B2_ACTIVITY_SUPPORT_OR_CAP_INVALID",
    "B2_SUPERVISION_CONTROL_UNCALIBRATED",
    "B2_DIRECT_SUCCEEDED_ORIGINAL_FAILED",
    "B2_BOTH_SUCCEEDED",
    "B2_DIRECT_FAILED_ORIGINAL_SUCCEEDED",
    "B2_BOTH_FAILED",
)
B2_CAPS = {
    "environment_transitions_total": 145_348,
    "real_training_episodes_total": 5_120,
    "evaluation_episodes_total": 1_920,
    "optimizer_updates_total": 1_920,
    "result_bearing_runs": 1,
    "pool_units": 1,
    "cpu_minutes": 30,
    "peak_memory_gib": 2,
}
B2_CLAIM_PATHS = (
    "experiments/candidates/vsp_02/vsp02_b2_paired_shadow_learner_localization.py",
    "scripts/run_vsp02_b2_paired_shadow_learner_localization.py",
    "tests/experiments/candidates/vsp_02/test_vsp02_b2_paired_shadow_learner_localization.py",
    "docs/research/candidates/vsp_02/VSP02_B2_CODE_SCIENCE_INDEX.md",
)
B2_PRECURSOR_PATHS = (
    "experiments/candidates/vsp_02/learned_cue_conditioned_lifecycle_control_v2.py",
    "experiments/candidates/vsp_02/owner_action_responsive_lifecycle.py",
)


class B2LifecycleHost(b1.LifecycleHost):
    """Accepted physical host with fresh B2-only tape identity."""

    def step(
        self,
        action: b1.Action,
        *,
        action_probabilities: Sequence[float],
    ) -> dict[str, object]:
        if not self._open or self.escrow is not None:
            raise RuntimeError("episode action can be committed exactly once")
        if len(action_probabilities) != 2:
            raise ValueError("RELEASE/HOLD probabilities required")
        probabilities = tuple(float(value) for value in action_probabilities)
        if (
            any(not math.isfinite(value) or value < 0.0 for value in probabilities)
            or abs(sum(probabilities) - 1.0) > 1e-12
        ):
            raise ValueError("invalid action probability pair")
        decide = self.decision_observation()
        escrow_id = hashlib.sha256(
            f"{B2_ASSIGNMENT_ID}/{self.lifecycle_id}/{self.owner_epoch}/{b1.B1_BEHAVIOR_VERSION}".encode()
        ).hexdigest()
        self.escrow = b1.ActionScoreEscrow(
            escrow_id=escrow_id,
            action=action.value,
            action_probabilities=probabilities,
            selected_likelihood=probabilities[action.index],
            owner_epoch=self.owner_epoch,
            behavior_version=b1.B1_BEHAVIOR_VERSION,
        )
        tape_id = f"{B2_PHYSICAL_TAPE_PREFIX}/{self.lifecycle_id}"
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
                    tape_id=tape_id,
                    natural=True,
                    primitive_action=b1.B1_PRIMITIVE,
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
            "lifecycle_id": self.lifecycle_id,
            "owner_epoch": self.owner_epoch,
            "true_cue": self.true_cue,
            "presented_cue": self.presented_cue,
            "observations": [asdict(self._cue_observation), asdict(decide)],
            "action": action.value,
            "action_probabilities": list(probabilities),
            "selected_likelihood": probabilities[action.index],
            "lifecycle_states": list(self.states),
            "reward_sequence": list(self.rewards),
            "physical_return": physical_return,
            "physical_tape_ids": list(self.tape_ids),
            "escrow": {
                **asdict(self.escrow),
                "closed": True,
                "end_cause": end_cause.value,
                "tombstone_phase": self.record.phase.value,
                "version_advance_permitted": b1.a1.version_can_advance(
                    (self.record,), new_version=b1.B1_BEHAVIOR_VERSION + 1
                ),
            },
            "environment_transitions": self.environment_transitions,
        }


def json_ready(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [json_ready(item) for item in value]
    if isinstance(value, Tensor):
        return value.detach().cpu().tolist()
    if hasattr(value, "value"):
        return getattr(value, "value")
    return value


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        json_ready(value), ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def b2_seed(unit_id: str, decimal_root: int, stream_name: str) -> int:
    if (unit_id, decimal_root) not in B2_UNITS:
        raise ValueError(f"unregistered B2 unit/root: {unit_id}/{decimal_root}")
    if stream_name not in B2_STREAMS:
        raise ValueError(f"unregistered B2 RNG stream: {stream_name}")
    material = (
        B2_SEED_PREFIX
        + unit_id
        + "\0"
        + str(decimal_root)
        + "\0"
        + stream_name
    ).encode("utf-8")
    first8 = hashlib.sha256(material).digest()[:8]
    return 1 + (int.from_bytes(first8, "big", signed=False) % 2_147_483_646)


def seed_report() -> dict[str, object]:
    derived = {
        unit_id: {
            stream: b2_seed(unit_id, root, stream) for stream in B2_STREAMS
        }
        for unit_id, root in B2_UNITS
    }
    flat = [seed for streams in derived.values() for seed in streams.values()]
    b1_values = {
        b1.stream_seed(seed_id, stream)
        for seed_id in b1.B1_SEED_IDS
        for stream in b1.B1_RNG_STREAMS
    }
    return {
        "function": (
            '1+(uint64_be(first8(SHA256(UTF8("VSP02-B2-V1\\0"+unit_id+'
            '"\\0"+decimal_root+"\\0"+stream_name)))) mod 2147483646)'
        ),
        "streams": list(B2_STREAMS),
        "derived": derived,
        "all_b2_seeds_unique": len(flat) == len(set(flat)),
        "collision_with_b1v2_seed_values": sorted(set(flat) & b1_values),
        "identity_collision_with_b1v2": (
            B2_ASSIGNMENT_ID == b1.B1_ASSIGNMENT_ID
            or B2_PHYSICAL_TAPE_PREFIX.startswith(f"{b1.B1_ASSIGNMENT_ID}/")
            or any(unit_id in b1.B1_SEED_IDS for unit_id, _ in B2_UNITS)
        ),
    }


def _tensor_payload(tensor: Tensor) -> dict[str, object]:
    cpu = tensor.detach().cpu().contiguous()
    return {
        "dtype": str(cpu.dtype),
        "shape": list(cpu.shape),
        "values": cpu.reshape(-1).tolist(),
    }


def model_payload(model: nn.Module) -> dict[str, object]:
    return {
        name: _tensor_payload(tensor)
        for name, tensor in sorted(model.state_dict().items())
    }


def optimizer_payload(optimizer: torch.optim.Optimizer) -> dict[str, object]:
    state = optimizer.state_dict()
    return json_ready(state)  # type: ignore[return-value]


def rng_digest(rng: random.Random) -> str:
    return digest(rng.getstate())


def _architecture_payload(model: b1.GRUActorCritic) -> dict[str, object]:
    return {
        "dtype": "torch.float64",
        "recurrent": "one-layer GRUCell",
        "input_size": int(model.gru.input_size),
        "hidden_size": int(model.gru.hidden_size),
        "actor_logits": int(model.actor.out_features),
        "critic_outputs": int(model.critic.out_features),
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "state_shapes": {
            name: list(tensor.shape) for name, tensor in sorted(model.state_dict().items())
        },
        "parameter_groups": [[name for name, _ in model.named_parameters()]],
    }


def _optimizer_contract(optimizer: torch.optim.Optimizer) -> dict[str, object]:
    group = optimizer.param_groups[0]
    return {
        "name": type(optimizer).__name__,
        "learning_rate": float(group["lr"]),
        "betas": list(group["betas"]),
        "epsilon": float(group["eps"]),
        "weight_decay": float(group["weight_decay"]),
        "amsgrad": bool(group["amsgrad"]),
        "gradient_norm_clip": 1.0,
        "batch_size": B2_BATCH_SIZE,
        "updates_per_unit": B2_UPDATES_PER_UNIT,
    }


B2_PARAMETER_ORDER = (
    "gru.weight_ih",
    "gru.weight_hh",
    "gru.bias_ih",
    "gru.bias_hh",
    "actor.weight",
    "actor.bias",
    "critic.weight",
    "critic.bias",
)


def _pure_initial_optimizer_payload() -> dict[str, object]:
    """The frozen empty Adam state, without constructing an optimizer."""

    return {
        "state": {},
        "param_groups": [
            {
                "lr": 0.003,
                "betas": [0.9, 0.999],
                "eps": 1e-08,
                "weight_decay": 0,
                "amsgrad": False,
                "maximize": False,
                "foreach": None,
                "capturable": False,
                "differentiable": False,
                "fused": None,
                "decoupled_weight_decay": False,
                "params": list(range(len(B2_PARAMETER_ORDER))),
            }
        ],
    }


def _pure_optimizer_contract() -> dict[str, object]:
    return {
        "name": "Adam",
        "learning_rate": 0.003,
        "betas": [0.9, 0.999],
        "epsilon": 1e-08,
        "weight_decay": 0.0,
        "amsgrad": False,
        "gradient_norm_clip": 1.0,
        "batch_size": B2_BATCH_SIZE,
        "updates_per_unit": B2_UPDATES_PER_UNIT,
    }


def _pure_architecture_payload() -> dict[str, object]:
    return {
        "dtype": "torch.float64",
        "recurrent": "one-layer GRUCell",
        "input_size": 10,
        "hidden_size": b1.B1_HIDDEN_SIZE,
        "actor_logits": 2,
        "critic_outputs": 1,
        "parameter_count": 1_395,
        "state_shapes": {
            "actor.bias": [2],
            "actor.weight": [2, b1.B1_HIDDEN_SIZE],
            "critic.bias": [1],
            "critic.weight": [1, b1.B1_HIDDEN_SIZE],
            "gru.bias_hh": [3 * b1.B1_HIDDEN_SIZE],
            "gru.bias_ih": [3 * b1.B1_HIDDEN_SIZE],
            "gru.weight_hh": [3 * b1.B1_HIDDEN_SIZE, b1.B1_HIDDEN_SIZE],
            "gru.weight_ih": [3 * b1.B1_HIDDEN_SIZE, 10],
        },
        "parameter_groups": [list(B2_PARAMETER_ORDER)],
    }


def _pure_seeded_parameter_payload(unit_id: str, root: int) -> dict[str, object]:
    """Registered initialization without constructing a model or touching global RNG."""

    generator = torch.Generator(device="cpu")
    generator.manual_seed(b2_seed(unit_id, root, "parameter_initialization"))
    bound = 1.0 / math.sqrt(b1.B1_HIDDEN_SIZE)

    def uniform(shape: tuple[int, ...]) -> Tensor:
        return torch.empty(shape, dtype=torch.float64).uniform_(
            -bound, bound, generator=generator
        )

    # This is the registered GRU parameter iteration order, followed by the
    # registered critic order.  Actor tensors are frozen zeros.
    parameters = {
        "gru.weight_ih": uniform((3 * b1.B1_HIDDEN_SIZE, 10)),
        "gru.weight_hh": uniform(
            (3 * b1.B1_HIDDEN_SIZE, b1.B1_HIDDEN_SIZE)
        ),
        "gru.bias_ih": uniform((3 * b1.B1_HIDDEN_SIZE,)),
        "gru.bias_hh": uniform((3 * b1.B1_HIDDEN_SIZE,)),
        "actor.weight": torch.zeros((2, b1.B1_HIDDEN_SIZE), dtype=torch.float64),
        "actor.bias": torch.zeros(2, dtype=torch.float64),
        "critic.weight": uniform((1, b1.B1_HIDDEN_SIZE)),
        "critic.bias": uniform((1,)),
    }
    return _pure_model_payload(parameters)


def _payload_tensors(payload: Mapping[str, object]) -> dict[str, Tensor]:
    tensors: dict[str, Tensor] = {}
    if set(payload) != set(B2_PARAMETER_ORDER):
        raise ValueError("model payload parameter set mismatch")
    for name in B2_PARAMETER_ORDER:
        item = payload[name]
        if not isinstance(item, Mapping):
            raise ValueError(f"{name} payload is not an object")
        shape = item.get("shape")
        values = item.get("values")
        if item.get("dtype") != "torch.float64" or not isinstance(shape, list) or not isinstance(values, list):
            raise ValueError(f"{name} payload dtype/shape/value mismatch")
        tensor = torch.tensor(values, dtype=torch.float64).reshape(tuple(int(v) for v in shape))
        tensors[name] = tensor
    return tensors


def _pure_model_payload(parameters: Mapping[str, Tensor]) -> dict[str, object]:
    return {name: _tensor_payload(parameters[name]) for name in sorted(B2_PARAMETER_ORDER)}


def _pure_optimizer_payload(
    moments: Mapping[str, tuple[Tensor, Tensor]], *, step: int
) -> dict[str, object]:
    payload = _pure_initial_optimizer_payload()
    if step:
        payload["state"] = {
            str(index): {
                "step": float(step),
                "exp_avg": json_ready(moments[name][0]),
                "exp_avg_sq": json_ready(moments[name][1]),
            }
            for index, name in enumerate(B2_PARAMETER_ORDER)
        }
    return payload


def _pure_forward_parameters(
    parameters: Mapping[str, Tensor], observations: Sequence[Mapping[str, object]]
) -> tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
    """Functional frozen GRU/heads; no learner or evaluator object is invoked."""

    hidden = torch.zeros(b1.B1_HIDDEN_SIZE, dtype=torch.float64)
    weight_ih = parameters["gru.weight_ih"]
    weight_hh = parameters["gru.weight_hh"]
    bias_ih = parameters["gru.bias_ih"]
    bias_hh = parameters["gru.bias_hh"]
    for observation in observations:
        value = b1.observation_vector(observation)
        hidden = torch._VF.gru_cell(  # type: ignore[attr-defined]
            value.unsqueeze(0),
            hidden.unsqueeze(0),
            weight_ih,
            weight_hh,
            bias_ih,
            bias_hh,
        ).squeeze(0)
    logits = parameters["actor.weight"] @ hidden + parameters["actor.bias"]
    raw_softmax = torch.softmax(logits, dim=0)
    behavior_probabilities = 0.8 * raw_softmax + 0.1
    entropy = -(behavior_probabilities * torch.log(behavior_probabilities)).sum()
    baseline = (parameters["critic.weight"] @ hidden + parameters["critic.bias"]).squeeze(0)
    return logits, raw_softmax, behavior_probabilities, baseline, entropy


def _pure_loss_terms(
    arm: str,
    parameters: Mapping[str, Tensor],
    batch: Sequence[Mapping[str, object]],
) -> tuple[Tensor, dict[str, object]]:
    actor_terms: list[Tensor] = []
    critic_terms: list[Tensor] = []
    label_targets: list[int] = []
    for row in batch:
        observations = row["O"]
        assert isinstance(observations, Sequence)
        logits, _, probabilities, baseline, entropy = _pure_forward_parameters(
            parameters, observations
        )
        physical_return = torch.tensor(float(row["G"]), dtype=torch.float64)
        critic_terms.append(0.5 * (physical_return - baseline) ** 2)
        if arm == "RL_ORIGINAL":
            action_index = b1.Action(str(row["A_behavior"])).index
            advantage = (physical_return - baseline).detach()
            actor_terms.append(
                -advantage * torch.log(probabilities[action_index]) - 0.01 * entropy
            )
        else:
            cue = int(row["metadata"]["true_cue"])  # type: ignore[index]
            target = cue if arm == "SUP_TRUE" else 1 - cue
            target_index = 0 if target == 1 else 1
            label_targets.append(target_index)
            actor_terms.append(
                torch.nn.functional.cross_entropy(
                    logits.unsqueeze(0), torch.tensor([target_index], dtype=torch.long)
                )
            )
    actor_loss = torch.stack(actor_terms).mean()
    critic_loss = torch.stack(critic_terms).mean()
    return actor_loss + critic_loss, {
        "actor_loss": float(actor_loss.detach()),
        "critic_loss": float(critic_loss.detach()),
        "label_targets": label_targets,
        "actor_route": (
            "-stop_gradient(G-b)*log(mu(A_behavior|history))-0.01*entropy"
            if arm == "RL_ORIGINAL"
            else "mean_cross_entropy(actor_logits[M_lifecycle],Y_true)"
            if arm == "SUP_TRUE"
            else "mean_cross_entropy(actor_logits[M_lifecycle],Y_flip)"
        ),
        "critic_route": "mean(0.5*(G-b)^2)",
    }


def _pure_adam_update(
    arm: str,
    parameters: Mapping[str, Tensor],
    moments: Mapping[str, tuple[Tensor, Tensor]],
    *,
    step: int,
    batch: Sequence[Mapping[str, object]],
) -> tuple[dict[str, Tensor], dict[str, tuple[Tensor, Tensor]], dict[str, object]]:
    """Recompute one frozen update as tensor math, never optimizer.step()."""

    leaves = {
        name: parameters[name].detach().clone().requires_grad_(True)
        for name in B2_PARAMETER_ORDER
    }
    before_parameters = digest(_pure_model_payload(leaves))
    before_optimizer = digest(_pure_optimizer_payload(moments, step=step))
    loss, route = _pure_loss_terms(arm, leaves, batch)
    gradients = torch.autograd.grad(loss, tuple(leaves[name] for name in B2_PARAMETER_ORDER))
    norms = torch.stack([torch.linalg.vector_norm(gradient, 2.0) for gradient in gradients])
    total_norm = torch.linalg.vector_norm(norms, 2.0)
    clip_coefficient = torch.clamp(1.0 / (total_norm + 1e-6), max=1.0)
    clipped_gradients = [gradient * clip_coefficient for gradient in gradients]
    next_step = step + 1
    beta1, beta2 = 0.9, 0.999
    bias_correction1 = 1.0 - beta1**next_step
    bias_correction2_sqrt = math.sqrt(1.0 - beta2**next_step)
    next_parameters: dict[str, Tensor] = {}
    next_moments: dict[str, tuple[Tensor, Tensor]] = {}
    with torch.no_grad():
        for name, gradient in zip(B2_PARAMETER_ORDER, clipped_gradients):
            previous_m, previous_v = moments.get(
                name,
                (torch.zeros_like(parameters[name]), torch.zeros_like(parameters[name])),
            )
            exp_avg = previous_m.detach().clone()
            exp_avg.lerp_(gradient, 1.0 - beta1)
            exp_avg_sq = previous_v.detach().clone()
            exp_avg_sq.mul_(beta2).addcmul_(gradient, gradient, value=1.0 - beta2)
            denominator = exp_avg_sq.sqrt() / bias_correction2_sqrt + 1e-8
            updated = parameters[name].detach().clone()
            updated.addcdiv_(
                exp_avg, denominator, value=-(0.003 / bias_correction1)
            )
            next_parameters[name] = updated.detach().clone()
            next_moments[name] = (exp_avg.detach().clone(), exp_avg_sq.detach().clone())
    summary = {
        "parameters_before": before_parameters,
        "parameters_after": digest(_pure_model_payload(next_parameters)),
        "optimizer_before": before_optimizer,
        "optimizer_after": digest(_pure_optimizer_payload(next_moments, step=next_step)),
        "loss": float(loss.detach()),
        "actor_loss": route["actor_loss"],
        "critic_loss": route["critic_loss"],
        "actor_route": route["actor_route"],
        "critic_route": route["critic_route"],
        "label_target_count": len(route["label_targets"]),  # type: ignore[arg-type]
        "gradient_norm_before_clip": float(total_norm),
        "clip_threshold": 1.0,
        "clipped": float(total_norm) > 1.0,
    }
    return next_parameters, next_moments, summary


def _new_learners(unit_id: str, root: int) -> tuple[
    dict[str, b1.GRUActorCritic], dict[str, torch.optim.Optimizer]
]:
    base = b1.GRUActorCritic(
        init_seed=b2_seed(unit_id, root, "parameter_initialization")
    )
    base_optimizer = torch.optim.Adam(base.parameters(), lr=0.003)
    base_optimizer_state = deepcopy(base_optimizer.state_dict())
    models = {arm: deepcopy(base) for arm in B2_ARMS}
    optimizers: dict[str, torch.optim.Optimizer] = {}
    for arm in B2_ARMS:
        optimizer = torch.optim.Adam(models[arm].parameters(), lr=0.003)
        optimizer.load_state_dict(deepcopy(base_optimizer_state))
        optimizers[arm] = optimizer
    return models, optimizers


def _forward(
    model: b1.GRUActorCritic, observations: Sequence[Mapping[str, object]]
) -> tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
    hidden = torch.zeros(b1.B1_HIDDEN_SIZE, dtype=torch.float64)
    hidden = model.gru(b1.observation_vector(observations[0]), hidden)
    hidden = model.gru(b1.observation_vector(observations[1]), hidden)
    logits = model.actor(hidden)
    raw_softmax = torch.softmax(logits, dim=0)
    behavior_probabilities = 0.8 * raw_softmax + 0.1
    entropy = -(behavior_probabilities * torch.log(behavior_probabilities)).sum()
    baseline = model.critic(hidden).squeeze(0)
    return logits, raw_softmax, behavior_probabilities, baseline, entropy


def _observation_firewall(observations: Sequence[Mapping[str, object]]) -> bool:
    if len(observations) != 2:
        return False
    expected = set(b1.B1_OBSERVATION_FIELDS)
    for observation in observations:
        if set(observation) != expected:
            return False
        if set(observation) & set(b1.B1_FORBIDDEN_OBSERVATION_FIELDS):
            return False
    cue, decide = observations
    return (
        cue["cue_mask"] == 1
        and cue["cue_value"] in (0, 1)
        and decide["cue_mask"] == 0
        and decide["cue_value"] == 0
    )


def _schedule_with_receipt(
    unit_id: str, root: int
) -> tuple[list[dict[str, object]], str]:
    cue_rng = random.Random(b2_seed(unit_id, root, "train_owner_cue_clone"))
    rows: list[dict[str, object]] = []
    for update_index in range(B2_UPDATES_PER_UNIT):
        cues = [0] * 4 + [1] * 4
        cue_rng.shuffle(cues)
        for within_update, cue in enumerate(cues):
            episode_index = update_index * B2_BATCH_SIZE + within_update
            rows.append(
                {
                    "unit_id": unit_id,
                    "decimal_root": root,
                    "update_index": update_index,
                    "within_update": within_update,
                    "episode_index": episode_index,
                    "owner_epoch": f"{unit_id}-TR-{episode_index:04d}",
                    "true_cue": cue,
                    "clone_id": f"{unit_id}/TRAIN/{episode_index:04d}",
                }
            )
    return rows, rng_digest(cue_rng)


def _schedule(unit_id: str, root: int) -> list[dict[str, object]]:
    return _schedule_with_receipt(unit_id, root)[0]


def _schedule_contract(rows: Sequence[Mapping[str, object]]) -> bool:
    if len(rows) != B2_TRAIN_EPISODES_PER_UNIT:
        return False
    total = Counter(int(row["true_cue"]) for row in rows)
    if total != Counter({0: 512, 1: 512}):
        return False
    for start in range(0, len(rows), B2_BATCH_SIZE):
        batch = rows[start : start + B2_BATCH_SIZE]
        if Counter(int(row["true_cue"]) for row in batch) != Counter({0: 4, 1: 4}):
            return False
    return True


def _synthetic_history(cue: int, *, owner_epoch: str) -> list[dict[str, object]]:
    common = dict(
        committed_phase="ACTIVE",
        prior_acknowledgements=("CLAIM_ACCEPTED",),
        physical_clock=0,
        primitive_clock=0,
        own_boundary_clock=0,
        owner_epoch_token=(b1.B1_OWNER_ID, owner_epoch, b1.B1_BEHAVIOR_VERSION),
        visible_roster=b1.B1_VISIBLE_ROSTER,
        primitive_policy=b1.B1_PRIMITIVE,
        partner_policy=b1.B1_PARTNER_POLICY,
    )
    cue_observation = b1.PolicyObservation(**common, cue_mask=1, cue_value=cue)
    decide = b1.PolicyObservation(**common, cue_mask=0, cue_value=0)
    # Pure tensor-fixture construction: no host/reset/step, root, episode,
    # optimizer update, checkpoint, or stochastic draw is created.
    return [asdict(cue_observation), asdict(decide)]


def _loss_terms(
    arm: str,
    model: b1.GRUActorCritic,
    batch: Sequence[Mapping[str, object]],
) -> tuple[Tensor, dict[str, object]]:
    actor_terms: list[Tensor] = []
    critic_terms: list[Tensor] = []
    label_targets: list[int] = []
    for row in batch:
        observations = row["O"]
        assert isinstance(observations, Sequence)
        logits, _, probabilities, baseline, entropy = _forward(model, observations)
        expected_probabilities = row.get("behavior_probabilities")
        if arm == "RL_ORIGINAL" and expected_probabilities is not None:
            if any(
                not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=1e-12)
                for actual, expected in zip(probabilities.detach(), expected_probabilities)
            ):
                raise RuntimeError("RL behavior probabilities changed before its paired update")
        physical_return = torch.tensor(float(row["G"]), dtype=torch.float64)
        critic_terms.append(0.5 * (physical_return - baseline) ** 2)
        if arm == "RL_ORIGINAL":
            action_index = b1.Action(str(row["A_behavior"])).index
            advantage = (physical_return - baseline).detach()
            actor_terms.append(
                -advantage * torch.log(probabilities[action_index]) - 0.01 * entropy
            )
        else:
            cue = int(row["metadata"]["true_cue"])  # type: ignore[index]
            target = cue if arm == "SUP_TRUE" else 1 - cue
            # Action.RELEASE has index zero, so X_b=1 maps to RELEASE.
            target_index = 0 if target == 1 else 1
            label_targets.append(target_index)
            actor_terms.append(
                torch.nn.functional.cross_entropy(
                    logits.unsqueeze(0), torch.tensor([target_index], dtype=torch.long)
                )
            )
    actor_loss = torch.stack(actor_terms).mean()
    critic_loss = torch.stack(critic_terms).mean()
    return actor_loss + critic_loss, {
        "actor_loss": float(actor_loss.detach()),
        "critic_loss": float(critic_loss.detach()),
        "label_targets": label_targets,
        "actor_route": (
            "-stop_gradient(G-b)*log(mu(A_behavior|history))-0.01*entropy"
            if arm == "RL_ORIGINAL"
            else "mean_cross_entropy(actor_logits[M_lifecycle],Y_true)"
            if arm == "SUP_TRUE"
            else "mean_cross_entropy(actor_logits[M_lifecycle],Y_flip)"
        ),
        "critic_route": "mean(0.5*(G-b)^2)",
    }


def _proof_batch() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, cue in enumerate((0, 1, 0, 1, 0, 1, 0, 1)):
        observations = _synthetic_history(cue, owner_epoch=f"B2-PROOF-{index:02d}")
        rows.append(
            {
                "O": observations,
                "H0": [0.0] * b1.B1_HIDDEN_SIZE,
                "M_reset": [1, 0],
                "M_active": [1, 1],
                "M_valid": [0, 1],
                "M_lifecycle": [0, 1],
                "A_behavior": b1.Action.RELEASE.value if index % 2 else b1.Action.HOLD.value,
                "R": [0.0],
                "Done": [True],
                "G": 1.0 if index % 2 else 0.5,
                "behavior_probabilities": [0.5, 0.5],
                "metadata": {"true_cue": cue, "clone_id": f"P3/{index}"},
            }
        )
    return rows


def _gradient_route_proof(
    models: Mapping[str, b1.GRUActorCritic],
    optimizers: Mapping[str, torch.optim.Optimizer],
) -> dict[str, object]:
    batch = _proof_batch()
    observation = batch[0]["O"]
    assert isinstance(observation, Sequence)

    _, _, probabilities, baseline, entropy = _forward(models["RL_ORIGINAL"], observation)
    physical_return = torch.tensor(float(batch[0]["G"]), dtype=torch.float64)
    rl_actor = (
        -(physical_return - baseline.detach())
        * torch.log(probabilities[b1.Action.HOLD.index])
        - 0.01 * entropy
    )
    rl_actor_to_critic = torch.autograd.grad(
        rl_actor,
        tuple(models["RL_ORIGINAL"].critic.parameters()),
        allow_unused=True,
        retain_graph=False,
    )

    logits, _, _, _, _ = _forward(models["SUP_TRUE"], observation)
    supervised_actor = torch.nn.functional.cross_entropy(
        logits.unsqueeze(0), torch.tensor([1], dtype=torch.long)
    )
    supervised_actor_to_critic = torch.autograd.grad(
        supervised_actor,
        tuple(models["SUP_TRUE"].critic.parameters()),
        allow_unused=True,
        retain_graph=False,
    )

    before = {
        "rl_parameters": digest(model_payload(models["RL_ORIGINAL"])),
        "rl_optimizer": digest(optimizer_payload(optimizers["RL_ORIGINAL"])),
        "rl_rng": digest("P3_NO_RL_RNG_CONSUMPTION"),
        "rl_successor_state": digest("P3_NO_SUCCESSOR_MUTATION"),
        "immutable_batch": digest(batch),
    }
    for arm in ("SUP_TRUE", "SUP_FLIP"):
        loss, _ = _loss_terms(arm, models[arm], batch)
        torch.autograd.grad(loss, tuple(models[arm].parameters()), allow_unused=True)
    after = {
        "rl_parameters": digest(model_payload(models["RL_ORIGINAL"])),
        "rl_optimizer": digest(optimizer_payload(optimizers["RL_ORIGINAL"])),
        "rl_rng": digest("P3_NO_RL_RNG_CONSUMPTION"),
        "rl_successor_state": digest("P3_NO_SUCCESSOR_MUTATION"),
        "immutable_batch": digest(batch),
    }
    return {
        "activity": {
            "roots": 0,
            "arms": 0,
            "host_resets": 0,
            "episodes": 0,
            "environment_transitions": 0,
            "optimizer_updates": 0,
            "checkpoints": 0,
            "rng_draws": 0,
        },
        "before": before,
        "after": after,
        "hash_identity": before == after,
        "batch_read_only": before["immutable_batch"] == after["immutable_batch"],
        "rl_actor_advantage_detached_from_critic_head": all(
            gradient is None for gradient in rl_actor_to_critic
        ),
        "supervised_actor_has_no_critic_head_route": all(
            gradient is None for gradient in supervised_actor_to_critic
        ),
        "rl_label_argument_surface": [],
        "supervised_original_actor_term_count": 0,
        "critic_route": "mean(0.5*(G-b)^2)",
    }


def _mixture_metrics_from_raw_q(*, q0: float, q1: float) -> dict[str, float]:
    p0, p1 = 0.1 + 0.8 * q0, 0.1 + 0.8 * q1
    return {
        "p_0": p0,
        "p_1": p1,
        "kappa": p1 - p0,
        "j_eval": 0.5 + p1 - 0.5 * p0,
    }


def _evaluator_sentinels() -> dict[str, object]:
    def values(q0: float, q1: float) -> tuple[float, float]:
        metrics = _mixture_metrics_from_raw_q(q0=q0, q1=q1)
        return metrics["j_eval"], metrics["kappa"]

    correct_j, correct_kappa = values(0.0, 1.0)
    inverse_j, inverse_kappa = values(1.0, 0.0)
    finite_low_j, finite_low_kappa = values(0.9, 0.1)
    finite_high_j, finite_high_kappa = values(0.1, 0.9)
    return {
        "correct": {"j_eval": correct_j, "kappa": correct_kappa},
        "inverse": {"j_eval": inverse_j, "kappa": inverse_kappa},
        "finite_neural_extrema": {
            "lower_j": finite_low_j,
            "lower_kappa": finite_low_kappa,
            "upper_j": finite_high_j,
            "upper_kappa": finite_high_kappa,
        },
        "valid": (
            math.isclose(correct_j, 1.35, rel_tol=0.0, abs_tol=1e-12)
            and math.isclose(correct_kappa, 0.8, rel_tol=0.0, abs_tol=1e-12)
            and math.isclose(inverse_j, 0.15, rel_tol=0.0, abs_tol=1e-12)
            and math.isclose(inverse_kappa, -0.8, rel_tol=0.0, abs_tol=1e-12)
            and finite_low_j > 0.15
            and finite_high_j < 1.35
            and -0.8 < finite_low_kappa < 0.8
            and -0.8 < finite_high_kappa < 0.8
        ),
    }


def build_manifest(
    *, source_revision: str, run_id: str, technical_only: bool
) -> dict[str, object]:
    return {
        "schema_version": B2_SCHEMA_VERSION,
        "artifact_kind": "vsp02_b2_manifest",
        "assignment_id": B2_ASSIGNMENT_ID,
        "candidate": B2_CANDIDATE,
        "host_id": B2_HOST_ID,
        "resource_class": B2_RESOURCE_CLASS,
        "pool_units": B2_POOL_UNITS,
        "source_revision": source_revision,
        "run_id": run_id,
        "technical_only": technical_only,
        "accepted_precursor_source": B2_ACCEPTED_PRECURSOR_SOURCE,
        "accepted_precursor_publication": B2_ACCEPTED_PRECURSOR_PUBLICATION,
        "freshness": {
            "physical_tape_prefix": B2_PHYSICAL_TAPE_PREFIX,
            "b1v2_artifact_checkpoint_batch_tape_reuse": False,
            "parameter_state_derived_once_then_cloned": True,
            "optimizer_state_derived_once_then_cloned": True,
        },
        "arms": list(B2_ARMS),
        "units": [
            {"unit_id": unit_id, "decimal_root": root} for unit_id, root in B2_UNITS
        ],
        "rng_streams": list(B2_STREAMS),
        "training": {
            "updates_per_unit": B2_UPDATES_PER_UNIT,
            "episodes_per_update": B2_BATCH_SIZE,
            "episodes_per_unit": B2_TRAIN_EPISODES_PER_UNIT,
            "cue_count_per_update": {"0": 4, "1": 4},
            "sole_generator": "RL_ORIGINAL",
        },
        "evaluation": {
            "episodes_per_unit_arm": B2_EVAL_EPISODES_PER_UNIT_ARM,
            "cue_counts": {"0": 64, "1": 64},
            "checkpoints": 1,
            "stochastic_action_draws": 0,
        },
        "optimizer": {
            "name": "Adam",
            "learning_rate": 0.003,
            "betas": [0.9, 0.999],
            "epsilon": 1e-8,
            "weight_decay": 0.0,
            "amsgrad": False,
            "gradient_norm_clip": 1.0,
        },
        "loss_contract": {
            "rl_actor": "-stop_gradient(G-b)*log(mu(A_behavior|history))-0.01*entropy",
            "supervised_true": "mean_cross_entropy(actor_logits[M_lifecycle],Y_true)",
            "supervised_flip": "mean_cross_entropy(actor_logits[M_lifecycle],Y_flip)",
            "critic": "mean(0.5*(G-b)^2)",
            "supervised_original_lifecycle_actor_terms": 0,
            "label_access_by_rl": False,
        },
        "caps": dict(B2_CAPS),
        "result_bearing_runs": 0 if technical_only else 1,
        "retry_rescue_sweep": 0,
    }


def manifest_identity(manifest: Mapping[str, object]) -> str:
    return digest(manifest)


def _manifest_literal_issues(manifest: Mapping[str, object]) -> dict[str, list[str]]:
    issues = {f"P{index}": [] for index in range(9)}
    expected = build_manifest(
        source_revision=str(manifest.get("source_revision", "")),
        run_id=str(manifest.get("run_id", "")),
        technical_only=bool(manifest.get("technical_only")),
    )
    p0_fields = (
        "schema_version",
        "artifact_kind",
        "assignment_id",
        "candidate",
        "host_id",
        "resource_class",
        "pool_units",
        "accepted_precursor_source",
        "accepted_precursor_publication",
        "technical_only",
        "result_bearing_runs",
        "retry_rescue_sweep",
        "freshness",
    )
    for field in p0_fields:
        if manifest.get(field) != expected[field]:
            issues["P0"].append(f"manifest {field} mismatch")
    if not manifest.get("source_revision") or not manifest.get("run_id"):
        issues["P0"].append("source_revision and run_id must be nonempty")
    if manifest.get("units") != expected["units"]:
        issues["P1"].append("fresh unit/root identity mismatch")
    if manifest.get("arms") != expected["arms"]:
        issues["P2"].append("arm identity mismatch")
    if manifest.get("optimizer") != expected["optimizer"]:
        issues["P2"].append("optimizer contract mismatch")
    if manifest.get("loss_contract") != expected["loss_contract"]:
        issues["P4"].append("loss/autograd contract mismatch")
    if manifest.get("training") != expected["training"]:
        issues["P6"].append("128x8 training schedule contract mismatch")
    if manifest.get("evaluation") != expected["evaluation"]:
        issues["P7"].append("evaluation contract mismatch")
    if manifest.get("rng_streams") != expected["rng_streams"]:
        issues["P8"].append("exhaustive RNG stream allow-list mismatch")
    if manifest.get("caps") != expected["caps"]:
        issues["P6"].append("activity cap mismatch")
    return issues


def _git_binding(repo_root: Path, source_revision: str) -> list[str]:
    issues: list[str] = []

    def git(*arguments: str) -> str:
        return subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    try:
        actual = git("rev-parse", "HEAD")
        if actual != source_revision:
            issues.append(f"source revision {source_revision} != checkout HEAD {actual}")
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", B2_ACCEPTED_PRECURSOR_SOURCE, actual],
            cwd=repo_root,
            check=False,
        ).returncode
        if ancestor != 0:
            issues.append("accepted B1V2 source is not an ancestor")
        if actual == B2_ACCEPTED_PRECURSOR_SOURCE:
            issues.append("B2 source revision is not fresh")
        tracked = set(git("ls-files", "--", *B2_CLAIM_PATHS).splitlines())
        if tracked != set(B2_CLAIM_PATHS):
            issues.append("B2 claim path set is not fully tracked")
        dirty = git("status", "--porcelain=v1", "--untracked-files=all", "--", *B2_CLAIM_PATHS)
        if dirty:
            issues.append("B2 claim paths differ from HEAD")
        for path in B2_PRECURSOR_PATHS:
            precursor_blob = git("rev-parse", f"{B2_ACCEPTED_PRECURSOR_SOURCE}:{path}")
            current_blob = git("rev-parse", f"{actual}:{path}")
            if precursor_blob != current_blob:
                issues.append(f"accepted precursor path changed: {path}")
    except (OSError, subprocess.CalledProcessError) as error:
        issues.append(f"Git source binding failed: {error}")
    return issues


def preflight_report(
    manifest: Mapping[str, object], *, repo_root: Path | None = None
) -> dict[str, object]:
    issues = _manifest_literal_issues(manifest)
    if manifest.get("technical_only") is False:
        if repo_root is None:
            issues["P0"].append("result-bearing preflight requires repo_root")
        else:
            issues["P0"].extend(_git_binding(repo_root, str(manifest["source_revision"])))

    seeds = seed_report()
    if (
        not seeds["all_b2_seeds_unique"]
        or seeds["collision_with_b1v2_seed_values"]
        or seeds["identity_collision_with_b1v2"]
    ):
        issues["P1"].append("B2 RNG seeds are not fresh and collision-free")

    unit_id, root = B2_UNITS[0]
    models, optimizers = _new_learners(unit_id, root)
    model_hashes = {arm: digest(model_payload(model)) for arm, model in models.items()}
    optimizer_hashes = {
        arm: digest(optimizer_payload(optimizer)) for arm, optimizer in optimizers.items()
    }
    architecture = {arm: _architecture_payload(model) for arm, model in models.items()}
    optimizer_contracts = {
        arm: _optimizer_contract(optimizer) for arm, optimizer in optimizers.items()
    }
    if len(set(model_hashes.values())) != 1 or len(set(optimizer_hashes.values())) != 1:
        issues["P2"].append("initial parameter or optimizer states are not byte-identical")
    if len({digest(value) for value in architecture.values()}) != 1:
        issues["P2"].append("arm architectures differ")
    if len({digest(value) for value in optimizer_contracts.values()}) != 1:
        issues["P2"].append("arm optimizer contracts differ")

    p3 = _gradient_route_proof(models, optimizers)
    if not p3["hash_identity"] or not p3["batch_read_only"]:
        issues["P3"].append("shadow computation mutated RL or immutable batch state")
    if not p3["rl_actor_advantage_detached_from_critic_head"]:
        issues["P4"].append("RL actor advantage is not stop-gradient detached")
    if not p3["supervised_actor_has_no_critic_head_route"]:
        issues["P4"].append("supervised actor reaches the critic head")
    if p3["rl_label_argument_surface"] or p3["supervised_original_actor_term_count"] != 0:
        issues["P4"].append("loss-route separation failed")

    histories = [_synthetic_history(cue, owner_epoch=f"P5-{cue}") for cue in (0, 1)]
    firewall = all(_observation_firewall(history) for history in histories)
    if not firewall:
        issues["P5"].append("observation/label firewall failed")

    schedules = {
        unit: _schedule_contract(_schedule(unit, decimal_root))
        for unit, decimal_root in B2_UNITS
    }
    if not all(schedules.values()):
        issues["P6"].append("balanced 128x8 schedule failed")

    evaluator = _evaluator_sentinels()
    if not evaluator["valid"]:
        issues["P7"].append("finite-logit evaluator sentinel failed")
    if tuple(manifest.get("rng_streams", ())) != B2_STREAMS:
        issues["P8"].append("RNG allow-list is incomplete or reordered")

    return {
        "artifact_kind": "vsp02_b2_preflight",
        "assignment_id": B2_ASSIGNMENT_ID,
        "manifest_identity": manifest_identity(manifest),
        "gates": {
            gate: {"passed": not gate_issues, "issues": gate_issues}
            for gate, gate_issues in issues.items()
        },
        "all_passed": not any(issues.values()),
        "architecture": architecture,
        "initial_parameter_hashes": model_hashes,
        "initial_optimizer_hashes": optimizer_hashes,
        "optimizer_contracts": optimizer_contracts,
        "p3_noninterference": p3,
        "label_firewall": firewall,
        "balanced_schedules": schedules,
        "evaluator_sentinels": evaluator,
        "rng": seeds,
        "activity": {
            "result_bearing_runs": 0,
            "host_resets": 0,
            "episodes": 0,
            "environment_transitions": 0,
            "optimizer_updates": 0,
            "checkpoints": 0,
        },
    }


def validate_manifest(manifest: object) -> tuple[str, ...]:
    if not isinstance(manifest, Mapping):
        return ("manifest is not an object",)
    issues = _manifest_literal_issues(manifest)
    return tuple(issue for gate in sorted(issues) for issue in issues[gate])


def _collect_batch(
    *,
    unit_id: str,
    update_index: int,
    rows: Sequence[Mapping[str, object]],
    rl_model: b1.GRUActorCritic,
    event_rng: random.Random,
    action_rng: random.Random,
) -> tuple[list[dict[str, object]], int]:
    batch: list[dict[str, object]] = []
    transitions = 0
    for row in rows:
        event_token = event_rng.getrandbits(64)
        host = B2LifecycleHost()
        cue_observation = host.reset(
            lifecycle_id=(
                f"{B2_ASSIGNMENT_ID}/{unit_id}/TRAIN/"
                f"{int(row['episode_index']):04d}/{event_token:016x}"
            ),
            owner_epoch=str(row["owner_epoch"]),
            true_cue=int(row["true_cue"]),
            presented_cue=int(row["true_cue"]),
        )
        decide = host.decision_observation()
        observations = [asdict(cue_observation), asdict(decide)]
        if not _observation_firewall(observations):
            raise RuntimeError("training observation firewall mismatch")
        with torch.no_grad():
            _, _, probabilities_tensor, _, _ = _forward(rl_model, observations)
        probabilities = [float(value) for value in probabilities_tensor]
        action = (
            b1.Action.RELEASE
            if action_rng.random() < probabilities[b1.Action.RELEASE.index]
            else b1.Action.HOLD
        )
        episode = host.step(action, action_probabilities=probabilities)
        transitions += int(episode["environment_transitions"])
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
            "behavior_probabilities": probabilities,
            "environment_transitions": int(episode["environment_transitions"]),
            "metadata": {
                "unit_id": unit_id,
                "update_index": update_index,
                "episode_index": int(row["episode_index"]),
                "owner_epoch": str(row["owner_epoch"]),
                "true_cue": int(row["true_cue"]),
                "clone_id": str(row["clone_id"]),
                "event_tape_token": f"{event_token:016x}",
                "physical_tape_ids": list(episode["physical_tape_ids"]),
            },
        }
        # Round-trip through canonical JSON to sever all host-owned references.
        frozen = json.loads(canonical_bytes(immutable))
        if digest(frozen) != digest(immutable):
            raise RuntimeError("immutable batch canonicalization mismatch")
        batch.append(frozen)
    return batch, transitions


def _immutable_row_contract(row: Mapping[str, object]) -> bool:
    if set(row) != {
        "O",
        "H0",
        "M_reset",
        "M_active",
        "M_valid",
        "M_lifecycle",
        "A_behavior",
        "R",
        "Done",
        "G",
        "behavior_probabilities",
        "environment_transitions",
        "metadata",
    }:
        return False
    observations = row.get("O")
    if not isinstance(observations, Sequence) or not _observation_firewall(observations):
        return False
    if row.get("H0") != [0.0] * b1.B1_HIDDEN_SIZE:
        return False
    if row.get("M_reset") != [1, 0] or row.get("M_active") != [1, 1]:
        return False
    if row.get("M_valid") != [0, 1] or row.get("M_lifecycle") != [0, 1]:
        return False
    if row.get("A_behavior") not in {action.value for action in b1.Action}:
        return False
    rewards, done = row.get("R"), row.get("Done")
    if not isinstance(rewards, list) or not isinstance(done, list) or len(rewards) != len(done):
        return False
    if not done or done[-1] is not True or any(done[:-1]):
        return False
    expected_return = sum(float(value) * b1.B1_GAMMA**index for index, value in enumerate(rewards))
    if not math.isclose(float(row.get("G", math.nan)), expected_return, rel_tol=0.0, abs_tol=1e-12):
        return False
    probabilities = row.get("behavior_probabilities")
    if not isinstance(probabilities, list) or len(probabilities) != 2:
        return False
    if any(not math.isfinite(float(value)) for value in probabilities):
        return False
    if not math.isclose(sum(float(value) for value in probabilities), 1.0, rel_tol=0.0, abs_tol=1e-12):
        return False
    if row.get("environment_transitions") not in (4, 5):
        return False
    metadata = row.get("metadata")
    if not isinstance(metadata, Mapping) or set(metadata) != {
        "unit_id",
        "update_index",
        "episode_index",
        "owner_epoch",
        "true_cue",
        "clone_id",
        "event_tape_token",
        "physical_tape_ids",
    }:
        return False
    if metadata.get("true_cue") not in (0, 1):
        return False
    tapes = metadata.get("physical_tape_ids")
    return (
        isinstance(tapes, list)
        and len(tapes) == 1
        and str(tapes[0]).startswith(f"{B2_PHYSICAL_TAPE_PREFIX}/")
        and not str(tapes[0]).startswith(f"{b1.B1_ASSIGNMENT_ID}/")
    )


def _optimizer_step(
    arm: str,
    model: b1.GRUActorCritic,
    optimizer: torch.optim.Optimizer,
    batch: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    before = digest(model_payload(model))
    optimizer_before = digest(optimizer_payload(optimizer))
    optimizer.zero_grad(set_to_none=True)
    loss, route = _loss_terms(arm, model, batch)
    loss.backward()
    gradient_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
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
        "label_target_count": len(route["label_targets"]),  # type: ignore[arg-type]
        "gradient_norm_before_clip": gradient_norm,
        "clip_threshold": 1.0,
        "clipped": gradient_norm > 1.0,
    }


def _rl_state_hashes(
    model: b1.GRUActorCritic,
    optimizer: torch.optim.Optimizer,
    action_rng: random.Random,
    successor_state: Mapping[str, object],
    batch: Sequence[Mapping[str, object]],
) -> dict[str, str]:
    return {
        "rl_parameters": digest(model_payload(model)),
        "rl_optimizer": digest(optimizer_payload(optimizer)),
        "rl_rng": rng_digest(action_rng),
        "rl_successor_state": digest(successor_state),
        "immutable_batch": digest(batch),
    }


def _train_unit(
    unit_id: str, root: int, *, capture_noninterference_receipt: bool
) -> dict[str, object]:
    schedules, schedule_rng_terminal = _schedule_with_receipt(unit_id, root)
    if not _schedule_contract(schedules):
        raise RuntimeError("unit schedule is not exact 128x8 balanced support")
    models, optimizers = _new_learners(unit_id, root)
    event_rng = random.Random(b2_seed(unit_id, root, "train_environment_event"))
    action_rng = random.Random(b2_seed(unit_id, root, "train_action_uniform"))
    minibatch_rngs = {
        arm: random.Random(b2_seed(unit_id, root, "train_minibatch_order"))
        for arm in B2_ARMS
    }
    stochastic_rngs = {
        arm: random.Random(b2_seed(unit_id, root, "train_stochastic_layer"))
        for arm in B2_ARMS
    }
    initial_models = {arm: digest(model_payload(model)) for arm, model in models.items()}
    initial_optimizers = {
        arm: digest(optimizer_payload(optimizer)) for arm, optimizer in optimizers.items()
    }
    batch_digests: list[str] = []
    batch_records: list[dict[str, object]] = []
    shadow_noninterference_receipts: list[dict[str, object]] = []
    update_summaries = {arm: [] for arm in B2_ARMS}
    environment_transitions = 0
    cue_counts: Counter[int] = Counter()
    all_batch_identity = True
    all_batch_contracts = True
    all_shadow_noninterference = True
    p3_runtime: dict[str, object] | None = None

    for update_index in range(B2_UPDATES_PER_UNIT):
        rows = schedules[
            update_index * B2_BATCH_SIZE : (update_index + 1) * B2_BATCH_SIZE
        ]
        batch, transitions = _collect_batch(
            unit_id=unit_id,
            update_index=update_index,
            rows=rows,
            rl_model=models["RL_ORIGINAL"],
            event_rng=event_rng,
            action_rng=action_rng,
        )
        environment_transitions += transitions
        cue_counts.update(int(row["metadata"]["true_cue"]) for row in batch)  # type: ignore[index]
        frozen_digest = digest(batch)
        batch_digests.append(frozen_digest)
        batch_records.append(
            {
                "update_index": update_index,
                "batch_digest": frozen_digest,
                "rows": batch,
                "environment_transitions": transitions,
            }
        )
        all_batch_contracts = all_batch_contracts and all(
            _immutable_row_contract(row) for row in batch
        )

        orders: dict[str, list[int]] = {}
        for arm in B2_ARMS:
            order = list(range(B2_BATCH_SIZE))
            minibatch_rngs[arm].shuffle(order)
            orders[arm] = order
        if len({tuple(order) for order in orders.values()}) != 1:
            raise RuntimeError("paired arm minibatch orders diverged")
        ordered_batches = {
            arm: [batch[index] for index in orders[arm]] for arm in B2_ARMS
        }
        if len({digest(value) for value in ordered_batches.values()}) != 1:
            all_batch_identity = False

        rl_update = _optimizer_step(
            "RL_ORIGINAL",
            models["RL_ORIGINAL"],
            optimizers["RL_ORIGINAL"],
            ordered_batches["RL_ORIGINAL"],
        )
        rl_update.update(
            {
                "update_index": update_index,
                "batch_digest": frozen_digest,
                "batch_order": orders["RL_ORIGINAL"],
            }
        )
        update_summaries["RL_ORIGINAL"].append(rl_update)
        successor_state = {
            "unit_id": unit_id,
            "next_update": update_index + 1,
            "event_rng": rng_digest(event_rng),
            "action_rng": rng_digest(action_rng),
        }
        before_shadows = _rl_state_hashes(
            models["RL_ORIGINAL"],
            optimizers["RL_ORIGINAL"],
            action_rng,
            successor_state,
            batch,
        )
        for arm in ("SUP_TRUE", "SUP_FLIP"):
            update = _optimizer_step(
                arm, models[arm], optimizers[arm], ordered_batches[arm]
            )
            update.update(
                {
                    "update_index": update_index,
                    "batch_digest": frozen_digest,
                    "batch_order": orders[arm],
                }
            )
            update_summaries[arm].append(update)
        after_shadows = _rl_state_hashes(
            models["RL_ORIGINAL"],
            optimizers["RL_ORIGINAL"],
            action_rng,
            successor_state,
            batch,
        )
        identity = before_shadows == after_shadows
        shadow_noninterference_receipts.append(
            {
                "update_index": update_index,
                "batch_digest": frozen_digest,
                "before": before_shadows,
                "after": after_shadows,
                "hash_identity": identity,
            }
        )
        all_shadow_noninterference = all_shadow_noninterference and identity
        if capture_noninterference_receipt and update_index == 0:
            p3_runtime = {
                "fixture": f"{unit_id}/UPDATE/000",
                "before": before_shadows,
                "after": after_shadows,
                "hash_identity": identity,
                "batch_read_only": (
                    before_shadows["immutable_batch"] == after_shadows["immutable_batch"]
                ),
                "extra_roots": 0,
                "extra_arms": 0,
                "extra_episodes": 0,
                "extra_updates": 0,
                "extra_checkpoints": 0,
            }

    stochastic_draw_counts = {arm: 0 for arm in B2_ARMS}
    stochastic_rng_hashes = {arm: rng_digest(rng) for arm, rng in stochastic_rngs.items()}
    return {
        "unit_id": unit_id,
        "decimal_root": root,
        "models": models,
        "training": {
            "real_rl_generated_episodes": len(schedules),
            "cue_counts": {str(cue): cue_counts[cue] for cue in (0, 1)},
            "environment_transitions": environment_transitions,
            "shadow_environment_episodes": 0,
            "updates_per_arm": {
                arm: len(update_summaries[arm]) for arm in B2_ARMS
            },
            "initial_parameter_hashes": initial_models,
            "initial_optimizer_hashes": initial_optimizers,
            "final_parameter_hashes": {
                arm: digest(model_payload(model)) for arm, model in models.items()
            },
            "final_model_states": {
                arm: model_payload(model) for arm, model in models.items()
            },
            "final_optimizer_states": {
                arm: optimizer_payload(optimizers[arm]) for arm in B2_ARMS
            },
            "batch_digests": batch_digests,
            "batch_records": batch_records,
            "train_clone_ids": [str(row["clone_id"]) for row in schedules],
            "immutable_batch_identity_all_arms": all_batch_identity,
            "immutable_batch_contract_all_rows": all_batch_contracts,
            "shadow_noninterference_all_updates": all_shadow_noninterference,
            "shadow_noninterference_receipts": shadow_noninterference_receipts,
            "p3_runtime": p3_runtime,
            "minibatch_rng_draw_counts_equal": len(
                {rng_digest(rng) for rng in minibatch_rngs.values()}
            ) == 1,
            "minibatch_rng_hashes": {
                arm: rng_digest(rng) for arm, rng in minibatch_rngs.items()
            },
            "stochastic_rng_draw_counts": stochastic_draw_counts,
            "stochastic_rng_hashes": stochastic_rng_hashes,
            "stochastic_rng_hashes_equal": len(set(stochastic_rng_hashes.values())) == 1,
            "terminal_rng_hashes": {
                "train_owner_cue_clone": schedule_rng_terminal,
                "train_environment_event": rng_digest(event_rng),
                "train_action_uniform": rng_digest(action_rng),
                "train_minibatch_order_by_arm": {
                    arm: rng_digest(rng) for arm, rng in minibatch_rngs.items()
                },
                "train_stochastic_layer_by_arm": stochastic_rng_hashes,
            },
            "updates": update_summaries,
        },
    }


def _evaluation_panel_with_receipt(
    unit_id: str, root: int
) -> tuple[list[dict[str, object]], dict[str, str]]:
    cue_rng = random.Random(b2_seed(unit_id, root, "evaluation_owner_cue_clone"))
    event_rng = random.Random(b2_seed(unit_id, root, "evaluation_environment_event"))
    cues = [0] * 64 + [1] * 64
    cue_rng.shuffle(cues)
    panel = [
        {
            "clone_id": f"{unit_id}/EVAL/{index:03d}",
            "owner_epoch": f"{unit_id}-EV-{index:03d}",
            "true_cue": cue,
            "event_tape_token": f"{event_rng.getrandbits(64):016x}",
        }
        for index, cue in enumerate(cues)
    ]
    return panel, {
        "evaluation_owner_cue_clone": rng_digest(cue_rng),
        "evaluation_environment_event": rng_digest(event_rng),
    }


def _evaluation_panel(unit_id: str, root: int) -> list[dict[str, object]]:
    return _evaluation_panel_with_receipt(unit_id, root)[0]


def _evaluate_arm_unit(
    *,
    unit_id: str,
    arm: str,
    model: b1.GRUActorCritic,
    panel: Sequence[Mapping[str, object]],
    panel_rng_terminal_hashes: Mapping[str, str] | None = None,
) -> dict[str, object]:
    release_by_cue: dict[int, list[float]] = {0: [], 1: []}
    argmax_by_cue: dict[int, list[str | None]] = {0: [], 1: []}
    transitions = 0
    clone_records: list[dict[str, object]] = []
    for index, row in enumerate(panel):
        cue = int(row["true_cue"])
        host = B2LifecycleHost()
        cue_observation = host.reset(
            lifecycle_id=(
                f"{B2_ASSIGNMENT_ID}/{unit_id}/{arm}/EVAL/{index:03d}/"
                f"{row['event_tape_token']}"
            ),
            owner_epoch=str(row["owner_epoch"]),
            true_cue=cue,
            presented_cue=cue,
        )
        decide = host.decision_observation()
        observations = [asdict(cue_observation), asdict(decide)]
        if not _observation_firewall(observations):
            raise RuntimeError("evaluation observation firewall mismatch")
        with torch.no_grad():
            logits, raw_softmax_tensor, probabilities_tensor, _, _ = _forward(
                model, observations
            )
        if (
            not torch.isfinite(logits).all()
            or not torch.isfinite(raw_softmax_tensor).all()
            or not torch.isfinite(probabilities_tensor).all()
        ):
            raise RuntimeError("non-finite evaluation logit or probability")
        raw_softmax = [float(value) for value in raw_softmax_tensor]
        probabilities = [float(value) for value in probabilities_tensor]
        q_release, q_hold = raw_softmax
        p_release, p_hold = probabilities
        release_by_cue[cue].append(q_release)
        raw_choice = (
            b1.Action.RELEASE.value
            if q_release > q_hold
            else b1.Action.HOLD.value
            if q_hold > q_release
            else None
        )
        choice = (
            b1.Action.RELEASE.value
            if p_release > p_hold
            else b1.Action.HOLD.value
            if p_hold > p_release
            else None
        )
        if raw_choice != choice:
            raise RuntimeError("raw-softmax and mixed-policy argmax diverged")
        argmax_by_cue[cue].append(choice)
        executed = b1.Action(choice) if choice is not None else b1.Action.HOLD
        episode = host.step(executed, action_probabilities=probabilities)
        episode_transitions = int(episode["environment_transitions"])
        transitions += episode_transitions
        clone_records.append(
            {
                "clone_id": str(row["clone_id"]),
                "owner_epoch": str(row["owner_epoch"]),
                "true_cue": cue,
                "event_tape_token": str(row["event_tape_token"]),
                "logits": [float(value) for value in logits],
                "raw_softmax": raw_softmax,
                "behavior_probabilities": probabilities,
                "argmax_action": choice,
                "executed_action": executed.value,
                "environment_transitions": episode_transitions,
            }
        )
    q0 = sum(release_by_cue[0]) / len(release_by_cue[0])
    q1 = sum(release_by_cue[1]) / len(release_by_cue[1])
    metrics = _mixture_metrics_from_raw_q(q0=q0, q1=q1)
    p0, p1 = metrics["p_0"], metrics["p_1"]
    kappa, j_eval = metrics["kappa"], metrics["j_eval"]
    exact_correct = all(value == b1.Action.HOLD.value for value in argmax_by_cue[0]) and all(
        value == b1.Action.RELEASE.value for value in argmax_by_cue[1]
    )
    exact_inverse = all(value == b1.Action.RELEASE.value for value in argmax_by_cue[0]) and all(
        value == b1.Action.HOLD.value for value in argmax_by_cue[1]
    )
    return {
        "unit_id": unit_id,
        "arm": arm,
        "checkpoint_id": f"{unit_id}/{arm}/FINAL/128",
        "final_model_hash": digest(model_payload(model)),
        "panel_digest": digest(panel),
        "panel_rng_terminal_hashes": dict(panel_rng_terminal_hashes or {}),
        "clone_records": clone_records,
        "episodes": len(panel),
        "cue_counts": {
            "0": len(release_by_cue[0]),
            "1": len(release_by_cue[1]),
        },
        "environment_transitions": transitions,
        "q_0": q0,
        "q_1": q1,
        "p_0": p0,
        "p_1": p1,
        "kappa": kappa,
        "j_eval": j_eval,
        "exact_correct_unit": exact_correct,
        "exact_inverse_unit": exact_inverse,
        "argmax_ties": sum(value is None for values in argmax_by_cue.values() for value in values),
        "finite_logits": True,
        "q_is_raw_softmax": True,
        "argmax_mixture_equivalent": True,
        "evaluation_updates": 0,
        "stochastic_action_draws": 0,
    }


def bounded_deterministic_replay_fixture() -> dict[str, object]:
    """One-unit/two-update replay proof; never a registered treatment full."""

    torch.set_num_threads(1)
    unit_id, root = B2_UNITS[0]
    models, optimizers = _new_learners(unit_id, root)
    schedule, schedule_terminal = _schedule_with_receipt(unit_id, root)
    event_rng = random.Random(b2_seed(unit_id, root, "train_environment_event"))
    action_rng = random.Random(b2_seed(unit_id, root, "train_action_uniform"))
    minibatch_rngs = {
        arm: random.Random(b2_seed(unit_id, root, "train_minibatch_order"))
        for arm in B2_ARMS
    }
    batches: list[dict[str, object]] = []
    updates: dict[str, list[dict[str, object]]] = {arm: [] for arm in B2_ARMS}
    for update_index in range(2):
        rows = schedule[update_index * 8 : (update_index + 1) * 8]
        batch, transitions = _collect_batch(
            unit_id=unit_id,
            update_index=update_index,
            rows=rows,
            rl_model=models["RL_ORIGINAL"],
            event_rng=event_rng,
            action_rng=action_rng,
        )
        batch_digest = digest(batch)
        batches.append(
            {
                "update_index": update_index,
                "batch_digest": batch_digest,
                "rows": batch,
                "environment_transitions": transitions,
            }
        )
        orders: dict[str, list[int]] = {}
        for arm in B2_ARMS:
            order = list(range(8))
            minibatch_rngs[arm].shuffle(order)
            orders[arm] = order
        if len({tuple(order) for order in orders.values()}) != 1:
            raise AssertionError("bounded replay arm ordering diverged")
        for arm in B2_ARMS:
            update = _optimizer_step(
                arm,
                models[arm],
                optimizers[arm],
                [batch[index] for index in orders[arm]],
            )
            update.update(
                {
                    "update_index": update_index,
                    "batch_digest": batch_digest,
                    "batch_order": orders[arm],
                }
            )
            updates[arm].append(update)
    panel, panel_rng_receipt = _evaluation_panel_with_receipt(unit_id, root)
    evaluations = {
        arm: _evaluate_arm_unit(
            unit_id=unit_id,
            arm=arm,
            model=models[arm],
            panel=panel,
            panel_rng_terminal_hashes=panel_rng_receipt,
        )
        for arm in B2_ARMS
    }
    return {
        "artifact_kind": "vsp02_b2_bounded_deterministic_replay_fixture",
        "assignment_id": B2_ASSIGNMENT_ID,
        "registered_fulls": 0,
        "result_bearing_runs": 0,
        "unit_id": unit_id,
        "decimal_root": root,
        "training_episodes": 16,
        "optimizer_updates": 6,
        "evaluation_episodes": 384,
        "batches": batches,
        "updates": updates,
        "final_model_states": {
            arm: model_payload(models[arm]) for arm in B2_ARMS
        },
        "final_optimizer_states": {
            arm: optimizer_payload(optimizers[arm]) for arm in B2_ARMS
        },
        "terminal_rng_hashes": {
            "train_owner_cue_clone": schedule_terminal,
            "train_environment_event": rng_digest(event_rng),
            "train_action_uniform": rng_digest(action_rng),
            "train_minibatch_order_by_arm": {
                arm: rng_digest(rng) for arm, rng in minibatch_rngs.items()
            },
            "evaluation": panel_rng_receipt,
        },
        "evaluations": evaluations,
    }


def validate_bounded_deterministic_replay_fixture(
    retained: object,
) -> tuple[str, ...]:
    if not isinstance(retained, Mapping):
        return ("bounded fixture differs from deterministic seed/host/Adam replay",)
    if {
        "artifact_kind": retained.get("artifact_kind"),
        "assignment_id": retained.get("assignment_id"),
        "registered_fulls": retained.get("registered_fulls"),
        "result_bearing_runs": retained.get("result_bearing_runs"),
        "training_episodes": retained.get("training_episodes"),
        "optimizer_updates": retained.get("optimizer_updates"),
        "evaluation_episodes": retained.get("evaluation_episodes"),
    } != {
        "artifact_kind": "vsp02_b2_bounded_deterministic_replay_fixture",
        "assignment_id": B2_ASSIGNMENT_ID,
        "registered_fulls": 0,
        "result_bearing_runs": 0,
        "training_episodes": 16,
        "optimizer_updates": 6,
        "evaluation_episodes": 384,
    }:
        return ("bounded fixture differs from deterministic seed/host/Adam replay",)
    unit_id, root = B2_UNITS[0]
    if retained.get("unit_id") != unit_id or retained.get("decimal_root") != root:
        return ("bounded fixture differs from deterministic seed/host/Adam replay",)
    batches, updates = retained.get("batches"), retained.get("updates")
    if not isinstance(batches, list) or len(batches) != 2:
        return ("bounded fixture differs from deterministic seed/host/Adam replay",)
    if not isinstance(updates, Mapping) or set(updates) != set(B2_ARMS):
        return ("bounded fixture differs from deterministic seed/host/Adam replay",)
    initial = _expected_initial_evidence(unit_id, root)["parameter_payload"]
    assert isinstance(initial, Mapping)
    parameters = {arm: _payload_tensors(initial) for arm in B2_ARMS}
    moments: dict[str, dict[str, tuple[Tensor, Tensor]]] = {arm: {} for arm in B2_ARMS}
    schedule, schedule_terminal = _schedule_with_receipt(unit_id, root)
    event_rng = random.Random(b2_seed(unit_id, root, "train_environment_event"))
    action_rng = random.Random(b2_seed(unit_id, root, "train_action_uniform"))
    minibatch_rngs = {
        arm: random.Random(b2_seed(unit_id, root, "train_minibatch_order"))
        for arm in B2_ARMS
    }
    for update_index, record in enumerate(batches):
        if not isinstance(record, Mapping):
            return ("bounded fixture differs from deterministic seed/host/Adam replay",)
        expected_rows = [
            _pure_expected_training_row(
                unit_id=unit_id,
                update_index=update_index,
                schedule_row=schedule[update_index * B2_BATCH_SIZE + offset],
                rl_parameters=parameters["RL_ORIGINAL"],
                event_rng=event_rng,
                action_rng=action_rng,
            )
            for offset in range(B2_BATCH_SIZE)
        ]
        expected_record = {
            "update_index": update_index,
            "batch_digest": digest(expected_rows),
            "rows": expected_rows,
            "environment_transitions": sum(
                int(row["environment_transitions"]) for row in expected_rows
            ),
        }
        if canonical_bytes(record) != canonical_bytes(expected_record):
            return ("bounded fixture differs from deterministic seed/host/Adam replay",)
        for arm in B2_ARMS:
            order = list(range(B2_BATCH_SIZE))
            minibatch_rngs[arm].shuffle(order)
            parameters[arm], moments[arm], summary = _pure_adam_update(
                arm,
                parameters[arm],
                moments[arm],
                step=update_index,
                batch=[expected_rows[index] for index in order],
            )
            summary.update(
                {
                    "update_index": update_index,
                    "batch_digest": expected_record["batch_digest"],
                    "batch_order": order,
                }
            )
            arm_updates = updates.get(arm)
            if (
                not isinstance(arm_updates, list)
                or len(arm_updates) != 2
                or not _summary_matches(arm_updates[update_index], summary)
            ):
                return ("bounded fixture differs from deterministic seed/host/Adam replay",)
    expected_models = {arm: _pure_model_payload(parameters[arm]) for arm in B2_ARMS}
    expected_optimizers = {
        arm: _pure_optimizer_payload(moments[arm], step=2) for arm in B2_ARMS
    }
    if canonical_bytes(retained.get("final_model_states")) != canonical_bytes(expected_models):
        return ("bounded fixture differs from deterministic seed/host/Adam replay",)
    if canonical_bytes(retained.get("final_optimizer_states")) != canonical_bytes(expected_optimizers):
        return ("bounded fixture differs from deterministic seed/host/Adam replay",)
    _, panel_rng = _evaluation_panel_with_receipt(unit_id, root)
    expected_rng = {
        "train_owner_cue_clone": schedule_terminal,
        "train_environment_event": rng_digest(event_rng),
        "train_action_uniform": rng_digest(action_rng),
        "train_minibatch_order_by_arm": {
            arm: rng_digest(rng) for arm, rng in minibatch_rngs.items()
        },
        "evaluation": panel_rng,
    }
    if retained.get("terminal_rng_hashes") != expected_rng:
        return ("bounded fixture differs from deterministic seed/host/Adam replay",)
    evaluations = retained.get("evaluations")
    if not isinstance(evaluations, Mapping) or set(evaluations) != set(B2_ARMS):
        return ("bounded fixture differs from deterministic seed/host/Adam replay",)
    for arm in B2_ARMS:
        metric = evaluations[arm]
        if not isinstance(metric, Mapping):
            return ("bounded fixture differs from deterministic seed/host/Adam replay",)
        _, _, metric_issues = _derive_evaluation_metric(
            metric,
            unit_id=unit_id,
            root=root,
            arm=arm,
            final_model_hash=digest(expected_models[arm]),
            final_model_state=expected_models[arm],
        )
        if metric_issues:
            return ("bounded fixture differs from deterministic seed/host/Adam replay",)
    return ()


def _arm_aggregate(unit_metrics: Sequence[Mapping[str, object]]) -> dict[str, object]:
    mean_j = sum(float(metric["j_eval"]) for metric in unit_metrics) / len(unit_metrics)
    mean_kappa = sum(float(metric["kappa"]) for metric in unit_metrics) / len(unit_metrics)
    correct_units = sum(bool(metric["exact_correct_unit"]) for metric in unit_metrics)
    inverse_units = sum(bool(metric["exact_inverse_unit"]) for metric in unit_metrics)
    correct_pass = mean_j - 1.0 > 0.05 and mean_kappa >= 0.70 and correct_units >= 4
    return {
        "mean_j_eval": mean_j,
        "psi": mean_j - 1.0,
        "mean_kappa": mean_kappa,
        "exact_correct_units": correct_units,
        "exact_inverse_units": inverse_units,
        "correct_arm_pass": correct_pass,
        "unit_metrics": [
            {key: value for key, value in metric.items() if key != "clone_records"}
            for metric in unit_metrics
        ],
    }


def classify_b2(
    *,
    preflight_valid: bool,
    runtime_valid: bool,
    activity_valid: bool,
    aggregates: Mapping[str, Mapping[str, object]] | None,
) -> str:
    if not preflight_valid:
        return B2_BRANCH_PRECEDENCE[0]
    if not runtime_valid:
        return B2_BRANCH_PRECEDENCE[1]
    if not activity_valid or aggregates is None:
        return B2_BRANCH_PRECEDENCE[2]
    flip = aggregates["SUP_FLIP"]
    flipped_control_pass = (
        float(flip["mean_kappa"]) <= -0.70
        and int(flip["exact_inverse_units"]) >= 4
        and not bool(flip["correct_arm_pass"])
    )
    if not flipped_control_pass:
        return B2_BRANCH_PRECEDENCE[3]
    direct = bool(aggregates["SUP_TRUE"]["correct_arm_pass"])
    original = bool(aggregates["RL_ORIGINAL"]["correct_arm_pass"])
    if direct and not original:
        return B2_BRANCH_PRECEDENCE[4]
    if direct and original:
        return B2_BRANCH_PRECEDENCE[5]
    if not direct and original:
        return B2_BRANCH_PRECEDENCE[6]
    return B2_BRANCH_PRECEDENCE[7]


def _zero_activity() -> dict[str, int]:
    return {
        "result_bearing_runs": 0,
        "real_training_episodes": 0,
        "shadow_training_environment_episodes": 0,
        "evaluation_episodes": 0,
        "environment_transitions": 0,
        "optimizer_updates": 0,
        "evaluation_updates": 0,
        "evaluation_stochastic_action_draws": 0,
        "checkpoints_per_arm_unit": 0,
        "checkpoints_total": 0,
        "retries_rescues_sweeps": 0,
    }


def run_treatment(
    manifest: Mapping[str, object], *, repo_root: Path
) -> dict[str, object]:
    preflight = preflight_report(manifest, repo_root=repo_root)
    base = {
        "schema_version": B2_SCHEMA_VERSION,
        "artifact_kind": "vsp02_b2_result",
        "assignment_id": B2_ASSIGNMENT_ID,
        "candidate": B2_CANDIDATE,
        "host_id": B2_HOST_ID,
        "manifest": dict(manifest),
        "manifest_identity": manifest_identity(manifest),
        "preflight": preflight,
        "branch_precedence": list(B2_BRANCH_PRECEDENCE),
        "caps": dict(B2_CAPS),
        "retry_rescue_sweep": 0,
    }
    if not preflight["all_passed"]:
        return {
            **base,
            "branch": B2_BRANCH_PRECEDENCE[0],
            "activity": _zero_activity(),
            "runtime_contract": None,
            "units": [],
            "aggregates": None,
            "strongest_technical_limitation": (
                "The frozen construction failed before any result-bearing episode or update."
            ),
        }

    torch.set_num_threads(1)
    unit_results: list[dict[str, object]] = []
    evaluation_by_arm: dict[str, list[dict[str, object]]] = {
        arm: [] for arm in B2_ARMS
    }
    total_training_transitions = 0
    total_evaluation_transitions = 0
    panel_digests: dict[str, dict[str, str]] = {}

    for unit_index, (unit_id, root) in enumerate(B2_UNITS):
        unit = _train_unit(
            unit_id, root, capture_noninterference_receipt=unit_index == 0
        )
        models = unit.pop("models")
        assert isinstance(models, Mapping)
        total_training_transitions += int(unit["training"]["environment_transitions"])  # type: ignore[index]
        panel_digests[unit_id] = {}
        evaluation_clone_ids: set[str] = set()
        for arm in B2_ARMS:
            # Each arm gets an independently recreated RNG object initialized
            # from the same registered seeds.  Identical bytes certify the
            # common held-out clone/event panel.
            panel, panel_rng_receipt = _evaluation_panel_with_receipt(unit_id, root)
            panel_digests[unit_id][arm] = digest(panel)
            evaluation_clone_ids.update(str(row["clone_id"]) for row in panel)
            metric = _evaluate_arm_unit(
                unit_id=unit_id,
                arm=arm,
                model=models[arm],  # type: ignore[index]
                panel=panel,
                panel_rng_terminal_hashes=panel_rng_receipt,
            )
            evaluation_by_arm[arm].append(metric)
            total_evaluation_transitions += int(metric["environment_transitions"])
        unit["evaluation_clone_ids"] = sorted(evaluation_clone_ids)
        unit_results.append(unit)

    aggregates = {
        arm: _arm_aggregate(evaluation_by_arm[arm]) for arm in B2_ARMS
    }
    common_panels = all(
        len(set(per_arm.values())) == 1 for per_arm in panel_digests.values()
    )
    initial_matching = all(
        len(set(unit["training"]["initial_parameter_hashes"].values())) == 1  # type: ignore[index,union-attr]
        and len(set(unit["training"]["initial_optimizer_hashes"].values())) == 1  # type: ignore[index,union-attr]
        for unit in unit_results
    )
    batch_identity = all(
        bool(unit["training"]["immutable_batch_identity_all_arms"])  # type: ignore[index]
        for unit in unit_results
    )
    batch_contracts = all(
        bool(unit["training"]["immutable_batch_contract_all_rows"])  # type: ignore[index]
        for unit in unit_results
    )
    shadow_noninterference = all(
        bool(unit["training"]["shadow_noninterference_all_updates"])  # type: ignore[index]
        for unit in unit_results
    )
    rng_draw_match = all(
        bool(unit["training"]["minibatch_rng_draw_counts_equal"])  # type: ignore[index]
        and bool(unit["training"]["stochastic_rng_hashes_equal"])  # type: ignore[index]
        for unit in unit_results
    )
    routes_valid = True
    for unit in unit_results:
        updates = unit["training"]["updates"]  # type: ignore[index]
        for arm in B2_ARMS:
            expected_actor = (
                "-stop_gradient(G-b)*log(mu(A_behavior|history))-0.01*entropy"
                if arm == "RL_ORIGINAL"
                else "mean_cross_entropy(actor_logits[M_lifecycle],Y_true)"
                if arm == "SUP_TRUE"
                else "mean_cross_entropy(actor_logits[M_lifecycle],Y_flip)"
            )
            for update in updates[arm]:  # type: ignore[index]
                routes_valid = routes_valid and update["actor_route"] == expected_actor
                routes_valid = routes_valid and update["critic_route"] == "mean(0.5*(G-b)^2)"
                routes_valid = routes_valid and int(update["label_target_count"]) == (
                    0 if arm == "RL_ORIGINAL" else B2_BATCH_SIZE
                )

    activity = {
        "result_bearing_runs": 1,
        "real_training_episodes": sum(
            int(unit["training"]["real_rl_generated_episodes"])  # type: ignore[index]
            for unit in unit_results
        ),
        "shadow_training_environment_episodes": sum(
            int(unit["training"]["shadow_environment_episodes"])  # type: ignore[index]
            for unit in unit_results
        ),
        "evaluation_episodes": sum(
            int(metric["episodes"])
            for metrics in evaluation_by_arm.values()
            for metric in metrics
        ),
        "environment_transitions": total_training_transitions + total_evaluation_transitions,
        "optimizer_updates": sum(
            sum(int(count) for count in unit["training"]["updates_per_arm"].values())  # type: ignore[index,union-attr]
            for unit in unit_results
        ),
        "evaluation_updates": 0,
        "evaluation_stochastic_action_draws": 0,
        "checkpoints_per_arm_unit": 1,
        "checkpoints_total": 15,
        "retries_rescues_sweeps": 0,
    }
    activity_valid = (
        activity["real_training_episodes"] == B2_CAPS["real_training_episodes_total"]
        and activity["shadow_training_environment_episodes"] == 0
        and activity["evaluation_episodes"] == B2_CAPS["evaluation_episodes_total"]
        and activity["optimizer_updates"] == B2_CAPS["optimizer_updates_total"]
        and activity["environment_transitions"] <= B2_CAPS["environment_transitions_total"]
        and activity["evaluation_updates"] == 0
        and activity["evaluation_stochastic_action_draws"] == 0
        and activity["result_bearing_runs"] == 1
        and activity["retries_rescues_sweeps"] == 0
    )
    support_valid = all(
        unit["training"]["cue_counts"] == {"0": 512, "1": 512}  # type: ignore[index]
        and unit["training"]["updates_per_arm"] == {arm: 128 for arm in B2_ARMS}  # type: ignore[index]
        for unit in unit_results
    ) and all(
        metric["cue_counts"] == {"0": 64, "1": 64}
        and metric["episodes"] == 128
        for metrics in evaluation_by_arm.values()
        for metric in metrics
    )
    train_eval_disjoint = all(
        not (
            set(unit["training"]["train_clone_ids"])  # type: ignore[index]
            & set(unit["evaluation_clone_ids"])
        )
        for unit in unit_results
    )
    runtime_contract = {
        "initial_parameter_optimizer_equality": initial_matching,
        "immutable_batch_identity_all_arms": batch_identity,
        "immutable_batch_contract_all_rows": batch_contracts,
        "shadow_noninterference_all_updates": shadow_noninterference,
        "exact_loss_gradient_routes": routes_valid,
        "label_firewall": bool(preflight["label_firewall"]),
        "common_evaluation_panels": common_panels,
        "train_evaluation_clone_overlap": not train_eval_disjoint,
        "paired_rng_draw_counts": rng_draw_match,
        "finite_logits": all(
            bool(metric["finite_logits"])
            for metrics in evaluation_by_arm.values()
            for metric in metrics
        ),
        "first_registered_shadow_noninterference_receipt": [
            unit["training"]["p3_runtime"] for unit in unit_results  # type: ignore[index]
            if unit["training"]["p3_runtime"] is not None  # type: ignore[index]
        ],
        "panel_digests": panel_digests,
        "label_creation": "post-forward-input-and-immutable-batch-freeze",
        "rl_label_access": False,
        "supervised_original_lifecycle_actor_term_count": 0,
        "critic_definition_target_mask_coefficient_reduction_route_invariant": True,
        "realized_critic_or_shared_gradient_equality_claimed": False,
    }
    runtime_valid = all(
        (
            initial_matching,
            batch_identity,
            batch_contracts,
            shadow_noninterference,
            routes_valid,
            bool(preflight["label_firewall"]),
            common_panels,
            train_eval_disjoint,
            rng_draw_match,
            runtime_contract["finite_logits"],
        )
    )
    branch = classify_b2(
        preflight_valid=True,
        runtime_valid=runtime_valid,
        activity_valid=activity_valid and support_valid,
        aggregates=aggregates,
    )
    return {
        **base,
        "branch": branch,
        "activity": activity,
        "activity_valid": activity_valid,
        "support_valid": support_valid,
        "runtime_contract": runtime_contract,
        "units": unit_results,
        "aggregates": aggregates,
        "evaluation": evaluation_by_arm,
        "strongest_technical_limitation": (
            "All supervised learners are off-policy shadows conditional on the evolving "
            "RL_ORIGINAL generator; cross-entropy changes gradient density, normalization, "
            "magnitude and variance and may interact differently with Adam and clipping."
        ),
        "nonclaims": [
            "B1V2 explanation, repair, replication, or pooling",
            "actor-critic incapacity or fixed-representation sufficiency",
            "temporal-credit, gradient-scale, variance, optimizer, or sample-efficiency causality",
            "independent on-policy algorithm superiority",
            "architecture or lifecycle-mechanism value superiority",
            "C, External Pro, promotion, retirement, retry, rescue, or successor",
        ],
    }


def _metric_issues(metric: Mapping[str, object]) -> list[str]:
    issues: list[str] = []
    q0, q1 = float(metric.get("q_0", math.nan)), float(metric.get("q_1", math.nan))
    expected = _mixture_metrics_from_raw_q(q0=q0, q1=q1)
    for field, value in expected.items():
        if not math.isclose(float(metric.get(field, math.nan)), value, rel_tol=0.0, abs_tol=1e-12):
            issues.append(f"evaluation metric {field} mismatch")
    if not (0.0 < q0 < 1.0 and 0.0 < q1 < 1.0):
        issues.append("finite neural raw-softmax q lies outside strict endpoints")
    if metric.get("q_is_raw_softmax") is not True:
        issues.append("evaluation q is not bound to raw softmax")
    if metric.get("argmax_mixture_equivalent") is not True:
        issues.append("raw-softmax/mixed-policy argmax equivalence failed")
    if metric.get("cue_counts") != {"0": 64, "1": 64} or metric.get("episodes") != 128:
        issues.append("evaluation support mismatch")
    if metric.get("evaluation_updates") != 0 or metric.get("stochastic_action_draws") != 0:
        issues.append("evaluation update or stochastic action draw occurred")
    return issues


def _expected_initial_evidence(unit_id: str, root: int) -> dict[str, object]:
    parameter_payload = _pure_seeded_parameter_payload(unit_id, root)
    optimizer_payload = _pure_initial_optimizer_payload()
    return {
        "parameter_payload": parameter_payload,
        "parameter_hashes": {arm: digest(parameter_payload) for arm in B2_ARMS},
        "optimizer_payload": optimizer_payload,
        "optimizer_hashes": {arm: digest(optimizer_payload) for arm in B2_ARMS},
        "architecture": {arm: _pure_architecture_payload() for arm in B2_ARMS},
        "optimizer_contracts": {arm: _pure_optimizer_contract() for arm in B2_ARMS},
    }


def _derive_evaluation_metric(
    metric: Mapping[str, object],
    *,
    unit_id: str,
    root: int,
    arm: str,
    final_model_hash: str,
    final_model_state: Mapping[str, object],
) -> tuple[dict[str, object] | None, list[dict[str, object]], list[str]]:
    issues: list[str] = []
    try:
        final_parameters = _payload_tensors(final_model_state)
    except (TypeError, ValueError) as error:
        return None, [], [f"{unit_id}/{arm} final model payload invalid: {error}"]
    records = metric.get("clone_records")
    if not isinstance(records, list) or len(records) != B2_EVAL_EPISODES_PER_UNIT_ARM:
        return None, [], [f"{unit_id}/{arm} retained clone record count mismatch"]
    release_by_cue: dict[int, list[float]] = {0: [], 1: []}
    choices: dict[int, list[str | None]] = {0: [], 1: []}
    panel: list[dict[str, object]] = []
    transitions = 0
    expected_record_fields = {
        "clone_id",
        "owner_epoch",
        "true_cue",
        "event_tape_token",
        "logits",
        "raw_softmax",
        "behavior_probabilities",
        "argmax_action",
        "executed_action",
        "environment_transitions",
    }
    for index, record in enumerate(records):
        if not isinstance(record, Mapping) or set(record) != expected_record_fields:
            issues.append(f"{unit_id}/{arm} clone {index} schema mismatch")
            continue
        expected_clone = f"{unit_id}/EVAL/{index:03d}"
        expected_owner = f"{unit_id}-EV-{index:03d}"
        if record.get("clone_id") != expected_clone or record.get("owner_epoch") != expected_owner:
            issues.append(f"{unit_id}/{arm} clone {index} identity mismatch")
        cue = record.get("true_cue")
        if cue not in (0, 1):
            issues.append(f"{unit_id}/{arm} clone {index} cue mismatch")
            continue
        logits = record.get("logits")
        raw = record.get("raw_softmax")
        behavior = record.get("behavior_probabilities")
        if (
            not isinstance(logits, list)
            or len(logits) != 2
            or not isinstance(raw, list)
            or len(raw) != 2
            or not isinstance(behavior, list)
            or len(behavior) != 2
        ):
            issues.append(f"{unit_id}/{arm} clone {index} logit/probability shape mismatch")
            continue
        logit_values = [float(value) for value in logits]
        if any(not math.isfinite(value) for value in logit_values):
            issues.append(f"{unit_id}/{arm} clone {index} non-finite logits")
            continue
        expected_observations = _synthetic_history(
            int(cue), owner_epoch=str(record["owner_epoch"])
        )
        expected_logits, _, _, _, _ = _pure_forward_parameters(
            final_parameters, expected_observations
        )
        if any(
            not math.isclose(actual, float(expected), rel_tol=0.0, abs_tol=1e-12)
            for actual, expected in zip(logit_values, expected_logits)
        ):
            issues.append(f"{unit_id}/{arm} clone {index} logits differ from final model")
        maximum = max(logit_values)
        exponentials = [math.exp(value - maximum) for value in logit_values]
        denominator = sum(exponentials)
        expected_raw = [value / denominator for value in exponentials]
        raw_values = [float(value) for value in raw]
        behavior_values = [float(value) for value in behavior]
        if any(
            not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12)
            for actual, expected in zip(raw_values, expected_raw)
        ):
            issues.append(f"{unit_id}/{arm} clone {index} raw softmax mismatch")
        expected_behavior = [0.1 + 0.8 * value for value in raw_values]
        if any(
            not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12)
            for actual, expected in zip(behavior_values, expected_behavior)
        ):
            issues.append(f"{unit_id}/{arm} clone {index} once-mixed behavior mismatch")
        raw_choice = (
            b1.Action.RELEASE.value
            if raw_values[0] > raw_values[1]
            else b1.Action.HOLD.value
            if raw_values[1] > raw_values[0]
            else None
        )
        behavior_choice = (
            b1.Action.RELEASE.value
            if behavior_values[0] > behavior_values[1]
            else b1.Action.HOLD.value
            if behavior_values[1] > behavior_values[0]
            else None
        )
        if raw_choice != behavior_choice or record.get("argmax_action") != raw_choice:
            issues.append(f"{unit_id}/{arm} clone {index} argmax mismatch")
        expected_executed = raw_choice if raw_choice is not None else b1.Action.HOLD.value
        if record.get("executed_action") != expected_executed:
            issues.append(f"{unit_id}/{arm} clone {index} executed action mismatch")
        episode_transitions = record.get("environment_transitions")
        expected_transitions = 4 if expected_executed == b1.Action.RELEASE.value else 5
        if episode_transitions != expected_transitions:
            issues.append(f"{unit_id}/{arm} clone {index} transition count mismatch")
        else:
            transitions += int(episode_transitions)
        release_by_cue[int(cue)].append(raw_values[0])
        choices[int(cue)].append(raw_choice)
        panel.append(
            {
                "clone_id": record["clone_id"],
                "owner_epoch": record["owner_epoch"],
                "true_cue": cue,
                "event_tape_token": record["event_tape_token"],
            }
        )
    if any(len(release_by_cue[cue]) != 64 for cue in (0, 1)):
        issues.append(f"{unit_id}/{arm} evaluation cue support mismatch")
        return None, panel, issues
    q0 = sum(release_by_cue[0]) / 64
    q1 = sum(release_by_cue[1]) / 64
    projected = _mixture_metrics_from_raw_q(q0=q0, q1=q1)
    exact_correct = all(value == b1.Action.HOLD.value for value in choices[0]) and all(
        value == b1.Action.RELEASE.value for value in choices[1]
    )
    exact_inverse = all(value == b1.Action.RELEASE.value for value in choices[0]) and all(
        value == b1.Action.HOLD.value for value in choices[1]
    )
    expected_panel, expected_panel_rng = _evaluation_panel_with_receipt(unit_id, root)
    if panel != expected_panel:
        issues.append(f"{unit_id}/{arm} evaluation panel seed replay mismatch")
    derived = {
        "unit_id": unit_id,
        "arm": arm,
        "checkpoint_id": f"{unit_id}/{arm}/FINAL/128",
        "final_model_hash": final_model_hash,
        "panel_digest": digest(panel),
        "panel_rng_terminal_hashes": expected_panel_rng,
        "clone_records": records,
        "episodes": 128,
        "cue_counts": {"0": 64, "1": 64},
        "environment_transitions": transitions,
        "q_0": q0,
        "q_1": q1,
        **projected,
        "exact_correct_unit": exact_correct,
        "exact_inverse_unit": exact_inverse,
        "argmax_ties": sum(value is None for values in choices.values() for value in values),
        "finite_logits": True,
        "q_is_raw_softmax": True,
        "argmax_mixture_equivalent": True,
        "evaluation_updates": 0,
        "stochastic_action_draws": 0,
    }
    for key, value in derived.items():
        if key == "clone_records":
            continue
        actual = metric.get(key)
        if isinstance(value, float):
            if not math.isclose(float(actual if actual is not None else math.nan), value, rel_tol=0.0, abs_tol=1e-12):
                issues.append(f"{unit_id}/{arm} derived metric {key} mismatch")
        elif actual != value:
            issues.append(f"{unit_id}/{arm} derived metric {key} mismatch")
    return derived, panel, issues


def _pure_expected_training_row(
    *,
    unit_id: str,
    update_index: int,
    schedule_row: Mapping[str, object],
    rl_parameters: Mapping[str, Tensor],
    event_rng: random.Random,
    action_rng: random.Random,
) -> dict[str, object]:
    """Reconstruct one host row from the frozen physical law without a host call."""

    episode_index = int(schedule_row["episode_index"])
    owner_epoch = str(schedule_row["owner_epoch"])
    cue = int(schedule_row["true_cue"])
    event_token = event_rng.getrandbits(64)
    observations = _synthetic_history(cue, owner_epoch=owner_epoch)
    _, _, probability_tensor, _, _ = _pure_forward_parameters(
        rl_parameters, observations
    )
    probabilities = [float(value) for value in probability_tensor]
    action = (
        b1.Action.RELEASE
        if action_rng.random() < probabilities[b1.Action.RELEASE.index]
        else b1.Action.HOLD
    )
    if action is b1.Action.RELEASE:
        rewards = [1]
        environment_transitions = 4
    else:
        rewards = [-1 if cue else 2, 0]
        environment_transitions = 5
    lifecycle_id = (
        f"{B2_ASSIGNMENT_ID}/{unit_id}/TRAIN/{episode_index:04d}/{event_token:016x}"
    )
    return json.loads(
        canonical_bytes(
            {
                "O": observations,
                "H0": [0.0] * b1.B1_HIDDEN_SIZE,
                "M_reset": [1, 0],
                "M_active": [1, 1],
                "M_valid": [0, 1],
                "M_lifecycle": [0, 1],
                "A_behavior": action.value,
                "R": rewards,
                "Done": [False] * (len(rewards) - 1) + [True],
                "G": sum(
                    reward * b1.B1_GAMMA**index
                    for index, reward in enumerate(rewards)
                ),
                "behavior_probabilities": probabilities,
                "environment_transitions": environment_transitions,
                "metadata": {
                    "unit_id": unit_id,
                    "update_index": update_index,
                    "episode_index": episode_index,
                    "owner_epoch": owner_epoch,
                    "true_cue": cue,
                    "clone_id": str(schedule_row["clone_id"]),
                    "event_tape_token": f"{event_token:016x}",
                    "physical_tape_ids": [f"{B2_PHYSICAL_TAPE_PREFIX}/{lifecycle_id}"],
                },
            }
        )
    )


def _summary_matches(actual: object, expected: Mapping[str, object]) -> bool:
    if not isinstance(actual, Mapping) or set(actual) != set(expected):
        return False
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if isinstance(expected_value, float):
            if not math.isclose(
                float(actual_value if actual_value is not None else math.nan),
                expected_value,
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                return False
        elif actual_value != expected_value:
            return False
    return True


def _pure_reconstruct_training(
    training: Mapping[str, object], *, unit_id: str, root: int
) -> tuple[dict[str, object] | None, list[str]]:
    """Replay retained rows/update math without host, optimizer, or evaluator calls."""

    issues: list[str] = []
    batches = training.get("batch_records")
    updates = training.get("updates")
    if not isinstance(batches, list) or len(batches) != B2_UPDATES_PER_UNIT:
        return None, [f"{unit_id} pure replay batch evidence missing"]
    if not isinstance(updates, Mapping) or set(updates) != set(B2_ARMS):
        return None, [f"{unit_id} pure replay update evidence missing"]
    expected_initial = _expected_initial_evidence(unit_id, root)
    initial_payload = expected_initial["parameter_payload"]
    assert isinstance(initial_payload, Mapping)
    parameters = {
        arm: _payload_tensors(initial_payload) for arm in B2_ARMS
    }
    moments: dict[str, dict[str, tuple[Tensor, Tensor]]] = {
        arm: {} for arm in B2_ARMS
    }
    schedule, schedule_terminal = _schedule_with_receipt(unit_id, root)
    event_rng = random.Random(b2_seed(unit_id, root, "train_environment_event"))
    action_rng = random.Random(b2_seed(unit_id, root, "train_action_uniform"))
    minibatch_rngs = {
        arm: random.Random(b2_seed(unit_id, root, "train_minibatch_order"))
        for arm in B2_ARMS
    }
    stochastic_rngs = {
        arm: random.Random(b2_seed(unit_id, root, "train_stochastic_layer"))
        for arm in B2_ARMS
    }
    expected_receipts: list[dict[str, object]] = []
    for update_index, batch_record in enumerate(batches):
        if not isinstance(batch_record, Mapping):
            issues.append(f"{unit_id} pure replay batch {update_index} schema mismatch")
            continue
        retained_rows = batch_record.get("rows")
        if not isinstance(retained_rows, list) or len(retained_rows) != B2_BATCH_SIZE:
            issues.append(f"{unit_id} pure replay batch {update_index} row count mismatch")
            continue
        expected_rows = [
            _pure_expected_training_row(
                unit_id=unit_id,
                update_index=update_index,
                schedule_row=schedule[update_index * B2_BATCH_SIZE + within_update],
                rl_parameters=parameters["RL_ORIGINAL"],
                event_rng=event_rng,
                action_rng=action_rng,
            )
            for within_update in range(B2_BATCH_SIZE)
        ]
        if canonical_bytes(retained_rows) != canonical_bytes(expected_rows):
            issues.append(f"{unit_id} batch {update_index} differs from seeded host-law reconstruction")
        batch_digest = digest(expected_rows)
        expected_transition_count = sum(
            int(row["environment_transitions"]) for row in expected_rows
        )
        if (
            batch_record.get("batch_digest") != batch_digest
            or batch_record.get("environment_transitions") != expected_transition_count
        ):
            issues.append(f"{unit_id} batch {update_index} pure projection mismatch")
        orders: dict[str, list[int]] = {}
        for arm in B2_ARMS:
            order = list(range(B2_BATCH_SIZE))
            minibatch_rngs[arm].shuffle(order)
            orders[arm] = order
            arm_updates = updates.get(arm)
            actual_update = (
                arm_updates[update_index]
                if isinstance(arm_updates, list) and len(arm_updates) == B2_UPDATES_PER_UNIT
                else None
            )
            next_parameters, next_moments, expected_summary = _pure_adam_update(
                arm,
                parameters[arm],
                moments[arm],
                step=update_index,
                batch=[expected_rows[index] for index in order],
            )
            expected_summary.update(
                {
                    "update_index": update_index,
                    "batch_digest": batch_digest,
                    "batch_order": order,
                }
            )
            if not _summary_matches(actual_update, expected_summary):
                issues.append(f"{unit_id}/{arm} update {update_index} pure Adam reconstruction mismatch")
            parameters[arm] = next_parameters
            moments[arm] = next_moments
        successor_state = {
            "unit_id": unit_id,
            "next_update": update_index + 1,
            "event_rng": rng_digest(event_rng),
            "action_rng": rng_digest(action_rng),
        }
        rl_hashes = {
            "rl_parameters": digest(_pure_model_payload(parameters["RL_ORIGINAL"])),
            "rl_optimizer": digest(
                _pure_optimizer_payload(moments["RL_ORIGINAL"], step=update_index + 1)
            ),
            "rl_rng": rng_digest(action_rng),
            "rl_successor_state": digest(successor_state),
            "immutable_batch": batch_digest,
        }
        expected_receipts.append(
            {
                "update_index": update_index,
                "batch_digest": batch_digest,
                "before": rl_hashes,
                "after": rl_hashes,
                "hash_identity": True,
            }
        )
    expected_final_models = {
        arm: _pure_model_payload(parameters[arm]) for arm in B2_ARMS
    }
    expected_final_optimizers = {
        arm: _pure_optimizer_payload(moments[arm], step=B2_UPDATES_PER_UNIT)
        for arm in B2_ARMS
    }
    if canonical_bytes(training.get("final_model_states")) != canonical_bytes(expected_final_models):
        issues.append(f"{unit_id} final model states differ from pure update reconstruction")
    if canonical_bytes(training.get("final_optimizer_states")) != canonical_bytes(expected_final_optimizers):
        issues.append(f"{unit_id} final Adam states differ from pure update reconstruction")
    if training.get("shadow_noninterference_receipts") != expected_receipts:
        issues.append(f"{unit_id} shadow receipts differ from pure reconstruction")
    expected_minibatch_terminals = {
        arm: rng_digest(rng) for arm, rng in minibatch_rngs.items()
    }
    expected_stochastic_terminals = {
        arm: rng_digest(rng) for arm, rng in stochastic_rngs.items()
    }
    expected_terminal = {
        "train_owner_cue_clone": schedule_terminal,
        "train_environment_event": rng_digest(event_rng),
        "train_action_uniform": rng_digest(action_rng),
        "train_minibatch_order_by_arm": expected_minibatch_terminals,
        "train_stochastic_layer_by_arm": expected_stochastic_terminals,
    }
    if training.get("minibatch_rng_hashes") != expected_minibatch_terminals:
        issues.append(f"{unit_id} minibatch terminal RNG differs from seed replay")
    if training.get("stochastic_rng_hashes") != expected_stochastic_terminals:
        issues.append(f"{unit_id} stochastic terminal RNG differs from seed replay")
    if training.get("terminal_rng_hashes") != expected_terminal:
        issues.append(f"{unit_id} terminal RNG evidence differs from seed replay")
    return {
        "final_model_states": expected_final_models,
        "final_optimizer_states": expected_final_optimizers,
        "receipts": expected_receipts,
    }, issues


def _derive_training_unit(
    unit: Mapping[str, object], *, unit_id: str, root: int, first_unit: bool
) -> tuple[dict[str, object] | None, list[str]]:
    issues: list[str] = []
    if unit.get("unit_id") != unit_id or unit.get("decimal_root") != root:
        issues.append(f"{unit_id} unit/root identity mismatch")
    training = unit.get("training")
    if not isinstance(training, Mapping):
        return None, issues + [f"{unit_id} training evidence missing"]
    expected_initial = _expected_initial_evidence(unit_id, root)
    if training.get("initial_parameter_hashes") != expected_initial["parameter_hashes"]:
        issues.append(f"{unit_id} seeded initial parameter hashes mismatch")
    if training.get("initial_optimizer_hashes") != expected_initial["optimizer_hashes"]:
        issues.append(f"{unit_id} seeded initial optimizer hashes mismatch")
    pure_evidence, pure_issues = _pure_reconstruct_training(
        training, unit_id=unit_id, root=root
    )
    issues.extend(pure_issues)

    batches = training.get("batch_records")
    if not isinstance(batches, list) or len(batches) != B2_UPDATES_PER_UNIT:
        return None, issues + [f"{unit_id} retained batch record count mismatch"]
    batch_digests: list[str] = []
    train_clones: list[str] = []
    cue_counts: Counter[int] = Counter()
    transitions = 0
    expected_schedule, expected_schedule_terminal = _schedule_with_receipt(unit_id, root)
    for update_index, record in enumerate(batches):
        if not isinstance(record, Mapping) or record.get("update_index") != update_index:
            issues.append(f"{unit_id} batch {update_index} identity mismatch")
            continue
        rows = record.get("rows")
        if not isinstance(rows, list) or len(rows) != B2_BATCH_SIZE:
            issues.append(f"{unit_id} batch {update_index} row count mismatch")
            continue
        batch_digest = digest(rows)
        batch_digests.append(batch_digest)
        if record.get("batch_digest") != batch_digest:
            issues.append(f"{unit_id} batch {update_index} digest mismatch")
        batch_transitions = 0
        batch_cues: Counter[int] = Counter()
        for within_update, row in enumerate(rows):
            if not isinstance(row, Mapping) or not _immutable_row_contract(row):
                issues.append(f"{unit_id} batch {update_index} immutable row contract mismatch")
                continue
            metadata = row["metadata"]
            assert isinstance(metadata, Mapping)
            episode_index = update_index * B2_BATCH_SIZE + within_update
            expected_clone = f"{unit_id}/TRAIN/{episode_index:04d}"
            if (
                metadata.get("unit_id") != unit_id
                or metadata.get("update_index") != update_index
                or metadata.get("episode_index") != episode_index
                or metadata.get("clone_id") != expected_clone
                or metadata.get("true_cue") != expected_schedule[episode_index]["true_cue"]
                or metadata.get("owner_epoch") != expected_schedule[episode_index]["owner_epoch"]
            ):
                issues.append(f"{unit_id} batch {update_index} row identity mismatch")
            cue = int(metadata["true_cue"])
            batch_cues[cue] += 1
            cue_counts[cue] += 1
            train_clones.append(str(metadata["clone_id"]))
            batch_transitions += int(row["environment_transitions"])
        if batch_cues != Counter({0: 4, 1: 4}):
            issues.append(f"{unit_id} batch {update_index} cue balance mismatch")
        if record.get("environment_transitions") != batch_transitions:
            issues.append(f"{unit_id} batch {update_index} transition projection mismatch")
        transitions += batch_transitions
    if len(train_clones) != len(set(train_clones)):
        issues.append(f"{unit_id} duplicate training clone identity")
    if training.get("batch_digests") != batch_digests:
        issues.append(f"{unit_id} batch digest projection mismatch")
    if training.get("train_clone_ids") != train_clones:
        issues.append(f"{unit_id} train clone projection mismatch")
    if training.get("cue_counts") != {"0": cue_counts[0], "1": cue_counts[1]}:
        issues.append(f"{unit_id} training cue projection mismatch")
    if training.get("environment_transitions") != transitions:
        issues.append(f"{unit_id} training transition projection mismatch")
    if training.get("real_rl_generated_episodes") != len(train_clones):
        issues.append(f"{unit_id} training episode projection mismatch")
    if training.get("shadow_environment_episodes") != 0:
        issues.append(f"{unit_id} shadow environment activity is nonzero")

    updates = training.get("updates")
    if not isinstance(updates, Mapping) or set(updates) != set(B2_ARMS):
        return None, issues + [f"{unit_id} arm update evidence mismatch"]
    initial_parameters = expected_initial["parameter_hashes"]
    initial_optimizers = expected_initial["optimizer_hashes"]
    final_hashes: dict[str, str] = {}
    common_orders: list[list[int]] | None = None
    for arm in B2_ARMS:
        arm_updates = updates.get(arm)
        if not isinstance(arm_updates, list) or len(arm_updates) != B2_UPDATES_PER_UNIT:
            issues.append(f"{unit_id}/{arm} update count mismatch")
            continue
        orders: list[list[int]] = []
        previous_parameter = str(initial_parameters[arm])  # type: ignore[index]
        previous_optimizer = str(initial_optimizers[arm])  # type: ignore[index]
        expected_actor = (
            "-stop_gradient(G-b)*log(mu(A_behavior|history))-0.01*entropy"
            if arm == "RL_ORIGINAL"
            else "mean_cross_entropy(actor_logits[M_lifecycle],Y_true)"
            if arm == "SUP_TRUE"
            else "mean_cross_entropy(actor_logits[M_lifecycle],Y_flip)"
        )
        for update_index, update in enumerate(arm_updates):
            if not isinstance(update, Mapping):
                issues.append(f"{unit_id}/{arm} update {update_index} schema mismatch")
                continue
            order = update.get("batch_order")
            if not isinstance(order, list) or sorted(order) != list(range(B2_BATCH_SIZE)):
                issues.append(f"{unit_id}/{arm} update {update_index} order mismatch")
                order = []
            orders.append(order)
            if update.get("update_index") != update_index or update.get("batch_digest") != batch_digests[update_index]:
                issues.append(f"{unit_id}/{arm} update {update_index} batch binding mismatch")
            if update.get("parameters_before") != previous_parameter:
                issues.append(f"{unit_id}/{arm} update {update_index} parameter chain mismatch")
            if update.get("optimizer_before") != previous_optimizer:
                issues.append(f"{unit_id}/{arm} update {update_index} optimizer chain mismatch")
            previous_parameter = str(update.get("parameters_after", ""))
            previous_optimizer = str(update.get("optimizer_after", ""))
            if update.get("actor_route") != expected_actor or update.get("critic_route") != "mean(0.5*(G-b)^2)":
                issues.append(f"{unit_id}/{arm} update {update_index} loss route mismatch")
            if update.get("label_target_count") != (0 if arm == "RL_ORIGINAL" else B2_BATCH_SIZE):
                issues.append(f"{unit_id}/{arm} update {update_index} label route mismatch")
            if update.get("clip_threshold") != 1.0:
                issues.append(f"{unit_id}/{arm} update {update_index} clip mismatch")
            for field in ("loss", "actor_loss", "critic_loss", "gradient_norm_before_clip"):
                if not math.isfinite(float(update.get(field, math.nan))):
                    issues.append(f"{unit_id}/{arm} update {update_index} non-finite {field}")
        if common_orders is None:
            common_orders = orders
        elif orders != common_orders:
            issues.append(f"{unit_id}/{arm} paired batch order differs")
        final_hashes[arm] = previous_parameter
    if training.get("final_parameter_hashes") != final_hashes:
        issues.append(f"{unit_id} final parameter hash projection mismatch")
    final_model_states = training.get("final_model_states")
    if not isinstance(final_model_states, Mapping) or {
        arm: digest(final_model_states.get(arm)) for arm in B2_ARMS
    } != final_hashes:
        issues.append(f"{unit_id} retained final model state/hash mismatch")
    final_optimizer_states = training.get("final_optimizer_states")
    if not isinstance(final_optimizer_states, Mapping):
        issues.append(f"{unit_id} retained final optimizer states missing")
    else:
        for arm in B2_ARMS:
            arm_updates = updates.get(arm)
            expected_optimizer_hash = (
                arm_updates[-1].get("optimizer_after")
                if isinstance(arm_updates, list) and arm_updates and isinstance(arm_updates[-1], Mapping)
                else None
            )
            if digest(final_optimizer_states.get(arm)) != expected_optimizer_hash:
                issues.append(f"{unit_id}/{arm} retained final optimizer state/hash mismatch")
    if training.get("updates_per_arm") != {arm: B2_UPDATES_PER_UNIT for arm in B2_ARMS}:
        issues.append(f"{unit_id} update-count projection mismatch")

    receipts = training.get("shadow_noninterference_receipts")
    if not isinstance(receipts, list) or len(receipts) != B2_UPDATES_PER_UNIT:
        issues.append(f"{unit_id} shadow noninterference receipt count mismatch")
    else:
        for update_index, receipt in enumerate(receipts):
            if not isinstance(receipt, Mapping):
                issues.append(f"{unit_id} shadow receipt {update_index} schema mismatch")
                continue
            before, after = receipt.get("before"), receipt.get("after")
            if (
                receipt.get("update_index") != update_index
                or receipt.get("batch_digest") != batch_digests[update_index]
                or before != after
                or receipt.get("hash_identity") is not True
                or not isinstance(before, Mapping)
                or before.get("immutable_batch") != batch_digests[update_index]
            ):
                issues.append(f"{unit_id} shadow receipt {update_index} mismatch")
    p3 = training.get("p3_runtime")
    if first_unit:
        if not isinstance(p3, Mapping) or not isinstance(receipts, list) or not receipts:
            issues.append(f"{unit_id} first noninterference receipt missing")
        elif (
            p3.get("fixture") != f"{unit_id}/UPDATE/000"
            or p3.get("before") != receipts[0].get("before")
            or p3.get("after") != receipts[0].get("after")
            or p3.get("hash_identity") is not True
            or p3.get("batch_read_only") is not True
            or any(p3.get(field) != 0 for field in ("extra_roots", "extra_arms", "extra_episodes", "extra_updates", "extra_checkpoints"))
        ):
            issues.append(f"{unit_id} P3 retained receipt mismatch")
    elif p3 is not None:
        issues.append(f"{unit_id} unexpected extra P3 retained receipt")

    minibatch_hashes = training.get("minibatch_rng_hashes")
    stochastic_hashes = training.get("stochastic_rng_hashes")
    if not isinstance(minibatch_hashes, Mapping) or set(minibatch_hashes) != set(B2_ARMS) or len(set(minibatch_hashes.values())) != 1:
        issues.append(f"{unit_id} minibatch RNG pairing mismatch")
    if not isinstance(stochastic_hashes, Mapping) or set(stochastic_hashes) != set(B2_ARMS) or len(set(stochastic_hashes.values())) != 1:
        issues.append(f"{unit_id} stochastic RNG pairing mismatch")
    if training.get("stochastic_rng_draw_counts") != {arm: 0 for arm in B2_ARMS}:
        issues.append(f"{unit_id} stochastic RNG draw count mismatch")
    terminal_rng = training.get("terminal_rng_hashes")
    if not isinstance(terminal_rng, Mapping) or terminal_rng.get("train_owner_cue_clone") != expected_schedule_terminal:
        issues.append(f"{unit_id} schedule terminal RNG mismatch")

    return {
        "unit_id": unit_id,
        "root": root,
        "training_episodes": len(train_clones),
        "training_transitions": transitions,
        "training_cues": {"0": cue_counts[0], "1": cue_counts[1]},
        "optimizer_updates": sum(
            len(updates[arm]) if isinstance(updates.get(arm), list) else 0 for arm in B2_ARMS
        ),
        "train_clone_ids": train_clones,
        "batch_digests": batch_digests,
        "final_parameter_hashes": final_hashes,
        "final_model_states": (
            pure_evidence["final_model_states"]
            if isinstance(pure_evidence, Mapping)
            else training.get("final_model_states")
        ),
        "p3": p3,
        "runtime_valid": not issues,
    }, issues


def _derive_runtime_result(result: Mapping[str, object]) -> tuple[dict[str, object], list[str]]:
    issues: list[str] = []
    units = result.get("units")
    evaluations = result.get("evaluation")
    if not isinstance(units, list) or len(units) != len(B2_UNITS):
        return {}, ["retained result must contain exactly five unit/root records"]
    if not isinstance(evaluations, Mapping) or set(evaluations) != set(B2_ARMS):
        return {}, ["retained result must contain exactly three evaluation arm records"]
    for arm in B2_ARMS:
        if not isinstance(evaluations.get(arm), list) or len(evaluations[arm]) != len(B2_UNITS):
            return {}, [f"{arm} must contain exactly five retained unit evaluations"]

    derived_training: dict[str, dict[str, object]] = {}
    derived_metrics: dict[str, list[dict[str, object]]] = {arm: [] for arm in B2_ARMS}
    panel_digests: dict[str, dict[str, str]] = {}
    evaluation_clone_ids: dict[str, set[str]] = {}
    total_eval_transitions = 0
    checkpoints: set[str] = set()
    for unit_index, (unit_id, root) in enumerate(B2_UNITS):
        unit = units[unit_index]
        if not isinstance(unit, Mapping):
            issues.append(f"{unit_id} retained unit is not an object")
            continue
        training, training_issues = _derive_training_unit(
            unit, unit_id=unit_id, root=root, first_unit=unit_index == 0
        )
        issues.extend(training_issues)
        if training is None:
            continue
        derived_training[unit_id] = training
        supplied_eval_clones = unit.get("evaluation_clone_ids")
        evaluation_clone_ids[unit_id] = set()
        panel_digests[unit_id] = {}
        for arm in B2_ARMS:
            metric = evaluations[arm][unit_index]
            if not isinstance(metric, Mapping):
                issues.append(f"{unit_id}/{arm} evaluation is not an object")
                continue
            final_states = training.get("final_model_states")
            if not isinstance(final_states, Mapping) or not isinstance(
                final_states.get(arm), Mapping
            ):
                issues.append(f"{unit_id}/{arm} final model state is unavailable")
                continue
            derived_metric, panel, metric_issues = _derive_evaluation_metric(
                metric,
                unit_id=unit_id,
                root=root,
                arm=arm,
                final_model_hash=str(training["final_parameter_hashes"].get(arm, "")),  # type: ignore[union-attr]
                final_model_state=final_states[arm],  # type: ignore[index]
            )
            issues.extend(metric_issues)
            if derived_metric is None:
                continue
            derived_metrics[arm].append(derived_metric)
            panel_digests[unit_id][arm] = digest(panel)
            evaluation_clone_ids[unit_id].update(
                str(record["clone_id"]) for record in derived_metric["clone_records"]  # type: ignore[index]
            )
            total_eval_transitions += int(derived_metric["environment_transitions"])
            checkpoints.add(str(derived_metric["checkpoint_id"]))
        if supplied_eval_clones != sorted(evaluation_clone_ids[unit_id]):
            issues.append(f"{unit_id} evaluation clone projection mismatch")
        if len(set(panel_digests[unit_id].values())) != 1:
            issues.append(f"{unit_id} common evaluation panel mismatch")
        if set(training["train_clone_ids"]) & evaluation_clone_ids[unit_id]:  # type: ignore[arg-type]
            issues.append(f"{unit_id} train/evaluation clone overlap")

    if set(derived_training) != {unit for unit, _ in B2_UNITS}:
        issues.append("complete five-unit training evidence was not derivable")
    if any(len(derived_metrics[arm]) != len(B2_UNITS) for arm in B2_ARMS):
        issues.append("complete fifteen-checkpoint evaluation evidence was not derivable")

    aggregates = (
        {arm: _arm_aggregate(derived_metrics[arm]) for arm in B2_ARMS}
        if all(len(derived_metrics[arm]) == len(B2_UNITS) for arm in B2_ARMS)
        else None
    )
    if aggregates is not None and result.get("aggregates") != aggregates:
        issues.append("aggregate projection differs from retained clone evidence")

    training_episodes = sum(int(unit["training_episodes"]) for unit in derived_training.values())
    training_transitions = sum(int(unit["training_transitions"]) for unit in derived_training.values())
    optimizer_updates = sum(int(unit["optimizer_updates"]) for unit in derived_training.values())
    evaluation_episodes = sum(
        int(metric["episodes"]) for metrics in derived_metrics.values() for metric in metrics
    )
    derived_activity = {
        "result_bearing_runs": 1,
        "real_training_episodes": training_episodes,
        "shadow_training_environment_episodes": 0,
        "evaluation_episodes": evaluation_episodes,
        "environment_transitions": training_transitions + total_eval_transitions,
        "optimizer_updates": optimizer_updates,
        "evaluation_updates": sum(
            int(metric["evaluation_updates"])
            for metrics in derived_metrics.values()
            for metric in metrics
        ),
        "evaluation_stochastic_action_draws": sum(
            int(metric["stochastic_action_draws"])
            for metrics in derived_metrics.values()
            for metric in metrics
        ),
        "checkpoints_per_arm_unit": 1 if len(checkpoints) == 15 else 0,
        "checkpoints_total": len(checkpoints),
        "retries_rescues_sweeps": 0,
    }
    if result.get("activity") != derived_activity:
        issues.append("activity projection differs from retained update/evaluation records")
    support_valid = (
        all(
            unit["training_episodes"] == 1_024
            and unit["training_cues"] == {"0": 512, "1": 512}
            and unit["optimizer_updates"] == 384
            for unit in derived_training.values()
        )
        and evaluation_episodes == 1_920
        and len(checkpoints) == 15
    )
    activity_valid = (
        training_episodes == B2_CAPS["real_training_episodes_total"]
        and evaluation_episodes == B2_CAPS["evaluation_episodes_total"]
        and optimizer_updates == B2_CAPS["optimizer_updates_total"]
        and derived_activity["environment_transitions"] <= B2_CAPS["environment_transitions_total"]
        and derived_activity["evaluation_updates"] == 0
        and derived_activity["evaluation_stochastic_action_draws"] == 0
        and len(checkpoints) == 15
    )
    if result.get("support_valid") is not support_valid:
        issues.append("support_valid differs from retained records")
    if result.get("activity_valid") is not activity_valid:
        issues.append("activity_valid differs from retained records")

    first_p3 = (
        [derived_training[B2_UNITS[0][0]]["p3"]]
        if B2_UNITS[0][0] in derived_training
        else []
    )
    expected_runtime = {
        "initial_parameter_optimizer_equality": not any(
            "seeded initial" in issue for issue in issues
        ),
        "immutable_batch_identity_all_arms": not any(
            "batch binding" in issue or "paired batch order" in issue for issue in issues
        ),
        "immutable_batch_contract_all_rows": not any(
            "immutable row contract" in issue for issue in issues
        ),
        "shadow_noninterference_all_updates": not any(
            "shadow receipt" in issue for issue in issues
        ),
        "exact_loss_gradient_routes": not any(
            "loss route" in issue or "label route" in issue for issue in issues
        ),
        "label_firewall": not any("immutable row contract" in issue for issue in issues),
        "common_evaluation_panels": all(
            len(values) == 3 and len(set(values.values())) == 1
            for values in panel_digests.values()
        ),
        "train_evaluation_clone_overlap": any("clone overlap" in issue for issue in issues),
        "paired_rng_draw_counts": not any("RNG" in issue for issue in issues),
        "finite_logits": not any("non-finite logits" in issue for issue in issues),
        "first_registered_shadow_noninterference_receipt": first_p3,
        "panel_digests": panel_digests,
        "label_creation": "post-forward-input-and-immutable-batch-freeze",
        "rl_label_access": False,
        "supervised_original_lifecycle_actor_term_count": 0,
        "critic_definition_target_mask_coefficient_reduction_route_invariant": True,
        "realized_critic_or_shared_gradient_equality_claimed": False,
    }
    runtime_valid = all(
        expected_runtime[field] is expected
        for field, expected in {
            "initial_parameter_optimizer_equality": True,
            "immutable_batch_identity_all_arms": True,
            "immutable_batch_contract_all_rows": True,
            "shadow_noninterference_all_updates": True,
            "exact_loss_gradient_routes": True,
            "label_firewall": True,
            "common_evaluation_panels": True,
            "train_evaluation_clone_overlap": False,
            "paired_rng_draw_counts": True,
            "finite_logits": True,
        }.items()
    )
    if result.get("runtime_contract") != expected_runtime:
        issues.append("runtime contract projection differs from retained evidence")
    return {
        "activity": derived_activity,
        "activity_valid": activity_valid,
        "support_valid": support_valid,
        "runtime_valid": runtime_valid,
        "aggregates": aggregates,
        "runtime_contract": expected_runtime,
    }, issues


def validate_result(
    manifest: object,
    result: object,
    *,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    issues = list(validate_manifest(manifest))
    if not isinstance(manifest, Mapping) or not isinstance(result, Mapping):
        return tuple(issues + ["manifest/result must be objects"])
    if result.get("artifact_kind") != "vsp02_b2_result":
        issues.append("result artifact kind mismatch")
    if result.get("assignment_id") != B2_ASSIGNMENT_ID or result.get("candidate") != B2_CANDIDATE:
        issues.append("result identity mismatch")
    if result.get("manifest") != manifest or result.get("manifest_identity") != manifest_identity(manifest):
        issues.append("result manifest binding mismatch")
    if result.get("branch") not in B2_BRANCH_PRECEDENCE:
        issues.append("unknown B2 branch")
        return tuple(issues)
    preflight = result.get("preflight")
    if not isinstance(preflight, Mapping):
        return tuple(issues + ["preflight evidence missing"])
    issues.extend(validate_preflight_evidence(manifest, preflight))
    if result["branch"] == "B2_NO_CONSTRUCTION":
        if preflight.get("all_passed") is not False:
            issues.append("no-construction branch lacks a failed preflight")
        if result.get("activity") != _zero_activity():
            issues.append("no-construction branch has result-bearing activity")
        if result.get("units") != [] or result.get("aggregates") is not None:
            issues.append("no-construction branch retained runtime evidence")
        return tuple(issues)

    if manifest.get("technical_only") is not False or manifest.get("result_bearing_runs") != 1:
        issues.append("post-preflight branch requires technical_only=false registered manifest")
        return tuple(issues)
    if preflight.get("all_passed") is not True:
        issues.append("runtime branch follows a failed preflight")
    derived, runtime_issues = _derive_runtime_result(result)
    issues.extend(runtime_issues)
    expected_branch = classify_b2(
        preflight_valid=True,
        runtime_valid=bool(derived.get("runtime_valid")),
        activity_valid=bool(derived.get("activity_valid")) and bool(derived.get("support_valid")),
        aggregates=derived.get("aggregates") if isinstance(derived.get("aggregates"), Mapping) else None,  # type: ignore[arg-type]
    )
    if result.get("branch") != expected_branch:
        issues.append(f"branch precedence mismatch: expected {expected_branch}")
    if runtime_issues:
        return tuple(issues)
    if repo_root is None:
        issues.append("post-preflight retained validation requires source-binding repo_root")
        return tuple(issues)
    issues.extend(_git_binding(repo_root, str(manifest["source_revision"])))
    return tuple(issues)


def validate_preflight_evidence(
    manifest: Mapping[str, object], preflight: Mapping[str, object]
) -> tuple[str, ...]:
    issues: list[str] = []
    if preflight.get("artifact_kind") != "vsp02_b2_preflight":
        issues.append("preflight artifact kind mismatch")
    if preflight.get("assignment_id") != B2_ASSIGNMENT_ID:
        issues.append("preflight assignment mismatch")
    if preflight.get("manifest_identity") != manifest_identity(manifest):
        issues.append("preflight manifest identity mismatch")
    gates = preflight.get("gates")
    if not isinstance(gates, Mapping) or tuple(sorted(gates)) != tuple(f"P{i}" for i in range(9)):
        issues.append("P0-P8 preflight gate set mismatch")
    else:
        passed_values: list[bool] = []
        for gate in (f"P{i}" for i in range(9)):
            evidence = gates[gate]
            if not isinstance(evidence, Mapping):
                issues.append(f"{gate} evidence is not an object")
                continue
            gate_issues = evidence.get("issues")
            if not isinstance(gate_issues, list):
                issues.append(f"{gate} issue list missing")
                continue
            expected_passed = not gate_issues
            if evidence.get("passed") is not expected_passed:
                issues.append(f"{gate} passed flag contradicts its issue list")
            passed_values.append(expected_passed)
        if preflight.get("all_passed") is not all(passed_values):
            issues.append("preflight all_passed contradicts P0-P8")

    seeds = preflight.get("rng")
    if not isinstance(seeds, Mapping) or seeds != seed_report():
        issues.append("RNG derivation/collision evidence mismatch")
    parameter_hashes = preflight.get("initial_parameter_hashes")
    optimizer_hashes = preflight.get("initial_optimizer_hashes")
    expected_initial = _expected_initial_evidence(*B2_UNITS[0])
    if parameter_hashes != expected_initial["parameter_hashes"]:
        issues.append("P2 parameter equality evidence mismatch")
    if optimizer_hashes != expected_initial["optimizer_hashes"]:
        issues.append("P2 optimizer equality evidence mismatch")
    architectures = preflight.get("architecture")
    optimizer_contracts = preflight.get("optimizer_contracts")
    if architectures != expected_initial["architecture"]:
        issues.append("P2 architecture equality evidence mismatch")
    if optimizer_contracts != expected_initial["optimizer_contracts"]:
        issues.append("P2 optimizer contract evidence mismatch")

    p3 = preflight.get("p3_noninterference")
    if not isinstance(p3, Mapping):
        issues.append("P3 evidence missing")
    else:
        if p3.get("before") != p3.get("after") or p3.get("hash_identity") is not True:
            issues.append("P3 pre/post hash identity mismatch")
        if p3.get("batch_read_only") is not True:
            issues.append("P3 immutable batch mismatch")
        expected_zero = {
            "roots": 0,
            "arms": 0,
            "host_resets": 0,
            "episodes": 0,
            "environment_transitions": 0,
            "optimizer_updates": 0,
            "checkpoints": 0,
            "rng_draws": 0,
        }
        if p3.get("activity") != expected_zero:
            issues.append("P3 proof fixture created forbidden activity")
        if p3.get("rl_actor_advantage_detached_from_critic_head") is not True:
            issues.append("P4 stop-gradient evidence mismatch")
        if p3.get("supervised_actor_has_no_critic_head_route") is not True:
            issues.append("P4 supervised actor route evidence mismatch")
        if p3.get("rl_label_argument_surface") != []:
            issues.append("P4/P5 RL label firewall mismatch")
        if p3.get("supervised_original_actor_term_count") != 0:
            issues.append("P4 supervised actor replacement mismatch")

    if preflight.get("label_firewall") is not True:
        issues.append("P5 label firewall evidence mismatch")
    schedules = preflight.get("balanced_schedules")
    if not isinstance(schedules, Mapping) or schedules != {unit: True for unit, _ in B2_UNITS}:
        issues.append("P6 balanced schedule evidence mismatch")
    evaluator = preflight.get("evaluator_sentinels")
    if not isinstance(evaluator, Mapping) or evaluator != _evaluator_sentinels():
        issues.append("P7 evaluator sentinel evidence mismatch")
    activity = preflight.get("activity")
    if activity != {
        "result_bearing_runs": 0,
        "host_resets": 0,
        "episodes": 0,
        "environment_transitions": 0,
        "optimizer_updates": 0,
        "checkpoints": 0,
    }:
        issues.append("preflight created result-bearing activity")
    return tuple(issues)

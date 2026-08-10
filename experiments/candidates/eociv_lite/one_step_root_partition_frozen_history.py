"""EOCIV-B7 one-step root-partition discriminator at frozen histories.

The treatment changes only how one immutable 4x4 root-by-shock panel is split
into four ordinary four-episode Adam updates.  Every branch starts from the
same retained actor, optimizer, counter, normalization and RNG anchor.  The
module deliberately reuses the real EOCIV sibling host and verified receipt
path, but owns fresh B7 roots, tapes, state and artifacts.

No registered run is started by importing this module.  The artifact lifecycle
is explicit and one-shot: claim -> train -> evaluate -> analyze -> validate.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import torch
from torch import nn

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import actuation_runtime as art
from experiments.candidates.eociv_lite import host_reward_snr_discrimination as host
from experiments.candidates.eociv_lite import payload_content_learnability as payload
from experiments.candidates.eociv_lite import real_valve_learning as learner
from experiments.candidates.eociv_lite import recurrent_retention_learnability as retention
from experiments.candidates.eociv_lite import sibling_env as sibling


TREATMENT = "EOCIV-B7-ONE-STEP-ROOT-PARTITION-FROZEN-HISTORY-DISCRIMINATOR"
DIRECTION = "CAND-VAP-EOCIV-LITE@adversarial-revision-v8"
RAW_OUTPUT_BINDING = "eociv_lite.one_step_root_partition_frozen_history.v1"
STAGE = "B_EXPLORATORY_REAL_TOY_EXPERIMENT"

INITIALIZATION_SEED = 91030
HISTORY_IDS = ("H0", "H1", "H2")
HISTORY_SEEDS = {"H0": 91031, "H1": 91032, "H2": 91033}
HISTORY_ACTION_TAPES = {"H0": 91101, "H1": 91102, "H2": 91103}
HISTORY_ORDER_TAPES = {"H0": 91201, "H1": 91202, "H2": 91203}
PREFIX_ROOTS = tuple(range(910101, 910109))

PROFILE_NAMES = ("train_4_3_6_5", "train_5_3_7_6", "train_6_4_8_6")
PROFILE_BY_NAME = {profile.name: profile for profile in learner.PROFILES}
if tuple(PROFILE_BY_NAME) != PROFILE_NAMES:
    raise RuntimeError("B7 registered profile order is unavailable or drifted")

SHOCK_TUPLES = (
    (sibling.SHOCK_A, sibling.SHOCK_A),
    (sibling.SHOCK_A, sibling.SHOCK_B),
    (sibling.SHOCK_B, sibling.SHOCK_A),
    (sibling.SHOCK_B, sibling.SHOCK_B),
)
EVALUATION_ARMS = ("CORRECT", "SWAPPED")
PARTITIONS = ("ROOT_CLUSTERED", "ROOT_STRATIFIED_LATIN")
LATIN_ROOT_ROWS = (
    (0, 1, 2, 3),
    (1, 2, 3, 0),
    (2, 3, 0, 1),
    (3, 0, 1, 2),
)

PANEL_ROOTS: Mapping[tuple[str, str], tuple[int, ...]] = {
    ("H0", "train_4_3_6_5"): (920101, 920102, 920103, 920104),
    ("H0", "train_5_3_7_6"): (920111, 920112, 920113, 920114),
    ("H0", "train_6_4_8_6"): (920121, 920122, 920123, 920124),
    ("H1", "train_4_3_6_5"): (921101, 921102, 921103, 921104),
    ("H1", "train_5_3_7_6"): (921111, 921112, 921113, 921114),
    ("H1", "train_6_4_8_6"): (921121, 921122, 921123, 921124),
    ("H2", "train_4_3_6_5"): (922101, 922102, 922103, 922104),
    ("H2", "train_5_3_7_6"): (922111, 922112, 922113, 922114),
    ("H2", "train_6_4_8_6"): (922121, 922122, 922123, 922124),
}
PANEL_ACTION_TAPES: Mapping[tuple[str, str], int] = {
    ("H0", "train_4_3_6_5"): 940101,
    ("H0", "train_5_3_7_6"): 940111,
    ("H0", "train_6_4_8_6"): 940121,
    ("H1", "train_4_3_6_5"): 941101,
    ("H1", "train_5_3_7_6"): 941111,
    ("H1", "train_6_4_8_6"): 941121,
    ("H2", "train_4_3_6_5"): 942101,
    ("H2", "train_5_3_7_6"): 942111,
    ("H2", "train_6_4_8_6"): 942121,
}
EVALUATION_ROOTS: Mapping[tuple[str, str], tuple[int, ...]] = {
    ("H0", "train_4_3_6_5"): (930101, 930102, 930103),
    ("H0", "train_5_3_7_6"): (930111, 930112, 930113),
    ("H0", "train_6_4_8_6"): (930121, 930122, 930123),
    ("H1", "train_4_3_6_5"): (931101, 931102, 931103),
    ("H1", "train_5_3_7_6"): (931111, 931112, 931113),
    ("H1", "train_6_4_8_6"): (931121, 931122, 931123),
    ("H2", "train_4_3_6_5"): (932101, 932102, 932103),
    ("H2", "train_5_3_7_6"): (932111, 932112, 932113),
    ("H2", "train_6_4_8_6"): (932121, 932122, 932123),
}

HORIZON = 48
GAMMA = 0.99
GAE_LAMBDA = 0.95
NORMALIZATION_EPSILON = 1e-8
ADAM_LR = 3e-4
GLOBAL_CLIP_CAP = 0.5

_DEPENDENCY_LITERALS = {
    "horizon": int(roster_env.HORIZON),
    "gamma": float(learner.GAMMA),
    "gae_lambda": float(host.GAE_LAMBDA),
    "normalization_epsilon": float(host.NORMALIZATION_EPSILON),
    "adam_lr": float(learner.ACTOR_LR),
    "global_clip_cap": float(learner.GRAD_NORM_CAP),
}
if _DEPENDENCY_LITERALS != {
    "horizon": HORIZON,
    "gamma": GAMMA,
    "gae_lambda": GAE_LAMBDA,
    "normalization_epsilon": NORMALIZATION_EPSILON,
    "adam_lr": ADAM_LR,
    "global_clip_cap": GLOBAL_CLIP_CAP,
}:
    raise RuntimeError(f"B7 protected learner/host literal drift: {_DEPENDENCY_LITERALS}")
if not set(EVALUATION_ARMS) <= set(payload.BODY_RULES):
    raise RuntimeError("B7 registered evaluation arm body rules are unavailable")

FULL_EXPECTED_COUNTS = {
    "unique_complete_episodes": 918,
    "environment_transitions": 44_064,
    "policy_calls": 44_064,
    "prefix_episodes": 288,
    "common_data_collection_episodes": 144,
    "evaluation_episodes": 486,
    "physical_trajectory_references": 288,
    "learner_batch_episode_references": 576,
    "learner_calls": 144,
    "trainer_calls": 144,
    "optimizer_updates": 144,
    "clip_calls": 144,
    "retry": 0,
    "rescue": 0,
    "sweep": 0,
    "checkpoint_selection": 0,
}

TERMINAL_BRANCHES = (
    "B7_INVALID_OR_UNIDENTIFIED",
    "B7_ROOT_SEMANTIC_EDGE",
    "B7_GENERIC_OPTIMIZATION_ONLY",
    "B7_ROOT_LOCAL_NULL",
    "B7_HISTORY_MODERATED_OR_JOINT",
)


@dataclass(frozen=True)
class ExecutionPlan:
    technical_only: bool
    histories: tuple[str, ...]
    profiles: tuple[str, ...]
    prefix_roots: tuple[int, ...]
    panel_root_count: int
    evaluation_root_count: int

    @property
    def cells(self) -> int:
        return len(self.histories) * len(self.profiles)

    @property
    def prefix_episodes(self) -> int:
        return len(self.histories) * len(self.prefix_roots) * len(self.profiles) * 4

    @property
    def common_episodes(self) -> int:
        return self.cells * self.panel_root_count * 4

    @property
    def evaluation_episodes(self) -> int:
        return self.cells * self.evaluation_root_count * 9 * 2

    @property
    def optimizer_updates(self) -> int:
        return len(self.histories) * len(self.prefix_roots) * len(self.profiles) + self.cells * 8

    @property
    def expected_counts(self) -> dict[str, int]:
        episodes = self.prefix_episodes + self.common_episodes + self.evaluation_episodes
        physical_references = self.cells * 8 * 4
        return {
            "unique_complete_episodes": episodes,
            "environment_transitions": episodes * HORIZON,
            "policy_calls": episodes * HORIZON,
            "prefix_episodes": self.prefix_episodes,
            "common_data_collection_episodes": self.common_episodes,
            "evaluation_episodes": self.evaluation_episodes,
            "physical_trajectory_references": physical_references,
            "learner_batch_episode_references": physical_references * 2,
            "learner_calls": self.optimizer_updates,
            "trainer_calls": self.optimizer_updates,
            "optimizer_updates": self.optimizer_updates,
            "clip_calls": self.optimizer_updates,
            "retry": 0,
            "rescue": 0,
            "sweep": 0,
            "checkpoint_selection": 0,
        }


FULL_PLAN = ExecutionPlan(False, HISTORY_IDS, PROFILE_NAMES, PREFIX_ROOTS, 4, 3)
TECHNICAL_PLAN = ExecutionPlan(True, HISTORY_IDS[:1], PROFILE_NAMES[:1], PREFIX_ROOTS[:1], 4, 1)


def plan_for(technical_only: bool) -> ExecutionPlan:
    return TECHNICAL_PLAN if technical_only else FULL_PLAN


def _empty_counts() -> dict[str, int]:
    return {key: 0 for key in FULL_EXPECTED_COUNTS}


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _digest_bytes(*values: bytes) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(len(value).to_bytes(8, "little"))
        digest.update(value)
    return digest.hexdigest()


def _tensor_digest(tensors: Iterable[torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for tensor in tensors:
        value = tensor.detach().cpu().contiguous()
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(_json_bytes(tuple(value.shape)))
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def _state_dict_digest(state: Mapping[str, torch.Tensor]) -> str:
    return _digest_bytes(
        *(
            name.encode("utf-8") + b"\0" + tensor.detach().cpu().contiguous().numpy().tobytes()
            for name, tensor in state.items()
        )
    )


def _optimizer_digest(state: Mapping[str, Any]) -> str:
    pieces: list[bytes] = []
    for group in state["param_groups"]:
        pieces.append(_json_bytes({key: value for key, value in group.items() if key != "params"}))
        pieces.append(_json_bytes(tuple(group["params"])))
    for parameter_id in sorted(state["state"]):
        pieces.append(str(parameter_id).encode("ascii"))
        for key, value in sorted(state["state"][parameter_id].items()):
            pieces.append(key.encode("ascii"))
            if isinstance(value, torch.Tensor):
                pieces.append(value.detach().cpu().contiguous().numpy().tobytes())
            else:
                pieces.append(_json_bytes(value))
    return _digest_bytes(*pieces)


def _rng_snapshot() -> dict[str, Any]:
    numpy_state = np.random.get_state()
    return {
        "python_state": random.getstate(),
        "numpy_state": (
            numpy_state[0],
            numpy_state[1].copy(),
            int(numpy_state[2]),
            int(numpy_state[3]),
            float(numpy_state[4]),
        ),
        "torch_cpu_state": torch.random.get_rng_state().clone(),
    }


def _rng_digest(state: Mapping[str, Any]) -> str:
    numpy_state = state["numpy_state"]
    return _digest_bytes(
        repr(state["python_state"]).encode("utf-8"),
        str(numpy_state[0]).encode("ascii"),
        np.asarray(numpy_state[1], dtype=np.uint32).tobytes(),
        _json_bytes(numpy_state[2:]),
        state["torch_cpu_state"].detach().cpu().numpy().tobytes(),
    )


def _anchor_rng_digest(global_state: Mapping[str, Any], order_tape_state: Mapping[str, Any]) -> str:
    return _digest_bytes(
        _rng_digest(global_state).encode("ascii"),
        _json_bytes(order_tape_state),
    )


def _structural_manifest(actor: learner.RecurrentActorCritic, optimizer: torch.optim.Optimizer) -> dict[str, Any]:
    names = list(actor.named_parameters())
    id_to_name = {id(parameter): name for name, parameter in names}
    return {
        "model_class": f"{type(actor).__module__}.{type(actor).__qualname__}",
        "policy_condition": "SEGMENT_LATCH_RNN",
        "parameter_order": [name for name, _ in names],
        "parameter_shapes": {name: list(parameter.shape) for name, parameter in names},
        "parameter_dtypes": {name: str(parameter.dtype) for name, parameter in names},
        "optimizer_class": f"{type(optimizer).__module__}.{type(optimizer).__qualname__}",
        "optimizer_parameter_groups": [
            {
                "parameter_names": [id_to_name[id(parameter)] for parameter in group["params"]],
                "lr": float(group["lr"]),
                "betas": [float(value) for value in group["betas"]],
                "eps": float(group["eps"]),
                "weight_decay": float(group["weight_decay"]),
                "amsgrad": bool(group["amsgrad"]),
            }
            for group in optimizer.param_groups
        ],
        "normalization": {
            "kind": "episode_local_normalized_terminal_gae",
            "gamma": GAMMA,
            "lambda": GAE_LAMBDA,
            "epsilon": NORMALIZATION_EPSILON,
            "running_state": None,
        },
        "gradient_rule": "actor_mean_plus_half_scaled_critic_mean",
        "clip_rule": "JOINT_GLOBAL_CLIP",
        "clip_cap": GLOBAL_CLIP_CAP,
    }


def _new_actor() -> learner.RecurrentActorCritic:
    return learner.RecurrentActorCritic(
        PROFILE_BY_NAME[PROFILE_NAMES[0]].member_capacity,
        INITIALIZATION_SEED,
        encoder_kind="content_separating",
    )


def _new_actor_optimizer(
    actor_state: Mapping[str, torch.Tensor] | None = None,
    optimizer_state: Mapping[str, Any] | None = None,
) -> tuple[learner.RecurrentActorCritic, torch.optim.Adam]:
    actor = _new_actor()
    if actor_state is not None:
        actor.load_state_dict(actor_state, strict=True)
    optimizer = torch.optim.Adam(actor.parameters(), lr=ADAM_LR)
    if optimizer_state is not None:
        optimizer.load_state_dict(copy.deepcopy(optimizer_state))
    return actor, optimizer


class RecordingRetentionPolicy(retention.RetentionPolicy):
    """Retention policy that records the exact immutable learner inputs."""

    def forward(
        self,
        observations: np.ndarray,
        active_mask: np.ndarray,
        external_slot_block: np.ndarray,
        hidden: np.ndarray,
        noise: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        result = super().forward(observations, active_mask, external_slot_block, hidden, noise)
        self.steps[-1]["observations"] = np.asarray(observations, dtype=np.float64).copy()
        self.steps[-1]["input_hidden"] = np.asarray(hidden, dtype=np.float32).copy()
        return result


def _make_env(
    profile: roster_env.RosterProfile,
    root_id: int,
    shock_tuple: tuple[str, str] | None,
    *,
    shock_seed: int,
) -> sibling.EocivSiblingRosterEnv:
    world_seed = sibling.profile_stream_identity(sibling.BASE_WORLD_STREAM, learner.MASTER_SEED, profile.name)
    ledger = roster_env.make_ledger(root_id, master_seed=world_seed, profile=profile)
    shocks = None if shock_tuple is None else (shock_tuple[0], sibling.SHOCK_NONE, shock_tuple[1])
    return sibling.EocivSiblingRosterEnv(ledger, sibling_seed=shock_seed, shock_states=shocks)


def _make_runner(
    actor: learner.RecurrentActorCritic,
    profile: roster_env.RosterProfile,
    root_id: int,
    body_fn,
    shock_tuple: tuple[str, str] | None,
    *,
    shock_seed: int,
    action_noise_seed: int,
) -> retention.RetentionEpisodeRunner:
    env = _make_env(profile, root_id, shock_tuple, shock_seed=shock_seed)
    policy = RecordingRetentionPolicy(actor, "SEGMENT_LATCH_RNN")
    runner = retention.RetentionEpisodeRunner(
        env,
        "LR",
        tape_seed=learner.TAPE_SEED,
        d_learned_fn=lambda _: True,
        body_fn=body_fn,
        policy=policy,
    )
    runner.action_noise_seed_identity = sibling.profile_stream_identity(
        sibling.ACTION_NOISE_STREAM, action_noise_seed, profile.name
    )
    runner.noise = roster_env.make_action_noise(
        [root_id],
        action_seed=runner.action_noise_seed_identity,
        member_capacity=profile.member_capacity,
    )[:, 0, :, :]
    runner.run_episode()
    return runner


def _trajectory_from_runner(
    runner: retention.RetentionEpisodeRunner,
    *,
    history_id: str,
    profile_name: str,
    root_id: int,
    shock_index: int,
    shock_tuple: tuple[str, str],
    action_noise_seed: int,
) -> dict[str, Any]:
    if len(runner.policy.steps) != HORIZON or len(runner.env.reward_trace) != HORIZON:
        raise RuntimeError("B7 frozen trajectory is not complete")
    steps = tuple(
        {
            "observations": np.asarray(step["observations"], dtype=np.float64).copy(),
            "active_mask": np.asarray(step["active_mask"], dtype=np.bool_).copy(),
            "effective_slot_block": np.asarray(step["effective_slot_block"], dtype=np.float32).copy(),
            "noise": np.asarray(step["noise"], dtype=np.float32).copy(),
            "sampled_action": np.asarray(step["sampled_action"], dtype=np.float32).copy(),
            "action_kernel": np.asarray(step["action_kernel"], dtype=np.float32).copy(),
            "reward": float(step["reward"]),
        }
        for step in runner.policy.steps
    )
    digest = _digest_bytes(
        *(
            np.ascontiguousarray(step[key]).tobytes()
            for step in steps
            for key in ("observations", "active_mask", "effective_slot_block", "noise", "sampled_action", "action_kernel")
        ),
        np.asarray([step["reward"] for step in steps], dtype=np.float64).tobytes(),
    )
    return {
        "trajectory_key": f"{history_id}|{profile_name}|{root_id}|{shock_index}",
        "history": history_id,
        "profile": profile_name,
        "root_id": root_id,
        "shock_index": shock_index,
        "critical_shock_tuple": shock_tuple,
        "full_shock_tuple": (shock_tuple[0], sibling.SHOCK_NONE, shock_tuple[1]),
        "action_noise_seed": action_noise_seed,
        "public_world_digest": host.public_world_digest(runner.env),
        "lifecycle_digest": host.lifecycle_digest(runner),
        "action_noise_tape_digest": host.action_noise_digest(runner),
        "receipt_digests": tuple(record.receipt.slot_digest for record in runner.boundary_records),
        "accepted_boundary_ticks": tuple(runner.accepted_boundary_ticks),
        "latch_started_zero": bool(runner.policy.started_zero),
        "latch_ended_zero": bool(runner.policy.ended_zero),
        "trajectory_digest": digest,
        "episode_return": float(sum(runner.env.reward_trace)),
        "steps": steps,
    }


def _replay_losses(
    actor: learner.RecurrentActorCritic,
    trajectory: Mapping[str, Any],
) -> tuple[torch.Tensor, torch.Tensor, dict[str, float]]:
    actor.set_capture(True)
    hidden = actor.initial_state()
    for step in trajectory["steps"]:
        action, kernel, hidden = actor.forward(
            step["observations"],
            step["active_mask"],
            step["effective_slot_block"],
            hidden,
            step["noise"],
        )
        if not np.array_equal(action, step["sampled_action"]):
            raise RuntimeError("B7 frozen sampled action did not replay byte-exactly")
        if not np.array_equal(kernel, step["action_kernel"]):
            raise RuntimeError("B7 frozen action kernel did not replay byte-exactly")
    actor_loss, critic_loss, diagnostics = host._episode_loss_tensors(
        actor, [float(step["reward"]) for step in trajectory["steps"]]
    )
    actor.set_capture(False)
    return actor_loss, critic_loss, diagnostics


def _flat_gradients(
    losses: torch.Tensor,
    parameters: Sequence[nn.Parameter],
    *,
    retain_graph: bool,
) -> torch.Tensor:
    gradients = torch.autograd.grad(losses, parameters, retain_graph=retain_graph, allow_unused=True)
    return torch.cat(
        tuple(
            torch.zeros_like(parameter).reshape(-1)
            if gradient is None
            else gradient.detach().reshape(-1)
            for parameter, gradient in zip(parameters, gradients)
        )
    )


def _flatten_parameter_values(parameters: Sequence[nn.Parameter]) -> torch.Tensor:
    return torch.cat(tuple(parameter.detach().reshape(-1).clone() for parameter in parameters))


def _flatten_parameter_grads(parameters: Sequence[nn.Parameter]) -> torch.Tensor:
    return torch.cat(
        tuple(
            torch.zeros_like(parameter).reshape(-1)
            if parameter.grad is None
            else parameter.grad.detach().reshape(-1).clone()
            for parameter in parameters
        )
    )


def _run_one_update(
    actor: learner.RecurrentActorCritic,
    optimizer: torch.optim.Adam,
    trajectories: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if len(trajectories) != 4:
        raise ValueError("B7 ordinary update requires exactly four frozen trajectories")
    parameters = tuple(actor.parameters())
    actor_losses: list[torch.Tensor] = []
    critic_losses: list[torch.Tensor] = []
    diagnostics: list[dict[str, float]] = []
    optimizer.zero_grad(set_to_none=True)
    for trajectory in trajectories:
        actor_loss, critic_loss, row = _replay_losses(actor, trajectory)
        actor_losses.append(actor_loss)
        critic_losses.append(critic_loss)
        diagnostics.append(row)
    actor_mean = torch.stack(actor_losses).mean()
    half_critic_mean = 0.5 * torch.stack(critic_losses).mean()
    total_loss = actor_mean + half_critic_mean
    actor_gradient = _flat_gradients(actor_mean, parameters, retain_graph=True)
    critic_gradient = _flat_gradients(half_critic_mean, parameters, retain_graph=True)
    joint_gradient = actor_gradient + critic_gradient
    optimizer.zero_grad(set_to_none=True)
    total_loss.backward()
    observed_gradient = _flatten_parameter_grads(parameters)
    grad_delta = torch.abs(observed_gradient - joint_gradient)
    preserved_dot_grad = observed_gradient.clone()
    exact_grad = bool(torch.equal(observed_gradient, preserved_dot_grad))
    component_exact = bool(torch.equal(observed_gradient, joint_gradient))
    component_close = bool(torch.allclose(observed_gradient, joint_gradient, rtol=1e-6, atol=1e-7))
    actor_norm = float(torch.linalg.vector_norm(actor_gradient.double()))
    critic_norm = float(torch.linalg.vector_norm(critic_gradient.double()))
    joint_norm = float(torch.linalg.vector_norm(joint_gradient.double()))
    actor_critic_dot = float(torch.dot(actor_gradient.double(), critic_gradient.double()))
    expected_scale = min(1.0, GLOBAL_CLIP_CAP / max(joint_norm, 1e-30))
    before_values = _flatten_parameter_values(parameters)
    before_optimizer = copy.deepcopy(optimizer.state_dict())
    returned_norm = float(nn.utils.clip_grad_norm_(parameters, GLOBAL_CLIP_CAP))
    clipped_gradient = _flatten_parameter_grads(parameters)
    clip_fidelity = bool(
        torch.allclose(clipped_gradient, joint_gradient * expected_scale, rtol=2e-6, atol=2e-7)
    )
    optimizer.step()
    after_values = _flatten_parameter_values(parameters)
    after_optimizer = copy.deepcopy(optimizer.state_dict())
    delta = after_values - before_values
    finite = bool(
        np.isfinite(
            np.asarray(
                [
                    float(actor_mean.detach()),
                    float(half_critic_mean.detach()),
                    float(total_loss.detach()),
                    actor_norm,
                    critic_norm,
                    joint_norm,
                    actor_critic_dot,
                    returned_norm,
                    float(torch.linalg.vector_norm(delta.double())),
                    *[float(value) for row in diagnostics for value in row.values()],
                ],
                dtype=np.float64,
            )
        ).all()
    )
    actor_projection = float(torch.dot(delta.double(), actor_gradient.double()))
    joint_projection = float(torch.dot(delta.double(), joint_gradient.double()))
    return {
        "trajectory_keys": [str(value["trajectory_key"]) for value in trajectories],
        "trajectory_digests": [str(value["trajectory_digest"]) for value in trajectories],
        "actor_loss": float(actor_mean.detach()),
        "half_scaled_critic_loss": float(half_critic_mean.detach()),
        "joint_loss": float(total_loss.detach()),
        "pre_step_actor_gradient_norm": actor_norm,
        "pre_step_half_scaled_critic_gradient_norm": critic_norm,
        "pre_step_joint_gradient_norm": joint_norm,
        "pre_step_actor_critic_dot": actor_critic_dot,
        "joint_clip_scale": expected_scale,
        "clip_returned_pre_norm": returned_norm,
        "exact_grad_fidelity": exact_grad,
        "grad_component_sum_exact": component_exact,
        "grad_component_sum_allclose": component_close,
        "grad_fidelity_max_abs": float(grad_delta.max()) if grad_delta.numel() else 0.0,
        "clip_fidelity": clip_fidelity,
        "pre_step_gradient_digest": _tensor_digest((observed_gradient,)),
        "post_clip_gradient_digest": _tensor_digest((clipped_gradient,)),
        "pre_step_optimizer_digest": _optimizer_digest(before_optimizer),
        "post_step_optimizer_digest": _optimizer_digest(after_optimizer),
        "one_step_adam_delta_norm": float(torch.linalg.vector_norm(delta.double())),
        "one_step_adam_delta_digest": _tensor_digest((delta,)),
        "one_step_adam_actor_projection": actor_projection,
        "one_step_adam_joint_projection": joint_projection,
        "finite_value_diagnostics": finite,
        "value_diagnostics": diagnostics,
        "optimizer_steps": 1,
        "clip_calls": 1,
    }


def partition_indices(partition: str, branch_index: int) -> tuple[int, ...]:
    if partition not in PARTITIONS or branch_index not in range(4):
        raise ValueError("unregistered B7 partition coordinate")
    if partition == "ROOT_CLUSTERED":
        return tuple(branch_index * 4 + shock for shock in range(4))
    roots = LATIN_ROOT_ROWS[branch_index]
    return tuple(roots[shock] * 4 + shock for shock in range(4))


def partition_witness() -> dict[str, Any]:
    clustered = tuple(partition_indices("ROOT_CLUSTERED", branch) for branch in range(4))
    latin = tuple(partition_indices("ROOT_STRATIFIED_LATIN", branch) for branch in range(4))
    expected = list(range(16))
    return {
        "clustered_rows": [list(row) for row in clustered],
        "latin_rows": [list(row) for row in latin],
        "clustered_exact_cover": sorted(value for row in clustered for value in row) == expected,
        "latin_exact_cover": sorted(value for row in latin for value in row) == expected,
        "same_information_multiset": sorted(value for row in clustered for value in row)
        == sorted(value for row in latin for value in row),
        "four_episodes_per_branch": all(len(row) == 4 for row in (*clustered, *latin)),
    }


def _history_prefix_episode_id(history_id: str, root: int, profile_index: int) -> int:
    # History seed/tape and profile stream provide the namespaces.  The ledger
    # root itself remains the exact registered prefix root in every history and
    # profile; it is never rewritten into a synthetic compound identifier.
    if history_id not in HISTORY_IDS or profile_index not in range(len(PROFILE_NAMES)):
        raise ValueError("unregistered B7 prefix coordinate")
    if root not in PREFIX_ROOTS:
        raise ValueError("unregistered B7 prefix root")
    return int(root)


def _collect_trajectory(
    actor: learner.RecurrentActorCritic,
    history_id: str,
    profile_name: str,
    root_id: int,
    shock_index: int,
    shock_tuple: tuple[str, str],
    *,
    shock_seed: int,
    action_noise_seed: int,
    counts: dict[str, int],
    count_kind: str,
) -> dict[str, Any]:
    runner = _make_runner(
        actor,
        PROFILE_BY_NAME[profile_name],
        root_id,
        payload._correct_body,
        shock_tuple,
        shock_seed=shock_seed,
        action_noise_seed=action_noise_seed,
    )
    counts["unique_complete_episodes"] += 1
    counts["environment_transitions"] += HORIZON
    counts["policy_calls"] += HORIZON
    counts[count_kind] += 1
    return _trajectory_from_runner(
        runner,
        history_id=history_id,
        profile_name=profile_name,
        root_id=root_id,
        shock_index=shock_index,
        shock_tuple=shock_tuple,
        action_noise_seed=action_noise_seed,
    )


def _train_histories(plan: ExecutionPlan, counts: dict[str, int]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    initial_actor, initial_optimizer = _new_actor_optimizer()
    initial_actor_state = copy.deepcopy(initial_actor.state_dict())
    initial_optimizer_state = copy.deepcopy(initial_optimizer.state_dict())
    shared_initial_digest = _state_dict_digest(initial_actor_state)
    structural = _structural_manifest(initial_actor, initial_optimizer)
    histories: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    for history_id in plan.histories:
        actor, optimizer = _new_actor_optimizer(initial_actor_state, initial_optimizer_state)
        start_rng = _rng_snapshot()
        order_rng = np.random.default_rng(HISTORY_ORDER_TAPES[history_id])
        order_rng_start_state = copy.deepcopy(order_rng.bit_generator.state)
        update_index = 0
        for root in plan.prefix_roots:
            for profile_index, profile_name in enumerate(plan.profiles):
                trajectories = [
                    _collect_trajectory(
                        actor,
                        history_id,
                        profile_name,
                        _history_prefix_episode_id(history_id, root, profile_index),
                        shock_index,
                        shock_tuple,
                        shock_seed=HISTORY_SEEDS[history_id],
                        action_noise_seed=HISTORY_ACTION_TAPES[history_id],
                        counts=counts,
                        count_kind="prefix_episodes",
                    )
                    for shock_index, shock_tuple in enumerate(SHOCK_TUPLES)
                ]
                learner_order = tuple(int(value) for value in order_rng.permutation(4))
                update = _run_one_update(actor, optimizer, [trajectories[index] for index in learner_order])
                update_index += 1
                counts["learner_calls"] += 1
                counts["trainer_calls"] += 1
                counts["optimizer_updates"] += 1
                counts["clip_calls"] += 1
                rows.append(
                    {
                        "history": history_id,
                        "history_seed": HISTORY_SEEDS[history_id],
                        "history_action_noise_tape": HISTORY_ACTION_TAPES[history_id],
                        "history_order_tape": HISTORY_ORDER_TAPES[history_id],
                        "prefix_root": root,
                        "profile": profile_name,
                        "update_index": update_index,
                        "shock_order": [list(value) for value in SHOCK_TUPLES],
                        "learner_order_tape_permutation": list(learner_order),
                        "order_tape_binding_digest": hashlib.sha256(
                            f"{HISTORY_ORDER_TAPES[history_id]}|{root}|{profile_name}|{learner_order}".encode("ascii")
                        ).hexdigest(),
                        "update": update,
                    }
                )
        end_rng = _rng_snapshot()
        histories[history_id] = {
            "history": history_id,
            "history_seed": HISTORY_SEEDS[history_id],
            "action_noise_tape": HISTORY_ACTION_TAPES[history_id],
            "order_tape": HISTORY_ORDER_TAPES[history_id],
            "initial_actor_digest": shared_initial_digest,
            "actor_state": copy.deepcopy(actor.state_dict()),
            "optimizer_state": copy.deepcopy(optimizer.state_dict()),
            "actor_digest": _state_dict_digest(actor.state_dict()),
            "optimizer_digest": _optimizer_digest(optimizer.state_dict()),
            "rng_state": end_rng,
            "rng_start_digest": _rng_digest(start_rng),
            "rng_end_digest": _rng_digest(end_rng),
            "order_tape_rng_start_state": order_rng_start_state,
            "order_tape_rng_end_state": copy.deepcopy(order_rng.bit_generator.state),
            "order_tape_rng_start_digest": hashlib.sha256(_json_bytes(order_rng_start_state)).hexdigest(),
            "order_tape_rng_end_digest": hashlib.sha256(
                _json_bytes(order_rng.bit_generator.state)
            ).hexdigest(),
            "trainer_counter": update_index,
            "sampler_episode_counter": update_index * 4,
            "normalization_state": structural["normalization"],
            "structural_manifest": structural,
        }
    return histories, rows


def _collect_panel(
    actor: learner.RecurrentActorCritic,
    history_id: str,
    profile_name: str,
    plan: ExecutionPlan,
    counts: dict[str, int],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    roots = PANEL_ROOTS[(history_id, profile_name)][: plan.panel_root_count]
    action_tape = PANEL_ACTION_TAPES[(history_id, profile_name)]
    before_actor = _state_dict_digest(actor.state_dict())
    before_rng = _rng_snapshot()
    trajectories: list[dict[str, Any]] = []
    for root in roots:
        for shock_index, shock_tuple in enumerate(SHOCK_TUPLES):
            trajectories.append(
                _collect_trajectory(
                    actor,
                    history_id,
                    profile_name,
                    root,
                    shock_index,
                    shock_tuple,
                    shock_seed=HISTORY_SEEDS[history_id],
                    action_noise_seed=action_tape,
                    counts=counts,
                    count_kind="common_data_collection_episodes",
                )
            )
    after_actor = _state_dict_digest(actor.state_dict())
    after_rng = _rng_snapshot()
    keys = [str(row["trajectory_key"]) for row in trajectories]
    root_groups: dict[int, list[dict[str, Any]]] = {
        root: [row for row in trajectories if int(row["root_id"]) == root] for root in roots
    }
    witness = {
        "history": history_id,
        "profile": profile_name,
        "panel_roots": list(roots),
        "action_noise_tape": action_tape,
        "trajectory_keys": keys,
        "trajectory_digests": [str(row["trajectory_digest"]) for row in trajectories],
        "exact_4x4_panel": len(trajectories) == plan.panel_root_count * 4,
        "unique_trajectory_keys": len(keys) == len(set(keys)),
        "shock_order_per_root": all(
            tuple(tuple(row["critical_shock_tuple"]) for row in root_groups[root]) == SHOCK_TUPLES
            for root in roots
        ),
        "same_public_world_within_root": all(
            len({str(row["public_world_digest"]) for row in root_groups[root]}) == 1 for root in roots
        ),
        "same_action_noise_within_root": all(
            len({str(row["action_noise_tape_digest"]) for row in root_groups[root]}) == 1 for root in roots
        ),
        "same_lifecycle_within_root": all(
            len({str(row["lifecycle_digest"]) for row in root_groups[root]}) == 1 for root in roots
        ),
        "legitimate_receipts": all(
            len(row["receipt_digests"]) == len(sibling.EVENT_TIMES)
            and tuple(row["accepted_boundary_ticks"]) == tuple(sibling.EVENT_TIMES)
            for row in trajectories
        ),
        "segment_latch_zero_boundaries": all(
            bool(row["latch_started_zero"]) and bool(row["latch_ended_zero"]) for row in trajectories
        ),
        "anchor_actor_immutable": before_actor == after_actor,
        "global_rng_immutable": _rng_digest(before_rng) == _rng_digest(after_rng),
    }
    return trajectories, witness


def _branch_cells(
    plan: ExecutionPlan,
    histories: Mapping[str, Any],
    counts: dict[str, int],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    retained: dict[str, Any] = {}
    panel_witnesses: list[dict[str, Any]] = []
    branch_rows: list[dict[str, Any]] = []
    for history_id in plan.histories:
        anchor = histories[history_id]
        for profile_name in plan.profiles:
            anchor_actor, anchor_optimizer = _new_actor_optimizer(anchor["actor_state"], anchor["optimizer_state"])
            panel, panel_witness = _collect_panel(anchor_actor, history_id, profile_name, plan, counts)
            panel_witnesses.append(panel_witness)
            cell_key = f"{history_id}|{profile_name}"
            endpoints: dict[str, Any] = {}
            clone_actor_digests: list[str] = []
            clone_optimizer_digests: list[str] = []
            clone_rng_digests: list[str] = []
            for partition in PARTITIONS:
                for branch_index in range(4):
                    actor, optimizer = _new_actor_optimizer(anchor["actor_state"], anchor["optimizer_state"])
                    rng_state = copy.deepcopy(anchor["rng_state"])
                    order_tape_rng_state = copy.deepcopy(anchor["order_tape_rng_end_state"])
                    indices = partition_indices(partition, branch_index)
                    batch = [panel[index] for index in indices]
                    clone_actor_digests.append(_state_dict_digest(actor.state_dict()))
                    clone_optimizer_digests.append(_optimizer_digest(optimizer.state_dict()))
                    clone_rng_digests.append(_anchor_rng_digest(rng_state, order_tape_rng_state))
                    update = _run_one_update(actor, optimizer, batch)
                    counts["physical_trajectory_references"] += 4
                    counts["learner_batch_episode_references"] += 8
                    counts["learner_calls"] += 1
                    counts["trainer_calls"] += 1
                    counts["optimizer_updates"] += 1
                    counts["clip_calls"] += 1
                    endpoint_id = f"{partition}|{branch_index}"
                    endpoints[endpoint_id] = {
                        "partition": partition,
                        "branch_index": branch_index,
                        "indices": indices,
                        "actor_state": copy.deepcopy(actor.state_dict()),
                        "optimizer_state": copy.deepcopy(optimizer.state_dict()),
                        "actor_digest": _state_dict_digest(actor.state_dict()),
                        "optimizer_digest": _optimizer_digest(optimizer.state_dict()),
                        "rng_state": rng_state,
                        "order_tape_rng_state": order_tape_rng_state,
                        "rng_digest": _anchor_rng_digest(rng_state, order_tape_rng_state),
                        "update": update,
                    }
                    branch_rows.append(
                        {
                            "history": history_id,
                            "profile": profile_name,
                            "endpoint_id": endpoint_id,
                            "partition": partition,
                            "branch_index": branch_index,
                            "indices": list(indices),
                            "update": update,
                        }
                    )
            clone_witness = {
                "all_actor_clones_exact_anchor": len(set(clone_actor_digests)) == 1
                and clone_actor_digests[0] == str(anchor["actor_digest"]),
                "all_optimizer_clones_exact_anchor": len(set(clone_optimizer_digests)) == 1
                and clone_optimizer_digests[0] == str(anchor["optimizer_digest"]),
                "all_rng_clones_exact_anchor": len(set(clone_rng_digests)) == 1
                and clone_rng_digests[0] == _anchor_rng_digest(
                    anchor["rng_state"], anchor["order_tape_rng_end_state"]
                ),
                "all_eight_endpoints_retained": len(endpoints) == 8,
                "no_post_step_learning": True,
                "partition": partition_witness(),
            }
            retained[cell_key] = {
                "history": history_id,
                "profile": profile_name,
                "anchor_actor_state": copy.deepcopy(anchor["actor_state"]),
                "anchor_optimizer_state": copy.deepcopy(anchor["optimizer_state"]),
                "anchor_actor_digest": str(anchor["actor_digest"]),
                "anchor_optimizer_digest": str(anchor["optimizer_digest"]),
                "anchor_rng_state": copy.deepcopy(anchor["rng_state"]),
                "anchor_order_tape_rng_state": copy.deepcopy(anchor["order_tape_rng_end_state"]),
                "structural_manifest": copy.deepcopy(anchor["structural_manifest"]),
                "panel_manifest": panel_witness,
                "clone_witness": clone_witness,
                "endpoints": endpoints,
            }
    return retained, panel_witnesses, branch_rows


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"B7 object is not a mapping: {path}")
    return value


def create_claim(root: Path, *, source_revision: str, run_id: str, technical_only: bool) -> dict[str, Any]:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    claim_path = root / "claim.json"
    if claim_path.exists() or any(root.iterdir()):
        raise FileExistsError("B7 isolated root must be empty before its one claim")
    claim = {
        "artifact_kind": "EOCIV_B7_TECHNICAL_EXERCISE_CLAIM" if technical_only else "EOCIV_B7_REGISTERED_FULL_CLAIM",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "treatment": TREATMENT,
        "direction": DIRECTION,
        "source_revision": str(source_revision),
        "run_id": str(run_id),
        "technical_only": bool(technical_only),
        "scientific_terminal_admitted": False,
        "one_registered_full": not technical_only,
        "retry_authorized": False,
        "rescue_authorized": False,
        "sweep_authorized": False,
    }
    _write_json(claim_path, claim)
    return claim


def train_phase(root: Path) -> dict[str, Any]:
    root = Path(root)
    claim = _read_json(root / "claim.json")
    endpoints_path = root / "retained_final_endpoints.pt"
    summary_path = root / "train_summary.json"
    if endpoints_path.exists() or summary_path.exists():
        raise FileExistsError("B7 train phase is one-shot")
    technical_only = bool(claim["technical_only"])
    plan = plan_for(technical_only)
    counts = _empty_counts()
    histories, prefix_rows = _train_histories(plan, counts)
    retained, panel_witnesses, branch_rows = _branch_cells(plan, histories, counts)
    expected_train_counts = plan.expected_counts.copy()
    expected_train_counts["unique_complete_episodes"] -= plan.evaluation_episodes
    expected_train_counts["environment_transitions"] -= plan.evaluation_episodes * HORIZON
    expected_train_counts["policy_calls"] -= plan.evaluation_episodes * HORIZON
    expected_train_counts["evaluation_episodes"] = 0
    if counts != expected_train_counts:
        raise RuntimeError(f"B7 train activity drifted: {counts} != {expected_train_counts}")
    payload_state = {
        "binding": RAW_OUTPUT_BINDING,
        "claim": claim,
        "plan": asdict(plan),
        "histories": histories,
        "cells": retained,
    }
    torch.save(payload_state, endpoints_path)
    fidelity = {
        "all_prefix_updates_finite": all(bool(row["update"]["finite_value_diagnostics"]) for row in prefix_rows),
        "all_branch_updates_finite": all(bool(row["update"]["finite_value_diagnostics"]) for row in branch_rows),
        "all_grad_fidelity": all(
            bool(row["update"]["exact_grad_fidelity"] and row["update"]["grad_component_sum_allclose"])
            for row in (*prefix_rows, *branch_rows)
        ),
        "all_clip_fidelity": all(bool(row["update"]["clip_fidelity"]) for row in (*prefix_rows, *branch_rows)),
        "all_panel_witnesses": all(
            all(bool(value) for key, value in row.items() if key in {
                "exact_4x4_panel", "unique_trajectory_keys", "shock_order_per_root",
                "same_public_world_within_root", "same_action_noise_within_root",
                "same_lifecycle_within_root", "legitimate_receipts",
                "segment_latch_zero_boundaries", "anchor_actor_immutable", "global_rng_immutable",
            })
            for row in panel_witnesses
        ),
        "all_clone_witnesses": all(
            all(bool(value) for key, value in cell["clone_witness"].items() if key != "partition")
            and all(bool(value) for key, value in cell["clone_witness"]["partition"].items() if key.endswith("cover") or key in {"same_information_multiset", "four_episodes_per_branch"})
            for cell in retained.values()
        ),
    }
    summary = {
        "artifact_kind": "EOCIV_B7_TRAIN_SUMMARY",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "source_revision": claim["source_revision"],
        "run_id": claim["run_id"],
        "technical_only": technical_only,
        "scientific_terminal_admitted": False,
        "plan": asdict(plan),
        "counts": counts,
        "configuration": registered_configuration(),
        "prefix_update_rows": prefix_rows,
        "panel_witnesses": panel_witnesses,
        "branch_update_rows": branch_rows,
        "fidelity": fidelity,
        "retained_endpoint_file": endpoints_path.name,
        "retained_state_policy": "UNCHANGED_ANCHOR_PLUS_EIGHT_FINAL_ONE_STEP_ENDPOINTS_PER_CELL_ONLY",
    }
    _write_json(summary_path, summary)
    return summary


def _evaluate_actor(
    actor_state: Mapping[str, torch.Tensor],
    history_id: str,
    profile_name: str,
    root_id: int,
    endpoint_id: str,
    counts: dict[str, int],
) -> dict[str, Any]:
    actor, _ = _new_actor_optimizer(actor_state, None)
    actor.eval()
    shock_seed = root_id + 1_000_000
    action_seed = root_id + 2_000_000
    runners = {
        arm: _make_runner(
            actor,
            PROFILE_BY_NAME[profile_name],
            root_id,
            payload.BODY_RULES[arm],
            None,
            shock_seed=shock_seed,
            action_noise_seed=action_seed,
        )
        for arm in EVALUATION_ARMS
    }
    counts["unique_complete_episodes"] += 2
    counts["environment_transitions"] += 2 * HORIZON
    counts["policy_calls"] += 2 * HORIZON
    counts["evaluation_episodes"] += 2
    correct = runners["CORRECT"]
    matching = {
        "natural_shock_seed_exact": shock_seed == root_id + 1_000_000,
        "action_noise_seed_exact": action_seed == root_id + 2_000_000,
        "same_realized_natural_shock_across_arms": all(
            runner.env._shock_states == correct.env._shock_states for runner in runners.values()
        ),
        "same_public_world_across_arms": len({host.public_world_digest(runner.env) for runner in runners.values()}) == 1,
        "same_lifecycle_across_arms": len({host.lifecycle_digest(runner) for runner in runners.values()}) == 1,
        "same_action_noise_across_arms": len({host.action_noise_digest(runner) for runner in runners.values()}) == 1,
        "legitimate_receipts": all(
            len(runner.boundary_records) == len(sibling.EVENT_TIMES)
            and {record.actuation_route for record in runner.boundary_records} == {"REAL"}
            for runner in runners.values()
        ),
        "latch_boundaries_clean": all(runner.policy.started_zero and runner.policy.ended_zero for runner in runners.values()),
    }
    arms = {arm: retention._arm_record(runner) for arm, runner in runners.items()}
    return {
        "history": history_id,
        "profile": profile_name,
        "held_out_root": root_id,
        "root_index": EVALUATION_ROOTS[(history_id, profile_name)].index(root_id),
        "endpoint_id": endpoint_id,
        "partition": "ANCHOR" if endpoint_id == "ANCHOR" else endpoint_id.split("|", 1)[0],
        "branch_index": None if endpoint_id == "ANCHOR" else int(endpoint_id.rsplit("|", 1)[1]),
        "natural_shock_seed": shock_seed,
        "action_noise_seed": action_seed,
        "natural_shock_tuple": list(correct.env._shock_states),
        "public_world_digest": host.public_world_digest(correct.env),
        "lifecycle_digest": host.lifecycle_digest(correct),
        "action_noise_tape_digest": host.action_noise_digest(correct),
        "matching": matching,
        "arms": arms,
        "phi": float(arms["CORRECT"]["episode_return"]) - float(arms["SWAPPED"]["episode_return"]),
    }


def evaluate_phase(root: Path) -> dict[str, Any]:
    root = Path(root)
    train = _read_json(root / "train_summary.json")
    evaluation_path = root / "evaluation_summary.json"
    if evaluation_path.exists():
        raise FileExistsError("B7 evaluate phase is one-shot")
    state = torch.load(root / str(train["retained_endpoint_file"]), map_location="cpu", weights_only=False)
    plan = plan_for(bool(train["technical_only"]))
    counts = copy.deepcopy(train["counts"])
    rows: list[dict[str, Any]] = []
    for history_id in plan.histories:
        for profile_name in plan.profiles:
            cell = state["cells"][f"{history_id}|{profile_name}"]
            models: list[tuple[str, Mapping[str, torch.Tensor]]] = [("ANCHOR", cell["anchor_actor_state"])]
            models.extend((endpoint_id, endpoint["actor_state"]) for endpoint_id, endpoint in cell["endpoints"].items())
            for root_id in EVALUATION_ROOTS[(history_id, profile_name)][: plan.evaluation_root_count]:
                for endpoint_id, actor_state in models:
                    rows.append(
                        _evaluate_actor(actor_state, history_id, profile_name, root_id, endpoint_id, counts)
                    )
    if counts != plan.expected_counts:
        raise RuntimeError(f"B7 final activity drifted: {counts} != {plan.expected_counts}")
    matching = {
        "all_row_matching": all(all(bool(value) for value in row["matching"].values()) for row in rows),
        "exact_rows": len(rows) == plan.cells * plan.evaluation_root_count * 9,
        "two_arms_per_row": all(set(row["arms"]) == set(EVALUATION_ARMS) for row in rows),
        "common_realized_objects_across_models": True,
    }
    for history_id in plan.histories:
        for profile_name in plan.profiles:
            for root_id in EVALUATION_ROOTS[(history_id, profile_name)][: plan.evaluation_root_count]:
                group = [row for row in rows if row["history"] == history_id and row["profile"] == profile_name and row["held_out_root"] == root_id]
                matching["common_realized_objects_across_models"] &= (
                    len({tuple(row["natural_shock_tuple"]) for row in group}) == 1
                    and len({row["public_world_digest"] for row in group}) == 1
                    and len({row["lifecycle_digest"] for row in group}) == 1
                    and len({row["action_noise_tape_digest"] for row in group}) == 1
                )
    summary = {
        "artifact_kind": "EOCIV_B7_EVALUATION_SUMMARY",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "source_revision": train["source_revision"],
        "run_id": train["run_id"],
        "technical_only": bool(train["technical_only"]),
        "scientific_terminal_admitted": False,
        "counts": counts,
        "matching": matching,
        "evaluation_rows": rows,
    }
    _write_json(evaluation_path, summary)
    return summary


def _mean(values: Sequence[float]) -> float:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0 or not np.isfinite(array).all():
        raise RuntimeError("B7 aggregation requires finite nonempty values")
    return float(array.mean())


def _aggregate_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    return {
        "J": _mean([float(row["J"]) for row in rows]),
        "C": _mean([float(row["C"]) for row in rows]),
        "G": _mean([float(row["G"]) for row in rows]),
        "correct_improvement": _mean([float(row["correct_improvement"]) for row in rows]),
        "swapped_improvement": _mean([float(row["swapped_improvement"]) for row in rows]),
    }


def _cell_contrasts(evaluation_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    anchors = {
        (row["history"], row["profile"], int(row["held_out_root"])): row
        for row in evaluation_rows
        if row["endpoint_id"] == "ANCHOR"
    }
    cells: list[dict[str, Any]] = []
    for key, anchor in anchors.items():
        endpoints = [
            row for row in evaluation_rows
            if (row["history"], row["profile"], int(row["held_out_root"])) == key
            and row["endpoint_id"] != "ANCHOR"
        ]
        clustered = [row for row in endpoints if row["partition"] == "ROOT_CLUSTERED"]
        latin = [row for row in endpoints if row["partition"] == "ROOT_STRATIFIED_LATIN"]
        if len(clustered) != 4 or len(latin) != 4:
            raise RuntimeError("B7 evaluation endpoint partition is incomplete")
        anchor_correct = float(anchor["arms"]["CORRECT"]["episode_return"])
        anchor_swapped = float(anchor["arms"]["SWAPPED"]["episode_return"])
        anchor_phi = float(anchor["phi"])
        def deltas(group: Sequence[Mapping[str, Any]]) -> tuple[list[float], list[float], list[float]]:
            correct = [float(row["arms"]["CORRECT"]["episode_return"]) - anchor_correct for row in group]
            swapped = [float(row["arms"]["SWAPPED"]["episode_return"]) - anchor_swapped for row in group]
            phi = [float(row["phi"]) - anchor_phi for row in group]
            return correct, swapped, phi
        cluster_correct, cluster_swapped, cluster_phi = deltas(clustered)
        latin_correct, latin_swapped, latin_phi = deltas(latin)
        correct_improvement = _mean(latin_correct) - _mean(cluster_correct)
        swapped_improvement = _mean(latin_swapped) - _mean(cluster_swapped)
        cells.append(
            {
                "history": key[0],
                "profile": key[1],
                "held_out_root": key[2],
                "root_index": int(anchor["root_index"]),
                "anchor_returns": {arm: float(anchor["arms"][arm]["episode_return"]) for arm in EVALUATION_ARMS},
                "anchor_phi": anchor_phi,
                "clustered_returns": {
                    row["endpoint_id"]: {arm: float(row["arms"][arm]["episode_return"]) for arm in EVALUATION_ARMS}
                    for row in clustered
                },
                "latin_returns": {
                    row["endpoint_id"]: {arm: float(row["arms"][arm]["episode_return"]) for arm in EVALUATION_ARMS}
                    for row in latin
                },
                "clustered_phi_deltas": cluster_phi,
                "latin_phi_deltas": latin_phi,
                "J": _mean(latin_phi) - _mean(cluster_phi),
                "C": correct_improvement,
                "G": 0.5 * (correct_improvement + swapped_improvement),
                "correct_improvement": correct_improvement,
                "swapped_improvement": swapped_improvement,
            }
        )
    return sorted(cells, key=lambda row: (row["history"], row["profile"], row["root_index"]))


def _aggregates(cells: Sequence[Mapping[str, Any]], plan: ExecutionPlan) -> dict[str, Any]:
    by_history = {
        history: _aggregate_rows([row for row in cells if row["history"] == history])
        for history in plan.histories
    }
    by_profile = {
        profile: _aggregate_rows([row for row in cells if row["profile"] == profile])
        for profile in plan.profiles
    }
    by_root_index = {
        str(root_index): _aggregate_rows([row for row in cells if int(row["root_index"]) == root_index])
        for root_index in range(plan.evaluation_root_count)
    }
    leave_one_profile = {
        profile: _aggregate_rows([row for row in cells if row["profile"] != profile])
        for profile in plan.profiles
    } if len(plan.profiles) > 1 else {}
    leave_one_root_index = {
        str(root_index): _aggregate_rows([row for row in cells if int(row["root_index"]) != root_index])
        for root_index in range(plan.evaluation_root_count)
    } if plan.evaluation_root_count > 1 else {}
    variance: dict[str, float] = {}
    for history in plan.histories:
        per_root = []
        for root_index in range(plan.evaluation_root_count):
            group = [row for row in cells if row["history"] == history and int(row["root_index"]) == root_index]
            per_root.append(
                {
                    "clustered": _mean([_mean(row["clustered_phi_deltas"]) for row in group]),
                    "latin": _mean([_mean(row["latin_phi_deltas"]) for row in group]),
                }
            )
        clustered = np.asarray([row["clustered"] for row in per_root], dtype=np.float64)
        latin = np.asarray([row["latin"] for row in per_root], dtype=np.float64)
        variance[history] = float(clustered.var(ddof=0) - latin.var(ddof=0))
    return {
        "grand": _aggregate_rows(cells),
        "by_history": by_history,
        "by_profile": by_profile,
        "by_root_index": by_root_index,
        "leave_one_profile": leave_one_profile,
        "leave_one_root_index": leave_one_root_index,
        "R_by_history": variance,
    }


def select_terminal_branch(
    aggregates: Mapping[str, Any],
    *,
    fidelity_valid: bool,
) -> str:
    if not fidelity_valid:
        return TERMINAL_BRANCHES[0]
    finite_values: list[float] = []
    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for nested in value.values():
                visit(nested)
        elif isinstance(value, (list, tuple)):
            for nested in value:
                visit(nested)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            finite_values.append(float(value))
    visit(aggregates)
    if not finite_values or not np.isfinite(np.asarray(finite_values, dtype=np.float64)).all():
        return TERMINAL_BRANCHES[0]
    grand = aggregates["grand"]
    histories = aggregates["by_history"]
    loo_profiles = aggregates["leave_one_profile"]
    loo_roots = aggregates["leave_one_root_index"]
    semantic = (
        float(grand["J"]) > 0.0
        and all(float(row["J"]) > 0.0 for row in histories.values())
        and bool(loo_profiles)
        and all(float(row["J"]) > 0.0 for row in loo_profiles.values())
        and bool(loo_roots)
        and all(float(row["J"]) > 0.0 for row in loo_roots.values())
        and float(grand["C"]) >= 0.0
        and all(float(value) > 0.0 for value in aggregates["R_by_history"].values())
    )
    if semantic:
        return TERMINAL_BRANCHES[1]
    if (
        (float(grand["G"]) > 0.0 or float(grand["C"]) > 0.0)
        and (
            float(grand["J"]) <= 0.0
            or float(grand["swapped_improvement"]) >= float(grand["correct_improvement"])
        )
    ):
        return TERMINAL_BRANCHES[2]
    if all(float(row["J"]) <= 0.0 for row in histories.values()):
        return TERMINAL_BRANCHES[3]
    return TERMINAL_BRANCHES[4]


def analyze_phase(root: Path) -> dict[str, Any]:
    root = Path(root)
    train = _read_json(root / "train_summary.json")
    evaluation = _read_json(root / "evaluation_summary.json")
    result_path = root / "result.json"
    if result_path.exists():
        raise FileExistsError("B7 analyze phase is one-shot")
    plan = plan_for(bool(train["technical_only"]))
    cells = _cell_contrasts(evaluation["evaluation_rows"])
    aggregates = _aggregates(cells, plan)
    fidelity = {
        **{f"train_{key}": bool(value) for key, value in train["fidelity"].items()},
        **{f"evaluation_{key}": bool(value) for key, value in evaluation["matching"].items()},
        "counts_exact": evaluation["counts"] == plan.expected_counts,
        "configuration_exact": train["configuration"] == registered_configuration(),
        "cell_count_exact": len(cells) == plan.cells * plan.evaluation_root_count,
        "activity_firewalls_zero": all(
            int(evaluation["counts"][key]) == 0 for key in ("retry", "rescue", "sweep", "checkpoint_selection")
        ),
    }
    fidelity_valid = all(fidelity.values()) and not plan.technical_only
    branch = select_terminal_branch(aggregates, fidelity_valid=fidelity_valid)
    result = {
        "artifact_kind": "EOCIV_B7_TECHNICAL_EXERCISE_RESULT" if plan.technical_only else "EOCIV_B7_REGISTERED_RESULT",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "treatment": TREATMENT,
        "direction": DIRECTION,
        "stage": STAGE,
        "source_revision": train["source_revision"],
        "run_id": train["run_id"],
        "technical_only": plan.technical_only,
        "scientific_terminal_admitted": not plan.technical_only,
        "terminal_branch": TERMINAL_BRANCHES[0] if plan.technical_only else branch,
        "technical_exercise_branch_suppressed": plan.technical_only,
        "configuration": registered_configuration(),
        "counts": evaluation["counts"],
        "fidelity": fidelity,
        "full_cell_table": cells,
        "aggregates": aggregates,
        "train_summary_locator": "train_summary.json",
        "evaluation_summary_locator": "evaluation_summary.json",
        "retained_final_endpoints_locator": train["retained_endpoint_file"],
        "interpretation_boundary": (
            "One frozen B7 partition comparison only. No branch licenses a B6 reconstruction, "
            "retry, rescue, sweep, extra history/root/profile/arm, checkpoint selection, C, "
            "formal compute, promotion, retirement, or External Pro."
        ),
    }
    _write_json(result_path, result)
    return result


def registered_configuration() -> dict[str, Any]:
    return {
        "initialization_seed": INITIALIZATION_SEED,
        "history_ids": list(HISTORY_IDS),
        "history_seeds": dict(HISTORY_SEEDS),
        "history_action_noise_tapes": dict(HISTORY_ACTION_TAPES),
        "history_order_tapes": dict(HISTORY_ORDER_TAPES),
        "prefix_roots": list(PREFIX_ROOTS),
        "profiles": list(PROFILE_NAMES),
        "shock_order": [list(value) for value in SHOCK_TUPLES],
        "panel_roots": {f"{key[0]}|{key[1]}": list(value) for key, value in PANEL_ROOTS.items()},
        "panel_action_noise_tapes": {f"{key[0]}|{key[1]}": value for key, value in PANEL_ACTION_TAPES.items()},
        "evaluation_roots": {f"{key[0]}|{key[1]}": list(value) for key, value in EVALUATION_ROOTS.items()},
        "evaluation_shock_seed_rule": "held_out_root+1000000",
        "evaluation_action_noise_seed_rule": "held_out_root+2000000",
        "evaluation_arms": list(EVALUATION_ARMS),
        "partitions": list(PARTITIONS),
        "latin_root_rows": [list(value) for value in LATIN_ROOT_ROWS],
        "horizon": HORIZON,
        "gamma": GAMMA,
        "gae_lambda": GAE_LAMBDA,
        "normalization_epsilon": NORMALIZATION_EPSILON,
        "adam_lr": ADAM_LR,
        "clip_rule": "JOINT_GLOBAL_CLIP",
        "global_clip_cap": GLOBAL_CLIP_CAP,
        "protected_dependency_literals": dict(_DEPENDENCY_LITERALS),
        "learner_batch_episode_reference_rule": "72 branches x 4 physical trajectories x 2 actor/critic replay channels",
        "physical_trajectory_reference_rule": "72 branches x 4 trajectories",
        "full_expected_counts": dict(FULL_EXPECTED_COUNTS),
    }


def validate_result(root: Path, *, require_full: bool) -> dict[str, Any]:
    root = Path(root)
    claim = _read_json(root / "claim.json")
    train = _read_json(root / "train_summary.json")
    evaluation = _read_json(root / "evaluation_summary.json")
    result = _read_json(root / "result.json")
    technical = bool(claim["technical_only"])
    plan = plan_for(technical)
    issues: list[str] = []
    if require_full and technical:
        issues.append("full validation rejects a technical-only artifact")
    if not all(value.get("raw_output_binding") == RAW_OUTPUT_BINDING for value in (claim, train, evaluation, result)):
        issues.append("raw output binding drift")
    if len({value.get("source_revision") for value in (claim, train, evaluation, result)}) != 1:
        issues.append("source revision drift")
    if len({value.get("run_id") for value in (claim, train, evaluation, result)}) != 1:
        issues.append("run id drift")
    if result.get("configuration") != registered_configuration() or train.get("configuration") != registered_configuration():
        issues.append("registered configuration drift")
    if evaluation.get("counts") != plan.expected_counts or result.get("counts") != plan.expected_counts:
        issues.append("activity count drift")
    if not technical and plan.expected_counts != FULL_EXPECTED_COUNTS:
        issues.append("full cap derivation drift")
    if int(result["counts"].get("physical_trajectory_references", -1)) * 2 != int(result["counts"].get("learner_batch_episode_references", -2)):
        issues.append("actor/critic replay-channel reference drift")
    if int(result["counts"].get("learner_batch_episode_references", -1)) != plan.cells * 8 * 4 * 2:
        issues.append("learner batch episode reference count drift")
    if int(result["counts"].get("physical_trajectory_references", -1)) != plan.cells * 8 * 4:
        issues.append("physical trajectory reference count drift")
    if result.get("terminal_branch") not in TERMINAL_BRANCHES:
        issues.append("unknown terminal branch")
    if technical and (result.get("scientific_terminal_admitted") or not result.get("technical_exercise_branch_suppressed")):
        issues.append("technical exercise admitted a scientific branch")
    if not technical and not result.get("scientific_terminal_admitted"):
        issues.append("registered full is not terminal-admitted")
    if len(result.get("full_cell_table", ())) != plan.cells * plan.evaluation_root_count:
        issues.append("full cell table shape drift")
    if not all(bool(value) for value in result.get("fidelity", {}).values()):
        issues.append("fidelity witness failed")
    endpoint_state = torch.load(root / str(result["retained_final_endpoints_locator"]), map_location="cpu", weights_only=False)
    if set(endpoint_state.get("cells", {})) != {
        f"{history}|{profile}" for history in plan.histories for profile in plan.profiles
    }:
        issues.append("retained endpoint cell set drift")
    for cell in endpoint_state.get("cells", {}).values():
        if len(cell.get("endpoints", {})) != 8:
            issues.append("retained endpoint count drift")
            break
        if any("MID" in key or "INIT" in key for key in cell):
            issues.append("non-final checkpoint retained")
            break
    if issues:
        raise RuntimeError("B7 artifact validation failed: " + "; ".join(issues))
    return {
        "artifact_valid": True,
        "technical_only": technical,
        "source_revision": result["source_revision"],
        "run_id": result["run_id"],
        "terminal_branch": result["terminal_branch"],
        "counts": result["counts"],
    }


def run_lifecycle(
    root: Path,
    *,
    source_revision: str,
    run_id: str,
    technical_only: bool,
) -> dict[str, Any]:
    create_claim(root, source_revision=source_revision, run_id=run_id, technical_only=technical_only)
    train_phase(root)
    evaluate_phase(root)
    analyze_phase(root)
    return validate_result(root, require_full=not technical_only)

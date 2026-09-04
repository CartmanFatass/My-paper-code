"""Native recurrent rollout and persistent 1,024-update trainer for r06.

This is the E1 flow-local implementation.  It deliberately exposes no panel
or lease orchestration.  A later E2 adapter may bind an authorized native
batch and an authorized master to this flow.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import inspect
import io
import math
from typing import Callable, Final, Mapping, Protocol

import numpy as np
import torch

from .production_backend import NativeBatch, empty_step_rows, rng_words_native
from .production_contract import ARMS, TRAIN_LANES, TRANSITIONS_PER_UPDATE, UPDATES
from .production_population import address
from .production_train_reset import TrainResetKey, arm_substream, build_train_reset_row
from .production_training import PersistentTrainer
from .production_training_engine import (
    ExactPolicyGraph, WelfordState, _policy_log_prob, _role_policy_heads,
)


TICKS_PER_UPDATE_PER_LANE: Final = 128
COPIES: Final = 4
HIDDEN: Final = 128


class RecurrentTrainerError(RuntimeError):
    pass


class AddressedPolicySampler(Protocol):
    def normal(self, *, lane: int, tick: int, field: str) -> float: ...
    def bernoulli(self, *, lane: int, tick: int, field: str, probability: float) -> int: ...


class PassiveLabelPlane(Protocol):
    """Native auxiliary-label boundary retained by the frozen training law."""

    def labels(self, *, tick: int, native_rows: Mapping[str, np.ndarray]) -> Mapping[str, np.ndarray]: ...


class MasterAddressedPolicySampler:
    """Exact counter-addressed Gaussian/Bernoulli policy stream for TRAIN."""

    def __init__(
        self, *, master: bytes, block: int, arm: str,
        episode_wave: np.ndarray, episode_tick: np.ndarray,
    ) -> None:
        self.master = bytes(master); self.block = block; self.arm = arm
        self.episode_wave = episode_wave; self.episode_tick = episode_tick
        if len(self.master) != 32 or not 0 <= block < 24 or arm not in ARMS:
            raise RecurrentTrainerError("policy sampler binding differs")
        if episode_wave.shape != (32,) or episode_tick.shape != (32,):
            raise RecurrentTrainerError("policy sampler lane state differs")
        self.slot = arm_substream(self.master, block, arm)

    def _uniform(self, *, lane: int, field: str, draw_index: int) -> float:
        key = TrainResetKey(self.block, self.arm, lane, int(self.episode_wave[lane]))
        value = address(
            purpose="POLICY_SAMPLE", block=self.block, split="TRAIN",
            regime=key.regime, schedule=key.schedule, evaluation_slot=None,
            lane=lane, cycle=None, arm_substream=self.slot,
            degradation_flag="DEGRADED_ONLY", fork_branch="NONE",
            episode=int(self.episode_wave[lane]), tick=int(self.episode_tick[lane]),
            field=field, draw_index=draw_index,
        )
        word = rng_words_native(self.master, (value,))[0]
        return ((word >> 11) + 0.5) / 2**53

    def normal(self, *, lane: int, tick: int, field: str) -> float:
        del tick  # Physical episode tick is the frozen address coordinate.
        first = self._uniform(lane=lane, field=field, draw_index=0)
        second = self._uniform(lane=lane, field=field, draw_index=1)
        return math.sqrt(-2.0 * math.log(first)) * math.cos(2.0 * math.pi * second)

    def bernoulli(self, *, lane: int, tick: int, field: str, probability: float) -> int:
        del tick
        if not 0.0 <= probability <= 1.0 or not math.isfinite(probability):
            raise RecurrentTrainerError("policy Bernoulli probability differs")
        return int(self._uniform(lane=lane, field=field, draw_index=0) < probability)


class MasterAddressedTrainResetFactory:
    def __init__(self, *, master: bytes, block: int, arm: str) -> None:
        self.master = bytes(master); self.block = block; self.arm = arm
        if len(self.master) != 32 or not 0 <= block < 24 or arm not in ARMS:
            raise RecurrentTrainerError("TRAIN reset factory binding differs")

    def rows(self, episode_wave: np.ndarray) -> tuple[Mapping[str, object], ...]:
        waves = np.asarray(episode_wave, dtype=np.int64)
        if waves.shape != (32,) or np.any(waves < 0):
            raise RecurrentTrainerError("TRAIN reset wave vector differs")
        return tuple(
            build_train_reset_row(self.master, TrainResetKey(self.block, self.arm, lane, int(waves[lane])))
            for lane in range(32)
        )


@dataclass
class RecurrentRolloutState:
    arm: str
    hidden: torch.Tensor
    actor_welford: WelfordState
    snapshot_welford: WelfordState
    critic_welford: WelfordState
    lane_episode_wave: np.ndarray
    lane_episode_tick: np.ndarray
    updates_completed: int = 0

    @classmethod
    def fresh(cls, arm: str, *, width: int = TRAIN_LANES) -> "RecurrentRolloutState":
        if arm not in ARMS:
            raise RecurrentTrainerError("recurrent trainer arm differs")
        if width <= 0 or width > TRAIN_LANES:
            raise RecurrentTrainerError("recurrent batch width differs")
        return cls(
            arm=arm, hidden=torch.zeros((width, COPIES, HIDDEN), dtype=torch.float32),
            actor_welford=WelfordState.empty(54), snapshot_welford=WelfordState.empty(18),
            critic_welford=WelfordState.empty(58),
            lane_episode_wave=np.zeros(width, dtype=np.int64),
            lane_episode_tick=np.zeros(width, dtype=np.int64),
        )

    def validate(self) -> None:
        width = self.hidden.shape[0] if self.hidden.ndim == 3 else -1
        if self.arm not in ARMS or self.hidden.shape != (width, 4, 128) or not 0 < width <= 32:
            raise RecurrentTrainerError("persistent recurrent-state shape differs")
        if self.lane_episode_wave.shape != (width,) or self.lane_episode_tick.shape != (width,):
            raise RecurrentTrainerError("persistent lane-state shape differs")
        if not 0 <= self.updates_completed <= UPDATES:
            raise RecurrentTrainerError("persistent update counter differs")

    def to_bytes(self) -> bytes:
        self.validate(); stream = io.BytesIO()
        torch.save({
            "arm": self.arm, "hidden": self.hidden,
            "actor_welford": self.actor_welford, "snapshot_welford": self.snapshot_welford,
            "critic_welford": self.critic_welford,
            "lane_episode_wave": self.lane_episode_wave,
            "lane_episode_tick": self.lane_episode_tick,
            "updates_completed": self.updates_completed,
        }, stream)
        return stream.getvalue()

    @classmethod
    def from_bytes(cls, payload: bytes) -> "RecurrentRolloutState":
        value = torch.load(io.BytesIO(bytes(payload)), map_location="cpu", weights_only=False)
        state = cls(**value); state.validate(); return state


def _load_policy(checkpoint_bytes: bytes | None) -> ExactPolicyGraph:
    model = ExactPolicyGraph()
    if checkpoint_bytes is not None:
        value = torch.load(io.BytesIO(bytes(checkpoint_bytes)), map_location="cpu", weights_only=False)
        if set(("model", "optimizer", "welford", "update")) - set(value):
            raise RecurrentTrainerError("persistent checkpoint schema differs")
        model.load_state_dict(value["model"])
    model.eval()
    return model


def build_master_addressed_initial_state(*, master: bytes, block: int, arm: str) -> bytes:
    """Materialize the frozen Xavier initialization only under later authority.

    E1 defines this source but never calls it: model initialization itself is
    question-relevant activity and remains behind the future Root lease.
    """

    raw_master = bytes(master)
    if len(raw_master) != 32 or not 0 <= block < 24 or arm not in ARMS:
        raise RecurrentTrainerError("production initialization coordinate differs")
    slot = arm_substream(raw_master, block, arm)
    model = ExactPolicyGraph()
    matrices = (
        model.encoder1, model.encoder2, model.wz, model.uz, model.wr, model.ur,
        model.wh, model.uh, model.motion, model.prepare, model.commit,
        model.prediction_mean, model.prediction_cholesky, model.service_q,
        model.link_mean, model.link_sigma, model.missing, model.snapshot_encoder,
        model.snapshot_bridge, model.flex_delta, model.flex_alpha,
        model.flex_readiness, model.flex_beta, model.critic1, model.critic2,
        model.critic_out,
    )
    with torch.no_grad():
        for module_ordinal, layer in enumerate(matrices):
            layer.bias.zero_() if layer.bias is not None else None
            if 19 <= module_ordinal <= 22:
                layer.weight.zero_(); continue
            fan_out, fan_in = layer.weight.shape
            bound = math.sqrt(6.0 / (fan_in + fan_out))
            values = torch.empty_like(layer.weight)
            addresses = []
            for column in range(fan_in):
                for row in range(fan_out):
                    draw_index = column * fan_out + row
                    addresses.append(address(
                        purpose="INIT", block=block, split="TRAIN", regime="NONE",
                        schedule="NONE", evaluation_slot=None, lane=None,
                        cycle=module_ordinal, arm_substream=slot,
                        degradation_flag="DEGRADED_ONLY", fork_branch="NONE",
                        field="PARAMETER_UNIFORM", draw_index=draw_index,
                    ))
            words = rng_words_native(raw_master, tuple(addresses))
            for column in range(fan_in):
                for row in range(fan_out):
                    draw_index = column * fan_out + row
                    uniform = ((words[draw_index] >> 11) + 0.5) / 2**53
                    values[row, column] = -bound + 2.0 * bound * uniform
            layer.weight.copy_(values)
        model.log_std.fill_(-0.5)
    matrix_parameters = [parameter for name, parameter in model.named_parameters() if parameter.ndim >= 2 and "flex_" not in name]
    matrix_ids = {id(parameter) for parameter in matrix_parameters}
    other_parameters = [parameter for parameter in model.parameters() if id(parameter) not in matrix_ids]
    optimizer = torch.optim.AdamW(
        [{"params": matrix_parameters, "weight_decay": 1e-4}, {"params": other_parameters, "weight_decay": 0.0}],
        lr=3e-4, betas=(0.9, 0.999), eps=1e-8,
    )
    payload = {
        "model": model.state_dict(), "optimizer": optimizer.state_dict(),
        "welford": {"actor": WelfordState.empty(54), "snapshot": WelfordState.empty(18), "critic": WelfordState.empty(58)},
        "update": 0, "evaluation_checkpoint": False,
        "initialization": {"block": block, "arm": arm, "arm_substream": slot},
    }
    stream = io.BytesIO(); torch.save(payload, stream); return stream.getvalue()


def _promotion(hidden: torch.Tensor, cas_applied: np.ndarray, owner_before: np.ndarray, alpha: np.ndarray) -> torch.Tensor:
    result = hidden.clone()
    for lane in np.flatnonzero(np.asarray(cas_applied, dtype=bool)):
        owner = int(owner_before[lane]); standby = 1 - owner
        old_i, old_s = 2 * owner, 2 * owner + 1
        new_i, new_s = 2 * standby, 2 * standby + 1
        promoted = torch.clamp(alpha[lane] * hidden[lane, new_s] + (1.0 - alpha[lane]) * hidden[lane, old_i], -1.0, 1.0)
        result[lane, new_i] = promoted
        result[lane, old_s] = hidden[lane, old_i]
    return result


class BatchedRecurrentPolicy:
    """One batched policy forward per primitive tick; no Python env loop."""

    def __init__(self, *, arm: str, checkpoint_bytes: bytes | None, state: RecurrentRolloutState) -> None:
        state.validate()
        if arm != state.arm:
            raise RecurrentTrainerError("policy/state arm binding differs")
        self.arm = arm; self.model = _load_policy(checkpoint_bytes); self.state = state
        self.last_behavior_log_prob = torch.empty(state.hidden.shape[0], dtype=torch.float32)
        if checkpoint_bytes is not None:
            retained = torch.load(io.BytesIO(bytes(checkpoint_bytes)), map_location="cpu", weights_only=False)
            welford = retained.get("welford", {})
            if {"actor", "snapshot", "critic"}.issubset(welford):
                self.state.actor_welford = welford["actor"]
                self.state.snapshot_welford = welford["snapshot"]
                self.state.critic_welford = welford["critic"]

    def normalized_actor(self, observation: Mapping[str, np.ndarray]) -> torch.Tensor:
        actor = torch.as_tensor(observation["actor"], dtype=torch.float32)
        width = self.state.hidden.shape[0]
        if actor.shape != (width, 4, 54):
            raise RecurrentTrainerError("native actor batch differs")
        return self.state.actor_welford.normalized(actor)

    def prepare_recurrent(
        self, observation: Mapping[str, np.ndarray], *, reset_lanes: np.ndarray | None = None,
    ) -> None:
        width = self.state.hidden.shape[0]
        resets = np.zeros(width, dtype=bool) if reset_lanes is None else np.asarray(reset_lanes, dtype=bool)
        if resets.shape != (width,):
            raise RecurrentTrainerError("episode-reset lane vector differs")
        self.state.hidden = self.model.prepare_recurrent_hidden(
            self.state.hidden,
            torch.as_tensor(observation["snapshot_payload"], dtype=torch.float32),
            torch.as_tensor(np.asarray(observation["snapshot_delivery_mask"]) != 0),
            torch.as_tensor(~resets, dtype=torch.float32),
            torch.as_tensor(observation["owner"], dtype=torch.long),
        )

    def step_rows(
        self, observation: Mapping[str, np.ndarray], *, sampler: AddressedPolicySampler,
        global_tick: int, deterministic: bool, reset_lanes: np.ndarray | None = None,
        recurrent_prepared: bool = False,
    ) -> np.ndarray:
        actor = torch.as_tensor(observation["actor"], dtype=torch.float32)
        width = self.state.hidden.shape[0]
        if actor.shape != (width, 4, 54):
            raise RecurrentTrainerError("native actor batch differs")
        owner = np.asarray(observation["owner"], dtype=np.int64)
        if not recurrent_prepared:
            self.prepare_recurrent(observation, reset_lanes=reset_lanes)
        normalized = self.normalized_actor(observation)
        with torch.no_grad():
            self.state.hidden = self.model.advance_recurrent_hidden(normalized, self.state.hidden)
            heads = self.model.heads(self.state.hidden)
        rows = empty_step_rows(width)
        rows["arm_mode"] = ARMS.index(self.arm)
        owner_tensor = torch.as_tensor(owner, dtype=torch.long)
        motion, prepare_logit, commit_logit = _role_policy_heads(heads, owner_tensor)
        means = (3.0 * torch.tanh(motion)).detach().cpu().numpy()
        log_std = torch.clamp(
            self.model.log_std.detach(), -5.0, 1.0,
        ).cpu().numpy()
        renew = np.asarray(observation["renew"], dtype=bool)
        for lane in range(width):
            for component, field in enumerate(("MOTION_OWNER_X", "MOTION_OWNER_Y", "MOTION_STANDBY_X", "MOTION_STANDBY_Y")):
                if renew[lane]:
                    noise = 0.0 if deterministic else sampler.normal(lane=lane, tick=global_tick, field=field)
                    rows["raw_action"][lane, component] = (
                        float(means[lane, component])
                        + math.exp(float(log_std[component])) * noise
                    )
                else:
                    physical_u0 = 0 if owner[lane] == 0 else 1
                    physical_u1 = 2 if owner[lane] == 1 else 3
                    physical = physical_u0 if component < 2 else physical_u1
                    rows["raw_action"][lane, component] = float(
                        actor[lane, physical, 8 + (component % 2)]
                    )
        action = torch.from_numpy(rows["raw_action"].astype(np.float32, copy=True))
        prepare_all = torch.sigmoid(prepare_logit).detach().cpu().numpy()
        commit_all = torch.sigmoid(commit_logit).detach().cpu().numpy()
        for lane in range(width):
            if renew[lane] and self.arm in ("STRUCTURED", "FLEX", "NEVER"):
                prepare_probability = float(prepare_all[lane])
                commit_probability = float(commit_all[lane])
                rows["prepare"][lane, owner[lane]] = int(prepare_probability >= 0.5) if deterministic else sampler.bernoulli(lane=lane, tick=global_tick, field="PREPARE_BERNOULLI", probability=prepare_probability)
                rows["commit"][lane, owner[lane]] = int(commit_probability >= 0.5) if deterministic else sampler.bernoulli(lane=lane, tick=global_tick, field="COMMIT_BERNOULLI", probability=commit_probability)
                if self.arm == "NEVER":
                    # Native arm_mode=NEVER serializes the equal-size charged
                    # NOOP intent and guarantees no effective CAS.
                    pass
            elif renew[lane] and self.arm in ("IMMEDIATE", "HYSTERESIS"):
                active = 2 * int(owner[lane]); gate_index = 45 if self.arm == "IMMEDIATE" else 46
                gate = bool(actor[lane, active, gate_index] >= 0.5)
                rows["prepare"][lane, owner[lane]] = int(gate)
                rows["commit"][lane, owner[lane]] = int(gate)
        prediction = heads["prediction_mean"].detach().cpu().numpy()
        cholesky = heads["prediction_cholesky"].detach().cpu().numpy()
        q_values = heads["service_q"].detach().cpu().numpy()
        for lane in range(width):
            incumbent = 2 * int(owner[lane]); standby_shadow = 2 * (1 - int(owner[lane])) + 1
            rows["prediction_mean"][lane, :4] = prediction[lane, incumbent]
            rows["prediction_mean"][lane, 4:] = prediction[lane, standby_shadow]
            for destination, copy_index in ((0, incumbent), (16, standby_shadow)):
                raw = cholesky[lane, copy_index]
                lower = np.zeros((4, 4), dtype=np.float64)
                cursor = 0
                for row in range(4):
                    for column in range(row + 1):
                        value = float(raw[cursor]); cursor += 1
                        lower[row, column] = math.log1p(math.exp(value)) + 1e-3 if row == column else value
                rows["prediction_covariance"][lane, destination:destination + 16] = (lower @ lower.T + 1e-4 * np.eye(4)).reshape(-1)
            rows["service_q"][lane] = q_values[lane, standby_shadow]
        rows["controller_hidden"] = self.state.hidden.detach().cpu().numpy().reshape(width, 512)
        if self.arm == "FLEX":
            alpha_all = heads["flex_alpha"][:, :, 0].detach().cpu().numpy()
            rows["promotion_alpha"] = np.asarray([alpha_all[lane, 2 * int(owner[lane])] for lane in range(width)])
        lane = np.arange(width)
        prepare_outcome = torch.from_numpy(rows["prepare"][lane, owner].astype(np.float32))
        commit_outcome = torch.from_numpy(rows["commit"][lane, owner].astype(np.float32))
        _, self.last_behavior_log_prob = _policy_log_prob(
            self.arm, motion, self.model.log_std.detach(), action,
            prepare_logit, commit_logit, prepare_outcome, commit_outcome,
            torch.as_tensor(renew),
        )
        return rows

    def apply_native_promotion(
        self, *, owner_before: np.ndarray, step_rows: np.ndarray,
        observation_after: Mapping[str, np.ndarray],
    ) -> None:
        self.state.hidden = _promotion(
            self.state.hidden, observation_after["cas_applied"], owner_before,
            np.asarray(step_rows["promotion_alpha"], dtype=np.float32),
        )


class NativePersistentTrainingFlow:
    """Flow-local native rollout plus the retained persistent PPO updater."""

    def __init__(
        self, *, native: NativeBatch, arm: str, master: bytes, block: int,
        checkpoint_bytes: bytes | None = None,
        state: RecurrentRolloutState | None = None,
    ) -> None:
        if native.width != TRAIN_LANES:
            raise RecurrentTrainerError("TRAIN native width must be 32")
        if checkpoint_bytes is None:
            raise RecurrentTrainerError("master-addressed initial training state is required")
        self.state = RecurrentRolloutState.fresh(arm) if state is None else state
        self.native = native
        self.sampler = MasterAddressedPolicySampler(
            master=master, block=block, arm=arm,
            episode_wave=self.state.lane_episode_wave, episode_tick=self.state.lane_episode_tick,
        )
        self.reset_factory = MasterAddressedTrainResetFactory(master=master, block=block, arm=arm)
        self.trainer = PersistentTrainer(arm=arm, checkpoint_bytes=checkpoint_bytes)
        self.policy = BatchedRecurrentPolicy(arm=arm, checkpoint_bytes=checkpoint_bytes, state=self.state)

    def collect_update(self, initial_observation: Mapping[str, np.ndarray]) -> Mapping[str, torch.Tensor]:
        """Collect exactly 32x128 native transitions for one PPO update."""

        observation_by_tick: list[Mapping[str, np.ndarray]] = []
        outcome_by_tick: list[Mapping[str, np.ndarray]] = []
        labels_by_tick: list[Mapping[str, np.ndarray]] = []
        actions_by_tick: list[np.ndarray] = []
        behavior_log_prob_by_tick: list[np.ndarray] = []
        normalized_actor_by_tick: list[np.ndarray] = []
        hidden_before_tick: list[np.ndarray] = []
        reset_by_tick: list[np.ndarray] = []
        observation = initial_observation
        owner_before = np.asarray(observation["owner"], dtype=np.int64)
        reset_lanes = np.zeros(TRAIN_LANES, dtype=bool)
        for offset in range(TICKS_PER_UPDATE_PER_LANE):
            observation_by_tick.append({name: np.asarray(value).copy() for name, value in observation.items()})
            normalized_actor_by_tick.append(self.policy.normalized_actor(observation).detach().cpu().numpy().copy())
            hidden_before_tick.append(self.state.hidden.detach().cpu().numpy().copy())
            reset_by_tick.append(reset_lanes.copy())
            action_rows = self.policy.step_rows(
                observation, sampler=self.sampler,
                global_tick=self.state.updates_completed * TICKS_PER_UPDATE_PER_LANE + offset,
                deterministic=False, reset_lanes=reset_lanes,
            )
            behavior_log_prob_by_tick.append(
                self.policy.last_behavior_log_prob.detach().cpu().numpy().copy()
            )
            labels_by_tick.append(self.native.passive_labels(action_rows))
            next_observation = self.native.step(action_rows)
            self.policy.apply_native_promotion(
                owner_before=owner_before, step_rows=action_rows, observation_after=next_observation,
            )
            outcome_by_tick.append(next_observation); actions_by_tick.append(action_rows.copy())
            owner_before = np.asarray(next_observation["owner"], dtype=np.int64)
            terminal = np.asarray(next_observation["terminal"], dtype=bool)
            self.state.lane_episode_tick += 1
            ended = terminal | (self.state.lane_episode_tick >= 1_200)
            self.state.lane_episode_wave[ended] += 1; self.state.lane_episode_tick[ended] = 0
            observation = self.native.reset_selected(
                ended, self.reset_factory.rows(self.state.lane_episode_wave),
            ) if bool(np.any(ended)) else next_observation
            owner_before = np.asarray(observation["owner"], dtype=np.int64)
            reset_lanes = ended
        if bool(np.any(reset_lanes)):
            self.state.hidden[torch.as_tensor(reset_lanes)] = 0.0
        if len(observation_by_tick) * TRAIN_LANES != TRANSITIONS_PER_UPDATE:
            raise RecurrentTrainerError("TRAIN update transition count differs")
        return self._fragments(
            observation_by_tick, outcome_by_tick, actions_by_tick, labels_by_tick,
            normalized_actor_by_tick, hidden_before_tick, reset_by_tick,
            behavior_log_prob_by_tick,
        )

    def _fragments(
        self, observation_ticks: list[Mapping[str, np.ndarray]],
        outcome_ticks: list[Mapping[str, np.ndarray]], action_ticks: list[np.ndarray],
        label_ticks: list[Mapping[str, np.ndarray]], normalized_actor_ticks: list[np.ndarray],
        hidden_before_ticks: list[np.ndarray], reset_ticks: list[np.ndarray],
        behavior_log_prob_ticks: list[np.ndarray],
    ) -> Mapping[str, torch.Tensor]:
        """Bind collected rows to the retained 64-fragment PPO schema."""

        def observation_stack(name: str) -> np.ndarray:
            return np.stack([np.asarray(row[name]) for row in observation_ticks], axis=0)
        def outcome_stack(name: str) -> np.ndarray:
            return np.stack([np.asarray(row[name]) for row in outcome_ticks], axis=0)
        def fragment(value: np.ndarray) -> np.ndarray:
            return np.ascontiguousarray(value.transpose(1, 0, *range(2, value.ndim)).reshape(64, 64, *value.shape[2:]))
        actor_raw = fragment(observation_stack("actor"))
        actor = fragment(np.stack(normalized_actor_ticks, axis=0))
        critic_tick = outcome_stack("critic")
        def label(name: str) -> np.ndarray:
            return np.stack([np.asarray(row[name]) for row in label_ticks], axis=0)
        action = np.stack(action_ticks, axis=0)
        owner = fragment(observation_stack("owner")).astype(np.int64)
        lane = np.arange(TRAIN_LANES)[None, :]
        owner_action = np.stack([np.asarray(row["owner"], dtype=np.int64) for row in observation_ticks], axis=0)
        prepare_outcome = action["prepare"][np.arange(128)[:, None], lane, owner_action]
        commit_outcome = action["commit"][np.arange(128)[:, None], lane, owner_action]
        hidden_sequence = np.stack(hidden_before_ticks, axis=0).transpose(1, 0, 2, 3)
        initial_hidden = hidden_sequence[:, (0, 64)].reshape(64, 4, 128)
        result = {
            "observation": torch.from_numpy(actor).float(),
            "actor_raw": torch.from_numpy(actor_raw).float(),
            "initial_hidden": torch.from_numpy(np.ascontiguousarray(initial_hidden)).float(),
            "owner": torch.from_numpy(owner).long(),
            "critic": torch.from_numpy(np.ascontiguousarray(critic_tick.transpose(1, 0, 2).reshape(4096, 58))).float(),
            "snapshot": torch.from_numpy(fragment(observation_stack("snapshot_payload"))).float(),
            "snapshot_mask": torch.from_numpy(fragment(observation_stack("snapshot_delivery_mask")).astype(bool)),
            "promotion_mask": torch.from_numpy(fragment(outcome_stack("cas_applied")).astype(bool)),
            "promotion_alpha": torch.from_numpy(fragment(action["promotion_alpha"]).astype(np.float32)),
            "reset_mask": torch.from_numpy((~fragment(np.stack(reset_ticks, axis=0)).astype(bool)).astype(np.float32)),
            "renew": torch.from_numpy(fragment(observation_stack("renew")).astype(bool)),
            "prepare_mask": torch.from_numpy(fragment(observation_stack("renew")).astype(bool)),
            "commit_mask": torch.from_numpy(fragment(observation_stack("renew")).astype(bool)),
            "action": torch.from_numpy(fragment(action["raw_action"])).float(),
            "prepare_outcome": torch.from_numpy(fragment(prepare_outcome).astype(np.float32)),
            "commit_outcome": torch.from_numpy(fragment(commit_outcome).astype(np.float32)),
            "behavior_log_prob": torch.from_numpy(fragment(
                np.stack(behavior_log_prob_ticks, axis=0)
            ).astype(np.float32)),
            "reward": torch.from_numpy(np.ascontiguousarray(outcome_stack("service").T)).float(),
            "done": torch.from_numpy(np.ascontiguousarray(outcome_stack("terminal").T)).float(),
            "target": torch.from_numpy(np.ascontiguousarray(label("target").transpose(1, 0, 2).reshape(4096, 4))).float(),
            "links": torch.from_numpy(np.ascontiguousarray(label("links").transpose(1, 0, 2, 3).reshape(4096, 4, 2))).float(),
            "missing": torch.from_numpy(np.ascontiguousarray(label("missing").transpose(1, 0, 2).reshape(4096, 4))).float(),
            "q_labels": torch.from_numpy(np.ascontiguousarray(label("q_labels").transpose(1, 0, 2).reshape(4096, 20))).float(),
            "q_mask": torch.from_numpy(np.ascontiguousarray(label("q_mask").T.reshape(4096))).bool(),
            "next_mask": torch.from_numpy(np.ascontiguousarray(label("next_mask").T.reshape(4096))).bool(),
            "q_copy_index": torch.from_numpy(np.ascontiguousarray(label("q_copy_index").T.reshape(4096))).long(),
        }
        return result

    def apply_update(self, fragments: Mapping[str, torch.Tensor]) -> Mapping[str, object]:
        if self.state.updates_completed >= UPDATES:
            raise RecurrentTrainerError("TRAIN job already reached 1,024 updates")
        receipt = self.trainer.run_update(fragments, source_label="R06_NATIVE_PRODUCTION_ROWS")
        self.state.updates_completed += 1
        if int(receipt["update"]) != self.state.updates_completed:
            raise RecurrentTrainerError("persistent update sequence differs")
        retained = torch.load(io.BytesIO(self.trainer.checkpoint_bytes), map_location="cpu", weights_only=False)
        self.state.actor_welford = retained["welford"]["actor"]
        self.state.snapshot_welford = retained["welford"]["snapshot"]
        self.state.critic_welford = retained["welford"]["critic"]
        self.policy = BatchedRecurrentPolicy(
            arm=self.state.arm, checkpoint_bytes=self.trainer.checkpoint_bytes, state=self.state,
        )
        return receipt

    def sole_evaluation_checkpoint(self) -> bytes:
        if self.state.updates_completed != UPDATES:
            raise RecurrentTrainerError("evaluation checkpoint requested before update 1,024")
        return self.trainer.sole_checkpoint()


def flow_local_trainer_self_audit() -> dict[str, object]:
    """Static/result-blind E1 audit; it does not instantiate a model or host."""

    source = inspect.getsource(NativePersistentTrainingFlow)
    required = (
        "TICKS_PER_UPDATE_PER_LANE", "TRANSITIONS_PER_UPDATE", "PersistentTrainer",
        "RecurrentRolloutState", "sole_evaluation_checkpoint", "passive_labels",
        "reset_selected", "MasterAddressedPolicySampler",
    )
    return {
        "schema": "DISH_RBHR_R06_E1_RECURRENT_TRAINER_FLOW_LOCAL_SELF_AUDIT_V1",
        "required_tokens_present": all(token in source or token in globals() for token in required),
        "train_lanes": TRAIN_LANES, "ticks_per_lane_per_update": TICKS_PER_UPDATE_PER_LANE,
        "transitions_per_update": TRAIN_LANES * TICKS_PER_UPDATE_PER_LANE,
        "updates_per_job": UPDATES, "persistent_hidden_shape": [32, 4, 128],
        "native_batch_required": True, "scalar_python_environment": False,
        "model_instantiated": False, "checkpoint_created": False,
        "training_activity": False, "question_relevant_output": False,
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
    }


__all__ = [
    "AddressedPolicySampler", "MasterAddressedPolicySampler", "MasterAddressedTrainResetFactory", "BatchedRecurrentPolicy", "NativePersistentTrainingFlow",
    "PassiveLabelPlane", "RecurrentRolloutState", "RecurrentTrainerError",
    "build_master_addressed_initial_state", "flow_local_trainer_self_audit",
]

"""B-level real actor/critic and detached-valve experiment for EOCIV-LITE.

This module is intentionally candidate-local.  It drives the real sibling
environment through :class:`ArmEpisodeRunner`; it does not license or execute
the registered C-level outcome experiment in ``capability_gate``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

import numpy as np
import torch
from torch import nn

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import actuation_runtime as art
from experiments.candidates.eociv_lite import capability_gate
from experiments.candidates.eociv_lite import sibling_env as sib


TREATMENT = "EOCIV-B1-REAL-VALVE-LEARNING-SIGNAL"
ACTOR_SEEDS = (86031, 86032, 86033)
PROFILES = roster_env.TRAIN_PROFILES
ACTOR_LR = 3e-4
VALVE_LR = 1e-2
GAMMA = 0.99
GRAD_NORM_CAP = 0.5
VALVE_L2 = 1e-3
VALVE_STEPS = 128
VALVE_THRESHOLD = 0.25
MASTER_SEED = capability_gate.MASTER_SEED
SIBLING_SEED = capability_gate.SIBLING_SEED
TAPE_SEED = capability_gate.TAPE_SEED

ROLE_NAMES = ("CAPABILITY_0", "CAPABILITY_1")
AGE_BINS = ("0_TO_4", "5_TO_16", "17_PLUS")
FEATURE_KEYS = frozenset(
    {
        "sender_role",
        "receiver_role",
        "active_member_count",
        "incoming_hard_valid_edge_count",
        "sender_spell_age_bin",
        "receiver_spell_age_bin",
        "payload_age",
        "policy_version_distance",
    }
)
FORBIDDEN_VALVE_FIELDS = frozenset(
    {
        "payload",
        "slot",
        "shock",
        "cell_class",
        "time",
        "event",
        "horizon",
        "profile_name",
        "episode_id",
        "member_identity",
        "cluster_id",
        "digest",
        "future_state",
        "future_reward",
        "realized_action",
        "actor_hidden",
        "global_rng",
        "control_tape",
        "evaluation_outcome",
    }
)
FEATURE_DIM = 14


class ValveInputError(ValueError):
    """The detached valve input is missing, extra, nonfinite, or unseen."""


@dataclass(frozen=True)
class ExperimentPlan:
    mode: str
    actor_seeds: tuple[int, ...]
    profiles: tuple[roster_env.RosterProfile, ...]
    train_episodes_per_profile: int
    receipt_roots_per_profile: int
    fit_roots_per_profile: int
    evaluation_roots_per_profile: int

    @property
    def calibration_roots_per_profile(self) -> int:
        return self.receipt_roots_per_profile - self.fit_roots_per_profile

    @property
    def maximum_transitions(self) -> int:
        train = (
            len(self.actor_seeds)
            * len(self.profiles)
            * self.train_episodes_per_profile
            * roster_env.HORIZON
        )
        receipts = (
            len(self.actor_seeds)
            * len(self.profiles)
            * self.receipt_roots_per_profile
            * len(sib.EVENT_TIMES)
            * 2
            * roster_env.HORIZON
        )
        evaluation = (
            len(self.actor_seeds)
            * len(self.profiles)
            * self.evaluation_roots_per_profile
            * len(sib.ARMS)
            * roster_env.HORIZON
        )
        return train + receipts + evaluation


FULL_PLAN = ExperimentPlan(
    "full",
    ACTOR_SEEDS,
    PROFILES,
    train_episodes_per_profile=32,
    receipt_roots_per_profile=12,
    fit_roots_per_profile=9,
    evaluation_roots_per_profile=16,
)
SMOKE_PLAN = ExperimentPlan(
    "smoke",
    ACTOR_SEEDS[:1],
    PROFILES,
    train_episodes_per_profile=1,
    receipt_roots_per_profile=4,
    fit_roots_per_profile=3,
    evaluation_roots_per_profile=2,
)


def plan_for_mode(mode: str) -> ExperimentPlan:
    if mode == "smoke":
        return SMOKE_PLAN
    if mode == "full":
        return FULL_PLAN
    raise ValueError("mode must be 'smoke' or 'full'")


def episode_id(stage: str, actor_index: int, profile_index: int, root: int) -> int:
    bases = {"train": 1_000_000, "receipt": 2_000_000, "evaluation": 3_000_000}
    if stage not in bases or min(actor_index, profile_index, root) < 0:
        raise ValueError("unregistered episode-id coordinate")
    return bases[stage] + actor_index * 100_000 + profile_index * 10_000 + root


def _make_env(
    profile: roster_env.RosterProfile,
    registered_episode_id: int,
) -> sib.EocivSiblingRosterEnv:
    world_seed = sib.profile_stream_identity(
        sib.BASE_WORLD_STREAM, MASTER_SEED, profile.name
    )
    ledger = roster_env.make_ledger(
        registered_episode_id, master_seed=world_seed, profile=profile
    )
    return sib.EocivSiblingRosterEnv(ledger, sibling_seed=SIBLING_SEED)


class RecurrentActorCritic(nn.Module):
    """Small recurrent stochastic continuous actor with a scalar value head."""

    def __init__(self, capacity: int, seed: int, hidden_dim: int = 16):
        super().__init__()
        self.capacity = int(capacity)
        self.seed = int(seed)
        self.hidden_dim = int(hidden_dim)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(self.seed)
            self.obs = nn.Linear(roster_env.OBSERVATION_DIM, hidden_dim, bias=False)
            self.recurrent = nn.Linear(hidden_dim, hidden_dim, bias=False)
            self.slot = nn.Linear(art.SLOT_DIM, hidden_dim, bias=True)
            self.actor = nn.Linear(hidden_dim, roster_env.ACTION_DIM)
            self.value = nn.Linear(hidden_dim, 1)
            self.log_std = nn.Parameter(torch.full((roster_env.ACTION_DIM,), -1.2))
        self._capture = False
        self._graph_hidden: torch.Tensor | None = None
        self._log_probs: list[torch.Tensor] = []
        self._values: list[torch.Tensor] = []

    def set_capture(self, enabled: bool) -> None:
        self._capture = bool(enabled)

    def initial_state(self) -> np.ndarray:
        self._graph_hidden = None
        self._log_probs = []
        self._values = []
        return np.zeros((self.capacity, self.hidden_dim), dtype=np.float32)

    def forward(
        self,
        observations: np.ndarray,
        active_mask: np.ndarray,
        slot_block: np.ndarray,
        hidden: np.ndarray,
        noise: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        obs = torch.as_tensor(observations, dtype=torch.float32)
        mask = torch.as_tensor(active_mask, dtype=torch.bool)
        slots = torch.as_tensor(slot_block, dtype=torch.float32)
        eps = torch.as_tensor(noise, dtype=torch.float32)
        if self._capture and self._graph_hidden is not None:
            previous = self._graph_hidden
        else:
            previous = torch.as_tensor(hidden, dtype=torch.float32)
        candidate = torch.tanh(self.obs(obs) + self.recurrent(previous) + self.slot(slots))
        new_hidden = torch.where(mask[:, None], candidate, previous)
        mean = self.actor(new_hidden)
        std = torch.exp(torch.clamp(self.log_std, -4.0, 1.0))
        raw = mean + std * eps
        action = torch.tanh(raw)
        action = torch.where(mask[:, None], action, torch.zeros_like(action))
        if self._capture:
            distribution = torch.distributions.Normal(mean, std)
            log_prob_rows = distribution.log_prob(raw.detach()).sum(dim=-1)
            active_count = torch.clamp(mask.sum(), min=1)
            self._log_probs.append(log_prob_rows[mask].sum() / active_count)
            pooled = new_hidden[mask].mean(dim=0)
            self._values.append(self.value(pooled).squeeze(-1))
            self._graph_hidden = new_hidden
        else:
            self._graph_hidden = new_hidden.detach()
        return (
            action.detach().cpu().numpy().astype(np.float32),
            mean.detach().cpu().numpy().astype(np.float32),
            new_hidden.detach().cpu().numpy().astype(np.float32),
        )

    def episode_loss(self, rewards: Sequence[float]) -> tuple[torch.Tensor, dict[str, float]]:
        if len(rewards) != len(self._log_probs) or len(rewards) != roster_env.HORIZON:
            raise RuntimeError("actor capture does not match one complete episode")
        returns: list[float] = []
        carry = 0.0
        for reward in reversed(tuple(float(value) for value in rewards)):
            carry = reward + GAMMA * carry
            returns.append(carry)
        returns.reverse()
        target = torch.as_tensor(returns, dtype=torch.float32)
        values = torch.stack(self._values)
        log_probs = torch.stack(self._log_probs)
        advantage = target - values
        actor_loss = -(log_probs * advantage.detach()).mean()
        critic_loss = torch.square(advantage).mean()
        loss = actor_loss + 0.5 * critic_loss
        return loss, {
            "actor_loss": float(actor_loss.detach()),
            "critic_loss": float(critic_loss.detach()),
        }


@dataclass(frozen=True)
class ValveFeatureRecord:
    sender_role: str
    receiver_role: str
    active_member_count: float
    incoming_hard_valid_edge_count: float
    sender_spell_age_bin: str
    receiver_spell_age_bin: str
    payload_age: float = 0.0
    policy_version_distance: float = 0.0


def _role(capability: np.ndarray) -> str:
    values = np.asarray(capability, dtype=np.float32)
    if values.shape != (2,) or not np.isfinite(values).all():
        raise ValveInputError("invalid capability role material")
    return ROLE_NAMES[int(values[1] > values[0])]


def _age_bin(age: int) -> str:
    if age < 0:
        raise ValveInputError("negative spell age")
    if age <= 4:
        return AGE_BINS[0]
    if age <= 16:
        return AGE_BINS[1]
    return AGE_BINS[2]


def feature_record_from_w_minus(
    w_minus_bytes: bytes,
    ledger: roster_env.CapacityRosterLedger,
) -> ValveFeatureRecord:
    """Project the sealed view to the exact detached whitelist.

    The full sealed view is parsed only at this engineering boundary; it is
    never passed to the learner.  The returned immutable record contains no
    payload, route, shock, identity, time, profile, action, reward, or digest.
    """
    decoded = json.loads(w_minus_bytes.decode("utf-8"))
    receiver = decoded["receiver"]
    sender = decoded["source"]
    active_count = int(sum(int(value) for value in decoded["active_mask"]))
    sender_key = int(sender["member_key"])
    receiver_key = int(receiver["member_key"])
    tick = int(decoded["time"])
    record = ValveFeatureRecord(
        sender_role=_role(ledger.capabilities[sender_key]),
        receiver_role=_role(ledger.capabilities[receiver_key]),
        active_member_count=float(active_count),
        incoming_hard_valid_edge_count=float(max(0, active_count - 1)),
        sender_spell_age_bin=_age_bin(tick - int(sender["opened_at"])),
        receiver_spell_age_bin=_age_bin(tick - int(receiver["opened_at"])),
    )
    encode_valve_features(asdict(record))
    return record


def encode_valve_features(material: Mapping[str, object]) -> np.ndarray:
    keys = frozenset(material)
    if keys != FEATURE_KEYS:
        extra = sorted(keys - FEATURE_KEYS)
        missing = sorted(FEATURE_KEYS - keys)
        raise ValveInputError(f"valve feature contract mismatch extra={extra} missing={missing}")
    sender = str(material["sender_role"])
    receiver = str(material["receiver_role"])
    sender_age = str(material["sender_spell_age_bin"])
    receiver_age = str(material["receiver_spell_age_bin"])
    if sender not in ROLE_NAMES or receiver not in ROLE_NAMES:
        raise ValveInputError("unseen capability role")
    if sender_age not in AGE_BINS or receiver_age not in AGE_BINS:
        raise ValveInputError("unseen spell-age bin")
    numeric = np.asarray(
        [
            float(material["active_member_count"]),
            float(material["incoming_hard_valid_edge_count"]),
            float(material["payload_age"]),
            float(material["policy_version_distance"]),
        ],
        dtype=np.float32,
    )
    if not np.isfinite(numeric).all() or numeric[0] <= 0 or numeric[1] < 0:
        raise ValveInputError("nonfinite or invalid numeric valve feature")
    if numeric[2] != 0 or numeric[3] != 0:
        raise ValveInputError("payload age and frozen policy distance must be zero")
    vector = np.concatenate(
        (
            np.eye(2, dtype=np.float32)[ROLE_NAMES.index(sender)],
            np.eye(2, dtype=np.float32)[ROLE_NAMES.index(receiver)],
            numeric[:2] / np.float32(8.0),
            np.eye(3, dtype=np.float32)[AGE_BINS.index(sender_age)],
            np.eye(3, dtype=np.float32)[AGE_BINS.index(receiver_age)],
            numeric[2:],
        )
    )
    if vector.shape != (FEATURE_DIM,) or not np.isfinite(vector).all():
        raise ValveInputError("encoded valve feature mismatch")
    return vector


class DetachedRidgeValve(nn.Module):
    def __init__(self, seed: int):
        super().__init__()
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(int(seed) + 17_000)
            self.linear = nn.Linear(FEATURE_DIM, 1)
        self.fitted = False
        self.support = {"positive": 0, "negative": 0}
        self.optimizer_steps = 0

    def fit(self, records: Sequence[ValveFeatureRecord], labels: Sequence[int]) -> None:
        y = np.asarray(labels, dtype=np.float32)
        self.support = {"positive": int(np.count_nonzero(y == 1)), "negative": int(np.count_nonzero(y == 0))}
        if not self.support["positive"] or not self.support["negative"]:
            self.fitted = False
            return
        x = np.stack([encode_valve_features(asdict(record)) for record in records])
        features = torch.as_tensor(x, dtype=torch.float32).detach()
        targets = torch.as_tensor(y[:, None], dtype=torch.float32).detach()
        optimizer = torch.optim.Adam(self.parameters(), lr=VALVE_LR)
        for _ in range(VALVE_STEPS):
            optimizer.zero_grad(set_to_none=True)
            logits = self.linear(features)
            ridge = VALVE_L2 * torch.square(self.linear.weight).sum()
            loss = nn.functional.binary_cross_entropy_with_logits(logits, targets) + ridge
            loss.backward()
            optimizer.step()
            self.optimizer_steps += 1
        self.fitted = True

    def decide(self, record: ValveFeatureRecord) -> tuple[bool, float | None, str]:
        if not self.fitted:
            return True, None, "SUPPORT_MISSING"
        try:
            vector = encode_valve_features(asdict(record))
        except (ValveInputError, TypeError, ValueError):
            return True, None, "HARD_OPEN"
        with torch.no_grad():
            score = float(torch.sigmoid(self.linear(torch.as_tensor(vector))).item())
        if not np.isfinite(score):
            return True, None, "HARD_OPEN"
        return bool(score >= VALVE_THRESHOLD), score, "LEARNED"


class _DecisionRecorder:
    def __init__(
        self,
        ledger: roster_env.CapacityRosterLedger,
        decisions: Sequence[bool] | Callable[[ValveFeatureRecord, int], bool],
    ):
        self.ledger = ledger
        self.decisions = decisions
        self.records: list[ValveFeatureRecord] = []

    def __call__(self, w_minus_bytes: bytes) -> bool:
        record = feature_record_from_w_minus(w_minus_bytes, self.ledger)
        index = len(self.records)
        if index >= len(sib.EVENT_TIMES):
            raise RuntimeError("more lifecycle decisions than registered events")
        self.records.append(record)
        if callable(self.decisions):
            return bool(self.decisions(record, index))
        if len(self.decisions) != len(sib.EVENT_TIMES):
            raise ValueError("one route decision per lifecycle event required")
        return bool(self.decisions[index])


def _run_episode(
    profile: roster_env.RosterProfile,
    registered_episode_id: int,
    actor: RecurrentActorCritic,
    arm: str,
    decisions: Sequence[bool] | Callable[[ValveFeatureRecord, int], bool],
) -> tuple[art.ArmEpisodeRunner, _DecisionRecorder]:
    env = _make_env(profile, registered_episode_id)
    recorder = _DecisionRecorder(env.ledger, decisions)
    actor.set_capture(False)
    runner = art.ArmEpisodeRunner(
        env,
        arm,
        tape_seed=TAPE_SEED,
        d_learned_fn=(lambda _: True) if arm == "CS" else recorder,
        d_control_fn=recorder if arm == "CS" else None,
        policy=actor,
    )
    runner.run_episode()
    return runner, recorder


def _payload_sensitivity(actor: RecurrentActorCritic) -> float:
    actor.set_capture(False)
    observations = np.zeros((actor.capacity, roster_env.OBSERVATION_DIM), dtype=np.float32)
    active = np.ones(actor.capacity, dtype=np.bool_)
    noise = np.zeros((actor.capacity, roster_env.ACTION_DIM), dtype=np.float32)
    slot_a = np.zeros((actor.capacity, art.SLOT_DIM), dtype=np.float32)
    slot_b = slot_a.copy()
    slot_a[0] = art.slot_features(sib._pad_slot(sib.real_payload_body(sib.SHOCK_A)))
    slot_b[0] = art.slot_features(sib._pad_slot(sib.real_payload_body(sib.SHOCK_B)))
    hidden = actor.initial_state()
    action_a, _, _ = actor.forward(observations, active, slot_a, hidden, noise)
    hidden = actor.initial_state()
    action_b, _, _ = actor.forward(observations, active, slot_b, hidden, noise)
    return float(np.abs(action_a[0] - action_b[0]).mean())


def _train_actor(
    actor: RecurrentActorCritic,
    actor_index: int,
    plan: ExperimentPlan,
    counts: dict[str, int],
) -> dict[str, object]:
    optimizer = torch.optim.Adam(actor.parameters(), lr=ACTOR_LR)
    returns: list[dict[str, object]] = []
    pre = _payload_sensitivity(actor)
    for profile_index, profile in enumerate(plan.profiles):
        for root in range(plan.train_episodes_per_profile):
            registered_id = episode_id("train", actor_index, profile_index, root)
            env = _make_env(profile, registered_id)
            actor.set_capture(True)
            runner = art.ArmEpisodeRunner(
                env,
                "LR",
                tape_seed=TAPE_SEED,
                d_learned_fn=lambda _: True,
                policy=actor,
            )
            runner.run_episode()
            optimizer.zero_grad(set_to_none=True)
            loss, loss_parts = actor.episode_loss(env.reward_trace)
            loss.backward()
            grad_norm = float(nn.utils.clip_grad_norm_(actor.parameters(), GRAD_NORM_CAP))
            optimizer.step()
            counts["environment_transitions"] += roster_env.HORIZON
            counts["policy_calls"] += roster_env.HORIZON
            counts["actor_critic_optimizer_steps"] += 1
            counts["training_episodes"] += 1
            returns.append(
                {
                    "profile": profile.name,
                    "episode_id": registered_id,
                    "return": float(sum(env.reward_trace)),
                    "grad_norm_before_clip": grad_norm,
                    **loss_parts,
                }
            )
    actor.set_capture(False)
    for parameter in actor.parameters():
        parameter.requires_grad_(False)
        parameter.grad = None
    return {
        "pre_payload_sensitivity": pre,
        "post_payload_sensitivity": _payload_sensitivity(actor),
        "episodes": returns,
    }


def _same_root(a: sib.EocivSiblingRosterEnv, b: sib.EocivSiblingRosterEnv) -> bool:
    left, right = a.ledger, b.ledger
    return bool(
        left.episode_id == right.episode_id
        and left.profile == right.profile
        and left.initial_keys == right.initial_keys
        and left.temporarily_absent == right.temporarily_absent
        and left.fresh_join == right.fresh_join
        and left.terminal_leave == right.terminal_leave
        and np.array_equal(left.capabilities, right.capabilities)
        and np.array_equal(left.load, right.load)
        and np.array_equal(left.target_mix, right.target_mix)
        and a._shock_states == b._shock_states
    )


def _build_receipts(
    actor: RecurrentActorCritic,
    actor_index: int,
    plan: ExperimentPlan,
    counts: dict[str, int],
) -> tuple[list[ValveFeatureRecord], list[int], dict[str, list[ValveFeatureRecord]], list[dict[str, object]]]:
    fit_records: list[ValveFeatureRecord] = []
    fit_labels: list[int] = []
    calibration: dict[str, list[ValveFeatureRecord]] = {profile.name: [] for profile in plan.profiles}
    raw: list[dict[str, object]] = []
    for profile_index, profile in enumerate(plan.profiles):
        for root in range(plan.receipt_roots_per_profile):
            registered_id = episode_id("receipt", actor_index, profile_index, root)
            for focal in range(len(sib.EVENT_TIMES)):
                all_real = [True] * len(sib.EVENT_TIMES)
                focal_neutral = all_real.copy()
                focal_neutral[focal] = False
                real_runner, real_recorder = _run_episode(
                    profile, registered_id, actor, "LS", all_real
                )
                neutral_runner, _ = _run_episode(
                    profile, registered_id, actor, "LS", focal_neutral
                )
                if not _same_root(real_runner.env, neutral_runner.env):
                    raise RuntimeError("paired receipt clones do not share root material")
                start = sib.EVENT_TIMES[focal]
                stop = start + sib.SEGMENT_LENGTH
                delta = float(
                    sum(real_runner.env.reward_trace[start:stop])
                    - sum(neutral_runner.env.reward_trace[start:stop])
                )
                record = real_recorder.records[focal]
                label = int(delta > 0.0)
                if root < plan.fit_roots_per_profile:
                    fit_records.append(record)
                    fit_labels.append(label)
                    split = "fit"
                else:
                    calibration[profile.name].append(record)
                    split = "calibration"
                raw.append(
                    {
                        "profile": profile.name,
                        "episode_id": registered_id,
                        "event_index": focal,
                        "split": split,
                        "delta_reveal": delta,
                        "label": label,
                        "shared_root_material": True,
                        "real_route": real_runner.boundary_records[focal].actuation_route,
                        "neutral_route": neutral_runner.boundary_records[focal].actuation_route,
                        "focal_action_changed": (
                            real_runner.step_traces[start].action_digest
                            != neutral_runner.step_traces[start].action_digest
                        ),
                    }
                )
                counts["environment_transitions"] += 2 * roster_env.HORIZON
                counts["policy_calls"] += 2 * roster_env.HORIZON
                counts["receipt_clone_episodes"] += 2
    return fit_records, fit_labels, calibration, raw


def _control_schedule(
    actor_seed: int,
    profile_name: str,
    root_count: int,
    learned_calibration_close_count: int,
    calibration_event_count: int,
) -> tuple[dict[tuple[int, int], bool], int]:
    coordinates = [
        (root, event)
        for root in range(root_count)
        for event in range(len(sib.EVENT_TIMES))
    ]
    if calibration_event_count <= 0:
        close_count = 0
    else:
        close_count = int(
            np.floor(
                len(coordinates)
                * learned_calibration_close_count
                / calibration_event_count
                + 0.5
            )
        )
    ranked = sorted(
        coordinates,
        key=lambda coordinate: hashlib.sha256(
            (
                f"EOCIV-B1-CONTROL|{actor_seed}|{profile_name}|"
                f"{coordinate[0]}|{coordinate[1]}"
            ).encode("ascii")
        ).digest(),
    )
    closed = set(ranked[:close_count])
    return ({coordinate: coordinate not in closed for coordinate in coordinates}, close_count)


def _evaluate(
    actor: RecurrentActorCritic,
    valve: DetachedRidgeValve,
    actor_index: int,
    actor_seed: int,
    plan: ExperimentPlan,
    calibration: Mapping[str, Sequence[ValveFeatureRecord]],
    counts: dict[str, int],
) -> tuple[list[dict[str, object]], list[float], dict[str, object]]:
    raw: list[dict[str, object]] = []
    block_effects: list[float] = []
    diagnostics: dict[str, object] = {}
    for profile_index, profile in enumerate(plan.profiles):
        calibration_decisions = [valve.decide(record)[0] for record in calibration[profile.name]]
        calibration_close = int(sum(not value for value in calibration_decisions))
        schedule, target_close = _control_schedule(
            actor_seed,
            profile.name,
            plan.evaluation_roots_per_profile,
            calibration_close,
            len(calibration_decisions),
        )
        actual_control_close = 0
        learned_eval_close = 0
        fallback = 0
        for root in range(plan.evaluation_roots_per_profile):
            registered_id = episode_id("evaluation", actor_index, profile_index, root)
            learned_statuses: list[dict[str, object]] = []

            def learned_decision(record: ValveFeatureRecord, event: int) -> bool:
                nonlocal learned_eval_close, fallback
                decision, score, status = valve.decide(record)
                learned_eval_close += int(not decision)
                fallback += int(status != "LEARNED")
                learned_statuses.append({"event_index": event, "open": decision, "score": score, "status": status})
                return decision

            control_decisions = [schedule[(root, event)] for event in range(len(sib.EVENT_TIMES))]
            runners: dict[str, art.ArmEpisodeRunner] = {}
            runners["LS"], _ = _run_episode(profile, registered_id, actor, "LS", learned_decision)
            runners["LR"], _ = _run_episode(profile, registered_id, actor, "LR", [True] * 3)
            runners["CS"], _ = _run_episode(profile, registered_id, actor, "CS", control_decisions)
            runners["CR"], _ = _run_episode(profile, registered_id, actor, "CR", [True] * 3)
            actual_control_close += sum(
                record.actuation_route == "NEUTRAL"
                for record in runners["CS"].boundary_records
            )
            if runners["LR"].step_traces != runners["CR"].step_traces:
                raise RuntimeError("LR/CR step traces differ under one paired block")
            values = {
                arm: float(np.mean(runner.env.reward_trace[sib.EVENT_TIMES[0] :]))
                for arm, runner in runners.items()
            }
            effect = (values["LS"] - values["LR"]) - (values["CS"] - values["CR"])
            block_effects.append(effect)
            raw.append(
                {
                    "actor_seed": actor_seed,
                    "profile": profile.name,
                    "episode_id": registered_id,
                    "arms": {
                        arm: {
                            "post_event_mean": values[arm],
                            "reward_trace": [float(value) for value in runner.env.reward_trace],
                            "routes": [record.actuation_route for record in runner.boundary_records],
                        }
                        for arm, runner in runners.items()
                    },
                    "learned_decisions": learned_statuses,
                    "control_decisions": control_decisions,
                    "lr_cr_identical": True,
                    "ls_lr_action_trace_changes": sum(
                        left.action_digest != right.action_digest
                        for left, right in zip(runners["LS"].step_traces, runners["LR"].step_traces)
                    ),
                    "block_effect": effect,
                }
            )
            counts["environment_transitions"] += len(sib.ARMS) * roster_env.HORIZON
            counts["policy_calls"] += len(sib.ARMS) * roster_env.HORIZON
            counts["evaluation_episodes"] += len(sib.ARMS)
        if actual_control_close != target_close:
            raise RuntimeError("exact-rate control close count mismatch")
        diagnostics[profile.name] = {
            "calibration_close_count": calibration_close,
            "calibration_event_count": len(calibration_decisions),
            "control_target_close_count": target_close,
            "control_actual_close_count": actual_control_close,
            "learned_evaluation_close_count": learned_eval_close,
            "fallback_count": fallback,
        }
        counts["valve_fallback_events"] += fallback
    return raw, block_effects, diagnostics


def _status(
    actor_diagnostics: Sequence[Mapping[str, object]],
    valves: Sequence[DetachedRidgeValve],
    block_effects: Sequence[float],
) -> str:
    if any(not np.isfinite(float(value)) for value in block_effects):
        return "INVALID_PAIRING_OR_CONTROL"
    if any(not valve.fitted for valve in valves):
        return "VALVE_SUPPORT_MISSING"
    if not any(float(row["post_payload_sensitivity"]) > 0.0 for row in actor_diagnostics):
        return "ACTOR_CAPABILITY_MISSING"
    tau = float(np.mean(block_effects))
    if tau > 0:
        return "VALID_POSITIVE_SIGNAL"
    if tau < 0:
        return "VALID_NEGATIVE_SIGNAL"
    return "VALID_ZERO_SIGNAL"


def run_experiment(mode: str = "smoke") -> dict[str, object]:
    plan = plan_for_mode(mode)
    if FULL_PLAN.maximum_transitions != 72_576:
        raise RuntimeError("registered full transition maximum drifted")
    counts = {
        "environment_transitions": 0,
        "policy_calls": 0,
        "actor_critic_optimizer_steps": 0,
        "valve_optimizer_steps": 0,
        "training_episodes": 0,
        "receipt_clone_episodes": 0,
        "evaluation_episodes": 0,
        "valve_fallback_events": 0,
    }
    actor_rows: list[dict[str, object]] = []
    receipt_rows: list[dict[str, object]] = []
    evaluation_rows: list[dict[str, object]] = []
    evaluation_diagnostics: dict[str, object] = {}
    effects: list[float] = []
    valves: list[DetachedRidgeValve] = []
    for actor_index, seed in enumerate(plan.actor_seeds):
        actor = RecurrentActorCritic(PROFILES[0].member_capacity, seed)
        actor_row = _train_actor(actor, actor_index, plan, counts)
        actor_row["actor_seed"] = seed
        actor_rows.append(actor_row)
        fit_records, fit_labels, calibration, receipts = _build_receipts(
            actor, actor_index, plan, counts
        )
        receipt_rows.extend({"actor_seed": seed, **row} for row in receipts)
        valve = DetachedRidgeValve(seed)
        valve.fit(fit_records, fit_labels)
        valves.append(valve)
        counts["valve_optimizer_steps"] += valve.optimizer_steps
        rows, actor_effects, diagnostics = _evaluate(
            actor,
            valve,
            actor_index,
            seed,
            plan,
            calibration,
            counts,
        )
        evaluation_rows.extend(rows)
        effects.extend(actor_effects)
        evaluation_diagnostics[str(seed)] = {
            "fit_support": valve.support,
            "fitted": valve.fitted,
            "optimizer_steps": valve.optimizer_steps,
            "profiles": diagnostics,
        }
    if counts["environment_transitions"] != plan.maximum_transitions:
        raise RuntimeError("actual environment count differs from frozen plan")
    if counts["policy_calls"] != counts["environment_transitions"]:
        raise RuntimeError("one real policy call per environment transition required")
    tau = float(np.mean(effects)) if effects else 0.0
    result = {
        "treatment": TREATMENT,
        "stage": "B_EXPLORATORY_REAL_TOY_EXPERIMENT",
        "mode": mode,
        "registered_c_outcome_experiment_licensed": capability_gate.REGISTERED_OUTCOME_EXPERIMENT["licensed"],
        "real_implementation": True,
        "real_environment_calls": counts["environment_transitions"] > 0,
        "real_policy_calls": counts["policy_calls"] > 0,
        "real_actor_learner_updates": counts["actor_critic_optimizer_steps"] > 0,
        "real_valve_learner_updates": counts["valve_optimizer_steps"] > 0,
        "real_evaluation_runner_calls": counts["evaluation_episodes"] > 0,
        "configuration": {
            "actor_seeds": list(plan.actor_seeds),
            "profiles": [profile.name for profile in plan.profiles],
            "horizon": roster_env.HORIZON,
            "event_times": list(sib.EVENT_TIMES),
            "actor_lr": ACTOR_LR,
            "gamma": GAMMA,
            "grad_norm_cap": GRAD_NORM_CAP,
            "valve_lr": VALVE_LR,
            "valve_l2": VALVE_L2,
            "valve_steps": VALVE_STEPS,
            "valve_threshold": VALVE_THRESHOLD,
            "train_episodes_per_profile": plan.train_episodes_per_profile,
            "receipt_roots_per_profile": plan.receipt_roots_per_profile,
            "fit_roots_per_profile": plan.fit_roots_per_profile,
            "calibration_roots_per_profile": plan.calibration_roots_per_profile,
            "evaluation_roots_per_profile": plan.evaluation_roots_per_profile,
            "maximum_transitions": plan.maximum_transitions,
            "episode_id_ranges": {
                "train": "1000000 + actor_index*100000 + profile_index*10000 + root",
                "receipt": "2000000 + actor_index*100000 + profile_index*10000 + root",
                "evaluation": "3000000 + actor_index*100000 + profile_index*10000 + root",
            },
            "namespaces": {
                "actor_initialization": "torch-local actor_seed",
                "base_world": sib.BASE_WORLD_STREAM,
                "action_noise": sib.ACTION_NOISE_STREAM,
                "control": "EOCIV-B1-CONTROL",
            },
            "valve_feature_keys": sorted(FEATURE_KEYS),
            "forbidden_valve_fields": sorted(FORBIDDEN_VALVE_FIELDS),
        },
        "counts": counts,
        "actor_training": actor_rows,
        "receipt_rows": receipt_rows,
        "evaluation_rows": evaluation_rows,
        "evaluation_diagnostics": evaluation_diagnostics,
        "primary": {
            "tau_B1": tau,
            "block_count": len(effects),
            "block_effects": effects,
        },
        "mechanical_status": _status(actor_rows, valves, effects),
        "interpretation_boundary": (
            "B-level descriptive diagnostic only; zero/negative signal, one-sided support, "
            "actor insensitivity, instability, or learned/control equivalence is not a "
            "promotion, retirement, deployment, or host-direction pause decision."
        ),
    }
    return result


def write_result(result: Mapping[str, object], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

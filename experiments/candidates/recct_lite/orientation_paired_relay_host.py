"""Real reset/step host for RECCT-B1 orientation-paired relay cancellation.

The host owns roster churn, graph-role assignment, slot permutation, cues,
message delivery, and rewards.  It deliberately exposes no orientation,
instance, slot, seed, capsule, or useful-edge coordinate in policy
observations.  Recurrent state is learner-owned; ``state_reset`` tells the
caller exactly when a fresh or rejoining occupant must start from zero.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np


HOST_ID = "RECCT-OrientationPairedRelayCancellation-v1"
ROLES = ("L", "R", "D")
PHASES_PER_EPOCH = 4
ROSTER_EPOCHS = 8
JOINT_STEPS = PHASES_PER_EPOCH * ROSTER_EPOCHS
ACTIVE_COUNT_BY_EPOCH = (3, 2, 3, 2, 3, 2, 3, 2)
OBSERVATION_DIM = 15
ACTION_NVECS = (2, 2)
TRAINING_POOL = tuple(f"T{index}" for index in range(8))
EVALUATION_POOL = tuple(f"E{index}" for index in range(8))
FORBIDDEN_OBSERVATION_FIELDS = (
    "instance_id",
    "slot_id",
    "omega",
    "seed",
    "capsule_digest",
    "useful_edge_label",
)
OBSERVATION_FIELDS = (
    "phase_one_hot_4",
    "graph_role_one_hot_3",
    "active_count_one_hot_2",
    "cue_visible",
    "cue_value_or_zero",
    "incoming_message_or_zero",
    "previous_epoch_reward",
    "survivor_flag",
    "rejoin_flag",
)


def _digest(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class Occupant:
    """Host-private lifecycle identity; never part of a policy observation."""

    token: str
    role: str
    survivor: bool
    rejoin: bool


@dataclass(frozen=True)
class EpochPlan:
    epoch: int
    cue: int
    occupants_by_role: tuple[tuple[str, Occupant], ...]
    slot_roles: tuple[str, ...]

    def occupant(self, role: str) -> Occupant:
        return dict(self.occupants_by_role)[role]


@dataclass(frozen=True)
class EpisodePlan:
    episode_seed: int
    orientation: int
    pool: tuple[str, ...]
    epochs: tuple[EpochPlan, ...]
    exogenous_digest: str

    def complemented(self) -> "EpisodePlan":
        return EpisodePlan(
            episode_seed=self.episode_seed,
            orientation=-self.orientation,
            pool=self.pool,
            epochs=self.epochs,
            exogenous_digest=self.exogenous_digest,
        )


@dataclass(frozen=True)
class HostStep:
    observations: np.ndarray
    active_roles: tuple[str, ...]
    occupant_tokens: tuple[str, ...]
    state_reset: tuple[bool, ...]
    rewards: np.ndarray
    terminal_reward: float
    done: bool
    epoch: int
    phase: int
    cue: int


def make_episode_plan(
    episode_seed: int,
    orientation: int,
    pool: Sequence[str],
) -> EpisodePlan:
    """Create one exogenous plan; orientation cannot affect its RNG draws."""

    if int(orientation) not in (-1, 1):
        raise ValueError("orientation must be -1 or +1")
    pool_tuple = tuple(str(row) for row in pool)
    if len(pool_tuple) != 8 or len(set(pool_tuple)) != 8:
        raise ValueError("relay host requires one unique eight-instance pool")
    if set(pool_tuple).intersection(TRAINING_POOL) and set(pool_tuple) != set(
        TRAINING_POOL
    ):
        raise ValueError("training pool may not be partially mixed")
    if set(pool_tuple).intersection(EVALUATION_POOL) and set(pool_tuple) != set(
        EVALUATION_POOL
    ):
        raise ValueError("evaluation pool may not be partially mixed")

    rng = np.random.default_rng(int(episode_seed))
    # The same finite pool may recur under churn.  Tokens bind lifecycle visits,
    # while the policy sees only graph role and survivor/rejoin flags.
    visit = {name: 0 for name in pool_tuple}
    next_pool = 0

    def fresh(role: str, *, rejoin: bool) -> Occupant:
        nonlocal next_pool
        base = pool_tuple[next_pool % len(pool_tuple)]
        next_pool += 1
        visit[base] += 1
        return Occupant(
            token=f"{base}:visit-{visit[base]}",
            role=role,
            survivor=False,
            rejoin=bool(rejoin),
        )

    live: dict[str, Occupant] = {
        role: fresh(role, rejoin=False) for role in ROLES
    }
    retired: list[Occupant] = []
    d_retired: Occupant | None = None
    rows: list[EpochPlan] = []
    for epoch, active_count in enumerate(ACTIVE_COUNT_BY_EPOCH):
        if epoch > 0:
            replacement_role = "L" if epoch % 2 == 1 else "R"
            retired.append(live[replacement_role])
            replacement_is_rejoin = epoch % 2 == 0
            if replacement_is_rejoin and retired:
                previous = retired.pop(0)
                base = previous.token.split(":", 1)[0]
                visit[base] += 1
                live[replacement_role] = Occupant(
                    token=f"{base}:visit-{visit[base]}",
                    role=replacement_role,
                    survivor=False,
                    rejoin=True,
                )
            else:
                live[replacement_role] = fresh(
                    replacement_role, rejoin=False
                )

            if active_count == 2:
                d_retired = live.pop("D", d_retired)
            elif "D" not in live:
                if d_retired is None:
                    live["D"] = fresh("D", rejoin=False)
                else:
                    base = d_retired.token.split(":", 1)[0]
                    visit[base] += 1
                    live["D"] = Occupant(
                        token=f"{base}:visit-{visit[base]}",
                        role="D",
                        survivor=False,
                        rejoin=True,
                    )
                    d_retired = None

        active_roles = tuple(role for role in ROLES if role in live)
        permuted = tuple(active_roles[index] for index in rng.permutation(len(active_roles)))
        cue = int(rng.choice(np.asarray((-1, 1), dtype=np.int8)))
        epoch_rows: list[tuple[str, Occupant]] = []
        for role in active_roles:
            occupant = live[role]
            if epoch == 0:
                row = occupant
            elif occupant.survivor or not (
                occupant.token.endswith(f"visit-{visit[occupant.token.split(':', 1)[0]]}")
            ):
                row = Occupant(occupant.token, role, True, False)
            else:
                row = occupant
            epoch_rows.append((role, row))
        # Any occupant that was already live at the previous boundary survives.
        if epoch > 0:
            prior_tokens = {
                occupant.token
                for _, occupant in rows[-1].occupants_by_role
            }
            epoch_rows = [
                (
                    role,
                    occupant
                    if occupant.token not in prior_tokens
                    else Occupant(occupant.token, role, True, False),
                )
                for role, occupant in epoch_rows
            ]
        live = {role: occupant for role, occupant in epoch_rows}
        rows.append(
            EpochPlan(
                epoch=epoch,
                cue=cue,
                occupants_by_role=tuple(epoch_rows),
                slot_roles=permuted,
            )
        )

    exogenous = tuple(
        (
            row.epoch,
            row.cue,
            tuple(
                (role, occupant.token, occupant.survivor, occupant.rejoin)
                for role, occupant in row.occupants_by_role
            ),
            row.slot_roles,
        )
        for row in rows
    )
    return EpisodePlan(
        episode_seed=int(episode_seed),
        orientation=int(orientation),
        pool=pool_tuple,
        epochs=tuple(rows),
        exogenous_digest=_digest(exogenous),
    )


class OrientationPairedRelayHost:
    """Finite real environment with a conventional ``reset``/``step`` API."""

    observation_dim = OBSERVATION_DIM
    action_nvecs = ACTION_NVECS

    def __init__(self) -> None:
        self._plan: EpisodePlan | None = None
        self._step = 0
        self._message = 0
        self._previous_epoch_reward = 0.0

    @property
    def plan(self) -> EpisodePlan:
        if self._plan is None:
            raise RuntimeError("host must be reset before use")
        return self._plan

    def reset(self, plan: EpisodePlan) -> HostStep:
        validate_episode_plan(plan)
        self._plan = plan
        self._step = 0
        self._message = 0
        self._previous_epoch_reward = 0.0
        return self._current_step(
            np.zeros((len(plan.epochs[0].slot_roles),), dtype=np.float32),
            terminal_reward=0.0,
        )

    def step(self, actions: np.ndarray) -> HostStep:
        current = self._metadata()
        action_rows = np.asarray(actions, dtype=np.int64)
        if action_rows.shape != (len(current.slot_roles), 2):
            raise ValueError("actions must match active slots and MultiDiscrete([2,2])")
        if bool(((action_rows < 0) | (action_rows > 1)).any()):
            raise ValueError("each action component must be encoded as 0 or 1")
        mapped = 2 * action_rows - 1
        source, receiver = self._source_receiver()
        slot_by_role = {role: index for index, role in enumerate(current.slot_roles)}
        phase = self._step % PHASES_PER_EPOCH
        terminal_reward = 0.0
        if phase == 0:
            self._message = int(mapped[slot_by_role[source], 0])
        elif phase == 3:
            prediction = int(mapped[slot_by_role[receiver], 1])
            terminal_reward = float(prediction == current.cue)
            self._previous_epoch_reward = terminal_reward
        rewards = np.full(
            (len(current.slot_roles),), terminal_reward, dtype=np.float32
        )
        self._step += 1
        done = self._step == JOINT_STEPS
        if done:
            return HostStep(
                observations=np.zeros((0, OBSERVATION_DIM), dtype=np.float32),
                active_roles=(),
                occupant_tokens=(),
                state_reset=(),
                rewards=rewards,
                terminal_reward=terminal_reward,
                done=True,
                epoch=ROSTER_EPOCHS - 1,
                phase=3,
                cue=current.cue,
            )
        return self._current_step(rewards, terminal_reward=terminal_reward)

    def _metadata(self) -> EpochPlan:
        return self.plan.epochs[self._step // PHASES_PER_EPOCH]

    def _source_receiver(self) -> tuple[str, str]:
        return ("L", "R") if self.plan.orientation == 1 else ("R", "L")

    def _current_step(
        self, rewards: np.ndarray, *, terminal_reward: float
    ) -> HostStep:
        epoch_row = self._metadata()
        phase = self._step % PHASES_PER_EPOCH
        source, receiver = self._source_receiver()
        observations = []
        tokens = []
        resets = []
        for role in epoch_row.slot_roles:
            occupant = epoch_row.occupant(role)
            row = np.zeros((OBSERVATION_DIM,), dtype=np.float32)
            row[phase] = 1.0
            row[4 + ROLES.index(role)] = 1.0
            row[7 + (len(epoch_row.slot_roles) - 2)] = 1.0
            cue_visible = phase == 0 and role == source
            row[9] = float(cue_visible)
            row[10] = float(epoch_row.cue if cue_visible else 0)
            row[11] = float(self._message if phase == 1 and role == receiver else 0)
            row[12] = float(self._previous_epoch_reward)
            row[13] = float(occupant.survivor)
            row[14] = float(occupant.rejoin)
            observations.append(row)
            tokens.append(occupant.token)
            resets.append(bool(phase == 0 and not occupant.survivor))
        return HostStep(
            observations=np.stack(observations),
            active_roles=epoch_row.slot_roles,
            occupant_tokens=tuple(tokens),
            state_reset=tuple(resets),
            rewards=np.asarray(rewards, dtype=np.float32),
            terminal_reward=float(terminal_reward),
            done=False,
            epoch=epoch_row.epoch,
            phase=phase,
            cue=epoch_row.cue,
        )


def validate_episode_plan(plan: EpisodePlan) -> None:
    if plan.orientation not in (-1, 1):
        raise ValueError("invalid orientation")
    if len(plan.epochs) != ROSTER_EPOCHS:
        raise ValueError("episode plan must contain eight roster epochs")
    if set(plan.pool).intersection(TRAINING_POOL) and set(plan.pool).intersection(
        EVALUATION_POOL
    ):
        raise ValueError("training and evaluation identities may not overlap")
    exogenous = tuple(
        (
            row.epoch,
            row.cue,
            tuple(
                (role, occupant.token, occupant.survivor, occupant.rejoin)
                for role, occupant in row.occupants_by_role
            ),
            row.slot_roles,
        )
        for row in plan.epochs
    )
    if _digest(exogenous) != plan.exogenous_digest:
        raise ValueError("episode exogenous plan digest mismatch")
    for epoch, (row, count) in enumerate(zip(plan.epochs, ACTIVE_COUNT_BY_EPOCH)):
        roles = tuple(role for role, _ in row.occupants_by_role)
        if row.epoch != epoch or set(roles) != set(row.slot_roles):
            raise ValueError("epoch role/slot permutation mismatch")
        if len(roles) != count or "L" not in roles or "R" not in roles:
            raise ValueError("epoch active-count or relay occupancy mismatch")
        if row.cue not in (-1, 1):
            raise ValueError("cue left {-1,+1}")


def validate_orientation_pair(plus: EpisodePlan, minus: EpisodePlan) -> None:
    validate_episode_plan(plus)
    validate_episode_plan(minus)
    if (
        plus.orientation != 1
        or minus.orientation != -1
        or plus.episode_seed != minus.episode_seed
        or plus.pool != minus.pool
        or plus.exogenous_digest != minus.exogenous_digest
        or plus.epochs != minus.epochs
    ):
        raise ValueError("orientation replicas are not exact exogenous complements")


def observation_schema() -> Mapping[str, object]:
    return {
        "dimension": OBSERVATION_DIM,
        "fields": OBSERVATION_FIELDS,
        "forbidden": FORBIDDEN_OBSERVATION_FIELDS,
        "action_nvecs": ACTION_NVECS,
    }

"""VSP02-B1V2 learned cue-conditioned lifecycle control.

The environment below is an episodic reset/step host built on the accepted A1
claim and boundary primitives.  It intentionally does not import the A2
enumerator: physical rewards are emitted by the host, never used as labels or
initial values, and evaluation acts through the same host as training.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from decimal import Decimal
from enum import Enum
import hashlib
import json
import math
import random
from typing import Any, Iterable, Mapping, Sequence

import torch
from torch import Tensor, nn

from experiments.candidates.vsp_02 import owner_action_responsive_lifecycle as a1


B1_SCHEMA_VERSION = 2
B1_ASSIGNMENT_ID = "VSP02-B1V2-LEARNED-CUE-CONDITIONED-LIFECYCLE-CONTROL"
B1_CANDIDATE = "CAND-VSP-02@adversarial-revision-v8"
B1_HOST_ID = "VSP02-A2-PHYSICAL-LIFECYCLE-HOST-v1"
B1_RESOURCE_CLASS = "B_TOY_LIGHT"
B1_POOL_UNITS = 1
B1_SLOT = 3
B1_OWNER_ID = "owner-A"
B1_BEHAVIOR_VERSION = 8
B1_VISIBLE_ROSTER = ("owner-A", "partner-B")
B1_PRIMITIVE = "FROZEN_PRIMITIVE_V1"
B1_PARTNER_POLICY = "FROZEN_PARTNER_NOOP_V1"
B1_HORIZON = 4
B1_GAMMA = 0.5
B1_HIDDEN_SIZE = 16
B1_TRAIN_BLOCKS = 16
B1_BLOCK_EPISODES = 64
B1_TRAIN_EPISODES = 1024
B1_BATCH_SIZE = 32
B1_NEURAL_STEPS = 32
B1_EVAL_EPOCHS = tuple(f"EV-{index:02d}" for index in range(16))
B1_TRAIN_EPOCHS = tuple(f"TR-{index:02d}" for index in range(32))
B1_SEED_IDS = tuple(f"VSP02-B1-20260809-S{index:02d}" for index in range(5))
B1_RNG_STREAMS = ("init", "action", "episode_order", "cue_shuffle")
B1_NEURAL_ARMS = (
    "FULL_LIFECYCLE_GRU_ACTOR_CRITIC",
    "CUE_BLIND_GRU",
    "CUE_SHUFFLED_GRU",
    "CURRENT_ONLY_GRU",
)
B1_TABULAR_ARMS = (
    "X_MEMORY_TABULAR_MONTE_CARLO",
    "RAW_HISTORY_TABULAR_MEMORIZER",
)
B1_LEARNED_ARMS = (
    "FULL_LIFECYCLE_GRU_ACTOR_CRITIC",
    "X_MEMORY_TABULAR_MONTE_CARLO",
    "CUE_BLIND_GRU",
    "CUE_SHUFFLED_GRU",
    "CURRENT_ONLY_GRU",
    "RAW_HISTORY_TABULAR_MEMORIZER",
)
B1_FIXED_ARMS = ("ALWAYS_RELEASE", "ALWAYS_HOLD", "UNIFORM_RANDOM")
B1_ORACLE = "EVALUATOR_ONLY_ORACLE"
B1_TERMINAL_PRECEDENCE = a1.TERMINAL_PRECEDENCE
B1_OBSERVATION_FIELDS = (
    "committed_phase",
    "prior_acknowledgements",
    "physical_clock",
    "primitive_clock",
    "own_boundary_clock",
    "owner_epoch_token",
    "visible_roster",
    "primitive_policy",
    "partner_policy",
    "cue_mask",
    "cue_value",
)
B1_FORBIDDEN_OBSERVATION_FIELDS = frozenset(
    {
        "a2_q",
        "a2_branch",
        "optimal_action",
        "future_terminal_tape",
        "future_reward_tape",
        "unreleased_return",
        "target",
        "treatment_identity",
        "future_outcome",
        "authoritative_membership",
        "true_cue",
    }
)
B1_BRANCH_PRECEDENCE = (
    "B1V2_INVALID_HOST_OR_INFORMATION_LEAK",
    "B1V2_ACTIVITY_OR_SUPPORT_INSUFFICIENT",
    "B1V2_LEARNING_PIPELINE_UNCALIBRATED",
    "B1V2_FULL_LEARNER_FAILED",
    "B1V2_CUE_ATTRIBUTION_FAILED",
    "B1V2_CURRENT_ONLY_SHORTCUT_SUFFICIENT",
    "B1V2_RAW_MEMORIZATION_NOT_EXCLUDED",
    "B1V2_CUE_LEARNING_PARTIAL_TABULAR_STRONGER",
    "B1V2_CUE_CONDITIONED_LIFECYCLE_LEARNING_TABULAR_SUFFICIENT",
    "B1V2_EVALUATION_DOMINANCE_INVARIANT_VIOLATED",
)
B1_CAPS = {
    "registered_fulls": 1,
    "learned_arm_seed_fits": 30,
    "training_episodes_exact": 30_720,
    "training_environment_transitions_max": 245_760,
    "total_environment_transitions_max": 300_000,
    "evaluation_episodes_max": 2_176,
    "policy_observation_calls_max": 75_000,
    "learner_calls_max": 30_720,
    "trainer_calls_max": 30_720,
    "neural_optimizer_updates_exact": 640,
    "tabular_updates_exact": 10_240,
    "wall_clock_cpu_minutes_max": 30,
    "memory_gib_max": 2,
}


class Action(str, Enum):
    RELEASE = "RELEASE"
    HOLD = "HOLD"

    @property
    def index(self) -> int:
        return 0 if self is Action.RELEASE else 1


@dataclass(frozen=True)
class PolicyObservation:
    committed_phase: str
    prior_acknowledgements: tuple[str, ...]
    physical_clock: int
    primitive_clock: int
    own_boundary_clock: int
    owner_epoch_token: tuple[str, str, int]
    visible_roster: tuple[str, ...]
    primitive_policy: str
    partner_policy: str
    cue_mask: int
    cue_value: int


@dataclass(frozen=True)
class ActionScoreEscrow:
    escrow_id: str
    action: str
    action_probabilities: tuple[float, float]
    selected_likelihood: float
    owner_epoch: str
    behavior_version: int
    consumption_count: int = 0


def stream_seed(seed_id: str, stream: str) -> int:
    if seed_id not in B1_SEED_IDS:
        raise ValueError(f"unregistered seed id: {seed_id}")
    if stream not in B1_RNG_STREAMS:
        raise ValueError(f"unregistered RNG stream: {stream}")
    digest = hashlib.sha256(f"{seed_id}/{stream}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def json_ready(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [json_ready(item) for item in value]
    if isinstance(value, Tensor):
        return value.detach().cpu().tolist()
    return value


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        json_ready(value), ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


class LifecycleHost:
    """One real B1 episode with A1 authority and boundary transitions."""

    def __init__(self) -> None:
        self._open = False

    def reset(
        self,
        *,
        lifecycle_id: str,
        owner_epoch: str,
        true_cue: int,
        presented_cue: int,
    ) -> PolicyObservation:
        if self._open:
            raise RuntimeError("TARGET_CLOSE is required before RESET")
        if true_cue not in (0, 1) or presented_cue not in (0, 1):
            raise ValueError("cues must be bits")
        self.lifecycle_id = lifecycle_id
        self.owner_epoch = owner_epoch
        self.true_cue = true_cue
        self.presented_cue = presented_cue
        self.token = a1.AuthorityToken(B1_OWNER_ID, owner_epoch, B1_BEHAVIOR_VERSION)
        self.world = a1.WorldView(
            authoritative_membership=frozenset({self.token.member_epoch}),
            visible_roster=B1_VISIBLE_ROSTER,
            current_behavior_version=B1_BEHAVIOR_VERSION,
        )
        initial = a1.LifecycleRecord(lifecycle_id=lifecycle_id, slot_id=B1_SLOT)
        claimed = a1.claim(initial, self.token, self.world, physical_clock=0)
        if not claimed.accepted:
            raise AssertionError("registered CLAIM was rejected")
        self.record = claimed.record
        self.states = [a1.Phase.UNCLAIMED.value, self.record.phase.value]
        self.rewards: list[int] = []
        self.environment_transitions = 2  # CLAIM and CUE_OBSERVE
        self.escrow: ActionScoreEscrow | None = None
        self._open = True
        self._cue_observation = self._observation(cue_mask=1, cue_value=presented_cue)
        return self._cue_observation

    def _observation(self, *, cue_mask: int, cue_value: int) -> PolicyObservation:
        return PolicyObservation(
            committed_phase=self.record.phase.value,
            prior_acknowledgements=self.record.acknowledgements,
            physical_clock=self.record.physical_clock,
            primitive_clock=self.record.primitive_clock,
            own_boundary_clock=self.record.own_boundary_clock,
            owner_epoch_token=(B1_OWNER_ID, self.owner_epoch, B1_BEHAVIOR_VERSION),
            visible_roster=B1_VISIBLE_ROSTER,
            primitive_policy=B1_PRIMITIVE,
            partner_policy=B1_PARTNER_POLICY,
            cue_mask=cue_mask,
            cue_value=cue_value,
        )

    def decision_observation(self) -> PolicyObservation:
        if not self._open or self.escrow is not None:
            raise RuntimeError("DECIDE observation is unavailable")
        # The direct cue byte is zero and masked.  No clock, reward, state, or
        # acknowledgement changes between CUE_OBSERVE and DECIDE.
        return self._observation(cue_mask=0, cue_value=0)

    def step(
        self,
        action: Action,
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
            f"{self.lifecycle_id}/{self.owner_epoch}/{B1_BEHAVIOR_VERSION}".encode()
        ).hexdigest()
        self.escrow = ActionScoreEscrow(
            escrow_id=escrow_id,
            action=action.value,
            action_probabilities=probabilities,
            selected_likelihood=probabilities[action.index],
            owner_epoch=self.owner_epoch,
            behavior_version=B1_BEHAVIOR_VERSION,
        )
        owner_action = a1.OwnerAction(action.value)
        first = a1.apply_boundary(
            self.record,
            contract=a1.candidate_contract(),
            action=owner_action,
            command_token=self.token,
            world=self.world,
            boundary_index=1,
            physical_clock=1,
            tape=a1.PairedTape(
                tape_id=f"{B1_ASSIGNMENT_ID}/PHYSICAL",
                primitive_action=B1_PRIMITIVE,
            ),
            release_id=escrow_id,
        )
        self.record = first.record
        self.states.append(self.record.phase.value)
        self.environment_transitions += 1
        if action is Action.RELEASE:
            self.rewards.append(1)
            if self.record.phase is not a1.Phase.ENDED_RELEASE:
                raise AssertionError("authorized RELEASE did not stop")
        else:
            self.rewards.append(-1 if self.true_cue else 2)
            if self.record.phase is not a1.Phase.ACTIVE:
                raise AssertionError("HOLD did not execute the frozen primitive")
            second = a1.apply_boundary(
                self.record,
                contract=a1.candidate_contract(),
                action=a1.OwnerAction.HOLD,
                command_token=self.token,
                world=self.world,
                boundary_index=2,
                physical_clock=2,
                tape=a1.PairedTape(
                    tape_id=f"{B1_ASSIGNMENT_ID}/PHYSICAL",
                    natural=True,
                    primitive_action=B1_PRIMITIVE,
                ),
                release_id=escrow_id,
            )
            self.record = second.record
            self.states.append(self.record.phase.value)
            self.environment_transitions += 1
            self.rewards.append(0)
            if self.record.phase is not a1.Phase.ENDED_NATURAL:
                raise AssertionError("HOLD did not naturally terminate")
        end_cause = self.record.end_cause
        if end_cause is None or self.escrow.consumption_count != 0:
            raise AssertionError("invalid pre-close escrow state")
        self.escrow = replace(self.escrow, consumption_count=1)
        self.record = replace(
            self.record,
            phase=a1.Phase.TARGET_CLOSED_TOMBSTONE,
            target_close_clock=self.record.physical_clock,
            tombstone_version=B1_BEHAVIOR_VERSION,
            acknowledgements=self.record.acknowledgements + ("TARGET_CLOSED",),
        )
        self.states.append(self.record.phase.value)
        self.environment_transitions += 1
        self._open = False
        physical_return = sum(
            reward * (B1_GAMMA**index) for index, reward in enumerate(self.rewards)
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
            "escrow": {
                **asdict(self.escrow),
                "closed": True,
                "end_cause": end_cause.value,
                "tombstone_phase": self.record.phase.value,
                "version_advance_permitted": a1.version_can_advance(
                    (self.record,), new_version=B1_BEHAVIOR_VERSION + 1
                ),
            },
            "environment_transitions": self.environment_transitions,
        }


def observation_vector(observation: Mapping[str, object]) -> Tensor:
    owner_epoch = str(observation["owner_epoch_token"][1])  # type: ignore[index]
    owner_hash = int.from_bytes(hashlib.sha256(owner_epoch.encode()).digest()[:2], "big")
    values = (
        float(observation["cue_mask"]),
        float(observation["cue_value"]),
        1.0 if observation["committed_phase"] == a1.Phase.ACTIVE.value else 0.0,
        1.0 if "CLAIM_ACCEPTED" in observation["prior_acknowledgements"] else 0.0,  # type: ignore[operator]
        float(observation["physical_clock"]) / B1_HORIZON,
        float(observation["primitive_clock"]) / B1_HORIZON,
        float(observation["own_boundary_clock"]) / B1_HORIZON,
        float(observation["owner_epoch_token"][2]) / B1_BEHAVIOR_VERSION,  # type: ignore[index]
        owner_hash / 65535.0,
        float(len(observation["visible_roster"])) / 2.0,  # type: ignore[arg-type]
    )
    return torch.tensor(values, dtype=torch.float64)


class GRUActorCritic(nn.Module):
    def __init__(self, *, init_seed: int) -> None:
        super().__init__()
        self.gru = nn.GRUCell(10, B1_HIDDEN_SIZE, dtype=torch.float64)
        self.actor = nn.Linear(B1_HIDDEN_SIZE, 2, dtype=torch.float64)
        self.critic = nn.Linear(B1_HIDDEN_SIZE, 1, dtype=torch.float64)
        generator = torch.Generator(device="cpu")
        generator.manual_seed(init_seed)
        bound = 1.0 / math.sqrt(B1_HIDDEN_SIZE)
        with torch.no_grad():
            for parameter in self.gru.parameters():
                parameter.uniform_(-bound, bound, generator=generator)
            self.critic.weight.uniform_(-bound, bound, generator=generator)
            self.critic.bias.uniform_(-bound, bound, generator=generator)
            self.actor.weight.zero_()
            self.actor.bias.zero_()

    def distribution(
        self,
        observations: Sequence[Mapping[str, object]],
        *,
        reset_before_decide: bool,
    ) -> tuple[Tensor, Tensor, Tensor]:
        hidden = torch.zeros(B1_HIDDEN_SIZE, dtype=torch.float64)
        hidden = self.gru(observation_vector(observations[0]), hidden)
        if reset_before_decide:
            hidden = torch.zeros_like(hidden)
        hidden = self.gru(observation_vector(observations[1]), hidden)
        logits = self.actor(hidden)
        softmax = torch.softmax(logits, dim=0)
        probabilities = 0.8 * softmax + 0.1
        entropy = -(probabilities * torch.log(probabilities)).sum()
        return probabilities, self.critic(hidden).squeeze(0), entropy


def serialize_model(model: GRUActorCritic) -> dict[str, object]:
    return {
        name: {
            "dtype": str(tensor.dtype),
            "shape": list(tensor.shape),
            "values": tensor.detach().cpu().reshape(-1).tolist(),
        }
        for name, tensor in sorted(model.state_dict().items())
    }


def model_digest(model: GRUActorCritic) -> str:
    return hashlib.sha256(canonical_bytes(serialize_model(model))).hexdigest()


def training_schedule(seed_id: str, *, blocks: int = B1_TRAIN_BLOCKS) -> list[dict[str, object]]:
    order_rng = random.Random(stream_seed(seed_id, "episode_order"))
    shuffle_rng = random.Random(stream_seed(seed_id, "cue_shuffle"))
    rows: list[dict[str, object]] = []
    for block in range(blocks):
        cells = [(epoch, cue) for epoch in B1_TRAIN_EPOCHS for cue in (0, 1)]
        order_rng.shuffle(cells)
        presented_by_cue: dict[int, list[int]] = {}
        for cue in (0, 1):
            presented = [0] * 16 + [1] * 16
            shuffle_rng.shuffle(presented)
            presented_by_cue[cue] = presented
        offsets = {0: 0, 1: 0}
        for within_block, (epoch, cue) in enumerate(cells):
            index = offsets[cue]
            offsets[cue] += 1
            rows.append(
                {
                    "episode_index": block * B1_BLOCK_EPISODES + within_block,
                    "block": block,
                    "owner_epoch": epoch,
                    "true_cue": cue,
                    "shuffled_presented_cue": presented_by_cue[cue][index],
                }
            )
    return rows


def _history_for_arm(
    arm: str, cue_observation: PolicyObservation, decide_observation: PolicyObservation
) -> list[dict[str, object]]:
    history = [asdict(cue_observation), asdict(decide_observation)]
    if arm == "CUE_BLIND_GRU":
        history[0]["cue_value"] = 0
    return history


def _raw_history_key(history: Sequence[Mapping[str, object]]) -> str:
    first = history[0]
    context_identity = (
        B1_HOST_ID,
        B1_SLOT,
        tuple(first["owner_epoch_token"]),  # type: ignore[arg-type]
        tuple(first["visible_roster"]),  # type: ignore[arg-type]
    )
    return hashlib.sha256(
        canonical_bytes({"context_identity": context_identity, "history": history})
    ).hexdigest()


def _tabular_distribution(
    table: Mapping[str, Sequence[float]], *, key: str, unseen_uniform: bool = False
) -> tuple[float, float]:
    values = table.get(key)
    if values is None:
        return (0.5, 0.5) if unseen_uniform else (0.9, 0.1)
    greedy = 0 if float(values[0]) >= float(values[1]) else 1
    return (0.9, 0.1) if greedy == 0 else (0.1, 0.9)


def _table_snapshot(
    sums: Mapping[str, Sequence[float]], counts: Mapping[str, Sequence[int]]
) -> dict[str, list[float]]:
    return {
        key: [
            float(sums[key][index]) / int(counts[key][index])
            if int(counts[key][index])
            else 0.0
            for index in range(2)
        ]
        for key in sorted(sums)
    }


def _episode(
    *,
    arm: str,
    seed_id: str,
    row: Mapping[str, object],
    action_probabilities: Sequence[float],
    action: Action,
    presented_cue: int,
    phase: str,
) -> dict[str, object]:
    host = LifecycleHost()
    cue = host.reset(
        lifecycle_id=f"{seed_id}/{arm}/{phase}/{row['episode_index']}",
        owner_epoch=str(row["owner_epoch"]),
        true_cue=int(row["true_cue"]),
        presented_cue=presented_cue,
    )
    decide = host.decision_observation()
    episode = host.step(action, action_probabilities=action_probabilities)
    if episode["observations"] != [asdict(cue), asdict(decide)]:
        raise AssertionError("host observation retention mismatch")
    return episode


def _prepare_episode(
    *, arm: str, seed_id: str, row: Mapping[str, object], phase: str
) -> tuple[LifecycleHost, list[dict[str, object]], int]:
    presented = (
        int(row["shuffled_presented_cue"])
        if arm == "CUE_SHUFFLED_GRU"
        else int(row["true_cue"])
    )
    host = LifecycleHost()
    cue = host.reset(
        lifecycle_id=f"{seed_id}/{arm}/{phase}/{row['episode_index']}",
        owner_epoch=str(row["owner_epoch"]),
        true_cue=int(row["true_cue"]),
        presented_cue=presented,
    )
    decide = host.decision_observation()
    return host, _history_for_arm(arm, cue, decide), presented


def train_neural_arm(
    arm: str, seed_id: str, schedule: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    if arm not in B1_NEURAL_ARMS:
        raise ValueError(arm)
    model = GRUActorCritic(init_seed=stream_seed(seed_id, "init"))
    initial_state = serialize_model(model)
    initial_digest = model_digest(model)
    parameter_snapshots = {initial_digest: initial_state}
    action_rng = random.Random(stream_seed(seed_id, "action"))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.003)
    episodes: list[dict[str, object]] = []
    updates: list[dict[str, object]] = []
    for batch_start in range(0, len(schedule), B1_BATCH_SIZE):
        batch = schedule[batch_start : batch_start + B1_BATCH_SIZE]
        actor_terms: list[Tensor] = []
        critic_terms: list[Tensor] = []
        batch_indices: list[int] = []
        before = model_digest(model)
        for row in batch:
            host, history, presented = _prepare_episode(
                arm=arm, seed_id=seed_id, row=row, phase="train"
            )
            probabilities, baseline, entropy = model.distribution(
                history, reset_before_decide=arm == "CURRENT_ONLY_GRU"
            )
            action = (
                Action.RELEASE
                if action_rng.random() < float(probabilities[0].detach())
                else Action.HOLD
            )
            episode = host.step(
                action, action_probabilities=probabilities.detach().cpu().tolist()
            )
            physical_return = torch.tensor(
                float(episode["physical_return"]), dtype=torch.float64
            )
            actor_terms.append(
                -(physical_return - baseline.detach())
                * torch.log(probabilities[action.index])
                - 0.01 * entropy
            )
            critic_terms.append(0.5 * (physical_return - baseline) ** 2)
            episode.update(
                {
                    "seed_id": seed_id,
                    "arm": arm,
                    "episode_index": int(row["episode_index"]),
                    "block": int(row["block"]),
                    "presented_cue": presented,
                    "learner_state": {
                        "kind": "neural_parameter_snapshot_reference",
                        "before_update": before,
                    },
                    "gradient_clip": None,
                    "activity": {
                        "environment_transitions": episode["environment_transitions"],
                        "policy_observation_calls": 2,
                        "policy_calls": 1,
                        "learner_calls": 1,
                        "trainer_calls": 1,
                        "optimizer_updates": 0,
                        "tabular_updates": 0,
                    },
                }
            )
            batch_indices.append(len(episodes))
            episodes.append(episode)
        optimizer.zero_grad(set_to_none=True)
        loss = torch.stack(actor_terms).mean() + torch.stack(critic_terms).mean()
        loss.backward()
        unclipped = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
        clipped = unclipped > 1.0
        optimizer.step()
        after = model_digest(model)
        parameter_snapshots[after] = serialize_model(model)
        update = {
            "step": len(updates) + 1,
            "batch_start": batch_start,
            "batch_size": len(batch),
            "loss": float(loss.detach()),
            "gradient_norm_before_clip": unclipped,
            "clip_threshold": 1.0,
            "clipped": clipped,
            "parameters_before": before,
            "parameters_after": after,
        }
        updates.append(update)
        for index in batch_indices:
            episodes[index]["learner_state"]["after_update"] = after  # type: ignore[index]
            episodes[index]["gradient_clip"] = deepcopy(update)
        episodes[batch_indices[-1]]["activity"]["optimizer_updates"] = 1  # type: ignore[index]
    return {
        "arm": arm,
        "seed_id": seed_id,
        "kind": "neural",
        "architecture": {
            "dtype": "torch.float64",
            "recurrent": "one-layer GRUCell",
            "input_size": 10,
            "hidden_size": B1_HIDDEN_SIZE,
            "actor_logits": 2,
            "critic_outputs": 1,
            "actor_initialization": "exact zeros",
        },
        "initial_state": initial_state,
        "final_state": serialize_model(model),
        "parameter_snapshots": parameter_snapshots,
        "optimizer": {
            "name": "Adam",
            "learning_rate": 0.003,
            "batch_size": B1_BATCH_SIZE,
            "gradient_norm_clip": 1.0,
            "updates": updates,
        },
        "episodes": episodes,
    }


def train_tabular_arm(
    arm: str, seed_id: str, schedule: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    if arm not in B1_TABULAR_ARMS:
        raise ValueError(arm)
    action_rng = random.Random(stream_seed(seed_id, "action"))
    sums: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    if arm == "X_MEMORY_TABULAR_MONTE_CARLO":
        for cue_key in ("0", "1"):
            sums[cue_key] = [0.0, 0.0]
            counts[cue_key] = [0, 0]
    initial_table = _table_snapshot(sums, counts)
    initial_counts = {key: list(value) for key, value in sorted(counts.items())}
    episodes: list[dict[str, object]] = []
    for row in schedule:
        host, history, presented = _prepare_episode(
            arm=arm, seed_id=seed_id, row=row, phase="train"
        )
        key = (
            str(presented)
            if arm == "X_MEMORY_TABULAR_MONTE_CARLO"
            else _raw_history_key(history)
        )
        before = _table_snapshot(sums, counts)
        probabilities = _tabular_distribution(before, key=key)
        action = Action.RELEASE if action_rng.random() < probabilities[0] else Action.HOLD
        episode = host.step(action, action_probabilities=probabilities)
        counts[key][action.index] += 1
        sums[key][action.index] += float(episode["physical_return"])
        after = _table_snapshot(sums, counts)
        episode.update(
            {
                "seed_id": seed_id,
                "arm": arm,
                "episode_index": int(row["episode_index"]),
                "block": int(row["block"]),
                "presented_cue": presented,
                "learner_state": {
                    "kind": "sample_mean_table",
                    "key": key,
                    "before": before,
                    "after": after,
                    "counts_after": {name: list(value) for name, value in sorted(counts.items())},
                },
                "gradient_clip": {
                    "applicable": False,
                    "gradient_norm_before_clip": None,
                    "clipped": False,
                },
                "activity": {
                    "environment_transitions": episode["environment_transitions"],
                    "policy_observation_calls": 2,
                    "policy_calls": 1,
                    "learner_calls": 1,
                    "trainer_calls": 1,
                    "optimizer_updates": 0,
                    "tabular_updates": 1,
                },
            }
        )
        episodes.append(episode)
    return {
        "arm": arm,
        "seed_id": seed_id,
        "kind": "tabular",
        "initial_state": {"table": initial_table, "counts": initial_counts},
        "final_state": {
            "table": _table_snapshot(sums, counts),
            "counts": {key: list(value) for key, value in sorted(counts.items())},
        },
        "updates": len(episodes),
        "episodes": episodes,
    }


def _restore_model(state: Mapping[str, object], *, seed_id: str) -> GRUActorCritic:
    model = GRUActorCritic(init_seed=stream_seed(seed_id, "init"))
    restored: dict[str, Tensor] = {}
    for name, payload in state.items():
        assert isinstance(payload, Mapping)
        restored[name] = torch.tensor(payload["values"], dtype=torch.float64).reshape(  # type: ignore[arg-type]
            tuple(int(value) for value in payload["shape"])  # type: ignore[arg-type]
        )
    model.load_state_dict(restored)
    return model


def run_training(manifest: Mapping[str, object]) -> dict[str, object]:
    issues = validate_manifest(manifest)
    if issues:
        raise ValueError("; ".join(issues))
    torch.set_num_threads(1)
    seed_ids = tuple(str(value) for value in manifest["seed_ids"])  # type: ignore[index]
    blocks = int(manifest["training_blocks"])
    fits: list[dict[str, object]] = []
    for seed_id in seed_ids:
        schedule = training_schedule(seed_id, blocks=blocks)
        for arm in B1_LEARNED_ARMS:
            fit = (
                train_neural_arm(arm, seed_id, schedule)
                if arm in B1_NEURAL_ARMS
                else train_tabular_arm(arm, seed_id, schedule)
            )
            fits.append(fit)
    return {
        "schema_version": B1_SCHEMA_VERSION,
        "artifact_kind": "vsp02_b1v2_training",
        "manifest_identity": manifest_identity(manifest),
        "fits": fits,
        "activity": sum_activity(
            episode for fit in fits for episode in fit["episodes"]  # type: ignore[index]
        ),
    }


def _policy_probabilities(
    fit: Mapping[str, object], history: Sequence[Mapping[str, object]]
) -> tuple[float, float]:
    arm = str(fit["arm"])
    if arm in B1_NEURAL_ARMS:
        model = _restore_model(fit["final_state"], seed_id=str(fit["seed_id"]))  # type: ignore[arg-type]
        with torch.no_grad():
            probabilities, _, _ = model.distribution(
                history, reset_before_decide=arm == "CURRENT_ONLY_GRU"
            )
        return tuple(float(value) for value in probabilities)  # type: ignore[return-value]
    table = fit["final_state"]["table"]  # type: ignore[index]
    key = (
        str(history[0]["cue_value"])
        if arm == "X_MEMORY_TABULAR_MONTE_CARLO"
        else _raw_history_key(history)
    )
    return _tabular_distribution(  # type: ignore[arg-type]
        table,
        key=key,
        unseen_uniform=arm == "RAW_HISTORY_TABULAR_MEMORIZER",
    )


def _fixed_probabilities(arm: str, true_cue: int) -> tuple[float, float]:
    if arm == "ALWAYS_RELEASE":
        return (1.0, 0.0)
    if arm == "ALWAYS_HOLD":
        return (0.0, 1.0)
    if arm == "UNIFORM_RANDOM":
        return (0.5, 0.5)
    if arm == B1_ORACLE:
        return (1.0, 0.0) if true_cue else (0.0, 1.0)
    raise ValueError(arm)


def _evaluation_rows_for_fit(fit: Mapping[str, object]) -> list[dict[str, object]]:
    arm, seed_id = str(fit["arm"]), str(fit["seed_id"])
    rows: list[dict[str, object]] = []
    model = (
        _restore_model(fit["final_state"], seed_id=seed_id)  # type: ignore[arg-type]
        if arm in B1_NEURAL_ARMS
        else None
    )
    index = 0
    for owner_index, owner_epoch in enumerate(B1_EVAL_EPOCHS):
        for true_cue in (0, 1):
            for forced_action in Action:
                row = {
                    "episode_index": index,
                    "owner_epoch": owner_epoch,
                    "true_cue": true_cue,
                    # Across the exact 64-row forced panel this gives 16 rows
                    # in every true-cue/presented-cue cell (both actions for
                    # eight owner epochs), independently of the true cue.
                    "shuffled_presented_cue": owner_index % 2,
                }
                host, history, presented = _prepare_episode(
                    arm=arm, seed_id=seed_id, row=row, phase="evaluation"
                )
                if model is not None:
                    with torch.no_grad():
                        probability_tensor, _, _ = model.distribution(
                            history, reset_before_decide=arm == "CURRENT_ONLY_GRU"
                        )
                    probabilities = tuple(float(value) for value in probability_tensor)
                else:
                    table = fit["final_state"]["table"]  # type: ignore[index]
                    key = (
                        str(history[0]["cue_value"])
                        if arm == "X_MEMORY_TABULAR_MONTE_CARLO"
                        else _raw_history_key(history)
                    )
                    probabilities = _tabular_distribution(  # type: ignore[arg-type]
                        table,
                        key=key,
                        unseen_uniform=arm == "RAW_HISTORY_TABULAR_MEMORIZER",
                    )
                episode = host.step(forced_action, action_probabilities=probabilities)
                episode.update(
                    {
                        "seed_id": seed_id,
                        "arm": arm,
                        "episode_index": index,
                        "forced_action": forced_action.value,
                        "presented_cue": presented,
                        "evaluation_update": False,
                        "activity": {
                            "environment_transitions": episode["environment_transitions"],
                            "policy_observation_calls": 2,
                            "policy_calls": 1,
                            "learner_calls": 0,
                            "trainer_calls": 0,
                            "optimizer_updates": 0,
                            "tabular_updates": 0,
                        },
                    }
                )
                rows.append(episode)
                index += 1
    return rows


def _evaluation_rows_for_reference(arm: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    index = 0
    for owner_epoch in B1_EVAL_EPOCHS:
        for true_cue in (0, 1):
            for forced_action in Action:
                host = LifecycleHost()
                cue = host.reset(
                    lifecycle_id=f"REFERENCE/{arm}/{index}",
                    owner_epoch=owner_epoch,
                    true_cue=true_cue,
                    presented_cue=true_cue,
                )
                decide = host.decision_observation()
                probabilities = _fixed_probabilities(arm, true_cue)
                episode = host.step(forced_action, action_probabilities=probabilities)
                episode.update(
                    {
                        "seed_id": None,
                        "arm": arm,
                        "episode_index": index,
                        "forced_action": forced_action.value,
                        "presented_cue": true_cue,
                        "evaluation_update": False,
                        "observations": [asdict(cue), asdict(decide)],
                        "activity": {
                            "environment_transitions": episode["environment_transitions"],
                            "policy_observation_calls": 2,
                            "policy_calls": 1,
                            "learner_calls": 0,
                            "trainer_calls": 0,
                            "optimizer_updates": 0,
                            "tabular_updates": 0,
                        },
                    }
                )
                rows.append(episode)
                index += 1
    return rows


def summarize_evaluation_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    clones: dict[tuple[str, int], dict[str, Mapping[str, object]]] = defaultdict(dict)
    for row in rows:
        clones[(str(row["owner_epoch"]), int(row["true_cue"]))][str(row["action"])] = row
    clone_values: list[float] = []
    release_by_cue: dict[int, list[float]] = defaultdict(list)
    choices: dict[int, list[str | None]] = defaultdict(list)
    for (_, cue), actions in sorted(clones.items()):
        if set(actions) != {Action.RELEASE.value, Action.HOLD.value}:
            raise ValueError("forced evaluation clone lacks both actions")
        probabilities = actions[Action.RELEASE.value]["action_probabilities"]
        if probabilities != actions[Action.HOLD.value]["action_probabilities"]:
            raise ValueError("forced actions changed policy probabilities")
        value = sum(
            float(probabilities[Action(action).index]) * float(record["physical_return"])  # type: ignore[index]
            for action, record in actions.items()
        )
        clone_values.append(value)
        p_release = float(probabilities[0])  # type: ignore[index]
        release_by_cue[cue].append(p_release)
        p_hold = float(probabilities[1])  # type: ignore[index]
        choices[cue].append(
            Action.RELEASE.value
            if p_release > p_hold
            else Action.HOLD.value
            if p_hold > p_release
            else None
        )
    mean_release = {
        str(cue): sum(values) / len(values) for cue, values in release_by_cue.items()
    }
    return {
        "episodes": len(rows),
        "clones": len(clones),
        "j_eval": sum(clone_values) / len(clone_values),
        "mean_release_probability_by_true_cue": mean_release,
        "kappa": mean_release["1"] - mean_release["0"],
        "argmax_ties": sum(choice is None for values in choices.values() for choice in values),
        "mapping_all_clones": all(choice == Action.RELEASE.value for choice in choices[1])
        and all(choice == Action.HOLD.value for choice in choices[0]),
    }


def run_evaluation(
    manifest: Mapping[str, object],
    training: Mapping[str, object],
    *,
    training_validated: bool = False,
) -> dict[str, object]:
    if not training_validated:
        issues = validate_training_artifact(manifest, training)
        if issues:
            raise ValueError("; ".join(issues))
    evaluations: list[dict[str, object]] = []
    for fit in training["fits"]:  # type: ignore[index]
        rows = _evaluation_rows_for_fit(fit)
        evaluations.append(
            {
                "arm": fit["arm"],
                "seed_id": fit["seed_id"],
                "rows": rows,
                "summary": summarize_evaluation_rows(rows),
            }
        )
    if manifest["technical_only"] is False:
        for arm in (*B1_FIXED_ARMS, B1_ORACLE):
            rows = _evaluation_rows_for_reference(arm)
            evaluations.append(
                {
                    "arm": arm,
                    "seed_id": None,
                    "rows": rows,
                    "summary": summarize_evaluation_rows(rows),
                }
            )
    all_rows = [row for evaluation in evaluations for row in evaluation["rows"]]
    return {
        "schema_version": B1_SCHEMA_VERSION,
        "artifact_kind": "vsp02_b1v2_evaluation",
        "manifest_identity": manifest_identity(manifest),
        "evaluations": evaluations,
        "activity": sum_activity(all_rows),
    }


def sum_activity(episodes: Iterable[Mapping[str, object]]) -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    for episode in episodes:
        activity = episode.get("activity", {})
        assert isinstance(activity, Mapping)
        for key, value in activity.items():
            totals[str(key)] += int(value)
    return dict(sorted(totals.items()))


def _support(training: Mapping[str, object]) -> dict[str, dict[str, int]]:
    support: dict[str, dict[str, int]] = {}
    for fit in training["fits"]:  # type: ignore[index]
        key = f"{fit['arm']}|{fit['seed_id']}"
        counts: dict[str, int] = defaultdict(int)
        for episode in fit["episodes"]:
            counts[f"{episode['true_cue']}|{episode['action']}"] += 1
        support[key] = dict(sorted(counts.items()))
    return support


def _evaluation_lookup(evaluation: Mapping[str, object]) -> dict[tuple[str, str | None], Mapping[str, object]]:
    return {
        (str(item["arm"]), None if item["seed_id"] is None else str(item["seed_id"])): item
        for item in evaluation["evaluations"]  # type: ignore[index]
    }


def _positive_control_seed_passes(summary: Mapping[str, object]) -> bool:
    return bool(summary["mapping_all_clones"]) and Decimal(
        str(summary["j_eval"])
    ) >= Decimal("1.30")


def _correct_table_seed_is_exact(summary: Mapping[str, object]) -> bool:
    return not bool(summary["mapping_all_clones"]) or abs(
        Decimal(str(summary["j_eval"])) - Decimal("1.35")
    ) <= Decimal("1e-12")


def _full_candidate_gate(*, psi: float, kappa: float, mapping_seeds: int) -> bool:
    return (
        Decimal(str(psi)) > Decimal("0.05")
        and Decimal(str(kappa)) >= Decimal("0.70")
        and mapping_seeds >= 4
    )


def _support_counts_meet_floor(counts: Mapping[str, int]) -> bool:
    return all(
        counts.get(f"{cue}|{action.value}", 0) >= 32
        for cue in (0, 1)
        for action in Action
    )


def compute_analysis(
    manifest: Mapping[str, object],
    training: Mapping[str, object],
    evaluation: Mapping[str, object],
) -> dict[str, object]:
    lookup = _evaluation_lookup(evaluation)
    seed_ids = tuple(str(value) for value in manifest["seed_ids"])  # type: ignore[index]
    per_arm_seed = {
        f"{arm}|{seed_id}": lookup[(arm, seed_id)]["summary"]
        for arm in B1_LEARNED_ARMS
        for seed_id in seed_ids
    }
    arm_means = {
        arm: sum(
            float(lookup[(arm, seed_id)]["summary"]["j_eval"])  # type: ignore[index]
            for seed_id in seed_ids
        )
        / len(seed_ids)
        for arm in B1_LEARNED_ARMS
    }
    support = _support(training)
    full_summaries = [lookup[(B1_LEARNED_ARMS[0], seed_id)]["summary"] for seed_id in seed_ids]
    x_summaries = [lookup[(B1_TABULAR_ARMS[0], seed_id)]["summary"] for seed_id in seed_ids]
    x_pass_seeds = sum(_positive_control_seed_passes(summary) for summary in x_summaries)
    x_exactness = all(
        not _support_counts_meet_floor(
            support[f"{B1_TABULAR_ARMS[0]}|{seed_id}"]
        )
        or _correct_table_seed_is_exact(summary)
        for seed_id, summary in zip(seed_ids, x_summaries)
    )
    full_mapping_seeds = sum(bool(summary["mapping_all_clones"]) for summary in full_summaries)
    psi = arm_means[B1_LEARNED_ARMS[0]] - 1.0
    kappa = sum(float(summary["kappa"]) for summary in full_summaries) / len(full_summaries)
    training_activity = training["activity"]
    evaluation_activity = evaluation["activity"]
    activity_totals = {
        key: int(training_activity.get(key, 0)) + int(evaluation_activity.get(key, 0))  # type: ignore[union-attr]
        for key in set(training_activity) | set(evaluation_activity)  # type: ignore[arg-type]
    }
    fixed_values = (
        {
            arm: float(lookup[(arm, None)]["summary"]["j_eval"])  # type: ignore[index]
            for arm in (*B1_FIXED_ARMS, B1_ORACLE)
        }
        if manifest["technical_only"] is False
        else {}
    )
    host_contract = {
        "forced_returns_exact": _forced_return_signature(evaluation)
        == {"0|HOLD": 2.0, "0|RELEASE": 1.0, "1|HOLD": -1.0, "1|RELEASE": 1.0},
        "fixed_values_exact": bool(fixed_values)
        and fixed_values
        == {
            "ALWAYS_RELEASE": 1.0,
            "ALWAYS_HOLD": 0.5,
            "UNIFORM_RANDOM": 0.75,
            B1_ORACLE: 1.5,
        },
        "episode_contracts_valid": not _all_episode_issues(training, evaluation),
        "decide_clones_byte_identical": _decide_clones_identical(evaluation),
        "owner_epoch_split_disjoint": set(B1_TRAIN_EPOCHS).isdisjoint(B1_EVAL_EPOCHS),
        "initial_table_firewall": _initial_firewall_valid(training),
        "arm_matching": _arm_matching_valid(training),
        "terminal_precedence_exact": tuple(B1_TERMINAL_PRECEDENCE)
        == ("TERMINAL", "INTERRUPT", "AUTHORIZED_RELEASE", "NATURAL", "HORIZON")
        and _terminal_precedence_behavior_valid(),
    }
    support_ok = all(_support_counts_meet_floor(counts) for counts in support.values())
    activity_ok = all(
        activity_totals.get(key, 0) > 0
        for key in (
            "environment_transitions",
            "policy_calls",
            "learner_calls",
            "trainer_calls",
            "optimizer_updates",
        )
    ) and int(evaluation_activity.get("policy_calls", 0)) > 0  # type: ignore[union-attr]
    gates = {
        "host_information_contract": all(host_contract.values()),
        "activity_nonzero": activity_ok,
        "support_floor": support_ok,
        "x_memory_positive_control": x_pass_seeds >= 4,
        "x_memory_table_exactness": x_exactness,
        "full_gate": _full_candidate_gate(
            psi=psi, kappa=kappa, mapping_seeds=full_mapping_seeds
        ),
    }
    analysis: dict[str, object] = {
        "schema_version": B1_SCHEMA_VERSION,
        "artifact_kind": "vsp02_b1v2_analysis",
        "manifest_identity": manifest_identity(manifest),
        "technical_only": manifest["technical_only"],
        "admission": "NONADMITTED_TECHNICAL_ONLY" if manifest["technical_only"] else B1_RESOURCE_CLASS,
        "host_contract": host_contract,
        "support": support,
        "activity": {
            "training": training_activity,
            "evaluation": evaluation_activity,
            "total": dict(sorted(activity_totals.items())),
        },
        "per_arm_seed": per_arm_seed,
        "arm_mean_j_eval": arm_means,
        "fixed_values": fixed_values,
        "estimands": {"psi": psi, "kappa": kappa},
        "seed_gate_counts": {
            "x_memory_positive_control": x_pass_seeds,
            "full_mapping": full_mapping_seeds,
        },
        "gates": gates,
        "branch": None,
    }
    if manifest["technical_only"] is False:
        analysis["branch"] = classify_b1v2(analysis)
    return analysis


def classify_b1v2(analysis: Mapping[str, object]) -> str:
    gates = analysis["gates"]
    means = analysis["arm_mean_j_eval"]
    assert isinstance(gates, Mapping) and isinstance(means, Mapping)
    if not bool(gates["host_information_contract"]):
        return B1_BRANCH_PRECEDENCE[0]
    if not bool(gates["activity_nonzero"]) or not bool(gates["support_floor"]):
        return B1_BRANCH_PRECEDENCE[1]
    if not bool(gates["x_memory_positive_control"]) or not bool(
        gates["x_memory_table_exactness"]
    ):
        return B1_BRANCH_PRECEDENCE[2]
    if not bool(gates["full_gate"]):
        return B1_BRANCH_PRECEDENCE[3]
    full = float(means["FULL_LIFECYCLE_GRU_ACTOR_CRITIC"])
    x_memory = float(means["X_MEMORY_TABULAR_MONTE_CARLO"])
    if any(
        abs(float(means[arm]) - full) <= 0.05
        for arm in ("CUE_BLIND_GRU", "CUE_SHUFFLED_GRU")
    ):
        return B1_BRANCH_PRECEDENCE[4]
    if abs(float(means["CURRENT_ONLY_GRU"]) - full) <= 0.05:
        return B1_BRANCH_PRECEDENCE[5]
    if abs(float(means["RAW_HISTORY_TABULAR_MEMORIZER"]) - full) <= 0.05:
        return B1_BRANCH_PRECEDENCE[6]
    gap = Decimal(str(x_memory)) - Decimal(str(full))
    if gap > Decimal("0.05"):
        return B1_BRANCH_PRECEDENCE[7]
    if gap >= Decimal("-1e-12"):
        return B1_BRANCH_PRECEDENCE[8]
    return B1_BRANCH_PRECEDENCE[9]


def _forced_return_signature(evaluation: Mapping[str, object]) -> dict[str, float]:
    values: dict[str, set[float]] = defaultdict(set)
    for item in evaluation["evaluations"]:  # type: ignore[index]
        for row in item["rows"]:
            values[f"{row['true_cue']}|{row['action']}"].add(float(row["physical_return"]))
    return {key: next(iter(group)) for key, group in values.items() if len(group) == 1}


def _initial_firewall_valid(training: Mapping[str, object]) -> bool:
    for fit in training["fits"]:  # type: ignore[index]
        if fit["kind"] == "tabular":
            expected = (
                {
                    "table": {"0": [0.0, 0.0], "1": [0.0, 0.0]},
                    "counts": {"0": [0, 0], "1": [0, 0]},
                }
                if fit["arm"] == "X_MEMORY_TABULAR_MONTE_CARLO"
                else {"table": {}, "counts": {}}
            )
            if fit["initial_state"] != expected:
                return False
        if fit["kind"] == "neural":
            actor = fit["initial_state"]
            for name in ("actor.weight", "actor.bias"):
                if any(float(value) != 0.0 for value in actor[name]["values"]):
                    return False
    return True


def _arm_matching_valid(training: Mapping[str, object]) -> bool:
    by_seed: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for fit in training["fits"]:  # type: ignore[index]
        if fit["arm"] in B1_NEURAL_ARMS:
            by_seed[str(fit["seed_id"])].append(fit)
    for fits in by_seed.values():
        if len(fits) != len(B1_NEURAL_ARMS):
            return False
        if len({canonical_bytes(fit["initial_state"]) for fit in fits}) != 1:
            return False
        if any(fit["architecture"] != fits[0]["architecture"] for fit in fits):
            return False
        if any(
            {key: fit["optimizer"][key] for key in ("name", "learning_rate", "batch_size", "gradient_norm_clip")}
            != {key: fits[0]["optimizer"][key] for key in ("name", "learning_rate", "batch_size", "gradient_norm_clip")}
            for fit in fits
        ):
            return False
    return True


def _decide_clones_identical(evaluation: Mapping[str, object]) -> bool:
    groups: dict[tuple[str, str | None, str], set[bytes]] = defaultdict(set)
    for item in evaluation["evaluations"]:  # type: ignore[index]
        for row in item["rows"]:
            key = (str(item["arm"]), item["seed_id"], str(row["owner_epoch"]))
            groups[key].add(canonical_bytes(row["observations"][1]))
    return all(len(values) == 1 for values in groups.values())


def _episode_issues(episode: Mapping[str, object]) -> list[str]:
    issues: list[str] = []
    observations = episode.get("observations")
    if not isinstance(observations, list) or len(observations) != 2:
        return ["observation history mismatch"]
    cue, decide = observations
    if set(cue) != set(B1_OBSERVATION_FIELDS) or set(decide) != set(B1_OBSERVATION_FIELDS):
        issues.append("observation field allow-list mismatch")
    if (set(cue) | set(decide)) & B1_FORBIDDEN_OBSERVATION_FIELDS:
        issues.append("forbidden observation field exposed")
    if cue.get("cue_mask") != 1 or decide.get("cue_mask") != 0 or decide.get("cue_value") != 0:
        issues.append("cue mask contract mismatch")
    ignored = {"cue_mask", "cue_value"}
    if any(cue[key] != decide[key] for key in cue if key not in ignored):
        issues.append("CUE_OBSERVE-to-DECIDE changed exposed bytes")
    action = str(episode.get("action"))
    true_cue = int(episode.get("true_cue", -1))
    expected_rewards = [1] if action == "RELEASE" else ([-1, 0] if true_cue else [2, 0])
    if episode.get("reward_sequence") != expected_rewards:
        issues.append("physical reward mismatch")
    expected_return = sum(value * B1_GAMMA**index for index, value in enumerate(expected_rewards))
    if float(episode.get("physical_return", math.nan)) != expected_return:
        issues.append("physical return mismatch")
    expected_states = (
        ["UNCLAIMED", "ACTIVE", "ENDED_RELEASE", "TARGET_CLOSED_TOMBSTONE"]
        if action == "RELEASE"
        else ["UNCLAIMED", "ACTIVE", "ACTIVE", "ENDED_NATURAL", "TARGET_CLOSED_TOMBSTONE"]
    )
    if episode.get("lifecycle_states") != expected_states:
        issues.append("lifecycle state mismatch")
    escrow = episode.get("escrow")
    if not isinstance(escrow, Mapping):
        issues.append("escrow missing")
    else:
        probabilities = episode.get("action_probabilities")
        expected_escrow_id = hashlib.sha256(
            f"{episode.get('lifecycle_id')}/{episode.get('owner_epoch')}/{B1_BEHAVIOR_VERSION}".encode()
        ).hexdigest()
        if not (
            isinstance(probabilities, list)
            and len(probabilities) == 2
            and all(math.isfinite(float(value)) and float(value) >= 0.0 for value in probabilities)
            and abs(sum(float(value) for value in probabilities) - 1.0) <= 1e-12
            and float(episode.get("selected_likelihood", math.nan))
            == float(probabilities[Action(action).index])
            and escrow.get("selected_likelihood") == episode.get("selected_likelihood")
            and list(escrow.get("action_probabilities", ())) == probabilities
            and escrow.get("escrow_id") == expected_escrow_id
            and escrow.get("action") == action
            and escrow.get("owner_epoch") == episode.get("owner_epoch")
            and escrow.get("behavior_version") == B1_BEHAVIOR_VERSION
            and escrow.get("consumption_count") == 1
            and escrow.get("closed") is True
            and escrow.get("version_advance_permitted") is True
        ):
            issues.append("escrow/closure mismatch")
    return issues


def _all_episode_issues(
    training: Mapping[str, object], evaluation: Mapping[str, object]
) -> list[str]:
    issues: list[str] = []
    for fit in training["fits"]:  # type: ignore[index]
        for episode in fit["episodes"]:
            issues.extend(_episode_issues(episode))
    for item in evaluation["evaluations"]:  # type: ignore[index]
        for episode in item["rows"]:
            issues.extend(_episode_issues(episode))
    return issues


def _terminal_precedence_behavior_valid() -> bool:
    token = a1.AuthorityToken(B1_OWNER_ID, "PRECEDENCE", B1_BEHAVIOR_VERSION)
    world = a1.WorldView(
        authoritative_membership=frozenset({token.member_epoch}),
        visible_roster=B1_VISIBLE_ROSTER,
        current_behavior_version=B1_BEHAVIOR_VERSION,
    )

    def cell(action: Action, **events: bool) -> a1.Phase:
        claimed = a1.claim(
            a1.LifecycleRecord("precedence", slot_id=B1_SLOT),
            token,
            world,
            physical_clock=0,
        )
        if not claimed.accepted:
            raise AssertionError("precedence CLAIM failed")
        result = a1.apply_boundary(
            claimed.record,
            contract=a1.candidate_contract(),
            action=a1.OwnerAction(action.value),
            command_token=token,
            world=world,
            boundary_index=1,
            physical_clock=1,
            tape=a1.PairedTape("B1-PRECEDENCE", **events),
            release_id="precedence-release",
        )
        return result.record.phase

    return (
        cell(Action.RELEASE, terminal=True, interrupt=True, natural=True, horizon=True)
        is a1.Phase.ENDED_TERMINAL
        and cell(Action.RELEASE, interrupt=True, natural=True, horizon=True)
        is a1.Phase.ENDED_INTERRUPT
        and cell(Action.RELEASE, natural=True, horizon=True) is a1.Phase.ENDED_RELEASE
        and cell(Action.HOLD, natural=True, horizon=True) is a1.Phase.ENDED_NATURAL
        and cell(Action.HOLD, horizon=True) is a1.Phase.ENDED_HORIZON
    )


def _history_from_retained_episode(
    arm: str, episode: Mapping[str, object]
) -> list[dict[str, object]]:
    history = deepcopy(episode["observations"])
    assert isinstance(history, list)
    if arm == "CUE_BLIND_GRU":
        history[0]["cue_value"] = 0
    return history


def _validate_neural_fit_replay(fit: Mapping[str, object]) -> list[str]:
    issues: list[str] = []
    arm, seed_id = str(fit["arm"]), str(fit["seed_id"])
    model = GRUActorCritic(init_seed=stream_seed(seed_id, "init"))
    if json_ready(serialize_model(model)) != json_ready(fit["initial_state"]):
        issues.append("neural initial state replay mismatch")
        return issues
    optimizer = torch.optim.Adam(model.parameters(), lr=0.003)
    action_rng = random.Random(stream_seed(seed_id, "action"))
    episodes = fit["episodes"]
    updates = fit["optimizer"]["updates"]
    for step, batch_start in enumerate(range(0, len(episodes), B1_BATCH_SIZE)):
        batch = episodes[batch_start : batch_start + B1_BATCH_SIZE]
        update = updates[step]
        if model_digest(model) != update["parameters_before"]:
            issues.append("neural parameters-before replay mismatch")
            return issues
        actor_terms: list[Tensor] = []
        critic_terms: list[Tensor] = []
        for episode in batch:
            history = _history_from_retained_episode(arm, episode)
            probabilities, baseline, entropy = model.distribution(
                history, reset_before_decide=arm == "CURRENT_ONLY_GRU"
            )
            retained = [float(value) for value in episode["action_probabilities"]]
            if any(
                not math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=1e-15)
                for actual, expected in zip(probabilities.detach(), retained)
            ):
                issues.append("neural retained policy probability replay mismatch")
                return issues
            replay_action = (
                Action.RELEASE
                if action_rng.random() < float(probabilities[0].detach())
                else Action.HOLD
            )
            if replay_action.value != episode["action"]:
                issues.append("neural action RNG replay mismatch")
                return issues
            physical_return = torch.tensor(
                float(episode["physical_return"]), dtype=torch.float64
            )
            action = Action(str(episode["action"]))
            actor_terms.append(
                -(physical_return - baseline.detach())
                * torch.log(probabilities[action.index])
                - 0.01 * entropy
            )
            critic_terms.append(0.5 * (physical_return - baseline) ** 2)
        optimizer.zero_grad(set_to_none=True)
        loss = torch.stack(actor_terms).mean() + torch.stack(critic_terms).mean()
        loss.backward()
        unclipped = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
        if not math.isclose(float(update["loss"]), float(loss.detach()), rel_tol=0.0, abs_tol=1e-12):
            issues.append("neural loss replay mismatch")
            return issues
        if not math.isclose(
            float(update["gradient_norm_before_clip"]), unclipped, rel_tol=0.0, abs_tol=1e-12
        ):
            issues.append("neural gradient norm replay mismatch")
            return issues
        if bool(update["clipped"]) != (unclipped > 1.0):
            issues.append("neural clip status replay mismatch")
            return issues
        optimizer.step()
        after = model_digest(model)
        if after != update["parameters_after"]:
            issues.append("neural optimizer replay mismatch")
            return issues
        for episode in batch:
            if episode["learner_state"] != {
                "kind": "neural_parameter_snapshot_reference",
                "before_update": update["parameters_before"],
                "after_update": update["parameters_after"],
            }:
                issues.append("neural episode snapshot linkage mismatch")
                return issues
            if episode["gradient_clip"] != update:
                issues.append("neural episode gradient status mismatch")
                return issues
    if json_ready(serialize_model(model)) != json_ready(fit["final_state"]):
        issues.append("neural final state replay mismatch")
    return issues


def _validate_tabular_fit_replay(fit: Mapping[str, object]) -> list[str]:
    issues: list[str] = []
    arm, seed_id = str(fit["arm"]), str(fit["seed_id"])
    sums: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    if arm == "X_MEMORY_TABULAR_MONTE_CARLO":
        for cue_key in ("0", "1"):
            sums[cue_key] = [0.0, 0.0]
            counts[cue_key] = [0, 0]
    action_rng = random.Random(stream_seed(seed_id, "action"))
    for episode in fit["episodes"]:
        history = episode["observations"]
        key = (
            str(episode["presented_cue"])
            if arm == "X_MEMORY_TABULAR_MONTE_CARLO"
            else _raw_history_key(history)
        )
        before = _table_snapshot(sums, counts)
        learner_state = episode["learner_state"]
        if learner_state["key"] != key or learner_state["before"] != before:
            issues.append("tabular before-state replay mismatch")
            return issues
        probabilities = _tabular_distribution(before, key=key)
        if list(probabilities) != episode["action_probabilities"]:
            issues.append("tabular policy probability replay mismatch")
            return issues
        replay_action = Action.RELEASE if action_rng.random() < probabilities[0] else Action.HOLD
        if replay_action.value != episode["action"]:
            issues.append("tabular action RNG replay mismatch")
            return issues
        counts[key][replay_action.index] += 1
        sums[key][replay_action.index] += float(episode["physical_return"])
        after = _table_snapshot(sums, counts)
        counts_after = {name: list(value) for name, value in sorted(counts.items())}
        if learner_state["after"] != after or learner_state["counts_after"] != counts_after:
            issues.append("tabular executed-cell sample-mean replay mismatch")
            return issues
    expected_final = {
        "table": _table_snapshot(sums, counts),
        "counts": {key: list(value) for key, value in sorted(counts.items())},
    }
    if fit["final_state"] != expected_final:
        issues.append("tabular final state replay mismatch")
    return issues


def build_manifest(
    *, source_revision: str, run_id: str, technical_only: bool
) -> dict[str, object]:
    return {
        "schema_version": B1_SCHEMA_VERSION,
        "artifact_kind": "vsp02_b1v2_frozen_manifest",
        "assignment_id": B1_ASSIGNMENT_ID,
        "candidate": B1_CANDIDATE,
        "host_id": B1_HOST_ID,
        "formal": False,
        "resource_class": B1_RESOURCE_CLASS if not technical_only else "TECHNICAL_ONLY",
        "pool_units": B1_POOL_UNITS if not technical_only else 0,
        "admitted": not technical_only,
        "technical_only": technical_only,
        "source_revision": source_revision,
        "run_id": run_id,
        "seed_ids": list(B1_SEED_IDS if not technical_only else B1_SEED_IDS[:1]),
        "rng_stream_seeds": {
            seed_id: {stream: stream_seed(seed_id, stream) for stream in B1_RNG_STREAMS}
            for seed_id in (B1_SEED_IDS if not technical_only else B1_SEED_IDS[:1])
        },
        "training_blocks": B1_TRAIN_BLOCKS if not technical_only else 1,
        "episodes_per_block": B1_BLOCK_EPISODES,
        "learned_arms": list(B1_LEARNED_ARMS),
        "fixed_references": list(B1_FIXED_ARMS),
        "evaluator_only_oracle": B1_ORACLE,
        "terminal_precedence": list(B1_TERMINAL_PRECEDENCE),
        "branch_precedence": list(B1_BRANCH_PRECEDENCE),
        "caps": deepcopy(B1_CAPS),
        "a2_table_role": "EVALUATOR_CALIBRATION_ONLY_NOT_IMPORTED",
        "recovery": "ZERO_RETRY_RESCUE_SWEEP",
    }


def manifest_identity(manifest: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_bytes(manifest)).hexdigest()


def validate_manifest(manifest: object) -> tuple[str, ...]:
    if not isinstance(manifest, Mapping):
        return ("manifest is not an object",)
    issues: list[str] = []
    technical_only = manifest.get("technical_only") is True
    canonical = build_manifest(
        source_revision=str(manifest.get("source_revision", "")),
        run_id=str(manifest.get("run_id", "")),
        technical_only=technical_only,
    )
    if json_ready(manifest) != json_ready(canonical):
        issues.append("manifest differs from frozen canonical construction")
    if not manifest.get("source_revision") or not manifest.get("run_id"):
        issues.append("source_revision and run_id must be nonempty")
    return tuple(issues)


def validate_training_artifact(
    manifest: Mapping[str, object], artifact: object
) -> tuple[str, ...]:
    if not isinstance(artifact, Mapping):
        return ("training artifact is not an object",)
    issues: list[str] = []
    if artifact.get("artifact_kind") != "vsp02_b1v2_training":
        issues.append("training artifact kind mismatch")
    if artifact.get("manifest_identity") != manifest_identity(manifest):
        issues.append("training manifest identity mismatch")
    fits = artifact.get("fits")
    expected_pairs = {
        (arm, seed_id)
        for arm in B1_LEARNED_ARMS
        for seed_id in manifest["seed_ids"]  # type: ignore[index]
    }
    if not isinstance(fits, list) or {(fit.get("arm"), fit.get("seed_id")) for fit in fits} != expected_pairs:
        issues.append("training fit roster mismatch")
        return tuple(issues)
    expected_episodes = int(manifest["training_blocks"]) * B1_BLOCK_EPISODES
    for fit in fits:
        episodes = fit.get("episodes")
        if not isinstance(episodes, list) or len(episodes) != expected_episodes:
            issues.append(f"{fit.get('arm')}|{fit.get('seed_id')} episode count mismatch")
            continue
        for episode in episodes:
            issues.extend(_episode_issues(episode))
        by_block: dict[int, list[Mapping[str, object]]] = defaultdict(list)
        for episode in episodes:
            by_block[int(episode["block"])].append(episode)
        if any(
            sum(int(row["true_cue"]) == cue for row in rows) != 32
            for rows in by_block.values()
            for cue in (0, 1)
        ):
            issues.append("true cue block balance mismatch")
        if fit["arm"] == "CUE_SHUFFLED_GRU" and any(
            sum(
                int(row["true_cue"]) == true_cue
                and int(row["presented_cue"]) == presented_cue
                for row in rows
            )
            != 16
            for rows in by_block.values()
            for true_cue in (0, 1)
            for presented_cue in (0, 1)
        ):
            issues.append("shuffled cue crossing mismatch")
        if fit["kind"] == "neural" and len(fit["optimizer"]["updates"]) != expected_episodes // B1_BATCH_SIZE:
            issues.append("neural optimizer update count mismatch")
        if fit["kind"] == "neural":
            snapshots = fit.get("parameter_snapshots")
            if not isinstance(snapshots, Mapping):
                issues.append("neural parameter snapshots missing")
            else:
                referenced = {
                    digest
                    for episode in episodes
                    for digest in (
                        episode["learner_state"]["before_update"],
                        episode["learner_state"]["after_update"],
                    )
                }
                if not referenced.issubset(snapshots):
                    issues.append("neural episode references unresolved parameter snapshot")
                if any(
                    hashlib.sha256(canonical_bytes(snapshot)).hexdigest() != digest
                    for digest, snapshot in snapshots.items()
                ):
                    issues.append("neural parameter snapshot digest mismatch")
            issues.extend(_validate_neural_fit_replay(fit))
        if fit["kind"] == "tabular" and fit.get("updates") != expected_episodes:
            issues.append("tabular update count mismatch")
        if fit["kind"] == "tabular":
            issues.extend(_validate_tabular_fit_replay(fit))
    recomputed_activity = sum_activity(
        episode for fit in fits for episode in fit["episodes"]
    )
    if artifact.get("activity") != recomputed_activity:
        issues.append("training activity summary mismatch")
    if not _initial_firewall_valid(artifact) or not _arm_matching_valid(artifact):
        issues.append("initial firewall or neural arm matching mismatch")
    if manifest["technical_only"] is False:
        if recomputed_activity.get("learner_calls") != 30_720:
            issues.append("learner call count mismatch")
        if recomputed_activity.get("trainer_calls") != 30_720:
            issues.append("trainer call count mismatch")
        if recomputed_activity.get("optimizer_updates") != 640:
            issues.append("neural optimizer update count mismatch")
        if recomputed_activity.get("tabular_updates") != 10_240:
            issues.append("tabular update count mismatch")
    return tuple(issues)


def validate_evaluation_artifact(
    manifest: Mapping[str, object], training: Mapping[str, object], artifact: object
) -> tuple[str, ...]:
    if not isinstance(artifact, Mapping):
        return ("evaluation artifact is not an object",)
    issues: list[str] = []
    if artifact.get("artifact_kind") != "vsp02_b1v2_evaluation":
        issues.append("evaluation artifact kind mismatch")
    if artifact.get("manifest_identity") != manifest_identity(manifest):
        issues.append("evaluation manifest identity mismatch")
    evaluations = artifact.get("evaluations")
    expected = len(training["fits"]) + (0 if manifest["technical_only"] else 4)  # type: ignore[arg-type]
    if not isinstance(evaluations, list) or len(evaluations) != expected:
        issues.append("evaluation roster mismatch")
        return tuple(issues)
    for item in evaluations:
        rows = item.get("rows")
        if not isinstance(rows, list) or len(rows) != 64:
            issues.append(f"{item.get('arm')} evaluation panel mismatch")
            continue
        for row in rows:
            issues.extend(_episode_issues(row))
            if row.get("evaluation_update") is not False:
                issues.append("evaluation update occurred")
        try:
            summary = summarize_evaluation_rows(rows)
        except (KeyError, TypeError, ValueError) as exc:
            issues.append(f"evaluation summary reconstruction failed: {exc}")
        else:
            if json_ready(item.get("summary")) != json_ready(summary):
                issues.append("evaluation summary mismatch")
    rows = [row for item in evaluations for row in item["rows"]]
    if artifact.get("activity") != sum_activity(rows):
        issues.append("evaluation activity summary mismatch")
    if manifest["technical_only"] is False and len(rows) != 2_176:
        issues.append("registered evaluation episode count mismatch")
    return tuple(issues)


def validate_analysis_artifact(
    manifest: Mapping[str, object],
    training: Mapping[str, object],
    evaluation: Mapping[str, object],
    artifact: object,
) -> tuple[str, ...]:
    if not isinstance(artifact, Mapping):
        return ("analysis artifact is not an object",)
    expected = compute_analysis(manifest, training, evaluation)
    return (
        ()
        if json_ready(artifact) == json_ready(expected)
        else ("analysis differs from independent retained-row reconstruction",)
    )


def validate_artifact_bundle(
    manifest: object, training: object, evaluation: object, analysis: object
) -> tuple[str, ...]:
    manifest_issues = validate_manifest(manifest)
    if manifest_issues or not isinstance(manifest, Mapping):
        return manifest_issues
    training_issues = validate_training_artifact(manifest, training)
    if training_issues or not isinstance(training, Mapping):
        return training_issues
    evaluation_issues = validate_evaluation_artifact(manifest, training, evaluation)
    if evaluation_issues or not isinstance(evaluation, Mapping):
        return evaluation_issues
    return validate_analysis_artifact(manifest, training, evaluation, analysis)

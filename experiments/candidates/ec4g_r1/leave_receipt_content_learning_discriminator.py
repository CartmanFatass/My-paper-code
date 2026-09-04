"""EC4G-B1 leave-receipt content learning discriminator.

The treatment is deliberately self-contained.  Two matched replicas learn in
the same four-step delayed-relay host; treatment identity enters only after the
actor, critic, optimizer, calibration table, and derived gate inputs are
sealed.  Retained-result validation is intentionally pure and never re-enters
the host, learner, optimizer, or evaluator.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from functools import lru_cache
import hashlib
import json
import math
from typing import Iterable, Mapping, Sequence

import torch
from torch import Tensor, nn


SCHEMA_VERSION = 1
ASSIGNMENT_ID = "EC4G-B1-LEAVE-RECEIPT-CONTENT-LEARNING-DISCRIMINATOR"
CANDIDATE = "CAND-VAP-EC4G-R1@rer3-prospective-complete-v8"
RESOURCE_CLASS = "B_TOY_LIGHT"
POOL_UNITS = 1
ACCEPTED_A5_SOURCE = "454e762241d145c94af2874405dd77b64071632e"
ACCEPTED_A5_PUBLICATION = "1f087574f6614d6ea96879ccca9ec143755c4937"
SEED_PREFIX = "EC4G_B1_V1"
OUTER_SEEDS = tuple(range(41_001, 41_009))
REPLICAS = ("EC4G", "DIRECT_TAU")
Q_VALUES = ("q0", "q1")
ARMS = ("R0", "RV", "RB", "RS", "PV", "PB", "PS")
PHYSICAL_ARMS = frozenset(("RV", "RB", "RS"))
SPLITS = ("TRAIN", "CALIBRATION", "FORCED_EVAL", "AUTONOMOUS_EVAL")
LANES = (
    "tag_permutation",
    "latent_z",
    "public_cue",
    "own_sensor",
    "blind_payload",
    "donor_record",
    "arm_order",
    "policy_action",
    "actuation",
)
TAG_DOMAINS = {
    "TRAIN": (0x0000, 0x007F),
    "CALIBRATION": (0x0100, 0x017F),
    "FORCED_EVAL": (0x0200, 0x02FF),
    "AUTONOMOUS_EVAL": (0x0300, 0x03FF),
}
BLIND_TAG = 0xFFFF
SPLIT_EPISODES = {
    "TRAIN": 128,
    "CALIBRATION": 128,
    "FORCED_EVAL": 256,
    "AUTONOMOUS_EVAL": 256,
}
HIDDEN_SIZE = 32
OBSERVATION_SIZE = 43
GAMMA = 1.0
LEARNING_RATE = 0.003
ENTROPY_COEFFICIENT = 0.01
VALUE_COEFFICIENT = 0.5
GRADIENT_CAP = 1.0
TAU = 0.02
BRANCH_PRECEDENCE = (
    "B1_STATIC_PREFLIGHT_INVALID",
    "B1_TAG_DONOR_MATCH_OR_Q1_NULL_FIREWALL_FAILED",
    "B1_ACTIVITY_OR_EVALUATION_PANEL_INCOMPLETE",
    "B1_FORCED_ARM_TREATMENT_INVARIANCE_FAILED",
    "B1_CONTENT_OR_PHYSICAL_CALIBRATION_FAILED",
    "B1_NO_LEARNED_Q1_GATE_DIVERGENCE",
    "B1_DIRECT_GENERIC_PROBE_EXPLORATORY_SIGNAL",
    "B1_CONTENT_SELECTIVITY_NO_MATERIAL_RETURN_SEPARATION",
    "B1_EC4G_POSITIVE_FINITE_PANEL_ANOMALY",
)
CAPS = {
    "episodes": 122_880,
    "environment_transitions": 491_520,
    "batched_policy_calls": 491_520,
    "active_agent_forward_rows": 1_105_920,
    "learner_calls": 2_048,
    "trainer_calls": 2_048,
    "optimizer_updates": 2_048,
    "calibration_table_updates": 28_672,
    "held_out_evaluation_episodes": 65_536,
    "final_checkpoints": 16,
    "registered_paired_fulls": 1,
    "cpu_minutes": 60,
    "peak_memory_gib": 2,
    "pool_units": 1,
}
CLAIM_PATHS = (
    "experiments/candidates/ec4g_r1/leave_receipt_content_learning_discriminator.py",
    "scripts/run_ec4g_b1_leave_receipt_content_learning_discriminator.py",
    "tests/experiments/candidates/ec4g_r1/test_leave_receipt_content_learning_discriminator.py",
    "docs/research/candidates/ec4g_r1/EC4G_B1_CODE_SCIENCE_INDEX.md",
)


def json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return json_ready(asdict(value))
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


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def tuple_seed(
    outer_seed: int,
    split: str,
    phase: str,
    q: str,
    arm: str,
    episode: int,
    lane: str,
    draw_index: int,
) -> int:
    """Frozen random-access counter seed (first eight bytes, little endian)."""

    if outer_seed not in OUTER_SEEDS:
        raise ValueError(f"unregistered outer seed: {outer_seed}")
    if split not in SPLITS:
        raise ValueError(f"unregistered split: {split}")
    if lane not in LANES:
        raise ValueError(f"unregistered lane: {lane}")
    material = "|".join(
        (
            SEED_PREFIX,
            str(outer_seed),
            split,
            phase,
            q,
            arm,
            str(int(episode)),
            lane,
            str(int(draw_index)),
        )
    ).encode("ascii")
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "little")


def _uniform(*key: object) -> float:
    # Each tuple already addresses one draw.  Consuming the frozen counter word
    # directly avoids a hidden stateful PRNG engine or any order dependence.
    return (tuple_seed(*key) + 0.5) / float(1 << 64)  # type: ignore[arg-type]


def _bit(*key: object, p: float = 0.5) -> int:
    return int(_uniform(*key) < p)


def _xor_noise(value: int, *key: object, probability: float) -> int:
    return int(value) ^ _bit(*key, p=probability)


@lru_cache(maxsize=None)
def split_tags(outer_seed: int, split: str) -> tuple[int, ...]:
    """One q/arm/treatment-blind keyed permutation for the whole split."""

    lo, hi = TAG_DOMAINS[split]
    tags = list(range(lo, hi + 1))
    tags.sort(
        key=lambda tag: tuple_seed(
            outer_seed,
            split,
            "TAG_ASSIGNMENT",
            "SHARED",
            "SHARED",
            tag,
            "tag_permutation",
            0,
        )
    )
    return tuple(tags)


@dataclass(frozen=True)
class DonorRecord:
    record_index: int
    tag: int
    latent_z: int
    payload: int


@lru_cache(maxsize=None)
def donor_records(outer_seed: int, split: str, q: str) -> tuple[DonorRecord, ...]:
    if split == "AUTONOMOUS_EVAL":
        return ()
    n = SPLIT_EPISODES[split]
    tags = split_tags(outer_seed, split)
    raw = tuple_seed(
        outer_seed,
        split,
        "DONOR_TABLE",
        q,
        "SHARED",
        0,
        "donor_record",
        0,
    )
    allowed_shifts = tuple(shift for shift in range(1, n) if shift != n // 2)
    shift = allowed_shifts[raw % len(allowed_shifts)]
    records: list[DonorRecord] = []
    for index in range(n):
        tag = tags[(index + shift) % n]
        z = _bit(
            outer_seed,
            split,
            "DONOR_TABLE",
            q,
            "SHARED",
            index,
            "donor_record",
            1,
        )
        if q == "q0":
            payload = _xor_noise(
                z,
                outer_seed,
                split,
                "DONOR_TABLE",
                q,
                "SHARED",
                index,
                "donor_record",
                2,
                probability=0.10,
            )
        else:
            payload = _bit(
                outer_seed,
                split,
                "DONOR_TABLE",
                q,
                "SHARED",
                index,
                "donor_record",
                2,
            )
        records.append(DonorRecord(index, tag, z, payload))
    return tuple(records)


def _body_family(arm: str) -> str:
    return {"PV": "RV", "PB": "RB", "PS": "RS"}.get(arm, arm)


def receipt_body(
    *,
    outer_seed: int,
    split: str,
    q: str,
    arm: str,
    episode: int,
    own_y: int,
) -> dict[str, int]:
    family = _body_family(arm)
    current_tag = split_tags(outer_seed, split)[episode]
    if family == "R0":
        return {"present": 0, "tag": 0, "payload": 0}
    if family == "RV":
        return {"present": 1, "tag": current_tag, "payload": int(own_y)}
    if family == "RB":
        payload = _bit(
            outer_seed,
            split,
            "EPISODE",
            q,
            "SHARED",
            episode,
            "blind_payload",
            0,
        )
        return {"present": 1, "tag": BLIND_TAG, "payload": payload}
    if family == "RS":
        records = donor_records(outer_seed, split, q)
        donor_index = (episode + len(records) // 2) % len(records)
        donor = records[donor_index]
        return {"present": 1, "tag": donor.tag, "payload": donor.payload}
    raise ValueError(f"unknown arm: {arm}")


def construction_audit(outer_seed: int) -> dict[str, object]:
    tag_rows: dict[str, dict[str, object]] = {}
    donor_rows: dict[str, dict[str, object]] = {}
    all_passed = True
    matched_body_checks = 0
    matched_body_failures = 0
    for split in SPLITS:
        tags = split_tags(outer_seed, split)
        lo, hi = TAG_DOMAINS[split]
        passed = (
            len(tags) == SPLIT_EPISODES[split]
            and len(set(tags)) == len(tags)
            and set(tags) == set(range(lo, hi + 1))
            and BLIND_TAG not in tags
        )
        all_passed &= passed
        tag_rows[split] = {
            "count": len(tags),
            "domain": [lo, hi],
            "permutation_digest": digest(tags),
            "passed": passed,
        }
        if split == "AUTONOMOUS_EVAL":
            continue
        n = SPLIT_EPISODES[split]
        for q in Q_VALUES:
            records = donor_records(outer_seed, split, q)
            passed = len(records) == n and all(
                (episode + n // 2) % n != episode
                and records[(episode + n // 2) % n].tag != tags[episode]
                for episode in range(n)
            )
            all_passed &= passed
            donor_rows[f"{split}/{q}"] = {
                "count": len(records),
                "offset": n // 2,
                "table_digest": digest(records),
                "passed": passed,
            }
            for episode in range(n):
                for own_y in (0, 1):
                    for physical, sham in (
                        ("RV", "PV"),
                        ("RB", "PB"),
                        ("RS", "PS"),
                    ):
                        matched_body_checks += 1
                        matched = canonical_bytes(
                            receipt_body(
                                outer_seed=outer_seed,
                                split=split,
                                q=q,
                                arm=physical,
                                episode=episode,
                                own_y=own_y,
                            )
                        ) == canonical_bytes(
                            receipt_body(
                                outer_seed=outer_seed,
                                split=split,
                                q=q,
                                arm=sham,
                                episode=episode,
                                own_y=own_y,
                            )
                        )
                        all_passed &= matched
                        matched_body_failures += int(not matched)
    return {
        "outer_seed": outer_seed,
        "tag_domains": tag_rows,
        "donor_tables": donor_rows,
        "matched_body_checks": matched_body_checks,
        "matched_body_failures": matched_body_failures,
        "tuple_serializer_has_treatment_field": False,
        "autonomous_exogenous_arm_key": "AUTONOMOUS_SHARED",
        "all_passed": all_passed,
    }


def terminal_reward(z: int, executed_bits: Sequence[int], physical_probe: bool) -> float:
    """The entire reward firewall: only z, executed bits, and probe status."""

    if len(executed_bits) != 2 or z not in (0, 1):
        raise ValueError("terminal reward requires z and two executed bits")
    return float(all(int(bit) == int(z) for bit in executed_bits)) - 0.02 * int(
        physical_probe
    )


def _tag_bits(tag: int) -> list[float]:
    return [float((tag >> bit) & 1) for bit in range(16)]


def observation_vector(
    phase: int,
    *,
    q: str | None = None,
    x: int | None = None,
    current_tag: int | None = None,
    receipt: Mapping[str, int] | None = None,
) -> Tensor:
    phase_bits = [float(index == phase) for index in range(4)]
    q_fields = [float(q is not None), float(q == "q1") if q is not None else 0.0]
    x_fields = [float(x is not None), float(x) if x is not None else 0.0]
    tag_fields = [float(current_tag is not None)] + (
        _tag_bits(int(current_tag)) if current_tag is not None else [0.0] * 16
    )
    if receipt is None:
        receipt_fields = [0.0] + [0.0] * 16 + [0.0]
    else:
        present = int(receipt["present"])
        receipt_fields = [float(present)] + _tag_bits(int(receipt["tag"])) + [
            float(receipt["payload"])
        ]
    vector = torch.tensor(
        phase_bits + q_fields + x_fields + tag_fields + receipt_fields,
        dtype=torch.float64,
    )
    if vector.numel() != OBSERVATION_SIZE:
        raise AssertionError("observation layout changed")
    return vector


class _NoInitGRUCell(nn.GRUCell):
    def reset_parameters(self) -> None:
        """All coordinates are filled by the frozen named-coordinate builder."""


class _NoInitLinear(nn.Linear):
    def reset_parameters(self) -> None:
        """All coordinates are filled by the frozen named-coordinate builder."""


class SharedGRUA2C(nn.Module):
    """One parameter-shared survivor GRU and one centralized value head."""

    def __init__(self, *, device: str | torch.device | None = None) -> None:
        super().__init__()
        self.gru = _NoInitGRUCell(
            OBSERVATION_SIZE,
            HIDDEN_SIZE,
            dtype=torch.float64,
            device=device,
        )
        self.actor = _NoInitLinear(
            HIDDEN_SIZE, 2, dtype=torch.float64, device=device
        )
        self.value = _NoInitLinear(
            HIDDEN_SIZE + 3, 1, dtype=torch.float64, device=device
        )

    def advance(self, observations: Tensor, hidden: Tensor) -> Tensor:
        return self.gru(observations, hidden)

    def logits(self, hidden: Tensor) -> Tensor:
        return self.actor(hidden)

    def centralized_value(self, hidden: Tensor, mask: Sequence[int]) -> Tensor:
        active = torch.tensor(mask, dtype=torch.float64, device=hidden.device)
        pooled = hidden.mean(dim=0)
        return self.value(torch.cat((pooled, active))).squeeze(0)


PARAMETER_SHAPES = {
    "actor.bias": (2,),
    "actor.weight": (2, HIDDEN_SIZE),
    "gru.bias_hh": (3 * HIDDEN_SIZE,),
    "gru.bias_ih": (3 * HIDDEN_SIZE,),
    "gru.weight_hh": (3 * HIDDEN_SIZE, HIDDEN_SIZE),
    "gru.weight_ih": (3 * HIDDEN_SIZE, OBSERVATION_SIZE),
    "value.bias": (1,),
    "value.weight": (1, HIDDEN_SIZE + 3),
}
PARAMETER_ORDER = tuple(sorted(PARAMETER_SHAPES))


def parameter_initialization_payload(
    outer_seed: int, parameter_order: Sequence[str] = PARAMETER_ORDER
) -> dict[str, Tensor]:
    """Stable named-coordinate initialization with no Torch/global RNG."""

    if set(parameter_order) != set(PARAMETER_ORDER) or len(parameter_order) != len(
        PARAMETER_ORDER
    ):
        raise ValueError("parameter initialization order must name every parameter once")
    bound = 1.0 / math.sqrt(HIDDEN_SIZE)
    payload: dict[str, Tensor] = {}
    for name in parameter_order:
        shape = PARAMETER_SHAPES[name]
        count = math.prod(shape)
        values = [
            (2.0 * _uniform(
                outer_seed,
                "TRAIN",
                f"PARAMETER_INITIALIZATION:{name}",
                "SHARED",
                "SHARED",
                0,
                "policy_action",
                draw_index,
            ) - 1.0)
            * bound
            for draw_index in range(count)
        ]
        payload[name] = torch.tensor(values, dtype=torch.float64).reshape(shape)
    return payload


def _new_model(outer_seed: int) -> SharedGRUA2C:
    # The exact GRU/Linear subclasses suppress their default random reset;
    # every allocated CPU coordinate is overwritten from the frozen tuple.
    model = SharedGRUA2C(device="cpu")
    payload = parameter_initialization_payload(outer_seed)
    named = dict(model.named_parameters())
    if {name: tuple(parameter.shape) for name, parameter in named.items()} != PARAMETER_SHAPES:
        raise AssertionError("SharedGRUA2C parameter layout changed")
    with torch.no_grad():
        for name in PARAMETER_ORDER:
            named[name].copy_(payload[name])
    return model


def model_payload(model: nn.Module) -> dict[str, object]:
    return {
        name: {
            "dtype": str(tensor.dtype),
            "shape": list(tensor.shape),
            "values": tensor.detach().cpu().contiguous().reshape(-1).tolist(),
        }
        for name, tensor in sorted(model.state_dict().items())
    }


def optimizer_payload(optimizer: torch.optim.Optimizer) -> object:
    return json_ready(optimizer.state_dict())


def training_order(outer_seed: int, block: int) -> tuple[tuple[str, str], ...]:
    combinations = [(q, arm) for q in Q_VALUES for arm in ARMS]
    combinations.sort(
        key=lambda item: tuple_seed(
            outer_seed,
            "TRAIN",
            "BLOCK_ORDER",
            item[0],
            item[1],
            block,
            "arm_order",
            0,
        )
    )
    return tuple(combinations)


def episode_latents(
    outer_seed: int, split: str, q: str, arm: str, episode: int
) -> tuple[int, int, int]:
    # AUTONOMOUS keys cannot depend on the treatment-selected RV/R0 arm.
    key_arm = "AUTONOMOUS_SHARED" if split == "AUTONOMOUS_EVAL" else arm
    z = _bit(
        outer_seed, split, "EPISODE", q, key_arm, episode, "latent_z", 0
    )
    x = _xor_noise(
        z,
        outer_seed,
        split,
        "EPISODE",
        q,
        key_arm,
        episode,
        "public_cue",
        0,
        probability=0.30,
    )
    if q == "q0":
        y = _xor_noise(
            z,
            outer_seed,
            split,
            "EPISODE",
            q,
            key_arm,
            episode,
            "own_sensor",
            0,
            probability=0.10,
        )
    else:
        y = _bit(
            outer_seed,
            split,
            "EPISODE",
            q,
            key_arm,
            episode,
            "own_sensor",
            0,
        )
    return z, x, y


def _action_uniform(
    outer_seed: int, split: str, q: str, arm: str, episode: int, agent: int
) -> float:
    key_arm = "AUTONOMOUS_SHARED" if split == "AUTONOMOUS_EVAL" else arm
    return _uniform(
        outer_seed,
        split,
        "TERMINAL",
        q,
        key_arm,
        episode,
        "policy_action",
        agent,
    )


def _actuation_uniform(
    outer_seed: int, split: str, q: str, arm: str, episode: int, agent: int
) -> float:
    key_arm = "AUTONOMOUS_SHARED" if split == "AUTONOMOUS_EVAL" else arm
    return _uniform(
        outer_seed,
        split,
        "TERMINAL",
        q,
        key_arm,
        episode,
        "actuation",
        agent,
    )


class FourStepRelayHost:
    """Exact fresh four-transition host with one t1 probe opportunity."""

    def __init__(self, *, outer_seed: int, split: str, q: str, arm: str, episode: int):
        self.outer_seed = outer_seed
        self.split = split
        self.q = q
        self.arm = arm
        self.episode = episode
        self.z, self.x, self.y = episode_latents(outer_seed, split, q, arm, episode)
        self.current_tag = split_tags(outer_seed, split)[episode]
        receipt_y = self.y
        if arm == "PV":
            # The sham body is the byte-identical corresponding RV object, not
            # a re-encoding of the sham episode's independently keyed sensor.
            _, _, receipt_y = episode_latents(outer_seed, split, q, "RV", episode)
        self.receipt = receipt_body(
            outer_seed=outer_seed,
            split=split,
            q=q,
            arm=arm,
            episode=episode,
            own_y=receipt_y,
        )
        self.physical_probe = arm in PHYSICAL_ARMS
        self.phase = 0
        self.transitions = 0
        self.probe_opportunities = 0

    def step(self) -> Tensor:
        if self.phase >= 4:
            raise RuntimeError("episode already terminal")
        if self.phase == 0:
            vector = observation_vector(
                0, q=self.q, x=self.x, current_tag=self.current_tag
            )
        elif self.phase == 1:
            self.probe_opportunities += 1
            vector = observation_vector(1)
        elif self.phase == 2:
            vector = observation_vector(2, receipt=self.receipt)
        else:
            vector = observation_vector(3)
        self.phase += 1
        self.transitions += 1
        return vector

    def finish(self, intended_bits: Sequence[int]) -> tuple[list[int], float]:
        if self.phase != 4 or self.probe_opportunities != 1:
            raise RuntimeError("terminal action requires the exact four-step path")
        executed: list[int] = []
        for agent, intended in enumerate(intended_bits):
            flip_probability = 0.02 if agent == 1 and self.physical_probe else 0.10
            flip = _actuation_uniform(
                self.outer_seed,
                self.split,
                self.q,
                self.arm,
                self.episode,
                agent,
            ) < flip_probability
            executed.append(int(intended) ^ int(flip))
        return executed, terminal_reward(self.z, executed, self.physical_probe)


def run_episode(
    model: SharedGRUA2C,
    *,
    outer_seed: int,
    split: str,
    q: str,
    arm: str,
    episode: int,
    stochastic: bool,
) -> dict[str, object]:
    host = FourStepRelayHost(
        outer_seed=outer_seed, split=split, q=q, arm=arm, episode=episode
    )
    hidden = torch.zeros((3, HIDDEN_SIZE), dtype=torch.float64)
    values: list[Tensor] = []
    policy_calls = 0
    forward_rows = 0
    for phase in range(4):
        observation = host.step()
        active = 3 if phase == 0 else 2
        if phase == 1:
            hidden = hidden[:2]
        batch = observation.unsqueeze(0).repeat(active, 1)
        hidden = model.advance(batch, hidden)
        values.append(model.centralized_value(hidden, (1, 1, 1 if active == 3 else 0)))
        policy_calls += 1
        forward_rows += active
    logits = model.logits(hidden)
    probabilities = torch.softmax(logits, dim=-1)
    actions: list[int] = []
    for agent in range(2):
        if stochastic:
            actions.append(
                int(
                    _action_uniform(outer_seed, split, q, arm, episode, agent)
                    >= float(probabilities[agent, 0].detach())
                )
            )
        else:
            # torch.argmax returns the first index, hence exact ties choose zero.
            actions.append(int(torch.argmax(logits[agent]).item()))
    executed, reward = host.finish(actions)
    selected_log_probs = torch.stack(
        [torch.log(probabilities[index, action]) for index, action in enumerate(actions)]
    )
    entropy = -(probabilities * torch.log(probabilities)).sum(dim=1).mean()
    return {
        "reward": reward,
        "z": host.z,
        "actions": actions,
        "executed": executed,
        "physical_probe": host.physical_probe,
        "receipt": dict(host.receipt),
        "current_tag": host.current_tag,
        "team_log_probability": selected_log_probs.mean(),
        "entropy": entropy,
        "values": values,
        "environment_transitions": host.transitions,
        "batched_policy_calls": policy_calls,
        "active_agent_forward_rows": forward_rows,
    }


def _episode_loss(row: Mapping[str, object]) -> Tensor:
    reward = torch.tensor(float(row["reward"]), dtype=torch.float64)
    values = row["values"]
    assert isinstance(values, Sequence)
    advantage = reward - values[-1]
    actor_loss = -row["team_log_probability"] * advantage.detach()  # type: ignore[operator]
    entropy_term = -ENTROPY_COEFFICIENT * row["entropy"]  # type: ignore[operator]
    value_loss = torch.stack([(reward - value) ** 2 for value in values]).mean()
    return actor_loss + entropy_term + VALUE_COEFFICIENT * value_loss


def _zero_activity() -> dict[str, int]:
    return {
        "episodes": 0,
        "training_episodes": 0,
        "calibration_episodes": 0,
        "forced_evaluation_episodes": 0,
        "autonomous_evaluation_episodes": 0,
        "held_out_evaluation_episodes": 0,
        "environment_transitions": 0,
        "batched_policy_calls": 0,
        "active_agent_forward_rows": 0,
        "learner_calls": 0,
        "trainer_calls": 0,
        "optimizer_updates": 0,
        "calibration_table_updates": 0,
        "final_checkpoints": 0,
        "registered_paired_fulls": 0,
        "retry_rescue_sweep": 0,
    }


def _add_episode_activity(activity: dict[str, int], row: Mapping[str, object], split: str) -> None:
    activity["episodes"] += 1
    activity["environment_transitions"] += int(row["environment_transitions"])
    activity["batched_policy_calls"] += int(row["batched_policy_calls"])
    activity["active_agent_forward_rows"] += int(row["active_agent_forward_rows"])
    field = {
        "TRAIN": "training_episodes",
        "CALIBRATION": "calibration_episodes",
        "FORCED_EVAL": "forced_evaluation_episodes",
        "AUTONOMOUS_EVAL": "autonomous_evaluation_episodes",
    }[split]
    activity[field] += 1
    if split in ("FORCED_EVAL", "AUTONOMOUS_EVAL"):
        activity["held_out_evaluation_episodes"] += 1


def train_replica(outer_seed: int) -> tuple[SharedGRUA2C, torch.optim.Optimizer, dict[str, int]]:
    model = _new_model(outer_seed)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    activity = _zero_activity()
    for block in range(128):
        losses: list[Tensor] = []
        for q, arm in training_order(outer_seed, block):
            row = run_episode(
                model,
                outer_seed=outer_seed,
                split="TRAIN",
                q=q,
                arm=arm,
                episode=block,
                stochastic=True,
            )
            losses.append(_episode_loss(row))
            _add_episode_activity(activity, row, "TRAIN")
        activity["learner_calls"] += 1
        loss = torch.stack(losses).mean()
        activity["trainer_calls"] += 1
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CAP)
        optimizer.step()
        activity["optimizer_updates"] += 1
    activity["final_checkpoints"] = 1
    return model, optimizer, activity


def calibration_table(
    model: SharedGRUA2C, outer_seed: int, activity: dict[str, int]
) -> dict[str, dict[str, dict[str, float | int]]]:
    table = {
        q: {arm: {"sum": 0.0, "count": 0} for arm in ARMS} for q in Q_VALUES
    }
    model.eval()
    with torch.no_grad():
        for q in Q_VALUES:
            for arm in ARMS:
                for episode in range(128):
                    row = run_episode(
                        model,
                        outer_seed=outer_seed,
                        split="CALIBRATION",
                        q=q,
                        arm=arm,
                        episode=episode,
                        stochastic=False,
                    )
                    table[q][arm]["sum"] = float(table[q][arm]["sum"]) + float(
                        row["reward"]
                    )
                    table[q][arm]["count"] = int(table[q][arm]["count"]) + 1
                    activity["calibration_table_updates"] += 1
                    _add_episode_activity(activity, row, "CALIBRATION")
    return table


def derived_gate_inputs(
    table: Mapping[str, Mapping[str, Mapping[str, float | int]]]
) -> dict[str, dict[str, float]]:
    output: dict[str, dict[str, float]] = {}
    for q in Q_VALUES:
        means = {
            arm: float(table[q][arm]["sum"]) / int(table[q][arm]["count"])
            for arm in ARMS
        }
        output[q] = {
            "T": means["RV"] - means["R0"],
            "C": means["RV"] - means["RS"],
            "V": means["RV"] - means["RB"],
        }
    return output


def gate_label(treatment: str, inputs: Mapping[str, float]) -> str:
    t = float(inputs["T"])
    if t < -TAU:
        return "N"
    if treatment == "DIRECT_TAU" and t > TAU:
        return "P"
    if treatment == "EC4G":
        # Direct is forbidden to consume C/V.  They are read only inside the
        # EC4G arm after treatment selection reaches this branch.
        c, v = float(inputs["C"]), float(inputs["V"])
        if t > TAU and c > TAU and v > TAU:
            return "P"
    elif treatment != "DIRECT_TAU":
        raise ValueError(f"unknown treatment: {treatment}")
    return "A"


def _evaluate_forced(
    model: SharedGRUA2C, outer_seed: int, activity: dict[str, int]
) -> dict[str, dict[str, dict[str, float | int]]]:
    output: dict[str, dict[str, dict[str, float | int]]] = {}
    model.eval()
    with torch.no_grad():
        for q in Q_VALUES:
            output[q] = {}
            for arm in ARMS:
                returns = 0.0
                intended_correct = 0
                executed_success = 0
                for episode in range(256):
                    row = run_episode(
                        model,
                        outer_seed=outer_seed,
                        split="FORCED_EVAL",
                        q=q,
                        arm=arm,
                        episode=episode,
                        stochastic=False,
                    )
                    returns += float(row["reward"])
                    intended_correct += sum(
                        int(action == row["z"]) for action in row["actions"]  # type: ignore[union-attr]
                    )
                    executed_success += int(
                        all(bit == row["z"] for bit in row["executed"])  # type: ignore[union-attr]
                    )
                    _add_episode_activity(activity, row, "FORCED_EVAL")
                output[q][arm] = {
                    "episodes": 256,
                    "mean_return": returns / 256.0,
                    "mean_intended_action_accuracy": intended_correct / 512.0,
                    "mean_executed_team_success": executed_success / 256.0,
                }
    return output


def _evaluate_autonomous(
    model: SharedGRUA2C,
    outer_seed: int,
    treatment: str,
    gates: Mapping[str, str],
    activity: dict[str, int],
) -> dict[str, object]:
    by_q: dict[str, dict[str, object]] = {}
    model.eval()
    with torch.no_grad():
        for q in Q_VALUES:
            arm = "RV" if gates[q] == "P" else "R0"
            returns = 0.0
            probes = 0
            for episode in range(256):
                row = run_episode(
                    model,
                    outer_seed=outer_seed,
                    split="AUTONOMOUS_EVAL",
                    q=q,
                    arm=arm,
                    episode=episode,
                    stochastic=False,
                )
                returns += float(row["reward"])
                probes += int(row["physical_probe"])
                _add_episode_activity(activity, row, "AUTONOMOUS_EVAL")
            by_q[q] = {
                "gate": gates[q],
                "executed_arm": arm,
                "episodes": 256,
                "mean_return": returns / 256.0,
                "probe_rate": probes / 256.0,
            }
    return {
        "treatment": treatment,
        "by_q": by_q,
        "balanced_return": 0.5
        * (float(by_q["q0"]["mean_return"]) + float(by_q["q1"]["mean_return"])),
        "probe_selectivity": float(by_q["q0"]["probe_rate"])
        - float(by_q["q1"]["probe_rate"]),
    }


def _sum_activity(*items: Mapping[str, int]) -> dict[str, int]:
    result = _zero_activity()
    for item in items:
        for key in result:
            result[key] += int(item.get(key, 0))
    return result


def run_unit(outer_seed: int) -> dict[str, object]:
    audit = construction_audit(outer_seed)
    replicas: dict[str, dict[str, object]] = {}
    sealed: dict[str, dict[str, object]] = {}
    for treatment in REPLICAS:
        model, optimizer, activity = train_replica(outer_seed)
        table = calibration_table(model, outer_seed, activity)
        inputs = derived_gate_inputs(table)
        sealed[treatment] = {
            "model": model_payload(model),
            "optimizer": optimizer_payload(optimizer),
            "calibration": table,
            "gate_inputs": inputs,
        }
        replicas[treatment] = {
            "model_object": model,
            "activity": activity,
            "calibration": table,
            "gate_inputs": inputs,
            "gates": {q: gate_label(treatment, inputs[q]) for q in Q_VALUES},
        }
    equality = {
        key: digest(sealed[REPLICAS[0]][key]) == digest(sealed[REPLICAS[1]][key])
        for key in ("model", "optimizer", "calibration", "gate_inputs")
    }
    for treatment in REPLICAS:
        record = replicas[treatment]
        model = record.pop("model_object")
        assert isinstance(model, SharedGRUA2C)
        activity = record["activity"]
        assert isinstance(activity, dict)
        record["forced"] = _evaluate_forced(model, outer_seed, activity)
        record["autonomous"] = _evaluate_autonomous(
            model,
            outer_seed,
            treatment,
            record["gates"],  # type: ignore[arg-type]
            activity,
        )
        record["checkpoint_state"] = sealed[treatment]["model"]
        record["optimizer_final_state"] = sealed[treatment]["optimizer"]
        record["checkpoint_digest"] = digest(sealed[treatment]["model"])
        record["optimizer_digest"] = digest(sealed[treatment]["optimizer"])
    forced_equal = canonical_bytes(replicas["EC4G"]["forced"]) == canonical_bytes(
        replicas["DIRECT_TAU"]["forced"]
    )
    return {
        "outer_seed": outer_seed,
        "construction_audit": audit,
        "pre_gate_byte_equality": equality,
        "forced_arm_pair_equality": forced_equal,
        "replicas": replicas,
        "activity": _sum_activity(
            replicas["EC4G"]["activity"],  # type: ignore[arg-type]
            replicas["DIRECT_TAU"]["activity"],  # type: ignore[arg-type]
        ),
    }


def _mean(values: Iterable[float]) -> float:
    values = tuple(values)
    return sum(values) / len(values)


def aggregate_units(units: Sequence[Mapping[str, object]]) -> dict[str, object]:
    def forced(unit: Mapping[str, object], q: str, arm: str, metric: str) -> float:
        replicas = unit["replicas"]
        assert isinstance(replicas, Mapping)
        row = replicas["EC4G"]
        assert isinstance(row, Mapping)
        panels = row["forced"]
        assert isinstance(panels, Mapping)
        return float(panels[q][arm][metric])  # type: ignore[index]

    contrasts: dict[str, float] = {}
    for q in Q_VALUES:
        for left, right in (("RV", "RS"), ("RV", "RB"), ("PV", "PS"), ("PV", "PB")):
            contrasts[f"{q}_{left}_minus_{right}"] = _mean(
                forced(unit, q, left, "mean_return")
                - forced(unit, q, right, "mean_return")
                for unit in units
            )
    generic_physical = _mean(
        0.5
        * (
            forced(unit, "q1", "RB", "mean_return")
            - forced(unit, "q1", "PB", "mean_return")
            + forced(unit, "q1", "RS", "mean_return")
            - forced(unit, "q1", "PS", "mean_return")
        )
        for unit in units
    )
    q0_gate_units = 0
    q1_divergence_units = 0
    selectivities: list[float] = []
    deltas: list[float] = []
    for unit in units:
        replicas = unit["replicas"]
        assert isinstance(replicas, Mapping)
        ec4g = replicas["EC4G"]
        direct = replicas["DIRECT_TAU"]
        assert isinstance(ec4g, Mapping) and isinstance(direct, Mapping)
        if ec4g["gates"]["q0"] == "P" and direct["gates"]["q0"] == "P":  # type: ignore[index]
            q0_gate_units += 1
        if direct["gates"]["q1"] == "P" and ec4g["gates"]["q1"] == "A":  # type: ignore[index]
            q1_divergence_units += 1
        selectivities.append(float(ec4g["autonomous"]["probe_selectivity"]))  # type: ignore[index]
        deltas.append(
            float(ec4g["autonomous"]["balanced_return"])  # type: ignore[index]
            - float(direct["autonomous"]["balanced_return"])  # type: ignore[index]
        )
    return {
        "forced_content_contrasts": contrasts,
        "generic_physical_effect": generic_physical,
        "q0_both_gates_p_units": q0_gate_units,
        "q1_direct_p_ec4g_a_units": q1_divergence_units,
        "balanced_probe_selectivity_mean": _mean(selectivities),
        "delta_j": _mean(deltas),
        "unit_delta_j": deltas,
    }


def expected_activity() -> dict[str, int]:
    activity = _zero_activity()
    activity.update(
        {
            "episodes": 122_880,
            "training_episodes": 28_672,
            "calibration_episodes": 28_672,
            "forced_evaluation_episodes": 57_344,
            "autonomous_evaluation_episodes": 8_192,
            "held_out_evaluation_episodes": 65_536,
            "environment_transitions": 491_520,
            "batched_policy_calls": 491_520,
            "active_agent_forward_rows": 1_105_920,
            "learner_calls": 2_048,
            "trainer_calls": 2_048,
            "optimizer_updates": 2_048,
            "calibration_table_updates": 28_672,
            "final_checkpoints": 16,
            "registered_paired_fulls": 1,
        }
    )
    return activity


def expected_replica_activity() -> dict[str, int]:
    activity = _zero_activity()
    activity.update(
        {
            "episodes": 7_680,
            "training_episodes": 1_792,
            "calibration_episodes": 1_792,
            "forced_evaluation_episodes": 3_584,
            "autonomous_evaluation_episodes": 512,
            "held_out_evaluation_episodes": 4_096,
            "environment_transitions": 30_720,
            "batched_policy_calls": 30_720,
            "active_agent_forward_rows": 69_120,
            "learner_calls": 128,
            "trainer_calls": 128,
            "optimizer_updates": 128,
            "calibration_table_updates": 1_792,
            "final_checkpoints": 1,
        }
    )
    return activity


def _retained_unit_issues(unit: Mapping[str, object], outer_seed: int) -> list[str]:
    issues: list[str] = []
    if unit.get("outer_seed") != outer_seed:
        issues.append("outer seed mismatch")
    audit = unit.get("construction_audit")
    if not isinstance(audit, Mapping):
        issues.append("missing construction audit")
    else:
        if (
            audit.get("outer_seed") != outer_seed
            or audit.get("matched_body_checks") != 6_144
            or audit.get("matched_body_failures") != 0
            or audit.get("tuple_serializer_has_treatment_field") is not False
            or audit.get("autonomous_exogenous_arm_key") != "AUTONOMOUS_SHARED"
            or audit.get("all_passed") is not True
        ):
            issues.append("construction audit summary mismatch")
        tag_rows = audit.get("tag_domains")
        if not isinstance(tag_rows, Mapping) or set(tag_rows) != set(SPLITS):
            issues.append("construction tag-domain roster mismatch")
        else:
            for split in SPLITS:
                row = tag_rows[split]
                if (
                    not isinstance(row, Mapping)
                    or row.get("count") != SPLIT_EPISODES[split]
                    or row.get("domain") != list(TAG_DOMAINS[split])
                    or row.get("passed") is not True
                    or not isinstance(row.get("permutation_digest"), str)
                    or len(row["permutation_digest"]) != 64
                ):
                    issues.append(f"construction {split} tag certificate mismatch")
        donor_rows = audit.get("donor_tables")
        expected_donors = {
            f"{split}/{q}"
            for split in ("TRAIN", "CALIBRATION", "FORCED_EVAL")
            for q in Q_VALUES
        }
        if not isinstance(donor_rows, Mapping) or set(donor_rows) != expected_donors:
            issues.append("construction donor-table roster mismatch")
        else:
            for key in sorted(expected_donors):
                split = key.split("/", 1)[0]
                row = donor_rows[key]
                if (
                    not isinstance(row, Mapping)
                    or row.get("count") != SPLIT_EPISODES[split]
                    or row.get("offset") != SPLIT_EPISODES[split] // 2
                    or row.get("passed") is not True
                    or not isinstance(row.get("table_digest"), str)
                    or len(row["table_digest"]) != 64
                ):
                    issues.append(f"construction {key} donor certificate mismatch")
    replicas = unit.get("replicas")
    if not isinstance(replicas, Mapping) or set(replicas) != set(REPLICAS):
        return issues + ["replica roster mismatch"]
    for treatment in REPLICAS:
        record = replicas[treatment]
        if not isinstance(record, Mapping):
            issues.append(f"{treatment} replica is not an object")
            continue
        if record.get("activity") != expected_replica_activity():
            issues.append(f"{treatment} replica activity mismatch")
        table = record.get("calibration")
        if not isinstance(table, Mapping) or set(table) != set(Q_VALUES):
            issues.append(f"{treatment} calibration roster mismatch")
            continue
        table_valid = True
        for q in Q_VALUES:
            if not isinstance(table[q], Mapping) or set(table[q]) != set(ARMS):
                table_valid = False
                break
            for arm in ARMS:
                cell = table[q][arm]
                if (
                    not isinstance(cell, Mapping)
                    or cell.get("count") != 128
                    or not isinstance(cell.get("sum"), (int, float))
                    or not math.isfinite(float(cell["sum"]))
                ):
                    table_valid = False
                    break
        if not table_valid:
            issues.append(f"{treatment} calibration cell mismatch")
            continue
        inputs = derived_gate_inputs(table)  # pure retained arithmetic
        if canonical_bytes(record.get("gate_inputs")) != canonical_bytes(inputs):
            issues.append(f"{treatment} derived gate inputs mismatch")
        gates = {q: gate_label(treatment, inputs[q]) for q in Q_VALUES}
        if canonical_bytes(record.get("gates")) != canonical_bytes(gates):
            issues.append(f"{treatment} gate labels mismatch")
        forced = record.get("forced")
        if not isinstance(forced, Mapping) or set(forced) != set(Q_VALUES):
            issues.append(f"{treatment} forced panel roster mismatch")
        else:
            for q in Q_VALUES:
                if not isinstance(forced[q], Mapping) or set(forced[q]) != set(ARMS):
                    issues.append(f"{treatment}/{q} forced arm roster mismatch")
                    continue
                for arm in ARMS:
                    panel = forced[q][arm]
                    if not isinstance(panel, Mapping) or panel.get("episodes") != 256:
                        issues.append(f"{treatment}/{q}/{arm} forced panel incomplete")
                        continue
                    for metric in (
                        "mean_return",
                        "mean_intended_action_accuracy",
                        "mean_executed_team_success",
                    ):
                        value = panel.get(metric)
                        if not isinstance(value, (int, float)) or not math.isfinite(
                            float(value)
                        ):
                            issues.append(f"{treatment}/{q}/{arm} {metric} invalid")
        autonomous = record.get("autonomous")
        if not isinstance(autonomous, Mapping) or autonomous.get("treatment") != treatment:
            issues.append(f"{treatment} autonomous panel identity mismatch")
        else:
            by_q = autonomous.get("by_q")
            if not isinstance(by_q, Mapping) or set(by_q) != set(Q_VALUES):
                issues.append(f"{treatment} autonomous q roster mismatch")
            else:
                retained_returns: list[float] = []
                retained_probes: dict[str, float] = {}
                for q in Q_VALUES:
                    row = by_q[q]
                    if not isinstance(row, Mapping) or row.get("episodes") != 256:
                        issues.append(f"{treatment}/{q} autonomous panel incomplete")
                        continue
                    expected_arm = "RV" if record["gates"][q] == "P" else "R0"  # type: ignore[index]
                    if row.get("gate") != record["gates"][q] or row.get("executed_arm") != expected_arm:  # type: ignore[index]
                        issues.append(f"{treatment}/{q} autonomous gate execution mismatch")
                    mean_return = row.get("mean_return")
                    probe_rate = row.get("probe_rate")
                    if not isinstance(mean_return, (int, float)) or not math.isfinite(float(mean_return)):
                        issues.append(f"{treatment}/{q} autonomous return invalid")
                        continue
                    if probe_rate not in (0.0, 1.0):
                        issues.append(f"{treatment}/{q} autonomous probe rate invalid")
                        continue
                    retained_returns.append(float(mean_return))
                    retained_probes[q] = float(probe_rate)
                if len(retained_returns) == 2:
                    if float(autonomous.get("balanced_return", math.nan)) != 0.5 * sum(retained_returns):
                        issues.append(f"{treatment} balanced return mismatch")
                    if float(autonomous.get("probe_selectivity", math.nan)) != retained_probes["q0"] - retained_probes["q1"]:
                        issues.append(f"{treatment} probe selectivity mismatch")
    if all(isinstance(replicas.get(name), Mapping) for name in REPLICAS):
        ec4g = replicas["EC4G"]
        direct = replicas["DIRECT_TAU"]
        expected_pre_gate = {
            "model": canonical_bytes(ec4g.get("checkpoint_state"))
            == canonical_bytes(direct.get("checkpoint_state")),
            "optimizer": canonical_bytes(ec4g.get("optimizer_final_state"))
            == canonical_bytes(direct.get("optimizer_final_state")),
            "calibration": canonical_bytes(ec4g.get("calibration"))
            == canonical_bytes(direct.get("calibration")),
            "gate_inputs": canonical_bytes(ec4g.get("gate_inputs"))
            == canonical_bytes(direct.get("gate_inputs")),
        }
        if canonical_bytes(unit.get("pre_gate_byte_equality")) != canonical_bytes(
            expected_pre_gate
        ):
            issues.append("pre-gate equality certificate mismatch")
        for treatment, record in (("EC4G", ec4g), ("DIRECT_TAU", direct)):
            if record.get("checkpoint_digest") != digest(record.get("checkpoint_state")):
                issues.append(f"{treatment} checkpoint digest mismatch")
            if record.get("optimizer_digest") != digest(
                record.get("optimizer_final_state")
            ):
                issues.append(f"{treatment} optimizer digest mismatch")
        forced_equal = canonical_bytes(ec4g.get("forced")) == canonical_bytes(
            direct.get("forced")
        )
        if unit.get("forced_arm_pair_equality") is not forced_equal:
            issues.append("forced-arm equality certificate mismatch")
        expected_unit_activity = _sum_activity(
            ec4g.get("activity", {}), direct.get("activity", {})  # type: ignore[arg-type]
        )
        if unit.get("activity") != expected_unit_activity:
            issues.append("unit activity projection mismatch")
    return issues


def _metric_gates(units: Sequence[Mapping[str, object]], aggregates: Mapping[str, object]) -> dict[str, bool]:
    contrasts = aggregates["forced_content_contrasts"]
    assert isinstance(contrasts, Mapping)
    return {
        "tag_donor_match_audit": all(
            bool(unit["construction_audit"]["all_passed"])  # type: ignore[index]
            and all(
                bool(unit["pre_gate_byte_equality"][key])  # type: ignore[index]
                for key in ("model", "optimizer", "calibration", "gate_inputs")
            )
            for unit in units
        ),
        "q1_null_firewall": all(
            abs(float(contrasts[f"q1_{left}_minus_{right}"])) <= 0.03
            for left, right in (("RV", "RS"), ("RV", "RB"), ("PV", "PS"), ("PV", "PB"))
        ),
        "activity_complete": _sum_activity(
            *(unit["activity"] for unit in units)  # type: ignore[arg-type]
        )
        == expected_activity(),
        "forced_pair_invariance": all(bool(unit["forced_arm_pair_equality"]) for unit in units),
        "q0_content": all(
            float(contrasts[f"q0_{left}_minus_{right}"]) >= 0.08
            for left, right in (("RV", "RS"), ("RV", "RB"), ("PV", "PS"), ("PV", "PB"))
        ),
        "generic_physical": float(aggregates["generic_physical_effect"]) >= 0.01,
        "q0_gate_sanity": int(aggregates["q0_both_gates_p_units"]) >= 6,
        "q1_gate_divergence": int(aggregates["q1_direct_p_ec4g_a_units"]) >= 6,
        "probe_selectivity": float(aggregates["balanced_probe_selectivity_mean"]) >= 0.375,
    }


def classify_result(
    *, preflight_valid: bool, gates: Mapping[str, bool], delta_j: float
) -> str:
    if not preflight_valid:
        return BRANCH_PRECEDENCE[0]
    if not gates.get("tag_donor_match_audit", False) or not gates.get(
        "q1_null_firewall", False
    ):
        return BRANCH_PRECEDENCE[1]
    if not gates.get("activity_complete", False):
        return BRANCH_PRECEDENCE[2]
    if not gates.get("forced_pair_invariance", False):
        return BRANCH_PRECEDENCE[3]
    if not all(
        gates.get(key, False)
        for key in ("q0_content", "generic_physical", "q0_gate_sanity")
    ):
        return BRANCH_PRECEDENCE[4]
    if not gates.get("q1_gate_divergence", False) or not gates.get(
        "probe_selectivity", False
    ):
        return BRANCH_PRECEDENCE[5]
    if delta_j <= -0.01:
        return BRANCH_PRECEDENCE[6]
    if delta_j < 0.02:
        return BRANCH_PRECEDENCE[7]
    return BRANCH_PRECEDENCE[8]


def analytic_counterexample() -> dict[str, object]:
    q0 = dict(zip(ARMS, (0.570, 0.774, 0.598, 0.598, 0.730, 0.570, 0.570)))
    q1 = dict(zip(ARMS, (0.570, 0.598, 0.598, 0.598, 0.570, 0.570, 0.570)))
    witness = {"R0": 73, "RV": 79, "RB": 79, "RS": 79, "count": 128}
    inputs = {
        "T": (witness["RV"] - witness["R0"]) / 128.0 - 0.02,
        "C": 0.0,
        "V": 0.0,
    }
    # Probe costs are already present in calibrated returns: (79-73)/128-.02.
    return {
        "q0": q0,
        "q1": q1,
        "q0_content_contrasts": [0.176, 0.176, 0.160, 0.160],
        "q1_content_contrasts": [0.0, 0.0, 0.0, 0.0],
        "q1_generic_physical_effect": 0.028,
        "q1_finite_witness": witness,
        "q1_finite_witness_inputs": inputs,
        "q1_finite_witness_gates": {
            "DIRECT_TAU": gate_label("DIRECT_TAU", inputs),
            "EC4G": gate_label("EC4G", inputs),
        },
        "branch_9_interpretation": "finite-panel anomaly, never EC4G value evidence",
    }


OBSERVATION_LAYOUT = {
    "phase_one_hot": [0, 1, 2, 3],
    "q_present": 4,
    "q_bit": 5,
    "x_present": 6,
    "x_bit": 7,
    "current_tag_present": 8,
    "current_tag_bits": list(range(9, 25)),
    "receipt_present": 25,
    "receipt_tag_bits": list(range(26, 42)),
    "receipt_payload": 42,
}


def constructive_parameter_coordinates() -> dict[str, float]:
    """Sparse coordinates for an executable four-step raw-tag GRU circuit."""

    coordinates: dict[str, float] = {}
    write, retain, scale = -40.0, 40.0, 2.0
    candidate = 2 * HIDDEN_SIZE

    def phase_update(hidden: int, write_phase: int) -> None:
        update_row = HIDDEN_SIZE + hidden
        for phase in range(4):
            coordinates[f"gru.weight_ih[{update_row},{phase}]"] = (
                write if phase == write_phase else retain
            )

    # h0..15 retain all sixteen raw current-tag bits as +/-tanh(2).
    for hidden, column in enumerate(OBSERVATION_LAYOUT["current_tag_bits"]):
        phase_update(hidden, 0)
        coordinates[f"gru.weight_ih[{candidate + hidden},8]"] = -scale
        coordinates[f"gru.weight_ih[{candidate + hidden},{column}]"] = 2.0 * scale
    # h16=x sign and h17=q0 sign survive leave and receipt.
    for hidden in (16, 17):
        phase_update(hidden, 0)
    coordinates[f"gru.weight_ih[{candidate + 16},6]"] = -scale
    coordinates[f"gru.weight_ih[{candidate + 16},7]"] = 2.0 * scale
    coordinates[f"gru.weight_ih[{candidate + 17},4]"] = scale
    coordinates[f"gru.weight_ih[{candidate + 17},5]"] = -2.0 * scale

    # At t2, reset gates 18/19 compare the retained raw bits with receipt bits
    # in both signed directions. Candidate rows turn those gates into explicit
    # mismatch features. h20/h21 retain present and y/payload signs.
    threshold = 1.0 / 65_535.0
    comparison_gain = 400_000.0
    memory_amplitude = math.tanh(scale)
    for hidden, direction in ((18, 1.0), (19, -1.0)):
        phase_update(hidden, 2)
        for bit in range(16):
            weight = (1 << bit) / 65_535.0
            coordinates[f"gru.weight_hh[{hidden},{bit}]"] = (
                direction * comparison_gain * weight / memory_amplitude
            )
            receipt_column = OBSERVATION_LAYOUT["receipt_tag_bits"][bit]
            coordinates[f"gru.weight_ih[{hidden},{receipt_column}]"] = (
                -direction * comparison_gain * 2.0 * weight
            )
        coordinates[f"gru.weight_ih[{hidden},2]"] = comparison_gain * (
            direction - threshold
        )
        coordinates[f"gru.bias_hh[{candidate + hidden}]"] = scale
    for hidden in (20, 21):
        phase_update(hidden, 2)
    coordinates[f"gru.weight_ih[{candidate + 20},2]"] = -scale
    coordinates[f"gru.weight_ih[{candidate + 20},25]"] = 2.0 * scale
    coordinates[f"gru.weight_ih[{candidate + 21},2]"] = -scale
    coordinates[f"gru.weight_ih[{candidate + 21},42]"] = 2.0 * scale

    # At t3, reset gates 24..28 are five DNF clauses for action one:
    # matching-q0-y1; x1&q1; x1&absent; x1&positive mismatch; x1&negative
    # mismatch. Their candidate rows are the actor-read hidden coordinates.
    clause_gain = 8.0
    clause_specs = {
        24: ({17: 1.0, 20: 1.0, 21: 1.0, 18: -2.0, 19: -2.0}, -2.0),
        25: ({16: 1.0, 17: -1.0}, -1.0),
        26: ({16: 1.0, 20: -1.0}, -1.0),
        27: ({16: 1.0, 18: 2.0}, -2.0),
        28: ({16: 1.0, 19: 2.0}, -2.0),
    }
    for hidden, (terms, bias) in clause_specs.items():
        phase_update(hidden, 3)
        for source, coefficient in terms.items():
            coordinates[f"gru.weight_hh[{hidden},{source}]"] = (
                clause_gain * coefficient / memory_amplitude
            )
        coordinates[f"gru.bias_ih[{hidden}]"] = clause_gain * bias
        coordinates[f"gru.bias_hh[{candidate + hidden}]"] = scale
        coordinates[f"actor.weight[0,{hidden}]"] = -1.0
        coordinates[f"actor.weight[1,{hidden}]"] = 1.0
    coordinates["actor.bias[0]"] = 0.5 * memory_amplitude
    coordinates["actor.bias[1]"] = -0.5 * memory_amplitude
    return coordinates


def _constructive_decision(
    *, x: int, q: str, current_tag: int, receipt_tag: int, payload: int, present: int
) -> int:
    return int(payload) if present and q == "q0" and receipt_tag == current_tag else int(x)


def _apply_sparse_witness(
    model: SharedGRUA2C, coordinates: Mapping[str, float]
) -> None:
    named = dict(model.named_parameters())
    with torch.no_grad():
        for parameter in named.values():
            parameter.zero_()
        for address, value in coordinates.items():
            name, raw_index = address.split("[", 1)
            indices = tuple(int(part) for part in raw_index[:-1].split(","))
            if name not in named or len(indices) not in (1, 2):
                raise ValueError(f"invalid constructive parameter address: {address}")
            named[name][indices] = float(value)


def _constructive_logits(
    model: SharedGRUA2C,
    *,
    x: int,
    q: str,
    current_tag: int,
    receipt_tag: int,
    payload: int,
    present: int,
) -> Tensor:
    hidden = torch.zeros((1, HIDDEN_SIZE), dtype=torch.float64)
    receipt = {"present": present, "tag": receipt_tag, "payload": payload}
    observations = (
        observation_vector(0, q=q, x=x, current_tag=current_tag),
        observation_vector(1),
        observation_vector(2, receipt=receipt),
        observation_vector(3),
    )
    with torch.no_grad():
        for observation in observations:
            hidden = model.advance(observation.unsqueeze(0), hidden)
        return model.logits(hidden)[0]


def constructive_representability_certificate(
    parameters: Mapping[str, float] | None = None,
    *,
    recurrent_transition_override: str | None = None,
) -> dict[str, object]:
    expected = constructive_parameter_coordinates()
    supplied = dict(expected if parameters is None else parameters)
    parameter_match = canonical_bytes(supplied) == canonical_bytes(expected)
    model = SharedGRUA2C(device="cpu")
    _apply_sparse_witness(model, supplied)
    if recurrent_transition_override == "zero_recurrent":
        with torch.no_grad():
            model.gru.weight_hh.zero_()
    elif recurrent_transition_override is not None:
        raise ValueError("unknown constructive recurrent transition override")
    tags = (
        0x0000,
        0x0001,
        0x007E,
        0x007F,
        0x0100,
        0x0101,
        0x017E,
        0x017F,
        0x0200,
        0x0201,
        0x02FE,
        0x02FF,
        0x0300,
        0x0301,
        0x03FE,
        0x03FF,
    )
    probe_count = 0
    probe_failures = 0
    path_margins: dict[str, list[float]] = {
        "raw_tag_match": [],
        "raw_tag_nonmatch": [],
        "q0_payload_path": [],
        "fallback_x_path": [],
    }
    for tag in tags:
        receipt_cases = [(tag, 1, "match")]
        if tag < 0xFFFF:
            receipt_cases.append((tag + 1, 1, "nonmatch"))
        if tag > 0:
            receipt_cases.append((tag - 1, 1, "nonmatch"))
        if tag != BLIND_TAG:
            receipt_cases.append((BLIND_TAG, 1, "nonmatch"))
        receipt_cases.append((0, 0, "absent"))
        for x in (0, 1):
            for q in Q_VALUES:
                for payload in (0, 1):
                    for receipt_tag, present, path in receipt_cases:
                        effective_payload = payload if present else 0
                        expected_decision = _constructive_decision(
                            x=x,
                            q=q,
                            current_tag=tag,
                            receipt_tag=receipt_tag,
                            payload=effective_payload,
                            present=present,
                        )
                        logits = _constructive_logits(
                            model,
                            x=x,
                            q=q,
                            current_tag=tag,
                            receipt_tag=receipt_tag,
                            payload=effective_payload,
                            present=present,
                        )
                        margin = float(
                            logits[expected_decision] - logits[1 - expected_decision]
                        )
                        probe_count += 1
                        probe_failures += int(margin <= 0.0)
                        path_margins[
                            "raw_tag_match" if path == "match" else "raw_tag_nonmatch"
                        ].append(margin)
                        path_margins[
                            "q0_payload_path"
                            if path == "match" and q == "q0"
                            else "fallback_x_path"
                        ].append(margin)
    margins = {name: min(values) for name, values in path_margins.items()}
    exact_layout = (
        OBSERVATION_SIZE == 43
        and HIDDEN_SIZE == 32
        and OBSERVATION_LAYOUT["current_tag_bits"] == list(range(9, 25))
        and OBSERVATION_LAYOUT["receipt_tag_bits"] == list(range(26, 42))
        and set(PARAMETER_SHAPES)
        == {
            "actor.bias",
            "actor.weight",
            "gru.bias_hh",
            "gru.bias_ih",
            "gru.weight_hh",
            "gru.weight_ih",
            "value.bias",
            "value.weight",
        }
    )
    issues: list[str] = []
    if not parameter_match:
        issues.append("constructive recurrent parameter coordinates mismatch")
    if not exact_layout:
        issues.append("SharedGRUA2C or observation layout mismatch")
    if recurrent_transition_override is not None:
        issues.append("constructive recurrent transition override active")
    if not all(value > 0.0 for value in margins.values()):
        issues.append("actual actor-logit margin is nonpositive")
    if probe_failures:
        issues.append("finite raw-tag decision probes failed")
    return {
        "model_class": "SharedGRUA2C: GRUCell(43,32)+two-action actor+central value",
        "observation_layout": deepcopy(OBSERVATION_LAYOUT),
        "parameter_coordinates": supplied,
        "parameter_coordinate_digest": digest(supplied),
        "parameter_coordinate_count": len(supplied),
        "checked_margins": margins,
        "recurrence": "four actual SharedGRUA2C.advance calls then actual actor logits",
        "recurrent_transition_override": recurrent_transition_override,
        "finite_tag_probe_count": probe_count,
        "finite_tag_probe_failures": probe_failures,
        "retains": ["x", "q", "sixteen raw current-tag bits"],
        "comparison": "raw receipt tag equals retained raw current tag",
        "decision": "matching q0 payload, otherwise retained x",
        "exact_class_and_layout": exact_layout,
        "parameter_match": parameter_match,
        "passed": not issues,
        "issues": issues,
        "representability_only": True,
        "learned_result": False,
    }


def representability_report() -> dict[str, object]:
    return constructive_representability_certificate()


def build_manifest(
    *, source_revision: str, run_id: str, technical_only: bool
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "ec4g_b1_frozen_manifest",
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "resource_class": RESOURCE_CLASS,
        "pool_units": POOL_UNITS,
        "source_revision": source_revision,
        "run_id": run_id,
        "technical_only": bool(technical_only),
        "accepted_a5_anchors": {
            "source": ACCEPTED_A5_SOURCE,
            "publication": ACCEPTED_A5_PUBLICATION,
            "inherited_structural_witness_only": {
                "join_equal": True,
                "leave_unequal": True,
                "rejoin_equal": True,
                "D_RER3": "1/4",
            },
        },
        "outer_seeds": list(OUTER_SEEDS),
        "replicas": list(REPLICAS),
        "q_values": list(Q_VALUES),
        "arms": list(ARMS),
        "splits": list(SPLITS),
        "lanes": list(LANES),
        "tag_domains": {key: list(value) for key, value in TAG_DOMAINS.items()},
        "blind_tag": BLIND_TAG,
        "split_episodes": dict(SPLIT_EPISODES),
        "host": {
            "steps": 4,
            "timeline": [
                "t0: a0,a1,a2; q,x,current raw tag",
                "t1: a2 leaves; one gate-controlled probe opportunity",
                "t2: fixed receipt envelope",
                "t3: intended bits, actuation, terminal reward",
            ],
            "q0_sensor_flip_probability": 0.10,
            "q1_sensor": "independent Bernoulli(.5)",
            "public_cue_flip_probability": 0.30,
            "physical_probe_target": "a1",
            "a0_terminal_flip_probability": 0.10,
            "a1_terminal_flip_without_probe": 0.10,
            "a1_terminal_flip_with_probe": 0.02,
            "reward": "1[all executed bits equal z]-.02*1[physical probe]",
            "intermediate_rewards": 0,
        },
        "receipt": {
            "layout": ["present", "sixteen raw tag bits", "payload"],
            "r0": "present=0 and canonical all-zero body",
            "physical_arms": sorted(PHYSICAL_ARMS),
            "matched_bodies": [["RV", "PV"], ["RB", "PB"], ["RS", "PS"]],
            "donor_index": "(episode+N/2) mod N",
            "train_calibration_n": 128,
            "forced_evaluation_n": 256,
            "autonomous_donor_use": 0,
            "arm_or_physical_identity_observed": False,
        },
        "rng": {
            "prefix": SEED_PREFIX,
            "ascii_fields": [
                "outer_seed",
                "split",
                "phase",
                "q",
                "arm",
                "episode",
                "lane",
                "draw_index",
            ],
            "derivation": "uint64_le(first8(SHA256(ASCII(pipe-joined fields))))",
            "uniform_draw": "(counter_seed+0.5)/2^64",
            "treatment_field_present": False,
            "common_within_pair": True,
            "independent_across_outer_seeds_and_splits": True,
        },
        "model": {
            "shared_per_agent_gru_hidden": HIDDEN_SIZE,
            "observation_size": OBSERVATION_SIZE,
            "terminal_actions": 2,
            "centralized_value_head": True,
            "survivor_state_retained": True,
        },
        "learning": {
            "algorithm": "A2C",
            "gamma": GAMMA,
            "optimizer": "Adam",
            "learning_rate": LEARNING_RATE,
            "entropy_coefficient": ENTROPY_COEFFICIENT,
            "value_coefficient": VALUE_COEFFICIENT,
            "global_gradient_cap": GRADIENT_CAP,
            "blocks": 128,
            "episodes_per_block": 14,
            "updates_per_replica": 128,
            "checkpoint_rule": "sole final checkpoint after update 128",
        },
        "gates": {
            "tau": TAU,
            "direct": "P iff T>.02; N iff T<-.02; else A",
            "ec4g": "P iff T>.02 and C>.02 and V>.02; N iff T<-.02; else A",
            "execution": "P->RV; N/A->identical R0",
        },
        "thresholds": {
            "q1_firewall_abs_max": 0.03,
            "q0_content_min": 0.08,
            "generic_physical_min": 0.01,
            "q0_gate_units_min": 6,
            "q1_divergence_units_min": 6,
            "probe_selectivity_min": 0.375,
            "delta_direct_signal_max": -0.01,
            "delta_positive_anomaly_min": 0.02,
        },
        "panels": {
            "training_episodes_per_replica": 1_792,
            "calibration_episodes_per_replica": 1_792,
            "forced_evaluation_episodes_per_replica": 3_584,
            "autonomous_evaluation_episodes_per_replica": 512,
            "held_out_evaluation_episodes_per_replica": 4_096,
            "replicas": 16,
            "independent_units": 8,
        },
        "branch_precedence": list(BRANCH_PRECEDENCE),
        "caps": dict(CAPS),
        "claim_paths": list(CLAIM_PATHS),
        "registered_fulls": 0 if technical_only else 1,
        "retry_rescue_sweep": 0,
    }


def manifest_identity(manifest: Mapping[str, object]) -> str:
    return digest(manifest)


def validate_manifest(manifest: Mapping[str, object]) -> tuple[str, ...]:
    source = manifest.get("source_revision")
    run_id = manifest.get("run_id")
    technical = manifest.get("technical_only")
    if not isinstance(source, str) or not source:
        return ("source_revision must be a nonempty string",)
    if not isinstance(run_id, str) or not run_id:
        return ("run_id must be a nonempty string",)
    if not isinstance(technical, bool):
        return ("technical_only must be boolean",)
    expected = build_manifest(
        source_revision=source, run_id=run_id, technical_only=technical
    )
    return () if canonical_bytes(manifest) == canonical_bytes(expected) else (
        "manifest differs from the frozen EC4G-B1 literals",
    )


def preflight_report(manifest: Mapping[str, object]) -> dict[str, object]:
    manifest_issues = validate_manifest(manifest)
    tags_ok = all(
        len(split_tags(OUTER_SEEDS[0], split)) == SPLIT_EPISODES[split]
        and len(set(split_tags(OUTER_SEEDS[0], split))) == SPLIT_EPISODES[split]
        for split in SPLITS
    )
    donor_ok = True
    for split in ("TRAIN", "CALIBRATION", "FORCED_EVAL"):
        n = SPLIT_EPISODES[split]
        tags = split_tags(OUTER_SEEDS[0], split)
        for q in Q_VALUES:
            records = donor_records(OUTER_SEEDS[0], split, q)
            donor_ok &= len(records) == n
            donor_ok &= all(
                (index + n // 2) % n != index
                and records[(index + n // 2) % n].tag != tags[index]
                for index in range(n)
            )
    own_y = 1
    body_ok = all(
        receipt_body(
            outer_seed=OUTER_SEEDS[0],
            split="FORCED_EVAL",
            q="q0",
            arm=left,
            episode=0,
            own_y=own_y,
        )
        == receipt_body(
            outer_seed=OUTER_SEEDS[0],
            split="FORCED_EVAL",
            q="q0",
            arm=right,
            episode=0,
            own_y=own_y,
        )
        for left, right in (("RV", "PV"), ("RB", "PB"), ("RS", "PS"))
    )
    representation = representability_report()
    analytic = analytic_counterexample()
    expected = expected_activity()
    gates = {
        "P0_FROZEN_LITERAL_BINDING": {
            "passed": not manifest_issues,
            "issues": list(manifest_issues),
        },
        "P1_RANDOM_ACCESS_TAG_DONOR": {
            "passed": tags_ok and donor_ok,
            "issues": [] if tags_ok and donor_ok else ["tag or donor construction mismatch"],
        },
        "P2_RECEIPT_REWARD_INPUT_FIREWALL": {
            "passed": body_ok,
            "issues": [] if body_ok else ["matched receipt bodies differ"],
        },
        "P3_EXACT_32_UNIT_CLASS_REPRESENTABILITY": {
            "passed": bool(representation["passed"]),
            "issues": list(representation["issues"]),
        },
        "P4_MODEL_AND_A2C_CONTRACT": {
            "passed": HIDDEN_SIZE == 32
            and GAMMA == 1.0
            and LEARNING_RATE == 0.003
            and GRADIENT_CAP == 1.0,
            "issues": [],
        },
        "P5_ANALYTIC_GATE_WITNESS": {
            "passed": analytic["q1_finite_witness_gates"]
            == {"DIRECT_TAU": "P", "EC4G": "A"},
            "issues": [],
        },
        "P6_EXACT_COUNTS_AND_CAPS": {
            "passed": all(expected[key] == CAPS[key] for key in CAPS if key in expected),
            "issues": [],
        },
        "P7_TOTAL_BRANCH_MAP": {
            "passed": len(BRANCH_PRECEDENCE) == 9
            and len(set(BRANCH_PRECEDENCE)) == 9,
            "issues": [],
        },
    }
    return {
        "artifact_kind": "ec4g_b1_static_preflight",
        "assignment_id": ASSIGNMENT_ID,
        "manifest_identity": manifest_identity(manifest),
        "gates": gates,
        "all_passed": all(bool(gate["passed"]) for gate in gates.values()),
        "representability": representation,
        "analytic_counterexample": analytic,
        "activity": _zero_activity(),
    }


def validate_preflight(
    manifest: Mapping[str, object], report: Mapping[str, object]
) -> tuple[str, ...]:
    expected = preflight_report(manifest)
    return () if canonical_bytes(report) == canonical_bytes(expected) else (
        "preflight differs from deterministic frozen construction proof",
    )


def validate_retained_preflight(
    manifest: Mapping[str, object], report: Mapping[str, object]
) -> tuple[str, ...]:
    """Validate only retained certificates and bindings; never rerun preflight."""

    issues: list[str] = []
    if report.get("artifact_kind") != "ec4g_b1_static_preflight":
        issues.append("retained preflight artifact kind mismatch")
    if report.get("assignment_id") != ASSIGNMENT_ID:
        issues.append("retained preflight assignment mismatch")
    if report.get("manifest_identity") != manifest_identity(manifest):
        issues.append("retained preflight manifest binding mismatch")
    gate_names = (
        "P0_FROZEN_LITERAL_BINDING",
        "P1_RANDOM_ACCESS_TAG_DONOR",
        "P2_RECEIPT_REWARD_INPUT_FIREWALL",
        "P3_EXACT_32_UNIT_CLASS_REPRESENTABILITY",
        "P4_MODEL_AND_A2C_CONTRACT",
        "P5_ANALYTIC_GATE_WITNESS",
        "P6_EXACT_COUNTS_AND_CAPS",
        "P7_TOTAL_BRANCH_MAP",
    )
    gates = report.get("gates")
    if not isinstance(gates, Mapping) or tuple(gates) != gate_names:
        issues.append("retained preflight gate roster/order mismatch")
        gate_passes: list[bool] = []
    else:
        gate_passes = []
        for name in gate_names:
            gate = gates[name]
            if (
                not isinstance(gate, Mapping)
                or not isinstance(gate.get("passed"), bool)
                or not isinstance(gate.get("issues"), list)
                or any(not isinstance(item, str) for item in gate.get("issues", []))
            ):
                issues.append(f"retained preflight {name} certificate malformed")
                continue
            gate_passes.append(bool(gate["passed"]))
            if bool(gate["passed"]) == bool(gate["issues"]):
                issues.append(f"retained preflight {name} pass/issues inconsistency")
        if isinstance(gates["P0_FROZEN_LITERAL_BINDING"], Mapping) and bool(
            gates["P0_FROZEN_LITERAL_BINDING"].get("passed")
        ) is bool(not validate_manifest(manifest)):
            pass
        else:
            issues.append("P0 gate/manifest literal binding mismatch")
    if report.get("all_passed") is not (len(gate_passes) == 8 and all(gate_passes)):
        issues.append("retained preflight all_passed projection mismatch")
    if report.get("activity") != _zero_activity():
        issues.append("retained preflight activity is not exact zero")
    representation = report.get("representability")
    if not isinstance(representation, Mapping):
        issues.append("missing retained representability certificate")
    else:
        coordinates = representation.get("parameter_coordinates")
        margins = representation.get("checked_margins")
        coordinate_binding_valid = True
        if (
            not isinstance(coordinates, Mapping)
            or representation.get("parameter_coordinate_count") != len(coordinates)
            or representation.get("parameter_coordinate_digest") != digest(coordinates)
        ):
            issues.append("retained constructive parameter binding mismatch")
            coordinate_binding_valid = False
        margins_valid = True
        if (
            not isinstance(margins, Mapping)
            or set(margins)
            != {
                "raw_tag_match",
                "raw_tag_nonmatch",
                "q0_payload_path",
                "fallback_x_path",
            }
            or any(
                not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or float(value) <= 0.0
                for value in margins.values()
            )
        ):
            issues.append("retained checked-margin certificate mismatch")
            margins_valid = False
        failures = representation.get("finite_tag_probe_failures")
        expected_pass = (
            coordinate_binding_valid
            and margins_valid
            and representation.get("exact_class_and_layout") is True
            and representation.get("parameter_match") is True
            and failures == 0
        )
        if (
            representation.get("model_class")
            != "SharedGRUA2C: GRUCell(43,32)+two-action actor+central value"
            or representation.get("observation_layout") != OBSERVATION_LAYOUT
            or representation.get("finite_tag_probe_count") != 632
            or not isinstance(failures, int)
            or failures < 0
            or representation.get("recurrence")
            != "four actual SharedGRUA2C.advance calls then actual actor logits"
            or representation.get("recurrent_transition_override") is not None
            or representation.get("passed") is not expected_pass
            or not isinstance(representation.get("issues"), list)
            or bool(representation.get("issues")) is expected_pass
            or representation.get("representability_only") is not True
            or representation.get("learned_result") is not False
        ):
            issues.append("retained representability result fields mismatch")
        if isinstance(gates, Mapping) and isinstance(
            gates.get("P3_EXACT_32_UNIT_CLASS_REPRESENTABILITY"), Mapping
        ):
            if gates["P3_EXACT_32_UNIT_CLASS_REPRESENTABILITY"].get(  # type: ignore[union-attr]
                "passed"
            ) is not representation.get("passed"):
                issues.append("P3 gate/certificate mismatch")
    analytic = report.get("analytic_counterexample")
    if not isinstance(analytic, Mapping):
        issues.append("missing retained analytic counterexample")
    elif (
        analytic.get("q1_finite_witness_gates")
        != {"DIRECT_TAU": "P", "EC4G": "A"}
        or analytic.get("q1_finite_witness_inputs")
        != {"T": 0.026875, "C": 0.0, "V": 0.0}
        or analytic.get("branch_9_interpretation")
        != "finite-panel anomaly, never EC4G value evidence"
    ):
        issues.append("retained analytic gate certificate mismatch")
    return tuple(issues)


def run_treatment(manifest: Mapping[str, object]) -> dict[str, object]:
    preflight = preflight_report(manifest)
    if not preflight["all_passed"]:
        return {
            "artifact_kind": "ec4g_b1_result",
            "assignment_id": ASSIGNMENT_ID,
            "candidate": CANDIDATE,
            "manifest": deepcopy(manifest),
            "manifest_identity": manifest_identity(manifest),
            "preflight": preflight,
            "branch": BRANCH_PRECEDENCE[0],
            "activity": _zero_activity(),
            "units": [],
            "aggregates": None,
            "metric_gates": None,
        }
    units = [run_unit(seed) for seed in OUTER_SEEDS]
    aggregates = aggregate_units(units)
    activity = _sum_activity(*(unit["activity"] for unit in units))  # type: ignore[arg-type]
    activity["registered_paired_fulls"] = 1
    gates = _metric_gates(units, aggregates)
    branch = classify_result(
        preflight_valid=True, gates=gates, delta_j=float(aggregates["delta_j"])
    )
    return {
        "artifact_kind": "ec4g_b1_result",
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "manifest": deepcopy(manifest),
        "manifest_identity": manifest_identity(manifest),
        "preflight": preflight,
        "branch": branch,
        "activity": activity,
        "units": units,
        "aggregates": aggregates,
        "metric_gates": gates,
        "limitations": {
            "branch_9_is_anomaly_not_value": True,
            "natural_value_claim": False,
            "successor_authorized": False,
        },
    }


def _retained_aggregate(units: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Pure arithmetic from retained panels; no host/model/learner construction."""

    return aggregate_units(units)


def validate_result(
    manifest: Mapping[str, object], result: Mapping[str, object]
) -> tuple[str, ...]:
    issues: list[str] = []
    issues.extend(validate_manifest(manifest))
    if result.get("artifact_kind") != "ec4g_b1_result":
        issues.append("artifact kind mismatch")
    if result.get("assignment_id") != ASSIGNMENT_ID or result.get("candidate") != CANDIDATE:
        issues.append("result identity mismatch")
    if result.get("manifest_identity") != manifest_identity(manifest):
        issues.append("manifest identity mismatch")
    if canonical_bytes(result.get("manifest")) != canonical_bytes(manifest):
        issues.append("embedded manifest mismatch")
    preflight = result.get("preflight")
    if not isinstance(preflight, Mapping):
        issues.append("missing preflight")
        return tuple(issues)
    issues.extend(validate_retained_preflight(manifest, preflight))
    branch = result.get("branch")
    if branch not in BRANCH_PRECEDENCE:
        issues.append("unknown result branch")
        return tuple(issues)
    if branch == BRANCH_PRECEDENCE[0]:
        if preflight.get("all_passed") is not False:
            issues.append("static-preflight branch requires a failed retained preflight")
        if result.get("activity") != _zero_activity() or result.get("units") != []:
            issues.append("static-preflight branch must have exact zero activity")
        return tuple(issues)
    if manifest.get("technical_only") is not False:
        issues.append("post-preflight result requires technical_only=false")
    units = result.get("units")
    if not isinstance(units, list) or len(units) != 8:
        issues.append("completed full requires exactly eight unit records")
        return tuple(issues)
    if [unit.get("outer_seed") for unit in units] != list(OUTER_SEEDS):
        issues.append("outer seed roster/order mismatch")
    for expected_seed, unit in zip(OUTER_SEEDS, units, strict=True):
        if isinstance(unit, Mapping):
            issues.extend(
                f"unit {expected_seed}: {issue}"
                for issue in _retained_unit_issues(unit, expected_seed)
            )
        else:
            issues.append(f"unit {expected_seed}: unit record is not an object")
    if result.get("activity") != expected_activity():
        issues.append("exact activity ledger mismatch")
    try:
        aggregates = _retained_aggregate(units)
        if canonical_bytes(result.get("aggregates")) != canonical_bytes(aggregates):
            issues.append("retained aggregate mismatch")
        gates = _metric_gates(units, aggregates)
        if canonical_bytes(result.get("metric_gates")) != canonical_bytes(gates):
            issues.append("metric gate mismatch")
        expected_branch = classify_result(
            preflight_valid=bool(preflight.get("all_passed")),
            gates=gates,
            delta_j=float(aggregates["delta_j"]),
        )
        if branch != expected_branch:
            issues.append("branch precedence mismatch")
    except (AssertionError, KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        issues.append(f"malformed retained unit panels: {exc}")
    return tuple(issues)


def bounded_technical_fixture() -> dict[str, object]:
    """Two real host episodes, no update, checkpoint, or registered full."""

    model = _new_model(OUTER_SEEDS[0])
    rows = []
    with torch.no_grad():
        for arm in ("RV", "PV"):
            row = run_episode(
                model,
                outer_seed=OUTER_SEEDS[0],
                split="FORCED_EVAL",
                q="q0",
                arm=arm,
                episode=0,
                stochastic=False,
            )
            rows.append(
                {
                    key: json_ready(row[key])
                    for key in (
                        "reward",
                        "z",
                        "actions",
                        "executed",
                        "physical_probe",
                        "receipt",
                        "current_tag",
                        "environment_transitions",
                        "batched_policy_calls",
                        "active_agent_forward_rows",
                    )
                }
            )
    return {
        "artifact_kind": "ec4g_b1_bounded_technical_fixture",
        "registered_paired_fulls": 0,
        "result_bearing_runs": 0,
        "episodes": 2,
        "optimizer_updates": 0,
        "rows": rows,
        "matched_body_equal": rows[0]["receipt"] == rows[1]["receipt"],
    }


def bounded_training_fixture() -> dict[str, object]:
    """One exact 14-episode block and one A2C/Adam update, never a full."""

    outer_seed = OUTER_SEEDS[0]
    model = _new_model(outer_seed)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    before_model = digest(model_payload(model))
    before_optimizer = digest(optimizer_payload(optimizer))
    losses: list[Tensor] = []
    episode_receipts: list[str] = []
    activity = _zero_activity()
    for q, arm in training_order(outer_seed, 0):
        row = run_episode(
            model,
            outer_seed=outer_seed,
            split="TRAIN",
            q=q,
            arm=arm,
            episode=0,
            stochastic=True,
        )
        losses.append(_episode_loss(row))
        episode_receipts.append(digest(row["receipt"]))
        _add_episode_activity(activity, row, "TRAIN")
    activity["learner_calls"] = 1
    loss = torch.stack(losses).mean()
    activity["trainer_calls"] = 1
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    gradient_before_clip = float(
        torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CAP)
    )
    optimizer.step()
    activity["optimizer_updates"] = 1
    return {
        "artifact_kind": "ec4g_b1_bounded_training_fixture",
        "registered_paired_fulls": 0,
        "result_bearing_runs": 0,
        "outer_seed": outer_seed,
        "block": 0,
        "order": [list(item) for item in training_order(outer_seed, 0)],
        "receipt_digests": episode_receipts,
        "loss": float(loss.detach()),
        "gradient_norm_before_clip": gradient_before_clip,
        "model_before": before_model,
        "model_after": digest(model_payload(model)),
        "optimizer_before": before_optimizer,
        "optimizer_after": digest(optimizer_payload(optimizer)),
        "activity": activity,
    }


def validate_bounded_technical_fixture(fixture: Mapping[str, object]) -> tuple[str, ...]:
    expected = bounded_technical_fixture()
    return () if canonical_bytes(fixture) == canonical_bytes(expected) else (
        "bounded fixture differs from deterministic host replay",
    )


def validate_bounded_training_fixture(fixture: Mapping[str, object]) -> tuple[str, ...]:
    expected = bounded_training_fixture()
    return () if canonical_bytes(fixture) == canonical_bytes(expected) else (
        "bounded training fixture differs from deterministic A2C/Adam replay",
    )

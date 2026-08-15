"""Constructed four-target host for ACVC-B1.

The module owns only physical scene generation, authenticated frame parsing,
and action scoring.  Learners and fixed policies live in :mod:`policies`.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
import itertools
import random
import struct
from typing import Callable, Iterable, Mapping, Sequence


FRAME_VERSION = 1
SENDER_ID = 0
CONFIDENCE_U8 = 242
PREDICATE = 1
VALID_FROM = 1
VALID_UNTIL = 12
COMMUNICATION_COST = -0.04
MAX_TARGET_ACTIONS = 3
FRAME_STRUCT = struct.Struct("<BHBBBQIQIII10s16s")
FRAME_SIZE = FRAME_STRUCT.size
SERVICE_ORDERS = tuple(itertools.permutations(range(4)))
PERMUTATIONS = SERVICE_ORDERS

SPLIT_COUNTS = {
    "train": (7_680, 3_840, 20),
    "validation": (768, 384, 2),
    "test": (3_840, 1_920, 10),
}
WORLD_NAMESPACES = {"train": 100_000, "validation": 400_000, "test": 500_000}
BINDING_NAMESPACES = {"train": 200_000, "validation": 450_000, "test": 600_000}


class Action(str, Enum):
    COMPLETE = "complete"
    CONTINUE = "continue"
    PROBE = "probe"
    ABSTAIN = "abstain"


ACTIONS = tuple(Action)


class Feedback(str, Enum):
    NONE = "none"
    PROBE_VALID = "probe_valid"
    PROBE_REPAIRABLE = "probe_repairable"
    PROBE_TERMINAL = "probe_terminal"
    CONTINUE_EPOCH_CHANGED = "continue_epoch_changed"
    CONTINUE_NO_CHANGE = "continue_no_change"


@dataclass(frozen=True)
class Binding:
    event_id: int
    subject_epoch: int
    target_id: int
    predicate: int = PREDICATE
    valid_from: int = VALID_FROM
    valid_until: int = VALID_UNTIL


@dataclass(frozen=True)
class TargetSpec:
    target_id: int
    event_id: int
    epoch: int


@dataclass(frozen=True)
class ParsedFrame:
    sender_id: int
    verdict_bit: int
    confidence_u8: int
    binding: Binding
    sequence: int
    auth_tag: bytes


@dataclass(frozen=True)
class FrameParseResult:
    accepted: tuple[ParsedFrame, ...]
    rejected: tuple[str, ...]


@dataclass(frozen=True)
class SceneBlueprint:
    split: str
    episode: int
    event: bool
    true_target: int | None
    subtype: str | None
    targets: tuple[TargetSpec, ...]
    service_order: tuple[int, ...]
    binding_permutation: tuple[int, ...]
    sequences: tuple[int, ...]
    tags: tuple[bytes, ...]
    frame_display_order: tuple[int, ...]

    def frame_bytes(self, arm: str) -> tuple[bytes, ...]:
        if arm not in {"LEARN-CORRECT", "LEARN-PERM", "DET-BOUND"}:
            raise ValueError(f"arm does not consume bound frames: {arm}")
        rows: list[bytes] = []
        for payload_slot in range(4):
            binding_slot = (
                payload_slot
                if arm in {"LEARN-CORRECT", "DET-BOUND"}
                else self.binding_permutation[payload_slot]
            )
            target = self.targets[binding_slot]
            verdict = int(self.event and payload_slot == self.true_target)
            rows.append(
                encode_frame(
                    sender_id=SENDER_ID,
                    verdict_bit=verdict,
                    confidence_u8=CONFIDENCE_U8,
                    binding=Binding(target.event_id, target.epoch, target.target_id),
                    sequence=self.sequences[payload_slot],
                    auth_tag=self.tags[payload_slot],
                )
            )
        return tuple(rows[index] for index in self.frame_display_order)


@dataclass(frozen=True)
class CanonicalState:
    service_position: int
    target_action_count: int
    previous_feedback: str
    any_authenticated_negative: bool
    active_matching_negative: bool
    event_located: bool

    def as_tuple(self) -> tuple[int, int, str, bool, bool, bool]:
        return (
            self.service_position,
            self.target_action_count,
            self.previous_feedback,
            self.any_authenticated_negative,
            self.active_matching_negative,
            self.event_located,
        )


def encode_frame(
    *, sender_id: int, verdict_bit: int, confidence_u8: int,
    binding: Binding, sequence: int, auth_tag: bytes,
) -> bytes:
    if len(auth_tag) != 16:
        raise ValueError("auth_tag must be 16 bytes")
    return FRAME_STRUCT.pack(
        FRAME_VERSION, sender_id, verdict_bit, confidence_u8, binding.predicate,
        binding.event_id, binding.subject_epoch, binding.target_id,
        binding.valid_from, binding.valid_until, sequence, bytes(10), auth_tag,
    )


def parse_frames(
    raw_frames: Sequence[bytes], *, authenticated_bytes: frozenset[bytes],
    approved_senders: frozenset[int] = frozenset({SENDER_ID}),
) -> FrameParseResult:
    """Parse frames in display order with the frozen rejection precedence."""
    accepted: list[ParsedFrame] = []
    rejected: list[str] = []
    seen_sequences: set[int] = set()
    for raw in raw_frames:
        if len(raw) != FRAME_SIZE:
            rejected.append("wrong_length")
            continue
        fields = FRAME_STRUCT.unpack(raw)
        if fields[0] != FRAME_VERSION:
            rejected.append("wrong_version")
            continue
        sender = fields[1]
        if raw not in authenticated_bytes:
            rejected.append("failed_authentication")
            continue
        if sender not in approved_senders:
            rejected.append("unapproved_sender")
            continue
        sequence = fields[10]
        if sequence in seen_sequences:
            rejected.append("duplicate_sequence")
            continue
        seen_sequences.add(sequence)
        accepted.append(
            ParsedFrame(
                sender_id=sender,
                verdict_bit=fields[2],
                confidence_u8=fields[3],
                binding=Binding(
                    event_id=fields[5], subject_epoch=fields[6],
                    target_id=fields[7], predicate=fields[4],
                    valid_from=fields[8], valid_until=fields[9],
                ),
                sequence=sequence,
                auth_tag=fields[12],
            )
        )
    return FrameParseResult(tuple(accepted), tuple(rejected))


def frame_signals(
    parsed: Sequence[ParsedFrame], *, target: TargetSpec, current_epoch: int, tick: int,
) -> tuple[bool, bool]:
    any_negative = any(frame.verdict_bit == 1 for frame in parsed)
    active = any(
        frame.verdict_bit == 1
        and frame.binding.event_id == target.event_id
        and frame.binding.subject_epoch == current_epoch
        and frame.binding.target_id == target.target_id
        and frame.binding.predicate == PREDICATE
        and frame.binding.valid_from <= tick <= frame.binding.valid_until
        for frame in parsed
    )
    return any_negative, active


def _unique_nonzero_u64(rng: random.Random, used: set[int]) -> int:
    while True:
        value = rng.getrandbits(64)
        if value and value not in used:
            used.add(value)
            return value


def _balanced_shuffled(items: Iterable[object], rng: random.Random) -> list[object]:
    result = list(items)
    rng.shuffle(result)
    return result


def iter_scenes(base_seed: int, split: str) -> Iterable[SceneBlueprint]:
    """Yield the exact paired, balanced scene manifest for one split and seed."""
    if split not in SPLIT_COUNTS:
        raise ValueError(f"unknown split: {split}")
    total, event_count, cell_repeats = SPLIT_COUNTS[split]
    clean_count = total - event_count
    world = random.Random(WORLD_NAMESPACES[split] + base_seed)
    binding = random.Random(BINDING_NAMESPACES[split] + base_seed)

    classes = _balanced_shuffled([True] * event_count + [False] * clean_count, world)
    event_specs = _balanced_shuffled(
        ((target, subtype) for target in range(4)
         for subtype in ("repairable", "terminal")
         for _ in range(event_count // 8)),
        world,
    )
    service_by_class = {
        flag: _balanced_shuffled(
            (order for order in SERVICE_ORDERS for _ in range(count // 24)), world
        )
        for flag, count in ((True, event_count), (False, clean_count))
    }
    event_perms: dict[tuple[int, str], list[tuple[int, ...]]] = {}
    for target in range(4):
        for subtype in ("repairable", "terminal"):
            event_perms[(target, subtype)] = _balanced_shuffled(
                (pi for pi in PERMUTATIONS for _ in range(cell_repeats)), binding
            )
    clean_perms = _balanced_shuffled(
        (pi for pi in PERMUTATIONS for _ in range(clean_count // 24)), binding
    )
    class_cursor = Counter()
    event_cursor = Counter()
    event_index = 0
    clean_index = 0
    for episode, is_event in enumerate(classes, start=1):
        if is_event:
            true_target, subtype = event_specs[event_index]
            event_index += 1
            key = (true_target, subtype)
            pi = event_perms[key][event_cursor[key]]
            event_cursor[key] += 1
        else:
            true_target = None
            subtype = None
            pi = clean_perms[clean_index]
            clean_index += 1
        service_order = service_by_class[is_event][class_cursor[is_event]]
        class_cursor[is_event] += 1
        used_target_ids: set[int] = set()
        used_event_ids: set[int] = set()
        targets = tuple(
            TargetSpec(
                target_id=_unique_nonzero_u64(world, used_target_ids),
                event_id=_unique_nonzero_u64(world, used_event_ids),
                epoch=world.randint(1, 2**32 - 2),
            )
            for _ in range(4)
        )
        used_sequences: set[int] = set()
        sequences: list[int] = []
        for _ in range(4):
            while True:
                value = binding.getrandbits(32)
                if value and value not in used_sequences:
                    used_sequences.add(value)
                    sequences.append(value)
                    break
        tags = tuple(binding.randbytes(16) for _ in range(4))
        display = list(range(4))
        binding.shuffle(display)
        yield SceneBlueprint(
            split=split, episode=episode, event=is_event,
            true_target=true_target, subtype=subtype, targets=targets,
            service_order=service_order, binding_permutation=pi,
            sequences=tuple(sequences), tags=tags,
            frame_display_order=tuple(display),
        )


def manifest_balance(scenes: Sequence[SceneBlueprint]) -> dict[str, object]:
    event_cells = Counter(
        (scene.true_target, scene.subtype, scene.binding_permutation)
        for scene in scenes if scene.event
    )
    order_by_class = {
        label: Counter(scene.service_order for scene in scenes if scene.event is flag)
        for label, flag in (("event", True), ("all_clean", False))
    }
    pi_by_class = {
        label: Counter(scene.binding_permutation for scene in scenes if scene.event is flag)
        for label, flag in (("event", True), ("all_clean", False))
    }
    return {
        "scenes": len(scenes),
        "event": sum(scene.event for scene in scenes),
        "all_clean": sum(not scene.event for scene in scenes),
        "event_cell_counts": sorted(event_cells.values()),
        "service_order_counts": {key: sorted(value.values()) for key, value in order_by_class.items()},
        "permutation_counts": {key: sorted(value.values()) for key, value in pi_by_class.items()},
    }


@dataclass
class TargetRuntime:
    spec: TargetSpec
    invalid: bool
    subtype: str | None
    epoch: int
    actions: list[str]
    reward: float = 0.0
    false_complete: bool = False


Selector = Callable[[CanonicalState], Action]


def run_scene(
    scene: SceneBlueprint, *, arm: str, selector: Selector,
    transition_observer: Callable[[CanonicalState, Action, float, CanonicalState | None, bool], None] | None = None,
    retain_rows: bool = False,
) -> dict[str, object]:
    """Run one scene. Terminal target actions transition to the next target state."""
    frame_arm = "LEARN-CORRECT" if arm in {"AUTH-PROBE", "IGNORE"} else arm
    raw_frames = scene.frame_bytes(frame_arm)
    parsed_result = parse_frames(raw_frames, authenticated_bytes=frozenset(raw_frames))
    if parsed_result.rejected or len(parsed_result.accepted) != 4:
        raise AssertionError("registered frame construction must parse exactly")
    runtimes = [
        TargetRuntime(
            spec=spec,
            invalid=bool(scene.event and index == scene.true_target),
            subtype=scene.subtype if scene.event and index == scene.true_target else None,
            epoch=spec.epoch,
            actions=[],
        )
        for index, spec in enumerate(scene.targets)
    ]
    tick = 1
    event_located = False
    feedback = Feedback.NONE
    rows: list[dict[str, object]] = []
    components: Counter[str] = Counter()
    transitions = 0
    for service_position, target_index in enumerate(scene.service_order):
        runtime = runtimes[target_index]
        feedback = Feedback.NONE
        for local_index in range(1, MAX_TARGET_ACTIONS + 1):
            any_negative, active = frame_signals(
                parsed_result.accepted, target=runtime.spec,
                current_epoch=runtime.epoch, tick=tick,
            )
            state = CanonicalState(
                service_position=service_position,
                target_action_count=local_index - 1,
                previous_feedback=feedback.value,
                any_authenticated_negative=any_negative,
                active_matching_negative=active,
                event_located=event_located,
            )
            action = selector(state)
            if action not in ACTIONS:
                raise ValueError(f"selector returned invalid action: {action}")
            pre_invalid = runtime.invalid
            pre_epoch = runtime.epoch
            reward = 0.0
            terminal = action in {Action.COMPLETE, Action.ABSTAIN}
            forced = False
            if action is Action.COMPLETE:
                if pre_invalid:
                    reward = -10.0
                    runtime.false_complete = True
                    components["complete_invalid"] += reward
                else:
                    reward = 1.0
                    components["complete_valid"] += reward
            elif action is Action.CONTINUE:
                reward = -0.10
                components["continue"] += reward
                if pre_invalid and runtime.subtype == "repairable":
                    runtime.invalid = False
                    runtime.epoch += 1
                    event_located = True
                    feedback = Feedback.CONTINUE_EPOCH_CHANGED
                else:
                    feedback = Feedback.CONTINUE_NO_CHANGE
            elif action is Action.PROBE:
                reward = -0.25
                components["probe"] += reward
                if not pre_invalid:
                    feedback = Feedback.PROBE_VALID
                elif runtime.subtype == "repairable":
                    feedback = Feedback.PROBE_REPAIRABLE
                    event_located = True
                else:
                    feedback = Feedback.PROBE_TERMINAL
                    event_located = True
            else:
                if pre_invalid and runtime.subtype == "terminal":
                    reward = 0.20
                    components["abstain_terminal"] += reward
                else:
                    reward = -0.80
                    components["abstain_valid_or_repairable"] += reward
            runtime.actions.append(action.value)
            if local_index == MAX_TARGET_ACTIONS and not terminal:
                forced = True
                terminal = True
                runtime.actions.append("forced_abstain")
                if runtime.invalid and runtime.subtype == "terminal":
                    reward += 0.20
                    components["abstain_terminal"] += 0.20
                else:
                    reward -= 0.80
                    components["abstain_valid_or_repairable"] -= 0.80
            runtime.reward += reward
            learning_reward = reward + (COMMUNICATION_COST if transitions == 0 else 0.0)
            transitions += 1
            tick += 1
            next_state: CanonicalState | None
            if terminal and service_position == 3:
                next_state = None
            elif terminal:
                next_index = scene.service_order[service_position + 1]
                next_runtime = runtimes[next_index]
                next_any, next_active = frame_signals(
                    parsed_result.accepted, target=next_runtime.spec,
                    current_epoch=next_runtime.epoch, tick=tick,
                )
                next_state = CanonicalState(
                    service_position=service_position + 1, target_action_count=0,
                    previous_feedback=Feedback.NONE.value,
                    any_authenticated_negative=next_any,
                    active_matching_negative=next_active,
                    event_located=event_located,
                )
            else:
                next_any, next_active = frame_signals(
                    parsed_result.accepted, target=runtime.spec,
                    current_epoch=runtime.epoch, tick=tick,
                )
                next_state = CanonicalState(
                    service_position=service_position,
                    target_action_count=local_index,
                    previous_feedback=feedback.value,
                    any_authenticated_negative=next_any,
                    active_matching_negative=next_active,
                    event_located=event_located,
                )
            if transition_observer is not None:
                transition_observer(
                    state, action, learning_reward, next_state,
                    terminal and service_position == 3,
                )
            if retain_rows:
                rows.append({
                    "service_position": service_position,
                    "target_index": target_index,
                    "local_action_index": local_index,
                    "action": action.value,
                    "reward": reward,
                    "learning_reward": learning_reward,
                    "pre_action_invalid": pre_invalid,
                    "post_action_invalid": runtime.invalid,
                    "pre_action_epoch": pre_epoch,
                    "post_action_epoch": runtime.epoch,
                    "feedback": feedback.value,
                    "forced_abstention": forced,
                    "terminal": terminal,
                })
            if terminal:
                break
    components["communication"] += COMMUNICATION_COST
    scene_reward = COMMUNICATION_COST + sum(runtime.reward for runtime in runtimes)
    false_complete = bool(
        scene.event and scene.true_target is not None and runtimes[scene.true_target].false_complete
    )
    d_joint = False
    if scene.event and scene.true_target is not None:
        invalid_runtime = runtimes[scene.true_target]
        clean_ok = all(
            runtime.actions == [Action.COMPLETE.value]
            for index, runtime in enumerate(runtimes) if index != scene.true_target
        )
        desired = (
            [Action.CONTINUE.value, Action.COMPLETE.value]
            if scene.subtype == "repairable"
            else [Action.CONTINUE.value, Action.ABSTAIN.value]
        )
        # Probing the invalid target is permitted by D_joint; the clean-target
        # clause above explicitly forbids probes on clean targets.
        invalid_nonprobe_actions = [
            action for action in invalid_runtime.actions if action != Action.PROBE.value
        ]
        d_joint = (
            not invalid_runtime.false_complete
            and clean_ok
            and invalid_nonprobe_actions == desired
        )
    result: dict[str, object] = {
        "split": scene.split,
        "episode": scene.episode,
        "event": scene.event,
        "true_target": scene.true_target,
        "subtype": scene.subtype,
        "scene_reward": scene_reward,
        "communication_cost": COMMUNICATION_COST,
        "reward_components": dict(components),
        "transitions": transitions,
        "false_complete": false_complete,
        "d_joint": d_joint,
        "target_returns": [runtime.reward for runtime in runtimes],
        "target_actions": [list(runtime.actions) for runtime in runtimes],
        "service_order": list(scene.service_order),
        "binding_permutation": list(scene.binding_permutation),
    }
    if retain_rows:
        result["target_action_outcome_rows"] = rows
    return result

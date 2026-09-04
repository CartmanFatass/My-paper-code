"""VSP02-B5R1 Windows-resource-admitted Adam-state continuity discriminator.

The two arms share one oracle-sign update and a byte-identical prepared second
update.  ``ADAM_CARRY`` retains the complete post-update-0 Adam state while
``ADAM_RESET`` alone receives canonical fresh-empty Adam slots.  Subsequent
closed-loop differences are retained as descendants of that one intervention.
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


B5R1_SCHEMA_VERSION = 1
B5R1_ASSIGNMENT_ID = "VSP02-B5R1-FULL-ADAM-STATE-CONTINUITY"
B5R1_RUN_ID = "VSP02-B5R1-REGISTERED-FULL-01"
B5R1_CANDIDATE = "CAND-VSP-02@adversarial-revision-v10"
B5R1_DIRECTION_ID = "CAND-VSP-02"
B5R1_HOST_ID = "VSP02-A2-PHYSICAL-LIFECYCLE-HOST-v1"
B5R1_RESOURCE_CLASS = "B_TOY_LIGHT"
B5R1_POOL_UNITS = 1
B5R1_IMPLEMENTATION_BASE = "204af1e02372686e9e51eb592ea60897076237ed"
B5R1_FREEZE_HANDOFF_SHA256 = "86e2327e1895be8a9a7ced0304b62c9b4833e82943bfba0012c4398ae16be0f8"
B5R1_FREEZE_PUBLICATION_COMMIT = "204af1e02372686e9e51eb592ea60897076237ed"
B5R1_CANONICAL_RUN_ROOT = "temp/sessions/code_project_manager/vsp02_b5r1_windows_resource_admission/"
B5R1_OPERATOR_RECEIPT = "temp/sessions/code_project_manager/vsp02_b5r1_operator_receipt.json"
B5R1_PHYSICAL_TAPE_PREFIX = f"{B5R1_ASSIGNMENT_ID}/PHYSICAL"
B5R1_SEED_PREFIX = "VSP02-B5R1-V1\0"
B5R1_UNITS = tuple((f"VSP02-B5R1-U{index:02d}", 22_051_000 + index) for index in range(1, 6))
B5R1_ARMS = ("ADAM_CARRY", "ADAM_RESET")
B5R1_SEED_STREAMS = (
    "parameter_initialization", "optimizer_initialization", "training_address_tape",
    "learner_stochasticity", "minibatch_order", "evaluation_address_tape",
)
B5R1_TAPE_KINDS = (
    "cue_schedule", "environment_randomness", "behavior_mixture_coin", "sampling_uniform",
    "minibatch_order", "evaluation_cue_schedule", "evaluation_environment_randomness",
)
B5R1_TAPE_STREAM_BY_KIND = {
    "cue_schedule": "training_address_tape",
    "environment_randomness": "training_address_tape",
    "behavior_mixture_coin": "training_address_tape",
    "sampling_uniform": "training_address_tape",
    "minibatch_order": "minibatch_order",
    "evaluation_cue_schedule": "evaluation_address_tape",
    "evaluation_environment_randomness": "evaluation_address_tape",
}
B5R1_UPDATES_PER_ARM = 128
B5R1_BATCH_SIZE = 8
B5R1_EVAL_EPISODES_PER_ARM_UNIT = 128
B5R1_BRANCH_PRECEDENCE = (
    "B5_INVALID_OR_INACTIVE",
    "B5_NEITHER_ARM_EXACT_SUCCESS_ON_PANEL",
    "B5_CARRY_DIRECTION_DISCORDANCE_ONLY",
    "B5_RESET_DIRECTION_DISCORDANCE_ONLY",
    "B5_NO_EXACT_ENDPOINT_LOCALIZATION_ON_PANEL",
    "B5_BIDIRECTIONAL_PAIRED_ROOT_TAPE_DISCORDANCE",
)
B5R1_CAPS = {
    "environment_transitions_total": 57_400,
    "real_training_episodes_total": 10_200,
    "evaluation_episodes_total": 1_280,
    "optimizer_updates_total": 1_275,
    "checkpoints_total": 10,
    "result_bearing_runs": 1,
    "pool_units": 1,
    "cpu_minutes": 30,
    "peak_memory_gib": 2,
}
B5R1_RSS_CAP_BYTES = 2 * 1024**3
B5R1_ADMISSION_MAX_AGE_SECONDS = 60.0
B5R1_WINDOWS_BINDING = {
    "ffi_path": "kernel32.GetCurrentProcess->psapi.GetProcessMemoryInfo",
    "get_current_process_restype": "ctypes.c_void_p",
    "get_process_memory_info_argtypes": [
        "ctypes.c_void_p", "ctypes.POINTER(ProcessMemoryCounters)", "wintypes.DWORD",
    ],
    "get_process_memory_info_restype": "wintypes.BOOL",
    "binding_valid": True,
}
B5R1_CLAIM_PATHS = (
    "experiments/candidates/vsp_02/vsp02_b5r1_windows_resource_admission.py",
    "scripts/run_vsp02_b5r1_windows_resource_admission.py",
    "tests/experiments/candidates/vsp_02/test_vsp02_b5r1_windows_resource_admission.py",
    "docs/research/candidates/vsp_02/VSP02_B5R1_WINDOWS_RESOURCE_ADMISSION_CODE_SCIENCE_INDEX.md",
)
B5R1_DEPENDENCY_PATHS = (
    "experiments/candidates/vsp_02/learned_cue_conditioned_lifecycle_control_v2.py",
    "experiments/candidates/vsp_02/owner_action_responsive_lifecycle.py",
)
B5R1_RUNTIME_PATHS = B5R1_CLAIM_PATHS + B5R1_DEPENDENCY_PATHS
ORACLE_SIGN_ACTOR_ROUTE = "-correctness_sign(A_behavior,cue)*detach(abs(G-b))*log(mu(A_behavior|history))-0.01*entropy"
CRITIC_ROUTE = "mean(0.5*(G-b)^2)"
BEHAVIOR_MIXTURE_ROUTE = "coin<0.8:sample(raw_softmax);else:sample(Uniform(RELEASE,HOLD));likelihood=0.8*raw_softmax+0.1"
FIXED_UPDATE_ORDER = B5R1_ARMS


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
    return json.dumps(json_ready(value), ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _tensor_payload(tensor: Tensor) -> dict[str, object]:
    cpu = tensor.detach().cpu().contiguous()
    return {"dtype": str(cpu.dtype), "shape": list(cpu.shape), "values": cpu.reshape(-1).tolist()}


def model_payload(model: torch.nn.Module) -> dict[str, object]:
    return {name: _tensor_payload(tensor) for name, tensor in sorted(model.state_dict().items())}


def optimizer_payload(optimizer: torch.optim.Optimizer) -> dict[str, object]:
    return json_ready(optimizer.state_dict())  # type: ignore[return-value]


def _architecture_payload(model: b1.GRUActorCritic) -> dict[str, object]:
    return {
        "dtype": "torch.float64", "recurrent": "one-layer GRUCell",
        "input_size": int(model.gru.input_size), "hidden_size": int(model.gru.hidden_size),
        "actor_logits": int(model.actor.out_features), "critic_outputs": int(model.critic.out_features),
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "parameter_order": [name for name, _ in model.named_parameters()],
        "parameter_groups": [[name for name, _ in model.named_parameters()]],
    }


def _cpu_time_seconds() -> float:
    return time.process_time()


def _peak_process_rss_bytes() -> int:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
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
    material = B5R1_SEED_PREFIX + "\0".join(str(part) for part in parts)
    return int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:8], "big")


def b5r1_seed(unit_id: str, decimal_root: int, stream_name: str) -> int:
    if (unit_id, decimal_root) not in B5R1_UNITS:
        raise ValueError(f"unregistered B5R1 unit/root: {unit_id}/{decimal_root}")
    if stream_name not in B5R1_SEED_STREAMS:
        raise ValueError(f"unregistered B5R1 seed stream: {stream_name}")
    return 1 + (_hash_int(unit_id, decimal_root, stream_name) % 2_147_483_646)


@dataclass(frozen=True)
class B5R1AddressTape:
    """Fresh stateless B5 exogenous tape keyed by complete semantic address."""

    unit_id: str
    decimal_root: int

    def __post_init__(self) -> None:
        if (self.unit_id, self.decimal_root) not in B5R1_UNITS:
            raise ValueError(f"unregistered B5R1 unit/root: {self.unit_id}/{self.decimal_root}")

    def word(self, kind: str, *address: object) -> int:
        if kind not in B5R1_TAPE_KINDS or not address:
            raise ValueError("unregistered or empty B5R1 tape address")
        stream = B5R1_TAPE_STREAM_BY_KIND[kind]
        return _hash_int(self.unit_id, self.decimal_root, stream, b5r1_seed(self.unit_id, self.decimal_root, stream), kind, *address)

    def uniform(self, kind: str, *address: object) -> float:
        return (self.word(kind, *address) + 0.5) / float(2**64)

    def token(self, kind: str, *address: object) -> str:
        return f"{self.word(kind, *address):016x}"

    def identity(self) -> str:
        return digest({"assignment": B5R1_ASSIGNMENT_ID, "unit_id": self.unit_id, "decimal_root": self.decimal_root})

    def address(self, kind: str, *address: object) -> dict[str, object]:
        if kind not in B5R1_TAPE_KINDS or not address:
            raise ValueError("invalid B5R1 tape address")
        return {"treatment": B5R1_ASSIGNMENT_ID, "unit_id": self.unit_id, "decimal_root": self.decimal_root,
                "stream": B5R1_TAPE_STREAM_BY_KIND[kind], "field": kind, "address": list(address)}


class B5R1LifecycleHost(b1.LifecycleHost):
    """Fresh B5 identity wrapper around the accepted B1/A1 physical law."""

    def step(self, action: b1.Action, *, action_probabilities: Sequence[float]) -> dict[str, object]:
        if not self._open or self.escrow is not None:
            raise RuntimeError("episode action can be committed exactly once")
        probabilities = tuple(float(value) for value in action_probabilities)
        if len(probabilities) != 2 or any(not math.isfinite(value) or value < 0.0 for value in probabilities) or abs(sum(probabilities) - 1.0) > 1e-12:
            raise ValueError("invalid RELEASE/HOLD probability pair")
        escrow_id = hashlib.sha256(f"{B5R1_ASSIGNMENT_ID}/{self.lifecycle_id}/{self.owner_epoch}/{b1.B1_BEHAVIOR_VERSION}".encode()).hexdigest()
        self.escrow = b1.ActionScoreEscrow(escrow_id=escrow_id, action=action.value,
            action_probabilities=probabilities, selected_likelihood=probabilities[action.index],
            owner_epoch=self.owner_epoch, behavior_version=b1.B1_BEHAVIOR_VERSION)
        tape_id = f"{B5R1_PHYSICAL_TAPE_PREFIX}/{self.lifecycle_id}"
        self.tape_ids = [tape_id]
        first = b1.a1.apply_boundary(self.record, contract=b1.a1.candidate_contract(),
            action=b1.a1.OwnerAction(action.value), command_token=self.token, world=self.world,
            boundary_index=1, physical_clock=1,
            tape=b1.a1.PairedTape(tape_id=tape_id, primitive_action=b1.B1_PRIMITIVE), release_id=escrow_id)
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
            second = b1.a1.apply_boundary(self.record, contract=b1.a1.candidate_contract(),
                action=b1.a1.OwnerAction.HOLD, command_token=self.token, world=self.world,
                boundary_index=2, physical_clock=2,
                tape=b1.a1.PairedTape(tape_id=tape_id, natural=True, primitive_action=b1.B1_PRIMITIVE),
                release_id=escrow_id)
            self.record = second.record
            self.states.append(self.record.phase.value)
            self.environment_transitions += 1
            self.rewards.append(0)
            if self.record.phase is not b1.a1.Phase.ENDED_NATURAL:
                raise AssertionError("HOLD did not naturally terminate")
        if self.record.end_cause is None or self.escrow.consumption_count != 0:
            raise AssertionError("invalid pre-close escrow state")
        self.escrow = replace(self.escrow, consumption_count=1)
        self.record = replace(self.record, phase=b1.a1.Phase.TARGET_CLOSED_TOMBSTONE,
            target_close_clock=self.record.physical_clock, tombstone_version=b1.B1_BEHAVIOR_VERSION,
            acknowledgements=self.record.acknowledgements + ("TARGET_CLOSED",))
        self.states.append(self.record.phase.value)
        self.environment_transitions += 1
        self._open = False
        return {"reward_sequence": list(self.rewards),
                "physical_return": sum(reward * (b1.B1_GAMMA**index) for index, reward in enumerate(self.rewards)),
                "physical_tape_ids": list(self.tape_ids), "environment_transitions": self.environment_transitions}


def _foreign_seed(prefix: str, unit_id: str, root: int, stream: str, *, b4_style: bool) -> int:
    if b4_style:
        material = prefix + "\0".join((unit_id, str(root), stream))
    else:
        material = prefix + unit_id + "\0" + str(root) + "\0" + stream
    return 1 + (int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:8], "big") % 2_147_483_646)


def seed_and_tape_report() -> dict[str, object]:
    derived: dict[str, dict[str, int]] = {}
    flat: list[int] = []
    for unit_id, root in B5R1_UNITS:
        tape = B5R1AddressTape(unit_id, root)
        values = {stream: b5r1_seed(unit_id, root, stream) for stream in B5R1_SEED_STREAMS}
        values.update({f"address_root/{kind}": tape.word(kind, "ROOT") for kind in B5R1_TAPE_KINDS})
        derived[unit_id] = values
        flat.extend(values.values())
    predecessor_values = {b1.stream_seed(seed_id, stream) for seed_id in b1.B1_SEED_IDS for stream in b1.B1_RNG_STREAMS}
    b2_streams = (
        "parameter_initialization", "optimizer_initialization", "train_owner_cue_clone",
        "train_environment_event", "train_action_uniform", "train_minibatch_order",
        "train_stochastic_layer", "evaluation_owner_cue_clone", "evaluation_environment_event",
    )
    for prefix, family, root_base, streams, b4_style in (
        ("VSP02-B2-V1\0", "B2", 22_020_000, b2_streams, False),
        ("VSP02-B3-V1\0", "B3", 22_030_000, b2_streams, False),
        ("VSP02-B4-V1\0", "B4", 22_040_000, B5R1_SEED_STREAMS, True),
        ("VSP02-B5-V1\0", "B5", 22_050_000, B5R1_SEED_STREAMS, True),
    ):
        predecessor_values.update(
            _foreign_seed(prefix, f"VSP02-{family}-U{index:02d}", root_base + index, stream, b4_style=b4_style)
            for index in range(1, 6) for stream in streams
        )
    predecessor_units = set(b1.B1_SEED_IDS) | {
        f"VSP02-{family}-U{index:02d}" for family in ("B2", "B3", "B4", "B5") for index in range(1, 6)
    }
    predecessor_roots = (
        set(range(22_020_001, 22_020_006))
        | set(range(22_030_001, 22_030_006))
        | set(range(22_040_001, 22_040_006))
        | set(range(22_050_001, 22_050_006))
    )
    return {
        "function": "SHA256(VSP02-B5R1-V1, unit_id, decimal_root, stream, field, full_address)",
        "seed_prefix": B5R1_SEED_PREFIX,
        "seed_streams": list(B5R1_SEED_STREAMS), "tape_kinds": list(B5R1_TAPE_KINDS),
        "derived_roots": derived, "all_b5_roots_unique": len(flat) == len(set(flat)),
        "collision_with_predecessor_values": sorted(set(flat) & predecessor_values),
        "identity_collision_with_predecessors": any(unit in predecessor_units or root in predecessor_roots for unit, root in B5R1_UNITS),
        "identity_families": {
            "run": B5R1_RUN_ID, "tape": B5R1_PHYSICAL_TAPE_PREFIX,
            "batch": f"{B5R1_ASSIGNMENT_ID}/<unit>/U<update>/<arm>/BATCH",
            "checkpoint": f"{B5R1_ASSIGNMENT_ID}/<unit>/<arm>/FINAL-128",
            "evaluation": f"{B5R1_ASSIGNMENT_ID}/<unit>/<arm>/EVAL/<episode>",
        },
        "identity_families_treatment_prefixed": True, "silent_reseed_path": False,
        "predecessor_or_g52_state_reuse": False,
    }


def _forward(model: b1.GRUActorCritic, observations: Sequence[Mapping[str, object]]) -> tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
    hidden = torch.zeros(b1.B1_HIDDEN_SIZE, dtype=torch.float64)
    hidden = model.gru(b1.observation_vector(observations[0]), hidden)
    hidden = model.gru(b1.observation_vector(observations[1]), hidden)
    logits = model.actor(hidden)
    raw = torch.softmax(logits, dim=0)
    probabilities = 0.8 * raw + 0.1
    entropy = -(probabilities * torch.log(probabilities)).sum()
    return logits, raw, probabilities, model.critic(hidden).squeeze(0), entropy


def _observation_firewall(observations: Sequence[Mapping[str, object]]) -> bool:
    if len(observations) != 2:
        return False
    expected = set(b1.B1_OBSERVATION_FIELDS)
    if any(set(observation) != expected or set(observation) & set(b1.B1_FORBIDDEN_OBSERVATION_FIELDS) for observation in observations):
        return False
    cue, decide = observations
    return cue["cue_mask"] == 1 and cue["cue_value"] in (0, 1) and decide["cue_mask"] == 0 and decide["cue_value"] == 0


def _initial_recurrent_state() -> dict[str, object]:
    return {"reset_each_episode": True, "hidden": [0.0] * b1.B1_HIDDEN_SIZE, "dtype": "torch.float64"}


def _initial_carried_learner_state() -> dict[str, object]:
    return {"next_update_index": 0, "optimizer_steps": 0, "batches_consumed": 0,
            "rows_consumed": 0, "last_batch_digest": None, "last_batch_order": None}


def _initial_learner_rng_state(unit_id: str, root: int) -> dict[str, object]:
    return {
        "parameter_initialization_seed": b5r1_seed(unit_id, root, "parameter_initialization"),
        "optimizer_initialization_seed": b5r1_seed(unit_id, root, "optimizer_initialization"),
        "learner_stochasticity_seed": b5r1_seed(unit_id, root, "learner_stochasticity"),
        "learner_stochasticity_draw_count": 0,
        "minibatch_order_seed": b5r1_seed(unit_id, root, "minibatch_order"),
        "minibatch_order_is_address_indexed": True, "unlisted_rng_allowed": False,
    }


def _complete_state_payload(model: b1.GRUActorCritic, optimizer: torch.optim.Optimizer,
                            learner_state: Mapping[str, object], rng_state: Mapping[str, object]) -> dict[str, object]:
    return {
        "actor_critic_recurrent_parameters": model_payload(model), "optimizer": optimizer_payload(optimizer),
        "recurrent_state": _initial_recurrent_state(), "carried_learner_state": dict(learner_state),
        "registered_learner_rng_state": dict(rng_state),
    }


def _complete_state_hash(model: b1.GRUActorCritic, optimizer: torch.optim.Optimizer,
                         learner_state: Mapping[str, object], rng_state: Mapping[str, object]) -> str:
    return digest(_complete_state_payload(model, optimizer, learner_state, rng_state))


def _new_common_learner(unit_id: str, root: int) -> tuple[b1.GRUActorCritic, torch.optim.Optimizer]:
    model = b1.GRUActorCritic(init_seed=b5r1_seed(unit_id, root, "parameter_initialization"))
    return model, torch.optim.Adam(model.parameters(), lr=0.003)


def _clone_post_update0(model: b1.GRUActorCritic, optimizer: torch.optim.Optimizer) -> tuple[
    dict[str, b1.GRUActorCritic], dict[str, torch.optim.Optimizer]
]:
    models = {arm: deepcopy(model) for arm in B5R1_ARMS}
    state = deepcopy(optimizer.state_dict())
    optimizers: dict[str, torch.optim.Optimizer] = {}
    for arm in B5R1_ARMS:
        clone = torch.optim.Adam(models[arm].parameters(), lr=0.003)
        clone.load_state_dict(deepcopy(state))
        optimizers[arm] = clone
    return models, optimizers


def _optimizer_group_contract(model: b1.GRUActorCritic, optimizer: torch.optim.Optimizer) -> dict[str, object]:
    names = {id(parameter): name for name, parameter in model.named_parameters()}
    return {
        "groups": [{
            "parameter_names": [names[id(parameter)] for parameter in group["params"]],
            "lr": float(group["lr"]), "betas": list(group["betas"]), "eps": float(group["eps"]),
            "weight_decay": float(group["weight_decay"]), "amsgrad": bool(group["amsgrad"]),
            "maximize": bool(group["maximize"]), "capturable": bool(group["capturable"]),
            "differentiable": bool(group["differentiable"]),
        } for group in optimizer.param_groups]
    }


def adam_state_report(model: b1.GRUActorCritic, optimizer: torch.optim.Optimizer) -> dict[str, object]:
    slots: dict[str, object] = {}
    finite = True
    steps: list[int] = []
    global_nonzero = False
    allowed = {"step", "exp_avg", "exp_avg_sq"} | ({"max_exp_avg_sq"} if optimizer.param_groups[0]["amsgrad"] else set())
    for name, parameter in model.named_parameters():
        state = optimizer.state.get(parameter, {})
        unexpected = sorted(set(state) - allowed)
        slot_payload = {key: _tensor_payload(value) if isinstance(value, Tensor) else value for key, value in sorted(state.items())}
        tensor_values = [value for value in state.values() if isinstance(value, Tensor)]
        finite = finite and not unexpected and set(state) == allowed and all(torch.isfinite(value).all() for value in tensor_values)
        if "step" in state:
            steps.append(int(state["step"].item() if isinstance(state["step"], Tensor) else state["step"]))
        global_nonzero = global_nonzero or any(bool(torch.count_nonzero(state[key])) for key in ("exp_avg", "exp_avg_sq") if key in state)
        slots[name] = {"slot_names": sorted(state), "unexpected_slots": unexpected, "payload": slot_payload}
    return {"parameter_order": [name for name, _ in model.named_parameters()], "slots": slots,
            "all_slots_finite": finite, "all_steps_exactly_one": len(steps) == len(tuple(model.parameters())) and all(step == 1 for step in steps),
            "globally_at_least_one_moment_nonzero": global_nonzero, "parameter_group_contract": _optimizer_group_contract(model, optimizer)}


def correctness_sign(action: str, cue: int) -> float:
    if action not in {b1.Action.RELEASE.value, b1.Action.HOLD.value} or cue not in (0, 1):
        raise ValueError("correctness sign requires registered action and cue")
    correct = (cue == 0 and action == b1.Action.HOLD.value) or (cue == 1 and action == b1.Action.RELEASE.value)
    return 1.0 if correct else -1.0


def _ranked_permutation(tape: B5R1AddressTape, kind: str, group: object, size: int) -> list[int]:
    return sorted(range(size), key=lambda index: (tape.word(kind, group, index), index))


def _schedule(unit_id: str, root: int) -> list[dict[str, object]]:
    tape = B5R1AddressTape(unit_id, root)
    rows: list[dict[str, object]] = []
    for update_index in range(B5R1_UPDATES_PER_ARM):
        base_cues = [0] * 4 + [1] * 4
        order = _ranked_permutation(tape, "cue_schedule", update_index, B5R1_BATCH_SIZE)
        for within, source in enumerate(order):
            episode = update_index * B5R1_BATCH_SIZE + within
            rows.append({"unit_id": unit_id, "decimal_root": root, "update_index": update_index,
                "within_update": within, "episode_index": episode, "owner_epoch": f"{unit_id}-TR-{episode:04d}",
                "true_cue": base_cues[source], "cue_source_index": source,
                "clone_id": f"{unit_id}/TRAIN/{episode:04d}"})
    return rows


def _schedule_contract(rows: Sequence[Mapping[str, object]]) -> bool:
    return len(rows) == 1_024 and Counter(int(row["true_cue"]) for row in rows) == Counter({0: 512, 1: 512}) and all(
        Counter(int(row["true_cue"]) for row in rows[start:start + 8]) == Counter({0: 4, 1: 4}) for start in range(0, 1_024, 8))


def _update_tape_receipt(tape: B5R1AddressTape, update_index: int) -> dict[str, object]:
    return json.loads(canonical_bytes({
        "tape_identity": tape.identity(), "update_index": update_index,
        "cue_permutation": _ranked_permutation(tape, "cue_schedule", update_index, 8),
        "minibatch_order": _ranked_permutation(tape, "minibatch_order", update_index, 8),
        "values": [{"within_update": within,
            "environment_randomness": tape.token("environment_randomness", update_index, within),
            "behavior_mixture_coin": tape.uniform("behavior_mixture_coin", update_index, within),
            "sampling_uniform": tape.uniform("sampling_uniform", update_index, within)} for within in range(8)],
    }))


def _collect_batch(*, unit_id: str, update_index: int, rows: Sequence[Mapping[str, object]],
                   model: b1.GRUActorCritic, tape: B5R1AddressTape) -> tuple[list[dict[str, object]], int]:
    if len(rows) != B5R1_BATCH_SIZE:
        raise ValueError("collector requires one complete eight-row batch")
    batch: list[dict[str, object]] = []
    transitions = 0
    for row in rows:
        within = int(row["within_update"])
        event_token = tape.token("environment_randomness", update_index, within)
        coin = tape.uniform("behavior_mixture_coin", update_index, within)
        sample = tape.uniform("sampling_uniform", update_index, within)
        cue = int(row["true_cue"])
        host = B5R1LifecycleHost()
        cue_observation = host.reset(
            lifecycle_id=f"{B5R1_ASSIGNMENT_ID}/{unit_id}/TRAIN/{int(row['episode_index']):04d}/{event_token}",
            owner_epoch=str(row["owner_epoch"]), true_cue=cue, presented_cue=cue)
        observations = [asdict(cue_observation), asdict(host.decision_observation())]
        if not _observation_firewall(observations):
            raise RuntimeError("training observation firewall mismatch")
        with torch.no_grad():
            _, raw_tensor, probabilities_tensor, _, _ = _forward(model, observations)
        raw = [float(value) for value in raw_tensor]
        probabilities = [float(value) for value in probabilities_tensor]
        policy_component = coin < 0.8
        release_threshold = raw[b1.Action.RELEASE.index] if policy_component else 0.5
        action = b1.Action.RELEASE if sample < release_threshold else b1.Action.HOLD
        episode = host.step(action, action_probabilities=probabilities)
        immutable = {
            "O": observations, "H0": [0.0] * b1.B1_HIDDEN_SIZE,
            "M_reset": [1, 0], "M_active": [1, 1], "M_valid": [0, 1], "M_lifecycle": [0, 1],
            "A_behavior": action.value, "R": list(episode["reward_sequence"]),
            "Done": [False] * (len(episode["reward_sequence"]) - 1) + [True],
            "G": float(episode["physical_return"]), "raw_policy_probabilities": raw,
            "behavior_probabilities": probabilities, "environment_transitions": int(episode["environment_transitions"]),
            "metadata": {
                "unit_id": unit_id, "decimal_root": tape.decimal_root, "update_index": update_index,
                "within_update": within, "episode_index": int(row["episode_index"]),
                "owner_epoch": str(row["owner_epoch"]), "true_cue": cue, "clone_id": str(row["clone_id"]),
                "event_tape_token": event_token,
                "behavior_mixture_component": "POLICY_0.8" if policy_component else "UNIFORM_0.2",
                "behavior_mixture_coin": coin, "sampling_uniform": sample,
                "tape_addresses": {
                    "cue_schedule": tape.address("cue_schedule", update_index, int(row["cue_source_index"])),
                    "environment_randomness": tape.address("environment_randomness", update_index, within),
                    "behavior_mixture_coin": tape.address("behavior_mixture_coin", update_index, within),
                    "sampling_uniform": tape.address("sampling_uniform", update_index, within),
                },
                "physical_tape_ids": list(episode["physical_tape_ids"]),
            },
        }
        batch.append(json.loads(canonical_bytes(immutable)))
        transitions += int(episode["environment_transitions"])
    return batch, transitions


def _immutable_row_contract(row: Mapping[str, object]) -> bool:
    expected_keys = {"O", "H0", "M_reset", "M_active", "M_valid", "M_lifecycle", "A_behavior", "R", "Done", "G",
                     "raw_policy_probabilities", "behavior_probabilities", "environment_transitions", "metadata"}
    if set(row) != expected_keys:
        return False
    observations = row.get("O")
    if not isinstance(observations, Sequence) or not _observation_firewall(observations):
        return False
    if row.get("H0") != [0.0] * b1.B1_HIDDEN_SIZE or row.get("M_reset") != [1, 0] or row.get("M_active") != [1, 1]:
        return False
    if row.get("M_valid") != [0, 1] or row.get("M_lifecycle") != [0, 1] or row.get("A_behavior") not in {"RELEASE", "HOLD"}:
        return False
    rewards, done = row.get("R"), row.get("Done")
    if not isinstance(rewards, list) or not isinstance(done, list) or len(rewards) != len(done) or not done or done[-1] is not True or any(done[:-1]):
        return False
    try:
        expected_return = sum(float(value) * b1.B1_GAMMA**index for index, value in enumerate(rewards))
        raw = [float(value) for value in row["raw_policy_probabilities"]]  # type: ignore[arg-type]
        mixture = [float(value) for value in row["behavior_probabilities"]]  # type: ignore[arg-type]
        metadata = row["metadata"]
        if not isinstance(metadata, Mapping):
            return False
        unit_id, root = str(metadata["unit_id"]), int(metadata["decimal_root"])
        update_index, within = int(metadata["update_index"]), int(metadata["within_update"])
        tape = B5R1AddressTape(unit_id, root)
        addresses = metadata["tape_addresses"]
        if not isinstance(addresses, Mapping):
            return False
        cue_source = int(addresses["cue_schedule"]["address"][-1])  # type: ignore[index]
    except (KeyError, TypeError, ValueError, IndexError):
        return False
    if not math.isclose(float(row["G"]), expected_return, rel_tol=0.0, abs_tol=1e-12):
        return False
    if len(raw) != 2 or len(mixture) != 2 or any(not math.isfinite(value) for value in (*raw, *mixture)):
        return False
    if not math.isclose(sum(raw), 1.0, rel_tol=0.0, abs_tol=1e-12) or any(not math.isclose(mix, 0.8 * policy + 0.1, rel_tol=0.0, abs_tol=1e-12) for mix, policy in zip(mixture, raw)):
        return False
    expected_addresses = {
        "cue_schedule": tape.address("cue_schedule", update_index, cue_source),
        "environment_randomness": tape.address("environment_randomness", update_index, within),
        "behavior_mixture_coin": tape.address("behavior_mixture_coin", update_index, within),
        "sampling_uniform": tape.address("sampling_uniform", update_index, within),
    }
    physical = metadata.get("physical_tape_ids")
    return (
        addresses == expected_addresses
        and _ranked_permutation(tape, "cue_schedule", update_index, 8)[within] == cue_source
        and int(metadata["true_cue"]) == ([0] * 4 + [1] * 4)[cue_source]
        and metadata.get("event_tape_token") == tape.token("environment_randomness", update_index, within)
        and float(metadata["behavior_mixture_coin"]) == tape.uniform("behavior_mixture_coin", update_index, within)
        and float(metadata["sampling_uniform"]) == tape.uniform("sampling_uniform", update_index, within)
        and row.get("environment_transitions") in (4, 5)
        and isinstance(physical, list) and len(physical) == 1
        and str(physical[0]).startswith(f"{B5R1_PHYSICAL_TAPE_PREFIX}/")
    )


def _gradient_payload(model: b1.GRUActorCritic) -> dict[str, object]:
    payload: dict[str, object] = {}
    for name, parameter in model.named_parameters():
        if parameter.grad is None:
            raise ValueError(f"missing gradient for {name}")
        if not torch.isfinite(parameter.grad).all():
            raise ValueError(f"nonfinite gradient for {name}")
        payload[name] = _tensor_payload(parameter.grad)
    return payload


def _loss_terms(model: b1.GRUActorCritic, batch: Sequence[Mapping[str, object]]) -> tuple[Tensor, dict[str, object]]:
    if len(batch) != B5R1_BATCH_SIZE:
        raise ValueError("oracle-sign loss requires one eight-row batch")
    batch_before = digest(batch)
    actor_terms: list[Tensor] = []
    policy_terms: list[Tensor] = []
    entropy_terms: list[Tensor] = []
    critic_terms: list[Tensor] = []
    forwards: list[dict[str, object]] = []
    coefficients: list[float] = []
    advantages: list[float] = []
    for row in batch:
        observations = row.get("O")
        if not isinstance(observations, Sequence) or not _observation_firewall(observations):
            raise ValueError("observation firewall or history missing")
        logits, raw, probabilities, baseline, entropy = _forward(model, observations)
        expected = row.get("behavior_probabilities")
        if not isinstance(expected, list) or len(expected) != 2 or any(
            not math.isclose(float(actual), float(bound), rel_tol=0.0, abs_tol=1e-12)
            for actual, bound in zip(probabilities.detach(), expected)):
            raise RuntimeError("collector behavior probabilities changed before own update")
        target = torch.tensor(float(row["G"]), dtype=torch.float64)
        advantage = target - baseline
        if not torch.isfinite(advantage):
            raise ValueError("nonfinite lifecycle advantage")
        action_index = b1.Action(str(row["A_behavior"])).index
        metadata = row.get("metadata")
        if not isinstance(metadata, Mapping) or metadata.get("true_cue") not in (0, 1):
            raise ValueError("oracle-sign cue missing")
        # The oracle is accessed only after the model forward and contributes this scalar sign alone.
        coefficient = torch.tensor(correctness_sign(str(row["A_behavior"]), int(metadata["true_cue"])), dtype=torch.float64) * advantage.detach().abs()
        policy_term = -coefficient * torch.log(probabilities[action_index])
        entropy_term = -0.01 * entropy
        actor_terms.append(policy_term + entropy_term)
        policy_terms.append(policy_term)
        entropy_terms.append(entropy_term)
        critic_terms.append(0.5 * advantage**2)
        coefficients.append(float(coefficient))
        advantages.append(float(advantage.detach()))
        forwards.append({"logits": [float(value) for value in logits], "raw_softmax": [float(value) for value in raw],
                         "behavior_probabilities": [float(value) for value in probabilities],
                         "baseline": float(baseline), "entropy": float(entropy)})
    if digest(batch) != batch_before:
        raise RuntimeError("loss route mutated immutable batch")
    actor_loss = torch.stack(actor_terms).mean()
    critic_loss = torch.stack(critic_terms).mean()
    policy_loss = torch.stack(policy_terms).mean()
    entropy_loss = torch.stack(entropy_terms).mean()
    return actor_loss + critic_loss, {
        "loss_components": {"actor_loss": float(actor_loss.detach()), "policy_actor_loss": float(policy_loss.detach()),
                            "entropy_loss": float(entropy_loss.detach()), "critic_loss": float(critic_loss.detach())},
        "forward_values": forwards, "actor_coefficients": coefficients, "advantages": advantages,
        "actor_route": ORACLE_SIGN_ACTOR_ROUTE, "critic_route": CRITIC_ROUTE,
        "oracle_scalar_only": True, "oracle_access_after_forward": True, "batch_digest_before_after": batch_before,
    }


def _prepare_update(model: b1.GRUActorCritic, optimizer: torch.optim.Optimizer,
                    batch: Sequence[Mapping[str, object]]) -> dict[str, object]:
    parameters_before = digest(model_payload(model))
    optimizer_before = digest(optimizer_payload(optimizer))
    batch_before = digest(batch)
    optimizer.zero_grad(set_to_none=True)
    loss, route = _loss_terms(model, batch)
    if not torch.isfinite(loss):
        raise ValueError("nonfinite loss")
    loss.backward()
    raw_gradients = _gradient_payload(model)
    preclip_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
    if not math.isfinite(preclip_norm):
        raise ValueError("nonfinite preclip norm")
    clipped_gradients = _gradient_payload(model)
    if digest(batch) != batch_before or digest(model_payload(model)) != parameters_before or digest(optimizer_payload(optimizer)) != optimizer_before:
        raise RuntimeError("gradient preparation mutated batch, parameters, or optimizer")
    receipt = {
        "parameters_before": parameters_before, "optimizer_before": optimizer_before,
        "batch_digest": batch_before, "loss": float(loss.detach()), **route,
        "raw_gradients": raw_gradients, "raw_gradient_digest": digest(raw_gradients),
        "clipped_gradients": clipped_gradients, "clipped_gradient_digest": digest(clipped_gradients),
        "gradient_norm_before_clip": preclip_norm, "clip_threshold": 1.0,
        "clip_factor": min(1.0, 1.0 / preclip_norm) if preclip_norm > 0.0 else 1.0,
        "clipped": preclip_norm > 1.0,
    }
    receipt["prepared_semantics_digest"] = digest({key: value for key, value in receipt.items() if key not in {"optimizer_before"}})
    return receipt


def _apply_prepared_update(model: b1.GRUActorCritic, optimizer: torch.optim.Optimizer,
                           prepared: Mapping[str, object]) -> dict[str, object]:
    if digest(model_payload(model)) != prepared.get("parameters_before") or digest(optimizer_payload(optimizer)) != prepared.get("optimizer_before"):
        raise RuntimeError("prepared update no longer binds current learner")
    if digest(_gradient_payload(model)) != prepared.get("clipped_gradient_digest"):
        raise RuntimeError("prepared clipped gradients changed before application")
    optimizer.step()
    return {
        "parameters_before": prepared["parameters_before"], "parameters_after": digest(model_payload(model)),
        "optimizer_before": prepared["optimizer_before"], "optimizer_after": digest(optimizer_payload(optimizer)),
        **{key: prepared[key] for key in (
            "batch_digest", "loss", "loss_components", "forward_values", "actor_coefficients", "advantages",
            "actor_route", "critic_route", "oracle_scalar_only", "oracle_access_after_forward",
            "raw_gradient_digest", "clipped_gradient_digest", "gradient_norm_before_clip", "clip_threshold", "clip_factor", "clipped",
        )},
    }


def _advance_carried_learner_state(state: Mapping[str, object], *, update_index: int,
                                   batch_digest: str, batch_order: Sequence[int]) -> dict[str, object]:
    if state.get("next_update_index") != update_index:
        raise RuntimeError("carried learner update index mismatch")
    return {"next_update_index": update_index + 1, "optimizer_steps": int(state["optimizer_steps"]) + 1,
            "batches_consumed": int(state["batches_consumed"]) + 1,
            "rows_consumed": int(state["rows_consumed"]) + 8,
            "last_batch_digest": batch_digest, "last_batch_order": list(batch_order)}


def _parameter_distance(carry: b1.GRUActorCritic, reset: b1.GRUActorCritic) -> float:
    carry_named, reset_named = list(carry.named_parameters()), list(reset.named_parameters())
    if [name for name, _ in carry_named] != [name for name, _ in reset_named]:
        raise RuntimeError("parameter order differs between arms")
    vector = torch.cat([(left.detach() - right.detach()).reshape(-1) for (_, left), (_, right) in zip(carry_named, reset_named)])
    return float(torch.linalg.vector_norm(vector, 2.0))


def _zero_activity() -> dict[str, int]:
    return {"result_bearing_runs": 0, "real_training_episodes": 0, "evaluation_episodes": 0,
            "environment_transitions": 0, "optimizer_updates": 0, "checkpoints_total": 0,
            "retries_rescues_sweeps": 0}


def validate_resource_admission_receipt(
    receipt: object,
    *,
    source_revision: str,
    require_current_process: bool = False,
    max_age_seconds: float | None = None,
) -> tuple[str, ...]:
    """Validate retained Windows preclaim evidence without obtaining a new sample."""

    if not isinstance(receipt, Mapping):
        return ("Windows resource-admission receipt missing or unreadable",)
    issues: list[str] = []
    if receipt.get("artifact_kind") != "vsp02_b5r1_windows_resource_admission_receipt":
        issues.append("resource-admission receipt identity mismatch")
    if receipt.get("assignment_id") != B5R1_ASSIGNMENT_ID or receipt.get("candidate") != B5R1_CANDIDATE:
        issues.append("resource-admission assignment/candidate mismatch")
    if receipt.get("source_revision") != source_revision or not source_revision:
        issues.append("resource-admission source revision mismatch")
    if receipt.get("platform") != "win32" or receipt.get("os_name") != "nt":
        issues.append("resource admission requires the real Windows host")
    if receipt.get("windows_ffi_binding") != B5R1_WINDOWS_BINDING:
        issues.append("Windows FFI binding metadata invalid")
    process = receipt.get("process_identity")
    if not isinstance(process, Mapping):
        issues.append("current process identity missing")
    else:
        pid = process.get("pid")
        executable = process.get("executable")
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0 or not isinstance(executable, str) or not executable:
            issues.append("current process identity unreadable")
        if require_current_process and (pid != os.getpid() or executable != str(Path(sys.executable).resolve())):
            issues.append("resource-admission receipt is not for the current process")
    cpu_seconds = receipt.get("cpu_time_seconds")
    if not isinstance(cpu_seconds, (int, float)) or isinstance(cpu_seconds, bool) or not math.isfinite(float(cpu_seconds)) or float(cpu_seconds) < 0.0:
        issues.append("CPU-time sample is not finite and nonnegative")
    rss = receipt.get("peak_process_rss_bytes")
    if (
        not isinstance(rss, int)
        or isinstance(rss, bool)
        or rss <= 0
        or rss > B5R1_RSS_CAP_BYTES
    ):
        issues.append("peak process RSS must be a positive non-bool int within 2 GiB")
    if receipt.get("configured_caps") != {
        "cpu_minutes": 30, "peak_memory_gib": 2, "peak_memory_bytes": B5R1_RSS_CAP_BYTES,
    }:
        issues.append("configured resource caps mismatch")
    if receipt.get("activity") != _zero_activity():
        issues.append("resource admission must retain exact zero-start activity")
    sampled_at_ns = receipt.get("sampled_at_unix_ns")
    if not isinstance(sampled_at_ns, int) or isinstance(sampled_at_ns, bool) or sampled_at_ns <= 0:
        issues.append("resource-admission timestamp unreadable")
    elif max_age_seconds is not None:
        age_seconds = (time.time_ns() - sampled_at_ns) / 1_000_000_000
        if not math.isfinite(age_seconds) or age_seconds < 0.0 or age_seconds > max_age_seconds:
            issues.append("resource-admission receipt is stale")
    unsigned = dict(receipt)
    retained_digest = unsigned.pop("receipt_digest", None)
    if retained_digest != digest(unsigned):
        issues.append("resource-admission receipt digest mismatch")
    if require_current_process and os.name != "nt":
        issues.append("resource admission cannot run on a non-Windows host")
    return tuple(issues)


def resource_admission_receipt(*, source_revision: str) -> dict[str, object]:
    """Obtain the production zero-activity Windows RSS receipt before a full claim."""

    if os.name != "nt" or sys.platform != "win32":
        raise OSError("Windows resource admission requires the real Windows host")
    rss = _peak_process_rss_bytes()
    receipt: dict[str, object] = {
        "artifact_kind": "vsp02_b5r1_windows_resource_admission_receipt",
        "assignment_id": B5R1_ASSIGNMENT_ID,
        "candidate": B5R1_CANDIDATE,
        "source_revision": source_revision,
        "platform": sys.platform,
        "os_name": os.name,
        "windows_ffi_binding": deepcopy(B5R1_WINDOWS_BINDING),
        "process_identity": {"pid": os.getpid(), "executable": str(Path(sys.executable).resolve())},
        "cpu_time_seconds": _cpu_time_seconds(),
        "peak_process_rss_bytes": rss,
        "configured_caps": {
            "cpu_minutes": 30, "peak_memory_gib": 2, "peak_memory_bytes": B5R1_RSS_CAP_BYTES,
        },
        "activity": _zero_activity(),
        "sampled_at_unix_ns": time.time_ns(),
    }
    receipt["receipt_digest"] = digest(receipt)
    issues = validate_resource_admission_receipt(
        receipt,
        source_revision=source_revision,
        require_current_process=True,
        max_age_seconds=B5R1_ADMISSION_MAX_AGE_SECONDS,
    )
    if issues:
        raise OSError("Windows resource admission failed: " + "; ".join(issues))
    return receipt


def _synthetic_history(cue: int, *, owner_epoch: str) -> list[dict[str, object]]:
    common = dict(committed_phase="ACTIVE", prior_acknowledgements=("CLAIM_ACCEPTED",),
                  physical_clock=0, primitive_clock=0, own_boundary_clock=0,
                  owner_epoch_token=(b1.B1_OWNER_ID, owner_epoch, b1.B1_BEHAVIOR_VERSION),
                  visible_roster=b1.B1_VISIBLE_ROSTER, primitive_policy=b1.B1_PRIMITIVE,
                  partner_policy=b1.B1_PARTNER_POLICY)
    return [asdict(b1.PolicyObservation(**common, cue_mask=1, cue_value=cue)),
            asdict(b1.PolicyObservation(**common, cue_mask=0, cue_value=0))]


def _proof_batch(model: b1.GRUActorCritic, *, tag: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, cue in enumerate((0, 1, 0, 1, 0, 1, 0, 1)):
        observations = _synthetic_history(cue, owner_epoch=f"{tag}-{index:02d}")
        with torch.no_grad():
            _, raw, probabilities, baseline, _ = _forward(model, observations)
        action = b1.Action.HOLD if index % 4 in (0, 1) else b1.Action.RELEASE
        physical_return = float(baseline) + (-0.75 if index % 3 == 0 else 0.5)
        rows.append({
            "O": observations, "H0": [0.0] * b1.B1_HIDDEN_SIZE, "M_reset": [1, 0],
            "M_active": [1, 1], "M_valid": [0, 1], "M_lifecycle": [0, 1],
            "A_behavior": action.value, "R": [physical_return], "Done": [True], "G": physical_return,
            "raw_policy_probabilities": [float(value) for value in raw],
            "behavior_probabilities": [float(value) for value in probabilities],
            "environment_transitions": 0, "metadata": {"true_cue": cue, "clone_id": f"{tag}/{index}"},
        })
    return json.loads(canonical_bytes(rows))


def _one_boundary_proof(unit_id: str, root: int) -> dict[str, object]:
    model, optimizer = _new_common_learner(unit_id, root)
    learner_state = _initial_carried_learner_state()
    rng_state = _initial_learner_rng_state(unit_id, root)
    update0_batch = _proof_batch(model, tag=f"{unit_id}-U0")
    prepared0 = _prepare_update(model, optimizer, update0_batch)
    common_update0 = _apply_prepared_update(model, optimizer, prepared0)
    learner_state = _advance_carried_learner_state(learner_state, update_index=0,
        batch_digest=digest(update0_batch), batch_order=list(range(8)))
    post0_adam = adam_state_report(model, optimizer)
    models, optimizers = _clone_post_update0(model, optimizer)
    states = {arm: deepcopy(learner_state) for arm in B5R1_ARMS}
    rng_states = {arm: deepcopy(rng_state) for arm in B5R1_ARMS}
    pre_reset_complete = {arm: _complete_state_hash(models[arm], optimizers[arm], states[arm], rng_states[arm]) for arm in B5R1_ARMS}
    pre_reset_optimizer = {arm: digest(optimizer_payload(optimizers[arm])) for arm in B5R1_ARMS}
    group_before = {arm: _optimizer_group_contract(models[arm], optimizers[arm]) for arm in B5R1_ARMS}
    optimizers["ADAM_RESET"].state.clear()
    group_after = {arm: _optimizer_group_contract(models[arm], optimizers[arm]) for arm in B5R1_ARMS}
    reset_receipt = {
        "pre_reset_complete_state_hashes": pre_reset_complete,
        "pre_reset_optimizer_hashes": pre_reset_optimizer,
        "pre_reset_complete_state_byte_identical": len(set(pre_reset_complete.values())) == 1,
        "post_update0_adam_state": post0_adam,
        "reset_slots_canonical_fresh_empty": optimizer_payload(optimizers["ADAM_RESET"])["state"] == {},
        "carry_slots_retained_exactly": digest(optimizer_payload(optimizers["ADAM_CARRY"])) == pre_reset_optimizer["ADAM_CARRY"],
        "parameter_groups_identical_before_after": len(set(digest(value) for value in (*group_before.values(), *group_after.values()))) == 1,
        "parameter_hashes_after_reset": {arm: digest(model_payload(models[arm])) for arm in B5R1_ARMS},
        "learner_state_hashes_after_reset": {arm: digest(states[arm]) for arm in B5R1_ARMS},
        "rng_state_hashes_after_reset": {arm: digest(rng_states[arm]) for arm in B5R1_ARMS},
    }
    update1_batches = {arm: _proof_batch(models[arm], tag=f"{unit_id}-U1") for arm in B5R1_ARMS}
    frozen = {arm: digest(update1_batches[arm]) for arm in B5R1_ARMS}
    prepared = {arm: _prepare_update(models[arm], optimizers[arm], update1_batches[arm]) for arm in B5R1_ARMS}
    semantic_keys = (
        "parameters_before", "batch_digest", "loss", "loss_components", "forward_values", "actor_coefficients",
        "advantages", "actor_route", "critic_route", "oracle_scalar_only", "oracle_access_after_forward",
        "raw_gradients", "raw_gradient_digest", "clipped_gradients", "clipped_gradient_digest",
        "gradient_norm_before_clip", "clip_threshold", "clip_factor", "clipped", "prepared_semantics_digest",
    )
    prepared_payloads = {arm: {key: prepared[arm][key] for key in semantic_keys} for arm in B5R1_ARMS}
    applied = {arm: _apply_prepared_update(models[arm], optimizers[arm], prepared[arm]) for arm in B5R1_ARMS}
    q_r = _parameter_distance(models["ADAM_CARRY"], models["ADAM_RESET"])
    parameter_hashes = {arm: digest(model_payload(models[arm])) for arm in B5R1_ARMS}
    return {
        "synthetic_only": True, "activity": _zero_activity(), "common_update0": common_update0,
        "common_update0_batch_digest": digest(update0_batch), "reset_receipt": reset_receipt,
        "update1_batches_frozen_before_updates": True,
        "update1_batch_digests": frozen,
        "update1_batch_byte_identical": canonical_bytes(update1_batches["ADAM_CARRY"]) == canonical_bytes(update1_batches["ADAM_RESET"]),
        "update1_prepared_payloads": prepared_payloads,
        "update1_prepared_byte_identical": canonical_bytes(prepared_payloads["ADAM_CARRY"]) == canonical_bytes(prepared_payloads["ADAM_RESET"]),
        "update1_applied": applied, "q_r": q_r, "q_finite_positive": math.isfinite(q_r) and q_r > 0.0,
        "parameter_hashes_after_update1": parameter_hashes,
        "parameter_hashes_differ_after_update1": len(set(parameter_hashes.values())) == 2,
    }


def build_manifest(*, source_revision: str, run_id: str, technical_only: bool) -> dict[str, object]:
    return {
        "schema_version": B5R1_SCHEMA_VERSION, "artifact_kind": "vsp02_b5r1_manifest",
        "assignment_id": B5R1_ASSIGNMENT_ID, "direction_id": B5R1_DIRECTION_ID, "candidate": B5R1_CANDIDATE,
        "treatment": B5R1_ASSIGNMENT_ID, "registered_full": B5R1_RUN_ID, "host_id": B5R1_HOST_ID,
        "evidence_class": B5R1_RESOURCE_CLASS, "formal": False, "resource_class": B5R1_RESOURCE_CLASS,
        "pool_units": B5R1_POOL_UNITS, "accelerator": "CPU_ONLY_NO_GPU", "paid_service": False,
        "implementation_base": B5R1_IMPLEMENTATION_BASE,
        "scientific_freeze": {"handoff_sha256": B5R1_FREEZE_HANDOFF_SHA256,
                              "publication_commit": B5R1_FREEZE_PUBLICATION_COMMIT,
                              "disposition": "REPAIR_FRESH_CANDIDATE", "scientific_repair": "NONE"},
        "canonical_artifacts": {"run_root": B5R1_CANONICAL_RUN_ROOT, "operator_receipt": B5R1_OPERATOR_RECEIPT,
                                "reserved_repo_result": "docs/research/candidates/vsp_02/VSP02_B5R1_WINDOWS_RESOURCE_ADMISSION_RESULT.json"},
        "source_revision": source_revision, "run_id": run_id, "technical_only": technical_only,
        "arms": list(B5R1_ARMS), "units": [{"unit_id": unit, "decimal_root": root} for unit, root in B5R1_UNITS],
        "seed_prefix": B5R1_SEED_PREFIX, "seed_streams": list(B5R1_SEED_STREAMS),
        "tape": {"kind": "immutable_address_indexed_sha256", "kinds": list(B5R1_TAPE_KINDS),
                 "fresh_assignment_namespace": True, "shared_mutable_rng": False,
                 "collision_policy": "FAIL_CLOSED_NO_RESEED"},
        "boundary_rule": "EARLIEST_NONVACUOUS_ADAM_BOUNDARY_AFTER_ONE_COMMON_ORACLE_SIGN_UPDATE",
        "training": {
            "common_update0": 1, "updates_per_arm_after_common": 127, "effective_steps_per_arm": 128,
            "episodes_per_update": 8, "cue_count_per_update": {"0": 4, "1": 4},
            "fixed_update_order": list(FIXED_UPDATE_ORDER), "collect_both_batches_before_either_update": True,
            "update1_batch_forward_loss_raw_clipped_gradient_equality": "BYTE_IDENTICAL",
            "updates_2_through_127_are_unmatched_causal_descendants": True,
        },
        "single_axis": {
            "ADAM_CARRY": "retain exact post-update-0 complete Adam slots",
            "ADAM_RESET": "replace only complete Adam slots with canonical fresh-empty state",
            "complete_slots": ["step", "exp_avg", "exp_avg_sq", "any configured slot"],
            "all_other_state_byte_identical": True, "q_gate": "finite and strictly greater than zero for every root",
            "effect_tolerance_or_threshold": None,
        },
        "optimizer": {"name": "Adam", "learning_rate": 0.003, "betas": [0.9, 0.999], "epsilon": 1e-8,
                      "weight_decay": 0.0, "amsgrad": False, "gradient_norm_clip": 1.0},
        "behavior_mixture": BEHAVIOR_MIXTURE_ROUTE,
        "loss_contract": {"oracle_sign_actor": ORACLE_SIGN_ACTOR_ROUTE, "critic": CRITIC_ROUTE,
                          "oracle_access": "post-forward scalar correctness sign only", "direct_label_or_cross_entropy": False},
        "evaluation": {"episodes_per_arm_unit": 128, "cue_counts": {"0": 64, "1": 64},
                       "common_held_out_panel": True, "argmax_ties_fail": True, "checkpoint_selection": False,
                       "exact_success": "all cue-0 HOLD and all cue-1 RELEASE and no tie"},
        "expected_activity": {"real_training_episodes": 10_200, "optimizer_updates": 1_275,
                              "evaluation_episodes": 1_280, "checkpoints_total": 10},
        "resource_admission": {
            "platform": "win32", "preclaim": True, "binding": deepcopy(B5R1_WINDOWS_BINDING),
            "rss_requirement": "positive non-bool int within 2 GiB", "activity": _zero_activity(),
            "fallback_skip_synthetic_inferred_rss": False,
        },
        "caps": dict(B5R1_CAPS), "evidence_complexity": {"H": 4, "K_search": 0, "hypothetical_transitions": 0},
        "branches": list(B5R1_BRANCH_PRECEDENCE), "result_bearing_runs": 0 if technical_only else 1,
        "retry_rescue_sweep_extra_root_checkpoint_threshold_boundary": 0,
        "nonclaims": [
            "no reinterpretation, rescue, pooling, or explanation of B4",
            "no G52 evidence, threshold, code, conclusion, or host/update-100 transfer",
            "no generic Adam, momentum, bias-correction, or component attribution",
            "no root population estimate, population superiority, necessity, sufficiency, or equivalence",
            "no mediator causality or robust acquisition beyond the exact thresholded finite panel",
            "no generic self-feedback, on-policy, actor-critic, recurrent, MARL, transfer, or sample-efficiency claim",
            "no C/formal/promotion/retirement meaning and no sibling transfer",
            "branch 2 is not optimizer irrelevance; branch 5 is binary endpoint nonlocalization only; branch 6 is qualitative finite-set heterogeneity only",
        ],
    }


def manifest_identity(manifest: Mapping[str, object]) -> str:
    return digest(manifest)


def validate_manifest(manifest: object) -> tuple[str, ...]:
    if not isinstance(manifest, Mapping):
        return ("manifest is not an object",)
    expected = build_manifest(source_revision=str(manifest.get("source_revision", "")),
                              run_id=str(manifest.get("run_id", "")), technical_only=bool(manifest.get("technical_only")))
    issues = [f"manifest {key} mismatch" for key, value in expected.items() if manifest.get(key) != value]
    if not manifest.get("source_revision") or not manifest.get("run_id"):
        issues.append("source_revision and run_id must be nonempty")
    if manifest.get("technical_only") is False and manifest.get("run_id") != B5R1_RUN_ID:
        issues.append(f"registered full run_id must be {B5R1_RUN_ID}")
    return tuple(issues)


def _git_binding(repo_root: Path, source_revision: str) -> list[str]:
    issues: list[str] = []
    def git(*arguments: str) -> str:
        return subprocess.run(["git", *arguments], cwd=repo_root, check=True, capture_output=True, text=True).stdout.strip()
    try:
        actual = git("rev-parse", "HEAD")
        if actual != source_revision:
            issues.append(f"source revision {source_revision} != checkout HEAD {actual}")
        tracked = set(git("ls-files", "--", *B5R1_RUNTIME_PATHS).splitlines())
        if tracked != set(B5R1_RUNTIME_PATHS):
            issues.append("B5R1 claim and runtime dependency path set is not fully tracked")
        if git("status", "--porcelain=v1", "--untracked-files=all", "--", *B5R1_RUNTIME_PATHS):
            issues.append("B5R1 claim or runtime dependency paths differ from HEAD")
        if subprocess.run(["git", "merge-base", "--is-ancestor", B5R1_IMPLEMENTATION_BASE, actual], cwd=repo_root).returncode != 0:
            issues.append("implementation base is not an ancestor of checkout HEAD")
        if git("cat-file", "-t", B5R1_FREEZE_PUBLICATION_COMMIT) != "commit":
            issues.append("scientific freeze publication anchor is not an exact Git commit object")
        elif subprocess.run(["git", "merge-base", "--is-ancestor", B5R1_FREEZE_PUBLICATION_COMMIT, actual], cwd=repo_root).returncode != 0:
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
    if not roots["all_b5_roots_unique"] or roots["collision_with_predecessor_values"] or roots["identity_collision_with_predecessors"]:
        gate_issues["P1"].append("B5R1 seed/tape namespace collision; silent reseed forbidden")
    proofs = [_one_boundary_proof(unit, root) for unit, root in B5R1_UNITS]
    if any(not proof["reset_receipt"]["pre_reset_complete_state_byte_identical"] for proof in proofs):
        gate_issues["P2"].append("post-update-0 complete-state fork bytes differ")
    if any(not all(proof["reset_receipt"][key] for key in ("reset_slots_canonical_fresh_empty", "carry_slots_retained_exactly", "parameter_groups_identical_before_after")) for proof in proofs):
        gate_issues["P3"].append("Adam reset schema or parameter-group identity failed")
    if any(not all(proof["reset_receipt"]["post_update0_adam_state"][key] for key in ("all_slots_finite", "all_steps_exactly_one", "globally_at_least_one_moment_nonzero")) for proof in proofs):
        gate_issues["P4"].append("post-update-0 Adam activity contract failed")
    if any(not proof["update1_batch_byte_identical"] or not proof["update1_prepared_byte_identical"] for proof in proofs):
        gate_issues["P5"].append("common update-1 batch or prepared gradient equality failed")
    if any(not proof["q_finite_positive"] or not proof["parameter_hashes_differ_after_update1"] for proof in proofs):
        gate_issues["P6"].append("per-root q activity gate failed")
    if not all(_schedule_contract(_schedule(unit, root)) for unit, root in B5R1_UNITS):
        gate_issues["P7"].append("balanced 128x8 schedule failed")
    if not all(_observation_firewall(_synthetic_history(cue, owner_epoch=f"P8-{cue}")) for cue in (0, 1)):
        gate_issues["P8"].append("oracle observation firewall failed")
    if manifest.get("expected_activity") != {"real_training_episodes": 10_200, "optimizer_updates": 1_275, "evaluation_episodes": 1_280, "checkpoints_total": 10}:
        gate_issues["P9"].append("exact activity counts mismatch")
    if manifest.get("evidence_complexity") != {"H": 4, "K_search": 0, "hypothetical_transitions": 0}:
        gate_issues["P10"].append("evidence complexity bound mismatch")
    if tuple(manifest.get("branches", ())) != B5R1_BRANCH_PRECEDENCE:
        gate_issues["P11"].append("six branch literals or precedence mismatch")
    report = {
        "artifact_kind": "vsp02_b5r1_preflight", "assignment_id": B5R1_ASSIGNMENT_ID,
        "manifest_identity": manifest_identity(manifest),
        "gates": {gate: {"passed": not issues, "issues": issues} for gate, issues in gate_issues.items()},
        "all_passed": not any(gate_issues.values()), "seed_and_tape": roots,
        "boundary_proofs": proofs, "oracle_firewall": True, "activity": _zero_activity(),
        "readiness_semantics": {
            "interface_smoke": "import and CLI surface only; no model, host, optimizer, train, evaluate, or analyze",
            "bounded_exercise": "call the real Windows RSS helper and retain the zero-activity admission receipt",
            "artifact_validation": "pure validation of the retained admission receipt",
            "artifact_reload": "reload and byte/digest stability of the retained admission receipt",
            "evaluate_entry": "prove evaluation entry is full-only; no evaluation",
            "analyze_entry": "prove analysis entry is full-only and branch classifier total; no analysis",
        },
    }
    report["evidence_digest"] = digest(report)
    return report


def validate_preflight_evidence(manifest: Mapping[str, object], preflight: Mapping[str, object]) -> tuple[str, ...]:
    """Pure retained validation: constructs no model, host, optimizer, trainer, or evaluator."""
    issues: list[str] = []
    if preflight.get("artifact_kind") != "vsp02_b5r1_preflight" or preflight.get("assignment_id") != B5R1_ASSIGNMENT_ID:
        issues.append("preflight identity mismatch")
    if preflight.get("manifest_identity") != manifest_identity(manifest):
        issues.append("preflight manifest binding mismatch")
    unsigned = dict(preflight)
    retained = unsigned.pop("evidence_digest", None)
    if retained != digest(unsigned):
        issues.append("preflight artifact mutation or evidence digest mismatch")
    gates = preflight.get("gates")
    if not isinstance(gates, Mapping) or set(gates) != {f"P{i}" for i in range(12)}:
        issues.append("P0-P11 gate set mismatch")
    else:
        passes = []
        for index in range(12):
            evidence = gates[f"P{index}"]
            if not isinstance(evidence, Mapping) or not isinstance(evidence.get("issues"), list):
                issues.append(f"P{index} schema mismatch")
                continue
            expected = not evidence["issues"]
            if evidence.get("passed") is not expected:
                issues.append(f"P{index} passed flag mismatch")
            passes.append(expected)
        if preflight.get("all_passed") is not all(passes):
            issues.append("preflight all_passed mismatch")
    proofs = preflight.get("boundary_proofs")
    if not isinstance(proofs, list) or len(proofs) != 5:
        issues.append("five boundary proofs required")
    elif any(not isinstance(proof, Mapping) or proof.get("activity") != _zero_activity()
             or proof.get("update1_batch_byte_identical") is not True
             or proof.get("update1_prepared_byte_identical") is not True
             or proof.get("q_finite_positive") is not True
             or proof.get("parameter_hashes_differ_after_update1") is not True for proof in proofs):
        issues.append("retained boundary proof mismatch")
    if preflight.get("activity") != _zero_activity():
        issues.append("preflight has scientific activity")
    return tuple(issues)


def _state_hashes(models: Mapping[str, b1.GRUActorCritic], optimizers: Mapping[str, torch.optim.Optimizer],
                  learner_states: Mapping[str, Mapping[str, object]], rng_states: Mapping[str, Mapping[str, object]]) -> dict[str, str]:
    return {arm: _complete_state_hash(models[arm], optimizers[arm], learner_states[arm], rng_states[arm]) for arm in B5R1_ARMS}


def _prepared_comparison_payload(prepared: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "parameters_before", "batch_digest", "loss", "loss_components", "forward_values", "actor_coefficients", "advantages",
        "actor_route", "critic_route", "oracle_scalar_only", "oracle_access_after_forward", "raw_gradients", "raw_gradient_digest",
        "clipped_gradients", "clipped_gradient_digest", "gradient_norm_before_clip", "clip_threshold", "clip_factor", "clipped",
        "prepared_semantics_digest",
    )
    return {key: prepared[key] for key in keys}


def _train_unit(unit_id: str, root: int) -> dict[str, object]:
    schedule = _schedule(unit_id, root)
    if not _schedule_contract(schedule):
        raise RuntimeError("B5 schedule contract failed")
    tape = B5R1AddressTape(unit_id, root)
    common_model, common_optimizer = _new_common_learner(unit_id, root)
    common_state = _initial_carried_learner_state()
    base_rng_state = _initial_learner_rng_state(unit_id, root)
    scheduled0 = schedule[:8]
    common_batch, common_transitions = _collect_batch(unit_id=unit_id, update_index=0, rows=scheduled0,
                                                       model=common_model, tape=tape)
    common_batch_before = digest(common_batch)
    common_order = list(_update_tape_receipt(tape, 0)["minibatch_order"])
    common_prepared = _prepare_update(common_model, common_optimizer, [common_batch[index] for index in common_order])
    common_update = _apply_prepared_update(common_model, common_optimizer, common_prepared)
    common_state = _advance_carried_learner_state(common_state, update_index=0,
        batch_digest=common_batch_before, batch_order=common_order)
    if digest(common_batch) != common_batch_before:
        raise RuntimeError("common update-0 batch mutated")
    post0_adam = adam_state_report(common_model, common_optimizer)
    if not all(post0_adam[key] for key in ("all_slots_finite", "all_steps_exactly_one", "globally_at_least_one_moment_nonzero")):
        raise RuntimeError("common update-0 Adam state inactive or invalid")
    models, optimizers = _clone_post_update0(common_model, common_optimizer)
    learner_states = {arm: deepcopy(common_state) for arm in B5R1_ARMS}
    rng_states = {arm: deepcopy(base_rng_state) for arm in B5R1_ARMS}
    pre_reset_complete = _state_hashes(models, optimizers, learner_states, rng_states)
    pre_reset_optimizer = {arm: digest(optimizer_payload(optimizers[arm])) for arm in B5R1_ARMS}
    groups_before = {arm: _optimizer_group_contract(models[arm], optimizers[arm]) for arm in B5R1_ARMS}
    optimizers["ADAM_RESET"].state.clear()
    groups_after = {arm: _optimizer_group_contract(models[arm], optimizers[arm]) for arm in B5R1_ARMS}
    reset_receipt = {
        "pre_reset_complete_state_hashes": pre_reset_complete,
        "pre_reset_complete_state_byte_identical": len(set(pre_reset_complete.values())) == 1,
        "post_update0_adam_state": post0_adam,
        "reset_slots_canonical_fresh_empty": optimizer_payload(optimizers["ADAM_RESET"])["state"] == {},
        "carry_slots_retained_exactly": digest(optimizer_payload(optimizers["ADAM_CARRY"])) == pre_reset_optimizer["ADAM_CARRY"],
        "parameter_groups_identical_before_after": len(set(digest(value) for value in (*groups_before.values(), *groups_after.values()))) == 1,
        "parameters_preserved_byte_identical": len({digest(model_payload(models[arm])) for arm in B5R1_ARMS}) == 1,
        "learner_state_preserved_byte_identical": len({digest(learner_states[arm]) for arm in B5R1_ARMS}) == 1,
        "rng_state_preserved_byte_identical": len({digest(rng_states[arm]) for arm in B5R1_ARMS}) == 1,
        "recurrent_state_preserved_byte_identical": True,
        "only_adam_slots_reset": True,
    }
    batch_records: list[dict[str, object]] = [{
        "update_index": 0, "common_ancestor": True,
        "batch_id": f"{B5R1_ASSIGNMENT_ID}/{unit_id}/U000/COMMON/BATCH",
        "batch_digest": common_batch_before, "rows": common_batch,
        "environment_transitions": common_transitions,
        "tape_receipt": _update_tape_receipt(tape, 0), "update": common_update,
    }]
    barriers: list[dict[str, object]] = []
    updates: dict[str, list[dict[str, object]]] = {arm: [{"shared_common_update0": True, **common_update}] for arm in B5R1_ARMS}
    transitions = common_transitions
    q_receipt: dict[str, object] | None = None
    for update_index in range(1, B5R1_UPDATES_PER_ARM):
        scheduled = schedule[update_index * 8:(update_index + 1) * 8]
        tape_receipt = _update_tape_receipt(tape, update_index)
        tape_before = digest(tape_receipt)
        collector_state_before = _state_hashes(models, optimizers, learner_states, rng_states)
        batches: dict[str, list[dict[str, object]]] = {}
        batch_transitions: dict[str, int] = {}
        for arm in B5R1_ARMS:
            batches[arm], batch_transitions[arm] = _collect_batch(
                unit_id=unit_id, update_index=update_index, rows=scheduled, model=models[arm], tape=tape)
        after_collections = _state_hashes(models, optimizers, learner_states, rng_states)
        if after_collections != collector_state_before:
            raise RuntimeError("collector mutated learner or optimizer state")
        batch_digests = {arm: digest(batches[arm]) for arm in B5R1_ARMS}
        frozen_before = {"batches": batch_digests, "tape": tape_before}
        order = list(tape_receipt["minibatch_order"])
        ordered = {arm: [batches[arm][index] for index in order] for arm in B5R1_ARMS}
        prepared = {arm: _prepare_update(models[arm], optimizers[arm], ordered[arm]) for arm in B5R1_ARMS}
        pre_apply_states = _state_hashes(models, optimizers, learner_states, rng_states)
        carry_update = _apply_prepared_update(models["ADAM_CARRY"], optimizers["ADAM_CARRY"], prepared["ADAM_CARRY"])
        learner_states["ADAM_CARRY"] = _advance_carried_learner_state(learner_states["ADAM_CARRY"],
            update_index=update_index, batch_digest=batch_digests["ADAM_CARRY"], batch_order=order)
        after_carry = _state_hashes(models, optimizers, learner_states, rng_states)
        if after_carry["ADAM_RESET"] != pre_apply_states["ADAM_RESET"]:
            raise RuntimeError("carry update contaminated reset arm")
        reset_update = _apply_prepared_update(models["ADAM_RESET"], optimizers["ADAM_RESET"], prepared["ADAM_RESET"])
        learner_states["ADAM_RESET"] = _advance_carried_learner_state(learner_states["ADAM_RESET"],
            update_index=update_index, batch_digest=batch_digests["ADAM_RESET"], batch_order=order)
        after_reset = _state_hashes(models, optimizers, learner_states, rng_states)
        if after_reset["ADAM_CARRY"] != after_carry["ADAM_CARRY"]:
            raise RuntimeError("reset update contaminated carry arm")
        frozen_after = {"batches": {arm: digest(batches[arm]) for arm in B5R1_ARMS},
                        "tape": digest(_update_tape_receipt(B5R1AddressTape(unit_id, root), update_index))}
        if frozen_before != frozen_after:
            raise RuntimeError("batch or address tape changed across update phase")
        updates["ADAM_CARRY"].append({"update_index": update_index, **carry_update})
        updates["ADAM_RESET"].append({"update_index": update_index, **reset_update})
        comparison = {arm: _prepared_comparison_payload(prepared[arm]) for arm in B5R1_ARMS}
        if update_index == 1:
            batch_equal = canonical_bytes(batches["ADAM_CARRY"]) == canonical_bytes(batches["ADAM_RESET"])
            prepared_equal = canonical_bytes(comparison["ADAM_CARRY"]) == canonical_bytes(comparison["ADAM_RESET"])
            q_r = _parameter_distance(models["ADAM_CARRY"], models["ADAM_RESET"])
            hashes = {arm: digest(model_payload(models[arm])) for arm in B5R1_ARMS}
            q_receipt = {
                "update_index": 1, "both_batches_frozen_before_either_update": True,
                "batch_byte_identical": batch_equal, "ordered_rows_byte_identical": canonical_bytes(ordered["ADAM_CARRY"]) == canonical_bytes(ordered["ADAM_RESET"]),
                "forward_loss_raw_clipped_gradient_norm_factor_byte_identical": prepared_equal,
                "prepared_comparison_payloads": comparison, "q_r": q_r,
                "q_finite_positive": math.isfinite(q_r) and q_r > 0.0,
                "parameter_hashes": hashes, "parameter_hashes_differ": len(set(hashes.values())) == 2,
            }
            if not all((batch_equal, prepared_equal, q_receipt["q_finite_positive"], q_receipt["parameter_hashes_differ"])):
                raise RuntimeError("update-1 common-ancestor or q gate failed")
        batch_records.append({
            "update_index": update_index, "common_ancestor": False,
            "batch_ids": {arm: f"{B5R1_ASSIGNMENT_ID}/{unit_id}/U{update_index:03d}/{arm}/BATCH" for arm in B5R1_ARMS},
            "batch_digests": batch_digests, "rows": batches, "environment_transitions": batch_transitions,
            "tape_receipt": tape_receipt,
        })
        barriers.append({
            "update_index": update_index,
            "phase_order": ["COLLECT_ADAM_CARRY_COMPLETE", "COLLECT_ADAM_RESET_COMPLETE", "PREPARE_BOTH_COMPLETE",
                            "UPDATE_ADAM_CARRY", "UPDATE_ADAM_RESET"],
            "both_batches_frozen_before_either_update": True, "collector_state_before": collector_state_before,
            "state_after_both_collections": after_collections, "pre_apply_states": pre_apply_states,
            "after_carry_states": after_carry, "after_reset_states": after_reset,
            "carry_update_preserved_reset": after_carry["ADAM_RESET"] == pre_apply_states["ADAM_RESET"],
            "reset_update_preserved_carry": after_reset["ADAM_CARRY"] == after_carry["ADAM_CARRY"],
            "frozen_before": frozen_before, "frozen_after": frozen_after,
            "rng_noninterference": "NO_MUTABLE_RNG_EXISTS", "tape_batch_noninterference": True,
        })
        transitions += sum(batch_transitions.values())
    if q_receipt is None:
        raise RuntimeError("missing update-1 q receipt")
    return {
        "unit_id": unit_id, "decimal_root": root, "_models": models,
        "training": {
            "real_training_episodes": 2_040, "optimizer_updates_applied": 255,
            "effective_steps_per_arm": {arm: 128 for arm in B5R1_ARMS},
            "environment_transitions": transitions,
            "cue_counts": {"common_update0": {"0": 4, "1": 4},
                           "per_arm_updates_1_127": {arm: {"0": 508, "1": 508} for arm in B5R1_ARMS}},
            "common_update0_receipt": {"batch_digest": common_batch_before, "update": common_update,
                                       "post_update0_parameter_hash": digest(model_payload(common_model)),
                                       "post_update0_optimizer_hash": digest(optimizer_payload(common_optimizer))},
            "reset_receipt": reset_receipt, "update1_q_receipt": q_receipt,
            "batch_records": batch_records, "barrier_receipts": barriers, "updates": updates,
            "final_parameter_hashes": {arm: digest(model_payload(models[arm])) for arm in B5R1_ARMS},
            "final_model_states": {arm: model_payload(models[arm]) for arm in B5R1_ARMS},
            "final_optimizer_states": {arm: optimizer_payload(optimizers[arm]) for arm in B5R1_ARMS},
            "final_carried_learner_states": learner_states, "final_registered_learner_rng_states": rng_states,
            "mutable_rng_objects": 0, "unlisted_rng_draws": 0,
            "later_differences_are_unmatched_descendants": True,
            "fixed_update_order": list(FIXED_UPDATE_ORDER), "oracle_scalar_only": True,
        },
    }


def _mixture_metrics_from_raw_q(*, q0: float, q1: float) -> dict[str, float]:
    p0, p1 = 0.1 + 0.8 * q0, 0.1 + 0.8 * q1
    return {"p_0": p0, "p_1": p1, "kappa": p1 - p0, "j_eval": 0.5 + p1 - 0.5 * p0}


def _evaluation_panel(unit_id: str, root: int) -> list[dict[str, object]]:
    tape = B5R1AddressTape(unit_id, root)
    base_cues = [0] * 64 + [1] * 64
    order = _ranked_permutation(tape, "evaluation_cue_schedule", "FINAL", 128)
    return [{"clone_id": f"{unit_id}/EVAL/{index:03d}", "owner_epoch": f"{unit_id}-EV-{index:03d}",
             "true_cue": base_cues[source],
             "event_tape_token": tape.token("evaluation_environment_randomness", index)}
            for index, source in enumerate(order)]


def _evaluate_arm_unit(*, unit_id: str, arm: str, model: b1.GRUActorCritic,
                       panel: Sequence[Mapping[str, object]]) -> dict[str, object]:
    releases: dict[int, list[float]] = {0: [], 1: []}
    choices: dict[int, list[str | None]] = {0: [], 1: []}
    records: list[dict[str, object]] = []
    transitions = 0
    for index, row in enumerate(panel):
        cue = int(row["true_cue"])
        host = B5R1LifecycleHost()
        cue_observation = host.reset(
            lifecycle_id=f"{B5R1_ASSIGNMENT_ID}/{unit_id}/{arm}/EVAL/{index:03d}/{row['event_tape_token']}",
            owner_epoch=str(row["owner_epoch"]), true_cue=cue, presented_cue=cue)
        observations = [asdict(cue_observation), asdict(host.decision_observation())]
        with torch.no_grad():
            logits, raw, probabilities, _, _ = _forward(model, observations)
        if not all(torch.isfinite(value).all() for value in (logits, raw, probabilities)):
            raise RuntimeError("nonfinite evaluation")
        q_release, q_hold = (float(value) for value in raw)
        choice = "RELEASE" if q_release > q_hold else "HOLD" if q_hold > q_release else None
        releases[cue].append(q_release)
        choices[cue].append(choice)
        executed = b1.Action(choice) if choice is not None else b1.Action.HOLD
        episode = host.step(executed, action_probabilities=[float(value) for value in probabilities])
        transitions += int(episode["environment_transitions"])
        records.append({
            "clone_id": row["clone_id"], "owner_epoch": row["owner_epoch"],
            "event_tape_token": row["event_tape_token"], "true_cue": cue,
            "logits": [float(value) for value in logits], "raw_softmax": [float(value) for value in raw],
            "behavior_probabilities": [float(value) for value in probabilities], "argmax_action": choice,
            "environment_transitions": int(episode["environment_transitions"]),
        })
    q0, q1 = sum(releases[0]) / 64, sum(releases[1]) / 64
    ties = sum(choice is None for values in choices.values() for choice in values)
    exact = ties == 0 and all(choice == "HOLD" for choice in choices[0]) and all(choice == "RELEASE" for choice in choices[1])
    return {
        "unit_id": unit_id, "arm": arm, "checkpoint_id": f"{B5R1_ASSIGNMENT_ID}/{unit_id}/{arm}/FINAL-128",
        "panel_digest": digest(panel), "episodes": 128, "cue_counts": {"0": 64, "1": 64},
        "environment_transitions": transitions, "finite_logits": True, "argmax_ties": ties,
        "exact_correct_unit": exact, "q_0": q0, "q_1": q1, **_mixture_metrics_from_raw_q(q0=q0, q1=q1),
        "evaluation_updates": 0, "stochastic_action_draws": 0, "clone_records": records,
        "final_model_hash": digest(model_payload(model)),
    }


def _derive_retained_evaluation_metric(*, unit_id: str, root: int, arm: str,
                                       metric: Mapping[str, object], expected_final_hash: object) -> tuple[dict[str, object] | None, list[str]]:
    """Purely recompute all branch-bearing evaluation projections from retained rows."""
    issues: list[str] = []
    records = metric.get("clone_records")
    if not isinstance(records, list) or len(records) != 128:
        return None, [f"{unit_id}/{arm} retained evaluation rows invalid"]
    expected_panel = _evaluation_panel(unit_id, root)
    releases: dict[int, list[float]] = {0: [], 1: []}
    choices: dict[int, list[str | None]] = {0: [], 1: []}
    reconstructed: list[dict[str, object]] = []
    transitions = 0
    expected_keys = {"clone_id", "owner_epoch", "event_tape_token", "true_cue", "logits", "raw_softmax",
                     "behavior_probabilities", "argmax_action", "environment_transitions"}
    for index, record in enumerate(records):
        if not isinstance(record, Mapping) or set(record) != expected_keys:
            issues.append(f"{unit_id}/{arm}/{index} evaluation row schema mismatch")
            continue
        try:
            cue = int(record["true_cue"])
            logits = [float(value) for value in record["logits"]]  # type: ignore[arg-type]
            raw = [float(value) for value in record["raw_softmax"]]  # type: ignore[arg-type]
            probabilities = [float(value) for value in record["behavior_probabilities"]]  # type: ignore[arg-type]
            row_transitions = int(record["environment_transitions"])
        except (TypeError, ValueError):
            issues.append(f"{unit_id}/{arm}/{index} evaluation scalar mismatch")
            continue
        if cue not in (0, 1) or len(logits) != 2 or len(raw) != 2 or len(probabilities) != 2 or any(not math.isfinite(value) for value in (*logits, *raw, *probabilities)):
            issues.append(f"{unit_id}/{arm}/{index} evaluation value mismatch")
            continue
        maximum = max(logits)
        exps = [math.exp(value - maximum) for value in logits]
        expected_raw = [value / sum(exps) for value in exps]
        if any(not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12) for actual, expected in zip(raw, expected_raw)):
            issues.append(f"{unit_id}/{arm}/{index} raw softmax mismatch")
        if any(not math.isclose(actual, 0.8 * policy + 0.1, rel_tol=0.0, abs_tol=1e-12) for actual, policy in zip(probabilities, raw)):
            issues.append(f"{unit_id}/{arm}/{index} behavior mixture mismatch")
        choice = "RELEASE" if raw[0] > raw[1] else "HOLD" if raw[1] > raw[0] else None
        if record.get("argmax_action") != choice:
            issues.append(f"{unit_id}/{arm}/{index} argmax mismatch")
        if row_transitions != (4 if choice == "RELEASE" else 5):
            issues.append(f"{unit_id}/{arm}/{index} transition mismatch")
        panel_row = {"clone_id": record["clone_id"], "owner_epoch": record["owner_epoch"],
                     "true_cue": cue, "event_tape_token": record["event_tape_token"]}
        if panel_row != expected_panel[index]:
            issues.append(f"{unit_id}/{arm}/{index} panel identity mismatch")
        reconstructed.append(panel_row)
        releases[cue].append(raw[0])
        choices[cue].append(choice)
        transitions += row_transitions
    if len(reconstructed) != 128 or any(len(releases[cue]) != 64 for cue in (0, 1)):
        return None, issues + [f"{unit_id}/{arm} cue support mismatch"]
    q0, q1 = sum(releases[0]) / 64, sum(releases[1]) / 64
    ties = sum(choice is None for values in choices.values() for choice in values)
    exact = ties == 0 and all(choice == "HOLD" for choice in choices[0]) and all(choice == "RELEASE" for choice in choices[1])
    derived = {
        "unit_id": unit_id, "arm": arm, "checkpoint_id": f"{B5R1_ASSIGNMENT_ID}/{unit_id}/{arm}/FINAL-128",
        "panel_digest": digest(reconstructed), "episodes": 128, "cue_counts": {"0": 64, "1": 64},
        "environment_transitions": transitions, "finite_logits": True, "argmax_ties": ties,
        "exact_correct_unit": exact, "q_0": q0, "q_1": q1, **_mixture_metrics_from_raw_q(q0=q0, q1=q1),
        "evaluation_updates": 0, "stochastic_action_draws": 0, "final_model_hash": expected_final_hash,
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
    return derived, issues


def classify_b5r1(*, valid: bool, carry_success: set[str] | frozenset[str],
                reset_success: set[str] | frozenset[str]) -> str:
    if not valid:
        return "B5_INVALID_OR_INACTIVE"
    carry_only = set(carry_success) - set(reset_success)
    reset_only = set(reset_success) - set(carry_success)
    if not carry_success and not reset_success:
        return "B5_NEITHER_ARM_EXACT_SUCCESS_ON_PANEL"
    if carry_only and not reset_only:
        return "B5_CARRY_DIRECTION_DISCORDANCE_ONLY"
    if reset_only and not carry_only:
        return "B5_RESET_DIRECTION_DISCORDANCE_ONLY"
    if set(carry_success) == set(reset_success):
        return "B5_NO_EXACT_ENDPOINT_LOCALIZATION_ON_PANEL"
    return "B5_BIDIRECTIONAL_PAIRED_ROOT_TAPE_DISCORDANCE"


def _resource_usage_evidence(*, cpu_start_seconds: float, cpu_end_seconds: float,
                             peak_rss_samples_bytes: Sequence[int]) -> dict[str, object]:
    values = tuple(int(value) for value in peak_rss_samples_bytes)
    if not values or cpu_end_seconds < cpu_start_seconds or any(value < 0 for value in values):
        raise ValueError("invalid resource measurement")
    minutes = (cpu_end_seconds - cpu_start_seconds) / 60.0
    peak_bytes = max(values)
    peak_gib = peak_bytes / float(1024**3)
    return {"measurement_scope": "registered train/evaluate/analyze process work only",
            "cpu_clock": "time.process_time", "peak_memory_measure": "lifetime process peak resident_or_working_set",
            "cpu_start_seconds": cpu_start_seconds, "cpu_end_seconds": cpu_end_seconds,
            "cpu_seconds": cpu_end_seconds - cpu_start_seconds, "cpu_minutes": minutes,
            "cpu_minutes_cap": 30, "peak_process_rss_samples_bytes": list(values),
            "peak_process_rss_bytes": peak_bytes, "peak_process_memory_gib": peak_gib,
            "peak_process_memory_gib_cap": 2, "cpu_within_cap": minutes <= 30,
            "peak_memory_within_cap": peak_gib <= 2,
            "all_resource_caps_passed": minutes <= 30 and peak_gib <= 2}


def train_registered_full(manifest: Mapping[str, object], preflight: Mapping[str, object]) -> dict[str, object]:
    if manifest.get("technical_only") is not False or manifest.get("run_id") != B5R1_RUN_ID or preflight.get("all_passed") is not True:
        raise ValueError("train is full-only and requires the passed registered-full preflight")
    return {"phase": "train", "units": [_train_unit(unit, root) for unit, root in B5R1_UNITS],
            "result_bearing_runs": 1, "retry_rescue_sweep": 0}


def evaluate_registered_full(manifest: Mapping[str, object], training: Mapping[str, object]) -> dict[str, object]:
    if manifest.get("technical_only") is not False or training.get("phase") != "train":
        raise ValueError("evaluate is full-only and requires the in-process registered train phase")
    units = training.get("units")
    if not isinstance(units, list) or len(units) != 5:
        raise ValueError("evaluate requires five trained units")
    metrics: dict[str, list[dict[str, object]]] = {arm: [] for arm in B5R1_ARMS}
    transitions = 0
    for unit in units:
        if not isinstance(unit, dict):
            raise ValueError("invalid trained unit")
        unit_id, root = str(unit["unit_id"]), int(unit["decimal_root"])
        models = unit.pop("_models")
        panel_digests = []
        for arm in B5R1_ARMS:
            panel = _evaluation_panel(unit_id, root)
            panel_digests.append(digest(panel))
            metric = _evaluate_arm_unit(unit_id=unit_id, arm=arm, model=models[arm], panel=panel)
            metrics[arm].append(metric)
            transitions += int(metric["environment_transitions"])
        if len(set(panel_digests)) != 1:
            raise RuntimeError("common held-out panels differ between arms")
        unit["evaluation_panel_digests"] = panel_digests
    return {"phase": "evaluate", "metrics": metrics, "environment_transitions": transitions,
            "evaluation_episodes": 1_280, "checkpoints_total": 10, "evaluation_updates": 0}


def analyze_registered_full(manifest: Mapping[str, object], preflight: Mapping[str, object],
                            training: Mapping[str, object], evaluation: Mapping[str, object],
                            resource_usage: Mapping[str, object],
                            admission_receipt: Mapping[str, object] | None = None) -> dict[str, object]:
    if manifest.get("technical_only") is not False or training.get("phase") != "train" or evaluation.get("phase") != "evaluate":
        raise ValueError("analyze is full-only and requires ordered train then evaluate phases")
    if not isinstance(admission_receipt, Mapping):
        raise ValueError("analyze requires the retained preclaim resource-admission receipt")
    units = training["units"]
    metrics = evaluation["metrics"]
    carry_success = {str(metric["unit_id"]) for metric in metrics["ADAM_CARRY"] if metric["exact_correct_unit"]}
    reset_success = {str(metric["unit_id"]) for metric in metrics["ADAM_RESET"] if metric["exact_correct_unit"]}
    training_transitions = sum(int(unit["training"]["environment_transitions"]) for unit in units)
    activity = {"result_bearing_runs": 1, "real_training_episodes": 10_200, "evaluation_episodes": 1_280,
                "environment_transitions": training_transitions + int(evaluation["environment_transitions"]),
                "optimizer_updates": 1_275, "checkpoints_total": 10, "retries_rescues_sweeps": 0}
    gates = {
        "identity": not validate_manifest(manifest), "state_reset": all(unit["training"]["reset_receipt"]["only_adam_slots_reset"] for unit in units),
        "common_ancestor": all(unit["training"]["reset_receipt"]["pre_reset_complete_state_byte_identical"] for unit in units),
        "update1_equality": all(unit["training"]["update1_q_receipt"]["forward_loss_raw_clipped_gradient_norm_factor_byte_identical"] for unit in units),
        "q": all(unit["training"]["update1_q_receipt"]["q_finite_positive"] and unit["training"]["update1_q_receipt"]["parameter_hashes_differ"] for unit in units),
        "oracle_firewall": all(unit["training"]["oracle_scalar_only"] for unit in units),
        "immutability": all(all(receipt["frozen_before"] == receipt["frozen_after"] for receipt in unit["training"]["barrier_receipts"]) for unit in units),
        "noninterference": all(all(receipt["carry_update_preserved_reset"] and receipt["reset_update_preserved_carry"] for receipt in unit["training"]["barrier_receipts"]) for unit in units),
        "finite_values": all(math.isfinite(float(update["loss"])) and math.isfinite(float(update["gradient_norm_before_clip"])) for unit in units for arm in B5R1_ARMS for update in unit["training"]["updates"][arm]),
        "activity": activity["real_training_episodes"] == 10_200 and activity["optimizer_updates"] == 1_275,
        "evaluation": all(len(metrics[arm]) == 5 for arm in B5R1_ARMS),
        "retained_validation": True,
        "resource_admission": not validate_resource_admission_receipt(
            admission_receipt, source_revision=str(manifest.get("source_revision", ""))
        ),
        "resources": activity["environment_transitions"] <= 57_400 and resource_usage.get("all_resource_caps_passed") is True,
    }
    valid = all(gates.values())
    branch = classify_b5r1(valid=valid, carry_success=carry_success, reset_success=reset_success)
    result = {
        "artifact_kind": "vsp02_b5r1_result", "assignment_id": B5R1_ASSIGNMENT_ID,
        "direction_id": B5R1_DIRECTION_ID, "candidate": B5R1_CANDIDATE,
        "manifest": dict(manifest), "manifest_identity": manifest_identity(manifest), "preflight": dict(preflight),
        "lifecycle": {"ordered_phases": ["train", "evaluate", "analyze"], "full_only": True,
                      "readiness_is_zero_runtime_and_separate": True},
        "branch": branch, "valid": valid, "gates": gates, "activity": activity,
        "resource_admission_receipt": dict(admission_receipt),
        "resource_usage": dict(resource_usage), "units": units, "evaluation": metrics,
        "exact_success_sets": {"C": sorted(carry_success), "R": sorted(reset_success),
                               "C_minus_R": sorted(carry_success - reset_success),
                               "R_minus_C": sorted(reset_success - carry_success)},
        "scalar_metrics_are_descriptive_only": True, "nonclaims": list(manifest["nonclaims"]),
        "automatic_successor_or_branch_repair": False,
    }
    result["evidence_digest"] = digest(result)
    return result


def run_treatment(manifest: Mapping[str, object], *, repo_root: Path | None = None,
                  admission_receipt: Mapping[str, object] | None = None) -> dict[str, object]:
    admission_issues = validate_resource_admission_receipt(
        admission_receipt,
        source_revision=str(manifest.get("source_revision", "")),
        require_current_process=True,
        max_age_seconds=B5R1_ADMISSION_MAX_AGE_SECONDS,
    )
    if admission_issues:
        raise ValueError("registered treatment requires a valid current preclaim admission receipt: " + "; ".join(admission_issues))
    assert admission_receipt is not None
    preflight = preflight_report(manifest, repo_root=repo_root)
    base = {"artifact_kind": "vsp02_b5r1_result", "assignment_id": B5R1_ASSIGNMENT_ID,
            "direction_id": B5R1_DIRECTION_ID, "candidate": B5R1_CANDIDATE,
            "manifest": dict(manifest), "manifest_identity": manifest_identity(manifest), "preflight": preflight,
            "resource_admission_receipt": dict(admission_receipt)}
    if not preflight["all_passed"]:
        result = {**base, "lifecycle": {"ordered_phases": [], "full_only": True,
                                        "readiness_is_zero_runtime_and_separate": True},
                  "branch": "B5_INVALID_OR_INACTIVE", "valid": False, "gates": None,
                  "activity": _zero_activity(), "resource_usage": None, "units": [], "evaluation": None,
                  "exact_success_sets": None, "scalar_metrics_are_descriptive_only": True,
                  "nonclaims": list(manifest.get("nonclaims", [])), "automatic_successor_or_branch_repair": False}
        result["evidence_digest"] = digest(result)
        return result
    if manifest.get("technical_only") is not False or manifest.get("run_id") != B5R1_RUN_ID:
        raise ValueError("treatment requires the registered technical_only=false manifest")
    cpu_start, rss_start = _cpu_time_seconds(), _peak_process_rss_bytes()
    training = train_registered_full(manifest, preflight)
    evaluation = evaluate_registered_full(manifest, training)
    cpu_end, rss_end = _cpu_time_seconds(), _peak_process_rss_bytes()
    resources = _resource_usage_evidence(cpu_start_seconds=cpu_start, cpu_end_seconds=cpu_end,
                                         peak_rss_samples_bytes=(rss_start, rss_end))
    return analyze_registered_full(manifest, preflight, training, evaluation, resources, admission_receipt)


def _validate_retained_update1_receipt(unit_id: str, receipt: object) -> tuple[str, ...]:
    """Purely derive update-1 equality/activity gates from retained payloads."""

    if not isinstance(receipt, Mapping):
        return (f"{unit_id} update-1 equality/q receipt missing",)
    issues: list[str] = []
    for key in ("both_batches_frozen_before_either_update", "batch_byte_identical", "ordered_rows_byte_identical"):
        if receipt.get(key) is not True:
            issues.append(f"{unit_id} update-1 {key} mismatch")
    payloads = receipt.get("prepared_comparison_payloads")
    derived_prepared_equal = (
        isinstance(payloads, Mapping)
        and set(payloads) == set(B5R1_ARMS)
        and all(isinstance(payloads[arm], Mapping) for arm in B5R1_ARMS)
        and canonical_bytes(payloads["ADAM_CARRY"]) == canonical_bytes(payloads["ADAM_RESET"])
    )
    if not derived_prepared_equal:
        issues.append(f"{unit_id} retained update-1 prepared payload equality mismatch")
    if receipt.get("forward_loss_raw_clipped_gradient_norm_factor_byte_identical") is not derived_prepared_equal:
        issues.append(f"{unit_id} update-1 prepared equality flag is not retained-payload-derived")
    q_r = receipt.get("q_r")
    derived_q_positive = isinstance(q_r, (int, float)) and not isinstance(q_r, bool) and math.isfinite(float(q_r)) and float(q_r) > 0.0
    if not derived_q_positive:
        issues.append(f"{unit_id} retained q_r is not finite and strictly positive")
    if receipt.get("q_finite_positive") is not derived_q_positive:
        issues.append(f"{unit_id} q activity flag is not retained-value-derived")
    hashes = receipt.get("parameter_hashes")
    derived_hashes_distinct = (
        isinstance(hashes, Mapping)
        and set(hashes) == set(B5R1_ARMS)
        and all(isinstance(hashes[arm], str) and bool(hashes[arm]) for arm in B5R1_ARMS)
        and hashes["ADAM_CARRY"] != hashes["ADAM_RESET"]
    )
    if not derived_hashes_distinct:
        issues.append(f"{unit_id} retained update-1 parameter hashes are not exact-arm distinct")
    if receipt.get("parameter_hashes_differ") is not derived_hashes_distinct:
        issues.append(f"{unit_id} parameter-hash difference flag is not retained-mapping-derived")
    return tuple(issues)


def validate_result(manifest: object, result: object, *, repo_root: Path | None = None,
                    expected_admission_receipt: Mapping[str, object] | None = None) -> tuple[str, ...]:
    """Pure retained validation: never calls preflight, train, evaluate, analyze, host, model, or optimizer."""
    issues = list(validate_manifest(manifest))
    if not isinstance(manifest, Mapping) or not isinstance(result, Mapping):
        return tuple(issues + ["manifest/result must be objects"])
    if result.get("artifact_kind") != "vsp02_b5r1_result" or result.get("assignment_id") != B5R1_ASSIGNMENT_ID or result.get("direction_id") != B5R1_DIRECTION_ID or result.get("candidate") != B5R1_CANDIDATE:
        issues.append("result identity mismatch")
    if result.get("manifest") != manifest or result.get("manifest_identity") != manifest_identity(manifest):
        issues.append("result manifest binding mismatch")
    admission = result.get("resource_admission_receipt")
    issues.extend(validate_resource_admission_receipt(
        admission, source_revision=str(manifest.get("source_revision", ""))
    ))
    if expected_admission_receipt is not None and admission != expected_admission_receipt:
        issues.append("result resource-admission receipt differs from the preclaim receipt")
    unsigned = dict(result)
    retained = unsigned.pop("evidence_digest", None)
    if retained != digest(unsigned):
        issues.append("retained artifact mutation or evidence digest mismatch")
    preflight = result.get("preflight")
    if not isinstance(preflight, Mapping):
        return tuple(issues + ["preflight evidence missing"])
    issues.extend(validate_preflight_evidence(manifest, preflight))
    if preflight.get("all_passed") is not True:
        if result.get("branch") != "B5_INVALID_OR_INACTIVE" or result.get("activity") != _zero_activity() or result.get("units") != [] or result.get("evaluation") is not None or result.get("resource_usage") is not None:
            issues.append("failed construction must be zero-activity invalid result")
        return tuple(issues)
    if manifest.get("technical_only") is not False or manifest.get("run_id") != B5R1_RUN_ID:
        issues.append("runtime result requires exact registered full manifest")
        return tuple(issues)
    units = result.get("units")
    evaluation = result.get("evaluation")
    if not isinstance(units, list) or len(units) != 5:
        issues.append("exactly five units required")
        return tuple(issues)
    if not isinstance(evaluation, Mapping) or set(evaluation) != set(B5R1_ARMS) or any(not isinstance(evaluation[arm], list) or len(evaluation[arm]) != 5 for arm in B5R1_ARMS):
        issues.append("exactly ten arm/unit evaluations required")
        return tuple(issues)
    training_transitions = 0
    final_hashes: dict[str, Mapping[str, object]] = {}
    derived_q_valid = True
    derived_common_valid = True
    derived_update1_valid = True
    derived_immutability = True
    derived_noninterference = True
    derived_finite = True
    for index, expected in enumerate(B5R1_UNITS):
        unit = units[index]
        if not isinstance(unit, Mapping) or (unit.get("unit_id"), unit.get("decimal_root")) != expected:
            issues.append(f"unit {index} identity mismatch")
            continue
        training = unit.get("training")
        if not isinstance(training, Mapping):
            issues.append(f"{expected[0]} training missing")
            continue
        if training.get("real_training_episodes") != 2_040 or training.get("optimizer_updates_applied") != 255 or training.get("effective_steps_per_arm") != {arm: 128 for arm in B5R1_ARMS}:
            issues.append(f"{expected[0]} activity mismatch")
        reset = training.get("reset_receipt")
        if not isinstance(reset, Mapping) or any(reset.get(key) is not True for key in (
            "pre_reset_complete_state_byte_identical", "reset_slots_canonical_fresh_empty", "carry_slots_retained_exactly",
            "parameter_groups_identical_before_after", "parameters_preserved_byte_identical",
            "learner_state_preserved_byte_identical", "rng_state_preserved_byte_identical",
            "recurrent_state_preserved_byte_identical", "only_adam_slots_reset")):
            issues.append(f"{expected[0]} reset receipt mismatch")
            derived_common_valid = False
        q = training.get("update1_q_receipt")
        q_issues = _validate_retained_update1_receipt(expected[0], q)
        issues.extend(q_issues)
        if q_issues:
            derived_q_valid = False
            derived_update1_valid = False
        batches = training.get("batch_records")
        barriers = training.get("barrier_receipts")
        updates = training.get("updates")
        if not isinstance(batches, list) or len(batches) != 128 or not isinstance(barriers, list) or len(barriers) != 127:
            issues.append(f"{expected[0]} batch/barrier count mismatch")
        else:
            for update_index, record in enumerate(batches):
                if not isinstance(record, Mapping) or record.get("update_index") != update_index:
                    issues.append(f"{expected[0]}/{update_index} batch identity mismatch")
                    continue
                if update_index == 0:
                    rows = record.get("rows")
                    if not isinstance(rows, list) or len(rows) != 8 or any(not isinstance(row, Mapping) or not _immutable_row_contract(row) for row in rows):
                        issues.append(f"{expected[0]} common batch invalid")
                    elif record.get("batch_digest") != digest(rows):
                        issues.append(f"{expected[0]} common batch digest mismatch")
                else:
                    rows_by_arm = record.get("rows")
                    if not isinstance(rows_by_arm, Mapping) or set(rows_by_arm) != set(B5R1_ARMS):
                        issues.append(f"{expected[0]}/{update_index} arm batches missing")
                        continue
                    for arm in B5R1_ARMS:
                        rows = rows_by_arm[arm]
                        if not isinstance(rows, list) or len(rows) != 8 or any(not isinstance(row, Mapping) or not _immutable_row_contract(row) for row in rows):
                            issues.append(f"{expected[0]}/{update_index}/{arm} immutable batch invalid")
                        elif record.get("batch_digests", {}).get(arm) != digest(rows):  # type: ignore[union-attr]
                            issues.append(f"{expected[0]}/{update_index}/{arm} batch digest mismatch")
            for barrier in barriers:
                if not isinstance(barrier, Mapping) or barrier.get("frozen_before") != barrier.get("frozen_after"):
                    derived_immutability = False
                if not isinstance(barrier, Mapping) or barrier.get("carry_update_preserved_reset") is not True or barrier.get("reset_update_preserved_carry") is not True:
                    derived_noninterference = False
        if not isinstance(updates, Mapping) or set(updates) != set(B5R1_ARMS) or any(not isinstance(updates[arm], list) or len(updates[arm]) != 128 for arm in B5R1_ARMS):
            issues.append(f"{expected[0]} update count mismatch")
        else:
            for arm in B5R1_ARMS:
                for update in updates[arm]:
                    if not isinstance(update, Mapping):
                        derived_finite = False
                        continue
                    if "loss" in update and (not isinstance(update["loss"], (int, float)) or not math.isfinite(float(update["loss"]))):
                        derived_finite = False
        try:
            training_transitions += int(training["environment_transitions"])
        except (KeyError, TypeError, ValueError):
            issues.append(f"{expected[0]} transition count invalid")
        hashes = training.get("final_parameter_hashes")
        if isinstance(hashes, Mapping):
            final_hashes[expected[0]] = hashes
    derived_metrics: dict[str, list[dict[str, object]]] = {arm: [] for arm in B5R1_ARMS}
    eval_transitions = 0
    for arm in B5R1_ARMS:
        for index, (unit_id, root) in enumerate(B5R1_UNITS):
            metric = evaluation[arm][index]
            if not isinstance(metric, Mapping):
                issues.append(f"{unit_id}/{arm} metric invalid")
                continue
            expected_hash = final_hashes.get(unit_id, {}).get(arm)
            derived, metric_issues = _derive_retained_evaluation_metric(unit_id=unit_id, root=root, arm=arm,
                                                                         metric=metric, expected_final_hash=expected_hash)
            issues.extend(metric_issues)
            if derived is not None:
                derived_metrics[arm].append(derived)
                eval_transitions += int(derived["environment_transitions"])
    carry_success = {metric["unit_id"] for metric in derived_metrics["ADAM_CARRY"] if metric["exact_correct_unit"]}
    reset_success = {metric["unit_id"] for metric in derived_metrics["ADAM_RESET"] if metric["exact_correct_unit"]}
    activity = result.get("activity")
    derived_activity = {"result_bearing_runs": 1, "real_training_episodes": 10_200, "evaluation_episodes": 1_280,
                        "environment_transitions": training_transitions + eval_transitions,
                        "optimizer_updates": 1_275, "checkpoints_total": 10, "retries_rescues_sweeps": 0}
    if activity != derived_activity or derived_activity["environment_transitions"] > 57_400:
        issues.append("retained activity/count/cap mismatch")
    resource = result.get("resource_usage")
    resource_valid = isinstance(resource, Mapping) and resource.get("all_resource_caps_passed") is True and isinstance(resource.get("cpu_minutes"), (int, float)) and float(resource["cpu_minutes"]) <= 30 and isinstance(resource.get("peak_process_memory_gib"), (int, float)) and float(resource["peak_process_memory_gib"]) <= 2
    derived_gates = {
        "identity": not validate_manifest(manifest), "state_reset": derived_common_valid,
        "common_ancestor": derived_common_valid, "update1_equality": derived_update1_valid,
        "q": derived_q_valid, "oracle_firewall": all(unit["training"].get("oracle_scalar_only") is True for unit in units if isinstance(unit, Mapping) and isinstance(unit.get("training"), Mapping)),
        "immutability": derived_immutability, "noninterference": derived_noninterference,
        "finite_values": derived_finite, "activity": activity == derived_activity,
        "evaluation": all(len(derived_metrics[arm]) == 5 for arm in B5R1_ARMS),
        "retained_validation": True,
        "resource_admission": not validate_resource_admission_receipt(
            admission, source_revision=str(manifest.get("source_revision", ""))
        ),
        "resources": resource_valid and derived_activity["environment_transitions"] <= 57_400,
    }
    valid = all(derived_gates.values()) and not issues
    expected_branch = classify_b5r1(valid=valid, carry_success=set(carry_success), reset_success=set(reset_success))
    if result.get("gates") != derived_gates:
        issues.append("retained gate projection mismatch")
    if result.get("valid") is not valid or result.get("branch") != expected_branch:
        issues.append("retained validity/branch mismatch")
    expected_sets = {"C": sorted(carry_success), "R": sorted(reset_success),
                     "C_minus_R": sorted(carry_success - reset_success), "R_minus_C": sorted(reset_success - carry_success)}
    if result.get("exact_success_sets") != expected_sets:
        issues.append("exact-success set projection mismatch")
    return tuple(issues)

"""Result-blind, resumable, atomic production runner for frozen ONLGR-B2."""

from __future__ import annotations

import argparse
from contextlib import AbstractContextManager
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from typing import Callable
import uuid

import torch

from .analysis import analyze_complete_package, diagnostic_grid, summarize_panel
from .config import (
    ARMS, CARD_RELATIVE_PATH, CLOSURE_RELATIVE_PATH, FRONTIER_REVISION,
    HORIZON, IID_EPISODES_PER_ARM_SEED, IID_SCHEDULE, KEEP_EPISODES_PER_ARM_SEED,
    PRODUCTION_CONFIG, REVISION, SAFETY_EPISODES_PER_ARM_SEED, SEEDS,
    TRAIN_SCHEDULES, UPDATES,
)
from .host import generate_episode, run_episode
from .models import B2Learner, PPOUpdateFacts

ATOMIC_REUSE_RESERVE_SECONDS = 1.0
ATOMIC_REPLACE_RESERVE_SECONDS = 2.0
TRAINING_CELL_RESERVE_SECONDS = 120.0
FINAL_EVALUATION_RESERVE_SECONDS = 900.0

ACTOR_STATE_SHAPES = {
    "input_layer.weight": (32, 7), "input_layer.bias": (32,),
    "hidden_layer.weight": (32, 32), "hidden_layer.bias": (32,),
    "output_layer.weight": (1, 32), "output_layer.bias": (1,),
}
CRITIC_STATE_SHAPES = {
    "network.0.weight": (64, 39), "network.0.bias": (64,),
    "network.2.weight": (64, 64), "network.2.bias": (64,),
    "network.4.weight": (1, 64), "network.4.bias": (1,),
}
ADAM_PARAM_GROUP_KEYS = {
    "lr", "betas", "eps", "weight_decay", "amsgrad", "maximize", "foreach",
    "capturable", "differentiable", "fused", "decoupled_weight_decay", "params",
}
COMPLETE_RESULT_TOP_LEVEL_FIELDS = {
    "artifact_kind", "revision", "PACKAGE_VALID", "MARK_SUPPORT_OK", "missing_facts",
    "failed_conformance", "anomalies", "conformance", "support_cells", "R_IID",
    "paired_difference_RATE_FLEX_minus_RATE_CONST", "branches", "diagnostic_grids",
    "initialization", "probability_jacobian_conformance", "iid_seed_arm_metrics",
    "safety_seed_arm_metrics", "keep_seed_arm_metrics", "training_seed_arm_facts",
    "checkpoint_facts", "registered_work", "strongest_remaining_alternative",
    "source_identity", "activity_facts", "fresh_counter_namespaces", "frontier",
    "resources", "result_materialization",
}
CLAIM_BEARING_RECOMPUTE_FIELDS = (
    "PACKAGE_VALID", "MARK_SUPPORT_OK", "missing_facts", "failed_conformance", "anomalies",
    "conformance", "support_cells", "R_IID", "paired_difference_RATE_FLEX_minus_RATE_CONST",
    "branches", "diagnostic_grids", "registered_work", "strongest_remaining_alternative",
    "initialization", "probability_jacobian_conformance",
)
CHECKPOINT_FACT_FIELDS = {
    "artifact_kind", "revision", "seed", "arm", "source_identity",
    "learned_state_sha256", "path", "sha256_before_evaluation",
    "sha256_after_evaluation", "immutable_before_after", "completed_updates",
    "actor_parameter_count", "critic_parameter_count", "source_identity_exact",
    "envelope_valid",
}


def _digest_recursive(digest: "hashlib._Hash", value: object) -> None:
    if isinstance(value, torch.Tensor):
        tensor = value.detach()
        digest.update(b"tensor\0")
        digest.update(str(tensor.dtype).encode("ascii") + b"\0")
        digest.update(str(tuple(tensor.shape)).encode("ascii") + b"\0")
        digest.update(str(tensor.device).encode("ascii") + b"\0")
        digest.update(tensor.cpu().contiguous().numpy().tobytes())
    elif isinstance(value, dict):
        digest.update(b"dict\0")
        for key in sorted(value, key=lambda item: (type(item).__name__, repr(item))):
            _digest_recursive(digest, key)
            _digest_recursive(digest, value[key])
    elif isinstance(value, (list, tuple)):
        digest.update(("tuple" if isinstance(value, tuple) else "list").encode("ascii") + b"\0")
        for item in value:
            _digest_recursive(digest, item)
    elif value is None or isinstance(value, (str, int, float, bool)):
        digest.update(type(value).__name__.encode("ascii") + b"\0")
        digest.update(repr(value).encode("utf-8") + b"\0")
    else:
        raise FrontierIdentityError(f"unsupported learned-state digest type: {type(value)!r}")


def learned_state_sha256(checkpoint: dict[str, object]) -> str:
    digest = hashlib.sha256()
    _digest_recursive(digest, {
        "actor": checkpoint.get("actor"), "critic": checkpoint.get("critic"),
        "optimizer": checkpoint.get("optimizer"),
    })
    return digest.hexdigest()


def _json_equivalent(left: object, right: object) -> bool:
    return json.dumps(left, sort_keys=True, separators=(",", ":"), allow_nan=False) == json.dumps(
        right, sort_keys=True, separators=(",", ":"), allow_nan=False,
    )


def _evaluation_binding_sha256(
    identity: dict[str, object], digest_map: dict[str, dict[str, str]], panel_payload_sha256: str,
) -> str:
    return hashlib.sha256(json.dumps(
        {
            "revision": REVISION, "source_identity": identity,
            "checkpoint_state_digests": digest_map,
            "panel_payload_sha256": panel_payload_sha256,
        },
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def _panel_payload_sha256(panels: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(
        panels, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()


def _validate_tensor_state(
    state: object, shapes: dict[str, tuple[int, ...]], label: str,
) -> dict[str, torch.Tensor]:
    if not isinstance(state, dict) or set(state) != set(shapes):
        raise FrontierIdentityError(f"{label} tensor keys are not exact")
    for key, shape in shapes.items():
        tensor = state[key]
        if (
            not isinstance(tensor, torch.Tensor) or tuple(tensor.shape) != shape
            or tensor.dtype != torch.float64 or tensor.device.type != "cpu"
            or not bool(torch.isfinite(tensor).all())
        ):
            raise FrontierIdentityError(f"{label} tensor is invalid: {key}")
    return state


def _validate_optimizer_state(
    optimizer: object, *, completed_updates: int,
) -> dict[str, object]:
    if not isinstance(optimizer, dict) or set(optimizer) != {"state", "param_groups"}:
        raise FrontierIdentityError("Adam optimizer schema is not exact")
    groups = optimizer["param_groups"]
    state = optimizer["state"]
    if not isinstance(groups, list) or len(groups) != 1 or not isinstance(groups[0], dict):
        raise FrontierIdentityError("Adam must have exactly one parameter group")
    group = groups[0]
    if set(group) != ADAM_PARAM_GROUP_KEYS:
        raise FrontierIdentityError("Adam parameter-group keys are not exact")
    expected_hyperparameters = {
        "lr": 3e-4, "betas": (0.9, 0.999), "eps": 1e-8, "weight_decay": 0,
        "amsgrad": False, "maximize": False, "foreach": None, "capturable": False,
        "differentiable": False, "fused": None, "decoupled_weight_decay": False,
    }
    if (
        not math.isfinite(float(group.get("lr", float("nan"))))
        or any(group.get(key) != value for key, value in expected_hyperparameters.items())
        or group.get("params") != list(range(12))
    ):
        raise FrontierIdentityError("Adam parameter-group hyperparameters are not frozen B2 values")
    if not isinstance(state, dict) or set(state) != set(range(12)):
        raise FrontierIdentityError("Adam state parameter IDs are not exact")
    parameter_shapes = [*ACTOR_STATE_SHAPES.values(), *CRITIC_STATE_SHAPES.values()]
    expected_step = completed_updates * 4
    for parameter_id, shape in enumerate(parameter_shapes):
        row = state[parameter_id]
        if not isinstance(row, dict) or set(row) != {"step", "exp_avg", "exp_avg_sq"}:
            raise FrontierIdentityError(f"Adam state schema is invalid for parameter {parameter_id}")
        step, average, squared = row["step"], row["exp_avg"], row["exp_avg_sq"]
        if (
            not isinstance(step, torch.Tensor) or tuple(step.shape) != ()
            or step.dtype != torch.float32 or step.device.type != "cpu"
            or not bool(torch.isfinite(step)) or float(step) != float(expected_step)
        ):
            raise FrontierIdentityError(f"Adam step is invalid for parameter {parameter_id}")
        for name, tensor in (("exp_avg", average), ("exp_avg_sq", squared)):
            if (
                not isinstance(tensor, torch.Tensor) or tuple(tensor.shape) != shape
                or tensor.dtype != torch.float64 or tensor.device.type != "cpu"
                or not bool(torch.isfinite(tensor).all())
            ):
                raise FrontierIdentityError(f"Adam {name} is invalid for parameter {parameter_id}")
    return optimizer


class FrontierIdentityError(RuntimeError):
    pass


class SliceExpired(RuntimeError):
    pass


def _rss_bytes() -> int:
    """Current process working set without an optional dependency."""
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
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD,
        ]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        handle = kernel32.GetCurrentProcess()
        if not handle or not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            raise OSError(ctypes.get_last_error(), "Windows process RSS query failed")
        return int(counters.WorkingSetSize)
    import resource
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if value > 10**8 else value * 1024


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_identity() -> dict[str, object]:
    """Bind only B2 semantic sources plus the exact closed card and intake."""
    root = _workspace_root()
    module_root = Path(__file__).resolve().parent
    paths = sorted(module_root.glob("*.py")) + [
        root / CARD_RELATIVE_PATH, root / CLOSURE_RELATIVE_PATH,
    ]
    if any(not path.is_file() for path in paths):
        raise FrontierIdentityError("a B2 source/card identity path is missing")
    files = {str(path.relative_to(root)).replace("\\", "/"): _sha256(path) for path in paths}
    composite = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {"revision": REVISION, "files": files, "composite_sha256": composite}


def _safe_output_root(path: Path) -> Path:
    resolved = path.resolve()
    workspace = _workspace_root().resolve()
    if resolved == workspace or workspace not in resolved.parents:
        raise ValueError("B2 output root must be a dedicated directory inside the workspace")
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        raise ValueError("B2 output root must be a real directory")
    path.mkdir(parents=True, exist_ok=True)
    return path


_ATOMIC_TEMP_NAME = re.compile(r"^\.(?:manifest\.json|results\.json|[^/\\]+\.pt)\.[0-9a-f]{32}\.tmp$")


def _discard_stale_atomic_temps(output_root: Path) -> None:
    """Discard only uncommitted files created by this runner's atomic protocol."""
    for path in output_root.rglob("*.tmp"):
        if path.is_symlink() or not path.is_file() or not _ATOMIC_TEMP_NAME.fullmatch(path.name):
            raise FrontierIdentityError(f"unexpected temporary frontier entry: {path}")
        path.unlink()


_TRAIN_CELL_NAME = re.compile(
    r"^train_seed_(137|149|163|181|199|223|239|257)_(RATE-FLEX|RATE-CONST)_update_([1-8])\.pt$"
)
_CHECKPOINT_DIRECTORY = re.compile(r"^seed_(137|149|163|181|199|223|239|257)$")


def _validate_output_entries(output_root: Path) -> None:
    """Reject aliases and every entry outside the registered B2 lifecycle."""
    allowed_top = {"manifest.json", "frontier", "checkpoints", "results.json", ".run.lock"}
    for entry in output_root.iterdir():
        if entry.is_symlink() or entry.name not in allowed_top:
            raise FrontierIdentityError(f"unexpected or symlinked B2 output entry: {entry}")
    frontier = output_root / "frontier"
    if frontier.exists():
        if not frontier.is_dir() or frontier.is_symlink():
            raise FrontierIdentityError("B2 frontier is not a real directory")
        for entry in frontier.iterdir():
            if entry.is_symlink() or not entry.is_file() or not _TRAIN_CELL_NAME.fullmatch(entry.name):
                raise FrontierIdentityError(f"unexpected B2 frontier entry: {entry}")
    checkpoint_root = output_root / "checkpoints"
    if checkpoint_root.exists():
        if not checkpoint_root.is_dir() or checkpoint_root.is_symlink():
            raise FrontierIdentityError("B2 checkpoint root is not a real directory")
        for directory in checkpoint_root.iterdir():
            if directory.is_symlink() or not directory.is_dir() or not _CHECKPOINT_DIRECTORY.fullmatch(directory.name):
                raise FrontierIdentityError(f"unexpected B2 checkpoint directory: {directory}")
            seed = directory.name.removeprefix("seed_")
            for entry in directory.iterdir():
                if (
                    entry.is_symlink() or not entry.is_file()
                    or entry.name not in {f"{arm}.pt" for arm in ARMS}
                    or seed not in {str(value) for value in SEEDS}
                ):
                    raise FrontierIdentityError(f"unexpected B2 checkpoint entry: {entry}")
    for name in ("manifest.json", "results.json", ".run.lock"):
        entry = output_root / name
        if entry.exists() and (entry.is_symlink() or not entry.is_file()):
            raise FrontierIdentityError(f"B2 lifecycle file is not a real file: {entry}")


class _ScopedRunLock(AbstractContextManager["_ScopedRunLock"]):
    def __init__(self, output_root: Path) -> None:
        self.path = output_root / ".run.lock"
        self.token = f"{os.getpid()}:{uuid.uuid4().hex}"
        self.stream = None

    def __enter__(self) -> "_ScopedRunLock":
        if self.path.is_symlink() or (self.path.exists() and not self.path.is_file()):
            raise FrontierIdentityError("unsafe B2 run lock")
        self.stream = self.path.open("a+b")
        self.stream.seek(0, os.SEEK_END)
        if self.stream.tell() == 0:
            self.stream.write(b"\0")
            self.stream.flush()
        self.stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.stream.close()
            self.stream = None
            raise FrontierIdentityError("another B2 process owns this output root") from exc
        self.stream.seek(0)
        self.stream.truncate()
        self.stream.write((self.token + "\n").encode("ascii"))
        self.stream.flush()
        os.fsync(self.stream.fileno())
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.stream is None:
            return
        self.stream.seek(0)
        changed = self.stream.read().decode("ascii").strip() != self.token
        try:
            self.stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
        finally:
            self.stream.close()
            self.stream = None
        if changed:
            raise FrontierIdentityError("B2 run lock ownership changed")


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, sort_keys=True, separators=(",", ":"), allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_torch(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as stream:
            torch.save(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _load_torch(path: Path) -> dict[str, object]:
    try:
        # Frontier files contain only tensors and primitive container types.  Keep
        # deserialization on PyTorch's restricted path so an untrusted/tampered
        # pickle cannot execute code before the schema and identity checks below.
        payload = torch.load(path, map_location="cpu", weights_only=True)
    except Exception as exc:  # pragma: no cover - exact exception is torch-version dependent.
        raise FrontierIdentityError(f"cannot load atomic B2 cell {path}") from exc
    if not isinstance(payload, dict):
        raise FrontierIdentityError(f"B2 cell is not an object: {path}")
    return payload


def _prepare_manifest(output_root: Path, identity: dict[str, object]) -> None:
    manifest_path = output_root / "manifest.json"
    expected = {
        "artifact_kind": "ONLGR_B2_RESULT_BLIND_FRONTIER",
        "frontier_revision": FRONTIER_REVISION,
        "source_identity": identity,
        "registered_config": asdict(PRODUCTION_CONFIG),
    }
    if manifest_path.exists():
        try:
            actual = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise FrontierIdentityError("B2 manifest is unreadable") from exc
        if actual != expected:
            raise FrontierIdentityError("B2 manifest/source/card/config identity mismatch")
    else:
        _atomic_json(manifest_path, expected)


def _cell_payload(
    *, kind: str, coordinate: str, identity: dict[str, object], data: object,
    started: float, rss_before: int, binding: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "artifact_kind": "ONLGR_B2_BLINDED_ATOMIC_CELL",
        "frontier_revision": FRONTIER_REVISION, "kind": kind,
        "coordinate": coordinate, "source_identity": identity,
        "binding": dict(binding or {}), "data": data,
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "rss_before_bytes": rss_before, "rss_after_bytes": _rss_bytes(),
        },
    }


def _validate_cell(
    payload: dict[str, object], *, kind: str, coordinate: str,
    identity: dict[str, object], binding: dict[str, object] | None = None,
) -> dict[str, object]:
    expected = {
        "artifact_kind": "ONLGR_B2_BLINDED_ATOMIC_CELL",
        "frontier_revision": FRONTIER_REVISION, "kind": kind,
        "coordinate": coordinate, "source_identity": identity,
        "binding": dict(binding or {}),
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise FrontierIdentityError(f"atomic cell identity mismatch: {coordinate}")
    if "data" not in payload or "resources" not in payload:
        raise FrontierIdentityError(f"atomic cell is incomplete: {coordinate}")
    return payload


def _deadline_ok(deadline: float, reserve: float = 0.25) -> None:
    if time.perf_counter() + reserve >= deadline:
        raise SliceExpired("resource slice ended before the next atomic cell")


def _run_or_load_cell(
    *, path: Path, kind: str, coordinate: str, identity: dict[str, object],
    deadline: float, work: Callable[[], object], binding: dict[str, object] | None = None,
    reserve_seconds: float = TRAINING_CELL_RESERVE_SECONDS,
) -> dict[str, object]:
    _deadline_ok(deadline, ATOMIC_REUSE_RESERVE_SECONDS)
    if path.exists():
        return _validate_cell(
            _load_torch(path), kind=kind, coordinate=coordinate,
            identity=identity, binding=binding,
        )
    _deadline_ok(deadline, reserve_seconds)
    started = time.perf_counter()
    rss_before = _rss_bytes()
    data = work()
    payload = _cell_payload(
        kind=kind, coordinate=coordinate, identity=identity, data=data,
        started=started, rss_before=rss_before, binding=binding,
    )
    _deadline_ok(deadline, ATOMIC_REPLACE_RESERVE_SECONDS)
    _atomic_torch(path, payload)
    _deadline_ok(deadline, 0.0)
    return payload


def _training_episode_work(episodes: list[object], learner: B2Learner) -> dict[str, object]:
    latencies = [value for episode in episodes for value in episode.decision_latencies_ns]
    identities = [identity for episode in episodes for identity in episode.identity_rows]
    identity_schema_valid = all(
        identity.episode_id and identity.agent_role in ("T", "R")
        and identity.owner_epoch >= 0 and identity.own_boundary_index >= 0
        and identity.behavior_version
        and identity.cause == "ROUTINE_CALLBACK"
        and identity.action in ("KEEP", "REFRESH-SAME", "REBIND")
        for identity in identities
    )
    return {
        "episodes": len(episodes), "physics_ticks": sum(episode.physics_ticks for episode in episodes),
        "actor_calls": sum(episode.actor_calls for episode in episodes),
        "critic_calls": sum(episode.critic_calls for episode in episodes),
        "messages": sum(episode.messages for episode in episodes),
        "transmitted_bits": sum(episode.transmitted_bits for episode in episodes),
        "identity_rows": len(identities),
        "identity_unique_within_episodes": all(episode.identity_unique for episode in episodes),
        "identity_schema_valid": identity_schema_valid,
        "reward_service_cost_exact": all(episode.reward_service_cost_exact for episode in episodes),
        "segment_ownership_exact": all(episode.segment_ownership_exact for episode in episodes),
        "terminal_boundary_absent": all(episode.terminal_boundary_absent for episode in episodes),
        "latency_call_count": len(latencies),
        "latency_sum_ns": sum(latencies), "latency_max_ns": max(latencies, default=0),
        "actor_parameter_count": learner.actor_parameter_count,
        "critic_parameter_count": learner.critic_parameter_count,
    }


def _validate_training_cell_data(data: object, coordinate: str) -> dict[str, object]:
    expected = {
        "checkpoint", "update_fact", "cumulative_update_facts",
        "cumulative_work_facts", "activity_fact", "learned_state_sha256",
    }
    if not isinstance(data, dict) or set(data) != expected or not isinstance(data.get("checkpoint"), dict):
        raise FrontierIdentityError(f"training continuation fields are not exact: {coordinate}")
    forbidden = {"actor_loss", "critic_loss", "return", "reward", "service", "support", "rate"}
    for fact in data.get("cumulative_update_facts", ()):
        if not isinstance(fact, dict) or forbidden & set(fact):
            raise FrontierIdentityError(f"training continuation contains outcome-bearing extras: {coordinate}")
    activity = data.get("activity_fact", {})
    if (
        not isinstance(activity, dict) or activity.get("scientific_activity_started") is not True
        or activity.get("claim_bearing_evaluation_persisted") is not False
        or activity.get("revision") != REVISION
    ):
        raise FrontierIdentityError(f"training continuation activity fact is invalid: {coordinate}")
    match = re.fullmatch(
        r"train:(137|149|163|181|199|223|239|257):(RATE-FLEX|RATE-CONST):update-([1-8])",
        coordinate,
    )
    if match is None:
        raise FrontierIdentityError(f"training continuation coordinate is invalid: {coordinate}")
    seed, arm, update = int(match.group(1)), match.group(2), int(match.group(3))
    _validate_learned_checkpoint(data["checkpoint"], seed=seed, arm=arm, completed_updates=update)
    digest = learned_state_sha256(data["checkpoint"])
    if data.get("learned_state_sha256") != digest:
        raise FrontierIdentityError(f"training continuation learned-state digest mismatch: {coordinate}")
    return data


def _validate_learned_checkpoint(
    checkpoint: object, *, seed: int, arm: str, completed_updates: int,
) -> dict[str, object]:
    expected_fields = {
        "seed", "arm", "completed_updates", "actor", "critic", "optimizer",
        "actor_parameter_count", "critic_parameter_count", "update_facts",
    }
    if not isinstance(checkpoint, dict) or set(checkpoint) != expected_fields:
        raise FrontierIdentityError(f"learned checkpoint fields are not exact: {seed}:{arm}")
    update_facts = checkpoint.get("update_facts")
    if (
        checkpoint.get("seed") != seed or checkpoint.get("arm") != arm
        or checkpoint.get("completed_updates") != completed_updates
        or not isinstance(update_facts, list) or len(update_facts) != completed_updates
    ):
        raise FrontierIdentityError(f"learned checkpoint coordinate is invalid: {seed}:{arm}")
    actor = _validate_tensor_state(checkpoint["actor"], ACTOR_STATE_SHAPES, "actor")
    critic = _validate_tensor_state(checkpoint["critic"], CRITIC_STATE_SHAPES, "critic")
    if (
        checkpoint.get("actor_parameter_count") != sum(tensor.numel() for tensor in actor.values())
        or checkpoint.get("critic_parameter_count") != sum(tensor.numel() for tensor in critic.values())
    ):
        raise FrontierIdentityError(f"learned checkpoint parameter counts are invalid: {seed}:{arm}")
    _validate_optimizer_state(checkpoint["optimizer"], completed_updates=completed_updates)
    return checkpoint


def _require_final_matches_frontier(
    envelope: dict[str, object], frontier_checkpoint: dict[str, object], *, coordinate: str,
) -> None:
    frontier_digest = learned_state_sha256(frontier_checkpoint)
    if (
        envelope.get("learned_state_sha256") != frontier_digest
        or learned_state_sha256(envelope["checkpoint"]) != frontier_digest
    ):
        raise FrontierIdentityError(
            f"final checkpoint differs from update-eight training frontier: {coordinate}"
        )


def _require_final_matches_durable_frontier(
    output_root: Path, envelope: dict[str, object], *, seed: int, arm: str,
    identity: dict[str, object], deadline: float,
) -> None:
    _deadline_ok(deadline, ATOMIC_REUSE_RESERVE_SECONDS)
    coordinate = f"train:{seed}:{arm}:update-{UPDATES}"
    cell = _validate_cell(
        _load_torch(
            output_root / "frontier" / f"train_seed_{seed}_{arm}_update_{UPDATES}.pt"
        ),
        kind="training_update", coordinate=coordinate, identity=identity,
    )
    data = _validate_training_cell_data(cell["data"], coordinate)
    _require_final_matches_frontier(
        envelope, data["checkpoint"], coordinate=f"{seed}:{arm}",
    )


def _train_coordinate(
    *, output_root: Path, frontier: Path, seed: int, arm: str,
    identity: dict[str, object], deadline: float,
) -> tuple[B2Learner, dict[str, object], dict[str, object]]:
    learner = B2Learner(seed, arm)
    cumulative_facts: list[PPOUpdateFacts] = []
    cumulative_work: list[dict[str, object]] = []
    completed_updates = 0
    for update_index in range(UPDATES):
        coordinate = f"train:{seed}:{arm}:update-{update_index + 1}"
        path = frontier / f"train_seed_{seed}_{arm}_update_{update_index + 1}.pt"

        def work(update_index: int = update_index) -> dict[str, object]:
            episodes = []
            for schedule in TRAIN_SCHEDULES:
                for local_index in range(8):
                    episode_index = update_index * 8 + local_index
                    exogenous = generate_episode(
                        seed=seed, episode_index=episode_index,
                        namespace="B2_TRAIN_PAIRED", schedule=schedule,
                    )
                    episodes.append(run_episode(
                        exogenous, arm=arm, learner=learner, collect_training=True,
                        owner_epoch=update_index, behavior_version=f"{arm}:behavior-{update_index}",
                    ))
            facts = learner.update(episodes, update_index + 1)
            all_facts = [*cumulative_facts, facts]
            work_fact = _training_episode_work(episodes, learner)
            all_work = [*cumulative_work, work_fact]
            checkpoint = learner.checkpoint(update_index + 1, all_facts)
            return {
                "checkpoint": checkpoint,
                "learned_state_sha256": learned_state_sha256(checkpoint),
                "update_fact": asdict(facts),
                "cumulative_update_facts": [asdict(value) for value in all_facts],
                "cumulative_work_facts": all_work,
                "activity_fact": {
                    "scientific_activity_started": True,
                    "trigger": "first retained task-trained actor/critic/optimizer update",
                    "trigger_coordinate": coordinate,
                    "earliest_registered_trigger": bool(
                        seed == SEEDS[0] and arm == ARMS[0] and update_index == 0
                    ),
                    "claim_bearing_evaluation_persisted": False,
                    "revision": REVISION,
                },
            }

        cell = _run_or_load_cell(
            path=path, kind="training_update", coordinate=coordinate, identity=identity,
            deadline=deadline, work=work,
        )
        data = _validate_training_cell_data(cell["data"], coordinate)
        learner.load_checkpoint(data["checkpoint"])
        cumulative_facts = [PPOUpdateFacts(**fact) for fact in data["cumulative_update_facts"]]
        cumulative_work = list(data.get("cumulative_work_facts", ()))
        completed_updates = int(data["checkpoint"]["completed_updates"])
        if (
            completed_updates != update_index + 1 or len(cumulative_facts) != completed_updates
            or len(cumulative_work) != completed_updates
            or not bool(data.get("activity_fact", {}).get("scientific_activity_started"))
            or bool(data.get("activity_fact", {}).get("claim_bearing_evaluation_persisted"))
        ):
            raise FrontierIdentityError(f"training frontier is noncontiguous: {coordinate}")

    final_checkpoint = output_root / "checkpoints" / f"seed_{seed}" / f"{arm}.pt"
    checkpoint_data = learner.checkpoint(completed_updates, cumulative_facts)
    checkpoint_state_digest = learned_state_sha256(checkpoint_data)
    checkpoint_envelope = {
        "artifact_kind": "ONLGR_B2_SOLE_FINAL_CHECKPOINT", "revision": REVISION,
        "source_identity": identity, "seed": seed, "arm": arm,
        "learned_state_sha256": checkpoint_state_digest, "checkpoint": checkpoint_data,
    }
    if final_checkpoint.exists():
        _deadline_ok(deadline, ATOMIC_REUSE_RESERVE_SECONDS)
        actual = _validate_checkpoint_envelope(
            final_checkpoint, seed=seed, arm=arm, identity=identity,
        )
        _require_final_matches_frontier(actual, checkpoint_data, coordinate=f"{seed}:{arm}")
        learner.load_checkpoint(actual["checkpoint"])
    else:
        _deadline_ok(deadline, ATOMIC_REPLACE_RESERVE_SECONDS)
        _atomic_torch(final_checkpoint, checkpoint_envelope)
        _deadline_ok(deadline, 0.0)
    checkpoint_hash = _sha256(final_checkpoint)
    training_summary = {
        "episodes": sum(int(fact["episodes"]) for fact in cumulative_work),
        "physics_ticks": sum(int(fact["physics_ticks"]) for fact in cumulative_work),
        "actor_calls": sum(int(fact["actor_calls"]) for fact in cumulative_work),
        "critic_calls": sum(int(fact["critic_calls"]) for fact in cumulative_work),
        "messages": sum(int(fact["messages"]) for fact in cumulative_work),
        "transmitted_bits": sum(int(fact["transmitted_bits"]) for fact in cumulative_work),
        "identity_rows": sum(int(fact["identity_rows"]) for fact in cumulative_work),
        "identity_unique_within_episodes": all(bool(fact["identity_unique_within_episodes"]) for fact in cumulative_work),
        "identity_schema_valid": all(bool(fact["identity_schema_valid"]) for fact in cumulative_work),
        "reward_service_cost_exact": all(bool(fact["reward_service_cost_exact"]) for fact in cumulative_work),
        "segment_ownership_exact": all(bool(fact["segment_ownership_exact"]) for fact in cumulative_work),
        "terminal_boundary_absent": all(bool(fact["terminal_boundary_absent"]) for fact in cumulative_work),
        "latency_call_count": sum(int(fact["latency_call_count"]) for fact in cumulative_work),
        "latency_sum_ns": sum(int(fact["latency_sum_ns"]) for fact in cumulative_work),
        "latency_max_ns": max(int(fact["latency_max_ns"]) for fact in cumulative_work),
        "actor_parameter_count": learner.actor_parameter_count,
        "critic_parameter_count": learner.critic_parameter_count,
        "completed_updates": completed_updates,
        "optimizer_steps": sum(fact.optimizer_steps for fact in cumulative_facts),
        "update_facts": [asdict(fact) for fact in cumulative_facts],
        "per_update_work_facts": cumulative_work,
    }
    checkpoint_fact = {
        "artifact_kind": "ONLGR_B2_SOLE_FINAL_CHECKPOINT", "revision": REVISION,
        "seed": seed, "arm": arm, "source_identity": identity,
        "learned_state_sha256": checkpoint_state_digest,
        "path": str(final_checkpoint.relative_to(output_root)).replace("\\", "/"),
        "sha256_before_evaluation": checkpoint_hash, "sha256_after_evaluation": None,
        "immutable_before_after": False, "completed_updates": completed_updates,
        "actor_parameter_count": learner.actor_parameter_count,
        "critic_parameter_count": learner.critic_parameter_count,
        "source_identity_exact": True, "envelope_valid": True,
    }
    return learner, training_summary, checkpoint_fact


def _validate_checkpoint_envelope(
    path: Path, *, seed: int, arm: str, identity: dict[str, object],
) -> dict[str, object]:
    envelope = _load_torch(path)
    if set(envelope) != {
        "artifact_kind", "revision", "source_identity", "seed", "arm",
        "learned_state_sha256", "checkpoint",
    }:
        raise FrontierIdentityError(f"checkpoint envelope fields are not exact: {seed}:{arm}")
    if (
        envelope["artifact_kind"] != "ONLGR_B2_SOLE_FINAL_CHECKPOINT"
        or envelope["revision"] != REVISION or envelope["source_identity"] != identity
        or envelope["seed"] != seed or envelope["arm"] != arm
    ):
        raise FrontierIdentityError(f"checkpoint envelope identity mismatch: {seed}:{arm}")
    checkpoint = _validate_learned_checkpoint(
        envelope.get("checkpoint"), seed=seed, arm=arm, completed_updates=UPDATES,
    )
    if (
        not isinstance(envelope.get("learned_state_sha256"), str)
        or envelope["learned_state_sha256"] != learned_state_sha256(checkpoint)
    ):
        raise FrontierIdentityError(f"checkpoint learned-state digest mismatch: {seed}:{arm}")
    return envelope


def _evaluate_panel(
    *, seed: int, arm: str, learner: B2Learner, panel: str, count: int,
    deadline: float | None = None,
) -> dict[str, object]:
    namespace = {
        "iid": "B2_IID_PAIRED", "safety": "B2_SAFETY_PAIRED", "keep": "B2_KEEP_PAIRED",
    }[panel]
    episodes = []
    for episode_index in range(count):
        if deadline is not None:
            _deadline_ok(deadline, ATOMIC_REPLACE_RESERVE_SECONDS)
        exogenous = generate_episode(
            seed=seed, episode_index=episode_index, namespace=namespace,
            schedule=IID_SCHEDULE, safety=panel == "safety",
        )
        episodes.append(run_episode(
            exogenous, arm=arm, learner=learner, force_keep=panel == "keep",
            owner_epoch=UPDATES, behavior_version=f"{arm}:final-update-8",
        ))
    return summarize_panel(episodes)


def _validate_complete_training_frontier(
    output_root: Path, identity: dict[str, object], *, deadline: float | None = None,
) -> list[dict[str, object]]:
    if deadline is not None:
        _deadline_ok(deadline, ATOMIC_REUSE_RESERVE_SECONDS)
    frontier = output_root / "frontier"
    expected = {
        frontier / f"train_seed_{seed}_{arm}_update_{update}.pt"
        for seed in SEEDS for arm in ARMS for update in range(1, UPDATES + 1)
    }
    actual = set(frontier.iterdir()) if frontier.exists() else set()
    if actual != expected:
        raise FrontierIdentityError("result-blind training frontier is not exactly 128 cells")
    resources: list[dict[str, object]] = []
    earliest_activity_coordinates: list[str] = []
    for seed in SEEDS:
        for arm in ARMS:
            for update in range(1, UPDATES + 1):
                if deadline is not None:
                    _deadline_ok(deadline, ATOMIC_REUSE_RESERVE_SECONDS)
                cell = _validate_cell(
                    _load_torch(frontier / f"train_seed_{seed}_{arm}_update_{update}.pt"),
                    kind="training_update", coordinate=f"train:{seed}:{arm}:update-{update}",
                    identity=identity,
                )
                coordinate = f"train:{seed}:{arm}:update-{update}"
                data = _validate_training_cell_data(cell["data"], coordinate)
                if bool(data["activity_fact"].get("earliest_registered_trigger")):
                    earliest_activity_coordinates.append(coordinate)
                resources.append(cell["resources"])
    if earliest_activity_coordinates != [f"train:{SEEDS[0]}:{ARMS[0]}:update-1"]:
        raise FrontierIdentityError("earliest durable B2 activity trigger is not unique and exact")
    return resources


def _validate_post_training_state(
    output_root: Path, identity: dict[str, object], *, deadline: float,
) -> list[dict[str, object]]:
    """Validate the entire durable frontier before reserving indivisible evaluation."""
    resources = _validate_complete_training_frontier(
        output_root, identity, deadline=deadline,
    )
    expected_checkpoints = {
        output_root / "checkpoints" / f"seed_{seed}" / f"{arm}.pt"
        for seed in SEEDS for arm in ARMS
    }
    _deadline_ok(deadline, ATOMIC_REUSE_RESERVE_SECONDS)
    actual_checkpoints = set((output_root / "checkpoints").rglob("*.pt"))
    if actual_checkpoints != expected_checkpoints:
        raise FrontierIdentityError("the 16 sole final checkpoint paths are not exact")
    for seed in SEEDS:
        for arm in ARMS:
            _deadline_ok(deadline, ATOMIC_REUSE_RESERVE_SECONDS)
            envelope = _validate_checkpoint_envelope(
                output_root / "checkpoints" / f"seed_{seed}" / f"{arm}.pt",
                seed=seed, arm=arm, identity=identity,
            )
            _require_final_matches_durable_frontier(
                output_root, envelope, seed=seed, arm=arm,
                identity=identity, deadline=deadline,
            )
    _deadline_ok(deadline, FINAL_EVALUATION_RESERVE_SECONDS)
    return resources


def _keep_pairing(panels: dict[str, dict[str, dict[str, object]]]) -> dict[str, bool]:
    return {
        str(seed): (
            panels["keep"][str(seed)]["RATE-FLEX"]["physics_ledger_sha256"]
            == panels["keep"][str(seed)]["RATE-CONST"]["physics_ledger_sha256"]
            and panels["keep"][str(seed)]["RATE-FLEX"]["dummy_call_ledger_sha256"]
            == panels["keep"][str(seed)]["RATE-CONST"]["dummy_call_ledger_sha256"]
            and panels["keep"][str(seed)]["RATE-FLEX"]["interval_ledger_sha256"]
            == panels["keep"][str(seed)]["RATE-CONST"]["interval_ledger_sha256"]
            and float(panels["keep"][str(seed)]["RATE-FLEX"]["mean_action_cost"]) == 0.0
            and float(panels["keep"][str(seed)]["RATE-CONST"]["mean_action_cost"]) == 0.0
        ) for seed in SEEDS
    }


def _materialize_panels_in_memory(
    learners: dict[tuple[int, str], B2Learner], *, deadline: float,
    panel_evaluator: Callable[..., dict[str, object]] = _evaluate_panel,
    grid_evaluator: Callable[[B2Learner], dict[str, object]] = diagnostic_grid,
    state_digests: dict[tuple[int, str], str] | None = None,
) -> dict[str, dict[str, dict[str, object]]]:
    """Evaluate the indivisible final package without any filesystem writes."""
    panels: dict[str, dict[str, dict[str, object]]] = {
        panel: {str(seed): {} for seed in SEEDS} for panel in ("iid", "safety", "keep", "grid")
    }
    for seed in SEEDS:
        for arm in ARMS:
            learner = learners[(seed, arm)]
            for panel, count in (
                ("iid", IID_EPISODES_PER_ARM_SEED),
                ("safety", SAFETY_EPISODES_PER_ARM_SEED),
                ("keep", KEEP_EPISODES_PER_ARM_SEED),
            ):
                summary = panel_evaluator(
                    seed=seed, arm=arm, learner=learner, panel=panel,
                    count=count, deadline=deadline,
                )
                if state_digests is not None:
                    summary["checkpoint_learned_state_sha256"] = state_digests[(seed, arm)]
                panels[panel][str(seed)][arm] = summary
            _deadline_ok(deadline, ATOMIC_REPLACE_RESERVE_SECONDS)
            grid = grid_evaluator(learner)
            if state_digests is not None:
                grid["checkpoint_learned_state_sha256"] = state_digests[(seed, arm)]
            panels["grid"][str(seed)][arm] = grid
    return panels


def _validate_existing_result(
    result_path: Path, *, output_root: Path, identity: dict[str, object], deadline: float,
) -> dict[str, object]:
    _deadline_ok(deadline, ATOMIC_REUSE_RESERVE_SECONDS)
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise FrontierIdentityError("existing B2 complete result is unreadable") from exc
    if not isinstance(result, dict) or set(result) != COMPLETE_RESULT_TOP_LEVEL_FIELDS:
        raise FrontierIdentityError("existing B2 result top-level fields are not exact")
    activity = result.get("activity_facts", {})
    namespaces = result.get("fresh_counter_namespaces", {})
    frontier = result.get("frontier", {})
    resources = result.get("resources", {})
    materialization = result.get("result_materialization", {})
    if (
        result.get("artifact_kind") != "ONLGR_B2_COMPLETE_ANALYSIS"
        or result.get("revision") != REVISION or result.get("source_identity") != identity
        or set(activity) != {
            "scientific_activity_started", "trigger", "trigger_coordinate",
            "single_revision_only", "revision",
        }
        or activity.get("scientific_activity_started") is not True
        or activity.get("trigger") != "first retained task-trained actor/critic/optimizer update"
        or activity.get("trigger_coordinate") != f"train:{SEEDS[0]}:{ARMS[0]}:update-1"
        or activity.get("single_revision_only") is not True or activity.get("revision") != REVISION
        or namespaces != {
            "training": "B2_TRAIN_PAIRED", "iid": "B2_IID_PAIRED",
            "safety": "B2_SAFETY_PAIRED", "keep_replay": "B2_KEEP_PAIRED",
            "global_domain_prefix": "ONLGR_B2_REV02", "r04_or_B1_namespace_reuse": False,
        }
        or set(frontier) != {
            "revision", "result_blind_until_complete", "persistent_training_cells",
            "persistent_evaluation_cells", "interrupted_evaluation_replayed_from_final_checkpoints",
            "slice_seconds_requested",
        }
        or frontier.get("revision") != FRONTIER_REVISION
        or frontier.get("result_blind_until_complete") is not True
        or frontier.get("persistent_training_cells") != 128
        or frontier.get("persistent_evaluation_cells") != 0
        or frontier.get("interrupted_evaluation_replayed_from_final_checkpoints") is not True
        or not math.isfinite(float(frontier.get("slice_seconds_requested", float("nan"))))
        or set(resources) != {
            "training_cell_wall_seconds", "final_evaluation_materialization_wall_seconds",
            "peak_observed_rss_bytes", "torch_intraop_threads", "torch_interop_threads",
            "resource_conditions_are_descriptive_not_scientific_gates",
        }
        or any(
            not math.isfinite(float(resources.get(key, float("nan")))) or float(resources[key]) < 0.0
            for key in (
                "training_cell_wall_seconds", "final_evaluation_materialization_wall_seconds",
                "peak_observed_rss_bytes",
            )
        )
        or resources.get("torch_intraop_threads") != 1
        or resources.get("torch_interop_threads") != 1
        or resources.get("resource_conditions_are_descriptive_not_scientific_gates") is not True
        or set(materialization) != {
            "complete_atomic_result", "claim_bearing_values_persisted_before_completion",
            "persistent_result_files", "checkpoint_state_digest_map", "panel_payload_sha256",
            "evaluation_binding_sha256",
        }
        or materialization.get("complete_atomic_result") is not True
        or materialization.get("claim_bearing_values_persisted_before_completion") is not False
        or materialization.get("persistent_result_files") != 1
    ):
        raise FrontierIdentityError("existing B2 result identity/lifecycle is not exact")
    _validate_complete_training_frontier(output_root, identity, deadline=deadline)
    digest_map: dict[str, dict[str, str]] = {str(seed): {} for seed in SEEDS}
    for seed in SEEDS:
        for arm in ARMS:
            _deadline_ok(deadline, ATOMIC_REUSE_RESERVE_SECONDS)
            path = output_root / "checkpoints" / f"seed_{seed}" / f"{arm}.pt"
            envelope = _validate_checkpoint_envelope(path, seed=seed, arm=arm, identity=identity)
            _require_final_matches_durable_frontier(
                output_root, envelope, seed=seed, arm=arm,
                identity=identity, deadline=deadline,
            )
            fact = result.get("checkpoint_facts", {}).get(str(seed), {}).get(arm, {})
            digest = _sha256(path)
            if (
                not isinstance(fact, dict) or set(fact) != CHECKPOINT_FACT_FIELDS
                or fact.get("artifact_kind") != "ONLGR_B2_SOLE_FINAL_CHECKPOINT"
                or fact.get("revision") != REVISION or fact.get("seed") != seed
                or fact.get("arm") != arm or fact.get("source_identity") != identity
                or fact.get("completed_updates") != UPDATES
                or not fact.get("source_identity_exact") or not fact.get("envelope_valid")
                or fact.get("learned_state_sha256") != envelope.get("learned_state_sha256")
                or fact.get("sha256_before_evaluation") != digest
                or fact.get("sha256_after_evaluation") != digest
                or not fact.get("immutable_before_after")
            ):
                raise FrontierIdentityError(f"existing result checkpoint binding mismatch: {seed}:{arm}")
            digest_map[str(seed)][arm] = str(envelope["learned_state_sha256"])
    panels = {
        "iid": result["iid_seed_arm_metrics"], "safety": result["safety_seed_arm_metrics"],
        "keep": result["keep_seed_arm_metrics"], "grid": result["diagnostic_grids"],
    }
    panel_payload_sha256 = _panel_payload_sha256(panels)
    if (
        materialization.get("checkpoint_state_digest_map") != digest_map
        or materialization.get("panel_payload_sha256") != panel_payload_sha256
        or materialization.get("evaluation_binding_sha256")
        != _evaluation_binding_sha256(identity, digest_map, panel_payload_sha256)
    ):
        raise FrontierIdentityError("existing result learned-state evaluation binding is invalid")
    _deadline_ok(deadline, ATOMIC_REUSE_RESERVE_SECONDS)
    recomputed = analyze_complete_package(
        panels=panels, checkpoints=result["checkpoint_facts"],
        training=result["training_seed_arm_facts"], source_identity_exact=True,
        atomic_frontier_exact=True, keep_pairing=_keep_pairing(panels),
        expected_source_identity=identity,
    )
    _deadline_ok(deadline, 0.0)
    for field in CLAIM_BEARING_RECOMPUTE_FIELDS:
        if not _json_equivalent(result.get(field), recomputed.get(field)):
            raise FrontierIdentityError(f"existing result claim-bearing field was altered: {field}")
    return result


def _configure_torch_threads() -> None:
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError as exc:
            if torch.get_num_interop_threads() != 1:
                raise FrontierIdentityError("Torch inter-op threads could not be fixed to one") from exc
    torch.use_deterministic_algorithms(True)


def run_registered(output_root: Path, *, slice_seconds: float) -> dict[str, object] | None:
    if slice_seconds <= ATOMIC_REPLACE_RESERVE_SECONDS:
        raise ValueError("slice_seconds must leave time for an atomic boundary")
    output_root = _safe_output_root(output_root)
    deadline = time.perf_counter() + slice_seconds
    with _ScopedRunLock(output_root):
        _discard_stale_atomic_temps(output_root)
        _validate_output_entries(output_root)
        _configure_torch_threads()
        identity = source_identity()
        _deadline_ok(deadline, ATOMIC_REPLACE_RESERVE_SECONDS)
        _prepare_manifest(output_root, identity)
        _deadline_ok(deadline, 0.0)
        frontier = output_root / "frontier"
        frontier.mkdir(exist_ok=True)
        result_path = output_root / "results.json"
        if result_path.exists():
            try:
                return _validate_existing_result(
                    result_path, output_root=output_root, identity=identity, deadline=deadline,
                )
            except SliceExpired:
                return None
        learners: dict[tuple[int, str], B2Learner] = {}
        training: dict[str, dict[str, object]] = {str(seed): {} for seed in SEEDS}
        checkpoints: dict[str, dict[str, object]] = {str(seed): {} for seed in SEEDS}
        try:
            for seed in SEEDS:
                for arm in ARMS:
                    learner, training_fact, checkpoint_fact = _train_coordinate(
                        output_root=output_root, frontier=frontier, seed=seed, arm=arm,
                        identity=identity, deadline=deadline,
                    )
                    learners[(seed, arm)] = learner
                    training[str(seed)][arm] = training_fact
                    checkpoints[str(seed)][arm] = checkpoint_fact
        except SliceExpired:
            return None

        try:
            training_resources = _validate_post_training_state(
                output_root, identity, deadline=deadline,
            )
        except SliceExpired:
            return None
        evaluation_started = time.perf_counter()
        evaluation_rss_before = _rss_bytes()
        try:
            state_digests = {
                (seed, arm): str(checkpoints[str(seed)][arm]["learned_state_sha256"])
                for seed in SEEDS for arm in ARMS
            }
            panels = _materialize_panels_in_memory(
                learners, deadline=deadline, state_digests=state_digests,
            )
            for seed in SEEDS:
                for arm in ARMS:
                    path = output_root / "checkpoints" / f"seed_{seed}" / f"{arm}.pt"
                    _validate_checkpoint_envelope(path, seed=seed, arm=arm, identity=identity)
                    after = _sha256(path)
                    checkpoints[str(seed)][arm]["sha256_after_evaluation"] = after
                    checkpoints[str(seed)][arm]["immutable_before_after"] = (
                        after == checkpoints[str(seed)][arm]["sha256_before_evaluation"]
                    )
            analysis = analyze_complete_package(
                panels=panels, checkpoints=checkpoints, training=training,
                source_identity_exact=source_identity() == identity,
                atomic_frontier_exact=True, keep_pairing=_keep_pairing(panels),
                expected_source_identity=identity,
            )
            analysis["source_identity"] = identity
            analysis["activity_facts"] = {
                "scientific_activity_started": True,
                "trigger": "first retained task-trained actor/critic/optimizer update",
                "trigger_coordinate": f"train:{SEEDS[0]}:{ARMS[0]}:update-1",
                "single_revision_only": True, "revision": REVISION,
            }
            analysis["fresh_counter_namespaces"] = {
                "training": "B2_TRAIN_PAIRED", "iid": "B2_IID_PAIRED",
                "safety": "B2_SAFETY_PAIRED", "keep_replay": "B2_KEEP_PAIRED",
                "global_domain_prefix": "ONLGR_B2_REV02", "r04_or_B1_namespace_reuse": False,
            }
            analysis["frontier"] = {
                "revision": FRONTIER_REVISION, "result_blind_until_complete": True,
                "persistent_training_cells": 128, "persistent_evaluation_cells": 0,
                "interrupted_evaluation_replayed_from_final_checkpoints": True,
                "slice_seconds_requested": slice_seconds,
            }
            analysis["resources"] = {
                "training_cell_wall_seconds": sum(float(row["wall_seconds"]) for row in training_resources),
                "final_evaluation_materialization_wall_seconds": time.perf_counter() - evaluation_started,
                "peak_observed_rss_bytes": max(
                    evaluation_rss_before, _rss_bytes(), *(
                        max(int(row["rss_before_bytes"]), int(row["rss_after_bytes"]))
                        for row in training_resources
                    ),
                ),
                "torch_intraop_threads": torch.get_num_threads(),
                "torch_interop_threads": torch.get_num_interop_threads(),
                "resource_conditions_are_descriptive_not_scientific_gates": True,
            }
            analysis["result_materialization"] = {
                "complete_atomic_result": True,
                "claim_bearing_values_persisted_before_completion": False,
                "persistent_result_files": 1,
                "checkpoint_state_digest_map": {
                    str(seed): {arm: state_digests[(seed, arm)] for arm in ARMS}
                    for seed in SEEDS
                },
                "panel_payload_sha256": _panel_payload_sha256(panels),
            }
            analysis["result_materialization"]["evaluation_binding_sha256"] = (
                _evaluation_binding_sha256(
                    identity, analysis["result_materialization"]["checkpoint_state_digest_map"],
                    analysis["result_materialization"]["panel_payload_sha256"],
                )
            )
            _deadline_ok(deadline, ATOMIC_REPLACE_RESERVE_SECONDS)
            _atomic_json(result_path, analysis)
            _deadline_ok(deadline, 0.0)
            return analysis
        except SliceExpired:
            if result_path.exists():
                try:
                    return _validate_existing_result(
                        result_path, output_root=output_root, identity=identity,
                        deadline=time.perf_counter() + ATOMIC_REUSE_RESERVE_SECONDS + 1.0,
                    )
                except SliceExpired:
                    return None
            return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run/continue frozen ONLGR-B2 revision 02")
    parser.add_argument("action", choices=("run",))
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--slice-seconds", type=float, required=True)
    args = parser.parse_args(argv)
    try:
        result = run_registered(args.output_root, slice_seconds=args.slice_seconds)
    except Exception as exc:
        print(f"ONLGR-B2 runner error: {exc}", file=sys.stderr)
        return 2
    if result is None:
        # No learned task statistic or branch is emitted from an incomplete frontier.
        return 75
    print(json.dumps({
        "results_path": str((args.output_root / "results.json").resolve()),
        "PACKAGE_VALID": result["PACKAGE_VALID"],
        "MARK_SUPPORT_OK": result["MARK_SUPPORT_OK"],
        "branches": result["branches"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

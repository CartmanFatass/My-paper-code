"""FRRIE R09 A03 tape-isolation probe: production tapes without learner or native work."""

from __future__ import annotations

import hashlib
import json
import sys
import time
import traceback
from dataclasses import fields
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from .contracts.core import canonical_json_bytes
from .rng import AddressedRNG
from .tapes import generate_episode_tape, generate_training_origin_schedule

OBJECT_ID = "FRRIE-R09-SEGFAULT-A03-TAPE-ISOLATION-20260906"
ROOT_HEX = "0000000000000000000000000000000000000000000000000000000000000003"
SEED_LABEL = "FRRIE-B09-CONTACT-BLOCK-003"
# Hard-coded from b01_contact_r02/semantics.py:27; that module imports torch.
ROSTERS = (9, 15)
ARRAY_FIELDS = (
    "event_times",
    "detection_uniform",
    "uplink_uniform",
    "base_uniform",
    "action_uniform",
)


def training_inputs_no_torch(
    root: bytes, seed_label: str, update: int,
) -> tuple[Any, ...]:
    rng = AddressedRNG(root)
    for roster in ROSTERS:
        generate_training_origin_schedule(
            rng, seed_block=seed_label, roster=roster, update=update, purpose="TRAIN",
        )
    roster_order = ROSTERS * 32
    return tuple(
        generate_episode_tape(
            rng, seed_block=seed_label, purpose="TRAIN", roster=roster,
            update=update, episode=position // 2,
        )
        for position, roster in enumerate(roster_order)
    )


def evaluation_tapes(root: bytes, seed_label: str, episodes: int = 256) -> tuple[Any, ...]:
    from .b01_contact_r02.tapes import evaluation_tape

    return tuple(
        evaluation_tape(root, seed_label=seed_label, roster=roster, episode=episode)
        for roster in ROSTERS
        for episode in range(episodes)
    )


def _tape_canonical_bytes(tape: Any) -> bytes:
    scalars: dict[str, Any] = {}
    parts: list[bytes] = []
    named = {item.name: getattr(tape, item.name) for item in fields(tape)}
    for name, value in named.items():
        if isinstance(value, np.ndarray):
            continue
        scalars[name] = value
    parts.append(canonical_json_bytes(scalars))
    for name in ARRAY_FIELDS:
        parts.append(np.ascontiguousarray(named[name]).tobytes())
    return b"".join(parts)


def tape_digest(tapes: Sequence[Any] | Iterable[Any]) -> str:
    digest = hashlib.sha256()
    for tape in tapes:
        digest.update(_tape_canonical_bytes(tape))
    return digest.hexdigest()


def _peak_rss_bytes() -> int | None:
    if not sys.platform.startswith("linux"):
        return None
    import resource

    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _module_version(name: str) -> str | None:
    module = sys.modules.get(name)
    if module is None:
        return None
    version = getattr(module, "__version__", None)
    return None if version is None else str(version)


def _process_facts() -> dict[str, Any]:
    return {
        "torch_in_sys_modules": "torch" in sys.modules,
        "numpy_in_sys_modules": "numpy" in sys.modules,
        "torch_version": _module_version("torch"),
        "numpy_version": _module_version("numpy"),
        "sys_flags": {name: getattr(sys.flags, name) for name in sys.flags.__match_args__},
        "sys_version": sys.version,
        "sys_executable": sys.executable,
        "trace_active": sys.gettrace() is not None,
        "peak_rss_bytes": _peak_rss_bytes(),
    }


def _phase(
    name: str, tapes: Sequence[Any], started: float,
) -> dict[str, Any]:
    nbytes = 0
    for tape in tapes:
        for field in ARRAY_FIELDS:
            nbytes += int(getattr(tape, field).nbytes)
    return {
        "phase": name,
        "wall_seconds": time.perf_counter() - started,
        "tape_count": len(tapes),
        "nbytes": nbytes,
        "digest": tape_digest(tapes),
    }


def cost_law(arm: str, repeat: int, updates: int, eval_episodes: int) -> dict[str, Any]:
    training = 64 * updates * repeat
    evaluation = (2 * eval_episodes * repeat) if arm == "T1" else 0
    return {
        "law": (
            "wall scales with 64 training tapes per update, plus 2*eval_episodes "
            "evaluation tapes on T1, times repetitions"
        ),
        "training_tapes": training,
        "evaluation_tapes": evaluation,
        "unit": "tape",
    }


def run_arm(
    arm: str,
    repeat: int,
    out_dir: str | Path,
    *,
    updates: int = 2,
    eval_episodes: int = 256,
    root: bytes | None = None,
    seed_label: str = SEED_LABEL,
    launch_sha: str | None = None,
    admission_receipt: str | Path | None = None,
) -> dict[str, Any]:
    if arm not in {"T0", "T1"}:
        raise ValueError("arm must be T0 or T1")
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    if root is None:
        root = bytes.fromhex(ROOT_HEX)
    admission = None
    admission_path = None
    if admission_receipt is not None:
        admission_path = Path(admission_receipt)
        if not admission_path.is_file():
            raise FileNotFoundError(f"admission receipt missing: {admission_path}")
        admission = json.loads(admission_path.read_text(encoding="utf-8"))
    summary: dict[str, Any] = {
        "object": OBJECT_ID,
        "arm": arm,
        "repeat": repeat,
        "updates": updates,
        "eval_episodes": eval_episodes,
        "root_hex": root.hex(),
        "seed_label": seed_label,
        "argv": list(sys.argv),
        "launch_sha": launch_sha,
        "admission_receipt": None if admission_path is None else str(admission_path),
        "admission": admission,
        "cost_law": cost_law(arm, repeat, updates, eval_episodes),
        "repetitions": [],
        "exception": None,
        "torch_present_at_work_start": None,
    }
    production_tapes = None
    caught: BaseException | None = None
    try:
        if arm == "T1":
            from .b01_contact_r02 import tapes as production_tapes
        summary["torch_present_at_work_start"] = "torch" in sys.modules
        for index in range(repeat):
            record: dict[str, Any] = {"index": index, "phases": []}
            summary["repetitions"].append(record)
            if arm == "T1":
                started = time.perf_counter()
                tapes = evaluation_tapes(root, seed_label, episodes=eval_episodes)
                record["phases"].append(_phase("evaluation", tapes, started))
            for update in range(1, updates + 1):
                started = time.perf_counter()
                if arm == "T0":
                    tapes = training_inputs_no_torch(root, seed_label, update)
                else:
                    tapes, _origins = production_tapes.production_training_inputs(
                        root, seed_label, update,
                    )
                record["phases"].append(_phase(f"training_update_{update}", tapes, started))
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        summary["exception"] = traceback.format_exc()
        caught = exc
    summary.update(_process_facts())
    (destination / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    if caught is not None:
        raise caught
    return summary

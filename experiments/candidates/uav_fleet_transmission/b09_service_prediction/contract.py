"""Frozen B09 addresses, source binding and compact record utilities (no native calls)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import resource
import time

import numpy as np

DIRECTION = "uav_fleet_transmission"
OBJECT = "fleet-b09-lawful-service-prediction-v1"
ROOT = Path(__file__).resolve().parents[4]
HORIZON = 3000
WORLD_SEEDS = tuple(range(29890001, 29890033))
ENGINEERING_SEED = 29890099
SEED_ROOT = 29890000
ARMS = ("C", "H", "F")
EVENTS = ("continued", "new", "ambiguous", "expired", "discarded", "cap_drop")
MODEL_SEED = 0
SAMPLES = (10, 20, 30)
# Exact same-source/node replay for policy/model traces. Native derived metrics
# retain the B08 reader's explicitly named tolerance, never an adaptive slack.
BS_SOURCES = ("absent", "inferred", "observed-current", "observed-memory")


def jobs(phase: str) -> list[dict]:
    if phase == "engineering":
        return [dict(job_key=f"{ENGINEERING_SEED}/{arm}", seed=ENGINEERING_SEED,
                     arm=arm, limit=61) for arm in ("REFERENCE", *ARMS)]
    if phase != "scientific":
        raise ValueError("unknown phase")
    result = []
    for index, seed in enumerate(WORLD_SEEDS):
        shift = index % 3
        for arm in ARMS[shift:] + ARMS[:shift]:
            result.append(dict(job_key=f"{seed}/{arm}", seed=seed, arm=arm, limit=HORIZON))
    return result


def json_value(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def write_json(path: Path, value) -> None:
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True,
                                    default=json_value, allow_nan=False) + "\n")
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(path: Path) -> dict:
    stat = Path(path).stat()
    return dict(sha256=sha256(path), bytes=stat.st_size, allocated_bytes=stat.st_blocks * 512)


def array_digest(*arrays) -> str:
    digest = hashlib.sha256()
    for value in arrays:
        array = np.ascontiguousarray(value)
        digest.update(str(array.dtype).encode())
        digest.update(str(array.shape).encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def source_binding(root=ROOT) -> dict:
    root = Path(root)
    frozen = json.loads((Path(__file__).with_name("frozen_sources.json")).read_text())
    for name, expected in frozen["files"].items():
        if sha256(root / name) != expected:
            raise ValueError("original host/controller source differs: " + name)
    names = set(frozen["files"])
    names.update(str(path.relative_to(root)) for path in
                 (root / "experiments/candidates/uav_fleet_transmission/b09_service_prediction").glob("*.py"))
    names.add("experiments/candidates/uav_fleet_transmission/b09_service_prediction/frozen_sources.json")
    return dict(original_source_sha=frozen["original_source_sha"],
                files={name: sha256(root / name) for name in sorted(names)})


def expected_counts(arm: str, length: int) -> dict:
    """Fixed ingestion/clock counts; candidate/model work is measured, not inferred."""
    plans = (length + 29) // 30
    return dict(proposals=length, plans=plans,
                canonicalizations=length if arm in ("H", "F") else plans,
                associations=length if arm in ("H", "F") else 0,
                current_projections=plans if arm in ("H", "F") else 0,
                future_projections=3 * plans if arm == "F" else 0)


def sum_counts(items) -> dict:
    result = {}
    for item in items:
        for key, value in item.items():
            result[key] = result.get(key, 0) + int(value)
    return result


def telemetry(wall: float, cpu: float) -> dict:
    return dict(wall_seconds=time.perf_counter() - wall,
                cpu_seconds=time.process_time() - cpu,
                peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def equal(actual, expected, label: str, atol=0.0) -> None:
    a, b = np.asarray(actual), np.asarray(expected)
    if a.shape != b.shape:
        raise AssertionError(f"{label}: shape {a.shape} != {b.shape}")
    if a.dtype.names:
        if a.dtype != b.dtype:
            raise AssertionError(label + ": structured dtype mismatch")
        for name in a.dtype.names:
            equal(a[name], b[name], label + "/" + name, atol)
        return
    if a.dtype.kind in "fc" or b.dtype.kind in "fc":
        good = np.allclose(a, b, atol=atol, rtol=0.0, equal_nan=True) if atol else np.array_equal(a, b, equal_nan=True)
    else:
        good = np.array_equal(a, b)
    if not good:
        raise AssertionError(label + ": values differ")

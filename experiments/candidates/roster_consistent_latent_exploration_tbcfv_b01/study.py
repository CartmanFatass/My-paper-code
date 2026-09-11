"""B01 two-arm single-seed study: authority seam, train, evaluate, publish."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Mapping, Sequence

import numpy as np
import torch

from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import (
    C1P1,
    FLEX,
    INDEPENDENT_NEAREST,
    NONZERO_UPDATE_NORM,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_contract import (
    _derive_block_digest,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_runner import (
    EpisodeCoordinate,
    SemanticRNG,
    execute_learned_batch,
    execute_scripted_batch,
    initialize_block_models,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.inference import (
    HELDOUT_CELLS,
    TRAINING_CELLS,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import (
    TBCFVModel,
    apply_registered_block_update,
    exact_advantage_loss,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.native_backend import (
    NativeBackendError,
    native_artifact_identity,
)

OBJECT_ID = "RCLE-TBCFV-B01-PERSIST-VS-FLEX"
IDENTITY = OBJECT_ID
SEED = 17
BLOCK_INDEX = 0
SEED_KEY_ASCII = f"{OBJECT_ID}/seed/{SEED}"
PREPARATION_KEY_ASCII = f"{OBJECT_ID}/seed/{SEED}/preparation"
B01_ARMS = (C1P1, FLEX)
PRIMARY_CELLS = (
    "8_to_12.ACTIVE_CONTINUATION",
    "12_to_8.ACTIVE_CONTINUATION",
)
DEFAULT_UPDATES = 200
DEFAULT_EVAL_EPISODES = 256
SELECTED_ROW_MODULUS = 8


class ArmWallExpired(Exception):
    """Internal arm wall cap reached (poll or SIGALRM)."""

    def __init__(self, message: str = "wall_cap") -> None:
        super().__init__(message)
        self.evaluated_rows: list[dict[str, object]] = []
        self.evaluated_cells: list[str] = []


@dataclass(frozen=True)
class B01BlockAuthority:
    """Minimal authority SemanticRNG and the batch executors actually read.

    Read attributes: ``require_active``, ``block_root_digest``, and
    ``certificate["native"]`` with ``source_sha256`` and ``build_key`` matching
    ``bind_native_backend()`` (default build root). No lease, expiry, or
    20-block range.
    """

    certificate: Mapping[str, object]
    block_index: int
    root_digest: str

    def require_active(self, *, now: datetime) -> None:
        del now

    def block_root_digest(self, block_index: int) -> str:
        if block_index != self.block_index:
            raise ValueError("B01 block authority is bound to a single block index")
        return self.root_digest


def seed_root_key(ascii_label: str = SEED_KEY_ASCII) -> bytes:
    return hashlib.sha256(ascii_label.encode("ascii")).digest()


def block_digest_hex(
    key: bytes, identity: str = IDENTITY, index: int = BLOCK_INDEX
) -> str:
    return _derive_block_digest(key, identity, index)


def native_certificate_payload(
    *, build_root: str | Path | None = None
) -> dict[str, object]:
    """Fill certificate['native'] from the built backend SemanticRNG will load.

    SemanticRNG always calls bind_native_backend() with the default root, so
    arm/reference/executability certificates use build_root=None. The build
    mode may pass a request-specific root; that artifact's build_key differs
    because the resolved path is part of the visible key.
    """

    observed = native_artifact_identity(build_root=build_root)
    toolchain = observed["toolchain"]
    assert isinstance(toolchain, Mapping)
    return {
        "source_sha256": observed["source_sha256"],
        "build_key": observed["build_key"],
        "artifact_sha256": observed["sha256"],
        "path": observed["path"],
        "abi": dict(observed["abi"]),  # type: ignore[arg-type]
        "runtime_abi": dict(observed["runtime_abi"]),  # type: ignore[arg-type]
        "resolved_build_root": observed["resolved_build_root"],
        "load_seconds": observed["load_seconds"],
        "toolchain": {
            "compiler_path": toolchain["compiler_path"],
            "compiler_sha256": toolchain["compiler_sha256"],
            "compile_flags": list(toolchain["compile_flags"]),  # type: ignore[arg-type]
        },
    }


def make_semantic_rng(
    *, key_ascii: str = SEED_KEY_ASCII, now: datetime | None = None
) -> tuple[B01BlockAuthority, SemanticRNG]:
    digest = block_digest_hex(seed_root_key(key_ascii))
    authority = B01BlockAuthority(
        certificate={"native": native_certificate_payload()},
        block_index=BLOCK_INDEX,
        root_digest=digest,
    )
    rng = SemanticRNG(
        authority, BLOCK_INDEX, now=now or datetime.now(timezone.utc)
    )
    return authority, rng


def restrict_two_arms(models: Mapping[str, TBCFVModel]) -> dict[str, TBCFVModel]:
    return {arm: models[arm] for arm in B01_ARMS}


def initialize_b01_models(rng: SemanticRNG) -> dict[str, TBCFVModel]:
    return restrict_two_arms(initialize_block_models(rng))


def flat_parameters(model: TBCFVModel) -> torch.Tensor:
    return torch.cat([parameter.detach().reshape(-1) for parameter in model.parameters()])


def peak_rss_bytes() -> int | None:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class _Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = _Counters()
        counters.cb = ctypes.sizeof(counters)
        get_current_process = ctypes.windll.kernel32.GetCurrentProcess
        get_current_process.restype = wintypes.HANDLE
        get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
        get_process_memory_info.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(_Counters),
            wintypes.DWORD,
        ]
        if not get_process_memory_info(
            get_current_process(),
            ctypes.byref(counters),
            counters.cb,
        ):
            return None
        return int(counters.PeakWorkingSetSize)
    try:
        import resource
    except ImportError:
        return None
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def process_cpu_seconds() -> float:
    try:
        import resource
    except ImportError:
        return time.process_time()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    total = float(usage.ru_utime + usage.ru_stime)
    if hasattr(resource, "RUSAGE_CHILDREN"):
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        total += float(children.ru_utime + children.ru_stime)
    return total


def directory_bytes(path: Path) -> int:
    total = 0
    if not path.is_dir():
        return 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            total += (Path(root) / name).stat().st_size
    return total


def json_ready(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (np.floating, float)):
        return float(value)
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(json_ready(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="ascii",
    )


def native_available() -> tuple[bool, str]:
    try:
        native_artifact_identity()
    except (NativeBackendError, OSError) as exc:
        return False, f"{type(exc).__name__}: {exc}"
    return True, ""


def check_wall(started: float, wall_cap: float) -> None:
    if time.perf_counter() - started > wall_cap:
        raise ArmWallExpired("wall_cap")


def load_control_summary(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError(f"control summary is missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"control summary is unparsable: {path}: {type(exc).__name__}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(
            f"control summary is unparsable: {path}: JSON root is "
            f"{type(payload).__name__}, expected object"
        )
    return payload


def validate_control_summary(
    control: Mapping[str, object],
    *,
    updates: int,
    eval_episodes: int,
    block_digest: str,
    object_id: str = OBJECT_ID,
    seed: int = SEED,
) -> dict[str, object]:
    """Card asymmetric-exposure stop: C1P1 COMPLETE, same object/seed/digest/eval/updates."""

    def require(field: str, observed: object, expected: object) -> None:
        if observed != expected:
            raise ValueError(
                f"control summary field {field} mismatch: "
                f"observed {observed!r}, expected {expected!r}"
            )

    require("arm", control.get("arm"), C1P1)
    require("status", control.get("status"), "COMPLETE")
    require("object", control.get("object"), object_id)
    require("seed", control.get("seed"), seed)
    require("block_digest_hex", control.get("block_digest_hex"), block_digest)
    configuration = control.get("configuration")
    if not isinstance(configuration, Mapping):
        raise ValueError(
            "control summary field configuration.eval_episodes_per_cell mismatch: "
            f"observed {configuration!r}, expected mapping with eval_episodes_per_cell"
        )
    require(
        "configuration.eval_episodes_per_cell",
        configuration.get("eval_episodes_per_cell"),
        eval_episodes,
    )
    counts = control.get("counts")
    if not isinstance(counts, Mapping):
        raise ValueError(
            "control summary field counts.completed_updates mismatch: "
            f"observed {counts!r}, expected mapping with completed_updates"
        )
    require("counts.completed_updates", counts.get("completed_updates"), updates)
    return {
        "control_arm": control["arm"],
        "control_completed_updates": counts["completed_updates"],
        "control_block_digest_hex": control["block_digest_hex"],
    }


def load_and_validate_control_summary(
    path: Path,
    *,
    updates: int,
    eval_episodes: int,
    block_digest: str,
) -> tuple[dict[str, object], dict[str, object]]:
    control = load_control_summary(path)
    identity = validate_control_summary(
        control,
        updates=updates,
        eval_episodes=eval_episodes,
        block_digest=block_digest,
    )
    identity["control_summary_path"] = str(path)
    return control, identity


def scenario_row(cell: str, index: int, arm: str, episode: object) -> dict[str, object]:
    y = getattr(episode, "Y", None)
    return {
        "cell": cell,
        "index": int(index),
        "arm": arm,
        "tau": float(episode.tau),  # type: ignore[attr-defined]
        "U": float(episode.U),  # type: ignore[attr-defined]
        "F": float(episode.F),  # type: ignore[attr-defined]
        "Y": None if y is None else float(y),
    }


def heldout_batches(
    cell: str, eval_episodes: int, *, block_index: int = BLOCK_INDEX
) -> list[tuple[EpisodeCoordinate, ...]]:
    batches: list[tuple[EpisodeCoordinate, ...]] = []
    start = 0
    remaining = eval_episodes
    while remaining:
        width = 32 if remaining >= 32 else 8 if remaining >= 8 else 1
        batches.append(
            tuple(
                EpisodeCoordinate(
                    block_index, cell, start + row, row % SELECTED_ROW_MODULUS
                )
                for row in range(width)
            )
        )
        start += width
        remaining -= width
    return batches


def _mean(values: Sequence[float]) -> float:
    return float(math.fsum(values) / len(values))


def execute_b01_training_update(
    model: TBCFVModel,
    arm: str,
    rng: SemanticRNG,
    update: int,
    baselines: torch.Tensor,
) -> tuple[torch.Tensor, dict[str, int], dict[str, object], bool]:
    results = []
    cells: list[int] = []
    for cell_start in range(0, len(TRAINING_CELLS), 4):
        selected = TRAINING_CELLS[cell_start : cell_start + 4]
        coordinates = tuple(
            EpisodeCoordinate(rng.block_index, cell, update, row)
            for cell in selected
            for row in range(8)
        )
        batch = execute_learned_batch(model, arm, rng, coordinates, training=True)
        results.extend(batch)
        for cell_index in range(cell_start, cell_start + len(selected)):
            cells.extend([cell_index] * 8)
    if len(results) != 64:
        raise RuntimeError("one B01 training update did not produce 64 episodes")
    returns = torch.tensor([item.Y for item in results], dtype=torch.float64)
    cell_indices = torch.tensor(cells, dtype=torch.int64)
    model.zero_grad(set_to_none=True)
    loss = exact_advantage_loss(
        returns,
        cell_indices,
        baselines,
        [torch.stack(item.plan_scores) for item in results],
        [torch.stack(item.claim_scores) for item in results],
    )
    if not bool(torch.isfinite(loss)):
        raise RuntimeError("training loss is nonfinite")
    loss.backward()
    audit = apply_registered_block_update(model, baselines, returns, cell_indices)
    per_cell = []
    for cell_index, cell in enumerate(TRAINING_CELLS):
        chosen = [results[row] for row in range(64) if cells[row] == cell_index]
        per_cell.append(
            {
                "cell": cell,
                "episodes": len(chosen),
                "Y_mean": _mean([float(item.Y) for item in chosen]),
                "tau_mean": _mean([float(item.tau) for item in chosen]),
                "U_mean": _mean([float(item.U) for item in chosen]),
                "F_mean": _mean([float(item.F) for item in chosen]),
            }
        )
    curve = {
        "update": update,
        "Y_mean": float(returns.mean().item()),
        "per_cell": per_cell,
        "nonzero": audit.parameter_update.nonzero,
        "parameter_delta_norm": audit.parameter_update.parameter_delta_norm,
        "raw_gradient_norm": audit.parameter_update.raw_gradient_norm,
        "event_order": list(audit.event_order),
    }
    counts = {
        "training_episodes": 64,
        "environment_ticks": 64 * 64,
        "agent_ticks": sum(item.agent_ticks for item in results),
        "agent_claim_decisions": sum(item.claim_decisions for item in results),
    }
    return audit.updated_baselines, counts, curve, audit.parameter_update.nonzero


def evaluate_learned(
    model: TBCFVModel,
    arm: str,
    rng: SemanticRNG,
    eval_episodes: int,
    *,
    started: float,
    wall_cap: float,
) -> tuple[list[dict[str, object]], list[str]]:
    rows: list[dict[str, object]] = []
    evaluated: list[str] = []
    try:
        with torch.no_grad():
            for cell in HELDOUT_CELLS:
                check_wall(started, wall_cap)
                cell_rows: list[dict[str, object]] = []
                for coordinates in heldout_batches(cell, eval_episodes):
                    episodes = execute_learned_batch(
                        model, arm, rng, coordinates, training=False
                    )
                    for coordinate, episode in zip(coordinates, episodes):
                        cell_rows.append(
                            scenario_row(
                                cell, coordinate.update_or_scenario, arm, episode
                            )
                        )
                rows.extend(cell_rows)
                evaluated.append(cell)
    except ArmWallExpired as exc:
        exc.evaluated_rows = rows
        exc.evaluated_cells = evaluated
        raise
    return rows, evaluated


def evaluate_scripted(
    rng: SemanticRNG, eval_episodes: int, *, arm: str = INDEPENDENT_NEAREST
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for cell in HELDOUT_CELLS:
        for coordinates in heldout_batches(cell, eval_episodes):
            episodes = execute_scripted_batch(arm, rng, coordinates)
            for coordinate, episode in zip(coordinates, episodes):
                rows.append(
                    scenario_row(cell, coordinate.update_or_scenario, arm, episode)
                )
    return rows


def _group(rows: Sequence[Mapping[str, object]]) -> dict[str, list[Mapping[str, object]]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["cell"]), []).append(row)
    for cell in grouped:
        grouped[cell] = sorted(grouped[cell], key=lambda item: int(item["index"]))  # type: ignore[arg-type, return-value]
    return grouped


def paired_difference_se(
    treatment: Sequence[float], flex: Sequence[float]
) -> float | None:
    if len(treatment) != len(flex) or len(treatment) <= 1:
        return None
    paired = [float(right) - float(left) for left, right in zip(treatment, flex)]
    return float(
        np.std(np.asarray(paired, dtype=np.float64), ddof=1) / math.sqrt(len(paired))
    )


def se_of_mean_of_independent_ses(ses: Sequence[float | None]) -> float | None:
    """SE of the arithmetic mean of independent path differences: sqrt(sum se_i^2) / k."""

    if not ses or any(item is None for item in ses):
        return None
    return float(math.sqrt(math.fsum(float(item) ** 2 for item in ses)) / len(ses))


def cell_endpoint_means(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}
    for cell, items in _group(rows).items():
        taus = [float(item["tau"]) for item in items]
        us = [float(item["U"]) for item in items]
        fs = [float(item["F"]) for item in items]
        ys = [item["Y"] for item in items]
        y_values = [float(value) for value in ys if value is not None]
        summary[cell] = {
            "episodes": len(items),
            "tau_mean": _mean(taus),
            "U_mean": _mean(us),
            "F_mean": _mean(fs),
            "Y_mean": None if not y_values else _mean(y_values),
            "tau40_fraction": sum(1 for value in taus if value == 40.0) / len(taus),
            "tau40_count": sum(1 for value in taus if value == 40.0),
        }
    return summary


def eight_cell_mean(cell_summary: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    cells = list(HELDOUT_CELLS)
    def field(name: str) -> float:
        return _mean([float(cell_summary[cell][name]) for cell in cells])  # type: ignore[arg-type]

    y_values = [cell_summary[cell]["Y_mean"] for cell in cells]
    return {
        "cells": cells,
        "tau_mean": field("tau_mean"),
        "U_mean": field("U_mean"),
        "F_mean": field("F_mean"),
        "Y_mean": None
        if any(value is None for value in y_values)
        else _mean([float(value) for value in y_values]),  # type: ignore[arg-type]
        "tau40_fraction": field("tau40_fraction"),
    }


def publish_paired_primary(
    treatment_rows: Sequence[Mapping[str, object]],
    flex_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """FLEX − C1P1 on the two ACTIVE_CONTINUATION held-out paths; positive favours treatment."""

    treatment = _group(treatment_rows)
    flex = _group(flex_rows)
    paths: list[dict[str, object]] = []
    differences: list[float] = []
    tau_ses: list[float | None] = []
    for cell in PRIMARY_CELLS:
        left = treatment[cell]
        right = flex[cell]
        if [int(item["index"]) for item in left] != [int(item["index"]) for item in right]:
            raise ValueError(f"paired scenario indices differ on {cell}")
        t_tau = [float(item["tau"]) for item in left]
        f_tau = [float(item["tau"]) for item in right]
        t_u = [float(item["U"]) for item in left]
        f_u = [float(item["U"]) for item in right]
        d_tau = _mean(f_tau) - _mean(t_tau)
        differences.append(d_tau)
        tau_se = paired_difference_se(t_tau, f_tau)
        u_se = paired_difference_se(t_u, f_u)
        tau_ses.append(tau_se)
        paths.append(
            {
                "path": cell.split(".", 1)[0],
                "cell": cell,
                "n": len(left),
                "c1p1_tau_mean": _mean(t_tau),
                "flex_tau_mean": _mean(f_tau),
                "difference_flex_minus_c1p1": d_tau,
                "c1p1_tau40_fraction": sum(1 for value in t_tau if value == 40.0) / len(t_tau),
                "flex_tau40_fraction": sum(1 for value in f_tau if value == 40.0) / len(f_tau),
                "c1p1_U_mean": _mean(t_u),
                "flex_U_mean": _mean(f_u),
                "difference_U_flex_minus_c1p1": _mean(f_u) - _mean(t_u),
                "c1p1_40U_mean": 40.0 * _mean(t_u),
                "flex_40U_mean": 40.0 * _mean(f_u),
                "paired_tau_se": tau_se,
                "paired_U_se": u_se,
            }
        )
    treatment_cells = cell_endpoint_means(treatment_rows)
    flex_cells = cell_endpoint_means(flex_rows)
    return {
        "active_paths": paths,
        "delta_tau_b01": _mean(differences),
        "delta_tau_b01_se": se_of_mean_of_independent_ses(tau_ses),
        "c1p1_cells": treatment_cells,
        "flex_cells": flex_cells,
        "c1p1_eight_cell_mean": eight_cell_mean(treatment_cells),
        "flex_eight_cell_mean": eight_cell_mean(flex_cells),
    }


def publish_paired_primary_or_error(
    treatment_rows: Sequence[Mapping[str, object]],
    flex_rows: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object] | None, str | None]:
    """Always return a pair; empty or mismatched tables become None plus an error string."""

    try:
        if not treatment_rows:
            raise ValueError("control scenarios are empty")
        if not flex_rows:
            raise ValueError("flex scenarios are empty")
        return publish_paired_primary(treatment_rows, flex_rows), None
    except ArmWallExpired:
        raise
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def cost_law(updates: int, eval_episodes: int) -> dict[str, object]:
    training_episodes = updates * 64
    heldout_episodes = eval_episodes * len(HELDOUT_CELLS)
    return {
        "updates": updates,
        "eval_episodes_per_cell": eval_episodes,
        "training_episodes": training_episodes,
        "heldout_episodes": heldout_episodes,
        "environment_ticks_training": training_episodes * 64,
        "environment_ticks_heldout": heldout_episodes * 64,
        "wall_unit": "complete logical invocation",
        "projection_note": (
            "no pre-launch numeric wall exists; measured wall per update and "
            "per held-out episode are recorded after the invocation"
        ),
    }


def run_arm(
    *,
    arm: str,
    out: Path,
    updates: int,
    eval_episodes: int,
    wall_cap: float,
    admission_receipt: Path | None,
    launch_sha: str,
    control_summary: Path | None = None,
) -> dict[str, object]:
    if arm not in B01_ARMS:
        raise ValueError(f"B01 arm must be {B01_ARMS}, got {arm!r}")
    if arm == FLEX and control_summary is None:
        raise ValueError("FLEX requires --control-summary")
    current_digest = block_digest_hex(seed_root_key())
    control_payload: dict[str, object] | None = None
    control_identity: dict[str, object] | None = None
    if arm == FLEX:
        assert control_summary is not None
        control_payload, control_identity = load_and_validate_control_summary(
            Path(control_summary),
            updates=updates,
            eval_episodes=eval_episodes,
            block_digest=current_digest,
        )
    started = time.perf_counter()
    cpu0 = process_cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    authority, rng = make_semantic_rng()
    models = initialize_b01_models(rng)
    model = models[arm]
    initial_norm = float(torch.linalg.vector_norm(flat_parameters(model)).item())
    initial = flat_parameters(model).clone()
    if arm == FLEX:
        other = models[C1P1]
        if not torch.equal(flat_parameters(model), flat_parameters(other)):
            raise RuntimeError("C1P1 and FLEX initial tensors differ")
    baselines = torch.zeros(8, dtype=torch.float64)
    curves: list[dict[str, object]] = []
    zero_updates = 0
    nonzero_updates = 0
    status = "COMPLETE"
    stop_reason = None
    try:
        for update in range(updates):
            check_wall(started, wall_cap)
            baselines, _counts, curve, nonzero = execute_b01_training_update(
                model, arm, rng, update, baselines
            )
            curves.append(curve)
            if nonzero:
                nonzero_updates += 1
            else:
                zero_updates += 1
        check_wall(started, wall_cap)
    except ArmWallExpired:
        status = "TECHNICAL_STOP"
        stop_reason = "wall_cap"
    displacement = float(torch.linalg.vector_norm(flat_parameters(model) - initial).item())

    def snapshot(
        *,
        status_value: str,
        stop: str | None,
        scenarios_value: list[dict[str, object]],
        evaluated: list[str],
        paired_value: object,
        paired_error_value: str | None,
        wall: float,
    ) -> dict[str, object]:
        cells = cell_endpoint_means(scenarios_value) if scenarios_value else {}
        body: dict[str, object] = {
            "object": OBJECT_ID,
            "status": status_value,
            "stop_reason": stop,
            "arm": arm,
            "seed": SEED,
            "identity": IDENTITY,
            "root_key_hex": seed_root_key().hex(),
            "block_digest_hex": authority.root_digest,
            "native": authority.certificate["native"],
            "configuration": {
                "updates_requested": updates,
                "updates_completed": len(curves),
                "eval_episodes_per_cell": eval_episodes,
                "heldout_cells": list(HELDOUT_CELLS),
                "training_cells": list(TRAINING_CELLS),
                "wall_cap": wall_cap,
                "nonzero_update_norm": NONZERO_UPDATE_NORM,
            },
            "counts": {
                "completed_updates": len(curves),
                "zero_update_incidence": zero_updates,
                "nonzero_update_count": nonzero_updates,
                "heldout_scenarios": len(scenarios_value),
            },
            "evaluated_cells": evaluated,
            "initial_parameter_norm": initial_norm,
            "final_displacement": displacement,
            "curves": curves,
            "display_points": [
                row for row in curves if int(row["update"]) % 25 == 0  # type: ignore[arg-type]
            ],
            "scenarios": scenarios_value,
            "cells": cells,
            "eight_cell_mean": eight_cell_mean(cells) if cells else None,
            "paired_primary": paired_value,
            "paired_primary_error": paired_error_value,
            "cost_law": cost_law(updates, eval_episodes),
            "wall_seconds": wall,
            "process_cpu_seconds": process_cpu_seconds() - cpu0,
            "peak_rss_bytes": peak_rss_bytes(),
            "scratch_bytes": None,
            "admission_receipt": None if admission_receipt is None else str(admission_receipt),
            "launch_sha": launch_sha,
        }
        if control_identity is not None:
            body.update(control_identity)
        return body

    torch.save(model.state_dict(), out / "parameters.pt")
    write_json(
        out / "summary.json",
        snapshot(
            status_value="TRAINED_UNEVALUATED",
            stop=None,
            scenarios_value=[],
            evaluated=[],
            paired_value=None,
            paired_error_value=None,
            wall=time.perf_counter() - started,
        ),
    )
    scenarios: list[dict[str, object]] = []
    evaluated_cells: list[str] = []
    if status == "COMPLETE":
        try:
            scenarios, evaluated_cells = evaluate_learned(
                model,
                arm,
                rng,
                eval_episodes,
                started=started,
                wall_cap=wall_cap,
            )
        except ArmWallExpired as exc:
            status = "TECHNICAL_STOP"
            stop_reason = "wall_cap"
            scenarios = list(exc.evaluated_rows)
            evaluated_cells = list(exc.evaluated_cells)
        else:
            try:
                check_wall(started, wall_cap)
            except ArmWallExpired:
                status = "TECHNICAL_STOP"
                stop_reason = "wall_cap"
    paired = None
    paired_error = None
    if arm == FLEX:
        control_rows: list[Mapping[str, object]] = []
        if isinstance(control_payload, Mapping):
            raw_rows = control_payload.get("scenarios", [])
            if isinstance(raw_rows, list):
                control_rows = raw_rows
        paired, paired_error = publish_paired_primary_or_error(control_rows, scenarios)
    wall = time.perf_counter() - started
    summary = snapshot(
        status_value=status,
        stop=stop_reason,
        scenarios_value=scenarios,
        evaluated=evaluated_cells,
        paired_value=paired,
        paired_error_value=paired_error,
        wall=wall,
    )
    torch.save(model.state_dict(), out / "parameters.pt")
    write_json(out / "summary.json", summary)
    summary["scratch_bytes"] = directory_bytes(out)
    write_json(out / "summary.json", summary)
    return summary


def run_reference(
    *,
    out: Path,
    eval_episodes: int,
    admission_receipt: Path | None,
    launch_sha: str,
) -> dict[str, object]:
    started = time.perf_counter()
    cpu0 = process_cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    authority, rng = make_semantic_rng()
    scenarios = evaluate_scripted(rng, eval_episodes)
    cells = cell_endpoint_means(scenarios)
    summary = {
        "object": OBJECT_ID,
        "status": "COMPLETE",
        "arm": INDEPENDENT_NEAREST,
        "seed": SEED,
        "identity": IDENTITY,
        "root_key_hex": seed_root_key().hex(),
        "block_digest_hex": authority.root_digest,
        "native": authority.certificate["native"],
        "configuration": {
            "eval_episodes_per_cell": eval_episodes,
            "heldout_cells": list(HELDOUT_CELLS),
        },
        "scenarios": scenarios,
        "cells": cells,
        "eight_cell_mean": eight_cell_mean(cells),
        "wall_seconds": time.perf_counter() - started,
        "process_cpu_seconds": process_cpu_seconds() - cpu0,
        "peak_rss_bytes": peak_rss_bytes(),
        "scratch_bytes": None,
        "admission_receipt": None if admission_receipt is None else str(admission_receipt),
        "launch_sha": launch_sha,
        "Y_note": "ScriptedEpisodeResult has no Y; rows store Y as null",
    }
    write_json(out / "summary.json", summary)
    summary["scratch_bytes"] = directory_bytes(out)
    write_json(out / "summary.json", summary)
    return summary


def build_native(build_root: Path) -> dict[str, object]:
    build_root.mkdir(parents=True, exist_ok=True)
    request_specific = native_certificate_payload(build_root=build_root)
    default_root = native_certificate_payload(build_root=None)
    payload = dict(request_specific)
    payload["default_root"] = default_root
    write_json(build_root / "native_identity.json", payload)
    return payload

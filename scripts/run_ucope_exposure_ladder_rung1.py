#!/usr/bin/env python3
"""Runner for UCOPE exposure-ladder rung 1 (section-11 recast, 2026-09-02).

Object
------
``UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R01-RUNG-1``, evidence class ``B/EXPLORE``.

Registered as a *named* B object by
``docs/research/candidates/ucope/UCOPE_SECTION11_RECAST_INTAKE_20260902.md`` under owner
decision 2 of ``docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md`` A.4
and the portfolio decision ``2026-09-02-first-wave-section11-recast.md``. It reuses the
frozen B1 code, host, oracle, competence predicate, seeds, folds, batch law, episode count
and checkpoint cadence; its single declared axis is optimizer exposure. Rung 1 is
``lr 3e-3`` at the frozen ``160``/``320`` tail/root updates, arms ``FT-XF-FLEX`` and
``FT-XF-BC``, three seeds, two group-disjoint folds.

What may hold this launch (spec ``MARL_EMPIRICAL_EVIDENCE_SPEC.md`` §11.4)
-------------------------------------------------------------------------
* the central 4 GiB memory admission, run immediately before the workload;
* the §4 integrity items the core already enforces (group-disjoint folds, odd training /
  even held-out support separation, no read of B1 or audit runtime rows, fresh
  counter-addressed data);
* the §5.2 nonzero transition / update / evaluation counts, reconciled exactly; and
* one machine-generated exposure line (parameter displacement relative to initialisation
  scale), produced by this runner from the run's own checkpoints.

What is recorded instead of gating (§11.4/§11.6 demotion)
---------------------------------------------------------
* the working-tree cleanliness of the bound source inventory and the HEAD commit;
* the absence of a dedicated A/RECON performance assessment for this object;
* resource telemetry: a failed or partial measurement sets ``resources_unmeasured`` with
  reasons and never annuls the run (owner decision 7, 2026-09-02);
* the exact-oracle competence predicate and its branch label, and the direction's own
  acquisition / COUNT-RAW sequencing locks.

Learner-side instrumentation failure still quarantines under §6.2: the transient work and
staging trees are moved into a ``quarantine-*`` namespace with a failure receipt, and
nothing is published.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.competence_first_scout_r01.artifact import (  # noqa: E402
    atomic_create_json,
    build_scientific_artifact,
    canonical_json_bytes,
    publish_complete,
    validate_complete_tree,
)
from experiments.candidates.ucope.competence_first_scout_r01.checkpoint import (  # noqa: E402
    load_checkpoint,
    restore_checkpoint,
    stage_checkpoint_inventory,
)
from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    LADDER_OBJECT_ID,
    LADDER_R02_MOVEMENT_THRESHOLDS,
    LADDER_R02_OBJECT_ID,
    LADDER_R02_RUNG_1_ID,
    LADDER_R02_RUNG_2_ID,
    LADDER_RUNG_1_ID,
    LADDER_RUNG_1_LEARNING_RATE,
    LADDER_RUNG_2_ID,
    OBJECT_ID,
    RunBinding,
    ScoutConfig,
)

# Rung registry: science object id, config factory, prose definition.
RUNGS = {
    1: (LADDER_RUNG_1_ID, ScoutConfig.ladder_rung_1, "lr 3e-3 at the frozen 160/320 tail/root updates"),
    2: (LADDER_RUNG_2_ID, ScoutConfig.ladder_rung_2, "lr 3e-4 at 1,600/3,200 tail/root updates"),
}
# The second exposure-ladder object reuses R01's rungs and workload byte for byte; only the
# reading rule differs (per arm, FLEX residual explicit). Registered by section 9 of
# docs/research/candidates/ucope/UCOPE_SECTION11_RECAST_INTAKE_20260902.md.
LADDER_OBJECTS = {
    "R01": (LADDER_OBJECT_ID, {1: LADDER_RUNG_1_ID, 2: LADDER_RUNG_2_ID}),
    "R02": (LADDER_R02_OBJECT_ID, {1: LADDER_R02_RUNG_1_ID, 2: LADDER_R02_RUNG_2_ID}),
}
from experiments.candidates.ucope.competence_first_scout_r01.model import build_arm  # noqa: E402
from experiments.candidates.ucope.competence_first_scout_r01.workflow import run_workload  # noqa: E402

PACKAGE_ROOT = PROJECT_ROOT / "experiments/candidates/ucope/competence_first_scout_r01"
RUNNER_PATH = Path(__file__).resolve()
RESOURCE_PREFLIGHT = PROJECT_ROOT / "scripts/hmasd_resource_preflight.py"
MINIMUM_MEMORY_BYTES = 4 * 1024**3
EVIDENCE_CLASS = "B/EXPLORE"
RESULT_FORMAT = "UCOPE_EXPOSURE_LADDER_R01_RUNG1_RUN_RECORD_V1"

# Section-11 recast ledger. Every row names a condition that used to hold, or would have
# held, a launch and now only produces a recorded field. The result record embeds it so a
# reader of the artifact alone can see what was demoted and on whose authority.
RECAST_LEDGER = {
    "authority": [
        "docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#11",
        "docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md#a4",
        "docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md",
        "docs/research/candidates/ucope/UCOPE_SECTION11_RECAST_INTAKE_20260902.md",
    ],
    "recorded_not_gating": [
        "clean_committed_source_inventory",
        "performance_ready_assessment",
        "resource_projection_caps",
        "exact_oracle_competence_predicate",
        "acquisition_and_count_raw_locks",
        "execution_topology",
    ],
    "still_gating": [
        "central_4gib_memory_admission",
        "section_4_integrity_items",
        "section_5_2_nonzero_counts",
        "machine_generated_exposure_line",
        "section_6_2_learner_side_quarantine",
    ],
}


class LaunchRefusal(RuntimeError):
    """Raised only by a condition §11.4 still permits to hold a B launch."""


# --------------------------------------------------------------------------------------
# Launch conditions
# --------------------------------------------------------------------------------------


def admit_memory(receipt: str | Path) -> dict[str, Any]:
    """Central 4 GiB physical + effective admission. A launch condition; it refuses."""
    path = Path(receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [sys.executable, str(RESOURCE_PREFLIGHT), "admit-memory", "--out", str(path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or not path.is_file():
        raise LaunchRefusal(
            f"central 4 GiB memory admission failed rc={completed.returncode}: {completed.stderr.strip()}"
        )
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or value.get("passed") is not True
        or value.get("physical_floor_pass") is not True
        or value.get("effective_floor_pass") is not True
        or int(value.get("available_physical_bytes", 0)) < MINIMUM_MEMORY_BYTES
        or int(value.get("effective_available_bytes", 0)) < MINIMUM_MEMORY_BYTES
    ):
        raise LaunchRefusal("central admission receipt does not establish both 4 GiB floors")
    return value


# --------------------------------------------------------------------------------------
# Recorded fields that used to be gates
# --------------------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_paths() -> tuple[Path, ...]:
    return tuple(sorted(PACKAGE_ROOT.glob("*.py"))) + (RUNNER_PATH,)


def source_status_record() -> dict[str, Any]:
    """Record the source inventory, HEAD and working-tree status. Never refuses.

    Demoted from ``scripts/run_ucope_bc_conditioning_discriminator_r01.py:82``-class
    "prepare-run requires clean committed source inventory" by §11.4 (byte manifests may
    not hold a B launch). The bytes are still recorded so the run is reproducible.
    """
    files = [
        {"path": path.relative_to(PROJECT_ROOT).as_posix(), "size_bytes": path.stat().st_size, "sha256": _sha256_file(path)}
        for path in source_paths()
    ]
    aggregate = hashlib.sha256(canonical_json_bytes(files)).hexdigest()
    record: dict[str, Any] = {
        "gating": False,
        "demoted_by": "MARL_EMPIRICAL_EVIDENCE_SPEC.md#11.4",
        "files": files,
        "aggregate_sha256": aggregate,
        "git_head": None,
        "porcelain_status": None,
        "clean": None,
        "observation_error": None,
    }
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", *(row["path"] for row in files)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        record["git_head"] = head
        record["porcelain_status"] = status
        record["clean"] = not status
    except (OSError, subprocess.SubprocessError) as exc:
        record["observation_error"] = f"{type(exc).__name__}: {exc}"
    return record


def performance_assessment_record() -> dict[str, Any]:
    """Record the readiness position for this object. Never refuses.

    The exposure ladder has no dedicated A/RECON performance assessment. Under §11.4 a
    capacity gate may not hold a B launch, so the absence is a recorded field. The frozen
    B1 measurement (three arms, same seeds/folds/updates, about 140 s wall and 455 MB peak
    RSS) is recorded as the prior for a two-arm run of the same shape.
    """
    return {
        "gating": False,
        "demoted_by": "MARL_EMPIRICAL_EVIDENCE_SPEC.md#11.4",
        "assessment_present": False,
        "disposition": "NOT_ASSESSED",
        "prior_source": "UCOPE_COMPETENCE_FIRST_SCOUT_R01_B1_RESULT_EVIDENCE_20260901.md",
        "prior_wall_seconds": 140.0,
        "prior_peak_rss_bytes": 455 * 1000 * 1000,
        "prior_arm_count": 3,
        "this_run_arm_count": 2,
    }


def topology_record() -> dict[str, Any]:
    """Record the execution topology. Recorded, never gating (§11.4)."""
    import torch

    return {
        "gating": False,
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "executable": str(Path(sys.executable).resolve()),
        "platform": platform.platform(),
        "torch_version": str(torch.__version__),
        "torch_cuda_available": bool(torch.cuda.is_available()),
        "torch_intraop_threads": int(torch.get_num_threads()),
        "torch_interop_threads": int(torch.get_num_interop_threads()),
        "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
        "logical_processors": int(os.cpu_count() or 1),
        "process_count": 1,
    }


# --------------------------------------------------------------------------------------
# Resource telemetry (recorded; missing measurement downgrades, never annuls)
# --------------------------------------------------------------------------------------


def _peak_working_set_bytes() -> int:
    """Peak working set of this process. Windows-specific; raises elsewhere."""
    class _Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_uint32),
            ("PageFaultCount", ctypes.c_uint32),
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
    counters.cb = ctypes.sizeof(_Counters)
    handle = ctypes.windll.kernel32.GetCurrentProcess()  # type: ignore[attr-defined]
    if not ctypes.windll.psapi.GetProcessMemoryInfo(  # type: ignore[attr-defined]
        ctypes.c_void_p(handle), ctypes.byref(counters), counters.cb
    ):
        raise OSError("GetProcessMemoryInfo failed")
    return int(counters.PeakWorkingSetSize)


def _directory_bytes(root: Path) -> int:
    total = 0
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            total += path.stat().st_size
    return total


def resource_record(
    *,
    wall_seconds: float | None,
    cpu_seconds: float | None,
    peak_rss_bytes: int | None,
    scratch_bytes: int | None,
    durable_bytes: int | None,
    reasons: Sequence[str] = (),
) -> dict[str, Any]:
    """Assemble the resource ledger.

    Owner decision 7 (2026-09-02): a missing or failed resource measurement downgrades the
    run to ``resources_unmeasured`` with reasons. It never annuls or quarantines, because
    this object makes no resource claim. Learner-side instrumentation failure is a separate
    matter and still quarantines under §6.2.
    """
    measured = {
        "wall_seconds": wall_seconds,
        "cpu_seconds": cpu_seconds,
        "peak_rss_bytes": peak_rss_bytes,
        "scratch_bytes": scratch_bytes,
        "durable_bytes": durable_bytes,
    }
    missing = sorted(name for name, value in measured.items() if value is None)
    all_reasons = [*reasons, *(f"{name}_missing" for name in missing)]
    return {
        "gating": False,
        "resources_unmeasured": bool(all_reasons),
        "unmeasured_reasons": all_reasons,
        "downgrade_only": True,
        "decision": "FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md#a4-decision-7",
        **measured,
    }


def measure_resources(start: Mapping[str, Any], scratch: Path, durable: Path) -> dict[str, Any]:
    """Best-effort terminal measurement. Every failure becomes a recorded reason."""
    reasons: list[str] = []
    wall: float | None
    cpu: float | None
    try:
        wall = time.perf_counter() - float(start["wall"])
        cpu = time.process_time() - float(start["cpu"])
    except (KeyError, TypeError, ValueError) as exc:
        wall = cpu = None
        reasons.append(f"clock_unavailable:{type(exc).__name__}")
    try:
        rss: int | None = _peak_working_set_bytes()
    except BaseException as exc:  # platform, permission, or API failure
        rss = None
        reasons.append(f"peak_rss_unavailable:{type(exc).__name__}")
    try:
        scratch_bytes: int | None = _directory_bytes(scratch)
    except BaseException as exc:
        scratch_bytes = None
        reasons.append(f"scratch_unavailable:{type(exc).__name__}")
    try:
        durable_bytes: int | None = _directory_bytes(durable)
    except BaseException as exc:
        durable_bytes = None
        reasons.append(f"durable_unavailable:{type(exc).__name__}")
    return resource_record(
        wall_seconds=wall,
        cpu_seconds=cpu,
        peak_rss_bytes=rss,
        scratch_bytes=scratch_bytes,
        durable_bytes=durable_bytes,
        reasons=reasons,
    )


# --------------------------------------------------------------------------------------
# The one mandatory exposure line (§11.4)
# --------------------------------------------------------------------------------------


def exposure_line(config: ScoutConfig, checkpoint_root: Path) -> dict[str, Any]:
    """Machine-generated parameter-displacement budget relative to initialisation scale.

    For every policy this compares the final checkpoint's parameters with the exact
    deterministic initialisation the same arm/seed/fold produces, per stage and for the
    Bellman coefficient vector alone. It is computed from the run's own checkpoints and
    reads no other object.
    """
    import torch

    rows = []
    for arm in config.arms:
        for seed in config.seed_ids:
            for fold in (0, 1):
                path = checkpoint_root / arm / seed / f"fold-{fold}" / f"root-{config.root_updates:04d}.pt"
                payload = load_checkpoint(path)
                final_root, final_tail, _ro, _to = restore_checkpoint(payload)
                init_root, init_tail = build_arm(arm, seed, fold)
                for stage, final_model, init_model in (("root", final_root, init_root), ("tail", final_tail, init_tail)):
                    final_state = final_model.state_dict()
                    init_state = init_model.state_dict()
                    displacement = 0.0
                    scale = 0.0
                    for name, tensor in init_state.items():
                        delta = (final_state[name].detach() - tensor.detach()).to(torch.float64)
                        displacement += float(torch.sum(delta * delta).item())
                        base = tensor.detach().to(torch.float64)
                        scale += float(torch.sum(base * base).item())
                    beta_delta = (final_state["beta"].detach() - init_state["beta"].detach()).to(torch.float64)
                    beta_init = init_state["beta"].detach().to(torch.float64)
                    # Largest absolute per-coordinate move over ALL trained coordinates of
                    # this arm. For FT-XF-BC that is the Bellman vector alone; for
                    # FT-XF-FLEX the paired residual is deliberately included, which is the
                    # statistic the R02 per-arm reading rule uses. The beta-only fields
                    # below keep the R01 definition unchanged.
                    all_move = max(
                        float(torch.max(torch.abs((final_state[name].detach() - tensor.detach()).to(torch.float64))).item())
                        for name, tensor in init_state.items()
                    )
                    rows.append({
                        "arm_id": arm,
                        "seed_id": seed,
                        "fold_id": fold,
                        "stage": stage,
                        "parameter_displacement_l2": displacement ** 0.5,
                        "initialisation_scale_l2": scale ** 0.5,
                        "displacement_over_initialisation_scale": (displacement ** 0.5) / (scale ** 0.5) if scale > 0 else None,
                        "beta_displacement_l2": float(torch.sqrt(torch.sum(beta_delta * beta_delta)).item()),
                        "beta_initialisation_l2": float(torch.sqrt(torch.sum(beta_init * beta_init)).item()),
                        "beta_max_abs_coordinate_move": float(torch.max(torch.abs(beta_delta)).item()),
                        "max_abs_coordinate_move": all_move,
                    })
    ratios = [row["displacement_over_initialisation_scale"] for row in rows if row["displacement_over_initialisation_scale"] is not None]
    moves = [row["beta_max_abs_coordinate_move"] for row in rows]
    per_arm = {}
    for arm in config.arms:
        arm_rows = [row for row in rows if row["arm_id"] == arm]
        if not arm_rows:
            continue
        per_arm[arm] = {
            "rows": len(arm_rows),
            "minimum_beta_max_abs_coordinate_move": min(row["beta_max_abs_coordinate_move"] for row in arm_rows),
            "maximum_beta_max_abs_coordinate_move": max(row["beta_max_abs_coordinate_move"] for row in arm_rows),
            "minimum_max_abs_coordinate_move": min(row["max_abs_coordinate_move"] for row in arm_rows),
            "maximum_max_abs_coordinate_move": max(row["max_abs_coordinate_move"] for row in arm_rows),
            "minimum_displacement_ratio": min(row["displacement_over_initialisation_scale"] for row in arm_rows),
            "residual_included_in_max_abs_coordinate_move": bool(
                any(name != "beta" for name in build_arm(arm, config.seed_ids[0], 0)[1].state_dict())
            ),
            "movement_threshold": LADDER_R02_MOVEMENT_THRESHOLDS.get(arm),
        }
    return {
        "statement": (
            "parameter displacement relative to initialisation scale, per policy and stage, "
            "computed from this run's own final checkpoints against the exact deterministic "
            "initialisation of the same arm/seed/fold"
        ),
        "learning_rate": config.learning_rate,
        "tail_updates": config.tail_updates,
        "root_updates": config.root_updates,
        "rows": rows,
        "minimum_displacement_ratio": min(ratios) if ratios else None,
        "maximum_displacement_ratio": max(ratios) if ratios else None,
        "per_arm": per_arm,
        "minimum_beta_max_abs_coordinate_move": min(moves) if moves else None,
        "maximum_beta_max_abs_coordinate_move": max(moves) if moves else None,
        "learner_can_move_in_its_budget": bool(moves) and min(moves) > 0.0,
    }


# --------------------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------------------


def _binding(source_aggregate: str, *, mode: str = "LADDER1", object_id: str = LADDER_RUNG_1_ID) -> RunBinding:
    manifest_digest = hashlib.sha256(f"{object_id}|MANIFEST".encode("utf-8")).hexdigest()
    assessment_digest = hashlib.sha256(f"{object_id}|NO_ASSESSMENT".encode("utf-8")).hexdigest()
    return RunBinding.ladder(
        mode,
        manifest_digest=manifest_digest,
        source_aggregate=source_aggregate,
        assessment_digest=assessment_digest,
    )


def _configure_topology(max_threads: int = 1) -> None:
    import torch

    torch.set_num_threads(max_threads)
    with contextlib.suppress(RuntimeError):
        torch.set_num_interop_threads(1)


def run_rung(output_root: str | Path, *, thread_cap: int = 1, rung: int = 1, ladder_object: str = "R01") -> Path:
    """Execute one exposure-ladder rung and publish a complete run record.

    ``ladder_object`` selects which named ladder object the rung is being run for. R01 and
    R02 share this workload byte for byte -- same arms, seeds, folds, update counts and
    counter-addressed RNG -- and differ only in the registered reading rule, so the object
    identity is recorded and nothing about the execution changes.
    """
    if rung not in RUNGS:
        raise LaunchRefusal(f"unknown ladder rung: {rung}")
    if ladder_object not in LADDER_OBJECTS:
        raise LaunchRefusal(f"unknown ladder object: {ladder_object}")
    science_object_id, config_factory, rung_definition = RUNGS[rung]
    ladder_object_id, rung_ids = LADDER_OBJECTS[ladder_object]
    science_object_id = rung_ids[rung]
    output = Path(output_root).resolve()
    if output.exists():
        raise LaunchRefusal(f"output root is create-once: {output}")
    attempt_id = uuid.uuid4().hex
    config = config_factory()
    output.mkdir(parents=True)
    work = output / "work"
    staging = output / f".complete-staging-{attempt_id}"
    work.mkdir()
    staging.mkdir()

    # Launch condition, immediately before any RNG master, model, or optimizer exists.
    admission = admit_memory(output / "preflight.json")
    _configure_topology(thread_cap)

    source = source_status_record()
    assessment = performance_assessment_record()
    start = {"wall": time.perf_counter(), "cpu": time.process_time()}
    resources: dict[str, Any] | None = None
    try:
        binding = _binding(source["aggregate_sha256"], mode=config.mode, object_id=science_object_id)
        result = run_workload(config, work, run_binding=binding)
        inventory = stage_checkpoint_inventory(config, result.checkpoints, staging_root=staging, run_binding=binding)
        exposure = exposure_line(config, work / "scientific_checkpoints")
        if not exposure["learner_can_move_in_its_budget"]:
            raise LaunchRefusal("exposure line reports no parameter movement in the budget")
        artifact = build_scientific_artifact(result, checkpoint_inventory=inventory, artifact_root=staging)
        resources = measure_resources(start, work, staging)
        record = {
            "format": RESULT_FORMAT,
            "schema_version": 1,
            "science_object_id": science_object_id,
            "ladder_object_id": ladder_object_id,
            "code_object_id": OBJECT_ID,
            "rung": rung,
            "rung_definition": rung_definition,
            "evidence_class": EVIDENCE_CLASS,
            "complete": True,
            "attempt_id": attempt_id,
            "learning_rate": config.learning_rate,
            "admission": admission,
            "recast_ledger": RECAST_LEDGER,
            "source_status": source,
            "performance_assessment": assessment,
            "execution_topology": topology_record(),
            "exposure_line": exposure,
            "resources": resources,
            "artifact": artifact,
        }
        publish_complete(staging / "result.json", artifact, artifact_root=staging)
        atomic_create_json(staging / "run-manifest.json", {
            "object_id": OBJECT_ID,
            "science_object_id": science_object_id,
            "config": config.to_dict(),
            "run_binding": binding.to_dict(),
            "rng_version": config.rng_version,
            "data_source": "fresh_counter_generated_host_only",
            "consumed_artifacts_read": False,
        })
        atomic_create_json(staging / "run-record.json", record)
        complete = output / "complete"
        os.replace(staging, complete)
        return complete / "run-record.json"
    except BaseException as exc:
        # Section 6.2: a learner-side or instrumentation failure is quarantined whole and
        # is not interpreted, resumed, or salvaged.
        if resources is None:
            with contextlib.suppress(BaseException):
                resources = measure_resources(start, work, staging)
        quarantine = output / f"quarantine-{attempt_id}"
        with contextlib.suppress(BaseException):
            quarantine.mkdir(exist_ok=False)
            if staging.exists():
                os.replace(staging, quarantine / "staging")
            if work.exists():
                os.replace(work, quarantine / "work")
            atomic_create_json(quarantine / "failure.json", {
                "science_object_id": science_object_id,
                "complete": False,
                "quarantined": True,
                "quarantine_rule": "MARL_EMPIRICAL_EVIDENCE_SPEC.md#6.2",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "source_status": source,
                "resources": resources,
            })
        raise


# Retained name: the committed section-11 recast tests address the implementation through it,
# and rung 1's published record was produced by this exact function body.
run_rung_1 = run_rung


def validate_complete(complete_root: str | Path) -> dict[str, Any]:
    root = Path(complete_root).resolve()
    record = json.loads((root / "run-record.json").read_text(encoding="utf-8"))
    artifact = json.loads((root / "result.json").read_text(encoding="utf-8"))
    validate_complete_tree(artifact, complete_root=root)
    if record["artifact"] != artifact:
        raise ValueError("run record and published artifact differ")
    return {
        "valid": True,
        "science_object_id": record["science_object_id"],
        "branch": artifact["internal_result"]["gates"]["branch"],
        "resources_unmeasured": record["resources"]["resources_unmeasured"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", allow_abbrev=False)
    run.add_argument("--output-root", required=True)
    run.add_argument("--thread-cap", type=int, default=1)
    run.add_argument("--rung", type=int, default=1, choices=sorted(RUNGS))
    run.add_argument("--ladder-object", default="R01", choices=sorted(LADDER_OBJECTS))
    validate = commands.add_parser("validate", allow_abbrev=False)
    validate.add_argument("--complete-root", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "run":
            result: dict[str, Any] = {
                "path": str(
                    run_rung(
                        args.output_root,
                        thread_cap=args.thread_cap,
                        rung=args.rung,
                        ladder_object=args.ladder_object,
                    )
                )
            }
        elif args.command == "validate":
            result = validate_complete(args.complete_root)
        else:
            raise AssertionError("unreachable")
    except (OSError, ValueError, TypeError, subprocess.SubprocessError, LaunchRefusal) as exc:
        print(f"UCOPE exposure ladder rung 1 stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 6
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

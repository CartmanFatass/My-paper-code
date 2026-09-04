#!/usr/bin/env python3
"""Exact production CLI for the UCOPE BC conditioning discriminator R01.

Section-11 recast, 2026-09-02
-----------------------------
Owner decision 2 of ``docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md``
A.4, formal record ``docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md``,
direction intake ``docs/research/candidates/ucope/UCOPE_SECTION11_RECAST_INTAKE_20260902.md``.

Two refusals in this file used to hold the launch and are now recorded fields:

* ``:82`` ``RunnerRefusal("prepare-run requires clean committed source inventory")`` ->
  ``source_binding()`` records ``git status --porcelain`` and the HEAD SHA and proceeds.
* ``:127`` ``RunnerRefusal("manifest assessment-03 binding mismatch")`` gated on a
  create-once ``assessment-03`` with a ``PERFORMANCE_READY`` disposition that does not
  exist -> ``recorded_assessment()`` records whichever assessment is on disk together with
  the contract's own declaration for it (``assessment-02.json`` is ``PERFORMANCE_READY``;
  the prospective contract at line 561 declares it ``INVALID_NOT_ADOPTED``; both facts are
  recorded, neither gates).

The projection resource caps inherited from that assessment are likewise recorded, with any
exceedance listed, because they are a §11.4 capacity gate derived from an assessment the
contract itself declares ineligible.

What still holds this launch: the central 4 GiB memory admission immediately before the
run; the §4 integrity items the workload enforces (group-disjoint folds, odd/even support
separation, no read of B1 or audit runtime rows, non-positive-definite ``G`` stops rather
than admitting repair); the §5.2 nonzero transition/update/evaluation counts; and one
machine-generated exposure line. Learner-side instrumentation failure still quarantines
under §6.2 -- the ``except BaseException`` path below is unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ucope.conditioning_discriminator_r01.contract import OBJECT_ID, WorkloadConfig  # noqa: E402
from experiments.candidates.ucope.conditioning_discriminator_r01.firewall import validate_import_firewall, validate_runtime_path  # noqa: E402
from experiments.candidates.ucope.conditioning_discriminator_r01.publication import (  # noqa: E402
    MANIFEST_FORMAT, RECAST_MANIFEST_FORMAT,
    atomic_create_json, build_assessment, build_complete_result, build_manifest,
    build_recast_manifest, canonical_json_bytes, stage_checkpoints, validate_admission,
    validate_assessment, validate_complete_result, validate_recast_manifest,
)
from experiments.candidates.ucope.conditioning_discriminator_r01.publication import (  # noqa: E402
    validate_manifest as validate_strict_manifest,
)
from experiments.candidates.ucope.conditioning_discriminator_r01.resources import ResourceMonitor, directory_bytes  # noqa: E402
from experiments.candidates.ucope.conditioning_discriminator_r01.workflow import run_workload  # noqa: E402
from experiments.candidates.ucope.conditioning_discriminator_r01.assessment_v2 import run_assessment_workload  # noqa: E402
from experiments.candidates.ucope.conditioning_discriminator_r01.training import load_checkpoint_models_read_only  # noqa: E402
from experiments.candidates.ucope.conditioning_discriminator_r01.evaluation import CheckpointEvaluation, evaluate_support  # noqa: E402
from experiments.candidates.ucope.conditioning_discriminator_r01.reducer import reduce_results  # noqa: E402
from experiments.candidates.ucope.conditioning_discriminator_r01.oracle import validate_host  # noqa: E402
from experiments.candidates.ucope.conditioning_discriminator_r01.topology import configure_torch_topology_once  # noqa: E402

PACKAGE_ROOT = PROJECT_ROOT / "experiments/candidates/ucope/conditioning_discriminator_r01"
RUNNER_PATH = Path(__file__).resolve()
CONTROL_ROOT = PROJECT_ROOT / "temp/directions/ucope/controls/ucope-bc-conditioning-r01"
RETAINED_ASSESSMENT_01_PATH = CONTROL_ROOT / "assessments/assessment-01.json"
RETAINED_ASSESSMENT_02_PATH = CONTROL_ROOT / "assessments/assessment-02.json"
ASSESSMENT_PATH = CONTROL_ROOT / "assessments/assessment-03.json"
ASSESSMENT_ADMISSION_PATH = CONTROL_ROOT / "admissions/assessment-03.json"
ASSESSMENT_SCRATCH_PATH = CONTROL_ROOT / "scratch/assessment-03"
MANIFEST_PATH = CONTROL_ROOT / "manifests/result-01.json"
ADMISSION_PATH = CONTROL_ROOT / "admissions/result-01.json"
OUTPUT_ROOT = PROJECT_ROOT / "temp/directions/ucope/exp/ucope-bc-conditioning-r01-result-01"


class RunnerRefusal(RuntimeError):
    pass


def _exact_path(value: str | Path, expected: Path, label: str) -> Path:
    observed = validate_runtime_path(value)
    if observed != expected.resolve(): raise RunnerRefusal(f"{label} must equal the frozen path: {expected}")
    return observed


def _load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as stream: value = json.load(stream)
    if not isinstance(value, dict): raise RunnerRefusal("JSON root must be an object")
    return value


def _sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_inventory() -> list[dict[str, Any]]:
    paths = [*sorted(PACKAGE_ROOT.glob("*.py")), RUNNER_PATH]
    validate_import_firewall(paths)
    return [{"path": path.relative_to(PROJECT_ROOT).as_posix(), "size_bytes": path.stat().st_size, "sha256": _sha256(path)} for path in paths]


def source_aggregate(inventory: list[dict[str, Any]] | None = None) -> str:
    return hashlib.sha256(canonical_json_bytes(inventory or source_inventory())).hexdigest()


def source_binding() -> dict[str, Any]:
    """Record the bound source inventory, the HEAD SHA and the working-tree status.

    Section-11 recast: this replaces the ``:82`` refusal
    ``"prepare-run requires clean committed source inventory"``. A dirty inventory is a
    recorded fact (``status.clean = false`` plus the porcelain lines), not a refusal --
    §11.4 forbids byte manifests from holding a B launch. The bytes and the HEAD are still
    recorded so the run stays reproducible.
    """
    inventory = source_inventory(); paths = [row["path"] for row in inventory]
    status: dict[str, Any] = {"gating": False, "demoted_by": "MARL_EMPIRICAL_EVIDENCE_SPEC.md#11.4", "porcelain": None, "clean": None, "observation_error": None}
    revision = ""
    try:
        porcelain = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--", *paths], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True).stdout.strip()
        status["porcelain"] = porcelain
        status["clean"] = not porcelain
    except (OSError, subprocess.SubprocessError) as exc:
        status["observation_error"] = f"{type(exc).__name__}: {exc}"
    return {"revision": revision, "inventory": inventory, "status": status}


# The prospective contract declares assessment-01 RETAINED_REPAIR_REQUIRED and assessment-02
# INVALID_NOT_ADOPTED (contract :561), and requires a create-once V3 assessment-03 that does
# not exist. Under the recast whichever assessment is on disk is recorded with the contract's
# declaration beside it, and none of it gates.
ASSESSMENT_CONTRACT_DECLARATIONS = {
    "assessment-03.json": "REQUIRED_BY_CONTRACT_ABSENT_ON_DISK",
    "assessment-02.json": "INVALID_NOT_ADOPTED",
    "assessment-01.json": "RETAINED_REPAIR_REQUIRED",
}


def recorded_assessment() -> dict[str, Any]:
    """Record whichever performance assessment exists. Never refuses.

    Section-11 recast: this replaces the ``:127`` refusal
    ``"manifest assessment-03 binding mismatch"``. Resolution order is assessment-03,
    assessment-02, assessment-01; the record carries the file's own disposition, the
    contract's declaration for that file, and ``gating: false``.
    """
    for path in (ASSESSMENT_PATH, RETAINED_ASSESSMENT_02_PATH, RETAINED_ASSESSMENT_01_PATH):
        if not path.is_file():
            continue
        value = _load_json(path)
        return {
            "gating": False,
            "demoted_by": "MARL_EMPIRICAL_EVIDENCE_SPEC.md#11.4",
            "present": True,
            "path": path.relative_to(PROJECT_ROOT).as_posix(),
            "assessment_id": value.get("assessment_id"),
            "schema": value.get("format"),
            "projection_law": value.get("projection_law"),
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
            "source_aggregate": value.get("source_aggregate"),
            "snapshot_count_check": value.get("snapshot_count_check"),
            "disposition": value.get("disposition"),
            "contract_declaration": ASSESSMENT_CONTRACT_DECLARATIONS.get(path.name, "UNDECLARED"),
            "projection": value.get("projection"),
        }
    return {
        "gating": False, "demoted_by": "MARL_EMPIRICAL_EVIDENCE_SPEC.md#11.4", "present": False,
        "path": None, "assessment_id": None, "schema": None, "projection_law": None, "sha256": None,
        "size_bytes": None, "source_aggregate": None, "snapshot_count_check": None,
        "disposition": "NOT_ASSESSED", "contract_declaration": "REQUIRED_BY_CONTRACT_ABSENT_ON_DISK",
        "projection": None,
    }


NO_CAP = {
    "wall_seconds": None, "cpu_seconds": None, "process_tree_rss_bytes": None, "scratch_bytes": None,
    "durable_bytes": None, "io_read_bytes": None, "io_write_bytes": None, "aggregate_io_bytes": None,
    "thread_cap": None, "process_cap": None, "child_process_cap": None,
}


def recorded_caps(assessment: Mapping[str, Any]) -> dict[str, Any]:
    """Resource caps carried forward from the recorded assessment, if it has a projection."""
    projection = assessment.get("projection")
    if not isinstance(projection, Mapping):
        return dict(NO_CAP)
    return {
        "wall_seconds": projection["guarded_wall_seconds"], "cpu_seconds": projection["guarded_cpu_seconds"],
        "process_tree_rss_bytes": projection["rss_cap_bytes"], "scratch_bytes": projection["scratch_cap_bytes"],
        "durable_bytes": projection["durable_cap_bytes"], "io_read_bytes": projection["read_cap_bytes"],
        "io_write_bytes": projection["write_cap_bytes"], "aggregate_io_bytes": projection["aggregate_io_cap"],
        "thread_cap": projection["thread_cap"], "process_cap": projection["process_cap"],
        "child_process_cap": projection["child_process_cap"],
    }


def validate_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    """Dispatch on manifest format: the recast format, or the retained strict V1."""
    if isinstance(value, Mapping) and value.get("format") == RECAST_MANIFEST_FORMAT:
        return validate_recast_manifest(value)
    return validate_strict_manifest(value)


def assess_run(admission_receipt: str | Path, output: str | Path) -> Path:
    admission_path = _exact_path(admission_receipt, ASSESSMENT_ADMISSION_PATH, "assessment admission receipt")
    destination = _exact_path(output, ASSESSMENT_PATH, "assessment output")
    if destination.exists(): raise RunnerRefusal("assessment output is create-once")
    admission = validate_admission(_load_json(admission_path))
    scratch = validate_runtime_path(ASSESSMENT_SCRATCH_PATH); durable = destination.parent.resolve()
    if scratch == durable or scratch in durable.parents or durable in scratch.parents: raise RunnerRefusal("assessment scratch and durable roots must be disjoint")
    if scratch.exists(): raise RunnerRefusal("assessment scratch identity already exists")
    durable.mkdir(parents=True, exist_ok=True)
    monitor = ResourceMonitor(scratch, durable).start()
    try:
        inventory = source_inventory(); aggregate = source_aggregate(inventory); binding = hashlib.sha256((OBJECT_ID + "|ASSESSMENT-02|" + aggregate).encode()).hexdigest()
        result = run_assessment_workload(binding=binding, scratch_root=scratch, durable_root=durable)
    finally: telemetry = monitor.finish()
    admission_binding = {"path": str(admission_path), "sha256": _sha256(admission_path), "size_bytes": admission_path.stat().st_size, "captured_at": admission["captured_at"], "assessed_at": admission["assessed_at"]}
    document = build_assessment(classified_timer_rows=result["timer_rows"], invocation_telemetry=telemetry, topology_record=result["topology"], observed_snapshot_count=result["snapshot_count"], source_aggregate=aggregate, admission_binding=admission_binding, scratch_bytes_created=directory_bytes(scratch), durable_bytes_created=0)
    return atomic_create_json(destination, document)


def prepare_run(manifest: str | Path, output_root: str | Path) -> Path:
    """Create the recast run manifest. No assessment or source gate remains here."""
    manifest_path = _exact_path(manifest, MANIFEST_PATH, "manifest")
    output = _exact_path(output_root, OUTPUT_ROOT, "output root")
    if manifest_path.exists() or output.exists(): raise RunnerRefusal("manifest/output identity is create-once")
    assessment = recorded_assessment()
    source = source_binding()
    assessment["source_aggregate_matches_live_source"] = assessment.get("source_aggregate") == source_aggregate(source["inventory"])
    value = build_recast_manifest(
        assessment_record=assessment,
        resource_caps=recorded_caps(assessment),
        execution_topology=configure_torch_topology_once(),
        source_record=source,
        output_root=str(output),
    )
    return atomic_create_json(manifest_path, value)


def _validate_bound_source(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Record live-source agreement with the manifest. Recorded, not gating (§11.4)."""
    source = source_binding()
    return {
        "gating": False,
        "live_revision": source["revision"],
        "manifest_revision": manifest.get("source_revision"),
        "revision_matches": source["revision"] == manifest.get("source_revision"),
        "inventory_matches": source["inventory"] == manifest.get("source_inventory"),
        "status": source["status"],
    }


def _validate_bound_assessment(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Record the live assessment beside the one the manifest bound. Never refuses.

    Demoted from the ``:127`` ``PERFORMANCE_READY`` assessment-03 binding refusal.
    """
    live = recorded_assessment()
    record = manifest.get("performance_assessment") or {}
    return {
        "gating": False,
        "demoted_by": "MARL_EMPIRICAL_EVIDENCE_SPEC.md#11.4",
        "manifest_record": dict(record),
        "live_record": {key: live[key] for key in ("present", "path", "assessment_id", "schema", "projection_law", "sha256", "size_bytes", "disposition", "contract_declaration")},
        "matches_manifest": live.get("sha256") == record.get("sha256"),
        "performance_ready": live.get("disposition") == "PERFORMANCE_READY",
        "contract_declaration": live.get("contract_declaration"),
    }


CAP_COMPARISONS = (
    ("wall_seconds", "wall_seconds"), ("cpu_seconds", "cpu_seconds"),
    ("process_tree_peak_rss_bytes", "process_tree_rss_bytes"),
    ("scratch_high_water_bytes", "scratch_bytes"), ("durable_high_water_bytes", "durable_bytes"),
    ("io_read_bytes", "io_read_bytes"), ("io_write_bytes", "io_write_bytes"),
    ("aggregate_io_bytes", "aggregate_io_bytes"), ("thread_count_peak", "thread_cap"),
    ("process_count_peak", "process_cap"), ("child_process_count_peak", "child_process_cap"),
)


def recast_resource_ledger(telemetry: Mapping[str, Any], caps: Mapping[str, Any], *, cap_source: Any) -> dict[str, Any]:
    """Assemble the run's resource ledger under the section-11 recast.

    The projection caps are inherited from an assessment the object's own prospective
    contract declares ineligible, so a measured exceedance is recorded (``cap_exceedances``)
    rather than refused: §11.4 does not let a capacity gate hold a B launch. A telemetry
    field the platform could not measure sets ``resources_unmeasured`` with a reason and
    downgrades the run only, per owner decision 7 of 2026-09-02. Neither path quarantines;
    §6.2 learner-side quarantine is unaffected.
    """
    unmeasured = sorted(name for name, _cap in CAP_COMPARISONS if telemetry.get(name) is None)
    exceedances = sorted(
        name for name, cap in CAP_COMPARISONS
        if telemetry.get(name) is not None and caps.get(cap) is not None and telemetry[name] > caps[cap]
    )
    return {
        "observed": dict(telemetry), "caps": dict(caps), "within_caps": not exceedances, "gating": False,
        "cap_source": cap_source,
        "cap_exceedances": exceedances,
        "resources_unmeasured": bool(unmeasured),
        "unmeasured_reasons": [f"{name}_missing" for name in unmeasured],
    }


def _expose_complete(output: Path, work: Path, staging: Path) -> Path:
    resolved_output = output.resolve()
    if work.resolve().parent != resolved_output or staging.resolve().parent != resolved_output: raise RunnerRefusal("work/staging must be direct output children")
    complete = output / "complete"
    if complete.exists(): raise RunnerRefusal("complete identity already exists")
    shutil.rmtree(work)
    os.replace(staging, complete)
    return complete


def run_result(manifest: str | Path, admission_receipt: str | Path, output_root: str | Path) -> Path:
    manifest_path = _exact_path(manifest, MANIFEST_PATH, "manifest")
    admission_path = _exact_path(admission_receipt, ADMISSION_PATH, "admission receipt")
    output = _exact_path(output_root, OUTPUT_ROOT, "output root")
    manifest_value = validate_manifest(_load_json(manifest_path)); admission_value = validate_admission(_load_json(admission_path))
    source_record = _validate_bound_source(manifest_value) or {}
    assessment_record = _validate_bound_assessment(manifest_value) or {}
    if manifest_value["output_root"] != str(output) or output.exists(): raise RunnerRefusal("output root binding/create-once violation")
    work = output / "work"; staging = output / f".complete-staging-{uuid.uuid4().hex}"; monitor = None; telemetry = None
    try:
        output.mkdir(parents=True); work.mkdir(); staging.mkdir()
        monitor = ResourceMonitor(work, staging).start()
        result = run_workload(WorkloadConfig.science(), binding=manifest_value["binding"], scratch_root=work)
        if result.runtime["execution_topology"] != manifest_value["execution_topology"]: raise RunnerRefusal("live science topology differs from manifest")
        checkpoint_inventory = stage_checkpoints(result.checkpoints, staging_root=staging)
        telemetry = monitor.finish(); monitor = None
        resource = recast_resource_ledger(
            telemetry,
            manifest_value["resource_caps"],
            cap_source=manifest_value["performance_assessment"].get("path"),
        )
        document = build_complete_result(result, manifest=manifest_value, admission_record={"path": str(admission_path), "sha256": _sha256(admission_path)}, resource_ledger=resource, checkpoint_inventory=checkpoint_inventory)
        shutil.copyfile(manifest_path, staging / "run-manifest.json"); shutil.copyfile(admission_path, staging / "admission.json")
        atomic_create_json(staging / "recast-record.json", {
            "format": "UCOPE_BC_CONDITIONING_R01_SECTION11_RECAST_RECORD_V1",
            "science_object_id": OBJECT_ID,
            "authority": [
                "docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#11",
                "docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md#a4",
                "docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md",
                "docs/research/candidates/ucope/UCOPE_SECTION11_RECAST_INTAKE_20260902.md",
            ],
            "source_status": source_record,
            "performance_assessment": assessment_record,
            "resources": resource,
            "execution_topology": {"gating": False, **dict(manifest_value["execution_topology"])},
            "competence_observation": {
                "gating": False,
                "note": "the exact-oracle competence predicate is reported in result.json reducer and decides nothing here",
                "reducer": result.reducer,
            },
            "exposure_line": exposure_line_from_workload(result),
        })
        atomic_create_json(staging / "result.json", document)
        validate_complete_result(_load_json(staging / "result.json"), complete_root=staging)
        complete = _expose_complete(output, work, staging)
        return complete / "result.json"
    except BaseException as exc:
        if monitor is not None:
            try: telemetry = monitor.finish()
            except BaseException: pass
        if output.exists():
            quarantine = output / f"quarantine-{uuid.uuid4().hex}"; quarantine.mkdir(exist_ok=False)
            if staging.exists(): os.replace(staging, quarantine / "staging")
            if work.exists(): os.replace(work, quarantine / "work")
            atomic_create_json(quarantine / "failure.json", {"object_id": OBJECT_ID, "complete": False, "error_type": type(exc).__name__, "error": str(exc), "resources": telemetry})
        raise


def exposure_line_from_workload(result: Any) -> dict[str, Any]:
    """The one machine-generated exposure line §11.4 still requires.

    Parameter displacement relative to initialisation scale, read from the run's own
    initialisation-parity and checkpoint records: for each policy the final Bellman
    coefficient vector against the exact deterministic initialisation of the same
    arm/seed/fold. Computed from this run only; no other object is read.
    """
    import torch

    from experiments.candidates.ucope.conditioning_discriminator_r01.checkpoint import load_checkpoint
    from experiments.candidates.ucope.conditioning_discriminator_r01.conditioning import TransformRecord
    from experiments.candidates.ucope.conditioning_discriminator_r01.model import initial_beta_for_arm

    rows = []
    final_update = max(result.config.checkpoint_root_updates)
    for record in result.checkpoints:
        if record["root_update"] != final_update:
            continue
        payload = load_checkpoint(Path(record["full"]["path"]))
        for stage in ("root", "tail"):
            transform = TransformRecord.from_bytes(payload["transforms"][stage])
            final_beta = payload[f"{stage}_state"]["beta"].detach().to(torch.float64)
            init_beta = torch.as_tensor(
                initial_beta_for_arm(stage, record["arm_id"], record["seed_id"], record["fold_id"], transform)
            ).detach().to(torch.float64).reshape(final_beta.shape)
            delta = final_beta - init_beta
            rows.append({
                "arm_id": record["arm_id"], "seed_id": record["seed_id"], "fold_id": record["fold_id"], "stage": stage,
                "beta_displacement_l2": float(torch.sqrt(torch.sum(delta * delta)).item()),
                "beta_initialisation_l2": float(torch.sqrt(torch.sum(init_beta * init_beta)).item()),
                "beta_max_abs_coordinate_move": float(torch.max(torch.abs(delta)).item()),
            })
    moves = [row["beta_max_abs_coordinate_move"] for row in rows]
    return {
        "statement": "parameter displacement relative to initialisation scale, per policy and stage, from this run's own final checkpoints",
        "rows": rows,
        "minimum_beta_max_abs_coordinate_move": min(moves) if moves else None,
        "maximum_beta_max_abs_coordinate_move": max(moves) if moves else None,
        "learner_can_move_in_its_budget": bool(moves) and min(moves) > 0.0,
    }


def independent_recompute(root: str | Path, result: Mapping[str, Any], config: WorkloadConfig) -> dict[str, Any]:
    """Read-only checkpoint-transform exact-metric recomputation; no episodes."""
    from experiments.candidates.ucope.conditioning_discriminator_r01.contract import K_EVAL, K_TRAIN
    root = Path(root); validate_host()
    checkpoint_records = {(row["arm_id"], row["seed_id"], row["fold_id"], row["root_update"]): row for row in result["checkpoints"]}; recomputed = []
    transform_bindings = {}
    for arm in config.arms:
        for seed in config.seed_ids:
            for fold in (0, 1):
                for update in config.checkpoint_root_updates:
                    record = checkpoint_records[(arm, seed, fold, update)]; path = root / record["projection_locator"]
                    payload, root_model, tail_model = load_checkpoint_models_read_only(path)
                    prior = transform_bindings.setdefault((seed, fold), payload["transforms"])
                    if payload["transforms"] != prior: raise RunnerRefusal("checkpoint transform binding changed across arm/update")
                    stored = next(item for item in result["evaluations"] if (item["arm_id"], item["seed_id"], item["fold_id"], item["root_update"]) == (arm, seed, fold, update))
                    odd = evaluate_support(root_model, tail_model, arm_id=arm, seed_id=seed, fold_id=fold, root_update=update, periods=K_TRAIN); even = evaluate_support(root_model, tail_model, arm_id=arm, seed_id=seed, fold_id=fold, root_update=update, periods=K_EVAL)
                    if odd.to_dict() != stored["odd"] or even.to_dict() != stored["even"]: raise RunnerRefusal("independent checkpoint exact evaluation recomputation mismatch")
                    recomputed.append(CheckpointEvaluation(arm, seed, fold, update, odd, even, stored["sampled"]))
    evaluation_rows = [item.to_dict() for item in recomputed]; reduced = reduce_results(recomputed, seed_ids=config.seed_ids, final_update=config.root_updates)
    if reduced != result["reducer"]: raise RunnerRefusal("independent reducer recomputation mismatch")
    return {"evaluations": evaluation_rows, "reducer": reduced}


def validate_complete(complete_root: str | Path) -> dict[str, Any]:
    live_topology = configure_torch_topology_once()
    root = _exact_path(complete_root, OUTPUT_ROOT / "complete", "complete root")
    before = sorted((path.relative_to(root).as_posix(), path.stat().st_size, _sha256(path)) for path in root.rglob("*") if path.is_file())
    result = validate_complete_result(_load_json(root / "result.json"), complete_root=root)
    manifest = validate_manifest(_load_json(root / "run-manifest.json"))
    if live_topology != manifest["execution_topology"]: raise RunnerRefusal("validate topology differs from manifest")
    if result["binding"] != manifest["binding"] or result["manifest_sha256"] != _sha256(root / "run-manifest.json"): raise RunnerRefusal("complete result/manifest binding mismatch")
    if result["resources"]["caps"] != manifest["resource_caps"]: raise RunnerRefusal("complete result resource caps differ from manifest")
    if result["admission"]["sha256"] != _sha256(root / "admission.json"): raise RunnerRefusal("complete result admission binding mismatch")
    validate_admission(_load_json(root / "admission.json"), maximum_age_seconds=None)
    independent_recompute(root, result, WorkloadConfig.science())
    after = sorted((path.relative_to(root).as_posix(), path.stat().st_size, _sha256(path)) for path in root.rglob("*") if path.is_file())
    if before != after: raise RunnerRefusal("validate must be read-only")
    return {"valid": True, "object_id": OBJECT_ID, "files": len(after)}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False); commands = parser.add_subparsers(dest="command", required=True)
    assess = commands.add_parser("assess-run", allow_abbrev=False); assess.add_argument("--admission-receipt", required=True); assess.add_argument("--output", required=True)
    prepare = commands.add_parser("prepare-run", allow_abbrev=False); prepare.add_argument("--manifest", required=True); prepare.add_argument("--output-root", required=True)
    run = commands.add_parser("run", allow_abbrev=False); run.add_argument("--manifest", required=True); run.add_argument("--admission-receipt", required=True); run.add_argument("--output-root", required=True)
    validate = commands.add_parser("validate", allow_abbrev=False); validate.add_argument("--complete-root", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "assess-run": result = {"path": str(assess_run(args.admission_receipt, args.output))}
        elif args.command == "prepare-run": result = {"path": str(prepare_run(args.manifest, args.output_root))}
        elif args.command == "run": result = {"path": str(run_result(args.manifest, args.admission_receipt, args.output_root))}
        elif args.command == "validate": result = validate_complete(args.complete_root)
        else: raise AssertionError("unreachable")
        print(json.dumps(result, sort_keys=True)); return 0
    except (OSError, ValueError, TypeError, subprocess.SubprocessError, RunnerRefusal) as exc:
        print(f"UCOPE conditioning runner refused: {exc}", file=sys.stderr); return 6


if __name__ == "__main__": raise SystemExit(main())

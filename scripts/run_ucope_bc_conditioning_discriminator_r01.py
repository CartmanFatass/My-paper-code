#!/usr/bin/env python3
"""Exact production CLI for the UCOPE BC conditioning discriminator R01."""

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
    atomic_create_json, build_assessment, build_complete_result, build_manifest,
    canonical_json_bytes, stage_checkpoints, validate_admission, validate_assessment,
    validate_complete_result, validate_manifest,
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


def clean_committed_source() -> tuple[str, list[dict[str, Any]]]:
    inventory = source_inventory(); paths = [row["path"] for row in inventory]
    status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--", *paths], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True)
    if status.stdout.strip(): raise RunnerRefusal("prepare-run requires clean committed source inventory")
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if len(revision) != 40: raise RunnerRefusal("source revision is not a commit SHA")
    return revision, inventory


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


def prepare_run(assessment: str | Path, manifest: str | Path, output_root: str | Path) -> Path:
    assessment_path = _exact_path(assessment, ASSESSMENT_PATH, "assessment")
    manifest_path = _exact_path(manifest, MANIFEST_PATH, "manifest")
    output = _exact_path(output_root, OUTPUT_ROOT, "output root")
    if manifest_path.exists() or output.exists(): raise RunnerRefusal("manifest/output identity is create-once")
    assessment_value = validate_assessment(_load_json(assessment_path))
    revision, inventory = clean_committed_source()
    if assessment_value["source_aggregate"] != source_aggregate(inventory): raise RunnerRefusal("assessment source bytes differ from clean committed source")
    value = build_manifest(assessment=assessment_value, source_revision=revision, source_inventory=inventory, output_root=str(output), assessment_sha256=_sha256(assessment_path), assessment_size_bytes=assessment_path.stat().st_size)
    return atomic_create_json(manifest_path, value)


def _validate_bound_source(manifest: Mapping[str, Any]) -> None:
    revision, inventory = clean_committed_source()
    if revision != manifest["source_revision"] or inventory != manifest["source_inventory"]: raise RunnerRefusal("live source differs from manifest")


def _validate_bound_assessment(manifest: Mapping[str, Any]) -> None:
    assessment = validate_assessment(_load_json(ASSESSMENT_PATH)); record = manifest["performance_assessment"]
    observed = {"assessment_id": assessment["assessment_id"], "schema": assessment["format"], "projection_law": assessment["projection_law"], "sha256": _sha256(ASSESSMENT_PATH), "size_bytes": ASSESSMENT_PATH.stat().st_size, "source_aggregate": assessment["source_aggregate"], "snapshot_count_check": assessment["snapshot_count_check"], "disposition": assessment["disposition"]}
    if observed != record or assessment["disposition"] != "PERFORMANCE_READY": raise RunnerRefusal("manifest assessment-03 binding mismatch")
    projection = assessment["projection"]
    expected_caps = {"wall_seconds": projection["guarded_wall_seconds"], "cpu_seconds": projection["guarded_cpu_seconds"], "process_tree_rss_bytes": projection["rss_cap_bytes"], "scratch_bytes": projection["scratch_cap_bytes"], "durable_bytes": projection["durable_cap_bytes"], "io_read_bytes": projection["read_cap_bytes"], "io_write_bytes": projection["write_cap_bytes"], "aggregate_io_bytes": projection["aggregate_io_cap"], "thread_cap": projection["thread_cap"], "process_cap": projection["process_cap"], "child_process_cap": projection["child_process_cap"]}
    if manifest["resource_caps"] != expected_caps: raise RunnerRefusal("manifest resource caps differ from assessment-03")
    if manifest["execution_topology"] != assessment["topology"]: raise RunnerRefusal("manifest topology differs from assessment-03")


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
    manifest_value = validate_manifest(_load_json(manifest_path)); admission_value = validate_admission(_load_json(admission_path)); _validate_bound_source(manifest_value); _validate_bound_assessment(manifest_value)
    if manifest_value["output_root"] != str(output) or output.exists(): raise RunnerRefusal("output root binding/create-once violation")
    work = output / "work"; staging = output / f".complete-staging-{uuid.uuid4().hex}"; monitor = None; telemetry = None
    try:
        output.mkdir(parents=True); work.mkdir(); staging.mkdir()
        monitor = ResourceMonitor(work, staging).start()
        result = run_workload(WorkloadConfig.science(), binding=manifest_value["binding"], scratch_root=work)
        if result.runtime["execution_topology"] != manifest_value["execution_topology"]: raise RunnerRefusal("live science topology differs from manifest")
        checkpoint_inventory = stage_checkpoints(result.checkpoints, staging_root=staging)
        telemetry = monitor.finish(); monitor = None
        caps = manifest_value["resource_caps"]
        comparisons = (("wall_seconds", "wall_seconds"), ("cpu_seconds", "cpu_seconds"), ("process_tree_peak_rss_bytes", "process_tree_rss_bytes"), ("scratch_high_water_bytes", "scratch_bytes"), ("durable_high_water_bytes", "durable_bytes"), ("io_read_bytes", "io_read_bytes"), ("io_write_bytes", "io_write_bytes"), ("aggregate_io_bytes", "aggregate_io_bytes"), ("thread_count_peak", "thread_cap"), ("process_count_peak", "process_cap"), ("child_process_count_peak", "child_process_cap"))
        if any(telemetry[source] > caps[cap] for source, cap in comparisons): raise RunnerRefusal("result resource cap exceeded")
        resource = {"observed": telemetry, "caps": caps, "within_caps": True}
        document = build_complete_result(result, manifest=manifest_value, admission_record={"path": str(admission_path), "sha256": _sha256(admission_path)}, resource_ledger=resource, checkpoint_inventory=checkpoint_inventory)
        shutil.copyfile(manifest_path, staging / "run-manifest.json"); shutil.copyfile(admission_path, staging / "admission.json")
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
    prepare = commands.add_parser("prepare-run", allow_abbrev=False); prepare.add_argument("--assessment", required=True); prepare.add_argument("--manifest", required=True); prepare.add_argument("--output-root", required=True)
    run = commands.add_parser("run", allow_abbrev=False); run.add_argument("--manifest", required=True); run.add_argument("--admission-receipt", required=True); run.add_argument("--output-root", required=True)
    validate = commands.add_parser("validate", allow_abbrev=False); validate.add_argument("--complete-root", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "assess-run": result = {"path": str(assess_run(args.admission_receipt, args.output))}
        elif args.command == "prepare-run": result = {"path": str(prepare_run(args.assessment, args.manifest, args.output_root))}
        elif args.command == "run": result = {"path": str(run_result(args.manifest, args.admission_receipt, args.output_root))}
        elif args.command == "validate": result = validate_complete(args.complete_root)
        else: raise AssertionError("unreachable")
        print(json.dumps(result, sort_keys=True)); return 0
    except (OSError, ValueError, TypeError, subprocess.SubprocessError, RunnerRefusal) as exc:
        print(f"UCOPE conditioning runner refused: {exc}", file=sys.stderr); return 6


if __name__ == "__main__": raise SystemExit(main())

"""Create-once assessment, manifest, result, and read-only validation schemas."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
import hashlib
import json
import math
import os
import shutil
import tempfile
import datetime as datetime_module

from .contract import CONTEXTS, ConditioningConfig, OBJECT_ID, RNG_VERSION, SCHEMA_VERSION, WorkloadConfig, context_id, expected_counts
from .evaluation import CheckpointEvaluation, SupportEvaluation, validate_support_evaluation
from .firewall import zero_effect_ledger
from .reducer import reduce_results
from .assessment_v2 import MEASURE_FIELDS, TIMER_SPECS
from .topology import measured_worker_count

ASSESS_FORMAT = "UCOPE_BC_CONDITIONING_R01_A_RECON_PERFORMANCE_V3"
ASSESSMENT_ID = "ucope-bc-conditioning-r01-assessment-03"
PROJECTION_LAW = "DECOMPOSED_STAGE_SCALING_V2_CONSTANT_SHAPE_SETUP_RELOAD"
MANIFEST_FORMAT = "UCOPE_BC_CONDITIONING_R01_RESULT_MANIFEST_V1"
# Section-11 recast (2026-09-02, owner decision 2 of FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md
# A.4): a second manifest format whose performance-assessment binding and source-cleanliness
# fields are recorded rather than gating. The strict V1 path above is retained unchanged so the
# historical assessment-03 contract stays readable; nothing calls it on the result path.
RECAST_MANIFEST_FORMAT = "UCOPE_BC_CONDITIONING_R01_RESULT_MANIFEST_RECAST_V1"
RESULT_FORMAT = "UCOPE_BC_CONDITIONING_R01_COMPLETE_RESULT_V1"
MAX_WALL_SECONDS = 900.0
MAX_RSS_BYTES = 603_979_776
MINIMUM_MEMORY_BYTES = 4_294_967_296
FORBIDDEN_ASSESS_KEY_TOKENS = ("loss", "coefficient", "policy", "checkpoint", "oracle", "regret", "agreement", "competence", "separation", "acquisition", "score", "root_vector", "branch")
FORBIDDEN_ASSESS_KEY_TOKENS += ("prediction", "selection", "action", "return", "metric", "model", "tensor", "optimizer", "snapshot", "payload")


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def atomic_create_json(path: str | Path, value: Mapping[str, Any]) -> Path:
    destination = Path(path)
    if destination.exists(): raise FileExistsError(f"create-once artifact exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(handle, "wb") as stream: stream.write(canonical_json_bytes(value)); stream.flush(); os.fsync(stream.fileno())
        os.link(temporary, destination)
    finally:
        try: os.unlink(temporary)
        except FileNotFoundError: pass
    return destination


def _reject_assess_outcomes(value: Any, path: str = "") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not (path == "" and key == "snapshot_count_check") and any(token in str(key).lower() for token in FORBIDDEN_ASSESS_KEY_TOKENS): raise ValueError(f"scientific field forbidden from assessment: {path}{key}")
            _reject_assess_outcomes(item, f"{path}{key}.")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value): _reject_assess_outcomes(item, f"{path}{index}.")


def _round_up_mib(value: int) -> int:
    return math.ceil(value / 1_048_576) * 1_048_576


def _require_exact_topology(topology: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(topology, Mapping) or topology.get("deterministic_algorithms") is not True or topology.get("intraop_threads") != 1 or topology.get("interop_supported") is not True or topology.get("interop_threads") != 1 or topology.get("configured_once") is not True or topology.get("static_no_spawn", {}).get("spawn_imports") != 0:
        raise ValueError(f"{label} exact execution topology mismatch")
    return topology


def _projection(timer_rows: list[Mapping[str, Any]], telemetry: Mapping[str, Any]) -> dict[str, Any]:
    keyed = {row["timer_key"]: row for row in timer_rows}
    scaled = {field: sum(TIMER_SPECS[key][2] * keyed[key][field] for key in TIMER_SPECS) for field in MEASURE_FIELDS}
    central_wall, central_cpu = scaled["wall_seconds"], scaled["cpu_seconds"]
    read_cap = 33_554_432 + math.ceil(1.25 * scaled["io_read_bytes"])
    write_cap = 33_554_432 + math.ceil(1.25 * scaled["io_write_bytes"])
    return {
        "central_wall_seconds": central_wall, "guarded_wall_seconds": 60 + 1.25 * central_wall,
        "central_cpu_seconds": central_cpu, "guarded_cpu_seconds": 60 + 1.25 * central_cpu,
        "read_cap_bytes": read_cap, "write_cap_bytes": write_cap, "aggregate_io_cap": read_cap + write_cap,
        "scratch_cap_bytes": _round_up_mib(67_108_864 + math.ceil(1.25 * scaled["scratch_bytes_created"])),
        "durable_cap_bytes": _round_up_mib(67_108_864 + math.ceil(1.25 * scaled["durable_bytes_created"])),
        "rss_cap_bytes": math.ceil(1.25 * max(255_455_232, 258_134_016, telemetry["process_tree_peak_rss_bytes"])),
        "thread_cap": 32, "process_cap": 1, "child_process_cap": 0,
    }


def build_assessment(*, classified_timer_rows: list[Mapping[str, Any]], invocation_telemetry: Mapping[str, Any], topology_record: Mapping[str, Any], observed_snapshot_count: int, source_aggregate: str, admission_binding: Mapping[str, Any], scratch_bytes_created: int, durable_bytes_created: int) -> dict[str, Any]:
    totals = {"wall_seconds": invocation_telemetry["wall_seconds"], "cpu_seconds": invocation_telemetry["cpu_seconds"], "io_read_bytes": invocation_telemetry["io_read_bytes"], "io_write_bytes": invocation_telemetry["io_write_bytes"], "scratch_bytes_created": scratch_bytes_created, "durable_bytes_created": durable_bytes_created}
    classified = {field: sum(row[field] for row in classified_timer_rows) for field in MEASURE_FIELDS}
    entry = {field: totals[field] - classified[field] for field in MEASURE_FIELDS}
    assessment_units, science_units, multiplier = TIMER_SPECS["entry_fixed"]
    entry_row = {"timer_key": "entry_fixed", **entry, "assessment_work_units": assessment_units, "science_work_units": science_units, "multiplier": multiplier}
    rows = [entry_row, *classified_timer_rows]
    projection = _projection(rows, invocation_telemetry)
    ready = projection["guarded_wall_seconds"] <= 900 and projection["rss_cap_bytes"] <= 603_979_776 and projection["scratch_cap_bytes"] <= 268_435_456 and projection["durable_cap_bytes"] <= 268_435_456 and projection["aggregate_io_cap"] <= 2_147_483_648 and invocation_telemetry["root_process_count"] == invocation_telemetry["process_count_peak"] == 1 and invocation_telemetry["child_process_count_peak"] == 0 and invocation_telemetry["thread_count_peak"] <= 32
    worker_count = measured_worker_count(invocation_telemetry, topology_record)
    snapshot_check = {"assessment": observed_snapshot_count, "science": 48, "pass": observed_snapshot_count == 8}
    value = {"format": ASSESS_FORMAT, "schema_version": SCHEMA_VERSION, "assessment_id": ASSESSMENT_ID, "projection_law": PROJECTION_LAW, "mode": "A/RECON", "source_aggregate": source_aggregate, "admission_binding": dict(admission_binding), "timer_rows": rows, "snapshot_count_check": snapshot_check, "invocation_totals": totals, "telemetry": dict(invocation_telemetry), "topology": dict(topology_record), "projection": projection, "worker_count": worker_count, "classification": "MUTUALLY_EXCLUSIVE_UNCLASSIFIED_TO_ENTRY_FIXED", "retained_assessment_01": {"sha256": "1dea9ee1762c1198b4cb71a10ac2450b8a6eadfd28edf3251f30151ffd9fb452", "disposition": "REPAIR_REQUIRED"}, "retained_assessment_02": {"sha256": "1456280de0bde1be6d8bb73448b5918d3ad5be963a1f1f6d5bf9862c32878a20", "disposition": "INVALID_NOT_ADOPTED"}, "disposition": "PERFORMANCE_READY" if ready and worker_count == 1 and snapshot_check["pass"] else "REPAIR_REQUIRED"}
    return validate_assessment(value)


def validate_assessment(value: Mapping[str, Any]) -> dict[str, Any]:
    required = {"format", "schema_version", "assessment_id", "projection_law", "mode", "source_aggregate", "admission_binding", "timer_rows", "snapshot_count_check", "invocation_totals", "telemetry", "topology", "projection", "worker_count", "classification", "retained_assessment_01", "retained_assessment_02", "disposition"}
    if not isinstance(value, Mapping) or set(value) != required or value["format"] != ASSESS_FORMAT or value["assessment_id"] != ASSESSMENT_ID or value["projection_law"] != PROJECTION_LAW or value["mode"] != "A/RECON": raise ValueError("assessment schema mismatch")
    _reject_assess_outcomes(value)
    admission = value["admission_binding"]
    if not isinstance(admission, Mapping) or set(admission) != {"path", "sha256", "size_bytes", "captured_at", "assessed_at"} or not str(admission["path"]).replace("\\", "/").endswith("/admissions/assessment-03.json") and admission["path"] != "assessment-03.json" or type(admission["sha256"]) is not str or len(admission["sha256"]) != 64 or type(admission["size_bytes"]) is not int or admission["size_bytes"] <= 0: raise ValueError("assessment admission binding mismatch")
    if any(type(admission[key]) is not str or not admission[key] for key in ("path", "captured_at", "assessed_at")) or any(character not in "0123456789abcdef" for character in admission["sha256"]): raise ValueError("assessment admission binding type mismatch")
    rows = value["timer_rows"]
    if not isinstance(rows, list) or len(rows) != len(TIMER_SPECS) or [row.get("timer_key") for row in rows] != list(TIMER_SPECS): raise ValueError("assessment timer inventory mismatch")
    required_row = {"timer_key", *MEASURE_FIELDS, "assessment_work_units", "science_work_units", "multiplier"}
    for row in rows:
        key = row["timer_key"]
        if set(row) != required_row or (row["assessment_work_units"], row["science_work_units"], row["multiplier"]) != TIMER_SPECS[key]: raise ValueError("assessment timer work/multiplier mismatch")
        if any(not isinstance(row[field], (int, float)) or isinstance(row[field], bool) or not math.isfinite(row[field]) or row[field] < 0 for field in MEASURE_FIELDS): raise ValueError("assessment timer measurement invalid")
    if value["snapshot_count_check"] != {"assessment": 8, "science": 48, "pass": True}: raise ValueError("assessment snapshot count check mismatch")
    if not isinstance(value["invocation_totals"], Mapping) or set(value["invocation_totals"]) != set(MEASURE_FIELDS) or any(not isinstance(value["invocation_totals"][field], (int, float)) or isinstance(value["invocation_totals"][field], bool) or not math.isfinite(value["invocation_totals"][field]) or value["invocation_totals"][field] < 0 for field in MEASURE_FIELDS): raise ValueError("assessment invocation totals inventory/type mismatch")
    for field in MEASURE_FIELDS:
        if not math.isclose(sum(row[field] for row in rows), value["invocation_totals"][field], rel_tol=0, abs_tol=1e-9): raise ValueError("assessment timer reconciliation mismatch")
    telemetry_keys = {"wall_seconds", "process_tree_peak_rss_bytes", "process_count_peak", "thread_count_peak", "scratch_high_water_bytes", "durable_high_water_bytes", "io_read_bytes", "io_write_bytes", "aggregate_io_bytes", "cpu_seconds", "cpu_core_equivalents", "logical_cpu_count", "host_cpu_occupancy", "samples", "root_process_count", "child_process_count_peak"}
    telemetry = value["telemetry"]
    if not isinstance(telemetry, Mapping) or set(telemetry) != telemetry_keys or any(not isinstance(telemetry[key], (int, float)) or isinstance(telemetry[key], bool) or not math.isfinite(telemetry[key]) or telemetry[key] < 0 for key in telemetry_keys) or any(type(telemetry[key]) is not int for key in ("process_tree_peak_rss_bytes", "process_count_peak", "thread_count_peak", "scratch_high_water_bytes", "durable_high_water_bytes", "io_read_bytes", "io_write_bytes", "aggregate_io_bytes", "logical_cpu_count", "samples", "root_process_count", "child_process_count_peak")) or telemetry["aggregate_io_bytes"] != telemetry["io_read_bytes"] + telemetry["io_write_bytes"]: raise ValueError("assessment telemetry inventory/type mismatch")
    if value["projection"] != _projection(rows, value["telemetry"]): raise ValueError("assessment projection arithmetic mismatch")
    projection_keys = {"central_wall_seconds", "guarded_wall_seconds", "central_cpu_seconds", "guarded_cpu_seconds", "read_cap_bytes", "write_cap_bytes", "aggregate_io_cap", "scratch_cap_bytes", "durable_cap_bytes", "rss_cap_bytes", "thread_cap", "process_cap", "child_process_cap"}
    projection = value["projection"]
    if not isinstance(projection, Mapping) or set(projection) != projection_keys or any(not isinstance(projection[key], (int, float)) or isinstance(projection[key], bool) or not math.isfinite(projection[key]) or projection[key] < 0 for key in projection_keys) or any(type(projection[key]) is not int for key in ("read_cap_bytes", "write_cap_bytes", "aggregate_io_cap", "scratch_cap_bytes", "durable_cap_bytes", "rss_cap_bytes", "thread_cap", "process_cap", "child_process_cap")): raise ValueError("assessment projection inventory/type mismatch")
    topology = value["topology"]
    retained = value["retained_assessment_01"]
    retained_02 = value["retained_assessment_02"]
    _require_exact_topology(topology, label="assessment")
    if value["worker_count"] != measured_worker_count(value["telemetry"], topology) or value["classification"] != "MUTUALLY_EXCLUSIVE_UNCLASSIFIED_TO_ENTRY_FIXED" or not isinstance(retained, Mapping) or set(retained) != {"sha256", "disposition"} or retained != {"sha256": "1dea9ee1762c1198b4cb71a10ac2450b8a6eadfd28edf3251f30151ffd9fb452", "disposition": "REPAIR_REQUIRED"} or not isinstance(retained_02, Mapping) or set(retained_02) != {"sha256", "disposition"} or retained_02 != {"sha256": "1456280de0bde1be6d8bb73448b5918d3ad5be963a1f1f6d5bf9862c32878a20", "disposition": "INVALID_NOT_ADOPTED"}: raise ValueError("assessment fixed identity/topology ledger mismatch")
    projection, telemetry = value["projection"], value["telemetry"]
    ready = projection["guarded_wall_seconds"] <= 900 and projection["rss_cap_bytes"] <= 603_979_776 and projection["scratch_cap_bytes"] <= 268_435_456 and projection["durable_cap_bytes"] <= 268_435_456 and projection["aggregate_io_cap"] <= 2_147_483_648 and telemetry["root_process_count"] == telemetry["process_count_peak"] == 1 and telemetry["child_process_count_peak"] == 0 and telemetry["thread_count_peak"] <= 32 and value["worker_count"] == 1
    if value["disposition"] != ("PERFORMANCE_READY" if ready else "REPAIR_REQUIRED"): raise ValueError("assessment readiness disposition mismatch")
    return dict(value)


def build_manifest(*, assessment: Mapping[str, Any], source_revision: str, source_inventory: list[dict[str, Any]], output_root: str, assessment_sha256: str, assessment_size_bytes: int) -> dict[str, Any]:
    validate_assessment(assessment)
    if assessment["disposition"] != "PERFORMANCE_READY": raise ValueError("prepare-run requires PERFORMANCE_READY")
    projection = assessment["projection"]
    resource_caps = {"wall_seconds": projection["guarded_wall_seconds"], "cpu_seconds": projection["guarded_cpu_seconds"], "process_tree_rss_bytes": projection["rss_cap_bytes"], "scratch_bytes": projection["scratch_cap_bytes"], "durable_bytes": projection["durable_cap_bytes"], "io_read_bytes": projection["read_cap_bytes"], "io_write_bytes": projection["write_cap_bytes"], "aggregate_io_bytes": projection["aggregate_io_cap"], "thread_cap": projection["thread_cap"], "process_cap": projection["process_cap"], "child_process_cap": projection["child_process_cap"]}
    config = WorkloadConfig.science(); binding_payload = {
        "object_id": OBJECT_ID, "config": config.to_dict(), "science_contract": ConditioningConfig.r01().to_dict(),
        "source_revision": source_revision, "source_inventory": source_inventory,
        "performance_assessment": {"assessment_id": ASSESSMENT_ID, "schema": ASSESS_FORMAT, "projection_law": PROJECTION_LAW, "sha256": assessment_sha256, "size_bytes": assessment_size_bytes, "source_aggregate": assessment["source_aggregate"], "snapshot_count_check": dict(assessment["snapshot_count_check"]), "disposition": assessment["disposition"]},
        "rng_version": RNG_VERSION,
        "data_ancestry_law": "counter_addressed_run_seed_episode_context_shared_across_arms",
        "batch_law": "ordered_rows_cyclic_batch_update_times_256_mod_inventory",
        "transform_implementation": "ordered_fp32_X_matmul_div_n_cholesky_lower_solve_triangular_column",
        "execution_topology": assessment["topology"],
        "scratch_root": f"{output_root}/work", "output_root": output_root, "resource_caps": resource_caps,
    }
    binding = hashlib.sha256(canonical_json_bytes(binding_payload)).hexdigest()
    return {"format": MANIFEST_FORMAT, "schema_version": SCHEMA_VERSION, **binding_payload, "binding": binding, "zero_effects": zero_effect_ledger()}


def validate_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    required = {"format", "schema_version", "object_id", "config", "science_contract", "source_revision", "source_inventory", "performance_assessment", "rng_version", "data_ancestry_law", "batch_law", "transform_implementation", "execution_topology", "scratch_root", "output_root", "binding", "resource_caps", "zero_effects"}
    if not isinstance(value, Mapping) or set(value) != required or value["format"] != MANIFEST_FORMAT or value["object_id"] != OBJECT_ID: raise ValueError("manifest schema/identity mismatch")
    if WorkloadConfig.from_dict(value["config"]) != WorkloadConfig.science(): raise ValueError("manifest must bind exact scientific configuration")
    ConditioningConfig.from_dict(value["science_contract"])
    assessment_record = value["performance_assessment"]
    if not isinstance(assessment_record, Mapping) or set(assessment_record) != {"assessment_id", "schema", "projection_law", "sha256", "size_bytes", "source_aggregate", "snapshot_count_check", "disposition"} or assessment_record["assessment_id"] != ASSESSMENT_ID or assessment_record["schema"] != ASSESS_FORMAT or assessment_record["projection_law"] != PROJECTION_LAW or assessment_record["snapshot_count_check"] != {"assessment": 8, "science": 48, "pass": True} or assessment_record["disposition"] != "PERFORMANCE_READY" or type(assessment_record["size_bytes"]) is not int or assessment_record["size_bytes"] <= 0: raise ValueError("manifest assessment-03 binding mismatch")
    cap_keys = {"wall_seconds", "cpu_seconds", "process_tree_rss_bytes", "scratch_bytes", "durable_bytes", "io_read_bytes", "io_write_bytes", "aggregate_io_bytes", "thread_cap", "process_cap", "child_process_cap"}
    if not isinstance(value["resource_caps"], Mapping) or set(value["resource_caps"]) != cap_keys or any(not isinstance(item, (int, float)) or isinstance(item, bool) or not math.isfinite(item) or item < 0 for item in value["resource_caps"].values()) or value["resource_caps"]["aggregate_io_bytes"] != value["resource_caps"]["io_read_bytes"] + value["resource_caps"]["io_write_bytes"]: raise ValueError("manifest V2 resource cap mismatch")
    topology = value["execution_topology"]
    _require_exact_topology(topology, label="manifest")
    payload = {key: value[key] for key in ("object_id", "config", "science_contract", "source_revision", "source_inventory", "performance_assessment", "rng_version", "data_ancestry_law", "batch_law", "transform_implementation", "execution_topology", "scratch_root", "output_root", "resource_caps")}
    if hashlib.sha256(canonical_json_bytes(payload)).hexdigest() != value["binding"] or value["zero_effects"] != zero_effect_ledger(): raise ValueError("manifest binding/firewall mismatch")
    return dict(value)


def build_recast_manifest(*, assessment_record: Mapping[str, Any], resource_caps: Mapping[str, Any], execution_topology: Mapping[str, Any], source_record: Mapping[str, Any], output_root: str) -> dict[str, Any]:
    """Manifest for the section-11 recast run.

    Differences from ``build_manifest``, and only these: the performance assessment is a
    recorded field (any assessment on disk, or none, with its contract declaration beside
    it) instead of a mandatory create-once ``assessment-03`` with a ``PERFORMANCE_READY``
    disposition; and the source revision/inventory carry the working-tree status instead of
    a refusal when it is dirty. Both demotions are §11.4. Everything the run's own claim
    needs -- exact scientific configuration, science contract, RNG version, data-ancestry
    law, batch law, transform implementation, zero-effect firewall -- is unchanged.
    """
    config = WorkloadConfig.science()
    binding_payload = {
        "object_id": OBJECT_ID, "config": config.to_dict(), "science_contract": ConditioningConfig.r01().to_dict(),
        "source_revision": source_record["revision"], "source_inventory": list(source_record["inventory"]),
        "source_status": dict(source_record["status"]),
        "performance_assessment": dict(assessment_record),
        "rng_version": RNG_VERSION,
        "data_ancestry_law": "counter_addressed_run_seed_episode_context_shared_across_arms",
        "batch_law": "ordered_rows_cyclic_batch_update_times_256_mod_inventory",
        "transform_implementation": "ordered_fp32_X_matmul_div_n_cholesky_lower_solve_triangular_column",
        "execution_topology": dict(execution_topology),
        "scratch_root": f"{output_root}/work", "output_root": output_root, "resource_caps": dict(resource_caps),
    }
    binding = hashlib.sha256(canonical_json_bytes(binding_payload)).hexdigest()
    return {"format": RECAST_MANIFEST_FORMAT, "schema_version": SCHEMA_VERSION, **binding_payload, "binding": binding, "zero_effects": zero_effect_ledger()}


def validate_recast_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    """Structural validation only for the recast manifest.

    It still binds the exact scientific configuration, science contract and zero-effect
    firewall, and it still detects tampering through the binding digest. It does not read
    the recorded assessment or source status as a pass/fail condition.
    """
    required = {"format", "schema_version", "object_id", "config", "science_contract", "source_revision", "source_inventory", "source_status", "performance_assessment", "rng_version", "data_ancestry_law", "batch_law", "transform_implementation", "execution_topology", "scratch_root", "output_root", "binding", "resource_caps", "zero_effects"}
    if not isinstance(value, Mapping) or set(value) != required or value["format"] != RECAST_MANIFEST_FORMAT or value["object_id"] != OBJECT_ID: raise ValueError("recast manifest schema/identity mismatch")
    if WorkloadConfig.from_dict(value["config"]) != WorkloadConfig.science(): raise ValueError("manifest must bind exact scientific configuration")
    ConditioningConfig.from_dict(value["science_contract"])
    assessment_record = value["performance_assessment"]
    if not isinstance(assessment_record, Mapping) or assessment_record.get("gating") is not False: raise ValueError("recast manifest assessment record must be marked non-gating")
    source_status = value["source_status"]
    if not isinstance(source_status, Mapping) or source_status.get("gating") is not False: raise ValueError("recast manifest source status must be marked non-gating")
    cap_keys = {"wall_seconds", "cpu_seconds", "process_tree_rss_bytes", "scratch_bytes", "durable_bytes", "io_read_bytes", "io_write_bytes", "aggregate_io_bytes", "thread_cap", "process_cap", "child_process_cap"}
    caps = value["resource_caps"]
    if not isinstance(caps, Mapping) or set(caps) != cap_keys: raise ValueError("recast manifest resource cap inventory mismatch")
    _require_exact_topology(value["execution_topology"], label="manifest")
    payload = {key: value[key] for key in ("object_id", "config", "science_contract", "source_revision", "source_inventory", "source_status", "performance_assessment", "rng_version", "data_ancestry_law", "batch_law", "transform_implementation", "execution_topology", "scratch_root", "output_root", "resource_caps")}
    if hashlib.sha256(canonical_json_bytes(payload)).hexdigest() != value["binding"] or value["zero_effects"] != zero_effect_ledger(): raise ValueError("manifest binding/firewall mismatch")
    return dict(value)


def validate_admission(value: Mapping[str, Any], *, now: datetime_module.datetime | None = None, maximum_age_seconds: float | None = 300.0) -> dict[str, Any]:
    assessment = value if isinstance(value, Mapping) else None
    required = {"schema_version", "captured_at", "assessed_at", "measurement_source", "minimum_available_bytes", "available_physical_bytes", "cgroup_memory_max_bytes", "cgroup_memory_current_bytes", "cgroup_headroom_bytes", "effective_available_bytes", "physical_floor_pass", "effective_floor_pass", "passed", "failure_reasons"}
    if not isinstance(assessment, Mapping) or set(assessment) != required or assessment.get("schema_version") != 1 or assessment.get("passed") is not True: raise ValueError("memory admission did not pass or schema drifted")
    if assessment.get("available_physical_bytes", 0) < MINIMUM_MEMORY_BYTES or assessment.get("effective_available_bytes", 0) < MINIMUM_MEMORY_BYTES: raise ValueError("memory admission below 4 GiB")
    if assessment.get("minimum_available_bytes") != MINIMUM_MEMORY_BYTES or assessment.get("physical_floor_pass") is not True or assessment.get("effective_floor_pass") is not True or assessment.get("failure_reasons") != []: raise ValueError("memory admission predicates drifted")
    try:
        captured = datetime_module.datetime.fromisoformat(str(assessment["captured_at"]).replace("Z", "+00:00")); assessed = datetime_module.datetime.fromisoformat(str(assessment["assessed_at"]).replace("Z", "+00:00"))
    except ValueError as exc: raise ValueError("memory admission timestamp invalid") from exc
    current = now or datetime_module.datetime.now(datetime_module.timezone.utc)
    if captured.tzinfo is None or assessed.tzinfo is None or not captured <= assessed <= current or (maximum_age_seconds is not None and (current - assessed).total_seconds() > maximum_age_seconds): raise ValueError("memory admission is stale or time-inconsistent")
    return dict(value)


def build_complete_result(workload, *, manifest: Mapping[str, Any], admission_record: Mapping[str, Any], resource_ledger: Mapping[str, Any], checkpoint_inventory: list[dict[str, Any]]) -> dict[str, Any]:
    return {"format": RESULT_FORMAT, "schema_version": SCHEMA_VERSION, "object_id": OBJECT_ID, "complete": True, "config": workload.config.to_dict(), "binding": workload.binding, "manifest_sha256": hashlib.sha256(canonical_json_bytes(manifest)).hexdigest(), "admission": dict(admission_record), "activity": workload.activity, "transform_evidence": list(workload.transform_evidence), "initialization_parity": list(workload.initialization_parity), "evaluations": [item.to_dict() for item in workload.evaluations], "reducer": workload.reducer, "checkpoints": checkpoint_inventory, "resources": dict(resource_ledger), "zero_effects": workload.zero_effects, "runtime": workload.runtime}


def _support_from_dict(value):
    converted = dict(value); converted["periods"] = tuple(converted["periods"]); return SupportEvaluation(**converted)


def validate_complete_result(value: Mapping[str, Any], *, complete_root: str | Path | None = None, allow_test: bool = False) -> dict[str, Any]:
    required = {"format", "schema_version", "object_id", "complete", "config", "binding", "manifest_sha256", "admission", "activity", "transform_evidence", "initialization_parity", "evaluations", "reducer", "checkpoints", "resources", "zero_effects", "runtime"}
    if not isinstance(value, Mapping) or set(value) != required or value["format"] != RESULT_FORMAT or value["complete"] is not True: raise ValueError("complete result schema mismatch")
    config = WorkloadConfig.from_dict(value["config"])
    if not allow_test and config != WorkloadConfig.science(): raise ValueError("complete result must bind exact scientific configuration")
    runtime = value["runtime"]
    if not isinstance(runtime, Mapping) or not isinstance(runtime.get("execution_topology"), Mapping): raise ValueError("complete result runtime topology missing")
    _require_exact_topology(runtime["execution_topology"], label="complete result")
    evaluations = []
    for item in value["evaluations"]:
        odd, even = _support_from_dict(item["odd"]), _support_from_dict(item["even"])
        validate_support_evaluation(odd); validate_support_evaluation(even)
        outer = (item["arm_id"], item["seed_id"], item["fold_id"], item["root_update"])
        if any((support.arm_id, support.seed_id, support.fold_id, support.root_update) != outer for support in (odd, even)): raise ValueError("checkpoint evaluation outer/support identity mismatch")
        sampled = item["sampled"]; cells = {context_id(context) for context in CONTEXTS}; expected_sample_episodes = len(CONTEXTS) * config.sampled_evaluation_episodes
        if not isinstance(sampled, Mapping) or set(sampled) != {"episodes", "transitions", "contexts"} or sampled["episodes"] != expected_sample_episodes or not isinstance(sampled["contexts"], Mapping) or set(sampled["contexts"]) != cells: raise ValueError("checkpoint sampled inventory/count mismatch")
        transition_sum = 0
        for row in sampled["contexts"].values():
            if not isinstance(row, Mapping) or set(row) != {"episodes", "transitions", "return_sum", "probe_count"} or row["episodes"] != config.sampled_evaluation_episodes or type(row["transitions"]) is not int or row["transitions"] <= 0 or type(row["probe_count"]) is not int or not 0 <= row["probe_count"] <= row["episodes"] or not isinstance(row["return_sum"], (int, float)) or isinstance(row["return_sum"], bool) or not math.isfinite(row["return_sum"]): raise ValueError("checkpoint sampled context row mismatch")
            transition_sum += row["transitions"]
        if sampled["transitions"] != transition_sum: raise ValueError("checkpoint sampled transition reconciliation mismatch")
        evaluations.append(CheckpointEvaluation(item["arm_id"], item["seed_id"], item["fold_id"], item["root_update"], odd, even, item["sampled"]))
    expected_evaluation_ids = {(arm, seed, fold, update) for arm in config.arms for seed in config.seed_ids for fold in (0, 1) for update in config.checkpoint_root_updates}
    observed_evaluation_ids = {(item.arm_id, item.seed_id, item.fold_id, item.root_update) for item in evaluations}
    if len(evaluations) != len(expected_evaluation_ids) or observed_evaluation_ids != expected_evaluation_ids: raise ValueError("complete result evaluation inventory mismatch")
    expected_activity = expected_counts(config)
    required_activity = set(expected_activity) | {"sampled_evaluation_transitions", "root_clip_events", "tail_clip_events", "nonfinite_events"}
    if not isinstance(value["activity"], Mapping) or set(value["activity"]) != required_activity: raise ValueError("complete result activity inventory mismatch")
    for key, expected in expected_activity.items():
        if value["activity"][key] != expected: raise ValueError("complete result activity mismatch")
    if value["activity"]["sampled_evaluation_transitions"] != sum(item.sampled["transitions"] for item in evaluations): raise ValueError("complete result sampled transition activity mismatch")
    if any(type(value["activity"][key]) is not int or value["activity"][key] < 0 for key in ("root_clip_events", "tail_clip_events", "nonfinite_events")): raise ValueError("complete result activity counter mismatch")
    expected_transform_ids = {(seed, fold, stage) for seed in config.seed_ids for fold in (0, 1) for stage in ("root", "tail")}
    transform_by_id = {(row.get("seed_id"), row.get("fold_id"), row.get("stage")): row for row in value["transform_evidence"]}
    expected_parity_ids = {(arm, seed, fold, stage) for arm in config.arms for seed in config.seed_ids for fold in (0, 1) for stage in ("root", "tail")}
    parity_by_id = {(row.get("arm_id"), row.get("seed_id"), row.get("fold_id"), row.get("stage")): row for row in value["initialization_parity"]}
    if len(value["transform_evidence"]) != len(expected_transform_ids) or len(value["initialization_parity"]) != len(expected_parity_ids) or set(transform_by_id) != expected_transform_ids or set(parity_by_id) != expected_parity_ids:
        raise ValueError("transform/parity evidence inventory mismatch")
    if any(not row.get("positive_diagonal") or not row.get("cholesky_success") or row.get("target_fields_read") != 0 or row.get("outcome_fields_read") != 0 or row.get("x_shape") != [config.episodes_per_context * (4 if row.get("stage") == "root" else 2), 7 if row.get("stage") == "root" else 5] or row.get("g_shape") != [7 if row.get("stage") == "root" else 5] * 2 or row.get("l_shape") != [7 if row.get("stage") == "root" else 5] * 2 or any(type(row.get(key)) is not str or len(row[key]) != 64 for key in ("ordered_x_sha256", "g_sha256", "l_sha256")) for row in value["transform_evidence"]):
        raise ValueError("transform evidence conformance mismatch")
    if any(row.get("maximum_absolute_error", float("inf")) > 32 * 2**-23 for row in value["initialization_parity"]):
        raise ValueError("initialization score parity mismatch")
    if value["reducer"] != reduce_results(evaluations, seed_ids=config.seed_ids, final_update=config.root_updates): raise ValueError("result reducer mismatch")
    if value["zero_effects"] != zero_effect_ledger() or any(value["zero_effects"].values()): raise ValueError("zero-effect firewall mismatch")
    expected_checkpoint_ids = {(arm, seed, fold, update) for arm in config.arms for seed in config.seed_ids for fold in (0, 1) for update in config.checkpoint_root_updates}
    checkpoint_by_id = {(row.get("arm_id"), row.get("seed_id"), row.get("fold_id"), row.get("root_update")): row for row in value["checkpoints"]}
    if len(value["checkpoints"]) != len(expected_checkpoint_ids) or set(checkpoint_by_id) != expected_checkpoint_ids: raise ValueError("checkpoint result inventory mismatch")
    if not allow_test:
        resources = value["resources"]
        if not isinstance(resources, Mapping): raise ValueError("result resource ledger mismatch")
        if resources.get("gating") is False:
            # Section-11 recast (2026-09-02): the projection caps are inherited from an
            # assessment the object's own contract declares ineligible, so a measured
            # exceedance is recorded, not invalidating (§11.4 capacity gate). Owner decision
            # 7: a missing measurement downgrades to resources_unmeasured, never annuls.
            recast_keys = {"observed", "caps", "within_caps", "gating", "cap_source", "cap_exceedances", "resources_unmeasured", "unmeasured_reasons"}
            if set(resources) != recast_keys: raise ValueError("recast result resource ledger inventory mismatch")
        else:
            if set(resources) != {"observed", "caps", "within_caps"} or resources["within_caps"] is not True: raise ValueError("result resource ledger mismatch")
            observed, caps = resources["observed"], resources["caps"]
            comparisons = (("wall_seconds", "wall_seconds"), ("cpu_seconds", "cpu_seconds"), ("process_tree_peak_rss_bytes", "process_tree_rss_bytes"), ("scratch_high_water_bytes", "scratch_bytes"), ("durable_high_water_bytes", "durable_bytes"), ("io_read_bytes", "io_read_bytes"), ("io_write_bytes", "io_write_bytes"), ("aggregate_io_bytes", "aggregate_io_bytes"), ("thread_count_peak", "thread_cap"), ("process_count_peak", "process_cap"), ("child_process_count_peak", "child_process_cap"))
            if any(observed.get(source, float("inf")) > caps.get(cap, -1) for source, cap in comparisons): raise ValueError("result resource cap violation")
    if complete_root is not None:
        root = Path(complete_root)
        for record in value["checkpoints"]:
            paths = {name: root / record[f"{name}_locator"] for name in ("full", "projection", "binding")}
            if any(not paths[name].is_file() or paths[name].stat().st_size != record[name]["size_bytes"] or hashlib.sha256(paths[name].read_bytes()).hexdigest() != record[name]["sha256"] for name in paths): raise ValueError("checkpoint publication tamper")
            from .checkpoint import load_checkpoint, load_evaluation_projection
            payload = load_checkpoint(paths["full"]); projection = load_evaluation_projection(paths["projection"])
            if payload["binding"] != value["binding"] or payload["config"] != config.to_dict() or (payload["arm_id"], payload["seed_id"], payload["fold_id"], payload["root_update"]) != (record["arm_id"], record["seed_id"], record["fold_id"], record["root_update"]): raise ValueError("checkpoint publication binding mismatch")
            if payload["evaluation_projection_sha256"] != record["projection"]["sha256"] or projection["root_state"]["beta"].equal(payload["root_state"]["beta"]) is False or projection["tail_state"]["beta"].equal(payload["tail_state"]["beta"]) is False or projection["transforms"] != payload["transforms"]: raise ValueError("full-shard/projection binding mismatch")
            binding_value = json.loads(paths["binding"].read_text(encoding="utf-8"))
            if binding_value != {"format": "UCOPE_BC_CONDITIONING_R01_SNAPSHOT_BINDING_V1", "identity": [record["arm_id"], record["seed_id"], record["fold_id"], record["root_update"]], "full": record["full"], "projection": record["projection"]}: raise ValueError("snapshot transaction binding mismatch")
            from .conditioning import TransformRecord
            for stage in ("root", "tail"):
                transform = TransformRecord.from_bytes(payload["transforms"][stage]); evidence = transform_by_id[(record["seed_id"], record["fold_id"], stage)]
                if hashlib.sha256(transform.gram_fp32_le).hexdigest() != evidence["g_sha256"] or hashlib.sha256(transform.cholesky_lower_fp32_le).hexdigest() != evidence["l_sha256"] or transform.ordered_design_sha256 != evidence["ordered_x_sha256"]: raise ValueError("checkpoint transform/evidence binding mismatch")
    return dict(value)


def stage_checkpoints(records, *, staging_root: str | Path) -> list[dict[str, Any]]:
    root = Path(staging_root); result = []
    for record in records:
        output = {key: record[key] for key in ("arm_id", "seed_id", "fold_id", "root_update")}
        for name, suffix in (("full", "full.pt"), ("projection", "eval.pt"), ("binding", "binding.json")):
            source = Path(record[name]["path"]); locator = f"checkpoints/{record['arm_id']}/{record['seed_id']}/fold-{record['fold_id']}/root-{record['root_update']:04d}.{suffix}"; destination = root / locator
            if destination.exists(): raise FileExistsError("staged checkpoint is create-once")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as source_stream, destination.open("xb") as destination_stream:
                shutil.copyfileobj(source_stream, destination_stream, length=1024 * 1024); destination_stream.flush(); os.fsync(destination_stream.fileno())
            output[f"{name}_locator"] = locator; output[name] = {"size_bytes": destination.stat().st_size, "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}
        result.append(output)
    return result

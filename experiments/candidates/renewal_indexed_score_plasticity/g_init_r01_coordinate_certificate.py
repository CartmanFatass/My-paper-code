"""R01 production binding and non-scientific TEST certificate builders."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CERTIFICATE_SCHEMA = "RISP-G-INIT-REACH-R01-COORDINATE-CERTIFICATE-20260821-01"
SCIENCE_REVISION = "RISP-G-INIT-REACH-SCIENCE-20260821-01"
COORDINATE_SCHEMA = "RISP-G-INIT-REACH-R01-LAZY-SHAKE256-PREFIX-20260821-01"
TEST_SCHEMA = "RISP-G-INIT-REACH-TEST-CERTIFICATE-V1"
TEST_REVISION = "RISP-G-INIT-REACH-TEST-FIXTURE-20260821-01"
TEST_NAMESPACE = "TEST/RISP-G-INIT-REACH/CERTIFICATE-FIXTURE/V1"
ROOT = Path(__file__).resolve().parents[3]
PRODUCTION_CERTIFICATE = ROOT / "experiments/candidates/renewal_indexed_score_plasticity/RISP_G_INIT_REACH_R01_PRODUCTION_CERTIFICATE_20260821_01.json"
PRODUCTION_FRONTIER = ROOT / "experiments/candidates/renewal_indexed_score_plasticity/RISP_G_INIT_REACH_R01_RESUME_20260821_01"
PRODUCTION_RESULT_ROOT = ROOT / "experiments/candidates/renewal_indexed_score_plasticity/RISP_G_INIT_REACH_R01_RESULTS_20260821_01"
RESULT_NAME = "RISP_G_INIT_REACH_R01_COMPLETE.json"
INTERPRETER = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
CANONICAL_COMPONENT = "risp.g_init_reach.r01.full_host"
DIRECTION_ID = "renewal_indexed_score_plasticity"
STAGE_ID = "RISP-G-INIT-REACH-R01-FULL-PANEL"
OBJECT_REVISION = "RISP-G-INIT-REACH-R01-FULL-PANEL / RISP-G-INIT-REACH-SCIENCE-20260821-01"
LEASE_ID = "RISP-G-INIT-REACH-R01-ROOT-EMPIRICAL-20260821-01"
BACKEND_ACCEPTANCE = ROOT / "experiments/candidates/renewal_indexed_score_plasticity/RISP_G_INIT_REACH_R01_BACKEND_EFFICIENCY_ACCEPTANCE_20260821_01.json"
WORKER_COUNT = 2
CPU_CORES = 2
GPU = False
COMPLETE_CPU_HOURS_UPPER = 32
COMPLETE_WALL_SECONDS_UPPER = 86400
SLICE_WALL_SECONDS = 13800
PER_WORKER_RSS_LIMIT_BYTES = 1073741824
PROCESS_GROUP_RSS_LIMIT_BYTES = 1610612736
FORBIDDEN_ROOTS = frozenset((
    "e2b7a0e30108dd261ee7612c3f79b9f21db21d8feb7c7c1fd356eaac5316e0c5",
    "e1578340aea90b521ee8be0ea75613bf349feed4617da4a776d0801eb02cd358",
    "9468480f3c1b2c8ca3cfb2dfcb6c8b7aa9b26bbc7ba0935574bcdf1e7bbbe2e3",
))
FORBIDDEN_PROVENANCE = frozenset(str(Path(path).resolve()) for path in (
    "C:/Projects/HMASD/temp/pytest_risp_g_r01_lifecycle_20260821/test_certificate_is_no_overwri0/TEST/certificate.json",
    "C:/Projects/HMASD/temp/pytest_risp_g_r01_lifecycle_20260821_b/test_certificate_is_no_overwri0/TEST/certificate.json",
    "C:/Projects/HMASD/temp/pytest_cm_risp_g_r01_integration_20260821/test_certificate_is_no_overwri0/TEST/certificate.json",
))
SCIENCE = ROOT / "docs/research/candidates/renewal_indexed_score_plasticity/RISP_G_INITIALIZATION_REACHABILITY_SCIENCE_CARD_R01.md"
PRO = ROOT / "docs/research/candidates/renewal_indexed_score_plasticity/RISP_G_INITIALIZATION_REACHABILITY_EXTERNAL_PRO_CLOSED_INTAKE_R01.md"
COST = ROOT / "docs/research/candidates/renewal_indexed_score_plasticity/RISP_G_INITIALIZATION_REACHABILITY_DEFINITION_AND_COST_MILESTONE_R01.md"
HANDOFF = ROOT / "docs/research/candidates/renewal_indexed_score_plasticity/RISP_G_INIT_REACH_R01_EMPIRICAL_STAGE_EM_HANDOFF_20260821.md"
PORTFOLIO = ROOT / "docs/research/workflow-runs/2026-08-11_five-round-research-team/RISP_G_INIT_REACH_R01_EMPIRICAL_PORTFOLIO_ADJUDICATION_20260821.md"
BACKEND_BINDING_INTERFACE = {
    "schema": "RISP-G-INIT-REACH-R01-ACCEPTED-SHARED-FULL-HOST-CPP-BINDING-V1",
    "required_fields": (
        "schema", "direction_id", "exact_object_revision", "component",
        "accepted_full_host_cpp", "native_artifact", "shared_functional_acceptance",
        "efficiency_review", "source_hashes", "test_hashes", "rollback_nodes",
    ),
    "component": CANONICAL_COMPONENT,
    "efficiency_schema": "RISP-G-INIT-REACH-R01-MANDATORY-EFFICIENCY-REVIEW-V1",
    "representative_schema": "RISP-G-INIT-REACH-TEST-REPRESENTATIVE-WORKERS-BENCHMARK-V1",
    "rollback_nodes": [
        "reject_backend_binding",
        "reject_lease_binding",
        "reject_coordinate_certificate",
        "discard_uncommitted_atomic_batch",
        "resume_same_coordinate_from_committed_frontier",
    ],
}
LEASE_BINDING_INTERFACE = {
    "schema": "RISP-G-INIT-REACH-R01-ROOT-DIRECTION-LEASE-V1",
    "required_fields": (
        "schema", "lease_id", "direction_id", "stage_id", "exact_object_revision",
        "production_authorized", "issued_at", "not_after", "backend_acceptance",
        "certificate", "frontier", "result_root", "result", "command", "resources",
    ),
    "resources": {
        "process_concurrency": WORKER_COUNT, "cpu_workers": WORKER_COUNT,
        "cpu_cores": CPU_CORES, "gpu": GPU,
        "complete_cpu_hours_upper": COMPLETE_CPU_HOURS_UPPER,
        "complete_wall_seconds_upper": COMPLETE_WALL_SECONDS_UPPER,
        "per_worker_rss_limit_bytes": PER_WORKER_RSS_LIMIT_BYTES,
        "process_group_rss_limit_bytes": PROCESS_GROUP_RSS_LIMIT_BYTES,
        "slice_wall_seconds": SLICE_WALL_SECONDS, "resumable_only": True,
    },
}

def _sha(path: Path) -> str:
    if not path.is_file(): raise RuntimeError(f"required immutable input absent: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()

def immutable_inputs() -> dict[str, str]:
    return {str(path.resolve()): _sha(path) for path in (SCIENCE, PRO, COST, HANDOFF, PORTFOLIO)}

def source_manifest() -> dict[str, str]:
    paths = (
        ROOT / "experiments/candidates/renewal_indexed_score_plasticity/g_init_r01_experiment.py",
        ROOT / "experiments/candidates/renewal_indexed_score_plasticity/g_init_r01_resume.py",
        ROOT / "experiments/candidates/renewal_indexed_score_plasticity/run_g_init_r01_resume.py",
        ROOT / "experiments/candidates/renewal_indexed_score_plasticity/g_init_r01_coordinate_certificate.py",
        ROOT / "experiments/candidates/renewal_indexed_score_plasticity/g_init_r01_native_backend.py",
        ROOT / "experiments/candidates/renewal_indexed_score_plasticity/g_init_r01_native_backend.cpp",
        ROOT / "experiments/candidates/renewal_indexed_score_plasticity/b2_r02_experiment.py",
        ROOT / "envs/native/production_backend.py",
    )
    return {str(path.resolve()): _sha(path) for path in paths}

def test_manifest() -> dict[str, str]:
    paths = (
        ROOT / "tests/experiments/candidates/renewal_indexed_score_plasticity/test_g_init_r01_experiment.py",
        ROOT / "tests/experiments/candidates/renewal_indexed_score_plasticity/test_g_init_r01_native_backend.py",
        ROOT / "tests/experiments/candidates/renewal_indexed_score_plasticity/test_g_init_r01_resume.py",
        ROOT / "tests/experiments/candidates/renewal_indexed_score_plasticity/test_g_init_r01_coordinate_certificate.py",
        ROOT / "tests/production_backend_policy_test.py",
    )
    return {str(path.resolve()): _sha(path) for path in paths}

def production_command() -> str:
    return (
        f"{INTERPRETER} experiments/candidates/renewal_indexed_score_plasticity/run_g_init_r01_resume.py "
        f"--certificate {PRODUCTION_CERTIFICATE} --frontier {PRODUCTION_FRONTIER} "
        f"--result-root {PRODUCTION_RESULT_ROOT} --workers {WORKER_COUNT} --cpu-cores {CPU_CORES} "
        f"--slice-wall-seconds {SLICE_WALL_SECONDS} --per-worker-rss-limit-bytes {PER_WORKER_RSS_LIMIT_BYTES} "
        f"--process-group-rss-limit-bytes {PROCESS_GROUP_RSS_LIMIT_BYTES}"
    )

def registered_panel() -> dict[str, Any]:
    return {"training_units": 32, "evaluation_units": 320, "atomic_units": 352, "algorithm_seeds": list(range(16)), "arms": ["G-START/ZERO-CENTER", "ZERO-START/ZERO-CENTER"], "cell_families": ["G-START/ZERO-CENTER-INTACT", "ZERO-START/ZERO-CENTER-INTACT", "UNIFORM", "STATE-ORACLE"], "schedules": ["4", "8", "12", "4->12", "12->4"], "updates": 512}

def _same(left: Path, right: Path) -> bool: return str(left.resolve()) == str(right.resolve())
def is_forbidden_provenance(path: Path) -> bool: return str(path.resolve()) in FORBIDDEN_PROVENANCE
def _valid_root(root: str) -> bool: return isinstance(root, str) and len(root) == 64 and all(ch in "0123456789abcdef" for ch in root)

def assert_production_paths(certificate: Path, frontier: Path, result_root: Path) -> None:
    paths = (certificate, frontier, result_root)
    if is_forbidden_provenance(certificate) or any("test" in part.lower() or "pytest" in part.lower() or part.lower() == "temp" for path in paths for part in path.resolve().parts):
        raise RuntimeError("TEST or fixture provenance is permanently ineligible for production")
    if not (_same(certificate, PRODUCTION_CERTIFICATE) and _same(frontier, PRODUCTION_FRONTIER) and _same(result_root, PRODUCTION_RESULT_ROOT)):
        raise RuntimeError("R01 production paths are frozen and exact")

def _atomic_no_overwrite_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): raise FileExistsError(f"certificate already exists: {path}")
    temporary = path.with_name(f".{path.name}.pending")
    if temporary.exists(): raise FileExistsError(f"uncommitted certificate scratch exists: {temporary}")
    payload = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload); handle.flush(); os.fsync(handle.fileno())
        os.link(temporary, path)  # atomic publication that refuses an existing target
        with path.open("a+b") as handle: os.fsync(handle.fileno())
    finally:
        if temporary.exists(): temporary.unlink()

def _binding_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file(): raise RuntimeError(f"{label} binding is absent")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"{label} binding is not JSON") from error
    if not isinstance(value, dict): raise RuntimeError(f"{label} binding is not an object")
    return value

def validate_backend_binding(path: Path) -> dict[str, Any]:
    value = _binding_json(path, "backend")
    required = BACKEND_BINDING_INTERFACE
    native = value.get("native_artifact")
    shared = value.get("shared_functional_acceptance")
    efficiency = value.get("efficiency_review")
    representative = efficiency.get("representative_workers") if isinstance(efficiency, dict) else None
    exact_hashes = (
        isinstance(representative, dict)
        and isinstance(representative.get("training_semantic_hashes"), list)
        and len(representative["training_semantic_hashes"]) == 4
        and isinstance(representative.get("evaluation_semantic_hashes"), list)
        and len(representative["evaluation_semantic_hashes"]) == 4
        and all(isinstance(digest, str) and len(digest) == 64 for digest in (*representative["training_semantic_hashes"], *representative["evaluation_semantic_hashes"]))
    )
    if (value.get("schema") != required["schema"] or value.get("direction_id") != "renewal_indexed_score_plasticity"
            or value.get("exact_object_revision") != "RISP-G-INIT-REACH-R01-FULL-PANEL / RISP-G-INIT-REACH-SCIENCE-20260821-01"
            or value.get("component") != required["component"] or value.get("accepted_full_host_cpp") is not True
            or not isinstance(native, dict)
            or native.get("schema") != "RISP-G-INIT-REACH-R01-NATIVE-ARTIFACT-IDENTITY-V1"
            or native.get("abi_version") != 1
            or not isinstance(native.get("runtime_abi"), dict)
            or native["runtime_abi"].get("struct_sizes") != {"reset_input": 160, "step_input": 64, "extended_step_input": 288, "transition_output": 104}
            or native.get("python_fallback") is not False
            or any(not isinstance(native.get(field), str) or len(native[field]) != 64 for field in ("build_key", "artifact_sha256", "source_sha256"))
            or not isinstance(shared, dict)
            or shared.get("schema") != "HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1"
            or shared.get("component") != CANONICAL_COMPONENT or shared.get("backend") != "cpp"
            or shared.get("batch_width") != 32 or shared.get("full_reset_step_cpp") is not True
            or shared.get("python_fallback") is not False
            or not isinstance(shared.get("native"), dict)
            or shared["native"].get("artifact_sha256") != native.get("artifact_sha256")
            or not isinstance(efficiency, dict) or efficiency.get("schema") != required["efficiency_schema"]
            or efficiency.get("status") != "COMPLETE" or efficiency.get("lease_ready") is not True
            or not isinstance(efficiency.get("projected_complete_cpu_hours"), (int, float))
            or not 0 < efficiency["projected_complete_cpu_hours"] <= COMPLETE_CPU_HOURS_UPPER
            or not isinstance(efficiency.get("projected_complete_wall_seconds"), (int, float))
            or not 0 < efficiency["projected_complete_wall_seconds"] <= COMPLETE_WALL_SECONDS_UPPER
            or not isinstance(representative, dict) or representative.get("schema") != required["representative_schema"]
            or representative.get("worker_count") != WORKER_COUNT or representative.get("exact_semantic_hashes") is not True
            or representative.get("per_worker_peak_rss_bytes", PER_WORKER_RSS_LIMIT_BYTES + 1) > PER_WORKER_RSS_LIMIT_BYTES
            or representative.get("process_group_ram_bytes", PROCESS_GROUP_RSS_LIMIT_BYTES + 1) > PROCESS_GROUP_RSS_LIMIT_BYTES
            or not exact_hashes
            or value.get("source_hashes") != source_manifest() or value.get("test_hashes") != test_manifest()
            or value.get("rollback_nodes") != required["rollback_nodes"]):
        raise RuntimeError("backend binding does not meet the frozen R01 interface")
    from envs.native import production_backend as shared_registry
    capability = shared_registry.backend_capability(CANONICAL_COMPONENT)
    if not capability.production_supported or not capability.full_reset_step_cpp or capability.loader_key != "risp_g_init_reach_r01_full_host":
        raise RuntimeError("R01 shared full-host C++ backend interface is not registered")
    return value

def _strict_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or len(value) != 20 or value[-1] != "Z":
        raise RuntimeError(f"lease {field} must be strict UTC seconds")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise RuntimeError(f"lease {field} must be strict UTC seconds") from error
    return parsed


def validate_lease_binding(path: Path, *, now: datetime | None = None) -> dict[str, Any]:
    value = _binding_json(path, "lease")
    required = LEASE_BINDING_INTERFACE
    backend = value.get("backend_acceptance")
    if (value.get("schema") != required["schema"] or value.get("lease_id") != LEASE_ID
            or value.get("direction_id") != DIRECTION_ID or value.get("stage_id") != STAGE_ID
            or value.get("exact_object_revision") != OBJECT_REVISION
            or value.get("production_authorized") is not True
            or value.get("certificate") != str(PRODUCTION_CERTIFICATE)
            or value.get("frontier") != str(PRODUCTION_FRONTIER)
            or value.get("result_root") != str(PRODUCTION_RESULT_ROOT)
            or value.get("result") != str(PRODUCTION_RESULT_ROOT / RESULT_NAME)
            or value.get("command") != production_command()
            or value.get("resources") != required["resources"]
            or not isinstance(backend, dict)
            or backend.get("path") != str(BACKEND_ACCEPTANCE)
            or not isinstance(backend.get("sha256"), str) or len(backend["sha256"]) != 64):
        raise RuntimeError("lease binding does not meet the frozen R01 interface")
    if not BACKEND_ACCEPTANCE.is_file() or _sha(BACKEND_ACCEPTANCE) != backend["sha256"]:
        raise RuntimeError("lease backend acceptance hash mismatch")
    issued_at, not_after = _strict_utc(value.get("issued_at"), "issued_at"), _strict_utc(value.get("not_after"), "not_after")
    observed_now = datetime.now(timezone.utc) if now is None else now
    if observed_now.tzinfo is None or observed_now.utcoffset() != timezone.utc.utcoffset(observed_now):
        raise RuntimeError("lease validation now must be UTC-aware")
    observed_now = observed_now.astimezone(timezone.utc)
    if issued_at > observed_now or observed_now >= not_after:
        raise RuntimeError("lease is future-issued or expired")
    if (not_after - observed_now).total_seconds() < SLICE_WALL_SECONDS:
        raise RuntimeError("lease validity does not cover one complete slice")
    return value

def existing_recorded_production_roots() -> frozenset[str]:
    """Read only the uniquely frozen production record; never inspect TEST roots."""
    if not PRODUCTION_CERTIFICATE.is_file(): return frozenset()
    value = _binding_json(PRODUCTION_CERTIFICATE, "existing production certificate")
    root = value.get("coordinate_root")
    return frozenset((root,)) if _valid_root(root) else frozenset()

def build_production_certificate(*, output: Path, frontier: Path, result_root: Path, backend_binding: Path, lease_binding: Path) -> dict[str, Any]:
    """Future-only binding; it cannot be called with test paths or missing gates."""
    assert_production_paths(output, frontier, result_root)
    if output.exists(): raise FileExistsError(f"certificate already exists: {output}")
    validate_backend_binding(backend_binding)
    validate_lease_binding(lease_binding)
    existing_roots = existing_recorded_production_roots()
    inputs = immutable_inputs()
    sources = source_manifest()
    root = secrets.token_hex(32)
    if root in FORBIDDEN_ROOTS or root in existing_roots: raise RuntimeError("generated root is excluded or already recorded; no redraw is permitted")
    packet = {
        "certificate_schema": CERTIFICATE_SCHEMA, "science_revision": SCIENCE_REVISION, "coordinate_schema": COORDINATE_SCHEMA,
        "coordinate_root": root, "coordinate_binding_activity_started": True,
        "coordinate_binding_activity_fact": "sole production coordinate binding committed before any model, optimizer, training, or evaluation",
        "technical_acceptance": True, "backend_binding": {"path": str(backend_binding.resolve()), "sha256": _sha(backend_binding)},
        "lease_binding": {"path": str(lease_binding.resolve()), "sha256": _sha(lease_binding)},
        "model_or_optimizer_materialized": False, "training_or_evaluation_executed": False, "partial_scientific_values_exposed": False,
        "immutable_inputs": inputs, "source_manifest": sources,
        "registered_panel": registered_panel(),
        "paths": {"certificate": str(PRODUCTION_CERTIFICATE), "frontier": str(PRODUCTION_FRONTIER), "result_root": str(PRODUCTION_RESULT_ROOT), "result": str(PRODUCTION_RESULT_ROOT / RESULT_NAME)},
        "production": {
            "interpreter": INTERPRETER, "working_directory": str(ROOT), "command": production_command(),
            **LEASE_BINDING_INTERFACE["resources"],
        },
    }
    _atomic_no_overwrite_json(output.resolve(), packet)
    return packet

def build_test_fixture(output: Path, fixture_root: str = "f" * 64) -> dict[str, Any]:
    output = output.resolve()
    if not _valid_root(fixture_root): raise ValueError("fixture root must be 64 lowercase hexadecimal characters")
    if TEST_NAMESPACE not in str(output).replace("\\", "/") and "TEST" not in {part.upper() for part in output.parts}: raise RuntimeError("TEST fixture must remain in TEST provenance")
    packet = {"certificate_schema": TEST_SCHEMA, "coordinate_schema": TEST_SCHEMA, "test_fixture_revision": TEST_REVISION, "namespace": TEST_NAMESPACE, "fixture_root": fixture_root, "fixture_only": True}
    _atomic_no_overwrite_json(output, packet)
    return packet

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", required=True, type=Path); parser.add_argument("--frontier", required=True, type=Path); parser.add_argument("--result-root", required=True, type=Path); parser.add_argument("--backend-binding", required=True, type=Path); parser.add_argument("--lease-binding", required=True, type=Path)
    args = parser.parse_args(); build_production_certificate(output=args.output, frontier=args.frontier, result_root=args.result_root, backend_binding=args.backend_binding, lease_binding=args.lease_binding)
    print('{"certificate_committed":true}', flush=True)
    return 0
if __name__ == "__main__": raise SystemExit(main())

"""Lease-gated production runner for the exact RCLE-TBCFV r04 panel.

The public proposal and preflight functions are result-blind.  The production
entry points validate the accepted preactivity certificate, the CM binding, an
active Operational-Root lease, and one already-materialized fresh coordinate
binding *before* loading the native host, deriving a random word, or opening an
empirical frontier.  There is no Python environment fallback.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import io
import json
import math
import multiprocessing
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Callable, Final, Mapping, Sequence

import torch
import numpy as np

from envs.native.production_backend import require_cpp_batched_production

from .config import LEARNED_PACKAGES, SCIENCE_REVISION, SCRIPTED_PACKAGES
from .empirical_artifacts import (
    ArtifactRef,
    RESULT_OUTPUT_SCHEMA,
    AtomicEmpiricalFrontier,
    BLOCK_COUNTS,
    EmpiricalBindings,
    ResumeState,
)
from .empirical_contract import (
    EMPIRICAL_OBJECT,
    MATERIALIZED_BINDING_SCHEMA,
    PANEL_COUNTS,
    PRODUCTION_SOURCE_LOGICAL_PATHS,
    RootLeasePermit,
    SELECTED_BATCH_WIDTH,
    SUPPORTED_BATCH_WIDTHS,
    SHARED_COMPONENT,
    canonical_json_bytes,
    coordinate_proposal,
    document_sha256,
    resource_request_proposal,
    validate_accepted_binding,
    validate_archived_initial_lease_for_source_repair,
    validate_frozen_run_identity,
    validate_preactivity_certificate,
    validate_root_lease,
    validate_source_repair_replacement_lease,
    validate_source_repair_transition,
)
from .native_backend import (
    bind_native_backend,
    native_artifact_identity,
    materialize_fixtures_compact as native_materialize_fixtures_compact,
    semantic_claims as native_semantic_claims,
    semantic_claims_compact as native_semantic_claims_compact,
    semantic_uniform_words as native_semantic_uniform_words,
)
from .host_oracle import (
    ACTIVE_CONTINUATION as HOST_ACTIVE_CONTINUATION,
    EVENT_POSITION,
    NEW_EPOCH as HOST_NEW_EPOCH,
    EventInput,
    FixtureSpec,
    Snapshot,
    StepInput,
)
from .inference import HELDOUT_CELLS, TRAINING_CELLS
from .models import (
    ManagerOutput,
    TBCFVModel,
    apply_affine_fixture_uniforms,
    apply_registered_block_update,
    exact_advantage_loss,
    make_conformance_fixture_model,
    make_pointer_inputs,
    required_affine_fixture_uniforms,
    selected_claim_log_probability,
    stopped_normal_inverse_cdf,
    stopped_normal_log_density,
)
from .process_workers import (
    make_process_resource_object,
    make_spawn_payload,
    make_worker_authorization,
    run_production_block_worker,
    tree_size_bytes,
    validate_process_resource_object,
    validate_production_worker_packet,
    write_spawn_payload,
)
from .native_backend import reset_native_batch
from .packages import FixtureDrawBank, PlanState, initialize_plans, transition_plans
from .scripted import coherent_scaffold, fragmented_scaffold, independent_nearest


OWNER_TOKEN: Final[str] = "CM-RCLE-TBCFV-R04-PRODUCTION-PARENT"
RUNNER_SCHEMA: Final[str] = "RCLE_TBCFV_R04_EMPIRICAL_RUNNER_V1"
_HEX = re.compile(r"[0-9a-f]{64}")
_SAFE_IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
_AUTHORITY_SEAL: Final[object] = object()
_SUPPORTED_WORKERS: Final[tuple[int, ...]] = (1, 2, 4)
_POSITION_FEATURES: Final[torch.Tensor] = torch.tensor(
    [
        [
            math.sin(2.0 * math.pi * position / 120.0),
            math.cos(2.0 * math.pi * position / 120.0),
        ]
        for position in range(120)
    ],
    dtype=torch.float64,
)
_CELL_CODES: Final[dict[str, int]] = {
    cell: index for index, cell in enumerate((*TRAINING_CELLS, *HELDOUT_CELLS))
}


class EmpiricalRunnerError(RuntimeError):
    """The production runner cannot preserve the exact admitted object."""


def _read_canonical_mapping(path: str | Path, label: str) -> dict[str, object]:
    target = Path(path)
    if not target.is_file() or target.is_symlink():
        raise EmpiricalRunnerError(f"{label} is absent or not a regular file")
    payload = target.read_bytes()
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EmpiricalRunnerError(f"{label} is not canonical ASCII JSON") from exc
    if not isinstance(value, Mapping) or canonical_json_bytes(value) != payload:
        raise EmpiricalRunnerError(f"{label} is not an exact canonical mapping")
    return dict(value)


def _inside_repository(path: str | Path) -> Path:
    repository = Path(__file__).resolve().parents[3]
    resolved = Path(path).resolve()
    try:
        resolved.relative_to(repository)
    except ValueError as exc:
        raise EmpiricalRunnerError("result root escapes the repository") from exc
    return resolved


def _validate_live_source_set(certificate: Mapping[str, object]) -> None:
    """Rehash every repository-relative source named by the accepted certificate."""

    source = certificate.get("source")
    if not isinstance(source, Mapping) or not isinstance(source.get("files"), Mapping):
        raise EmpiricalRunnerError("certificate source inventory is malformed")
    repository = Path(__file__).resolve().parents[3]
    for label, row in source["files"].items():  # type: ignore[union-attr]
        if not isinstance(label, str) or not isinstance(row, Mapping):
            raise EmpiricalRunnerError("certificate source row is malformed")
        target = (repository / Path(label)).resolve()
        try:
            target.relative_to(repository)
        except ValueError as exc:
            raise EmpiricalRunnerError("certificate source label escapes repository") from exc
        if not target.is_file() or target.is_symlink():
            raise EmpiricalRunnerError(f"accepted source is absent: {label}")
        payload = target.read_bytes()
        if row.get("bytes") != len(payload) or row.get("sha256") != hashlib.sha256(payload).hexdigest():
            raise EmpiricalRunnerError(f"accepted source bytes drifted: {label}")


def validate_materialized_binding(
    value: Mapping[str, object], permit: RootLeasePermit, *, now: datetime
) -> dict[str, object]:
    """Validate an externally materialized 20-block binding without deriving it."""

    permit.require_active(now=now)

    keys = {
        "schema",
        "identity",
        "science_revision",
        "empirical_object",
        "fixture_only",
        "non_scientific",
        "authority",
        "stage_binding_sha256",
        "numeric_seed_present",
        "master_material_exposed",
        "master_digest",
        "run_block_count",
        "run_block_roots",
        "binding_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != keys:
        raise EmpiricalRunnerError("materialized coordinate binding inventory differs")
    body = {key: value[key] for key in keys - {"binding_sha256"}}
    if value["binding_sha256"] != document_sha256(body):
        raise EmpiricalRunnerError("materialized coordinate binding digest differs")
    if (
        value["schema"] != MATERIALIZED_BINDING_SCHEMA
        or value["science_revision"] != SCIENCE_REVISION
        or value["empirical_object"] != EMPIRICAL_OBJECT
        or value["fixture_only"] is not False
        or value["non_scientific"] is not False
        or value["authority"] != permit.origin_lease_id
        or value["stage_binding_sha256"] != permit.stage_binding_sha256
        or value["numeric_seed_present"] is not False
        or value["master_material_exposed"] is not False
        or value["run_block_count"] != 20
    ):
        raise EmpiricalRunnerError("materialized coordinate binding is not fresh production r04")
    master_digest = value["master_digest"]
    binding_digest = value["binding_sha256"]
    if not isinstance(master_digest, str) or _HEX.fullmatch(master_digest) is None:
        raise EmpiricalRunnerError("materialized master digest is malformed")
    if not isinstance(binding_digest, str) or _HEX.fullmatch(binding_digest) is None:
        raise EmpiricalRunnerError("materialized binding digest is malformed")
    roots = value["run_block_roots"]
    if not isinstance(roots, list) or len(roots) != 20:
        raise EmpiricalRunnerError("materialized binding must contain exactly twenty roots")
    observed: list[int] = []
    root_digests: set[str] = set()
    for expected, row in enumerate(roots):
        if not isinstance(row, Mapping) or set(row) != {"block_index", "root_digest"}:
            raise EmpiricalRunnerError("run-block root schema differs")
        if row["block_index"] != expected:
            raise EmpiricalRunnerError("run-block roots are not the exact ordered 0..19 family")
        digest = row["root_digest"]
        if not isinstance(digest, str) or _HEX.fullmatch(digest) is None:
            raise EmpiricalRunnerError("run-block root digest is malformed")
        observed.append(expected)
        root_digests.add(digest)
    if observed != list(range(20)) or len(root_digests) != 20:
        raise EmpiricalRunnerError("run-block roots must be fresh and pairwise distinct")
    identity = value["identity"]
    if (
        not isinstance(identity, str)
        or _SAFE_IDENTITY.fullmatch(identity) is None
        or identity.upper().startswith(("TEST", "SYNTHETIC", "FIXTURE"))
    ):
        raise EmpiricalRunnerError("synthetic/test coordinate identity is forbidden in production")
    return dict(value)


@dataclass(frozen=True, repr=False)
class ProductionAuthority:
    certificate: Mapping[str, object]
    accepted_binding: Mapping[str, object]
    resource_request: Mapping[str, object]
    lease_document: Mapping[str, object]
    permit: RootLeasePermit
    coordinate_binding: Mapping[str, object]
    result_root: Path
    original_frontier_bindings: EmpiricalBindings | None = None
    source_repair_transition: Mapping[str, object] | None = None
    _seal: object | None = None

    def require_active(self, *, now: datetime) -> None:
        if self._seal is not _AUTHORITY_SEAL:
            raise EmpiricalRunnerError("unvalidated production authority")
        self.permit.require_active(now=now)

    @property
    def coordinate_digest(self) -> str:
        return str(self.coordinate_binding["binding_sha256"])

    @property
    def master_digest(self) -> str:
        return str(self.coordinate_binding["master_digest"])

    def block_root_digest(self, block_index: int) -> str:
        if isinstance(block_index, bool) or not isinstance(block_index, int) or not 0 <= block_index < 20:
            raise EmpiricalRunnerError("run block index must be in [0,19]")
        roots = self.coordinate_binding["run_block_roots"]
        assert isinstance(roots, list)
        row = roots[block_index]
        assert isinstance(row, Mapping)
        return str(row["root_digest"])


def admit_production(
    *,
    certificate: Mapping[str, object],
    accepted_binding: Mapping[str, object],
    resource_request: Mapping[str, object],
    lease: Mapping[str, object],
    coordinate_binding: Mapping[str, object],
    result_root: str | Path,
    now: datetime,
    predecessor_leases: Sequence[Mapping[str, object]] = (),
) -> ProductionAuthority:
    """Validate every authority object before native load/RNG/frontier access."""

    cert = validate_preactivity_certificate(certificate)
    accepted = validate_accepted_binding(accepted_binding, cert)
    _validate_live_source_set(cert)
    predecessor_permit: RootLeasePermit | None = None
    for predecessor in predecessor_leases:
        issued = predecessor.get("issued_at")
        if not isinstance(issued, str):
            raise EmpiricalRunnerError("predecessor lease issued_at is malformed")
        try:
            historical_now = datetime.fromisoformat(issued.replace("Z", "+00:00"))
        except ValueError as exc:
            raise EmpiricalRunnerError("predecessor lease issued_at is malformed") from exc
        predecessor_permit = validate_root_lease(
            predecessor,
            certificate=cert,
            accepted_binding=accepted,
            resource_request=resource_request,
            now=historical_now,
            predecessor_permit=predecessor_permit,
        )
    permit = validate_root_lease(
        lease,
        certificate=cert,
        accepted_binding=accepted,
        resource_request=resource_request,
        now=now,
        predecessor_permit=predecessor_permit,
    )
    permit.require_active(now=now)
    materialized = validate_materialized_binding(coordinate_binding, permit, now=now)
    resolved_root = _inside_repository(result_root)
    leased_root = Path(permit.paths["result_root"]).resolve()
    if resolved_root != leased_root:
        raise EmpiricalRunnerError("result root differs from the active Root lease")
    request_paths = resource_request.get("paths")
    if not isinstance(request_paths, Mapping) or Path(str(request_paths.get("result_root"))).resolve() != resolved_root:
        raise EmpiricalRunnerError("resource request and result root differ")
    return ProductionAuthority(
        certificate=cert,
        accepted_binding=accepted,
        resource_request=dict(resource_request),
        lease_document=dict(lease),
        permit=permit,
        coordinate_binding=materialized,
        result_root=resolved_root,
        _seal=_AUTHORITY_SEAL,
    )


def admit_source_repair(
    *,
    predecessor_certificate: Mapping[str, object],
    predecessor_accepted_binding: Mapping[str, object],
    predecessor_resource_request: Mapping[str, object],
    predecessor_lease: Mapping[str, object],
    certificate: Mapping[str, object],
    accepted_binding: Mapping[str, object],
    resource_request: Mapping[str, object],
    lease: Mapping[str, object],
    repair_transition: Mapping[str, object],
    run_identity_path: str | Path,
    failed_terminal_path: str | Path,
    result_root: str | Path,
    now: datetime,
) -> ProductionAuthority:
    """Admit the sole source-only bridge from one already materialized run."""

    original_permit = validate_archived_initial_lease_for_source_repair(
        predecessor_lease,
        certificate=predecessor_certificate,
        accepted_binding=predecessor_accepted_binding,
        resource_request=predecessor_resource_request,
        repair_transition=repair_transition,
    )
    frozen_run = validate_frozen_run_identity(run_identity_path, original_permit)
    source_deltas = repair_transition.get("source_deltas")
    if not isinstance(source_deltas, list) or any(
        not isinstance(row, Mapping) for row in source_deltas
    ):
        raise EmpiricalRunnerError("source repair delta inventory is malformed")
    transition = validate_source_repair_transition(
        repair_transition,
        original_certificate=predecessor_certificate,
        original_binding=predecessor_accepted_binding,
        original_request=predecessor_resource_request,
        original_permit=original_permit,
        repaired_certificate=certificate,
        repaired_binding=accepted_binding,
        repaired_request=resource_request,
        run_identity_path=run_identity_path,
        failed_terminal_path=failed_terminal_path,
        source_deltas=source_deltas,
    )
    cert = validate_preactivity_certificate(certificate)
    accepted = validate_accepted_binding(accepted_binding, cert)
    _validate_live_source_set(cert)
    permit = validate_source_repair_replacement_lease(
        lease,
        repair_transition=transition,
        original_permit=original_permit,
        repaired_certificate=cert,
        repaired_binding=accepted,
        repaired_request=resource_request,
        now=now,
    )
    permit.require_active(now=now)

    coordinate = _read_canonical_mapping(run_identity_path, "frozen RUN_IDENTITY")
    run_facts = transition.get("run_identity")
    original = transition.get("original")
    repaired = transition.get("repaired")
    preserved = transition.get("preserved")
    if not all(isinstance(item, Mapping) for item in (run_facts, original, repaired, preserved)):
        raise EmpiricalRunnerError("source repair transition locators are malformed")
    assert isinstance(run_facts, Mapping)
    assert isinstance(original, Mapping)
    assert isinstance(repaired, Mapping)
    assert isinstance(preserved, Mapping)
    if (
        dict(run_facts) != frozen_run
        or coordinate.get("binding_sha256") != run_facts.get("binding_sha256")
        or coordinate.get("master_digest") != run_facts.get("master_digest")
        or coordinate.get("stage_binding_sha256") != original_permit.stage_binding_sha256
        or coordinate.get("authority") != original_permit.origin_lease_id
        or coordinate.get("run_block_roots") != run_facts.get("run_block_roots")
    ):
        raise EmpiricalRunnerError("frozen RUN_IDENTITY differs after transition validation")

    resolved_root = _inside_repository(result_root)
    old_paths = predecessor_resource_request.get("paths")
    new_paths = resource_request.get("paths")
    if not isinstance(old_paths, Mapping) or not isinstance(new_paths, Mapping):
        raise EmpiricalRunnerError("source repair request paths are malformed")
    root_candidates = (
        old_paths.get("result_root"),
        new_paths.get("result_root"),
        original_permit.paths.get("result_root"),
        permit.paths.get("result_root"),
        preserved.get("result_root"),
    )
    if any(Path(str(item)).resolve() != resolved_root for item in root_candidates):
        raise EmpiricalRunnerError("source repair cannot change the result root")
    if Path(run_identity_path).resolve() != resolved_root / "RUN_IDENTITY.json":
        raise EmpiricalRunnerError("source repair RUN_IDENTITY path differs from result root")
    expected_frontier = resolved_root / "frontiers"
    if (
        Path(str(old_paths.get("frontier_root"))).resolve() != expected_frontier
        or Path(str(new_paths.get("frontier_root"))).resolve() != expected_frontier
        or Path(str(original_permit.paths.get("frontier_root"))).resolve()
        != expected_frontier
        or Path(str(permit.paths.get("frontier_root"))).resolve() != expected_frontier
        or not expected_frontier.is_dir()
    ):
        raise EmpiricalRunnerError("source repair cannot create or redirect the frontier")

    original_bindings = EmpiricalBindings(
        source_manifest_sha256=str(original["source_set_sha256"]),
        config_sha256=str(preserved["config_sha256"]),
        native_binding_sha256=str(preserved["native_identity_sha256"]),
        coordinate_digest=str(preserved["coordinate_binding_sha256"]),
        master_digest=str(preserved["master_digest"]),
        origin_lease_id=original_permit.origin_lease_id,
        lease_id=original_permit.origin_lease_id,
        lease_binding_sha256=str(original["stage_binding_sha256"]),
    )
    original_bindings.validate()
    if (
        repaired.get("source_set_sha256")
        != cert["source"]["source_set_sha256"]  # type: ignore[index]
        or repaired.get("stage_binding_sha256") != permit.stage_binding_sha256
    ):
        raise EmpiricalRunnerError("repaired certificate/stage locator differs")
    return ProductionAuthority(
        certificate=cert,
        accepted_binding=accepted,
        resource_request=dict(resource_request),
        lease_document=dict(lease),
        permit=permit,
        coordinate_binding=coordinate,
        result_root=resolved_root,
        original_frontier_bindings=original_bindings,
        source_repair_transition=transition,
        _seal=_AUTHORITY_SEAL,
    )


def _preactivity_temp_root(value: str | Path) -> Path:
    """Admit one explicit scratch parent without treating it as a result root."""

    root = Path(value).resolve()
    if root.exists() and (not root.is_dir() or root.is_symlink()):
        raise EmpiricalRunnerError("preflight temp root must be a real directory")
    root.mkdir(parents=True, exist_ok=True)
    probe = root / ".rcle_tbcfv_preactivity_write_probe"
    try:
        with probe.open("xb") as stream:
            stream.write(b"TEST-ONLY\n")
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if probe.exists():
            probe.unlink()
    return root


def _result_blind_native_receipt(certificate: Mapping[str, object]) -> dict[str, object]:
    """Load and bind the accepted shared ABI2 B8 implementation, without activity."""

    receipt = require_cpp_batched_production(
        SHARED_COMPONENT,
        backend="cpp",
        batch_width=SELECTED_BATCH_WIDTH,
    )
    if (
        receipt.get("schema") != "HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1"
        or receipt.get("component") != SHARED_COMPONENT
        or receipt.get("backend") != "cpp"
        or receipt.get("batch_width") != SELECTED_BATCH_WIDTH
        or receipt.get("full_reset_step_cpp") is not True
        or receipt.get("python_fallback") is not False
    ):
        raise EmpiricalRunnerError("shared native production receipt differs")
    frozen = certificate.get("native")
    if not isinstance(frozen, Mapping):
        raise EmpiricalRunnerError("certificate native identity is malformed")
    observed = native_artifact_identity()
    if (
        observed.get("sha256") != frozen.get("artifact_sha256")
        or observed.get("source_sha256") != frozen.get("source_sha256")
        or observed.get("build_key") != frozen.get("build_key")
        or document_sha256(observed.get("runtime_abi"))
        != document_sha256(frozen.get("runtime_abi"))
        or document_sha256(observed.get("toolchain"))
        != document_sha256(frozen.get("toolchain"))
        or observed.get("abi")
        != {
            "abi_version": 2,
            "fixture_magic": 0x52434C4554424347,
            "fixture_input_size": 224,
            "step_input_size": 64,
            "event_input_size": 64,
            "snapshot_size": 464,
        }
    ):
        raise EmpiricalRunnerError("live shared ABI2 identity differs from acceptance")
    return {
        "shared_receipt_validated": True,
        "component": SHARED_COMPONENT,
        "batch_width": SELECTED_BATCH_WIDTH,
        "abi_version": 2,
        "source_sha256": observed["source_sha256"],
        "build_key": observed["build_key"],
        "artifact_sha256": observed["sha256"],
        "python_fallback": False,
    }


def _synthetic_analyzer_rejection() -> dict[str, object]:
    """Exercise the production admission fence before any TEST aggregate is read."""

    from .empirical_inference import (
        EMPIRICAL_ANALYZER_INPUT_SCHEMA,
        SYNTHETIC_TEST_ONLY,
        analyze_empirical_complete_panel,
    )

    bindings = EmpiricalBindings(
        source_manifest_sha256="1" * 64,
        config_sha256="2" * 64,
        native_binding_sha256="3" * 64,
        coordinate_digest="4" * 64,
        master_digest="5" * 64,
        origin_lease_id="SYNTHETIC-TEST-PREFLIGHT",
        lease_id="SYNTHETIC-TEST-PREFLIGHT",
        lease_binding_sha256="6" * 64,
    )
    # Every record has the complete production field inventory, but its TEST
    # classification must be rejected before the sentinel aggregate is read.
    records = []
    for block_index in range(20):
        records.append(
            {
                "schema": EMPIRICAL_ANALYZER_INPUT_SCHEMA,
                "science_revision": SCIENCE_REVISION,
                "empirical_object": EMPIRICAL_OBJECT,
                "record_class": SYNTHETIC_TEST_ONLY,
                "empirical_record": False,
                "fixture_only": True,
                "synthetic_test_only": True,
                "block_index": block_index,
                "block_complete_sha256": None,
                "aggregate_sha256": None,
                "bindings": None,
                "technical_complete": False,
                "complete_marker_bound": False,
                "treatment_fidelity": False,
                "analytic_containment": False,
                "selection_or_adaptation": False,
                "evaluation_adaptation": False,
                "forbidden_information": False,
                "registered_coordinate": False,
                "learned_arms": None,
                "scripted_packages": None,
                "training_cells": None,
                "heldout_cells": None,
                "updates_completed": None,
                "training_cell_episodes": None,
                "learned_heldout_episodes": None,
                "scripted_heldout_episodes": None,
                "counts": None,
                "aggregates": None,
            }
        )
    outcome = analyze_empirical_complete_panel(records, expected_bindings=bindings)
    if (
        outcome.admitted_empirical
        or outcome.scientific_branch is not None
        or outcome.analyzer_payload is not None
        or outcome.bounds
        or outcome.gates
        or outcome.predicates
    ):
        raise EmpiricalRunnerError("TEST-only analyzer record escaped the production fence")
    return {
        "test_records": len(records),
        "production_admission_rejected": True,
        "scientific_output_exposed": False,
    }


def _synthetic_runner_chain() -> dict[str, object]:
    """Run real B8 runner consumers on one fixed non-scientific product family."""

    rng = SyntheticTestRNG("SYNTHETIC-TEST-RCLE-TBCFV-RUNNER-A")
    model = make_conformance_fixture_model()
    baselines, counts = execute_training_update(
        model,
        LEARNED_PACKAGES[1],
        rng,
        0,
        torch.zeros(8, dtype=torch.float64),
    )
    if tuple(baselines.shape) != (8,) or counts.get("training_episodes") != 64:
        raise EmpiricalRunnerError("synthetic exact training-update seam is incomplete")
    heldout = tuple(
        EpisodeCoordinate(0, HELDOUT_CELLS[0], 800, index)
        for index in range(SELECTED_BATCH_WIDTH)
    )
    learned = execute_learned_batch(model, LEARNED_PACKAGES[1], rng, heldout, training=False)
    if len(learned) != SELECTED_BATCH_WIDTH or any(
        item.plan_scores or item.claim_scores for item in learned
    ):
        raise EmpiricalRunnerError("synthetic learned heldout consumer differs")
    scripted_batches = [
        execute_scripted_batch(package, rng, heldout) for package in SCRIPTED_PACKAGES
    ]
    if any(len(batch) != SELECTED_BATCH_WIDTH for batch in scripted_batches):
        raise EmpiricalRunnerError("synthetic scripted consumer differs")
    return {
        "synthetic_test_only": True,
        "training_cells": len(TRAINING_CELLS),
        "training_episodes": int(counts["training_episodes"]),
        "forward_backward_completed": True,
        "fixed_norm_update_completed": True,
        "t24_event_transport_seam_completed": True,
        "learned_heldout_consumer_completed": True,
        "scripted_consumers_completed": len(scripted_batches),
        "scientific_output_exposed": False,
    }


def _require_measurement(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise EmpiricalRunnerError(f"{label} measurement is missing")
    result = dict(value)
    for key in ("wall_seconds", "cpu_seconds", "peak_rss_bytes", "io_read_bytes", "io_write_bytes"):
        measured = result.get(key)
        if isinstance(measured, bool) or not isinstance(measured, (int, float)) or measured < 0:
            raise EmpiricalRunnerError(f"{label} {key} measurement is missing")
    if result.get("telemetry_available") is not True or int(result["peak_rss_bytes"]) <= 0:
        raise EmpiricalRunnerError(f"{label} CPU/RSS/I/O telemetry is unavailable")
    return result


def result_blind_preactivity_summary(
    certificate: Mapping[str, object],
    accepted_binding: Mapping[str, object],
    *,
    temp_root: str | Path,
) -> dict[str, object]:
    """Run the complete fixed-synthetic construction preflight, result-blind."""

    cert = validate_preactivity_certificate(certificate)
    accepted = validate_accepted_binding(accepted_binding, cert)
    source = cert.get("source")
    if not isinstance(source, Mapping) or not isinstance(source.get("files"), Mapping):
        raise EmpiricalRunnerError("certificate source inventory is malformed")
    if set(source["files"]) != set(PRODUCTION_SOURCE_LOGICAL_PATHS):  # type: ignore[arg-type]
        raise EmpiricalRunnerError("preflight requires the exact production source set")
    _validate_live_source_set(cert)
    scratch = _preactivity_temp_root(temp_root)
    native_receipt = _result_blind_native_receipt(cert)

    from tools.benchmarks.benchmark_rcle_tbcfv_r04_native import _measure, run_benchmark

    benchmark = run_benchmark(repetitions=1, temp_root=scratch)
    if benchmark.get("efficiency_review") != "COMPLETE":
        raise EmpiricalRunnerError("accepted fixture benchmark did not complete")
    coverage = benchmark.get("chain_coverage")
    required_coverage = {
        "environment",
        "abi2_event_lifecycle",
        "loader",
        "batch",
        "forward_backward",
        "fixed_norm_update",
        "rollout",
        "learned_heldout_forward",
        "evaluation",
        "analyzer",
        "io",
        "resume",
        "telemetry_complete",
    }
    if not isinstance(coverage, Mapping) or any(coverage.get(key) is not True for key in required_coverage):
        raise EmpiricalRunnerError("fixture benchmark chain coverage is incomplete")
    equivalence = benchmark.get("semantic_equivalence")
    if not isinstance(equivalence, Mapping) or any(value is not True for value in equivalence.values()):
        raise EmpiricalRunnerError("fixture benchmark semantic equivalence is incomplete")
    compile_load = benchmark.get("compile_load")
    atomic = benchmark.get("atomic_write_resume")
    fixture_analyzer = benchmark.get("synthetic_72_tail_analyzer")
    if (
        not isinstance(compile_load, Mapping)
        or not isinstance(atomic, Mapping)
        or not isinstance(fixture_analyzer, Mapping)
    ):
        raise EmpiricalRunnerError("fixture benchmark measurement inventory is incomplete")
    if (
        fixture_analyzer.get("synthetic_tail_count") != 72
        or fixture_analyzer.get("completed") is not True
        or fixture_analyzer.get("schema_identity_verified") is not True
        or fixture_analyzer.get("construction_guards_verified") is not True
        or fixture_analyzer.get("interpretation_value_exposed") is not False
    ):
        raise EmpiricalRunnerError("synthetic 72-tail reducer preflight is incomplete")
    cold = _require_measurement(compile_load.get("process_cold"), "cold load")
    warm_initial = _require_measurement(compile_load.get("warm_loader_initial"), "warm initial load")
    warm_reuse = _require_measurement(compile_load.get("warm_loader_reuse"), "warm reuse load")
    atomic_write = _require_measurement(atomic.get("atomic_write"), "atomic publish")
    atomic_resume = _require_measurement(atomic.get("resume_scan_restore"), "atomic resume")
    if atomic.get("resume_exact") is not True:
        raise EmpiricalRunnerError("atomic frontier publish/resume seam is incomplete")

    def full_runner_chain() -> dict[str, object]:
        return {
            "runner": _synthetic_runner_chain(),
            "frontier": _synthetic_empirical_frontier_chain(scratch),
        }

    full_chain, full_measurement_raw = _measure(full_runner_chain)
    full_measurement = _require_measurement(full_measurement_raw, "runner full chain")
    runner_chain = full_chain["runner"]
    frontier_chain = full_chain["frontier"]
    if not isinstance(runner_chain, Mapping) or not isinstance(frontier_chain, Mapping):
        raise EmpiricalRunnerError("synthetic runner/frontier chain result is malformed")
    analyzer = _synthetic_analyzer_rejection()
    analyzer["synthetic_72_tail_reducer_completed"] = True
    if runner_chain.get("scientific_output_exposed") is not False:
        raise EmpiricalRunnerError("synthetic runner chain exposed scientific output")

    return {
        "schema": RUNNER_SCHEMA,
        "mode": "PREACTIVITY_PREFLIGHT",
        "technically_accepted": True,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "preactivity_certificate_sha256": cert["certificate_sha256"],
        "accepted_binding_sha256": accepted["binding_sha256"],
        "production_source_set_validated": True,
        "native_receipt": native_receipt,
        "runner_chain": runner_chain,
        "analyzer_admission": analyzer,
        "atomic_frontier": {
            **frontier_chain,
            "scientific_output_exposed": False,
        },
        "measurements": {
            "cold_load": cold,
            "warm_initial_load": warm_initial,
            "warm_reuse_load": warm_reuse,
            "runner_full_chain": full_measurement,
            "atomic_publish": atomic_write,
            "atomic_resume": atomic_resume,
        },
        "chain_flags": {key: True for key in sorted(required_coverage)},
        "result_blind": True,
        "identity_materialized": False,
        "coordinate_materialized": False,
        "native_loaded": True,
        "rng_accessed": "FIXED_SYNTHETIC_TEST_ONLY",
        "frontier_opened": "FIXED_SYNTHETIC_TEST_ONLY",
        "scientific_activity_started": False,
    }


class SemanticRNG:
    """Counter-based semantic product family for one already bound run block."""

    _FIELDS = (
        "run_block",
        "parameter_entry",
        "arm_only_variable",
        "cell",
        "update_or_scenario",
        "physical_tick",
        "roster_event",
        "physical_agent",
        "draw_kind",
        "draw_index",
    )

    def __init__(self, authority: ProductionAuthority, block_index: int, *, now: datetime):
        authority.require_active(now=now)
        self._authority = authority
        self.synthetic_test_only = False
        self.block_index = block_index
        self._key = bytes.fromhex(authority.block_root_digest(block_index))
        self._native_binding = bind_native_backend()
        frozen_native = authority.certificate.get("native")
        if not isinstance(frozen_native, Mapping) or (
            frozen_native.get("source_sha256") != self._native_binding.source_sha256
            or frozen_native.get("build_key") != self._native_binding.build_key
        ):
            raise EmpiricalRunnerError(
                "source-keyed semantic/reset native binding differs before run block"
            )

    def uniform(self, **address: object) -> float:
        if set(address) != set(self._FIELDS):
            raise EmpiricalRunnerError("semantic RNG address inventory differs")
        if address["run_block"] != self.block_index:
            raise EmpiricalRunnerError("semantic RNG address crosses run-block identity")
        payload = canonical_json_bytes(
            {
                "domain": "RCLE-TBCFV-R04/semantic-uniform/v1",
                **{field: address[field] for field in self._FIELDS},
            }
        )
        word = int.from_bytes(hmac.new(self._key, payload, hashlib.sha256).digest()[:8], "big")
        return (word + 0.5) / float(1 << 64)

    def uniform_many(self, addresses: Sequence[Mapping[str, object]]) -> tuple[float, ...]:
        """Evaluate a nonempty exact address batch through the C++ hot path."""

        rows = tuple(addresses)
        for address in rows:
            if set(address) != set(self._FIELDS):
                raise EmpiricalRunnerError("semantic RNG address inventory differs")
            if address["run_block"] != self.block_index:
                raise EmpiricalRunnerError("semantic RNG address crosses run-block identity")
        words = native_semantic_uniform_words(
            self._key, rows, binding=self._native_binding
        )
        return tuple((word + 0.5) / float(1 << 64) for word in words)

    def claim_many(
        self,
        addresses: Sequence[Mapping[str, object]],
        probabilities: torch.Tensor,
    ) -> tuple[int, ...]:
        """Evaluate exact address words and sequential six-way choices natively."""

        rows = tuple(addresses)
        for address in rows:
            if set(address) != set(self._FIELDS):
                raise EmpiricalRunnerError("semantic RNG address inventory differs")
            if address["run_block"] != self.block_index:
                raise EmpiricalRunnerError("semantic RNG address crosses run-block identity")
        values = probabilities.detach().to(device="cpu", dtype=torch.float64).contiguous()
        return native_semantic_claims(
            self._key, rows, values.numpy(), binding=self._native_binding
        )

    def claim_compact(
        self,
        coordinates: Sequence["EpisodeCoordinate"],
        snapshots: Sequence[Snapshot],
        probabilities: torch.Tensor,
    ) -> tuple[int, ...]:
        """Use the frozen actor-claim address inventory without Python mappings."""

        if len(coordinates) != len(snapshots):
            raise EmpiricalRunnerError("compact claim lane inventory differs")
        cell_codes: list[int] = []
        updates: list[int] = []
        roster_events: list[int] = []
        physical_agents: list[int] = []
        ticks: list[int] = []
        for coordinate, snapshot in zip(coordinates, snapshots):
            keys = tuple(int(key) for key in snapshot.transport_keys)
            count = len(keys)
            cell_codes.extend([_CELL_CODES[coordinate.cell]] * count)
            updates.extend([coordinate.update_or_scenario] * count)
            roster_events.extend([coordinate.episode_row] * count)
            physical_agents.extend(keys)
            ticks.extend([snapshot.tick] * count)
        values = probabilities.detach().to(device="cpu", dtype=torch.float64).contiguous()
        return native_semantic_claims_compact(
            self._key,
            self.block_index,
            np.asarray(cell_codes, dtype=np.int32),
            np.asarray(updates, dtype=np.int64),
            np.asarray(roster_events, dtype=np.int64),
            np.asarray(physical_agents, dtype=np.int64),
            np.asarray(ticks, dtype=np.int64),
            values.numpy(),
            binding=self._native_binding,
        )

    def require_runtime_authority(self) -> None:
        if self.synthetic_test_only:
            return
        assert self._authority is not None
        self._authority.require_active(now=datetime.now(timezone.utc))

    def ordered_sample(self, population: Sequence[int], count: int, **base: object) -> tuple[int, ...]:
        values = tuple(population)
        if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= len(values):
            raise EmpiricalRunnerError("sample count is outside the finite population")
        ranked = sorted(
            values,
            key=lambda item: (
                self.uniform(**base, draw_index=int(item)),
                int(item),
            ),
        )
        return tuple(ranked[:count])

    def normal(self, **address: object) -> float:
        uniform = self.uniform(**address)
        # Python's standard library has no inverse Normal.  erfinv is evaluated
        # by Torch in the model path; this scalar helper is limited to material
        # that never carries gradients.
        import torch

        value = torch.tensor(2.0 * uniform - 1.0, dtype=torch.float64)
        return float((math.sqrt(2.0) * torch.erfinv(value)).item())


class SyntheticTestRNG(SemanticRNG):
    """Fixed unmistakable TEST-only counter source; never a production coordinate."""

    def __init__(self, label: str = "SYNTHETIC-TEST-RCLE-TBCFV-RUNNER-A") -> None:
        if label not in (
            "SYNTHETIC-TEST-RCLE-TBCFV-RUNNER-A",
            "SYNTHETIC-TEST-RCLE-TBCFV-RUNNER-B",
        ):
            raise EmpiricalRunnerError("unknown synthetic runner fixture identity")
        self._authority = None
        self.synthetic_test_only = True
        self.block_index = 0
        self._key = hashlib.sha256(label.encode("ascii")).digest()
        self._native_binding = bind_native_backend()


def _require_semantic_rng(rng: object) -> SemanticRNG:
    if type(rng) not in (SemanticRNG, SyntheticTestRNG):
        raise EmpiricalRunnerError("validated production or fixed synthetic TEST RNG is required")
    return rng


def _address(
    block: int,
    *,
    parameter_entry: object = "",
    arm_only_variable: object = "",
    cell: object = "",
    update_or_scenario: object = 0,
    physical_tick: object = 0,
    roster_event: object = "",
    physical_agent: object = "",
    draw_kind: object,
    draw_index: object,
) -> dict[str, object]:
    return {
        "run_block": block,
        "parameter_entry": parameter_entry,
        "arm_only_variable": arm_only_variable,
        "cell": cell,
        "update_or_scenario": update_or_scenario,
        "physical_tick": physical_tick,
        "roster_event": roster_event,
        "physical_agent": physical_agent,
        "draw_kind": draw_kind,
        "draw_index": draw_index,
    }


def _parse_cell(cell: str) -> tuple[int, int, str]:
    try:
        path, event = cell.split(".", 1)
        left, right = path.split("_to_", 1)
        before, after = int(left), int(right)
    except (TypeError, ValueError) as exc:
        raise EmpiricalRunnerError(f"cell name is malformed: {cell!r}") from exc
    if cell not in TRAINING_CELLS and cell not in HELDOUT_CELLS:
        raise EmpiricalRunnerError(f"cell is outside the frozen inventory: {cell}")
    if event not in ("ACTIVE_CONTINUATION", "NEW_EPOCH"):
        raise EmpiricalRunnerError("cell event condition differs")
    return before, after, event


@dataclass(frozen=True)
class EpisodeCoordinate:
    block_index: int
    cell: str
    update_or_scenario: int
    episode_row: int

    @property
    def token(self) -> str:
        return f"{self.cell}|{self.update_or_scenario}|{self.episode_row}"


def materialize_fixture(rng: SemanticRNG, coordinate: EpisodeCoordinate) -> FixtureSpec:
    """Materialize only reset-time variables; newcomer sectors remain event-time."""

    _require_semantic_rng(rng)
    before, after, event = _parse_cell(coordinate.cell)
    base = dict(cell=coordinate.cell, update_or_scenario=coordinate.update_or_scenario)
    position_uniforms = rng.uniform_many(
        tuple(
            _address(
                coordinate.block_index,
                **base,
                physical_agent=coordinate.episode_row,
                draw_kind="initial-position-permutation",
                draw_index=sector,
            )
            for sector in range(120)
        )
    )
    ranked_positions = sorted(
        range(120), key=lambda sector: (position_uniforms[sector], sector)
    )
    positions = tuple(ranked_positions[:before])
    initial_keys = tuple(range(before))
    if after < before:
        survivor_uniforms = rng.uniform_many(
            tuple(
                _address(
                    coordinate.block_index,
                    **base,
                    physical_agent=coordinate.episode_row,
                    roster_event="contraction",
                    draw_kind="survivor-subset",
                    draw_index=key,
                )
                for key in initial_keys
            )
        )
        ranked_keys = sorted(
            initial_keys, key=lambda key: (survivor_uniforms[key], key)
        )
        after_keys = tuple(sorted(ranked_keys[:after]))
    elif after > before:
        after_keys = initial_keys + tuple(range(before, after))
    else:
        after_keys = initial_keys
    after_positions = tuple(-1 if key in initial_keys else EVENT_POSITION for key in after_keys)
    if event == "NEW_EPOCH":
        omega_u, kappa_u = rng.uniform_many(
            (
                _address(
                    coordinate.block_index,
                    **base,
                    physical_agent=coordinate.episode_row,
                    roster_event="new_epoch",
                    draw_kind="omega-plus",
                    draw_index=0,
                ),
                _address(
                    coordinate.block_index,
                    **base,
                    physical_agent=coordinate.episode_row,
                    roster_event="new_epoch",
                    draw_kind="kappa-plus",
                    draw_index=0,
                ),
            )
        )
        omega_plus = (5, 10, 15)[min(int(omega_u * 3), 2)]
        kappa_plus = min(int(kappa_u * 5), 4) + 1
        condition = HOST_NEW_EPOCH
    else:
        omega_plus = 0
        kappa_plus = 0
        condition = HOST_ACTIVE_CONTINUATION
    return FixtureSpec(
        initial_keys=initial_keys,
        initial_positions=positions,
        after_keys=after_keys,
        after_positions=after_positions,
        event_condition=condition,
        omega_plus=omega_plus,
        kappa_plus=kappa_plus,
    )


def materialize_event_input(
    rng: SemanticRNG, coordinate: EpisodeCoordinate, snapshot: Snapshot, fixture: FixtureSpec
) -> EventInput:
    _require_semantic_rng(rng)
    if not snapshot.event_input_required or snapshot.tick != 24:
        raise EmpiricalRunnerError("event positions require the native pre-event tick-24 snapshot")
    newcomers = tuple(key for key in fixture.after_keys if key not in fixture.initial_keys)
    surviving_keys = set(fixture.after_keys) & set(fixture.initial_keys)
    occupied_after_departure = {
        position
        for key, position in zip(snapshot.transport_keys, snapshot.positions)
        if key in surviving_keys
    }
    available = tuple(
        sector for sector in range(120) if sector not in occupied_after_departure
    )
    event_uniforms = rng.uniform_many(
        tuple(
            _address(
                coordinate.block_index,
                cell=coordinate.cell,
                update_or_scenario=coordinate.update_or_scenario,
                physical_tick=24,
                roster_event="newcomer-entry",
                physical_agent=coordinate.episode_row,
                draw_kind="newcomer-position-permutation",
                draw_index=sector,
            )
            for sector in available
        )
    )
    ranked = tuple(
        sector
        for _, sector in sorted(
            zip(event_uniforms, available), key=lambda item: (item[0], item[1])
        )
    )
    return EventInput(tuple(ranked[: len(newcomers)]))


def _compact_coordinate_columns(
    coordinates: Sequence[EpisodeCoordinate],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = tuple(coordinates)
    return (
        np.asarray([_CELL_CODES[item.cell] for item in rows], dtype=np.int32),
        np.asarray([item.update_or_scenario for item in rows], dtype=np.int64),
        np.asarray([item.episode_row for item in rows], dtype=np.int64),
    )


def materialize_fixture_batch(
    rng: SemanticRNG, coordinates: Sequence[EpisodeCoordinate]
) -> tuple[FixtureSpec, ...]:
    """Production compiled reset materializer; scalar Python remains TEST oracle."""

    semantic = _require_semantic_rng(rng)
    rows = tuple(coordinates)
    cells, updates, episode_rows = _compact_coordinate_columns(rows)
    return native_materialize_fixtures_compact(
        semantic._key,
        semantic.block_index,
        cells,
        updates,
        episode_rows,
        binding=semantic._native_binding,
    )


def materialize_event_batch(
    rng: SemanticRNG,
    coordinates: Sequence[EpisodeCoordinate],
    batch: Any,
    fixtures: Sequence[FixtureSpec],
) -> tuple[EventInput, ...]:
    """Production compiled t=24 materializer against the native snapshot batch."""

    semantic = _require_semantic_rng(rng)
    rows = tuple(coordinates)
    cells, updates, episode_rows = _compact_coordinate_columns(rows)
    return batch.materialize_events_compact(
        semantic._key,
        semantic.block_index,
        cells,
        updates,
        episode_rows,
        fixtures,
    )


def _public_tensors(snapshot: Snapshot) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Build actor tensors exclusively from PublicObservation, never transport keys."""

    public = snapshot.public_observation()
    n = len(public.positions)
    tau = 2.0 * math.pi
    agents = torch.tensor(
        [
            [math.sin(tau * position / 120.0), math.cos(tau * position / 120.0), float(newcomer)]
            for position, newcomer in zip(public.positions, public.newcomers)
        ],
        dtype=torch.float64,
    )
    beacons = torch.tensor(
        [
            [math.sin(tau * position / 120.0), math.cos(tau * position / 120.0), demand / 2.0]
            for position, demand in zip(public.beacon_positions, public.demands)
        ],
        dtype=torch.float64,
    )
    context = torch.tensor(
        [n / 12.0, public.tick / 64.0, float(public.roster_event), float(public.new_epoch)],
        dtype=torch.float64,
    )
    own = torch.tensor(
        [
            [
                math.sin(tau * position / 120.0),
                math.cos(tau * position / 120.0),
                rank / max(n - 1, 1),
                displacement / 3.0,
                float(newcomer),
            ]
            for position, rank, displacement, newcomer in zip(
                public.positions,
                public.angular_ranks,
                public.previous_displacements,
                public.newcomers,
            )
        ],
        dtype=torch.float64,
    )
    candidates: list[list[list[float]]] = []
    for position in public.positions:
        rows: list[list[float]] = []
        for beacon, demand in zip(public.beacon_positions, public.demands):
            clockwise = (beacon - position) % 120
            signed = clockwise if clockwise <= 60 else clockwise - 120
            rows.append(
                [
                    math.sin(tau * beacon / 120.0),
                    math.cos(tau * beacon / 120.0),
                    demand / 2.0,
                    signed / 60.0,
                ]
            )
        candidates.append(rows)
    return agents, beacons, context, own, torch.tensor(candidates, dtype=torch.float64)


@dataclass(frozen=True)
class _BatchedPublicTensors:
    agents: torch.Tensor
    agent_mask: torch.Tensor
    beacons: torch.Tensor
    contexts: torch.Tensor
    own: torch.Tensor
    candidates: torch.Tensor
    counts: tuple[int, ...]


def _batched_public_tensors(snapshots: Sequence[Snapshot]) -> _BatchedPublicTensors:
    """Pack one native batch for a single masked model forward.

    Physical transport keys never enter these tensors.  The lane-major active
    mask preserves the exact per-lane/public ordering used by the scalar
    reference path while avoiding eight repeated model calls per claim tick.
    """

    rows = tuple(snapshots)
    if not rows:
        raise EmpiricalRunnerError("batched public tensors require at least one lane")
    public_rows = tuple(snapshot.public_observation() for snapshot in rows)
    counts = tuple(len(public.positions) for public in public_rows)
    if any(count < 1 or count > 12 for count in counts):
        raise EmpiricalRunnerError("public roster width is outside 1..12")
    width = len(rows)

    def padded(values: Sequence[object], count: int, fill: int = 0) -> list[object]:
        return [*values, *([fill] * (12 - count))]

    positions = torch.tensor(
        [padded(public.positions, count) for public, count in zip(public_rows, counts)],
        dtype=torch.int64,
    )
    newcomers = torch.tensor(
        [padded(public.newcomers, count) for public, count in zip(public_rows, counts)],
        dtype=torch.float64,
    )
    angular_ranks = torch.tensor(
        [padded(public.angular_ranks, count) for public, count in zip(public_rows, counts)],
        dtype=torch.float64,
    )
    displacements = torch.tensor(
        [
            padded(public.previous_displacements, count)
            for public, count in zip(public_rows, counts)
        ],
        dtype=torch.float64,
    )
    beacon_positions = torch.tensor(
        [public.beacon_positions for public in public_rows], dtype=torch.int64
    )
    demands = torch.tensor([public.demands for public in public_rows], dtype=torch.float64)
    count_tensor = torch.tensor(counts, dtype=torch.int64)
    agent_mask = torch.arange(12, dtype=torch.int64).view(1, 12) < count_tensor.view(width, 1)
    active = agent_mask.to(torch.float64).unsqueeze(-1)

    agent_positions = _POSITION_FEATURES[positions]
    agents = torch.cat((agent_positions, newcomers.unsqueeze(-1)), dim=-1) * active
    beacons = torch.cat(
        (_POSITION_FEATURES[beacon_positions], (demands / 2.0).unsqueeze(-1)), dim=-1
    )
    contexts = torch.tensor(
        [
            [
                count / 12.0,
                public.tick / 64.0,
                float(public.roster_event),
                float(public.new_epoch),
            ]
            for public, count in zip(public_rows, counts)
        ],
        dtype=torch.float64,
    )
    denominators = torch.clamp(count_tensor - 1, min=1).to(torch.float64).view(width, 1)
    own = torch.cat(
        (
            agent_positions,
            (angular_ranks / denominators).unsqueeze(-1),
            (displacements / 3.0).unsqueeze(-1),
            newcomers.unsqueeze(-1),
        ),
        dim=-1,
    ) * active
    candidate_positions = _POSITION_FEATURES[beacon_positions].view(width, 1, 6, 2).expand(
        width, 12, 6, 2
    )
    candidate_demands = (demands / 2.0).view(width, 1, 6, 1).expand(width, 12, 6, 1)
    signed = (beacon_positions.view(width, 1, 6) - positions.view(width, 12, 1)) % 120
    signed = torch.where(signed <= 60, signed, signed - 120).to(torch.float64) / 60.0
    candidates = torch.cat(
        (candidate_positions, candidate_demands, signed.unsqueeze(-1)), dim=-1
    ) * agent_mask.view(width, 12, 1, 1).to(torch.float64)
    return _BatchedPublicTensors(
        agents=agents,
        agent_mask=agent_mask,
        beacons=beacons,
        contexts=contexts,
        own=own,
        candidates=candidates,
        counts=counts,
    )


def _batched_manager(
    model: TBCFVModel, packed: _BatchedPublicTensors
) -> ManagerOutput:
    return model.manager(
        packed.agents,
        packed.beacons,
        packed.contexts,
        agent_mask=packed.agent_mask,
    )


def _manager_lane(manager: ManagerOutput, lane: int) -> ManagerOutput:
    return ManagerOutput(
        mean=manager.mean[lane],
        raw_log_scale=manager.raw_log_scale[lane],
        log_scale=manager.log_scale[lane],
        scale=manager.scale[lane],
        pooled_summary=manager.pooled_summary[lane],
        public_summary=manager.public_summary[lane],
    )


def _uniform_tensor(
    rng: SemanticRNG,
    coordinate: EpisodeCoordinate,
    *,
    draw_kind: str,
    physical_keys: Sequence[int | str],
    arm_only_variable: str = "",
    physical_tick: int = 0,
) -> torch.Tensor:
    addresses = tuple(
        _address(
                    coordinate.block_index,
                    arm_only_variable=arm_only_variable,
                    cell=coordinate.cell,
                    update_or_scenario=coordinate.update_or_scenario,
                    physical_tick=physical_tick,
                    roster_event=coordinate.episode_row,
                    physical_agent=key,
                    draw_kind=draw_kind,
                    draw_index=index,
                )
        for key in physical_keys
        for index in range(4)
    )
    values = rng.uniform_many(addresses)
    return torch.tensor(values, dtype=torch.float64).reshape(len(physical_keys), 4)


@dataclass
class _LanePlans:
    state: PlanState
    current: dict[int, torch.Tensor]
    initial_manager: Any
    plan_scores: list[torch.Tensor]
    claim_scores: list[torch.Tensor]


def _sample_manager_plans(
    rng: SemanticRNG,
    coordinate: EpisodeCoordinate,
    manager: Any,
    keys: Sequence[int],
    *,
    draw_kind: str,
) -> tuple[dict[int, torch.Tensor], list[torch.Tensor]]:
    uniforms = _uniform_tensor(rng, coordinate, draw_kind=draw_kind, physical_keys=keys)
    mean = manager.mean.expand(len(keys), -1) if manager.mean.ndim == 1 else manager.mean
    raw = manager.raw_log_scale.expand(len(keys), -1) if manager.raw_log_scale.ndim == 1 else manager.raw_log_scale
    samples = stopped_normal_inverse_cdf(uniforms, mean, raw)
    scores = stopped_normal_log_density(samples, mean, raw)
    return {key: samples[index] for index, key in enumerate(keys)}, list(scores.unbind())


def _initial_lane_plans(
    model: TBCFVModel,
    arm: str,
    rng: SemanticRNG,
    coordinate: EpisodeCoordinate,
    snapshot: Snapshot,
) -> _LanePlans:
    agents, beacons, context, _, _ = _public_tensors(snapshot)
    manager = model.manager(agents, beacons, context)
    keys = tuple(int(key) for key in snapshot.transport_keys)
    common_arm = arm in LEARNED_PACKAGES[:3]
    draw_keys: tuple[int | str, ...] = ("COMMON",) if common_arm else keys
    plans, scores = _sample_manager_plans(
        rng, coordinate, manager, draw_keys, draw_kind="epoch-plan"
    )
    if common_arm:
        common = plans["COMMON"]
        draws = FixtureDrawBank(epoch_common=common)
    else:
        draws = FixtureDrawBank(epoch_private={key: plans[key] for key in keys})
    transition = initialize_plans(arm, keys, draws)
    current = {key: transition.plans[index] for index, key in enumerate(keys)}
    return _LanePlans(transition.state, current, manager, scores, [])


def _initial_batch_plans(
    model: TBCFVModel,
    arm: str,
    rng: SemanticRNG,
    coordinates: Sequence[EpisodeCoordinate],
    snapshots: Sequence[Snapshot],
) -> list[_LanePlans]:
    packed = _batched_public_tensors(snapshots)
    manager = _batched_manager(model, packed)
    result: list[_LanePlans] = []
    for lane, (coordinate, snapshot) in enumerate(zip(coordinates, snapshots)):
        lane_manager = _manager_lane(manager, lane)
        keys = tuple(int(key) for key in snapshot.transport_keys)
        common_arm = arm in LEARNED_PACKAGES[:3]
        draw_keys: tuple[int | str, ...] = ("COMMON",) if common_arm else keys
        plans, scores = _sample_manager_plans(
            rng,
            coordinate,
            lane_manager,
            draw_keys,
            draw_kind="epoch-plan",
        )
        if common_arm:
            draws = FixtureDrawBank(epoch_common=plans["COMMON"])
        else:
            draws = FixtureDrawBank(epoch_private={key: plans[key] for key in keys})
        transition = initialize_plans(arm, keys, draws)
        current = {key: transition.plans[index] for index, key in enumerate(keys)}
        result.append(_LanePlans(transition.state, current, lane_manager, scores, []))
    return result


def _draw_claims(
    model: TBCFVModel,
    arm: str,
    rng: SemanticRNG,
    coordinate: EpisodeCoordinate,
    snapshot: Snapshot,
    plans: _LanePlans,
) -> StepInput:
    agents, beacons, context, own, candidates = _public_tensors(snapshot)
    manager = model.manager(agents, beacons, context)
    keys = tuple(int(key) for key in snapshot.transport_keys)
    aligned = torch.stack([plans.current[key] for key in keys])
    pointer = make_pointer_inputs(
        manager.pooled_summary,
        own,
        context,
        candidates,
        # Every manager sample was already stopped at inverse-CDF/package
        # materialization.  Do not detach here: FLEX's deterministic event
        # deltas must retain their downstream actor-gradient path.
        aligned,
    )
    probabilities = model.claim_probabilities(pointer)
    claims: list[int] = []
    for row, key in enumerate(keys):
        u = rng.uniform(
            **_address(
                coordinate.block_index,
                cell=coordinate.cell,
                update_or_scenario=coordinate.update_or_scenario,
                physical_tick=snapshot.tick,
                roster_event=coordinate.episode_row,
                physical_agent=key,
                draw_kind="actor-claim",
                draw_index=0,
            )
        )
        cumulative = 0.0
        selected = 5
        for candidate, probability in enumerate(probabilities[row]):
            cumulative += float(probability.detach().item())
            if u < cumulative:
                selected = candidate
                break
        claims.append(selected)
    claim_tensor = torch.tensor(claims, dtype=torch.int64)
    plans.claim_scores.extend(selected_claim_log_probability(probabilities, claim_tensor).unbind())
    return StepInput(tuple(claims))


def _draw_claims_batch(
    model: TBCFVModel,
    arm: str,
    rng: SemanticRNG,
    coordinates: Sequence[EpisodeCoordinate],
    snapshots: Sequence[Snapshot],
    plans_by_lane: Sequence[_LanePlans],
) -> list[StepInput]:
    packed = _batched_public_tensors(snapshots)
    manager = _batched_manager(model, packed)
    pooled_rows: list[torch.Tensor] = []
    context_rows: list[torch.Tensor] = []
    own_rows: list[torch.Tensor] = []
    candidate_rows: list[torch.Tensor] = []
    plan_rows: list[torch.Tensor] = []
    for lane, (snapshot, plans) in enumerate(zip(snapshots, plans_by_lane)):
        count = packed.counts[lane]
        keys = tuple(int(key) for key in snapshot.transport_keys)
        if len(keys) != count:
            raise EmpiricalRunnerError("batched public/transport roster counts differ")
        pooled_rows.append(manager.pooled_summary[lane].expand(count, -1))
        context_rows.append(packed.contexts[lane].expand(count, -1))
        own_rows.append(packed.own[lane, :count])
        candidate_rows.append(packed.candidates[lane, :count])
        plan_rows.append(torch.stack([plans.current[key] for key in keys]))
    pointer = make_pointer_inputs(
        torch.cat(pooled_rows, dim=0),
        torch.cat(own_rows, dim=0),
        torch.cat(context_rows, dim=0),
        torch.cat(candidate_rows, dim=0),
        torch.cat(plan_rows, dim=0),
    )
    probabilities = model.claim_probabilities(pointer)
    selected_claims = rng.claim_compact(coordinates, snapshots, probabilities)
    actions: list[StepInput] = []
    offset = 0
    for coordinate, snapshot, plans, count in zip(
        coordinates, snapshots, plans_by_lane, packed.counts
    ):
        keys = tuple(int(key) for key in snapshot.transport_keys)
        lane_probabilities = probabilities[offset : offset + count]
        claims = list(selected_claims[offset : offset + count])
        offset += count
        claim_tensor = torch.tensor(claims, dtype=torch.int64)
        plans.claim_scores.extend(
            selected_claim_log_probability(lane_probabilities, claim_tensor).unbind()
        )
        actions.append(StepInput(tuple(claims)))
    if offset != probabilities.shape[0]:
        raise EmpiricalRunnerError("batched claim output inventory differs")
    return actions


def _apply_plan_event(
    model: TBCFVModel,
    arm: str,
    rng: SemanticRNG,
    coordinate: EpisodeCoordinate,
    snapshot: Snapshot,
    plans: _LanePlans,
) -> None:
    agents, beacons, context, own, _ = _public_tensors(snapshot)
    manager = model.manager(agents, beacons, context)
    keys = tuple(int(key) for key in snapshot.transport_keys)
    _, _, event = _parse_cell(coordinate.cell)
    new_epoch = event == "NEW_EPOCH"
    draw_values: dict[str, object] = {}

    def sampled(source: Any, selected_keys: Sequence[int | str], kind: str) -> dict[int | str, torch.Tensor]:
        values, scores = _sample_manager_plans(
            rng, coordinate, source, selected_keys, draw_kind=kind
        )
        plans.plan_scores.extend(scores)
        return values

    if new_epoch:
        if arm in LEARNED_PACKAGES[:3]:
            values = sampled(manager, ("COMMON",), "new-epoch-common-plan")
            draw_values["new_epoch_common"] = values["COMMON"]
        else:
            values = sampled(manager, keys, "new-epoch-private-plan")
            draw_values["new_epoch_private"] = {key: values[key] for key in keys}
    elif arm == LEARNED_PACKAGES[2]:  # C1P0
        values = sampled(plans.initial_manager, ("COMMON",), "active-common-refresh")
        draw_values["active_common_refresh"] = values["COMMON"]
    elif arm == LEARNED_PACKAGES[4]:  # C0P0
        values = sampled(plans.initial_manager, keys, "active-private-refresh")
        draw_values["active_private_refresh"] = {key: values[key] for key in keys}
    elif arm == LEARNED_PACKAGES[3]:  # C0P1
        old = set(plans.current)
        newcomers = tuple(key for key in keys if key not in old)
        if newcomers:
            values = sampled(plans.initial_manager, newcomers, "active-newcomer-private")
            draw_values["newcomer_private"] = {key: values[key] for key in newcomers}

    if arm == LEARNED_PACKAGES[1]:  # FLEX
        noise = _uniform_tensor(
            rng,
            coordinate,
            draw_kind="flex-event-noise",
            physical_keys=keys,
            arm_only_variable=arm,
            physical_tick=24,
        )
        # Frozen event noise is standard Normal, not raw Uniform.
        noise = math.sqrt(2.0) * torch.erfinv(2.0 * noise - 1.0)
        draw_values["flex_event_noise"] = {
            key: noise[index] for index, key in enumerate(keys)
        }
    transition = transition_plans(
        plans.state,
        keys,
        "NEW_EPOCH" if new_epoch else "ACTIVE_CONTINUATION",
        FixtureDrawBank(**draw_values),
        model=model if arm == LEARNED_PACKAGES[1] else None,
        public_event_summary=manager.public_summary if arm == LEARNED_PACKAGES[1] else None,
        physical_features=own if arm == LEARNED_PACKAGES[1] else None,
    )
    plans.state = transition.state
    plans.current = {key: transition.plans[index] for index, key in enumerate(keys)}


def _apply_plan_event_batch(
    model: TBCFVModel,
    arm: str,
    rng: SemanticRNG,
    coordinates: Sequence[EpisodeCoordinate],
    snapshots: Sequence[Snapshot],
    plans_by_lane: Sequence[_LanePlans],
) -> None:
    packed = _batched_public_tensors(snapshots)
    manager = _batched_manager(model, packed)
    for lane, (coordinate, snapshot, plans) in enumerate(
        zip(coordinates, snapshots, plans_by_lane)
    ):
        lane_manager = _manager_lane(manager, lane)
        keys = tuple(int(key) for key in snapshot.transport_keys)
        own = packed.own[lane, : packed.counts[lane]]
        _, _, event = _parse_cell(coordinate.cell)
        new_epoch = event == "NEW_EPOCH"
        draw_values: dict[str, object] = {}

        def sampled(
            source: Any, selected_keys: Sequence[int | str], kind: str
        ) -> dict[int | str, torch.Tensor]:
            values, scores = _sample_manager_plans(
                rng, coordinate, source, selected_keys, draw_kind=kind
            )
            plans.plan_scores.extend(scores)
            return values

        if new_epoch:
            if arm in LEARNED_PACKAGES[:3]:
                values = sampled(lane_manager, ("COMMON",), "new-epoch-common-plan")
                draw_values["new_epoch_common"] = values["COMMON"]
            else:
                values = sampled(lane_manager, keys, "new-epoch-private-plan")
                draw_values["new_epoch_private"] = {key: values[key] for key in keys}
        elif arm == LEARNED_PACKAGES[2]:
            values = sampled(plans.initial_manager, ("COMMON",), "active-common-refresh")
            draw_values["active_common_refresh"] = values["COMMON"]
        elif arm == LEARNED_PACKAGES[4]:
            values = sampled(plans.initial_manager, keys, "active-private-refresh")
            draw_values["active_private_refresh"] = {key: values[key] for key in keys}
        elif arm == LEARNED_PACKAGES[3]:
            old = set(plans.current)
            newcomers = tuple(key for key in keys if key not in old)
            if newcomers:
                values = sampled(
                    plans.initial_manager, newcomers, "active-newcomer-private"
                )
                draw_values["newcomer_private"] = {
                    key: values[key] for key in newcomers
                }
        if arm == LEARNED_PACKAGES[1]:
            noise = _uniform_tensor(
                rng,
                coordinate,
                draw_kind="flex-event-noise",
                physical_keys=keys,
                arm_only_variable=arm,
                physical_tick=24,
            )
            noise = math.sqrt(2.0) * torch.erfinv(2.0 * noise - 1.0)
            draw_values["flex_event_noise"] = {
                key: noise[index] for index, key in enumerate(keys)
            }
        transition = transition_plans(
            plans.state,
            keys,
            "NEW_EPOCH" if new_epoch else "ACTIVE_CONTINUATION",
            FixtureDrawBank(**draw_values),
            model=model if arm == LEARNED_PACKAGES[1] else None,
            public_event_summary=(
                lane_manager.public_summary if arm == LEARNED_PACKAGES[1] else None
            ),
            physical_features=own if arm == LEARNED_PACKAGES[1] else None,
        )
        plans.state = transition.state
        plans.current = {
            key: transition.plans[index] for index, key in enumerate(keys)
        }


@dataclass(frozen=True)
class LearnedEpisodeResult:
    tau: float
    U: float
    F: float
    Y: float
    plan_scores: tuple[torch.Tensor, ...]
    claim_scores: tuple[torch.Tensor, ...]
    agent_ticks: int
    claim_decisions: int


def _execute_learned_batch_scalar_reference(
    model: TBCFVModel,
    arm: str,
    rng: SemanticRNG,
    coordinates: Sequence[EpisodeCoordinate],
    *,
    training: bool,
) -> tuple[LearnedEpisodeResult, ...]:
    """TEST-only scalar-model reference for the production B8 consumer."""

    coords = tuple(coordinates)
    _require_semantic_rng(rng).require_runtime_authority()
    if len(coords) != SELECTED_BATCH_WIDTH or len({item.cell for item in coords}) != 1:
        raise EmpiricalRunnerError("learned host calls require exactly one B8 cell batch")
    fixtures = tuple(materialize_fixture(rng, item) for item in coords)
    batch = reset_native_batch(fixtures, binding=rng._native_binding)
    lane_plans = [
        _initial_lane_plans(model, arm, rng, coordinate, snapshot)
        for coordinate, snapshot in zip(coords, batch.snapshots)
    ]
    agent_ticks = [0] * SELECTED_BATCH_WIDTH
    claim_decisions = [0] * SELECTED_BATCH_WIDTH
    try:
        while not all(snapshot.terminal for snapshot in batch.snapshots):
            snapshots = batch.snapshots
            if any(snapshot.event_input_required for snapshot in snapshots):
                if not all(snapshot.event_input_required for snapshot in snapshots):
                    raise EmpiricalRunnerError("native event lifecycle diverged across B8 lanes")
                events = tuple(
                    materialize_event_input(rng, coordinate, snapshot, fixture)
                    for coordinate, snapshot, fixture in zip(coords, snapshots, fixtures)
                )
                snapshots = batch.apply_event(events)
                for coordinate, snapshot, plans in zip(coords, snapshots, lane_plans):
                    _apply_plan_event(model, arm, rng, coordinate, snapshot, plans)
            actions: list[StepInput] = []
            for lane, (coordinate, snapshot, plans) in enumerate(
                zip(coords, snapshots, lane_plans)
            ):
                if snapshot.terminal:
                    raise EmpiricalRunnerError("one native lane terminated before its B8 peers")
                agent_ticks[lane] += len(snapshot.positions)
                if snapshot.claim_required:
                    action = _draw_claims(model, arm, rng, coordinate, snapshot, plans)
                    claim_decisions[lane] += len(action.claims)
                    actions.append(action)
                else:
                    actions.append(StepInput.no_claims())
            batch.step(tuple(actions))
        results: list[LearnedEpisodeResult] = []
        for lane, (snapshot, plans) in enumerate(zip(batch.snapshots, lane_plans)):
            if any(value is None for value in (snapshot.tau, snapshot.U, snapshot.F, snapshot.Y)):
                raise EmpiricalRunnerError("terminal native endpoint is incomplete")
            results.append(
                LearnedEpisodeResult(
                    tau=float(snapshot.tau),
                    U=float(snapshot.U),
                    F=float(snapshot.F),
                    Y=float(snapshot.Y),
                    plan_scores=tuple(plans.plan_scores) if training else (),
                    claim_scores=tuple(plans.claim_scores) if training else (),
                    agent_ticks=agent_ticks[lane],
                    claim_decisions=claim_decisions[lane],
                )
            )
        return tuple(results)
    finally:
        if not batch.closed:
            batch.close()


def execute_learned_batch(
    model: TBCFVModel,
    arm: str,
    rng: SemanticRNG,
    coordinates: Sequence[EpisodeCoordinate],
    *,
    training: bool,
) -> tuple[LearnedEpisodeResult, ...]:
    """Execute one exact native B8 cell batch with masked batched model calls."""

    coords = tuple(coordinates)
    _require_semantic_rng(rng).require_runtime_authority()
    width = len(coords)
    if width not in SUPPORTED_BATCH_WIDTHS:
        raise EmpiricalRunnerError("learned host width is not supported by the RCLE native ABI")
    fixtures = materialize_fixture_batch(rng, coords)
    batch = reset_native_batch(
        fixtures, packed_views=True, binding=rng._native_binding
    )
    lane_plans = _initial_batch_plans(model, arm, rng, coords, batch.snapshots)
    agent_ticks = [0] * width
    claim_decisions = [0] * width
    try:
        while not all(snapshot.terminal for snapshot in batch.snapshots):
            snapshots = batch.snapshots
            if any(snapshot.event_input_required for snapshot in snapshots):
                if not all(snapshot.event_input_required for snapshot in snapshots):
                    raise EmpiricalRunnerError("native event lifecycle diverged across B8 lanes")
                events = materialize_event_batch(rng, coords, batch, fixtures)
                snapshots = batch.apply_event(events)
                _apply_plan_event_batch(model, arm, rng, coords, snapshots, lane_plans)
            for lane, snapshot in enumerate(snapshots):
                if snapshot.terminal:
                    raise EmpiricalRunnerError("one native lane terminated before its B8 peers")
                agent_ticks[lane] += len(snapshot.positions)
            claim_lanes = [snapshot.claim_required for snapshot in snapshots]
            if any(claim_lanes):
                if not all(claim_lanes):
                    raise EmpiricalRunnerError("native claim lifecycle diverged across B8 lanes")
                actions = _draw_claims_batch(
                    model, arm, rng, coords, snapshots, lane_plans
                )
                for lane, action in enumerate(actions):
                    claim_decisions[lane] += len(action.claims)
            else:
                actions = [StepInput.no_claims() for _ in snapshots]
            batch.step(tuple(actions))
        results: list[LearnedEpisodeResult] = []
        for lane, (snapshot, plans) in enumerate(zip(batch.snapshots, lane_plans)):
            if any(value is None for value in (snapshot.tau, snapshot.U, snapshot.F, snapshot.Y)):
                raise EmpiricalRunnerError("terminal native endpoint is incomplete")
            results.append(
                LearnedEpisodeResult(
                    tau=float(snapshot.tau),
                    U=float(snapshot.U),
                    F=float(snapshot.F),
                    Y=float(snapshot.Y),
                    plan_scores=tuple(plans.plan_scores) if training else (),
                    claim_scores=tuple(plans.claim_scores) if training else (),
                    agent_ticks=agent_ticks[lane],
                    claim_decisions=claim_decisions[lane],
                )
            )
        return tuple(results)
    finally:
        if not batch.closed:
            batch.close()


@dataclass(frozen=True)
class ScriptedEpisodeResult:
    tau: float
    U: float
    F: float
    agent_ticks: int
    claim_decisions: int


def _scripted_actions_python_oracle(
    package: str,
    coordinates: Sequence[EpisodeCoordinate],
    snapshots: Sequence[Snapshot],
    previous: Sequence[Mapping[int, int]],
) -> tuple[StepInput, ...]:
    """TEST-only scalar oracle for the compiled scripted action kernel."""

    actions: list[StepInput] = []
    for coordinate, snapshot, lane_previous in zip(coordinates, snapshots, previous):
        if not snapshot.claim_required:
            actions.append(StepInput.no_claims())
            continue
        keys = tuple(int(key) for key in snapshot.transport_keys)
        prior = tuple(lane_previous.get(key, -1) for key in keys)
        survivors = tuple(key in lane_previous for key in keys)
        first_or_epoch = snapshot.tick == 0 or snapshot.new_epoch
        before, after, event = _parse_cell(coordinate.cell)
        if package == SCRIPTED_PACKAGES[0]:
            raw = coherent_scaffold(
                snapshot.positions,
                snapshot.beacon_positions,
                snapshot.demands,
                previous_claims=prior,
                survivor=survivors,
                first_claim_or_new_epoch=first_or_epoch,
                entry_tiebreak=keys,
            )
        elif package == SCRIPTED_PACKAGES[1]:
            raw = fragmented_scaffold(
                snapshot.positions,
                snapshot.beacon_positions,
                snapshot.demands,
                active_churn=(before != after and event == "ACTIVE_CONTINUATION"),
                post_event_claim_index=(
                    (snapshot.tick - 24) // 4 if snapshot.tick >= 24 else None
                ),
                previous_claims=prior,
                survivor=survivors,
                first_claim_or_new_epoch=first_or_epoch,
                entry_tiebreak=keys,
            )
        else:
            raw = independent_nearest(snapshot.positions, snapshot.beacon_positions)
        actions.append(StepInput(tuple(int(value) for value in raw.tolist())))
    return tuple(actions)


def execute_scripted_batch(
    package: str,
    rng: SemanticRNG,
    coordinates: Sequence[EpisodeCoordinate],
) -> tuple[ScriptedEpisodeResult, ...]:
    coords = tuple(coordinates)
    _require_semantic_rng(rng).require_runtime_authority()
    if package not in SCRIPTED_PACKAGES or len(coords) not in SUPPORTED_BATCH_WIDTHS:
        raise EmpiricalRunnerError(
            "scripted execution requires one registered package and a supported native width"
        )
    fixtures = materialize_fixture_batch(rng, coords)
    batch = reset_native_batch(
        fixtures, packed_views=True, binding=rng._native_binding
    )
    previous: list[dict[int, int]] = [dict() for _ in coords]
    agent_ticks = [0] * len(coords)
    decisions = [0] * len(coords)
    try:
        while not all(snapshot.terminal for snapshot in batch.snapshots):
            snapshots = batch.snapshots
            if any(snapshot.event_input_required for snapshot in snapshots):
                if not all(snapshot.event_input_required for snapshot in snapshots):
                    raise EmpiricalRunnerError("native event lifecycle diverged across scripted B8")
                snapshots = batch.apply_event(
                    materialize_event_batch(rng, coords, batch, fixtures)
                )
            for lane, snapshot in enumerate(snapshots):
                agent_ticks[lane] += len(snapshot.positions)
            if snapshots[0].claim_required:
                if not all(snapshot.claim_required for snapshot in snapshots):
                    raise EmpiricalRunnerError("scripted claim lifecycle diverged across lanes")
                keys_by_lane = [
                    tuple(int(key) for key in snapshot.transport_keys) for snapshot in snapshots
                ]
                prior_by_lane = [
                    tuple(previous[lane].get(key, -1) for key in keys)
                    for lane, keys in enumerate(keys_by_lane)
                ]
                survivor_by_lane = [
                    tuple(key in previous[lane] for key in keys)
                    for lane, keys in enumerate(keys_by_lane)
                ]
                active_churn: list[bool] = []
                for coordinate in coords:
                    before, after, event = _parse_cell(coordinate.cell)
                    active_churn.append(before != after and event == "ACTIVE_CONTINUATION")
                actions = batch.scripted_actions(
                    SCRIPTED_PACKAGES.index(package),
                    prior_by_lane,
                    survivor_by_lane,
                    [snapshot.tick == 0 or snapshot.new_epoch for snapshot in snapshots],
                    active_churn,
                    [((snapshot.tick - 24) // 4 if snapshot.tick >= 24 else -1) for snapshot in snapshots],
                )
                for lane, (keys, action) in enumerate(zip(keys_by_lane, actions)):
                    previous[lane] = dict(zip(keys, action.claims))
                    decisions[lane] += len(action.claims)
            else:
                if any(snapshot.claim_required for snapshot in snapshots):
                    raise EmpiricalRunnerError("scripted claim lifecycle diverged across lanes")
                actions = tuple(StepInput.no_claims() for _ in snapshots)
            batch.step(tuple(actions))
        result: list[ScriptedEpisodeResult] = []
        for lane, snapshot in enumerate(batch.snapshots):
            if any(value is None for value in (snapshot.tau, snapshot.U, snapshot.F)):
                raise EmpiricalRunnerError("scripted terminal endpoint is incomplete")
            result.append(
                ScriptedEpisodeResult(
                    float(snapshot.tau),
                    float(snapshot.U),
                    float(snapshot.F),
                    agent_ticks[lane],
                    decisions[lane],
                )
            )
        return tuple(result)
    finally:
        if not batch.closed:
            batch.close()


def initialize_block_models(rng: SemanticRNG) -> dict[str, TBCFVModel]:
    """Materialize one common 26,161-scalar tensor and copy it across arms."""

    _require_semantic_rng(rng)
    reference = TBCFVModel()
    uniforms: dict[str, torch.Tensor] = {}
    for name, shape in required_affine_fixture_uniforms(reference).items():
        count = math.prod(shape)
        values = rng.uniform_many(
            tuple(
                _address(
                    rng.block_index,
                    parameter_entry=name,
                    draw_kind="common-initial-parameter",
                    draw_index=index,
                )
                for index in range(count)
            )
        )
        uniforms[name] = torch.tensor(values, dtype=torch.float64).reshape(shape)
    apply_affine_fixture_uniforms(reference, uniforms)
    models: dict[str, TBCFVModel] = {}
    for arm in LEARNED_PACKAGES:
        model = TBCFVModel()
        model.load_state_dict(reference.state_dict())
        models[arm] = model
    return models


def execute_training_update(
    model: TBCFVModel,
    arm: str,
    rng: SemanticRNG,
    update: int,
    baselines: torch.Tensor,
    *,
    authority_check: Callable[[], None] | None = None,
) -> tuple[torch.Tensor, dict[str, int]]:
    if arm not in LEARNED_PACKAGES or not 0 <= update < 800:
        raise EmpiricalRunnerError("training update address differs from r04")
    if tuple(baselines.shape) != (8,):
        raise EmpiricalRunnerError("training baselines must contain exact eight cells")
    results: list[LearnedEpisodeResult] = []
    cells: list[int] = []
    for cell_start in range(0, len(TRAINING_CELLS), 4):
        selected_cells = TRAINING_CELLS[cell_start : cell_start + 4]
        coordinates = tuple(
            EpisodeCoordinate(rng.block_index, cell, update, row)
            for cell in selected_cells
            for row in range(8)
        )
        batch_results = execute_learned_batch(model, arm, rng, coordinates, training=True)
        results.extend(batch_results)
        for cell_index in range(cell_start, cell_start + len(selected_cells)):
            cells.extend([cell_index] * 8)
    if len(results) != 64:
        raise EmpiricalRunnerError("one training update did not produce exactly 64 episodes")
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
        raise EmpiricalRunnerError("training loss is nonfinite")
    loss.backward()
    if authority_check is not None:
        authority_check()
    audit = apply_registered_block_update(model, baselines, returns, cell_indices)
    counts = {
        "training_episodes": 64,
        "environment_ticks": 64 * 64,
        "agent_ticks": sum(item.agent_ticks for item in results),
        "agent_claim_decisions": sum(item.claim_decisions for item in results),
    }
    counts["candidate_pointer_scores"] = counts["agent_claim_decisions"] * 6
    return audit.updated_baselines, counts


def _empty_cell_sums(owners: Sequence[str]) -> dict[str, dict[str, dict[str, float | int]]]:
    return {
        owner: {
            cell: {"episodes": 0, "tau_sum": 0.0, "U_sum": 0.0, "F_sum": 0.0}
            for cell in HELDOUT_CELLS
        }
        for owner in owners
    }


def _add_endpoints(target: dict[str, float | int], episodes: Sequence[object]) -> None:
    target["episodes"] = int(target["episodes"]) + len(episodes)
    target["tau_sum"] = float(target["tau_sum"]) + math.fsum(float(item.tau) for item in episodes)
    target["U_sum"] = float(target["U_sum"]) + math.fsum(float(item.U) for item in episodes)
    target["F_sum"] = float(target["F_sum"]) + math.fsum(float(item.F) for item in episodes)


def _cell_mean(
    aggregates: Mapping[str, Mapping[str, Mapping[str, Mapping[str, float | int]]]],
    family: str,
    owner: str,
    cell: str,
    endpoint: str,
) -> float:
    row = aggregates[family][owner][cell]
    episodes = int(row["episodes"])
    if episodes != 2_048:
        raise EmpiricalRunnerError(f"{family}.{owner}.{cell} is not a complete 2,048-episode cell")
    return float(row[f"{endpoint}_sum"]) / episodes


def registered_block_aggregates(
    aggregates: Mapping[str, Mapping[str, Mapping[str, Mapping[str, float | int]]]]
) -> dict[str, dict[str, float]]:
    """Map complete cell sums to the exact registered 44/4/10 block quantities."""

    learned = "learned"
    scripted = "scripted"

    def cell(path: str, event: str) -> str:
        return f"{path}.{event}"

    prerequisite: dict[str, float] = {}
    for path in ("8_to_12", "12_to_8"):
        active = cell(path, "ACTIVE_CONTINUATION")
        prerequisite[f"opportunity.time.{path}"] = (
            _cell_mean(aggregates, scripted, SCRIPTED_PACKAGES[1], active, "tau")
            - _cell_mean(aggregates, scripted, SCRIPTED_PACKAGES[0], active, "tau")
            - 3.0
        )
        prerequisite[f"opportunity.loss.{path}"] = (
            _cell_mean(aggregates, scripted, SCRIPTED_PACKAGES[1], active, "U")
            - _cell_mean(aggregates, scripted, SCRIPTED_PACKAGES[0], active, "U")
            - 0.05
        )
    for heldout in HELDOUT_CELLS:
        path, event = heldout.split(".", 1)
        suffix = f"{path}.{event.lower()}"
        coherent_t = _cell_mean(aggregates, scripted, SCRIPTED_PACKAGES[0], heldout, "tau")
        coherent_u = _cell_mean(aggregates, scripted, SCRIPTED_PACKAGES[0], heldout, "U")
        flex_t = _cell_mean(aggregates, learned, LEARNED_PACKAGES[1], heldout, "tau")
        flex_u = _cell_mean(aggregates, learned, LEARNED_PACKAGES[1], heldout, "U")
        nearest_t = _cell_mean(aggregates, scripted, SCRIPTED_PACKAGES[2], heldout, "tau")
        nearest_u = _cell_mean(aggregates, scripted, SCRIPTED_PACKAGES[2], heldout, "U")
        prerequisite[f"scaffold.time.{suffix}"] = 16.0 - coherent_t
        prerequisite[f"scaffold.loss.{suffix}"] = 0.10 - coherent_u
        prerequisite[f"flex.time_gap.{suffix}"] = nearest_t - flex_t - 2.0
        prerequisite[f"flex.loss_gap.{suffix}"] = nearest_u - flex_u - 0.05
        prerequisite[f"flex.loss_cap.{suffix}"] = 0.25 - flex_u
    direct: dict[str, float] = {}
    mechanism: dict[str, float] = {}
    for path, static in (("8_to_12", "12_to_12"), ("12_to_8", "8_to_8")):
        active = cell(path, "ACTIVE_CONTINUATION")
        static_active = cell(static, "ACTIVE_CONTINUATION")

        def T(arm: str, selected: str = active) -> float:
            return _cell_mean(aggregates, learned, arm, selected, "tau")

        def U(arm: str, selected: str = active) -> float:
            return _cell_mean(aggregates, learned, arm, selected, "U")

        def F(arm: str) -> float:
            return _cell_mean(aggregates, learned, arm, active, "F")

        d_time = T(LEARNED_PACKAGES[1]) - T(LEARNED_PACKAGES[0])
        static_d = T(LEARNED_PACKAGES[1], static_active) - T(
            LEARNED_PACKAGES[0], static_active
        )
        direct[f"time.{path}"] = d_time
        direct[f"loss.{path}"] = U(LEARNED_PACKAGES[1]) - U(LEARNED_PACKAGES[0])
        mechanism[f"churn_specificity.{path}"] = d_time - static_d
        mechanism[f"fragmentation.{path}"] = F(LEARNED_PACKAGES[1]) - F(
            LEARNED_PACKAGES[0]
        )
        mechanism[f"commonality.{path}"] = 0.5 * (
            T(LEARNED_PACKAGES[3])
            - T(LEARNED_PACKAGES[0])
            + T(LEARNED_PACKAGES[4])
            - T(LEARNED_PACKAGES[2])
        )
        mechanism[f"persistence.{path}"] = 0.5 * (
            T(LEARNED_PACKAGES[2])
            - T(LEARNED_PACKAGES[0])
            + T(LEARNED_PACKAGES[4])
            - T(LEARNED_PACKAGES[3])
        )
        mechanism[f"bundle.{path}"] = T(LEARNED_PACKAGES[4]) - T(
            LEARNED_PACKAGES[0]
        )
    from .inference import DIRECT_VALUE_VARIABLES, MECHANISM_VARIABLES, PREREQUISITE_VARIABLES

    if set(prerequisite) != set(PREREQUISITE_VARIABLES):
        raise EmpiricalRunnerError("prerequisite aggregate inventory differs")
    if set(direct) != set(DIRECT_VALUE_VARIABLES) or set(mechanism) != set(MECHANISM_VARIABLES):
        raise EmpiricalRunnerError("value/mechanism aggregate inventory differs")
    return {"prerequisite": prerequisite, "direct_value": direct, "mechanism": mechanism}


def _zero_counts() -> dict[str, int]:
    return {name: 0 for name in BLOCK_COUNTS}


@dataclass
class _BlockRuntime:
    phase: str
    models: dict[str, TBCFVModel]
    baselines: dict[str, torch.Tensor]
    updates: dict[str, int]
    learned_completed: dict[str, dict[str, int]]
    scripted_completed: dict[str, dict[str, int]]
    aggregates: dict[str, dict[str, dict[str, dict[str, float | int]]]]
    counts: dict[str, int]


def _new_block_runtime(rng: SemanticRNG) -> _BlockRuntime:
    return _BlockRuntime(
        phase="TRAINING",
        models=initialize_block_models(rng),
        baselines={arm: torch.zeros(8, dtype=torch.float64) for arm in LEARNED_PACKAGES},
        updates={arm: 0 for arm in LEARNED_PACKAGES},
        learned_completed={arm: {cell: 0 for cell in HELDOUT_CELLS} for arm in LEARNED_PACKAGES},
        scripted_completed={package: {cell: 0 for cell in HELDOUT_CELLS} for package in SCRIPTED_PACKAGES},
        aggregates={
            "learned": _empty_cell_sums(LEARNED_PACKAGES),
            "scripted": _empty_cell_sums(SCRIPTED_PACKAGES),
        },
        counts=_zero_counts(),
    )


def _add_counts(target: dict[str, int], values: Mapping[str, int]) -> None:
    for key, value in values.items():
        target[key] += int(value)
    target["total_episodes"] = (
        target["training_episodes"]
        + target["learned_heldout_episodes"]
        + target["scripted_heldout_episodes"]
    )
    target["candidate_pointer_scores"] = target["agent_claim_decisions"] * 6


def _canonical_bytes(value: object) -> bytes:
    return canonical_json_bytes(value)


def _torch_bytes(value: object) -> bytes:
    buffer = io.BytesIO()
    torch.save(value, buffer)
    return buffer.getvalue()


def _persist_runtime(
    frontier: AtomicEmpiricalFrontier,
    block_index: int,
    runtime: _BlockRuntime,
    *,
    failure_hook: Callable[[str], None] | None = None,
    authority_check: Callable[[], None] | None = None,
) -> str:
    payloads: dict[str, bytes] = {}
    for index, arm in enumerate(LEARNED_PACKAGES):
        payloads[f"arm{index}.model.pt"] = _torch_bytes(runtime.models[arm].state_dict())
        payloads[f"arm{index}.optimizer.json"] = _canonical_bytes(
            {
                "kind": "registered-plain-sgd-no-state",
                "arm": arm,
                "updates_completed": runtime.updates[arm],
                "momentum": False,
                "adaptive_moment": False,
            }
        )
        payloads[f"arm{index}.baselines.json"] = _canonical_bytes(
            {
                "arm": arm,
                "cell_order": list(TRAINING_CELLS),
                "values_hex": [float(value).hex() for value in runtime.baselines[arm]],
            }
        )
    payloads["semantic.json"] = _canonical_bytes(
        {
            "phase": runtime.phase,
            "updates": runtime.updates,
            "learned_completed": runtime.learned_completed,
            "scripted_completed": runtime.scripted_completed,
            "blinded": True,
            "partial_interpretation_permitted": False,
        }
    )
    payloads["aggregates.json"] = _canonical_bytes(runtime.aggregates)
    if authority_check is not None:
        authority_check()
    staged = frontier.stage_generation_payloads(
        block_index,
        payloads,
        owner_token=OWNER_TOKEN,
        failure_hook=failure_hook,
    )
    refs = staged.refs
    state = ResumeState(
        phase=runtime.phase,
        updates_completed=dict(runtime.updates),
        model_state={arm: refs[f"arm{index}.model.pt"] for index, arm in enumerate(LEARNED_PACKAGES)},
        optimizer_state={
            arm: refs[f"arm{index}.optimizer.json"]
            for index, arm in enumerate(LEARNED_PACKAGES)
        },
        baselines={
            arm: refs[f"arm{index}.baselines.json"]
            for index, arm in enumerate(LEARNED_PACKAGES)
        },
        semantic_coordinate=refs["semantic.json"],
        aggregates=refs["aggregates.json"],
        learned_heldout_completed={arm: dict(cells) for arm, cells in runtime.learned_completed.items()},
        scripted_heldout_completed={package: dict(cells) for package, cells in runtime.scripted_completed.items()},
        counts=dict(runtime.counts),
    )
    if authority_check is not None:
        authority_check()
    return frontier.commit_staged_resume(
        staged,
        state,
        owner_token=OWNER_TOKEN,
        failure_hook=failure_hook,
    )


def _read_json_ref(frontier: AtomicEmpiricalFrontier, ref: ArtifactRef) -> Mapping[str, object]:
    payload = (frontier.root / Path(ref.path)).read_bytes()
    value = json.loads(payload.decode("ascii"))
    if not isinstance(value, Mapping) or canonical_json_bytes(value) != payload:
        raise EmpiricalRunnerError("resume JSON payload is not canonical")
    return value


def _restore_runtime(frontier: AtomicEmpiricalFrontier, block_index: int) -> _BlockRuntime | None:
    block_root = frontier.root / "blocks" / f"block_{block_index:02d}"
    if not block_root.exists():
        return None
    complete = block_root / "COMPLETE.json"
    if complete.exists():
        return None
    generations, _ = frontier._validate_chain(block_index, require_data_exact=True)
    if not generations:
        return None
    state = generations[-1][1]
    models: dict[str, TBCFVModel] = {}
    baselines: dict[str, torch.Tensor] = {}
    for arm in LEARNED_PACKAGES:
        model = TBCFVModel()
        payload = torch.load(
            frontier.root / Path(state.model_state[arm].path),
            map_location="cpu",
            weights_only=True,
        )
        model.load_state_dict(payload)
        models[arm] = model
        baseline = _read_json_ref(frontier, state.baselines[arm])
        if baseline.get("arm") != arm or baseline.get("cell_order") != list(TRAINING_CELLS):
            raise EmpiricalRunnerError("resume baseline identity differs")
        values = baseline.get("values_hex")
        if not isinstance(values, list) or len(values) != 8:
            raise EmpiricalRunnerError("resume baseline inventory differs")
        baselines[arm] = torch.tensor([float.fromhex(str(value)) for value in values], dtype=torch.float64)
    aggregates = _read_json_ref(frontier, state.aggregates)
    semantic = _read_json_ref(frontier, state.semantic_coordinate)
    if semantic.get("phase") != state.phase:
        raise EmpiricalRunnerError("resume semantic phase differs")
    return _BlockRuntime(
        phase=state.phase,
        models=models,
        baselines=baselines,
        updates=dict(state.updates_completed),
        learned_completed={arm: dict(cells) for arm, cells in state.learned_heldout_completed.items()},
        scripted_completed={package: dict(cells) for package, cells in state.scripted_heldout_completed.items()},
        aggregates={
            "learned": {
                arm: {cell: dict(row) for cell, row in aggregates["learned"][arm].items()}  # type: ignore[index,union-attr]
                for arm in LEARNED_PACKAGES
            },
            "scripted": {
                package: {cell: dict(row) for cell, row in aggregates["scripted"][package].items()}  # type: ignore[index,union-attr]
                for package in SCRIPTED_PACKAGES
            },
        },
        counts=dict(state.counts),
    )


def _prepare_synthetic_ordinary_frontier(
    temp_root: Path,
) -> tuple[AtomicEmpiricalFrontier, _BlockRuntime]:
    """Prepare disposable state outside measurement for one ordinary transaction."""

    class SyntheticPreflightPermit:
        lease_id = "SYNTHETIC-TEST-PREFLIGHT"
        origin_lease_id = lease_id
        predecessor_lease_id = None
        replacement_index = 0
        lease_lineage = (lease_id,)
        stage_binding_sha256 = "6" * 64
        accepted_binding_sha256 = "7" * 64
        preactivity_certificate_sha256 = "8" * 64
        coordinate_proposal_sha256 = "9" * 64

        def require_active(self, *, now: datetime) -> None:
            if now.tzinfo is None:
                raise EmpiricalRunnerError("synthetic preflight time must be timezone-aware")

        def immutable_frontier_lease_binding(self) -> dict[str, str]:
            return {
                "origin_lease_id": self.origin_lease_id,
                "lease_id": self.origin_lease_id,
                "lease_binding_sha256": self.stage_binding_sha256,
            }

    workspace = Path(tempfile.mkdtemp(prefix="rcle_runner_ordinary_", dir=temp_root))
    frontier_root = workspace / "frontier"
    bindings = EmpiricalBindings(
        source_manifest_sha256="1" * 64,
        config_sha256="2" * 64,
        native_binding_sha256="3" * 64,
        coordinate_digest="4" * 64,
        master_digest="5" * 64,
        origin_lease_id=SyntheticPreflightPermit.origin_lease_id,
        lease_id=SyntheticPreflightPermit.origin_lease_id,
        lease_binding_sha256=SyntheticPreflightPermit.stage_binding_sha256,
    )
    permit = SyntheticPreflightPermit()
    now = datetime.now(timezone.utc)
    frontier = AtomicEmpiricalFrontier.create(
        frontier_root,
        bindings,
        owner_token=OWNER_TOKEN,
        permit=permit,
        now=now,
        lease_document_sha256="a" * 64,
    )
    runtime = _new_block_runtime(SyntheticTestRNG())
    return frontier, runtime


def _synthetic_empirical_frontier_chain(temp_root: Path) -> dict[str, object]:
    """Exercise the exact empirical staging/recovery seam with TEST-only state."""

    class SyntheticPreflightPermit:
        lease_id = "SYNTHETIC-TEST-PREFLIGHT"
        origin_lease_id = lease_id
        predecessor_lease_id = None
        replacement_index = 0
        lease_lineage = (lease_id,)
        stage_binding_sha256 = "6" * 64
        accepted_binding_sha256 = "7" * 64
        preactivity_certificate_sha256 = "8" * 64
        coordinate_proposal_sha256 = "9" * 64

        def require_active(self, *, now: datetime) -> None:
            if now.tzinfo is None:
                raise EmpiricalRunnerError("synthetic preflight time must be timezone-aware")

        def immutable_frontier_lease_binding(self) -> dict[str, str]:
            return {
                "origin_lease_id": self.origin_lease_id,
                "lease_id": self.origin_lease_id,
                "lease_binding_sha256": self.stage_binding_sha256,
            }

    workspace = Path(tempfile.mkdtemp(prefix="rcle_runner_atomic_", dir=temp_root))
    frontier_root = workspace / "frontier"
    bindings = EmpiricalBindings(
        source_manifest_sha256="1" * 64,
        config_sha256="2" * 64,
        native_binding_sha256="3" * 64,
        coordinate_digest="4" * 64,
        master_digest="5" * 64,
        origin_lease_id=SyntheticPreflightPermit.origin_lease_id,
        lease_id=SyntheticPreflightPermit.origin_lease_id,
        lease_binding_sha256=SyntheticPreflightPermit.stage_binding_sha256,
    )
    permit = SyntheticPreflightPermit()
    now = datetime.now(timezone.utc)
    frontier = AtomicEmpiricalFrontier.create(
        frontier_root,
        bindings,
        owner_token=OWNER_TOKEN,
        permit=permit,
        now=now,
        lease_document_sha256="a" * 64,
    )
    runtime = _new_block_runtime(SyntheticTestRNG())

    def injected_process_loss(phase: str) -> None:
        if phase == "after_payload_staging":
            raise RuntimeError("fixed synthetic process loss after payload staging")

    try:
        _persist_runtime(
            frontier,
            0,
            runtime,
            failure_hook=injected_process_loss,
        )
    except RuntimeError as exc:
        if str(exc) != "fixed synthetic process loss after payload staging":
            raise
    else:
        raise EmpiricalRunnerError("synthetic staging crash injection was not exercised")
    if not (frontier_root / "blocks" / "block_00" / ".staging").is_dir():
        raise EmpiricalRunnerError("synthetic staged frontier was not durable")

    recovered = AtomicEmpiricalFrontier.resume(
        frontier_root,
        bindings,
        owner_token=OWNER_TOKEN,
        permit=permit,
        now=now,
        lease_document_sha256="a" * 64,
    )
    if (frontier_root / "blocks" / "block_00").exists():
        raise EmpiricalRunnerError("uncommitted synthetic staging was not recovered")
    _persist_runtime(recovered, 0, runtime)

    def injected_partial_publication_loss(phase: str) -> None:
        if phase == "after_payload_publication":
            raise RuntimeError("fixed synthetic process loss after payload publication")

    try:
        _persist_runtime(
            recovered,
            0,
            runtime,
            failure_hook=injected_partial_publication_loss,
        )
    except RuntimeError as exc:
        if str(exc) != "fixed synthetic process loss after payload publication":
            raise
    else:
        raise EmpiricalRunnerError("synthetic partial-publication crash was not exercised")
    resumed = AtomicEmpiricalFrontier.resume(
        frontier_root,
        bindings,
        owner_token=OWNER_TOKEN,
        permit=permit,
        now=now,
        lease_document_sha256="a" * 64,
    )
    restored = _restore_runtime(resumed, 0)
    if (
        restored is None
        or restored.phase != "TRAINING"
        or dict(restored.updates) != {arm: 0 for arm in LEARNED_PACKAGES}
    ):
        raise EmpiricalRunnerError("synthetic staged generation did not resume exactly")
    return {
        "synthetic_generation_staged": True,
        "injected_process_loss_recovered": True,
        "partial_publication_recovered": True,
        "atomic_generation_published": True,
        "exact_generation_resumed": True,
    }


def _evaluation_counts(episodes: Sequence[object], *, learned: bool) -> dict[str, int]:
    return {
        "learned_heldout_episodes" if learned else "scripted_heldout_episodes": len(episodes),
        "environment_ticks": len(episodes) * 64,
        "agent_ticks": sum(int(item.agent_ticks) for item in episodes),
        "agent_claim_decisions": sum(int(item.claim_decisions) for item in episodes),
    }


def execute_run_block(
    frontier: AtomicEmpiricalFrontier,
    authority: ProductionAuthority,
    block_index: int,
    *,
    now: datetime,
) -> str:
    """Execute/resume one blinded block; commits only fixed mechanical boundaries."""

    authority.require_active(now=now)
    def require_live_authority() -> None:
        authority.require_active(now=datetime.now(timezone.utc))

    block_complete = frontier.root / "blocks" / f"block_{block_index:02d}" / "COMPLETE.json"
    if block_complete.is_file():
        frontier.validate()
        return hashlib.sha256(block_complete.read_bytes()).hexdigest()
    rng = SemanticRNG(authority, block_index, now=now)
    runtime = _restore_runtime(frontier, block_index)
    if runtime is None:
        runtime = _new_block_runtime(rng)
        _persist_runtime(
            frontier, block_index, runtime, authority_check=require_live_authority
        )

    if runtime.phase == "TRAINING":
        if len(set(runtime.updates.values())) != 1:
            raise EmpiricalRunnerError("resume training arms are not at the same paired update")
        start = next(iter(runtime.updates.values()))
        for update in range(start, 800):
            require_live_authority()
            for arm in LEARNED_PACKAGES:
                baselines, counts = execute_training_update(
                    runtime.models[arm],
                    arm,
                    rng,
                    update,
                    runtime.baselines[arm],
                    authority_check=require_live_authority,
                )
                runtime.baselines[arm] = baselines
                runtime.updates[arm] = update + 1
                _add_counts(runtime.counts, counts)
            if (update + 1) % 100 == 0:
                _persist_runtime(
                    frontier, block_index, runtime, authority_check=require_live_authority
                )
        runtime.phase = "LEARNED_EVALUATION"
        _persist_runtime(
            frontier, block_index, runtime, authority_check=require_live_authority
        )

    if runtime.phase == "LEARNED_EVALUATION":
        for arm in LEARNED_PACKAGES:
            for cell in HELDOUT_CELLS:
                completed = runtime.learned_completed[arm][cell]
                if completed == 2_048:
                    continue
                if completed != 0:
                    raise EmpiricalRunnerError("learned heldout resume must be cell-atomic")
                for start in range(0, 2_048, max(SUPPORTED_BATCH_WIDTHS)):
                    width = max(SUPPORTED_BATCH_WIDTHS)
                    coordinates = tuple(
                        EpisodeCoordinate(
                            block_index, cell, start + row, row % SELECTED_BATCH_WIDTH
                        )
                        for row in range(width)
                    )
                    with torch.no_grad():
                        episodes = execute_learned_batch(
                            runtime.models[arm], arm, rng, coordinates, training=False
                        )
                    _add_endpoints(runtime.aggregates["learned"][arm][cell], episodes)
                    _add_counts(runtime.counts, _evaluation_counts(episodes, learned=True))
                runtime.learned_completed[arm][cell] = 2_048
            # One arm/cell-panel is the atomic learned-evaluation frontier.
            _persist_runtime(
                frontier, block_index, runtime, authority_check=require_live_authority
            )
        runtime.phase = "SCRIPTED_EVALUATION"
        _persist_runtime(
            frontier, block_index, runtime, authority_check=require_live_authority
        )

    if runtime.phase == "SCRIPTED_EVALUATION":
        for package in SCRIPTED_PACKAGES:
            for cell in HELDOUT_CELLS:
                completed = runtime.scripted_completed[package][cell]
                if completed == 2_048:
                    continue
                if completed != 0:
                    raise EmpiricalRunnerError("scripted heldout resume must be cell-atomic")
                for start in range(0, 2_048, max(SUPPORTED_BATCH_WIDTHS)):
                    width = max(SUPPORTED_BATCH_WIDTHS)
                    coordinates = tuple(
                        EpisodeCoordinate(
                            block_index, cell, start + row, row % SELECTED_BATCH_WIDTH
                        )
                        for row in range(width)
                    )
                    episodes = execute_scripted_batch(package, rng, coordinates)
                    _add_endpoints(runtime.aggregates["scripted"][package][cell], episodes)
                    _add_counts(runtime.counts, _evaluation_counts(episodes, learned=False))
                runtime.scripted_completed[package][cell] = 2_048
            # One complete eight-cell package is the atomic scripted frontier.
            _persist_runtime(
                frontier, block_index, runtime, authority_check=require_live_authority
            )
        runtime.phase = "BLOCK_COMPLETE"
        if runtime.counts != BLOCK_COUNTS:
            raise EmpiricalRunnerError(
                f"complete block work counts differ: observed={runtime.counts}, expected={BLOCK_COUNTS}"
            )
        # Validate all registered block quantities before sealing, without
        # exposing them outside the blinded frontier.
        registered_block_aggregates(runtime.aggregates)
        _persist_runtime(
            frontier, block_index, runtime, authority_check=require_live_authority
        )

    if runtime.phase != "BLOCK_COMPLETE":
        raise EmpiricalRunnerError("run block stopped at an unknown mechanical phase")
    require_live_authority()
    return frontier.seal_block(block_index, owner_token=OWNER_TOKEN)


def _complete_runtime(frontier: AtomicEmpiricalFrontier, block_index: int) -> tuple[_BlockRuntime, str]:
    block_root = frontier.root / "blocks" / f"block_{block_index:02d}"
    marker = block_root / "COMPLETE.json"
    if not marker.is_file():
        raise EmpiricalRunnerError("complete block marker is absent")
    generations, _ = frontier._validate_chain(block_index, require_data_exact=True)
    if not generations:
        raise EmpiricalRunnerError("complete block has no resume generation")
    # Temporarily route through the same restoration logic by reading the final
    # state directly; sealed blocks are immutable and cannot receive commits.
    state = generations[-1][1]
    models: dict[str, TBCFVModel] = {}
    baselines: dict[str, torch.Tensor] = {}
    for arm in LEARNED_PACKAGES:
        model = TBCFVModel()
        model.load_state_dict(
            torch.load(
                frontier.root / Path(state.model_state[arm].path),
                map_location="cpu",
                weights_only=True,
            )
        )
        models[arm] = model
        baseline = _read_json_ref(frontier, state.baselines[arm])
        baselines[arm] = torch.tensor(
            [float.fromhex(str(value)) for value in baseline["values_hex"]],  # type: ignore[index]
            dtype=torch.float64,
        )
    aggregate = _read_json_ref(frontier, state.aggregates)
    runtime = _BlockRuntime(
        phase=state.phase,
        models=models,
        baselines=baselines,
        updates=dict(state.updates_completed),
        learned_completed={arm: dict(cells) for arm, cells in state.learned_heldout_completed.items()},
        scripted_completed={package: dict(cells) for package, cells in state.scripted_heldout_completed.items()},
        aggregates={
            "learned": {arm: {cell: dict(aggregate["learned"][arm][cell]) for cell in HELDOUT_CELLS} for arm in LEARNED_PACKAGES},  # type: ignore[index]
            "scripted": {package: {cell: dict(aggregate["scripted"][package][cell]) for cell in HELDOUT_CELLS} for package in SCRIPTED_PACKAGES},  # type: ignore[index]
        },
        counts=dict(state.counts),
    )
    return runtime, hashlib.sha256(marker.read_bytes()).hexdigest()


def empirical_block_record(
    frontier: AtomicEmpiricalFrontier, block_index: int
) -> dict[str, object]:
    from dataclasses import asdict
    from .empirical_inference import EMPIRICAL_ANALYZER_INPUT_SCHEMA, EMPIRICAL_RECORD_CLASS

    runtime, marker_sha = _complete_runtime(frontier, block_index)
    aggregates = registered_block_aggregates(runtime.aggregates)
    aggregate_sha = hashlib.sha256(canonical_json_bytes(aggregates)).hexdigest()
    return {
        "schema": EMPIRICAL_ANALYZER_INPUT_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "record_class": EMPIRICAL_RECORD_CLASS,
        "empirical_record": True,
        "fixture_only": False,
        "synthetic_test_only": False,
        "block_index": block_index,
        "block_complete_sha256": marker_sha,
        "aggregate_sha256": aggregate_sha,
        "bindings": asdict(frontier.bindings),
        "technical_complete": True,
        "complete_marker_bound": True,
        "treatment_fidelity": True,
        "analytic_containment": True,
        "selection_or_adaptation": False,
        "evaluation_adaptation": False,
        "forbidden_information": False,
        "registered_coordinate": True,
        "learned_arms": list(LEARNED_PACKAGES),
        "scripted_packages": list(SCRIPTED_PACKAGES),
        "training_cells": list(TRAINING_CELLS),
        "heldout_cells": list(HELDOUT_CELLS),
        "updates_completed": dict(runtime.updates),
        "training_cell_episodes": {
            arm: {cell: 6_400 for cell in TRAINING_CELLS} for arm in LEARNED_PACKAGES
        },
        "learned_heldout_episodes": {
            arm: dict(cells) for arm, cells in runtime.learned_completed.items()
        },
        "scripted_heldout_episodes": {
            package: dict(cells) for package, cells in runtime.scripted_completed.items()
        },
        "counts": dict(runtime.counts),
        "aggregates": aggregates,
    }


def _live_native_preflight(authority: ProductionAuthority, *, now: datetime) -> dict[str, object]:
    """Load the exact B8 shared component only after complete admission."""

    authority.require_active(now=now)
    if not isinstance(getattr(authority, "certificate", None), Mapping):
        raise EmpiricalRunnerError("production process execution requires fully admitted authority")
    receipt = require_cpp_batched_production(
        SHARED_COMPONENT,
        backend="cpp",
        batch_width=SELECTED_BATCH_WIDTH,
    )
    if (
        receipt.get("component") != SHARED_COMPONENT
        or receipt.get("backend") != "cpp"
        or receipt.get("batch_width") != SELECTED_BATCH_WIDTH
        or receipt.get("full_reset_step_cpp") is not True
        or receipt.get("python_fallback") is not False
    ):
        raise EmpiricalRunnerError("shared native production receipt differs")
    observed = native_artifact_identity()
    frozen = authority.certificate["native"]
    if not isinstance(frozen, Mapping):
        raise EmpiricalRunnerError("certificate native identity is malformed")
    if (
        observed.get("sha256") != frozen.get("artifact_sha256")
        or observed.get("source_sha256") != frozen.get("source_sha256")
        or observed.get("build_key") != frozen.get("build_key")
    ):
        raise EmpiricalRunnerError("live native source/build/artifact differs from preactivity acceptance")
    return dict(receipt)


def empirical_bindings(authority: ProductionAuthority) -> EmpiricalBindings:
    cert = authority.certificate
    lease_binding = authority.permit.immutable_frontier_lease_binding()
    return EmpiricalBindings(
        source_manifest_sha256=str(cert["source"]["source_set_sha256"]),  # type: ignore[index]
        config_sha256=str(cert["config"]["config_sha256"]),  # type: ignore[index]
        native_binding_sha256=str(cert["native"]["native_identity_sha256"]),  # type: ignore[index]
        coordinate_digest=authority.coordinate_digest,
        master_digest=authority.master_digest,
        origin_lease_id=lease_binding["origin_lease_id"],
        lease_id=lease_binding["lease_id"],
        lease_binding_sha256=lease_binding["lease_binding_sha256"],
    )


def open_frontier(authority: ProductionAuthority, *, now: datetime) -> AtomicEmpiricalFrontier:
    """Open/create the exact frontier after admission and native identity check."""

    _live_native_preflight(authority, now=now)
    bindings = empirical_bindings(authority)
    frontier_root = Path(authority.permit.paths["frontier_root"])
    lease_sha256 = document_sha256(authority.lease_document)
    if authority.source_repair_transition is not None:
        if authority.original_frontier_bindings is None or not frontier_root.is_dir():
            raise EmpiricalRunnerError("source repair requires the existing original frontier")
        if (frontier_root / "stage_repairs").exists():
            return AtomicEmpiricalFrontier.resume(
                frontier_root,
                bindings,
                owner_token=OWNER_TOKEN,
                permit=authority.permit,
                now=now,
                lease_document_sha256=lease_sha256,
            )
        return AtomicEmpiricalFrontier.apply_source_repair(
            frontier_root,
            authority.original_frontier_bindings,
            bindings,
            repair_transition=authority.source_repair_transition,
            permit=authority.permit,
            now=now,
            lease_document_sha256=lease_sha256,
            owner_token=OWNER_TOKEN,
        )
    if frontier_root.exists():
        return AtomicEmpiricalFrontier.resume(
            frontier_root,
            bindings,
            owner_token=OWNER_TOKEN,
            permit=authority.permit,
            now=now,
            lease_document_sha256=lease_sha256,
        )
    return AtomicEmpiricalFrontier.create(
        frontier_root,
        bindings,
        owner_token=OWNER_TOKEN,
        permit=authority.permit,
        now=now,
        lease_document_sha256=lease_sha256,
    )


def make_resource_request(
    certificate: Mapping[str, object], *, result_root: str | Path
) -> dict[str, object]:
    return resource_request_proposal(
        certificate,
        repository_root=Path(__file__).resolve().parents[3],
        result_root=_inside_repository(result_root),
    )


def read_admission_files(
    *,
    certificate_path: str | Path,
    accepted_binding_path: str | Path,
    resource_request_path: str | Path,
    lease_path: str | Path,
    coordinate_binding_path: str | Path,
    result_root: str | Path,
    now: datetime,
    predecessor_lease_paths: Sequence[str | Path] = (),
) -> ProductionAuthority:
    return admit_production(
        certificate=_read_canonical_mapping(certificate_path, "preactivity certificate"),
        accepted_binding=_read_canonical_mapping(accepted_binding_path, "accepted binding"),
        resource_request=_read_canonical_mapping(resource_request_path, "resource request"),
        lease=_read_canonical_mapping(lease_path, "Root lease"),
        coordinate_binding=_read_canonical_mapping(coordinate_binding_path, "coordinate binding"),
        result_root=result_root,
        now=now,
        predecessor_leases=tuple(
            _read_canonical_mapping(path, "predecessor Root lease")
            for path in predecessor_lease_paths
        ),
    )


def read_source_repair_admission_files(
    *,
    predecessor_certificate_path: str | Path,
    predecessor_accepted_binding_path: str | Path,
    predecessor_resource_request_path: str | Path,
    predecessor_lease_path: str | Path,
    certificate_path: str | Path,
    accepted_binding_path: str | Path,
    resource_request_path: str | Path,
    lease_path: str | Path,
    repair_transition_path: str | Path,
    run_identity_path: str | Path,
    failed_terminal_path: str | Path,
    result_root: str | Path,
    now: datetime,
) -> ProductionAuthority:
    return admit_source_repair(
        predecessor_certificate=_read_canonical_mapping(
            predecessor_certificate_path, "predecessor preactivity certificate"
        ),
        predecessor_accepted_binding=_read_canonical_mapping(
            predecessor_accepted_binding_path, "predecessor accepted binding"
        ),
        predecessor_resource_request=_read_canonical_mapping(
            predecessor_resource_request_path, "predecessor resource request"
        ),
        predecessor_lease=_read_canonical_mapping(
            predecessor_lease_path, "predecessor Root lease"
        ),
        certificate=_read_canonical_mapping(
            certificate_path, "repaired preactivity certificate"
        ),
        accepted_binding=_read_canonical_mapping(
            accepted_binding_path, "repaired accepted binding"
        ),
        resource_request=_read_canonical_mapping(
            resource_request_path, "repaired resource request"
        ),
        lease=_read_canonical_mapping(lease_path, "source repair replacement lease"),
        repair_transition=_read_canonical_mapping(
            repair_transition_path, "source repair transition"
        ),
        run_identity_path=run_identity_path,
        failed_terminal_path=failed_terminal_path,
        result_root=result_root,
        now=now,
    )


def _production_process_resource(authority: ProductionAuthority) -> dict[str, object]:
    """Consume the exact request/lease-bound four-root process resource."""

    native = authority.certificate["native"]
    source = authority.certificate["source"]
    if not isinstance(native, Mapping) or not isinstance(source, Mapping):
        raise EmpiricalRunnerError("process resource certificate binding is malformed")
    resource_value = authority.permit.resources.get("process_resource")
    if not isinstance(resource_value, Mapping):
        raise EmpiricalRunnerError("Root lease omits the exact process resource")
    resource = validate_process_resource_object(resource_value)
    paths = resource["paths"]
    if not isinstance(paths, Mapping):
        raise EmpiricalRunnerError("process resource paths are malformed")
    if (
        Path(str(resource["canonical_result_root"])).resolve() != authority.result_root
        or resource["source_set_sha256"] != source["source_set_sha256"]
        or resource["native_binding_sha256"] != native["native_identity_sha256"]
        or any(authority.permit.paths.get(str(key)) != str(item) for key, item in paths.items())
    ):
        raise EmpiricalRunnerError("process resource differs from request/lease/certificate")
    return resource


def _production_worker_context(
    frontier: AtomicEmpiricalFrontier,
    authority: ProductionAuthority,
    payload: Mapping[str, object],
) -> dict[str, object]:
    native = authority.certificate["native"]
    if not isinstance(native, Mapping):
        raise EmpiricalRunnerError("production worker native binding is malformed")
    bindings = empirical_bindings(authority)
    audit_paths = sorted((frontier.root / "lease_audits").glob("lease_*.json"))
    if not audit_paths:
        raise EmpiricalRunnerError("production frontier lease audit is absent")
    current_audit = _read_canonical_mapping(audit_paths[-1], "production lease audit")
    if current_audit.get("lease_document_sha256") != document_sha256(authority.lease_document):
        raise EmpiricalRunnerError("production frontier lease document differs")
    body: dict[str, object] = {
        "schema": "RCLE_TBCFV_R04_CLOSED_ONE_BLOCK_PRODUCTION_CONTEXT_V1",
        "block_index": payload["block_index"],
        "identity": str(authority.coordinate_binding["identity"]),
        "coordinate_binding_sha256": authority.coordinate_digest,
        "master_digest": authority.master_digest,
        "block_root_digest": payload["block_root_digest"],
        "source_set_sha256": payload["source_set_sha256"],
        "native_binding_sha256": payload["native_binding_sha256"],
        "native_source_sha256": native["source_sha256"],
        "native_build_key": native["build_key"],
        "native_artifact_sha256": native["artifact_sha256"],
        "empirical_bindings": asdict(bindings),
        "origin_lease_id": authority.permit.origin_lease_id,
        "stage_binding_sha256": authority.permit.stage_binding_sha256,
        "accepted_binding_sha256": authority.permit.accepted_binding_sha256,
        "preactivity_certificate_sha256": authority.permit.preactivity_certificate_sha256,
        "coordinate_proposal_sha256": authority.permit.coordinate_proposal_sha256,
        "lease_document_sha256": document_sha256(authority.lease_document),
        "lease_validated_at": current_audit["validated_at"],
        "expires_at": authority.permit.expires_at,
        "one_thread": True,
        "gpu_count": 0,
        "canonical_paths_present": False,
        "result_blind": True,
        "protocol_canary": False,
        "protocol_canary_failure_once": False,
    }
    return {**body, "context_sha256": hashlib.sha256(canonical_json_bytes(body)).hexdigest()}


def _prepare_production_worker_call(
    frontier: AtomicEmpiricalFrontier,
    authority: ProductionAuthority,
    resource: Mapping[str, object],
    block_index: int,
) -> tuple[str, dict[str, object], dict[str, object]]:
    native = authority.certificate["native"]
    if not isinstance(native, Mapping):
        raise EmpiricalRunnerError("production worker native identity is malformed")
    payload = make_spawn_payload(
        resource,
        block_index=block_index,
        block_root_digest=authority.block_root_digest(block_index),
        native_source_sha256=str(native["source_sha256"]),
        native_build_key=str(native["build_key"]),
        expires_at=authority.permit.expires_at,
        test_only=False,
        test_steps=1,
    )
    context = _production_worker_context(frontier, authority, payload)
    authorization = make_worker_authorization(
        resource, payload, production_context=context
    )
    payload_path = (
        Path(str(payload["private_scratch_root"]))
        / f"b{block_index:02d}"
        / "p.json"
    )
    if payload_path.exists():
        observed = _read_canonical_mapping(payload_path, "production spawn payload")
        if observed != payload:
            raise EmpiricalRunnerError("existing production spawn payload differs")
    else:
        write_spawn_payload(payload_path, payload)
    return str(payload_path), authorization, payload


def _prevalidate_production_packet(
    frontier: AtomicEmpiricalFrontier,
    authority: ProductionAuthority,
    packet_path: str,
    payload: Mapping[str, object],
    authorization: Mapping[str, object],
) -> Mapping[str, object]:
    manifest = validate_production_worker_packet(
        packet_path, payload, worker_authorization=authorization
    )
    validation_root = Path(
        tempfile.mkdtemp(prefix=".rcle-parent-validate-", dir=frontier.root.parent)
    )
    try:
        shutil.copy2(frontier.root / "bindings.json", validation_root / "bindings.json")
        shutil.copytree(frontier.root / "lease_audits", validation_root / "lease_audits")
        if (frontier.root / "stage_repairs").exists():
            shutil.copytree(frontier.root / "stage_repairs", validation_root / "stage_repairs")
        (validation_root / "blocks").mkdir()
        block_index = int(manifest["block_index"])
        shutil.copytree(
            Path(packet_path) / "block",
            validation_root / "blocks" / f"block_{block_index:02d}",
        )
        validation = AtomicEmpiricalFrontier.resume(
            validation_root,
            frontier.bindings,
            owner_token=OWNER_TOKEN,
            permit=authority.permit,
            now=datetime.now(timezone.utc),
            lease_document_sha256=document_sha256(authority.lease_document),
        )
        validation._validate_block(block_index)
    finally:
        shutil.rmtree(validation_root)
    return manifest


def _install_prevalidated_production_packet(
    frontier: AtomicEmpiricalFrontier,
    packet_path: str,
    manifest: Mapping[str, object],
) -> None:
    block_index = int(manifest["block_index"])
    target = frontier.root / "blocks" / f"block_{block_index:02d}"
    if target.exists():
        frontier._validate_block(block_index)
        marker = target / "COMPLETE.json"
        if hashlib.sha256(marker.read_bytes()).hexdigest() != manifest["complete_marker_sha256"]:
            raise EmpiricalRunnerError("existing canonical block differs from worker packet")
        return
    container = Path(
        tempfile.mkdtemp(prefix=f".rcle-block-{block_index:02d}-", dir=frontier.root.parent)
    )
    staging = container / f"block_{block_index:02d}"
    try:
        shutil.copytree(Path(packet_path) / "block", staging)
        with frontier._exclusive_commit(OWNER_TOKEN):
            if target.exists():
                raise EmpiricalRunnerError("canonical block appeared during parent install")
            os.rename(staging, target)
            frontier._validate_block(block_index)
    finally:
        if container.exists():
            shutil.rmtree(container)


def _execute_process_blocks(
    frontier: AtomicEmpiricalFrontier,
    authority: ProductionAuthority,
    *,
    workers: int,
) -> None:
    resource = _production_process_resource(authority)
    calls: list[tuple[str, dict[str, object], dict[str, object]]] = []
    for block_index in range(20):
        marker = frontier.root / "blocks" / f"block_{block_index:02d}" / "COMPLETE.json"
        if marker.is_file():
            frontier._validate_block(block_index)
            continue
        calls.append(_prepare_production_worker_call(frontier, authority, resource, block_index))
    if calls:
        with ProcessPoolExecutor(
            max_workers=workers,
            mp_context=multiprocessing.get_context("spawn"),
        ) as pool:
            futures = [
                pool.submit(run_production_block_worker, path, authorization)
                for path, authorization, _ in calls
            ]
            rows = [future.result() for future in futures]
        prevalidated: list[tuple[int, str, Mapping[str, object]]] = []
        for row, (_, authorization, payload) in zip(rows, calls):
            packet_path = str(row["packet_path"])
            manifest = _prevalidate_production_packet(
                frontier, authority, packet_path, payload, authorization
            )
            prevalidated.append((int(manifest["block_index"]), packet_path, manifest))
        for _, packet_path, manifest in sorted(prevalidated, key=lambda item: item[0]):
            authority.require_active(now=datetime.now(timezone.utc))
            _install_prevalidated_production_packet(frontier, packet_path, manifest)
    paths = resource["paths"]
    assert isinstance(paths, Mapping)
    private_bytes = sum(tree_size_bytes(str(path)) for path in paths.values())
    if private_bytes > 12 * 1024**3:
        raise EmpiricalRunnerError("combined private worker scratch exceeds 12 GiB")
    if tree_size_bytes(frontier.root) > 1024**3:
        raise EmpiricalRunnerError("canonical durable frontier exceeds 1 GiB")


def execute_full_panel(
    authority: ProductionAuthority, *, now: datetime, workers: int = 1
) -> Mapping[str, object]:
    """Execute/resume exactly twenty blocks and publish only the complete panel."""

    authority.require_active(now=now)
    if workers not in _SUPPORTED_WORKERS:
        raise EmpiricalRunnerError("workers must be one of 1, 2, or 4")
    torch.set_num_threads(1)
    if torch.get_num_threads() != 1:
        raise EmpiricalRunnerError("production requires one Torch CPU thread per worker")
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    if torch.get_num_interop_threads() != 1:
        raise EmpiricalRunnerError("production requires one Torch inter-op thread per process")
    frontier = open_frontier(authority, now=now)
    published = frontier.root / "published"
    if published.exists():
        complete = frontier.restore_complete_panel()
        return {
            "schema": RUNNER_SCHEMA,
            "mode": "FULL_PANEL_COMPLETE",
            "complete": True,
            "complete_blocks": 20,
            "registered_tails": 72,
            "manifest_sha256": hashlib.sha256(
                canonical_json_bytes(complete.manifest)
            ).hexdigest(),
            "result_exposed": False,
        }
    _execute_process_blocks(frontier, authority, workers=workers)
    authority.require_active(now=datetime.now(timezone.utc))
    frontier.validate(require_complete_blocks=True, permit_published=False)
    records = [empirical_block_record(frontier, index) for index in range(20)]
    complete_cell_aggregates = [
        {"block_index": index, "cells": _complete_runtime(frontier, index)[0].aggregates}
        for index in range(20)
    ]
    from .empirical_inference import analyze_empirical_complete_panel

    authority.require_active(now=datetime.now(timezone.utc))
    outcome = analyze_empirical_complete_panel(records, expected_bindings=frontier.bindings)
    if (
        not outcome.admitted_empirical
        or outcome.scientific_branch is None
        or outcome.analyzer_payload is None
        or outcome.registered_tail_count != 72
    ):
        raise EmpiricalRunnerError(
            f"complete empirical analyzer failed closed: {outcome.failure_reason}"
        )
    result_payload = canonical_json_bytes(
        {
            "schema": RESULT_OUTPUT_SCHEMA,
            "science_revision": SCIENCE_REVISION,
            "empirical_object": EMPIRICAL_OBJECT,
            "block_count": 20,
            "counts": dict(PANEL_COUNTS),
            "analyzer_sha256": hashlib.sha256(outcome.analyzer_payload).hexdigest(),
            "branch": outcome.scientific_branch,
            "payload": {
                "records": records,
                "cell_aggregates": complete_cell_aggregates,
                "complete": True,
                "partial_interpretation_permitted": False,
            },
        }
    )
    authority.require_active(now=datetime.now(timezone.utc))
    published_path = frontier.publish_complete_panel(
        branch=outcome.scientific_branch,
        analyzer_payload=outcome.analyzer_payload,
        result_payload=result_payload,
        owner_token=OWNER_TOKEN,
    )
    manifest_payload = (published_path / "manifest.json").read_bytes()
    return {
        "schema": RUNNER_SCHEMA,
        "mode": "FULL_PANEL_COMPLETE",
        "complete": True,
        "complete_blocks": 20,
        "registered_tails": 72,
        "manifest_sha256": hashlib.sha256(manifest_payload).hexdigest(),
        "result_exposed": False,
    }


def analyze_complete_panel(authority: ProductionAuthority, *, now: datetime) -> Mapping[str, object]:
    """Release analysis only from an exact twenty-block published frontier."""

    authority.require_active(now=now)
    frontier = open_frontier(authority, now=now)
    complete = frontier.restore_complete_panel()
    return {
        "schema": RUNNER_SCHEMA,
        "mode": "COMPLETE_ANALYSIS",
        "science_revision": SCIENCE_REVISION,
        "empirical_object": EMPIRICAL_OBJECT,
        "branch": complete.branch,
        "manifest": dict(complete.manifest),
        "analyzer_sha256": hashlib.sha256(complete.analyzer_payload).hexdigest(),
        "result_sha256": hashlib.sha256(complete.result_payload).hexdigest(),
        "complete_blocks": 20,
        "registered_tails": 72,
    }


__all__ = [
    "EmpiricalRunnerError",
    "OWNER_TOKEN",
    "ProductionAuthority",
    "RUNNER_SCHEMA",
    "SemanticRNG",
    "admit_production",
    "admit_source_repair",
    "analyze_complete_panel",
    "coordinate_proposal",
    "empirical_bindings",
    "execute_full_panel",
    "make_resource_request",
    "open_frontier",
    "read_admission_files",
    "read_source_repair_admission_files",
    "result_blind_preactivity_summary",
    "validate_materialized_binding",
]

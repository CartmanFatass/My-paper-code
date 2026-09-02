"""Explicit A/RECON and RUN-01 entry points for the isolated SCDMP B01 chain."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
from typing import Callable, Sequence

import torch

from .assessment import raise_after_quarantine, run_assess
from .active_gate import ActiveInvocationGate
from .quarantine import validate_quarantine_lock
from .contracts import NAMED_RUN_ID, RESOURCE_CAPS
from .orchestration import (
    Attempt, AttemptError, atomic_create_bytes, atomic_create_json, canonical_result_root,
    _initialize_or_resume_attempt, _issue_initial_telemetry_witness, _validate_resume_history,
    _read_regular_bytes, load_checkpoint_training_receipt, load_foundation_checkpoint,
    validate_sealed_identity,
)
from .preflight import PreflightError, PreflightReceipt, preflight_run
from .performance_readiness import validate_performance_readiness_receipt
from .production import PipelineOutcome, execute_full_pipeline
from .frontier import (
    RESOURCE_SCHEMA, FrontierController, TechnicalSliceStop, technical_frontier_value,
)
from .resources import (
    ContinuousResourceMonitor, MeasurementIncident, ResourceLimits, ResourceTelemetry,
    foreground_io_snapshot, tree_bytes,
)


class ResultExecutionDisabled(RuntimeError):
    pass


A_PILOT_PERFORMANCE_DISPOSITION = "PILOT_ONLY"
A_RECON_PERFORMANCE_DISPOSITION = "REVIEW_REQUIRED"
RUN_01_PERFORMANCE_DISPOSITION = "REPAIR_REQUIRED"
RUN_CONFIRMATION = NAMED_RUN_ID


def _validate_new_result_root(result_root: str | Path) -> Path:
    try:
        root = canonical_result_root(result_root)
    except AttemptError as error:
        raise PreflightError(str(error)) from error
    if _optional_direct_regular_bytes(
        root / "published-result.json", label="published result",
    ) is not None:
        raise ResultExecutionDisabled("published RUN-01 is immutable")
    normalized = str(root).replace("\\", "/").lower()
    if "foundation_conditioned_event_order_value" in normalized or "2026-08-31." in normalized:
        raise PreflightError("old FCEOV .1/.2/.3 result coordinates are isolated")
    if root.exists():
        raise PreflightError("prospective B01 result root must not exist during preflight")
    return root


def _new_scientific_size_source() -> Callable[[Path, Path], tuple[int, int]]:
    """Allow precreation zero once, then fail if an observed durable root disappears."""

    durable_observed = False

    def measure(scratch: Path, durable: Path) -> tuple[int, int]:
        nonlocal durable_observed
        scratch_bytes = tree_bytes(scratch)
        if durable.exists():
            durable_observed = True
            return scratch_bytes, tree_bytes(durable)
        if durable_observed:
            raise OSError("observed canonical durable root disappeared")
        return scratch_bytes, 0

    return measure


def preflight_only(
    *, receipt: str | Path, result_root: str | Path,
    command_runner: Callable[..., object],
) -> PreflightReceipt:
    _validate_new_result_root(result_root)
    return preflight_run(receipt, command_runner=command_runner)


def _load_telemetry(path: Path) -> ResourceTelemetry:
    try:
        value = json.loads(_read_regular_bytes(path, label="prior resource telemetry"))
        if isinstance(value, dict) and isinstance(value.get("invocation_telemetry"), dict):
            value = value["invocation_telemetry"]
        raw_incidents = value.get("measurement_incidents", [])
        if not isinstance(raw_incidents, list):
            raise TypeError("measurement incidents are not a canonical list")
        result = ResourceTelemetry(**{
            **value, "failure_reasons": tuple(value.get("failure_reasons", ())),
            "measurement_incidents": tuple(MeasurementIncident(**row) for row in raw_incidents),
        })
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError) as error:
        raise AttemptError("prior invocation telemetry is unreadable") from error
    if not result.passed or result.failure_reasons or result.exit_status != 0:
        raise AttemptError("prior invocation telemetry did not pass")
    return result


def _prior_telemetry(attempt: Attempt) -> tuple[ResourceTelemetry, ...]:
    directory = attempt.root / "resources"
    paths = tuple(sorted(directory.glob("invocation-*.json"))) if _direct_directory_exists(directory) else ()
    expected = tuple(directory / f"invocation-{index:06d}.json" for index in range(attempt.invocation_index))
    if paths != expected:
        raise AttemptError("technical resume lacks a contiguous prior telemetry record")
    return tuple(_load_telemetry(path) for path in paths)


def _aggregate_telemetry(rows: Sequence[ResourceTelemetry]) -> dict[str, object]:
    values = tuple(rows)
    if not values:
        raise AttemptError("result publication lacks invocation telemetry")
    wall = sum(row.wall_seconds for row in values)
    aggregate: dict[str, object] = {
        "invocations": len(values),
        "sample_count": sum(row.sample_count for row in values),
        "process_tree_peak_rss_bytes": max(row.process_tree_peak_rss_bytes for row in values),
        "scratch_high_water_bytes": max(row.scratch_high_water_bytes for row in values),
        "durable_high_water_bytes": max(row.durable_high_water_bytes for row in values),
        "wall_seconds": wall,
        "cpu_seconds": sum(row.cpu_seconds for row in values),
        "cpu_utilization_fraction": sum(row.cpu_seconds for row in values) / wall if wall > 0 else 0.0,
        "max_process_count": max(row.max_process_count for row in values),
        "max_thread_count": max(row.max_thread_count for row in values),
        "start_available_memory_bytes": values[0].start_available_memory_bytes,
        "end_available_memory_bytes": values[-1].end_available_memory_bytes,
        "foreground_io_read_bytes": sum(row.foreground_io_read_bytes for row in values),
        "foreground_io_write_bytes": sum(row.foreground_io_write_bytes for row in values),
        "process_tree_io_read_bytes": sum(row.process_tree_io_read_bytes for row in values),
        "process_tree_io_write_bytes": sum(row.process_tree_io_write_bytes for row in values),
        "observed_torch_intraop_threads": [row.torch_intraop_threads for row in values],
        "observed_torch_interop_threads": [row.torch_interop_threads for row in values],
        "observed_os_cpu_count": [row.os_cpu_count for row in values],
        "native_internal_worker_threads": [row.native_internal_worker_threads for row in values],
        "measurement_incidents": [
            asdict(incident) for row in values for incident in row.measurement_incidents
        ],
    }
    reasons = []
    if any(not row.passed for row in values): reasons.append("invocation_telemetry_failed")
    if int(aggregate["process_tree_peak_rss_bytes"]) > RESOURCE_CAPS["peak_rss_bytes"]:
        reasons.append("process_tree_peak_rss_exceeded")
    if int(aggregate["scratch_high_water_bytes"]) > RESOURCE_CAPS["scratch_bytes"]:
        reasons.append("scratch_high_water_exceeded")
    if int(aggregate["durable_high_water_bytes"]) > RESOURCE_CAPS["durable_bytes"]:
        reasons.append("durable_output_exceeded")
    if wall > RESOURCE_CAPS["wall_seconds"]: reasons.append("cumulative_wall_time_exceeded")
    aggregate["passed"] = not reasons
    aggregate["failure_reasons"] = reasons
    return aggregate


def _artifact_inventory(root: Path, outcome: PipelineOutcome, run_manifest) -> list[dict[str, object]]:
    completed, _history = _validate_resume_history(root)
    required = [root / "attempt-header.json", root / "manifest.json", root / "run-master.bin",
                root / "realized-q-audit.json",
                root / "source-identity.json",
                root / "foundation-competence-gate.json"]
    required += [root / "foundations" / str(seed) / "checkpoints" / f"update-{update:03d}.json"
                 for seed in (1709, 2903) for update in range(161)]
    required += [root / "foundations" / str(seed) / "curves" / f"update-{update:03d}.json"
                 for seed in (1709, 2903) for update in range(0, 161, 20)]
    required += [root / "foundations" / str(seed) / "competence.json" for seed in (1709, 2903)]
    required += [
        root / directory / f"invocation-{index:06d}.json"
        for directory in ("admissions", "invocations")
        for index in range(completed)
    ]
    if _direct_regular_exists(root / "technical-frontier.json"):
        required.append(root / "technical-frontier.json")
    validation_dir = root / "resume-validation"
    if _direct_directory_exists(validation_dir):
        required += list(sorted(validation_dir.glob("invocation-*.json")))
    if outcome.branch != "FOUNDATION_COMPETENCE_NOT_ESTABLISHED":
        source_dir = root / "source-states"
        if not _direct_directory_exists(source_dir):
            raise AttemptError("source scan artifact directory is missing")
        sources = tuple(source_dir.glob("k*.json")) + tuple(source_dir.glob("*-not-established.json"))
        if not sources: raise AttemptError("source scan artifact inventory is empty")
        required += list(sources)
    if outcome.branch not in {"FOUNDATION_COMPETENCE_NOT_ESTABLISHED", "REACHABLE_STATE_PANEL_NOT_ESTABLISHED"}:
        required.append(root / "development-action-map.json")
        required += [root / "development" / str(seed) / f"{state}.json"
                     for seed in (1709, 2903)
                     for state in ("k7-early", "k7-middle", "k7-late", "k13-early", "k13-middle", "k13-late")]
    if outcome.complete_full_chain:
        required.append(root / "heldout-analysis.json")
        required += [root / "heldout" / str(seed) / f"{state}.json"
                     for seed in (1709, 2903)
                     for state in ("k7-early", "k7-middle", "k7-late", "k13-early", "k13-middle", "k13-late")]
    direct_by_path = {}
    for path in required:
        try:
            direct_by_path[path] = _read_regular_bytes(path, label="required publication artifact")
        except AttemptError as error:
            raise AttemptError(f"required publication artifact is invalid: {path.name}") from error
    # Cold, streamed validation of every one of the 322 checkpoints.  This
    # validates full run/source binding, parameter tensors, Adam moments and
    # update frontier instead of trusting receipt-only summaries.
    for seed in (1709, 2903):
        for update in range(161):
            path = root / "foundations" / str(seed) / "checkpoints" / f"update-{update:03d}.json"
            model, optimizer = load_foundation_checkpoint(
                path, expected_seed=seed, run_manifest=run_manifest,
            )
            if optimizer.step_index != update * 12 or model.foundation_seed != seed:
                raise AttemptError("cold checkpoint frontier validation differs")
            receipt = load_checkpoint_training_receipt(path)
            if (update == 0) != (receipt is None):
                raise AttemptError("cold checkpoint training receipt frontier differs")
    unique = tuple(sorted(set(required), key=str))
    result = []
    for path in unique:
        direct = direct_by_path[path]
        result.append({
            "relative_path": path.relative_to(root).as_posix(),
            "direct_size_bytes": len(direct),
            "sha256": hashlib.sha256(direct).hexdigest(),
        })
    return result


def _direct_regular_exists(path: Path) -> bool:
    try:
        observed = os.lstat(path)
    except FileNotFoundError:
        return False
    attributes = int(getattr(observed, "st_file_attributes", 0))
    if stat.S_ISLNK(observed.st_mode) or attributes & 0x400:
        raise AttemptError("publication artifact coordinate is a symlink, junction, or reparse point")
    return stat.S_ISREG(observed.st_mode)


def _optional_direct_regular_bytes(path: Path, *, label: str) -> bytes | None:
    """Return exact opened bytes, or None when the lexical leaf is absent."""

    try:
        observed = os.lstat(path)
    except FileNotFoundError:
        return None
    attributes = int(getattr(observed, "st_file_attributes", 0))
    if (
        stat.S_ISLNK(observed.st_mode)
        or attributes & 0x400
        or not stat.S_ISREG(observed.st_mode)
    ):
        raise AttemptError(f"{label} is a symlink, junction, reparse point, or nonregular file")
    return _read_regular_bytes(path, label=label)


def _direct_directory_exists(path: Path) -> bool:
    try:
        observed = os.lstat(path)
    except FileNotFoundError:
        return False
    attributes = int(getattr(observed, "st_file_attributes", 0))
    if stat.S_ISLNK(observed.st_mode) or attributes & 0x400:
        raise AttemptError("publication directory is a symlink, junction, or reparse point")
    if not stat.S_ISDIR(observed.st_mode):
        raise AttemptError("publication directory coordinate is not a directory")
    return True


def _publish_or_validate(path: Path, value: dict[str, object]) -> None:
    encoded = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    existing = _optional_direct_regular_bytes(path, label="partial publication artifact")
    if existing is not None:
        if existing != encoded: raise AttemptError(f"partial publication differs: {path.name}")
    else:
        atomic_create_json(path, value)


def _canonical_bytes(value: dict[str, object]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _tree_bytes(path: Path) -> int:
    return tree_bytes(path)


@dataclass(frozen=True, slots=True)
class PublicationTailPlan:
    payloads: tuple[tuple[str, bytes], ...]
    prepublication_durable_bytes: int
    exact_tail_bytes: int
    new_tail_bytes: int
    predicted_final_durable_bytes: int
    preview_io_read_bytes: int
    preview_io_write_bytes: int
    sealed_identity_inventory: tuple[dict[str, object], ...]


@dataclass(frozen=True, slots=True)
class TechnicalSliceTailPlan:
    resource_relative_path: str
    resource_bytes: bytes
    frontier_bytes: bytes
    prepublication_durable_bytes: int
    predicted_final_durable_bytes: int
    sealed_identity_inventory: tuple[dict[str, object], ...]


def _validate_tail_capacity(prepublication_bytes: int, new_tail_bytes: int) -> int:
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in (prepublication_bytes, new_tail_bytes)
    ):
        raise AttemptError("publication capacity inputs differ")
    predicted = prepublication_bytes + new_tail_bytes
    if predicted > RESOURCE_CAPS["durable_bytes"]:
        raise AttemptError("predicted final durable output exceeds 256 MiB before publication")
    return predicted


def _build_technical_slice_tail_plan(
    *, attempt: Attempt, stopped: TechnicalSliceStop, telemetry: ResourceTelemetry,
    prepublication_durable_bytes: int,
) -> TechnicalSliceTailPlan:
    sealed_identity = validate_sealed_identity(attempt)
    relative = f"resources/invocation-{attempt.invocation_index:06d}.json"
    accounting: dict[str, object] = {}
    resource_bytes = b""
    frontier_bytes = b""
    for _ in range(12):
        frontier = technical_frontier_value(
            attempt, stopped=stopped, telemetry_relative_path=relative,
            tail_accounting=accounting,
        )
        resource = {
            "schema": RESOURCE_SCHEMA,
            "run_binding": attempt.run_manifest.to_dict(),
            "invocation_index": attempt.invocation_index,
            "source_identity_sha256": frontier["source_identity_sha256"],
            "sealed_identity_inventory": list(sealed_identity),
            "frontier_id": stopped.frontier_id,
            "frontier_index": stopped.frontier_index,
            "invocation_telemetry": asdict(telemetry),
            "tail_accounting": accounting,
            "scientific_polarity": None,
            "ordered_branch": None,
        }
        resource_bytes = _canonical_bytes(resource)
        frontier_bytes = _canonical_bytes(frontier)
        next_accounting = {
            "prepublication_durable_bytes": prepublication_durable_bytes,
            "resource_exact_bytes": len(resource_bytes),
            "frontier_exact_bytes": len(frontier_bytes),
            "exact_tail_bytes": len(resource_bytes) + len(frontier_bytes),
            "predicted_final_durable_bytes": (
                prepublication_durable_bytes + len(resource_bytes) + len(frontier_bytes)
            ),
            "durable_cap_bytes": RESOURCE_CAPS["durable_bytes"],
        }
        if next_accounting == accounting:
            break
        accounting = next_accounting
    else:
        raise AttemptError("technical slice tail byte-accounting fixed point did not converge")
    predicted = prepublication_durable_bytes + len(resource_bytes) + len(frontier_bytes)
    _validate_tail_capacity(prepublication_durable_bytes, predicted - prepublication_durable_bytes)
    if predicted != accounting.get("predicted_final_durable_bytes"):
        raise AttemptError("technical slice tail byte accounting differs")
    return TechnicalSliceTailPlan(
        relative, resource_bytes, frontier_bytes, prepublication_durable_bytes, predicted,
        sealed_identity,
    )


def _stage_and_commit_technical_slice_tail(
    plan: TechnicalSliceTailPlan,
    *, attempt: Attempt, scratch: Path, active_gate: ActiveInvocationGate,
    final_committer: Callable[[Path, Path], None] = os.rename,
) -> Path:
    staged = scratch / "technical-slice-tail"
    staged.mkdir(exist_ok=False)
    staged_resource = staged / "resource.json"
    staged_frontier = staged / "technical-frontier.json"
    atomic_create_bytes(staged_resource, plan.resource_bytes)
    atomic_create_bytes(staged_frontier, plan.frontier_bytes)
    if (
        staged_resource.read_bytes() != plan.resource_bytes
        or staged_frontier.read_bytes() != plan.frontier_bytes
        or _tree_bytes(scratch) > RESOURCE_CAPS["scratch_bytes"]
    ):
        raise AttemptError("technical slice staged tail bytes or scratch cap differ")
    resource_path = attempt.root / plan.resource_relative_path
    frontier_path = attempt.root / "technical-frontier.json"
    if (
        _optional_direct_regular_bytes(resource_path, label="technical resource tail") is not None
        or _optional_direct_regular_bytes(frontier_path, label="technical frontier tail") is not None
    ):
        raise AttemptError("technical slice tail coordinate is not create-once")
    if _tree_bytes(attempt.root) != plan.prepublication_durable_bytes:
        raise AttemptError("technical slice prepublication durable bytes changed")
    active_gate.assert_owner()
    if (
        (attempt.root / "terminal-no-polarity.json").exists()
        or validate_quarantine_lock(attempt.root, mode="RUN-01")
    ):
        raise AttemptError("terminal/quarantine state forbids technical frontier commit")
    resource_path.parent.mkdir(parents=True, exist_ok=True)
    os.rename(staged_resource, resource_path)
    if (
        _optional_direct_regular_bytes(
            resource_path, label="technical resource committed readback",
        ) != plan.resource_bytes
        or _tree_bytes(attempt.root) + len(plan.frontier_bytes) != plan.predicted_final_durable_bytes
    ):
        raise AttemptError("technical slice resource or direct durable accounting differs")
    active_gate.assert_owner()
    active_gate.retain_until_process_exit()
    if validate_sealed_identity(attempt) != plan.sealed_identity_inventory:
        raise AttemptError("sealed identity changed after technical tail staging")
    # Unique final commit: successful rename is followed only by immediate
    # return.  No cleanup, readback, lease release, or finally action follows.
    final_committer(staged_frontier, frontier_path)
    return frontier_path


def _build_tail_plan(
    *,
    attempt: Attempt,
    outcome: PipelineOutcome,
    telemetry: ResourceTelemetry,
    aggregate: dict[str, object],
    inventory: list[dict[str, object]],
    prepublication_durable_bytes: int,
    preview_io_read_bytes: int,
    preview_io_write_bytes: int,
    active_gate_binding: dict[str, object],
) -> PublicationTailPlan:
    sealed_identity = validate_sealed_identity(attempt)
    ledger, branch, published = _publication_values(
        attempt, outcome, aggregate, inventory, sealed_identity=sealed_identity,
    )
    for value in (ledger, branch, published):
        value["active_invocation_gate"] = active_gate_binding
    branch["status"] = "PREPARED_NOT_PUBLISHED"
    branch["branch_candidate"] = branch.pop("ordered_branch")
    branch["scientific_polarity"] = None
    accounting: dict[str, object] = {}
    payloads: tuple[tuple[str, bytes], ...] = ()
    for _ in range(12):
        resource = {
            "schema": "SCDMP_MF_RS_MK_B01_INVOCATION_RESOURCE_V1",
            "invocation_telemetry": asdict(telemetry),
            "aggregate_telemetry": aggregate,
            "publication_accounting": accounting,
        }
        published["publication_accounting"] = accounting
        candidate = (
            (f"resources/invocation-{attempt.invocation_index:06d}.json", _canonical_bytes(resource)),
            ("work-ledger.json", _canonical_bytes(ledger)),
            ("ordered-branch.json", _canonical_bytes(branch)),
            ("published-result.json", _canonical_bytes(published)),
        )
        exact = sum(len(encoded) for _name, encoded in candidate)
        new = sum(
            len(encoded) for name, encoded in candidate
            if _optional_direct_regular_bytes(
                attempt.root / name, label="publication tail planning artifact",
            ) is None
        )
        next_accounting = {
            "prepublication_durable_bytes": prepublication_durable_bytes,
            "exact_logical_tail_bytes": exact,
            "new_tail_write_bytes": new,
            "predicted_final_durable_bytes": prepublication_durable_bytes + new,
            "durable_cap_bytes": RESOURCE_CAPS["durable_bytes"],
            "preview_io_read_bytes": preview_io_read_bytes,
            "preview_io_write_bytes": preview_io_write_bytes,
            "preview_is_exact_publication_shape": True,
        }
        payloads = candidate
        if next_accounting == accounting:
            break
        accounting = next_accounting
    else:
        raise AttemptError("publication tail byte-accounting fixed point did not converge")
    predicted = prepublication_durable_bytes + sum(
        len(encoded) for name, encoded in payloads
        if _optional_direct_regular_bytes(
            attempt.root / name, label="publication tail prediction artifact",
        ) is None
    )
    _validate_tail_capacity(prepublication_durable_bytes, predicted - prepublication_durable_bytes)
    return PublicationTailPlan(
        payloads, prepublication_durable_bytes, sum(len(row[1]) for row in payloads),
        predicted - prepublication_durable_bytes, predicted,
        preview_io_read_bytes, preview_io_write_bytes, sealed_identity,
    )


def _stage_and_publish_tail(
    plan: PublicationTailPlan,
    *,
    attempt: Attempt,
    scratch: Path,
    writer: Callable[[Path, bytes], None] = atomic_create_bytes,
    final_committer: Callable[[Path, Path], None] = os.rename,
) -> Path:
    root = attempt.root
    staged = scratch / "publication-tail"
    staged.mkdir(exist_ok=False)
    for name, encoded in plan.payloads:
        stage_path = staged / name.replace("/", "__")
        atomic_create_bytes(stage_path, encoded)
        if stage_path.read_bytes() != encoded:
            raise AttemptError("staged publication tail bytes differ")
    if _tree_bytes(scratch) > RESOURCE_CAPS["scratch_bytes"]:
        raise AttemptError("publication tail staging exceeds scratch cap")
    # Publish polarity last. Every preceding direct-byte mismatch therefore
    # fails while no scientific result is published.
    for name, encoded in plan.payloads[:-1]:
        path = root / name
        existing = _optional_direct_regular_bytes(path, label="publication tail existing artifact")
        if existing is not None:
            if existing != encoded:
                raise AttemptError("publication tail existing bytes differ")
        else:
            writer(path, encoded)
        if _optional_direct_regular_bytes(
            path, label="publication tail committed readback",
        ) != encoded:
            raise AttemptError("publication tail direct size/bytes mismatch before polarity")
    published_name, published_bytes = plan.payloads[-1]
    published_path = root / published_name
    staged_published_path = staged / published_name.replace("/", "__")
    if _optional_direct_regular_bytes(
        published_path, label="published result commit coordinate",
    ) is not None:
        raise AttemptError("published result commit already exists")
    direct_prefinal = _tree_bytes(root)
    if direct_prefinal + len(published_bytes) > RESOURCE_CAPS["durable_bytes"]:
        raise AttemptError("direct pre-polarity durable check exceeds cap")
    if direct_prefinal + len(published_bytes) != plan.predicted_final_durable_bytes:
        raise AttemptError("prefinal durable size differs from exact publication prediction")
    # This same-volume create-only rename is the transaction commit point.  The
    # staged file has already been fsynced, read back, sized, and accounted.
    # No cleanup (including temp unlink), read, lease mutation, assertion, or
    # other fallible operation may follow a successful rename.
    if validate_sealed_identity(attempt) != plan.sealed_identity_inventory:
        raise AttemptError("sealed identity changed after publication tail staging")
    final_committer(staged_published_path, published_path)
    return published_path


def _publication_values(
    attempt: Attempt, outcome: PipelineOutcome, aggregate: dict[str, object],
    inventory: list[dict[str, object]],
    *, sealed_identity: tuple[dict[str, object], ...] | None = None,
):
    if sealed_identity is None:
        sealed_identity = validate_sealed_identity(attempt)
    reconciliation = outcome.ledger.reconcile_for_branch(
        branch=outcome.branch, source_states=outcome.source_states, ppo_updates=outcome.ppo_updates,
    )
    ledger = {"schema": "SCDMP_MF_RS_MK_B01_WORK_LEDGER_V1", "run_binding": attempt.run_manifest.to_dict(),
              "branch": outcome.branch, "rows": [{"stage": stage, **asdict(row)} for stage, row in outcome.ledger.rows],
              "reconciliation": reconciliation}
    branch = {"schema": "SCDMP_MF_RS_MK_B01_ORDERED_BRANCH_V1", "run_binding": attempt.run_manifest.to_dict(),
              "ordered_branch": outcome.branch,
              "scientific_polarity": outcome.branch if outcome.complete_full_chain else None,
              "early_stop_no_order_value_polarity": not outcome.complete_full_chain}
    published = {"schema": "SCDMP_MF_RS_MK_B01_PUBLISHED_RESULT_V1", "run_binding": attempt.run_manifest.to_dict(),
                 "resolved_result_root": str(attempt.root), "ordered_branch": outcome.branch,
                 "scientific_polarity": outcome.branch if outcome.complete_full_chain else None,
                 "complete_full_chain": outcome.complete_full_chain, "work_ledger_file": "work-ledger.json",
                 "ordered_branch_file": "ordered-branch.json", "resource_telemetry": aggregate,
                 "artifact_inventory_scope": "complete_prepublication_scientific_and_engineering_inputs",
                 "artifact_inventory": inventory,
                 "sealed_identity_inventory": list(sealed_identity),
                 "excluded_transaction_tail_artifacts": [
                     "resources/invocation-NNNNNN.json", "work-ledger.json",
                     "ordered-branch.json", "published-result.json",
                 ],
                 "technical_resume_artifacts_in_inventory": [
                     "technical-frontier.json", "resume-validation/invocation-NNNNNN.json",
                 ]}
    return ledger, branch, published


def run_result(
    *, result_root: str | Path, admission_receipt: str | Path | None = None,
    confirmation: str | None = None, resume: bool = False, argv: Sequence[str] = (),
    cwd: str | Path | None = None, command_runner: Callable[..., object] = subprocess.run,
    monitor_factory: Callable[..., ContinuousResourceMonitor] = ContinuousResourceMonitor,
    stop_after_frontier: str | None = None,
    performance_readiness: str | Path | None = None,
) -> Path:
    root = canonical_result_root(result_root)
    if confirmation != RUN_CONFIRMATION or admission_receipt is None or cwd is None or not argv:
        raise ResultExecutionDisabled(
            f"RUN-01 requires explicit --confirm-run-id {RUN_CONFIRMATION}, receipt, cwd, and argv"
        )
    if performance_readiness is None:
        raise ResultExecutionDisabled("RUN-01 performance readiness receipt is required")
    try:
        validate_performance_readiness_receipt(performance_readiness)
    except Exception as error:
        raise ResultExecutionDisabled("RUN-01 performance readiness receipt is invalid") from error
    scratch = root.with_name(f".{root.name}.scratch-{Path(admission_receipt).stem}")
    monitor: ContinuousResourceMonitor | None = None
    attempt: Attempt | None = None
    telemetry: ResourceTelemetry | None = None
    active_gate = ActiveInvocationGate(root, mode="RUN-01")
    active_gate.acquire()
    try:
        if resume and (
            (root / "terminal-no-polarity.json").exists()
            or validate_quarantine_lock(root, mode="RUN-01")
        ):
            raise AttemptError("quarantined replacement attempt cannot be resumed")
        if resume:
            next_index, _history = _validate_resume_history(root)
            expected_receipt = root / "admissions" / f"invocation-{next_index:06d}.json"
            requested_receipt = Path(os.path.abspath(os.fspath(admission_receipt)))
            if requested_receipt != expected_receipt:
                raise AttemptError("resume admission receipt is not the verified next history slot")
        if scratch.exists():
            raise AttemptError("invocation scratch coordinate already exists")
        admission = preflight_run(admission_receipt, command_runner=command_runner)
        scratch.mkdir(exist_ok=False)
        monitor = monitor_factory(
            scratch_root=scratch, durable_root=root, limits=ResourceLimits(),
            size_source=_new_scientific_size_source(), autostart=False,
        )
        monitor.sample_now()
        telemetry_witness = _issue_initial_telemetry_witness(monitor)
        monitor.start()
        attempt = _initialize_or_resume_attempt(
            result_root=root, admission_receipt=admission_receipt, admission=admission,
            argv=argv, cwd=cwd, resume=resume, telemetry_witness=telemetry_witness,
        )
        prior = _prior_telemetry(attempt)
        frontier_controller = FrontierController(attempt, stop_after=stop_after_frontier)
        torch.set_num_threads(1)
        try:
            outcome = execute_full_pipeline(
                attempt, scratch_observer=monitor.observe_scratch_path,
                frontier_controller=frontier_controller,
            )
        except TechnicalSliceStop as stopped:
            telemetry = monitor.finalize(exit_status=0)
            if not telemetry.passed:
                raise AttemptError("technical slice resource telemetry did not pass")
            slice_plan = _build_technical_slice_tail_plan(
                attempt=attempt, stopped=stopped, telemetry=telemetry,
                prepublication_durable_bytes=_tree_bytes(attempt.root),
            )
            return _stage_and_commit_technical_slice_tail(
                slice_plan, attempt=attempt, scratch=scratch, active_gate=active_gate,
            )
        inventory = _artifact_inventory(attempt.root, outcome, attempt.run_manifest)
        atomic_create_json(
            scratch / "publication-preview.json",
            {"schema": "SCDMP_MF_RS_MK_B01_PUBLICATION_PREVIEW_V1", "branch": outcome.branch,
             "ledger_rows": len(outcome.ledger.rows)}, scratch_observer=monitor.observe_scratch_path,
        )
        telemetry = monitor.finalize(exit_status=0)
        aggregate = _aggregate_telemetry((*prior, telemetry))
        if not telemetry.passed or aggregate.get("passed") is not True:
            raise AttemptError("RUN-01 measured resource contract did not pass")
        prepublication_durable = _tree_bytes(attempt.root)
        probe_ledger, probe_branch, probe_published = _publication_values(
            attempt, outcome, aggregate, inventory,
        )
        probe_bytes = b"".join((
            _canonical_bytes({"telemetry": asdict(telemetry), "aggregate": aggregate}),
            _canonical_bytes(probe_ledger), _canonical_bytes(probe_branch),
            _canonical_bytes(probe_published),
        ))
        io_before = foreground_io_snapshot()
        atomic_create_bytes(scratch / "publication-tail-io-probe.bin", probe_bytes)
        io_after = foreground_io_snapshot()
        preview_read = max(
            0, io_after["foreground_io_read_bytes"] - io_before["foreground_io_read_bytes"],
        )
        preview_write = max(
            0, io_after["foreground_io_write_bytes"] - io_before["foreground_io_write_bytes"],
        )
        plan = _build_tail_plan(
            attempt=attempt, outcome=outcome, telemetry=telemetry, aggregate=aggregate,
            inventory=inventory, prepublication_durable_bytes=prepublication_durable,
            preview_io_read_bytes=preview_read, preview_io_write_bytes=preview_write,
            active_gate_binding=active_gate.binding(),
        )
        active_gate.assert_owner()
        if (
            (attempt.root / "terminal-no-polarity.json").exists()
            or validate_quarantine_lock(attempt.root, mode="RUN-01")
        ):
            raise AttemptError("terminal/quarantine state forbids result publication")
        active_gate.retain_until_process_exit()
        return _stage_and_publish_tail(plan, attempt=attempt, scratch=scratch)
    except BaseException as error:
        if telemetry is None and monitor is not None:
            telemetry = monitor.finalize(exit_status=1)
        if root.is_dir():
            quarantine = root
        else:
            # Admission/telemetry failure before the canonical root remains retryable.
            if monitor is not None:
                monitor.stop()
            try:
                scratch.rmdir()
            except OSError:
                pass
            try:
                active_gate.release()
            except BaseException as gate_error:
                setattr(error, "active_gate_release_error", gate_error)
            raise
        try:
            try:
                active_binding = active_gate.binding()
            except BaseException as gate_error:
                setattr(error, "active_gate_ownership_error", gate_error)
                active_binding = None
            raise_after_quarantine(quarantine, mode="RUN-01", stage="production-or-publication",
                                   original=error, telemetry=telemetry,
                                   active_gate_binding=active_binding)
        finally:
            try:
                if validate_quarantine_lock(quarantine, mode="RUN-01"):
                    active_gate.release()
            except BaseException as gate_error:
                setattr(error, "active_gate_release_error", gate_error)


__all__ = ["A_PILOT_PERFORMANCE_DISPOSITION", "A_RECON_PERFORMANCE_DISPOSITION",
           "RUN_01_PERFORMANCE_DISPOSITION", "RUN_CONFIRMATION", "ResultExecutionDisabled",
           "preflight_only", "run_assess", "run_result"]

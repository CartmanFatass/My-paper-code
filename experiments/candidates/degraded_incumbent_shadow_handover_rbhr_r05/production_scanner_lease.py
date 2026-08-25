"""Fail-closed conditional scanner-only lease for DISH RBHR r05.

Importing and validating this module is preactivity-safe.  A scientific master,
identity, coordinate, and accepted-tape frontier can be materialized only by
``run_scanner`` after an exact active Operational-Root lease is validated.
The scanner receipt exposes counters, resource projections, and digests only;
winning attempts and candidate classifications remain in the sealed run root.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import time
from typing import Mapping, Sequence

from .production_backend import scan_production_candidate_attempts
from .production_contract import (
    COMPONENT,
    EVALUATION_SCHEDULES,
    PACKAGES,
    SCIENCE_REVISION,
    STRATA,
)
from .production_preactivity import process_io_bytes, process_memory_bytes
from .production_tapes import AcceptedTapeCoordinate, complete_accepted_tape_coordinates


REQUEST_SCHEMA = "DISH_RBHR_R05_CONDITIONAL_SCANNER_LEASE_REQUEST_V1"
LEASE_SCHEMA = "DISH_RBHR_R05_CONDITIONAL_SCANNER_ROOT_LEASE_V1"
STATE_SCHEMA = "DISH_RBHR_R05_SEALED_SCANNER_STATE_V1"
RECEIPT_SCHEMA = "DISH_RBHR_R05_CONDITIONAL_SCANNER_RECEIPT_V1"
LEASE_KIND = "CONDITIONAL_GUARDED_SCANNER_ONLY"
LEASE_ID = "DISH-RBHR-R05-CONDITIONAL-SCANNER-20260822-01"
EXPECTED_COORDINATES = 11_520
ATTEMPT_CAP = 100_000
REJECTION_HALT_BEFORE = 10_451_148
MAX_REJECTIONS = REJECTION_HALT_BEFORE - 1
GIB = 1024.0 ** 3

GATES = {
    "cpu_core_hours": 560.0,
    "wall_hours": 110.0,
    "aggregate_rss_gib": 40.0,
    "scratch_gib": 120.0,
    "durable_gib": 16.0,
    "total_io_gib": 400.0,
}
BASE = {
    "cpu_core_hours": 278.447917844373,
    "wall_hours": 44.7681636558252,
    "aggregate_rss_gib": 2.57534790039062,
    "scratch_gib": 0.663042068481445,
    "durable_gib": 0.330453045666218,
    "total_io_gib": 34.0669612884521,
}
SECONDS_PER_REJECTED_ATTEMPT = 0.09698337291774806
MEASURED_EIGHT_WORKER_SPEEDUP = 6.219775284621071

PROHIBITED = (
    "MODEL", "OPTIMIZER", "CHECKPOINT", "TRAINING", "EVALUATION", "FORK",
    "BOOTSTRAP", "BRANCH", "RESULT", "PARTIAL_VALUE_EXPOSURE", "FULL_PANEL",
    "SECOND_OR_REPLACEMENT_IDENTITY",
)

PACKAGE_INDEX = {name: index for index, name in enumerate(PACKAGES)}
SCHEDULE_INDEX = {name: index for index, name in enumerate(EVALUATION_SCHEDULES)}
SPLIT_INDEX = {"CLAIM": 1, "CALIBRATION": 2}
STRATUM_VALUE = {"POSITIVE": 1, "NEAR_ZERO": 0, "NEGATIVE": -1}


class ScannerLeaseError(RuntimeError):
    pass


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")


def _read_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ScannerLeaseError(f"invalid JSON artifact: {path}") from error
    if not isinstance(value, dict):
        raise ScannerLeaseError(f"JSON artifact is not an object: {path}")
    return value


def _write_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    data = _canonical_bytes(value)
    with temporary.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def validate_request(request: Mapping[str, object], *, repository_root: Path) -> None:
    expected = {
        "schema": REQUEST_SCHEMA,
        "lease_id": LEASE_ID,
        "direction_id": "degraded_incumbent_shadow_handover",
        "object_revision": SCIENCE_REVISION,
        "component": COMPONENT,
        "lease_kind": LEASE_KIND,
        "issuer_required": "OPERATIONAL_ROOT",
        "master_count": 1,
        "identity_count": 1,
        "coordinate_count": 1,
        "accepted_tape_slots": EXPECTED_COORDINATES,
        "attempt_cap_per_slot": ATTEMPT_CAP,
        "rejection_guard": "HALT_BEFORE_CUMULATIVE_REJECTION_10451148",
        "gates": GATES,
        "prohibited": list(PROHIBITED),
        "full_panel_execution_authorized": False,
        "partial_values_authorized": False,
        "second_or_replacement_identity_authorized": False,
        "benchmark_path": "runtime/benchmarks/dish_rbhr_r05_production_preactivity_final_boundary_20260822.json",
        "benchmark_sha256": "a7be029df48dfd2fd295c2efa75d013fb09157b5c40160c70a5caa5b9811d2ff",
        "lease_path": "runtime/leases/dish_rbhr_r05_conditional_scanner_lease_20260822.json",
        "run_root": "runtime/scanner/dish_rbhr_r05_conditional_scanner_20260822_01",
    }
    for key, value in expected.items():
        if request.get(key) != value:
            raise ScannerLeaseError(f"conditional scanner request field differs: {key}")
    manifest = request.get("source_manifest")
    if not isinstance(manifest, dict) or not manifest:
        raise ScannerLeaseError("conditional scanner request source manifest is absent")
    for relative, expected_digest in manifest.items():
        if not isinstance(relative, str) or not isinstance(expected_digest, str):
            raise ScannerLeaseError("conditional scanner source manifest schema differs")
        path = repository_root / relative
        if not path.is_file() or _sha256_bytes(path.read_bytes()) != expected_digest:
            raise ScannerLeaseError(f"conditional scanner source differs: {relative}")


@dataclass(frozen=True)
class ScannerLeaseBinding:
    repository_root: Path
    request_path: Path
    lease_path: Path
    request: Mapping[str, object]
    lease: Mapping[str, object]
    request_sha256: str
    lease_sha256: str
    run_root: Path
    master: bytes | None = None
    identity_sha256: str | None = None

    @classmethod
    def load(cls, *, repository_root: Path, request_path: Path, lease_path: Path) -> "ScannerLeaseBinding":
        request = _read_json(request_path)
        validate_request(request, repository_root=repository_root)
        request_sha = _sha256_bytes(request_path.read_bytes())
        lease = _read_json(lease_path)
        required = {
            "schema": LEASE_SCHEMA,
            "lease_id": LEASE_ID,
            "status": "ACTIVE",
            "issuer": "OPERATIONAL_ROOT",
            "direction_id": "degraded_incumbent_shadow_handover",
            "object_revision": SCIENCE_REVISION,
            "component": COMPONENT,
            "lease_kind": LEASE_KIND,
            "request_sha256": request_sha,
            "gates": GATES,
            "rejection_halt_before": REJECTION_HALT_BEFORE,
            "master_count": 1,
            "identity_count": 1,
            "coordinate_count": 1,
            "accepted_tape_slots": EXPECTED_COORDINATES,
            "full_panel_execution_authorized": False,
            "partial_values_authorized": False,
            "second_or_replacement_identity_authorized": False,
            "prohibited": list(PROHIBITED),
            "run_root": request["run_root"],
        }
        for key, value in required.items():
            if lease.get(key) != value:
                raise ScannerLeaseError(f"Root scanner lease field differs: {key}")
        if not isinstance(lease.get("root_nonce"), str) or len(str(lease["root_nonce"])) < 32:
            raise ScannerLeaseError("Root scanner lease nonce is absent")
        expires = lease.get("expires_utc")
        if not isinstance(expires, str):
            raise ScannerLeaseError("Root scanner lease expiry is absent")
        try:
            expiry = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        except ValueError as error:
            raise ScannerLeaseError("Root scanner lease expiry differs") from error
        if expiry <= datetime.now(timezone.utc):
            raise ScannerLeaseError("Root scanner lease expired")
        run_root = (repository_root / str(request["run_root"])).resolve()
        runtime_root = (repository_root / "runtime" / "scanner").resolve()
        if run_root.parent != runtime_root:
            raise ScannerLeaseError("scanner run root escapes exact runtime scope")
        return cls(
            repository_root.resolve(), request_path.resolve(), lease_path.resolve(), request, lease,
            request_sha, _sha256_bytes(lease_path.read_bytes()), run_root,
        )

    def require_active(self) -> None:
        if self.master is None or self.identity_sha256 is None:
            raise ScannerLeaseError("scanner identity is not materialized")
        self.require_scanner_active()

    def require_scanner_active(self) -> None:
        if self.lease.get("status") != "ACTIVE" or self.lease.get("lease_kind") != LEASE_KIND:
            raise ScannerLeaseError("scanner-only lease is not active")

    def with_identity(self, master: bytes, identity_sha256: str) -> "ScannerLeaseBinding":
        if len(master) != 32 or _sha256_bytes(master + self.lease_sha256.encode("ascii")) != identity_sha256:
            raise ScannerLeaseError("scanner identity binding differs")
        return ScannerLeaseBinding(
            self.repository_root, self.request_path, self.lease_path, self.request, self.lease,
            self.request_sha256, self.lease_sha256, self.run_root, master, identity_sha256,
        )

    @property
    def component(self) -> str:
        return COMPONENT

    def validate_scanner_rows(self, rows: Sequence[Mapping[str, object]]) -> None:
        self.require_active()
        for row in rows:
            if int(row.get("test_mode", -1)) != 0:
                raise ScannerLeaseError("scanner row is not activity mode")
            raw_master = row.get("master")
            value = bytes.fromhex(raw_master) if isinstance(raw_master, str) else bytes(raw_master or b"")
            if value != self.master:
                raise ScannerLeaseError("scanner row master differs from sole identity")
            if int(row.get("lane", 0)) != -1 or int(row.get("cycle", 0)) != -1 or int(row.get("episode", 0)) != -1:
                raise ScannerLeaseError("scanner row contains non-scanner coordinate")
            if int(row.get("arm_substream", -1)) != 0 or int(row.get("degradation_flag", -1)) != 0 or int(row.get("fork_branch", -1)) != 0:
                raise ScannerLeaseError("scanner row coupling differs")


def _uniform(master: bytes, address: str) -> float:
    digest = hashlib.sha256(master + b"\0" + address.encode("utf-8")).digest()
    return ((int.from_bytes(digest[:8], "big") >> 11) + 0.5) / 2**53


def _address(
    coordinate: AcceptedTapeCoordinate,
    attempt: int | None,
    *,
    purpose: str,
    field: str,
) -> str:
    fields = (
        "DISH", "RBHR", "R05", purpose, str(coordinate.block), coordinate.split,
        coordinate.package, coordinate.schedule,
        "NONE" if attempt is None else str(coordinate.accepted_slot),
        "NONE" if attempt is None else str(attempt),
        "NONE", "NONE", "COMMON", "PAIR_SHARED", "PREFORK", "NONE",
        "NONE", "NONE", "NONE", "NONE", "NONE", field, "0",
    )
    return "/".join(fields)


def _choice(master: bytes, address: str, values: Sequence[int]) -> int:
    index = min(int(math.floor(_uniform(master, address) * len(values))), len(values) - 1)
    return int(values[index])


def scanner_reset_row(master: bytes, coordinate: AcceptedTapeCoordinate, attempt: int) -> dict[str, object]:
    if len(master) != 32 or not 0 <= attempt < ATTEMPT_CAP:
        raise ScannerLeaseError("scanner reset request differs")
    j = coordinate.accepted_slot
    ell = coordinate.within_stratum_slot
    schedule = coordinate.schedule
    if schedule == "K4":
        k_initial = k_new = 4
    elif schedule == "K8":
        k_initial = k_new = 8
    elif schedule == "K12":
        k_initial = k_new = 12
    elif schedule == "K4_TO_K12":
        k_initial, k_new = 4, 12
    elif schedule == "K12_TO_K4":
        k_initial, k_new = 12, 4
    else:
        raise ScannerLeaseError("scanner schedule differs")
    tau_d_seconds = (42, 54, 66)[j % 3]
    switch_tick = 1199
    if k_initial != k_new:
        switch_tick = 10 * (36, 48, 60, 72)[(j % 12) // 3]
    phase_address = _address(coordinate, None, purpose="K_SCHEDULE", field="PHASE_OFFSET")
    phase_offset = int(math.floor(k_initial * _uniform(master, phase_address)))
    def draw(purpose: str, field: str, values: Sequence[int]) -> int:
        return _choice(master, _address(coordinate, attempt, purpose=purpose, field=field), values)
    fixture_key = int.from_bytes(hashlib.sha256(
        master + b"\0" + coordinate.canonical_key().encode("ascii") + b"\0" + str(attempt).encode("ascii")
    ).digest()[:8], "big")
    return {
        "fixture_key": fixture_key,
        "master": master,
        "test_mode": 0,
        "package": PACKAGE_INDEX[coordinate.package],
        "reflection": 1 if (ell & 1) == 0 else -1,
        "initial_owner": (ell >> 1) & 1,
        "qa_owner": (ell >> 2) & 1,
        "k_initial": k_initial,
        "k_new": k_new,
        "switch_tick": switch_tick,
        "tau_d_tick": 10 * tau_d_seconds,
        "phase": (j + phase_offset) % k_initial,
        "route_speed": draw("TARGET", "ROUTE_SPEED", (4, 6, 8)),
        "turn_magnitude_deg": draw("TARGET", "TURN_MAGNITUDE", (25, 35, 45)),
        "turn_sign": draw("TARGET", "TURN_SIGN", (-1, 1)),
        "initial_ux": draw("INIT", "INITIAL_UX", (-80, -40, 40, 80)),
        "initial_uy": draw("INIT", "INITIAL_UY", (-180, -120, 120, 180)),
        "block": coordinate.block,
        "split": SPLIT_INDEX[coordinate.split],
        "schedule": SCHEDULE_INDEX[schedule],
        "accepted_slot": coordinate.accepted_slot,
        "candidate_attempt": attempt,
        "lane": -1,
        "cycle": -1,
        "arm_substream": 0,
        "degradation_flag": 0,
        "fork_branch": 0,
        "episode": -1,
    }


def _materialize_identity(binding: ScannerLeaseBinding) -> ScannerLeaseBinding:
    binding.require_scanner_active()
    binding.run_root.mkdir(parents=True, exist_ok=True)
    master_path = binding.run_root / "master.bin"
    identity_path = binding.run_root / "identity.json"
    if master_path.exists():
        master = master_path.read_bytes()
        if len(master) != 32:
            raise ScannerLeaseError("existing sole master is invalid; replacement is forbidden")
    else:
        master = secrets.token_bytes(32)
        try:
            with master_path.open("xb") as stream:
                stream.write(master)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            master = master_path.read_bytes()
    identity_sha = _sha256_bytes(master + binding.lease_sha256.encode("ascii"))
    identity = {
        "schema": "DISH_RBHR_R05_NONREPLACEABLE_SCANNER_IDENTITY_V1",
        "lease_id": LEASE_ID,
        "lease_sha256": binding.lease_sha256,
        "request_sha256": binding.request_sha256,
        "identity_sha256": identity_sha,
        "master_count": 1,
        "coordinate_count": 1,
        "master_blinded": True,
        "replacement_authorized": False,
    }
    if identity_path.exists():
        if _read_json(identity_path) != identity:
            raise ScannerLeaseError("existing sole identity differs; replacement is forbidden")
    else:
        _write_atomic(identity_path, identity)
    return binding.with_identity(master, identity_sha)


def _sealed_state_path(binding: ScannerLeaseBinding) -> Path:
    return binding.run_root / "sealed_scanner_state.json"


def _initial_state(binding: ScannerLeaseBinding) -> dict[str, object]:
    return {
        "schema": STATE_SCHEMA,
        "identity_sha256": binding.identity_sha256,
        "lease_sha256": binding.lease_sha256,
        "coordinate_index": 0,
        "next_attempt": 0,
        "accepted_attempts": [],
        "cumulative_attempts": 0,
        "executed_candidate_assays": 0,
        "cumulative_rejections": 0,
        "scanner_cpu_seconds": 0.0,
        "scanner_wall_seconds": 0.0,
        "io_bytes": 0,
        "status": "SCANNING",
    }


def _load_state(binding: ScannerLeaseBinding) -> dict[str, object]:
    path = _sealed_state_path(binding)
    if not path.exists():
        value = _initial_state(binding)
        _write_atomic(path, value)
        return value
    value = _read_json(path)
    if value.get("schema") != STATE_SCHEMA or value.get("identity_sha256") != binding.identity_sha256 or value.get("lease_sha256") != binding.lease_sha256:
        raise ScannerLeaseError("sealed scanner state identity differs")
    if not isinstance(value.get("accepted_attempts"), list):
        raise ScannerLeaseError("sealed scanner accepted frontier differs")
    return value


def _directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _resource_projection(state: Mapping[str, object], binding: ScannerLeaseBinding) -> dict[str, float]:
    accepted = len(state["accepted_attempts"])
    rejected = int(state["cumulative_rejections"])
    executed = int(state.get("executed_candidate_assays", state["cumulative_attempts"]))
    resource_attempts = max(rejected, executed - accepted)
    projected_rejections = resource_attempts if accepted == 0 else resource_attempts / accepted * EXPECTED_COORDINATES
    projected_rejections = max(float(resource_attempts), projected_rejections)
    scanner_cpu_complete = projected_rejections * SECONDS_PER_REJECTED_ATTEMPT / 3600.0
    scanner_wall_complete = scanner_cpu_complete / MEASURED_EIGHT_WORKER_SPEEDUP
    memory = process_memory_bytes(os.getpid())
    run_bytes = _directory_bytes(binding.run_root)
    io_bytes = int(state.get("io_bytes", 0))
    return {
        "cpu_core_hours": BASE["cpu_core_hours"] + scanner_cpu_complete,
        "wall_hours": BASE["wall_hours"] + scanner_wall_complete,
        "aggregate_rss_gib": max(BASE["aggregate_rss_gib"], memory["current"] / GIB),
        "scratch_gib": BASE["scratch_gib"] + run_bytes / GIB,
        "durable_gib": BASE["durable_gib"] + run_bytes / GIB,
        "total_io_gib": BASE["total_io_gib"] + io_bytes / GIB,
    }


def _guard_reason(state: Mapping[str, object], projection: Mapping[str, float]) -> str | None:
    if int(state["cumulative_rejections"]) >= REJECTION_HALT_BEFORE:
        return "CUMULATIVE_REJECTION_GUARD"
    for name, ceiling in GATES.items():
        if float(projection[name]) > ceiling:
            return name.upper() + "_GUARD"
    return None


def _public_receipt(state: Mapping[str, object], binding: ScannerLeaseBinding, projection: Mapping[str, float]) -> dict[str, object]:
    accepted = list(state["accepted_attempts"])
    accepted_digest = _sha256_bytes(_canonical_bytes(accepted))
    complete = len(accepted) == EXPECTED_COORDINATES and state.get("status") == "COMPLETE"
    all_gates = all(float(projection[name]) <= ceiling for name, ceiling in GATES.items())
    return {
        "schema": RECEIPT_SCHEMA,
        "direction_id": "degraded_incumbent_shadow_handover",
        "object_revision": SCIENCE_REVISION,
        "lease_id": LEASE_ID,
        "lease_sha256": binding.lease_sha256,
        "identity_sha256": binding.identity_sha256,
        "same_identity_preserved": True,
        "replacement_identity_created": False,
        "accepted_tape_count": len(accepted),
        "accepted_tape_inventory_complete": complete,
        "accepted_tape_frontier_sha256": accepted_digest,
        "cumulative_attempts": int(state["cumulative_attempts"]),
        "executed_candidate_assays": int(state.get("executed_candidate_assays", state["cumulative_attempts"])),
        "cumulative_rejections": int(state["cumulative_rejections"]),
        "resource_projection": dict(projection),
        "high_gates": GATES,
        "all_six_high_gates_established": bool(complete and all_gates),
        "status": state["status"],
        "guard_reason": state.get("guard_reason"),
        "partial_values_exposed": False,
        "model_training_evaluation_activity": False,
        "full_panel_executed": False,
    }


def run_scanner(
    *, repository_root: Path, request_path: Path, lease_path: Path, batch_size: int = 32,
) -> dict[str, object]:
    """Run/resume only the accepted-tape scanner under the exact Root lease."""

    if not 1 <= batch_size <= 256:
        raise ScannerLeaseError("scanner batch size differs")
    binding = ScannerLeaseBinding.load(
        repository_root=repository_root, request_path=request_path, lease_path=lease_path,
    )
    binding = _materialize_identity(binding)
    state = _load_state(binding)
    coordinates = complete_accepted_tape_coordinates()
    if len(coordinates) != EXPECTED_COORDINATES:
        raise ScannerLeaseError("complete accepted-tape inventory differs")
    if state.get("status") in ("COMPLETE", "GUARD_TRIP", "INVALID_PROTOCOL_OR_MEASUREMENT"):
        projection = _resource_projection(state, binding)
        return _public_receipt(state, binding, projection)
    io_start = process_io_bytes(os.getpid())
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    while int(state["coordinate_index"]) < EXPECTED_COORDINATES:
        projection = _resource_projection(state, binding)
        reason = _guard_reason(state, projection)
        if reason:
            state["status"] = "GUARD_TRIP"
            state["guard_reason"] = reason
            break
        coordinate_index = int(state["coordinate_index"])
        attempt = int(state["next_attempt"])
        if attempt >= ATTEMPT_CAP:
            state["status"] = "INVALID_PROTOCOL_OR_MEASUREMENT"
            state["guard_reason"] = "ATTEMPT_CAP_EXHAUSTED"
            break
        remaining_rejection_budget = MAX_REJECTIONS - int(state["cumulative_rejections"])
        if remaining_rejection_budget <= 0:
            state["status"] = "GUARD_TRIP"
            state["guard_reason"] = "CUMULATIVE_REJECTION_GUARD"
            break
        width = min(batch_size, ATTEMPT_CAP - attempt, remaining_rejection_budget)
        coordinate = coordinates[coordinate_index]
        rows = tuple(scanner_reset_row(binding.master or b"", coordinate, attempt + index) for index in range(width))
        output = scan_production_candidate_attempts(rows, authority=binding)
        state["executed_candidate_assays"] = int(state.get("executed_candidate_assays", state["cumulative_attempts"])) + width
        target = STRATUM_VALUE[coordinate.stratum]
        winner: int | None = None
        for index, row in enumerate(output):
            if int(row["eligible"]) and int(row["stratum"]) == target:
                winner = index
                break
        consumed = width if winner is None else winner + 1
        state["cumulative_attempts"] = int(state["cumulative_attempts"]) + consumed
        rejected_in_batch = consumed if winner is None else winner
        state["cumulative_rejections"] = int(state["cumulative_rejections"]) + rejected_in_batch
        if winner is None:
            state["next_attempt"] = attempt + consumed
        else:
            accepted = list(state["accepted_attempts"])
            accepted.append({"coordinate_key": coordinate.canonical_key(), "candidate_attempt": attempt + winner})
            state["accepted_attempts"] = accepted
            state["coordinate_index"] = coordinate_index + 1
            state["next_attempt"] = 0
        state["scanner_cpu_seconds"] = float(state["scanner_cpu_seconds"]) + (time.process_time() - cpu_start)
        state["scanner_wall_seconds"] = float(state["scanner_wall_seconds"]) + (time.perf_counter() - wall_start)
        io_now = process_io_bytes(os.getpid())
        state["io_bytes"] = int(state.get("io_bytes", 0)) + sum(
            max(0, io_now[name] - io_start[name]) for name in ("read_bytes", "write_bytes", "other_bytes")
        )
        _write_atomic(_sealed_state_path(binding), state)
        cpu_start = time.process_time(); wall_start = time.perf_counter(); io_start = io_now
    if int(state["coordinate_index"]) == EXPECTED_COORDINATES and state.get("status") == "SCANNING":
        state["status"] = "COMPLETE"
    projection = _resource_projection(state, binding)
    reason = _guard_reason(state, projection)
    if reason and state.get("status") == "COMPLETE":
        state["status"] = "GUARD_TRIP"
        state["guard_reason"] = reason
    _write_atomic(_sealed_state_path(binding), state)
    receipt = _public_receipt(state, binding, projection)
    _write_atomic(binding.run_root / "scanner_receipt.json", receipt)
    return receipt


__all__ = [
    "ATTEMPT_CAP", "GATES", "LEASE_ID", "LEASE_KIND", "LEASE_SCHEMA",
    "MAX_REJECTIONS", "REJECTION_HALT_BEFORE", "REQUEST_SCHEMA",
    "ScannerLeaseBinding", "ScannerLeaseError", "run_scanner",
    "scanner_reset_row", "validate_request",
]

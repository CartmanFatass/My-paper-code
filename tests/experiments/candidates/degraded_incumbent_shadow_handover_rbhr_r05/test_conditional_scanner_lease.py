from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import pytest

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_backend import (
    artifact_identity,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_scanner_lease import (
    GATES,
    LEASE_ID,
    LEASE_KIND,
    LEASE_SCHEMA,
    PROHIBITED,
    REQUEST_SCHEMA,
    ScannerLeaseBinding,
    ScannerLeaseError,
    scanner_reset_row,
    validate_request,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_tapes import (
    complete_accepted_tape_coordinates,
)


ROOT = Path(__file__).resolve().parents[4]


def _request() -> dict[str, object]:
    relative = "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r05/production_tapes.py"
    return {
        "schema": REQUEST_SCHEMA,
        "lease_id": LEASE_ID,
        "direction_id": "degraded_incumbent_shadow_handover",
        "object_revision": "DISH-RBHR-SCIENCE-20260821-05",
        "component": "dish.rbhr.r05.full_host",
        "lease_kind": LEASE_KIND,
        "issuer_required": "OPERATIONAL_ROOT",
        "master_count": 1,
        "identity_count": 1,
        "coordinate_count": 1,
        "accepted_tape_slots": 11_520,
        "attempt_cap_per_slot": 100_000,
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
        "source_manifest": {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()},
    }


def test_complete_first_attempt_rows_have_exact_slot_balance_and_native_abi() -> None:
    coordinates = complete_accepted_tape_coordinates()
    master = hashlib.sha256(b"TEST/DISH/RBHR/R05/SCANNER-ROW").digest()
    rows = tuple(scanner_reset_row(master, coordinate, 0) for coordinate in coordinates)
    assert len(rows) == 11_520
    for field, values in (("reflection", (-1, 1)), ("initial_owner", (0, 1)), ("qa_owner", (0, 1))):
        assert {value: sum(row[field] == value for row in rows) for value in values} == {values[0]: 5_760, values[1]: 5_760}
    assert artifact_identity()["abi_version"] == 4


def test_request_and_root_lease_are_exact_and_do_not_materialize_identity(tmp_path: Path) -> None:
    request = _request()
    validate_request(request, repository_root=ROOT)
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request, sort_keys=True) + "\n", encoding="utf-8")
    request_sha = hashlib.sha256(request_path.read_bytes()).hexdigest()
    lease = {
        "schema": LEASE_SCHEMA,
        "lease_id": LEASE_ID,
        "status": "ACTIVE",
        "issuer": "OPERATIONAL_ROOT",
        "direction_id": "degraded_incumbent_shadow_handover",
        "object_revision": "DISH-RBHR-SCIENCE-20260821-05",
        "component": "dish.rbhr.r05.full_host",
        "lease_kind": LEASE_KIND,
        "request_sha256": request_sha,
        "gates": GATES,
        "rejection_halt_before": 10_451_148,
        "master_count": 1,
        "identity_count": 1,
        "coordinate_count": 1,
        "accepted_tape_slots": 11_520,
        "full_panel_execution_authorized": False,
        "partial_values_authorized": False,
        "second_or_replacement_identity_authorized": False,
        "prohibited": list(PROHIBITED),
        "run_root": request["run_root"],
        "root_nonce": "0" * 64,
        "expires_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }
    lease_path = tmp_path / "lease.json"
    lease_path.write_text(json.dumps(lease, sort_keys=True) + "\n", encoding="utf-8")
    binding = ScannerLeaseBinding.load(repository_root=ROOT, request_path=request_path, lease_path=lease_path)
    assert binding.master is None
    assert not binding.run_root.exists()


def test_scanner_lease_rejects_replacement_permission(tmp_path: Path) -> None:
    request = _request()
    request["second_or_replacement_identity_authorized"] = True
    with pytest.raises(ScannerLeaseError, match="request field differs"):
        validate_request(request, repository_root=ROOT)

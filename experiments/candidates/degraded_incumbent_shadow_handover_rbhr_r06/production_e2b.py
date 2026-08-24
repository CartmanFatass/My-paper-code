"""Independent TEST-only E2B acceptance and lease-request validator."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from .production_contract import COMPONENT, SCIENCE_REVISION, TestAuthority
from .production_full_panel import STAGE_TOTALS


TEST_REQUEST_SCHEMA = "TEST_DISH_RBHR_R06_ROOT_LEASE_REQUEST_V1"
TEST_LEASE_SCHEMA = "TEST_DISH_RBHR_R06_ROOT_LEASE_V1"


class E2BAcceptanceError(RuntimeError):
    pass


@dataclass(frozen=True)
class TestRootLeaseBinding:
    __test__ = False
    component: str = COMPONENT
    identity_sha256: str = hashlib.sha256(b"TEST/DISH/RBHR/R06/E2B/IDENTITY").hexdigest()
    lease_chain_sha256: str = hashlib.sha256(b"TEST/DISH/RBHR/R06/E2B/LEASE").hexdigest()
    workers: int = 8
    cpu_cores: int = 8
    gpu: int = 0

    def require_active(self) -> None:
        TestAuthority().require_test_only()


class TestCompleteDataPlane:
    """Value-free exact-inventory data plane for the production executor."""

    __test__ = False
    scratch_root: Path
    durable_root: Path

    def __init__(self, root: Path, *, fail_once_at: tuple[str, int] | None = None) -> None:
        self.scratch_root = root / "scratch"; self.durable_root = root / "durable"
        self.fail_once_at = fail_once_at; self.failed = False

    @staticmethod
    def preferred_batch(stage: str, start: int, remaining: int) -> int:
        return min(4_096, remaining)

    def execute_units(self, stage: str, start: int, count: int) -> Sequence[bytes]:
        if stage not in STAGE_TOTALS or start < 0 or count <= 0 or start + count > STAGE_TOTALS[stage]:
            raise E2BAcceptanceError("TEST full-panel stage inventory differs")
        if self.fail_once_at == (stage, start) and not self.failed:
            self.failed = True
            raise E2BAcceptanceError("TEST injected failure before receipt commit")
        return tuple(f"TEST/R06/{stage}/{index}".encode("ascii") for index in range(start, start + count))

    def complete_result(self) -> Mapping[str, object]:
        return {"branch_result": {"schema": "TEST_DISH_RBHR_R06_COMPLETE_BRANCH_V1", "value_bearing": False},
                "test_only": True, "question_relevant_output": False}

    def inference_unit(self) -> Mapping[str, object]:
        return {"schema": "TEST_DISH_RBHR_R06_COMPLETE_INFERENCE_V1", "value_bearing": False}

    def population_unit(self, index: int) -> bytes: return self.execute_units("POPULATION", index, 1)[0]
    def training_unit(self, index: int) -> bytes: return self.execute_units("TRAINING", index, 1)[0]
    def evaluation_unit(self, index: int) -> bytes: return self.execute_units("EVALUATION", index, 1)[0]
    def fork_unit(self, index: int) -> bytes: return self.execute_units("FORK", index, 1)[0]


def load_test_only_cli_lease(repository_root: Path, lease_path: Path, request_path: Path):
    """TEST namespace loader used solely to exercise the exact production CLI."""

    TestAuthority().require_test_only()
    request = json.loads(request_path.read_text(encoding="ascii")); lease = json.loads(lease_path.read_text(encoding="ascii"))
    if request != {"schema": TEST_REQUEST_SCHEMA, "test_only": True, "activity": False}:
        raise E2BAcceptanceError("TEST CLI request differs")
    expected = {"schema": TEST_LEASE_SCHEMA, "test_only": True, "activity": False,
                "request_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest()}
    if lease != expected:
        raise E2BAcceptanceError("TEST CLI lease differs")
    run_root = repository_root.resolve() / "runtime" / "test_only" / "dish_rbhr_r06_e2b_cli_data_plane"
    return TestRootLeaseBinding(), TestCompleteDataPlane(run_root)


def validate_prepared_lease_request(repository_root: Path, request_path: Path, acceptance_path: Path) -> dict[str, object]:
    """Validate current-byte production request without issuing a lease."""

    root = repository_root.resolve(); request_path = request_path.resolve(); acceptance_path = acceptance_path.resolve()
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if request.get("schema") != "DISH_RBHR_R06_ROOT_LEASE_REQUEST_V1":
        raise E2BAcceptanceError("production lease-request schema differs")
    if request.get("component") != COMPONENT or request.get("science_revision") != SCIENCE_REVISION:
        raise E2BAcceptanceError("production lease-request object differs")
    if request.get("one_fresh_nonreplaceable_identity") is not True or request.get("partial_values_exposed") is not False:
        raise E2BAcceptanceError("production lease-request identity/firewall differs")
    if request.get("identity_materialized") is not False or request.get("lease_issued") is not False:
        raise E2BAcceptanceError("production lease-request preissue state differs")
    expected_resources = {
        "workers_max": 8, "cpu_cores_max": 8, "gpu": 0,
        "ordinary_cpu_hours": 320.0, "ordinary_wall_hours": 65.0,
        "hard_cpu_hours": 560.0, "hard_wall_hours": 110.0,
        "rss_gib": 40.0, "scratch_gib": 120.0, "durable_gib": 16.0, "io_gib": 400.0,
    }
    if request.get("resource_envelope") != expected_resources:
        raise E2BAcceptanceError("production lease-request resource envelope differs")
    acceptance_sha256 = hashlib.sha256(acceptance_path.read_bytes()).hexdigest()
    if request.get("acceptance_receipt") != str(acceptance_path.relative_to(root)).replace("\\", "/") or request.get("acceptance_sha256") != acceptance_sha256:
        raise E2BAcceptanceError("production lease-request acceptance binding differs")
    sources = request.get("source_sha256")
    if not isinstance(sources, Mapping) or not sources:
        raise E2BAcceptanceError("production lease-request source binding is absent")
    for relative, digest in sources.items():
        path = root / str(relative)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise E2BAcceptanceError("production lease-request source binding differs")
    if request.get("complete_inventory") != {"population": 11_520, "training_updates": 122_880,
                                               "evaluation_episodes": 115_200, "fork_rows": 6_912,
                                               "estimands": 6_990, "resamples": 99_999}:
        raise E2BAcceptanceError("production lease-request complete inventory differs")
    return {"schema": "DISH_RBHR_R06_LEASE_REQUEST_VALIDATION_V1", "request": str(request_path),
            "request_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
            "acceptance_sha256": acceptance_sha256, "lease_request_issuable": True,
            "lease_issued": False, "identity_materialized": False, "question_relevant_output": False}


__all__ = ["E2BAcceptanceError", "TEST_LEASE_SCHEMA", "TEST_REQUEST_SCHEMA", "TestCompleteDataPlane",
           "TestRootLeaseBinding", "load_test_only_cli_lease", "validate_prepared_lease_request"]

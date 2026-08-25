"""Fail-closed Root-lease loader binding for the future R06 full panel.

This module defines no request and materializes no master.  A caller must pass
two existing Root-authored files.  Only after their hashes, authority, resource
shape and single-identity invariants validate is the sealed master opened and
the concrete data plane constructed.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Mapping

from .production_contract import COMPONENT, SCIENCE_REVISION
from .production_full_panel import ResourceCeilings


class ProductionLeaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class RootLeaseBinding:
    component: str
    science_revision: str
    request_sha256: str
    identity_sha256: str
    lease_chain_sha256: str
    master_hex: str
    workers: int
    cpu_cores: int
    gpu: int
    active: bool

    def require_active(self) -> None:
        if not self.active:
            raise ProductionLeaseError("Root lease is not active")

    @property
    def master(self) -> bytes:
        self.require_active()
        raw = bytes.fromhex(self.master_hex)
        if len(raw) != 32 or hashlib.sha256(raw).hexdigest() != self.identity_sha256:
            raise ProductionLeaseError("sealed master identity differs")
        return raw


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _exact_resource_shape(value: Mapping[str, object]) -> None:
    ceilings = ResourceCeilings()
    exact = {
        "workers_max": ceilings.workers, "cpu_cores_max": ceilings.cpu_cores,
        "gpu": ceilings.gpu, "ordinary_cpu_hours": ceilings.ordinary_cpu_hours,
        "ordinary_wall_hours": ceilings.ordinary_wall_hours, "hard_cpu_hours": ceilings.hard_cpu_hours,
        "hard_wall_hours": ceilings.hard_wall_hours, "rss_gib": ceilings.rss_gib,
        "scratch_gib": ceilings.scratch_gib, "durable_gib": ceilings.durable_gib,
        "io_gib": ceilings.io_gib,
    }
    if dict(value) != exact:
        raise ProductionLeaseError("Root lease resource envelope differs")


def load_root_lease(repository_root: Path, lease_path: Path, request_path: Path):
    """Validate an issued lease and return ``(authority, data_plane)``.

    No file is created by this function.  Master materialization occurs only
    after both Root-authored inputs validate and ``active`` is true.
    """

    repository_root = repository_root.resolve(); lease_path = lease_path.resolve(); request_path = request_path.resolve()
    if not lease_path.is_file() or not request_path.is_file():
        raise ProductionLeaseError("Root lease and request files are required")
    request = json.loads(request_path.read_text(encoding="utf-8")); lease = json.loads(lease_path.read_text(encoding="utf-8"))
    if request.get("schema") != "DISH_RBHR_R06_ROOT_LEASE_REQUEST_V1" or lease.get("schema") != "DISH_RBHR_R06_ROOT_LEASE_V1":
        raise ProductionLeaseError("Root lease schema differs")
    if request.get("component") != COMPONENT or request.get("science_revision") != SCIENCE_REVISION:
        raise ProductionLeaseError("Root request object differs")
    request_sha256 = _sha256(request_path)
    if lease.get("request_sha256") != request_sha256 or lease.get("component") != COMPONENT or lease.get("science_revision") != SCIENCE_REVISION:
        raise ProductionLeaseError("Root lease request binding differs")
    if request.get("one_fresh_nonreplaceable_identity") is not True or request.get("partial_values_exposed") is not False:
        raise ProductionLeaseError("Root request identity/firewall differs")
    _exact_resource_shape(request.get("resource_envelope", {})); _exact_resource_shape(lease.get("resource_envelope", {}))
    authority = RootLeaseBinding(
        component=COMPONENT, science_revision=SCIENCE_REVISION, request_sha256=request_sha256,
        identity_sha256=str(lease.get("identity_sha256", "")), lease_chain_sha256=str(lease.get("lease_chain_sha256", "")),
        master_hex=str(lease.get("sealed_master_hex", "")), workers=int(lease.get("workers", 0)),
        cpu_cores=int(lease.get("cpu_cores", 0)), gpu=int(lease.get("gpu", -1)), active=lease.get("active") is True,
    )
    authority.require_active()
    if not 1 <= authority.workers <= 8 or not 1 <= authority.cpu_cores <= 8 or authority.gpu != 0:
        raise ProductionLeaseError("Root lease compute shape differs")
    master = authority.master
    from .production_data_plane import R06ProductionDataPlane
    run_root = repository_root / "runtime" / "dish_rbhr_r06" / authority.identity_sha256
    worker_spec = {
        "loader_module": "experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_lease",
        "loader_function": "load_process_worker_data_plane",
        "loader_kwargs": {"repository_root": str(repository_root), "lease_path": str(lease_path),
                          "request_path": str(request_path), "run_root": str(run_root)},
        "pin_affinity": False, "high_priority": True, "ideal_processor": False,
    }
    data_plane = R06ProductionDataPlane(authority=authority, master=master, run_root=run_root,
                                        process_worker_spec=worker_spec)
    return authority, data_plane


def load_process_worker_data_plane(*, repository_root: str, lease_path: str, request_path: str, run_root: str):
    """Spawn-safe worker loader; authority validation remains identical."""

    authority, _ = load_root_lease(Path(repository_root), Path(lease_path), Path(request_path))
    from .production_data_plane import R06ProductionDataPlane
    return R06ProductionDataPlane(authority=authority, master=authority.master, run_root=Path(run_root),
                                  process_worker_spec=None)


def lease_loader_binding_manifest() -> dict[str, object]:
    return {
        "schema": "DISH_RBHR_R06_LEASE_LOADER_BINDING_V1",
        "loader": "experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_lease:load_root_lease",
        "request_created": False, "lease_issued": False, "master_materialized": False,
        "single_nonreplaceable_identity": True, "fail_closed": True,
    }


__all__ = ["ProductionLeaseError", "RootLeaseBinding", "lease_loader_binding_manifest", "load_process_worker_data_plane", "load_root_lease"]

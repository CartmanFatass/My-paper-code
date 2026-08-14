from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from .config import DIRECTION, REGISTERED, REVISION, SEEDS


def require_production_authorization(path: Path, result_root: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "direction": DIRECTION,
        "revision": REVISION,
        "production_authorized": True,
        "result_root": str(result_root.resolve()),
        "max_workers": 1,
        "cpu_cores": 1,
        "gpu_count": 0,
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise PermissionError(f"production authorization mismatch for {key}")
    memory = payload.get("memory_mib")
    if not isinstance(memory, int) or not (0 < memory <= REGISTERED.max_memory_mib):
        raise PermissionError("lease memory_mib must be in (0,2048]")
    for key in ("lease_token", "stage_boundary"):
        if not isinstance(payload.get(key), str) or not str(payload[key]).strip():
            raise PermissionError(f"nonempty {key} is required")
    issued_raw = payload.get("issued_at_utc")
    expiry_raw = payload.get("not_after_utc")
    if not isinstance(issued_raw, str) or not isinstance(expiry_raw, str):
        raise PermissionError("timezone-aware issued_at_utc and not_after_utc are required")
    issued = datetime.fromisoformat(issued_raw.replace("Z", "+00:00"))
    expiry = datetime.fromisoformat(expiry_raw.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    if issued.tzinfo is None or expiry.tzinfo is None or not (issued <= now < expiry):
        raise PermissionError("production lease is not currently valid")
    authorized = payload.get("authorized_seeds")
    if (
        not isinstance(authorized, list)
        or not authorized
        or len(set(authorized)) != len(authorized)
        or not set(authorized).issubset(SEEDS)
    ):
        raise PermissionError("authorized_seeds must be a unique nonempty frozen subset")
    return payload


_SENTINEL = object()


class ProductionPermit:
    def __init__(self, sentinel: object, path: Path, result_root: Path, payload: dict[str, object]) -> None:
        if sentinel is not _SENTINEL:
            raise PermissionError("ProductionPermit cannot be constructed directly")
        self.path = path
        self.result_root = result_root
        self.payload = payload
        self.expiry = datetime.fromisoformat(str(payload["not_after_utc"]).replace("Z", "+00:00"))

    def assert_active(self) -> None:
        if datetime.now(timezone.utc) >= self.expiry:
            raise PermissionError("production lease expired")
        if require_production_authorization(self.path, self.result_root) != self.payload:
            raise PermissionError("production lease changed during execution")

    def assert_local_validity(self) -> None:
        if datetime.now(timezone.utc) >= self.expiry:
            raise PermissionError("production lease expired")

    def require_seed(self, seed: int) -> None:
        self.assert_active()
        if seed not in self.payload["authorized_seeds"]:
            raise PermissionError("seed is outside the direction lease")


def load_production_permit(path: Path, result_root: Path, certificate_path: Path) -> ProductionPermit:
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    if (
        certificate.get("revision") != REVISION
        or certificate.get("passed") is not True
        or certificate.get("registered_stochastic_object_materialized") is not False
    ):
        raise PermissionError("passing exact-r04 preactivity certificate is required")
    payload = require_production_authorization(path, result_root)
    return ProductionPermit(_SENTINEL, path, result_root, payload)


def require_active_permit(permit: ProductionPermit) -> None:
    if not isinstance(permit, ProductionPermit):
        raise PermissionError("validated ProductionPermit is required")
    permit.assert_local_validity()

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from .config import DIRECTION, REVISION, SEEDS


def require_production_authorization(path: Path, result_root: Path) -> dict[str, object]:
    """Fail-closed gate owned by Root; this package cannot mint authorization."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "direction": DIRECTION,
        "revision": REVISION,
        "production_authorized": True,
        "result_root": str(result_root.resolve()),
        "max_workers": 1,
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise PermissionError(f"production authorization mismatch for {key}")
    token = payload.get("lease_token")
    stage = payload.get("stage_boundary")
    issued_at = payload.get("issued_at_utc")
    not_after = payload.get("not_after_utc")
    if not isinstance(token, str) or not token.strip():
        raise PermissionError("nonempty Root lease_token is required")
    if not isinstance(stage, str) or not stage.strip():
        raise PermissionError("explicit stage_boundary is required")
    if not isinstance(issued_at, str) or not isinstance(not_after, str):
        raise PermissionError("issued_at_utc and not_after_utc are required")
    issued = datetime.fromisoformat(issued_at.replace("Z", "+00:00"))
    expiry = datetime.fromisoformat(not_after.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    if issued.tzinfo is None or expiry.tzinfo is None or not (issued <= now < expiry):
        raise PermissionError("production lease is not currently valid or is timezone-naive")
    authorized_seeds = payload.get("authorized_seeds")
    if (
        not isinstance(authorized_seeds, list)
        or not authorized_seeds
        or len(set(authorized_seeds)) != len(authorized_seeds)
        or not set(authorized_seeds).issubset(SEEDS)
    ):
        raise PermissionError("authorized_seeds must be a unique nonempty subset of registered seeds")
    wall_clock = payload.get("cumulative_wall_clock_cap_hours")
    if not isinstance(wall_clock, (int, float)) or not (0 < wall_clock <= 8):
        raise PermissionError("lease wall-clock cap must be in (0,8] hours")
    if (expiry - issued).total_seconds() > float(wall_clock) * 3600.0:
        raise PermissionError("lease validity window exceeds its cumulative wall-clock cap")
    return payload


_PERMIT_SENTINEL = object()


class ProductionPermit:
    """Capability returned only after exact-revision certificate/lease validation."""

    def __init__(
        self, sentinel: object, path: Path, result_root: Path, payload: dict[str, object],
    ) -> None:
        if sentinel is not _PERMIT_SENTINEL:
            raise PermissionError("ProductionPermit cannot be constructed directly")
        self._path = path
        self._result_root = result_root
        self.payload = payload
        self._expiry = datetime.fromisoformat(
            str(payload["not_after_utc"]).replace("Z", "+00:00")
        )

    def assert_local_validity(self) -> None:
        if datetime.now(timezone.utc) >= self._expiry:
            raise PermissionError("production permit expired")
        if not isinstance(self.payload.get("lease_token"), str):
            raise PermissionError("invalid ProductionPermit")

    def assert_active(self) -> None:
        self.assert_local_validity()
        current = require_production_authorization(self._path, self._result_root)
        if current != self.payload:
            raise PermissionError("production authorization changed during execution")

    def require_seed(self, seed: int) -> None:
        self.assert_active()
        if seed not in self.payload["authorized_seeds"]:
            raise PermissionError("seed is outside the Root lease")


def load_production_permit(
    path: Path, result_root: Path, certificate_path: Path,
) -> ProductionPermit:
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    if (
        certificate.get("revision") != REVISION
        or certificate.get("passed") is not True
        or certificate.get("registered_stochastic_object_materialized") is not False
    ):
        raise PermissionError("passing exact-revision preactivity certificate is required")
    payload = require_production_authorization(path, result_root)
    return ProductionPermit(_PERMIT_SENTINEL, path, result_root, payload)


def require_active_permit(permit: ProductionPermit) -> None:
    if not isinstance(permit, ProductionPermit):
        raise PermissionError("validated ProductionPermit is required")
    # The formal progress loop refreshes external validity; every stochastic
    # primitive still requires the capability object itself.
    permit.assert_local_validity()

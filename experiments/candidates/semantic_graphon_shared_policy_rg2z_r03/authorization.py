"""Fail-closed Root-lease authorization for the frozen RG2Z r03 panel."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

import hashlib

from .config import COUNTER_ROOT, DEVICE, DIRECTION, REVISION, SEEDS


ACTION = "SGSP-RG2Z-R03-FULL-PANEL"
ARMS = ("PHY-TRUST", "EDGE-FLEX")


_FRACTIONAL_TIMESTAMP = re.compile(
    r"^(?P<head>.+)\.(?P<fraction>\d+)(?P<offset>[+-]\d{2}:\d{2})$"
)


def parse_lease_timestamp(value: object, *, issued_boundary: bool) -> datetime:
    """Parse ISO/.NET lease timestamps without rounding expiry outward."""
    if not isinstance(value, str):
        raise PermissionError("lease timestamp must be a string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    match = _FRACTIONAL_TIMESTAMP.fullmatch(normalized)
    if match and len(match.group("fraction")) > 6:
        fraction = match.group("fraction")
        microseconds = int(fraction[:6])
        if issued_boundary and any(digit != "0" for digit in fraction[6:]):
            microseconds += 1
        if microseconds == 1_000_000:
            parsed = datetime.fromisoformat(match.group("head") + match.group("offset"))
            parsed += timedelta(seconds=1)
        else:
            normalized = f'{match.group("head")}.{microseconds:06d}{match.group("offset")}'
            parsed = datetime.fromisoformat(normalized)
    else:
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as error:
            raise PermissionError("lease timestamp is not valid ISO 8601") from error
    if parsed.tzinfo is None:
        raise PermissionError("lease timestamp must be timezone-aware")
    return parsed


def _registered_device() -> str:
    return str(DEVICE)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_exact_certificate(path: Path) -> dict[str, object]:
    certificate = json.loads(path.read_text(encoding="utf-8"))
    if certificate.get("revision") != REVISION or certificate.get("passed") is not True:
        raise PermissionError("a passing exact-revision preactivity certificate is required")
    if certificate.get("registered_stochastic_object_materialized") is not False:
        raise PermissionError("certificate must attest no registered stochastic materialization")
    source_hashes = certificate.get("source_hashes")
    package_root = Path(__file__).resolve().parent
    expected_paths = {source.name for source in package_root.glob("*.py")}
    if not isinstance(source_hashes, dict) or set(source_hashes) != expected_paths:
        raise PermissionError("certificate must cover exactly the current package sources")
    for relative, expected in source_hashes.items():
        candidate = (package_root / relative).resolve()
        if not isinstance(expected, str) or len(expected) != 64 or candidate.parent != package_root:
            raise PermissionError("certificate source hash entry is invalid")
        if not candidate.is_file() or _sha256(candidate) != expected:
            raise PermissionError("certificate is stale against current source hashes")
    return certificate


def require_production_authorization(path: Path, result_root: Path, certificate_path: Path) -> dict[str, object]:
    """Validate one exact Root-issued authorization; this package cannot mint it."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "direction": DIRECTION,
        "revision": REVISION,
        "action": ACTION,
        "production_authorized": True,
        "result_root": str(result_root.resolve()),
        "counter_root": COUNTER_ROOT,
        "device": _registered_device(),
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise PermissionError(f"production authorization mismatch for {key}")
    if payload.get("certificate_sha256") != _sha256(certificate_path):
        raise PermissionError("production authorization is not bound to this exact certificate")
    max_workers = payload.get("max_workers")
    if not isinstance(max_workers, int) or not 1 <= max_workers <= 4:
        raise PermissionError("Root lease max_workers must be an integer in [1,4]")
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
    issued = parse_lease_timestamp(issued_at, issued_boundary=True)
    expiry = parse_lease_timestamp(not_after, issued_boundary=False)
    now = datetime.now(timezone.utc)
    if not issued <= now < expiry:
        raise PermissionError("production lease is not currently valid")
    authorized_seeds = payload.get("authorized_seeds")
    if not isinstance(authorized_seeds, list) or not authorized_seeds:
        raise PermissionError("authorization must name a nonempty registered seed subset")
    if len(set(authorized_seeds)) != len(authorized_seeds) or not set(authorized_seeds).issubset(SEEDS):
        raise PermissionError("authorization contains an invalid registered seed subset")
    if authorized_seeds != [seed for seed in SEEDS if seed in set(authorized_seeds)]:
        raise PermissionError("authorization seed subset must preserve frozen panel order")
    return payload


_PERMIT_SENTINEL = object()


class ProductionPermit:
    """A capability constructed only after all exact identity checks succeed."""

    def __init__(self, sentinel: object, path: Path, result_root: Path, certificate_path: Path, certificate: dict[str, object], payload: dict[str, object]) -> None:
        if sentinel is not _PERMIT_SENTINEL:
            raise PermissionError("ProductionPermit cannot be constructed directly")
        self._path = path
        self._result_root = result_root
        self._certificate_path = certificate_path
        self._certificate = certificate
        self.payload = payload
        self._expiry = parse_lease_timestamp(payload["not_after_utc"], issued_boundary=False)

    def assert_local_validity(self) -> None:
        if datetime.now(timezone.utc) >= self._expiry:
            raise PermissionError("production permit expired")
        if not isinstance(self.payload.get("lease_token"), str):
            raise PermissionError("invalid ProductionPermit")

    def assert_active(self) -> None:
        self.assert_local_validity()
        if require_exact_certificate(self._certificate_path) != self._certificate:
            raise PermissionError("preactivity certificate changed during execution")
        if require_production_authorization(self._path, self._result_root, self._certificate_path) != self.payload:
            raise PermissionError("production authorization changed during execution")

    def require_seed(self, seed: int) -> None:
        self.assert_active()
        if seed not in self.payload["authorized_seeds"]:
            raise PermissionError("seed is outside the frozen registered panel")


def load_production_permit(path: Path, result_root: Path, certificate_path: Path) -> ProductionPermit:
    certificate = require_exact_certificate(certificate_path)
    payload = require_production_authorization(path, result_root, certificate_path)
    return ProductionPermit(_PERMIT_SENTINEL, path, result_root, certificate_path, certificate, payload)


def require_active_permit(permit: ProductionPermit) -> None:
    if not isinstance(permit, ProductionPermit):
        raise PermissionError("validated ProductionPermit is required")
    permit.assert_active()

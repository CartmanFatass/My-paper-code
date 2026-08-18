"""Per-binding wake leases. Exactly one scheduler holder wins."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .mailbox_models import DEFAULT_LEASE_SECONDS
from .store import ObserverStore


class LeaseError(RuntimeError):
    """Raised when a lease cannot be acquired or renewed."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat()


class SchedulerLeases:
    def __init__(self, store: ObserverStore) -> None:
        self.store = store

    def lease_key(self, binding_id: str) -> str:
        return f"wake:{binding_id}"

    def acquire(
        self,
        binding_id: str,
        holder_instance_id: str,
        *,
        ttl_seconds: float = DEFAULT_LEASE_SECONDS,
    ) -> dict[str, object]:
        key = self.lease_key(binding_id)
        now = _now()
        expires = now + timedelta(seconds=ttl_seconds)
        with self.store._lock, self.store.connection:
            existing = self.store.connection.execute(
                "SELECT * FROM scheduler_leases WHERE lease_key = ?",
                (key,),
            ).fetchone()
            if existing is None:
                self.store.connection.execute(
                    """INSERT INTO scheduler_leases (
                        lease_key, holder_instance_id, acquired_at, expires_at, generation
                    ) VALUES (?, ?, ?, ?, 1)""",
                    (key, holder_instance_id, _iso(now), _iso(expires)),
                )
                generation = 1
            else:
                expires_at = datetime.fromisoformat(str(existing["expires_at"]))
                holder = str(existing["holder_instance_id"])
                if holder != holder_instance_id and expires_at > now:
                    raise LeaseError("lease is held by another instance")
                generation = int(existing["generation"]) + 1
                self.store.connection.execute(
                    """UPDATE scheduler_leases
                    SET holder_instance_id = ?, acquired_at = ?, expires_at = ?, generation = ?
                    WHERE lease_key = ?""",
                    (holder_instance_id, _iso(now), _iso(expires), generation, key),
                )
        return {
            "lease_key": key,
            "holder_instance_id": holder_instance_id,
            "generation": generation,
            "expires_at": _iso(expires),
        }

    def renew(
        self,
        binding_id: str,
        holder_instance_id: str,
        *,
        ttl_seconds: float = DEFAULT_LEASE_SECONDS,
    ) -> dict[str, object]:
        key = self.lease_key(binding_id)
        now = _now()
        with self.store._lock, self.store.connection:
            existing = self.store.connection.execute(
                "SELECT * FROM scheduler_leases WHERE lease_key = ?",
                (key,),
            ).fetchone()
            if existing is None or str(existing["holder_instance_id"]) != holder_instance_id:
                raise LeaseError("caller does not hold the lease")
            expires = now + timedelta(seconds=ttl_seconds)
            generation = int(existing["generation"]) + 1
            self.store.connection.execute(
                "UPDATE scheduler_leases SET expires_at = ?, generation = ? WHERE lease_key = ?",
                (_iso(expires), generation, key),
            )
        return {"lease_key": key, "generation": generation, "expires_at": _iso(expires)}

    def release(self, binding_id: str, holder_instance_id: str) -> None:
        key = self.lease_key(binding_id)
        with self.store._lock, self.store.connection:
            self.store.connection.execute(
                "DELETE FROM scheduler_leases WHERE lease_key = ? AND holder_instance_id = ?",
                (key, holder_instance_id),
            )

    def recover_stale(self, *, now: datetime | None = None) -> list[str]:
        current = now or _now()
        with self.store._lock, self.store.connection:
            rows = self.store.connection.execute(
                "SELECT lease_key FROM scheduler_leases WHERE expires_at <= ?",
                (_iso(current),),
            ).fetchall()
            keys = [str(row[0]) for row in rows]
            if keys:
                self.store.connection.executemany(
                    "DELETE FROM scheduler_leases WHERE lease_key = ?",
                    [(key,) for key in keys],
                )
            return keys

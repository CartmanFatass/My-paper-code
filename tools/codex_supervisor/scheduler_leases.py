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

    def get(self, binding_id: str) -> dict[str, object] | None:
        row = self.store.connection.execute(
            "SELECT * FROM scheduler_leases WHERE lease_key = ?",
            (self.lease_key(binding_id),),
        ).fetchone()
        return dict(row) if row is not None else None

    def assert_held(
        self,
        binding_id: str,
        holder_instance_id: str,
        generation: int,
    ) -> dict[str, object]:
        current = self.get(binding_id)
        now = _now()
        if current is None:
            raise LeaseError("lease is not held")
        if str(current["holder_instance_id"]) != holder_instance_id:
            raise LeaseError("lease is held by another instance")
        if int(current["generation"]) != int(generation):
            raise LeaseError("lease generation mismatch")
        if datetime.fromisoformat(str(current["expires_at"])) <= now:
            raise LeaseError("lease has expired")
        return current

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
        with self.store._lock:
            previous = self.store.connection.isolation_level
            self.store.connection.isolation_level = None
            try:
                self.store.connection.execute("BEGIN IMMEDIATE")
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
                    cursor = self.store.connection.execute(
                        """UPDATE scheduler_leases
                        SET holder_instance_id = ?, acquired_at = ?, expires_at = ?, generation = generation + 1
                        WHERE lease_key = ?
                          AND (holder_instance_id = ? OR expires_at <= ?)""",
                        (
                            holder_instance_id,
                            _iso(now),
                            _iso(expires),
                            key,
                            holder_instance_id,
                            _iso(now),
                        ),
                    )
                    if cursor.rowcount != 1:
                        raise LeaseError("lease is held by another instance")
                    generation = int(
                        self.store.connection.execute(
                            "SELECT generation FROM scheduler_leases WHERE lease_key = ?",
                            (key,),
                        ).fetchone()[0]
                    )
                self.store.connection.execute("COMMIT")
            except Exception:
                self.store.connection.execute("ROLLBACK")
                raise
            finally:
                self.store.connection.isolation_level = previous
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
        generation: int | None = None,
    ) -> dict[str, object]:
        key = self.lease_key(binding_id)
        now = _now()
        expires = now + timedelta(seconds=ttl_seconds)
        with self.store._lock:
            previous = self.store.connection.isolation_level
            self.store.connection.isolation_level = None
            try:
                self.store.connection.execute("BEGIN IMMEDIATE")
                if generation is None:
                    existing = self.store.connection.execute(
                        "SELECT * FROM scheduler_leases WHERE lease_key = ?",
                        (key,),
                    ).fetchone()
                    if existing is None or str(existing["holder_instance_id"]) != holder_instance_id:
                        raise LeaseError("caller does not hold the lease")
                    generation = int(existing["generation"])
                cursor = self.store.connection.execute(
                    """UPDATE scheduler_leases
                    SET expires_at = ?
                    WHERE lease_key = ? AND holder_instance_id = ? AND generation = ? AND expires_at > ?""",
                    (_iso(expires), key, holder_instance_id, generation, _iso(now)),
                )
                if cursor.rowcount != 1:
                    raise LeaseError("caller does not hold the lease")
                self.store.connection.execute("COMMIT")
            except Exception:
                self.store.connection.execute("ROLLBACK")
                raise
            finally:
                self.store.connection.isolation_level = previous
        return {"lease_key": key, "generation": generation, "expires_at": _iso(expires)}

    def release(self, binding_id: str, holder_instance_id: str, generation: int | None = None) -> None:
        key = self.lease_key(binding_id)
        with self.store._lock:
            previous = self.store.connection.isolation_level
            self.store.connection.isolation_level = None
            try:
                self.store.connection.execute("BEGIN IMMEDIATE")
                if generation is None:
                    self.store.connection.execute(
                        "DELETE FROM scheduler_leases WHERE lease_key = ? AND holder_instance_id = ?",
                        (key, holder_instance_id),
                    )
                else:
                    self.store.connection.execute(
                        """DELETE FROM scheduler_leases
                        WHERE lease_key = ? AND holder_instance_id = ? AND generation = ?""",
                        (key, holder_instance_id, generation),
                    )
                self.store.connection.execute("COMMIT")
            except Exception:
                self.store.connection.execute("ROLLBACK")
                raise
            finally:
                self.store.connection.isolation_level = previous

    def recover_stale(self, *, now: datetime | None = None) -> list[str]:
        current = now or _now()
        with self.store._lock:
            previous = self.store.connection.isolation_level
            self.store.connection.isolation_level = None
            try:
                self.store.connection.execute("BEGIN IMMEDIATE")
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
                self.store.connection.execute("COMMIT")
                return keys
            except Exception:
                self.store.connection.execute("ROLLBACK")
                raise
            finally:
                self.store.connection.isolation_level = previous

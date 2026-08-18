from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tools.codex_supervisor.scheduler_leases import LeaseError, SchedulerLeases
from tools.codex_supervisor.store import ObserverStore


def test_two_instances_one_winner_and_stale_takeover(tmp_path: Path) -> None:
    store = ObserverStore(tmp_path)
    leases = SchedulerLeases(store)
    first = leases.acquire("bind_a", "inst-1", ttl_seconds=30)
    assert first["generation"] == 1
    with pytest.raises(LeaseError):
        leases.acquire("bind_a", "inst-2", ttl_seconds=30)
    leases.release("bind_a", "inst-1")
    second = leases.acquire("bind_a", "inst-2", ttl_seconds=1)
    assert second["holder_instance_id"] == "inst-2"
    leases.store.connection.execute(
        "UPDATE scheduler_leases SET expires_at = ? WHERE lease_key = ?",
        ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(), "wake:bind_a"),
    )
    leases.store.connection.commit()
    recovered = leases.recover_stale()
    assert "wake:bind_a" in recovered
    third = leases.acquire("bind_a", "inst-1", ttl_seconds=30)
    assert third["generation"] == 1
    store.close()

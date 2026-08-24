from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import make_observer_config, write_fake_codex
from tools.codex_supervisor.observer import ObserverService
from tools.codex_supervisor.store import ObserverStore


class _Scheduler:
    def __init__(self, *, eligible: bool = False, error: str | None = None) -> None:
        self.eligible = eligible
        self.error = error
        self.calls = 0

    def has_eligible_work(self) -> bool:
        return self.eligible

    async def once(self) -> dict[str, object]:
        self.calls += 1
        if self.error:
            raise RuntimeError(self.error)
        return {"scheduled": {"wake_batch_id": "wake-one"}}


def _service(tmp_path: Path) -> ObserverService:
    return ObserverService(
        make_observer_config(tmp_path, reconcile_interval_seconds=0.01),
        binary=write_fake_codex(tmp_path),
        store=ObserverStore(tmp_path / "runtime"),
    )


async def _finish(service: ObserverService) -> None:
    if service._single_wake_task is not None:
        await asyncio.wait_for(service._single_wake_task, timeout=1)


def test_host_accepts_only_one_arm(tmp_path: Path) -> None:
    async def body() -> None:
        service, scheduler = _service(tmp_path), _Scheduler()
        assert service.arm_single_wake(scheduler)["state"] == "ARMED"
        with pytest.raises(ValueError, match="already armed"):
            service.arm_single_wake(_Scheduler())
        await service.stop("NORMAL")
        service.store.close()
    asyncio.run(body())


def test_no_event_causes_no_scheduler_or_turn_attempt(tmp_path: Path) -> None:
    async def body() -> None:
        service, scheduler = _service(tmp_path), _Scheduler()
        service.arm_single_wake(scheduler)
        await asyncio.sleep(0.04)
        assert scheduler.calls == 0
        assert service.single_wake_status()["state"] == "ARMED"
        await service.stop("NORMAL")
        service.store.close()
    asyncio.run(body())


def test_one_event_causes_at_most_one_scheduling_attempt(tmp_path: Path) -> None:
    async def body() -> None:
        service, scheduler = _service(tmp_path), _Scheduler()
        service.arm_single_wake(scheduler)
        scheduler.eligible = True
        await _finish(service)
        assert scheduler.calls == 1
        assert service.single_wake_status()["state"] == "CONSUMED"
        await service.stop("NORMAL")
        service.store.close()
    asyncio.run(body())


def test_uncertain_attempt_consumes_arm_without_resend(tmp_path: Path) -> None:
    async def body() -> None:
        service, scheduler = _service(tmp_path), _Scheduler(eligible=True, error="submission uncertain")
        service.arm_single_wake(scheduler)
        await _finish(service)
        await asyncio.sleep(0.03)
        assert scheduler.calls == 1
        assert service.single_wake_status()["result"]["outcome"] == "REJECTED_OR_UNCERTAIN"
        with pytest.raises(ValueError):
            service.arm_single_wake(_Scheduler(eligible=True))
        await service.stop("NORMAL")
        service.store.close()
    asyncio.run(body())


def test_host_stop_cancels_unconsumed_arm(tmp_path: Path) -> None:
    async def body() -> None:
        service, scheduler = _service(tmp_path), _Scheduler()
        service.arm_single_wake(scheduler)
        await service.stop("NORMAL")
        assert service._single_wake_task is not None and service._single_wake_task.done()
        assert service.single_wake_status()["state"] == "CANCELLED"
        assert scheduler.calls == 0
        service.store.close()
    asyncio.run(body())

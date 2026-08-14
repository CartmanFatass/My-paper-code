from __future__ import annotations

import time

from ..resources import _resident_bytes
from .config import RESOURCES


class ResourceLimitExceeded(RuntimeError):
    pass


class ResourceMonitor:
    def __init__(self) -> None:
        self.started = time.monotonic()
        self.peak_rss = 0
        self.checks = 0

    def check(self) -> None:
        elapsed = time.monotonic() - self.started
        rss = _resident_bytes()
        self.peak_rss = max(self.peak_rss, rss)
        self.checks += 1
        if elapsed > RESOURCES.wall_seconds:
            raise ResourceLimitExceeded(f"B2 wall limit exceeded: {elapsed}")
        if rss >= RESOURCES.rss_bytes:
            raise ResourceLimitExceeded(f"B2 RSS limit reached: {rss}")

    def facts(self) -> dict[str, object]:
        self.check()
        return self.snapshot()

    def snapshot(self) -> dict[str, object]:
        return {"elapsed_seconds": time.monotonic() - self.started, "peak_rss_bytes": self.peak_rss,
                "checks": self.checks, "cpu_workers": 1, "gpu_used": False,
                "wall_limit_seconds": RESOURCES.wall_seconds, "rss_limit_bytes": RESOURCES.rss_bytes}

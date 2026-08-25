from __future__ import annotations

import time

from ..resources import _resident_bytes


class ResourceMonitor:
    """Observes resources without turning a wall slice or RSS value into a stop rule."""

    def __init__(self) -> None:
        self.started = time.monotonic()
        self.peak_rss = 0
        self.checks = 0

    def check(self) -> None:
        self.peak_rss = max(self.peak_rss, _resident_bytes())
        self.checks += 1

    def snapshot(self) -> dict[str, object]:
        return {"elapsed_seconds": time.monotonic() - self.started,
                "peak_rss_bytes": self.peak_rss, "checks": self.checks,
                "cpu_workers": 1, "gpu_used": False,
                "resource_values_are_scientific_stopping_rules": False}

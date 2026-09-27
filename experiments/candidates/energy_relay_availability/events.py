"""Read-only native fault diagnostics and descriptive within-episode QoS windows."""

from __future__ import annotations

from contextlib import contextmanager

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.observation import own_energy


class FaultObserver:
    """Copy pre-reset/post-step raw timers; never expose them to the controller."""

    def __init__(self, raw):
        self.raw = raw
        self.rows: dict[str, list[np.ndarray]] = {
            key: [] for key in ("pre_timer", "post_timer", "pre_failed", "post_failed",
                            "pre_available", "post_available", "pre_charging",
                            "post_charging", "onset", "expiry", "refault", "recovery")
        }
        self._pre_timer = None

    @contextmanager
    def attach(self, controller):
        # evaluate_world calls attach after env.reset. No controller hook is needed.
        self._pre_timer = np.asarray(self.raw.uav_failure_timers, dtype=np.int16).copy()
        try:
            yield
        finally:
            self._pre_timer = None

    def on_step(self, *, t, observations_t, observations_t1, **_):
        pre = self._pre_timer
        if pre is None or pre.shape != (8,):
            raise RuntimeError("fault observer was not attached after reset")
        post = np.asarray(self.raw.uav_failure_timers, dtype=np.int16).copy()
        pre_failed = pre > 0
        post_failed = np.asarray(self.raw.uav_failed, dtype=bool).copy()
        pre_legal = own_energy(observations_t)
        post_legal = own_energy(observations_t1)
        values = {
            "pre_timer": pre, "post_timer": post,
            "pre_failed": pre_failed, "post_failed": post_failed,
            "pre_available": pre_legal["available"],
            "post_available": post_legal["available"],
            "pre_charging": pre_legal["charging"],
            "post_charging": post_legal["charging"],
            "onset": post > np.maximum(pre - 1, 0),
            "expiry": pre == 1,
            "refault": (pre == 1) & (post > 0),
            "recovery": pre_failed & ~post_failed,
        }
        if (not np.array_equal(post_failed, post > 0)
                or np.any(post_failed & post_legal["available"])):
            raise ValueError("native fault flags disagree with timers or legal availability")
        for key, value in values.items():
            self.rows[key].append(np.asarray(value).copy())
        self._pre_timer = post

    def as_arrays(self) -> dict[str, np.ndarray]:
        return {key: np.asarray(values) for key, values in self.rows.items()}


def event_windows(qos: np.ndarray, events: dict[str, np.ndarray]) -> dict:
    """Each event is an observation at transition t; only full windows enter means."""
    qos = np.asarray(qos, dtype=np.float64)
    if qos.ndim != 1 or not np.isfinite(qos).all():
        raise ValueError("QoS trace must be one finite transition series")
    length = len(qos)
    all_positions = []
    result = {}
    for kind in ("onset", "recovery"):
        mask = np.asarray(events[kind], dtype=bool)
        if mask.shape != (length, 8):
            raise ValueError(f"{kind} shape differs from transition trace")
        positions = list(zip(*np.nonzero(mask)))
        all_positions.extend((kind, int(t), int(uav)) for t, uav in positions)
        rows = []
        for t, uav in positions:
            pre = qos[max(0, t - 20):t]
            post = qos[t:min(length, t + 20)]
            post60 = qos[t:min(length, t + 60)] if kind == "recovery" else None
            rows.append({
                "t": int(t), "uav": int(uav),
                "pre_length": len(pre), "post_length": len(post),
                "pre_mean": float(pre.mean()) if len(pre) else None,
                "post_mean": float(post.mean()) if len(post) else None,
                "full_20": len(pre) == 20 and len(post) == 20,
                "delta20": float(post.mean() - pre.mean()) if len(pre) == 20 and len(post) == 20 else None,
                "post60_length": len(post60) if post60 is not None else None,
                "post60_mean": float(post60.mean()) if post60 is not None and len(post60) else None,
                "full_60": len(post60) == 60 if post60 is not None else None,
            })
        complete = [item["delta20"] for item in rows if item["full_20"]]
        full_post60 = [item["post60_mean"] for item in rows if item["full_60"]]
        result[kind] = {
            "events": len(rows), "complete20": len(complete),
            "censored20": len(rows) - len(complete),
            "world_mean_delta20": float(np.mean(complete)) if complete else None,
            "complete60": sum(item["full_60"] for item in rows) if kind == "recovery" else None,
            "censored60": len(rows) - len(full_post60) if kind == "recovery" else None,
            "world_mean_full_post60": float(np.mean(full_post60)) if full_post60 else None,
            "rows": rows,
        }
    for kind in ("onset", "recovery"):
        for row in result[kind]["rows"]:
            t = row["t"]
            # Explicitly retain overlapping events, including simultaneous UAVs.
            row["overlaps_other_event"] = any(
                other_kind != kind or other_t != t or other_uav != row["uav"]
                for other_kind, other_t, other_uav in all_positions
                if max(t - 20, other_t - 20) < min(t + 20, other_t + 20)
            )
        result[kind]["overlapping_events"] = sum(
            item["overlaps_other_event"] for item in result[kind]["rows"])
    result["expiry_count"] = int(np.asarray(events["expiry"]).sum())
    result["refault_count"] = int(np.asarray(events["refault"]).sum())
    return result


def aggregate_events(rows: list[dict], kind: str) -> dict:
    """World-level mean is the unit; events and UAVs are descriptive counts only."""
    complete = [row["events"][kind]["world_mean_delta20"] for row in rows
                if row["events"][kind]["world_mean_delta20"] is not None]
    full60 = [row["events"][kind]["world_mean_full_post60"] for row in rows
              if row["events"][kind]["world_mean_full_post60"] is not None]
    return {
        "events": sum(row["events"][kind]["events"] for row in rows),
        "complete20": sum(row["events"][kind]["complete20"] for row in rows),
        "censored20": sum(row["events"][kind]["censored20"] for row in rows),
        "overlapping_events": sum(row["events"][kind]["overlapping_events"] for row in rows),
        "event_worlds": sum(row["events"][kind]["events"] > 0 for row in rows),
        "no_event_worlds": sum(row["events"][kind]["events"] == 0 for row in rows),
        "censored_worlds": sum(row["events"][kind]["censored20"] > 0 for row in rows),
        "complete_event_worlds": len(complete),
        "world_mean_delta20": float(np.mean(complete)) if complete else None,
        "world_sd_delta20": float(np.std(complete, ddof=1)) if len(complete) > 1 else None,
        "complete60": sum(row["events"][kind]["complete60"] for row in rows)
        if kind == "recovery" else None,
        "censored60": sum(row["events"][kind]["censored60"] for row in rows)
        if kind == "recovery" else None,
        "full60_worlds": len(full60) if kind == "recovery" else None,
        "world_mean_full_post60": float(np.mean(full60)) if full60 else None,
    }

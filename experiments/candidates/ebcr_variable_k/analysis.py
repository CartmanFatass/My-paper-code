from __future__ import annotations

from collections import Counter
import math
from typing import Iterable

import numpy as np

from .host import EpisodeResult

T_975 = {
    1: 12.706204736, 2: 4.30265273, 3: 3.182446305, 4: 2.776445105,
    5: 2.570581836, 6: 2.446911851, 7: 2.364624252, 8: 2.306004135,
    9: 2.262157163, 10: 2.228138852, 11: 2.20098516, 12: 2.17881283,
    13: 2.160368656, 14: 2.144786688, 15: 2.131449546, 16: 2.119905299,
    17: 2.109815578, 18: 2.10092204, 19: 2.093024054, 20: 2.085963447,
    21: 2.079613845, 22: 2.073873068, 23: 2.06865761, 24: 2.063898562,
    25: 2.059538553, 26: 2.055529439, 27: 2.051830516, 28: 2.048407142,
    29: 2.045229642, 30: 2.042272456,
}


def student_t_interval(values: Iterable[float]) -> dict[str, float | int | None]:
    array = np.asarray(tuple(values), dtype=np.float64)
    if array.size < 2:
        return {"n": int(array.size), "mean": float(array.mean()) if array.size else None,
                "standard_error": None, "lower": None, "upper": None}
    mean = float(array.mean())
    standard_error = float(array.std(ddof=1) / math.sqrt(array.size))
    critical = T_975.get(array.size - 1, 1.959963985)
    return {"n": int(array.size), "mean": mean, "standard_error": standard_error,
            "lower": mean - critical * standard_error, "upper": mean + critical * standard_error}


def summarize_episodes(rows: Iterable[EpisodeResult]) -> dict[str, object]:
    episodes = list(rows)
    if not episodes:
        return {"episodes": 0}
    total_ticks = sum(row.physics_ticks for row in episodes)
    periods = Counter(period for row in episodes for role in row.ordinary_periods for period in role)
    renewal_counts = Counter(tuple(row.total_renewals) for row in episodes)
    delays = [delay for row in episodes for delay in row.boundary_delays]
    pending = [delay for row in episodes for delay in row.pending_delays]
    total_renewals = sum(sum(row.total_renewals) for row in episodes)
    return {
        "episodes": len(episodes),
        "mean_return": float(np.mean([row.normalized_return for row in episodes])),
        "success_rate": sum(row.packet_successes for row in episodes) / total_ticks,
        "stale_tick_rate": sum(row.stale_ticks for row in episodes) / total_ticks,
        "renewal_downtime_rate": sum(row.renewal_downtime for row in episodes) / total_ticks,
        "mean_renewal_cost": float(np.mean([row.renewal_cost for row in episodes])),
        "mean_unsafe_normal_renewal_cost": float(np.mean([row.unsafe_normal_renewal_cost for row in episodes])),
        "realized_period_histogram": {str(key): value for key, value in sorted(periods.items())},
        "renewal_count_histogram": {f"{key[0]},{key[1]}": value for key, value in sorted(renewal_counts.items())},
        "mean_boundary_to_renewal_delay": float(np.mean(delays)) if delays else None,
        "mean_pending_delay": float(np.mean(pending)) if pending else None,
        "simultaneous_renewal_rate": sum(row.simultaneous_renewal_ticks for row in episodes) / total_ticks,
        "renewals_ready_rate": sum(sum(row.renewals_ready) for row in episodes) / max(1, total_renewals),
        "request_rate_by_role": [
            sum(row.request_counts[role] for row in episodes) / total_ticks for role in range(2)
        ],
        "executed_renewal_rate_by_role": [
            sum(row.total_renewals[role] for row in episodes) / total_ticks for role in range(2)
        ],
        "forced_event_counts_by_role": [
            sum(row.forced_event_counts[role] for row in episodes) for role in range(2)
        ],
        "emergency_immediate_rate": sum(row.emergency_immediate for row in episodes) / len(episodes),
        "cap_violations": sum(row.cap_violation for row in episodes),
        "resource": {
            "actor_forward_calls": sum(row.actor_forward_calls for row in episodes),
            "messages": sum(row.messages for row in episodes),
            "transmitted_bits": sum(row.transmitted_bits for row in episodes),
            "physics_ticks": total_ticks,
            "task_packets": sum(row.packet_successes for row in episodes),
        },
    }


def analyze_seed_cells(
    per_seed: dict[int, dict[str, dict[str, dict[str, object]]]],
    *, selected_fixed_arm: str,
) -> dict[str, object]:
    seed_estimands: dict[str, dict[str, dict[str, float]]] = {}
    for seed, arms in per_seed.items():
        seed_estimands[str(seed)] = {}
        for arm, cells in arms.items():
            means = [float(cell["mean_return"]) for cell in cells.values() if cell.get("episodes", 0)]
            if len(means) == 8:
                seed_estimands[str(seed)][arm] = {"P": float(np.mean(means)), "W": min(means)}
        if selected_fixed_arm in seed_estimands[str(seed)]:
            seed_estimands[str(seed)]["FIXED-BEST"] = seed_estimands[str(seed)][selected_fixed_arm].copy()
    arms = sorted(set.intersection(*(set(rows) for rows in seed_estimands.values())))
    summaries: dict[str, object] = {}
    for arm in arms:
        summaries[arm] = {
            estimand: student_t_interval(seed_estimands[str(seed)][arm][estimand] for seed in per_seed)
            for estimand in ("P", "W")
        }
    contrasts: dict[str, object] = {}
    comparisons = [
        (adaptive, "FIXED-BEST") for adaptive in ("LOCAL", "COORD")
    ] + [("COORD", "LOCAL")]
    for left, right in comparisons:
        if all(left in seed_estimands[str(seed)] and right in seed_estimands[str(seed)] for seed in per_seed):
            contrasts[f"{left}_minus_{right}"] = {
                estimand: student_t_interval(
                    seed_estimands[str(seed)][left][estimand] - seed_estimands[str(seed)][right][estimand]
                    for seed in per_seed
                ) for estimand in ("P", "W")
            }
    for control in ("COORD-SHUFFLE", "COORD-YOKED"):
        reference = f"{control}-REFERENCE"
        if all(reference in seed_estimands[str(seed)] and control in seed_estimands[str(seed)] for seed in per_seed):
            contrasts[f"COORD_minus_{control}"] = {
                estimand: student_t_interval(
                    seed_estimands[str(seed)][reference][estimand]
                    - seed_estimands[str(seed)][control][estimand]
                    for seed in per_seed
                ) for estimand in ("P", "W")
            }
    coupling = []
    for seed, arms_by_seed in per_seed.items():
        if "COORD" not in arms_by_seed or "LOCAL" not in arms_by_seed:
            continue
        differences = {}
        for mode in ("ON", "OFF"):
            differences[mode] = np.mean([
                float(arms_by_seed["COORD"][f"{tempo}_{mode}"]["mean_return"])
                - float(arms_by_seed["LOCAL"][f"{tempo}_{mode}"]["mean_return"])
                for tempo in ("ID", "SHORT", "LONG", "MIXED_NOISY")
            ])
        coupling.append(float(differences["ON"] - differences["OFF"]))
    return {
        "seed_estimands": seed_estimands, "estimand_intervals": summaries,
        "paired_contrasts": contrasts,
        "coupling_interaction": student_t_interval(coupling),
    }

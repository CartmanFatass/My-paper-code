"""Common-world conditional package contrasts; incomplete panels are never promoted."""

from experiments.candidates.energy_relay_availability.readout import paired
from experiments.candidates.uav_information_value.readout import distribution, number
from .constants import ARMS, HORIZON

CONTRASTS = (("L", "O"), ("L", "P"), ("O", "P"))
EXCLUDED = {"seed", "raw_bytes", "worker_wall_seconds", "worker_cpu_seconds", "worker_peak_rss_kib"}
PAIR_FIELDS = ("initial_state_sha256", "ground_bs_sha256", "user_xy_trace_sha256", "rng_state_stream_sha256")
RISK_FIELDS = ("cutoff_event_count_sum", "depletion_event_count_sum",
               "terminal_zero_service", "final300_persistent_reserve_members")


def summarize(rows, jobs, *, horizon=HORIZON):
    expected = {row["job_key"]: row for row in jobs}
    indexed = {row["job_key"]: row for row in rows}
    if len(expected) != len(jobs) or len(indexed) != len(rows) or set(indexed)-set(expected):
        raise ValueError("duplicate or unexpected evaluation world")
    for key, row in indexed.items():
        if any(row[field] != expected[key][field] for field in ("arm", "seed")):
            raise ValueError("world identity differs from the fixed plan")
    complete = len(rows) == len(jobs) and all(
        row["status"] == "completed" and row["actual_length"] == horizon for row in rows)
    groups = {arm: [row for row in rows if row["arm"] == arm and row["status"] == "completed"] for arm in ARMS}
    fields = sorted({field for panel in groups.values() for row in panel for field, value in row.items()
                     if number(value) and field not in EXCLUDED})
    panels = {arm: {
        "completed_worlds": len(panel),
        "zero_service_worlds": [r["seed"] for r in panel if r.get("zero_service")],
        "terminal_zero_service_worlds": [r["seed"] for r in panel if r.get("terminal_zero_service")],
        "metrics": {field: distribution([r[field] for r in panel if number(r.get(field))]) |
                    {"missing": sum(not number(r.get(field)) for r in panel)} for field in fields},
    } for arm, panel in groups.items()}
    contrasts, pairing, practical = {}, {}, {}
    pairing_failures = []
    if complete:
        by_arm = {arm: {row["seed"]: row for row in panel} for arm, panel in groups.items()}
        seeds = sorted(by_arm["P"])
        if any(sorted(panel) != seeds for panel in by_arm.values()):
            raise ValueError("arms lack the same unique common-world panel")
        pairing = {field: {str(seed): len({by_arm[arm][seed].get(field) for arm in ARMS}) == 1
                           and by_arm["P"][seed].get(field) is not None for seed in seeds}
                   for field in PAIR_FIELDS}
        pairing_failures = [{"field": field, "seed": int(seed)}
                            for field, worlds in pairing.items() for seed, equal in worlds.items() if not equal]
        complete = not pairing_failures
    if complete:
        for field in fields:
            contrasts[field] = {}
            for left, right in CONTRASTS:
                name = f"{left}-{right}"
                if any(not number(by_arm[arm][seed].get(field)) for arm in (left, right) for seed in seeds):
                    contrasts[field][name] = {"status": "not_comparable"}
                    continue
                delta = [by_arm[left][seed][field]-by_arm[right][seed][field] for seed in seeds]
                contrasts[field][name] = paired(delta, [0.] * len(delta)) | {
                    "positive": sum(v > 0 for v in delta), "negative": sum(v < 0 for v in delta),
                    "ties": sum(v == 0 for v in delta), "minimum": min(delta), "maximum": max(delta),
                    "by_seed": dict(zip(map(str, seeds), delta)),
                }
        for left, right in CONTRASTS:
            name = f"{left}-{right}"
            risks = {field: [seed for seed in seeds if by_arm[left][seed][field] > by_arm[right][seed][field]]
                     for field in RISK_FIELDS}
            reserve_delta = sum(by_arm[left][seed]["native_reserve_uav_step_fraction"]-
                                by_arm[right][seed]["native_reserve_uav_step_fraction"] for seed in seeds) / len(seeds)
            qos_delta = sum(by_arm[left][seed]["horizon_normalized_qos"]-
                            by_arm[right][seed]["horizon_normalized_qos"] for seed in seeds) / len(seeds)
            j_delta = sum(by_arm[left][seed]["raw_native_J"]-by_arm[right][seed]["raw_native_J"] for seed in seeds) / len(seeds)
            practical[name] = dict(additional_risk_worlds=risks, mean_reserve_exposure_delta=reserve_delta,
                                    mean_service_threshold_pass=qos_delta >= .01 and j_delta > 0,
                                    default_use_blocked=any(risks.values()) or reserve_delta > 0)
    return dict(status="complete" if complete else "incomplete", planned_jobs=len(jobs),
                completed_jobs=sum(map(len, groups.values())), missing_jobs=[key for key in expected if key not in indexed],
                failed_jobs=[r["job_key"] for r in rows if r["status"] != "completed"],
                panels=panels, contrasts=contrasts, pairing=pairing, pairing_failures=pairing_failures,
                practical=practical, n_train=1,
                estimand="total central-information finite H3000 deployment of fixed L/O/P packages",
                inference_unit="initial evaluation-world seed, conditional on one trained instance",
                evaluation_optimizer_updates=0,
                intervals="exploratory paired t95; no multiplicity adjustment or learning replication")

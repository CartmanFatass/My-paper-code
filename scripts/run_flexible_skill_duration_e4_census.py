"""FSD E4: unchanged renewal DP census; non-400 horizons are toy observations."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from time import perf_counter

START = perf_counter()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from envs.relay_corridor.config import RelayCorridorConfig
from envs.relay_corridor.references import dp_service_profile, enumerate_references


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--law", required=True, choices=("deterministic", "geometric", "lognormal"))
    parser.add_argument("--mode", required=True, choices=("calibration", "census"))
    parser.add_argument("--horizon", type=int, default=400)
    parser.add_argument("--seed", type=int, choices=(0,), default=0)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cold_start = perf_counter()
    config = RelayCorridorConfig(event_process="renewal", renewal_law=args.law, horizon=args.horizon)
    law = config.region_laws()[0]
    cap = min(law.dp_age_cap(args.horizon), args.horizon)
    mean, variance = law.mean(), law.variance()
    hazard = law.hazard_table(cap)
    law_record = dict(mean=mean, variance=variance, dp_age_cap=cap, hazard=hazard.tolist())
    if args.law == "lognormal":
        first, second, mass = law._moments()
        law_record.update(log_location=law.log_location, moment_support_cap=law.support_cap,
                          first_moment=first, second_moment=second, computed_mass=mass,
                          residual_mass=1.0 - mass)
        assert -1e-12 <= mass <= 1.0 + 1e-12, f"computed mass inconsistent: {mass}"
    cold_seconds = perf_counter() - cold_start
    assert abs(mean - 20.0) <= 1e-8 and variance >= -1e-10, f"law calibration inconsistent: {law_record}"
    assert np.isfinite(hazard).all() and ((hazard >= 0) & (hazard <= 1)).all(), f"invalid hazard: {hazard.tolist()}"
    summary = dict(config=asdict(config), law=law_record, launch_sha=args.launch_sha,
                   node=args.node, command=sys.argv, seed=args.seed, seed_active=False,
                   mode=args.mode, toy=args.horizon != 400, cold_seconds=cold_seconds,
                   mean_discrepancy=mean - 20.0, resources_unmeasured=["peak_rss"])
    summary["learner_exposure"] = dict(episodes=0, transitions=0, optimizer_updates=0,
                                       checkpoint_selection=0)
    if args.mode == "calibration":
        samples = [("switching", dict(renew_on_flag=True))]
        for stamp, periods in (("oracle", (1, 40)), ("open", (1, 40, None))):
            for period in periods:
                boundaries = () if period is None else range(period, args.horizon, period)
                samples.append((f"{stamp}_{period}", dict(stamp=stamp, boundaries=boundaries)))
        times = {}
        for name, kwargs in samples:
            started = perf_counter()
            service = dp_service_profile(hazard, args.horizon, config.n_roles, **kwargs)
            times[name] = perf_counter() - started
            assert np.isfinite(service).all(), "nonfinite calibration DP"
        summary.update(dp_seconds=times, age_states=len(hazard), dp_calls_per_census=36,
                       projection_seconds=2 * (cold_seconds + 36 * max(times.values())),
                       cost_law="2 * (cold_seconds + 36 * max(dp_seconds)); empirical heuristic")
    else:
        report = enumerate_references(config)
        summary.update(report.as_dict(), open_candidates=report.open_candidates)
        summary["fixed_improvement_over_k20"] = report.j_best_fixed_k - report.j_fixed_k[20]
        discrepancies = dict(greedy_minus_switch=report.j_greedy - report.j_switch,
                             open_max_minus_stored=max(r[2] for r in report.open_candidates) - report.j_open_best,
                             m_error=report.m - (report.j_switch - report.j_open_best),
                             m_dur_error=report.m_dur - (report.j_switch - report.j_best_fixed_k))
        if args.law == "deterministic":
            discrepancies["switch_minus_k20"] = report.j_switch - report.j_fixed_k[20]
        summary["discrepancies"] = discrepancies
        assert len(report.open_candidates) == 96, f"incomplete open-loop census: {len(report.open_candidates)}"
        assert all(abs(x) <= 1e-10 for x in discrepancies.values()), f"reference inconsistency: {discrepancies}"
        summary["gap_ordering"] = {
            key: "positive" if summary[key] > 1e-10 else "opposite" if summary[key] < -1e-10 else "unresolved"
            for key in ("m", "m_dur", "fixed_improvement_over_k20")
        }
    summary["wall_seconds_before_publication"] = perf_counter() - START
    summary["timing_window"] = "module body before numpy import through computation; excludes interpreter startup/output"
    summary["status"] = "COMPLETE"
    output_start = perf_counter()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(output_seconds=perf_counter() - output_start,
                          module_wall_seconds_through_output=perf_counter() - START)))


if __name__ == "__main__":
    main()

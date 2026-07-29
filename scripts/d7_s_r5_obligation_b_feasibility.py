"""D7.S R5 obligation B -- real source-state feasibility on the development topology.

Closes obligation B of Pro's R5 ruling: record, at every relevant check on
development topology 20260725, the total duties, covered duties, airborne UAVs,
action-bearing incumbents, eligible matching size, whether a full derangement
exists, and the reason for every exclusion.

This is a MEASUREMENT PROBE, not the R5 control. It rolls `constructive_mixed`
exactly as the audit does and only *observes* what a derangement would face at
each shared check. It never applies a derangement, never alters a duty map, and
writes nothing into the audit path.

Development topology only. `TOPOLOGY_SEED_DEV = 20260725` carries no scientific
reading, and this exercise is not conclusion-bearing.

Run from the repository root:
    C:\\Users\\fires\\.conda\\envs\\hmasd-amd-cpu\\python.exe scripts/d7_s_r5_obligation_b_feasibility.py
"""
import argparse
import itertools
import json
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import audit_d7_s_event_aligned as audit  # noqa: E402

TARGET_IDENTITY_TOL = 1e-6      # the registered geometric dedup tolerance


def _departing_for_charge(env, i):
    """True when the energy controller, not the duty, determines this UAV's
    action -- branch (b) of `scripted_source_actions`."""
    station_idx, _, distance = env._nearest_charging_station(i)
    if station_idx < 0:
        return False
    trigger = audit.dock_trigger_ratio_for_env(env, i, distance)
    return bool(audit.should_depart_for_charge(
        battery_ratio=float(env.uav_battery_ratios[i]), trigger_ratio=trigger))


def observe_check(env, duty_map, duty_positions):
    """One check-boundary observation. Returns the obligation-B row."""
    n_uavs = int(env.n_uavs)
    charging = np.asarray(env.uav_charging, dtype=bool)
    uav_to_duty = {u: d for d, u in duty_map.items()}

    total_duties = audit.N_RELAY_DUTIES + audit.N_SERVICE_DUTIES
    covered = sorted(duty_map.keys())
    airborne = [i for i in range(n_uavs) if not charging[i]]

    exclusions = Counter()
    action_bearing = []
    for i in range(n_uavs):
        if i not in uav_to_duty:
            exclusions["no_incumbent_duty"] += 1
            continue
        if charging[i]:
            exclusions["charging"] += 1
            continue
        if _departing_for_charge(env, i):
            exclusions["duty_overridden_by_station_return"] += 1
            continue
        action_bearing.append(i)

    # Condition 6 needs a candidate duty pool; the pool is the duties held by
    # action-bearing incumbents, which is the retained covered set restricted to
    # agents whose duty actually drives them.
    pool = {uav_to_duty[u] for u in action_bearing}
    allowed = {}
    for u in action_bearing:
        d0 = uav_to_duty[u]
        z0 = np.asarray(duty_positions[d0], dtype=float)[:2]
        opts = set()
        for d in pool:
            if d == d0:
                continue
            if np.linalg.norm(np.asarray(duty_positions[d], dtype=float)[:2] - z0) > TARGET_IDENTITY_TOL:
                opts.add(d)
        if opts:
            allowed[u] = opts
        else:
            exclusions["no_geometrically_distinct_alternative"] += 1

    eligible = sorted(allowed)
    # Restrict options to the eligible pool, then test Hall's condition.
    elig_duties = {uav_to_duty[u] for u in eligible}
    allowed_r = {u: (allowed[u] & elig_duties) for u in eligible}
    empty_after = [u for u in eligible if not allowed_r[u]]
    for _ in empty_after:
        exclusions["no_alternative_within_eligible_pool"] += 1
    eligible = [u for u in eligible if allowed_r[u]]
    elig_duties = {uav_to_duty[u] for u in eligible}
    allowed_r = {u: (allowed_r[u] & elig_duties) for u in eligible}
    eligible = [u for u in eligible if allowed_r[u]]

    n_e = len(eligible)
    witness = None
    if n_e < 2:
        exists = False
        witness = {"reason": "fewer_than_two_eligible", "n_eligible": n_e}
    else:
        idx = {u: k for k, u in enumerate(eligible)}
        duty_idx = {d: k for k, d in enumerate(sorted(elig_duties))}
        sets = [set(duty_idx[d] for d in allowed_r[u]) for u in eligible]
        w = None
        for size in range(1, n_e + 1):
            for S in itertools.combinations(range(n_e), size):
                nbr = set()
                for k in S:
                    nbr |= sets[k]
                if len(nbr) < len(S):
                    w = {"reason": "hall_violation",
                         "S_uavs": [eligible[k] for k in S],
                         "neighbourhood_size": len(nbr)}
                    break
            if w:
                break
        exists = w is None
        witness = w
        del idx

    return {
        "total_duties": total_duties,
        "covered_duties": len(covered),
        "airborne_uavs": len(airborne),
        "action_bearing_incumbents": len(action_bearing),
        "eligible_matching_size": n_e,
        "full_derangement_exists": bool(exists),
        "infeasibility_witness": witness,
        "exclusions": dict(exclusions),
    }


def run_episode(config, *, topology_seed, coords, coord_hash, idx, max_steps):
    ep_seed = audit._derived_seed(topology_seed=topology_seed, block="calibration",
                                  idx=idx, tag="episode_seed")
    en_seed = audit._derived_seed(topology_seed=topology_seed, block="calibration",
                                  idx=idx, tag="energy_seed")
    uw_seed = audit.user_world_seed(topology_seed=topology_seed, block="calibration",
                                    episode_index=idx)
    env = audit.build_pinned_env(config, episode_seed=ep_seed, coords=coords,
                                 coord_hash=coord_hash, energy_stage="S3",
                                 user_world_seed=uw_seed)
    audit.apply_energy_profile(env, audit.draw_energy_permutation(energy_seed=en_seed))

    duty_map = audit.initial_duty_map()
    centroids = None
    rows = []
    for step_index in range(max_steps):
        duty_positions, centroids_next = audit.compute_duty_positions(env, centroids)
        if step_index % audit.DELTA == 0:
            row = observe_check(env, duty_map, duty_positions)
            row["step_index"] = step_index
            row["episode_index"] = idx
            rows.append(row)
        step = audit.step_once(env, duty_map=duty_map, service_centroids=centroids,
                               schedule="constructive_mixed", step_index=step_index)
        duty_map = step["duty_map"]
        centroids = step["service_centroids"]
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=4)
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    config = audit.build_config()
    seed = audit.TOPOLOGY_SEED_DEV
    coords, coord_hash = audit.build_topology_template(config, topology_seed=seed)
    print(f"development topology {seed}  coord_hash={coord_hash[:16]}...")
    print(f"DELTA={audit.DELTA}  duties={audit.N_RELAY_DUTIES + audit.N_SERVICE_DUTIES}")

    rows = []
    for idx in range(args.episodes):
        r = run_episode(config, topology_seed=seed, coords=coords, coord_hash=coord_hash,
                        idx=idx, max_steps=args.steps)
        rows.extend(r)
        feas = sum(1 for x in r if x["full_derangement_exists"])
        print(f"  episode {idx}: checks={len(r)}  derangement_feasible={feas}"
              f"  infeasible={len(r) - feas}")

    total = len(rows)
    feasible = sum(1 for r in rows if r["full_derangement_exists"])
    print("\n=== obligation B summary ===")
    print(f"checks_observed={total}")
    print(f"full_derangement_exists={feasible}  ({100.0*feasible/max(total,1):.1f}%)")
    print(f"infeasible={total - feasible}")

    ec = Counter()
    for r in rows:
        for k, v in r["exclusions"].items():
            ec[k] += v
    print("\nexclusions by reason (agent-checks):")
    for k, v in ec.most_common():
        print(f"  {k:42s} {v}")

    wc = Counter(r["infeasibility_witness"]["reason"]
                 for r in rows if r["infeasibility_witness"])
    print("\ninfeasibility witnesses:")
    for k, v in wc.most_common():
        print(f"  {k:42s} {v}")

    sizes = Counter(r["eligible_matching_size"] for r in rows)
    print("\neligible matching size distribution:")
    for k in sorted(sizes):
        print(f"  n_eligible={k:2d}  checks={sizes[k]}")

    cov = Counter(r["covered_duties"] for r in rows)
    print("\ncovered-duty count distribution:")
    for k in sorted(cov):
        print(f"  covered={k:2d}  checks={cov[k]}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"topology_seed": seed, "coord_hash": coord_hash,
                       "delta": audit.DELTA, "rows": rows}, fh, indent=2)
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

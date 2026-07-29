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


def _present_and_acting(env, i):
    """Eligibility conditions 1 and 3 -- present and active at the boundary, and
    not failed, terminal or otherwise non-acting.

    Asserted rather than assumed (Pro 2026-07-29). The registered Scenario 7 env
    exposes no failure or termination flag per UAV; every attribute probed here
    is optional, so a future env that gains one is handled instead of silently
    treated as healthy.
    """
    for attr, bad in (("uav_failed", True), ("uav_terminated", True),
                      ("uav_active", False), ("uav_alive", False)):
        arr = getattr(env, attr, None)
        if arr is None:
            continue
        try:
            if bool(np.asarray(arr, dtype=bool)[i]) == bad:
                return False
        except (IndexError, TypeError, ValueError):
            continue
    return True


def eligibility(env, duty_map, duty_positions):
    """THE frozen six-condition eligibility construction, in one place.

    Obligations B, C, D and E must all use this exact function. Two copies of an
    eligibility rule is how the control and its witness end up sharing a
    narrowed definition -- the R4 failure, one obligation later.

    Returns the sets the derangement operates on, plus the exclusion tally.
    """
    n_uavs = int(env.n_uavs)
    charging = np.asarray(env.uav_charging, dtype=bool)
    # KNOWN LOSSY (measured 2026-07-29, ruling pending). This inversion drops a
    # duty whenever one UAV holds two, which `constructive_mixed_update`'s REJOIN
    # branch produces at ~33% of check boundaries. It is written exactly as the
    # audit's own action rule writes it (audit_d7_s_event_aligned.py:2330) --
    # DELIBERATELY, so this probe sees the duty set the source actually flies,
    # not a repaired one. Silently fixing it here would make the probe disagree
    # with the instrument and hide the defect instead of measuring it.
    # Evidence: docs/research/cdc/EVIDENCE_NOTES/
    #           20260729_D7_S_ONE_UAV_CAN_HOLD_TWO_DUTIES.md
    uav_to_duty = {u: d for d, u in duty_map.items()}

    # ---- The six-condition eligibility definition, asserted rather than assumed.
    # FROZEN RULE (Pro 2026-07-29, option 2 of the two offered): the eligible set
    # is established ONCE from the six conditions. A later empty adjacency is
    # MATCHING INFEASIBILITY, not a reason to shrink the treated set. Iterating a
    # pruning loop to a fixed point would choose whom to treat on the basis of
    # feasibility, which preferentially treats the easy agents -- the exact
    # selection effect the post-start abort rule exists to prevent.
    exclusions = Counter()
    action_bearing = []
    for i in range(n_uavs):
        if not _present_and_acting(env, i):          # conditions 1 and 3
            exclusions["absent_failed_or_terminal"] += 1
            continue
        if i not in uav_to_duty:                     # condition 4
            exclusions["no_incumbent_duty"] += 1
            continue
        if charging[i]:                              # condition 2
            exclusions["charging"] += 1
            continue
        if _departing_for_charge(env, i):            # condition 5
            exclusions["duty_overridden_by_station_return"] += 1
            continue
        action_bearing.append(i)

    # The retained covered-duty set is the set of duties held by action-bearing
    # incumbents -- that is what the derangement permutes. Condition 6 is
    # evaluated against it, once.
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
        if opts:                                     # condition 6
            allowed[u] = opts
        else:
            exclusions["no_geometrically_distinct_alternative"] += 1

    eligible = sorted(allowed)                       # FROZEN from here on
    elig_duties = {uav_to_duty[u] for u in eligible}
    allowed_r = {u: (allowed[u] & elig_duties) for u in eligible}

    return {
        "uav_to_duty": uav_to_duty,
        "action_bearing": action_bearing,
        "pool": pool,
        "eligible": eligible,
        "elig_duties": elig_duties,
        "allowed": allowed_r,
        "exclusions": exclusions,
        "charging": charging,
        "n_uavs": n_uavs,
    }


def observe_check(env, duty_map, duty_positions):
    """One check-boundary observation. Returns the obligation-B row."""
    el = eligibility(env, duty_map, duty_positions)
    uav_to_duty = el["uav_to_duty"]
    exclusions = el["exclusions"]
    eligible = el["eligible"]
    allowed_r = el["allowed"]
    elig_duties = el["elig_duties"]
    charging = el["charging"]
    n_uavs = el["n_uavs"]

    total_duties = audit.N_RELAY_DUTIES + audit.N_SERVICE_DUTIES
    covered = sorted(duty_map.keys())
    airborne = [i for i in range(n_uavs) if not charging[i]]

    n_e = len(eligible)
    witness = None
    if n_e < 2:
        exists = False
        witness = {"reason": "fewer_than_two_eligible", "abs_S": n_e}
    else:
        duty_list = sorted(elig_duties)
        duty_idx = {d: k for k, d in enumerate(duty_list)}
        sets = [set(duty_idx[d] for d in allowed_r[u]) for u in eligible]
        w = None
        for size in range(1, n_e + 1):
            for S in itertools.combinations(range(n_e), size):
                nbr = set()
                for k in S:
                    nbr |= sets[k]
                if len(nbr) < len(S):
                    # Full witness: S, N(S), |S|, |N(S)| -- a size alone cannot
                    # be checked against the graph that produced it.
                    w = {"reason": "hall_violation",
                         "S": [eligible[k] for k in S],
                         "N_S": [duty_list[k] for k in sorted(nbr)],
                         "abs_S": len(S), "abs_N_S": len(nbr)}
                    break
            if w:
                break
        exists = w is None
        witness = w

    return {
        "total_duties": total_duties,
        "covered_duties": len(covered),
        "airborne_uavs": len(airborne),
        "action_bearing_incumbents": len(el["action_bearing"]),
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

"""Did the REJOIN branch ever fire on the R4 population?

Step H (`30403322062`) is a mechanically clean R4 artifact that ran at
`a00612ad`, one commit before the source-assignment repair `23fecff3`. Its
disposition rests on the commit graph rather than on a measurement, because the
artifact records no rejoin field. See
`docs/research/cdc/EVIDENCE_NOTES/20260729_H_RETURNED_AND_CANNOT_CLOSE_ROUND_4.md`.

There is a decidable question underneath it. The repair's scope is Pro's (b1),
the REJOIN branch, plus a universal final assertion. **If a roll produces ZERO
REJOIN events, the repaired branch never executed, so the pre-repair and
post-repair trajectories through that roll are identical.** A zero here is
therefore evidence about H itself, not merely about this code.

This is a DIAGNOSTIC. It counts events and asserts nothing about any estimand:
no margin is read, no limb is certified, no branch is recorded, no artifact is
written into the audit path. It rolls `constructive_mixed` exactly as
`roll_prefix_and_find_event` does and reports counters.

A zero result is only meaningful if this probe COULD have seen a nonzero, so it
reports steps rolled and charging occurrences alongside, and refuses to call a
zero informative when no UAV ever charged.

Run from the repository root:
    python scripts/d7_s_r4_rejoin_exposure_probe.py --topologies 20260734
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import audit_d7_s_event_aligned as audit  # noqa: E402


def roll_one_episode(config, *, topology_seed, coords, coord_hash, idx, block, max_steps):
    ep_seed = audit._derived_seed(topology_seed=topology_seed, block=block,
                                  idx=idx, tag="episode_seed")
    en_seed = audit._derived_seed(topology_seed=topology_seed, block=block,
                                  idx=idx, tag="energy_seed")
    uw_seed = audit.user_world_seed(topology_seed=topology_seed, block=block,
                                    episode_index=idx)
    env = audit.build_pinned_env(config, episode_seed=ep_seed, coords=coords,
                                 coord_hash=coord_hash, energy_stage="S3",
                                 user_world_seed=uw_seed)
    audit.apply_energy_profile(env, audit.draw_energy_permutation(energy_seed=en_seed))

    duty_map = audit.initial_duty_map()
    centroids = None
    stats = {"rejoins": 0, "leaves": 0, "charging_steps": 0, "steps": 0,
             "refusals": 0}
    audit.reset_injectivity_check_count()
    for step_index in range(max_steps):
        try:
            step = audit.step_once(env, duty_map=duty_map, service_centroids=centroids,
                                   schedule="constructive_mixed", step_index=step_index)
        except audit.SourceAssignmentInvariantError:
            # Conclusive, and it dominates: it means the repaired code refuses
            # where the historical code would have produced a lossy answer.
            stats["refusals"] += 1
            break
        stats["rejoins"] += len(step["rejoin_uavs"])
        stats["leaves"] += len(step["leave_uavs"])
        stats["charging_steps"] += int(
            np.count_nonzero(np.asarray(env.uav_charging, dtype=bool)))
        stats["steps"] += 1
        duty_map = step["duty_map"]
        centroids = step["service_centroids"]
    stats["injectivity_checks"] = audit.injectivity_check_count()
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topologies", type=int, nargs="+",
                    default=list(audit.TOPOLOGY_SEEDS_R4))
    ap.add_argument("--episodes", type=int, default=2)
    ap.add_argument("--steps", type=int, default=audit.T_E_MAX)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    config = audit.build_config()
    totals = {"rejoins": 0, "leaves": 0, "charging_steps": 0, "steps": 0,
              "refusals": 0, "injectivity_checks": 0}
    rows = []
    print(f"R4 rejoin-exposure probe -- {len(args.topologies)} topologies x "
          f"{args.episodes} episodes x up to {args.steps} steps")
    for seed in args.topologies:
        coords, coord_hash = audit.build_topology_template(config, topology_seed=seed)
        for block in ("calibration", "audit"):
            for idx in range(args.episodes):
                s = roll_one_episode(config, topology_seed=seed, coords=coords,
                                     coord_hash=coord_hash, idx=idx, block=block,
                                     max_steps=args.steps)
                s.update({"topology_seed": seed, "block": block, "episode_index": idx})
                rows.append(s)
                for k in totals:
                    totals[k] += s[k]
                print(f"  {seed} {block:11s} ep{idx}: steps={s['steps']:4d} "
                      f"leaves={s['leaves']:2d} rejoins={s['rejoins']:2d} "
                      f"charging_steps={s['charging_steps']:5d} "
                      f"checks={s['injectivity_checks']:5d} refusals={s['refusals']}")

    print("\n=== totals ===")
    for k in ("steps", "leaves", "rejoins", "charging_steps", "injectivity_checks",
              "refusals"):
        print(f"  {k:20s} {totals[k]}")

    print()
    if totals["refusals"]:
        verdict = "R4_REJOIN_PROBE_REFUSED"
        print(f"{verdict}: the repaired code REFUSED on this population. That is "
              "conclusive, and it means the historical code was producing a lossy "
              "answer at the same boundary. H is contaminated.")
    elif totals["charging_steps"] == 0:
        verdict = "R4_REJOIN_PROBE_INCONCLUSIVE"
        print(f"{verdict}: no UAV ever charged, so zero rejoins is arithmetic over "
              "an empty set and says nothing about the REJOIN branch.")
    elif totals["rejoins"] == 0:
        verdict = "R4_REJOIN_PROBE_ZERO_WITH_POWER"
        print(f"{verdict}: {totals['charging_steps']} charging steps occurred and "
              f"{totals['injectivity_checks']} injectivity checks ran, yet ZERO "
              "REJOIN events. The repaired (b1) branch never executed, so on this "
              "sample the pre-repair and post-repair trajectories coincide.")
        print("This is evidence about H, not just about this code. It is NOT by "
              "itself a rehabilitation: it covers the episodes rolled here, at "
              "this episode count, and the formal artifact must carry its own "
              "roll_power.")
    else:
        verdict = "R4_REJOIN_PROBE_FIRED"
        print(f"{verdict}: {totals['rejoins']} REJOIN events on the R4 population. "
              "The defective branch was reachable and reached, so H ran code that "
              "could double-assign at exactly these boundaries. H is contaminated.")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"verdict": verdict, "totals": totals, "rows": rows,
                       "episodes": args.episodes, "max_steps": args.steps}, fh, indent=2)
        print(f"\nwrote {args.out}")
    print(f"\n{verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

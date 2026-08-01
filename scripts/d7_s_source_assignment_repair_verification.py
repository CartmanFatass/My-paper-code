"""Did the source-assignment repair actually remove the defect it was for?

A green test suite says the constructed cases behave. It does not say the
33% of check boundaries measured on the development topology went away -- that
was a rate, and a rate is what has to be re-measured. Two samples cannot
separate a cause from a coin, and neither can a unit test.

Pre-repair, measured at stage commit 1b17dfb0 and again at 78c02b86:

    duty map non-injective at 33.6% of STEPS
    duty map non-injective at 33.3% of CHECK boundaries
    all 8 development episodes affected, max excess 1
    absorbing: every episode enters the state and never leaves

Post-repair this script expects 0.0% on both, and it expects the PHANTOM count
to be non-zero -- because phantoms were always there, and the repair's point is
that they are now visible instead of silently counted as coverage.

The map-level assertion is fail-closed inside production, so a failed repair
surfaces here as SourceAssignmentInvariantError rather than as a bad number.
That is caught and reported rather than allowed to look like a crash.

Development feedback, runs locally.
Conclusion-bearing nothing: no registered quantity is read.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audit_d7_s_event_aligned as audit  # noqa: E402


def _holders_doubled(duty_map):
    holders = list(duty_map.values())
    seen, doubled = set(), set()
    for u in holders:
        if u in seen:
            doubled.add(u)
        seen.add(u)
    return sorted(doubled)


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
    stat = {"steps": 0, "checks": 0, "dup_steps": 0, "dup_checks": 0,
            "phantom_steps": 0, "phantom_total": 0, "refusal": None,
            "phantom_tags": {}, "phantom_uavs": {},
            # Zero CHARGING phantoms has TWO explanations: docking removes the
            # duty from the map (the mechanism), or nobody ever docked (no
            # evidence at all). These separate them.
            "leaves": 0, "rejoins": 0, "charging_steps": 0,
            "holder_charging_steps": 0}
    for step_index in range(max_steps):
        is_check = (step_index % audit.DELTA == 0)
        doubled = _holders_doubled(duty_map)
        stat["steps"] += 1
        if is_check:
            stat["checks"] += 1
        if doubled:
            stat["dup_steps"] += 1
            if is_check:
                stat["dup_checks"] += 1
        try:
            step = audit.step_once(env, duty_map=duty_map, service_centroids=centroids,
                                   schedule="constructive_mixed", step_index=step_index)
        except audit.SourceAssignmentInvariantError as exc:
            stat["refusal"] = f"step {step_index}: {exc.reason}: {exc}"
            break
        stat["leaves"] += len(step["leave_uavs"])
        stat["rejoins"] += len(step["rejoin_uavs"])
        charging_now = step["charging_before"]
        if bool(charging_now.any()):
            stat["charging_steps"] += 1
        if any(bool(charging_now[u]) for u in duty_map.values()):
            stat["holder_charging_steps"] += 1
        covered = step["executable_covered_duties"]
        phantoms = set(duty_map) - set(covered)
        if phantoms:
            stat["phantom_steps"] += 1
            stat["phantom_total"] += len(phantoms)
            # WHICH source made each phantom a phantom. A count alone invites a
            # guess about the mechanism, and guessing from source rather than
            # measuring has produced two confident wrong explanations in this
            # line of work.
            for d in phantoms:
                holder = duty_map[d]
                tag = step["action_provenance"].get(holder, ("ABSENT", None))[0]
                stat["phantom_tags"][tag] = stat["phantom_tags"].get(tag, 0) + 1
                stat["phantom_uavs"][holder] = stat["phantom_uavs"].get(holder, 0) + 1
        duty_map = step["duty_map"]
        centroids = step["service_centroids"]
    return stat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=8)
    ap.add_argument("--steps", type=int, default=400)
    args = ap.parse_args()

    config = audit.build_config()
    seed = audit.TOPOLOGY_SEED_DEV
    coords, coord_hash = audit.build_topology_template(config, topology_seed=seed)
    print(f"development topology {seed}  coord_hash={coord_hash[:16]}...")
    print(f"DELTA={audit.DELTA}  duties={audit.N_RELAY_DUTIES + audit.N_SERVICE_DUTIES}"
          f"  episodes={args.episodes}  steps={args.steps}")

    tot = {"steps": 0, "checks": 0, "dup_steps": 0, "dup_checks": 0,
           "phantom_steps": 0, "phantom_total": 0,
           "leaves": 0, "rejoins": 0, "charging_steps": 0,
           "holder_charging_steps": 0}
    all_tags, refusals = {}, []
    for idx in range(args.episodes):
        s = run_episode(config, topology_seed=seed, coords=coords,
                        coord_hash=coord_hash, idx=idx, max_steps=args.steps)
        for k in tot:
            tot[k] += s[k]
        for t, c in s["phantom_tags"].items():
            all_tags[t] = all_tags.get(t, 0) + c
        if s["refusal"]:
            refusals.append(f"episode {idx}: {s['refusal']}")
        extra = ""
        if s["phantom_steps"]:
            extra = (f"  tags={dict(sorted(s['phantom_tags'].items()))}"
                     f"  uavs={dict(sorted(s['phantom_uavs'].items()))}")
        print(f"  episode {idx}: steps={s['steps']} dup_steps={s['dup_steps']} "
              f"dup_checks={s['dup_checks']}/{s['checks']} "
              f"phantom_steps={s['phantom_steps']}{extra}")

    dup_step_rate = tot["dup_steps"] / max(tot["steps"], 1)
    dup_check_rate = tot["dup_checks"] / max(tot["checks"], 1)
    print("\n--- totals ---")
    print(f"steps={tot['steps']}  checks={tot['checks']}")
    print(f"non-injective at steps  : {tot['dup_steps']}  ({dup_step_rate:.4%})")
    print(f"non-injective at checks : {tot['dup_checks']}  ({dup_check_rate:.4%})")
    print(f"steps with >=1 phantom  : {tot['phantom_steps']}  "
          f"(total phantom duty-steps {tot['phantom_total']})")
    print(f"phantom holder sources  : {dict(sorted(all_tags.items()))}")
    print(f"LEAVE events            : {tot['leaves']}      "
          f"REJOIN events: {tot['rejoins']}")
    print(f"steps with a UAV docked : {tot['charging_steps']}")
    print(f"steps with a HOLDER docked: {tot['holder_charging_steps']}   "
          f"<- must be 0 if docking removes the duty from the map")
    if refusals:
        print("\nFAIL-CLOSED REFUSALS (the repair did not hold):")
        for r in refusals:
            print("  " + r)
        # A refusal DOMINATES the power guard below. Measured on the
        # topology-level paired negative: with the (b1) skip removed the run
        # refused at step 910, and because the exception breaks the episode
        # loop before that step's counters are added, the REJOIN count stayed
        # 0 and the power guard reported INCONCLUSIVE -- labelling the
        # strongest possible detection as "this says nothing either way".
        # Under-powered means "no evidence"; a refusal IS evidence.
        print("\nREPAIR_VERIFICATION_FAILED")
        return 1

    # THE POWER GUARD, and the reason this script exists in its current form.
    #
    # The first version reported REPAIR_VERIFICATION_OK on 3200 steps with
    # ZERO REJOIN events. The repaired branch is inside REJOIN handling, so a
    # run with no REJOIN events cannot observe the repair working OR failing --
    # 0.0000% non-injective was arithmetic about an empty set, not evidence.
    #
    # That is precisely the defect this whole line of work exists to remove:
    # a check that cannot fail for the reason it exists. It appeared here, in
    # the script written to verify the fix for it. The onset of charging on
    # this topology is around step 900, so 400-step episodes stop before any
    # battery depletes enough to dock.
    #
    # A run without the events is now INCONCLUSIVE and exits non-zero. Silence
    # must not be able to look like success.
    if tot["rejoins"] == 0:
        print("\nREPAIR_VERIFICATION_INCONCLUSIVE: zero REJOIN events in "
              f"{tot['steps']} steps. The repaired branch never executed, so "
              "this run says nothing about it either way. Raise --steps past "
              "the charging onset (~900 on this topology).")
        return 2

    ok = (tot["dup_steps"] == 0 and tot["dup_checks"] == 0 and not refusals)
    print("\nREPAIR_VERIFICATION_OK" if ok else "\nREPAIR_VERIFICATION_FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

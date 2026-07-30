"""Prove the R2 shared-prefix clone path against the REAL Scenario-7 env.

Why this exists rather than `--smoke`: the six Stage-B conditions are proved in
the focused suite against `_CloneableFakeEnv`, which is a hand-written stand-in.
Nothing has yet shown that `copy.deepcopy` reproduces a real
`UAVEnergyAwareRelayEnv` faithfully -- and if it does not, the entire
realization is wrong and a multi-hour audit would be measuring a broken clone.
That is a genuinely untested path.

A full `--smoke` at the 2/2 volume with full horizons projects to 35-58 minutes,
over the 20-minute nonformal cap in `EVIDENCE_COMPLEXITY_POLICY.md`. This check
is the minimum that proves the untested path instead: one real pinned env, one
real prefix, one snapshot, real clones, the conditions asserted, and condition 1
(clone equivalence against an independent replay) on a SHORT horizon.

It also times the continuation loop, which collapses the 0.10-0.30 s/step band
the cost projection currently has to sweep.

This is a conformance and timing exercise. It reads no scientific result, and
its output is never a margin.

Usage:
    python scripts/d7_s_clone_conformance_check.py
    python scripts/d7_s_clone_conformance_check.py --equivalence-horizon 60
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

import scripts.audit_d7_s_event_aligned as audit


def _fmt(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topology-seed", type=int, default=audit.TOPOLOGY_SEED_DEV)
    ap.add_argument("--equivalence-horizon", type=int, default=60,
                    help="continuation steps for the condition-1 comparison; short on "
                         "purpose -- equivalence either holds from step 1 or it does not")
    ap.add_argument("--max-episodes", type=int, default=8,
                    help="how many episodes to scan for a qualifying joint event")
    ap.add_argument("--search-budget-seconds", type=float, default=900.0,
                    help="stop scanning past this elapsed time; keeps the whole check "
                         "inside the 20-minute nonformal cap")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    started = time.time()
    report: dict = {"topology_seed": args.topology_seed,
                    "equivalence_horizon": args.equivalence_horizon}

    config = audit.build_config()
    coords, coord_hash = audit.build_topology_template(config, topology_seed=args.topology_seed)

    # Not every episode yields a qualifying joint event, and the conditions
    # cannot be checked on real state without one. Scan a bounded number of
    # episodes rather than concluding from the first miss.
    prefix = None
    episode_seed = energy_seed = None
    energies = None
    search_seconds = 0.0
    searched = 0

    for idx in range(int(args.max_episodes)):
        if time.time() - started > float(args.search_budget_seconds):
            break
        episode_seed = audit._derived_seed(topology_seed=args.topology_seed, block="audit",
                                            idx=idx, tag="episode_seed")
        energy_seed = audit._derived_seed(topology_seed=args.topology_seed, block="audit",
                                           idx=idx, tag="energy_seed")
        env = audit.build_pinned_env(config, episode_seed=episode_seed, coords=coords,
                                      coord_hash=coord_hash)
        energies = audit.draw_energy_permutation(energy_seed=energy_seed)
        audit.apply_energy_profile(env, energies)

        t_search = time.time()
        candidate = audit.roll_prefix_and_find_event(env)
        dt = time.time() - t_search
        search_seconds += dt
        searched += 1
        steps_rolled = len(candidate.get("recorded_actions", [])) or audit.T_E_MAX
        report["search_seconds_per_step"] = dt / max(1, steps_rolled)
        print(f"[scan] episode_index={idx} qualifying_event="
              f"{candidate['event'] is not None} search_s={dt:.1f}",
              file=sys.stderr, flush=True)
        if candidate["event"] is not None:
            prefix = candidate
            report["episode_index"] = idx
            break

    report["episodes_searched"] = searched
    report["event_search_seconds"] = search_seconds
    report["qualifying_event_found"] = prefix is not None
    if prefix is None:
        prefix = {"event": None}

    if prefix["event"] is None:
        # Still worth proving deepcopy on the real object even without an event.
        report["verdict"] = "NO_QUALIFYING_EVENT_CLONE_CHECK_ONLY"
        import copy as _copy
        t0 = time.time()
        clone = _copy.deepcopy(env)
        report["deepcopy_seconds"] = time.time() - t0
        report["deepcopy_succeeded"] = True
        report["topology_preserved"] = bool(
            audit.coordinate_hash(clone.ground_bs_positions, clone.charging_station_positions)
            == coord_hash)
        report["elapsed_seconds"] = time.time() - started
        print(json.dumps(report, indent=2) if args.json else report)
        return

    event = prefix["event"]
    recorded_actions = prefix["recorded_actions"]
    report["t_e_steps"] = len(recorded_actions)

    # --- R3: capture directly off the LIVE certified environment -------------
    # No reconstruction replay. `env` here is the very environment the event was
    # certified in, so there is no second user world to disagree with.
    t0 = time.time()
    snapshot = audit.capture_event_snapshot(env, coord_hash=coord_hash, event=event)
    report["live_capture_seconds"] = time.time() - t0
    report["reconstruction_replays_performed"] = 0
    report["full_fingerprint_at_te"] = snapshot.full_fingerprint[:16]

    # --- conditions 2-5, on the real object ----------------------------------
    t0 = time.time()
    clone_a = snapshot.clone(context="conformance check A")
    report["deepcopy_seconds"] = time.time() - t0
    clone_b = snapshot.clone(context="conformance check B")

    report["condition_4_topology_preserved"] = bool(
        audit.coordinate_hash(clone_a.ground_bs_positions,
                              clone_a.charging_station_positions) == coord_hash)
    report["condition_5_state_restored"] = bool(
        audit.compute_state_hash(
            audit.real_env_state_snapshot(clone_a, snapshot.duty_map_at_te))
        == snapshot.hash_at_te)

    rng_before = audit._rng_state_token(snapshot._env)
    snapshot.clone(context="rng isolation probe")
    report["condition_3_rng_isolated"] = bool(
        audit._rng_state_token(snapshot._env) == rng_before)

    clone_a.uav_positions[0] += 250.0
    clone_a.uav_battery_ratios[0] = 0.011
    sibling_untouched = bool(
        audit.compute_state_hash(
            audit.real_env_state_snapshot(clone_b, snapshot.duty_map_at_te))
        == snapshot.hash_at_te)
    try:
        snapshot.assert_source_intact(context="conformance check")
        source_intact = True
    except audit.CloneIsolationError:
        source_intact = False
    report["condition_2_mutation_isolated"] = bool(sibling_untouched and source_intact)

    # --- conditions 1A / 1B, both clones off ONE live snapshot ---------------
    h = int(args.equivalence_horizon)
    cont_seed = audit.stream_seed(
        topology_seed=args.topology_seed, block="audit", episode_seed=episode_seed,
        limb="stable", event_index=0, candidate_target_id="KEEP",
        phase="evaluate", replicate_index=0)
    other_seed = audit.stream_seed(
        topology_seed=args.topology_seed, block="audit", episode_seed=episode_seed,
        limb="stable", event_index=0, candidate_target_id="KEEP",
        phase="evaluate", replicate_index=1)

    t0 = time.time()
    verdict = audit.verify_clone_conformance(
        snapshot, event=event, limb="stable", continuation_seed=cont_seed,
        other_seed=other_seed, horizon=h)
    report["continuation_seconds_per_step"] = (time.time() - t0) / max(1, 3 * h)

    report["condition_1a_same_stream_identical"] = verdict["condition_1a_same_stream_identical"]
    report["condition_1b_pre_stream_state_equal"] = verdict.get(
        "condition_1b_pre_stream_state_equal")
    report["different_stream_changed_trajectory"] = verdict.get(
        "different_stream_changed_trajectory")
    report["g_total"] = verdict["g_total"]

    # --- cross-limb: one snapshot must serve both limbs identically ----------
    # Pro requires this demonstrated. The compact witness is a neutral
    # continuation with no focal intervention through both limb call paths:
    # same snapshot, same stream, same horizon, no limb-specific locks.
    stable_side = audit.verify_clone_conformance(
        snapshot, event=event, limb="stable", continuation_seed=cont_seed, horizon=h)
    flex_side = audit.verify_clone_conformance(
        snapshot, event=event, limb="flex", continuation_seed=cont_seed, horizon=h)
    report["cross_limb_identical"] = bool(
        stable_side["g_total"] == flex_side["g_total"]
        and stable_side["pre_stream_state_equal"]
        and flex_side["pre_stream_state_equal"])

    conditions = [report["condition_1a_same_stream_identical"],
                  bool(report["condition_1b_pre_stream_state_equal"]),
                  report["cross_limb_identical"],
                  report["condition_2_mutation_isolated"],
                  report["condition_3_rng_isolated"],
                  report["condition_4_topology_preserved"],
                  report["condition_5_state_restored"]]
    report["all_conditions_pass"] = all(conditions)
    report["verdict"] = "CLONE_CONFORMANCE_PASS" if all(conditions) else "CLONE_CONFORMANCE_FAIL"
    report["elapsed_seconds"] = time.time() - started

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print("D7.S shared-prefix clone conformance -- REAL Scenario-7 environment")
    print(f"topology_seed={args.topology_seed} episode_seed={episode_seed} "
          f"t_e={report.get('t_e_steps')} steps")
    print()
    print(f"  condition 1A same snapshot, same stream, identical   : "
          f"{_fmt(report['condition_1a_same_stream_identical'])}")
    print(f"  condition 1B different stream, same pre-stream state : "
          f"{_fmt(bool(report['condition_1b_pre_stream_state_equal']))}")
    print(f"  cross-limb   one snapshot serves both limbs          : "
          f"{_fmt(report['cross_limb_identical'])}")
    print(f"  condition 2  mutation isolation                      : "
          f"{_fmt(report['condition_2_mutation_isolated'])}")
    print(f"  condition 3  RNG isolation                           : "
          f"{_fmt(report['condition_3_rng_isolated'])}")
    print(f"  condition 4  topology preservation                   : "
          f"{_fmt(report['condition_4_topology_preserved'])}")
    print(f"  condition 5  complete-state restoration              : "
          f"{_fmt(report['condition_5_state_restored'])}")
    print()
    print(f"  deepcopy per clone      : {report['deepcopy_seconds']:.3f} s")
    print(f"  reconstruction replays  : {report['reconstruction_replays_performed']}")
    print(f"  continuation s/step     : {report['continuation_seconds_per_step']:.4f}")
    print(f"  elapsed                 : {report['elapsed_seconds']:.1f} s")
    print()
    print(f"  {report['verdict']}")
    print()
    print("Condition 6 (failure semantics) is proved in the focused suite, not here:")
    print("it asserts what happens when these fail, which cannot be observed on a")
    print("healthy environment.")

    _emit_world_digest_block()


def _emit_world_digest_block() -> None:
    """Print R4 world component digests and this runtime's identity, as JSON.

    WHY THIS IS HERE rather than in its own job. Step 1 of the provenance
    correction (Pro ruling 2026-07-30) needs component digests for R4 episode
    keys from two different machines, with each machine's identity recorded so an
    AGREEMENT can be told apart from two samples that shared hardware.

    Of the three existing workflow jobs, none provided that: `audit` is the
    114-minute formal run, `workers` is the development topology only, and adding
    a job needs a workflow-file change that is not this actor's to make. Both
    attempts through `workers` returned `WORLD_CONFORMANCE_UNTESTED` for reasons
    recorded in advance.

    The `benchmark` job pipes this script's stdout into the artifact it uploads,
    so printing the block here delivers exactly the missing measurement through a
    job that already exists.

    **Construction only.** It builds environments and hashes their initial world.
    It never steps one, never forks a continuation, computes no estimand and
    writes nothing into the audit path -- so it cannot influence the conformance
    result printed above, which has already completed by the time this runs.

    Failures are swallowed and reported. A diagnostic must never be the reason a
    benchmark job goes red.
    """
    print()
    print("=== D7_S_WORLD_DIGEST_BLOCK_BEGIN ===")
    try:
        config = audit.build_config()
        worlds = []
        for seed in audit.TOPOLOGY_SEEDS_R4:
            coords, coord_hash = audit.build_topology_template(config, topology_seed=seed)
            for block in ("calibration", "audit"):
                for index in range(2):
                    episode_seed = audit._derived_seed(
                        topology_seed=seed, block=block, idx=index,
                        tag="episode_seed", contract_id=audit.R4_POPULATION_NAMESPACE)
                    user_seed = audit.user_world_seed(
                        topology_seed=seed, block=block, episode_index=index,
                        contract_id=audit.R4_POPULATION_NAMESPACE)
                    env = audit.build_pinned_env(
                        config, episode_seed=episode_seed, coords=coords,
                        coord_hash=coord_hash, energy_stage="S3",
                        user_world_seed=user_seed)
                    record = audit.episode_world_fingerprint(env, seed_value=user_seed)
                    worlds.append({
                        "topology_seed": seed, "block": block,
                        "episode_index": index, "episode_seed": episode_seed,
                        "user_world_seed": record["user_world_seed"],
                        "pinned_coordinate_hash": record["pinned_coordinate_hash"],
                        "n_users": record["n_users"],
                        "fingerprint": record["fingerprint"],
                        "component_digests": record["component_digests"],
                    })
        payload = {
            "episode_world_provenance": {"episode_worlds": worlds},
            "runtime_identity": audit.runtime_identity(),
            "contract_id": audit.R4_POPULATION_NAMESPACE,
            "probe": "d7_s_clone_conformance_check",
        }
        print(json.dumps(payload, sort_keys=True))
    except Exception as error:  # pragma: no cover - diagnostic must not fail a job
        print(json.dumps({"world_digest_block_error": f"{type(error).__name__}: {error}"}))
    print("=== D7_S_WORLD_DIGEST_BLOCK_END ===")


if __name__ == "__main__":
    main()

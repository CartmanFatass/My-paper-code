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

    # --- the canonical replay + snapshot -------------------------------------
    t0 = time.time()
    snapshot = audit.materialize_event_snapshot(
        config, coords=coords, coord_hash=coord_hash, episode_seed=episode_seed,
        recorded_actions=recorded_actions, expected_hash=event["hash_at_te"],
        duty_map_at_te=event["duty_map_at_te"], energy_permutation=energies)
    report["canonical_replay_seconds"] = time.time() - t0
    report["replay_seconds_per_step"] = (report["canonical_replay_seconds"]
                                          / max(1, len(recorded_actions)))

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

    # --- condition 1: clone vs independent replay ----------------------------
    h = int(args.equivalence_horizon)
    cont_seed = audit.stream_seed(
        topology_seed=args.topology_seed, block="audit", episode_seed=episode_seed,
        limb="stable", event_index=0, candidate_target_id="KEEP",
        phase="evaluate", replicate_index=0)

    def _run(e) -> dict:
        bc, bd = audit._baseline_masks(e)
        out = audit.fork_continuation(
            e, duty_map_at_te=event["duty_map_at_te"],
            duty_positions_at_te=event["duty_positions_at_te"],
            service_centroids_at_te=event["service_centroids_at_te"],
            schedule="constructive_mixed", horizon=h, continuation_seed=cont_seed)
        return audit.window_g_from_step_metrics(
            out["step_metrics"], out["qos_user_steps"], h=h,
            baseline_cutoff_mask=bc, baseline_depletion_mask=bd)

    t0 = time.time()
    g_clone = _run(snapshot.clone(context="equivalence clone"))
    clone_cont_seconds = time.time() - t0
    report["continuation_seconds_per_step"] = clone_cont_seconds / max(1, h)

    reference_env = audit.replay_prefix(
        config, coords=coords, coord_hash=coord_hash, episode_seed=episode_seed,
        recorded_actions=recorded_actions, expected_hash=event["hash_at_te"],
        duty_map_at_te=event["duty_map_at_te"], energy_permutation=energies)
    g_ref = _run(reference_env)

    report["clone_g_total"] = float(g_clone["g_total"])
    report["reference_g_total"] = float(g_ref["g_total"])
    report["condition_1_clone_equivalence"] = bool(
        g_clone["g_total"] == g_ref["g_total"]
        and np.array_equal(g_clone["g_series"], g_ref["g_series"]))
    report["max_abs_series_delta"] = float(
        np.max(np.abs(g_clone["g_series"] - g_ref["g_series"]))) if h else 0.0

    conditions = [report["condition_1_clone_equivalence"],
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
    print(f"  condition 1  clone equivalence vs independent replay : "
          f"{_fmt(report['condition_1_clone_equivalence'])}")
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
    print(f"  replay      s/step      : {report['replay_seconds_per_step']:.4f}")
    print(f"  continuation s/step     : {report['continuation_seconds_per_step']:.4f}")
    print(f"  elapsed                 : {report['elapsed_seconds']:.1f} s")
    print()
    print(f"  {report['verdict']}")
    print()
    print("Condition 6 (failure semantics) is proved in the focused suite, not here:")
    print("it asserts what happens when these fail, which cannot be observed on a")
    print("healthy environment.")


if __name__ == "__main__":
    main()

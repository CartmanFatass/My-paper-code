"""D7.S R5 obligation C -- same-support witness.

D7_S_R5_DEVELOPMENT_OBLIGATIONS_NOT_A_RESULT

Closes obligation C: applying the derangement changes ONLY eligible
agent-to-duty ownership. The covered-duty set, the number of assignments, the
non-eligible incumbent pairs and every energy/charging decision are unchanged.

Development topology 20260725 only. Emits no D_A, no branch, no population
identity, and performs no inference.

INDEPENDENCE. The witness never asks the control whether it behaved. It
recomputes every property from traces:
  * the incoming and outgoing duty maps;
  * the real environment's own action vectors under each map, whose element [3]
    is the dock-request bit -- so the charging decision is read off the action
    the environment would execute, not off a flag this module maintains.
The five mutations perturb the produced map or actions while the witness code
stays fixed, which is what stops the control and its test sharing one narrowed
definition of "same support".

DEPENDENCE, declared. Like obligation B this harness imports
`audit_d7_s_event_aligned` and steps real environments through its helpers. It
is a probe under the current audit/source realization, not an independent
verification of that realization.

Run:
    C:\\Users\\fires\\.conda\\envs\\hmasd-amd-cpu\\python.exe scripts/d7_s_r5_obligation_c_same_support.py
"""
import argparse
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import audit_d7_s_event_aligned as audit                      # noqa: E402
import d7_s_r5_obligation_a_proof as oba                      # noqa: E402
import d7_s_r5_obligation_b_feasibility as obb                # noqa: E402

DOCK_BIT = 3

# A mutation can return this instead of a (map, actions) pair to say "this
# negative cannot be built in this state, and here is why". It is NOT a pass:
# a negative that is never constructible is a negative that never ran.
UNCONSTRUCTIBLE = "__unconstructible__"


def solve_derangement(el, duty_positions, env):
    """Minimum-transit derangement over the FROZEN eligible sets.

    Forbidden edges are logically absent -- the incumbent edge plus every
    geometrically identical target -- and reach the solver through
    `forbidden_from_allowed`, so the graph solved is the graph the witness sees.
    """
    eligible = el["eligible"]
    if len(eligible) < 2:
        return None, {"reason": "fewer_than_two_eligible", "abs_S": len(eligible)}
    duties = sorted(el["elig_duties"])
    n = len(eligible)
    if len(duties) != n:
        return None, {"reason": "cardinality_mismatch", "abs_S": n, "abs_N_S": len(duties)}

    didx = {d: k for k, d in enumerate(duties)}
    allowed_idx = [set(didx[d] for d in el["allowed"][u]) for u in eligible]
    w = oba.hall_witness(n, allowed_idx)
    if w is not None:
        return None, {"reason": "hall_violation",
                      "S": [eligible[k] for k in w["S"]],
                      "N_S": [duties[k] for k in w["N_S"]],
                      "abs_S": w["abs_S"], "abs_N_S": w["abs_N_S"]}

    agent_pos = [np.asarray(env.uav_positions[u], dtype=float) for u in eligible]
    duty_pos = [np.asarray(duty_positions[d], dtype=float) for d in duties]
    C = oba.cost_matrix(agent_pos, duty_pos)
    if not oba.sentinel_dominates(C, n):
        return None, {"reason": "sentinel_not_dominant"}
    forb = oba.forbidden_from_allowed(n, allowed_idx)
    pairs, _ = oba.canonical_min_derangement(C, forb, n)
    if pairs is None:
        return None, {"reason": "solver_refused"}
    if any(p in forb for p in pairs):
        return None, {"reason": "solver_returned_forbidden_edge"}
    return {duties[j]: eligible[i] for i, j in pairs}, None


def apply_derangement(duty_map, assignment):
    m1 = dict(duty_map)
    for d, u in assignment.items():
        m1[d] = u
    return m1


def witness_same_support(m0, m1, el, actions0, actions1):
    """Independent same-support witness. Every clause is recomputed from the
    maps and the environment's own action vectors."""
    elig_duties = set(el["elig_duties"])
    eligible = set(el["eligible"])
    n_uavs = el["n_uavs"]

    changed_duties = {d for d in m0 if m0.get(d) != m1.get(d)}
    changed_actions = {
        i for i in range(n_uavs)
        if not np.allclose(np.asarray(actions0[audit.agent_name(i)], dtype=float),
                           np.asarray(actions1[audit.agent_name(i)], dtype=float),
                           atol=0.0, rtol=0.0)
    }
    dock_equal = all(
        float(np.asarray(actions0[audit.agent_name(i)])[DOCK_BIT])
        == float(np.asarray(actions1[audit.agent_name(i)])[DOCK_BIT])
        for i in range(n_uavs))

    return {
        "covered_set_unchanged": set(m1.keys()) == set(m0.keys()),
        "assignment_count_unchanged": len(m1) == len(m0),
        "noneligible_pairs_unchanged": all(m1.get(d) == m0.get(d)
                                           for d in m0 if d not in elig_duties),
        "charging_decisions_unchanged": dock_equal,
        "only_eligible_ownership_changed": changed_duties <= elig_duties,
        "only_eligible_actions_changed": changed_actions <= eligible,
        "assigned_uavs_unchanged": set(m1.values()) == set(m0.values()),
    }


def _all_ok(w):
    return all(w.values())


# --- paired negatives: perturb the PRODUCT, never the witness ---------------

def _mut_uncovered_duty(m0, m1, el, a0, a1):
    """Let the derangement take a duty that was not covered."""
    m = dict(m1)
    uncovered = [d for d in range(audit.N_RELAY_DUTIES + audit.N_SERVICE_DUTIES)
                 if d not in m0]
    if not uncovered or not el["eligible"]:
        return None
    victim = sorted(el["elig_duties"])[0]
    m[uncovered[0]] = m.pop(victim)
    return m, a1


def _mut_move_noneligible(m0, m1, el, a0, a1):
    """Move an incumbent the treatment is not allowed to touch.

    Swapping two non-eligible duties is a NO-OP whenever both are held by the
    SAME UAV -- which happens here, because `constructive_mixed_update`'s REJOIN
    branch can give one UAV two duties (see the evidence note
    20260729_D7_S_ONE_UAV_CAN_HOLD_TWO_DUTIES). The swap then produces a map
    identical to the unmutated one and the witness correctly reports no
    violation. That is not a witness hole and it is not a caught mutation; it is
    a state where this negative cannot be constructed at all, and the harness
    scores it in its own bucket rather than laundering it into either column.
    """
    non_elig = [d for d in m0 if d not in el["elig_duties"]]
    if len(non_elig) < 2:
        return None
    a, b = non_elig[0], non_elig[1]
    if m1.get(a) == m1.get(b):
        return UNCONSTRUCTIBLE, "both non-eligible duties share one holder"
    m = dict(m1)
    m[a], m[b] = m[b], m[a]
    return m, a1


def _mut_drop_covered(m0, m1, el, a0, a1):
    """Shrink the covered-duty set."""
    if not m1:
        return None
    m = dict(m1)
    m.pop(sorted(m)[0])
    return m, a1


def _mut_flip_charging(m0, m1, el, a0, a1):
    """Alter one UAV's charging decision."""
    a = {k: np.asarray(v, dtype=float).copy() for k, v in a1.items()}
    key = audit.agent_name(0)
    a[key][DOCK_BIT] = 1.0 - a[key][DOCK_BIT]
    return m1, a


def _mut_touch_ineligible_action(m0, m1, el, a0, a1):
    """Change the flight action of a UAV outside the eligible set."""
    outside = [i for i in range(el["n_uavs"]) if i not in set(el["eligible"])]
    if not outside:
        return None
    a = {k: np.asarray(v, dtype=float).copy() for k, v in a1.items()}
    key = audit.agent_name(outside[0])
    a[key][0] = a[key][0] + 0.25
    return m1, a


MUTATIONS = (
    ("derangement takes an uncovered duty", _mut_uncovered_duty),
    ("non-eligible incumbent moved", _mut_move_noneligible),
    ("covered-duty count shrinks", _mut_drop_covered),
    ("charging decision altered", _mut_flip_charging),
    ("ineligible UAV's action changed", _mut_touch_ineligible_action),
)


def run_episode(config, *, coords, coord_hash, idx, max_steps, mutation_hits,
                mutation_reasons):
    ep_seed = audit._derived_seed(topology_seed=audit.TOPOLOGY_SEED_DEV,
                                  block="calibration", idx=idx, tag="episode_seed")
    en_seed = audit._derived_seed(topology_seed=audit.TOPOLOGY_SEED_DEV,
                                  block="calibration", idx=idx, tag="energy_seed")
    uw_seed = audit.user_world_seed(topology_seed=audit.TOPOLOGY_SEED_DEV,
                                    block="calibration", episode_index=idx)
    env = audit.build_pinned_env(config, episode_seed=ep_seed, coords=coords,
                                 coord_hash=coord_hash, energy_stage="S3",
                                 user_world_seed=uw_seed)
    audit.apply_energy_profile(env, audit.draw_energy_permutation(energy_seed=en_seed))

    duty_map = audit.initial_duty_map()
    centroids = None
    checks = passed = refused = 0
    failures = Counter()

    for step_index in range(max_steps):
        duty_positions, _ = audit.compute_duty_positions(env, centroids)
        if step_index % audit.DELTA == 0:
            el = obb.eligibility(env, duty_map, duty_positions)
            assignment, refusal = solve_derangement(el, duty_positions, env)
            if assignment is None:
                refused += 1
            else:
                checks += 1
                m1 = apply_derangement(duty_map, assignment)
                a0 = audit.scripted_source_actions(env, duty_map=duty_map,
                                                   duty_positions=duty_positions)
                a1 = audit.scripted_source_actions(env, duty_map=m1,
                                                   duty_positions=duty_positions)
                w = witness_same_support(duty_map, m1, el, a0, a1)
                if _all_ok(w):
                    passed += 1
                else:
                    for k, v in w.items():
                        if not v:
                            failures[k] += 1
                for name, mut in MUTATIONS:
                    try:
                        out = mut(duty_map, m1, el, a0, a1)
                    except audit.SourceAssignmentInvariantError as exc:
                        # The source-assignment repair made action synthesis
                        # FAIL-CLOSED, so a mutation that produces a
                        # non-injective map is now refused instead of returning
                        # a lossy answer. That mutation could not be BUILT, so
                        # it is neither caught nor missed -- the same scoring
                        # rule that already covers the explicit UNCONSTRUCTIBLE
                        # return, and the rule that surfaced the defect in the
                        # first place. Scoring it as a hit would credit the
                        # probe for a mutation it never made.
                        mutation_hits[name + " :: UNCONSTRUCTIBLE"] += 1
                        mutation_reasons[name].add(f"refused: {exc.reason}")
                        continue
                    if out is None:
                        continue
                    mm, ma = out
                    if mm is UNCONSTRUCTIBLE:
                        mutation_hits[name + " :: UNCONSTRUCTIBLE"] += 1
                        mutation_reasons[name].add(ma)
                        continue
                    wm = witness_same_support(duty_map, mm, el, a0, ma)
                    if not _all_ok(wm):
                        mutation_hits[name] += 1
                    else:
                        mutation_hits[name + " :: MISSED"] += 1
        step = audit.step_once(env, duty_map=duty_map, service_centroids=centroids,
                               schedule="constructive_mixed", step_index=step_index)
        duty_map = step["duty_map"]
        centroids = step["service_centroids"]

    return checks, passed, refused, failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=3)
    ap.add_argument("--steps", type=int, default=1200)
    args = ap.parse_args()

    config = audit.build_config()
    coords, coord_hash = audit.build_topology_template(
        config, topology_seed=audit.TOPOLOGY_SEED_DEV)
    print(f"development topology {audit.TOPOLOGY_SEED_DEV}  "
          f"coord_hash={coord_hash[:16]}...  DELTA={audit.DELTA}")

    total = total_pass = total_refused = 0
    all_fail = Counter()
    mutation_hits = Counter()
    mutation_reasons = defaultdict(set)
    for idx in range(args.episodes):
        c, p, r, f = run_episode(config, coords=coords, coord_hash=coord_hash,
                                 idx=idx, max_steps=args.steps,
                                 mutation_hits=mutation_hits,
                                 mutation_reasons=mutation_reasons)
        total += c
        total_pass += p
        total_refused += r
        all_fail.update(f)
        print(f"  episode {idx}: deranged_checks={c} same_support_pass={p} refused={r}")

    print("\n=== obligation C summary ===")
    print(f"deranged checks   {total}")
    print(f"same-support pass {total_pass}")
    print(f"refused (support) {total_refused}")
    ok = (total > 0 and total_pass == total)
    if all_fail:
        print("\nwitness clauses that failed:")
        for k, v in all_fail.most_common():
            print(f"  {k:38s} {v}")

    print("\n=== paired negatives -- each MUST go red ===")
    for name, _ in MUTATIONS:
        hits = mutation_hits.get(name, 0)
        missed = mutation_hits.get(name + " :: MISSED", 0)
        unbuildable = mutation_hits.get(name + " :: UNCONSTRUCTIBLE", 0)
        # An unconstructible negative is NOT a pass. It is a state where the
        # perturbation could not be expressed, which is a fact about the source,
        # not evidence about the witness.
        caught = hits > 0 and missed == 0 and unbuildable == 0
        print(f"  {name:38s} caught={hits:5d} missed={missed:5d} "
              f"unconstructible={unbuildable:5d}  clean={caught}")
        for r in sorted(mutation_reasons.get(name, ())):
            print(f"      unconstructible because: {r}")
        ok &= caught

    print(f"\nOBLIGATION_C_CHECKS_PASS={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

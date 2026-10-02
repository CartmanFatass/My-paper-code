"""A genuinely suspended upstream branch: generator locals preserve the mid-sweep cursor."""
from __future__ import annotations

import copy
import time

from ..b02 import evidence as e
from ..b02 import search as old

PREFIX = 36


def new_state(candidate, rank, share, initial_count):
    return {"rank": rank, "candidate_index": candidate["index"], "kind": candidate["kind"], "k": candidate["k"],
            "positions_xyz": copy.deepcopy(candidate["positions_xyz"]),
            "start_reward": float(candidate["contract_reward"]), "reward": float(candidate["contract_reward"]),
            "potential": float(candidate["potential"]), "share": share, "used": 0, "xy_step_index": 0,
            "moved": False, "uav": None, "move_index": None, "converged": False, "done": False,
            "accepted_descent": 0, "accepted_plateau": 0, "initial_count": initial_count,
            "history": [{"evaluations": initial_count, "stage": "start", "start": rank,
                         "candidate_index": candidate["index"], "contract_reward": float(candidate["contract_reward"]),
                         "potential": float(candidate["potential"])}]}


def suspended_branch(env, p, state):
    import numpy as np
    position = np.array(state["positions_xyz"], dtype=float)
    reward, potential = state["reward"], state["potential"]
    used, stage_index = 0, 0
    share = state["share"]
    while used < share:
        moved = False
        step = p.XY_STEPS_M[stage_index]
        moves = ((step, 0.0, 0.0), (-step, 0.0, 0.0), (0.0, step, 0.0), (0.0, -step, 0.0),
                 (0.0, 0.0, p.Z_STEP_M), (0.0, 0.0, -p.Z_STEP_M))
        for uav in range(env.n_uavs):
            for move_index, move in enumerate(moves):
                if used >= share:
                    break
                trial = position.copy()
                trial[uav] += move
                trial = p._clip_positions(env, trial)
                if np.array_equal(trial, position):
                    continue
                info = p.static_evaluate(env, trial, allow_a2a=True)
                used += 1
                trial_potential = p.plateau_potential(env, True)
                trial_reward = float(info["contract_reward"])
                stage = None
                if trial_reward > reward + p.IMPROVEMENT_TOL:
                    stage = "descent"
                elif (abs(trial_reward - reward) <= p.IMPROVEMENT_TOL
                      and trial_potential < potential - p.POTENTIAL_TOL):
                    stage = "plateau"
                if stage is not None:
                    position, reward, potential = trial, trial_reward, trial_potential
                    moved = True
                    state["accepted_" + stage] += 1
                    state["history"].append({"evaluations": state["initial_count"] + used, "stage": stage,
                                             "start": state["rank"], "contract_reward": reward, "potential": potential,
                                             "uav": uav, "step_m": step, "move": [float(v) for v in move]})
                state.update(positions_xyz=position.copy(), reward=reward, potential=potential, used=used,
                             xy_step_index=stage_index, moved=moved, uav=uav, move_index=move_index)
                # Acceptance and potential are complete before another branch touches env.
                # Resumption continues after this yield inside the SAME Python for/while loops.
                yield state
            if used >= share:
                break
        if used >= share:
            break
        if not moved:
            if stage_index + 1 < len(p.XY_STEPS_M):
                stage_index += 1
            else:
                state["converged"] = True
                break
    state.update(done=True, used=used, xy_step_index=stage_index, positions_xyz=position.copy(),
                 reward=reward, potential=potential)


def advance(generator, queries):
    for _ in range(queries):
        try:
            next(generator)
        except StopIteration:
            break


def record(state, p):
    return {"start": state["rank"], "candidate_index": state["candidate_index"], "kind": state["kind"],
            "k": state["k"], "start_reward": state["start_reward"], "final_reward": state["reward"],
            "share": state["share"], "evaluations": state["used"], "converged": state["converged"],
            "accepted_descent": state["accepted_descent"], "accepted_plateau": state["accepted_plateau"],
            "final_xy_step_m": p.XY_STEPS_M[state["xy_step_index"]],
            "began_at_evaluation": state["initial_count"], "ended_at_evaluation": state["initial_count"] + state["used"]}


def choose(env, p, world, arm):
    if arm in ("G", "P"):
        return old.prepare_and_choose(env, p, world, arm, None)
    if arm != "Q":
        raise ValueError("fixed G/Q/P arms only")
    import numpy as np
    initial, users, bs = env.uav_positions.copy(), env.user_positions.copy(), env.ground_bs_positions[0].copy()
    t = time.perf_counter()
    flat = p.search_placement(env, False, 3000, np.random.default_rng(world))
    timing = {"flat_seconds": time.perf_counter() - t}
    t = time.perf_counter()
    report = {}
    candidates = p.build_candidates(env, np.random.default_rng(world), True, report=report)
    extra = np.array(flat.positions_xyz, dtype=float).reshape(6, 3)
    if not np.array_equal(p._clip_positions(env, extra), extra):
        raise ValueError("illegal flat incumbent")
    duplicate = next((c["index"] for c in candidates if np.round(np.asarray(c["positions_xyz"]), 6).tobytes()
                      == np.round(extra, 6).tobytes()), None)
    candidates.append({"index": len(candidates), "kind": "flat_result_incumbent", "k": None,
                       "positions_xyz": extra, "duplicate_of": duplicate})
    if len(candidates) > 3000:
        raise ValueError("full initial list exceeds original budget")
    report["extra_candidates"] = 1
    for c in candidates:
        info = p.static_evaluate(env, c["positions_xyz"], allow_a2a=True)
        c.update(contract_reward=float(info["contract_reward"]), coverage_backhauled=float(info["coverage_backhauled"]),
                 potential=p.plateau_potential(env, True))
    ranked, shares = old.ranked_shares(candidates)
    timing["relay_construction_initial_scoring_seconds"] = time.perf_counter() - t
    states = [new_state(candidates[i], r, shares[r], len(candidates)) for r, i in enumerate(ranked)]
    generators = [suspended_branch(env, p, s) for s in states]
    t = time.perf_counter()
    for g in generators:
        advance(g, PREFIX)
    prefix_states = [e.plain(copy.deepcopy(s)) for s in states]
    rewards = [s["reward"] for s in states]
    rank = max(range(3), key=lambda r: (rewards[r], -r))
    timing["all_prefixes_choice_seconds"] = time.perf_counter() - t
    t = time.perf_counter()
    for _ in generators[rank]:
        pass
    timing["selected_suffix_seconds"] = time.perf_counter() - t
    selected = record(states[rank], p)
    fb = selected["final_reward"] < candidates[ranked[0]]["contract_reward"] - 1e-12
    positions = np.array(candidates[ranked[0]]["positions_xyz"] if fb else states[rank]["positions_xyz"], dtype=float)
    t = time.perf_counter()
    metadata = p.static_evaluate(env, positions, allow_a2a=True)
    perm = p.assign_targets(initial, positions)
    timing["final_metadata_matching_seconds"] = time.perf_counter() - t
    return {"world": world, "arm": arm, "initial_positions_xyz": initial.tolist(), "user_positions_xy": users.tolist(),
            "bs_xyz": bs.tolist(), "flat": old.search_json(flat),
            "relay": {"candidates": e.plain(candidates), "candidates_evaluated": len(candidates), "candidate_report": report,
                      "starts": [record(s, p) for s in states], "history": sum([s["history"] for s in states], []),
                      "evaluations": len(candidates) + sum(s["used"] for s in states)},
            "ranked_indices": ranked, "original_shares": shares, "prefix_states": prefix_states,
            "prefix_rewards": rewards, "prefix_query_counts": [s["used"] for s in prefix_states], "prefix_queries": PREFIX,
            "requested_rank": rank, "selected_branch": selected, "fallback": fb,
            "executed_origin": "rank0_initial" if fb else f"rank{rank}_final", "positions_xyz": positions.tolist(),
            "target_permutation": perm.tolist(), "assigned_targets_xyz": positions[perm].tolist(),
            "static_info": e.plain(metadata), "timing": timing, "features": None, "predicted_gains": None}

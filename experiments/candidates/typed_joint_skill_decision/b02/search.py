"""One original-share branch, using the upstream candidate/scoring/geometry functions."""
from __future__ import annotations

import time

from . import model
from .evidence import plain


def ranked_shares(candidates, budget=3000):
    if len(candidates) > budget or len(candidates) < 3:
        raise ValueError("all initial candidates and exactly three starts must fit")
    ranked = sorted(range(len(candidates)), key=lambda i: (-candidates[i]["contract_reward"], i))[:3]
    remaining = budget - len(candidates)
    return ranked, [remaining // 3 + int(r < remaining % 3) for r in range(3)]


def branch(env, p, candidate, rank, share, initial_count):
    """Verbatim descent semantics of search_placement, with a precomputed three-start share."""
    import numpy as np
    position = np.array(candidate["positions_xyz"], dtype=float)
    reward, potential = float(candidate["contract_reward"]), float(candidate["potential"])
    used, stage_index, converged = 0, 0, False
    accepted = {"descent": 0, "plateau": 0}
    history = [{"evaluations": initial_count, "stage": "start", "start": rank,
                "candidate_index": candidate["index"], "contract_reward": reward, "potential": potential}]
    while used < share:
        moved = False
        step = p.XY_STEPS_M[stage_index]
        moves = ((step, 0.0, 0.0), (-step, 0.0, 0.0), (0.0, step, 0.0), (0.0, -step, 0.0),
                 (0.0, 0.0, p.Z_STEP_M), (0.0, 0.0, -p.Z_STEP_M))
        for uav in range(env.n_uavs):
            for move in moves:
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
                    accepted[stage] += 1
                    history.append({"evaluations": initial_count + used, "stage": stage, "start": rank,
                                    "contract_reward": reward, "potential": potential,
                                    "uav": uav, "step_m": step, "move": [float(v) for v in move]})
            if used >= share:
                break
        if used >= share:
            break
        if not moved:
            if stage_index + 1 < len(p.XY_STEPS_M):
                stage_index += 1
            else:
                converged = True
                break
    record = {"start": rank, "candidate_index": candidate["index"], "kind": candidate["kind"],
              "k": candidate["k"], "start_reward": candidate["contract_reward"], "final_reward": reward,
              "share": share, "evaluations": used, "converged": converged,
              "accepted_descent": accepted["descent"], "accepted_plateau": accepted["plateau"],
              "final_xy_step_m": p.XY_STEPS_M[stage_index], "began_at_evaluation": initial_count,
              "ended_at_evaluation": initial_count + used}
    return position, record, history


def full_search(env, p, world):
    import numpy as np
    t = time.perf_counter()
    flat = p.search_placement(env, False, 3000, np.random.default_rng(world))
    flat_seconds = time.perf_counter() - t
    t = time.perf_counter()
    relay = p.search_placement(env, True, 3000, np.random.default_rng(world),
                               extra_candidates=[flat.positions_xyz], extra_kind="flat_result_incumbent")
    return flat, relay, {"flat_seconds": flat_seconds, "relay_full_seconds": time.perf_counter() - t}


def search_json(result):
    data = result.to_json()
    for c, source in zip(data["candidates"], result.candidates):
        c["potential"] = float(source["potential"])
    return plain(data)


def prepare_and_choose(env, p, world, arm, state):
    import numpy as np
    initial = env.uav_positions.copy()
    users = env.user_positions.copy()
    bs = env.ground_bs_positions[0].copy()
    timing = {}
    if arm == "P":
        flat, relay, timing = full_search(env, p, world)
        candidates = relay.candidates[:relay.candidates_evaluated]
    else:
        t = time.perf_counter()
        flat = p.search_placement(env, False, 3000, np.random.default_rng(world))
        timing["flat_seconds"] = time.perf_counter() - t
        t = time.perf_counter()
        report = {}
        candidates = p.build_candidates(env, np.random.default_rng(world), True, report=report)
        extra = np.array(flat.positions_xyz, dtype=float).reshape(6, 3)
        if not np.array_equal(p._clip_positions(env, extra), extra):
            raise ValueError("illegal flat incumbent")
        key = np.round(extra, 6).tobytes()
        duplicate = next((c["index"] for c in candidates
                          if np.round(np.asarray(c["positions_xyz"], dtype=float), 6).tobytes() == key), None)
        candidates.append({"index": len(candidates), "kind": "flat_result_incumbent", "k": None,
                           "positions_xyz": extra, "duplicate_of": duplicate})
        if len(candidates) > 3000:
            raise ValueError("declared full initial candidate list exceeds budget")
        report["extra_candidates"] = 1
        for c in candidates:
            info = p.static_evaluate(env, c["positions_xyz"], allow_a2a=True)
            c.update(contract_reward=float(info["contract_reward"]),
                     coverage_backhauled=float(info["coverage_backhauled"]),
                     potential=p.plateau_potential(env, True))
        timing["relay_construction_initial_scoring_seconds"] = time.perf_counter() - t
    ranked, shares = ranked_shares(candidates)
    t = time.perf_counter()
    xs = ([model.features(candidates[index], rank, initial, users, bs, p.assign_targets)
           for rank, index in enumerate(ranked)] if arm == "L" else None)
    timing["learned_features_matching_seconds"] = time.perf_counter() - t if arm == "L" else None
    prediction = None
    t = time.perf_counter()
    if arm == "L":
        prediction = model.predict(xs, state).tolist()
        rank = model.choose_rank([candidates[i]["contract_reward"] for i in ranked], prediction)
    elif arm == "G":
        rank = 0
    elif arm == "P":
        rank = relay.best_start["start"]
    else:
        raise ValueError("only G/L/P are actual arms")
    timing["choice_inference_seconds"] = time.perf_counter() - t
    if arm == "P":
        positions = relay.positions_xyz.copy()
        selected = relay.best_start
        history = relay.history
        relay_json = search_json(relay)
        use_fallback = False
    else:
        t = time.perf_counter()
        positions, selected, history = branch(env, p, candidates[ranked[rank]], rank, shares[rank], len(candidates))
        timing["selected_branch_seconds"] = time.perf_counter() - t
        use_fallback = model.fallback(selected["final_reward"], candidates[ranked[0]]["contract_reward"])
        if use_fallback:
            positions = np.array(candidates[ranked[0]]["positions_xyz"], dtype=float)
        relay_json = {"candidates": plain(candidates), "candidate_report": report,
                      "candidates_evaluated": len(candidates), "starts": [selected], "history": history,
                      "evaluations": len(candidates) + selected["evaluations"]}
    t = time.perf_counter()
    # The original final metadata evaluation and original matching are paid by every arm.
    final_info = p.static_evaluate(env, positions, allow_a2a=True)
    perm = p.assign_targets(initial, positions)
    timing["final_metadata_matching_seconds"] = time.perf_counter() - t
    return {"world": world, "arm": arm, "initial_positions_xyz": initial.tolist(),
            "user_positions_xy": users.tolist(), "bs_xyz": bs.tolist(), "flat": search_json(flat),
            "relay": relay_json, "ranked_indices": ranked, "original_shares": shares,
            "features": xs, "predicted_gains": prediction, "requested_rank": rank,
            "selected_branch": plain(selected), "fallback": use_fallback,
            "executed_origin": "rank0_initial" if use_fallback else f"rank{rank}_final",
            "positions_xyz": positions.tolist(), "target_permutation": perm.tolist(),
            "assigned_targets_xyz": positions[perm].tolist(), "static_info": plain(final_info), "timing": timing}

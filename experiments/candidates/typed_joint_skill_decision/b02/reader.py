"""Complete post-result reconstruction; no ridge solve and no online cross-arm cache."""
from __future__ import annotations

import itertools
import math
import time

from . import model
from .evidence import Trace, encoded, load_output, plain, read_trace, relative_path, verify_outputs, cpu
from .native import SERIES, state, rng_identity
from .search import full_search, search_json


def check_close(actual, expected, name, diagnostics, atol=1e-10, rtol=1e-10):
    import numpy as np
    a, b = np.asarray(actual), np.asarray(expected)
    okay = a.shape == b.shape and np.allclose(a, b, atol=atol, rtol=rtol, equal_nan=False)
    error = None if a.shape != b.shape else float(np.max(np.abs(a.astype(float) - b.astype(float)))) if a.size else 0.0
    diagnostics.append({"check": name, "passed": bool(okay), "max_abs_error": error,
                        "atol": atol, "rtol": rtol, "choice_consequence": "all executed rank/origin checks also required"})
    if not okay:
        raise AssertionError(f"reader mismatch: {name}, max_abs={error}")


def independent_features(c, rank, initial, users, bs, bill=None):
    """Scalar physical reconstruction, including first-permutation lexicographic matching."""
    sites = c["positions_xyz"]
    kind = c["kind"]
    if kind not in model.KINDS:
        raise ValueError("unknown archived kind")
    import numpy as np
    d3 = np.linalg.norm(np.asarray(initial, dtype=np.float64)[:, None, :]
                        - np.asarray(sites, dtype=np.float64)[None, :, :], axis=2)
    permutation = independent_assignment(initial, sites, bill)
    travel = [d3[i][permutation[i]] for i in range(6)]
    centre = [sum(p[j] for p in sites) / 6 for j in (0, 1)]
    return [float(c["contract_reward"]), float(c["coverage_backhauled"]), float(c["potential"]) / 5000,
            *[float(kind == k) for k in model.KINDS], 0.0 if c["k"] is None else c["k"] / 6,
            rank / 2, sum(math.dist(p[:2], bs[:2]) for p in sites) / 6 / 5000,
            sum(min(math.dist(u[:2], p[:2]) for p in sites) for u in users) / 50 / 5000,
            math.sqrt(sum(sum((p[j] - centre[j]) ** 2 for j in (0, 1)) for p in sites) / 6) / 5000,
            sum((p[2] - 50) / 100 for p in sites) / 6, max(travel) / 5000, sum(travel) / 6 / 5000]


def independent_assignment(initial, sites, bill=None):
    """Same float64 primitive/reduction order and first-permutation tie rule, independently written."""
    import numpy as np
    if bill is not None:
        bill.charge("matching_calls")
    distances = np.linalg.norm(np.asarray(initial, dtype=np.float64)[:, None, :]
                               - np.asarray(sites, dtype=np.float64)[None, :, :], axis=2)
    best_key, best_perm = None, None
    for perm in itertools.permutations(range(6)):
        travel = distances[np.arange(6), perm]
        key = (float(np.max(travel)), float(np.sum(travel)))
        if best_key is None or key < best_key:
            best_key, best_perm = key, perm
    if bill is not None:
        bill.charge("matching_completed")
    return best_perm


def independent_transform(x, fit):
    import numpy as np
    x = np.asarray(x, dtype=np.float64)
    z = (x - np.asarray(fit["base_mean"])) / np.asarray(fit["base_sd"])
    columns = [z[:, i] for i in range(15)]
    columns += [z[:, i] * z[:, j] for i in range(15) for j in range(i, 15)]
    basis = np.stack(columns, axis=1)
    return np.column_stack((np.ones(len(x)), (basis - fit["basis_mean"]) / fit["basis_sd"]))


def archive_reader(records, rows, fit, diagnostics, bill=None):
    import numpy as np
    rebuilt = []
    for old in records:
        relay = old["static"]["P_relay"]
        for rank, start in enumerate(relay["starts"]):
            c = dict(relay["candidates"][start["candidate_index"]])
            c["potential"] = next(h["potential"] for h in relay["history"]
                                   if h["stage"] == "start" and h["start"] == rank)
            x = independent_features(c, rank, old["initial_positions_xyz"], old["user_positions_xy"], [2500, 2500, 30], bill)
            best = relay["starts"][0]["start_reward"]
            fb = start["final_reward"] < best - 1e-12
            final = best if fb else start["final_reward"]
            rebuilt.append({"world": old["world"], "rank": rank, "features": x,
                            "target_gain": final - start["start_reward"], "fallback": fb,
                            "executable_final_reward": final})
    if len(rebuilt) != 192 or [(r["world"], r["rank"]) for r in rebuilt] != [(r["world"], r["rank"]) for r in rows]:
        raise AssertionError("complete ordered archive row identities differ")
    if [r["fallback"] for r in rebuilt] != [r["fallback"] for r in rows]:
        raise AssertionError("training fallback differs")
    x = np.asarray([r["features"] for r in rebuilt], dtype=np.float64)
    y = np.asarray([r["target_gain"] for r in rebuilt], dtype=np.float64)
    check_close([r["features"] for r in rows], x, "all training physical features", diagnostics)
    check_close([r["target_gain"] for r in rows], y, "all fallback-adjusted labels", diagnostics)
    mu, sd = x.mean(axis=0), x.std(axis=0)
    sd[sd == 0] = 1
    check_close(fit["base_mean"], mu, "training-only base means", diagnostics)
    check_close(fit["base_sd"], sd, "training-only base SD", diagnostics)
    z = (x - mu) / sd
    q = np.column_stack([z[:, i] for i in range(15)] + [z[:, i] * z[:, j] for i in range(15) for j in range(i, 15)])
    qm, qs = q.mean(axis=0), q.std(axis=0)
    qs[qs == 0] = 1
    check_close(fit["basis_mean"], qm, "training-only quadratic means", diagnostics)
    check_close(fit["basis_sd"], qs, "training-only quadratic SD", diagnostics)
    a = independent_transform(x, fit)
    w = np.asarray(fit["coefficients"], dtype=np.float64)
    if w.shape != (136,) or fit["initial_coefficients"] != [0.0] * 136:
        raise AssertionError("fixed initial/final parameter shape")
    if (fit["dtype"] != "float64" or fit["lambda_sum_loss"] != 1.0
            or fit["features"] != list(model.FEATURES) or fit["pairs"] != [list(p) for p in model.PAIRS]):
        raise AssertionError("fixed model field/basis/regularizer mismatch")
    residual = a.T @ (a @ w - y) + np.r_[0.0, w[1:]]
    check_close(fit["normal_equation_residual"], residual, "saved normal equation residual vector", diagnostics, atol=1e-8, rtol=1e-8)
    check_close(fit["training_residuals"], a @ w - y, "saved all training residuals", diagnostics)
    relative = float(np.linalg.norm(residual) / max(1.0, np.linalg.norm(a.T @ y)))
    diagnostics.append({"check": "independent normal equation, no second solve", "passed": relative <= 1e-8,
                        "relative_residual": relative, "tolerance": 1e-8})
    if relative > 1e-8:
        raise AssertionError("saved fit violates fixed normal equation")
    check_close(fit["training_predictions"], a @ w, "saved all-row predictions", diagnostics)
    means = [sum(r["executable_final_reward"] for r in rebuilt if r["rank"] == k) / 64 for k in range(3)]
    fixed_rank = max(range(3), key=lambda r: (means[r], -r))
    if fixed_rank != 0:
        raise AssertionError("declared B=G alias not established from bound archive")
    if len(fit["training_decisions"]) != 64:
        raise AssertionError("all saved training decisions required")
    prediction = a @ w
    for offset, saved in zip(range(0, 192, 3), fit["training_decisions"]):
        group = rebuilt[offset:offset + 3]
        estimates = [rows[offset + rank]["initial_candidate"]["contract_reward"] + prediction[offset + rank] for rank in range(3)]
        rank = max(range(3), key=lambda r: (estimates[r], -r))
        if saved["world"] != group[0]["world"] or saved["initial_rank"] != 0 or saved["final_rank"] != rank or saved["selected_fallback"] != group[rank]["fallback"]:
            raise AssertionError("saved training decision/fallback differs")
        check_close(saved["predicted_gains"], prediction[offset:offset + 3], "training choice predictions", diagnostics)
    return {"rows": 192, "independent_training_contexts": 64, "fixed_rank_means": means,
            "fixed_rank": fixed_rank, "B_alias": "G", "normal_equation_relative": relative,
            "mse_initial": float(np.mean(y ** 2)), "mse_final": float(np.mean((a @ w - y) ** 2)),
            "parameter_movement_l2_from_zero": float(np.linalg.norm(w)),
            "fallback_rows": [{"world": r["world"], "rank": r["rank"]} for r in rebuilt if r["fallback"]],
            "feature_min": x.min(axis=0).tolist(), "feature_max": x.max(axis=0).tolist(),
            "feature_nonzero_counts": (x != 0).sum(axis=0).tolist(), "fits_replayed": 0}


def endpoint(search, rank):
    """Reconstruct from initial + accepted moves, never trusting the candidate endpoint."""
    import numpy as np
    start = search["starts"][rank]
    position = np.array(search["candidates"][start["candidate_index"]]["positions_xyz"], dtype=float)
    for h in search["history"]:
        if h.get("start") == rank and h["stage"] in ("descent", "plateau"):
            position[h["uav"]] += np.asarray(h["move"])
            position[:, :2] = np.clip(position[:, :2], 0, 5000)
            position[:, 2] = np.clip(position[:, 2], 50, 150)
    return position


def path_signature(history, rank, began):
    return [{k: v for k, v in h.items() if k not in ("evaluations", "start")}
            | {"relative_evaluations": h["evaluations"] - began}
            for h in history if h.get("start") == rank and h["stage"] in ("descent", "plateau")]


def query_reader(path, saved, flat, relay, reference_queries):
    """Every online static request/response, including rejected trials and final metadata."""
    flat_count = flat.evaluations
    initial_count = relay.candidates_evaluated
    rank = saved["requested_rank"]
    if saved["arm"] == "P":
        expected = reference_queries
    else:
        start = relay.starts[rank]
        offset = flat_count + start["began_at_evaluation"]
        expected = reference_queries[:flat_count + initial_count] + reference_queries[offset:offset + start["evaluations"]]
        target = encoded(saved["positions_xyz"])
        # Initial/accepted positions must have been paid; their radio score is physical state only.
        selected_info = next((q["info"] for q in reference_queries[flat_count:]
                              if q["allow_a2a"] and encoded(q["positions_xyz"]) == target), None)
        if selected_info is None:
            raise AssertionError("executed layout absent from original paid reference queries")
        expected += [{"positions_xyz": saved["positions_xyz"], "allow_a2a": True, "info": selected_info}]
    count = 0
    for count, (a, b) in enumerate(itertools.zip_longest(read_trace(path), expected), 1):
        if a is None or b is None or encoded(a) != encoded(b):
            raise AssertionError(f"original static request/response path differs at query {count}")
    if count != saved["case_counts"]["static_calls"] or count != saved["case_counts"]["static_completed"]:
        raise AssertionError("actual saved static stream/counter count differs")
    return count


def verify_world_identity(decision, reset, reference):
    """Bind stored geometry and executor reset to the freshly created reference world."""
    for key in ("world", "initial_positions_xyz", "user_positions_xy", "bs_xyz"):
        if encoded(decision[key]) != encoded(reference[key]):
            raise AssertionError(f"fresh reference world identity differs: {key}")
    if reset is not None:
        for key in ("native_rng_sha256", "agents", "transmitter_mask"):
            if encoded(reset[key]) != encoded(reference[key]):
                raise AssertionError(f"fresh reference reset identity differs: {key}")
        if (reset["state"]["current_step"] != reference["current_step"]
                or encoded(reset["state"]["positions_xyz"]) != encoded(reference["initial_positions_xyz"])):
            raise AssertionError("fresh reference reset state differs")


def decision_reader(saved, flat, relay, fit, diagnostics, bill=None):
    import numpy as np
    reference = search_json(relay)
    flat_ref = search_json(flat)
    if encoded(saved["flat"]) != encoded(flat_ref):
        raise AssertionError("original full flat path differs")
    candidate_ref = reference["candidates"]
    if len(saved["relay"]["candidates"]) != len(candidate_ref):
        raise AssertionError("relay candidate count differs")
    for i, (a, b) in enumerate(zip(saved["relay"]["candidates"], candidate_ref)):
        for k in ("index", "kind", "k", "duplicate_of"):
            if a.get(k) != b.get(k):
                raise AssertionError(f"candidate {i} identity differs: {k}")
        check_close(a["positions_xyz"], b["positions_xyz"], f"candidate {i} positions", diagnostics, atol=1e-8, rtol=0)
        check_close([a[k] for k in ("contract_reward", "coverage_backhauled", "potential")],
                    [b[k] for k in ("contract_reward", "coverage_backhauled", "potential")],
                    f"candidate {i} initial scores", diagnostics)
    ranked = [s["candidate_index"] for s in reference["starts"]]
    shares = [s["share"] for s in reference["starts"]]
    if saved["ranked_indices"] != ranked or saved["original_shares"] != shares:
        raise AssertionError("original top-three ordering/share mismatch")
    xs = [independent_features(candidate_ref[i], rank, saved["initial_positions_xyz"],
                               saved["user_positions_xy"], saved["bs_xyz"], bill) for rank, i in enumerate(ranked)]
    if saved["arm"] == "L":
        check_close(saved["features"], xs, "online physical features", diagnostics)
    elif saved["features"] is not None:
        raise AssertionError("ordinary online paths must omit learned-only features/matching")
    estimated = independent_transform(xs, fit) @ np.asarray(fit["coefficients"])
    arm = saved["arm"]
    if arm == "L":
        check_close(saved["predicted_gains"], estimated, "independent L predicted gains", diagnostics)
        choice_values = [candidate_ref[i]["contract_reward"] + estimated[r] for r, i in enumerate(ranked)]
        rank = max(range(3), key=lambda r: (choice_values[r], -r))
    else:
        rank = 0 if arm == "G" else reference["best_start"]["start"]
    if saved["requested_rank"] != rank:
        raise AssertionError("requested choice differs; no tolerance-based rank substitution")
    expected_start = reference["starts"][rank]
    for k in ("start", "candidate_index", "share", "evaluations", "converged", "accepted_descent",
              "accepted_plateau", "final_xy_step_m", "start_reward", "final_reward"):
        if saved["selected_branch"][k] != expected_start[k]:
            raise AssertionError(f"original selected branch differs: {k}")
    got_path = path_signature(saved["relay"]["history"], rank, saved["selected_branch"]["began_at_evaluation"])
    expected_path = path_signature(reference["history"], rank, expected_start["began_at_evaluation"])
    if encoded(got_path) != encoded(expected_path):
        raise AssertionError("original selected branch accepted path/query counts differ")
    if arm == "P" and encoded(saved["relay"]) != encoded(reference):
        raise AssertionError("P differs from original full relay search")
    branch_final = endpoint(reference, rank)
    fb = arm != "P" and expected_start["final_reward"] < reference["starts"][0]["start_reward"] - 1e-12
    positions = candidate_ref[ranked[0]]["positions_xyz"] if fb else branch_final
    if saved["fallback"] != fb or saved["executed_origin"] != ("rank0_initial" if fb else f"rank{rank}_final"):
        raise AssertionError("paid incumbent fallback/commitment differs")
    check_close(saved["positions_xyz"], positions, "executed reference-derived endpoint", diagnostics, atol=1e-8, rtol=0)
    # Reconstruct matching with separate scalar arithmetic; exact permutation consequences.
    initial = saved["initial_positions_xyz"]
    perm = independent_assignment(initial, positions, bill)
    if saved["target_permutation"] != list(perm):
        raise AssertionError("final matching permutation differs")
    check_close(saved["assigned_targets_xyz"], np.asarray(positions)[list(perm)], "assigned targets", diagnostics, atol=1e-8, rtol=0)
    finals = [s["final_reward"] if s["final_reward"] >= reference["starts"][0]["start_reward"] - 1e-12
              else reference["starts"][0]["start_reward"] for s in reference["starts"]]
    g_positions = (candidate_ref[ranked[0]]["positions_xyz"]
                   if reference["starts"][0]["final_reward"] < reference["starts"][0]["start_reward"] - 1e-12
                   else endpoint(reference, 0))
    g_assigned = np.asarray(g_positions)[list(independent_assignment(initial, g_positions, bill))]
    return {"requested_rank": rank, "fallback": fb, "static_regret_vs_P": relay.contract_reward - saved["static_info"]["contract_reward"],
            "all_three_executable_final_rewards": finals, "all_three_predicted_gains": estimated.tolist(),
            "all_three_gain_errors": [float(estimated[r] - (finals[r] - candidate_ref[i]["contract_reward"])) for r, i in enumerate(ranked)],
            "executed_layout_differs_from_G": not np.allclose(saved["assigned_targets_xyz"], g_assigned, atol=1e-8, rtol=0)}


def trace_reader(path, env, native, decision, result, diagnostics, reference_identity):
    import numpy as np
    rows = iter(read_trace(path))
    first = next(rows)
    if first["type"] != "initial" or first["world"] != decision["world"] or first["arm"] != decision["arm"]:
        raise AssertionError("trace identity mismatch")
    verify_world_identity(decision, first["reset"], reference_identity)
    expected_rng = first["reset"]["native_rng_sha256"]
    previous = first["reset"]["state"]
    check_close(previous["positions_xyz"], decision["initial_positions_xyz"], "trace reset positions", diagnostics, atol=0, rtol=0)
    if previous["current_step"] != 0 or first["target_permutation"] != decision["target_permutation"]:
        raise AssertionError("trace initial step/matching differs")
    values = {k: [] for k in SERIES}
    changes, losses, count = [], [], 0
    assigned = np.asarray(decision["assigned_targets_xyz"])
    def verify_state(saved, label):
        native.bill.charge("reader_state_checks")
        env.current_step = saved["current_step"]
        native.host.static_evaluate(env, saved["positions_xyz"], allow_a2a=True)
        refreshed = state(env)
        for k in ("positions_xyz", "user_association", "backhauled_users_mask", "connections",
                  "uav_connections", "uav_bs_connections", "routing_paths"):
            if encoded(saved[k]) != encoded(refreshed[k]):
                raise AssertionError(f"paid pinned-radio state mismatch: {label}/{k}")
        for k, expected in refreshed["reward_info"].items():
            actual = saved["reward_info"][k]
            if isinstance(expected, (bool, str)):
                if actual != expected:
                    raise AssertionError(f"native metadata mismatch: {k}")
            elif not np.isclose(actual, expected, rtol=1e-10, atol=1e-10):
                diagnostics.append({"check": label + "/" + k, "passed": False, "actual": actual, "expected": expected})
                raise AssertionError(f"paid pinned-radio reward mismatch: {label}/{k}")
    verify_state(previous, "initial")
    for t, row in enumerate(rows):
        if row["type"] != "step" or row["t"] != t or t >= 500 or row["state"]["current_step"] != t + 1:
            raise AssertionError("complete contiguous H500 trace required")
        old = np.asarray(previous["positions_xyz"], dtype=float)
        delta = assigned - old
        distances = np.sqrt(np.sum(delta * delta, axis=1))
        expected_action = np.zeros((6, 3), dtype=float)
        moving = distances > 1e-6
        expected_action[moving] = delta[moving] / np.maximum(30.0, distances[moving])[:, None]
        norms = np.linalg.norm(expected_action, axis=1)
        expected_action[norms > 1] /= norms[norms > 1, None]
        check_close(row["actions"], expected_action, f"action {t}", diagnostics, atol=1e-12, rtol=0)
        a = np.asarray(row["actions"], dtype=np.float64)
        norms = np.linalg.norm(a, axis=1)
        a[norms > 1] /= norms[norms > 1, None]
        after = old + 30 * a
        after[:, :2] = np.clip(after[:, :2], 0, 5000)
        after[:, 2] = np.clip(after[:, 2], 50, 150)
        check_close(row["state"]["positions_xyz"], after, f"kinematics {t}", diagnostics, atol=1e-8, rtol=0)
        if row["native_rng_sha256"] != expected_rng:
            raise AssertionError("native RNG advanced")
        terminated = row["terminations"]
        if any(bool(v) != (t == 499) for v in terminated.values()) or any(row["truncations"].values()):
            raise AssertionError("native termination/truncation differs")
        verify_state(row["state"], f"step{t}")
        info = row["state"]["reward_info"]
        check_close(sum(row["rewards"].values()), info["contract_reward"], f"team reward {t}", diagnostics, atol=1e-9, rtol=0)
        for k in SERIES:
            values[k].append(info[k])
        changes.append(sum(a != b for a, b in zip(previous["user_association"], row["state"]["user_association"])))
        losses.append(sum(a and not b for a, b in zip(previous["backhauled_users_mask"], row["state"]["backhauled_users_mask"])))
        previous, count = row["state"], t + 1
    if count != 500 or result["steps"] != 500:
        raise AssertionError("missing native frames")
    if result["association_changes_per_step"] != changes or result["backhaul_losses_per_step"] != losses:
        raise AssertionError("native event series differ")
    for k in SERIES:
        check_close(result["series"][k], values[k], f"all {k} native series", diagnostics)
        check_close([result[k + "_mean_all"], result[k + "_mean_final100"]],
                    [np.mean(values[k]), np.mean(values[k][-100:])], f"{k} native aggregate", diagnostics)
    return {k: {"mean_all": float(np.mean(v)), "mean_final100": float(np.mean(v[-100:]))} for k, v in values.items()} | {
        "association_change_count": sum(changes), "backhaul_loss_events": sum(losses), "state_checks": 501}


def original_episode_audit(env, native, decision, trace_path, diagnostics, audit_path):
    """Original closed_loop_execute called once, with a recorder around its real step."""
    from .evidence import Trace
    main_rows = iter(read_trace(trace_path))
    next(main_rows)
    original_step = env.step
    trace = Trace(audit_path, native.bill)
    frame = 0
    def recorded_step(actions):
        nonlocal frame
        result = original_step(actions)
        row = {"t": frame, "actions": [plain(actions[a]) for a in env.agents], "state": state(env),
               "rewards": plain(result[1]), "terminations": plain(result[2]), "truncations": plain(result[3])}
        trace.write(row)
        main = next(main_rows)
        for k in ("actions", "state", "rewards", "terminations", "truncations"):
            if encoded(row[k]) != encoded(main[k]):
                diagnostics.append({"check": f"original whole executor/frame{frame}/{k}", "passed": False})
                raise AssertionError(f"original executor disagrees at frame {frame}/{k}")
        frame += 1
        return result
    env.step = recorded_step
    native.bill.charge("audit_episodes")
    try:
        original = native.p.closed_loop_execute(env, decision["positions_xyz"], max_steps=500, allow_a2a=True)
    finally:
        del env.step
        trace.close()
    if frame != 500 or original["steps"] != 500:
        raise AssertionError("complete original H500 audit required")
    return original


def paired(values):
    n = len(values)
    mean = sum(values) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1)) if n > 1 else None
    se = sd / math.sqrt(n) if sd is not None else None
    return {"n": n, "mean": mean, "sd": sd, "se": se,
            "t63_95_interval": [mean - 1.998340542520741 * se, mean + 1.998340542520741 * se] if n == 64 else None,
            "positive": sum(v > 0 for v in values), "negative": sum(v < 0 for v in values),
            "zero": sum(v == 0 for v in values), "min": min(values), "max": max(values),
            "uncertainty_scope": "64 worlds conditional on one fitted asset, not fit replication"}


def complete_reader(store, native, records, rows, fit):
    started = time.perf_counter()
    verify_outputs(store.root, store.files)
    diagnostics, per_world = [], []
    try:
        train = archive_reader(records, rows, fit, diagnostics, native.bill)
        for world in range(107100000, 107100064):
            world_started, world_cpu = time.perf_counter(), cpu()["total_seconds"]
            before_counts = native.bill.snapshot()["counters"]
            env = native.host.make_host(world, area_size=5000)
            reference_identity = plain({"world": int(env.world_seed), "initial_positions_xyz": env.uav_positions.copy(),
                                        "user_positions_xy": env.user_positions.copy(), "bs_xyz": env.ground_bs_positions[0].copy(),
                                        "native_rng_sha256": rng_identity(env), "agents": list(env.agents),
                                        "transmitter_mask": env._transmitter_mask.copy(), "current_step": env.current_step})
            native.bill.charge("reader_reference_searches")
            reference_relative = f"raw/reader/{world}/original-search-queries.jsonl.gz"
            query_trace = Trace(relative_path(store.root, reference_relative), native.bill)
            native.query_trace = query_trace
            try:
                flat, relay, reference_timing = full_search(env, native.p, world)
                native.host.static_evaluate(env, relay.positions_xyz, allow_a2a=True)
            finally:
                native.query_trace = None
                query_trace.close()
                store.register(reference_relative)
            reference_queries = list(read_trace(relative_path(store.root, reference_relative)))
            store.write(f"raw/reader/{world}/original-search.json", {"flat": search_json(flat), "relay": search_json(relay),
                                                                      "timing": reference_timing, "initial_world_identity": reference_identity})
            readings = {}
            for arm in ("G", "L", "P"):
                base = f"raw/main/{world}/{arm}"
                decision = load_output(store.root, store.files, base + "/decision.json")
                result = load_output(store.root, store.files, base + "/native.json")
                verify_world_identity(decision, result["reset_identity"], reference_identity)
                choice = decision_reader(decision, flat, relay, fit, diagnostics, native.bill)
                query_relative = base + "/search-queries.jsonl.gz"
                if query_relative not in store.files:
                    raise AssertionError("unbound main query stream")
                query_count = query_reader(relative_path(store.root, query_relative), decision, flat, relay, reference_queries)
                trace_path = relative_path(store.root, base + "/trace.jsonl.gz")
                if base + "/trace.jsonl.gz" not in store.files:
                    raise AssertionError("unbound native trace")
                native_means = trace_reader(trace_path, env, native, decision, result, diagnostics, reference_identity)
                audit = None
                if world < 107100004:
                    audit_relative = f"raw/reader/{world}/{arm}-original-executor.jsonl.gz"
                    audit = original_episode_audit(env, native, decision, trace_path, diagnostics,
                                                  relative_path(store.root, audit_relative))
                    store.register(audit_relative)
                    store.write(f"raw/reader/{world}/{arm}-original-executor.json", audit)
                xs = decision["features"]
                out_of_range = (None if xs is None else [[j for j, value in enumerate(x) if value < train["feature_min"][j] or value > train["feature_max"][j]] for x in xs])
                readings[arm] = {"choice": choice, "native": native_means, "cold_selection_seconds": decision["parent_cold_selection_seconds"],
                                 "process_wall_seconds": decision["parent_process_wall_seconds"], "child_cpu": decision["child_cpu"],
                                 "child_selection_cpu": decision["child_selection_cpu"], "cold_latency_scope": decision["cold_latency_scope"],
                                 "static_calls": decision["case_counts"]["static_calls"], "native_steps": decision["case_counts"]["native_steps"],
                                 "internal_radio_refresh_calls": decision["case_counts"]["radio_refresh_calls"],
                                 "native_wall_seconds": result["native_wall_seconds_including_trace"], "timing": decision["timing"],
                                 "features_outside_training_range": out_of_range, "whole_executor_audited": audit is not None}
                readings[arm]["all_static_queries_checked"] = query_count
            after_counts = native.bill.snapshot()["counters"]
            per_world.append({"world": world, "arms": readings,
                              "reader_wall_seconds": time.perf_counter() - world_started,
                              "reader_cpu_seconds": cpu()["total_seconds"] - world_cpu,
                              "reader_counts": {k: after_counts[k] - before_counts[k] for k in after_counts},
                              "L_minus_G_J": readings["L"]["native"]["contract_reward"]["mean_all"] - readings["G"]["native"]["contract_reward"]["mean_all"],
                              "L_minus_G_C_bh": readings["L"]["native"]["coverage_backhauled"]["mean_all"] - readings["G"]["native"]["coverage_backhauled"]["mean_all"]})
            store.progress("reader", completed_worlds=len(per_world))
        store.write("raw/reader/per-world.json", per_world)
        comparisons = {}
        for a, b in (("L", "G"), ("L", "P"), ("G", "P")):
            label = a + "_minus_" + b
            comparisons[label] = {k: paired([r["arms"][a]["native"][k]["mean_all"] - r["arms"][b]["native"][k]["mean_all"] for r in per_world]) for k in SERIES}
            comparisons[label].update({k: paired([r["arms"][a][k] - r["arms"][b][k] for r in per_world]) for k in ("cold_selection_seconds", "static_calls", "process_wall_seconds", "native_wall_seconds")})
            comparisons[label].update({"child_selection_cpu_seconds": paired([r["arms"][a]["child_selection_cpu"]["total_seconds"] - r["arms"][b]["child_selection_cpu"]["total_seconds"] for r in per_world]),
                                       "child_total_cpu_seconds": paired([r["arms"][a]["child_cpu"]["total_seconds"] - r["arms"][b]["child_cpu"]["total_seconds"] for r in per_world])})
        absolute = {arm: {k: paired([r["arms"][arm]["native"][k]["mean_all"] for r in per_world]) for k in SERIES} for arm in ("G", "L", "P")}
        choices = {arm: {"ranks": [sum(r["arms"][arm]["choice"]["requested_rank"] == rank for r in per_world) for rank in range(3)],
                         "fallback_worlds": [r["world"] for r in per_world if r["arms"][arm]["choice"]["fallback"]],
                         "different_from_G_worlds": [r["world"] for r in per_world if r["arms"][arm]["choice"]["executed_layout_differs_from_G"]],
                         "static_regret_vs_P": paired([r["arms"][arm]["choice"]["static_regret_vs_P"] for r in per_world])} for arm in ("G", "L", "P")}
        absolute_costs = {arm: {k: paired([r["arms"][arm][k] for r in per_world])
                               for k in ("cold_selection_seconds", "process_wall_seconds", "static_calls", "native_wall_seconds")}
                          | {"child_cpu_seconds": paired([r["arms"][arm]["child_cpu"]["total_seconds"] for r in per_world])}
                          | {"child_selection_cpu_seconds": paired([r["arms"][arm]["child_selection_cpu"]["total_seconds"] for r in per_world])}
                          for arm in ("G", "L", "P")}
        return {"training": train, "absolute_native_means": absolute, "comparisons": comparisons, "choices": choices,
                "absolute_costs": absolute_costs,
                "B_alias": "G", "B_minus_G": 0, "fitted_assets": 1, "fresh_worlds": 64,
                "reader_seconds": time.perf_counter() - started,
                "trust_boundary": "independent branch/feature/label/state reconstruction uses pinned upstream radio, not an independent physics engine; historical-to-current source shift not runtime-certified",
                "interpretation": "conditional one-fit capability and full cold cost; no training replication, causal/pretraining attribution, or best ordinary frontier claim",
                "support_cost": "implementation/review/preparation/support work partly unmetered; unknown is not zero"}
    finally:
        store.write("raw/reader/checks.json", diagnostics)

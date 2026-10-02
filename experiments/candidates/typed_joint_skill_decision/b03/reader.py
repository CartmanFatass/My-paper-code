"""Post-selection paid-evidence gate and complete exposed-panel reconstruction."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import time

from ..b02 import evidence as e
from ..b02 import reader as old
from ..b02.native import SERIES

NEW_WORLDS = (107100000, 107100011, 107100025, 107100027, 107100032, 107100033, 107100036)
AUDIT_WORLDS = (107100000, 107100036)


def f64_digest(array):
    import numpy as np
    x = np.asarray(array, dtype=np.dtype("<f8"))
    if x.shape != (6, 3) or not np.isfinite(x).all():
        raise ValueError("finite float64 6x3 geometry required")
    return hashlib.sha256(x.tobytes(order="C")).hexdigest()


class Prior:
    """Parent/reader only. Neither this object nor any old row reaches the online child."""
    def __init__(self, manifest, source_root):
        self.contract, self.root = manifest, Path(manifest["prior_root"]).resolve(strict=True)
        m = e.bound_json(self.root / "artifact-manifest.json", manifest["prior_manifest_sha256"])
        self.files, self.used = m["files"], {}
        self.alias_path = e.relative_path(source_root, manifest["alias_reader_manifest"])
        if e.sha(self.alias_path) != manifest["alias_reader_manifest_sha256"]:
            raise ValueError("reader-only alias manifest digest mismatch")
        self.alias = None  # Parsed only at a gate after immutable selection-ready.
        self.verified_header = False

    def bytes(self, relative):
        if relative not in self.files:
            raise ValueError(f"unlisted prior artifact: {relative}")
        data = e.relative_path(self.root, relative).read_bytes()
        expected = self.files[relative]
        if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
            raise ValueError(f"prior artifact byte mismatch: {relative}")
        self.used[relative] = expected
        return data

    def json(self, relative):
        return json.loads(self.bytes(relative))

    def path(self, relative):
        self.bytes(relative)
        return e.relative_path(self.root, relative)

    def headers_after_selection(self):
        if self.verified_header:
            return
        config, summary = self.json("config.json"), self.json("summary.json")
        source = self.contract["source_of_original_reference"]
        if (config["launch_sha"] != source or config["admission"]["sha"] != source
                or summary["launch_sha"] != source or summary["status"] != "complete"
                or config["dtype"] != "float64" or summary["interpreter"]["numpy"] != "1.26.3"
                or config["input_manifest_data"]["pinned_upstream_sources"] != self.contract["pinned_upstream_sources"]
                or summary["bill"]["counters"]["reader_state_checks"] != 96192
                or summary["bill"]["counters"]["native_completed"] != 102000):
            raise AssertionError("prior source/complete reader/runtime identity mismatch")
        self.path(summary["diagnostics"]["path"])  # Inherit B02's bound paid physics witness.
        self.alias = e.bound_json(self.alias_path, self.contract["alias_reader_manifest_sha256"])
        if (self.alias["source_sha"] != source or self.alias["prior_manifest_sha256"] != self.contract["prior_manifest_sha256"]
                or [r["world"] for r in self.alias["rows"]] != list(range(107100000, 107100064))
                or self.alias["missing_worlds"] != list(NEW_WORLDS)):
            raise AssertionError("complete reader-only alias identity mismatch")
        self.verified_header = True


def exact(a, b, label, diagnostics):
    okay = e.encoded(a) == e.encoded(b)
    diagnostics.append({"check": label, "passed": okay, "comparison": "exact encoded fields/float64 bytes; no near-match substitution"})
    if not okay:
        raise AssertionError("B03 exact mismatch: " + label)


def q_projection(reference):
    """Saved accepted histories, not the candidate's chosen rank, determine prefix incumbents."""
    import numpy as np
    relay = reference["relay"]
    rewards, prefix_positions = [], []
    for r, s in enumerate(relay["starts"]):
        reward = s["start_reward"]
        position = np.array(relay["candidates"][s["candidate_index"]]["positions_xyz"], dtype=float)
        for h in relay["history"]:
            if h.get("start") == r and h["stage"] in ("descent", "plateau") and h["evaluations"] - s["began_at_evaluation"] <= 36:
                reward = h["contract_reward"]
                position[h["uav"]] += np.asarray(h["move"])
                position[:, :2] = np.clip(position[:, :2], 0, 5000)
                position[:, 2] = np.clip(position[:, 2], 50, 150)
        rewards.append(reward)
        prefix_positions.append(position.tolist())
    rank = max(range(3), key=lambda r: (rewards[r], -r))
    chosen = relay["starts"][rank]
    fb = chosen["final_reward"] < relay["starts"][0]["start_reward"] - 1e-12
    endpoint = (relay["candidates"][relay["starts"][0]["candidate_index"]]["positions_xyz"] if fb else old.endpoint(relay, rank).tolist())
    return {"rank": rank, "prefix_rewards": rewards, "prefix_positions": prefix_positions,
            "prefix_counts": [min(36, s["evaluations"]) for s in relay["starts"]],
            "fallback": fb, "positions_xyz": endpoint}


def query_sequence(reference, reference_queries, decision):
    flat, relay = reference["flat"], reference["relay"]
    base = flat["evaluations"]
    if decision["arm"] == "P":
        return reference_queries
    result = reference_queries[:base + relay["candidates_evaluated"]]
    if decision["arm"] == "G":
        s = relay["starts"][0]
        offset = base + s["began_at_evaluation"]
        result += reference_queries[offset:offset + s["evaluations"]]
    else:
        for s in relay["starts"]:
            offset = base + s["began_at_evaluation"]
            result += reference_queries[offset:offset + min(36, s["evaluations"])]
        s = relay["starts"][decision["requested_rank"]]
        offset = base + s["began_at_evaluation"]
        result += reference_queries[offset + min(36, s["evaluations"]):offset + s["evaluations"]]
    target = e.encoded(decision["positions_xyz"])
    info = next(q["info"] for q in reference_queries[base:] if q["allow_a2a"] and e.encoded(q["positions_xyz"]) == target)
    result.append({"positions_xyz": decision["positions_xyz"], "allow_a2a": True, "info": info})
    return result


def verify_gate(prior, decision, current_queries_path, diagnostics, bill):
    """Called only after the parent has received immutable selection evidence + timing."""
    import numpy as np
    bill.check()
    prior.headers_after_selection()
    world, arm = decision["world"], decision["arm"]
    reference = prior.json(f"raw/reader/{world}/original-search.json")
    fresh = reference["initial_world_identity"]
    old.verify_world_identity(decision, decision["reset_identity"], fresh)
    # B02 physics reset after its full search is the execution identity, not constructor routing zeros.
    originals = {a: prior.json(f"raw/main/{world}/{a}/selection.json") for a in ("G", "L", "P")}
    native_records = {a: prior.json(f"raw/main/{world}/{a}/native.json") for a in ("G", "L", "P")}
    for a in originals:
        old.verify_world_identity(originals[a], native_records[a]["reset_identity"], fresh)
        exact(decision["reset_identity"], native_records[a]["reset_identity"], f"{world}/{arm} complete reset vs {a}", diagnostics)
    if arm == "Q":
        exact(decision["flat"], reference["flat"], f"{world}/Q full flat", diagnostics)
        for key in ("candidates", "candidates_evaluated", "candidate_report"):
            exact(decision["relay"][key], originals["G"]["relay"][key], f"{world}/Q common {key}", diagnostics)
        for key in ("ranked_indices", "original_shares"):
            exact(decision[key], originals["G"][key], f"{world}/Q common {key}", diagnostics)
        projected = q_projection(reference)
        alias_row = prior.alias["rows"][world - 107100000]
        for name, key in (("requested_rank", "rank"), ("prefix_rewards", "prefix_rewards"),
                          ("prefix_query_counts", "prefix_counts"), ("fallback", "fallback"), ("positions_xyz", "positions_xyz")):
            exact(decision[name], projected[key], f"{world}/Q {name}", diagnostics)
        exact(alias_row["rank"], projected["rank"], f"{world} declared Q rank", diagnostics)
        exact(alias_row["prefix_rewards"], projected["prefix_rewards"], f"{world} declared prefix values", diagnostics)
        for r, s in enumerate(reference["relay"]["starts"]):
            snap = decision["prefix_states"][r]
            exact(snap["used"], projected["prefix_counts"][r], f"{world}/prefix{r} used", diagnostics)
            exact(snap["positions_xyz"], projected["prefix_positions"][r], f"{world}/prefix{r} incumbent", diagnostics)
            exact(snap["share"], s["share"], f"{world}/prefix{r} original share", diagnostics)
        rank = projected["rank"]
        selected = reference["relay"]["starts"][rank]
        for k in ("start", "candidate_index", "kind", "k", "start_reward", "final_reward", "share", "evaluations",
                  "converged", "accepted_descent", "accepted_plateau", "final_xy_step_m"):
            exact(decision["selected_branch"][k], selected[k], f"{world}/Q resumed {k}", diagnostics)
        for r, s in enumerate(reference["relay"]["starts"]):
            expected = old.path_signature(reference["relay"]["history"], r, s["began_at_evaluation"])
            if r != rank:
                expected = [h for h in expected if h["relative_evaluations"] <= 36]
            got = old.path_signature(decision["relay"]["history"], r, reference["relay"]["candidates_evaluated"])
            exact(got, expected, f"{world}/Q branch{r} accepted prefix/suffix", diagnostics)
        expected_position = projected["positions_xyz"]
    else:
        expected = originals[arm]
        for key in ("flat", "relay", "ranked_indices", "original_shares", "requested_rank", "selected_branch", "fallback", "executed_origin", "static_info"):
            exact(decision[key], expected[key], f"{world}/{arm} original {key}", diagnostics)
        expected_position = expected["positions_xyz"]
    perm = old.independent_assignment(fresh["initial_positions_xyz"], expected_position, bill)
    assigned = np.asarray(expected_position, dtype=float)[list(perm)]
    exact(decision["target_permutation"], list(perm), f"{world}/{arm} original matching", diagnostics)
    exact(f64_digest(decision["positions_xyz"]), f64_digest(expected_position), f"{world}/{arm} unassigned f64", diagnostics)
    exact(f64_digest(decision["assigned_targets_xyz"]), f64_digest(assigned), f"{world}/{arm} assigned f64", diagnostics)
    ref_queries = list(e.read_trace(prior.path(f"raw/reader/{world}/original-search-queries.jsonl.gz")))
    expected_queries = query_sequence(reference, ref_queries, decision)
    count = 0
    for count, (actual, expected) in enumerate(itertools.zip_longest(e.read_trace(current_queries_path), expected_queries), 1):
        exact(actual, expected, f"{world}/{arm} static request/response {count}", diagnostics)
        if count % 100 == 0:
            bill.check(sample_disk=False)
    exact(decision["static_info"], expected_queries[-1]["info"], f"{world}/{arm} final metadata", diagnostics)
    exact(count, decision["selection_counts"]["static_calls"], f"{world}/{arm} attempts", diagnostics)
    exact(count, decision["selection_counts"]["static_completed"], f"{world}/{arm} completions", diagnostics)
    if arm == "Q":
        row = prior.alias["rows"][world - 107100000]
        exact(count, row["query_count"], f"{world}/Q declared cost", diagnostics)
        exact(f64_digest(assigned), row["assigned_f64le_sha256"], f"{world}/Q alias-map assigned bytes", diagnostics)
        exact(f64_digest(expected_position), row["unassigned_f64le_sha256"], f"{world}/Q alias-map unassigned bytes", diagnostics)
        exact(list(perm), row["target_permutation"], f"{world}/Q alias-map permutation", diagnostics)
        aliases = [a for a in ("G", "L", "P") if f64_digest(originals[a]["positions_xyz"]) == f64_digest(expected_position)
                   and f64_digest(originals[a]["assigned_targets_xyz"]) == f64_digest(assigned)
                   and originals[a]["target_permutation"] == list(perm)]
        exact(aliases, row["exact_saved_aliases"], f"{world}/Q complete aliases", diagnostics)
        alias = aliases[0] if aliases else None
        exact(alias, row["preferred_alias"], f"{world}/Q fixed first alias", diagnostics)
        if (alias is None) != (world in NEW_WORLDS):
            raise AssertionError("undeclared new-episode request; no eighth episode allowed")
    else:
        alias = arm
    bill.charge("alias_gates")
    return {"world": world, "arm": arm, "alias_arm": alias, "new_episode": alias is None,
            "selection_static_calls": count, "prior_root": str(prior.root),
            "prior_native": None if alias is None else f"raw/main/{world}/{alias}/native.json",
            "prior_trace": None if alias is None else f"raw/main/{world}/{alias}/trace.jsonl.gz",
            "reference_identity": fresh, "all_queries_exact": True}


def reaggregate(path, decision, result, diagnostics, reset_identity, bill):
    """Entire saved trajectory, no new physics query. Its B02 per-state witness is inherited."""
    import numpy as np
    rows = iter(e.read_trace(path))
    first = next(rows)
    if first["type"] != "initial" or first["world"] != decision["world"]:
        raise AssertionError("reused trace world identity mismatch")
    exact(first["reset"], reset_identity, "reused full trace reset", diagnostics)
    exact(first["target_permutation"], decision["target_permutation"], "reused permutation", diagnostics)
    exact(f64_digest(first["assigned_targets_xyz"]), f64_digest(decision["assigned_targets_xyz"]), "reused assigned target bytes", diagnostics)
    previous = first["reset"]["state"]
    values = {k: [] for k in SERIES}
    changes, losses, arrival = [], [], None
    for t, row in enumerate(rows):
        if t >= 500 or row["t"] != t or row["state"]["current_step"] != t + 1:
            raise AssertionError("complete contiguous alias H500 required")
        old_position = np.asarray(previous["positions_xyz"], dtype=float)
        delta = np.asarray(decision["assigned_targets_xyz"], dtype=float) - old_position
        distance = np.sqrt(np.sum(delta * delta, axis=1))
        expected_actions = np.zeros((6, 3), dtype=float)
        moving = distance > 1e-6
        expected_actions[moving] = delta[moving] / np.maximum(30.0, distance[moving])[:, None]
        norms = np.linalg.norm(expected_actions, axis=1)
        expected_actions[norms > 1] /= norms[norms > 1, None]
        if arrival is None and np.all(distance <= 1e-6):
            arrival = t
        old.check_close(row["actions"], expected_actions, f"alias actions {t}", diagnostics, atol=1e-12, rtol=0)
        a = np.asarray(row["actions"], dtype=float)
        norms = np.linalg.norm(a, axis=1)
        a[norms > 1] /= norms[norms > 1, None]
        after = old_position + 30 * a
        after[:, :2] = np.clip(after[:, :2], 0, 5000)
        after[:, 2] = np.clip(after[:, 2], 50, 150)
        old.check_close(row["state"]["positions_xyz"], after, f"alias kinematics {t}", diagnostics, atol=1e-8, rtol=0)
        exact(row["native_rng_sha256"], reset_identity["native_rng_sha256"], f"alias RNG {t}", diagnostics)
        if any(bool(v) != (t == 499) for v in row["terminations"].values()) or any(row["truncations"].values()):
            raise AssertionError("alias terminal behavior mismatch")
        association, routes = row["state"]["user_association"], row["state"]["routing_paths"]
        backhauled = [a >= 0 and str(a) in routes for a in association]
        exact(backhauled, row["state"]["backhauled_users_mask"], f"alias primary coverage mask {t}", diagnostics)
        info = row["state"]["reward_info"]
        old.check_close(info["coverage_backhauled"], sum(backhauled) / 50, f"alias coverage {t}", diagnostics)
        old.check_close(info["contract_reward"], .5 * (info["coverage_backhauled"] + info["throughput_term"]), f"alias J {t}", diagnostics)
        old.check_close(sum(row["rewards"].values()), info["contract_reward"], f"alias returned team {t}", diagnostics, atol=1e-9, rtol=0)
        for k in SERIES:
            values[k].append(info[k])
        changes.append(sum(a != b for a, b in zip(previous["user_association"], association)))
        losses.append(sum(a and not b for a, b in zip(previous["backhauled_users_mask"], backhauled)))
        previous = row["state"]
        if t % 25 == 0:
            bill.check()
    if len(values[SERIES[0]]) != 500 or result["steps"] != 500:
        raise AssertionError("alias episode missing frames")
    for k in SERIES:
        old.check_close(values[k], result["series"][k], "alias complete " + k, diagnostics)
        old.check_close([np.mean(values[k]), np.mean(values[k][-100:])],
                        [result[k + "_mean_all"], result[k + "_mean_final100"]], "alias aggregates " + k, diagnostics)
    exact(changes, result["association_changes_per_step"], "alias association transitions", diagnostics)
    exact(losses, result["backhaul_losses_per_step"], "alias backhaul loss transitions", diagnostics)
    gap = float(np.linalg.norm(np.asarray(previous["positions_xyz"]) - decision["assigned_targets_xyz"], axis=1).max())
    if arrival is None and gap <= 1e-6:
        arrival = 500
    exact(arrival, result["arrival_step"], "alias arrival", diagnostics)
    old.check_close(gap, result["final_max_distance_to_target_m"], "alias final target gap", diagnostics, atol=1e-8, rtol=0)
    return {k: {"mean_all": float(np.mean(v)), "mean_final100": float(np.mean(v[-100:]))} for k, v in values.items()} | {
        "arrival_step": arrival, "association_change_count": sum(changes), "backhaul_loss_events": sum(losses)}


def complete_reader(store, prior, cases, diagnostics):
    from ..b02.native import Native
    started = time.perf_counter()
    panel = []
    e.verify_outputs(store.root, store.files)
    for world in range(107100000, 107100064):
        arms = {}
        for arm in ("G", "Q", "P"):
            case = cases[(world, arm)]
            decision = e.load_output(store.root, store.files, case["decision_path"])
            gate = case["gate"]
            if gate["new_episode"]:
                result = e.load_output(store.root, store.files, case["native_path"])
                path = e.relative_path(store.root, case["trace_path"])
                with Native(store.bill) as native:
                    env = native.host.make_host(world, area_size=5000)
                    old.verify_world_identity(decision, result["reset_identity"], gate["reference_identity"])
                    physics_means = old.trace_reader(path, env, native, decision, result, diagnostics, gate["reference_identity"])
                    if world in AUDIT_WORLDS:
                        relative = f"raw/reader/{world}/original-executor.jsonl.gz"
                        audit = old.original_episode_audit(env, native, decision, path, diagnostics, e.relative_path(store.root, relative))
                        store.register(relative)
                        store.write_gzip(f"raw/reader/{world}/original-executor.json.gz", audit)
                readings = reaggregate(path, decision, result, diagnostics, result["reset_identity"], store.bill)
                exact({k: readings[k] for k in SERIES}, {k: physics_means[k] for k in SERIES}, f"{world} new physics/whole reader", diagnostics)
            else:
                result = prior.json(gate["prior_native"])
                path = prior.path(gate["prior_trace"])
                readings = reaggregate(path, decision, result, diagnostics, decision["reset_identity"], store.bill)
                store.bill.charge("prior_episode_reads")
                store.bill.charge("reused_episodes")
            arms[arm] = {"native": readings, "static_reward": decision["static_info"]["contract_reward"],
                         "rank": decision["requested_rank"], "fallback": decision["fallback"], "alias": gate["alias_arm"],
                         "cold_selection_wall_seconds": decision["parent_cold_selection_seconds"],
                         "selection_child_cpu_seconds": decision["child_selection_cpu"]["total_seconds"],
                         "selection_static_calls": gate["selection_static_calls"], "decision_timing": decision["timing"],
                         "new_native_wall_seconds": result["native_wall_seconds_including_trace"] if gate["new_episode"] else None,
                         "full_episode_cpu_measurement": "not measured contemporaneously; reused trajectories have no new full-episode timing"}
        jdiff = arms["Q"]["native"]["contract_reward"]["mean_all"] - arms["G"]["native"]["contract_reward"]["mean_all"]
        staticdiff = arms["Q"]["static_reward"] - arms["G"]["static_reward"]
        p_jdiff = arms["Q"]["native"]["contract_reward"]["mean_all"] - arms["P"]["native"]["contract_reward"]["mean_all"]
        p_staticdiff = arms["Q"]["static_reward"] - arms["P"]["static_reward"]
        panel.append({"world": world, "arms": arms, "Q_minus_G_J": jdiff, "Q_minus_G_static": staticdiff,
                      "Q_minus_P_J": p_jdiff, "Q_minus_P_static": p_staticdiff,
                      "Q_P_static_native_sign_reversal": p_staticdiff * p_jdiff < 0,
                      "static_native_sign_reversal": staticdiff * jdiff < 0})
        store.progress("reader", completed_worlds=len(panel))
    store.write_gzip("raw/reader/per-world.json.gz", panel)
    comparisons = {}
    for left, right in (("Q", "G"), ("Q", "P"), ("G", "P")):
        result = {k: old.paired([r["arms"][left]["native"][k]["mean_all"] - r["arms"][right]["native"][k]["mean_all"] for r in panel]) for k in SERIES}
        result.update({k: old.paired([r["arms"][left]["native"][k] - r["arms"][right]["native"][k] for r in panel])
                       for k in ("association_change_count", "backhaul_loss_events")})
        result.update({k: old.paired([r["arms"][left][k] - r["arms"][right][k] for r in panel]) for k in ("static_reward", "cold_selection_wall_seconds", "selection_child_cpu_seconds", "selection_static_calls")})
        for statistic in result.values():
            statistic["uncertainty_scope"] = "descriptive df63 exposed-world interval; adaptive exploratory reuse, no fresh confirmation or fit replication"
        comparisons[left + "_minus_" + right] = result
    def descriptive(values):
        result = old.paired(values)
        result["uncertainty_scope"] = "descriptive df63 exposed-world interval; no fresh confirmation or fit replication"
        return result
    return {"status": "complete", "worlds": 64, "arms": ["G", "Q", "P"], "comparisons": comparisons,
            "absolute_native": {a: {k: descriptive([r["arms"][a]["native"][k]["mean_all"] for r in panel]) for k in SERIES} for a in ("G", "Q", "P")},
            "absolute_service_transitions": {a: {k: descriptive([r["arms"][a]["native"][k] for r in panel])
                                                  for k in ("association_change_count", "backhaul_loss_events")} for a in ("G", "Q", "P")},
            "arrival": {a: {"steps_by_world": [r["arms"][a]["native"]["arrival_step"] for r in panel],
                            "not_arrived": sum(r["arms"][a]["native"]["arrival_step"] is None for r in panel)} for a in ("G", "Q", "P")},
            "absolute_selection_cost": {a: {k: descriptive([r["arms"][a][k] for r in panel]) for k in ("cold_selection_wall_seconds", "selection_child_cpu_seconds", "selection_static_calls")} for a in ("G", "Q", "P")},
            "Q_rank_counts": [sum(r["arms"]["Q"]["rank"] == rank for r in panel) for rank in range(3)],
            "fallback_worlds": {a: [r["world"] for r in panel if r["arms"][a]["fallback"]] for a in ("G", "Q", "P")},
            "static_native_sign_reversal_worlds": [r["world"] for r in panel if r["static_native_sign_reversal"]],
            "Q_P_static_native_sign_reversal_worlds": [r["world"] for r in panel if r["Q_P_static_native_sign_reversal"]],
            "new_main_episodes": 7, "reused_Q_episodes": 57, "reused_G_P_episodes": 128, "original_audits": 2,
            "fits": 0, "weights_or_GPU_forwards": 0, "reader_seconds": time.perf_counter() - started,
            "information_boundary": "36-query feedback is static search-oracle progress before flight, not native service-history adaptation",
            "host_clock": "planning wall delay reported separately; it does not advance the H500 host clock",
            "timing_scope": "fresh process through immutable selection-ready, before alias lookup; instrumented decision timing, no fictional new full-episode timing",
            "trust_boundary": "inherits bound B02 paid per-state physics for aliases; seven new per-state checks use pinned radio, not independent physical laws",
            "prior_bill": "B01, B02 and historical training/source/alias-arithmetic costs remain sunk; new evaluation reuse is not an online speedup",
            "support_cost": "metered run bill separate from partly unmetered support; unknown is not zero"}

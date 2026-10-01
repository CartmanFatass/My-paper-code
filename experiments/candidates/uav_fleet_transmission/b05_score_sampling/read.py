"""Full B05 saved-history replay, with no new environment transition."""
import json
from pathlib import Path
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, MemoC, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.policies import FeatureMemo, indexed_uniform
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity
from .assets import load_assets, verify_assets, verify_calibration
from .contract import (ARMS, FROZEN, LOW, HIGH, OBJECT, Protocol, actor_for, array_digest,
                       source_identities, write_json)
from .policies import ORDINARY_ARMS
from .reading import comparisons, episode_metrics, grid_probabilities


def equal(actual, expected, label, atol=0.):
    a, b = np.asarray(actual), np.asarray(expected)
    valid = a.shape == b.shape and (np.array_equal(a, b) if not atol else np.allclose(a, b, rtol=0., atol=atol))
    if not valid:
        raise AssertionError(label)


def probability_reference(arm, base):
    """Reconstruct the declared formula, without calling the candidate kernel."""
    if arm in ORDINARY_ARMS:
        c = base["action_index"]
        epsilon = .05 if arm == "Q05" else 0. if arm == "C" else .1
        p = np.full(27, epsilon / 26., dtype=np.float64)
        p[c] = 1 - epsilon
        scores = base["scores"]
        if arm == "G" and not np.all(scores == scores[0]):
            alternatives = [i for i in range(27) if i != c]
            values = scores[alternatives]
            weights = np.exp((values - max(values)) / .014)
            p[alternatives] = .1 * (weights / weights.sum(dtype=np.float64))
        return p
    values = base["logits"].astype(np.float64) / (2. if arm == "Bstar_L0" else 1.)
    weights = np.exp(values - max(values))
    return weights / weights.sum(dtype=np.float64)


def check_episode(raw, row, protocol, actor, *, progress=None):
    state = dict(memos=[], actor_rows=0, indexed_draws=0, verified_native_ticks=0)
    try:
        return _check_episode(raw, row, protocol, actor, state)
    finally:
        if progress is not None:
            progress.update(arm=row["arm"], world=row["world"], tape=row["tape"],
                            replay_counts=sum_counts(m.counters for m in state["memos"]),
                            actor_rows_attempted=state["actor_rows"], indexed_draws=state["indexed_draws"],
                            verified_native_ticks=state["verified_native_ticks"], new_native_steps=0)


def _check_episode(raw, row, protocol, actor, state):
    h, d, arm = protocol.horizon, protocol.horizon // 4, row["arm"]
    ordinary = arm in ORDINARY_ARMS
    shapes = dict(observations=(h, 5, 104), terminal_observation=(5, 104), commands=(h, 5, 3),
                  positions=(h + 1, 5, 3), initial_users=(50, 2), reward=(h,), served=(h,),
                  sinr_quality=(h,), sinr=(h, 5, 50), connections=(h, 5, 50), transmitter_mask=(h, 5),
                  features=(d, 5, 114), probabilities=(d, 5, 27), decision_ticks=(d,))
    shapes.update({k: (d, 5) for k in ("nav_pre", "nav_next", "fallback", "action_index", "memo_hit",
                   "n_current", "n_peers", "innovation", "entropy", "behavior_entropy", "chosen_probability", "logp")})
    shapes.update(dict(c_index=(d, 5), policy_scores=(d, 5, 27), policy_served=(d, 5, 27)) if ordinary
                  else dict(logits=(d, 5, 27)))
    if set(raw) != set(shapes):
        raise AssertionError("raw schema changed")
    for key, shape in shapes.items():
        if raw[key].shape != shape or not np.isfinite(raw[key]).all():
            raise AssertionError("nonfinite/wrong raw shape: " + key)
    for key in ("observations", "terminal_observation", "commands", "features") + (() if ordinary else ("logits",)):
        if raw[key].dtype != np.float32:
            raise AssertionError("FP32 contract: " + key)
    for key in ("positions", "initial_users", "probabilities", "innovation", "sinr", "reward", "sinr_quality"):
        if raw[key].dtype != np.float64:
            raise AssertionError("FP64 contract: " + key)
    for key in ("connections", "transmitter_mask", "fallback", "memo_hit"):
        if raw[key].dtype != bool:
            raise AssertionError("boolean contract: " + key)
    for key in ("nav_pre", "nav_next", "action_index", "decision_ticks", "served", "n_current", "n_peers"):
        if not np.issubdtype(raw[key].dtype, np.integer):
            raise AssertionError("integer contract: " + key)
    if np.any((raw["action_index"] < 0) | (raw["action_index"] >= 27)):
        raise AssertionError("invalid category")
    equal(raw["decision_ticks"], np.arange(0, h, 4), "decision clocks")
    if not raw["transmitter_mask"].all():
        raise AssertionError("all-on host changed")
    equal(raw["commands"], np.repeat(COMMANDS[raw["action_index"]], 4, axis=0), "four-tick holds")
    equal(raw["positions"][1:], np.clip(raw["positions"][:-1] + raw["commands"].astype(np.float64) * 30., LOW, HIGH),
          "native clipped motion")
    normalized = raw["positions"].copy()
    normalized[..., :2] /= 1000.
    normalized[..., 2] = (normalized[..., 2] - 50.) / 100.
    equal(raw["observations"][..., :3], normalized[:-1].astype(np.float32), "actual own position provenance")
    equal(raw["terminal_observation"][..., :3], normalized[-1].astype(np.float32), "terminal position")
    equal(raw["observations"][..., -1], np.broadcast_to((np.arange(h) / h).astype(np.float32)[:, None], (h, 5)), "clock")
    equal(raw["terminal_observation"][..., -1], np.ones(5), "terminal clock")
    served = raw["connections"].sum(axis=(1, 2))
    equal(raw["served"], served, "native service reduction")
    if (np.any(raw["connections"].sum(axis=1) > 1) or np.any(raw["connections"].sum(axis=2) > 10)
            or np.any(raw["sinr"][raw["connections"]] < 3.)):
        raise AssertionError("native assignment/capacity/eligibility")
    quality = np.where(raw["connections"], np.clip((raw["sinr"] - 3.) / 30., 0., 1.), 0.).sum(axis=(1, 2)) / np.maximum(served, 1)
    equal(raw["sinr_quality"], quality, "native quality", 1e-14)
    equal(raw["reward"], .7 * served / 50. + .3 * quality, "native reward", 1e-12)
    state["verified_native_ticks"] = h
    memos = [MemoC() if ordinary else FeatureMemo() for _ in range(5)]
    state["memos"] = memos
    nav = np.array([initial_nav(r) for r in raw["observations"][0]])
    sampling_root = protocol.sampling_roots[max(row["tape"], 0)]
    if row["sampling_root"] != (None if arm == "C" else sampling_root):
        raise AssertionError("sampling identity")
    actor_rows = 0
    for di, tick in enumerate(raw["decision_ticks"]):
        equal(raw["nav_pre"][di], nav, "pre-navigation continuity")
        for agent, memo in enumerate(memos):
            base = memo.query(raw["observations"][tick, agent].copy(), int(tick), int(nav[agent]))
            for key in ("features", "fallback", "memo_hit", "n_current", "n_peers"):
                equal(raw[key][di, agent], base[key], "saved-history replay: " + key)
            nav[agent] = base["next_nav"]
            if ordinary:
                equal(raw["c_index"][di, agent], base["action_index"], "source C category")
                equal(raw["policy_scores"][di, agent], base["scores"], "full source C score replay")
                equal(raw["policy_served"][di, agent], base["served"], "full source C service replay")
            else:
                state["actor_rows"] += 1
                with torch.inference_mode():
                    base["logits"] = actor(torch.from_numpy(base["features"]).reshape(1, 114))[0].cpu().numpy()
                actor_rows += 1  # Intentionally check every decision, including deployed cache hits.
                equal(raw["logits"][di, agent], base["logits"], "one-row immutable actor replay")
            p = probability_reference(arm, base)
            equal(raw["probabilities"][di, agent], p, "independent probability formula")
            state["indexed_draws"] += int(arm != "C")
            u = -1. if arm == "C" else indexed_uniform(sampling_root, row["world"], int(tick), agent)
            equal(raw["innovation"][di, agent], u, "indexed innovation")
            cdf = np.cumsum(p, dtype=np.float64)
            cdf[-1] = 1.
            choice = base["action_index"] if arm == "C" else int(np.searchsorted(cdf, u, side="right"))
            equal(raw["action_index"][di, agent], choice, "ordered inverse-CDF category")
            positive = p > 0
            entropy = float(-np.sum(p[positive] * np.log(p[positive])))
            equal(raw["entropy"][di, agent], entropy, "entropy")
            equal(raw["behavior_entropy"][di, agent], entropy, "behavior entropy")
            equal(raw["chosen_probability"][di, agent], p[choice], "chosen density")
            equal(raw["logp"][di, agent], np.log(p[choice]), "chosen log density")
        equal(raw["nav_next"][di], nav, "next-navigation continuity")
    replay_counts = sum_counts(memo.counters for memo in memos)
    deployed = dict(replay_counts, sampled_draws=0 if arm == "C" else d * 5,
                    score_tail_evaluations=d * 5 if arm == "G" else 0)
    if not ordinary:
        deployed["neural_rows"] = deployed["misses"]
        deployed["cache_array_bytes"] += deployed["misses"] * 27 * 4
    if deployed != row["policy_counts"]:
        raise AssertionError("actual cache/helper/model accounting")
    for key, value in episode_metrics(raw).items():
        equal(row[key], value, "episode metric: " + key)
    for key, value in row.items():
        if key.endswith("_seconds") and (not np.isfinite(value) or value < 0):
            raise AssertionError("invalid timing field")
    equal(row["initial_state_sha256"], array_digest(raw["positions"][0], raw["initial_users"]), "initial geometry hash")
    return dict(ordinary_policy_counts=replay_counts if ordinary else {},
                feature_counts={} if ordinary else replay_counts, actor_rows=actor_rows,
                ordinary_queries=d * 5 if ordinary else 0, student_queries=0 if ordinary else d * 5,
                indexed_draws=0 if arm == "C" else d * 5, native_team_ticks_verified=h,
                native_agent_motion_ticks_verified=5 * h, new_native_steps=0)


def g_saved_comparison(raw):
    """Q10 at actual G histories: categorical and geometric, never a reward counterfactual."""
    c = raw["c_index"]
    q = np.full((*c.shape, 27), .1 / 26., dtype=np.float64)
    np.put_along_axis(q, c[..., None], .9, axis=-1)
    cdf = np.cumsum(q, axis=-1)
    cdf[..., -1] = 1.
    choice = (raw["innovation"][..., None] >= cdf).sum(axis=-1)
    g = raw["action_index"]
    starts = raw["positions"][raw["decision_ticks"]].copy()
    hypothetical, ever = starts.copy(), np.zeros(c.shape, dtype=bool)
    for offset in range(1, 5):
        hypothetical = np.clip(hypothetical + COMMANDS[choice].astype(np.float64) * 30., LOW, HIGH)
        ever |= np.any(hypothetical != raw["positions"][raw["decision_ticks"] + offset], axis=-1)
    p, scores = raw["probabilities"], raw["policy_scores"]
    expected_gain = np.sum((p - q) * scores, axis=-1)
    effective_gain = np.sum((grid_probabilities(p) - grid_probabilities(q)) * scores, axis=-1)
    realized_gain = np.take_along_axis(scores, g[..., None], -1)[..., 0] - np.take_along_axis(scores, choice[..., None], -1)[..., 0]
    return dict(queries=int(c.size), geometric_agent_ticks=int(c.size * 4),
                different_categories=int(np.count_nonzero(g != choice)), different_physical_holds=int(ever.sum()),
                different_final_positions=int(np.any(hypothetical != raw["positions"][raw["decision_ticks"] + 4], axis=-1).sum()),
                g_departures=int(np.count_nonzero(g != c)), q10_departures=int(np.count_nonzero(choice != c)),
                departure_event_changes=int(np.count_nonzero((g != c) != (choice != c))),
                exact_all_score_ties=int(np.all(scores == scores[..., :1], axis=-1).sum()),
                mean_expected_proxy_gain=float(expected_gain.mean()), min_expected_proxy_gain=float(expected_gain.min()),
                mean_grid_expected_proxy_gain=float(effective_gain.mean()), mean_realized_proxy_gain=float(realized_gain.mean()),
                zero_float_categories=int(np.count_nonzero(p == 0)), zero_grid_categories=int(np.count_nonzero(grid_probabilities(p) == 0)),
                reward_counterfactuals=0)


def read_result(out, repo, *, fixture_models=None, fixture_records=None):
    state = dict(completed_episodes=0, completed_replay=[], inflight={})
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    try:
        return _read_result(out, repo, fixture_models=fixture_models, fixture_records=fixture_records, state=state)
    except BaseException as error:
        write_json(Path(out) / "reading.json", dict(status="FAILED", error=repr(error), traceback=traceback.format_exc(),
                   reader_cpu_seconds=time.process_time() - start_cpu, reader_wall_seconds=time.perf_counter() - start_wall,
                   actual_work=state, new_native_steps=0))
        raise


def _read_result(out, repo, *, fixture_models, fixture_records, state):
    out, repo = Path(out), Path(repo)
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    config = json.loads((out / "config.json").read_text())
    summary = json.loads((out / "summary.json").read_text())
    protocol = Protocol.from_dict(config["protocol"])
    fixture = fixture_models is not None
    if (fixture and (protocol == FROZEN or config["scientific_invocation"])) or (not fixture and protocol != FROZEN):
        raise ValueError("fixture/production protocol mismatch")
    if config["object"] != OBJECT or summary["state"] != "COMPLETE" or summary["launch_sha"] != config["launch_sha"]:
        raise AssertionError("incomplete or wrong study identity")
    if not fixture and (config["runtime"]["torch_threads"] != 1 or config["runtime"]["torch_interop_threads"] != 1
                        or not config["runtime"]["deterministic_algorithms"] or torch.get_num_threads() != 1
                        or torch.get_num_interop_threads() != 1 or not torch.are_deterministic_algorithms_enabled()):
        raise AssertionError("production deterministic single-thread contract")
    if source_identities(repo) != config["source_identities"]:
        raise AssertionError("source identity changed")
    if not fixture:
        equal(config["calibration"], verify_calibration(repo), "calibration binding")
        models, records = load_assets(protocol)
        if records != config["assets"]:
            raise AssertionError("production asset binding changed")
    else:
        models, records = fixture_models, fixture_records
    verify_assets(models, records)
    rows, work, g_rows = summary["episodes"], [], []
    state["completed_replay"] = work
    expected_order = [(arm, world, tape) for wi, world in enumerate(protocol.worlds) for arm, tape in protocol.episode_order(wi)]
    if [(r["arm"], r["world"], r["tape"]) for r in rows] != expected_order:
        raise AssertionError("complete rotated evaluation order")
    expected_raw = set()
    for row in rows:
        path = (out / row["raw"]["path"]).resolve()
        if not path.is_relative_to((out / "raw").resolve()):
            raise AssertionError("raw identity escapes output")
        expected_raw.add(path.name)
        identity = file_identity(path)
        if any(identity[k] != row["raw"][k] for k in ("bytes", "sha256")):
            raise AssertionError("raw file identity mismatch")
        with np.load(path, allow_pickle=False) as archive:
            raw = {key: archive[key] for key in archive.files}
        state["inflight"] = {}
        work.append(check_episode(raw, row, protocol, actor_for(row["arm"], models), progress=state["inflight"]))
        if row["arm"] == "G":
            g_rows.append(dict(world=row["world"], tape=row["tape"], **g_saved_comparison(raw)))
        state["completed_episodes"] += 1
        state["inflight"] = {}
    if {p.name for p in (out / "raw").iterdir()} != expected_raw:
        raise AssertionError("undeclared or partial raw output")
    for world in protocol.worlds:
        if len({r["initial_state_sha256"] for r in rows if r["world"] == world}) != 1:
            raise AssertionError("paired initial geometry differs")
    if summary["counts"] != protocol.expected():
        raise AssertionError("complete realized exposure mismatch")
    paired = comparisons(rows, protocol)
    if summary["paired"] != paired:
        raise AssertionError("paired-world result reconstruction")
    for arm in ARMS:
        if summary["policy_counts"][arm] != sum_counts(r["policy_counts"] for r in rows if r["arm"] == arm):
            raise AssertionError("aggregate policy cost")
    verify_assets(models, records)
    result = dict(status="VERIFIED", object=OBJECT, launch_sha=config["launch_sha"], scientific_invocation=not fixture,
                  protocol=protocol.to_dict(), paired=paired, episodes=len(rows), counts=summary["counts"],
                  policy_counts=summary["policy_counts"], saved_G_Q10=g_rows,
                  replay_counts=dict(ordinary=sum_counts(w["ordinary_policy_counts"] for w in work),
                                     features=sum_counts(w["feature_counts"] for w in work),
                                     **sum_counts({k: v for k, v in w.items() if not k.endswith("counts")} for w in work)),
                  reader_cpu_seconds=time.process_time() - start_cpu, reader_wall_seconds=time.perf_counter() - start_wall,
                  process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  peak_scope="shared worker/reader process high-water mark; not a sum of peaks",
                  complete_worker_cpu_seconds=summary["worker_cpu_seconds"],
                  complete_worker_wall_seconds=summary["worker_wall_seconds"],
                  scope="All saved raw arrays, original source scores, helper/navigation/cache state, every student "
                        "one-row actor, random address, CDF/category, native metric/command, paired geometry and summary checked. "
                        "G/Q10 saved-history differences are not alternative native rewards; 0 new environment steps.")
    write_json(out / "reading.json", result)
    return result

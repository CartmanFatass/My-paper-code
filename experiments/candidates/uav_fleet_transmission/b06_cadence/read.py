"""Independent full-context replay of B06; no environment is constructed or stepped."""
import json
from pathlib import Path
import resource
import time
import traceback
import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02 import controllers as inherited
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity
from experiments.candidates.uav_fleet_transmission.b05_score_sampling.read import equal, probability_reference
from .assets import load_assets, verify_assets, verify_calibration
from .contract import (CELLS, FROZEN, LOW, HIGH, OBJECT, ORDINARY_ARMS, Protocol, actor_for,
                       array_digest, cell_name, source_identities, write_json)
from .reading import comparisons, episode_metrics


def _native_arrays(raw, h, d, ordinary):
    shapes = dict(observations=(h, 5, 104), terminal_observation=(5, 104), commands=(h, 5, 3),
                  positions=(h + 1, 5, 3), initial_users=(50, 2), reward=(h,), served=(h,),
                  sinr_quality=(h,), sinr=(h, 5, 50), connections=(h, 5, 50), transmitter_mask=(h, 5),
                  initial_sinr=(5, 50), initial_connections=(5, 50),
                  features=(d, 114), probabilities=(d, 27))
    shapes.update({k: (h, 5) for k in ("query_mask", "own_count", "count_loss", "extra_available", "extra_used")})
    shapes.update({k: (d,) for k in ("decision_ticks", "decision_agents", "query_kind", "held_before",
                   "remaining_motion_changed", "nav_pre", "nav_next", "fallback", "action_index", "memo_hit",
                   "n_current", "n_peers", "innovation", "entropy", "behavior_entropy", "chosen_probability", "logp")})
    shapes.update(dict(c_index=(d,), policy_scores=(d, 27), policy_served=(d, 27)) if ordinary
                  else dict(logits=(d, 27)))
    if set(raw) != set(shapes):
        raise AssertionError("raw schema changed")
    for key, shape in shapes.items():
        if raw[key].shape != shape or not np.isfinite(raw[key]).all():
            raise AssertionError("nonfinite/wrong raw shape: " + key)
    fp32 = ("observations", "terminal_observation", "commands", "features") + (() if ordinary else ("logits",))
    fp64 = ("positions", "initial_users", "probabilities", "innovation", "sinr", "initial_sinr", "reward",
            "sinr_quality", "entropy", "behavior_entropy", "chosen_probability", "logp")
    boolean = ("connections", "initial_connections", "transmitter_mask", "fallback", "memo_hit", "query_mask",
               "count_loss", "extra_available", "extra_used", "remaining_motion_changed")
    integer = ("nav_pre", "nav_next", "action_index", "decision_ticks", "decision_agents", "query_kind",
               "held_before", "served", "n_current", "n_peers", "own_count")
    for names, dtype in ((fp32, np.float32), (fp64, np.float64), (boolean, np.bool_)):
        for key in names:
            if raw[key].dtype != dtype:
                raise AssertionError("dtype contract: " + key)
    for key in integer:
        if not np.issubdtype(raw[key].dtype, np.integer):
            raise AssertionError("integer contract: " + key)
    if (np.any((raw["action_index"] < 0) | (raw["action_index"] >= 27))
            or np.any((raw["decision_agents"] < 0) | (raw["decision_agents"] >= 5))):
        raise AssertionError("invalid category or agent")
    if not raw["transmitter_mask"].all():
        raise AssertionError("all-on host changed")
    equal(raw["positions"][1:], np.clip(raw["positions"][:-1] + raw["commands"].astype(np.float64) * 30., LOW, HIGH),
          "native clipped motion")
    normalized = raw["positions"].copy()
    normalized[..., :2] /= 1000.
    normalized[..., 2] = (normalized[..., 2] - 50.) / 100.
    equal(raw["observations"][..., :3], normalized[:-1].astype(np.float32), "own position provenance")
    equal(raw["terminal_observation"][..., :3], normalized[-1].astype(np.float32), "terminal position")
    equal(raw["observations"][..., -1], np.broadcast_to((np.arange(h) / h).astype(np.float32)[:, None], (h, 5)), "clock")
    equal(raw["terminal_observation"][..., -1], np.ones(5), "terminal clock")
    sinr = np.concatenate((raw["initial_sinr"][None], raw["sinr"]), axis=0)
    connections = np.concatenate((raw["initial_connections"][None], raw["connections"]), axis=0)
    if (np.any(connections.sum(axis=1) > 1) or np.any(connections.sum(axis=2) > 10)
            or np.any(sinr[connections] < 3.) or np.any((sinr >= 3.).sum(axis=1) > 1)):
        raise AssertionError("native uniqueness/capacity/eligibility")
    equal(connections.sum(axis=2), np.minimum(10, (sinr >= 3.).sum(axis=2)), "native eligible count at capacity")
    observations = np.concatenate((raw["observations"], raw["terminal_observation"][None]), axis=0)
    slot_counts = np.count_nonzero(observations[..., 3:63].reshape(h + 1, 5, 20, 3)[..., 2] > 0., axis=-1)
    equal(slot_counts, np.minimum(20, (sinr >= 3.).sum(axis=2)), "local user-slot count provenance")
    equal(np.minimum(10, slot_counts), connections.sum(axis=2), "lawful count equals actual own service")
    served = raw["connections"].sum(axis=(1, 2))
    equal(raw["served"], served, "native service reduction")
    quality = np.where(raw["connections"], np.clip((raw["sinr"] - 3.) / 30., 0., 1.), 0.).sum(axis=(1, 2)) / np.maximum(served, 1)
    equal(raw["sinr_quality"], quality, "native quality", 1e-14)
    equal(raw["reward"], .7 * served / 50. + .3 * quality, "native reward", 1e-12)
    return np.minimum(10, slot_counts[:-1])


def _source_c(controller, observation, tick, nav):
    """Full immutable C on each actual context, including deployed cache hits."""
    own, users, observed_sinr, peers = inherited.original._parse(observation)
    controller._nav_index = int(nav)
    controller.counters["ingests"] += 1
    _, _, _, indices = controller._ingest(users, int(tick))
    scores, served, _, _ = controller._decide(own, observed_sinr, peers, indices)
    plan = controller._plan
    return dict(action_index=plan["selected_index"], next_nav=controller._nav_index, fallback=plan["fallback"],
                scores=scores, served=served, command=controller._command.copy(),
                n_current=len(users), n_peers=len(peers),
                features=inherited._features(observation, int(nav), plan["fallback"]))


def check_episode(raw, row, protocol, actor, *, progress=None):
    state = dict(ordinary_queries=0, student_queries=0, actor_rows=0, indexed_draws=0,
                 helper_counts={}, source_controllers=[], verified_native_ticks=0)
    try:
        return _check_episode(raw, row, protocol, actor, state)
    finally:
        if progress is not None:
            progress.update({k: v for k, v in state.items() if k != "source_controllers"})
            progress.update(arm=row["arm"], mode=row["mode"], world=row["world"], tape=row["tape"],
                            source_counts=sum_counts(c.counters for c in state["source_controllers"]), new_native_steps=0)


def _check_episode(raw, row, protocol, actor, state):
    h, arm, mode = protocol.horizon, row["arm"], row["mode"]
    ordinary, d = arm in ORDINARY_ARMS, len(raw["decision_ticks"])
    native_counts = _native_arrays(raw, h, d, ordinary)
    state["verified_native_ticks"] = h
    controllers = [inherited.original.LocalController(history=False) for _ in range(5)] if ordinary else []
    state["source_controllers"] = controllers
    caches = [set() for _ in range(5)]
    nav = np.asarray([inherited.initial_nav(r) for r in raw["observations"][0]], dtype=np.int64)
    held, used = np.full(5, -1, dtype=np.int64), np.zeros(5, dtype=bool)
    commands = np.zeros((5, 3), dtype=np.float32)
    deployed = ({name: 0 for name in inherited.COUNTER_NAMES} if ordinary else dict(
        requests=0, hits=0, misses=0, helper_calls=0, helper_setup_links=0, helper_extreme_links=0,
        neural_rows=0, cache_entries=0, cache_key_bytes=0, cache_array_bytes=0))
    deployed.update(sampled_draws=0, score_tail_evaluations=0)
    sampling_root = protocol.sampling_roots[max(row["tape"], 0)]
    equal(row["sampling_root"], None if arm == "C" else sampling_root, "sampling identity")
    index = 0
    for tick in range(h):
        boundary = tick % 4 == 0
        if boundary:
            used[:] = False
        loss = native_counts[tick] < native_counts[tick - 1] if tick else np.zeros(5, dtype=bool)
        available = np.logical_not(used) & (not boundary) if mode == "E" else np.zeros(5, dtype=bool)
        extra = loss & available if mode == "E" else np.zeros(5, dtype=bool)
        query = np.ones(5, dtype=bool) if boundary or mode == "H1" else extra
        if mode == "E":
            used |= extra
        equal(raw["query_mask"][tick], query, "independent query eligibility")
        equal(raw["own_count"][tick], native_counts[tick] if mode == "E" else np.full(5, -1), "gate count")
        equal(raw["count_loss"][tick], loss if mode == "E" else np.zeros(5, dtype=bool), "consecutive count loss")
        equal(raw["extra_available"][tick], available, "original-block extra availability")
        equal(raw["extra_used"][tick], used, "spent allowance")
        for agent in np.flatnonzero(query):
            if index >= d:
                raise AssertionError("missing decision record")
            expected_kind = 0 if boundary else 1 if extra[agent] else 2
            equal((raw["decision_ticks"][index], raw["decision_agents"][index], raw["query_kind"][index]),
                  (tick, agent, expected_kind), "ordered actual decision address")
            equal(raw["nav_pre"][index], nav[agent], "pre-navigation continuity")
            equal(raw["held_before"][index], held[agent], "held category continuity")
            observation = raw["observations"][tick, agent]
            key = observation[:103].tobytes() + bytes([int(nav[agent])])
            hit = key in caches[agent]
            equal(raw["memo_hit"][index], hit, "episode-private exact cache")
            deployed["requests"] += 1
            deployed["hits" if hit else "misses"] += 1
            if ordinary:
                state["ordinary_queries"] += 1
                base = _source_c(controllers[agent], observation, tick, nav[agent])
                equal(raw["c_index"][index], base["action_index"], "original C category")
                equal(raw["policy_scores"][index], base["scores"], "full original scores")
                equal(raw["policy_served"][index], base["served"], "full original service scores")
            else:
                state["student_queries"] += 1
                base = inherited.analyze(observation, nav[agent])
                state["helper_counts"] = sum_counts((state["helper_counts"], base["counters"]))
                state["actor_rows"] += 1
                with torch.inference_mode():
                    base["logits"] = actor(torch.from_numpy(base["features"]).reshape(1, 114))[0].cpu().numpy()
                equal(raw["logits"][index], base["logits"], "one-row actor on every actual context")
            for key_name in ("features", "fallback", "n_current", "n_peers"):
                equal(raw[key_name][index], base[key_name], "original replay: " + key_name)
            if not hit:
                caches[agent].add(key)
                deployed["cache_entries"] += 1
                deployed["cache_key_bytes"] += len(key)
                if ordinary:
                    for name, value in dict(trajectories=27, model_ticks=108, objective_reductions=108,
                                           candidate_links=108 * base["n_current"],
                                           setup_links=(1 + base["n_peers"]) * base["n_current"]).items():
                        deployed[name] += value
                    deployed["cache_array_bytes"] += sum(base[k].nbytes for k in ("command", "scores", "served", "features"))
                else:
                    for name, value in base["counters"].items():
                        deployed[name] += value
                    deployed["neural_rows"] += 1
                    deployed["cache_array_bytes"] += base["features"].nbytes + base["logits"].nbytes
            nav[agent] = base["next_nav"]
            equal(raw["nav_next"][index], nav[agent], "next navigation")
            p = probability_reference(arm, base)
            equal(raw["probabilities"][index], p, "independent probability law")
            if arm == "C":
                u, choice = -1., base["action_index"]
            else:
                state["indexed_draws"] += 1
                u = float(np.random.default_rng(np.random.SeedSequence(
                    [int(sampling_root), int(row["world"]), tick, int(agent)])).random())
                cdf = np.cumsum(p, dtype=np.float64)
                cdf[-1] = 1.
                choice = int(np.searchsorted(cdf, u, side="right"))
            deployed["sampled_draws"] += int(arm != "C")
            deployed["score_tail_evaluations"] += int(arm == "G")
            equal(raw["innovation"][index], u, "actual-tick innovation")
            equal(raw["action_index"][index], choice, "ordered CDF category")
            positive = p > 0
            entropy = float(-np.sum(p[positive] * np.log(p[positive])))
            for name, value in dict(entropy=entropy, behavior_entropy=entropy,
                                    chosen_probability=p[choice], logp=np.log(p[choice])).items():
                equal(raw[name][index], value, name)
            previous, replacement = raw["positions"][tick, agent].copy(), raw["positions"][tick, agent].copy()
            changed = False
            if held[agent] >= 0:
                for _ in range(4 - tick % 4):
                    previous = np.clip(previous + 30. * commands[agent].astype(np.float64), LOW, HIGH)
                    replacement = np.clip(replacement + 30. * inherited.COMMANDS[choice].astype(np.float64), LOW, HIGH)
                    changed |= not np.array_equal(previous, replacement)
            equal(raw["remaining_motion_changed"][index], changed, "remaining original-block geometry")
            commands[agent], held[agent] = inherited.COMMANDS[choice], choice
            index += 1
        equal(raw["commands"][tick], commands, "actual command and original-boundary hold")
    equal(index, d, "no extra decision records")
    if deployed != row["policy_counts"]:
        raise AssertionError("deployed cache/helper/model accounting")
    for name, value in episode_metrics(raw).items():
        equal(row[name], value, "episode reduction: " + name)
    for key, value in row.items():
        if key.endswith("_seconds") and (not np.isfinite(value) or value < 0):
            raise AssertionError("invalid timing")
    equal(row["initial_state_sha256"], array_digest(raw["positions"][0], raw["initial_users"],
                                                   raw["initial_sinr"], raw["initial_connections"]), "initial geometry identity")
    return dict(source_counts=sum_counts(c.counters for c in controllers), helper_counts=state["helper_counts"],
                ordinary_queries=state["ordinary_queries"], student_queries=state["student_queries"],
                actor_rows=state["actor_rows"], indexed_draws=state["indexed_draws"],
                gate_count_decodes=h * 5 if mode == "E" else 0,
                gate_checks=(h - h // 4) * 5 if mode == "E" else 0,
                native_team_ticks_verified=h, native_agent_motion_ticks_verified=h * 5, new_native_steps=0)


def read_result(out, repo, *, fixture_models=None, fixture_records=None):
    state = dict(completed_episodes=0, completed_replay=[], inflight={})
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    try:
        return _read_result(out, repo, fixture_models=fixture_models, fixture_records=fixture_records,
                            state=state, start_wall=start_wall, start_cpu=start_cpu)
    except BaseException as error:
        write_json(Path(out) / "reading.json", dict(status="FAILED", error=repr(error), traceback=traceback.format_exc(),
                   reader_cpu_seconds=time.process_time() - start_cpu, reader_wall_seconds=time.perf_counter() - start_wall,
                   actual_work=state, new_native_steps=0))
        raise


def _read_result(out, repo, *, fixture_models, fixture_records, state, start_wall, start_cpu):
    out, repo = Path(out), Path(repo)
    config = json.loads((out / "config.json").read_text())
    summary = json.loads((out / "summary.json").read_text())
    protocol = Protocol.from_dict(config["protocol"])
    fixture = fixture_models is not None
    if (fixture and (protocol == FROZEN or config["scientific_invocation"])) or (not fixture and protocol != FROZEN):
        raise ValueError("fixture/production protocol mismatch")
    if config["object"] != OBJECT or summary["state"] != "COMPLETE" or summary["launch_sha"] != config["launch_sha"]:
        raise AssertionError("incomplete/wrong study identity")
    if not fixture and (config["runtime"]["torch_threads"] != 1 or config["runtime"]["torch_interop_threads"] != 1
                        or not config["runtime"]["deterministic_algorithms"] or torch.get_num_threads() != 1
                        or torch.get_num_interop_threads() != 1 or not torch.are_deterministic_algorithms_enabled()):
        raise AssertionError("production deterministic one-thread contract")
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
    rows, work = summary["episodes"], state["completed_replay"]
    expected_order = [(arm, mode, world, tape) for wi, world in enumerate(protocol.worlds)
                      for arm, mode, tape in protocol.episode_order(wi)]
    if [(r["arm"], r["mode"], r["world"], r["tape"]) for r in rows] != expected_order:
        raise AssertionError("complete rotated panel order")
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
        state["completed_episodes"] += 1
        state["inflight"] = {}
    if {p.name for p in (out / "raw").iterdir()} != expected_raw:
        raise AssertionError("undeclared or partial raw output")
    for world in protocol.worlds:
        if len({r["initial_state_sha256"] for r in rows if r["world"] == world}) != 1:
            raise AssertionError("paired initial state differs")
    protocol.check_counts(summary["counts"])
    expected_queries = dict(ordinary_queries=sum(w["ordinary_queries"] for w in work),
                           student_queries=sum(w["student_queries"] for w in work),
                           sampled_draws=sum(w["indexed_draws"] for w in work),
                           score_tail_evaluations=sum(r["queries"] for r in rows if r["arm"] == "G"))
    for key, value in expected_queries.items():
        equal(summary["counts"][key], value, "actual variable exposure: " + key)
    paired = comparisons(rows, protocol)
    if summary["paired"] != paired:
        raise AssertionError("paired-world reductions")
    for arm, mode in CELLS:
        if summary["policy_counts"][cell_name(arm, mode)] != sum_counts(
                r["policy_counts"] for r in rows if r["arm"] == arm and r["mode"] == mode):
            raise AssertionError("aggregate policy cost")
    verify_assets(models, records)
    result = dict(status="VERIFIED", object=OBJECT, launch_sha=config["launch_sha"], scientific_invocation=not fixture,
                  protocol=protocol.to_dict(), paired=paired, episodes=len(rows), counts=summary["counts"],
                  policy_counts=summary["policy_counts"],
                  replay_counts=dict(source_counts=sum_counts(w["source_counts"] for w in work),
                                     helper_counts=sum_counts(w["helper_counts"] for w in work),
                                     **sum_counts({k: v for k, v in w.items() if not k.endswith("counts")} for w in work)),
                  reader_cpu_seconds=time.process_time() - start_cpu, reader_wall_seconds=time.perf_counter() - start_wall,
                  process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  peak_scope="same worker/reader process high-water mark, not a sum",
                  complete_worker_cpu_seconds=summary["worker_cpu_seconds"],
                  complete_worker_wall_seconds=summary["worker_wall_seconds"],
                  scope="All saved arrays; independent native-count, consecutive-loss scheduler and original-block holds; "
                        "full original C or analytic helper plus one-row actor at EVERY actual query, including deployed "
                        "cache hits; private cache accounting, real-tick random addresses, probabilities/nav/commands/"
                        "aliases, native reductions, paired geometry and complete summaries. Zero new environment steps.")
    write_json(out / "reading.json", result)
    return result

"""Full original-C replay and independent clock/telemetry reconstruction; no env."""
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
from experiments.candidates.uav_fleet_transmission.b06_cadence.read import _source_c
from .contract import CELLS, FROZEN, LOW, HIGH, OBJECT, Protocol, array_digest, cell_name, source_identities, write_json
from .reading import comparisons, episode_metrics


def _native_arrays(raw, h, d):
    shapes = dict(observations=(h, 5, 104), terminal_observation=(5, 104), commands=(h, 5, 3),
                  positions=(h + 1, 5, 3), initial_users=(50, 2), reward=(h,), served=(h,),
                  sinr_quality=(h,), sinr=(h, 5, 50), connections=(h, 5, 50), transmitter_mask=(h, 5),
                  query_mask=(h, 5), initial_sinr=(5, 50), initial_connections=(5, 50),
                  features=(d, 114), probabilities=(d, 27), policy_scores=(d, 27), policy_served=(d, 27),
                  phases=(5,), phase_offsets=(5,))
    shapes.update({key: (d,) for key in ("decision_ticks", "decision_agents", "decision_phases", "hold_ticks",
                   "next_deadline", "held_before", "category_changed", "physical_hold_changed", "nav_pre", "nav_next",
                   "fallback", "action_index", "memo_hit", "n_current", "n_peers", "innovation", "entropy",
                   "behavior_entropy", "chosen_probability", "logp", "c_index")})
    if set(raw) != set(shapes) or d != 5 * h // 4:
        raise AssertionError("raw schema or exact decision exposure changed")
    for key, shape in shapes.items():
        if raw[key].shape != shape or not np.isfinite(raw[key]).all():
            raise AssertionError("nonfinite/wrong raw shape: " + key)
    fp32 = ("observations", "terminal_observation", "commands", "features")
    fp64 = ("positions", "initial_users", "probabilities", "innovation", "sinr", "initial_sinr", "reward",
            "sinr_quality", "entropy", "behavior_entropy", "chosen_probability", "logp", "policy_scores", "policy_served")
    boolean = ("connections", "initial_connections", "transmitter_mask", "fallback", "memo_hit", "query_mask",
               "category_changed", "physical_hold_changed")
    integer = set(shapes) - set(fp32) - set(fp64) - set(boolean)
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


def check_episode(raw, row, protocol, *, progress=None):
    state = dict(ordinary_queries=0, indexed_draws=0, source_controllers=[], verified_native_ticks=0,
                 clipped_hold_comparison_ticks=0)
    try:
        return _check_episode(raw, row, protocol, state)
    finally:
        if progress is not None:
            progress.update({key: value for key, value in state.items() if key != "source_controllers"})
            progress.update(arm=row["arm"], schedule=row["schedule"], world=row["world"], q=row["q"], tape=row["tape"],
                            source_counts=sum_counts(c.counters for c in state["source_controllers"]), new_native_steps=0)


def _check_episode(raw, row, protocol, state):
    h, arm, schedule = protocol.horizon, row["arm"], row["schedule"]
    if ((arm, row["tape"]) not in (("C", -1), ("Q10", 0), ("Q10", 1))
            or schedule not in ("SYNC", "DISPERSED") or row["world"] not in protocol.worlds
            or type(row["q"]) is not int or row["q"] not in range(4)):
        raise AssertionError("undeclared episode identity")
    d = len(raw["decision_ticks"])
    _native_arrays(raw, h, d)
    state["verified_native_ticks"] = h
    offsets = np.random.default_rng(np.random.SeedSequence([protocol.phase_root, row["world"]])).permutation(
        np.array([0, 0, 1, 2, 3], dtype=np.int64))
    phases = np.array([row["q"] if schedule == "SYNC" else (row["q"] + int(offset)) % 4 for offset in offsets])
    equal(raw["phase_offsets"], offsets, "independent world phase roles")
    equal(row["phase_offsets"], offsets, "row phase role binding")
    equal(raw["phases"], phases, "independent per-member phases")
    equal(row["phases"], phases, "row phase binding")
    clocks = [[0, *range(4 + int(phase), h, 4), h] for phase in phases]
    query_sets = [set(clock[:-1]) for clock in clocks]
    deadlines = [{tick: end for tick, end in zip(clock[:-1], clock[1:])} for clock in clocks]
    controllers = [inherited.original.LocalController(history=False) for _ in range(5)]
    state["source_controllers"] = controllers
    caches = [set() for _ in range(5)]
    nav = np.asarray([inherited.initial_nav(obs) for obs in raw["observations"][0]], dtype=np.int64)
    held, commands = np.full(5, -1, dtype=np.int64), np.zeros((5, 3), dtype=np.float32)
    deployed = {name: 0 for name in inherited.COUNTER_NAMES}
    deployed.update(sampled_draws=0, score_tail_evaluations=0)
    sampling_root = protocol.sampling_roots[max(row["tape"], 0)]
    equal(row["sampling_root"], None if arm == "C" else sampling_root, "sampling identity")
    index = 0
    for tick in range(h):
        query = np.array([tick in member_clock for member_clock in query_sets], dtype=bool)
        equal(raw["query_mask"][tick], query, "independent query eligibility")
        for agent in np.flatnonzero(query):
            if index >= d:
                raise AssertionError("missing decision record")
            length = deadlines[agent][tick] - tick
            equal((raw["decision_ticks"][index], raw["decision_agents"][index], raw["decision_phases"][index],
                   raw["hold_ticks"][index], raw["next_deadline"][index]),
                  (tick, agent, phases[agent], length, tick + length), "ordered actual decision address and deadline")
            equal(raw["nav_pre"][index], nav[agent], "pre-navigation continuity")
            equal(raw["held_before"][index], held[agent], "held category continuity")
            observation = raw["observations"][tick, agent]
            key = observation[:103].tobytes() + bytes([int(nav[agent])])
            hit = key in caches[agent]
            equal(raw["memo_hit"][index], hit, "episode-private exact cache")
            deployed["requests"] += 1
            deployed["hits" if hit else "misses"] += 1
            state["ordinary_queries"] += 1
            base = _source_c(controllers[agent], observation, tick, nav[agent])
            equal(raw["c_index"][index], base["action_index"], "original C category")
            equal(raw["policy_scores"][index], base["scores"], "full original scores")
            equal(raw["policy_served"][index], base["served"], "full original service scores")
            for name in ("features", "fallback", "n_current", "n_peers"):
                equal(raw[name][index], base[name], "original replay: " + name)
            if not hit:
                caches[agent].add(key)
                deployed["cache_entries"] += 1
                deployed["cache_key_bytes"] += len(key)
                for name, value in dict(trajectories=27, model_ticks=108, objective_reductions=108,
                                       candidate_links=108 * base["n_current"],
                                       setup_links=(1 + base["n_peers"]) * base["n_current"]).items():
                    deployed[name] += value
                deployed["cache_array_bytes"] += sum(base[name].nbytes for name in ("command", "scores", "served", "features"))
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
            deployed["sampled_draws"] += int(arm == "Q10")
            equal(raw["innovation"][index], u, "actual-tick innovation")
            equal(raw["action_index"][index], choice, "ordered CDF category")
            positive = p > 0
            entropy = float(-np.sum(p[positive] * np.log(p[positive])))
            for name, value in dict(entropy=entropy, behavior_entropy=entropy,
                                    chosen_probability=p[choice], logp=np.log(p[choice])).items():
                equal(raw[name][index], value, name)
            previous = raw["positions"][tick, agent].copy()
            replacement, changed = previous.copy(), False
            if held[agent] >= 0:
                for _ in range(length):
                    previous = np.clip(previous + 30. * commands[agent].astype(np.float64), LOW, HIGH)
                    replacement = np.clip(replacement + 30. * inherited.COMMANDS[choice].astype(np.float64), LOW, HIGH)
                    changed |= not np.array_equal(previous, replacement)
                    state["clipped_hold_comparison_ticks"] += 1
            equal(raw["category_changed"][index], held[agent] >= 0 and held[agent] != choice, "held category change")
            equal(raw["physical_hold_changed"][index], changed, "clipped hold until own next deadline")
            commands[agent], held[agent] = inherited.COMMANDS[choice], choice
            index += 1
        equal(raw["commands"][tick], commands, "actual command and private-deadline hold")
    equal(index, d, "no extra decision records")
    if deployed != row["policy_counts"]:
        raise AssertionError("deployed cache/model accounting")
    for name, value in episode_metrics(raw).items():
        equal(row[name], value, "episode reduction: " + name)
    for key, value in row.items():
        if key.endswith("_seconds") and (not np.isfinite(value) or value < 0):
            raise AssertionError("invalid timing")
    equal(row["initial_state_sha256"], array_digest(raw["positions"][0], raw["initial_users"],
                                                   raw["initial_sinr"], raw["initial_connections"]), "initial geometry identity")
    signatures = [array_digest(raw["decision_ticks"][raw["decision_agents"] == agent],
                               raw["innovation"][raw["decision_agents"] == agent]) for agent in range(5)]
    return dict(source_counts=sum_counts(controller.counters for controller in controllers),
                ordinary_queries=state["ordinary_queries"], indexed_draws=state["indexed_draws"],
                clipped_hold_comparison_ticks=state["clipped_hold_comparison_ticks"],
                native_team_ticks_verified=h, native_agent_motion_ticks_verified=h * 5,
                clock_draw_signatures=signatures, new_native_steps=0, actor_rows=0, analytic_helper_queries=0)


def read_result(out, repo, *, fixture=False):
    state = dict(completed_episodes=0, completed_replay=[], inflight={})
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    try:
        return _read_result(out, repo, fixture=fixture, state=state, start_wall=start_wall, start_cpu=start_cpu)
    except BaseException as error:
        write_json(Path(out) / "reading.json", dict(status="FAILED", error=repr(error), traceback=traceback.format_exc(),
                   reader_cpu_seconds=time.process_time() - start_cpu, reader_wall_seconds=time.perf_counter() - start_wall,
                   actual_work=state, new_native_steps=0))
        raise


def _read_result(out, repo, *, fixture, state, start_wall, start_cpu):
    out, repo = Path(out), Path(repo)
    config = json.loads((out / "config.json").read_text())
    summary = json.loads((out / "summary.json").read_text())
    protocol = Protocol.from_dict(config["protocol"])
    if ((fixture and (config["scientific_invocation"] or set(protocol.worlds) & set(FROZEN.worlds)))
            or (not fixture and (protocol != FROZEN or not config["scientific_invocation"]))):
        raise ValueError("fixture/production protocol mismatch")
    if (config["object"] != OBJECT or summary["object"] != OBJECT or summary["state"] != "COMPLETE"
            or summary["launch_sha"] != config["launch_sha"]):
        raise AssertionError("incomplete/wrong study identity")
    if not fixture and (config["runtime"]["torch_threads"] != 1 or config["runtime"]["torch_interop_threads"] != 1
                        or not config["runtime"]["deterministic_algorithms"] or torch.get_num_threads() != 1
                        or torch.get_num_interop_threads() != 1 or not torch.are_deterministic_algorithms_enabled()):
        raise AssertionError("production deterministic one-thread contract")
    if source_identities(repo) != config["source_identities"]:
        raise AssertionError("source identity changed")
    equal(config["expected_exact"], protocol.expected(), "configured exposure")
    equal(config["worker_uncached_ceiling"], protocol.model_ceiling(), "worker model ceiling")
    equal(config["reader_full_ceiling"], protocol.model_ceiling(), "reader model ceiling")
    rows, work = summary["episodes"], state["completed_replay"]
    expected_order = []
    for wi, world in enumerate(protocol.worlds):
        block = wi // 2
        r = np.random.default_rng(np.random.SeedSequence([protocol.phase_root, world])).permutation([0, 0, 1, 2, 3])
        equal(config["phase_offsets"][str(world)], r, "configured phase roles")
        for j in range(4):
            for k in range(3):
                arm, tape = (("C", -1), ("Q10", 0), ("Q10", 1))[(block + j + k) % 3]
                pair = ("SYNC", "DISPERSED") if (wi + j + k) % 2 == 0 else ("DISPERSED", "SYNC")
                expected_order.extend(dict(arm=arm, schedule=schedule, world=world, q=(block + j) % 4, tape=tape)
                                      for schedule in pair)
    equal(config["processing_order"], expected_order, "declared balanced processing order")
    equal([{key: row[key] for key in ("arm", "schedule", "world", "q", "tape")} for row in rows],
          expected_order, "actual balanced processing order")
    expected_raw, clock_draws = set(), {}
    for row in rows:
        path = (out / row["raw"]["path"]).resolve()
        if not path.is_relative_to((out / "raw").resolve()):
            raise AssertionError("raw identity escapes output")
        expected_raw.add(path.name)
        identity = file_identity(path)
        if any(identity[key] != row["raw"][key] for key in ("bytes", "sha256")):
            raise AssertionError("raw file identity mismatch")
        with np.load(path, allow_pickle=False) as archive:
            raw = {key: archive[key] for key in archive.files}
        state["inflight"] = {}
        checked = check_episode(raw, row, protocol, progress=state["inflight"])
        work.append(checked)
        for agent, signature in enumerate(checked["clock_draw_signatures"]):
            group = (row["world"], row["arm"], row["tape"], agent, row["schedule"])
            clock_draws.setdefault(group, []).append(signature)
        state["completed_episodes"] += 1
        state["inflight"] = {}
    if {path.name for path in (out / "raw").iterdir()} != expected_raw or len(expected_raw) != len(rows):
        raise AssertionError("undeclared, duplicated or partial raw output")
    for world in protocol.worlds:
        if len({row["initial_state_sha256"] for row in rows if row["world"] == world}) != 1:
            raise AssertionError("paired initial state differs")
        for arm, tape in (("C", -1), ("Q10", 0), ("Q10", 1)):
            for agent in range(5):
                sync = clock_draws[world, arm, tape, agent, "SYNC"]
                dispersed = clock_draws[world, arm, tape, agent, "DISPERSED"]
                if len(sync) != 4 or len(dispersed) != 4 or sorted(sync) != sorted(dispersed):
                    raise AssertionError("individual full-clock/draw multisets do not match")
    protocol.check_counts(summary["counts"])
    equal(summary["counts"]["ordinary_queries"], sum(item["ordinary_queries"] for item in work), "actual C exposure")
    equal(summary["counts"]["sampled_draws"], sum(item["indexed_draws"] for item in work), "actual Q10 draws")
    counts = summary["counts"]
    equal(summary["native_dense_power_slots"], 275 * (counts["native_steps"] + counts["explicit_resets"]
                                                      + counts["constructor_resets"]), "native dense slots")
    paired = comparisons(rows, protocol)
    if summary["paired"] != paired:
        raise AssertionError("paired-world reductions")
    for arm, schedule in CELLS:
        if summary["policy_counts"][cell_name(arm, schedule)] != sum_counts(
                row["policy_counts"] for row in rows if row["arm"] == arm and row["schedule"] == schedule):
            raise AssertionError("aggregate policy cost")
    total_source = sum_counts(item["source_counts"] for item in work)
    for name, ceiling in protocol.model_ceiling().items():
        value = total_source[name]
        if value > ceiling or (name in ("trajectories", "model_ticks", "objective_reductions") and value != ceiling):
            raise AssertionError("full original C reader exposure")
    replay = dict(source_counts=total_source,
                  **sum_counts({key: value for key, value in item.items()
                                if key not in ("source_counts", "clock_draw_signatures")} for item in work))
    result = dict(status="VERIFIED", object=OBJECT, launch_sha=config["launch_sha"], scientific_invocation=not fixture,
                  protocol=protocol.to_dict(), paired=paired, episodes=len(rows), counts=summary["counts"],
                  policy_counts=summary["policy_counts"], replay_counts=replay,
                  matching=dict(worlds=len(protocol.worlds), program_tapes=3, agents=5, offsets=4,
                                full_clock_draw_multisets_checked=len(protocol.worlds) * 3 * 5),
                  reader_cpu_seconds=time.process_time() - start_cpu, reader_wall_seconds=time.perf_counter() - start_wall,
                  process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  peak_scope="same worker/reader process high-water mark, not a sum",
                  complete_worker_cpu_seconds=summary["worker_cpu_seconds"],
                  complete_worker_wall_seconds=summary["worker_wall_seconds"],
                  scope="Every saved C query including deployed hits reconstructed from the original source; "
                        "private cache/nav/RNG/phase/deadline/holds, whole-clock/draw multiset matching, "
                        "clipped physical holds, source/raw identities, saved native telemetry eligibility/capacity/"
                        "uniqueness/local-count provenance and service/quality/reward reductions, pairing/order "
                        "and complete summaries. No new environment/actor/helper queries; native radio not resimulated.")
    write_json(out / "reading.json", result)
    return result

"""One bounded complete reading: saved native arrays, fixed final actors,80 C/helper rows."""
import hashlib
import json
from pathlib import Path
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest, state_copy, movement
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from .assets import load_initial_assets
from .audit import check_episode
from .contract import CALIBRATION_SOURCE, COUNTS, FINAL_COUNTS, FITS, FROZEN, OBJECT, array_digest, source_identities
from .controllers import MemoC, analyze
from .model import make_inherited
from .reading import METRICS, comparisons, cost_totals, validate_counts


def _artifact(out, record):
    path = (out / record["path"]).resolve()
    path.relative_to(out)
    found = file_identity(path)
    if any(found[k] != record[k] for k in ("sha256", "bytes")):
        raise AssertionError("artifact identity mismatch: " + record["path"])
    return path


def _planned_rows(protocol):
    rows = [("fixture", None, "C", n, protocol.fixture_world, None, None) for n in COUNTS]
    for lineage in (0, 1):
        for arm in FITS:
            for phase in range(3):
                rows += [("acquisition", lineage, arm, protocol.acquisition_count(arm, j), world, phase, None)
                         for j, world in enumerate(protocol.phase_worlds(lineage, phase))]
    for n in FINAL_COUNTS:
        for world in protocol.evaluation_worlds:
            rows.append(("evaluation", None, "C", n, world, None, None))
            rows += [("evaluation", None, "Q", n, world, None, t) for t in (0, 1)]
            for lineage in (0, 1):
                rows += [("evaluation", lineage, arm, n, world, None, t)
                         for arm in ("P", "F", "M", *(("Bstar",) if lineage == 0 else ())) for t in (0, 1)]
    return rows


def _optimizer(saved, actor, steps):
    optimizer = saved["optimizer"]
    groups = optimizer["param_groups"]
    if len(groups) != 1:
        raise AssertionError("one fixed Adam group required")
    group = groups[0]
    options = dict(lr=3e-4, betas=(.9, .999), eps=1e-8, weight_decay=0,
                   amsgrad=False, foreach=False, fused=False, maximize=False)
    if any(group[k] != value for k, value in options.items()):
        raise AssertionError("saved Adam law differs")
    parameters, ids = list(actor.parameters()), group["params"]
    if len(ids) != len(parameters) or len(set(ids)) != len(ids) or set(optimizer["state"]) != set(ids):
        raise AssertionError("incomplete Adam parameter ownership")
    for parameter, key in zip(parameters, ids):
        entry = optimizer["state"][key]
        if set(entry) != {"step", "exp_avg", "exp_avg_sq"} or float(entry["step"]) != steps:
            raise AssertionError("Adam step/field identity mismatch")
        for name in ("exp_avg", "exp_avg_sq"):
            tensor = entry[name]
            if tensor.shape != parameter.shape or tensor.dtype != torch.float32 or not torch.isfinite(tensor).all():
                raise AssertionError("invalid saved Adam tensor")
    if saved["optimizer_steps"] != steps or saved["adam_step_values"] != [steps] * len(parameters):
        raise AssertionError("checkpoint optimizer accounting differs")


def _phase_record(record, data, before, after, phase, root, protocol):
    x, y, n = data
    examples, epochs = protocol.expected()["datasets"][phase], protocol.epochs[phase]
    updates = examples // protocol.batch_size
    if (record["phase"] != phase or record["status"] != "COMPLETE" or record["examples"] != examples
            or len(record["epochs"]) != epochs or record["optimizer_steps"] != updates * epochs
            or record["sample_presentations"] != examples * epochs or record["shuffle_root"] != root
            or record["data_sha256"] != array_digest(x, y, n)
            or record["before_sha256"] != state_digest(before)
            or record["after_sha256"] != state_digest(after)
            or record["movement"] != movement(before, after)):
        raise AssertionError("phase identity/data/exposure/movement mismatch")
    if record["label_counts"] != np.bincount(y, minlength=27).tolist():
        raise AssertionError("phase label histogram differs")
    if record["count_counts"] != {str(k): int(np.count_nonzero(n == k)) for k in COUNTS}:
        raise AssertionError("phase fleet row exposure differs")
    if record["unique_feature_rows"] != len(np.unique(x, axis=0)):
        raise AssertionError("unique feature count differs")
    all_order = hashlib.sha256()
    prior = sum(protocol.expected()["phase_updates"][:phase])
    for epoch, row in enumerate(record["epochs"]):
        order = np.random.default_rng(np.random.SeedSequence([root, phase, epoch])).permutation(examples)
        payload = order.astype("<i8", copy=False).tobytes()
        all_order.update(payload)
        if (row["epoch"] != epoch or row["status"] != "COMPLETE" or row["updates"] != updates
                or row["sample_presentations"] != examples or row["stream_rows"] != examples
                or row["shuffle_sha256"] != hashlib.sha256(payload).hexdigest()
                or not np.isfinite(row["stream_cross_entropy"]) or row["stream_cross_entropy"] < 0
                or not 0 <= row["stream_accuracy"] <= 1
                or row["zero_gradient_updates"] + row["nonzero_gradient_updates"] != updates
                or row["count_zero_gradient_updates"] + row["count_nonzero_gradient_updates"] != updates
                or row["adam_step_values"] != [prior + (epoch + 1) * updates] * 7):
            raise AssertionError("saved epoch exposure/order/gradient trace differs")
    confusion = np.asarray(record["epochs"][-1]["stream_confusion"], dtype=np.int64)
    if (confusion.shape != (27, 27) or np.any(confusion < 0)
            or not np.array_equal(confusion.sum(axis=1), np.bincount(y, minlength=27))
            or float(np.trace(confusion) / examples) != record["epochs"][-1]["stream_accuracy"]
            or record["epochs"][-1]["state_sha256"] != state_digest(after)
            or record["all_shuffle_sha256"] != all_order.hexdigest()):
        raise AssertionError("terminal phase stream confusion/state differs")


def _load_learning(out, batch, original_states, originals, protocol):
    datasets, checkpoints, states = {}, {}, {}
    for record in batch["datasets"]:
        key = record["lineage"], record["arm"], record["phase"]
        if key in datasets:
            raise AssertionError("duplicate dataset")
        with np.load(_artifact(out, record["artifact"]), allow_pickle=False) as saved:
            if set(saved.files) != {"features", "labels", "fleet_counts"}:
                raise AssertionError("dataset columns changed")
            data = tuple(saved[name] for name in ("features", "labels", "fleet_counts"))
        x, y, n = data
        expected = protocol.expected()["phase_labels"][key[2]]
        if (x.shape != (expected, 114) or x.dtype != np.float32 or y.shape != (expected,)
                or y.dtype != np.int64 or n.shape != y.shape or n.dtype != np.int64
                or not np.isfinite(x).all() or np.any((y < 0) | (y >= 27))
                or array_digest(*data) != record["data_sha256"] or record["rows"] != expected):
            raise AssertionError("dataset shape/identity differs")
        if key[1] == "F" and not np.all(n == 5) or key[1] == "M" and (
                np.count_nonzero(n == 3) * 10 != expected * 3 or np.count_nonzero(n == 7) * 10 != expected * 7):
            raise AssertionError("acquisition count-row distribution differs")
        datasets[key] = data
    expected_keys = {(l, a, p) for l in (0, 1) for a in FITS for p in range(3)}
    if set(datasets) != expected_keys:
        raise AssertionError("incomplete fixed learning data")
    for record in batch["checkpoints"]:
        key = record["lineage"], record["arm"], record["phase"]
        if key in checkpoints or key not in expected_keys:
            raise AssertionError("unexpected phase checkpoint")
        saved = torch.load(_artifact(out, record), map_location="cpu", weights_only=True)
        if (saved["schema"] != "uav_fleet_adaptation.b06.full_actor.v1" or saved["launch_sha"] != batch["launch_sha"]
                or saved["protocol"] != protocol.to_dict() or saved["endpoint"] != key[1]
                or saved["lineage"] != key[0] or saved["phase"] != key[2]
                or saved["original_state_sha256"] != batch["initial_assets"][key[0]]["state_sha256"]
                or saved["parameters"] != 34843 or saved["architecture"] != [114, 128, 128, 27]
                or saved["activation"] != "relu" or saved["dtype"] != "float32"
                or saved["count_domain"] != [3, 4, 5, 6, 7]
                or saved["count_branch"] != dict(shape=[128], feature="(N-5)/2", placement="before first ReLU")):
            raise AssertionError("checkpoint parent/interface identity differs")
        actor = make_inherited(original_states[key[0]], protocol.actor_constructor_seeds[key[0]])
        actor.load_state_dict(saved["state_dict"], strict=True)
        if any(v.dtype != torch.float32 or not torch.isfinite(v).all() for v in actor.state_dict().values()):
            raise AssertionError("invalid checkpoint parameters")
        actual_sha = state_digest(actor.state_dict())
        if actual_sha != saved["state_sha256"] or actual_sha != record["state_sha256"]:
            raise AssertionError("checkpoint tensor digest differs")
        steps = sum(protocol.expected()["phase_updates"][:key[2] + 1])
        _optimizer(saved, actor, steps)
        if key[1] == "F":
            if torch.count_nonzero(actor.count_weight) or any(
                    torch.count_nonzero(saved["optimizer"]["state"][saved["optimizer"]["param_groups"][0]["params"][0]][name])
                    for name in ("exp_avg", "exp_avg_sq")):
                raise AssertionError("F count branch or its Adam moments moved")
        actor.eval().requires_grad_(False)
        checkpoints[key], states[key] = actor, state_copy(actor)
    if set(checkpoints) != expected_keys:
        raise AssertionError("missing phase checkpoint")
    if {(r["lineage"], r["arm"]) for r in batch["fits"]} != {(l, a) for l in (0, 1) for a in FITS} or len(batch["fits"]) != 4:
        raise AssertionError("four fit records required")
    for fit in batch["fits"]:
        lineage, arm = fit["lineage"], fit["arm"]
        initial = state_copy(originals[lineage])
        final = states[lineage, arm, 2]
        if (fit["generalized_initial_sha256"] != state_digest(initial)
                or fit["final_state_sha256"] != state_digest(final)
                or fit["original_state_sha256"] != batch["initial_assets"][lineage]["state_sha256"]
                or fit["movement"] != movement(initial, final) or len(fit["phases"]) != 3):
            raise AssertionError("fit movement/initial identity differs")
        for phase, record in enumerate(fit["phases"]):
            data = tuple(np.concatenate([datasets[lineage, arm, p][i] for p in range(phase + 1)], axis=0) for i in range(3))
            before = initial if phase == 0 else states[lineage, arm, phase - 1]
            _phase_record(record, data, before, states[lineage, arm, phase], phase,
                          protocol.shuffle_roots[lineage], protocol)
            checkpoint_record = next(r for r in batch["checkpoints"] if (r["lineage"], r["arm"], r["phase"]) == (lineage, arm, phase))
            if checkpoint_record["training_record"] != record:
                raise AssertionError("phase stream/checkpoint record differs")
    return datasets, checkpoints


def _spot(raw, row, j, agent, work):
    n, tick = row["n"], int(raw["decision_ticks"][j])
    obs, nav = raw["observations"][tick, agent].copy(), int(raw["nav_pre"][j, agent])
    controller = MemoC(n)
    work["C_requests"] += 1
    c = controller.query(obs, tick, nav)
    work["C_paths"] += controller.counters["trajectories"]
    work["C_model_ticks"] += controller.counters["model_ticks"]
    work["C_power_links"] += controller.counters["candidate_links"] + controller.counters["setup_links"]
    work["helper_requests"] += 1
    h = analyze(obs, nav, n)
    work["helper_power_links"] += h["counters"]["helper_setup_links"] + h["counters"]["helper_extreme_links"]
    prefix = "expert" if row["kind"] == "acquisition" else "policy"
    label = raw["expert_action_index"][j, agent] if prefix == "expert" else raw["mode_index"][j, agent]
    if (c["action_index"] != label or not np.array_equal(c["scores"], raw[prefix + "_scores"][j, agent])
            or not np.array_equal(c["served"], raw[prefix + "_served"][j, agent])):
        raise AssertionError("bounded C numerical replay mismatch")
    for result in (c, h):
        if (not np.array_equal(result["features"], raw["features"][j, agent])
                or result["fallback"] != raw["fallback"][j, agent]
                or result["next_nav"] != raw["nav_next"][j, agent]
                or result["n_current"] != raw["n_current"][j, agent]
                or result["n_peers"] != raw["n_peers"][j, agent]):
            raise AssertionError("bounded helper/C trace mismatch")
    return dict(id=row["id"], n=n, tick=tick, agent=agent)


def _read(out, repo, work):
    batch = json.loads((out / "summary.json").read_text())
    config = json.loads((out / "config.json").read_text())
    protocol = FROZEN.from_dict(batch["protocol"])
    if (protocol != FROZEN or batch["object"] != OBJECT or batch["state"] != "COMPLETE"
            or batch["scientific_execution"] is not True or batch["expected"] != protocol.expected()):
        raise AssertionError("not the complete selected B06 study")
    for key, value in config.items():
        if value != batch[key]:
            raise AssertionError("config/summary binding changed: " + key)
    if batch["sources"] != source_identities(repo):
        raise AssertionError("read source differs from producer")
    if (batch["inherited_calibration"] != CALIBRATION_SOURCE
            or file_identity(repo / CALIBRATION_SOURCE["reading_path"])["sha256"] != CALIBRATION_SOURCE["reading_sha256"]):
        raise AssertionError("paid Bstar source changed")
    if torch.get_num_threads() != 1 or batch["runtime"]["torch_threads"] != 1:
        raise AssertionError("same one-thread CPU arithmetic required")
    original_states, originals, initial_records = load_initial_assets()
    if initial_records != batch["initial_assets"]:
        raise AssertionError("original parameter bindings changed")
    datasets, actors = _load_learning(out, batch, original_states, originals, protocol)
    actual_keys = [(r["kind"], r["lineage"], r["arm"], r["n"], r["world"], r["phase"], r["tape"]) for r in batch["rows"]]
    if actual_keys != _planned_rows(protocol) or len({r["id"] for r in batch["rows"]}) != len(batch["rows"]):
        raise AssertionError("collection order/panel identity changed")
    offsets = {key: 0 for key in datasets}
    spots_by_n = {n: 0 for n in COUNTS}
    spots, verified_rows, shared_layouts = [], [], {}
    for row in batch["rows"]:
        with np.load(_artifact(out, row["raw"]), allow_pickle=False) as saved:
            raw = dict(saved)
        checked = check_episode(raw, row, protocol)
        for metric, value in checked["metrics"].items():
            if value != row[metric]:
                raise AssertionError("saved/reconstructed episode metric differs: " + metric)
        for name in ("saved_native_steps", "saved_agent_ticks", "decision_rows", "observation_rows",
                     "saved_assignment_matrices", "fallback_geometric_rankings"):
            work[name] += int(checked[name])
        work["fallback_geometric_paths"] += 27 * checked["fallback_geometric_rankings"]
        work["fallback_geometric_ticks"] += 108 * checked["fallback_geometric_rankings"]
        if row["kind"] == "fixture" and checked != batch["fixture_saved_checks"][str(row["n"])]:
            raise AssertionError("worker fixture saved-array reading differs")
        world, n = row["world"], row["n"]
        if world in shared_layouts and shared_layouts[world] != row["shared_layout_sha256"]:
            raise AssertionError("exogenous user/seven-UAV pairing differs")
        shared_layouts[world] = row["shared_layout_sha256"]
        if row["kind"] == "acquisition":
            key = row["lineage"], row["arm"], row["phase"]
            cases = (raw["features"].reshape(-1, 114), raw["expert_action_index"].reshape(-1).astype(np.int64),
                     np.full(raw["features"].shape[0] * n, n, dtype=np.int64))
            if array_digest(*cases) != row["label_data_sha256"]:
                raise AssertionError("raw label binding differs")
            first, stop = offsets[key], offsets[key] + len(cases[1])
            if any(not np.array_equal(data[first:stop], actual) for data, actual in zip(datasets[key], cases)):
                raise AssertionError("saved data is not the ordered acquired rows")
            offsets[key] = stop
            expected_sha = None if row["phase"] == 0 else state_digest(actors[row["lineage"], row["arm"], row["phase"] - 1].state_dict())
            if row["policy_sha256"] != expected_sha:
                raise AssertionError("greedy acquisition actor version changed")
        if row["kind"] == "evaluation" and row["neural"]:
            actor = originals[row["lineage"]] if row["arm"] in ("P", "Bstar") else actors[row["lineage"], row["arm"], 2]
            if state_digest(actor.state_dict()) != row["policy_sha256"]:
                raise AssertionError("final actor endpoint differs")
            count_tensor = torch.tensor([n], dtype=torch.int64)
            with torch.inference_mode():
                for j in range(len(raw["decision_ticks"])):
                    for agent in range(n):
                        x = np.ascontiguousarray(raw["features"][j, agent], dtype=np.float32)
                        work["student_forward_calls"] += 1
                        z = actor(torch.from_numpy(x).reshape(1, 114), count_tensor)[0].numpy()
                        work["student_rows"] += 1
                        if not np.array_equal(z, raw["logits"][j, agent]):
                            raise AssertionError("final one-row actor replay differs")
        eligible_spot = (n in (3, 7) and row["kind"] == "acquisition" and row["lineage"] == 0
                         and row["arm"] == "M" and row["phase"] == 0) or (
                             n in FINAL_COUNTS and row["kind"] == "evaluation" and row["arm"] == "C")
        if eligible_spot and spots_by_n[n] < 16:
            for j in range(len(raw["decision_ticks"])):
                for agent in range(n):
                    if spots_by_n[n] < 16:
                        spots.append(_spot(raw, row, j, agent, work))
                        spots_by_n[n] += 1
        work["raw_files"] += 1
        work["raw_bytes"] += row["raw"]["bytes"]
        verified_rows.append(row)
    if any(offsets[key] != len(datasets[key][1]) for key in offsets) or set(spots_by_n.values()) != {16}:
        raise AssertionError("incomplete data or bounded spot reading")
    expected = protocol.expected()
    for name, target in (("student_rows", expected["reader_student_rows"]), ("student_forward_calls", expected["reader_student_rows"]),
                         ("C_requests", 80), ("helper_requests", 80), ("C_paths", 2160), ("C_model_ticks", 8640),
                         ("saved_native_steps", expected["native_steps"]), ("saved_agent_ticks", expected["native_uav_ticks"])):
        if work[name] != target:
            raise AssertionError("reader actual exposure differs: " + name)
    costs = cost_totals(verified_rows)
    if costs != batch["costs"]:
        raise AssertionError("saved controller costs differ")
    validate_counts(batch["actual"], costs, protocol)
    result_comparisons = comparisons(verified_rows, protocol)
    if result_comparisons != batch["comparisons"]:
        raise AssertionError("fixed clustered reading differs")
    result_keys = ("id", "lineage", "arm", "n", "world", "phase", "tape", *METRICS,
                   "zero_service_ticks", "fallback_decisions", "command_counts", "visible_peer_counts",
                   "more_than_four_peer_decisions", "no_visible_peer_decisions", "mean_visible_peers",
                   "zero_displacement_uav_ticks", "policy_decisions", "policy_cache_hits", "raw")
    return dict(status="VERIFIED", object=OBJECT, launch_sha=batch["launch_sha"], protocol=protocol.to_dict(),
                sources=batch["sources"], initial_assets=batch["initial_assets"],
                inherited_calibration=CALIBRATION_SOURCE, actual=batch["actual"], costs=costs,
                runtime=batch["runtime"], worker_wall_seconds=batch["worker_wall_seconds"],
                worker_cpu_seconds=batch["worker_cpu_seconds"], worker_max_rss_kib=batch["worker_max_rss_kib"],
                worker_timing_scope=batch["timing_scope"], fits=batch["fits"], datasets=batch["datasets"],
                checkpoints=[{k: v for k, v in r.items() if k != "training_record"} for r in batch["checkpoints"]],
                comparisons=result_comparisons, bounded_contexts=spots,
                final_rows=[{k: r[k] for k in result_keys} for r in verified_rows if r["kind"] == "evaluation"],
                fixture_rows=[{k: r[k] for k in result_keys} for r in verified_rows if r["kind"] == "fixture"],
                bulk_summary=file_identity(out / "summary.json"),
                scope="all saved native/observation/feature/choice/label traces, all final actor rows,80 C/helper contexts; no acquisition actor, full teacher, radio-physics or Adam replay; conditional exploratory counts/lineages, no default adoption")


def read_result(out, repo):
    out, repo = Path(out).resolve(), Path(repo).resolve()
    started, cpu_started = time.perf_counter(), time.process_time()
    work = {key: 0 for key in ("raw_files", "raw_bytes", "saved_native_steps", "saved_agent_ticks", "decision_rows",
                               "observation_rows", "saved_assignment_matrices", "fallback_geometric_rankings",
                               "fallback_geometric_paths", "fallback_geometric_ticks",
                               "student_forward_calls", "student_rows", "C_requests", "helper_requests", "C_paths",
                               "C_model_ticks", "C_power_links", "helper_power_links", "native_steps", "optimizer_steps")}
    # Reserve the priced attempt before any replay. A hard interruption leaves
    # this marker, so neither a concurrent call nor a later restart repeats it.
    try:
        with (out / "reading.json").open("x") as stream:
            json.dump(dict(status="INCOMPLETE", object=OBJECT, reader_work=work), stream)
    except FileExistsError as error:
        raise FileExistsError("priced reading already attempted; no automatic repeated reader") from error
    result = dict(status="FAILED", object=OBJECT)
    try:
        result = _read(out, repo, work)
    except BaseException:
        result["failure"] = traceback.format_exc()
        raise
    finally:
        result.update(reader_work=work, reader_wall_seconds=time.perf_counter() - started,
                      reader_cpu_seconds=time.process_time() - cpu_started,
                      process_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                      memory_scope="whole same-process producer plus reader high-water RSS; not incremental reader RSS")
        write_json(out / "reading.json", result)
    return result

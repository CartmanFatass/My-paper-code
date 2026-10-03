"""Selected acquisition, three fixed fits, fresh panel, cold audits and readers."""
from __future__ import annotations

from copy import deepcopy
import json
import multiprocessing
from pathlib import Path
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_transmission.b02.controller import KINDS, empty_counts, trace_counts
from experiments.candidates.uav_fleet_transmission.b02.host import make_env
from experiments.candidates.uav_fleet_transmission.b02.study import COMPONENTS
from experiments.candidates.uav_fleet_transmission.b03.option import branch_id
from experiments.candidates.uav_fleet_transmission.b03.study import SNAPSHOTS
from experiments.candidates.uav_fleet_transmission.host import mask_bits
from experiments.candidates.uav_fleet_transmission.study import metrics

from . import contract as c, evidence as e, features, functional, learning, model
from .planner import BudgetedProgram


def cpu_tensors(feature_menu):
    return {name: torch.from_numpy(np.ascontiguousarray(value))[None] for name, value in feature_menu.items()}


def load_model(out, checkpoint):
    path = e.checked_path(out, checkpoint["weights"])
    payload = torch.load(path, map_location="cpu", weights_only=True)
    state = payload["state"]
    if model.state_digest(state) != checkpoint["state_sha256"]:
        raise ValueError("checkpoint state hash differs")
    module = model.build(checkpoint["init_seed"])
    module.load_state_dict(state, strict=True)
    module.eval()
    return module, state


def worker_scorer(module, collector):
    def score(report, history, mask, bank, plans):
        if collector.queries:
            raise ValueError("a learned arm made more than its one declared online query")
        mark = time.process_time()
        menu = features.build_features(report, history.commands, mask, plans, bank)
        packed = cpu_tensors(menu)
        packed_done = time.process_time()
        with torch.no_grad():
            scores = module(packed)[0].detach().cpu().numpy().copy()
        forward_done = time.process_time()
        if scores.dtype != np.float32 or scores.shape != (8,) or not np.isfinite(scores).all():
            raise ValueError("invalid deployed padded prediction")
        row = {"t": 40, "scores": e.array_binding(scores), "score_bits": scores.tobytes().hex(),
               "features": {key: e.array_binding(value) for key, value in menu.items()},
               "valid_count": len(plans), "state_sha256": model.state_digest(module.state_dict()),
               "feature_pack_cpu_seconds": packed_done - mark,
               "forward_cpu_seconds": forward_done - packed_done}
        collector.queries.append(row)
        e.write_json(collector.root / "query.json", row)
        return scores[:len(plans)].copy()
    return score


def execute_case(out, world, arm, kind, budget, *, module=None):
    """One own native prefix or mission; records completed evidence on failure."""
    out = Path(out)
    steps = 40 if kind == "train" else 500
    if kind not in ("train", "final", "audit") or (kind == "train" and arm != "A2"):
        raise ValueError("undeclared native case")
    if arm not in c.ARMS or ((arm.startswith("L2")) != (module is not None)):
        raise ValueError("arm/scorer binding differs")
    key = f"{kind}/w{world['world_id']}/{arm}"
    budget.case = key
    wall, cpu = time.monotonic(), time.process_time()
    collector = e.Collector(out, key, budget)
    policy = BudgetedProgram("L2" if module is not None else arm, branch_sink=collector.branch_sink,
                             candidate_sink=collector.candidate_sink, reuse=True,
                             segment_sink=collector.segment_sink, menu_sink=collector.menu_sink,
                             scorer=worker_scorer(module, collector) if module is not None else None)
    raw = {name: [] for name in (*SNAPSHOTS, "actions", "mask", "components", "scalar_reward", "terminal")}
    decisions, counts = [], empty_counts()
    calls = {kind: 0 for kind in KINDS}
    timings = {"initialization_cpu_seconds": 0.0, "controller_model_and_record_cpu_seconds": 0.0,
               "native_and_snapshot_cpu_seconds": 0.0, "root_label_cpu_seconds": 0.0}
    result, env, complete = None, None, False
    try:
        mark = time.process_time()
        actual_scene = c.scene(world)
        env = make_env(actual_scene, 500, world["runtime_seed"])
        native = env.env.env
        obs, info = env.reset(seed=world["runtime_seed"])
        state, old_mask = np.asarray(info["state"]), 255
        timings["initialization_cpu_seconds"] += time.process_time() - mark

        def snapshot():
            raw["positions"].append(native.uav_positions.copy())
            raw["observations"].append(np.asarray(obs).copy())
            raw["states"].append(state.copy())
            raw["sinr"].append(native.sinr_matrix.copy())
            raw["connections"].append(native.connections.copy())
            raw["peer_sinr"].append(native.uav_sinr_matrix.copy())
            raw["visible_users"].append([len(native._local_user_entries(i)[0][:20]) for i in range(8)])
            raw["visible_peers"].append([len(native._local_uav_entries(i)[0][:10]) for i in range(8)])

        snapshot()
        for t in range(steps):
            mark = time.process_time()
            command, new_mask, decision = policy.select(t, state if t % 10 == 0 else None, old_mask)
            if t % 10 and new_mask != old_mask:
                raise ValueError("mask changed between lawful report boundaries")
            trace_counts(decision, counts)
            for name in KINDS:
                calls[name] += int(name in decision)
            decisions.append(deepcopy(decision))
            timings["controller_model_and_record_cpu_seconds"] += time.process_time() - mark
            mark = time.process_time()
            if t % 10 == 0:
                native.set_transmitter_mask(mask_bits(new_mask, 8))
            raw["actions"].append(command.copy())
            raw["mask"].append(new_mask)
            obs, reward, terminated, truncated, info = env.step(command)
            state = np.asarray(info["next_state"])
            done = bool(terminated or truncated)
            if done != (t == 499):
                raise ValueError("fixed native H500 termination differs")
            component = info["reward_components"]["reward_info"]
            raw["components"].append([float(component[name]) for name in COMPONENTS])
            raw["scalar_reward"].append(float(reward))
            raw["terminal"].append(done)
            old_mask = new_mask
            snapshot()
            timings["native_and_snapshot_cpu_seconds"] += time.process_time() - mark
            if t % 10 == 0:
                budget.check(progress={"case_native_transitions": t + 1})
        if kind == "train":
            mark = time.process_time()
            policy.prepare_first(state, old_mask)
            timings["root_label_cpu_seconds"] = time.process_time() - mark
        complete = True
    finally:
        if env is not None:
            env.close()
        arrays = {name: np.asarray(values) for name, values in raw.items()}
        arrays["users"] = np.asarray(world["user_positions"], dtype=np.float64)
        native_path, trace_path = collector.root / "native.npz", collector.root / "native.json.gz"
        e.write_arrays(native_path, arrays)
        e.write_gzip(trace_path, decisions)
        catalog = collector.catalog(policy)
        catalog_path = collector.root / "evidence.json.gz"
        e.write_gzip(catalog_path, catalog)
        timings.update(cpu_seconds=time.process_time() - cpu, wall_seconds=time.monotonic() - wall,
                       evidence_callback_cpu_seconds=collector.io_cpu)
        timings["controller_model_cpu_excluding_owned_callback_IO"] = max(
            0.0, timings["controller_model_and_record_cpu_seconds"] + timings["root_label_cpu_seconds"] - collector.io_cpu)
        result = {"kind": kind, "arm": arm, "world_id": world["world_id"], "runtime_seed": world["runtime_seed"],
                  "complete": complete, "steps": len(raw["components"]), "decisions_attempted": len(decisions),
                  "n": 8, "timing": timings,
                  "native_candidate_counts": counts, "calls": calls,
                  "raw": c.binding(native_path, out), "decisions": c.binding(trace_path, out),
                  "evidence_catalog": c.binding(catalog_path, out), "resources": e.resources()}
        if complete:
            if len(decisions) != steps:
                raise ValueError("missing native transitions")
            result.update(metrics=metrics(arrays, 8), costs=e.case_costs(catalog, counts))
        e.write_json(collector.root / "case.json", result)
    budget.check(force_disk=True)
    return result


def bank_features(out, rows):
    feature_rows, labels, entries = [], [], []
    if [row["world_id"] for row in rows] != list(c.TRAIN_IDS):
        raise ValueError("training bank order is incomplete")
    for row in rows:
        catalog = e.read_gzip(e.checked_path(out, row["evidence_catalog"]))
        if len(catalog["menus"]) != 1 or catalog["menus"][0]["start_t"] != 40:
            raise ValueError("training menu not captured exactly once")
        menu = catalog["menus"][0]
        arrays = features.build_features(e.decode_array(menu["report"]), e.decode_array(menu["commands"]),
                                        menu["mask"], menu["plans"], menu["bank"])
        selection = catalog["selections"]["40"]
        expected_ids = [branch_id(plan) for plan in menu["plans"]]
        if list(selection["Q2"]) != expected_ids:
            # Canonical JSON sorts keys, so compare the set then address by menu order.
            if set(selection["Q2"]) != set(expected_ids):
                raise ValueError("acquisition lacks a complete root label")
        q = np.zeros(8, dtype=np.float64)
        q[:len(expected_ids)] = [selection["Q2"][key] for key in expected_ids]
        if not np.isfinite(q).all():
            raise ValueError("nonfinite label")
        feature_rows.append(arrays)
        labels.append(q)
        entries.append({"world_id": row["world_id"], "evidence_catalog": row["evidence_catalog"],
                        "valid_ids": expected_ids, "Q2": q[:len(expected_ids)].tolist(),
                        "feature_bindings": {name: e.array_binding(a) for name, a in arrays.items()}})
    bank = {key: np.stack([r[key] for r in feature_rows]) for key in feature_rows[0]}
    labels = np.stack(labels)
    e.write_arrays(Path(out) / "raw" / "training-bank.npz", {**bank, "Q2": labels})
    e.write_json(Path(out) / "bank.json", {"world_ids": list(c.TRAIN_IDS), "entries": entries,
                                          "array_artifact": c.binding(Path(out) / "raw" / "training-bank.npz", out)})
    return bank, labels, c.binding(Path(out) / "bank.json", out)


def fit_one(out, bank, labels, fit, budget, source_sha, bank_binding):
    out = Path(out)
    root = out / "raw" / "fits" / f"s{fit['fit_id']}"
    root.mkdir(parents=True, exist_ok=False)
    checkpoints = []
    wall, cpu = time.monotonic(), time.process_time()
    path = root / "updates.jsonl.gz"
    raw_stream = path.open("xb")
    gzip_stream = None
    import gzip
    try:
        gzip_stream = gzip.GzipFile(fileobj=raw_stream, mode="wb", mtime=0)

        def checkpoint(record):
            state, predictions = record["state"], record["predictions"]
            update = record["update"]
            if update not in c.CHECKPOINTS or update != c.CHECKPOINTS[len(checkpoints)]:
                raise ValueError("checkpoint schedule differs")
            weight_path = root / f"update-{update}.pt"
            with weight_path.open("xb") as target:
                torch.save({"state": state}, target)
            prediction_path = root / f"predictions-{update}.npy"
            with prediction_path.open("xb") as target:
                np.save(target, predictions, allow_pickle=False)
            metadata = {key: value for key, value in record.items() if key not in ("state", "predictions", "valid")}
            metadata["valid"] = record["valid"].tolist()
            saved = {**metadata, "fit_index": fit["fit_id"], "init_seed": fit["init_seed"],
                     "permutation_seed": fit["permutation_seed"], "source_sha": source_sha,
                     "bank": bank_binding, "state_sha256": model.state_digest(state),
                     "weights": c.binding(weight_path, out), "predictions": c.binding(prediction_path, out)}
            checkpoints.append(saved)
            e.write_json(root / f"checkpoint-{update}.json", saved)
            budget.check(progress={"fit": fit["fit_id"], "updates": update})

        def update(record):
            gzip_stream.write(c.encoded(record) + b"\n")
            gzip_stream.flush()
            budget.check(progress={"fit": fit["fit_id"], "updates": record["update"]})

        result = learning.fit(bank, labels, c.TRAIN_IDS, init_seed=fit["init_seed"],
                              permutation_seed=fit["permutation_seed"], on_checkpoint=checkpoint, on_update=update)
    finally:
        if gzip_stream is not None:
            gzip_stream.close()
        raw_stream.close()
    if [row["update"] for row in checkpoints] != list(c.CHECKPOINTS):
        raise ValueError("missing fixed checkpoint")
    total_cpu = time.process_time() - cpu
    research_cpu = result["metadata"]["checkpoint_work_cpu_seconds"] + result["metadata"]["update_callback_cpu_seconds"]
    if research_cpu < 0 or research_cpu > total_cpu:
        raise ValueError("fit research-observation accounting overlaps/exceeds complete fit CPU")
    row = {**fit, "checkpoints": checkpoints, "final": checkpoints[-1], "metadata": result["metadata"],
           "updates": c.binding(path, out), "cpu_seconds": total_cpu,
           "intrinsic_cpu_seconds": total_cpu - research_cpu, "research_observation_cpu_seconds": research_cpu,
           "wall_seconds": time.monotonic() - wall}
    e.write_json(root / "fit.json", row)
    return row


def audit_child(out, world, arm, checkpoint, source_root, wall_started, prior_cpu):
    """One predeclared cold process belonging to the admitted parent study."""
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    budget = e.Budget(out, source_root, wall_started=wall_started, cpu_offset=prior_cpu,
                      progress_name=f"audit-progress-{arm}.json")
    budget.stage = "cold_audit"
    root = Path(out) / "raw" / "audit" / f"w{world['world_id']}" / arm
    try:
        load_started = time.process_time()
        module = load_model(out, checkpoint)[0] if checkpoint is not None else None
        load_cpu = time.process_time() - load_started
        row = execute_case(out, world, arm, "audit", budget, module=module)
        e.write_json(root / "cold-process.json", {"status": "complete", "case": row,
                                                "model_restore_cpu_seconds": load_cpu,
                                                "resources": e.resources()})
    except BaseException as exc:
        root.mkdir(parents=True, exist_ok=True)
        e.write_json(root / "cold-process.json", {"status": "failed", "error": f"{type(exc).__name__}: {exc}",
                                                "traceback": traceback.format_exc(), "resources": e.resources()})
        raise


def run_study(out, launch_sha, admission, input_path, input_sha, wall_started):
    from . import reader
    out = Path(out)
    if any((out / name).exists() for name in ("config.json", "summary.json", "raw", "reading.json")):
        raise FileExistsError("existing attempt; no implicit replay or resume")
    inputs = c.validate_input(input_path, input_sha)
    worlds = c.load_world_input()
    indexed_worlds = {world["world_id"]: world for world in worlds["worlds"]}
    budget = e.Budget(out, c.REPO, wall_started=wall_started)
    config = {"scope": c.fixed_scope(), "inputs": inputs, "input_sha256": input_sha, "launch_sha": launch_sha,
              "admission_command_sha256": admission["command_sha256"], "runtime": c.runtime()}
    e.write_json(out / "config.json", config)
    summary = {"status": "running", "stage": "acquisition", "launch_sha": launch_sha,
               "config_artifact": c.binding(out / "config.json", out), "acquisition": [], "fits": [],
               "final": [], "audits": [], "case_readings": [], "functional_readings": [],
               "preparation_cpu": {}}
    e.write_json(out / "summary.json", summary)

    def persist():
        summary["resources"] = e.resources()
        summary["budget"] = budget.check(force_disk=True)
        e.write_json(out / "summary.json", summary, replace=True)

    try:
        for world_id in c.TRAIN_IDS:
            budget.stage = summary["stage"] = "acquisition"
            row = execute_case(out, indexed_worlds[world_id], "A2", "train", budget)
            summary["acquisition"].append(row)
            persist()
            budget.stage = summary["stage"] = "acquisition_reader"
            summary["case_readings"].append(reader.verify_case(out, row, indexed_worlds[world_id], budget))
            persist()
        mark = time.process_time()
        bank, labels, bank_binding = bank_features(out, summary["acquisition"])
        summary["preparation_cpu"]["bank_packing"] = time.process_time() - mark
        summary["bank"] = bank_binding
        for fit in worlds["fits"]:
            budget.stage = summary["stage"] = "fit"
            row = fit_one(out, bank, labels, fit, budget, launch_sha, bank_binding)
            summary["fits"].append(row)
            persist()
            budget.stage = summary["stage"] = "functional_training_reader"
            summary["functional_readings"].append(reader.verify_fit(out, row, bank, labels, budget,
                                                                   source_sha=launch_sha, bank_binding=bank_binding))
            persist()
        seal = {"launch_sha": launch_sha, "input_sha256": input_sha, "bank": bank_binding,
                "finals": [row["final"] for row in summary["fits"]], "fresh_world_ids": list(c.FINAL_IDS),
                "final_parameter_policy": "all three fixed2048; no outcome-selected endpoint"}
        e.write_json(out / "seal.json", seal)
        summary["seal"] = c.binding(out / "seal.json", out)
        modules, states = {}, {}
        mark = time.process_time()
        for i, fit in enumerate(summary["fits"]):
            modules[f"L2-s{i}"], states[f"L2-s{i}"] = load_model(out, fit["final"])
        summary["preparation_cpu"]["panel_model_restoration"] = time.process_time() - mark
        for i, world_id in enumerate(c.FINAL_IDS):
            for offset in range(len(c.ARMS)):
                arm = c.ARMS[(i + offset) % len(c.ARMS)]
                e.checked_path(out, summary["seal"])
                budget.stage = summary["stage"] = "fresh_panel"
                row = execute_case(out, indexed_worlds[world_id], arm, "final", budget, module=modules.get(arm))
                summary["final"].append(row)
                persist()
                budget.stage = summary["stage"] = "fresh_reader"
                summary["case_readings"].append(reader.verify_case(out, row, indexed_worlds[world_id], budget,
                                                                  state=states.get(arm)))
                persist()
        context = multiprocessing.get_context("spawn")
        for arm in c.ARMS:
            budget.stage = summary["stage"] = "cold_audit"
            checkpoint = summary["fits"][int(arm[-1])]["final"] if arm.startswith("L2") else None
            child = context.Process(target=audit_child,
                args=(str(out), indexed_worlds[c.FINAL_IDS[0]], arm, checkpoint, str(c.REPO), budget.wall_started,
                      budget.elapsed_cpu()), daemon=True)
            child.start()
            try:
                while child.is_alive():
                    child.join(timeout=10)
                    # The child enforces its residual CPU as it works; parent
                    # adds its actual rusage only once the child is reaped.
                    budget.check(force_disk=True)
                if child.exitcode != 0:
                    raise RuntimeError(f"declared cold audit failed: {arm}, exit={child.exitcode}")
            finally:
                if child.is_alive():
                    child.terminate()
                    child.join()
                child.close()
            result_path = out / "raw" / "audit" / f"w{c.FINAL_IDS[0]}" / arm / "cold-process.json"
            cold = json.loads(result_path.read_text())
            if cold["status"] != "complete":
                raise ValueError("cold process lacks complete evidence")
            row = cold["case"]
            row["cold_process"] = c.binding(result_path, out)
            row["cold_process_resources"] = cold["resources"]
            row["model_restore_cpu_seconds"] = cold["model_restore_cpu_seconds"]
            summary["audits"].append(row)
            persist()
            budget.stage = summary["stage"] = "audit_reader"
            summary["case_readings"].append(reader.verify_case(out, row, indexed_worlds[c.FINAL_IDS[0]], budget,
                                                              state=states.get(arm)))
            reader.verify_cold_identity(out, row, next(r for r in summary["final"]
                                                      if r["world_id"] == c.FINAL_IDS[0] and r["arm"] == arm))
            persist()
        if c.validate_input(input_path, input_sha) != inputs:
            raise ValueError("input/source mutation during the study")
        budget.stage = summary["stage"] = "complete_reading"
        mark = time.process_time()
        reading = reader.complete_reading(out, summary, budget)
        reading["cost_accounts"]["final_aggregation_cpu_seconds"] = time.process_time() - mark
        reading["cost_accounts"]["result_process_resources_after_aggregation"] = e.resources()
        e.write_json(out / "reading.json", reading)
        summary["reading"] = c.binding(out / "reading.json", out)
        summary["status"], summary["stage"] = "complete", "complete"
        persist()
        return summary
    except BaseException as exc:
        summary["status"] = "failed"
        summary["error"] = f"{type(exc).__name__}: {exc}"
        summary["traceback"] = traceback.format_exc()
        summary["resources"] = e.resources()
        summary["wall_seconds"] = time.monotonic() - budget.wall_started
        e.write_json(out / "summary.json", summary, replace=True)
        raise

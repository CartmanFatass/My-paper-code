"""Complete B06 saved-evidence reading; no optimizer or old-physics replay.

The admitted entry owns runtime setup. Frozen B05 independent kernels are used
only on new paid traces; old teacher physics is certified by its bound reader.
The R trace recurrence below is adapted from the frozen B05 reader solely for
the explicit one/four tape cap. This module never patches the frozen module.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

from . import acquisition as acq, contract as c
from .storage import MISSION_SHAPES, R_SHAPES, R_STATS
from ..b05_request_schedule import reader as old
from ..b05_request_schedule.reader import (
    FIFO, assignment, candidates, check_actual_native_events, check_timing,
    commanded_motion, compose, contained, distribution, features, future_arrivals,
    geometry, greedy, lawful, load_arrays, marker_gap, motion, packed, physical_state,
    predict_g, public, read_json, report_identity, request_metrics, require, same,
    slots_for, unpack, wire_key, write_json,
)


def typed_hash(value):
    result = hashlib.sha256()
    old.hash_replay_row(result, value)
    return result.hexdigest()


class Audit:
    """B06 ceilings, reserved before a call; no inherited B05 fixed limits."""
    LIMITS = {"native_physical_attempts": 269024, "R_initial_physical_attempts": 3840,
              "R_prefix_physical_attempts": 5201920, "G_attempts": 271488,
              "G_reserved_candidate_ticks": 246912000, "neural_attempted_rows": 73440,
              "scorer_constructor_attempts": 6}

    def __init__(self, meter, source_identity):
        self.meter, self.source_identity, self.counts = meter, source_identity, {}

    def add(self, name, amount=1):
        require(type(amount) is int and amount >= 0, "numeric reader count")
        self.counts[name] = self.counts.get(name, 0) + amount
        self.meter.add("reader_" + name, amount)

    def reserve(self, name, amount=1):
        self.meter.check()
        require(name in self.LIMITS and self.counts.get(name, 0) + amount <= self.LIMITS[name],
                "B06 reader exposure bound: " + name)
        self.meter.reserve("reader_" + name, amount)
        self.counts[name] = self.counts.get(name, 0) + amount

    def physics(self, row, users, role):
        require(role in ("native", "R_initial", "R_prefix"), "reader physical role")
        self.reserve(role + "_physical_attempts")
        result = physical_state(row["positions"], users)
        self.add(role + "_physical_states")
        self.add(role + "_physical_relations", 321)
        for name in ("connections", "uav_connections", "bs_connections"):
            same(unpack(row[name], result[name].shape), result[name], "new native physical " + name)
        for name in ("routes", "route_lengths"):
            same(row[name], result[name], "new native physical " + name)
        ack = np.any(result["connections"] & (result["route_lengths"] > 0)[:, None], axis=0)
        same(unpack(row["ack"], (50,)), ack, "new native ACK")
        return ack

    def g(self, row, state, role):
        report_identity(row, state, costs=True)
        horizon = min(240, 1200 - state["tick"])
        self.reserve("G_attempts")
        self.reserve("G_reserved_candidate_ticks", 4 * horizon)
        costs, actual_horizon, boundaries = predict_g(state)
        self.add("G_queries")
        self.add("G_candidate_ticks", 4 * actual_horizon)
        self.add("G_candidate_values", 4)
        self.add("G_cluster_recurrences", 16 * actual_horizon)
        self.add("G_kinematic_uav_steps", 24 * actual_horizon)
        self.add("G_future_arrival_cluster_additions", 16 * boundaries)
        self.add("G_" + role + "_queries")
        same(row["costs"], costs, "independent exact corrected G")
        return costs

    def infer(self, scorer, rows):
        self.reserve("neural_attempted_rows", len(rows))
        self.add("deployment_neural_attempts")
        result = scorer.forward(rows, training=False)
        self.add("neural_rows", len(rows))
        self.add("deployment_neural_rows", len(rows))
        self.add("deployment_neural_calls")
        require(result.dtype == np.float32 and result.shape == (len(rows) // 4, 4) and
                np.isfinite(result).all(), "finite fixed-shape deployment residual")
        return result.reshape(4)


class NeuralMeter:
    """Map the six bank/load utilities into ONE aggregate purchased-row bill.

    Phase counters remain diagnostic. reader_neural_attempted_rows/neural_rows
    alone aggregate bank and deployment rows; never add phase rows to them again.
    """
    def __init__(self, audit):
        self.audit, self.meter = audit, audit.meter

    def check(self):
        return self.meter.check()

    def reserve(self, name, amount=1):
        if name.endswith("_forward_attempted_rows"):
            self.audit.reserve("neural_attempted_rows", amount)
        elif name.endswith("_scorer_constructor_attempts"):
            self.audit.reserve("scorer_constructor_attempts", amount)
        self.meter.reserve(name, amount)

    def add(self, name, amount=1):
        self.meter.add(name, amount)
        if name.endswith("_forward_rows"):
            self.audit.add("neural_rows", amount)
            self.audit.add("bank_neural_rows", amount)
        elif name.endswith("_scorer_constructors"):
            self.audit.add("scorer_constructors", amount)


def validate_manifest(root, manifest, summary, config, source_identity, audit):
    require(manifest["schema"] == summary["schema"] == 1 and summary["status"] == "COMPLETE" and
            summary["object"] == c.OBJECT and summary["missions"] == 224 and
            summary["source_identity"] == config["source_identity"] == source_identity and
            summary["launch_sha"] == config["launch_sha"] and config["mode"] == "worker" and
            config["seed"] == c.MASTER_SEED and config["contract"] == c.frozen_contract(), "B06 worker binding")
    records = manifest["records"]
    same([(item["world"], item["label"]) for item in records], c.expected_roster(), "complete rotated B06 roster")
    require(all(item["status"] == "COMPLETE" and item["completed_native_steps"] == 1200 for item in records),
            "complete new missions")
    required = {"config.json", "endpoint-counts.json", "constant.json", "bank.npz", "bank-provenance.json"}
    required.update(item[name] for item in records for name in ("npz", "metadata"))
    for fit in range(3):
        prefix = f"fits/fit{fit}/"
        required.update(prefix + name for name in (f"fit{fit}_initial.pt", f"fit{fit}_final.pt", f"fit{fit}_training.pt",
                                                   "initial-bank.npz", "final-bank.npz", "updates.jsonl", "epochs.json", "fit.json"))
    require(required <= set(manifest["files"]), "required scientific artifacts are byte-bound")
    for relative, expected in manifest["files"].items():
        audit.meter.check()
        path = contained(root, relative)
        actual = acq.file_identity(path)
        require(actual["bytes"] == expected["bytes"] and actual["sha256"] == expected["sha256"], "worker artifact hash " + relative)
        audit.add("file_hashes")
    require(read_json(root / "config.json") == config and
            read_json(root / "endpoint-counts.json") == manifest["endpoint_counts"] == summary["endpoint_counts"],
            "bound config/endpoint mirrors")
    require(manifest["fits"] == summary["fits"] and [record["fit"] for record in manifest["fits"]] == [0, 1, 2],
            "three fixed fit record mirrors")
    expected_totals = dict(constant_fits=1, neural_fits=3, updates=6336, backwards=6336,
                           context_presentations=403200, training_neural_rows=1612800, bank_endpoint_neural_rows=50400)
    for name, expected in expected_totals.items():
        same(summary["acquisition_totals"][name], expected, "whole acquisition total " + name)
    return records


def teacher_mean(trace, selected):
    """Read four ordered action outcomes independently, preserving aliases.

    The branch outcomes are the arithmetic source. Cohort cost copies and the
    selected metadata are identity checks, not inputs to a shared worker mean.
    """
    require(len(selected) == 4, "independent teacher four-cohort roster")
    samples, seen = [], {}
    for tape in range(4):
        require(trace["tape_complete"][tape] == trace["cohort_complete"][tape] == 1,
                "independent teacher complete tape/cohort")
        item = selected[tape]
        require(item["tape"] == tape, "independent teacher numeric tape order")
        key = bytes(trace["cohort_input_sha256"][tape]).hex()
        require(item["input_sha256"] == key, "independent teacher input identity")
        previous = seen.get(key)
        require(int(trace["cohort_reuse"][tape]) == (-1 if previous is None else previous) and
                item["reused_cohort"] == previous, "independent teacher alias identity")
        branches = trace["cohort_branches"][tape]
        same(branches, item["branches"], "independent teacher selected branch identities")
        require(len(set(map(int, branches))) == 4, "independent teacher four distinct actions")
        costs = np.empty(4, dtype=np.float64)
        for action in range(4):
            branch = int(branches[action])
            require(branch in range(16) and trace["branch_complete"][branch] == 1 and
                    int(trace["branch_action"][branch]) == action and
                    int(trace["branch_tape"][branch]) == (tape if previous is None else previous),
                    "independent teacher branch action and source tape")
            costs[action] = trace["branch_cost"][branch]
        require(np.isfinite(costs).all(), "independent teacher finite outcomes")
        same(costs, trace["cohort_costs"][tape], "independent teacher cohort outcome copies")
        same(costs, item["costs"], "independent teacher selected outcomes")
        if previous is not None:
            same(branches, trace["cohort_branches"][previous], "independent teacher reused branches")
            same(costs, samples[previous], "independent teacher reused outcomes")
        else:
            seen[key] = tape
        samples.append(costs)
    # Four rows stay in numeric tape order even when several refer to one
    # physical cohort. This matches the fixed source's float64 reduction order.
    return np.asarray(samples, dtype=np.float64).sum(axis=0) / 4.


def verify_teacher_features(bank, teacher_root, audit):
    """Old public features/anchors and labels only: no G or physical call."""
    manifest = read_json(Path(teacher_root) / "manifest.json")
    records = sorted((record for record in manifest["records"] if record["label"] in
                      ("main/R", "audit0/R", "audit1/R", "audit2/R")), key=lambda item: item["world"])
    position = 0
    for record in records:
        audit.meter.check()
        with np.load(contained(teacher_root, record["npz"]), allow_pickle=False) as archive:
            users, rates, pairs, reports = (archive[name] for name in ("users", "rates", "pairs", "reports"))
        metadata = read_json(contained(teacher_root, record["metadata"]))
        for decision, report in enumerate(reports):
            state = public(report, users, rates, pairs, int(record["world"]))
            reconstructed = features(state, report["costs"])
            same(bank.features[position], reconstructed, "independent old public303 feature rows")
            same(bank.raw_g[position], report["costs"], "independent old rawG/anchor")
            trace_record = metadata["rollout_traces"][decision]
            require(trace_record["decision"] == decision, "independent old rollout order")
            with np.load(contained(teacher_root, trace_record["path"]), allow_pickle=False) as archive:
                trace = {name: archive[name] for name in ("tape_complete", "cohort_complete", "cohort_reuse",
                         "cohort_branches", "cohort_costs", "cohort_input_sha256", "branch_complete",
                         "branch_action", "branch_tape", "branch_cost")}
            same(bank.teacher[position], teacher_mean(trace, metadata["decisions"][decision]["cohorts"]),
                 "independent old four-cohort teacher mean including reuse multiplicity")
            audit.add("old_public_feature_contexts")
            audit.add("old_teacher_label_contexts")
            position += 1
    require(position == 2100, "all old public contexts checked without old physics")


def verify_constant(bank, meter, *, solver=None):
    """Independent scalar ordered system and ONE purchased bordered solve."""
    bank.validate()
    count = acq.Counts("constant_verification", meter, None)
    H, z = np.zeros((4, 4), np.float64), np.zeros(4, np.float64)
    count.event("system.attempt", "system_attempts", attempt=True)
    count.event("system.rows.reserve", "system_attempted_action_rows", 8400, attempt=True)
    for context in range(2100):
        count.check()
        raw, target = bank.raw_g[context], bank.teacher[context]
        anchor = min(range(4), key=lambda action: (raw[action], action))
        for action in range(4):
            direction = [float(index == action) - float(index == anchor) for index in range(4)]
            value = (target[action] - target[anchor]) - (raw[action] - raw[anchor])
            for row in range(4):
                z[row] += direction[row] * value
                for column in range(4):
                    H[row, column] += direction[row] * direction[column]
            count.event("system.row.complete", "system_action_rows")
    count.event("system.complete", "systems")
    bordered, rhs = np.zeros((5, 5), np.float64), np.zeros(5, np.float64)
    bordered[:4, :4] = H
    for index in range(4):
        bordered[index, 4] = bordered[4, index] = 1.
        rhs[index] = z[index]
    count.event("solve.attempt", "solve_attempts", attempt=True)
    solution = (np.linalg.solve if solver is None else solver)(bordered, rhs)
    require(solution.dtype == np.float64 and solution.shape == (5,) and np.isfinite(solution).all(),
            "independent finite bordered solution")
    count.event("solve.complete", "solves")
    return {"H": H, "z": z, "b": solution[:4].copy(), "lambda": float(solution[4]),
            "normal_residual": H @ solution[:4] + solution[4] - z,
            "constraint_residual": float(solution[:4].sum()), "counts": count.counts,
            "bank_identity": bank.identity}


def verify_endpoint_arrays(bank, predicted, saved):
    """Independent NumPy arithmetic over paid residuals, not another forward."""
    residual = predicted["residual"]
    q = bank.raw_g / 1200. + residual.astype(np.float64)
    anchor = np.argmin(bank.raw_g, axis=1)
    rows = np.arange(2100)
    errors = (q - q[rows, anchor][:, None]) - (bank.teacher - bank.teacher[rows, anchor][:, None]) / 1200.
    actions = np.lexsort((np.broadcast_to(np.arange(4), q.shape), bank.raw_g, q), axis=1)[:, 0]
    teacher_min = bank.teacher.min(axis=1)
    expected = {"residual": residual, "q": q, "relative_errors": errors,
                "relative_loss": np.mean(errors ** 2, axis=1), "action": actions,
                "teacher_action": np.argmin(bank.teacher, axis=1),
                "regret": bank.teacher[rows, actions] - teacher_min,
                "ties": q == q.min(axis=1)[:, None], "teacher_ties": bank.teacher == teacher_min[:, None],
                "margin": np.diff(np.sort(q, axis=1)[:, :2], axis=1).reshape(-1),
                "teacher_margin": np.diff(np.sort(bank.teacher, axis=1)[:, :2], axis=1).reshape(-1)}
    require(set(saved) == set(expected), "complete saved endpoint evidence roster")
    for name, value in expected.items():
        same(saved[name], value, "exact endpoint evidence " + name)
    return {"relative_loss_mean": float(expected["relative_loss"].mean()),
            "relative_loss_max": float(expected["relative_loss"].max()),
            "teacher_regret_mean": float(expected["regret"].mean()), "teacher_regret_max": float(expected["regret"].max()),
            "limited_action_accuracy": float(np.mean(actions == expected["teacher_action"])),
            "selected_action_counts": np.bincount(actions, minlength=4).tolist(),
            "teacher_tied_contexts": int(np.count_nonzero(expected["teacher_ties"].sum(axis=1) > 1)),
            "student_tied_contexts": int(np.count_nonzero(expected["ties"].sum(axis=1) > 1)),
            "exposed_teacher_distribution_only": True}


def tensor_array(value):
    return value.detach().cpu().numpy() if hasattr(value, "detach") else value


def verify_fit(root, worker_root, record, bank, models, audit):
    """Replay schedule, hashes and saved scalars; ZERO optimizer/gradient replay."""
    fit = record["fit"]
    prefix = worker_root / f"fits/fit{fit}"
    local = read_json(prefix / "fit.json")
    require(all(record[key] == value for key, value in local.items()) and record["status"] == "COMPLETE" and
            record["bank_identity"] == bank.identity and record["source_identity"] == audit.source_identity,
            "complete source-bound fit metadata")
    backend = models[fit, "final"]
    audit.meter.check()
    state = backend.torch.load(prefix / f"fit{fit}_training.pt", map_location="cpu", weights_only=False)
    audit.add("training_state_reads")
    require(state["schema"] == 1 and state["fit"] == fit and state["init_seed"] == c.TORCH_INIT_SEEDS[fit] and
            state["bank_identity"] == bank.identity and state["source_identity"] == audit.source_identity and
            state["launch_sha"] == record["launch_sha"], "final optimizer/RNG lineage")
    expected_counts = dict(scorer_constructor_attempts=1, scorer_constructors=1, update_attempts=2112, updates=2112,
                           forward_attempts=2112, forward_attempted_rows=537600, forward_calls=2112, forward_rows=537600,
                           backward_attempts=2112, backwards=2112, clip_attempts=2112, clips=2112,
                           optimizer_attempts=2112, optimizer_steps=2112)
    require(state["counts"] == record["counts"] == expected_counts, "fit actual attempt/completion purchase")
    optimizer = state["optimizer"]
    require(len(optimizer["param_groups"]) == 1, "one Adam group")
    group = optimizer["param_groups"][0]
    for name, expected in c.frozen_contract()["adam"].items():
        actual = list(group[name]) if name == "betas" else group[name]
        same(actual, expected, "fixed Adam " + name)
    require(not group["capturable"] and not group["differentiable"], "CPU Adam no graph capture")
    weights = backend.payload["parameters"]
    require(len(group["params"]) == len(weights) and set(optimizer["state"]) == set(group["params"]), "all Adam parameter states")
    for identifier, parameter in zip(group["params"], weights.values()):
        values = optimizer["state"][identifier]
        require(set(values) == {"step", "exp_avg", "exp_avg_sq"}, "Adam moment keys")
        for name, value in values.items():
            converted = tensor_array(value)
            require(converted.dtype == np.float32 and np.isfinite(converted).all() and
                    converted.shape == (() if name == "step" else parameter.shape), "finite shaped FP32 Adam state")
            if hasattr(value, "device"):
                require(value.device.type == "cpu", "CPU Adam state")
        same(tensor_array(values["step"]), 2112., "all final Adam step counts")
    initial = models[fit, "initial"].payload["parameters"]
    initial_hash, final_hash = typed_hash(initial), typed_hash(weights)
    require(state["initial_parameter_sha256"] == initial_hash and state["final_parameter_sha256"] == final_hash,
            "initial/final parameter checkpoint mirrors")
    delta = np.concatenate([(tensor_array(weights[name]) - tensor_array(value)).reshape(-1).astype(np.float64)
                            for name, value in initial.items()])
    movement = {"l2": float(np.linalg.norm(delta)), "max": float(np.abs(delta).max()),
                "changed_coordinates": int(np.count_nonzero(delta))}
    require(record["parameter_motion"] == movement, "endpoint motion arithmetic")
    journal = [json.loads(line) for line in (prefix / "updates.jsonl").read_text().splitlines()]
    require(len(journal) == 4224, "2112 attempt and completion records")
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence((109259999, 51, fit))))
    previous_parameters = initial_hash
    previous_optimizer = typed_hash({"state": {}, "param_groups": copy.deepcopy(optimizer["param_groups"])})
    epochs, norms, ordinal, forward_rows = [], [], 0, 0
    for epoch in range(64):
        permutation = rng.permutation(2100)
        weighted = 0.
        for batch, start in enumerate(range(0, 2100, 64)):
            ordinal += 1
            indices = permutation[start:start + 64]
            attempt, complete = journal[2 * (ordinal - 1):2 * ordinal]
            for event in (attempt, complete):
                require(event["fit"] == fit and event["epoch"] == epoch and event["batch"] == batch and
                        event["number"] == ordinal and event["batch_size"] == len(indices), "update schedule coordinates")
                same(event["indices"], indices, "exact PCG64 shuffle indices")
                require(event["parameters_before"] == previous_parameters and event["optimizer_before"] == previous_optimizer,
                        "ordered parameter/optimizer identity chain")
            require(attempt["status"] == "ATTEMPTED" and not attempt["completed"] and
                    complete["status"] == "COMPLETE" and complete["completed"], "successful update publication pair")
            for name in ("loss", "gradient_norm_before", "gradient_norm_after", "cpu_seconds", "wall_seconds"):
                require(type(complete[name]) in (int, float) and np.isfinite(complete[name]) and complete[name] >= 0,
                        "finite update diagnostic " + name)
            forward_rows += 4 * len(indices)
            counter = complete["counts"]
            require(all(counter[name] == (1 if name.startswith("scorer_") else
                         forward_rows if name in ("forward_rows", "forward_attempted_rows") else ordinal)
                        for name in expected_counts), "per-update attempt/completion counters")
            previous_parameters, previous_optimizer = complete["parameters_after"], complete["optimizer_after"]
            require(all(isinstance(value, str) and len(value) == 64 for value in
                        (previous_parameters, previous_optimizer)), "compact state SHA fields")
            weighted += complete["loss"] * len(indices)
            norms.append([complete["gradient_norm_before"], complete["gradient_norm_after"]])
        epochs.append({"epoch": epoch, "context_weighted_online_loss": weighted / 2100., "contexts": 2100,
                       "updates": 33, "fixed_endpoint_evaluation": False})
    require(state["rng"] == rng.bit_generator.state and previous_parameters == final_hash and
            previous_optimizer == typed_hash(optimizer), "terminal shuffle and state chain identities")
    require(read_json(prefix / "epochs.json") == epochs, "online weighted changed-parameter epoch curve")
    module = ast.parse((root / "experiments/candidates/uav_decision_generalization/b06_request_amortization/acquisition.py").read_text())
    clipping = [node for node in ast.walk(module) if isinstance(node, ast.Call) and
                isinstance(node.func, ast.Attribute) and node.func.attr == "clip_grad_norm_"]
    require(len(clipping) == 1 and ast.literal_eval(clipping[0].args[1]) == 10., "bound source global norm cap10")
    audit.add("verified_update_records", 2112)
    return {"fit": fit, "updates": 2112, "context_presentations": 134400, "training_forward_rows": 537600,
            "movement": movement, "epochs": epochs, "optimizer_replayed": False,
            "historical_gradients_reconstructed": False, "gradient_norm_before_max": float(np.max(norms, axis=0)[0]),
            "gradient_norm_after_max": float(np.max(norms, axis=0)[1]),
            "gradient_cap_excess_diagnostic": float(max(0., np.max(norms, axis=0)[1] - 10.))}


# Frozen B05 rollout recurrence, with only the explicit B06 R1/R4 cap adaptation.
def rollout_read(arrays, state, collected, selected, audit, tape_limit):
    """Read committed prefixes/queries, including unused work; never finish one."""
    require(tape_limit in (1, 4), "selected R1/R4 cap")
    require(not arrays["tape_complete"][tape_limit:].any() and not arrays["cohort_complete"][tape_limit:].any() and
            not arrays["rows"][4*tape_limit:].any() and np.all(arrays["branch_tape"] < tape_limit), "no work beyond R tape cap")
    statistics = {name: int(arrays["stats"][i]) for i, name in enumerate(R_STATS)}
    require(all(value >= 0 for value in statistics.values()), "negative R exposure")
    require(statistics["tape_attempts"] <= tape_limit and statistics["cohorts_complete"] <= tape_limit, "R attempt cap")
    interrupted = bool(selected["timing"]["deadline_expired"])
    horizon = min(160, 1200 - state["tick"])
    require(np.all((arrays["rows"] >= 0) & (arrays["rows"] <= horizon + 1)), "committed R prefix bound")
    for name in ("tape_complete", "cohort_complete", "branch_complete"):
        require(np.all((arrays[name] == 0) | (arrays[name] == 1)), "binary R commit markers")
    require(statistics["initial_attempts"] <= 1 and statistics["initial_complete"] <=
            statistics["initial_attempts"], "single public reconstruction")
    rows = arrays["rows"]
    if np.any(rows):
        require(statistics["initial_complete"] == 1, "clones require committed shared reconstruction")
    if statistics["initial_complete"]:
        report_identity(arrays["initial"][0], state)
        audit.physics(arrays["initial"][0], state["users"], "R_initial")
    tape_indices = np.flatnonzero(arrays["tape_complete"])
    same(tape_indices, np.arange(len(tape_indices)), "contiguous committed R tapes")
    tapes, keys = {}, {}
    for index in tape_indices:
        index = int(index)
        audit.meter.check()
        audit.add("R_tape_reconstructions")
        times, tape = future_arrivals(state, index)
        audit.add("R_tape_uniforms", int(tape.size))
        size = int(arrays["tape_lengths"][index])
        require(size == len(times), "R tape endpoint length")
        same(arrays["tape_times"][index, :size], times, "fixed R tape times")
        same(arrays["tape_times"][index, size:], np.full(8 - size, -1), "R tape padding")
        same(arrays["tapes"][index, :size], tape, "separate public-rate R tape")
        same(arrays["tapes"][index, size:], np.zeros((8 - size, 4)), "R tape unused bits")
        tapes[index] = {int(tick): bit for tick, bit in zip(times, tape)}
        keys[index] = wire_key(state, times, tape, audit.source_identity)
    committed_branches = np.flatnonzero(rows)
    same(committed_branches, np.arange(len(committed_branches)), "contiguous committed branch starts")
    if len(committed_branches) > 1:
        require(np.all(arrays["branch_complete"][committed_branches[:-1]] == 1),
                "only the last started candidate may be incomplete")
        require(np.all(np.diff(arrays["branch_tape"][committed_branches]) >= 0),
                "physical candidates follow tape publication order")
    for tape_index in tape_indices:
        ids = np.flatnonzero((rows > 0) & (arrays["branch_tape"] == tape_index))
        rotation = (state["world"] + state["tick"] // 20 + int(tape_index)) % 4
        same(arrays["branch_action"][ids], np.roll(np.arange(4), -rotation)[:len(ids)],
             "fixed rotated candidate prefix order")
        require(len(ids) <= 4, "four physical candidates per unique tape")
        if any(keys[int(previous)] == keys[int(tape_index)] for previous in tape_indices
               if previous < tape_index and arrays["cohort_complete"][previous]):
            require(len(ids) == 0, "duplicate full input must reuse prior physical cohort")
    gaps = {"tapes": marker_gap(len(tape_indices), statistics["tape_draws"], interrupted, "R tape")}
    require(len(tape_indices) <= statistics["tape_attempts"] <= len(tape_indices) + int(interrupted),
            "R tape attempts/commits")
    # Uniforms are a second publication after tape_draws, so at most the final
    # committed tape's exact draw count can be missing on cancellation.
    tape_uniforms = sum(len(tape) * 4 for tape in tapes.values())
    last_tape_uniforms = len(tapes[int(tape_indices[-1])]) * 4 if len(tape_indices) else 0
    missing_uniforms = tape_uniforms - statistics["tape_uniforms"]
    require(missing_uniforms in ((0, last_tape_uniforms) if interrupted else (0,)),
            "R tape uniform counter")
    if gaps["tapes"] or missing_uniforms:
        last = int(tape_indices[-1])
        require(not np.any((rows > 0) & (arrays["branch_tape"] == last)) and
                arrays["cohort_complete"][last] == 0, "tape counter gap must be final publication")
        if gaps["tapes"]:
            require(missing_uniforms == last_tape_uniforms, "draw publication precedes uniform counter")
    complete_g = np.flatnonzero(arrays["g"]["complete"])
    same(complete_g, np.arange(len(complete_g)), "contiguous committed R G queries")
    require(np.all((arrays["g"]["complete"] == 0) | (arrays["g"]["complete"] == 1)), "binary G commits")
    gaps["G"] = marker_gap(len(complete_g), statistics["g_complete"], interrupted, "R G")
    require(len(complete_g) <= statistics["g_attempts"] <= len(complete_g) + int(interrupted), "R G attempts")
    predictions, matched = {}, set()
    for index in complete_g:
        index = int(index)
        query = arrays["g"][index]
        if index == 0:
            report_identity(query, state, costs=True)
            if collected["complete"]:
                same(query["costs"], collected["costs"], "R base-G duplicate cost identity")
                predictions[index] = query["costs"].copy()
                audit.add("G_duplicate_R_base_records")
            else:
                predictions[index] = audit.g(query, state, "R_base_only")
            matched.add(index)
        else:
            query_state = public(query, state["users"], state["rates"], state["pairs"], state["world"])
            predictions[index] = audit.g(query, query_state, "R_internal")
    predicted_ticks = sum(4 * min(240, 1200 - int(arrays["g"][i]["tick"])) for i in complete_g)
    completed_ticks = statistics["g_complete_candidate_ticks"]
    allowed_tick_gap = (4 * min(240, 1200 - int(arrays["g"][complete_g[-1]]["tick"]))) if len(complete_g) else 0
    require(predicted_ticks - completed_ticks in ((0, allowed_tick_gap) if interrupted else (0,)),
            "R committed G candidate-tick counter")
    require(predicted_ticks == completed_ticks or gaps["G"] == 1,
            "G tick publication precedes complete counter")
    require(statistics["g_reserved_candidate_ticks"] >= predicted_ticks, "R reserved G ticks")
    require(np.all(arrays["g_links"][:, 7] == -1), "unused internal G link slot")
    candidates0 = candidates(state)
    frontier_inputs = {}
    branch_readouts = []
    for branch in np.flatnonzero(rows):
        branch = int(branch)
        action, tape_index = int(arrays["branch_action"][branch]), int(arrays["branch_tape"][branch])
        require(action in range(4) and tape_index in tapes, "committed branch action/tape")
        same(arrays["states"][branch, 0], arrays["initial"][0], "clone initial exact copied identity")
        ledger = FIFO(state["counts"], state["progress"])
        require(all(request["arrival_tick"] is None for queue in ledger.queues for request in queue),
                "model reconstruction must not invent ages")
        active, pending = state["slots"].copy(), candidates0[action].copy()
        paid = int(rows[branch]) - 1
        for offset in range(paid):
            tick = state["tick"] + offset
            previous = arrays["states"][branch, offset]
            same(previous["counts"], ledger.counts, "R pre-arrival integer counts")
            same(previous["progress"], ledger.progress, "R pre-arrival head progress")
            if offset and offset % 20 == 0:
                active = pending.copy()
            arrivals = tapes[tape_index].get(tick, np.zeros(4, dtype=bool))
            same(arrays["arrivals"][branch, offset], arrivals, "R branch public future arrivals")
            ledger.arrive(tick, arrivals)
            same(arrays["tick_cost"][branch, offset], ledger.charge(), "R pre-service residence charge")
            if offset and offset % 20 == 0:
                index = int(arrays["g_links"][branch, offset // 20 - 1])
                require(index in predictions, "paid native prefix needs completed continuation G")
                expected = public(previous, state["users"], state["rates"], state["pairs"], state["world"])
                expected.update(tick=tick, counts=ledger.counts,
                                progress=np.asarray(ledger.progress), slots=active)
                report_identity(arrays["g"][index], expected)
                matched.add(index)
                pending = candidates(expected)[int(np.argmin(predictions[index]))].copy()
            successor = arrays["states"][branch, offset + 1]
            _, _, following, _ = commanded_motion(previous["positions"], active, state["users"])
            same(successor["positions"], following, "R faithful copied-vector native motion")
            same(successor["slots"], active, "R delayed active slots")
            same(successor["tick"], tick + 1, "R successor clock")
            ack = audit.physics(successor, state["users"], "R_prefix")
            ledger.service(tick, ack)
            same(successor["counts"], ledger.counts, "R native FIFO counts")
            same(successor["progress"], ledger.progress, "R native FIFO progress")
        complete = bool(arrays["branch_complete"][branch])
        require(not complete or paid == horizon, "complete branch must contain full paid horizon")
        endpoint = state["tick"] + paid
        query_at_frontier = (paid > 0 and paid % 20 == 0 and endpoint < 1200)
        score = None
        if query_at_frontier:
            previous = arrays["states"][branch, paid]
            active = pending.copy()
            arrivals = tapes[tape_index].get(endpoint, np.zeros(4, dtype=bool))
            ledger.arrive(endpoint, arrivals)  # no endpoint residence charge
            expected = public(previous, state["users"], state["rates"], state["pairs"], state["world"])
            expected.update(counts=ledger.counts, progress=np.asarray(ledger.progress), slots=active)
            slot = 8 if paid == horizon else paid // 20 - 1
            index = int(arrays["g_links"][branch, slot])
            if index >= 0:
                require(index in predictions, "frontier G link must be committed")
                report_identity(arrays["g"][index], expected)
                same(arrays["arrivals"][branch, paid], arrivals, "R endpoint arrivals")
                matched.add(index)
                if paid == horizon:
                    score = ledger.area + float(np.min(predictions[index]))
            frontier_inputs[branch] = expected
        elif paid == horizon and endpoint == 1200:
            score = ledger.area + 240 * int(ledger.counts.sum())
        if complete:
            require(score is not None, "complete nonterminal branch needs completed tail")
            same(arrays["branch_cost"][branch], score, "R score excludes endpoint double charge")
        branch_readouts.append({"branch": branch, "action": action, "tape": tape_index,
                                "committed_native_steps": paid, "complete": complete,
                                "cost": float(score) if complete else None})
    # A last G payload can be committed before its branch link is published.
    unmatched = set(predictions) - matched
    require(len(unmatched) <= int(interrupted), "unjoined completed R G queries")
    for index in unmatched:
        require(index == int(complete_g[-1]) and len(committed_branches) > 0 and
                arrays["branch_complete"][committed_branches[-1]] == 0,
                "only final candidate may have an unlinked final G payload")
        query = arrays["g"][index]
        expected = frontier_inputs.get(int(committed_branches[-1]))
        require(expected is not None and
                all(np.array_equal(query[name], expected[name]) for name in
                    ("positions", "counts", "progress", "slots", "tick")) and
                np.array_equal(unpack(query["ack"], (50,)), expected["ack"]),
                "unlinked G must match the final candidate prefix frontier")
    if gaps["G"]:
        if int(complete_g[-1]) == 0:
            require(statistics["initial_attempts"] == 0 and statistics["tape_attempts"] == 0 and
                    not len(committed_branches), "base G counter gap precedes all R model work")
        else:
            require(unmatched == {int(complete_g[-1])}, "G counter gap must precede final link publication")
    native_commits = sum(int(value) - 1 for value in rows if value)
    gaps["native"] = marker_gap(native_commits, statistics["native_complete"], interrupted, "R native")
    require(native_commits <= statistics["native_attempts"] <= native_commits + int(interrupted),
            "R native attempt exposure")
    if gaps["native"]:
        final_branch = int(committed_branches[-1]) if len(committed_branches) else -1
        paid = int(rows[final_branch]) - 1 if final_branch >= 0 else 0
        frontier_slot = 8 if paid == horizon else paid // 20 - 1
        has_later_G = paid > 0 and paid % 20 == 0 and state["tick"] + paid < 1200 and \
            arrays["g_links"][final_branch, frontier_slot] >= 0
        require(len(committed_branches) > 0 and
                arrays["branch_complete"][final_branch] == 0 and not unmatched and not has_later_G,
                "native counter gap must precede final candidate completion or new G work")
    clone_rows = int(np.count_nonzero(rows))
    require(clone_rows <= statistics["clones"] <= clone_rows + int(interrupted) and
            statistics["clones"] <= statistics["clone_attempts"] <= statistics["clones"] + int(interrupted),
            "R clone call/row publication")
    require(np.all(arrays["branch_complete"][rows == 0] == 0), "no complete empty branch")
    cohort_indices = np.flatnonzero(arrays["cohort_complete"])
    same(cohort_indices, np.arange(len(cohort_indices)), "contiguous committed cohorts")
    gaps["cohorts"] = marker_gap(len(cohort_indices), statistics["cohorts_complete"], interrupted, "R cohort")
    require(len(tape_indices) in (len(cohort_indices), len(cohort_indices) + 1) and
            statistics["tape_attempts"] <= len(cohort_indices) + 1,
            "next tape starts only after preceding cohort publication")
    if not interrupted:
        require(len(cohort_indices) == tape_limit and statistics["initial_complete"] == 1,
                "completed R decision contains its exact tape limit")
    if gaps["cohorts"]:
        require(len(tape_indices) == len(cohort_indices) == statistics["tape_attempts"] and
                len(selected["cohorts"]) < len(cohort_indices),
                "cohort counter gap must precede next tape and selected message")
    cohorts, cache, used_branches = [], {}, set()
    for index in cohort_indices:
        index = int(index)
        require(index in tapes, "completed cohort has its committed tape")
        previous = cache.get(keys[index])
        reused = int(arrays["cohort_reuse"][index])
        require(reused == (-1 if previous is None else previous), "exact full-input cohort reuse")
        ids = arrays["cohort_branches"][index]
        if previous is None:
            require(len(set(map(int, ids))) == 4, "four distinct first-action branches")
            for action, branch in enumerate(ids):
                branch = int(branch)
                require(branch in range(16) and arrays["branch_complete"][branch] == 1 and
                        int(arrays["branch_action"][branch]) == action and
                        int(arrays["branch_tape"][branch]) == index, "complete cohort action correspondence")
                same(arrays["cohort_costs"][index, action], arrays["branch_cost"][branch], "cohort costs")
                used_branches.add(branch)
            cache[keys[index]] = index
        else:
            same(ids, arrays["cohort_branches"][previous], "reused exact branch identities")
            same(arrays["cohort_costs"][index], arrays["cohort_costs"][previous], "reused score multiplicity")
        same(arrays["cohort_input_sha256"][index], np.frombuffer(bytes.fromhex(keys[index]), dtype=np.uint8),
             "full source/public/tape reuse hash")
        require(int(arrays["cohort_ready_ns"][index]) >= int(selected["timing"]["start_ns"]), "cohort ready time")
        size = int(arrays["tape_lengths"][index])
        cohorts.append({"tape": index, "times": arrays["tape_times"][index, :size].astype(int).tolist(),
                        "bits": arrays["tapes"][index, :size].astype(int).tolist(),
                        "input_sha256": keys[index], "reused_cohort": None if reused < 0 else reused,
                        "branches": ids.astype(int).tolist(), "costs": arrays["cohort_costs"][index].tolist()})
    committed_reuse = sum(cohort["reused_cohort"] is not None for cohort in cohorts)
    require(committed_reuse <= statistics["cohorts_reused"] <= committed_reuse + int(interrupted),
            "R reuse-hit versus committed publication")
    if state["tick"] >= 940:
        require(len(cache) <= 1, "no-arrival tail has one exact physical cohort")
    chosen = selected["cohorts"]
    require(chosen == cohorts[:len(chosen)], "selected complete cohort prefix")
    messages = check_timing(selected["timing"])
    selected_messages = [message for message in messages if message["type"] == "cohort"]
    require(len(chosen) == len(selected_messages), "eligible cohort messages define selected multiplicity")
    for cohort, message in zip(chosen, selected_messages):
        require(int(arrays["cohort_ready_ns"][cohort["tape"]]) <= int(message["ready_ns"]),
                "committed cohort precedes its actual ready message")
    selected_branches = {branch for cohort in chosen for branch in cohort["branches"]}
    audit.add("R_committed_native_steps", native_commits)
    audit.add("R_complete_cohorts", len(cohorts))
    audit.add("R_selected_cohorts", len(chosen))
    audit.add("R_reused_cohorts", committed_reuse)
    audit.add("R_incomplete_native_attempts", statistics["native_attempts"] - native_commits)
    native_events = {name: int(arrays["native_events"][i]) for i, name in enumerate(c.NATIVE_EVENT_NAMES)}
    require(all(value >= 0 for value in native_events.values()), "negative paid native event exposure")
    require(0 <= statistics["native_attempts"] - native_events["native_step_calls"] <= int(interrupted),
            "R registered step attempt precedes native entry sink")
    require(native_events["native_steps"] >= native_commits and
            native_events["native_steps"] <= native_commits + int(interrupted), "R returned native step exposure")
    return {"statistics": statistics, "native_events": native_events,
            "commit_counter_gaps": gaps, "branches": branch_readouts,
            "committed_cohorts": len(cohorts), "completed_cohort_records": cohorts, "selected_cohorts": len(chosen),
            "reused_cohorts": committed_reuse,
            "completed_unused_branches": [int(i) for i in np.flatnonzero(arrays["branch_complete"])
                                           if int(i) not in selected_branches],
            "deadline_expired": interrupted}


def extended_metrics(ledger, ack, positions, route_lengths, counts, active):
    result = request_metrics(ledger, ack, positions, route_lengths, counts, active)
    completed = [item["completion_tick"] - item["request"]["arrival_tick"] for item in ledger.completions]
    unfinished = [1200 - item["arrival_tick"] for queue in ledger.queues for item in queue]
    T = max(completed) if completed else None
    W = max(result["user_longest_service_gap"])
    result.update(T_completed_max=T, W_max=W, completed_residences=completed,
                  unfinished_age_lower_bounds=unfinished,
                  censored_residence_max_lower_bound=max(completed + unfinished) if completed or unfinished else None,
                  T_missing_no_completions=not bool(completed), empty_workload=not bool(ledger.requests),
                  requests_ledger=ledger.requests, completions_ledger=ledger.completions,
                  unfinished_requests=[list(queue) for queue in ledger.queues],
                  routed_fraction_per_user=(ack.mean(axis=0)).tolist(),
                  never_served_users=np.flatnonzero(~ack.any(axis=0)).astype(int).tolist(),
                  mean_routed_users_per_tick=float(ack.sum(axis=1).mean()))
    for cluster, item in enumerate(result["per_cluster"]):
        item["completed_residences"] = [entry["completion_tick"] - entry["request"]["arrival_tick"]
                                       for entry in ledger.completions if entry["request"]["cluster"] == cluster]
        item["unfinished_age_lower_bounds"] = [1200 - entry["arrival_tick"] for entry in ledger.queues[cluster]]
    return result


def score_and_command(arrays, index, arm, raw_g, expected_features, eligible, audit, models, constant):
    """Read committed late caches too; eligibility alone permits a command."""
    neural, scored = bool(arrays["nn_complete"][index]), bool(arrays["score_complete"][index])
    is_student = arm.startswith("S")
    require(not neural or (is_student and scored and raw_g is not None), "lawful neural cache markers")
    if is_student:
        require(neural == scored, "student score and neural commits agree")
    elif arm == "B":
        require(not neural and not arrays["residual"][index].any(), "B has no neural work")
    else:
        require(not neural and not scored and not arrays["residual"][index].any(), "ordinary score placeholders")
        return int(np.argmin(raw_g)) if eligible else 0
    if scored:
        require(raw_g is not None, "score needs committed canonical G")
        if is_student:
            residual = audit.infer(models[int(arm[-1]), "final"], expected_features)
            same(arrays["residual"][index], residual, "exact four-row final student output")
            total = raw_g / 1200. + residual.astype(np.float64)
        else:
            total = raw_g + constant
            audit.add("B_committed_scores")
        same(arrays["total_q"][index], total, "exact student/B composition order")
        chosen = int(greedy(total, raw_g))
        same(arrays["greedy_action"][index], chosen, "score/rawG/action lex minimum")
        return chosen if eligible else 0
    require(not eligible, "student/B eligible result requires complete score")
    return 0


def first_cohort_identity(trace, check):
    cohorts = check["completed_cohort_records"]
    if not cohorts:
        return None
    ids = cohorts[0]["branches"]
    prefixes = [(trace["states"][branch, :int(trace["rows"][branch])],
                 trace["arrivals"][branch], trace["tick_cost"][branch],
                 trace["g_links"][branch], trace["branch_cost"][branch]) for branch in ids]
    queries = sorted({0} | {int(value) for branch in ids for value in trace["g_links"][branch] if value >= 0})
    return typed_hash((trace["initial"], prefixes, trace["g"][queries], cohorts[0]))


def read_mission(record, worker_root, manifest, audit, models, constant):
    label, world = record["label"], int(record["world"])
    arm = label.split("/")[1]
    require(arm in c.ARMS, "fixed B06 endpoint label")
    arrays = load_arrays(contained(worker_root, record["npz"]), MISSION_SHAPES)
    metadata = read_json(contained(worker_root, record["metadata"]))
    require(metadata["schema"] == 1 and metadata["status"] == "COMPLETE" and metadata["world"] == world and
            metadata["label"] == label and metadata["training"] is False and metadata["initial_audit"] is False and
            metadata["completed_native_steps"] == 1200 and metadata["completed_decisions"] == 60 and
            len(metadata["decisions"]) == 60 and metadata["last_command_unused"], "complete new mission metadata")
    check_actual_native_events(metadata["actual_native_events"])
    cost = metadata["cost"]
    same(cost["inclusive_cpu_seconds"], cost["after"]["phase_cpu_seconds"] - cost["before"]["phase_cpu_seconds"],
         "mission inclusive CPU snapshots")
    require(np.isfinite(cost["inclusive_cpu_seconds"]) and cost["inclusive_cpu_seconds"] >= 0 and
            np.isfinite(cost["inclusive_wall_seconds"]) and cost["inclusive_wall_seconds"] >= 0, "mission time signs")
    audit.meter.check()
    initial_positions, users = geometry(world)
    audit.add("geometry_reconstructions")
    same(arrays["users"], users, "unchanged geometry law")
    same(arrays["states"][0]["positions"], initial_positions, "source-fixed reset positions")
    rates = np.random.Generator(np.random.PCG64(np.random.SeedSequence((109259999, 20, world)))).permutation(
        np.asarray([6, 3, 2, 1], dtype=np.uint8))
    draws = np.random.Generator(np.random.PCG64(np.random.SeedSequence((109259999, 21, world)))).random((48, 4))
    tape = draws < rates.astype(np.float64) / 10.
    same(arrays["rates"], rates, "fixed public rate address")
    same(arrays["arrival_draws"], draws, "private actual tape address")
    same(arrays["arrival_tape"], tape, "actual outcome-only tape")
    audit.add("actual_arrival_tape_reconstructions")
    audit.add("actual_arrival_uniforms", 192)
    active, pairs = assignment(users, rates, initial_positions)
    same(arrays["pairs"], pairs, "immutable assignment pairs")
    same(arrays["initial_slots"], active, "720-permutation initial assignment")
    same(arrays["states"]["tick"], np.arange(1201), "full native clocks")
    require(np.all((arrays["reports"]["complete"] == 0) | (arrays["reports"]["complete"] == 1)), "G binary commit flags")
    ack = np.stack([audit.physics(row, users, "native") for row in arrays["states"]])
    executed, following, _ = motion(arrays["states"]["positions"][:-1], arrays["raw_actions"])
    same(arrays["executed_actions"], executed, "float64 strict norm>1 execution")
    same(arrays["states"]["positions"][1:], following, "exact native motion recurrence")
    audit.add("native_motion_steps", 1200)
    ledger, pending = FIFO(), active.copy()
    expected_macro = np.zeros(60, dtype=np.uint32)
    actual_active = np.empty((1200, 6), dtype=np.uint8)
    pre_counts = np.empty((1200, 4), dtype=np.int64)
    states, rollout_checks, missing = [], [], []
    traces = {int(item["decision"]): item for item in metadata["rollout_traces"]}
    require(len(traces) == len(metadata["rollout_traces"]) == (60 if arm in ("R1", "R4") else 0), "new R trace roster")
    if traces:
        require(set(traces) == set(range(60)), "all new R decisions retained")
    first_public, first_cohort = None, None
    for tick in range(1200):
        if tick % 20 == 0:
            audit.meter.check()
        index, row = tick // 20, arrays["states"][tick]
        same(row["counts"], ledger.counts, "native before-arrival FIFO counts")
        same(row["progress"], ledger.progress, "native before-arrival head progress")
        same(row["slots"], active, "preceding active targets")
        if tick and tick % 20 == 0:
            active = pending.copy()
        arrivals = tape[index] if tick % 20 == 0 and tick <= 940 else np.zeros(4, dtype=bool)
        same(arrays["arrivals"][tick], arrivals, "arrival-before-report chronology")
        ledger.arrive(tick, arrivals)
        charged = ledger.charge()
        same(arrays["tick_cost"][tick], charged, "pre-service FIFO residence")
        expected_macro[index] += charged
        pre_counts[tick], actual_active[tick] = ledger.counts, active
        if tick % 20 == 0:
            state = public(row, users, rates, pairs, world)
            state.update(counts=ledger.counts, progress=np.asarray(ledger.progress), slots=active.copy())
            states.append(state)
            if index == 0:
                first_public = typed_hash(state)
            report = arrays["reports"][index]
            report_identity(report, state)
            raw_g, expected_features = None, None
            if report["complete"]:
                raw_g = audit.g(report, state, "collected")
                expected_features = features(state, raw_g)
                same(arrays["features"][index], expected_features, "independent303 public features")
                same(arrays["g_action"][index], int(np.argmin(raw_g)), "raw float64 G/action ordering")
            else:
                require(not arrays["nn_complete"][index] and not arrays["score_complete"][index], "scores cannot precede G")
                missing.append({"decision": index, "G_cache_missing": True, "score_cache_missing": arm in ("B", "S0", "S1", "S2")})
            decision = metadata["decisions"][index]
            same(decision["score_complete"], bool(arrays["score_complete"][index]), "metadata cached-score mirror")
            eligible = check_timing(decision["timing"])
            if eligible:
                require(raw_g is not None, "eligible command needs committed G")
            selected = score_and_command(arrays, index, arm, raw_g, expected_features, eligible, audit, models, constant)
            if arm in ("R1", "R4"):
                trace = traces[index]
                expected_path = f"raw/rollouts/{arm}/{world}_{index}.npz"
                require(trace["path"] == expected_path and expected_path in manifest["files"], "distinct arm R prefix identity")
                trace_arrays = load_arrays(contained(worker_root, expected_path), R_SHAPES)
                same(trace_arrays["stats"], [trace["stats"][name] for name in R_STATS], "R lower counters mirror")
                check = rollout_read(trace_arrays, state, report, decision, audit, 1 if arm == "R1" else 4)
                check["decision"] = index
                rollout_checks.append(check)
                if index == 0:
                    first_cohort = first_cohort_identity(trace_arrays, check)
                if decision["cohorts"]:
                    score = np.mean(np.stack([cohort["costs"] for cohort in decision["cohorts"]]), axis=0, dtype=np.float64)
                    selected = int(greedy(score, raw_g))
            elif arm in ("B", "S0", "S1", "S2") and raw_g is not None and not arrays["score_complete"][index]:
                missing.append({"decision": index, "G_cache_missing": False, "score_cache_missing": True})
            same(arrays["action"][index], selected, "last eligible result or KEEP")
            choices = candidates(state)
            same(arrays["commands"][index], choices[selected], "reported-position orientation and pending command")
            pending = arrays["commands"][index].copy()
            lawful(pending, pairs)
        direction = slots_for(users)[active] - row["positions"]
        expected_raw = direction / np.maximum(30., np.linalg.norm(direction, axis=-1))[:, None]
        same(arrays["raw_actions"][tick], expected_raw, "lawful active command steering")
        ledger.service(tick, ack[tick + 1])
        successor = arrays["states"][tick + 1]
        same(successor["counts"], ledger.counts, "post-native FIFO")
        same(successor["progress"], ledger.progress, "20-tick completion/reset")
        same(successor["slots"], active, "exact20-tick target delay")
    terminal = 240 * int(ledger.counts.sum())
    expected_macro[-1] += terminal
    same(arrays["macro_cost"], expected_macro, "area plus terminal C")
    require(int(expected_macro.sum()) == metadata["total_cost"] == record["total_cost"] and ledger.area == metadata["area_cost"] and
            terminal == metadata["terminal_charge"] and metadata["requests"] == ledger.requests and
            metadata["completions"] == ledger.completions and metadata["unfinished"] == [list(queue) for queue in ledger.queues],
            "complete request identities, timestamps and cost conservation")
    require(metadata["logical_reset_bytes"] == 404 and metadata["logical_report_bytes"] == 61 * 171 and
            metadata["logical_command_bytes"] == 360 and metadata["logical_training_feedback_bytes"] == 0,
            "fixed logical interface bill")
    metrics = extended_metrics(ledger, ack[1:], arrays["states"]["positions"], arrays["states"]["route_lengths"][1:], pre_counts, actual_active)
    joins = old.intervention_joins(arrays, states, ledger.completions, "L") if arm in ("B", "S0", "S1", "S2") else []
    for index, join in enumerate(joins):
        join["score_argmin_differs_G"] = join.pop("neural_argmin_differs_G")
        decision = join["decision"]
        join["cached_score_complete"] = bool(arrays["score_complete"][decision])
        join["score_publication_eligible"] = bool(check_timing(metadata["decisions"][decision]["timing"]))
        join["G_action"] = int(arrays["g_action"][decision])
        join["score_argmin_action"] = int(arrays["greedy_action"][decision]) if join["cached_score_complete"] else None
        join["actual_command_action"] = int(arrays["action"][decision])
        choices = candidates(states[decision])
        join["actual_command_aliases_G"] = not join["command_differs_G"]
        join["score_command_aliases_G"] = (bool(np.array_equal(choices[join["score_argmin_action"]],
                                                                     choices[join["G_action"]]))
                                            if join["cached_score_complete"] else None)
    timings = [decision["timing"] for decision in metadata["decisions"]]
    metrics.update(schema=1, status="CHECKED", label=label, world=world, arm=arm, cost=cost,
                   native_physical_states=1201, G_collected_complete=int(arrays["reports"]["complete"].sum()),
                   committed_score_decisions=int(arrays["score_complete"].sum()),
                   committed_neural_decisions=int(arrays["nn_complete"].sum()), policy_cache_missingness=missing,
                   deadline_misses=sum(bool(item["deadline_expired"]) for item in timings),
                   decision_wall_seconds=distribution([(item["command_fixed_ns"] - item["start_ns"]) / 1e9 for item in timings]),
                   decision_cpu_seconds=distribution([item["cpu_seconds"] for item in timings]),
                   reap_seconds=distribution([(item["reaped_ns"] - item["command_fixed_ns"]) / 1e9 for item in timings]),
                   rollout_checks=rollout_checks, intervention_joins=joins,
                   first_public_identity=first_public, first_cohort_identity=first_cohort)
    audit.add("missions")
    return metrics


def cost_object(value, label):
    require(set(("cpu_seconds", "wall_seconds", "scope")) <= set(value) and
            all(type(value[name]) in (int, float) and np.isfinite(value[name]) and value[name] >= 0
                for name in ("cpu_seconds", "wall_seconds")), "measured acquisition cost " + label)
    return value


def acquire_checks(root, worker_root, context, audit):
    """Rebind originals, one B verification, six bank endpoints, saved fits."""
    manifest, summary = context["manifest"], context["worker_summary"]
    bank = acq.binding_bank(context["teacher_root"], context["teacher_reader_summary"],
                            meter=audit.meter, phase="bank_reader")
    saved = load_arrays(worker_root / "bank.npz", {"features": ((2100, 4, 303), "float32"),
                        "raw_g": ((2100, 4), "float64"), "teacher": ((2100, 4), "float64"), "keys": ((2100, 2), "int64")})
    for name in ("features", "raw_g", "teacher"):
        same(saved[name], getattr(bank, name), "derived bank bound original " + name)
    same(saved["keys"], np.asarray(bank.keys, dtype=np.int64), "derived bank ordered source keys")
    require(read_json(worker_root / "bank-provenance.json") == bank.provenance and
            manifest["bank"] == summary["bank"] and manifest["bank"]["identity"] == bank.identity,
            "single derived bank provenance/identity")
    for key, relative in (("arrays", "bank.npz"), ("provenance", "bank-provenance.json")):
        require(manifest["bank"][key] == manifest["files"][relative], "bank manifest file identity mirror")
    verify_teacher_features(bank, context["teacher_root"], audit)
    constant = read_json(worker_root / "constant.json")
    require(constant["schema"] == 1 and constant["object"] == c.OBJECT and
            constant["source_identity"] == audit.source_identity and constant["bank_identity"] == bank.identity and
            constant["launch_sha"] == summary["launch_sha"] and
            manifest["constant"] == summary["constant"] == manifest["files"]["constant.json"], "constant provenance")
    rebuilt = verify_constant(bank, audit.meter)
    for name in ("H", "z", "b", "lambda", "normal_residual", "constraint_residual"):
        same(constant["solution"][name], rebuilt[name], "one independently repeated ordered LS " + name)
    require(constant["solution"]["bank_identity"] == bank.identity and
            constant["solution"]["counts"]["solves"] == rebuilt["counts"]["solves"] == 1,
            "one B fit and one B verification, no alternative")
    cost_object(constant["acquisition_cost"], "constant")
    models, endpoint_checks, fit_checks = {}, [], []
    bridge = NeuralMeter(audit)
    for fit in range(3):
        record = manifest["fits"][fit]
        require(record["launch_sha"] == summary["launch_sha"], "fit original launch SHA")
        cost_object(record["acquisition_cost"], f"fit{fit}")
        for stage in ("initial", "final"):
            relative = f"fits/fit{fit}/fit{fit}_{stage}.pt"
            require(record[stage] == manifest["files"][relative], "checkpoint file identity mirror")
            scorer = acq.load_scorer(worker_root / relative, record[stage], fit_index=fit, stage=stage,
                                     source_identity=audit.source_identity, bank_identity=bank.identity,
                                     meter=bridge, phase=f"reader_load_fit{fit}_{stage}")
            require(scorer.payload["launch_sha"] == summary["launch_sha"], "loaded checkpoint original launch SHA")
            models[fit, stage] = scorer
            predicted = acq.evaluate_endpoint(bank, scorer, phase=f"reader_fit{fit}_{stage}_bank", meter=bridge)
            relative = f"fits/fit{fit}/{stage}-bank.npz"
            require(record[stage + "_bank"] == manifest["files"][relative], "bank evaluation identity mirror")
            with np.load(worker_root / relative, allow_pickle=False) as archive:
                stored = {name: archive[name] for name in archive.files}
            checked = verify_endpoint_arrays(bank, predicted, stored)
            require(predicted["counts"] == record[stage + "_forward_counts"] ==
                    {"forward_attempts": 33, "forward_attempted_rows": 8400, "forward_calls": 33, "forward_rows": 8400},
                    "exact64/52 worker and reader bank forward schedule")
            if stage == "initial":
                same(predicted["residual"], np.zeros((2100, 4), dtype=np.float32), "zero-head full bank identity")
                same(stored["action"], np.argmin(bank.raw_g, axis=1), "canonical initial G deployment definition")
            endpoint_checks.append({"fit": fit, "stage": stage, "counts": predicted["counts"], **checked})
        for key, filename in (("training", f"fit{fit}_training.pt"), ("epochs", "epochs.json"), ("update_evidence", "updates.jsonl")):
            require(record[key] == manifest["files"][f"fits/fit{fit}/{filename}"], "fit evidence identity mirror")
        fit_checks.append(verify_fit(root, worker_root, record, bank, models, audit))
    require(audit.counts["bank_neural_rows"] == 50400 and audit.counts["scorer_constructors"] == 6,
            "complete bank verification purchase")
    return models, np.asarray(rebuilt["b"], dtype=np.float64), {
        "bank_identity": bank.identity, "teacher_contexts": 2100, "teacher_action_labels": 8400,
        "old_public_features_checked": 2100, "old_physics_replayed": False, "new_teacher_queries": 0,
        "constant": {"fit_solves": 1, "verification_solves": 1, "solution": constant["solution"],
                     "acquisition_cost": constant["acquisition_cost"]}, "endpoints": endpoint_checks,
        "fits": fit_checks, "optimizer_replayed": False}


METRICS = ("C", "area_cost", "terminal_charge", "T_completed_max", "W_max", "completed", "unfinished", "requests",
           "censored_residence_max_lower_bound", "travel_metres_total", "mean_routed_users_per_tick",
           "team_zero_service_ticks", "longest_team_zero_service_run", "active_uav_target_changes", "deadline_misses")


def paired_read(values, worlds, conditioning):
    missing = [world for world, value in zip(worlds, values) if value is None]
    if missing:
        return {"n": len(values), "defined": len(values) - len(missing), "values": values,
                "missing_worlds": missing, "mean": None, "interval": None, "conditioning": conditioning,
                "unconditional_32_world_interval_withheld": True, "descriptive_exploration": True}
    return old.paired_t(np.asarray(values, dtype=np.float64), conditioning)


def paired_difference(left, right, conditioning):
    require(len(left) == len(right) == 32, "paired world vector")
    values = [None if a is None or b is None else a - b for a, b in zip(left, right)]
    return paired_read(values, c.MAIN_WORLDS, conditioning)


def compare_panel(readouts, manifest, summary, meter):
    indexed = {(item["arm"], item["world"]): item for item in readouts}
    require(len(indexed) == 224, "unique complete seven-arm panel")
    conditioning = "32 paired new worlds, conditional on this shared old teacher bank, three fixed optimization replicates and G/R programs"
    vectors = {arm: {metric: [indexed[arm, world][metric] for world in c.MAIN_WORLDS] for metric in METRICS}
               for arm in c.ARMS}
    pairs = [(f"S{fit}", baseline) for fit in range(3) for baseline in ("G", "B", "R1", "R4")]
    pairs += [("R4", "G"), ("R1", "G"), ("R1", "R4"), ("B", "G")]
    contrasts = {left + "-" + right: {metric: paired_difference(vectors[left][metric], vectors[right][metric], conditioning)
                                     for metric in METRICS} for left, right in pairs}
    fit_summaries = {}
    for baseline in ("G", "B", "R1", "R4"):
        result = {}
        for metric in METRICS:
            means = [contrasts[f"S{fit}-{baseline}"][metric]["mean"] for fit in range(3)]
            fit_panel = paired_read(means, [0, 1, 2], "3 optimization replicates conditional on one bank and the same32-world panel; df2")
            average = [None if any(vectors[f"S{fit}"][metric][index] is None for fit in range(3)) else
                       float(np.mean([vectors[f"S{fit}"][metric][index] for fit in range(3)])) for index in range(32)]
            result[metric] = {"three_fit_means": fit_panel,
                              "shared_world_student_average": paired_difference(average, vectors[baseline][metric],
                                  "32 common worlds; conditional on this one bank and these three policies, covariance retained")}
        fit_summaries[baseline] = result
    means = {arm: {metric: {"mean": None if any(value is None for value in rows) else float(np.mean(rows)),
                           "values": rows, "missing_worlds": [world for world, value in zip(c.MAIN_WORLDS, rows) if value is None]}
                   for metric, rows in vectors[arm].items()} for arm in c.ARMS}
    cpu = {arm: float(np.mean([indexed[arm, world]["cost"]["inclusive_cpu_seconds"] for world in c.MAIN_WORLDS])) for arm in c.ARMS}
    bank_cost = cost_object(summary["bank_handling_cost"], "shared bank")
    constant_cost = cost_object(read_json(Path(manifest["constant"]["path"]))["acquisition_cost"], "B")
    acquisition_cost = cost_object(summary["acquisition_cost"], "whole new acquisition")
    fit_cost = [cost_object(record["acquisition_cost"], "fit") for record in manifest["fits"]]
    whole = meter.report()["cumulative_cpu_seconds"]
    curves = []
    for fit in range(3):
        student = f"S{fit}"
        marginal = bank_cost["cpu_seconds"] + fit_cost[fit]["cpu_seconds"]
        for baseline in ("G", "B", "R1", "R4"):
            savings = cpu[baseline] - cpu[student]
            comparator_acquisition = bank_cost["cpu_seconds"] + constant_cost["cpu_seconds"] if baseline == "B" else 0.
            incremental = max(0., marginal - comparator_acquisition)
            curves.append({"fit": fit, "baseline": baseline, "student_cpu_per_use": cpu[student],
                           "baseline_cpu_per_use": cpu[baseline], "per_use_cpu_savings": savings,
                           "marginal_shared_bank_plus_one_fit_cpu": marginal,
                           "shared_bank_cpu": bank_cost["cpu_seconds"], "student_fit_cpu": fit_cost[fit]["cpu_seconds"],
                           "B_fit_cpu": constant_cost["cpu_seconds"], "comparator_acquisition_cpu": comparator_acquisition,
                           "incremental_acquisition_difference_cpu": incremental,
                           "marginal_crossing_uses": marginal / savings if savings > 0 else None,
                           "incremental_crossing_uses": incremental / savings if savings > 0 else None,
                           "historical_teacher_measured_cpu_seconds": 7026.128558,
                           "historical_teacher_crossing_measured_lower_bound": (7026.128558 + marginal) / savings if savings > 0 else None,
                           "historical_teacher_unknown_additive_acquisition_and_reader_cost": True,
                           "whole_study_crossing_uses": whole / savings if savings > 0 else None,
                           "whole_study_scope": "one shared purchased study, not multiplied by three; incompletely metered support unknown",
                           "service_contrasts": contrasts[student + "-" + baseline],
                           "no_value_equivalence_or_deployment_volume_assumption": True})
    for world in c.MAIN_WORLDS:
        r1, r4 = indexed["R1", world], indexed["R4", world]
        require(r1["first_public_identity"] == r4["first_public_identity"], "paired initial R public input identity")
        if r1["first_cohort_identity"] is not None and r4["first_cohort_identity"] is not None:
            require(r1["first_cohort_identity"] == r4["first_cohort_identity"], "same initial input, same tape0 complete cohort")
    deployment = sum(item["cost"]["inclusive_cpu_seconds"] for item in readouts)
    return {"main_worlds": list(c.MAIN_WORLDS), "means": means, "contrasts": contrasts,
            "fit_conditional_summaries": fit_summaries, "cpu_crossings": curves,
            "inclusive_cpu_per_use": cpu, "shared_bank_handling_cost": bank_cost,
            "constant_fit_cost": constant_cost, "per_fit_cost": fit_cost, "whole_new_acquisition_cost": acquisition_cost,
            "deployment_inclusive_cpu_seconds": deployment,
            "worker_unattributed_cpu_residual": summary["cost"]["phase_cpu_seconds"] - acquisition_cost["cpu_seconds"] - deployment,
            "worker_unattributed_scope": "outer setup, final metadata/endpoint close/hash/publication and timing-boundary residual; not zero",
            "old_teacher_measured_mission_cpu_seconds": 7026.128558, "old_teacher_measured_mission_cpu_hours": 1.951702,
            "old_teacher_unknown_extra_acquisition_and_reader_cost": True,
            "old_whole_B05_research_CPU_hours_approx": 5.374, "overlapping_old_scopes_not_added_twice": True,
            "whole_new_research_CPU_intercept_counted_once": whole, "unknown_support_is_zero": False,
            "CPU_request_cost_exchange_rate": None, "positive_effect_threshold_or_equivalence_claim": False}


def run(root, out, args, context):
    """One source-bound complete worker read; failure preserves paid prefixes."""
    root, out, worker_root = Path(root), Path(out), Path(context["worker_root"])
    meter, manifest, summary = context["meter"], context["manifest"], context["worker_summary"]
    audit, readouts = Audit(meter, context["source_identity"]), []
    try:
        # Bound output size: detailed request/user checks and all compact update
        # summaries, without duplicating raw arrays or optimizer evidence.
        meter.check_disk(anticipated_bytes=96 * 1024**2)
        records = validate_manifest(worker_root, manifest, summary, context["worker_config"], audit.source_identity, audit)
        models, constant, acquisition = acquire_checks(root, worker_root, context, audit)
        write_json(out / "acquisition-checks.json", acquisition)
        for record in records:
            meter.check()
            result = read_mission(record, worker_root, manifest, audit, models, constant)
            write_json(out / "checks" / record["label"] / f"{record['world']}.json", result)
            readouts.append(result)
            write_json(out / "progress.json", {"checked_missions": len(readouts), "last_record": record,
                                               "counts": audit.counts, "cost": meter.report()})
        endpoints = {record["name"]: record for record in manifest["endpoint_counts"]}
        require(set(endpoints) == set(c.ARMS) and len(endpoints) == len(manifest["endpoint_counts"]), "seven endpoint count names")
        worker_neural = sum(record["counts"]["frozen_nn_rows"] for record in endpoints.values())
        require(audit.counts.get("deployment_neural_rows", 0) <= worker_neural <= 23040, "committed/censored student rows")
        neural_exposure = {}
        for arm in c.ARMS:
            counts = endpoints[arm]["counts"]
            attempted, completed = counts["frozen_nn_attempted_rows"], counts["frozen_nn_rows"]
            committed = 4 * sum(item["committed_neural_decisions"] for item in readouts if item["arm"] == arm)
            require(0 <= committed <= completed <= attempted <= (7680 if arm.startswith("S") else 0) and
                    attempted % 4 == completed % 4 == 0, "worker neural attempts/completion/cache exposure")
            neural_exposure[arm] = {"worker_attempted_rows": attempted, "worker_completed_rows": completed,
                                    "committed_cache_rows_replayed": committed,
                                    "completed_rows_without_committed_cache": completed - committed,
                                    "attempted_rows_without_completed_forward": attempted - completed}
        require(audit.counts["neural_rows"] == audit.counts["bank_neural_rows"] + audit.counts.get("deployment_neural_rows", 0) <= 73440 and
                audit.counts["bank_neural_rows"] == 50400 and audit.counts["native_physical_states"] == 269024 and
                audit.counts["native_motion_steps"] == 268800 and audit.counts["missions"] == 224,
                "complete reader fixed exposure with declared neural censoring")
        require(sum(len(item["rollout_checks"]) for item in readouts) == 3840, "all new R1/R4 traces read")
        B_commits = audit.counts.get("B_committed_scores", 0)
        B_lower = endpoints["B"]["counts"]["constant_scores"]
        B_interrupted = sum(item["deadline_misses"] for item in readouts if item["arm"] == "B")
        require(0 <= B_commits - B_lower <= B_interrupted, "B final publication gaps only on interrupted decisions")
        comparison = compare_panel(readouts, manifest, summary, meter)
        reading = {"schema": 1, "object": c.OBJECT, "status": "COMPLETE", "mode": "reader", "launch_sha": args.launch_sha,
                   "worker_launch_sha": summary["launch_sha"], "source_identity": audit.source_identity,
                   "missions": 224, "counts": audit.counts, "acquisition_checks": "acquisition-checks.json",
                   "comparison": comparison, "per_record_checks": "checks/main/<arm>/<world>.json",
                   "input_identities": {name: context[name] for name in ("config_identity", "summary_identity", "manifest_identity") if name in context},
                   "new_teacher_collection": 0, "old_physics_replayed": False, "optimizer_updates": 0,
                   "B_lower_completed_counter": B_lower, "B_committed_score_payloads": B_commits,
                   "deployment_neural_exposure": neural_exposure,
                   "numerical_comparison": "exact source-bound masks/routes/FIFO/G/features/composition/frozen outputs; gradient norms finite diagnostics only",
                   "cost": meter.report()}
        write_json(out / "reading.json", reading)
        write_json(out / "summary.json", reading)
        meter.check_disk()
    except BaseException as error:
        reading = {"schema": 1, "object": c.OBJECT, "status": "FAILED", "mode": "reader", "launch_sha": args.launch_sha,
                   "checked_missions": len(readouts), "counts": audit.counts,
                   "error": {"type": type(error).__name__, "message": str(error)}, "cost": meter.report()}
        write_json(out / "reading.json", reading)
        write_json(out / "summary.json", reading)
        raise

"""Independent old-byte and state-certificate audit; zero new model queries.

This module imports no controller, scorer, simulator or native environment.
It reconstructs certificate state and work from immutable audited arrays.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import platform
import re
import struct
import time

import numpy as np

from .inputs import (COUNT_KEYS, KINDS, DIRECTION, OBJECT_ID, LOGICAL_COSTS, SEED,
                     VARIANTS, WORLD_IDS, OriginalInputs, checked_file, load_arrays,
                     load_catalog, load_trace, payload_binding, public_users,
                     record_bytes, same_array, same_payload, same_record)

# Independent declarations of the two actually used, source-bound formats.
SEGMENT_KEY_LAYOUT = "<i8 phase40,mask,n_uavs; <f8 physical[8,3],estimated[8,3],users[50,2]; <f4 issued[8,3],public_users[100]"
B06_KEY_LAYOUT = "<i8 phase40,mask; <f8 physical[8,3],estimated[8,3]; <f4 issued[8,3],public_users[50,2]"


def _zeros():
    return {name: 0 for name in COUNT_KEYS}


def _controller_zeros():
    return {kind: _zeros() for kind in KINDS}


def _add_counts(target, source):
    for name in COUNT_KEYS:
        value = source[name]
        if type(value) is not int or value < 0:
            raise ValueError("noninteger or negative scientific query counter")
        target[name] += value


def _trace(decision, target):
    for kind in KINDS:
        if kind in decision:
            source = decision[kind].get("counts", decision[kind])
            _add_counts(target[kind], source)


def _requests(counts):
    return sum(counts[kind]["requested_candidates"] for kind in KINDS)


def _envelope_matches(envelope, expected, label):
    value = np.asarray(expected)
    dtype = value.dtype.newbyteorder("<")
    if (set(envelope) != {"dtype", "shape", "hex"} or envelope["dtype"] != dtype.str
            or envelope["shape"] != list(value.shape)
            or envelope["hex"] != value.astype(dtype, copy=False).tobytes(order="C").hex()):
        raise ValueError(f"boundary array envelope mismatch: {label}")


def _history(record, *, next_t, mask, physical, positions, users, commands, label):
    if set(record) != {"next_t", "n_uavs", "mask", "physical", "positions", "users", "commands"}:
        raise ValueError(f"boundary fields differ: {label}")
    for name, expected in (("next_t", next_t), ("n_uavs", 8), ("mask", mask)):
        if type(record[name]) is not int or record[name] != expected:
            raise ValueError(f"boundary scalar differs: {label}/{name}")
    for name, value in (("physical", physical), ("positions", positions), ("users", users), ("commands", commands)):
        _envelope_matches(record[name], value, f"{label}/{name}")


def _key(layout, t, physical, estimate, users, command, mask, report):
    f64 = lambda value: np.asarray(value, dtype="<f8").tobytes(order="C")
    f32 = lambda value: np.asarray(value, dtype="<f4").tobytes(order="C")
    if layout == B06_KEY_LAYOUT:
        return (struct.pack("<qq", t % 40, mask) + f64(physical) + f64(estimate)
                + f32(command) + f32(report[32:132]))
    if layout == SEGMENT_KEY_LAYOUT:
        return (struct.pack("<qqq", t % 40, mask, 8) + f64(physical) + f64(estimate)
                + f64(users) + f32(command) + f32(report[32:132]))
    raise ValueError("unrecognized recurrence key layout")


def _barrier_and_plan(identifier, certificate, reference):
    decisions = reference.payload["decisions"]
    arrivals = [i for i, row in enumerate(decisions) if row["phase"] == "arrival"]
    if len(arrivals) > 1:
        raise ValueError("more than one arrival in a bounded original segment")
    plan = certificate["plan"]
    if reference.plan_bound:
        same_record(plan, reference.expected_plan, "full recoverable original plan")
    if not arrivals:
        if plan is not None and plan.get("initiated") is not False:
            raise ValueError("certificate adds an absent original arrival")
        if any(row["phase"] != "ordinary" for row in decisions):
            raise ValueError("unexpected original no-arrival segment phase")
        return reference.start
    duration = arrivals[0]
    barrier = reference.start + duration
    if (not isinstance(plan, dict) or plan.get("initiated") is not True
            or type(plan.get("duration")) is not int or plan["duration"] != duration
            or duration not in (10, 20, 30, 40) or plan["arrival_t"] != barrier
            or plan.get("start_t", reference.start) != reference.start):
        raise ValueError("certificate plan does not match original arrival boundary")
    if any(decisions[i]["phase"] != ("transit" if i < duration else "arrival" if i == duration else "ordinary")
           for i in range(len(decisions))):
        raise ValueError("original segment phase ordering differs")
    if not 0 <= plan["member"] < 8 or (reference.entry_mask & (1 << plan["member"])):
        raise ValueError("invalid/speaking planned member")
    command = np.asarray(plan["commands"], dtype=np.float32)
    same_array(command, reference.payload["arrays"]["actions"][:duration], "fixed original transit commands")
    if np.any(np.delete(command, plan["member"], axis=1)):
        raise ValueError("transit changes another member")
    local = identifier.split("/")[2] if reference.kind == "prefix" else identifier.rsplit("/", 1)[-1]
    if reference.kind != "suffix":
        match = re.fullmatch(r"m([0-7])_s([0-9]+)", local)
        if match is None or (plan["member"], plan["site"]) != tuple(map(int, match.groups())):
            raise ValueError("plan member/site differ from original branch identity")
    return barrier


def _reports(arrays, start, end):
    times, reports = arrays["report_times"], arrays["reports"]
    same_array(times, np.arange(start, end, 10, dtype=np.int64), "absolute model report times")
    if reports.dtype != np.dtype(np.float32) or reports.shape != (len(times), 133):
        raise ValueError("original report shape/dtype differs")
    first = reports[0]
    for index, t in enumerate(times):
        same_array(reports[index, 32:132], first[32:132], "static public-user bits")
        if index == 0:
            continue
        # Only codec arithmetic on saved physical positions, no model call.
        expected = first.copy()
        physical = np.asarray(arrays["positions"][int(t) - start], dtype=np.float32)
        expected[:24].reshape(8, 3)[:, :2] = physical[:, :2] / 1000.0
        expected[:24].reshape(8, 3)[:, 2] = (physical[:, 2] - 50.0) / 100.0
        expected[-1] = np.float32(float(t) / 500.0)
        same_array(reports[index], expected, f"regenerated absolute report/{t}")


def verify_certificate(identifier, record, reference, reuse):
    """Reconstruct all certificate facts from original arrays, without simulation."""
    if set(record) != {"id", "certificate", "scientific"} or record["id"] != identifier:
        raise ValueError("segment certificate identity/fields differ")
    same_record(record["scientific"], payload_binding(reference.payload), "segment scientific digest")
    cert, arrays = record["certificate"], reference.payload["arrays"]
    start, end = reference.start, reference.end
    count = end - start
    if (set(cert) != {"schema", "start_t", "end_t", "report_horizon", "plan", "entry_report", "entry", "terminal", "reuse"}
            or cert["schema"] != "b08_exact_segment.v1"
            or cert["start_t"] != start or cert["end_t"] != end or cert["report_horizon"] != 500):
        raise ValueError("fixed segment certificate bounds/schema differ")
    shapes = {"positions": ((count + 1, 8, 3), np.dtype("<f8")),
              "controller_estimates": ((count + 1, 8, 3), np.dtype("<f8")),
              "actions": ((count, 8, 3), np.dtype("<f4")),
              "masks": ((count,), np.dtype("<i8")),
              "reward_components": ((count, 4), np.dtype("<f8"))}
    for name, (shape, dtype) in shapes.items():
        if arrays[name].shape != shape or arrays[name].dtype != dtype:
            raise ValueError(f"original segment array dimensions differ: {name}")
    if len(reference.payload["decisions"]) != count:
        raise ValueError("original segment decision count differs")
    _reports(arrays, start, end)
    report = arrays["reports"][0]
    _envelope_matches(cert["entry_report"], report, "entry report")
    _history(cert["entry"], next_t=start, mask=reference.entry_mask,
             physical=arrays["positions"][0], positions=arrays["controller_estimates"][0],
             commands=reference.entry_commands, users=reference.entry_users, label="entry")
    _history(cert["terminal"], next_t=end, mask=int(arrays["masks"][-1]),
             physical=arrays["positions"][-1], positions=arrays["controller_estimates"][-1],
             commands=arrays["actions"][-1], users=public_users(arrays["reports"][-1]), label="terminal")
    same_array(reference.entry_users, public_users(report), "history/static public-user agreement")
    barrier = _barrier_and_plan(identifier, cert, reference)
    work = cert["reuse"]
    b06 = reuse and identifier.startswith("actual/t40/branch/")
    layout = B06_KEY_LAYOUT if b06 else SEGMENT_KEY_LAYOUT
    schema = "exact_ordinary_recurrence.v1" if b06 else "b08_exact_recurrence.v1"
    if work["key_layout"] != layout or work["schema"] != schema or work["eligibility_after_t"] != barrier:
        raise ValueError("actual recurrence schema/key/barrier differs")
    logical_cc, actual_cc = _controller_zeros(), _controller_zeros()
    logical_rc, actual_rc = _zeros(), _zeros()
    source_times, first_repeat, cache = [], None, {}
    users = reference.entry_users
    computed = 0
    for i, decision in enumerate(reference.payload["decisions"]):
        t = start + i
        if decision["t"] != t:
            raise ValueError("original absolute model clock differs")
        entering_command = reference.entry_commands if i == 0 else arrays["actions"][i - 1]
        entering_mask = reference.entry_mask if i == 0 else int(arrays["masks"][i - 1])
        key = _key(layout, t, arrays["positions"][i], arrays["controller_estimates"][i],
                   users, entering_command, entering_mask, report)
        source_t = t
        if reuse and t > barrier:
            source_t = cache.setdefault(key, t)
        source_times.append(source_t)
        # A fresh reward scorer receives one full team. Its per-UAV geometry
        # reuse counts equal unique position-row bytes, without a radio query.
        unique_rows = len({row.tobytes() for row in arrays["positions"][i + 1]})
        reward_counts = {"requested_candidates": 1, "scored_candidates": 1,
                         "cached_candidates": 0, "geometry_rows_computed": unique_rows,
                         "geometry_rows_reused": 8 - unique_rows}
        _trace(decision, logical_cc)
        _add_counts(logical_rc, reward_counts)
        if source_t == t:
            computed += 1
            _trace(decision, actual_cc)
            _add_counts(actual_rc, reward_counts)
        else:
            j = source_t - start
            if source_t <= barrier or source_t >= t or source_times[j] != source_t or (t - source_t) % 40:
                raise ValueError("invalid computed recurrence source")
            if first_repeat is None:
                first_repeat = {"source_t": source_t, "repeat_t": t, "period": t - source_t,
                                "phase": t % 40, "entering_mask": entering_mask,
                                "key_sha256": hashlib.sha256(key).hexdigest()}
            for name in ("actions", "masks", "reward_components"):
                same_array(arrays[name][i], arrays[name][j], f"reuse transition/{name}/{t}")
            for name in ("positions", "controller_estimates"):
                same_array(arrays[name][i + 1], arrays[name][j + 1], f"reuse next state/{name}/{t}")
            source_decision = deepcopy(reference.payload["decisions"][j])
            source_decision["t"] = t
            same_record(decision, source_decision, f"reuse decision/{t}")
    summary = reference.payload["summary"]
    same_record(logical_cc, summary["controller_counts"], "original logical controller ledger")
    same_record(logical_rc, summary["reward_counts"], "original logical reward ledger")
    expected = {"schema": schema, "key_layout": layout, "eligibility_after_t": barrier,
                "computed_ticks": computed, "reused_ticks": count - computed,
                "logical_controller_calls": count, "actual_controller_calls": computed,
                "logical_reward_calls": count, "actual_reward_calls": computed,
                "logical_controller_counts": logical_cc, "actual_controller_counts": actual_cc,
                "logical_reward_counts": logical_rc, "actual_reward_counts": actual_rc,
                "logical_controller_requests": _requests(logical_cc), "actual_controller_requests": _requests(actual_cc),
                "logical_reward_requests": logical_rc["requested_candidates"],
                "actual_reward_requests": actual_rc["requested_candidates"],
                "logical_requested_candidates": _requests(logical_cc) + logical_rc["requested_candidates"],
                "actual_requested_candidates": _requests(actual_cc) + actual_rc["requested_candidates"],
                "logical_candidate_position_predictions": logical_cc["motion"]["requested_candidates"],
                "actual_candidate_position_predictions": actual_cc["motion"]["requested_candidates"],
                "first_repeat": first_repeat, "source_times": source_times,
                "logical_report_calls": len(arrays["report_times"]), "actual_report_calls": len(arrays["report_times"])}
    same_record(work, expected, "complete independently reconstructed recurrence ledger")
    return {"start_t": start, "end_t": end, "eligibility_after_t": barrier,
            "computed_ticks": computed, "reused_ticks": count - computed,
            "actual_controller_counts": actual_cc, "actual_reward_counts": actual_rc,
            "actual_requested_candidates": expected["actual_requested_candidates"],
            "logical_requested_candidates": expected["logical_requested_candidates"],
            "first_repeat": first_repeat}


def expected_segments(catalog, arm):
    if arm == "G2":
        return [row["id"] for row in catalog["model_branches"]]
    result, first_seen = [], set()
    for row in catalog["model_branches"]:
        identifier = row["id"]
        if identifier.startswith("a2/first/"):
            first = identifier.split("/")[2]
            if first not in first_seen:
                first_seen.add(first)
                result.append(f"a2/first/{first}/prefix")
            result.append(f"a2/first/{first}/suffix" if identifier.endswith("/outer") else identifier)
        else:
            result.append(identifier)
    return result


def verify_history(row, out, inputs):
    mark = (time.perf_counter(), time.process_time())
    arm, mode = row["variant"].split("_")
    if (arm != row["arm"] or (mode == "reuse") != row["reuse"] or row["steps"] != 500
            or row["complete"] is not True or row["error"] is not None or row["new_native_steps"] != 0):
        raise ValueError("complete replay history metadata differs")
    reference = inputs.episode(arm, row["world_id"])
    same_record(row["original_native"], reference.row["raw"], "original native binding")
    same_record(row["original_metrics"], reference.row["metrics"], "inherited native metrics, not recomputed")
    raw = load_arrays(checked_file(out, row["commands"]))
    if set(raw) != {"actions", "masks"}:
        raise ValueError("replay command keys differ")
    same_array(raw["actions"], reference.native["actions"], "all500 actual commands")
    same_array(raw["masks"], reference.native["mask"], "all500 actual masks")
    decisions = load_trace(checked_file(out, row["decisions"]))
    same_record(decisions, reference.decisions, "all500 actual decisions")
    counts, calls, predictions = _controller_zeros(), {kind: 0 for kind in KINDS}, 0
    for t, decision in enumerate(decisions):
        if decision["t"] != t:
            raise ValueError("actual clock missing or reordered")
        _trace(decision, counts)
        for kind in KINDS:
            calls[kind] += int(kind in decision)
        predictions += 216 * int("motion" in decision)
    for name, value in (("native_candidate_counts", counts), ("calls", calls), ("position_predictions", predictions)):
        same_record(row[name], value, f"new controller ledger/{name}")
        same_record(value, reference.row[name], f"old controller ledger/{name}")
    same_record(row["logical_costs"], reference.row["costs"], "original complete logical ledger")
    catalog = load_catalog(checked_file(out, row["evidence_catalog"]))
    if set(catalog) != set(reference.catalog):
        raise ValueError("new complete catalog fields differ")
    for name in ("plans", "selections", "banks"):
        same_record(catalog[name], reference.catalog[name], f"complete program/{name}")
    if [b["id"] for b in catalog["model_branches"]] != [b["id"] for b in reference.catalog["model_branches"]]:
        raise ValueError("complete emitted model branch order differs")
    for branch in catalog["model_branches"]:
        payload = {"arrays": load_arrays(checked_file(out, branch["raw"])),
                   "decisions": load_trace(checked_file(out, branch["decisions"])), "summary": branch["summary"]}
        same_payload(payload, reference.branch(branch["id"]), f"emitted branch/{branch['id']}")
        same_record(branch["scientific"], payload_binding(payload), "emitted scientific digest")
    if [b["id"] for b in catalog["candidate_banks"]] != [b["id"] for b in reference.catalog["candidate_banks"]]:
        raise ValueError("stationary candidate bank order differs")
    for bank in catalog["candidate_banks"]:
        saved = np.load(checked_file(out, bank["raw"]), allow_pickle=False)
        same_array(saved, reference.bank(bank["id"]), f"every stationary candidate/{bank['id']}")
    records = load_trace(checked_file(out, row["certificates"]))
    if [r["id"] for r in records] != expected_segments(reference.catalog, arm):
        raise ValueError("complete segment certificate order/coverage differs")
    verified = [{"id": record["id"], "scientific": record["scientific"],
                 **verify_certificate(record["id"], record, reference.segment(record["id"]), row["reuse"])}
                for record in records]
    same_record(row["segments"], verified, "complete independently checked segment readings")
    final = row["final_history"]
    if set(final) != {"next_t", "n_uavs", "mask", "positions", "users", "commands"}:
        raise ValueError("actual terminal history fields differ")
    if (final["next_t"], final["n_uavs"], final["mask"]) != (500, 8, int(reference.native["mask"][-1])):
        raise ValueError("actual terminal clock/mask differs")
    _envelope_matches(final["commands"], reference.native["actions"][-1], "actual final issued commands")
    _envelope_matches(final["users"], public_users(reference.native["states"][490]), "actual final public users")
    # Private actual terminal positions were not in the old native artifact.
    # The caller also checks their bits against the newly timed frozen original
    # variant; model terminal certificates above use the archived arrays directly.
    if (final["positions"]["dtype"] != "<f8" or final["positions"]["shape"] != [8, 3]
            or len(bytes.fromhex(final["positions"]["hex"])) != 8 * 3 * 8):
        raise ValueError("actual terminal estimate envelope differs")
    actual = _zeros()
    _add_counts(actual, reference.row["costs"]["native_controller_counts_excluding_banks"])
    _add_counts(actual, reference.row["costs"]["stationary_bank_counts"])
    for item in verified:
        for kind in KINDS:
            if kind != "option":
                _add_counts(actual, item["actual_controller_counts"][kind])
        _add_counts(actual, item["actual_reward_counts"])
    if sum(item["end_t"] - item["start_t"] for item in verified) != row["logical_costs"]["model_physical_transitions"]:
        raise ValueError("segment versus complete-branch tick ledger differs")
    return {"variant": row["variant"], "world_id": row["world_id"], "all_scientific_bytes_equal": True,
            "model_segments_verified": len(verified), "model_branches_verified": len(catalog["model_branches"]),
            "stationary_banks_verified": len(catalog["candidate_banks"]),
            "computed_model_ticks": sum(item["computed_ticks"] for item in verified),
            "reused_model_ticks": sum(item["reused_ticks"] for item in verified),
            "actual_all_state_mask_counts": actual,
            "actual_state_mask_requests": actual["requested_candidates"],
            "logical_state_mask_requests": row["logical_costs"]["worker_state_mask_requests"],
            "first_repeats": [{"segment": item["id"], **item["first_repeat"]}
                              for item in verified if item["first_repeat"] is not None],
            "worker_timing": row["timing"],
            "reader_timing": {"cpu_seconds": time.process_time() - mark[1],
                              "wall_seconds": time.perf_counter() - mark[0]}}


def _write_json(path, value):
    path = Path(path)
    partial = path.with_suffix(path.suffix + ".partial")
    partial.write_bytes(json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n")
    partial.replace(path)


def read_run(out):
    out = Path(out)
    mark = (time.perf_counter(), time.process_time())
    summary = json.loads((out / "summary.json").read_text())
    if summary["status"] != "collected" or summary["worker_status"] != "complete":
        raise ValueError("worker has not completed all selected histories")
    config = json.loads(checked_file(out, summary["config_artifact"]).read_text())
    if (config["object_id"] != OBJECT_ID or config["direction"] != DIRECTION
            or config["launch_sha"] != summary["launch_sha"]
            or not re.fullmatch(r"[0-9a-f]{40}", config["launch_sha"])):
        raise ValueError("fixed admitted source/object identity differs")
    manifest = json.loads((out / "launch-manifest.json").read_text())
    if (manifest["acceptance"] != "accepted" or manifest["sha"] != config["launch_sha"]
            or manifest["direction"] != DIRECTION or manifest["node"] != "local_linux"
            or manifest["command_sha256"] != config["admission_command_sha256"]):
        raise ValueError("actual accepted local operation binding differs")
    spec = {"world_ids": list(WORLD_IDS), "variants": list(VARIANTS), "n_uavs": 8, "horizon": 500,
            "report_cadence": 10, "order": "ascending original world; variants rotated by world index mod4",
            "seed": SEED, "rng_draws": 0, "torch_threads": 1}
    same_record(config["spec"], spec, "fixed complete replay design")
    for name in ("new_native_steps", "new_worlds", "new_fits", "updates", "new_training_targets", "independent_reader_model_queries"):
        if config[name] != 0 or summary[name] != 0:
            raise ValueError("zero new native/learning/reader-query contract differs")
    same_record(config["expected_logical_costs"], LOGICAL_COSTS, "fixed logical work")
    verification_mark = (time.perf_counter(), time.process_time())
    originals = config["original_inputs"]
    inputs = OriginalInputs(originals["records_root"], originals["bulk_root"])
    same_record(inputs.binding(), originals, "complete original input binding")
    same_record(inputs.sources, config["source_bindings"], "executed source bytes")
    common_verification = {"cpu_seconds": time.process_time() - verification_mark[1],
                           "wall_seconds": time.perf_counter() - verification_mark[0]}
    order = [(VARIANTS[(i + offset) % 4], world) for i, world in enumerate(WORLD_IDS) for offset in range(4)]
    rows = summary["histories"]
    if [(row["variant"], row["world_id"]) for row in rows] != order:
        raise ValueError("complete interleaved variant order differs")
    readings = []
    for row in rows:
        value = verify_history(row, out, inputs)
        readings.append(value)
        _write_json(out / "progress.json", {"phase": "reader", "verified_histories": len(readings),
                                            "variant": row["variant"], "world_id": row["world_id"]})
        print(json.dumps({"independent_histories_verified": len(readings), "variant": row["variant"],
                          "world_id": row["world_id"]}), flush=True)
    panel = {(row["variant"], row["world_id"]): row for row in rows}
    for world in WORLD_IDS:
        for arm in ("G2", "A2"):
            same_record(panel[f"{arm}_reuse", world]["final_history"],
                        panel[f"{arm}_original", world]["final_history"], "actual terminal history to timed original")
    costs = {name: sum(row["logical_costs"][name] for row in rows) for name in LOGICAL_COSTS}
    same_record(costs, LOGICAL_COSTS, "complete replay logical total")
    same_record(summary["logical_costs"], costs, "worker logical total")
    aggregate = {}
    for variant in VARIANTS:
        group = [row for row in readings if row["variant"] == variant]
        aggregate[variant] = {name: sum(row[name] for row in group) for name in (
            "computed_model_ticks", "reused_model_ticks", "actual_state_mask_requests", "logical_state_mask_requests",
            "model_segments_verified", "model_branches_verified", "stationary_banks_verified")}
        for kind in ("cpu_seconds", "wall_seconds"):
            worker = sum(row["worker_timing"][kind] for row in group)
            reader = sum(row["reader_timing"][kind] for row in group)
            aggregate[variant][f"worker_{kind}"] = worker
            aggregate[variant][f"reader_{kind}"] = reader
            aggregate[variant][f"worker_plus_reader_{kind}"] = worker + reader
    comparisons = {}
    for left, right in (("G2_reuse", "G2_original"), ("A2_reuse", "A2_original"), ("A2_reuse", "G2_reuse")):
        fields = ("worker_cpu_seconds", "worker_wall_seconds", "worker_plus_reader_cpu_seconds",
                  "worker_plus_reader_wall_seconds", "actual_state_mask_requests")
        comparisons[f"{left}/{right}"] = {field: aggregate[left][field] / aggregate[right][field] for field in fields}
    result = {"status": "complete", "source_sha": summary["launch_sha"], "config_artifact": summary["config_artifact"],
              "histories_verified": len(readings), "controller_clock_calls_verified": 32000,
              "new_native_steps": 0, "new_worlds": 0, "new_fits": 0, "updates": 0, "new_training_targets": 0,
              "reader_policy_queries": 0, "reader_scorer_queries": 0, "reader_model_queries": 0, "reader_native_queries": 0,
              "all_original_scientific_payload_bits_and_records_equal": True,
              "all_model_terminal_states_recovered_from_original_arrays": True,
              "all_actual_terminal_histories_equal_timed_original": True,
              "all_recurrence_keys_sources_and_actual_work_independently_reconstructed": True,
              "original_inputs": inputs.binding(), "logical_costs": costs,
              "aggregates": aggregate, "cost_ratios": comparisons, "histories": readings,
              "common_original_input_verification_timing": common_verification,
              "timing": {"cpu_seconds": time.process_time() - mark[1], "wall_seconds": time.perf_counter() - mark[0]},
              "cost_scope": "ratios of summed matched per-history work; shared input verification and enclosing-chain overhead separately charged",
              "native_scope": "old bound native outcomes preserved; no new native throughput, reward or fresh-world evidence",
              "timing_exposure": "one prospectively ordered replay per variant/world; no resampling or population precision claim"}
    _write_json(out / "reading.json", result)
    return result

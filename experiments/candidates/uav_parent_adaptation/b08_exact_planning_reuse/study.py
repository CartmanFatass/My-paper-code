"""Admitted, fully recorded saved-history replay; no native environment calls."""
from copy import deepcopy
from datetime import datetime, timezone
import gc
import gzip
import json
import os
from pathlib import Path
import platform
import re
import resource
import time

import numpy as np
import torch

from .controller import TemporalProgram
from .segment import encode_array
from .inputs import (COUNT_KEYS, KINDS, DIRECTION, OBJECT_ID, VARIANTS, WORLD_IDS,
                     LOGICAL_COSTS, SEED, OriginalInputs, artifact, checked_file,
                     json_record, payload_binding, record_bytes, same_array,
                     same_payload, same_record, source_bindings)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    partial.write_bytes(json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n")
    partial.replace(path)


def write_trace(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as stream:
            for row in rows:
                stream.write(record_bytes(row) + b"\n")


def write_catalog(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as stream:
            stream.write(record_bytes(value) + b"\n")


def write_arrays(path, arrays):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)


def resources():
    own, child = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"self_user_seconds": own.ru_utime, "self_system_seconds": own.ru_stime,
            "child_user_seconds": child.ru_utime, "child_system_seconds": child.ru_stime,
            "peak_rss_kib_process": own.ru_maxrss,
            "scope": "process lifetime including imports; child CPU separate"}


def execution_context():
    """Read-only sampled process context; no reservation or process control."""
    others = []
    for directory in Path("/proc").iterdir():
        if not directory.name.isdigit() or int(directory.name) == os.getpid():
            continue
        try:
            argv = (directory / "cmdline").read_bytes().split(b"\0")
            if not argv or b"python" not in Path(os.fsdecode(argv[0])).name.encode():
                continue
            command = b" ".join(argv).decode(errors="replace")
            entries = re.findall(r"(?:experiments/candidates/[\w/.-]+|experiments\.candidates\.[\w.]+|runs/[\w/.-]+)", command)
            if not entries:
                continue
            stat = (directory / "stat").read_text().rsplit(")", 1)[1].split()
            others.append({"pid": int(directory.name), "source_or_output": entries,
                           "start_ticks": int(stat[19]), "cpu_ticks": int(stat[11]) + int(stat[12])})
        except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError, IndexError):
            continue
    return {"at": datetime.now(timezone.utc).isoformat(), "host": platform.node(),
            "pid": os.getpid(), "load_average": list(os.getloadavg()),
            "other_scientific_processes": sorted(others, key=lambda item: item["pid"]),
            "scope": "sampled history boundaries, not continuous isolation certification"}


def fixed_config(inputs):
    return {"object_id": OBJECT_ID, "direction": DIRECTION,
            "spec": {"world_ids": list(WORLD_IDS), "variants": list(VARIANTS),
                     "n_uavs": 8, "horizon": 500, "report_cadence": 10,
                     "order": "ascending original world; variants rotated by world index mod4",
                     "seed": SEED, "rng_draws": 0, "torch_threads": 1},
            "original_inputs": inputs.binding(), "source_bindings": inputs.sources,
            "expected_logical_costs": LOGICAL_COSTS,
            "new_native_steps": 0, "new_worlds": 0, "new_fits": 0, "updates": 0,
            "new_training_targets": 0, "independent_reader_model_queries": 0,
            "primary_costs": ["G2_reuse/G2_original", "A2_reuse/A2_original", "A2_reuse/G2_reuse"],
            "equality": "all original scientific array payload bits/dtypes/shapes and ordered records",
            "native_scope": "old audited outcomes retained by unchanged full commands/masks; no new native throughput",
            "barriers": "actual modeled program boundaries; G2 t40 C-only model has no120 event",
            "versions": {"python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__}}


def _counts():
    return {kind: {name: 0 for name in COUNT_KEYS} for kind in KINDS}


def _add_trace(decision, target):
    for kind in KINDS:
        if kind in decision:
            counts = decision[kind].get("counts", decision[kind])
            for name in COUNT_KEYS:
                target[kind][name] += int(counts[name])


def _identifier(identifier):
    if not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", identifier):
        raise ValueError("invalid evidence identifier")
    return Path(*identifier.split("/"))


def _clock():
    return time.perf_counter(), time.process_time()


def _elapsed(mark):
    return {"wall_seconds": time.perf_counter() - mark[0], "cpu_seconds": time.process_time() - mark[1]}


def replay_history(variant, world_id, out, inputs):
    mark = _clock()
    arm, mode = variant.split("_")
    reuse = mode == "reuse"
    key = f"n8_{variant}_w{world_id}"
    root = out / "raw" / key
    root.mkdir(parents=True, exist_ok=False)
    context_before = execution_context()
    input_mark = _clock()
    reference = inputs.episode(arm, world_id)
    input_timing = _elapsed(input_mark)
    branch_records, bank_records, segment_records = [], [], []
    branch_ids, bank_ids, segment_ids = set(), set(), set()
    commands, masks, decisions = [], [], []
    counts, calls = _counts(), {kind: 0 for kind in KINDS}
    predictions = 0
    buckets = {name: {"cpu_seconds": 0., "wall_seconds": 0.} for name in (
        "controller_including_callbacks", "selection_including_callbacks", "segment_check_and_certificate",
        "branch_check_and_output", "bank_check_and_output")}
    certificate_path = out / "certificates" / f"{key}.jsonl.gz"
    certificate_path.parent.mkdir(parents=True, exist_ok=True)
    certificate_raw = certificate_path.open("xb")
    certificate_stream = gzip.GzipFile(fileobj=certificate_raw, mode="wb", mtime=0)

    def add_timing(name, start):
        elapsed = _elapsed(start)
        for field in elapsed:
            buckets[name][field] += elapsed[field]

    def segment_sink(identifier, payload):
        begin = _clock()
        if identifier in segment_ids:
            raise ValueError("duplicate model segment certificate")
        segment_ids.add(identifier)
        record = {"id": identifier, "certificate": payload["certificate"],
                  "scientific": payload_binding(payload)}
        certificate_stream.write(record_bytes(record) + b"\n")
        certificate_stream.flush()
        try:
            expected = reference.segment(identifier)
            same_payload(payload, expected.payload, f"{key}/{identifier}")
            # Independent certificate arithmetic also runs before a divergent
            # boundary can affect subsequent saved-report reconstruction.
            from .reader import verify_certificate
            verified = verify_certificate(identifier, record, expected, reuse)
        except BaseException:
            failure = root / "first-mismatch" / _identifier(identifier)
            write_arrays(failure.with_suffix(".npz"), payload["arrays"])
            write_trace(failure.with_suffix(".jsonl.gz"), payload["decisions"])
            write_json(failure.with_suffix(".json"), {"id": identifier, "summary": payload["summary"],
                                                       "certificate": payload["certificate"]})
            raise
        segment_records.append({"id": identifier, "scientific": record["scientific"], **verified})
        write_json(out / "progress.json", {"phase": "worker", "variant": variant, "world_id": world_id,
                                          "last_checked_segment": identifier, "model_segments": len(segment_records)})
        add_timing("segment_check_and_certificate", begin)

    def branch_sink(identifier, payload):
        begin = _clock()
        index = len(branch_records)
        if identifier in branch_ids or index >= len(reference.catalog["model_branches"]):
            raise ValueError("duplicate or unexpected complete branch")
        branch_ids.add(identifier)
        path = (root / "models" / _identifier(identifier)).with_suffix(".npz")
        trace = path.with_suffix(".jsonl.gz")
        write_arrays(path, payload["arrays"])
        write_trace(trace, payload["decisions"])
        branch_records.append({"id": identifier, "raw": artifact(path, out), "decisions": artifact(trace, out),
                               "summary": json_record(payload["summary"]), "scientific": payload_binding(payload)})
        if reference.catalog["model_branches"][index]["id"] != identifier:
            raise ValueError("complete branch emission order differs")
        same_payload(payload, reference.branch(identifier), f"{key}/branch/{identifier}")
        add_timing("branch_check_and_output", begin)

    def candidate_sink(identifier, rows):
        begin = _clock()
        index = len(bank_records)
        if identifier in bank_ids or index >= len(reference.catalog["candidate_banks"]):
            raise ValueError("duplicate or unexpected stationary bank")
        bank_ids.add(identifier)
        path = (root / "banks" / _identifier(identifier)).with_suffix(".npy")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            np.save(stream, rows, allow_pickle=False)
        bank_records.append({"id": identifier, "raw": artifact(path, out)})
        if reference.catalog["candidate_banks"][index]["id"] != identifier:
            raise ValueError("stationary bank order differs")
        same_array(rows, reference.bank(identifier), f"{key}/bank/{identifier}")
        add_timing("bank_check_and_output", begin)

    policy = TemporalProgram(arm, branch_sink=branch_sink, candidate_sink=candidate_sink,
                             reuse=reuse, segment_sink=segment_sink)
    old_mask, complete, error = 255, False, None
    try:
        for t in range(500):
            begin = _clock()
            command, new_mask, decision = policy.select(
                t, reference.native["states"][t].copy() if t % 10 == 0 else None, old_mask)
            add_timing("controller_including_callbacks", begin)
            if t in (40, 120):
                add_timing("selection_including_callbacks", begin)
            commands.append(np.asarray(command).copy())
            masks.append(int(new_mask))
            decisions.append(deepcopy(decision))
            # Save the failed decision in the final partial output, then stop.
            try:
                same_array(command, reference.native["actions"][t], f"{key}/actual command/{t}")
            except BaseException:
                # Preserve the failed dtype/bits before the complete-command
                # container's fixed float32 conversion in the finally block.
                write_arrays(root / "first-mismatch" / f"command_t{t}.npz",
                             {"actual": np.asarray(command), "expected": reference.native["actions"][t]})
                raise
            same_record(decision, reference.decisions[t], f"{key}/actual decision/{t}")
            if new_mask != int(reference.native["mask"][t]) or (t % 10 and new_mask != old_mask):
                raise ValueError(f"actual mask/hold mismatch: {key}/{t}")
            _add_trace(decision, counts)
            for kind in KINDS:
                calls[kind] += int(kind in decision)
            predictions += 216 * int("motion" in decision)
            old_mask = int(new_mask)
        if (len(branch_records) != len(reference.catalog["model_branches"])
                or len(bank_records) != len(reference.catalog["candidate_banks"])
                or policy.controller.next_t != 500):
            raise ValueError("complete controller/model/bank coverage differs")
        for name in ("plans", "selections", "banks"):
            same_record(json_record(getattr(policy, name)), reference.catalog[name], f"{key}/{name}")
        for name, actual in (("native_candidate_counts", counts), ("calls", calls),
                             ("position_predictions", predictions)):
            same_record(actual, reference.row[name], f"{key}/{name}")
        complete = True
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        certificate_stream.close()
        certificate_raw.close()
        command_path, decision_path = root / "commands.npz", root / "decisions.jsonl.gz"
        write_arrays(command_path, {"actions": np.asarray(commands, dtype=np.float32).reshape(-1, 8, 3),
                                    "masks": np.asarray(masks, dtype=np.int64)})
        write_trace(decision_path, decisions)
        final_history = {"next_t": int(policy.controller.next_t), "n_uavs": 8, "mask": int(old_mask)}
        for name in ("positions", "users", "commands"):
            value = getattr(policy.controller, name)
            final_history[name] = None if value is None else encode_array(value)
        catalog = {"plans": json_record(policy.plans), "selections": json_record(policy.selections),
                   "banks": json_record(policy.banks), "model_branches": branch_records,
                   "candidate_banks": bank_records}
        catalog_path = root / "evidence.json.gz"
        write_catalog(catalog_path, catalog)
        row = {"variant": variant, "arm": arm, "reuse": reuse, "world_id": world_id,
               "steps": len(decisions), "complete": complete, "new_native_steps": 0,
               "native_candidate_counts": counts, "calls": calls, "position_predictions": predictions,
               "logical_costs": deepcopy(reference.row["costs"]), "segments": segment_records,
               "logical_cost_scope": "original full-history work; completed work only when complete=true",
               "commands": artifact(command_path, out), "decisions": artifact(decision_path, out),
               "evidence_catalog": artifact(catalog_path, out), "certificates": artifact(certificate_path, out),
               "final_history": final_history, "original_native": deepcopy(reference.row["raw"]),
               "original_metrics": deepcopy(reference.row["metrics"]), "error": error,
               "input_loading_timing": input_timing, "timing_buckets": buckets,
               "timing_scope": "complete input/replay/scientific outputs/hash/certificate work; callback buckets overlap controller",
               "context_before": context_before, "context_after": execution_context()}
        # This write is inside the measured variant. The enclosing writer's
        # subsequent append/summary updates remain separately paid common work.
        write_json(out / "histories" / f"{key}.json", row)
        # Release cyclic selector/callback references within its timing scope.
        del policy
        gc.collect()
        row["timing"] = _elapsed(mark)
        write_json(out / "histories" / f"{key}.json", row)
        if not complete:
            write_json(out / "first-failure.json", row)
    return row


def run_study(out, launch_sha, admission, records_root, bulk_root, entry_mark=None):
    mark = _clock() if entry_mark is None else entry_mark
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in ("summary.json", "config.json", "raw", "certificates", "reading.json")):
        raise FileExistsError("existing B08 attempt; no implicit replay or retry")
    summary = {"launch_sha": launch_sha, "status": "input_verification", "worker_status": "incomplete",
               "histories": [], "new_native_steps": 0, "new_worlds": 0, "new_fits": 0,
               "updates": 0, "new_training_targets": 0, "independent_reader_model_queries": 0}
    write_json(out / "summary.json", summary)
    try:
        verification_mark = _clock()
        inputs = OriginalInputs(records_root, bulk_root)
        config = dict(fixed_config(inputs), launch_sha=launch_sha,
                      admission_command_sha256=admission["command_sha256"])
        write_json(out / "config.json", config)
        summary["config_artifact"] = artifact(out / "config.json", out)
        summary["common_input_verification_timing"] = _elapsed(verification_mark)
        summary["status"] = "worker"
        summary["context_before"] = execution_context()
        write_json(out / "summary.json", summary)
        for index, world_id in enumerate(WORLD_IDS):
            for offset in range(4):
                variant = VARIANTS[(index + offset) % 4]
                summary["current_history"] = dict(variant=variant, world_id=world_id)
                write_json(out / "summary.json", summary)
                row = replay_history(variant, world_id, out, inputs)
                summary["histories"].append(row)
                write_json(out / "summary.json", summary)
                arm = row["arm"]
                paired = [item for item in summary["histories"]
                          if item["arm"] == arm and item["world_id"] == world_id]
                if len(paired) == 2:
                    same_record(paired[0]["final_history"], paired[1]["final_history"],
                                f"first available {arm}/{world_id} terminal-history pair")
                print(json.dumps({"complete_controller_histories": len(summary["histories"]),
                                  "world_id": world_id, "variant": variant,
                                  "cpu_seconds": row["timing"]["cpu_seconds"]}), flush=True)
        totals = {name: sum(row["logical_costs"][name] for row in summary["histories"])
                  for name in LOGICAL_COSTS}
        same_record(totals, LOGICAL_COSTS, "complete selected logical work")
        if len(summary["histories"]) != 64 or sum(row["steps"] for row in summary["histories"]) != 32000:
            raise ValueError("complete selected controller panel differs")
        same_record(source_bindings(inputs.config["source_bindings"]), config["source_bindings"],
                    "source unchanged after complete worker")
        summary.update(worker_status="complete", status="collected", logical_costs=totals,
                       worker_timing=_elapsed(mark), context_after_worker=execution_context())
        write_json(out / "summary.json", summary)
        from .reader import read_run
        read_run(out)
        summary["reading"] = artifact(out / "reading.json", out)
        summary["status"] = "complete"
        summary["total_timing"] = dict(_elapsed(mark), process_resources=resources())
        write_json(out / "summary.json", summary)
        return summary
    except BaseException as exc:
        summary["failure_stage"] = summary["status"]
        summary.update(status="failed", error=f"{type(exc).__name__}: {exc}",
                       failed_timing=dict(_elapsed(mark), process_resources=resources()))
        write_json(out / "summary.json", summary)
        raise

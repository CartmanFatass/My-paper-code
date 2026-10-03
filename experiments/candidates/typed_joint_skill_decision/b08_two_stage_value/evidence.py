"""One-copy streamed evidence and bounded accounting for the fixed B08 study."""
from __future__ import annotations

from copy import deepcopy
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import time

import numpy as np

from . import contract as c


def json_value(value):
    return json.loads(c.encoded(value))


def write_json(path, value, *, replace=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = c.encoded(value) + b"\n"
    if not replace:
        with path.open("xb") as stream:
            stream.write(data)
    else:
        temporary = path.with_name(path.name + ".partial")
        with temporary.open("wb") as stream:
            stream.write(data)
        temporary.replace(path)


def write_gzip(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as stream:
            stream.write(c.encoded(value) + b"\n")


def read_gzip(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def write_arrays(path, arrays):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)


def load_arrays(path):
    with np.load(path, allow_pickle=False) as source:
        return {key: source[key] for key in source.files}


def exact(a, b, label):
    a, b = np.asarray(a), np.asarray(b)
    if a.dtype.str != b.dtype.str or a.shape != b.shape or a.tobytes(order="C") != b.tobytes(order="C"):
        raise ValueError(f"array identity differs: {label}")


def same_record(a, b, label):
    if c.encoded(a) != c.encoded(b):
        raise ValueError(f"record identity differs: {label}")


def array_binding(value):
    a = np.asarray(value)
    return {"dtype": a.dtype.str, "shape": list(a.shape),
            "sha256": hashlib.sha256(a.tobytes(order="C")).hexdigest()}


def payload_binding(value):
    return {"arrays": {key: array_binding(a) for key, a in sorted(value["arrays"].items())},
            "summary_sha256": c.digest(value["summary"]), "decisions_sha256": c.digest(value["decisions"])}


def checked_path(root, record):
    root = Path(root).resolve()
    rel = Path(record["path"])
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("absolute or traversing artifact path")
    path = (root / rel).resolve()
    if not path.is_relative_to(root) or c.binding(path, root) != record:
        raise ValueError(f"artifact bytes differ: {rel}")
    return path


def resources():
    own, child = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"self_cpu_seconds": own.ru_utime + own.ru_stime,
            "finished_children_cpu_seconds": child.ru_utime + child.ru_stime,
            "peak_rss_kib_process": own.ru_maxrss,
            "finished_children_max_rss_kib": child.ru_maxrss,
            "scope": "process lifetime; completed children separately; RSS maxima are not simultaneous"}


def allocated_bytes(path):
    path = Path(path)
    if not path.exists():
        return 0
    seen = set()
    total = 0
    for parent, dirs, files in os.walk(path, followlinks=False):
        for name in (".", *dirs, *files):
            target = Path(parent) / name
            stat = target.lstat()
            key = (stat.st_dev, stat.st_ino)
            if key not in seen:
                seen.add(key)
                total += stat.st_blocks * 512
    return total


class Budget:
    """Global result-chain limits; audit children receive the remaining CPU."""
    def __init__(self, out, source_root, *, wall_started=None, cpu_offset=0.0, progress_name="progress.json"):
        self.out, self.source_root = Path(out), Path(source_root)
        self.wall_started = time.monotonic() if wall_started is None else float(wall_started)
        self.cpu_offset = float(cpu_offset)
        if Path(progress_name).name != progress_name:
            raise ValueError("budget progress name must be a basename")
        self.progress_path = self.out / progress_name
        self.last_disk_clock = -float("inf")
        self.source_allocated = allocated_bytes(self.source_root)
        self.disk_bytes = self.source_allocated
        self.stage = "initializing"
        self.case = None
        self.progress = {}

    def elapsed_cpu(self):
        r = resources()
        return self.cpu_offset + r["self_cpu_seconds"] + r["finished_children_cpu_seconds"]

    def check(self, *, force_disk=False, progress=None):
        if progress is not None:
            self.progress.update(progress)
        now, cpu = time.monotonic(), self.elapsed_cpu()
        if force_disk or now - self.last_disk_clock >= 30:
            self.disk_bytes = self.source_allocated + allocated_bytes(self.out)
            self.last_disk_clock = now
        row = {"stage": self.stage, "case": self.case, "cpu_seconds": cpu,
               "wall_seconds": now - self.wall_started, "normal_allocated_bytes": self.disk_bytes,
               "resources": resources(), **self.progress}
        write_json(self.progress_path, row, replace=True)
        if cpu >= c.CPU_LIMIT_SECONDS or row["wall_seconds"] >= c.WALL_LIMIT_SECONDS or self.disk_bytes >= c.DISK_LIMIT_BYTES:
            raise RuntimeError("fixed result-chain CPU/wall/normal-allocation stop reached")
        return row


def identifier_path(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", identifier):
        raise ValueError("invalid evidence identifier")
    return Path(*identifier.split("/"))


def menu_record(*, start_t, report, commands, history, mask, bank, plans):
    """Lawful pre-model inputs only; no candidate rows duplicated here."""
    from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse.segment import encode_array
    return {"start_t": int(start_t), "report": encode_array(report), "commands": encode_array(commands),
            "history": {"n_uavs": history.n_uavs, "next_t": history.next_t,
                        "positions": encode_array(history.positions), "users": encode_array(history.users),
                        "commands": encode_array(history.commands)}, "mask": int(mask),
            "bank": json_value({key: value for key, value in bank.items() if key != "candidate_rows"}),
            "plans": json_value(plans)}


def decode_array(record):
    a = np.frombuffer(bytes.fromhex(record["hex"]), dtype=np.dtype(record["dtype"])).copy()
    return a.reshape(record["shape"])


class Collector:
    """Every segment array is saved once; complete outer branches reference parts."""
    def __init__(self, out, key, budget):
        self.out, self.budget = Path(out), budget
        self.root = self.out / "raw" / key
        self.root.mkdir(parents=True, exist_ok=False)
        self.segments, self.branches, self.banks, self.menus, self.queries = {}, [], [], [], []
        self.io_cpu = 0.0

    def _path(self, group, identifier, suffix):
        path = self.root / group / identifier_path(identifier)
        return path.with_suffix(suffix)

    def segment_sink(self, identifier, result):
        mark = time.process_time()
        if identifier in self.segments:
            raise ValueError("duplicate paid model segment")
        raw = self._path("segments", identifier, ".npz")
        trace = raw.with_suffix(".json.gz")
        write_arrays(raw, result["arrays"])
        write_gzip(trace, result["decisions"])
        record = {"id": identifier, "raw": c.binding(raw, self.out), "decisions": c.binding(trace, self.out),
                  "summary": json_value(result["summary"]), "certificate": json_value(result["certificate"]),
                  "scientific": payload_binding(result)}
        self.segments[identifier] = record
        write_json(raw.with_suffix(".record.json"), record)
        self.io_cpu += time.process_time() - mark
        self.budget.check(progress={"completed_case_segments": len(self.segments)})

    def branch_sink(self, identifier, result):
        mark = time.process_time()
        if any(row["id"] == identifier for row in self.branches):
            raise ValueError("duplicate complete model branch")
        if identifier.endswith("/outer"):
            parts = [identifier[:-5] + "prefix", identifier[:-5] + "suffix"]
        else:
            parts = [identifier]
        if any(part not in self.segments for part in parts):
            raise ValueError("branch lacks its completed unique segment evidence")
        record = {"id": identifier, "segments": parts, "summary": json_value(result["summary"]),
                  "scientific": payload_binding(result)}
        self.branches.append(record)
        write_json(self._path("branches", identifier, ".json"), record)
        self.io_cpu += time.process_time() - mark

    def candidate_sink(self, identifier, rows):
        mark = time.process_time()
        if any(row["id"] == identifier for row in self.banks):
            raise ValueError("duplicate paid stationary bank")
        path = self._path("banks", identifier, ".npy")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            np.save(stream, rows, allow_pickle=False)
        self.banks.append({"id": identifier, "raw": c.binding(path, self.out)})
        self.io_cpu += time.process_time() - mark

    def menu_sink(self, **values):
        mark = time.process_time()
        record = menu_record(**values)
        if any(row["start_t"] == record["start_t"] for row in self.menus):
            raise ValueError("duplicate actual menu callback")
        self.menus.append(record)
        write_gzip(self.root / f"menu-{record['start_t']}.json.gz", record)
        self.io_cpu += time.process_time() - mark

    def catalog(self, policy):
        return {"plans": json_value(policy.plans), "selections": json_value(policy.selections),
                "banks": json_value(policy.banks), "model_branches": self.branches,
                "candidate_banks": self.banks, "segments": list(self.segments.values()),
                "menus": self.menus, "queries": self.queries}


def load_segment(out, record):
    value = {"arrays": load_arrays(checked_path(out, record["raw"])),
             "decisions": read_gzip(checked_path(out, record["decisions"])),
             "summary": deepcopy(record["summary"])}
    same_record(payload_binding(value), record["scientific"], "saved segment payload")
    return value


def load_branch(out, catalog, record):
    segments = {r["id"]: r for r in catalog["segments"]}
    parts = [load_segment(out, segments[key]) for key in record["segments"]]
    if len(parts) == 1:
        value = parts[0]
    elif len(parts) == 2:
        left, right = parts
        exact(left["arrays"]["positions"][-1], right["arrays"]["positions"][0], "outer physical concatenation")
        arrays = {key: np.concatenate((left["arrays"][key], right["arrays"][key][1:]
                                       if key in ("positions", "controller_estimates") else right["arrays"][key]), axis=0)
                  for key in left["arrays"]}
        decisions = deepcopy(left["decisions"] + right["decisions"])
        decisions[len(left["decisions"])]["predicted_temporal_selection"] = deepcopy(record["summary"]["inner_selection"])
        value = {"arrays": arrays, "decisions": decisions}
    else:
        raise ValueError("unexpected complete-branch segment count")
    value["summary"] = deepcopy(record["summary"])
    same_record(payload_binding(value), record["scientific"], "saved complete-branch payload")
    return value


def case_costs(catalog, native_counts):
    from experiments.candidates.uav_fleet_transmission.b02.controller import KINDS
    native = sum(native_counts[k]["requested_candidates"] for k in KINDS if k != "option")
    bank_requests = sum(bank["counts"]["requested_candidates"] for bank in catalog["banks"].values())
    works = [segment["certificate"]["reuse"] for segment in catalog["segments"]]
    return {"native_controller_requests": native, "stationary_bank_requests": bank_requests,
            "logical_model_requests": sum(w["logical_requested_candidates"] for w in works),
            "actual_model_requests": sum(w["actual_requested_candidates"] for w in works),
            "logical_worker_requests": native + bank_requests + sum(w["logical_requested_candidates"] for w in works),
            "actual_worker_requests": native + bank_requests + sum(w["actual_requested_candidates"] for w in works),
            "logical_model_ticks": sum(s["certificate"]["end_t"] - s["certificate"]["start_t"] for s in catalog["segments"]),
            "computed_model_ticks": sum(w["computed_ticks"] for w in works),
            "reused_model_ticks": sum(w["reused_ticks"] for w in works),
            "stationary_banks": len(catalog["banks"]),
            "stationary_candidate_rows": sum(bank["candidate_count"] for bank in catalog["banks"].values()),
            "candidate_transit_ticks": sum(bank["counts"]["model_ticks"] for bank in catalog["banks"].values()),
            "model_segments": len(works), "complete_branches": len(catalog["model_branches"])}

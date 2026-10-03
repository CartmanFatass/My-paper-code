"""Stream unique model evidence and compact reconstructible segment copies."""
from copy import deepcopy
import gzip
import json
from pathlib import Path

import numpy as np

from experiments.candidates.uav_fleet_transmission.b04.study import identifier_path
from .inputs import (artifact, checked_file, json_record, load_arrays, load_trace,
                     payload_binding, same_payload, same_record)


def write_catalog(path, value):
    partial = path.with_suffix(path.suffix + ".partial")
    with partial.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as stream:
            stream.write(json.dumps(value, sort_keys=True, allow_nan=False).encode() + b"\n")
    partial.replace(path)


def write_trace(path, rows):
    with path.open("xb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as stream:
            for row in rows:
                stream.write(json.dumps(row, sort_keys=True, allow_nan=False).encode() + b"\n")


def save_payload(out, base, payload):
    path, trace = base.with_suffix(".npz"), base.with_suffix(".jsonl.gz")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        np.savez_compressed(stream, **payload["arrays"])
    write_trace(trace, payload["decisions"])
    return {"raw": artifact(path, out), "decisions": artifact(trace, out),
            "summary": json_record(payload["summary"])}


def load_payload(out, record):
    return {"arrays": load_arrays(checked_file(out, record["raw"])),
            "decisions": load_trace(checked_file(out, record["decisions"])), "summary": record["summary"]}


def project_segment(payload, start, end, summary, kind):
    """Recover a saved prefix/suffix from its concatenated complete outer branch."""
    outer_start = payload["summary"]["start_t"]
    left, count = start - outer_start, end - start
    if left < 0 or count <= 0 or left + count > len(payload["decisions"]):
        raise ValueError("invalid retained outer-segment interval")
    source = payload["arrays"]
    report_rows = (source["report_times"] >= start) & (source["report_times"] < end)
    arrays = {}
    for name, values in source.items():
        if name in ("positions", "controller_estimates"):
            arrays[name] = values[left:left + count + 1].copy()
        elif name in ("reports", "report_times"):
            arrays[name] = values[report_rows].copy()
        else:
            arrays[name] = values[left:left + count].copy()
    decisions = deepcopy(payload["decisions"][left:left + count])
    if kind == "suffix":
        # concatenate's outer record adds this declaration after the segment sink.
        decisions[0].pop("predicted_temporal_selection", None)
    return {"arrays": arrays, "decisions": decisions, "summary": deepcopy(summary)}


def segment_payload(out, segment, branches):
    if "derived_from_model" not in segment:
        return load_payload(out, segment)
    parent = branches[segment["derived_from_model"]]
    return project_segment(load_payload(out, parent), segment["certificate"]["start_t"],
                           segment["certificate"]["end_t"], segment["summary"], segment["kind"])


class EvidenceStore:
    def __init__(self, out, raw_dir, meter):
        self.out, self.raw_dir, self.meter = out, raw_dir, meter
        self.branches, self.banks, self.segments = [], [], []
        self.branch_ids, self.bank_ids, self.segment_ids = set(), set(), set()

    def segment_sink(self, identifier, result):
        if identifier in self.segment_ids:
            raise ValueError("duplicate model segment")
        self.segment_ids.add(identifier)
        kind = identifier.rsplit("/", 1)[-1]
        kind = kind if kind in ("prefix", "suffix") else "ordinary"
        record = dict(id=identifier, kind=kind, certificate=json_record(result["certificate"]),
                      scientific=payload_binding(result), **save_payload(
                          self.out, self.raw_dir / "segments" / identifier_path(identifier), result))
        self.segments.append(record)
        self.meter.check()

    def branch_sink(self, identifier, result):
        if identifier in self.branch_ids:
            raise ValueError("duplicate complete model branch")
        self.branch_ids.add(identifier)
        segment = next((s for s in self.segments if s["id"] == identifier), None)
        if segment is not None:
            binding = payload_binding(result)
            same_record(binding["arrays"], segment["scientific"]["arrays"], "shared segment/branch arrays")
            same_record(binding["decisions_sha256"], segment["scientific"]["decisions_sha256"],
                        "shared segment/branch decisions")
            row = {"raw": segment["raw"], "decisions": segment["decisions"],
                   "summary": json_record(result["summary"])}
        else:
            row = save_payload(self.out, self.raw_dir / "models" / identifier_path(identifier), result)
        self.branches.append(dict(id=identifier, **row))
        self.meter.check()

    def candidate_sink(self, identifier, rows):
        if identifier in self.bank_ids:
            raise ValueError("duplicate stationary bank")
        self.bank_ids.add(identifier)
        path = (self.raw_dir / "banks" / identifier_path(identifier)).with_suffix(".npy")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            np.save(stream, rows, allow_pickle=False)
        self.banks.append({"id": identifier, "raw": artifact(path, self.out)})
        self.meter.check()

    def catalog(self, policy):
        return {"plans": json_record(policy.plans), "selections": json_record(policy.selections),
                "banks": json_record(policy.banks), "model_branches": self.branches,
                "candidate_banks": self.banks, "segments": self.segments}


def compact_verified_segments(out, catalog_path, catalog, *, audit=None):
    """After the full reader, remove only payloads bit-recoverable from an outer."""
    audit = {} if audit is None else audit
    audit.update(deleted=[], allocated_file_bytes_removed=0, planned_deletions=[])
    branches = {row["id"]: row for row in catalog["model_branches"]}
    deletions = []
    for row in catalog["segments"]:
        if row["kind"] not in ("prefix", "suffix") or "derived_from_model" in row:
            continue
        outer_id = row["id"].rsplit("/", 1)[0] + "/outer"
        if outer_id not in branches:
            raise ValueError("complete read segment lacks its retained outer branch")
        projected = project_segment(load_payload(out, branches[outer_id]), row["certificate"]["start_t"],
                                    row["certificate"]["end_t"], row["summary"], row["kind"])
        same_payload(projected, load_payload(out, row), "lossless post-reader compaction")
        same_record(payload_binding(projected), row["scientific"], "retained segment digest")
        for field in ("raw", "decisions"):
            path = checked_file(out, row[field])
            if any(path == out / parent[field]["path"] for parent in branches.values()):
                raise ValueError("refusing to delete a live full-branch evidence path")
            deletions.append({"path": str(path), "allocated_bytes": path.stat().st_blocks * 512})
        row.pop("raw")
        row.pop("decisions")
        row["derived_from_model"] = outer_id
    # Publish replacement references before removing redundant files. A failure
    # leaves readable references and at worst explicitly listed unused copies.
    audit["planned_deletions"] = deletions
    write_catalog(catalog_path, catalog)
    audit["replacement_catalog_published"] = True
    for item in deletions:
        Path(item["path"]).unlink()
        audit["deleted"].append(item)
        audit["allocated_file_bytes_removed"] += item["allocated_bytes"]
    return audit

"""Read-only binding to the unique retained B01 endpoints and training witnesses."""

import hashlib
import json
from pathlib import Path

from experiments.candidates.uav_parent_adaptation.b01.model import read_checkpoint
from .protocol import (LINEAGES, PARENT_SOURCE, PARENT_SUMMARY_SHA256, TRAIN, HORIZON,
                       WITNESS_FIELDS, addresses)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_assets(root, *, summary_sha256=PARENT_SUMMARY_SHA256, train=TRAIN, horizon=HORIZON):
    """No constructors, random draws, writes or optimization; fixed bytes precede U."""
    root = Path(root).resolve()
    summary_path = root / "summary.json"
    if digest(summary_path) != summary_sha256:
        raise ValueError("retained B01 summary digest mismatch")
    summary = json.loads(summary_path.read_text())
    if (summary["object"] != "UAV-PARENT-ADAPTATION-B01" or summary["status"] != "COMPLETE"
            or summary["limits"] or summary["source_sha"] != PARENT_SOURCE):
        raise ValueError("retained B01 source or completion mismatch")
    cells = {(c["lineage"], c["stage"]): c for c in summary["fits"]}
    if set(cells) != {(l, s) for l in LINEAGES for s in ("C", "B", "K", "D")}:
        raise ValueError("retained B01 fixed fit set mismatch")
    checkpoints, witnesses, streams = {}, {}, {}
    for lineage in LINEAGES:
        checkpoints[lineage] = {}
        for program, stage in (("P", "B"), ("K", "K"), ("D", "D")):
            cell = cells[(lineage, stage)]
            if cell["status"] != "COMPLETE" or cell["limits"] or cell["launch_sha"] != PARENT_SOURCE:
                raise ValueError("retained cell is incomplete or has a different source")
            binding = cell["final_checkpoint"]
            if Path(binding["path"]).resolve() != root / str(lineage) / stage / "final.pt":
                raise ValueError("retained endpoint path mismatch")
            read_checkpoint(Path(binding["path"]).read_bytes(), binding, lineage=lineage,
                            stage=stage, endpoint="final", launch_sha=PARENT_SOURCE)
            checkpoints[lineage][program] = binding
            if program == "P":
                continue
            if binding["parent"] != checkpoints[lineage]["P"]:
                raise ValueError("retained adaptation belongs to another parent")
            stream = root / str(lineage) / stage / "episodes.jsonl"
            if digest(stream) != cell["episode_stream_sha256"]:
                raise ValueError("retained training stream digest mismatch")
            rows = [json.loads(row) for row in stream.read_text().splitlines()]
            if len(rows) != train:
                raise ValueError("retained training exposure mismatch")
            addr = addresses(lineage, "U", train=train)
            for e, row in enumerate(rows):
                if (row["lineage"] != lineage or row["arm"] != stage or row["phase"] != "train"
                        or row["episode"] != e or row["steps"] != horizon
                        or row["reset_seed"] != addr["scene_start"] + e
                        or row["channel_seed"] != addr["channel_start"] + e
                        or row["motion_seed"] != addr["motion"]):
                    raise ValueError("retained training address contract mismatch")
            current = [tuple(row[k] for k in WITNESS_FIELDS) for row in rows]
            if program == "K":
                witnesses[lineage] = current
            elif current != witnesses[lineage]:
                raise ValueError("retained K/D actual exogenous streams differ")
            streams[f"{lineage}/{stage}"] = dict(path=str(stream), bytes=stream.stat().st_size,
                                                sha256=cell["episode_stream_sha256"])
    return dict(checkpoints=checkpoints, witnesses=witnesses,
                identity=dict(root=str(root), source_sha=PARENT_SOURCE,
                              summary=dict(path=str(summary_path), bytes=summary_path.stat().st_size,
                                           sha256=summary_sha256), training_streams=streams))

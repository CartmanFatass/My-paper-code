"""Verify the complete declared old-bank manifest before model construction."""

import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from .contract import B_SHA, D_SHA, DATA_SHA, SUMMARY_SHA, FIELDS, require, sha256, verify_artifact


def load_inputs(manifest_path, manifest_sha, d_path, d_sha, b_path, b_sha):
    require(sha256(manifest_path) == manifest_sha, "input manifest digest")
    manifest = json.loads(Path(manifest_path).read_text())
    require(manifest.get("schema_version") == 1 and manifest.get("object") == "UAV-MESSAGE-CONTENT-B07-INPUTS",
            "input manifest schema")
    for key, path, digest, expected in (("parent_d", d_path, d_sha, D_SHA),
                                        ("parent_b", b_path, b_sha, B_SHA)):
        record = manifest[key]
        require(record["path"] == str(path) and digest == record["sha256"] == expected,
                "explicit checkpoint differs from manifest/selected parent")
        verify_artifact(record)
    data = manifest["teacher_data"]
    require(data["summary_sha256"] == SUMMARY_SHA and data["inventory_sha256"] == DATA_SHA,
            "selected teacher bank identity")
    require(len(data["episodes"]) == 32, "complete old32 required")
    digest, total, episodes = hashlib.sha256(), 0, []
    for e, record in enumerate(data["episodes"]):
        require(record["episode"] == e and record["split"] == ("fit" if e < 24 else "development"), "old split/order")
        path = verify_artifact(record)
        require(path.name == f"final_{e:02d}.npz", "old episode name")
        digest.update(f"{path.name}\0{record['bytes']}\0{record['sha256']}\n".encode())
        total += record["bytes"]
        row = record["original_row"]
        require((row["arm"], row["master"], row["phase"], row["episode"], row["steps"],
                 row["reset_seed"], row["channel_seed"], row["motion_seed"], row["raw_sha256"]) ==
                ("D", 19702, "final_eval", e, 256, 1970002000 + e, 1970007000 + e,
                 1970003000 + e, record["sha256"]), "original row binding")
        with np.load(path, allow_pickle=False) as archive:
            names = ("actor_input", "packet", "composed_mean", "sample_logp", "pre_tanh_motion",
                     "sender", "due", "good", "log_std", "records", "action")
            episode = {name: archive[name].copy() for name in names}
        validate_episode(episode)
        episodes.append(episode)
    require(digest.hexdigest() == DATA_SHA and total == data["total_bytes"] == 9061080,
            "old bank complete inventory")
    return manifest, episodes


def validate_episode(data):
    shapes = dict(actor_input=(256, 5, 186), packet=(256, 10), composed_mean=(256, 5, 3),
                  sample_logp=(256, 5), pre_tanh_motion=(256, 5, 3), log_std=(3,),
                  records=(256, 5, 5, 13), action=(256, 5, 3), sender=(256,), due=(256,), good=(256,))
    for name, shape in shapes.items():
        require(data[name].shape == shape and np.isfinite(data[name]).all(), f"old {name} shape/finite")
    for name in ("actor_input", "packet", "composed_mean", "sample_logp", "pre_tanh_motion", "log_std", "action", "records"):
        require(data[name].dtype == np.float32, f"old {name} FP32")
    require(np.array_equal(data["sender"], np.arange(256) % 5), "old RR")
    require(np.isin(data["good"], (0, 1)).all() and
            np.array_equal(data["due"], np.arange(256) + np.where(data["good"], 1, 5)), "old send delay")
    require(not data["packet"][:, [5, 7, 8, 9]].any() and not data["actor_input"][..., 171:].any(),
            "old known zeros")
    source = data["packet"][:, list(FIELDS)]
    require(((source >= 0) & (source <= 1)).all(), "old source range")
    require(not data["actor_input"][0, :, 104:108].any() and
            np.array_equal(data["actor_input"][1:, :, 104:107], data["action"][:-1]) and
            not data["actor_input"][..., 107].any(), "old previous-command binding")


def cache_addresses(data):
    """Pure causal send addresses; no policy execution and no source features added."""
    horizon = len(data["due"])
    addresses = np.zeros((horizon, 5, 5), dtype=np.int64)
    records = np.zeros((5, 5), dtype=np.int64)
    for t in range(horizon):
        for sent in np.flatnonzero(data["due"][:t] == t):
            sender = int(data["sender"][sent])
            records[np.arange(5) != sender, sender] = sent + 1
        addresses[t] = records
    return torch.from_numpy(addresses)

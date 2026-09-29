"""Fixed source/artifact binding without native environment construction."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.uav_persistent_service.b05 import binding


def _row(root, arm, length=4, *, changed_state=None):
    seed = binding.SEEDS[0]
    users = np.zeros((length+1, 30, 2))
    if changed_state is not None:
        users[changed_state, 0, 0] = 1
    ends = np.zeros((length, 2), dtype=bool)
    ends[-1, 0] = True
    path = root/f"{arm}.npz"
    np.savez(path, user_xy_m=users, rng_state_sha256_by_step=np.full(length+1, "a"*64),
             reward=np.zeros(length), ends=ends, initial_native_battery=np.ones(8))
    decisions = root/f"{arm}.json"
    decisions.write_text("{}")
    return {"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}", "actual_length": length,
            "effective_config": {"max_steps": 12000}, "initial_state_sha256": "b",
            "ground_bs_sha256": "c", "user_xy_trace_sha256": "d", "rng_state_stream_sha256": "e",
            "raw_path": path.name, "raw_sha256": binding.sha256_file(path),
            "raw_bytes": path.stat().st_size, "decisions_path": decisions.name,
            "decisions_sha256": binding.sha256_file(decisions), "control_root": str(root)}


def test_pair_requires_every_common_exogenous_state_and_initial_battery(tmp_path):
    control = _row(tmp_path, "R")
    candidate = _row(tmp_path, "S", 2)
    assert binding.verify_pair(tmp_path, candidate, control)["status"] == "verified"
    candidate = _row(tmp_path, "S", 2, changed_state=1)
    assert binding.verify_pair(tmp_path, candidate, control)["status"] == "failed"
    candidate = _row(tmp_path, "S")
    candidate["rng_state_stream_sha256"] = "different"
    assert binding.verify_pair(tmp_path, candidate, control)["status"] == "failed"


def test_manifest_hash_and_every_artifact_are_verified(tmp_path):
    artifact = tmp_path/"data.json"
    artifact.write_text("{}")
    manifest = {"launch_sha": "old", "storage_bytes": 2,
                "artifacts": {artifact.name: {"sha256": binding.sha256_file(artifact), "bytes": 2}}}
    path = tmp_path/"manifest.json"
    path.write_text(json.dumps(manifest))
    spec = {"manifest": binding.sha256_file(path), "source": "old", "artifacts": 1}
    assert binding.verify_original_manifest(tmp_path, spec) == manifest
    artifact.write_text("[]")
    with pytest.raises(ValueError, match="artifact missing or changed"):
        binding.verify_original_manifest(tmp_path, spec)
    spec["manifest"] = hashlib.sha256(b"not manifest").hexdigest()
    with pytest.raises(ValueError, match="manifest identity differs"):
        binding.verify_original_manifest(tmp_path, spec)


def test_frozen_dependencies_remain_byte_identical():
    repo = Path(__file__).resolve().parents[5]
    result = binding.bind_source(repo)
    assert result["file_count"] == 291
    assert result["source_map_sha256"] == "e9aca789906052070e7fea9ceda83b5f8593de17b3ad89a9928fae468ade8d9c"

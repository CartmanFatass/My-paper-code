import hashlib
import json

import numpy as np
import pytest

from experiments.candidates.uav_message_content.b07 import inputs
from experiments.candidates.uav_message_content.b07.contract import artifact


def synthetic_episode():
    shapes = dict(actor_input=(256, 5, 186), packet=(256, 10), composed_mean=(256, 5, 3),
                  sample_logp=(256, 5), pre_tanh_motion=(256, 5, 3), log_std=(3,),
                  records=(256, 5, 5, 13), action=(256, 5, 3))
    result = {key: np.zeros(shape, dtype=np.float32) for key, shape in shapes.items()}
    result.update(sender=np.arange(256) % 5, due=np.arange(256) + 1, good=np.ones(256, dtype=int))
    return result


def test_complete_synthetic_manifest_identities_and_frozen_split(tmp_path, monkeypatch):
    d, b = tmp_path / "D.pt", tmp_path / "B.pt"
    d.write_bytes(b"synthetic D; not a checkpoint")
    b.write_bytes(b"synthetic B; not a checkpoint")
    dr, br = artifact(d), artifact(b)
    monkeypatch.setattr(inputs, "D_SHA", dr["sha256"])
    monkeypatch.setattr(inputs, "B_SHA", br["sha256"])
    episodes, digest, total = [], hashlib.sha256(), 0
    raw = tmp_path / "raw"
    raw.mkdir()
    for e in range(32):
        path = raw / f"final_{e:02d}.npz"
        np.savez_compressed(path, **synthetic_episode())
        record = artifact(path)
        record.update(episode=e, split="fit" if e < 24 else "development",
                      original_row=dict(arm="D", master=19702, phase="final_eval", episode=e, steps=256,
                                        reset_seed=1970002000 + e, channel_seed=1970007000 + e,
                                        motion_seed=1970003000 + e, raw_sha256=record["sha256"]))
        digest.update(f"{path.name}\0{record['bytes']}\0{record['sha256']}\n".encode())
        total += record["bytes"]
        episodes.append(record)
    monkeypatch.setattr(inputs, "DATA_SHA", digest.hexdigest())
    # The synthetic bank cannot match the purchased bank's exact9061080-byte binding.
    manifest = dict(schema_version=1, object="UAV-MESSAGE-CONTENT-B07-INPUTS", parent_d=dr, parent_b=br,
                    teacher_data=dict(summary_sha256=inputs.SUMMARY_SHA, inventory_sha256=digest.hexdigest(),
                                      total_bytes=total, episodes=episodes))
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    # Complete enumeration reaches the exact real-bank total-byte binding after all32 hashes.
    with pytest.raises(ValueError, match="complete inventory"):
        inputs.load_inputs(path, artifact(path)["sha256"], d, dr["sha256"], b, br["sha256"])
    manifest["teacher_data"]["episodes"][24]["split"] = "fit"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="old split/order"):
        inputs.load_inputs(path, artifact(path)["sha256"], d, dr["sha256"], b, br["sha256"])
    with pytest.raises(ValueError, match="manifest digest"):
        inputs.load_inputs(path, "wrong", d, dr["sha256"], b, br["sha256"])


@pytest.mark.parametrize("field,mutation", [
    ("packet", lambda a: a.__setitem__((0, 5), 1.)),
    ("actor_input", lambda a: a.__setitem__((0, 0, 171), 1.)),
    ("composed_mean", lambda a: a.__setitem__((0, 0, 0), np.nan)),
    ("sender", lambda a: a.__setitem__(0, 1)),
    ("due", lambda a: a.__setitem__(0, 5)),
])
def test_strict_old_contract_malformed(field, mutation):
    episode = synthetic_episode()
    inputs.validate_episode(episode)
    mutation(episode[field])
    with pytest.raises(ValueError):
        inputs.validate_episode(episode)

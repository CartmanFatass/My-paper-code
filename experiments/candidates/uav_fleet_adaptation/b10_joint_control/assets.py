"""Exact retained P0 and HIDDEN inputs, verified before any model construction."""
from pathlib import Path

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_digest
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.assets import checked_path
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.fit import _parameters
from experiments.candidates.uav_local_history.b01.study import file_identity
from .contract import ASSET_BINDINGS, FROZEN


def load_assets(paths):
    if set(paths) != {"P0", "HIDDEN"}:
        raise ValueError("exact original P0 and HIDDEN files are required")
    identities = {}
    for name, path in paths.items():
        identity, binding = file_identity(Path(path)), ASSET_BINDINGS[name]
        if any(identity[key] != binding[key] for key in ("bytes", "sha256")):
            raise ValueError("original " + name + " artifact identity changed")
        identities[name] = dict(identity, canonical_path=binding["path"], canonical_node="wsl_4070",
                                source_launch_sha=binding["launch_sha"])
    binding = ASSET_BINDINGS["P0"]
    saved = torch.load(paths["P0"], map_location="cpu", weights_only=True)
    if (saved.get("endpoint") != "S" or saved.get("launch_sha") != binding["launch_sha"]
            or saved.get("architecture") != [114, 128, 128, 27] or saved.get("activation") != "relu"
            or saved.get("dtype") != "float32" or saved.get("optimizer_steps") != 8000
            or saved.get("state_sha256") != binding["state_sha256"]
            or state_digest(saved["state_dict"]) != binding["state_sha256"]):
        raise ValueError("original P0 tensor/training identity changed")
    with np.load(paths["HIDDEN"], allow_pickle=False) as loaded:
        gate = {key: loaded[key].copy() for key in loaded.files}
    _parameters(gate, 253)
    actor = make_student(FROZEN.actor_constructor_seed)
    actor.load_state_dict(saved["state_dict"], strict=True)
    actor.eval().requires_grad_(False)
    if any(value.dtype != torch.float32 or not torch.isfinite(value).all() for value in actor.state_dict().values()):
        raise ValueError("finite original FP32 P0 parameters required")
    identities["P0"]["state_sha256"] = state_digest(actor.state_dict())
    return actor, gate, identities

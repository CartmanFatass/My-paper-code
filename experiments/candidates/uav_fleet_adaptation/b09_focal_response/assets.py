"""Exact original P0/P1 files and immutable states, never checkpoint search."""
from pathlib import Path

import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_digest
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.assets import checked_path
from experiments.candidates.uav_local_history.b01.study import file_identity
from .contract import ASSET_BINDINGS, FROZEN


def load_parents(paths):
    if set(paths) != {"P0", "P1"}:
        raise ValueError("both exact retained parents required")
    # Presence/file verification for BOTH precedes even a constructor, let alone a query.
    identities = {}
    for name, path in paths.items():
        identity = file_identity(Path(path))
        binding = ASSET_BINDINGS[name]
        if any(identity[key] != binding[key] for key in ("bytes", "sha256")):
            raise ValueError("original " + name + " file differs from frozen artifact")
        identities[name] = dict(identity, canonical_path=binding["path"], canonical_node="wsl_4070",
                                source_launch_sha=binding["launch_sha"], state_sha256=binding["state_sha256"])
    actors = {}
    for name, path in paths.items():
        binding = ASSET_BINDINGS[name]
        saved = torch.load(path, map_location="cpu", weights_only=True)
        if (saved.get("endpoint") != "S" or saved.get("launch_sha") != binding["launch_sha"]
                or saved.get("architecture") != [114, 128, 128, 27] or saved.get("activation") != "relu"
                or saved.get("dtype") != "float32" or saved.get("optimizer_steps") != 8000
                or saved.get("state_sha256") != binding["state_sha256"]
                or state_digest(saved["state_dict"]) != binding["state_sha256"]):
            raise ValueError("original " + name + " checkpoint contract changed")
        actor = make_student(FROZEN.actor_constructor_seed)
        actor.load_state_dict(saved["state_dict"], strict=True)
        actor.eval().requires_grad_(False)
        if state_digest(actor.state_dict()) != binding["state_sha256"] or any(
                value.dtype != torch.float32 or not torch.isfinite(value).all() for value in actor.state_dict().values()):
            raise ValueError("invalid original FP32 Student")
        actors[name] = actor
    return actors, identities

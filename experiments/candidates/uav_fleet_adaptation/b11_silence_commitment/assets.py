"""Exact original P0 artifact/metadata/tensors, before any Student construction."""
from pathlib import Path
import torch
from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_digest
from experiments.candidates.uav_local_history.b01.study import file_identity
from .contract import ASSET_BINDINGS, FROZEN


def load_assets(paths):
    if set(paths) != {"P0"}:
        raise ValueError("exact original P0 only is required")
    binding = ASSET_BINDINGS["P0"]
    identity = file_identity(Path(paths["P0"]))
    if any(identity[key] != binding[key] for key in ("bytes", "sha256")):
        raise ValueError("original P0 artifact identity changed")
    saved = torch.load(paths["P0"], map_location="cpu", weights_only=True)
    if (saved.get("endpoint") != "S" or saved.get("launch_sha") != binding["launch_sha"]
        or saved.get("architecture") != [114,128,128,27] or saved.get("activation") != "relu"
        or saved.get("dtype") != "float32" or saved.get("optimizer_steps") != 8000
        or saved.get("state_sha256") != binding["state_sha256"]
        or state_digest(saved["state_dict"]) != binding["state_sha256"]):
        raise ValueError("original P0 tensor/training identity changed")
    actor = make_student(FROZEN.actor_constructor_seed)
    actor.load_state_dict(saved["state_dict"], strict=True)
    actor.eval().requires_grad_(False)
    if sum(value.numel() for value in actor.parameters()) != 34715 or any(
        value.dtype != torch.float32 or not torch.isfinite(value).all() for value in actor.state_dict().values()):
        raise ValueError("34715 finite original FP32 parameters required")
    identity.update(canonical_path=binding["path"], canonical_node="wsl_4070",
        source_launch_sha=binding["launch_sha"], state_sha256=state_digest(actor.state_dict()))
    return actor, {"P0": identity}

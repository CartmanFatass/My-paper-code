"""Immutable original students; the only new checkpoints are the small heads."""
from pathlib import Path
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_digest
from experiments.candidates.uav_fleet_adaptation.b04_native_development.assets import verify_initial_assets
from experiments.candidates.uav_local_history.b01.study import file_identity
from .contract import FROZEN, INITIAL_ASSETS


def load_initial_assets(protocol=FROZEN, *, bindings=None, permit_fixture=False):
    bindings = INITIAL_ASSETS if bindings is None else tuple(bindings)
    if len(bindings) != 2:
        raise ValueError("both original students are required")
    if not permit_fixture and (protocol != FROZEN or bindings != INITIAL_ASSETS):
        raise ValueError("production asset substitution is forbidden")
    if permit_fixture and protocol == FROZEN:
        raise ValueError("fixture cannot use production protocol")
    models, records = [], []
    for lineage, binding in enumerate(bindings):
        path = Path(binding["path"]).resolve()
        actual = file_identity(path)
        if any(actual[key] != binding[key] for key in ("sha256", "bytes")):
            raise ValueError("immutable initial asset file identity changed")
        saved = torch.load(path, map_location="cpu", weights_only=True)
        if (saved.get("endpoint") != "S" or saved.get("launch_sha") != binding["launch_sha"]
                or saved.get("architecture") != [114, 128, 128, 27] or saved.get("activation") != "relu"
                or saved.get("dtype") != "float32" or saved.get("optimizer_steps") != 8000):
            raise ValueError("initial source/architecture/selection history changed")
        state = saved["state_dict"]
        if (any(x.dtype != torch.float32 or not torch.isfinite(x).all() for x in state.values())
                or state_digest(state) != binding["state_sha256"] or saved["state_sha256"] != binding["state_sha256"]):
            raise ValueError("initial tensor identity changed")
        model = make_student(protocol.actor_constructor_seeds[lineage]).eval()
        model.load_state_dict(state, strict=True)
        model.requires_grad_(False)
        if state_digest(model.state_dict()) != binding["state_sha256"]:
            raise AssertionError("loading changed the original student")
        models.append(model)
        records.append({**binding, "path": str(path), "lineage": lineage,
                        "inherited_optimizer_loaded_for_training": False,
                        "architecture": [114, 128, 128, 27], "activation": "relu", "dtype": "float32"})
    return models, records

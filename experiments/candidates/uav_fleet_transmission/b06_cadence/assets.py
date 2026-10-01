"""Exact local copies of immutable S assets; paid calibration stays pinned in Git."""
from pathlib import Path
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_digest
from experiments.candidates.uav_local_history.b01.study import file_identity
from experiments.candidates.uav_fleet_transmission.b05_score_sampling.assets import (
    verify_assets, verify_calibration,
)
from .contract import FROZEN, LOCAL_ASSETS


def load_assets(protocol=FROZEN):
    if protocol != FROZEN:
        raise ValueError("production asset substitution forbidden")
    models, records = [], []
    for lineage, record in enumerate(LOCAL_ASSETS):
        identity = file_identity(record["path"])
        if any(identity[k] != record[k] for k in ("bytes", "sha256")):
            raise ValueError("original S file identity changed")
        payload = torch.load(record["path"], map_location="cpu", weights_only=True)
        if (payload.get("endpoint") != "S" or payload.get("launch_sha") != record["launch_sha"]
                or payload.get("architecture") != [114, 128, 128, 27] or payload.get("activation") != "relu"
                or payload.get("dtype") != "float32" or payload.get("optimizer_steps") != 8000):
            raise ValueError("original S endpoint/architecture binding changed")
        state = payload["state_dict"]
        if (not state or state_digest(state) != record["state_sha256"]
                or payload["state_sha256"] != record["state_sha256"]
                or any(x.dtype != torch.float32 or not torch.isfinite(x).all() for x in state.values())):
            raise ValueError("original S tensor identity changed")
        model = make_student(protocol.actor_constructor_seeds[lineage]).eval()
        model.load_state_dict(state, strict=True)
        model.requires_grad_(False)
        models.append(model)
        records.append(dict(record, path=str(Path(record["path"]).resolve()), lineage=lineage,
                            inherited_optimizer_loaded=False, parameters=34715))
    verify_assets(models, records)
    return models, records

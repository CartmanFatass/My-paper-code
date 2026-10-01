"""Read original fixed S tensors and paid B* choices without training state."""
import hashlib
import json
from pathlib import Path
import subprocess

import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_digest
from experiments.candidates.uav_local_history.b01.study import file_identity
from .contract import CALIBRATION, CANONICAL_ASSETS, FROZEN


def verify_calibration(repo):
    # A launcher snapshot may deliberately omit tracked bulk from its working tree.
    blob = subprocess.check_output(
        ["git", "-C", str(repo), "show", CALIBRATION["evidence_commit"] + ":" + CALIBRATION["reading_path"]],
        stderr=subprocess.PIPE, timeout=30)
    if hashlib.sha256(blob).hexdigest() != CALIBRATION["reading_sha256"]:
        raise ValueError("paid calibration blob identity changed")
    reading = json.loads(blob)
    if (reading["status"] != "VERIFIED" or reading["launch_sha"] != CALIBRATION["launch_sha"]
            or [(x["lineage"], x["winner"]) for x in reading["calibrations"]]
            != list(enumerate(CALIBRATION["winners"]))):
        raise ValueError("paid calibration source/choice changed")
    return CALIBRATION.copy()


def load_assets(protocol=FROZEN):
    if protocol != FROZEN:
        raise ValueError("production asset substitution forbidden")
    models, records = [], []
    for lineage, record in enumerate(CANONICAL_ASSETS):
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


def verify_assets(models, records):
    if len(models) != 2 or len(records) != 2:
        raise AssertionError("both S lineages required")
    for model, record in zip(models, records):
        if state_digest(model.state_dict()) != record["state_sha256"]:
            raise AssertionError("immutable S tensors changed")
        found = file_identity(record["path"])
        if any(found[k] != record[k] for k in ("sha256", "bytes")):
            raise AssertionError("immutable S file changed")

"""Bound original assets and previously paid calibration; no Adam is loaded."""
import hashlib
import json
from pathlib import Path
import subprocess

import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_local_history.b01.study import file_identity
from .contract import CALIBRATION_SOURCE, FROZEN, INITIAL_ASSETS
from .model import make_inherited


def verify_calibration(repo):
    """Read the pinned published blob even when a sparse checkout omits it."""
    binding = CALIBRATION_SOURCE
    blob = subprocess.check_output(
        ["git", "-C", str(repo), "show", binding["evidence_commit"] + ":" + binding["reading_path"]],
        stderr=subprocess.PIPE, timeout=30)
    if hashlib.sha256(blob).hexdigest() != binding["reading_sha256"]:
        raise ValueError("paid calibration source bytes changed")
    saved = json.loads(blob)
    if (saved["status"] != "VERIFIED" or saved["launch_sha"] != binding["launch_sha"]
            or [(r["lineage"], r["winner"]) for r in saved["calibrations"]]
            != list(enumerate(binding["winners"]))):
        raise ValueError("paid calibration choices/source changed")
    return True


def verify_initial_assets(bindings=INITIAL_ASSETS):
    for binding in bindings:
        found = file_identity(binding["path"])
        if any(found[k] != binding[k] for k in ("sha256", "bytes")):
            raise ValueError("original asset bytes changed")
    return True


def load_initial_assets(protocol=FROZEN):
    if protocol != FROZEN:
        raise ValueError("production parent substitution is forbidden")
    states, models, records = [], [], []
    verify_initial_assets()
    for lineage, binding in enumerate(INITIAL_ASSETS):
        saved = torch.load(binding["path"], map_location="cpu", weights_only=True)
        if (saved.get("endpoint") != "S" or saved.get("launch_sha") != binding["launch_sha"]
                or saved.get("architecture") != [114, 128, 128, 27] or saved.get("activation") != "relu"
                or saved.get("dtype") != "float32" or saved.get("optimizer_steps") != 8000):
            raise ValueError("original source/architecture/selection contract changed")
        state = saved["state_dict"]
        if (state_digest(state) != binding["state_sha256"] or saved["state_sha256"] != binding["state_sha256"]
                or any(v.dtype != torch.float32 or not torch.isfinite(v).all() for v in state.values())):
            raise ValueError("original tensor identity changed")
        model = make_inherited(state, protocol.actor_constructor_seeds[lineage]).eval()
        model.requires_grad_(False)
        states.append({k: v.detach().clone() for k, v in state.items()})
        models.append(model)
        records.append(dict(binding, path=str(Path(binding["path"]).resolve()), lineage=lineage,
                            generalized_state_sha256=state_digest(model.state_dict()),
                            inherited_optimizer_loaded=False, count_branch_initialization="exact_zero_128"))
    return states, models, records

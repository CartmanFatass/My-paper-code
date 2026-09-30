"""Verify both immutable inherited tensors before native construction."""
from pathlib import Path

import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_digest
from experiments.candidates.uav_local_history.b01.study import file_identity
from .contract import FROZEN, STAGED_ASSETS


def load_initial_assets(protocol=FROZEN, *, bindings=None, permit_fixture=False):
    bindings = STAGED_ASSETS if bindings is None else tuple(bindings)
    if len(bindings) != 2:
        raise ValueError("both immutable initial assets are required")
    if not permit_fixture and (protocol != FROZEN or bindings != STAGED_ASSETS):
        raise ValueError("production asset substitution is forbidden")
    if permit_fixture and protocol == FROZEN:
        raise ValueError("fixture cannot use production protocol")
    models, records = [], []
    for lineage, record in enumerate(bindings):
        path = Path(record["path"]).resolve()
        actual = file_identity(path)
        if any(actual[key] != record[key] for key in ("bytes", "sha256")):
            raise ValueError("immutable initial asset file identity changed")
        payload = torch.load(path, map_location="cpu", weights_only=True)
        if (payload.get("endpoint") != "S" or payload.get("launch_sha") != record["launch_sha"]
                or payload.get("architecture") != [114, 128, 128, 27]
                or payload.get("activation") != "relu" or payload.get("dtype") != "float32"
                or payload.get("optimizer_steps") != 8000):
            raise ValueError("initial asset source/endpoint/architecture binding changed")
        state = payload["state_dict"]
        if (not state or any(x.dtype != torch.float32 or not torch.isfinite(x).all() for x in state.values())
                or state_digest(state) != record["state_sha256"]
                or payload["state_sha256"] != record["state_sha256"]):
            raise ValueError("initial actor dtype/tensor identity changed")
        actor = make_student(protocol.actor_constructor_seeds[lineage]).eval()
        actor.load_state_dict(state, strict=True)
        if state_digest(actor.state_dict()) != record["state_sha256"]:
            raise AssertionError("initial actor load changed tensors")
        # No inherited optimizer object or state is exposed to the continuation.
        models.append(actor)
        records.append({**record, "path": str(path), "lineage": lineage,
                        "inherited_optimizer_loaded_for_training": False,
                        "architecture": [114, 128, 128, 27], "dtype": "float32", "activation": "relu"})
    return models, records


def verify_initial_assets(models, records):
    for model, record in zip(models, records):
        if state_digest(model.state_dict()) != record["state_sha256"]:
            raise AssertionError("an immutable starting actor was modified")
        found = file_identity(Path(record["path"]))
        if any(found[k] != record[k] for k in ("bytes", "sha256")):
            raise AssertionError("canonical starting asset was changed during execution")

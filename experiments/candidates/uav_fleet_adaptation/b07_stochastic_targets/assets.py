"""Hash-bound temporary consumption of canonical F0 evidence and fixed actors."""
from pathlib import Path

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b06_count_development.assets import verify_calibration
from experiments.candidates.uav_fleet_adaptation.b06_count_development.contract import FROZEN as OLD_PROTOCOL
from experiments.candidates.uav_fleet_adaptation.b06_count_development.model import make_inherited
from experiments.candidates.uav_local_history.b01.study import file_identity
from .contract import FROZEN, INPUT_ROOT, OLD_REL, PARENT_REL, array_digest, input_manifest


def checked_path(root, relative, binding):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("input escaped declared root")
    identity = file_identity(path)
    if any(identity[k] != binding[k] for k in ("bytes", "sha256")):
        raise ValueError("input file identity changed: " + str(relative))
    return path


def verify_inputs(root=INPUT_ROOT):
    manifest = input_manifest()
    rows = manifest["rows"]
    expected = [(phase, world) for phase in range(3) for world in OLD_PROTOCOL.phase_worlds(0, phase)]
    if ([(r["phase"], r["world"]) for r in rows] != expected
            or any((r["arm"], r["lineage"], r["n"], r["kind"]) != ("F", 0, 5, "acquisition") for r in rows)
            or manifest["source_protocol"] != OLD_PROTOCOL.to_dict()):
        raise ValueError("original F0 archive contract changed")
    files = [(PARENT_REL, manifest["parent"]), (OLD_REL / manifest["endpoint"]["path"], manifest["endpoint"])]
    files += [(OLD_REL / row["raw"]["path"], row["raw"]) for row in rows]
    files += [(OLD_REL / row["artifact"]["path"], row["artifact"]) for row in manifest["datasets"]]
    if len(files) != 261 or len({str(p) for p, _ in files}) != 261:
        raise ValueError("required input file roster changed")
    for path, binding in files:
        checked_path(root, path, binding)
    return manifest


def load_actors(repo, root=INPUT_ROOT, manifest=None):
    manifest = verify_inputs(root) if manifest is None else manifest
    verify_calibration(repo)
    parent_binding = manifest["parent"]
    saved = torch.load(checked_path(root, PARENT_REL, parent_binding), map_location="cpu", weights_only=True)
    if (saved.get("endpoint") != "S" or saved.get("launch_sha") != parent_binding["launch_sha"]
            or saved.get("architecture") != [114, 128, 128, 27] or saved.get("activation") != "relu"
            or saved.get("dtype") != "float32" or saved.get("optimizer_steps") != 8000
            or saved.get("state_sha256") != parent_binding["state_sha256"]
            or state_digest(saved["state_dict"]) != parent_binding["state_sha256"]):
        raise ValueError("original P0 checkpoint contract changed")
    parent_state = {k: v.clone() for k, v in saved["state_dict"].items()}
    parent = make_inherited(parent_state, FROZEN.actor_constructor_seed).eval().requires_grad_(False)
    if state_digest(parent.state_dict()) != parent_binding["generalized_state_sha256"]:
        raise ValueError("P0 zero-count adapter identity changed")
    end_binding = manifest["endpoint"]
    endpoint = torch.load(checked_path(root, OLD_REL / end_binding["path"], end_binding),
                          map_location="cpu", weights_only=True)
    if (endpoint.get("schema") != "uav_fleet_adaptation.b06.full_actor.v1"
            or (endpoint.get("endpoint"), endpoint.get("lineage"), endpoint.get("phase")) != ("F", 0, 2)
            or endpoint.get("launch_sha") != manifest["source_launch_sha"]
            or endpoint.get("protocol") != OLD_PROTOCOL.to_dict() or endpoint.get("optimizer_steps") != 8000
            or endpoint.get("original_state_sha256") != parent_binding["state_sha256"]
            or endpoint.get("state_sha256") != end_binding["state_sha256"]
            or state_digest(endpoint["state_dict"]) != end_binding["state_sha256"]):
        raise ValueError("paid F0 checkpoint contract changed")
    fixed = make_inherited(parent_state, FROZEN.actor_constructor_seed)
    fixed.load_state_dict(endpoint["state_dict"], strict=True)
    fixed.eval().requires_grad_(False)
    if (any(v.dtype != torch.float32 or not torch.isfinite(v).all() for v in fixed.state_dict().values())
            or torch.count_nonzero(fixed.count_weight) != 0):
        raise ValueError("invalid paid F0 tensors/count-zero branch")
    return parent_state, parent, fixed


def load_dataset(manifest, root=INPUT_ROOT):
    pieces = []
    for phase, record in enumerate(manifest["datasets"]):
        if (record["phase"], record["arm"], record["lineage"], record["rows"]) != (
                phase, "F", 0, FROZEN.expected()["phase_rows"][phase]):
            raise ValueError("F0 chunk order or extent changed")
        path = checked_path(root, OLD_REL / record["artifact"]["path"], record["artifact"])
        with np.load(path, allow_pickle=False) as archive:
            if set(archive.files) != {"features", "labels", "fleet_counts"}:
                raise ValueError("F0 dataset fields changed")
            x, y, n = (archive[key] for key in ("features", "labels", "fleet_counts"))
        if (x.shape != (record["rows"], 114) or x.dtype != np.float32 or not np.isfinite(x).all()
                or y.shape != (len(x),) or y.dtype != np.int64 or np.any((y < 0) | (y > 26))
                or n.shape != y.shape or n.dtype != np.int64 or not np.all(n == 5)
                or array_digest(x, y, n) != record["data_sha256"]):
            raise ValueError("F0 dataset array identity changed")
        pieces.append((x, y, n))
        combined = tuple(np.concatenate([piece[i] for piece in pieces]) for i in range(3))
        if array_digest(*combined) != manifest["fit"]["phases"][phase]["data_sha256"]:
            raise ValueError("accumulated original F0 row/order digest changed")
    return combined

"""One fixed B07 panel consuming, never modifying, the published B06 fit."""
from pathlib import Path
import json
import re

from experiments.candidates.uav_fleet_transmission.study import artifact, sha256
from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization.contract import (
    FIT_FILE, source_bindings as inherited_bindings,
)
from .host import WORLD_FILE, WORLD_IDS

REPO = Path(__file__).resolve().parents[4]
DIRECTION = "uav_parent_adaptation"
TAG = "b07_shortlist_amortization_a01"
BOOTSTRAP_SEED = 29367991
ARMS = ("R", "T_E", "K2_E", "L2_E")
FIT_SHA256 = "a2b5d1a8c127c50494e8b8aa76ff84ba3ca61e4b5db6281e4713e524ea2fd0c1"
CEILINGS = {
    "worker_state_mask_requests": 37972448, "model_physical_transitions": 103040,
    "candidate_transit_ticks": 1792000, "stationary_candidate_rows": 44800,
    "model_branches": 224, "native_steps": 32000, "episodes": 64,
}
OWN_PREFIX = "experiments/candidates/uav_parent_adaptation/b07_shortlist_amortization/"
OWN_SOURCE_PATHS = tuple(OWN_PREFIX + f for f in (
    "__init__.py", "host.py", "worlds.json", "contract.py", "controller.py",
    "outcomes.py", "study.py", "reader.py", "run.py"))
CONTRASTS = (("L2_E", "K2_E"), ("L2_E", "R"), ("L2_E", "T_E"),
             ("T_E", "R"), ("K2_E", "R"), ("T_E", "K2_E"))


def source_bindings():
    inherited = inherited_bindings()
    original = json.loads((FIT_FILE.parent / "config.json").read_text())["source_bindings"]
    if inherited != original:
        raise ValueError("frozen B06 executable or paid source has changed")
    own = {p: {"sha256": sha256(REPO / p), "bytes": (REPO / p).stat().st_size}
           for p in OWN_SOURCE_PATHS}
    return {**inherited, **own}


def fixed_config(fit_sha256=FIT_SHA256):
    if fit_sha256 != FIT_SHA256:
        raise ValueError("B07 consumes only the original fixed B06 ranker")
    binding = artifact(FIT_FILE, REPO)
    if binding["sha256"] != FIT_SHA256:
        raise ValueError("original fitted artifact bytes differ")
    return {
        "direction": DIRECTION, "object_id": "parent_n8_shortlist_amortization_b07",
        "phase": "evaluate", "source_bindings": source_bindings(),
        "fit_artifact": binding,
        "fit_inputs": {name: artifact(FIT_FILE.parent / name, REPO) for name in (
            "config.json", "summary.json", "reading.json", "training_rows.json",
            "ranker.json", "launch-manifest.json")},
        "new_fits": 0, "updates": 0, "new_training_acquisition": 0,
        "inherited_B06_fits": 1, "evaluation_refit": False,
        "training_worlds": list(range(29326000, 29326016)), "training_rows": 58,
        "feature_count": 12, "coefficient_count": 13, "shortlist_size": 2,
        "negative_predictions_remain_eligible": True,
        "world_ids": list(WORLD_IDS), "world_file": artifact(WORLD_FILE, REPO),
        "world_order": "ascending world; cyclic R/T_E/K2_E/L2_E starting at world index mod4",
        "n": 8, "users": 50, "capacity": 10, "min_sinr": 0., "horizon": 500,
        "cadence": 10, "option_t": 40, "arms": list(ARMS),
        "contrasts": [list(v) for v in CONTRASTS],
        "suffix": "460 post-action outcomes for t40..499; connections[41:]",
        "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_replicates": 10000,
        "ceilings": CEILINGS.copy(), "numerical_threads": 1,
    }


def validate_operation(summary, out):
    from experiments.candidates.uav_fleet_transmission.b03.reader import checked_path
    config = summary["config"]
    expected = fixed_config()
    if (any(config.get(k) != v for k, v in expected.items())
            or set(config) != set(expected) | {"launch_sha", "admission_command_sha256", "versions"}
            or not re.fullmatch(r"[0-9a-f]{40}", summary["launch_sha"])
            or summary["launch_sha"] != config["launch_sha"]
            or not re.fullmatch(r"[0-9a-f]{64}", config["admission_command_sha256"])):
        raise ValueError("fixed B07 configuration/source/admission differs")
    path = checked_path(out, summary["config_artifact"])
    if path != out / "config.json" or json.loads(path.read_text()) != config:
        raise ValueError("bound saved B07 configuration differs")
    manifest = json.loads((out / "launch-manifest.json").read_text())
    if (manifest.get("acceptance") != "accepted" or manifest.get("sha") != summary["launch_sha"]
            or manifest.get("direction") != DIRECTION
            or manifest.get("command_sha256") != config["admission_command_sha256"]):
        raise ValueError("accepted B07 launch manifest differs")

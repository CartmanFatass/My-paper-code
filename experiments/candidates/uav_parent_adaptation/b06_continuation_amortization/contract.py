"""Published source/data identities and fixed exposure for the one B06 study."""
from pathlib import Path
import json
import re

from experiments.candidates.uav_fleet_transmission.b03.study import SOURCE_PATHS as FROZEN_PATHS
from experiments.candidates.uav_fleet_transmission.study import artifact, sha256

from .host import WORLD_FILE, WORLD_IDS

REPO = Path(__file__).resolve().parents[4]
DIRECTION = "uav_parent_adaptation"
BOOTSTRAP_SEED = 29366991
ARMS = ("R", "T_E", "K2_E", "L")
PAID_SOURCE = "02e8c1adc5a625037490facc6388e4b8bc9fd74e"
PAID_SUMMARY_REL = "runs/uav_fleet_transmission/b03_complete_continuation_a02/summary.json"
PAID_SUMMARY = REPO / PAID_SUMMARY_REL
PAID_SUMMARY_SHA = "df0d60b900d816bc93fed1855feca1afc9050dc2b719b017a7beb5d159a5cd7d"
PAID_RAW = Path("/home/fires/hmasd-artifacts/uav_fleet_transmission/b03_complete_continuation_a02/raw")
FIT_REL = "runs/uav_parent_adaptation/b06_paid_ranker_fit_a01/ranker.json"
FIT_FILE = REPO / FIT_REL
CEILINGS = {
    "worker_state_mask_requests": 32706304, "model_physical_transitions": 80960,
    "candidate_transit_ticks": 1792000, "stationary_candidate_rows": 44800,
    "model_branches": 176, "native_steps": 32000, "episodes": 64,
}
OWN_PREFIX = "experiments/candidates/uav_parent_adaptation/b06_continuation_amortization/"
PAID_COMPACT = tuple(str(Path(PAID_SUMMARY_REL).parent / name)
                     for name in ("config.json", "reading.json"))
SOURCE_PATHS = tuple(dict.fromkeys((*FROZEN_PATHS, PAID_SUMMARY_REL, *PAID_COMPACT, *(
    OWN_PREFIX + f for f in ("__init__.py", "host.py", "worlds.json", "contract.py",
                            "learning.py", "cycle.py", "controller.py", "fit.py",
                            "study.py", "reader.py", "run.py")))))


def source_bindings():
    result = {p: {"sha256": sha256(REPO/p), "bytes": (REPO/p).stat().st_size} for p in SOURCE_PATHS}
    if result[PAID_SUMMARY_REL]["sha256"] != PAID_SUMMARY_SHA:
        raise ValueError("paid training summary differs from the original published evidence")
    frozen = json.loads(PAID_SUMMARY.read_text())["config"]["source_bindings"]
    if any(result[p] != frozen[p] for p in FROZEN_PATHS):
        raise ValueError("inherited executable differs from the original paid B03 source")
    return result


def fixed_config(phase, fit_sha256=None):
    if phase not in ("fit", "evaluate"):
        raise ValueError("unknown B06 phase")
    if phase == "fit" and fit_sha256 is not None:
        raise ValueError("the single fit cannot consume an evaluated artifact")
    config = {
        "direction": DIRECTION, "object_id": "parent_n8_amortization_b06_" + phase,
        "phase": phase, "source_bindings": source_bindings(),
        "training_summary": artifact(PAID_SUMMARY, REPO), "training_raw_root": str(PAID_RAW),
        "training_source": PAID_SOURCE, "training_worlds": list(range(29326000, 29326016)),
        "training_rows": 58, "new_training_acquisition": 0,
        "new_fits": int(phase == "fit"), "updates": 0, "ridge_penalty_all_coefficients": .1,
        "row_weight": "1/(16*world_champion_count); no penalty rescaling",
        "feature_count": 12, "coefficient_count": 13,
        "world_ids": list(WORLD_IDS), "world_file": artifact(WORLD_FILE, REPO),
        "world_order": "ascending world; cyclic R/T_E/K2_E/L starting at world index mod4",
        "n": 8, "users": 50, "capacity": 10, "min_sinr": 0., "horizon": 500,
        "cadence": 10, "option_t": 40, "arms": list(ARMS),
        "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_replicates": 10000,
        "ceilings": CEILINGS.copy(), "numerical_threads": 1,
        "evaluation_refit": False,
    }
    if phase == "evaluate":
        if not isinstance(fit_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", fit_sha256):
            raise ValueError("evaluation requires the published fit SHA256")
        binding = artifact(FIT_FILE, REPO)
        if binding["sha256"] != fit_sha256:
            raise ValueError("published fit artifact bytes differ")
        config["fit_artifact"] = binding
        config["fit_inputs"] = {name: artifact(FIT_FILE.parent/name, REPO) for name in (
            "config.json", "summary.json", "reading.json", "training_rows.json", "ranker.json", "launch-manifest.json")}
    return config

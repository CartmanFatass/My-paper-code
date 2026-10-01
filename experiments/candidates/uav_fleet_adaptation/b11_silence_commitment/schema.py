"""Explicit ordinary/bypass schema; unavailable C values are NaN with a mask."""
import numpy as np
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.audit import equal, require

BOOL_DECISIONS = ("fallback", "memo_hit", "eligible", "requested_off", "off_evaluated", "c_available",
    "pending_before", "pending_after", "memory_created", "memory_consumed", "origin_available")
INT_DECISIONS = ("action_index", "motion_index", "n_current", "n_peers", "c_index", "gate_count",
    "origin_tick", "origin_agent", "origin_count", "origin_c_index", "origin_issued_index", "origin_nav", "stored_index")
FLOAT_DECISIONS = ("innovation", "entropy", "gate_prediction", "off_score", "off_service")
DECISIONS = (*BOOL_DECISIONS, *INT_DECISIONS, *FLOAT_DECISIONS,
             "features", "probabilities", "policy_scores", "policy_served", "origin_row")


def shapes(horizon, program):
    d=horizon//4
    values=dict(positions=(horizon+1,5,3), observations=(horizon,5,104), commands=(horizon,5,3),
        reward=(horizon,), served=(horizon,), sinr_quality=(horizon,), sinr=(horizon,5,50),
        peer_sinr=(horizon,5,5), connections=(horizon,5,50), transmitter_mask=(horizon,5),
        terminated=(horizon,), truncated=(horizon,), step_generation=(horizon,), step_path_loss_misses=(horizon,),
        nav_pre=(d,5), nav_next=(d,5), features=(d,5,114), probabilities=(d,5,27),
        policy_scores=(d,5,27), policy_served=(d,5,27), origin_row=(d,5,104),
        old_decision_mask=(d,5), installed_mask=(d,5), eligible_agent=(d,),
        refresh_sinr=(d,5,50), refresh_peer_sinr=(d,5,5), refresh_connections=(d,5,50),
        refresh_observations=(d,5,104), refresh_generation=(d,), refresh_path_loss_misses=(d,),
        initial_users=(50,2), initial_sinr=(5,50), initial_peer_sinr=(5,5), initial_connections=(5,50),
        initial_generation=(), terminal_observation=(5,104), terminal_pending=(5,), decision_ticks=(d,))
    values.update({key:(d,5) for key in (*BOOL_DECISIONS,*INT_DECISIONS,*FLOAT_DECISIONS)})
    values.update({key:(d,) for key in ("gate_innovation", "gate_prediction_boundary", "gate_count_boundary",
                                     "gate_requested_off", "gate_off", "gate_forced")})
    if program == "Hdirect_ZERO":
        values.update(logits=(d,5,27), hidden=(d,5,128), parent_probabilities=(d,5,27))
    return values


def dtype(key):
    booleans={*BOOL_DECISIONS,"connections","transmitter_mask","terminated","truncated",
        "old_decision_mask","installed_mask","refresh_connections","initial_connections",
        "gate_requested_off","gate_off","gate_forced","terminal_pending"}
    integers={*INT_DECISIONS,"served","step_generation","step_path_loss_misses","nav_pre","nav_next",
        "eligible_agent","refresh_generation","refresh_path_loss_misses","initial_generation","decision_ticks","gate_count_boundary"}
    fp32={"observations","commands","features","origin_row","refresh_observations","terminal_observation","logits","hidden"}
    return np.bool_ if key in booleans else np.int64 if key in integers else np.float32 if key in fp32 else np.float64


def check(raw, horizon, program):
    roster=shapes(horizon,program)
    require(set(raw)==set(roster), "complete B11 raw field roster")
    unavailable={"features","policy_scores","policy_served","off_score","off_service"}
    for key, shape in roster.items():
        a=raw[key]
        require(a.shape==shape, key+": shape")
        require(a.dtype==dtype(key), key+": dtype")
        if key in unavailable:
            mask=raw["off_evaluated"] if key in ("off_score","off_service") else raw["c_available"]
            require(np.isfinite(a[mask]).all() and np.isnan(a[~mask]).all(), key+": availability")
        elif key not in ("sinr","peer_sinr","refresh_sinr","refresh_peer_sinr","initial_sinr","initial_peer_sinr"):
            require(np.isfinite(a).all(), key+": finite")
    require(np.all(raw["c_index"][~raw["c_available"]]==-1), "unavailable original C category")
    equal(raw["decision_ticks"],np.arange(0,horizon,4),"complete boundary clocks")

"""Block 1 readings of ``b04_geometry_probe_a01`` (inputs of the pre-written rules, no verdicts).

Heading of a proposal = atan2(a_y, a_x) of the raw 4-vector.  Per (world, agent, t, condition):
dtheta = wrap(theta_c[j] - theta_ID[m(j)]) and |da_xy|, with m the recorded matching (identity
except ROT / MIR_X / MIR_Y).  Symmetry error e = |wrap(theta_c[j] - ideal(theta_ID[m(j)]))| with
ideal = theta + pi (ROT, ROT_KEEP), pi - theta (MIR_X: x -> A - x), -theta (MIR_Y: y -> A - y);
pooled over exact matches (< MATCH_EXACT_M at t = 0), the non-exact agent reported separately.
UAV pairs with a shield mode on either side are dropped from heading readings and counted.
"""

from __future__ import annotations

import numpy as np

from .geometry_probe import CONDITIONS, MATCH_EXACT_M, PLANNERS, QUERY_STEPS

SYMMETRY = {"ROT": lambda a: a + np.pi, "ROT_KEEP": lambda a: a + np.pi,
            "MIR_X": lambda a: np.pi - a, "MIR_Y": lambda a: -a}
PLANNER_ROTATION_DEG = 20.0


def wrap(angle):
    """Wrap to [-pi, pi)."""
    return (np.asarray(angle) + np.pi) % (2.0 * np.pi) - np.pi


def heading(actions):
    actions = np.asarray(actions, dtype=np.float64)
    return np.arctan2(actions[..., 1], actions[..., 0])


def symmetry_error(theta_c, theta_id, condition):
    return np.abs(wrap(theta_c - SYMMETRY[condition](theta_id)))


def _stats(values_deg):
    values = np.asarray(values_deg, dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {"n": 0, "median": None, "q25": None, "q75": None}
    q25, median, q75 = np.percentile(values, [25, 50, 75])
    return {"n": int(values.size), "median": round(float(median), 3),
            "q25": round(float(q25), 3), "q75": round(float(q75), 3)}


def per_pair(proposals, modes, matching, id_index=0):
    """dtheta / |da_xy| / keep-mask [W, T, C, n] from proposals [W, T, C, n, 4], modes [W, T, C, n],
    matching [W, C, n] (m(j) per condition)."""
    theta = heading(proposals)
    idx = matching[:, None, :, :]
    theta_id = np.take_along_axis(np.broadcast_to(theta[:, :, id_index:id_index + 1], theta.shape), np.broadcast_to(idx, theta.shape), -1)
    mode_id = np.take_along_axis(np.broadcast_to(modes[:, :, id_index:id_index + 1], modes.shape), np.broadcast_to(idx, modes.shape), -1)
    a_id = np.take_along_axis(np.broadcast_to(proposals[:, :, id_index:id_index + 1, :, :2], proposals[..., :2].shape),
                              np.broadcast_to(idx[..., None], proposals[..., :2].shape), -2)
    keep = ~(modes | mode_id)
    return {"theta": theta, "theta_id": theta_id, "dtheta": wrap(theta - theta_id),
            "dxy": np.linalg.norm(proposals[..., :2] - a_id, axis=-1), "keep": keep}


def readings(arrays: dict, matching: np.ndarray, exact: np.ndarray, conditions=CONDITIONS,
             steps=QUERY_STEPS) -> dict:
    """``arrays``: stacked Block 1 arrays (world axis first); ``matching`` / ``exact`` [W, C, n]."""
    learner = per_pair(arrays["proposals"], arrays["modes"], matching)
    later = np.asarray([t > 0 for t in steps])
    result = {"conditions": list(conditions), "query_steps": list(steps), "t0": {}, "t10_90": {},
              "per_index": {}, "symmetry_error": {}, "dropped_shield_pairs": {}, "planners": {},
              "sign_agreement": {}}
    for k, condition in enumerate(conditions):
        keep = learner["keep"][:, :, k]
        result["dropped_shield_pairs"][condition] = {"t0": int((~keep[:, 0]).sum()),
                                                     "t10_90": int((~keep[:, later]).sum())}
        for label, select in (("t0", ~later), ("t10_90", later)):
            mask = keep[:, select]
            dtheta = np.degrees(np.abs(learner["dtheta"][:, select, k]))[mask]
            result[label][condition] = {"abs_dtheta_deg": _stats(dtheta),
                                        "abs_dxy": _stats(learner["dxy"][:, select, k][mask])}
        result["per_index"][condition] = {
            label: [_stats(np.degrees(np.abs(learner["dtheta"][:, select, k, j]))[keep[:, select, j]])
                    for j in range(keep.shape[-1])]
            for label, select in (("t0", ~later), ("t10_90", later))}
        if condition in SYMMETRY:
            error = np.degrees(symmetry_error(learner["theta"][:, :, k], learner["theta_id"][:, :, k], condition))
            exact_k = np.broadcast_to(exact[:, None, k, :], keep.shape)
            block = {}
            for label, select in (("t0", ~later), ("t10_90", later)):
                block[label] = {"exact_matches": _stats(error[:, select][(keep & exact_k)[:, select]]),
                                "non_exact": _stats(error[:, select][(keep & ~exact_k)[:, select]])}
            block["non_exact_agents"] = [
                {"world": int(w), "agent": int(j)} for w, j in zip(*np.nonzero(~exact[:, k, :]))]
            result["symmetry_error"][condition] = block
    for p, planner in enumerate(PLANNERS):
        prop = arrays["planner_proposals"][:, p][:, None]          # [W, 1, C, n, 4]
        mode = arrays["planner_modes"][:, p][:, None]
        pairs = per_pair(prop, mode, matching)
        valid = pairs["keep"] & np.isfinite(pairs["dtheta"])
        block, agreement = {}, {}
        for k, condition in enumerate(conditions):
            mask = valid[:, 0, k]
            block[condition] = {"abs_dtheta_deg": _stats(np.degrees(np.abs(pairs["dtheta"][:, 0, k]))[mask])}
            if condition in SYMMETRY:
                error = np.degrees(symmetry_error(pairs["theta"][:, 0, k], pairs["theta_id"][:, 0, k], condition))
                block[condition]["symmetry_error_exact"] = _stats(error[mask & exact[:, k]])
            rotating = mask & learner["keep"][:, 0, k] & (np.degrees(np.abs(pairs["dtheta"][:, 0, k])) > PLANNER_ROTATION_DEG)
            same = np.sign(learner["dtheta"][:, 0, k]) == np.sign(pairs["dtheta"][:, 0, k])
            agreement[condition] = {"pairs": int(rotating.sum()),
                                    "share": (round(float(same[rotating].mean()), 4) if rotating.any() else None)}
        result["planners"][planner] = block
        result["sign_agreement"][planner] = agreement
    result["rule_inputs"] = {
        "median_e_rot": {"t0": result["symmetry_error"].get("ROT", {}).get("t0", {}).get("exact_matches", {}).get("median"),
                         "t10_90": result["symmetry_error"].get("ROT", {}).get("t10_90", {}).get("exact_matches", {}).get("median")},
        "learner_median_abs_dtheta": {c: {"t0": result["t0"][c]["abs_dtheta_deg"]["median"],
                                          "t10_90": result["t10_90"][c]["abs_dtheta_deg"]["median"]}
                                      for c in conditions},
        "planner_median_abs_dtheta": {p: {c: result["planners"][p][c]["abs_dtheta_deg"]["median"]
                                          for c in conditions} for p in PLANNERS},
        "sign_agreement_share": {p: {c: result["sign_agreement"][p][c]["share"] for c in conditions}
                                 for p in PLANNERS},
        "planner_rotation_threshold_deg": PLANNER_ROTATION_DEG, "exact_match_m": MATCH_EXACT_M}
    return result

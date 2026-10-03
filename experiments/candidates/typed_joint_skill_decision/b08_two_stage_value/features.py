"""Lawful B08 features; no host imports, queries, outcomes or random draws.

Plans and bank use the frozen fleet B04 dictionary schema. ``None`` is stay.
Construction uses FP64 arithmetic on decoded FP32 public bits, then one FP32
cast. Peer order is ascending source member with self removed. The frozen
stationary ``energy_penalty`` field is the native all-UAV height penalty.
"""
import math
from numbers import Integral

import numpy as np

SHAPES = {"U": (8, 8, 20), "Y": (8, 50, 2),
          "E_UY": (8, 8, 50, 9), "E_UU": (8, 8, 7, 9), "S": (8, 17)}


def build_features(report, commands, mask, plans, bank):
    report, commands = np.asarray(report), np.asarray(commands)
    if (report.dtype != np.float32 or report.shape != (133,)
            or commands.dtype != np.float32 or commands.shape != (8, 3)
            or not np.isfinite(report).all() or not np.isfinite(commands).all()):
        raise ValueError("finite FP32 public report[133] and issued commands[8,3] required")
    if (not np.array_equal(report[24:32], np.ones(8, dtype=np.float32))
            or np.any(report[:24] < 0) or np.any(report[:24] > 1)
            or np.any(report[32:] < 0) or np.any(report[32:] > 1)
            or not np.isin(commands, [-1, 0, 1]).all()):
        raise ValueError("invalid N8 report/ternary command contract")
    if isinstance(mask, (bool, np.bool_)) or not isinstance(mask, Integral) or not 1 <= mask <= 255:
        raise ValueError("nonempty N8 transmitter mask required")
    active = np.array([(int(mask) >> i) & 1 for i in range(8)], dtype=np.float64)
    members = np.flatnonzero(active == 0).tolist()
    if (len(plans) != 1 + len(members) or plans[0] is not None
            or [p["member"] for p in plans[1:]] != members):
        raise ValueError("complete source-ascending stay/champion menu required")
    current = report[:24].reshape(8, 3).astype(np.float64)
    positions = current * (1000., 1000., 100.) + (0., 0., 50.)
    users = report[32:132].reshape(50, 2).astype(np.float64)
    peer = np.array([[j for j in range(8) if j != i] for i in range(8)])
    result = {key: np.zeros(shape, dtype=np.float32) for key, shape in SHAPES.items()}
    result["valid"] = np.arange(8) < len(plans)
    stay = bank["original_R"]
    for a, plan in enumerate(plans):
        selected = np.zeros(8)
        if plan is None:
            dest, arrival = positions.copy(), active.copy()
            tail = stay["stay_score"]
            scalars = [1., 0., 0., 0., 0., 0., 0., 0., tail["J"],
                       tail["served"] / 50., tail["quality"], tail["energy_penalty"] / .1,
                       0., 0.]
        else:
            # Original B04 t40 menus delegate to B03's _plan, whose schema
            # implies t40 and omits start_t. An explicit different clock is
            # still illegal; never insert a field into the supplied plan.
            if plan["initiated"] is not True or plan.get("start_t", 40) != 40:
                raise ValueError("forced t40 stationary champion required, including nonpositive options")
            member = plan["member"]
            dest = np.asarray(plan["predicted_destination"], dtype=np.float64)
            predicted_mask = plan["predicted_mask"]
            if (dest.shape != (8, 3) or not np.isfinite(dest).all()
                    or np.any(dest < [0, 0, 50]) or np.any(dest > [1000, 1000, 150])
                    or isinstance(predicted_mask, (bool, np.bool_))
                    or not isinstance(predicted_mask, Integral)
                    or not 1 <= predicted_mask <= 255 or not (predicted_mask & (1 << member))
                    or not np.array_equal(dest[np.arange(8) != member], positions[np.arange(8) != member])):
                raise ValueError("invalid lawful stationary destination/arrival mask")
            if plan["duration"] not in (10, 20, 30, 40):
                raise ValueError("fixed commitment duration required")
            arrival = np.array([(int(predicted_mask) >> i) & 1 for i in range(8)], dtype=np.float64)
            selected[member] = 1.
            detail, tail = plan["selected"], plan["selected"]["tail_score"]
            kx, ky = plan["offsets"]
            scalars = [0., plan["duration"] / 40., kx / 34., ky / 34.,
                       detail["descent_ticks"] / 4., detail["path"] / (1200. * math.sqrt(3.)),
                       (plan["predicted_total_J"] - stay["stay_total_J"]) / 460.,
                       (plan["predicted_total_served"] - stay["stay_total_served"]) / (460. * 50.),
                       tail["J"], tail["served"] / 50., tail["quality"],
                       tail["energy_penalty"] / .1, detail["transit_J"] / 40.,
                       detail["transit_served"] / (40. * 50.)]
        target = (dest - (0., 0., 50.)) / (1000., 1000., 100.)
        result["U"][a] = np.concatenate((current, commands, active[:, None], np.eye(8),
                                          target, arrival[:, None], selected[:, None]), axis=-1)
        result["Y"][a] = users
        cur_user = np.empty((8, 50, 3)); dst_user = np.empty_like(cur_user)
        cur_user[..., :2] = (positions[:, None, :2] - (users * 1000.)[None]) / 1000.
        dst_user[..., :2] = (dest[:, None, :2] - (users * 1000.)[None]) / 1000.
        cur_user[..., 2] = (positions[:, None, 2] - 50.) / 100.
        dst_user[..., 2] = (dest[:, None, 2] - 50.) / 100.
        rights = np.stack((active, arrival, selected), axis=-1)
        result["E_UY"][a] = np.concatenate((cur_user, dst_user,
                                               np.broadcast_to(rights[:, None], (8, 50, 3))), axis=-1)
        result["E_UU"][a] = np.concatenate(((positions[:, None] - positions[peer]) / (1000., 1000., 100.),
                                               (dest[:, None] - dest[peer]) / (1000., 1000., 100.), rights[peer]), axis=-1)
        result["S"][a] = scalars + [float(report[-1]), len(members) / 7., active.sum() / 8.]
    if any(not np.isfinite(result[k]).all() for k in SHAPES):
        raise ValueError("nonfinite stationary-bank feature")
    return result

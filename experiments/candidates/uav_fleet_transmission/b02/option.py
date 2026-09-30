"""The fixed t40 silent relocation option, using only decoded public inputs."""

import hashlib
from numbers import Integral

import numpy as np

from ..control import _Scores, predict_next
from ..host import mask_bits

PLAN_DIGEST_LAYOUT = ["member", "site", "kx", "ky", "descent_ticks", "duration",
                      "mask", "total_J", "total_served", "path", "transit_J",
                      "transit_served", "tail_J", "tail_served", "tail_quality",
                      "tail_energy_penalty"] + [f"destination_{i}_{axis}"
                                                for i in range(8) for axis in "xyz"]
ARRIVAL_DIGEST_LAYOUT = ["mask", "J", "served", "quality", "energy_penalty"]


def _integer(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an integer")
    return int(value)


def _inputs(positions, users):
    positions = np.asarray(positions, dtype=np.float64)
    users = np.asarray(users, dtype=np.float64)
    if positions.shape != (8, 3) or not np.isfinite(positions).all():
        raise ValueError("requires eight finite public UAV positions")
    if users.shape != (50, 2) or not np.isfinite(users).all():
        raise ValueError("requires fifty finite public user positions")
    if (np.any(positions < [0, 0, 50]) or np.any(positions > [1000, 1000, 150])
            or np.any(users < 0) or np.any(users > 1000)):
        raise ValueError("public positions must lie within native bounds")
    return positions, users


def _sites(users):
    centroids = []
    for anchor in range(50):
        delta = users - users[anchor]
        squared = delta[:, 0] * delta[:, 0] + delta[:, 1] * delta[:, 1]
        others = np.arange(50)[np.arange(50) != anchor]
        nearest = others[np.argsort(squared[others], kind="stable")[:9]]
        # Anchor first, then the nine neighbors in distance/row order. The
        # explicit anchor matters when ten or more user rows coincide.
        centroids.append(np.mean(users[np.r_[anchor, nearest]], axis=0))
    return np.concatenate((users, np.asarray(centroids)), axis=0)


def _project(coordinate, target):
    return min(range(-34, 35), key=lambda k: (
        abs(float(np.clip(coordinate + 30 * k, 0, 1000)) - target),
        float(np.clip(coordinate + 30 * k, 0, 1000)), abs(k), k))


def _mask_choice(scorer, positions, member):
    masks = [mask for mask in range(1, 256) if mask & (1 << member)]
    scores = scorer.score(positions, masks)
    index = max(range(128), key=lambda i: (scores[i]["J"], scores[i]["served"], -masks[i]))
    return masks, scores, index


def arrival_mask(users, positions, member):
    """Search all 128 member-containing masks; do not prefer the old mask."""
    positions, users = _inputs(positions, users)
    member = _integer(member, "member")
    if not 0 <= member < 8:
        raise ValueError("member must be in [0, 7]")
    scorer = _Scores(users)
    masks, scores, index = _mask_choice(scorer, positions, member)
    # Rows are ascending mask integer, each little-endian float64 in the
    # documented column order. No native-endian bytes or JSON formatting.
    readings = [[mask, score["J"], score["served"], score["quality"], score["energy_penalty"]]
                for mask, score in zip(masks, scores)]
    digest = hashlib.sha256(np.asarray(readings, dtype="<f8").tobytes()).hexdigest()
    return masks[index], dict(counts=dict(scorer.counts), selected_mask=masks[index],
                              selected_score=scores[index], candidate_digest=digest,
                              digest_layout=ARRIVAL_DIGEST_LAYOUT.copy())


def _transit(positions, member, site, stay_score):
    offsets = [_project(positions[member, axis], site[axis]) for axis in range(2)]
    descent = int(np.ceil((positions[member, 2] - 50.0) / 30.0))
    unrounded = max(abs(offsets[0]), abs(offsets[1]), descent)
    duration = 10 * max(1, (unrounded + 9) // 10)
    if duration > 40:
        raise ValueError("candidate duration exceeds the fixed forty-tick commitment")
    commands = np.zeros((duration, 8, 3), dtype=np.float32)
    for axis, offset in enumerate(offsets):
        commands[:abs(offset), member, axis] = np.sign(offset)
    commands[:descent, member, 2] = -1.0
    predicted = positions.copy()
    transit_J, path = 0.0, 0.0
    radio_J = .7 * (stay_score["served"] / 50) + .3 * stay_score["quality"]
    for command in commands:
        next_positions = predict_next(predicted, command)
        path += float(np.linalg.norm(next_positions - predicted, axis=1).sum())
        # Only a silent member moves. Radio service is invariant, but the
        # native all-physical-UAV height term is recomputed at every tick.
        height = (np.mean(next_positions[:, 2]) - 50.0) / 100.0 * .1
        transit_J += float(radio_J - height)
        predicted = next_positions
    return dict(offsets=offsets, descent_ticks=descent, unrounded_duration=unrounded,
                duration=duration, commands=commands, destination=predicted,
                transit_J=transit_J, transit_served=duration * stay_score["served"], path=path)


def plan_option(positions, users, old_mask, t=40, horizon=500):
    """Plan once with a stationary tail; this is not continued ordinary control.

    Digest rows cover every silent-member/site pair in ascending member then
    site order, including duplicate sites. Each row consists of the named
    PLAN_DIGEST_LAYOUT columns serialized as little-endian float64. Requested
    candidates count stay plus all destination state/mask requests; model_ticks
    counts every propagated transit tick separately from radio requests.
    """
    positions, users = _inputs(positions, users)
    t, horizon = _integer(t, "t"), _integer(horizon, "horizon")
    if t != 40 or horizon != 500:
        raise ValueError("this option is fixed at t40/H500")
    active = mask_bits(old_mask, 8)
    old_mask = int(old_mask)
    scorer = _Scores(users)
    stay = scorer.score(positions, [old_mask])[0]
    remaining = horizon - t
    stay_total_J, stay_total_served = remaining * stay["J"], remaining * stay["served"]
    sites = _sites(users)
    digest = hashlib.sha256()
    best, best_rank = None, None
    model_ticks, candidate_count = 0, 0
    for member in np.flatnonzero(~active).tolist():
        for site_index, site in enumerate(sites):
            candidate = _transit(positions, member, site, stay)
            masks, scores, mask_index = _mask_choice(scorer, candidate["destination"], member)
            tail = scores[mask_index]
            duration = candidate["duration"]
            total_J = candidate["transit_J"] + (remaining - duration) * tail["J"]
            total_served = candidate["transit_served"] + (remaining - duration) * tail["served"]
            candidate.update(member=member, site=site_index, predicted_mask=masks[mask_index],
                             tail_score=tail, predicted_total_J=total_J,
                             predicted_total_served=total_served)
            readings = [member, site_index, *candidate["offsets"], candidate["descent_ticks"],
                        duration, masks[mask_index], total_J, total_served, candidate["path"],
                        candidate["transit_J"], candidate["transit_served"], tail["J"],
                        tail["served"], tail["quality"], tail["energy_penalty"],
                        *candidate["destination"].reshape(-1)]
            digest.update(np.asarray(readings, dtype="<f8").tobytes())
            rank = (total_J, total_served, -candidate["path"], -duration, -member, -site_index)
            if best_rank is None or rank > best_rank:
                best, best_rank = candidate, rank
            model_ticks += duration
            candidate_count += 1
    initiated = best is not None and best["predicted_total_J"] > stay_total_J
    selected = None
    if best is not None:
        selected = {key: value for key, value in best.items() if key not in ("commands", "destination")}
        selected["predicted_destination"] = best["destination"].tolist()
        selected["arrival_t"] = t + best["duration"]
    return dict(initiated=bool(initiated), member=best["member"] if initiated else None,
                site=best["site"] if initiated else None,
                offsets=best["offsets"] if initiated else None,
                commands=best["commands"].tolist() if initiated else [],
                duration=best["duration"] if initiated else 0,
                arrival_t=t + best["duration"] if initiated else None,
                predicted_destination=(best["destination"] if initiated else positions).tolist(),
                predicted_mask=best["predicted_mask"] if initiated else None,
                predicted_total_J=best["predicted_total_J"] if initiated else stay_total_J,
                predicted_total_served=best["predicted_total_served"] if initiated else stay_total_served,
                stay_score=stay, stay_total_J=stay_total_J, stay_total_served=stay_total_served,
                selected=selected, candidate_digest=digest.hexdigest(),
                digest_layout=PLAN_DIGEST_LAYOUT.copy(), candidate_count=candidate_count,
                counts=dict(scorer.counts, model_ticks=model_ticks))

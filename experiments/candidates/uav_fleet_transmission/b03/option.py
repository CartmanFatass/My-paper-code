"""Original R enumeration, retaining one stationary champion per silent member."""
import hashlib

import numpy as np

from ..control import _Scores
from ..host import mask_bits
from ..b02.option import PLAN_DIGEST_LAYOUT, _inputs, _mask_choice, _sites, _transit


def stationary_rank(candidate):
    return (candidate["predicted_total_J"], candidate["predicted_total_served"],
            -candidate["path"], -candidate["duration"], -candidate["member"], -candidate["site"])


def _plan(best, positions, stay, digest, counts, candidate_count, *, force=False):
    stay_J, stay_served = 460 * stay["J"], 460 * stay["served"]
    initiated = best is not None and (force or best["predicted_total_J"] > stay_J)
    selected = None
    if best is not None:
        selected = {key: value for key, value in best.items() if key not in ("commands", "destination")}
        selected["predicted_destination"] = best["destination"].tolist()
        selected["arrival_t"] = 40 + best["duration"]
    return dict(initiated=bool(initiated), member=best["member"] if initiated else None,
        site=best["site"] if initiated else None, offsets=best["offsets"] if initiated else None,
        commands=best["commands"].tolist() if initiated else [],
        duration=best["duration"] if initiated else 0,
        arrival_t=40 + best["duration"] if initiated else None,
        predicted_destination=(best["destination"] if initiated else positions).tolist(),
        predicted_mask=best["predicted_mask"] if initiated else None,
        predicted_total_J=best["predicted_total_J"] if initiated else stay_J,
        predicted_total_served=best["predicted_total_served"] if initiated else stay_served,
        stay_score=stay, stay_total_J=stay_J, stay_total_served=stay_served,
        selected=selected, candidate_digest=digest, digest_layout=PLAN_DIGEST_LAYOUT.copy(),
        candidate_count=candidate_count, counts=dict(counts))


def enumerate_champions(positions, users, old_mask):
    """Match R's requests, ranks and digest, including nonpositive champions.

    Candidate rows are the full original stationary enumeration, not branch
    returns. Every retained champion is forced into its hypothetical commitment
    even when original R would decline that physical option.
    """
    positions, users = _inputs(positions, users)
    active = mask_bits(old_mask, 8)
    scorer = _Scores(users)
    stay = scorer.score(positions, [int(old_mask)])[0]
    candidates, champions, model_ticks = [], [], 0
    sites = _sites(users)
    for member in np.flatnonzero(~active).tolist():
        best = None
        for site_index, site in enumerate(sites):
            candidate = _transit(positions, member, site, stay)
            masks, scores, index = _mask_choice(scorer, candidate["destination"], member)
            tail, duration = scores[index], candidate["duration"]
            total_J = candidate["transit_J"] + (460 - duration) * tail["J"]
            total_served = candidate["transit_served"] + (460 - duration) * tail["served"]
            candidate.update(member=member, site=site_index, predicted_mask=masks[index],
                tail_score=tail, predicted_total_J=total_J, predicted_total_served=total_served)
            candidates.append([member, site_index, *candidate["offsets"], candidate["descent_ticks"],
                duration, masks[index], total_J, total_served, candidate["path"],
                candidate["transit_J"], candidate["transit_served"], tail["J"], tail["served"],
                tail["quality"], tail["energy_penalty"], *candidate["destination"].reshape(-1)])
            if best is None or stationary_rank(candidate) > stationary_rank(best):
                best = candidate
            model_ticks += duration
        champions.append(best)
    rows = np.asarray(candidates, dtype="<f8").reshape(-1, len(PLAN_DIGEST_LAYOUT))
    digest = hashlib.sha256(rows.tobytes()).hexdigest()
    counts = dict(scorer.counts, model_ticks=model_ticks)
    global_best = max(champions, key=stationary_rank) if champions else None
    return {"original_R": _plan(global_best, positions, stay, digest, counts, len(rows)),
            "champions": [_plan(c, positions, stay, digest, counts, len(rows), force=True)
                          for c in champions],
            "candidate_rows": rows}


def physical_identity(plan):
    """Executed primitive commitment, ignoring aliases between site indices."""
    if plan is None or not plan["initiated"]:
        return "stay"
    commands = np.asarray(plan["commands"], dtype="<f4")
    payload = np.asarray([plan["member"], plan["duration"]], dtype="<i8").tobytes() + commands.tobytes()
    return hashlib.sha256(payload).hexdigest()


def branch_id(plan):
    return "stay" if plan is None or not plan["initiated"] else f"m{plan['member']}_s{plan['site']}"

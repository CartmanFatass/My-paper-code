"""The unchanged R menu, with its remaining-time price at 40 or 120."""
import hashlib
from copy import deepcopy

import numpy as np

from ..b02.option import PLAN_DIGEST_LAYOUT, _inputs, _sites, _transit, _mask_choice
from ..b03.option import enumerate_champions as first_champions, stationary_rank, branch_id, physical_identity
from ..control import _Scores
from ..host import mask_bits


def enumerate_champions(positions, users, old_mask, start_t=40, horizon=500):
    if horizon != 500 or start_t not in (40, 120):
        raise ValueError("the fixed menu is priced only at 40/120 under H500")
    if start_t == 40:
        return first_champions(positions, users, old_mask)
    positions, users = _inputs(positions, users)
    active = mask_bits(old_mask, 8)
    scorer = _Scores(users)
    stay = scorer.score(positions, [int(old_mask)])[0]
    remaining = horizon-start_t
    rows, champions, model_ticks = [], [], 0
    sites = _sites(users)
    for member in np.flatnonzero(~active).tolist():
        best = None
        for site_index, site in enumerate(sites):
            candidate = _transit(positions, member, site, stay)
            masks, scores, index = _mask_choice(scorer, candidate["destination"], member)
            tail, duration = scores[index], candidate["duration"]
            total_J = candidate["transit_J"] + (remaining-duration)*tail["J"]
            total_served = candidate["transit_served"] + (remaining-duration)*tail["served"]
            candidate.update(member=member, site=site_index, predicted_mask=masks[index],
                tail_score=tail, predicted_total_J=total_J, predicted_total_served=total_served)
            rows.append([member, site_index, *candidate["offsets"], candidate["descent_ticks"],
                duration, masks[index], total_J, total_served, candidate["path"],
                candidate["transit_J"], candidate["transit_served"], tail["J"],
                tail["served"], tail["quality"], tail["energy_penalty"],
                *candidate["destination"].reshape(-1)])
            if best is None or stationary_rank(candidate) > stationary_rank(best):
                best = candidate
            model_ticks += duration
        champions.append(best)
    rows = np.asarray(rows, dtype="<f8").reshape(-1, len(PLAN_DIGEST_LAYOUT))
    digest = hashlib.sha256(rows.tobytes()).hexdigest()
    counts = dict(scorer.counts, model_ticks=model_ticks)
    def make_plan(best, force=False):
        stay_J, stay_served = remaining*stay["J"], remaining*stay["served"]
        initiate = best is not None and (force or best["predicted_total_J"] > stay_J)
        selected = None
        if best is not None:
            selected = {k: deepcopy(v) for k, v in best.items() if k not in ("commands", "destination")}
            selected.update(predicted_destination=best["destination"].tolist(), arrival_t=start_t+best["duration"])
        return dict(start_t=start_t, initiated=bool(initiate), member=best["member"] if initiate else None,
            site=best["site"] if initiate else None, offsets=best["offsets"] if initiate else None,
            commands=best["commands"].tolist() if initiate else [], duration=best["duration"] if initiate else 0,
            arrival_t=start_t+best["duration"] if initiate else None,
            predicted_destination=(best["destination"] if initiate else positions).tolist(),
            predicted_mask=best["predicted_mask"] if initiate else None,
            predicted_total_J=best["predicted_total_J"] if initiate else stay_J,
            predicted_total_served=best["predicted_total_served"] if initiate else stay_served,
            stay_score=stay, stay_total_J=stay_J, stay_total_served=stay_served, selected=selected,
            candidate_digest=digest, digest_layout=PLAN_DIGEST_LAYOUT.copy(), candidate_count=len(rows), counts=counts.copy())
    best = max(champions, key=stationary_rank) if champions else None
    return dict(original_R=make_plan(best), champions=[make_plan(c, True) for c in champions], candidate_rows=rows)


def decline(bank, positions):
    plan = deepcopy(bank["original_R"])
    plan.update(initiated=False, member=None, site=None, offsets=None, commands=[], duration=0,
                arrival_t=None, predicted_destination=positions.tolist(), predicted_mask=None,
                predicted_total_J=plan["stay_total_J"], predicted_total_served=plan["stay_total_served"])
    return plan

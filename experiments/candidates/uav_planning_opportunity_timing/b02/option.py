"""Rolling stationary menu using original primitives and remaining-time prices."""

from copy import deepcopy
from dataclasses import dataclass
import hashlib

import numpy as np

from experiments.candidates.uav_fleet_transmission.b02.option import (
    PLAN_DIGEST_LAYOUT, _inputs, _integer, _sites, _transit, _mask_choice,
)
from experiments.candidates.uav_fleet_transmission.b03.option import stationary_rank, branch_id, physical_identity
from experiments.candidates.uav_fleet_transmission.b04.option import decline
from experiments.candidates.uav_fleet_transmission.control import _Scores
from experiments.candidates.uav_fleet_transmission.host import mask_bits

STARTS = tuple(range(40, 191, 10))


@dataclass(frozen=True)
class MenuDependencies:
    scorer: object = _Scores
    sites: object = _sites
    transit: object = _transit
    mask_choice: object = _mask_choice


DEFAULT_DEPENDENCIES = MenuDependencies()


def next_clock(plan, start_t):
    start_t = _integer(start_t, "start_t")
    if start_t not in STARTS:
        raise ValueError("rolling opportunity requires an aligned start40..190")
    if plan is None:
        return start_t + 10
    if not isinstance(plan.get("initiated"), bool) or _integer(plan.get("start_t", start_t), "plan start") != start_t:
        raise ValueError("next clock requires the current explicit commitment")
    if not plan["initiated"]:
        return start_t + 10
    duration = _integer(plan["duration"], "duration")
    arrival = _integer(plan["arrival_t"], "arrival_t")
    if duration not in (10, 20, 30, 40) or arrival != start_t + duration:
        raise ValueError("next clock requires the aligned commanded arrival")
    return arrival + 10


def enumerate_champions(positions, users, old_mask, start_t=40, horizon=500, *, dependencies=DEFAULT_DEPENDENCIES):
    start_t = _integer(start_t, "start_t")
    if horizon != 500 or start_t not in STARTS:
        raise ValueError("rolling menu requires H500 and a scheduled start40..190")
    positions, users = _inputs(positions, users)
    active = mask_bits(old_mask, 8)
    scorer = dependencies.scorer(users)
    stay = scorer.score(positions, [int(old_mask)])[0]
    remaining = horizon - start_t
    rows, champions, model_ticks = [], [], 0
    sites = dependencies.sites(users)
    for member in np.flatnonzero(~active).tolist():
        best = None
        for site_index, site in enumerate(sites):
            candidate = dependencies.transit(positions, member, site, stay)
            masks, scores, index = dependencies.mask_choice(scorer, candidate["destination"], member)
            tail, duration = scores[index], candidate["duration"]
            total_J = candidate["transit_J"] + (remaining - duration) * tail["J"]
            total_served = candidate["transit_served"] + (remaining - duration) * tail["served"]
            candidate.update(member=member, site=site_index, predicted_mask=masks[index], tail_score=tail,
                             predicted_total_J=total_J, predicted_total_served=total_served)
            rows.append([member, site_index, *candidate["offsets"], candidate["descent_ticks"], duration,
                         masks[index], total_J, total_served, candidate["path"], candidate["transit_J"],
                         candidate["transit_served"], tail["J"], tail["served"], tail["quality"],
                         tail["energy_penalty"], *candidate["destination"].reshape(-1)])
            if best is None or stationary_rank(candidate) > stationary_rank(best):
                best = candidate
            model_ticks += duration
        champions.append(best)
    rows = np.asarray(rows, dtype="<f8").reshape(-1, len(PLAN_DIGEST_LAYOUT))
    digest = hashlib.sha256(rows.tobytes()).hexdigest()
    counts = dict(scorer.counts, model_ticks=model_ticks)

    def make_plan(best, force=False):
        stay_J, stay_served = remaining * stay["J"], remaining * stay["served"]
        initiate = best is not None and (force or best["predicted_total_J"] > stay_J)
        selected = None
        if best is not None:
            selected = deepcopy({k: v for k, v in best.items() if k not in ("commands", "destination")})
            selected.update(predicted_destination=best["destination"].tolist(), arrival_t=start_t + best["duration"])
        return dict(start_t=start_t, initiated=bool(initiate), member=best["member"] if initiate else None,
                    site=best["site"] if initiate else None, offsets=best["offsets"] if initiate else None,
                    commands=best["commands"].tolist() if initiate else [], duration=best["duration"] if initiate else 0,
                    arrival_t=start_t + best["duration"] if initiate else None,
                    predicted_destination=(best["destination"] if initiate else positions).tolist(),
                    predicted_mask=best["predicted_mask"] if initiate else None,
                    predicted_total_J=best["predicted_total_J"] if initiate else stay_J,
                    predicted_total_served=best["predicted_total_served"] if initiate else stay_served,
                    stay_score=deepcopy(stay), stay_total_J=stay_J, stay_total_served=stay_served, selected=selected,
                    candidate_digest=digest, digest_layout=PLAN_DIGEST_LAYOUT.copy(), candidate_count=len(rows),
                    counts=counts.copy())

    best = max(champions, key=stationary_rank) if champions else None
    return dict(original_R=make_plan(best), champions=[make_plan(c, True) for c in champions], candidate_rows=rows)

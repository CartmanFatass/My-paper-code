"""Separate TOP/DENSE pair entry and final native-score readout; one newly allocated TOP object."""

import copy
import json
import math
from pathlib import Path
import statistics

from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.geometry import TOP, DENSE, NativeGeometryActor
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import templates


def build_top_pair(seed):
    """Future native learner entry; the encoder-only fixture never calls this."""
    common_actor, common_critic = templates(seed)
    return {
        arm: (NativeGeometryActor(common_actor, arm, 100000 * seed + 12),
              copy.deepcopy(common_critic))
        for arm in (TOP, DENSE)
    }


def reading(delta, complete):
    if not complete:
        return "INCOMPLETE"
    return "TOP_ABOVE_MEI" if delta > .01 else "TOP_ADVERSE" if delta < -.01 else "INSIDE_MEI"


def primary(rows):
    """Read all 32 ordered final 256-step scores per arm, with no H or selection."""
    values = {arm: {} for arm in (TOP, DENSE)}
    errors = {arm: [] for arm in values}
    for row in rows:
        if row.get("phase") != "eval":
            continue
        arm, episode, score = row.get("arm"), row.get("episode"), row.get("J")
        if arm not in values:
            for messages in errors.values():
                messages.append("unknown evaluation arm")
        elif type(episode) is not int or episode not in range(32) or episode in values[arm]:
            errors[arm].append("duplicate or invalid episode index")
        elif type(score) not in (int, float) or not math.isfinite(score) or row.get("steps") != 256:
            values[arm][episode] = None
            errors[arm].append("missing, nonfinite or incomplete J")
        else:
            values[arm][episode] = score
    complete = all(set(values[arm]) == set(range(32)) and not errors[arm] for arm in values)
    ids = sorted(e for e in set(values[TOP]) & set(values[DENSE])
                 if values[TOP][e] is not None and values[DENSE][e] is not None)
    differences = [values[TOP][e] - values[DENSE][e] for e in ids]
    delta = statistics.mean(differences) if complete else None
    return {
        "complete": complete, "reading": reading(delta, complete), "errors": errors,
        "J": {arm: [values[arm][e] for e in sorted(values[arm])] for arm in values},
        "episode_ids": {arm: sorted(values[arm]) for arm in values},
        "TOP_minus_DENSE": {
            "episode_ids": ids, "differences": differences, "complete": complete,
            "mean": delta,
            "conditional_se": statistics.stdev(differences) / math.sqrt(32) if complete else None,
        },
    }


def publish_summary(path, summary):
    """Shared closed-file publication for supplied scores and the bounded fixture."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return path

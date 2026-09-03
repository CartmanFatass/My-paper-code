"""Ordered competence, acquisition, and COUNT/RAW gates."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping

from .contract import ARM_IDS, FLEX_ARMS
from .evaluation import PolicyEvaluation


def apply_gates(
    evaluations: Iterable[PolicyEvaluation],
    *,
    seed_ids: tuple[str, ...],
    final_root_update: int,
    valid_attempt: bool = True,
    host_valid: bool = True,
    support_limited: Mapping[str, bool] | None = None,
    arms: tuple[str, ...] = ARM_IDS,
) -> dict[str, object]:
    """Reduce the exact-oracle competence predicate over the run's own arm inventory.

    Section-11 recast (2026-09-02): this reducer is a *recorded observation*. It never
    refuses, quarantines, or halts a run; the branch label and the per-arm/seed competence
    and acquisition flags it returns are published beside the run whatever their value.
    The acquisition and COUNT/RAW locks it reports are the direction's own sequencing
    choice, not evidence-spec gates.
    """
    values = tuple(item for item in evaluations if item.root_update == final_root_update)
    expected = {(arm, seed, fold) for arm in arms for seed in seed_ids for fold in (0, 1)}
    keyed = {(item.arm_id, item.seed_id, item.fold_id): item for item in values}
    if not valid_attempt or set(keyed) != expected or any(not item.all_finite for item in values):
        return _locked("INVALID_OR_INCOMPLETE", seed_ids, arms)
    if not host_valid:
        return _locked("HOST_NONDISTINGUISHING", seed_ids, arms)
    support_limited = dict(support_limited or {})
    arm_seed_competence = defaultdict(dict)
    arm_seed_acquisition = defaultdict(dict)
    required = 2 if len(seed_ids) >= 3 else len(seed_ids)
    for arm in arms:
        for seed in seed_ids:
            limited = support_limited.get(seed, False)
            both_competent = not limited and all(keyed[(arm, seed, fold)].competence_pass for fold in (0, 1))
            both_acquisition = both_competent and all(keyed[(arm, seed, fold)].acquisition_pass for fold in (0, 1))
            arm_seed_competence[arm][seed] = both_competent
            arm_seed_acquisition[arm][seed] = both_acquisition
    arm_competent = {arm: sum(row.values()) >= required for arm, row in arm_seed_competence.items()}
    arm_acquisition = {
        arm: arm_competent[arm] and sum(arm_seed_acquisition[arm].values()) >= required
        for arm in arms
    }
    unlock = any(arm_competent[arm] and arm_acquisition[arm] for arm in arms if arm in FLEX_ARMS)
    if not any(arm_competent.values()):
        branch = "NO_ARM_COMPETENT"
    elif not any(arm_acquisition.values()):
        branch = "COMPETENT_BUT_NO_ACQUISITION"
    elif unlock:
        branch = "FLEX_COMPETENCE_PLUS_ACQUISITION"
    else:
        branch = "BC_ONLY_ACQUISITION"
    return {
        "branch": branch,
        "arm_seed_competence": dict(arm_seed_competence),
        "arm_seed_acquisition": dict(arm_seed_acquisition),
        "arm_competent": arm_competent,
        "arm_acquisition_positive": arm_acquisition,
        "count_raw_status": "UNLOCK_SEPARATE_B_DESIGN" if unlock else "LOCKED",
    }

def _locked(branch: str, seed_ids: tuple[str, ...], arms: tuple[str, ...] = ARM_IDS) -> dict[str, object]:
    false_seeds = {seed: False for seed in seed_ids}
    return {
        "branch": branch,
        "arm_seed_competence": {arm: dict(false_seeds) for arm in arms},
        "arm_seed_acquisition": {arm: dict(false_seeds) for arm in arms},
        "arm_competent": {arm: False for arm in arms},
        "arm_acquisition_positive": {arm: False for arm in arms},
        "count_raw_status": "LOCKED",
    }

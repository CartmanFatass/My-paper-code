"""Frozen competence, dominance, stable-separation, and branch predicates."""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from typing import Iterable, Mapping

from .contract import ARM_IDS
from .evaluation import CheckpointEvaluation, SupportEvaluation

RAW, WHITENED = ARM_IDS


def materially_dominates(left: SupportEvaluation, right: SupportEvaluation) -> bool:
    nonworse = left.root_hamming <= right.root_hamming and left.regret_fraction <= right.regret_fraction and left.agreement_fraction >= right.agreement_fraction
    material = left.root_hamming <= right.root_hamming - 1 or left.regret_fraction <= right.regret_fraction - Fraction(1, 50) or left.agreement_fraction >= right.agreement_fraction + Fraction(1, 20)
    return bool(nonworse and material)


def reduce_results(evaluations: Iterable[CheckpointEvaluation], *, seed_ids: tuple[str, ...], final_update: int) -> dict[str, object]:
    values = tuple(evaluations)
    keyed = {(item.arm_id, item.seed_id, item.fold_id, item.root_update): item for item in values}
    expected = {(arm, seed, fold, update) for arm in ARM_IDS for seed in seed_ids for fold in (0, 1) for update in sorted({item.root_update for item in values})}
    if set(keyed) != expected:
        raise ValueError("evaluation combination inventory mismatch")
    required_seed_count = 2 if len(seed_ids) == 3 else len(seed_ids)
    seed_even, seed_odd, seed_near = defaultdict(dict), defaultdict(dict), defaultdict(dict)
    for arm in ARM_IDS:
        for seed in seed_ids:
            seed_even[arm][seed] = all(keyed[(arm, seed, fold, final_update)].even.competence for fold in (0, 1))
            seed_odd[arm][seed] = all(keyed[(arm, seed, fold, final_update)].odd.competence for fold in (0, 1))
            seed_near[arm][seed] = all(keyed[(arm, seed, fold, final_update)].odd.odd_near for fold in (0, 1))
    arm_competent = {arm: sum(seed_even[arm].values()) >= required_seed_count for arm in ARM_IDS}
    checkpoints = sorted({item.root_update for item in values})
    paired = {}
    clear = {}
    for update in checkpoints:
        rows = []
        for seed in seed_ids:
            for fold in (0, 1):
                whitened = keyed[(WHITENED, seed, fold, update)].even; raw = keyed[(RAW, seed, fold, update)].even
                rows.append({"seed_id": seed, "fold_id": fold, "whitened_dominates": materially_dominates(whitened, raw), "raw_dominates": materially_dominates(raw, whitened)})
        paired[str(update)] = rows
        clear[str(update)] = sum(row["whitened_dominates"] for row in rows) >= 4 and sum(row["raw_dominates"] for row in rows) <= 1 if len(rows) == 6 else False
    stable = bool(clear.get("160", False) and clear.get("320", False))
    positive = bool(arm_competent[WHITENED] and not arm_competent[RAW] and stable)
    falsifier = bool(not arm_competent[WHITENED] and not stable)
    both_all_noncompetent = all(not value for arm in ARM_IDS for value in seed_even[arm].values())
    no_odd_signal = all(not value for arm in ARM_IDS for row in (seed_odd[arm], seed_near[arm]) for value in row.values())
    contrary = bool(both_all_noncompetent and no_odd_signal and not stable)
    return {
        "arm_seed_even_competence": dict(seed_even), "arm_seed_odd_competence": dict(seed_odd), "arm_seed_odd_near": dict(seed_near),
        "arm_competent": arm_competent, "paired_dominance": paired, "clear_whitened_advantage": clear,
        "stable_clear_advantage_160_320": stable, "conditioning_positive": positive,
        "falsifier": falsifier, "contrary_park_observation": contrary,
        "paid_acquisition_status": "UNEVALUATED_LOCKED", "count_raw_status": "LOCKED_UNTIL_COMPETENCE",
    }

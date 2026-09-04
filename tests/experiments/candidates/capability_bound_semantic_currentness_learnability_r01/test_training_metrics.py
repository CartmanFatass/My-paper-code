from __future__ import annotations

from fractions import Fraction

import torch

from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.codecs import CodecArm
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.host import panel
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.initialization import initialized_learner
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.metrics import (
    AUC_WEIGHTS,
    normalized_auc,
    toggle_counts,
)
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.support import Purpose, Split
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.training import (
    _materialize,
    evaluate_adaptation_free,
)


def test_auc_literal_weights_and_exact_reduction() -> None:
    assert AUC_WEIGHTS == (1 / 16, 1 / 8, 3 / 16, 3 / 8, 1 / 4)
    assert sum(AUC_WEIGHTS) == 1.0
    curve = [float(value) for value in (5, 4, 3, 2, 1)]
    assert normalized_auc(curve) == sum(w * v for w, v in zip(AUC_WEIGHTS, curve))


def test_untrained_evaluation_is_adaptation_free_and_first_max() -> None:
    contexts = panel(Purpose.MAIN, 0, Split.EVAL)
    inputs, _ = _materialize(contexts, CodecArm.STRUCT)
    model = initialized_learner(Purpose.MAIN, 0)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, betas=(0.9, 0.999), eps=1e-8)
    evaluation = evaluate_adaptation_free(model, optimizer, contexts, inputs, update=0)
    assert evaluation.state_unchanged
    assert evaluation.finite
    assert set(evaluation.choices) == {0}
    assert not any(evaluation.strict)
    assert len(evaluation.regrets) == 768
    counts = toggle_counts(evaluation, contexts)
    assert set(counts) == {
        "neutral_active", "persist_refresh", "correct_swapped", "open_gated",
        "owner_live_broken", "authentic_reassociated",
    }
    assert all(0 <= count <= 16 for pair in counts.values() for count in pair)

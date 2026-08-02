"""V-K0D CONTROL arm — current roster encoding, per-check randomized order.

`docs/research/designs/VK0D_REALIZATION_DECISION_LEDGER.md` VD-6 / A-VD-3, the
mandatory simpler control against which the PRIMARY structural correction is
read.

Everything except the field below is inherited verbatim from
`config_d7_2b_toy_learned_keep`, the V-K0D REFERENCE arm — see the matched
exposure note in `config_d7_2b_toy_conjugate_keep`. This arm's sole
pre-training difference is its order schedule; the encoder is the unchanged
absolute-ID one.
"""

from __future__ import annotations

from config_d7_2b_toy_learned_keep import Config as ReferenceConfig


class Config(ReferenceConfig):
    """CONTROL: absolute-ID roster + uniform-per-check serialization."""

    scenario_label = "d7_2b_toy_randorder_keep"
    high_controller = "r30_fixed_clock_ar_edit"
    r30_training_order_policy = "uniform_per_check"

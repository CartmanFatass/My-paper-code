"""V-K0D PRIMARY arm — anonymous-OTHER roster encoding, canonical order.

`docs/research/designs/VK0D_REALIZATION_DECISION_LEDGER.md` VD-6 / A-VD-3.

Everything except the two fields below is inherited verbatim from
`config_d7_2b_toy_learned_keep`, the V-K0D REFERENCE arm. That inheritance is
the mechanism, not a convenience: A-VD-6 and VD-7 require the three arms to be
matched exactly on model geometry, optimizer budget, environment interactions
and exact interaction/update counts, and a subclass cannot drift from those
numbers the way a duplicated 150-line file can. The only pre-training
difference this arm carries is the anonymous-encoding flag, which reaches the
policy through the controller string (`StandaloneProcessAgent` maps it to
`FixedClockAREditPolicy(conjugate_context=True)`).
"""

from __future__ import annotations

from config_d7_2b_toy_learned_keep import Config as ReferenceConfig


class Config(ReferenceConfig):
    """PRIMARY: relative/anonymous OTHER roster + canonical serialization."""

    scenario_label = "d7_2b_toy_conjugate_keep"
    high_controller = "r30_fixed_clock_ar_edit_conjugate"
    r30_training_order_policy = "canonical"

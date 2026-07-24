# Active-set-centered delayed residual G20 screen

Date: 2026-07-24

The exact integrated source
`81708930883edad1fc3bd0f826b64b0b462a6857` completed the bounded screen at
`logs/nonformal_active_set_centered_residual_g20_20260724_8170893_pm1`.

```text
formal=false
backend=cpu
torch=2.7.0+cpu
torch_threads=1
status=COMPLETE
operational_valid=true
maximum_replay_error=2.9103830456733704e-10
maximum_anchor_difference=0.0
maximum_centering_error=2.9103830456733704e-10
source_controls_valid=true
branch=NONFORMAL_NO_DELAYED_ACCESS_CENTERED_RESIDUAL_G20
wall_seconds=467.0216296
```

Project Manager independently closed source/runtime identity, finite updates,
lifecycle/source controls, replay, anchor identity and the registered
first-match branch.

## Evidence

The centered residual preserves every G17 gate:

```text
g17_anchor_iid_utility=0.9435338343
g17_final_iid_utility=0.9435325476
g17_anchor_heldout_utility=0.9442790014
g17_final_heldout_utility=0.9442779224
g17_gain_over_zero=0.7541791785
g17_minimum_episode=0.9118961081
g17_effort_correlation=0.9832264452
g17_mix_correlation=0.9923362686
g17_effort_mae=0.0187116468
g17_mix_mae=0.0208566937
```

The G18 residual is exercised but obtains no delayed access:

```text
g18_anchor_utility=0.5833333333
g18_final_utility=0.5833333333
g18_gain_over_anchor=0.0
g18_spike_utility=0.0
g18_rotating_effort_share=0.4959656006
g18_minimum_step_utility=0.0
g18_residual_output_max_abs=0.0020525125
```

The active-coordinate sum error remains below `3e-10`, inactive/replay fields
close, and the frozen anchor has zero drift. The failure is therefore
scientific, not an implementation or source-identifiability failure.

## Disposition

G20 retains the G19 anchor lemma and shows that an active-set-zero-mean
pre-squash residual is sufficient to preserve the immediate controller. It
rejects the stronger claim that redistribution-only action-mean freedom is
sufficient for the delayed battery source. The exact candidate is retired
without optimizer, budget, seed, threshold or same-package tuning and does not
advance to formal compute or UAV.

The smallest discriminator removes only the active-set centering while keeping
the frozen anchor, exact-zero initialization, successor credit, SGD, budgets,
seeds policy and first-match gates. This tests whether delayed control requires
a common-mode component before changing optimizer or credit.

```text
conclusion_bearing_iteration_cost=0
iterations_remaining=8
next_boundary=UNCONSTRAINED_ANCHORED_DELAYED_RESIDUAL_G21_DERIVATION
```

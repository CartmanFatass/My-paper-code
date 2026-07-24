# Active-set centered counterfactual residual G20

```text
status=DESIGN_FROZEN_BOUNDED_SCREEN
algorithm=ACTIVE_SET_CENTERED_COUNTERFACTUAL_RESIDUAL_G20
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Scientific basis and declared estimator class

This design realizes the P2 candidate made eligible by
`docs/research/cdc/EVIDENCE_NOTES/20260724_TIMING_CREDIT_IDENTIFIABILITY_G20_DERIVATION.md`
under the untied-k bootstrap round's pre-registered reactivation conditions.
The derivation established that the registered G18 delayed direction lies in
the anonymous active-set-centered action subspace and that no schedule of
shared-scalar credit is member-resolved.

The slow credit estimator is therefore declared, per the adopted taxonomy, as
a **per-agent counterfactual (marginal) advantage**: a leave-one-out contrast
on a learned slow action-critic. It is not a shared team advantage, not an
option-level difference return, and not a value-decomposition target.

Declared scope (Q4): the centered-authority claim is valid only for sources
whose delayed-optimal allocation preserves the immediate aggregate. The
registered G18 source is inside this scope; the common-mode-reduction
counterexample class is outside it and no claim extends there.

## Executable algorithm boundary

`ACTIVE_SET_CENTERED_COUNTERFACTUAL_RESIDUAL_G20` retains the G17
continuous-roster actor as a trained-then-frozen fast path, exactly as the
closed G19 package did. It differs from closed G19 in precisely two ways, and
reopens nothing else:

1. **Action-space authority decomposition replaces gradient projection.**
   The delayed head is an observation-only residual applied to the pre-tanh
   action mean and **exactly centered over the active set** at every
   environment step: with raw per-member outputs `f(o_i)` and active count
   `N`, member `i` receives `f(o_i) - (1/N) * sum_{j active} f(o_j)`. The
   applied residual therefore sums to zero over the active set per action
   coordinate, per batch row, at every step. Inactive rows receive no
   residual. There is no gradient projection anywhere; G19's projection is
   deleted from this candidate, not reused.
2. **Member-resolved slow credit replaces the shared scalar channel.**
   A slow action-critic `Q_slow(critic_state, active_mask, R_t)` receives the
   masked centered-residual table `R_t` (the applied pre-tanh residual rows,
   flattened over capacity) and regresses the discounted slow return
   (`gamma=0.99`, `lambda`-free, terminal bootstrap zero — the same return
   construction as the closed G19 slow-return target). The per-member
   advantage is the detached leave-one-out contrast

   ```text
   A_slow[i, t] = Q_slow(s_t, R_t) - Q_slow(s_t, R_t with row i zeroed)
   ```

   attached to member `i`'s token log-probability in a PPO clip surrogate.
   The advantage tensor is `[time, batch, member]`, normalized over active
   tokens only (masked mean and unbiased=False std over all active tokens in
   the update batch, epsilon `1e-8`). No shared scalar advantage multiplies
   residual-channel score functions anywhere.

Everything else is unchanged from the accepted surfaces: the fast actor,
recurrent transition, routing order, action factorization, tanh-Gaussian
sampling, exploration scale, sources, rewards, observations, active masks,
lifecycle contracts and exact teacher-replay semantics. The base
`ContinuousRosterPolicy` file is not modified; the subclass overrides
`forward_step` to compute the per-step centered table and the existing
`_action_mean_for_member` hook to apply it.

### Phases, parameters and optimizers

- **Fast phase** — identical in structure to the closed G19 fast phase: the
  base policy (residual head zero-initialized and frozen) trains with the
  immediate-reward-minus-baseline advantage; base critic frozen; the
  immediate baseline head trains alongside.
- **Delayed phase** — begins exactly once, requires the residual output layer
  exactly zero at entry, freezes every fast parameter including `log_std` and
  the baseline heads, and enables only the residual head and `Q_slow`. The
  delayed actor loss is the member-resolved PPO surrogate above; the only
  other delayed loss is the `Q_slow` clipped regression. Neither touches any
  fast parameter.
- **Optimizers** — Adam for every trainable group in both phases. G19's SGD
  requirement existed only to preserve the projection's first-order sign;
  with the projection deleted the rationale does not transfer.

### Why no projection is needed

Fast-parameter retention is architectural (disjoint parameters, frozen fast
path) and aggregate retention is functional (the centered subspace carries no
common mode where no clip binds). The screen measures both retentions; it
does not assume them.

## Bounded screen

The paired dual-source protocol, phase counts, evaluation sizes and
thresholds mirror the registered G19 screen exactly; only the mechanism and
seeds differ. Zero conclusion-bearing iterations.

```text
replicates=1
num_envs=8
ppo_passes=2
g17_fast_updates=100
g17_delayed_updates=100
g18_fast_updates=100
g18_delayed_updates=300
g17_eval_episodes_per_domain=48
g18_slot_permutations=3
formal=false
```

Fresh screen seeds, fixed before execution, disjoint from every earlier
package:

```text
g17_model=2619000
g17_train_ledger=2629000
g17_action=2639000
g17_evaluation_ledger=2649000
g17_evaluation_action=2659000
g18_model=2719000
g18_action=2739000
```

First-match result system:

1. `INVALID_CENTERED_COUNTERFACTUAL_RESIDUAL_G20` on operational, replay,
   lifecycle, source-control, centering, zero-residual-equivalence or
   gradient-ownership failure;
2. `NONFORMAL_NO_G17_COMPATIBILITY_CENTERED_RESIDUAL_G20` unless final G17
   IID and held-out means are at least `0.90`, gain over zero at least
   `0.10`, minimum episode at least `0.80`, both mapping correlations at
   least `0.90`, and both MAEs at most `0.05`;
3. `NONFORMAL_NO_DELAYED_ACCESS_CENTERED_RESIDUAL_G20` unless final G18
   utility is at least `0.95`, gain over its frozen fast anchor at least
   `0.10`, and spike utility is at least `0.90`;
4. `NONFORMAL_NO_DELAYED_MECHANISM_CENTERED_RESIDUAL_G20` unless
   rotating-member low-phase effort share is at least `0.75`; or
5. `NONFORMAL_CENTERED_COUNTERFACTUAL_RESIDUAL_PROMISING_G20`.

Only branch 5 licenses preparing a formal contract. No branch supports a UAV
claim, a variable-period claim, or reopening any closed candidate. There is
no same-package retry or hyperparameter sweep.

## Proof-sized acceptance

- exact zero-residual equivalence to the base policy under deterministic,
  sampled and teacher-replay modes;
- exact active-set centering: the applied residual sums to zero over active
  members per coordinate and batch row (tolerance `1e-6`), and inactive rows
  receive exactly zero residual;
- member-resolved credit: on a fixed synthetic `Q_slow`, the leave-one-out
  advantage matches direct evaluation and differs across members;
- gradient ownership: the delayed actor loss and `Q_slow` regression have
  exactly no gradient on fast actor parameters, `log_std`, base critic or
  baseline heads; `Q_slow` regression has no gradient on the residual head;
- exact replay and inactive-row zero likelihood on both G17 and G18 with a
  nonzero residual active;
- one finite update per phase; the delayed phase begins exactly once with an
  exactly zero residual output layer;
- first-match branch precedence.

## Files

- `ha_ctse_process/centered_residual_g20.py` — policy subclass, `Q_slow`,
  member-resolved credit, both update rules;
- `scripts/screen_centered_counterfactual_residual_g20.py` — bounded paired
  screen runner writing `result.json` under
  `logs/nonformal_centered_counterfactual_residual_g20_<date>_<commit>_pm1/`;
- `tests/ha_ctse_process_centered_residual_g20_test.py` — focused proofs
  above.

`ha_ctse_process/continuous_roster_policy.py`, both source modules, the
closed G17/G18/G19 runners and every closed result remain unchanged evidence
at their Git commits.

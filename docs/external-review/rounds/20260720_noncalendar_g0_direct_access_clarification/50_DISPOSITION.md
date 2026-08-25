# Retracted Disposition — Noncalendar Direct-Access Clarification

## Decision

`RETRACT_D0_D1_OBJECTIVE_INVERSION`

The focused Convergent response in `41_PRO_CONVERGENT_RAW.md` remains immutable
reviewer evidence, but its selected route is retracted before implementation or
compute. It converted ordinary-controller access from a matched comparator and
diagnostic into a prerequisite for studying the hierarchy, skill and
variable-lifetime mechanisms intended to build a stronger MARL algorithm. That
is an inversion of the project objective.

The completed source remains valid `NO_ACCESS_BENCHMARK_ORDINARY_CONTROL`; it is
not rerun, repaired or relabeled. This retraction changes only the successor
authority. The detailed D0/D1 contract below is retained solely to identify the
retracted proposal; it has no active implementation or experiment authority.

## Retracted causal edge

Compare two ordinary recurrent primitive controllers under the same task,
information authority, lifecycle, action distribution, external reward,
optimizer, exposure, seeds and evaluation:

- `D0`: the existing 15-field demand-visible ordinary controller;
- `D1`: replace only the organization of current causal demand information by
  removing aggregate demand/error fields from the actor observation and using
  explicit focal-local demand-transition encoding
  `(x_i/2, g_i/2, (g_i-x_i)/4, delta_g_i/4)` together with the retained local
  `target_changed`, previous thrust, action-run length, anonymous active-set
  size and pooled active-set representation.

`delta_g_i = g_i,t - g_i,t-1`, normalized by four to `[-1,1]`. It is current
causal information derivable from the existing target history, not future
demand or an increase in information authority.

The treatment is one observation-schema factorization replacement. It does not
add a skill, option, high controller, intrinsic reward, posterior, graph,
communication mechanism, latent, hazard or new critic.

## Frozen learner and lifecycle contract

- Retain the primitive autoregressive distribution over `{-1,0,+1}`, earlier
  action prefix, lifecycle GRU width 32, centralized value path, PPO/GAE,
  terminal-only external utility and existing replay/checkpoint/RNG semantics.
- JOIN continues to initialize new physical and recurrent state to zero;
  temporary absence freezes state; REJOIN restores it; terminal LEAVE deletes
  it after finalization. The clarification's phrase about not resetting JOIN
  cannot override this already frozen anonymous-lifecycle contract.
- D0 and D1 start from matched zero-step initialization. No pretrained or best
  D checkpoint is used.
- Parameter counts must be within one percent; inert parameter padding is
  allowed only for accounting and must not affect forward or gradient flow.

## Registered exposure and evaluation

Per arm:

- CUDA, 16 environments, horizon 80;
- 250 updates, 320,000 transitions, 1,000 optimizer steps, 4,000 episodes;
- Adam `3e-4`, gamma `0.99`, GAE lambda `0.95`, four PPO epochs, gradient clip
  `0.5`;
- model initialization `58058`, training ledger `68058`, order `78058`, action
  `88058`, IID evaluation `98058`, held-out evaluation `99058`, bootstrap
  `108058`;
- training durations `{5,9,13}` and held-out durations `{5,7,9}`;
- 10,000 paired bootstrap repetitions clustered by `base_id`;
- unchanged IID/held-out deterministic and stochastic evaluation cells.

D1 access requires held-out deterministic tracking/completion/utility at least
`0.72/0.85/0.78` and a paired D1-minus-D0 utility 95% lower bound greater than
`0.10`.

## Result branches

- `INVALID_D1_OBSERVATION_CONTRACT`: replay, mask, checkpoint, information
  leakage or implementation failure; repair only the failed engineering path.
- `D1_PASS_OBSERVATION_ACCESS`: M0 passes, all absolute D1 access floors pass,
  and D1-minus-D0 utility LCB is greater than `0.10`; observation/data-flow
  explanation gains support and temporal-necessity weight falls.
- `D1_NO_GAIN`: M0 passes but D1 does not materially exceed D0; simple local
  factorization is rejected while ordinary access remains unresolved.
- `D1_FAIL_WITH_VALID_ACCESS`: M0 passes and D1 moves materially but misses the
  absolute access contract; ordinary access remains absent and hierarchy is not
  promoted.

If neither ordinary arm establishes access, stop this benchmark algorithm line
without model, seed, budget, reward, threshold or intrinsic rescue.

## Active boundary

No code, focused check or formal compute is authorized from this disposition.
The Code Implementation Manager stopped and the retracted files were removed.
The active controller must obtain one Research Project Manager alignment brief
and return the exact objective-inversion conflict to Convergent Pro for a
focused correction. The corrected route must advance a stronger MARL algorithm;
ordinary MARL may remain a matched comparator or diagnostic but not a universal
admission gate.

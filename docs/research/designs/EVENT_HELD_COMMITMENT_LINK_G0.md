# EVENT_HELD_COMMITMENT_LINK_G0

Status: CONTROLLER_ADOPTED_SOURCE
Source commit: `356d0dbb407b928bd108cc7d334452d08fc92801`
Adopted: 2026-07-20

## Scientific purpose

Test one causal link for a stronger anonymous MARL algorithm with runtime-
variable membership and learned variable individual lifetime:

```text
event-held commitment reaches primitive action selection
  -> natural persistent individual lifetimes and useful state visitation
  -> held-out external utility
```

Ordinary recurrent MARL remains the strongest matched comparator and access
null. It is not an admission gate.

## Arms and estimands

- `OR`: byte-identical source-commit ordinary recurrent actor, critic,
  primitive distribution and PPO.
- `DUM`: adds the complete commitment/event machinery but fixes treatment bit
  `m=0`, so commitment cannot change primitive logits.
- `EHC`: identical to `DUM` except `m=1`.

The only treatment is:

```text
primitive_logits = base_logits + W_z(m * z)
```

Primary estimand:

```text
G = E[U_EHC - U_DUM]
```

Secondary complete-algorithm estimand:

```text
V = E[U_EHC - U_OR]
```

## Architecture and capacity control

Preserve `OR` exactly. `DUM/EHC` add:

- bias-free `W_z: 8 -> 3`, 24 parameters;
- categorical event head `Linear(87,2)`, 176 parameters;
- continuous mark head `Linear(87,16)`, 1,408 parameters;
- total added trainable actor parameters: 1,608 in both arms.

Event heads read `stopgrad([o_15,h_64,z_8])`. The critic is byte-identical and
does not read `z`. Event heads share no parameters or gradients with the base
trunk. Copy the `OR` base before initializing additions from a dedicated RNG.

## Event and lifecycle state machine

- At genuine `JOIN`, initialize `h=0`, force `CREATE`, draw the mark, draw
  `Delta` uniformly from `{4,8,12}` on a dedicated opportunity RNG and set
  `q=Delta`.
- Every active primitive transition decrements `q` once.
- `q=0` causes one opportunity before the next active primitive action.
- Policy support at later opportunities is exactly `{KEEP, RENEW}`.
- `KEEP` preserves `z`, segment ID and segment start, and resamples only `q`.
- `RENEW` closes the prior complete segment, increments segment ID, samples a
  new mark and `q`, and starts a new segment.
- Terminal `LEAVE` and episode end force `CLOSE` outside policy support with no
  categorical likelihood.
- Temporary `LEAVE` freezes `h,z,q` and the open segment; inactive time does not
  decrement `q`.
- `REJOIN` restores the lifecycle and handles a due `q=0` opportunity before
  its next action.
- Forced close occurs after the final reward, right-censors the segment, then
  deletes lifecycle state.
- Rollout cutoff is not an event. `h,z,q`, segment and lifecycle state continue;
  `h` is detached identically in all arms and nonterminal GAE bootstraps from
  the unchanged critic.
- Lifecycle keys exist only in the ledger and never enter policy inputs.

## Probability and credit

`CREATE/RENEW` draw non-reparameterized:

```text
u ~ Normal(mu, diag(sigma^2))
sigma = 0.1 + 0.9 * sigmoid(s)
z = tanh(u)
```

Mark log probability uses the transformed density:

```text
Normal.log_prob(u) - sum(log(1 - tanh(u)^2))
```

implemented with a stable log-sech-squared expression. `KEEP` has categorical
log probability only; `RENEW` has categorical plus mark log probability.
Forced `CREATE` has no categorical factor but its sampled mark remains a policy
factor. Forced `CLOSE` has no policy factor.

Use unchanged primitive PPO/GAE with `gamma=0.99`, `lambda=0.95`. An eligible
event row uses the same advantage as the primitive action it precedes. `z` is a
detached sampled action value and never backpropagates into the event heads;
event/mark policies learn only through score-function PPO ratios.

Use separate Adam optimizers for base and event parameters:

- learning rate `3e-4`;
- epsilon `1e-5`;
- weight decay `0`;
- clip `0.2`;
- separate gradient-norm clip `0.5`.

Base loss is primitive clipped PPO plus `0.5` value loss minus `0.01` primitive
entropy. Event loss is clipped PPO minus `0.01` categorical entropy with zero
mark-entropy bonus. Each update collects `16 x 80` recurrent rows and performs
four full-sequence epochs. Total exposure is 1,000 base optimizer steps in every
arm and 1,000 event steps in `DUM/EHC`, reported separately.

## Replay and checkpoint contract

Primitive rows store `o,h_pre,z_pre,action,old_logp,value,reward`, terminal,
bootstrap and active masks, lifecycle/epoch/segment/`q`, plus all owned RNG
state. Eligible event rows store kind, input, categorical action, `u`, new `z`,
component and joint old log probabilities. Recomputed eligible component and
joint log probabilities must have maximum absolute error `<=1e-6`.

Checkpoint only at update boundaries with an empty rollout buffer. Save every
model, optimizer and counter; normalizers or an explicit none marker; complete
simulator, environment and membership state; Python, NumPy, CPU/CUDA and every
ledger/opportunity/event/mark/primitive RNG; all `h,z,q`, segment and lifecycle
tables; masks, collector/update/episode positions and accumulators. Reload must
reproduce one rollout and one update with exact discrete/RNG equality and
continuous, log-probability and parameter error `<=1e-7`. Evaluate only
`update_250.pt`.

## Formal experiment contract

Run five paired training replicates, `r=0..4`, only after separate controller
authorization. Per arm and replicate:

- 16 environments;
- horizon 80;
- 250 updates;
- 320,000 transitions and 4,000 episodes;
- 1,000 base optimizer steps;
- 1,000 event steps for `DUM/EHC`, zero for `OR`.

Seeds add `1000*r` to:

- initialization `58058`;
- ledger `68058`;
- order `78058`;
- primitive `88058`;
- opportunity `90058`;
- event `92058`;
- mark `94058`;
- IID evaluation `98058`;
- held-out evaluation `99058`.

Bootstrap seed is `108058`. Evaluate `update_250.pt` using 256 IID deterministic,
256 IID stochastic, 256 held-out deterministic and 256 held-out stochastic
episodes per replicate and arm. Deterministic execution uses categorical
argmax, `z=tanh(mu)` and the existing deterministic primitive rule.

Use the unchanged G0 utility `U`; absolute access floor is `0.78`. For every
estimand use 10,000 paired hierarchical bootstrap repetitions: resample the five
training-seed triples, then whole paired episode IDs within each seed. Preserve
all agents, events and censored segments. Use percentile 95% intervals and
strict inequalities.

Natural-use conditions on held-out stochastic non-CREATE opportunities:

- `LCB(P_KEEP) > 0.20`;
- `LCB(P_RENEW) > 0.10`.

Complete lifetime is active primitive steps from `CREATE/RENEW` until `RENEW`.
Temporary absence and rollout cutoff do not end it; forced close is censored.
Require:

- `LCB(CV(T)) > 0.25`;
- at least two of `[1,8]`, `[9,16]`, `[17,infinity]` have
  `LCB(proportion) > 0.10`.

For intervention, use held-out stochastic decision states with at least two
active lifecycles. Derange `z` across lifecycles while holding `o,h`, environment
and primitive RNG fixed, and compute:

```text
I = mean(||W_z(z - z_perm)||_2 / sqrt(3))
```

Require `LCB(I) > 0.10`. Evaluation is identifiable only with at least 1,000
non-CREATE opportunities and 250 lifecycles containing at least two such
opportunities across the five seeds.

## Mutually exclusive result branches

Apply in order:

1. `INVALID_OPERATIONAL`: probability, replay, no-op, lifecycle, RNG or resume
   invariant fails. Repair once under the identical contract; no scientific
   iteration is consumed.
2. `BENCHMARK_NON_IDENTIFIABLE`: either exposure floor is missed. Close this G0
   source without mechanism inference.
3. `NO_ACCESS_THIS_BENCHMARK`: maximum arm utility UCB is below `0.78`. Close
   only this comparison; do not veto stronger-MARL work.
4. `UNDERPOWERED_ACCESS`: maximum arm LCB is below `0.78` while UCB reaches it.
   Close under the frozen budget with no rescue.
5. `COMMITMENT_SUPPORTED`: access established, `LCB(G)>0.10`, and every natural
   use, lifetime and intervention condition passes. This authorizes controller
   consideration of integration, not automatic integration.
6. `REPRESENTATION_ONLY`: `LCB(G)>0.10` but behavior confidently fails. Retire
   the variable-lifetime claim.
7. `ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED`: `UCB(G)<=0.10`. Retire the
   EHC link; any matched-control deviation is operational invalidity rather
   than capacity evidence.
8. `MIXED_UNDERPOWERED`: every remaining valid numerical pattern. Close this
   source without integration or rescue.

## Prohibited changes

No environment-specific intrinsic reward, task shaping, identity/role input,
skill catalogue, duration action, learned hazard or terminate action, graph,
team latent, communication module, new credit objective, ordinary-access
admission gate, or post-result change to reward, observation, G0 distribution,
base PPO, budget, seed or threshold.

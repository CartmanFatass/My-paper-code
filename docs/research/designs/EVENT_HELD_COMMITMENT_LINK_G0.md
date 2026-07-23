# EVENT_HELD_COMMITMENT_LINK_G0

Status: PREREGISTERED_EXECUTABLE_CONTRACT_NOT_AUTHORIZED
Executable source commit: `1cc6552a00c06bc7389235a4474ca0005c4ca9b6`
Canonicalized: 2026-07-23

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

## Replay, typed evidence and checkpoint contract

Primitive rows store `o,h_pre,z_pre,action,old_logp,value,reward`, terminal,
bootstrap and active masks, lifecycle/epoch/segment/`q`, plus all owned RNG
state. Eligible event rows store kind, input, categorical action, `u`, new `z`,
component and joint old log probabilities.

Replay validation uses the executable named contract: exact support, mask,
detach and action fields; mixed absolute-relative and ratio gates for each
likelihood component; state bounds; support-leak checks; and compositional
primitive/event joint assembly. Any non-finite leaf fails closed. Derived
critic and likelihood records remain separate from causal state and must pass
their recomputable replay validators.

Every selected source-natural pair carries
`event_held_commitment_link_g0.causal_audit.v2`. The validator rederives exact
structural fields, native-dtype causal float/payload bits, complete outcomes,
RNG schedules/variates/end states, executed event/mark/primitive kernels and
bijective pair binding. A validly bound causal-field or executed-kernel mismatch
with every operational and derived guard valid yields `unavailable`; malformed
binding, instrumentation, RNG, schema, discrete state, segment, outcome,
finiteness or derived evidence is `INVALID_OPERATIONAL`.

Evidence publication uses immutable SHA-256 root-relative update shards and
evaluation-cell references: train manifest/index/update schema versions
`6/3/2`, evaluation manifest/cell versions `6/9`, formal train artifact v6,
formal evaluation artifact v9 and formal analysis artifact v6. Temporary files
are forbidden at a terminal boundary.

Checkpoint only at update boundaries with an empty rollout buffer. Save every
model, optimizer and counter; normalizers or an explicit none marker; complete
simulator, environment and membership state; Python, NumPy, CPU/CUDA and every
ledger/opportunity/event/mark/primitive RNG; all `h,z,q`, segment and lifecycle
tables; masks, collector/update/episode positions and accumulators. Reload must
reproduce one rollout and one update with exact discrete/RNG equality and the
registered continuous, replay and parameter tolerances. Evaluate only
`update_250.pt`.

## Formal experiment contract

The executable object is branch `Claude`, source commit
`1cc6552a00c06bc7389235a4474ca0005c4ca9b6`, on the registered CPU backend with
one Torch intra-op thread. Run five paired training replicates, `r=0..4`, only
after separate Controller authorization. Per arm and replicate:

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

The held-out stochastic cell is conclusion-bearing. Use unchanged utility `U`;
absolute access floor is `0.78`. Primary `G=E[U_EHC-U_DUM]`; secondary
`V=E[U_EHC-U_OR]`. For every estimand use 10,000 paired hierarchical bootstrap
repetitions: resample the five training-seed triples, then whole paired episode
IDs within each seed. Preserve all agents, events and censored segments. Use
strict percentile 95% intervals.

The canonical behavior and consequence battery is:

- raw KEEP/RENEW rates are diagnostics; require at least 128 eligible KEEP and
  128 eligible RENEW rows;
- lifetime is the number `K` of policy opportunities in a complete spell, with
  bins `K==1`, `K==2`, `K>=3`; at least two bin proportions require
  `LCB95 > 0.10`;
- physical lifetime, its CV and physical-time bins are descriptive only;
- intervention is primitive-action-distribution total variation under the
  registered same-state mark intervention, requiring `LCB95(TV) > 0.10`;
- same-state exact-snapshot CRN forcing produces `C_total`, `C_timing` and
  `C_mark` for each naturally selected action. `C_total` compares the natural
  action's held/candidate continuation against its forced alternative;
  `C_timing` holds the renewal candidate deranged as registered; `C_mark` is the
  remaining component, with binary64 additivity checked against its
  deterministic ULP-derived bound;
- both `LCB95(C_total|KEEP) > 0` and
  `LCB95(C_total|RENEW) > 0`, and both corresponding means must be at least
  `0.02`.

Evaluation is identifiable only with at least 1,000 non-CREATE opportunities,
250 multi-opportunity lifecycles, both 128-row natural
support floors and exactly 32 selected KEEP plus 32 selected RENEW audit rows
in every replicate. The audit budget is 320 selected rows and 960 three-branch
continuation rows total. Quotas cannot be lowered, pooled across replicates,
topped up or selectively retained.

The two point floors are not part of the confident-failure dual. Clearing the
interval gates while missing a point floor is mixed/underpowered, not a
confident negative. `C_timing` and `C_mark` are preregistered diagnostics and do
not alter the executable result branch.

## Mutually exclusive terminal branches

Typed evidence is classified before the complete selector:

1. `INVALID_OPERATIONAL`: any probability, replay, lifecycle, RNG, checkpoint,
   schema, binding, typed, finiteness or publication invariant fails. Repair at
   most once under the identical contract; no scientific iteration is consumed.
2. `FORK_EVIDENCE_UNAVAILABLE`: one validly bound exact causal-field or
   executed-kernel comparison fails while every operational and derived guard
   passes. Retain independently valid natural evidence, quarantine every C row,
   expose no zero-filled C estimate and never call the complete selector.

When typed evidence is complete, apply
`ha_ctse_process/noncalendar_commitment_testbed.py::select_result_branch` in
first-match order:

1. `INVALID_OPERATIONAL`: a complete-path operational input is invalid.
2. `BENCHMARK_NON_IDENTIFIABLE`: any exposure, natural-support or per-replicate
   32/32 causal-audit floor is missed. Close this exact G0 without mechanism
   inference.
3. `NO_ACCESS_THIS_BENCHMARK`: maximum arm utility UCB is below `0.78`. Close
   only this comparison; do not veto stronger-MARL work.
4. `UNDERPOWERED_ACCESS`: maximum arm LCB is below `0.78` while its UCB reaches
   the floor. Close under the frozen budget with no rescue.
5. `COMMITMENT_SUPPORTED`: access is established,
   `LCB95(G)>0.10`, at least two `K` bins pass, TV passes and both natural-action
   `C_total` interval and point gates pass.
6. `REPRESENTATION_ONLY`: `LCB95(G)>0.10` but at least one registered interval
   condition confidently fails according to the exact statistical dual.
7. `ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED`: `UCB95(G)<=0.10`.
8. `MIXED_UNDERPOWERED`: every remaining valid numerical pattern.

Every branch updates only this exact benchmark/comparator/source. A
`COMMITMENT_SUPPORTED` result supports the explicit EHC link here and authorizes
consideration, not integration. A timing-specific claim additionally requires
positive two-sided `C_timing` evidence in both natural-action strata. Positive
mark-TV, `C_mark`, `V` or `G` alone cannot substitute for the complete branch.
No result here settles general hierarchy, semantic skill or complementary team
coordination.

## Exact preregistration and resource boundary

Scientific status is
`SCHEDULE_ONE_PREREGISTERED_FORMAL_OR_DUM_EHC_COMPARISON`; execution status is
`NOT_AUTHORIZED`.

- Training aggregate: 4,800,000 transitions, 60,000 episodes, 15,000 base
  optimizer steps, 10,000 event optimizer steps, 1,250 update shards and 15
  final checkpoints.
- Evaluation aggregate: 60 valid cells, 15,360 episodes and 1,228,800 primitive
  transitions.
- Analysis requires every final checkpoint, every evaluation cell, paired
  episode/RNG identities, all five 32/32 EHC audits, typed identity and derived
  fidelity for every selected complete row, and 10,000 bootstrap repetitions.
- Clean source worktree:
  `C:\Projects\My-paper-code-formal-1cc6552`.
- Fresh output root:
  `C:\Projects\My-paper-code\logs\20260723_event_held_commitment_link_g0_formal_cpu_registered`.
- Require at least 64 GiB free before every phase; hard output cap 32 GiB; hard
  elapsed cap 18 hours, divided into train 10 hours, evaluate 6 hours and
  analyze 2 hours.
- Retain the complete no-clobber run root through accepted external disposition
  and 30 calendar days afterward; retain tracked terminal summaries, hashes,
  reconciliation and disposition permanently.

Insufficient resources return `BLOCKED_RESOURCE`; they never reduce any seed,
replicate, update, optimizer exposure, episode, audit quota or bootstrap count.
The first `INVALID_OPERATIONAL` permits one bounded repair under this identical
contract; a second is a blocker. A valid negative, no-access, underpowered,
mixed or fork-unavailable result receives no pilot, extra seed, top-up,
threshold change or rerun.

The registered native Spark-medium Experiment Monitor must be rebuilt and
atomically registered before assignment. Formal train, evaluate and analyze
each independently require:

```text
AUTHORIZE_EVENT_HELD_COMMITMENT_LINK_G0_FORMAL
```

That token remains prohibited until one later explicit Controller authorization
names the exact run, Monitor and resource boundary. A valid conclusion-bearing
terminal result consumes the third of five authorized iterations;
preregistration and `INVALID_OPERATIONAL` do not.

## Prohibited changes

No environment-specific intrinsic reward, task shaping, identity/role input,
skill catalogue, duration action, learned hazard or terminate action, graph,
team latent, communication module, new credit objective, ordinary-access
admission gate, or post-result change to reward, observation, G0 distribution,
model, base PPO, optimizer, budget, seed, threshold, audit quota, estimand,
backend or thread topology.

Do not use an old checkpoint or aborted output root, run a pilot seed or extra
smoke, inspect interim utility for a decision, pool or top up evidence, treat
fork unavailability as zero C, retry a valid terminal result, or automatically
integrate EHC. Scheduling this comparison retires none of C-REC, C-CREDIT,
C-BENCH, C-COORD, C-MEASURE or broader C-FORK-TYPED.

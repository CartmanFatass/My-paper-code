# HA-CTSE Active Implementation Plan

Updated: 2026-07-21
Status: BATTERY_REVISION_AUTHORIZED
Work ID: `event-held-commitment-link-g0-implementation-20260720-retry1`
Base/source boundary: `5a34c16065c6b92d77f897abaa692ab88d2f2c0f`
Implementation commit: `ce0d0ec2ee1dc9e2ceee15ee0b76f19ebd84573c`

The executable design below is frozen and implemented. Every focused acceptance
item in the final section was reproduced on CUDA before commit; the measured
values are recorded in `docs/project/CURRENT_WORK.md` and in the review package
`docs/external-review/gpt5_6_pro/20260721_event_held_commitment_link_g0_code_review/`.
No formal training or registered evaluation has run. Do not edit this plan to
match a later implementation change; a contract change requires a new
authorized boundary.
Scientific source: `docs/research/designs/EVENT_HELD_COMMITMENT_LINK_G0.md`

## Outcome and authority

Replace the superseded noncalendar H/C/S/D executable benchmark with one
three-arm `OR`/`DUM`/`EHC` package for the controller-adopted
`EVENT_HELD_COMMITMENT_LINK_G0` source. The package must be runnable for a
short explicitly non-formal smoke and fully package the registered formal
training, evaluation and analysis contract, but this work does not launch
formal training or registered evaluation.

The adopted design is the only scientific authority. The implementation may
change only:

- `docs/project/IMPLEMENTATION_PLAN.md`;
- `ha_ctse_process/`;
- `scripts/`;
- `tests/`.

No Git mutation, experiment launch, reward/observation/task change, compatibility
adapter, successor route or project-control edit is authorized.

## Replacement ledger

- Preserve the current noncalendar ledger generator, anonymous 15-field
  observations, membership schedule, target/duration distributions and external
  G0 utility exactly.
- Use the full anonymous observation for all three new arms. The superseded
  calendar-masked arm, hindsight H/C/S/D solvers, old result tree, old checkpoint
  schema and their runner/test entry points are removed rather than retained
  behind flags or aliases.
- Keep `dynamic_roster_direct.DirectPrimitiveARPolicy` as the single ordinary
  recurrent base. Any optional prepared-step or primitive-logit-bias interface
  must leave the no-bias `OR` path exactly equal in parameters, state, actions,
  log probabilities, values, hidden transitions and PPO algebra under matched
  weights and RNG.
- The active executable surface remains
  `ha_ctse_process/noncalendar_commitment_testbed.py`,
  `scripts/run_noncalendar_commitment_benchmark_g0.py` and
  `tests/ha_ctse_process_noncalendar_commitment_benchmark_g0_test.py`; add a
  narrowly named helper module only if it eliminates duplication without
  preserving an obsolete path.

## Frozen model and treatment

Initialize one ordinary base with seed `58058`, clone it strictly into `DUM`
and `EHC`, then initialize the additions once from dedicated event/mark RNG
state and clone those additions strictly between `DUM` and `EHC`.

- `OR`: the existing 14,980-parameter direct recurrent actor-critic only.
- `DUM` and `EHC`: the same base plus bias-free `W_z: Linear(8,3)` (24
  parameters), `event_head: Linear(87,2)` (176), and
  `mark_head: Linear(87,16)` (1,408), for exactly 1,608 added trainable
  parameters in each arm.
- Existing source state is 32-wide locally and its anonymous active-set context
  is also 32-wide. Therefore the source's `h_64` event feature is frozen as
  `concat(h_pre_32, context_32)`. This is a parameter-free use of the two
  already-computed source states; neither widens nor changes the ordinary base.
  Event inputs are exactly
  `stopgrad(concat(o_15, h_pre_32, context_32, z_pre_8))`.
- Event and mark heads share no parameter and no gradient with the base trunk.
  The critic never reads `z`.
- The sole arm treatment is
  `primitive_logits = base_logits + W_z(m * stopgrad(z))`, with `m=0` for
  `DUM` and `m=1` for `EHC`. `OR` supplies no bias. No other arm-conditioned
  branch is permitted in sampling, storage, replay, loss or execution.

`W_z` belongs to the primitive/base optimizer because it is identified only by
primitive PPO. The base optimizer owns base parameters plus `W_z` in DUM/EHC;
the event optimizer owns only the categorical and mark heads. In `DUM`, the
zero treatment input produces an explicit zero gradient for `W_z`, so its Adam
step exposure matches `EHC` while its primitive effect is exactly zero.

## Clocks, lifecycle and execution

Maintain a per-environment table keyed only by the ledger lifecycle key. Each
entry owns membership epoch, `h`, `z`, `q`, open segment ID/start, and complete
or censored segment records. Keys never enter a model input.

For each physical row, use this order:

1. Apply the environment membership transition and reconcile lifecycle state.
   Genuine `JOIN` resets `h=0`, forces `CREATE`, samples a mark and samples
   `Delta` uniformly from `{4,8,12}`, setting `q=Delta`. Temporary leave freezes
   the full entry. Rejoin restores it. Terminal leave forces `CLOSE` after that
   lifecycle's preceding final reward and deletes it.
2. For every active entry with `q=0`, process exactly one opportunity before
   its primitive action. Support is exactly `KEEP`/`RENEW`. `KEEP` retains mark,
   segment ID and start and resamples only `q`; `RENEW` records a complete
   segment, increments the segment ID, samples a new mark and `q`, and opens the
   new segment. A due opportunity on rejoin is processed before its action.
3. Form the detached event-held mark table and execute the existing
   autoregressive primitive policy with the arm's sole logit treatment.
4. Step the unchanged environment, attach reward/terminal data, then decrement
   `q` exactly once for each lifecycle that took an active primitive action.
5. At episode end, after the final reward, force `CLOSE`, record every remaining
   open segment as right-censored and delete all lifecycle entries.

Inactive physical time never decrements `q`. Forced `CREATE` and `CLOSE` have no
categorical likelihood. A rollout cutoff is not an event: preserve `z,q`, the
segment and lifecycle table, carry the environment, detach `h` in all arms, and
bootstrap the unchanged critic. No forced close or event row is created.

The collector must support a resumable partial rollout for focused lifecycle
tests even though the registered update is 16 complete 80-step environments.
Batch environment/member/event tensors; retain loops only for simulator,
membership, recurrent and autoregressive causal order.

## Probability and trajectory contract

At forced `CREATE` and policy `RENEW`, sample a non-reparameterized mark using a
dedicated stream:

```text
u ~ Normal(mu, diag(sigma^2))
sigma = 0.1 + 0.9 * sigmoid(s)
z = detach(tanh(u))
```

For numerical stability compute each transformed component with
`log(1-tanh(u)^2) = 2*(log(2)-u-softplus(-2u))`. Mark log probability is the
sum of Normal component log probabilities minus this Jacobian. No gradient may
flow through sampled `u/z` into either head.

Store primitive rows with observation, `h_pre`, `z_pre`, action, old primitive
log probability, value, reward, terminal/continuation/bootstrap and active
masks, order/prefix, membership epoch, segment, `q` and owned RNG/collector
position. Store at most one padded event row per active lifecycle and physical
row with kind, 87-vector input, factor masks, categorical action, `u`, new `z`,
categorical old log probability, per-mark-component old log probabilities and
joint old log probability.

Likelihood support is exact:

- `CREATE`: mark factor only;
- `KEEP`: categorical factor only;
- `RENEW`: categorical plus transformed-mark factors;
- `CLOSE`: no policy row.

Teacher replay uses the recorded primitive action, categorical event action and
`u`; it recomputes the identical inputs, masks, factors and joint sums. Before
any update, maximum absolute error for every eligible categorical component,
mark component and joint likelihood must be `<=1e-6`.

## Credit, losses and exposure

Use the unchanged primitive recurrent PPO and GAE with `gamma=0.99`,
`lambda=0.95`, clip `0.2`, value coefficient `0.5`, primitive entropy
coefficient `0.01`, and correct terminal/continuation bootstrap masks. Every
event row receives the same scalar advantage as the primitive action it
precedes.

- Primitive loss: clipped primitive PPO + `0.5` clipped value loss - `0.01`
  primitive categorical entropy.
- Event loss: clipped PPO on the row's joint event likelihood - `0.01`
  categorical entropy for later `KEEP/RENEW` opportunities; mark entropy bonus
  is exactly zero and forced `CREATE` has no categorical entropy.
- Optimizers: separate Adam, learning rate `3e-4`, epsilon `1e-5`, weight decay
  `0`; separate gradient-norm clipping at `0.5`.

Each registered update is `16 x 80` rows and four full recurrent-sequence
epochs. It increments base optimizer exposure by four for every arm and event
exposure by four for DUM/EHC only. At update 250 the exact totals are 1,000 base
steps for all arms, 1,000 event steps for DUM/EHC and zero event steps for OR.
Report parameter counts, optimizer parameter counts, non-None/zero-gradient
counts, event-factor counts and optimizer steps separately by arm and group.
Pack/transfer each collected trajectory once and reuse it for all four epochs.

## RNG and pairing

For replicate `r`, add `1000*r` to base initialization `58058`, ledger `68058`,
order `78058`, primitive `88058`, opportunity `90058`, event `92058`, mark
`94058`, IID evaluation `98058`, and held-out evaluation `99058`. Bootstrap seed
is `108058`.

Ledger, order and primitive streams are paired across all arms without
consumption coupling. Opportunity/event/mark streams are paired between DUM and
EHC. Parameter initialization and every stream have separate owned state; no
arm's branch may advance another stream. Deterministic evaluation uses
categorical argmax, `z=tanh(mu)` and the existing deterministic primitive rule.

## Checkpoint and runner package

Checkpoint only at update boundaries with an asserted empty rollout buffer.
Use a strict versioned key set and registered-contract header. Save and restore:

- every model and both applicable optimizer states;
- completed update, next ledger/episode IDs, parameter and optimizer exposure;
- explicit `normalizers=None`;
- collector position, pending environments/membership snapshots and accumulator
  state (explicit empty values at the registered complete-episode boundary);
- all lifecycle/segment tables and masks;
- Python, global NumPy, CPU/CUDA torch and every dedicated ledger, order,
  primitive, opportunity, event and mark RNG state.

Load strictly rejects arm, replicate, shape, registered seed/threshold/budget or
key-set mismatch. A save/load continuation must reproduce one complete rollout
and one four-epoch update with exact discrete choices and RNG states, and with
continuous values, likelihoods, model and optimizer tensors differing by at
most `1e-7`. Formal evaluation accepts only a strict update-250 checkpoint.

The runner exposes explicit non-formal smoke, formal train, update-250
evaluation and aggregate-analysis modes. Formal modes require an unmistakable
explicit authorization flag; default invocation may only print the contract or
run the bounded smoke. Artifacts identify arm, replicate, mode, registered
contract, counts and checkpoint origin. The implementation task runs only the
short smoke.

Formal packaging fixes five paired replicates `r=0..4`, 16 environments,
horizon 80, 250 updates, 320,000 transitions/4,000 episodes per arm, and four
evaluation cells of 256 paired episodes per arm/replicate: IID deterministic,
IID stochastic, held-out deterministic and held-out stochastic. Evaluate only
`update_250.pt`.

## Statistical and result contract

Use 10,000 paired hierarchical-bootstrap repetitions. Resample the five
replicate seed triples, then whole paired episode IDs within each selected
replicate. Preserve all agents, events, complete/censored segments and paired
arm rows. Percentile intervals are 95%; all declared pass inequalities are
strict.

Primary `G` is held-out stochastic `U_EHC-U_DUM`; secondary `V` is held-out
stochastic `U_EHC-U_OR`. Access uses held-out stochastic arm utility and floor
`0.78`. Support, lifetime and intervention measurements use EHC held-out
stochastic trajectories.

This battery was revised on 2026-07-21 under external disposition
`docs/external-review/gpt5_6_pro/20260721_lifetime_battery_contract_question/`,
before any result was observed. The superseded battery gated on `P_KEEP`,
`P_RENEW`, `CV(T)`, physical-time lifetime bins and a raw logit-residual norm.
Each was passable without learned commitment timing: the usage gates only
require non-degeneracy of a binary support; `CV(T)` mixes policy timing with
exogenous gap variance, so `CV(T)=0.408` under always-`RENEW` while a crisply
learned deterministic `K=3` rule yields `0.236` and fails; and a residual
proportional to `(c,c,c)` has positive norm yet leaves the three-action softmax
exactly unchanged.

Define `K` for each commitment spell as the number of exogenous opportunity
intervals it contains, so terminating `RENEW` at the first later opportunity is
`K=1`, one `KEEP` then `RENEW` is `K=2`, and so on. `K` is policy-determined.
Temporary absence contributes neither a gap nor active duration. Spells
censored by terminal leave, forced close or rollout cutoff are excluded from
complete-spell `K` statistics and reported separately.

- Support, not evidence: at least `128` eligible natural `KEEP` rows and at
  least `128` eligible natural `RENEW` rows. `P_KEEP` and `P_RENEW` remain
  reported diagnostics and gate nothing.
- Policy-generated lifetime: over complete spells, bins `K=1`, `K=2`,
  `K>=3` require at least two with `LCB(proportion)>0.10`.
- Executable mark dependence: at states with at least two active lifecycles,
  derange `z` across lifecycles while holding observation, recurrent hidden
  state, action mask, active-set context and primitive prefix fixed. Require
  `LCB(I_TV)>0.10` where
  `I_TV = E[0.5 * sum_a |pi(a|o,h,z) - pi(a|o,h,z_perm)|]`. This is invariant
  to a softmax-common logit shift by construction.
- Identifiability requires at least 1,000 non-CREATE opportunities and at least
  250 lifecycles with two or more such opportunities across all five seeds.

`T`, `CV(T)` and the physical-time bins `[1,8]`, `[9,16]`, `[17,infinity]`
remain computed and serialized as descriptive outputs. They gate nothing.

For the source phrase "behavior confidently fails", use the exact statistical
dual of the LCB pass rule: at least one required lifetime-bin or intervention
condition has `UCB <=` its registered threshold. Support-count failures are not
part of this dual; they resolve earlier as non-identifiable. This introduces no
new threshold and leaves intervals crossing a threshold to the underpowered
branch.

## Natural event-decision consequence

Adopted 2026-07-21 under
`docs/external-review/gpt5_6_pro/20260721_replacement_c_scope_followup/`. This
is a **held-out evaluation-only** measurement. Training behavior, the PPO
objective, the behavior-policy likelihood, optimizer state and the checkpoint
schema are unchanged, and no additional RNG draw is permitted anywhere.

The collector already draws a mark candidate for every request before the
categorical mask is applied, and discards it on `KEEP`. The measurement
therefore requires retention of an existing quantity, not new sampling.

Retain the unmasked `candidate_u` and `candidate_z = tanh(candidate_u)` for
every opportunity. On a natural `CREATE` or `RENEW` row this is the executed
mark; on a natural `KEEP` row it is an auxiliary counterfactual mark. Candidate
fields are stored in all modes for a uniform trajectory schema and are
audit-only: they never enter a likelihood, loss, gradient or optimizer state.

At each eligible held-out non-`CREATE` opportunity, fork the frozen state into
two common-randomness branches. The `KEEP` branch retains `z`; the `RENEW`
branch applies the stored `candidate_z`. Both advance to episode termination
under identical realized future demand and membership, opportunity gaps,
primitive order, primitive-action uniforms, later event uniforms and later
candidate marks. Each branch owns cloned state; the two branches of a pair must
not share one mutable generator, because advancing one would shift the draws the
other sees. Truncating a branch to a fixed horizon is prohibited: this
environment pays zero reward until the terminal step, so a truncated branch
estimates a different quantity.

For a natural `KEEP` row, `A_KEEP = U(KEEP) - U(RENEW(candidate_z))`. For a
natural `RENEW` row, `A_RENEW = U(RENEW(candidate_z)) - U(KEEP)`. Cluster by
original sign-paired base episode, never by event row; multiple selected rows
from one cluster travel together in every resample. Batch membership is not a
statistical unit.

Gates are `LCB(A_KEEP)>0` and `LCB(A_RENEW)>0` with frozen point floors
`mean(A_KEEP)>=0.02` and `mean(A_RENEW)>=0.02`.

Forks are a batched forced-branch dimension per the binding engineering
constraints, sized in units of the registered 16-environment width. Batched and
sequential execution must agree exactly on discrete membership, event and
primitive actions, on terminal outcomes and utilities, and on RNG states after
continuation, with continuous values within `1e-7`; the natural-action branch
must additionally reproduce the originally collected continuation exactly. If
either equality fails the batched engine is invalid.

Default is full per-opportunity forking. The only accepted reduced form is 32
natural `KEEP` and 32 natural `RENEW` opportunities per replicate, selected
after natural trajectories are collected but before any fork outcome is
computed, by simple random sampling without replacement within each
`(replicate, natural_action)` stratum from a dedicated deterministic stream
derived from the registered bootstrap seed under a separate namespace. The
selection key may use only replicate, base episode ID and sign parity, physical
time, opaque lifecycle key, membership epoch, segment ID and the natural
action; it may not use observation values, mark values, future trajectory,
utility or counterfactual advantage. If any replicate has fewer than 32 eligible
rows for either natural action, the run is `BENCHMARK_NON_IDENTIFIABLE` rather
than repaired by changing the quota. Adaptive post-result resampling and
post-result top-up are prohibited.

Implementation is staged. Stage 1 is retention only. Stage 2 is the batched
fork engine and its equivalence evidence. The result contract does not consume
`A_KEEP`/`A_RENEW` until stage 2 is accepted.

Apply exactly this first-match result priority:

1. `INVALID_OPERATIONAL` for any probability, replay, no-op, lifecycle, RNG or
   resume invariant failure.
2. `BENCHMARK_NON_IDENTIFIABLE` if either identifiability count floor or either
   `128`-row support floor is missed.
3. `NO_ACCESS_THIS_BENCHMARK` if maximum arm utility UCB is `<0.78`.
4. `UNDERPOWERED_ACCESS` if maximum arm utility LCB is `<0.78` while its UCB
   reaches the floor.
5. `COMMITMENT_SUPPORTED` if access is established, `LCB(G)>0.10`, and every
   `K`-bin and intervention condition passes.
6. `REPRESENTATION_ONLY` if `LCB(G)>0.10` and behavior confidently fails as
   defined above.
7. `ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED` if `UCB(G)<=0.10`.
8. `MIXED_UNDERPOWERED` for every other valid numerical pattern.

The analyzer returns exactly one branch and the inputs used for every earlier
predicate; it never selects a successor, changes a threshold or performs a
post-result rescue.

## Focused acceptance evidence

The integrated package is accepted only after all of the following pass:

1. Exact CREATE/KEEP/RENEW/CLOSE transitions, q ordering and complete versus
   censored segment accounting.
2. Temporary leave/rejoin freezes and restores `h,z,q`/segment state; a due
   opportunity precedes the rejoin action; a partial rollout cutoff preserves
   lifecycle state and bootstraps without a synthetic event.
3. Matched-base OR and DUM with identical weights, observations, orders and
   primitive uniforms produce exact actions/log probabilities/values/hidden
   states when the DUM treatment input is zero.
4. DUM/EHC added parameter counts and optimizer ownership/exposure are equal;
   W_z treatment is the only primitive difference.
5. CREATE/KEEP/RENEW factor support and transformed mark component/joint replay
   errors are each `<=1e-6`; sampled `z` and stored event inputs are detached
   from base/event trunks as specified.
6. Strict checkpoint reload reproduces one rollout and update with exact
   discrete/RNG equality and all continuous/model/optimizer errors `<=1e-7`.
7. The eight result branches are mutually exclusive by first-match precedence,
   including equality and interval-crossing boundaries.
7b. `K` accounting is exact: a `CREATE`-opened spell closed by `RENEW` after two
   `KEEP` decisions records `K=3`; censored spells are excluded from complete-
   spell statistics and reported separately; temporary absence adds no
   opportunity. `I_TV` lies in `[0,1]`, is exactly zero under a softmax-common
   logit shift, and is computed from the same held-fixed state as the natural
   action.
8. One real short GPU non-formal smoke performs collection, replay, a finite
   four-epoch base update for all arms and event update for DUM/EHC, strict
   checkpoint round-trip, and artifact serialization without launching formal
   training/evaluation.

All local focused tests and the short smoke use the current default CUDA device;
tests must fail closed rather than silently fall back to CPU when CUDA is not
available. After focused checks pass, one fresh read-only Sol-xhigh reviewer inspects this
plan, the complete diff and evidence for the scientific invariants, replay and
checkpoint equivalence, throughput structure and numerical stability. At most
one concrete repair cycle is allowed before manager acceptance or a blocker.

## Prohibited mechanisms

No environment-specific intrinsic reward, task shaping, identity/role input,
skill catalogue, duration action, learned hazard/terminate action, graph/team
latent, communication module, new credit objective, ordinary-access admission
gate, reward/observation/G0 change, altered budget/seed/threshold/result meaning,
formal run, compatibility path or successor selection.

# USEFUL_EFFECT_ROSTER_G3

Status: formal evidence contract frozen; implementation and formal compute have
not started.

## Scientific provenance

The nonformal `ASYNC_COMMITMENT_ROSTER_G3` gate passed all 18,400 structural
cases. It established lifecycle-owned records and roster-to-edit causality but
used label uniqueness only as an audit quantity. It is preserved at
`logs/nonformal_async_commitment_roster_g3_20260723_pm1/result.json` and is not
renamed, rerun or promoted into a formal result.

This independent learned source repairs `CE-DIVERSITY-AS-UTILITY`: standing
commitments produce realized service effects, and external return measures task
demand actually served. Some tasks require repeated equal effects and make
other labels useless, so different labels alone cannot solve the source.

## Scientific question

Can a permutation-equivariant explicit roster of lifecycle-held commitments
learn asynchronous demand-matched allocation and transport it to unseen active
count plus unseen record age/gap better than both a no-roster editor and a
persistent team recurrent summary of the same public event history?

The primary claim is structured memory and held-out generalization. It is not a
claim that a finite TEAM_REC is mathematically unable to represent a finite
roster.

## Source and external utility

There are four anonymous service effects `{0,1,2,3}`. One held commitment emits
one unit of its selected effect throughout its service duty. For active count
`N`, the environment samples a nonnegative integer demand vector `d in N^4`
with `sum(d)=N` and at least two positive coordinates.

At one asynchronous decision, `N-1` anonymous standing lifecycles retain their
commitments. A deficit effect `q` is selected uniformly from the positive
coordinates of `d`; the standing service-count vector is exactly
`d-one_hot(q)`. Standing records and physical packing are uniformly permuted.
The editor must select one new commitment. After selection, all active records
execute their effect for the registered duty window.

Per-step external reward and episode utility are both:

```text
U = sum_k min(service_count_k, d_k) / sum_k d_k
```

There is no intrinsic reward, diversity payment, uniqueness shaping, named
role, task-phase label or future-reference input. The task reward is an
environment-side service objective.

The complete demand support is used:

- `N=2`: all permutations of `(1,1,0,0)`;
- `N=3`: all permutations of `(2,1,0,0)` and `(1,1,1,0)`;
- `N=4`: all permutations of `(3,1,0,0)`, `(2,2,0,0)`, `(2,1,1,0)` and
  `(1,1,1,1)`.

Thus duplicate effects are required in many cells and zero-demand effects are
always present except the all-one held-out cell.

## Lifecycle and profile contract

Editor event kinds are exactly `JOIN`, `RENEW` and `TERMINAL_REPLACE`, balanced
within every demand/deficit cell. RENEW releases the editor's previous held
record before selection. TERMINAL_REPLACE deletes the departed lifecycle and a
new anonymous lifecycle begins uncommitted. JOIN is fresh. Standing records may
execute a temporary leave/rejoin pair in their public history; the held
commitment freezes and restores independent of physical slot.

Training uses `N in {2,3}`, standing-record ages `{1,2,3}`, independent nuisance
gap lengths `{0,1,2}` and duty lengths `{3,5}`. IID evaluation uses the same
support with fresh ledgers. Held-out profiles are:

- `heldout_cardinality`: `N=4`, gaps `{0,2}`, ages `{1,3}`, duties `{5,7}`;
- `heldout_gap`: `N in {2,3}`, gaps `{8,16}`, ages `{8,16}`, duties `{8,12}`;
- `heldout_joint`: `N=4`, gaps `{8,16}`, ages `{8,16}`, duties `{8,12}`.

Gap events are balanced, target-independent nuisance signs recorded in the
public history. They do not change demand, membership or standing records.
Physical slots are never actor identity. Every source row has a paired ledger
under all arms.

## Actor, roster and critic information

The editor base query has exactly 13 fields:

- normalized demand counts, width 4;
- one-hot editor event kind, width 3;
- normalized active count, width 1;
- previous editor commitment one-hot, width 4; all zero for fresh editors; and
- previous-commitment-present flag, width 1.

It excludes physical/logical identity, deficit effect, exact standing counts,
future schedule, remaining lifetime, reward and source profile.

Each current standing-record token has seven fields: effect one-hot (4),
normalized record age, normalized current service duration and rejoin flag.
Token order and physical slot are absent.

The TEAM_REC public history uses ten fields per event: event-kind one-hot for
COMMIT/TEMP_LEAVE/REJOIN/NUISANCE (4), effect one-hot (4), normalized elapsed
time and nuisance sign. It contains exactly the events needed to reconstruct
the current roster, plus the registered irrelevant gap events. It contains no
deficit label or future information.

The centralized critic receives the 13-field base query plus normalized exact
standing service counts (4), width 17. Critic-only fields never reach query,
roster tokens, TEAM_REC history or edit logits.

## Matched learned arms

All arms instantiate the same modules and initialization:

- 32-wide base-query encoder;
- shared 32-wide standing-token encoder and one-head query-conditioned set
  attention;
- 32-wide TEAM_REC GRU over public history;
- base edit head, roster treatment `W_R`, team treatment `W_T`;
- 32-wide critic encoder and value head.

All trainable parameter inventories, decision ledgers, PPO passes and RNG
namespaces are identical. Only the declared edit-logit route differs:

```text
NO_ROSTER:   edit_logits = base_logits
TEAM_REC:    edit_logits = base_logits + W_T(h_team)
ROSTER_ATTN: edit_logits = base_logits + W_R(attend(query, standing_records))
```

ROSTER_ATTN set attention is invariant to standing-token order. TEAM_REC sees
the complete matched history. NO_ROSTER sees the same base query and source
exposure but neither memory treatment. Unused treatment modules remain
instantiated and receive exact zero edit-policy gradient.

The selected commitment is the event-held service record. It persists until
that lifecycle's later RENEW or terminal LEAVE; the one-decision source measures
the assignment edge without adding a low-level actor. This is an event-level
MARL allocation gate, not an end-to-end environment claim.

## PPO, budget and backend

The decision is a one-step categorical event policy. Use Adam `3e-4`, gamma
`0.99`, GAE lambda `0.95`, PPO clip/value clip `0.20`, value coefficient `0.50`,
entropy coefficient `0.01`, gradient clip `0.50` and four full-batch PPO passes.
Termination after the decision makes gamma/lambda operationally irrelevant but
keeps the registered PPO implementation path.

```text
replicates=5
training_episodes_per_update=512
updates=120
optimizer_steps_per_arm_replicate=480
training_episodes_per_arm_replicate=61440
evaluation_episodes_per_profile_mode=512
evaluation_profiles=iid,heldout_cardinality,heldout_gap,heldout_joint
evaluation_modes=deterministic,stochastic
natural_audit_episodes_per_replicate=128
bootstrap_repetitions=10000
backend=cpu
torch=2.7.0+cpu
torch_threads=1
```

One fixed counter-based seed registry owns model initialization, source
ledgers, standing permutation, membership/event type, nuisance, edit sampling,
evaluation, audit and bootstrap, with a disjoint replicate offset. No seed
sweep, CUDA fallback, backend mixing or cross-backend resume exists.

## Estimands and source identification

For each arm, `U` is mean deterministic `heldout_joint` demand-served utility.
The primary gain is:

```text
G_team = U_ROSTER_ATTN - U_TEAM_REC
```

The null gain is `G_null = U_ROSTER_ATTN - U_NO_ROSTER`. Use paired hierarchical
bootstrap over replicate and exact demand/deficit/source clusters for means and
95% intervals.

Before interpreting gains, formal evidence must reproduce:

- complete demand supports and exact uniform deficit selection within demand;
- standing counts exactly `d-one_hot(q)` and constructive oracle utility 1.0;
- the analytic NO_ROSTER Bayes utility for every demand-support-size and active-
  count stratum;
- balanced editor kinds, packing permutations and temporary-rejoin histories;
- exact lifecycle ownership and absence of actor deficit/count leakage;
- at least 128 natural heldout-joint ROSTER_ATTN decisions per replicate.

The access floor is `0.90`; the meaningful gain margin is `0.10`.

## Minimal consequence battery

On heldout-joint ROSTER_ATTN decisions, record:

- natural optimal-effect probability and deterministic utility;
- exact-snapshot replacement of one standing effect with the natural selected
  effect while keeping query, demand, membership, packing and future duty fixed;
- edit-distribution TV between natural and intervened standing rosters;
- natural-choice replay utility versus adapted-choice utility under the
  intervened roster; and
- duplicate-demand and zero-demand-label utility strata.

The battery passes only when natural optimal-effect and utility LCBs reach
`0.90`, roster-intervention TV and adapted-minus-replayed utility LCBs exceed
`0.10`, and both duplicate-demand and zero-demand-label utility LCBs reach
`0.90`. These are behavioral/effect statistics and require no arbitrary latent
label alignment.

## First-match result semantics

Apply exactly in this order:

1. `INVALID_OPERATIONAL_USEFUL_ROSTER_G3`: any finite-value, probability,
   gradient, replay, lifecycle, RNG, checkpoint, backend, reference or schema
   invariant fails.
2. `SOURCE_NON_IDENTIFIABLE_USEFUL_ROSTER_G3`: any support, oracle, Bayes-null,
   balance, anonymity, ownership, leakage or natural-quota predicate fails.
3. `NO_ACCESS_USEFUL_ROSTER_G3`: maximum arm utility UCB is below `0.90`.
4. `UNDERPOWERED_ACCESS_USEFUL_ROSTER_G3`: maximum arm LCB is below `0.90`
   while its UCB reaches `0.90`.
5. `ROSTER_GENERALIZATION_SUPPORTED_G3`: both gain LCBs exceed `0.10` and the
   complete consequence battery passes.
6. `TEAM_REC_SUFFICIENT_USEFUL_ROSTER_G3`: `UCB(G_team) <= 0.10`.
7. `NO_ROSTER_SUFFICIENT_USEFUL_ROSTER_G3`: `UCB(G_null) <= 0.10`.
8. `ROSTER_REPRESENTATION_ONLY_G3`: both gain LCBs exceed `0.10` and at least
   one consequence interval confidently fails its registered threshold.
9. `MIXED_UNDERPOWERED_USEFUL_ROSTER_G3`: every other valid pattern.

A consequence confidently fails only when its UCB is at or below its threshold.
No later diagnostic relabels an earlier branch.

## Artifact and launch contract

The runner will expose `train`, `evaluate`, `analyze` and reduced `exercise`.
Formal evidence requires `formal=true`, one exact integrated 40-character source
commit, all five replicates, final update-120 checkpoints, 120 evaluation files,
source controls, 640 natural audit rows and 10,000 bootstrap repetitions. The
analyzer rederives every metric and calls one pure first-match selector.

`exercise` is always `formal=false`, uses reduced counts, covers collection,
PPO replay/update, checkpoint reload, every arm/profile, roster intervention and
analyzer rejection by formal validation. Per-file hashes are not an authority
gate.

The authorization token is
`AUTHORIZE_USEFUL_EFFECT_ROSTER_G3_FORMAL_CPU_V1`. Formal iteration 4 becomes
launchable only after Project Manager accepts focused tests, one fresh bounded
exercise and the exact integrated source commit. A valid conclusion must be
followed by the Chinese user report `docs/report/ITERATION_4.md` before any
successor action. Two conclusion-bearing iterations remain before launch.

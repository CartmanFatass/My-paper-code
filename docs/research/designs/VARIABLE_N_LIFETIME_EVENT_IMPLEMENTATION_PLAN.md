# Variable-N + Variable-Lifetime Event Architecture Implementation Plan

Status: implementation plan; code and training require a separate approval
Date: 2026-07-17
Owning contract:
`docs/research/designs/VARIABLE_N_LIFETIME_EVENT_ARCHITECTURE_CONTRACT.md`

## 1. Outcome and implementation boundary

The architecture contract reached **Outcome A**. Implement one default-off
production path shared by:

- `F0`: Active-Set Scheduled Recurrent MARL;
- `F1`: Exchangeable Exogenous-Opportunity Event-Frontier Commitment Editor.

F0 and F1 use the same collector, lifecycle table, opportunity schedule,
active-set encoder, recurrent policy, critic, low actor, buffers, credit,
optimizer structure, checkpoint schema and parameter count. One non-parameter
mode switch chooses which already-computed context is passed to the commitment
decoder:

```text
F0: initial active-set summary g(C^(0))
F1: current applied-prefix summary g(C^(j-1))
```

No other F0/F1 branch is permitted. In particular, F1 receives no adapter,
extra layer, team latent, attention block, reward, mask or optimizer that F0
does not receive.

This plan does not authorize a new environment, training run, experiment gate,
intrinsic reward, shaping term or checkpoint migration from HMASD/R30.

## 2. Repository placement and reuse

Add one production module:

```text
ha_ctse_process/variable_roster_event.py
```

It owns the lifecycle table, active-only packer, external opportunity clock,
uniform frontier order, shared F0/F1 commitment model, structured event ledger
and member-event return builder. It does not own a separate trainer.

Integrate it through the existing production surfaces:

```text
ha_ctse_process/standalone_agent.py
ha_ctse_process/train.py
tests/ha_ctse_process_variable_roster_event_test.py
```

The existing `r30_fixed_clock.py` path remains unchanged and default. Reuse its
three established semantics, not its fixed-size implementation:

1. one native K-way categorical action whose incumbent channel means `KEEP`;
2. applied-working-set teacher forcing for sampled actions;
3. actor-invalid continuation rows when an update interrupts a live return.

Do not import `scripts/r49_orse.py`; it is synthetic interface evidence, not a
production model. Do not import, execute or rename the uncommitted R55 draft.

## 3. Default-off dispatch

Add one controller value and one mode value:

```text
high_controller = "variable_roster_event"
event_architecture_mode = "f0" | "f1"
event_architecture_schema_version = 1
event_opportunity_schedule = "uniform_active_gap_v1"
```

The current `legacy_duration` and `r30_fixed_clock_ar_edit` dispatches do not
pass through the new module. The event path fails closed if the mode, schedule,
collector schema or checkpoint schema is absent or unsupported.

## 4. Exact exogenous opportunity schedule

Freeze the first schedule as follows:

```text
k0 = 10 active primitive transitions
gap_i ~ DiscreteUniform({1, 2, ..., 19})
E[gap_i] = 10
```

Each vectorized environment owns two independent, policy-independent RNG
streams: one for opportunity gaps and one for frontier permutations. Their full
bit-generator states are checkpointed. Environment index may select an RNG
stream but is never a network input.

For each lifecycle, `active_gap_remaining` follows these rules:

- episode-start members are genuine joins and are due immediately;
- a genuine join or rejoin is due exactly once at that event boundary;
- after the member's commitment token is applied, sample a new gap in recorded
  frontier order;
- decrement the gap once after every completed primitive transition in which
  that member was active;
- temporary absence freezes the remaining gap;
- the mandatory rejoin opportunity supersedes the frozen remainder, and the
  post-rejoin token samples a fresh gap;
- terminal leave discards it;
- if a due member leaves at the same boundary, atomic membership handling wins
  and no policy token is created for the leaver.

The substep order is fixed:

```text
completed primitive transition
-> increment active skill ages and decrement active gaps
-> close affected leave traces from pre-removal old values
-> atomically apply membership events
-> form due frontier
-> sample uniform frontier order
-> sample/apply all commitment tokens
-> expose the final active commitment set to the low policy
```

Silent steps, gap samples, membership events and frontier-order samples have no
policy log-probability. The audit probability of an order is
`-lgamma(m + 1)` and cancels from every PPO ratio.

## 5. Active-only tensor contract

No policy tensor has a permanent `N_max` axis. At an environment batch
boundary, pack only active lifecycles:

```text
PackedActiveBatch
  env_ptr:                 int64   [B + 1]
  member_obs:              float32 [A, obs_dim]
  critic_member_features:  float32 [A, critic_member_dim]
  critic_global_features:  float32 [B, critic_global_dim]
  skills:                  int64   [A]
  active_ages:             int64   [A]
  event_flags:             bool    [A, 2]  # genuine_join, rejoin
  low_actor_hidden:        float32 [A, h_low]
  low_critic_hidden:       float32 [A, h_low]
  high_hidden:             float32 [A, h_high]
```

`A = sum_b |A_b|`. The CPU routing view additionally carries lifecycle keys and
membership epochs, but the model-facing dataclass has no fields for either.
Packing creates an ephemeral key-to-row map used only to route actions and
state updates.

The event batch is also ragged:

```text
PackedEventBatch
  event_active_ptr:        int64 [E + 1]
  event_frontier_ptr:      int64 [E + 1]
  ordered_owner_rows:      int64 [T]
  token_positions:         int64 [T]
  legal_masks:             bool  [T, K]
  combined_actions:        int64 [T]
  old_token_logp:          float [T]
  old_owner_values:        float [T]
  actor_valid:             bool  [T]
```

Here `T` is the number of actual frontier tokens. Structured per-event
snapshots store the exact active lifecycle list, initial skills/ages, every
pre-token and post-token working skill/age vector, order and membership events.
They are source arrays, not digests or checksums.

An empty active set is unsupported in schema v1 and fails closed. A later
all-absent no-op state requires an explicit collector contract rather than a
dummy policy member.

## 6. Shared F0/F1 commitment model

Use one class and one state-dict shape for both modes.

### 6.1 Member and set encoding

For each active member:

```text
u_i = [x_i, skill_embedding(z_i), normalized_log_age,
       is_genuine_join, is_rejoin]
e_i = phi(u_i)
g(C) = [sum_i e_i, log(1 + N)]
```

For a genuine join, the skill embedding is a fixed non-learned zero vector.
`phi` is shared. The implementation maintains the sum incrementally after a
`SET` by subtracting the old member embedding and adding the updated one.
There is no processed flag, permanent index embedding, key embedding, mean
pool, team code, bridge, attention, graph or slot.

### 6.2 Per-member recurrent policy

A shared `GRUCell` advances only when its owner receives a policy opportunity.
It reads the focal member embedding and the selected set summary. Its stored
pre-token hidden state is teacher-forced during replay. Silent steps and other
members' tokens do not advance it.

The same decoder emits exactly `K` logits. For a member with incumbent `z_i`:

```text
channel z_i -> KEEP
channel z   -> SET(z), z != z_i
```

For a genuine join, all K channels mean `SET(z)`. `SET(current)` therefore does
not exist and a separate KEEP head is not added.

F0 feeds the immutable initial summary to every decoder call. F1 feeds the
incrementally updated summary. Both still apply the same stored legality mask
before the categorical distribution. The architecture mode is not a learned
input and creates no parameters.

### 6.3 Centralized event critic

Use one shared per-owner critic:

```text
V_i = value(owner_critic_embedding_i,
            sum(active_critic_embeddings),
            log(1 + N),
            critic_global_features,
            boundary_kind)
```

`boundary_kind` is critic-only and distinguishes ordinary opportunity,
rollout truncation, temporary pre-removal leave and terminal boundary. It does
not enter the actor. F0 and F1 have the same critic and value normalizer.

## 7. Low-policy compatibility without fixed N

Preserve the low actor contract exactly:

```text
pi_low(a_i | o_i, z_i)
```

Reuse the strict recurrent actor computation and action distribution, but call
it on the flat active-member rows. Do not add team code, lifecycle flag, member
key, set summary or identity to the low actor.

The current fixed-N centralized critic cannot be used because its shape embeds
fixed state/team-code assumptions. In the event path only, replace it with a
shared active-set critic over `critic_member_features`, focal skill and the
same sum/count form. This is correctness infrastructure shared by F0/F1, not a
causal difference. Original low-policy classes and checkpoints remain
unchanged; schema v1 provides no migration from them.

Primitive rollout storage is flat by lifecycle transition, with offsets for
environment steps and recurrent chunks. A chunk is keyed by routing metadata
outside the model:

- survivor/KEEP/SET: hidden state continuous;
- temporary leave: close the chunk with a critic truncation and freeze hidden;
- rejoin: begin a new chunk from the restored hidden, not zero;
- genuine join: begin from zero hidden;
- terminal leave: close with zero bootstrap and discard hidden.

Packed recurrent replay must match scalar active-member inference and must not
insert dummy-agent transitions.

## 8. Lifecycle runtime and event ownership

`VariableRosterEventCore` owns one lifecycle table per vectorized environment.
Each record contains exactly the contract fields plus
`active_gap_remaining`. Membership events supplied by the collector must name
their temporary/terminal semantics and expected membership epoch.

At a concurrent frontier:

1. snapshot the post-membership/pre-policy active set once;
2. compute initial member embeddings and initial sum once;
3. sample the uniform external order;
4. for each ordered owner, store the exact pre-token working state and mask;
5. evaluate the shared policy with the F0 or F1 context;
6. apply the chosen token immediately;
7. update only the changed member embedding and set sum;
8. store the exact post-token working state and new high hidden;
9. after the transaction, clear one-boundary join/rejoin flags and route the
   final commitment set to the low actor.

Any stale epoch, duplicate lifecycle state, inactive frontier member, mask
mismatch, routing key in model input or post-sampling repair raises before the
environment action is issued.

## 9. Event return, GAE and update boundary

Every policy token opens one return row owned by that member. While active, all
open owner rows accumulate the unchanged scalar environment team reward with
physical-time discount:

```text
R_i = sum_{r=0}^{Delta_i-1} gamma^r r_env[t+r]
bootstrap_i = gamma^Delta_i V_i(next owner boundary)
```

Other members' opportunities do not advance this owner's event-depth trace.
GAE links only successive rows of the same lifecycle and policy version.
Actor loss uses one combined categorical ratio per valid token; a concurrent
frontier is averaged over its actual tokens.

At a PPO update boundary:

1. close every open owner row with the old critic and
   `policy_truncated=true`;
2. do not reset simulator state, lifecycle state, skills, ages, opportunity
   gaps or recurrent hidden states;
3. after the update, open actor-invalid continuation rows for active members;
4. close a continuation at that member's next owner boundary before opening a
   new actor-valid decision row.

This preserves physical reward accounting without attaching post-update
reward to an old behavior ratio.

## 10. Collector integration

Extend the existing collector result schema rather than creating a second
trainer. Event-mode reset/step results provide:

```text
active lifecycle routing records
active member observations
critic-only member/global features
atomic membership events since the previous action
scalar team reward and optional unchanged per-member low rewards
terminal/truncation status
```

Actions are returned through the ephemeral routing map in the collector's
current active presentation order. The policy never sees that order or the
routing keys. Non-event collectors keep their current fixed-array contract.

`train_loop` retains one outer loop. It selects fixed-array or active-ragged
packing at the controller boundary, then uses the same optimizer/reporting
boundary. Do not add an event-specific script, environment or experiment
runner during implementation.

## 11. Checkpoint and resume

Event-mode checkpoints use top-level schema version 3 and contain a mandatory
`event_architecture` bundle:

```text
architecture_mode
event_architecture_schema_version
opportunity_schedule_name and k0
commitment_model_state
event_critic_state
low_actor_state
low_critic_state
high/low optimizer states
high/low normalizer states
lifecycle table schema and all live records
opportunity RNG states
frontier-order RNG states
open event rows and actor-invalid continuations
policy_version
```

F0/F1 checkpoints have identical parameter-key and optimizer-key sets. Resume
requires exact architecture mode and every live runtime field. Loading schema
1/2, R30 or legacy HMASD weights into this path is a hard error. Evaluation may
load model/normalizer state without live lifecycle records only when starting
from a fresh environment reset and the checkpoint explicitly declares
`runtime_state_absent_for_fresh_eval=true`.

## 12. Staged implementation

### Stage 1 — pure state and probability core

Implement in `variable_roster_event.py`:

- lifecycle state machine and exact opportunity schedule;
- active-only packer with model/routing type separation;
- shared F0/F1 policy and critic;
- uniform-order sampling and exact sequence replay;
- structured ledger and per-owner return builder.

No production collector or optimizer runs in this stage.

### Stage 2 — agent and ragged low-policy path

In `standalone_agent.py`:

- add fail-closed event-mode dispatch;
- delegate lifecycle/high-event behavior to the core;
- run the low actor and new active-set low critic on flat active rows;
- add lifecycle-based recurrent primitive storage and bootstrap;
- keep all R30/legacy branches unchanged.

### Stage 3 — collector, update and checkpoint wiring

In `train.py`:

- accept the dynamic roster result schema only in event mode;
- route atomic membership events before commitment actions;
- update the shared event PPO and ragged low PPO at the existing update
  boundary;
- save/load the strict schema-3 event bundle;
- expose only implementation telemetry, not scientific metrics.

### Stage 4 — focused correctness checks

Add one focused test file. Run only the checks in Section 13. Do not launch an
environment, benchmark or training run. Remove transient pytest output after
success.

## 13. Focused acceptance checks

Implementation is complete only if all checks pass:

1. **Lifecycle sequence.** Hand-authored join, KEEP, SET, temporary leave,
   survivor continuation, rejoin and terminal leave produce exact skills,
   ages, gaps, epochs and hidden states; stale or ambiguous events fail.
2. **Opportunity schedule.** Gaps are in `[1,19]`, decrement only while active,
   join/rejoin are immediate, resume reproduces future frontiers exactly and
   no schedule term enters actor likelihood.
3. **Permutation compatibility.** Relabeling a synthetic active roster and its
   stored order relabels actions/values while leaving probability unchanged to
   `1e-6`; routing keys cannot be found in model input fields.
4. **Sampling/replay parity.** Stored order, mask, action, initial working set
   and applied prefixes reproduce every token log-probability to `1e-6`.
5. **F0/F1 capacity match.** State-dict keys, tensor shapes and parameter count
   are exactly equal; paired initialization is byte-equal.
6. **Algebraic reduction.** F0 and F1 are exactly equal when applied prefixes
   leave the working summary unchanged and when the decoder's summary effect
   is action-independent on common support.
7. **F1 structural path.** With a synthetic earlier `SET`, a later token's
   common-support relative logits have a finite nonzero derivative through the
   updated set summary. This establishes wiring only, not usefulness.
8. **Duration credit.** A manual multi-member timeline matches direct
   `gamma^Delta` returns and per-owner GAE; another member's event does not
   advance trace depth; temporary leave uses pre-removal truncation.
9. **Ragged low replay.** Flat active-member inference and packed recurrent
   replay match actions/log-probabilities/values/hidden states to `1e-6` across
   different active counts, leave/rejoin and survivor continuity.
10. **Checkpoint fail-closed.** A full live-state round trip reproduces model,
    optimizers, normalizers, lifecycle records, open traces and both RNG
    streams; deleting any mandatory field or changing mode/schema is rejected.
11. **Legacy isolation.** Importing and constructing existing R30 and legacy
    controllers produces unchanged state-dict signatures and does not import
    the event module unless selected.

These checks are engineering evidence only. They do not establish cooperation,
learnability, variable-N benefit, lifetime benefit, HMASD parity or an F1
advantage over F0.

## 14. Stop conditions and next decision

Stop implementation and return to F0-only design if any required fix would:

- expose lifecycle keys, epochs, persistent slots or semantic identities;
- let prefix affect only masks while claiming learned F1 coupling;
- add an F1-only module, parameter, reward, critic or optimizer;
- require a team latent, graph, slot stack, learned ordering or learned hazard;
- repair actions after sampling outside the stored categorical probability;
- retain dummy members or permanent `N_max x N_max` tensors;
- make exact resume depend on permissive partial loading.

After focused checks pass, stop. The next boundary is a separate architecture-
matched testbed and experiment contract comparing F0 with F1; it must be
authorized independently and cannot be inferred from this plan.

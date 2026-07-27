# D0 — carrier and estimand derivation

```text
id=D0
cost=zero compute
status=derivation complete, freezes proposed
authority=project_manager derivation; scientific ratification belongs to external review
source_ruling=20260725_research_direction_and_ledger
```

The ruling's first scheduled action. Nothing here is measured; everything here is
*defined*, because D7 exists to separate natural renewal from five other ways a
commitment can appear to end, and that separation is a definition rather than an
observation.

Every claim below is anchored to code read on 2026-07-25, not inferred from
naming.

## 1. Three clocks, which are not the same thing

The project principles already distinguish these. The code confirms they diverge.

| Clock | What it is | Code |
|---|---|---|
| **Check opportunity** | When the high level is *offered* a decision | `steps_to_check[env_id]`, decremented per step, reset to `skill_interval` |
| **Realized commitment lifetime** | How long a commitment actually persists | `skill_age[env_id, agent_id]`, incremented per step for active agents, **reset to 0 only on SET** |
| **Learning-credit window** | The span a high-level advantage is attached to | `HighCheckRow`, opened per check and closed by `HighCheckBuffer.close(...)` |

**The check clock is shared, not per-agent.** `steps_to_check` is indexed by
`env_id` alone (`standalone_agent.py:3103`). Every active agent is offered a
decision at the same physical time.

So *untied `k`* under R30 means **untied realized lifetime**, never untied check
opportunity. The paper must claim the former. This is the claim boundary recorded
in `RESEARCH_GOAL.md`; it is the one point where the ruling interpreted user
intent rather than reading it.

### The three clocks decouple, and one decoupling is a trap

At every policy update, `start_high_continuations_after_update` calls
`segments.renew(...)` with `switched=False`, `initial_assignment=False` and
`skill_age_prev=skill_age[env_id, agent_id]` (`standalone_agent.py:3166-3191`).

Therefore, at a policy-update boundary:

- `skill_age` **continues** — the commitment is not interrupted;
- `active_skills` is **unchanged** — no renewal decision was taken;
- but a **new segment record is opened** — the record is split in two.

> **Measurement trap.** Lifetime counted from *segment records* is fragmented into
> rollout-length pieces at every policy update, whatever the policy does. With
> `rollout=40` and `k0=5` that is a hard ceiling of 8 check opportunities per
> fragment. A short-lifetime reading taken that way is an artifact of the update
> cadence.

Realized lifetime must therefore be measured as **`skill_age` at the moment of a
genuine SET**, or equivalently as KEEP-run length in check opportunities — never
as a segment-record length.

**Checked, and the trap is latent rather than active.** `process_update` sets
`valid = [] if self.r30_enabled else transition_segments`
(`standalone_agent.py:6330`) and early-returns on `if not valid:` (`:6349`), so
under R30 `segment_length_mean`, `segment_length_max`, `skill_switch_rate` and
`duration_target_mean` are **hardcoded `0.0`** — not fragmented, not computed.
Symmetrically, the update-boundary `segments.renew` that causes fragmentation is
R30-only, since `start_high_continuations_after_update` returns early when
`not r30_enabled`.

So no existing metric is currently misleading. The hazard is that **the R30 lane
emits no lifetime metric at all**, and the obvious way to add one — count segment
records — is precisely the fragmented measurement. This trap is waiting for D7,
not behind it.

This is the same *class* of defect as legacy's short-segment sampling bias, on the
carrier chosen partly to avoid that bias. R30 avoids legacy's **sampling** bias; it
does not avoid **record fragmentation**. The two must not be conflated.

## 2. Carrier eligibility — only one of three branches contains a renewal decision

`FixedClockAREditPolicy.act_sequence` (`r30_fixed_clock.py:246-298`) has three
mutually exclusive regimes:

| Regime | Condition | Is KEEP a decision? |
|---|---|---|
| Native categorical | `native_categorical_edit` | **No.** KEEP is a post-hoc *label* applied when the sampled skill happens to equal the current skill (`skill == working_skills[agent_id]`). `keep_head` is bypassed; `logp` is the skill log-prob alone |
| **No incumbent** | `not active`, `:263-267` | **No.** Forced SET; `keep_logit` reaches neither `kind` nor `logp`. There is nothing to keep |
| Full refresh | `force_refresh_every_check` | **No.** Always SET |
| **Learned keep** | neither flag, **and an incumbent exists** | **Yes.** `keep_logit -> sigmoid`, with `log_keep` / `log_switch` factorization |

Both flags default `False` (`getattr(config, ..., False)`, `standalone_agent.py:1850-1854`),
so the live main lane is the learned-keep branch. The carrier is eligible.

> **Eligibility condition, frozen.** Renewal urgency is observable **only** under
> the learned-keep branch. Under native-categorical edit a "KEEP rate" is the
> collision rate of the skill categorical — a measure of skill-policy
> concentration wearing the same metric name. Any renewal statistic must record
> which branch produced it.

Two incidental properties of the learned-keep branch, both useful:

- `best_skill = skill_dist.sample()` is drawn whether or not KEEP is chosen
  (`r30_fixed_clock.py:288-290`), so RNG consumption does not depend on the
  outcome — paired replay under common random numbers stays aligned across arms.
- `entropy_weight = (1 - sigmoid(keep_logit)).detach()` — skill entropy is
  downweighted by keep probability. A high-KEEP policy therefore receives less
  skill-entropy pressure, which is a plausible self-reinforcing path into
  concentration and must be logged, not assumed neutral.

## 3. Renewal urgency — the estimand

**Completed 2026-07-25 per the D7 ruling.** The earlier single formula was
underspecified in three ways: "re-decide" did not say which replacement skill,
`Δ` was not fixed, and `H` did not exist.

### Corrected 2026-07-25 — two was not enough, and one was misnamed

**Ruling: `docs/external-review/rounds/20260725_d7_2b_source_persistence_necessity/21_PRO_OPEN_RAW.md`.**
Order 0 of that ruling's revised sequence is this reconciliation. The two
estimands below are both correct and both **policy-conditional**; naming one of
them a *source* property was the defect that let D7.2B spend a run on a source
that could not identify its own proposition.

**`U_opp` is renamed.** Its maximization runs under the frozen learned joint
policy — later agents and future decisions still follow that policy — so it is the
**best focal SET under policy continuation**, written `U_max_pi` below. It is not
an oracle property of the source and must never again be described as "does the
source *contain* a valuable renewal".

**A third, source-level estimand is required**, with the other agents and later
decisions **reoptimized or supplied by a constructive oracle in both terms**:

```text
U*_{i,src}(h; H) =   max_{z != z_i, joint continuation} E[ G_H | SET_i(z) ]
                   - max_{joint continuation}           E[ G_H | KEEP_i ]
```

A history is **persistence-essential** only with a material margin on both sides:

```text
U*_stable,src / B_H  <=  -0.10          U*_flex,src / B_H  >=  +0.10
```

Equivalently: the best all-SET continuation must sit materially below the optimal
mixed KEEP/SET continuation.

**Why this matters more than a definition tidy-up.** On
`two_timescale_role_free_actions`, `U*_stable,src = 0` exactly, because persistence
and full-sync swapping both reach the ceiling. That one number is decidable on
paper and is the whole reason the source fails as a positive control — a source
gate computing it would have cost nothing and saved the run.

So there are **three layers, never fewer**, and D7.2B is the case that shows why:

| Layer | Quantity | Question it answers |
|---|---|---|
| source necessity | `U*_{i,src}` | does *this source* require an individual to persist? |
| policy-conditional effect | `U_pi`, `U_max_pi` | does renewal help *under this policy's* coordination convention? |
| natural behaviour | KEEP/SET hazard, realized individual lifetime | does the policy actually do it? |

The retired toy had a slow-timescale duty, did **not** require one individual to
carry it, and the learned policy coordinated by swapping. Only the first layer
separates those.

### Two estimands, never one number

Under learned-keep R30 a SET **excludes the incumbent** — the skill head is masked
— so the return depends on *which* non-incumbent skill is chosen. That splits the
question in two:

```text
U_max_pi(h; H) = max_{z != z_i} Q^pi_H(h, SET(z))          - Q^pi_H(h, KEEP)
U_pi    (h; H) = E_{z ~ pi_SET(.|h)} [ Q^pi_H(h, SET(z)) ] - Q^pi_H(h, KEEP)
```

Both carry `Q^pi` deliberately: the continuation is the frozen learned joint
policy in both, which is the whole reason neither is a source property.

- **`U_max_pi`**, written `U_opp` before 2026-07-25 — the **best focal SET under
  policy continuation**. Superseded framing: this was described as asking whether
  the source *contains* a valuable renewal. It does not. Its continuation is the
  frozen learned joint policy, so it is policy-conditional like `U_pi`, and the
  source-level question belongs to `U*_{i,src}` above.
- **`U_pi`** — can the **current** conditional SET policy actually exploit it?

These are different claims and must not be collapsed. A source can be rich in
renewal opportunity while the policy is incompetent to use it — but note that
neither of these two separates "no heterogeneity" from "no competence" on its own,
because both condition on the same policy's coordination convention. That
separation needs `U*_{i,src}`.

**`U_max_pi` requires a split sample.** The maximizing skill is selected on one
replicate set and evaluated on an **independent** one. Maximizing over noisy
returns on the same sample manufactures an optimistic effect — the selection is
itself an estimate. `U*_{i,src}` needs the same discipline for the same reason.

### Δ and H, frozen

- **`Δ` = one check interval.** A KEEP token under R30 commits only until the
  next shared check, so anything longer is not what the action does. The policy
  resumes normally at the following check.
- **`H` must cover the claimed downstream consequence.** On the toy the primary
  `H` is **one full slow period, 30 primitive steps**, with `H = 5` — the next
  check — retained as a secondary temporal localization. The source itself sets
  those two clocks. For the main scenario `H` is frozen from its causal duty
  window *before* the audit runs.
- **`H` is named per mechanism, not per source.** One source can carry more than
  one renewal-creating mechanism, and each has its own causal duty window. The
  toy's `30` and `5` are the *same* mechanism localized at two resolutions, which
  is why a single `H` looked sufficient; two mechanisms are a different case and a
  single `H` misprices whichever one it was not derived from. An audit must state
  which mechanism its `H` serves and report the margin against the `B_H` measured
  over that same `H`. Scenario 7 has two:

  | Mechanism | Duty window | Derivation |
  |---|---|---|
  | Relay/role exchange | **~139 steps** | mean separation `0.5214 x 8000 = 4171 m` at max speed `30` per `1.0 s` step |
  | Energy-driven roster change | **~1500 steps** | time to first dock dominates: ~1071 steps to fall from `0.55` to the dock trigger, *then* ~403 s of charging plus transit |

  The energy row was first written as `~400-500 steps` from the charge duration
  alone. That was wrong, and measurement caught it: `charge_steps` is exactly
  `0.0` in every arm at both `H = 139` and `H = 450`, and only becomes non-zero
  (`678.5`) at `H = 1500`. A duty window must span **time-to-first-event plus the
  event**, not the event alone — otherwise the horizon excludes the very mechanism
  it was derived for, which is the mispricing this rule exists to prevent.

  An `H` set to the exchange window truncates the energy consequence before it can
  occur, so renewal measures as worthless for a reason that is an artifact of the
  horizon. That is distinct from — and can co-occur with — the energy mechanism
  being **absent**, which is what stage `S1` does by disabling battery and
  charging outright. Both produce a non-positive `B_H`; only the second is fixed
  by changing stage.

### Continuation semantics — total policy-mediated effect

| Position | Treatment |
|---|---|
| Tokens before the focal agent | fixed |
| Focal token | forced KEEP or forced SET |
| **Later agents in the same check** | **allowed to react** to the changed autoregressive prefix |
| Later checks and primitive actions | generated by the same frozen policy under common random numbers |

Holding later factual actions fixed would estimate a *direct* effect and would not
correspond to the deployed autoregressive policy. The quantity we want is the
total effect the intervention has through the policy.

### Normalization

`U_tilde = U / B_H`, where `B_H` is frozen **before** the audit as either the
feasible external-utility range over `H`, or a constructive-minus-null return gap
from a separate source control. It is never estimated from the treatment outcome
— that would scale the effect by the thing being measured.

Both expectations start from the **same pre-decision history**. `G` is external
task return only.

Hazard form: `λ_i(t) = Pr(renewal is beneficial | h_{i,t})`.

- **stable** — `U_i` negligible over the relevant window;
- **flexible** — `U_i` materially positive;
- an agent may move between regimes within one lifecycle.

Realized lifetime is a **consequence** of `U_i`, not a definition of it. Three
quantities that are *not* the estimand, and why:

| Quantity | Why not |
|---|---|
| Skill-assignment churn | Conflates flexibility, exploration noise, skill-label symmetry and a bad controller |
| Dwell time / realized lifetime | Circular — it is what the controller is supposed to learn |
| Duration-posterior entropy | Measures concentration, not whether re-decision is valuable |
| KEEP frequency alone | A controller can KEEP because it is inert |

### What the expectation averages over — scope of the claim

Ruled by external review on 2026-07-27, in the round archived at
`docs/external-review/rounds/20260727_d7_s_stage_b_crn_and_user_world/`. The
estimand itself is unchanged; what is fixed here is the population, because a
correct number stated over the wrong population is still a wrong claim.

The measure is **topology-conditioned**, not a single flat draw:

```text
T ~ P_T          topology, drawn from the registered seed set
W ~ P(W | T)     user world, drawn conditional on that topology
```

The existing topology/episode bootstrap hierarchy already represents this. **No
additional bootstrap level is introduced** — the conditioning was always in the
sampler, only the wording described it as unconditional.

Two consequences bind any eventual write-up:

1. The result is an **equal-topology-weighted average over the eight registered
   seeds**. It is not a claim of uniform performance across topologies, and must
   not be worded as one.
2. Those eight seeds contain **only three of the four BS-quadrant classes**. The
   ensemble stays valid and needs no re-registration, but the missing class is a
   stated limitation, not a gap to be quietly closed. **The seed list must not be
   rebalanced after the fact** — changing the registered population once results
   exist converts a limitation into a selection effect.

Topology records expose quadrant composition so this is checkable from the
artifacts rather than from memory at writing time.

## 4. Search-cost estimand

Search cost is **not** wall time and **not** nominal action-space cardinality.
Reported separately, because equal environment steps do not imply equal learning
opportunity:

1. environment interactions;
2. high-level decision samples;
3. optimizer updates and gradient contribution, resolved by lifetime stratum.

The claim is *reaching a registered utility level* at lower cost on these axes.
The utility level must be registered before D7 runs, not chosen after.

## 5. Comparator roles, frozen

| Arm | Role | Constraint |
|---|---|---|
| **R30 learned-keep** | Primary carrier **and** unrestricted comparator | The same mechanism serves both; the constrained arm differs only by the regime structure imposed on it |
| **Best shared fixed lifetime** | Lower comparator | Must be the *best* fixed setting under a sweep, not an arbitrary one |
| **`legacy_duration`** | Frozen sampled-duration comparator and bias diagnostic | Cannot support any general conclusion about unrestricted variable lifetime — only about legacy's own update geometry |

Matched across arms: information, action support, optimizer exposure.

## 6. Censoring — how a commitment stops without a renewal decision

**Corrected 2026-07-25.** An earlier revision listed six sources for the carrier.
Four of them are legacy-only: `standalone_agent.py:4151` reads
`if self.r30_enabled: return self._r30_maybe_assign_skills(...)`, and every path
from `:4162` onward — team-intent Z boundary, the active-mask expiry test,
`situation_hazard_forced_renewal`, and duration exhaustion — is in the branch
below that return. Under the R30 carrier they are unreachable, and attributing an
R30 commitment end to them would be a category error.

For the carrier, the list is short:

| # | Source | Anchor | Real decision? |
|---|---|---|---|
| 1 | **Genuine SET** | `segments.renew(...)` under `token_kind == SET_TOKEN`, `standalone_agent.py:4103`; sets `completion_reason="renewal"` | Yes — the only one |
| 2 | Episode end | `segments.flush(reason="episode")`, `train.py:7465` | No |
| 3 | **Policy-update boundary** | `segments.flush(reason="update")`, `train.py:7488`, preceded by `policy_truncated=True` at `:3131` | No — the fragmentation trap of §1 |
| 4 | **Synthetic continuation reopen** | `segments.renew(...)` in `start_high_continuations_after_update`, `:3166` | No — a bookkeeping row |

Sources 2 and 3 carry distinct `completion_reason` strings, so they are directly
attributable. Source 4 is **not** marked by any single flag: it is inferable only
from a constellation — `switched=False`, `initial_assignment=False`,
`duration_target=0`, `high_logp=0.0`.

That every `completion_reason == "renewal"` really is a genuine SET holds only
because the update-boundary `flush` nulls the slot before
`start_high_continuations_after_update` calls `renew`, so the reopen never takes
`renew`'s `old is not None` retag branch. **This is a real invariant resting on
call ordering in two different files.** D7 must assert it explicitly rather than
build attribution on it silently, and an explicit synthetic-continuation flag
would retire the dependency altogether.

Fewer contamination sources is a further point for the carrier. It also raises
the relative weight of source 3, now one of only two non-decision ways a record
ends.

**Right-censoring is mandatory reporting, not a footnote.** A commitment still
running when its observation window ends is censored, not short. Long lifetimes
are the quantity of interest and they are exactly the ones censoring removes, so
an uncensored mean lifetime is biased toward the answer that kills the thesis.

## 7. A purpose-built two-timescale source already exists, and already failed once

`two_timescale_role_free_actions` (`envs/pettingzoo/two_timescale_role_free_actions.py`)
is a toy with ground-truth heterogeneous timescales: a fast target flipping every
`k0=5` steps and a slow target flipping every `k0 * 6 = 30`, roles never named or
fixed, no intrinsic reward, and `r39_toy_slow_match` / `r39_toy_fast_match` logged
separately for evaluation only.

That is close to an ideal source for D7's first question, and one run completed:
`EXP-20260715-r39-native-hmasd-toy-credit`, recorded
`VALID_FAIL_R39_NATIVE_TOY_CREDIT_ANCHOR` with match/slow/fast at
`0.455 / 0.465 / 0.445`.

**This is not evidence against the carrier.** That lane runs under
`r39_native_categorical_edit = True` — the branch where KEEP is a post-hoc collision
label and `keep_head` is bypassed entirely (§2). It exercises a *different decision
structure* on the toy, and it failed a *credit anchor*, not a heterogeneity test.

Two consequences:

- the toy is a candidate cheap source for D7, and would need re-running under the
  learned-keep branch to speak to the carrier at all;
- the existing failure must not be cited either for or against R30 renewal. It is
  evidence about native-categorical edit under a credit anchor.

## 8. What D7 must log, given the above

Beyond the ruling's list, these follow from the code facts here:

- which `act_sequence` branch is live, recorded per run, not per config file;
- realized lifetime from `skill_age` at genuine SET, **never** from segment records;
- both weightings — decision-count and primitive-time — for every distribution;
- termination reason resolved to the six sources of §6, with 4 and 5 separated;
- right-censored commitments reported as a distinct category with their counts;
- age-conditioned KEEP hazard, which no current metric emits;
- `sigmoid(keep_logit)` distribution by age and context, separately from realized outcome;
- entropy-weight values, to test the self-reinforcing concentration path of §2.

The existing R30 metrics are counts and rates (`r30_switch_count`,
`r30_spell_gt_4k0_frac`, `r30_full_sync_set_rate`). **No age-conditioned hazard is
emitted today**, and no per-step trace is persisted, so D7's instrumentation is new
work rather than a logging flag.

### Two things are not recoverable without a schema change

1. **`sigmoid(keep_logit)` is never captured.** It is computed in `_token_context`
   (`r30_fixed_clock.py:199-203`), consumed locally, and never returned;
   `EditSequenceSample` has no field for it, and `HighCheckRow.old_token_logp`
   holds the *combined* log-prob — `log_keep` for KEEP but `log_switch + skill_logp`
   for SET, which conflates the renewal decision with the skill categorical.

   Reconstructing it by replay is **not equivalent**: the weights have moved by
   the time `update_high_from_checks` runs. So the decision probability must be
   threaded live at decision time — `_token_context -> EditSequenceSample ->
   HighCheckRow` — or it is not measurable. This is the one unavoidable schema
   change in D7, and it is on the quantity the whole primitive rests on.

2. **`skill_age` does not advance during evaluation rollouts.** It is incremented
   inside `record_environment_step` (`:3102`), and `export_substrate_gate.py`
   never calls that method. Ages observed on the eval host are therefore
   *check-boundary values*, not elapsed steps.

   This is decisive for the cheap route of D7 §3: an age-conditioned hazard
   computed there would be conditioned on a quantity that does not move. Either
   the eval host gains an increment call, or the measurement is defined purely on
   `prev_ages` — which is check-synchronised in both hosts — and documented as
   check-opportunity age rather than primitive-step age.

Both were found by mapping the two hosts before writing anything, which is what
D0 exists to do.

## 9. Open, and not resolvable here

1. ~~Whether `segment_length_mean` is computed from fragmented records.~~
   **Closed 2026-07-25.** It is not computed under R30 at all (§1). No existing
   metric is misleading; the R30 lane simply has no lifetime measurement.
2. Whether the registered utility level for the search-cost claim should be set on
   the toy or the main scenario.
3. Whether D7 runs on `two_timescale_role_free_actions` under the learned-keep
   branch, or on the main scenario. The toy has ground truth and is cheap; the main
   scenario is what the paper claims about.

Items 2 and 3 are scientific selections, not derivations, and belong to external
review with D7's design.

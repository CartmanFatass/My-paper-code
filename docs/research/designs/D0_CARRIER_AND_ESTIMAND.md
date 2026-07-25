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
| Full refresh | `force_refresh_every_check` | **No.** Always SET |
| **Learned keep** | neither flag | **Yes.** `keep_logit -> sigmoid`, with `log_keep` / `log_switch` factorization |

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

```text
U_i(t, Δ) = E[G_t | agent i re-decides now] - E[G_t | agent i keeps its commitment for Δ]
```

Both expectations start from the **same pre-decision history** and use the **same
continuation semantics**. `G_t` is external task return only.

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

## 6. Censoring — six ways a commitment stops that are not a renewal decision

Any one of these, unseparated, turns a policy measurement into an environment
measurement.

| # | Source | Anchor |
|---|---|---|
| 1 | Episode end | `standalone_agent.py:3104`, `terminal=True` |
| 2 | Team-intent / Z boundary | `team_intent_boundary_trunc_by_duration`, `standalone_agent.py:4164-4190` |
| 3 | Active-mask change — leave / rejoin | `has_active_skill` false ⇒ segment ends |
| 4 | **Forced renewal** | `situation_hazard_forced_renewal_rate`, `standalone_agent.py:4287` |
| 5 | **Policy-update boundary** | `policy_truncated=True`, `standalone_agent.py:3131-3136` — cuts the **credit window**, splits the **record**, does **not** cut the commitment |
| 6 | Duration exhaustion | Legacy only — `duration_remaining <= 0` |

Sources 4 and 5 were not in the ruling's list. Source 4 means renewals occur that
the policy did not choose. Source 5 is the fragmentation trap of §1.

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

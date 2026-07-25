# What this paper is about

```text
owner=user
authority=user_intent -- not derivable from code, and not a Project Manager decision
restated=2026-07-25
claim_and_carrier=external_ruling_20260725_research_direction_and_ledger
```

Read this before any design, any round, and any judgement about whether work is
on the critical path. Every other document in `docs/project/` describes *how* we
work. This one is the only statement of *what for*.

The problem and the goal below are the user's. The paper claim, the primitive and
the carrier were set by the external ruling of 2026-07-25 and are recorded here
because a thesis split across two documents is how the last drift started.

## The problem

HMASD fixes the skill period `k`. In an asynchronous setting a single fixed
period is clearly wrong: different agents face decisions on genuinely different
timescales.

The UAV case makes it concrete. A drone acting as a **relay** holds a role that
persists — a long period is natural. A **service** drone repeatedly re-decides as
users move — a short period is natural. Forcing both onto one `k` mismatches at
least one of them.

## The difficulty, which is the actual contribution

Unbinding `k` is trivial to state and expensive to do. **Letting each agent choose
its own period expands the temporal search space**, and exploration becomes
prohibitive. A method that merely allows variable `k` and then fails to explore it
has not solved anything.

The claim is *not* "an unrestricted action space is expensive, so we constrain
it" — that is a standard design principle, instantiated already by discretised
duration candidates and by termination policies. It only becomes a contribution
if the constraint is **learned, label-free, dynamically applicable, and shown to
improve a registered search-efficiency tradeoff**.

So the paper's shape is:

> On anonymous cooperative MARL tasks with heterogeneous per-agent renewal
> urgency, a decision-time-learned, low-cardinality renewal-class policy attains
> higher held-out external return than the best shared fixed renewal period, and
> reaches a registered utility level with fewer environment interactions or
> high-level decision samples than an unrestricted per-agent renewal policy —
> under matched information, action support and optimizer exposure.

The framing is **structured approximation trading unrestricted temporal
expressivity for finite-budget learnability**. It is not "we accept a suboptimal
result": suboptimality relative to an unknown optimum cannot be established
merely by constraining the controller.

It is also not an anti-collapse contribution. Collapse is one possible failure
mode of unrestricted lifetime learning, not the thesis. The framing has to
survive the case where collapse never occurs.

### Qualifiers the claim carries

- no hand-coded relay/service labels, no role-specific reward;
- no claim of global or asymptotic optimality;
- search cost measured as **interaction and optimizer exposure**, not wall time
  and not nominal action-space size;
- role and membership permutations included in held-out evaluation;
- fixed-`k`, unrestricted, and constrained arms each matched to their own claim.

### What would make it non-obvious

At least one of: the stability class is *inferred* from generic decision-time
state and changes as an agent's function changes; the structure transports across
anonymous slot permutation, join/leave/rejoin and held-out team sizes; strong
matched reductions fail; the search benefit is measured rather than argued;
forcing an agent into the wrong regime moves persistence and utility in the
predicted direction; or the method helps **even when unrestricted lifetime usage
stays broad**, which would prove the contribution is search structure rather than
regularisation.

A hard-coded "relay gets long, service gets short" is a UAV heuristic, not a MARL
contribution.

## The primitive: renewal urgency, not role

The reusable quantity is **per-agent, state-dependent renewal urgency** — how much
value is lost by withholding a re-decision:

```text
U_i(t, Δ) = E[G_t | agent i re-decides now] - E[G_t | agent i keeps its commitment for Δ]
```

Both expectations start from the same pre-decision history and use the same
continuation semantics. Equivalently, a hazard `λ_i(t) = Pr(renewal is beneficial | h_{i,t})`.

- **stable commitment** — withholding re-decision costs almost nothing;
- **flexible commitment** — an immediate re-decision has material expected value;
- the same agent may move between regimes within one lifecycle;
- **realized lifetime is a consequence of this quantity, not its definition.**

"Stable role" is the right intuition and the wrong primitive: naming agents relay
or service supplies the semantics the method is supposed to discover. Churn and
dwell time are **outcomes** — using either to define the property the controller
must learn is circular, and churn additionally conflates true flexibility with
exploration noise and skill-label symmetry.

## The carrier: R30 KEEP/SET

`high_controller = "r30_fixed_clock_ar_edit"` is the primary carrier and the
unrestricted comparator. `legacy_duration` is retained as a **frozen
sampled-duration comparator and bias diagnostic**, not as a candidate mechanism.

R30 is preferred because lifetime emerges from repeated local KEEP decisions
rather than a sampled catalogue value, so it is not capped by the candidate set,
it aligns directly with renewal urgency, and it avoids the legacy path's
short-segment high-sample bias at the carrier level.

### Claim boundary — recorded, not resolved

**R30 does not untie the observation/check clock.** `steps_to_check` is indexed
per environment (`standalone_agent.py:3103`), one shared clock; what R30 unties is
the *realized renewal interval*. So:

- if the target is that relay-like commitments persist while service-like ones
  renew often — R30 carries it;
- if the target literally requires different agents to be *offered* decisions at
  different physical clock times — R30 is a comparator, not the final mechanism.

The relay/service examples above describe persistence and re-decision frequency,
so we proceed on the **functional realized-lifetime** reading. This is the one
place where the ruling interpreted user intent rather than reading it; overturning
it changes the carrier.

## Current state of the codebase — checked 2026-07-25

The previous revision of this section stated three things that are false. They are
recorded here because each one was load-bearing for an ordering that has now been
dropped:

| Was claimed | Actually |
|---|---|
| `legacy_duration` is the live research default | It is the **frozen comparator**; R30 must be selected explicitly |
| The fixed-clock challenger never completed | The stopped 320k pairing is one run; **adaptive R30 arms completed and anchored R31–R33**, with R33 recording R30 safety PASS |
| Collapse has never been observed | Collapse was recorded at **R16.5** under `0.1` intrinsic pressure; `0.05` was adopted as the cleaner base |

What is true and useful:

- The variable-lifetime machinery exists on both paths. Legacy emits
  `duration_logits` over `skill_lifetime_candidates = (3, 7, 13, 24)`; R30 emits a
  single `keep_logit` with `KEEP_TOKEN`/`SET_TOKEN` (`r30_fixed_clock.py:278`).
- SMDP high-level discount and bootstrap are implemented and on
  (`use_smdp_discounted_high_return`, `use_smdp_bootstrap`).
- **Four ways a segment ends other than by its own choice**: episode end, team-intent
  Z boundary (`team_intent_boundary_trunc_by_duration`), active-mask change, and a
  **forced** renewal path (`situation_hazard_forced_renewal_rate`). Any hazard
  reading that does not separate these measures the environment, not the policy.
- **No per-step trace is persisted.** Metrics are aggregated per update. Age-conditioned
  renewal hazard — the quantity the primitive needs — is not currently measurable
  from any existing artifact.
- The completed legacy arm used `(1,2,3,4)` at `k0=10`. The current `(3,7,13,24)`
  configuration has **no completed run**.

## What this means for scope

**On the critical path**: establishing that heterogeneous renewal urgency exists
in the source, and that conditioning renewal on a learned low-cardinality regime
improves external value or search efficiency against both fixed `k` and
unrestricted R30.

**Infrastructure, only if it blocks the above**: member-resolved delayed-credit
identification. It earns promotion only when the selected controller has verified
source access and capacity and *still* cannot orient its renewal policy — and then
only the blocking fragment, not the programme.

**Off the path**: refining an identification protocol beyond what the claim needs.

## The drift this document exists to prevent

By 2026-07-25 the active line had spent six external rounds on whether a delayed
credit estimator could be *identified*, and had never varied `k`. The branch is
named `untied-k`; the goal appeared in the bootstrap round on 2026-07-24 and in no
active document thereafter. Around twenty governance documents existed and not one
said what the paper was about, so every downstream decision optimized for
locally-defensible correctness with no thesis to check against.

Drift of that kind is not caused by bad decisions. It is caused by correct
decisions taken against a missing reference.

**Standing check, applied to any proposed work**: *what does this let us say about
variable `k` that we could not say before?* If the answer needs more than a
sentence, it is probably not on the path.

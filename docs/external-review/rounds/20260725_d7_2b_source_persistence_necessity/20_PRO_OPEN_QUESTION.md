# D7.2B: the positive control admits an optimum that never persists

You ruled on 2026-07-25 that D7 becomes a staged diagnostic and that stage 2B —
the toy positive control on `two_timescale_role_free_actions` under the
learned-keep branch — is the route, since no qualified R30 checkpoint exists.

That is built, it reached competence, and **the source turns out to be unable to
do the job it was chosen for.** I am not asking you to re-rule the route. I am
asking what a replacement source must satisfy, because that is a source-contract
selection and it is yours.

Nothing about the carrier is in question below. The audit machinery, the
interventional hook, `U_opp`/`U_pi`, the normalizer and the event ledger were all
exercised and all transfer unchanged.

## A. What was established

**Competence was reached.** Three epochs, `lr_coordinator = 1e-3`, 1,000 updates —
3,000 high-level optimizer steps. `env_reward_mean` went from chance (~0.44) to
`0.984375` at update 100 and `1.000000` by update 218.

An earlier screen at one epoch and `lr = 1e-4` sat flat at chance for 200 updates
and I nearly read that as a credit failure. It was 200 optimizer steps: at update
150 `keep_prob` was `0.599` against its `0.6` initialization and skill entropy was
`1.096` against a `ln 3 = 1.0986` maximum. The policy had not left its
initialization. Recorded because the same trap sits in front of the prior art —
`EXP-20260715-r39-native-hmasd-toy-credit` recorded `VALID_FAIL_..._CREDIT_ANCHOR`
at `match = 0.455`, and its archived contract shows **20 outer updates and 12,800
timesteps**, a tenth of this screen. That is evidence the toy was not learned in 20
updates, not that it cannot be.

**At competence the policy never uses KEEP.** Both agents SET at every check, in
anti-phase, with `skill_age = 5` at every check:

```text
c1  a0 inc=2(y) SET->1(x)     a1 inc=1(x) SET->3(y)
c2  a0 inc=1(x) SET->2(y)     a1 inc=3(y) SET->1(x)
c3  a0 inc=2(y) SET->1(x)     a1 inc=1(x) SET->3(y)
```

**The mechanism is structural, not a property of this checkpoint.** The team reward
is the better of the two agent-to-duty assignments, so any pair holding one correct
x-skill and one correct y-skill scores `1.0`. From `(A = x+, B = y+)`, when the fast
target flips to `y-` the needed set `{x+, y-}` is reachable two ways:

| Route | A | B | Tokens |
|---|---|---|---|
| persist | keeps `x+` | `y+ -> y-` | KEEP, SET |
| **swap** | `x+ -> y-` | `y+ -> x+` | **SET, SET** |

The swap is always available: a SET masks only the *incumbent*, and under the swap
both agents move to a skill they do not currently hold. So there are **two distinct
optima and one of them never persists**, with every realized commitment lifetime
pinned at exactly one check interval.

**Measured** — full-power audit of the run's final checkpoint, 24 episodes ×
4 replicates, 336 pairs, 0 dropped, `act_sequence` branch `learned_keep`. The
audited object was declared to be the final checkpoint while the run was still
training and before any audit had been run, because competence arriving early makes
checkpoint choice an outcome-relevant knob.

`B_H` measured from two source controls before the audit: `B_30 = 10.000`
(constructive `30.000`, null `20.000`, 72 windows); `B_5 = 1.875`.

```text
branch  NONFORMAL_NO_URGENCY_SEPARATION_D7_2B

A  slow_match  1.0000  LCB 1.0000     fast_match 1.0000  LCB 1.0000  PASS (floor 0.75)
B  U~_flex     0.43006 LCB 0.40828                                   pass (floor 0.10)
   U~_stable   0.25186 UCB 0.27496                                   FAIL (ceiling 0.05)
   difference  0.17820 LCB 0.15908                                   FAIL (floor 0.20)
   U~_opp,flex 0.43006 LCB 0.40828   split-sample
C  P(SET | flex)    1.0000                                           pass
   P(KEEP | stable) 0.0000                                           FAIL (floor 0.75)
   gap              0.0000                                           FAIL (floor 0.50)
   full-sync SET    1.0000  mixed-urgency                            FAIL (ceiling 0.25)
```

**`U~_stable = 0.252` is the load-bearing number, not `U~_flex`.** Renewing the
holder of the *low-urgency* duty is still worth a quarter of the whole renewal
headroom. That is the swap signature: under swap coordination **both** agents'
renewals are load-bearing, because forcing the low-urgency agent to KEEP breaks the
coordination its partner has learned to expect, and the partner — regenerated under
the modified prefix, per your continuation semantics — does not compensate. B fails
twice: `U~_stable` at five times its ceiling, and the difference short of its floor.

C is exact `0` or `1` with zero variance across 24 episodes.

One correction I am volunteering because it bears on how much weight to give small
checks: a 2-episode machinery validation earlier gave `flex 0.214 / stable 0.232 /
difference -0.018`, which read as *no separation at all*. At full power the
difference is positive but insufficient. The negative sign was a small-sample
artifact, and no conclusion was drawn from it.

## B. What this did to the reasoning, including mine

Your D7 ruling anticipated the shared-reward objection and dismissed it:

> The shared reward is **not** an objection — at a given history the current
> assignments break the instantaneous symmetry, so a focal KEEP/SET intervention
> has a well-defined team-return effect.

I now read that as true but insufficient. The intervention **is** well defined;
what fails is the inference from it. Instantaneous asymmetry gives a focal effect;
it does not make persistence *necessary*, and only necessity makes a null
informative.

My own realization contract inherited the same gap and I want it on the record: I
argued the urgency rule is non-discretionary because an agent's regime is read from
the axis of its incumbent, which is sound **instantaneously**. I then used "stable"
as though it were an agent-level regime that would hold. Under a swap optimum it
does not.

## C. The part I nearly did not ask about

A pre-send adversarial pass over this question found something my own disposition
was suppressing, and it may matter more than Q2.

**Both optima score `1.0`. The policy chose the one without persistence — and the
carrier's own initialization makes that the cheaper one to reach.**

```text
keep_head.weight is zero-initialized; its bias is set to logit(keep_init = 0.6)
  => keep_logit starts state-INDEPENDENT

swap optimum    needs: keep bias down (a scalar) + skill-head alternation
                       (the skill head is already state-dependent through `hidden`)
persist optimum needs: keep_head to acquire state-DEPENDENT WEIGHTS,
                       so it can KEEP for the x-holder and SET for the y-holder
```

So the swap is reachable with strictly less learning than persistence, and the
policy walked to it **despite starting biased toward KEEP at 0.6**.

**The full-power ledger confirms this rather than merely suggesting it** — 384 rows
across 24 episodes:

```text
token_kind        takes exactly one value in the entire ledger: SET
                  KEEP never occurs, not once
skill_age         exactly 5 at every check past the first
                  every commitment lives precisely one check interval

keep_prob         min 0.000000   max 0.000168   mean 0.000017
    flex     n=168   mean 0.000011   std 1.71e-05
    stable   n=168   mean 0.000023   std 3.34e-05
    between-regime difference 1.2e-05  <  within-regime std 3.3e-05
```

So `keep_head` never acquired state dependence. It lowered its bias and stopped.
The toy was solved entirely through the skill head, and the renewal decision — the
primitive this whole line is about — ended up **degenerate and unused**.

This is an observation about the **carrier**, not the source, and it sits awkwardly
against my Q1 disposition that the carrier is untouched. I am not claiming it
refutes anything — a degenerate source cannot support that — but I should not have
left it out, and I would rather you saw it than have it surface later as a premise
I had already smuggled in.

## Q0 — is a replacement positive control even the right successor?

Asked first because it can make Q2 moot.

- **If the retirement routes straight to D7.3** (the main-scenario urgency audit),
  say so and Q2 is unnecessary.
- **If a positive control is still required first**, Q2 stands.
- **If the answer depends on Q4** — whether the main scenario shares the
  degeneracy — say which way each branch goes.

## Q1 — do you accept the retirement, and at what scope?

My proposed disposition: this retires **the benchmark-comparator pair** —
`two_timescale_role_free_actions` as D7's positive control — under your
*"benchmark gives no access, or cannot separate candidates"* category, and nothing
else. Carrier, estimands, machinery and the P1–P4 portfolio intact.

- **If you accept that scope**: go to Q2.
- **If you think a null on this source is still informative** despite two optima,
  say what makes it so, because I cannot see it and I will otherwise build a
  replacement I do not need.
- **If you think the scope is too narrow** — that something about the carrier or
  the estimand is also implicated — name it, since I have written the opposite into
  the ledger and the evidence note.
- **Given section C**, is there a third reading I should register: that the
  informative content here is *optimum selection* — the carrier converging to the
  non-persistent optimum when both are available and it started biased toward
  KEEP? If that is a legitimate reading, it is a **stronger** statement than the
  one I wrote, and it needs a pre-registered form before I measure it across seeds
  rather than after.

## Q1a — was the competence budget change legitimate?

Stated plainly because it is the kind of thing that becomes a bad premise. Condition
A failed flat, and I then raised the optimizer budget — three epochs, `lr 1e-3`,
five times the updates — until A passed. I hold that this is sound because A is a
competence *prerequisite* and not a scientific reading, its thresholds were never
touched, and the routing rule "a flat A buys budget, not a conclusion" was written
into the contract **before** the flat result. But I chose it, after seeing a failure.

- **If that is acceptable**, may the same latitude apply on the replacement source,
  or do you want the competence budget pre-registered there?
- **If it is not**, what is the correct procedure for reaching a competence floor
  without tuning against it?

## Q2 — what must a replacement source satisfy?

The requirement I would write is: **persistence must be necessary for optimality,
not merely permitted.** Concretely, no optimal policy may achieve the ceiling with
every commitment lasting one check interval.

Four candidate mechanisms. I have a preference but this is your selection, and one
of them collides with a frozen constraint:

| # | Mechanism | Cost | Note |
|---|---|---|---|
| a | **Tenure-dependent effectiveness** — a duty's contribution ramps with how long its holder has served it | small env change | Makes persistence strictly better without any penalty term |
| b | **Agent-specific duty affinity** — each agent has a private per-axis effectiveness, so the assignment matters and swapping is lossy | small env change | Breaks permutation invariance directly |
| c | **Switch cost** — a SET costs external reward | small | **Collides**: the R30 contract is reward-pure and forbids edit/switch penalties (`edit_penalty_alpha`, `switch_penalty_beta` are hard-zeroed and a construction check rejects them). This route needs an explicit exception from you |
| d | **Asymmetric action support** — agents hold disjoint skill subsets so a swap is not expressible | small | Removes the degeneracy by construction, but also removes role-freeness, which your earlier ruling wanted |

- **If you rule (a) or (b)**: is the tenure/affinity signal permitted in the
  centralized state that the high controller reads, or must it stay evaluator-only?
  D7 forbids feeding role labels; a tenure term is not a label but it is close
  enough that I will not decide it.
- **If you rule (c)**: I need the reward-purity exception stated explicitly,
  including whether the cost enters the external return that `U` is computed on —
  because if it does, `U` then contains the very penalty that manufactures the
  effect.
- **If you rule (d)**: does the loss of role-freeness invalidate the comparison
  with the main scenario, where the roster is open?

## Q3 — does the class constraint generalize?

My candidate general statement, which I want ruled rather than assumed:

> A source whose reward is invariant to which agent serves which duty cannot
> establish heterogeneous **individual** renewal urgency, because role exchange
> substitutes for persistence at zero cost.

- **If that holds as a class constraint**, it is a standing requirement on every
  future source built for the variable-`k` claim, and I will add it to the
  pre-freeze checklist.
- **If it does not**, what additional condition makes a permutation-invariant
  source usable? I would rather have the narrow true statement than my broad one.

## Q4 — does this reach D7.3, D8, or the main scenario?

This is the question I am least able to answer and the most worried about. The main
scenario's service roster is, as far as I can read it, also largely indifferent to
*which* member covers a demand.

- **If the main scenario shares the degeneracy**, then D7.3 inherits it and the
  variable-`k` claim has a source problem rather than a mechanism problem — which
  reorders the ledger substantially. Say so and give the revised order.
- **If it does not**, what breaks the symmetry there? Naming it would also tell me
  what to import into the replacement toy, which is cheaper than inventing one.

## Q5 — does the estimand stay agent-level?

D0 defines `U_i` per agent. Under duty churn the *duty* persists while the agent
serving it changes, so a duty-level persistence estimand would have been satisfied
by the swap solution.

- The paper's claim is about **individual** lifetime, so I believe agent-level is
  correct and the source must be fixed rather than the estimand. Confirm or correct.
- **If you would reframe to duty-level**, that changes what "untied `k`" claims,
  and I would want that stated before anything else is built on it.

## Q6 — anything above you would reorder

Nothing is built for the replacement. Changing the ordering now is free.

## Evidence to read

- `docs/research/cdc/EVIDENCE_NOTES/20260725_D7_2B_TOY_SWAP_DEGENERACY_DERIVATION.md`
- `docs/research/designs/D7_2B_TOY_POSITIVE_CONTROL_REALIZATION.md`
- `docs/research/designs/D7_R30_RENEWAL_DIAGNOSTIC.md`
- `docs/research/designs/D0_CARRIER_AND_ESTIMAND.md`
- `docs/project/RESEARCH_GOAL.md`
- `docs/project/EXPLORATION_LEDGER.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `envs/pettingzoo/two_timescale_role_free_actions.py`
- `ha_ctse_process/r30_fixed_clock.py`
- `scripts/audit_d7_2b_toy_positive_control.py`
- `config_d7_2b_toy_learned_keep.py`

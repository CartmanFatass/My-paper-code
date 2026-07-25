# D7.2B — the toy positive control admits a full-sync swap optimum

```text
id=D7.2B-SWAP-DEGENERACY
status=closed -- derivation complete, final-checkpoint audit registered,
       ACCEPTED by External Pro 2026-07-25 with a broadened correction
ruling=docs/external-review/rounds/20260725_d7_2b_source_persistence_necessity/21_PRO_OPEN_RAW.md
cost=zero compute for the derivation; one toy competence run for the audit
source=envs/pettingzoo/two_timescale_role_free_actions.py
contract=docs/research/designs/D7_2B_TOY_POSITIVE_CONTROL_REALIZATION.md
parent=docs/research/designs/D7_R30_RENEWAL_DIAGNOSTIC.md
```

`two_timescale_role_free_actions` cannot serve as a positive control for renewal
urgency. It admits an optimal policy in which **no commitment ever persists**, so
it does not make the behaviour under test necessary — only permitted.

This retires the **source as D7's positive control**. It retires nothing about the
learned-keep carrier, R30, or the P1–P4 portfolio.

## The derivation

The team reward is the better of the two agent-to-duty assignments
(`_score_actions`, `direct` versus `swapped`). With the supplied executor every
action is a unit axis vector, so:

```text
reward = 1.0  <=>  the pair holds {correct x-skill, correct y-skill}, in either order
```

Within one slow period the x target is constant and the y target flips at every
check. Take the pair at `(A = x+, B = y+)` and let the y target flip to `y-`. The
needed set is `{x+, y-}`, and it is reachable two ways:

| Route | A | B | Tokens |
|---|---|---|---|
| persist | keeps `x+` | `y+ -> y-` | KEEP, SET |
| **swap** | `x+ -> y-` | `y+ -> x+` | **SET, SET** |

The swap is always available, because under learned keep a SET masks only the
*incumbent* and both agents are moving to a skill they do not currently hold. So
both routes reach reward `1.0`, and the swap does it with a full-sync SET and a
realized commitment lifetime of exactly one check interval for every commitment.

**Two distinct optima, one of which never persists.** A positive control must make
its target behaviour necessary. This source leaves it optional, so a null tells us
nothing about whether the carrier *can* express urgency.

## What was observed

**Registered result — full-power audit of the run's final checkpoint**, 24 episodes
× 4 replicates, 336 pairs, 0 dropped, `act_sequence` branch `learned_keep`. The run
completed 1,000 updates with its last twenty all at exactly `1.0`.

`B_H` measured from the two source controls before the audit: `B_30 = 10.000`
(constructive `30.000`, null `20.000`, 72 windows); `B_5 = 1.875`.

```text
branch  NONFORMAL_NO_URGENCY_SEPARATION_D7_2B

A  slow_match  1.0000  LCB 1.0000        fast_match 1.0000  LCB 1.0000   PASS (floor 0.75)
B  U~_flex     0.43006 LCB 0.40828                                       pass (floor 0.10)
   U~_stable   0.25186 UCB 0.27496                                       FAIL (ceiling 0.05)
   difference  0.17820 LCB 0.15908                                       FAIL (floor 0.20)
   U~_opp,flex 0.43006 LCB 0.40828   (split-sample)
C  P(SET|flex)      1.0000                                               pass
   P(KEEP|stable)   0.0000                                               FAIL (floor 0.75)
   gap              0.0000                                               FAIL (floor 0.50)
   full-sync SET    1.0000  (mixed-urgency)                              FAIL (ceiling 0.25)
```

**`U~_stable = 0.252` is the load-bearing number, not `U~_flex`.** Renewing the
holder of the *low-urgency* duty is still worth a quarter of the entire renewal
headroom. That is the swap signature: under swap coordination both agents'
renewals matter, so B fails twice over — `U~_stable` is five times its ceiling and
the difference misses its floor.

**A 2-episode machinery validation earlier gave `flex 0.214 / stable 0.232 /
difference -0.018`**, which read as no separation whatsoever. At full power the
difference is positive (`0.430` against `0.252`) but insufficient. The small-sample
sign was an artifact, and it is recorded because it is the reason machinery-check
numbers must never be used as a result.

`U~_opp,flex` equals `U~_pi,flex` to five decimals. The split-sample maximum over
non-incumbent skills recovers exactly the policy's own choice, which is what a
deterministic optimal skill selection should give — a consistency check on the
estimator rather than a separate finding.

C is exact `0` or `1` with **zero variance across 24 episodes**: the policy SETs
both agents at every check.

The event ledger shows the mechanism directly — both agents SET at every check, in
anti-phase, with `skill_age = 5` at every one:

```text
c1  a0 inc=2(y) SET->1(x)     a1 inc=1(x) SET->3(y)
c2  a0 inc=1(x) SET->2(y)     a1 inc=3(y) SET->1(x)
c3  a0 inc=2(y) SET->1(x)     a1 inc=1(x) SET->3(y)
```

`U~_stable ≈ U~_flex` is coherent rather than anomalous. Under a swap-coordinated
policy **both** agents' renewals are load-bearing: forcing the low-urgency agent to
KEEP breaks the coordination its partner has learned to expect, and the partner —
correctly regenerated under the modified prefix, per D0's continuation semantics —
does not compensate. So renewal has value for both regimes and the contrast
vanishes.

## The carrier-side observation, found by a pre-send adversarial pass

Both optima score `1.0`, and the policy chose the one without persistence. The
carrier's own initialization makes that the cheaper route:

```text
keep_head.weight is zero-initialized, bias = logit(keep_init = 0.6)
  => keep_logit starts state-INDEPENDENT

swap    needs: keep bias down (a scalar) + skill-head alternation,
               and the skill head is already state-dependent through `hidden`
persist needs: keep_head to acquire state-DEPENDENT WEIGHTS, to KEEP for the
               x-holder and SET for the y-holder
```

Measured, not argued. The full-power ledger, 384 rows across 24 episodes:

```text
token_kind   takes exactly one value in the whole ledger: SET -- KEEP never occurs
skill_age    exactly 5 at every check past the first: every commitment lives
             precisely one check interval

keep_prob    min 0.000000   max 0.000168   mean 0.000017
    flex     n=168   mean 0.000011   std 1.71e-05
    stable   n=168   mean 0.000023   std 3.34e-05
    between-regime difference 1.2e-05  <  within-regime std 3.3e-05
```

`token_kind ∈ {SET}` and `skill_age ≡ 5` are the derivation's two predictions,
observed exactly and without exception.

`keep_head` never acquired state dependence; it lowered its bias and stopped. The
toy was solved entirely through the skill head, leaving the renewal decision — the
primitive this line exists to study — **degenerate and unused**.

This is about the carrier, not the source, and it does not refute anything: a
source with two optima cannot support a claim about which one a good carrier
*should* pick. It is registered as an open observation, and whether "optimum
selection" is a legitimate pre-registered reading is one of the questions in the
round below. It is recorded here because it was nearly omitted, and an unmarked
omission becomes a premise.

## What this does to the design's reasoning

D7 anticipated the shared-reward objection and dismissed it:

> The shared reward is **not** an objection — at a given history the current
> assignments break the instantaneous symmetry, so a focal KEEP/SET intervention
> has a well-defined team-return effect.

That is true and insufficient. The intervention *is* well defined; what fails is
the inference from it. Instantaneous asymmetry gives a focal effect; it does not
make persistence necessary, and only necessity makes a null informative.

The realization contract inherited the same gap. Its section 3 argued the axis rule
identifies urgency without discretion, and that holds *instantaneously* — an
x-axis incumbent is serving the low-urgency duty at that check. But "stable" was
read as though the agent would continue serving that duty. Under a swap optimum it
will not, so low **duty** urgency does not imply low **agent** renewal value. The
identification is sound; its interpretation as an agent-level regime is not.

## Disposition

Per `AGENTS.md`, *Result interpretation*: "the benchmark gives no access, or cannot
separate candidates" retires **that benchmark-comparator pair**. Concretely:

- **retired** — `two_timescale_role_free_actions` as D7's positive control, and
  the D7.2B branch reading as a statement about the carrier;
- **intact** — the learned-keep carrier, R30, `U_opp`/`U_pi`, the interventional
  machinery, `B_H`, and the P1–P4 portfolio. All were exercised and none was
  refuted;
- **kept** — the audit, the forcing hook and the ledger transfer unchanged to any
  replacement source. The build is not wasted.

A replacement source must make persistence **necessary**, not optional. The
cheapest structural fix to state (not yet ruled, and it is a scientific selection
that belongs to External Pro): break the permutation invariance so that duties are
attached to agents over an interval, for example by making a duty switch cost
something, or by giving each duty an agent-specific component so the swap is not
free. Either changes the source contract and must be ruled, not chosen here.

## Standing check

From `RESEARCH_GOAL.md` — *what does this let us say about variable `k` that we
could not say before?* That a permutation-invariant multi-agent source cannot
establish heterogeneous renewal urgency, because role exchange substitutes for
persistence at no cost. That is a constraint on every future source built for the
variable-`k` claim, and it was cheap to learn.

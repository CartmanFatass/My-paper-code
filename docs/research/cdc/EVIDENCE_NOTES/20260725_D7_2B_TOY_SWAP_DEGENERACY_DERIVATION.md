# D7.2B — the toy positive control admits a full-sync swap optimum

```text
id=D7.2B-SWAP-DEGENERACY
status=derivation complete; final-checkpoint audit pending
cost=zero compute for the derivation; observed on the competence run's update-100 checkpoint
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

The competence run's update-100 checkpoint, `env_reward_mean = 0.984375` rising to
`1.000000` by update 218, audited at small scale — machinery validation, not the
registered result, which is reserved for the final checkpoint per the contract:

```text
condition A   slow_match 1.0   fast_match 1.0        competence fully met
condition C   P(SET|flex)      1.0
              P(KEEP|stable)   0.0                   KEEP is never used at all
              full-sync SET    1.0   (mixed-urgency) ceiling is 0.25
condition B   U~_flex          0.214
              U~_stable        0.232                 no separation
              difference      -0.018
```

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

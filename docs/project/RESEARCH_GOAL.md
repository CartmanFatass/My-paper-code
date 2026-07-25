# What this paper is about

```text
owner=user
authority=user_intent -- not derivable from code, and not a Project Manager decision
restated=2026-07-25
supersedes_silence=this document did not exist until 2026-07-25
```

Read this before any design, any round, and any judgement about whether work is
on the critical path. Every other document in `docs/project/` describes *how* we
work. This one is the only statement of *what for*.

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
its own period massively expands the action space**, and exploration becomes
prohibitive. A method that merely allows variable `k` and then fails to explore it
has not solved anything.

So the paper's shape is:

> Unbinding `k` produces an action space too costly to explore. We reintroduce
> tractability with an assumption or constraint that collapses it onto a small set
> of periods, and we accept a **suboptimal** result in exchange for a search cost
> that is actually payable.

The claim is explicitly not optimality. It is that a constrained variable-`k`
policy beats fixed `k` at a search cost far below unconstrained variable `k`.

## Two candidate constraints

1. **Self-learned convergence** — let the period be learned and converge onto a
   small number of values, rather than fixing them by hand.
2. **Role-conditioned period classes** — distinguish only long-term and
   short-term `k`, tied to what the agent is doing (relay versus service).

Both are constraints on the same explosion. Either can carry the paper; the second
is cheaper to state and to defend.

## Current state of the codebase — checked 2026-07-25, not assumed

Four findings that make the remaining work much smaller than the drifted line
suggested. All from reading configuration, objective code and `ExpRecord`.

**Variable `k` is already built and is the default.** `high_controller =
"legacy_duration"` is the variable-duration mode; the high policy already emits
`duration_logits` alongside `skill_logits`; and the search space is already
discretised as `skill_lifetime_candidates = (3, 7, 13, 24)`, in high-level
intervals so the primitive horizon is `candidate * k`.

**The config already names the role distinction.** The comment on those
candidates reads *"UAV service/relay formation is a long-horizon task"* — the
stable-versus-flexible split, written down and unexploited.

**The fixed-clock challenger never won.**
`EXP-20260714-r30-fixed-clock-paired-320k` is recorded as *stopped — superseded
before completion*: the legacy arm completed, the R30 treatment retry was stopped
when a faster screen was chosen, and **no M1–M4 scientific outcome exists**. So
`legacy_duration` is not a retired path — it is the live default and the only
controller with a completed arm. That also answers whether it trains: a 320k arm
completed.

**But the paper's premise is not yet evidenced.** `duration_entropy_floor_*`
exists, default-off, described in-code as *"a one-variable guard for duration
collapse, not a new task-specific reward"* — so collapse is **anticipated by the
engineering and nowhere observed in `ExpRecord`**.

That last point sets the first real experiment. Before designing a constraint,
**measure whether unconstrained duration selection actually collapses** on the
existing `legacy_duration` path. It is cheap, the machinery exists, and it
decides the shape of the paper:

- if duration collapses, that is the motivating figure and the constraint is the
  contribution;
- if it does not collapse, the problem statement is wrong and the contribution
  has to be re-argued — better to learn that from one run than after building a
  constraint for a problem that is not there.

## What this means for scope

**On the critical path**: anything that varies `k`, constrains the resulting
search, or measures a constrained variable-`k` policy against fixed `k`.

**Infrastructure, only if it blocks the above**: delayed credit assignment across
periods of unequal length is a real dependency, because a variable period changes
what a credit signal is attached to. It earns its place only while it is blocking
a variable-`k` result — not as a research programme of its own.

**Off the path**: refining an identification protocol beyond what a variable-`k`
claim needs.

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

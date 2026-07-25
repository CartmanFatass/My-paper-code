# Exploration ledger

```text
owner=project_manager
policy=user_20260725 -- stay open, record promising directions, order by cost,
       validate cheapest first unless the user designates a direction
```

This is **not** the decision ledger. That one records protected decisions inside
a frozen contract. This one records *directions we might explore*, so that a
promising idea is neither lost nor silently promoted to the critical path.

## How it is used

- Anything plausible gets an entry, including ideas we do not intend to run soon.
  A cheap entry costs a row; a lost direction costs a rediscovery.
- Ordered by **cost**, cheapest first, and worked in that order **unless the user
  designates one**.
- A direction that is killed stays in the ledger with the reason. Deleting it
  invites its re-proposal — the same rule the decision ledger uses for rejected
  entries.
- `settles` is recorded next to `cost` deliberately. Cheapest-first is the
  ordering rule, but a cheap probe that resolves nothing is worse than a slightly
  costlier one that kills or confirms a direction. When two entries are close in
  cost, prefer the one that settles more.

Cost is recorded on three axes because they are not interchangeable: **build**
(implementation effort), **compute** (runs), **review** (external rounds, which
are serial and the scarcest).

## Active directions

| id | Direction | Build | Compute | Review | Settles |
|---|---|---|---|---|---|
| **D1** | **Instrumented `legacy_duration` run: log duration usage entropy + histogram over `(3,7,13,24)`, and per-agent skill-assignment churn, per role** | small — logging only | one run | 0 | **Both premises at once.** Whether unconstrained duration actually collapses, and whether stable/flexible roles are separable from churn |
| D3 | Role-conditioned duration classes — derive long/short from measured role stability instead of searching | medium | one paired run vs fixed `k` | 1 | Whether the constraint beats fixed `k` **and** unconstrained duration |
| D4 | Self-learned convergence of duration onto few values | large | several runs | 1–2 | Whether periods can be learned rather than hand-specified |
| D6 | Grill mechanism V1/V2 validation | medium | none | 1 | Whether the discovery mechanism transfers. Tooling, not science |
| D5 | G20R3 identification rework — nine blockers | large | several runs | 2+ | Whether delayed credit is identifiable. **Infrastructure only** |

### Why D1 is first, and by a wide margin

It is the only entry whose build cost is *logging* and whose review cost is zero,
and it settles both premises the paper rests on. Everything below it is
conditional on its result:

- if duration **collapses**, that is the motivating figure and D3 is the
  contribution;
- if it **does not collapse**, the problem statement is wrong and D3/D4 are
  built for a problem that is not there.

Two facts make it cheap. The machinery exists — `legacy_duration` is the live
default, the high policy already emits `duration_logits`, and the candidates are
already discretised. And a 320k legacy arm has already completed, so the path
trains.

One fact makes it necessary rather than merely useful: **the premise is currently
unevidenced.** `duration_entropy_floor_*` exists default-off, described in-code
as a guard for duration collapse, and `ExpRecord` records no observed collapse
anywhere.

### Why D1 absorbed a separate entry

Role-stability measurement was going to be its own direction, and was briefly the
cheapest candidate on the theory that existing logs might already contain
per-agent skill assignments. They do not — a run log holds only a small
`result/*.json`, with no per-step traces. So role stability needs a run, and it
needs *the same* instrumentation on *the same* path as the collapse measurement.
One run answers both.

## Retired directions

| id | Direction | Why retired |
|---|---|---|
| D2 | Compute role stability from existing logs, zero compute | Traces are not persisted; run logs contain only a small result json. Folded into D1 |

## Standing check before promoting any entry

From `RESEARCH_GOAL.md`: *what does this let us say about variable `k` that we
could not say before?* If the answer needs more than a sentence, the entry
belongs in this ledger rather than on the critical path.

D5 fails that check today. It is kept because delayed credit across unequal
periods is a real dependency the moment a variable period changes what a credit
signal attaches to — but it earns promotion only when it blocks a variable-`k`
result, not before.

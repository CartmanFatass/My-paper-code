# D7.S — six more guards that cannot fail

External review found two unfailable guards on this instrument in two
consecutive rounds: the `stream_seed` CRN tautology, and the
`full_state_fingerprint` clone/restoration cluster. Two in two rounds is a
writing habit, not two accidents, so the rest were swept for internally on
2026-07-27 rather than waiting for a third round to find the third one.

Audited at commit `8585352`, excluding the two known cases and the concurrent
`full_state_fingerprint` rewrite. Every finding below carries a **concrete
mutation to production code that leaves the suite green** — a finding without
one is a suspicion and was dropped.

Spot-verified independently before adoption: `default_rng(seed)` at
`audit_d7_s_event_aligned.py:1098`, the `charging_mask`/`lifecycle_mask`
aliasing at :1805-1812, and the `getattr(env, "np_random", None)` fallback at
:2320 all read as reported, at the cited lines.

## The findings

| # | Site | Cannot fail because | Green-leaving mutation | Reaches a wrong claim? |
|---|---|---|---|---|
| 1 | `audit_d7_s_event_aligned_test.py:651` `test_stream_seed_is_deterministic` | `f(x) == f(x)`, one process | `stream_seed` → salted `hash()` | Yes — pooled shards from separate invocations become incommensurable |
| 2 | :917 bootstrap determinism | `f(x) == f(x)`; no test asserts a *different* seed differs | `default_rng(seed)` → `default_rng(0)` | **Yes, most directly** |
| 3 | `pool_d7_s_event_aligned_shards_test.py:181` order invariance | All six fixture topologies carry identical degenerate values | Feed unsorted rows to the bootstrap, report sorted | Yes — `U*` depends on CLI argument order |
| 4 | :1984 condition 1A | Fixture `step()` draws no randomness at all | Seed reduction `% (2**32-1)` → `% 1000` | Yes — CRN pairing becomes accidental |
| 5 | :931 state-hash equality | `dict(snap)` is a *shallow* copy — same ndarray objects | Drop `station_occupancy`, `station_queue` from `array_keys` | Yes — flips event eligibility |
| 6 | :1923 condition 3 | `clone()` already raises on that exact comparison first | `np_random` → `_np_random` in `_rng_state_token` | Yes — removes RNG from condition 5 and `assert_source_intact` |

Finding 1 sits **43 lines above** the CRN test that was already repaired. The
repair fixed the instance review pointed at and did not look one screen up.
That is the clearest single piece of evidence that this is a habit.

### The most dangerous one

Finding 2. `hierarchical_bootstrap_quantity` seeds `hierarchical_bootstrap_events`
per `(iteration, slot)`. A version ignoring that seed makes the within-topology
resample **identical in every topology slot of every outer iteration**,
collapsing that variance component. `u_star_iters` narrows, `LCB95(U*)` becomes
over-confident, and `decide_branch` returns 5 or 7 where the honest answer is 10
(unresolved). A wrong published branch, produced by a test that reads as
coverage of exactly this.

## One production defect found incidentally

**`_rng_state_token` returns the constant `"none"` on attribute-name drift**
rather than raising. It is the *sole* RNG coverage inside
`full_state_fingerprint`, because a `RandomState`/`Generator` is neither
ndarray nor scalar nor numeric list and so the include-by-default loop skips
it. Silent degradation of the only RNG signal — the same shape as the blocker
itself: a silent fallback where a loud failure belonged.

### Withdrawn — the mask aliasing is declared, not silent

The sweep also reported `real_env_state_snapshot` aliasing `charging_mask` and
`lifecycle_mask` to the same object (`:1805-1812`) as a second defect, and the
first version of this note adopted that. **It is wrong.** The function's own
docstring states the identity explicitly — "lifecycle mask (CHARGE_ABSENT ==
`uav_charging`, per the module's own two-state real-env realization documented
in its header)". The aliasing is the documented modelling choice, not an
accident.

The redundancy is real — one of six keys carries no independent information —
but a *declared* redundancy is not the blocker shape, and filing it as one
would have sent an implementer to "fix" a deliberate semantic. Recorded rather
than deleted because over-accepting a plausible finding is the same failure as
under-checking a test.

## Cause, and the rule adopted

One cause in all six: **the tests were written from the implementation, so both
sides of every comparison come from the same code path.** It surfaces three
ways — determinism asserted as `f(x) == f(x)` in a single interpreter; digest
tests varying only the one field the author had in mind; and fixtures made
degenerate or randomness-free for tractability, deleting exactly the variance
the property is about.

The rule adopted in `AGENTS.md` is the smallest one that would have caught most
of them: **a guard test needs a paired negative**, with the perturbation drawn
from the whole declared domain, and anything called *registered*, *stable* or
*reproducible* must be observed reproducing **across a process boundary**.

## Standing

These are **not** part of the Stage B blocker and do not widen its closure
conditions. They are gates on the same launch: findings 2, 3 and 4 can each move
the result branch, so the audit does not carry a conclusion until they are
repaired. Sequenced after the fingerprint work rather than beside it, because
both touch `audit_d7_s_event_aligned_test.py`.

# D7 — frozen spec: capture the renewal decision probability

```text
scope=one bounded schema change, diagnostic capture only
invariant=required under every branch of the outstanding D7 review round
protected=probability factorization, gradients, RNG -- all must be provably unchanged
```

This is the one part of D7 that does not depend on the review answer. Host,
scenario, descriptive-versus-interventional and comparator design are all open;
this is required regardless, because without it the primitive's own quantity is
not measurable at all (`D0_CARRIER_AND_ESTIMAND.md` §8).

## What is missing

`sigmoid(keep_logit)` is the per-agent, per-check probability of withholding
re-decision — the observable form of renewal urgency. Today it is computed and
discarded.

`HighCheckRow.old_token_logp` is **not** a substitute: it holds `log_keep` on KEEP
rows but `log_switch + skill_logp` on SET rows, so it conflates the renewal
decision with the skill categorical. Post-hoc replay is **not** a substitute
either: `update_high_from_checks` steps the optimizer, so a replayed logit is
taken under different weights than the decision was.

## What already exists

Less is missing than a first reading suggests:

- `_token_context` **already returns** `keep_logit` — `r30_fixed_clock.py:210`;
- `act_sequence` **already binds** it — `:234`.

It is dropped at the `EditSequenceSample` boundary. The change is to carry it
three hops further, not to compute anything new.

## Required change

1. **`EditSequenceSample`** (`r30_fixed_clock.py:21-30`, `@dataclass(frozen=True)`)
   gains one field, `keep_prob: torch.Tensor`, shaped like `token_kind`.
   Every construction site must supply it — the dataclass is frozen, so a missed
   site is a construction error rather than a silent `None`.

2. **`act_sequence`** accumulates it in the existing per-token loop alongside
   `kinds` / `logps` / `entropies`, and stacks it at `:311-314`.

3. **`HighCheckRow`** (`:494-515`) gains a matching per-position array, populated
   where `token_kind` and `old_token_logp` already are
   (`standalone_agent.py:4058-4073`).

4. **`HIGH_BUFFER_VERSION`** (`:18`) goes `1 -> 2`. `HighCheckBuffer.version`
   carries it, and a row schema change that leaves the version alone is how a
   stale buffer gets read as a current one.

## Three constraints that make this safe, and are the whole risk

**These are the acceptance criteria. The field itself is trivial; every way this
goes wrong is here.**

1. **`.detach()` is mandatory.** The captured value is diagnostic and must never
   create a gradient path. `keep_logit` is live in the graph at the point of
   capture — storing it undetached would put a measurement into the loss and
   change training. Capture `torch.sigmoid(keep_logit).detach()`.

2. **`token_logp` must be byte-identical before and after.** The probability
   factorization is protected. This change adds an observation; it must not
   reorder, rescale or re-derive the log-prob. The existing
   `log_keep` / `log_switch + skill_logp` construction at `:296-297` is untouched.

3. **RNG consumption must be unchanged.** `sigmoid` draws nothing, so this holds
   by construction — but it must be *demonstrated*, not asserted, because paired
   replay under common random numbers is what D7's interventional half depends
   on. A same-seed run before and after must produce identical trajectories.

## Branch semantics — record absence, never a plausible number

`act_sequence` has three regimes (`D0` §2) and `keep_head` may be `None`
(`:199-203`, which substitutes zeros). Under a `None` head, `sigmoid(0) = 0.5` —
a fabricated coin-flip that is indistinguishable from a genuinely undecided
policy.

Record **`NaN`**, not `0.5`, whenever the value is not a real renewal decision:

| Regime | `keep_prob` |
|---|---|
| Learned keep — neither flag set | `sigmoid(keep_logit).detach()` |
| `native_categorical_edit` | `NaN` — KEEP is a post-hoc label on a skill collision, not a decision |
| `force_refresh_every_check` | `NaN` — always SET |
| `keep_head is None` | `NaN` |

`NaN` propagates through any careless aggregation and shows up as `NaN`, which is
the desired behaviour: a mean renewal probability pooled across a
native-categorical run is a category error, and it should be loud rather than
plausible. Every consumer must therefore aggregate with explicit `NaN` handling
and report the excluded count.

Record the live regime once per run as a scalar alongside the metrics, so a
downstream reader never has to infer it from a config file.

## Verification

- same-seed trajectory equality before and after the change — proves 3, and
  catches 2 if the factorization moved;
- `token_logp` equality on a fixed batch — proves 2 directly;
- a gradient-path assertion that `keep_prob` has no `grad_fn` — proves 1;
- a `NaN` count on a native-categorical run equal to the token count — proves the
  branch semantics fire.

## Out of scope

Metric emission, hazard computation, censoring attribution and the choice of host.
Those wait on the review round. This spec stops at making the quantity exist and
reach both hosts' drain points.

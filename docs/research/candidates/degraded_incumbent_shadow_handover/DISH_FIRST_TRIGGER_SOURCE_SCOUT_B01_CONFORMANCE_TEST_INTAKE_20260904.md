# DISH B01 production conformance C01 — final-suite failure intake

- Direction: `degraded_incumbent_shadow_handover`
- Scientific object: `DISH-FIRST-TRIGGER-SOURCE-SCOUT-B01`
- Engineering attempt: `DISH-B01-PRODUCTION-CONFORMANCE-C01`
- Evidence class and claim ceiling: unchanged **B — EXPLORE** card; this intake has no
  scientific claim
- Frozen science card:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_SCIENCE_CARD_20260904.md`
- Engineering objective:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_CONFORMANCE_OBJECTIVE_20260904.md`
- Result-bearing launches: zero

## Direct observation and classification

After the independent reviewer returned `No material finding` on the repaired implementation,
CM ran the objective's single final focused suite on the then-current bytes. It returned
`3 passed, 1 failed, 1 warning in 9.07s` (wrapper wall `10.702s`). The failing natural TEST prefix
completed 1,100 ticks without reaching a B01 trigger. The smallest relevant existing regression
set separately returned `4 passed, 1 warning in 10.27s` (wrapper wall `11.957s`).

Direct static inspection of the failed bytes located the mismatch in `b01_origin_valid`: the new
predicate required current `readiness_tick`, current `readiness_snapshot`, and both current lineage
locks to equal the stored origin certificate after application arrivals. The accepted legacy
first-application law's reasons 2--12 instead evaluate the stored intent ticks against the current
snapshot; application arrivals legitimately advance current readiness. The old reason 13 alone
depends on the application raw action and is forbidden by the frozen B01 causal cut. The added
current-readiness/lineage equalities therefore reject naturally formed, otherwise valid stored-
origin proposals before the B01 fork.

This is a directly observed engineering-conformance failure over the recorded implementation
bytes. It is not an `FTS-*` observation: no admission receipt, scientific root, seed master, model,
optimizer, checkpoint, 16-row panel, result rule, or scientific summary was created. The B01
object remains unchanged and unconsumed.

## Checks applied

- The failure was compared against the frozen post-arrival/post-assimilation/pre-application-GRU
  cut and the accepted production first-application reasons, not against a TEST-only scientific
  surrogate.
- The independent static review had already closed the prior live/replay, one-shot continuation,
  equal-cost, legacy-observable, receipt/hash, admission, stop-rule, and scope findings.
- The observed failure is upstream of any consequence endpoint or result-rule input, so it carries
  no mechanism polarity.
- The implementation remains confined to the objective's eleven owned paths. No section-4
  machinery or scope-budget deviation is implicated.
- No result-bearing retry is authorized by this intake. Any eventual seed invocation still needs
  conformance acceptance, a committed launch SHA, and its own fresh 4 GiB physical/effective
  admission.

## Decisions this intake produces

### Decision 1 — disposition of the failed final-suite bytes (object tier)

Options:

- **(a)** keep B01 and the causal cut frozen, repair only `b01_origin_valid` so it mirrors accepted
  legacy reasons 2--12 while omitting raw-action reason 13 and the extra current-readiness/lineage
  equalities, then permit one final focused-suite invocation on the new bytes;
- **(b)** stop C01 as a technical failure and leave the still-unconsumed B01 parked before launch;
  or
- **(c)** weaken the causal cut or reinterpret the no-trigger TEST observation as science.

Recommendation: **(a)**. It is a reversible, outcome-blind repair of an implementation predicate,
uses no scientific outcome, and preserves the frozen origin certificate, application timing, and
raw-action independence. Option (b) leaves a localized conformance defect unresolved. Option (c)
changes scientific meaning and is not delegated.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. The original failed bytes remain technical evidence; the repaired bytes are a
new engineering attempt boundary. Exactly one final focused suite is authorized on those repaired
bytes, after independent static re-review. This decision does not authorize `run`, admission, or a
scientific seed.

## Bounded reading and next discriminator

The only supported reading is that the reviewed C01 bytes still did not instantiate the frozen
natural first-application predicate. The strongest support is the direct `3/1` focused-suite
outcome plus the matching predicate trace. The strongest contradiction is that all other focused
categories and the existing regressions passed, localizing rather than generalizing the defect.
The next discriminator is an independent review of the exact predicate repair followed by the one
authorized final suite and non-result `project-cost`; scientific B01 launch remains downstream of
technical acceptance.

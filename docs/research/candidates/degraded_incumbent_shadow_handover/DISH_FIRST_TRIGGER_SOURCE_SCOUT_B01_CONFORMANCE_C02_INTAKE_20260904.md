# DISH B01 production conformance C02 — terminal engineering intake

- Direction: `degraded_incumbent_shadow_handover`
- Scientific object: `DISH-FIRST-TRIGGER-SOURCE-SCOUT-B01`
- Engineering attempt: `DISH-B01-PRODUCTION-CONFORMANCE-C02`
- Evidence class and claim ceiling: unchanged **B — EXPLORE** card; this intake has no
  scientific claim
- Frozen science card:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_SCIENCE_CARD_20260904.md`
- C02 authorization:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_CONFORMANCE_SMOKE_INTAKE_20260904.md`
- Result-bearing launches: zero

## Direct observation and rule application

The C02 test-only change replaced the malformed natural-panel smoke prefix with the existing
native-owned `b01_production_test_fixture(width=1, origin_valid=True)`. Independent static review
returned `No material finding`: the fixture state remained `test_mode=0`, the smoke retained
parent/prepared immutability, three-way cloning, one policy forward and completion per branch,
JSON serialization, the real non-result `project-cost` subprocess, and its 60-second bound. No
production, predicate, runner, science-card, or other-test byte changed in C02.

CM then ran the authorized final-byte existing regressions, which returned
`4 passed, 1 warning in 3.64s` (wrapper wall `5.254s`). The single C02 final focused-suite
invocation returned `3 passed, 1 failed, 1 warning in 4.57s` (wrapper wall `6.332s`). The only
failure occurred at the smoke's first `np.float32` reference because C02 import cleanup had removed
the `numpy` import. Execution did not reach the branch loop or the smoke's `project-cost`
subprocess. CM therefore did not run a separate `project-cost`, stage, commit, push, admit memory,
or invoke any seed.

The C02 prospective rule was applied verbatim: **if its single final suite fails, the chain stops
without another local repair authorization**. The missing import is a directly observed technical
assembly failure. It is not production conformance, an `FTS-*` result, evidence that a normal
panel row does or does not trigger, or a scientific object consumption event. The uncommitted C01/
C02 implementation is not accepted as the price of a result.

## Checks and bounded reading

- Static review closed the substantive live/replay, native cut, equal-cost, receipt, origin-law,
  legacy-behavior, deadline, resource-receipt, and scope findings before C02 execution.
- Dynamic evidence bounds only the executed bytes: four existing regressions and three focused
  categories passed; the smoke stopped on a missing test import before its required path.
- No scientific root, RNG master, model, optimizer, checkpoint, panel endpoint, result summary,
  admission receipt, or detached result process was created.
- No independent cost row was accepted on final bytes because the required command was not run.
- Section-4 additions and scope-budget breaches remain none, but scope compliance cannot replace
  the failed technical acceptance condition.

Claim ceiling remains the frozen B/EXPLORE preliminary panel/budget ceiling. This intake's claim
ceiling is engineering-only: C02 is incomplete and B01 remains unconsumed.

## Decisions this intake produces

### Decision 1 — terminal disposition of the current CM chain (object tier)

Options:

- **(a)** apply the prospective C02 rule, quarantine the uncommitted implementation, stop this CM
  chain, and preserve unchanged B01 before launch;
- **(b)** rewrite the C02 terminal rule after observing its missing-import failure and authorize
  another local smoke invocation; or
- **(c)** accept the static review/three passing categories as conformance or science.

Recommendation: **(a)**. It preserves the prospective engineering boundary and the science/
conformance distinction. Option (b) would rewrite a recorded terminal condition after its outcome;
option (c) ignores a mandatory focused category and cannot support any mechanism claim.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. This is reversible at a future clean object-tier assignment: a fresh,
prospectively specified engineering attempt may correct the import without changing B01. It does
not authorize that attempt here and creates no direction- or Portfolio-tier decision.

## Strongest support, contradiction, and next discriminator

Strongest support for stopping this chain is the direct final-suite failure plus C02's recorded
terminal rule. Strongest contradiction is that the failure is isolated to a missing test import,
while the production-byte static review and all executed non-smoke categories were clean; this
keeps a future fresh conformance attempt plausible but does not make the current bytes acceptable.
The next discriminator is a separately authorized, prospectively frozen fresh engineering attempt
whose final test bytes retain the required import, pass independent review and the complete suite,
emit all three cost rows, and only then reach per-seed 4 GiB admission.

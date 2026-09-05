# DISH B01 production conformance C03 — reviewer portability decision

- Direction: `degraded_incumbent_shadow_handover`
- Scientific object: `DISH-FIRST-TRIGGER-SOURCE-SCOUT-B01`
- Engineering attempt: `DISH-B01-PRODUCTION-CONFORMANCE-C03`
- Evidence class and claim ceiling: unchanged **B — EXPLORE** card; this decision has no
  scientific claim
- Frozen objective:
  `DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_CONFORMANCE_C03_OBJECTIVE_20260904.md`
- Reviewed implementation SHA: `2e54977a62f1bf6b54c883900ab8b36ef55b1d01`
- Decision time: `2026-09-04T10:16:25-07:00`
- Result-bearing launches: zero

## Direct observation and boundary

Before the sole final verification, the independent review and CM inspection found that the new
R06 production loader could compile and load its exact source as a POSIX `.so`, but
`production_backend.artifact_identity()` still called the imported R05 retained-gate identity.
That imported identity compiles and describes a separate MSVC/`.dll` artifact and is not runnable
on WSL. The mandatory archived regression calls the top-level identity, so the reviewed SHA is not
yet portable and has not been accepted.

The loaded R06 artifact is the actual service-bearing artifact on POSIX. No executable historical
POSIX R05 nested descriptor exists to preserve. Windows identity output remains a compatibility
surface and must stay unchanged. This is a descriptor/build-path defect, not a learner, comparator,
RNG, checkpoint, return, trigger-support, or `FTS-*` observation. No test, cost command, admission,
seed, scientific root, learner, checkpoint, or result has run in C03.

## Decision 1 — POSIX nested artifact identity (object tier)

Options:

- **(a)** within the already owned R06 `production_backend.py`, emit on POSIX a truthful nested
  descriptor for the exact loaded R06 service-bearing artifact, while preserving the top-level
  identity keys and digests, all native/RNG behavior, and every Windows output byte;
- **(b)** expand ownership into R05 and port its retained identity/compiler path; or
- **(c)** refuse WSL portability and verify only on the local Windows host.

Recommendation: **(a)**. It describes the artifact that actually supplies the native service,
keeps the scientific runtime unchanged, and preserves the frozen portable/remote-first boundary.
Option (b) expands the C03 path contract and adds unrelated machinery. Option (c) contradicts the
card's prospective portability and cannot make a remote launch ready. The POSIX descriptor must
not impersonate R05 or claim an ABI it does not expose, and the independent reviewer must inspect
the complete repaired diff before the sole WSL suite.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. This is reversible before launch because no result-bearing invocation exists.
It changes no treatment, comparator, arm, budget, card rule, direction lifecycle, or Portfolio
state.

## Bounded reading

This decision authorizes only a pre-suite engineering repair in an owned path. It cannot establish
WSL portability until the exact repaired SHA passes independent review and the single frozen WSL
verification, and it cannot establish source value or any scientific result branch.

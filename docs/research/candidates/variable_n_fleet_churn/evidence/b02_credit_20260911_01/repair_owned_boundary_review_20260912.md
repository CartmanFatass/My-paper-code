# Independent owned-mean boundary review — 2026-09-12

Reviewer: `review_a_h_vnfc_alternative`, Astra/high, read-only, directly under DM.
The first review received the frozen contract and retained evidence without the DM's
implementation discussion. Its recommendation was then checked against the actual diff.
No reviewer edit, numerical fixture, model, environment, RNG master or native execution ran.

## Design and actual-source findings

The whole detached tensor → private Python values → exact-integer mean → owned Torch
output boundary is a credible same-meaning candidate. It removes both the Fraction
constructor and the local Torch/NumPy shared-storage chain. The NumPy model reuses
the same arithmetic. Prior mathematical review of integer ratios remains applicable.
The private helper receives rectangular float lists at both reachable callers;
`zip` cannot truncate a ragged reachable input. Existing finite/nonempty validation,
zero-column output, exact reduction/order invariance, CPU float64 and `g/N` remain.
Actual source and the single retained-input test have **no material review finding**.

The test checks real imported modules on the retained7x64 values,24 copies and256
complete forward/backward applications, plus one preliminary NumPy-wrapper mean.
It checks the retained exact output, shaped gradient and unchanged input. Inspected
repository imports create constants/shape dictionaries/contract data only, with no
scientific model, environment, optimizer, RNG master or native build. No parent
conftest adds such construction. The encoder consumer and checkpoint state-dict
publication retain their inventory/schema; no changed publication/RNG dependency or
Engineering Scope section4 machinery was found.

## Relevant evidence and limit

The earlier allocator failure occurred in this isolated autograd context without
the native environment/model, so one fixed-input allocator-debug check is relevant.
A completed256-application check, normal teardown and actual source/ownership review
could support bounded alternative-path acceptance under Portfolio section6. The old
64-application pass did not cover the failing allocator-debug setup. No old-path rerun,
training reconstruction or uniquely localized writer is required for this narrow claim.

The external receipt must record the configured interpreter, PYTHONMALLOC=debug,
20-second complete-process ceiling, diagnostic stderr, completed counts and normal
exit. A printed count alone precedes teardown. A timeout/abort/incomplete count gives
no pass and cannot be repaired by shortening the check. The test's upstream gradient
is one; unchanged `g/N` supplies the general linear backward argument.

A pass does not prove Fraction or NumPy was the old writer: changed heap layout also
removes a detection opportunity. It does not resolve the expected40/saved32-byte
boundary, certify interpreter safety/all inputs, establish full-pair runtime, supply
scientific primary output or rehabilitate B02. Runtime acceptance is pending the one
check and DM interpretation. No additional fixture is required by this review.

First review: six commands,1.8918168 seconds. Actual-diff review: five commands,
1.6770806 seconds. These are summed command clocks; enclosing tool clocks excluded.

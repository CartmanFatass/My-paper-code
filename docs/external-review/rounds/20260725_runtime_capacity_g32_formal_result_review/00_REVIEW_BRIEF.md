# G32 formal-result scientific disposition brief

```text
semantic_author=project_manager
artifact_scope=reviewer_visible_scientific_boundary
scientific_authority=external_pro
repair_owner=project_manager
review_mode=FORMAL_RESULT_SCIENTIFIC_DISPOSITION
round=20260725_runtime_capacity_g32_formal_result_review
formal_compute_authority=none
```

## Purpose

Formal iteration 24 has a mechanically valid, non-rescuable registered branch:
`USABLE_RUNTIME_CAPACITY_G32`. This round asks External Pro to decide only its
scientific meaning, the smallest retained or retired units, the required
CDC/portfolio/ledger changes and exactly one next scientific action inside the
user-authorized dynamic-roster research goal.

Project Manager owns the code and artifact closure but has no scientific
authority. The PM-observed live tensor-width rebinding gap is a candidate
counterexample, not a selected successor. External Pro may select it, reject it
as engineering-only, choose a different smallest discriminator, or conclude
that this research slice is sufficiently usable and move to another in-scope
scientific boundary.

## Frozen result facts

- source commit: `fbce3609b11353634d1b4acb20cb27372de40bf2`;
- runtime: CPU, torch `2.7.0+cpu`, one thread;
- train/evaluate/analyze: complete with zero exit codes;
- `formal=true`, `operational_valid=true`, `operational_errors=[]`;
- training: capacity 8 only, three fresh replicates;
- evaluation: strict-load the same final checkpoints at capacities 6, 8 and
  12 with zero optimizer steps;
- capacity-8 utility LCB: `0.9502524571532565`;
- capacity-6 utility LCB: `0.9375734680832539`;
- capacity-12 utility LCB: `0.9483212781442009`;
- held-out gain LCB: `0.36581296460255164`;
- minimum held-out replicate: `0.9428362257983847`;
- held-out stochastic mean: `0.875914291159546`;
- exact capacity-8/capacity-12 common-active padding mismatches: all zero;
- registered first-match branch: `USABLE_RUNTIME_CAPACITY_G32`.

The branch cannot be relabelled. It covers the registered fixed-capacity
6/8/12 toy instances and one strict-loadable checkpoint. It does not directly
cover arbitrary capacities, a width change inside one active trajectory, UAV
physics, source-identifiable UAV transport, asynchronous skill lifetime,
intrinsic-reward advantage or comparative superiority.

## Decision needed

External Pro should distinguish three questions rather than merge them:

1. What does G32 add scientifically beyond G31's within-episode active-count
   changes under one preallocated maximum width?
2. Does the registered evidence already constitute a usable test version for
   runtime-variable team membership in the current project sense, and with
   what exact limits?
3. What is the cheapest next evidence object that can still change a scientific
   decision: live in-trajectory width rebinding, a source-identifiable UAV
   transport test, another toy discriminator, stopping this slice, or another
   explicitly justified in-scope action?

The answer must preserve toy-first iteration and may promote to heavy UAV only
with an explicit scientific reason. It does not authorize implementation or
formal compute.

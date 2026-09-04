# DISH phased two-owner oracle and prospective inference hold

Date: `2026-08-31`

Object: `DISH-PROMOTION-SOURCE-FORK-R01`

## Decision-level conclusion

The source-selection question survives, and a bounded TEST-only two-owner phased/pathwise oracle is
now implemented. Production remains stopped before every scientific master, model, checkpoint,
coordinate, or result for a new controlling reason: the frozen 24-block bootstrap max-t law has no
finite-sample coverage guarantee for the declared bounded/discrete block law. This is a prospective
scientific hold, not negative evidence about generic transfer or shadow preparation.

The current code therefore advances reusable conformance only. It does not make the direct runner
READY and does not authorize the 24 STRUCTURED checkpoints or the 6,912-row panel.

## Finite-sample counterexample

For one legal `SHADOW-COPY` mean-service block contrast, let

```text
X =  1/25  with probability 24/25
X = -1     with probability  1/25.
```

Then `E[X] = -1/625 = -0.0016`, but all 24 observed blocks equal `1/25 = 0.04` with probability

```text
(24/25)^24 = 0.375413246727102.
```

On that event `production_inference.py::joint_max_t` marks the column identical, excludes it from
the studentized maximum, and forces the interval to `[0.04,0.04]`. The lower endpoint crosses the
registered mean-service material margin `0.03` although the population mean is negative. Marginal
coverage is therefore at most about `0.624587`; simultaneous 95% coverage is impossible. The same
empirical-support problem applies to an all-zero hard-event column. More bootstrap resamples or a
different zero-SE branch cannot reveal unobserved tail mass.

This is an exact mathematical counterexample plus a direct reading of the implementation. It is
not a claim that any future DISH sample would realize this distribution.

## Estimand and replay factorization corrections

The two support axes must be resolved separately. Failure to identify `COPY-RETAIN` does not erase
an identified `SHADOW-COPY` contrast, and failure to identify `SHADOW-COPY` does not erase generic
transfer. Each axis needs its own `identified`, `value`, `no-material`, `imprecise`, and `harm`
disposition before aggregation. `GENERIC_TRANSFER_ONLY` is valid only when the shadow axis is
identified and no-material; an unidentified shadow axis requires an explicit partial label.

An exact on-time replay can contain only `Delta_shadow`: replay still performs the owner/actuator
transfer. It cannot pre-empt `Delta_transfer`. The result vocabulary must therefore permit combined
statements such as `SHADOW_ABSORBED + GENERIC_TRANSFER_VALUE` or
`SHADOW_ABSORBED + GENERIC_TRANSFER_NO_MATERIAL`.

The future full replay ledger must also bind initial owner and per-tick owner/CAS/promotion history,
unless a prospective proof establishes that no promotion can occur before `t*` and owner history is
uniquely recoverable. Containment must cover every triggered row contributing to an endpoint, not
only separation-support witnesses.

## Direct TEST-only engineering observations

The additive implementation introduces an isolated versioned native sidecar and a separate Python
process seam without modifying the shared R06 backend or REAL/SHAM path:

- `native/dish_promotion_source_fork_r01.cpp` implements nonmutating `begin_tick` and validated
  `clone_prepared` TEST seams;
- `production_source_factored_backend.py` binds the independent ABI and rejects stale, lane-swapped,
  nonfinite, out-of-range, or wrong-recipient recurrent handoffs;
- `production_source_factored_process.py` implements source-specific per-dimension actor, snapshot,
  and critic Welford state plus the bounded two-owner one-tick oracle;
- native 54/58 observations equal an independently reconstructed Python causal oracle over both
  owners and all RETAIN/COPY/SHADOW branches;
- a typed owner-history replay path is independent from the vectorized live path, starts from the
  stored fragment-initial recurrent state, consumes frozen rollout-start Welford state, and matches
  hidden state, logits, old-policy log probability, post-collection Welford state, and exact
  behavior-policy ratio one before optimizer mutation;
- the current `t*` observation is excluded from `W^u`, used for normalization/forward, and only then
  updates `W^{u+1}`.

After independent review corrections—serial rather than batch-merged float64 Welford updates,
complete row-54 common-SOURCE/lineage authority with current/stale/absent coverage, and a truthful
read-only-cache V2 preflight producer that pins its loaded library across a source-key race—an
independent DM run of the complete R06 direction test namespace observed:

```text
48 passed in 5.16s
```

The fresh result-blind TEST preflight receipt is:

`temp/directions/degraded_incumbent_shadow_handover/preflight/wave3-two-owner-oracle-inference-hold-final-20260831/preflight-receipt.json`

It records schema `DISH_PROMOTION_SOURCE_FORK_R01_PREFLIGHT_RECEIPT_V2`, oracle pass over 1,296
actor and 348 critic fields, exact behavior-policy ratio one, zero compiler children, both
scientific holds, `production_mode_reachable=false`, and final `passed=false,status=NOT_READY`. The
requested preflight root contains only that receipt.

These are result-blind TEST facts. They do not prove normal-tick production advance, a real
checkpoint/snapshot bridge, the complete trainer/PPO path, cold/resume checkpoint parity, a full
causal replay with direct deadline timing, no-trigger storage, valid inference, or complete process-
tree resources.

## Claim ceiling and next discriminator

During the hold the only admissible claim is TEST conformance of the bounded phased/pathwise slice.
Even after a future positive result, the ceiling remains fixed-host, finite-budget,
first-trigger-conditional source selection and/or generic transfer under SHADOW-trained checkpoints;
it does not establish unique information, an optimal COPY-trained policy, natural prevalence,
arbitrary `k` or `N`, safety, deployment, or flight.

Before further production investment, Root must choose one prospective target:

1. a fixed realized 24-root panel with exact descriptive margins and no superpopulation confidence
   or promotion-grade VALUE claim; or
2. an explicit block/master superpopulation with independent sampling assumptions, finite bounds
   (including ratio denominator floors), a finite-sample simultaneous-valid method, and a
   precomputed power/resource contract.

For scale only, a Hoeffding bound for one `[-1,1]` mean with half-width `0.03` and 95% confidence
already requires about 8,198 independent roots; this is not a proposed DISH method, but it shows why
24 roots cannot be retained without a different target or stronger justified structure. If no
scientifically valid and affordable design survives, the direction should PARK. Otherwise the
revised inference law, per-axis branch algebra, and oracle must all be frozen before full production
work resumes.

No result-bearing experiment was launched in this wave, so no scientific resource-admission
receipt, master, checkpoint, coordinate, or result was created. The TEST preflight above is not a
scientific experiment and did not invoke a compiler or create a scientific root.

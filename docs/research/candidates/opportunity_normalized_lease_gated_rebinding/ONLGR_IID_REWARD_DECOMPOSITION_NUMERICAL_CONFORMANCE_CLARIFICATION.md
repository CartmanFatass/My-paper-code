# ONLGR IID reward-decomposition numerical conformance clarification

Owner: `direction:opportunity_normalized_lease_gated_rebinding` Explorer Manager
Treatment: `ONLGR-B1-MARKED-LEASE-CENSORED-RATE-v1`
Exact scientific object: `ONLGR-PRO-PREACTIVITY-CORRECTION-20260812-01 + ONLGR-PRO-PREACTIVITY-MATH-DELTA-20260812-02`
Mathematical closure: `ONLGR-PRO-PREACTIVITY-MATH-CLOSURE-20260812-03`
Clarification: `ONLGR-IID-REWARD-DECOMPOSITION-CONFORMANCE-20260812-01`
Classification: `NON_SCIENCE_NUMERICAL_CONFORMANCE_CLARIFICATION`

## Owner decision

`R_IID` is the claim-bearing algebraic quantity computed from the retained
service and explicit-action-cost aggregates:

```text
R_IID[s,a] := S_IID[s,a] - C_IID[s,a].
```

An independently accumulated normalized tick reward is retained as
`R_IID_direct` only to check implementation conformance. It is never the value
used for an IID gate, confidence interval, service/cost decomposition, or
second-surface qualification. Floating-point equality is assessed with the
ordinary named absolute/relative tolerance below, not bit equality and not
`x == y`.

This makes the delta D12 phrase “verify this decomposition exactly” precise:
the mathematical estimand is exactly the declared algebraic decomposition;
the independent float accumulation must agree numerically within an ordinary
tolerance. Display rounding never enters either computation.

No scientific observable, arm, input, schedule, seed, episode, threshold,
resource, treatment identity, interpretation branch, or claim ceiling changes.
This is not a prospective science delta and does not reopen the completed
Principles-to-Critic mathematical review. It is an implementation/analyzer
conformance clarification for CM.

## Canonical episode and aggregate definitions

For every `RAND-IID-4-16-32` seed `s`, learned arm `a`, episode
`n in {0,...,31}`, and `H=256`, retain before display formatting:

```text
S_episode[s,a,n]
  = (1/256) * sum_t service_t

C_episode[s,a,n]
  = (1/256) * sum_t
      (0.02*n_refresh_t + 0.04*n_rebind_t)

R_episode_direct[s,a,n]
  = (1/256) * sum_t r_t

R_episode_recomposed[s,a,n]
  = S_episode[s,a,n] - C_episode[s,a,n].
```

The seed/arm aggregates are:

```text
S_IID[s,a] = (1/32) * sum_n S_episode[s,a,n]
C_IID[s,a] = (1/32) * sum_n C_episode[s,a,n]
R_IID[s,a] = S_IID[s,a] - C_IID[s,a]              # claim-bearing

R_IID_direct[s,a]
  = (1/32) * sum_n R_episode_direct[s,a,n]         # diagnostic only.
```

All scientific IID contrasts, paired seed effects, intervals, gates, and the
`R_IID=S_IID-C_IID` result field use `R_IID`, never `R_IID_direct`.
The direct value tests the tick-reward ledger and accumulator; it supplies no
additional scientific vote.

## Ordinary numerical tolerance

Freeze:

```text
decomposition_atol = 1e-12
decomposition_rtol = 1e-10

tol(x,y) = decomposition_atol
           + decomposition_rtol * max(abs(x),abs(y))

isclose_decomposition(x,y)
  = abs(x-y) <= tol(x,y).
```

Apply this once per episode to
`R_episode_direct` versus `R_episode_recomposed` and once per seed/arm to
`R_IID_direct` versus `R_IID`. The comparison includes equality at the
tolerance boundary. No bit pattern, summation order, hash, serialized text,
or exact float equality is prescribed. CM may use a numerically stable float64
accumulator; the method is reported as an implementation fact rather than a
scientific gate.

Conformance requires every episode comparison and every seed/arm aggregate
comparison to pass. A failure is an analyzer/reward-ledger implementation
mismatch. It is not a negative, null, or reverse ONLGR result and cannot be
repaired by changing a scientific threshold. Until unchanged-science repair,
IID return, service/cost interpretation, content-access language, second-
surface activation, and complete-coherent-package status are unavailable.
An otherwise coherent native `P/W` contrast retains only its already frozen
bounded native interpretation.

## Exact analyzer/result fields

The future result packet exposes these exact fields.

### Panel-level metadata

```text
iid_decomposition_definition = "R_IID := S_IID - C_IID"
iid_decomposition_atol = 1e-12
iid_decomposition_rtol = 1e-10
iid_accumulation_dtype = "float64"
iid_accumulation_method = <reported implementation fact>
```

### Per episode, keyed by `(seed,arm,episode_index)`

```text
iid_service_episode
iid_action_cost_episode
iid_return_episode_direct
iid_return_episode_recomposed
iid_return_episode_residual
iid_return_episode_tolerance
iid_return_episode_decomposition_ok
```

with

```text
iid_return_episode_residual
  = iid_return_episode_direct - iid_return_episode_recomposed

iid_return_episode_tolerance
  = tol(iid_return_episode_direct,iid_return_episode_recomposed).
```

### Per seed/arm

```text
S_IID
C_IID
R_IID
R_IID_direct
R_IID_direct_residual
R_IID_direct_tolerance
R_IID_direct_decomposition_ok
iid_episode_decomposition_fail_count
iid_max_abs_episode_decomposition_residual
iid_worst_episode_decomposition_index
iid_seed_arm_decomposition_ok
```

with

```text
R_IID = S_IID-C_IID
R_IID_direct_residual = R_IID_direct-R_IID
iid_seed_arm_decomposition_ok
  = R_IID_direct_decomposition_ok
    AND (iid_episode_decomposition_fail_count==0).
```

### Package summary

```text
iid_reward_decomposition_conformant
  = AND over every learned seed/arm iid_seed_arm_decomposition_ok.
```

The result analyzer must report all residuals and failure locations; it must
not silently substitute `R_IID_direct` for the canonical value or discard a
failing episode.

## Optional-panel completeness confirmation

The result-blind intake map's completeness semantics remain unchanged:

- missing yoke output is non-gating for the core complete coherent package and
  the Pro trigger; it removes only `Psi`;
- missing exposure-clamp output is non-gating for the core package and Pro
  trigger; it removes only the clamp interpretation;
- missing degenerate/oracle output is non-gating for the core package and Pro
  trigger; it removes the corresponding finer control interpretation; and
- because the continuous two-UAV activation conjunction explicitly requires
  `H_oracle>=0.02`, missing oracle or any input needed to compute that frozen
  comparison makes second-surface qualification unavailable. It does not make
  the core package incomplete.

The fixed-rate diagnostic is a core complete-package item and is not included
in the optional degenerate/oracle exception. A scientific support failure from
an executed yoke remains an outcome; an unexecuted optional row is simply
reported missing and cannot be imputed.

## Exact Root-to-CM relay

```text
ONLGR_IID_REWARD_DECOMPOSITION_CONFORMANCE_CLARIFICATION
direction=opportunity_normalized_lease_gated_rebinding
treatment=ONLGR-B1-MARKED-LEASE-CENSORED-RATE-v1
exact_scientific_object=ONLGR-PRO-PREACTIVITY-CORRECTION-20260812-01+ONLGR-PRO-PREACTIVITY-MATH-DELTA-20260812-02
math_closure=ONLGR-PRO-PREACTIVITY-MATH-CLOSURE-20260812-03
clarification=ONLGR-IID-REWARD-DECOMPOSITION-CONFORMANCE-20260812-01
classification=NON_SCIENCE_NUMERICAL_CONFORMANCE_CLARIFICATION
science_delta_required=false
revision_bound_rereview_required=false
treatment_changed=false

Define claim-bearing R_IID algebraically from retained S_IID and C_IID:
R_IID := S_IID-C_IID. Retain the independently accumulated tick-reward value
as diagnostic-only R_IID_direct. Never use R_IID_direct for a scientific gate,
confidence interval, content/service interpretation, or activation decision.

Check direct versus recomposed values per episode and per seed/arm using
abs(x-y) <= 1e-12 + 1e-10*max(abs(x),abs(y)), including equality. Report the
exact fields frozen in
docs/research/candidates/opportunity_normalized_lease_gated_rebinding/ONLGR_IID_REWARD_DECOMPOSITION_NUMERICAL_CONFORMANCE_CLARIFICATION.md.
No bit equality, fixed summation order, hash, or serialized-text identity is a
gate.

All episode and aggregate checks must pass for IID decomposition conformance.
A failure is unchanged-science analyzer/reward-ledger work for CM, not an
empirical ONLGR outcome. Until repaired, IID return and service/cost claims,
content-access wording, second-surface activation, and complete-coherent-package
status are unavailable; a complete coherent native P/W result retains only its
registered bounded native interpretation.

Yoke, exposure-clamp, and degenerate/oracle absence remains non-gating for the
core complete coherent package and same-conversation Pro trigger. Missing yoke
removes Psi; missing clamp removes its diagnostic; missing degenerate/oracle
removes their finer interpretations. Missing oracle makes H_oracle and hence
second-surface qualification unavailable. FIXED-RATE remains a core item.

No runtime/result was inspected and no production authority is conveyed.
```

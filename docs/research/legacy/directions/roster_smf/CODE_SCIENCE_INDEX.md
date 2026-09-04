# ROSTER-SMF access/resource certificate

## Narrow technical conclusion

For the one explicitly registered production DTO feature
`critic_member_features[0]`, the current `BoundarySnapshot` member interface
provides every protected and bulk row under one physical-time/membership-epoch
token.  The proof-sized bound fixture therefore resolves to `FULL_ACCESS`, its
fixed-order float32 census is exact, and the candidate terminates as
`CENSUS_CONFORMANT_PRODUCTION_HT_RETIRED`.

This is deliberately narrow.  It does not claim that every present or future
roster feature is fully accessible.  It does not claim unbiasedness after
clipping, normalization, ratios, layer norm, policy kernels, or another
nonlinear transform.  It runs no environment step, rollout, training, tuning,
learned-return computation, or production integration.

## Bound production interface

- DTOs: `ha_ctse_process.variable_roster_event_types.BoundarySnapshot` and
  `BoundaryMember`.
- Registered value: the scalar float32 row component
  `critic_member_features[0]`.
- Current interface fact: `variable_roster_event.pack_active` stacks every
  snapshot member's `critic_member_features` row.  This candidate consumes the
  DTO directly and does not modify or wrap that production path.
- Snapshot token: physical time `41` with lifecycle/epoch rows
  `protected/7`, `bulk-1/11`, `bulk-2/13`, `bulk-3/17`.
- Membership: one protected row and exactly three disjoint bulk rows.
- Gradient contract: the boundary values are NumPy float32 snapshot inputs and
  are bound as a detached immutable Fraction projection.  The arithmetic
  emulator uses protected-then-snapshot-bulk float32 reduction order.

The actual full-access trace is exactly:

```text
protected:protected_exact
bulk-1:bulk_exact
bulk-2:bulk_exact
bulk-3:bulk_exact
```

All events carry the same token and each row is read once.  The immutable
componentwise resources are `R_max=(4,3,4)`, `R_all=(4,3,4)`, and
`R_selected=(3,2,3)` in `(row_reads, accumulator_ops, resident_rows)` order.
The cheap-G0 pair sampler dependency is registered with the immutable semantic
commitment `finite-pair-table/N3-m2/precommitted@1`, but remains inactive and
retired in the bound full-access branch.

## Exact counterfactual HT checks

The retained HT code is evidence for the counterfactual
`SAMPLING_NEEDED` branch only; it is not kept in the bound production branch.
Every finite design uses exact `Fraction` first- and second-order inclusion
probabilities and independently compares direct design variance with the
inclusion-covariance formula.

| Fixture | Exact expectation | Exact variance | Additional discriminator |
|---|---:|---:|---|
| uniform pairs, `y=(1,2,4)` | `7` | `7/2` | sample totals `9/2,15/2,9` |
| uniform pairs, `y=(1,-1,0)` | `0` | `3/2` | sample totals `0,3/2,-3/2` |
| unequal `p12=1/2,p13=1/3,p23=1/6`, `y=(1,2,4)` | `7` | `41/5` | common-weight expectation `25/4`; raw expectation `25/6` |
| protected exact value `10` plus uniform positive bulk | `17` | `7/2` | protected row is outside the sample frame |

For the unequal design, `pi=(5/6,2/3,1/2)` and pairwise inclusion is exactly
`(1/2,1/3,1/6)`.  Thus correct member-specific weights are mechanically
separated from both one common weight and raw unweighted pair totals.

## Claim-to-code map

- `experiments/candidates/roster_smf/access_resource_certificate.py`
  - real DTO binding, immutable token/projection, access-regime fork,
    componentwise resources, trace sentinel, fixed-order float32 census,
    finite-design HT expectation and two independent variance calculations;
  - canonical deterministic JSON entry point.
- `tests/experiments/candidates/roster_smf/test_access_resource_certificate.py`
  - constructs the real DTO and exercises the bound full-access result;
  - exhausts all 64 access-fork Boolean assignments;
  - proves the three finite designs and protected exclusion;
  - rejects mixed/mutated snapshots, invalid inclusion probabilities, wrong
    sample frames, duplicate/missing membership, unsampled expensive access,
    resource failure, dtype/order/gradient drift, and nonlinear unbiased labels.
  - enforces the 500-active-line ceiling and scans all Python files under
    `ha_ctse_process`, `envs`, and `scripts` for forbidden reverse imports.

## Executed evidence

Registered interpreter:
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.

Focused command:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q -p no:cacheprovider tests/experiments/candidates/roster_smf/test_access_resource_certificate.py
```

Raw result:

```text
..................                                                       [100%]
19 passed in 1.87s
```

Candidate entry command, executed twice for byte stability:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m experiments.candidates.roster_smf.access_resource_certificate
```

Raw canonical candidate output:

```json
{"access_trace":[{"key":"protected","kind":"protected_exact"},{"key":"bulk-1","kind":"bulk_exact"},{"key":"bulk-2","kind":"bulk_exact"},{"key":"bulk-3","kind":"bulk_exact"}],"actual_binding":"BOUND_VARIABLE_ROSTER_SNAPSHOT_FULL_ACCESS","census_total":"17","feature":"critic_member_features[0]","fixtures":{"protected_exact":{"expectation":"17","variance":"7/2"},"unequal":{"common_weight_expectation":"25/4","expectation":"7","raw_expectation":"25/6","variance":"41/5"},"uniform_positive":{"expectation":"7","variance":"7/2"},"uniform_signed":{"expectation":"0","variance":"3/2"}},"float32_census":17.0,"gradient_mode":"detached_boundary_numpy","regime":"FULL_ACCESS","resources":{"R_all":{"accumulator_ops":3,"resident_rows":4,"row_reads":4},"R_max":{"accumulator_ops":3,"resident_rows":4,"row_reads":4},"R_selected":{"accumulator_ops":2,"resident_rows":3,"row_reads":3}},"sampler_dependency":{"active":false,"commitment":"finite-pair-table/N3-m2/precommitted@1","name":"cheap_g0_pair_sampler","present":true,"reason":"retired_on_full_access"},"snapshot_token":{"membership":[["protected",7],["bulk-1",11],["bulk-2",13],["bulk-3",17]],"physical_time":41},"terminal":"CENSUS_CONFORMANT_PRODUCTION_HT_RETIRED"}
```

The double-run comparison printed `BYTE_STABLE=True`.

Canonical key output:

```text
actual_binding=BOUND_VARIABLE_ROSTER_SNAPSHOT_FULL_ACCESS
regime=FULL_ACCESS
census_total=17
float32_census=17.0
terminal=CENSUS_CONFORMANT_PRODUCTION_HT_RETIRED
uniform_positive=(E=7,Var=7/2)
uniform_signed=(E=0,Var=3/2)
unequal=(E=7,Var=41/5,common=25/4,raw=25/6)
protected_exact=(E=17,Var=7/2)
```

Both entry invocations emitted identical canonical UTF-8 JSON bytes.  The
source has 479 active nonblank/non-comment lines, below the 500-line isolated
candidate limit.  The fixed proof has `H=0`, no hypothetical transitions, and
only three registered pair outcomes, so it is constant-size finite algebra and
finishes far below the nonformal wall-clock cap.

Post-pass inspection found one local trace-oracle defect: it compared token and
key order but not the access-kind label.  The oracle now requires
`bulk_exact` for census reads and `bulk_sampled` for counterfactual sampled
reads.  Focused tests corrupt each direction (`exact -> sampled` and
`sampled -> exact`) and prove fail-closed behavior.  The final rerun above
passed.

## Directory, readiness, and deletion boundary

The implementation lives under `experiments/candidates/roster_smf/`, its test
mirrors that path under `tests/experiments/candidates/`, and this public
science-to-code map lives under `docs/research/candidates/`.  Production code
does not import the candidate.

Execution readiness is not triggered: this is an isolated proof-sized
candidate with no production entry, runner phase, artifact lifecycle,
serialization, checkpoint, or shared runtime change.  If the direction is
parked, retired, or replaced, delete this source, its mirrored test, and this
index together.  Git is the archive; no compatibility wrapper or historical
code directory is retained.

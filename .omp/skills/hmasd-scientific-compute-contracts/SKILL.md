---
name: hmasd-scientific-compute-contracts
description: On-demand bounded property search and explicit numerical artifact comparison.
---

# HMASD Scientific Compute Contracts

## Purpose and activation

Use this Skill only when an EM-owned evidence gap or a frozen CM verification
contract specifically requires property-based falsification or numerical
artifact comparison. It is not manager-autoloaded and does not change the
project's default Python environment, numerical algorithms, RNG objects,
checkpoint formats, or bit-identity rules. Activate only the reviewed optional
research-tools environment; a missing Hypothesis, NumPy, or SciPy dependency
fails closed rather than selecting another implementation.

These helpers are original local wrappers informed by the public Hypothesis,
NumPy, and SciPy APIs. They do not copy or substantially adapt upstream source.
The dependency gate is authoritative for exact versions and licenses. The
reviewed API surface is Hypothesis `settings`, `seed`, `find`, `Phase`,
`HealthCheck`, and `SearchStrategy`; NumPy dtype/shape/layout predicates,
`isfinite`, `isnan`, `isinf`, `signbit`, array bytes, and `.npy` loading; and
SciPy `linalg.norm`. Property testing is bounded falsification, not proof, and a
numerical comparator is an oracle implementation, not a scientific verdict.

Primary documentation:

- Hypothesis: <https://hypothesis.readthedocs.io/en/latest/>;
- NumPy testing and array semantics:
  <https://numpy.org/doc/stable/reference/testing.html>; and
- SciPy: <https://docs.scipy.org/doc/scipy/reference/>.

## Frozen property-test contract

Before using `PropertyTestContract`, record all of the following without
shrinking the domain or resource limit for convenience:

- property ID and exact predicate in words and code/artifact reference;
- generator domain, representation boundaries, filters, and every explicit
  example;
- fixed non-negative seed and named local profile;
- `max_examples`, deadline (`None` is explicit), enabled phases, suppressed
  health checks, and multiple-bug setting;
- Hypothesis version, relevant application/library versions, and the exact
  strategy implementation;
- retained minimal counterexample, or the documented bounded search with no
  counterexample; and
- Hypothesis reproduce-failure version/blob when Hypothesis supplies one.

`with_hypothesis_contract` applies the frozen explicit examples, settings, and
seed to an already `@given` property. `find_counterexample` searches one strategy
with Hypothesis generation and shrinking, a local `random.Random(seed)`, and no
example database. Hypothesis `find` internally suppresses all health checks,
does not run recorded `@example` inputs, and searches for one witness; the
helper records those effective settings and rejects `report_multiple_bugs=True`
rather than hiding the override. Its metadata records the domain, profile, seed,
dependency version, minimal witness, and replay limitations. A seed replays
only with the frozen strategy, settings, and dependency version. A
reproduce-failure blob is stronger version-bound replay evidence; neither
establishes cross-version identity.

Filters must remain visible. Excessive filtering, a health-check suppression,
a changed phase, a lower `max_examples`, or a tighter generator range is a new
contract, not local recovery. A completed run means only that Hypothesis found
and shrank the recorded witness or found no witness within that exact run.

## Frozen numerical contract

Construct `ArrayContract` and `ComparisonContract` before reading the result.
The contract requires:

- dtype including byte order, exact shape, CPU device, C or Fortran layout,
  units, NaN policy, infinity policy, and signed-zero policy;
- exact algorithm and version plus the declared reference oracle;
- for approximate mode, finite non-negative `atol` and `rtol`, a non-empty
  domain justification, and the visible asymmetric formula
  `abs(actual - expected) <= atol + rtol * abs(expected)`;
- ordering, conditioning/convergence and warning handling, statistical
  assumptions when relevant, and the producing NumPy/SciPy versions in the
  surrounding run artifact; and
- the exact RNG class/object, seed or state, draw order, and state hashes when
  the producer is stochastic. These comparison helpers never create or reseed
  a global RNG.

Policies are deliberate:

- `nan_policy=forbid` rejects any NaN; `equal` accepts only paired NaN
  positions; `unequal` permits their presence in the array contract but never
  treats them as equal.
- `inf_policy=forbid` rejects any infinity; `equal` accepts only paired
  same-sign infinite values; `unequal` never treats an infinity as equal.
- approximate mode may set signed-zero policy to `equal` or `distinguish`.
  Exact mode requires `distinguish`.

`exact` and `approximate` are disjoint modes. Exact mode rejects tolerances and
compares documented canonical bytes consisting of dtype, shape, declared
layout, and uncoerced array bytes; it also reports SHA-256. It refuses
noncontiguous layout rather than silently copying or normalizing it. Therefore
NaN payloads, byte order, and signed zero remain identity-bearing. A SHA-256 is
reported evidence, while the equality decision itself compares bytes.

Approximate mode requires a tolerance contract and never reports approximate
agreement as exact identity. Dtype, shape, layout, NaN, infinity, and
signed-zero checks remain separate from the tolerance check. Do not use a
passing tolerance check to excuse a failed structural or special-value policy.
Warnings, nonconvergence, ill-conditioning, nondeterminism, and upstream
algorithm changes remain explicit producer failures or limitations; the
comparator does not suppress them.

## Invariant helpers

Use the narrow assertion helpers inside Hypothesis properties or independent
checks:

- `assert_array_contract` for dtype, shape, layout, and special-value policy;
- `assert_all_finite`, `assert_bounded`, and `assert_monotonic` for direct
  mathematical invariants;
- `assert_normalized` with an explicit `ToleranceContract`; and
- `assert_linear_solution_residual` for the declared SciPy norm oracle and the
  explicit residual bound `||A x - b|| <= atol + rtol ||b||`.

An invariant failure is a counterexample to the coded property under its frozen
representation. It is not automatically a counterexample to the scientific
claim; EM evaluates applicability, assumptions, falsifier, uncertainty,
consequence, and recommendation independently.

## Artifact comparison CLI

Run the module only against recorded single-array `.npy` artifacts:

```text
python -m tools.research.scientific_compute compare \
  --expected expected.npy --actual actual.npy \
  --mode approximate --dtype '<f8' --shape 20,4 --order C \
  --nan-policy forbid --inf-policy forbid --signed-zero-policy distinguish \
  --units dimensionless --device cpu --oracle frozen-reference-v3 \
  --algorithm scipy-solve --algorithm-version 1.15.2 \
  --atol 1e-12 --rtol 1e-10 \
  --tolerance-justification 'forward-error bound from the frozen condition estimate'
```

Use `--shape scalar` for a zero-dimensional array. Exact mode requires the same
structural and policy arguments, requires signed-zero `distinguish`, and rejects
all tolerance arguments. The loader sets `allow_pickle=False` and rejects `.npz`
archives because implicit array selection would be an unrecorded normalization.

Output is deterministic JSON with `schema_version: 1`, stable tool/status/ok
fields, the entire visible contract, ordered checks, canonical hashes when
available, artifact paths, and NumPy/SciPy versions. There are no timestamps or
implicit defaults for scientific fields. Exit `0` means every declared check
passed, `2` means a mismatch or invalid contract, and `3` means an artifact
could not be read. Technical success does not set scientific status.

## Return and authority boundary

Retain the JSON result and property replay metadata as technical evidence. The
requesting analytical product still supplies assignment/gap ID, task family,
claim, exact evidence locators, assumptions, falsifier or counterexample,
uncertainty/limitations, consequence/decision relevance, and recommendation.
A bounded negative result may support `NO_MATERIAL_INSIGHT` only when its
sources inspected, methods attempted, reason, and residual uncertainty are
complete. This Skill, a passing property run, a hash match, SciPy, NumPy, or
Hypothesis never approves code, proves a theorem, accepts a scientific claim,
or changes an EM disposition.

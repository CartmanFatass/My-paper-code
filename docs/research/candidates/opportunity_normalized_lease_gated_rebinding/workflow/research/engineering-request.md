# ONLGR held-out `Delta_H=2` exact-assay engineering request

- Request ID: `ONLGR-G4-DELTA2-EXACT-ASSAY-R01`
- Direction: `opportunity_normalized_lease_gated_rebinding`
- Scientific owner: `EM-opportunity_normalized_lease_gated_rebinding`
- Source assignment: `onlgr-heldout-delta2-g4-r1`, generation 4
- Cycle: `2026-08-30-portfolio-r19-onlgr-heldout-transfer-01`
- Status: `PREPARED_NOT_AUTHORIZED`
- Evidence burden: conclusion-bearing deterministic exact assay
- Technical execution status: `NOT_STARTED`
- Result observation status: `NOT_OBSERVED`

## Authority and dependency boundary

This request is inert semantic content. It authorizes no implementation, test,
command, provider operation, state mutation, Git operation, lifecycle action, or
external Effect.

Exact scientific inputs are:

- assignment base
  `72f1b4fbbb588d51943c4155814031b6ed56e20f`;
- accepted prior g4 integrated checkpoint
  `d0f1dca00421620b64ffb36eaae06272ea6597f1`;
- immutable original held-out scope
  `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/evidence/2026-08-30-2026-08-30-portfolio-r19-onlgr-heldout-transfer-01-scope-and-grounding.md`,
  SHA-256
  `c2831053ecd59d37fbe434f88d93dad8beaf0ae6c58eef5153b2efece27ffdd4`;
- prospective geometry-readiness amendment and total decision function
  `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/evidence/2026-08-30-2026-08-30-portfolio-r19-onlgr-heldout-transfer-01-geometry-readiness-g4.md`,
  SHA-256
  `ae53a9038e534c5b8b3b3238378a8eaad95981fa594d059987756455f3866c6a`;
- principles SHA-256
  `9c72a38cb511954c5974569d7ccb4237588a15636c72170e5320de8eceaabc4d`;
- Portfolio SHA-256
  `ae07ea07dc7782c19cd537029db8dfe74f65bd0fe44753386d27d9bba7a823f7`;
- question SHA-256
  `2cb6cb88afda93bd778ad253f85a2b19f29bf4e9468667a4c56055c57fbd6f01`;
- evidence-set SHA-256
  `a456a131a3f1def6712909f7226f9748418d41737fa54fbe74464d8e94ad47be`.

A future same-direction CM dispatch requires a new Root assignment and a strict
dependency on the exact accepted EM `integrated_sha` for these bytes. Before CM
starts, the fresh cycle's neutral Pro Innovator must have a terminal EM
disposition, or the user must have exactly waived that still-unsent stage. If
that disposition changes any object, predicate, comparator, claim ceiling,
interface, oracle, command, or input identity, this request is superseded and
must not be implemented. Request presence is never dispatch authority.

## Scientific question and decision relevance

After fitting only spacings one and four, does the unchanged one-parameter RATE
or EXP form make an operationally useful exact prediction at the one
prospectively held-out spacing `Delta_H=2`, relative to unretuned RAW, the
held-out unrestricted-`Q` state-blind-memoryless ceiling, KEEP, and each
candidate's payload-null shell?

The result can distinguish one-cell operational form performance from a finite
two-spacing fit. It cannot identify physical-rate or exponential semantics:
`FINITE-AFFINE` reproduces RATE's spacing-two prediction and finite
log-survival interpolation reproduces EXP's. The current accepted result remains
`GENERIC_RATE_SUPPORTED`, not `EXP_LINK_SPECIFIC`, until a later valid EM
interpretation says otherwise.

## Frozen object and estimands

Preserve exactly:

- one regenerative unit;
- service lifetime `L=7`;
- renewal cost `c=2`;
- service for an interval before the action at its ending opportunity boundary;
- early renewal discards residual service and does not stack service;
- infinite-horizon physical-time average, with no episode boundary, censoring,
  discount, stochastic estimate, learned state, optimizer, or checkpoint;
- fitting roster `Delta in {1,4}` at equal physical-time weight;
- only held-out spacing `Delta_H=2`, never pooled into fitting;
- grid `Q={0/16,1/16,...,16/16}`;
- locked RAW prediction `q=1/4`;
- locked, unprojected EXP prediction `q=7/16`;
- locked, uncapped-at-this-cell RATE prediction `q=3/8`;
- exact registered return operator
  `J_Delta(q)=q*E[min(Delta*K,7)]/Delta-2q/Delta`, with geometric
  `K` on `{1,2,...}` and explicit `J_Delta(0)=0`;
- exact material margin `M=1/32` per physical tick;
- lower executed physical activity, then lower grid index, for an unrestricted
  grid tie; and
- no cross-family tie breaker beyond the exact decision function.

The primary estimand is `D=E-R`, where `E` and `R` are the held-out direct
returns of the locked EXP and RATE predictions. Required companion metrics are
`W` for locked RAW; `C=max_{q in Q} J_2(q)`; `C-E` and `C-R`; `E-W` and `R-W`;
KEEP and matched-shell headroom for both candidates; service and charge
components; every unrestricted row and oracle tie witness; and the separately
reported first-legal-boundary age-conditioned competence diagnostic.

All deployed families receive the same spacing, opportunity flag, physical
slots, age/exposure information, action shell, cost, reset, and observation
class. The unrestricted policy is a diagnostic ceiling, not a deployed or
transfer family. The age-conditioned policy is an out-of-family competence
diagnostic, not a memoryless ceiling or link comparator.

## Protected semantics and explicit non-goals

Scientific and numerical semantics that may not change are lifetime, cost,
service-before-action order, regenerative averaging, physical-time exposure,
equal fit weights, base grid, locked coordinates, unprojected EXP transform,
RATE cap definition, state-blind memorylessness, shell definition, oracle and
fit tie rules, exact rational arithmetic, the `1/32` margin, branch priority,
and the distinction between validity, technical status, and scientific branch.

RNG/seed identity is `NONE`. Data identity is `NONE`. Checkpoint identity is
`NONE`. No floating-point value may control a fit, optimum, tie, margin,
predicate, or branch. No network or external access is permitted.

Non-goals are refitting or learning any coordinate; scanning, substituting, or
averaging a held-out spacing; changing the grid, host, lifetime, cost, order,
weight, shell, margin, or tie; using the prior provider response or quarantined
B3 package; evaluating task content, causal lease, `REBIND`, population change,
UAV transfer, safety, deployment, workload, or PPO; claiming arbitrary-spacing,
continuous-time, common-rate, or exponential semantics; and making a Portfolio
or lifecycle decision.

## Implementation contract

A future CM may create only these source/test paths unless a new EM request
changes the interface before CM starts:

- `experiments/candidates/opportunity_normalized_lease_gated_rebinding/heldout_delta2/__init__.py`;
- `experiments/candidates/opportunity_normalized_lease_gated_rebinding/heldout_delta2/contracts.py`;
- `experiments/candidates/opportunity_normalized_lease_gated_rebinding/heldout_delta2/evaluator.py`;
- `experiments/candidates/opportunity_normalized_lease_gated_rebinding/heldout_delta2/run.py`;
- `experiments/candidates/opportunity_normalized_lease_gated_rebinding/heldout_delta2/__main__.py`; and
- `tests/experiments/candidates/opportunity_normalized_lease_gated_rebinding/test_heldout_delta2.py`.

Do not edit or import the legacy B2/B3 hosts as scientific oracles. Current B2
mutates renewal state before same-tick service, while this object requires
service before the ending-boundary action. The new package is a small pure exact
rational evaluator, not a simulator, learner, host repair, or compatibility
shim.

Use canonical reduced rational pairs `[numerator,denominator]` with positive
denominators. Use no binary floating point in the scientific path. The package
must independently derive the finite geometric expectation for each requested
`q`, then derive service, charge, and direct return from the frozen operator. It
must evaluate all 17 `Q` rows exactly once in deterministic grid order. RAW,
EXP, and RATE values must be references to the identical matching rows in that
table; a second candidate-specific calculation is forbidden.

The contract-check path must verify the exact scope and readiness file bytes,
all constants, candidate membership in `Q`, required output fields, branch
predicate definitions, and destination confinement without invoking the
held-out evaluator. Source identity and the future accepted CM integrated SHA
are recorded by the owning CM/Experiment Operator facts; the evaluator does not
infer Git acceptance.

## Terminal result artifact

The only claim-bearing output path is

`temp/directions/opportunity_normalized_lease_gated_rebinding/exp/heldout_delta2_g4_r1/ONLGR_HELDOUT_DELTA2_G4_RESULT.json`.

Write canonical UTF-8 compact sorted JSON with one final LF by an atomic
write-once replacement. Refuse a pre-existing terminal file or stale temporary
file; never overwrite or append. Print no candidate return, optimum, metric,
predicate, branch, or partial result before the terminal file is sealed.

The terminal payload must include at least:

- schema `hmasd.onlgr-heldout-delta2-exact-result/v1` and request ID;
- exact scope/readiness/request paths and observed SHA-256s;
- exact command arguments and source/module SHA-256s;
- the complete frozen constants, clock, ordering, fit and held-out rosters,
  candidate coordinates, margin, ties, and non-goals;
- all 17 grid rows, each with canonical `q`, geometric expectation, service,
  charge, and direct return rational pairs;
- locked RAW/EXP/RATE row indices and identity-equality witnesses against the
  corresponding unrestricted rows;
- all maximizing grid rows, the selected oracle row, and complete tie witness;
- KEEP, `N_EXP`, `N_RATE`, candidate service/charge decompositions, candidate
  KEEP/shell headrooms, `E`, `R`, `W`, `C`, both regrets, both RAW increments,
  `D`, and `abs(D)<=M` as a separately derived link-form-null predicate;
- the first-legal-boundary age-conditioned diagnostic under the same cost and
  ordering, marked out of family and excluded from branch selection;
- named Boolean values `DC_EXP`, `DC_RATE`, `TC_EXP`, `TC_RATE`, `I_EXP`, and
  `I_RATE`;
- a sequential branch trace showing every evaluated clause and the first return;
- `validity_status`, `technical_status`, exact scientific branch, umbrella
  decision class where applicable, and `scientific_update_permitted`; and
- an explicit limitations block retaining `FINITE-AFFINE`, finite log-survival,
  other equal-information finite mappings, and the finite claim ceiling.

A complete valid packet must also assert and independently verify `C>=E`,
`C>=R`, and `C>=W`; exact decomposition identities; unique row identity; all
predicate arithmetic; and branch/output consistency. Any contradiction is
`INVALID`, not a scientific outcome.

## Total decision function

For `F` in `{EXP,RATE}` use exactly:

- `DC_F := (J_F-KEEP>M) and (J_F-N_F>M)`;
- `TC_F := DC_F and (C-J_F<=M)`;
- `I_F := J_F-W>M`;
- `D := E-R`.

Apply in order:

1. `INVALID` on any changed identity, leakage, missing/inconsistent field,
   changed protected semantic, non-exact arithmetic, or failed invariant;
2. `TECHNICAL_FAILURE` when a valid input cannot produce a sealed complete
   artifact;
3. `NO_DIRECT_HEADROOM` when `not (DC_EXP and DC_RATE)`;
4. `RAW_NOT_MATERIALLY_WORSE` when
   `DC_EXP and DC_RATE and not I_EXP and not I_RATE`;
5. `BOTH_MAPPINGS_MISS` when `C-E>M and C-R>M`;
6. `EXP_FORM_TRANSFER` when `TC_EXP and I_EXP and D>M`;
7. `RATE_FORM_TRANSFER` when `TC_RATE and I_RATE and D<=M`;
8. `AMBIGUOUS_VALID_OBSERVATION` otherwise.

Branches 3-5 map to `NO_IDENTIFIED_FORM_TRANSFER` while preserving their exact
labels and tuple. Equality to `M` is no-material. `RATE_FORM_TRANSFER` may
include a material RATE win or an EXP advantage no larger than `M`; only
`abs(D)<=M` is additionally a link-form null. Invalidity and technical failure
keep the scientific branch null and make no claim update.

## Focused technical verification

Future CM verification must be non-result-bearing. It must not invoke the
registered result command, write the terminal result path, or expose the frozen
held-out tuple. Use alternate synthetic host constants and symbolic metric
packets for evaluator and branch tests.

Required focused coverage is:

- exact geometric expectation and service/charge identities on alternate
  fixtures, including `q=0` and `q=1`;
- canonical reduced-rational serialization and rejection of float/noncanonical
  input;
- 17-row ordering, candidate-row identity, maximum/tie selection, and exact
  equality boundaries;
- KEEP, shell, and age-conditioned control definitions;
- every ordered scientific branch plus invalid and technical statuses using
  synthetic packets;
- the accepted adversarial witness from the readiness artifact, which must
  return `RAW_NOT_MATERIALLY_WORSE`;
- catch-all totality and first-matching-clause precedence;
- changed scope/readiness hash, retuning, wrong spacing/grid/order/margin, and
  incomplete/inconsistent packet invalidation;
- contract-check isolation from the evaluator;
- output-root confinement, atomic write-once behavior, refusal to overwrite,
  canonical reread, and no partial stdout leakage.

The focused test command is exactly:

`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/experiments/candidates/opportunity_normalized_lease_gated_rebinding/test_heldout_delta2.py -q`

The non-result-bearing CLI smoke command is exactly:

`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.opportunity_normalized_lease_gated_rebinding.heldout_delta2 --check-contract --scope-path docs/research/candidates/opportunity_normalized_lease_gated_rebinding/evidence/2026-08-30-2026-08-30-portfolio-r19-onlgr-heldout-transfer-01-scope-and-grounding.md --scope-sha256 c2831053ecd59d37fbe434f88d93dad8beaf0ae6c58eef5153b2efece27ffdd4 --readiness-path docs/research/candidates/opportunity_normalized_lease_gated_rebinding/evidence/2026-08-30-2026-08-30-portfolio-r19-onlgr-heldout-transfer-01-geometry-readiness-g4.md --readiness-sha256 ae53a9038e534c5b8b3b3238378a8eaad95981fa594d059987756455f3866c6a`

CM stops after source, focused tests, and contract-only smoke evidence. CM must
not run, import through an executing entry point, or otherwise observe the
registered held-out result. Technical acceptance is not scientific acceptance.

## Separately owned future result plan

Only one separately authorized Experiment Operator may own the exact
result-bearing command from start through terminal return. The frozen command is:

`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.opportunity_normalized_lease_gated_rebinding.heldout_delta2 --scope-path docs/research/candidates/opportunity_normalized_lease_gated_rebinding/evidence/2026-08-30-2026-08-30-portfolio-r19-onlgr-heldout-transfer-01-scope-and-grounding.md --scope-sha256 c2831053ecd59d37fbe434f88d93dad8beaf0ae6c58eef5153b2efece27ffdd4 --readiness-path docs/research/candidates/opportunity_normalized_lease_gated_rebinding/evidence/2026-08-30-2026-08-30-portfolio-r19-onlgr-heldout-transfer-01-geometry-readiness-g4.md --readiness-sha256 ae53a9038e534c5b8b3b3238378a8eaad95981fa594d059987756455f3866c6a --request-path docs/research/candidates/opportunity_normalized_lease_gated_rebinding/workflow/research/engineering-request.md --output-root temp/directions/opportunity_normalized_lease_gated_rebinding/exp/heldout_delta2_g4_r1`

Before launch, Root must bind the exact accepted CM integrated SHA, working
directory, command, request hash, scope/readiness hashes, output destination,
operator identity, and zero prior result access in a separate run authority.
This request does not supply that authority.

The resource ceiling is one CPU thread, 512 MiB peak RSS, 60 wall-clock seconds,
no GPU, no network, no RNG, no training, and exactly 17 unrestricted grid
evaluations plus fixed candidate/control lookups. Stop after one terminal file
and process witness. The command is result-bearing even though deterministic.
An unknown or committed outcome is observe-only; never launch a second command,
change an input, scan another spacing, or rerun to repair an unfavorable result.

## Outcome and failure interpretation

- `EXP_FORM_TRANSFER`: at most one-cell operational EXP-form predictive value;
  finite log-survival remains an alternative.
- `RATE_FORM_TRANSFER`: at most one-cell operational RATE-form predictive value;
  `FINITE-AFFINE` remains an alternative and no physical-rate causality follows.
- `NO_DIRECT_HEADROOM`: valid adverse competence result; no form-transfer claim.
- `RAW_NOT_MATERIALLY_WORSE`: valid null for added physical-time-map value at
  this cell.
- `BOTH_MAPPINGS_MISS`: valid negative held-out form result even if one map is
  the less-bad relative fit.
- `AMBIGUOUS_VALID_OBSERVATION`: preserve the exact tuple and competing
  explanations; do not relabel as null, negative-complete, or failure.
- `INVALID`: no scientific update; repair requires a new prospective object if
  any result-sensitive input was exposed.
- `TECHNICAL_FAILURE`: no scientific update and no automatic rerun.

The program and Experiment Operator report facts only. EM alone interprets a
valid packet. A test pass, program exit, provider statement, CM conclusion,
runtime fact, or Git fact cannot select a scientific branch or Portfolio action.

## Finite claim ceiling, stop, and reentry

The maximum claim remains one exact operational out-of-fit comparison at
spacing two on the same single-unit, seven-tick, cost-two, base-`1/16`-grid,
state-blind-memoryless regenerative host. It establishes no arbitrary-spacing
law, semantic physical rate, exponential mechanism, learned ONLGR value, causal
lease or rebinding, task-content use, natural policy behavior, population/UAV
transfer, safety, deployment, workload equality, or PPO superiority.

Stop this request at `PREPARED_NOT_AUTHORIZED`. Reentry for CM requires the exact
accepted EM integrated SHA, unchanged request/readiness/scope hashes, terminal
Innovator disposition or exact waiver, a new Root CM assignment, and disjoint
engineering ownership. Reentry for the result requires technically accepted CM
integration and a separate exact Experiment Operator authorization. Reentry for
science requires the exact terminal artifact and operator fact under a new EM
assignment. No successor may infer authorization from this file's presence.

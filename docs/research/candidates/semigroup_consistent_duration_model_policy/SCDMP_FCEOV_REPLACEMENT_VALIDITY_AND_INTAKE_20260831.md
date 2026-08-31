# SCDMP FCEOV replacement validity and result intake

- Date: `2026-08-31`
- Direction: `semigroup_consistent_duration_model_policy`
- Scientific object: `foundation_conditioned_event_order_value`
- Scope: outcome-blind replacement of the incomplete V3 evidence attempt
- Quarantine boundary: the occupied `.1` root remains unread for outcome, non-resumable and
  non-reusable

## Conclusion

The replacement is the unchanged FCEOV scientific object, not a new estimand and not a continuation
of `.1`. Its treatment, graph-blind comparator simplex, foundation and assay population laws,
endpoint, `562` tapes, `3,372` cells, three normalized gaps, Bernoulli-KL intersection-union test,
integer thresholds and stop rule remain fixed. The earlier attempt omitted required prospective and
run-time resource observations, so it was an incomplete implementation and did not consume this
object. No field containing its outcome may inform the replacement or this note.

The replacement can be interpreted only after validity is established without opening its scientific
statistics. A missing required observation or a partial or drifting assignment is invalid evidence
with no polarity and no object consumption. A valid competence nonpass and either valid complete-panel
branch are frozen scientific branches and consume this exact purchase.

## Unchanged scientific object

### Question and strongest same-information null

At `QUAD-UAV-PALLET-GANTRY-24P5M-v1`, conditional on one fresh competence-qualified graph-erased
foundation, test whether the precommitted mapping

```text
RH -> A_RH = index 12 = (2,(0,0,1,-1))
HR -> A_HR = index 10 = (2,(1,-1,0,0))
```

has strictly greater balanced-graph native full-mission value than every graph-blind fixed or
randomized policy on

```text
A_RH, A_HR, COMMON = index 0 = (1,(0,0,0,0)).
```

The graph-blind simplex is the competent containing null. No realized tape selects an action. The
fixed host uses primitive tick `0.1 s`, horizon `364`, external `k=13`, the frozen reachable public
Dirac state, and the two fixed `HR` and `RH` latent support assignments. First-renewal public
observations are byte-identical; only latent support assignment differs. Entity membership and
identity are fixed.

### Foundation and competence law

Train exactly one fresh graph-erased `FoundationActorCritic` from genesis for `160` updates with `12`
complete fixed-13 episodes per update, balanced across graphs. The actor and critic receive no graph
bit, ordered token or latent assignment. Training resets retain the frozen product law for
`Uv,Uy,Uphi`, with no graph or disturbance dependence.

Competence uses `120` fresh independent missions, `60` per graph, disjoint from training and assay.
For the seven-member one-sided Clopper--Pearson family use `alpha=0.05/7` and require:

- each graph safe-docking lower bound strictly greater than `0.72`;
- the pooled safe-docking lower bound strictly greater than `0.84`;
- each of four pooled physical-failure upper bounds strictly less than `0.10`.

Boundary contact, incomplete competence evaluation or a valid competence nonpass stops before any
assay tape exists. There is no checkpoint, foundation-seed or retry selection.

### Assay population, endpoint and estimand

One observational unit is one complete disturbance tape. The registered scientific model treats
distinct `(domain,tape,tick,component)` assay addresses as mutually independent fair bits and the
assay domain as independent of foundation training and competence. Within a tape, the same
disturbance is shared across all six graph/action cells. Coverage and power are conditional on this
ideal-PRF/i.i.d.-tape abstraction.

Force the precommitted first action for `13` ticks or absorption, then return active lanes to the same
immutable foundation under deterministic lexicographic argmax. The sole endpoint is

```text
U = 1[safe dock] * (1 - dock_tick/364), failure or timeout = 0.
```

Let `B=363/364`, and retain exactly

```text
G_RH     = 0.5*d_1m
G_HR     = 0.5*d_0m
G_COMMON = 0.5*(d_0c+d_1c)
V_A      = min(E[G_RH], E[G_HR], E[G_COMMON]).
```

The first two gaps have support `[-B/2,B/2]` and range `B`; `G_COMMON` has support `[-B,B]` and
range `2B`. Normalize each component by its complete range as `X_j=0.5+G_j/R_j`. Simultaneous
positivity of the three means is necessary and sufficient for dominance over the complete
graph-blind comparator simplex. Separate signs for `d_0c` and `d_1c` are not scientific claims.

### Fixed sample, inference and stopping

Use exactly `562` independent tapes in `23` serial slices of `24` tapes and one final slice of `10`
tapes. Every tape appears in all six graph/action cells, yielding `3,372` complete terminal cells.
Analyze once and only after the entire panel is complete.

For each normalized component, use

```text
p_j = 1                                      if mean(X_j) <= 0.5
p_j = exp(-562*kl(mean(X_j)||0.5))           otherwise
p_IUT = max(p_RH,p_HR,p_COMMON).
```

The joint result passes only when `p_IUT < 0.05`; boundary equality does not pass. The scientific
margin is zero. Direct integer-grid and independent float64 log-space reductions must agree. Exact
strict passage requires

```text
S_RH     >= 21,046
S_HR     >= 21,046
S_COMMON >= 42,091.
```

Each preceding integer does not pass. The single publishable effect-scale bound is

```text
L_theta = min(ell_RH-0.5, ell_HR-0.5, ell_COMMON-0.5).
```

It is a one-sided 95% lower bound for the minimum normalized gap, not three standalone or
simultaneous component bounds. `L_theta>0`, all three component tests passing and `V_A>0` are the
same positive branch. At the frozen planning alternative of a gap equal to `0.1` of each component's
full support range, the distribution-free joint-power lower bound is `0.801021247429385`; this is a
design statement, not a claim margin.

No statistic, partial cell, favorable slice, resource observation or early pattern may stop,
extend, replace or reorder the panel. No new master, tape redraw, checkpoint selection, changed
`n`, changed threshold or result-aware extension is permitted after scientific activity begins.

## Pre-run validity checklist

Every item below must be established result-blind before the replacement becomes result-eligible.

### Quarantine and entrypoint

- The `.1` quarantine root is unchanged and every attempt to enter, resume, reuse or overwrite it
  refuses before scientific effect.
- One different canonical replacement root and one command are frozen prospectively; undeclared
  roots refuse before root, master, model, optimizer, checkpoint, tape or result creation.
- The replacement creates one fresh internal OS-cryptographic master with no CLI seed, master,
  retry, redraw or checkpoint-selection control.
- Initialization, complete-slice frontier publication and final publication are create-only and
  atomic. Same-instance recovery accepts only the same raw master, checkpoint, fixed tape addresses,
  immutable complete slices and next slice index.
- The owned and allowlisted Python/native surfaces and the actually loaded native binary have a
  pre-activity create-only snapshot of resolved path, byte length and full raw bytes. Recovery uses
  direct `read_bytes()` equality. No hash, digest, identity, authentication or approval field is
  introduced.

### Scientific and numerical conformance

- Host, public state, `k=13`, tick, horizon, event graphs, action catalogue entries, 13-tick hold,
  endpoint and graph-erased foundation inputs exactly match the frozen contract.
- Training is `160 x 12` complete fixed-13 episodes; the only checkpoint is update `160` at AdamW
  step `1,920`; fresh-genesis restore equality is observed directly.
- Competence has all `120` missions, the seven exact bounds and strict thresholds above, with
  training/competence/assay RNG domains disjoint.
- A competence nonpass creates no assay master addresses, tapes or cells.
- A competence pass enters exactly `24` fixed-order serial slices: `23 x 24 x 6` cells plus
  `1 x 10 x 6` cells. Each cell terminates and satisfies endpoint/support constraints.
- The ideal addressed fair-bit law, same-tape six-cell pairing, frozen foundation and deterministic
  post-hold argmax are unchanged; no action selector, graph input to the foundation or partial-result
  exposure exists.
- Integer-grid gaps, float64 `fsum` reduction, log statistics, p-value bounds, flags and `L_theta`
  are finite, support-valid and mutually consistent. Student-t, sign-flip and permutation analyses
  cannot activate a branch.

### Prospective resources and telemetry

- Before scientific root/master creation, run the direction-specific assessment with projected
  peak RSS `1 GiB`, scratch ceiling `64 MiB`, durable ceiling `64 MiB`, wall ceiling `300 s`, one
  worker and one native/Torch thread; persist its numeric sources, ceilings and verdict.
- Immediately before the formal invocation, and again before every result-bearing resume, retry or
  internal slice, run `python scripts/hmasd_resource_preflight.py admit-memory --out <fresh-receipt>`.
  Both physical and effective available memory must be at least `4 GiB`; missing or failed
  measurement refuses work.
- Observe the formal process tree's wall time and peak RSS live, and observe scratch high-watermark
  separately from final durable bytes. Persist every measurement and require wall `<=300 s`, peak
  RSS `<=1 GiB`, scratch `<=64 MiB` and durable output `<=64 MiB`.
- A failed memory admission performs no slice work and preserves the last complete frontier for a
  same-instance resume. Work performed with missing required telemetry makes the attempt incomplete
  and invalid; post-hoc directory or process measurements cannot repair it.

### Atomic evidence bundle

- Validity/resource records are inspectable separately from scientific outcome fields.
- The complete result atom contains exactly the `3,372` raw cells, three integer-grid gap vectors,
  point estimates, log statistics, p-value bounds, `p_IUT`, component audit flags and the single
  `L_theta`; no component or slice file is independently publishable.
- The final bundle binds the resolved canonical replacement root, raw master, run record and full
  raw-byte snapshot, and is published only after every required validity and resource observation
  is present.
- Unit, fixture, TEST_ONLY native and result-blind preflight checks pass without creating a result
  root, master, model, optimizer, checkpoint, assay tape or scientific result.

## Result intake order and branches

Intake is ordered so scientific statistics cannot influence validity adjudication.

1. Verify quarantine isolation, canonical replacement root, frozen source/configuration, fresh
   master law, atomic frontier, complete prospective resource records and run-time high-watermark
   telemetry using only validity and structure fields.
2. If any required stage, observation, numerical/RNG/support invariant or publication atom is
   missing or drifting, classify `INVALID_EVIDENCE`, do not open or quote scientific statistics,
   assign no polarity and do not consume the object. Quarantine that attempt. A later fresh
   outcome-blind replacement may implement the same unchanged assignment after defect repair.
3. If the implementation is valid through the competence stop and competence does not pass,
   classify `FOUNDATION_COMPETENCE_NOT_ESTABLISHED`. Confirm that no assay tape exists. This is a
   valid frozen branch and consumes this exact purchase, but establishes nothing about event-order
   value.
4. Only after validity and competence pass are fixed may intake open the complete atomic panel.
   Recompute all cells, gaps, support checks, integer thresholds, log statistics, `p_IUT` and
   `L_theta` independently from the raw terminal records.
5. If all three component tests strictly pass, classify
   `TARGET_CANDIDATE_ORDER_VALUE_ESTABLISHED` and publish only the joint conjunction and single
   `L_theta`.
6. Every other valid complete panel is
   `TARGET_CANDIDATE_ORDER_VALUE_NOT_ESTABLISHED_AT_FROZEN_RESOLUTION`. It consumes this exact
   purchase and closes the exact state/`k`/foundation/candidate-set gate before an adapter. It does
   not establish zero, negativity or which component failed in the population.

A resource refusal or clean process interruption at an atomic frontier is technical rather than a
scientific branch. It may continue within the same evidence instance only with the same master,
checkpoint, tape addresses, immutable complete slices and fresh passing 4 GiB admission. Partial
cell salvage, a rewritten complete slice, a new master or a result-informed continuation is invalid.

## Claim ceiling and interpretation boundary

At most, a valid positive result supports:

> Conditional on one fresh competence-qualified order-erased foundation, at the exact public state,
> external `k=13`, exact simulator and registered fair-bit disturbance law, the prospectively fixed
> graph-matched mapping has greater balanced-graph full-mission value than every graph-blind fixed
> or randomized policy on `{A_RH,A_HR,COMMON}`.

It does not establish either per-graph COMMON contrast separately, any component as a standalone
95% claim, best-18-action value, the foundation's natural first action, learned order use, causal
mediation, general chronology, duration selection, semigroup composition, arbitrary state, graph or
`k`, another foundation, variable membership, transfer, safety, deployment or flight. The inference
is conditional on the one realized competent foundation and the ideal-PRF/i.i.d.-tape abstraction;
there is no foundation-seed superpopulation claim.

A valid positive makes this fixed candidate gate eligible for a separate adapter decision; it does
not authorize integration by itself. A valid complete nonpass ends this exact purchase before an
adapter. A valid competence nonpass leaves order value unobserved. Invalid or incomplete evidence
changes neither scientific polarity nor this claim ceiling.

## Evidence paths

- `AGENTS.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/research/portfolio/PORTFOLIO.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/IMPLEMENTATION_THRESHOLD.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_FCEOV_PROSPECTIVE_FINITE_SAMPLE_INFERENCE_FREEZE_20260831.md`
- `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_FCEOV_V3_INVALID_EVIDENCE_RESOURCE_AUDIT_20260831.md`

The quarantined `.1` outcome and result fields were not inputs to this note.

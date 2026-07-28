# Reconciliation — the autopsy plan, converged

Ruling: `21_PRO_OPEN_RAW.md`, stage commit `f1d79b17`. **APPROVED WITH
MODIFICATIONS.** Pro converged it; this conversation implements it.

## The decision

The artifact-only autopsy remains the next scientific action and may run locally
against the byte-unchanged pooled artifact. No new environment run, no expansion
topologies, no added replicates, no changed threshold, no reinterpretation of R3
as an identified source-necessity result. *"No environment compute is selected by
this ruling."*

## The six modifications, and what each obliges

1. **Name the output correctly.** The autopsy analyzes *the scalar quantities
   recorded by the executed R3 code, conditional on the correctness of that
   execution path*. Every emitted quantity is labelled `artifact-derived`. It is
   not a second validation of the trajectories.
2. **An input-and-semantics sentinel, fail-closed.** Before emitting any
   statistic the script must verify the artifact hash, contract id and procedure
   version, the exact seed set `20260726–20260733`, `smoke=False`, the four
   `topology_units` collections, and **exact reproduction of all six registered
   R3 bounds**. My manual 1e-12 reproduction becomes an executable precondition
   rather than an external assertion — the strongest single modification, because
   it converts my own verification into something the instrument re-does.
3. **Preserve the bootstrap factorization.** Shared *topology* indices across
   quantities, but calibration episodes and audit events resampled
   **independently within** a topology — they are disjoint blocks. My plan said
   "shared topology resampling stream" without stating the inner independence,
   which was ambiguous enough to implement wrongly.
4. **Explanations overlap.** Emit an evidence vector, never a winning cause.
5. **N4 may establish heterogeneity, not regimes.** Eight observed topologies
   with no permitted expansion cannot close a regime claim. Any partition by BS
   quadrant or geometry is exploratory and must be marked so.
6. **The autopsy may nominate but not freeze R4.** The scale-versus-carrier
   decision is a scientific disposition at the next boundary.

## Where Pro corrected this conversation

1. **A fifth explanation was missing.** **N5 — comparator-scale mismatch:** `B_m`
   measures global proactive rotation versus none, while `U*_m` measures a focal
   one-Δ reassignment under reoptimized continuation. *These are not the same
   intervention.* The normalizer may be measured correctly and still be the wrong
   scale for the effect. This is the most consequential thing in the ruling, and
   my plan's four explanations had no room for it.
2. **"Everything else is executable as written" was too strong.** N4 lacked a
   criterion separating heterogeneity from regimes, and the `B_m`–`U*_m`
   association needed the paired-outer/independent-inner resampling of (3).
3. **A selection-instability diagnostic is required** as a qualifier on N2 — at
   the `2/2` floor the selected SET alternative can be unstable, and R2 already
   required selection frequencies and entropy.
4. **The apparatus lemma was stated too broadly** — see below.
5. **"Valid matched observation" needs downgrading** — see below.
6. **`component_invariance_evaluated=False` is not a complete prospective
   design** — see below.

## Q3(b): raising it against my own plan was right

Pro withdrew its own earlier wording. The retained lemma is now:

> The artifact preserves the intended eight-topology data and provenance
> structure well enough for conditional artifact analysis. The current test suite
> did not independently certify every guard or numeric transformation on the path
> that produced it.

And the run is now described not as "a valid matched observation" but as *"a
provenance-recorded, CRN-paired, executed-code observation that remains
admissible for diagnostic reanalysis, but is not independently validated at every
conclusion-bearing transformation."*

**But the second half of my own argument was rejected, correctly.** I had put it
that if the observation is not usable, instrumenting the guards should come
first. Pro: adding guard tests now *"could not retroactively reconstruct the
missing component series"*, so hardening instead of running the autopsy would not
solve the historical limitation. The autopsy proceeds; every conclusion inherits
the conditional scope.

**A hard gate was set, though:** before any *future* environment run, the guard
gaps in `window_g_from_step_metrics`, baseline masks, calibration arm ordering,
audit-limb assignment, seed-controlled provenance, qualifying-event construction,
and clone conditions 2/3/5 **must** be closed with paired negatives or another
independent conformance mechanism. That is now a precondition on the next run,
not a backlog item.

## N3 and component invariance

`N3 = UNDISCRIMINATED_FROM_STORED_ARTIFACT`. Option 3 with option 1 as the
mandatory historical report — my recommendation, adopted. Prospective persistence
must retain per paired continuation the QoS and capped return-cost series, the
window-local cutoff and depletion transition series, component window totals,
total `G`, saturation, and the paired arm identity. Pro added a requirement I had
not seen: **exact paired-sequence equality must be computed before serialization
and recorded separately**, because persisting only the `nondegeneracy_report`
would allow coarse decomposition but could not establish exact arm-invariance,
which R2 made a distinct degeneracy condition.

On component invariance, **neither of my two options was right**. Tri-state:

```text
if normalizer_forces_degenerate:      # not (stable_b_identified or flex_b_identified)
    branch = PRIMARY_G_DEGENERATE     # reason NO_POSITIVE_NORMALIZER_ON_EITHER_LIMB
elif not component_invariance_evaluated:
    result = INVALID_EVENT_ALIGNED_AUDIT   # branch 1, not branch 10
    reason = MANDATORY_PRIMARY_G_COMPONENT_AUDIT_MISSING
else:
    ... stable_measurement_valid / flex_measurement_valid ...
```

So branch 3 stays reachable through the independently sufficient normalizer
condition — which is what the current implementation already does, and Pro
confirmed it *"correctly applies the disjunctive normalizer rule"* — while a
future run with a missing mandatory component audit fails **closed** under branch
1 rather than proceeding. My binary framing would have either fabricated the
input or made the branch unreachable again.

## Execution order, as converged

1. Implement the deterministic artifact-only autopsy with the modifications.
2. Abort unless the input sentinel reproduces the six frozen R3 bounds.
3. Emit standalone distributions and the N1/N2/N4/N5/selection evidence matrix.
4. Record N3 as `UNDISCRIMINATED_FROM_STORED_ARTIFACT`.
5. Add prospective component persistence and fail-closed component-audit
   semantics, without rerunning R3.
6. Return the autopsy artifact for the R4-scale-versus-source-retirement
   decision.

Steps 1–5 are this workflow's implementation. Step 6 is its result submission —
touchpoint 3, and the next workflow's touchpoint 1.

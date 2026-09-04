# UCOPE root target-versus-fit R01 attempt 02 — DM intake

- Direction: `ucope`
- Object: `UCOPE-A-RECON-THREE-WITNESS-ROOT-TARGET-VS-ROOT-FIT-AUDIT-R01`
- Evidence class: **A/RECON**
- Attempt status: **quarantined incomplete; no scientific polarity**
- Applied branch: `RECONSTRUCTION_OR_BINDING_FAILURE_NO_SCIENCE`
- Intake date: 2026-09-04

## What I checked

I compared the copied summary and admission receipt with the frozen card, launch SHA, staged-input
binding, remote task facts, exact argv, counts, resource floor, wall cap, reconstruction tolerance
and result rule. The result root contains one receipt and one summary at the recorded hashes. The
supervisor accepted only task 02, which terminated with exit 6; no second task or local fallback was
started.

CM independently recalculated all 24 predicates from the copied JSON bytes. The recalculation
matches every stored pass flag: all six tail references pass, three of six root references fail,
and five of twelve live-root distance checks fail. CM also reapplied the card branch order and
reproduced `RECONSTRUCTION_OR_BINDING_FAILURE_NO_SCIENCE`.

## Observation that bounds the attempt

Direct observation: the exact retained input and full declared reconstruction workload ran after a
valid remote admission, but eight solver-derived checks lie between
`1.010413974711355e-12` and `1.1838308111578044e-12`, above the absolute `1e-12` boundary. The
runner therefore correctly withheld complete policies and scientific polarity.

Bounded reading: this is a cross-node numerical-conformance failure. It says nothing about whether
the two false-positive roots arise in target construction, exact projection or finite fitting. It
also says nothing about UCOPE headroom, baseline competence, treatment value, acquisition,
COUNT/RAW, lifecycle or Portfolio priority.

Strongest technical support: exact source/input binding, complete work counts, 24/24 independent
predicate agreement and the first-match no-science rule.

Strongest contradiction to a simple diagnosis: every MSE-tail check passes and 16/24 predicates
pass; the artifacts do not identify which numerical backend operation produced the marginal root
differences. Calling this specifically a LAPACK failure would exceed the evidence.

## Flags for the owner

- The attempt is not a negative result and does not change the direction's `ACTIVE/HIGH` state.
- The frozen `1e-12` tolerance, `lstsq(rcond=None)`, solver, input and result rule were not changed
  after output.
- A local fallback is not used: the remote scientific task was accepted and produced
  question-relevant reconstruction values.
- The exact mechanism question remains open. No successor is selected from this attempt.
- A diagnostic that binds one failing `design64` and target array byte-for-byte across nodes is the
  smallest way to locate the engineering boundary, but it is not a scientific rerun or polarity.

## Decisions this intake produces

### Decision 1 — disposition of attempt 02 (object tier)

Options:

- **(a) Quarantine the attempt.** Preserve its receipt, summary and task facts; publish no mechanism
  branch; keep the frozen object unresolved.
- **(b) Salvage it by relaxing the tolerance or selecting the passing rows.** This would rewrite
  the frozen rule after observing output and is inadmissible.
- **(c) Rerun locally or launch another unchanged remote task.** The accepted remote task already
  produced question-relevant values; an unchanged repeat or node switch is not an allowed remedy.

Recommendation: **(a)**.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. This is a reversible attempt-level quarantine, not closure of the object family
or direction.

No direction-tier decision is formed. Changing the frozen numerical boundary or selecting a new
mechanism object is outside this intake.

## Next engineering discriminator

Serialize one or a few failed blocks' `design64`, FP32 target arrays and retained reference vectors;
verify their byte identity on both nodes; then execute the same `lstsq(rcond=None)` while recording
NumPy and LAPACK backend facts. Identical targets with different roots would localize the solver;
different target bytes would move the boundary earlier. This is a recommendation for a separately
frozen diagnostic, not authorization to rerun or reinterpret attempt 02.

## Evidence paths

- Card: `docs/research/candidates/ucope/UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_CARD_20260904.md`
- Attempt evidence:
  `docs/research/candidates/ucope/UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_ATTEMPT02_EVIDENCE_20260904.md`
- Summary:
  `temp/directions/ucope/exp/root_target_vs_root_fit_audit_r01_20260904/summary.json`
- Admission:
  `temp/directions/ucope/exp/root_target_vs_root_fit_audit_r01_20260904/resource_admission.json`
- Task facts:
  `temp/directions/ucope/exp/root_target_vs_root_fit_audit_r01_20260904_operator_attempt02/`

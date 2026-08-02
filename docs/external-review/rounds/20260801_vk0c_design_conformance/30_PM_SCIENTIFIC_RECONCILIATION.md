# Reconciliation — 20260801_vk0c_design_conformance

Ruling: `21_PRO_OPEN_RAW.md` (CHANGES_REQUIRED) converged by
`22_PRO_CONVERGENCE_3.md` (CONFORMS), stage commit
`060a86d9181be1f2721d693fd30a84a2f27affcb`.

## What was decided

Touchpoint 2 of workflow 7. The fence returned CHANGES_REQUIRED with ten
blocking amendments; entered verbatim into
`docs/research/designs/VK0C_REALIZATION_DECISION_LEDGER.md` as A-VC-1..11
(commit d5721372) and submitted in convergence turn 1. The certified
convergence decision (turn 3, after two transport-truncated captures — see
the intake record) is **CONFORMS**: all eleven amendments closed, no
remaining deviation, no new protected decision, no further design round.
Every scientific surface is FROZEN (question, checkpoint set, 2,688-anchor
population, order comparison, token probability semantics, finite-state
propagation, normalization, occupancy interpretation, Factor A–E system,
artifact provenance, fresh-init control).

The decision adds five realization clarifications, binding at Gate B, not
new design surface:

1. `token_mass` is the sole probability authority — one path
   (`token_mass → act_sequence sampling → V-K0C enumeration`); a second
   logits-to-probability implementation reopens A-VC-1/A-VC-2.
2. The propagation state is frozen as (check index, physical-agent joint
   skill pair, skill ages, active mask, target phase/sign state); a hidden
   mutable variable found to affect probabilities, transitions, rewards,
   order transport or occupancy either enters the formal state or returns
   the design to review.
3. Numerical sequence: raw masses → validate (finite, nonnegative, legal
   support, same-label SET exactly zero, dtype-tolerance sum) → ONE
   canonical normalized distribution used everywhere downstream, raw masses
   and correction preserved. Report-only normalization, raw propagation,
   and split distributions are prohibited.
4. Occupancy-mediation label is `SERIALIZATION_INDUCED_OCCUPANCY_SHIFT_
   IDENTIFIED`, requiring matched-state equivalence in pooled AND both
   stratum views plus exact propagation reproducing the competence split;
   pooled cancellation from opposite direct effects is not mediation.
5. Analyzer authorization comes only from `vk0c_input_manifest.json` and
   the row files; directory names, filesystem state, checkpoint filenames
   and unstamped artifacts are prohibited authorization sources.

Next permitted step per the decision: the proof-sized realization artifact
demonstrating the Gate-B witnesses (probability, transition, order,
artifact and numerical paths) before full implementation; execution is not
yet authorized.

## Where I was corrected

The ten amendments themselves are the correction record for this round: the
original ledger under-specified token-mass branch semantics, input-manifest
immutability, initial/inter-check transitions, the mass-tolerance rule,
stratified reporting, Factor-D stratum safety, analyzer authorization and
the fresh-init hash scope. The 1e-9 / report-only normalization rule I had
written was withdrawn and replaced by the dtype-derived rule. Conclusion
survived (the route conforms), the realization bindings did not — all ten
were entered verbatim rather than reinterpreted.

## Next action

Implementation wave W-A/W-B/W-C per the amended ledger with the Gate-B
witnesses as focused tests and a bounded smoke as the proof-sized artifact;
the formal 2,688-anchor run is a separate PM-launched step afterwards, then
touchpoint 3 with the result.

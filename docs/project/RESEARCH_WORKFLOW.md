# HMASD Agile Research Workflow

## Research loop

1. Keep multiple plausible research routes alive rather than converging early.
2. Probe independent mechanism families through distinct consequences and simpler explanations.
3. Choose the smallest reversible action with the highest expected information gain.
4. Freeze evidence meaning before collection, then update only the smallest unit implicated by the result.
5. Preserve promising routes with explicit reactivation conditions, and integrate late only after they withstand simpler explanations.

## Review and repair


Immediately before Git push, the complete stable round receives one collective
final review: the Reviewer and Verifier inspect the same package in parallel.
If they find no defect, this is the round's only review.

If that review or an authorized run exposes a concrete defect, freeze the
failure, dispatch `hmasd-frontier-implementer` for the bounded repair, and
append a fresh independent collective review of the repaired package. Repeat
repair and independent review until the workflow is resolved or a genuine
external blocker remains. Never retry an unchanged failure or push before the
final gate is clean.

Do not test workflow documents or file topology. The research action itself
provides the evidence: a derivation, counterexample, focused executable
exercise, prototype observation or authorized experiment.

## Minimal records

A research action needs one concise conjecture card, one smallest discriminating action and one scientific delta. Write an implementation plan only when implementation is selected; write an experiment contract only when a run is authorized.

Git branch and commit are the sole artifact identity and provenance. Do not create document hashes, source manifests, receipt schemas, response markers, snapshot-stability gates, archival validators, topology tests or duplicated handoff files.

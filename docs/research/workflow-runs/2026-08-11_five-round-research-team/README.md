# Five-round research-team workflow log

This directory is a compact factual ledger for the requested five end-to-end
loops. A round number is a target loop slot, not proof that the loop is already
complete. The observed lanes proceed concurrently and are not a serial queue.

Luna is a passive recorder only. Root remains the sole scheduler and workflow authority. Unknown session identity values remain `null`; this log does not create an identity or authentication system.

Workflow-contract/log baseline: commit `980f44df`, ordinary-pushed to `origin/aggressive`.

Disposition vocabulary is object-level. The ledger must name whether a fact
applies to a `run`, `treatment`, `formulation`, `prospective successor`, or whole
`direction`. Legacy `FILTERED` events record only that a candidate was not
allocated under the then-current screen; they do not establish scientific
failure or direction retirement. Code/host absence is an engineering-cost fact
unless the exact claim is retrospective existence or provenance. A direction is
retired only after explicit construct-first successor exhaustion; otherwise use
`PROSPECTIVE_SUCCESSOR_UNEVALUATED`, `QUEUED_FOR_CM_FEASIBILITY`, or
`PARKED_BY_PRIORITY_WITH_TRIGGER` as applicable.

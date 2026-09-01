# VNFC BPCR B/EXPLORE R01 engineering milestone

## Disposition

`VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R01` is construction-complete enough for
static review but is not executable. The runner declares `IMPLEMENTATION_READY = False`.
Do not run DEBUG, PRIMARY, OPTIONAL, result serialization, or DEBUG-gate construction.
Every public execution or publication entry must first validate a fresh passing 4 GiB
preflight receipt and then stop with `REPAIR_REQUIRED`, before native admission, RNG/model
construction, training, checkpoint creation, result reads, or file writes.

The pre-seal baseline reported by the integration wave is 53 non-result-bearing tests.
The focused runner suite additionally checks the centralized hard fence and has no native
endpoint test enabled.

## Final-review material repair contracts

The final independent review found three material gaps. The hard fence prevents them from
producing activity or an artifact; it does not resolve them:

1. Failure quarantine is incomplete. Once execution is eventually enabled, every post-admission
   training, gate, checkpoint, and evaluation failure must create one structured `INCOMPLETE`
   record without leaving an orphaned create-once checkpoint that blocks the namespace. The
   common-host BCRH failure path must carry an explicit reason and must never index a missing
   `missing_adapter` field.
2. Artifact validation is not yet meaning-complete. Recovery values must be recomputed from the
   retained raw tick rows. BCRH checker rows, N7 sensitivity, DIRECT residual activity, native tick
   totals, and primary-only versus paired host-call counts must be deeply validated and rebound to
   the terminal rather than accepted from lengths or summary booleans.
3. PS-B0 evidence is incomplete. A source-bound built-in actual-path support-state adapter must
   construct the null-legal, multi-candidate, opaque deterministic tie-support states without
   claiming an unobserved equal-logit tie. The artifact must retain all 288 addressed comparisons
   plus canonical/presented score and probability-difference diagnostics instead of only a summary.

After those repairs, measured external performance telemetry is still required. Current schema
validators and static counts are not end-to-end evidence and do not establish peak RSS, throughput,
scratch/durable high-water marks, I/O, or the true overhead of primary-only BCRH and sensitivity
calls.

Recovery/tick telemetry is directly observed on the deterministic shadow host. Its application to
the registered R09 primary host is only an inference conditioned on exact same-input/action,
boundary-output, and source equivalence; it must never be described as a direct primary-host
observation.

## Preserved engineering work

The construction surface contains paired single-seam native wiring, exact DEBUG/PRIMARY count and
exposure contracts, finite-value/action-probability rejection, training/evaluation/readout schemas,
create-once checkpoint/result format scaffolds, and treatment-blind N7 action-sensitivity wiring.
The material validation and quarantine gaps above remain open. These are implementation assets,
not permission to execute R01.

Construction-only helpers are deliberately excluded from the module public export list. The
internal lower-level orchestrator remains solely for static call-order tests and is not an
alternative runtime entry.

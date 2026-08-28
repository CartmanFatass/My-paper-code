# Historical Portfolio pilot audit — terminal cancellation (2026-08-28)

This note records the terminal audit of the two-direction pilot. Current
lifecycle and capacity remain authoritative only in
`docs/research/portfolio/PORTFOLIO.md`.

## Native task and writer-phase audit

- EGRCR EM task: `01a0499e-4466-73b0-8d3b-f21b3f6a030c`, native worktree
  created from `main` at `f421a814d87c36be3492ac778c473f3b3cacb4c5`.
  Its R02 WORK was cancelled only after the submitted Innovator operation
  reached `NATURAL_COMPLETION_VERIFIED` (`sendCount=1`); response is archived.
- ONLGR EM task: `01a0499e-8419-74d2-b4f2-5ae92c722a90`, native worktree
  created from the same baseline. Its Innovator preflight stopped before send
  with `IDENTITY_UNREADABLE` (`sendCount=0`) and was then cancelled.
- No CM task or experiment command ran for either direction. No Convergence
  call ran. Both targets are released by terminal `CANCELLED` results; no
  archived participant was reused and no target had multiple unfinished
  inbound WORKs.

The native writer-phase contract was preserved: EM-only scope/state writes
were committed in each direction worktree before cancellation; no CM writer
phase was opened, so no EM→CM fast-forward or CM→EM adoption was required.
No shared-core path, numerical/RNG/checkpoint semantics, or external project
state was changed.

## Defects and disposition

The pilot is not clean enough to expand. EGRCR incurred a material
commitment-unknown interval (`SUBMITTED_UNVERIFIED/query_aborted`) before
observation completed; ONLGR had an unreadable Pro identity before send.
These transport defects blocked the required Innovator/Convergence sequence,
so the scientific round has no new executable observation or adversarial
convergence evidence. Both directions are PARKED with no current advancing
capacity. A future attempt requires a fresh complete Portfolio WORK and fresh
cycle identity after the native Pro transport is readable; no current
operation may be resent.

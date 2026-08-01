# Reconciliation — 20260801_d7_s_b3l_design_conformance

Ruling: `21_PRO_OPEN_RAW.md`, stage commit `eac5b6d807e6aedb87352aefc51f60ffae0a4563`.

## What was decided

`CONVERGENCE_DECISION: FREEZE AFTER MODIFICATION.` The B3-L route, complete
assertion-6 scope, int32 binding, fresh-population rule, R4 estimand, fixed
evidence volume and fail-closed provenance principle are correctly
transcribed; D1, D7, D8, D9 conform as designed; D2, D5, D10 conform with
clarifications; D3, D4, D6, D11, D12 required changes. All required
modifications are now entered in the ledger's **Frozen amendments** section
(same commit as this reconciliation): launch-time execution-class
enforcement with parent/worker attestation and a stable `source_code_id`
replacing commit currency (D3, O1, O6, O10); the gate exercising the actual
four-worker spawn route with Part-A + focal block coverage, deterministic
development-key selection, three initial-RNG witnesses, and deterministic
pre-bootstrap comparison only (D4, O2, O3, O4); the canonical versioned
trajectory-digest surface with fail-closed completeness (D5, O7); three
post-preaction liveness deltas (D6); topology-procedure version and amended
identities in the inventory (D10, O9); the exact formal A/B
paired-construction protocol with "always continue from A" (D11, O5); and a
self-contained, non-self-referential PASS certificate (D12, O8).

All four flagged interpretations were ACCEPTED (D10 coordinate timing; D5
gate-only per-step digests; D11 gate-only reasons; D6 fingerprint exclusion
— the last conditionally, with its paired negative required).

Implementation may now proceed under ordinary PM authority without a third
design round, provided no new protected choice is introduced; any newly
discovered protected decision returns to Pro. The gate remains unrun; steps
N and O remain held; the ruling authorizes no compute.

## Where I was corrected

- **Commit-based certificate currency was self-invalidating** (committing
  the certificate changes the commit it names) — replaced by
  `source_code_id` over a frozen path closure. I designed a currency test
  that could never be current.
- **The gate as designed did not exercise the process topology it
  certified** — a sequential subprocess with `workers=4` written in its
  record proves nothing about the spawn pool. Attestation is now required.
- **Part-A was omitted** — I covered only the focal-audit block while the
  conclusion consumes both blocks.
- **"Choose another dev index" was a discretionary selection step** — now a
  frozen ascending search with a rejection log.
- **The liveness counter could count initialization** — replaced by
  post-preaction deltas across three named regeneration mechanisms.
- **The committed certificate was not self-contained** — its load-bearing
  evidence lived under a gitignored path.

## Next action

Loop step 5: implement the amended ledger via registered subagents
(`hmasd-task-design` sizing, `hmasd-implementer` execution), PM review and
focused tests (step 6), then the gate run, step N and step O (step 7) under
the active grant, then touchpoint 3.

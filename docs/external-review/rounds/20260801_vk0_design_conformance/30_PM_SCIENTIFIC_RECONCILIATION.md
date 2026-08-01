# Reconciliation — 20260801_vk0_design_conformance

Ruling: `21_PRO_OPEN_RAW.md` (CHANGES_REQUIRED) then `22_PRO_CONVERGENCE.md`
(CONFORMS), stage commit `5d471457d1de2bb4974124cef0f1d3dea244f206`.

## What was decided

First turn: CHANGES_REQUIRED with six closure items — permutation-equivariant
two-track V-K0A incumbents (the lexicographic tie-break was not anonymous:
it does not commute with slot permutation and can collapse the two panels
onto one identity-preferred path); complete from-reset boundary fingerprint
with fail-closed replay (the cited precedent verified prefix
actions/rewards/incumbents only, and drop-and-count could alter sample
composition — any mismatch is now `INVALID_VARIABLE_K_URGENCY_AUDIT`);
durable row identity/recomputation keys plus row-persisted natural
five-step reward and match vectors; resolved-runtime preflight and
checkpoint/config/authorization provenance (identity never binds to the
filename `latest.pt`); V-K0B computes `U_src` by the exhaustive oracle on
each row's ACTUAL incumbent pair (the older audit's skill-axis shortcut is
prohibited as a conclusion-bearing label); and executable decisive-failure
versus unresolved branch predicates for every stratum.

Convergence turn: the amendments (ledger section A-VK-D2..D10, entered at
commit `317a3588`) CLOSE the check. The V-K0 sequence, source estimand,
policy-side estimands, panel construction, paired replay semantics,
trace/provenance semantics and branch predicates are FROZEN; no new
protected decision; no further design round. Two realization
clarifications, PM-owned: (1) the V-K0A artifact hash is
non-self-referential — a sidecar digest or launch-manifest hash, verified
by V-K0B against an independently frozen expected digest; (2) the
"any other mutable runtime field" clause must become an explicit enumerated
field set in the proof-sized skeleton, verified at the internal realization
gate; a newly discovered omitted field is an implementation-conformance
defect, not a design reopening.

The next permitted artifact is the proof-sized executable skeleton (two-
track panel, actual-incumbent oracle, complete replay fingerprint, row
serialization and joins, authorization verification, bootstrap inputs,
branch-selector witnesses), which then passes the internal realization
review. Implementation and experiments sit outside the ruling's own
authorization; compute is covered by the user's active grant.

## Where I was corrected

- My tie-break was identity-preferring under relabelling — an anonymity
  defect in the panel realization I had flagged as safe.
- I overclaimed the replay precedent ("verifies every listed snapshot
  component" was false — it verifies four of them).
- "Verbatim schema" was wrong in the other direction: the ruled lists were
  semantic minima, and my reading would have shipped rows that cannot be
  joined or resampled.
- Post-run exposure checking alone is too late; the preflight belongs
  before the first environment step.
- "Eight rows verbatim" was not an executable selector; the decisive/
  unresolved split needed freezing and was a protected branch decision.

## Next action

Loop step 5: implement via registered subagents in waves — V-K0A oracle
driver; `agent_order` threading with its guard; V-K0B driver with the
fingerprint, trace and authorization chain plus the training launcher and
preflight; analyzer with the frozen predicates. Then the proof-sized
skeleton witnesses, PM review (step 6), V-K0A run, and conditionally V-K0B
(step 7).

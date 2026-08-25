# RCLE TBCFV r04 current-authority reacceptance evidence gap

```text
direction_id=roster_consistent_latent_exploration
logical_identity=EM-roster_consistent_latent_exploration
generation=1
artifact_role=local_evidence_reconciliation_and_exact_technical_gap
registry_revision=7
registry_sha256=fb1c32ce91d10625f7e1117c4fe3cff9f031c9ce66a1b540880d38ce075d3089
portfolio_sha256=a3da214941f3163f21033991f6d5f2338e2d3b59f32c3ef32cb4dfcc1998f65a
frozen_question_sha256=b02a61943ad67c19a55ebe4ca841d92917dd38825246be39ca78d5bd187e8e2b
frozen_evidence_set_sha256=03e131b71d63db78ca5c13ffe497fa778a9ae23a6cc53e301bb0350797543ce0
engineering_request_activated=false
external_review_performed=false
lease_issued=false
operator_authorized=false
scientific_command_executed=false
result_or_partial_output_inspected=false
direction_authority_changed=false
source_or_test_changed=false
```

## Frozen authority and lifecycle reconciliation

| Reference | SHA-256 |
| --- | --- |
| `docs/research/candidates/roster_consistent_latent_exploration/DIRECTION.md` | `f98b477bfb15f286f1b6a4fd798cb949713986f19911adb676b031829e0f71f2` |
| `docs/research/candidates/roster_consistent_latent_exploration/RCLE_TARGET_BOUND_COMMITMENT_FRAGMENTATION_VALUE_SCIENCE_CARD.md` | `86a0f5efd69d6b92482cb081973effa67972aad8421d3abd25305e50dc6c1fd8` |
| `docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_R04_IMMEDIATE_SUPERSEDING_LEASE_PORTFOLIO_EM_INTAKE_20260824.md` | `0f2f4d1f9a36c0815cf3db89b95b0f47a38fc4640eb47926e0f3fe863f544a85` |
| `docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_R04_EXTERNAL_PRO_CLOSED_INTAKE.md` | `6e6b9271c2309069eff8e19a03d50eb0bf76f80cf6782f423fcf0a97ebb88b7f` |
| `docs/research/candidates/roster_consistent_latent_exploration/workflow/external-review/index.json` | `7ff2d6c32704e505fb490e87abc965a60e04f87a6b50f36628b4fd5f7b18a75e` |

The assignment began from research-state revision 1, SHA-256
`1e5c8c141ce993a9ef1aa12d2b3e97e3f615c30fb55772a755dc9df87a71dec0`.
Root subsequently performed a compatible schema migration. The reconciled input
is research-state revision 2/schema 2, SHA-256
`86a53281e7eac1d091291f1926f19209aa3c79f26afab453ca0a7619f08f8f02`;
its scientific question, evidence-set identity, actionability, and null
engineering request are unchanged.

Registry revision 7 keeps RCLE `ACTIVE`, generation 1, and preserves the
revision-6 lifecycle decision, “Legacy-state correction and Portfolio
expansion — 2026-08-25T11:50:42Z.” The later Portfolio checkpoint retires the
generic `PARKED` lifecycle but does not alter the RCLE target. Historical
`DORMANT_REVISIT` and the non-launched index-3 record therefore do not suppress
bounded preparation work. They also do not erase the immutable bytes and
history that a technical supersession proof must preserve.

The direction authority retains the panel as Pro-closed. The historical closure
intake records `provider_disposition=CLOSED`, zero science-bearing defects, and
`em_disposition=ACCEPT_CLOSED`. The current external-review index has no rounds.
Those facts are compatible: the closure is repository-held provenance from the
prior workflow, not a current provider operation or a round that may be resent.
No external review is needed for the non-scientific lease-authority question.

The research question and evidence-set SHA values remain frozen. Portfolio and
registry checkpoints are workflow authority, not a silent change to RCLE
science.

## Material conclusion

The immediate-window intake supports a precise candidate CM boundary, but the
current repository does **not** support activating that boundary as a directly
actionable engineering request.

Two indispensable technical inputs are absent. First, the immutable index-3
lease bytes, accepted CM return, scratch validator, and complete predecessor
byte/history chain live at ignored `temp/` locators and are not present in this
checkout. Second, the accepted RCLE admission path has no current-authority
registry, revocation input, or supersession gate. A new byte-preserving wrapper
could validate a sidecar relation, but the old index-3 lease would remain
independently admissible through the unchanged runner and CLI. Such a wrapper
cannot prove exactly one launchable authority.

Changing the existing contract, runner, or CLI to consume a supersession record
would change members of the accepted 24-row production source inventory and
therefore violate this cycle's accepted-byte preservation boundary unless a
separate authority first permits fresh current-byte reacceptance. No such
permission is inferred here.

This is an exact technical evidence gap, not a science failure, a negative RCLE
result, or a reason to deactivate the direction.

## Evidence separation

### Repository facts

1. The immediate intake binds the historical record to:
   - lease path `temp/leases/RCLE_TBCFV_R04_ROOT_INDEX3_LEASE_20260824_04.json`;
   - lease ID `RCLE-TBCFV-R04-ROOT-EMPIRICAL-20260824-04`;
   - lease SHA-256 `8b9ae6520b5bbae547ce65973fcdeb24ea46f270dee18ddbb4b7b8d213b49f36`;
   - raw UTC window `2026-08-24T14:01:23Z..2026-08-25T14:01:23Z`;
   - `replacement_index=3`, global index cap `3`, and state
     `ISSUED_IMMUTABLE_PRESTART`; and
   - admission law
     `BYTE_IDENTICAL_ACCEPTED_PROPOSAL|ACTIVE_UTC|EXACT_INSTALLED_BYTES|LIVE_CAPACITY`.
2. The same intake names the accepted technical record at
   `temp/handoffs/code_manager_to_root/RCLE_TBCFV_R04_CURRENT_BYTE_INDEX3_LINEAGE_TECHNICAL_ACCEPTANCE_CM_RETURN_20260823.md`.
   This checkout exposes neither named file nor the scratch validator referenced
   by the focused current-byte test seam. `temp/` is ignored local scratch.
3. `empirical_contract.py` defines `MAX_SOURCE_REPAIR_REPLACEMENT_INDEX = 3`.
   `validate_root_lease` rejects an index above 3, requires an immediate
   predecessor with index incremented by one, preserves the stage, certificate,
   binding, proposal, paths, and resources, and requires contiguous windows.
4. `empirical_runner.py:admit_production` validates only the predecessor leases
   supplied by its caller and then the current lease. `read_admission_files` and
   `__main__.py` expose the direct certificate/binding/request/lease/coordinate
   admission path. None consumes a current-authority registry, revocation
   record, or supersession relation.
5. `empirical_artifacts.py` keeps an append-only, contiguous lease-audit chain
   and rejects rollback, gaps, changed origin, source/config/native/coordinate/
   master bindings, or replacement-coordinate creation. Its source-repair
   bridge is not a general current-authority revocation surface.
6. The accepted production inventory is the 24-row
   `empirical_contract.PRODUCTION_SOURCE_LOGICAL_PATHS`. It includes
   `empirical_contract.py`, `empirical_runner.py`, and `__main__.py`. Adding a
   separate module would not change those bytes; gating all existing admission
   routes would.
7. The frozen process/resource fields remain: identity
   `RCLE-TBCFV-R04-FULL-PANEL-20260821-01`, coordinate binding
   `614e4b503a258cff325284376ed8e6f5d65ac713c95a9bb4b8bfd669ad776915`,
   master digest
   `d35b0f3f3ccb33826e2d3e68d73fad086951ac1cdab7e62e0e38be41e1a626a2`,
   zero committed generation, an indivisible twenty-block panel, exact block
   order/RNG law, result blindness, at most four one-thread workers, CPU
   `<=32.0 h`, four-process wall `<=8.861 h`, group RSS `<=2 GiB`, private
   scratch `<=12 GiB`, canonical durable storage `<=1 GiB`, checkpoint read
   `<=4 GiB`, checkpoint write `<=1 GiB`, and GPU count zero.

### External evidence

No provider was contacted. The retained Pro closure is used only as a frozen
repository decision record. It supplies no permission and no technical proof
for a new lease surface.

### Local inference

1. The old index-3 record is not a lifecycle veto, but byte/history
   preservation makes it a mandatory technical parent of any supersession
   proof.
2. A validator that is optional or reachable only through a new wrapper cannot
   establish exactly one launchable authority while the old direct admission
   route remains callable.
3. A valid byte-preserving solution therefore needs a Root-owned sole-entrypoint
   gate outside the accepted production source set, bound to an explicit
   old-to-new current-authority relation. The present evidence names neither
   that gate nor its bytes, path, or authority contract.
4. The word “renewal” in historical request metadata cannot be promoted into a
   generic continuation route. The next surface, if grounded, must be one exact
   object-specific supersession and must leave the repair-lineage index at 3.

### Speculation retained as speculation

Whether Root can recover the complete immutable history bytes, whether a sole
external gate can be frozen without changing accepted production bytes, and
whether a CM can then produce a positive technical reacceptance are unknown.
No efficacy, resource-headroom, execution, or scientific outcome follows from
that uncertainty.

## Candidate CM boundary — not activated

A later engineering request may own only the construction and validation of one
distinct RCLE-TBCFV-r04 current-authority surface. A byte-preserving
implementation candidate would be confined to new direction-scoped files such
as:

- `experiments/candidates/roster_consistent_latent_exploration_tbcfv/current_authority.py`;
- `tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv/test_current_authority.py`; and
- the existing
  `tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv/test_empirical_contract.py`
  only to replace its missing ignored-`temp` validator seam after a tracked
  surface exists.

No member of `PRODUCTION_SOURCE_LOGICAL_PATHS` may change under this candidate
boundary. The missing Root-owned sole-entrypoint gate must have an exact path
and contract before the owned-path set is complete; EM does not invent it.

If activated after the resume condition below, the request must require all of
the following acceptance evidence:

1. Hash the immutable index-3 lease and every predecessor/history record before
   parsing, prove a complete gap-free chain, and leave every byte unchanged.
2. Bind one exact request-only current-authority payload to a distinct proposed
   ID, canonical path, canonical byte SHA-256, and raw UTC window. CM may return
   a proposal and validation receipt; only Operational Root may issue or
   install a lease at an executable lease path.
3. Preserve index 3 as the maximum. Reject index 4, a reset origin, a hidden
   lineage element, lease mutation/reuse/rebinding/extension, and every generic
   renewal route.
4. Bind an explicit old-ID/old-SHA to new-ID/new-SHA supersession relation and
   prove fail closed on a missing, malformed, altered, replayed, or mismatched
   relation.
5. Prove exactly one launchable authority through the Root-owned sole gate.
   Reject both old and new bytes when uniqueness cannot be established; never
   treat expiration alone as supersession.
6. Preserve the complete accepted production source manifest and all identity,
   science revision, coordinate, master, zero-commit frontier, panel/count,
   block-order/RNG, comparator, observable, claim, result-blind, path, and
   resource fields exactly.
7. Keep import, construction, and validation result-blind and side-effect-free.
   They may inspect authority bytes, hashes, canonical paths, timestamps,
   capacity metadata, and file existence only; they may not open coordinates,
   frontier commits, checkpoints, endpoints, aggregates, results, or partial
   values.
8. Prove tamper rejection for every frozen field, incomplete history, dual
   authority, old direct-route use, wrong installed bytes, inactive time, and
   insufficient live capacity. Hand-written deterministic fixtures are the only
   permitted validation data.
9. Return either one exact request/validator/supersession/lineage packet with
   paths and SHAs or one precise incompatibility. A negative return creates no
   fallback, renewal, index increment, or activity authority.

### Resource boundary

Future validation is static, deterministic, and result-blind. It may hash and
parse only the finite authority/history files and exercise hand-written
synthetic lease fixtures. It may not invoke `execute_full_panel`, load a native
scientific host, materialize a coordinate, read a frontier/checkpoint/result,
run a production benchmark, or alter any scientific/resource ceiling. The
accepted full-panel resource envelope is an immutable field to compare, not a
command budget or execution authorization.

### Explicit non-scope

No engineering request is active in this cycle. There is no source or test
change, CM dispatch, worktree, certificate/binding rewrite, lease issuance,
Operator registration or dispatch, experiment/result command, target
materialization, coordinate/master/frontier access, result or partial-value
exposure, index 4, generic renewal, science or claim change, provider operation,
deployment, Git operation, or flight authority.

## Exact technical evidence gap and resume condition

Root may wake this direction for request authoring only after both of these
inputs are durable and exact:

1. **Immutable history input:** the actual canonical bytes for the accepted
   index-3 lease, the accepted CM technical return, the complete predecessor
   lease/history chain, and every path/SHA relation needed to prove that history
   without opening scientific values.
2. **Sole-gate input:** an explicit Root-owned, byte-preserving admission gate
   outside the accepted 24-row production source set, with its exact path,
   owner, caller boundary, and old-to-new fail-closed supersession contract.
   It must make bypass of the current-authority validator impossible without
   changing accepted production bytes.

If Root cannot supply both, the exact disposition is
`CURRENT_AUTHORITY_TECHNICAL_REACCEPTANCE_NOT_YET_CONSTRUCTIBLE`. The direction
remains `ACTIVE` and waiting; the retained Pro-closed panel and accepted bytes
remain intact.

## Workflow disposition

Research state should move to `WAITING`, `actionable=false`, with no engineering
request and exact Root-owned waiting refs to this artifact. `DIRECTION.md`, the
engineering state, and external-review index remain unchanged. No current
external round exists, and no CM, Transport, or Experiment Operator is
activated by this handoff.

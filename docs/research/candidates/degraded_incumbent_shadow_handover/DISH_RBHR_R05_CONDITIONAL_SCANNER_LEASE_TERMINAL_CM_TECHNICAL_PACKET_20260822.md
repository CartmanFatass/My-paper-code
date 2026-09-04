# DISH RBHR r05 conditional scanner-lease terminal CM technical packet — 2026-08-22

```text
document_kind=code_manager_conditional_scanner_terminal_packet
owner=Operational-Root-owned Code Manager /root/dish_r05_preactivity_repair_cm
direction_id=degraded_incumbent_shadow_handover
exact_object_revision=DISH-RBHR-SCIENCE-20260821-05
lease_id=DISH-RBHR-R05-CONDITIONAL-SCANNER-20260822-01
lease_sha256=34de1ce458d25b3828b0dc6696c505ef6d51f1ea72c4a847cc9212e776e6f67a
decision_level_fact=INVALID_PROTOCOL_OR_MEASUREMENT_AT_FROZEN_PER_SLOT_ATTEMPT_CAP
technical_acceptance=CONDITIONAL_SCANNER_PATH_ACCEPTED_AND_EXECUTED_FAIL_CLOSED
accepted_tape_inventory=INCOMPLETE_0_OF_11520
all_six_high_gates=NOT_ESTABLISHED_COMPLETE_INVENTORY_ABSENT
replacement_identity_authorized=false
question_relevant_values_exposed=false
full_panel_executed=false
```

## Decision-level fact

Operational Root issued the exact conditional scanner-only lease. The request
and lease validators passed before materialization. The exact requested command
then created one blinded, nonreplaceable master/identity and the sole scanner
coordinate under that lease.

The frozen native scanner evaluated attempts `0..99999` for the first accepted-
tape slot in literal numeric order. None satisfied that slot's requested
admission stratum. The per-slot `100,000`-attempt cap was therefore exhausted.
The runner atomically sealed
`status=INVALID_PROTOCOL_OR_MEASUREMENT`, `guard_reason=ATTEMPT_CAP_EXHAUSTED`,
`accepted_tape_count=0`, `cumulative_attempts=100000`, and
`cumulative_rejections=100000`. This is the host manifest's registered
generator-failure outcome. It is not a resource-guard trip and is not a
scientific interpretation.

The sole identity digest is
`097d408ccc1b521aae97214ecd500307507f1fc459d3d2f900b1d8c21a72e723`.
The same identity and terminal frontier remain durable. No second or replacement
master, identity, or coordinate was created.

## Exact artifacts

| artifact | path | SHA-256 |
|---|---|---|
| CM Root lease request | `temp/handoffs/code_manager_to_root/DISH_RBHR_R05_CONDITIONAL_SCANNER_ROOT_LEASE_REQUEST_20260822.json` | `72c2559c8207187f1dfc9c711d46a66e6aecca2ad26bd44109af69077489a447` |
| Root-issued lease | `runtime/leases/dish_rbhr_r05_conditional_scanner_lease_20260822.json` | `34de1ce458d25b3828b0dc6696c505ef6d51f1ea72c4a847cc9212e776e6f67a` |
| request validator | `temp/handoffs/code_manager_to_root/validate_dish_rbhr_r05_conditional_scanner_lease_request_20260822.py` | `c953762bcfa99c37786798e8c5a4f6a61ff7bf79fa50cdd3ade0095df33ff1b8` |
| preactivity benchmark | `runtime/benchmarks/dish_rbhr_r05_conditional_scanner_lease_validation_20260822.json` | `a392ea8ae105d9e04a45907933d58423da153ca369087e22e1cf13e60ef03736` |
| exact scanner runner | `temp/handoffs/code_manager_to_root/run_dish_rbhr_r05_conditional_scanner_20260822.py` | `de073d1311c407969ba3b2bbf2f33b395860bc7d77560e8e93cebb18a258b280` |
| durable identity | `runtime/scanner/dish_rbhr_r05_conditional_scanner_20260822_01/identity.json` | `cb015fc6c598d08dfc0aaa4d85924ab0e75524022eca904f6715299091e6a815` |
| sealed same-identity state/frontier | `runtime/scanner/dish_rbhr_r05_conditional_scanner_20260822_01/sealed_scanner_state.json` | `391d8d6b6db02b6739cf918c1d2e35adcd0fda21ad3fa148567952ccd548f8e2` |
| public result-blind terminal receipt | `runtime/scanner/dish_rbhr_r05_conditional_scanner_20260822_01/scanner_receipt.json` | `6c9c765265470dad22b08078ac34ab5adf8f105b182ea3a1d34c7f6e0c7a6e47` |

The blinded `master.bin` exists only inside the exact run root. Its bytes and a
standalone digest are intentionally omitted from this packet.

## Acceptance and resource disposition

Before issuance, the validator established the exact 11,520-slot coordinate
inventory, balanced reflection/initial-owner/qA-owner bits, lowest-attempt
ordering, native ABI v4, eight-thread result-blind batch scanner, same-identity
resume, rejection guard, and all six resource guards. The complete DISH test
directory passed: `46 passed in 49.03s`.

At terminal return, no resource ceiling tripped. The receipt's complete-chain
projection was:

```text
CPU=281.14190042542157 h <= 560 h
wall=45.20129547454374 h <= 110 h
aggregate RSS=2.57534790039062 GiB <= 40 GiB
scratch=0.6630429886281487 GiB <= 120 GiB
durable=0.33045396581292175 GiB <= 16 GiB
total I/O=34.2413698136806 GiB <= 400 GiB
```

Those numerical resource projections pass, but the six high gates are not
established because the accepted-tape inventory is incomplete. No later full-
panel lease can be technically accepted from this receipt.

## Four-layer boundary

```text
observed_fact=The one leased blinded identity exhausted the frozen 100000-attempt cap on the first accepted-tape slot; zero of 11520 accepted tapes were installed; the durable terminal receipt is INVALID_PROTOCOL_OR_MEASUREMENT.
observation_method=Exact Root-issued scanner-only command, native full-host candidate assay, atomic sealed state, and result-blind terminal receipt.
actions_taken=Validated the exact Root request and lease; materialized one master/identity/coordinate under lease; scanned only frozen candidates; atomically sealed the same-identity terminal frontier and receipt.
actions_not_taken=No second/replacement identity or coordinate; no model, optimizer, checkpoint, training, evaluation, fork, bootstrap, branch, result analysis, partial-value exposure, full-panel execution, provider, Git, science, panel, ceiling, allocation, or UAV-classification change.
remaining_unknown=No accepted-tape inventory exists, so complete-panel execution and all six complete-panel gates remain unestablished; scientific meaning and any possible revision are outside CM authority.
causal_hypothesis=The exact frozen generator/admission law produced no qualifying candidate within the registered cap for its first requested slot; CM makes no scientific causal interpretation.
applies_to=The sole DISH-RBHR-SCIENCE-20260821-05 conditional scanner identity and accepted-tape frontier only.
does_not_imply=Replacement attempt, permission to regenerate identity, panel shrink, changed admission law, scientific result, direction retirement, allocation change, or authority for full-panel activity.
local_action_fence=The terminal scanner state must not be resumed past the cap, reset, deleted, replaced, or used to create another master/identity/coordinate; no full-panel activity may start from the incomplete inventory.
scientific_stage_continuation=Portfolio still owns interpretation of the registered INVALID_PROTOCOL_OR_MEASUREMENT generator failure and any science-bearing response; CM has no unchanged-science continuation that can create a legal complete inventory.
continuation_owner=Operational Root for lease closure and exact cross-root relay; same-direction Portfolio EM for scientific interpretation or revision; same DISH CM only for a later exact unchanged-science technical request that preserves this identity and terminal fact.
root_decision_class=Exact cross-root science-bearing incompatibility relay and lease closure; no resource expansion or replacement identity is technically legal under the current object.
smallest_next_action=Operational Root relays this exact CM packet and receipt to Portfolio and records the conditional scanner lease as terminal/consumed without issuing a replacement.
```

# VSP-06 MSSR D0 exact-revision technical reconciliation

```text
assignment_id=rs_c2_vsp06_d0_reconciliation_20260809_28d9758
owner_role=code_project_manager
owner_mode=treatment
evidence_level=A
technical_disposition=ACCEPTED_BOUNDED_PACKAGE
joint_contract_terminal=CONTRACT_NOT_CLOSED
scientific_authority=none
```

## Conclusion

The package at input revision `1236cdc096fe913d7854892275284c652d7df00b` is technically accepted as bounded A-only evidence. The old `CONTRACT_NOT_CLOSED` entry and the later registered-source objects are not same-revision contradictions once their revision and scope are made explicit: the old entry is a historical active-surface finding bound to `c628683ae04e102620246e440b0e8193955f1e3c`, while the later objects establish narrower component existence. The accepted evidence does not close the joint production MSSR contract.

This CPM acceptance does not qualify as a Scheduler C-cycle event.

## Revision relation

- Historical comparison anchor: `c628683ae04e102620246e440b0e8193955f1e3c`.
- Inspected package revision: `1236cdc096fe913d7854892275284c652d7df00b`.
- The historical anchor is an ancestor of the inspected package revision.
- All eight assignment-named VSP-06 source, test, and index paths are absent at the historical anchor.
- The historical certificate and index first appear at `773357410958a76dd50dd3d7ef98961b333d7e42`.
- The three component object implementations/tests first coexist at `75174d98b9f499ec91b7da25095f162f4ba6174e`: the fixed synthetic S/P/F manifest was already present, and this revision added the registered P source and opt-in pre-recurrence action head.
- The registered-source terminal is narrowed to `MSSR_P_REGISTERED_SOURCE_PRESENT` at `61ba29f39a20c95c526b530f3a19fc0154283e13`.
- The current-source coupling witness receives its bounded temporal interpretation at `dc836faca4507071283cec25752196c64ae1a85c`.
- The publication commit containing this record is the accepted evidence revision; its exact commit is supplied by the assignment-specific Git ref and native CPM result.

## Per-object findings

| Object | Finding | Exact evidence | Limit |
|---|---|---|---|
| Selective S/P/F partition | **Present in the fixed rational synthetic unit; absent as a registered production partition.** | `preaction_closure_certificate.py::frozen_manifest`, `validate_manifest`; `test_preaction_closure_certificate.py::test_manifest_is_complete_nonoverlapping_and_explicit` | The manifest proves a synthetic partition and descendant closure only. It is not wired to a production action path. |
| Authenticated support-native historical P | **Present as a registered source/carrier; insufficient for matched support.** | `support_native_p_reachability.py::owner_private_state_inventory`, `registered_partner_transition`; `test_support_native_p_objects.py::test_partner_history_is_frozen_and_provenance_bound`, `test_partner_transition_writes_genuine_cross_member_p` | Provenance-bound owner-private history exists, but no two legal histories are shown at one byte-identical current non-P context with different retained P. |
| Action-before-recurrence first logits | **Present as an opt-in feasible surface.** | `support_native_p_reachability.py::preaction_ordering`; `test_support_native_p_objects.py::test_first_logits_is_genuinely_pre_recurrence`, `test_first_logits_reads_historical_p` | The default action path remains post-recurrence; no end-to-end production route jointly binds this surface to a selective S/P/F partition. |
| Matched-support/current-source relation | **Present only as current-source coupling and carrier retention; insufficient for historical matched-support reachability.** | `matched_support_reachability.py::carrier_retains_history`, `single_partner_variation_moves_owner_context`; corresponding focused tests | The measured partner-observation variation is a current-source/model-domain object, not a legal-history reconvergence witness. |

The exact missing engineering object is one production-integrated selective S/P/F partition bound on the same registered path to the provenance-authenticated historical P carrier and the pre-recurrence first-logit action surface, together with a focused legal-history matched-support witness. This identifies an engineering gap only; it does not select or authorize a scientific design.

## Focused receipts

Executed with `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, zero training and zero hypothetical transitions:

- The four assignment-named focused test files: `54 passed`.
- `preaction_closure_certificate.py`: `P_PREACTION_RESIDUAL_PATH_EXISTS|GATE_EXACTLY_FACTORIZED|CONTRACT_NOT_CLOSED`.
- `python -m experiments.candidates.vsp_06_mssr.support_native_p_reachability`: `MSSR_P_REGISTERED_SOURCE_PRESENT`; all checks passed.
- `python -m experiments.candidates.vsp_06_mssr.matched_support_reachability`: `MSSR_CURRENT_SOURCE_SINGLE_PARTNER_COUPLING_WITNESS`; all checks passed.

The two runtime-backed proof modules require package-module invocation so the repository root is importable. Direct file invocation does not reach proof execution because `ha_ctse_process` is not on `sys.path`; this is an invocation-interface limit, not evidence for or against the measured objects.

## Public source, test, index, and result locators

- Source: `experiments/candidates/vsp_06_mssr/preaction_closure_certificate.py`
- Source: `experiments/candidates/vsp_06_mssr/support_native_p_reachability.py`
- Source: `experiments/candidates/vsp_06_mssr/matched_support_reachability.py`
- Tests: `tests/experiments/candidates/vsp_06_mssr/test_preaction_closure_certificate.py`
- Tests: `tests/experiments/candidates/vsp_06_mssr/test_support_native_p_reachability.py`
- Tests: `tests/experiments/candidates/vsp_06_mssr/test_support_native_p_objects.py`
- Tests: `tests/experiments/candidates/vsp_06_mssr/test_matched_support_reachability.py`
- Index: `docs/research/candidates/vsp_06_mssr/CODE_SCIENCE_INDEX.md`
- Result/evidence record: `docs/research/candidates/vsp_06_mssr/REVISION_RECONCILIATION.md`

## Limits

This acceptance establishes only that the named code, tests, exact-revision history, and bounded outputs are mutually consistent under the per-object readings above. It performs no B run, training, rollout, KEEP-versus-current decision, hidden closure inference, broad production scan, or scientific successor selection. It does not establish value, semantic memory, partner transport, return, deployment, matched-support reachability, or the joint production MSSR contract.

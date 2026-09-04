# DISH RBHR r05 post-recovery fresh first-binding embedding and hash audit

```text
document_kind=direction_post_recovery_provider_request_definition_embedding_hash_audit
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-05
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
science_object_changed=false
r06_created=false
hash_algorithm=SHA-256
byte_definition=exact_file_bytes
encoding=UTF-8_no_BOM
line_endings=LF
tuple_release_state=UNRELEASED_DEFINITION_ONLY
requester_partition_created=false
provider_operation_created=false
provider_operation_authorized=false
runtime_reload_authorized=false
provider_action=false
science_activity=false
```

## Exact frozen sources and owner artifacts

Candidate paths below are relative to
`docs/research/candidates/degraded_incumbent_shadow_handover/`.

| artifact | SHA-256 | bytes | lines |
|---|---|---:|---:|
| `DISH_RBHR_R05_SCIENCE_CARD_20260821.md` | `68db90000d04eca718c7077860cdb77b4e04b1f579978b387cc4983cc5255067` | 22,239 | 427 |
| `DISH_RBHR_R05_HOST_GENERATOR_AND_RNG_MANIFEST_20260821.md` | `b4b3f9f0479c3e84489ca8b09c9193b4cce26db067a0a604c322784991ef729d` | 19,381 | 420 |
| `DISH_RBHR_R05_TOTAL_RNG_ALLOCATION_TABLE_20260821.md` | `3f0f3438f9913f57e997d60c850ddd2563da958d8bd0df99490b80d96f69bbb5` | 10,117 | 204 |
| `DISH_RBHR_R05_PAYLOAD_SERVICE_TICK_AND_COST_RECURRENCE_20260821.md` | `5e10d62d74500a1bfad3f81df8236c6b63615cd2abd198be9eb29d79957dd871` | 14,711 | 335 |
| `DISH_RBHR_R05_CONTROLLER_TREATMENT_COMPARATORS_AND_CERTIFICATE_20260821.md` | `3b69088ce5829261db6f4453c980548727e377b53d9403d439bb7cca66a35b30` | 33,401 | 673 |
| `DISH_RBHR_R05_TRAINING_AND_POPULATION_MANIFEST_20260821.md` | `bb451c4c9f13a972c79169692d87592687b9113eb65caa0ec97b4d12dd0b1a3b` | 16,086 | 329 |
| `DISH_RBHR_R05_OPPORTUNITY_FORK_ENDPOINT_INFERENCE_AND_BRANCH_MANIFEST_20260821.md` | `a20401b355763ce60791d3c1a75b98f0f5c07c88119fc982ea98b85b52141cad` | 21,305 | 492 |
| `DISH_RBHR_R05_13_DEFECT_RESOLUTION_MAP_20260821.md` | `fb9048b42f85de4d3df103d590d8abad03e34c0335cf93f303d4a48939149bfc` | 8,834 | 147 |
| `DISH_RBHR_R05_CHATGPT_PRO_STANDALONE_FIRST_BINDING_CLOSURE_QUESTION_20260821.md` | `edabebd4ebdf40dfbdf992fcb94628123f33876468ca6ba13b27a38d4867be41` | 149,371 | 3,096 |
| `DISH_RBHR_R05_POST_TUPLE_RECOVERY_EM_INTAKE_20260822.md` | `56d0ce0707ad472e400efacc59c52cb26e914910e1f26a34025b652d102924d6` | 6,517 | 139 |
| `DISH_RBHR_R05_CHATGPT_PRO_POST_RECOVERY_FRESH_FIRST_BINDING_AUTHORIZATION_REQUEST_20260822.md` | `6f49368e98b1c288686860b1bbb7f7def6c6d28718d7fabcdd850099ec18d9c1` | 7,291 | 119 |
| `DISH_RBHR_R05_POST_RECOVERY_PORTFOLIO_CANDIDATE_DECISION_20260822.md` | `3ea9e32dcd28a53b29bd9d9f0027899f9d65a439913f9b541c298a712293e936` | 5,939 | 116 |

The eight frozen scientific-source hashes exactly match the earlier r05
artifact manifest and standalone-question audit. Every listed file has final
LF, no BOM and no CR. The scientific composite and provider-visible question
are byte-unchanged; only local post-recovery intake, tuple definition and
decision-candidate artifacts are new.

## Exact embedding audit

The audit compared decoded UTF-8 source content by ordinal substring equality,
not normalized Markdown rendering. The unchanged standalone question contains
each source once and only once, with one exact named BEGIN marker and one exact
END marker:

| source | exact content copies | BEGIN markers | END markers |
|---|---:|---:|---:|
| r05 science card | 1 | 1 | 1 |
| host/generator/RNG manifest | 1 | 1 | 1 |
| total RNG allocation | 1 | 1 | 1 |
| payload/service/cost recurrence | 1 | 1 | 1 |
| controller/treatment/certificate | 1 | 1 | 1 |
| training/population manifest | 1 | 1 | 1 |
| opportunity/fork/inference/branch manifest | 1 | 1 | 1 |
| thirteen-defect resolution map | 1 | 1 | 1 |

The fresh tuple changes no provider-visible framing or scientific bytes. The
question remains a standalone complete r05 packet rather than a continuation,
recovery narrative or request to inspect repository/runtime evidence.

## Provider-visible exclusion audit

The exact standalone question contains zero occurrences of:

- local absolute workspace paths or `results.json`;
- recovered operation IDs `a235b271-fbbe-4e46-923d-5f65898d59e7` and
  `1d32dc16-d1ed-4081-965b-f559386e858d`;
- old no-resend operation `3d049425-9666-4dce-9764-7ba319231cf1`;
- the new stable key or new idempotency key;
- `SUBMITTED_UNVERIFIED`, `ZERO_COMMIT_CANCELLED`, runtime-reload or
  stale-inflight language.

It includes no prior answer, inferred disposition, archive, receipt, runtime
request, code review, hash/byte audit or transport wrapper. Scientific SHA-256
references inside the normative RNG/message-integrity laws are unaffected.

## Recovery evidence hash audit

| artifact | SHA-256 | bytes | lines |
|---|---|---:|---:|
| `docs/session/WORKFLOW_RECOVERY_DISH_RBHR_R05_FRESH_FIRST_BINDING_IMMUTABLE_TUPLE_VIOLATION_RESULT_20260822.md` | `26851d0c3fdb581edce78b6cbbb82471107071cd641976b90d519af02d4327c6` | 4,838 | 94 |
| `docs/session/DISH_RBHR_R05_FRESH_FIRST_BINDING_EM_SAFE_PAUSE_HANDOFF_20260821.md` | `fb81cc7eb5be02922fda088ae58cfedbda38f0d7beedc8ff977c0211abc6c345` | 7,362 | 148 |
| `temp/sessions/agentify_transport_operator/independent_research_explorer/dish_rbhr_r05_chatgpt_pro_fresh_first_binding_closure_20260821_01/results.json` | `ec7ae157eb0676b57245f39587971695444b41cd75fb0b6e2a386895ae037683` | 1,052 | 27 |

The recovery result is controlling for the final row dispositions and tab
cleanup. The mechanical archive is controlling only for its durable submitted-
unverified row fields; its earlier pending-close marker is superseded by the
recovery's later native close evidence.

## Fresh unused tuple and absent-partition audit

```text
provider=chatgpt
model=Pro
conversation_url=https://chatgpt.com/
conversation_id=__new__
first_binding=true
stable_key=DISH-RBHR-R05-CHATGPT-PRO-POST-RECOVERY-FRESH-FIRST-BINDING-20260822-01-68c94fa6-9b83-4550-afef-44551b990155
idempotency_key=DISH-RBHR-R05-PRO-POST-RECOVERY-FRESH-FIRST-BINDING-CLOSURE-20260822-01-d7f94f60-f221-4aed-9515-2f4c4f1c90cf
planned_partition=temp/sessions/agentify_transport_operator/independent_research_explorer/dish_rbhr_r05_chatgpt_pro_post_recovery_fresh_first_binding_closure_20260822_01/
planned_partition_exists=false
requester_partition_created=false
provider_operation_created=false
provider_action=false
```

Before any owner artifact named the new tuple, exact documentation and durable
strict-ledger search found zero occurrences of both keys and the planned
partition was absent. Immediately before this audit was written, the keys
appeared only in the held authorization request and EM Portfolio-decision
candidate, remained absent from the strict ledger, and the planned partition
remained absent. This audit is the third owner-artifact occurrence and does not
materialize the partition.

## Runtime and scientific boundary

The new tuple remains held behind three separate facts: an independently
authorized no-provider Agentify application/server reload, direct proof that
the repaired runtime has cleared the stale strict inflight admission, and a
later exact Portfolio release of this tuple. None exists merely because this
audit or request exists.

The strongest alternatives and claim ceiling remain unchanged. If a later
separately authorized operation returns `CLOSED` or `REVISION_REQUIRED`, its
raw response returns to the same-direction EM and Portfolio. Another absent-
response or ambiguous committed terminal authorizes no automatic Pro turn,
continuation, r06, Gemini, CM request, construction or scientific activity.

```text
applies_to=Integrity and non-materialization of the post-recovery fresh r05 tuple definition
does_not_imply=runtime reload authority|stale inflight clearance|provider release|provider operation|mathematical closure|r06|Gemini authority|CM authority|activity
continuation_owner=Dedicated Portfolio Root for the candidate decision; operational authority for any separately relayed reload; same-direction EM for later valid provider intake
root_decision_class=none; exact audit evidence for a held Portfolio decision candidate
```

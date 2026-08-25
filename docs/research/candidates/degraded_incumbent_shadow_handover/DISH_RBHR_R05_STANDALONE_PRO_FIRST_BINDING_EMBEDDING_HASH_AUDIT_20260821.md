# DISH RBHR r05 standalone Pro first-binding embedding and hash audit

```text
document_kind=direction_provider_request_definition_embedding_hash_audit
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-05
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
science_object_changed=false
r06_created=false
hash_algorithm=SHA-256
byte_definition=exact_file_bytes
encoding=UTF-8_no_BOM
line_endings=LF
provider_operation_authorized=false
provider_action=false
science_activity=false
```

## Exact frozen sources and request artifacts

All paths are relative to
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
| `DISH_RBHR_R05_CHATGPT_PRO_FRESH_FIRST_BINDING_AUTHORIZATION_REQUEST_20260821.md` | `ae5d84860b2dc2b75b89853943093a90142477070505d4cd88d194fa5cbb78d2` | 5,930 | 100 |

The first seven source rows and the resolution-map row exactly match the
previously frozen r05 artifact manifest. Each file has final LF, no BOM, no CR
and no byte mutation. The standalone request therefore changes only provider
framing and future operation identity; it does not change science.

## Exact embedding audit

The audit compared decoded UTF-8 source content by ordinal substring equality,
not normalized Markdown rendering. The standalone question contains each
source once and only once, with one exact named BEGIN marker and one exact END
marker:

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

The frozen r05 card and the thirteen-defect map are therefore represented
exactly once, while the other six normative files make the question genuinely
self-contained rather than relying on repository access or an earlier
conversation.

## Provider-visible exclusion audit

The exact standalone question contains zero occurrences of:

- local absolute Windows paths;
- `results.json`, an idempotency key or an operation ID;
- the prior saved conversation ID or prior operation UUID;
- `timeout_waiting_for_response`, `SUBMITTED_UNVERIFIED` or response-receipt
  fields;
- the prior EM anomaly-intake or recovery-adjudication artifact names.

It includes no prior provider answer, inferred prior disposition, runtime
request, code-review request, hash/receipt block or transport wrapper. Its only
scientific SHA-256 references are the unchanged RNG and message-integrity laws
inside the exact normative composite.

## Fresh unused tuple and closed-partition audit

```text
provider=chatgpt
model=Pro
conversation_url=https://chatgpt.com/
conversation_id=__new__
first_binding=true
stable_key=DISH-RBHR-R05-CHATGPT-PRO-FRESH-FIRST-BINDING-20260821-01-f9f56e42-c296-4c08-a29b-e58501edd7bb
idempotency_key=DISH-RBHR-R05-PRO-FRESH-FIRST-BINDING-CLOSURE-20260821-01-76a70bb2-0b51-4389-ad7b-80946582f35b
planned_partition=temp/sessions/agentify_transport_operator/independent_research_explorer/dish_rbhr_r05_chatgpt_pro_fresh_first_binding_closure_20260821_01/
planned_partition_exists=false
requester_partition_created=false
provider_operation_created=false
provider_action=false
```

Before this audit artifact was written, exact workspace search found each new
stable/idempotency key only in the unused authorization request, and the
planned requester partition was absent. This audit does not create that
partition.

## Scientific and stop boundary

The strongest alternatives remain generic standby geometry/redundancy, a
simple-rule substitute, finite-budget FLEX underoptimization, matched-compute
effects, `k` timing/alignment and mask-host artifacts. The claim ceiling remains
finite-budget direct service/tail value in the exact two-UAV host and registered
fixed/held-out/switched-`k` mask packages, with no variable-`N`, arbitrary-`k`,
pure-channel, deployment, safety or flight claim.

If a later separately authorized operation returns `CLOSED` or
`REVISION_REQUIRED`, its raw archive returns to the same-direction EM and
Portfolio. If it instead produces another no-response or ambiguous committed
terminal, no further Pro turn, continuation, r06, Gemini, CM request,
construction or scientific activity is automatic.

# DISH RBHR revision 05 artifact, hash and embedding audit

```text
document_kind=direction_science_artifact_hash_and_embedding_manifest
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-05
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
hash_algorithm=SHA-256
byte_definition=exact_file_bytes
encoding=UTF-8_no_BOM
line_endings=LF
manifest_self_hash_excluded=true
stage=definition-only
accepted_r04_defects_resolved=13
em_local_meaning_completeness_audit=NO_RESIDUAL_SCIENCE_AMBIGUITY_IDENTIFIED
mathematical_closure=false
provider_dispatch=HELD_NOT_AUTHORIZED
science_activity_authorized=false
```

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
| `DISH_RBHR_R05_CHATGPT_PRO_RECLOSURE_QUESTION_20260821.md` | `11ea1516b8afb760413392ab77a70119246271a7da6059926915e05fba03f6af` | 149,423 | 3,097 |
| `DISH_RBHR_R05_GEMINI_INNOVATION_QUESTION_20260821.md` | `126a21c23d508b702fc028d1e9935ef7522cc60135e6d33c147d97effbf2734b` | 139,965 | 2,931 |
| `DISH_RBHR_R05_CHATGPT_PRO_CONTINUATION_AUTHORIZATION_REQUEST_20260821.md` | `178c246a750a70bfbd0d0d869eab93dd30abe1fa5b5eb6d00a19ddccd19e201b` | 5,086 | 86 |

## Packet structure

- The first seven rows are the complete indivisible normative r05 composite.
- The resolution map audits all thirteen accepted r04 defects against those
  exact normative files; it is not an eighth treatment-default source.
- The Pro question contains the seven normative artifacts plus the resolution
  map between exact named BEGIN/END markers.
- The Gemini question independently contains only the seven normative
  artifacts. It contains no resolution map, Pro response, Pro disposition,
  response archive or simulated external consensus.
- The authorization request freezes one future same-conversation tuple but is
  not authorization and creates no requester partition.

## Exact embedding audit

The audit compared decoded UTF-8 file content by ordinal substring equality,
not normalized Markdown rendering. Every listed source has a final LF, no BOM
and no CRLF.

| embedded source | exact copies in Pro | Pro BEGIN/END | exact copies in Gemini | Gemini BEGIN/END |
|---|---:|---:|---:|---:|
| science card | 1 | 1 / 1 | 1 | 1 / 1 |
| host/generator/RNG manifest | 1 | 1 / 1 | 1 | 1 / 1 |
| total RNG allocation | 1 | 1 / 1 | 1 | 1 / 1 |
| payload/service/cost recurrence | 1 | 1 / 1 | 1 | 1 / 1 |
| controller/treatment/certificate | 1 | 1 / 1 | 1 | 1 / 1 |
| training/population manifest | 1 | 1 / 1 | 1 | 1 / 1 |
| opportunity/fork/inference/branch manifest | 1 | 1 / 1 | 1 | 1 / 1 |
| thirteen-defect resolution map | 1 | 1 / 1 | 0 | 0 / 0 |

Both provider questions were also scanned for local absolute Windows paths,
`results.json`, idempotency keys and operation IDs; every count is zero. The
Gemini question contains neither the resolution-map name nor the Pro prompt's
prior-disposition/machine-header text. Repository-relative artifact names,
scientific uses of SHA-256 inside the frozen RNG/integrity law, and the
normative requirement for future same-conversation closure are part of the
scientific composite and do not disclose a current provider answer.

## Future tuple and hold

Stable key `DISH-RBHR-R02-CHATGPT-PRO-VISIBLE-PRO-20260821-03` remains bound to
saved conversation `6a88ab31-b02c-83e8-8c44-acfc8c00bc6a`. The new unused
idempotency key is
`DISH-RBHR-R05-PRO-RECLOSURE-CONTINUATION-20260821-01-b62579e1-faff-4d7c-9dc0-d5edd0105fa3`.
Its planned requester partition
`temp/sessions/agentify_transport_operator/independent_research_explorer/dish_rbhr_r05_chatgpt_pro_reclosure_20260821_01/`
was absent at freeze and remains unmaterialized. The authorization request's
question SHA and byte count agree with the Pro question row above.

No Pro or Gemini provider action is authorized. Gemini remains blind and held
until a future Pro `CLOSED` intake, a separately authorized release and the
required app-lifetime-safe repaired Gemini runtime activation. The manifest
excludes its own self-hash; mutation of any listed source invalidates its row
and the corresponding embedded question snapshot until deliberately refrozen.

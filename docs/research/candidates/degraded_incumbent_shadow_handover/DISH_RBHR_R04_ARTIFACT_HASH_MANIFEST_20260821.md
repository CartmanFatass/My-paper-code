# DISH RBHR revision 04 artifact and hash manifest

```text
document_kind=direction_science_artifact_hash_manifest
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-04
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
hash_algorithm=SHA-256
byte_definition=exact_file_bytes
manifest_self_hash_excluded=true
stage=definition-only
accepted_r03_defects_resolved=20
em_local_meaning_completeness_audit=NO_RESIDUAL_SCIENCE_AMBIGUITY_IDENTIFIED
mathematical_closure=false
provider_dispatch=HELD
science_activity_authorized=false
```

All paths are relative to
`docs/research/candidates/degraded_incumbent_shadow_handover/`.

| artifact | SHA-256 | bytes | lines |
|---|---|---:|---:|
| `DISH_RBHR_R04_SCIENCE_CARD_20260821.md` | `a9c26ad8496a11e2294b6286648e37e7c6c07a0a705a647650228274e0752aae` | 19,982 | 393 |
| `DISH_RBHR_R04_HOST_GENERATOR_AND_RNG_MANIFEST_20260821.md` | `7a64db806882a09165ff7c9c7716e3d4d64fe3b27606381d8a0cfa41f7e3254e` | 17,581 | 389 |
| `DISH_RBHR_R04_TOTAL_RNG_ALLOCATION_TABLE_20260821.md` | `5f7ca71bbe724b1c5e2a2a98279fa402eb8faa1595834b86d45c3c09210898a0` | 8,891 | 169 |
| `DISH_RBHR_R04_PAYLOAD_SERVICE_TICK_AND_COST_RECURRENCE_20260821.md` | `78e68dde6e94c6c7a4277c95776039157a824387f1af4b18ed8ea6775b99964c` | 14,130 | 324 |
| `DISH_RBHR_R04_CONTROLLER_TREATMENT_COMPARATORS_AND_CERTIFICATE_20260821.md` | `8bfce2221c16d38b390c3dd71ded9f35c9595b312ebf94e204ddbdfc615e3a6b` | 29,681 | 595 |
| `DISH_RBHR_R04_TRAINING_AND_POPULATION_MANIFEST_20260821.md` | `3dd1a2b4b28eed864af999a5eff585ad357a9f2211213c396f1a6f26b1aba009` | 12,700 | 274 |
| `DISH_RBHR_R04_OPPORTUNITY_FORK_ENDPOINT_INFERENCE_AND_BRANCH_MANIFEST_20260821.md` | `3f8540ff5825adad12a6aa9e046b392dfa152e102b1eed06e6d1cb8e2aa31621` | 18,493 | 427 |
| `DISH_RBHR_R04_20_DEFECT_RESOLUTION_MAP_20260821.md` | `da5feaddd2d49d3f2e23f3f23b26a46100b447d710f3a216b5594bac1fb3e773` | 10,239 | 175 |
| `DISH_RBHR_R04_CHATGPT_PRO_RECLOSURE_QUESTION_20260821.md` | `795a84fddb38dbbbd769df9e7f6091043dc3663ba5d8bc0ae5780653c34dcb3c` | 135,014 | 2,817 |
| `DISH_RBHR_R04_GEMINI_INNOVATION_QUESTION_20260821.md` | `f63f2de8a63ee87bf5c7d14a303b340222a837a5ac46cb9ffebbd9376d81f0ad` | 124,184 | 2,623 |
| `DISH_RBHR_R04_CHATGPT_PRO_CONTINUATION_AUTHORIZATION_REQUEST_20260821.md` | `1870c3a8749063d3a73d72c59d7c919abc1477186d1739953ffb2b0a4622c13b` | 5,167 | 88 |

## Packet structure and verification boundary

- The first seven rows are the complete indivisible normative r04 composite.
- The resolution map audits all twenty accepted r03 defects against those
  exact normative sources; it is not an eighth source of treatment defaults.
- The Pro question contains byte-exact textual copies of all seven normative
  artifacts plus the resolution map, delimited by named BEGIN/END markers.
- The Gemini question independently contains byte-exact textual copies of only
  the seven normative artifacts. It contains no Pro response, disposition,
  defect map or simulated external consensus.
- The continuation request freezes one future same-conversation tuple only.
  Stable key
  `DISH-RBHR-R02-CHATGPT-PRO-VISIBLE-PRO-20260821-03` remains bound to saved
  conversation `6a88ab31-b02c-83e8-8c44-acfc8c00bc6a`; new idempotency key
  `DISH-RBHR-R04-PRO-RECLOSURE-CONTINUATION-20260821-01-214b00b4-a015-4b59-962c-0e2b2f1057c7`
  is unused. Its planned requester partition does not exist.
- Provider dispatch is held until Portfolio explicitly confirms the VQFP r03
  Gemini same-cause recovery is durably terminal and shared Agentify capacity
  is released, then separately authorizes the exact tuple. No provider action
  is implied by this freeze.

The manifest deliberately excludes its own self-hash. Any mutation to a listed
artifact invalidates its row and, for a normative source, invalidates both
embedded provider-question snapshots until deliberately refrozen.


# DISH RBHR revision 03 artifact and hash manifest

```text
document_kind=direction_science_artifact_hash_manifest
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-03
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
hash_algorithm=SHA-256
byte_definition=exact_file_bytes
manifest_self_hash_excluded=true
stage=definition-only
science_activity_authorized=false
```

All paths are relative to
`docs/research/candidates/degraded_incumbent_shadow_handover/`.

| artifact | SHA-256 | bytes | lines |
|---|---|---:|---:|
| `DISH_RBHR_R03_SCIENCE_CARD_20260821.md` | `0c44196b8545c8718291d06f2e1137e018fdfe3cb618db548be48f4f99d7fec3` | 18,619 | 373 |
| `DISH_RBHR_R03_HOST_GENERATOR_AND_RNG_MANIFEST_20260821.md` | `1d5d5a66b69ac9ed4ba6d4eb645b6c484c06400a2f2c836daf291d91124364cd` | 14,632 | 311 |
| `DISH_RBHR_R03_PAYLOAD_SERVICE_AND_COST_RECURRENCE_20260821.md` | `0eb53ca56d4dfe27c3f9209a8bae7f365ff253b6848c50a3875ceda46b251885` | 10,628 | 267 |
| `DISH_RBHR_R03_TREATMENT_COMPARATORS_AND_CERTIFICATE_20260821.md` | `ce8fa9c58b0148922273e4589f62b1e55f6e02ea0fa8339074c912e8fecdabe6` | 12,089 | 274 |
| `DISH_RBHR_R03_TRAINING_AND_POPULATION_MANIFEST_20260821.md` | `ed3ea828fb5f95695be526b683cf8dad7a7c1e91e0a01df24168604b19cb72a4` | 9,782 | 227 |
| `DISH_RBHR_R03_OPPORTUNITY_FORK_ENDPOINT_INFERENCE_AND_BRANCH_MANIFEST_20260821.md` | `57522e211d2ddfc54ce2fe5f9b90e74db0f8b31a5864a9cddc09537f7fa50cd3` | 15,695 | 377 |
| `DISH_RBHR_R03_21_DEFECT_RESOLUTION_MAP_20260821.md` | `89f7da92318a780e560dce552edc695f76103133fefdf5a9ba4b78ef547a6c34` | 8,515 | 152 |
| `DISH_RBHR_R03_CHATGPT_PRO_RECLOSURE_QUESTION_20260821.md` | `f21fd18e349c38a5b443fa2ae1b8a657f71bfbf3c4a3357c3b5be2d07d3aef55` | 92,998 | 2,060 |
| `DISH_RBHR_R03_GEMINI_INNOVATION_QUESTION_20260821.md` | `445ee3941125948572b77fc612748a8c237b449bbf542ff88fd65a07a80a2e26` | 84,018 | 1,890 |
| `DISH_RBHR_R03_CHATGPT_PRO_CONTINUATION_AUTHORIZATION_REQUEST_20260821.md` | `ba3dd7ac788248bf231bad896ca51561f83b73a2c911eb12fd6a5f3b7417272e` | 4,719 | 82 |

## Packet structure

- The first six rows are the indivisible normative r03 composite.
- The resolution map audits all 21 accepted r02 defects against that composite.
- The Pro question contains byte-exact textual copies of all six normative
  artifacts plus the resolution map, delimited by named BEGIN/END markers.
- The Gemini question independently contains byte-exact textual copies of only
  the six normative artifacts and contains no prior external-review answer.
- The continuation request freezes a future same-conversation tuple only; its
  requester partition does not exist and no provider operation is authorized.

The manifest deliberately excludes its own self-hash. Any mutation to a listed
artifact invalidates its row and, for a normative source, also invalidates both
embedded provider-question snapshots until they are deliberately refrozen.

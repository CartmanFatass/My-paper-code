# VQFP aggregate-witness alignment R01 Pro Innovator transport request — 2026-08-30

## Request identity and state

```text
document_kind=direction_external_review_transport_request
assignment_id=vqfp-witness-alignment-r01-pro-innovator-transport-g4
requester=EM-voronoi_quadrature_field_policy
requester_generation=4
return_route=Root
provider=chatgpt
mode=INNOVATOR
review_stage=pro_innovator
workflow_version=hmasd-external-review-v1
round_id=e47f1643da200939b2dc
request_state=PREPARED_UNSENT
agentify_operation_id=null
agentify_operation_status=NOT_CREATED
commitment_state=UNSENT_NO_OPERATION
provider_conversation_state=NEW_NOT_CREATED
assignment_send_count=0
operation_budget=1
```

This artifact freezes one send-capable request for Root-mediated singleton `BrowserTransport`. It does not invoke Agentify, create an Agentify operation or provider conversation, insert a prompt, create an archive, or send a provider turn. The future Agentify operation ID is intentionally `null`: Agentify generates it atomically only if Root later dispatches this exact request. The exact immutable operation intent is bound now by the stable key, idempotency key, prompt identity, response path, and request fingerprint below.

## Objective and decision relevance

Obtain exactly one independent ChatGPT Pro Innovator analytical product for the fresh object `VQFP-AGGREGATE-WITNESS-ALIGNMENT-R01`. The product may change only the EM's definition-level judgment about whether the existing aggregate and separate-witness grammar is sufficient for its narrow association-contribution interpretation. It cannot decide ladder polarity, authorize enumeration or engineering, or change Portfolio lifecycle.

## Frozen scientific identities

```text
direction_id=voronoi_quadrature_field_policy
cycle_id=2026-08-30.19-vqfp-aggregate-witness-alignment-r01
cycle_boundary=FRESH_MATERIAL_CYCLE
object=VQFP-AGGREGATE-WITNESS-ALIGNMENT-R01
question_path=docs/research/candidates/voronoi_quadrature_field_policy/VQFP_AGGREGATE_WITNESS_ALIGNMENT_R01_SCIENCE_CARD_20260830.md
question_sha256=2932932eedd72305c3817065a1d367e304ec025649d4554a5a357f1735fe4368
evidence_path=docs/research/candidates/voronoi_quadrature_field_policy/VQFP_AGGREGATE_WITNESS_ALIGNMENT_R01_EVIDENCE_SET_20260830.md
evidence_sha256=89bd737bfc9e6b4e6ebcfaea5abe4911ff60cc1b11e9997997ef02ca15400c2c
round_id=e47f1643da200939b2dc
canonical_round_derivation=SHA256(direction_id LF question_sha256 LF evidence_sha256 LF workflow_version) first 20 hex
historical_round_excluded=9f48f4a6bcace75fddeb
historical_observed_round_excluded=211d583818335dd612c7
```

The round ID was derived with `scripts/hmasd_external_review.py round-id` from the exact tuple above. It is not the historical canonical round. The recovered historical archive remains only in the v3 `historical_archives` collection and is not a provider fact, prompt input, operation, resend authority, or destination for this request.

## Exact prompt identity

```text
prompt_path=docs/external-review/directions/voronoi_quadrature_field_policy/e47f1643da200939b2dc/pro_innovator/PRO_INNOVATOR_PROMPT.md
transport_prompt_path=/home/fires/hmasd/docs/external-review/directions/voronoi_quadrature_field_policy/e47f1643da200939b2dc/pro_innovator/PRO_INNOVATOR_PROMPT.md
prompt_sha256=a9e5dbc9537ca5853598740742c02f980e2aabeb15656d1535d762b3ad403019
prompt_size_bytes=7562
prompt_utf8=true
prompt_bom=false
prompt_crlf_count=0
prompt_lf_count=65
```

`BrowserTransport` must fingerprint and reread the exact integrated prompt path before strict send. It must not compose, summarize, wrap, append, translate, or otherwise alter these bytes.

## Immutable strict Agentify request

```text
stableKey=vqfp-g4-witness-alignment-r01-pro-innovator
provider=chatgpt
model=GPT-5.6 Pro
conversationUrl=https://chatgpt.com/
conversationId=__new__
idempotencyKey=vqfp-g4-witness-alignment-r01-pro-innovator-30713e8a-6f45-4c35-bfcb-87276cb8c646
promptSha256=a9e5dbc9537ca5853598740742c02f980e2aabeb15656d1535d762b3ad403019
responsePath=/home/fires/hmasd/docs/external-review/directions/voronoi_quadrature_field_policy/e47f1643da200939b2dc/pro_innovator/chatgpt/NATURAL_COMPLETION_ARCHIVE.json
timeoutMs=2700000
firstBinding=true
geminiBootstrap=false
geminiBootstrapContinuation=false
bootstrapNonScientific=false
verifyExisting=false
diagnoseExisting=false
existingTabId=null
request_fingerprint=47f9d22aed9c90006bd544616215df3be96782d79c4fed56c2320993c6893036
```

The fingerprint is the SHA-256 of Agentify's normalized JSON field order and values:

```json
{"stableKey":"vqfp-g4-witness-alignment-r01-pro-innovator","provider":"chatgpt","model":"GPT-5.6 Pro","conversationUrl":"https://chatgpt.com/","conversationId":"__new__","idempotencyKey":"vqfp-g4-witness-alignment-r01-pro-innovator-30713e8a-6f45-4c35-bfcb-87276cb8c646","promptSha256":"a9e5dbc9537ca5853598740742c02f980e2aabeb15656d1535d762b3ad403019","responsePath":"/home/fires/hmasd/docs/external-review/directions/voronoi_quadrature_field_policy/e47f1643da200939b2dc/pro_innovator/chatgpt/NATURAL_COMPLETION_ARCHIVE.json","timeoutMs":2700000,"firstBinding":true,"geminiBootstrap":false,"geminiBootstrapContinuation":false,"bootstrapNonScientific":false}
```

Root must reject a changed field, prompt hash, model label, conversation mode, idempotency key, response path, timeout, or fingerprint. Root must also establish that the exact idempotency key has no prior Agentify operation before authorizing a send. This EM assignment did not inspect or mutate the Agentify ledger.

## Stage-owned destination

```text
archive_path=docs/external-review/directions/voronoi_quadrature_field_policy/e47f1643da200939b2dc/pro_innovator/chatgpt/NATURAL_COMPLETION_ARCHIVE.json
archive_absolute_path=/home/fires/hmasd/docs/external-review/directions/voronoi_quadrature_field_policy/e47f1643da200939b2dc/pro_innovator/chatgpt/NATURAL_COMPLETION_ARCHIVE.json
archive_state=ABSENT_EXPECTED_UNTIL_NATURAL_COMPLETION
archive_sha256=null
```

This is the required future stage-owned path. It is disjoint from the later `pro_convergence` path and from every legacy direction/round/provider archive. This request does not create, import, copy, move, rewrite, or validate archive bytes.

## Root-to-transport assignment contract

### Inputs

Root supplies this request, the exact prompt ref, the question/evidence identities, the active-round index ref, and the integrated checkpoint. The requester is `EM-voronoi_quadrature_field_policy`, and transport returns only to Root.

### Authorized effect

At most one strict `agentify_review_query` send-capable attempt may use the exact immutable request after Root validation. Only the singleton `BrowserTransport` may perform the provider operation. No ordinary send surface, operator Enter, Retry, Continue, Regenerate, alternate model, alternate provider, alternate conversation, or second operation is authorized.

### Acceptance

Completion requires the exact provider and visible model, one provider-visible user turn byte-equal to the prompt, its causal natural assistant completion, immutable stage-owned archive bytes, exact operation/idempotency/fingerprint/commitment facts, response and archive hashes, and Root validation under `scripts/hmasd_external_review.py`. Provider completion is evidence availability, not accepted science.

### Observation bound and reentry

The send-capable operation budget is one and the natural-completion wait bound is 2,700,000 ms. `SENT_WAITING`, `COMMITMENT_UNKNOWN`, and `SENT_UNREADABLE` are same-operation observe-only states and never resend. `ZERO_SEND_FAILED` proves only zero send for that exact operation and creates no replacement authority. A material transport fact returns through Root to this same EM cycle for scientific disposition. Pro Convergence remains unauthored, has no prompt, operation, commitment, provider fact, or archive, and may be frozen only after Innovator disposition and updated durable local synthesis.

## Scientific branches and protected non-goals

A valid sufficiency, adverse, ambiguous, or `NO_MATERIAL_INSIGHT` product is interpreted only by EM under the frozen claim ceiling. Invalid scientific input and technical transport failure remain separate. Do not enumerate the ladder, run code or an experiment, dispatch CM, modify scientific/numerical/RNG/checkpoint/bit-identity semantics, alter Portfolio/registry/lifecycle authority, mutate historical archives, or treat an archive, review, test, hash, or transport receipt as approval.

## Exact next action

```text
next_action.owner=TRANSPORT
next_action.kind=SUBMIT_FROZEN_PRO_INNOVATOR
next_action.input=request artifact plus exact prompt/question/evidence/index/checkpoint refs
return=common_v1 transport fact to Root, then same-cycle EM disposition
```

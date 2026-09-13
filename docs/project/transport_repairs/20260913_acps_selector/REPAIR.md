# ACPS canonical model selector repair

Root assigns same-request engineering repair for ACPS Q, with no replacement operation,
prompt/hash/tab change or external Send by the engineering DM. ACPS remains the author;
its native Transport retains the original continuation route. This is separate from MGTAP
science, compute and cost.

## L0 and protected boundary

Deliverable: recover canonical `GPT-6 Astra` selection when the current UI uses `Latest`,
without changing immutable operation arguments. Owned change: the strict selector in
`C:/Projects/agentify-desktop/chatgpt-controller.mjs`; regression fixtures, this record and
the minimal patch are published from `C:/Projects/HMASD-worktrees/dm-n5-continue-20260904`.
Preserve all pre-existing Agentify dirty edits. The source patch is anchored by full before/
after hashes in [REPAIR_RECEIPT.json](REPAIR_RECEIPT.json); it does not commit unrelated
Agentify work. Accept through focused real-module tests and independent Astra/high review.
Budget/stop: no scientific invocation, no live Send, no app-wide reload that loses an owned
tab or interrupts another request. Stop dependent dispatch on a remaining runtime-loading
conflict; continue the exact request only after its repaired preflight passes.

## Failure and minimal repair

Frozen HANDOFF `aaf0b977de1f547794ac0a540480be9778f1524e`, TASK
`c32e6e241b9fa6942482f554524659d943fa8163`; request
`2026-09-13-acps-post-b02-use-01`, stable key
`em:actuator_conditioned_partial_sharing:convergence`. Operation
`b7f00c5e-8e41-4ad1-805d-65cebf1ec763` remains exactly unchanged, including
`productModel="GPT-6 Astra"`, `sendAttempted=false` and null provider IDs. Its prompt
SHA is `bee9b6e037f7b68e37143d152dd004cfefd10a9904d5c13bb648750ee9a2ab84`.
Dedicated tab `4cd5b361-b097-48cc-95cc-a10dfcdf5ddf` remains open and bound.

The actual composer displays `6Pro`; its selected product row is `Latest`, with only
Sol/5.5 alternatives. The prior controller compared the row label literally to Astra.
Changing the frozen model argument to Latest then correctly produced an idempotency
conflict. The failed attempts never reached Send. One current UI sample plus the existing
operation is sufficient; no new identity/approval or replacement-request route follows.
CUA exposed only an empty IAB, so this repair used Agentify's purpose-built scoped UI tools.

[agentify-controller.patch](agentify-controller.patch) adds one explicit product-evidence
classifier and passes the existing composer trigger's observed closed label into it.
It recognizes the current Astra alias only when that exact composer says `6 Pro`/`6Pro`,
there is one product menu, exactly one selected product, and exactly one Latest row.
An available but unselected explicit Astra row prevents alias fallback. Pro is checked
separately using the original semantic slider. Missing/generic/account/future-7 label,
wrong selection, duplicate rows or multiple selected products fail. The alias is a
current UI identity mapping under the existing provider configuration, not backend model
attestation or a permanent meaning assigned to the word Latest.

Normal flow remains one closed composer observation while opening its menu → selected
product → Pro slider → close. A manually pre-opened menu may conceal the required closed
label; close it as a concrete UI repair before the same preflight. Do not change the
operation model to its selector hint. Idempotency, Send, archive and receipt code are untouched.

## Focused evidence and remaining runtime prerequisite

The focused unittest passed in 1.843s: twelve identity cases; actual controller preflight
browser expressions against a visible DOM fixture; independent Pro rejection; frozen
ACPS HANDOFF/prompt/parent/operator checks; actual v4 operation persistence through pre-Send
failure→same-operation repair; model-argument conflict preserved; uncertain effect→observation;
paired IDs, exact archive/hash/size; archived continuation without another mocked Send.
There were two fixture Send effects and **zero external Sends**. New scratch was removed.
Node syntax and reverse patch applicability checks pass. This does not repeat the full
already accepted Transport workflow suite.

One live non-sending preflight on the preserved tab still returns
`chatgpt_product_model_unavailable_or_unselected`. Source is repaired on disk, but the
running Agentify controller has not loaded it. Main statically imports its controller;
the current app has no supported per-tab controller refresh and reconstructs logical
tabs at startup. A blind app restart would therefore violate this assignment's exact-tab
preservation requirement. No restart, new tab, operation edit or alternate Send route ran.

Remaining concrete prerequisite: the application runtime owner must load the tested
controller while preserving/reconciling this exact Q tab/key/operation. Then the ACPS
Transport performs one non-sending Astra/Pro preflight and continues the original operation
once only if it still proves nonacceptance. The current unique next action is runtime
deployment/reconciliation, not repeating the failed preflight or changing the request.
This is VERIFIED_NONACCEPTANCE; no uncertain-effect lock is invented.

## Independent review and DM acceptance

The direct native Astra/high Reviewer `/root/dm_mgtap_resume/rv_ah_transport` returned
no material findings for patch `3478d5499b3f0138064890e5a9d29537adafcebeb64cfd5da9e68ffeed7c4e58`
and controller `c57264e72050e17c0905972304d29a80cb259614885fe4a85088b3899b734084`.
It verified the source/patch hashes, reverse applicability and Node syntax; traced the
closed composer, unique product selection and separate Pro slider through both preflight
and query before `onSendAttempted`; and independently checked the alias positive plus six
negative probes, including duplicate unselected Latest and explicit unselected Astra.
It reviewed the actual DOM/v4 fixtures and confirmed that operation identity, Send effects,
uncertain recovery and archive code remain unchanged. It made no source, UI, runtime or
operation writes and sent no request.

DM technical acceptance on 2026-09-13: accept the bounded source repair and its focused
regression evidence, published in `e7baaf528`. Live runtime readiness is **not accepted**:
the preserved operation still requires the tested controller to be loaded and one changed-
runtime preflight. Current `6Pro` plus selected Latest is a configured UI identity mapping,
not backend attestation; this limit remains explicit. The direct parent action is to assign
or reconcile application runtime loading without destroying the Q tab/key/operation, then
return that changed fact to the ACPS author/Transport. No scientific decision, budget,
request identity or lifecycle changes follow from this engineering acceptance.

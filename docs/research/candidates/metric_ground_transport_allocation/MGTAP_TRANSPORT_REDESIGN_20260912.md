# MGTAP Transport workflow engineering acceptance

## Assignment and L0

Root assigned the full Transport redesign on 2026-09-12: one exact handoff/manifest
preflight, one explicit Send or no Send, same-request bounded observation/archive,
and one direct native receipt. The owner specifically requested screenshot/CUA
state sampling and fixtures for verified nonacceptance, uncertain effect and
accepted effect. This is engineering work; MGTAP science, lifecycle and empirical
allocation are unchanged.

- Deliverable: the minimal current native workflow, focused behavioral tests,
  independent external-effect review and one exact MGTAP live exercise if still unsent.
- Ownership: DM `/root/dm_mgtap_resume`, checkout
  `C:/Projects/HMASD-worktrees/dm-n5-continue-20260904`, branch `codex/mgtap`.
  Owned edits are Transport skill/scripts/references, its role and adjacent route
  docs, focused `tests/skills`/fixture files and this evidence record. Agentify's
  implementation is a read-only dependency; Root integrates shared control changes.
- Protected semantics: original HANDOFF/TASK/prompt bytes, Portfolio conversation,
  one immutable operation identity, single writer, full immutable response and
  distinction between receipt and scientific answer. Historical IDs remain provenance;
  the current native parent/operator are recorded separately.
- Acceptance: exact frozen legacy and current-native inputs, route ownership,
  provider/Pro and protected-tab checks, failed preflight recovery, uncertain/accepted
  observation without Send, archive hash/size/conflict and one native receipt.
  Engineering Scope §7.3 requires independent Reviewer coverage of external effects.
- Budget/stop: only short control-plane fixtures and validator checks, using system
  Python 3.11+ and existing Node; all scratch under invocation-owned `temp/` and
  removed after preserving diagnostics. No scientific compute, new request or
  empirical implementation. An external Send is only the already authorized exact
  MGTAP request after demonstrable nonacceptance and repaired readiness.

Scope §4: none. No service, scheduler, transport relay or new scientific gate.

## Baseline evidence

At clean starting revision `766b72b89`, the immutable request at
`9929beb6eb699b94603a1dfd5d200363e5802ed1` fails the existing validator with
`Transport singleton config must be schema 1, singleton, and active` under current
`dm_native` configuration. Independent Reviewer reproduced this without browser writes.
Existing receipt helpers use the historical parent and cannot represent the assigned
native recovery parent while preserving original metadata.

The actual strict operation `19ca18f5-1683-418c-b204-e03873309af7` failed
`TAB_KEY_MISMATCH` before Send: `sendAttempted=false`, no user/assistant IDs and no
archive. The repaired dedicated tab is keyed `portfolio:cross_direction`; one
non-sending strict preflight verified Latest/Pro. This is verified nonacceptance,
not an uncertain Send. Historical registry parent metadata also differs from the
frozen handoff; the discrepancy must be retained alongside the current native route.

The CUA inspection of the same Portfolio URL showed an empty composer and `6 Pro`
with historical receipt content. A screenshot cannot prove that this particular
request was never accepted; exact request/operation evidence supplies that fact.
The Agentify DOM sample also labelled sidebar titles containing “Continue” as
generation controls. Only controls in the current response/composer count for the
page reading. The CUA inspection tab was closed after the screenshot.

## State transitions and why each step remains

```mermaid
stateDiagram-v2
    READY_UNSENT --> SEND_ATTEMPTED: Exact strict query
    SEND_ATTEMPTED --> READY_UNSENT: VERIFIED_NONACCEPTANCE, repair same inputs
    SEND_ATTEMPTED --> OBSERVE: UNCERTAIN_EFFECT or ACCEPTED
    OBSERVE --> ARCHIVE: Complete paired answer
    ARCHIVE --> RECEIPT: Exact full bytes verified
```

1. One immutable preflight protects the actual request, model, target and single writer.
   The page sample supplies visible facts; the registry and operation supply hidden identity
   and effect history. Failed pre-Send checks do not require another parent authorization.
2. One effect branch prevents duplicate external effects while permitting an unchanged,
   demonstrably unsent request to proceed after a real repair. Workflow bookkeeping alone
   is not evidence of an external click. Retained acceptance history remains controlling.
3. Bounded observation plus the existing strict completion test protects the paired complete
   answer. Exact full-file archival keeps a short delivery receipt distinct from science.
4. One current-parent native receipt makes that archive available for author intake.
   Frozen historical routes and any earlier receipt remain intact.

Removed from the ordinary loop: repeated DOM/account/identity inventories; separate model-menu
confirmation after a successful strict preflight; repeated parent release questions after known
pre-Send failure; an extra operator stability loop; unchanged status broadcasts; Root/app-task
receipt forwarding and ACK loops. None changes binding, external-effect or archive conclusions
once the corresponding evidence exists. First-binding retains its existing explicit Agentify
route; the new recovery helper explicitly handles existing-conversation GitHub handoffs only.

## Validation and independent review

System Python 3.11 and existing Node v24.18.0; no dependencies installed. Commands use
`python -B -m pytest -q -p no:cacheprovider --basetemp <owned temp/tests invocation> <paths>`.

| Focus | Result |
| --- | --- |
| New workflow + existing native transport + send recovery | 90 passed, 3.58 s |
| Existing transport, conversation binding, prompt author, round reset compatibility | 158 passed, 3.83 s |
| Final workflow after independent-review corrections | 49 passed, 3.38 s |
| Role TOML parsing and `git diff --check` | Passed |

The real Agentify `runReviewQuery` dependency was imported from
`C:/Projects/agentify-desktop/review-transport.mjs`, SHA-256
`71a5c377315be9fb3a4de8cf4cff4cdf913bdd6f114b2e5b0e46a47ea4647a86`.
The dry-run uses the exact committed MGTAP prompt; browser/controller effects and all state/output
paths are test fixtures. It reproduces TAB_KEY_MISMATCH/false, repairs the tab while retaining
the operation, records one mocked Send, then observes and archives. A separate crash-after-attempt
fixture observes the same operation without another Send. Exact archive hash/size/conflict,
unknown-operation refusal and immutable input conflict are checked. These tests do not establish
live provider behavior and spend zero scientific invocations.

The screenshot fixture and explicit interpretation are
`tests/fixtures/native_transport/page-ready.png` and `page-ready.json`. SHA-256:
`1a26fb1cb814c69278bb02ee4f1d144d09640d294cc363b80ff280ddd270510a`.
Both DM and independent Reviewer inspected the image. It is an annotated human reading,
not an automated pixel classifier; negative page/model/key/protection cases mutate its
interpreted facts. The actual pre-Send operation receipt is preserved in `mgtap-presend.json`.

Independent Astra/high Reviewer `/root/dm_mgtap_resume/rv_ah_transport` found and the DM repaired:
accepted legacy history ignored by Send classification; generation key lost on successor;
same conversation claimable by another node; newer mirror-only effects overwritten; and a
helper boundary that incorrectly implied first-binding support. Each has a regression. The
Reviewer completed correction review with no remaining material finding and independently
reproduced the repaired boundaries. DM accepts this bounded existing-conversation workflow;
live provider behavior is the separate next exercise. Self-review is not independent review.

The first test invocation found slash-root Git-path handling on Windows; this was repaired.
Its temp parent was missing, producing fixture setup errors; subsequent invocations created
the parent explicitly. Routine failures are engineering facts, not scientific evidence.

## Cleanup and live continuation

Runtime automatic approval review rejected the combined test/cleanup command, then separately
rejected exact-path `Remove-Item -LiteralPath .../temp/tests/mgtap-transport-redesign-02 -Recurse -Force`
after the resolved target was verified. No bypass was attempted. Retained owned directories under
this checkout's `temp/tests/`: `mgtap-transport-redesign-02`, `mgtap-transport-compatibility-01`,
`mgtap-transport-final-01`, `mgtap-transport-review-01`, `mgtap-transport-review-02`.
The failed initial `mgtap-transport-redesign-01` directory does not exist. The original screenshot
scratch under main's `temp/directions/metric_ground_transport_allocation/transport-redesign-20260912`
is also retained; the necessary image is now committed as a fixture. Cleanup remains a concrete
runtime restriction, not a scientific or Send prerequisite.

Live continuation is separate from repair acceptance. The native child will reuse the original
MGTAP HANDOFF and operation after final review/publication, reconcile current effects once,
and take its unique branch. No new performance observation or Portfolio decision has formed
in this engineering work; MGTAP remains ACTIVE and fresh cap/cost fields remain unassigned/unknown.

## 2026-09-13 visibility follow-up and live effect

Root relayed the owner's added requirement: before ending a bounded assignment at completion,
a material conflict or no-current-work/ACTIVE, send one direct native action message containing
assignment, status, evidence/commit and next step. The skill, role and sibling communication
instructions now state this. Nonarchive boundary messages no longer require a completed answer;
they preserve the request's existing effect state and earlier return history. Unchanged waits
produce no message. Active Pro generation is ongoing work, not a terminal prerequisite merely
because several bounded calls time out.

Focused follow-up coverage: 56 workflow tests passed in 4.03 s. It covers nonarchive actionable
messages, current direct destination, unchanged-wait silence, old receipt deduplication, delivering
a historical pending receipt without changing a newer one, and refusing a second COMPLETE answer
across an intervening conflict. Independent Reviewer found the latter two edge cases; DM repaired
them and the Reviewer independently replayed both corrected cases with no material finding. DM
accepts this visibility follow-up. Additional retained scratch: `mgtap-transport-boundary-01`
and `mgtap-transport-boundary-review-01`, under the same recorded cleanup restriction.

The actual live preflight passed at `NATIVE_PREFLIGHT.json` under main's existing runtime archive
`temp/sessions/hmasd-chatgpt-pro-transport/archive/portfolio/2026-09-12-mgtap-unequal-exposure-investment-01/`.
The unchanged operation `19ca18f5-1683-418c-b204-e03873309af7` made one Send attempt, then strict
Agentify returned `USER_MESSAGE_CONTENT_MISMATCH`. Persisted `sendAttempted=true`/click count 1
means UNCERTAIN_EFFECT, permanently observation-only while acceptance remains possible. The
dedicated tab displayed the exact conversation, empty composer and active Stop answering.
No paired current provider IDs or full response was yet available at this record boundary.
The original mismatch and subsequent bounded observations remain in
`AGENTIFY_OPERATION_19ca18f5-1683-418c-b204-e03873309af7_FINAL_OBSERVATION.json` and
`..._IMPASSE_OBSERVATION.json`. Those filenames are historical operator labels; active generation
was not accepted as a terminal impasse. The DM resumed the same child's non-sending observation
and sent Root one action update. No second Send, new idempotency key, scientific invocation or
Portfolio decision was created. Full-response intake remains the dependent outstanding work.

## Actual full-delivery recovery and final technical acceptance

The live exercise ultimately exposed a further workflow defect: the leaf inferred missing output
from strict/UI pairing failure without reading the fixed GitHub response target. Its completion
conflict record at 08:24:19 UTC was not proof that no decision existed. DM checked that target and
found the complete response already delivered at 07:01:37 UTC. Full immutable commit
`f1897441ce560dbca01a834dd72e035c63c68e0a`, Git blob `78a9810d52dedefc881009ea2672dbce36c49cc3`,
Issue17 comment5651823362 and the original fixed TASK jointly establish this request's delivery.
The exact185-line/37775-byte full file has SHA-256
`cb533e36190e03444fc963d2f639338b5ec9f19defc7713d6547d819fd425391`.
It was preserved in Git via `cd609fd307a316b39d127e3d664c2d668ddc7a30`, a single-file cherry-pick
of the actual Pro delivery. The native child then collected the same full bytes at its separate
`__05_FULL_RESPONSE.md`. The original strict response path remains unused, and its mismatch/IDs
are preserved rather than renamed or fabricated.

The repaired route checks the fixed GitHub scope on strict failure and again at completion if
previously absent. It verifies the full immutable response URL/path, Git blob/hash/size and exact
TASK/response pairing in the designated delivery comment. This independent source binding can
complete archival when provider IDs remain null. Frozen delivery scope/task are separate from
observed `github_delivery` facts; same-request claims and mirror reconciliation preserve all
earlier evidence. The child's observed metadata used the Issue URL in `fixed_task_url`; the
correct frozen TASK URL is retained separately and the metadata discrepancy is explicit.

The child also reported that `collaboration.send_message` is not callable in its runtime.
Its actionable native final did return directly to this DM. The workflow now records that
actual native capability instead of requiring an unavailable call, inventing success or adding
an app relay. Same-boundary method changes require demonstrated non-delivery and preserve the
prior method; delivered or uncertain receipts are never resent. This creates no additional
parent permission or ACK step.

Final focused result: **64 workflow tests passed in5.24s**, in addition to the already passing
207 unchanged native/recovery/compatibility tests. Independent Reviewer verified the real GitHub
comment/blob/bytes pairing with null provider IDs, then reviewed corrections for preserving
observed scope, native-method recovery and mirror-only GitHub evidence; no material finding remains.
DM accepts the final engineering workflow. This does not establish that the Agentify page pairing
defect itself is repaired; the scoped immutable GitHub recovery path handles the actual delivery.

Additional retained owned test scratch under the same cleanup restriction:
`mgtap-transport-github-recovery-01`, `mgtap-transport-github-review-01`,
`mgtap-transport-native-final-01`, `mgtap-transport-final-recovery-01`.
No further recursive deletion was attempted. The DM's exact full-file read copy at
`temp/directions/metric_ground_transport_allocation/mgtap-delivery-f1897441.md` is retained as
collection evidence. No unique scientific evidence or shared checkout was removed.

The complete [scientific intake](pro_packets/20260912_cond512_dense768_use/PORTFOLIO_INTAKE_20260913.md)
records Portfolio B and its new600/900/1500/900/2400s limits, plus two concrete current-spec
conflicts requiring the same-node correction: five-chain target and independent Monitor goal.
No implementation, experiment or new Pro request is part of this completed bounded assignment.
MGTAP remains ACTIVE/MEDIUM; the next science is the already selected funded pair, not a vacancy.

DM exercised the reviewed archival recovery on the actual immutable file and comment. The shared
registry and mirror are now ARCHIVED, full-response SHA/size verified, and native receipt SENT
with `transport=native_final`; `NATIVE_ARCHIVE_ACCEPTANCE.json` records this application. Original
strict operation/send uncertainty, null IDs, observed-delivery facts and corrected frozen TASK
metadata remain. The owned tab was closed. ACPS was notified that the shared binding is free;
Root receives the full intake and the same-node correction dependency. This completes the actual
one-attempt lifecycle without another Send.

## Authorized conformance follow-up: successful paired delivery — 2026-09-13

After the original full decision was archived and intaken, Root's coordinated continuation
retained this DM's authorship of the two-clause Portfolio correction. This distinct authorized
request is not a retry of the original uncertain operation. The committed HANDOFF
`c585a70234e9bd6a61f20ba3252ebda33333d12c` binds the fixed TASK at
`755d8fcedceaf83d0ea9d67462ee631c1093ec58`, current parent/child, the same Portfolio conversation
and shared direction branch. The existing reviewed workflow was used without new code changes.

The [operation receipt](../../portfolio/pro_packets/20260913_mgtap_conformance_correction/archive/TRANSPORT_OPERATION.json)
records the initial TAB_KEY_MISMATCH before any persisted Send operation and repair of the
dedicated tab key. This positively observed pre-Send failure permitted the same unchanged
request after repair. Operation `c30e5aae-2de6-484a-aed0-37510c55d908`, idempotency key
`2026-09-13-mgtap-portfolio-conformance-correction-01`, used Latest/Pro and the same prompt hash,
binding, conversation and responsePath. It then recorded one Send at08:58:38 UTC with user
`a8238013-f2ea-4b4e-9044-a69a2ad86281` and assistant `f66dc4c3-ea5d-48fa-a522-fc12dbdad722`.
The final strict operation has no error. No duplicate Send or extra parent confirmation occurred.

The96-byte strict chat receipt was archived separately. The complete task-bound amendment is
the41-line/6860-byte [RESPONSE.md](../../portfolio/pro_packets/20260913_mgtap_conformance_correction/archive/RESPONSE.md)
at `3a69ae2b02f16ac815d1e41ea2fff3a46f3bb0c2`, Git blob
`c7c59ae3da5a190acb6d4efe4b6de7198ed90256`, SHA-256
`330bfaa59c0e30d26fdb946a4f4d0327932af12adb9bf5810569d73f032c19fd`.
The [delivery facts](../../portfolio/pro_packets/20260913_mgtap_conformance_correction/archive/GITHUB_DELIVERY_FACTS.json)
and preserved [Issue comment](../../portfolio/pro_packets/20260913_mgtap_conformance_correction/archive/DELIVERY_COMMENT.md)
bind exact TASK and response URLs. DM compared all immutable Git bytes with the child's full
runtime archive, inspected the single-file commit and actual comment, and read the full answer.

The child returned one actionable native final; both registry views are identical and
ARCHIVED/RECEIPT, with actual native_final receipt SENT. Its owned tab is closed. ACPS received
the explicit shared-binding release. This covers the successful accepted/pairing path in live
use, in addition to the original request's live uncertain/GitHub-recovery path and the focused
dry-run branch coverage. It does not retroactively change the original strict mismatch.

The amendment resolves both procedural conflicts without changing science, caps or lifecycle.
See intake §5. No extra engineering suite was rerun for this document/receipt closeout; the
accepted 64 focused workflow and207 compatibility checks remain the applicable code evidence.
No new empirical experiment or implementation began. Root's next action is integration and
the existing DM's funded continuation; MGTAP remains ACTIVE/MEDIUM. The prior cleanup restriction
and retained scratch inventory remain explicit; no new deletion attempt was made.

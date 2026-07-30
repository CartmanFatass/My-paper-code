---
name: hmasd-review-round
description: Use for GPT-5.6 Pro browser transport, natural-completion monitoring and exact raw archival in either the persistent Research Operations Manager or the separately registered Independent Research Pro Review Operator, under the applicable role-owned wrapper and storage boundary.
---

# HMASD External Pro Review Transport

## Contract boundary

Role contracts are normative. Read the root `AGENTS.md` and these relevant role
documents before operating:

- `.agents/roles/RESEARCH_OPERATIONS_MANAGER.md`
- `.agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md` when the exact review
  is an independent methodology audit
- `.agents/roles/EXTERNAL_PRO.md`

This Skill grants no authority. It is an operational transport procedure only.
It must not decide the need for review or scientific completeness, how to use a
response, or what work follows it.

The applicable registered transport owner activates `$hmasd-review-round` in
the same persistent task and uses `$browser:control-in-app-browser` for
submission and archival. Research Operations Manager alone owns formal review
packages and state. The Independent Research Pro Review Operator may use these
mechanics only through `$hmasd-independent-research-pro-review`, with one
separate conversation and local `local_research/pro_reviews/` storage. After one
exact full-hash Assignment identity is verified in the main body or its
attachment payload, assign
the registered nonpersistent `hmasd-pro-response-monitor` to observe the
transport-owner-brokered metadata sentinel for that turn. The child never
opens the browser. Do not create another transport task, relay, ad hoc monitor or manager
polling loop.

## Required inputs

Require the assigned review mode, round path, pushed 40-character
`stage_commit`, exact question path, exact raw path, mechanical-intake path,
registered reviewer conversation, and declared input paths. The question must
declare exactly one of:

```text
DESIGN_ASSERTION_AUDIT
IMPLEMENTATION_ALIGNMENT_CLARIFICATION
CODE_SCIENCE_ALIGNMENT_AUDIT
FORMAL_RESULT_SCIENTIFIC_DISPOSITION
INDEPENDENT_RESEARCH_METHODOLOGY_AUDIT
```

Before browser submission:

1. Confirm the supplied paths and Git source identity match the
   assignment and are Git-visible at `stage_commit`.
2. Run
   `.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1`
   with that commit and question path.
3. Render the Assignment identity block with
   `.agents/skills/hmasd-review-round/scripts/render_review_fence.ps1` in
   `Assignment` mode. A short, uppercase or otherwise nonexact commit is an
   error before browser interaction. Preserve the exact complete payload bytes
   that will be sent and require them to contain this block exactly once.
4. Select only the role-owned registered conversation. Formal reviews read
   `docs/external-review/REVIEWER_CONVERSATIONS.json`; an independent
   methodology audit reads only its local registry under
   `local_research/pro_reviews/` and must use a different conversation ID.

An identity mismatch stops transport for correction; it does not authorize
editing, paraphrasing, or validating the package.


## Registered-owner transport mode

The tables and shared recovery rules below use `operator` for the persistent
task that owns the exact browser conversation. Formal state and operations-loop
language applies only to Research Operations Manager. The independent operator
instead archives locally and returns one exact methodology packet to Workflow
Design Manager; it never resumes or mutates the formal operations loop.

### Deterministic browser state machine

Execute these states in order. Do not skip a state because an older response is
visible or the page title looks familiar.

| State | Required observation | Mechanical action | Exit condition |
|---|---|---|---|
| `RESOLVE_REGISTERED_CONVERSATION` | Registry supplies one `conversation_id` and URL | Reuse a controlled matching tab; otherwise open the URL once. On a signed-in home-page redirect, find and open the visible link with that exact ID. If the matching page is observably stuck, wait once, take a fresh snapshot, then reload the same tab once for that stuck episode. | URL contains the registered ID and visible conversation messages are readable. |
| `VERIFY_FRESHNESS_FENCE` | Visible user turns can be inspected by message role | Match the renderer identity in the main body or verify the exact attachment payload of that user turn. Submit once only after readable history proves both identity sources absent. | One verified full-hash identity exists, the single prefix-only correction condition is established, or one uncommitted client send requires the persistence check. |
| `RECOVER_UNPERSISTED_ASSIGNMENT` | Exactly one client send occurred; the post-reload history and one fresh exact-URL reopen show zero full or prefix fences, no attachment-backed candidate turn and zero corresponding responses; no sentinel, monitor or prior recovery exists | Classify the action as `UNPERSISTED_CLIENT_SEND` and replay the unchanged complete payload bytes once. | Exactly one main-body or attachment-backed identity is verified, or transport terminates as `REVIEW_TRANSPORT_BLOCKED` with no further Assignment send. |
| `POST_ERROR_PERSISTENCE_RECHECK` | Both permitted Assignment client sends are terminal; no main-body or attachment-backed identity, response, sentinel or monitor exists; the recheck has not run | Without sending, inspect the fresh exact registered URL and signed-in conversation search, including any attachment-backed candidate turn. | Exactly one verified identity restores monitoring or archival; true absence closes as `REVIEW_TRANSPORT_CLOSED_UNPERSISTED_ASSIGNMENT`; unreadable attachment, prefix, duplicate, mismatch or uncertainty remains `REVIEW_TRANSPORT_BLOCKED`. |
| `USER_AUTHORIZED_ASSIGNMENT_SEND` | Direct user authorization names one send after `REVIEW_TRANSPORT_CLOSED_UNPERSISTED_ASSIGNMENT`; the existing package and registered conversation identity remain exact; the grant has not been consumed | Immediately before sending, require the exact registered URL and signed-in search to agree that both identity sources and any corresponding response are absent. Send the unchanged complete payload once only if both prove absence. | One post-send snapshot verifies exactly one main-body or attachment-backed identity and restores monitoring or archival; true absence closes as `REVIEW_TRANSPORT_CLOSED_USER_AUTHORIZED_SEND_UNPERSISTED`; unreadable or mismatched identity is `REVIEW_TRANSPORT_BLOCKED`. |
| `USER_AUTHORIZED_ASSIGNMENT_RESEND` | A new direct user authorization names one resend after `REVIEW_TRANSPORT_CLOSED_USER_AUTHORIZED_SEND_UNPERSISTED`; the prior grant is consumed; the same package and registered conversation remain exact; the resend grant is unused | Immediately before resending, require the exact registered URL and signed-in search to agree that both identity sources and any corresponding response are absent. Send the unchanged complete payload once only if both prove absence. | One post-send snapshot verifies exactly one main-body or attachment-backed identity and restores monitoring or archival; true absence closes as `REVIEW_TRANSPORT_CLOSED_USER_AUTHORIZED_RESEND_UNPERSISTED`; unreadable or mismatched identity is `REVIEW_TRANSPORT_BLOCKED`; emit one local terminal Ops callback. |
| `CORRECT_PREFIX_FENCE` | Exactly one visible assignment differs only because `stage_commit` is a strict 7-39 character hexadecimal prefix of the assigned 40-character commit; all other fields match; no assistant response and no earlier correction exist | Retire any sentinel and monitor bound to the rejected prefix record. Render and send one `FullHashCorrection` message in the same registered conversation. Do not include the scientific question body or alter its allow-list or instruction. | The correction is visibly exact; a fresh sentinel and the only live replacement monitor bind its complete identity. |
| `WAIT_FOR_RESPONSE` | Exact main-body or attachment-backed identity and its user turn are known | The registered transport owner initializes one metadata-only JSONL sentinel, mechanically generates one monitor-assignment receipt, passes only its absolute path to exactly one `hmasd-pro-response-monitor`, then records bounded browser observations at ordinary task wakeups. The child never opens the browser or reads response text. | Repeated 45-second bounded watches in the same monitor remain pending until the Sentinel returns one identity-matched `COMPLETE` or `ERROR`. |
| `RETRY_RESPONSE_CONTRACT` | The original full-hash Assignment identity remains verified, attempt 1 is neither `USER_AUTHORIZED_ASSIGNMENT_SEND` nor `USER_AUTHORIZED_ASSIGNMENT_RESEND`, attempt 1 is terminal with no live monitor or sentinel, no retry exists, and either a stable answer mechanically omits question-declared response items or recovery is exhausted without a complete answer | Render `ResponseRetry`, require the original Assignment as its exact prefix, submit it once in the same registered conversation, then bind one fresh sentinel and replacement monitor to the complete attempt-2 text. | Attempt 2 produces a mechanically format-complete stable answer, or terminates as `REVIEW_TRANSPORT_BLOCKED` with no third submission. |
| `RECOVER_EVIDENCE_ACCESS` | Assistant explicitly reports missing question-listed evidence or unavailable repository access | Treat it as a transport diagnostic. Build the exact `stage_commit` allow-list archive, attach it in the same session and send one mechanical continuation. Do not create another accepted assignment fence or a prefix correction. | A later assistant candidate is attributable to the repair message. |
| `ARCHIVE_AND_INTAKE` | Candidate passes stable completion checks | After monitor `COMPLETE`, the registered transport owner confirms stable text, writes exact visible text to its role-owned raw path, rereads for exact equality, writes provenance intake and confirms monitor absence. | Formal ROM resumes its operations loop; the independent operator returns one exact packet and stops. |

`Response actions` such as `Copy response` plus stable text are supporting
completion evidence, not a substitute for message identity and inactive
generation controls. A CAPTCHA, login or application-approval boundary requires
user action; a generic ChatGPT home page does not.

Always inspect the registered conversation before submission.

Generate the original browser text only with:

```powershell
& .agents/skills/hmasd-review-round/scripts/render_review_fence.ps1 `
  -Mode Assignment `
  -Round <round> `
  -StageCommit <40-character-stage-commit> `
  -Question <question>
```

Search visible user turns for the exact emitted fence identity:

```text
CURRENT_REVIEW_ASSIGNMENT
repository=CartmanFatass/My-paper-code
branch=aggressive
round=<round>
stage_commit=<stage_commit>
question=<question>
instruction=Ignore earlier rounds and refs. Read only this question and its listed evidence from stage_commit.
```

### Assignment identity evidence

Record these observations separately for every client action:

```text
client_send_consumed=true|false
main_body_fence_visible=true|false
attachment_identity_verified=true|false
assistant_generation_started=true|false
natural_completion_verified=true|false
```

The Assignment identity is accepted through exactly one of two sources:

- `MAIN_BODY_IDENTITY_VERIFIED`: the same user turn exposes the complete exact
  renderer identity in its main body; or
- `ATTACHMENT_IDENTITY_VERIFIED`: the same user turn exposes a readable
  `Pasted_text` attachment payload, or provider-native payload metadata, that
  passes the deterministic attachment validator.

For the attachment route, inspect only the attachment belonging to that exact
user turn. Do not download or search unrelated data. Invoke the registered
HMASD Python interpreter on
`.agents/skills/hmasd-review-round/scripts/verify_assignment_attachment_identity.py`
with the preserved complete payload, registered conversation ID, exact user-turn
ID, round, full stage commit and question. A readable attachment must equal the
preserved payload byte-for-byte. Provider-native metadata is admissible only
when it binds the same conversation, turn and immutable attachment ID to the
exact byte count and SHA-256. The attachment filename, icon, preview, ordinary
file size, cleared composer, assistant placeholder or generation control is
never sufficient.

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  .agents/skills/hmasd-review-round/scripts/verify_assignment_attachment_identity.py `
  --expected-payload <exact-complete-payload-path> `
  --observed-attachment <same-turn-readable-attachment-path> `
  --conversation-id <registered-conversation-id> `
  --user-turn-id <exact-user-turn-id> `
  --attachment-id <provider-attachment-id> `
  --round <round> `
  --stage-commit <40-character-stage-commit> `
  --question <question>
```

Use `--provider-metadata` instead of `--observed-attachment` and
`--attachment-id` only for provider-native metadata with the required exact
identity, byte-count and digest fields.

On `ATTACHMENT_IDENTITY_VERIFIED`, initialize the sentinel with the validator's
complete canonical `sentinel_fence_identity`; do not rebuild it from the round,
filename or digest. On `IDENTITY_UNREADABLE` or `IDENTITY_MISMATCH`, record
`REVIEW_TRANSPORT_BLOCKED` without claiming the client send failed and without
authorizing another send. `assistant_generation_started=true` is compatible
with an unreadable identity and never proves natural completion.

- If a matching main-body or attachment-backed identity is verified, adopt its browser state and continue.
  Do not duplicate it during the first attempt. The only same-question
  resubmission is the once-only response retry after the first attempt reaches
  its complete eligibility predicate.
- If a stable response follows that verified identity, archive it without submission.
- If the readable conversation proves both identity sources absent, submit the
  payload once and verify the resulting user turn through either source.
- If identity presence or absence cannot be established, recover the same conversation;
  uncertainty never authorizes submission.

### One unpersisted-assignment recovery

An Assignment is accepted only after its complete rendered identity is verified
in the main body or exact attachment payload. Clicking send, clearing the
composer, receiving a client acknowledgement, observing a transient placeholder
or seeing generation start does not establish identity. An observed attachment
whose contents cannot be read is `IDENTITY_UNREADABLE` and blocked, not an
`UNPERSISTED_CLIENT_SEND`. Record `UNPERSISTED_CLIENT_SEND` only when readable
observations prove that both identity sources and any attributable response are
absent.

Replay is permitted once only when all of the following are mechanically true:

- the same registered conversation is readable and its URL identity is exact;
- exactly one client send action was recorded for this Assignment;
- the readable post-reload history and one fresh exact-URL reopen both show
  zero complete matching fences, zero matching strict-prefix fences, no
  attachment-backed candidate user turn and zero assistant responses
  attributable to this Assignment;
- no sentinel or monitor was initialized, and no prefix correction, response
  retry or unpersisted-assignment recovery exists; and
- the round, 40-character `stage_commit`, question path, repository, branch and
  instruction still equal the pushed package and renderer output.

A same-tab reload alone is insufficient. The replay predicate requires both
server-readable observations and every conjunct above; ordinary visibility
uncertainty remains ineligible.

Render the identity again with the unchanged inputs and require the complete
replay payload to equal the first complete payload byte-for-byte. Send those bytes once in
the same registered conversation without an added explanation, scientific
question body, evidence, instruction or recovery marker. This is the second and
last client send but, because the prior verified identity count is zero, it may
create only the first accepted Assignment. It is not a `FullHashCorrection`,
`ResponseRetry`, UI `Retry` or new scientific assignment.

After replay, initialize the sentinel and monitor only when a fresh readable
snapshot verifies exactly one main-body or attachment-backed identity. An
unreadable attachment, absent identity, duplicate, delayed earlier message or
mismatch terminates as `REVIEW_TRANSPORT_BLOCKED`.
This automatic recovery grants no third Assignment client attempt. Only a
separate direct-user-authorized contract may grant the later send described
below. This recovery changes no review input or authority and consumes zero
scientific iterations.

### One post-error persistence recheck

When both allowed Assignment client sends are terminal as unpersisted, perform
at most one `POST_ERROR_PERSISTENCE_RECHECK`. This is an observation of possible
delayed server persistence, not another submission or another scientific
assignment. It is eligible only when the round, 40-character `stage_commit`,
question path, repository, branch, instruction and registered conversation are
unchanged; no full or prefix fence, attachment-backed candidate turn,
corresponding assistant response, sentinel or monitor is currently visible;
and no prior post-error recheck exists.

Use exactly these bounded read-only observations:

1. Reacquire the exact registered URL and require readable role-identified
   conversation history.
2. Use signed-in conversation search with the exact round, full stage commit
   and question basename. A candidate is evidence only when its URL contains
   the registered conversation ID and its user turn has a verified main-body or
   attachment-backed Assignment identity.

Do not send or render a message, reload repeatedly, use UI `Retry`, invoke
`ResponseRetry`, activate `Answer now`, or initialize a sentinel or monitor
before observing exactly one accepted identity. Then classify once:

- exactly one verified identity and no assistant response: initialize the normal
  sentinel and unique monitor for that identity;
- exactly one verified identity with a stable assistant response: apply the ordinary
  stable-completion and archival checks without sending;
- zero full or prefix fences, no attachment-backed candidate turn and no
  attributable response in both readable observations:
  `REVIEW_TRANSPORT_CLOSED_UNPERSISTED_ASSIGNMENT`;
- a prefix, duplicate, identity mismatch, unreadable attachment or history, or
  disagreement between observations: `REVIEW_TRANSPORT_BLOCKED`.

The recheck consumes zero scientific iterations and cannot repeat. The closed
state resumes only when the same exact Assignment identity later becomes verifiable
without a new send, or a new explicit user-authorized workflow contract defines
any further client send or replacement review package. An unchanged absence is
terminal, not a reason to poll or reopen the conversation again.

### One direct-user-authorized Assignment send

A direct user instruction may authorize exactly one
`USER_AUTHORIZED_ASSIGNMENT_SEND` after
`REVIEW_TRANSPORT_CLOSED_UNPERSISTED_ASSIGNMENT`. This is a new explicit grant,
not automatic recovery and not a reset of the two earlier client sends. Reuse
the existing pushed package, registered conversation, round, repository,
branch, full `stage_commit`, question, evidence allow-list and instruction.
A replacement package requires a separately established package defect and is
not justified by transport nonpersistence alone.

Before consuming the grant:

1. Reacquire the exact registered URL and require readable role-identified
   history.
2. Run signed-in conversation search using the exact round, full stage commit
   and question basename. Accept a candidate only under the same registered
   conversation ID and verified main-body or attachment-backed Assignment identity.
3. Require both observations to agree on zero full matching fences, zero
   strict-prefix matching fences, no attachment-backed candidate turn and zero
   corresponding assistant responses.
4. Require no live generation, sentinel or monitor, and no earlier use of this
   user grant.

If exactly one accepted identity is found, cancel the authorized send and
continue with that existing identity. A prefix, duplicate, mismatch, unreadable
attachment or history, or disagreement is `REVIEW_TRANSPORT_BLOCKED` and consumes no
send. Only the agreed zero state may proceed. Render `Assignment` with the
unchanged inputs, require complete-payload byte equality with the original Assignment, and
perform exactly one client send. The client action consumes the grant whether
or not its identity becomes verifiable.

After the send, take one fresh readable snapshot only. Do not reload, reopen,
search again or enter another recovery:

- exactly one verified identity and no assistant response: initialize the normal
  sentinel and unique monitor;
- exactly one verified identity with a stable assistant response: apply normal
  stable-completion and archival checks without another message;
- zero full or prefix fences, no attachment-backed candidate turn and no
  attributable response:
  `REVIEW_TRANSPORT_CLOSED_USER_AUTHORIZED_SEND_UNPERSISTED`;
- a prefix, duplicate, mismatch, unreadable attachment or uncertainty:
  `REVIEW_TRANSPORT_BLOCKED`.

Do not use UI `Retry`, `ResponseRetry`, a prefix correction, another post-error
recheck, `Answer now`, a replacement package or another Assignment send. The
grant cannot be inherited by another round or attempt and consumes zero
scientific iterations. The closed state resumes only when the same exact Assignment identity
later becomes verifiable without another send, or another direct user grant
is implemented through a new explicit workflow contract.

### One direct-user-authorized Assignment resend

A new direct user instruction may authorize exactly one
`USER_AUTHORIZED_ASSIGNMENT_RESEND` after
`REVIEW_TRANSPORT_CLOSED_USER_AUTHORIZED_SEND_UNPERSISTED`. This is a distinct
grant; it does not reset or inherit the consumed
`USER_AUTHORIZED_ASSIGNMENT_SEND` and creates no reusable resend permission.
Reuse the identical pushed package, registered conversation, round, repository,
branch, full `stage_commit`, question, evidence allow-list and instruction.
Transport nonpersistence alone never requires a replacement package.

Before consuming the resend grant:

1. Reacquire the exact registered URL and require readable role-identified
   history.
2. Run signed-in conversation search with the exact round, full stage commit and
   question basename, accepting only the same registered conversation ID and
   verified main-body or attachment-backed Assignment identity.
3. Require both observations to agree on zero full matching fences, zero
   strict-prefix matching fences, no attachment-backed candidate turn and zero
   corresponding assistant responses.
4. Require no live generation, sentinel or monitor and no prior use of this
   resend grant.

If one accepted identity exists, cancel the resend and adopt it. A
prefix, duplicate, mismatch, unreadable attachment or history, or disagreement is
`REVIEW_TRANSPORT_BLOCKED` and does not consume the grant. Only the agreed zero
state may render the unchanged `Assignment`, prove byte equality with the
original Assignment payload and perform exactly one client resend. The client action
consumes the resend grant whether or not its identity becomes verifiable.

After the resend, take one fresh readable snapshot only. Do not reload, reopen,
search again or invoke any recovery:

- exactly one verified identity and no assistant response: initialize the normal
  sentinel and unique monitor;
- exactly one verified identity with a stable assistant response: apply normal
  stable-completion and archival checks without another message;
- zero full or prefix fences, no attachment-backed candidate turn and no
  attributable response:
  `REVIEW_TRANSPORT_CLOSED_USER_AUTHORIZED_RESEND_UNPERSISTED`;
- a prefix, duplicate, mismatch, unreadable attachment or uncertainty:
  `REVIEW_TRANSPORT_BLOCKED`.

Emit exactly one local terminal operations callback after the pre-send cancel or
the post-send classification:

```text
USER_AUTHORIZED_ASSIGNMENT_RESEND_TERMINAL
outcome=EXISTING_FENCE_ADOPTED|FENCE_ACCEPTED|UNPERSISTED|BLOCKED
client_send_consumed=true|false
server_visible_full_fence_count=0|1|greater_than_1
main_body_fence_visible=true|false
attachment_identity=VERIFIED|UNREADABLE|MISMATCH|ABSENT
assistant_response_visible=true|false
assistant_generation_started=true|false
natural_completion_verified=true|false
sentinel_initialized=true|false
monitor_initialized=true|false
```

Do not emit a pending callback, repeat the terminal callback or create a
cross-task completion relay. Do not use UI `Retry`, `ResponseRetry`, a prefix
correction, another post-error recheck, `Answer now`, a replacement package or
another Assignment send. The grant cannot be inherited and consumes zero
scientific iterations. Its closed state resumes only when the same exact Assignment identity
later becomes verifiable without another send, or another direct user grant
is implemented through a new explicit workflow contract.

### Full-hash prefix correction

A visible assignment whose `stage_commit` is a strict 7-39 character
hexadecimal prefix of the assigned pushed 40-character commit is not an accepted
fence. It is a rejected transport record. Exactly one correction is permitted
only when all other rendered identity fields are equal, the scientific question
was submitted once, no assistant response is visible, and no prior correction
exists. A `USER_AUTHORIZED_ASSIGNMENT_SEND` or
`USER_AUTHORIZED_ASSIGNMENT_RESEND` is ineligible for this correction.
A different round, repository, branch, question, instruction, unrelated
hash or already-visible assistant response fails closed under ordinary transport
blocking; it is never normalized into this exception.

Before correction, make any sentinel and monitor bound to the rejected prefix
terminal and confirm neither is live. Generate the correction only with:

```powershell
& .agents/skills/hmasd-review-round/scripts/render_review_fence.ps1 `
  -Mode FullHashCorrection `
  -Round <round> `
  -StageCommit <40-character-stage-commit> `
  -Question <question> `
  -SupersedesStageCommit <visible-strict-prefix>
```

Send the emitted correction once in the same pending review turn and registered
conversation. It
contains the unchanged identity and instruction plus the prefix-expansion scope;
it contains no scientific question body, no new evidence allow-list and no new
scientific instruction. Do not use `Retry`, resubmit the original question, or
activate `Answer now`. After a fresh snapshot proves every correction field
exact, initialize a new sentinel with the complete correction text as its fence
identity and assign one replacement monitor with the returned opaque token. At
most one monitor and sentinel generation may be live. The corrected full-hash
message is the sole accepted fence and the recovery consumes zero scientific
iterations.

### One response-contract retry

This recovery is distinct from a full-hash correction. It is permitted exactly
once only when all of the following are mechanically established:

- the accepted attempt is neither `USER_AUTHORIZED_ASSIGNMENT_SEND` nor
  `USER_AUTHORIZED_ASSIGNMENT_RESEND`;
- the original full-hash Assignment identity remains verified in the registered
  conversation and every identity field is exact;
- submission attempt 1 is terminal, its monitor and sentinel are no longer
  live, and no response retry is visible;
- the original question explicitly declares required response headings,
  fields, sections or disposition tokens; and
- either two stable snapshots show a complete assistant answer that omits at
  least one declared response item, or applicable read-only recovery is
  exhausted without a complete assistant answer.

Checking presence of declared response items is mechanical. Do not judge the
answer's scientific reasoning, correctness, strength or preferred conclusion.
A client-only message, an absent original fence after reload, an uncertain
conversation identity, elapsed time alone, subjective dissatisfaction or a
question without an explicit response format is ineligible.

After confirming no generation, sentinel or monitor remains live, generate the
second message only with:

```powershell
& .agents/skills/hmasd-review-round/scripts/render_review_fence.ps1 `
  -Mode ResponseRetry `
  -Round <unchanged-round> `
  -StageCommit <unchanged-40-character-stage-commit> `
  -Question <unchanged-question> `
  -RetryReason <format_nonconforming|no_response_after_exhausted_recovery>
```

The renderer reproduces the complete original Assignment byte-for-byte as the
message prefix, then appends `CURRENT_REVIEW_RESPONSE_RETRY`,
`submission_attempt=2`, `supersedes_submission_attempt=1`, the bounded reason
and fixed `RESPONSE_REQUIREMENTS`. Submit that complete text once in the same
registered conversation. It changes no question, evidence allow-list, commit,
scientific instruction or authority and consumes zero scientific iterations.

Require a fresh visible snapshot to match the entire attempt-2 message before
initializing one new sentinel and the only live replacement monitor. Their
opaque identity is the complete retry text, not the repeated Assignment prefix.
If attempt 2 has no format-complete stable response, terminate as
`REVIEW_TRANSPORT_BLOCKED`; never submit attempt 3, create a new scientific
assignment or activate `Answer now`.

Keep one registered page, one live append-only sentinel and exactly one live
registered Pro-response monitor while pending. The bounded prefix correction
or response retry retires the prior generation before creating its single
replacement. Do not create a heartbeat, automation
poller, second monitor or transport task. The registered transport owner owns all
browser access because a native child does not inherit the in-app-browser
binding. At ordinary task wakeups, the operator takes one bounded read-only page
snapshot and calls `scripts/hmasd_pro_response_sentinel.py record`; it does not
run a timer loop or emit pending progress messages. The response text remains
in the browser and is represented in the sentinel only by a content
fingerprint, assistant-message identity and control state.

After Sentinel `init`, create exactly one monitor-assignment receipt with:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/hmasd_pro_response_sentinel.py assignment --state <absolute-jsonl> --receipt <new-absolute-receipt-json>
```

The receipt binds the absolute sentinel path and the opaque
`monitor_assignment_token`. Pass only the receipt path to the native child and
invoke only:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/hmasd_pro_response_sentinel.py watch --assignment-receipt <absolute-receipt-json> --max-wait-seconds 45
```

Do not copy the token into the assignment or command and do not parse, shorten
or rebuild it from a round name, question basename or visible fence. The
Sentinel loads it mechanically from the receipt, decodes the complete
conversation and fence identities, compares them exactly with the initialized
JSONL state, and returns that exact fence identity in its terminal payload. A
missing, duplicate, malformed or mismatched receipt is terminal `ERROR`.

The monitor runs only bounded `watch` calls against that sentinel. Each call is
limited to at most 45 seconds so one tool invocation does not remain blocked;
the same monitor continues these calls for the full Pro response duration.
Expiry of one call is only `PENDING`, never a response deadline, error or
blocked outcome. Two matching inactive operator observations at least three
seconds apart cause the sentinel tool to emit `COMPLETE`; a browser,
identity or response-control error emits `ERROR`. On `COMPLETE`, the operator
already owns the browser and performs exact archival snapshots. On `ERROR`, the operator handles
transport recovery without allowing the monitor to browse, submit or retry.
The JSONL ledger is append-only rather than atomically replaced, avoiding the
Windows file-replacement race previously seen in long runs. Its content
fingerprint is a local stability discriminator, not a workflow artifact hash,
handoff identity or scientific evidence.

Never activate `Answer now`; the monitor is bound by the same prohibition.

`Answer now` is not a completion or recovery control. Never click it, invoke it
through keyboard or script, or use a localized equivalent to satisfy a timeout.
It asks Pro to stop extended reasoning and answer from the partial state.
Because the UI may offer it throughout normal reasoning, its presence or absence is neutral:
neither makes a response pending nor proves completion.
Only Pro's natural completion is admissible.

### Conversation discovery ladder

A redirect to the ChatGPT home page is not a blocker. Keep the valid browser
binding, discard only a stale tab binding, and perform this conversation
discovery ladder before reporting transport unavailable:

1. Inspect controlled and user-visible tabs for a visible conversation link
   whose `href` contains the registered `conversation_id`. Reuse it when found.
2. Open the registered URL once. If it redirects to the signed-in home page,
   inspect visible conversation links and the sidebar/history for that same
   `conversation_id`.
   Treat a blank content pane, missing message-role containers, controls that do
   not respond, or unchanged incomplete rendering after one bounded wait and a
   fresh snapshot as one observed stuck-page episode. Reload the same tab once
   for that episode, take a new snapshot, and re-establish both the registered
   `conversation_id` in the URL and readable message-role state. Reloading never
   proves the matching fence absent and never authorizes submission. Another
   reload requires recovery or materially changed page state followed by a new
   observed stuck episode; an unchanged stuck state proceeds to a materially
   distinct recovery instead of a reload loop.
3. Use the signed-in conversation search with unique current-round evidence:
   the exact `round`, `stage_commit`, and question basename. A candidate is
   accepted only when the candidate URL contains the registered
   `conversation_id` and its visible user turn matches the full fence identity.
4. If the page is a real authentication or application-approval boundary,
   request that user action. A generic home page is not authentication proof.

Never select a conversation from title similarity, page-tail text or an older
round response. Reacquiring or opening a tab does not invalidate the existing
browser binding and does not authorize a new fence.

### Response completion detection

Locate the exact user message containing the accepted main-body or
attachment-backed Assignment identity, or full-hash correction, then inspect
the assistant message after that user turn using
message-role containers such as
`data-message-author-role="assistant"`. Do not use the page tail, a single
spinner, elapsed time or a global status label as the response identity.

Treat the response as naturally complete only when all transport evidence
agrees:

Require two stable snapshots from distinct inspections separated by at least three seconds.

- the same assistant message identity and complete visible text appear in two
  stable snapshots from distinct inspections;
- the second snapshot adds no text and exposes no active `Stop generating` or
  `Stop answering` or cancel-generation control for that turn;
- `Answer now`, including a localized equivalent, is never activated; its
  presence or absence is ignored rather than used as completion evidence;
- no response error, `Retry`, or continue-generation control exists for the
  current turn; partial assistant text plus such a control is not complete; and
- the response belongs to the exact verified Assignment identity rather than an earlier
  assistant turn.

A visible `Thinking` label alone does not prove generation is active. If a
stable assistant response exists and generation controls are inactive, a stale
or collapsed thinking label cannot keep the round pending. Conversely,
changing response text or an active stop control proves generation is still in
progress.

Elapsed time, a monitor deadline, a long thinking phase or partial readable
text never authorizes `Answer now`. Continue waiting for natural completion or,
after safe recovery is exhausted, report a transport blocker without forcing a
shortened answer. Do not keep a naturally completed response pending merely
because `Answer now` remains visible.

When the UI is ambiguous, inspect button labels, disabled state, message roles
and one more stable snapshot before deciding. If an explicit response error has
no completed assistant message, a same-turn `Retry` may be used once as a
recorded recovery after confirming it cannot submit another freshness fence.
After stable completion, check only the presence of response headings, fields,
sections and disposition tokens explicitly required by the question. Do not
assess their scientific content; External Pro retains that authority.

### Evidence-access transport recovery

An assistant message that explicitly says it could not read one or more
question-listed evidence paths, asks for those files, or reports unavailable
repository/connector access is an operational transport diagnostic. This is an
objective provenance failure, not a scientific judgment about response
completeness. Do not archive that diagnostic as scientific raw or treat it as
the round answer.

Recover in the same registered conversation and under the same accepted fence:

1. Parse the exact evidence paths listed by the question. Ignore any additional
   path invented or requested by the diagnostic response.
2. Verify every listed path exists at the pushed `stage_commit`, then
   materialize them from `stage_commit`, not from the current working tree.
   Use one archive with repository-relative paths preserved when duplicate
   basenames exist. Verify the archive member set equals the question allow-list
   exactly and contains no extra file. Use the deterministic builder rather
   than assembling paths manually:

   ```powershell
   & .agents/skills/hmasd-review-round/scripts/build_review_evidence_archive.ps1 `
     -Commit <stage_commit> `
     -QuestionPath <repository-relative-question-path> `
     -OutputPath <new-absolute-zip-path>
   ```

   Continue only when it returns `REVIEW_EVIDENCE_ARCHIVE_READY` with the
   expected commit and file count.
3. Attach that exact archive to the same conversation and send one mechanical
   continuation stating its commit, allow-list identity and that the prior
   response is a transport diagnostic. Do not submit another accepted assignment
   fence or use the prefix-correction exception.
4. The candidate raw is the stable assistant response after the
   latest registered-operator transport-repair message, still anchored to the original
   matching fence. Apply the same two-snapshot and generation-control checks to
   that candidate.
5. If archive ingestion explicitly fails, try one materially distinct
   path-preserving delivery of only the same allow-listed files. Never add
   current-worktree content, an internal scratch artifact, an unlisted Skill or
   a newly authored scientific explanation.

Record the diagnostic and recovery as transport facts in the mechanical intake.
They never change the question contents or the one-accepted-fence state.

## Exact archival, cleanup, and intake

After stable completion:

1. Copy the complete visible response text to the assigned raw path without
   rewriting, normalization, filtering, or summary.
2. Reread it and require exact text equality; record its source commit, paths,
   completion evidence, and any transport recovery in the role-owned mechanical
   intake. Record no scientific quality classification.
3. Confirm the registered response monitor is terminal and no second monitor or
   heartbeat exists.
4. Keep transport facts separate from scientific content. External Pro owns the
   in-boundary scientific disposition. Research Operations Manager resumes the
   formal operations loop from formal raw. The independent operator instead
   copies a format-complete methodology packet verbatim to the registered
   cross-task handoff and stops; it does not update formal state.

Do not compute or require input-file or raw-response hashes. The pushed Git
commit identifies reviewer inputs; exact reread equality plus the later Git
commit identifies archived raw.

The required order is:

```text
monitor terminal -> exact raw -> provenance intake -> monitor absence -> resume operations loop
```

## Recovery and retirement

A browser, runtime, navigation, archive, approval, or response-monitor failure keeps
the same round active while a safe in-scope recovery
remains. Inspect the direct error and current state, then try materially distinct
recoveries such as reconnecting the registered runtime, reusing its tab,
reopening its URL, or rechecking message roles. Never repeat an identical
failed action without changed state. Record:

```text
RECOVERY_ATTEMPT
attempt=<positive integer>
boundary=<failed operation>
action=<diagnostic or recovery action>
outcome=<observed result>
```

A local argument-transport failure, terminated monitor process, stale page,
wrong message anchor or objectively correctable observation is an operational
recovery condition, not `REVIEW_TRANSPORT_BLOCKED`. After the prior monitor is
terminal, the registered transport owner may reuse the same verified receipt to
start one replacement monitor for the same verified Assignment;
there is never more than one live monitor. It may reacquire the same registered
conversation, re-anchor the current verified user turn and assistant message,
and take fresh read-only snapshots without resubmitting the question. These
recoveries consume zero scientific iterations.

`REVIEW_TRANSPORT_BLOCKED` is permitted only when identity or page state remains
uncertain after every safe in-scope read-only or zero-egress recovery is
exhausted and the next action would risk a duplicate send, `Answer now`, wrong
raw archival or another irreversible external effect. One parser error, one
monitor `ERROR`, elapsed time or a corrected observation is never sufficient.
If later objective evidence proves an earlier blocked classification was an
operational misclassification, preserve that record and append an exact
`RECOVERED_OPERATIONAL_MISCLASSIFICATION` correction with its evidence,
duplicate-submission status and `scientific_iteration_cost=zero`; never rewrite
the historical entry silently.

Before the first Assignment client send, prove the matching fence absent. A
client action remains uncommitted until its exact main-body or attachment-backed
identity is verified; the single exact replay above is the only recovery for a
mechanically established `UNPERSISTED_CLIENT_SEND`. After a verified Assignment
identity record exists, only the
once-only prefix correction or response retry may follow, each under its own
complete eligibility predicate. Neither uncertainty nor one missing
client-visible observation authorizes replay or resubmission. Report
`REVIEW_TRANSPORT_BLOCKED` only after all safe in-scope recovery is exhausted;
include the direct cause, attempt summary, duplicate-submission risk, exact
resume condition, and `recovery_exhausted=true`.

At terminal success or terminal block, confirm the response monitor is no
longer live and return control to the applicable registered transport owner.
Only Research Operations Manager resumes the formal operations loop. A stale response from
another round has no authority and never replaces the exact current-round raw
or launches a successor.

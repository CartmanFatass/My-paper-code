# HMASD External Review Protocol

Use a review round only for a cross-round architecture contradiction, design of
a coherent route connected to variable team membership plus variable skill
lifetime, or a critical result whose validity or promotion cannot be settled
from its registered contract.

The round is portfolio-based. Divergent reviewers may propose competing
replacements; the controller synthesis retains two to four live candidates
when evidence permits. The convergent reviewer ranks, attacks and distinguishes
that portfolio and recommends a next serialized evidence source or a stop. It
does not convert resource serialization into a unique legal route.

## Round Sources

The controller starts with `00_REVIEW_BRIEF.md` and
`01_SHARED_SOURCE_MANIFEST.md`. Both divergent reviewers use the shared
manifest. Only Gemini additionally uses `02_GEMINI_LOCAL_SOURCE_MANIFEST.md`
and its allowlisted local papers. Reviewer-specific role and output contracts
live in `10_GEMINI_DIVERGENT_QUESTION.md`, `20_PRO_OPEN_QUESTION.md`, and
`40_PRO_CONVERGENT_QUESTION.md`; the Pro handoff template is transport-neutral.
Both Pro question files must state their role explicitly and contain an exact
`Repository files to inspect` section.

## Gemini Divergent Reviewer

Reuse the exact Antigravity session and Gemini 3.1 Pro (High) model registered
in `docs/external-review/REVIEWER_CONVERSATIONS.json`.
Run in plan and sandbox mode with the tracked local-file and paper allowlist.
Before transmitting private repository content, logs or local papers, record
consent with `review_state.ps1 -Mode consent -ConsentState APPROVED`, the exact
manifest path, its 40-character Git commit, destination and a
`user:<thread-id>:<message-ref>` receipt. The registered Gemini reviewer's
standing consent may supply that receipt without another user prompt, but does
not remove the per-round manifest, commit or destination freeze. Any manifest
difference invalidates consent; `NOT_REQUIRED` is invalid while that
local-source manifest exists.
Keep one live client for research, then export its exact completed response from
the local `transcript_full.jsonl`; do not send another archival prompt. Use a
non-interactive invocation only as a failure fallback, never concurrently with
the live client, and never bypass permissions. Recover a conversation only
after a failure, restart, or concrete source-completeness miss.

## GPT-5.6 Pro Reviewers

### Required 1:1 transport

The active controller never submits a Pro prompt itself. There are exactly two
local/external pairs:

```text
External Review Exchange — Open Pro
  -> OPEN_DIVERGENT external Pro

External Review Exchange — Convergent Pro
  -> CONVERGENT external Pro
```

The controller does not call the browser. It sends routing metadata to the
matching local exchange with all target settings explicit. Each exchange is
created once as `Luna High`; after creation its model is immutable.

Use the Codex built-in browser. Reuse the dedicated open reviewer conversation
and the dedicated convergent reviewer conversation registered in
`docs/external-review/REVIEWER_CONVERSATIONS.json`. The two roles must have
different conversation IDs. Verify the exact URL, visible `Pro` model label and
stored role ACK before each submission; never open the model selector or
change the model of a registered conversation. Replace only the commit and
question-path placeholders in the neutral handoff template, submit it verbatim,
and copy the completed response exactly. The open and convergent roles come
only from their respective question files.

The role ACK is an identity handshake, not a review request. An exchange becomes
usable only after its history contains the registry's exact ACK. On later
submissions, verify that ACK and the current thread/model identity without
adding identity-only turns. Any mismatch is `BLOCKED_REVIEW_THREAD_IDENTITY`.

Every Pro role has a separate one-to-one local Codex exchange conversation in
the registry. `External Review Exchange — Open Pro` may access only the
`OPEN_DIVERGENT` external thread and `21_PRO_OPEN_RAW.md`; `External Review
Exchange — Convergent Pro` may access only the `CONVERGENT` external thread and
`41_PRO_CONVERGENT_RAW.md`. The controller never performs these browser sends
itself.

Cross-task communication is directional. Controller-to-Exchange dispatch uses
the first exact command in `SKILL.md`: `codex_app__list_threads` is authoritative
for target host, thread and status; accept only the registered host/thread with
status `notLoaded`, `completed`, or `idle`. The thread API does not expose
authoritative live model/effort, so use the frozen Exchange registry values and
never claim a live re-read. The dispatch must include `model`, `thinking`,
`hostId`, the route token, and the active controller's
host/thread/model/effort in its prompt. Explicit values must not be used to
repair a reported mismatch.

Exchange-to-controller delivery uses the second exact command in `SKILL.md`.
It must target the controller host/thread supplied by the current dispatch and
must explicitly pass that controller's supplied `model` and `thinking`.
Omitting them, inferring them, or reusing the Exchange model is a target-model
mutation risk and invalidates the relay. A final answer visible only inside the
Exchange task does not notify the controller. Before ending a `COMPLETE`,
`BLOCKED`, or `WAIT_PRO_THINKING` turn, the Exchange sends one `REVIEW_RELAY`
payload and requires a successful tool result for the exact controller thread.
It never sends to the other role and never writes `05_REVIEW_STATE.json`.

After delivery, `codex_app__read_thread` must expose the completed Exchange turn;
its UUID is the `turn:<uuid>` completion reference. When the received dispatch
message and completed answer are two items in that same turn, identify them as
`turn:<uuid>#item-<id>` using the exact item IDs returned by `read_thread`.
Those two item-qualified references are distinct receipts; do not fabricate a
second turn.

The external Pro response must finish naturally. The Exchange must never click
`立即回答`, `停止回答`, `重新生成`, `重试`, a continuation control or an equivalent
response-control button. A browser tool timeout ends only that read attempt:
restore the same page and inspect it without mutation. If the page remains in
`Pro 思考中`, return `WAIT_PRO_THINKING`; the controller keeps the registered
stage `DISPATCHED` and may later request read-only inspection of that same
response. Never submit the question again. If a forbidden control is used, the
transport is invalid, no raw is admissible, and recovery requires an explicit
controller decision.

The Exchange acknowledges its Codex thread ID, target Pro conversation ID and
role before opening the browser, then sends its terminal payload to the active
controller through the required return relay. It may answer locally only after
that call succeeds. `BLOCKED_CONTROLLER_RELAY` means the controller was not
notified even if a local final answer exists.

Use route token `<round>:<role>:<commit>:<raw-path>` for idempotence. Only a
state-script `COMPLETE` transition with the matching route, structured receipt
and nonempty raw closes the token. A GitHub-plugin, authentication, model, thread
identity or incomplete-response failure closes only the transport attempt and
must not be written as `21_PRO_OPEN_RAW.md` or `41_PRO_CONVERGENT_RAW.md`.

Before submission, resolve the proposed commit to exactly 40 hexadecimal
characters, confirm it is reachable from `My-paper-code/aggressive`, and check
the question path plus every listed repository path against that commit tree.
Run `scripts/verify_pro_review_boundary.ps1` from the Skill directory and use
the same immutable commit for the entire submission. A missing commit, role,
section or path is `BLOCKED_REMOTE_EVIDENCE`, not a reviewer task and not a
scientific result.

`DISPATCHED` is not a claim that a send was intended. The state transition must
include a structured `-DispatchReceipt` with the registered session,
conversation, role and model, the exact route, `terminal=DISPATCHED`, and a
`turn:<uuid>` or `turn:<uuid>#item-<id>` reference from the target Exchange task exposed by
`codex_app__read_thread` or `transcript:<id>` for the submitted Gemini prompt
event. A non-manual completion cannot replace that route and requires a second
structured receipt with `terminal=COMPLETE` and a distinct destination-side
reference. The stage artifact is fixed by
stage name; `-ArtifactPath` may only repeat that exact path and cannot redirect
evidence to another file in the round.

## Evidence and Disposition

Use the round's tracked `05_REVIEW_STATE.json` as the sole progress authority.
Create and validate it only with `scripts/review_state.ps1`; artifact presence,
conversation prose or an intended tool call cannot advance a stage. Do not
commit stage progress alone. Commit one package containing both divergent raws,
controller synthesis and their state before convergent Pro when Git-visible
evidence is required; commit convergent raw, disposition and final state together.

Store the exact prompt boundary, raw response, source model, date and related
claim in the tracked round. Raw absence means incomplete evidence. The
controller evaluates claims by evidence and reasoning rather than model
identity and owns every disposition and next authorization.

Before transport, validate and show the state file, then run `-Mode next`.
Gemini and open Pro are independent prerequisites: a blocker in one does not
prevent `next` from selecting the other, but at most one external stage may be
`DISPATCHED`. Synthesis requires both `COMPLETE`; convergent review requires
synthesis; disposition requires convergent review. Treat an identity-confirmed raw as immutable and never
resubmit its prompt. Record a nonempty raw without a matching Exchange receipt
or explicitly identified manual source as `BLOCKED_UNVERIFIED_RAW`; preserve it
for exact recovery rather than generating a duplicate.

# Agentify transport recovery — independent Terra session handoff

```text
handoff_kind=workflow_recovery_protocol_design
target_owner=independent_terra_high_session
execution_leaf=luna_medium
primary_repository=C:/Projects/agentify-desktop
candidate_worktree=C:/Projects/HMASD/temp/worktrees/agentify_full_transport_recovery
candidate_baseline=49253ce5fc37976151cf3a0e58d6b321dbd6737f
science_authority=none
portfolio_authority=none
git_authority=operational_root_only
```

## Assignment

You are the Agentify transport protocol designer and workflow-recovery owner,
not the ordinary page-transport operator. Finish the internal Agentify repair
so a registered Luna-medium transport leaf can reliably complete both:

1. ChatGPT External Pro new binding and saved-conversation continuation; and
2. Gemini bootstrap-first, then same-conversation Gemini 3.1 Pro + Extended
   target request and continuation.

This is fundamentally an MCP-controlled web interaction task. The protocol is
allowed to inspect and modify Agentify source, add narrowly scoped diagnostic
and input primitives, control a task-owned runtime, and perform bounded
non-scientific live validation. Do not let an old Skill, current primitive or
exhausted observation surface define the action space. Those are internal
diagnostic evidence. Design the next safe primitive and close the loop.

Actual repetitive page mechanics should be delegated to a Luna-medium leaf.
Terra-high owns diagnosis, protocol design, source repair, primitive selection,
receipt interpretation and acceptance. Do not instantiate Terra itself as the
routine transport operator.

## Required instruction re-anchor

Read:

1. `C:/Projects/HMASD/AGENTS.md`
2. `C:/Projects/HMASD/.agents/roles/WORKFLOW_RECOVERY_MANAGER.md`
3. `C:/Projects/HMASD/.codex/agents/hmasd-workflow-recovery-manager.toml`
4. this handoff
5. the retained evidence listed below

The current project contract is authoritative over older handoff language. In
particular, `AUTHORITY_BOUNDARY` is not available merely because the old Skill
or current MCP surface lacks a useful primitive. Return outside this recovery
only for a directly required user-exclusive credential or physical action, an
irreversible external risk, or an external side effect not authorized here.
Never return generic `BLOCKED`.

## Authorization

The user has authorized internal Agentify source repair, diagnostic surfaces,
task-owned runtime control, and bounded low-risk non-scientific provider tests.
Routine page submission of a synthetic transport token is inside this recovery;
do not repeatedly ask operational Root for approval. Preserve these hard
boundaries:

- never resend after a visible provider user turn or concrete conversation
  identity;
- never mix directions or use a real scientific prompt for transport testing;
- never operate Stop, Continue, Retry, Answer now or Regenerate;
- never copy cookies or credentials;
- never close or kill ordinary Chrome or its pre-existing tabs/process;
- never modify provider account settings;
- never stage, commit or push; return an exact integration delta to operational
  Root.

## Candidate state

The isolated Agentify candidate is:

`C:/Projects/HMASD/temp/worktrees/agentify_full_transport_recovery`

It is based on `49253ce5fc37976151cf3a0e58d6b321dbd6737f` and currently has a large,
uncommitted 14-file delta (roughly 897 insertions / 63 deletions):

- `browser-backend.mjs`
- `chatgpt-controller.mjs`
- `chrome-cdp-backend.mjs`
- `http-api.mjs`
- `main.mjs`
- `mcp-server.mjs`
- `review-transport.mjs`
- `state.mjs`
- `tab-manager.mjs`
- `tests/browser-backend.test.mjs`
- `tests/chatgpt-controller.test.mjs`
- `tests/http-api.test.mjs`
- `tests/mcp-server-names.test.mjs`
- `tests/review-transport.test.mjs`

Do not assume this whole diff is correct or minimal. Audit it against the
actual failure and split or delete speculative machinery when a smaller stable
primitive suffices. Do not integrate it into `C:/Projects/agentify-desktop`
until the acceptance matrix below passes.

Retained records:

- protocol draft:
  `C:/Projects/HMASD/temp/sessions/agentify_transport_operator/root/agentify_full_transport_recovery/AGENTIFY_TRANSPORT_PROTOCOL_INSTRUCTIONS.md`
- prior recovery handoff:
  `C:/Projects/HMASD/temp/sessions/agentify_transport_operator/root/agentify_full_transport_recovery/WORKFLOW_RECOVERY_HANDOFF.md`
- chronological mechanical report:
  `C:/Projects/HMASD/temp/sessions/agentify_transport_operator/root/agentify_full_transport_recovery/transport_report.txt`
- task runtime state:
  `C:/Projects/HMASD/temp/sessions/agentify_transport_operator/root/agentify_full_transport_recovery/runtime-state/`

The older handoff/report contains stale intermediate conclusions. Use it as a
chronology, not as the current diagnosis.

## What already worked

- Agentify can attach explicitly and fail-closed to the user's already-running,
  authenticated Chrome CDP surface without copying credentials or taking
  ownership of ordinary Chrome.
- The authenticated Gemini shell and Gemini 3.1 Pro control were visible.
- ChatGPT Pro new binding completed naturally through Agentify.
- A second ChatGPT request reopened the saved `/c/<id>` conversation and
  completed naturally.
- Focused source tests for the strict transport/bootstrap model were largely
  passing in the candidate.

These facts show the account and provider are reachable. Do not revive the old
"user is logged out" or "provider unavailable" explanation without new exact
tab evidence.

## What failed before the manual diagnostic

Gemini conditionally mounted a real enabled localized Send button after prompt
insertion. Agentify observed valid geometry and hit-test ownership. Multiple
automation primitives still left the complete prompt in the composer and
created no visible user turn or `/app/<id>`:

- in-page `HTMLElement.click()`;
- trusted CDP pointer dispatch;
- focused Enter;
- focused Enter after a settle interval.

The failures were recorded as `click_no_turn`. They are immutable operations
and must never be resent. They disproved several narrow hypotheses but did not
prove logout, provider refusal or scientific failure.

## Latest incident — this supersedes the older handoff conclusion

The protocol owner prepared one fresh non-scientific Gemini draft and the user
manually clicked the visible Send button once. The last Luna observation stated:

- one manual Gemini user turn was observed;
- the repaired serializer returned `serializerOk=true` with semantic root
  `P`;
- reconciliation still returned
  `review_user_message_content_mismatch`;
- no natural assistant-response receipt had yet been accepted;
- no further action occurred, and the diagnostic tab was retained at that
  observation point.

This proves that the visible real click crosses an interaction boundary that
the tested automated gestures did not, but it also exposes a second defect in
rendered-user-turn identity/reconciliation. Do not collapse those into one
cause.

Because a visible user turn exists, the manual operation is permanently
observe-only. Never click Send again, never reinsert that logical request, and
never create a duplicate provider turn. First inspect the exact retained tab,
URL, message identities, generation state and ledger. If a reply exists or is
still generating, observe naturally and archive it; do not operate a response
control. If no accepted reply is observable, record the exact remaining
unknown rather than guessing.

## Required diagnosis

Resolve both layers independently.

### A. Rendered user-turn identity

Find the first semantic difference between the frozen bootstrap text and the
rendered Gemini user turn after the real click. Use a sanitized diagnostic:
code-point class, whitespace/line-break topology, semantic block sequence,
first mismatch index and hashes are acceptable; do not leak arbitrary page or
account text.

The comparison model must be unified across:

- pre-send composer identity;
- post-send rendered user turn;
- saved-conversation observation/rebind;
- recovery reconciliation.

Do not accept `trim`, substring, equal-length or provider-specific broad
normalization. Canonicalization may repair only browser transformations that
are proven reversible from the frozen source. Preserve source SHA provenance
and fail closed on real content corruption.

### B. Automated activation

Compare the successful physical click with Agentify's failed automation at the
actual browser event/target/focus level. Inspect, as necessary:

- event sequence and trusted/input-source semantics;
- pointer down/up/click ordering and coordinates;
- frame/target/session routing;
- focus/activation/user-gesture state;
- overlay or descendant hit target changes;
- whether the runtime dispatches to the same CDP target as the visible tab;
- whether Gemini requires a platform-specific mouse/touch/key sequence;
- whether Agentify observes the post-click DOM too early or on the wrong
  document.

Do not merely add more arbitrary gestures. Add the smallest diagnostic needed
to discriminate these hypotheses, then choose one evidence-supported input
primitive. The existing-profile Chrome surface is externally owned; do not
close it.

## Required Gemini design

The user specifically selected send-first-then-switch:

1. On a fresh disposable Gemini root tab, send one short explicitly
   non-scientific bootstrap using the currently selected default model.
2. Require a visible user turn, concrete `/app/<conversation-id>`, natural
   assistant reply and durable archive.
3. Reopen that saved conversation in a fresh disposable tab.
4. Select and visibly verify Gemini 3.1 Pro plus Extended thinking.
5. Send one short non-scientific target with a new idempotency key.
6. Reopen the same saved conversation and complete one further continuation.

Do not switch model before the bootstrap. A Gemini target is never allowed
until the bootstrap identity is durably established.

If the manually created user turn already produced a concrete Gemini
conversation and a valid natural response, it may be the bootstrap identity;
continue it only after exact observation/reconciliation. If it did not, it
still remains immutable and may not be resent. A later fresh synthetic
operation must use a new key and be fully automated.

## Acceptance matrix

Do not declare recovery complete until all rows pass on the repaired runtime:

| Provider path | Required evidence |
|---|---|
| ChatGPT new binding | one user turn, one assistant reply, concrete `/c/<id>`, exact prompt identity, natural completion |
| ChatGPT continuation | reopen same `/c/<id>`, new key, one new turn/reply, no duplicate |
| Gemini bootstrap | fully automated send, visible user turn, concrete `/app/<id>`, natural reply |
| Gemini model transition | same saved `/app/<id>`, exactly one visible switch to 3.1 Pro + Extended |
| Gemini target | new key, exact rendered identity, natural reply on switched model |
| Gemini continuation | reopen same `/app/<id>`, no second model transition, one new turn/reply |
| No-resend safety | existing user turn/identity is observation-only under every recovery route |
| Cleanup | disposable tabs close only after archive and inactive generation; ordinary Chrome/default tabs remain intact |

Use only non-scientific synthetic prompts and exact short response tokens for
this matrix.

## Testing and validation authority

Focused source tests and bounded live provider tests are explicitly authorized
for this recovery. Prefer focused tests around the changed adapter, identity,
state/ledger and MCP surfaces. A broad unrelated suite is not a prerequisite.
Record unrelated pre-existing failures separately rather than expanding scope.

The Luna-medium leaf returns mechanical evidence only. Terra-high must inspect
that evidence, continue the recovery loop, and return one conclusion-first
packet only after the acceptance matrix is satisfied or a genuine external
boundary is directly proven.

## Final deliverables to operational Root

Return:

1. plain root cause for both the activation and identity defects;
2. exact changed files and a minimal integration patch/delta against the
   current `C:/Projects/agentify-desktop` baseline;
3. focused test results;
4. live acceptance-matrix receipts without scientific/provider content;
5. updated durable Agentify transport instructions covering Pro and Gemini;
6. cleanup state and any honest residual risk.

Do not stage, commit or push. Operational Root owns final integration.

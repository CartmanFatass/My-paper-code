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

Reuse the persistent Antigravity CLI conversation with Gemini 3.1 Pro (High).
Run in plan and sandbox mode with the tracked local-file and paper allowlist.
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

The controller activates the matching registered heartbeat with routing
metadata; it does not call the browser or send the review prompt across Codex
threads. Each local exchange is created once as `Luna High`; after creation its
model is immutable. No transport or heartbeat call may contain a model or
thinking override.

Use the Codex built-in browser. Reuse the dedicated open reviewer conversation
and the dedicated convergent reviewer conversation registered in
`docs/external-review/REVIEWER_CONVERSATIONS.json`. The two roles must have
different conversation IDs. Verify the exact URL, visible `Pro` model label and
stored role heartbeat before each submission; never open the model selector or
change the model of a registered conversation. Replace only the commit and
question-path placeholders in the neutral handoff template, submit it verbatim,
and copy the completed response exactly. The open and convergent roles come
only from their respective question files.

The role heartbeat is an identity handshake, not a review request. A reviewer
conversation becomes usable only after its history contains the registry's
exact ACK. On later submissions, passively verify that ACK and the current
thread/model identity; do not add repeated heartbeat turns unless the page or
identity is ambiguous. Any mismatch is `BLOCKED_REVIEW_THREAD_IDENTITY`.

Every Pro role has a separate one-to-one local Codex exchange conversation in
the registry. `External Review Exchange — Open Pro` may access only the
`OPEN_DIVERGENT` external thread and `21_PRO_OPEN_RAW.md`; `External Review
Exchange — Convergent Pro` may access only the `CONVERGENT` external thread and
`41_PRO_CONVERGENT_RAW.md`. The controller never performs these browser sends
itself.

Each exchange conversation is awakened by its own registered heartbeat rather
than a direct cross-thread review prompt. The wake payload contains no model
selection and no review content, only routing metadata, immutable commit and
the first missing artifact. It must acknowledge its Codex thread ID, target Pro
conversation ID and role before opening the browser. The controller rejects a
stale, missing or cross-role ACK. The exchange pauses its heartbeat after raw
archival or a transport blocker; it never sends a prompt to the other role.

This heartbeat is a compatibility boundary around a confirmed direct-message
transport defect, not a permanent architectural preference. In the affected
Codex Desktop/runtime version, an omitted `model`/`thinking` argument still
allows the sender turn's settings to enter the target `UserInput`, and a reverse
message can produce the appearance of a model swap. Therefore neither the
controller nor an exchange thread sends a direct return message. The raw file
and route token are the mailbox; the controller observes the artifact and the
heartbeat state. Explicit target-model overrides, database edits and automatic
post-send restoration are forbidden because they mutate rather than preserve
thread identity.

Direct thread messaging may replace this compatibility route only after an
updated product passes a disposable A/B regression: different source and target
models, omitted overrides, A-to-B and B-to-A delivery, idle and busy targets,
exactly one delivery, unchanged effective turn settings and unchanged persisted
thread settings. A production review round is never the regression fixture.

Use route token `<round>:<role>:<commit>:<raw-path>` for idempotence. A nonempty
scientific raw closes the token. A GitHub-plugin, authentication, model, thread
identity or incomplete-response failure closes only the transport attempt and
must not be written as `21_PRO_OPEN_RAW.md` or `41_PRO_CONVERGENT_RAW.md`.

Before submission, resolve the proposed commit to exactly 40 hexadecimal
characters, confirm it is reachable from `My-paper-code/aggressive`, and check
the question path plus every listed repository path against that commit tree.
Run `scripts/verify_pro_review_boundary.ps1` from the Skill directory and use
the same immutable commit for the entire submission. A missing commit, role,
section or path is `BLOCKED_REMOTE_EVIDENCE`, not a reviewer task and not a
scientific result.

## Evidence and Disposition

Store the exact prompt boundary, raw response, source model, date and related
claim in the tracked round. Raw absence means incomplete evidence. The
controller evaluates claims by evidence and reasoning rather than model
identity and owns every disposition and next authorization.

Before transport, inspect the ordered artifact list and resume at the first
missing artifact. Treat every nonempty raw file as immutable completed evidence;
never resubmit its prompt. If the stored raw is partial or its identity cannot
be verified, stop for exact manual recovery rather than generating a duplicate.

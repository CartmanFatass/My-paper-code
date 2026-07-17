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

When a dedicated Codex transport conversation is used, it is awakened by its
own heartbeat rather than a direct cross-thread review prompt. The wake payload
contains no model selection and no review content, only routing metadata. It
must acknowledge its Codex thread ID, target Pro conversation ID and role before
opening the browser. The controller rejects a stale, missing or cross-role ACK.

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

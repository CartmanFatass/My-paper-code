# HMASD External Review Protocol

Use a review round only for a cross-round architecture contradiction, design of
a coherent route connected to variable team membership plus variable skill
lifetime, or a critical result whose validity or promotion cannot be settled
from its registered contract.

## Round Sources

The controller starts with `00_REVIEW_BRIEF.md` and
`01_SHARED_SOURCE_MANIFEST.md`. Both divergent reviewers use the shared
manifest. Only Gemini additionally uses `02_GEMINI_LOCAL_SOURCE_MANIFEST.md`
and its allowlisted local papers. Reviewer-specific role and output contracts
live in `10_GEMINI_DIVERGENT_QUESTION.md`, `20_PRO_OPEN_QUESTION.md`, and
`40_PRO_CONVERGENT_QUESTION.md`; the Pro handoff template is transport-neutral.

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
and the existing `HMASD Algorithm Consultation` convergent conversation. Verify
that each already uses GPT-5.6 Pro; never change the model. Replace only the
commit and question-path placeholders in the neutral handoff template, submit
it verbatim, and copy the completed response exactly. The open and convergent
roles come only from their respective question files.

Before submission, resolve the proposed commit to exactly 40 hexadecimal
characters, confirm it is reachable from `My-paper-code/aggressive`, and check
the question path plus every listed repository path against that commit tree.
Use the same immutable commit for the entire submission. A missing commit or
path is `BLOCKED_REMOTE_EVIDENCE`, not a reviewer task and not a scientific
result.

## Evidence and Disposition

Store the exact prompt boundary, raw response, source model, date and related
claim in the tracked round. Raw absence means incomplete evidence. The
controller evaluates claims by evidence and reasoning rather than model
identity and owns every disposition and next authorization.

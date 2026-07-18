# HMASD External Review Workflow

External reviewers have different contexts, but no fixed hierarchy of
intellectual authority. Claims are weighted by evidence, reasoning and fit to
the HMASD contract rather than by model identity.

## Roles

1. **Gemini divergent reviewer.** A persistent local Antigravity CLI
   conversation using Gemini 3.1 Pro (High). It reads the shared evidence pack
   plus explicitly allowlisted local papers and may propose, replace or reject
   architecture hypotheses.
2. **GPT-5.6 Pro open reviewer.** A dedicated persistent conversation,
   separate from the convergent reviewer. It receives the shared Git-visible
   evidence pack but not Gemini's response. It performs an independent open
   architecture review and has equal standing with Gemini.
3. **Codex controller.** It compares the two raw reviews, checks them against
   repository evidence and writes a synthesis without selecting by model name.
4. **GPT-5.6 Pro convergent reviewer.** The existing `HMASD Algorithm
   consultation role in its own registered persistent conversation. It receives
   the evidence pack, both raw reviews and the Codex synthesis, then ranks and
   stress-tests a portfolio of two to four live candidates and recommends the
   next serialized evidence source or an explicit stop. Only the controller
   adopts or rejects that recommendation.

The two divergent reviews are blind on their first pass. Neither output is an
experiment authorization. The convergent reviewer may add an omitted candidate
only by identifying a concrete omission in the evidence pack. It must not turn
one scheduled experiment into a claim that only one research direction exists.

## Execution default

Reviewer communication is automatic by default. Gemini retains one persistent
local Codex Exchange bound to its Antigravity session. The active controller
accesses the two persistent role-specific Pro conversations directly through
the pinned `codex-chatgpt-control` plugin. A tracked Git-visible Pro review needs
no repeated approval after the round is authorized. Transmitting private
repository material, logs or local papers to Gemini/Antigravity requires
explicit informed approval for the named allowlist; automatic review authority
does not imply external-data consent. The sequence remains bounded to one blind
divergent response per reviewer, one controller synthesis and one convergent
response. A follow-up may repair a concrete missing source or ambiguous
response, not search until a preferred answer appears.

Before either Pro submission, the controller must resolve the exact full
40-character commit, confirm that it is reachable from the remote `aggressive`
branch, and verify that the question plus every `Repository files to inspect`
path exists in that same commit. Each Pro question must also identify its role
explicitly and contain that exact section. The controller runs
`.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1`;
any failed remote boundary check stops the submission before browser transport.

The machine-readable registry is
`docs/external-review/REVIEWER_CONVERSATIONS.json`. It binds Gemini to its one
Exchange and binds each Pro role to a distinct external URL. Reuse these exact
sessions; do not create substitutes, mix roles, or run two external transports
at once. Automatic review does not authorize reviewer-proposed edits,
experiments or promotion.

The Pro sequence is:

```text
controller verifies remote commit/question boundary
-> plugin opens Chat and the exact registered URL
-> plugin verifies visible Pro intelligence
-> one prompt submission and chatgpt_control DISPATCHED receipt
-> bounded same-thread wait/read until natural completion
-> exact raw archive and chatgpt_control COMPLETE receipt
-> controller resumes from the first missing artifact
```

The Gemini Exchange alone uses `codex_app__send_message_to_thread`, with only
`hostId`, `threadId` and `prompt`; do not add `model` or `thinking`. Pro transport
uses no Codex task, cross-task relay, heartbeat, automation, shell sleep or
replacement conversation. While Pro is generating, status/read calls reuse the
same visible thread and never resubmit the prompt.

The idempotence token is `<round>:<role>:<commit>:<raw-path>`. A plugin or
authentication failure is not a scientific reviewer response and is never
stored in the role raw path.

All Pro submissions use the visible Chat surface exposed by the pinned plugin.
If the browser bridge, login, role-specific conversation or verified `Pro`
setting is unavailable, return the plugin's structured blocker; never create a
substitute or bypass the product UI.

## Round ownership

New multi-review work lives under one round directory:

```text
rounds/YYYYMMDD_topic/
  00_REVIEW_BRIEF.md
  01_SHARED_SOURCE_MANIFEST.md
  02_GEMINI_LOCAL_SOURCE_MANIFEST.md
  05_REVIEW_STATE.json
  09_GEMINI_LIVE_RESEARCH_PROMPT.md
  10_GEMINI_DIVERGENT_QUESTION.md
  11_GEMINI_DIVERGENT_RAW.md
  20_PRO_OPEN_QUESTION.md
  21_PRO_OPEN_RAW.md
  30_CONTROLLER_SYNTHESIS.md
  40_PRO_CONVERGENT_QUESTION.md
  41_PRO_CONVERGENT_RAW.md
  50_DISPOSITION.md
```

The brief, manifests and initial review state are written once. Reviewer-specific questions
contain only role and requested-output differences. Raw responses are archived
before synthesis. Accepted algorithm design moves to `docs/research/`; current
ownership stays in `memory/CURRENT_WORK.md`; runtime evidence stays in `logs/`.

`05_REVIEW_STATE.json`, maintained by the Skill's state script, is the sole
progress authority. Run `-Mode next` and act only on `NEXT:<stage>`; divergent
reviewers are independent prerequisites but their submissions are serialized.
A state-confirmed raw is immutable and its prompt is never submitted again.
Preserve a nonempty raw without a matching structured receipt as
`BLOCKED_UNVERIFIED_RAW`; it is neither completion evidence nor permission to
create a duplicate.

Existing model-specific directories remain historical/operational stores and
are not reorganized retroactively.

## Gemini process lifecycle

Keep one live `agy` process for the Gemini research phase of a review round.
Send follow-up questions to that process rather than repeatedly resuming the
conversation. Before closing it, verify that every mandatory local source was
actually inspected; repair a missing-source finding inside the same live
process. After the final answer is visible, exit the process and export that
exact completed response from Antigravity's local `transcript_full.jsonl` as
`11_GEMINI_DIVERGENT_RAW.md`. Do not send another prompt merely to obtain an
archivable answer. Conversation-ID recovery is only a crash,
application-restart or concrete source-completeness repair fallback; the
non-interactive invocation remains a one-turn fallback, not the normal end of
a live research phase.

This removes repeated CLI startup and local conversation reload, but it does
not promise provider-side KV-cache persistence. Long-context cost still grows
with the conversation itself, so close the process at the round boundary and
start a fresh review conversation when the research topic materially changes.

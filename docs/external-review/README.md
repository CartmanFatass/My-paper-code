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

Reviewer communication is automatic by default through three persistent
one-to-one local Codex Exchanges: Gemini, Open Pro and Convergent Pro. The
controller never performs their browser or Antigravity transport directly. A
tracked Git-visible Pro exchange needs no repeated approval after the round is
authorized. Transmitting private repository material, logs or local papers to
Gemini/Antigravity requires explicit informed approval for the named allowlist;
automatic review authority does not imply external-data consent. The automatic
sequence remains bounded to one blind divergent response per reviewer, one
controller synthesis and one convergent response. A follow-up may repair a
concrete missing source or ambiguous response, not search until a preferred
answer appears.

Before either Pro submission, the controller must resolve the exact full
40-character commit, confirm that it is reachable from the remote `aggressive`
branch, and verify that the question plus every `Repository files to inspect`
path exists in that same commit. Each Pro question must also identify its role
explicitly and contain that exact section. The controller runs
`.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1`;
any failed remote boundary check stops the submission before browser transport.

The machine-readable registry is
`docs/external-review/REVIEWER_CONVERSATIONS.json`. It binds each reviewer to
one external session and one local Exchange task. Open and convergent roles use
different external and local conversations. Before every submission, verify
the exact local host/thread/title/cwd and external URL/model label/role ACK.
Neither thread API exposes authoritative live model settings; do not claim a
live model read or repair a mismatch. Any reported mismatch is
`BLOCKED_REVIEW_THREAD_IDENTITY`.

Reuse the three registered Exchanges and their external sessions. Do not create,
fork, hand off, rename, duplicate or alter their models. Automatic exchange
does not authorize reviewer-proposed edits, experiments or promotion.

The exact dispatch sequence is:

```text
controller read_thread identity preflight
-> send hostId/threadId/prompt to the matching Exchange
-> read_thread delivery confirmation and DISPATCHED receipt
-> Exchange external identity check and submission
-> exact raw archive or transport blocker
-> Exchange sends one terminal REVIEW_RELAY to the controller
-> controller confirms the Exchange terminal turn/item
-> controller resumes from the first missing artifact
```

Both directions call `codex_app__send_message_to_thread` with only `hostId`,
`threadId` and `prompt`. Do not add `model` or `thinking`: current tool semantics
preserve the target settings when they are omitted, while supplying either is
an override. Confirm both deliveries with `read_thread`. A local Exchange final
without the active terminal relay is not notification. Do not use a review
transport subagent, `collaboration.send_message`, heartbeat, automation, shell
sleep or a replacement conversation.

The idempotence token is `<round>:<role>:<commit>:<raw-path>`. A plugin or
authentication failure is not a scientific reviewer response and is never
stored in the role raw path.

All GPT-5.6 Pro submissions use the Codex built-in browser inside the matching
Exchange. If a registered task or external conversation is missing or busy,
recover that same pair or return `BLOCKED`; never create a substitute or use
Chrome, Computer Use or a generic web request.

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

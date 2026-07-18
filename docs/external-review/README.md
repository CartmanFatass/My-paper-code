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

Reviewer communication is automatic by default. The controller may run Gemini
after each tracked question boundary is committed and pushed. Pro submissions
are performed only by role-specific Terra Medium transport subagents; the
controller never submits them in its own browser. A tracked Git-visible Pro
exchange needs no repeated approval after the round is authorized. Transmitting
private repository material, logs or local papers to Gemini/Antigravity requires
explicit informed approval for the named allowlist; automatic review authority
does not imply external-data consent. The automatic sequence remains bounded to one
blind divergent response per reviewer, one controller synthesis and one
convergent response. A follow-up is allowed only to repair a concrete missing
source or ambiguous response, not to keep searching until a preferred answer
appears.

Before either Pro submission, the controller must resolve the exact full
40-character commit, confirm that it is reachable from the remote `aggressive`
branch, and verify that the question plus every `Repository files to inspect`
path exists in that same commit. Each Pro question must also identify its role
explicitly and contain that exact section. The controller runs
`.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1`;
any failed remote boundary check stops the submission before browser transport.

The machine-readable Pro role and exchange registry is
`docs/external-review/REVIEWER_CONVERSATIONS.json`. It binds each role to one
external conversation ID, URL, visible model label and role ACK. Open and
convergent roles use different external conversations and different
role-specific Terra Medium transport subagents. Before every submission, verify
the exact URL, visible model label and existing role ACK without changing the
external model. Any mismatch stops as `BLOCKED_REVIEW_THREAD_IDENTITY`; never
route to the other role or a mixed-purpose conversation as fallback.

Reuse the two registered Pro conversations and the one live Gemini process.
Do not create duplicate conversations, alter a conversation's model or run the
open and convergent prompts in the same conversation. Automatic exchange does
not authorize reviewer-proposed edits, experiments or promotion.

The controller does not perform Pro browser transport. It creates one
depth-one `gpt-5.6-terra` medium subagent for the reached reviewer role. The
child is fixed at creation, accesses only its matching external conversation,
stays active through natural Pro completion, archives the exact raw and returns
one final payload that the subagent runtime delivers to `/root`. It never sends
a second collaboration message or receives model settings in a message.

The exact dispatch sequence is:

```text
controller preflight
-> spawn the role-specific Terra Medium subagent
-> verify external role/conversation/model ACK
-> child browser submission and internal wait
-> exact raw archive or transport blocker
-> automatic subagent final delivery
-> controller resumes from the first missing artifact
```

Do not create local Exchange conversations or use `send_message_to_thread`,
`list_threads`, `read_thread`, heartbeat or automation. Those paths combine
transport with conversation identity and previously allowed sender/receiver
model settings to cross. Subagent collaboration messages contain no model or
reasoning fields; the child uses only its automatic final delivery and the
controller remains idle until `COMPLETE` or actionable `BLOCKED`.

The idempotence token is `<round>:<role>:<commit>:<raw-path>`. A plugin or
authentication failure is not a scientific reviewer response and is never
stored in the role raw path.

All GPT-5.6 Pro submissions use the Codex built-in browser. Reuse a registered
usable conversation; if it is busy, wait or recover it. Create one and register
it only when no usable corresponding conversation exists. Never use Chrome,
Computer Use or a generic web request as a substitute.

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

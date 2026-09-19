---
name: hmasd-pro-research-prompt-author
description: Write a focused Pro question in NOTES.md for evidence synthesis, failure diagnosis, a prototype/source bridge, targeted revision, hypothesis generation or pre-confirmation criticism. Preserve the scientific thread and exact transport boundary; never an automatic review or resend.
---

# Pro question

Authority: `docs/project/OPERATING_CONSTITUTION.md` section 5. Pro is an adviser, not an
approval stage. Select the reasoning needed: evidence synthesis, competing failure explanations,
simple-model/literature bridge, targeted revision, candidate generation or pre-confirmation
criticism. Do not turn every result into a consultation or require three to five new ideas.
Pro reasons from the repository at the supplied sha and explicitly supplied primary sources;
it does not inherit the author's chat memory. Use an existing adviser conversation when useful.

## Steps

1. **Write the section.** Append to `docs/research/candidates/<direction>/NOTES.md`:

   ```
   ## Pro question <YYYY-MM-DD> <slug>
   Conversation: <URL from the NOTES.md header, or "new">
   Question: <one focused question; which judgment or choice the answer can change>
   Standing: <current explanation, the motivating observation/gap, supporting and contrary
     evidence, and links to the prior notebook interpretation, runs and claim note>
   Context: <concrete governance/method/evidence files and sections selected using
     references/pro-reading-context.md; source_sha unless an explicit frozen/evidence sha is given>
   Allowance: <fits available for what follows>
   Constraints: seeds and matched baseline per constitution section 8; no training, no edits
     outside the empty "### Answer" subsection; write only there on branch <branch>.
     Read the question at the pinned source, but fetch the latest target file before editing
     and use its actual blob SHA. Preserve all other bytes; stop on overlapping edits.
     On successful write, report the actual commit. On write failure return the complete
     answer in chat, not just a SHA, status message or link.
   Return: <what the evidence strengthens/weakens/leaves unresolved; source-grounded
     explanation or prototype with assumptions and omitted MARL coupling; next useful
     observation and strongest alternative. A targeted revision predicts an intermediate
     change and native consequence, with fit and non-fit cost. Candidate count is task-specific;
     no new idea is required. For criticism also return MATERIAL_DISSENT yes/no.>
   ### Answer
   ```

2. **Commit and push** that file by pathspec on the direction branch. Record the full sha.
3. **Compose the message** with repository, branch, source_sha, target_path,
   question_heading and answer_heading (`### Answer`), the source-pinned URL and the exact
   answer-only write instruction. The source is immutable; the write target is the latest
   version of this file on the named branch. Use a unique question heading, not a reused slot.
   Include the reading/source-precedence instruction from the context reference in the actual
   message; do not send only a bare question URL or assume existing chat memory is current.
4. **Hand off** those same fields, subject key (direction id), message and conversation URL to Transport
   (`hmasd-chatgpt-pro-transport`), or send it yourself when you are the Claude session and
   the Agentify tools are available.
5. **On return**, fetch and inspect before integrating. Apply the Transport complete-answer
   checks to the specified target and immutable answer commit; a short receipt is not an
   answer. While Pro owns the subsection, the DM and its leaves do not edit it. Reconcile an
   uncertain write before taking back that subsection. Paste a complete recovered fallback
   only after verifying no answer already landed and the question is unchanged; commit and
   note "saved from chat". For a new conversation, put its actual URL in the notebook header.
   Use the current branch/file version; never overwrite concurrent changes with the pinned copy.
6. **Respond in writing.** In the next notebook entry record what you adopt, modify or reject,
   which prior judgment changes (or remains unresolved), and why the selected next action follows.
   Preserve contrary evidence and hypotheses inherited from prior work. Advice or consensus is
   not an independent experiment; the DM chooses. Do not create a second reflection report.

## Method context

Pro does not inherit local skills or role instructions. In the existing question, inline the
brief methods that matter or explicitly ask it to read named sections of the scientific-tools
and, when relevant, research-engineering skills at a full published sha. Keep current methods
distinct from frozen experiment inputs; supply only relevant foundation/primary passages.
Check referenced paths exist at the published revision. Include the strongest alternative and
discriminator; fit counts alone need not describe a nested search or sweep's dominant cost.
This is question context, not a packet, recursive reading assignment or additional Pro round.
Use [pro-reading-context.md](references/pro-reading-context.md) to choose the concrete reading
set for synthesis, diagnosis, prototype reasoning, hypotheses or claim review, and an owner-triggered Portfolio
question. It also describes explicitly requested control reviews without adding a routine trigger.
On return, assess the answer's source use and unread material gaps before adopting recommendations.

## Never

No packet, TASK or HANDOFF files, request ids, registry, binding records, finality labels or
mandatory result-review loop. Uncertain send state means reconciliation through Transport on the same
message, never a second send. A method or wording change does not resend a question.

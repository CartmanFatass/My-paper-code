---
name: hmasd-portfolio-task
description: Prepare an owner-triggered HMASD Portfolio review as a dated section in docs/research/RESEARCH.md, send it to the Portfolio Pro conversation, and apply the owner's decision to the direction table. Only when the owner asks; otherwise queue recommendations in NOTES.md.
---

# Portfolio review (owner-triggered)

Authority: `docs/project/OPERATING_CONSTITUTION.md` sections 2 and 4. The owner chooses which
directions exist and triggers review. Nothing else triggers it: not object completion, idle
capacity, a budget concern, a closing note or a timer. Without a trigger, recommendations wait
as `NOTES.md` entries.

## Steps

1. **Gather.** The `RESEARCH.md` tables, each active and reserve direction's last notebook
   entries and claim notes, and the queued recommendations. Verify a standing line against the
   runs folder when it conflicts with the notebook.
2. **Write the section.** Append to `RESEARCH.md`:

   ```
   ## Portfolio review <YYYY-MM-DD> <unique-slug>
   Conversation: <Portfolio conversation URL, one long-lived conversation>
   Standing: <one line per active and reserve direction with sha-pinned links>
   Decisions asked: <activate, archive, reserve, priority order, per-idea allowance changes>
   Options: <each with its consequence; the DM recommendations and reasons>
   ### Answer
   ### Decision
   ```

3. **Publish through the shared integrator.** Root owns main/RESEARCH.md while it is
   coordinating Codex; otherwise the explicitly acting Claude integrator may publish from its
   own checkout. Coordinate the shared writer, commit by pathspec and push. Supply Transport
   repository, branch, source_sha, target_path=`docs/research/RESEARCH.md`, question_heading,
   answer_heading=`### Answer`, subject key=`portfolio`, message and conversation URL.
   Instruct Pro to read the pinned question, fetch the current target version and write only
   the empty answer subsection, preserving the question, tables and `### Decision`. Return
   the actual commit on success or the complete answer in chat on write failure.
   The shared integrator hands off only this subsection while Pro writes and does not edit
   it concurrently. A short receipt is not an answer. Use the same complete-answer, scope and
   uncertain-write reconciliation checks as a direction question; do not look in NOTES.md.
4. **Read the whole answer.** Pro advises. The owner decides; if the owner says to apply Pro's
   answer, apply it. Write the decision and its date under `### Decision`.
5. **Apply.** Update the direction rows (state, priority, lead runtime, standing) and push.
   Nothing else changes: no lifecycle labels, ledger, owner items or decision files.

## Boundaries

A narrow negative closes only the idea it tested; archiving for investment reasons is not a
scientific verdict. Fusion of two directions needs materially the same question, comparator,
estimand and next step, not shared code. Allowances outside section 3 are the owner's to grant.

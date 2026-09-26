---
name: hmasd-portfolio-task
description: Prepare an owner-requested or delegated HMASD project review in RESEARCH.md, obtain Pro advice and apply the responsible scientific decision; consolidate the current index and retire completed review material by date.
---

# Portfolio review (owner-requested or delegated)

Authority: `docs/project/OPERATING_CONSTITUTION.md` sections 2 and 4. Use for an owner's project
review request or consequential project decisions within an explicit management delegation.
The 2026-09-23 delegation lets Root and DMs choose worthwhile research within the project's
purpose without repeated owner approval. A recipe's completion or failure does not automatically
require this review; DM reflection and pivots may use their existing NOTES and section 5 advice.

## Steps

1. **Gather.** The relevant shared background and current tables in `RESEARCH.md`, each active and reserve direction's last notebook
   entries and claim notes, and the queued recommendations. Verify a standing line against the
   runs folder when it conflicts with the notebook. Read the latest working explanation and
   the relevant predecessor: what has been learned, which reasons for hope were weakened,
   what remains untested and what next observation would matter. Do not rank by the latest
   sign or count reviewed experiments as accumulated mechanism understanding.
   In the existing review, check whether relevant shared knowledge actually shaped a comparator,
   prediction or investment choice in the direction's NOTES, and whether reusable changes reached
   RESEARCH. Judge those consequences, not citation counts; absent evidence is unverified use.
   This check belongs to the owner-triggered review, not a new watch or adoption-report cycle.
   Use the section 2 Scientific Reviewer for an independent evidence-first diagnosis and
   direction-correction recommendation, in a separate context rather than a DM/Root history
   fork. Preserve material disagreement with Root as well as with DMs. Reuse that same review
   across overlapping project/claim questions; do not add a second critic ceremony. Root owns
   the reasoned project decision, and the reviewer does not replace section 5 Pro consultation.
2. **Write the working section.** Add the current review to `RESEARCH.md`. It stays here
   while its question, answer or decision is unresolved; completed reviews are retired in step 5,
   not retained as an accumulating project log. Use:

   ```
   ## Portfolio review <YYYY-MM-DD> <unique-slug>
   Conversation: <current Portfolio conversation URL; reuse normally, replace when stale>
   Standing: <one line per active and reserve direction with sha-pinned links>
   Context: <concrete governance/method/evidence sections and revisions selected from the
     Portfolio profile in hmasd-pro-research-prompt-author/references/pro-reading-context.md>
   Decisions asked: <activate, archive, reserve, priority order, next investment and its cost>
   Options: <each with its consequence; recommendation, supporting/contrary evidence,
     uncertainty, known complete cost, substitutability/reversibility, smallest useful next
     investment and what would justify revisiting the choice; include only relevant dimensions>
   ### Answer
   ### Decision
   ```

   Use these comparisons to judge the value of the next investment, not merely the best observed
   score. Explain practical effect importance or headroom only where it bears on that choice;
   an untuned reference gap or a proof unrelated to the claim is not an investment verdict.
   Compare informative continuation (including an unchanged replication) with diagnosis, a
   targeted repair, switching and idle as relevant. Do not require a new architecture to keep
   a question alive, or exhaustive falsification to decline its current cost. Investment
   stopping and scientific weakening are different judgments; neither creates a new gate.
   Include the applicable method context as described in `hmasd-pro-research-prompt-author`,
   within this same section; Pro does not inherit local skills. No separate packet or review trigger.
   Use its [Portfolio reading profile](../hmasd-pro-research-prompt-author/references/pro-reading-context.md):
   current Constitution, relevant scientific methods, affected directions' evidence and real options.
   Historical specs are included only for named frozen obligations or explanatory comparisons.

3. **Publish the scoped review.** The session assigned this owner-triggered project review
   refreshes main, preserves concurrent direction entries, commits by pathspec and pushes from
   its owned checkout. Direction DMs retain their own publication authority. Supply the browser procedure
   repository, branch, source_sha, target_path=`docs/research/RESEARCH.md`, question_heading,
   answer_heading=`### Answer`, subject key=`portfolio`, message and conversation URL.
   Instruct Pro to read the pinned question, fetch the current target version and write only
   the empty answer subsection, preserving the question, tables and `### Decision`. Return
   the actual commit on success or the complete answer in chat on write failure.
   Include the context reference's reading/source-precedence instruction in the actual send message,
   including current-context replacement of stale chat rules and disclosure of critical unread sources.
   The review author hands off only this subsection while Pro writes and does not edit
   it concurrently. A short receipt is not an answer. Use the same complete-answer, scope and
   uncertain-write reconciliation checks as a direction question; do not look in NOTES.md.
4. **Read the whole answer.** Pro advises. The assigned Root/DM decides within the owner's
   explicit delegation; otherwise the owner decides. Do not turn delegated scientific choices
   into another permission request. Check consequential recommendations against the supplied methods and evidence;
   state dependent source gaps without inventing a further review trigger. Write the decision and
   its date under `### Decision`.
5. **Apply and retire.** Update the affected direction rows and replace the current plan with
   the decision's still-effective priorities, reasons, limits and next useful comparisons.
   If the evidence changes a shared judgment, revise that background topic in RESEARCH with its
   scope and supporting/contrary sources; do not add a chronological result account or a second consensus file.
   Keep outcome details in their direction evidence; the index links to them. After the complete
   answer has been read, its write reconciled and the decision recorded, retire the complete
   review and superseded project narrative under `docs/research/archive/<YYYY-MM-DD>/RESEARCH.md`
   in the same publication. Retain the completed review or substantively superseded project plan,
   not each intervening start, collection or acceptance update. Routine status/routing/wording
   changes use Git history and create no archive file. A scoped copy of the retired material is
   sufficient; use a whole-index snapshot only when that context is needed. Include its
   source revision and a historical-only banner, rebase relative links, and preserve inbound
   citations with direct archive links or small compatibility anchors. Use a new suffix if that
   date's file exists. Do not overwrite or keep appending to retired snapshots.

   Pending decisions, accepted-operation recovery and an in-flight answer target remain current
   until resolved; never relocate the target to make a review look complete. Keep current pause,
   states, lead-runtime values, actual routing and frozen obligations recoverable. Retirement
   does not change these facts or restart research. Leave direction NOTES/claims/runs in their
   existing roles and maintain shared background in RESEARCH. Keep a date-directory link and only relevant archive
   references in RESEARCH; no chronological maintenance log, archive registry or new decision file.

## Boundaries

A narrow negative constrains the claims it actually tested; it does not automatically close a direction. Archiving for investment reasons is not a
scientific verdict. Fusion of two directions needs materially the same question, comparator,
estimand and next step, not shared code. Cost remains recorded in fits under section 3.

Index cleanup is ordinary document maintenance under section 4; it does not trigger another
Portfolio review or Pro consultation. Retire superseded content, not decisions merely because
they are old. The archive preserves why a decision was made; RESEARCH states what applies now.

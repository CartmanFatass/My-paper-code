# Portfolio control and the approved set: concurrency is a ceiling, not a quota (OWNER_DIRECT, 2026-09-15 21:37 PDT)

**Provenance.** Owner instruction 2026-09-15 21:35 PDT: "I should not have put the Portfolio
interaction itself into the automated loop. Going forward, we should stop trying to maintain a fixed
number of active directions at all times. Instead, execution should follow the set of directions
that have actually been implemented and explicitly selected through Portfolio review. If the number
of viable directions exceeds the maximum parallel capacity, the additional ones can remain parked as
backups and be pulled in when capacity opens up. But if there are no suitable directions to add, we
should not refill the slots just for the sake of maintaining a target concurrency level. In other
words, concurrency should be a ceiling, not a quota. Portfolio decides what is worth pursuing, and
the execution loop advances that approved set rather than continuously trying to keep every slot
occupied." The hub's redrafted plan (21:36 PDT) was approved at 21:37 PDT ("approve. Do as you
say"). Label `OWNER_DIRECT`. This record supersedes every slot-count, working-set-target, vacancy-
replacement and refill rule in `AGENTS.md`, the loop-dispatch skill, the hub skill and
`PORTFOLIO.md`; it builds on the workflow lanes of 21:03 PDT
(`2026-09-15-workflow-lanes.md`). Git rules, the evidence spec and the decision ladder's tiers are
unchanged.

## 1. Control model

1. **Portfolio review is owner-triggered.** The loop never fires it: not on a slot count, an ended
   allocation, a CLOSE, an idle direction or a timer. The hub prepares the dossier (section 5) when
   the owner asks; the owner decides directly (`OWNER_DIRECT`) or sends the dossier through
   `portfolio:cross_direction` once and intakes the answer (`PRO_FINAL / OWNER_DELEGATED`).
2. **The approved set is the only thing that runs.** `docs/research/portfolio/APPROVED_SET.md` is a
   versioned authority listing each approved direction with lane, standing budget, priority order
   and reopening conditions, plus a parked-backup list in priority order. A direction not in the
   approved list has no producer, no launch and no Pro round.
3. **Concurrency is a ceiling.** Hub ceiling: two directions (unchanged). Node ceiling: whatever
   fresh admission allows. If the approved set exceeds the ceiling, lower-priority approved
   directions wait as backups and are pulled in when a slot opens. If the set is smaller than the
   ceiling, capacity stays empty. No target number of chains exists.
4. **Leaving the set.** A direction that reaches lane CLOSE leaves the approved list. Its slot is not
   refilled. The closing memo and the DM's lifecycle recommendation are queued in
   `APPROVED_SET.md` ("Queued for the next review") and read at the next owner-triggered review.
   The loop does not send lifecycle questions.
5. **Retired.** Root's vacancy-replacement request, the three-chain working-set target, "next chains"
   and slot-refill Portfolio questions, reserved-slot bookkeeping, and the loop-dispatch steps that
   count occupied slots. Root's remaining coordination duties (integration, shared writers, remote
   capacity) are unchanged.

## 2. What the loop still does on its own, inside the set

- Object tier within the direction's lane and standing budget (workflow lanes sections 1, 5, 7).
- Direction-tier convergence rounds only as the lanes allow (CONFIRM: one round at card freeze;
  result review only when the outcome is outside the pre-registered rule). Convergence may conclude
  questions and families; it may not change lifecycle.
- Records, technical acceptance, preservation, cleanup, handoffs at clean boundaries.

## 3. Batches within an approved direction

- EXPLORE: the DM proposes three to five pilots in one packet to `em:<direction>:innovator`; Pro
  prunes and ranks once; the survivors launch in parallel within admission; one review covers the
  batch. No per-pilot Pro rounds.
- CONFIRM: one card with pre-registered branches, seeds per the lanes, one Pro round.

## 4. Stickiness

The hub works the approved set in priority order and stays on a direction until its batch completes
or blocks. Switching only at batch boundaries or on a blocker. The hub's normal shape is one primary
CONFIRM direction plus one background EXPLORE batch. "Drive the other direction meanwhile" applies
only within that shape.

## 5. Portfolio dossier

Prepared by the hub on request as `docs/research/portfolio/dossiers/<date>_PORTFOLIO_DOSSIER.md`:
one table across every candidate direction, approved or parked, with signal on record, headroom
record or none, cost per valid result, lane, budget used, pilots run without signal, the DM's
proposal, and any queued closing memo. Kill criteria (for example no signal after N pilots) appear
as flags in the table; they are never automatic actions.

## 6. Governance

This record and its owner block replace the superseded wording rather than layering on it. After
this change, no process change is made without the owner's request.

## 7. Immediate application (initial approved set, owner-confirmed 21:37 PDT)

| Direction | Status | Lane | Priority | Note |
| --- | --- | --- | --- | --- |
| flexible_skill_duration | approved | CONFIRM | 1 | first object: headroom card (tuned same-information baseline on the UAV host), seeds per the lanes |
| acvc | CLOSE, left the set | CLOSE | – | closing memo `ACVC_CLOSING_MEMO_20260916.md` queued for the first review; slot not refilled |
| vap_folr_core | parked backup | (EXPLORE default) | 2 | Codex-side, operationally paused; enters only by review |
| tail_return_distributional_learning | parked backup | (CONFIRM candidate on retained B01) | 3 | Codex-side, operationally paused; enters only by review |
| every other candidate direction | not approved | – | – | listed in the dossier; enters only by review |

The first dossier is prepared now (owner, 21:37 PDT) so that the ACVC lifecycle and any candidate
additions are decided in one review.

## 8. Files changed by this decision

`docs/research/portfolio/APPROVED_SET.md` (new authority), `AGENTS.md` (owner block at section 5;
the three slot/refill passages in sections 1, 2 and 5 replaced by pointers),
`.agents/skills/hmasd-loop-dispatch/SKILL.md` (steps 4 and 5), `.claude/skills/hmasd-research-hub/SKILL.md`
(Capacity), `CLAUDE.md` (pointer), `PORTFOLIO.md` (header), and
`docs/Claude_docs/changes/2026-09-15-portfolio-control.md`.

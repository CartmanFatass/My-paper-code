# Workflow lanes: process proportional to direction state (OWNER_DIRECT, 2026-09-15 21:03 PDT)

**Provenance.** Owner instruction 2026-09-15 21:01 PDT: "The current workflow is too rigid. We need
to make some adjustments. ... Using the same process across all stages and applying the same
standards to every workstream is clearly not appropriate." The Claude hub proposed seven changes
(session `https://claude.ai/code/session_019aK3w1QeucCiHzZgsVKrti`, 21:02 PDT); the owner replied
"approve" at 21:03 PDT. This record is the normative text. Label: `OWNER_DIRECT`. It is a
Portfolio-tier governance decision under `AGENTS.md` section 2 and a specification change under
section 4.7 made directly by the owner; where it conflicts with older direction, template, skill or
role wording it prevails. The evidence spec section 11 remains controlling for every confirmatory
object. Git rules (pathspec commits, immediate push, no history rewrites, no evidence deletion) are
unchanged.

## 1. Three lanes

A lane is a property of a direction, recorded in `PORTFOLIO.md`, assigned by the direction's DM
with a one-line reason and changeable by Portfolio or the owner. A direction without an effect on
record is in the exploratory lane by default.

| Lane | Enters when | Object type | Process |
| --- | --- | --- | --- |
| **EXPLORE** | no established effect, or a question the DM wants to size before committing | `PILOT`: one fit per arm, single seed allowed, DM-chosen at object tier | pilot note, `summary.json`, one intake paragraph; no Pro round; no brief unless something moved; independent review only per section 6 |
| **CONFIRM** | an effect on record (a pilot or a prior B result) that the direction now wants to establish | B object under evidence spec section 11 | full card with pre-registered branches and decision rule; seeds per section 5; independent review per section 6; brief; at most one Pro round per object (section 3) |
| **CLOSE** | Convergence or Portfolio concludes the direction's questions, or the DM finds no defensible confirmatory object | none | one closing memo `<DIRECTION>_CLOSING_MEMO_<date>.md`; one Portfolio lifecycle round, bundled with any other pending Portfolio question; no new objects unless Portfolio reopens |

`PILOT` objects are A-class exploratory work under evidence spec section 11.1. They are reported
as a signed effect with its n and the label `PILOT`, never with an MEI verdict, never cited as a B
result, and they have no consumption state. Their purpose is to choose the confirmatory object.

## 2. Direction-tier and Portfolio-tier authority is unchanged

Opening or closing an object family, park, recast and lifecycle stay with the Pro nodes and the
owner. What changes is how often they are consulted (section 3) and what a pilot may do without
them (section 1).

## 3. Pro rounds: at most one per object, none per pilot

- A CONFIRM object gets one Pro round, at card freeze, that fixes the decision rule for every
  result branch. The result review is dispatched only when the outcome lands outside the
  pre-registered rule, when the DM dissents from applying the rule, or when the node asked to see
  the result.
- A pilot gets no Pro round. The DM records its object-tier choice in the intake paragraph.
- Direction-tier and Portfolio-tier questions are batched at natural boundaries (a concluded
  object, a lane change, a lifecycle event) rather than sent one at a time.
- Requests already sent keep their route; the pending ACVC result review is intaken as sent.

## 4. Records: three per object, refresh once per boundary

- Per object: the card (CONFIRM) or pilot note (EXPLORE), `summary.json`, and the intake (a
  section in one intake file, or a paragraph appended to `DIRECTION.md` for a pilot).
- `DIRECTION.md`, the direction handoff, the root handoff, `PORTFOLIO.md` and
  `EXPERIMENT_TRACKING.md` are refreshed once per clean boundary, not after every event.
- Audit ledger rows only for `selection` decisions with a real alternative. Technical facts stay
  in the intake. Owner inbox items only for lifecycle or Portfolio decisions and confirmatory
  results (P1); pilots produce no item.
- The evidence folder keeps what the claim needs (native outputs, reduce summary, launch facts).
  Separate dependency, prediction-scoring, world-difference, preservation and cleanup files are
  optional for pilots and may be folded into `summary.json` or the intake for CONFIRM objects.

## 5. Statistical burden by lane

- EXPLORE: single seed, any effect size, label `PILOT`.
- CONFIRM: at least two independent training seeds per arm, or a declared minimum effect of
  interest at least as large as the recorded seed spread on the direction's host, with the DM's
  reason. Cards state which. No project-wide number; section 11.8 proportional burden applies.
- A "within MEI" or "above MEI" verdict is issued only in the CONFIRM lane.

## 6. Review proportional to risk

Independent `hmasd-reviewer` review is required only for diffs touching shared core, numerics,
RNG, checkpoint format, result identity or external effects (`ENGINEERING_SCOPE_SPEC.md` section
7.3). Thin entries that rebind already-reviewed runners, pilot runners and record-only changes
get DM self-review plus the existing tests. The L0 five facts are still written for every code
task; they may be three lines for a pilot.

## 7. Standing per-direction compute budget

Each ACTIVE direction has a standing budget instead of per-object Portfolio grants:

- EXPLORE: up to four single-seed fits per seven-day window.
- CONFIRM: one confirmatory object per seven-day window, sized by its card (seeds included).
- Unused budget does not roll over. Per-invocation runtime limits, fresh resource admission and
  the remote-first route are unchanged. A DM that needs more asks Portfolio once, with the
  pilot evidence; Portfolio reviews allocations at lifecycle events and on request.
- Portfolio grants already recorded (ACVC G3) are spent and closed; nothing here reopens them.

## 8. Two loops, one specification

The evidence spec, Git rules and decision ladder are shared. The Claude hub runs the EXPLORE
lane with the lighter records above because its two-direction cap and session quota make the
full ceremony expensive; the Codex loop applies the same lanes when it drives a direction. The
lane belongs to the direction, not to the runtime.

## 9. Immediate application

| Direction | Lane | Reason |
| --- | --- | --- |
| acvc | CLOSE, effective when the pending result review (`2026-09-16-acvc-matched-package-result-review-01`) is intaken | three matched comparisons show a compensating wrapper, no consistent package advantage, two recasts consumed; the DM sees no defensible confirmatory object. If the node selects another object, that object runs as a pilot and the direction stays in CLOSE afterwards unless the pilot shows an effect. |
| flexible_skill_duration | CONFIRM | the one direction with an effect on record (foundations review 2026-09-14); first object is the headroom card: tuned same-information baseline on the UAV host versus the direction's reference, seeds per section 5 |
| vap_folr_core, tail_return_distributional_learning | assigned by their DMs at resume; default EXPLORE (FOLR mixed block pattern), TRDL may enter CONFIRM on its retained B01 positive result | Codex-side directions, operationally paused |

## 10. Files changed by this decision

`AGENTS.md` (owner block after "Workflow calibration"), `CLAUDE.md` (owner instruction
paragraph), `.claude/skills/hmasd-research-hub/SKILL.md` (Lanes section), `PORTFOLIO.md`
(lane paragraph), `docs/Claude_docs/changes/2026-09-15-workflow-lanes.md` and its README index
line. The trace is the commit that adds this file.

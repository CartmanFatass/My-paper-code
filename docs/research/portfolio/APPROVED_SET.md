> Superseded 2026-09-16 17:53 PDT: the current approved set is `docs/research/RESEARCH.md` (constitution section 4). This file is historical and no longer maintained.

# Approved set (authority; version 1, 2026-09-15 21:37 PDT, OWNER_DIRECT)

The execution loop advances only the directions listed under "Approved", in priority order, within
the concurrency ceiling. Nothing else runs. Changes to this file are made only by an owner-triggered
Portfolio review (`decisions/2026-09-15-portfolio-control-and-approved-set.md`). Lanes and budgets
follow `decisions/2026-09-15-workflow-lanes.md`.

## Ceiling

Hub: two directions. Node: fresh admission. Empty capacity stays empty.

## Approved

| Priority | Direction | Lane | Standing budget | First object | Reopening / exit conditions |
| --- | --- | --- | --- | --- | --- |
| 1 | flexible_skill_duration | CONFIRM | one confirmatory object per seven days, sized by its card | `FSD_MATCHED_INFORMATION_BASELINE_B01` (fixed by the direction node 2026-09-16 05:19Z, option C, replacing the DM's headroom draft): standing D1280 versus a central-input flat with limited learning-rate selection, five fresh blocks at 45 rollouts, MEI .05 J, 16 fits; `headroom_record: not established` | every branch ends the object and keeps the result; CLOSE, a hazard host or further objects are recommendations for the owner's review, never automatic |

## Parked backups (pulled in only by review, in this order)

| Order | Direction | Lane on entry | Note |
| --- | --- | --- | --- |
| 1 | vap_folr_core | EXPLORE | Codex-side; operationally paused at `HANDOFF_20260915_AUGMENTATION_REPEAT_OWNER_PAUSE.md`; mixed block pattern, no signal |
| 2 | tail_return_distributional_learning | CONFIRM candidate | Codex-side; operationally paused; B01 positive retained, B02 inside MEI; Pro review of B02 never started |

## Left the set

| Direction | When | Record |
| --- | --- | --- |
| acvc | 2026-09-16 04:30Z (lane CLOSE after result review A) | `../candidates/acvc/ACVC_CLOSING_MEMO_20260916.md`; slot not refilled |

## Queued for the next review

- ACVC lifecycle: DM recommends PARK with assets retained and three reopening conditions (closing
  memo). Alternative on record: a second matched block (option B of the result review).
- Candidate additions: see the current dossier under `dossiers/`.

## Version history

- v1, 2026-09-15 21:37 PDT: initial set fixed by the owner with the control decision.
- v1.1, 2026-09-16 05:30Z: FSD first-object wording replaced by the node-fixed object (direction-tier decision; no set change).

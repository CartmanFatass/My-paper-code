# Cross-Validation Archive

Created: 2026-07-07

Purpose: append-only archive for outside advice, cross-model handoffs,
dispositions, and modification metadata. Root memory should stay focused on the
current work.

## Imported History

- Full previous cross-validation ledger:
  `memory/LTM/CROSS_VALIDATION_20260707_full_import.md`

## Entry Template

```text
### <Cross-validation ID> - <short title>

Archived:
Source:
Input artifacts:
Context:
Response status:
Response rationale:
Principle impact:
Plan impact:
Code impact:
Experiment impact:
Modification metadata:
Follow-up:
```

### CV-20260707-external-r1-r24-bridge - External Round 1 R23/R24 Disposition

Archived: 2026-07-07
Source: ExternalReviewManager handoff from archived external review Round 1
Input artifacts:
- `memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md` — Round 1, "R23 final read / R24 Assignment-to-Behavior Bridge"
- Current compact memory: `memory/CURRENT_WORK.md`, `memory/IMPLEMENTATION_PLAN.md`, `memory/ExpRecord.md`
Context:
- R23-next matrix validated q_A residual as a learnable `Z -> xi` assignment-actionability mechanism.
- The same matrix did not establish `xi -> low-level/joint behavior -> recoverable team effect`; q_D target/timescale audit was null with an underpowered caveat.
- 320k coverage differences remain treated as noise/confounding, not a task claim.
Response status: accepted with modifications
Response rationale:
- Accept the sequencing advice: R24 should first prove behavior separation with forced-xi / forced-z audits, then run a team-conditioned q_d reward-off process probe, and only then consider low-only q_d reward.
- Treat q_A as high-level validation, not full closure. Keep q_D reward, q_D coefficient sweeps, and 960k scale runs deferred until the behavior bridge is validated.
- Do not promote the external advice into a new principle yet because the active principle contract already contains the order `Z -> xi -> effect -> q_D`, and behavioral evidence is still missing.
Principle impact:
- No edit to `memory/ALGORITHM_PRINCIPLES.md`.
- Existing principle contract is reinforced, not changed.
Plan impact:
- Added "Round 24 Assignment-to-Behavior Bridge" staged gates to `memory/IMPLEMENTATION_PLAN.md`.
- Updated `memory/CURRENT_WORK.md` next actions and do-not-do-yet list around R24 sequencing.
Code impact:
- None. No code, runner scripts, packages, or logs were edited.
Experiment impact:
- Added planned dashboard row and active-detail stub in `memory/ExpRecord.md` for `EXP-20260707-r24-assignment-to-behavior-bridge`.
- R24 first owner is ExpManager for audit/probe specification and package/run handoff; no launch is implied by this memory update.
Modification metadata:
- Memory-only update by LongTimeMemoryManager.
- External review index memory decision updated from pending to accepted-with-modifications.
Follow-up:
- ExpManager should prepare the forced-xi / forced-z behavior audit spec using the q_A reward checkpoint and H={10,20,50}.
- After that, ExpManager should prepare the reward-off team-conditioned q_d process probe with full-vs-prior and shortcut baselines.
- LongTimeMemoryManager should reconsider principle updates only after R24 forced-z/q_d evidence shows persistent behavior separation.

### CV-20260708-r24-gpt-round4-null-control - GPT web continuation accepted

Archived: 2026-07-08
Source: ExternalReviewManager handoff `external-review-archive-20260708-gpt-r24-q-d-null-control`
Input artifacts:
- `memory/LTM/external_reviews/DIALOGUE_ARCHIVE.md`
- `memory/LTM/external_reviews/INDEX.md`
- `.superpowers/sdd/result-read-20260708-r24-q-d-null-control-cloud.md`
Context:
- Cloud continuation confirmed: two completed 64-env q_d reward-off seed runs (seed1/seed2) at 320k.
- Latest-step q_d residual gate failed on both seeds (`seed1` residual 0.02998 with frac 0.59066, `seed2` residual -0.01928 with frac 0.51704).
- Updated interpretation preserved: q_A supports `Z -> xi`; q_d/q_D reward remains blocked; next action is diagnostic refinement and matched-null/frozen controls.
- Branch is not abandoned; localized blocker identified as `ξ / z_i -> stable behavior semantics -> recoverable q_d residual`.
Response status: accepted
Response rationale:
- Keep gate posture unchanged: no q_d/q_D reward injection until gate-consistent q_d recovery evidence is shown.
- Preserve the distinction that `q_behavior` can be positive individual-semantics evidence without proving cooperative team semantics.
- Treat `q_pre` as a selection/history confound control rather than a pure leakage-null.
Principle impact:
- No algorithm-principle changes at this point; reinforce existing `Z -> xi -> effect -> q_D` sequencing and diagnostic-first rule.
Plan impact:
- `memory/CURRENT_WORK.md` and `memory/IMPLEMENTATION_PLAN.md` synchronized to record two-seed cloud gate-fail status.
Experiment impact:
- Confirmed: q_d/q_D reward remains blocked after current R24 q_d null-control evidence; next gate branch is matched-null and intervention-based diagnostics.
Code impact:
- None. No runner, script, or model code edits.
Modification metadata:
- Memory-only owner update by LongTimeMemoryManager for 2026-07-08 continuation.
Follow-up:
- ExpManager and ResultAnalyst to preserve the completed cloud run as mechanism evidence and continue with matched-null/frozen diagnostics before any reward-arm planning.

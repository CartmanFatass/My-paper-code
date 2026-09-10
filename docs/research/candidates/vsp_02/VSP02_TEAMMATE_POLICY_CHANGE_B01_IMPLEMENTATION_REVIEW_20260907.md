# VSP02 B01 implementation review and comparison return

**Review date:** 2026-09-07. **Direction:** VSP02. **Object:** `VSP02-TEAMMATE-POLICY-CHANGE-B01` (B/EXPLORE, prospective; no scientific invocation released).

## Integrated candidate

The configured baseline CM arm (`/root/vsp02_cm_baseline_b01`, `gpt-6-astra` / `medium`) was selected for the direction's normal implementation checkout. Its eight owned files were copied byte-for-byte from the matched comparison worktree started at source SHA `a1b8c56f2a36e2027372bf578fc2646dfd57efe9`. The implementation has 626 research-source lines (runner 32) and 336 test lines.

The source review checked the frozen code specification §§2–5 directly. The host implements fixed N=2, 16 three-step rounds over H=48, simultaneous movement/transfer ordering, old/new scripted courier targets, local 18-field observation masking, persisted round history and terminal-only completion. The learner implements the shared 18→64→64 recurrent policy, one full Adam optimizer, GAE/PPO settings, complete-episode rollout updates and independent CARRY/RESET state forks. Named RNG streams are paired across descendants and isolated from evaluation. Publication retains raw native returns, shared q0 once, partial counts, update counters, deadline status and the required primary/evaluation/figure outputs. No core, governance or runtime configuration was changed.

## Comparison return and independent checks

All five matched arms completed with source-content identity at the common starting SHA and zero scientific invocations. Independent verification ran the same pytest and engineering-fixture/readback checks against each return: baseline 15 tests, Sol 11, Claude/Opus 40, Grok 18 and omp/Gemini 14; every arm exited 0 and passed fixture/readback. Raw returns and patches remain under `temp/cm-model-comparison/20260907/batch-01/`.

Codex accounting is archived in `C:/Projects/HMASD/temp/cm-model-comparison/20260907/batch-01/outputs/codex-comparison/report.{md,json}`: baseline `gpt-6-astra` / medium used 1,639,962 total tokens and 674.959 seconds; Sol `gpt-5.6-sol` / high used 2,934,507 tokens and 1,242.481 seconds (1.789× tokens, 1.841× duration). Baseline pricing is unavailable; Sol is recorded at $3.027438. Headless wall times were Claude 1,116.25s (`claude-opus-5`), Grok 1,187.282s (`grok-4.6-build`) and omp 415.157s (`google-antigravity/gemini-3.8-flash-high`). These are task-specific observations, not a general model ranking.

The baseline is the integration candidate because it is the configured CM arm, has the smallest compliant source surface and has complete participant plus independent acceptance. The other arms remain preserved comparison evidence; their code is not merged automatically. The omp arm was not selected because its runner starts the study clock after imports and its evaluation loop does not check the deadline per environment step, both material deviations from code-spec §5. No scientific conclusion is drawn from fixture returns or completion speed.

## Integrated acceptance

In `C:/Projects/HMASD-worktrees/dm-vsp02`, after copying the baseline files, the unchanged focused pytest command passed **15 tests** (one existing `cache_dir` warning). The engineering fixture completed with seed 17, P16/Q16/E4, 48 training episodes, 48 optimizer steps, 16 evaluation episodes and 2,304 training / 768 evaluation joint steps; the unchanged raw-file readback passed and `git diff --check` passed. The fixture remains engineering-only (`scientific_comparison_complete=false`, primary delta 0.0 is not evidence).

No B01 scientific runner invocation, remote admission, UAV entry, extra seed, provider request, branch creation or source guard was added. The next route is DM/CM readiness review; only a later named execution command can release the complete 1,800-second scientific invocation under the card.


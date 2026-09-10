# VSP03 B02 — Root-owned sole invocation

Current assignment: Portfolio / `P09-VSP03-SELECTED-B02-01`, relayed by Root after the recorded pre-acceptance access failure. Root owns source integration, fresh remote admission, the one launch, observation and collection. The same CM retains technical acceptance and DM retains scientific intake. This preparation performs no SSH, admission, model construction, trajectory, evaluation or scientific invocation.

## Accepted implementation, review and currentness

Implementation, frozen card/counts and independent affected-path review were published together at **`00ebefa5823dbb41e64aed11b90ba26a8ff97020`** and are already integrated on main. The exact launch SHA remains that commit. Reuse the accepted [source record](VSP03_B02_SOURCE_ACCEPTANCE_20260907.md), [independent review](VSP03_B02_SOURCE_REVIEW_20260907.md), [card](VSP03_B02_SCIENCE_CARD_20260907.md) and [launch boundary](VSP03_B02_LAUNCH_BOUNDARY_20260907.md). There is no new implementation or review result to manufacture.

Currentness comparison against main `02728db5a385d0e7990beef3e037983bef021ecd` found no byte changes in B02, reused B01, runner, memory preflight, helper tests, frozen card/counts or independent review. Three local-Conda zero-trajectory helpers passed in 4.57 seconds; independent review found no material issue. No repeated test or fixture is selected. The implementation remains 422 non-test lines with a 28-line runner and no optional ENGINEERING_SCOPE_SPEC §4 machinery.

Authoring reuses `C:/Projects/HMASD-worktrees/dm-vsp03-p07-prep-20260907` on `codex/pro-vsp03-shared-service-convergence-20260906`. Its clean saved checkout was reattached; current committed main and the immutable remote response `a62defbbe843149c836c132d6a8f6bb5540506a2` were reconciled without rewriting history. Reconciliation head `a00fd3f894a3c3a2d126971d19538a907e80e8d2` has the same file tree as that main input. Root needs only this handoff's final documentation commit for new content; source/review commit `00ebefa58` is already present.

The [historical access receipt](VSP03_B02_REMOTE_PATH_RECEIPT_20260907.json), [technical E0](VSP03_B02_RESULT_EVIDENCE_20260907.md), [path intake](VSP03_B02_PATH_UNAVAILABLE_INTAKE_20260907.md) and superseded dispatch document stay unchanged. The only earlier access attempt was supervisor-help discovery and failed before connection; it requested no launch. This handoff does not assert that the configured route is now restored. Root makes that direct observation under the current continuation command and returns any remaining pre-acceptance gap without a fallback or duplicate.

## Exact destination and source staging

Use only `.codex/hmasd-compute.toml` node `wsl_4070`, configured SSH target `hmasd-wsl-node`, CPU float32, one compute thread, interpreter `/home/wu/.venvs/hmasd/bin/python`. Root executes these Bash commands on that configured node after integration. They do not run a learner:

```bash
git -C /home/wu/projects/HMASD fetch origin main
git -C /home/wu/projects/HMASD worktree add --detach /home/wu/hmasd-worktrees/vsp03-b02-p09-00ebefa5823dbb41e64aed11b90ba26a8ff97020 00ebefa5823dbb41e64aed11b90ba26a8ff97020
```

If the destination already exists, inspect and reuse the matching exact-SHA checkout; do not overwrite it or create an additional authoring branch. Check any authoritative supervisor state for this same handle if Root has since attempted a launch. The last known state is definitively unaccepted; an uncertain new send is resolved against the same handle before any further action.

- Handle: `vsp03-b02-p09-20260907`.
- Output directory: `/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p09_20260907`.
- Adjacent admission receipt: `/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p09_20260907_admission.json`.
- Local collection destination: `C:/Projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p09_20260907`, with the admission JSON and supervisor evidence retained beside it.

## Exact single supervisor dispatch

The existing supervisor's `agent-task run <name> <command>` interface is evidenced by the completed [UCOPE B04 execution record](../ucope/UCOPE_SHARED_DATA_RETURN_MODEL_B04_RESULT_EVIDENCE_20260907.md). This is interface reuse, not scientific evidence for B02. The following Bash block constructs a literal payload and submits it once. It preserves the independently reviewed timeout/admission/runner body; the existing `/usr/bin/time` wrapper records complete elapsed and peak RSS outside that unchanged timeout and grants no extra experiment time.

```bash
VSP03_B02_PAYLOAD=$(cat <<'VSP03_B02_LITERAL'
cd /home/wu/hmasd-worktrees/vsp03-b02-p09-00ebefa5823dbb41e64aed11b90ba26a8ff97020 || exit
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VSP03_B02_COMMAND='VSP03_B02_STARTED=$(/home/wu/.venvs/hmasd/bin/python -c "import time; print(time.perf_counter())")
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p09_20260907_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b02.py --seed 4 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p09_20260907 --started-monotonic "$VSP03_B02_STARTED" --node wsl_4070'
exec /usr/bin/time -f 'whole_wall_seconds=%e peak_rss_kib=%M' /usr/bin/timeout --signal=KILL 120s bash -c "$VSP03_B02_COMMAND"
VSP03_B02_LITERAL
)
/usr/local/bin/agent-task run vsp03-b02-p09-20260907 "$VSP03_B02_PAYLOAD"
```

The 120-second complete cap encloses the timestamp helper, immediately adjacent destination admission, imports, initialization, one eight-episode check, both learners, six final evaluation/reference executions, publication/readback and runner exit. Arms and stages do not reset the clock. There is no grace period, second invocation, separate R0 run, extra seed, pilot, retry, local fallback, recast or Pro round. No standalone focused check precedes this invocation. The timestamp and summary elapsed values are narrower than the complete-process observation.

The same CM checked this resolved handoff without editing it: both Bash blocks passed local `bash -n`, the literal quoting and unchanged outer cap had no concrete gap, and collection conditions retain the frozen outputs. Its source comparison included the actual reused `experiments/candidates/vsp_03/vsp03_b01/b01.py` dependency and found no change from the accepted SHA. This short handoff check made no remote call, admission, model, trajectory or test rerun; the original independent source review remains the review evidence.

## Acceptance and collection for return

Apply the existing card sections `Evaluation, output and reading rule`, `Counts, complete cost and stop` and `Implementation, review and execution boundary`, plus evidence spec §§4, 11.4 and 11.8.6–11.8.7. Required acceptance is concrete:

1. The actual detached cwd/source SHA and supervisor command match this handoff. Fresh admission on `wsl_4070` measures both physical and effective available memory at least 4 GiB and succeeds immediately before the runner through `&&`. Refusal constructs no scientific state.
2. Retain the accepted handle, supervisor start/status/exit and complete stdout/stderr, the outer command and wall observation, and admission JSON. Complete success requires terminal exit 0 and complete elapsed within 120 seconds; `summary.status=complete` or `runner_exit_ready` alone is insufficient. Keep all partial evidence if any selected measurement or completion is absent.
3. Complete exposure is 38920 joint episodes, 1556800 team ticks, 3113600 target transitions, two model constructions and 256 Adam steps. Each arm has 16384 training episodes, 128 updates, 128 curve rows and 2048 final evaluation episodes. The check uses eight complete episodes and zero optimizer steps. Actual valid and gradient rows remain policy-dependent and readable.
4. Collect `summary.json`, `focused_check.json`, `T_curve.jsonl`, `G_curve.jsonl`, `T_final.pt`, `G_final.pt`, `T_greedy.json`, `T_stochastic.json`, `G_greedy.json`, `G_stochastic.json`, `R.json`, `R0.json` and `paired_differences.json`. Each endpoint/contrast set has 1024 paired worlds. Retain initial, first-step and final parameter exposure, final weights and the required in-invocation JSON/weight readbacks.
5. The primary remains final update-128 greedy `T_greedy-R`; all six absolute results, R0/G comparisons and opposite-sign stochastic companions stay readable. Conditional world SD/SE is not training-population uncertainty. The independent unit is one paired training instance, seed 4; no modes, controllers or evaluation worlds become extra seeds.

Root owns launch, routine observation and collection for this continuation. Send the actual collection paths and authoritative terminal facts to the same CM `/root/dm_amx_vsp03_next/cm_vsp03_b02` for technical acceptance, then this DM for scientific intake and the Chinese brief. Raw transfer or a zero exit is not scientific acceptance. Do not overwrite the historical PATH_UNAVAILABLE evidence when recording the first actual invocation.

## Object-tier preparation decision

Options: (a) reuse the already accepted implementation/review and return the exact Root-owned handoff; (b) reopen a concrete changed-source or semantic gap. Recommendation and selected option: **(a)**; currentness found no gap. **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Owner review readback found no unapplied instruction. This is a technical handoff update within the selected object, with zero new scientific exposure and owner flag `none`; existing new-card item `20260907-vsp03-002` remains applicable. No new scientific card, direction decision or owner-console item is created.

# UCOPE B03 — implementation and objective review

**Accepted source: `70900ac7e7aa3a85b4f4ad6a2a8031ccb346fd44`.** The selected B03 amendment is implemented; the original focused directory suite passed on the configured remote node. No 7101 scientific pair or standalone smoke was launched. DM owns source/card binding and the existing Root launch route.

## Delivered change and protected boundaries

Contract: [B03 code spec §§1–6](UCOPE_UAV_MOTION_PREFIX_B03_CODE_SPEC_20260908.md) and [card §§1–6](UCOPE_UAV_MOTION_PREFIX_B03_SCIENCE_CARD_20260908.md), selected under P57. The full task/source/check set reached Root before coding. All three comparison batches were already complete; no fourth batch was enrolled.

CM reused `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, branch `codex/ucope`, starting clean at `f5230ca30537e7baa7db71ee2ba437a17efe807b`. Its relevant research source matched accepted B02 `6374063408208ba67b8cb7c69ebc0babb0f00259`. Applicable AGENTS/runtime/scope instructions were unchanged. CM retained overlapping source/test/index ownership; no authoring branch was created and no unrelated file was edited.

- `learner.py::update` now accepts `entropy_coef=0.01`; the actual objective is `policy_loss + .5*value_loss - entropy_coef*entropy.mean()`. The existing unweighted entropy measurements remain in logs.
- `study.py` derives B03 coefficient 0.0 and `agent_compound` from the named pair, declares only master 7101, and passes the coefficient to both learned-arm updates. Collector options contain only ratio grouping. Configuration/checkpoints, summary and learned-arm metadata identify the actual coefficient, B03 object/card and real section 5.
- The existing runner supports `--pair b03`, refuses wrong real masters and rejects B03 aggregation before input-file/workload access. Direct `aggregate(..., pair='b03')` also refuses this single-pair operation. No new aggregate implementation or CLI coefficient sweep option exists.
- Existing synthetic capability retains fixture master/mode and a truthful B03 code-spec §4 label; it is not accepted as real B03 evidence. No standalone fixture was run.
- Focused test changes are `test_pair_plumbing.py` and new `test_entropy_objective.py`. Policy/sampling/density, environment, adapter, reward, critic architecture/targets, recurrence, masks, default clipping, FP32, RNG streams, Adam/counts and final sampled primary are unchanged. Historical p21/p24/b02 routes retain coefficient 0.01.

Engineering scope §4: **none**, per card/code spec. Non-test diff is **+31/−11 lines**; runner is **54 lines**. This is one scalar objective/identity change, not a new learner, framework, configuration registry, profiler, telemetry system or launch guard. No dependency or security/configuration change occurred.

## Committed-source remote acceptance

Code/tests were explicitly committed and immediately pushed before remote execution. The accepted commit's tree is `13634a339b2d6e323238a46feac29f443d022b8e`. A detached **test execution** worktree was staged at `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b03-p57-check-20260908` on `hmasd-wsl-node`; this is not an additional authoring checkout or accepted scientific launch.

Existing remote objects were enumerated without an implicit fetch. Only 48 missing committed objects were carried over the existing authenticated SCP route in a 166712-byte pack, SHA-256 `33ddfa66958edf68da971360f257adf5cee822c0f87182a43456ccf4d83e9bc2`. The remote digest passed before indexing. Exact HEAD/tree and a clean checkout were checked, and all five changed code/test files were materialized with blob bytes matching the local committed source. No uncommitted working-tree content was staged.

Receipts remain under `temp/directions/ucope/test/b03_p57_check_20260908/` in the authoring checkout: `staging-inputs.json`, `stage.sh`, `stage.stdout.txt`, `stage-receipt.json`, `suite-launch.sh`, `suite-launch-receipt.json`, and `supervisor/{runner.sh,task.log,status,exit_code,start_time,pid}`. Staging exited 0 in 0.828 seconds. Source-carrier and raw receipts are retained; their cleanup is not a launch condition.

One configured `agent-task` supervisor, **`ucope-uav-motion-prefix-b03-p57-check-20260908`**, ran the original directory suite at the exact committed source:

```bash
cd /home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b03-p57-check-20260908
/home/wu/.venvs/hmasd/bin/python -m pytest tests/experiments/candidates/ucope/uav_motion_prefix_b01 -q
```

The stored supervisor command wraps that complete check with `/usr/bin/time` and `/usr/bin/timeout --signal=KILL 300s`; no scientific admission or runner invocation is part of it. Terminal facts: **finished, exit 0, PID 2852234**, start `2026-09-09T04:31:46+08:00`, end `2026-09-09T04:31:48+08:00`, tmux inactive. Raw result: **61 passed in 1.86s**, complete process wall **2.30s**, peak RSS **529392 KiB**. One suite was executed; there was no failure, correction rerun, standalone smoke, warm-up, profile or scientific pair. Aggregate CPU was not measured and no CPU-budget claim is made.

The focused evidence establishes:

1. The **actual update** executes four Adam steps on fixed tensors for coefficient 0, explicit 0.01 and omitted/default coefficient. First pre-global-clip gradients match an independently formed native policy/value gradient minus the selected coefficient times the actual entropy gradient. Both Gaussian log-std and nonuniform categorical-duration entropy derivatives are exposed; zero coefficient removes those explicit contributions while native log-std/duration policy gradients remain nonzero. Loss logs obey the selected objective, entropy remains unweighted descriptive output, and default/explicit 0.01 updates agree. Update RNG state is unchanged.
2. Fake-workload CLI/Config/study tests trace 7101's initialization/reset/action domains, 512 training episodes per learned arm, all 32 final reset associations per T/G/H, and 256 update calls per learned arm. Both B03 updates receive 0.0; the collector never receives `entropy_coef`. Saved configurations and summary/arm metadata agree. Synthetic mode remains synthetic.
3. B03 direct/CLI aggregate refusal occurs before input access. Wrong real masters are refused before workload. Existing joint/agent clipping, held-row scale, old/new detachment, information/reward, recurrent/chunk, initialization, real synthetic update counts, historical aggregation, primary/dependency and clock/cap tests remain covered.

The tensor/synthetic suite establishes these affected implementation boundaries. It does not measure a B03 UAV endpoint, 7101 wall time, native gain or training-population uncertainty.

## Independent review and return

The existing configured `hmasd-reviewer` child **`rv_ah_ucope_b02_credit`** was reused for this closely related objective review. It inspected the actual committed diff and complete B03 contract without edits, index operations, duplicate learner execution or a new literature review. Its final return found **no material findings**: coefficient 0 is common to both B03 updates, collector options remain grouping-only, defaults retain 0.01, native duration/log-std credit and masks are preserved, and single-master/refusal/identity paths conform. Scope review found no §4 addition. The reviewer independently read the [terminal suite log](../../../../temp/directions/ucope/test/b03_p57_check_20260908/supervisor/task.log), confirmed 61 passes /1.86s and full wall 2.30s /exit 0 at the reviewed source, and requested no repair. This section preserves its final independent technical review; it makes no UAV-performance or scientific-validity claim.

CM's technical acceptance rests on the committed diff, actual-objective/default/plumbing coverage and independent review. No runtime source patch or scientific selection followed from B02's negative outcomes. The historical **80.578s/60s B02 smoke breach**, P48 disposition and earlier wrong-cwd/pre-admission failure remain unchanged; B03 does not retrospectively make that smoke conforming.

Per-arm future cost context remains card §6: unchanged complete loop, existing B02 references approximately 138.26s T /137.54s G, and no added dominant work from scalar bonus removal. Those are projections, not observed 7101 timing. Existing publication code plus focused checkpoint/summary wiring checks cover the affected post-learner path; no extra smoke is required.

After DM binding and Root integration, the existing P57 route permits **one** 7101 T/G/H pair at most: 286720 native team steps, 2048 Adam calls, 96 final episodes, 1800 seconds per complete learned arm and 3600 seconds through complete pair publication/exit, with fresh actual-node admission. Root owns that exact-source scientific staging/launch/observation; CM retains terminal collection and DM all-outcome intake. No retry, second pair, extra evaluation or further scientific allocation is implied by this acceptance.

# UCOPE UAV motion prefix B01 — P21 readiness intake, 2026-09-07

## 1. Current assignment and accepted boundary

[P21 UCOPE](../../portfolio/handoffs/2026-09-07-p21-fsd-ucope-frrie-continuations.md#ucope--accepted-uav-b-implementation-through-two-fixed-pairs), source `d3f03ffa4`, allocates the exact two fixed pairs from the [science card §§2–6,8](UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md). The full [Pro direction decision III–VI](pro_packets/20260907_uav_interface_convergence/archive/RESPONSE.md) remains immutable at `426513b18b38b477dd255b3e8524424d8deb8a19`; [its accepted intake](UCOPE_UAV_INTERFACE_CONVERGENCE_INTAKE_20260907.md) remains the family-opening interpretation. This is a B/EXPLORE execution continuation, not a new family, promotion, recast or Portfolio disposition.

The existing baseline CM committed `78dd2a461e838b9d863b81ed9e2d5946d011f33a` in the designated checkout `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, branch `codex/ucope`, before this continuation. At resume, the tree was clean. P21 inputs were merged and pushed at `cfc3fce13`; two append-only audit conflicts were resolved retaining every row, with the resulting audit bytes exactly equal to the P21 input. All seven accepted UCOPE code/test files were preserved. Card §8's current allocation was committed/pushed at `536949660fee3ab9ac92aba29c2c0455ffe9f6e1`.

P15's zero-UAV boundary remains historical at its frozen revision. P21 supersedes it only for **master6801 then master6802**, each a serial **T → G → H** invocation. The second pair follows the first's technical acceptance regardless of its score. Each learned arm retains 131,072 training team steps and 1,024 Adam calls; T/G/H each receive 32 final sampled evaluation episodes. Fixed five UAVs, CPU FP32 learner, one scientific process/thread, common information permissions and RNG domains remain unchanged. Complete caps are 1,800 s per arm, 3,600 s per pair, 7,200 s summed, with H/pair publication inside G and startup/common initialization inside T.

## 2. What was checked and what it establishes

The applied rule is evidence-spec §11.8.6, verbatim: “Use existing trustworthy paths and checks where applicable. Add one focused verification for changed behavior and primary output; do not repeat smoke merely because a launch boundary occurred.” Section 11.4's common integrity, real-learner counts, actual-node resource admission and machine-generated exposure line remain the only B launch conditions. A real UAV run remains necessary for empirical B evidence; source/fixture success is engineering evidence.

I inspected the actual accepted factory and feature/reward/hold implementation in `environment.py`, episode collection boundaries in `learner.py`, and primary/aggregate arithmetic in `study.py`. These checks were confined to the card's changed scientific boundaries:

- The lazy real constructor names the selected unchanged `MultiUAVEnv`/`ParallelToArrayAdapter` and all fixed parameters. The 108-component actor retains own local observations, prior command and own remaining hold; the 136-component critic normalizes current state/earlier commitments separately, before current decisions.
- Native reward is the sum of the five returned per-agent rewards, not the adapter's additional average. Opening d=4 repeats one actual velocity through t=3; free observations and every actor's recurrent state advance at all primitive steps. Held commands add no fresh likelihood samples.
- Complete episodes retain native reward sum, time average, prefix/suffix returns, exposure and selected source-index diagnostics. Episode-end return targets do not cross reset. Source-index diagnostics are read before the associated action's environment step and never enter actor features.
- Final T−G and G−H differences are formed from matched complete episode IDs. Aggregation uses two training-pair endpoints, their sample SD and conditional whole-episode evaluation SE; incomplete T/G, H and diagnostics retain separate dependencies. No score selects a checkpoint, seed or new run.

I retained the existing CM-owned independent review `/root/ucope_cm_baseline_b01/integration_review`, which covered all seven changed files against CODE_SPEC §§2–8/card §§2–5 and the affected base/adapter interfaces, and reported no material finding or unrequested §4 machinery. The accepted additions are 785 non-test source lines, including a 48-line runner, plus 377 test lines. No ordinary code review or test suite was commissioned again solely because P21 released execution.

The original independent raw evidence at `C:/Projects/HMASD/temp/cm-model-comparison/20260907/batch-03/independent_verify/baseline_final/` was read: `status.json` records pytest/fixture exit0; `pytest.txt` records **12 passed in 4.34 s**; the fixture summary/episode rows record **32 training + 48 evaluation = 80 synthetic team steps, eight actual optimizer calls, four training/six evaluation episodes, 100 diagnostic frames, ten complete episode rows and zero scientific UAV calls**. Primary/hover are complete, with no recorded limits. Synthetic return values remain test data, not native UAV evidence. No parameters/checkpoints were loaded during this DM readback.

The existing [machine-computed exposure/work facts](UCOPE_UAV_MOTION_PREFIX_B01_PREPARATION_FACTS_20260907.json) are unchanged: G=66,311/T=66,441 trainable parameters, positive lr3e-4, 1,024 prescribed Adam calls per real fit; four fits/524,288 training team steps plus 49,152 evaluation team steps, total **573,440 team steps/2,240 episodes**. Actual parameter displacement and real counts must be read from the eventual runs. No new runtime forecast is inferred from the fixture or B05's finite-host wall time.

## 3. Decisions this readiness intake produces

**Object/technical options:** (a) accept the existing card/code correspondence and original independent evidence, use P21's exact allocated two-pair route; (b) return a concrete source/command defect to the same CM; (c) return a frozen-meaning conflict through Root. Recommendation: **(a)**. No source-level scientific conflict was found in the checked boundaries; metadata-only runtime compatibility and fixture evidence do not answer native performance, but they do not create an extra prelaunch pilot requirement.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Card §8 records the present release; the same baseline CM supplies exact committed command/handle/output bindings and remains responsible for collection/technical acceptance. Root alone performs actual-node admission, detached launches and observation under the named route. Technical acceptance of6801 releases the already allocated6802 without reading its sign as a gate. Cap/nonfinite/integrity failure stops its dependent route and returns the bounded facts; there is no retry, extra seed/evaluation, automatic cap increase or fallback.

This is an existing baseline continuation/correction path after completed comparison batch03; all three requested batches are already completed. No new coding assignment is silently excluded or enrolled, and no comparison scientific invocation exists. Ordinary command/integration facts stay in Root's log; this completion asks Portfolio for no extra decision.

Live-main owner reviews were empty at **2026-09-07 20:54:14 PDT** and the final **21:04:17 PDT** boundary, with no UCOPE audit owner override. The original card predictions remain recorded and the owner prediction slot remains **not taken (unattended)**; no real result was supplied to score them at readiness. Ordinary technical readiness has no separate P1/P2 item or valid-result brief. The current card's owner item remains `20260907-ucope-009`; subsequent valid-result intake will supply the Chinese brief, prediction score and audit.

## 4. Execution binding and remaining scientific limits

The complete [CM Root handoff](UCOPE_UAV_MOTION_PREFIX_B01_P21_ROOT_HANDOFF_20260907.md) was committed/pushed at **f894168c674554cdec5754f6eb7a7f6351211066**. I read its entire binding, staging and two launch literals against the card and accepted source. The execution SHA is **536949660fee3ab9ac92aba29c2c0455ffe9f6e1**, with the seven source/test paths unchanged from accepted `78dd2a461`. No correction or repeated learner check was needed.

| Binding | Value |
| --- | --- |
| Execution node / interpreter | `hmasd-wsl-node` / `/home/wu/.venvs/hmasd/bin/python` |
| Detached cwd | `/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p21-20260907` |
| First prospective supervisor name | `ucope-uav-motion-prefix-b01-6801-p21-20260907` |
| Second prospective supervisor name | `ucope-uav-motion-prefix-b01-6802-p21-20260907` |
| Scientific outputs | `temp/directions/ucope/exp/uav-motion-prefix-b01-<master>-p21-20260907/` relative to that cwd |
| Fresh receipt | `resource_admission.json` in each output directory, assessed before the runner and joined to it by `&&` |
| Runtime observation / technical acceptance | Root / existing `/root/ucope_cm_baseline_b01` |

CM observed the proposed cwd/handles absent and syntax-checked the five Bash blocks without executing them. Its optional remote commit-presence read stalled and was cancelled; this is a limited read result, not failed scientific execution or a native negative. The published staging block explicitly fetches the pushed branch and creates the exact-SHA detached cwd before launch, resolving source materialization through Root. The literal's external 3,600 s bound includes admission/interpreter startup and complements the existing per-arm internal clocks; no grace computation or new runtime machinery is added. Paths and names remain prospective until Root reports acceptance.

A prepared command, code acceptance or supervisor intention is not actual UAV entry. Actual entry requires the accepted scientific invocation and observed UAV execution, traced to card §8 and the immutable Pro direction decision. Root observation does not relaunch a process, and CM collection does not change its scientific budget. This readiness decision is appended to [the audit](../../portfolio/audit/2026-09-07.md#ucope-p21-uav-readiness--2026-09-07); the original direction/Portfolio dispositions remain unchanged.

The claim ceiling remains preliminary performance of these fitted control packages on this fixed task/budget. B05's two finite-host acquisition gains motivate the question; B04's harmful acquisition/native negative endpoint, B01 nulls and older competence limits remain the strongest contrary evidence. They are not pooled with UAV results. Geometry, time structure, optimization and ordinary feedback remain alternatives to an information-specific effect. Missing or adverse G−H limits a competent-generic interpretation; favorable local observations/actions cannot offset native return loss.

Real UAV binary/runtime conformance, complete-cap feasibility, learned generic competence, headroom and both native endpoints remain unmeasured at readiness. The next scientific discriminator is the prescribed two real pairs; any damaged dependent claim will be identified from actual counts, outputs and receipts, retaining independently trustworthy narrower facts. No successor or promotion is selected here.

# ACVC_CLUSTER_FIXED_RECIPE_C01 — six prospective fixed1024 programmes

## 1. Authority, decision and claim

The complete [Portfolio decision](../../portfolio/pro_packets/20260914_acvc_post_paired_direction/archive/RESPONSE.md) at `902df04e46a4cea8fe788baed14ca8c447cf18ea` was read and applied in the [full DM response](../../portfolio/pro_packets/20260914_acvc_post_paired_direction/INTAKE.md) at `943626ecfc4bb7c4f66ef640df3525f12eec4308`; canonical main application/release is `bccf4941a717e98a258fc6e2050a98465b7e9d9a`. ACVC remains CONTINUE / MEDIUM / recasts2 in its existing slot. This card executes the unique selected six-programme objective, not a new Portfolio request.

Question: under the prospective clustered training/evaluation law in section3, does the complete fixed F execution package have expected final J increments greater than .01 over both C and own-predicate dwell? One fit plus its finite final panel is one independent sampling unit. Evidence class: **C-BENCH, provisional single-task inference qualified by the prespecified iid-normal working model for complete fit-panel contrast means**. Actual neural-training coverage/calibration is not established. No default deployment, all-world safety, isolated retrace/history cause, tuned headroom, transfer or formal-UAV claim follows.

Options for the remaining DM design choice: (a) the declared iid seed-pair law and two simultaneous working-model t intervals; (b) six complete programmes reported descriptively without the expected-increment interval; (c) a different prospectively justified estimator. Recommend/select(a): it directly addresses the selected expectation question while exposing model dependence, using the already understood C01 inferential form with the new population, six units and df5. No new calibration, normality or power pilot is needed. A failure of its assumptions/precision narrows the result; it does not justify automatic extra sampling.

Owner-delegated decision (unattended, 2026-09-03 instruction): freeze this six-programme design and its first outcome-blind draw, then implement and execute within the applied Portfolio scope. Owner prediction: not taken (unattended).

## 2. Protected native task, learner and private execution

Reuse the complete real learner and action/information semantics from [longer-C B01](ACVC_CLUSTER_LONGER_C_B01_SCIENCE_CARD_20260914.md), its accepted source `914a3d0e78d49d385c54aaec0776ead63712b624`, and current unchanged shared runner `scripts/run_acvc_fresh_dense_reuse_b01.py`. The new code changes only explicit object/unit identities, new m/q mapping, fixed1024 orchestration and complete six-unit inference. `experiments/candidates/acvc/cluster_deployment_b01/protocol.py::make_cluster` changes the existing native environment's user_distribution to cluster; its world-generation and observation/reward/action definitions are unchanged.

Five UAVs, fifty clustered users, H256, area1000, altitude50–150, speed30, bandwidth20e6, base-station power30, current20-user/10-UAV observations, existing normalization/cache/vectorized SINR; no paper-reward, FDMA, shadowing or information change. S is the full native team reward sum and J=S/256. Private GRU64 actors and training-only critic remain CPU FP32, Torch intra/inter-op1 and numerical library threads1. Preserve constructor ordering, all overwritten initialization draws, optimizer/replay/GRU state lifetimes and proposed-versus-actual action feedback.

Each unit is one new C-only fit of1024 complete256-step episodes in512 successive two-episode rollouts, four full-rollout PPO epochs and2048 persistent Adam/backward calls. Preserve the existing gamma-one Monte Carlo/no-GAE returns, detached population-SD advantage standardization, compound-three-coordinate per-agent likelihood, agent clipping[.8,1.2], five-surrogate sum/team-row mean, critic coefficient.5, entropy.01, replay chunk32/detached chunk starts, gradient clip.5 and Adam lr3e-4/betas(.9,.999)/eps1e-8 without decay/amsgrad/foreach/fused. No initial-return panel, midpoint snapshot/evaluation, fitted F/dwell arm or fit-quality gate.

Save only the fixed final actor/critic checkpoint after update2048. Evaluate C, F, dwell in that order, each with its own freshly loaded base, private five-GRU state, cue/proposal/actual-action history and environment. Each receives all64 matched exogenous world/reset addresses and inherited private random-stream law. Histories, triggers, interventions and trajectories evolve separately; there is no forced matched dose or shared recurrent state. F uses the unchanged legal own-history cue-loss/away predicate and clipped negative prior-displacement/30 command; dwell uses that same predicate definition on its own trajectory. C's bypassed cue counters are unmeasured incidence.

Each unit runs in a fresh process with independent model/optimizer/replay/runtime RNG state. No checkpoint, trained prefix or mutable state is reused across units.

## 3. Prospective iid sampling and fixed identities

Before any new learning/evaluation, draw six iid pairs in unit order1–6 using twelve sequential standard-library OS-backed uniform-integer calls, m_i then q_i:
`m_i = 10000 + secrets.randbelow(10000)`;
`q_i = 20000 + secrets.randbelow(10000)`.
Sampling is **with replacement**, without identity rejection, outcome screening or redraw. Repeated numeric pairs are allowed sampling outcomes; distinct unit indices/processes/output directories preserve separate draws and state. Do not deduplicate seed values or key identity only by master. The domains are separate from the completed clustered B masters21457/21493/21937/22319/22591 and their31457/31493/31937/32319/32591 evaluation roots. The old uniform C01 used these ranges for a different population; none of its fitted states or outcomes enters this new study.

The implementation population is the product of these declared M and Q laws through the unchanged seeded clustered learner, native-world and private-proposal mapping. Evaluation averages the fixed64 indices e=0–63 within each sampled q; equivalently the target also averages a uniform index on that panel. Independence follows the prospective independent pair draws and separate process state under this mapping, not merely distinct displayed seed labels. Usual seeded-PRNG interpretation and the working normal model remain assumptions.

Inherited training reset:100000*m+1000+episode for episode0–1023; evaluation reset:100000*q+2000+e for e0–63. Preserve the shared actor/velocity/rollout/proposal/constructor RNG consumers of m and q without changing their offsets or order. The domains keep all inherited uint32 seed addresses below2^32.

The first twelve returned values must be written immediately to `ACVC_CLUSTER_FIXED_RECIPE_C01_PROSPECTIVE_FACTS_20260914.json`, before later configuration checks. The actual fixed ordered pairs and computed work are appended below before implementation dispatch. This is configuration sampling, with no model/environment creation or runtime scientific RNG use.

## 4. Estimands, joint uncertainty and frozen reading

For Q in C,dwell, each complete unit i gives
`D_iQ = fmean_e(J_i,F,e - J_i,Q,e)` from all64 worlds.
Use `mean_Q=fmean_i(D_iQ)`, sample `s_Q=statistics.stdev(D_iQ)` over all six complete units, and `SE_Q=s_Q/sqrt(6)`. Units are equally weighted, regardless of their performance or within-unit precision. Finite evaluation noise is already included in unit variance: do not subtract it or add it a second time. Keep each unit's paired64-world conditional SD/SE and all individual contrasts descriptively.

For each primary, the prespecified interval is `mean_Q ± scipy.stats.t.ppf(.9875,5)*SE_Q`. The executable local SciPy1.15.2 calculation gives critical value **3.1633814497486235**. The two 97.5% two-sided marginal intervals provide at least95% simultaneous coverage **only under the expressly assumed iid-normal model for each complete fit-panel contrast mean**; the two contrasts may depend through shared F. Six fits, favourable signs or many worlds do not verify this working model or actual neural-training calibration. Do not multiply contrast probabilities. No alternative/bootstrap interval is selected after outcomes.

If a primary has zero observed between-unit SD, retain its point estimate and all observations but report `ZERO_VARIANCE_UNRESOLVED` with no inferential interval/strict pass; no variance-floor or zero-width certainty is invented. This is a prespecified inference limitation, not a launch gate or reason for an extra fit.

For a finite nonzero-SD component: upper<0 means `BELOW_ZERO`; otherwise upper<=.01 means `AT_OR_BELOW_MEI`; lower>.01 means `ABOVE_MEI`; otherwise `UNRESOLVED`. No rounding precedes the comparisons. Joint `JOINT_ABOVE_MEI` requires both lower bounds strictly>.01 with available intervals. Otherwise the complete study is `JOINT_NOT_ESTABLISHED`; missing/incomplete units give `INCOMPLETE` with no six-unit interval. A non-pass is not equivalence or proof of universal failure. Dwell−C is a descriptive secondary.

Report both estimates/intervals, every unit mean, absolute C/F/dwell, complete training curves/update records, all64 per-unit paired vectors and adverse/favourable/zero identities/extrema, independent-unit assumptions, development-selection history and costs. Preserve intact negative/extreme units. All older clustered B endpoints, paired snapshots and uniform C01 are excluded from the six-unit sample.

Permitted passing wording: under this declared fixed1024 clustered training/evaluation law, F has provisional model-dependent support for expected complete-package increments>.01 J over C and own-dwell using the prespecified iid-normal complete-fit-panel model and simultaneous t intervals; actual neural-training calibration is unestablished. This does not certify tail acceptability or turn F into a default.

DM judgmental forecasts, conditional on a technically complete six-unit study: P(F−C strict interval pass)=.80; P(F−dwell strict pass)=.60; P(joint pass)=.55. P(all six original units technically complete)=.90. These are not computed power or calibration evidence. If the study is incomplete, only the completeness forecast is scored; conditional interval forecasts are not scored as failures.

## 5. Finite work, resources and stopping

Each unit:1024 training+192 final evaluation=1216 episodes;262144 training+49152 evaluation=311296 team ticks;2048 Adam/backward calls;one final checkpoint/three loads/four environment constructors. Six units:6144train+1152eval=7296episodes;1572864train+294912eval=1867776ticks;12288updates;six checkpoints/eighteen loads/twenty-four constructors. No midpoint/initial panels, policy search, separate F/dwell fit or additional scientific validation invocation is selected.

The measured longer-C final-only unit gives296.30s per-unit native reference and1777.8s summed reference for six, not an elapsed guarantee, scaling result or complete cost. Ordinary planning estimates are500s per unit,3000s summed native and4800s support,7800s combined; they are DM plans, not owner caps. All actual native wall/CPU/peak RSS and support invocations are retained, with unknown lifetime/provider/agent costs kept UNKNOWN. A prospective planning revision may not change a running frozen exposure or count.

Run the six original unit invocations in fixed order, without an efficacy or futility decision between them. A poor/negative/extreme but intact unit receives every panel and remains in the primary. Unit-local failure is preserved; continue independent remaining preselected units if scientifically unaffected and freshly admitted. A concrete shared integrity fault holds only affected work until the DM resolves the dependency. No seventh/replacement fit, scientific retry, changed seed, best endpoint, dropped unit, missing-as-zero value or successful-survivor interval belongs to this allocation. All selected unit identities remain represented even if unexecuted/incomplete.

A valid complete six-unit result consumes this frozen C object regardless of polarity or interval precision. Incomplete evidence neither consumes C nor rejects the hypothesis; retained narrower facts remain labelled and no new invocation is automatically authorized. Existing archived records may be recovered/analysed without new scientific exposure. A new scientific repair/object must be separately and prospectively defined under the actual authority.

Use remote-first exact committed source on hmasd-wsl-node, detached worktree and configured agent-task supervisor. Fresh adjacent physical/effective memory>=4GiB admission precedes each actual unit invocation. CPU portability is prospectively declared; local fallback only if no remote unit was accepted, the remote exact source cannot run or fails fresh admission, and local fresh admission passes, without any scientific-semantic change. Never migrate a live process.

Each complete unit's process-relative safeguard is1800s from first import/start through learning, evaluation and publication; the outer supervisor command uses1860s TERM/+10s KILL. These are ordinary watchdog plans, with the full1024/2048/192 scientific endpoint fixed. Do not restart a watchdog per phase or infer a resource cap from500s planning. Resolve an unexpected terminal/publication contradiction from actual complete records, not a blind relaunch.

## 6. L0 engineering scope and acceptance

Deliverable: one exact-index runner for each selected unit and one six-unit all-record reducer implementing section4, plus the existing detached launch method. Reuse checkout `C:/Projects/HMASD-worktrees/codex-acvc`, branch `codex/acvc`; current baseline `943626ecfc4bb7c4f66ef640df3525f12eec4308`. DM retains science, Git, engineering acceptance and launch.

Owned new paths: `scripts/run_acvc_cluster_fixed_recipe_c01.py`; `experiments/candidates/acvc/cluster_fixed_recipe_c01/{__init__.py,protocol.py,launch.sh,.gitattributes}`; `tests/experiments/candidates/acvc/cluster_fixed_recipe_c01/`; and `docs/research/candidates/acvc/evidence/cluster_fixed_recipe_c01_20260914/engineering_check.txt`. Existing learner/collector/environment/binding and earlier C/B protocols are read-only references. Do not modify old results, C01 or shared numerical helpers. If a concrete shared change is required, return the exact dependency to DM.

The runner takes --unit in1..6, output, launch-sha and execution-seconds, maps by unit index to the frozen m/q pair, and calls the existing full `run` with make_cluster, train_episodes1024, C training and C/F/dwell final arms. Object/card/mode/planning metadata are explicit. Record unit index without re-keying by master. Use existing clustered final-panel publication and include its final metadata/readback within the process-relative safeguard. The unit must refuse prior output reuse; output is `.../cluster_fixed_recipe_c01_20260914/unit_01` through unit_06. The same m/q sampled twice would still have different indexed output/process state.

The reducer accepts exactly the six indexed units and the bound launch SHA. Verify object/unit/m/q/configuration,1024 ordered training identities/reset law,2048 ordered four-epoch updates, all192 uniquely paired finite evaluation rows, checkpoint/fit/count completeness and protected1024 clustered semantics. Require all six accepted complete original units for inference. Retain all unit facts/issues and derive each contrast directly from recorded J; no survivor or seed-deduplicated substitute. Use standard SciPy t quantile and statistics or equivalent float64 reductions with the frozen df5/n6 law. Keep population/joint wording qualified.

Engineering Scope section4 additions: **fixed unit/complete-primary validation, original-output refusal and complete-invocation timeout, only for this card's actual identity, inferential completeness and one-invocation boundaries**. Reuse existing checkpoints/admission/supervisor; no new scheduler, retry/resume/lease/provenance framework, cache, process pool, profiler or validator service. New research code<2000lines, each runner<600; one bounded focused synthetic check batch within the existing research-directory300s check limit. Native/model/power pilots and extra evaluation are excluded.

Acceptance covers actual m/q/index routing, fresh full-run arguments/unchanged helper semantics, all six units including repeated numeric identities, df5/sqrt6 and simultaneous conjunction, zero-SD/threshold/adverse/incomplete handling, complete row/rollout identities and refusal/timeout/publication. Reuse the existing stub orchestration style; no real model/environment/learner invocation in tests. Do not rerun passed checks absent an actual new change/failure. Use the scientific Python3.10, PYTHONDONTWRITEBYTECODE=1 and exact invocation-owned temp/ scratch, no cache. The creator owns retained diagnostics and safe exact cleanup under tests/AGENTS; policy rejection is recorded and never bypassed.

An optional native Sol/medium Implementer owns this complete code/check batch; a separate Sol/high Reviewer with independent context reviews the full high-risk diff and reachable RNG/numerical/primary path under current Engineering Scope7.3. DM resolves material findings and accepts exact bytes. No new CM layer, scientific delegation or Root permission is created.

## 7. Execution, observation and scientific intake

After the frozen draw and source/technical acceptance, commit/push before any remote preparation or launch; append exact source SHA, declared source paths, commands and run roots. Every unit uses the same accepted source surface in a detached exact-SHA worktree and one original handle. Native monitor: one new batch-scoped Luna/low child, reused within these six units, with direct MONITOR_ADOPTED for accepted handles and direct terminal returns to this DM. No old-batch child or duplicate observer is reused.

DM collects and verifies each original unit before proceeding in the frozen order, without an efficacy selection. Once all six original units have been addressed, run the recorded-data reducer, preserve every raw output/checkpoint/supervisor record and cost, write complete E0/intake/Chinese brief and obtain one meaningful complete independent scientific review. Read/respond to all material findings before dependent claims are accepted. Future direction development is reported from the actual result; no automatic next study or PARK is pre-applied.

Scientific-reading basis: empirical spec5.3 and11.4/11.8–11.10, FOUNDATIONS6 and 04_EMPIRICAL distinguish programme/world/snapshot dependence, package versus component effects and working-model qualification. The current Portfolio answer chose six because the next information concerns same-recipe future programmes. These principles supply neither a universal seed quota nor verified normality. No new literature premise or framework is needed.

## 8. First prospective draw and source binding

The exact first draw, timestamp, twelve values, inherited address ranges and work are to be recorded immediately below and in the prospective facts before implementation begins. No new scientific invocation exists at initial card authoring.

The first and only draw completed at **2026-09-14T17:22:32.036382+00:00** and was persisted before domain/work checks. The six actual pairs happen to be distinct; no identity test selected or rejected them. [Prospective facts](ACVC_CLUSTER_FIXED_RECIPE_C01_PROSPECTIVE_FACTS_20260914.json) retain the original order, full address ranges, work and the separate quantile calculation.

| Unit | m | q | Output suffix |
| --- | ---: | ---: | --- |
| 1 | 13783 | 22845 | unit_01 |
| 2 | 17291 | 22568 | unit_02 |
| 3 | 14179 | 21574 | unit_03 |
| 4 | 13325 | 26056 | unit_04 |
| 5 | 11751 | 28453 | unit_05 |
| 6 | 17639 | 20217 | unit_06 |

These exact indexed values and sections1–7 are now scientifically frozen before implementation. Source acceptance/launch SHA remains pending; no native scientific invocation or extra sampling has occurred.

## 9. Prospective operational watchdog clarification before execution

Independent engineering review found that the reused fitter cancels its SIGALRM before its own summary publication. The first corrective wrapper repaired final readback/inference acceptance and CPU measurement, but rearming after the fitter returns does not enforce the deadline during that inherited publication. Before any scientific unit exists, DM selects the existing GNU timeout mechanism directly around the Python process: `time ... timeout --signal=TERM --kill-after=10s 1860s timeout --signal=TERM --kill-after=10s 1800s python ...`. The1800s deadline covers the complete Python invocation from before interpreter entry through all publications/readbacks and immediate process exit;1860s remains the outer backstop. In-process elapsed/readback checks and successful-exit/native-resource validation remain, with native wall/user/system CPU/RSS retained. The same independent Reviewer assessed this concrete arrangement as resolving the operational gap without changing healthy-run semantics.

This explicitly clarifies the ordinary complete-invocation watchdog implementation prospectively under the DM's runtime-plan authority; it does not amend1024training/2048updates/192evaluation, unit identities, estimands, inference, missing-unit rules or the six-original-invocation allocation. No shared learner source change, timer thread, scheduler, extra fit or retry is introduced. An interrupted summary may be partial; original episode/update/checkpoint/log/resource evidence is retained, with incomplete inference as specified. Exact final implementation/check acceptance and launch SHA are recorded in the intake after they exist.

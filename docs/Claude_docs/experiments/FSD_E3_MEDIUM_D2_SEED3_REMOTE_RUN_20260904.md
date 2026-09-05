# FSD E3 medium D2 seed 3 attempt 01 â€” remote run record

Status at initial acceptance: **running, terminal acceptance pending**. Exactly one invocation
was accepted. This record establishes launch conformance only; it supplies no scientific outcome,
paired gain or E3 branch. DM owns scientific intake after technical collection.

## Engineering contract

Binding card: `docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`.
Prospective continuation: `FSD_E3_MEDIUM_D2_SEED3_CONTINUATION_INTAKE_20260904.md` in the same
directory, committed and pushed at `31bfecd79fc0f708546786ee26dfd8faa9e85dfb`.
The owner resumed automatic research and the old safe-drain hold is superseded.
At intake 11/18 cells were valid, zero running, seven never launched; this is only the next cell.

Question: policy-gap interruption at c=0.25 under heterogeneous hazards versus the competent
same-information best fixed clock. H1 predicts actionable regional event-linked renewal; H0
predicts weak event alignment and no advantage; optimizer variation and team interference remain
competing explanations. This B/EXPLORE cell is preliminary mechanism evidence on the declared
corridor only. No E3 aggregate is formed until all 18 cells are valid. No transfer, retuning,
new mechanism, numerical repair, local fallback or successor launch belongs to this slice.

Owned tracked path: this document only. CM worktree:
`C:/Projects/HMASD-worktrees/cm-fsd-medium-d2-seed3-20260904`, branch
`codex/cm-fsd-medium-d2-seed3-20260904`, created from the prospective SHA above.
Ignored collection belongs under `temp/directions/flexible_skill_duration/exp/`.
The saved checkout and unrelated DM/Root changes are untouched.

Engineering scope section 4 additions: **none**. No source edits, orchestration, retry, resume,
guard, telemetry, queue, new supervisor or repeated suite. New research code/test lines: zero.

Frozen cell:
- Medium hazards (0.005,0.10), Delta 0.6; N6, three pinned agents per region; K2/Z4/H400;
  Bernoulli rho0, no probe/coupling; continuous two-vector action decoded by argmax.
- D2 costs c=cZ=0.25, individual cap40/team cap400, delta1, age off. Learner/environment
  master seed3; evaluator master770003, ordered keyed episode tapes starting at zero.
  Matched medium D0 seed3 is already valid, k5 with infinite costs.
- CPU four threads; 20 rollouts x16 lanes x400 steps =128000 transitions/320 episodes.
  Evaluations at5/10/15/20 use512/512/512/2048 episodes, chunk512.
- Preserve current float32 learner parameters, existing higher-precision host/return and exposure
  calculations, all RNG streams/tapes, ordering, support, recurrent state, optimizer semantics,
  evaluator/normalizer-copy synchronization, checkpoint format, actions and rewards.
- Acceptance requires summary/manifest, passing receipt, four evaluations with ordered per-episode
  returns,20 learner and regional-path records, first/final float64 per-network displacement
  ratios and readable final checkpoint. Missing learner instrumentation means incomplete;
  missing resource telemetry alone means resources_unmeasured.
- Stop20 rollouts, first nonfinite learner loss/return, or first completed rollout after8h.
  Cost per arm: (20*(64.6+0.769*750)+3584*0.46)*1.15 = conservative4.63h, below8h.
  E2 c0.25 minimum final exposure0.04826/0.05293 supports budget motion; this cell emits its own.

Post-learner path coverage: accepted repair `69b24de052f19d3fbdf457358edd1a9c222585f4`
exercised publication offline following Linux peak-RSS failure. The accepted13/13 suite covers
unavailable-RSS publication with the real512/512/512/2048 constants and toy end-to-end output.
Runner/test bytes are unchanged; no additional suite was run for this unchanged cell.
Source inspection traces E3 recorder/publication -> E2 learner loop -> E0 RNG/exposure helpers and
corridor driver -> agent optimizer/checkpoint -> synchronized second-agent evaluator. Regional
arrays live per recorder/rollout; recurrent state remains agent-owned, evaluation preserves RNG,
and normalizers are deep-copied. No ownership/lifetime/serialization boundary changes.
Compared with accepted repair, E3/test/E2/core/corridor are unchanged; E0 only changes a usage
docstring. This is not a new cross-host bit-identity or resume-equivalence result.

## Exact execution and initial observation

Prospective portability: existing Windows/Linux CPU route, CPU device pinned; no CUDA substitution.
Node `wsl_4070` / `LAPTOP-U9TDKC8A`, SSH `hmasd-wsl-node`,
Python `/home/wu/.venvs/hmasd/bin/python`, supervisor `/usr/local/bin/agent-task`.

Task: `fsd_e3_medium_d2_seed3_20260904_01`.
Remote cwd: `/home/wu/hmasd-worktrees/fsd_e3_medium_d2_seed3_20260904_01`.
Launch SHA: `31bfecd79fc0f708546786ee26dfd8faa9e85dfb`.
Run root: `<cwd>/temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d2_seed3`.
Receipt: `<run root>/preflight.json`.
Supervisor directory: `/home/wu/.agent-tasks/fsd_e3_medium_d2_seed3_20260904_01`;
log `task.log`, exact wrapper `runner.sh`, PID/start witnesses `pid`/`start_time`.
Authoritative terminal witness is the same task's `agent-task status` exit_code.

Preparation used configured `zsh -lic` to fetch the pushed branch and create a detached exact-SHA
worktree. Interactive-shell gitstatus diagnostics appeared but fetch/worktree completed exit0;
this did not affect scientific execution. Remote HEAD matched launch SHA and git status was clean.
Runner SHA256 was `4c4a002868378bd7fba8125e1d36d633101c5dd07a703f33a3d3e524d4fd9ba1`.
Immediately before submission the task was not_found and searches under remote project/worktree
roots found no medium_d2_seed3 directories; canonical local cell was also absent.
An initial unquoted find glob was refused by zsh and was corrected as a read-only search before
preparation; no run was submitted during that diagnostic.

Exactly once, `agent-task run fsd_e3_medium_d2_seed3_20260904_01 bash -lc '<payload>'`
received this payload:

```sh
export PATH=/home/wu/.local/bin:/usr/lib/wsl/lib:/home/wu/.venvs/hmasd/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && cd /home/wu/hmasd-worktrees/fsd_e3_medium_d2_seed3_20260904_01 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/fsd_e3_medium_d2_seed3_20260904_01/temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d2_seed3/preflight.json && /home/wu/.venvs/hmasd/bin/python scripts/run_flexible_skill_duration_e3.py --row medium --arm d2 --seed 3 --preflight-receipt /home/wu/hmasd-worktrees/fsd_e3_medium_d2_seed3_20260904_01/temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d2_seed3/preflight.json --output-root /home/wu/hmasd-worktrees/fsd_e3_medium_d2_seed3_20260904_01/temp/directions/flexible_skill_duration/exp/E3_20260904 --launch-commit 31bfecd79fc0f708546786ee26dfd8faa9e85dfb --rollouts 20 --num-envs 16 --threads 4 --horizon 400 --eval-interval 5 --eval-episodes 2048 --eval-intermediate-episodes 512 --eval-chunk 512
```

Supervisor returned started in tmux `agent_fsd_e3_medium_d2_seed3_20260904_01`.
At26 seconds status was running, exit_code null, wrapper PID106154, tmux_active true.
Direct process inspection found learner PID106170, parent106154, with the exact runner argv.

Receipt assessed `2026-09-04T23:46:29.300533Z`, /proc/meminfo:
physical and effective available bytes each **15432294400**, floor **4294967296**.
All pass fields true, failure_reasons empty. Admission was destination-local and immediately
joined to the runner with &&. This proves initial admission, not runtime memory conformance.
Peak RSS is expected unavailable on this existing Linux route and must be marked accordingly.

## Observation handoff and remaining acceptance

Accepted task/node/SHA/cwd/root/receipt/log/terminal handle and bound were sent immediately to
DM `/root/dm_amx_fsd_continue` before this record was written. Initial receipt and PIDs followed.
Shared observer is `/root/tracker_tl_experiments`; DM hands it the accepted task directly.
CM retains collection and technical acceptance, and releases routine polling after adoption.
DM subsequently relayed the tracker's direct adoption ACK for this exact node/task/SHA.
The tracker is now the sole routine observer; CM polling has stopped and CM awaits terminal
collection dispatch. The experiment remains live under its original accepted supervisor.
No duplicate, restart, checkpoint resume or next-cell launch is authorized by changing observer.

Recover the existing task with:

```sh
ssh hmasd-wsl-node '/usr/local/bin/agent-task status fsd_e3_medium_d2_seed3_20260904_01'
ssh hmasd-wsl-node '/usr/local/bin/agent-task logs fsd_e3_medium_d2_seed3_20260904_01 30'
```

Terminal exit, final artifact completeness, actual wall and exposures remain unobserved at this
initial boundary. Tracker will remind DM at terminal state; CM then collects and inspects the
existing evidence. Process acceptance and inherited tests establish no gain or E3 polarity.


## Terminal technical acceptance

**Technically accepted complete cell**, original task exit0. This supersedes the initial running
boundary. DM resumed CM solely for existing-evidence collection after the dedicated tracker
reported completion. Its earlier SSH timeout at00:10:58Z was an observation gap, now recovered.
No new learner, admission, evaluation, replay, test, source change or successor was invoked.

Direct agent-task status: finished,exit0,wrapper106154,tmux inactive. The retained log records
terminal2026-09-05T00:29:52Z and actual supervisor duration **2603 seconds**. Status uptime3125s
at collection is time since task start, not runtime. Runner wall **2525.5407063739985 seconds**;
both actual durations are below4.63h projection/8h cap. Remote HEAD remains exact launch SHA
31bfecd79fc0f708546786ee26dfd8faa9e85dfb and checkout is clean.

Ordinary JSON/NumPy reads and Torch load(map_location=cpu) on copied evidence verified:

| Observation | Direct facts |
| --- | --- |
| Completion |completed=true,20 requested/completed,timing_only=false,instability=null,no QUARANTINED file|
| Interaction |20 x6400=128000 transitions;20 x16=320 episodes|
| Optimizer totals |coordinator3075,actor9000,critic9000,team300,individual1200;positive each rollout and sums agree|
| Learner/path |metrics,path,interruptions,gaps each20 ordered rollout IDs1–20;400 steps/16 lanes/6 agents;two regions each19200 agent-steps per rollout|
| Evaluation |(5,512),(10,512),(15,512),(20,2048),total3584;ordered IDs0..n-1;master770003,deterministic,chunk512|
| Arithmetic |all recorded losses/returns finite;each eval episode mean and sample-SE matches within1e-15;JSONL equals summary evaluations/return inputs|
| Configuration |medium(.005,.10),Delta.6,N6/K2/Z4/H400,rho0,no probe/coupling,seed3,c=cZ.25,caps40/400,age off,CPU/four threads|
| Publication |E3 identity/exact launch SHA,nonreduced evaluation,reference/final and cumulative regional path/exposure fields present;final path equals last path record|
| Checkpoint |readable64782527 bytes;all nested tensors finite;network tensors float32|
| Resources |resources_unmeasured,peakRSS null,no peak scratch measurement;artifact payload67315167 bytes|

Raw final single-cell evaluation mean0.35348229980468726,SE0.000670192216097249; mean training
rollout wall80.71256490539963s. No paired gain,row aggregate,superiority or E3 branch was computed.
Checkpoint network tensor counts are89/29/24/29 for coordinator/discoverer/team/individual.
All five optimizer states are present with87/15/14/24/29 entries. Coordinator/discoverer value
normalizers and config are present. RNG schema hmasd_rollout_sampler_rng_v1 contains streams.
Training interface:skill_interval40,rollout_length400,episode_length400. Policy interface remains
continuous Gaussian/action_dim2. These reads do not establish resume equivalence or cross-host
bit identity. Existing evaluator normalization/RNG semantics and source are unchanged.

The unchanged E0 helper computes exposure with float64 copies/arithmetic; each positive finite
first/final network ratio agrees exactly between summary and rollout1/20 learner records:

| Network | Rollout1 | Rollout20 |
| --- | ---: | ---: |
|coordinator|0.028561278072037403|0.12703892421509116|
|discoverer_actor|0.07535687324368119|0.4260967307456796|
|discoverer_critic|0.10545783232374614|0.40127404889520485|
|team_discriminator|0.013571879290845029|0.05824783929347061|
|individual_discriminator|0.016231476440611046|0.08319374434299935|

Receipt remains the passed15,432,294,400-byte physical/effective admission reported above.
Accepted repair13/13 publication-path coverage remains applicable; full publication succeeded
here. No new publication defect was found. Resource peaks remain unmeasured.

Original remote root remains the launch root above. Distinct ignored staging cell:
`C:/Projects/HMASD-worktrees/cm-fsd-medium-d2-seed3-20260904/temp/directions/flexible_skill_duration/exp/E3_20260904/remote_fetch_medium_d2_seed3_terminal_01/medium_d2_seed3`.
Canonical cell, created only after checking absence:
`C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d2_seed3`.

scp copied the original root to staging. Remote find/sha256sum enumerated10 files; every staged
hash matched. PowerShell Copy-Item then copied to the absent canonical cell; all10 hashes matched
again. Empty log directories add no files. Prior cells/quarantines remain untouched. Initial
sha256sum glob reported two directories; recursive file enumeration resolved this read-only
listing issue and established the complete10-file set.

| File | SHA256, identical remote/staged/canonical |
| --- | --- |
|checkpoint_final.pt|ee03672db113c899863c84bd21bc54c2e44954b341ba36ac96aa7482ea10d0e6|
|eval.jsonl|8e62bd1f9971991698928ad2e2881677d9727af3125a18f8a3256235f76f3363|
|gaps.jsonl|fa510f7cc61d3b23ed737510474cdabbdfe530772e2dc7cd86f6eff04d62f933|
|interruptions.jsonl|164d5dad8318d8af82b5299dec5acd9f60b95f11c5d4aa19bbbff23109ae4fe9|
|manifest.json|c669efa098ae5c16396b98723666bef966c4517c18d76f5d77dc67dfdfa2e514|
|metrics.jsonl|123277ba69a93a3a6fc4f67a65bb9da8fa03789b7b0510648d9b5f1a9dc1ad3e|
|path.jsonl|0cb5edc0b6eef48a660c6aff7a940a202635c97d408c66657b458cf051784503|
|preflight.json|dd6db2583717e07ac809f0cc48671e8757d9189d2901462c8a14b6bc98a702c0|
|rollout1_match.npz|6b0c4af6b1bd8c75f3edc67046a958aa1ccb0f5df53eead4829e726610cd47ba|
|summary.json|7cee34416a1508b900b06715d514273bc195e540109be181c747302595d0167c|

**Disposition:** technically accept this cell and return evidence to DM for intake. Scope additions
remain none. Missing peakRSS/scratch limits resource claims but does not invalidate this mechanism
cell. No successor admitted: large_d0_seed1 awaits DM intake and prospective launch SHA.

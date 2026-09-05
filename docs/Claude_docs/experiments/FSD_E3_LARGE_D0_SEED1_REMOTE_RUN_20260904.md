# FSD E3 large D0 seed 1 attempt 01 â€” remote run record

**Accepted once, running; terminal technical acceptance pending.** No paired gain, row aggregate
or E3 branch is applied. DM accepted the preceding medium D2 seed3 cell; E3 was12/18 valid,
zero running,six never launched before this invocation. This starts only large_d0_seed1.

## Contract and ownership

Binding unchanged card:
`docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`.
Prospective selection: same directory's
`FSD_E3_MEDIUM_D2_SEED3_INTAKE_20260904.md`, Meaning-complete next invocation,
pushed at **f42dcb7a76f6341d3552a27134ca674674b29718**. The explicit owner resume supersedes
historical drain statements; this preserves the original remaining sequence.

B/EXPLORE question: policy-gap interruption c=.25 under heterogeneous hazards versus the strongest
same-information fixed clock. This invocation measures the large-row D0 comparator; event-linked
renewal, noisy gaps, optimizer variation and team interference remain competing explanations.
Claim ceiling is preliminary mechanism evidence on the declared corridor. No retuning, transfer,
new mechanism, altered rule, source repair, local fallback or later cell is in scope.
All18 valid cells remain necessary before the frozen E3 branch is read.

CM owns this tracked document and ignored evidence staging only, reusing clean
`C:/Projects/HMASD-worktrees/cm-fsd-medium-d2-seed3-20260904`,
branch `codex/cm-fsd-medium-d2-seed3-20260904`, based on prior receipt commit6b0669394.
The launch is the new prospective SHA, not the CM documentation branch HEAD. Source comparison
against launch SHA has no diff across E3/E2/E0,test,core,corridor/config surfaces.
Saved checkout and unrelated DM/Root changes remain untouched.

Engineering-scope section4 additions: **none**. No source,tests,orchestration,retry,queue,guard,
telemetry,supervisor or compatibility layer added. Reuse accepted repair69b24de and13/13 focused
coverage; no repeated suite for unchanged source. Post-learner coverage includes offline
publication and real512/512/512/2048 counts after the historical Linux RSS defect.
The production chain remains E3 recorder/publication -> E2 learner loop -> E0 RNG/exposure
helpers/corridor driver -> agent optimizer/checkpoint -> synchronized second-agent evaluation.
Regional arrays remain recorder-owned per rollout, recurrence stays agent-owned, evaluation
preserves RNG and deep-copies normalizers; serialization/lifetime boundaries are unchanged.

Frozen behavior:
- Large hazards(.02,.20),Delta1,N6/three agents perregion,K2/Z4,H400,Bernoulli rho0,no probe/coupling.
- Seed1,D0k5 via existing D2 route with c=cZ=infinity,both caps5,delta1,ageoff.
- CPU four threads;20x16x400=128000 transitions/320 episodes.
- Deterministic eval at5/10/15/20:512/512/512/2048 episodes,chunk512,master770003,
  ordered keyed episode IDs starting0; preserve pairing across arms.
- Preserve float32 learner,existing higher-precision host/return/exposure arithmetic,RNG,
  support,ordering,recurrent/optimizer semantics,actions,rewards,checkpoint and normalizer copies.
- Require summary/manifest,receipt,20 learner/two-region path records,four per-episode evaluations,
  first/final per-network float64 displacement ratios,readable final checkpoint.
- Per-arm cost [20*(64.6+.769*150)+3584*.46]*1.15=6034.786s=1.68h,below8h.
  Stop20 rollouts,first nonfinite learner loss/return,or first completed rollout after8h.
  E2 exposure minima.04826/.05293 show budget motion; this cell must emit its own.
- Missing learner instrumentation means incomplete; resource telemetry missing means
  resources_unmeasured. No runtime peak claim follows from memory admission.

## Exact launch and direct initial facts

Prospective host portability is Windows/Linux CPU; CPU is pinned,no CUDA substitution.
Node wsl_4070/LAPTOP-U9TDKC8A,SSH hmasd-wsl-node,Python /home/wu/.venvs/hmasd/bin/python.
Task **fsd_e3_large_d0_seed1_20260904_01**,supervisor /usr/local/bin/agent-task.
Cwd `/home/wu/hmasd-worktrees/fsd_e3_large_d0_seed1_20260904_01`.
Root `<cwd>/temp/directions/flexible_skill_duration/exp/E3_20260904/large_d0_seed1`.
Receipt `<root>/preflight.json`;supervisor log
`/home/wu/.agent-tasks/fsd_e3_large_d0_seed1_20260904_01/task.log`.
Exit witness is same task's agent-task status exit_code.

Configured zsh -lic fetch/worktree preparation completed exit0. Shell gitstatus emitted initialization
diagnostics, and automatic Git gc reported failure to traverse parent of732cc2b2299821a58d644e202c4b95c392932447
and failed repack. No repository maintenance/repair was attempted; exact-SHA worktree creation
succeeded and clean HEAD was verified directly. Runner SHA256 remained
4c4a002868378bd7fba8125e1d36d633101c5dd07a703f33a3d3e524d4fd9ba1.
Immediately before submission,task not_found;remote project/worktree search had no matching
large_d0_seed1 directory,canonical local cell was absent. No older cell was changed.

Exactly one `agent-task run fsd_e3_large_d0_seed1_20260904_01 bash -lc '<payload>'`:

```sh
export PATH=/home/wu/.local/bin:/usr/lib/wsl/lib:/home/wu/.venvs/hmasd/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && cd /home/wu/hmasd-worktrees/fsd_e3_large_d0_seed1_20260904_01 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/fsd_e3_large_d0_seed1_20260904_01/temp/directions/flexible_skill_duration/exp/E3_20260904/large_d0_seed1/preflight.json && /home/wu/.venvs/hmasd/bin/python scripts/run_flexible_skill_duration_e3.py --row large --arm d0 --seed 1 --preflight-receipt /home/wu/hmasd-worktrees/fsd_e3_large_d0_seed1_20260904_01/temp/directions/flexible_skill_duration/exp/E3_20260904/large_d0_seed1/preflight.json --output-root /home/wu/hmasd-worktrees/fsd_e3_large_d0_seed1_20260904_01/temp/directions/flexible_skill_duration/exp/E3_20260904 --launch-commit f42dcb7a76f6341d3552a27134ca674674b29718 --rollouts 20 --num-envs 16 --threads 4 --horizon 400 --eval-interval 5 --eval-episodes 2048 --eval-intermediate-episodes 512 --eval-chunk 512
```

Supervisor accepted in tmux agent_fsd_e3_large_d0_seed1_20260904_01.
At20s:running,exitnull,tmuxtrue,wrapperPID802417;direct ps showed learner802469,parent802417,
with exact runner argv. Receipt assessed2026-09-05T00:52:33.793656Z from/proc/meminfo:
physical/effective each **15042007040 bytes**,floor4294967296;all pass fields true,no failures.
Admission and runner were immediately joined with && on the actual node. PeakRSS remains an
expected unavailable measurement on this existing Linux path,not a learner defect.

## Handoff and remaining boundary

Accepted node/task/SHA/cwd/root/receipt/log/bound were sent immediately to DM
`/root/dm_amx_fsd_continue`;initial receipt/PIDs followed. DM hands the existing handle directly
to `/root/tracker_tl_experiments`. CM retains technical collection and releases routine
observation after adoption. No observer change authorizes a duplicate,restart or resume.
DM relayed the tracker's direct adoption ACK for this exact node/task/SHA. Routine polling has
ended; tracker is the sole observer and will wake DM for original-task terminal collection.

```sh
ssh hmasd-wsl-node '/usr/local/bin/agent-task status fsd_e3_large_d0_seed1_20260904_01'
ssh hmasd-wsl-node '/usr/local/bin/agent-task logs fsd_e3_large_d0_seed1_20260904_01 30'
```

Terminal exit,artifact completeness,actual wall and exposure await the original task's completion
and CM collection. Initial process success and inherited tests establish no scientific polarity.


## Terminal technical acceptance and owner-direct stop

**Technically accept the original large_d0_seed1 cell as complete.** Tracker directly woke CM,
then DM confirmed collection-only scope and latest **OWNER_DIRECT drain: finish this existing
cell, STOP before large_d2_seed1**. CM explicitly acknowledges and applies that instruction.
No successor, retry, new admission, learner, evaluation, replay, repair, Pro or test was started.
No CM child was spawned. All collection shell sessions ended; this CM returns idle after push.

Direct original agent-task status:finished,exit0,wrapper802417,tmux inactive. Retained supervisor
log terminal **2026-09-05T01:41:53Z**, actual duration **2960 seconds**. Status uptime3307 at
collection was time-since-start,not runtime. Runner wall **2837.5571884999954 seconds**;
mean training rollout wall94.44350262129993s. Both actual durations below1.68h projection/8h cap.
Remote worktree remained clean at exact launch f42dcb7a76f6341d3552a27134ca674674b29718.

JSON/NumPy arithmetic and CPU Torch checkpoint reads established:

| Required observation | Direct evidence |
| --- | --- |
| Completion |completed=true,20 requested/completed,timing_only=false,instability=null,no quarantine file|
| Interaction |20 x6400=128000 transitions;20 x16=320 training episodes;1280 coordinator rows each rollout|
| Optimizer steps |coordinator3000,actor72000,critic72000,team300,individual1200;positive every rollout;record sums match summary|
| Learner/path |metrics,path,interruptions,gaps each20 ordered IDs1–20;400 steps/16 lanes/6 agents;both regions19200 agent-steps per rollout|
| Evaluation |(5,512),(10,512),(15,512),(20,2048),total3584;ordered IDs0..n-1,master770003,deterministic,chunk512|
| Arithmetic |every eval mean/sample-SE matches episode inputs within1e-15;JSONL equals summary evaluations and ordered return inputs|
| Configuration |large(.02,.20),Delta1,N6/K2/Z4/H400,rho0,no probe/coupling,seed1,k5,infinite costs,bothcaps5,ageoff,CPU/four threads|
| Publication |E3/exact launch identity,nonreduced eval,reference/cumulative and final regional paths/exposures present;final path equals last path record|
| Numerical integrity |recorded learner losses/training and evaluation returns finite;all network exposure values positive finite;checkpoint nested tensors finite|
| Resource limits |resources_unmeasured,peakRSS null,no peak scratch measurement;artifact payload67848670 bytes|

An initial read-only config assertion expected Python infinity but JSON records use the existing
string Infinity. Direct source inspection of E0 _jsonable lines81–82 confirms this exact
serialization; inspection was corrected to the existing representation and all checks passed.
No experiment defect, source repair, or semantic substitution occurred.

Single-cell final mean **0.5481325276692715**,SE **0.0005496801464339235**.
Exact fixed-clock reference Jk **0.619056016**; recomputed D0/reference ratio
**0.8854328421053118** agrees with summary within1e-15. This is the card's competence input,
not a paired treatment gain or E3 branch. No cross-cell arithmetic was performed.

Checkpoint64782527 bytes,network tensor counts89/29/24/29 for coordinator/discoverer/team/
individual,all float32. Five optimizer states contain87/15/14/24/29 entries;config and
coordinator/discoverer value-normalizer states present. RNG schema hmasd_rollout_sampler_rng_v1
with streams;training interface skill_interval5,rollout_length400,episode_length400. These reads
establish readable evidence,not resume equivalence or cross-host bit identity.

First/final ratios agree exactly with rollout1/20 learner records. Unchanged E0 helper computes
these displacement ratios in float64; learner weights remain float32.

| Network | Rollout1 | Rollout20 |
| --- | ---: | ---: |
|coordinator|0.03963771164671024|0.12392500707800136|
|discoverer_actor|0.15977620771044398|0.8630096950038654|
|discoverer_critic|0.2305541232709665|0.8745928208891488|
|team_discriminator|0.010203675033779294|0.03338753931700782|
|individual_discriminator|0.013056890182455691|0.053849379252340644|

The receipt retains initial passed physical/effective15042007040-byte availability. It proves
admission only. Inherited accepted13/13 coverage includes real publication constants; full E3
publication succeeded here,no new publication defect. Resource peaks remain unmeasured.

Original remote cell remains at the launch root above. Unique ignored staging:
`C:/Projects/HMASD-worktrees/cm-fsd-medium-d2-seed3-20260904/temp/directions/flexible_skill_duration/exp/E3_20260904/remote_fetch_large_d0_seed1_terminal_01/large_d0_seed1`.
Canonical cell created only after checking absence:
`C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/large_d0_seed1`.

scp copied original evidence to staging. Remote find/sha256sum enumerated10 files; every staged
hash matched. PowerShell Copy-Item copied the complete cell to the absent canonical root;
all10 canonical hashes matched staging. Existing cells and historical quarantine were untouched.

| File | SHA256, identical remote/staged/canonical |
| --- | --- |
|checkpoint_final.pt|59afabe7719242c4174816d108a0aec8dc197264488d61bcf4d43a0f81086fc5|
|eval.jsonl|74ef6d638c323bc8c87d4f0ce9132d1282e78c6af15f710d4b6652a4a6ebc7fb|
|gaps.jsonl|01455ebce041ecd1f4a869fafaab5ea57a97db50080e786fd68e4acc68fa02f0|
|interruptions.jsonl|b77b3d2f0b93c437055455f916e6388f0c6cbc2474023f779dc77508c45021fc|
|manifest.json|3df42033d7beac55be23d5a571dc38529e24600556550f1167f91e2ab18b54d6|
|metrics.jsonl|2879210ee3e0e5c09cdd77deb2334450e7b10aed9c27a9f1ece4330ec4a1b310|
|path.jsonl|ff08dfaaf6da4c19267bcfad5e380ed9f39141f5ae338e79fc5afe9908cb9ebe|
|preflight.json|f31fcb33e8e4fd820716ba70f54dffcc2ebe057ee30acdca42be5039d0aa7453|
|rollout1_match.npz|70fe7fb86381f04e0d116bd352a08368f1327a38c46ce2cd74ffb367e1eb8e2f|
|summary.json|fc0507d3d5a1fb128c5f2bf9ffa8fced81490e4e62ca073473841ffbca8a4418|

Technical acceptance is complete; DM owns final scientific intake. Scope additions remain none.
**Safe handoff:** original task terminal,all required evidence collected,no active CM child or
shell session,no successor created. Pending frozen order remains large_d2_seed1,large_d0_seed2,
large_d2_seed2,large_d0_seed3,large_d2_seed3. All five remain unlaunched by this CM and are held
under the latest owner-direct pause. Lifecycle,priority,card,predictions and rule are unchanged.
No paired or aggregate E3 rule is read before18/18 valid cells.

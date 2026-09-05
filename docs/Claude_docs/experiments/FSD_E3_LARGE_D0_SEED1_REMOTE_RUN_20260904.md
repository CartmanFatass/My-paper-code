# FSD E3 large D0 seed 1 attempt 01 — remote run record

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

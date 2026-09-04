# FSD E3 medium D2 seed 3 attempt 01 — remote run record

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

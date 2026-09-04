# FSD E3 medium D0 seed 3 attempt 01 — remote launch receipt

## Engineering boundary

This record owns the acceptance of exactly one detached invocation of unchanged B/EXPLORE
`FSD-E3-HET-R01`, `medium_d0_seed3` attempt 01. Root/DM own scheduling and scientific intake;
CM owns resumed direct runtime observation and technical acceptance. A running receipt is not
a valid completed cell and supplies no scientific polarity.
No intermediate return comparison or E3 branch is made here. The full 18-cell matrix remains
required before applying the frozen large-row rule.

Binding card: `docs/research/candidates/flexible_skill_duration/FSD_E3_HETEROGENEOUS_HAZARD_SCIENCE_CARD_20260904.md`.
Prior quarantine and publication repair are recorded in that directory's seed-1 quarantine intake
and E3 run state. The owner resumed automated research on 2026-09-04; the prior drained pause no
longer controls this single invocation.

Owned tracked path: this document only. Local working branch is
`codex/cm-fsd-seed3-resume-20260904`, created from
`8d1c597871b38edc7d5f139f34f5a3ce2941c7d0` in
`C:/Projects/HMASD-worktrees/cm-fsd-seed3-resume-20260904`.
Ignored evidence stays under `temp/directions/flexible_skill_duration/exp/`.
Unrelated primary-checkout changes and all older evidence roots were preserved.

Engineering scope section 4 additions: **none**; no source edits, new orchestration, telemetry,
guards, retry, scheduler, or repeated smoke tests. Existing configured `agent-task` is used once.
The code-size and test-time budgets add zero lines and zero test time in this slice.

## Frozen behavior and readiness

- Medium host: hazards `(0.005, 0.10)`, Delta `0.6`, six agents pinned three per region, `K=2`,
  `Z=4`, `H=400`, Bernoulli events, rho zero, no probe or coupling.
- D0: existing D2 implementation with both costs infinity, both caps `5`, interruption delta `1`,
  and age feature off. Learner and host master seed `3`; evaluation master `770003`, episode IDs
  starting at zero, keying `(master_seed, episode_id, entity_or_region_id)`.
- CPU with four Torch threads, 20 rollouts by 16 lanes by 400 steps: 128,000 transitions and 320
  training episodes. Preserve numerical precision, RNG streams, recurrence, checkpoint format,
  evaluator/normalizer synchronization, actions, rewards, ordering, and paired tapes.
- Evaluations at 5/10/15/20 use 512/512/512/2048 episodes, chunk 512. Final acceptance needs
  summary, manifest, passing preflight, 20 learner/path records, four evaluations with per-episode
  paired inputs, final checkpoint, and float64 per-network parameter displacement ratios after
  rollout 1 and 20.
- Stop at 20 rollouts, first nonfinite learner loss or return, or first completed rollout after
  eight hours. No automatic retry or local fallback is authorized in this slice.
- Per-arm projection: `(20*(64.6+0.769*150)+3584*0.46)*1.15`, about **1.68 hours**, below the
  **8-hour per-arm cap**. Prior E2 c=0.25 minimum final exposure ratios 0.04826/0.05293 establish
  budget exposure; this invocation must publish its own actual exposure lines.
- Post-learner coverage: accepted repair `69b24de052f19d3fbdf457358edd1a9c222585f4` exercised
  publication offline after the seed-1 Linux RSS failure; accepted focused suite 13/13 includes
  unavailable-RSS publication with real 512/512/512/2048 counts and toy end-to-end output. This
  slice reuses that evidence because the runner and test Git bytes are unchanged.

The source chain inspected is E3 instrumentation -> existing E2 loop -> E0 RNG/exposure helpers
and corridor driver -> native agent optimizer/checkpoint -> synchronized second-agent evaluator
-> E3 publication. Per-rollout recorder arrays own the regional consequence data; recurrent
state stays in the agent, and evaluation uses preserved RNG state. No state ownership changed.
The wider source comparison against the accepted repair found only an E0 module-docstring usage
example change (`a1ce91797`), with no executable change.

The prospective portability boundary is Linux/Windows host portability of this existing CPU
route; the device remains CPU. Remote-first node `wsl_4070` uses SSH `hmasd-wsl-node`, interpreter
`/home/wu/.venvs/hmasd/bin/python`, supervisor `/usr/local/bin/agent-task`, and exact-SHA detached
worktree. Node-local admission must measure physical and effective availability each at least
4 GiB immediately before the runner in the same payload, joined with `&&`.

Before launch preparation, authoritative task status was `not_found` for
`fsd_e3_medium_d0_seed3_20260904_01`, and a directory search under both remote project and
worktree roots found no `medium_d0_seed3*`. Five older FSD tasks were terminal. The quarantined
seed-1 attempt 01 remains untouched.

## Launch and observation

**Accepted once and running.** The DM supplied pushed launch assignment
`9c0a990537a8ffef58306429a1ff402550fc4b82` on `origin/codex/dm-fsd-resume-20260904`.
Its source surface is unchanged from this slice's base. Remote preparation verified a clean
detached checkout at exactly that SHA and runner SHA-256
`4c4a002868378bd7fba8125e1d36d633101c5dd07a703f33a3d3e524d4fd9ba1`.
The final task check still returned `not_found`, and the remote seed-3 result-root search was
empty immediately before submission.

Execution cwd: `/home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed3_20260904_01`.
Run root: `/home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed3_20260904_01/temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d0_seed3`.
Task: `fsd_e3_medium_d0_seed3_20260904_01` on `wsl_4070` / `LAPTOP-U9TDKC8A`.
Supervisor log: `/home/wu/.agent-tasks/fsd_e3_medium_d0_seed3_20260904_01/task.log`.

The exact payload below was supplied once to `/usr/local/bin/agent-task run
fsd_e3_medium_d0_seed3_20260904_01` as `bash -lc '<payload>'`:

```sh
export PATH=/home/wu/.local/bin:/usr/lib/wsl/lib:/home/wu/.venvs/hmasd/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && cd /home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed3_20260904_01 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed3_20260904_01/temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d0_seed3/preflight.json && /home/wu/.venvs/hmasd/bin/python scripts/run_flexible_skill_duration_e3.py --row medium --arm d0 --seed 3 --preflight-receipt /home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed3_20260904_01/temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d0_seed3/preflight.json --output-root /home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed3_20260904_01/temp/directions/flexible_skill_duration/exp/E3_20260904 --launch-commit 9c0a990537a8ffef58306429a1ff402550fc4b82 --rollouts 20 --num-envs 16 --threads 4 --horizon 400 --eval-interval 5 --eval-episodes 2048 --eval-intermediate-episodes 512 --eval-chunk 512
```

The configured supervisor wrapper was inspected after acceptance and retains that exact
preflight-and-runner payload. At uptime 10 seconds it reported `running`, `exit_code: null`,
`pid: 74470`, `tmux_active: true`. Process inspection independently showed the exact full
runner argv in learner PID `74473`, parent `74470`.

Admission receipt: `<run root>/preflight.json`, assessed at
`2026-09-04T21:39:47.176686Z`, source `/proc/meminfo`. Physical and effective available memory
were each **15,429,533,696 bytes**, both above **4,294,967,296 bytes**. All three pass fields
were true and failure reasons were empty. This is admission evidence, not measured runtime
peak-RSS conformance. Peak RSS is expected to be unavailable on this Linux route; final
publication must report `resources_unmeasured` if so.

Preparation note: the first Git fetch used a non-login remote shell and stalled. Only this
slice's read-only fetch and diagnostic were terminated. The configured `zsh -lic` fetch then
succeeded. A transient CRLF argument error in that preparation was corrected before fetching;
no supervisor submission or learner existed during these transport steps. No source changed.

## Handoff and limits

The accepted task identity, PIDs, SHA, root and passing receipt were sent immediately to the DM.
The task remains detached. This assigned observation ends at running acceptance; terminal exit,
20-rollout completion, checkpoint, final publication and complete artifact counts are **not yet
observed or accepted**. This document does not count the cell as valid and makes no outcome
comparison, comparator-competence finding, event-path finding, or E3 branch claim.

Continue observation using the existing task only:

```sh
ssh hmasd-wsl-node '/usr/local/bin/agent-task status fsd_e3_medium_d0_seed3_20260904_01'
ssh hmasd-wsl-node '/usr/local/bin/agent-task logs fsd_e3_medium_d0_seed3_20260904_01 30'
```

Root routes resumed CM observation to terminal evidence and subsequent technical artifact intake.
Loss of observation is not authorization for another launch. Scientific interpretation remains
with the DM after the full frozen matrix is complete.

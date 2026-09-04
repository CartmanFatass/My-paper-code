# FSD E3 medium D0 seed 3 attempt 01 — remote launch receipt

Terminal update, 2026-09-04: **technically accepted complete cell**. The original task finished
with exit 0; all required artifacts were collected, checked and copied to the previously absent
canonical seed-3 root. The owner-requested execution drain stops here, before `medium_d2_seed3`.
No paired scientific comparison or aggregate E3 branch has been applied.

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

## Initial running handoff

The accepted task identity, PIDs, SHA, root and passing receipt were sent immediately to the DM.
The initial assignment ended at detached running acceptance. Terminal exit, completion and
publication were not then observed or accepted. Root's tracker subsequently adopted the exact
task, and CM routine polling ended after its acknowledgment. The later terminal acceptance is
recorded below; neither boundary supplies a paired outcome comparison or aggregate E3 branch.

Continue observation using the existing task only:

```sh
ssh hmasd-wsl-node '/usr/local/bin/agent-task status fsd_e3_medium_d0_seed3_20260904_01'
ssh hmasd-wsl-node '/usr/local/bin/agent-task logs fsd_e3_medium_d0_seed3_20260904_01 30'
```

Root routes resumed CM observation to terminal evidence and subsequent technical artifact intake.
Loss of observation is not authorization for another launch. Scientific interpretation remains
with the DM after the full frozen matrix is complete.

## Terminal technical acceptance and safe drain

The DM resumed this CM solely to collect the existing completed cell. The actual CM branch was
clean at `2a40b1531da19aaaf1e11693bc4bb4bfb55bdf70`. The original remote worktree remained clean
at launch SHA `9c0a990537a8ffef58306429a1ff402550fc4b82`. No new experiment, preflight, source
edit, suite, repair, heartbeat, or tracker was created. Engineering-scope additions remain none.

Authoritative `/usr/local/bin/agent-task status fsd_e3_medium_d0_seed3_20260904_01` reported
`finished`, exit `0`, wrapper PID `74470`, `tmux_active: false`. The retained supervisor log
records terminal time `2026-09-05T06:26:00+08:00` (`2026-09-04T22:26:00Z`) and duration
**2,773 seconds**. The published runner wall is **2,687.7446834669972 seconds**. These are
distinct reported timing observations; neither has been substituted for the other. Both are
below the 1.68-hour projection and the eight-hour cap. No runtime peak-RSS bound is claimed.

Direct reads used the existing Python JSON parser and Torch checkpoint loader on copied
evidence, without constructing a learner or running evaluations. Inspection established:

| Required observation | Observed |
| --- | --- |
| Completion | `completed=true`, 20 requested/completed rollouts, `timing_only=false`, `instability=null`; no quarantine file |
| Training exposure | 128,000 transitions, 320 episodes; each rollout 6,400 transitions and 16 episodes; 1,280 coordinator rows each |
| Optimizer updates | coordinator 3,000; discoverer actor 72,000; discoverer critic 72,000; team discriminator 300; individual discriminator 1,200; positive in every rollout |
| Learner and path records | 20 each in metrics, path, interruptions and gaps; ordered rollout IDs 1–20; 400 steps, 16 lanes, six agents and both regional records |
| Evaluation | rollout/episode counts `(5,512)`, `(10,512)`, `(15,512)`, `(20,2048)`; total 3,584; deterministic, master 770003, chunk 512 |
| Paired inputs | ordered IDs `0..episodes-1` and one finite return per ID in every evaluation; exact agreement between eval JSONL and summary inputs; keyed tape law unchanged |
| Frozen configuration | medium host, seed 3, CPU/four threads, both costs infinity, both caps 5, age off, no probe/coupling; manifest agrees with summary and copied admission |
| Numerical integrity | all recorded learner losses and training/evaluation returns finite; network checkpoint tensors finite and float32 |
| Final publication | summary and manifest identify E3 and the launch SHA; `reduced_from_contract=false`; reference, competence-input, final/cumulative two-region path, exposure and artifact fields present |
| Checkpoint | readable, 64,782,527 bytes; network, all five optimizer, config, coordinator/discoverer value-normalizer and rollout-sampler RNG states present |
| Resources | `resource_telemetry_status=resources_unmeasured`, peak RSS null; collected artifact payload 67,857,158 bytes; no peak-scratch measurement is published |

The checkpoint contains 89 skill-coordinator, 29 skill-discoverer, 24 team-discriminator and
29 individual-discriminator state tensors. Its training interface is skill interval 5 and
rollout/episode length 400. The inherited RNG schema remains `hmasd_rollout_sampler_rng_v1`.
Checkpoint inspection establishes readable saved evidence, not a new resume-equivalence claim.
The accepted source still deep-copies evaluator normalizers and preserves evaluation RNG state;
this slice makes no additional cross-host bit-identity claim.

Machine-generated per-network `||theta-theta_0||_2 / ||theta_0||_2` values below agree exactly
between summary and rollout-1/20 learner records. The unchanged E0 helper explicitly converts
parameters and displacement computations to float64.

| Network | Rollout 1 | Rollout 20 |
| --- | ---: | ---: |
| coordinator | 0.04080823588801077 | 0.11708156078197213 |
| discoverer actor | 0.16684791425000306 | 0.8676006529359155 |
| discoverer critic | 0.24597084848341444 | 0.9337023457398214 |
| team discriminator | 0.009194614542247207 | 0.03807650598342086 |
| individual discriminator | 0.012286576779590372 | 0.05680384685020319 |

## Artifact collection and provenance

Original remote root remains unchanged:
`/home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed3_20260904_01/temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d0_seed3`.

Distinct ignored local staging root:
`C:/Projects/HMASD-worktrees/cm-fsd-seed3-resume-20260904/temp/directions/flexible_skill_duration/exp/E3_20260904/remote_fetch_seed3_terminal_01/medium_d0_seed3`.

Verified canonical root, created only after confirming it was absent:
`C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d0_seed3`.

Collection used `scp -r hmasd-wsl-node:<original remote root> <distinct staging parent>/`.
Remote `find <root> -type f -exec sha256sum {} \;` supplied the hashes below. All ten staged
files matched. After technical acceptance, PowerShell `Copy-Item -LiteralPath <staged cell>
-Destination <absent canonical cell> -Recurse` copied the complete cell; all ten canonical
file hashes matched the staging copy again. Existing cells and the quarantined attempt were
neither overwritten nor modified. Hashes here record transfer verification; no runtime guard or
provenance machinery was added.

| File | SHA-256 |
| --- | --- |
| checkpoint_final.pt | `92fa61b25076d215769adc990aa203616c061214593cb9b9b89373df5eaea022` |
| eval.jsonl | `dcb14e5f52c1f6398c56901fd29457578cf11b4e2f358b47d8c1ca59c47eef9c` |
| gaps.jsonl | `559c6582e927b8a785f6615a863623fe86ed05f263050918b94cfdab6cf696aa` |
| interruptions.jsonl | `5ba44905230fd1012bf9ecffdf30c027e57dc25659b084c7b53a20d4a7fe8d1b` |
| manifest.json | `f85d1a7af6e2f889d2a36401e05dba5ff7ac54f8dbd9783de43117217e5ac075` |
| metrics.jsonl | `dc776ccd6c89a5abdcec917b19c612775e03c03f7c3ab7af3647028fb54a86ef` |
| path.jsonl | `75be6bb5b3280d2402e03557b3c3058d6dad892da8dd75050d33b625673f8cbb` |
| preflight.json | `d0cf5a6731fe6037b3b33dcaa5b08db25c2c25196de585e8865c8324bac97d89` |
| rollout1_match.npz | `6d5ca367b7ea7e25e1bfacb533f14f6074b9048564a33d181de79e19d92ffdda` |
| summary.json | `4895b4c92ed28f5e36b4e92ca407a952b22011faac3218b0ede7233ed1b52a52` |

The post-learner coverage line remains the previously accepted offline publication repair and
13/13 focused suite with real evaluation constants. Required E3 publication succeeded here; no
new publication-path engineering defect was found. Missing peak RSS and unmeasured peak scratch
remain resource limitations, not learner instrumentation defects or scientific findings.

**Disposition:** technically accept this complete single cell and return its verified summary
to DM for intake. The owner-requested safe drain stops before `medium_d2_seed3`; no next cell
was launched or admitted. No paired-arm return comparison, aggregate mechanism interpretation,
or E3 result branch is made by this receipt.

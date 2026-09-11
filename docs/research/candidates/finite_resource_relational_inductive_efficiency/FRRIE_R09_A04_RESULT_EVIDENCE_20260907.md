# FRRIE A04 result evidence and CM technical acceptance

The single P12 setup/T0 chain meets the frozen card §3 branch **A04_T0_PATH_COMPLETED**.
All six 64-tape phases completed, preserving the recorded same-update A03 digests.
This establishes one bounded alternative-stack input-path completion at A/RECON ceiling.
It does not identify A03's cause, establish stability or authorize R09.

## Binding and terminal evidence

- Contract: [A04 card §§1–4](FRRIE_R09_A04_ALTERNATIVE_STACK_SCIENCE_CARD_20260907.md)
  and [prospective handoff §§1–2](FRRIE_R09_A04_PROSPECTIVE_HANDOFF_20260907.md), frozen
  at `6fb13f9a9`; P12 allocation and source-staging facts are retained in the
  [execution record](FRRIE_R09_A04_P12_EXECUTION_RECORD_20260907.md).
- Sole accepted handle: `frrie-a04-system312-p11-d6844bb25f6f`, node `wsl_4070`,
  detached cwd `/home/wu/hmasd-worktrees/frrie-a04-d6844bb25f6f`, source
  `d6844bb25f6f1030aa7123467935861dcc719450`. DM's clean exact-SHA staging receipt
  is reused; no scientific source changed during collection.
- [Supervisor log](a04_system312_20260907/task.log) records start
  `2026-09-07T21:38:13Z`, exit 0 at `21:38:29Z`, duration **16 s**. The copied
  `status`, `exit_code`, `pid` and `start_time` retain terminal supervisor facts.
  The status command returned `finished`, PID `2751953`, tmux inactive.
  Status-query uptime (57 s at CM's first read; approximately 97 s at DM's read)
  is elapsed time since launch, not process runtime.
- [Launch receipt](a04_system312_20260907/launch_receipt.txt),
  [1379-byte LF command](a04_system312_20260907/command.sh) and actual
  [supervisor runner](a04_system312_20260907/runner.sh) are retained. Offline comparison
  confirmed the supervisor payload equals the frozen command payload; command SHA256 is
  `959a43cefb989e823a8fe38cdccc30dc83914f13bc3218a8cdda635c691be885`.
  The entire setup-through-publication chain has the declared 300 s TERM / 5 s KILL bound.

## Setup, semantics and publication

The complete log records system CPython 3.12.3 venv creation and one successful binary-only
NumPy 1.26.3 installation. Installed [WHEEL metadata](a04_system312_20260907/numpy_WHEEL.txt)
identifies cp312-cp312 manylinux x86_64. The raw [summary](a04_system312_20260907/summary.json)
records the dedicated interpreter, CPython 3.12.3 / GCC 13.3.0 and imported NumPy 1.26.3.
The prior [node inventory](FRRIE_A04_PREPARATION_NODE_INVENTORY_20260907.json) supplies
the declared WSL2 host/kernel/OS facts; collection used that same configured SSH node.

The argv, root ending `0003`, label `FRRIE-B09-CONTACT-BLOCK-003`, T0, repeat 3,
updates 2 and eval-episodes 256 match the card. Actual evaluation tape count is zero.
The preserved source defines roster order `(9,15)*32`, horizon 12, origin schedules,
addressed RNG and FP32/int64 arrays. The exact supervisor command sets all four declared
compute-thread environment variables to 1 and uses `-X faulthandler`.
Summary fields `torch_present_at_work_start`, `torch_in_sys_modules` and `trace_active`
are false; `exception` is null. No learner, optimizer, model or native work was invoked.

The result directory contains only `summary.json`; its six nested phase records are the
existing runner's complete phase artifacts, not missing separate tape files. Publication
completed and the summary retains its original A03 implementation object string. A04
identity is carried by the card, distinct handle and distinct output root.

## Phase and resource checks

Offline Python assertions over retained JSON verified repetition indices 0,1,2, exactly
two ordered update phases per repetition, 64 tapes per phase, the flags above, admission
equality, command identity and exit 0. No workload, smoke, learner, historical regeneration
or extra environment probe was run. Machine-produced details are in
[collection checks](a04_system312_20260907/collection_checks.json).

| Update | Repetitions completed | Tape constructions | Digest in each repetition and recorded A03 |
| --- | --- | --- | --- |
| 1 | 0, 1, 2 | 192 | `0f0fb392c59dcfdbaa475ae8becca03323751d0a849ee6f39c9a8c9d68057b5f` |
| 2 | 0, 1, 2 | 192 | `7e155dc5452d9303688d0a807b190ab0050db723078a7f890e1ee6b5f71a4f16` |

All 384 constructions cover 128 distinct addressed inputs repeated three times. The
comparison reads only the retained [A03 T0 summary](a03_tape_isolation_20260906/t0/summary.json).
No first-matching failure, incompleteness or content-difference branch applies.

The [fresh on-node admission](a04_system312_20260907/a04_system312_admission.json) at
`21:38:19.414305Z` passed with physical and effective available memory both
15,664,181,248 bytes (14.5884 GiB), above 4 GiB. It is identical to the summary's receipt.
T0 process peak RSS is 46,542,848 bytes. Setup-process peak RSS, scratch usage and aggregate
CPU work were not measured; this does not enlarge the claim into whole-chain resource health.

Per-arm prospective projection remains card §4: 17.73 s construction from recorded remote
A03 phase times, or 41.33 s from Windows, with setup/publication cost previously unknown.
Observed single-chain critical path and summed invocation wall are both 16 s at supervisor
one-second resolution, within 300+5 s. Summed recorded phase wall is 10.297324 s; it excludes
digest work and is not whole-chain time. Aggregate CPU seconds remain unknown.
Post-work publication coverage is the actual successfully written and parsed summary.

## Acceptance boundary and next owner

Technical acceptance is complete for the frozen single invocation. No additional invocation,
retry, alternate stack, torch, local fallback or R09 release follows. Historical A03 failure
and staging/ref-collision evidence remain unchanged. DM owns ordered-rule scientific intake,
the Chinese brief and the next scoped path recommendation. Source additions/deletions and
engineering-scope §4 machinery additions are zero.

scope: none

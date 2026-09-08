# FRRIE A07 / P37 terminal technical E0 — 2026-09-08

The corrected P37 process terminated with **exit 139**, and the retained report
is explicitly **`Fatal Python error: Segmentation fault`**. It is not labelled a
scheduled report: no `Timeout (...)!` header appears. There are 16 current-thread
Python frames and one other thread with `<no Python frame>`. The current stack
reaches original RNG validation through training-tape generation. No cause or
scientific interpretation is assigned here; DM applies the prospective A07 rule.

This corrects Root's preliminary “scheduled stack” label using the actual log.
The 63s supervisor duration alone cannot establish a scheduled report or its timing.
No collection action rearmed a timer, relaunched or executed the target.

## 1. Accepted paths and binding

[A07 card](FRRIE_R09_SCHEDULED_STACK_A07_SCIENCE_CARD_20260908.md) binding at
`81b58964e1c266a7a120dbfde851464489342e4e` and
[P37 transport handoff](FRRIE_R09_SCHEDULED_STACK_A07_P37_TRANSPORT_HANDOFF_20260908.md)
at `f9a785b6caf898ca120778812150de53a4991049` identify this execution.
Node: `hmasd-wsl-node`; supervisor handle:
`frrie-a07-scheduled-stack-p37-43eec21e`, PID 2768577, reported inactive by Root.

The accepted script retains the original P35 cwd
`/home/wu/hmasd-worktrees/frrie-a07-scheduled-stack-p35-43eec21e`, output
`temp/directions/finite_resource_relational_inductive_efficiency/exp/a07_scheduled_stack_p35`,
and `/home/wu/.agent-tasks/frrie-a07-scheduled-stack-p35-43eec21e/process-time.txt`.
The corrected log/status/runner are under
`/home/wu/.agent-tasks/frrie-a07-scheduled-stack-p37-43eec21e`.
The old P35 exit 127 wrapper's six original artifacts remain separate, retained by
P37's preparation record; its zero-scientific-exposure reconciliation is unchanged.
This is one scientific invocation after one failed transport attempt, not two
scientific samples. Collection scientific invocations: zero.

Remote HEAD is original `43eec21e9584c83e5e8d940402d7e4570b454e59`, with no
tracked modifications; only generated `_native/` is untracked. The staged script
readback matches the 1287-byte payload SHA256
`8ed56ed4489b0d211355f74a1e91a07f9ae8ac1efc43cecf77c824a5fc56e51c`.
Helper/stdin hashes match the 30643b7 bindings recorded in the handoff. These facts
preserve command/source identity, not scientific-state or runtime reliability.

## 2. Report frames and limits

The report labels **current thread `0x0000717491b39080`**, most recent first:

| Source-relative file (or stdlib identity) | Line | Function |
| --- | ---: | --- |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/rng.py` | 133 | `validate` |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/rng.py` | 204 | `canonical_bytes` |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/rng.py` | 251 | `block` |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/rng.py` | 273 | `uniform_float32` |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/tapes.py` | 369 | `generate_episode_tape` |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r02/tapes.py` | 247 | `<genexpr>` |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r02/tapes.py` | 246 | `production_training_inputs` |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r02/experiment.py` | 242 | `execute` |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r02/experiment.py` | 560 | `main` |
| `scripts/run_frrie_b01_contact_r09.py` | 9 | `<module>` |
| `/usr/lib/python3.12/bdb.py` | 600 | `run` |
| `/usr/lib/python3.12/pdb.py` | 1738 | `_run` |
| `/usr/lib/python3.12/pdb.py` | 1944 | `main` |
| `/usr/lib/python3.12/pdb.py` | 1971 | `<module>` |
| `<frozen runpy>` | 88 | `_run_code` |
| `<frozen runpy>` | 198 | `_run_module_as_main` |

The separately reported thread `0x00007173b9bff6c0` has `<no Python frame>`.
Its role cannot be assigned from that text. Do not identify it as the watchdog,
a waiting worker or the faulting thread. The current-thread designation belongs
to the fatal report. The extension-module list contains 24 names and is preserved
verbatim in raw stderr and as an array in JSON; presence is not causal attribution.
No explicit truncation marker appears, but this is the bounded Python report,
not proof of complete native frames, memory state or all-thread coverage.

The top report line is `rng.py:133 in validate`; source inspection places this
at the method definition boundary. It does not identify a faulting expression
or C instruction. `experiment.py:242` calls `production_training_inputs` with
`number = update + 1` from the original loop. The stack retains no value for
`update`, `number`, tape index or optimizer counters. It therefore locates a
training-input caller without establishing actual completed updates/episodes/
slots. Source ordering is not a measurement of completed work or publication.

The lower pdb/bdb/runpy frames are the original execution harness. No bounded
capture-helper or traceback-processing frame appears in this reported chain.
There is no ordinary uncaught Python traceback or A05 state record. The scheduled
arming command remains present in the exact invocation, but there is no separate
arming-success receipt or attributable scheduled emission. The fatal record must
not be relabelled based on its proximity to 60s.

## 3. Termination, resources and publication

| Direct fact | Value |
| --- | --- |
| Start / terminal UTC | 2026-09-08 08:36:02 / 08:37:05 |
| Shell Python PID / termination | 2768586 / `Segmentation fault (core dumped)` |
| Supervisor exit / status | 139 / failed |
| Supervisor duration / GNU time wall | 63s / 62.86s |
| GNU time peak RSS | 874680 KiB = 895672320 bytes |
| Admission captured / assessed UTC | 08:36:02.232705 / 08:36:02.233145 |
| Physical/effective available memory | 15636484096 bytes; both passed 4294967296-byte floor |
| Cgroup headroom / aggregate CPU | Unavailable / unmeasured |
| Output files | Only 504-byte `learner_admission.json`; `learner/` empty |
| Summary / A05 capture marker | Absent / absent |
| Completed updates/episodes/native slots | Unknown |

The process-time file belongs to this P37 execution even though its path is under
the P35 supervisor directory. Both recorded durations are below the original
TERM 115s + 5s grace = 120s complete cap. Peak RSS is reported as GNU time provides
it, without asserting aggregate descendant RSS or uninterrupted headroom.
The shell's `(core dumped)` wording is retained; collection did not search for or
open a core dump, and it establishes no retained core location.

Cost context: the original allocation remains one 120s seedless A chain. Observed
single-invocation wall sum is 62.86s; control-plane elapsed and aggregate CPU remain
unmeasured. Previous A06 timing is not a work-equivalent comparator. No pilot,
setup, additional sample or budget extension was performed.
Post-learner coverage remains the accepted A05 fixture/static A07 checks; the
actual learner publication path produced no files here. Missing publication does
not imply zero learning, and no historical conditional counts transfer to A07.

## 4. Retention, technical acceptance and next owner

[Machine-readable E0](FRRIE_R09_SCHEDULED_STACK_A07_RESULT_EVIDENCE_20260908.json)
contains parsed frames, separate other-thread text, extensions, receipts and raw
SHA256/length inventory. The raw collection root in the direction checkout is
`temp/directions/finite_resource_relational_inductive_efficiency/exp/a07_collection_p37/`:
corrected `supervisor/`, fixed-path `process-time.txt`, `output/`, script readback,
remote source/path/hash readback and the two focused source excerpts. Remote
originals remain untouched. These are collections of existing bytes only.

Checks reconcile exit/status, report headers and 16 frames, 24 extension entries,
complete output-file inventory/empty learner directory, exact payload and input
hashes, source state and time receipt. No scheduled report is inferred. DM next
applies card §2's distinction between scheduled and fatal records and its complete
outcome rule; this E0 makes no scientific disposition or next-task selection.
Root integrates the technical evidence. This terminal boundary exhausts the
allocated P35/P37 observation; no retry, rearm, extra sample or cap reset follows.

scope: none

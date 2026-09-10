# B03 actor100 E0 technical result — incomplete pair

**W1 completed; W100 terminated by signal11, supervisor exit139. The allocated pair is
incomplete, Delta_U is unavailable, and there is no paired algorithmic polarity.**
No W100 retry, reference invocation, new seed, model call or successor was launched.

Card §5 damaged-output branch, applied verbatim: “Report the actual failure and counts;
only independent narrower facts survive. No algorithmic polarity.”
Source and checked implementation: `ad2fdfb854e295d6d9dddb229dd17cde58465919`, pushed to
`codex/rcle`. [CM record](RCLE_TBCFV_B03_CM_RECORD_20260909.md) covers the focused check,
independent review, projections, source boundaries and interrupted-app reconciliation.

## Retained measurements and acceptance

[Machine-readable result](RCLE_TBCFV_B03_ACTOR100_RESULT_SUMMARY_20260909.json),
[all4,096 retained evaluation rows](RCLE_TBCFV_B03_ACTOR100_RAW_ROWS_20260909.csv), and
[all200 W1 block curves](RCLE_TBCFV_B03_ACTOR100_TRAINING_CURVES_20260909.json) preserve
eight cells, Y/U/tau/F, per-cell block means and actual raw-gradient/update norms.
W100 curves/final observations remain null, rather than inferred or filled with zeros.

| ACTIVE_CONTINUATION path | Shared FLEX init U | W1 final U | G_U,W1 |
| --- | ---: | ---: | ---: |
| 8→12 | 0.6924397786458333 | 0.6923502604166666 | 0.0000895182291667 |
| 12→8 | 0.7165405273437500 | 0.7163208007812500 | 0.0002197265625000 |
| Equal path mean | 0.7044901529947917 | 0.7043355305989583 | 0.0001546223958333 |

Tau mean40 and tau40 fraction1 in both initialization/final primary paths; final40U is
27.694010416666668 / 28.65283203125. W1's eight-cell secondary U is0.7033447265625;
all eight tau means are40. These are one fitted W1 policy's observations, not evidence
for the W100 intervention. MEI0.05 and all comparison rules are unchanged.

W1 reports12,800 training episodes,200 backward/joint-step calls,200 nonzero steps,
zero zero-steps,2,048 initialization and2,048 final episodes:16,896 retained episodes,
1,081,344 primitive ticks. Each of200 blocks retains eight cells×eight episodes and
step-before-baseline order. Initial norm21.230992499025053; final displacement
0.15598634254049473. W1 final checkpoint is finite CPU FP64 with26,161 scalars.

Both invocations finished initialization: twelve allocated models, two training instances
started, ten untrained helper allocations. W1/W100 initial checkpoint files have the same
SHA256 `9c5ba67eb37dabdb9bdd35913f8664f10cf6b8cf52e1e0d1e772cdf0a7286b53` and their tensors
compare equal. Only W1's completed training counts are known. W100 has no summary, curves
or final checkpoint; its additional training episode/backward prefix is unknown (bounded
by12,800 episodes/200 backward calls). Do not report the planned33,792/400 as actual.
No W100 final panel or reference panel ran: code reaches final evaluation only after the
missing trained checkpoint/summary publication, and the shell stopped before reference.

Readback used only retained bytes:10 run files and6 supervisor files all matched remote
SHA256s; it checked paired initialization, W1 full curve/row counts, finite metrics and
checkpoint, and published the narrower result. No model was constructed, no derivative
or native episode executed. The retained analysis script is82 lines in the runtime root.
Research source is236 lines (184 study+1 initializer+41 Python runner+10 shell); adding
that analysis is318. Focused test is72 lines. Approximate orchestration share is over30%
(runner plus I/O dominate this reuse path); reviewer found no unnecessary §4 machinery.

## Execution and complete costs

Sole observer: this CM. Node `wsl_4070`; CPU FP64, one compute thread. Detached cwd:
`/home/wu/hmasd-worktrees/rcle-b03-actor100-20260909` at the source SHA above.
Run root beneath it: `temp/directions/roster_consistent_latent_exploration/exp/b03-actor100-20260909`.
Supervisor handle `rcle-b03-actor100-20260909`, PID3064366; terminal status `failed`,
exit139, tmux inactive. No live scientific process remains. Start receipt Unix1788975387;
supervisor reports133s duration. The exact generated supervisor `runner.sh` and task log
are retained locally alongside all raw outputs, admissions and timing receipts.

The committed wrapper passed `bash -n`; remote cwd/HEAD and source/preflight surface
matched committed inputs. Shell SHA256
`e5fb812724dd2ab6d1210636a208edb9267045587f669ad839b030a11b071142`.
The supervisor executed the fixed committed list under `timeout1450`, with each complete
interpreter under `timeout600`. `HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python`.
No staging-only failure was a scientific invocation: the initial non-login fetch stalled,
its exact process was terminated; configured login-shell fetch received the commit but
hit an old remote-tracking-name collision. Exact commit was present. A partial-clone
checkout needed the same login environment; its failed creation was reconciled and the
configured-shell detached creation succeeded. No refs were removed or rewritten.

| Charged work | Complete wall seconds | Outcome |
| --- | ---: | --- |
| W1, import/init/training/both panels/publication/process exit | 79.24 | exit0 |
| W100, import/init/failed training prefix/process termination | 53.20 | signal11 |
| Whole sequential remote chain including both admissions | 132.54 | exit139 |
| All focused check attempts | 14.3754106 | final pass |
| Collected-byte readback/publication | 2.2644268 | pass, no model calls |
| Bounded existing-log/binary diagnosis, including SSH overhead | 4.8913502 | no core/backtrace recovered |
| Staging syntax/input check and test parent creation, conservatively charged | 1.1689993 | complete |
| Subtotal before final document arithmetic/check | 155.2401869 | below1,500 |

W1+W100 logical invocation walls sum132.44s; use132.54 chain wall once for cumulative
accounting, not both totals. The132.54s remote execution critical path is measured;
overall first-local-check-to-final-E0 elapsed includes the app restart/authoring/staging
and is unmeasured. Git, network transfer, agent work and external queue time remain
separate/unmeasured. Aggregate CPU is unmeasured; no CPU-efficiency claim follows.
Final arithmetic took0.2081013s; final JSON/CSV-count publication and document check took
0.3392798s complete command wall (publication body0.0362784s). Measured charged work
therefore totals155.7875680s; conservatively charge160s including the final bookkeeping
tail. The result summary retains the measured components and conservative charge.
No600s learned bound or1,500s object bound was reached.

W1 admission at17:36:28UTC: physical/effective15,633,690,624 bytes; W100 admission at
17:37:47UTC:15,638,384,640 bytes. Both passed the4GiB floor immediately before invocation.
Whole invocation peak RSS:572,052KiB W1;821,028KiB W100, also whole-chain maximum.
These are process peaks, not simultaneous aggregate memory. W100 GNU time printed
`exit=0` for its signalled child; the same file explicitly says `terminated by signal11`,
and the supervisor/chain exit139 is authoritative. Never interpret that field as success.
W1 reused the existing native artifact (load0.005519s), with no standalone build pilot.

## Bounded failure diagnosis and feasible next repair

Root explicitly selected diagnosis from existing logs/core within the remaining check
budget; no diagnostic simulation ran. Runtime logs show fatal signal11 and no Python
traceback. A recent kernel event for this interpreter reports read address0x40 and
faulting bytes `4d 8b 51 40`, with R9=0. Accounting for the executable text segment's
0x145000 load offset maps the recorded instruction to0x1d081a, `Array_ass_item`
(ctypes), and the disassembly bytes match. Interpreter SHA256:
`ca420bd4614ae7757b4cd4938b3c663e98d2b631bda518610071d9a4ca0b509e`.
The event also records WSL crash capture for guest pid3064466. Kernel versus supervisor
clock/PID namespaces differ; without the process stack/core their association remains
qualified. This identifies a candidate fault boundary, not its cause or the responsible
array/caller. No native C++ corruption, CPython defect, or coefficient-induced numerical
failure is proven.

Kernel `core_pattern` routes to `/wsl-capture-crash`; that hook is not a regular accessible
file in this guest. WSL logged capture on port50005. No matching core exists in the run
cwd, `/var/crash`, `/var/lib/systemd/coredump`, accessible recent `/tmp` core paths, or
the Windows `wsl-crashes` directory (only older Xorg dumps). Some unrelated private
system `/tmp` directories were not readable; no access override was attempted.

The smallest demonstrated measurement gap is loss of W100's already-required curves:
the study keeps them in memory until training finishes. A future separately selected
attempt can persist those same block rows incrementally and enable Python fatal-stack
capture, preserving the scientific law and budgets. This is a feasible evidence repair,
not a proven crash fix. No source change to shared ctypes/native code, interpreter
upgrade, device change or scientific retry is justified by the retained evidence alone.
DM/Root owns the next bounded decision; no new result invocation remains authorized here.

## Preservation and closeout responsibility

All outputs, initial/final tensors,10 run-file hashes,6 supervisor-file hashes, kernel
excerpt, fault-address analysis and readback script are retained locally at
`C:/Projects/HMASD-worktrees/dm-rcle-a02-20260906/temp/directions/roster_consistent_latent_exploration/exp/b03-actor100-20260909`.
The result JSON inventories retained bytes. Remote tracked checkout is clean; only this
output root and supervisor record are evidence dependencies. The global native cache
under `/tmp/hmasd_rcle_tbcfv_native/` is shared and not a reclamation target.
CM retains the exact detached checkout and generated supervisor wrapper until Root's
explicit integration trigger, then performs its assigned closeout; Root accepts cleanup.

Automatic approval review rejected deletion of CM-owned local test scratch twice with
`blocked by policy`. Exact path and commands remain in the CM record. The scratch is
preserved and no removal bypass/repetition was attempted after that rejection. It is
independent of the signal11 failure and the scientific result.

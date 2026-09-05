# MGTAP B03 engineering contract and execution

Card: `MGTAP_B03_STEPSIZE_SCIENCE_CARD_20260904.md`, base SHA
`da765da0ac607ebac7d6b6e330a2ba7648e0f69f`.

The observable is the complete symmetric scalar-rate panel: METRIC/INTACT and
FREE/INTACT at 0.1, 0.3, 1, 3, seeds 307/311/313, 256 updates and all 17
checkpoints per fit. Global mean three-seed AUC selects one rate per actor;
exact ties choose the smaller rate. The complete panel reports selected D and
paired d, common 0.1 contrast, each selection gain, H, and selected FREE endpoint
oracle gap. No branch is assigned to an incomplete panel.

The implementation reuses B02 numerical functions without changing old files.
Actor parameters are fresh zero-initialized float64 CPU arrays (60 scalars).
SGD is momentum/decay free with gradient clip 5; only its scalar rate changes.
B02 training/evaluation phase labels and PCG64 address law remain unchanged.
Training addresses depend on seed/update/N; evaluation depends on seed/N/pair/
load/epoch, never actor/rate/checkpoint. Evaluation groups live for one seed and
are reused read-only by every fit. Actors, optimizer and learner traces live
for one fit. Persisted arrays retain checkpoint, 60 parameters, and normalized
returns shaped checkpoint x N x pair x load x tape. Oracle data enters only
reporting, never learner inputs or loss. Decoder, population, ordering, counts,
reward, precision, support and inherited scientific side effects are protected.
There is no checkpoint resume, production-route replacement or core edit.

Owned new paths are the B03 runner, its helper, mirrored tests and B03 technical/
result documents. DM owns card/intake/owner items; Root owns shared Portfolio.
Unrelated primary-checkout edits were observed and left untouched. CM works at
`C:/Projects/HMASD-worktrees/cm-n5-b03-20260904` on
`codex/cm-n5-b03-20260904`; implementation has a separate worktree.

Engineering scope section 4 additions: **none**. Existing remote agent-task
and admission are reused. No retry, scheduler, resume, provenance gate, extra
telemetry, registry or compatibility layer is added.

Per-configuration projection before launch: METRIC 11.4792425391 seconds and
FREE 6.1553556643 seconds for each rate over three seeds, from the card's
existing B02 cost law `2*3*(256*u+17*e)`. All eight configurations fit their
individual 60-second caps; no pilot or arm dropping is needed. Each fit stops
at ordinary elapsed checks at 20 seconds; shared setup cap is 20 seconds per
seed; total cap 540 seconds. Completion or retained incomplete/capped outputs
are the terminal boundary; there is no automatic retry.

Execution is prospectively Windows/Linux CPU portable, with no cross-host bit
identity claim. Remote node `wsl_4070`, SSH `hmasd-wsl-node`, interpreter
`/home/wu/.venvs/hmasd/bin/python`, one thread. Exact committed/pushed bytes
will run from detached `/home/wu/hmasd-worktrees/mgtap_b03_20260904`.
Each seed invocation has adjacent node-local `admit-memory && runner` in the
existing supervisor. Raw output roots are
`temp/directions/metric_ground_transport_allocation/exp/mgtap_b03_main_<seed>`.
The existing B02 oracle is loaded read-only from
`/home/wu/hmasd-worktrees/mgtap_b02_20260904/temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_pilot_1907/oracle_returns.npy`.
No source or input staging route is added.

Post-learner path coverage and final technical acceptance are recorded below
when implementation, focused checks and independent review are complete.
Engineering conformance does not establish mechanism value.

## Implemented and inspected

The final diff adds 173 runner lines, 99 scientific reporting helper lines and
127 test lines; old source is unchanged. Independent reviewer
`/root/dm_amx_n5_continue/cm_am_n5_b03/rev_ah_n5_b03` found no material correctness
issue and no section 4 additions. Execution/plumbing estimate is 110 / 399
whole research diff lines = 27.57%. The source-only estimate is 89 / 272 =
32.72%; section 5 explicitly excludes tests only for the new-code line cap,
so the whole-diff denominator is used for orchestration share. Neither code
nor tests were padded to alter that denominator.

Six selection/rule checks passed and one toy end-to-end run plus real CLI
publication passed in 6.53 seconds. The toy checks zero initialization,
common initial return arrays, scalar first-step scaling, raw array/curve
agreement, counts and actual optimizer movement. Synthetic full-grid packets
exercise global selection across three seeds, tie breaking, incomplete-panel
handling, all rule branches and exact formal count totals through publication.
The toy uses the real --oracle loading path. It does not execute 256 updates;
that full learner path is the panel's runtime observation. No prior B03
post-learner failure exists. Publication coverage has no open item; full-run
learner trace finiteness remains to be inspected after collection.

Local command interpreter was `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`;
focused test path is
`tests/experiments/candidates/metric_ground_transport_allocation/mgtap_b03_stepsize`.
Initial test collection exposed a missing brace, and the smoke exposed an
optional Windows RSS assumption; both were fixed before final checks. Peak
RSS on the Windows toy is unavailable (`resources_unmeasured`), consistent with
the card. Toy wall 1.7092827 seconds is not a replacement cost pilot. The
existing pytest unknown cache_dir warning is unrelated.

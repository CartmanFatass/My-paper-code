# VSP03 B04 launch and exit-publication boundary

Binding: [card](VSP03_B04_SCIENCE_CARD_20260908.md) sections2,3,5,6 and
[assignment](VSP03_B04_CM_ASSIGNMENT_20260908.md). No scientific run has started.
SOURCE_SHA is resolved to the accepted pushed source after DM acceptance and Root
integration, then staged into an exact-SHA detached remote execution worktree.
Same configured wsl_4070 node, SSH hmasd-wsl-node, CPU float32, one thread; no fallback.

```bash
VSP03_B04_PAYLOAD=$(cat <<'VSP03_B04_LITERAL'
(
cd /home/wu/hmasd-worktrees/vsp03-b04-p64-SOURCE_SHA || exit
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VSP03_B04_COMMAND='VSP03_B04_STARTED=$(/home/wu/.venvs/hmasd/bin/python -c "import time; print(time.perf_counter())")
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p64_20260908_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b04.py --seed 6 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p64_20260908 --started-monotonic "$VSP03_B04_STARTED" --node wsl_4070'
/usr/bin/time -f 'payload_wall_seconds=%e peak_rss_kib=%M' /usr/bin/timeout --signal=KILL 120s bash -c "$VSP03_B04_COMMAND"
)
VSP03_B04_LITERAL
)
/usr/local/bin/agent-task run vsp03-b04-p64-20260908 "$VSP03_B04_PAYLOAD"
```

The outer subshell returns its actual final command status to the existing agent-task
wrapper's eval. A cwd failure exits only that subshell; no exec replaces the supervisor.
The inner exec of the Python runner is confined to the timed child shell. Existing
supervisor EXIT_CODE/file/status/footer publication remains reachable on success and
failure. No supervisor source is edited, and no new monitor or retry is introduced.

The timeout covers timestamp helper, adjacent admission, imports, one G initialization,
128 training batches and four final evaluations, required output/readback and scientific
process exit. The existing supervisor publishes its real numeric exit afterward.
The timer's payload_wall_seconds is deliberately narrower than the complete boundary.

For complete elapsed accounting, collect the existing supervisor start_time integer
Unix timestamp (written before tmux launch) and the nanosecond modification timestamps
of its exit_code, status and task.log after termination. Use the maximum of those
required publication timestamps minus start_time as a conservative complete receipt
span: it includes startup, admission, learner/output/exit and receipt/footer publication;
the start is rounded down. Report the raw timestamps, span and numeric exit. Use this
complete span, not the lower-level timer, for the120s conformance statement. A missing
receipt or span above120s is reported as that concrete gap; no cap expansion or retry.
The supervisor's subsequent one-second idle sleep is not scientific work or required
publication. No new timer process, instrumentation framework or resource claim follows.

Per-arm cost projection: exactly one seed6 G, inherited admission/import + G init +
128 C(128,40,2) +4 E(1024,40,2) +output/readback/exit publication. B03's3.50s payload
wall is the available planning observation, not an upper bound or scaled estimate.
Complete new wall and aggregate CPU remain unknown. The complete120s cap applies once.

Post-learner coverage: reuse B03 scientific/output review and readback. Static checks
cover B03 default and B04 seed/object/arm bindings. A harmless literal exit7 check of
the existing wrapper postamble validates the new subshell status return without any
scientific imports, model, RNG, episode, learner or evaluation. Normal run alone reads
required primary/count/weight output. Preserve all B03 facts including its null exit.

Fresh physical/effective memory admission each>=4GiB is immediately joined to the
runner by &&. On accepted handle, send node/name/SHA/cwd/log/result/admission/bound to
Root /root and copy DM /root/dm_vsp03_p54_reentry. CM observes until Root ACK, then
retains collection/technical acceptance. Stop at the sole output/exit publication,
120s, or a dependent defect, with no second scientific invocation or local host.

# VSP03 B04 technical source acceptance

Started clean at aaf36703f in the existing shared VSP03 checkout/branch. Applicable
AGENTS and compute configuration are unchanged since B03 collection. This record
covers the minimal B04 source and new payload boundary; science remains DM-owned.

Scope before writing: B04 card section6 requests none of scope-spec section4's
optional machinery. Added none. The shared run function gains one optional object_name
argument defaulting to VSP03_B03, used only in the summary object label. The new28-line
runner fixes seed6 and passes VSP03_B04; the old runner remains seed5 and unchanged.
No learner copy, B01/B02 edit, scientific loop change, RNG relabelling or extra mode.
One G still uses arm1; seed6 therefore supplies Torch40006 and the inherited addresses.

Focused static tests: scientific Python -B -m pytest -q -p no:cacheprovider
--basetemp temp/directions/vsp_03/test/b04_binding_20260908
 tests/experiments/candidates/vsp_03/vsp03_b04/:2 passed in0.11s.
They import no scientific module and check B03/default and B04/seed/object/arm binding.
No scratch was generated (the named basetemp does not exist). Prior scientific/output
review and checks are reused; no old fixture, model construction or trajectory smoke.
The exact new launch block passed remote bash -n through stdin (exit0).

The [launch boundary](VSP03_B04_LAUNCH_BOUNDARY_20260908.md) encloses the payload in
a subshell returning its status to the unmodified supervisor. It removes top-level
exec of /usr/bin/time; the inner exec remains confined to the timed child shell.
A cwd error likewise exits the subshell, allowing supervisor exit publication.

One harmless exit7 check copied the actual existing generated B03 wrapper into a
unique remote temp test directory, changed its file destinations to that directory
and replaced only its eval payload with the new subshell containing timed literal
exit7. The real inherited status/exit/footer postamble executed: numeric exit7,
status failed, footer code7. Wrapper process itself returned0 after its idle sleep,
which demonstrates why its process return must not replace the command's exit receipt.
The old B03 label remains literal inside the copied fixture log; no B03 evidence or
live supervisor path was touched. [Raw wrapper/log/exit evidence](VSP03_B04_EXIT_CHECK_20260908.json)
retains the exact check. Complete receipt span0.353791744s; scientific models/episodes/
steps0/0/0. The created remote temp directory was resolved to its exact owned absolute
path and removed in finally; scratch_removed=true. Old rejected B03 scratch was untouched.

Complete elapsed will use the existing supervisor start_time through latest required
exit/status/log publication mtime, conservatively including timestamp rounding and
startup. The narrower payload timer is separately reported. A missing numeric exit
or complete span above120s limits the corresponding acceptance; no retry or cap
expansion follows. No lower-level timer alone proves complete conformance.

Independent affected-path review, final source commit, DM source intake and Root
integration precede the sole scientific invocation. No B04 scientific run yet.

## Independent review boundary finding

The reused reviewer found one P2 issue in the proposed launch boundary: child timeout
starts after supervisor start and excludes the supervisor postamble. Receipt-span
measurement detects complete120s nonconformance but cannot enforce that hard stop
on the timeout path. CM confirmed there is no omitted existing supervisor-level
deadline and returned the concrete card section5 conflict to DM. Seed/object/status
propagation conforms; no other material finding. No watchdog, manual receipt-writing,
recursive wrapper or supervisor modification was introduced. Source acceptance of
the launch boundary remains pending this named contract resolution; no science run.
See [independent review](VSP03_B04_SOURCE_REVIEW_20260908.md).

## P65 candidate adapter

P65/card section8 at aa2e409f8 now explicitly authorizes one task-local deadline/
termination adapter for complete invocation wall<=120s. This supplies the scope that
was missing in the earlier candidate; it does not erase that review or change science.
The installed supervisor remains unchanged. Its actual start_time precedes detached
startup, and is the original clock consumed by the new deadline.sh/deadline.py adapter.

The shell derives remaining whole seconds with elapsed rounded up, then GNU timeout
contains the Python adapter, admission, runner, ordinary descendants, cleanup and all
authoritative terminal publication/readback plus /usr/bin/time's final line. Its
remaining duration is not reset to120. The Python worker maps the same original start
once to monotonic time, stops scientific work by110s, and ends cleanup by118s to reserve
publication within the outer conservative limit. A subreaper adopts orphaned children;
remaining descendants are killed and reaped before the task terminal receipt. An
unresolved survivor keeps containment active until the hard group kill. All selected
processes stay in the inherited group; no new sessions are created in the frozen route.

The task's own terminal.json is authoritative for task status/termination. No adapter
writes the supervisor's exit_code/status/footer; those actual later observations remain
separate bookkeeping as P65 explicitly permits. Missing required task publication or
an observed failure is retained, never converted into a success or another invocation.

Local compile passed; current candidate changes leave all scientific source, B03 and
B04 runner bindings unchanged against1289f0514 (scoped git diff exit0). Actual installed
Linux headers confirm PR_SET_CHILD_SUBREAPER=36; timeout help confirms default child
containment and the use of uncatchable KILL. The existing seed/object/status checks
remain reused. Independent shortened non-scientific lifecycle tests and review remain
pending before acceptance. No B04 scientific run or prior scratch-cleanup retry.

## Revised P65 startup containment candidate

Candidate28164ecb4 supersedes the preceding GNU-timeout launch boundary. The latter
charged startup time but did not enforce a stall before timeout arming; the independent
finding remains recorded. The existing systemd user manager now arms a119s oneshot
startup timer before ExecStart, with immediate cgroup SIGKILL on expiry and a1s margin
inside the unchanged120s cap. The manager's pre-start monotonic origin is passed to
controller, payload, admission and runner. This is one task-specific transient unit,
not an installed/standing service or global supervisor edit.

The controller launches the unchanged agent-task with a private tmux server inside
its cgroup. After child exit and real supervisor receipt collection, it kills/reaps
remaining private control descendants and writes/reads the authoritative whole-task
terminal receipt. Private TMUX_TMPDIR access and manager journal commands are recorded
in the revised launch boundary. Missing task publication on a hard kill remains a
failed observation; manager outcome and actual supervisor files stay distinct.

Local AST parse passed for both Python adapter files. The exact protected scientific
source and seed6 runner diff against1289f0514 is empty. The production private socket
path is105 bytes, within Linux's108-byte sockaddr_un field including terminator.
The reused independent reviewer is checking the startup/unit/private-server and final
publication paths with harmless shortened fixtures. This paragraph does not accept
that candidate or launch science; final review/check evidence follows below.

## Final P65 technical acceptance

Accepted source candidate: b5d605bf4f39b5ab18f01c98e04dc07e53764354. The independent
revised-unit fixtures in VSP03_B04_DEADLINE_CHECK_20260908.json all passed in25.511s
on wsl_4070 using exact committed launch/control bytes, a TASK_DIR-only copy of the
installed supervisor, and no scientific model/episode/update exposure. With cap10s
and reserve4s: actual nonzero exit7 published7 in0.395s; work timeout published124
in6.043s; pre-controller startup stall terminated by manager SIGKILL in9.024s;
stopped controller terminated with its cgroup in9.126s; earlier payload0 followed
by actual shell7 published final7 in0.305s. Known and sampled cgroup PIDs were absent,
final cgroups empty, and owned scratch removed. Hard-kill cases correctly lacked
final publication. Single-origin and command metadata propagated through private tmux.

The reviewer-found missing command environment was fixed in2e02bce40. The DM-found
actual-exit precedence gap was fixed inb5d605bf4 and exercised independently. These
repairs change task evidence plumbing only; science/seed/object bytes remain at1289.
The revised independent review dispositions and original rejected boundaries remain
in VSP03_B04_SOURCE_REVIEW_20260908.md. No unresolved technical finding remains on
this bounded path. This accepts engineering conformance, not scientific outcome.

One important observation distinction: systemd-run --wait returned1 for each failed
unit even when ExecMainStatus was7,124 or9. Its numeric client return is not the task
exit. Collect the actual manager ExecMainCode/ExecMainStatus/Result, journal, controller
receipt and unchanged supervisor files. Use the explicit private TMUX_TMPDIR for live
status. Successful unit state can unload; preserve the --wait output/journal and
receipt. No scientific invocation has started; DM source acceptance and Root integration
are the remaining prerequisites already specified by this assignment.

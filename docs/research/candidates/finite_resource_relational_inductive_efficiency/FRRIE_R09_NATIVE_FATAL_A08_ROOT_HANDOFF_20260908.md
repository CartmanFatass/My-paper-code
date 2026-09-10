# FRRIE A08 / P39 native first-fatal method handoff — 2026-09-08

**COMMAND_NOT_ACCEPTED / LIVE_INVOCATIONS_0.** Existing systemd facilities can
cover GDB and its inferior from target creation through cgroup-wide KILL, but
the investigated command does not establish the card's complete120s clock across
frontend/unit-request time before its service timer. No Root-ready launch literal
is frozen. No service, GDB, inferior, fixture, target import, setup or new core
lookup was executed. The retained P39 result is not repeated.

Authority: [A08 card §§1–4](FRRIE_R09_NATIVE_FATAL_A08_SCIENCE_CARD_20260908.md)
at `ecd581786e99d9e2e5addebe2fb2da1f20964f30`, P39 at
`bbdafe545315735bac5b4ebc8ef04d5ba7b0b541`, and the same CM's
[retained-material result](FRRIE_NATIVE_CONTEXT_P39_RETAINED_EVIDENCE_20260908.md).
Both DM and Root assigned this bounded existing-facility static inquiry. The
complete-startup requirement comes from P39's complete<=120s/all-startup clause
and A08 §§3–4; it is not a new DM launch rule. DM highlighted accounting for
frontend/unit-request time under those existing clauses; Root directed a bounded
handoff or gap.

Starting checkout: `C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`,
`codex/frrie`, tracked-clean at the card revision. Only this new handoff is authored;
DM's owner packet/card and all source, old inputs and unrelated paths are preserved.

## Established method facts

Reuse the [P36 GDB capability/gap](../capability_bound_semantic_currentness/CBSC_B05_NATIVE_FATAL_P36_ROOT_HANDOFF_20260908.md):
GDB15.1 is installed, but its inferior's separate-pgrp interval precedes
post-startup EXITKILL. No GDB inventory or containment experiment was repeated.

Read-only host configuration shows PID1 is systemd; WSL configuration enables
it. The current user manager reports version255.4-1ubuntu8.17 and state `running`,
with ControlGroup `/user.slice/user-1000.slice/user@1000.service`. The user's
cgroup.procs is owned by wu and writable; installed systemd-run and local manuals
are present. These are configuration facts, not a successful service start or a
measurement of target containment.

The candidate uses existing transient **Type=oneshot**, explicit
**TimeoutStartSec=115s / TimeoutStopSec=5s**, KillMode=control-group,
SIGTERM then SIGKILL, SendSIGKILL=yes, no restart or remain-after-exit. The
installed manuals describe oneshot as remaining in startup until its command
exits, and control-group termination as covering all remaining unit processes.

The [v255.4 service source](https://raw.githubusercontent.com/systemd/systemd-stable/v255.4/src/core/service.c)
shows `service_spawn` arming the start timer at line1666 before process spawning;
oneshot uses `timeout_start_usec` at lines2381–2392. TERM handling calls the unit
kill context and arms the stop timer at lines2113–2135. The
[execution source](https://raw.githubusercontent.com/systemd/systemd-stable/v255.4/src/core/exec-invoke.c)
attaches to the cgroup at lines4197–4218 before target exec at5219. Descendants
inherit this cgroup despite a process-group change. This supplies a static
creation-through-KILL route for the service's GDB/inferior and addresses P36's
specific early-pgrp gap. It does not put earlier frontend processing under that
service timer. The upstream versioned sources support the interpretation of the
installed manuals; the Ubuntu-patched executable was not rebuilt or proven
byte-equivalent, and no live scheduling/ptrace behavior was tested.

## Exact remaining gap

The draft's sequence is supervisor → dispatch shell → systemd-run/user-manager
request → service timer → time/env/shell → adjacent preflight → GDB → inferior.
The115+5s timer covers service startup, admission and all scientific/reporting
work, but is armed only after the earlier request path. That earlier elapsed
time has not been bounded. Consequently the draft cannot claim that its complete
chain fits120s, even though its service portion has the required timer.

A separate timeout that kills only the systemd-run frontend would not cancel an
already accepted unit, so it cannot silently close this gap. A smaller service
timeout plus an assumed frontend margin also lacks an enforced bound on that
margin. No extra startup allowance or change of the cap origin is accepted.
The missing fact is **one deadline/termination method spanning frontend request
acceptance and all subsequently created debugger/inferior work**, without a late
accepted unit surviving beyond that deadline. This is a method gap, not an
observed escape, resource violation or scientific negative. It does not establish
that every existing-facility method is impossible.

## Completed input work and its limits

Unaccepted draft scripts in the ignored receipt directory preserve the original
A06 Python tail byte-for-byte: original43ee source,306 helper/stdin, P22 system312
runtime/root3/full schedule and initial pdb continue/q/EOF; no scheduled arming.
The prospective native command has one `run`, selected SIGSEGV/SIGBUS/SIGILL/
SIGFPE/SIGABRT stop/print/nopass, `bt 32` with frame arguments suppressed, `x/i $pc`,
the card's18 named registers, `info symbol $pc` and `info proc exe`, then kill/quit.
Normal ASLR is explicit; auto-load, downloads and startup shell are disabled.

Each report/kill/quit is a separate GDB -ex argument. Versioned
[GDB15.1 main.c](https://raw.githubusercontent.com/RTEMS/sourceware-mirror-binutils-gdb/gdb-15.1-release/gdb/main.c)
lines595–607 catch errors for each argument and iterate onward; lines1188–1189
apply -iex before symbol-file processing. Thus a report-command error need not
skip the later kill/quit. Reused P36 fork/inflow source supports inherited stdin
without a replacement tty; no live inferior verified that path. These command
facts do not override the incomplete total-clock method.

Both draft shell scripts passed nonexecuting `bash -n` with exit0/empty output;
static argv checks found one run and18 registers and matched the original A06
Python tail. Their `static_acceptance.json` explicitly says
COMMAND_NOT_ACCEPTED and launch_authorized=false. **Do not stage or dispatch
these drafts.** No candidate service identity or GDB process was created.

## Bounded engineering proposal and return

Select one focused static follow-up on a timer-outside-creation recipe using
existing util-linux PID-namespace/parent-death facilities, only if the assigning
route accepts that task. A preliminary upstream unshare source read located its
parent pidfd check and parent-death signal path, but installed build support,
namespace permission/configuration, inherited identity/proc semantics and the
complete deadline were not established; this is not a second accepted method.
No unshare invocation or namespace experiment occurred.

Proposed deliverable: one exact existing-binary containment command whose outer
clock starts before utility/debugger creation, with static installed-version and
kernel/configuration support for parent-death/race handling and forced removal
of all namespace descendants; explicitly preserve UID/environment/proc needs of
the original runtime. Stop at a concrete remaining gap. Limit work to relevant
source/config reads, command/syntax acceptance and one handoff; no utility code,
installation, target/inert process, runtime containment test or scientific sample.
Any requirement beyond those bounds returns for task selection rather than being
performed here. This is a concrete engineering proposal, not authorization or a
request for Root to design the method.

Receipts are under `temp/directions/finite_resource_relational_inductive_efficiency/exp/a08_preparation_p39/`:
`systemd_config_and_man.txt`, versioned `service.c`, `exec-invoke.c`, `gdb-main.c`,
preliminary `unshare.c`, unaccepted `observation.sh`/`dispatch.sh`, static checks
and `METHOD_STATUS.txt`. The initial incorrect upstream tag URL and partial HTTP
transfer were repaired by static source retrieval; neither invoked a host target.
DM's `owner_packet.json` is preserved.

`static_host_read_costs.json` records the five enclosing shell calls with host
configuration or syntax operations:1.1098162s (card/config read, final absent
sysctl caused exit1),0.5737684s (manager/cgroup/manual read, exit0),2.4326051s
(manager environment/manual plus local GDB source retrieval, exit0),0.6711339s
(retained manager/manual read, exit0),1.2269812s (two syntax checks plus local
draft construction, exit0). Their sum is6.0143048s; these are enclosing shell
measurements, not remote-only execution times. The final retained read and each
syntax SSH subprocess had20s timeouts; none remained live. No new static-read
wall cap was assigned, and P39's earlier30s core lookup budget was not reused.
The native120s allocation was not started. Local source-fetch failures and
repairs were control-plane reads, not target or service work.

Per-arm cost remains the card's one120s ceiling; frontend/report overhead is
unmeasured, not extra budget. Prior A07 timing is no native-observation forecast.
Post-learner coverage remains the existing A05 recipe; no native report or learner
publication was produced by this preparation. Actual scientific exposure here is
zero. DM/Root receives this exact method gap and proposal; no launch follows from
this handoff, and the conditional live allowance remains unused.

scope: none

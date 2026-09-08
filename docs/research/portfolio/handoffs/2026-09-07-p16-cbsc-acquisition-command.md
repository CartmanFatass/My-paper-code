# P16 CBSC bounded acquisition-command engineering — 2026-09-07

This incremental command replaces only the exhausted P15 CBSC metadata route.
Retain the other P15 direction chains and their individual return routes. This
changes no lifecycle, priority, scientific object, or result-bearing allocation.
Owner reviews at this boundary returned [] using the configured local Python.

## Target and deliverable

Root resumes `/root/dm_amx_cbsc_next` in the existing
`C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`, branch `codex/cbsc`.
First finish/integrate the pending P15 DM intake. Then use the same available CM
that authored `a463df10accb1caf0571ebf25575f0f64ea183a2` to prepare and implement
one task-specific command for the supported local Windows direct acquisition,
transfer, and remote setup route. If that CM cannot resume, restore the configured
CM role on the same checkout and bounded assignment; do not create another branch.
DM owns the prospective card and full implementation spec; CM owns the command.

## Inputs and preserved semantics

Read `CBSC_LOCAL_ACQUISITION_P15_ROUTE_NOTE_20260907.md` at the above commit,
especially Full work and concrete command gap, and the final P15 DM intake.
Use the referenced existing ROOT_HANDOFF/PATH_ADDENDUM only for the exact 23 pins,
21 retained remote containers, URLs, original setup/import command, and source
bindings. Preserve FRRIE metadata `aa44d72ec` as shared artifact evidence, all failed
attempts/partial files, RAW-only B04 and the missing STRUCT observation.
Local .NET UseProxy=false/default TLS/no credentials/no redirects is the observed
changed condition; HTTP 200 headers do not establish complete body transfer or speed.
No package, interpreter, device, learner, comparator or scientific meaning changes.

## Engineering scope and acceptance

This explicitly supersedes P15's no-new-source boundary only for a disposable
single-task command enclosing local acquisition, transfer and remote setup/import.
Before coding, DM states the required cross-node boundary in the prospective card
under ENGINEERING_SCOPE_SPEC section 4 and supplies the complete identical code
spec. Root applies the existing first-three-new-CM comparison enrollment before
coding if enrollment remains; do not reserve, replay or add a fourth batch.

Use existing OS/process tools and the configured remote supervisor. Account for
all local and remote work in the existing 600 s complete bound, with the existing
540 s work cutoff retained where applicable. Local acquisition/setup/transfer must
consume that same budget; no fresh full remote budget starts afterward. Remote
work must enforce its remaining bound independently of the local SSH connection.
Specify and verify bounded termination of started work on timeout, transfer
failure and lost client connection. No standing service, scheduler, retry/resume
framework, background monitor or generic multi-node framework is requested.

Deliver the command, minimal focused engineering checks with fake transfers and
processes, exact future launch literal/source/runtime/output bindings, and the
termination/accounting argument. Tests must exercise timeout/failure boundaries,
not download wheel bodies or install/import the actual target dependencies.
If the complete bound cannot be expressed with this limited command, return the
precise remaining technical gap without growing the assignment into infrastructure.
Independent review covers the cross-node deadline/process-termination behavior;
reuse ordinary CM review routing and proportionate checks.

## Budget, integration and return

Zero network requests, real wheel-body downloads, actual dependency installation,
imports/probes, training or result-bearing invocations are allocated. The two unused
P15 metadata requests do not transfer into this command. Engineering fixture checks
use inert/fake work only; no throughput claim or scientific result follows.

Root integrates accepted explicit-path commits and returns the accepted command to
this DM for prospective execution readiness and a requested complete-chain budget.
Then report that concrete execution-allocation need to Portfolio; do not launch.
If engineering ends with a scoped blocker, report it immediately for the next
command. Ordinary dispatch/integration facts remain in Root's log. Count CBSC only
while this new native work actually advances, once regardless of CM/comparison arms.

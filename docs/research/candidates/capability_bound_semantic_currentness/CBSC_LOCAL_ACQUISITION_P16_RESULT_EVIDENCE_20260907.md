# CBSC P16 — E0 command preparation evidence

**One complete command is prepared under documented clock/scheduling assumptions.**
The final focused suite has 18 passing cases and independent review has no remaining
material finding within those assumptions. This is A/RECON engineering evidence;
no actual body delivery, remote setup/import or algorithm result is established.

## Definition, source and rule applied

Card at `a3e3c2cba713bc1eda1f18e327f6f188bd16317b`:
[Question, primary observable and reading](CBSC_LOCAL_ACQUISITION_P16_SCIENCE_CARD_20260907.md#question-primary-observable-and-reading).
The original engineering rule, applied verbatim:

> Reading rule: accept command preparation only if the delivered source, fake checks
> and independent review support the specified complete boundary and preserved inputs.
> Otherwise return the precise technical gap within this assignment. Neither result
> establishes actual acquisition/import readiness, throughput, a proxy diagnosis or
> an algorithm effect. The accepted command returns through Root for a separately
> selected execution allocation; it is never launched by P16 preparation.

Implementation: `5828af584c5f5e6764f5a44c9951473d82bf04ad`; exact future handoff:
`35a4fcaeabb8f8590ac0ac4a410327414bc4ef63`. Root integrated those at
`3d565bf223ae4a8bfe432cf23423cfa259dbbd5c` and recorded the receipt at `9a23d97ff`.
DM compared the eight committed source/test blobs with that main revision; all
match. Command source remains distinct from historical input literal
`71131d728a0b5f04663301e3d838e699ce70af41` and unchanged preflight
`ec8866b3968fcb1566976ce405d7c552d4d9a5de`.

The independent unit here is the delivered command implementation. Eighteen test
cases are not independent training runs or empirical acquisition observations.

## Directly inspected behavior and preserved work

DM inspected the actual entry point and all six task helper files, the changed
test boundaries and final raw pytest output. No CM check or command was rerun.
The new entry point captures its local origin before task imports/CLI/bootstrap,
owns an atomic kill-on-close Windows job, and limits work to that origin + 540 s.
A one-shot in-process timer covers complete local publication to origin + 600 s.

The remote BOOTTIME sample predates its receipt on Windows. The mapping is
`remote_sample + (local_remaining_at_receipt - 1) / 1.01`; later transfer and
dispatch use that original absolute deadline. Linux helpers arm one-shot absolute
BOOTTIME timers; detached setup owns one process group. Receiver and short clients
have their own bounded paths. Remote completion/publication uses the work deadline
plus 59 s. These are inspected source mechanisms, not measured Linux behavior.

The argument assumes a maximum/minimum elapsed-clock rate ratio at most 1.01,
local monotonic seconds measuring the complete bound, and ordinary OS scheduling.
It assumes no synchronized wall-clock epoch. Host/VM suspension and clock-domain
restart are unsupported. A restart or exhausted deadline starts no next phase.
Actual clock-rate/scheduling behavior and Linux timer/group/supervisor operation
were not probed; no measured timing guarantee is inferred from the source.

The unchanged input set is 21 named old container links, 23 install pins and the
same metadata acceptance expression. Descriptive object/source/seed fields alone
change. The two exact bodies remain 955,455,844 and 156,503,769 bytes; their
combined 1,111,959,613 bytes move once to Windows and once to the remote receiver.
New files/partials are separate from all old evidence. The .NET client disables
proxy, redirects, default/explicit credentials and cookies, retaining default TLS.
It streams two sequential full GETs without retry, fallback, ranges or resumption.

SSH stdin streaming is the bounded transfer implementation on the configured SSH
route. It replaces an otherwise unbounded scp receiver without changing packages,
body order, completeness or the whole budget. There are four prospective SSH calls:
clock mapping, receiver, supervisor launch and collection. The future chain keeps
local and remote setup admissions, one system-Python venv, one full offline binary
install and one original NumPy/Torch metadata publication/readback. No source stage,
admission or real invocation occurred in preparation.

## Focused checks, corrections and independent review

The final raw output reports **18 passed in 2.84 s**, one benign pytest configuration
warning for disabled cache-provider `cache_dir`; CM reports 3.344 s command wall.
CLI help and whitespace checks also passed. The tests exercise inert Windows
child/grandchild exit on timeout/controller loss, including loss before child resume,
and an independently bounded fake remote process after a separate client exits.
They also exercise fixed inputs, reduced remaining time, scheduling delay, exhausted
phases, partial body/transfer/launch failure, metadata absence and successful readback.

Preserve the earlier outcomes: first run 1 pass / 12 setup errors due to a missing
basetemp parent (0.65 s); after that fixture directory correction, 13 pass (2.68 s).
An expanded fixture run had two Windows MAX_PATH failures and 16 passes (3.08 s).
Replacing those irrelevant long-path link operations with the specified fake link
boundary retained all 21 names; the corrected run had 18 passes (3.04 s), followed
by the final 18-pass run. These five reported pytest durations sum to 12.29 s;
they are not complete engineering elapsed time or candidate cost.

The independent reviewer `review_p16` originally identified four material code
issues: delayed clock conversion, non-atomic Windows job assignment, multiple
remote groups and unbounded remote publication. Their recorded corrections are,
respectively, retaining the original absolute deadline, atomic STARTUPINFOEX job
assignment, one setup group, and an absolute timer through publication/cleanup.
The final documentation correction replaced an individual-clock allowance with
the actual maximum/minimum relative-rate assumption.

The same CM supplied the existing reviewer's final text for intake, without a new
review or check:

> No material findings remain within the declared assumptions. The four original
> code findings are resolved. Existing evidence remains 18 passing focused tests;
> Linux timer/group and supervisor behavior were source-reviewed, not runtime-tested.

This is independent engineering review evidence, not independent empirical
acquisition evidence or execution authorization. Its dispositions and limits are
also recorded in the immutable [CM handoff](CBSC_LOCAL_ACQUISITION_P16_ROOT_HANDOFF_20260907.md#focused-acceptance-and-independent-review).

## Counts, scope and receipts

Stdlib parsing/counting of committed source confirms 764 new non-test source lines,
91 runner lines, 392 test lines, 21 containers, 23 pins and two complete body inputs.
These fit the 2,000 / 600 source budgets. The five reported pytest durations are
below 300 s; no section 5 breach is reported or observed. Total engineering wall,
aggregate check-process wall and CPU/RSS are `resources_unmeasured` where absent.

The orchestration serves the card's named task-specific multi-node/process and
minimal phase/deadline boundary (card lines 92–95). No retry/resume framework,
standing watcher, scheduler, service, generic transport, hash gate, registry or
internal-schema machinery was added. The boot identifier belongs to the clock
domain mapping, not a source/provenance predicate. No scientific semantics changed.

Compact receipts under the shared checkout:
`temp/directions/capability_bound_semantic_currentness/exp/local_acquisition_p16_preparation_20260907/`:
`pytest_final.txt`, `contract_counts.json`, `dm_intake_counts.json`.
Earlier check/review outcomes are preserved in the committed handoff and the
existing native CM/reviewer returns; DM did not reproduce them.

Actual acquisition/metadata/SSH/supervisor/admission calls, wheel-body bytes,
candidate creations, installs/target imports/probes, scientific host/model/RNG,
learner/optimizer/evaluation calls: **all zero**. Ordinary code-control Git delivery
and inert engineering processes are distinct from that exposure line.

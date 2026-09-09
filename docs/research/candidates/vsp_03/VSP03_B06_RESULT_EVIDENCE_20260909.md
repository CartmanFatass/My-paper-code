# B06 completed three-fit technical acceptance

All three selected fits completed and are technically accepted at frozen source
edb74aaf5292600480763403cd30cbd733dd1583. Exactly one invocation per fit, with no
failures, retries, replacements, resume, fallback or extra scientific validation.
This completed-batch section supersedes pending statements in the retained sequential
collection history below. Original DM owns full scientific intake and prediction scoring.

| Fit | D128 greedy minus R0 | Primary D512 | Paired Q | D512 greedy minus R | Complete wall s | CPU s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
|10801|0.02076171875|0.02599609375|0.005234375|0.024599609375|8.888241|8.762|
|10802|0.01107421875|0.0145068359375|0.0034326171875|0.0131884765625|8.718389|8.712|
|10803|0.0000439453125|0.0096875|0.0096435546875|0.0098388671875|8.380174|8.313|

Three-fit primary arithmetic mean **0.016730143229166668**, descriptive sample SD
(ddof1) **0.008378536806060969**. Q descriptive mean0.006103515625, sample
SD0.003195385771193459. Per-fit Q conditional SD/SE comes directly from paired-world
changes; independent endpoint variances were not added. The independent unit is one
continuous fit: n=3, not6 endpoints or24 mode panels. Across-fit SD includes evaluation
noise and is not pure training variance. No old128 pooling or best-fit selection.

Full four means, five contrasts, conditional SD/SE and native opportunity accounting
at both endpoints are retained in [aggregate](VSP03_B06_AGGREGATE_20260909.json) and
the three COLLECTION JSON files. Each ARTIFACTS tar.gz holds the complete original
native rows,512 curve rows, two snapshots and admission/terminal/payload receipts.
Raw data was read back without constructing another model or evaluating another world.
All8192 native rows per fit, five contrasts at both endpoints, rule-panel identity,
paired Q and all1536 training entropy coefficients were checked from retained bytes.

Summed complete wall **25.986804s**, aggregate CPU **25.787s** (each unit reports
milliseconds), study elapsed **457.616116s** from first manager origin to last
Finished journal event. Study elapsed includes monitoring/collection/control gaps;
it is not summed machine time. Each complete fit stays under its60s cap. Prelaunch
13.012736-16.766912s per-fit extrapolation remains an estimate, not a measured bound.

Actual totals:3 models;1536 backward calls and Adam steps;196608 training episodes;
24576 evaluation episodes;221184 total episodes;8847360 team ticks;17694720 target
transitions;1194757 gradient rows;1360653 all decision rows;26125 model rollout calls.
Each fit retains initial/first/128/512 scale and displacement. Main learner RSS
maximum494186496 bytes. All fresh same-node admissions passed, while cgroup headroom
is unavailable. No additional test or scientific exposure was needed for collection.

Card section4 reading rule retained for DM intake: final512 above both R0 and R
supports the sampled longer-budget controller; positive Q with native accounting
supports budget-sensitive improvement along these paths. This does not isolate pure
optimization, a unique MARL cause, stable superiority or convergence. Signs and sizes
inside MEI remain visible. No successor is selected by this engineering acceptance.

## Final fit10803 collection

Root confirmed Monitor adoption and terminal2026-09-09T22:55:21.6980135Z: finished,
exit0, tmuxfalse, PID3077211. Complete wall8.380174s, CPU8.313s, learner RSS494153728
bytes; physical/effective admission15608881152 bytes. Controller and payload exit0;
no timeout/error/remaining descendants.512 updates,392143 gradient rows,446850 total
decision rows,8709 rollout model calls. Q conditional SD0.2419800507548193,
SE0.007561876586088103. All selected artifacts and counts are intact.

## Final retention inventory and next owner

Preserve scientific output roots and adjacent _admission.json, _terminal.json and
_terminal.payload.json receipts under /home/wu/projects/HMASD/temp/directions/vsp_03/exp:

- b06_10801_20260909
- b06_10802_20260909
- b06_10803_20260909

Execution worktree: /home/wu/hmasd-worktrees/vsp03-b06-edb74aaf5292600480763403cd30cbd733dd1583.
Supervisor wrapper directories under /home/wu/.agent-tasks:

- vsp03-b06-10801-20260909
- vsp03-b06-10802-20260909
- vsp03-b06-10803-20260909

Private socket directories are each scientific output base plus _terminal.tmux.
No live execution remains. Root explicitly requested preservation until its subsequent
verified-closeout trigger. Original CM then owns authorized wrapper/worktree closeout,
with disk and worktree-registration absence checks. No scientific evidence deletion.
The designated local authoring checkout/branch remains in use by DM.

Two local mocked-test scratch directories remain under the separate automatic approval
rejection in technical acceptance. No bypass or repeated rejected deletion occurred.
This cleanup blocker does not alter completed runtime or scientific observations.
Source and all evidence are published; Root integrates, original DM performs intake.
No further scientific invocation remains allocated.

# Sequential collection history

## Fit10801 accepted

Source edb74aaf5292600480763403cd30cbd733dd1583. Direct independent monitor adoption
and terminal receipt confirmed by Root at2026-09-09T22:47:53.0771610Z: finished,
exit0, tmux false, PID3076352. Raw scientific outputs, both snapshots and admission/
terminal receipts are retained in VSP03_B06_10801_ARTIFACTS_20260909.tar.gz;
VSP03_B06_10801_COLLECTION_20260909.json includes summary, admission, terminal,
raw systemd journal and artifact readback. Launch and staged bytes are in adjacent
10801_LAUNCH and STAGING records. No scientific re-execution was performed.

Complete manager-origin through journal Finished wall8.888241s (<60s); this includes
admission, learning, output, actual process exit and descendant cleanup. Systemd
aggregate CPU8.762s (reported millisecond precision). Controller/payload exit0,
no timeout/error/remaining descendants. Main learner peak RSS494186496 bytes;
unit memory-peak9.9M is a distinct supervisor observation, not substituted for learner
RSS. Same-node physical/effective admission15192563712 bytes passes4GiB; cgroup
headroom unavailable, not asserted zero. One compute thread is source-enforced;
no live thread census was added. Three-fit summed wall/study elapsed remain pending.

One model,512 backward/Adam steps,65536 training episodes,8192 evaluation episodes,
73728 total;2949120 team ticks;5898240 target transitions. Gradient rows405660,
all rollout decision rows460422, model rollout forwards8712.512 curve rows,
initial/first/128/512 scale fields and exactly128/512 weight snapshots retained.
Artifact readback recomputed native accounting on8192 rows, all five contrasts per
endpoint and paired Q. R0/R rows agree exactly between panels. Scientific world/
model construction count for collection is zero; no extra held-out evaluation.

D128=0.02076171875; primary D512=0.02599609375; Q=0.005234375,
conditional paired-world Q SD0.219871871846595, SE0.006870995995206094.
Both endpoints retain all four means, five contrasts and opportunity accounting.
No three-fit mean is reported with only one collected fit. DM owns interpretation.
The intact result permits continuing the already allocated10802 and10803, with
one invocation each, unchanged source/semantics and fresh actual-node admission.

## Retention and cleanup inventory

Remote exact-SHA checkout /home/wu/hmasd-worktrees/vsp03-b06-edb74aaf5292600480763403cd30cbd733dd1583
is still required by the two unlaunched fits; retain until final batch collection
and Root integration/retention trigger. CM owns later verified worktree unregister/
removal and task-wrapper closeout. Fit10801 wrapper directory:
/home/wu/.agent-tasks/vsp03-b06-10801-20260909; private socket directory:
/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b06_10801_20260909_terminal.tmux.
Scientific output root plus admission/terminal/payload receipts remain evidence;
no evidence deletion is requested. Local test scratch cleanup remains the separately
recorded policy blocker in technical acceptance; it does not impair this result.

## Fit10802 accepted

Root confirmed Monitor adoption/terminal2026-09-09T22:52:39.1577029Z: finished,
exit0, tmuxfalse, PID3076799. Collection and raw artifact archive use the matching
10802 names. Complete manager-through-Finished wall8.718389s; aggregate CPU8.712s;
learner RSS493867008 bytes; actual-node physical/effective admission15194279936 bytes.
Controller/payload exit0; no timeout/error/remaining descendants. Source unchanged.
512 real steps,73728 total episodes,2949120 ticks,5898240 target transitions,
396954 gradient rows,453381 all decision rows,8704 rollout model calls. Both selected
snapshots and all512 curve rows retained. Readback verified all8192 native rows,
all endpoint comparisons, identical rule rows, original entropy schedule and paired Q.
Primary D512=0.0145068359375; Q=0.0034326171875, conditional Q SD0.248953546626463,
SE0.007779798332077. No new scientific work occurred during collection. The intact
fit permits the last allocated10803. No three-fit aggregate is reported yet.

Additional cleanup inventory: /home/wu/.agent-tasks/vsp03-b06-10802-20260909 and
/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b06_10802_20260909_terminal.tmux;
scientific root and receipts remain retained. Same CM/Root cleanup event as above.

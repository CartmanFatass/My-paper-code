# B06 technical collection — allocated batch in progress

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

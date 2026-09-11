# VSP03 B04 P64/P65 — prelaunch source intake

**P65 source b5d605bf4 is accepted at section 5; Root integration precedes the sole
P64 invocation.** The complete-boundary correction and five independent shortened
checks resolve the named findings. No B04 scientific run has started. Sections 1–4
retain the earlier rejected candidates and their original technical meaning; their
findings were repaired, not overruled or converted into a result about G.

## 1. Evidence checked and the controlling requirement

DM read candidate commit **`1289f051494306daf17d8844ca7c13c2a21d3b13`**: the actual
two-line shared-driver change, thin B04 runner, complete independent
[review](VSP03_B04_SOURCE_REVIEW_20260908.md),
[technical record](VSP03_B04_TECHNICAL_ACCEPTANCE_20260908.md),
[candidate launch body](VSP03_B04_LAUNCH_BOUNDARY_20260908.md) and raw
[harmless wrapper check](VSP03_B04_EXIT_CHECK_20260908.json). The unchanged B03
scientific functions/review and [B04 card](VSP03_B04_SCIENCE_CARD_20260908.md)
sections 2, 3, 5 and 6 were the acceptance references. Tests and scientific functions
were not rerun by the DM.

[P64](../../portfolio/handoffs/2026-09-08-p64-vsp03-independent-greedy-instance.md)
requires, verbatim:

> fix the new launch payload's top-level `exec` interaction
> with the existing supervisor so its numeric exit is actually published inside
> the same complete cap.

It also fixes one 120s complete admission/import/train/evaluate/readback/publication/
exit cap with no stage reset or extra grace, and no new supervisor framework. The
card's matching stop condition remains in force. An observed complete duration
comfortably within 120s could establish that invocation's measured conformance;
such a scientific observation does not yet exist.

## 2. Conforming work and the remaining gap

The shared run function adds only `object_name="VSP03_B03"` and uses it in the
summary. The new runner fixes seed 6 and object VSP03_B04. B03's seed-5 CLI/default
binding and B01/B02 remain unchanged. G arm 1 and initialization 40000+seed give
G1/Torch40006. There is no changed learner, rollout, metric, native reward, information,
RNG address or evaluation path, and no copied training loop or old weights.

The two focused static checks passed in 0.11s; the new shell block passed remote
`bash -n`. A harmless copy of the existing generated wrapper replaced only its file
destinations and eval payload. A subshell executing literal `exit 7` produced actual
numeric exit 7, status failed and footer code 7. The wrapper process itself returned
0 after its idle sleep, so that process exit cannot substitute for the command receipt.
The raw check gives a conservative required-publication span of 0.353791744s and
records removal of its own scratch. It did not create another agent-task or touch
the prior B03 evidence or rejected scratch. New scientific models/episodes/steps: 0/0/0.

The independent reviewer identified one P2 issue. The candidate timeout covers the
child payload, beginning after supervisor startup; the supervisor writes its numeric
exit, status and footer after the child returns. Therefore the child may consume
120s while required work still lies outside that timer. The proposed start-time to
latest-publication-mtime measurement correctly detects an overrun, but does not
implement the complete stop boundary. The reviewer and CM found no omitted enclosing
deadline in the unmodified supervisor interface. DM confirms the actual supplied
command/postamble ordering and does not substitute the narrower timer for complete
conformance. This finding does not invalidate the successful status-propagation check.

No new watchdog, recursive wrapper, manual supervisor-receipt writing or supervisor
framework was added to make a launch possible. Scope section 4 still needs none;
source and test budgets have no observed breach. The remaining issue is the selected
execution constraint, not lack of positive headroom, exact scientific diagnosis,
additional validation exposure, a Pro round or a stronger evidence class.

## 3. Decisions this intake produces and exact return

**Object tier, technical acceptance.** Options (a) accept the conforming seed/object
and status-propagation evidence while keeping the complete-cap finding open;
(b) label the candidate fully launch-accepted from the harmless test; (c) discard
its independently trustworthy checks. Recommend and select (a).
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**

**Object tier, dependent execution.** Options (a) retain the selected 120s complete
boundary and return the precise missing enclosing-deadline route through Root;
(b) launch assuming the prior 3.50s timing guarantees compliance; (c) add unrequested
execution machinery or silently weaken the cap. Recommend and select (a). The
candidate/source records are committed and recoverable, with no scientific handle,
remote staging or run accepted. **Owner-delegated decision (unattended,
2026-09-03 instruction): (a).** No reviewer finding is overruled and owner flag is none.

Root's next action is to resolve the supported complete-wrapper deadline route or
commission the specifically scoped execution-boundary correction needed to retain
that complete cap. The existing CM should receive that concrete route/allowed
correction, finish focused acceptance and return the exact source/command before
the single launch. The unchanged seed/object comparison needs no redesign or extra
scientific invocation. DM retains the card and scientific intake; this return does
not ask Root to decide scientific polarity or change Portfolio state.

Fresh owner reviews returned `[]`; the existing P2 new-card item remains the actual
card freeze, not code acceptance or a fabricated owner approval. The corresponding
audit rows identify `2026-09-08T22:32:53Z`. The seed-6 prediction remains unscored,
owner prediction not taken. No new valid B result or all-outcome scientific intake
exists yet. P64's allocation, prior seed-5 negative result/null exit, discovery
seed 4, recasts 1, old family pauses and absence of UAV entry are unchanged.

## 4. P65 supplies the bounded correction

Root returned the committed [P65 handoff](../../portfolio/handoffs/2026-09-08-p65-vsp03-complete-deadline-correction.md)
at `5ded954073bcada7e60e06d62ab80009dd3aca01`. It expressly permits one small
B04-specific wrapper/adapter and task-local deadline enforcement covering required
startup/admission, all work, descendant termination and attributable terminal publication.
It does not permit a global supervisor/framework change, forged records, a second clock,
grace beyond 120s, or another scientific invocation. CM chooses from actual installed
source and OS tools; no unobserved capability or completed acceptance is presumed.

**Object-tier decision:** options (a) apply this exact engineering scope in card
section 8 and resume the same CM for focused correction/review; (b) retain the old
unsupported payload-only boundary; (c) alter science, cap or global framework.
Recommend and select (a). **Owner-delegated decision (unattended, 2026-09-03
instruction): (a).** This is the newly supplied technical route, not an overruling
of the prior finding or a new Pro/Portfolio scientific decision. The P64 finding
stays open until the actual implementation and independent shortened fixtures close it.

Fresh main owner reviews returned `[]`; no owner takeover or VSP03 override was found.
The shared checkout merged committed P65 inputs at `b6ad47e95`, starting clean. The
only audit merge conflict was resolved with exact main bytes after verifying all
prior nonblank direction records were present. P64's one seed-6 allocation remains
unstarted and its prediction unscored. Existing new-card item 003 points to the
updated card; the ordinary technical decision is in the audit, without another item.

## 5. P65 source acceptance and sole-invocation continuation

The DM accepts source **`b5d605bf4f39b5ab18f01c98e04dc07e53764354`**, with complete
independent review, check evidence and technical/launch records committed at
**`c2c092894e0523b88822fb597f481dc810071c24`**. The DM read the changed launch,
controller and deadline paths, the actual exit-precedence correction, the final
review/technical record and the raw check JSON's manager, terminal, PID and cgroup
facts. The existing seed/object/scientific checks are reused. No CM command or
scientific function was rerun during this intake.

P65's controlling requirement is applied verbatim:

> Start the
> one clock before required startup/admission and reserve any shutdown/publication
> time inside it. Cover descendants and failure paths; do not restart the clock,
> grant grace beyond 120s, forge existing supervisor records, or infer success from
> an outer wrapper's zero exit.

The first P65 candidate c436e7bab still armed its timer after required startup;
both DM and reviewer identified that gap. The final path uses the already-running
user systemd manager's transient oneshot startup timer before ExecStart. Its
pre-start monotonic origin reaches the controller, unchanged agent-task, private
tmux, adjacent admission and learner. Work stops at origin+110s, cleanup is reserved
through origin+118s, and the manager sends a cgroup SIGKILL at origin+119s, inside
the unchanged 120s cap. The private server prevents unrelated default-server work
from escaping or entering this task's cgroup. Final publication follows the
payload/supervisor receipt and control-descendant cleanup.

The reviewer-found missing command environment was repaired in 2e02bce40. DM's
subsequent actual-exit finding was repaired in b5d605bf4: a later nonzero supervisor
exit overrides an earlier differing payload receipt; a contradictory actual zero
becomes task125. Both original observations remain. The installed supervisor and
its records are unchanged, and its raw files remain separate from the adapter's
authoritative terminal and the manager's actual code/status/result.

The five independent revised-path checks used cap10s/reserve4s. Normal nonzero
execution published7 in0.395306s; forced work timeout published124 in6.043307s;
pre-controller startup stall was killed in9.024161s; a stopped controller and its
cgroup were killed in9.125985s; an earlier payload0 followed by actual shell7
published task7 in0.305349s. The last check is a literal interface stub; the normal,
work-timeout and stopped-controller cases used the installed supervisor copied
with only its task-directory destination changed. Every recorded/sampled PID was
absent and every sampled cgroup empty before test cleanup. The two hard-kill cases
correctly have no final task receipt. All five passed in25.511261s; combined with
the retained earlier downstream harness, P65 fixture wall is34.996686s. All new
fixture scratch was removed; the older rejected B03 cleanup remains untouched.
New scientific model/episode/update exposure is **0/0/0**.

The raw check records manager ExecMainStatus7,124 or9 while the systemd-run client
returned1. Therefore that client code is not a task exit. The concrete
[launch/observation binding](VSP03_B04_LAUNCH_BOUNDARY_20260908.md) specifies the
private TMUX_TMPDIR, unit journal and authoritative terminal paths. A successful
unit may unload; absence of later unit properties alone is not failure. Actual
run publication, complete-span/termination and resources remain to be observed.
The fixtures do not establish performance, scientific runtime, or immunity to
arbitrary kernel scheduling delay.

Scope section4's one task-local deadline/termination adapter is explicitly named
by card section8 for complete wall<=120s. The final adapter has270 source lines;
including the earlier seed/object plumbing gives300 additions, below2000. The
scientific runner remains28 lines, below600. No source, runner or test budget
breach is observed. No global supervisor/configuration edit, installed service,
standing framework, pool, recovery or retry was added. High orchestration share
serves this named correction and is not a separate acceptance gate.

**Decisions this intake produces — object tier, technical.** Options (a) accept
the resolved source/boundary and continue P64's already-selected single invocation
after Root integration; (b) return a concrete remaining source/coverage conflict;
(c) add scientific validation or another allocation. Recommend and select (a):
the review has no material finding and the targeted raw evidence matches P65.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** No dissent
is overruled; owner flag none. Main's fresh owner review query returned `[]` at
2026-09-08T23:35:36Z, with no VSP03 override. The existing new-card item003 remains
the card record; this ordinary technical decision adds an audit row, not a new item.

Root integrates the needed implementation chain c436e7bab,28164ecb4,2e02bce40,
b5d605bf4 and evidence c2c092894, plus this intake/command binding. These retain
the rejected intermediate source as provenance; only the final b5d605bf4 surface
is accepted for the scientific launch. The earlier input-sync b6ad47e95 is not an
integration deliverable. Root's latest explicit continuation assigns the single
launch to Root after this accepted binding/integration. Root executes the exact-SHA
detached wsl_4070 command, including fresh adjacent admission, through the configured
agent-task route. The same CM has been told not to launch separately and retains
collection/technical acceptance of Root's actual unit/handle; DM takes every outcome
in. No timeout retry, extra seed or scientific probe follows.

The original seed6/G1/Torch40006 learner,128 updates,20480 joint episodes,1638400
target transitions, four final modes and five contrasts remain unchanged. B04's
primary/prediction is unobserved and unscored. Seed5's negative result/null exit,
separate discovery seed4, old family pauses, recasts1 and lack of UAV entry remain.
The next scientific discriminator is the already-selected seed6 outcome; P64 ends
at its all-outcome intake and creates no automatic successor.

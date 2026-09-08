# VSP03 B04 P64 — candidate source and unresolved complete-cap boundary

**The seed/object and exit-status corrections conform, but the candidate is not
accepted for scientific launch.** The complete 120s stop boundary is not enforced
through the existing supervisor's required postamble. P64's one scientific instance
remains entirely unstarted; this is an execution-contract gap, not a result about G.

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

# CRTO B08 finite-zero movement repair intake — 2026-09-09

**Status: technically accepted by the original CM and DM; bounded repair complete.** Root explicitly resumed this
bounded zero-scientific-exposure correction from the foundations special Pro review §2.10.
The selected-panel balanced-residual family stays PARK. No experiment, scientific retry/resume,
new seed, endpoint, budget, MEI, successor family or Pro Send is authorized by this assignment.

Recorded 2026-09-09T19:28:38.281475+00:00. Designated checkout `C:/Projects/HMASD-worktrees/codex-crto`, branch `codex/crto`,
began clean at `531263fdcb49e32246d782fee67d7c5470c60b87`. Required committed owner configuration,
scientific-reading references/current spec and special-review response were copied exactly from
main `88a540f9273649086c8e84fffb14cb9d784f3afe` into the direction checkout at **31cf38b790eef1e901d0e67901e36f19a4a11444** and pushed.
This satisfies the pending clean-input sync recorded in the restart handoff; no main/index was
edited, no accepted Pro binding changed and no model/runtime hot reload is claimed. The synced
empirical note retains its pre-existing final blank line; the whitespace warning describes the
input as published, not an authored content change. All sixteen synchronized surfaces match main.

## 1. Finding, card and necessity

Root's special-review source is
`docs/research/portfolio/pro_packets/20260909_foundations_special_review/archive/RESPONSE.md`,
original immutable commit `e865e7b25beb16a7348070181161f18706fced4e`, integrated identically on main
at `88a540f9273649086c8e84fffb14cb9d784f3afe`. Section 2.10, the paragraph beginning “有一个具体但未触发的实现风险应回原 CM”, identifies
B08 `native_cost_b08/experiment.py::train_path`'s final-update rejection of any movement value
`<= 0.0`. Its explicit bound is that this did not trigger in the actual positive-movement B08,
and the review executed no reproducer, code repair or new experiment. Root accepted the full
special review and assigned this scoped finding; this DM is not re-intaking all other directions.

The DM read that finding and the current B08 card §§6–7 before the implementation and relevant
current evidence-spec §§11.4, 11.8.5–7 and 11.10. The frozen card's §6 instruction, verbatim:

> Emit each arm/endpoint's actual updates, examples, lr and nominal exposure, initial L2/RMS/Linf,
> displacement L2/initial-L2 and Linf/initial-Linf using the existing exposure implementation.

Section 7 limits launch conditions to §11.4 and preserves actual nonzero learner counts. It does
not require positive endpoint displacement. The helper `_movement` computes norms of the net
parameter difference from initialization, divided by initialization scales. That is an endpoint
displacement, not cumulative update distance, a count of optimizer calls, gradient connectivity,
learning success or native gain. A finite zero therefore cannot alone classify training as absent
or the primary native measurement as broken. The reported source condition is present at the
accepted original runtime source `d9f643b761d57584de313b1f837d6c2c0becc931`.

Scientific-reading use: `FOUNDATIONS.md` §§4 and 6 and `topic-notes/04_EMPIRICAL.md`, “先分清在比较什么”,
“随机性有层级” and “完整方法比较与机制归因”, separate the algorithm's update process, a resulting
policy instance and its native evaluation. Applied here, actual zero displacement is recorded as
one implementation observation rather than converted to “no optimizer execution”. The limits are
explicit: neither zero nor positive displacement establishes meaningful native learning, complete
competence or mechanism value. This conceptual mapping changes only the necessity assessment of
the rejection; card, reward, optimizer, information, seed and native measurement remain fixed.
No external paper claim or new literature retrieval is needed for this implementation fact.

The strongest reason to retain a check is real broken training: a disconnected loss can fail to
reach any model parameter. The present source directly calls backward/Adam and checks nonfinite
loss, existing gradients, parameters and movement. Simply accepting zero must not remove the
ability to detect disconnected gradients or nonfinite/broken primary data. The CM must inspect
that dependency and use direct training evidence for a missing-graph failure if the old movement
condition was its only proxy; finite zero gradient tensors remain legitimate values. Do not add
per-parameter positive-gradient thresholds, telemetry or a generic validation framework.

## 2. Bounded technical assignment and acceptance

The original CM `/root/dm_crto_p68_reentry/cm_crto_native_cost_b08` owns implementation, focused
synthetic regression, independent semantic review as required, and the complete technical return.
It has exclusive direction index ownership through its returned commit. DM reserves this intake,
the audit/brief and restart-status annotation; no overlapping edits occur during the CM batch.
All participants preserve other writers and the existing checkout.

Owned runtime/test paths:
`experiments/candidates/commitment_residual_triggered_options/native_cost_b08/experiment.py`
and `tests/experiments/candidates/commitment_residual_triggered_options/native_cost_b08/test_native_cost.py`.
The CM's focused result evidence belongs in
`CRTO_B08_ZERO_MOVEMENT_REPAIR_RESULT_EVIDENCE_20260909.md` in this direction directory.
Older B04/B06/B07/A01 helpers are reference dependencies, not repair targets.

Required acceptance: map the final change to the card's exposure clause and the actual dependency;
finite zero net movement must be honestly emitted when the real update path is intact; preserve
nonfinite loss/gradient/parameter/movement checks, disconnected-gradient detection and unchanged
primary scoring/rules. Verify changed behavior with a meaningful bounded synthetic fixture, plus
failure-path checks needed by that dependency. Retain every original B08 result/card/Pro packet
and the exact P71 source binding; no historical result is regenerated or reclassified.
Independent review is required for the changed scientific training-validity interpretation,
without a new reviewer/verification chain beyond what that bounded risk needs. The CM may reuse
its available original reviewer. No result-bearing runner, native evaluator, host generation,
profiling or production seed package is allowed as a regression test.

Budget: only this source correction, meaningful focused fixtures and scoped review; at most 300
seconds total focused research-directory test wall. Synthetic fixture optimizer calls are test
work, reported separately from zero scientific exposure. Existing code/runner caps remain. Use
`tests/AGENTS.md` invocation-owned `temp/` scratch and creator cleanup. No ENGINEERING_SCOPE_SPEC
§4 machinery is needed. Short synthetic checks stay local; no portable scientific run or remote
scientific staging is allocated. Stop at technically accepted source or a concrete unresolvable
scope/semantic/runtime blocker, then return to DM. No automatic scientific successor follows.

## 3. Decisions this intake produces (allocation boundary)

Options: (a) repair only unjustified finite-zero rejection with preserved direct training integrity;
(b) retain the proxy as a universal positive-displacement condition; (c) re-run or reopen the
scientific family. Recommendation and selected option: **(a)**. The direct card/code mapping
supports the correction, while (b) demands an unrequired outcome and (c) exceeds this assignment.

Owner-delegated decision (unattended, 2026-09-03 instruction): (a), under Root's explicit bounded
follow-up. This is an object-tier technical correction informed by the Pro finding, not a family
recast or new direction decision. No owner-console override or prediction reply was present in
main or this checkout at intake. Owner prediction: not taken; no new scientific prediction/run
is selected. Ordinary technical work creates no new P1/P2 card or direction item.

All original empirical claims remain exactly as accepted: B08 weak-new-RAW diagnostics, zero
matched controls, all historical gains/losses and the fixed-reference original-MEI ceiling. The
actual B08 movements were positive; the flagged branch never affected the completed run. The
family PARK and the general no-successor boundary remain while this explicitly assigned repair
is completed. The final technical acceptance and restart annotation are recorded below.


## 4. Final DM technical acceptance and limits

Accepted 2026-09-09T19:36:34.421303+00:00. The original CM returned source/test/result-evidence commit
**`9cd01f8191b1139c59b42ec22f1048e902fed57a`**, already pushed, with a clean checkout and released
index. The DM inspected the exact three-path diff against the assigned `ced81c37f...` revision,
the complete [technical evidence](CRTO_B08_ZERO_MOVEMENT_REPAIR_RESULT_EVIDENCE_20260909.md),
and the meaningful stationary and failure fixtures. No source, test or scientific command was
rerun during this intake. Read-only checks confirmed the test scratch directory is absent, the
focused diff has no whitespace errors, and the frozen card, P71 result/intake, DIRECTION and
runner have no changes in the repair commit. Required input sync is separate from authored repair.

The final runtime change is four added / three deleted lines. The final positivity rejection is
removed, while nonfinite movement still fails at every recorded endpoint. Immediately after
`zero_grad(set_to_none=True)` and backward, an all-model-parameter-`grad is None` condition now
rejects a disconnected update before clipping/Adam. A detached loss still fails through backward.
Finite present zero gradients are allowed; the same computed zero displacement is emitted without
substitution, clipping or a positive surrogate. Nonfinite loss, present gradients and post-step
parameters still use the original checks. The objective, optimizer arguments, update order,
snapshots, displacement normalization, exposure fields and primary scores/rules are unchanged.

This is necessary for the card/spec mapping in §1: a norm of final-minus-initial parameters is
not an optimizer-call or connectivity test. The direct all-None check preserves the relevant
protection lost by removing the proxy. It does not impose all-parameters-connected or nonzero
per-parameter-gradient requirements. It is a concrete training-integrity check, not new §4
infrastructure, a new exposure gate or evidence that a connected update is useful learning.

| Acceptance fact | Observation and bound |
| --- | --- |
| Connected finite-zero case | Equal legal costs on a tiny eight-parameter synthetic module; actual B08 loss/backward/clipping and two original Adam.step calls; both gradients present and zero, both endpoint movement ratios zero, update/example counts and snapshots emitted |
| Genuine failures retained | Six injections: nonfinite loss, gradient, parameter and movement; unrelated differentiable leaf reaching no model parameter; detached loss |
| Focused checks | 8 passed / 13 deselected; pytest reports 5.41 seconds, complete command process 7.016 seconds, within the 300-second allocation |
| Synthetic optimizer work | Four Adam calls total across the connected stationary case and two post-step faults; test work only, zero scientific optimizer exposure |
| Independent semantic review | Original reviewer `rev_ah_crto_b08`, no material finding; source/dependency/fixture inspection, no duplicate test execution |
| Scope | Runtime module + initializer + runner 360 lines, runner 43; runtime net +1, tests +90; no §4 machinery or §5 breach |
| Scratch | Named invocation `temp/directions/commitment_residual_triggered_options/test/b08-zero-movement-20260909-a` absent; no retained pytest scratch or deleted scientific evidence |

The existing source-body preservation check was adjusted only to normalize the explicit new
all-missing-gradient check and its already-known B08 differences. The new stationary fixture
executes the real loss/optimizer/movement/exposure path with substituted tiny constructor,
collation and RNG; it would fail the old final-zero condition. Thus acceptance rests on meaningful
behavior plus dependency inspection, not merely a textual mirror or reviewer completion label.
Primary native code is unchanged, so no full historical suite or native evaluation was needed.

The CM's independent reviewer concluded that all-None after zeroing/backward is a direct broken-graph
condition, whereas present finite-zero gradients can be intact. The DM accepts that narrow
assessment. The limitation remains: these checks do not certify arbitrary partial missing
gradients, convergence, useful optimization, or native value under all inputs. No broader training
or telemetry rewrite is included.

Historical classification stays unchanged. The DM separately read the accepted P71 analysis at
`601d9d8f0612461f4c04ef5f855a9ddd2aed9cee`: all twelve recorded movement numbers (L2 and Linf for
three arms at two endpoints) are positive. For example, LONG L2 ratios remain RAW
.21999455794994616, TRUE .21182928158673486, DERANGED .22742086472745415. Therefore the repaired
branch was untriggered in that run. Original source `d9f643b761d57584de313b1f837d6c2c0becc931`,
result bytes, weak-new-RAW diagnostic reading, zero matched contrasts, historical gains/losses,
fixed-baseline bound and original MEI retain their accepted meanings. This source revision is
not a new B08 execution, retrospective rescue or family re-entry.

## 5. Final decisions this intake produces and next boundary

Options: (a) accept the bounded correction and finish this technical batch; (b) return a specific
remaining training-integrity or scope gap. Recommendation and executed choice: **(a)**, because
the exact implementation, connected-zero fixture, preserved failure cases and independent review
support the required behavior; no unresolved material gap was found.

Owner-delegated decision (unattended, 2026-09-03 instruction): (a), under Root's explicit
foundations follow-up. This is object-tier technical acceptance, not a new scientific result,
direction disposition or specification change. Main and direction owner-console reviews were
empty at the final read boundary; no owner reply was invented. Owner prediction remains not taken.
No separate P1/P2 item is added for this ordinary technical correction. The
[Chinese brief](../../portfolio/owner/briefs/commitment_residual_triggered_options/2026-09-09_B08-zero-movement.md)
labels it as engineering work and preserves the empirical ceiling.

This batch adds zero result-bearing invocations, environment/native/evaluator calls, production
model or seed-package construction and scientific optimizer updates. Four synthetic Adam calls
are accounted separately above. No admission, remote staging, profiling, scientific retry/resume,
new seed/arm/endpoint/budget or Pro Send occurred. All work authorized by this repair is complete;
no successor is selected or allocated. The selected-panel balanced-residual family remains PARK.
There is no new live external work requiring observation.

Root's next action is to accept/integrate the allocation, source and final annotation commits,
checking what is already integrated. `31cf38b790eef1e901d0e67901e36f19a4a11444` contains exact
main `88a540f92` input surfaces and is not a new control-plane policy to apply on main. The
[restart record](CRTO_RESTART_HANDOFF_20260909.md) now records that the bounded repair and pending
input sync are complete, while no next scientific object has been chosen. Future direction work
needs its actual assignment; this source correction does not lift the scientific family boundary.

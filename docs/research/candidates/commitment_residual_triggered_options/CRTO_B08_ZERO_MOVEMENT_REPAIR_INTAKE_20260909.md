# CRTO B08 finite-zero movement repair intake — 2026-09-09

**Status: original CM technical batch allocated, result pending.** Root explicitly resumed this
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
is completed. Final acceptance and restart annotation will be appended on CM return.

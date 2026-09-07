# Service-allocation decision — proposed completion amendment

**Question:** should the formed 2026-09-07 service-allocation decision be amended to allow
one narrowly bounded rule-only completion, or should the incomplete assignment remain as it is?
This is a proposal for the same Convergence node, not an executed amendment or a new host,
mechanism, comparator, seed, training run or winner-selection rule.

The evidence class remains the existing bounded B/EXPLORE comparison. Its added component
would be a finite fixed-policy measurement using two already-completed real learners; it
creates no new independent training instance and supports no C or population conclusion.

## Evidence and decision value

The [frozen card](../../VSPC1_K4_SERVICE_ALLOCATION_B01_SCIENCE_CARD_20260907.md),
[CM E0 return](../../VSPC1_K4_SERVICE_ALLOCATION_B01_EXECUTION_20260907.md) and
[DM scientific intake](../../VSPC1_K4_SERVICE_ALLOCATION_B01_INTAKE_20260907.md) preserve
two real seed402 learners, 256 updates each and all five fixed evaluations. FACTOR final
J=0.7589111328125, GENERIC=0.7524007161458333, Delta=+0.006510416667, conditional evaluation
SE=0.002109066044. Period differences are +0.001708984375 and +0.011311848958. The gain is
below MEI 0.025; full-grid AUC difference +0.001363118490 and both initial-to-final changes
remain secondary and retained. There is one paired training instance, not 256 replicates.

GENERIC failed at publication after its complete learner summary was written, before rule
evaluation. The source compared a loaded checkpoint list against an in-memory tuple;
both saved JSON budgets are identical. The existing synthetic fixture omitted the checkpoint
field and normalized both inputs, missing that boundary. The complete assignment remains
incomplete; no rule result, rule-relative value or prediction score exists.

This request is **outcome-informed**: these learner results and the failure are known before
requesting the extra call. The missing reference was selected prospectively, but placing it
in a later invocation was not. A completion cannot turn the below-MEI Delta into the declared
FACTOR-over-GENERIC promotion signal, erase the failed invocation, or count as a new independent
confirmation. It would only determine whether either already-trained policy improves on the
already-selected same-information rule, using the fixed endpoints and all the original tapes.

DM recommends option A because learner usefulness relative to the rule was the original
unanswered discriminator. The strongest alternative is option B: this small below-MEI
representation difference may not merit any further engineering or measurement. Sunk effort,
zero learner updates and a small tick count alone do not establish completion's value.
There is no tuned new-host headroom record; no exact upper, search or extra cost experiment
is proposed as a prerequisite.

## Exact existing clauses affected

The original [formed response](../20260907_service_allocation_convergence/archive/RESPONSE.md),
archived at `5d3027ebe` from immutable Pro delivery
`2347dbf2fea870cdcd02aa2eb8b3cbaff147ec34`, is preserved unchanged. Its section 五,
“完整工作与停止边界”, contains these exact clauses:

> 固定策略评价与配对发布放在第二个完整调用内。

> 不能借用另一臂余额、切片重置上限、开第三调用或自动重试。

Its section 六, “各结果改变的选择与工作预测”, explicitly says:

> 若只是参照缺失而两学习臂可比，保留 Δ，仅将相对规则的价值列为未确认；不自动补第三调用。

The same placement and limit appear in card §5 (“inside the second complete invocation”;
“no automatic third call”), §6 (“Two arms”, FACTOR then GENERIC, reference/publication within
the second call, no borrowing/third call/automatic retry), and §7 (second call publishes the
reference and all three contrasts). The proposed additional invocation conflicts with that
explicit selected boundary even though its reward, policies, information and tapes are fixed.
The previous unused caps and evidence-spec §11.8.7 do not authorize it. A formed scoped
amendment is therefore requested; no general repository/specification exception is requested.

## Option A — proposed exact limited amendment

Permit **one additional complete rule-only invocation, cap 120 seconds**, after the focused
publication repair is technically accepted and a later Root execution command binds the
new committed source and data paths. This is a new invocation at a new repair SHA, not a
retry of either learner call or use of their unused 2,700-second budgets. It completes only
the previously missing reference/publication dependency; the original failed GENERIC
invocation and outcome-informed timing remain visible in every intake.

The added invocation reads both untouched saved learner summaries, evaluates the existing
LQ-EXCLUDE rule **once** on 128 episodes at each of periods 2 and 6, and publishes all three
paired comparisons using their existing indexed learner endpoints. No learner construction,
optimizer, retraining, learner reevaluation, extra checkpoint, seed, host, comparator, tuning,
best-point selection or rollout beyond those 256 reference episodes is permitted.

Use the original `tapes(seed=402, period=d, episodes=128, update=0, evaluation=True)` contract:
PCG64 SeedSequence namespaces 31/32, NumPy 1.26.3, original call order and array shapes. The
original helper already regenerates these fixed exogenous tapes for the rule; it does not
reuse learner queue/action traces. Each rule episode starts its own queues/hold and follows
its own endogenous trajectory under the unchanged host/partner/hold/reward rules. No change
to `experiment.py`, its tape generator, `collect`, `lq_exclude` or `evaluate_rule` is proposed.

Keep `wsl_4070`, the configured Python, CPU float32 tensors, one compute thread and the
original rule evaluation batch of 128 episodes per period. Training batch16 remains unchanged
and unused. The new thin completion entry point must set the existing thread limits without
calling `run()` or constructing a QNetwork/optimizer. Raw learner artifacts and original
output roots remain read-only; rule and combined outputs go to a separate completion root.

The 120-second cap covers startup/import, immediately adjacent same-node memory admission,
input reads, fixed tape regeneration, all rule steps, comparison/readback, metadata and exit.
Existing detached `agent-task` supervision and fresh physical/effective memory >=4 GiB apply.
Preserve partial counts on any failure. Stop after the one call or its concrete failure/cap;
no automatic repair call, resampling or fourth invocation. No reserve is borrowed from earlier
calls. Optional resource gaps retain `resources_unmeasured`; damaged primary dependencies
remain bounded under evidence-spec §11.8.7.

If adopted, these terms are an explicit exception only to the original reference's placement
inside GENERIC and its prohibition on an additional call for this completion. Every other
card scientific clause, MEI, endpoint, period weighting, SE/AUC definition, prediction and
family boundary remains. Publish the amendment beside the original card/decision; never
rewrite the old verdict, traceback or attempt status into a prospective successful run.

## Option B — retain the current incomplete assignment

Authorize no extra invocation and leave the valid learner-only observation as recorded.
The rule-relative values and prediction stay unresolved, without a negative reference result
or an optimality/equivalence claim. This does not close K4, recast a family, or change Portfolio
priority. No source or fixture repair is commissioned by this request if B is selected.

## Work and implementation boundary

The [machine count record](COMPLETION_COUNTS.json) separates past actual exposure, zero new
preparation exposure, proposed rule work and proposed synthetic validation. Added algorithm
work is one policy × two periods × 128 episodes × 48 ticks = 12,288 joint ticks, with 4,096
renewal rule decisions and no model/Q/optimizer work or nested candidate search. The partner
acts at each tick; the rule also predicts its immediate choice at each renewal. Regeneration
uses the already-fixed evaluation draws, not a new independent evaluation sample.

The two previous complete-call walls were 6.52/4.84 seconds (11.36 total), CPU 8.58 seconds.
Rule-only full wall and incremental repair/review time have not been measured. 120 seconds
is the proposed complete-call budget, not a prediction or proof of feasibility; finite and
zero-learner work is not treated as free. No benchmark or cost probe is proposed.
The proposed cap leaves bounded room for admission/import and publication relative to the
observed short learner calls, while avoiding transfer of their much larger original caps.

Conditional engineering scope is in the [five-item CM handoff](CM_REPAIR_HANDOFF.md): targeted
budget-sequence normalization, one thin rule-only entry point, one focused synthetic mixed
representation fixture and independent review. Proposed non-test changed-line cap is 150
(A+D), with at most 100 lines in the new runner, within the existing overall limits. One
focused fixture invocation is capped at five minutes, with zero model/host/rule/RNG exposure.
Scope §4 needs **none**; no schema, guard framework, registry, retry/lease system or service.

Preparation creates no implementation, test, model, environment, rule or provider execution.
The answer should choose A or B, state the exact affected clauses and retained claim ceiling,
and identify a concrete conflict if either option cannot be decided within this node's scope.

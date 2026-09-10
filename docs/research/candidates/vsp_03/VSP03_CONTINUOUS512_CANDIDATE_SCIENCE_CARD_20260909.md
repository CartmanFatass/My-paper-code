Continuing ordinary G from update128 to a fixed update512 may change its sampled native utility relative to fixed readiness on the public shared-service task.
Binding structure: temporal abstraction / termination at fixed N=2; an eight-tick shared-slot submission changes the partner's feasible opportunities and remaining team return.

# VSP03 continuous512 candidate — three fresh fits, two fixed panels

**B/EXPLORE candidate; proposed, not selected, not frozen and not allocated.**
This prepares the owner's synthesis candidate for the existing Convergence node.
The tested update128 ordinary-G family stays paused until a conforming new
direction decision is taken. No source implementation or scientific/test/profiling
invocation is authorized by this document. Recasts currently remain **1**.

## 1. Question and the stopped scope

Does extending the same real training process from128 to512 updates change the
native comparison enough to reconsider ordinary greedy G's usefulness against
R0 and R? The primary is **fixed update512 greedy G minus R0**, with three fresh
training fits and an explanatory within-fit128→512 comparison. This tests a
different training budget; it does not rerun three standalone128 fits or select
a good checkpoint from a grid.

Root's OWNER_DIRECT synthesis assignment, from owner task
`01a087ed-f4c5-71e3-9f72-965da3508dc3`, authorizes this preparation and read-only
source/cost feasibility. It names three fresh continuous512 G fits, fixed128/512
four-mode panels, original .02 MEI and no2048/grid/best-checkpoint allocation.
The [synthesis §§4 VSP03,5.3 VSP03,6](https://github.com/CartmanFatass/My-paper-code/blob/dae6a74bbf8e402a3ea47256176f5795eb277206/docs/research/portfolio/pro_packets/20260909_third_party_planning_comparison/RESEARCH_PLAN_SYNTHESIS_CODEX_20260909.md)
was non-executing advice; the current assignment makes only this preparation
actionable. Actual implementation/execution remains for a later concrete command.

The [post-B05 full decision](pro_packets/20260909_post_b05_convergence/archive/RESPONSE.md)
at `3da3a0c44ff7296c19e85342a56ee3128dce1451`, applied in
[its intake](VSP03_POST_B05_CONVERGENCE_INTAKE_20260909.md), pauses the exact tested
ordinary-G/update128/public fixed-N2 greedy-replacement combination. Its §IV
expressly selects no changed update count. A new longer-budget question is not
that decision's authorization. DM therefore asks the same Convergence node to
select this bounded budget comparison or retain the pause without a successor;
no local family reopening is made. This is a scope decision, not a general Pro
prerequisite for B. No new mechanism, host, information structure or initialization
intervention is proposed; DM recommends preserving recasts=1, subject to the
node's actual classification.

## 2. Preserved environment, learner and native consequence

The [P76 card §§2–3](VSP03_B05_P76_SCIENCE_CARD_20260909.md) and accepted source
`32ce8a7355b86bee64956e3d24b76d01c31a8d77` define the reused semantics. There are
two fixed controller/job identities, each owning one job, with public offset
opportunity clocks. Both targets evolve all40 primitive transitions. Occupied
targets leave with probability1/(d+4), absent targets return with probability1/2.
An accepted SUBMIT occupies the sole slot for all eight transitions even on
failure; release/completion precedes the next decision. Forced waits have no
gradient row. Target absence/return is not entity or roster churn.

Both agents see the same14 public own/partner event, readiness and clock features;
actor and critic receive no future tape or hidden success information. Both
controllers co-adapt the one shared G during learning and freeze it for each
panel. A valid action is credited with actual remaining team return through t40,
subtracting already accrued reward: gamma1, zero terminal bootstrap. Utility is
the two jobs' `200*success -10*attempt -waiting_ticks` sum divided by400.
Thus a submission changes slot access, partner opportunities and native outcomes;
neither fewer waits nor a moving parameter vector alone demonstrates useful
coordination. The fully public centralized scheduling interpretation survives.

Keep the generic **2,083-parameter** model (actor/direct1,570; critic513), current
initialization, Adam lr0.001/betas(0.9,0.999)/eps1e-8, unchanged actor/critic loss
and no clipping, normalization, replay, extra epochs or online adaptation.
There is one backward and Adam step per128-episode batch. The original entropy
coefficient is **0.01*max(0,(64-update)/63)**: zero from64 through512. Extending
training must not stretch or restart that schedule. The stochastic training
objective need not improve greedy execution.

The only learning-budget change is **128→512 continuous updates**. Keep one model
and one Adam instance from update1 through512; after the128 panel resume at129
without reseeding, reinitializing, reloading or resetting optimizer state. The
current b03 driver is fixed at128 and needs a new thin driver if selected;
calling it twice or changing the old frozen runner does not implement this card.

R0 still submits on an actual legal opportunity when own b=1. R adds only the
existing yield to a pending, currently ready, strictly older partner with a
future opportunity, submitting on age ties. Neither is tuned or weakened.
Greedy G submits iff **logit>0**, continuing on ties. R0/R are reused because
their action/information/utility/world distribution match. They are useful legal
controls, not learned policies with a training-budget requirement or tuned uppers.

## 3. Fresh fits, private randomness and fixed panels

Proposed fit keys are **10801/10802/10803**, with Torch initialization
**50801/50802/50803** and G arm1. No old weights, optimizer, worlds or RNG state
load. A bounded search of the direction's source/cards/requests found no prior
use of these keys; independence comes from the declared generation design, not
the labels or that search alone.

Reuse the address law: world target tapes
`[302,fit,split,episode,target]`, phase `[302,fit,split,episode,2]`; PCG64 with
SeedSequence,40 uniforms per target. Training split100 has episodes0…65535;
batch update u begins at `(u-1)*128`. Evaluation split200 has worlds0…1023.
The three fit keys separate initialization, training and evaluation generations.

Action tapes remain `[303,fit,split,mode,1,episode]`,17 calendar-position uniforms.
Training mode0/split100 and stochastic evaluation mode1/split200 are disjoint.
Within each fit, use the **same1,024 evaluation worlds/phase and stochastic
evaluation tapes at both128 and512**. That intentional common-randomness pairing
supports the within-fit curve contrast; it does not mix evaluation with learning.
Greedy and rules consume no action tape. No numeric RNG, master or world is
created by this preparation.

Immediately after completed Adam steps128 and512, execute **greedy G,
stochastic G, R0 and R once each**,1,024 worlds per mode. Evaluation uses fresh
environment arrays and no gradients and changes no parameter, optimizer, training
RNG or update index. The current MLP has no dropout, batchnorm or recurrent state.
Both deterministic rule panels are executed and counted at each endpoint as
requested, even though identical worlds imply identical rule results. Neither
panel feeds checkpoint selection, tuning, early stopping or future training.

Retain checkpoint-keyed native rows and all four means/five original contrasts;
each success/attempt/waiting component;512 training-curve rows per fit; actual
decision/gradient/forward counts; initial, first-step,128 and512 displacement;
and only the two selected128/512 weight snapshots. Serialize detached snapshot
bytes at the actual boundary, avoiding later-mutated state_dict references.
Do not construct another model or save resume/optimizer checkpoints to produce
these panels. Two selected snapshots do not request every intermediate weight.

## 4. Observable, reading rule and inferential limit

For each fit i, let **d512_i=mean_world(J(G512 greedy)−J(R0))**. Report the three
primary scores, their arithmetic mean and descriptive sample SD. For both panels
retain paired-world SD/SE for all original contrasts. Report explanatory
**q_i=d512_i−d128_i**, with common-world differences and their conditional
uncertainty; fixed R0 cancels algebraically but its actual panel is retained.
The G−R and three stochastic contrasts at both panels remain visible.

The independent training unit is **one fresh continuous fit**. There are three,
not six checkpoints,24 panels or thousands of independent trained policies.
Within-fit panel comparisons use intentional pairing; across-fit score variation
still includes finite evaluation noise. The three new fits form a newly specified
exploratory budget package after seeing old outcomes. Old seeds5/6/7 remain the
separate mixed128 record; seed4 remains outcome-informed discovery. No pooled
cross-budget mean or confirmatory relabeling is proposed.

**Prospective reading rule:** final512 greedy G above both R0 and R supports the
sampled longer-budget controller; an above-R0 but below-R point supports only the
R0 comparison. Positive mean q with corresponding native accounting supports
budget-sensitive improvement along these runs, even if512 still loses to rules;
a final gain with small/negative q supplies endpoint evidence without showing
that extending128 produced it. Flat or adverse q does not prove convergence,
policy-class limits or optimizer failure. Inside-MEI values keep their sign and
size. A zero/adverse final primary favors readiness for that sampled comparison.
Stochastic losses restrict a greedy gain to its declared mode. Retain every fit,
sign and failure; do not demand three improvements, change the primary or select
the best checkpoint after seeing outcomes.

This is native finite-budget performance exploration. It does not identify a
unique MARL mechanism, exact maximum, stable superiority/inferiority/equivalence,
initialization value, C promotion, UAV entry/transfer or deployment/safety.
A fixed two-panel curve cannot establish asymptotic convergence. No outcome
automatically authorizes2048, more fits, a diagnostic or a family disposition.
Any later direction decision follows intake under the existing ladder.

## 5. MEI, headroom, prediction and the next choice

MEI remains **0.02 absolute native utility**, equivalent to eight total waiting
ticks/400, for interpretable task scale without unstable relative ratios. It is
not an equivalence, validity, seed-quota or follow-up gate. Tuned N2 headroom is
**absent**, not zero; unchanged R0/R are not an upper reference.

Proposed low-confidence prediction on record: **abs(mean_i d512_i)<=0.02**.
No positive-sign or monotonic-improvement forecast is made. This prediction is
not yet frozen or scored because the candidate is unselected. Owner prediction:
not taken (unattended) unless a relevant reply later exists.

A beyond-MEI final gain over both rules, especially with positive within-fit
change, would strengthen the case for a specifically bounded follow-up. Small
or mixed margins retain their actual evidence; adverse finals favor readiness
for this budget package. DM would return whether any concrete unresolved
observation warrants investment, preserving all signs. None is an automatic
successor, ten-seed escalation or wholesale failure verdict.

The alternative is to retain the present narrow pause: two small128 gains and
one larger loss leave a competent fixed rule, and additional ordinary training
may still buy only small uncertain tradeoffs. DM recommends asking Convergence
to select this one bounded512 comparison because it directly separates continued
learning from another unchanged128 realization at low projected work. This is
not proof that128 undertrained, that512 will improve, or that all directions
need a generic learner census. Three fits are the owner's concrete candidate
size, not a repository seed requirement.

## 6. Exact work, cost and stop boundary

[Prospective counts](VSP03_CONTINUOUS512_PROSPECTIVE_COUNTS_20260909.json) and the
[original CM's source feasibility](VSP03_CONTINUOUS512_CM_FEASIBILITY_20260909.md)
derive the work without scientific execution:

| Work | One fit | Three fits |
| --- | ---: | ---: |
| Training episodes:512×128 | 65,536 | 196,608 |
| Training team ticks / target transitions | 2,621,440 /5,242,880 | 7,864,320 /15,728,640 |
| Backward calls and Adam steps | 512 each | 1,536 each |
| Evaluation episodes:2 panels×4 modes×1,024 | 8,192 | 24,576 |
| Evaluation team ticks / target transitions | 327,680 /655,360 | 983,040 /1,966,080 |
| Total episodes | 73,728 | 221,184 |
| **Total team ticks / target transitions** | **2,949,120 /5,898,240** | **8,847,360 /17,694,720** |
| Rollout model batch calls, upper | 8,772 | 26,316 |

The model-call bound excludes objective/critic/backward; R0/R make no model
calls. Actual eligible/gradient rows depend on behavior and must be reported,
not filled to a quota. No nested candidate, future-trajectory, solver or policy
search occurs. Added scientific validation models/episodes/updates/evaluations
are0/0/0/0. There are no15 fits, separate128 fits or2048 updates.

Cost law per fit: admission/import/startup + G initialization +512 C(128,40,2)
+2×4 E(1024,40,2) + selected snapshots/panels/readback/publication + actual exit
and descendant termination. P67/P76 complete wall3.253184/4.191728s and unit
CPU3.278770/3.500596s are retained observations. Fourfold complete-path projection
is **13.012736–16.766912s per fit**, **39.038208–50.300736s summed for three**.
Training scales4×, panels2×, total ticks3.6×; differing component work means this
is an extrapolation, not a measured or statistical upper. Future wall, movement,
return, resource use and unmeasured authoring/collection work remain unknown.

CM finds **60s complete invocation per fit** plausible. Proposed total cap is
**180s summed complete-fit invocation wall**, not end-to-end study elapsed and
not a new global deadline. Each fit's one clock begins at the earliest manager
start and covers admission, imports, initialization, learning, both panels,
required checks/publication, actual exit and descendants: work ends50s, cleanup58s,
hard kill59s within60s. Study elapsed and summed invocation wall are recorded
separately; staging/control-plane gaps are not invented as zero. No pilot or
profiling run is authorized to calibrate this projection.

If later selected and allocated, use three ordinary separately detached exact-SHA
invocations on **remote-first wsl_4070, CPU float32, one compute thread; float64
worlds**, with fresh same-node resource admission immediately before each fit.
Preflight must pass physical/effective available memory>=4GiB before scientific
construction. No empirical execution is pinned to local Windows. Per-fit process
isolation also preserves the existing Torch interop-thread setup.

The proposed allocation would allow **at most one accepted invocation per named
fit**, with all three planned irrespective of return sign. A completed/failed/
refused/timed-out fit is not replaced or retried; no resume, fallback, extra
evaluation, pilot or fourth fit follows. Preserve actual counts and128-only
partials; missing512 cannot be replaced by128, zero or a best checkpoint. A
concrete shared defect threatening reward/information/comparison/training/primary
pauses dependent launches for repair/allocation reconciliation; trustworthy
other evidence survives. No three-success condition is imposed.

The original CM would implement/launch/collect/accept; the current independent
monitor would adopt accepted handles under Root's current operations instructions;
DM would interpret every result. This preparation creates no handles, execution
roots, source binding, resource receipt or monitor dispatch.

## 7. Engineering scope and conceptual use

**ENGINEERING_SCOPE_SPEC §4 needed:** reuse the existing task-local deadline/
termination adapter for the quantity **complete per-fit wall<=60s including
publication and descendants**. No other §4 machinery is needed. The adapter
already accepts60/reserve10; only a future driver/binding must align its internal
clock and checkpoint-keyed outputs. Do not add distributed/resumable execution,
provenance guards, registries, telemetry services, worker pools, validation
frameworks or an overall study scheduler. Ordinary three-command sequencing is
not a new execution platform. Existing §5 source/runner/cumulative test budgets
remain; a new budget panel grants no new testing allowance.

Future affected acceptance concerns are continuous model/Adam/global-update state,
evaluation isolation, exact fixed panels and primary identity, private addresses,
snapshot bytes and the60s clock. Reuse accepted environment/reward/information/
rule/lifecycle checks. Concrete changed behavior deserves proportionate focused
checks and required independent review; none is executed or allocated now.

Current [FOUNDATIONS §§3–6](https://github.com/CartmanFatass/My-paper-code/blob/090da20372152c7ceecf6c54c70f3f0587439a08/docs/rl-marl-foundations-20260907/FOUNDATIONS.md)
and [empirical topic: comparison, randomness, evidence](https://github.com/CartmanFatass/My-paper-code/blob/090da20372152c7ceecf6c54c70f3f0587439a08/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md)
change the design in three concrete ways: a checkpoint is the same learning
process, so128/512 cannot double the fit population; fixed-endpoint and selected-
maximum evidence differ, so512 stays primary; representability and finite
learning differ, so a weak128 result cannot certify convergence or a policy
class limit. Shared team reward and public scheduling do not isolate a MARL
cause. These are explanatory limits, not authority or new launch conditions.

The current empirical spec §§4,5.2,11.4,11.7–11.10 governs the B claim. Prior
question-driven local-library checks recorded in
[P74 question intake §3](VSP03_P74_POST_B04_QUESTION_INTAKE_20260909.md#3-binding-mechanism-competent-alternative-and-source-use)
are reused for unchanged opportunity clocks, ongoing-action credit and ordinary
termination learning. There is no new mechanism/comparator or literary novelty
claim, no new library search or assertion of current full-corpus coverage.

## 8. Preparation boundary and next owner

Designated checkout is
`C:/Projects/HMASD-worktrees/dm-vsp03-p07-prep-20260907`, existing shared branch
`codex/pro-vsp03-shared-service-convergence-20260906`. Current source and accepted
science remain at47f8983ed's existing tree. Newer method and synthesis passages
are read on main and independently pinned; no governance or unrelated direction
file is imported or rewritten by this preparation.

DM owns this candidate, counts, preparation intake, owner item and fixed GitHub
request. The original CM delivered one read-only feasibility record; no source
writer was commissioned. Root receives the ready handoff and sends it once
through the configured Transport, then forwards the full immutable answer to
this DM. Only a conforming selection and the later scoped implementation/run
assignment can advance the candidate beyond this boundary. Old paused scopes,
failed attempts, all three mixed128 outcomes and Portfolio lifecycle remain.

# UAV cooperative planning — direction notebook

## 2026-09-27 — DM3 successor: anticipatory rematching and return-horizon choice (L0)

**State: exploring. No implementation, training fit, or native launch is accepted yet.** This is
the bounded follow-up after the complete B02 handover in
[`energy_relay_imitation/NOTES.md`](../energy_relay_imitation/NOTES.md). B02 was one-init BC
repair on shield-active decisions; it neither tested cooperative planning nor supports another
mask/DAgger/PPO branch. The inherited DM3 focus is whether learned selection of a cooperative
movement schedule can improve native service over a capable ordinary planner, without waiting
for a positive DM4 result. See the current [Root planning review](../../RESEARCH.md#uav-planning-review-20260927).

### Question and bounded claim

On S7-S2/H3000, can a pooled-legal-observation team selector that predicts native team return
over the next 300 seconds improve complete-episode QoS and raw native J over (a) the same
selector trained on only the next 10 seconds and (b) either fixed ordinary schedule? Both
candidate schedules use the same H_local planner and production safety controls. The only
schedule difference is whether H_local anticipates a return-shield departure by waiting and
rematching the remaining UAVs.

This tests one bounded cooperative schedule-selection question. It is not a general MARL
architecture claim, a causal claim about one UAV's credit, a trajectory learner, or a claim that
the selector learned user motion. The legal observation does not expose true user velocities or
stable user identities.

### Fixed candidate schedules

1. **H_local@10:** existing S7-S2 H_local with `information="local"`, six service targets,
   30 m/s horizontal movement and `replan_period=10`. It pools the eight legal observations and
   uses the same target planner at every 10-step replan.
2. **Anticipatory rematching@10:** the identical H_local controller plus the following
   direction-owned controller rule. At H_local's 10-step replans, use the legal return-margin
   suffix sampled at each 1-second decision. With at least 31 samples, estimate the current
   margin slope by the 30-second secant. For a positive margin and negative slope, estimate
   time to the production shield's zero-margin entry as `margin / -slope`; nonnegative slopes,
   insufficient history, nonpositive margin, or missing legal values give no forecast.

   A nominee must be in the last completed H_local plan's currently held **service-target**
   role (there is no eligible role before the reset-time plan), not already in the production
   shield, and legally available, noncharging, nonreturning, and without a dock
   request. Role is reconstructed from that UAV's assigned target coordinate in the actual
   H_local plan and its service-centroid/relay/search targets; ambiguous cross-kind coordinate
   ties are ineligible. `last_plan["kinds"]` is target order, not a per-UAV role map.
   At most one nominee is active: smallest forecast time first, then lowest UAV index. Nominate
   when the projected entry is within 60 seconds.

   For an active nominee, send an augmented planning-availability mask to the ordinary H_local
   matcher for reassignment (actual shield modes remain unchanged) and propose a zero action so
   it waits at its current position. Keep the nomination until actual production-shield entry
   or a 60-second timeout, whichever comes first. On timeout, replan normally and suppress that
   UAV from another nomination until its forecast is outside the 60-second window or its margin
   slope is nonnegative. A shielded, unavailable or charging UAV cannot be nominated. At a
   schedule boundary that switches away from anticipatory rematching, cancel its pending
   nomination but preserve timeout suppression and H_local target memory; when it remains
   selected, preserve the nomination and H_local target memory. H_local replans every 10 steps
   in both schedules. Do not mutate the real production shield's mode state or native
   guard/configuration: pass actual modes to feedback, then run the same production shield and
   backhaul guard on the controller proposal, including the intentional zero wait for the nominee.

The margin forecast is a lawful recent-trend heuristic, **not a battery clock**: return margin
also changes with position and nearest-station distance, and the intervention can change its
own future slope. Station changes remain in the observed margin history and may cause a bad
forecast. The experiment evaluates the complete native outcome, not forecast accuracy as a
substitute endpoint. Holding a UAV out of planning may leave its current role unused; ordinary
rematching can omit a target or be constrained by the native backhaul guard. Those are measured
tradeoffs, not assumed-away mechanics.

### Collection, fitting and evaluation contract

- **Domain:** S7-S2, eight UAVs/thirty users, H=3000 one-second transitions, native reward and
  metrics. All observations and controller features come from the eight legal 365-field
  observations plus documented controller memory. No raw `state`, simulator positions or
  velocities, hidden user identities, `plan_inputs`, synthetic labels, teacher labels, or
  counterfactual returns enter the predictors.
- **Collection:** 64 fresh worlds, seeds `970001–970064`, one H3000 episode each. Each episode
  has ten consecutive 300-step blocks. At each block boundary, uniformly shuffle five
  H_local and five anticipatory-rematching block labels using per-world
  `SeedSequence([970902, world_seed])`; hold the selected schedule for the full 300 steps.
  H_local replans every 10 steps. Preserve ordinary planner memory; carry active anticipation
  only across adjacent selected rematching blocks. Each block contributes its pre-action legal
  joint context, selected schedule, actual un-discounted native team reward sum over the next
  10 steps, and actual native team reward sum over the next 300 steps. Only the selected
  schedule's observed outcome is labelled; no counterfactual label is constructed. These are
  640 block records nested in 64 worlds, not 640 independent worlds.
- **Two offline fits:** one MLP for the 10-step return target and one for the 300-step target;
  same features, architecture (two ReLU hidden layers, widths 128 and 64), MSE objective,
  Adam learning rate `1e-3`, 50 passes over the same 640 records, minibatches of 64 (500
  updates/model maximum), normalization rule, initialization seed `970903`, and minibatch order.
  Standardize input dimensions and each model's target from the collection records only. No
  validation-based checkpoint selection, tuning, refit or extra seed. This is **one started fit
  per horizon / two started fits total**, so any learned result remains exploratory under
  constitution section 8; it cannot confirm an empirical learning claim.
- **Selector:** at each 300-step boundary, score both fixed schedules using the corresponding
  model and choose the higher predicted return; exact ties choose H_local. The selected schedule
  is held for the next 300 steps. The 10-step target model is thus a short-window selector at
  the same decision cadence as the 300-step target model, not a 10-step actuator.
- **Evaluation:** 32 fresh paired worlds, seeds `971001–971032`, each evaluated once under four
  arms: fixed H_local, fixed anticipatory rematching, 10-step-return selector and
  300-step-return selector. Same seed per world across arms; no evaluation seed is used for
  fitting or selection. Four arms × 32 episodes = 128 evaluation episodes.
- **Total:** 64 collection episodes + 128 evaluation episodes = 192 H3000 episodes / 576,000
  environment transitions; two fits, at most 1,000 optimizer updates in total. Planned native
  concurrency is two workers; prior H_local world timing implies roughly 105–145 minutes of
  episode execution, plus unmeasured collection, fitting, controller, output and current-node
  contention. This is an estimate only; a fresh configured-node admission and memory check is
  required immediately before launch. A technical failure, incomplete native window or failed
  world is preserved and reported; no automatic seed replacement, retry or fit continuation.

### Readout and decision

Primary episode outcomes are mean QoS satisfaction per actual step and raw native J (the
undiscounted sum of the actual team reward); report paired per-world differences and 95% paired
t intervals. Also report all zero-service worlds, return/charging cost, minimum-battery tail,
cutoff/depletion counts, guard-blocked actions, rematching nominations, forecast/actual shield
entry timing, timeout and schedule-selection frequencies. These latter traces explain behavior;
they do not replace native endpoints.

The candidate earns a **long-window exploratory signal** only if the 300-step selector exceeds
both fixed schedules and the 10-step selector by at least `0.03` mean QoS per step, has positive
mean paired raw-J difference to each, and its aggregate cutoff and depletion counts do not
exceed either fixed schedule. Otherwise record the adverse or inconclusive reading without
extending the batch. Even if this rule passes, one fit per horizon is not confirmation; any
replication is a new DM decision with its own prospective 3–5 fresh fit seeds per learned arm.
No automatic follow-up batch is authorized by this entry.

### Implementation boundary

The bounded implementation belongs only under
`experiments/candidates/uav_cooperative_planning/b01/`; compact records belong under
`runs/uav_cooperative_planning/<tag>/`; scratch belongs under `temp/directions/uav_cooperative_planning/`.
Read the nearest `AGENTS.md` before code edits. Reuse existing S7-S2 environment, H_local,
production feedback and metric interfaces by import where practical; do not edit shared
environment, learner, benchmark, other direction files or the RESEARCH routing block. The
entrypoint must preserve exact seeds, matched option contracts, per-world failures, legal-only
predictor inputs and output hashes. No tests are added or run under the current instruction;
bounded static/syntax checks may be reported separately from scientific evidence.

## 2026-09-27 — owner-requested re-review: end the binary-selector investment

**Disposition: end investment in the unexecuted B01 as written.** Its claim and L0 are
withdrawn; no implementation or result batch is selected. This is a contribution/cost decision,
not a negative experimental result. The earlier proposal remains above so the change is
inspectable. Its scientific cost is **zero fits, zero episodes and zero optimizer updates**.
The DM retains the wider assigned question of a useful learning increment in cooperative UAV
planning; ending this recipe does not answer that question or transfer its ownership.

### Evidence, reusable contribution and closest methods

The motivating [B02 source re-review](../energy_relay_imitation/NOTES.md#2026-09-27--owner-requested-source-re-review-and-b02-corrections)
supports better error on the teacher's shield-inactive stratum under a changed BC objective.
Its native panel means improve with uncertainty and adverse worlds. It provides no observation
of a long-horizon coordination bottleneck, impending service-role departure as a dominant loss,
or residual opportunity beyond a competent planner. Neither additional diagnostics nor proof
of such a bottleneck is a universal prerequisite to exploration; this specific proposal still
needs an informative comparator and a contribution worth its stated cost.

If the proposed selector passed its four-arm rule, the reusable result would be conditional
evidence that a learned return model can choose between two existing feedback controllers
better than always enabling either controller on this S7 panel. The model does not learn new
joint paths, a service layout, a role-transfer action, or low-level multi-agent policies. The
anticipatory controller supplies all these motion proposals through ordinary matching plus
a waiting rule. Switching these proposals is a legitimate modest controller study, but the
proposal does not yet specify the additional reusable planning relation sought by the owner.

The closest learning construction is ordinary **reward-model regression followed by action
selection**. Dudík, Langford and Li's [ICML 2011 paper, section 2.1](https://arxiv.org/pdf/1103.4601)
describes the direct reward-model method from observed context/action/reward data. Our proposed
10/300-step targets would be option-return labels for two controllers. This is a structural
comparison, not an application of that paper's contextual-bandit guarantees: S7 actions change
later states, blocks share history, and learned deployment changes the visited distribution.

For the wider MARL ambition, [ALMA](https://proceedings.neurips.cc/paper_files/paper/2022/file/2f27964513a28d034530bfdd117ea31d-Paper-Conference.pdf)
already learns subtask allocation with low-level agent policies, while
[MAT](https://proceedings.neurips.cc/paper_files/paper/2022/file/69413f87e5a34897cd010ca698097d0a-Paper-Conference.pdf)
models joint decisions as an autoregressive observation-to-action sequence. These are relevant
original structural references, not measured S7 baselines or a claim of an exhaustive novelty
survey. Merely adding a learned high-level choice or a longer return label is insufficient to
specify an increment relative to established methods.

### Strongest ordinary alternative and the comparison failure

H_local already performs global matching with feedback replanning. The anticipatory overlay
adds a standard recent-margin extrapolation, temporary planning exclusion and wait. Its fixed
arm is already state-dependent internally. A further ordinary alternative is a **state-dependent
rolling choice** that weighs service retained during a wait against travel and return timing,
using the same legal observations/history, same available moves and same decision opportunities.
A simple arrival-versus-departure rule is also relevant: advance replacement only when the
ordinary travel estimate and predicted departure timing make it useful. Their actual native
performance is unknown; they are credible competing explanations/comparators, not asserted winners.

The proposed fixed H_local and fixed-overlay arms do not cover this extra adaptive choice.
The 10-step regressor is another learned selector with a different target; it does not stand in
for a competent ordinary rolling planner. A success over the stated four arms would leave
ordinary contextual rule selection as the strongest explanation of the gain.

DM4's B04 draft offers a concrete finite transit-hold scoring approach worth recognizing, but
it uses H_central's current user coordinates. It is **not** a matched H_local-information
comparator and has no completed result establishing superiority. Reusing that scorer unchanged
would break the proposed legal-only comparison. Building an appropriate ordinary comparator
requires an explicit information contract and real engineering, not renaming the central scorer.

The 10-versus-300 target difference changes how much future reward is included, along with
target variability and finite regression difficulty. It is a valid narrow target-window contrast,
but cannot by itself identify a new interaction mechanism. The 300-step target has no learned
continuation value after its block. Both models rank two options using 640 records from 64
worlds, not 640 independent situations; balanced block assignments and policy-dependent later
states need their actual history/support accounted for. Actual selected-option reward labels
are legitimate observations, not synthetic counterfactuals. Still, random-mixture collection
does not guarantee accurate ranking on selector-induced states. One initialization per horizon
is permitted for exploration and is not, by itself, a reason to reject the study.

The earlier independent critique remains applicable: return-margin slope is not a battery
clock; holding changes the slope; relay donors can sustain backhaul; centroid/target order is
not stable per-UAV role identity; the native shield/guard may prevent an intended motion.
Those objections improved the proposed rule, but did not establish that ordinary rematching
constitutes a new cooperation algorithm or resolve the missing adaptive comparator.

### Alternatives considered and full marginal cost

| Possible next observation | What it could distinguish | Known cost and remaining limits | Choice |
| --- | --- | --- | --- |
| Original two-horizon, four-arm B01 | Return-window choice and learned switching versus two fixed feedback controllers | 64 collection + 128 evaluation episodes = 192 H3000 episodes / 576,000 transitions; two fits, up to 1,000 updates. Prior episode timings suggest 105–145 minutes for all native episodes with two workers; model fitting, additional recording/controller overhead, engineering, review and readback are additional and unmeasured. | Withdraw: does not distinguish the requested planning increment from ordinary adaptive selection. |
| Evaluate anticipatory rematching against H_local only | Whether the particular no-fit overlay has complete native utility | 32 paired worlds = 64 episodes / 192,000 transitions, zero fits; simple scaling of the same timing gives roughly 35–48 minutes before added overhead. This is an estimate, not a runtime measurement. | Do not substitute this as an automatic successor: it answers an ordinary-rule question, with no current evidence making it the most useful investment. |
| Add a matched ordinary adaptive planner to the original four-arm study | Whether learned ranking adds native value over that declared ordinary method, beyond the return-window contrast | At least one additional 32-world arm: 224 total episodes / 672,000 transitions, still two fits / at most 1,000 updates if collection is unchanged. Base native time scales to roughly 123–169 minutes, plus currently unpriced legal-state scoring and all other overhead. | Not selected: the ordinary method and the learned increment have not been specified well enough to justify that enlarged package. |
| Smaller revised comparison: 300-step learner versus a specified legal rolling planner | Learned option value beyond that ordinary planner, without paying for a second target-horizon fit | Retaining 64 collection worlds and evaluating two arms on 32 paired worlds gives 128 episodes / 384,000 transitions and one fit (up to 500 updates under the old fitting contract). Base episode time scales to roughly 70–97 minutes, plus unmeasured planner scoring, fitting, engineering and reading. This is a costed possibility, not a registered design. | Not selected now: the comparator and its full scoring cost remain unspecified; a positive preliminary run is not required to reconsider a concrete proposal. |
| Direct learning of joint motion or a residual continuation value | Potentially a distinct planning increment over matched ordinary planning and equally informed ordinary learning | This would require a new concrete action/learning relation, architecture, data and exposure contract. No honest full cost is available for the currently unspecified idea. | Retain as a parent question, not an executable plan or automatic new fit. |

The timing estimates include the 64 collection episodes where present; their environment cost
must not be counted twice. None includes independent training replication for confirmation.
No continuation is made conditional on DM4 first producing a positive score. The current
decision is to buy none of these studies now, rather than create another diagnostic sequence
without a decision-changing purpose. No BC/DAgger/PPO warm-start, extra threshold search or
generic new hierarchy follows from this re-review.

### Scope and retained files

The interrupted helper left no candidate implementation, test, run or scratch directory.
The three short proposal documents are the only retained candidate files, preserving the
withdrawn scope and its reasons. The completed B02 source snapshot has separately been
reclaimed with unchanged canonical evidence, as recorded in its notebook. The remaining
research question is open; the exact B01 investment is closed, with no accepted operation,
pending result or automatic restart.

### Independent scientific challenge and final DM response

One focused ResearchCritic review covered the corrected evidence and this changed investment
choice in a separate context. No DM/Root conversation history was inherited. The assignment
nevertheless disclosed the assigning DM's proposed disposition and prior objections, and an
early scope lookup exposed the prior review. This framing exposure is recorded; the review is
not claimed to have been blind or an uncontaminated evidence-first reconstruction.

The reviewer independently checked the B01/B02 study code against accepted source, verified
both remote summary hashes, and recomputed J from all 64 final trajectories. All trajectory
hashes and reward sums matched. It confirms the corrected J SE, native uncertainty, adverse
worlds, teacher-recorded loss mask, recurrent-history and information limits. It recommends
retaining B02's finite supervision-allocation evidence without treating it as evidence for
a long-horizon planning bottleneck.

Its strongest consequential objection is that both selectors hold an option for 300 steps,
while one learns only ten steps of reward. A 300-step win could reflect better target/commitment
alignment or prediction properties. The four arms omit a service-aware ordinary rolling selector,
so such a win cannot identify an advantage over that planning alternative. It also agrees that
DM4's central scorer cannot be imported unchanged under H_local information rights.

The reviewer gives the following outcome interpretations for the withdrawn design:

- Winning against all three arms would support exploratory contextual selection in this option
  library; it would leave coordination mechanism and ordinary rolling comparison unresolved.
- Beating the 10-step predictor but losing to a fixed controller would improve the target-window
  comparison without producing a useful selected controller.
- No native gain would fail to demonstrate utility of this exact package, while leaving finite
  fitting, activation, representation and collection coverage as possible explanations.
- Higher mean service with worse adverse tails would remain a use-dependent tradeoff.

It recommends **no new run for this disposition**. Its smaller possible revision—one 300-step
learner against a specified legal rolling planner, 128 episodes / 384,000 transitions and one
fit—is included above, with its unresolved scoring and engineering costs. It does not demand
a new architecture, exact headroom or a positive toy result before learning research.

**MATERIAL_DISSENT: yes, against purchasing the original two-fit B01 as the next investment in
the assigned MARL planning contribution.** The reviewer agrees with ending that investment,
retaining corrected B02 evidence and retaining the wider question's ownership.

**DM response:** accept the substantive objection and the no-run recommendation. Withdraw the
original claim/L0 and decline both the original batch and the automatic simpler-rule substitute.
The smaller learning/planning comparison is an acknowledged possibility, not a hidden selected
continuation. The present sources do not yield a sufficiently specified, worthwhile next study
to buy now. This is an investment judgment, not proof that cooperative learning cannot help.
No material disagreement remains over this disposition, and a second review or Pro round offers
no distinct decision value here. B01+B02 imitation work has two completed fits and about
111.61 minutes total runner wall; this unexecuted candidate adds no scientific execution cost.

## 2026-09-27 — concrete successor comparison: learned values for a common transit library

**Scientific-review proposal; no implementation or result execution selected by this entry.**
New Root's published `d235d4e42` [four-DM plan](../../RESEARCH.md#current-research-plan) asks for
one concrete learning/ordinary-planning comparison and an investment decision. The prior B01
withdrawal remains in force. The applicable B02 and withdrawal reviews are reused; neither
the original raw-data audit nor the old two-window experiment is repeated. The new comparison
below changes the executable decision and learning relation, so it receives one focused section-5
challenge before its disposition.

### Question, ordinary references and actual decision

Can a standard offline action-value learner improve complete native service over ordinary
service-scored rolling movement/holding, when both receive the same central information and
the same joint-motion options? A success would supply a useful data-trained ranking of this
specific motion library and a reusable controller/evidence asset. It would not establish a new
general MARL algorithm, a learned trajectory generator, a hierarchy/credit advantage or a causal
long-horizon mechanism. This is a centralized joint-control learning question; there are no
independently adapting low-level agents. It does not change Claude's fixed-label allocation or
credit estimator.

Use the repaired ordinary B04 implementation at
`025350669bc5e8ab99fc71954f749ae47a6853e9`, in
`energy_relay_availability/b04/transit_hold.py`. At every ten-second decision it generates the
usual H1 six-service/two-relay targets and distance/hysteresis matching. Its candidate library is
all-move plus one horizontal hold at the current position for each eligible assigned UAV, at
most nine joint proposals. The other UAVs keep their assigned motion; the vertical controller
continues normally. Hold proposals do not alter H1's target-continuation memory. The commitment
lasts ten steps, with ordinary one-step go-to updates and the unchanged production return shield
and native backhaul guard. Any active/entering shield falls back to all-move in every arm.
The available action here is a joint ten-second movement/hold commitment, not a 300-second
switch between two complete controller programs. It supplies no role replacement during shield
takeover and must not be described as having tested that capability.

The primary ordinary reference **P** is B04's feedback selector: compute the native static
service score at current, nominal step-5 and nominal step-10 joint positions with current users
held fixed and fresh association; choose the maximum `(q0 + 2*q5 + q10)/4`, strict ties all-move
then lowest UAV index. It is already state-dependent, non-additive in joint service geometry,
and refreshed at the same ten-step clock as the learner. It is not an oracle or an established
best possible MPC method. More accurate dynamics, different lookahead and explicit search remain
ordinary alternatives, but are not prerequisites for this narrow complete comparison.

Because B04's own full utility result is still unread here, **H** = H_central@10/all-move is a
second ordinary reference. Its established native competence must not be lost by only beating
a potentially weak new selector. This extra reference costs 32 episodes and no fit; it is not
an extra flat learned arm or a horizon ablation. No favorable B04 result is required to consider
this design. The learned candidate must be useful against both specified ordinary choices.

### Matched information and computation

All three arms deliberately adopt the **H_central@10 contract**, replacing the withdrawn
H_local proposal. They receive current global user/BS xy at ten-step boundaries, legal own-UAV
positions/energy/availability and production shield modes, current H1 targets/history and time.
They share the same target generator, eligible action library, refresh and execution rules.
No raw SET `state`, true user velocities, future waypoints/RNG, live hidden association history
or additional simulator fields enter the learner. The known static S2 radio/routing/demand model
is used identically by P and the learner to produce all candidate scores. H can skip those scores
because it always chooses all-move; its smaller computation is reported, not filled with dummy work.

For a concrete reusable learner interface, the proposed per-candidate input has 250 fields:
time fraction (1); normalized own xyz (24); each UAV's battery, availability, charging, returning,
dock bit and return margin (48); legal station xy (4); central user xy (60) and BS xy (4);
base H1 targets (16) and validity bits (8); shield modes (8); candidate hold one-hot, all-zero
for all-move (8); candidate targets (16); nominal step-5/10 UAV xyz (48); q0/q5/q10/integrated
score (4); and a missing-score bit (1). Invalid targets use the current position with a zero
validity bit. Fallback contexts have one legal all-move option and zero/missing score fields.
Positions use the fixed map/height units; other continuous coordinates and then all feature
dimensions are standardized from collection contexts only, with constant-scale dimensions set
to scale one. No test-panel statistics or post-action fields are used.

These features are a lossy observed-state representation, not a demonstrated Markov state.
The future user motion and association/charging history not encoded here limit Bellman
interpretations. P sees the same permitted primitive inputs and computes the same model scores;
the learner does not gain a new measurement channel. It adds offline experience and a learned
continuation estimate, at an explicitly additional data/fit/inference cost.

### One batch learner, fixed exposure and labels

The concrete candidate **L** is a small shared candidate-value MLP (250→128→64→1, ReLU), trained
from scratch on observed native ten-step transitions. Hidden weights use one declared random
initialization; the last linear layer starts at zero. No BC, old policy checkpoint, actor or
critic is warm-started. The normal tie rule uses P's score and then its deterministic ordering.
There is no separate actor or learned low-level motion generator.

Collect 64 fresh H3000 worlds, 300 consecutive ten-step macro-transitions each: **19,200
transitions / 192,000 native environment steps**. At every nontrivial decision, an independent
behavior RNG chooses P's action with probability .5 and a uniform legal candidate with probability
.5. Record the actual mixture probability, candidate mask/features, chosen proposal, actual
ten-step native reward sum and next context. Fallback has probability one for all-move.
The policy RNG is separate from environment streams. No branching, teacher action label,
synthetic reward, counterfactual return or evaluation-world fitting is used. Scorer copies must
leave live state and all RNG streams unchanged.

One persistent MLP/Adam training procedure runs **5,000 optimizer updates**, batch 256 sampled
uniformly with replacement from the fixed collection, learning rate 1e-3, gradient norm cap 1,
no weight decay/dropout/early stopping. A frozen target copy is refreshed every 100 updates.
The target is

`y = actual_native_J_over_10_steps / 10 + .97 * (1 - terminal) * max_valid_a Q_target(x_next, a)`.

The reward division changes prediction units only; it does not alter native reward or evaluation.
The discount is per ten-step commitment (effective scale about 333 seconds), not a 300-second
observed-return label. Terminal H3000 transitions have zero continuation. Padding is excluded
from the maximum; a terminal context needs no scorer call. This is one started learner fit,
one initialization, 5,000 updates / 1,280,000 sampled transition exposures and 50 target-copy
refreshes, with no independent refit hidden in the count. Save only the fixed final endpoint.
Report actual parameter movement, finite checks, failures and the counts of multi-option versus
forced transitions. They diagnose execution rather than gate a result into a positive reading.

The nearest original bridge is batch fitted action-value learning from transition tuples,
as set out in [Ernst, Geurts and Wehenkel, section 3](https://jmlr.org/papers/volume6/ernst05a/ernst05a.pdf).
Here a persistent neural target-network procedure approximates that Bellman regression idea;
it is not the paper's independently refitted tree algorithm or its convergence guarantee.
The multi-UAV coupling enters the common native reward/next observation and joint candidate
geometry. Finite coverage, bootstrap extrapolation and partial observation can defeat this
construction; .5 exploration does not guarantee coverage of learned-policy visits. Its primary
purpose is a complete utility test, not to identify which one of those limitations dominates.

### Fixed evaluation and decisions it could change

Evaluate final L, P and H on the same 32 fresh H3000 worlds, once per arm: **96 episodes /
288,000 steps**. Provisional unused seed blocks are collection 29092701–29092764 and evaluation
29102701–29102732, with fit seed 29092791; production binding and an exact integer exposure scan
would be part of a selected contract. Use per-world collection RNG derived from the collection
seed plus an independent fixed stream tag. Do not borrow B04's exposed worlds or any sealed
historical holdout. No development evaluations, model selection or second initialization.

The complete proposed batch is therefore **160 episodes / 480,000 native steps and one fit**.
The 64 collection worlds, 19,200 dependent macro-transitions and 32 paired evaluation worlds
are different sampling units; none is an independent training-seed replication.

The primary reading is paired complete QoS/step and raw J for L−P, with L−H as the competence
check. Report paired t31 descriptive intervals conditional on this one fit; all world rows,
zero-service cases, return cost, minimum-battery/lowest-eight tail, fixed reserve exposure,
cutoff/depletion, charging, guard/shield activity, actual holds and runtime remain visible.

- If L exceeds both references by at least .03 mean QoS/step and has positive mean J differences,
  with no additional cutoff/depletion or zero-service worlds, retain a conditional useful learned
  ranking candidate. Any lower-battery or return-cost conflict still needs a stated use judgment;
  the gate does not establish reliability, safety or confirmation. A further fit is a new choice.
- If L only beats P but not H, reject it as an improvement over the competent ordinary portfolio.
  It may expose P's tradeoff; that does not rescue the learned package automatically.
- If L fails to improve native utility, end this fixed data/learner package. Finite optimization,
  observed-state sufficiency and collection coverage remain limitations, without converting them
  into an automatic diagnostic, extra seed, different discount or larger-network sequence.
- A mean service/J gain with adverse failures or tails remains a conflict, not adoption by mean.
  Technical failure or an incomplete panel is missing evidence, never a scientific negative.

All three arms' actual choices occur every ten steps. Thus this avoids the old confounding of
different target windows with the same 300-step program commitment. A win still combines learned
score calibration, discounted continuation, native-reward weighting and offline data. It cannot
be attributed uniquely to horizon length, nor promoted to a hierarchy/MARL mechanism claim.

### Full marginal cost and feasible implementation boundary

The old 70–97 minute quote does not price this scoring/three-arm design. A cost-only read of B04's
completed **32 H_central reference worlds** on configured `local_linux` gives mean worker wall
**168.173803 s** (range 144.658675–212.126331), mean worker CPU **160.660910 s**, peak worker RSS
at most **388,504 KiB**, and raw output **55,887,377 bytes** in total. Source is the accepted
`025350669...` B04 run's perworld file; this reading makes no paired B04 scientific claim.
The candidate arm was incomplete in the inspected copy. These costs are host-specific and are
not silently transferred to wsl_4070.

| Cost component | Prospective amount / estimate |
| --- | --- |
| Native collection | 64 episodes / 192k steps; included in the total below, not counted twice. |
| Native final evaluation | 3 × 32 episodes / 288k steps. |
| Native base work | 160 × 168.174 worker seconds ≈ 7.47 aggregate worker-hours; about 3.74 h with two workers before added scoring/learning/recording. An estimate under comparable contention, not a guarantee. |
| Static service scoring | 128 scored episodes (collection, P and L), at most 38,400 windows × 19 = 729,600 snapshots, 345,600 candidate plans. Earlier 8.1–13.4 ms technical snapshot timings imply 1.64–2.72 additional CPU-hours, about .82–1.36 h at two workers. H does not pay for unused scores. Actual fallback and shorter candidate sets reduce this bound. |
| Fitting | One CPU fit / 5,000 updates; at most 1.28M chosen-feature rows and 11.52M next-candidate rows for target forward passes. No measured fit time yet; provisionally allow 5–20 minutes. No checkpoint is selected by wall time. |
| Recording and preparation | Additional scoring-context storage/serialization, imports and admission: provisionally 15–30 minutes. A 250-field float32 matrix for every possible candidate at 19,200 collection states is at most 172.8 MB before metadata; store next-state references rather than duplicate it. Native raw traces scale to roughly 0.28 GB from the complete reference panel. One canonical evidence copy, with a planning allowance below 1 GB, subject to actual output accounting. |
| Total scientific runner estimate | Approximately **5–6 hours on local_linux with two native workers**, including the above scoring, fit and recording allowances. Different node/load requires an explicit revised price before admission. This is not a runtime stop or automatic retry allowance. |
| Engineering and reading | One bounded adapter/data/learner implementation, independent numerical/RNG/information review and repairs, exact-source publication/admission, then full native readback. Provisionally **2–4 h implementation/review plus .5–1 h scientific reading**; these human/agent wall estimates are unmeasured, separate from runner time, and are reported honestly if exceeded. |

Use of `local_linux` would be a specific CPU-only choice to keep the price grounded in the
recent measured execution path; a fresh node-memory/resource check remains mandatory. This
is no reservation and creates no operation. Reusing the repaired B04 class by a direction-owned
adapter can first compute its base plan/scores, then select/record L's candidate before execution;
H1 continuation memory remains the superclass's base memory. No mutable monkeypatch, copied
shared learner, changes to DM2's files, or new information channel is needed. The adapter must
distinguish P's suggested action from the actually executed candidate in records. Frozen source
semantics and live-state/RNG independence remain engineering checks, not scientific results.

**Proponent's provisional judgment:** this is a concrete, modest learning-utility question worth
considering because it asks whether data-derived value adds to an already capable joint-motion
decision interface, with a competence anchor. It costs substantially more than the withdrawn
binary fit estimate and claims less than a new planning algorithm. The focused independent
review may recommend select, revise or decline; no result batch is purchased by this draft.

**Pre-review source-binding correction:** the actual S2 config has one ground BS and two
charging stations (`b04_transit_hold_a01/config.json`, `n_ground_bs=1`). Thus the BS xy block
above is **2**, not 4 fields; the correct proposed feature/MLP input width is **248**, not 250.
The full collection candidate matrix is at most **171,417,600 bytes** before metadata.
The integer-boundary seed scan finds the proposed seed blocks only in this new note; no existing
run/config/source match was found. These are corrected prospective dimensions, not measured data.

### Native termination clarification

Source inspection of `envs/pettingzoo/relay/energy_aware.py` shows that exhaustion of all
UAV batteries while none is charging terminates an episode naturally. Thus **480,000 native
steps and 19,200 collection transitions are planned maxima**, not required achieved counts.
Keep naturally terminated worlds as scientific outcomes; do not replace, pad, discard or
classify them as technical failures. A final segment shorter than ten steps retains its
actual reward sum divided by ten and has zero continuation. Report actual segment lengths,
episode lengths and terminal kinds. Report native QoS per actual step and also QoS sum/3000;
the latter exposes lost remaining service without changing any environment reward. Equal
seed pairing requires equal initial conditions and equal exogenous user/RNG histories over
the common observed prefix, not equal full-trace hashes when native termination differs.

### Focused independent scientific review — complete substantive response

Reviewer: internal `transit_value_comparison_review`, registered ResearchCritic, separate
context without inherited conversation. It reconstructed accepted B04 source before reading
the proposal and portfolio disposition. Its framing exposure and limitations are retained below.
No duplicate B01/B02 trajectory audit, new environment execution or Pro request was made.

> **Recommend select this one bounded study.** The concrete comparison can answer whether a
> learned ranking adds useful native performance to the specified ordinary controllers at its
> full additional cost. No material design defect currently defeats that observation.
>
> This was a separate context without inherited Root/DM conversation. It was not blind: the
> assignment disclosed the recipe and Root's decision framing, and supplied background
> summaries. I reconstructed the accepted source before reading the proposal and portfolio
> disposition. I made no edits or runs and drew no B04 performance conclusion.
>
> At accepted source `025350669bc5e8ab99fc71954f749ae47a6853e9`, the actual choice is all-move
> versus one eligible UAV holding horizontally for ten steps. H1 already adapts six service
> and two relay targets to current users, performs assignment with hysteresis, and preserves
> target history separately from temporary holds. P adds joint service scoring at nominal
> steps 0/5/10. Users and batteries remain fixed in that forecast; charging transitions and
> future guard interventions are omitted. Real execution retains the shield and guard. These
> facts create a plausible opportunity for learned ranking without establishing that the
> opportunity is large or learnable.
>
> **The strongest simpler explanation is ordinary competence plus reward calibration.** P
> or H may already exploit the useful choices. If L wins, it may simply learn when P's service
> proxy misprices energy, return costs or actual guarded execution. That would still be a
> useful controller result. It would not identify long-horizon reasoning, new coordination
> structure or hierarchy as its cause. The proposal expressly accepts this limitation.
>
> P is a credible primary comparator for this narrow question: it is adaptive, uses joint
> geometry, and shares L's candidate library and decision clock. H is worth its additional
> 32 episodes because it prevents beating a poor service selector from being mistaken for
> improvement over the available ordinary portfolio. Neither reference establishes superiority
> over all capable planning methods. Requiring an additional architecture or exhaustive MPC
> search would purchase a different question.
>
> The **online information and execution conditions match sufficiently** for the proposed
> package comparison. L's offline experience and fitting remain additional resources. P and L
> both compute the static model scores, so this proposal does not amortize away planning
> computation: L pays for those scores plus inference. The corrected **248-feature** input is
> consistent with one ground BS and two charging stations. Fixed collection-only normalization
> and exclusion of future motion, raw central state and live hidden association history are
> appropriate.
>
> The Bellman target is coherent as an approximate **discounted macro-return** prediction.
> Dividing rewards by ten rescales values; `.97` per commitment defines a training objective
> distinct from undiscounted H3000 J. Including time and zeroing terminal continuation makes
> the finite episode boundary explicit. The observation representation remains partially
> observed, so neither Bellman consistency nor convergence follows. Ernst et al. §3 supports
> the transition-to-regression construction; its convergence conditions do not establish
> convergence of this persistent neural procedure.
>
> The principal technical scientific risk is **unsupported value maximization**. The behavior
> mixture gives each eligible action probability at least `1/18` at a visited nontrivial
> context, but does not cover every context subsequently visited by greedy L. Maximizing
> noisy, bootstrapped values can favor poorly supported candidates; partial observation and
> correlated trajectories compound this. Gradient clipping and finite checks do not resolve
> it. Nevertheless, the final native comparison remains informative about whether this fixed
> package works. Those uncertainties are legitimate exploratory risks, rather than reasons
> to insert another diagnostic sequence.
>
> The smallest worthwhile complete observation is the proposed collection, one fixed fit and
> the three-arm final panel. Actual reward must cover the executed, shielded ten-step segment,
> while records distinguish P's suggestion from the executed proposal. Next contexts must
> retain the actual H1 memory and legal action mask. The current controller/evaluator interfaces
> appear reusable through a direction-owned adapter; engineering acceptance still has to
> establish those bindings. No learner or collector implementation presently exists.
>
> The fixed readout should change decisions as follows:
>
> - **L clears the declared service/J criteria against both references without the specified
>   adverse events:** retain this particular conditional controller candidate. Better score
>   calibration, immediate reward alignment and learned continuation remain competing
>   explanations. Replication would require a separate investment judgment.
> - **L beats P but fails against H:** reject the package as an improvement over the available
>   ordinary portfolio.
> - **L fails the utility criterion:** end this fixed data/learner package. This weakens its
>   usefulness at this exposure; it does not identify representation, optimization or coverage
>   as the cause.
> - **Means improve but tails or return costs worsen:** preserve the conflict and make the
>   stated use judgment. Zero observed failures does not establish safety.
> - **Execution or the panel is incomplete:** record missing evidence and actual expenditure;
>   neither a negative scientific conclusion nor an automatic retry follows.
>
> The `.03` service threshold is an investment preference, not a statistical discovery
> boundary. Paired world intervals describe evaluation variation conditional on one fitted
> policy. The 64 collection worlds, 19,200 transitions, repeated minibatch exposures and 32
> evaluation worlds do not provide independent training replication.
>
> The cost accounting is substantially complete:
>
> - **Native work:** 64 collection plus 96 evaluation episodes; up to 480,000 steps.
> - **Fit:** one initialization, 5,000 updates, 1.28 million sampled transition exposures and
>   up to 11.52 million target candidate evaluations.
> - **Planning:** at most 345,600 candidate plans and 729,600 static service snapshots.
> - **Measured anchor:** the 32 H reference episodes average 168.174 worker seconds and
>   160.661 CPU seconds. Scaling gives approximately 7.47 aggregate worker-hours, or 3.74
>   hours with two workers before added work.
> - **Unmeasured additions:** scoring, fitting, serialization, contention and support explain
>   the provisional 5–6 hour local runner estimate. Engineering/review adds 2–4 hours and
>   scientific reading .5–1 hour. These remain estimates.
> - **Storage:** the maximum collection feature matrix is 171,417,600 bytes; reference-scaled
>   native traces add roughly .28 GB. The below-1-GB allowance is plausible, not verified.
>
> This buys a complete conditional utility answer at a credible bounded price. Root's earlier
> request for a concrete choice is now satisfied; neither a requirement to fill a runtime slot
> nor a requirement for B04 positivity should determine this investment. No additional
> scientific review or preliminary experiment is warranted by the present uncertainty.
>
> **MATERIAL_DISSENT: no — I support the specified one-fit investment and its narrow utility
> interpretation, based on the accepted decision semantics, comparator matching and complete
> cost accounting.**

The review's primary source is [Ernst, Geurts and Wehenkel §3](https://jmlr.org/papers/volume6/ernst05a/ernst05a.pdf);
its local evidence is the accepted B04 controller, this prospective entry and B04's complete
reference-world timing metadata. Review agreement is not empirical evidence of learner benefit.

### DM disposition — select B02 transit-value utility comparison

I adopt the review and **select this one bounded study**, named
`uav_cooperative_planning/b02_transit_value_a01`. The old unexecuted B01 remains withdrawn.
The scientific reason is that ordinary scoring leaves a concrete mismatch between nominal
joint service and the actual shielded/guarded trajectory, which a fixed learned value ranking
could usefully absorb. Its utility can be read against P and H without first establishing
the mismatch's size or assigning it uniquely to temporal credit. The approximately 5–6-hour
runner plus 2–4-hour engineering and .5–1-hour reading price is warranted for that complete
conditional answer. This decision buys one fit and the stated panel, not a rescue sequence.

Use the corrected 248 fields, natural-termination rule, exact seed blocks, reward target,
5,000 updates, three arms and outcome rules above. No new scientific review or Pro round is
needed for unchanged implementation. Ordinary fixed-rule execution and independent engineering
review follow; a consequential design change would be recorded prospectively. There is no
accepted operation at this decision and no fit has started. The implementation can proceed
within existing direction responsibility without another Root acknowledgment.

### L0 — bounded implementation of selected B02

Deliver the common-library controller adapter, collection/one-fit/three-arm runner and compact
readout under `experiments/candidates/uav_cooperative_planning/b02/`, with package markers in
its parent. The direction-owned entry is `run.py` (explicit argparse, including launch SHA,
out, workers and numeric threads); it calls runner-side `require_admission` before any scientific
effect. Bulk belongs only to canonical `runs/uav_cooperative_planning/b02_transit_value_a01/raw/`.
No edits to another direction, shared learner, environment, launcher or frozen source. Reuse
the accepted B04 scorer/library and existing production evaluator instead of copying them.

The Implementer owns only that new code tree and returns its diff, static checks and risks;
DM owns NOTES/RESEARCH, Git operations, scientific decisions and launch. The shared checkout
is main, `/home/fires/hmasd-wsl`; other writers' changes must be preserved. No child agents,
Pro requests, result launch, tests added or tests run in this bounded code task. Syntax/static
inspection and independent numerical/RNG/information review supply the current engineering
checks; executable assertions must expose a violated contract rather than silently repair data.

Implementation bindings and acceptance points:

- Exact collection seeds 29092701–29092764; paired evaluation seeds 29102701–29102732;
  fit seed 29092791. `local_linux`, CPU float32 learner, two serial-world workers with one
  numeric thread each, no GPU. A dedicated per-world `numpy.random.Generator` from
  `SeedSequence([world_seed, 290927])` drives the .5 P/.5 uniform mixture independently of
  environment and fit streams. Frozen final policy evaluations perform zero optimizer updates.
- Collection uses actual replan contexts and records candidate arrays/masks, P's recommendation,
  chosen candidate/hold and its marginal mixture probability. Obtain rewards from the existing
  evaluator's actual per-step native `reward` array; aggregate each segment once. Consecutive
  contexts are linked by indices; terminal segments have no successor. Do not score an extra
  terminal state, branch the simulator or repeat a controller replan to obtain a target.
- Preserve separate H1 base memory and actual execution targets. The learned selection happens
  after the inherited scorer constructs the library and before that commitment executes.
  Record both P's recommendation and actual choice; inherited P decision logs alone are
  insufficient. H uses the original all-move controller and incurs no dummy scoring.
- Features follow the corrected 248-field order above. Read only the declared legal observations,
  central position snapshot, fixed model parameters and controller memory. Raw environment is
  used only by the shared declared scorer and by evidence instrumentation inaccessible to L.
  Use population feature mean/standard deviation across all valid collection candidate rows;
  standardize every field after fixed coordinate scaling, constant dimensions use scale one.
  Finite shape checks precede use. Do not use test statistics or fit-time labels as features.
- Fit one 248→128→64→1 ReLU MLP from scratch with the stated zero final layer, Adam, target-copy
  interval, 5,000 updates and .97 target. Sample transition rows with replacement using a fit-only
  seeded stream. Use squared Bellman regression loss; clip gradient norm at one. Store the fixed
  final checkpoint with normalization, configuration and initialization/final movement identity.
  Target evaluation masks padded candidates and terminal continuation exactly. No early stop,
  tuning endpoint, secondary fit or saved checkpoint selection. Fail on nonfinite values.
- Reuse native evaluation trace/reward semantics. Keep natural early termination, final partial
  macro rewards and actual lengths. For paired arms preserve initial-state identity plus user and
  RNG trace equality over their common prefix; unequal native lengths alone are not technical
  failure. Include both native QoS/actual-step and QoS-sum/3000, complete J, tails, all adverse
  worlds, return costs, guard/shield activity, hold counts and stated conditional decision rules.
- One admitted runner performs collection, then exactly one fit, then the 96 fixed evaluations;
  any technical failure leaves incomplete status and prevents dependent stages, no automatic
  retry or replacement. Save compact config, perworld/progress, learner counts/finite/movement
  readings, summary and artifact identities incrementally; raw/checkpoint outputs remain one
  canonical copy. Preserve actual wall/CPU/RSS/storage, transition/fit/update/inference/scorer
  counts and partial work if a stage fails. Do not treat estimates as achieved measurements.

Stop after this implementation and its static checks; DM reviews/accepts and obtains the
independent engineering review before publishing the exact inputs and considering admission.

**Prospective readout clarification during implementation:** “no additional” adverse worlds
is read pairwise against each reference. A new L zero-service world where that reference
provided service, or a larger native cutoff/depletion event count in any paired world, is
an adverse conflict even if another world improves enough to offset the aggregate count.
Show both counts and paired flags. Passing the numerical service/J/adverse-event rule means
conditional candidate eligibility; battery-tail and return-cost conflicts still require the
DM's stated use judgment and cannot be converted into automatic adoption by the runner.

**Relevant main refresh during implementation (`5272918c1`).** DM2 has now published the
complete B04 reading: P−H QoS/step +.01058, descriptive interval [+.00018,+.02098], and J
+34.74 [+2.56,+66.92], with 21 winning and 11 losing worlds. This supplies a conditional
competence observation for P, after the selection/review above; it is not the reason the
study was admitted for consideration, does not establish learning headroom and does not
remove H. DM2's newly selected B05 ordinary one-step scorer is its independent comparison.
Our declared P remains the accepted 0/5/10 scorer; no extra arm, wait-for-positivity rule or
changed collection/evaluation seed follows from that published update. Its future evidence,
if available at our reading, can constrain use claims without changing this fixed panel.

**Implementation storage price refinement, before execution.** Retaining candidate inputs
for the scored evaluation arms as well as collection permits direct final-policy choice
reconstruction. It raises the maximum uncompressed feature matrix bytes across all retained
worlds to **342,835,200**, plus the earlier roughly .28-GB native trace estimate, metadata and
one small final checkpoint. This still fits the prospective below-1-GB storage planning
allowance; compressed and allocated sizes remain actual measurements to report. The
171,417,600-byte figure above remains the collection-only maximum, not the full run size.

### B02 implementation and independent engineering acceptance

The bounded Implementer delivered seven new Python files in the owned package: two package
markers, `controller.py`, `learner.py`, `runner.py`, `readout.py` and admission entry `run.py`.
The DM read the code and accepted the implementation after the independent engineering review
below. No shared or other-direction executable was edited. Accepted B04 `transit_hold.py`
bytes still match `025350669bc5e8ab99fc71954f749ae47a6853e9`.

Static inspection repaired the tied-Q subset's secondary service ordering, made collection
row order independent of worker completion order, checked each L/reference pair through that
pair's own common native prefix, and excluded mutable launcher files from the scientific
artifact digest inventory. The DM also added a persisted fit-attempt start before collection
data are loaded for fitting, fit wall/CPU accounting and explicit incomplete-resource fields.
These changes preserve the selected arms, seeds, learner objective and exposure.

Internal `dm3_b02_transit_value_engineering` used the registered read-only Engineering Reviewer
in a separate context and returned this final disposition:

> **No material finding remains in the final B02 source.** Acceptance remains with the
> assigning DM/Root.
>
> The failure-accounting finding is repaired in runner.py: missing worker telemetry produces
> null totals, measured subtotals and explicit gaps; incomplete scorer/inference counts are
> labelled lower bounds. The parent's fit-start repair also persists the attempt before
> fitting and records elapsed resources.
>
> Static tracing covered:
>
> - Legal 248-field inputs, candidate ordering/masks, behavior probabilities, learned ties
>   and separate H1 continuation memory.
> - Actual shielded native rewards, consecutive context links, partial terminal segments
>   and zero terminal continuation.
> - Collection-only normalization, one 5,000-update fit, masked target maximization and
>   frozen evaluation.
> - Admission before scientific effects, independent RNG streams, paired common-prefix
>   checks, both native contrasts, adverse-world flags and artifact identity.
>
> All seven final files parse successfully and have no trailing whitespace. B04
> transit_hold.py remains unchanged from accepted `025350669bc5e8ab99fc71954f749ae47a6853e9`.
> Final runner SHA256: `20b6b4e8e15e5e934c9cf8a875bb1efd543432a608c6b751f89dc31512bafdb8`.
>
> **Residual limits:** no tests, scientific imports, numerical execution, checkpoint
> loading, multiprocessing, admission handshake or episode execution were performed under
> the assigned restriction. Runtime correctness, convergence, realized pairing and
> resource/storage estimates remain unverified. I made no edits or Git mutations.

The DM accepts that bounded static engineering evidence and its limits. No tests or extra
episodes were added/run; the implementation and review have consumed **zero scientific fits
and zero environment steps**. Engineering labor/model time was not separately instrumented;
the earlier 2–4-hour estimate is not reported as actual measured time. Exact-source publication
and fresh actual-node admission precede the one selected result execution. A later technical
failure remains a failed/incomplete attempt with its actual and lower-bound costs, not an
automatic replacement or a negative utility conclusion.

### B02 native admission and deterministic observation

The exact implementation was published on main at
`9f72afd2223baccd9ed554b0ef86bcbe5277afb5` before the single native launch request.
Admission returned **accepted** at 2026-09-27 18:22:51 UTC. The
[native launch manifest](../../../../runs/uav_cooperative_planning/b02_transit_value_a01/launch-manifest.json)
is the authoritative operation/source/process/output binding; the
[actual-node preflight](../../../../runs/uav_cooperative_planning/b02_transit_value_a01/admission-preflight.json)
and [effective scientific configuration](../../../../runs/uav_cooperative_planning/b02_transit_value_a01/config.json)
are retained with it. The configured local CPU node passed the fresh physical/effective
memory-floor checks. The frozen launcher source snapshot remains in use while this operation
is live; the authoring checkout stays on main.

Same-operation status observed running supervisor and runner identities with consistent
records, no exit witness, and collection initialized. This is technical acceptance and
progress only, not successful fitting, complete evaluation or evidence of utility.

`tools/hmasd_wait.py` was armed in this DM's current thread, generation **1**, window **1500 s**,
job `launch-b02-transit-value-a01`. The first drain observed the existing operation running at
18:24:39 UTC with zero observation errors; no wake was yet due. Its private request is
`temp/directions/uav_cooperative_planning/b02_transit_value_a01/wait-request.json`.
At a checkpoint rearm this same generation/handle through the standard drain/rearm protocol;
do not launch another worker or change the source/output tag to retry. Completion/error must
be reconciled against the native exit witness and complete/partial artifacts before reading.

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

**Checkpoint 1, 2026-09-27 18:49 UTC:** drained the sole CHECKPOINT event. The same native
runner/supervisor identities remain running and consistent, with no exit witness or observer
error. The read summary records **14/64 collection worlds, 42,000 native steps and 4,200
macro-transitions; zero fits/updates and zero evaluation worlds**. All returned worlds are
complete H3000 episodes; failed jobs are empty and stdout/stderr are empty. Recorded parent
wall is 1,547.619 s; 39,178 service snapshots are a completed-world lower bound. Pending-worker
resource gaps are explicitly unmeasured, not zero or a failure. Refreshed published main
retains the active lead/state and no newer pause. Rearmed the existing operation at generation
**2**, 1500-second window; no worker was restarted. This routine progress is not a utility reading.

**Checkpoint 2, 2026-09-27 19:17 UTC:** the sole new event is CHECKPOINT; the original
runner/supervisor remain running with consistent identities, no exit witness and zero observer
errors. The current summary records **30/64 collection worlds, 90,000 native steps and 9,000
macro-transitions**, all returned episodes H3000; fitting and evaluation have not started.
No failed jobs or runner/pool errors are recorded; stdout/stderr remain empty. Parent wall
is 3,262.837 s and recorded service snapshots are at least 83,049; pending-worker telemetry
remains explicitly incomplete. Refreshed published main preserves the active lead and pause
state. Consumed this event and rearmed the same operation at generation **3**, 1500 seconds;
the fixed source, contract and worker are unchanged. No scientific conclusion follows yet.

**Checkpoint 3, 2026-09-27 19:45 UTC:** same accepted operation running, identities consistent,
no exit witness or observer error. **48/64 collection worlds, 144,000 native steps, 14,400
macro-transitions; zero fits/updates/evaluation worlds**, all returned episodes H3000 and no
failed jobs. Logs remain empty. Recorded parent wall 4,898.529 s; service-snapshot lower bound
133,760. Refreshed main retains the active lead and pause state. Consumed the sole CHECKPOINT
and rearmed the same handle at generation **4**, 1500 seconds. No utility reading or new execution.

**Checkpoint 4, 2026-09-27 20:13 UTC:** collection is **64/64 H3000 worlds, 192,000 steps
and 19,200 macro-transitions**. The one declared fit completed **5,000 updates**, 1,280,000
sampled transitions and 50 target copies, in **39.356 s wall / 39.029 s CPU**. Recorded final
loss is .282797 and parameter L2 movement 13.068514; these are execution diagnostics, not
utility evidence. Collection contains 9,369 multi-option and 9,831 forced transitions;
target forward rows 11,482,047 include 6,242,439 valid candidate rows. The fixed checkpoint
`raw/final_value.pt` exists at **166,981 bytes**, SHA256
`e47082385d5ca029629d917ea8387219c307a20bce4390f322c252c4eca93d41`.
Evaluation has returned **2/96** complete worlds, total recorded native steps 198,000;
no paired learner comparison exists yet. Original runner/supervisor identities remain running,
no exit witness, no failed jobs or observer errors, and empty stdout/stderr. Refreshed main
preserves lead/state and pause. Consumed the CHECKPOINT and rearmed the same operation at
generation **5**, 1500 seconds; no new fit, worker or scientific decision was added.

**Checkpoint 5, 2026-09-27 20:42 UTC:** the original operation remains running with consistent
identities, no exit witness or observer error. Evaluation is **22/96 completed worlds (P 22,
H 0, L 0)**; collection remains 64/64 and the single fit remains at 5,000 updates. All 86
returned episodes are H3000, totaling **258,000 native steps**. No failed jobs or runner/pool
errors; stdout/stderr remain empty. Recorded parent wall 8,307.323 s and service-snapshot lower
bound 236,265. Refreshed published main preserves lead/state and pause. Consumed CHECKPOINT
and rearmed the same operation at generation **6**, 1500 seconds. The learner comparison is
still missing; ordinary-reference progress establishes no learning benefit.

**Checkpoint 6, 2026-09-27 21:10 UTC:** the original operation remains running with consistent
runner/supervisor identities, no exit witness and zero observer errors. Evaluation is **44/96
completed worlds (P 32, H 12, L 0)**; collection remains 64/64 and the one fit remains at 5,000
updates. All 108 returned episodes are H3000, totaling **324,000 native steps**. No failed jobs
or runner/pool errors; stdout/stderr remain empty. Recorded parent wall is 9,980.686 s and
service-snapshot lower bound 264,613. Pending-worker resource telemetry remains explicitly
unmeasured. Refreshed published main preserves the active lead/state and lifted pause.
Consumed the sole CHECKPOINT and rearmed the same operation at generation **7**, 1500 seconds.
The learned arm has not returned an evaluation world; no learning-utility conclusion follows.

**Checkpoint 7, 2026-09-27 21:44 UTC:** drained the sole CHECKPOINT event. The original
runner/supervisor identities remain running and consistent, with no exit witness or observer
errors. Evaluation has returned **74/96 complete worlds (P 32, H 32, L 10)**; collection is
64/64 and the one fit remains at 5,000 updates, with zero evaluation optimizer updates.
All 138 returned episodes are H3000, totaling **414,000 native steps**; no failed jobs or
runner/pool errors and stdout/stderr remain empty. Recorded parent wall is 12,105.530 s and
service-snapshot lower bound 291,175; pending-worker telemetry is explicitly incomplete.
Refreshed main preserves the active lead/state and lifted pause. Consumed the event and
rearmed the same operation at generation **8**, 1500 seconds. The 32-world paired panel is
incomplete; no utility decision or change to the frozen study follows from interim means.

**Checkpoint 8, 2026-09-27 22:12 UTC:** the original operation remains running with consistent
runner/supervisor identities, no exit witness and zero observer errors. Evaluation is **94/96
completed worlds (P 32, H 32, L 30)**, with only L/29102731 and L/29102732 outstanding.
Collection remains 64/64; the single fit remains at 5,000 updates and evaluation updates are
zero. All 158 returned episodes are H3000, totaling **474,000 native steps**. No failed jobs
or recorded errors; stdout/stderr remain empty. Recorded parent wall is 13,723.326 s and
service-snapshot lower bound 345,971; pending-worker resource telemetry remains incomplete.
Refreshed main preserves the active lead/state and lifted pause. Consumed the sole CHECKPOINT
and rearmed the same operation at generation **9**, 1500 seconds. The full paired panel and
terminal evidence are still pending; no utility decision or execution change was made.

## 2026-09-27 — complete native B02 reading

The accepted source is `9f72afd2223baccd9ed554b0ef86bcbe5277afb5`; its exact
[implementation](https://github.com/CartmanFatass/My-paper-code/tree/9f72afd2223baccd9ed554b0ef86bcbe5277afb5/experiments/candidates/uav_cooperative_planning/b02)
and frozen 248-field contract remain the source for this result. The operation accepted at
18:22:51 UTC ended at **22:14:35 UTC**, with a valid process-exit witness, exit **0**, absent
original runner/supervisor, consistent operation identity and empty stdout/stderr. All
**64 collection + 96 evaluation worlds completed H3000, 480,000 native steps**; one started and
completed fit made **5,000 updates**, with **zero evaluation updates**, no missing/failed jobs
or unmeasured worker-resource fields. The summary is complete; the progress file retains the
last evaluation callback (160 completed jobs), not a contradictory claim of a live runner.
The sole READY event was consumed with its exact IDs; observer generation **10** has no pending
events/wake and no running observation. No worker/fit was repeated.

### Artifact and native-result readback

Canonical evidence is on `local_linux` / host `Jacob`, at
`/home/fires/hmasd-wsl/runs/uav_cooperative_planning/b02_transit_value_a01/`.
[summary](../../../../runs/uav_cooperative_planning/b02_transit_value_a01/summary.json),
[all collection/evaluation world rows](../../../../runs/uav_cooperative_planning/b02_transit_value_a01/perworld.json),
[manifest](../../../../runs/uav_cooperative_planning/b02_transit_value_a01/manifest.json) and
[existing-artifact readback](../../../../runs/uav_cooperative_planning/b02_transit_value_a01/reading.json)
are compact records; the 160 trajectory archives and one final checkpoint stay in the single
canonical `raw/` directory. There is no orphan raw file. All **165 manifest artifacts** pass
size and SHA256 readback. The **14 native metric sums/means per world reproduce exactly**;
all panel means and paired mean/SD/SE/t31 intervals reproduce exactly. Both L-reference
comparisons retain all 3,000 observed native steps: **64 paired user/RNG trace comparisons**
match, and the three recorded initial-state digests agree in each of 32 worlds.

The reader's first battery-minimum comparison used the wrong source: decoded float32 battery
versus native `battery_min_ratio`. It flagged 114 tiny differences (maximum 3.67836e-9).
The frozen evaluator deliberately records `min_decoded_battery` and the native
`episode_minimum_battery_ratio` separately. Correcting that reader mapping reproduces both
fields exactly in all 160 worlds; reserve/cutoff fractions use decoded ratios and the original
`<=` thresholds. The initial discrepancies and their resolution remain in `reading.json`.
No runner output, threshold or experimental source was changed to resolve them.

The final checkpoint hash matches the manifest and its parameter digest matches the fit
record. Its normalization matches exactly the **94,152 valid collection candidate rows**, in
fixed seed order. Replaying the saved checkpoint on the recorded L decision contexts reproduces
all **4,582 active choices**, with **zero learned-value ties**. This is artifact readback only,
with no new environment interaction or optimizer update. It establishes that the reported
negative belongs to the active fixed learned policy; it does not establish Bellman accuracy,
coverage, convergence or why its ranking loses utility.

### Fixed utility rule and all paired outcomes

The prewritten retention rule required **at least +.03 mean QoS/step and positive mean J against
both P and H**, with the declared adverse-world/tail reading. The final package fails it.
These intervals describe **32 worlds conditional on this one fit**; they are not independent
training replications or a population learning claim.

| Contrast | QoS/step difference [descriptive t31 95% interval] | Native J difference [interval] | QoS wins/losses | J wins/losses |
| --- | --- | --- | --- | --- |
| L−P | -0.016488229 [-0.026709971, -0.006266486] | -55.388987 [-92.449289, -18.328685] | 7/25 | 8/24 |
| L−H | -0.009203793 [-0.021418134, +0.003010548] | -15.895282 [-62.571504, +30.780941] | 11/21 | 11/21 |

The P comparison is adverse for this fit; the H intervals cross zero. Neither gives the required
positive practical increment. The following table retains every world; full costs, battery,
reserve and controller fields are in the linked perworld/readback files.

| World seed | L−P QoS | L−P J | L−H QoS | L−H J |
| --- | --- | --- | --- | --- |
| 29102701 | -0.007240 | -21.487 | -0.013554 | -40.403 |
| 29102702 | -0.031541 | -94.160 | -0.013810 | -42.040 |
| 29102703 | -0.052038 | -161.885 | -0.096629 | -261.583 |
| 29102704 | +0.039169 | +113.874 | +0.053569 | +158.350 |
| 29102705 | -0.028578 | -86.068 | +0.013642 | +42.826 |
| 29102706 | -0.005261 | -16.399 | +0.007663 | +34.230 |
| 29102707 | +0.004166 | +12.482 | -0.012391 | -36.781 |
| 29102708 | -0.010953 | -33.459 | -0.014724 | -44.010 |
| 29102709 | +0.030831 | +60.590 | +0.011239 | -17.073 |
| 29102710 | -0.014975 | -9.841 | -0.024616 | -12.260 |
| 29102711 | -0.060912 | -183.678 | -0.051911 | -156.210 |
| 29102712 | -0.059890 | -182.686 | -0.056061 | -171.410 |
| 29102713 | -0.041776 | -124.436 | -0.044002 | -131.070 |
| 29102714 | -0.031929 | -135.240 | +0.004772 | +45.989 |
| 29102715 | +0.000240 | +1.323 | -0.036565 | -110.697 |
| 29102716 | -0.001162 | -2.842 | -0.011561 | -27.698 |
| 29102717 | -0.003344 | -6.981 | -0.002563 | -8.220 |
| 29102718 | -0.027249 | -80.253 | +0.017867 | +54.598 |
| 29102719 | -0.009110 | -26.739 | +0.026259 | +78.511 |
| 29102720 | +0.033819 | +124.504 | +0.044243 | +201.747 |
| 29102721 | -0.015425 | -46.386 | -0.000323 | -0.844 |
| 29102722 | -0.040498 | -116.847 | -0.019121 | -58.011 |
| 29102723 | -0.050713 | -151.270 | -0.038932 | -117.103 |
| 29102724 | -0.003914 | -11.421 | +0.015247 | +46.008 |
| 29102725 | -0.040965 | -120.744 | -0.041571 | -123.780 |
| 29102726 | -0.012364 | -34.101 | -0.013908 | -44.272 |
| 29102727 | -0.012978 | +46.053 | -0.037689 | +335.317 |
| 29102728 | -0.051871 | -126.638 | -0.002261 | -8.996 |
| 29102729 | -0.048088 | -143.622 | -0.039962 | -119.339 |
| 29102730 | +0.041163 | +121.633 | +0.058371 | +172.609 |
| 29102731 | +0.013671 | +27.592 | +0.038359 | +131.631 |
| 29102732 | -0.027909 | -363.316 | -0.013600 | -278.664 |

### Risk, process observations and contrary worlds

All three evaluation arms have **zero zero-service worlds, zero cutoff and zero depletion**;
all episodes reached H3000. This finite observation does not establish safety or risk equality.
Mean return cost is **P 5.081636, H 13.899052, L 8.041537**. L−P is **+2.959902
[−6.739107,+12.658910]** and L−H **−5.857514 [−22.577112,+10.862084]**. Average native
minimum battery is **P .100023315, H .098624995, L .099850366**; the lowest-eight-world
mean is **P .094525328, H .088916862, L .093643117**. Mean fraction of UAV-steps at/below
10% reserve is **P .007196615, H .017010417, L .008740885**. Signs differ across references;
these averages do not support a general risk-saving explanation.

- **29102732:** versus P, L has QoS −.027909 and J **−363.316106**, return cost
  **+139.792705**. Native minimum battery falls **.101449112→.076675905** and reserve
  exposure **0→.147333333**. This adverse world remains in all means and intervals.
- **29102727:** L loses service versus both references (−.012978 versus P, −.037689 versus H)
  but improves J (+46.053253/+335.316612), alongside lower return cost. It is a real
  service/risk tradeoff, not evidence that every J change measures service improvement.
- Worst L−P QoS is **−.060912316** in 29102711; worst L−H QoS is **−.096629239** in
  29102703. Positive worlds are retained as well; they do not rescue the fixed rule.

L selects **4,575 holds / 4,582 active multi-option windows** (142.96875 holds/world);
P selects **1,600 / 4,558** (50/world), H zero. Shield/fallback times and later visited states
can differ because choices differ. This nearly all-hold deployment is observed behavior,
not a demonstrated causal failure mechanism or proof of unsupported-value maximization.
The fixed feature/model/reward/discount/data package changes several things together; the
result does not isolate long-horizon continuation, credit assignment, partial observability,
finite coverage or optimization. Native guard/shield, charging and all per-world fields remain
available in the complete records.

### Actual cost and retention

Runner wall was **13,899.235 s = 3.86090 h** on `local_linux`, versus the prospective 5–6 h
estimate, with two workers and one numeric thread each. Summed worker CPU was
**27,623.045 s = 7.67307 h**, summed worker wall **27,639.599 s**; parent CPU **42.919 s**.
The single fit itself took **39.356 s wall / 39.029 s CPU**. Parent/recorded worker cumulative
peak RSS was **1,217,092 KiB**; this is not simultaneous node memory or an isolated fit peak.
Engineering/review and scientific-reading time were quoted prospectively and were not separately
instrumented; they are not reported as measured stopwatch totals.

| Stage | Worlds | Summed worker wall (s) | Summed worker CPU (s) | Service snapshots |
| --- | --- | --- | --- | --- |
| collect | 64 | 12585.839 | 12572.747 | 178011 |
| P | 32 | 5621.966 | 5619.685 | 86602 |
| H | 32 | 4240.702 | 4240.059 | 0 |
| L | 32 | 5191.092 | 5190.554 | 87058 |

Actual model cost: **166,581 candidate plans, 351,671 service snapshots, 41,238 L candidate
inferences**. Fit used 1,280,000 sampled transitions, 11,482,047 target forward rows including
padding (6,242,439 valid targets) and 50 target copies. All raw files total **306,466,449 logical
bytes**, including the checkpoint; allocated raw size is **306,827,264 bytes**. Manifest-listed
artifacts total **307,423,045 bytes** before the later readback record. No duplicate bulk package
was created. The canonical directory remains durable in shared main's checkout; it is not a
worktree scheduled for removal. Compact-file digests:

- `summary.json`: 102239 bytes; SHA256 `62e62636ebd180e7603079aaf0c790372fcdd11babc05b29c7294a41a223a741`.
- `perworld.json`: 850873 bytes; SHA256 `8ec68cac74e7293d9ad125b564621c01d471131d8eb0d086bb49556d1bc9b62e`.
- `manifest.json`: 23944 bytes; SHA256 `482c45c28eceeab464c28df91feb79c0bcfa405fb771f82c2248b992e97bd449`.
- `reading.json`: 40552 bytes; SHA256 `78f8c5f6dcc16de012db74ddb692b53b1b2208d191ca00a0ce55a7e48ae6629f`.
- `raw/final_value.pt`: 166981 bytes; SHA256 `e47082385d5ca029629d917ea8387219c307a20bce4390f322c252c4eca93d41`.

The independent result/direction review is in progress in a separate context. Current published
background at `9475b0b5507762bca6152d049e534f492e9b83b3`, especially
[ordinary planning evidence](../../RESEARCH.md#6-实证研究是在具体条件下缩小解释空间), preserves
B04/B05's scoped gains, risk counterexamples and finite-precision limitations. They make P a
substantive ordinary comparison; they do not change this study's frozen arms, add a new arm or
turn the negative into a statement that all cooperative planning is impossible. The final
investment disposition will incorporate the review below.

### Independent scientific review — completed B02 and direction investment

Reviewer: registered `hmasd-research-critic`, child `/root/dm3_b02_result_review`, dedicated
instructions and `fork_turns="none"`. It received source identities, the actual question,
frozen contract and supporting/adverse outputs before proponents' explanations. The complete
substantive response follows; code links are pinned to the executed source for later retirement.

**Recommend stop this B02 package and make no further result-bearing investment now.** Retain P and H as ordinary comparison assets and DM3’s ownership of the broader planning question, with the direction in reserve. This is an investment decision, not evidence that learned cooperative planning is impossible.

No DM/Root conversation history was supplied. The assignment disclosed the comparison and decision framing; a general workspace memory overview was also present. I reconstructed frozen code, native summaries, all per-world endpoints and selected raw trajectories before reading the B02 proposal and prior scientific review. This was separate-context review, not blinded review or protection against model bias. No post-result DM explanation or successor proposal was present in NOTES when inspected.

The execution source is `9f72afd2223baccd9ed554b0ef86bcbe5277afb5`; its imported B04 controller has the identical Git blob to the declared `025350669…` dependency. The [controller](https://github.com/CartmanFatass/My-paper-code/blob/9f72afd2223baccd9ed554b0ef86bcbe5277afb5/experiments/candidates/uav_cooperative_planning/b02/controller.py), [learner](https://github.com/CartmanFatass/My-paper-code/blob/9f72afd2223baccd9ed554b0ef86bcbe5277afb5/experiments/candidates/uav_cooperative_planning/b02/learner.py) and [frozen decision declaration](#fixed-evaluation-and-decisions-it-could-change) support a sufficiently matched **centralized controller-package comparison**: common information rights, target generator, move/hold library, ten-step clock, guard and shield. L additionally receives offline experience and fitting, while still computing P’s scores. There are no independently adapting teammates or new coordination architecture.

All 64 collection and 96 evaluation worlds completed H3000: 480,000 native steps, one fit, 5,000 updates and zero evaluation updates. The collection contains 19,200 transitions, of which 9,369 offer multiple actions. Parameter movement and changed final identity establish execution of learning, not useful value estimation. The DM’s subsequently supplied [full readback](../../../../runs/uav_cooperative_planning/b02_transit_value_a01/reading.json) records complete artifact verification, matching exogenous prefixes and exact reconstruction of 4,582 active L choices. I inspected that evidence without duplicating its complete audit. There is no technical-failure or censoring explanation for this completed result.

The [native summary](../../../../runs/uav_cooperative_planning/b02_transit_value_a01/summary.json) gives:

| Endpoint | P | H | L |
|---|---:|---:|---:|
| Mean QoS/step | .760207 | .752923 | .743719 |
| Mean native J | 2239.932 | 2200.439 | 2184.543 |
| Mean return-cost sum | 5.082 | 13.899 | 8.042 |

| Paired difference | Mean | Descriptive 95% interval |
|---|---:|---:|
| L−P QoS/step | −.016488 | [−.026710, −.006266] |
| L−P J | −55.389 | [−92.449, −18.329] |
| L−H QoS/step | −.009204 | [−.021418, +.003011] |
| L−H J | −15.895 | [−62.572, +30.781] |

The prewritten rule required at least **+.03 mean QoS and positive mean J against both references**, with additional adverse-event and tail scrutiny. L fails even the mean-improvement condition. This is not a borderline decision created by the .03 threshold. The intervals describe world variation conditional on one fitted policy; neither 32 evaluation worlds nor 64 collection worlds supplies independent training replication.

The [per-world evidence](../../../../runs/uav_cooperative_planning/b02_transit_value_a01/perworld.json) preserves consequential positives and negatives:

- L improves QoS over P in 7/32 worlds and J in 8/32; against H, each improves in 11/32.
- Seed **29102704** improves over P by +.039169 QoS and +113.874 J. Seed **29102720** improves by +.033819 and +124.504, with lower return cost.
- Seed **29102711** loses −.060912 QoS and −183.678 J against P.
- Seed **29102732** introduces a substantial risk loss: return cost **140.989 versus P’s 1.196**, minimum battery **.076676 versus .101449**, and reserve exposure **14.733% versus zero**. Its J loss is −363.316.
- Conversely, seed **29102727** avoids H’s return-cost tail, **2.021 versus 226.213**. That single improvement exceeds the entire panel’s net return-cost reduction against H.

Thus “learned conservatism trades service for reliable risk reduction” is not supported. All arms have zero cutoff/depletion and no wholly zero-service world, but these zeros coexist with serious reserve deficits.

The strongest supported diagnosis is **ordinary competence plus an unsuccessful learned ranking at this exposure**. Raw choice arrays sharpen that diagnosis: L selects a hold in **4,575/4,582 active windows**, compared with P’s **1,600/4,558**. In 18/32 L worlds, one particular UAV accounts for at least 90% of active selections; median dominant-choice share is 93.35%. L agrees with P’s recommendation on its own visited contexts only 448/4,582 times. The selected hold proposals change target coordinates rather than being duplicate all-move proposals; guard/shield intervention still controls actual execution.

This persistent holding is an observed policy behavior, **not an identified cause**. Holding itself can be useful. The [B04 outputs](../../../../runs/energy_relay_availability/b04_transit_hold_a01/summary.json) support a conditional P−H gain of +.010578 QoS and +34.736 J. The matched [B05 outputs](../../../../runs/energy_relay_availability/b05_one_step_comparator_a01/summary.json) support five_ten−one_step gains of +.016071 and +35.808, with substantial adverse tails. These make P a credible ordinary reference; they do not establish calibrated anticipation, numerical robustness, or headroom available to learning. B02’s fresh panel also places P above H on both means.

The hypothesis update should therefore remain precise:

- **Opportunity:** useful choices exist within this library, as ordinary-controller comparisons show. Incremental learnable opportunity beyond P remains unmeasured.
- **Representation and learning:** unsupported maximization, incomplete behavioral coverage, partial observation and finite fitting remain plausible explanations. The result does not select among them. The discounted training objective also differs from undiscounted H3000 utility, as declared prospectively.
- **Complete usefulness:** this particular fitted package fails. It adds collection, fitting and inference without demonstrated native benefit or amortizing away ordinary scoring.
- **MARL interpretation:** neither the failure nor isolated favorable worlds identifies a long-horizon coordination or credit-assignment bottleneck.

The actual cost matters. Acceptance-to-exit was **13,903.83 seconds, or 3.862 hours**, on `local_linux` with two workers. Worker CPU totaled **7.673 hours**; the fit itself took only **39.36 seconds**. There were 351,671 service snapshots, 166,581 candidate-plan evaluations and 41,238 learned inference candidate evaluations. Original manifest-listed scientific artifacts total about **307.4 MB**. Engineering, publication and complete review/readback effort are not fully metered. Per-process RSS peaks do not establish simultaneous total memory.

I considered three continuations:

| Possible next observation | What it could change | Recommendation |
|---|---|---|
| More worlds for this fixed L | Precision of its conditional utility estimate | Decline: it already fails the fixed use decision. A comparable three-arm panel costs roughly 2.1 hours at observed two-worker throughput. |
| Another initialization or collection | Recurrence across fitted instances | Decline now: no useful candidate currently needs replication. A reused-data refit is cheap, but its L evaluation alone is roughly .72 hours and does not replicate data collection. |
| Changed target, discount, representation or coverage | Utility of a revised learner package | Decline now: these are legitimate possible explorations, but current evidence does not make one a sufficiently valuable discriminating investment. They should not become an automatic rescue sequence. |

This judgment does **not** require exhaustive diagnosis, exact headroom or a positive preliminary experiment before future exploration. It reflects the present result, competent alternatives, unresolved attribution and complete marginal cost. The smallest worthwhile complete observation for this selected question has already been obtained. Publish it, preserve the behavioral finding and adverse worlds, and release the active runtime commitment. Broader question ownership continues without inventing a waiting dependency or claiming scientific impossibility.

The original bounded investment was defensible and returned useful negative information. Its failure does not retrospectively invalidate that choice, nor oblige Root to keep four DM execution slots occupied. No distinct unresolved expertise question presently warrants Pro; another advisory pass would not supply empirical replication or identify the failure mechanism.

**MATERIAL_DISSENT: no — I support the frozen failure branch and recommend ending new investment in this package, based on negative native means against both competent references and the retained adverse worlds. No competing post-result investment proposal was present to dispute.**

### DM disposition — end B02 investment and reserve the broader question

Adopt the review's recommendation and frozen failure branch. **End this exact offline-data/value-
ranking package; select no further result-bearing study now and set `uav_cooperative_planning`
to reserve.** P and H remain ordinary assets under their existing owner. This closes the
current investment, not the scientific possibility of useful learned cooperation. The broader
question remains with this DM; reserve records an affirmative opportunity-cost choice, with no
pending approval, missing result, external waiting dependency or promised automatic restart.
The exploratory negative is conditional on one fitted instance; it is not a replicated claim
against an algorithm family or a proof that the representation cannot work.

The result changes the expectation that the specified experience/continuation package adds
useful native ranking beyond P. It does not support the alternative story of reliable risk
savings: 29102732 is strongly adverse and 29102727 dominates the net savings against H.
Ordinary B04/B05 gains show some choices matter, while this active learned policy spends almost
every discretionary window holding. The source/checkpoint verification excludes an inactive
learner or missing endpoint as the explanation. It does not identify bootstrap extrapolation,
coverage, objective mismatch or capacity as the cause; none earns a repair by being plausible.

The wider reconsideration includes the earlier imitation result and withdrawn two-window
selector, current DM2 ordinary-planning evidence, and the current division of work at
`9475b0b5507762bca6152d049e534f492e9b83b3`. A fresh fixed-L panel would cost about **2.09 h**
of two-worker execution to narrow world uncertainty without changing this fixed use decision.
A new reused-data fit would be cheap but require roughly **.72 h** for L-only evaluation,
plus an explicit exposure/comparator design; the negative candidate has no current use requiring
such replication. Changing discount/target/coverage could produce a different package, but
there is no resolved prediction here that makes one a sufficiently discriminating investment.
A broader shield-handoff/role-rematching library would require a new concrete ordinary comparator
and alters the actual decision problem; it was never tested by B02 and overlaps ordinary
planning and the Claude coordinator/credit questions already assigned elsewhere. I do not
rename the current failure or take over those questions as a substitute for a useful next choice.
No generic architecture change, exhaustive diagnostic, positive preliminary gate or waiting
condition is introduced. These alternatives are declined now on use and full marginal cost.

One adequate independent scientific review covers this result/route decision. I find no distinct
unresolved expertise or disagreement that Pro could change now; no Pro question is added.
The standing/shared-background update will preserve both ordinary competence and this failed
learned increment, including scope and risk counterexamples. Publish the complete positive,
adverse and uncertainty record independently; no App message or Root acknowledgment is needed.
Acceptance-to-exit (**13,903.828 s**) and runner wall (**13,899.235 s**) use different start
points and are both retained. L's lower observed evaluation worker time than P is not scorer
amortization: both still execute the same scorer, and their visited trajectories and arm order
differ. Withdraw unused B02 implementation from current main after consumer checks; its exact
source remains in Git. Preserve the one canonical raw evidence copy for the fixed contract.

### Retirement of unused B02 files — measured result

After the completed independent review and reserve decision, direct Python/config/entrypoint
consumer search found only the owned B02 self-imports and entry. No external consumer or owned
test file exists. The seven source files still matched accepted `9f72afd...`; original runner
and supervisor were absent, terminal artifacts were read, and the exact observer was stopped
after consuming READY (generation 10, no pending events). No live study depends on these files.

Removed all seven explicitly named files under `experiments/candidates/uav_cooperative_planning/`
and its empty directories with explicit Git paths. Exact-source links above recover the executed
implementation; B04 and all other directions' code were preserved. Removed the sole obsolete
`temp/directions/uav_cooperative_planning/b02_transit_value_a01/wait-request.json` and empty scratch
directories. The private observer state remains at its original task state directory for recovery.

Allocated bytes before→after: implementation **77824→0**, scratch
**12288→0**; both target trees are absent. The cleanup interval reclaimed
**90112 allocated bytes** net. The sole necessary raw evidence remained unchanged at
**306827264→306827264 allocated bytes**, with manifest/trajectory/checkpoint digests already verified.

The exact launcher snapshot `.git/hmasd-launch-sources/ca8f0c6028be4180a7f96bae3ab4b7d3`
remains **1,601,449,984 allocated bytes**. The supported snapshot GC refused its ordinary preview
because `/proc/374/cwd` was not inspectable; the provided elevated read-only scan then refused
with `process 2026 changed during reference inspection`, including one bounded repeat. No apply
or manual deletion bypass was attempted. This is an actual remaining cleanup target/tool blocker,
not released space. No backup, tarball, duplicate retention copy or shared-process repair was created.

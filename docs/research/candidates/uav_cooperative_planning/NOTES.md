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

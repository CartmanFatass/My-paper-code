Claim under test: event-triggered survivor clearing may outperform full retention and one preset random-clearing law on the public-lifecycle host at equal real training exposure.
Binding MARL structure: (a) roster change; (d) other-agent non-stationarity or partial observability.

# FOLR-PUBLIC-LIFECYCLE-TIMING-B01 — prospective three-law comparison

## 1. Status, question and claim boundary

**B/EXPLORE; prospective candidate only. No implementation or scientific invocation is
allocated.** Root assigned judgment/preparation after complete B03 intake under the owner's
synthesis execution command. The [preparation intake](FOLR_PUBLIC_LIFECYCLE_TIMING_B01_INTAKE_20260909.md)
records this authority, retained-denominator finding and object-tier choice. This is a
comparator refinement inside the accepted public-lifecycle family, not a family opening,
recast, C/UAV promotion or Portfolio priority decision. Root reviews this concrete candidate
and allocates any subsequent engineering/execution step.

Question: in one new matched training instance, does the event-clearing trained package
offer a useful final native-return advantage over both generic retention and a fixed
event-independent Bernoulli clearing law? Earlier RETAIN-minus-event differences are
B01 `-2.0021875`, B02 `-1.9228125`, B03 `+2.559375`. B03 reversed the sign and missed the
leading RESET prediction. All three points and their broad conditional evaluation spread
remain in the [B03 scientific intake §§4–7](FOLR_PUBLIC_LIFECYCLE_B03_INTAKE_20260909.md#4-complete-result-against-the-frozen-card).
This weakens the simple repeatability expectation and lowers confidence in event-specific
advantage; it does not erase the first two observations or impose an all-positive-seed rule.

The candidate compares **complete separately trained packages**. Random clearing is
explicitly **unmatched in frequency**. Any difference can combine timing, reset dose,
optimization/data paths and partner co-adaptation. The question does not require strict
separation of those causes. No pure event-timing effect, stale-memory localization,
regularization cause, typed/strictly-self state, stable population winner, original-CAMA
performance or transfer conclusion is sought. The richer comparator changes the next
performance choice without a rate census, exact optimum or explanation prerequisite.

Same-information tuned baseline/upper headroom remains absent. Reuse the accepted generic
RETAIN implementation: host, observation/action/information and training recipe match.
Historical final evaluation had32 episodes, while this candidate fixes128 per arm, so old
checkpoints/endpoints are contextual evidence, not substitutes for any new comparator arm.
All three arms are fresh fits and receive the same new evaluation budget.

## 2. Preserved host, information and learning

Use [B03 card §2](FOLR_PUBLIC_LIFECYCLE_B03_SCIENCE_CARD_20260909.md#2-unchanged-scientific-recipe-and-fresh-randomness)
and accepted source `434f10cf95f16dd342cbf754382aa76155fcd2b7` as the implementation base.
That source does not yet implement RANDOM or128 final episodes; a future CM publishes the
minimal changed source before any execution. No launch SHA is invented here.

Keep native CAMA easy Traffic Junction: five slots/actions, vision1, 7×7 grid,20 primitive
steps, add rate0.1 and the exact native reward/side effects. After each native transition,
actual departures D and births B define true survivors `C=A_before & A_after & ~D & ~B`
and public event `E=any(D | B)`, including same-step replacement. Both lifecycle signals
precede the next controller update. All arms receive identical local attention plus public
E/own B, with unchanged mixer information. The random mask controls hidden-state clearing;
it is not added as a learned actor input feature or a new native observation.

Common rules remain: new trips start fresh, inactive hidden state is zero, and only true
survivors retain the legal preceding action before attention. Slot reuse does not preserve
entity identity. Clearing is applied to the **preceding hidden state before the GRU
processes the current input**; it does not remove that input or clear the newly computed
state afterward. Survivor history may contain teammate information; it is not self-only.

Retain entity-attention GRU64/FlexQMixer, double Q, replay capacity5,000, uniform sampling
of32 complete episodes without replacement, one RMSprop update per episode from episode32,
target copies every200 complete episodes, lr0.0005, clipping and all existing optimizer
settings. Epsilon remains1→0.05 over50,000 training ticks measured at episode start.
Primitive gamma0.99 and no bootstrap at the true20-step cooperative terminal remain;
individual departures do not terminate the team episode. Approximate discounted learning
does not guarantee exact optimization of the final **undiscounted native reward sum**.

The causal path under comparison remains: native membership event → true entity ownership
and common freshness → available local/public information → selected survivor-state law
before action → the same law during learner history reconstruction → native team return.
All evaluation decisions use the arm's trained law, with no parameter updates.

## 3. Three state laws and prospective random-mask protocol

- **RETAIN:** carry true-survivor state, with only the common freshness/inactive handling.
- **EVENT:** the earlier RESET arm; additionally clear each true survivor on public E.
- **RANDOM:** additionally clear each true survivor when its independent external uniform
  draw is below **p=0.1**, whether E is true or false. Public E remains available as in all arms.

The probability is independent of E conditional on the current eligible survivor decision;
realized masks can still correlate with events through eligibility and the evolving trajectory.

The retained B01–B03 outputs do not contain an all-eligible-survivor denominator.
`survivor_opportunities` is gated by E, final checkpoints omit replay/trajectory data,
and aggregate event/return logs do not retain per-decision membership. The read-only
source/artifact finding is in intake §2 and the [plan](evidence/2026-09-09-folr-public-lifecycle-timing-b01-plan.json).
Do not use event-only counts as that denominator, reconstruct old traffic with a new
scientific run, tune p, or match one arm to future events induced by another arm.
Here `.1` is the owner's preset sparse alternative: probability10% at each eligible
decision, not a fitted rate, optimal value or promise of equal realized reset counts.

Freeze all randomness before new output:

- **Training seed7804; final evaluation seed107804**, the next unused pair in the direction
  records. Each arm starts a new process and seeds Python/global NumPy/Torch before identical
  actor/mixer construction order. Create fresh targets, optimizer, replay, environment and
  hidden state; load no earlier weights/data/RNG state. Reset those three RNGs to107804 and
  create a fresh environment before the single final evaluation phase. Native traffic/replay
  retain global NumPy plumbing; Torch epsilon draws, including greedy/terminal calls, remain.
- Only RANDOM uses a separate **NumPy Generator(PCG64(207804))** for training masks and a
  new **Generator(PCG64(307804))** for final-evaluation masks. These generators never supply
  traffic, exploration, replay selection or model initialization. They continue across
  episodes within their phase and are not reset at each episode.
- At every RANDOM controller position `t=0..20`, draw one five-entry uniform vector in slot
  order0..4, including draws for ineligible slots. Set `mask_t = C_t & (U_t < .1)` once.
  The fixed draw schedule has21×5 scalars per episode. At episode entry C is false; new
  entrants/inactive slots never inherit an old owner's state. A terminal mask may affect
  the final controller pass, but there is no native action/bootstrap there and it does not
  enter action-opportunity/reset counts.
- Store each **realized Boolean mask with that episode at its original controller position**
  in the existing replay data. Acting, online and target unroll use that same mask. No model
  forward or replay draw resamples it. The update may use different current/target weights,
  but it must reconstruct the same realized clearing history. Full replay/checkpoint
  persistence, resumption and publication of all intermediate trajectories are not required.

This is one independent new fitting instance per arm under the ordinary PRNG assumption,
matched in base initialization. Neither seed labels nor isolated mask RNG force equal
traffic, since actions and prior masks can affect membership/RNG consumption. Do not pair
same-index episode returns as if they shared a frozen exogenous trajectory.

## 4. Exposure, endpoint, reading and prediction

Each arm trains exactly **5,000 complete episodes /100,000 native ticks /4,969 RMSprop
steps**, publishes one final checkpoint, then receives **128 once-fixed greedy episodes**
under its own trained law. Greedy means epsilon zero; RANDOM's intrinsic clearing remains
stochastic as specified. No periodic evaluation, best-checkpoint selection, post-result
episode top-up or evaluation-only arm reassignment occurs. All final returns and training
returns remain visible separately. More final rollouts target conditional evaluation
variation; they do not add training instances or guarantee a particular SE.

The primary observable is the complete final native-return mean for each arm. Report all
three contrasts: `d_ER=J_EVENT-J_RETAIN`, `d_MR=J_RANDOM-J_RETAIN`,
`d_EM=J_EVENT-J_RANDOM`. **Absolute MEI=1.0 native return unit per episode**, preserving
one target-progress unit/one tenth of a -10 collision penalty and avoiding a ratio around
small or negative returns. For each named contrast, `d>=1` favors its first arm beyond
MEI, `d<=-1` favors its second arm, and `-1<d<1` is WITHIN_MEI, not equivalence.

Use the following combined reading of the new triple only:

1. **EVENT_CLEAR_ADVANTAGE:** `d_ER>=1` and `d_EM>=1`. This supports considering another
   bounded performance discriminator for EVENT against both legal nulls. It does not
   isolate alignment from frequency or establish a general benefit.
2. **SHARED_RESET_GAIN:** `d_ER>=1`, `d_MR>=1` and `-1<d_EM<1`. Both reset packages have
   useful local points over retention, with no above-MEI separation here. This weakens
   an event-exclusive interpretation without proving equivalence or regularization.
3. **MIXED_OR_REVERSE:** all remaining cases. Preserve the three individual signs/margins,
   including any clear RANDOM or RETAIN advantage; finish this finite investment and
   reconsider the next question from the complete evidence. Do not discard an adverse
   arm, tune p after output, or convert an unfinished pair into a selected result.

These branches describe a local trained-package observation. Earlier three pairs remain
separate; their32-episode endpoints are not pooled into the new128-episode branches.
Every branch ends the finite batch with intake, not an automatic successor or family change.
Zero actual eligible/reset exposure limits its dependent interpretation under §11.8.7;
trustworthy native returns remain reportable without filtering event-conditioned episodes.

**DM prediction, after seeing all three old pairs but before new output: MIXED_OR_REVERSE.**
The B03 reversal and broad evaluation spread lower confidence that EVENT clears both
comparators by1.0. RANDOM is untested here, so this is a low-confidence forecast, not a
literature-backed estimate. Other branches remain possible. Owner prediction: not taken
(unattended). Selection of this candidate is outcome-informed B exploration.

## 5. Runner-derived work, proposed cost and stop boundary

The machine-generated plan uses the accepted loops and the explicit128-episode change,
without a target import, simulator call or cost-only run.

| Work quantity | Per arm | New triple |
| --- | ---: | ---: |
| Training episodes / native ticks | 5,000 /100,000 | 15,000 /300,000 |
| RMSprop steps | 4,969 | 14,907 |
| Final episodes / native ticks | 128 /2,560 | 384 /7,680 |
| Total native ticks | 102,560 | 307,680 |
| Acting GRU row forwards, terminal included | 538,440 | 1,615,320 |
| Online-plus-target replay GRU row forwards | 33,391,680 | 100,175,040 |

Dominant work is `3 arms ×4969 updates ×32 replay episodes ×21 positions ×5 slots
×2 actor passes`, plus backward and mixing. Acting adds `3 ×5128 ×21 ×5` rows. RANDOM
alone adds `5128 ×21 ×5=538440` private uniform draws and525,000 Boolean training-mask
entries in the existing finite replay. There is no nested controller search or validation
candidate multiplier. **Exposure per arm:100,000 real training ticks;4,969 trainable
actor/mixer RMSprop steps at lr0.0005;128 final greedy episodes.** Nominal lr×steps2.4845
is not parameter displacement. Additional verification is separate from this algorithm work.

| Complete wall planning, seconds | RETAIN | EVENT | RANDOM |
| --- | ---: | ---: | ---: |
| Mean of three old complete arm walls / proxy | 764.123 | 751.313 | 757.718 |
| Candidate point projection | 778.701 | 765.647 | 772.174 |
| Proposed complete-arm cap | 1,800 | 1,800 | 1,800 |

The known learner/replay work ratio is1.0; native/acting work grows by5128/5032=1.019078.
For planning, apply that latter factor to the complete historical mean, although training
and evaluation phase times are not separately measured. RANDOM uses the midpoint of the
two means as an **unmeasured proxy**, with mask overhead and trajectory variation unknown.
The summed point is2,316.522s, about38.61 minutes; it is neither a guaranteed upper bound
nor a new allocation. Proposed total cap is**5,400s**, with**300s total supporting
engineering/checks/readbacks** for the changed boundary. Full invocation caps include
startup/imports, learning, final evaluation and publication. No extra profiling or cost
experiment is proposed.

If separately allocated, submit RETAIN → EVENT → RANDOM sequentially, exactly one accepted
scientific submission per arm. All arms are planned before output; an intact early sign
does not choose whether later arms run. A failed scientific attempt ends its allowance and
returns the exact partial boundary; no scientific retry/replacement, extra seed, fourth
arm, diagnostic, tuning, extra final evaluation, local fallback or automatic successor.
Uncertain acceptance is reconciled through the same handle. **Current allocation remains zero.**

## 6. Engineering scope, focused acceptance and execution route

Engineering Scope Spec §4 needs only the existing births/departures/event-bound true-survivor
opportunities/actual survivor resets plus **one added aggregate: all eligible true-survivor
control opportunities**, separately for training/final evaluation in each arm. The added
denominator describes actual reset exposure; it does not retune p or retrospectively create
a matched-frequency claim. Count a survivor/reset only where a subsequent native action
is taken; exclude terminal passes and common entrant/episode clears. Birth/departure counting
keeps the existing terminal-step convention. RANDOM reset counts come from realized masks.
Mask storage in the ordinary episode replay is algorithm data needed for consistent history,
not a new telemetry/archive service. No other §4 machinery is needed.

Future implementation is confined to the existing runner plus `model.py`, `collection.py`,
the small counter boundary in `environment.py` and any directly necessary `learner.py`
plumbing under `experiments/candidates/vap_folr_core/public_lifecycle_b01/`. Preserve native
environment, attention, mixer, reward and optimizer semantics. Name future tests under the
existing mapped test surface. No new framework, registry, resume/checkpoint orchestration,
compatibility shim, guard, repeated smoke or full trajectory publication is requested.

CM acceptance must verify the changed action/learning boundary: true-survivor eligibility
with join/leave/refill, clearing before GRU, isolated once-sampled masks, identical realized
masks in acting/online/target replay, terminal-count exclusion, actual new denominator and
128 final episodes with no learning. Reuse old checks for unchanged semantics; add only
focused coverage for those changes and retain required independent review of the high-impact
state/replay semantics. Source/test success is not a scientific result. Evidence spec §§4,
5.2,11.4/11.8 applies; no Pro round or stronger evidence class holds this ordinary B.

Reuse authoring checkout `C:/Projects/HMASD-worktrees/codex-vap-folr`, branch `codex/vap-folr`.
CM/DM edits and index ownership are serialized; Root owns main integration. No implementation
is dispatched by this card. Any later accepted source is committed/pushed and staged in a
new detached exact-SHA remote worktree with new timing-object roots, not reclaimed B01–B03
worktrees. Route to `hmasd-wsl-node`, configured Python, CPU FP32 and one Torch compute/interop
thread, with each arm's own fresh destination admission immediately joined to its runner.
Host identity is not the estimand; no device/dtype/topology substitution is included.

Use the live main Monitor policy/config paths named in B03 card §5. Original CM directly
registers each accepted handle with the shared Monitor and returns pending collection;
Root resumes the same CM on terminal notice. CM retains technical acceptance/closeout,
DM scientific intake and owner brief, and Root integration/capacity/reclamation acceptance.

Claim under test: event-triggered survivor clearing may retain its useful final-return advantage over retention and preset random clearing in one new matched training instance.
Binding MARL structure: (a) roster change; (d) other-agent non-stationarity or partial observability.

# FOLR-PUBLIC-LIFECYCLE-TIMING-B02

## 1. Question, authority and interpretation boundary

**B/EXPLORE; RETAIN accepted, Monitor dispatch accepted, adoption pending; no result yet.** Root applied Portfolio
PRO_FINAL A and assigned this complete triple on 2026-09-10; see
[execution mapping, FOLR](../../portfolio/pro_packets/20260910_next_five_chains/EXECUTION_MAPPING.md#folr--one-new-timing-triple)
and [conforming Portfolio intake](../../portfolio/decisions/2026-09-10-next-five-chains.md).
The current assignment supplies a fresh finite allocation; the earlier triple is complete.
Source/check/card commit `6a8eacdad072c37d477aca95a9c871aba68cee78` was pushed and staged
before RETAIN submission; Root integrated it as main `8eb423ff2`. This is the launch source
for all three allocated laws. [E0](FOLR_PUBLIC_LIFECYCLE_TIMING_B02_RESULT_EVIDENCE_20260910.md)
records the exact accepted command and observation handover. EVENT/RANDOM are unsubmitted.
The shared checkout started clean at `0a809f5282a957e28ff772dc0ffc33cc84b2350a`.
This is an object-tier new instance inside the accepted public-lifecycle family.

Question: does the complete trained-package endpoint ordering recur with new initialization,
training and evaluation streams? TIMING-B01 returned RETAIN 2.54453125, EVENT 5.349296875,
RANDOM 3.985625: EVENT−RETAIN +2.804765625 and EVENT−RANDOM +1.363671875.
The narrow latter margin, broad conditional evaluation spread, EVENT's lower cumulative
training return, and earlier B03 RETAIN-over-event reversal remain contrary evidence.
[Prior intake §§9–13](FOLR_PUBLIC_LIFECYCLE_TIMING_B01_INTAKE_20260909.md#9-complete-result-against-the-frozen-card)
retains all outcomes. No previous fit, evaluation episode or RNG state is reused here.

The ceiling is one new matched fitting-instance observation of three separately trained
packages. RANDOM remains **p=.1, unmatched in dose**; timing, joint reset pattern,
data/optimization paths and partner co-adaptation can contribute together. No pure timing,
isolated stale-memory cause, event-exclusive benefit, stable population superiority,
self-only memory, tuned headroom, original-CAMA performance, transfer or C claim follows.
Current same-information tuned baseline/upper headroom is absent. The accepted RETAIN
baseline matches this host, observation, action, information and training/evaluation budget.
No baseline fitting or upper-reference measurement is added.

## 2. Preserved mechanism, host and learner

The accepted implementation is source `74d023d7d55453da8a5d5dccebd518e4ffdb65c8`.
The source surface is unchanged at the current checkout before this new seed binding.
[TIMING-B01 card §§2–3](FOLR_PUBLIC_LIFECYCLE_TIMING_B01_SCIENCE_CARD_20260909.md#2-preserved-host-information-and-learning)
supplies the unchanged host and laws; its old instance and execution ownership do not
govern this new assignment. Native CAMA easy Traffic Junction has five slots/actions,
vision1, 7×7 grid,20 primitive ticks and add rate .1. Native rewards and side effects stay.

True survivors are `C=A_before & A_after & ~D & ~B`; public `E=any(D | B)` includes
same-step departure/refill. Births create fresh entities, inactive hidden state is zero,
and true survivors alone retain legal previous actions. All laws have the same local
attention, public E/own birth and mixer information. RETAIN carries survivor hidden state;
EVENT clears it on E; RANDOM clears on its recorded eligible Bernoulli mask. Clearing
acts on the incoming state **before GRU processing**. The realized mask is algorithm data,
not a learned input feature; acting, online and target replay reuse it without resampling.

Entity-attention GRU64/FlexQMixer, double Q, 5000-episode replay, uniform32-episode sample
without replacement, RMSprop lr .0005 and existing clipping/settings remain. One update
per episode starts at episode32; targets copy every200 episodes. Epsilon1→.05 over50000
training ticks, episode-start scheduling, gamma .99, and the true20-step cooperative
terminal are unchanged. Departures do not terminate the team episode. The final observable
is the undiscounted native reward sum, distinct from the discounted training objective.

The trace is native membership event → true entity ownership/common freshness → local
and public information → selected incoming-state law → acting and consistent learner
history reconstruction → native team consequence. Unchanged foundations and prior CAMA/
Sable retrieval from TIMING-B01 intake §3 are reused: a recurrent policy depends on its
realized history, and a complete-package comparison does not isolate a mechanism cause.

## 3. New instance and RNG binding

Freeze **training 7805 / evaluation 107805**, common across the three fresh processes.
Python, global NumPy and Torch seed before model construction in the accepted order;
construct new model/target/optimizer/replay/environment and hidden state. Reset all three
to107805 and create the final environment once after training. Existing traffic/replay
global NumPy and Torch epsilon draws, including greedy/terminal draws, stay unchanged.

RANDOM alone uses phase-persistent private `Generator(PCG64(207805))` for training and
new `Generator(PCG64(307805))` for evaluation. Neither stream supplies initialization,
traffic, exploration or replay sampling. Each RANDOM controller position t=0..20 draws
five uniforms in slot order, including ineligible slots, then stores `C & (U < .1)` once.
The generators persist across episodes and differ between phases. Terminal masks are
replayed but enter no native action/bootstrap or action-opportunity/reset counts.

The labels were checked prospectively against direction/source/test records; no prior
scientific use was found (an unrelated library-manifest byte length7805 is not a seed).
This is a new independent fitting instance under the ordinary PRNG assumption, matched
in base initialization across arms. Same labels do not fix exogenous traffic trajectories
after actions and RNG consumption diverge. Same-index final episodes are not paired
worlds. One new fit per arm cannot estimate training-population uncertainty.

## 4. Exposure, endpoint, reading and prediction

Each law receives **5000 complete training episodes /100000 native ticks /4969 RMSprop
updates**, one final checkpoint, then **128 non-learning greedy episodes /2560 ticks**.
RANDOM's intrinsic mask remains stochastic at epsilon zero. No periodic evaluation,
checkpoint selection, favorable-arm selection, episode top-up or repeated final panel.
Report every final return and all cumulative training evidence actually recorded:
training return sum/mean plus episode/update/wall logs. No per-episode training return
curve exists in the accepted runner; none will be reconstructed or inferred from those logs.

Primary means are J_RETAIN, J_EVENT and J_RANDOM. Report `d_ER=J_EVENT-J_RETAIN`,
`d_MR=J_RANDOM-J_RETAIN`, `d_EM=J_EVENT-J_RANDOM`. **Absolute MEI=1.0 native return unit**,
one target-progress unit / one tenth of a collision penalty; a relative rule would be
unstable around small or negative means. Each d>=1 favors the first arm; d<=-1 favors
the second; -1<d<1 is WITHIN_MEI, without an equivalence claim.

The new triple alone uses the unchanged combined rule, in order:

1. **EVENT_CLEAR_ADVANTAGE:** `d_ER>=1` and `d_EM>=1`.
2. **SHARED_RESET_GAIN:** `d_ER>=1`, `d_MR>=1` and `-1<d_EM<1`.
3. **MIXED_OR_REVERSE:** all remaining cases.

How the result will be interpreted: above-MEI EVENT gains over both controls would add
another local point in favor of that trained package; a shared gain would weaken event
exclusivity, and an inside-MEI or opposite-sign result would weaken repeatability and
favor reconsidering unchanged-law spending. Preserve all individual signs and margins.
Every branch ends this allocation with full intake and advice, without an automatic
successor or family disposition. Keep earlier32-episode pairs separate. TIMING-B01 may
be described alongside B02 as two matched fitting instances with the same128 endpoint;
it never enters B02's reading rule or becomes prospective confirmation. Zero actual
eligible/reset exposure limits the dependent interpretation, not trustworthy native returns.

**Prospective DM prediction: EVENT_CLEAR_ADVANTAGE, low confidence.** The immediately
preceding three-law observation supports recurrence more directly than the old two-law
pairs, but its small EVENT−RANDOM margin, adverse training mean and B03 reversal make
failure to recur plausible. This is an outcome-informed exploratory forecast, not a
probability estimate or stable-performance claim. Owner prediction: not taken (unattended).

## 5. Work, cost and stop

The [machine-generated plan](evidence/2026-09-10-folr-public-lifecycle-timing-b02-plan.json)
computes the fixed loops without target imports or a simulator/cost run. Total exposure is
**3 fits ×5000×20 training ticks +3×128×20 final ticks =307680 native ticks;
14907 RMSprop calls;384 final episodes**. Per-law exposure line:100000 real training ticks,
4969 actor/mixer optimizer steps at lr .0005,128 final evaluations. Nominal lr×steps2.4845
is not parameter displacement. The real learner can move under the unchanged accepted path.

Dominant replay work is `3×4969×32×21×5×2=100175040` actor-row forwards, plus backward
and mixing. Acting adds `3×5128×21×5=1615320` rows. RANDOM alone adds538440 private
uniform draws and525000 finite-replay Boolean entries. No nested search, candidate sweep,
trajectory search, diagnostic or validation multiplier. Supporting checks are separate.

The old triple's conservative complete-chain charges739/788/820s project RETAIN/EVENT/
RANDOM at the same work ratio1, sum2347s (39.12min), not a guaranteed upper bound. The
old precise runner walls738.20/786.72/819.15s excluded preflight and are **not** complete
chain clocks. The new allowance is **1800s per complete law,5400s summed triple, plus
≤300s separately accounted support**. Admission, initialization/imports, training, final
evaluation, publication and exit belong to each complete law. Record complete outer wall,
CPU work, runner wall and study elapsed separately. Use outer time/timeout around the
admission-to-runner chain; no timing pilot. The research-directory test budget remains
cumulative, including earlier checks; it does not restart at B02.

Execute RETAIN → EVENT → RANDOM, exactly one accepted invocation each, all selected
before output regardless of earlier signs. A failed invocation preserves trustworthy
partial facts and stops the dependent sequence. No scientific retry, replacement, second
triple, mask-dose matching, extra scientific test/pilot, extra evaluation or automatic successor is
allocated. Reconcile uncertain acceptance through the original handle. No local fallback.

## 6. Engineering, acceptance and observation

Scope Spec §4: this object needs the **existing five aggregate counters** (births,
departures, event-bound survivor opportunities, all eligible survivor control opportunities,
actual survivor resets), separately for train/final per law, to describe realized dose.
Action/reset counts exclude terminal passes and common entrant/episode clears; birth/
departure terminal convention remains. Ordinary realized replay masks are algorithm data.
No new §4 machinery is needed or added. Existing detached supervisor, source binding and
resource receipt are the mandated execution route, not new infrastructure.

Own only this direction's card/E0/intake/brief, runner seed/publication wiring and mapped
tests in the shared checkout `C:/Projects/HMASD-worktrees/codex-vap-folr`, branch
`codex/vap-folr`. Model/collection/learner/environment stay unchanged. The DM performs
science and implementation directly under Root's current assignment. Reuse accepted state,
membership, mask/replay and terminal checks; check the changed seeds, once-per-phase
generators and published metadata with the three existing scientific-stand-in runner
cases. Independent Astra/high review covers this RNG diff; no repeated scientific smoke.
Tests, review and process exit establish engineering facts, not a performance conclusion.

Commit and immediately push exact source before any launch. New detached worktree on
`hmasd-wsl-node`, configured `/home/wu/.venvs/hmasd/bin/python`, CPU FP32 and one Torch
compute/interop thread. Host identity is not part of the estimand; no device/precision
substitution. Fresh destination `admit-memory && runner` per accepted invocation, wrapped
as one supervised command. Check only the declared source surface when later docs differ.

Read live `C:/Projects/HMASD/.codex/hmasd-monitor.toml`; directly register each accepted
handle, source/cwd/root/receipt with that existing Monitor. Record dispatch separately
from Root-confirmed adoption. Return pending collection, with no parallel DM status polls;
Root resumes the same DM at terminal for collection and the next allocated law. The DM
owns technical acceptance, separate scientific intake and scoped closeout; Root integrates
and accepts execution closure. All incomplete or adverse outcomes remain visible.

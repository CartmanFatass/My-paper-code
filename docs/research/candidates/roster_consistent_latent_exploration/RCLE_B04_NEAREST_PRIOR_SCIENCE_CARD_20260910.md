Claim to test: a nearest-guided FLEX controller can learn lower post-churn unmet demand than the attained INDEPENDENT-NEAREST service reference under the unchanged native reward.
Binding MARL structure: agent-count scaling or roster change, with shared policies adapting their coordinated native service after membership changes.

# RCLE-TBCFV-B04-NEAREST-PRIOR — master24

## Authority and question

One B/EXPLORE fit is selected by the complete four-slot Portfolio decision,
`docs/research/portfolio/decisions/2026-09-10-four-slot-rolling-refill.md`, its immutable
response at `1ea43d8fbc846807d71d4d894136f357f65551b6`, and its RCLE execution mapping.
Root's restart assignment transfers the remaining DM implementation/execution/intake
to `/root/dm_rcle_restart_recovery2`. The clean shared authoring checkout is
`C:/Projects/HMASD-worktrees/dm-rcle-a02-20260906`, branch `codex/rcle`.
It was fast-forwarded from 85b5b1435 to current main 6b07553ec and pushed; no live
B04 handle or previous B04 implementation/card was found. Existing B03 results remain.

The accepted [design intake](RCLE_SERVICE_COMPARISON_DESIGN_INTAKE_20260910.md) §§2–5
fixes the scientific content below; its old design-only allowance is prospectively
superseded by this explicit allocation. The next observation asks whether real learning
improves an attained service rule. This is outcome-informed exploration inside FLEX,
not a new family, direction recast, fourth unchanged B03 replica, or C claim.

## Learner, information, state and comparator

One fresh B04 domain/master24, one FLEX fit ending at exactly 200 updates. Reuse
the existing eight training cells, 64 episodes per update, 64 native ticks per episode,
full Y=1−sum(u_t)/64, manager-score mean plus100 times claim-score mean, one joint
backward and normalized nonzero full-vector step .02, then .95/.05 cell baseline.
All26,161 parameters remain trainable. No fitted B03 state or baseline is loaded.

The 81 legal pointer fields and six candidates are unchanged. Distance is field76,
the signed circular distance divided by60. At each four-tick claim opportunity,
minimum absolute distance wins; exact ties choose the first beacon index.
The probability is softmax(pointer scores + log45 on that nearest candidate).
The pointer output affine starts at zero; probabilities initially are .9 nearest
and .02 for each other action. Other fresh tensors and zero FLEX final update heads
come from the existing initializer. Six untrained helper allocations plus the new
subclass produce one trained model, seven allocations in total. The same probability
tensor supplies sampled actions and their selected-action log probabilities; the
trainable scores can override the fixed offset. No action is masked.

Tick24 membership changes alter legal public sets, physical positions/demands and
distances. Surviving entity state follows FLEX; departed state is removed, newcomers
receive its prescribed state/noise, and rank is recomputed rather than used as a
persistent slot identity. ACTIVE_CONTINUATION and NEW_EPOCH retain distinct event
paths. No rejoin/replacement or new identity semantics are introduced. Fixed four-tick
claims, primitive time, undiscounted Y and partner co-adaptation are unchanged.
Native movement/proximity coverage produces U; claim-demand shortfall produces F.
F is not an optimization reward. Tau remains the first qualifying four-zero-U run,
with failure coded40, not an uncensored recovery time.

Three roles receive the same eight held-out cells×256 scenarios: the initialization,
the final200 sampled learned policy, and deterministic INDEPENDENT-NEAREST. Initial
and final share semantic exogenous/action-uniform addresses; reference shares exogenous
addresses and consumes no actor uniforms. Distinct training/evaluation purposes and
cell domains remain. Policy-dependent trajectories need not match. Reference receives
no privileged information, training or tuning; the learner has the larger compute bill.
Reference Y is unavailable in the existing wrapper and will remain null. No matching
tuned same-information baseline package/headroom exists; attained-reference deficit
is not upper-minus-tuned-baseline headroom or equal-training-efficiency evidence.

## Measurement, reading and prediction

Primary Delta_ref is equal-weight U_reference−U_final on ACTIVE_CONTINUATION8→12
and12→8. Positive favors final. Report both path levels/contrasts, G_U=U_initial−U_final,
signed remaining gap U_final−U_reference,40U, every eight-cell U/F/tau level and contrast,
tau40 counts/fractions, and initial/final Y. One complete fresh fit is the independent
learning unit,n1; conditional paired-scenario Monte Carlo SE and an approximate95%
interval do not estimate training-population uncertainty. Retain all outcomes/blocks.

Absolute U MEI=.05, the accepted design's two normalized unmet-demand ticks over40.
There is no F MEI, F/U exchange rate, aggregate utility or post-hoc nonharm threshold.
Apply every applicable row; all branches end this allocation.

| Observation | Bounded reading and recommendation |
| --- | --- |
| Delta_ref≥.05 and G_U>0 | Above-interest local service improvement over the attained reference with native learning; retain the size of G_U, both paths and every F/recovery consequence. Consider one independent follow-up only through a later allocation. |
| 0<Delta_ref<.05 | Small reference improvement; retain exact size, initialization gain and cost. No stable superiority claim. |
| Delta_ref≤0 and G_U>0 | Learning may improve the supplied stochastic prior, but the attained reference deficit remains; do not call this competent-reference superiority or automatically extend training. |
| G_U≤0, whatever the reference contrast | No positive learning-from-initialization claim; report any supplied-prior benefit separately. |
| Opposed primary paths or worsened F/recovery | Mixed native consequences, reported alongside intact service facts. No post-hoc scalar tradeoff or unqualified nonharm. |
| Reward/information/training/primary defect | No dependent performance polarity; preserve any independently trustworthy facts and actual exposure. |

How the result will be interpreted: an above-MEI benefit with learning supports a
bounded independent follow-up recommendation. A smaller benefit retains its exact
size without automatic extension. An opposite sign bounds this candidate at200;
initialization improvement alone does not defeat the reference. F/recovery harm stays
alongside service facts. None of these outcomes explains the old weight100 effect,
establishes general recovery, stable superiority, tuned headroom or transfer.

DM prediction before numerical work: G_U>0, but Delta_ref≤0 after200; the supplied
.1 exploratory mass plausibly leaves an attained-reference deficit. Confidence60%,
a judgment rather than a calibrated probability. All-cell F nonharm and improved
recovery are not predicted. Strongest support: B03's native service learning across
three roots. Strongest contradiction: reference deficit, failure-coded recovery and
seed23 fragmentation harm in all eight cells. Owner prediction: not taken (unattended).

## Exposure, cost and stops

Machine-generated [EXPOSURE_PLAN.json](b04_nearest_prior_20260910/EXPOSURE_PLAN.json)
uses the existing cost law and fixed counts. Intrinsic work:1 fit×200×64=12,800 training
episodes,3×8×256=6,144 endpoint episodes, total18,944 episodes/1,212,416 ticks;
200 backward/update calls,400 rollout batches,2,293,760 neural agent-claim decisions×6
scores. The prior adds a six-way nearest comparison and constants, no extra controller
or trajectory. L2 path-length budget is200×.02=4.0 for nonzero steps; actual displacement
and its ratio to fresh initialization norm are reported. Changed score-gradient flow
is checked on supplied tensors, not an extra environment trajectory.

Caps: learned≤150s, reference≤10s, all additional invoked runtime support≤140s,
complete≤300s. Learned/reference caps include adjacent admission, imports/startup,
initialization, learning, all panels/checkpoint/publication and process exit. A simple
external timeout bounds each complete arm. Earlier same-shape200 analogues were
89.83s learned with initial/final,80.62s with final only, and2.85s reference. The new
action-law/build cost is unmeasured; those are analogues, not a certified forecast.
All build/staging/focused checks/review execution/Monitor/collection/analysis/publication/
preservation/cleanup are charged once within140s. Authoring/reasoning calendar time is
unmeasured and separate. No transferred sibling savings, automatic retry, extra seed,
1000-update extension, evaluation panel, reference fit or profiling is allocated.

## Engineering L0 and execution

- Deliver a thin B04 model/study, fixed entry and final comparison publication. Owned
  source: `experiments/candidates/roster_consistent_latent_exploration/b04_nearest_prior/study.py`,
  `scripts/run_rcle_b04_nearest_prior.py` and its literal sequential `.sh`; focused tests
  mirror the study under `tests/experiments/candidates/roster_consistent_latent_exploration/b04_nearest_prior/`.
  This placement follows current experiments/AGENTS rather than the design's proposed
  sibling directory. Existing B01/B03/model/native sources stay unchanged.
- Preserve the legal inputs, entity state, full native reward/metrics, FP64 CPU, one
  compute thread, semantic RNG consumers,200×64 update exposure and sampled endpoints.
  Ordinary checkpoints store tensors and explicit nearest-prior/initialization settings.
- Acceptance: independent high-risk review (§7.3) and one supplied tensor/output check
  covering ties, .9/.02, action/score identity, live gradient, checkpoint and full run
  publication plus branch boundaries. No native validation episode is allocated.
  Synthetic allocations/backward/stub outputs are technical exposure, separately recorded.
- Remote-first at wsl_4070, `/home/wu/.venvs/hmasd/bin/python`, detached exact-SHA
  worktree with `/usr/local/bin/agent-task`. Linux CPU FP64/thread1 only for this attempt;
  no local fallback is selected. Publish source/command, then each admission is joined
  by && immediately before its runner. Read current main Monitor configuration and send
  MONITOR_ADD after accepted launch; dispatch is not adoption. No duplicate polling/run.
- Stop at complete endpoint or actual failure/cap/dependent defect; preserve partials.
  No new §4 machinery is needed. Existing learner checkpoints and owner supervisor/
  Monitor are reused. Standard≤2000 source lines,≤600 runner lines and cumulative≤300s
  focused-test budget apply. Creator cleans only its own test scratch.

Scientific reading: current Foundations §§3–6,02_MARL information/shared-parameter
sections and04_EMPIRICAL independent-unit/package comparison sections support the
assumption that the legal distance preference changes an inductive bias, not actor
information. Representability and finite learnability are separate. Reuse the design's
verified local MARL-0576 guidance passages/coverage limitations (§6); no new literature
claim or acquisition is required. Neither that paper nor this rationale predicts
competence or supplies a causal explanation.

## Decisions this card produces

Object tier: options(a) freeze/execute the Portfolio-selected exact B04 comparison,
(b) defer or change the design. Recommend/select(a), preserving the allocated question,
counts and caps. Owner-delegated decision (unattended,2026-09-03 instruction): **(a)**.
Portfolio allocation is PRO_FINAL / OWNER_DELEGATED; no local Portfolio disposition.
Read/apply owner reviews at each clean boundary; none applied at recovery. Record
the new-card item, prediction score at intake, audit, E0 and Chinese valid-result brief.
Return acceptance/evidence and any later allocation recommendation to Root; all
branches end this allocation without buying a successor.

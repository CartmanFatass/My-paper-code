# UCOPE UAV motion prefix B01 — P24 scientific intake, 2026-09-07

**Accept COMPLETE / WITHIN under the fixed P24 rule.** The two fresh pair
means are +0.0433518665 and −0.0503654225, averaging **−0.0035067780**
against MEI ±0.01. The four-pair outcome-informed descriptive mean is
**+0.0058553213**. P21 retains its original UP reading; neither this new
result nor the combined description establishes stable equivalence or
superiority. The allocated work is complete, with no further experiment or
family/Portfolio decision in this intake.

## 1. Assignment, authority and checks

[P24](../../portfolio/handoffs/2026-09-07-p24-ucope-fresh-uav-pairs.md)
allocates exactly two fresh pairs and their all-outcome intake.
[P26](../../portfolio/handoffs/2026-09-07-p26-ucope-fresh-pair-plumbing.md)
permits the bounded seed/pair plumbing correction. [Card §10](UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md#10-prospective-p24-fresh-pair-continuation-and-p26-plumbing--2026-09-07),
prospective commit `8cb59913be5015c3948e4a1c24024147023fdf97`, selects
masters 6901/6902, preserves §§2–5, and fixes the new-pair primary and
four-pair descriptive reading before output. Controlling evidence-spec
§11.8.1–4 and §11.8.6–7 separate native facts, independent units,
scientific interpretation and engineering conformance.

I read both complete CM returns, the committed verification/count/exposure
facts and the P24 aggregate against those card sections. I inspected actual
summary/config/RNG bindings, native arrays, saved episode and selected
diagnostic rows, and the supervisor commands/admission/terminal receipts.
The [E0](UCOPE_UAV_MOTION_PREFIX_B01_P24_RESULT_EVIDENCE_20260907.md) records
the **verbatim rule**, counts, both signs, receipt identities, caps and
limits. The [scientific analysis](UCOPE_UAV_MOTION_PREFIX_B01_P24_SCIENTIFIC_ANALYSIS_20260907.json)
recomputes the question-relevant endpoints and selected movement/learning
descriptions from saved bytes; it agrees with the original CM aggregate.
It uses one endpoint per training pair and no second pairing or episode
pooling. It adds no environment, model, optimizer, evaluation or checkpoint
execution. Existing accepted source/review/tests support unlogged learner
internals; they were not replayed during intake.

The two technical commits are `eb287e235d98eba404f534defbb2b09c4b58fda7`
and `b5a79533a623b42d1cea4a2a989216c908b1c979`, already integrated by Root.
This designated `codex/ucope` checkout started clean at the latter commit.
The live Portfolio P24/P26 pointers supply this assignment; its older UCOPE
row is historical context. This intake changes no Portfolio surface.

## 2. Native reading and comparator limits

The applied card rule is:

> -.01 <= Delta <= .01: no gain at the selected scale under this budget; not stable equivalence.

P24's mean **−0.003506778020263196** is inside that interval. Its two
endpoint sample SD is **0.06626813058389298** and conditional evaluation SE
of the mean is **0.007033641405302189**. The endpoints lie on opposite sides
of ±0.01. This describes materially different fitted-policy outcomes; a small
joint point estimate does not mean the individual effects are small or that
the two algorithms are equivalent.

| Master | T−G | Conditional SE | Adverse T−G episodes | G−H | Conditional SE |
| --- | ---: | ---: | ---: | ---: | ---: |
| 6901 | +0.0433518665 | 0.0101066870 | 9/32 | −0.0282038164 | 0.0139165852 |
| 6902 | −0.0503654225 | 0.0097848517 | 27/32 | +0.0171009380 | 0.0118908145 |

The gain in 6901 is against a G fit whose observed return is below fixed
hover. T itself is +0.0151480500 above hover there. In 6902, G exceeds hover,
while T is −0.0332644846 below hover. These reference comparisons retain both
the weakness of one generic fit and the native harm of the other T fit.
They are not reasons to erase either T−G endpoint or to relabel a complete
run as an engineering failure. Competent generic control across this budget
is not established; hover is neither tuned nor an upper reference.

For the four named training pairs, the equal-weight descriptive mean is
**+0.005855321301029148**, sample SD **0.040359534081716275**, and conditional
evaluation SE **0.005149755379587538**. Three positive means coexist with the
largest-magnitude negative mean; all remain visible in E0. This continuation
was selected after P21 outcomes, so n=4 is explicitly outcome-informed
description. It supplies no new success rule, prospective confirmation,
population variance claim or replacement for P21's +0.0152174206 / UP.
No absence-of-gain conclusion extends to the whole UCOPE direction.

## 3. Movement, local information, action and native credit

The source-backed event path remains velocity → position/channel/service →
each owning UAV's next local observation → recurrent state and owned velocity
→ primitive native reward → PPO credit. Five actors co-adapt inside a fit;
membership is fixed and local sorted slots are not enduring entity IDs.
During T's hold, observations, memory and reward continue. G keeps the same
free information and legal movement, including repeating a velocity or
hovering. No independent sensing fee or actor-visible diagnostic was added.

Saved final-evaluation summaries describe 160 agent prefixes per arm/pair,
not 160 independent learning runs:

| Opening observation | 6901 T / G | 6902 T / G |
| --- | ---: | ---: |
| Mean displacement over first four steps, m | 82.5813 / 57.2555 | 79.2356 / 56.2720 |
| Mean path length over first four steps, m | 117.6736 / 123.4796 | 116.2577 / 121.2947 |
| Local user set changes t0→t4, of 160 | 95 / 89 | 94 / 83 |
| Other local input values change t0→t4, of 160 | 148 / 142 | 140 / 139 |
| Local user-entry total, t0→t4 | 270→267 / 270→277 | 283→295 / 283→299 |

Of T's 79/72 long prefixes, 73/63 receive changed other-local values during
the hold. All T/G agents make a new decision at t4 with a command different
from their t0 command; stochastic command differences do not demonstrate
causal use of those inputs. The stored timing/masks correspond to the
accepted source and CM technical checks. Actor inputs exclude diagnostic
source indices and centralized critic data.

T therefore retains the larger opening displacement in **both** new pairs,
including the native loss. T's opening observed-user total falls in the
positive pair and grows in the negative pair. These selected snapshots do
not support a consistent “more opening observations imply more return”
account. Later local-entry counts were not collected, so this is no exclusion
of every information-mediated effect.

Normalized contributions from the first four versus remaining 252 steps are
+0.0000163047 / +0.0433355618 in 6901 and +0.0000533506 / −0.0504187731
in 6902. The positive opening reward differences coexist with opposite and
much larger complete-return outcomes. The package changes learned trajectories
throughout the episode; this split does not isolate an opening intervention
or attribute later returns uniquely to information. Geometry, motion
persistence, recurrent memory, action-sample exposure, optimization and
partner co-adaptation remain alternatives. The complete native loss takes
priority over favorable movement or input-change diagnostics.

## 4. Exposure, interpretation and prior evidence

All four new fits execute their 1,024 Adam calls and have nonzero parameter
motion; exposure totals are **573,440 actual UAV team steps / 4,096 Adam
calls / 192 final evaluation episodes**. Both new duration heads move from
zero and remain mixed at final evaluation. Neither mixed duration use nor
parameter movement shows that the duration rule is useful.

The retained four successive 128-episode on-policy training means are:

| Master / arm | Block 1 | Block 2 | Block 3 | Block 4 |
| --- | ---: | ---: | ---: | ---: |
| 6901 / T | 0.13519 | 0.10291 | 0.12116 | 0.15677 |
| 6901 / G | 0.11892 | 0.17429 | 0.15079 | 0.11693 |
| 6902 / T | 0.06432 | 0.02622 | 0.07695 | 0.09445 |
| 6902 / G | 0.12699 | 0.14225 | 0.13337 | 0.15687 |

These are saved training curves under changing policies and reset samples,
not repeated final-checkpoint evaluations or a causal learning-progress
estimate. They rule out a literal zero-learning account together with the
actual updates/checkpoints; they do not localize the comparator's weakness
or identify a training repair. No defect threatening native measurement,
reward, information or learning integrity was found.

**Strongest support:** three of the four fitted-pair means favor T, including
the new +0.04335 result, and the selected legal movement/observation/action
path is realized on the real UAV host. **Strongest contradiction:** the new
−0.05037 T−G and −0.03326 T−hover result, the positive pair's weak G reference,
and both P24 and the descriptive four-pair point means below the MEI. The
current record supports heterogeneous finite-budget packages, with no
demonstrated persistent advantage at the chosen scale.

The prior question-driven local-library retrieval is reused from [proposal
§5](UCOPE_POST_B01_RETURN_MODEL_QUESTION_PROPOSAL_20260907.md#5-question-driven-source-check)
and [P21 intake §4](UCOPE_UAV_MOTION_PREFIX_B01_INTAKE_20260907.md#4-predictions-evidence-change-and-alternatives).
That verified DACOM/VIL2C evidence concerns downstream decision consequences
and native cost, not these UAV policies. The VIL2C local source is
`C:/Projects/Inst-sci/papers/MyLib/json/MARL-0203.json`, page4 elements
227/229/230 and page5 elements295/303/304; the proposal retains the DACOM
pointer and verified real-corpus search coverage. No new coverage or novelty
claim is made. What it changes here is the interpretation: changed local
inputs or a movement statistic do not rescue the native loss or establish
information value. No extra related-work search or implementation follows.

Finite-host B05's positive acquisition result remains motivation on its own
host. B04's harmful extra purchase/negative endpoint, B01's nulls and older
false-probe/unchanged-competence evidence remain separate and unpooled.
The retained-policy numerical-locus family stays at its earlier boundary.

## 5. Predictions, resources and owner flags

| Prospective P24 prediction | Probability | Observed | Score |
| --- | ---: | --- | --- |
| New joint reading UP | .60 | WITHIN | Miss |
| Both new G−H means positive | .60 | Negative in 6901 | Miss |
| Each new T d4 frequency strictly between .1 and .9 | .80 | .49375 / .45 | Match |

**One of three predictions matches. Owner prediction: not taken
(unattended).** P21's earlier predictions remain scored against P21 only.
Live-main unapplied reviews and relevant UCOPE ledger owner columns were
empty at the final clean boundary, **2026-09-07 23:30:51 PDT**. Ordinary result facts,
predictions and object choices remain in this intake/card/audit, with no new
P1/P2 item or fabricated reply.

Both invocations finish with intact primary/hover/diagnostics and no cap
breach. Summed external wall is **564.93 s**, with measured peak RSS and fresh
actual-node memory admission; aggregate CPU/scratch are
`resources_unmeasured`. The recorded P24 supervisor interval is927 s and
includes its technical-return gap. No engineering §4 additions or §5 budget
breach, extra evaluation, retry or new execution occurred during intake.

The [P21 entry chain on card §9](UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md#9-observed-p21-completion-and-uav-entry--2026-09-07)
remains the actual B UAV-validation entry, linked to Pro decision
`426513b18b38b477dd255b3e8524424d8deb8a19`. The P24 sign reversal does not
erase that entry or count as another direction entering UAV validation.
No C promotion/consumption, lifecycle, priority or recast-count change follows.

Owner-visible limits: native harm in 6902; no across-pair competent-generic
claim; unknown tuned headroom; outcome-informed n=4; no pure-information,
stable performance, transfer, safety or deployment conclusion. Audit owner
flag is `none`: the rule application is unambiguous, with no material critic
dissent or separate close-call decision. Uncertainty is reported directly.

## 6. Decisions this intake produces

1. **Object / scientific acceptance:** (a) accept COMPLETE / WITHIN at the
   fixed class and retain all endpoint/reference signs; (b) return a concrete
   CM primary/integrity gap; (c) infer equivalence or select only favorable
   pairs. Recommendation and selected **(a)**: all dependent data are complete
   and the original rule applies as written.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
2. **Object / current allocation boundary:** (a) complete this two-pair
   continuation and recommend reassessing this single-opening prefix before
   expanding it; (b) append unchanged seeds now; (c) close/recast the family
   or promote locally. Recommendation and selected **(a)**, following the
   card's inside-MEI narrative. The new sign reversal and comparator weakness
   change the value of unchanged expansion; this is not an all-seeds-positive
   requirement or a failure of the declared B class.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**

The [audit rows](../../portfolio/audit/2026-09-07.md#ucope-p24-joint-scientific-intake--2026-09-07)
record those reversible object choices. The Chinese [owner brief](../../portfolio/owner/briefs/ucope/2026-09-07_uav-motion-prefix-b01-p24.md)
preserves the loss and current boundary. There is no additional owner item
for ordinary result acceptance or an automatic family disposition.

## 7. Next discriminator and return boundary

The next useful question is whether a **specifically justified change to
the one-opening prefix** can improve native service relative to competent
ordinary feedback at a bounded real-training budget. This result gives no
reason to privilege larger displacement or more opening input changes as
the success criterion. A complete causal diagnosis, tuned headroom, exact
policy upper or separate competence-only prerequisite is not required.

Direction-local next-task recommendation: a bounded source/evidence-based
question-selection task for this same DM within the accepted family, using
this intake and the unchanged feedback comparator. Its deliverable would be
one concrete treatment/comparator amendment with an action-to-native-return
reason, or the exact family-scope question to return to Convergence if no
such amendment is justified. This is advice for Portfolio planning through
Root; **no amendment, Pro request, new card/CM assignment, invocation or
investment/lifecycle decision is selected by the current intake**. It does
not ask Root to choose the science.

Any eventual performance discriminator should use real learning and sampled
complete native return, preserve every outcome and declare its own work.
For scale only, the completed unchanged two-pair route used four fits,
573,440 team steps,4,096 Adam calls and564.93 s summed external wall under
the original1800/3600/7200 s caps. That record is not a forecast or budget for
an unselected amendment. P24 now returns complete at a recoverable boundary;
the existing family stays open under its prior decision until changed by
the appropriate authority.

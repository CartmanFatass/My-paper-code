# P79: intact ordinary critic plus hold gate, or end this instantiated comparison?

Proposed claim: adding the existing remaining-hold gate to the full attained ordinary critic may improve sampled native return at a fixed 768-episode learning budget.
Binding MARL structure: temporal abstraction or termination; entity-owned residual holds enter centralized training while decentralized recurrent actors observe during those holds.

**Consultation preparation, not a selected card or result.** Ask `em:vsp_c1:convergence`
to decide whether this concrete B continuation is worth selecting, or to end the
instantiated gated-value comparison. DM recommends the latter, for the bounded
investment reason below. The node may question that recommendation and the
candidate's assumptions. No family disposition has been taken locally.

## 1. Current authority and the decision that is actually open

Root's P79 assignment follows acceptance of [B12 intake §6](VSPC1_NATIVE_HOLD_VALUE_B12_INTAKE_20260909.md#6-p78-valid-result-intake-and-decisions).
It authorizes one authored question and fixed GitHub publication, with **zero new
scientific invocation, retry, tuning, checkpoint reevaluation or new card**. Root
dispatches the ready request; independent Transport owns provider Send and observation.

| Restriction or choice | Actual authority and scope |
| --- | --- |
| One preparation-only consultation | Current P79 assignment. Publication is authorized; this DM does not Send or run. |
| Direction decision, including the next object/family question after historical C work | The existing proper node under AGENTS §§2–4; its full direction authority is not replaced by a local DM stop, a three-seed rule or a narrow historical packet. |
| Same actor, information, host, gate and 768 budget in the candidate below | A concrete DM performance proposal, **not** a permanent owner restriction on every conforming direction decision. If these assumptions need changing, say what and why, with the new claim/work, instead of treating their necessity as established by these results. |
| Existing P49 decision | It opened the named native hold-value comparison. Its original one-pair definition is historical authority for that opening, not a new launch authorization or a limit on this node's current decision. Later B protocols retain their own definitions. |
| Lifecycle, priority, capacity, fusion, investment across directions | Portfolio/Root responsibility; no such disposition is requested. ACTIVE/MEDIUM is the current Portfolio row. |

Keep the existing Convergence conversation and accepted requests unchanged. A
complete conforming answer is final for its node. A concrete owner/spec conflict
must return to that same node before the affected requirement is executed. A
connector or delivery failure forms no decision and has no scientific polarity.

## 2. Evidence that motivates this question, including contrary outcomes

Three independent matched training pairs use continuous fits, private train/eval
state, fixed 512 and 768 endpoints and one common 32-identity H panel. Their
primary `C = Delta768 - Delta512`, where `Delta = mean(J_GATED - J_MLP)` and
`J = native reward_sum / 256`. Each endpoint/primary is read at absolute MEI .01.
Episode SE is conditional on fitted policies; checkpoints are repeated observations.

| Master | Delta512 (conditional SE) | Delta768 (conditional SE) | C (conditional SE) |
| --- | ---: | ---: | ---: |
| 8501 | +.0638797040 (.0076598446) | +.0096406106 (.0080877338) | −.0542390934 (.0092154971) |
| 8502 | +.0213148509 (.0043565904) | +.0093906006 (.0076329951) | −.0119242503 (.0074169721) |
| 8503 | −.0149815972 (.0072213019) | −.0735897558 (.0103586543) | −.0586081586 (.0114590896) |

All three Cs are CHANGE_DOWN; 512 is **UP/UP/DOWN**, 768 **WITHIN/WITHIN/DOWN**.
Full SEs/vectors and every adverse identity are in the machine facts and the
accepted individual intakes. 8502 C is only .0019242503 below negative MEI and its
768 point only .0006093994 below positive MEI. 8503's 512 DOWN is also close to
its boundary (.0049815972, .68985 conditional SE); its 768 deficit is much larger
(.0635897558 below negative MEI, 6.13880 SE; 31/32 negative identities).

| Master | GATED512 / MLP512 | GATED768 / MLP768 | H mean | H-loss identities: G512 / M512 / G768 / M768 |
| --- | --- | --- | ---: | --- |
| 8501 | .2003165067 / .1364368028 | .2041025987 / .1944619882 | .1706160337 | 10 / 23 / 10 / 13 |
| 8502 | .2091129100 / .1877980590 | .2093991683 / .2000085677 | .1623154235 | 5 / 10 / 7 / 9 |
| 8503 | .1653390673 / .1803206645 | .1611642375 / .2347539933 | .1394977424 | 11 / 11 / 14 / 5 |

8501 MLP512's mean is below H; every other learned mean here exceeds H.
Every episode loss remains reportable. H is untuned zero-velocity control, not
an upper reference or a tuned competence certificate. **Matching tuned
same-information headroom is absent.** The MLP768 endpoint in 8503 is the
strongest attained comparator in that pair, not an oracle.

Descriptive n=3 mean/sample SD: C −.0415905008/.0257844332; Delta512
+.0234043192/.0394721498; Delta768 −.0181861815/.0479810656. Every MLP mean
increases more than its paired GATED mean between these endpoints. In 8503 the
GATED change is −.0041748298 (SE .0094990262), MLP +.0544333288 (SE .0084185173).
These are finite-panel learning realizations, not a population interval,
equivalence, stable inferiority or isolated causal effect of additional budget.

Keep the **older protocols separate**. Final-only normalized width133 512 pairs
8301/8302/8303 gave +.0165919114/−.0066345182/+.0333779164 (UP/WITHIN/UP).
Final-only 768 pairs 8401/8402 gave −.0338649204/−.0135349558 (DOWN/DOWN).
8401 GATED−H was −.0405925743 and MLP−H −.0067276539; 8402 both learned
means exceeded H but retained 6/7 episode losses. Earlier width128, unnormalized,
quarantined attempts and historical service-allocation/UCOPE evidence keep their
original meanings. No pooling or retrospective relabeling follows. The facts
retain all current and older width133 native/contrast/H records with source pointers.

## 3. Strongest concrete continuation case

The current comparison spends about the same critic parameter count differently:
GATED has a 136→128→128→1 body plus 640 gate parameters (34,817 total),
while ordinary MLP has a 136→128→133→1 body (34,827). The generic comparator
has 650 additional ordinary-body parameters. This is direct source arithmetic,
**not evidence that those parameters caused the late differences**.

The proposed new package gives **both arms that full ordinary 136→128→133→1
body**. Copy all common parameters, including the five privately initialized
extra second-layer rows/biases and their initially zero output weights. Only the
treatment adds the same zero-initialized bias-free 128×5 remaining-hold gate:

`MLP hidden = tanh(z + B r)`; `GATED hidden = tanh(z * (1 + A r) + B r)`,
with `z = W_x x + b`, the existing 131 non-hold inputs `x`, five existing
remaining/4 inputs `r`, and the first-layer gate `A`. The second layer is now
133 wide in both arms. Counts are **35,467 versus 34,827**, +640 or **1.83765%**.
This preserves the strongest attained generic body and tests adding the bias
without replacing ordinary units. It is explicitly **not capacity-matched**.
Any gain would belong to the whole parameterization/optimization package; it
would not uniquely identify hold credit, sharing or a capacity explanation.

Actual source anchors at preparation SHA `a46b4bf232f2b544720eccaa3a569a97c199d08d`:
`native_hold_value_b01/critic.py` GatedCritic and models (the current factory
does **not** widen GATED); `native_hold_value_b05/critic.py` WideCritic;
`native_hold_value_b01/study.py` Config/run_pair; and the B12 runner. Their full
repository paths, hashes and symbol ranges are in the facts. Wrapping a common
WideCritic in the existing GatedCritic is a source-based implementation idea;
it has not been implemented, imported, instantiated or tested in P79.

The concrete path remains opening duration at t0 → each of five fixed agents'
remaining hold at t1–3 → centralized critic/value loss and joint optimization →
separate local recurrent actors → motion/service → native reward. Both actors
have the same 108-dimensional local inputs and duration1/4 choice only at t0,
observe/update recurrent state during holds and use ordinary feedback after t4.
The critic's 136 inputs are assembled before the decision: t0 remaining holds
are zero, so the just-chosen duration is unavailable. The critic does not select
actions. There are no joins/leaves/replacements or slot-identity changes here.

Preserve normalized critic targets with cumulative FP32 moments, decoded native
values for gamma1 full-episode return-to-go advantages, detached/normalized
advantages reused across four epochs, compound-agent PPO ratios, joint gradient
clipping, native reward, action law and partner co-adaptation. About 1.13% of
training rows have nonzero holds. Shared weights/moments/clipping can propagate
their influence, so sparsity is an objection, not an upper bound on return effect.

Why this is the strongest continuation case: it retains early positive instances
and preserves the strongest attained ordinary architecture, with one small,
explicit change and a real late-return discriminator. The late gain remains
untested. Neither the previous positives nor the source's nesting promises it.

## 4. Lowest sufficient future measurement and known work

If the node selects this continuation, the proposed minimum is **one fresh
matched training pair**, two continuous 768×256 real fits, with final768 sampled
returns and the common H reference only. The future master is unselected; use
fresh initialization/training/evaluation domains, matched between arms where
declared. No old training state, tuned choice, H panel or checkpoint is reused.

Primary is the new package's final768 `Delta`, with one prospective checkpoint
and absolute MEI .01 (one mean native-reward point per 100 steps; a useful
decision scale relative to attained means around .14–.23). UP above .01 would
support one bounded new independent follow-up if its native/H behavior warrants
it; WITHIN including boundaries would provide no selected-scale local advantage;
DOWN below −.01 would favor the ordinary body for this pair. Retain conditional
noise, every native/H loss and every result. These proposed descriptive branches
do not establish equivalence, stable superiority or cause, and are **not frozen**.

Dropping the intermediate panel answers a new final-budget performance question;
it is not another C-change measurement. Preserve the accepted four-environment
train/eval separation and frozen evaluation moments. Do not select the old
`fixed_endpoints=False` route if doing so restores shared train/eval environment
state. A future CM change must implement the named final-only measurement while
preserving that boundary. No old result is reinterpreted or pooled into this B.

| Known algorithm work | Proposed full-body-plus-gate B | Legal fourth unchanged two-endpoint pair |
| --- | ---: | ---: |
| Fits × episodes × primitive steps | 2 × 768 × 256 | 2 × 768 × 256 |
| Training steps / Adam calls | 393,216 / 3,072 | 393,216 / 3,072 |
| Rollouts × epochs | 768 × 4 | 768 × 4 |
| Evaluation panels × episodes × steps | 3 × 32 × 256 | 5 × 32 × 256 |
| Evaluation episodes / steps | 96 / 24,576 | 160 / 40,960 |
| Total native team steps | **417,792** | **434,176** |
| Environment constructors | 4 | 4 |
| Complete arm / whole caps proposed | 1,800s / 3,600s | 1,800s / 3,600s |

Per proposed arm: 196,608 train steps, 384 rollouts, 1,536 Adam calls and
8,192 learned-eval steps; MLP also carries 8,192 H steps. Four epochs evaluate
1,572,864 target-row terms across the pair. There is no nested candidate search,
counterfactual trajectory or solver loop. Added validation is a focused check of
the changed model/comparison/primary-output boundary, **not** another scientific
arm, pilot, profiling run or replay. Scope §4 machinery needed: **none**;
ordinary ≤2,000 new production/≤600 runner lines remain the future CM bounds.

The unchanged protocol's actual whole walls on hmasd-wsl-node CPU/FP32/thread1
are **475.85/507.29/504.91s**, sum 1,488.05s or 496.0166667s per valid pair.
They are planning references, not guarantees for the new body/gate or a complete
historical cost. New per-arm unit time, incremental gate/body wall, engineering
time and aggregate CPU work remain unknown. The proposed cost law is the known
train/rollout/epoch/evaluation factors above; no added cost experiment is needed.
Future portable execution uses remote_first and actual-node admission. No host
effect is claimed; no launch or resource admission occurs during consultation.

A fourth unchanged pair remains a legal B: it mainly adds another realization
of the current performance variation. Extra old-checkpoint evaluation mainly
refines conditional panel noise. Exact policy maxima, full support/causal
diagnosis or bounded/beam search would answer a stronger different question and
have unspecified additional work; none is a prerequisite for either real B.
The recommendation below is evidence-specific, not a three-seed stop threshold
or an added Pro gate for conforming A/B work.

## 5. Literature changes and what Pro should decide

Task-specific retrieval asked whether critic-architecture work supports the
specific intact-body proposal or requires a different competent null. Verified
Inst-sci catalog coverage is 190 real records; bounded critic/capacity and prior
ACAC/MVD/UTE searches preceded source reading. The existing My-lib mechanism
index contains two documented synthetic demo rows; its existing page index has
zero rows. No real coverage there was assumed, and no index/acquisition ran.

Source-verified MARC, Utke/Houssineau/Montana, AAAI2025,
DOI10.1609/aaai.v39i20.35390, PDF hash and JSON passage pointers in the facts:
p5 elements142/145/155 describe per-agent local-observation action-value critics,
a shared relational encoder, individual heads and SAC-style updates; element167
states comparator selection criteria. Those are different information/action/value
consumers from this single central state-value critic and PPO learner. **Resulting
choice:** keep the attained same-information MLP; no graph/SAC conversion or
claim that MARC predicts a hold-gate recovery. The full-body idea comes from our
source contrast, not that paper. Reuse the previously verified P49 §6/B03 §9/P67
§4 ACAC/UTE/MVD/PPO limits; none establishes unique hold credit or a budget cause.

**DM recommendation to the node: end this instantiated gated-value comparison
without a successor B on the present evidence.** This is a recommendation only.
The strongest reason is the accumulated absence of a selected-scale 768 advantage,
8503's large attained-comparator deficit and mixed512 performance. The wider
gated body is a plausible, inexpensive-looking package change, but its late
benefit is speculative and buys additional generic capacity. That is insufficient
for the DM's next-investment preference; it is not evidence that all hold-credit
or value-sharing mechanisms fail. The strongest case against this recommendation
is the preserved early positive instances and the direct, modestly changed,
one-pair performance test. Pro should assess that case at B class, without
demanding C evidence or a complete mechanism explanation.

Please return one conclusion-first formed direction decision, its exact smallest
scope, strongest support/contradiction and surviving alternative. Compare:
(a) this concrete full-body-plus-gate B or a precisely justified correction within
the node's authority; (b) ending the instantiated comparison; (c) the legal fourth
unchanged B as a decision-value alternative. If continuing, give only the concise
card-ready question/comparator/observable/MEI/exposure/budget/interpretation and
working prediction needed for that one next object. If ending, state what stops
and what remains untested; do not turn it into broad lifecycle or hold-credit
failure. Distinguish any RECAST explicitly so its existing policy can be applied.
Do not add stronger-class prerequisites or silently except a current rule.

Machine-generated consultation exposure is in
[PREPARATION_FACTS](VSPC1_NATIVE_HOLD_VALUE_P79_PREPARATION_FACTS_20260909.json):
new invocations/native steps/Adam/model/environment construction all **zero**;
existing B12 movement/counts are historical measured exposure, not a new-candidate
result. No new prediction is frozen or scoreable; owner prediction is not taken.

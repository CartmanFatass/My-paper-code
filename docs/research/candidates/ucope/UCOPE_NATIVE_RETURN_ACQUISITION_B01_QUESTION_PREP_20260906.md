Claim under test: On the finite renewal host, a policy trained on sampled net return can learn when to buy information and earn more than the strongest immediate-commitment reference.
Binding MARL structure: **systems / information flow**. The question abstracts a coordinator paying to obtain otherwise unavailable observations before committing to a service period; this finite host does not itself establish a multi-agent partial-observability or non-stationarity result.

# UCOPE native-return acquisition — question preparation

**Status: PREPARED / DRAFT; prospective B/EXPLORE, not a frozen card.**
Prepared on 2026-09-06 from repository base `688cf2d3912d46c3f8c8b91ff12f13769e713561`
for Root's bounded question-preparation assignment. No object, implementation, invocation,
Pro request, recast or Portfolio disposition is selected here. New experiment exposure: **zero**.

## 1. Why this question is distinct and useful

[DIRECTION.md, current scientific position and exploration calibration](DIRECTION.md#current-scientific-position--2026-09-05)
retains PA-B paid-acquisition behaviour in 5/6 treatment policies versus 6/6 references.
[TW-B result, §§1, 6 and 11](UCOPE_THREE_WITNESS_HINGE_R01_RESULT_EVIDENCE_20260904.md)
then records tail agreement in 6/6 versus 4/6, unchanged full competence in 3/6, and two additional
false-positive root probes, each losing 0.028562899. Its intervention used oracle-signed hinges;
fresh draws and a non-oracle-signed objective were not evaluated there.

The next proposed observation is whether a fresh learner can earn native value when acquisition
and duration receive credit from realized return, with no oracle action labels or fitted-root
Bellman targets. This is an outcome-informed new learning question, not a causal explanation of
TW-B. Its inputs exclude all retained policies, offset-2,000,000 rows, root projections and the
two-node numerical-locus output. The retained-policy root-residual family remains parked with
all its existing obligations intact.

A minimal real B answers this learnability question more directly than a root-solver diagnostic:
the diagnostic would characterize different retained policies under a different objective.
No exhaustive policy search, support census, historical replay or exact reconstruction is needed
by this proposed claim. This follows [evidence-spec §11.8.1–3, 6–7](../../specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md#118-exploration-and-publication-burden-calibration-2026-09-05).

## 2. Proposed learner and comparator

Use the eight contexts and unchanged native cost/return law in
[PA-B01 card, §§3–4](UCOPE_PAID_ACQUISITION_B01_CARD_20260903.md). The episode starts before paying.
The coordinator sees the public context, chooses `IMMEDIATE(k=4)` or `PROBE`, pays the host's
actual probe cost if probing, receives only the legally revealed protected count, and then
chooses a period. That choice and the paid cost determine the native episode return.

- **Treatment `RETURN-ACTOR`:** a categorical root policy with logits per public context;
  an informed tail policy with one 32-unit tanh layer, taking the public context and revealed
  count and producing logits for periods `{2,4,6,8}`. Train both from scratch with Monte Carlo
  score-function policy gradients, FP32 Adam, learning rate 0.003, 1,024 updates of 256 episodes
  each, stratified to 32 episodes per context per update. Use the realized cost-inclusive
  episode return and a leave-one-out within-context batch mean as the action-independent
  baseline. Only visited actions receive score gradients; the tail receives no update from
  immediate-commitment episodes. No oracle-signed loss, critic, exact solve or auxiliary reward.
- **Comparator `IMMEDIATE-4`:** always commit immediately to period 4. PA-B01 §3 identifies this
  as the best immediate value at the initial belief in every context, 0.794. It receives no
  purchased count. The treatment shares this same immediate option, so this comparison tests
  the incremental value of learning to acquire and use information, not learning an already
  known immediate action. It is a fixed legal reference, not an independent trained arm.

For this new question, training and evaluation use the same period set `{2,4,6,8}`. The earlier
odd-to-even period transfer question is outside its scope. No COUNT/RAW or representation
advantage is claimed; such a claim would need an equal-information learned comparator.
Hidden modes, oracle probe signs and counterfactual unchosen returns are unavailable to the learner.

## 3. Primary estimand, minimum effect and reading

For each independently trained seed `s`, evaluate its **final checkpoint's modal actions** on
4,096 fresh episodes in each of the eight contexts, with matched exogenous draws for `IMMEDIATE-4`.
Fix ties to immediate at the root and then increasing period at the tail. The primary measurement is
`Delta_s = (1/8) sum_c mean_e [R_RETURN-ACTOR(s,c,e) - R_IMMEDIATE-4(s,c,e)]`.
The proposed two-seed summary is their arithmetic mean; publish both seed differences and all
eight context differences. Training seeds are the independent learning units; contexts and
evaluation episodes do not become additional training samples.

**MEI: +0.001 absolute mean native return.** The historical oracle's target gain is
`17149681/800000000`; uniform weighting gives only **0.00267963765625** over immediate commitment.
Thus 0.001 asks the learner to retain about 37% of this small available reference gain, with losses
elsewhere charged in full. This arithmetic uses existing evidence, not a new oracle computation.
There is **no tuned generic current-host headroom record**; the historical oracle/reference gap
is a diagnostic bound for this host and action set, not that missing tuned-baseline record.

Above the MEI, recommend a bounded independent-seed follow-up of this comparison, retaining any
adverse seed or context. Inside `[-0.001,+0.001]`, report no material mean signal at this budget;
seed-specific gains remain local and select no automatic extra invocation. Below -0.001, recommend
no unchanged extension of this learner. These are draft reading branches, not decisions already
taken. Report uncertainty from finite evaluation separately; two training instances cannot support
stable population superiority. A positive sampled gain does not establish its cause, complete
competence, held-out-period transfer or a generic MARL benefit.

Minimum useful B evidence is one complete real training instance and a trustworthy sampled native
comparison over all eight contexts. The proposed batch contains two independent instances; keep
both outcomes and any incomplete exposure, with no stop-on-positive or requirement that both improve.
Probe frequencies, per-context return and paid-cost components describe acquisition mistakes;
oracle agreement and competence may be descriptive but do not suppress the primary return.

## 4. Prospective binding and work proposal

The eventual card would bind seeds `6301` and `6302`, with separate named training and evaluation
RNG streams and fresh environment draws; seed labels are not reused retained-policy identities.
It would bind the sampler, public-context/count availability, native return/time/cost mapping,
optimizer and initialization settings, RNG mapping, source SHA and final-checkpoint selection
before question-relevant output. Code entry points were deliberately not inspected in this
preparation; the exact sampler interface and complete-invocation time are unverified execution
facts for the next bounded CM assignment, not evidence for or against the hypothesis.

Known work, computed with Python from the proposed configuration:

| Quantity | Proposed total |
| --- | ---: |
| Fresh trained policies | 1 learner arm × 2 independent seeds |
| Training episodes | 2 × 1,024 × 256 = 524,288 |
| Optimizer steps | 2 × 1,024 = 2,048 |
| Evaluation episodes, including fixed reference | 2 seeds × 2 policies × 8 contexts × 4,096 = 131,072 |
| Total sampled episodes | 655,360 |
| Complete invocation cap, including initialization, learning, both evaluations and publication | 600 s per training seed; 1,200 s summed maximum |

These are **proposed bounds, not allocated budget**. Primitive transitions depend on the host's
actual episode path and must be counted; optimizer steps above are joint root/tail updates.
Dominant algorithm work is sampled episodes plus one batched backward pass per update, followed
by the two fixed-policy evaluations. There are no nested candidate searches, tuning arms,
cross-validation folds, diagnostic trajectories or validation reruns in these totals.
Unit time is unknown: the TW-B 62.506/62.641 s charged arm timings concern another learner and are
not a throughput estimate for this actor. No extra cost experiment is requested.

The proposed object is host portable, FP32 CPU with one compute thread, on the configured
`remote_first` route; neither Windows nor a specific processor is part of its estimand.
Existing detached-launch and resource-admission tools would be reused. It needs **no new
ENGINEERING_SCOPE_SPEC §4 machinery**. One focused check of the changed information/reward path
and primary publication is the proposed added validation; no complete-array or solver-equality
contract transfers from the parked object.

## 5. Evidence check, risks and next action

Local retrieval asked whether costly information should be optimized jointly with downstream
return rather than credited for predictive coverage alone. My-lib's current `coverage` command
reported only `synthetic-core` (2 fixture papers); those were excluded. The Inst-sci formal
`llm-index/catalog.v2.jsonl` snapshot contained 190 real-corpus index rows. Its cost/communication
search located DACOM; the relevant source was read, rather than treating the index match as evidence.

Yuan et al., **DACOM**, AAAI 2023, DOI `10.1609/aaai.v37i10.26389`, pp. 3–5,
source `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0006.json`, elements 123–124, 186, 188,
190–192 and 213–215, models delay in action value and learns waiting decisions alongside actions.
[Publisher source](https://ojs.aaai.org/index.php/AAAI/article/view/26389).
Metadata verifies the title and a publisher-open PDF with no listed quality warning. This changes
the proposed endpoint to full cost-inclusive return and makes the immediate-action alternative
explicit. **DM inference:** it motivates this finite-host test; it does not establish the proposed
Monte Carlo learner, its sample efficiency or novelty. DACOM itself uses a learned critic.

The main risks are the small available gain, noisy policy-gradient credit, early cessation of
probing starving the tail learner, and stochastic-training/modal-evaluation mismatch. A negative
result would bound this learner and budget; it would not establish which risk caused it or undo
PA-B/TW-B. The public information and realized-return sampler still need a source-level binding.

**Return: PREPARED at question level; execution readiness unassessed.** The next DM action is
to select or revise this separate paid-acquisition question under the existing decision ladder
and, if selected, freeze its card and give CM the bounded implementation assignment. Root owns
integration and routing; Portfolio retains lifecycle and sequencing. No owner approval gate is
introduced. The owner-item review command returned no unapplied instructions at preparation.
No frozen card, new experiment result or delegated run selection was created by this memo.

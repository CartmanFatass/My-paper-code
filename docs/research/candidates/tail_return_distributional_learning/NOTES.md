# Tail Return Distributional Learning

## 2026-09-29 - Changed Scalar Comparator, Fixed Three-Pair Study

### Question And Inherited Evidence

New native Codex DM `/root/dm_tail_learning`, assigned by Root, owns this
changed-comparator successor on shared main. This is not a restoration of the
archived TRDL session. The old `DIRECTION.md`, B01/B02 cards, outputs, verdicts,
and unstarted B02 Pro remain unchanged evidence. Root is publishing the active
ownership and complete selection review; no result launch precedes that row.

Question: on the native decentralized UAV service host, does factual full-return
distribution fitting improve finite lower-tail learning beyond directly fitting
the actor's scalar tail score when both packages use the current empirical eta?
The intended contribution is empirical understanding of finite critic/learning
packages. This is not a planner-superiority, distributional-necessity, unbiased
gradient, safety, individual-user fairness, or cross-host claim.

The original [B01 card](TRDL_B01_SCIENCE_CARD_20260914.md),
[B01 reading](TRDL_B01_RESULT_EVIDENCE_20260914.md), and
[B02 reading](TRDL_B02_RESULT_EVIDENCE_20260914.md) retain Q32-SCALAR own-tail
contrasts +0.0345634681 and -0.0024197226, with mean contrasts +0.0516480640
and -0.0006779595. Both signs matter. The independent selection review reported
direct rereading of both raw ZIPs: each original arm completed 512 train and
256 final episodes and 128 updates, nonzero actor/critic gradients, no active
joint clipping, and three strictly negative W values per 16-episode batch.
These are historical learning observations, not replications of S_eta.

The constructive conjecture is that fitting factual return quantiles supplies
useful finite structure across returns. The simpler alternative is that a scalar
conditional score critic supplied current eta is sufficient in this finite
recipe. Zero W targets constrain that fit; they are informative data. The first
study is a complete direct learning comparison, with no mandatory pilot, toy
pass, cross-fitting arm, theorem, or additional diagnostic gate.

### Structural Background And Decision Interface

Read current published main `d1a992c91af313e332ed4e03bac8e05f936e6ca5`,
[learning background](../../RESEARCH.md#4-学习理论表示能力和有限训练结果处在不同层面)
and [empirical/statistical background](../../RESEARCH.md#6-实证研究是在具体条件下缩小解释空间).
Their concrete effects here are to test a finite learning package rather than
deduce benefit from a richer representation; use the trained scalar score
comparator for this learning question; separate training replication from the
256 nested evaluation worlds; preserve native service components and adverse
worlds alongside J; and avoid giving proxy fitting differences a causal reading.

Source trace: `trdl_b01/learner.py` collects the existing 137-vector training
context, empirical eta at the fourth order statistic of 16 returns, whole-score
advantages, fixed replay, and own-arm 64-of-256 endpoint.
`ucope/uav_motion_prefix_b01/environment.py:make_real` binds five UAVs, 50 static
uniform users, H256, 1000 m area, height 50-150, speed 30, free-space vectorized
channels, no shadowing/FDMA/paper reward. All five agents act every primitive tick.
Their shared DENSE/GRU64 actor receives 108 private features, emits three
tanh-Gaussian velocity commands, and has no eta, return, quantile, or central
state input. Partner behavior changes through shared policy learning. There is
no duration choice, role label, communication, eligibility gate, or new control
right. The unchanged host maps all velocity coordinates through its normal
physical clipping and scaling; no method-specific fallback or action alias is
added.

Native reward is the sum of the five reward entries, equal to
0.7 * served_users / 50 + 0.3 * average normalized SINR quality. Full-episode
J is the double-precision ordered reward sum divided by 256. Logging reads
the host's factual connections and SINR, verifies the reward decomposition,
and never changes observations, rewards, or transitions.

### Prospective Comparison And Exposure

Study `b03_eta`: exactly S_eta versus unchanged Q32 at fresh independent training
masters 9621, 9622, 9623. Six fits, executed sequentially in one detached batch.
Each fit has 512 training episodes, 32 collections of 16 episodes, four joint
Adam epochs per collection (128 updates), and 256 sole-final stochastic
evaluation episodes, all H256. No intermediate evaluation, selected checkpoint,
tuning, extra seed, automatic retry, or automatic batch extension.

S_eta appends the detached current eta to each already-collected 137-dimensional
training context. A scalar 138->128->128->1 tanh critic fits
W=(G-eta) * 1[G<=eta] / .25 by MSE, including zeros, and predicts the pre-update
baseline using the same appended eta. Q32 retains its 137->128->128->32 critic,
factual full-G pinball target, midpoint quantiles, and current-eta transform of
its quantile predictions. Eta, W, baseline, and actor advantages are detached and
frozen before all four epochs. The actor surrogate, private recurrent inputs,
optimizer recipe, clipping, FP32 CPU semantics, collection order, and final
evaluation contract remain unchanged.

Eta is an empirical statistic of the same own-batch returns. Consequently,
E[W|c,eta] and transforming an estimate of G|c are not automatically the same
ideal estimand. This package comparison does not identify eta causality, pure
representation, or the reason for B01. S_eta has an ordinary seeded 138-wide
first layer; this added input changes scalar first-layer initialization and
parameter count, another disclosed package difference. Actors remain paired
at initialization; Q32's model and stream bindings match its inherited recipe.

For master m, base=100000*m. Actor template/branch seeds: base+11/+12; critic
trunk base+13, S_eta head base+14, Q32 head base+15. Common training reset
panel: base+1000+e, e=0..511; common final reset panel: base+2000+e, e=0..255.
Private continuing action RNG: S_eta base+21, Q32 base+22. Private final
episode action RNG: S_eta base+3000+e, Q32 base+6000+e. The explicit S_eta
mapping must never fall through the historical 'not SCALAR means Q32' branch.
Fixed fit order is master ascending, S_eta then Q32. Tests use unrelated seeds
and synthetic fixtures only.

Total planned scientific work: 786432 train + 393216 evaluation = 1179648
native team steps, 4608 scored episodes, 768 joint Adam calls, plus six
unscored constructor resets. Q32's three fits evaluate 50331648 pinball terms.
There is no simulation search, counterfactual branching, replay target
cross-product, or preliminary result-producing run. Historical B01/B02 pair
process costs were 395.64 and 537.19 seconds; six fits therefore extrapolate
to about 20-27 summed process-minutes. This is not a current measurement.
Added logging, import/build, node contention, reading, and publication remain
visible costs; implementation/review preparation estimate 4-8 hours is conjectural.

Prefer configured wsl_4070, CPU FP32, one Torch/BLAS thread, with actual-node
admission and exact published source snapshot. Root is reconciling its canonical
policy because HTTPS fetch stalled. A suitable local fallback requires a
recorded concrete reason before launch. No operation has been accepted yet.

### Prospective Reading And Stop

For each final policy compute its own lowest-64-of-256 J mean. For each master
report Delta_tail = L_Q32 - L_S_eta and Delta_mean = mean_Q32 - mean_S_eta.
Never sort paired differences or pool returns from different trained policies
for the primary. Keep all six per-world native J/service/quality readings,
paired-world descriptive losses, complete training/update streams, actual
counts, displacement from initialization, and gradient/clipping diagnostics.

The three training pairs are the independent uncertainty units. Report every
pair contrast, their mean, standard deviation, and a descriptive small-n
t interval (df=2, assumptions stated). Nested world uncertainty is a different
quantity; it does not increase training n. This first S_eta study is exploration,
not statistical confirmation or an equivalence test.

Prospective useful recurrence reading: all three tail contrasts positive and
their average above +.01 supports a recurring finite Q32 tail signal worth
considering further; the mirror pattern below -.01 supports S_eta. The .01
scale retains the native task interpretation of 2.56 summed reward units over
H256, about .714 mean connected-user equivalents if quality were fixed. It is
an investment reading, not a significance, equivalence, or safety threshold.
Mixed signs or smaller differences weaken a stable package preference and may
favor scalar simplicity while preserving uncertainty. Tail improvement with
mean or service harm is explicitly a tradeoff; it cannot become unqualified
adoption. A scalar win supports this comparator, not proof eta explains B01.
No outcome erases either historical sign or automatically buys another fit.

After full reading, obtain one independent scientific diagnosis covering the
new evidence and choice. Compare further replication, a concrete targeted
revision, and stopping for their knowledge value and cumulative cost. Return
any out-of-question pivot or material disagreement to Root. The broader
question remains distinct from this finite recipe's result. At this boundary
publish the result and owned standing, preserve required unique evidence, and
remove verified disposable source/scratch and redundant data with measured
allocated-byte reduction.

### L0 - Eta-Conditioned Scalar Successor

Deliver one runnable, fixed six-fit S_eta/Q32 comparison and compact reader,
reusing the immutable historical host/actor/optimizer helpers. Implementer owns
only `experiments/candidates/tail_return_distributional_learning/b03_eta/` and
`tests/experiments/candidates/tail_return_distributional_learning/b03_eta/`.
Entry `b03_eta/run.py` validates fixed bindings and calls `require_admission`
before output creation or scientific effects; it checks the supplied launch SHA
against admission. No production bypass switch. Old learner/study/runner/cards
must remain unchanged. DM owns this notebook, result interpretation, Git index,
commit/push, launch, collection, and RESEARCH publication.

Required checks: explicit S_eta scalar-head/MSE/RNG routing; paired actors and
unchanged Q32 path; post-collection detached eta used in the pre-update baseline
and all critic epochs; frozen W/baseline/advantages; nonzero actor and critic
updates on synthetic input; training/evaluation separation; factual native
reward components; exact masters/exposure; own-tail rather than tail-of-difference
aggregation; incomplete fits retain facts and prevent a complete batch verdict;
admission before scientific effects. Run focused existing/new synthetic tests,
then independent engineering review of numerical, recurrent, seed, native-metric,
and result-identity paths. No fit, native evaluation, test tuning on masters,
extra arm, or scope expansion from implementation. Stop on concrete semantic or
resource conflicts and return facts; do not repair by changing the science.

### Primary-Source Bridge And Scope

Read the actual local primary passages, located through each library's catalog:

- Wang et al., *A Reductions Approach to Risk-Sensitive Reinforcement Learning
  with Optimized Certainty Equivalents*, arXiv:2403.06323v2, section 2.1,
  PDF pp. 4-5, at
  `/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/icml-2025/pmlr-v267-wang25bl/arxiv-2403.06323.pdf`.
  The augmented state (s,b) uses b_next=b-r, and Theorem 2.1 relates an
  optimally chosen initial budget and risk-neutral augmented policy to optimal
  OCE under its MDP assumptions. This makes scalar augmentation a serious
  competing route; it does not prove that our same-batch-eta neural baseline,
  decentralized actor, or finite clipped surrogate is unbiased or optimal.
  The learned budget-aware control policy of that theorem is not our execution
  actor, which receives none of this training-only information.
- Shen et al., *RiskQ: Risk-sensitive Multi-Agent Reinforcement Learning Value
  Factorization*, MARL-0563, sections 4.1-4.3, PDF pp. 5-7, at
  `/home/fires/projects/Inst-sci/papers/MyLib/pdf/MARL-0563.pdf` (structured source
  `/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0563.json`).
  RIGM concerns consistency between joint risk-sensitive argmax and individual
  risk-sensitive argmax; the implementation models per-agent quantiles and
  uses their risk values to choose greedy actions. Our critic is a training-only
  action-independent baseline for a stochastic actor, with no quantile mixing
  or greedy risk action selection. Thus RiskQ motivates multi-agent risk
  learning broadly but supplies neither a mechanism proof nor an already
  matched comparator here.

These primary readings retain the scalar alternative and strengthen the
package-only interpretation. The eta comparator was already proposed in the
archived TRDL review; no claim that it or the broader idea is novel is made.

### Selection Review Read And Adopted

The complete [Oracle recommendation, independent scientific review, and Root
disposition](https://github.com/CartmanFatass/My-paper-code/blob/abf118395bcaf66d4ca1fca72f902c19b92519d4/docs/research/archive/2026-09-29/RESEARCH-oracle-reserve-selection.md)
have been read in full. This is the separate-context review assigned by Root,
not a review supplied by this DM's implementer. MATERIAL_DISSENT: no. Adopt its
explicit scalar mapping, detached postcollection eta, informative zero-target,
own-tail endpoint, three-training-pair uncertainty, and finite-package
interpretation corrections. The primary-source readings above independently
verify the two load-bearing literature mappings. Root also accepts the ordinary
seeded 138-input initialization and exploratory recurrence rule as disclosed.
No additional Pro consultation changes a presently unresolved selection
decision; the historical unstarted B02 Pro is not resumed.

The source-published active row assigns lead `Codex DM (native child)` and this
native child address. The first published edit still contained the old reserve
row as well; the duplication was reported through native parent communication
for the initial index edit to reconcile before admission. It authorizes no
duplicate process and changes none of the experiment's scientific exposure.

### Engineering Preparation

The bounded registered Implementer added only the new b03_eta source and tests,
with no native call, staging, commit, or result launch. Its first handback passed
22 combined successor and historical synthetic tests in 3.24 seconds. DM source
review corrected launcher-directory handling (native launch records exist before
the runner), structured JSON parsing, compact adverse-world publication, and
process-high-water RSS labeling. The independent registered engineering Reviewer
repeated the suites: 22 passed in 4.72 seconds. Its current review identified
raw-row arm/seed validation and required learner-movement acceptance gaps;
these are being fixed before source acceptance. Neither test pass nor a source
review is a native result.

### Engineering Acceptance And Prospective Node Fallback

The independent engineering Reviewer's final two findings were:

1. Raw same-master S_eta/Q32 episode and update streams could be swapped without
   the reader noticing, because shared reset panels and update order still
   matched. Its synthetic reproduction reversed the reported recurring sign.
2. Required learner displacement accounting could fail after fit status became
   complete, and the reader accepted missing movement evidence.

Both have been repaired and independently rechecked. Every raw episode/update
row is checked for the expected arm and master. Missing or nonfinite movement
metrics block the dependent learning verdict while preserving endpoints, counts,
checkpoints, and raw facts. Finite zero displacement remains a valid measured
outcome, not an added positive-learning gate. Closeout errors remain separate.
The combined repair suite passed 24 tests in 3.44 seconds; after the explicit
zero-displacement correction, the Implementer's focused suite passed 10 tests
in 2.25 seconds and the Reviewer independently passed the same 10 in 2.04
seconds. It reported both findings resolved and no remaining material finding
in the bounded review. DM read the final source and tests and accepts this
implementation. Historical learner/study/runner files have no diff. The
remaining unmeasured boundary is the actual native run, not permission to add
a scientific smoke/pilot. Timing fields now distinguish entry, batch,
final-reader, and final-write boundaries and include user/system CPU.

Prospective execution choice: use configured `local_linux` for the one fixed
six-fit batch. The preferred `wsl_4070` is reachable: SSH hostname returned
`LAPTOP-U9TDKC8A`; its canonical origin/main was `570fd45646` at the probe.
However, this DM's read-only `timeout 20s git -C /home/wu/projects/HMASD
ls-remote origin refs/heads/main` over SSH exited 124 with no result. Root
independently reported the same failing published-control query after object
transfer while reconciling G0. Thus the remote cannot currently establish the
fresh published authority required by the launcher. No remote experiment or
duplicate scientific attempt was started. This concrete authority-network
failure activates the already permitted local fallback; it does not bypass
admission, change reward/actor/exposure/RNG/dtype, or migrate accepted work.
Local CPU FP32/thread1 will be checked and admitted at launch using the
configured scientific interpreter. Cross-host bit equality is not claimed.

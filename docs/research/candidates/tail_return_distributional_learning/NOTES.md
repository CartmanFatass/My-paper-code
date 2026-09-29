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

### Accepted Batch And Observation

Exact inputs published at `ccd96d4c868f800c8cc9827e799bc376aa17c990`.
Root removed the superseded reserve duplicate in `10e1902a6`; the active state
and `Codex DM (native child)` lead were unambiguous at admission. The fixed
`b03_eta_20260929_a01` batch was accepted at 15:08 UTC; all native identities,
source/output bindings, command and authority observation are in the
[launch manifest](../../../../runs/tail_return_distributional_learning/b03_eta_20260929_a01/launch-manifest.json).
The actual-node [preflight](../../../../runs/tail_return_distributional_learning/b03_eta_20260929_a01/admission-preflight.json)
recorded 9372807168 available physical/effective bytes against the 4294967296
floor. Six fits are planned; started/completed counts come from the output,
not from supervisor acceptance.

`tools/hmasd_wait.py` was armed on this same launch handle, generation 1,
window 1500 seconds. First drain observed consistent accepted/running
supervisor and runner identities. The observer belongs to native child runtime
`01a0eda1-4db6-78b1-9ead-47ec6aa792ff`; private request is
`temp/directions/tail_return_distributional_learning/b03_eta_wait.json`.
This child stays active for deterministic waiting, same-handle drain/rearm,
collection, and reading. No fallback launch or restart follows an observation
timeout. Current state is technically running, with no scientific result yet.

Observer checkpoint, about 15:33 UTC: generation 1 reported consistent running
identities, zero probe errors, no terminal witness. The native App queue rejected
its wake (`-32600`, unloaded spawned sub-agent); the deterministic foreground
wait on this child's observer event returned normally, so no replacement or
App rerouting was needed. Drained and consumed that checkpoint, then rearmed
generation 2 on the identical accepted handle. Progress-only read showed three
completed fits and master 9622 Q32 at training batch 20 (336/512 train episodes,
84 updates), with empty stderr. No endpoint selection or partial scientific
reading was used. The historical 20-27 process-minute extrapolation is slow
for this local invocation; based on completed work and current progress,
revise the ordinary total runtime estimate to about 40-45 minutes. Exposure,
endpoint, order, source, and stopping semantics remain fixed.

### Complete B03 Result - Scalar Tail Signal With Training Uncertainty

The same accepted operation exited 0 at 15:54:48 UTC on 2026-09-29, with a
valid native `process-exit.json`, both process identities absent, consistent
manifest/status/claim records, and empty stderr. Observer generation 2 delivered
READY locally at 15:54:51 with zero probe errors. Its App wake again failed
with the documented native-child -32600 limitation; the active deterministic
foreground event wait returned. The READY event was consumed on the same
handle, generation 3 was stopped, and no scientific restart or new attempt
occurred. The [complete summary](../../../../runs/tail_return_distributional_learning/b03_eta_20260929_a01/summary.json)
and [fixed configuration transcription](../../../../runs/tail_return_distributional_learning/b03_eta_20260929_a01/config.json)
bind the output to the published inputs. The transcription records existing
input facts after collection; it is not a revised prospective plan.

All six fits completed. Direct recorded-byte audit read all 4608 episode rows,
768 update rows, 192 frozen-batch records and six checkpoints. It checked every
arm/master/reset/phase/order/H binding, complete update/epoch sequences, native
reward sums, FP32 fourth-order eta and W statistics, final vectors, checkpoint
source/identity/hash/finite dtype/parameter counts/final norms, and the own-tail
reductions independently of the batch reader. Native component reconstruction
agreed within 3.61e-16 in J. There were exactly 786432 training and 393216 final
evaluation team steps, 3072 training and 1536 evaluation episodes, 768 joint
Adam updates, six unscored constructor resets, and 5898240 velocity decisions.
No missing fit, skipped world, intermediate evaluation or selected checkpoint
was substituted. Q32's three fits used the planned 50331648 pinball terms.

| Master | S_eta own tail | Q32 own tail | Q32-S_eta tail | S_eta mean J | Q32 mean J | Q32-S_eta mean J |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 9621 | .094959485 | .090800605 | -.004158880 | .153743459 | .155360900 | +.001617442 |
| 9622 | .114940223 | .109624196 | -.005316026 | .177748130 | .172296918 | -.005451212 |
| 9623 | .134312821 | .108495599 | -.025817222 | .200968613 | .167798171 | -.033170441 |

Three-pair tail contrast mean is -.0117640427, sample SD .0121841551,
descriptive t95(df=2) [-.0420311620,+.0185030765]. Mean-J contrast is
-.0123347372, SD .0183871256, t95 [-.0580108894,+.0333414150]. These are
training-pair intervals under approximate normality, not world-resampled
confidence or confirmation. The prospective mirror rule labels this
`S_ETA_RECURRING`: all three own-tail differences favor scalar and their mean
exceeds .01 in magnitude. The first two differences are small; removing 9623
leaves -.0047374530. This sensitivity is descriptive, not a replacement endpoint
or a reason to exclude 9623. No pooled-mixture or tail-of-differences was used.

| Master | S_eta / Q32 served users per tick | Q32-S_eta served | S_eta / Q32 quality | Q32-S_eta quality | J worlds worse for Q32 / S_eta |
| --- | --- | ---: | --- | ---: | --- |
| 9621 | 9.170395 / 9.171509 | +.001114 | .084526 / .089866 | +.005339 | 127 / 129 |
| 9622 | 10.582047 / 10.252075 | -.329971 | .098665 / .095893 | -.002772 | 134 / 122 |
| 9623 | 12.098602 / 9.925812 | -2.172791 | .105294 / .096123 | -.009171 | 182 / 74 |

All counts are out of each paired 256-world final panel, with no J ties. The
mean-J advantages in pairs 9622/9623 include both service and quality; 9621 is a
tail-versus-mean/quality tradeoff, with nearly identical mean service. Q32's
worst J world differences are -.128704818 (9621/e28), -.156228318 (9622/e101),
and -.166914819 (9623/e94). S_eta's worst losses, expressed as positive Q32-S_eta,
are +.167808023 (9621/e242), +.142426283 (9622/e10), +.112935035 (9623/e75).
Service losses occur in 127/137/176 worlds for Q32 and 129/119/80 for S_eta;
quality losses occur in 103/139/173 for Q32 and 153/117/83 for S_eta. The compact
summary lists every adverse-Q32 world, while both complete raw streams preserve
all scalar losses too. These are realized stochastic-policy/world comparisons,
not paired common-action-noise counterfactuals or user-fairness claims.

All actor/critic gradient norms were finite and nonzero. Actor parameter
displacements (S_eta/Q32) were .911990/.891260, 1.103505/.887085,
1.011165/.910893; critic displacements .562281/1.150257, .624731/1.173266,
.527899/1.158277. This verifies parameter learning, not improved performance
relative to an unmeasured initial-policy evaluation. All 192 batches had three
strictly negative W targets and thirteen zeros, including the threshold row;
zeros constrain scalar fitting. Joint norm clipping activated only for S_eta
9621 update 1, norm .579327762; the other 767 updates were unclipped. Unlike the
old B01/B02 observations, this new scalar package has one realized clipping
event. It is an optimization detail, not an identified explanation for the
tail pattern. Scalar and quantile losses have different targets/scales and
their magnitudes are not evidence of superior baseline accuracy.

Actual runner wall through final reader and before its last summary write was
2804.384954 seconds (46.740 minutes), versus the historical 20-27 minute
extrapolation and revised 40-45 minute progress estimate. Batch wall after
imports/admission was 2802.797789 seconds; runner user/system CPU was
2647.183965/28.743978 seconds (2675.927943 total), and process-high-water RSS
494563328 bytes (about .461 GiB). Sequential fit walls were
304.070/372.701/569.896/512.974/492.326/550.602 seconds in the fixed order.
These are local invocation measurements, not a controlled S_eta/Q32 speed
comparison or proof of a contention cause. The independent recorded-byte audit
took 2.70 seconds and added zero native exposure. Engineering/review/test costs
above are additional; preparation wall time was not instrumented, so the
4-8 hour conjecture is not an actual measurement and unmeasured time is not zero.
Independent scientific reading/publication/cleanup are additional work too.

The durable unique bulk is the 24 files under this run's `raw/` directory on
configured `local_linux` at `/home/fires/hmasd-wsl/runs/tail_return_distributional_learning/b03_eta_20260929_a01/raw/`.
They contain all episode/update streams, six final checkpoints and six compact
fit summaries: 3964148 logical bytes, 4059136 allocated file bytes at reading.
The SHA256 of concatenated sorted records `file_sha256 + "  " + POSIX_relative_path
+ "\n"` (relative to `raw/`) is
`390f84ec1cd35c7d19895f740bd0cc67dc2bf59cc2670d502273e17f8780d88c`.
Batch summary SHA256 is
`452be2a34c462c2e8a278755c5b0e4e7b9f5eb2fa4c5a455b83d792aad3b1491`.
All checkpoints and streams are retained in this durable main checkout, which
is not scheduled for retirement. Compact summaries/config/native records are
published; no new ZIP, retention copy, or whole-tree backup is made.

This complete observation weakens the specific expectation that factual
distribution fitting adds recurring lower-tail value beyond the eta-conditioned
scalar package at this finite exposure. It strengthens S_eta as a credible
ordinary scalar alternative within the tested contract. It does not establish a
stable population ranking, distributional redundancy, eta as the cause of B01,
or equality of ideal estimands. The historical B01 positive and B02 adverse
Q32-SCALAR results remain separate and unchanged. Independent scientific
diagnosis of this evidence and the next investment is in progress; no extra
fit or automatic extension has been selected.

### Independent Scientific Reading And Investment Decision

Registered ResearchCritic `/root/dm_tail_learning/eta_result_scientific_review`
worked read-only in a separate context (`fork_turns=none`). It received the
question, fixed contract, original B01/B02 sources/raw ZIPs and all B03 outputs.
It reconstructed the data before reading the full Oracle answer and before
receiving this DM's tentative interpretation. The prospective notebook did
expose the original conjecture and selection-review summary; no DM/Root
conversation was inherited. The completed review reports **MATERIAL_DISSENT:
no**, recommending conditional scalar retention and stopping this fixed recipe.

The Reviewer independently checked all B03 episode/update streams, identities,
reset schedules, horizons, FP32 eta/W, own-tail endpoints, native components,
gradients and clipping; it matched six checkpoint hashes and source files against
the accepted SHA and launcher snapshot, and independently reduced both old raw
archives. It did not deserialize checkpoints, recompute displacement, rerun
policies, or inspect unavailable full action/state trajectories. The DM's
separate checkpoint audit above covers finite tensors/counts/final norms; neither
audit is a new rollout. The review reproduced every pair contrast, scalar
recurrence and all tradeoffs. It emphasized that 9623 supplies about 73% of the
total tail contrast: recurring sign is stronger than a stable material magnitude.

Its strongest simpler explanation is that directly fitting the required scalar
score is effective enough under this finite exposure, with initialization,
fitting dynamics, private trajectories and shared-policy co-adaptation producing
variable effects. Technical failure, missing updates and universal clipping are
not viable accounts of this completed batch. Statistical dependence on the same
returns survives eta detachment, so current-eta conditioning, input-width/init,
target/loss and ideal conditional-object differences remain package distinctions,
not separately identified causes. A scalar win cannot explain B01 retroactively.
The constructive positive is the recurring scalar tail sign and simultaneous
mean/service/quality advantages in two pairs. Preserve that ordinary learned
comparator, all scalar losses, and both original Q32-SCALAR signs; do not call it
a tuned task optimum, selected deployment checkpoint, distributional redundancy,
or resolution of broader UAV control opportunity.

The Reviewer compared the next investments explicitly. Stopping is justified
because this exploratory comparison removes preferential investment in unchanged
Q32 without needing a precise population ranking or an identified repair.
An unchanged fresh three-pair replication would cost six fits, 1179648 native
steps, and roughly the observed 47-minute runner wall as a planning reference,
plus uncertain support/contention costs. It is worthwhile when recurrence or
precision changes a named scientific conclusion or downstream choice; another
three pairs does not guarantee adequate precision. Recurring scalar benefits
would strengthen retention, small/mixed effects weaken a material ranking, and
recurring Q32 benefits reopen package selection. An eta-visible versus eta-blinded
scalar comparison using the same 138-input initialization could test finite
conditioning value, with native improvement rather than proxy fitting error as
the relevant consequence; it still would not explain B01. No identified current
decision would change enough to buy that attribution study.

DM accepts the review and ends new investment in this fixed Q32/S_eta recipe.
Retain S_eta as the preferred *finite comparison reference*, both implementations,
the pure reader and regression checks; retain all six policy assets and full
positive/adverse records. This is an investment preference, not a confirmed
population-superiority or deployment-adoption claim. No zero-clipping repair,
eta ablation, additional seed, longer fit, model module or new Pro was selected.
The direction becomes `reserve`, with no producer, unread result, approval wait
or selected successor. The broader factual-distribution learning question remains
open. A concrete re-entry condition is a named need to choose the default critic
for this contract, or a new finite-learning prediction whose possible outcomes
change method selection. Re-entry need not prove that scalar methods lack
representational capacity. Any richer information, risk-query or training-resource
contract must give the competent scalar comparator that same addition and count
its full cost; cross-question changes return to Root for allocation.

Before this investment decision, refreshed published main to `07aed46dc` and
read the relevant learning/statistical background. Its distinction between
representation, finite optimization, and training-pair versus world uncertainty
continues to govern this result. Adjacent ordinary-control/history evidence does
not supply a planner comparison for this critic question; we neither claim such
superiority nor convert another direction's failure into a required repair here.
The directly reusable update is that a scalar target with current-threshold
conditioning is a serious finite risk-learning comparator, and zero scalar
targets are information, while same-batch thresholds limit ideal-estimand claims.
This useful scope correction will be added to shared learning background.

Cost correction found by the Reviewer and verified directly in both original
raw ZIP invocation-time records: B01 summed process walls are 395.64 seconds;
B02 summed walls are 538.42 seconds, whereas 537.19 is B02 user+system CPU.
The earlier notebook's wording mixed these timing bases. Across the selected
B01/B02/B03 learning studies, ten fits used 1966080 native steps and 1280 updates,
about 62.3 summed process-wall minutes with the recorded timing boundaries.
Their total is not ten S_eta replications and not an elapsed cross-host duration.
B03 alone used .7433 recorded runner CPU-hours. Preparation, independent reading,
publication and cleanup remain incompletely metered. No scientific follow-on
has been bought to consume the saved compute.

### Publication, Retention And Measured Cleanup

The complete reading, independent scientific disposition, fixed config, compact
batch/fit summaries and native admission/exit records were published to main at
`25af96ea0ed18be32f9cf91dbeb8992476a8f07f`. Useful S_eta/Q32 code and focused
tests were already published at input `ccd96d4c`. They remain the implemented
ordinary comparator and exact result reader, not an authorization to repeat this
batch. All old frozen cards/source/runs/verdicts remain unchanged.

Before cleanup, the science worker and supervisor had valid terminal identities,
the observer state was stopped with both checkpoint and READY consumed, and
the independent scientific reader had returned. No consumer needed this source
snapshot. The supported exact-target snapshot collector previewed it eligible,
then removed it with its normal accepted-operation checks and the read-only
`--sudo-process-scan`. No manual snapshot deletion, backup chain or new copy was
used. An initial forced-rm cache command was rejected by the tool without an
effect; exact `.pyc` deletion followed by empty-directory removal succeeded.
There is no outstanding cleanup-tool blocker.

Deleted targets and measured allocated bytes were:

| Target relative to `/home/fires/hmasd-wsl` | Allocated bytes removed |
| --- | ---: |
| `.git/hmasd-launch-sources/d609499b0c7042e99af15510f023c125` | 1641111552 |
| `experiments/candidates/tail_return_distributional_learning/b03_eta/__pycache__/` | 45056 |
| `tests/experiments/candidates/tail_return_distributional_learning/b03_eta/__pycache__/` | 53248 |
| `temp/directions/tail_return_distributional_learning/b03_eta_wait.json` and now-empty direction scratch directory | 8192 |

All targets are absent, their allocated usage is now zero, and net measured
reduction is **1641218048 bytes**. This is exact-target working-filesystem
reclamation, not a claim about concurrent whole-host free space or Git history.
The 24 raw evidence files remain at their one durable canonical path; the
post-cleanup aggregate SHA256 is still
`390f84ec1cd35c7d19895f740bd0cc67dc2bf59cc2670d502273e17f8780d88c`.
Required operation/observer recovery records, useful code/tests, compact results
and unique raw/checkpoints remain. No unused target or unread result remains
from this selected batch. Direction standing/routing and the directly affected
learning-background paragraph are published with this closure entry; substantive
return to Root carries the reserve state and conditional re-entry recommendation.

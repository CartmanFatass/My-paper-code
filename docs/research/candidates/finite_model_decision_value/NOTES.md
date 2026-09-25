# Finite model knowledge and decision value

Lead runtime: Codex DM (independent session). Native task:
`01a0d937-e2f7-7d03-982a-d16bf16385cc`, host `local`.
Authoring checkout: `/home/fires/.codex/worktrees/3839/hmasd-wsl`;
branch: `codex/finite-model-decision-value-sept25`.
Pro conversation: new Jev conversation; private address stays in local operation state.

## 2026-09-25 — Question ownership, inherited evidence and concrete first design

Owner-authorized independent assignment received through task creation. I directly own
the question, with one result-bearing study at a time; there is no intermediate DM.
The old C07 direction remains archived. Its positive NEAR result and fixed LONG reading
are inherited evidence, not operations to reopen. No result operation has been accepted.
FSD remains owner-paused and G33 frozen. No App messages to Root or other DMs are sent.

Started this branch from published main and refreshed to
`01a6f18f566a896b351cda0718acf005c9d1847c`; its RESEARCH row now records this direction
as exploring under the fixed lead above. Read the current constitution, direct-DM body,
scientific-tools and research-engineering. Root's initial registration is present;
actual result admission will still use fresh main/canonical controls and real node memory.

### Evidence and what it changes

The [structural background at the adopted revision](https://github.com/CartmanFatass/My-paper-code/blob/2e2becaae8d376908d74364dca7e4713bdcb4a2a/docs/research/RESEARCH.md#8-数学信息与博弈结构怎样帮助dm选择实验)
and current main sections 2, 6–8 change the comparison: parameter accuracy is not the
endpoint, and a nonlinear advantage only permits, rather than guarantees, a useful
decision difference. Distinguish a persistent physical parameter, fresh movement noise,
hidden peer state and an unknown partner policy. Here only the first and third are
uncertain; partner feedback/continuation is fixed and supplied. No new learner is needed
to answer this first planning question. This is a small cooperative host study in its own
right, not a positive-toy prerequisite or measured UAV transfer.

Read the complete C07 re-entry/closure interpretation in
`skill_information_refresh/NOTES.md` (2026-09-21 re-entry and owner-supplied review),
and `CLAIM_near_commit_c07.md`. C07 reports NEAR−AF +102 completed jobs across 1,280
fresh worlds, with 79 positive, 13 negative and 1,188 tied worlds. It uses a known .75
law, approximate physical belief and a fixed finite planner. LONG's bounded increment
does not establish global optimality. The old 138,555,584 model branch transitions and
about 26× NEAR/AF panel-time ratio are historical costs, not a new wall estimate or
an online-deadline measurement. Original run evidence stays at its original identities.

Read the Portfolio's complete C1 advice and its responsible Decision in
[`RESEARCH-question-led-programme-adopted.md`](https://github.com/CartmanFatass/My-paper-code/blob/01a6f18f566a896b351cda0718acf005c9d1847c/docs/research/archive/2026-09-24/RESEARCH-question-led-programme-adopted.md).
It motivates matched plug-in versus uncertainty-aware opportunity values, with cheap AF
and true-model knowledge reference. It does not choose our population, prior, data or
actual estimator and therefore does not replace the following targeted consultation.

Read VSP03's complete B11 interpretation and its B09 claim as inherited scope: independent
calibration already produced useful fitted rules; B11's three O_R0−O_full differences
were negative, negative and zero, while O_R0−R0 were positive. Better or differently
obtained parameter fits do not force a changed decision. This study will not claim
independent calibration as a contribution or pool C07/VSP as replication.

### Source boundary audit

A bounded read-only Scout mapped the retained source at
`3ca4cb1f83ea869e1efca852a099db31c52b0e2c`; DM read the decision-critical host,
filter and planning definitions at that same revision. No old experiment was executed.
The C06 original source is `45a1f534539032c021f5d44a7d78f4b503b0ba51`.

* `c01/host.py:Worlds.make` samples actual advances with probability .75, then
  `CrossingHost.step` consumes them for APPROACH with positive distance. Job distance
  law remains uniform 1..7; gates, conflicts and crossing duration are deterministic.
* `c06/belief.py:PhysicalBelief.update` separately uses .25/.75 transition weights for
  own and peer movement. `take_local` exposes own state, own sent history, received
  packet payload/time and quota, not peer truth or world futures. Packet and own-motion
  conditioning inform hidden state. This filter deliberately omits the likelihood of
  state-dependent peer sending/silence and is not an exact Bayesian posterior.
* `c06/planning.py:independent_model_worlds` separately uses .75 for fresh synthetic
  futures. Its paired roots share sampled hidden state and exogenous futures; future
  send continuation is ACTIVE_FIRST. NEAR includes the full commitment containing the
  next cache-sensitive receiver opportunity, bounded by 32 ticks and the H96 endpoint.
* `c01/host.py:project` uses `floor(.75*age)`, and `choose_route` divides arrival
  distances by .75. These are deterministic constants of the receiver/controller.
  Keeping that receiver fixed means retaining these constants in both real and model
  rollouts even when the physical movement law changes. They are public nominal policy
  constants, not access to each task's hidden true parameter. Updating them with an
  estimator would change the receiver and answer a different package question.

The proposed adaptation therefore changes actual movement, physical-law inference and
synthetic movement together, while preserving the receiver and channel. A true-law
filter under an unknown-law label is explicitly excluded. The joint filter must retain
parameter/state dependence and packet likelihood mass across parameter hypotheses,
not normalize each conditional filter and silently discard that evidence.

### Mathematical bridge and limits

For a fixed lawful history, common actions and continuation, the simple bridge compares
`Delta(h, E[theta | D,h])` with `E[Delta(h,theta) | D,h]`. If this same conditional
advantage is affine in theta, equality follows. Curvature permits a difference but
does not establish an action flip, an advantage under finite Monte Carlo, or better
full-horizon return under subsequent replanning.

Primary passages checked on 2026-09-25:

* [Guez, Silver and Dayan (2012), section 3.1–3.2](https://proceedings.nips.cc/paper_files/paper/2012/file/35051070e572e47d2c26c241ab88307f-Paper.pdf)
  sample a model at a search root and keep it across that simulation. We borrow this
  persistence idea; we do not implement BAMCP's search tree or inherit its convergence
  result. Resampling an independent physical parameter at every future tick would
  represent a different environment.
* [Ross, Chaib-draa and Pineau (2007), sections 3–4](https://papers.nips.cc/paper_files/paper/2007/file/3b3dbaf68507998acd6a5a5254ab2d76-Paper.pdf)
  represent uncertainty jointly over physical state and model statistics and discuss
  approximate belief tracking. This supports treating the two uncertainties together;
  it supplies neither an accurate posterior for our omitted send likelihood nor a
  cooperative-controller performance guarantee.

For our proposed shared-filter comparator, let `mu(x,theta | D,h)` be the approximate
joint physical belief and `b(x)` its state marginal. The two root targets are

    U = E_mu[Delta(x,theta)]
    P = E_b[Delta(x,theta_bar)],   theta_bar = E_mu[theta].

This collapses both parameter dispersion and its association with hidden state. Even
if `Delta(x,theta)=a(x)+c(x)*theta`, U−P can be `Cov_mu(c(x),theta)`; the simpler
affinity equality requires its stated common conditional object. Thus a U−P gain will
not by itself identify Jensen curvature, state correlation or optimal exploration.
This is a DM derivation for choosing the comparison, not an already measured mechanism.
Two asynchronous agents replan, collide and exchange selected observations; their
closed-loop coupling and the ignored send-likelihood remain outside the single-agent
guarantees. Necessary information/RNG/numerical checks remain, but no exact solution,
positive toy or exhaustive same-root census is required.

### Proposed B01: a finite, well-specified population comparison

This is a concrete proposal for Pro criticism, not an accepted/frozen result batch.

**Population and unknown.** Use the retained two-robot CrossingHost H96, periods12/16,
TDMA quota/delay/forced-send rules, native completed jobs and fixed nominal-.75 receiver.
Each new deployment context draws one persistent shared movement probability uniformly
from `{.35, .55, .75, .95}`. It stays constant for both robots throughout calibration
and evaluation; conditional movement trials are independent Bernoulli and jobs retain
their original independent law. The support and uniform prior are supplied to all
estimators; the realized probability is private to environment generation and the
explicit knowledge-reference arm. These four values are chosen before scores to span
moderately unreliable to reliable movement; there is no empirical deployment-client
or robustness claim. This changes the population rather than relearning a universal .75.

**Legal finite data.** Before each deployment, run a simulated controlled movement
calibration: one robot starts at distance33 in an unobstructed corridor and makes32
advance attempts using the same unknown physical law. Consecutive own distances yield
32 observed zero/one advances without saturation, hidden labels, peer truth or future
evaluation arrays. The calibration record is a public predeployment input to both
robots; this permission is explicit and common to all arms, not extra online bandwidth.
Use its first4 trials for the small-data comparison and all32 for the larger-data
comparison. The k4 code receives only its prefix. `q(theta | D_k)` is the normalized
four-point prior times `theta^successes*(1-theta)^failures`. No hyperparameter tuning
or learned prior. Calibration process noise and evaluation/model RNG streams are separate.

**Shared inference and comparator.** P and U both initialize the same joint finite
physical filter over 4 parameter values ×22 peer physical states, separately for each
robot. Each consecutive lawful observation updates this approximate joint belief;
online information rights are identical although histories can diverge under policies.
Retain C06's omission of peer-send/silence likelihood in both; label the belief approximate.
The P arm samples root peer states from the state marginal and uses the posterior mean
parameter for all forward dynamics. U samples `(theta, peer state)` jointly and retains
theta throughout each paired HOLD/SEND rollout. Both use32 paired root particles,
identical opportunity endpoint, AF continuation, threshold zero and AF on exact ties.
Use common addressed state/process uniforms where meaningful, with a separate parameter
sampling stream; no data-dependent draw consumption or actual-world future access.

This **posterior-mean forward NEAR** is the proposed primary plug-in control. Giving it
the same joint inference prevents a U advantage from merely reflecting a superior
upstream filter; it is stronger/more expensive than a minimal point-estimate-only
pipeline. We do not call it an estimator-cost reduction. The main question is whether
retaining uncertain dynamics in the opportunity estimate helps after the same inference.
A separate approximate point-filter baseline is possible, but not silently substituted
or purchased as an extra arm. Pro is asked to challenge this comparator choice directly.

**Arms and evaluation.** P4, U4, P32, U32, AF, and KNOW_P_NEAR. AF and KNOW_P_NEAR do not
use calibration, so evaluate each once on the same worlds and reuse the identical
reference reading for both data levels. KNOW_P_NEAR has the true persistent parameter
in its physical filter/rollout, still a partial-state approximate filter and finite
planner with the same fixed receiver; it is a knowledge reference, never a global upper.
Use256 independent deployment contexts, one H96 evaluation world each, paired across
all six policies and data doses. There is no PPO, policy fitting, checkpoint selection,
LONG arm, post-score extension or adaptive world/parameter selection.

**Question and predictions.** Primary exploratory estimand is mean completed jobs
`U4−P4` over the declared parameter/calibration/world/planner law. Retaining uncertainty
may change useful send ordering while a mean law can lose persistence or state
association. Tentative prediction: positive average U4−P4, with fewer decision
differences and less incremental value at k32 as parameter uncertainty contracts.
This prediction can fail because of finite-P32 variance, little relevant nonlinearity,
rapid online identification, approximate belief, fixed receiver or subsequent
replanning. Even a locally correct ranking need not improve the whole task. AF can
still be preferable once its much lower compute is considered.

Read all per-context absolute completions and differences, signs/ties, conflicts,
waits, packets and costs; include negative/tail examples and parameter-stratified
descriptions without converting selected subgroups into claims. Report ordinary paired
mean/SE intervals as exploratory, conditional on this model family/program; no new
confirmation or equivalence verdict. Context is the independent unit; robots, ticks,
particle branches and the nested k4/k32 doses are not additional n. Planned secondary
readings are U32−P32, their paired dose contrast and each policy versus AF/KNOW_P_NEAR.

For an intermediate reading, compare recorded P/U decisions only along their identical
actual common prefixes, including the first differing root and its posterior variance,
value estimates and actions. No extra counterfactual rollouts are bought for this.
After paths diverge, record values/actions but do not compare them as the same history.
Finite Monte Carlo and joint-state/parameter projection remain combined mechanisms.

**Complete prospective work.** 256 calibration trajectories ×32 =8,192 calibration
movement steps;512 distinct closed-form finite-support calibration fits (256 contexts
at each of two data sizes), shared initially by P/U;0 neural/policy fits or optimizer
updates. Evaluation is6×256=1,536 full episodes and147,456 real team ticks, plus the
8,192 one-robot calibration steps. Five planner arms mean1,280 planned episodes and
at most `1280*72*32*2*32 = 188,743,680` model branch transitions, plus synthetic draws,
model initialization and per-tick filtering. P/U filtering has88 support entries versus
22 for the known-parameter reference; count actual likelihood/support work and roots.
AF carries no unnecessary filter. Measure calibration/fitting/filter/planning/evaluation
wall components, full process wall/CPU/RSS, model branch counts and output sizes.
These integer counts are not measured wall times. Historical C07 timing is only an
order-of-work clue; engineering/review, data saving, waiting and readback cost are extra.

Prefer configured wsl_4070 for the result batch with bounded native threading and fresh
admission. Source recovery, implementation and independent numerical/RNG/information
review are required before launch. Preserve original source identities, use disposable
direction code, small correctness fixtures and native admission/observer. Bulk raw
calibration/decision/trajectory records go to durable recorded storage with hashes;
commit compact per-context results/config/status. No result-bearing profile/pilot has
been run and none is needed to decide whether the comparison is conceptually coherent.

## Pro question 2026-09-25 joint-belief-versus-mean-dynamics

Conversation: new (Jev private address remains local).

Question: Should I execute the concrete B01 comparison above using a shared approximate
joint physical filter followed by posterior-mean versus joint-sampled NEAR, or make one
specific correction to its primary comparator/population before implementing? Please
resolve the actual decision, not another generic whether-to-prepare consultation.

Standing: C07 supplied a bounded known-model planning benefit and ended the fixed LONG
pursuit. VSP already answered independent-calibration construction. Our untested question
is finite persistent model knowledge affecting full decisions, under the complete
population/data/budget stated above. There are no new scores. The strongest simpler
explanations are that posterior uncertainty disappears before useful opportunities,
the value ordering is insensitive, or finite planning/filter error costs more than
the retained uncertainty helps. In that case the first full run may be adverse or
uninformative; a positive result is not owed.

Please address whether shared joint inference makes P a serious ordinary plug-in control
for this estimand; whether the calibration and four-point population establish a clean,
honest finite-knowledge question; and what the correlation/affinity bridge actually
predicts. If a minimal alternative is substantially more informative, specify it and
its complete price. Do not add a proof, positive-toy, exact-headroom, suffix-replay or
exhaustive rank-flip requirement. Necessary correctness checks are welcome. A numerical
gain is not proof of a mechanism or general MARL/UAV superiority. No generic new
architecture search, old LONG extension or borrowed training-fit price.

Context (paths marked source_sha resolve at the full commit in the sent message):

* Current owner assignment and full candidate are in this notebook at source_sha.
  Constitution `docs/project/OPERATING_CONSTITUTION.md` §§1–6,8 at source_sha governs;
  owner pause is lifted except FSD, G33 is frozen, this independent direction is selected.
* Current methods at source_sha: `.agents/skills/hmasd-scientific-tools/SKILL.md`,
  Mathematics/conjectures/experiments, Explore, Statistics, Cost and Pro; engineering
  skill Checks/review and Execution/admission only for any dependent implementation issue.
* `docs/research/RESEARCH.md` §§2,6–8 and finite-model row/plan at source_sha are revisable
  shared background, not proof or extra approval. Relevant effects are described above.
* Historical evidence: `docs/research/candidates/skill_information_refresh/NOTES.md`
  2026-09-21 re-entry/closure and owner-review sections, plus `CLAIM_near_commit_c07.md`
  at source_sha. Executable source is explicitly `3ca4cb1f83ea869e1efca852a099db31c52b0e2c`:
  `experiments/candidates/skill_information_refresh/c01/host.py`, `c06/belief.py`,
  `c06/planning.py`. These are old known-law contracts, not silently changed new inputs.
* Prior applicable advice: `docs/research/archive/2026-09-24/RESEARCH-question-led-programme-adopted.md`
  C1 section of Answer and Decision at source_sha. VSP contrary/scope evidence:
  `docs/research/candidates/vsp_03/NOTES.md` B11 completed section and
  `CLAIM_fitted_opportunity_b09.md`, both at source_sha. No full raw re-audit is claimed.
* Primary papers linked in the mathematical bridge, specifically BAMCP root sampling
  sections3.1–3.2 and BA-POMDP joint-belief sections3–4. State any source you cannot read.

Prospective cost: the proposed512 closed-form calibration fits,0 neural/policy fits,
8,192 calibration steps,147,456 evaluation team ticks, up to188,743,680 branch transitions,
and the additional filter/draw/init/storage/review/readback work above. No actual launch
is accepted and no measured wall estimate exists for the adapted implementation.

Constraints: advise only; no training or experiments. Write only in the empty Answer
subsection below on `codex/finite-model-decision-value-sept25`. Read the pinned question,
then fetch the latest target blob before editing; use its actual blob SHA. Preserve the
question and all other bytes and stop on overlap. On write success report the actual
commit. If GitHub writeback is unavailable, return the complete answer in chat, not only
a receipt, link or SHA. The DM owns the choice and will verify consequential claims.

Return: a direct recommendation with material reasons and the strongest alternative;
what the bridge does/does not establish; the smallest useful complete comparison and
any specific adjustment to the above with its cost; predicted intermediate and native
observations including adverse/inconclusive interpretation. For material objections
include MATERIAL_DISSENT yes/no. No new record, approval process or fixed idea quota.

### Answer

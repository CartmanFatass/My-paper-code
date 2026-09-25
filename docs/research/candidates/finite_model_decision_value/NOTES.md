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

#### 一、直接建议：按 B01 实施，不替换主对照或四点总体

**建议保留 P4、U4、P32、U32、AF、KNOW_P_NEAR 的完整 B01，按已声明的有限比较实施。MATERIAL_DISSENT: no。** 共享联合推断后，再比较 posterior-mean forward NEAR 与 joint-sampled NEAR，是本题估计对象的严肃对照。我不建议先换总体、降低校准量、增加算法臂，或购买一个寻找阳性机会的前置批次。下面提出的是既有合同的实现澄清和结果解释，不是新的批准条件；是否接受及实际执行仍由 DM 负责。[本题固定设计][B01]与[当前治理][constitution]支持这个范围。

理由不是预期 U 必胜，而是三个问题现在已经具体化：未知的是跨校准与部署持续存在的物理参数；数据取得及在线信息权利已明确；干预发生在同一推断之后的前向机会估值。一次完整结果即使不利，也能限制“在这套数据、近似过滤和 32 粒子程序中，保留联合不确定性值得付费”的具体判断。这比继续笼统准备，或重新估回所有世界通用的 .75，更有信息价值。

这也正确继承了历史。C07 的 NEAR−AF 为 1,280 世界多完成 102 个任务，79 正、13 负、1,188 平；它支持已知律普通规划的有限用途。固定 LONG 的结论不证明 NEAR 全局最优，也不要求本题重新打开 LONG。VSP B11 的 O_R0−O_full 三块为负、负、零，而 O_R0−R0 均正；独立校准构造已经有答案，参数拟合变化并不强迫产生相应的策略价值变化。本题不把这些异质实验池化成复现，也不把其旧成本当新报价。[C07 完整结果、重入及 owner-review][C07-notes]；[C07 冻结合同][C07-claim]；[VSP B11 完整结果][VSP-notes]；[VSP B09 合同及追加结果][VSP-claim]。

#### 二、P 是合格的 plug-in，但要准确说清“合格于什么比较”

P 使用联合过滤所得的状态边缘和参数均值，把后者代入全部前向物理转移。这是**推断资源匹配的后验均值前向规划器**，并非故意不给数据的弱基线。P 已经利用模型不确定性来形成上游隐状态推断；U 若胜出，不能仅归因于“U 有联合滤波而 P 没有”。这是保留该对照最有力的理由，也落实了既有 C1 关于同数据、同规划资源下比较 plug-in 与不确定性机会估值的建议。[C1 Answer 与 Decision][C1]

但不要把它称为“最廉价的普通点估计流水线”，也不要把共享联合过滤视为已证明更准确。它比只保留一个参数估计和 22 个状态质量的点过滤器持有更多表示资源；双方仍共同遗漏发送/沉默似然，未获得真实后验保证。P 的名称应始终包含 **posterior-mean forward**，而不是让读者误以为它从估计到规划全程只维护一个模型。

同样，“共享推断”指**同一程序、同一初始校准分布、相同合法历史下同一输出**，不是两条已分叉轨迹在线共享后验。P 与 U 的发送改变接收缓存和后续物理路径，之后各自合法观测、隐状态边缘及参数均值都可能不同。这些后果属于完整策略干预；不能为了维持后验数值相同而跨臂复制在线观测，也不能把两机器人的私有后验合并成免费公共信息。[B01][B01]；[合法记录与过滤代码][belief]

最强的普通替代是“有限参数估计＋点参数物理过滤＋NEAR”。它适合回答从头到尾的低成本流水线是否值得采用；**现在用它替换 P，会同时改变推断和前向模型，从而降低本题的可解释性**。此外，该流水线还须明确在线怎样更新点参数，以及点参数变化后怎样处理过去的隐状态分布，不能只把 88 改成 22 就当作完整算法。我不购买这个额外臂，也不声称当前 P 在墙钟或收益上支配它。

#### 三、总体与校准成立；有限知识的范围要比“模型学习有效”窄

四点总体与正确先验是一套清楚的、well-specified 的研究总体。每个 context 的真实 θ 在校准及 H96 中固定，且两机器人共享；新运动噪声则在给定 θ 后独立。这区分了参数未知、当次随机运动和隐藏 peer 状态，也避免了把每 tick 独立重抽的潜变量错误地当成可从过去识别的持续参数。[B01][B01]

距离 33、32 次尝试使最后距离至少为 1，因此整个校准段不会因到达终点而停止暴露。由连续自身距离取得的成功数 s 足以计算

```text
q_k(theta_j) = theta_j^s (1-theta_j)^(k-s)
              / sum_l theta_l^s (1-theta_l)^(k-s),
theta_j in {.35, .55, .75, .95}.
```

均匀先验在分子分母抵消。这里的校准后验是声明模型下的精确有限计算；接入遗漏发送似然的在线过滤后，整体仍须标为 approximate joint physical belief，不能沿用“精确后验”的标签。校准是真实生成并保存的自身观测，不应通过直接读取环境的 Bernoulli 标签替代所声明的数据接口。

k4 必须只收到前四次记录，不能先拟合 32 次再截取展示。两个机器人复制同一公共校准输入是允许的，但不是两份独立数据；不能把同一个 D 重复计入似然。在线也没有新增参数广播、peer truth 或未到达的包。校准与评价独立指给定共享 θ 后的过程随机流独立，不是要求两者边缘上与 θ 无关。

还有一个值得预先点明、但不应“纠正”的事实：四点先验均值是 .65，固定接收器的名义常数是 .75。它们没有义务相等。`project` 的 `floor(.75*age)` 和 `choose_route` 的距离/.75 是双方真实执行与模型执行都必须保留的控制律；修改它们会把接收器适应混入估值干预。θ_bar 也不必落在四点支持上：它是合法 Bernoulli 参数，不能悄悄舍入成最近支持点或换成 MAP。[固定 host 源码][host]

因此，研究范围是“对这一预先选择的四点总体、正确支持与公共校准权限、固定名义接收器的有限决策价值”。它不估计真实部署总体，不检验未知先验、支持外 θ 或结构错设下的鲁棒性，也不保证 k32 足够辨别所有相邻参数。没有这些外推不妨碍该小型合作研究本身成立；不需要发明外部客户或先交付 UAV 阳性。

#### 四、数学桥接：不只曲率，也不推出 U 的原生收益为正

固定一个双方相同的合法历史，令 Δ(x,θ) 是同一 SEND/HOLD 干预、同一固定 AF continuation、同一 NEAR 终点规则下，给定隐状态与参数后的期望完成数差。把未来过程噪声积分进 Δ。记 μ 为该根的近似联合信念，b 为其状态边缘，则题面的两个目标准确地是

```text
U = E_mu[Delta(x,theta)]
P = E_b[Delta(x,theta_bar)],       theta_bar = E_mu[theta].
```

实际运行使用 32 粒子估计这些目标，不直接观察 U、P 的精确值；它们也不是完整 H96 策略收益。以下均为关于这些对象的条件推导，不是已测机制。

**仿射相等必须作用于同一个条件对象。** 若同一个 f(theta)=Delta(h,theta) 对 θ 仿射，当然 E[f(theta)]=f(E[theta])。但当前 P 还切断了 x 与 θ 的关联。若对每个 x 有 Δ(x,θ)=a(x)+c(x)θ，则

```text
U - P = E_mu[c(x)*theta] - E_b[c(x)]*E_mu[theta]
      = Cov_mu(c(x),theta).
```

所以“每个状态下优势对参数仿射”不足以推出本题 P 与 U 相同。也不能由协方差可能非零推出它为正。令 m(x)=E_mu[theta|x]，可进一步写成

```text
U-P = E_b{ E[Delta(x,theta)|x] - Delta(x,m(x)) }
    + E_b{ Delta(x,m(x)) - Delta(x,theta_bar) }.
```

第一项是条件参数分布相对其条件均值的差；第二项来自用全局均值替换状态相关均值。一般优势并无统一凸性，这两项没有共同的正号保证。用状态条件均值作为另一个对照可以回答不同的分解问题，但不是本题普通全局参数 plug-in 的必要替代，也不在此次增加机制臂。[题面桥接与其限制][B01]

**“单次 Bernoulli 转移仿射”不等于联合或多步优势仿射。** 对两个预先指定、均有运动资格的试验，给定同一 θ 时独立，令其结果为 A1、A2。在根参数分布 q 下，

```text
Pr(A1=A2=1) = E_q[theta^2]
            = E_q[theta]^2 + Var_q(theta).
```

均值参数的独立运动模拟给出 E_q[theta]^2。两个试验既可跨时间，也可属于同一 tick 的两个机器人。因此 P 是 **mean-parameter dynamics**，不必等于完整联合状态转移核的 posterior-predictive mean；未知的共享参数同时带来跨时与跨机器人的预测关联。这说明保留持久模型具有具体数学对象，却仍没有告诉我们发送排序、冲突或完成数差的方向。每 tick 重抽 θ，或每个机器人独立抽 θ，都不是声明的 U。

**决策差异与任务收益还隔着两层。** U 与 P 的优势值不同，可能仍同号；恰好为零时还要执行原 AF tie rule。即使理想 U 对其近似信念、同一固定 continuation 下的二选一更合算，也不代表该近似信念对真实世界正确，更不代表双方随后反复重规划的 H96 结果更好。有限 MC 的排序错误、被省略的发送似然及真实策略/AF continuation 差异都保留在程序中。不能把“平均优势更大”当作原生完成数改善的证明。

**大数据预测也只是有条件的。** 对精确校准分布及嵌套 D4、D32，全方差公式给出

```text
E[Var(theta|D4)] - E[Var(theta|D32)]
  = E[(E[theta|D32] - E[theta|D4])^2] >= 0.
```

这支持初始不确定性平均收缩的预测，不保证每个 context 的方差逐样本下降，更不保证 U32−P32、P32−P4 或完整收益单调。后续在线数据又受策略影响。在参数分布退化为一点时，P/U 的理想目标相同；实际有限估值是否完全相同还取决于是否采用相同状态与过程随机数。

文献桥接应保持在这个强度。[Guez、Silver、Dayan 2012 §§3.1–3.2][BAMCP] 的 root sampling 在一次模拟中保持同一模型，但同时有跨未来历史的 UCT 搜索；本题只借用模型持久性，不实现该搜索，也不继承其收敛结论。[Ross、Chaib-draa、Pineau 2007 §§3–4][BAPOMDP] 把状态和模型统计量放入联合信念，并讨论有限近似与信念跟踪；它不验证本题省略发送似然后的后验，更不提供双机器人闭环性能保证。U 不是“抽一个模型并执行其最优策略”的策略，也不是已实现最优探索的 BAMCP。

#### 五、最小有用完整比较与价格：保留六臂，别把相同粒子数写成相同墙钟

针对**主问题加已经提出的数据剂量预测**，六臂设计没有明显冗余。P4/U4 是主比较；P32/U32 判断较多初始合法知识是否改变增量；AF 判断复杂规划包相对廉价规则的用途；KNOW_P_NEAR 区分额外真实参数知识这一资源条件。AF 与 KNOW 每 context 各执行一次、在两个剂量读法中复用同一行是正确的，重复评价不会新增知识。[B01 的工作量合同][B01]

| 工作 | 保留的 B01 总量 |
| --- | ---: |
| 独立 deployment contexts | 256 |
| 校准轨迹及运动步 | 256 × 32 = 8,192 步 |
| 不同 context×剂量的闭式校准拟合 | 512；P/U 共享初始拟合 |
| 神经/策略 fits；optimizer updates | 0；0 |
| 完整评价 episodes；真实 team ticks | 1,536；147,456 |
| 规划 episodes；模型分支转移保守上界 | 1,280；188,743,680 |
| P/U 与 KNOW 的单机器人过滤支持 | 88 与 22；AF 不设多余过滤 |

上界为 `1280*72*32*2*32`。72 是 H96 中每帧最多六个非强制 TDMA 时刻、共十二帧的保守根数界，并非每条实际策略都会用满。每个分支转移还是一个双机器人 model-host tick，不能混称为一次原生评价或一个独立样本。还要计入参数/状态采样、完整未来数组、模型初始化、过滤似然工作、复制、保存及读取。旧规划源码按完整 H96 构造合成数组，并可能执行到批内最远所需端点；实际 NEAR 的较短平均端点不等于同比例减少这些工作。[规划与计数源码][planning]

**最强的节约方案是只保留 k4 四臂 P4/U4/AF/KNOW，而不是削弱 P。** 同样 256 contexts，只收集四次校准，则是 1,024 校准步、256 次闭式拟合、1,024 个评价 episodes、98,304 team ticks、768 个规划 episodes及至多 113,246,208 分支转移；仍有完整采样/过滤/初始化/存储/工程成本、零神经 fits，墙钟未知。相对 B01 省去 7,168 校准步、256 次拟合、512 个 episodes、49,152 team ticks 和至多 75,497,472 个分支转移，却完全丢掉剂量对照。我不选它：本题已经具体关心有限知识增加后的增量变化，额外两个剂量臂购买的是不同信息，并非替主结果增加名义 n。这是比较价格，不是另一个已批准批次。

实验总价要按实际收集的 32 次计；讨论 k4 方法所需的数据时可以注明它只消费四次，不能反过来把其余 28 次在本次实验中算作免费。参考臂不消费校准，不意味着整个实验没有校准成本。各程序相同 32 粒子是规划曝光匹配，不是相同 wall、相同方差或相同总推断成本。AF 可能以远低的计算量保持更好的实际使用选择；没有预定成本—收益换算，就并列报告完成数和成本，不编造“净部署效用”。C07 的 138,555,584 分支和约 26 倍面板时间只作历史量级背景。

#### 六、必要实现澄清：特别防止归一化抹去模型证据

这些检查应进入当前实现的已有测试/审阅，而不是增加结果性仿真、精确解、阳性 toy 或枚举全部同根翻转。它们针对已读源码的可达失败点，遵循[科学方法][methods]与[工程 Checks/review、Execution/admission][engineering]。

**联合过滤须保留跨 θ 的证据质量。** 旧 `PhysicalBelief._condition_packet` 在已知参数条件下，将与已到达包匹配的前一时刻 peer 状态重置为质量 1；对旧条件过滤这是其接口。新实现若分别运行四份旧过滤器，然后保留旧参数权重，就会丢掉各假设解释这个包和自身观测的相对可能性。设送时包约束为 M_t(x)，L_theta 表示随后物理转移及合法自身观测条件，则应保持形如

```text
w(theta,x') = sum_x mu_t(theta,x) * M_t(x)
                   * L_theta(x', own_observation | x, lawful_history)
mu_(t+1)(theta,x') = w(theta,x') / sum_(theta,x') w(theta,x').
```

也可以存储条件过滤器和参数权重，但必须把每个条件过滤的归一化常数作为模型证据乘回参数权重。某一个 θ 分量被观测排除可以合法归零；全联合支持为零才是应如实报错的矛盾，不能回填 peer truth 或任意重置先验。[旧过滤完整代码][belief]

包负载约束的是发送时刻的状态，随后才传播到新观察时刻；同一缓存不能每 tick 当成新的独立观测。自身在任务边界被重置的距离不能错误计作一次运动成败，非 APPROACH/正距离时也不能虚构 Bernoulli 失败。重复公共 D、不保留包的跨参数似然、把事后 peer 状态当成当时已知，都会直接改变科学问题。保留发送/沉默似然的省略并在结果中注明；这不妨碍合法 quota/pending 状态按实际收发时刻恢复。

**根采样可以更紧地配对，而不改变任何一臂的分布。** 建议把现有“有意义处共享 state uniforms”具体化为：先用共同状态随机数从 b 抽 x，再在 U 中用独立参数随机数从 μ(theta|x) 抽 θ；P 使用同一个 x 与 θ_bar。因为 `b(x)*mu(theta|x)=mu(x,theta)`，这仍是联合抽样，不是把两个边缘独立相乘。它保证相同历史下 P/U 的根状态样本相同，减少无关的状态采样差别；无需新增 particles 或模型分支，只增加已有小支持上的条件概率/CDF 工作。

每个 U 粒子的 θ 同时用于两个机器人、整个未来段及成对 HOLD/SEND；每个运动试验仍使用不同的过程 uniform。P 使用 θ_bar 作为整条该根模拟的固定物理参数。以 context、剂量所需公共配对、tick、agent、particle、过程类别等固定地址确定随机流，不能因某臂多走一条分支而移动另一臂之后的随机数。参数抽样流与状态/运动/任务流分开；模型与真实评价未来流分开；改变批处理顺序不应改变各已声明根的随机输入。世界 ID 仅作随机流地址，不能编码可读取的真实 θ。

**端点与控制律按语义匹配。** 保留同一 NEAR 规则：首个下一缓存敏感接收机会，计到包含它的承诺结束，受 32 ticks/H96 限制。不同参数模型下机会可能出现在不同 tick，因此“同一终点规则”不要求 P/U 的每个样本有同一个数值端点。每个粒子内部的 HOLD/SEND 必须使用共同的机会终点及既有 reward mask；不能按哪个分支先有利就停止，也不能将批处理 padding 的奖励误计入短目标。两分支根后都用 AF，精确零优势仍回到 AF；不能悄悄改成一律 HOLD、风险奖励或未来再次调用 U。[配对模型与机会识别源码][planning]

小型固定输入检查应覆盖：四点似然及 k4 前缀隔离；合法观察不受未发送 peer truth/真实未来数组的修改影响；联合证据全局归一化；相同历史的 P/U 过滤输出一致；θ 分布退化为一点且随机输入匹配时，P/U 的根目标与决策一致；host 物理律改变但 `.75` 接收器常数保持。这里要求的是被改代码的正确性，不是先证明任务改善或借检查调参。

#### 七、怎样读中间量与完整原生结果，包括不利和无信息结果

保留“U4−P4 平均可能为正、k32 的增量及分歧可能减少”作为**可失败的工作预测**，不提高为当前结论。最有力的简单解释依次是：有用接收机会出现前参数已经从自身运动中迅速识别；剩余不确定性不改变动作符号；或有限规划/近似过滤与后续闭环代价超过其用途。这些解释可以限制当前程序，不必先购买排除它们的批次。

中间读数沿已经运行的共同前缀取得即可。每个剂量分别记录共同前缀是否出现分歧、第一次分歧的实际时刻/发送者/可选资格、参数方差与均值、两边优势估计及动作；已有根样本 SE 可作 MC 噪声描述。没有分歧的 context 也保留。参数不确定性在首批有用机会前是否已收缩，比仅报告校准刚结束时的方差更贴近问题；若用已保存的合法运动观测数量说明收缩，不能把它们当新的独立实验单位。

一旦实际路径分叉，后面的值和动作只属于各自历史。不得把重新碰巧相同的物理快照当成相同信息历史，也不得把“发生过首处分歧的世界”作为主效果总体。共同前缀长度与是否存活到后期本身由策略差异影响，所以不同剂量的前缀分歧数量只能作相应暴露范围的描述，不能冒充同一根总体上的纯机制频率。

| 完整读数 | 可以保留的解释；不能越过的边界 |
| --- | --- |
| 机会前不确定性已很小，P/U 少有分歧 | 当前校准＋在线信息下，不确定性保留可能没有足够决策窗口；不证明所有有限知识问题无价值。 |
| 不确定性仍在、估值不同，但动作多同号 | 在已访问的共同前缀上，值差未充分越过决策边界；不要求为了制造翻转而改阈值。 |
| 动作确实不同，完成数差小、混合或为负 | 排序变化不足以带来所预测的完整用途；MC、信念近似、状态关联与闭环后效尚未被分别识别。 |
| U4−P4 为正，且 U32−P32 较小 | 与有限知识增量预测相容，仍只是这套联合保留程序的结果，不是 Jensen、关联或探索的单独因果证明。 |
| U 的增量为正，却低于 AF，或付出很大计算代价 | 可以保留规划器内部增量，同时降低采用整个规划包的理由；不隐去廉价 AF。 |
| k32 未减少分歧/增量，或某些臂随数据增加反而损失 | 数据剂量预测受挫；保留完整反例，不由“理论上知识更多”删除它，也不自动追加剂量或粒子扫描。 |

KNOW_P_NEAR 不是单调上界：真实参数知识不消除部分状态、近似过滤、有限 MC、固定接收器或有限 continuation 的限制。它有利可以提示本程序中已知参数资源有用途；它无优势不能证明没有 headroom，偶尔低于 U/P 也不能证明少知识一般更优。

原生主读数仍是每 context 的完整完成任务数。附带读取绝对完成、所有差值、正负平局、冲突、等待、包、分支和成本，以及预先四个 θ 层的描述和负尾部。固定 H96/12/16 有 14 次任务开始，原 quota 合同每 episode 24 个包；收益是时机的用途，不是节省发送量。少冲突或少等待不能单独替代完成数，也不能把全程差值分配成某个根动作的因果贡献。[host][host]；[B01 读数范围][B01]

统计上定义 `d_i,k = jobs(Uk,i)-jobs(Pk,i)`，以 256 个独立 context 计算均值和 `sd(d_i,k)/sqrt(256)`。剂量对比直接对同一 context 的 `d_i,32-d_i,4` 求均值/SE，不能把两个剂量当独立样本；复用参考行也不增加 n。实际有限规划随机性已经包含在每 context 的政策结果中，不把根 MC SE 再加一次。普通配对区间按原计划作探索性近似，既不借用 C07 的 .05 确认门槛，也不导出等价或非劣结论。高度稀疏乃至全平局可能使样本 SE 为零，却不证明总体增量精确为零。[统计与探索方法][methods]

若技术失败或必要配对缺失，报告可信部分及缺失依赖，不补零、不换种子、不把部分完成包装成固定 256-context 结果。遥测缺失只限制相应资源主张；代码或必要结果证据缺失则限制依赖的科学比较。无论正、负或不确定，都不因结果本身自动扩大这一次设计。

#### 八、来源边界与最终选择

科学输入使用 `53149a02d93c2b5b925d3276993824bb481cc80c`：已读取完整本题、constitution §§1–6、8、指定 scientific-tools 方法、engineering 的 Checks/review 与 Execution/admission、RESEARCH §§2、6–8 及本方向行/计划；已读取 C07 的完整重入/收尾及 owner-review、冻结 claim，C1 的完整适用 Answer 段与 Decision，以及 VSP B11 完成节和 B09 claim/追加结果。旧 host/filter/planner 的实际代码按显式指定的 `3ca4cb1f83ea869e1efca852a099db31c52b0e2c` 读取，没有以目标分支后续内容替换这些科学输入。[当前共享背景与计划][research]

两篇论文的指定正文段落均可读；BAMCP 的 PDF 截图接口失败，但 §§3.1–3.2 的正文完整可读，本答复没有依赖未取得的图像。BA-POMDP §§3–4 的正文及相关页面已核对。没有决策关键指定正文的未读缺口。

**仍未完成、也不能声称完成的是：历史原始轨迹/NPZ 的独立全量重算，新的四参数实现和独立工程验收，以及 B01 的实际成本与原生结果。** 历史数字来自已读固定记录中的作者归约；它们不是本次新实验。本次仅进行了来源读取、条件代数及工作量整数核算，没有拟合数据、执行 host/model rollout、训练、结果性 profile/pilot 或实际 launch。当前运行准入和节点资源应在 DM 真正执行时按既有流程核验，不由本答复代替，也不新增审批。

**最终选择不变：保留当前六臂 B01；落实联合似然质量、持久共享 θ、固定接收器及配对 RNG 的实现语义，然后由完整一次结果判断用途。** 我不选择改总体、换成弱推断 P、重做独立校准贡献、重开 LONG，或购买机制分解臂。最值得购买的新信息，是这套明确有限知识条件下 U 是否真的改变并改善完整团队决策，而不是提前证明它应该获胜。

[B01]: https://github.com/CartmanFatass/My-paper-code/blob/53149a02d93c2b5b925d3276993824bb481cc80c/docs/research/candidates/finite_model_decision_value/NOTES.md
[constitution]: https://github.com/CartmanFatass/My-paper-code/blob/53149a02d93c2b5b925d3276993824bb481cc80c/docs/project/OPERATING_CONSTITUTION.md
[methods]: https://github.com/CartmanFatass/My-paper-code/blob/53149a02d93c2b5b925d3276993824bb481cc80c/.agents/skills/hmasd-scientific-tools/SKILL.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/53149a02d93c2b5b925d3276993824bb481cc80c/.agents/skills/hmasd-research-engineering/SKILL.md
[research]: https://github.com/CartmanFatass/My-paper-code/blob/53149a02d93c2b5b925d3276993824bb481cc80c/docs/research/RESEARCH.md
[C07-notes]: https://github.com/CartmanFatass/My-paper-code/blob/53149a02d93c2b5b925d3276993824bb481cc80c/docs/research/candidates/skill_information_refresh/NOTES.md
[C07-claim]: https://github.com/CartmanFatass/My-paper-code/blob/53149a02d93c2b5b925d3276993824bb481cc80c/docs/research/candidates/skill_information_refresh/CLAIM_near_commit_c07.md
[C1]: https://github.com/CartmanFatass/My-paper-code/blob/53149a02d93c2b5b925d3276993824bb481cc80c/docs/research/archive/2026-09-24/RESEARCH-question-led-programme-adopted.md
[VSP-notes]: https://github.com/CartmanFatass/My-paper-code/blob/53149a02d93c2b5b925d3276993824bb481cc80c/docs/research/candidates/vsp_03/NOTES.md
[VSP-claim]: https://github.com/CartmanFatass/My-paper-code/blob/53149a02d93c2b5b925d3276993824bb481cc80c/docs/research/candidates/vsp_03/CLAIM_fitted_opportunity_b09.md
[host]: https://github.com/CartmanFatass/My-paper-code/blob/3ca4cb1f83ea869e1efca852a099db31c52b0e2c/experiments/candidates/skill_information_refresh/c01/host.py
[belief]: https://github.com/CartmanFatass/My-paper-code/blob/3ca4cb1f83ea869e1efca852a099db31c52b0e2c/experiments/candidates/skill_information_refresh/c06/belief.py
[planning]: https://github.com/CartmanFatass/My-paper-code/blob/3ca4cb1f83ea869e1efca852a099db31c52b0e2c/experiments/candidates/skill_information_refresh/c06/planning.py
[BAMCP]: https://proceedings.nips.cc/paper_files/paper/2012/file/35051070e572e47d2c26c241ab88307f-Paper.pdf
[BAPOMDP]: https://papers.nips.cc/paper_files/paper/2007/file/3b3dbaf68507998acd6a5a5254ab2d76-Paper.pdf

## 2026-09-25 — Full Pro reading, adoption and B01 implementation scope

Read the complete 13,093-character Answer at
`8a40ed97ecca2a0ef91f09ee3fbab2975a91ddf5`. The deterministic observer collected a
533-character chat receipt, not the scientific answer; `deliver` verified the actual
answer commit on the intended branch, the initially empty subsection, unchanged question
and unchanged remainder. Jev key is
`hmasd:b27ac79065f0f87e3bb81b0d3c4df4d2de5af2a0f8000d29f740185a3475d4ff`;
Send accepted at6 Pro, completion COMPLETE, delivery DELIVERED, zero recoveries/resends.
The owned conversation has zero remaining browser tabs; four unrelated tabs are preserved.
The answer-only writer lease is reconciled. Latest published main inspected at
`dee97605e9f25243ed8587a67b4bc122aeb32180` still has lifted project pause and this
direction's selected independent lead. Its new S7 evidence does not change this design.

**DM decision: execute the proposed six-arm B01 as exploration.** Pro's no-material-dissent
is advice, not data. I retain P4/U4/P32/U32/AF/KNOW_P_NEAR, the four-point law, calibration
and 256 contexts, and all declared costs/readings. I considered the four-arm k4 alternative:
it saves49,152 team ticks and up to75,497,472 branch ticks but loses the useful initial-data
dose contrast; that observation is worth the extra finite work. No LONG or point-filter
pipeline arm is added. The projection comparison deliberately conditions on an inference
resource supplied to both planners and does not certify the cheapest plug-in pipeline.

The source audit already verified the consequential packet-likelihood issue: old
`_condition_packet` resets a compatible state to unit mass, which cannot be copied
independently across parameter hypotheses without preserving each likelihood. I adopt
one global normalization over parameter×state, permitting a single parameter's mass to
become zero and failing only for impossible joint evidence. No peer truth fallback.
The posterior is still a physical-law approximation that omits send/silence likelihood.

I also adopt Pro's tighter root coupling: sample x from the shared state marginal using
the same addressed uniform, then U samples theta conditional on that x using a separate
uniform; P uses the overall posterior parameter mean. This exactly targets the stated
joint distribution, with no extra particles or branches. The same U theta governs both
robots, both root branches and every simulated tick. The local covariance derivation is
algebraically correct; the shared-parameter two-trial identity E[theta^2]−E[theta]^2
also clarifies why mean-parameter Bernoulli dynamics are not necessarily the full joint
posterior-predictive kernel. Neither supplies a sign for native benefit. The larger-data
variance identity holds in expectation for exact nested calibration; we will retain
per-context increases and any native dose reversals. Existing primary-source readings
support only the limited model-persistence/joint-belief bridge already recorded.

**Final prospective identifiers.** B01 uses context IDs0..255, world master925731,
parameter/calibration phase40 (separate stream0/1), evaluation phase41, planner
master925973/phase42. The same addressed state/parameter/process/job streams apply
across arms and doses where applicable. Context IDs only address randomness; the
controller never sees the hidden theta or actual future arrays. Batch16, H96, P32,
one native compute process, BLAS/OpenMP threads1. No tuning or endpoint selection.
The runner will assert the fixed scientific configuration. Counts remain512 shared
closed-form calibration fits,0 policy fits/optimizer updates,8,192 calibration steps,
1,536 full evaluation episodes/147,456 team ticks and the188,743,680 branch-tick bound.
Implementation/test inputs are separate fixtures, not the 256 evaluation contexts.

**L0 — one bounded core adaptation.** Implement disposable B01 code under
`experiments/candidates/finite_model_decision_value/b01/` and mirrored tests. Recover
only the required C01 host/C06 belief/planner from explicit source
`3ca4cb1f83ea869e1efca852a099db31c52b0e2c` into this direction; preserve provenance in
module docstrings. Do not restore historical experiment history into main or edit old
code. Core deliverable: parameterized world law, lawful joint physical filter and
matched P/U root estimates with exact inherited NEAR/AF semantics. Independent Reviewer
must examine information access, global likelihood normalization, RNG addressing,
conditional sampling, masks/endpoints, costs and output identity before result execution.

The bounded Implementer owns only `b01/host.py`, `b01/belief.py`, `b01/planning.py` and
`tests/experiments/candidates/finite_model_decision_value/b01/test_core.py` in this
checkout. It returns facts/diff/checks, never edits NOTES or index, launches results,
sends Pro or creates children. DM owns `b01/study.py`, the admission entry
`scripts/run_fmdv_b01.py`, study tests, records and acceptance. These are compatible
concurrent edits; neither writer reverts the other's work or stages the other's paths.

Interface: `Worlds.make(..., probabilities=...)` creates the retained host; only actual
world generation receives true theta. `JointPhysicalBelief(record, theta_values,
parameter_weights)` stores theta values as B×K and joint weights B×K×22, initializes
the original peer-state distribution, and updates from copied `LocalRecord` only.
Properties expose state/parameter marginals, parameter mean/variance and counters.
For KNOW, K=1 with per-context true parameter supplied explicitly. Planner
`paired_values(record, weights, theta_values, states, ids, seed=..., phase=...,
particles=32, mode='POSTERIOR_MEAN'|'JOINT', counters=...)` returns per-root `delta`
and `mc_se` arrays, plus bounded optional details; it uses only this lawful input.
Calibration in the DM-owned study derives likelihood counts from observed corridor
positions, never an environment success label. P/U share initial calibration fits,
not their diverged online observations or private robot beliefs.

Checks use small held-out fixtures, not result-bearing panels: known-law compatibility
against source; packet/own likelihood with an independently hand-computed case;
parameter-state dependence and per-component zero mass; degenerate-parameter P/U
identity; own-boundary masking; common root states and persistent shared theta; preserved
.75 receiver; RNG batch/order invariance and no future/peer-truth leakage; exact NEAR
endpoint and full runner counts/artifact roundtrip under mocked admission. Stop and
return any semantic ambiguity, unsupported required measurement or contradiction.
Do not change scientific arms, prior, data doses, seeds or budgets during implementation.
Actual inputs will be committed/pushed before fresh wsl_4070 admission. Tests and review
costs are recorded separately; no scientific performance or model-fit result exists yet.

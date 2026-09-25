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

## 2026-09-25 — B01 code acceptance and source publication

Accepted the bounded Implementer's host/filter/planner after DM source review and an
independent Reviewer pass. The reviewer independently compared a full H48 fixture with
the retained C01 source: physical/cache/quota arrays, rewards, metrics and endpoint rows
matched. The host diff is limited to the declared probability parameterization and
provenance text; fixed receiver/channel semantics remain. Joint normalization, lawful
information boundaries, conditional root sampling, NEAR endpoint, AF continuation and
paired statistics had no material finding. The executable production entry requires
native admission before output/science and refuses substituted seeds or SHA.

One P2 recovery finding was repaired before any result execution. An exception after
a real planner call originally kept the trajectory but lost the current batch's completed
model work counters/times. The failure path now retains current-batch `.cost.json`,
observed/completed ticks, filtering/model work and timings, and the FAILED summary hashes
the partial raw artifacts. An injected-after-planner test verifies this actual path.
The persistent-parameter test was strengthened to intercept simulated advances across
both robots, all future ticks and both branches, using the independently specified
theta0/1 conditional law rather than the planner's returned parameter as its oracle.

All12 focused tests passed in1.14s on configured local scientific Python3.10.20/
NumPy1.26.3. This includes one complete six-arm correctness fixture with2 contexts,
H48/P2, separate seeds441731/442973 and mocked admission checks; it is not a B01 result
panel or score-selection exposure. The reviewer independently ran all prior11 tests
(1.11s), then the3 affected follow-up tests (1.05s) and closed P2 with no remaining
material finding. Abrupt termination and inability to write any metadata remain outside
the tested exception-recovery path; native exit/partial evidence will retain that scope.

The plan is already independently published to main as
`adf68344620a2439276bdf3061b2e0e0fc94f48d`, preserving concurrent controller-composition
and S7 changes; no archive or App notification was made. Its six-arm scientific exposure
is unchanged. Source publication below precedes actual node preparation/admission.
Remote wsl_4070 is reachable, with configured Python3.10.21 and NumPy1.26.3, and its
canonical direction/lead is present. The node's canonical checkout has unrelated owned
dirty/untracked work; we will not edit or clean it. A separate exact-source worktree and
kernel snapshot will hold this direction, with outputs durably retained there.

Result tag selected before execution: `b01_finite_knowledge_s925731`. Run source and
native identity will be bound by its launch manifest; no result-bearing operation has
yet been accepted. The unchanged counts are above; no adapted wall-time estimate is
invented from the old C07 or test fixture. CPU-only single-process evaluation is suitable
for this NumPy host; threads remain1, and actual memory admission occurs on wsl_4070.

## 2026-09-25 — B01 native admission and observation

The fixed six-arm B01 is now admitted. The authoritative
[launch manifest](../../../../runs/finite_model_decision_value/b01_finite_knowledge_s925731/launch-manifest.json)
binds its exact published source, native operation, process identities and output paths;
the copied [actual-node preflight](../../../../runs/finite_model_decision_value/b01_finite_knowledge_s925731/admission-preflight.json)
passed the configured memory floor. The
[initial native status](../../../../runs/finite_model_decision_value/b01_finite_knowledge_s925731/native-status.initial.json)
reports accepted admission, consistent records and both native processes running. The
outer supervisor's successful exit only records the launch command; it is not the
scientific child's completion or acceptance. No endpoint result has been read.

Before admission the same12 focused checks passed on the configured executing-node
interpreter in0.87s, and its source checkout was clean. Two source-preparation commands
initially stalled because the non-login SSH environment omitted the configured network
proxy: the explicit fetch, then the partial clone's on-demand object fetch during
worktree creation. Only those verified preparation process trees were terminated.
Repeating preparation through the configured `zsh -lic` environment completed the
checkout and checks; no scientific worker or accepted result operation was restarted.
Git also reported pre-existing historical object/commit-graph maintenance warnings;
we did not alter shared Git configuration, canonical owned files or old worktrees.
The required current source was materialized and the native admission succeeded.

Observe the accepted operation with the task-local `tools/hmasd_wait.py` launch probe.
Retain the fixed256 contexts, six arms, calibration doses, seeds, endpoints and declared
cost bound. On return, reconcile the same operation and read complete output, costs,
adverse evidence and raw-artifact hashes before any scientific acceptance. A terminal
failure is preserved and requires a separate diagnosis/decision; observation never
restarts the worker or creates a replacement run.

## 2026-09-25 — B01 complete: decision changes without the predicted small-data native gain

**Technical acceptance.** The same native operation exited0 with a valid exit witness;
runner and supervisor are absent and records consistent in the
[final status](../../../../runs/finite_model_decision_value/b01_finite_knowledge_s925731/native-status.final.json).
All256 contexts completed all six H96 arms:1,536 episodes/147,456 team ticks,512/512
closed-form calibration fits and8,192 calibration moves;0 policy fits, optimizer or
policy-parameter updates. All96 arm batches are COMPLETE with no filter contradiction.
No replacement context, extra result run, changed threshold or endpoint was used.

Read the complete structured [summary](../../../../runs/finite_model_decision_value/b01_finite_knowledge_s925731/summary.json),
[per-context results](../../../../runs/finite_model_decision_value/b01_finite_knowledge_s925731/episodes.json)
and [common-prefix records](../../../../runs/finite_model_decision_value/b01_finite_knowledge_s925731/common_prefix.json).
Independent existing-array readback checked all197 runner-listed hashes, every endpoint
against its raw trajectory, all contrast means/SE/sign counts and all512 common-prefix
rows against actual histories and identical joint root beliefs. Calibration posteriors
were independently reconstructed from observed position differences using log likelihoods.
All checks agree. Stored root MC SE uses float32 arithmetic: exact float32 recomputation
agrees; the maximum float64 rounding difference is1.8021e-8, not a scientific discrepancy.
No environment or model rollout was added by this readback (successful readback body0.547s).

**Complete outcomes.** Counts are completed jobs; every arm begins14 jobs/context and
sends24 packets/context. Context, not tick/robot/particle, is the paired unit (n256).
The four realized parameter strata each contain64 contexts; this is the realized draw,
not a post-score allocation or extra independent panel.

| Arm | Total jobs | Mean jobs | Total difference from AF | Arm-batch wall seconds |
| --- | ---: | ---: | ---: | ---: |
| AF | 2958 | 11.554688 | 0 | 0.450734 |
| P4 | 2994 | 11.695313 | +36 | 24.579910 |
| U4 | 2994 | 11.695313 | +36 | 24.945998 |
| P32 | 2995 | 11.699219 | +37 | 24.813000 |
| U32 | 2998 | 11.710938 | +40 | 24.703007 |
| KNOW_P_NEAR | 2996 | 11.703125 | +38 | 15.180398 |

Primary U4−P4 mean is **0**, approximate paired normal95% interval
**[−.030685,+.030685]**:3 positive,4 negative and249 tied contexts; range[−2,+2].
U32−P32 is **+.01171875** jobs/context (total+3), interval[−.008526,+.031964],
3 positive/1 negative/252 tied, range[−1,+2]. The paired dose contrast
`(U32−P32)−(U4−P4)` is+.01171875, interval[−.015903,+.039340],5 positive/2 negative/249 tied.
These exploratory intervals are not confirmation, equivalence or proof of zero benefit;
the sparse observed differences leave tail and programme-population uncertainty.

All nonzero primary differences are retained here (remaining contexts tie):

| Dose | Context: U−P jobs |
| --- | --- |
| k4 | 87:+2;109:−1;181:+2;209:−1;235:+1;240:−2;252:−1 |
| k32 | 181:+2;187:+1;226:+1;252:−1 |

At theta .35/.55/.75/.95, U4−P4 totals are−1/+1/0/0; U32−P32 totals0/+3/0/0.
These are descriptive predeclared strata, not a selected subpopulation claim. U4−P4
has one fewer conflict overall but **33 more wait ticks** (mean+.12890625,
approximate interval[+.019139,+.238674]); k32 has one fewer conflict and one more wait
tick. Local component improvements cannot substitute for the complete primary outcome.
The k32−k4 native means are+.00390625 for P and+.015625 for U, with intervals spanning0.

The planning package's conditional positive comparison with AF remains: P4 and U4 each
have31 positive/4 negative/221 tied contexts versus AF, total+36; P32 has33/6/217,total+37;
U32 has33/3/220,total+40; KNOW has32/4/220,total+38. Every planning arm loses up to2 jobs
against AF on a context. Losses occur at P4:60,181,197,231; U4:60,197,209,231;
P32:181,187,197,209,226,231; U32:197,209,231; KNOW:160,197,209,231. Complete values and
all wait/conflict/packet components stay in the linked output. KNOW exceeds P4 by only2
jobs and is below U32 by2 on this panel; it is not a monotone or global upper bound.

**Intermediate prediction and limits.** Calibration mean parameter variance contracts
from.022359153 at k4 to.004034720 at k32 (all256 contexts contract here); posterior-mean
parameter MSE also falls from.023788144 to.004241332. Yet the primary native gain and
predicted decrease of the U increment with more data are not observed.
The recorded same-history roots number5,521/7,381 for k4/k32, with508/284 different
estimated values. First actual-send divergence occurs in135/256 and65/256 contexts;
first-divergence tick medians17/24 and joint parameter-variance medians.010237922/.004840154.
Thus this is not a nonactivation result or a case of uncertainty disappearing before
every differing decision. Different prefix survival/exposure means those root rates
are not a controlled frequency comparison on one common root population.

At121/135 and58/65 first action differences, one estimate is exactly zero and invokes
the fixed AF tie fallback. A descriptive read of existing paired particle differences
finds no first value gap greater than twice its paired MC SE. Those selected-root,
finite-sample diagnostics do not prove pure sampling noise or zero target advantage;
they make finite-estimation/tie sensitivity a live alternative to useful model integration.
128/135 and61/65 diverging contexts still tie in full completed jobs. No causal job
credit is assigned to the first root, and histories after divergence are not compared
as if they remained identical. Parameter dispersion, state association, approximate
filtering and closed-loop consequences remain combined, not separately identified.

**Cost and retention.** Actual44,778 model roots initialized2,865,792 paired-branch
worlds and consumed58,432,832 model branch transitions (below188,743,680 bound), with
275,116,032 synthetic advance draws and the same number of job draws. P/U filtering
has the shared88-entry joint support; KNOW has22. Calibration collection/fitting took
.007918/.000727s; P4/U4/P32/U32 filtering sums14.3984/14.6824/14.6453/14.5784s,
planning9.4115/9.4923/9.3972/9.3631s. The scientific process reports116.092555s through
artifact hashing,122.611940 CPU seconds and62,996,480-byte peak single-process RSS;
the manifest-to-exit-witness interval is123.575550s. Final summary write and supervisor
are excluded from the scientific-process timer. Engineering, Pro, source preparation,
publication and readback are additional work, not zero; no end-to-end support total was
measured. Arm-batch times above include their filtering/environment/saving work, not the
shared calibration or all support. Roughly55× AF batch wall for P/U is an offline cost
observation, not a measured online deadline violation or deployment loss.

The durable executing-node output is the `output_root` in the launch manifest, outside
the disposable source snapshot; the complete204-file collection (10,844,290 bytes) was
copied here and independently SHA256-matched to the remote inventory. Raw artifacts
occupy9,180,567 bytes; their individual hashes/bytes/relative paths are in the summary.
Summary SHA256 is `043f9cfe970bea29b17ee995080cc83f89105e8679c5ff6e84882b16fb01b93b`.
Bulk raw traces and logs remain on that retained authoring worktree and in the verified
local collection, outside Git. The operation's source snapshot was reclaimed only after
verification: ordinary preview refused protected `/proc/660/cwd`; configured read-only
sudo process inspection then passed preview and apply. Claim, manifests, outputs,
authoring worktree and source branch remain. The completed wait event was consumed;
there is no remaining result-bearing operation.

**Working update and decision boundary.** Current main `adf68344620a2439276bdf3061b2e0e0fc94f48d`
still supports the C07/VSP distinction between an information-processing method and its
complete utility. B01 now adds a finite-knowledge counterexample to treating narrower
parameter uncertainty or frequent decision changes as sufficient for extra native gain.
It weakens the particular small-data integration prediction while preserving the ordinary
NEAR-versus-AF asset under this new population. It does not invalidate all posterior
integration, establish P/U equivalence, revive LONG or establish UAV/MARL transfer.

No confirmation or B01 extension is selected. I am deciding whether one prospective
finite-estimation comparison would change the interpretation/use enough to justify its
complete cost, versus ending this recipe and considering the parent question's other
feasible opportunities. The previous Pro answer covers this bounded result reading;
newly observed tie/MC structure and any renewed investment or route closure need a
focused follow-up at the actual choice. A positive result or a new architecture is not owed.

## 2026-09-25 — Independent reading and the finite-simulation investment question

A bounded read-only ResearchCritic independently reproduced the primary native means,
signs and intervals and found no material dissent from the bounded B01 reading. It
correctly distinguished the selected first-divergence diagnostics from evidence that
either action was erroneous, and cautioned that more particles can expose small nonzero
values and increase disagreement. It modestly favors one fresh finite-budget interaction
comparison, while declining to infer that MC hid a beneficial uncertainty mechanism.

The Critic found a useful uncensored reading in the existing records: every context's
first optional root is tick0. On this common root population the P/U action disagreement
is32/256 at k4 and10/256 at k32; estimated-value disagreement is147/256 and64/256.
DM independently verified those exact counts and identical initial tick. This preserves
the successful intermediate data-dose prediction without relying on unequal later
prefix exposure. It does not recover the failed native-benefit or native-dose prediction.
The previous paragraph's finite-knowledge example is an observed separation of these
quantities, not a theorem or population-equivalence counterexample.

I adopt the Critic's distinction between the budget interaction and each policy's own
budget response: `(U256−P256)−(U32−P32)>0` caused only by P getting worse is not evidence
that a better-resolved U improves use. Sampling precision, model approximation and AF
continuation remain different potential limits. No additional same-root rollout census
or preliminary screening study is warranted merely to establish a reason to explore.
The candidate below is a complete fresh comparison, with an initial-root diagnostic
already contained in its runs. I add one cheap AF evaluation per fresh context to keep
absolute package use visible; it is not needed to identify the four-policy interaction.

Current result/background publication is
`9fc287e0487cb66fb91b5c6eb4a84e39bafeb3cf` on main. No other direction was edited or
messaged. Current published evidence supports ordinary planning and the separation of
better estimates from native usefulness; it neither mandates another budget nor forbids
a modest direct experiment. Old C07 LONG and VSP independent-calibration routes remain
closed. Controller composition has its own owner; archived S7/spatial recipes bring no
specific new finite-model intervention here. Reopening them or inventing a UAV unknown
would cost more implementation and change more premises than the candidate below. This
is the concrete remaining local opportunity, not a claim that all broader questions are
exhausted. Prior Pro advice covers B01's interpretation, but not investment after this
newly measured finite-estimate/tie pattern. The new consultation informs that choice.

## Pro question 2026-09-25 simulation-budget-interaction-after-b01

Conversation: reuse the existing Jev conversation; its address remains only in local
transport state. This is a new scientific question after completed B01, not a resend.

**Question.** Should I buy the following single new exploration of simulation budget's
effect on uncertainty integration, or end this NEAR recipe now and preserve its bounded
result? Please decide whether the comparison would usefully change explanation or use,
and correct a decision-critical defect if present. Neither a positive result, a new
architecture nor an exact solution is owed. This is not confirmation or an extension of B01.

**Standing and what changed.** Read the two preceding dated entries and the full B01
outputs. B01 primary U4−P4 is0 total jobs (3+/4−/249 ties); k32 is+3 (3+/1−/252 ties),
both approximate intervals span0. P4 and U4 each beat AF by36 jobs with4 adverse contexts.
Calibration variance/MSE contract, and at the common tick0 root action disagreement falls
32→10 across data doses. At selected first divergences, however,121/135 and58/65 involve
an exact-zero estimate; no paired difference exceeds twice its particle SE. That last
fact is selected and does not prove noise, mistaken actions or a hidden beneficial target.
The fixed program's complete benefit is not identified by its local estimate precision.

**Candidate B02, still a proposal.** Keep k4, H96, the four-point persistent physical
parameter/prior, fixed nominal-.75 receiver, lawful shared joint physical inference,
NEAR endpoint, AF continuation and exact-zero AF fallback. Draw256 fresh independent
contexts, paired across `P_k4_M32`, `U_k4_M32`, `P_k4_M256`, `U_k4_M256`, and AF.
Here M is root-particle count, not the calibration dose. The high/low policies receive
exactly the same initial calibration and each thereafter uses its own lawful observations.
Both P and U retain identical inference; P's future law is the global posterior mean,
U samples theta conditionally on the common root state and holds it across each future.
No k32, true-model, LONG, threshold scan, new receiver or policy learner is purchased.

Use world/calibration master925831, planner master926073, phases50/51/52 and context
IDs0..255, selected now before new scores. Collect only4 controlled calibration moves
from distance33, with no saturation, then256 shared closed-form posteriors. Evaluation
and model streams remain independent. Existing per-context/tick/category RNG addressing
allows the first32 particles to be nested in256 on the same history, with separate
state, parameter, movement and job streams; verify that unchanged sampling contract.
No root-state/process truth from evaluation is available to the planner.

The primary exploratory estimand is the context mean
`I=(jobs(U_M256)−jobs(P_M256))−(jobs(U_M32)−jobs(P_M32))`.
Jointly read both U−P contrasts, `U_M256−U_M32`, `P_M256−P_M32`, every policy versus
the fresh AF row, complete adverse worlds/components, and full work. Ordinary paired
approximate intervals use n256 contexts and their actual paired differences; roots,
particles and the four nested policies add no n. Read fixed H96 endpoints once; no
score-based extension, seed replacement or extra particle values.

Tentative hypothesis: if finite root estimation materially limits the extra usefulness
of retained uncertainty, M256 may yield a positive U−P contrast and positive interaction
alongside an absolute U budget improvement. This is a conjecture, not an implication of
smaller MC SE. Equal gains in P and U instead support generic simulation value; positive
interaction solely from P loss does not establish improved U use. More stable estimates
without native improvement weaken this particular repair rationale. Mixed/sparse readings
can remain inconclusive and do not automatically trigger a larger-M scan.

At the predeclared tick0 root shared by all policies, compare the stored M32/M256
estimates/actions and paired sample SE descriptively. This uses particles already paid
for by the complete runs, no extra branches or selection on first divergent histories.
The intermediate expectation is greater estimator precision in distribution, not a
guaranteed reduction in action flips: rare-event zeros can become small signed values.
NEAR/AF continuation and the omitted peer-send likelihood remain uncorrected, so even a
positive native interaction does not isolate a pure MC, curvature or dependence mechanism.

**Prospective complete price.** 0 neural/policy fits or optimizer updates;256 closed-form
calibration fits and1,024 one-robot moves;5×256=1,280 full episodes/122,880 team ticks.
Four planner arms mean1,024 planning episodes and at most
`256*2*72*(32+256)*2*32 = 679,477,248` model branch transitions, plus sampling,
initialization,88-entry physical filtering, output and reading. Scaling B01's observed
P4/U4 branch counts by9 under unchanged visits gives210,714,624 transitions, a conditional
work estimate only. B01's P4/U4 pair took49.525907 arm-batch seconds, including29.080789
filter and18.903771 planning seconds; higher-M wall time is not measured and not assumed
to scale uniformly. Fresh AF adds256 episodes/24,576 ticks (historical256-context AF wall
.450734s is not a new guarantee). Engineering/review, preparation and consultation are
additional. One native scientific process, threads1, configured node and fresh admission;
all frozen B01 outputs remain intact. No implementation or B02 result run has started.

**Strongest alternative.** Decision-relevant target differences may be tiny or have weak
closed-loop value despite real uncertainty; approximate inference, finite NEAR and AF
continuation may dominate. True-law B01 is only2 jobs above P4, which lowers enthusiasm
but supplies no ceiling. A more precise model target may still cost more than its use.
Ending this recipe is legitimate without declaring all finite-knowledge MARL questions
solved. If a different concrete feasible next observation is materially better, explain
its changed estimand/prediction and full price; do not prescribe a generic architecture
search or a mandatory exhaustive diagnosis.

**Context and sources.** Paths marked source_sha resolve at the full question commit
supplied in the transport message; historical/frozen inputs keep their own revisions.

* Governance: `docs/project/OPERATING_CONSTITUTION.md` sections1–5 and8 at source_sha;
  independent DM owns this question and may revise it. Owner pause remains lifted except
  FSD; G33 frozen. Advice is not new authority or approval.
* Methods: `.agents/skills/hmasd-scientific-tools/SKILL.md`, sections Explore an idea,
  Update the working explanation, Statistics, Cost and exposure, Pro; and
  `.agents/skills/hmasd-research-engineering/SKILL.md`, Retain outputs and Execution.
* Current shared understanding: `docs/research/RESEARCH.md` at
  `9fc287e0487cb66fb91b5c6eb4a84e39bafeb3cf`, sections2,5,6,8 and the finite-model row.
  Its C07/VSP ordinary-method assets and bounded negative/uncertain readings inform the
  comparator and cost judgment; do not reconstruct other directions' histories.
* This notebook at source_sha: complete prior Pro answer, its adoption, B01 full result
  and independent reading above. The result entry separates observations from conjecture.
* Evidence at `69e6287ea9fd24fb9e0500b41146d5d6b39ea6e4`:
  `runs/finite_model_decision_value/b01_finite_knowledge_s925731/summary.json`,
  `episodes.json`, `common_prefix.json`, config and native manifest/status. Raw-array
  hashes and durable locations are recorded; a summary is not raw evidence. No assertion
  that Pro can inspect executing-node raw NPZ is made.
* Frozen executable B01 at `b40ea0965788f0d04b023870c34f47e86a00ceff`:
  `experiments/candidates/finite_model_decision_value/b01/{host,belief,planning,study}.py`
  and `scripts/run_fmdv_b01.py`; inspect only definitions needed for the disputed premise.

**Return.** Recommend the actual next choice with its strongest reason and alternative.
State what B01 strengthens/weakens/leaves unresolved. If retaining the comparison,
identify any necessary comparator, prediction, estimand or full-cost correction and
what each outcome could change. Do not demand a positive toy, exact headroom, same-root
census or repeated mechanism screens as admission. End `MATERIAL_DISSENT: yes/no` for
material disagreement with the proposed reading/comparison. Cite sources actually read
and state decision-critical unread gaps; no training or result simulation.

**Write contract.** On branch `codex/finite-model-decision-value-sept25`, write only the
empty `### Answer` subsection immediately below this unique question in
`docs/research/candidates/finite_model_decision_value/NOTES.md`. Read reasoning inputs
at the pinned source, but fetch the latest target blob before writing and use its actual
blob SHA. Preserve every other byte; stop on overlapping changes. Report the actual
answer commit on success. On connector failure return the complete answer in chat,
not a receipt, abbreviated summary or link. No other file edit or experiment launch.

### Answer

Saved from chat after same-key delivery verification found no repository answer. Complete collected text follows verbatim, including its source limitations and the explicit distinction between the cited file blob and an answer commit.

本轮 GitHub 读取部分可用，但没有可调用的仓库文件更新或提交动作，也未取得可用的替代写入通道。因此没有修改仓库，没有新的 Answer commit。 已重新读取指定分支：本次问题下的 ### Answer 仍为空，当前文件 blob 为 04f5ed1f3c8b82451a1a8f369390fc5e0657accb；它不是答复提交。以下给出完整答复。

读取范围有一项重要限制：episodes.json 的完整正文未能取得，common_prefix.json 未完成全量逐条审阅，执行节点上的原始 NPZ 也未读取。下面区分直接核对的汇总与源码、NOTES 中作者的完整数据归约，以及本次条件推导，不声称完成了独立原始数据审计。

Answer — simulation-budget-interaction-after-b01
一、直接建议：执行这一次五臂 B02，不在现在结束该配方

建议保留题面的五臂、256 个新 context、k4、M32/M256 和完整 H96 评价，执行这一项新的探索。主估计对象仍为预算交互 I，不替换总体、主对照、接收器、continuation 或零值回退规则。

我选择继续一次，不是因为 B01 已经证明“Monte Carlo 噪声遮住了有益的不确定性处理”，而是因为现在存在一个具体、可单独改变的计算因素，并且完整比较能够区分三种有不同使用含义的结果：更多模拟特别帮助 U、同时帮助 P/U，或者只是更精确地计算了一个没有额外完整用途的目标。现有实现已经提供了相应的配对采样与可变粒子参数，不必同时发明新的物理未知量、校准来源或控制架构。

这仍是有机会成本的研究选择，而不是必须补齐的诊断。B01 应降低对 U 特有增量的期待；B02 也可能稀疏、不利或没有足够辨别力。但题面已经把“增加计算”落实为一个完整策略比较，而不是不断追加同根采样寻找有利排序。按当前方法规范，这足以成为一次有理由的新探索，不需要先取得阳性 toy、精确 headroom 或完整机制证明。

需要落实的修正主要在实现与解释上：显式分开校准剂量 k 和粒子数 M；验证嵌套采样与逐粒子终点；将九倍分支量外推补上批内填充不变的条件；不能只按 I>0 判断采用 U。 这些不要求改变五臂科学设计。

二、B01 实际加强、削弱和留下了什么
加强：有限合法信息处理确实改变行为，普通规划包仍有有限用途

B01 中，k4 与 k32 分别有 135/256、65/256 个 context 出现 P/U 首次实际发送分歧。更重要的是，在不按后续分歧选择的共同 tick0 根上，动作分歧为 32/256 和 10/256。因此，不能把结果解释为“不确定性处理从未激活”，也不能说所有相关机会到来前不确定性都已消失。不同后期共同前缀的长度和存活范围不同，不能再把那些根的比例当作同一根总体上的受控频率比较。

完整用途与这一行为事实要分开。AF、P4、U4 的总完成量分别为 2,958、2,994、2,994；P4/U4 各比 AF 多完成 36 个任务，但各有四个不利 context，最差少完成两个任务。这个普通规划资产应保留，不因 U−P 主增量未出现而一起抹去。

削弱：小数据下保留不确定性会产生额外完成收益的预测

固定读数如下，单位是每 context 完成任务数：

B01 比较	均值	近似配对 95% 区间	正／负／平 context
U4−P4	0	[−0.030685, +0.030685]	3／4／249
U32−P32	+0.011719	[−0.008526, +0.031964]	3／1／252
(U32−P32)−(U4−P4)	+0.011719	[−0.015903, +0.039340]	5／2／249

这些数值来自固定结果条目，并与已读取的 summary 相应统计一致；它们不是等价、零效应或确认结论。

初始校准的平均参数方差由约 0.022359 降到 0.004035，参数均值 MSE 也下降；共同 tick0 的动作分歧减少。但预期的小数据原生增量，以及该增量随更多数据衰减的模式，都没有出现。U4 相对 P4 还多了 33 个等待 tick，虽然总冲突少一个、完成量相同。这正是“估计、中间行为与完整用途不是同一件事”的一个有限观察，而不是某类模型积分无效的定理。

留下：有限采样敏感性是合理解释之一，不是已定位的原因

首次分歧中，121/135 和 58/65 涉及一个精确零估值；作者对已有配对粒子的读取没有发现估值差超过其两倍配对 MC SE。它们使有限采样与 tie fallback 敏感性成为具体候选解释，但这些根经过“发生分歧”的选择，不能由此推出哪一方选错、真实优势为零，或者 U 的有益目标被噪声掩盖。

同样，KNOW_P_NEAR 只比 P4 多两个任务，会降低再投入的吸引力，却不是剩余增益上界。它仍使用有限粒子、近似物理过滤、固定接收器与 NEAR/AF continuation；该面板上它还比 U32 少两个任务。不能把知识参照的差值当作最优可达收益。

三、B02 的比较对象成立，但交互量不是采用判据

令 R
A,M,i
	​

 表示 context i 中，方法 A∈{P,U}、根预算 M∈{32,256} 的完整 H96 完成量。保留：

g
32,i
	​

=R
U,32,i
	​

−R
P,32,i
	​

,g
256,i
	​

=R
U,256,i
	​

−R
P,256,i
	​

,
u
i
	​

=R
U,256,i
	​

−R
U,32,i
	​

,p
i
	​

=R
P,256,i
	​

−R
P,32,i
	​

,
I
i
	​

=g
256,i
	​

−g
32,i
	​

=u
i
	​

−p
i
	​

.

最后一个等式直接说明：正交互可能来自 U 改善，也可能来自 P 恶化。 因而，题面要求同时读取两个 U−P、两个自身预算响应及 AF，是必要而非装饰性的。不能将主终点保留为 I，却在结果后仅展示其中最有利的一项。

hmasd-pro-question-finite-model…

P 仍是本题合适的普通主对照：它获得相同的联合推断资源，但将全局参数后验均值用于前向动力学；U 保留联合参数—状态分布。提高 M 时，不应悄悄把 P 换成更弱的点过滤器，也不应把比较写成 U256 对 P32——后者同时改变方法与预算，不能代替预算交互。当前源码确实按状态边缘共同采样，再为 U 抽取条件参数，并让该参数贯穿两机器人、两根分支及模拟未来。

“相同推断”仍指同一算法在相同合法历史上的输出相同，不是四个部署程序分叉后继续共享后验。四臂可以共用 D4，但之后必须各自消费实际收到的合法观察；不能为保持配对而跨臂复制消息或过滤状态。预算干预引起的后续历史变化，是完整策略响应的一部分。

统计上，直接对 256 个 I
i
	​

 计算均值和样本标准差除以 
256
	​

。不要将四臂区间端点相减，也不要假设四臂独立后相加方差。根 MC 随机性已进入每个 context 的完整结果，不再把根 SE 加到世界 SE 中。B01 不并入 B02 的主估计，也不拿旧低预算面板直接减新高预算面板。独立单位与近似区间的范围，按题面保持不变。

hmasd-pro-question-finite-model…

四、提高 M 的数学预测，比“更稳定的动作”窄

以下是对已读采样结构的条件推导，不是 B02 实测结果。

在同一固定合法历史 h、同一过滤分布与同一估值规则下，设单个配对粒子的 SEND−HOLD 完成差为 Z
A,j
	​

(h)。在声明的独立同分布粒子模型下，

Δ
A,M
	​

(h)=
M
1
	​

j=1
∑
M
	​

Z
A,j
	​

(h),Var(
Δ
A,M
	​

∣h)=
M
σ
A
2
	​

(h)
	​

.

因此，在目标与历史不变时，M32 到 M256 将估计量方差缩为八分之一、标准差缩为 1/
8
	​

。这里降低的是围绕该近似规划目标的采样误差，不是获得了更多真实物理知识。 k4 没变；被省略的发送似然、固定 continuation 与真实闭环之间的偏差，也没有因此消失。源码中的 NEAR 估值、联合过滤和 AF 后续策略正是这些条件的具体来源。

这不保证每个根的样本 SE 都下降：M32 可能没看到稀有非零样本，M256 才看到，此时报告的 SE 反而可能从零升高。也不保证 P/U 动作分歧减少。当前动作映射在估值零点不连续：正值 SEND、负值 HOLD、精确零使用 AF。目标很小或恰为零时，估值更接近目标，不必使动作更稳定，更不必收敛到精确计算下的 AF tie 选择。当前 threshold_requests 明确使用这个映射。

所以，我保留题面的中间预测，并作如下收紧：

在预先指定的共同 tick0 根上，更多粒子提供对相同近似目标更高的分布意义精度；已保存样本用于描述估值、配对 SE、零值状态和动作变化，不宣称已经测到了相对未知精确目标的实际误差。

配对 SE 还应使用正确的样本对象。比较 U 与 P 时，先形成同编号粒子的

D
j
	​

=Z
U,j
	​

−Z
P,j
	​

,

再计算其样本 SE，而不是把 U、P 的 SE 当独立量合并。比较嵌套预算时也不能忽略重用。例如，同一固定根上若前 32 个 D
j
	​

 包含在 256 个中，则

Var(
D
ˉ
256
	​

−
D
ˉ
32
	​

∣h)=σ
D
2
	​

(h)(
32
1
	​

−
256
1
	​

),

而不是两个均值方差之和。这是嵌套样本的代数性质，不是新的检验门槛。

tick0 是合适的有限中间读法，因为它不按后续分歧筛选；但它不能代表所有后期根。即使 tick0 精度和完整收益都改善，也不能把全程增益归给这个根。反过来，tick0 没有醒目变化，也不证明后期预算无用。无需因此购买后期同根 census。

hmasd-pro-question-finite-model…

五、需要落实的实现修正与正确性检查
最重要的具体修正：彻底分开 k 与 M

冻结 B01 的 run_study 使用：

Python
运行
dose = 32 if arm.endswith("32") else 4

来选择校准后验；collect_calibration 又明确要求 32 次校准，汇总器也绑定原六臂及两个剂量。不能只把臂名改成 P_k4_M32 等就复用这条路径，否则后缀 32 会被误读为校准剂量，或触发错误的完整性与计数逻辑。

B02 应显式记录每臂的 mode、calibration_k=4 和 particles=32/256；只生成四次位置差，只构造一个 D4 后验供四臂初始化。同步调整五臂完整性、256 次拟合、1,024 次校准移动及按各臂 M 求和的成本计数。原 B01 CLI 还固定了旧种子，因此应保留它，使用新的 B02 入口绑定题面的新种子与阶段，而不是放松旧合同。

嵌套必须核对样本及其收益，不只核对 seed

当前规划器按 context、tick 和类别分别生成状态、参数、运动和任务随机数，数组采用粒子优先布局；这支持所需的前缀嵌套设计。可是 NumPy 的正式兼容保证把请求数组大小也视为参数，并不对任意不同大小调用承诺前缀相同。因此需要在选定的执行版本上，用独立小型正确性 fixture 检查 M32 与 M256 前 32 个状态、条件参数、过程/任务抽样及最终 sample_delta 的一致性。不能仅凭“seed 相同”宣布合同成立。 
NumPy

这也应覆盖批次拆分、顺序和可选根筛选：随机地址不要包含 arm、M、批内位置或此前已消耗的根数。不同 context 的流独立性仍按声明的伪随机模型理解，不把主种子相同自动等同于只有一个实验单位。 
NumPy

保留逐粒子 NEAR 终点，而不是改成批最大终点计分

源码会为整批模拟到所需的最晚时刻，但最终用每个粒子的 near_mask 截断收益。更多粒子可能增加批内最大终点，却不应改变已有粒子的计分终点；若丢掉这个逐粒子 mask，就会把“增加 M”混成“部分粒子看得更远”。这是本题特别值得保留的检查。

其余科学不变量不需要重新设计：联合似然质量与全局归一化不变，U 的 θ 持久共享，P 使用全局均值，真实与模拟接收器都保留名义 .75，AF continuation 与精确零回退不变。不要将“置信区间包含零”改成 AF 回退，也不要增加容差零区间；那会成为另一项决策规则干预。

这些是确保执行了题面比较的工程检查，不是结果性 pilot、精确解证明或新的审批。

六、完整价格成立，但九倍外推需要补充条件

题面的主要整数核算正确：

工作	B02 前瞻数量
神经／策略 fits、optimizer updates	0
共享闭式校准 fits	256
单机器人校准移动	1,024
完整评价 episodes	1,280
实际团队 ticks	122,880
规划 episodes	1,024
模型分支转移上界	679,477,248

上界是

256×2×72×(32+256)×2×32.

其中 72 是每 episode 可选根数的保守上界，两个“2”分别对应 P/U 与 HOLD/SEND。AF 的 256 episodes、24,576 ticks 已包含在总评价量中，不要再次加到 122,880 上。

hmasd-pro-question-finite-model…

按照当前源码仍为每个粒子生成完整 H96 数组的路径，进一步的保守整数计数为：根粒子最多 10,616,832 个，配对分支模型初始化最多 21,233,664 个；运动与任务随机值各最多生成 2,038,431,744 个。这些是由上述配置和源码形状推得的数量，不是新增执行结果，也不等于内存峰值。过滤、复制、数组构造、保存和读取仍在这些计数之外。

需要修正的是 210,714,624 的条件描述，而不是否定这个量级参考。 九倍外推不仅需要旧的访问次数不变，还需要相近的每批模拟长度／填充结构。M256 可能抽到更晚的 NEAR 终点，让整批粒子执行更多转移；预算改变动作后，后续根数和过滤工作也会变。因此应将它写成“在旧访问与批内模拟长度结构均保持时的比例外推”，不能当作预期成本上界。真正的声明上界仍是 679,477,248。

B01 P4/U4 的约 49.526 秒中，过滤约 29.081 秒、规划约 18.904 秒。不能把整个时间乘九：过滤不按粒子数直接倍增，而规划又不保证线性缩放。B01 全科学进程约 116.093 秒也不是 B02 的墙钟承诺。按题面在实际运行中测量完整时间、CPU、RSS、模型根与分支、抽样、输出大小和读取成本即可，不需要为取得报价额外做结果性 profile。

若只删 AF，四格交互仍可计算，评价会降为 1,024 episodes／98,304 ticks，但主导的模型分支上界不变。鉴于 AF 在本题承担完整包用途参照，且旧实现的这部分测量成本很低，我不建议为省掉它牺牲解释；也不把历史耗时当作新保证。原始输出按现有保全方法保存，不新增记录体系。

七、各结果应改变什么，而不是只留下一个交互符号

以下是前瞻解释方向，不是新增多重显著性门槛。所有方向都要连同区间、完整差值与负尾部读取；几个点估计同号不自动构成已建立的联合结论。

完整读数模式	可以更新的判断与使用含义
g
256
	​

>0、I>0，且 U 自身预算响应 u>0	支持“在已测两个预算间，U 的额外完整用途对模拟预算敏感”的有限解释；再看 U256 相对 AF 的绝对用途与代价。不能据此追认为 B01 的失败已由纯 MC 机制解释。
P、U 都有正的自身预算响应，交互没有清楚方向	更多模拟可能有普通规划价值，但 U 特有的预算收益未建立。不能因交互接近零就宣称两种响应等价。
I>0 主要来自 P 退步，U 不改善或也退步	不支持“更充分积分让 U 变得更有用”。应记录 P 的预算敏感性，而不是用相对胜出推动 U 升级。
U 自身改善，但 U256 仍不超过 P256	支持 U 对计算有响应，不支持积分优于同预算 plug-in；普通对照的使用理由仍在。
样本估值看起来更稳定，但完整收益没有相应改善，或更多计算使用途恶化	削弱这项有限精度修复理由。保留所有有利世界，但不靠局部精度或行为分歧为继续加 M 辩护。
结果仍稀疏、区间宽或方向混合	保留“不确定”；不把它改称等价，也不自动接 M512、换 seed、改阈值或增加世界。

这张表落实的是题面已经提出的“交互、自身改善、AF 与完整后果联合读取”，不是用另一个 endpoint 替换主估计对象。

hmasd-pro-question-finite-model…

无论哪一行，都应报告每个 context 的四个规划结果、AF、I
i
	​

、自身预算差及冲突／等待／包量。总量优势不能删除不利 context，少冲突也不能代替更多完成。技术失败或缺失配对另行保留，不补零、不替换种子；不将较窄的可信事实冒充完整固定批次。

采用问题还多一步：当前并没有把每秒计算换算为多少任务损失的部署效用函数。即使完成量提高，也应将成本并列报告，而不是仅凭“涨分”称为净部署收益。反过来，离线慢很多也不是已测的在线期限违规。

八、最强停止理由成立，但此刻还不足以压过这一次具体比较

支持现在结束的最强理由是：B01 已有较多实际行为分歧，绝大多数却没有转成完成量差；KNOW 也没有显示醒目的剩余用途。再花计算可能只是更稳定地采用微小、受模型偏差影响的优势，甚至失去低预算随机性的偶然有利作用。这个理由比“没有显著性所以关闭”强得多，必须保留。

我仍选择 B02，是因为它没有同时扩展接收器、先验、环境或学习器，也没有把问题缩成一个与完整用途脱节的局部诊断。五臂结果能够直接改变下一项实际判断：是否保留低预算普通程序，是否值得增加普通规划预算，或者是否出现了 U 特有、但仍有范围限制的预算响应。所需主要采样路径已存在，工程任务具体，成本虽明显增加但已有配置上界；这比泛化地寻找新架构或重新打开旧 LONG 更直接。

这不是承诺 B02 一定能决定采用，也不是规定它之后必须继续。若没有获得足以改变使用或解释的完整收益模式，我倾向结束这条通过增加粒子修复当前 NEAR 配方的投入，保留 P/AF 和已有正反证据。即使区间还宽，这也可以是机会成本判断，而不是声称无限预算无效或所有有限模型知识问题已经解决。当前规范允许这种区分：既不以负结果自动结束科学责任，也不要求无限救援。

九、来源与未读缺口

本答复的科学输入是 82d5f663d404350990a1db9bb4a5fe68cdc26d72 的本次问题、先前 Pro 答复及采纳、B01 完整结果条目和独立读法，以及该版本的治理／方法。共享认识使用指定的 9fc287e0487cb66fb91b5c6eb4a84e39bafeb3cf；其 finite-model 行仍将 B01 记为主增量预测未获支持、下一步比较或结束尚待决定，没有把这次咨询当作已接受运行。

直接证据核对覆盖 69e6287ea9fd24fb9e0500b41146d5d6b39ea6e4 的 summary 相关统计、计数与资源字段、config、launch manifest 和 final native status。后者记录正常退出及一致的终止证据；这与 summary 的 COMPLETE 一致，但不是本次重新查询执行节点。代码使用冻结的 b40ea0965788f0d04b023870c34f47e86a00ceff，重点检查参数化 host、联合过滤、采样与终点、study 分派和原 CLI。

未完成的读取要求必须明确保留： episodes.json 的文件接口未给出可用完整正文，其他读取路径也未成功；这不证明仓库文件为空或实验失败。common_prefix.json 只检查了局部正文，未完成全部 512 条逐条复核；原始 NPZ、全部文件哈希和配对粒子 SE 没有在本次重新归约。因此，全部不利 context 与选中根诊断的全量一致性，仍依赖已读 NOTES 中作者及独立 Critic 的归约记录，而不是我的新增原始审计。这个缺口限制独立验证强度，但已读的固定汇总、结果解释和实际源码足以支持上述前瞻设计建议。

本次外部核对仅用 NumPy 官方文档说明随机流与跨数组大小兼容性的边界；它不验证 B01 的实测结果。本文的方差关系和工作量细化是明示条件下的代数与整数计算。没有运行训练、宿主／模型 rollout、B02 实验或结果性试跑，也没有接受新的实现或替代实际节点准入。

最终建议：保留并执行这一项 B02 五臂探索；修正 k/M 分派风险，核对嵌套与逐粒子终点，补充九倍成本外推的条件。用完整预算交互、自身预算响应、AF 和实际成本决定它改变了什么，不用更小的 MC SE 替代用途，也不预购后续粒子扫描。

MATERIAL_DISSENT: no

## 2026-09-25 — B02 advice read and one complete budget interaction adopted

Read the complete answer above. Same-key transport delivery was `NOT_DELIVERED`:
`04f5ed1f3c8b82451a1a8f369390fc5e0657accb` is the original notebook blob, not an
answer commit. The branch still matched question source
`82d5f663d404350990a1db9bb4a5fe68cdc26d72` with the answer empty before local
fallback insertion. The saved text is 20,630 bytes including its final newline,
SHA256 `7ed1c21afaa8f967adaafed000c6390bbd368fc03f90bd0186d14fba82a9d677`;
the observer's body hash without that newline is
`9f949f6cb4e40ae28cb26e2ba270b4e43e9b08047cd52708d6b63db90dda6289`.
Verified one verbatim copy in this notebook. No question was resent. No owned
conversation tab remained at cleanup; all five unrelated targets were preserved.
Consumed generation6 / wake `22645685-0597-4f11-9597-cfea88614b34` /
event `670f4b930430b45cf9532ac0`, rearmed generation7 with no worker restart.

**DM decision.** Adopt the proposed single five-arm B02 exploration, with all fixed
seeds, arms, k4, H96, 256 contexts, primary interaction and joint readings as stated
in the question. This is a prospective computational intervention after the weak B01
native prediction, not confirmation, a B01 extension or a diagnosis that noise hid
beneficial uncertainty. B01 remains frozen and adverse evidence carries forward.
The useful alternatives are a U-specific budget response, generic planning response,
or greater estimator precision without worthwhile complete use. The direct complete
comparison is currently a smaller premise change than a new unknown physical quantity,
receiver or learner; the AF reference preserves actual usefulness and its full cost.
No M512, seed extension, threshold tuning or later-root census is selected.

Current main `636db7ec5574081a7eade10446075eeb7f1faeaa` still lifts the project
pause except FSD, freezes G33 and assigns this question to this DM. Its shared
finite-model/estimate-versus-use reading retains the B01 limitation. The independently
completed controller-composition result does not provide a new finite-model intervention
or change the matched P comparator. No other direction or App task is taken over.

**Advice response and checked claims.** Accept the k/M separation, nested sample and
per-particle endpoint requirements. Frozen B01's arm-suffix dose parser is unsuitable;
reuse its per-arm evaluator only through an explicit B02 arm specification. Independently
checked the official [NumPy 1.26 compatibility policy](https://numpy.org/doc/1.26/reference/random/compatibility.html):
array sizes are part of RNG calls, so same seed alone does not prove prefix nesting.
Verify actual state/theta/process/job draws and credited particle outcomes on the
configured NumPy build, using correctness fixtures distinct from result contexts.
For fixed-root iid paired samples, the conditional nested-budget difference variance
is sigma-squared times `(1/32 - 1/256)`; four-policy outcome intervals instead use
the actual context interaction, without adding root SE or treating arms independently.
The precision prediction is distributional, not a guarantee that every estimated SE
or action disagreement decreases. Positive I from P deterioration alone is not improved
U use. Keep own-budget effects and every policy-minus-AF outcome, including all losses.

Correct the conditional cost extrapolation: 210,714,624 branch transitions additionally
assumes unchanged batch simulation lengths/padding as well as root visits. It is not
an upper bound. The fixed conservative model bound is 679,477,248 branch transitions,
10,616,832 root particles, 21,233,664 branch-world initializations, and at most
2,038,431,744 advance draws plus the same number of job draws. These exclude filtering,
initialization overhead, raw output, review and reading. Full exposure remains 256
closed-form fits, 1,024 calibration moves, 0 policy fits/updates, 1,280 H96 episodes
and 122,880 team ticks. Wall time is measured, not the old entire pipeline times nine.
Pro's incomplete episodes/common-prefix/raw access limits its independent audit;
the previously recorded complete DM and Critic reductions remain the evidence for
B01. Adviser agreement adds no empirical replicate. There is no material dissent.

### B02 L0 — explicit budget arms over the frozen NEAR evaluator

Deliver `experiments/candidates/finite_model_decision_value/b02/study.py`, an admitted
`scripts/run_fmdv_b02.py`, and mirrored B02 tests. Frozen B01 files are read-only.
Explicit arm records contain name, mode, `calibration_k=4`, and particles32/256;
AF is separate. The callable small-fixture Config may vary context/horizon/particle
counts, but the result CLI binds exactly the question's defaults and seeds925831/926073,
phases50/51/52, batch16 and threads1. Only four position differences from distance33
enter one shared q4 posterior per context. Each arm then consumes its own lawful
history. No new model, receiver, likelihood, RNG address, threshold or endpoint rule.

The study reuses B01 `evaluate_batch` with a per-arm Config and validates its mode
mapping; it never calls B01 `run_study` or its 32-step calibration collector. Save raw
calibration and complete trajectories, sample deltas, individual NEAR endpoints,
initial-root comparisons, all per-context outcomes/contrasts, compact summary, config,
status, counts, time/RSS and artifact hashes. Primary is paired I; include both U-P,
both own-budget effects and four planner-minus-AF readings. Initial-root diagnostics
compare actual stored particles, paired U-P SE and nested-budget variance estimates,
zero/actions and nesting; they are descriptive and buy no extra rollouts. Preserve
partial artifacts and actual completed work on failure, refusing any existing output.

Bounded Implementer ownership is the B02 study and its `test_study.py` only, with no
Git/index or notebook writes. DM owns the entry, `test_entry.py`, independent
`test_nested_sampling.py`, notebook and publication. Both use this same authoring
checkout without overlapping file/index writes. Checks cover k4 versus M32 dispatch,
five-arm pairing and context arithmetic, admitted entry, failure cost retention,
actual M32/M256 random and outcome prefixes, batch/order/optional-root invariance,
and per-particle endpoint masks. Fixture seeds differ from B02's fresh panel.
Independent high-risk review precedes DM acceptance; selected-node focused checks
precede one committed/published native launch. Stop only the dependent action on a
real semantics, ownership, resource or uncertain-operation conflict; no silent repair
of an accepted result or duplicate attempt. Remaining result/interpretation ownership
stays with this DM after implementation and collection.

## 2026-09-25 — Late repository Pro answer preserved in full

A normal push found a later answer commit after the earlier NOT_DELIVERED check.
Re-running read-only deliver with the same request key verified DELIVERED at
`a0ca3dc907551c6f476ff48df0cc8236487476a2`: only the target file changed, the
question and all other bytes were unchanged, and the answer was empty at its parent.
The earlier complete chat fallback remains above; the later repository answer follows
verbatim. Both versions are preserved in this normal merge, without force or resend.

#### 一、直接选择：保留这一次五臂 B02，而不是现在结束 NEAR 配方

**建议执行题面这一次新的、固定的五臂预算交互探索：P/U × M32/M256，加同一新面板上的 AF；保持 k4、256 个新 context 和所有既定物理、信息、接收器及 continuation 条件。** 不增加 k32、真模型、LONG、阈值或其他粒子值。我没有发现需要替换主对照或主估计对象的决策关键缺陷；需要落实的是嵌套采样及记录语义，并收紧九倍工作估算和 tick0 诊断的解释。[本次问题与完整前瞻][B02-question]

最强理由不是“MC 已经被证明掩盖了 U 的优势”，而是：**B01 已把未知判断缩小到一个可直接干预、可用完整任务读出的计算条件。** 相同推断下，U 的新增用途没有出现；同时，实际决策确实改变，精确零估值及有限样本排序仍影响程序。把 M 从 32 改为 256，并同时保留 P 的预算响应，可以区分“U 的完整用途随预算改善”“只是普通规划共同受益”“相对改善仅来自 P 变差”以及“更多模拟仍没有有用原生后果”。这些分支会改变方法使用或停止当前修复理由，不只是让一个代理指标更漂亮。

这是我对新增信息价值的有限投资判断，不是成功概率估计或预算授权。B01 的结果不会被改写；即使 B02 有利，也不能追认原 B01 假说已经成立。既有科学方法允许有明确猜想的完整探索，不要求先做阳性 toy、精确 headroom 或同根穷举；DM 仍承担实际选择、实现验收和正常节点准入。[治理与方法][B02-constitution]、[探索和成本方法][B02-methods]

#### 二、B01 改变了什么：普通规划用途保留，U 的增量解释须降温

在指定版本的完整结果条目与摘要中，AF/P4/U4/P32/U32/KNOW 的完成总数分别为 2958/2994/2994/2995/2998/2996。P4、U4 各比 AF 多 36 个任务，却各有四个不利 context。这个观察支持此总体下普通有限规划包的探索性用途，不是每个世界改善，更不是在计算成本计价后的部署支配。[B01 完整结果][B02-results]、[原生摘要][B02-summary]

主比较 U4−P4 总数为 0，3 正、4 负、249 平，近似 95% 区间为每 context [−.030685,+.030685]；k32 为总数 +3，区间 [−.008526,+.031964]。剂量交互区间也跨零。因此，“小数据时 U 有正原生增量，更多数据时增量减少”的完整预测没有得到支持；既不能用 k32 的 +3 挽救 k4 主结果，也不能由零点估计宣布两程序等价。[B01 完整结果及全部非零差值][B02-results]

这里并非没有改变决策。校准平均参数方差从 .022359153 降到 .004034720，参数均值 MSE 从 .023788144 降到 .004241332；在不受后续前缀存活影响的 tick0，动作分歧从 32/256 降到 10/256。另一方面，135/65 个发生首次实际发送分歧的 context 中，128/61 个最终仍同完成数；U4 还伴随总等待增加 33 ticks，而冲突少一个。这加强了“估计、决策响应与完整用途是不同判断”，削弱了把频繁动作差异直接当作收益机会的解释。[完整读数与独立读取条目][B02-results]、[共享背景][B02-background]

121/135、58/65 个首次分歧涉及精确零估值，且已记录的配对差没有超过两倍粒子 SE，是选择后的描述。它没有证明某个动作错误，没有证明 U 的理想根目标有正增量，也没有识别 MC 为主因。当前 KNOW 只比 P4 多两个任务，会降低对巨大知识收益的期待；但它仍是近似过滤、有限粒子和固定 continuation 的程序，不能提供剩余收益上界。

所以 B01 **加强**了普通方法资产和“中间量改善不充分”的有限反例；**削弱**了当前 M32、k4 的 U 增量预测；**留下未决**的是预算响应、近似推断、目标截断/continuation 与闭环访问变化各自的作用。不要把这些未决项都升级为必须排除的故障，也不要把它们当作负证据失效的理由。

#### 三、五臂和主交互值得保留；必须同时读取绝对预算响应

对新 context i，记完整完成数为 Y。定义

```text
D32_i  = Y(U_M32,i)  - Y(P_M32,i)
D256_i = Y(U_M256,i) - Y(P_M256,i)
G_U_i  = Y(U_M256,i) - Y(U_M32,i)
G_P_i  = Y(P_M256,i) - Y(P_M32,i)
I_i    = D256_i - D32_i = G_U_i - G_P_i.
```

这个 I 是正确的有限程序预算交互。它识别“增加预算对 U 的完整效果是否不同于对 P 的完整效果”，不是纯参数不确定性或纯 MC 机制。四个规划臂缺一，便不能在相同新 context 上直接形成此交互。特别不能拿 B01 的旧 M32 结果作为 B02 的低预算单元：那会同时改变世界、校准和规划抽样，失去题面要买的实际配对。[B02 设计][B02-question]

AF 不是交互识别的必要臂，却以不运行过滤/规划的方式保留完整包用途参照。我保留它：额外工作明确为 256 个 H96 episode、24,576 team ticks，且不增加模型分支。删除 AF 只能节约这些原生评价及相应输出，不能节约四个规划臂的主导成本。只做高预算 P/U/AF 虽更便宜，却改成“高预算内部比较”，不能回答预算交互；这不是更合适的同问题替代。

“共享推断”仍指同一合法历史下相同的过滤程序与结果，不指已分叉政策共享后验。各臂在开始时使用同一 D4，随后各自处理实际到达的包及自身观察；不跨臂复制新历史，不把两机器人的私有信息免费合并。P 的前向参数继续是全局后验均值，不改为状态条件均值、MAP 或新的点过滤流水线；否则增加 M 以外的干预。[联合过滤][B02-belief]、[根采样][B02-planning]

统计上直接对 256 个 I_i 求均值及 `sd(I_i)/sqrt(256)`；D32、D256、G_U、G_P 和各臂对 AF 同理。保留计划中的近似区间及逐 context 差值，不把相关的四臂区间独立相加，也不把根 MC SE 再加到完整结果 SE。这里的 n 是新 context，不是粒子、机器人、根数或四份政策。稀疏乃至全平局时，零样本 SE 不证明零总体效应；探索性区间也不自动形成等价、非劣或多重比较的联合确认。[统计方法][B02-methods]

#### 四、增加 M 改变的是有限决策程序，不是已知的有利目标

固定同一个合法历史 h 及其近似联合信念，记第 j 个配对模拟的 SEND−HOLD 完成数差为 Z_Aj，A 为 P 或 U。则

```text
T_A(h)       = E[Z_Aj | h]
T_hat_A,M(h) = (1/M) sum_j Z_Aj.
```

在所声明的条件独立模拟模型下，`Var(T_hat_A,M | h)=Var(Z_Aj | h)/M`；对同索引 P/U 配对差也有相同形式。因此在固定 h、固定目标、非零有限方差下，M256 相对 M32 的理论标准误尺度为 `1/sqrt(8)`。这是条件代数，不是每个观察到的样本 SE 都会下降的保证，更不是完整 Y 会提高的定理。新增样本发现原先未出现的后果时，原来为零的样本 SE 可以变成正值。

两个理想根目标 T_P(h)、T_U(h) 本身不随 M 改变；M 改变其有限估计、符号与精确零 fallback 的使用。部署中动作改变后，后续 h 与近似信念也随之改变，所以完整预算响应不仅是同一批根误差的简单平均。遗漏 peer-send 似然、有限 NEAR 目标以及 AF 模型 continuation 都没有被提高 M 修复。[前向估值及其执行语义][B02-planning]

**不要把精确零改成新的置信门槛。** 完成数差是整数，M32/M256 的样本均值有离散步长；精确零可以来自所有样本都为零，也可以来自正负抵消。已读的 `common_prefix.json` 中，context 6、k4、tick0 的 U 估值为 0，但 MC SE 约 .08980，就是不能把“零估值”一律读成“所有样本无作用”的具体例子。它不识别总体机制。[共同前缀记录][B02-prefix]

因此保留阈值零、精确零回到 AF。不要附加“超过两倍 SE 才行动”、epsilon tie、只信高 M 或事后改 fallback；这些会购买另一个策略。M256 可能使动作分歧增加，因为过去触发 AF 的零均值变成很小的负值。这既不自动是改进，也不自动是实现错误。B02 应检验其完整后果，而非预先要求分歧减少。

#### 五、tick0 诊断合适，但其范围及嵌套协方差要写清

保留所有 256 个 context 的 tick0，不按首次分歧、非零 SE 或估值符号筛选。它提供一个未受后续策略分叉选择的共同历史切面，足以描述初始有限估计如何响应 M；它不是整个 H96 所有决策机会的代表样本。

更具体地，冻结 `JointPhysicalBelief` 在 t0 将每个 θ 的质量按原始七个 SHARED approach 距离均分。因此初始信念为 `q4(theta) × b0(x)`，此处 θ 与隐藏 peer 初态独立。tick0 可以检验不确定动力学积分与均值动力学在该初始机会的有限估值，却**不能诊断后续状态—参数关联的贡献、在线识别速度或状态依赖发送被忽略的影响**。这只是明确诊断范围，不要求增加后期同根 census。[初始联合信念定义][B02-belief]

冻结采样代码确实分别为状态、参数、运动及任务构造按 context/tick/category 编址的流，并以 particle 为完整未来数组的首轴；P/U 先共享状态样本，U 再条件抽 θ。这支持题面嵌套方案，但应对实际运行版本作小型固定输入检查，不能仅以“seed 相同”代替验证。[采样定义][B02-planning]

检查应确认同一 h 下，M256 前 32 个粒子的四类输入、根状态、相应参数和逐粒子 masked SEND/HOLD 收益等于 M32；允许高 M 为其他粒子多执行 padding，但不能改变前 32 个粒子的计分端点。U 的一个 θ 仍贯穿两机器人、两分支和整个未来；P 不采用 U 的条件 θ。分叉之后只保留地址配对，不再声称根历史或样本分布相同。这些是本次改动的正确性检查，不是结果性前置研究。

在 tick0 的统计描述中，高低 M 不是独立估值。例如令 `d_j=Z_Uj−Z_Pj`，则真正嵌套时有

```text
mean(d_1:256) - mean(d_1:32)
    = (7/8) * [mean(d_33:256) - mean(d_1:32)].
```

这可直接用已付费样本检查，也说明不能把高低 M 的 SE 按独立观测平方相加。P/U 的差应使用 `sd(d_j)/sqrt(M)`，而不是忽略共同随机数的协方差。M256 仍不是精确真值：一次嵌套比较能描述精度与动作响应，不能据此认定 M32 动作“错了”，也不要求新增独立模拟流来证明稳定性。

#### 六、完整价格成立；九倍数值还需要一个明确条件

题面的核心整数预算正确，保留如下范围：

| 工作 | B02 前瞻总量 |
| --- | ---: |
| 独立新 context | 256 |
| 实际校准 | 1,024 个单机器人运动步；256 次闭式后验计算 |
| 神经/策略 fits；optimizer updates | 0；0 |
| 完整评价 | 1,280 episodes；122,880 team ticks |
| 规划 episode；可选根保守上界 | 1,024；73,728 |
| 模型分支转移保守上界 | 679,477,248 |

分支上界为 `256*2*72*(32+256)*2*32`。其中前一个 2 是 P/U，后一个 2 是 HOLD/SEND，末尾 32 是模拟时域上界，不是第二个 M32。校准的单机器人步与评价 team ticks 分开记录；不把两者混称为同一种环境步。新研究只收集四次，不能继续沿旧 B01 路径实际收集 32 次却仅计四次。[前瞻价格][B02-question]、[冻结收集与运行实现][B02-study]

**必要的估算澄清：210,714,624 是条件性工作估算，不仅需要相同访问根，还需要相同实际补算长度。** 当前 NEAR 以批内所需最远端点决定模型执行长度，再按粒子自己的端点 mask 计分。更多粒子可能把批内最远端点向后推，即使实际 root 没变，模型工作也可能偏离简单八倍；政策路径和根数变化又增加一层差异。因此将旧 P4/U4 的 23,412,736 分支乘以九，应该注明“低/高预算具有相应相同根工作及 padding 时的比例外推”，不称为预测保证或预算上限。679,477,248 的保守上界仍有效。[模型执行与计分][B02-planning]

全 H96 合成数组也不能漏计。若保持当前实现，在最大可选根数下，四臂共至多 10,616,832 个根粒子实例，初始化至多 21,233,664 个分支模型世界；运动随机数与任务抽样各至多 2,038,431,744 个标量。这里“各”不能合并漏掉一类。这些是同一保守配置下的计数，不是实际访问量，也没有增加原定分支预算；状态/参数采样、CDF、复制及输出还在其外。

B01 的 P4/U4 合计约 49.525907 arm-batch 秒，过滤约 29.080789 秒、规划约 18.903771 秒。B02 有四份完整过滤轨迹，而不是把过滤重复八次；规划、全数组构造及存储才更直接受 M 影响。即使暂用“不改变访问”的近似，也不能把 49.525907 整体乘九当墙钟。保留每臂过滤/规划/环境与保存、校准/拟合、全进程 wall/CPU/RSS、实际根/分支/抽样及字节；准备、审阅、咨询和读取另计。新的 M256 墙钟、RSS 与支持总成本目前未知。[已完成成本记录][B02-results]

同粒子数是 P/U 规划曝光匹配，不是保证等墙钟或等方差；高低 M 本来就是不等计算的干预。没有给出把计算折算成完成任务的使用目标，就把收益与成本并列，不制造净效用分数或在线期限。也不需要为取得时间报价另买一个结果性 profile/pilot。[成本及保全方法][B02-methods]、[输出与执行方法][B02-engineering]

#### 七、预先说明每类结果会改变什么，而不是预先要求通过

| B02 完整读数 | 对解释及当前方法使用的影响 |
| --- | --- |
| D256 为正、I 为正，且 G_U 为正 | 与“这一预算增加改善 U 的额外完整用途”相容；还要读新 AF、负尾部和额外成本。可保留这个 M256 有限实例，不追认 B01，也不识别纯 MC/曲率/关联机制。 |
| P、U 均有近似相同的预算增益，I 很小或不确定 | 更符合普通模拟预算共同有用；没有不确定性积分的选择性收益证据。按完整收益和成本看较简单选择，不能由不显著宣布效果相等。 |
| I 为正主要或完全因为 P 变差，U 不改善 | 交互算术成立，但 U 修复预测未成立；不能以相对排名掩盖绝对损失，也不将高 M 自动提升为采用方案。 |
| 根估计更精细或零估值更少，但 U 无原生增益、甚至退步 | 削弱“多粒子能把 U 的估值变化转成完整用途”的这一具体修复理由；并不证明原目标精确为零，也不唯一诊断过滤或 continuation。 |
| D256 有正观察，但 G_U/I 或 AF 比较不支持相应预测 | 分别保留高预算内部比较、预算响应与完整包用途，不能只截取有利的一项；若不值得额外计算，可以保留较低预算/AF 参照。 |
| 差异仍稀疏、区间宽或方向混合 | 当前预算的结果仍不确定。结束此修复投入可以基于下一份信息不值得其成本，而不能写成等价、无 headroom 或全部有限知识方法无效。 |
| 技术失败、缺失配对或不完整计分 | 保留原操作与可信部分；不补零、不换 seed、不把部分结果当固定 n256 完成，也不自动追加或重跑。 |

这些是判读分支，不是一套新显著性合取门槛。尤其“正交互＋U 自身改善＋高预算 U−P”应连同各自的不确定性陈述，而不是三个正点估计就称为确认。所有 context 的冲突、等待、完成数和包量都保留；相同完成数不表示相同轨迹，少冲突也不一定提高完整任务收益。

**最强替代仍是现在结束这条 NEAR 配方。** 支持它的理由很实在：只有七个 k4 context 的完成数有差；大量实际发送分歧没有转成任务差；KNOW 的有限参照也未显示很大增量；更准地估计一个近似、截断、固定 continuation 的目标可能只会增加成本。现在停止新增工作为零 fits、零新校准/评价/分支，但保留解释和发布的成本；不是否定母问题。

我仍选择这一批，是因为与改 receiver、加精确信念、换宿主或增加神经学习器相比，它只改变一个已明确、可实现的计算维度，保留强普通对照，并直接读取完整后果。只做大量根重复模拟会更直接测局部估计方差，却不能回答完整预算用途，当前不比五臂部署比较更值得购买。我不提出未完整定价的其他实验，也不把 B02 的任何结果变成 M512/M1024 扫描的起点。

#### 八、来源边界与交付范围

本次采用问题固定来源 `82d5f663d404350990a1db9bb4a5fe68cdc26d72` 的完整问题、先前完整 Answer、DM 采纳、B01 完整结果及独立读取条目；治理与指定方法也按此来源。共享背景按题目另指定的 `9fc287e0487cb66fb91b5c6eb4a84e39bafeb3cf`，不是用移动分支的新结论替换科学输入。冻结执行定义按 `b40ea0965788f0d04b023870c34f47e86a00ceff` 阅读，重点是联合过滤、初始分布、四类随机流、持久 θ、NEAR mask 和 runner 数据/粒子配置。

原生证据采用 `69e6287ea9fd24fb9e0500b41146d5d6b39ea6e4`。GitHub 对部分大文件的内容/原始读取发生空正文、截断或 RPC 错误；后续读取取得了摘要、逐 context 表及共同前缀正文的可读内容，并核对了 config 与 native manifest/status。**没有在本次独立遍历、重新归约全部共同前缀记录或执行节点的原始 NPZ，也没有重验所有 197 个制品哈希。** 本文的完整统计、全部分歧计数及校准归约采用已读固定 NOTES 中 DM 的完整读取；具体示例和程序定义另由已读内容核对，不把摘要当作原始轨迹审计。该缺口限制独立全量复核的声明，不改变本次依据已发表读数作设计/投入建议的范围。[结果与独立读取][B02-results]、[原生运行清单][B02-manifest]

B02 尚无实现验收、M256 实测成本或新结果；本次没有启动训练、校准、环境评价、模型 rollout 或结果性试跑。上述方差和计数是条件推导/整数核算，不是实验。建议只覆盖这一项前瞻探索，不改变冻结 B01、旧 LONG/VSP、其他方向 ownership、FSD 暂停或 G33 冻结。

**最终建议：保留五臂 B02，按当前信息与控制合同执行一次完整新探索；采用上述成本条件和有限诊断范围，随后由原生预算响应、对 AF 的用途及全成本决定保留或结束，而不是把更精确估值本身当作继续投资的理由。**

[B02-question]: https://github.com/CartmanFatass/My-paper-code/blob/82d5f663d404350990a1db9bb4a5fe68cdc26d72/docs/research/candidates/finite_model_decision_value/NOTES.md#pro-question-2026-09-25-simulation-budget-interaction-after-b01
[B02-results]: https://github.com/CartmanFatass/My-paper-code/blob/82d5f663d404350990a1db9bb4a5fe68cdc26d72/docs/research/candidates/finite_model_decision_value/NOTES.md#2026-09-25--b01-complete-decision-changes-without-the-predicted-small-data-native-gain
[B02-summary]: https://github.com/CartmanFatass/My-paper-code/blob/69e6287ea9fd24fb9e0500b41146d5d6b39ea6e4/runs/finite_model_decision_value/b01_finite_knowledge_s925731/summary.json
[B02-prefix]: https://github.com/CartmanFatass/My-paper-code/blob/69e6287ea9fd24fb9e0500b41146d5d6b39ea6e4/runs/finite_model_decision_value/b01_finite_knowledge_s925731/common_prefix.json
[B02-manifest]: https://github.com/CartmanFatass/My-paper-code/blob/69e6287ea9fd24fb9e0500b41146d5d6b39ea6e4/runs/finite_model_decision_value/b01_finite_knowledge_s925731/launch-manifest.json
[B02-planning]: https://github.com/CartmanFatass/My-paper-code/blob/b40ea0965788f0d04b023870c34f47e86a00ceff/experiments/candidates/finite_model_decision_value/b01/planning.py
[B02-belief]: https://github.com/CartmanFatass/My-paper-code/blob/b40ea0965788f0d04b023870c34f47e86a00ceff/experiments/candidates/finite_model_decision_value/b01/belief.py
[B02-study]: https://github.com/CartmanFatass/My-paper-code/blob/b40ea0965788f0d04b023870c34f47e86a00ceff/experiments/candidates/finite_model_decision_value/b01/study.py
[B02-background]: https://github.com/CartmanFatass/My-paper-code/blob/9fc287e0487cb66fb91b5c6eb4a84e39bafeb3cf/docs/research/RESEARCH.md
[B02-constitution]: https://github.com/CartmanFatass/My-paper-code/blob/82d5f663d404350990a1db9bb4a5fe68cdc26d72/docs/project/OPERATING_CONSTITUTION.md
[B02-methods]: https://github.com/CartmanFatass/My-paper-code/blob/82d5f663d404350990a1db9bb4a5fe68cdc26d72/.agents/skills/hmasd-scientific-tools/SKILL.md
[B02-engineering]: https://github.com/CartmanFatass/My-paper-code/blob/82d5f663d404350990a1db9bb4a5fe68cdc26d72/.agents/skills/hmasd-research-engineering/SKILL.md

MATERIAL_DISSENT: no

## 2026-09-25 — Late answer read; B02 decision and L0 retained

Read all 10,644 characters of the delivered answer. It retains the five-arm comparison,
primary interaction, interpretation limits and cost correction; no material dissent or
changed scientific plan. The updated source boundary says later reads obtained the
episodes table and more common-prefix text, but still no exhaustive raw/hash reduction;
this does not convert either answer into an independent raw audit.

Verified its additional concrete point in frozen belief initialization: at tick0, each
parameter has q4/7 mass on each of the seven SHARED approach distances. Thus tick0
is a factorized q4(theta)*b0(state) slice and cannot test later parameter-state
dependence, online identification or the omitted send likelihood. Verified its example
against the preserved common-prefix record: context6/k4/tick0 has U delta0 and
MC SE .08980265259742737. An exact-zero mean does not imply all-zero particles.
These points refine the already planned descriptive initial-root reading; they do not
add a later-root census, new threshold or result exposure. The adopted L0 above stands.

## 2026-09-25 — B02 implementation accepted for the fixed prospective run

Accepted the bounded Implementer's new study after DM inspection and independent
high-risk review. All B01 host, filter, planner, study, CLI and tests match their
frozen `b40ea0965788f0d04b023870c34f47e86a00ceff` bytes. B02 uses explicit
`P_k4_M32/U_k4_M32/P_k4_M256/U_k4_M256/AF` specifications; four observed moves
initialize q4 and each deployed arm updates only its own legal history. The primary
and native component contrasts are computed from complete paired context outcomes.
All-context tick0 diagnostics consume existing samples, with no extra model rolls.

DM review repaired four implementation issues before any B02 result operation:
allow the native-prepared output root while refusing existing scientific files;
hash only study-owned artifacts rather than changing native logs; require exactly
contexts0..255 in every arm rather than accepting a jointly missing context; and
pin reuse to the original B01 SHA. The independent Reviewer verified these repairs
and reported no remaining material finding. The common native admission call precedes
scientific imports/output and rejects missing admission, mismatched SHA and other seeds.

All9 B02 correctness checks passed locally (Implementer1.57s; independent Reviewer1.59s).
Fixtures use unrelated seeds and small complete H48 panels; the RNG/endpoint checks
also use actual M32/M256 with H96 at fixed correctness roots. They verify all four
RNG stream prefixes, conditional theta/state sampling, batch split/reorder/selected-root
invariance, individual HOLD/SEND and delta credit, and a forced extra slow particle
that expands batch padding16->32 without expanding the first32 particles' credited
endpoints. Complete five-arm counts/hashes, independent contrast arithmetic and partial
second-arm failure retention also pass. They are correctness exposure, not B02 outcomes.

An additional combined run was10 passed/1 failed in1.73s: the failure is the existing
repository-wide admission AST scan at unchanged
`scripts/run_fsd_commitment_visibility_b12.py` (blob
`0eeae9f93d1a3d500a202cd7c57379fdfd7ac897`), which lacks the scanned direct call.
The B02 AST/native boundary and all B02 tests pass. FSD is paused, its file is unchanged,
and no unrelated repair or result execution is introduced. Abrupt termination and
total metadata-write failure remain outside the exception-retention fixture.

Published the material B02 plan independently to main at
`6d2e2ff3e18d5b1fcadeaa89272cf724f15613fc`, preserving other writers and controls.
The configured wsl_4070 reports Python3.10.21/NumPy1.26.3; prepare a new source
worktree there and check these focused tests on that actual interpreter before launch.
Remote fetch succeeds through the configured login shell; its pre-existing Git gc
bad-tree warning persists and does not establish whole-repository integrity. Required
input materialization and the native source/admission checks still apply.

Fixed result tag: `b02_budget_interaction_s925831`. One CPU scientific process,
threads1, original seeds/phases/n256/H96/arms and full cost bound above. Native fresh
resource admission remains before execution. No B02 result has been launched or read;
this commit publishes the exact accepted inputs, and the eventual manifest binds its SHA.

## 2026-09-25 — B02 pre-admission control refresh; no scientific attempt yet

Exact input source is `5b5d73100ae8554b8005758055b181d03fb6603e`. Its new remote
authoring checkout is clean and all9 B02 tests passed there in1.36s on the configured
Python3.10.21/NumPy1.26.3. Latest published controls still lift pause except FSD,
retain this lead and leave two selected research tracks within the three-track ceiling.

The first outer supervisor command (`fmdv-b02-sept25-s925831`) exited4 after17s:
`canonical control checkout has not fetched the published control head; sync it before launch`.
Main had advanced after the earlier remote fetch. Read the full supervisor log and
the launch source ordering: this refusal precedes claim reservation and worker spawn.
Read-only reconciliation found no B02 output/status root and zero matching native
claims. Thus there is no accepted operation or worker to restart, and0 scientific
fits/calibration/evaluation/model work occurred. Preserve the supervisor log in private
scratch and its original durable node task path; it is a technical pre-launch failure.

DM chooses to fetch the new published control commit and resubmit the identical
scientific request after the missing-control condition is resolved. Source, output
tag, world/model seeds, exposure and expected lead stay fixed; only the outer command
label distinguishes this post-refresh submission and preserves the first log. This
does not replace a terminal accepted operation or bypass its native claim. Any subsequent
accepted/uncertain handle must be reconciled as itself without another worker launch.

## 2026-09-25 — B02 admitted and observing the original operation

After fetching published control head `fc3778b9ac3bb46add596f62bd6327106cfc21dc`,
the identical request was accepted on wsl_4070. The
[native manifest](../../../../runs/finite_model_decision_value/b02_budget_interaction_s925831/launch-manifest.json)
binds source `5b5d73100ae8554b8005758055b181d03fb6603e`, the native claim,
snapshot and stable output root. The copied
[fresh memory preflight](../../../../runs/finite_model_decision_value/b02_budget_interaction_s925831/admission-preflight.json)
passed with14,967,615,488 available bytes versus the4GiB floor. The
[initial native status](../../../../runs/finite_model_decision_value/b02_budget_interaction_s925831/native-status.initial.json)
reports accepted admission, consistent records and running scientific/supervisor
identities; summary and exit witness were absent at that observation. This is
technical admission, with no B02 endpoint reading or scientific acceptance yet.

The task-local wait controller observes this exact native claim with the new B02
launch job; prior Pro/B01 terminal jobs remain consumed. At completion or checkpoint,
drain and reconcile this same handle, preserving failure or missing evidence. Collect
and verify all required raw/native outputs, full paired outcomes, initial-root diagnostics
and actual cost before the scientific reading. No restart, replacement seed, changed
budget, extra root census or score-based continuation is authorized by an observation.

## 2026-09-25 — B02 complete: precision changed, native budget response remains small and uncertain

The original admitted operation completed with exit0, a valid native exit witness,
absent runner/supervisor identities and consistent records. Read the full structured
[summary](../../../../runs/finite_model_decision_value/b02_budget_interaction_s925831/summary.json),
[episodes](../../../../runs/finite_model_decision_value/b02_budget_interaction_s925831/episodes.json),
[paired context readings](../../../../runs/finite_model_decision_value/b02_budget_interaction_s925831/per_context.json)
and [all initial-root diagnostics](../../../../runs/finite_model_decision_value/b02_budget_interaction_s925831/initial_roots.json).
The [final native status](../../../../runs/finite_model_decision_value/b02_budget_interaction_s925831/native-status.final.json)
reconciles the accepted handle; its process exit alone was not scientific acceptance.
No seed, arm, horizon, threshold, fallback or output was replaced or extended.

**Integrity and reading.** Copied all173 remote files,13,006,919 bytes, and matched
all byte counts/SHA256 values against an independently read remote inventory. Also
verified all166 runner-manifest artifacts. Independently reconstructed all1,280 raw
H96 endpoints, cumulative completion rewards and packet counts; matched all256 initial
histories/joint weights, both exact M32 prefixes of M256 sample deltas/endpoints, all
45 contrast-metric reductions and context entries, and every actual model root/branch/
initialization/draw count from the raw eligibility masks and per-batch simulation lengths.
Recomputed q4 using observed position differences and log likelihood, never hidden
success flags. Every arm has contexts0..255,14 jobs started and24 packets per context.
The scientific config exactly matches the five-arm contract and input
`5b5d73100ae8554b8005758055b181d03fb6603e`; stdout/stderr are empty.

The readback's first strict MC-SE equality check used float64 reduction on stored
float64 samples and exposed only the inherited float32 reduction rounding. Recomputing
in the planner's actual float32 dtype matches every stored SE exactly; maximum float64
versus stored difference is1.11634e-8. No action, endpoint or result was repaired.

### Fixed primary reading and all required complete comparisons

Here P/U32/256 abbreviate the explicit k4 arms, not calibration doses. Every interval
is the predeclared paired normal approximation over256 new contexts; particles, roots,
agents and nested policies add no independent n. The sparse sample and zero/tied rows
are not equivalence or confirmation. B01 is not pooled into these estimates.

| Completed-jobs comparison | Total difference | Mean per context | Approximate95% interval | Positive / negative / tied |
| --- | ---: | ---: | --- | --- |
| I = (U256−P256)−(U32−P32) | +4 | +0.01562500 | [-0.01686479, +0.04811479] | 7 / 2 / 247 |
| U32−P32 | -1 | -0.00390625 | [-0.01718459, +0.00937209] | 1 / 2 / 253 |
| U256−P256 | +3 | +0.01171875 | [-0.01590290, +0.03934040] | 5 / 2 / 249 |
| U256−U32 | +4 | +0.01562500 | [-0.01686479, +0.04811479] | 10 / 5 / 241 |
| P256−P32 | +0 | +0.00000000 | [-0.03254635, +0.03254635] | 8 / 7 / 241 |
| P32−AF | +32 | +0.12500000 | [+0.06862807, +0.18137193] | 25 / 3 / 228 |
| U32−AF | +31 | +0.12109375 | [+0.06511672, +0.17707078] | 24 / 3 / 229 |
| P256−AF | +32 | +0.12500000 | [+0.06363002, +0.18636998] | 29 / 6 / 221 |
| U256−AF | +35 | +0.13671875 | [+0.07719123, +0.19624627] | 30 / 5 / 221 |

Total completed jobs are AF2824, P32=2856, U32=2855, P256=2856 and U256=2859.
All three conjectured native point-estimate signs (I, U256−P256 and U's own budget
response) are positive. This is weak, directionally compatible evidence, not a
falsification of their signs and not an established useful repair. Each interval
includes0; the high-budget U−P is nonzero in only7 contexts. A context-level statement
that ordinary planning helps must retain AF losses and its much greater compute.

The positive interaction has heterogeneous origins. Contexts22/31/95/176 contribute
+5 interaction jobs through P worsening while U is unchanged;70/82/245 contribute+3
through U improving. Context120 has U−1 and P+1 (I−2);137 has U−2 and P0 (I−2).
Across the whole panel P's budget total is0 and U's is+4, so the aggregate is not solely
P degradation. Across the nine interaction-bearing contexts, however, U's budget total
is0 and P's is−4; the remaining contexts share a net+4 budget change in each policy.
Neither decomposition identifies a pure noise or uncertainty-integration mechanism.

All nonzero primary/U−P completed-job differences, as context:signed jobs:

I = (U256−P256)−(U32−P32): 22:+2, 31:+1, 70:+1, 82:+1, 95:+1, 120:-2, 137:-2, 176:+1, 245:+1.

U32−P32: 31:-1, 120:+1, 176:-1.

U256−P256: 22:+2, 70:+1, 82:+1, 95:+1, 120:-1, 137:-2, 245:+1.

Own-budget losses remain P:22(−2),31/38/95/149/176/188(−1);
U:137(−2),38/120/149/188(−1). Against AF, adverse contexts are
P32:70/120/220(−1); U32:31/70/220(−1); P256:22(−2),31/38/70/149/188(−1);
U256:31/38/120/149/188(−1). All favorable and adverse components remain in the
complete linked per-context table; no world is discarded for an inconvenient reading.

Greater budget reduces total waits by84 for P and91 for U: means−.328125
[−.477357,−.178893] and−.355469[−.524001,−.186936] per context. The wait interaction
is−.027344[−.144392,+.089705], and each high-budget policy has one additional conflict.
Both are real native components, but the generic waiting reduction does not replace the
completed-jobs endpoint or establish a U-selective effect. All arms use6,144 packets.
Parameter-stratum counts .35/.55/.75/.95 are79/58/56/63; their I totals are+2/+4/−2/0.
These are random realized strata, not balanced blocks or additional training replicates.

### Intermediate prediction and its limits

All256 predeclared common tick0 roots have identical initial legal records and q4,
and verified nested samples/endpoints. Their initial theta variance averages.021813787,
parameter-mean MSE .022781398. At this root q4(theta) and hidden peer state factorize.
It does not test later parameter-state dependence or identify the missing send likelihood.

| Tick0 description | M32 | M256 |
| --- | ---: | ---: |
| P mean reported particle SE | .0568470 | .0245918 |
| U mean reported particle SE | .0591957 | .0247015 |
| Paired U−P mean reported particle SE | .0504536 | .0225052 |
| P RMS reported particle SE | .0792975 | .0287417 |
| U RMS reported particle SE | .0799466 | .0286400 |
| Paired U−P RMS reported particle SE | .0694745 | .0246278 |
| P exact-zero means / all-zero particle sets |114 /109|16 /10|
| U exact-zero means / all-zero particle sets |104 /99|16 /8|
| P sends / U sends |216 /213|173 /177|
| U/P action disagreements |25|32|

P changes53 initial actions and U46;47/38 of those involve an exact-zero estimate.
P/U/paired SE decrease at147/157/152 roots, increase at99/91/100 and tie at10/8/4.
Every increase starts from a zero low-budget SE. The precision intervention therefore
changed the finite estimator in the intended limited sense, with rare outcomes absent
from M32 appearing in M256; it did not promise fewer disagreements or every SE falling.
These are sample-based precision descriptions, not observed error against an exact
model target. No extra diagnostic rollout was purchased. Smaller SE and fewer zeros
coexist with a small uncertain differential completion effect and adverse worlds.
The data weaken the rationale for a readily useful MC-budget repair; they do not
identify approximate filtering, NEAR/AF continuation or closed-loop response as its cause.

### Complete cost, retention and independent reading

Started/completed256 closed-form calibration fits,1,024 single-robot calibration moves,
0 policy/neural fits or parameter/optimizer updates;1,280 complete episodes and122,880
team ticks. Actual model work is36,428 roots,5,307,456 root particles,10,614,912 branch
world initializations and215,389,184 branch transitions (bound679,477,248). Synthetic
advance and job draws are each1,019,031,552. The old210,714,624 conditional extrapolation
was not a bound; changed root visits and batch padding were explicitly permitted.

| Arm | Sum of arm-batch wall seconds | Filtering seconds | Planning seconds |
| --- | ---: | ---: | ---: |
| P_k4_M32 | 22.509729 | 13.183812 | 8.647278 |
| U_k4_M32 | 22.473792 | 13.134860 | 8.658137 |
| P_k4_M256 | 51.564095 | 13.443885 | 37.120021 |
| U_k4_M256 | 51.596460 | 13.404638 | 37.188595 |
| AF | 0.374633 | 0.000000 | 0.000000 |

Full scientific process wall through artifact hashing149.267414s, CPU158.123655s,
peak single-process RSS92,508,160 bytes, raw artifacts11,060,483 bytes. Manifest-to-exit
elapsed157.116284s additionally includes native startup/finalization; the separate
pre-admission refusal cost17s and no scientific work. Measured file collection/verification
was4.189881s. Preparation, fixture checks, code/independent review, Pro consultation and
scientific reading are additional support work, not zero or included in the scientific
wall. No full human/agent effort or general speedup claim is made. Each high-budget arm
cost about2.29x its low-budget arm wall, rather than8x/9x the whole pipeline. AF wall
is .374633s; these are offline batch costs, not an invented deployment deadline.

Durable complete outputs remain on wsl_4070 at
`/home/wu/hmasd-worktrees/fmdv-b02-sept25/runs/finite_model_decision_value/b02_budget_interaction_s925831/`,
with the fully verified local collection in the linked run directory. Compact config,
summary, per-context/episode/initial-root results and native records are versioned;
raw NPZ and logs remain at both recorded locations with runner artifact hashes.
Summary SHA256 `f6ce8b8b3fec1c5fb30808ad135a1bf0e3918756d67a93af73294d27d6085444`.
Only source snapshot `3a57f2b7358f44d7b8265c462443e3a6` was reclaimed after eligible
preview and apply with the permitted read-only sudo process scan; the collector verified
terminal identities, durable Git reachability and preserved outputs. Claims, authoring
checkout and native/raw evidence remain. Generation8 / wake
`68dc3241-c10f-4d33-957b-8f884807a1ba` / event `4457aaffb45d2d4e3d481340` was
consumed and rearmed as generation9, with no remaining active observation job.

The independent ResearchCritic rederived all45 contrast-metric readings from the full
JSON evidence, inspected all initial-root summaries and the heterogeneous interaction,
and agreed with the weak compatible reading above. It favors ending additional MC
rescue investment absent a concrete use decision that recurrence would change.
It did not repeat the exhaustive NPZ/hash audit or query the node; its review adds no
new empirical replicate. MATERIAL_DISSENT: no. DM independently accepts this complete
fixed result and retains the positive, adverse and unresolved observations.

## 2026-09-25 — End current NEAR budget-repair investment; retain the finite result

**Decision.** End the current finite-knowledge NEAR recipe's additional investment and
archive this direction for current investment. Retain ordinary P32/AF as useful assets,
the full U/M256 observations and the shared waiting response; do not elevate a small
uncertain differential to a new default or suppress its favorable point estimates.
This closes the tested recipe and the presently selected work, not the general question
of when finite model knowledge helps MARL/UAV decisions. No confirmation, further
simulation budget, extra contexts or selected successor is pending, and there is no
external dependency being used to defer this choice.

Reuse the complete Pro advice already read above, including the delivered answer at
`a0ca3dc907551c6f476ff48df0cc8236487476a2`, sections4–7 and its explicit branches for
joint positive points, sparse/mixed native readings, precision without decisive complete
utility, and ending investment without an equivalence claim. Those cases cover this
fixed comparison and the present keep/end decision; the physical/comparator premises
have not changed. Its advice did not require another per-batch consultation. This is
DM's information-value choice, not an adviser approval or a conclusion inferred from
process completion. The Critic's agreement does not replace that prior Pro consultation.

The intermediate intervention worked: more simulations resolve many sample zeros and
reduce aggregate reported uncertainty. The native response is weakly compatible with
U-specific value, yet rare, heterogeneous and too uncertain to locate a robust method
advantage. I therefore lower enthusiasm for further MC rescue, rather than calling the
prediction falsified or the methods equivalent. The ordinary P-versus-AF completed-job
asset recurs on this new panel (+32 versus B01 +36); different context populations and
B01 dose arms remain separate evidence, not a pooled confirmatory test. Native waiting
improves in both budget arms and remains a secondary useful observation.

Considered what could be done next beyond merely ending this batch:

* M512/M1024 or a changed tie threshold has no distinct currently supported complete-use
  prediction beyond making the same approximate target more precise or changing policy.
  The former link was exercised; the latter would add a new intervention without a
  located native bottleneck. Neither is selected.
* An unchanged fresh comparison at the existing budgets is feasible, and measured149s
  means machine cost alone is not prohibitive. It could sharpen this simulator's small
  effect or test recurrence. I do not buy it now: no concrete method-use choice currently
  turns on that small difference, and it would not distinguish the surviving target,
  inference and closed-loop explanations. This is opportunity-cost judgment, not a
  post-hoc equivalence margin or a claim that replication has no information.
* Incorporating policy-conditioned send/silence likelihood or changing NEAR/continuation
  would test a different model/decision bias. Neither has been diagnosed by B02. Exact
  recursive teammate-policy likelihood, longer branches or a new receiver are not
  obligatory repairs; no narrow, fully specified comparison here is presently more
  useful than retaining the bounded result. A direct learner/UAV test remains possible,
  but choosing a new unknown law, host and training comparison would introduce premises
  that these two panels do not currently select. No generic architecture proposal or
  positive-toy prerequisite is substituted for that missing research reason.
* Current shared main retains controller-composition's separately owned direct partner
  training question; this DM does not take it. Closed S7/spatial recipes and other
  reserve questions retain their own adverse constraints. B02 supplies no new evidence
  that would make reopening them, or renaming this MC repair, worthwhile now. Reading
  them as alternatives does not create a new track or require a Root message.

Across B01+B02, retained exposure is768 closed-form calibrations,9,216 calibration moves,
0 policy fits,2,816 full episodes/270,336 team ticks and273,822,016 model branch
transitions; combined scientific wall is about265.36s, with support work additional.
These finite costs and all results carry forward if a materially new information/decision
comparison is chosen later. The current state is closed investment with no active
producer or queue, not an indefinite admission/re-entry wait and not a universal negative.

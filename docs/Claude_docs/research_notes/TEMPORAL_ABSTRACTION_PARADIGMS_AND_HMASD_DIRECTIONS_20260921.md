# Temporal abstraction paradigms and HMASD directions

Advisory note written after first-hand reading of the primary sources — 2026-09-21

**Status.** Read-only third-party advice that the owner asked for on 2026-09-21; the owner allowed
a detailed report in this tree. Nothing was launched, no direction record was edited,
`flexible_skill_duration` (FSD) stays rested. This note supersedes my three chat-only rounds of
the same day. The owner judged round 2 "old ideas", round 3 too micro, and then named the cause:
I was working from scout summaries instead of the originals ("你应该亲自读一下重要的原文比如HMASD
当前滥用scout导致有些失真"). So this note is built on papers and repository records I read myself;
whatever I did not read is labelled as such.

**Revised before first publication, same day.** Two things changed the draft.

1. Upstream `main` published the acting Root's review of the *same* owner question
   (`docs/research/RESEARCH.md`, "Portfolio review 2026-09-21 temporal-learning-and-uav-design").
   It records the owner's correction — "我发现当前切入点有问题 这本质是一个marl算法" — and Root's adopted
   position: the research object is "联合技能怎样被学会和使用", and "无需为使方法获胜新造切换费、预约或隐藏信息".
   My draft's main recommendation was a price or budget on re-assignment. It is withdrawn.
2. An independent critic pass on the draft returned `MATERIAL_DISSENT: yes`. I checked each finding
   against code and records myself; most stand, one only in part. §7 lists every change.

This note agrees with the research object Root adopted. It tries to add only what first-hand
reading and the programme's own July and September records contribute to it.

**Labels used throughout.**

- `[READ]` — I read the primary source (paper text, repository record or code) myself in this
  session. PDFs were downloaded and read directly, not through a summarising tool.
- `[SCOUT]` — reported by a delegated scout, not re-read by me. A pointer, not evidence.
- `[HYP]` — my own derivation, analogy or conjecture.
- Against the programme's record: `TRIED` (run here), `RECORDED` (written down here, never run),
  `NEW` (not found in the record; my map of the record is bounded, see Appendix B).

Jargon is defined where it first appears. "High level" means HMASD's skill coordinator (the
transformer that assigns a team skill Z and individual skills z^i); "low level" means the skill
discoverer (the shared actor that turns an observation and a skill into an action); "k" is the
skill interval, the number of steps between two assignments.

---

## 0. 中文摘要

**这份笔记回答什么，以及它和今天 Root 决定的关系。** 您的两个问题：(1) 可变技能周期扩大了决策空间，理论上
有更好的最优解，但探索压力更大，如何权衡；(2) 不考虑可变周期，当前研究共识还能给 HMASD 带来哪些改进，或让它
更贴合 UAV 基站服务用户的场景。同一个问题您也交给了 Codex 代理 Root；期间您纠正"这本质是一个marl算法"，Root
据此把研究对象定为"联合技能怎样被学会和使用"，并写明"无需为使方法获胜新造切换费"。我的初稿主建议恰恰是
"给重分配定价或设预算"，与此冲突，也被独立批评者用项目自己的记录驳倒（7 月 R30 处置已拒绝显式切换惩罚）。
该建议已撤回。本稿同意 Root 采纳的研究对象，只写亲读原文和项目自身记录能为它**增加**的东西。
这次我亲自通读了 HMASD 全文（18 页，含附录 A–H）和十二篇关键原文；未亲读的一律标 `[SCOUT]`。

**一、亲读 HMASD 读出来、之前 scout 没报出来的事实（§2）**

1. HMASD 的价值主张是**稀疏奖励下的协作**：0-1 奖励的 SMAC 上 MAPPO、MAT "完全不工作"；奖励稀少的任务 λ_e=100；
   去掉内在奖励基本不工作。三类任务都是"与"型耦合（Alice_and_Bob 必须一人踩按钮另一人才能取钻石）。
   本项目的 UAV 场景 1 是稠密奖励。
2. 论文自己的 k 消融（3m，回合长 100）是**尖峰**：k=25 约 80% 胜率，k=5 约 0，k=10 与 k=50 约 20%。
   论文各任务每回合高层决策 2–40 次；本项目 k=10、T=500，每回合 50 次。
3. 论文的技能数很小（n_Z 2–3，n_z 2–5，2–3 个智能体，联合标签空间 ≤ 81）；本项目 n_Z=n_z=6、6 架 UAV，
   联合标签空间 279,936。内在奖励的有效权重（.025 / .01）比原文（.1–1）小一到两个数量级，
   判别器只学到了技能的边际频率。
4. 作者自述三条局限：只有约 24% 的技能有用（共识文件已注明这不是普适常数）；n_Z、n_z、k 需逐任务精调且不稳定
   （35 次运行 26 次成功）；只能学"全队"技能，没有子队技能。
5. 论文对 k 的解释是**执行结构**："每 k 步一次集中式执行，其余 k−1 步分散执行"（教练叫暂停）。
   k 不在概率图模型里，是模型之外的装置。

**二、对"更大决策空间 vs 探索压力"的宏观判断（§3）**

1. **单智能体里，没有代价就没有收益。** Nachum 2019、Harb 2018 原文明说：逐步决策的策略已经可以最优，时间抽象
   在表示上没有收益。FSD、UCOPE、方向 A 三个"免费重决策"宿主上的零结果，是同一条定理的三次观测。
2. **合作 MARL 里，高层只有三种原生功能，k 在每种功能里含义不同。** (i) *信息*：协调器知道智能体不知道的事，
   k 是全局信息的刷新率；(ii) *相关/互补*：联合技能组合的收益不可加——HMASD 顺序解码的原话是"防止技能重复、
   让智能体选择互补的个体技能"，k 是一个联合组合的寿命；(iii) *承诺*：队友在 k 步内可预测，各自的学习问题更平稳
   （COPA 原话：教练"最有用的时候，是它让智能体的行为在时间上平滑一致"）。可变 k 的"更好的最优解"只能来自这三条。
3. **项目自己的 B12 已经测到：场景 1 上第 (ii) 条为零。** 标签效应"逐智能体、近似可加"，联合（非可加）映射被拒绝，
   同标签项还略为负（轻微递减收益，"不是协调需求"）。也就是说协调器在这个宿主上没有可协调的东西：
   "选哪个标签"只值 .02–.09 J，"何时换"更不可能重要。您说"这本质是一个 MARL 算法"，B12 给了它一个可测的形式：
   **MARL 算法贡献需要一个交互项不为零的宿主和技能集**，而 B12 的回归（加交互项）就是现成的、零训练的度量工具。
   共识文件和 Root 的决定都没有这样用 B12（**NEW**）。
4. **两个月份撞的是同一堵墙的两面。** 把宿主按"任务可及性 × 团队耦合"分成 2×2：7 月的玩具任务
   （R30 的 Alice–Bob 筛查、稀疏终端奖励的 R51 AMDT）有耦合但完不成任务——R30 两臂任务成功率均为 0，
   R51 的共享策略和各固定 N 专家都没见过一次正回报；9 月的场景 1 摸得到奖励但没有耦合——什么都学得会，
   什么联合的东西都不重要。HMASD 论文本身在"稀疏 + 耦合"格，靠多样性机制解决可及性。
   **"稠密但耦合"这一格（场景 7 一类）在联合技能问题上还没被问过（就我查到的记录而言）。**
5. **探索压力是学习内生的，不需要发明切换费。** HMASD 的 k=25 尖峰和 COPA 的 T=4 最优（"与越小越好的直觉相反"）
   奖励里都没有任何切换代价。MARL 特有的那部分代价是**联合驻留时间** `[HYP]`：n 个智能体各自独立重选时，
   一个联合组合只活约 k/n 步（R30 的 p_keep=.6、6 个智能体：个体技能平均保持 2.5 个检查点，全队同时保持的概率
   只有 4.7%）。于是得到一个不对称：**异步在技能可加时便宜（也无用），在技能互补时昂贵（而那正是需要协调的地方）。**
   出路不是更聪明的触发器，而是**以条件化代替同步**：解码器看得见队友当前持有的技能（项目 D2 路径与 7 月 R30
   已有），评论家看得见"持有的联合技能 + 各自的时钟"（Root 今天提出的假设；ACAC 是已发表的最近实例，
   它的消融显示去掉这一点会变慢或陷入次优）。
6. **文献空白，四篇原文互证（有界检索）。** ACAC（ICML 2025）原话："多数工作学习宏动作（技能），但强制固定时长、
   同步运行；我们处理的是预定义的、时长不等的宏动作。"IARO（ICLR 2026）的联合 option 需要全队一致才能启动、
   全队一致才能终止，"任意子集智能体的 option 留作未来工作"。VO-MASD（IJCAI 2025）有子群技能但离线、
   长度 H 固定。HMASD 自述只有全队技能。**学到的合作技能 × 子队范围 × 异步寿命 × 在线**这一格是空的。
   7 月 HA-CTSE/R30 的研究对象正是这一格（"异步技能过程在稀疏团队奖励下保持可学、可区分、有用"），
   仓库里 7 月就有 ACAC、IARO 的精读分析和本地 PDF——Root 今天说没取到 PDF，其实不必重取。
7. **为什么两次都没走通、这次该有什么不同。** 发现技能的论文都同步（发现需要稳定的度量单元），做异步的论文都
   给定宏动作；"同时发现 + 异步"是两个难题相乘，7 月正是两者同时做、且在摸不到奖励的任务上做。
   建议分两段：先在有真实耦合的稠密宿主上、固定 k，让"联合技能有用"成立并用干预测出来；再在这些技能上解开时间，
   那时 R30 的 KEEP/SET 编辑、ACAC 式评论家、宏观 λ 折扣都是现成技术。

**三、第二问：不考虑可变周期，共识之外还能加什么（§5）**

共识文件（FOUNDATIONS）已有：HMASD 局限作为动机、策略类分解、评论家缺少持有技能上下文、`chunk_length=k` 耦合、
信息匹配对照等。亲读补充的是：(a) "论文体制 vs 本项目体制"对照表，以及由此得到的最直接的性能建议——
**把标签空间缩回论文的量级**（论文从未超过 81 个联合标签；B12 算出当前每次决策的信噪比约 10⁻⁴）；
(b) 用 B12 工具度量耦合；(c) 宿主选择：场景 7（8 架 UAV、强制中继、端到端 QoS、两个容量为 1 的充电站、S4 故障）
原生具备三种功能，而且 ACAC 作者明说"缺少连续动作的异步 MARL 基准"；(d) 多样性机制要么按论文体制运行，
要么替换；(e) 为"稠密 + 耦合"体制重新陈述 HMASD 的价值主张（协调与承诺，而不是稀疏奖励下的探索），
这需要一个有能力的、信息匹配的扁平对照；(f) 始终带一个脚本化参照。

**四、范式选项与建议（§6）**

A 维持现状——不建议；**B 联合技能、分两段（建议）**；C 机理分析（Nachum 式假设隔离），作为低成本并行收获；
D 回到论文原生基准做"免调 k"；E 预算化协调（我初稿的主建议）——撤回，仅当宿主原生有通信约束时才有意义。
B 的第一步都不需要训练：一个两三个智能体的"联合驻留"玩具模型（四个臂：共享时钟 / 独立时钟 /
独立时钟 + 看得见队友持有技能 / 再加评论家上下文），以及在耦合宿主的检查点上跑 B12 式交互项度量。
这两步都是诊断，不是门槛。

**需要您发话的（我不会在您发话前启动任何实验）：**
[DECIDE-1] MARL 算法主张的验证域是否从场景 1 换到有真实耦合的宿主（场景 7 一类；紧邻您冻结的 G33 谱系）；
[DECIDE-2] 先做固定 k 的"联合技能有用性"，还是直接做异步协调（Root 的候选）——我建议前者先行；
[DECIDE-3] 由谁承载：第二段与 FSD 的重开条件吻合，第一段是固定 k 问题、不属于 FSD；FSD 继续休息；
[DECIDE-4] 是否让 Pro 对 §3 与 §6 做一次关键批评（本稿提交后即可发）。

---

## 1. What I read myself

| Source | Part read | What it contributes here |
|---|---|---|
| Yang et al. 2023, *Hierarchical Multi-Agent Skill Discovery* (local PDF, 18 pp.) | all, including Appendices A–H | §2 entirely |
| Nachum, Tang, Lu, Gu, Lee, Levine 2019, *Why Does Hierarchy (Sometimes) Work So Well in RL?* arXiv 1909.10618v2 | pp. 1–9 (all main text) | no representational benefit of hierarchy in Markovian single-agent settings; benefit is exploration; c_train and c_expl decoupled; Switching Ensemble; footnote 1 leaves variable length to future work; transfer named as the unevaluated benefit |
| Farquhar, Gustafson, Lin, Whiteson, Usunier, Synnaeve 2019, *Growing Action Spaces* arXiv 1906.12266v1 | §1–7 | nested action spaces as a curriculum; V*_i ≤ V*_j for i<j; Q_{ℓ+1}(s,a) = Q_ℓ(s,parent(a)) + Δ_ℓ(s,a); restricted-space data is valid for the larger space; multi-agent version grows 1→2→4→8 position clusters |
| Fruit & Lazaric 2017, *Exploration–Exploitation in MDPs with Options* arXiv 1703.08667v2 | §1–2, Thm 1–2, §5 | regret of learning with options = SMDP learning regret + a linear term T_n(ρ*(M) − ρ*(M_O)); sufficient conditions for options to help |
| Harb, Bacon, Klissarov, Precup 2018, *When Waiting is not an Option* arXiv 1709.04571v1 | introduction through the switching-cost section | optimal policies need no temporal abstraction; bounded rationality and the deliberation cost η; η is a margin on the advantage in the termination gradient; options as a compressed communication of intent |
| Tallec, Blier, Ollivier 2019, *Making Deep Q-learning Methods Robust to Time Discretization* arXiv 1901.09732v2 | §1–3.1 | an action held for a short time has a correspondingly small advantage; Q collapses to V as the step shrinks; claims restricted to off-policy Q methods |
| Dabney, Ostrovski, Barreto 2020, *Temporally-Extended ε-Greedy Exploration* arXiv 2006.01782v1 | §1–4 (opening) | persistence is what ε-greedy lacks; temporal extension is put in the exploration policy "without modifying the greedy policy" |
| Liu, Liu, Stone, Garg, Zhu, Anandkumar 2021, *Coach-Player MARL for Dynamic Team Composition* (COPA) arXiv 2105.08692v3 | §3.1–3.4, §4.1, Table 1 | the closest published relative of HMASD's clock; interval ablation peaks at T=4; adaptive re-distribution by an ℓ2 threshold with a bounded-loss theorem |
| Chen, Lan, Aggarwal 2025, *Variational Offline Multi-agent Skill Discovery* (VO-MASD) arXiv 2405.16386v3 | abstract, §1, §4.2–4.3 | HMASD used as the online hierarchical baseline; fails sparse 7m / 10m / MMM2; criticised for whole-team skills; VO-MASD's own skill length H is fixed |
| Xiao, Tan, Amato 2022, *Asynchronous Actor-Critic for Multi-Agent RL* arXiv 2209.10113v2 | abstract, §1, §2.5 | MacDec-POMDP; macro-actions and their terminations are given; hierarchical MARL methods "assume agents' high-level decisions [have] the same duration"; trajectory squeezing |
| Jung, Hong, Yoon, Lee, Lim 2025, *Agent-Centric Actor-Critic for Asynchronous MARL* (ACAC), ICML, PMLR 267 | pp. 1–9 (all main text) | a centralised critic built from per-agent macro-observation histories, each stamped with the time it was obtained; macro-level λ-discounting; macro-actions are pre-defined; "most works … learn macro-actions … and typically enforce fixed durations, operating in synchronous settings" |
| Steleac, Sridharan, Abel 2026, *Inter-Agent Relative Representations for Multi-Agent Option Discovery* (IARO), ICLR | §1–6 (all main text) | discovered *joint* options; initiation needs full-team consensus, termination needs every agent's vote, hard stop at 50 steps; options "involving arbitrary subsets of agents" left to future work; large option sets destabilise training |
| Mahajan, Rashid, Samvelyan, Whiteson 2019, *MAVEN* arXiv 1910.07483 | §1, §4, ablations | committed exploration through one shared latent held for a whole episode; learned latent policy beats uniform |

Repository records read today: upstream `docs/research/RESEARCH.md` (direction rows; the
temporal-learning review's Question, Pro Answer and Decision) and
`docs/rl-marl-foundations-20260907/FOUNDATIONS.md` in full (this is "the consensus" of the owner's
second question); FSD `NOTES.md` (B01, B03, the discriminator inspection, B10–B13 readings);
`configs/config_1.py` (scenario 1 and the scenario 7 preset); `envs/pettingzoo/uav_env.py`
(observation and state builders, SINR); `hmasd/networks.py:968-1000`; the July external-review
records R30 (keep/set disposition, background, result), R41A, R41B, R43, R44, R51, R54, the
variable-team toy design, the N/K literature disposition, the 2026-07-18 iteration-4 convergence;
the July literature deep-dive's analyses of ACAC and IARO; the 2026-09-01 ledger in this directory.

Not read this session, cited only as background or pointers: Sutton–Precup–Singh 1999 (the
interruption theorem, textbook knowledge), Jong 2008, Brunskill & Li 2014, Mann 2014, Harutyunyan
2019, Sabbioni 2023, Metelli 2020, TempoRL, UTE, ODIS, HiSSD, MAZero, Expert Iteration, UPDeT,
InforMARL, the UAV-BS and O-RAN papers. One lesson on the way: the arXiv number I carried for
Fruit & Lazaric turned out to be an unrelated paper; I corrected it only because I opened the file.

---

## 2. HMASD as published versus HMASD as run here

All paper facts `[READ]`; project values from `configs/config_1.py` and FSD `NOTES.md` `[READ]`.

| | HMASD paper (Tables 1–3, §4, App. D–G) | This project, UAV scenario 1 |
|---|---|---|
| Reward | sparse and conjunctive: 0-1 SMAC, Overcooked, Alice_and_Bob. On 0-1 SMAC "MAT and MAPPO don't work at all"; on Overcooked HMASD is "superior … over baselines" | dense coverage reward every step |
| λ_e (team reward in the low-level reward) | 0 on Alice_and_Bob, 100 where reward is rare | 1.0 |
| λ_D, λ_d (diversity rewards) | .1–1 and .1–1 | .05 and .02 nominal, .025 and .01 effective (`legacy_mi_reward_coef = 0.5`); the terms act as a near-constant offset of about −.06 per agent-step |
| Discriminators | essential: without intrinsic reward HMASD "can't work on most scenarios" | losses 1.72–1.76 against ln 6 = 1.79; accuracy .30–.38 team, .24–.28 individual; consistent with having learned only the marginal skill frequency |
| λ_l (action entropy) | .01 | .05 |
| λ_h (skill entropy) | .001–.1, summed over agents in the paper's own Eq. 6 | .07, summed over six agents |
| Actions | discrete | continuous, unclamped Gaussian |
| Agents | 2–3 | 6 |
| n_Z, n_z | 2–3, 2–5 | 6, 6 |
| Joint label space n_Z · n_z^n | 12–81 | 279,936 |
| k and episode length T | k 10–50, T 100–400 | k 10, T 500 |
| High-level decisions per episode | 2 (Alice_and_Bob), 4 (3m), 16–40 (Overcooked) | 50 |
| Upper bound on information sent per step, log2(n_Z · n_z^n)/k `[HYP]` | .07–.48 bit | 1.8 bit |
| k ablation | 3m: k=25 ≈ 80 % win, k=5 ≈ 0, k=10 and k=50 ≈ 20 % (read off Fig. 10a) | k=1 against k=10 in training: no difference (B07, one valid block); hold and redraw rules at deployment: no difference (B08) |
| Authors' stated limits (App. F–G) | 24 % of learned individual skills useful on SMAC (all useful in the good Overcooked runs); 26 of 35 runs learn anything ("the final performance is either 1 or 0"); n_Z, n_z need careful tuning; "can only learn team skills for the entire team" | — |

Three readings.

**R1. The method's demonstrated value is coordination under sparse reward, and that is not this
host's regime.** The paper's case is built where flat learners score zero or clearly less; its
ablations say the intrinsic reward and the high level are both necessary *there*. Nachum et al.
reach the same conclusion for single-agent hierarchy: "most of the observed benefits of hierarchy
can be attributed to improved exploration, as opposed to easier policy learning or imposed
hierarchical structures", and "an explicit higher-level policy … is not necessary in these
environments". The programme's record mirrors that. "No high-level lever moved D's score"
(RESEARCH.md, FSD row: B02, B07, B08, B09, B13, B14); "a learner with no coordinator optimizer
step reached historical D1280's level, a feasibility observation and not an equivalence"; and the
hierarchy's +.29 J over the flat comparator has "whether its gain comes from the skill structure
or from having a denser learning signal" recorded as untouched (NOTES, B03 reading). None of this
is a mysterious failure. It is what the papers predict for a dense-reward task.

**R2. The project runs HMASD with far more high-level exploration pressure than its authors ever
did, and with the diversity machinery almost switched off.** Fifty decisions per episode over a
label space of 279,936, against at most forty decisions over 81; effective diversity weights one
to two orders of magnitude below the paper's. A near-uniform label law and a coordinator that
does not matter are the expected outcome. The July iteration-4 record
(`A_NO_MATERIAL_Z_DEPENDENCE`, "conditional SMDP credit remains closed until material,
persistent and naturally executed semantics exist") and the September B12 line ("the signal is
present *and* unusable as credited": a per-decision signal-to-noise of about 10⁻⁴ against an
entropy bonus of .07) are the same finding at two dates. I add nothing to that diagnosis except
the paper-side numbers. **RECORDED.**

**R3. The paper's own rationale for k is an execution structure, not a learning device.** "Our
method performs one timestep of centralized execution and k − 1 timesteps of decentralized
execution in every k timesteps", the basketball coach calling a timeout, "a balance between
fully centralized execution … and fully decentralized execution". The probabilistic graphical model has
no time structure over skills: Z depends on s, z^i on (o^i, Z), per step. k sits outside the
model. In the Alice_and_Bob case study the team skill switches at t=k, after the first diamond
is collected: the clock approximates an event. This reading feeds §3.2.

---

## 3. The owner's question, in MARL terms

### 3.1 In single-agent RL the better optimum is worth exactly nothing without a price

Nachum et al., p. 2: "in Markovian systems, there is no theoretical representational benefit to
imposing temporally extended, hierarchical structures, since non-hierarchical policies that make
a decision at every step can be optimal". Harb et al., p. 1: "from the point of view of absolute
optimality, temporal abstractions are not necessary: the optimal policy is achieved by primitive
actions. Therefore, it has been difficult to formalize in what precise theoretical sense
temporally abstract actions are helpful." Their answer is bounded rationality: a *deliberation
cost* η paid at every switch, which enters the termination gradient as a margin on the advantage,
(A(s′,o) + η). Without η, learned termination degenerates: "frequent terminations can become an
issue unless regularization is used".

So a policy that may re-decide whenever it likes, and remembers what it was doing, contains every
fixed-k policy; and with re-deciding free, its optimum is per-step feedback. "Variable duration
has a better optimum" is then true and empty. The programme has measured this three times
`[READ, RESEARCH.md]`:

- FSD: D2 interruption, the E2 cost sweep, the E3 heterogeneous corridor, B07–B14. No lever on
  timing moved the score.
- UCOPE (Codex): "Can feedback-conditioned KEEP/END of a UAV velocity commitment improve native
  return over ordinary feedback and fixed renewal?" B02–B10 adverse; "keep ordinary
  deterministic G".
- Direction A (`termination_rule_experience_reuse`): ordinary multi-step reuse worked; a
  long-commitment collector "did not improve its prewritten primary endpoint".

All three hosts make re-deciding free. The consensus document is right that this constrains those
packages and not every learned duration; my point is only that the single-agent literature
predicts nulls of exactly this kind, so they should not be read as bad luck.

### 3.2 What a high level is for in cooperative MARL: three functions, three meanings of k

This is where a MARL project differs from the single-agent literature it borrows from. A
coordinator that assigns skills to a team can pay in three ways that have no single-agent
counterpart. Each gives k a different meaning, and a different native prediction for an unfixed k.

| Function | What the coordinator supplies | What k is | When an unfixed k can pay | Measurable on a host without training anything new |
|---|---|---|---|---|
| **(i) Information** | what it sees and the agents do not | refresh rate of global information | the value of fresh global information varies over time and across agents | how much of the global state an agent's own observation already carries |
| **(ii) Correlation / complementarity** | a joint choice that a product of independent policies cannot make: who takes which role | lifetime of one joint combination | the complementarity structure changes locally, so some agents should re-pair while others stay | the interaction (non-additive) share of team return over skill combinations |
| **(iii) Commitment** | teammates that are predictable for k steps, hence a more stationary learning problem for everyone | predictability window | responsiveness and predictability trade off differently across agents or phases | the shape of the fixed-k learning curve family |

Sources. (i) is HMASD's own account of k (§2, R3) and COPA's architecture: an omniscient coach
sends each player a strategy vector every T steps, and at deployment re-sends only if the new
vector differs from the held one by more than β, with a theorem bounding the loss by
2(n_a·η·β + κ)/(1−γ); performance holds down to 13 % of steps carrying a broadcast (175.6 → 168.8)
and "drops faster in more dynamic environments". Harb et al. motivate options the same way: they
"offer a mechanism for communicating intents … by compressing the information into a simpler form,
sending only the identifier of the options". (ii) is HMASD's stated reason for sequential decoding,
"which can prevent skill duplication and allow agents to choose complementary individual skills
based on the team skill"; MAVEN's committed exploration through a shared latent is the exploration
side of the same function. (iii) is COPA's reading of its own interval ablation: "the coach is most
useful when it can cause the agents to behave smoothly/consistently over time."

Two cautions on (i), both from checking the critic's objection against the code `[READ]`. My draft
said the skill is "the only path" by which global information reaches an actor. That was wrong as
written: each agent observes users and other UAVs directly (`uav_env.py:435-498`). The critic's
counter-claim, that actors see everything within 1,500 m, is not right either: `observation_radius`
is never used in `uav_env.py`; the filter is SINR ≥ `min_sinr`, and with `use_fdma = True` that is
a pure signal-to-noise range test. The coordinator's state holds every position
(`uav_env.py:353-366`). How much of it each agent already sees was measured by neither of us. So
function (i) is *unmeasured* on this host. And where it is active, per-step refresh is optimal
unless something makes refreshing costly (§3.4).

One correction to my draft: published HMASD re-decodes everyone from a start symbol at each
boundary and never sees the labels currently held. The programme's code already goes further:
the D2 path teacher-forces the held joint action in canonical order,
ℓ_i(z) = log π(z | Z_held, z_held,<i) (`hmasd/networks.py:968-1000`), and partial assignment
re-samples only the masked tokens.

### 3.3 The programme's own measurement: function (ii) is zero on scenario 1

B12 (FSD `NOTES.md`, 2026-09-20 20:19) regressed each commitment's mean reward on the six label
counts, with 12,800 ten-step commitments per block down to 256 at length 500 `[READ]`:

- "the label ranking is in the reward at every commitment length, per-agent and additive";
- the alternative, "the joint map is not additive — a label pays only when all six …", was
  **rejected**: "additive per-agent coefficients from mixed teams reproduce the all-equal map's
  ranking and most of its spread on 3/3";
- the homogeneity term (Σn²) is slightly *negative*, "mild diminishing returns to everyone holding
  the same label, not a coordination requirement";
- "the labels are per-agent, approximately additive, long-horizon policies", worth .02–.03 J when
  held ten steps and .06–.09 J when held for the episode.

Read through §3.2: on this host, with these skills, there is no complementarity for a coordinator
to exploit. A product of independent per-agent choices is already as good as any joint choice.
Then *which* label matters little, and *when* to change it cannot matter more. The mild negative
homogeneity is what a coverage reward under FDMA should produce: agents add up, except where they
double-cover. Scenario 1 is close to a team of independent coverage agents.

This gives the owner's correction — "这本质是一个marl算法" — a measurable form. **A MARL-algorithm
claim about joint skills needs a host and a skill set whose interaction term is not zero, and B12's
regression with an interaction term is a ready, zero-fit instrument for checking that on any
trained checkpoint.** July's forced-label test (`A_NO_MATERIAL_Z_DEPENDENCE`: action-TV and
forced-effect upper bounds below 1/12) is its interventional sibling. Using B12 this way is
**NEW** to the record as far as I can find: the consensus document and Root's decision argue for
"real team coupling" from the scenario's missing mechanisms, not from this measurement.

The additivity is a property of the *learned* skills on this host, not a theorem about the task.
But the task's reward gives little reason to expect otherwise.

### 3.4 The exploration price is endogenous to learning, so no fee has to be invented

MARL has two direct measurements of an interior optimum in the clock, and neither task charges
for switching `[READ]`. HMASD App. D: "HMASD performs poorly with too short or too long skill
intervals, which demonstrates that an appropriate number of timesteps is necessary for each skill
to be learned effectively." COPA §4.1: trained with T ∈ {2, 4, 8, 12, 16, 20, 24}, "the
performance peaks at T = 4, countering the intuition that smaller T is better". The richer class
(small k) loses *in learning* in both. So the owner's "探索压力" is real and native; what the
programme's hosts lack is not a fee but the interior optimum itself (B07: k=1 and k=10 tie).
This agrees with Root's "无需为使方法获胜新造切换费" and with July's R30 disposition, which rejected
"default switch penalties" because "otherwise long lifetimes would be hard-coded rather than
learned from task advantage".

What the price consists of.

- *A two-class statement from theory.* Fruit & Lazaric, Lemma 2: the regret of learning with a set
  of options O after T_n primitive steps is Δ(M, A, T_n) = Δ(M_O, A, n) + T_n·(ρ*(M) − ρ*(M_O)).
  The second term is "due to the fact that the introduction of options amounts to constraining the
  space of policies"; it is linear in time. The first is the cost of learning in the induced
  semi-Markov problem and grows like √n in the number of decisions. Their sufficient condition
  asks that options do not exclude the optimal policy, that there are no more options than
  primitive actions, and that holding times are bounded; then "it is enough to choose options
  which are long enough (but not too much)". This compares two *fixed* classes over one horizon,
  in tabular undiscounted UCRL. It does not license switching class mid-run; that inference is
  mine `[HYP]` and is why "enter from a solution" (§3.5) matters. The consensus document's
  identity, J̄_var − J̄_fixed = (J*_var − J*_fixed) − (ε_var − ε_fixed), is the same decomposition
  without rates.
- *Four roles of k inside one learner* `[HYP; the first three were my round-3 "three clocks", and
  Nachum's c_train and c_expl partly anticipate them]`: the control clock; the credit clock (an
  assignment held briefly has a small advantage — the Tallec et al. effect, measured in-house by
  B12, where the label's share of advantage variance rises from 1e-4 at length 10 to 2–3e-2 at
  length 500); the exploration clock (a sampled label persists, which is temporally extended
  exploration in the sense of Dabney et al.); and the identifiability horizon of the diversity
  objective (a skill must last long enough to reach states that reveal it).
- *The MARL-specific part: joint dwell time* `[HYP]`. If n agents re-decide independently, each
  holding a skill for about k steps, a given *joint* combination survives only about k/n steps.
  With R30's initial keep probability .6 and six agents, an individual skill lasts 2.5 checks on
  average while the whole roster survives a check with probability .6⁶ ≈ 4.7 %. If skills are
  additive this is harmless: each agent's contribution accrues over its own lifetime. If skills
  are complementary, the object that carries the value — the combination — is never held long
  enough to be credited, and the number of distinct combinations visited explodes.
  **Asynchrony is cheap exactly where it is useless, and expensive exactly where coordination
  matters.** A shared clock is the blunt fix (HMASD; IARO). The sharper one is to *condition
  instead of synchronise*: let the re-deciding agent's policy see the roster the others hold, and
  let the critic see that roster and each commitment's age, so that what has to be learned is a
  conditional marginal ("given what they hold and for how long, what should I take") and not a
  joint. The first half exists here (R30's working roster, D2's teacher-forced pass, ledger §9.4
  item 1). The second half is the hypothesis Root wrote today — "表示决策前的联合技能与时钟上下文，
  能否改善价值学习及完整团队回报？" — and ACAC is its closest published instance: each agent's
  macro-observation history is encoded with the timestep at which it was obtained, because
  "without this duration information, identical consecutive macro-observations lack context about
  whether the interval between them is one timestep or ten"; the ablation that pads instead
  "converges more slowly or even settles into suboptimal solutions". ACAC also moves λ-discounting
  from primitive steps to decision points, A = Σ_k λ^k γ^(l(k)−l(0)) δ_l(k), because otherwise "as a
  macro-action becomes longer, this discounting method applies a greater discount to its future
  rewards, thereby diminishing the perceived importance of that macro-action decision". All of
  this is in ACAC's setting: pre-defined macro-actions, sparse-reward Overcooked and BoxPushing,
  discrete actions.

### 3.5 Ways to enter a larger space without paying the full price

1. **Condition instead of synchronise** (§3.4). MARL-specific. Decoder side **TRIED** in July
   (R30), critic side **RECORDED** today by Root and in July's ARES-SMDP plan ("ACAC for
   agent-owned event histories and duration-correct SMDP credit").
2. **Enlarge along locality.** MARL-specific. Growing Action Spaces grows a many-unit action space
   as 1 → 2 → 4 → 8 position clusters that must act alike. For HMASD the axis is *who is
   re-assigned together*: whole team → sub-team → individual. HMASD's third limitation, VO-MASD's
   criticism and IARO's future work all point here. The growth order is **NEW**; the partial
   re-assignment mechanics are **RECORDED** (ledger §9.4) and the all-agent form **TRIED** (R30).
3. **Keep the old clock an exact member of the new class.** Pro's answer to Root makes the point:
   a k₀ entry in a softmax menu does not reproduce fixed-k behaviour if every other duration keeps
   positive probability at deployment. R30's KEEP/SET does it better: the fixed check clock stays,
   a lifetime is a run of KEEPs, and each agent has K choices per check instead of K·D. **TRIED.**
4. **Enter from a solution.** Growing Action Spaces: a nested family A_0 ⊂ A_1 ⊂ …, monotone
   optimal values because "the agent can always in the worst case fall back to a policy using a
   more restricted action space", and the larger space's value initialised from the smaller one's,
   Q_{ℓ+1}(s,a) = Q_ℓ(s, parent(a)) + Δ_ℓ(s,a). Training the large space from scratch "struggle[s]
   with exploration"; the small one "plateau[s] comparatively low"; growing beats both; the
   ablation without the parent decomposition is "the most striking failure". For durations the
   nested family is the set of decision times, and the parent of every finer-clock action is
   *continue the held skill*. Pro's "releasable prior toward k₀" is the same family. Root files
   this under training technique: "固定周期起点可以是训练技巧，但课程本身并未解释 MARL 耦合". I agree; a k
   schedule is **NEW** to the record and is a technique, not the research object.
5. **Share data across clocks.** Experience gathered on a coarse clock is valid for a fine one
   wherever "continue" was the action taken (Farquhar et al.'s off-action-space learning; the
   consensus document's TempoRL note is the same idea). Direction A **TRIED** the tabular relative:
   ordinary multi-step reuse worked, longer traces added nothing.
6. **Keep exploration persistent while control becomes fine.** Dabney et al. put persistence in the
   exploration policy "without modifying the greedy policy"; Nachum et al. split HIRO's single c
   into c_train and c_expl. Not a free gain: direction A's long-commitment collector (A02,
   **TRIED**) did not improve target learning.
7. **Do not choose durations at all: let the world end the skill.** In the MacDec-POMDP line
   macro-actions come with termination conditions, so "agents can start and end macro-actions at
   different time steps" and the learner chooses only *which*. HMASD needs a clock because skills
   discovered by mutual information have no meaning and hence no natural end: **k is a prosthesis
   for missing semantics** `[HYP]`. **RECORDED** in substance (ledger untying (e); July's "timing
   credit closed until semantics exist"); the phrasing is mine.

### 3.6 The open cell in the literature, and the programme's July ancestor

Four originals, read today, agree on where the gap is (a bounded search):

- ACAC, related work: "Most works focus on learning macro-actions (options or skills) and
  typically enforce fixed durations, operating in synchronous settings. In contrast, our work
  addresses scenarios with pre-defined macro-actions of varying durations". Xiao et al. likewise:
  "we assume a set of macro-actions has been predefined".
- IARO: asynchronous schemes "typically rely on single-agent (local) options that do not express
  cooperative behaviours. Therefore, coordination occurs only at the option selection level, but
  not within the option policies themselves." Its own joint options need "full team consensus for
  initiation", every agent's vote to terminate and a hard stop at 50 steps, and it leaves "options
  involving arbitrary subsets of agents to future work".
- VO-MASD discovers sub-group skills, but offline and with a fixed segment length H.
- HMASD: whole-team skills on one shared clock; sub-team flexibility is its third stated limit.

Discovered skills come synchronised; asynchronous methods are handed their macro-actions.
**Learned cooperative skills × sub-team scope × asynchronous lifetimes × online** is empty. My
reading of why `[HYP]`: discovery needs a stable unit over which a skill's effect is measured
(HMASD's k-step segments, VO-MASD's H, IARO's option training), and asynchrony removes the common
unit. Doing both at once multiplies two hard problems.

The programme has been in this cell before `[READ]`. July's HA-CTSE line stated its object as
"asynchronous skill processes that remain learnable, differentiated, and useful under sparse team
reward", "not merely a larger duration action set". It first sampled a skill and a duration
together whenever an agent's skill expired, listed the structural problems that creates (no token
for every agent at a check; short lifetimes generate more high-level samples; "duration can become
a shortcut for skill identity"), and replaced it with R30's fixed-clock all-agent KEEP/SET editing.
R30 ran once, on an Alice–Bob environment whose reward was still shaped: the adaptive arm used its
freedom (full-synchronisation SET rate .169, 125 skill spells longer than 4·k₀), and both arms
scored zero task success ("failed to access the task within this short screen"). The ARES-SMDP
plan then ordered the work (representation sufficiency → ordinary learning → exogenous membership
→ exogenous heterogeneous time → joint), absorbing "ACAC for agent-owned event histories and
duration-correct SMDP credit"; its first gate failed (R54,
`CONFIRM_NO_ACCESS_R54_FULL_SET_REFERENCE`) and that exact contract was retired. R51's
entity-pointer dispatch toy ended the same way: neither the shared policy nor any specialist
"observed a positive terminal return". The repository still holds July's close
readings of ACAC and IARO with local PDFs
(`docs/research/literature/n_k_many_agent_deep_dive/analysis/P02_ACAC.md`, `P08_IARO.md`); Root
reports reading only abstracts today because the PDFs would not download. IARO's analysis there
already names the counter-example a shared clock invites: under charging and stragglers "最慢成员
支配所有人的重新决策时刻".

Two months, one wall, seen from two sides:

| | skills additive across agents (no coupling) | skills complementary (coupled) |
|---|---|---|
| **task success hard to reach** | — | July's toys (R30's Alice–Bob screen, R51 AMDT with a sparse terminal reward): no arm ever completed the task, so nothing could matter. HMASD's own benchmarks sit here too, and its diversity machinery is the tool for reaching reward. |
| **reward easy to reach** | scenario 1 in September: everything learns, nothing joint matters (B12) | **a dense-and-coupled host. Not yet asked the joint-skill question, as far as I found.** |

### 3.7 What success should mean

- **Evidence by intervention that joint skills matter**: a non-zero interaction share in a
  forced-label factorial on the host, before any claim about how they are selected or timed.
- **A competent information-matched flat learner** as the reference. The consensus document and
  Root both insist on this; FSD never had one (B01, B03, B04).
- For unfixed durations: conditioned-asynchronous against a shared clock and against independent
  clocks, at matched information and resources, reporting what Root lists — marginal durations,
  re-decision counts, label changes, information refresh, update counts.
- **Robustness to k** remains an attractive secondary claim: HMASD loses sixty points of win rate
  when k is mis-set by a factor of 2.5 and lists the tuning burden as a limitation.
- The frequency of centralised steps is worth *reporting* as a column, as COPA reports f. It does
  not belong in the reward unless the task charges for it.

---

## 4. Idea seeds

Each seed: where it comes from, how it transfers, what it predicts, the cheapest first observation,
its status against the record, the main risk. None is a plan; none has been costed. In the owner's
order of work (inspiration model → B-class exploration) the first observation is always a scripted
or toy one. Grouped by the two stages of §6.

### Stage 1 — make joint skills matter, at fixed k

**S1. Measure coupling before building mechanism.**
*From:* §3.3. *Transfer:* run B12's regression with pairwise interaction terms (and July's
forced-label test) on checkpoints of a candidate host. *Predicts:* near-zero interaction on
scenario 1 (already seen); a clearly non-zero share on a host with relay chains or contended
chargers, if HMASD's skills pick up roles there. *First observation:* zero-fit where a checkpoint
under the current interface exists; otherwise it needs one ordinary training run, which is the
DM's call and not mine. *Status:* the instrument is **TRIED** (B12); using it as the host- and
skill-selection diagnostic is **NEW**. It is a diagnostic, not a gate. *Risk:* an additive map
under HMASD's current skills says the skills are not roles, not that the task has no roles.

**S2. Size the label space to the decisions available.**
*From:* §2, R2. *Transfer:* the paper never ran more than 81 joint labels, against 2–40 decisions
per episode, with diversity weights of .1–1. Bring n_Z, n_z and the intrinsic weights into that
regime on the UAV host, or factor the labels by sub-team (S6). *Predicts:* a label law that leaves
uniform, discriminators above the marginal, and a coordinator that matters. *Status:* lower
coordinator entropy is **RECORDED** (I3, never run); the regime replication is **NEW**. *Risk:*
HMASD is unstable even in its own regime (26 of 35 runs; R43's anchor drifted from .89–.93 to
.52–.61 under continued optimisation).

**S3. Discovery that seeks complementarity** `[HYP]`.
*From:* §3.2 (ii); IARO. *Transfer:* HMASD's diversity terms reward a team skill that the global
state reveals and individual skills that each agent's own observation reveals. Nothing rewards
*combinations* that do something no product of individual skills does; that is left to the
extrinsic reward. IARO shows one way to aim discovery at relations between agents (a relative
representation of the joint state, options discovered on it). A lighter version inside HMASD: a
discriminator on the joint label from a relational view of the state. *Predicts:* a non-additive
label map on a coupled host. *Status:* **NEW** to the record as far as I found; July's C1
("environment-agnostic semantic creation") is the nearest relative and was blocked for want of a
clean process view. Literature novelty unchecked. *Risk:* speculative; IARO's discovery is offline
and needs shared observations.

**S4. Semantic high-level actions: the coordinator as a pointer-style assigner.**
*From:* §3.5 item 7; HMASD's own account of sequential decoding as duplicate avoidance, which is an
assignment problem. *Transfer:* keep the architecture and change what a high-level action *is*: a
pointer to an entity (a demand cluster, a failed neighbour's cell, a charging slot). Skills then
end on observable conditions, carry over when N changes, and are complementary by construction.
*First observation:* scripted: assignment plus go-to control is both the missing scripted
reference (`greedy_coverage` emits zero actions on scenario 1) and a ceiling on label stakes.
*Status:* entity-pointer actions were **TRIED** in July's R51 AMDT (anonymous set-pointer
actor-critic, N = 2–6, sparse terminal reward) and never reached reward; the lesson is about
reward access, not about pointers. My draft asked the owner to relax a July rule for this. That
was unnecessary: the rule constrains the *inputs of the intrinsic posterior* (task clock,
progress, owner state, reward, duration, identity, action echo, "hard-coded coordinate slicing"),
not what a high-level action denotes. *Risk:* less "discovery" in the story; Root's caution that
"改进一个 UAV 控制器本身，尚未证明改进了 MARL 学习" applies, so the scripted version is a reference.

**S5. At the high level, evaluate instead of exploring — as a reference.**
*From:* the programme's numbers: decisions are few, collection is about 9 % of wall time, and in
skill_information_refresh "known-model planning captures 34 of 36 extra completions". *Transfer:*
improve the assignment by simulated rollouts with the low level frozen, then distil. *Status:*
B13's external label bandit **TRIED** the constant-label version on the static host ("selection
within the constant class is worth about the panel noise"). Root's adopted line places this kind
of tool: "专用规划器可作成本透明的强参照，不能替代有能力的信息匹配 HMASD/MARL 对照". Direction B's B09 is a
caution: better joint prediction and better one-step choices, "no stable closed-loop benefit".

### Stage 2 — untie time over skills that matter

**S6. Asynchronous joint skills: condition, don't synchronise; grow along locality.**
*From:* §3.4–3.6. *Transfer:* R30's KEEP/SET editing (or D2's partial assignment) for the policy
side; a critic that sees the held roster and each commitment's age; ACAC's decision-level λ.
Re-assign the neighbourhood that changed and leave the rest committed; grow scope
team → sub-team → agent. Root asks for one main change first; between the two I would take the
critic context, because it is function-preserving (zero-initialised inputs leave the fixed-clock
learner unchanged) and Root itself calls the plain version "强的简单参照". *Predicts* (from the
joint-dwell model): with additive skills all arms tie; with complementary skills independent
clocks lose to a shared clock; conditioned-asynchronous beats the shared clock only where change
is local and uneven across the team. *First observation:* a bandit-scale toy — two or three
agents, an assignment payoff with a tunable interaction term, targets that drift locally, four
arms (shared clock; independent clocks; independent clocks with the held roster visible to the
policy; the same plus roster and ages visible to the critic), matched decisions. *Status:*
mechanics **RECORDED/TRIED** (above); the joint-dwell model, its asymmetry and the toy are
**NEW**; the critic hypothesis is Root's. *Risk:* the team skill Z loses its common clock (ledger
K-5): Z must stay on a slow clock or go. And in July, "direct anonymous active-set control" (C3)
was the empirical leader: a flat learner with the same information may simply be enough.

**S7. Skills that end themselves; agents that may call the timeout.**
*From:* §3.5 item 7; HMASD's individual discriminator q_d(z^i | o^i, Z). *Transfer:* an agent can
evaluate log q_d for its own held skill from its own observation; when that confidence collapses,
its situation no longer looks like the skill it was given. A decentralised termination signal
that adds no action to anyone's space. *First observation:* offline, on stored rollouts of a host
with events: does the drop lead or lag the event, at what false-alarm rate? *Status:* the family
(termination on a local mismatch signal) is **RECORDED** — CRTO stopped at a technical gate, and
my round-2 outcome-surprise trigger belonged to it; this statistic is **NEW** (the critic checked
and agreed). *Risk:* it needs discriminators that carry state information, and here they carry
none; it presupposes S2 or S4.

**S8. Grow the clock — a training technique.**
*From:* §3.5 items 4–5. Train coarse; add decision ticks at half the period with the gate
initialised to *continue*; share the label head. *Status:* R44 **TRIED** a zero-output warm-start
retain/replace factor at one decision point on the frozen source (zero discordance, guaranteed by
construction). A schedule over clocks is **NEW**, and the critic confirmed that. By Root's
adopted reading it answers the shared-clock question, not the asynchronous one, so it is a tool
for S6's comparisons and not a direction.

### Harvest

**S9. "Why does hierarchy (sometimes) work in cooperative MARL?"**
*From:* Nachum et al. as the template: hypotheses isolated by decoupled horizons, a shadow agent
trained on the hierarchical agent's data, hierarchy-free switching ensembles. *Transfer:* the
programme already holds the negative half of such a study: a coordinator that does not matter
(B08, B09, B13, B14), a hierarchy-over-flat gap of unknown origin (B01, B03, B04), discriminators
that learn only the marginal, a k that does not matter on an uncoupled host (B07), label effects
that are additive and grow with commitment (B12), three nulls for free-switching termination (FSD,
UCOPE, A). §3.2's three functions are the MARL hypotheses Nachum's single-agent study could not
have. A few controlled fits close the open cells: random labels with no coordinator, a flat
learner given the same intrinsic signal, a flat learner imitating the hierarchy. *Status:* the
July Pro answer **RECORDED** the untested channels; framing the record this way is **NEW**.
*Risk:* an analysis carries less weight alone; it needs one host where some function is
demonstrably active, which stage 1 supplies.

### Withdrawn

**Budgeted coordination** (the draft's S1 and main line): price or cap re-assignments and claim a
return-against-centralisation frontier. Withdrawn as a recommendation, for four reasons. Root's
adopted position rules out inventing the fee. July's R30 disposition had already rejected switch
penalties, for a good reason. Where timing had value in the programme, a transparent rule took
most of it (skill_information_refresh: "the transparent VoI rule solves the timing decision";
vsp_03: one guard recovers 56 % of the fitted rule's margin), and where sends were priced the
learned sender lost to round-robin (CADC, −.0134, one pair). And §3.4 shows the trade-off exists
without a fee. What survives: report centralised-step frequency as a column; and on a host whose
communication constraint is *native*, the question may be asked again.

---

## 5. Ignoring duration: what can be added to the consensus

"The consensus" is `docs/rl-marl-foundations-20260907/FOUNDATIONS.md`, which I read in full. It
already holds, carefully hedged: HMASD's existing mechanisms and its three stated limits as
motivation (with the note that 24 % is not a universal constant); COPA as a reference whose
threshold saves broadcasts, not coach inference; information-matched comparison; the
class-inclusion identity with Metelli and Dabney as single-agent precedent; asynchronous action
opportunities as a MARL learning problem; the value heads' missing held-skill context; the
`chunk_length = k` and normaliser couplings; shared-duration learning (TempoRL,
Timing-as-an-Action); the minimum detectable effect of five seeds (≈ .125 and .174 J). Root's
decision adds three fixed-k problems: skill usefulness and composability, team and temporal
credit, co-update stability. I do not repeat those. What first-hand reading adds:

1. **The regime table of §2, and the plainest performance lever it implies: run HMASD in the regime
   it was built for, or know that you are not.** A joint label space 3,500 times the paper's
   largest, more decisions per episode than any paper task, diversity weights a tenth to a
   hundredth of the paper's. B12 computed what that does to credit: a per-decision
   signal-to-noise near 10⁻⁴ against an entropy bonus of .07. S2.
2. **Choose the host by coupling, and measure it.** §3.3, S1. Scenario 7 as configured here
   `[READ, configs/config_1.py:426-555]`: eight UAVs, thirty users in forced relay clusters, one
   ground station, an end-to-end QoS reward with a return-safety constraint, batteries and two
   charging stations of capacity one (S2–S4), failures (S4), 1,500-step episodes, and
   `scenario7_skill_interval_candidates = (10, 25, 50)` already in the preset. A relay chain is a
   conjunction (function ii), a charger of capacity one is a contended resource (function ii),
   and battery-driven hand-overs have uneven natural durations (function iii). Whether each agent
   sees the whole chain (function i) is something to check, not something I know. Root's review
   states the limits: the current interface is not the old arm-A result, and S4 enables failures.
   The host also sits next to the owner-frozen G33 lineage.
3. **Restate HMASD's value proposition for a dense-and-coupled task.** In the paper, skills are how
   the team reaches reward at all. Where reward is dense, that role is gone; what may remain is
   coordination and commitment: fewer miscoordinated equilibria, steadier teammates. That is a
   different claim with a different control, a competent flat learner with the same execution-time
   information, and the programme does not have it on any UAV host (my 2026-09-14 foundations
   review; FSD's B01–B04).
4. **Run the diversity machinery fully or not at all.** Either the paper's regime (S2) or a
   replacement (S3, S4). Half-on, it is a constant offset.
5. **The field has a stated gap that a UAV host fits.** ACAC's closing paragraph: "a primary
   challenge is the current lack of asynchronous MARL benchmarks that combine continuous actions
   with defined macro-actions. Developing such benchmarks is crucial future work."
6. **Always carry a scripted domain reference.** COPA can say its learned agents without global
   information are "significantly worse than the hand-coded baseline" because it had one. Scenario
   1 has no working scripted reference.
7. **Entities, not a flat vector** — but this is **RECORDED/TRIED**, not new: July's ARES-SMDP plan
   took InforMARL as "the permutation-safe full active-set reference", and R54's supervised
   full-active-set reference failed its access gate. COPA's attention over entities, with
   zero-shot generalisation over team size, remains the design to beat on the N axis.

---

## 6. Paradigm options and one recommendation

| | Claim type | Host | Success means | Uses what is in hand | Main risk |
|---|---|---|---|---|---|
| **A. Status quo** | method beats HMASD on J | scenario 1 | J above the seed noise | everything | structurally null: no price (§3.1), no coupling (§3.3); five seeds resolve only ≈ .13–.18 J |
| **B. Joint skills, in two stages** | MARL algorithm: cooperative skills that are learned, matter and are used; then lifetimes that differ across agents | one dense-and-coupled UAV host, one version | stage 1: a non-zero interaction share by intervention, and a gain over a competent information-matched flat learner. Stage 2: conditioned-asynchronous against shared and independent clocks at matched resources | B12's instrument, July's forced-label test, R30's KEEP/SET, D2's partial decoding, July's ACAC and IARO analyses, the scenario 7 factory | a flat learner with the same information may be enough (July's C3); HMASD is unstable |
| **C. Mechanism study** | analysis: which functions of hierarchy are active in cooperative MARL | the existing hosts plus one coupled host | clean isolation of the functions | B01–B14, UCOPE, A, the July record; a few new fits | carries less weight alone |
| **D. Native benchmarks** | robustness: HMASD without a k to tune | the paper's sparse tasks | within a few points of the best fixed k everywhere | the original source runs here (R41B) | leaves UAV-BS; SMAC and Overcooked are not in the repository; HMASD is unstable (R43) |
| **E. Budgeted coordination** | a return–centralisation frontier | only a host whose communication limit is native | — | — | withdrawn as a main line (§4) |

**Recommendation: B in two stages, with C as the parallel low-cost harvest.** B is the research
object Root adopted after the owner's correction. What this note adds to it is an order of work
and the reasons for it. Stage 1 comes first because every timing result in the record, July and
September, was bounded from above by skills that did not matter; and because the literature's
open cell (§3.6) is open for a reason: discovering skills and untying their clocks at once has
not worked for anyone, this programme included. Stage 2 then inherits technology that exists (R30,
the ACAC critic, decision-level λ) and a prediction that can fail (S6). C turns three months of
careful nulls into a contribution and tells B which function each host activates.

First observations, none of which needs a fit: (1) the joint-dwell toy of S6; (2) the coupling
measurement of S1 on whatever checkpoint of a coupled host exists under its current interface.
Both are diagnostics, not gates; neither waits on the other. If (2) needs a checkpoint that does
not exist, that is one ordinary training run and the DM's decision.

This differs from Root's text in one place. Root keeps as its first distinguishable candidate the
coordinated skill–duration sampling under others' commitments. I would put stage 1 before it, or
at least measure coupling on the chosen host first. With an additive label map that candidate has
nothing to coordinate and will return another clean null.

**What needs the owner's word.** I start nothing before it.

- **[DECIDE-1]** Whether the validation domain for the MARL claim moves from scenario 1 to a host
  with real coupling (the scenario 7 family). Root's text leans that way and froze no host. It is
  adjacent to the frozen G33 lineage, and any shared-environment change needs the Reviewer.
- **[DECIDE-2]** Stage 1 first (fixed k, joint-skill usefulness), or straight to asynchronous
  coordination. My recommendation is stage 1 first.
- **[DECIDE-3]** Who hosts it. Stage 2 matches FSD's reopening condition ("on a skill basis that
  has task meaning … a mechanism with a native prediction for an unfixed duration"); stage 1 is a
  fixed-k question and is not FSD's. FSD stays rested either way until the owner says otherwise.
- **[DECIDE-4]** A Pro critic pass on §3 and §6. Pro is the owner's preferred critic for
  decision-critical reasoning; this note can be sent once committed.

---

## 7. Corrections and limits

**What the critic found, and what I did after checking each point myself.**

- *The draft's "only path" sentence was false* (critic, blocking). Accepted in part: agents observe
  users and UAVs directly. The critic's replacement claim was also off: the 1,500 m radius is
  unused; the filter is an SINR threshold. Function (i) is now "unmeasured on this host" (§3.2).
- *"The programme's only two positive results" was false* (blocking). Accepted.
  `tail_return_distributional_learning` B01 is a retained positive, and
  `skill_teammate_drift_learning` has positive B04 and B10 readings; neither is a timing
  direction. The scarcity "pattern" was a selection. The sentence is gone.
- *The draft's sub-team seed labelled its in-filling view NEW* (blocking). Accepted: ledger §9.4
  item 1 describes it and says the code path exists; R30 ran the all-agent form. Relabelled (now
  §3.5 items 1–2 and S6).
- *The budget was labelled NEW* (blocking). Accepted: the ledger's interruption rule already has a
  switching cost c, and July's R30 disposition rejected switch penalties. With Root's adopted
  position this removed the draft's main line.
- *The two timing positives argue against a learned timing policy* (material). Accepted; it is one
  of the four reasons in §4's withdrawal.
- *R51 AMDT and the July entity-encoder work were missing* (material). Accepted; now credited in
  §3.6, S4, §5 and Appendix B.
- *The July "environment-agnostic" rule is narrower than I assumed* (material). Accepted; the
  draft's DECIDE-2 is dropped.
- *Fruit–Lazaric was over-licensed* (material). Accepted: two fixed classes, tabular, undiscounted;
  "enter late" is my conjecture. §3.4 says so.
- *B13 cannot contradict "high-level credit is the bottleneck"* (material). Accepted. The
  notebook's own reading rule, written before scores, says the P2-and-P3 failure "不能据此直接宣告
  '选择原来就不是瓶颈'": the coordinator's value update was off as well, and P3's bar could not be
  met even by perfect constant-label selection. My round-3 claim is withdrawn as *unsupported*, not
  as refuted. B12's signal-to-noise reading is the more careful statement of the same concern.
- *"MAPPO and MAT score zero on every paper task"* (material). Accepted: that sentence is about
  0-1 SMAC only. Fixed in §0 and §2.
- *The capacity row .1–.6 bit* (minor). Recomputed from Table 3: .07–.48.
- The critic confirmed every paper quotation and number in §1–§4 of the draft, the July facts I
  had cited, and the NEW labels on a clock schedule and on discriminator-confidence termination.

**My own corrections to earlier rounds.**

- Round 3's "change-triggered interruption" exists in the literature as COPA's deployment rule in
  strategy space.
- Rounds 2 and 3 treated the missing price as a footnote. §3.1 puts it at the centre for the
  single-agent case; §3.4 says why MARL does not need one.
- My round-2 "value-of-timing law" (event rate × waiting time × response gain) is bounded in the
  consensus document, fairly: it explains a preset event-response mechanism and cannot set every
  adaptive termination value to zero where no exogenous event exists.
- My "three clocks" were partly anticipated by Nachum's c_train and c_expl.
- The draft read k mainly as a centralisation rate. That is one function of three, and the one I
  cannot show to be active here.

**Limits.**

- The capacity bound is an upper bound on information sent, not a measurement of information used.
- The k-ablation percentages are read off a figure with wide bands.
- Tallec et al. restrict their claim to off-policy Q-learning; carrying it to HMASD's PPO
  coordinator is my analogy, and B12 is the in-house measurement that supports it.
- The joint-dwell argument is a derivation from a simple model. Nothing has tested it.
- Scenario 7 is described from its configuration preset. I did not read its environment code or
  any of its results, and I did not check what the G33 freeze covers.
- "Not found" always means a bounded search. Of the thirty-nine July review folders I have now
  read twelve; of the September nine-route portfolio, the route table and the opening of a few
  directions. The critic did not read R29–R42, R45–R49, R52–R53 either.
- The critic reviewed the draft, not this revision. No Pro pass has been made.

---

## Appendix A. Round-3 micro findings, kept for the record

Checked against code and records earlier on 2026-09-21; file references as verified then.

- D2's trigger is level-triggered: gap = max logit − held logit ≥ c (`hmasd/agent.py:2579-2596,
  2612`). It fires when the held label is off-argmax, so it interrupts exploratory labels
  because they are exploratory. In options theory interruption compares *values* (Q(s,o) against
  V(s), plus Harb's margin); D2 compares *policy logits* of an entropy-regularised coordinator
  whose per-agent temperature is 6·λ_h, so a fixed c is not scale-free.
- On static scenario 1 D2 cut individual segments from 10 to about 2.8–3.5 steps; on the E3
  corridor the firing rate was the same in low- and high-hazard regions, with event precision
  2.5–4 times chance. E2 swept c over .25–2: at c=2 segments reach the cap, verdict NEITHER.
- Exposure confound: 3,765 coordinator optimizer steps for D2 against 525 for D0.
- Low-level action std grew from 1.0 to 2.8–3.2 under λ_l = .05; the active `DiagGaussian` has
  no clamp (`hmasd/r_mappo_utils.py:73-95`); the environment does not clip requests
  (`envs/pettingzoo/uav_env.py:283`), so max_speed is unenforced; the paper uses λ_l = .01 on
  discrete actions. B03 fixed the same mechanism in the flat learner. Evaluation is mean-action,
  so B10's .05–.16 J is a deployment-sampling cost, not a predicted gain.
- The coordinator sees users as one flat token (`hmasd/networks.py:749-754`); it has V(state)
  and per-agent V(obs) heads and no label-conditioned value; the decode order is fixed
  (`networks.py:1058-1061`); the low-level GRU is not reset at skill boundaries and no network
  receives the skill's age.
- Value normalisation is on; the time limit is handled consistently because the step index is in
  observation and state. Neither is a defect.
- RPGM mobility exists in `envs/pettingzoo/relay/` (`belief_map.py`, `forced_relay.py`,
  `routed_core.py`); `uav_env.py` never moves users.
- Exact per-UAV difference rewards were never tried (LCAC was the learned COMA-like version and
  came out null or adverse).

## Appendix B. The map of the programme's record behind the TRIED / RECORDED / NEW labels

- 2026-07 external-review series (R29–R54), read: the fixed-clock KEEP/SET disposition (R30:
  duration head retired, all-agent autoregressive editing on a working roster, "no explicit
  switch/edit penalty, no lifetime bonus, and no forced maximum age"); R30's background (the
  HA-CTSE object; six agents, four skills, k₀=10, durations {1,2,3,4} checks) and its one paired
  run (seed 30031, 64,000 transitions per arm, zero task success in both arms); R41B positive
  anchor of the original HMASD source on Alice_and_Bob (seed 1, full exposure); R43 anchor lost
  under continued optimisation; R44 frozen-source renewal factor, zero discordance, "the
  frozen-source K=50 renewal-timing route is permanently retired"; the variable-team toy design
  and R51 AMDT (entity-pointer dispatch, N = 2–6, 32-step horizon, no positive terminal return in
  any arm, contract retired); the N/K literature disposition (`ACCEPT_WITH_MODIFICATION:
  ARES-SMDP`) and R54 (supervised full-active-set reference fails its access gate, exact contract
  retired); iteration 4: `A_NO_MATERIAL_Z_DEPENDENCE`, direct control (C3) the empirical leader,
  environment-agnostic semantic creation (C1) blocked by the lack of a clean process view, timing
  credit closed until semantics exist.
- `docs/research/literature/n_k_many_agent_deep_dive/` (2026-07-17): eight papers, among them
  ACAC and IARO, each with an absorb / do-not-absorb table for HMASD.
- 2026-09-01 ledger in this directory: five ways to untie k, entries K-1 to K-7, §9.2 (menu cost,
  the interruption rule with its switching cost c, hazard heterogeneity), §9.4 (asynchronous
  partial re-assignment with kept agents as forced tokens), §9.5 Q4 (sweep c from zero).
- The 2026-09-04 nine-route map (`docs/research/portfolio/decisions/`): under flexible skill
  duration, K1 interruption and renewal (FSD, vsp_03), K2 (CRTO, residual-triggered options;
  stopped at a technical gate), K3 information acquisition and renewal (UCOPE), K4 duration
  representation and value sharing (SCDMP, VSP-C1; prospective, nothing run); under flexible
  agent count, N1–N5. I read only the route table and the opening of CRTO and SCDMP.
- Direction A, `termination_rule_experience_reuse` (Codex, archived): A01 ordinary multi-step reuse
  beats one-step, longer traces add nothing; A02 long-commitment collector, no gain in target
  learning.
- CADC, `contention_aware_decentralized_communication`: sends priced at .001 each; learned
  sender ADVERSE against round-robin, one matched pair (−.0134 J_net).
- FSD `DIRECTION.md` and `NOTES.md`: arms D0–D2 (D3 never built), E2, E3, B01–B14, reserve ideas
  I1 (run as B13), I2 (longer caps) and I3 (lower coordinator entropy), neither run.
- Upstream `RESEARCH.md` on 2026-09-21: `skill_teammate_drift_learning` active (B09 no stable
  closed-loop benefit, B10 positive against two fixed rules on the same three learners); FSD,
  tail-return, cross-play and `variable_n_fleet_churn` in reserve; skill_information_refresh,
  vsp_03, UCOPE and FOLR archived by the acting Root's whole-project decision, positives retained.
- A scout's map (not re-verified by me) found no record of: skill priors, uncertainty-driven
  commitment, k schedules or population-based tuning, exact difference rewards,
  residual-over-scripted control, distance-based skill objectives, constrained-diversity
  repertoires, annealing of intrinsic weights. The critic showed that its entries for entity
  encoders and grounded or pointer actions were wrong; treat the rest as pointers.

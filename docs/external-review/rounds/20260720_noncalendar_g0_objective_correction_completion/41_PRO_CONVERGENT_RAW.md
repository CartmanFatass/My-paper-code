1. User-facing route brief

当前更强 MARL 目标不是证明普通 recurrent MARL 失败，而是在变量成员数量、匿名 JOIN/LEAVE/REJOIN、survivor continuity 与异步个体生命周期下，验证是否存在比普通 primitive recurrence 更有价值的时间抽象机制。

下一步应构建并测量一个 mission-aligned 的机制证据源：围绕commitment abstraction / temporal credit的最小替换，而不是继续修补 G0 access。原因是 G0 已经证明结构可达、calendar null 有效、shared renewal 存在压力，但 ordinary recurrent controller 尚未完全访问；当前需要识别的是“时间抽象是否提供不可约价值”，而不是单纯提高普通控制器分数。

ordinary recurrent MARL 保留为 matched comparator 与诊断工具，用于判断新增机制是否提供额外能力，而不是作为进入研究的 gate。

结果分支含义：

若简单 recurrent/credit 修复即可解决：说明机制价值下降，组合回归 ordinary MARL；

若时间抽象机制在匹配比较下产生外部价值：支持继续研究 commitment/lifetime abstraction；

若机制失败：退休该机制，不通过调参、扩预算或修改 benchmark 救援；

若 benchmark 本身无法识别目标能力：停止该 benchmark 线，重新设计更符合 mission 的证据源。

2. Correction verdict

接受前序 correction。

此前选择的 ordinary-access localization source 不再成立，因为它试图通过 observation readout 改变 D，但冻结 D 已经包含相关 demand/error 字段，因此该 treatment 不是科学变量变化，而是 no-op。

同时保留已有结论：

G0 的 NO_ACCESS_BENCHMARK_ORDINARY_CONTROL 有效；

H 证明结构可达；

C 证明 calendar/static null 不足；

S 证明 shared renewal 存在限制；

D 未建立充分 ordinary access。

这些结果不能被重新解释为：

hierarchy 已失败；

skill 已无价值；

temporal abstraction 已被证明。

它们只限定当前 benchmark 与 ordinary controller 的关系。

3. Mission-forward selected source or stop

选择：

TEMPORAL_COMMITMENT_CREDIT_LOCALIZATION_SOURCE

这是一个新的 bounded mechanism source。

不再选择：

observation 修补；

G0 rerun；

budget expansion；

更大 direct model。

原因：

当前真正未决问题：

在已有 observation 与 membership contract 下，是否存在一种显式 commitment/temporal credit 机制，能够产生 ordinary recurrence 难以获得的长期行为组织能力？

该 source 直接针对最终 mission：

variable membership；

variable individual lifetime；

asynchronous commitment；

long-horizon coordination。

它不是为了让 hierarchy“赢”，而是为了判断 temporal abstraction 是否具有不可约贡献。

4. Causal claim and strongest simple explanation
Causal claim

加入显式 commitment-aware temporal credit 后，策略是否能够产生：

稳定持续行为；

个体异步生命周期；

对在线需求变化的长期适应；

并且该收益不能由普通 recurrent hidden state、calendar memory 或 primitive action factorization 简单解释。

Strongest simple explanation

最强 ordinary-MARL explanation：

recurrent policy 已经能够在 hidden state 中编码持续行为，新增 commitment object 只是额外参数化。

因此任何成功必须证明：

不是容量增加；

不是 reward shaping；

不是更强信息输入；

而是真正的时间抽象。

Alternative explanations

保留：

Credit explanation

失败可能来自：

sparse terminal reward；

long horizon credit；

PPO optimization。

Representation explanation

失败可能来自：

recurrent state compression；

data flow；

representation bottleneck。

Temporal abstraction explanation

只有当：

ordinary recurrent；

credit修正；

仍不能解释，而 commitment mechanism 成功时，才支持。

5. Algorithm and replacement boundary
保留

保留：

anonymous lifecycle；

JOIN/LEAVE/REJOIN；

survivor continuity；

physical time；

event/commitment clock separation；

external reward；

primitive execution。

新增

只允许一个机制：

commitment state representation

例如：

c
i
	​


表示当前成员持续行为状态。

它必须：

由 policy 学习产生；

不读取 future；

不读取 identity；

不读取 task role；

不读取 reward history。

删除

删除：

任何为了制造 skill 的标签；

supplied primitive；

duration catalogue；

task-specific lifetime reward。

禁止堆叠

不加入：

graph；

team latent；

posterior；

intrinsic reward；

hazard；

new critic；

communication module。

每个新增模块必须有唯一 causal role。

6. Matched comparator and evidence contract
Comparator

主要比较：

Commitment model

vs

ordinary recurrent primitive MARL

两者保持：

observation；

communication；

model capacity；

optimizer exposure；

training budget。

Information contract

禁止：

future demand；

future duration；

oracle action；

identity；

role；

task progress。

允许：

当前 local state；

当前需求；

当前 membership state；

recurrent memory。

Training contract

固定：

同一 environment；

同一 membership distribution；

同一 held-out distribution；

同一 seeds；

同一 optimizer。

不得：

增加预算；

增加模型；

改 threshold。

Evidence metrics

必须同时测量：

外部任务价值；

commitment duration distribution；

held-out membership/lifetime generalization；

natural execution。

不能使用：

label accuracy；

forced branch；

posterior predictability；

作为成功标准。

7. Mutually exclusive outcomes
INVALID

触发：

replay；

checkpoint；

probability；

RNG；

lifecycle contract；

错误。

处理：

只修工程。

NO_MECHANISM_VALUE

触发：

commitment model 无法超过 matched recurrent comparator。

更新：

temporal abstraction 降权；

ordinary recurrent explanation 上升；

停止该机制线。

CREDIT_LIMITED

触发：

credit修正后有效，但 commitment 本身无额外贡献。

更新：

credit hypothesis 上升；

temporal abstraction 降权。

TEMPORAL_ABSTRACTION_SUPPORTED

触发：

commitment model：

在匹配 comparator 下提升外部任务；

在未见 lifetime/membership 下保持；

产生自然持续行为。

更新：

temporal abstraction 上升；

可进入下一 integration review。

但仍不能声称：

hierarchy superiority；

HMASD parity；

UAV transfer。

BENCHMARK_NOT_IDENTIFYING

触发：

无法区分：

recurrence；

commitment；

benchmark shortcut。

处理：

停止该 benchmark。

8. Prohibitions and parked ideas

禁止：

G0 rescue；

重跑同 contract；

调 seed；

调 budget；

调 threshold；

改 reward；

弱化 recurrent comparator；

deliberate memory sabotage。

禁止：

task-shaped intrinsic reward；

identity/role leakage；

supplied skill；

duration payment；

posterior stacking；

graph/field/slot/latent stacking。

Parked ideas
Factorized executor

保留。

重新激活条件：

commitment abstraction 已证明有价值，但 executor interference 仍未解决。

Applied-prefix cooperation

保留。

重新激活条件：

出现真实 multi-owner coordination conflict。

Continuous marks

保留。

重新激活条件：

离散 commitment 已证明有效，但连续控制提供额外 generalization。

Larger direct model

继续 park。

只有当：

representation bottleneck 被证实，而非机制缺失。

Stop condition

如果：

commitment mechanism；

credit localization；

matched recurrent comparison；

均无法证明不可约价值，

则停止当前 temporal abstraction 研究线，回到更简单 ordinary MARL 或重新定义最终 benchmark。

END_OF_REGISTERED_RESPONSE
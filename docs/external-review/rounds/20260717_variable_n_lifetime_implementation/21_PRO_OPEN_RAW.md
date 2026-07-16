1. Plan verdict

MODIFY_PLAN — F0/F1 架构不需要语义身份、固定槽位或 F1 专属容量即可落地，但当前计划尚未封闭生命周期唯一所有权、临时离开前价值快照、低层 actor/critic 拆分、ragged replay 以及 schema-3 的早期严格分派，按现稿直接编码会使实现正确性和 F0/F1 因果隔离不可审计。

2. Contract-to-code audit
证据事实

可复用的是语义，不是现有固定形状实现。

FixedClockAREditPolicy 已有三项可复用语义：单个 K-way 类别动作、采样后立即修改 working roster、按已应用 working roster 做 teacher-forced replay。但它把 n_agents 写入对象、prefix 维度和逐 agent 身份槽，因此不能作为 variable-N 生产实现直接复用。

StrictHMASDMAPPOLowLevelPolicy 的 actor 主干确实保持了 obs → skill FiLM → recurrent actor → action distribution，因此其 actor 计算和动作分布可以复用；但同一个类同时包含固定 state_dim、team-code FiLM 的 critic，而且现有序列接口将数据整理成 [T,B,N]，不是 active-only ragged 接口。

StandaloneProcessAgent 的固定 N 假设不只存在于一个 buffer 中。其构造器保存固定 n_agents，随后建立 [num_envs,n_agents,...] 的 skill、age、actor hidden、critic hidden 和 segment manager；act_low_batch 又显式使用 batch_size*n_agents 展平、向每个 agent 复制 state，并生成固定 agent-ID 行。

训练入口同样在 agent 创建前后假定固定 env.n_uavs，现有 checkpoint 是 schema-2。其加载器虽然对部分主干严格加载，但对多个模块使用 strict=False，并在若干 optimizer/module 不匹配时吞掉异常；这与事件路径要求的完整 live-state、RNG、open trace 严格恢复不兼容。

现有计划与上轮 contract 有一个直接所有权矛盾。

架构 contract 明确写的是 collector 持有按 lifecycle key 索引的权威 lifecycle table；实现计划却两次写成新 VariableRosterEventCore 拥有 lifecycle table。若 collector 和 core 各自保存一份，就会出现 stale epoch、离开类型和 hidden/skill 状态的双重真相源。

R49 实现与结果 JSON 的证据边界如下。

我检查了生成 R49 结果 JSON 的实现。该 runner 写入 schema、状态、注册计数、M0/M1、数值误差、参数暴露、artifact 路径和 decision，并在 PASS 时把授权主张严格限制为 “interface correctness only”，同时明确禁止将其解释为 cooperation、variable-lifetime efficacy、within-episode join/leave training 或开放 roster 论文贡献。

Git-visible 项目记录登记的正式结果是：1,024 个 base case、8,192 个 permutation read、1,024 个 padding variant、1,024 个 sample/replay sequence、256 个 membership pair；最大 permutation/incremental 误差为 2.98e-8，padding/replay 误差为零，prefix-gradient support 为 1.0、中位数 0.19933，环境步、reward read、optimizer step 和参数漂移均为零。该记录本身也只把它解释为 interface-only PASS。

正式路径 logs/r49_orse_20260716_191959/result/r49_orse.json 在指定 Git 提交中不可读取；仓库规则整体忽略 logs/。所以这里复核了 JSON 的生成实现和 Git-visible 的结果登记，但没有把未进入 Git 对象的 JSON 原件冒充为已经直接复核。

审阅推断

这些证据支持的是：架构可实现，但现稿还不是可安全编码的接口合同。 当前缺口均可通过删去双重所有权、补全边界快照、提前分派 event path 和冻结 replay/checkpoint schema 来关闭；它们不要求 team latent、slot、graph、learned ordering、learned hazard 或 F1 专属模块。因此不需要返回重做整个架构，也没有证据要求停止在 F0；但也不能原样接受计划。

3. Probability and event ownership
可以接受的部分

计划冻结的机会过程在概率所有权上是闭合的：

每个 active lifecycle 的 gap 独立于 policy parameter、action 和 task signal；

gap RNG 与 frontier-order RNG 分开，并要求完整 checkpoint；

silent primitive step、membership event、gap sample 和 uniform order 都不是 actor action；

uniform order 的 1/m! 是外部增强变量，在 PPO 新旧策略比值中抵消；

incumbent channel 表示 KEEP，其他 channel 表示 SET(z)；genuine join 的全部 K 个 channel 都是 SET(z)；

没有另一个 duration head，也没有采样后 conflict repair。

因此在这些前提被实现和记录的情况下，不缺 policy survival likelihood，也不需要为 exogenous gap 或 uniform order 添加 actor log-probability。

必须修改的部分

第一，生命周期只能有一个权威 owner。

计划应恢复 contract 的原始边界：

collector/lifecycle store 是 external membership fact、temporary/terminal 语义、membership epoch 和 active presentation 的唯一权威来源；

event core 通过一次原子 transaction 读取并更新同一 store 中的 policy-runtime payload；

禁止 collector table 与 core table 双写、复制后同步或事后 reconciliation。

这不是换名字问题，而是避免同一 lifecycle 同时成为 ACTIVE 和 TEMPORARILY_ABSENT、或者 core 接受 stale epoch 的必要条件。

第二，collector 必须提供两个不同的边界快照。

temporary leave 的 bootstrap 必须来自：

完成 primitive transition 后
但在 leaver 被移除前

当前计划的 collector schema只列出了 active routing record、active observation、critic feature 和“自上一动作后的 membership events”，没有规范一个能够包含即将离开的 owner 的 post-transition/pre-membership critic snapshot。仅靠移除后的 active set 无法重建该价值。

必须改成一个明确的双快照 transaction：

pre_membership_boundary_snapshot
  = post-transition / pre-removal active lifecycles and critic inputs

atomic_membership_delta
  = join / temporary leave / terminal leave / rejoin with epochs

post_membership_pre_policy_snapshot
  = active set used to form frontier and C^(0)

leaver 的 critic-only bootstrap 只允许从第一个快照读取；新 frontier 和初始 commitment set 只允许从第三个快照读取。

第三，外部抽样也要有来源记录。

仅保存 RNG state 足以支持未来 resume，却不足以审计已经完成的 transaction。每次机会后实际分配给每个 owner 的新 gap，以及实际 sampled frontier order，都应进入结构化 event ledger。它们不进入 actor likelihood，也不进入网络输入。

第四，ephemeral row index 不能成为 replay 真相。

ordered_owner_rows 只在一次 packing 中有效。持久 ledger 必须存 source member tensors、membership epoch、owner hidden snapshot、initial working set、每个 token 前后的 working set、mask、action 和 old log-probability；replay 时才重新生成临时 row map。contract 已明确禁止从当前 roster 反推旧事件。

4. Credit and recurrent continuity
理论信用合同成立

每个 policy token 打开一条 owner-owned row；环境团队 reward 以物理时间的 gamma^Δ 累积，而 lambda 只沿同一 lifecycle、同一 policy version 的 successive owner event 推进。其他成员的机会不增加该 owner 的 GAE 深度，temporary leave 是 critic-only truncation，terminal leave 使用零 bootstrap。该分解没有把共享 reward 错误改写成 intrinsic reward，也没有漏掉 external-event actor ratio。

更新边界的方向也正确：用 old critic 关闭 open owner rows，保留 simulator、skill、age、gap 和 hidden；更新后先建立 actor-invalid continuation，直到该 owner 的下一次真实机会才关闭 continuation 并建立新的 actor-valid row。

仍需封闭的四个实现问题

1. 冻结 concurrent frontier 中 critic 的估值时点。

计划列出了 old_owner_values，但没有明确 later token 的 value 是基于：

immutable C^(0)，还是

之前 token 已应用后的 exact pre-token working set。

必须二选一并写进 source ledger。基于现有 contract 的 pre-token 字段，最一致的选择是：每个 owner 的 old value 从该 token 的 exact pre-token centralized context 计算并存储。F0/F1 使用完全相同的 critic 规则；actor mode switch 仍然只决定 decoder 收到 initial summary 还是 working summary。不能在 collection 与 replay 中分别采用不同快照。

2. 低层 actor 的“复用”必须变成可执行接口。

现有 strict class 的 act() 同时推进 actor 和固定 critic。事件路径需要：

strict_low_actor_step(active flat rows)
strict_low_actor_replay(ragged recurrent chunks)
active_set_low_critic_step(...)
active_set_low_critic_replay(...)

actor-only 接口必须调用原 strict actor 的同一参数和同一 action distribution，不能复制出第二套 actor 参数；新的 active-set low critic 则是 F0/F1 共用的 correctness infrastructure。旧 low class 和 checkpoint 不迁移。

3. ragged low replay 需要规范性 row/chunk schema。

“flat transitions + offsets”还不够。至少要冻结：

routing-only:
  environment_index, lifecycle_key, membership_epoch,
  physical_time, policy_version

model/replay source:
  obs, skill, action, old_logp, old_value,
  actor_pre_hidden, critic_pre_hidden,
  critic member/global source features,
  reward, boundary_kind

indexing:
  environment-step ptr,
  lifecycle-chunk ptr,
  next-bootstrap source

continuity应为：

survivor、KEEP、SET：hidden 连续；

temporary leave：chunk 以 pre-removal critic bootstrap 关闭，hidden 冻结；

rejoin：从冻结 hidden 开新 chunk；

genuine join：零 hidden；

terminal leave：零 bootstrap 后删除；

PPO 更新：旧 chunk 关闭，新 policy version 从保留 hidden 开新 chunk。

不允许 dummy transition，也不允许仅凭当前 active set 重建旧 row。现有固定 [T,B,N] replay 不能通过 mask 改名后继续使用。

4. schema-3 必须在 legacy loader 之前分派。

不能先构造固定-N StandaloneProcessAgent、加载一部分 schema-2 state，再检查是不是 event checkpoint。应先只读 checkpoint header：

top-level schema
controller
event architecture mode
event schema version
runtime-state presence

确认 event schema-3 后，才构造 event runtime，并对 model、optimizer、normalizer、lifecycle store、两个 RNG、open high rows、ragged low chunks和 policy version 做逐字段严格加载。任何字段缺失均在模型执行前报错。现有 permissive schema-2 loader不得成为 event fallback。

5. F0/F1 causal isolation

相同 state-dict key、shape、参数量和 byte-equal 初始化是必要条件，但还不充分。第一轮比较还必须保证：

同一 collector schema 与 lifecycle transaction；

同一 gap/order 生成器和外部随机流；

同一 active-only packing、mask、working-set apply 和 replay ledger；

同一 high/low critic、normalizer、optimizer结构和更新次数；

F0 仍然按同一顺序立即应用 token，只是 decoder 始终读取 g(C^(0))；

唯一 mode intervention 是 initial summary 与 working summary 的选择。

否则，一个看似 F1 的结果仍可能来自数据暴露、边界处理、critic 或 checkpoint 的差异，而不是 applied-prefix coupling。

当前竞争性因果假设
假设	当前证据状态	区分它所需的最小证据
H0：ordinary-MARL reduction。共享 active-set recurrent MARL 已包含动态 roster、异步机会、skill persistence 和正确 credit；F1 的 prefix 只改变 mask 或给所有 common-support action 加同一偏移。	强且未被击败。contract 的 reduction theorem 直接覆盖 action-independent shift；m=1 时也没有 earlier token，F1 与 F0 必然相同。	在 production 路径上固定同一 active snapshot、order、mask 和参数，验证 earlier SET 是否改变 later token 的 common-support relative logits，而不只是 raw hidden、gradient 或合法集。
H1：真正的 event-frontier mark coupling。earlier applied edit 会改变 later learned relative scores，并可能提供额外 cooperative value。	仅有结构可实现性证据。R49 证明存在 prefix gradient 和精确 replay 接口，但未证明 production integration、分布差异或 utility。	先通过一个集成 production trace，证明 exact replay 下 common-support relative distribution 非零变化；utility 仍需以后另行授权、架构匹配的 F0/F1 testbed，当前不能推断。
H2：实现/账本混淆。任何 F1 gain 或 failure 可能来自固定-N 泄漏、错误 leave bootstrap、policy-version 混合、ragged replay 错配或 permissive resume。	当前仍然显著，因为计划存在上述未闭合接口，而现有生产代码广泛固定 N。	一个覆盖 membership、low/high replay、update truncation 和 schema-3 round trip 的单一集成 transaction trace。该证据必须先排除 H2，才能解释 H0/H1。

不应再把“frontier 太稀疏”单列为第四条算法路线；它是 H0 的具体退化机制。learned event time/point process 也没有证据进入当前竞争集合，继续保持 deferred：只有以后在 mark policy 与所有基础设施均已成立后，才能讨论机会时点是否为 binding limit。

Final-capability map 裁定

F0：保留为 mandatory ordinary-MARL baseline。 它必须拥有完整 dynamic roster、survivor/rejoin continuity、异步 exogenous opportunity、skill-conditioned low actor 和 duration-correct credit，不能用弱 buffer 或较小 encoder 人为降级。

F1：保留，但降格为“可实现、尚未集成验证的 mark-coupling 假设”。 它不是 variable-N、ragged tensor、event ledger、gamma^Δ 或 skill persistence 的发明者；唯一候选贡献仍是 common-support learned-score coupling。

Learned point process：继续 deferred。

F2：继续并入 F0/point-process 分解，不恢复独立名称。

这与上轮 capability map 的结构一致，但本轮不能把 R49 的 isolated PASS 升格为 “F1 已可集成”或“F1 已优于 ordinary MARL”。

6. Required plan corrections
Must-fix before code

修正 lifecycle ownership。 在 contract 和 plan 中统一为一个 collector-owned authoritative lifecycle store；event core 只通过原子 transaction 操作同一对象，不保留 shadow table。

冻结双快照 collector boundary。 明确 pre_membership_boundary_snapshot、atomic membership delta 和 post_membership_pre_policy_snapshot；temporary-leave old value 只能来自前者。

把 event dispatch 提前到固定-N 构造之前。 high_controller="variable_roster_event" 必须在创建固定 arrays、compact/bridge、旧 process stack、R30 buffer 和旧 optimizer 之前分流。可以保留同一个公共训练入口，但不能让 event mode 先实例化退休模块再置为 unused。

给 strict low actor 建立 actor-only 生产接口。 复用同一 actor 参数和 distribution；在 event path 中换成共享 active-set low critic。禁止复制 actor、额外 adapter 参数或 F1-only critic。

将 high-event ledger 与 ragged-low ledger 写成规范性 dataclass/schema。 明确 source tensor、routing metadata、policy version、snapshot 时点、chunk pointers、bootstrap source和 stale-epoch 检查；ephemeral packed row 不得作为持久标识。

冻结 concurrent frontier 的 critic 时点。 建议统一采用 exact pre-token working centralized context；无论选择哪一种，都必须 collection/replay 一致并在 F0/F1 间完全共享。

建立 schema-3 早期、独立、严格 loader。 先检查 header 再构造 runtime；禁止 schema-1/2 migration、strict=False、optimizer 异常吞并或缺字段继续运行。

把 F0/F1 isolation 写成机器检查。 除 state-dict shape/参数量外，检查 byte-equal 初始化、optimizer/normalizer key、collector schema、外部 RNG 初始状态、mask/ledger/credit代码路径相同；唯一允许差异是 decoder summary selector。

产生一个可长期复核的结果 JSON。 Stage 4 应输出一份位于非 logs/ 路径的机器可读 artifact，至少含 source commit、schema、逐项 checks、最大误差、F0/F1 state-dict signatures、RNG/checkpoint round-trip 和 authorized/prohibited claims。仅留下 transient pytest stdout 会重复 R49 原件无法由 GitHub 复核的问题。

Replacement ledger
类别	本轮裁定
删除／不在 event path 实例化	固定 [num_envs,n_agents,...] runtime；agent-ID/team-code low critic 输入；fixed-roster high buffer；discrete duration head；sampled team latent/bridge/default q_D；全队同步 renewal barrier；dummy member；permissive partial checkpoint load；重复 lifecycle table。legacy/R30 文件本身不删除，继续隔离运行。
保留	F0 mandatory baseline；F1 单一 mark-coupling 假设；exogenous per-member gaps；uniform recorded order；native K-way KEEP/SET；active-only sum/count；strict skill-conditioned low actor；member-owned gamma^Δ 与 same-owner GAE；survivor/leave/rejoin continuity；R30、HMASD 和现有 ordinary baselines 的原路径。
新增，仅限 correctness interface	单一权威 lifecycle transaction；pre-removal/post-membership 双快照；actor-only low API；共享 active-set low critic；规范化 high/low ragged ledger；早期 schema-3 dispatch/validator；一个 durable acceptance JSON。

这里没有新增科学模块。机制预算仍满足“新增必须删除、吸收或取代旧机制”的原则。

Optional / deferred

允许在 exact parity 之后做不改变图结构的性能优化，例如增量维护 set sum 或缓存 packing metadata；这些优化必须对 F0/F1 完全相同。

以下不是当前“可选增强”，而是继续 deferred 或禁止：attention、graph、slot stack、team latent、learned pointer、learned hazard/point process、新 intrinsic reward、task-specific shaping、R53/R55 恢复、扩 seed、改阈值、调 gap 分布或并行路线。上轮 disposition 已明确禁止用这些方式替代架构取舍。

7. Implementation sequence and stop point

本裁定先要求修订计划；它本身不授权编码或训练。在另行获得实现批准后，最小顺序应是：

先修正文档合同。 关闭唯一 lifecycle owner、双快照、critic 时点、ragged schemas 和 early schema-3 dispatch；在这些内容冻结前不改生产代码。

纯 state/probability core。 实现 lifecycle transaction、exogenous schedule、uniform order、F0/F1 shared model、exact event ledger 和 owner-return builder；不接 collector、不运行 optimizer。

早期 agent dispatch 与 ragged low path。 接入 actor-only strict low actor、active-set low critic、high/low recurrent ledgers；legacy/R30 signatures 保持不变。

collector/checkpoint 接线。 接入双快照 membership transaction和严格 schema-3 save/load；仍不启动真实环境。

只执行一个高信息量证据源：单一集成 production transaction trace。

该唯一证据源应是一条 hand-authored、deterministic、无真实环境和无训练的完整事件轨迹，同时覆盖：

genuine join
concurrent frontier with m >= 2
KEEP and SET
survivor continuation
temporary leave with pre-removal bootstrap
rejoin from frozen hidden
terminal leave
ragged low scalar/packed replay
PPO update truncation and actor-invalid high continuation
schema-3 live-state save/resume
F0/F1 byte-equal modules
common-support relative-logit audit

它不是另一个编号 toy gate，也不是多个并行试验；它是对同一生产 transaction、ledger 和 checkpoint 的端到端工程证据。

单一 trace 的结果	对假设组合的更新
所有 lifecycle/replay/checkpoint parity 精确通过，且 F1 的 earlier SET 对 later common-support relative logits 有非零影响	H2 显著下降；H1 仅保留为“结构上已集成”；H0 仍是 mandatory baseline。在此停止，不得据此声称 usefulness 或启动训练。
所有 correctness 检查通过，但 F1 只改变 mask、产生 action-independent shift，或在有效 concurrent frontier 上与 F0 分布完全相同	H1 归约并退休；裁决转为 STOP_AT_F0。不再做 isolated AR gate。
lifecycle、pre-removal value、ragged replay、policy-version 或 schema-3 任一不一致	H2 成为主解释；该实现证据无效。只允许修正已命名的合同/实现缺陷，不产生下一条算法路线或实验。
通过 trace 必须引入永久 identity、slot、F1-only capacity、team latent、graph、learned order 或 learned hazard	当前 F1 架构不闭合；直接 STOP_AT_F0，而不是堆叠模块。

精确停止点： durable acceptance JSON 写出并复核后立即停止；不得启动真实环境 reset、rollout、optimizer training、benchmark、F0/F1 utility comparison或新的 numbered gate。原计划所列的 focused checks 本来就只能支持 engineering evidence，不能支持 cooperation、learnability 或 F1 advantage。

8. Strongest ordinary-MARL objection

最强 ordinary-MARL 基线不是旧的同步 fixed-N controller，而是完整匹配基础设施的 F0 Active-Set Scheduled Recurrent MARL。它已经拥有：

episode-internal join/leave/rejoin；

survivor hidden 与 skill continuity；

exogenous staggered per-member opportunity；

variable realized lifetime；

skill-conditioned recurrent low actor；

centralized active-set critic；

exact categorical likelihood；

member-owned duration credit；

与 F1 相同的 collector、ledger、checkpoint 和数据暴露。

因此 F1 必须证明的不是“能处理 variable N”或“能做异步 lifetime”，而只有一个极窄增量：同一 concurrent frontier 内，earlier applied edit 是否对 later token 的 common-support learned relative scores产生有用因果影响。

ordinary-MARL 的最强反对意见是：

独立的 per-member gap 很可能产生大量 singleton frontier；当 m=1 时没有 earlier token，F1 与 F0 完全相同。

即使 m>1，sum/count summary 的改变也可能只形成所有合法动作共有的 logit 平移，softmax 会将其消去。

变化也可能只影响 legality mask，而不是 common-support learned scores。

random frontier order 下，prefix 影响可能交换对称地平均掉。

即使 raw prefix gradient 非零，也可能既不改变 action distribution，也不提高 cooperative utility。

这正是 reduction theorem 已形式化的边界；R49 的 prefix-gradient PASS 不能反驳它。

所以本轮收敛后的组合不是“F1 为唯一永久路线”，而是：

F0：强制保留、尚未被击败的 ordinary-MARL 解释
F1：经修改计划后才可接受集成审计的条件性假设
learned event time：继续 deferred
其他退休路线：不恢复、不调参、不扩种子、不改阈值

当前证据支持的是修正实现计划并只保留一个集成工程证据源，不支持新算法、并行执行或任何训练启动。

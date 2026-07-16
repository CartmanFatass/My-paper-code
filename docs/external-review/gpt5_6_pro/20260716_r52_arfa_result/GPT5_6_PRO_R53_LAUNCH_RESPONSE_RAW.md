裁决
CONFIRM_R53_RCMA_G0_LAUNCH_EXACT
	​


四个缺失定义均可在不改变既定因果边、环境目标、模型宽度、预算、阈值、比较器或禁止救援条款的情况下闭合。R53 现在可以按以下唯一合同实现；不得在实现时另行猜测字段、时钟或统计语义。该裁决严格保持既定路线：

observable residual capacity→capacity-feasible AR support→stochastic-to-deterministic mode transport→shared variable-N evaluation.
R53-RCMA-G0 统一 launch-exact 合同
项目	唯一实现定义
基本环境	N∈{2,3,4,5,6}；P
N
	​

=⌊N/2⌋ persistent queues；B
N
	​

=N+1−P
N
	​

 burst queues；K
N
	​

=N+1；episode horizon H=16。Persistent arrivals 位于 t={0,2,4,6,8,10,12,14}；burst waves 位于 t={3,9}；burst initial deadline 为 3。所有中间 reward 为 0，终局 U=
F
P
	​

F
B
	​

	​

。
Member encoder 的两个 actor-visible 字段，顺序固定	member[0] = has_previous_queue：当前 focal agent 是否拥有一个上一 primitive step 的选择；reset 时为 0，完成第一次选择后为 1。member[1] = served_previous_step：上一选择是否从所选 queue 实际移除了一单位 work；reset 时为 0。两者均为 float32 二元量，不做额外归一化。
七维 queue view，顺序固定	queue[0] active；queue[1] backlog / 8；queue[2] new_arrival；queue[3] deadline_remaining / 3；queue[4] cumulative_served / cumulative_arrived；queue[5] expired_fraction；queue[6] selected_previous_step_count / N。所有字段均为 actor-visible。
Queue edge cases	全部 K=N+1 个 queues 在整个 episode 中始终 action-active，包括空 queue、当前无 live job 的 burst queue和已有 expired history 的 queue。Residual-capacity mask 是唯一动态 feasibility mask。cumulative_served/cumulative_arrived 在 denominator 为 0 时定义为 0。Persistent queue 的 expired_fraction=0；burst queue 在尚无 arrival 时也为 0，之后为 expired_jobs / cumulative_burst_arrivals。Persistent queue 或无 live burst job时 deadline_remaining=0。Step 0 的 selected_previous_step_count/N=0。
Queue backlog 语义	Persistent queue 的 backlog 为尚未服务的累计 work units，最大为 8。Burst queue 的 backlog 为当前 live job 的 0/1 work；仍按注册公式除以 8，而不是按 queue type 使用不同尺度。Expired job 的当前 backlog 变为 0，但仍计入累计 expired fraction。
New-arrival 语义	在当前 step 的 arrivals 已写入、但 observation 尚未生成时设置。仅在该 arrival step 为 1，下一 step 开始前清零。Persistent queue 在每个偶数 arrival step为1；burst queue在 t=3,9 为1。
Previous-queue reset	Episode reset时：previous_queue=-1、has_previous_queue=0、served_previous_step=0。第一次 action 的 is_previous_queue_for_focal 在所有 K 个 queue positions 上均为0，不虚构 depot或默认queue。
Previous-queue update	每个step执行完service后，无论所选queue是否为空，都设置 previous_queue_i ← selected_queue_i。下一step对该queue的relation为1。若选择空queue，served_previous_step=0，但previous queue仍更新。该状态只表示紧邻的上一primitive action；每step被新选择覆盖。更早历史只能通过GRU保存。它不包含agent ID、slot、固定角色或membership身份。
Focal relation	对当前focal agent和每个presented queue，is_previous_queue_for_focal = 1[canonical_queue == previous_queue_i]。Reset首步为全零；之后严格one-hot。它作为queue key的一个附加标量输入，不进入七维queue encoder。
Residual capacity	每个primitive step、每个queue初始化 c
q
(0)
	​

=1。按外生agent order顺序采样；第 j 个agent选择queue q 后立刻令 c
q
(j)
	​

=0。所有后序agents对该queue的logit设为 −∞。空queue也消耗该step的容量。下一个primitive step全部capacity重置为1。不得根据backlog、arrival、deadline、queue type或reward额外mask。
Actor pooling与cardinality	沿用已验证R52 set-pointer substrate：共享member encoder和queue encoder；active members与全部queues分别mean-pool。Member-pool第一个coordinate加入 log(1+N)，queue-pool第一个coordinate加入 log(1+K)。这些cardinality量为actor-visible generic set statistics，不是learned size embedding。
Actor query	Member encoder：2 → 32 → 32，GELU。Queue encoder：7 → 32 → 32，GELU。GRU hidden 32。Query输入严格为 [focal_member_embedding, member_pool, queue_pool, focal_GRU_hidden]，共128维，经 128 → 64 → 32。
Queue key	每个queue key输入严格为 [queue_embedding(32), residual_capacity(1), is_previous_queue_for_focal(1)]，即34维，经 34 → 32。Logit为query与key的缩放点积。Queue type、reward和oracle priority均不输入。
Centralized critic完整输入	Pre-action critic输入为 [member_pool(32), queue_pool(32), critic_fields(4)]，共68维，经 68 → 64 → 1。四个critic-only scalars顺序固定为：① t / 16；② total_persistent_backlog / (8P_N)；③ cumulative_persistent_units_served / (8P_N)；④ timely_burst_jobs_completed / (2B_N)。四个denominator在注册的 N≥2 下均非零。Actor不得读取这四个scalars。Critic不读取当前step的AR prefix、residual capacities或已经采样的actions。
参数量	Member input由R52的6维降至2维，减少 4×32=128；queue input由8维降至7维，减少32；其余query、key、GRU和四维critic fields保持同形状。因此 24,897−160=24,737，与注册值严格一致。
Queue presentation	每个episode采样一个anonymous queue-presentation permutation，并在该16-step episode内固定；不同episodes重新采样。Canonical queue key和presentation permutation存入ledger，但queue key不输入网络。这是对R52已验证ledger方式的显式继承。
Agent order	每个primitive step独立采样一个active-agent permutation，shared和对应specialist使用相同order。Order必须存储并在teacher-forced replay时原样使用；不学习order。
Sampling uniforms	每个step、每个AR position预生成一个categorical uniform。Shared和对应specialist使用同一uniform ledger；sample与replay使用同一动态capacity support。
Within-step order 1：arrivals	Step t 开始先将全部new_arrival清零。若 t 为偶数，则每个persistent queue增加1个backlog unit、累计arrival加1，并设置new_arrival=1。若 t∈{3,9}，则每个burst queue生成一个work=1、deadline=3的live job，累计burst arrival加1，并设置new_arrival=1。
Within-step order 2：observation	Arrivals写入后构造member view、queue view和critic fields。因此当前step的新arrival和初始deadline立即可见。此时cumulative_arrived包含当前arrival，而cumulative_served尚不包含当前step的service。
Within-step order 3：RCMA actions	所有queue capacity初始化为1；按存储的external agent order执行sequential pointer choices。每次选择后立即更新capacity mask，再为后序agent计算logits。
Within-step order 4：service	每个被唯一选择的queue最多服务1个unit。Persistent queue若backlog>0则backlog减1、cumulative served加1。Live burst queue若work=1则及时完成、work变0、timely completion加1。选择空queue不产生service。
Within-step order 5：deadline与expiration	对service后仍live且未完成的burst jobs，deadline减1。若由1降至0，则在本step结束时立即expired，不能在未来补服务，也不能增加timely completion。
Within-step order 6：selection history	在service和expiration后，将当前每个agent的selected queue写为下一step的previous_queue；记录是否实际served；对每个queue记录当前step的selected count。由于RCMA，该count只可能为0或1。
Within-step order 7：terminal metric	仅在 t=15 完成上述全部transition后计算 F
P
	​

=1−∑
p
	​

q
p,16
	​

/(8P
N
	​

)、F
B
	​

=timely completions/(2B
N
	​

)、U=
F
P
	​

F
B
	​

	​

，并把 U 作为唯一非零reward。
Burst service windows	t=3 arrival：observation时deadline=3，可在整数steps {3,4,5} 服务；若三步均未服务，在step 5结束时expired，step 6已不可完成。t=9 arrival：可在 {9,10,11} 服务；未服务则在step 11结束时expired。
Constructive M0 schedule	每个偶数persistent-arrival step，为每个persistent queue指派一个不同agent；每个burst-wave step t=3,9，为全部 B
N
	​

 burst queues各指派一个不同agent，剩余 P
N
	​

−1 agents选择不同且当前为空的queues；其他steps执行任意injective queue assignment。因为persistent arrivals与burst waves不重合且 B
N
	​

≤N，此schedule对全部 N 产生 F
P
	​

=F
B
	​

=U=1。
Negative schedules	Persistent-only schedule服务全部persistent arrivals但不服务burst，得到 F
P
	​

=1,F
B
	​

=0,U=0。Burst-only schedule及时服务全部burst但不服务persistent，得到 F
P
	​

=0,F
B
	​

=1,U=0。
Evaluation ledger	对每个 N 用seed 83053一次性生成128个episode ledgers。相同arrival schedule、queue presentation、external agent order和categorical uniforms同时用于：zero stochastic、zero deterministic、final stochastic、final deterministic，以及shared和对应specialist。Deterministic evaluation忽略uniforms，但使用相同其余ledger。
Deterministic decode	按存储的external agent order进行sequential greedy decode；每个position在当前residual-capacity-feasible support内选择最大logit。发生精确tie时选择presented-order中最小index，即标准argmax第一项。选择后立即更新capacity，再解码下一个agent。禁止temperature、beam search、joint MAP或事后修复。
Bootstrap unit	唯一cluster是同一 N 下的完整paired episode index。每次bootstrap重采样episode indices，并同时携带该episode的shared、specialist、zero、final、stochastic和deterministic记录。重复10,000次，seed 93053，使用percentile 95% interval。
Per-N gaps	Stochastic-to-deterministic gap按同一episode计算 U
e
stoch
	​

−U
e
det
	​

。Final-minus-zero按同一episode计算 U
e,final
det
	​

−U
e,zero
det
	​

。两者均在每个 N 内paired bootstrap。
Blocks	Final deterministic的128个episodes按ledger index固定分成四个连续32-episode blocks。Block gate直接使用四个arithmetic means，不做bootstrap或重排。Shared和specialist使用完全相同的block indices。
Macro intervals	每个bootstrap replicate在五个 N 内分别重采样128个paired episode indices，先计算每个 N 的mean difference，再对五个 N 等权平均。不得按agent-token数或 N 加权。Shared-versus-specialist noninferiority和shared final-minus-zero macro均采用此规则。
Ratio gates	Within-N shared/specialist ratio和equal-N macro ratio仍是预注册的full-sample point-estimate gates。若结果JSON额外输出ratio CIs，必须用上述paired episode bootstrap：同一resample同时形成numerator和denominator；这些CI仅为diagnostic，不取代注册的point thresholds。
训练曝光	固定100 balanced cycles、500 N-specific batches/arm、16 episodes/batch、16 steps/episode、128K transitions/arm、512K tokens/arm、500 shared optimizer steps、100 steps/specialist、PPO epoch 1、无batch reuse。不得修改。

该定义显式保留了R52已验证的anonymous pooling、cardinality injection、recurrent pointer、stored-order replay和pre-action scalar critic结构，同时只把R53注册的residual capacity与previous-queue relation加入queue key。R52基底确实使用mean member/entity pools、log(1+N) cardinality injection、pre-action pooled critic和逐token pointer replay；R53的24,737参数量也与上述输入维度严格一致。

Launch-exact M0

必须全部成立：

P
N
	​

=⌊N/2⌋、B
N
	​

=N+1−P
N
	​

、K
N
	​

=N+1，且arrival counts、deadline和horizon精确。

两维member view、七维queue view、previous-queue relation、四维critic-only fields及其顺序、归一化和zero conventions与上表一致。

全部queues始终action-active；除residual capacity外没有任何oracle feasibility mask。

Reset首步relation全零；之后严格one-hot；选择空queue也必须更新previous queue。

Persistent和burst arrivals发生在observation之前；service发生在deadline decrement之前。

t=3 jobs只可在3、4、5服务；t=9 jobs只可在9、10、11服务。

每queue每step最多被一个agent选择和服务；sampling、replay和deterministic decode使用同一动态support。

Constructive、persistent-only和burst-only schedules分别产生 U=1,0,0。

全部中间reward为0，terminal reward逐episode严格等于
F
P
	​

F
B
	​

	​

。

无agent ID、slot、queue-type label、oracle priority、skill、KEEP/SET、shaping或intrinsic输入。

Exact model parameter count为24,737，state-dict shape对所有 N 一致。

Shared与specialists初始参数逐位相同，训练/evaluation ledgers严格配对。

精确达到128K transitions/arm、25,600/N、512K tokens/arm、500 shared steps、100 steps/specialist、PPO epoch 1，无数据复用。

Sample/replay log-probability、dynamic-mask、prefix、previous-relation和hidden误差均 ≤10
−6
；masked probability mass为0。

Relevant modules均有有限非零gradient exposure和parameter drift；所有参数有限。

Exact-final checkpoint reload误差为0。

Zero/final、stochastic/deterministic、shared/specialist evaluation均使用注册的同一paired ledgers和128 episodes/N。

M0失败：

INVALID_R53_RCMA_WIRING

唯一动作：只修复被明确定位的transition、input、previous-state、capacity support、reward、ledger、replay、count、statistics或checkpoint defect，并按同一合同重跑。

Launch-exact M1：fixed-N specialists

每个 N 必须同时满足：

P
train
	​

(U>0)≥0.50,
U
ˉ
N
spec,stoch
	​

≥0.70,
U
ˉ
N
spec,det
	​

≥0.65,
F
ˉ
P,N
spec,det
	​

≥0.70,
F
ˉ
B,N
spec,det
	​

≥0.70,
UCB
95
	​

[U
N
spec,stoch
	​

−U
N
spec,det
	​

]<0.15,
LCB
95
	​

[U
N,final
spec,det
	​

−U
N,zero
spec,det
	​

]>0.15.

四个连续32-episode deterministic blocks中至少三个满足：

U
ˉ
N,block
spec,det
	​

≥0.60.

Equal-N deterministic macro：

U
ˉ
spec,det
≥0.70.

M0通过但M1失败：

NO_ACCESS_R53_RCMA_SPECIALISTS

唯一动作：永久退休精确AMQA dynamics、terminal utility、七维queue view、previous-queue contract、residual-capacity action support及stochastic-to-deterministic transport gate；shared结果全部隔离。

Launch-exact M2：shared variable-N

每个 N 必须满足：

U
ˉ
N
shared,stoch
	​

≥0.70,
U
ˉ
N
shared,det
	​

≥0.65,
F
ˉ
P,N
shared,det
	​

≥0.70,
F
ˉ
B,N
shared,det
	​

≥0.70,
UCB
95
	​

[U
N
shared,stoch
	​

−U
N
shared,det
	​

]<0.15.

并要求：

U
ˉ
shared,det
≥0.70,
N
min
	​

U
ˉ
N
spec,det
	​

+10
−8
U
ˉ
N
shared,det
	​

	​

≥0.85,
U
ˉ
spec,det
+10
−8
U
ˉ
shared,det
	​

≥0.90,
LCB
95
	​

[
5
1
	​

N
∑
	​

(U
N
shared,det
	​

−U
N
spec,det
	​

)]>−0.08,
LCB
95
	​

[
U
ˉ
final
shared,det
	​

−
U
ˉ
zero
shared,det
	​

]>0.20.

M0、M1通过但M2失败：

VALID_FAIL_R53_SHARED_VARIABLE_N

唯一动作：永久退休精确shared RCMA contract，并停止当前variable-N learning line，进入一次只读架构失败审查。

M0、M1、M2全部通过：

PASS_R53_RCMA_VARIABLE_N

唯一下一动作：只允许在同一AMQA、同一RCMA policy和同一terminal utility上注册一次within-episode exogenous join/leave与membership-censoring gate。不得进入skills、variable lifetime、intrinsic reward、learned admission、S7/UAV、mean field或field slots。

永久 no-rescue 边界

以下均禁止：

重跑或修改R52；

给R52 specialists追加updates、epochs或新evaluation decoder；

修改R53的128K transitions、500/100 optimizer exposure、PPO epoch、seeds、model width或24,737参数规模；

修改arrival schedule、deadline、capacity 1、terminal utility或M0/M1/M2阈值；

根据backlog、deadline、arrival、queue type或reward增加额外action mask；

temperature、beam search、joint MAP、best checkpoint或post-hoc action repair；

增加训练seed、预算、model width或数据复用；

agent ID、slot-specific head、learned agent order或learned admission；

environment-specific intrinsic reward或中间shaping；

在R53并行加入mean field、field slots、skills、KEEP/SET、variable k 或variable lifetime；

通过改统计cluster、macro weighting、ratio定义或deterministic tie-break救援有效失败。

有效M1或M2失败只能触发其注册的永久退休分支，不能通过结果后修改合同重开。该边界符合仓库关于“有效失败不得通过预算、seed、阈值、reward或model size重新解释”的因果纪律。

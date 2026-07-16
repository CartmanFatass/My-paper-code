1. Final verdict
MODIFY_PLAN

F1 仍是可实施且与 F0 代数上可区分的 leading hypothesis，但在生命周期唯一所有权、临时离开双快照、严格 live-resume、独立 event low-policy、pre-token critic、比较口径和 common-support 证据全部冻结前，不应开始生产代码。

2. Claim adjudication
2.1 证据事实与推断
仓库事实

当前 production low path 不能直接接受 ragged active-member rows：

act_low_batch 先把每个环境观测拟合成固定 [n_agents, obs_dim]；

flatten 数量固定为 batch_size * n_agents；

centralized state 和 team code 被复制到所有固定成员；

critic 显式接收 torch.arange(n_agents) 形成的 agent ID；

action、value 和 recurrent hidden 最终重新 reshape 为 [batch_size, n_agents, ...]。

当前 train_loop 先构造并 reset collector，再根据 env.n_uavs 构造固定-N StandaloneProcessAgent，最后才调用 checkpoint loader；这不能满足 event schema-3 在任何 fixed-N runtime 被创建前完成模式判断与 live-state restore 的要求。

当前 collector 只有：

reset
step
spec
close

以及固定 n_uavs spec；没有 membership transaction、pre/post membership snapshots、pending transaction 或 simulator snapshot/restore。

当前 checkpoint loader 对多个非核心模块使用 strict=False，并允许 legacy-to-R30 migration；它不是 event-mode 所需的独立 fail-closed schema-3 loader。

架构合同写的是“collector-owned table”，而实施计划写的是新 event module “owns the lifecycle table”，属于真实的双权威冲突。

R49 确实证明了接口级能力，包括：

active-only set encoding；

permutation/padding invariance；

recorded external order；

teacher-forced replay；

join/leaver/survivor semantics；

prefix gradient path。

但它是无环境、无奖励、无 optimizer、无 checkpoint 的 synthetic gate；其模型还使用 mean pooling、processed 输入以及独立 KEEP head，与当前合同的 sum/count、native K-way incumbent mapping 不同，因此不能作为 production implementation 导入。

R49 的 “prefix actionability” 判据本质上是 Jacobian norm；它证明存在计算路径，但没有证明 earlier prefix 会改变共同合法支持上的相对动作分布。

本轮没有新的 raw experiment result 被提升为科学证据，R49 仍然只是 interface-level evidence。

我的推断

因此目前有三个活跃解释和一个 deferred 解释：

假设	因果主张	当前地位
H0 / F0	active-set scheduling、lifecycle routing、skill-conditioned recurrent actor 与 γ
Δ
 credit 已足够；给定初始 active-set context 后，各成员 mark 条件独立	最强 ordinary-MARL 零假设，尚未被击败
H1 / F1	concurrent event frontier 中 earlier applied edit 会改变 later member 在共同合法支持上的 learned relative scores，因此 joint conditional assignment 不可约	结构上可行，但尚未集成，也无 usefulness 证据
H2	当前最大风险是 lifecycle、snapshot、ragged replay 或 resume 的 implementation confound，而不是 F0/F1 的真实算法差异	高度活跃，必须先消除
H
time
	​

	exogenous opportunity clock 本身是瓶颈，必须学习 hazard/point process	deferred；当前无证据授权
2.2 八项争议裁决
1. Dedicated trainable event low policy
ACCEPT

应新增一个可训练的 event-mode low policy，而不是：

冻结 legacy low actor 并包一层 ragged adapter；

把 ragged 接口塞进 StrictHMASDMAPPOLowLevelPolicy；

修改 legacy class 的 checkpoint/state-dict 合同。

该新对象保留计算语义：

MLPBase(o
i
	​

)→FiLM(z
i
	​

)→RNN→ACT,

并保持：

π
l
	​

(a
i
	​

∣o
i
	​

,z
i
	​

).

但其 API 必须是：

actor-only flat active-row inference；

lifecycle-owned recurrent chunk replay；

无 team-code、agent-ID 或固定 roster 输入；

与单独的 active-set low critic 解耦。

F0 与 F1 使用同一个 class、相同参数键、相同初始化、相同 optimizer contract。Legacy class 与旧 checkpoint 完全不改，也不做 schema-1/2 权重迁移。Codex 的这一边界正确。

2. Single authoritative lifecycle owner
ACCEPT_WITH_EXACT_DOMAIN_SPLIT

每个 vector environment 必须只有一个 policy-runtime LifecycleStore。

精确所有权为：

environment worker:
    physical simulator state
    physical membership facts
    environment RNG

collector:
    typed transport transaction
    no policy lifecycle state

event runtime:
    sole LifecycleStore
    skill / age / hidden / gap
    membership epoch validation
    open event and low traces
    policy version

也就是说：

worker 是物理事实权威；

event runtime 是策略生命周期权威；

collector 只是事务输送者；

StandaloneProcessAgent、worker 和 collector 均不得保存 policy lifecycle shadow copy。

架构合同中的 collector-owned table 必须删除并替换为上述规则。

3. Two-snapshot temporary-leave transaction
ACCEPT — MANDATORY

每个 membership boundary 必须产生一个原子事务：

pre_membership_boundary_snapshot
    post-transition
    pre-removal active set
    exact critic source tensors

atomic_membership_delta
    JOIN
    TEMPORARY_LEAVE
    TERMINAL_LEAVE
    REJOIN
    lifecycle key + membership epoch

post_membership_pre_policy_snapshot
    post-delta active set
    event flags
    new frontier
    initial working commitment set C^(0)

语义不可交换：

temporary leaver 的旧 trace 只能用第一个 snapshot bootstrap；

membership delta 必须一次性应用；

新 frontier、F0 initial summary 和 F1 working set 只能来自第三个 snapshot；

sampled replacement gap 与 frontier order 必须写入 ledger，尽管没有 policy log-probability。

Temporary leave 同时关闭：

该成员的高层 owner trace；

当前低层 recurrent chunk。

两者均为 critic-only truncation，不产生 actor ratio。该成员的 skill、age、gap 和 hidden 被冻结；inactive 期间不积累 reward、age 或 gap decrement。REJOIN 恢复保存状态并创建一个新的 policy opportunity。

4. Exact live resume requires simulator/collector snapshot
ACCEPT — FAIL CLOSED

只有模型、optimizer、normalizer、LifecycleStore 和 RNG 不足以精确恢复 mid-episode 运行。Schema 3 还必须保存：

当前 observation/state boundary；

collector active presentation；

pending membership transaction；

worker/environment snapshot；

environment RNG；

collector pending command/response state；

snapshot capability name 与 version。

若选定 collector/environment 无法完整 round-trip，这个环境上的 event-mode live resume 必须硬失败，不能退化成 reset 后继续。

必须区分：

live_resume:
    requires all runtime + simulator state

fresh_reset_eval:
    model/normalizer only
    explicit runtime_state_absent_for_fresh_eval=true

此外，resume header 必须在创建 collector、reset 环境或构造 fixed-N agent 之前读取。

5. Exact pre-token critic context
ACCEPT

对 frontier 中第 j 个 token，old value 必须来自：

V
ϕ
	​

(u
σ
j
	​

	​

,h
σ
j
	​

pre
	​

,g(C
t
j−1
	​

),membership-event flags).

其中：

C
t
j−1
	​

 是该 token 之前已经应用 earlier edits 的精确 working commitment set；

不允许用整个 event 的初始 value 重复给所有 token；

不允许 replay 时从当前 roster 重构；

不允许读 sampled action、post-token set 或新采样的未来 gap。

F0 与 F1 使用相同的 critic 和同一 pre-token context。两者唯一差异仍然是：

F0 actor summary = g(C^(0))
F1 actor summary = g(C^(j-1))
6. Comparison contract
ACCEPT “SAME DATA-GENERATION CONTRACT”; REJECT “IDENTICAL REALIZED DATA”

F0/F1 必须匹配：

model graph 和 parameter count；

paired initialization；

collector transaction schema；

reset distribution；

external membership and opportunity RNG contract；

reward；

low actor/critic；

replay；

update budget；

evaluator。

但一旦两臂因 learned action distribution 不同而选择不同动作，后续 on-policy state visitation 合法地发生分叉。强制两臂继续使用相同 realized trajectories 会改变 estimand。

因此文档中的 same data exposure 应统一替换为：

same data-generation contract and matched exposure budget

在当前 deterministic engineering trace 中，两臂使用同一个 hand-authored source transaction；未来若训练，只配对外生随机性，不配对 treatment-induced trajectory。

7. F1 structural evidence
ACCEPT COMMON-SUPPORT RELATIVE-SCORE EVIDENCE; REJECT RAW GRADIENT AS SUFFICIENT

选择同一 later token、同一 focal state、同一 incumbent skill，并构造两个合法 earlier prefixes p,p
′
。令其共同合法支持为：

S=supp(p)∩supp(p
′
),∣S∣≥2.

定义 centered logits：

ℓ
a
	​

(p)=ℓ
a
	​

(p)−
∣S∣
1
	​

b∈S
∑
	​

ℓ
b
	​

(p),

以及：

D
prefix
	​

=
a∈S
max
	​

	​

ℓ
a
	​

(p)−
ℓ
a
	​

(p
′
)
	​

.

Focused test 必须包含两个确定性 parameter controls：

Reduction null：summary contribution 对所有 actions 相同，要求 F0/F1 完全相等；

Constructive positive control：summary 的一个维度对至少两个 action logits 使用不同固定权重。

在 1e-6 tolerance 下：

F0:
    D_prefix <= 1e-6

F1 positive control:
    D_prefix > 1e-6

只有以下变化不计为 F1 证据：

mask/support 改变；

所有 logits 的共同 additive shift；

只有 Jacobian 非零但 normalized distribution 不变；

只有某个永久顺序位置产生差异。

Codex 对 derivative-only gate 的否决正确。

8. Second tracked acceptance JSON
REJECT AS A SECOND SOURCE OF TRUTH

不需要再提交一个与 test/log 重复的 acceptance JSON。

规范来源应为：

focused deterministic test：拥有所有工程 assertions；

production code：拥有实现语义；

logs/ 下唯一 canonical run output；

CURRENT_WORK.md：记录 exact command、commit、log path 和状态。

R49 自己也把 generated result 写入 run-root，并把授权 claim 限定为 interface correctness only。

只有将来某个科学主张无法从 test、代码和唯一 owning log 审计时，才可提交一个科学 result artifact；现在复制第二份 JSON 只会制造漂移。

3. Binding plan corrections

以下是开始代码前必须一次性关闭的有限修正。

3.1 Correctness corrections

统一生命周期所有权

架构合同和实施计划统一为：

physical membership owner = environment worker
transaction carrier       = collector
policy lifecycle owner    = event runtime LifecycleStore

冻结 typed membership transaction

事务必须包含：

pre-membership snapshot；

typed atomic delta；

post-membership/pre-policy snapshot；

lifecycle key；

membership epoch；

event timestamp；

stale-event rejection data。

冻结 dedicated event low API

新 low actor 必须是 trainable、actor-only、active-flat、skill-conditioned、lifecycle recurrent；低 critic 是独立 active-set critic。禁止 frozen wrapper、agent ID、team code、legacy critic 和 live actor copy。

把 ragged schemas 从说明性结构升级为 normative schema

Persistent high-event row 必须保存 source tensors，而不是只保存临时 row index：

owner key/epoch；

event/frontier/order；

initial active set；

exact pre-token working set；

legal mask；

combined action；

old log-prob/value；

pre-token recurrent state；

elapsed physical time；

policy version；

terminal/temporary-leave/update-truncation kind。

Persistent low row/chunk 至少保存：

owner key/epoch；

observation；

skill；

primitive action/log-prob/value；

actor/critic hidden before；

active-set critic source tensors；

reward；

terminal/truncation；

policy version。

Ephemeral packed row index 只能在当前 collector call 内使用，不能成为 replay 身份。

冻结 token critic 时序

每个 token 使用自己的 C
j−1
 pre-token centralized context；collection 和 replay 必须使用同一 source arrays。

冻结 leave/rejoin 的高低层边界

temporary leave：pre-removal critic bootstrap；

absence：无 actor row、无 reward ownership、无 age/gap progression；

rejoin：恢复 hidden/skill/age，开始新 chunk 和新 policy event；

terminal leave：bootstrap zero，销毁 state；

genuine join：zero hidden、null incumbent、只能 SET。

重写 schema-3

Mandatory fields增加：

simulator snapshot；

environment RNG；

collector presentation；

pending transaction；

snapshot capability/version；

current observation/state boundary。

Live resume 缺任何字段均失败。

早期 dispatch

train.py 必须先读取 config/checkpoint header，再决定：

legacy/R30 -> existing fixed-N path
event      -> event collector + event runtime

Event resume 不得先调用 reset_all()，也不得构造 StandaloneProcessAgent。

修正比较术语

全部 same data、same exposure 的模糊描述替换为：

same data-generation contract
matched external RNG contract
matched exposure budget
naturally divergent on-policy trajectories

替换 F1 acceptance check

删除 derivative-only PASS；改为 reduction null + constructive common-support relative-score check。

3.2 Final-capability map

该 map 是架构能力合同，不是经验 PASS：

Family	Episode-internal join/leave/rejoin	Survivor continuity	Heterogeneous realized lifetime	Skill bottleneck	Learned joint coupling	当前地位
F0 active-set scheduled MARL	是	是	是，来自 exogenous opportunities + KEEP/SET	是	否；common-support scores 条件独立	强制 ordinary baseline
F1 event-frontier editor	与 F0 相同	与 F0 相同	与 F0 相同	与 F0 相同	是，限于 applied-prefix relative scores	leading hypothesis，未获 usefulness 证据
Learned event-time family	理论可支持	理论可支持	原生	可支持	可独立或联合	deferred

F0/F1 之外，H2 是 correctness explanation，不是新增 architecture family。

3.3 Replacement ledger
删除出 event path，但不删除 legacy 文件

fixed [num_envs,n_agents,...] lifecycle arrays；

fixed [T,B,N] replay；

fixed-N HighCheckBuffer；

policy-visible agent ID、slot ID、lifecycle key；

team-code-conditioned low critic；

sampled team latent/bridge；

duration head；

full-team renewal barrier；

dummy/padded members的语义角色；

legacy/R30 checkpoint migration；

permissive partial loading；

lifecycle shadow copies。

保留其功能，而非固定实现

π
l
	​

(a
i
	​

∣o
i
	​

,z
i
	​

)；

HMASD-scale recurrent actor computation；

native K-way incumbent-is-KEEP mapping；

applied working-set teacher forcing；

external task reward；

exact PPO old-log-prob replay；

survivor recurrent continuity；

per-owner γ
Δ
 return 与 event-depth GAE；

F0 完整 ordinary baseline；

legacy/R30 paths 原样可用。

只新增必要 correctness interfaces

一个 LifecycleStore；

一个 typed two-snapshot membership transaction；

一个 trainable actor-only event low policy；

一个 shared active-set low critic；

ragged high/low ledgers；

strict snapshot-aware schema-3 loader；

一个 focused deterministic transaction test。

3.4 Deferred，不得预装

sparse graph；

attention；

fixed slots；

critical residual；

team latent；

q
D
	​

/q
d
	​

 新 reward；

intrinsic reward；

learned order；

independent hazard；

point process；

service priority；

environment-specific fields；

reward shaping。

4. File/interface boundary

我接受 Codex 的文件边界，但作以下明确化。

文件	允许的唯一变化
docs/research/designs/VARIABLE_N_LIFETIME_EVENT_ARCHITECTURE_CONTRACT.md	生命周期所有权、双快照、比较口径、live-resume 和 F0/F1 reduction 条款
docs/research/designs/VARIABLE_N_LIFETIME_EVENT_IMPLEMENTATION_PLAN.md	dedicated low API、normative row schemas、pre-token critic、schema-3、distributional F1 check、实施顺序
ha_ctse_process/variable_roster_event.py 新增	LifecycleStore、typed transaction、active packer、F0/F1 shared commitment model、event critic、event low actor、active-set low critic、ragged ledgers、returns、schema-3 payload
ha_ctse_process/train.py	在 collector/reset/fixed-agent 构造前读取 mode/header；event runtime 直接分派；独立 strict schema-3 load/save
ha_ctse_process/collectors.py	default-off typed two-snapshot transaction；snapshot/restore capability；worker physical-state transport
tests/ha_ctse_process_variable_roster_event_test.py 新增	唯一 deterministic production transaction trace
memory/CURRENT_WORK.md	focused test 执行后，只记录 commit、command、canonical log path 和状态
standalone_agent.py
不列为 required modification

原因：

event mode 不应通过 StandaloneProcessAgent dispatch；

不应在其 fixed-N arrays 中增加 ragged shadow state；

不应改变 legacy state dict；

新模块直接使用底层 MLPBase、FiLM、RNN、ACT building blocks即可。

Codex 给出的 “no required event dispatch and no legacy state-dict change” 是正确边界。

R49 files

scripts/r49_orse.py 与 scripts/run_r49_orse_gate.py 保持只读 evidence：

不 import 到 production；

不修改为 F0/F1 production class；

不把其 separate KEEP head、mean pooling 或 derivative gate带入新实现。

明确禁止修改

r30_fixed_clock.py；

legacy HMASD/R30 checkpoint schema；

environment dynamics/reward；

intrinsic modules；

plotting scientific metrics；

retired R29–R48 mechanisms；

新 event-specific runner 或新 environment。

5. Implementation order and stop point
5.1 最小授权顺序

只修文档

完成第 3 节的 binding corrections；

确认 architecture contract 与 implementation plan 无双 owner、无含糊 resume、无 derivative-only gate。

实现 pure core

LifecycleStore；

state machine；

exogenous schedule；

F0/F1 model；

event/low ledgers；

direct return/GAE；

全部使用 hand-authored tensors。

实现 event low 与 early dispatch

dedicated trainable event low actor；

active-set critic；

ragged recurrent replay；

event schema header 在 fixed-N agent 构造前生效。

实现 collector transaction 与 strict resume

synthetic snapshot-capable collector；

double snapshots；

worker snapshot/RNG；

pending transaction；

schema-3 exact round-trip。

执行一个 focused deterministic production transaction trace

5.2 唯一高信息量证据源

该 trace 必须在同一 authored lifecycle 中覆盖：

genuine JOIN
concurrent frontier
KEEP and SET
survivor continuation
temporary LEAVE
REJOIN
terminal LEAVE
PPO policy-version truncation
actor-invalid continuation
ragged low replay
schema-3 live save/restore
permutation relabeling
F0 reduction null
F1 common-support positive control

它必须验证：

exact replay；

exact snapshot round-trip；

no routing-key input；

same F0/F1 state dict；

F0 relative-score invariance；

F1 constructive relative-score change；

direct γ
Δ
 return equality；

other-member events不推进 owner 的 λ depth。

5.3 Outcome-dependent hypothesis update
Outcome A — 任意 lifecycle/replay/resume mismatch

更新：

H2↑,H0/H1 保持未识别.

唯一动作：

只修复被点名的 correctness defect，禁止环境运行和算法解释。

Outcome B — correctness 全过，F0 invariant，F1 relative scores 改变

更新：

H2↓,H1 结构上存活,H0 仍未被经验击败.

支持的唯一结论：

F1 在生产接口中确实不是 F0 的纯重命名。

不支持 usefulness、learnability 或 integration。执行到此停止，等待独立训练/testbed 授权。

Outcome C — correctness 全过，但 F1 只有 mask、共同 additive shift 或分布不变

更新：

H1 退休,H0↑.

裁决：

STOP_AT_F0

不产生下一轮 AR 修复实验。

Outcome D — F1 只能依赖 identity、slot、F1-only capacity、team latent、graph、learned order 或 hazard 才能通过

更新：

H1 与当前约束不兼容.

裁决同样为：

STOP_AT_F0
5.4 精确停止位置

Focused test 通过或失败后都必须停止在以下边界之前：

不调用真实 make_env；

不调用真实 collector reset_all 或 step；

不创建 subprocess environment；

不对 environment data 调用任何 optimizer .step()；

不训练；

不 benchmark；

不生成科学 PASS/FAIL；

不推断 F1 优于 F0；

不进入 variable-N/lifetime task。

这与 Codex 建议的“完成 deterministic transaction test 后停止”一致。

6. Authorization
Document corrections
AUTHORIZED NOW

允许现在修改：

architecture contract；

implementation plan；

必要的 review/current-work pointers。

不得同时开始代码，以免实现再次成为隐含规范。

Production implementation after corrections
CONDITIONALLY AUTHORIZED

当且仅当第 3 节所有 binding corrections 已经进入两份设计文档，并且二者不存在 lifecycle owner、critic timing、snapshot 或 evidence contract 冲突后，授权按第 5 节顺序实施生产代码。

授权范围只到：

single focused deterministic transaction trace
	​


不需要再做一次架构路线选择，但必须严格遵守 fail-closed stop。

Training and scientific experiment
NOT AUTHORIZED

仍禁止：

真实环境 rollout；

optimizer training；

新 testbed；

R53/R55 revival；

intrinsic reward；

task shaping；

threshold/seed/budget sweep；

graph/slot/team-latent/hazard module；

variable-team 或 lifetime efficacy claim；

把 synthetic PASS 当成 integration evidence。

最终组合保持：

F1 是 leading skill-based hypothesis，F0 是未被击败且完全匹配的 ordinary-MARL reduction。
	​


当前继续实施的唯一理由，是一次有限的生产正确性轨迹能够同时：

消除 H2 implementation-confound；

判断 F1 是否在共同合法支持上真正超出 F0。

它不能、也不应被解释为 F1 已经可集成。

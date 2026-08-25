1. 证据有效性裁决

裁决：接受注册终局 RETIRE_SPATIAL_CARRIER_NO_DIRECT_ACCESS；保留开放组合；不接受对已退休 spatial carrier 的任何预算、容量、种子或阈值救援。

已支持的结论

实现与证据管线有效。 三个 arm 均完成注册暴露；C1-on/off 的策略初始化完全一致，semantic trainer 除 beta 外一致；high/low replay、posterior 梯度隔离、checkpoint round-trip 和 C3 optimizer/model 恢复均通过。C1 process window 确实由唯一的 lifecycle、membership epoch、policy version 和 low-row 集合所有；输入在进入 posterior 前 detach，posterior 没有行为似然，semantic score 只修改所属 low transition 的 reward，并按有效 window 长度归一化。runner 也正确执行了“实现 → carrier/direct access → semantics → task value”的冻结优先级，而不是事后选择有利分支。

精确的 Iteration-5 spatial carrier 没有建立普通 direct learner access。 Constructive controller 的 P/S/U 均为 1，random control 的正 utility 比例为 1、均值约 0.4259，所以状态机和终端回报并非不可达；但这不能替代学习访问。C3 完成 320,000 transitions 和 1,000 optimizer steps，replay/checkpoint error 为零且参数发生非零变化；最终 deterministic P/S/U=1.0000/0.526855/0.763428、stochastic U=0.724528，而 deterministic final-minus-zero utility CI95 仅为 [0.048381,0.070475,0.093140]。它失败于 short floor 和学习增量门，不是未训练或加载错误。

这个结果应表述为：

在冻结 observation、policy class、预算、优化器和 gate 下，该 spatial carrier 未提供足以承担后续算法归因的 ordinary-learning access。

它不支持“空间任务在数学上无法学习”，也没有识别究竟是 observation、任务动力学、direct policy 的信息/容量结构、PPO optimization，还是高 zero-step utility 导致的有限学习余量。C3 的 zero-step deterministic utility 已约为 0.693，其中 persistent score 约为 0.888，因此单看最终 utility 会严重高估训练所得的增量。

精确的 Iteration-5 C1 objective 没有建立 material executable semantics。 参考折选出的技能对为 1–2；其 same-input action-TV CI95 为 [0.010141,0.011219,0.012263]，12-active-step forced process-effect distance CI95 为 [0.002604,0.014579,0.033543]，两个上界都低于冻结的 1/12 materiality floor。自然占比分别约为 0.397 与 0.312，但自然频繁使用不等于 intervention control；natural-to-forced overlap 和 context/mask-matched shuffle residual 的区间都跨零。

这一负结果的解释力度比“posterior 写错了”更强：实现中的 positive process view 确实只读取 focal member 的归一化位置后果，计算相对起点位移和逐步位移，不读取 primitive action、task reward 或 named role；full/null posterior 共用 context tower、classifier，并对 skill 与 window length 分层平衡。因而本轮关闭的是这个经过约束的 position-process residual objective，而不是因为显然的 action-one-hot 或 reward leakage 才失败。

C1-on 对训练轨迹存在注册内处理效应，但没有建立语义因果或算法价值。 C1-on minus off deterministic utility CI95 为 [0.037862,0.044495,0.051137]，C1-on final-minus-zero CI95 为 [0.116801,0.129700,0.143148]。这证明 intrinsic injection 改变了 low-level optimization 或状态访问分布；由于 semantic_pass=false、task_access_pass=false、direct_access_pass=false，不能将该差异解释为可复用技能、hierarchy gain、合作改善或最终目标进展。

尚未支持或仍然混杂的结论

本轮不能判断：

hierarchy 相对强 ordinary recurrent MARL 是有益、有害还是冗余；

intrinsic reward 的正负任务因果效应；

主要缺陷是 high assignment、SMDP credit、event context、categorical interface、shared executor interference，还是 carrier access；

C1 数值效应能否迁移至未见 roster、未见 lifetime 或 UAV；

原始 HMASD 的 q_d、q_D、team latent 或 autoregressive assignment 中哪个组件导致 R41B 成功。

R41B 只是一个固定 N、单 seed、完整原始源路径的正锚：约 2.9984M transitions，最终 win/key0/key1 为 0.89/0.97/0.92；它不是任何单组件必要性的消融。

对两份发散建议的收敛修正

Gemini 提议通过扩大 width 和 transitions 恢复 spatial carrier；这直接违反本轮关闭条件，不能成为下一证据源。其 segment-information proposal 又把 primitive-action trajectory 纳入 positive view，容易退化为已退休 R29 action-information 家族；无约束连续 skill 还会删除当前 KEEP/SET lifetime 与行为概率合同，并可能只等价于更深的 flat recurrent network。

Open-Pro 对证据和优先级的解释基本成立；但其 B/C 架构和 E1/E2/E3 是待权衡假设，不是已有结论。下文保留其中可证伪的结构，并只选择一个下一证据源。

2. 加权的四候选组合

当前权重排序为：

A — access-valid evidence substrate：高权重的识别解释

D — hierarchy-null direct recurrence：中高权重的算法解释和强制 null

B — factorized discrete process executor：中低权重的层级解释

C — simplex process command：低权重、parked 的接口解释

排序表示当前相对证据，不表示只有一个方向合法。

A — Access-valid、clean-process-channel evidence substrate

机制与最终能力关系。 Iteration 5 主要暴露了一个上游识别失败：构造轨迹可达，但 ordinary learner 没有通过同-carrier access gate。A 不添加算法模块；它替换的是承担算法比较的 carrier/evidence contract。其作用是提供一个同时具有匿名 JOIN、temporary leave、REJOIN、terminal leave、survivor continuity、稀疏终端任务以及 task-neutral local process channel 的可学习基座，使后续 variable-lifetime 和 semantic hypotheses 可识别。

Estimand、比较和分支。

Δ
access
	​

=U
direct,final
	​

−U
direct,zero
	​


并同时要求 persistent、reactive/short 和总 utility 的绝对 access floors。比较对象是 constructive controller、uniform random control 和不含 high、skill、posterior、intrinsic 的 active-set direct recurrent learner。

Controls 与 direct 都通过：A 被解析为“Iteration-5-specific substrate mismatch”，B/C/D 获得可识别的后续测试入口。

Controls 通过、direct 失败：普通 access 仍未建立，B/C 不可解释，D 也未获最终支持。

Constructive/random calibration 失败：carrier 本身无效。

M0 失败：只修具体 wiring，合同不变。

将 A 与 D 区分的关键观察是：新的 access carrier 上 direct 通过，但层级语义仍重复 material null。这会说明 A 只解释了 Iteration 5 的归因失败，不能解释持续的 skill bottleneck。

Replacement ledger。 保留 typed lifecycle spine、active-only masks、survivor/rejoin continuity、terminal external objective 和 direct null；删除精确 Iteration-5 spatial carrier作为算法比较基座；替换 carrier/evidence contract；只增加一个独立的 direct-access qualification，不增加 learner 模块。

最强反证与置信度。 若最后一次严格 carrier qualification 仍出现 controls pass、direct fail，则继续制造新 toy 已没有信息增益，应停止 carrier 搜索并回到 observability/objective/ordinary learner contract。对“Iteration 5 未识别”置信度高；对“换 carrier 后 hierarchy 会成功”置信度低。

Ordinary-MARL reduction 与退休边界。 A 本身就是普通 MARL access 问题，不是 skill claim；它不使用 R29/R31/R32/R33、identity、task shaping、scheduler 或 duration catalogue。

D — Hierarchy-null active-set direct recurrent MARL

机制与最终能力关系。 删除 high assignment、skill bottleneck、semantic learner 和 policy-owned event opportunities，让 lifecycle-owned recurrent state直接在 primitive time 内实现持续、响应和恢复行为。该解释允许最终系统支持匿名 membership churn，但把“skill lifetime”还原为不可命名的 recurrent internal state，而非显式、可干预的过程变量。旧 Generic-SHORT Stage B 的 direct success和多轮 hierarchy semantic null均支持 D；Iteration-5 同-carrier direct fail又阻止把它升级成最终 verdict。

Estimand、比较和分支。

Δ
D
	​

=U
verified hierarchy,heldout
	​

−U
matched direct,heldout
	​


需要在 direct-access 已通过的同一 carrier、同信息、同训练/optimizer exposure 和未见 membership/lifetime 条件下比较。

Direct noninferior 或更优：D 上升；可解释 skill 不应集成。

Hierarchy 在保持 material semantics 时取得外部 utility 或样本效率优势：D 下降。

Hierarchy utility 上升但 semantics 坍缩：归因于容量、优化或 shortcut，不反驳 D。

两者均失去 access：carrier 不能承担该比较。

将 D 与 B/C 区分的观察是：B/C 能制造稳定过程命令，但在 held-out roster/lifetime 上不优于 direct。这会支持“语义存在但不 load-bearing”。

Replacement ledger。 保留 dynamic membership state machine、active-set encoding、centralized training critic、survivor hidden continuity；删除 high、skill、semantic objective；以 primitive autoregressive recurrent policy 替换 hierarchy；不增加学习模块。

最强反证与置信度。 唯一强反证是一个经过 shortcut-resistant audit 的 hierarchy，在信息、容量、预算和 checkpoint 规则匹配时，对未见 membership/lifetime 给出 material external advantage。置信度中高。

重要限制。 当前 C3 access instrument在每个 primitive step读取 active-set sum/count context和 earlier-action prefix；它是很强的 team-context access upper bound，不能自动等同于最终 decentralized executor。最终 D 若要集成，必须证明这些输入在执行时可获得，或改用与 hierarchy low actor 信息匹配的 direct comparator。

B — Factorized discrete process-basis executor

机制与最终能力关系。 保留三个 categorical skills、KEEP/SET、event-time credit、shared observation trunk和 decentralized execution，但以三个互斥、受限容量的 recurrent/action adapters 替换“完全共享 actor + FiLM 是唯一 skill 分隔”的执行路径。每个 active lifecycle 一次只执行一个 adapter；第一证据门不加入 intrinsic reward。这一结构试图让每个 z 真正拥有闭环状态转移，而不是依赖 classifier reward 在共享动力学中自行产生模式。

Estimand、比较和分支。

Δ
B
	​

=S
factorized
	​

−S
capacity-matched shared
	​


其中 S 同时包含：

same-snapshot primitive distribution；

固定 active-time 的物理 process consequence；

held-out lifecycle、join/rejoin、active-age stability；

natural execution overlap。

Comparator 必须用相同总参数预算的 shared-conditioning reference，新增 adapter 容量需要 inactive/sham path 匹配。

B 通过、shared失败：executor interference解释显著上升。

B 与 shared 都通过：主要问题更可能是 Iteration-5 learning pressure 或 carrier，而不是参数分隔。

Adapter 有梯度与参数变化但没有 material consequence：退休 B。

仅参数或 action logits分离、环境过程不分离：同样退休。

将 B 与 C 区分的观察是：one-hot factorized adapters已在所有 event strata 中通过，而 simplex interpolation不增加新过程区域或 held-out gain。此时 categorical interface不是必要问题。

Replacement ledger。 保留 K=3、KEEP/SET、外生机会和 event return；删除精确 Iteration-5 posterior reward作为语义生成器；替换 low recurrent/action conditioning；增加三个容量受限且互斥的 process adapters。它不能与 C、posterior、graph或learned hazard首次同时启用。

最强反证与置信度。 参数隔离可能只是把网络复制三份；容量匹配的 direct recurrent actor也可能内部实现同样模式。只有 reuse、intervention stability 和后续 transfer才有层级含义。置信度中低。

退休路线边界。 Forced branches仅做审计；不把 action information、observational effect、intervention effect或 roster complementarity变成 reward/advantage，因此不是 R29、R31、R32 或 R33。首门也无 task-shaped intrinsic、identity、scheduler或duration action。

C — Three-basis simplex process command

机制与最终能力关系。 仍只有三个共享 process bases，但把 hard z∈{0,1,2} 替换为

w
i
	​

∈Δ
2
,c
i
	​

=
k=1
∑
3
	​

w
ik
	​

b
k
	​

.

KEEP 保持当前 command，SET(w) 更新 command；realized lifetime仍是连续 active KEEP 的运行长度。它不增加 duration head、learned timing、team latent或第二 controller。C 是 B 的替代，而不是叠加。

Estimand、比较和分支。

Δ
C
	​

=G
simplex
	​

−G
one-hot
	​


在相同三个 bases、总参数、训练 exposure和 process read 下，比较 held-out start、membership strata和 roster/lifetime上的 controllability/generalization。

非顶点 command产生可重复的过程插值，并优于 one-hot：C 上升。

权重几乎总在顶点，或中间 command没有新的可预测过程：C并入B或退休。

只有 C 通过 process realizability：hard categorical interface解释上升。

B/C都通过：接口可实现，仍需后续 load-bearing task比较。

Replacement ledger。 保留 lifecycle、event opportunity、low recurrence和三个 process bases；删除 categorical embedding和 categorical SET head；以 simplex command替换 z；任何未来实现都必须记录实际连续 sample和完整 transformed density，不能采样后投影或做未记录修复。

最强反证与置信度。 Direct recurrent hidden state可能内部模拟同一连续量；C也可能只是装饰性 latent。当前没有证据证明“离散性”是主要瓶颈，故置信度低、当前 parked。

退休路线边界。 C 不通过 task reward反向穿越环境学习 latent，不使用 effect gradient或 action-information reward，不学习 timing，不增加 skill count，因此不是 R29/R31/R32/R33、scheduler-only或duration catalogue。

3. 唯一下一证据源
推荐：一次性的 clean-process-channel dynamic-roster direct-access qualification

这是唯一推荐的下一证据源。它是新的、单独注册的 carrier qualification，不是 Iteration-5 spatial carrier重跑，也不是 C1/B/C训练。

Comparator 与冻结边界

同一新 carrier 上只包含：

routing-only constructive controller；

uniform random control；

未经修改的 active-set direct recurrent learner。

禁止 high、skill、KEEP/SET、posterior、intrinsic、task shaping和semantic audit参与科学分支。

新 carrier 必须：

保留匿名 within-episode JOIN → temporary LEAVE → REJOIN/new JOIN → terminal LEAVE；

保留 survivor state continuity和终端-only P/S/U；

保留 persistent 与 reactive/short 两种时间负载；

另行暴露一个只读的 focal physical-process channel，供未来审计使用，但该 channel不进入 direct actor、critic或reward；

process channel不得包含目标、任务进度、role、reward、success、contact、phase、identity或routing key；

不是精确 Iteration-5 position/target carrier，也不修改其终局。

为避免把“换 carrier”变成隐藏预算救援，使用既有 Stage A/B access exposure和阈值：16 environments、H/rollout 80、250 updates、320,000 transitions、PPO4、1,000 optimizer steps；constructive P/S/U≥0.95，random positive fraction ≥0.20 且 mean U<0.55；direct final deterministic U≥0.70、P/S≥0.65、stochastic U≥0.60、final-minus-zero utility LCB95 >0.15。这些门已在原 direct-access contract 中定义，不因结果修改。

因果 estimand与能力边界

该 source只检验：

在保留最终 anonymous membership spine 和 clean process observability 的最小 carrier 上，普通 active-set recurrent control能否获得严格正的、组件完整的学习访问。

它是最终 variable-membership/variable-lifetime研究的上游 access prerequisite。它不检验显式 skill、natural assignment、heterogeneous learned lifetime或 hierarchy value。

冻结结果分支

Positive — PASS_CLEAN_CARRIER_DIRECT_ACCESS
Carrier calibration和direct access全部通过。A被解析为 Iteration-5-specific substrate问题；D继续作为强制 null；B/C保持live但不自动获得实现资格。该结果不能声称 hierarchy不必要。

Null — controls通过、direct失败
停止当前 process-skill/hierarchy carrier路线。B/C保持未识别但不再值得在另一 toy 上执行；D也不能被宣称成功。后续只能重新审查 observability、ordinary objective或最终 benchmark本身，不能制造第三个 carrier。

Disconfirming — constructive或random calibration失败，或clean channel不满足信息边界
退休该新 carrier，不读取learner结果，不替换阈值或重写任务。

Invalid — state machine、mask、replay、RNG、checkpoint或count失败
仅修具体实现缺陷，保持 carrier、预算、seed、阈值和branch不变。

禁止救援

结果后不得：

改 observation、reward、horizon、model width、optimizer、budget、seed或threshold；

选择 best checkpoint；

加 task shaping、identity、role、contact、progress或success字段；

加 posterior、intrinsic、graph、slot、team latent、communication、scheduler或learned timing；

以 Iteration-5 C1 utility差异作为 carrier pass；

将失败转化为 capacity sweep。

后续可操作的实现边界

未来控制器若单独授权，只应新增：

一个独立命名的 carrier/ledger及其 typed event adapter；

clean process-channel 的只读 schema；

对现有 direct runner的环境工厂接线；

state-machine、mask、replay、checkpoint和control calibration测试。

不得修改现有 C1 objective、process_semantics.py、direct actor architecture或 retired Iteration-5结果。该建议本身不授权这些改动或执行。

4. 可变成员与 lifetime 语义审计

下列项目必须成为该 source 的 M0/诊断读数，不能从旧 architecture contract自动继承为“已证明”。

JOIN

Genuine join必须创建新 opaque lifecycle：

membership_epoch=0；

recurrent hidden为零；

无旧 command/skill状态；

当步进入 active mask；

路由标签或相同物理名称不能恢复旧状态。

必须测量新 member 的 hidden确为零、没有 join前 low row、没有 lifecycle-key network input。现有 event contract已经定义这一语义，但新 carrier仍须独立验证。

Temporary leave

Temporary leave应发生在完成前一 primitive transition之后、从 active set移除之前：

leaver不再产生 primitive actor row；

direct recurrent hidden冻结；

absence期间不计 active execution、不分 inactive reward；

所有 survivor hidden连续且逐值保持其自身演化；

leave本身不是 policy action，也没有 actor ratio。

必须记录 leave前后 hidden、active token数、reward ownership和stale-row rejection。

REJOIN

REJOIN恢复同一 lifecycle状态并增加 epoch：

恢复 frozen recurrent state；

第一个 rejoin active row不能继承 inactive-time transition；

actor只通过普通 observation或公开 rejoin flag获知边界；

不能把 absence当作连续 recurrent update。

必须测量恢复 hidden与leave时快照完全一致，以及旧 epoch row不能进入新 replay。

Terminal leave

Terminal leave关闭并最终化当前row后删除 recurrent state；未来同物理标签必须创建新 lifecycle。不能有terminal后actor token或非零bootstrap。

Masks、顺序与 survivor continuity

只聚合当前 ACTIVE tokens；

active token count必须等于真实 active count；

presentation和primitive autoregressive order由policy-independent RNG生成并完整记录；

routing key/epoch只做定位和stale-row拒绝；

permutation replay必须得到相同 joint probability；

不得用dummy slot伪造成员。

现有事件合同规定外部顺序是均匀、记录且重放时不得重采样；E1应对primitive direct order执行同等检查。

Physical time、event time与credit

E1 direct learner只有 physical-time primitive decisions：

reward/GAE沿每个真实环境步；

membership event没有actor likelihood；

不存在high KEEP/SET、opportunity action、survival likelihood或owner-event GAE。

因此E1 不验证 variable skill lifetime。它只验证一个具有membership churn和异质时间负载的access基座。未来B/C若进入hierarchical比较，才必须恢复：

R
i,n
	​

=
r=0
∑
Δ
i,n
	​

−1
	​

γ
r
r
env
	​

(t
i,n
	​

+r),γ
Δ
i,n
	​

V(C
t
i,n+1
	​

	​

)

并让 lambda 只沿同一 owner 的真实policy events推进；silent steps、其他成员事件和membership事件不得制造actor ratio。

Process channel与segment ownership

E1中的clean process channel是read-only证据字段：

按 focal lifecycle和active primitive step记录；

temporary leave后不推进；

rejoin后开启新的可审计片段；

不跨membership epoch或policy version；

不进入direct policy、critic或reward。

E1不训练posterior，也没有semantic credit window。其作用只是证明后续若选择B/C，carrier已经提供不依赖task bookkeeping的真实action consequence。

Probability与RNG

Direct joint behavior probability仅由当前active成员的primitive autoregressive factors组成。外部membership ledger和recorded presentation/order是policy-independent常数；采样和replay必须使用相同active set、order、action prefix和hidden。Task ledger、presentation/order RNG、policy-action RNG和evaluation RNG应相互独立并进入checkpoint。当前direct policy确实依赖active-set summary和earlier-action counts，因此这些source tensors必须原样保存，不能从后来的roster重建。

Checkpoint/replay

Strict checkpoint至少保存：

actor、critic、optimizer和normalizer；

每lifecycle recurrent hidden和membership epoch；

environment/membership snapshot；

active presentation与尚未消费的ledger ID；

order/action/environment RNG；

current observation/state boundary。

缺失live state必须hard fail，不能reset-and-continue。原event contract的fail-closed原则仍是最低边界。

Decentralized execution

不能假设C3已经满足最终decentralized execution。其actor显式读取active-set aggregate和当前primitive frontier的earlier-action prefix。E1应把它标记为access instrument，并记录其信息范围。未来D与hierarchy的load-bearing比较必须另行满足以下之一：

所有direct inputs在部署时通过允许的公共通信可获得；或

direct comparator被限制到与hierarchical low actor相同的local information；或

两者都获得相同、明确计费的team communication。

否则“direct胜过hierarchy”会混杂 centralized execution advantage。

5. 文献原则与不兼容项

ACAC提供时间语义，而不是完整架构。 可吸收的是 gamma按真实physical elapsed time、lambda按宏事件深度推进，以及每成员有效event history；其fixed-n_agent runner、critic shell和experience结构不支持episode内roster churn。该原则已经与现有owner-event contract一致，无需在E1加入ACAC模块。

ACE提供per-member readiness和dropout压力，但不提供正确的duration return或open roster。 它的buffer仍由固定num_agents分配，return没有gamma^{T_i}；可保留为survivor/dropout诊断来源，不能复制其collector或把mask解释为JOIN/REJOIN。

InforMARL说明共享、permutation-safe、稀疏表示可跨固定N复用，但没有within-episode membership语义。 其GNN或pooling只有在E1测得当前sum/count表示的信息或scaling缺陷后才可能作为替换；不能先添加graph。纯mean pooling还会丢失绝对人数和rare-critical member。

ExpoComm只提供bounded sparse candidate topology原则。 固定循环ID、同步全局轮换和旧邻居message memory与roster churn不兼容；其重构/对比辅助目标也不能顺带加入技能门。

Sable是固定大N的吞吐/显存对照，不是dynamic roster方案。 固定T×N序列会使成员删除改变token phase和hidden ownership；它不应进入当前第一因果边。

Safe-M3-UCRL的mean field和IARO的同步joint option都与目标存在结构冲突。 前者抹去absolute mass和关键个体，后者要求全员投票、共同执行和共同终止；可借鉴population mass或relative spread作为无奖励诊断，但不能导入完整model-based optimizer、eigenvector reward或同步option系统。

CT-MARL进一步支持duration必须进入value semantics，但不支持PINN/HJB/VGI整栈。 其所有成员共享同一Δt、joint state和固定N，与per-agent异步事件不同。

收敛原则是：

active lifecycle ownership
+ exact physical/event time semantics
+ task-neutral local process evidence
+ mandatory direct recurrent null

而不是：

graph + retention + communication + mean field
+ team latent + option discovery + continuous-time model

现有综述也确认，没有一篇列出的工作同时实现episode内JOIN/LEAVE/REJOIN、survivor continuity和正确on-policy roster semantics。

6. Portfolio停止、合并与集成条件
候选处置

A — access/substrate

E1通过：A被解析并退出算法组合；它只说明Iteration-5 carrier不合格。

E1 controls通过但direct失败：停止继续搜索carrier；B/C暂停，不能再建下一toy。

A不能通过增大模型、预算或调整threshold“通过”。

B — factorized discrete executor

退休条件：

adapters有非零gradient和drift但没有material process separation；

分离仅存在于logits/参数，不进入环境后果；

nuisance或join/rejoin strata中反向；

未来语义通过但相对matched direct没有transfer、utility或sample-efficiency价值。

C — simplex command

长期坍缩到simplex顶点并与B等价：并入B；

中间command无可预测插值或held-out gain：退休；

不得通过增加basis数量、temperature sweep或新posterior保留C。

D — direct recurrence

D只能由以下联合证据显著削弱：

同-carrier direct access已通过；

hierarchy具有material、persistent、natural、nuisance-resistant semantics；

actor-visible information、critic、参数/optimizer exposure和checkpoint选择匹配；

hierarchy在未见membership schedule或lifetime distribution上取得material external-utility或sample-efficiency优势；

该优势仍满足decentralized execution要求。

Posterior accuracy、label occupancy、forced effect或训练内utility差异都不能退休D。

Whole-line stop

整个显式process-skill/hierarchy路线在以下任一条件成立时停止：

推荐的最后一次E1仍不能建立普通direct access；

access通过，但B/C都不能产生稳定、可执行、跨event strata的process commands；

B/C产生语义，但matched direct在held-out membership/lifetime上noninferior；

唯一成功方案需要task field、identity、role、learned scheduler、duration catalogue或已退休effect objective；

只有同时叠加team latent、graph、communication、new critic、hazard和semantic reward才工作，因果归因已经失效。

未来集成阈值

任何hierarchical候选进入独立integration review前，至少必须同时满足：

同一carrier上的普通direct access先通过；

JOIN、temporary leave、REJOIN、terminal leave、survivor continuity逐项实测通过；

exact probability、mask、RNG、credit、replay和checkpoint有效；

semantic segment所有权唯一且不跨policy version；

same-snapshot action control、持续process consequence、nuisance stability和natural overlap均达到预注册material门；

不读取task reward、progress、role、identity或contact shortcut；

与信息、容量、环境暴露和optimizer exposure匹配的direct policy相比，在未见membership/lifetime条件上有material外部优势；

结果来自一个明确替换，而非多个新模块同时启用；

robustness使用事前登记的种子集合，不在有效失败后追加种子。

最终建议：保留A/D/B/C四候选；唯一下一证据源为一次性的clean-process-channel dynamic-roster direct-access qualification。 这是一项审阅建议，不授权代码、训练、算力、另一自动迭代或后续E2/E3；实际注册、实施和科学处置仍由控制器承担。
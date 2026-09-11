# 选择一次真实的 actor100 对照训练，而不是再做资格诊断

**唯一下一对象选择：RCLE-TBCFV-B03-ACTOR100，类别 B/EXPLORE。** 在相同 FLEX 包、相同可用信息、相同初始化和新配对训练种子 19 上，比较 claim-score 固定权重 100 与原权重 1；两臂每次非零全向量更新范数均为 0.02，每臂训练 200×64 episode，只比较 update-200 的最终原生服务结果。选择它的理由是：A02 已把“再增加整体运动量”的动机收窄为一个可以干预的学习法则问题，而这次比较直接观察该干预是否减少成员变化后的未服务需求，不再用梯度、概率运动或一个新的 A 代替回报。

**最窄主张是一个新训练种子上的法则效果信号或反例：在这个固定宿主、FLEX 模型和曝光下，W100 相对新训练的 W1 是否降低两条 ACTIVE_CONTINUATION held-out 路径的平均 U。** 不是证明低 actor 占比是 B02 失败的原因，不是修复成功的预告，也不估计 C1P1/FLEX 包差异。两次真实训练、一个共享初始化面板和一个同面板脚本参考已足够回答这个问题；不选择零基线第三臂、四臂析因、进一步冻结探查、系数搜索或延长阶梯。此处选择对象及其必要卡片内容，不代替 DM 写卡、CM 实现验证或 Root 集成，也不启动实验。[提案：Recommended object、Alternatives compared][proposal]；[经验规范 §§5.2、11.4、11.8–11.9][spec]

## 一、先保留已经知道的事实，而不是把动机写成疗效

### A02 的全部块读法与相反证据

A02 是 seed18 保存状态上的完整 A/RECON：四个逻辑配置×两个探查块，512 个结果 episode、32,768 tick、32 次完成求导，零 optimizer step、零 baseline update。两个探查块不是两个训练种子，四个配置也不是四次独立训练。全部八张原基线图的 r_A、r_P 如下；所有行都同时低于 0.01，也都满足较弱的 manager-dominant 描述 r_A<0.5。[A02 intake §§1–3][intake]；[E0：Complete exposure and identity、Primary observations][evidence]；[完整主表：Original-baseline score allocation][tables]

| 配置 | 块 | r_A | r_P |
| --- | ---: | ---: | ---: |
| C1P1-init | 19001 | 0.00934238849 | 0.00941476692 |
| C1P1-init | 19002 | 0.00755212707 | 0.00756448282 |
| FLEX-init | 19001 | 0.00934447557 | 0.00941476673 |
| FLEX-init | 19002 | 0.00755675076 | 0.00756448255 |
| C1P1-final | 19001 | 0.00758724535 | 0.00760733249 |
| C1P1-final | 19002 | 0.00671868818 | 0.00673617113 |
| FLEX-final | 19001 | 0.00760950255 | 0.00761280071 |
| FLEX-final | 19002 | 0.00641083238 | 0.00641687601 |

这不是“actor 没有作用”。manager 与 actor 两个聚合梯度的余弦约为 −0.0094 至 −0.0004，相消比约 0.9907–0.9936；因此不能把这些样本中的低占比解释成两项之间的大幅反向抵消。样本内部抵消、跨 agent 冲突、梯度噪声及其训练期变化没有被识别。两个 loss 通路都可到达共享 encoder；FLEX 的最终事件头有非零 actor 梯度，已连接的隐藏头梯度可以数值为零。初始前向策略相同不等于反向图相同。[intake §3；tables：All five gradient-group projections][intake]

零基线反事实也必须保留全部四行，不能只引用第一块的正余弦：

| 最终状态 | 块 | 原／零联合范数 | cos(原,零) | 零基线 r_A | 零基线 r_P |
| --- | ---: | ---: | ---: | ---: | ---: |
| C1P1 | 19001 | 0.0988989568 | 0.811611093 | 0.00716168128 | 0.00719182815 |
| C1P1 | 19002 | 0.0453089754 | −0.189325433 | 0.00544843096 | 0.00544132722 |
| FLEX | 19001 | 0.0989116764 | 0.811568586 | 0.00729228793 | 0.00731180205 |
| FLEX | 19002 | 0.0463483646 | −0.244324980 | 0.00539244596 | 0.00537463535 |

去基线扩大原始范数约 10–22 倍并改变方向，但 actor/pointer 占比仍低于 1%，有些更低。这是去基线“已修复分配”的直接反例，却不是去基线训练一定无效的反例。每格常数居中保留了观察到的回报标准差；64 条原始 Y 均值／SD 与 advantage 均值／RMS／SD 记录整体保留，不能以 advantage 均值接近零声称奖励信息被消灭。原基线比较均附带同一精度限制：最终 buffer 由各自 200 条有序全精度曲线重建，`math.fsum/len` 与原 `torch.mean` 的 FP64 reduction 次序不同，不是缺失 buffer 的逐位恢复；没有把零基线替代值标成原值。[intake §§1、3；tables：Same-graph zero-baseline comparison、All per-cell return and advantage statistics][intake]；[E0：Complete exposure and identity][evidence]

固定输入的两块结果如下。每块都保留全部八格、三份熵、均值与最大值；此汇总不替代源表。[完整主表：All fixed-input probability statistics][tables]

| 块 | C1P1 final/init 平均 TV／最大 TV | FLEX final/init 平均 TV／最大 TV | FLEX/C1P1 final 平均 TV／最大 TV |
| --- | --- | --- | --- |
| 19001 | 0.00535123840／0.0103800609 | 0.00534134180／0.0103474469 | 0.0000172250／0.0000348292 |
| 19002 | 0.00544612839／0.0106404335 | 0.00543670243／0.0106135669 | 0.0000164805／0.0000363949 |

16 个 cell/block 行中，两最终状态相对初始化的格均值均低于 0.01，但若干点最大值超过 0.01；不能把平均小写成每点不变。原 64 条回报／advantage 行的差异也不丢弃：例如块 19002 的 6→10 ACTIVE_CONTINUATION，C1P1-final 的 Y 均值为 0.291992187，FLEX-final 为 0.291145833。这是冻结策略测量，不是新训练收益。直接参数位移为 C1P1 final/init 0.472889394、FLEX final/init 0.472943899；直接 final/final 距离为 0.00234143919，不是前两范数相减。pointer 位移约 0.0157，FLEX common/agent 头位移分别约 0.000279551／0.000327731，均非零。输入库固定外部输入和 C1P1-init latent，并逐状态重编码，因而不测最终策略的 latent 改变或访问分布。[tables：Direct parameter displacements、两组 All… 表][tables]；[intake §3][intake]

**预测记分不改。** 上一节点的 manager-dominant／小平均条件变化预测得到支持；它原先没有预测必过更强的 1% 标记。DM 的 actor 占比 0.1–0.5 和至少一块平均 TV>0.01 两项预测均失败，点最大值不能挽救块均值预测。A02 的完成是本次 A 支出的结束，不是方向暂停，更不是后续 B 的资格门槛。[intake §§2、4、6][intake]；[前次答复 §§四–五、七][previous]

### B02 的原生反例和 headroom 限制

B02 仍是其原卡法则下 seed18 单配对的近乎平坦服务结果。所列前次答复保留的两条 ACTIVE_CONTINUATION 数据为：

| 路径 | 初始化 U | C1P1 最终 U | FLEX 最终 U | 最近信标参考 U |
| --- | ---: | ---: | ---: | ---: |
| 8→12 | 0.696696 | 0.695286 | 0.695319 | 0.245646 |
| 12→8 | 0.721233 | 0.718720 | 0.718683 | 0.318652 |

两学习臂的 G_U 均约 +0.00196，原包差约 −0.00000191，初始化与最终学习面板的 τ 全为 40。原先期待约 0.05 学习改善的预测没有发生；不能因 A02 有非零梯度就改记为成功。历史参考 U 约 0.282、学习臂约 0.707、差约 0.425，只说明一个已实现脚本行为提供了可见的改善空间，不是最优上参考减去已调优通用基线的 H_A1；H_A1 仍未识别。新 B 不需要补齐它。[前次答复 §§一、七][previous]；[intake §§3、5][intake]；[经验规范 §11.7][spec]

## 二、为何选 actor100，而不是零基线或四臂

**这是有依据但不被证据保证的优先次序。** actor100 直接改变当前两个已观察样本中很弱的 claim-score 项相对权重，且保持总步长不变；其收益若出现，将是一个具体可复用的学习法则结果。零基线以同样的两实例预算研究另一件事：有限样本中心化和归一化方向是否影响回报。它有真正理由，因为第二块方向甚至反转；不能仅因低占比没有消失就排除其疗效。现在选择 actor100，是把有限支出集中在更直接的相对 score 权重干预上，不是在两个尚未训练的新法则之间宣称已证明优劣。[proposal：Recommended object、Alternatives compared][proposal]；[intake §3][intake]

**最强反对意见**是范数依赖参数化，小 actor 范数未必意味着有效控制信用不足。许多 claim 的分别平均可能给出小而有用的梯度；扩大 100 倍可能放大噪声，挤走有用的 manager 方向，并经共享 encoder 与事件头改变后续访问分布。A02 只看两个冻结块，既不代表全部 200 次更新，也不能预测新 seed 的梯度几何。即使 W100 的 pointer 变化更大，原生 U 仍可能不变或恶化。新比较的价值正是让这个反对意见在真实训练的最终 U 上受到检验，而不是再测一轮梯度去排除它。

令相同数据、参数、baseline 上的两项梯度为 g_M、g_A，则该改动在这一张图上给出 g_λ=g_M+λg_A。固定范数以后，作用对象是 `(g_M+λg_A)/‖g_M+λg_A‖` 的方向，而非原始范数本身。若两项恰好正向共线，单纯放大一项甚至可以不改变归一化方向；若方向有噪声，也可能变坏。这是对法则的代数说明，不是额外 A02 运算、未来分配测量或疗效定理。100 是公开结果知情的数量级启发，不是 1% 的精确倒数校准、最优系数、逐参数学习率或无偏策略梯度修正。保留各自 episode 内均值也意味着不能把它说成恢复了某个一般的 sum-score 定理。[models.py：averaged_episode_score、exact_advantage_loss，L316–363][models]；[B02 study.py：fixed_norm_sgd_step、apply_b02_block_update，L125–184][study]

**零基线备选的具体含义**是 λ=1、b 始终为零，对照为相同 FLEX、λ=1、原 0.95/0.05 基线，完整步长仍为 0.02，其余 seed／曝光／面板保持配对。它仍是独立候选，不是本轮第三臂；本轮 W100 对 W1 不能判断“零基线是否更好”。本轮若失败，零基线方向问题可以重新比较决策价值，但没有自动后继授权。[proposal：Alternatives compared；cost：alternatives.zero_baseline_pair][proposal]

包×权重四臂回答学习法则与包的交互，当前问题不需要它。把 FLEX 固定不会剥夺包比较独立成为普通 B 的资格，也不要求先证明 FLEX 有能力。省去四臂即放弃包效应与交互归因；省去新 A、全更新分解即放弃全训练期分配／完整机制归因；省去搜索和调优即放弃最优权重与调优基线胜利主张。这些放弃不损害同信息、同包、同曝光的法则比较。[proposal；经验规范 §§11.8–11.9][proposal]；[spec][spec]

沿用 A02 intake §3 已核实的文献边界，不新建文献门槛：其 HyperMARL 本地原文核对讨论跨 agent 梯度分解／冲突，不是这里 manager/actor 的 loss 分解；其 Greensmith–Bartlett–Baxter 控制变量依据说明平均回报基线未必最小化方差，不证明 RCLE 的 `g/‖g‖` 更新期望或零基线疗效。本咨询仅复用该已核实记录，没有重新访问其本地 PDF 或外部网页；actor100 无新颖性或文献支持的最优性主张。[intake §3：Literature grounding that changes this reading][intake]

## 三、可直接写入新卡的学习比较

### 同包、同信息和真实法则

两臂都是同一 26,161 标量的最大 FLEX 结构，两个事件头照原语义可训练；没有 C1P1 臂。W1/W100 是报告标签，不是新包。沿用原 Xavier／零 bias 初始化，两最终事件头层起点为零；两个训练实例复制同一次初始化，不加载 seed18 最终参数，不热启动。宿主保持 120 扇区、6 信标、H=64、tick24 成员／epoch 事件、每 4 tick 的 claim 时钟、六个合法 claim 和原 MOVE-TO-CLAIM decoder。保持观测、通信、公共／个体／候选信息、join/leave/rejoin、entity ownership、计划生命周期、事件与动作时序；不增加特权信息或 N 专属头。[B02 卡 §§2–4][card]；[models.py：manager、event_plan][models]

对每个完整平衡 block 的 64 个 episode，定义 s_M,e 为实际使用 manager log-density 的均值，s_A,e 为实际使用 claim log-probability 的均值；不取消原平均、不按 roster 另加权。以更新前各臂自己的格基线计算：

`L_λ = −(1/64) Σ_e stop(Y_e − b_c(e)) · (s_M,e + λ s_A,e)`，其中 W1 的 λ=1，W100 的 λ=100。

`g_λ = ∇_θ L_λ`；若 g_λ 非零，`θ ← θ − 0.02 g_λ / ‖g_λ‖₂`，否则参数不更新。

每 block 只做一次联合 backward、一次全向量 step 调用。随后才更新八个格基线：`b_c ← 0.95 b_c + 0.05 mean_{e:c(e)=c} Y_e`，初值全零、两臂独立。即使某次 g=0，仍按原顺序更新基线；非零参数步数与 step 调用次数分开记录。返回值、baseline、随机抽样和 old-epoch 样本保持原 stop-gradient；FLEX 当期确定性事件头到 claim score 的导数路径必须保留，不能误将整个事件头输出 detach。训练回报保持 `Y=1−(1/64)Σ_{t=0}^{63}u_t`，不换成只计后 40 tick 的优化目标。没有熵项、Adam、momentum、辅助奖励、return normalization、分组 optimizer、梯度裁剪、adaptive balancing 或额外反传。[models.py：averaged_episode_score、exact_advantage_loss][models]；[study.py：apply_b02_block_update、execute_b02_training_update][study]；[card §§2、4][card]

源码已显示，现有 exact_advantage_loss 把两项直接相加，B02 的实际训练调用它；只在配置／报告里写 λ=100 不会改变训练。新对象必须把固定权重送进真实 loss，并让 λ=1 落回原法则；不要覆盖历史 B02 或定义卡的函数／结果。报告标签、共享 init 的 FLEX 语义及主量正负号，也不能照搬旧 C1P1/FLEX 包比较的硬编码。[models L316–363；study L187–252、initialization_panel、publish_b02_primary][models]；[study][study]

### 种子、RNG 和面板

只用一个新配对训练种子 19，root key 为 ASCII `RCLE-TBCFV-B03-ACTOR100/seed/19` 的 SHA256；所列机器记录给出 `4b17629c25d71afceed93bbe657c0b5799d468d1f5673d90a7ceee644ec474c5`。沿用既有派生函数，identity 用这个新对象、block index=0，不借用 B02 的 identity 或 seed18 block digest。[cost：seed_key_ascii、seed_root_sha256；proposal：RNG 段][cost]

初始化、外生成员和物理情景，以及原语义允许配对的 plan／actor 抽样都按现有坐标配对。两臂传入随机地址的真实包值均为 FLEX；W1/W100、λ 和执行先后次序不进入语义随机地址。两臂仍分别真实采样，策略分歧后不强迫相同 action、visit 或后续回报；这是同一随机驱动下的法则比较，不是强制轨迹相同。训练／评估用途域分离，情景由新 root、block、cell、index 确定，不能用最终结果换 seed、情景或随机域。[proposal；B02 卡 §3][proposal]；[card][card]

训练八格是 `6→6、10→10、6→10、10→6` × `ACTIVE_CONTINUATION、NEW_EPOCH`，每次更新每格 8 episode；每臂 200 次更新。held-out 八格是 `8→8、12→12、8→12、12→8` × 两种条件，每格固定 256 episode。只评估 update200 的两个最终参数；另外在同一新面板执行一次共享 update0 FLEX 评估和一次未改动 INDEPENDENT-NEAREST 参考。参考为每个 agent 取当前最近信标、平局取小索引，无 latent、无训练、无规则调优；脚本不具备的 Y 保持 null 并说明，不能填成学习器回报。[proposal；card §§3–4][proposal]；[card][card]

全部 200 个训练 block 的每格原生曲线、零／非零更新计数、已有 raw/applied norm、最终状态和全部八格端点保留。原有曲线可每 25 次显示，不新增中途评估／checkpoint 选择。初始化评估不能决定是否继续训练，参考不能决定是否“获准”做包比较。B02 的旧回报仅作背景，不能代替新 W1 控制臂。

### 主量、伴随量和采样不确定性

保留 `U=(1/40)Σ_{t=24}^{63}u_t`。主量固定为：

`Δ_U = 1/2 · [mean_{256}(U_W1−U_W100)_{8→12,ACTIVE_CONTINUATION} + mean_{256}(U_W1−U_W100)_{12→8,ACTIVE_CONTINUATION}]`。

**正号利于 W100。** 两路径等权，每路径全部 256 情景等权；先按 cell/index 形成真实配对差，公布两臂水平、每路径差和总差，不以方便的八格均值替换主量。以全部指定情景为分母，不删除失败、agent、时间区间或不利 cell。伴随量为同两路径上各臂 `G_U=U_init−U_final`、`40U`、τ、τ=40 比例，并公布全部八格 U／τ／Y／F 及已声明的八格次要均值。NEW_EPOCH 不是纯粹“抹去身份”的单因素消融。[proposal：Primary；card §4][proposal]；[card][card]

τ 保持原定义：从 tick24+h 起连续四个零未服务 tick 的首次 h∈0..36，否则记 40；这是带失败码的有界得分，不是未删失恢复时间均值。即使 U 改善而 τ 仍全为 40，也只可说累计未服务需求改善，不能说恢复更快。`40U` 是累计归一化未服务需求，不是原始服务件数或总 agent-tick。[card §4][card]

**MEI 采用绝对 U=0.05**，同时用于描述 Δ_U 和 G_U：40 tick 窗口中对应两个归一化未服务 tick；这个物理尺度比任意百分比更可解释，也明显区分于 B02 约 0.002 的微小 G_U，但不是用新结果优化出来的阈值。τ 的 4 tick 尺度只描述一个 claim period 的反向权衡，不要求 τ 离开 40，不另设非劣门槛。MEI 不是功效保证、显著性边界、B 成败审批线或所有路径必须同号的规定。[card §5；proposal：Primary；经验规范 §11.7][card]；[spec][spec]

最小统计观察用现有 NumPy 在已保留的配对情景 U 差上求均值和样本标准误即可，无新环境调用或 bootstrap 实验。每路径报告 `SE=s(d)/sqrt(256)`；在原 cell 分域确实独立的抽样语义下，等权主量的 SE 为 `sqrt(SE_1²+SE_2²)/2`。若实现复用了同一实际外生抽样单元，则保留其协方差／按该单元成组，而不能把共享数据当独立；同名 index 本身也不证明跨路径配对。可附近似 95% 描述区间，明确其仅为固定这一次训练结果的情景 Monte Carlo 不确定性。一个配对训练种子不能估计训练种子总体方差；tick、agent、cell、两个最终 checkpoint 和 256 个 episode 均不能充当独立训练重复。[card §4；经验规范 §§5.2、11.8.3][card]；[spec][spec]

## 四、前瞻预测、可检验反例与所有结果读法

**我的低置信度工作预测为 `0<Δ_U<0.05`，τ=40 仍会很普遍。** 我保留与 DM 同方向但低于 MEI 的预测：改变相对 score 方向可能产生小改善，但两个样本的范数比例和固定输入敏感性不足以支持大幅原生收益预报。最强竞争预测是 `Δ_U≤0`：放大的 actor 噪声或被挤走的 manager／encoder 信用，使回报不变或更差。没有新训练结果用于这些预测，也不虚构 owner 预测。[DM 原预测：proposal 的结果段][proposal]

有效完成后的 Δ_U≤0 是工作预测的反例；Δ_U≥0.05 支持正方向，却推翻“小于 MEI”的大小预测。若抽样误差跨越这些尺度，保留点估计和不确定性，不将一个符号机械写成总体结论。A02 的低占比即便依然成立，也不能挽救一个不利的原生回报比较。

| 完整观察 | 本轮读法与可能的下一建议 | 明确不能推出 |
| --- | --- | --- |
| Δ_U≥0.05，未见同量级反向原生权衡 | 该 seed／预算上的 W100 累计服务正信号，优先考虑另行选择一个新独立配对复核 | 稳定优越、最优权重、包效应或低占比已被因果定位 |
| 0<Δ_U<0.05 | 局部小改善，工作预测相符；按两路径、G_U 和成本判断是否值得一个有名后续比较 | 等价、实质优越或自动续算 |
| Δ_U=0 或带内负值 | 没有支持 W100 正方向；精确保留零／反向数值，采样误差大时为未决 | 普遍无效、零基线更好或方向应关闭 |
| Δ_U≤−0.05，或明显不利服务／恢复权衡 | 此固定权重在本次预算上的有价值反例；也可因反例值得复核而另选一个独立配对 | 只能正结果才准继续；换 seed 直到结果为正 |
| |Δ_U|<0.05，而至少一臂 G_U≥0.05 | 出现了原生学习，但没有同量级法则优势；记录究竟是哪一臂 | actor100 修复成立或胜过调优通用基线 |
| |Δ_U|<0.05、两臂 G_U 很小、τ 饱和 | 本次 200-update 法则比较没有提供有用收益；结束这笔支出，把完整反例交还下一对象选择 | 再加一轮 A 才能训练；自动延长、扫系数或热启动 |
| 主量有利但 G_U≤0 | 可能只是 W100 比 W1 退步更少；相对效果和绝对退步同时报告 | 从初始化学得更好；G_U 为正是后续 B 的通用门槛 |
| 两路径相反、U 与 τ 相反或 Monte Carlo 区间跨越兴趣尺度 | 混合／未决；保留所有路径与伴随指标，不用有利 cell 替换主量 | 无条件总体优势、非劣或纯恢复加速 |
| 主量依赖的训练、信息或读出损坏 | 报告实际异常、退出、缺量与完成计数；保留不依赖该故障的窄事实 | 给算法判正负、把部分执行记完整或自动补臂／换 seed |

这些行是重叠的描述性读法，不是新的 C 冻结检验或审批表。所谓“反向权衡”具体报告两路径各自 U 差、τ 差和饱和比例，按 U=0.05／τ=4 的既有尺度说明；不临时引入第三指标挑赢家，不要求每格同号。梯度或概率变大而 U 不变不算性能成功。零结果与可信反例也可支持一个另行选择的、理由具体的 B；没有结果自动打开后继。[经验规范 §§11.7、11.8.2–11.8.4][spec]

## 五、完整曝光、成本与停止边界

### 主导工作与没有购买的维度

复杂度首先是两臂×一个训练种子×200 个更新×64 episode，随后四个 2,048-episode 面板。算法内在工作包括原生环境推进、每个合法 claim 时钟对六候选评分、block 图保留、一次联合反传和全向量更新；不存在 `6^N` 联合动作枚举、`b^H` 轨迹树、beam／best-of-many 策略搜索、反复 solver/controller 搜索或系数网格。六路 action selection 不是“先搜索再允许学习”的前置对象。[proposal：Work…；card §6；study：execute_b02_training_update][proposal]；[study][study]

以下采用所列 EXPOSURE_AND_COST.json 的机器算术，不是本咨询执行结果：

| 工作 | Episode | 环境 tick | 学习调用 |
| --- | ---: | ---: | --- |
| 两臂训练 | 25,600 | 1,638,400 | 400 次 backward／联合 step 调用 |
| 两个最终八格面板 | 4,096 | 262,144 | 无训练 |
| 一个共享初始化 FLEX 面板 | 2,048 | 131,072 | 无训练 |
| 一个同面板脚本参考 | 2,048 | 131,072 | 无训练 |
| 合计 | 33,792 | 2,162,688 | 两个真实训练实例、一个配对种子 |

400 是计划调用数，不保证 400 次非零参数更新；实际非零／零步、完成 block 和未完成工作如实列出。每臂参数路径长度最多 200×0.02=4，不是净位移或能力保证。初始化尺度的现有参考约 21.2，新 seed19 的实际初始范数在已计费调用中记录；路径预算约为该历史尺度的 0.19 倍只是曝光说明，不是验收目标。现有初始化 helper 若分配未训练模型，分配数量另报，不能把它们算训练臂，也不能将其开销隐去。[cost：training/evaluation/count 字段][cost]；[card §3；study：b02_allocations、run_arm][card]；[study][study]

零基线配对也是 25,600 训练 episode、400 次反传、33,792 总 episode，成本阶相同。四臂包×权重析因变为 51,200 训练 episode、800 次反传、四个最终面板，加共享 init／参考后为 63,488 episode；不是为当前问题所必需。以后一个额外独立配对另增 33,792 episode／400 次反传；两个另增 67,584／800，均须另行选择和计费，不属于本轮。此处的倍数是工作计数，不假装等于运行时倍数。[cost：alternatives；proposal：Work…][cost]

新增验证仅是一项针对真实 weighted loss、λ=1 原法则极限和主量输出的聚焦检查，配合必要独立 review；可在同一检查中覆盖 stop-gradient／先 step 后 baseline、FLEX 语义标签和 Δ_U 符号等实际变更风险。技术 fixture 的模型／导数等曝光由 CM 分列实报，不能塞进 33,792 的科学分母，也不能预填为零；其实际执行成本仍在完整对象上限内。这里不增加结果性探查面板、A02 全分解、全历史 replay、全量支持检查或新 framework。[proposal：Added validation；cost：added_validation][proposal]；[经验规范 §11.8.6][spec]

### 支出上限不是实测报价

机器记录中的 B02 完整学习调用为 71.47 s 和 71.23 s，脚本参考 2.62 s，完整链 152.622 s。第一条历史学习调用是包含共享 init 的 C1P1，第二条 FLEX 不含 init；只能作为计数匹配的约 72 s/学习调用规划参考，不能从二者差求一个面板耗时，也不能把它们当 actor100 实测。前次答复中参考约 1.5 s 的粗略表述不覆盖本轮所列 machine record 的 2.62 s。新法则、必要准备／编译／聚焦检查和出版开销仍未知；不发明加速比，也不要求另做校准实验。[cost：planning_reference][cost]

采用**新鲜完整上限：每个完整学习调用最多 600 s，整个对象累计执行墙时最多 1,500 s**。每臂上限含其必要启动／构建、初始化、全部训练、最终评估和出版；共享 init 只计一次并放在 W1 完整调用中。全对象再包含实际必要准备、聚焦检查、参考、共享结果合并和出版，每项只计一次。不能让子脚本分别填满上限，再把初始化或尾部出版追加出去；同时报告 study elapsed critical path 与逻辑调用墙时之和。未测成本不能当零；若已有具体事实表明完整设计越限，应重审问题和必要工作，不先启动再找继承余额。A02、B02 的旧剩余额度和历史 runtime 阈值均不转入本轮。[proposal：Work, cost…；cost：proposed_caps_s][proposal]；[card §6；经验规范 §11.9][card]；[spec][spec]

工程范围为“不新增 §4 所列机械设施”；普通非测试源代码 2,000 行、runner 600 行与必要测试边界保留，30% 编排占比只是 review 提示。CM 按当前 focused handoff 直接完成普通有界工作，不要求额外实现者链、调度器、registry、retry service、全参数遥测或历史检查再演。必要 independent review 针对 loss／RNG／比较边界，不变成新的普遍 Pro 审批。[工程范围规范 §§4–5][engineering]；[AGENTS：Workflow calibration、Focused reading…、§8][agents]

本轮选择的便携执行约束保持 remote-first `wsl_4070`、CPU FP64／单 compute thread、确切 committed-and-pushed 源码和已有 detached supervision；每次实际调用前在同节点测得 physical/effective 可用内存均至少 4 GiB。没有 GPU、精度／节点／线程更换或自动重试授权。**提案末段“全局监测单一 heartbeat 在 adoption ACK 前必须活跃”的旧措辞不纳入新卡**：当前 TASK 明确覆盖它，固定 AGENTS §5 及附录已把技术执行／观察交给当前 CM/Operator 与既有交接，不增加 scheduler、heartbeat 或站立任务。本咨询不修改任何规范，也不读取未列入清单的 ROOT_OPERATIONS 文件来扩展权限。[proposal：Remote-first 段][proposal]；[AGENTS §§1–2、5、7–8及附录 A][agents]；[当前 TASK：Additional caller constraints][task]

### 正常结束、技术停止和依赖保留

正常执行至两个 update200 最终面板及共享 init／参考和出版完成，即结束这次支出。有限但很差的回报、零优势、τ=40、某些零梯度或第一臂表现差，不触发结果驱动的提前停止；不延长到更多更新、替换 seed、改系数或挑 checkpoint。只有真实的时间／资源边界、非有限数值、错误 reward／信息／时序／RNG、断裂学习链或主测量依赖损坏才停止相应工作。技术停止记录实际完成数量与失败位置，不推导算法极性，不获得自动补跑预算。[card §6；经验规范 §§4、11.4、11.8.7][card]；[spec][spec]

若 W1 已损坏到不能构成预定配对，不为凑齐臂而盲花 W100 额度；若第二臂损坏，保留第一臂真实事实。若只缺共享 init，G_U 不可得，但两最终面板、训练曝光和配对完整时，Δ_U 的窄比较仍可报告；若只缺参考，不抹去学习器比较，也不自动重跑参考。计划所需面板缺失仍不是“完整对象”。可选资源数值缺失只降低相应资源断言，不自动抹掉独立可信原生结果；强制准入与上限控制仍保留。所有结局都返回当前节点的科学 intake，不改变 RCLE 的生命周期或下一对象权限。[card §6；AGENTS §8；经验规范 §11.8.7][card]；[agents][agents]；[spec][spec]

## 六、最后的因果边界与实际访问

若未来有效比较有正差，可以把它归于在本次固定随机驱动、模型和预算下实施的**整条 W100 训练法则干预**，但不能分解为“pointer 放大”的纯效果：共享 encoder、FLEX 事件头、manager 相对份额、训练访问和各臂 baseline 序列都会随训练内生变化。没有冻结它们就不做路径归因；冻结它们反而会变成不同算法。参数化、噪声、跨 agent 冲突、长程信用、表达能力或优化曝光谁是主因，本轮都不识别。负差也不证明 actor 信息无用或整个宿主不可学。

一个新配对种子只支持观察设置上的 B 信号／反例；不支持稳定优越、任意 roster 泛化、完整机制因果说明、C1P1/FLEX 包效应、调优通用基线胜利、最优 λ、恢复时间非劣或 C 类结论。后续一至两个独立训练种子只是按信息价值另行选择的重复性观察，不要求全部为正，更不是此次启动前的义务。当前方向继续，已结束的是 A02 支出；此答复只选一个 B，不冻结 C，不变更规范或 Portfolio 生命周期、优先级、容量、融合、注册。[经验规范 §§5.2、11.8–11.9][spec]；[当前 TASK：claim ceiling][task]

本咨询通过连接的 GitHub 读取了固定 TASK，以及清单中的全部 13 个证据路径；科学证据均为 `9ed540ea7a6de32e2f389fd38aaef5fcf0098689`。对模型和训练代码读取上述相关函数，对规范和协作文件读取指定相关节；没有递归追踪它们的未列链接。TASK 来自 `c03c37a6f186a27c2abce3c387aec8a0548325ab`，交付分支 HEAD 只用于交付检查，未替换科学输入版本。没有证据路径访问缺口。[task][task]

Issue #8 正文与全部三个既有评论已实际读到，并与固定 ISSUE_SNAPSHOT.json 对照；本次写入前评论复核观察约为 **2026-09-09 09:39 PDT（America/Los_Angeles，UTC−07:00）**。三个历史评论是 [first-B r02](https://github.com/CartmanFatass/My-paper-code/issues/8#issuecomment-5560789984)、[post-B01](https://github.com/CartmanFatass/My-paper-code/issues/8#issuecomment-5562367990)、[post-B02](https://github.com/CartmanFatass/My-paper-code/issues/8#issuecomment-5564117795)，都不是本轮交付；未沿链接取用清单之外的代码／文件。Issue 中历史“从未执行”文字不能覆盖固定 B02/A02 结果；讨论是可变来源，不是 commit-pinned 科学记录。[Issue #8](https://github.com/CartmanFatass/My-paper-code/issues/8)；[固定快照][snapshot]

没有执行代码、构造模型、加载参数二进制、创建原生状态、运行 episode、求导、更新、测试或实验；这些本咨询曝光全部为零。A02 数值与 B02 背景来自已列文字证据／主表，未宣称独立逐位复现；成本使用已列机器记录，未实测 actor100。上述未来曝光、实际准备成本和实现正确性由后续既有 DM/CM/Root 链承担。本次仓库交付仅为指定答复及其一条链接评论。

[task]: https://github.com/CartmanFatass/My-paper-code/blob/c03c37a6f186a27c2abce3c387aec8a0548325ab/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260909_post_a02_innovator_recovery/TASK.md
[proposal]: https://github.com/CartmanFatass/My-paper-code/blob/9ed540ea7a6de32e2f389fd38aaef5fcf0098689/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_a02_innovator/PROPOSAL.md
[cost]: https://github.com/CartmanFatass/My-paper-code/blob/9ed540ea7a6de32e2f389fd38aaef5fcf0098689/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_a02_innovator/EXPOSURE_AND_COST.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/9ed540ea7a6de32e2f389fd38aaef5fcf0098689/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_a02_innovator/ISSUE_SNAPSHOT.json
[intake]: https://github.com/CartmanFatass/My-paper-code/blob/9ed540ea7a6de32e2f389fd38aaef5fcf0098689/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_A02_RESULT_INTAKE_20260906.md
[evidence]: https://github.com/CartmanFatass/My-paper-code/blob/9ed540ea7a6de32e2f389fd38aaef5fcf0098689/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_A02_RESULT_EVIDENCE_20260906.md
[tables]: https://github.com/CartmanFatass/My-paper-code/blob/9ed540ea7a6de32e2f389fd38aaef5fcf0098689/docs/research/candidates/roster_consistent_latent_exploration/a02_frozen_score_allocation_20260906/PRIMARY_TABLES.md
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/9ed540ea7a6de32e2f389fd38aaef5fcf0098689/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260906_post_b02_innovator/archive/RESPONSE.md
[card]: https://github.com/CartmanFatass/My-paper-code/blob/9ed540ea7a6de32e2f389fd38aaef5fcf0098689/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B02_NORM_0P02_SCIENCE_CARD_20260906.md
[models]: https://github.com/CartmanFatass/My-paper-code/blob/9ed540ea7a6de32e2f389fd38aaef5fcf0098689/experiments/candidates/roster_consistent_latent_exploration_tbcfv/models.py
[study]: https://github.com/CartmanFatass/My-paper-code/blob/9ed540ea7a6de32e2f389fd38aaef5fcf0098689/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b02/study.py
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/9ed540ea7a6de32e2f389fd38aaef5fcf0098689/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/9ed540ea7a6de32e2f389fd38aaef5fcf0098689/docs/project/ENGINEERING_SCOPE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/9ed540ea7a6de32e2f389fd38aaef5fcf0098689/AGENTS.md

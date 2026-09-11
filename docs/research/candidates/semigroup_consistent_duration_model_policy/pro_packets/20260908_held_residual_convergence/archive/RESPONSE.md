**选择一次 SCDMP-NATIVE-HOLD-RESIDUAL-B01：保留完整 MLP、完整 Monte Carlo（MC）锚点和原有时长 actor，只增加真实保持段的双端残差惩罚，与完整 MLP-MC 做一个新的配对训练比较。** 理由不是已经证明保持段具有特殊价值，而是源码已明确给出一个不等于重写 MC 目标、也不等于复制 VSPC1 门控的梯度干预；它可以在不增加环境交互、模型参数或优化器调用的条件下，由最终 sampled 策略的完整原生回报直接裁决。其收益预期不强，但这一对训练足以回答一个有用的局部问题：这个具体损失包是否值得以后再看一个独立训练实例。未知 headroom、稀疏保持支持和不能唯一定位因果机制，都不应替代这个实际性能问题。[^1][^12]

**这次选择是一次新的、实质性的机制 RECAST。** 它不恢复旧 D6 行为空间／源状态／倒计时搜索家族，不改写先前 RECAST_D6，也不把之后的 PARK 算成一次 RECAST。此次从跨 k 的动作价值共享与人口寻找，转向既有原生 actor–critic 路径中的残差-MC 损失耦合；不是仅调整诊断负担。这里明确新增一次机制重定向的分类，但不修改仓库的 recast 计数、优先级、生命周期或 UAV 进入状态，也不据此触发任何自动后继。[^3][^4][^11]

## 为什么值得选，而不是再找人口或先做诊断

本次人口来自已经实际运行过的 UCOPE/VSPC1 五 UAV 原生学习 recipe，不是因为 A01 没有 k=7 正号而重新挑选，也不是因为 A02 的晚状态提前 dock 而移动事件时间。新问题固定原有观察、动作、奖励和训练预算，改变的是已有批次上的 critic 梯度。来源准备已把该变化、实际 actor 作用路径、完整比较器和工作量写成可执行的有限比较；这满足旧 PARK 所要求的“来自旧搜索谱系之外、联系原生动作后果、能改变下一步选择”的重入依据。满足依据并不自动证明值得做；我的判断是在完整 MC 锚点、零新增参数和单对预算的限制下，值得选这一次。[^1][^3][^11]

这里也须纠正旧限制的泛化：先要求出现两个时长各自占优的状态、完整支持、精确上界或唯一保持机制，然后才允许普通 B，并不是本次的科学必要条件。现行证据规范 §11.8–11.9 明确要求同时校准“研究什么”和“需要多少证据”，并明确指出，把不必要的 B 前置条件搬到先行 A 仍不使它合理。因此不再选 A 普查、近邻参数、倒计时、策略搜索或归因比较。旧 A01/A02 的结果及停止含义原样保存，不被这条当前方法约束追溯改写。[^12]

不选后继也有合理理由：它是已知的一般残差正则化，保持相关样本少，完整 MLP 本来就能拟合这些输入，而且近期原生控制结果有明显反证。我的选择并不是“只要非重复就应该跑”，而是这个候选的最小直接比较能区分三种局部行动——考虑一次独立重复、不再重复这个固定惩罚、或偏向完整 MC——而额外找原因并不能先验决定其最终原生回报。[^1][^9][^10]

## 源码真正改变了什么

对一条已经采集完的 episode，记 G_t 为 t 至 255 的完整 MC 回报，R_t:4 为 r_t 至 r_3 的实际奖励和，V_t 为当前 epoch 对已存 pre-action critic 输入的预测。用 e_t=V_t−G_t 表示 MC 拟合误差，则在同一实际奖励路径的代数意义下：

G_t = R_t:4 + G_4，

V_t − R_t:4 − V_4 = e_t − e_4。

因此，把目标写成 R_t:4+G_4 只是原来的 MC 目标；把尾项改成 stopgrad(V_4) 则是多步半梯度 TD。此次选定的项是 (V_t−R_t:4−V_4)^2，并且两个 V 都参与反向传播，其梯度为 2(e_t−e_4)(∇V_t−∇V_4)。这是误差之间的耦合，不是独立 MC 损失的简单重加权。上述是基于来源奖励定义的代数分析，不是执行出来的数值结果，也不是 FP32 逐位相等声明。[^1][^5]

来源 intake §4 已核查的文献把它归入已有 sampled residual-gradient fitting，并记录随机转移下的 double-sampling 限制和梯度抵销问题。本次沿用这个已核查的分类，不宣称发现了新的 semigroup 信息，也不把检索未命中当作新颖性证据。我没有另行访问原论文或本地文献库；这一文献判断的直接来源是列入清单的 intake，而非本次独立完成的文献复核。已知方法的包含关系限制表述，不构成禁止性能探索的门槛。[^1]

保持也不等于联合动作恒定。t0 各 agent 才选择 d1/d4；有 d4 时 t1–3 可以仍在保持，t4 全部恢复 primitive 反馈。其间未保持的 agent 仍可能重新抽动作，五个 actor GRU 也持续接收观察。critic 只有当前全局状态及已有命令／remaining-hold 信息，不读取 actor 隐藏历史，也不读取刚选择的动作或时长。因此不假设该输入是充分 Markov 状态，不宣称段内是确定性联合转移，更不能把一个实际后继的双端残差梯度说成平方“期望 Bellman 残差”的无偏梯度。此次优化的就是已采样批次上的损失，不增加第二后继、模型转移或额外回放。[^2][^5][^6]

完整作用路径是：真实保持运动及服务 → 实际团队奖励、pre-action 状态和承诺记录 → 新增 critic 双端梯度 → 原有 actor/critic 联合梯度裁剪，以及下一 rollout 的 baseline → 原有归一化并 detach 的 advantages 与 compound PPO → 后续局部随机动作 → 完整 native return。新增项没有直接通往 actor 参数的可微路径，但联合 norm clip 会即时改变 actor 更新尺度；之后 baseline 的变化也会影响后续采集到的 advantages。不能把这两条路径误写成“actor 完全不受影响”或“已经证明 baseline 改善是唯一原因”。[^5][^6][^8]

## 支持、最强反证和仍然存在的解释

最强支持不是另一个方向的正号，而是实际源码提供了一个明确的非冗余学习干预及可测量的原生回报路径。MC 锚点仍覆盖全部 row，残差中共同的实际未来尾部在误差差中消去；这可能提供有限预算下有用的正则化。它没有给模型新增信息，也没有证明保持边界本身具有独有价值。[^1][^5]

必须同时保留以下相反证据：

| 来源观察 | 本次必须保留的含义 |
| --- | --- |
| VSPC1 master8101：GATED−MLP = +0.0293656586；GATED−H = +0.0194005494；MLP−H = −0.0099651092 | 这是损失不变、增加 640 参数门控的另一个 n=1 包观察。完整 MLP 低于 H，训练方差未知；其正号不能转移给残差损失。原有六个 GATED−MLP 负 episode、七个 GATED−H 负 episode 仍属于结果。 |
| UCOPE B02 master7001：T−G = −0.0472671044，T−H = −0.0224883084 | 时长能力并未在该已接受实例中带来可用控制改善。 |
| UCOPE B02 master7002：T−G = −0.0061362058，T−H = −0.0243921875；两对 T−G 均值 −0.0267016551 | 更近的两个训练实例均给出不利 T−G，且 T 都低于 H。这比只引用 VSPC1 一个正实例更不利于乐观预期。 |
| SCDMP A01：W=2498、R7=0、R13=1；A02 在 321 个候选 mission 后完整触发人口未建立分支 | 旧人口没有提供原设想的双向动作选择基础。A02 的 K 量未观测，不是零；这些既不救新损失，也不构成新损失已经失败。 |

这些数值分别来自各自的完整 intake／技术接受记录，比较器和干预不同，不合并成残差实验的样本。更早 UCOPE6901/6902 的不利背景也不被删除或与新配对混作重复。[^3][^9][^10]

对本候选最强的实质性反对是：完整非线性 MLP 可能已经足够；只在开头三行约束两个预测的差，可能学不到对最终控制有用的东西，反而把 t4 的估计误差传播给 earlier endpoints。两个端点的梯度可能抵销；随机后继与 critic 看不到的 actor 历史可能造成有害耦合；即使回报提高，也可能只是一般正则化或联合裁剪改变了 actor 更新，而不是保持语义。[^1][^5]

稀疏性尤其不能被误读成“小到没有优化影响”。每条 episode 最多三个团队 pair，每个两-episode rollout 最多六个；但 L_seg 按实际 pair 数取均值，L_MC 按全部 512 row 取均值，再赋予同为 1 的内部权重。故不足 1.2% 的 row 支持并不意味着不足 1.2% 的梯度权重。这个归一化选择可能帮助，也可能让少量边界对主导更新；本次按原候选保留系数 1，不把它包装成无偏暴露校正，也不先调权重。[^1][^2]

## 选定比较保持哪些具体含义

选定的是下面这一项完整原生 B/EXPLORE，而非一种可任意修改的残差研究许可。

| 项目 | 本次选定内容 |
| --- | --- |
| 独立训练单位 | 一个全新配对 master8201；RESIDUAL-MC 与 MLP-MC 两个 learner，H 只作 attained reference，不是第三个 learner。 |
| 模型与信息 | 两边均保留完整 136→128→128→1 critic 和同样的 recurrent duration actor；每个 learner 66,441 参数，无门控、无新增参数／head；观察、动作权限、奖励和 terminal law 不变。 |
| 原生人口 | 原 recipe 的五 UAV、50 uniform 用户、256 primitive 秒及固定 motion/channel/service 配置；不按旧 R7 或 A02 失败选择来源人口。 |
| 采集与优化 | 每臂 512 条完整训练 episode；两条组成 512-row rollout，共 256 rollout；每次四 epoch，共 1,024 次真实 Adam；chunk32、lr3e-4、PPO clip0.2、joint grad clip0.5。 |
| 唯一处理差异 | 原 policy_loss + 0.5×(L_MC + 1.0×L_seg) − 0.01×mean_entropy；MLP-MC 保留原 policy_loss + 0.5×L_MC − 0.01×mean_entropy。 |
| 评价 | 仅最终 sampled 策略，每臂 32 episode；再在相同 32 reset 上评 H。不选 checkpoint，不转 greedy，不评旧权重，不加第三 learner。 |
| 运行边界 | remote_first wsl_4070，CPU FP32、单线程、exact committed accepted source；不是 GPU 加速或设备效果比较。 |

这些是来源 recipe 和唯一候选的选定规格，不是本次已经运行的数量。源码中的 VSPC1 master8101 和旧结果不得覆盖。[^1][^2][^6][^8]

每个实际 rollout 内，pair 集合只由已经存下的 remaining-hold 决定：对每条 episode 的 t∈{1,2,3}，若任一 agent 的 remaining-hold 非零，则加入一个 (t,4) 团队标量 pair。不能按保持 agent 数复制同一团队样本，不能跨 episode 连接，也不能用更新后的 actor 重采时长来重选 pair。R_t:4 只含 r_t…r_3，不含 r_4；V_4 是该 episode 在 t4 原始 primitive 动作前的已存输入所对应预测。[^1][^2][^5]

L_MC 是全部 512 row 的原 MC MSE；L_seg 是实际 pair 的平方残差均值，没有 pair 则为零。每个 epoch 都使用该 epoch 当前 critic 的同一次完整 batch 输出取 V_t、V_4，两端保留梯度。奖励、已采集目标和 mask 都不是新可微路径。原 advantages 仍由 rollout 采集时的 value 形成，按原方法归一化后 detach，并在四 epoch 内固定；不借此改成 TD advantage、重算 advantage 或另添 target network。[^5]

随机性沿用 b=100000×8201 的来源域安排，匹配初始化和 reset；两臂各有自己的 action／duration generator 对象，不共用会被另一臂消耗的可变流。它们是 on-policy 学习，后续轨迹和保持暴露可以不同；“配对”不是逐条训练轨迹相同的承诺，也不允许为了匹配而强制时长或伪造转移。[^1][^8]

## 原生结果怎样决定下一步

主要量是 32 个 reset 对齐的 δ_e=J_RESIDUAL,e−J_MLP,e 的均值 Δ，其中 J 是原生团队总回报除以 256。两项相对 H 的差、所有 episode（包括负差）、实际保持 row／pair 数和条件评价 SE 都保留。已有差值统计与 primary 读回路径足以服务这一问题；不新增 bootstrap 框架或策略搜索。若报告 s_δ/√32，应明确它只描述本次已训练模型和评价抽样条件下的噪声，不是训练总体标准误。独立训练单位仍为 n=1，32 个 reset 不能变成 32 个独立训练结果。[^1][^8][^12]

采用绝对 MEI=0.01 的原生时间平均团队回报作为本地解释尺度。来源给出一名持续服务用户的 coverage 贡献 0.7/50=0.014，只用于说明量纲，不保证服务质量或未测 headroom。H 不是上界，也不是经调优的完整同信息基线集合；这里仍没有 upper-minus-tuned-baseline headroom，不得从 H 差值推算比例改善。[^1][^9][^12]

| 完整且可比较的主结果 | 本地解释，不是自动后继规则 |
| --- | --- |
| Δ>0.01 | 对这个完整残差-MC 包出现一次可能值得再看的原生信号。只支持在全结果 intake 后考虑一个独立配对，不分配它，不要求所有 episode 都为正，也不称稳定优势。 |
| −0.01≤Δ≤0.01 | 在所选尺度内，没有重复这个不变惩罚的明确改善理由。包含精确边界；不称两种方法统计等价，也不把小正号或好看的残差误作成功。 |
| Δ<−0.01 | 此实例偏向完整 MC，保留所有损失；不自动调系数、加预算、换 seed 或反转方向结论。不能据此关闭所有 SCDMP 或所有残差方法。 |
| 依赖不完整 | 只限制依赖该缺口的结论。若两个最终 learner 的主比较不完整，不能给上述完整预算包作性能裁决；独立可信的已完成 episode、计数和异常仍报告。H 缺失不自动抹去独立完整的 learner 主比较，但所有 H 相关结论缺失。 |

若任一 learner 的 J−H 为负，必须和 Δ 并列；即使 Δ>0.01，也只能说相对本次完整 MC 有局部改善，不能借此宣称可用控制已建立。尤其两者都低于 H 时，不能将“较弱者中的较好者”写成已经实现有用时长控制。拟合损失下降、L_seg 下降或参数移动都不能救原生回报损失。预算或退出的缺陷同样应按实际依赖分别说明，不能用技术异常制造负性能，也不能据此自动重复已选调用。[^1][^8][^12]

如果所有实际 batch 都没有合格 pair，零辅助项仍是合法执行结果，而不是新的暴露门槛或重抽时长理由；它没有检验到非零残差处理的效果，只能如实限制解释。若支持很少，同样保留实际数目和回报，不增设“至少多少保持”才发布的门槛。[^1][^2]

## 工作量、预算及相称检查

主工作为两臂各一次训练，共 2×512×256 个 native team steps，加两个 learner 和 H 各 32×256 步最终评价：总计 286,720 native team steps、2,048 次 Adam、96 个最终评价 episode。没有中间 checkpoint 评价、候选策略搜寻、联合动作枚举、轨迹分支、solver 或额外 replay。因此主要成本来自原生采集及已有 recurrent PPO 更新，而不是所谓有限但可能组合爆炸的先验搜索。[^1][^2][^8]

每臂在 131,072 个训练 row 中最多有 1,536 个非零保持 row；处理臂四 epoch 累计最多 6,144 个 scalar 残差项。完整 batch critic 输出可以复用，不增加完整网络 forward、单独 backward 或 optimizer 调用；索引、残差运算及对现有计算图新增的梯度贡献仍是实际算法成本，不能写成零成本。对照只保留原 MC，不为了“工作相同”而给它增加另一种未选定损失。[^2][^5]

每臂的来源成本表达式保持为 131072×c_collection + 1024×c_update + 8192×c_eval + 完整开销；第二臂另承担 8192 个 H 步及配对输出。处理臂 c_update 包含新残差计算，不能直接假设等于对照。VSPC1 原配对 308.63 秒的完整外部 wall 是已有规划锚点，不是新损失的运行上界，更不是速度提升证据。新增 wall／CPU 未测；不再增加校准或 profiling 实验来取得选择资格。[^1][^9]

保留每臂 1,800 秒、整对 3,600 秒的完整 cap，覆盖 admission 邻接启动、导入与初始化、训练、最终评价、必要检查、publication/readback 和 exit；第二臂含 H 和整对输出。不能切片、重置时钟、借用第二臂额度掩盖第一臂超限，或把退出和发布排除后宣称满足完整上限。只在实际获选执行时取得新鲜资源 admission 和 detached accepted handle；本次没有取得新的运行 handle，也没有测量候选成本。超限或主要依赖失败就停止此次执行、保留已完成事实，不发生自动重试、加臂或加 seed。[^1][^8][^11]

相称检查仅覆盖本次改变及主比较：真实 episode 内 t1–3→t4 的索引与奖励区间、双端梯度、mask／无 pair 情况、原 MC 和 actor loss／detached advantages 的保留、配对 RNG 及 native primary 汇总。尤其应区分“辅助项对 actor 的直接梯度为零”和“联合裁剪后 actor 更新必须不变”：后者不成立，也不应作为错误的等价要求。独立 review 只覆盖受影响的学习路径；不重复未改动的 native 环境 suite，不做全历史回放或新增归因实验。这是 reward、information、training 和 primary 的必要检查，不是第五类 B 准入层。工程 scope §4 无新增需求，沿用现行研究代码和 runner 预算。[^5][^12][^13]

来源 MLP 的机器记录为每 learner 66,441 参数、1,024 次真实 Adam，total displacement/initial-L2=0.4681669210，critic 比值 0.7238134732。这支持既有 recipe 在该预算中能移动，不是新 penalty 已移动或有效的证据。新运行沿用实际参数组的初始尺度／位移记录，区分 total、critic、common actor 和 duration；零初始化 duration head 的相对比值没有意义，应读绝对位移，不能用分母加极小数制造巨大“暴露”。残差没有独立参数，也不设每个参数组必须移动的普遍门槛。[^2][^6]

## 源码缺口与后续边界

目前 main-derived 证据树缺少 `experiments/candidates/ucope/uav_motion_prefix_b01/environment.py`。我没有把这个文件当作已在本次输入中完整读取：其 hold、actor/critic feature 和团队奖励接口依据的是来源事实 JSON 中由 DM 从已指明原提交直接读取并保留的精确片段。已读取的 learner/policy 及 VSPC1 critic/study 则是本次固定证据版本的实际文件。这个区别使科学选择可以形成，却不等于当前拼装代码已可运行。[^1][^2][^5][^6][^7][^8]

选定后，由同一 CM 按既有已接受源码补齐该依赖、保持接口与原生语义，连同新增损失做上述相称检查和独立 review；若依赖补齐不成，报告具体执行缺口，而不是宣告机制负结果或另选人口。这里没有授权 Pro 修复源码、运行测试或实验；也没有实际源码接受结论。[^1][^11]

完整答复由同一 DM 直接 intake，随后形成这一个对象的卡，进入 CM 实现／review、accepted source、单次已选有界执行、全部结果收集与科学 intake；Root 按既有路径集成和观察。没有新增 Portfolio 实现批准、审批记录层或先行资格实验。任何后续独立 pair、TD 比较、非保持段比较、参数变化或 C 提升均未由这次选择分配。[^11][^12]

旧边界完整保留：RECAST_D6 保留当时的跨 k 共享问题；随后 PARK 保留其源状态／倒计时搜索家族没有已选后继的事实。A01 的一边倒 k13 及 A02 在 321 mission 后的人口失败都不重算，缺失 K 不填零；FCEOV 的原非通过与旧停止也不被新宿主消除。当前选择只是来自不同已运行 recipe 的新损失家族，不恢复旧 D6 搜索，不产生稳定优势、gate/TD 优势、唯一保持或 semigroup 归因、期望 Bellman 保证、迁移、安全、部署或自动 UAV 进入结论。[^3][^4]

本次咨询本身只有来源读取与这份交付；来源记录中的新模型、环境、native/synthetic steps、训练、评价、optimizer、replay、profiling 和新科学结果调用全为零，parameter displacement 对本次尚不存在的 learner 不适用。最小下一科学观察已明确：仅上述一个新配对的最终 sampled 原生回报，而不是先找一个更好看的残差或双向时长人口。[^2]

## 实际读取与引用范围

以下十三项均通过 GitHub connector 在同一固定证据版本 `21a801279bd449c09907f5cf040efa693ae345a3` 读取。DIRECTION 只据 D6 recast／family park 的相关段落作判断；证据规范主要使用 §§4、5.2、11.4、11.7–11.9，工程规范使用 §§4–5。未访问它们所链接的未列入清单文件、旧运行根、原 environment.py 全文件或文献原文；引用来源 reconnaissance 时已明确归属。TASK 的固定版本与交付分支状态分别读取，仅用于本次范围及交付，不替换科学证据版本。

[^1]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_INTAKE_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_INTAKE_20260908.md)，§§2–4 的源码／梯度及文献归属，§§5–6 的唯一候选和工作量，§§7–9 的反证、边界及返回路径。

[^2]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_FACTS_20260908.json](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_FACTS_20260908.json)，`sources`、`held_interface_excerpts`、`source_budget_reference_only`、`prior_mlp_exposure`、`actual_p56_exposure` 和 `unselected_candidate`；计数为来源或前瞻量，不是本次已执行量。

[^3]: [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_D6_A02_POPULATION_CONVERGENCE_INTAKE_20260904.md](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_D6_A02_POPULATION_CONVERGENCE_INTAKE_20260904.md)，“Decision executed without local override”“Direct observations retained”“Exact re-entry condition”。

[^4]: [docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md)，“D6 cross-k Q-sharing recast — 2026-09-04”及“D6 action-choice family park — 2026-09-04”。

[^5]: [experiments/candidates/ucope/uav_motion_prefix_b01/learner.py](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py)，`returns_to_go`（12–14）、`collect_episode`（29–155）、`optimizer_for`（173–176）、`update`（179–212）。

[^6]: [experiments/candidates/ucope/uav_motion_prefix_b01/policy.py](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/experiments/candidates/ucope/uav_motion_prefix_b01/policy.py)，Actor/Critic、`joint_terms`、`sample`及参数组／exposure。

[^7]: [experiments/candidates/vsp_c1/native_hold_value_b01/critic.py](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/experiments/candidates/vsp_c1/native_hold_value_b01/critic.py)，`GatedCritic`、`models`和零初始 gate 位移处理。

[^8]: [experiments/candidates/vsp_c1/native_hold_value_b01/study.py](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/experiments/candidates/vsp_c1/native_hold_value_b01/study.py)，`Config`、`Deadline`、`primary_from_rows`、`run_pair`及 final-only sampled/H 评价、RNG 与 publication/readback。

[^9]: [docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B01_INTAKE_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B01_INTAKE_20260908.md)，§§1–4 的 n=1 结果、负 episode、稀疏支持、解释限制与完整外部 wall。

[^10]: [docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B02_P47_7002_AND_JOINT_TECHNICAL_ACCEPTANCE_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B02_P47_7002_AND_JOINT_TECHNICAL_ACCEPTANCE_20260908.md)，“Existing arithmetic-only aggregate”及“Preserved limitations and return”；技术接受和数值事实不代替 UCOPE 的方向裁决。

[^11]: [docs/research/portfolio/handoffs/2026-09-08-p56-scdmp-native-return-composition-question.md](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/docs/research/portfolio/handoffs/2026-09-08-p56-scdmp-native-return-composition-question.md)，Target/deliverable、Source constraints、Acceptance/return、Budget/stop。

[^12]: [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md)，§§4、5.2、11.4、11.7–11.9，特别是问题选择、单次可信 B、依赖限定、未知成本与禁止搜索先于普通训练的普遍门槛。

[^13]: [docs/project/ENGINEERING_SCOPE_SPEC.md](https://github.com/CartmanFatass/My-paper-code/blob/21a801279bd449c09907f5cf040efa693ae345a3/docs/project/ENGINEERING_SCOPE_SPEC.md)，§§4–5；无新机械设施，相称检查与现行预算。

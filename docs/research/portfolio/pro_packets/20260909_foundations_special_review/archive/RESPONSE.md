# 保留有限实验事实，纠正推断边界，不作整批无效判定

**本次复审的实质结论是：没有证据支持把这十个方向的近期研究整体判为无效，也没有证据把其成败归因于 Astra 缺少背景知识。应保留已经读到的有限原生结果和多数包级停止决定，同时作明确的局部纠正。最重要的例外是 RCLE：B03 的配对比较没有完成，W100 的未知训练前缀不能记为零，W1 的完整单臂观察不能替代 W100−W1 的效应。CRTO 则有完整可读的诊断结果，但没有原卡要求的合格对照残差结论；这两种情况不能混为一种“失败”。**

我的 Portfolio 提案是：先处理已有记录的归因、单位和状态文字问题；继续把 UCOPE 已选的 normalized/raw G 问题与 FOLR 的独立训练比较作为优先准备事项；RCLE 只把缺失配对及其实际运行风险返回原 DM/CM，不自动重跑。FSD、VSP-C1、ACVC、MGTAP、CRTO 的具名停止可以保留。VSP03 的暂停是可辩护但证据不决定唯一答案的 close-call，不能变成“没有新用途就不许增加独立 seed”的规则。SCDMP 当前只是本次投入结束，没有据此关闭整个 residual 家族。

**这些是科学有效性判断与待整合的后续建议，不分配新实验，不选择新 seed，不改变任何生命周期、Priority、recast 计数、五链目标或旧 D6 边界。** 当前规范足以处理下面的问题，无需新增全局规范例外、审查层或统一诊断前置。历史卡、数据和判断保留；本报告是显式追加的现时复审，不把旧结果静默改成另一规则的通过或失败。〔[任务][task]；[当前证据规范 §§4–6、11.8–11.10][spec]；[当前 Portfolio][portfolio]〕

## 一、如何判断“站得住脚”

这里分别回答三个问题，而不以一个总标签代替它们：第一，记录的干预、训练和主要测量是否支持所报告的有限比较；第二，解释是否越过该比较能够识别的范围；第三，在保留不确定性的前提下，继续或停止是否是合理的投资判断。实际源码阅读能够发现接口和公式问题，但不是运行复现；技术验收记录支持历史执行事实，也不是本节点重新验收了所有依赖。

基础材料在本题中的实际用途如下。

**状态变化、循环状态更新和参数学习不同。** 固定策略在部署时更新 GRU 或依据新观测改变动作，不等于部署时更新参数。共同训练的队友可以通过彼此改变的策略产生训练非平稳性；这不要求外部环境规律漂移。相反，固定公开伙伴计划的 toy 不能仅凭有两个实体就取得战略性 MARL 的解释。FOLR 的真实成员事件、ACVC 的固定成员链路观测变化、UCOPE 的动作保持和 VSP03 的共享服务槽，分别是不同的变化。〔[RL 专题][rl]；[MARL 专题][marl]；[层级与异步专题][hier]〕

**表示包含不等于有限训练保证。** 一个 GENERIC 含有处理臂的输入或函数路径，并不保证在相同有限预算内更优；参数数相同也不保证有效容量、计算量或优化条件相同。固定非学习参照可能很强，但它不是调优通用 learner 或全局上界。没有打败强固定参照，可以限制实际增量价值，不必使两个真实 learner 之间的比较失去定义。〔[FOUNDATIONS][found]；[RL 专题][rl]〕

**训练包差异不等于单机制因果效应。** critic 改动可以通过未来优势估计、联合梯度裁剪和后续采样影响 actor；不能因 critic 不直接输出动作而说它无因果通路，也不能因最终回报变化就把原因唯一归到 critic 表示。保持动作的时间跨度、GRU 的观测频率、信用归一化和参数更新次数必须分别追踪。有限时域 gamma=1 的 Monte Carlo 回报不需要为了“层级”而人为添加周期折扣；其合法性也不意味着所用压缩 critic 状态自动具有精确 Bellman 闭合。〔[RL 专题][rl]；[层级与异步专题][hier]〕

**评价配对与训练重复不同。** 合法的共同随机数比较允许两策略采取不同动作、访问不同状态；配对不是要求轨迹逐步相同。但相同 seed 标签本身也不证明相同外生事件，尤其在事件和随机数消耗依赖动作时。以下条件评价 SE 不被当成训练总体 SE，checkpoint、车辆、UAV 或反复使用的历史身份均不增加独立训练实例数。MEI 是本对象的尺度和原读法，不是显著性或等价检验。〔[经验研究专题][emp]；[证据规范 §11.8.3–5][spec]〕

没有将这些基础材料中的某种算法偏好推广为十个方向都必须采用 MAPPO、return-only 或一种统一训练器。

## 二、逐方向复审

### 1. UCOPE：P85 反对本次 mean-velocity 用途，不否定先前 sampled F−G 观察

**原问题与实际实验。** P85 在一个新配对训练实例中训练 F/G，再对相同最终权重分别读 Fmean、Gmean、Fsample、Gsample 和 H。这里 mean 是执行 `tanh(mu)`，不是 `E[tanh(U)]`；Fmean 仍有固定随机持续时间，因此不是整个联合策略都变成确定性。F 的持续头是固定律，不是学会了何时付费获取信息。主张必须限于该固定保持／执行包，不恢复早期 paid-information 主张。〔[P85 卡 §§2–3][u-card]；[policy.sample 与 joint_terms][u-policy]；[P85 结果][u-result]〕

**源码链条支持的内容。** 本轮读取的执行版 `environment.py::actor_features/critic_features/team_reward` 把私有观测、实际上一命令和剩余保持送给 actor，global state 与先前承诺送给 critic；没有从这些路径发现把全局诊断索引喂给 actor。`uav_env.py::step` 先更新全部 UAV 位置，再更新信道和奖励，每个 agent 得到团队奖励的五分之一。原 adapter 的 scalar 是再次平均后的量，而本实验 `team_reward` 明确求和原 `rewards_dict`，故这里没有凭 scalar 错把 J 再除以五。`learner.py` 使用完整 256 步回报、终端零续接、已采集动作及 active mask；动作保持时 GRU 仍处理观测。以上核验不等于独立复核了全部无线信道数值实现。〔[执行版环境快照][u-env]；[native reset/step 与观测段][native]；[adapter.step][adapter]；[执行版 learner][u-learner]〕

**测量与解释。** P85 主差 Fmean−Gmean 为 −0.0083501310，条件 SE 0.0067366485，原读法 WITHIN 正确，但不等价于零。Fmean/Gmean 均值约 0.06637/0.07472，均低于 H 的约 0.15647；F/G 从 sampled 改为 mean 的差分别约 −0.04256/−0.05655。本次数据不支持“去采样噪声就恢复服务”的预期。它不能唯一识别训练失败原因，也不能用新 mean 主量覆盖原 sampled 主量。〔[P85 结果的完整五模式表][u-result]〕

最强反对广泛否定的证据仍是真实旧增益：P83 F−G 为 +0.0420551463，且 F−H 为 +0.0168804390；P84 F−G 为 +0.0643936652，但 F−H 已为 −0.0291844433、G−H 为 −0.0935781085。因此“两次 F−G UP”不等于两次比 hover 更有用，也不能用 hover 损失追溯宣布两个 learner 的原比较无效。五评价模式只来自两个新训练 fit；32 个 episode 每模式只提供条件评价信息。〔[P83 intake §§6–8][u83]；[P84 intake §§7–8][u84]〕

**最小纠正与下一问题。** 保留现有完整 Pro 对未来 normalized-G/raw-G/H 问题的选择，同时保留“尚未定位原因”。执行版中优势在 rollout 上计算并 detach，actor 和 critic 参数随后共同裁剪；归一化 critic target 可能改变 value-loss 尺度、裁剪因子和未来 baseline，却不是已证实的疗法。它也不自动等同 PopArt、奖励变换或不变的优化轨迹。最小有用后续是原节点已经提出的真实 G 比较，不是再次 mean 测试或对十方向统一补 value normalization。本轮不填写它尚未选择的 master、训练预算或调用。〔[P85 后完整 Pro 的选择与 normalization 说明][u-pro]；[learner.update][u-learner]〕

### 2. FOLR：RESET 的有限胜出有效，但不是“遗忘必有益”

**问题与链条。** 这里确有车辆出生、离开和同一步填回，不是把 slot mask 翻转当作实体生命期。`environment.py` 记录真实 D/B，并用 `C=A_before & A_after & ~D & ~B` 区分真正续存；当前演员都看到公开 E 和自身 B。`model.py` 在处理当前观测前执行本臂的 hidden-state 规则，online/target unroll 均采用它；两臂共同清理新生／不活动 slot，并仅为真实续存者保留上一动作。固定公共生命周期协议本身是明确的信息扩展，不能称为原始 CAMA 私有协议不变。〔[科学卡][fo-card]；[事件适配][fo-env]；[model.Actor][fo-model]；[learner.Learner.update][fo-learner]〕

这是一项分别在 RETAIN/RESET 规则下训练的整体系统比较，不是对已经在 RETAIN 下训练的策略事后破坏记忆。学习器使用 replay、double Q、FlexQMixer 和 gamma=.99；评价读完整原生 episode return。共同采用这一训练法可以支持有限性能比较，但不保证精确优化其未折扣终点。控制者可用的是受可见性约束的实体表示加两项公开生命周期信息；本轮没有逐层重新审计 imported attention/mixer 的全部实现。

**有效观察。** 最终均值 RETAIN 2.104375、RESET 4.1065625，差 −2.0021875，按含边界 MEI=1 落入 RESET_ABOVE_MEI。两臂各有 5,000 个训练 episode、4,969 个 RMSprop step，最终 32 个评价 episode；记录中真实 survivor 机会及 RESET 操作非零。RESET 的训练期平均表现较差、最终 episode 离散程度很大，都与该终点反向结果一起保留。没有依据将其排除为“和记忆理论相反所以无效”。〔[完整结果][fo-result]；[intake 的结果解释及下一步][fo-intake]〕

**推断上限与最强反证。** 一个配对训练实例不证明 RESET 稳定获益。相同初始化和起始随机种子也不保证两臂有相同交通事件：不同动作可以改变碰撞、离场、再生和全局随机流消耗。机会数差异是可能的策略后果，不能按事后事件筛选或除以 reset 次数来制造纯遗忘效应。状态归属为“本车”不意味着其历史中没有队友信息；结果不能恢复严格 self-only ancestry 主张。前次 Pro 已明确 RESET 也可能获益，故当前反向结果没有推翻当时选实验的逻辑。〔[collection][fo-collection]；[native_env 已读移动/移除/填回路径][fo-native]；[完整 P78 Pro][fo-pro]〕

**处置。** 保留本次 B 和公开生命周期问题；支持将原 DM 的另一个独立训练对建议优先准备，目的只是检验这种训练后效果的重复性，不需先定位哪个记忆内容有害。当前不分配该训练对、不挑 seed，也不增加一套事件普查。若后续没有可控的真实 survivor 后续行动机会，则只限制该记忆解释，而不是凭总回报宣布状态管理有效。

### 3. RCLE：选择 actor100 的理由可成立，B03 却没有给出它的疗效

**干预是学习法则，不是表示包胜负。** B03 在同一 FLEX 中把 claim-score 权重从 1 改为 100，同时保持每次非零整体更新范数 .02。干预改变的是 `(g_M+100g_A)/||g_M+100g_A||`，不是把参数移动放大 100 倍，也不是由“小 actor 梯度比例”推导出的无偏策略梯度修正。前次 A02 的低比例、基线敏感性及局部概率变化为这个假说提供动机，不保证 W100 的服务回报改善。原 Innovator 正文已经保留该反对理由，选择真实训练而非再做资格 A 是合理的 B 设计。〔[B03 卡][rc-card]；[study 的权重与固定范数更新调用][rc-code]；[前次完整 Pro 的 A02 解读及备选比较][rc-pro]〕

宿主中的出生／离开、续存与 NEW_EPOCH 语义、局部信标和 claim 动作进入真实服务后果；主量 U 是事件后窗口未服务比例，低为好。训练 Y 的时间范围不同，不能只用 Y 改善替代两条 ACTIVE_CONTINUATION 路径的最终 U。八格、两个路径和每格场景都不变成独立训练实例。

**现有结果是“单臂完整，配对缺失”。** W1 完成 200 次非零更新、12,800 训练 episode，以及初始化／最终各 2,048 个评价 episode，共 1,081,344 ticks。它的主路径均值 U 从 0.704490153 到 0.704335531，G_U=+0.000154622396、条件场景 SE≈0.0005000111；这是 W1 自身的伴随测量，不是 W1−W100。八格 tau=40 及 8→8 NEW_EPOCH 的负 G_U 仍保留。W100 signal11，没有最终面板，训练前缀未知；其初始 checkpoint 存在不能证明没开始训练，53.20 秒存活也不能推出完成了多少更新。脚本参考缺失同样不填入历史另一面板值。〔[最终 905be66c… intake][rc-intake]〕

**纠正。** 不形成 actor100 阳性、阴性、baseline 病因或 RCLE 无法学习的结论。原 intake 已将辅助面板标签 `init` 与先前期待的 `FLEX-INIT` 对齐；这是记录绑定纠正，不是新增实验或给 W100 补值。十二个分配模型对象含两个训练起点与十个 helper，不是十二次训练。日志中的 ctypes 线索没有匹配的调用栈证实原因，不把它当成故障定位完成。

最小后续是将确切缺失和运行风险交回原 DM/CM：以后若另有工程／实验分配，针对会威胁配对比较的依赖处理，并取得真实 W100/W1 比较；是否能在同一比较合同下复用保留 W1，应明确判断，不能默默把历史 W1 配给一个改变了算法或数据的 W100。本次不授予 retry、另一个诊断或更强系数。现有有效 W1 不被一并丢弃，原 B03 也不因一个进程失败而产生科学负极性。

### 4. SCDMP：residual-MC 是一个可解释的训练干预，不是精确 Bellman 定理

**实验回答的是辅助信用包是否改善最终策略。** 在 opening hold 为 1/4 的实际 UAV 路径中，用 gamma=1 完整 MC 保留主 critic loss；处理臂另加 held-context 约束，t=1、2、3 的值与边界 t=4 及其间实际 reward 相连。源码 `learner.py` 对两端 value 都保留梯度，`R_t:4` 不含 r4；它不是把 t=4 value detach 后的普通 TD target，也不是教师提供的最优 value。实际目标为 actor loss 加 `.5*(MC+segment)` 再减 entropy 项。〔[卡][sc-card]；[residual learner][sc-code]〕

在实际轨迹上，令 `e_t=V_t-G_t`，则 `(V_t-R_t:4-V_4)=e_t-e_4` 是该 gamma=1 回报分解下的代数关系；**它没有证明压缩 critic 输入满足精确 Markov/Bellman 方程，也没有保证该差值惩罚降低策略损失或方差**。critic loss 通过后续 baseline 和共同裁剪影响 actor；当前优势已 detach，不能写成辅助值损失直接穿过优势对当前 actor 求导。eligible team-time pair 不是五个独立 agent 样本；单独归一化的稀疏辅助项，其权重也不能由占总步数比例推断。〔[共同收集/更新源码快照][sc-base]；[环境承诺状态快照][sc-env]；[原 held-residual Pro][sc-pro]〕

**测量成立，但只支持小正点。** RESIDUALMC−MLPMC 为 +0.00673740746，条件 SE .00559654654，14/32 个 episode 差为负，原 ±.01 读法 WITHIN 正确。双方均值 .154934041432/.148196633977；对 H 的 +.007086659469/+.000349252013 同样有限，分别保留 15/18 个负 episode。记录有 1,500 eligible pairs、6,000 residual terms 和两端梯度，不能说新项没有被执行；非零梯度也不证明它有用。〔[结果及 intake §§结果、曝光、解释][sc-intake]〕

**处置。** 保留本次有效包观察，不把 WITHIN 改写为零、等价或 semigroup 失败。当前没有不变更地续跑的分配，这是可保留的支出边界，而非整个 residual 家族被否证。一个独立训练对本可研究重复性；若以后重提，需说明它与优先事项的边际价值，不必先证明机制或得到超过 MEI 的旧点。本轮不自动追加它，也不重开旧 D6；第二次 recast 的排序保持。

### 5. FSD：两次终点损失支持停止这个训练扩展，不识别中断机制普遍有害

实际比较是 scenario1、六 UAV、k=10、cap=10、个体中断成本 .25、五个训练更新阶段的 I/D0。报告 `J=6U/500` 恢复 native 团队逐步单位，而不是改训练 reward；五个更新阶段不等于五次 optimizer.step。入口读取显示训练和固定评价分开、保留完整 500 步终局和新评价种子，但本轮没有逐行重审所导入的全部 D2/buffer/协调器实现，故不另宣称完成了内层训练正确性证明。〔[B02 卡][fs-card]；[runner 的配置、训练和评价循环][fs-run]〕

P72 I−D0 为 −0.03531272530，条件 SE .01252348994；P70 为 −0.04967056317，两对均为局部负面。P72 仍有 9 个正 episode，且 sampled 训练回报后期较高；它们不替代最终固定评价。训练期 I 有 65,761 个 gap、3,765 次协调器调用，D0 为 0/525；这说明训练经验及高层更新机会随处理变化。两臂最终评价都没有 gap，却有不同 token switching 和服务结果，因此不能把终点损失描述成“评价时频繁中断直接付了 .25 的代价”。〔[P72 完整 E0][fs-result]〕

P72 的覆盖损失与质量／高度相关收益相抵，P70 的组成不同；没有共同原因已经被识别。训练机会、优化、上下层协同适应及实际执行行为都仍是解释的一部分。实际因果对照是整个配置训练包，不是孤立的中断时机效应。〔[完整 P74 Pro 的原生组成及反证][fs-pro]〕

**保留停止。** 两次同配置终点受损且原扩展已回答有限复现问题，停止这一个 `.25/k10/five-update` 包合理。最强反对理由是更长训练或其他中断信用可能不同；现有数据不能否定它，但也没有测得更长训练有效。若以后重入，应明确改变的时序／信用问题和共同曝光，不把单纯多跑称作已证实修复。本轮不加第三对、二十阶段或调整门槛，不关闭灵活时长方向。

### 6. VSP-C1：B13 是 intact-body-plus-gate 的反例，不是旧容量解释的排他检验

B13 不再是早先公开固定伙伴的两周期 toy。其当前任务是 native UAV 上 136 维 critic：完整普通 body 加 640 个 gate 参数，对比无 gate 的完整 MLP。critic 参数数 35,467/34,827，**不容量匹配**；两臂 actor 相同。`critic.py` 的零 gate 起点包含普通 body，但优化后可不同；`value_normalization.py` 以每个 rollout 的训练 target 更新一次累计矩、四个 epoch 和评价时冻结使用，不是 output-preserving PopArt。〔[B13 卡][c1-card]；[critic][c1-critic]；[normalization][c1-norm]；[study 的 intact_body、训练与最终评价分支][c1-study]〕

critic→未来优势→PPO→actor 以及 actor/critic 共同梯度裁剪是一条真实路径。由于当前优势在四个 epoch 前已固定、两网络并非任意共享隐藏参数，不能把这一路径简写成当前 critic loss 直接给 actor 一项可证明改善的梯度。gate 只在持有相关状态活跃，也不意味着最终收益影响至多为前四步比例。〔[该执行版本的共同 learner.update][c1-base]〕

B13 一对新 master 8601 各训练 768 episode、1,536 次 Adam；最终 GATED−MLP 为 −0.03206858050，条件 SE .01011068353，25/32 为负，DOWN 成立。GATED/MLP/H 均值约 .1443234961/.1763920766/.1408296190；GATED 仍有小正 H 点，MLP 对 H 的较大正点必须同时保留。gate 有非零暴露，不是永远留在零投影。零初始化投影只报告绝对位移或未定义相对值，不能用 epsilon 分母得到巨大“相对学习成功”。〔[B13 结果][c1-result]〕

早先 512 更新协议的 UP/UP/DOWN 与 768 协议的 WITHIN/WITHIN/DOWN 保留。一个实例内的 512/768 状态相关，新的 B13 又同时改变 body、训练实例和评价设置；它不是旧容量权衡原因的受控反事实。完整 Pro 已承认这些差别，因此无需撤销历史正值，也不能从 B13 证明所有 gate 或跨时长 value sharing 无效。〔[B13 后完整 Pro 的历史表及容量讨论][c1-pro]〕

**保留停止当前 intact-body-plus-gate 包。** 若重入，须有具体 critic 操作或有明确价值的同配置重复问题，继续观察完整 native J，并披露容量、归一化和优化变化；不要求先证明表示必要性。当前单对负面足以支持不再投资的选择，却不足以科学关闭整个 critic 家族。

### 7. VSP03：小正值是真实 B 信息；暂停是边际偏好，不是统计裁决

实际对象有两个固定控制者竞争一个服务槽，提交后占槽八步，即使失败也不提前释放，可能影响伙伴最后机会。`b02.py` 的团队 return-to-go 排除已经发生的前缀收益，保留以后伙伴的后果；训练用真实 action score，最终按事前固定的 `logit>0` greedy 执行。十四维信息公开，具有真实多主体资源耦合，但可以由全公开集中调度观点描述，不识别去中心化或私有信息的独特价值。〔[P76 卡][v3-card]；[b02 实际事件/信用路径][v3-code]；[b01 训练定义相关段][v3-base]；[b03 greedy 评价][v3-greedy]〕

seed5/6/7 最终 greedy G−R0 为 −.013974609375、+.0026123046875、+.0023291015625；三实例描述均值 −.00301106771、SD .00949576144。seed7 的条件评价 SE .007670301077 大于其正点，但这不是推翻原 B 读法的新显著性门槛。新的正点来自更多成功、更多尝试成本和少量等待收益之和，不是仅一个代理指标。另一方面，seed7 stochastic G−R0 为 −.05152832031，必须保留；它限制随机执行用途，不否定已先选定的 greedy 用途。〔[P76 intake §§2–4][v3-intake]〕

一个训练 G 的四种评价模式不是四次训练，1,024 个世界也不是 1,024 个 learner。跨实例的评价世界也改变，实例 SD 未分离纯训练方差；发现用 seed4 单列、不并入后续三实例。所有这些当前记录的限定是正确的。

**我保留本次暂停为可辩护的 close-call，但不把它写成数据强迫的唯一结论。** 两个便宜的独立 greedy 正点是最强反对意见；没有证据证明再一实例无信息价值。最新 Pro 已明确修正“没有新用途就不能续跑”的旧论证，并承认未算出下一观察价值为负。因此无需因它选择暂停而指控逻辑错误；也不应让 Root/DM 再把同预算独立重复排除为不合法。若资源和研究目标重新支持复现，可回原节点以未解决的变异问题重新比较，不必先改算法、发明新用途或找到正向原因。本轮不静默解除 ordinary-G/update128/公开 N2 greedy 家族的暂停。〔[最新完整 Pro 的 close-call、上次纠正与最终边界][v3-pro]〕

### 8. ACVC：固定 F 更强限制选择器价值，但历史与 retrace 仍有用

这里没有成员变化：五 UAV 都存在，变化的是自身局部链路可见性。`binding.py` 用既有坐标与 SINR 约定绑定上一低 SINR 用户，仅在不空、不饱和、无歧义的当前列表中判断该锚点缺失；机会还要求当前 sampled proposer 朝远离方向移动。retracing 反转的是上一实际位移／30，经边界裁剪后可能不等于命令的负值，更不恢复其他 UAV 的联合状态。私有链路丢失也可能伴随有利的用户转交，不等于全局服务失败。〔[B02 卡][ac-card]；[binding][ac-binding]〕

C 直接执行冻结的 DENSE/8201 proposal，F 在机会时总 retrace；T/G 训练选择器，G 包含 T 的路径加同信息 residual。`learner.py` 复用采集到的 proposal 计算 gate-only likelihood，没有为了优化重抽一个 proposal；非机会行不虚构 gate 动作。F 的 gate 是确定的，但底层 proposal 仍 sampled，故 F 不是整个过程确定性。G 的函数包含不保证有限训练赢 T；C/F 是常数选择的极限，也不应写成有限 sigmoid 参数必能逐值实现。〔[model][ac-model]；[learner][ac-learner]；[report 的固定对照聚合][ac-report]〕

两次实例 T/G 对 C 都有增益、对 F 都有损失。最新 T−C=+.0535912110、T−F=−.0542533634、T−G=−.0065945815；首次 T−G 的 +.0369687053 没有在第二次保持。主要 `min(mean(T−C),mean(T−F))` 是两个事前固定对照均值的较差差值，不是逐 episode 选择最佳参考，也没有一个凭选择后复用的独立 SE。旧 .25 S=.0009765625 J 和本轮 .01 J=2.56 S 不混用。〔[B02 intake][ac-intake]；[完整后续 Pro 的两实例表][ac-pro]〕

**保留结束该 instantiated learned selective-retrace 包。** 最强停止依据是无需额外训练的 F 两次都更强，而不是两个 seed 证明选择学习普遍无用。最强反证是 T/G 的真实改善及 F 对 C 更大的原生收益；这些使有价值的例外选择仍是可能的新问题。F 本身使用历史，且共同 proposer 已 recurrent，因此 F−C 不是纯 history/no-history 实验。DENSE8201 是看过早先结果后选择的固定资产，新的试验独立随机性不消除该选择背景。今后若重入，应说明拟学的 F 例外及同信息强对照，不靠选择更差 C 来制造成功；本轮不选第三实例，保留第二次 recast 排序。

### 9. MGTAP：REL 包确有负面结果，但“mean 抹掉数量”不是该源码事实

实际动作是 UAV 速度，服务分配仍由 native 规则完成；没有 actor 选择 ground allocation。`geometry.py` 在完整 raw 输入旁加入 typed nonlinear row 分支，user/UAV 聚合分别除以固定 20/10 个槽数，bias-free 零 padding 不贡献激活。DENSE 保留同样全部原始信息和 recurrent 主体。两附加分支参数均为 2,768，完整 learner 各 69,079；这只是计数匹配，不是相同函数类、计算或优化。〔[卡][mg-card]；[geometry.py][mg-code]；[runner 的实际两臂收集/评价][mg-run]〕

8201 REL−DENSE 为 −.0446825251645，8202 为 −.00324368344565，等权两 master 均值 −.0239631043051，原 REL_ADVERSE 成立。第二个 master 在 MEI 内且 REL 高于 H，是反对广泛几何失败的重要事实。训练对 SD .02930168598 与合并条件评价 SE .00264853582 描述不同随机性，不能拿较小后者宣布 DENSE 稳定优越。两 master 才是训练单位，全部 episode 和五个 UAV 不扩充该单位。〔[P75 intake §§3–6][mg-intake]〕

**前次 Pro 对 sum/mean 的代数区分成立。** 把固定分母的 mean 改为 sum，可以通过重标定 learned projection 的两个 block 表达同一映射；这不证明 Adam 轨迹或有限回报一样。明确 count feature 或非线性 count-conditioned 处理仍可能改变可学性；原 raw 输入可导出某信息，也不意味着显式处理毫无价值。但其 count 必须是当前截断后可见记录数，不是用户总数、隐含需求或 global 服务数。〔[完整 Pro 的 pooling/备选讨论][mg-pro]〕

保留当前 native actor-family 的可逆暂停与旧 coordinate 家族的独立暂停。停止是对已测不利包及当前未充分具体化改动的价值判断，不是证明所有几何处理无效。若下一提案具体到一种 count/geometry 操作及其 native 作用，可再比较真实学习；不要求先证明新增信息、先定位 P75 原因或先取得正值。本轮不把合法但未选择的 sum/count B 自动分配出去。旧记录“allocation consumed”仅指预算结束，不能移植成 B 假说被消费。

### 10. CRTO：诊断结果完整，零控制差可读；原始合格残差信号没有成立

这是固定选中历史上的监督式 native-action cost 学习，而非全策略在线 RL。`expected_native_cost_loss` 对合法动作 softmax 的 native regret 求期望，label detach；训练输出是 logits，评价用确定的合法 argmax。训练 loss 下降不保证 argmax 改变。三个表示都采用新目标，RAW 含 TRUE 变换所用输入，derangement 保留 packet multiset 而破坏对应。一个复用 seed0、48 TRAIN/16 多次开发暴露的 EVAL 身份、33/258 两端点，只支持这个有限选中面板；96 个读数不是 96 次独立训练。〔[B08 卡 §§1–4][cr-card]；[experiment.py 的 loss/train_path/score_summary][cr-code]〕

实际三个臂、两个端点动作向量相同，均为 11 KEEP、5 RELAY-L，regret .00212945449306。RAW-LONG 的 KEEP 8/8、REPLAN 5/8，两个 side 的平均 regret 合格，但 REPLAN 未达至少 6 个 oracle 动作。因而保留 WEAK_NEW_RAW_LONG_DIAGNOSTICS_ONLY，不借旧 RAW 资格救新 RAW，也不因此说“什么都没有观察到”。两个 matched contrast 均为零是直接事实；它不证明 packet 被忽略、函数等价或所有中间更新的 policy 一直相同。〔[P71 intake §§1–3][cr-intake]〕

历史 RAW 对 TRUE 的净增益 SHORT +.00445242649647、LONG +.00165197559264 含有 3/2 条损失。TRUE 相对自身历史改善更大也不识别 alignment。对固定这十六行和这份 RAW，非负 regret 给出 `R(RAW)-R(T) <= .00212945449306 < .0025`；该现成算术解释了为何修补第六个正确动作并不能达原 margin。它不是全策略最大值、调优 headroom，尤其不证明另一个训练实例或明确不同问题不值得研究。这里无需为使用这条简单现成界再建一个 A。〔[完整 Pro 的 recorded-baseline ceiling 与重入条件][cr-pro]〕

**有一个具体但未触发的实现风险应回原 CM。** 在实际 `experiment.py::train_path`，最终 update 对 movement 字典中任何非正值直接抛异常；已观测 B08 的位移为正，因此它没有使此次结果失效。但有限的零净位移并不逻辑等于未执行 optimizer 或没有有效 reward 信息。该检查可能比当前“如实记录实际曝光、不设任意位移门槛”的方法要求更强。最小处理是由原 DM/CM核对这个卡实际需要的移动量定义和影响，把非必要零值自动拒绝改为诚实的曝光读法；保留 nonfinite、错误训练和损坏主量的真实检查。本轮没有执行到此分支、没有复现故障、没有修补代码或分配重新运行。最强反对理由是它本来可抓住断图／完全不更新；因此要对实际更新证据和依赖作精确处理，而不是删除所有曝光检查。〔[train_path 最终 movement 条件][cr-code]；[规范 §11.4、11.8.5–7][spec]〕

**保留 selected-panel balanced-residual 家族的可逆 PARK。** 理由是当前控制差、固定参考的 margin 限制及没有更有价值的具体后继，而非单独的 5/8、缺统计显著或全方向不存在学习空间。更小效应、另一合法信用问题或独立训练重复可在正确命名下重新比较，不能降低旧 MEI、剔除已学好的 RAW 或挑更差 seed 来声称原问题成功。

## 三、跨方向发现：明确错误、未证实风险和合理分歧分开

| 所在记录／责任层 | 本轮发现及性质 | 影响与最小处理 |
| --- | --- | --- |
| Root `PORTFOLIO.md` 的当前开头与 RCLE 当前行 | 开头仍说原 DM 完成 B03 intake 是下一事项，同一快照当前行却已记 final intake 接受；最新 905be66c… 文档也完整。属于异步状态文字冲突 | 后续整合时以实际完整 intake 为事实，修正当前摘要，不再制造一次“等待科学 intake”的依赖；保留历史边界，不改 W100 缺失 |
| Root 机械 `EXPOSURE.json` 的 CRTO `primary_and_mei` | 写成每个“8-row budget”；原卡实际是 RAW-LONG 每个八行 side 的资格，SHORT/LONG 是不同概念 | 修正索引描述为 KEEP/REPLAN 两 side，不能因此增设 SHORT 也必须单独合格。原卡及 P71 读法不变 |
| RCLE DM 的辅助面板名称 | 先前预计 FLEX-INIT，实际产物为 init；最终 intake 已按真实标签及内容完成绑定纠正 | 这是已处理的记录问题，不是新数据，也不能被复审重复宣布仍缺初始化证据 |
| CRTO semantic 实现的最终 movement 条件 | 上述未触发的零值拒绝风险 | 返回原 CM 核对依赖和必要性；不撤销当前真实正位移结果，不增加新测试框架 |
| VSP03 前后 Pro 的续投理由 | 最新 Pro 明确纠正旧“无新用途所以不能续跑”的论证，同时仍选择 close-call 暂停 | 独立训练重复的描述性价值本来合法；现时停止可以保留为可逆偏好，不能再写成统计或方法禁令 |
| CM、DM、Pro 的 accepted/COMPLETE/UP 字样 | 在已读最新正文中通常已有局限；这些标签离开原上下文容易被 Root 摘要放大 | COMPLETE 只在相应依赖完整时用；UP/WITHIN 保留原 estimand 和单位，不自动传播为创新、充分学习、稳定优势或整个方向状态 |

前两项直接依据当前 [Portfolio][portfolio] 与 [EXPOSURE][work] 对照原卡及 final intake；第三项见 [RCLE 最终 intake][rc-intake]；后两项见 [CRTO 源码][cr-code] 与 [VSP03 原答][v3-pro]。这些问题不全是科学实验错误。反过来，当前已经主动保留相反结果、比较器局限和成本的 DM/CM/Pro 记录，也不能为了说明模型偏差而忽略。

更普遍的**推断风险**是把“有名字的结构”当成被孤立的机制：UCOPE 不自动等于付费信息，FOLR 状态所有权不等于 self-only 信息，SCDMP residual 不等于精确 semigroup，MGTAP 不等于 actor 控制分配，ACVC link loss 不等于队友离开。当前许多卡和完整 Pro 已作了这些澄清，本轮保留它们，而不是虚构它们仍声称了更强结论。

还应避免两个相反的错误。其一，全部 learner 低于 H 并不使其相互差值不可读，但限制“有实用增量”的说法；其二，只要一个代理量、参数范数、F−C 或训练曲线为正，就忽略最终强对照损失，同样不成立。FSD 的高训练回报、CRTO 的历史改善、ACVC 对 C 的增益都必须放回完整原生终点和对照集合。

**没有形成模型层面的缺陷归因。** 清单没有同任务、同输入、同工具条件下可比的模型组，也没有足以把记录错误定位为某一模型知识缺失的过程证据。实际角色名和 runtime 型号亦不能代替这种证据。我们可以指出一条错误、一个实现风险或一个过度停止理由；不能据结果不理想断言 Astra/Root/DM/Pro 普遍不懂 RL，也不能因部分答复严谨就证明不存在模型偏差。

## 四、成本、headroom 与后续顺序

### 只比较已知窗口，不把小实验或失败历史隐去

所有方向在本清单的当前 host 上，都没有匹配的调优 same-information generic／upper-reference headroom 记录。H、脚本基线、旧理论上界和 CRTO 固定 RAW 算术均不补成这两个项。缺失是诊断和排序信息，不是排除投入的门槛。各方向 MEI 保持各自单位：UCOPE/SCDMP/VSP-C1/ACVC/MGTAP 的 .01 J、FOLR 的 1 原生 episode return、RCLE 的 .05 U、FSD 的 .01 J、VSP03 的 .02 尺度、CRTO 的 .0025 原主张与 .000625 诊断尺度互不替换。〔[EXPOSURE 的各方向归因][work]；各卡及 [规范 §11.7][spec]〕

| 当前窗口 | 实际科学工作及独立单位 | 已测成本与不可相加的项 |
| --- | --- | --- |
| UCOPE P85 | 两 fit；512 train episode/fit，2,048 Adam，303,104 native steps，160 最终模式 episode；一训练对 | 完整 331.58 s；focused 7.61 s 分列；CPU 未测。P77–P85 的 3,042.26 s/九对象是不同问题的历史窗口，不是九次同实验 |
| FOLR B01 | 两 fit，各 5,000 episode/4,969更新；201,280 native ticks、64最终 episode；一训练对 | arm wall 770.69+746.89=1,517.58 s，CPU 1,518.71 s；checks/readback 后 charge 1,531.0133944 s；critical path 1,625 s 另列 |
| RCLE B03 | W1 200真实更新、16,896总 episode；W100前缀未知；零完整配对结果、一个完整W1臂 | workers 132.44 s、chain 132.54 s；已记 charge 155.787568 s，保守160 s；CPU未知。不能除以零个配对结果得到效率 |
| SCDMP residual B01 | 两 fit×512训练 episode/1,024 Adam；286,720 steps，96最终 episode；一对 | 完整323.02 s、CPU321.77 s；focused10.44 s、synthetic smoke4.21 s分列，合成动作不是native结果 |
| FSD P72 | 80,000存储训练步、32,000评价步、50,040实际optimizer调用；两个训练起点，另有评价模型 | wall1,768.78 s、CPU7,016.85 s、critical1,911 s；四计算线程使CPU可大于wall。两对窗口wall3,462.16 s/CPU13,739.12 s，不能套用别的单线程规定 |
| VSP-C1 B13 | 两fit×768episode/1,536Adam；417,792 steps、96最终episode；一对 | 完整477.99 s；focused6.2284523 s另列；CPU未测，不与旧512/768窗口混算 |
| VSP03 P76 | 一个G，16,384训练episode、128更新；加四模式共20,480episode/819,200ticks | 完整4.191728 s、unit CPU3.500596 s；其他seed及失败分配不隐去，也不当本次计时 |
| ACVC B02 | 两fit×512episode/1,024Adam；294,912steps，128最终episode | result357.55 s，checks5.4396806 s，总charge362.9896806 s；两实例charge736.3966541 s；CPU未测 |
| MGTAP P75 | 两训练对、四fit，573,440steps/4,096Adam，192最终episode | native353.71+368.12 s及aggregate .81 s，共722.64 s；critical899.39566469 s；CPU/RSS未测 |
| CRTO B08 | 774 gate更新/24,768例，另100 predictor更新/12,800例；96读数只16身份 | 全调用169 s；各臂139.1011/137.735/138.2389 s含共享费用，不求和为机器wall；CPU未测 |

这些数字来自各方向 E0/intake 与 [机械曝光归因][work]；完整全历史科学、工程和代理成本均未知。本轮未运行统计脚本、训练、回放、profiling 或环境，新增科学暴露为零。调用 wall、study critical path、checks 和 aggregate CPU 按各自边界保留，不用 cap 倍数、native/C++ 名字或 GPU 配置宣称加速。〔[runtime 一般要求§1–3][runtime]〕

### 后续是问题准备次序，不是新的调用队列

**先完成不增加实验的纠正。** Root 在后续正常 intake 中修正 RCLE 当前状态和 CRTO 索引字样；将本报告中需要降低解释强度的句子附在相应旧记录旁。原 DM/CM 处理 CRTO 的未触发 guard 风险及 RCLE 的真实缺失依赖。不要为这两条事实开一项十方向普查，也不要删除旧产物或把每个警告变成一个新 A。

**第一组准备：UCOPE、FOLR。** UCOPE 已有与实际 loss/clip 路径相连的 normalized/raw G 问题，宜先把尚未选择的具体比较补完整；现有331.58秒只是原P85参考，不是新方案时长。FOLR有一个反向但可解释的完整训练对，原建议的独立训练比较直接回答重复性；已测约1,518秒显示其成本明显不是VSP03那样的几秒。两者无需先做完整原因审计，也不互为资格前置。

**第二组准备：RCLE 的可恢复配对问题，以及有明确优先价值时的 VSP03 原节点复议。** RCLE首先缺的是比较产物和受控运行风险，不是更多梯度推演；前缀未知使任何后续不能宣称原W100已完整计费或未执行。VSP03是十项中再次同配置训练的直接计算成本最低、又有两个真实正点的停止争议，但它仍是当前暂停包，只能把这份价值意见返回原节点，不能据此直接启动第四次。

**其余维持现时边界。** SCDMP的小正点可作为未来重复性问题的理由，目前不自动追加；FSD、VSP-C1、ACVC、MGTAP、CRTO按各节说明保持具名停止。重入条件是一个具体、能改变决策的比较或对重复性的重新估价，不是事先证明成功。其作用、信息和对照必须清楚，但不要求独特机制证明或全新架构。任何改变旧margin、host、控制器或支持的提案都须明确说是新问题。

以上顺序仅是本 Portfolio 节点的待整合建议，不变更当前 HIGH/MEDIUM/LOW。SCDMP、ACVC 的第二次 recast／争用时最低排序保持；UCOPE、VSP03已记次数也不重算。科学回报的有效性先判断，排序再考虑已有成本与授权；不为凑满五个工作链制造研究。当前各方向运行额度均不因本报告恢复。

## 五、读取范围、版本和仍不能核验的部分

本轮使用 GitHub 连接器，按 TASK 的逐文件固定 SHA 读取。没有用默认分支、新方法版本源码、其他 conversation 的旧结果或外部检索替代本轮输入。基础知识只在 `d89be7656d367ca10f75ca1185797081b5d722fa` 使用；结果装配主要来自 `05b17ef2388c355579e4251facc7f57c26b3c837`；完整历史 Pro 文件读取于 `eab10bfc8854171e5a5c6ca5c93d25267223a489`，不跟随其文内未列明链接。实际链接在各节及本节给出，均携带完整版本。

### 实际主要阅读清单

| 范围 | 实际读取内容与限制 |
| --- | --- |
| 本轮 task/index/question/exposure | 固定 TASK 分段读到全部授权和各路径映射；`EVIDENCE_INDEX.md` 用于十方向定位；`REVIEW_QUESTION.md`全文；`EXPOSURE.json`各方向工作/成本归因段。未把 index 当作源码或原答替代 |
| 方法及基础 | `FOUNDATIONS.md`和`topic-notes/01_RL.md`、`02_MARL.md`、`03_HIERARCHY_ASYNC.md`、`04_EMPIRICAL.md`；证据规范相关正文及§11.8–11.10；AGENTS第1–145、210–380行；ENGINEERING_SCOPE第1–115行；MARL_RUNTIME第1–67行。不是全部规范的逐句审计 |
| UCOPE | P85卡、P85结果；P85后完整Pro实质选择/normalization及解释段；P83 intake第105–240行、P84 intake第163–260行。snapshot study第1–230行，learner/policy/environment对应函数及全文返回；native uav_env第205–408行、env_adapter第150–282行 |
| FOLR | 科学卡、完整结果，intake第120行以后的解释/后续段；P78 Pro公共协议、原source局限、比较选择和成本段；environment/model/learner/collection；native_env第1–250行。attention、mixer全部依赖未独立复核 |
| RCLE | actor100卡、B03 study；905be66c…最终科学intake；post-A02 Pro的实际诊断表、反证、权重选择与备选。不是对旧所有模型/宿主依赖重做审计 |
| SCDMP | residual卡、实际residual learner、完整intake、原held-residual Pro的定义/选择/边界；该版本共同learner全文、environment第1–80行 |
| FSD | individual-renewal B02卡、P72 E0、P74 Pro的比较/反证/停止理由；runner第1–390行。未进入完整 hmasd D2内层及全部buffer源码 |
| VSP-C1 | native B13卡、结果，post-B13 Pro的旧预算数据/容量解释/停止段；critic、value_normalization、study第1–290行、对应共同learner全文；共用已读SCDMP版本环境快照 |
| VSP03 | P76卡、完整intake；post-B05 Pro实质正文及最终边界；b02第1–207行、b01第135–186行、b03评价代码。未重新读取逐世界原始数据 |
| ACVC | native-link-loss B02卡、intake及post-B02 Pro的两实例/信息/停止论证；binding/model/learner/report。未读取冻结DENSE权重tensor或重放轨迹 |
| MGTAP | native-ground-geometry B01卡、P75 intake、post-B01 Pro的结果/pooling/选择/重入论证；geometry全文和runner第1–270行，采用TASK允许的共同environment快照；该执行版完整依赖及learner另一blob未全部复核 |
| CRTO | native-cost卡相关全文段、P71 intake的实际结果/曝光/解释、post-B08 Pro实质正文；experiment第1–285行的loss、train_path、paired_contrast和reading。未递归读取历史prepare、全部native标签生成或原始411KB结果 |
| 当前状态 | `PORTFOLIO.md`当前头部、十方向行和相关成本段；Issue16正文和评论集合实际可读。准备交付时没有本轮既有评论/响应文件；Issue时间字段不被冒充本轮读取时刻 |

本报告引用的长 Pro 文本阅读重心是实质选择、推理、反证和边界，部分文末长来源表、历史成本尾段未逐行重读；没有声称完整原答内的每个引用也已核验。所有实际请求的文件窗口均返回，无妨碍以上有限判断的连接器或指定窗口访问缺口；**未选择读取的其余允许路径，不等于不可访问，也不等于已审阅。**

共享源码特别遵循 TASK 的实际 snapshot 路径，而非只按原始文件名合并版本：

- UCOPE P85使用 `baea9644805275c62325f0a99e4cdd2f92b358d1` 的study、`3f40f56ffbab1a334589640c4a0dff799b752b93` 的learner、`28e98a47256f10a60f085cc9d97d7b8ba9a4183c` 的policy；它们的snapshot链接版本为装配 `9d984bc…`，对应执行版本是卡所列 `52bf50a…`。
- SCDMP共同learner为 `766c48a860b39e93216e2969bf3d045e55465e28`；VSP-C1为 `09a4c1cb832f5968d5de5b4ba562294fcc8640fb`，没有把它们与P85或MGTAP另一个learner blob视为相同。
- 共同environment读取 `4b59281bfb76245dd3283fe860327e35463c2b26` 及 `e6eace082a635237931375856d8fab562c22e28e` 两版，按TASK分别归属。逐字节对应是清单提供的出处，本节点没有执行hash或Git对象重建来独立证明映射。

仍不能从本轮材料确定：RCLE W100实际训练前缀和崩溃根因；各神经方法在更充分优化下的极限；critic尺度、稀疏gate、共享梯度等是否是各次结果的唯一原因；新seed总体性能；各host调优headroom；未读深层依赖的全部正确性和全部历史成本。没有这些更强结论，不阻止保留现有可信B事实；有具体主要测量缺口，也不能因想推进而猜造一个完整结果。

**最终判断：当前最需要修正的是事实归属与推断强度，而不是把失败全部归于模型、把正值全部升级为创新，或再加一套“先证明实验值得做”的前置。保留每个已读实验的真实得失、RCLE的真实缺失，以及停止决定中诚实的价值分歧；让下一次被另行选择的观察回答一个仍未被回答的问题。**

## 固定来源链接

[task]: https://github.com/CartmanFatass/My-paper-code/blob/c18cbc6ae64603f2a70e2474c9ddf9d13c8aaedb/docs/research/portfolio/pro_packets/20260909_foundations_special_review/TASK.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/d89be7656d367ca10f75ca1185797081b5d722fa/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[found]: https://github.com/CartmanFatass/My-paper-code/blob/d89be7656d367ca10f75ca1185797081b5d722fa/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[rl]: https://github.com/CartmanFatass/My-paper-code/blob/d89be7656d367ca10f75ca1185797081b5d722fa/docs/rl-marl-foundations-20260907/topic-notes/01_RL.md
[marl]: https://github.com/CartmanFatass/My-paper-code/blob/d89be7656d367ca10f75ca1185797081b5d722fa/docs/rl-marl-foundations-20260907/topic-notes/02_MARL.md
[hier]: https://github.com/CartmanFatass/My-paper-code/blob/d89be7656d367ca10f75ca1185797081b5d722fa/docs/rl-marl-foundations-20260907/topic-notes/03_HIERARCHY_ASYNC.md
[emp]: https://github.com/CartmanFatass/My-paper-code/blob/d89be7656d367ca10f75ca1185797081b5d722fa/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[portfolio]: https://github.com/CartmanFatass/My-paper-code/blob/9d984bc7544707a7452e1146a8100d0e567458b4/docs/research/portfolio/PORTFOLIO.md
[work]: https://github.com/CartmanFatass/My-paper-code/blob/9d984bc7544707a7452e1146a8100d0e567458b4/docs/research/portfolio/pro_packets/20260909_foundations_special_review/EXPOSURE.json
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/d89be7656d367ca10f75ca1185797081b5d722fa/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[u-card]: https://github.com/CartmanFatass/My-paper-code/blob/52bf50a089d3389d9fada0b531e4f4e56e83f9b8/docs/research/candidates/ucope/UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_SCIENCE_CARD_20260909.md
[u-result]: https://github.com/CartmanFatass/My-paper-code/blob/05b17ef2388c355579e4251facc7f57c26b3c837/docs/research/candidates/ucope/UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_P85_RESULT_EVIDENCE_20260909.md
[u-pro]: https://github.com/CartmanFatass/My-paper-code/blob/eab10bfc8854171e5a5c6ca5c93d25267223a489/docs/research/candidates/ucope/pro_packets/20260909_post_mean_velocity_b01_convergence/archive/RESPONSE.md
[u83]: https://github.com/CartmanFatass/My-paper-code/blob/eab10bfc8854171e5a5c6ca5c93d25267223a489/docs/research/candidates/ucope/UCOPE_UAV_SHORT_FIXED_RENEWAL_B02_P83_INTAKE_20260909.md
[u84]: https://github.com/CartmanFatass/My-paper-code/blob/eab10bfc8854171e5a5c6ca5c93d25267223a489/docs/research/candidates/ucope/UCOPE_UAV_SHORT_FIXED_RENEWAL_B03_P84_INTAKE_20260909.md
[u-policy]: https://github.com/CartmanFatass/My-paper-code/blob/9d984bc7544707a7452e1146a8100d0e567458b4/docs/research/portfolio/pro_packets/20260909_foundations_special_review/source_snapshots/28e98a47256f10a60f085cc9d97d7b8ba9a4183c/experiments/candidates/ucope/uav_motion_prefix_b01/policy.py
[u-env]: https://github.com/CartmanFatass/My-paper-code/blob/9d984bc7544707a7452e1146a8100d0e567458b4/docs/research/portfolio/pro_packets/20260909_foundations_special_review/source_snapshots/4b59281bfb76245dd3283fe860327e35463c2b26/experiments/candidates/ucope/uav_motion_prefix_b01/environment.py
[u-learner]: https://github.com/CartmanFatass/My-paper-code/blob/9d984bc7544707a7452e1146a8100d0e567458b4/docs/research/portfolio/pro_packets/20260909_foundations_special_review/source_snapshots/3f40f56ffbab1a334589640c4a0dff799b752b93/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py
[native]: https://github.com/CartmanFatass/My-paper-code/blob/52bf50a089d3389d9fada0b531e4f4e56e83f9b8/envs/pettingzoo/uav_env.py
[adapter]: https://github.com/CartmanFatass/My-paper-code/blob/52bf50a089d3389d9fada0b531e4f4e56e83f9b8/envs/pettingzoo/env_adapter.py
[fo-card]: https://github.com/CartmanFatass/My-paper-code/blob/387a40f3f1c15ba0ddc4c59d9245ff2b47bc2358/docs/research/candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B01_SCIENCE_CARD_20260909.md
[fo-result]: https://github.com/CartmanFatass/My-paper-code/blob/05b17ef2388c355579e4251facc7f57c26b3c837/docs/research/candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B01_RESULT_EVIDENCE_20260909.md
[fo-intake]: https://github.com/CartmanFatass/My-paper-code/blob/05b17ef2388c355579e4251facc7f57c26b3c837/docs/research/candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B01_INTAKE_20260909.md
[fo-pro]: https://github.com/CartmanFatass/My-paper-code/blob/eab10bfc8854171e5a5c6ca5c93d25267223a489/docs/research/candidates/vap_folr_core/pro_packets/20260909_p78_public_lifecycle_convergence/archive/RESPONSE.md
[fo-env]: https://github.com/CartmanFatass/My-paper-code/blob/387a40f3f1c15ba0ddc4c59d9245ff2b47bc2358/experiments/candidates/vap_folr_core/public_lifecycle_b01/environment.py
[fo-model]: https://github.com/CartmanFatass/My-paper-code/blob/387a40f3f1c15ba0ddc4c59d9245ff2b47bc2358/experiments/candidates/vap_folr_core/public_lifecycle_b01/model.py
[fo-learner]: https://github.com/CartmanFatass/My-paper-code/blob/387a40f3f1c15ba0ddc4c59d9245ff2b47bc2358/experiments/candidates/vap_folr_core/public_lifecycle_b01/learner.py
[fo-collection]: https://github.com/CartmanFatass/My-paper-code/blob/387a40f3f1c15ba0ddc4c59d9245ff2b47bc2358/experiments/candidates/vap_folr_core/public_lifecycle_b01/collection.py
[fo-native]: https://github.com/CartmanFatass/My-paper-code/blob/387a40f3f1c15ba0ddc4c59d9245ff2b47bc2358/experiments/candidates/vap_folr_core/public_lifecycle_b01/native_env.py
[rc-card]: https://github.com/CartmanFatass/My-paper-code/blob/ad2fdfb854e295d6d9dddb229dd17cde58465919/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B03_ACTOR100_SCIENCE_CARD_20260909.md
[rc-code]: https://github.com/CartmanFatass/My-paper-code/blob/ad2fdfb854e295d6d9dddb229dd17cde58465919/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b03/study.py
[rc-intake]: https://github.com/CartmanFatass/My-paper-code/blob/905be66c868ae2840a10243e0696bcd674127f3a/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B03_ACTOR100_RESULT_INTAKE_20260909.md
[rc-pro]: https://github.com/CartmanFatass/My-paper-code/blob/eab10bfc8854171e5a5c6ca5c93d25267223a489/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260909_post_a02_innovator_recovery/archive/RESPONSE.md
[sc-card]: https://github.com/CartmanFatass/My-paper-code/blob/7d0fc9d0091e046617493a1b23bbbf07297821cf/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_SCIENCE_CARD_20260909.md
[sc-code]: https://github.com/CartmanFatass/My-paper-code/blob/7d0fc9d0091e046617493a1b23bbbf07297821cf/experiments/candidates/scdmp_variable_k/native_hold_residual_b01/learner.py
[sc-intake]: https://github.com/CartmanFatass/My-paper-code/blob/05b17ef2388c355579e4251facc7f57c26b3c837/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_INTAKE_20260909.md
[sc-pro]: https://github.com/CartmanFatass/My-paper-code/blob/eab10bfc8854171e5a5c6ca5c93d25267223a489/docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260908_held_residual_context_repair/archive/RESPONSE.md
[sc-base]: https://github.com/CartmanFatass/My-paper-code/blob/9d984bc7544707a7452e1146a8100d0e567458b4/docs/research/portfolio/pro_packets/20260909_foundations_special_review/source_snapshots/766c48a860b39e93216e2969bf3d045e55465e28/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py
[sc-env]: https://github.com/CartmanFatass/My-paper-code/blob/9d984bc7544707a7452e1146a8100d0e567458b4/docs/research/portfolio/pro_packets/20260909_foundations_special_review/source_snapshots/e6eace082a635237931375856d8fab562c22e28e/experiments/candidates/ucope/uav_motion_prefix_b01/environment.py
[fs-card]: https://github.com/CartmanFatass/My-paper-code/blob/08199a932671d9bacdbe4eb0bfebab38c37fca1f/docs/research/candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B02_SCIENCE_CARD_20260908.md
[fs-run]: https://github.com/CartmanFatass/My-paper-code/blob/08199a932671d9bacdbe4eb0bfebab38c37fca1f/scripts/run_fsd_uav_individual_renewal_b01.py
[fs-result]: https://github.com/CartmanFatass/My-paper-code/blob/05b17ef2388c355579e4251facc7f57c26b3c837/docs/research/candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_RESULT_EVIDENCE_20260909.md
[fs-pro]: https://github.com/CartmanFatass/My-paper-code/blob/eab10bfc8854171e5a5c6ca5c93d25267223a489/docs/research/candidates/flexible_skill_duration/pro_packets/20260909_p74_post_uav_b02_convergence/archive/RESPONSE.md
[c1-card]: https://github.com/CartmanFatass/My-paper-code/blob/23ebb0f5e22286d9ea77a145f980bedacc32d9da/docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B13_SCIENCE_CARD_20260909.md
[c1-critic]: https://github.com/CartmanFatass/My-paper-code/blob/23ebb0f5e22286d9ea77a145f980bedacc32d9da/experiments/candidates/vsp_c1/native_hold_value_b01/critic.py
[c1-norm]: https://github.com/CartmanFatass/My-paper-code/blob/23ebb0f5e22286d9ea77a145f980bedacc32d9da/experiments/candidates/vsp_c1/native_hold_value_b03/value_normalization.py
[c1-study]: https://github.com/CartmanFatass/My-paper-code/blob/23ebb0f5e22286d9ea77a145f980bedacc32d9da/experiments/candidates/vsp_c1/native_hold_value_b01/study.py
[c1-base]: https://github.com/CartmanFatass/My-paper-code/blob/9d984bc7544707a7452e1146a8100d0e567458b4/docs/research/portfolio/pro_packets/20260909_foundations_special_review/source_snapshots/09a4c1cb832f5968d5de5b4ba562294fcc8640fb/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py
[c1-result]: https://github.com/CartmanFatass/My-paper-code/blob/05b17ef2388c355579e4251facc7f57c26b3c837/docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B13_RESULT_EVIDENCE_20260909.md
[c1-pro]: https://github.com/CartmanFatass/My-paper-code/blob/eab10bfc8854171e5a5c6ca5c93d25267223a489/docs/research/candidates/vsp_c1/pro_packets/20260909_native_hold_value_post_b13_convergence/archive/RESPONSE.md
[v3-card]: https://github.com/CartmanFatass/My-paper-code/blob/32ce8a7355b86bee64956e3d24b76d01c31a8d77/docs/research/candidates/vsp_03/VSP03_B05_P76_SCIENCE_CARD_20260909.md
[v3-code]: https://github.com/CartmanFatass/My-paper-code/blob/32ce8a7355b86bee64956e3d24b76d01c31a8d77/experiments/candidates/vsp_03/vsp03_b02/b02.py
[v3-base]: https://github.com/CartmanFatass/My-paper-code/blob/32ce8a7355b86bee64956e3d24b76d01c31a8d77/experiments/candidates/vsp_03/vsp03_b01/b01.py
[v3-greedy]: https://github.com/CartmanFatass/My-paper-code/blob/32ce8a7355b86bee64956e3d24b76d01c31a8d77/experiments/candidates/vsp_03/vsp03_b03/b03.py
[v3-intake]: https://github.com/CartmanFatass/My-paper-code/blob/05b17ef2388c355579e4251facc7f57c26b3c837/docs/research/candidates/vsp_03/VSP03_B05_P76_INTAKE_20260909.md
[v3-pro]: https://github.com/CartmanFatass/My-paper-code/blob/eab10bfc8854171e5a5c6ca5c93d25267223a489/docs/research/candidates/vsp_03/pro_packets/20260909_post_b05_convergence/archive/RESPONSE.md
[ac-card]: https://github.com/CartmanFatass/My-paper-code/blob/4e019ca35b930c2216fdfe110ba587e222ca7384/docs/research/candidates/acvc/ACVC_NATIVE_LINK_LOSS_B02_SCIENCE_CARD_20260909.md
[ac-binding]: https://github.com/CartmanFatass/My-paper-code/blob/4e019ca35b930c2216fdfe110ba587e222ca7384/experiments/candidates/acvc/native_link_loss_b01/binding.py
[ac-model]: https://github.com/CartmanFatass/My-paper-code/blob/4e019ca35b930c2216fdfe110ba587e222ca7384/experiments/candidates/acvc/native_link_loss_b01/model.py
[ac-learner]: https://github.com/CartmanFatass/My-paper-code/blob/4e019ca35b930c2216fdfe110ba587e222ca7384/experiments/candidates/acvc/native_link_loss_b01/learner.py
[ac-report]: https://github.com/CartmanFatass/My-paper-code/blob/4e019ca35b930c2216fdfe110ba587e222ca7384/experiments/candidates/acvc/native_link_loss_b01/report.py
[ac-intake]: https://github.com/CartmanFatass/My-paper-code/blob/05b17ef2388c355579e4251facc7f57c26b3c837/docs/research/candidates/acvc/ACVC_NATIVE_LINK_LOSS_B02_INTAKE_20260909.md
[ac-pro]: https://github.com/CartmanFatass/My-paper-code/blob/eab10bfc8854171e5a5c6ca5c93d25267223a489/docs/research/candidates/acvc/pro_packets/20260909_native_link_loss_followup_convergence/archive/RESPONSE.md
[mg-card]: https://github.com/CartmanFatass/My-paper-code/blob/4f65eefb1b15e44b42d694376630fba0c230cc6c/docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_SCIENCE_CARD_20260908.md
[mg-code]: https://github.com/CartmanFatass/My-paper-code/blob/4f65eefb1b15e44b42d694376630fba0c230cc6c/experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/geometry.py
[mg-run]: https://github.com/CartmanFatass/My-paper-code/blob/4f65eefb1b15e44b42d694376630fba0c230cc6c/experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/runner.py
[mg-intake]: https://github.com/CartmanFatass/My-paper-code/blob/05b17ef2388c355579e4251facc7f57c26b3c837/docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_INTAKE_20260909.md
[mg-pro]: https://github.com/CartmanFatass/My-paper-code/blob/eab10bfc8854171e5a5c6ca5c93d25267223a489/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260909_post_b01_convergence/archive/RESPONSE.md
[cr-card]: https://github.com/CartmanFatass/My-paper-code/blob/d9f643b761d57584de313b1f837d6c2c0becc931/docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_B08_SCIENCE_CARD_20260908.md
[cr-code]: https://github.com/CartmanFatass/My-paper-code/blob/d9f643b761d57584de313b1f837d6c2c0becc931/experiments/candidates/commitment_residual_triggered_options/native_cost_b08/experiment.py
[cr-intake]: https://github.com/CartmanFatass/My-paper-code/blob/05b17ef2388c355579e4251facc7f57c26b3c837/docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_B08_P71_INTAKE_20260908.md
[cr-pro]: https://github.com/CartmanFatass/My-paper-code/blob/eab10bfc8854171e5a5c6ca5c93d25267223a489/docs/research/candidates/commitment_residual_triggered_options/pro_packets/20260908_post_b08_convergence/archive/RESPONSE.md

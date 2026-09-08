**决定：在方向层开放“原生开局持有条件下的中央价值参数化”这一窄家族，选择一个 VSPC1-NATIVE-HOLD-VALUE-B01，证据类别仅为 B/EXPLORE。只比较 GATED-V 与完整 MLP-V，两臂保留完全相同的时长可选演员和逐智能体复合 PPO；新配对训练种子仅 8101，每臂 512 个完整训练回合、1,024 次 Adam，最终各 32 个采样评价回合，另在同 32 个布局上评价一次零速度 H。完整上限为 1,800 秒/臂、3,600 秒/对，不增加其他臂、种子、检查点或科学调用。** 这是新对象的科学选择与可写卡范围，不是代码接受、实验启动、正式 UAV 进入认定、C 冻结或 Portfolio 动作。服务分配对象的停止和更早家族边界保持不变。[候选，§§2–4][proposal]；[当前授权，Five-item assignment][assignment]

最强理由是可以回答一个实际的学习器选择，而不需要改变演员的权限或任务：在持有中的队友仍影响运动、服务和后续局部观测时，对已经合法可见的剩余持有量显式作乘性条件化，是否比完整通用价值网络带来值得保留的全回合原生收益？收益或损害将决定这个门控价值包是否值得一到两个独立训练对的后续，或直接保留 MLP-V、停止推进该包。这里不是用价值网络替演员选时长，而是比较同一实际 PPO 训练器中的两种中央基线参数化。源码给出了基线到优势、联合梯度裁剪、演员更新和原生回报的具体路径；这使所选观察有用途，但并不预先证明门控有益。[learner.py，collect_episode、update][learner]；[policy.py，Critic、joint_terms][policy]

**最强反对意见是门的直接作用极稀疏，而且与本轮开局时长选择不在同一信息时点。** 每回合至多三个原始行有非零剩余持有量；完整 MLP 本来就能利用这些输入。即使出现正回报差，也可能主要来自新增容量、价值优化或联合裁剪改变了演员步长，而不是独立的跨时长共享收益。我不以“代码已存在”“每次门计算很少”或历史正例压过这个反对意见。仍选择一次有限 B，是因为同起点、同信息、同演员的直接比较能决定是否保留这一具体训练包；不要求这一次同时判明收益的唯一原因。**若它只能通过加入刚选时长、强制长持有或改成另一个事件才能显效，那不是本对象的修补空间。**[候选，§§2–3、6][proposal]；[证据规范，§§11.8–11.9][spec]

## 一、此次究竟比较什么：先保留信息时点和真实消费者

源码证据使用候选明确列出的实现版本 `6374063408208ba67b8cb7c69ebc0babb0f00259`。文档、结果 intake 与规范使用本轮固定输入版本 `14c3cdb9f2677539b4fd4b34f169e2c7e635d04d`。下列为实际读取的源代码事实，不是新运行结果。

宿主是现有 MultiUAVEnv 与 ParallelToArrayAdapter：五架持续存在的 UAV、50 个均匀布局用户、256 个一秒步、1000 米区域、高度 50–150 米、每坐标最大速度 30 米/秒，使用既有 free-space/vectorized 路径，不引入 shadowing、FDMA、paper reward 或玩具替代环境。归一化速度先更新位置并作物理边界截断，随后计算信道、连接、原生奖励和新观测。五个成员共享演员权重，各保留自己的循环状态；没有 roster 变化。[environment.py，make_real][environment]；[uav_env.py，step，L265–351][native]

| 边界 | 所读实现及本对象保留的含义 |
| --- | --- |
| 演员输入 | 104 个既有局部值：自身位置、20 个局部用户槽、10 个局部 UAV 槽和原始时间；再接自身上一归一化命令 xyz、剩余持有量/4，合计 108。局部槽按 SINR 排序，不是持久实体身份；全局状态和源索引诊断不送入演员。 |
| 中央价值输入 | 已有 116 个全局状态值，接五组上一命令 xyz 与 remaining/4，合计 136。全局位置按原代码归一化，不追加演员隐藏态、未来观测或当前尚未选出的动作。 |
| 决策与持有 | 每个 UAV 只在 t=0 选择 d=1 或 4，并在可行动时采样三坐标 tanh-Gaussian 命令。d=4 保持开局命令至 t=3，t=4 起所有成员都恢复普通反馈；d=1 从 t=1 起可反馈。持有中仍逐步接收观测并更新 GRU。 |
| 价值时点 | cx 和价值都在当前采样之前组装。t=0 的五个 remaining 全是零；d=4 对应后续 t=1、2、3 的剩余量 3、2、1。t≥4 又全为零。不能将刚选出的 duration 回填到同一决策的基线中。 |
| 原生信用 | 完整回合的实际 team reward 作 gamma=1 的 return-to-go；减收集时价值后，在两回合共 512 个原始行上统一归一化并 detach。没有 duration-Q、GAE、终局 bootstrap 或未执行时长样本。 |

输入和时点依据 [environment.py，actor_features、critic_features、HoldState，L27–74][environment]、[learner.py，collect_episode，L29–155][learner]；局部排序依据 [uav_env.py，L382–433、L575–589][native]；adapter 的真实状态来源和返回字段依据 [env_adapter.py，reset、step、_state_array][adapter]。

实际学习路径需要再说清两点。第一，四个 epoch 共用一次计算好的 detach 优势；本 epoch 更新 critic 并不会立即重算该 rollout 的优势。价值变化通常通过后续收集值影响后续优势。第二，演员和 critic 的梯度一起裁剪到总范数 0.5，因此门参数的梯度还可能在当前优化步就改变演员梯度的共同缩放。即使 A=0 时两臂初始价值相同，也不能声称首个优化步的演员更新必然相同。[learner.py，update，L179–212][learner]

若某行所有 UAV 都在持有，逐智能体 PPO 的演员项为零；该行仍进入价值损失、循环序列、原生 return-to-go 和 512 行优势归一化。若只部分成员持有，其他实际决策仍使用共同标量优势。由此推论，少量非零 r 行可能通过归一化、共享权重更新和联合裁剪影响更广的训练轨迹；**3/256 是直接门输入的稀疏度，不是完整回报效应的上界。** 反过来，这也使“改善专属持有信用”不能由一个正终点独立证明。[learner.py，clipped_policy_loss、recurrent_outputs、update][learner]

这条路径是“过去的命令/持有及当前原生状态 → 中央价值基线与联合优化 → 局部循环演员的参数 → 后续合法运动和服务”。它不同于旧队列 Q 值直接选站点，也不同于 UCOPE 改演员行动支持或 FSD 改续约执行。源代码足以支持这个窄比较；不需要另改演员、观测、事件或宿主才能让比较在语义上成立。

## 二、确定的两个训练包：完整 MLP 不削弱

用原 136 维输入中的五个 remaining/4 字段组成 r；其余 131 个原生状态及旧命令字段组成 x。按现有数组的零基编号，r 位于 119、123、127、131、135；这是从 critic_features 的五个四值块直接推得的索引，不是新增信息。保持每个字段与原第一层列的对应关系。[environment.py，critic_features，L32–39][environment]

令 z=W_x x+b1，B 为原第一层中这五列的权重，选择且仅选择：

- MLP-V：h1=tanh(z+B r)。
- GATED-V：h1=tanh(z⊙(1+A r)+B r)。
- 两臂后续均为 V=W3 tanh(W2 h1+b2)+b3，宽度与原 128→128→1 相同；A 是无偏置的 5→128 映射，初始全零。

MLP-V 必须保留原始 136→128→128→1 的完整非线性函数及全部输入，不能改成无时长网络、表格、较窄网络或拆掉原 B r。两臂每个共同参数从同一初始化副本复制；默认层初始化沿用原 templates 的 actor-then-critic 顺序，不改成另一套初始化。两边都装同一个初始为零的二分类 duration head，优化器和可变模型存储彼此独立。零门不需要新的随机抽样。[policy.py，Actor、Critic、templates、arm_copy，L10–49][policy]；[候选，§3][proposal]

机器算术给出：两演员各 32,264 参数；MLP critic 34,177，GATED critic 34,817；完整 learner 分别 66,441 与 67,081。新增 640 参数约为通用 critic 的 1.87%、完整通用 learner 的 0.96%。A=0 在数学上包含原通用函数，**包含关系不保证有限优化中不劣**。新增容量、梯度和数值计算路径都属于处理包，不能用“同初始化”抹去。[准备事实，proposed_parameters][facts]

这里仅需对字段映射、共同参数对应及 A=0 的普通 FP32 输出做聚焦检查，不要求科学意义上的逐位同一、精确包含证明或全支持枚举。r=0 时门的直接贡献与 A 的该行导数为零；但训练后两臂共同权重已经可能不同，因此不能把后续 r=0 的价值差都归为实现错误。也不增加“等参数无门”“分离裁剪”第三学习臂来完成本次未请求的归因研究。

源码复用不能只是把原 study 的 T/G 改名：其原 arm_copy 只给 T 装 duration head，默认 learner 路径又可能采用 joint ratio。这个新对象两臂都必须保留 duration head，并显式共同采用 agent_compound。旧 G 的无 duration 策略、旧两种子 aggregate 及其主量不能被当成新 MLP-V、强迫多跑一个 seed 或改变 n=1。所需只是 VSPC1 自有的窄 critic/study 适配，原 UCOPE 与 core 保持只读。[study.py，Config、aggregate、run_pair][study]；[policy.py，arm_copy][policy]

## 三、保留的最强正向、负向和弱基线事实

原生 UCOPE 的已测结果能说明现有接口确实承载真实学习及收益异质性，但它们比较的是旧 T 与 primitive-only G，不是本次同演员的两个 critic，也不是本次 B02 共同裁剪下的门效应。

| 既有证据 | 不改写的观测及限制 |
| --- | --- |
| 原 P21 | 原平均 T−G 为 +0.0152174206，保持当时 UP；不是新 gate 的正结果。 |
| P24 master 6901 | T−G=+0.0433518665，但 G−H=−0.0282038164；T−H=+0.0151480500。有利 T−G 与弱 G 同时成立。 |
| P24 master 6902 | T−G=−0.0503654225，T−H=−0.0332644846，G−H=+0.0171009380；完整原生损害不能由位移或局部信息变化抵消。 |
| P24 及历史四对 | 新两对平均 −0.0035067780；四对结果知情描述均值 +0.0058553213。三个正对均值与最大幅度的负对均值并存，不合成稳定优势或等价。 |

数字和原解释来自 [P24 intake，§§2–5][ucope-results]。其中 6901、6902 的前四步位移 T 都较大，却对应相反的完整回报符号；变化的局部输入、duration 使用和实际参数移动均不是收益替代终点。该 intake 保留的早期有限宿主正、零、负证据仍在各自范围，不合并到这个新原生对象。

服务分配的结果也必须保持：固定规则 J=0.785196940，高于 FACTOR=0.758911133 与 GENERIC=0.752400716；小正 Δ=+0.006510417 低于原 MEI 0.025。规则相对 FACTOR 的损失幅度虽名义越过原 MEI，但边界尚不能仅凭点估计宣布充分分辨。该对象已经按完整、结果知情补测后的读法停止；之前 GENERIC 发布失败并未被改判成功。原公开计划家族、双队列不加调用、A01 缺失 headroom 和 D6 边界都不改变。[完成 intake，§§3–5][completion]；[先前 preparation yield，Open question/limits][yield]

这些历史限制使保留 H 很重要，却不使 H 成为最优或调优过的 competent baseline。本次 MLP-V 的实际 competence 仍未知；当前没有与它的演员、裁剪、种子和预算相匹配的调优 headroom 包。缺少这个包不构成前置否决，历史的弱 G 也不证明本次 MLP-V 必然弱。[候选，§§4、6][proposal]；[证据规范，§§11.7–11.9][spec]

## 四、可写卡的训练、评价和独立单位

两臂均沿用实际 primitive-step learner，不迁入队列式段奖励或 duration-Q。演员为 Linear(108,64)/tanh/GRU64、三坐标 tanh-Gaussian 速度头和同样的 duration head；每个回合从零循环状态和零 hold 状态开始。每个两回合 rollout 共 512 团队原始行，32 步截断循环梯度使用收集的 chunk 初始状态。四个 full-rollout epoch，各一次联合 Adam：lr=3e−4、betas=(.9,.999)、eps=1e−8、无 decay/scheduler；value 系数 .5、entropy 系数 .01、PPO clip .2、联合梯度 clip .5。[learner.py，L158–212][learner]；[UCOPE B02 卡，§3][ucope-card]

每个真实 agent 决策的 log density 包括三坐标速度，且只在开局加该 agent 的 duration log probability；两者在同一 agent 的 compound ratio 内裁剪。持有成员无新的速度密度。对实际决策 mask 的各 agent surrogate 先求和，再对所有原始行求均值，不能再除以五或当前决策数。每次更新的值目标是完整回合未折扣 return-to-go，不是 J 的平均值；用于报告的 J 才除以 256。保留优势一次归一化、无 GAE/terminal bootstrap、无额外反事实转移的原义。[policy.py，joint_terms][policy]；[learner.py，returns_to_go、clipped_policy_loss、update][learner]

只选择新根种子 8101，沿用 b=100000s 的域。共同 actor/critic 初始化 b+11；各臂私有训练速度流 b+21、duration 流 b+22；训练 reset b+1000+e，e=0…511；最终评价 reset b+2000+e、私有速度和 duration 流分别 b+3000+e、b+4000+e，e=0…31。固定 H 在同 32 个 reset 上发送零速度，使用第二臂环境，不建演员或 critic，不调参。配对的是共同初始参数和外生 reset 输入；两臂不共享可变优化器、循环轨迹或训练数据，持有 mask 的变化可能改变随机流消费。因此不能宣称每个时间步的动作噪声或内生轨迹逐项相同。[准备事实，rng、seed_search][facts]；[study.py，run_pair][study]

最小独立学习单位是这一个匹配训练对，n=1。两个训练模型不是两个独立重复，五个 agent、1,024 次更新、32 个评价回合也不增加训练 n。96 个最终评价回合对应 32 个匹配 reset 组，不是 96 个独立布局。既有 UCOPE 或队列结果不并入新均值、方差或成功计数。

本对象没有外生平衡的时长分层。每回合五个开局 duration 是策略内生决策，可能长短混合；不为了增加门曝光强制 d=4，也不把 d=1 与 d=4 的事后子组差当随机时长效应。保留实际开局 duration、采样长持有频率和由已有 cx 可直接计得的非零 r 行数即可。没有新策略或 critic 调用来计数；不要求最小长持有比例或最小门位移门槛。

主测量是最终固定训练预算后的采样政策回报，不是 greedy 替换、最佳 checkpoint、critic loss 或 prefix reward：

`R_t = sum(info['rewards_dict'][agent] for the five agents)`；`J_e = sum_(t=0..255) R_t / 256`；`Delta = mean_(e=0..31)(J_GATED,e − J_MLP,e)`。

环境把全局奖励等分给五 agent，adapter 又返回一个额外平均标量；必须像原 learner 一样使用 rewards_dict 的和，不使用那个标量、不另写奖励函数。原奖励的覆盖项为 .7×连接数/50，加 .3×既有 SINR quality 均值。主结果以原奖励的 Python float/float64 累加，训练仍用 FP32。**MEI 采用绝对 .01**；一个持续多服务用户对覆盖项贡献 .7/50=.014，使 .01 有原生刻度意义，但质量项也可变化，故不能解释为必然多服务某个固定人数。[uav_env.py，_compute_reward，L1421–1484][native]；[env_adapter.py，step][adapter]；[environment.py，team_reward][environment]

同时报告三个完整回报列表及 GATED−H、MLP−H 的 32 个配对差；三项差共享数据，满足 `(GATED−H)−(MLP−H)=Delta`，不是三条独立成功。每项条件评价 SE 用对应 32 个差的样本标准差除以 sqrt(32)；它仅描述固定训练政策在这种配对采样下的评价噪声，不是训练群体不确定性。保留每臂训练记录、损失、实际参数位移、最终 checkpoint 和所有不利回合。训练回报随政策及 reset 变化，不能冒充固定政策重复评价；不新增初始评价或中间 checkpoint 来得到更好曲线。[study.py，difference_stats、primary_from_rows、run_pair][study]

## 五、工作量、完整预算和最小实现范围

主导工作是两次真实 fit，而非门的单次算术：两臂各 512×256 训练步，256 rollout×4 epoch；最终两学习臂和 H 各 32×256 步。它没有候选策略树、轨迹搜索、额外 solver、ensemble 或 counterfactual controller rollout。[准备事实，per_fit、proposed_pair、cost_law][facts]

| 计划工作 | GATED-V | MLP-V | H | 合计 |
| --- | ---: | ---: | ---: | ---: |
| 完整训练回合 | 512 | 512 | 0 | 1,024 |
| 训练团队原始步 | 131,072 | 131,072 | 0 | 262,144 |
| Adam 调用 | 1,024 | 1,024 | 0 | 2,048 |
| 最终评价回合 | 32 | 32 | 32 | 96 |
| 评价团队步 | 8,192 | 8,192 | 8,192 | 24,576 |
| 全部已评分回合 | 544 | 544 | 32 | 1,120 |
| 训练加评价团队步 | 139,264 | 139,264 | 8,192 | 286,720 |

表格是所给机器文件的前瞻算术，不是已执行量。还计两次环境构造及其两次未评分 constructor reset。每个 fit 有 2,560 次开局 duration 决策，均发生在 r=0；训练速度决策随长持有数变化，为 647,680 至 655,360。每臂收集、最终评价与四 epoch 优化合计 663,552 个 critic forward 行。GATED 每行额外有 640 个乘加及 128 个元素乘积，但没有额外 critic forward；这不是完整 FLOPs、内存或墙钟测量。[准备事实，per_fit、proposed_pair][facts]

非零 r 的训练行上限是每 fit 512×3=1,536，即 131,072 行的 1.171875%；实际数取决于是否有人采到长持有。门的有效曝光低，是我预测小效应的主要理由；它不使这次运行在计数上变成“只训练三步”，也不能据此虚构成本同比缩小。共用优化权重及规范化使影响范围可能扩大，但无证据保证这种扩大有利。

完整执行顺序选择 GATED-V 后 MLP-V；启动和共同初始化计入第一臂，H 的 8,192 步及配对发布/readback计入第二臂。第一臂 139,264 团队步，第二臂包括 H 共 147,456 步；每臂最多 1,800 秒，全对最多 3,600 秒。所有导入、构造、训练、所选评价、必要检查、文件/模型发布和退出均在完整边界内；不通过切片、改标签、暂停计时或另一臂余额重置上限。没有独立 H 补测额度、第二对或自动 retry；完整有效第一臂的正负表现不得成为是否执行第二臂的选择依据。[候选，§4][proposal]

已有 P21 同循环计划参照为约 148.2671 秒的 T 和 141.3719 秒的 G（含 H/发布），P24 两对实际完整 wall 之和 564.93 秒。前两数是历史规划参照，不是此新 fit 的测得系数；后者是旧两对观测，不含全部工程/代理成本。本对象第二臂也有 duration 演员、两臂共同用 agent_compound，GATED 增加算术与梯度；新每单位 wall、峰值内存和增量实现费仍未知。不能从640参数推出完整增量可忽略，也不必为了选择这一有上限的直接 B 先另跑成本实验。[准备事实，historical_exposure_source、cost_law][facts]；[P24 intake，§5][ucope-results]

保持现有 remote-first、CPU FP32、单科学进程/线程和真实节点逐调用资源准入，使用已有 detached supervision，不把宿主节点当估计量。命中固定计数即结束；超时、非有限学习或威胁奖励、信息、训练、主测量的具体缺陷则停止并保存可信部分。若主对完整而只缺 H 或可选遥测，分别保留 Delta、把 H 相对用途或资源声明限缩；不能以缺读回或可选诊断失败断言没有运行，也不能自动补跑。准入失败不等同可选资源遥测缺失。[AGENTS，§5][agents]；[证据规范，§§11.4、11.8.6–7][spec]

与再加一对相比，当前仅一个训练对承担训练实例不确定性的明确限制；与去掉 H 相比，一次固定 H 的 8,192 步能暴露旧记录已出现过的弱基线，值得保留。更强的精确价值解、完整政策搜索或独立因果诊断既不直接替代这个训练包的 native endpoint，也无已有低成本保证，因而不选。所放弃的是最优性、纯机制归因与稳定人口主张，而不是实际 reward、同信息比较和真实学习。[证据规范，§11.9][spec]

未来实现只需在 VSPC1 的窄 critic/study/entry 中接入上述门、正确的双 duration 演员、单对结果算术和现有计数，复用所读 native environment、actor、learner；不改 UCOPE 或 core。工程 scope §4 为 none，普通 2,000 新增非测试研究行、600 runner 行和五分钟聚焦检查边界保持。检查应覆盖输入列/预决策时点、共同初始化及零门对应、双演员和 compound mask/reduction、主量与 H 发布；无变化部分复用已有检查。至多按后来具体工程任务需要使用一次有界合成 plumbing smoke，不能将它视作 UAV 性能证据，不能在这里暗增原生调用。当前没有派工、源码接受或测试执行；选择后的卡和完整 CM 规范仍沿既有路线交回 Root，后来的工程实现比较臂不增加本卡科学臂数。[工程规范，§§3–5][engineering]；[当前授权，§4–5项][assignment]

## 六、结果将改变什么，以及工作预测

以下保留候选的边界：严格大于 .01 为 UP，严格小于 −.01 为 DOWN，恰等于边界也在 WITHIN。它们是 B 的描述性读法，不是显著性、等价性、C 晋级条件或预算自动发放规则。

| 实际观察 | 有限解释与下一研究选择 |
| --- | --- |
| Delta>.01，主比较可信 | 本实例为 gated critic 整体包的局部正向原生信号，值得考虑另选一到两个相同设置的独立训练对；不是共享的唯一因果效应，不自动追加。所有 H 差和负回合并列保留。 |
| −.01≤Delta≤.01 | 本实例未提供所选刻度的门控收益理由，保留小正、小负或零及 SE，停在该对象边界；不宣布等价，不为跨过界线延长训练或评价。 |
| Delta<−.01 | 对该门控包的同预算原生反例；此具体选择倾向 MLP-V。critic loss、长持有频率和参数移动不抵消损害，不扩大为 K4 无效。 |
| 学习器比 H 弱，尤其两者都弱 | 两学习器之间可信 Delta 仍成立，但不能称获得相对可用固定参照的控制能力。正 Delta 也不自动使重复有价值；当前更应停止自动推进门控，除非后续明确提出有用途的新问题，而非挽救正号。H 仍不是最优或调优 baseline。 |
| 采样 SE 使 MEI 附近的读法不清楚 | 同时报告点估计所属区间和条件不确定性，不把它升级为训练群体结论，不自动追加回合。 |
| 某个主依赖受损或一臂终点不完整 | 不形成该依赖的性能判断，保存独立可信的计数/回报；缺失不是负实验。只缺 H 时保留可信主对，规则相对用途未确认。 |

这些分支共同读取：primary 决定 learner 对比，H 限定实用含义；不会以 H 改写主量或事后挑最有利比较。即使一个结果值得跟进，下一对也须另行具体选择并保留每个符号。相反，阴性并不从逻辑上禁止别的真正有用途的 B；但本次没有选择改演员、强制事件、另一个宿主或搜索议程。

**工作预测：最终 Delta 落在 [−.01,.01] 的概率判断为 .65。** 完整 MLP 已能使用同样 hold 信息，显式门只在极少数原始行直接参与，且无已知原生归纳优势；这些是谨慎预期的理由，不是新测量或 calibrated probability。若完整固定主对产生 Delta>.01 或 Delta<−.01，该“WITHIN”预测在这一次不吻合，两侧都可反驳；报告条件 SE，不用它把未命中改成命中。一个概率预测的一次结果不构成概率校准。所有者预测未取得，不代写。[候选，§§3–4][proposal]

如果长持有极少、门变化小，结果只适用于这个实际自选持有暴露；不将自然低暴露当作可补做强制长持有的许可。若 Delta 大但门直接行少，同样先保留 native fact 与优化耦合替代解释，不把大差强归因于几行“信息收益”。要作更强机制主张需另有针对它的问题和证据，不作为当前 B 前置。

最接近的替代选择是维持无后继对象：极少直接行和强通用 null 可能使投入主要得到另一项优化方差观察。这不是不合法的意见，也不是因缺少 C 或 headroom 才成立。我没有选择它，是因为这次已界定在实际原生学习器中保留哪种 critic 的决策，且一次对照就可以终止这一具体包的自动推进，而不必先把问题扩成全因果研究。没有选择任何其他替代任务。

## 七、实际访问与最后的主张上限

本轮清单内 12 个文档/数据路径均成功由 GitHub 连接器在固定输入版本取回；较长规范按相关条款读取，包含完整 §§11.8–11.9。又依候选 §1 明确授权的固定链接，读取了实现版本的六个源码路径：environment.py、policy.py、learner.py、study.py，以及 native uav_env.py 的 step/state/局部观测与排序/reward 段、env_adapter.py 的 reset/step/state 段。没有沿未列出的文献、旧原始包、其他方向文件或移动 main 取证。当前零 gate 性能曝光，不能把对源码的读取写成新实现已接受或新 gate 已能改善回报。[候选，§1][proposal]；[准备事实，source_symbols、new_exposure][facts]

Issue 5 正文和七条既有评论实际读取并在写入前查重；其中[原服务分配交付](https://github.com/CartmanFatass/My-paper-code/issues/5#issuecomment-5571198932)及[其补测修订交付](https://github.com/CartmanFatass/My-paper-code/issues/5#issuecomment-5573132669)是历史，不是本轮答案。阅读阶段时钟记录为 2026-09-08 09:48:52 PDT（16:48:52 UTC）；固定快照的采集时刻是 16:36:23 UTC，二者分开。评论没有替代固定科学文件，也不扩大允许写入的范围。[固定快照][snapshot]；[GitHub 协作说明，Task and delivery scope][collaboration]

既有文献在候选 §5 中提供了对时点、实际段曝光和因果用语的限制。本次只读取该固定综述，没有独立访问其本地文库、论文全文或外部页面，未作新颖性认定。尤其此处持有期间仍有原始步观测，不能因 ACAC 的另一信息制度而更改它；UTE/VSP 也不授权未执行时长样本、值分解或唯一乘性效应结论。[候选，§5][proposal]

本咨询没有构造模型/环境、模拟、profiling、训练、评价或运行源码/测试。机器文件引用的旧 learner 相对位移 .518345–.598358 只是历史 can-move 证据，新 fit 必须由其实际调用保留自己的初始范数、位移及非零学习计数。零初始化门自己的相对位移不能除以零初范数后冒充可靠比例；保留绝对门变化以及有定义的共同/总参数变化即可，不设任意移动阈值。[准备事实，historical_exposure_source、new_exposure][facts]

**最终范围只到这一同演员、同信息、同 PPO 的 gated critic 对 full MLP critic 的单对 B，以及同布局零速度参照。它可以产生固定任务/预算中的局部原生信号或反例，不支持稳定优越、等价、严格低秩、唯一共享原因、最优性、未见时长或队伍迁移、安全/部署，亦不支持对历史 primitive-only UCOPE G 的新比较。没有修改规范、Portfolio 状态或旧对象含义。**

[proposal]: https://github.com/CartmanFatass/My-paper-code/blob/14c3cdb9f2677539b4fd4b34f169e2c7e635d04d/docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_P49_QUESTION_20260908.md
[facts]: https://github.com/CartmanFatass/My-paper-code/blob/14c3cdb9f2677539b4fd4b34f169e2c7e635d04d/docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_P49_PREPARATION_FACTS_20260908.json
[assignment]: https://github.com/CartmanFatass/My-paper-code/blob/14c3cdb9f2677539b4fd4b34f169e2c7e635d04d/docs/research/portfolio/handoffs/2026-09-08-p49-vspc1-native-value-question.md
[ucope-card]: https://github.com/CartmanFatass/My-paper-code/blob/14c3cdb9f2677539b4fd4b34f169e2c7e635d04d/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B02_SCIENCE_CARD_20260908.md
[ucope-results]: https://github.com/CartmanFatass/My-paper-code/blob/14c3cdb9f2677539b4fd4b34f169e2c7e635d04d/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_P24_INTAKE_20260907.md
[yield]: https://github.com/CartmanFatass/My-paper-code/blob/14c3cdb9f2677539b4fd4b34f169e2c7e635d04d/docs/research/candidates/vsp_c1/VSPC1_POST_SERVICE_ALLOCATION_P10_YIELD_20260907.md
[completion]: https://github.com/CartmanFatass/My-paper-code/blob/14c3cdb9f2677539b4fd4b34f169e2c7e635d04d/docs/research/candidates/vsp_c1/VSPC1_K4_SERVICE_ALLOCATION_COMPLETION_INTAKE_20260907.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/14c3cdb9f2677539b4fd4b34f169e2c7e635d04d/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/14c3cdb9f2677539b4fd4b34f169e2c7e635d04d/docs/project/ENGINEERING_SCOPE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/14c3cdb9f2677539b4fd4b34f169e2c7e635d04d/AGENTS.md
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/14c3cdb9f2677539b4fd4b34f169e2c7e635d04d/docs/research/candidates/vsp_c1/pro_packets/20260908_native_hold_value_convergence/ISSUE_SNAPSHOT.json
[collaboration]: https://github.com/CartmanFatass/My-paper-code/blob/14c3cdb9f2677539b4fd4b34f169e2c7e635d04d/docs/project/GITHUB_RESEARCH_COLLABORATION.md
[environment]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/experiments/candidates/ucope/uav_motion_prefix_b01/environment.py
[policy]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/experiments/candidates/ucope/uav_motion_prefix_b01/policy.py
[learner]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py
[study]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/experiments/candidates/ucope/uav_motion_prefix_b01/study.py
[native]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/envs/pettingzoo/uav_env.py
[adapter]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/envs/pettingzoo/env_adapter.py

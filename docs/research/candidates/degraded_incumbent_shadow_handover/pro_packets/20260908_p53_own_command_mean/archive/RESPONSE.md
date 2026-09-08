**选择一个新的 DISH-OWN-COMMAND-MEAN-B07（B/EXPLORE）：新配对种子127，OWN_COMMAND_MEAN 对 DIRECT_MEAN，两臂各十六更新，只比较各自 update16 的完整模态原生服务，并保留各臂自己的初始化模态参考。** 这使现有普通来源应用议程继续到一个具体的学习／控制参数化问题，不重开 B06 已停止的联合抽样执行支线，不选择另一学习率配对，不作整个 DISH 的 PARK、CLOSE 或 RECAST。完整新支出界为每臂1,800秒、配对合计3,600秒，包含必要检查和发布；本次只作科学选择，不实施、不运行。

选择的正面理由是：源码已经给出同一物理车辆可用的当前已施加加速度，且它在实时输入和训练片段中均可取得；把该输入直接接入均值计算，可在不增加信息、参数或动作机会的条件下，改变学习器形成普通控制的方式。新训练的同信息 DIRECT_MEAN 提供清楚的反事实比较，完整服务可以决定这条直接输入路径是否值得继续，而无需先制造一次换主。**这是假设有用的参数化偏置，不是已发现的 B06 原因、合法性修复或独特 MARL 机制。** 最强反对理由仍是网络本来就看到该输入、native 已处理施加命令的变化限制，以及延续不合适的加速度可能损害转弯和链路；这些反例正是本次有限比较要保留的可能结果。[P53 source intake §§2–5][source-intake]；[当前任务][task]；[证据规范 §§5.2、11.8–11.9][method]。

## 一、已接受结果没有变成新处理的疗效证据

前次完整决定已经停止 B06 所测试的联合高斯运动／Bernoulli 意图抽样规则的当前扩展，并在当时选择了零后继。P53 是后来明确提出的下一问题，不是把旧停止改写为从未发生，也不是要求再次裁决 B06。方向记录的最终 post-B06 段与 P53 段、已接受 intake 和实际 P53 任务共同支持这一区分。[post-B06 intake 开篇、§§4、7][post-b06]；[DIRECTION 最终两个相关章节][direction]；[P53 handoff][handoff]。

B06 的有限事实仍完整保留：同一 seed113 最终控制器的抽样减模态均值为 **−77.5 tick**，四个条件依次为 **−92.5、−41、−94、−82.5**；初始模态／最终模态／最终抽样均值为369.75／662.25／584.75。模态初末变化 **+292.5**，抽样对初始模态 **+215** 混合了学习和执行接口变化，并保留 TERRAIN/K8 的 **−57**。两条抽样轨迹分别胜出14和3，不改写两样本等权主量。全部16行各运行1,200 tick，无提前终止、无普通合法换主，首换主时刻均为 null。[post-B06 intake §§2–3][post-b06]。

原生代价同样保留：最终模态／抽样 invalid_commit 均值为 **3.5／31.875**，分别来自14次／4个 episode 与255次／8个 episode；抽样能量均值多 **4,642.6427，约1.69%**，每个条件的平均无效提交和能量均增加。训练另有 **1,030次无效提交、3次分离越界、35次终止事件**，不能用最终评价其他六类硬事件为零来覆盖它们。低置信度 `Delta_exec<=−24` 的旧预测获得符号／阈值命中，不等于精确预测−77.5或识别噪声原因。[post-B06 intake §§2–5][post-b06]。

B04／seed89 的学习率差分+182.75、LOW_LR 对自身初始化−57及 CONTROL 在tick684的提前分离终止，B05／seed101 的+236.25、LOW_LR 初末+219.75、CONTROL 初末−16.5、−277条件、209次 LOW_LR 评价无效提交和3次 CONTROL 训练换主，也都保持各自含义。两学习率配对的+209.5只是描述；B06不是第三个学习率配对，本次 B07也不是。P53源码观察没有产生任何新的参数、轨迹或性能结果。[post-B06 intake §4][post-b06]；[source intake §§1、4–5][source-intake]。

## 二、唯一处理：各物理车辆自己的原始加速度进入自己的均值

### 公式与角色／物理次序

对物理车辆 `i∈{0,1}`，以本次决策输入的 owner `o` 选择循环副本：`c_i=2i+1[i≠o]`。`m_i` 是该副本现有的两维 motion head，`a_prev,i` 是**同一决策前输入**的 `actor_raw[...,c_i,8:10]`。两臂在普通续约时分别使用：

`mu_OWN,i = 3*tanh(m_i + a_prev,i/3)`；

`mu_DIRECT,i = 3*tanh(m_i)`。

除数3与系数1固定，不学习、不调参、不扫描。这里的 `a_prev` 是车辆当前**已施加**的加速度，不是上一条未投影 raw_action，不是本步投影之后的 `s.a`，不是快照中的旧命令，也不是经过 Welford 标准化的特征。实时已有 FP32 actor tensor 与片段中的 FP32 `actor_raw` 提供该量；原 encoder／GRU 仍用原有标准化输入，不改变归一化更新法则。[trainer 267–335、482–524][trainer]；[native actor_row 304–317][native]。

| 决策输入 owner | 物理车辆0的 motion／own-input 副本 | 物理车辆1的 motion／own-input 副本 | prepare 决策副本 | commit 决策副本 |
| --- | --- | --- | --- | --- |
| 0 | 0：车辆0 incumbent | 3：车辆1 shadow | 0 | 3 |
| 1 | 1：车辆0 shadow | 2：车辆1 incumbent | 2 | 1 |

**最终 motion/raw_action 四项顺序保持物理车辆0的x、y，再物理车辆1的x、y。** `_role_policy_heads` 的 live 一维 owner 与 replay 二维 owner 分支都这样构造。不要根据现有随机字段字符串中的 OWNER／STANDBY 字样，把数组前两项改成随 owner 换位的槽；原字段名称及随机地址保持，新的 own-input 按实际物理次序配对。prepare 来自 incumbent，commit 来自 standby shadow，随后二者都序列化到 native owner 槽。这种序列化不意味着两个神经决策都由 incumbent 作出，更不意味该 actor 拥有全局证书。发生 CAS 时也不能用后继 owner 倒推重排本次已记录的动作或输入；保持原 `apply_native_promotion` 与其 owner-before 语义。[engine `_role_policy_heads` 345–383][engine]；[trainer `step_rows`、`apply_native_promotion` 287–384][trainer]。

这是 soft own-command mean，不是 delta-action 上界或精确保持器。由公式可直接看出，`m=0` 时得到 `3*tanh(a_prev/3)`，通常不是 `a_prev`；它也不能保证每个状态下变化更小。均值仍是逐分量有界，不等于二维向量范数已满足 native 限制。训练仍在相应均值外加原学习高斯噪声；不对随机 latent 作 tanh，不截断或重抽样 raw action。非续约维持现有物理命令和零新意图，循环状态仍按原法推进。[source intake §3][source-intake]；[trainer 308–335][trainer]。

### 保留信息集，不把原宿主说成更强的去中心化系统

新直连只使用 own acceleration。现有接口的其余限制须原样披露：native actor 29:38 在 `partner_present` 下读取当前 partner 状态，而不是逐项保证新鲜接收的历史包内容；字段44依赖当前 owner 的退化状态；45:54主要是重复 prepare_latched、warmup 和 handover 摘要，不是可供 actor 查询的 readiness／version／origin certificate。两臂完整保留这些已有输入，不在本次修复它们，也不增加 native 状态、私有未来标签或 partner hidden state 访问。[native `actor_row` 304–317、materialization 328–353][native]；[source intake §2][source-intake]。

因此本次最多是在**既有 A03 信息／所有权宿主**上的同信息比较；不得把结果宣传成严格仅依赖新鲜通信的去中心化优势。分类为 systems / information flow：已有自车执行状态如何直接进入控制参数化，发生在部分观测、移动伙伴与角色循环状态背景中。它不是已识别的仅在多智能体中才成立的机制。[source intake 首两行、§§2–4][source-intake]。

### 投影和合法应用不是同一个保证

native `project` 先把 raw 向量限到范数3，再把相对旧施加向量的变化限到1.5。普通步里，已有 pending intent 的应用检查先发生；当前续约投影随后更新 `s.a`；新的 origin certificate 又在该更新之后被调用。后者比较 clipped raw 与此时的 `s.a`，并另检查共同 SOURCE、warmup、预测 Mahalanobis、service q95、几何和终止等条件。应用端还检查消息时序、版本、epoch、序列、双方电量和几何。[native 261–264、356–358、433–481][native]。

本处理用的是决策前的 own acceleration，不得偷换为这些后续内部状态。即使 raw/applied 差变小，也不等于 origin 合格、readiness 可用或下一步应用成功；更不能把 B06 的无效提交全部归因于该差。新的法则不增加合法性 mask、拒绝重采样、阈值调整、forced hold 或强制换主。[native 同上][native]。

## 三、学习器、随机绑定和评价：一对新训练，不是旧端点旁测

**唯一新配对种子127**，训练／环境主随机源固定为 `SHA256(ASCII('DISH-OWN-COMMAND-MEAN-B07/seed/127'))`。本次只规定法则，未生成或调用这个 master。它须实际进入共同初始化、原训练 reset／语义随机流及新评价 reset，不能只改变结果标签。两臂都以 STRUCTURED 身份使用同一组初始参数和对应共同外生流；OWN／DIRECT 是均值处理标签，不是新 native arm 或另换一个训练 substream 的借口。之后各自的 native、optimizer、循环与 Welford 状态独立演化，不强求动作、标签 eligible 数、后续观察或最终参数相等。[source intake §§3–5][source-intake]；[成本记录 proposed_B_not_selected][cost]。

两臂均用既有 LOW_LR：AdamW 两个原参数组恒定3e-5，原 weight decay、PPO、mean-MSE、BCE-with-logits、link／missingness 辅助项、梯度裁剪、Welford、recurrent replay、私有标签、32-lane训练分布与所有掩码不变。`forecast_package=False`、service-Q raw logits不变。高斯方差的参数化、初始值、学习法则和 Bernoulli 意图法则不变；最终 log_std、意图概率或辅助预测可因各自学习而不同，不能为追求“只变均值”再冻结这些参数或强制轨迹相同。[B06 card §2][b06-card]；[engine 540–642][engine]。

每臂完成 **16×32×128=65,536** 普通训练转移和 **16×4×8=512** optimizer steps，最终只保存／选择 update16用于主比较。保留每次更新的学习率读回、service／loss／gradient及有限性、实际更新与步数、初始化／最终范数和位移、eligible／next-mask、训练事件与换主等已有摘要。不能以配置中写了16代替真实学习计数。[成本文件 per_arm、pair][cost]。

每个条件仍是 TARGET_VISUAL_MASK／TERRAIN_RELAY_MASK × K8／K4_TO_K12，speed4、slot0、block0，按继承 canonical-coordinate／reset 法则用新 master 派生并记录。初始和最终、OWN和DIRECT复用同一条件的 reset／外生法则；不借用 seed89／101／113的 phase、参数或已知回报。所有 episode 以新鲜 native 和循环状态开始；初始参考保持 count-0 Welford，最终评价用**各臂自己的最终固定 Welford**，评价过程中不拟合统计量、不更新参数。训练分布不缩成这四个开发条件。[source intake §4][source-intake]；[B06 card §§2–4 的继承边界][b06-card]。

**每臂均有四行自己的零更新 raw-interface 模态参考，加四行最终模态评价，共十六行。** 共同初始权重不等于两个参数化的初始化控制器相同：一旦已施加加速度非零，OWN的直接输入就可能改变行为。因此不能用一套共同参考代替两臂自己的初始四行。它们属于同一 B 的伴随观察，不是先行 A 或好初始化门槛；不得据参考回报换 seed、跳过训练、挑条件或增加曝光。最终模态使用各臂自己的均值与原 prepare／commit概率0.5阈值，不另加最终随机评价或第二个相同 DIRECT learner。[source intake §§3–4][source-intake]。

真实后果链为：普通事件和续约 → 自车／伙伴既有观测、消息与角色状态 → 自车 raw acceleration 和现有 recurrent motion 输出 → 本臂均值及原训练动作采样 → 不变的 native 投影、通信、合法应用与服务 → 普通 transition／原私有监督 → recurrent PPO／AdamW → update16 完整模态后果。私有 label clone 的额外两步、forced promotion及未来服务仅产生原辅助标签，不是 actor 的信息，也不计普通合法换主。[trainer 417–445、482–524][trainer]；[native 731–746][native]。

## 四、关键正确性依赖：实际动作分布与 PPO 所算的分布相同

现有源码有三个直接相关位置：`step_rows` 发出均值并计算 behavior log probability；engine `_policy_log_prob` 428–458给出高斯／Bernoulli联合概率；训练段571–595又调用该函数并重复计算 motion mean／motion log probability。**选中处理后，实时均值、实时行为概率、PPO重放概率和这处重复均值都必须使用同一臂的公式及相同物理次序。** 仅改变评价或仅改变动作生成，会变成另一实验或损坏 PPO 比较。[trainer 308–325、370–374][trainer]；[engine 428–458、571–595][engine]。

实时计算使用本步发送动作前的 raw actor；重放使用该片段记录的 `actor_raw`、当时 `owner` 和原始 raw action，不能使用最新 simulator 状态、更新后的 Welford 特征或未来投影。旧 behavior log probability保持真实采集值；新概率用当前参数、同一记录状态和相应均值求值。均值内的加速度是已记录输入，梯度仍须通过 motion 输出及 tanh；不反传环境，也不把均值整体 detach 掉。密度仍是**未投影 raw action 的高斯密度**，不是施加加速度的密度；tanh只变换均值，不新增 squashed-action Jacobian。Bernoulli项、续约／prepare／commit mask及原熵法则保持。[engine 428–458、565–628][engine]；[trainer `_fragments`][trainer]。

后续必要检查限定为一次聚焦的改动／主输出覆盖：用 owner=0和1、不同且非零的两车加速度、零加速度及含非续约／重置／角色变化的少量输入，核对 physical-copy 选择、OWN均值与 DIRECT退化情形；核对在线行为概率和片段重放在同一状态／参数／动作下使用相同均值，并使训练的重复项一致、梯度到达 motion 参数。再用少量人工结果行检查四条件主归约、两套初始化参考、原生终止余段计零与换主时刻/null。检查实际 mode/master 传播和 DIRECT 路径未被连带改变。容差按 FP32与相应概率／动作尺度确定，不要求全轨迹逐bit相等。[证据规范 §§4、11.8.5–11.8.7][method]。

这些是保护当前 reward／information／training／primary 的直接依赖，不是新 A、历史 B06 replay或另一个科学启动门。可信的 A03 host、普通续约、native终止与原学习器覆盖直接复用，不因launch边界重跑全套smoke。源码中的现有 mean 尚未实现本处理；本答复没有声称新实现或检查已经通过。

## 五、主量、预测和有限读法

记 `J_A,u,r` 为 arm A 在更新u、条件r上固定1,200-tick范围的原生服务和。native提前终止则停止stepping，余段计零，并列实际／未执行tick和终止原因；保留坏行，不除以存活时长、不匹配较短生存时间、不停止于首个成功或首个换主。原生终止本身是结果，不是技术重跑理由。两臂最终普通评价都继续经过可能的合法换主，且不创建来源fork。[继承 card §4][b06-card]。

主量为 `Delta_mean = (1/4) Σ_r [J_OWN,16,r − J_DIRECT,16,r]`。并列两臂初始／最终均值、每个条件的差分，以及 `D_OWN = mean_r(J_OWN,16,r − J_OWN,0,r)`、`D_DIRECT = mean_r(J_DIRECT,16,r − J_DIRECT,0,r)`。主量不是初末差之差，也不因初始化差异而事后重新定基准。它测的是两套具名学习／控制参数化在相同曝光后的完整性能；若初始参数化本身已不同，不能只凭最终差分称为更快学习或从学习中独立识别了直连贡献。[source intake §4][source-intake]。

**MEI取+24平均服务tick**，是1,200范围的2%，为此项不增参数的改动保留可比较的开发尺度；相反尺度−24，开区间带为(−24,+24)。不是数值容差、逐条件最低改善、显著性门槛或仓库通用值。模态 DIRECT 是实际新训练的匹配对照，不能以 seed113旧端点或一个弱化／零训练对照替换；它也不被称为调优oracle。已有 headroom 缺失与零更新参考非上界保持明示。[source intake §§3–4][source-intake]；[证据规范 §11.7][method]。

**我的事前主预测与 DM 同向：低置信度 `Delta_mean>0`；能否跨越+24不作确定预测。** 正面理由是直接自车执行输入可能减少有限训练中重新学习该关系的负担；反面理由是冗余输入和持续错误加速度可能占优。`Delta_mean<=−24`，包括无效提交变少但服务更差，是重要竞争观察。记录正号预测不等于预测到将来的效应量；没有记录概率，不作校准结论。不给合法换主设下限，也不把来源仍无事件预先判成失败。intake记录 owner预测未取得，本次不补造回复。[source intake §§4、6][source-intake]。

| 完整新观察 | 对这个候选的有限读法与后续建议 |
| --- | --- |
| `Delta_mean>=+24`，原生服务／事件／能量权衡仍值得开发 | 一个新配对实例上的有用原生信号，可据全部行考虑一至两个独立配对种子的有限跟进；不是自动加种子、稳定优势或全方向采用。混合行仍保留，不因其存在否认均值。 |
| 有相对 DIRECT 的增量，但 `D_OWN<=−24` | 仍低于本臂自己的初始化；不能称为恢复初始化能力或一般学习改进。保持初末和相对比较同时可见。 |
| `−24<Delta_mean<+24`，或伴随代价使开发价值不清楚 | 报告本曝光下弱／未决／异质性，不称等价；倾向不自动扩展，不增加样本、种子或checkpoint直到出现同号。 |
| `Delta_mean<=−24`，或收益伴随足以否定其开发价值的原生损害 | 保留 DIRECT，停止该 OWN_COMMAND_MEAN 候选的当前扩展；不以无效提交减少、平滑代理指标或一次换主挽救负服务结果。不得据此关闭整个来源议程。 |
| 无普通合法换主 | 原生服务主量仍有效；收益只能称普通／incumbent服务证据，来源原点及 COPY−RETAIN／SHADOW−COPY 仍未估计。 |
| 出现普通合法换主 | 报告次数、首次 native post-step `cas_applied` 时刻和完整后果；它只是路径事实，不自动证明来源原点可用、换主受益或 prepared-state价值，不追加fork。 |
| 输入、真实学习或主比较受损／未完成 | 保留实际计数、失败和独立可信行，不填造完整配对主量；具体缺口只限制依赖结论。非主张必需的资源量未测，不连带否定原生服务。 |

原生伴随量保留原七类硬事件：buffer_clear、command_slew_breach、dual_owner、dual_payload、invalid_commit、separation_breach、token_gap；每行能量、终止原因、实际／余段tick、合法换主次数、首次时刻或null及换主前后时间分割的服务。事件的原始数与曝光分母并列，训练和评价分开；能量比较说明实际持续时长，不能把提前终止的低能量叫同等服务效率。时间上换主后的服务不等于新 owner 发出的包或换主的因果收益。没有逐机会分母就不把invalid_commit计数说成拒绝概率，零事件也不是安全。[native service/application 433–497][native]；[card §4][b06-card]。

一个配对训练根只有一份配对学习观察，四条件不是四种子；两臂不是两个独立配对，初始行也不是额外学习重复。未来即使出现正均值，也仍可能受初始化、数据／Welford演化及伙伴角色共适应影响；不给训练总体置信区间，不按条件bootstrap制造独立性，不声称独特MARL效果。[证据规范 §§5.2、11.8.2–11.8.4][method]。

## 六、完整工作、支出与源于问题的比例判断

| 工作因素 | 每臂 | 本次一对合计 |
| --- | ---: | ---: |
| 新训练实例 | 1 | 2个learner，共1个配对种子 |
| 普通转移 | 65,536 | 131,072 |
| 更新／optimizer steps | 16／512 | 32／1,024 |
| 普通批量策略前向 | 2,048次，batch32 | 4,096次，另有训练重放／critic工作 |
| recurrent replay | 512 minibatch，每批64循环步 | 1,024 minibatch |
| 初始化模态＋最终模态 | 4＋4 episode | 16 episode，至多19,200评价tick |
| 科学选择／搜索 | 仅update16；无额外处理强度 | 无候选／轨迹树、来源fork或grid |

上述是已给机器算术，不是本次已执行量。每臂普通N=65,536之外，仍有N个next-label步、2E个eligible延迟步和H个私有后果步，故原生训练调用为 **`2N+2E+H`**，`0<=E<=N`、`0<=H<=20E`，每臂 **131,072–1,572,864**，两臂 **262,144–3,145,728**，另加评价。前向、critic、backward、optimizer、构建／加载和发布不在这个native-step界内，不能遗漏。没有新的候选动作枚举、a^N／b^H扩展或“找到一条好轨迹再学习”的搜索。[成本文件 per_arm、pair][cost]；[native passive_labels_one][native]。

**本次选择新的完整 cap：每臂1,800秒，合计3,600秒。** 共同初始化／必要共同检查／共享构建与归约发布的实际共享工作记S，只计一次并事前各分摊S/2；各臂自己的初始四行、训练／标签、最终四行、加载和输出计入各自完整调用。若部分发布在某臂进程中完成，分摊时不能重复收取。每臂完整收费不超过1,800，含S总和不超过3,600；分脚本或阶段不重置cap，给完整发布留在额度内。不另加初始参考、smoke或其他模式的科学额度。[source intake §5][source-intake]；[成本文件 cap scope][cost]。

B05整对 **432.82秒** 和 B06单控制器／执行比较 **226.02秒** 是有用的同规模工作参照，支持把这看成已有实现基础上的有限购买；它们既不测本次两套均值及检查成本，也不构成完成保证。新 E/H、轨迹、cache／load与实际时间仍未知，不能以除以核数、cap比率或一行公式的大小推算加速。B06相对参数L2移动0.04474046045735298说明原学习器在该曝光内能发生移动，不承诺seed127位移或效果。未知成本不自动变成新校准实验。[成本文件 historical_B06、cost_uncertainty][cost]。

停止边界是完成这一个配对的固定学习与全部评价／发布，或达到原完整支出界、出现真实非有限训练状态或威胁主量的故障。保留已发生计数和可信部分；有限大梯度不是非有限故障。没有效果导向的早停选checkpoint、换seed／reset、补跑坏行、增加epoch、调系数或扩大预算。native提前终止按原范围读结果，不产生retry。若后来具体实现已知不能在所选边界内保全科学工作，返回那个明确成本／范围冲突，不静默删除标签或缩短训练／回报。[证据规范 §11.8.7][method]。

选择 B 而不保留零后继，是一次**有限问题价值判断**，不是因为尚未估计来源价值就必须继续。已有源码没有给出该参数化与DIRECT在有限网络／学习过程下完全等价的结论，也没有证明它能带来利益；它提供的是无需新信息的具体计算路径、可保持的真实学习器以及直接的原生对照。现在一对学习结果可改变是否保留此路径，而证书支持census、私有见证或固定动作诊断不能替代训练后的服务比较。继续的理由到这一对为止，不延伸成开放式控制修复计划。[source intake §§3–5、7][source-intake]；[P53 handoff][handoff]。

保留负担各有用途：原交互／标签／PPO定义学习算法；八个最终行测主量；八个初始行限定各臂学习叙述；事件／能量／终止限制收益解释；own-input／likelihood检查防止处理或训练错配。省略完整历史replay、精确上界、调优headroom、全支持census、所有中间数组和原因分解，同时放弃最优性、普遍可达性、唯一原因、严格轨迹等价和来源价值等强主张。不把省略项目移到一个先行A，也不要求再次Pro轮作为B启动手续。[证据规范 §§11.4、11.7–11.9][method]。

## 七、后续落地边界与未验证事实

后续卡和完整CM规格必须保留本文选定的均值、物理映射、真实两臂、种子／master、16行、主量和完整预算，重用既有 native／policy／trainer边界。选定路径保持 remote_first `wsl_4070` CPU、native float64／policy FP32、单Torch／BLAS计算线程、精确提交／推送源码及实际调用前同节点physical和effective available memory各至少4GiB。当前没有做resource admission或触发任何计算。[source intake §5][source-intake]；[AGENTS §§5–8][agents]。

工程范围§4**不需要新增任何设施**：无source-fork框架、scheduler、registry、guard、profiler或通用验证服务。普通2,000新增非测试行、600行runner及既有五分钟目录测试预算保持；30%编排占比只是审查信号。进行与动作分布／训练语义风险匹配的既有独立review，不增加审批层级或为了启动重做历史检查。[工程范围 §§4–5][scope]；[证据规范 §11.8.6、11.8.8][method]。

P53本身未登记CM比较批次。本选择不派遣CM、实现者或额外训练臂；后来coding任务按当前既有规则交给Root，任何仍适用的临时CM比较批次接收**相同完整规格、任务、起始源码和原接受检查**，不得以比较实现方式增加科学调用。剩余批次数和现场路由不在当前证据中，本答复不推测它们，更不改写其规则。[AGENTS“Focused reading and engineering handoffs”][agents]；[source intake §5][source-intake]。

真正尚未验证的是：candidate分支能否在所有指定 live／replay consumer中正确实现，seed127能否完成所选曝光，原生均值／代价和E/H／时间会是多少。它们是后续实现及所选实验要产生的事实，不是现在已观测的疗效，也不是再开一个抽象评估的理由。若合法换主出现，原点资格和 COPY−RETAIN／SHADOW−COPY 仍需另一个实际匹配干预；本次没有授权它。

文献边界保持源归属：source intake §6报告，其检查到的My-lib条目为合成示例，Inst-sci目录190项；所读UTE片段警示重复不佳动作可有代价，但研究Gridworld／Atari中的动作持续长度，不验证当前均值、这一宿主或多智能体利益。我没有另取该论文或从标题推导效果。它支持把持续错误动作保留为反对解释，不提供新颖性、全库缺失或性能保证。[source intake §6][source-intake]。

## 八、实际来源和交付范围

科学证据只使用 **d19bded986f364600cf7769497d1daf3c8fc3ca6**，通过连接GitHub读取；没有用更旧附件、moving branch、镜像或历史聊天判断补充本轮事实。下表C/为 `docs/research/candidates/degraded_incumbent_shadow_handover/`，R/为 `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/`，P/为C/下 `pro_packets/20260908_p53_own_command_mean/`。

| 实际读取的允许路径 | 范围 |
| --- | --- |
| [C/DISH_P53_NATIVE_PROPOSAL_SOURCE_INTAKE_20260908.md][source-intake] | 全文§§1–8，分段补齐尾部 |
| [C/DISH_POST_B06_CONVERGENCE_INTAKE_20260907.md][post-b06] | 全文，补齐§7及尾部；复用已接受结果，不重做实验归约 |
| [C/DIRECTION.md][direction] | 820至末尾中的最终post-B06及P53章节完整；定位时另返回440–660的历史窗口，不把全文称为已读 |
| [R/production_recurrent_trainer.py][trainer] | 260–445、465–535：live、promotion、collection、actor_raw与标签／reward片段 |
| [R/production_training_engine.py][engine] | 25–108、345–458、540–642：graph／snapshot、物理roles、概率、重复mean、实际更新与Welford |
| [R/native/rbhr_r06_production_backend.cpp][native] | 251–358、398–497、731–746：投影、actor／证书、普通顺序／service及private labels |
| [C/DISH_SAMPLED_EXECUTION_B06_SCIENCE_CARD_20260906.md][b06-card] | 25–185，完整相关§§2–5及成本开头；其seed113抽样比较不变成本次处理 |
| [P/EXPOSURE_AND_COST.json][cost] | 全文；配置算术、历史锚点和未来未测量分开 |
| [P/ISSUE_SNAPSHOT.json][snapshot] | 全文八条历史交付及Issue状态；不以评论时间冒称快照读取时刻 |
| [docs/research/portfolio/handoffs/2026-09-08-p53-dish-native-proposal-question.md][handoff] | 全文；只采用P53本方向范围，不操作其中其他方向 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][method] | 35–112、365至末尾，含§§3–5.2、11.4、11.7–11.9 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][scope] | 48–100，§§4–5；不采用旧对象专属例外 |
| [AGENTS.md][agents] | 1–510分段，相关§§1–2、4–6、8完整；未递归读取其外链文件 |

十三项允许科学路径均已实际访问；范围读取不冒称整份文件或其未列依赖已审计。当前没有妨碍形成此有限选择的证据访问缺口。此前的B06底层结果和论文只按本轮允许的接受记录引用，不冒称本次重跑或另取其未列原文。

本轮在 **2026-09-08 18:07:44 UTC（11:07:44 PDT）之前**已读取可变[Issue4][issue]正文及最新[post-B06交付评论][prior-comment]，并读取固定快照中的八条历史交付。Issue标题／正文仍停留在较早B05讨论，不取代当前固定任务。写入前再读实际HEAD、目标及新评论；当前授权允许在科学基底的正常后继上只新增本轮路径，科学版本不随分支推进改变。[固定TASK授权段][task]。

本次未构造模型、native状态，未执行源码、测试、replay、训练、评价、profiling或实验；未修改科学状态、Portfolio或任何既有结果。唯一交付改动是本文与其Issue链接评论。**最终选择是这一对OWN_COMMAND_MEAN／DIRECT_MEAN的真实学习比较；没有新效果被报告，没有额外对象被一并购买。**

[source-intake]: https://github.com/CartmanFatass/My-paper-code/blob/d19bded986f364600cf7769497d1daf3c8fc3ca6/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_P53_NATIVE_PROPOSAL_SOURCE_INTAKE_20260908.md
[post-b06]: https://github.com/CartmanFatass/My-paper-code/blob/d19bded986f364600cf7769497d1daf3c8fc3ca6/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_POST_B06_CONVERGENCE_INTAKE_20260907.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/d19bded986f364600cf7769497d1daf3c8fc3ca6/docs/research/candidates/degraded_incumbent_shadow_handover/DIRECTION.md
[trainer]: https://github.com/CartmanFatass/My-paper-code/blob/d19bded986f364600cf7769497d1daf3c8fc3ca6/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_recurrent_trainer.py
[engine]: https://github.com/CartmanFatass/My-paper-code/blob/d19bded986f364600cf7769497d1daf3c8fc3ca6/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_training_engine.py
[native]: https://github.com/CartmanFatass/My-paper-code/blob/d19bded986f364600cf7769497d1daf3c8fc3ca6/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/native/rbhr_r06_production_backend.cpp
[b06-card]: https://github.com/CartmanFatass/My-paper-code/blob/d19bded986f364600cf7769497d1daf3c8fc3ca6/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_SAMPLED_EXECUTION_B06_SCIENCE_CARD_20260906.md
[cost]: https://github.com/CartmanFatass/My-paper-code/blob/d19bded986f364600cf7769497d1daf3c8fc3ca6/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260908_p53_own_command_mean/EXPOSURE_AND_COST.json
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/d19bded986f364600cf7769497d1daf3c8fc3ca6/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260908_p53_own_command_mean/ISSUE_SNAPSHOT.json
[handoff]: https://github.com/CartmanFatass/My-paper-code/blob/d19bded986f364600cf7769497d1daf3c8fc3ca6/docs/research/portfolio/handoffs/2026-09-08-p53-dish-native-proposal-question.md
[method]: https://github.com/CartmanFatass/My-paper-code/blob/d19bded986f364600cf7769497d1daf3c8fc3ca6/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[scope]: https://github.com/CartmanFatass/My-paper-code/blob/d19bded986f364600cf7769497d1daf3c8fc3ca6/docs/project/ENGINEERING_SCOPE_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/d19bded986f364600cf7769497d1daf3c8fc3ca6/AGENTS.md
[task]: https://github.com/CartmanFatass/My-paper-code/blob/ba699af4e79be7a1c9dd6ef7811dc04c02c9ff14/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260908_p53_own_command_mean/TASK.md
[issue]: https://github.com/CartmanFatass/My-paper-code/issues/4
[prior-comment]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5574756410

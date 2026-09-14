**独立科学审查结论：B10 支持三个必须同时保留的有限事实——相对本次初始化有真实服务学习，相对 attained nearest 有服务优势，但相对同信息、同配额相位支持的 fixed greedy 仍有 U 劣势。在指定设计、两份实际源码及完整已发表记录中，未发现足以使这三个主比较失效的实质性科学缺陷。** 这不是对所有依赖实现的无错证明，也不是稳定训练总体结论。DM 偏好本次观测中的 greedy U，有直接依据；其可逆 PARK 是对下一项研究价值的管理判断，不能由单 fit 的负 D_g 自动推出，也不需要本审查批准。[B10 card，Question / Observable][card]；[B10 intake，Observations / DM direction decision][intake]；[INTAKE_ANALYSIS，comparison][analysis]。

**我没有发现必须撤销当前观测、改终点或补跑才能消除的已证实缺陷；同时建议在既有 DM 回复中补清两点：nearest 优势并非全部由训练新增，拒绝 fresh1024 重复是在接受未测训练变异的机会成本，而不是该重复没有科学辨别力。** 最强反对 PARK 的证据是 G_U=+.061531575521、D_n=+.154589843750、全部八格相同的有利符号、仅一条 final1024 训练历史，以及较小但仍为负的 D_g=−.019075520833。最强支持现有服务偏好的证据是两条主路径、全部八格 U 仍偏向 greedy，且恢复存在不同方向的损害。以下审查区分这些事实、可作的推断和仍未解决的问题，不另选实验、资金或生命周期。[intake，同节][intake]；[analysis，primary_means / comparison / all_eight_cell_means][analysis]。

## 一、发现及其实际后果

**实质性科学发现：没有已证实的设计、信息、学习或主量完整性缺陷。** 这里的“未发现”限于本次明确列出的源码和证据，不代表我重新执行了模型、测试、原生环境或独立数值归约。下列是具体审查结果与需要保持的表述边界，而非新的审批清单。

| 审查项 | 发现与来源 | 对现有结论的后果、相称处理 |
|---|---|---|
| 实际策略、训练及终点 | `policy.py` 使用实际组合分布；`study.py` 的 B10 入口明确进入新对象、seed30、1024 更新与 `final1024` 全链；记录有完整四角色、真实更新及原生输出。[policy][policy] [study][study] [e0][e0] | 未发现据此隔离或撤销 B10 的理由。不要求复跑或引入更强证据类。 |
| 学习与导入规则能力 | 新初始化本身已有 U=.186840820313，优于 nearest=.279899088542；final=.125309244792 又优于该初始化。[analysis，primary_means][analysis] | 建议明确写出“起点能力与训练增益同时存在”。G_U 是新增的自身学习读数，D_n 不是纯学习或纯锚定效应。当前 intake 的三个量分列是正确的；无需新增控制臂才能保留这些量。 |
| greedy 劣势、平局与恢复 | D_g 为负；97 个主场景 U 平局不代表策略相同。恢复均值与失败码数不完全同向，`reading()` 又只接收三个 U 差。[analysis，comparison / all_eight_cell_means][analysis] [study，reading][study] | 保留完整 intake 的混合后果，不能只发布一个 `no_increment_over_greedy` 标签。人工 intake 已披露恢复损害；这不是已发现的主量错误。 |
| PARK 与重复实验价值 | DM 已提供 no-new-work 与 fresh1024 重复的对照理由，未声称稳定退化或全部思路失败。[intake，DM direction decision][intake] | 判断在其当前用途范围内可辩护，但不由数据唯一决定。建议明确接受可能错过更优训练实例的风险；不能把“当前不选择”改写成“重复没有决策价值”。无需由 Reviewer 下达继续或 PARK 指令。 |
| 成本完整性 | 161.35 秒是完整 native 实测；516.5290922 秒是题面给出的结果发布前 support 检查点，后续工作及若干覆盖仍未知。[e0][e0] [task，Additional caller constraints][task] | 不认证完整 support/total cap 合规，也不凭缺失计时宣布违例。成本限制不消灭独立可信的非资源主量。 |

当前 intake 已明确拒绝稳定优劣、等价和预算因果，因此这些被禁止的扩展结论不是我声称 DM 已经犯下的错误。上述两项补充是科学解释上的非阻断澄清，不是改变主量、追加研究或再次批准的条件。若后续报告实际越过这些边界，才需要限制其相应主张。[intake，Observations / Scientific reading][intake]；[证据规范 §§8.1、11.8.7、11.9][spec]。

## 二、设计、信息、比较器及学习法则

### 1. 实验回答的是固定1024终点的完整方法用途，不是预算效应

B10 预先选择一个新 seed30、final1024 的 greedy-anchored common-phase fit。它没有加载 B09 checkpoint 或继续其优化器；B09 的 seed29/final256 是另一训练历史和另一终点。选择较长曝光受 B09 结果启发，是公开的探索，不应被改称盲于既有结果的确认。新 fit 和固定终点使 B10 的自身四角色比较成立，但不能单独识别“从256增加到1024造成了多少改善”。[card，Object decision / Question / fresh identity][card]；[B09 intake，Strongest support / ceiling][b09]。

两份源码与该设计一致：`run_exposure1024` 固定 seed30，并将 `B10_OBJECT, 1024, True` 传给 `_run`；`_run` 构造新对象域的 key、新模型、自己的优化器及八个零 baseline。`final_role=f"final{updates}"` 同时用于 checkpoint 文件、评价角色、`contrasts(panels, final_role)` 和 summary。文件顶部留存的旧 `ROLES`/`final256` 字面量没有代替 B10 的局部角色表；普通 `run` 入口继续服务 B08/B09。这不是看见旧常量就可成立的终点混用缺陷。[study，run / run_exposure1024 / _run][study]。

训练与评价也没有由本文件可见的终点择优：初始化在训练前评价；完整执行1024次更新后保存并评价 sampled final1024；没有中途 held-out 选择、挑最佳 checkpoint 或训练到阳性。训练曲线的 first32/last32 是训练混合分布上的描述，不是额外独立 hold-out 或收敛证明。[study，_run / evaluate][study]；[e0，训练与检查记录][e0]。

### 2. 公共事件到实体动作的路径保留

宿主仍是120-sector、六 beacon、H64 的物理 roster 服务问题。每四 tick 作一次共同相位决定，t24 的成员/epoch 变更先于新 roster 的行动。survivor 保留物理状态，departure 不保留后续行动行，newcomer 按原生事件规律进入。`rollout` 先在需要时 `materialize_events_compact`/`apply_event`，再取得当前 snapshot 的 public observation、构造各 same-N lane 的行动，并交给 `batch.step`。rank 是当前物理次序，不是固定学习身份。[card，Question / comparison][card]；[study，rollout][study]。

对长度 N 的需求列表 b 和当前实体 rank r_i，行动仍为

\[
a_i(s)=b[(r_i+s)\bmod N],\qquad s\in\{0,\ldots,N-1\}.
\]

`quota_arrays` 使用 int64 位置、rank、需求和 beacon 数据，构造全部 N 个映射；环形距离在 delta≤60 时取正方向，精确半圈保留 clockwise tie。固定 greedy 对每个 phase 的绝对整数距离沿实体轴求和，以最小 phase 破平。锚定分支复用同一构造中的整数 signed distance，不用浮点归一化 feature 反推 tie，也不另做未来轨迹搜索。[policy，quota_arrays / phase_features / phase_log_probabilities / greedy_phase][policy]。

这使 greedy 成为有力的同支持、同公共调度设施参照。nearest 通过已有原生 scripted kernel 在自己的当前状态上行动；它不需要 common-phase message。四角色都走真实物理轨迹，不以旧面板均值替代。该比较没有等通信、等计算或无通信分散执行含义；“同一允许的信息”也不等于加入手工 greedy 计算后所有方法的归纳偏置相同。[study，rollout 的 nearest/greedy 分支][study]；[card，四角色与信息边界][card]。

我没有读取未列出的原生 kernel、公共排序依赖或 runner；对这些底层实现的既有合法性与执行环境，采用 card/E0 的已记录检查与准入事实，而不声称独立重写了 nearest、重新验证全部环境代码。已列源码没有显示隐藏未来信息、私有行动传递或削弱参照的新增路径。[e0，source / admission / engineering checks][e0]；[policy，公共特征构造][policy]。

### 3. 真实组合似然与 full-Y 学习相符

实际策略是

\[
q(s\mid x)=.9\,\mathbf1\{s=g(x)\}+.1/N,\qquad
\pi_\theta(s\mid x)=\frac{q(s\mid x)e^{z_\theta(s,x)}}{\sum_aq(a\mid x)e^{z_\theta(a,x)}}.
\]

`phase_log_probabilities` 将 `q.log()` 加到模型 logits 后统一 `log_softmax`；`sampled_phase` 用这同一分布的 detached CDF 取一个 phase，返回对应的同一 log probability 和整队映射。每次机会是一项共同随机决定，不是 N 份重复似然。q 的参数不训练，但不能据此从归一化和评分中删掉 q。对固定公共状态的数学得分为

\[
\nabla_\theta\log\pi_\theta(s\mid x)
=\nabla_\theta z_\theta(s,x)-\sum_a\pi_\theta(a\mid x)\nabla_\theta z_\theta(a,x).
\]

这是源码策略的解释，不是本次新执行的梯度实验，也不需要使整数 argmin 或环境转移可微。[policy，phase_log_probabilities / sampled_phase][policy]。

每个 episode 的 score 是16次共同决定的 log probability 之和，使用实际原生 full64-tick Y：

\[
Y_e=1-\frac1{64}\sum_{t=0}^{63}u_{e,t},\quad
S_e=\sum_{t\in\{0,4,\ldots,60\}}\log\pi_\theta(s_{e,t}\mid x_{e,t}),\quad
L=-\operatorname{mean}_{64}\!\left[\operatorname{stop}(Y_e-\beta_{c(e)})S_e\right].
\]

每个64-episode块覆盖八个6/10训练格各八条 episode。`adam_update` 使用 detached return/baseline，一次 backward、一次 Adam 后才更新 cell baseline；loss/gradient 非有限在该参数步骤前被拒绝。Adam 为 lr3e−4、betas(.9,.999)、eps1e−8、weight_decay0、foreach=False，baseline 按 `.95*old+(1-.95)*cell_mean_Y` 更新。没有 teacher、critic、imitation、F reward、额外导数或 clip。[policy，adam_update][policy]；[study，_run 的训练块与 optimizer][study]；[card，learner][card]。

此全回报 score 估计仍可能有较高方差或有限优化困难，但“可能”不是已识别病因。训练目标 Y 与 post-event U 不完全相同，是已声明的设计边界，不是事后 reward 替换；B10 的直接 full-Y 也必须保留，不能只看 U 推定整个回报。[card，Observable][card]；[FOUNDATIONS §§3–4][foundations]。

原2,561参数模型、shared assignment encoder、mean pooling 与 phase head 均保留，只有最终 scalar layer 初始为零。因此初始策略是 q，而不是 deterministic greedy。固定 log-prior 每次决策重算，不只是一次 warm start；后续 logits 能压过它，.1/N 不是训练后每相位的概率下界，.9 也不是保住 greedy 行为的安全约束。数学正支持不证明充分探索、有限可学性或实测性能。[policy，PhasePolicy / phase_log_probabilities][policy]；[card，策略与初始化][card]。

## 三、实际证据：三个服务方向和全部原生后果

以下数值直接沿用固定 `INTAKE_ANALYSIS.json`/intake；没有重算均值、置信区间或合并不同训练根。展示精度不替换保留的原始精度。

### 主量与绝对水平

令 P 为 ACTIVE_CONTINUATION 8→12、12→8，两条路径各权重1/2；0、f、g、n 分别指本次初始化、final1024、greedy、nearest：

\[
G_U=\tfrac12\sum_{p\in P}(\bar U_{0,p}-\bar U_{f,p}),\quad
D_n=\tfrac12\sum_{p\in P}(\bar U_{n,p}-\bar U_{f,p}),\quad
D_g=\tfrac12\sum_{p\in P}(\bar U_{g,p}-\bar U_{f,p}).
\]

| 主路径等权量 | Own initialization | Final1024 | Fixed greedy | Attained nearest |
|---|---:|---:|---:|---:|
| U，越低越好 | .186840820313 | .125309244792 | .106233723958 | .279899088542 |
| 40U，归一化未满足需求 ticks | 7.473632812500 | 5.012369791667 | 4.249348958333 | 11.195963541667 |
| 直接 full-Y，越高越好 | .804382324219 | .862991333008 | .881484985352 | .720779418945 |
| 失败编码 tau 均值 | 21.859375 | 22.250000 | 22.359375 | 39.375000 |

| 比较 | 均值 | 条件场景 SE | 已发表近似95%条件区间 |
|---|---:|---:|---|
| G_U | +.061531575521 | .007654835280 | [.046528098372, .076535052670] |
| D_n | +.154589843750 | .009113396231 | [.136727587138, .172452100362] |
| D_g | −.019075520833 | .003436903786 | [−.025811852255, −.012339189412] |

三个量的含义不同。正 G_U 和 full-Y 改善是这个实例的真实学习，不因未超过 greedy 而消失；正 D_n 是实际 package 对 nearest 的优势；负 D_g 表明该 sampled endpoint 没有替代 greedy 的 U 优势。起点已经优于 nearest，故不能把全部 D_n 归为训练所创造，也不能凭 G_U 反推出 anchor 的独立因果效应。[analysis，primary_means / comparison][analysis]；[intake，Observations][intake]。

### 两条主路径与实际符号

下表括号内是对应差值的“有利／不利／平局”场景数，均为每路径64条。

| 路径 | G_U | D_n | D_g |
|---|---|---|---|
| ACTIVE_CONTINUATION 8→12 | +.075944010417（35／3／26） | +.187207031250（62／2／0） | −.026041666667（0／18／46） |
| ACTIVE_CONTINUATION 12→8 | +.047119140625（33／9／22） | +.121972656250（57／7／0） | −.012109375000（2／11／51） |

against greedy 的2/128有利、29/128不利、97/128平局，支持有限的观测解释；不能把“每个主路径和每格均值均负”写成“每个场景都负”。同样，初始化与 nearest 的所有格均值有利，不表示没有不利 episode。全部场景仍进入原定总体。[analysis，comparison.paths][analysis]。

### 全部八格 U

active 为 ACTIVE_CONTINUATION，new 为 NEW_EPOCH；这些行不是八个训练重复。

| 格 | U_init | U_final1024 | U_greedy | U_nearest |
|---|---:|---:|---:|---:|
| 8→8 active | .250244140625 | .188378906250 | .171875000000 | .322265625000 |
| 8→8 new | .253417968750 | .195849609375 | .185644531250 | .339794921875 |
| 12→12 active | .094921875000 | .018750000000 | .000000000000 | .242187500000 |
| 12→12 new | .110156250000 | .041406250000 | .025390625000 | .265104166667 |
| 8→12 active | .133300781250 | .057356770833 | .031315104167 | .244563802083 |
| 8→12 new | .139778645833 | .052213541667 | .036783854167 | .258365885417 |
| 12→8 active | .240380859375 | .193261718750 | .181152343750 | .315234375000 |
| 12→8 new | .246337890625 | .201904296875 | .188330078125 | .341259765625 |

这八格同时保留正初始化学习、优于 nearest、落后 greedy。全部八格 full-Y 的方向也一致：final 高于本次初始化和 nearest，低于 greedy；它们是实际 terminalY，不是由 post-event U 重建。12→12 active 的 greedy U=0 是该面板的事实，不能被推广为所有状态/策略类的最优定理，也不能把“八格都必须胜 greedy”增设为未来学习条件。[analysis，all_eight_cell_means][analysis]。

### 恢复与 F 的必要限定

三个 quota 角色的各格 F=0；nearest 的 F 仍为正。F 的差反映申领计数结构，不证明到位、恢复或 reward。以下每个单元格为“tau 均值；tau40失败码数/64”。

| 格 | Initialization | Final1024 | Greedy | Nearest |
|---|---|---|---|---|
| 8→8 active | 37.640625；56/64 | 38.593750；61/64 | 40.000000；64/64 | 39.250000；62/64 |
| 8→8 new | 20.265625；28/64 | 19.703125；29/64 | 20.500000；31/64 | 39.750000；63/64 |
| 12→12 active | .343750；0/64 | .156250；0/64 | .000000；0/64 | 39.375000；63/64 |
| 12→12 new | 1.578125；0/64 | 1.046875；0/64 | 1.015625；0/64 | 40.000000；64/64 |
| 8→12 active | 6.578125；0/64 | 5.562500；0/64 | 5.343750；0/64 | 40.000000；64/64 |
| 8→12 new | 5.687500；0/64 | 4.359375；0/64 | 4.109375；0/64 | 40.000000；64/64 |
| 12→8 active | 37.140625；55/64 | 38.937500；61/64 | 39.375000；63/64 | 38.750000；62/64 |
| 12→8 new | 20.109375；28/64 | 21.546875；32/64 | 20.750000；31/64 | 39.500000；63/64 |

final 相对初始化有3/8格 tau 均值恶化，相对 greedy 有5/8格恶化；对 nearest 有7格改善及 active12→8 的+.1875小损害。active8→12 的0/64失败码与 active12→8 的61/64非常不同。primary tau 比初始化差 .390625、比 greedy 好 .109375 的汇总，不能隐藏这种路径差别。[analysis，all_eight_cell_means / primary_means][analysis]；[intake，Recovery is mixed][intake]。

还需区分均值与失败概率：8→8 new 相对初始化的 tau 均值下降，却从28/64变为29/64失败码；active12→8 相对 nearest 的均值稍差，却是61/64对62/64失败码。这里不新增检验或显著性结论，只保留已记录数量。tau40 不是40 tick必然恢复，也不能把带失败编码的均值读成未删失的成功恢复时间。[analysis，相应两格][analysis]。

`study.reading(dg,dn,gu)` 只有三个 U 输入，因此 summary 的单一标签在逻辑上不能表达 tau/F 的混合结论。当前 intake 已补上这些后果，故不存在因此失效的 U 比较；后续简报不能舍弃这部分，仅用机器标签替代科学阅读。不需为本次审查修改代码或建立新验证服务。[study，reading][study]；[intake，恢复段][intake]。

## 四、不确定性、跨 B09/B10 比较和不能推出的结论

**独立训练单位为一条 seed30/final1024 历史。** 四个512面板、八格、1024曲线点、同一 final 对两个规则的差，都不是新增训练实例。`evaluate` 固定每个 held-out cell 的scenario0..63；`contrasts` 按同一 cell/scenario配对，路径 SE 为样本 SD/8，两个等权路径的 SE 按 `sqrt(sum(SE_path^2))/2` 合并。这个公式与独立 cell 随机域的声明相符，但不能自动产生训练总体或跨任务总体区间。[study，evaluate / contrasts][study]；[card，coupling / limits][card]；[04_EMPIRICAL，随机性有层级][empirical]。

初始化和final使用共同的外生语义地址及phase uniforms，确定规则不消费policy uniforms。每个角色依自己的行动演化，newcomer占位依该角色的物理状态；共同随机键不是共同轨迹。配对能降低某些条件差的噪声，却不使D_g和D_n独立，因为它们共享final，也共享部分场景驱动。[card，四角色和coupling][card]；[study，rollout / phase_uniforms / evaluate][study]。

95%区间是源代码中的normal近似。greedy比较含大量点质量和平局，不能把近似区间写成精确覆盖率证书；当前均值、各路径符号和全部计数足以作窄观测阅读，不需要因此强制bootstrap、power study或新面板。若要另外声称等价、非劣或尾部风险，才需匹配那个新主张的设计与分析；本轮没有这样的主张或新增计算。[study，contrasts][study]；[证据规范 §§11.8.1、11.8.3–11.8.5][spec]。

D_g的绝对点估计小于.025，并不使它成为“等价”；其已发表条件区间为负，且下端越过−.025。因此既不能从点估计或97个平局认证非劣，也不能把+.025的原正收益兴趣尺度回溯改为对称负失败界。active8→12的点差为−.026041666667，而active12→8为−.012109375，两条路径也不能被总均值替代。原MEI只用于两项参照收益，不是G_U阈值。[analysis，comparison][analysis]；[card，Observable / MEI][card]。

B09保留 G_U=+.05126953125、D_n=+.1460205078125、D_g=−.0317708333333，以及对greedy的6/128有利、41不利、81平局和全部恢复损害。B10的负差数值较小，但训练根、终点和评价外生实例都不同；不计算两者的“训练预算效应”，不合并为两个final1024重复，也不以两个方向一致结果估计稳定优势或劣势。它们只能作为公开的不同探索实例、各带自身边界。[B09 intake，Strongest support / ceiling / Exposure][b09]；[B10 card，预算因果非目标][card]。

还有两个具体未识别的解释。第一，G_U可能包含减少q随机偏离所带来的损失，也可能包含对某些服务时序的有益修正；记录没有把两者分离。第二，U平局可以来自不同动作和轨迹，不能由平局率推出“网络已完全复制greedy”。因此不能声称已经发现credit修复、锚定的净因果价值、最优解或表示能力限制。提出这些可能解释只限制归因，不消除实测G_U。[policy，combined law][policy]；[analysis，comparison][analysis]；[FOUNDATIONS §§3–4、6][foundations]。

## 五、对 DM 后继计划与可逆 PARK 的独立挑战

### 有根据的部分

DM的理由不是“1024用完，所以必须停止”，而是当前固定规则已提供更好的U，尚未认为一个后继观察足以改变开发取舍。intake明确列出fresh1024重复这个反选项、拒绝永久CLOSE，并保留重新进入的条件。这与本次B的结果强度相称：研究推进可以因目前的边际价值选择而暂停，不能由此宣布家族或学习的一般失败。[intake，DM direction decision / Reopen condition][intake]；[证据规范 §§7–8][spec]。

特别是，B10既有正学习又有nearest收益，仍没有在该panel上提供替代greedy的U理由。保持fixed greedy作为**这个观测用途的参照偏好**，不需要先证明greedy最优，也不是因为缺tuned headroom而排除研究。两项更早exact-recipe HOLD及已有家族身份保留；B09不被回溯新增一个HOLD，B10也不被改成旧对象的重试。[card，旧HOLD与B09边界][card]；[intake，PARK范围][intake]。

### 最强反对意见，不应被简化成“还有不确定性”

反选项有具体内容：final1024的全部八格都改善了自己的初始化、超过nearest；mean greedy缺口只有−.019075520833，主场景大多U平局，且只有一条1024训练历史。161.35秒完整native运行证明本配置至少在已记录节点完成过，不是一个从未跑通的遥远设想。B09虽不能充当1024重复，仍保留另一条不同曝光下的真实学习事实。**这些足以使fresh1024重复成为科学上认真、可辩护的B，而不是必须先得到新用户需求、阳性pilot或完整病因才能提出的要求。**[analysis，comparison / checkpoint][analysis]；[e0，完整调用][e0]；[b09，观测与局限][b09]；[spec §§11.8.2–11.8.3][spec]。

我的具体挑战是：不要把“当前没有选择一个后继”本身当成“后继没有决策价值”的论证。原服务取舍仍可被改变：另一个完整、独立final1024实例若显示对greedy有实际相关的优势并保留正G_U，会削弱只保留固定规则的开发理由；相近缺口会加强该偏好；相反符号或混合后果会暴露训练变动而限制任何总体结论。因而这个重复有明确辨别力，尽管它不保证出现重要结果。[card，reading narrative][card]；[intake，Alternative B / direction reasons][intake]。

不过，科学辨别力不等于必须现在购买，单次重复也不能自动决定稳定替代。现有记录没有给出训练变异大小、成功概率或完整增量成本，Reviewer也不能伪造期望信息价值。DM可以判断这项信息目前不值得继续投入，但应把该句理解并表述为**当前的定性价值判断和风险接受**，而非重复无用、未来不可能获益或“未达margin者不可研究”的普遍规则。[spec §§8.1、11.8.2、11.9][spec]。

建议在既有DM回应里补充一句：当前不选择重复，接受可能错过一个更优fresh1024实例；PARK的依据是目前对这项信息的开发价值判断，而不是已经测得训练总体劣势。该澄清使理由更准确，不需要新实验、固定种子数、数值决策模型或Reviewer批准。intake已经给出的“科学上可辩护、能改变learned-versus-greedy选择的用途/方法问题或实质审查发现”作为再访条件是足够开放的，不应再增加新customer、精确上界或阳性证据要求。[intake，Reopen condition][intake]。

本次没有识别出一个使DM现有PARK理由在科学上必须撤回的缺陷，也没有证据迫使选择永久CLOSE。是否保留、调整或结束当前推进，仍由DM在回应审查后负责；我不再次下达PARK、恢复ACTIVE或购买fresh1024的命令。[AGENTS，角色定义及§2 Decision ownership][agents]；[spec §8.1][spec]。

## 六、已做工作、未选反选项及真实成本边界

| 工作维度 | 已完成B10；若将来另选同配置重复，其规模才可复用 |
|---|---|
| 训练单位 | 1 fresh fit、1个模型/优化器、2,561 FP64参数、八个cell baselines |
| 真实训练 | 1024×64=65,536 episodes；1024 backward/Adam；全部1024步骤有非零参数移动 |
| 评价 | 4×512=2,048 episodes，自己的初始化、sampled final1024及两个固定规则 |
| 完整规模 | 67,584 episodes；4,325,376 native ticks；2,112个native32 batches |
| 训练共同phase draws / heads / assignment rows | 1,048,576 / 8,388,608 / 71,303,168 |
| 初始化与final sampled panels的assignment rows | 1,703,936 |
| sampled-policy greedy-prior整数归约贡献 | 73,007,104，总计，复用已构造距离 |
| 实际native执行 | 161.35秒；peak RSS623,056 KiB；exit0 |
| 原B10本地有限界 | whole native≤300秒；额外invoked support≤600秒；complete invoked≤900秒；一次started结果调用 |

计数沿用card、题面与analysis，不是本次新统计。N个phase乘N个实体的评分/整数距离归约是算法本身的O(N²)工作；greedy参照同样作普通当前行动选择。没有6^N联合动作搜索、future-trajectory tree或策略枚举前置项目。四角色不是四个训练模型，参数少也不证明总成本低。[card，Work / resources][card]；[task，exposure / prospective alternative][task]；[analysis，counts / native_receipt][analysis]。

E0记录fresh actual-node physical/effective memory为15,626,235,904 bytes、4GiB floor，实际source为`e5fd439735bcc52d7f4cba9943b8c5c5138e21c2`，无source/seed metadata偏差；本次不把B08的旧terminal-CR事故归到B10。完整native计时覆盖准入、startup/build、model、训练、四面板、checkpoint与必要publication/readback/exit；`study.py`内的study-body时间是更窄的源码计时窗口，不能取代161.35秒。[e0，执行与准入][e0]；[analysis，source_metadata / native_receipt][analysis]；[study，_run计时边界][study]。

记录中的工程检查与实际学习不同：四项focused tests和独立engineering review覆盖identity/endpoint wiring；实测1024更新、参数位移8.652219035相对初始范数5.828174590、全部有限checkpoint/baseline以及完整四面板支持真实执行。位移或“全部坐标改变”本身不证明有用协调；直接U/Y比较才给出这里的学习后果。训练Y从first32均值.812937419到last32均值.880493927也不能推出已收敛、还需几步或未来会超过greedy。[e0][e0]；[analysis，checkpoint / observed_curve][analysis]。

失败支持工作不能隐藏：checkout未就绪前选中的测试实际没有运行、literal-SHA bundle拒绝、一次无数据的过早analysis、两个staging和一个source-bundle网络stall，都在E0中保留。它们没有形成第二个科学fit；后续复用同一terminal原始归档。当前没有证据把这些支持故障认定为reward/likelihood/primary缺陷，也不能由最终完成宣称以前没有失败。[e0，Support failures][e0]；[spec §11.8.7][spec]。

**完整成本仍未认证。** 题面明确给出结果发布前support检查点516.5290922秒，之后还有实际工作；固定intake/E0同时保留Monitor/Transport准备、provider/agent寿命和integration等未覆盖项。我未读取不在清单内的`SUPPORT_ACCOUNT.json`或更新后的账，因此不能把检查点当最终support、计算可用余额，或断言600/900秒完整账已经合规。已测native在300秒以内是可保留事实；未知尾项既不是零，也不足以凭空认定超支。[task，成本约束][task]；[intake，Costs / preservation][intake]；[e0，cost limits][e0]。

B09的47.13秒与其历史费用属于另一个对象；card中的172.81秒常均episode成本外推只是旧规划场景，不能替换B10的161.35秒实测，更不能成为未来保证。下一条fresh1024若日后由DM明确选择，需要自己的完整有限工作/成本说明和实际节点准入；这里不预选seed、不重置B10 cap、不授予retry，也不把描述反选项变成新资源承诺。[card，Work / costs / stop][card]；[b09，Exposure / costs][b09]；[agents，§2成本和对象责任][agents]。

固定输入记录已保全raw归档与source bundle，后续review、integration、mapped cleanup属于closeout。它们可在DM管理PARK下完成，不是新的活跃实验，也不是“没有待做清理才准许PARK”的科学条件。本审查不验证当前远端资产是否已删除，不把交付分支后来的文件名或进度当作新科学证据。[intake，Costs / next actual action][intake]。

## 七、相称的处理与未解决问题

目前需要的是保留并准确传播限定，不是补做一套新研究。三个主量、原两项+.025兴趣尺度、fixed final1024、全部有利/不利场景、full-Y及tau40应保持；对nearest的先验起点能力和新增G_U并列，对greedy的负U与局部恢复优势并列；PARK理由明确为可逆的当前价值判断。没有实际缺陷要求新增上界、headroom、完整support census、完整历史故障归因、统计power、阳性pilot或成本校准实验。[spec §§11.4、11.7–11.10][spec]。

剩余科学不确定性是：同一1024方法的训练实例变动；相位MLP在所需区域的表达/优化表现；收益有多少来自减少随机偏离、有多少来自有益服务修正；恢复失败与平均U之间的用途取舍；新对象的真实完整增量成本。现有证据没有把它们定位成一个唯一故障。所需证据类随未来真实问题而变，不是现在逐项购买的清单。[foundations §§3–4、6][foundations]；[empirical，完整方法/机制归因、return和开销][empirical]。

若未来唯一问题就是训练特异性，已有的fresh1024、同四角色、同量级真实B反选项最直接；重评旧checkpoint不能增加训练根，新的exact最大值或机制搜索也不能代替它。若没有当前需要该答案的开发取舍，允许暂不选择。这里解释其作用，不创建新卡、增加拟合次数或安排继续咨询。[intake，Alternative B][intake]；[spec §§11.8.2–11.8.3、11.9][spec]。

没有发现必须提出规范例外的冲突。当前`AGENTS`角色定义和§2、evidence spec§8.1明确由DM负责完整生命周期，Convergence负责实质独立科学审查；历史B09记录中的ACTIVE/旧Portfolio用语不控制当前管理状态。Reviewer不能因自主权而不指出问题，DM也不能借自主权忽略实质发现；但本次没有已证实需要修复的主比较缺陷，审查完成本身不是资金、排期或生命周期审批。[agents，角色定义/§2][agents]；[spec §§8.1、11.9][spec]。

## 八、实际读取与审查边界

本轮直接通过GitHub读取固定TASK及全部11个清单证据路径，按各自有效完整commit。没有借旧聊天结果替代B10证据，也未沿import、原始hash清单或历史引用递归读取未列文件。源码仅读取，未执行；全部经验数值和工作量来自已发表记录，策略/SE等式只解释已有法则。

| 有效版本 | 实际读取及采用范围 |
|---|---|
| `a3114f9e717f920d8c14e4c2e653dd4cdae636a4` | [B10 science card][card]全文：固定设计、身份、learner、四角色、读法、计数/cap与stop；[B10 intake][intake]全文：观测、PARK理由、反选项和成本/closeout；[B10 E0][e0]全文：真实执行、checks、失败及保全边界。 |
| 同上 | [B10 INTAKE_ANALYSIS.json][analysis]：source/counts、checkpoint/curve、primary_means、全部comparison/path reductions、reading flag、native receipt和全部八格U/F/tau/Y/40U/失败码；尾部原始文件hash不是新的读取授权。 |
| `d741be527662c5cec18ed03ae03531658059dff6` | [B09 intake][b09]全文，用于seed29/final256的观测与边界；不采用其历史权限或ACTIVE-idle作为当前指令。 |
| `e5fd439735bcc52d7f4cba9943b8c5c5138e21c2` | [study.py][study]全文：坐标、rollout、事件前后、训练/evaluation、final-role wiring、contrast及publication；[policy.py][policy]全文：公共特征、greedy整数tie、组合似然、模型和Adam/baseline次序。 |
| `4dfdb5f8f8b377eea29006d0715a737429c719bc` | [MARL_EMPIRICAL_EVIDENCE_SPEC][spec]§§7–8、11.4一般条款、11.7–11.10；[AGENTS][agents]角色定义lines32–48与§2 Decision ownership。相邻窗口文本不扩充任务。 |
| 同上 | [FOUNDATIONS][foundations]§§3–4、6；[04_EMPIRICAL][empirical]比较对象、随机层级、package/component、return/cost及证据强度，直接用于上述信息、学习和推断边界。 |

没有决策必要的清单源访问缺口。明确未独立访问的是清单之外的底层native实现、完整runner/测试日志、raw512-row面板与checkpoint二进制、analysis执行脚本、support ledger和远端实时状态。它们的已记录检查可作为来源事实使用，但我没有再次实施那些检查；因此不认证未读全链、重新计算的raw统计或完整成本账。现有清单已经足以完成这项有限设计/解释/后继理由审查，不因未做额外审计而制造启动障碍。[task，读取和审查范围][task]；[spec §§11.8.6–11.10][spec]。

Issue8及交付分支仅用于本轮文件/评论去重和实际交付核对。其旧正文、旧评论、分支新进度不是额外科学输入或权限。B10实际source、固定证据ref与本次文档交付commit互不替代。本次新增fits、models、scientific RNG、episodes/ticks、backward/Adam、evaluation、numerical reanalysis、tests和profiler均为零。

**最终审查意见：保留B10的正初始化学习、对nearest的有限服务优势、对greedy的U劣势和混合恢复；没有已证实使该观测失效或必须追加实验才能解决的实质科学缺陷。** 不把小差、平局、跨B09/B10变化或native完成时间转换成等价、预算/anchor/optimizer因果或稳定总体结论。DM当前PARK理由在所述用途内可辩护，但应明确它接受未测训练变异的机会成本，而不是数据证明没有下一项有价值的问题。生命周期及对本审查的最终回应仍由DM负责；本文件不给出新grant、fit、审批token或生命周期命令。

[task]: https://github.com/CartmanFatass/My-paper-code/blob/34c7ad37324453a87e809222ed8849e0644c0b82/docs/research/candidates/roster_consistent_latent_exploration/pro_packets/20260913_b10_scientific_review/delivery/TASK.md
[card]: https://github.com/CartmanFatass/My-paper-code/blob/a3114f9e717f920d8c14e4c2e653dd4cdae636a4/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B10_GREEDY_ANCHORED_1024_SCIENCE_CARD_20260913.md
[intake]: https://github.com/CartmanFatass/My-paper-code/blob/a3114f9e717f920d8c14e4c2e653dd4cdae636a4/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B10_GREEDY_ANCHORED_1024_INTAKE_20260913.md
[e0]: https://github.com/CartmanFatass/My-paper-code/blob/a3114f9e717f920d8c14e4c2e653dd4cdae636a4/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B10_GREEDY_ANCHORED_1024_RESULT_EVIDENCE_20260913.md
[analysis]: https://github.com/CartmanFatass/My-paper-code/blob/a3114f9e717f920d8c14e4c2e653dd4cdae636a4/docs/research/candidates/roster_consistent_latent_exploration/b10_greedy_anchored_1024_20260913/INTAKE_ANALYSIS.json
[b09]: https://github.com/CartmanFatass/My-paper-code/blob/d741be527662c5cec18ed03ae03531658059dff6/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B09_GREEDY_ANCHORED_PHASE_INTAKE_20260913.md
[study]: https://github.com/CartmanFatass/My-paper-code/blob/e5fd439735bcc52d7f4cba9943b8c5c5138e21c2/experiments/candidates/roster_consistent_latent_exploration/joint_quota_phase/study.py
[policy]: https://github.com/CartmanFatass/My-paper-code/blob/e5fd439735bcc52d7f4cba9943b8c5c5138e21c2/experiments/candidates/roster_consistent_latent_exploration/joint_quota_phase/policy.py
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/4dfdb5f8f8b377eea29006d0715a737429c719bc/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[foundations]: https://github.com/CartmanFatass/My-paper-code/blob/4dfdb5f8f8b377eea29006d0715a737429c719bc/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[empirical]: https://github.com/CartmanFatass/My-paper-code/blob/4dfdb5f8f8b377eea29006d0715a737429c719bc/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/4dfdb5f8f8b377eea29006d0715a737429c719bc/AGENTS.md

# RCLE：E01 之后的完整方向报告与继续建议

DM 建议 **CONTINUE：用一个有限的新 B 检验可学习先验强度**，提交 Portfolio 作最终方向判断。
这替代 E01 审查前的 PARK 建议，没有预先应用方向处置、释放席位或启动新实验。具体发现、
独立审查及逐项回应见 SOURCE_MANIFEST 的 e01_intake/e01_review；以下是决策综合，不能替代
完整原文。科学材料的固定版本不因报告日期更新而被重写。

## 1. 这次结果改变了什么

方向问题是：在合法信息与真实成员变化下，联合学习能否改善原生服务和恢复，并超过有能力的
固定规则。现有 joint-quota-phase 家族使用公共相位、原生 full-Y 学习、固定 greedy 配额相位
以及 attained nearest 和自身初始化参照。两个更早的精确配方 HOLD 仍保留；家族不等于某个
已测配方，也没有全方向不可学习结论。

| 完成的 sampled final1024 实例 | 自身初始化收益 G_U | 对 nearest 的 D_n | 对 greedy 的 D_g |
| --- | ---: | ---: | ---: |
| B10 / seed30 | +.06153157552083333 | +.15458984375 | −.01907552083333333 |
| B12 / seed32 | +.06503092447916667 | +.15638020833333338 | −.0141357421875 |

这是实际学习和 nearest 收益，同时仍有 greedy 缺口。B11 / seed31 在164次完整更新后 SIG11，
没有 final1024 端点；不能当作第三个负结果或从尝试分母删除。单独 D1 未复现崩溃，B12/E01
成功也没有定位或修复其原因。两次完成者及其不同评价根不能估计训练总体方差或预算因果作用。

E01 根据已生效的具名 §11.4.2，冻结 B10/B12 保留模型，在原来的面板运行实际组合策略的
确定性 mode，复用各自原始 greedy 行。新增1,024评价、65,536 ticks，零新拟合/更新。
每个 base 的512行在 U/F/tau/40U/direct-full-Y 上均相等，主 D_mode_g 均为0。
它削弱了“只需换成 mode 就能从现有模型得到超越 greedy 的服务收益”的选择理由。
它没有证明动作/轨迹等价、greedy 最优、总体等价或其他学习法则无用。面板在选择 E01 前已见，
所以不是新的确认集；算术 SE=0/[0,0] 不构成总体等价证书。

保持反证：mode 虽消除 sampled 的服务缺口，却损失部分恢复优势。例如 B12 active12→8
的 sampled tau37.78125/失败59/64，变为 mode/greedy tau38.125/失败61/64；active8→8
从 tau39.03125/失败59/64 变为40/64/64。40是失败编码。没有规定服务与恢复兑换率，
不能把向量压成全指标改善或全无价值。完整各格、计数和成本保留在固定结果及比较记录中。

## 2. 独立审查和 DM 实质回应

完整 E01 审查为93bb8ffcd4de430a722bbb6b84e9733f40d26782，36,074字节，SHA256
628c07bbe61b88d04578748befcb09858ff40ed4abf99abf1f6204a6b1cc752a，已全文读完。
审查未发现使有限观察失效的实质缺陷，要求保留上述恢复代价、选择/复用面板和未知故障边界。
它没有独立重跑二进制/原始实验；采用明确列出的工程和统计核查记录，不能扩写为全面运行时验证。

审查具体挑战了“后继尚未选定”作为 PARK 理由，并提出一个可学习先验强度的反方案；同时认为
PARK 与继续都可辩护，现有结果没有强迫追加实验，也不支持永久 CLOSE。DM 接受前述实质挑战，
已经撤回循环理由并改变建议；不是用“接受但仍 close-call”替代推理，也不是假称审查命令继续。
旧审查关于 DM 最终生命周期权限的文字是其当时背景；新 owner protocol 对本次方向判断生效。

## 3. 最强可行下一判别及其代价

建议一个新学习法则：`pi(theta,eta)=softmax(exp(eta)*log(q)+z_theta)`，一个共享 eta 从0开始，
保持现有 q 的精确构造、合法信息、原生 full-Y 和实际组合分布的 score-gradient，学习 eta 与
现有 scorer。起始分布保持 q，不增加 teacher、信息、奖励替换或预训练搜索。

当前固定先验下，非 greedy 分数要超过 greedy，需跨过 log(9N+1)：N=8约4.29046，N=12约4.69135。
这是源码定义的代数，不是 checkpoint 间隔测量，也不证明 prior 是 E01 平局的病因。
改变训练中的可学习自由度，能直接回答固定 mode 测量没有回答的问题：一个真实学得的新 package
能否提供超越有能力规则的有限服务增量，并呈现怎样的恢复后果。

等待提交期间的一次有限 A/RECON 进一步保留了不确定性：读取两份既有 checkpoint 的标量 head
权重，得到理想范围表达式2×L1为 B10 7.85439、B12 7.76574，均高于上述 prior 量级。
因此最简单的“head范围必然不够”解释没有得到支持；这也不表示极值可达、实际 logits 已跨过
prior 或存在更好动作。这个1.56s内层/2.06s外层的记录量检查没有新模型、训练、场景或评价，
不改变 E01 结论，也不把继续方案包装成已诊断瓶颈的修复。完整限制见 RETAINED_SCORE_SCALE.md
及 SCORE_SCALE.json；不因它未识别原因就追加诊断门槛。

具体建议规模：一套新独立训练过程，1,024×64训练 episodes；sampled 初始化、sampled final、
greedy、nearest、fixed final mode 五个512评价面板。合计68,096 episodes、4,358,144 ticks、
2,128 native32 batches、1,024更新。mode 面板服务这个问题，不是普遍加码要求；初始 mode
由 eta=0/zero scorer 解析为 greedy，因此不再重复买初始 mode 面板。全结果向量、真实参数变化
及 eta 变化保留。DM 已将建议具体化为 B13 实现准备卡和 seed33/新域的代码；24项合成/旧路径
检查通过，独立 Sol/high 代码审查无实质发现，DM 已接受源码91811c61的工程准备。完整审查及
验收在清单内；零评价参数位移目前只在合成 fixture 观察到，没有真实 B13 结果。它前瞻推进了
原先计划在方向决定后才开始的可逆实现准备；
原生调用仍未选择或启动，须按 Portfolio 的实际方向决定应用，当前零新原生曝光。

这仅支持新学习 package 的有限比较。没有新的固定-eta 匹配控制，就不能声称 eta 的纯因果
效果；历史 B10/B12 也不能冒充控制。不是系数网格、decoder 扫描或跑到阳性为止。

选择它而非立即 PARK 的理由是：存在一个具体且可实现的法则限制尚未被改变，起点能力可保留，
实测结果可以改变 learned-versus-greedy 的开发选择。直接给先验一个任意固定 .5 会改变起点且
不让学习决定强度，故不选。另一条不变1024实例仍有复现信息，但对这个剩余法则问题较不直接。
学习得到更强先验并只逼近 greedy、减弱先验后损害服务、继续平局，都是有意义的可能结果。

最强 PARK 理由也真实存在：当前 sampled 与 mode 均未给出替换 greedy 的服务理由，新标量
可能只重现规则，完整工程/解释和跨方向机会成本未知。DM 认为这个具体问题值得一次适度比较，
不是证明其期望价值为正；请 Portfolio 结合下面的实际全局工作判断追问还是暂缓。
新种子/更长训练/全状态诊断既不是自动后续，也不是缺少新机制时必须禁止的工作。

已知 native chain：B10 161.35s、B11 partial40.83s、D1 39.69s、B12 192.81s、E01 6.73s，
合计441.41s。该和不是完整研究 elapsed、aggregate CPU 或完整费用。E01 body3.456s内嵌于6.73s。
新 B 的实测时间 UNKNOWN，B10/B12 只能作粗略参考；一个标量不等于免费研究。
support/provider/agent/review/integration 尾项仍有 UNKNOWN。历史 B10 support 下界627.289636s
和偏差不改写；600s及普通 wall 规划允许误差，不是停止、Send、升级或 PARK 条件。
执行使用既有节点、实际内存 admission 与有限科学端点；不申请新增付费容量或占用第四席。

## 4. 三席全局快照与过期记录的明确修正

目标三个 occupied+reserved。实际提交前更新为 main5456aec117b9746f141d09292af2da1f803b8262
的固定快照：FOLR 的完整 Portfolio CONTINUE 已归档、读完并应用，第三席从预留转为占用。
SOURCE_MANIFEST 的 registry/portfolio_report 和下列具名证据共同说明当前三占用、零预留/空缺；
报告初稿的旧工作集与 pending FOLR 文案已由本次实际决定替代，不沿用过期归档表：

| 方向 | 当前席位及真实工作 | 科学位置、反证与机会成本 |
| --- | --- | --- |
| RCLE | 占用1；E01及完整审查/回应已完成，本报告待 Portfolio；未新拟合 | 当前 .9-prior learned package 有学习/nearest收益而未超过 greedy；建议新可学习 prior 强度问题，完整成本未知。 |
| MGTAP | 占用1；独立工程与科学设计审查已 intake；LR-SELECTION-B01 于07:55:41UTC实际接受，原生调用在途，本报告无新结果 | 原符号混合，DENSE仍默认；等机会三候选学习率选择后新 holdout，共8 fits/589,824 team ticks/4,096 Adam。原生15–30分钟为规划参考；实际结果及完整成本未知。 |
| FOLR | 占用1；Portfolio CONTINUE / MEDIUM 已应用，B03 工程审查和九项远端测试已接受；裁决应用时零 B03 native，DM正准备执行 | B02 一个 fresh/fresh 对比 BANK−Generic=−4.830859375 保持不利证据；B03 是新完整学习程序实现敏感性，2 fits/205,120 ticks/9,938更新。训练与最终评价种子都变，不能单独识别训练方差。旧3041.46 native秒仅为工作量参考。 |

MGTAP 初始科学位置固定3594eafe28ed91b2558fcc064e46ea714edd2e1c；实际接受的源码与设计
intake 为2d351d48604396ce478aa900584bd24b3255def5，launch receipt为cde2d77e9212b5e29cf96c94bee51eb97410aa5f。
这是具名登记和 peer 发布的执行事实，不是本 DM 独立代码接受或新 return 数据。
FOLR 完整新裁决及 DM 回应固定4776103de4f55beaee610c52506112651bfaed04，完整答复17,764字节，
SHA25612f367046d07b6b7b54461cb321329eb1bd691b02ca74ee4cdf6518a1c9a675f。其最强 PARK 反方
和 DISH 替代仍保留；Portfolio 明确说明第二个完整程序观察能改变开发选择，并从机会成本与
原空缺前提两方面撤回旧 DISH 选择。它没有认定每个负结果必须再买第二个 seed。
各方向的完整现行材料在清单内，供实际读取；不同 host/算法的 tick 数不作跨方向效能排序。

旧 PORTFOLIO.md 曾列 UCOPE/LCAC/ACVC 为工作集、RCLE/MGTAP/FOLR 为归档；当前 derived report
已修正。中央 Clerk 已退休。注册表 RCLE report仍引用08c012初稿、次要 historical_evidence
仍写旧 review producer；本报告/完整归档/精确最终请求前瞻替代这些过时描述。FOLR 旧 PARK 与
预留状态由新 CONTINUE 实际应用替代。不能因此创造空缺、重复 DM 或应用旧 DISH 补位建议。

同一个 Portfolio 会话6aa7836e-e4a0-83e8-985d-c633d94935b1中，FOLR 请求
2026-09-14-folr-portfolio-direction-reconciliation-01已经终态，assistant
59c57a65-c3e2-4dfa-861f-e15a67323945；作者已归档、intake并释放绑定给 RCLE。
当前 registry指定 RCLE 请求2026-09-14-rcle-e01-direction-decision-01接续；尚无 RCLE Send。
本报告只请决定 RCLE，不改变 MGTAP/FOLR 的研究、占用或额外资源。

## 5. 需要 Portfolio 决定并交还执行的内容

请按当前 owner protocol 阅读固定材料，明确选择 RCLE 的 CONTINUE/RECAST/PARK/CLOSE，说明
底层假设如何更新、为什么最强可行下一判别值得做或应放弃、范围、claim limits、下一 DM 目标
及任何真实资源条件。DM 推荐上述 CONTINUE，接受需认真衡量的 PARK 反方；永久 CLOSE 无现有
证据支持。不是请求逐实验批准，也不是用原600s support当作资格门。

此前 Portfolio 的真实 reentry 原问、完整答复、DM直接回应及 acknowledgment 均在清单。
其独立实例问题已由 B11实际尝试/B12完成，随后 E01 实际判别与完整独立审查完成；本轮不是
“开始后只整理文档再结束”。同时，新方向问题仍未被这些工作解决，文档完成本身不决定去留。

请列明真正读取的实质材料与缺失内容。网页没有本地技能或会话继承；链接存在不等于读取。
如决策关键内容不可访问，要求同一请求补齐精确正文；不虚构、不因读取问题 PARK。
返回完整判断正文，DM 读完并对实质意见回应，然后应用合规决定，无需 Root 再确认。

# LCAC 暂存与重开记录

## 为什么现在暂存

DM于2026-09-14在完成B03后选择 **PARK，recasts0**。当前程序先在256训练回合做B01，再在1024做B02和一次独立同终点复验B03；两次1024结果分别接近零和不利，没有出现超过+.01的平均优势。B03回答了独立审阅提出的具体抽样敏感性问题，并提供了反面证据。继续重复、再次延长训练或修改优化器，目前都没有比暂存更强的具体开发理由。

选择是可逆的投入价值判断，不能写成“反事实信用分配已证伪”“两算法等效”或稳定劣势。样本量小、再做一次可能改变判断，且单次运行成本不高，这是最强反对理由；它们没有被隐藏。DM没有因耗尽所有者预算、Portfolio否决、等待批准或缺少新机制而停止。[完整intake与选项](LCAC_B03_INTAKE_20260914.md)。

## 研究所得与相反结果

| 对象／master | 每组训练／最终评估 | V J | Q J | Q−V | 解释 | 完整进程秒 |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| B01／9411 |256／32|.18068077|.17705434|−.00362643|MEI内|129.80|
| B02／9412 |1024／32|.18844571|.19066834|+.00222263|MEI内|443.91|
| B03／9413 |1024／32|.20659912|.18879471|−.01780441|不利|498.62|

[第一轮](LCAC_B01_RESULT_EVIDENCE_20260914.md)、[第二轮](LCAC_B02_RESULT_EVIDENCE_20260914.md)、[第三轮](LCAC_B03_RESULT_EVIDENCE_20260914.md)各自保留全部32个正负差、绝对得分、训练日志、模型、计数和成本。B03有18个负、14个正场景，范围−.13298到+.10636。两个1024配对的描述均值−.00779089不能替换B03的不利分类。B01训练量不同，单独保留；32个评估世界不是32个训练实例。

两组确实更新了actor和critic；训练残差、熵和参数移动没有证明策略充分胜任、Q校准、信用方差下降或一个应当修复的优化器缺陷。独立审阅纠正了扩展训练时的种子区间问题：B02/B03训练offset1000–2023、最终3000–3031已分离；未来若选4096，1000–5095会覆盖旧最终区间，必须在新卡中重新分离。没有执行4096、超参数干预、额外原生诊断或被选择的中途checkpoint。

完整独立科学答复与DM逐条回应均在现有intake/pro_packets中保留。B02完整审阅提出并评估了B03及其小／不利结果后的选择；B03实际结果由DM intake，没有伪称新增一轮Pro实测审阅。具体代码改动各有独立检查。

## 可复用资产与边界

- 原生五UAV七动作分类接口、私有DENSE/GRU actor、标量V与factual-Q的完整有限学习比较：experiments/candidates/learned_counterfactual_agent_credit/lcac_b01/{study,policy,learner}.py；算法源25ea4d61c0e1f2484da77f4bc1851e17cdc8eb4a保留于B03源81fec5e1b3a2cee810029f0cd30713a0ea64fce3。
- 固定入口scripts/run_lcac_b01.py、run_lcac_b02.py、run_lcac_b03.py；B01启动源133218a8e08c29e833b4d549ffd48f00b204bf2e，B02启动源25ea4d61c0e1f2484da77f4bc1851e17cdc8eb4a，B03启动源81fec5e1b3a2cee810029f0cd30713a0ea64fce3。
- evidence/b01_seed9411、b02_seed9412、b03_seed9413下的全部raw模型/结果/JSONL、收集SHA256、checkpoint安全读回、计数、图、独立训练单位汇总和执行收据。模型供复核或有明确新目标的后续研究，不是稳定优势的可部署声明。
- pro_packets/20260914_first_design_review、20260914_b01_result_review、20260914_b02_result_review保留完整prompt、answer、provider身份、不可变Git版本和DM intake；不能把短聊天收据当成科学答复。

累计4800回合、1228800 native ticks、9216 Adam，三个完整runner时间之和1072.33秒（约17分52秒），最大单进程RSS559.72MiB。全部支持、模型提供方、方向生命周期成本和CPU总工作仍UNKNOWN；不能据此宣称研究总成本或稳定Q/V速度差。

## 怎样重开

可在现有证据上作出有理由的新判断，无需先有新数据、新客户、正面试验或不同机制。论证应具体说明为何第三次同1024配对、更晚端点或某项有目的改动，能够回答比当前PARK更有价值的问题，并回应上面的同终点不利证据与所有已考虑选项。具体实现/种子/计数缺陷若被发现，也应先保留旧证据再前瞻修正。不得重写旧冻结卡或把新对象伪装成旧对象重试。

先通过实时registry中的Clerk协调当前三槽位准入，复用这个DM和已保存资产。若Portfolio提出重开，DM直接交流并给出采纳、细化或异议理由；首次使用新的DM–Portfolio约定时须将权责、当前intake/PARK理由、候选选项和实际约束交给对方。请求和完整答复及DM回应归档；不把Clerk摘要当完整科学对话。

## 生产者与安全收尾

三个实验均finished0、tmux inactive，全部模型/数据已收集；B03 native Monitor /root/lcac_b03_monitor终态SENT、active_set与pending_notices均空。三个已接受Pro请求均完整归档，Transport报告SENT且各自tab关闭。没有活实验、待发科学请求或继续对象。

本地作者checkout C:/Users/fires/.codex/worktrees/891a/HMASD，branch codex/lcac；本DM任务01a09da1-6639-7fd0-bedd-9e006db051a9。实时端点以C:/Projects/HMASD/.codex和ROOT_OPERATIONS为准。远端复用的执行checkout /home/wu/hmasd-worktrees/lcac-b01-26e23ff3最后源码为81fec5e1，三个结果目录与_receipts全部已复制；没有实时运行依赖。Clerk在本回合结束后完成已接受记录集成、任务安全归档、槽位协调及有实际权限的回收。

两处旧B01测试scratch仍在temp/directions/learned_counterfactual_agent_credit/test/b01-check-20260914-02与-03。早先递归清理命令被自动审批拒绝；DM未绕过删除限制。九个小型合成输出已复制到evidence/b01_seed9411/LOCAL_SCRATCH_RECOVERY.zip，并用LOCAL_SCRATCH_RETENTION.json逐文件hash校验；原目录保留。清理责任仍属DM，等待实际允许的清理边界。不要经其他代理或删除整个checkout绕过同一拒绝；此项不占科学槽位，也不构成未完成实验。

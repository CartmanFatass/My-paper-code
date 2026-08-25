# 第 22 轮算法迭代报告

## 本轮科学问题

本轮先回答一个比“哪种算法更好”更基础的问题：现有 UAV 临时脱离/可恢复失灵
场景，是否真的能把需要动态生命周期处理的行为，与“不做事件后重新分配”的简单
控制区分开。只有来源可识别，才允许用它判断 G31 或其他 learned policy。

## 环境与实验条件

- 场景：S7-S1 风格的 8 架物理 UAV、30 个用户、1 个地面站；每个 episode 为
  500 个物理步。
- 扰动：无失联、单次 IID 失联、较晚且较长的单次失联、两架重叠失联四个 cell；
  失联在动作前生效，随后允许同一物理 UAV 恢复服务。
- 控制器：`constructive` 读取完整失联 ledger 并按冻结规则重新配置；
  `no_reallocation` 在失联后保持原服务目标。两者共享完全相同的 ledger、环境随机性
  和 episode 身份。
- 证据规模：3 个 replicate、4 个 cell、每个 cell 128 个 episode、2 个控制器；
  共 192 个已提交 chunk、6,144 行成对评估记录，bootstrap 10,000 次。
- 平台：本机 AMD CPU，`torch 2.7.0+cpu`，单线程；无 CUDA、无跨后端比较。
- 科学源码提交：`2f8e47c16f0563ed1144e370fff787c22508a14d`。
- analyzer 执行修复提交：`a7e8329d2a4429211c7cd2303dafbb75273c10db`。
- 运行目录：`logs/formal_uav_temp_loss_g1_cpu_20260724_2f8e47c_r1`。

由于 UAV 物理环境较重，完整控制证据跨越了三个前台工具窗口。后两个窗口只按
runner 的 immutable chunk 身份续行同一个 run，没有增加样本、改变 seed 或重复计算
已完成 chunk。train/evaluate 闭合后，fresh analyzer 曾因未先设置 Torch 单线程而产生
运行身份假冲突；最小修复只在 analyzer/validator 入口调用既有 runtime 初始化，并由
回归测试证明。它没有改变任何科学数据或结果规则。

## 证据闭合

正式 validator 全量通过，`operational_valid=true`、`operational_errors=[]`。
source law 与成对随机性检查通过，192 个控制 chunk 和 6,144 行记录完整闭合。
因为 source predicate 失败，runner 按预注册顺序在模型初始化前停止：训练行数为 0、
optimizer step 为 0、checkpoint 为 0；learned access/gain gates 没有被计算。

PM 使用冻结的 `select_result_branch` 对 analyzer 的 predicate inputs 独立重算，结果与
artifact 完全一致。

## 注册结果

首匹配结果为：

`SOURCE_NON_IDENTIFIABLE_UAV_TEMP_LOSS_G1`

关键来源指标为：

- constructive `J_event` CI95：
  `[0.8481144, 0.8566158, 0.8652401]`，均值低于冻结的 `0.90` 可行性线；
- `constructive - no_reallocation` CI95：
  `[-0.1181600, -0.1058924, -0.0920913]`，整个区间为负，而冻结要求其下界严格高于
  `0.10`；
- `source_law_and_pairing_pass=true`；
- `constructive_feasibility_pass=false`；
- `disturbed_load_bearing_pass=false`。

## 对科学决策的影响

这说明当前临时失联 G1 的困难并没有被注册控制对识别出来：知道完整未来失联 ledger
并执行 constructive 重配置，反而比不重新分配更差。因此，任何 learned policy 在此源
上的优劣都无法被解释为“动态生命周期能力”。本轮永久关闭这个精确来源，不调门槛、
不换控制器、不改 seed、不增加训练来救它。

本轮并不否定 G31。G31 在 paired toy 上的正式成功保持有效；在本轮中 G31 以及两个
UAV learned arms 根本没有被初始化，所以不存在 UAV learner 失败证据。科学推进应转向
机制独立且已完成外部合同冻结的充电轮换 G2：充电/排队/回归让缺席 UAV 的物理状态
继续演化，更接近用户要求的数量变化与生命周期鲁棒性问题。

## 本轮不支持的结论

- 不支持“G31 在 UAV 上失败”；本轮没有 learned training。
- 不支持“所有临时失灵场景都不可识别”；只关闭当前冻结的 S7-S1 G1 来源与控制对。
- 不支持充电轮换、突增通信需求或三类场景组合的任何结果。
- 不允许把 lower-precedence access/gain 指标补算出来重新标记本轮结果。
- 不允许通过增强 constructive、削弱 no-reallocation 或降低 `0.10` 门槛救回 G1。

## 下一边界

下一步为 `UAV_CHARGE_ROTATION_ROSTER_G2_EXECUTABLE_REALIZATION`。先按已冻结的
S7-S3 充电、排队、0.80 回归、ACTIVE/CHARGE_ABSENT/TERMINAL 状态机实现最小 active
line，完成 proof-sized 测试和一次 bounded nonformal CPU exercise，再由同一个
source-first runner 决定是否允许 learned training。本轮消耗一次有效结论性迭代，自动
研究授权剩余 5 轮。

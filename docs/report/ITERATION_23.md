# 迭代 23:事件对齐源合同经修改后冻结

日期:2026-07-26 · 分支 `untied-k` · 轮次
`docs/external-review/rounds/20260726_d7_s_event_aligned_contract_freeze`

## 科学问题与决策

迭代 22 的裁决把下一件证据制品定为"重注册的事件对齐 D7.S 源合同"。本迭代
起草该合同、以 `hmasd-contract-griller` 做冻结前对抗审(20 项发现,
F01–F21,集中于 flex 事件机制:未注册的 0.25 停靠触发器、H_flex=450 的
算术仅经该触发器闭合、约 120 步的支持裕量、不可触发的 Part-A 矛盾分支、
逐 episode 闩锁使窗口 G 依赖窗口前历史),将全部未决决定作为一棵预走分支
树送 Pro 冻结确认。

## 裁决(FREEZE AFTER MODIFICATION,十一项修正,无争议接收)

- **事件锚**:弃 0.25 触发器,锚定注册的 G2 LEAVE/CHARGE_ABSENT 边界
  (计划性捕获转换);排除排队、紧急切断/耗尽、临时失效路径。
- **H_flex = 550**:Pro 自行推导——充电功率须减悬停功耗
  ((0.80−0.02)·160·3600/(1000−168.49) ≈ 540.3,进位到共享检查点 550),
  这一项草案与对抗审都未发现。合格期限 t_e ≤ 950,完全案例支持,不用
  删失估计器。
- **能量剖面**:审计与校准全部用注册的 `heldout_low`(0.45–0.80),主张
  显式限定于该剖面;训练剖面只作不合并的支持诊断。
- **每 episode 恰一个联合混合紧迫度事件**,两肢在同一 t_e 评估。
- **认证阈值**:X=50 m(S7 将用户速度覆写为 5 m/s,纠正了提问中 150 m
  的通用尺度)、Y=10 步、Z=139 步;空替代集使历史不合格。
- **constructive_mixed** 以 G2 `CONSTRUCTIVE_CHARGE_ROTATION` 为约束参照
  并给出操作定义;null 为事件对齐的 NO_PROACTIVE_ROTATION。
- **推断**:n_select=4、n_eval=8、种子哈希域;分层自举 10,000 次单侧
  95% 百分位、公共流 2026072601、自举内重跑选择;δ=0.05 等价检验定义
  PART_A_CONTRADICTION。
- **拓扑**:种子 20260726–33 冻结,一次性扩展 20260734–41,此外永不;
  钉定程序修正——坐标必须在每次 episode reset 之后恢复(reset 会重初始化
  充电站)。
- **G 绑定**:capped return cost、分析器按固定权重合成、窗口局部事件
  闩锁;强制非退化审计,新增 `QOS_COMPONENT_SATURATED` 与
  `PRIMARY_G_DEGENERATE`。
- **分支系统**扩为十个首匹配分支,含三个肯定性阴性分辨
  (`STABLE_PERSISTENCE_WITHOUT_MATERIAL_FLEX_RENEWAL` 等),
  `SOURCE_NECESSITY_UNRESOLVED` 变为真残差。

合同已按裁决全文改定并标记 **FROZEN**;传输一次栅栏、一次卡页替换、
哨兵校验捕获 33,355 字节逐字节相等。

## 下一边界

证据行动 1:零计算一致性推导(事件检测、拓扑恢复、职责图、合法候选枚举、
五臂两两可分、窗口局部安全分量、十分支可达性),随后 20260725 开发拓扑
的证明尺度演练,再一次八拓扑联合审计。D7.3 仅在
`PERSISTENCE_NECESSARY_SOURCE` 上推进;D8 维持阻塞。

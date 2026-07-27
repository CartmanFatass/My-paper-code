# 迭代 27:守卫扫查进入分析器本身,发现断言打在了旁观者身上

日期:2026-07-27 · 分支 `untied-k` · 支撑性工作,不消耗结论性迭代额度
(授权余量维持 17)。

发射闸门仍被外壳层拦下,继续做在结果落地前必须完成的事。

## 方法先行,这一轮是它的验证

迭代 26 收尾时定的下轮做法:**先按测试名字里的量词批量筛,再读函数体**——只比对
名字与夹具,不需要理解实现。本轮照做,一次命中,而且命中的是至今最重的一处。

筛出的候选里,`test_window_local_counts_at_most_one_transition_per_uav` 最该先看:
它守的是 D7.S 冻结的 §7 窗口内闩锁约定,即论文侧的事件计数,且与迭代 26 第二条
是同一个 "per uav" 形状——只是这次在**分析器**里,不在环境里。

## 发现:一条测试,三层失效

```python
def test_window_local_counts_at_most_one_transition_per_uav():
    window = np.array([[False], [True], [False], [True]])   # 形状 (4, 1)
    assert audit.window_latched_counts(window, np.zeros_like(window))["cutoff_count"] == 1
```

1. **夹具只有一架无人机。** 名字对 UAV 取全称量词,夹具只有一列。全队共用一个
   标志的闩锁照样通过。变异后 **180/180 全绿**。

2. **它断言的量结构上不可能违反该性质。** `cutoff_count` 是对**布尔数组**取
   `np.sum`,任何实现下都不可能超过每机一次——闩锁在不在都一样。这正是迭代 26
   第一条那个"钳位断言自己的钳位"形状。所以**完全删掉闩锁**在这里是不可见的。

3. **而且它根本不是进入结果的那个字段。**

```text
:2877  new_cutoff_count=int(latched["cutoff_per_step"][i + 1])   -> compute_G
:2886  cutoff_incidence=latched["cutoff_count"]                  -> 仅诊断
```

`compute_G` 减去 `5·new_cutoff + 10·new_depletion`,取自 **`cutoff_per_step`**。
测试断言的 `cutoff_count` 只喂诊断字段。**真正进入主量的那个序列没有任何测试。**

删掉闩锁后,原夹具的 `cutoff_per_step` 从 `[0,1,0,0]` 变成 `[0,1,0,1]`——一个以
`−5` 进入 `G` 的幽灵 cutoff——而 `cutoff_count` 恒为 `1`,测试恒绿。

## 修复

三架无人机、错开首次跃迁,并在同一夹具里让 UAV 0 复发一次,**两个输出都断言**:

```python
window = np.array([
    [False, False, False],   # step 0 = t_e 基线
    [True,  False, False],   # uav0 首次        -> 计数
    [False, True,  False],   # uav0 恢复,uav1 首次
    [True,  True,  True],    # uav0 复发(不得重计),uav2 首次
])
assert result["cutoff_count"]          == 3
assert list(result["cutoff_per_step"]) == [0, 1, 1, 1]
```

两个 RED,且由**不同**断言捕获——这正是两条都写的理由:

- 全局闩锁 → 计数上 `assert 1 == 3`;
- 删除闩锁 → 逐步序列上 `[0,1,1,2] != [0,1,1,1]`。

中途有一次自我纠错:我第一版修复只断言了 `cutoff_count`,对"删除闩锁"变异**仍然
是绿的**。正是这次失败暴露了第 3 层——断言打在了旁观者字段上。若没有对每个修复
都跑配对反例,这一层会被我自己漏掉。

240 项测试绿,生产代码未改动。

## 规则更新

`$hmasd-acceptance-gate` 新增:**断言进入结果的那个字段,不是顺手的那个兄弟字段。**
写断言前把值追到估计器:若被测量从不被 `compute_G`、pooler 或分支判定读取,这个
守卫守的是旁观者,却会被读成对真实输出的覆盖。

## 六例的分布

| # | 位置 | 形状 | 触及主量 |
|---|---|---|---|
| 1–2 | 外审发现(CRN 同义反复、指纹簇) | 两边同源 | 是 |
| 3 | 六守卫内扫(自举种子等) | 多种 | 三条可移动分支 |
| 4 | S7 返航阈值 | 钳位断言自己 + 公式两副本 | 间接(轨迹与观测) |
| 5 | S7 cutoff/depletion 闩锁 | 名字有量词、测试无 | 直接(`−5`/`−10`) |
| 6 | 分析器窗口闩锁 | 上述两者 + **断言了旁观者字段** | 直接(`−5`/`−10`) |

**六例中有五例可由"把名字当规格读"这一扫捕获。** 这是目前性价比最高的做法。

## 下一边界

`USER_COMPUTE_AUTHORIZATION`。放行后下一个结论性迭代即审计结果本身。在此之前
继续按量词筛剩余测试面:`test_state_hash_is_sensitive_to_every_digested_key`、
`test_user_world_seed_is_disjoint_from_every_other_registered_seed`、
`test_stable_certification_requires_all_four_predicates` 等仍未查。

## 时间分布(迭代 27)

墙钟只对可测项给数;本会话经过时间未测,不编造。

| 桶 | 内容 | 约计 | 占比 |
|---|---|---|---|
| 科研推进 | 量词筛选、三层失效的定位、`cutoff_per_step` 到 `compute_G` 的追踪、四次变异、两版修复 | 大头 | ~80% |
| 核定/仪式 | 证据笔记、规则更新、迭代报告 | 中 | ~18% |
| 损耗 | 无(第一版修复不完整,但正是它暴露了第 3 层,计入推进) | 极小 | ~2% |

可测锚点:聚焦测试每次 0.3–0.5s;全相关套件 240 项约 41s。

**无事故**:科研推进远高于 50%。

**下轮削减**:本轮筛选已用 grep 一次性列出全部含量词的测试名,该清单可直接续用,
不必重扫。

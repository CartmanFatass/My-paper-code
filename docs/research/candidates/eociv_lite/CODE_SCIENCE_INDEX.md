# EOCIV-LITE arm/calibration/route closure

## 结论

这个隔离候选通过了 `EOCIV-LITE-V8-ARM-CALIBRATION-ROUTE-CLOSURE` 的五项确定性检查。结果只说明 rational unit configuration 中的四臂干预、校准、native-neutral、critical-route 与 gradient firewall 是机械闭合且可解释的；它不支持 targeting value、generic masking value、semantic staleness、utility 或 return 结论。

项目当前生产路径中没有已注册的 EOCIV lifecycle/native-neutral/semi-Markov 实例，因此实际绑定状态是 `ABSENT_ACTIVE_EOCIV_OBJECTS`。这不是负科学结果。未来若要进入 outcome-bearing trial，至少需要：

1. 已注册的 lifecycle opportunity clock 与完整 `W_minus` schema；
2. 带 `HARD_OPEN` 覆盖的 support-native neutral kernel；
3. 四个 ancestry-disjoint pools，以及冻结的 pre-reveal critical graph 和 parameter/recurrent route graph。

需要 Explorer 在未来明确的唯一选择是：哪一个 active lifecycle opportunity population 与 support-native neutral 定义应替换本 rational unit configuration。当前实现不替代该科学选择。

## 目录与隔离理由

- 实现：`experiments/candidates/eociv_lite/arm_calibration_route_closure.py`
- 镜像测试：`tests/experiments/candidates/eociv_lite/test_arm_calibration_route_closure.py`
- 本索引：`docs/research/candidates/eociv_lite/CODE_SCIENCE_INDEX.md`

该方向尚无生产消费者，因此保留在 isolated candidate tree；`ha_ctse_process/`、`envs/` 与 `scripts/` 均不导入它。若方向被放弃，应整组删除这三个路径，Git 保存历史；不创建 compatibility layer 或历史代码目录。

## 冻结对象与机械值

- 候选：`CAND-VAP-EOCIV-LITE@adversarial-revision-v8`
- trigger：`receiver-opportunity-v1`
- cluster：`cluster-rational-00`
- exact horizon：8 个完整 semi-Markov opportunities，physical ticks 为 `10,13,16,19,22,25,28,31`
- ancestry roots：`ancestor-fit`, `ancestor-cal`, `ancestor-policy`, `ancestor-focal`，无共享 root 或 sample
- finite threshold grid：`0, 1/4, 1/2, 3/4, 1`
- deterministic most-open feasible threshold：`kappa_c=1/4`
- 仅由 `D_cal` 冻结的 `q_c`：`route-a=1/4`, `route-b=1/4`
- learned open sequences：两个 cell 均为 `[false,true,true,true]`
- target-independent constant-control sequences：两个 cell 均为 `[false,true,true,true]`
- support-matched sham score：每个 cell 的 support 精确保持 `{0,1/4,1/2,3/4}`，无 missingness
- exact clock/run law：global opportunities `0..7` 与 physical ticks 严格递增；每个 cell 的 declared control sequence、previous-open、open/close run positions 全部一致
- critical route：声明的 critical edge 在 deadline 前位于每条 frozen live path；否则不能使用 `HARD_OPEN`
- source active lines：486（不计空行与注释行，低于 500）

`q_c` 初值只从 `D_cal` 的 `calibration_rows` 推导，随后作为 frozen immutable table 使用；validation 会重新从 `D_cal` 推导并要求精确相等。`D_C` 的 tape 和 sham permutation 位于独立预声明的 `control_table`，其直接函数不接收 target score、payload label、outcome、body 或 learned decision。测试同时改变 target score 与 payload label 后，control/sham 输出保持不变，而 `D_L` 仍只随 learned score 改变。reward、fold outcome 与 post-reveal state 均在 selector allow-list 外并 fail-close。

## 五项 closure 与代码符号

| 机械断言 | 代码入口 | focused test | 结果 |
|---|---|---|---|
| 两个 legal bodies 在 masked route 的 actor inputs 与全部 downstream writes 逐字节相同；real route 保留原 bytes | `_payload_pair_closed`, `receiver_trace`, `actuate` | `test_payload_pair_masked_writes_are_byte_identical_and_real_bytes_survive` | PASS |
| LR/CR 在 action sampling 前逐字节相同且 action kernels 相同；不同 body 会被检测 | `always_real_equivalent`, `pre_sampling_trace`, `action_kernel` | `test_lr_cr_are_identical_before_sampling_and_mismatch_is_detected` | PASS |
| LS 只读 `D_L`，CS 只读 `D_C`，LR/CR always-real，`G=0` suppressed，unsupported `G=1` HARD_OPEN | `_arm_mapping_closed`, `actuate` | `test_ls_reads_only_d_l_cs_only_d_c_and_controls_are_always_real`, `test_g_zero_suppresses_every_arm`, `test_unsupported_g_one_is_hard_open_for_every_arm` | PASS |
| `dL_team/dtheta_valve=0`, `dL_team/dkappa_c=0`, `dL_valve/dtheta_backbone=0`，body 只能经 `body->actuation->receiver_recurrence` | `route_closure_closed`, `validate_config`, `_reachable` | `test_gradient_and_pre_actuation_route_graphs_have_no_bypass`, `test_each_gradient_bypass_fails_closed`, `test_each_body_pre_actuation_bypass_fails_closed` | PASS |
| `q_c`、独立 control/sham tables、clock/run laws、critical all-live-path、neutral envelope/cost 与 sealed route 均闭合 | `_outcome_null_closed`, `derive_q_from_calibration`, `control_open`, `sham_score`, `clock_run_law_closed`, `critical_paths_closed` | `test_score_and_payload_label_mutations_cannot_reach_control_or_sham`, `test_clock_monotonicity_and_declared_run_law_fail_closed`, `test_critical_edge_must_be_on_every_live_path_for_hard_open` | PASS |

Mutation coverage 对 `body`, `body_metadata`, `arm_bit`, `reward`, `post_reveal_state`, `fold_outcome`, `owner_private_proxy`, `global_rng` 全部返回 `FAIL_CLOSED`。测试也证明 control kernel 不调用 Python global RNG；三个 gradient null 分别有独立 bypass 负例；body-to-selector、body-to-recurrence direct 与 alternate-body path 分别 fail-close；nonmonotonic clock、错误 run position、critical live path 缺失 declared edge、非法 neutral、pool overlap 与未冻结 calibration 均触发 `ClosureError`。

## 实际命令与原始输出

Focused tests：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q -p no:cacheprovider tests/experiments/candidates/eociv_lite/test_arm_calibration_route_closure.py
```

```text
.........................................                                [100%]
41 passed in 0.14s
```

候选入口连续运行两次：

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' experiments/candidates/eociv_lite/arm_calibration_route_closure.py
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' experiments/candidates/eociv_lite/arm_calibration_route_closure.py
```

两次标准输出逐字节一致；每次原始输出为：

```json
{"actual_instance_status":"ABSENT_ACTIVE_EOCIV_OBJECTS","candidate":"CAND-VAP-EOCIV-LITE@adversarial-revision-v8","closures":{"always_real_pre_sampling_equivalence":true,"exhaustive_arm_mapping":true,"outcome_sealed_null_conformance":true,"payload_pair_byte_closure":true,"zero_jacobian_and_pre_actuation":true},"control_open_sequences":{"route-a":[false,true,true,true],"route-b":[false,true,true,true]},"future_explorer_choice":"Which active lifecycle opportunity population and support-native neutral definition should replace the rational unit before any outcome-bearing trial?","learned_open_sequences":{"route-a":[false,true,true,true],"route-b":[false,true,true,true]},"minimum_actual_objects":["registered lifecycle opportunity clock and W_minus schema","support-native neutral kernel with HARD_OPEN coverage","four disjoint ancestry pools plus frozen critical and route graphs"],"mutations":{"arm_bit":"FAIL_CLOSED","body":"FAIL_CLOSED","body_metadata":"FAIL_CLOSED","fold_outcome":"FAIL_CLOSED","global_rng":"FAIL_CLOSED","owner_private_proxy":"FAIL_CLOSED","post_reveal_state":"FAIL_CLOSED","reward":"FAIL_CLOSED"},"non_claims":["targeting value","generic masking value","semantic staleness","utility or return"],"pool_roots":["ancestor-fit","ancestor-cal","ancestor-policy","ancestor-focal"],"q_c":{"route-a":"1/4","route-b":"1/4"},"route_predicates":{"clock_run_law":true,"critical_all_live_paths":true},"terminal":"PASS_INTERVENTION_CLOSURE","threshold":"1/4","treatment":"EOCIV-LITE-V8-ARM-CALIBRATION-ROUTE-CLOSURE"}
```

## 技术验收边界

实现不进行 episode/return trial、independent focal audit、learning、fitting、reward estimation、threshold tuning、rescue、environment step 或 production integration。它只执行 hand-checkable rational branch/closure logic。

执行 readiness 未触发：候选没有修改 production entry、runner phase、artifact lifecycle、shared serialization 或任何生产模块；证据只属于 isolated direction-local prototype。最终科学语义验收仍由 Explorer 对精确 pushed revision 组织，本文仅记录 Code Manager 的机械证据入口。

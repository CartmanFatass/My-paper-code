# Proposed only — not applied

Derived from the exact archived Pro rule block; only the stray space before the A05 runner path is removed. No approval or implementation is inferred.

### CBSC B1修复与DISH A05对象限定附款

**1．适用对象与基线。** 本附款仅适用于下表两个完整逻辑变更。所有依赖文件及后续修订从同一声明基线合并计数；已有候选的新增行计入上限，不另发增量额度。通用“小规模复用／净删除例外”的100行规定保持不变。

| 对象                                                      | 计数基线                                                        | 整项非测试源码边界                                         |
| ------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------- |
| `DISH-PREDICTION-HEAD-CONTRACT-A05`完整原卡实施               | pre-A05 accepted `d543146cc11ccf880da1245bfb6884356772dd38` | `A≤250，D=0`；只新增下列runner和薄C++导出，不改既有生产源码           |
| `CBSC-OMRC-B01`在2026-09-05 selection intake声明的完整执行到发布修复 | `0ffca930b9e43b0c6402fce65493cdf6ae24f66f`                  | `A≤200，D≤500`，因此`A+D≤700`；仅限下列既有依赖范围，不增加runner或框架 |

A05运行源码仅为`scripts/run_dish_prediction_head_contract_a05.py`和`experiments/candidates/degraded_incumbent_shadow_handover/head_contract_a05.cpp`。

CBSC运行源码仅限`experiments/candidates/capability_bound_semantic_currentness/omrc_b01/`中的`b1.py`、`telemetry.py`、`b1_metrics_production.py`、`b1_metrics_training_assembly.py`、`b1_metrics_rehydrate.py`、`b1_mechanical.py`、`b1_metrics_artifact.py`。每个实际变更仍须属于资源缺失的真实报告、独立wall处理、同一原始fixture的定位、科学量组装或完整发布／消费者处理。

**2．比例规则。** 对符合上述对象、范围和行数边界的变更，完整报告A、D、O及`O/(A+D)`，替换两侧计数，测试和文档分列。编排占比达到或超过30%本身不再自动退回；既有独立reviewer审阅必要性、全部受影响科学量与消费者，并列明未验证事实。不重新分类已报告编排行以取得资格，不把未改helper或测试计入分母。

**3．科学保护。** A05原卡第2—7节的真实调用、输入、全部读数、正控制、数值语义、分支、曝光和运行上限不变；四个保护生产surface不变。CBSC原完整科学比较、种子、曝光、数值/RNG语义、十五表、summary、RAW能力输入和解释权限不变。不得删除科学量来适配源码或验证预算；不得把可选资源缺失重新提升为科学有效性门槛，也不得把部分资源观察认证为完整资源覆盖。

**4．验证与非授权。** 不新增§4机械设施，不改变2000新增行、600行runner、既有测试／发布要求、资源准入、逐臂数值预算或证据规范§11.4。本附款不接受`ea05e9308`、`9ee4a381`、`cfbe91367`或任何旧拒绝补丁，不放行任何调用。A05依原非卡smoke／rule profile验证；CBSC保留原真实常量离线发布及全部读回要求。测试不因不利输出而删除；不足的验证预算如实返回。

**5．完成与停止。** 不得拆分逻辑变更、重置基线、挪移／压缩代码或填充计算规避计数。预算内只处理该范围内明确发现的问题；出现所列范围之外依赖、保护语义改变或预算不足时，返回整个变更与具体缺口，不自动扩展。A05在原完整读数intake后、CBSC在完整工程验证intake后结束本项投入；后继对象与新learner运行不继承此例外。此结束是投资边界，不是A/B消费或科学负面。

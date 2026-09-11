# DISH A02 后 Convergence 决定简报 — 2026-09-06

**一句话**：Pro（PRO_FINAL）继续 RETAIN/COPY/SHADOW 探索家族，下一笔投入只选一个修正接口上的 B03：CONTROL 对 FORECAST_PACKAGE 的真实学习比较，新的配对种子 73，每臂 16 次更新，4 个最终评估 episode，MEI 仍为 +24 平均服务 tick，每臂 1,800 s、合计 3,600 s。不是 RECAST；不先做旧 checkpoint 的零训练见证；不加仅持有参考行；B02 不当作「已修复后重跑」。

## 理由

具体、已观测的动作交付障碍已在限定范围内被排除（A02：64/64 许可一致、12/12 准入按 native 投影采纳）。现在值得直接看：在修正边界上重新训练的联合预测包，能否比同边界上的原学习器带来有用的原生服务增量。最强反向事实保留：动作交付后短窗服务未增（60/64）、能量增加；B02 的 572/447/433/428 与 inside-MEI 读法继续成立，B03 无论正负都不翻转它。

## 对象要点

- 宿主不变（A03 地面终端）；两臂都用修正边界；差异只在 B02 的联合预测监督（NLL，系数 0.025）与 sigmoid 服务概率接口；NLL/协方差法则不变，不调系数不换目标。
- 种子 73：master = sha256("DISH-FORECAST-PACKAGE-B03/seed/73")；seed 61 的 master/checkpoint/结果不作输入。
- 每臂 65,536 普通训练转移、512 优化步、只用 update 16、四个评估条件、最多 4,800 评估 tick；全部计数与曲线必须来自新运行。
- 读法沿用 B02 的六行结构（有用信号 ≥ +24 → 可另预算 1–2 个独立配对种子；inside-MEI/异质 → 无清晰增益、不自动延长；adverse → 不以代理量续费；无合法换主 → incumbent-only；有换主 → 机会观察而非 SHADOW 优势；缺主测量 → 受损）。
- 启动前：不需要训练侧历史测量、A02 重跑或校准实验；只需一次与本改动和主输出相关的聚焦检查，并在节点上补齐 Windows 未收集的 `test_package.py`，不 stub 关键依赖。
- 成本：B02 的 642.66 s（一对）只是带边界的规划参考，不是每臂投影；每臂上限 1,800 s，共享准备成本各分摊一半；不重试、不换种子、不扩 cap。

## Pro 更正的两条 DM 表述

「没有 partner co-adaptation」不被材料支持（固定协议不等于固定学习关系，保留该解释）；重释里「新运动从未被采纳」对完整历史 B01/B02 只作源码支持的推断，两个窗口才是测量。

## 执行

DM 冻结 B03 卡与 CM 目标（Grok 实现薄入口，枢纽审阅），operator 在 wsl_4070 启动。详情：`docs/research/candidates/degraded_incumbent_shadow_handover/DISH_POST_A02_CONVERGENCE_INTAKE_20260906.md`；原文 `pro_packets/20260906_post_a02_convergence/archive/RESPONSE.md`（提交 d7710921）。

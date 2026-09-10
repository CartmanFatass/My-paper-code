# CM 直接实现 + 独立 reviewer

当前项目基线：Astra/medium CM 直接实现，Astra/high reviewer 独立审查。
无 implementer。默认一轮五类经典题＋随机一道非典型题，六题说明与源码开局全部可见。
代码题、Git 和检查真实执行；背景回执为明确标注的 synthetic 材料。

在 `C:/Projects/CodexBechmark/cm_direct_review/workspace` 打开新 session，说：

> 开始测试，seed=17

当前 session 就是 CM。它连续完成六题和杂务、调用真实 reviewer、保留无关改动并
完成本地 Git 交付。结束后自动生成 REPORT.md、独立评分和真实会话成本，无需创建 CM
子代理或手工粘贴下一题。[完整入口说明](../_shared/cm_tasks/QUICKSTART.md)。

实现与离线校准完成；候选模型试跑尚未发生。每次独立裁判单列成本，未完成或缺失
证据不按通过处理。预估难度尚未用实际模型成功率校准。

本项是 [spec 比较](../_shared/cm_tasks/SPEC_DESIGN.md) 的直接实现参照。
Terra/high、Luna/max CM 或其他 reviewer 组合是可选后续配置；入口不批量执行它们。
变更模型需要在新 session 启动前配置并核验实际运行设置，不能仅更改记录中的名称。
不得从一个两题流程宣称生产角色最优；生产配置不会随 benchmark 改动。

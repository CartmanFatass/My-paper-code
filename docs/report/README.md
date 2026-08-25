# HMASD 结论性迭代报告

本目录是面向用户的中文科学决策视图。每个有效的结论性迭代结束后，
Project Manager 必须在推进后继动作前直接写入：

```text
docs/report/ITERATION_<轮次>.md
iteration_report_language=zh-CN
separate_approval=not_required
additional_review=false
```

该动作处于用户的长期授权范围内，无需再次询问。报告至少包含：

1. 本轮科学问题与运行前冻结的决策；
2. 源码身份、实验环境、后端、线程、预算和比较组；
3. 证据闭合与登记结果；
4. 结果对猜想、算法方向和后续边界的影响；
5. 本轮结果不能支持的结论；
6. 剩余结论性迭代和下一最小动作。

报告不替代原始日志、正式分析、CDC 证据或设计合同，也不形成新的审批、
复审或验收层。正式结果仍由冻结的 first-match 规则和原始证据决定。

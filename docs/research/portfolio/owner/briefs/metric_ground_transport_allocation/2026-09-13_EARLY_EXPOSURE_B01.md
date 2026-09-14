# 问题

同样训练256 episodes，mean-COND 是否在一个新的原生训练实例中优于完整 DENSE？

# 预测

符号不确定，DM 首选预期为 MEI 内；owner 未作预测。

# 结果

唯一 master8241 完整完成：COND0.056117、DENSE0.040988，差+0.015129 J，高于卡片 MEI0.01。32个配对最终世界25正7负，但只有一个独立训练对。

# 边界

这是一个早期暴露点的局部支持，不是稳定优势、学习曲线或机制因果。历史正负结果不变，DENSE 仍为通用默认。

# 成本

完整原生188.19秒；450/450/900秒上限通过。支撑和全链成本仍有未测量尾项，合规 UNKNOWN。Monitor 一次过早中断判断已按正常退出原始记录纠正，没有重跑。

# 下一步

Convergence 完整设计 review 未发现实质缺陷；DM 已回应其解释边界，下一步决定独立256/256复现与方向去留，不请求生命周期批准。

[完整 E0](../../../../candidates/metric_ground_transport_allocation/MGTAP_EARLY_EXPOSURE_B01_RESULT_20260913.md)

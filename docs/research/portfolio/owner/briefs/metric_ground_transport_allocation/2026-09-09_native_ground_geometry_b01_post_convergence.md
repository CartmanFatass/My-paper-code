# metric_ground_transport_allocation · native ground-geometry B01 Convergence · 2026-09-09

## 问题
P75 的 REL 相对 DENSE 已完成且不利；现在是否继续尝试新的原生几何 actor？

## 机制与比较器
原生任务是五架 UAV 的速度控制。局部几何经信道、干扰、SINR、容量和关联进入团队奖励；DENSE 保留同样输入，是有效但未调参的比较器。H 只作诊断。

## 结果一句话
两主种子差异为 −0.04468 与 −0.00324，聚合 −0.02396，低于 −0.01；8202 的 inside-MEI 结果和 H 均保留。

## 预测核对
原预测是小幅或处于关注尺度内；无人值守时没有所有者预测，因此不补写预测分数。

## 排除了什么
结果不证明 DENSE 稳定更强、几何无效、等价、因果、收敛或部署价值；旧的配置坐标家族继续暂缓。

## 下一步与需要你做的
当前原生 ground-geometry actor family 可逆暂缓，新增暴露为零。重入须提出一个实质改变、同信息、同原生奖励和合格 generic comparator 的操作；仅把 mean 改 sum 或加一个未说明的 count 不够。整体方向仍 ACTIVE/MEDIUM。

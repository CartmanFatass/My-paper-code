# CM delegation-granularity 场景

用户接受测试时，在 workspace/ 使用全新顶层 session；该 session 就是 CM，
按 workspace/AGENTS.md 的一句话入口启动。CM 按本轮 L0–L3 与 fresh/reuse
真实生成交接，调用配置的 implementer 与独立 reviewer；不再创建 CM 子代理。

只操作本轮分发的源码与公开检查，不查看其他档位、历史正确 patch 或隐藏验收。
维护任务可读主持实现。当前实现已完成离线检查，尚未运行候选模型比较。
生产科研授权和预算不随题包继承。

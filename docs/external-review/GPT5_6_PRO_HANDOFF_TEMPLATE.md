# GPT-5.6 Pro Handoff Template

Replace only `<commit>` and `<question-path>`, then submit the complete text
verbatim to the designated GPT-5.6 Pro conversation. If automatic submission
is unavailable, give the same complete text to the user as the manual fallback.

```text
请通过 GitHub 插件读取私有仓库 CartmanFatass/My-paper-code 的 aggressive 分支，
以提交 <commit> 为准。本轮唯一审阅入口是：
<question-path>

请先完整阅读该文件及其中 “Repository files to inspect” 列出的材料，然后严格按
“Requested decision” 回答。不要只做摘要，不要跳过实现与结果 JSON，也不要通过调参、
扩种子或改阈值挽救已经退休的路线。

你在本轮是稀疏的收敛性对抗审阅者，而不是在每次 FAIL 后自动生成下一轮实验的控制器。
请先区分证据事实与推断，审查当前两到四个竞争性因果假设及区分它们所需的最小证据；
随后审查问题文件中的 final-capability map、replacement ledger（删除、保留、新增）
以及最强 ordinary-MARL 基线/反对意见。允许重排、合并或退休假设，也允许明确裁决为
停止、维持现状或先做跨轮架构审计，不必给出新算法。

只有当证据确实支持继续时，才选择至多一个当前应执行的高信息量证据源，并说明其每种
结果如何更新假设组合。不要要求唯一永久路线，也不要提出并行执行；不要用堆叠新模块
代替架构取舍，也不要把孤立 toy gate 的 PASS 直接解释为可集成。
```

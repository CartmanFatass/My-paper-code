# GPT-5.6 Pro Convergent Reviewer Handoff Template

Replace only `<commit>` and `<question-path>`, then submit the complete text
verbatim to the designated GPT-5.6 Pro conversation. If automatic submission
is unavailable, give the same complete text to the user as the manual fallback.

```text
请通过 GitHub 插件读取私有仓库 CartmanFatass/My-paper-code 的 aggressive 分支，
以提交 <commit> 为准。本轮唯一审阅入口是：
<question-path>

请先完整阅读该文件及其中 “Repository files to inspect” 列出的材料，然后严格按
“Requested decision” 回答，并遵循 `docs/project/ALGORITHM_PRINCIPLES.md` 与
`docs/external-review/CONVERGENT_REVIEW_PRINCIPLES.md`。请完成证据综合、候选权重、
下一证据源或停止决策，并保留有价值但未选择的想法。不要只做摘要，不要跳过实现与
结果 JSON，也不要通过调参、扩种子或改阈值挽救已经退休的路线。
```

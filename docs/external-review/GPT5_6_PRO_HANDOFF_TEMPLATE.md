# GPT-5.6 Pro Manual Handoff Template

Replace only `<commit>` and `<question-path>`, then give the complete text to the
user as a directly copyable prompt.

```text
请通过 GitHub 插件读取私有仓库 CartmanFatass/My-paper-code 的 aggressive 分支，
以提交 <commit> 为准。本轮唯一审阅入口是：
<question-path>

请先完整阅读该文件及其中 “Repository files to inspect” 列出的材料，然后严格按
“Requested decision” 回答。不要只做摘要，不要跳过实现与结果 JSON，不要提出并行
路线，也不要通过调参、扩种子或改阈值挽救已经退休的路线。请输出一个明确裁决、
可复用的因果结论，以及唯一下一条可证伪的算法路线和最小 abandonment gate。
```

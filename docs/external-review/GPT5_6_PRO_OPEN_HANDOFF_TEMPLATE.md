# GPT-5.6 Pro Open Reviewer Handoff Template

Create or reuse only the dedicated `HMASD Open Architecture Reviewer`
conversation. Do not use the convergent `HMASD Algorithm Consultation`
conversation for this turn.

```text
请通过 GitHub 插件读取私有仓库 CartmanFatass/My-paper-code 的 aggressive 分支，
以提交 <commit> 为准。本轮唯一入口是：
<question-path>

你是独立的 GPT-5.6 Pro 开放性算法审阅者，与 Gemini 发散审阅者具有同等地位，
但本轮必须保持盲化：不要读取任何 GEMINI_*_RAW、CODEX_SYNTHESIS、
PRO_CONVERGENT 或 DISPOSITION 文件。

请完整读取入口、00_REVIEW_BRIEF.md、01_SHARED_SOURCE_MANIFEST.md 及其中列出的
Git 可见材料，并遵循 `docs/project/ALGORITHM_PRINCIPLES.md` 与
`docs/external-review/OPEN_REVIEW_PRINCIPLES.md`。你可以推翻现有假设组合、提出
遗漏的结构性路线或判断普通 MARL 已经足够，但不要选择唯一后续路线、生成调参救援
或并行实现任务。区分仓库事实、文献证据和你的推断，并严格按入口中的 Requested
response 输出。不要修改仓库或启动实验。
```

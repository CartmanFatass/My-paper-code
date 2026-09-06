# 隔离恢复验证

所有者明确授权开始这两项验证；这不是科研裁决或规范审阅。
只使用当前 GitHub 连接器完成以下两项状态检查和条件交付。不要运行实验。

## 已有交付恢复

仓库 CartmanFatass/My-paper-code，分支 codex/pro-github-write-probe-20260905。
任务是恢复之前的 ROUNDTRIP_REVIEW.md 交付：
文件 docs/research/portfolio/collaboration_probe/ROUNDTRIP_REVIEW.md，
既有交付提交 2f8a08af920a8881832d89357b06065b87facf53，
Issue https://github.com/CartmanFatass/My-paper-code/issues/3 。
请实际读取目标和 Issue 评论，确定本轮既有文件与交付链接是否匹配。
若已匹配，复用已有固定文件和评论链接，不重新生成评审、提交或评论。
若缺失或归属无法确定，指出实际缺口，不猜正文也不替换文件。

## 目标内容冲突

仓库相同，隔离分支 codex/pro-github-recovery-probe-20260905。
目标 docs/research/portfolio/collaboration_probe/CONFLICT_TARGET.md。
期望本次交付正文恰为：

```text
# Requested recovery delivery
A new response for this isolated test.
```

写入契约：只有目标不存在才允许新增；目标已存在且逐字匹配则复用；
目标已存在但内容不匹配则报告冲突，不覆盖、不删文件、不创建替代路径或评论。
实际读取分支目标后选择对应处理，不能根据本提示的标题猜测状态。
不得改 main、其他分支、其他路径或科学状态；没有 force-push 权限。

最后聊天用简短自然语言分别报告实际读取结果、采用的处理、对应固定链接。
不回 JSON/任务ID/路由字段。Root 将独立比较分支head、原文件字节和评论集合。
本测试只覆盖已存在状态和已有冲突，不宣称覆盖检查后写入前的真实并发竞态。

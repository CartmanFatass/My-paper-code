这是所有者明确批准的一次 GitHub 写入能力测试，沿用当前 portfolio 会话，但不是科学裁决或代码实现。本次仅针对下面两个测试目标放开之前的只读要求；其他研究请求仍保持原边界。

请先检查你实际可调用的 GitHub 工具。只有读接口时，不尝试构造不存在的工具，不借助其他会话或要求提供凭据；直接简短说明无法完成哪些写操作。不要生成一篇研究报告。

仓库 CartmanFatass/My-paper-code；专用Issue：https://github.com/CartmanFatass/My-paper-code/issues/3 。先读取已有评论，避免重复。若存在写评论工具且已获连接权限，直接且仅一次发表以下文本：

Pro 直接写入能力测试：这条评论由当前 Pro 会话调用其 GitHub 写接口创建；它不包含科研结论。对应测试文件是 docs/research/portfolio/collaboration_probe/pro-write-check.md。

专用分支 codex/pro-github-write-probe-20260905 已由Root创建，基线 b11d1f212233ce28549d7896e4ab7ae06e158945。若存在文件写入工具且已获连接权限，先查该分支是否已有目标文件；若无，仅新增 docs/research/portfolio/collaboration_probe/pro-write-check.md，内容为以下两行（UTF-8，LF，末尾换行）：
# Pro GitHub write probe
This file is a connectivity test, not research evidence.

只提交该文件到上述测试分支，不合并main，不编辑已有文件，不创建新的分支、PR、账号或服务，不修改权限设置。提交消息：Pro GitHub connectivity probe。存在相同目标时只读回，不再写入；任何写入返回不确定先读取真实状态，不盲重试。若只有一类写能力，完成这一类并说明另一类缺失。

最后在聊天中仅返回实际评论链接、实际提交SHA/文件链接，以及未完成的能力；未写入不得声称成功。这里是测试证据所需链接，不是transport路由信息。请勿用一段“可复制评论/文件”代替实际操作；Root/Transport不会代写来冒充你写入。

本次无训练、评价、环境或科研工具运行，零新科学曝光。原科研执行继续，不等待此测试。
# GitHub 往返协作验证

## 已观察：上次直接写入

本会话通过自己的连接器读到[Issue 3正文](https://github.com/CartmanFatass/My-paper-code/issues/3)及[既有评论](https://github.com/CartmanFatass/My-paper-code/issues/3#issuecomment-5555607897)。[提交b86b9f71](https://github.com/CartmanFatass/My-paper-code/commit/b86b9f71ea22291b3a664249f93a14abaa2a8968)的变更清单和diff仅新增[pro-write-check.md](https://github.com/CartmanFatass/My-paper-code/blob/b86b9f71ea22291b3a664249f93a14abaa2a8968/docs/research/portfolio/collaboration_probe/pro-write-check.md)两行，读回内容与声明一致。作者显示为连接账号CartmanFatass，不是独立的Pro GitHub身份。这支持上次指定评论及单文件写入成功，不能推成全仓库权限或迁移完成。

## 已观察：脚本能力

固定版本`cd2695866`的[工具说明](https://github.com/CartmanFatass/My-paper-code/blob/cd2695866/.agents/skills/hmasd-scientific-tools/SKILL.md)要求先选定每个task、arm及独立训练run的endpoint。[summarize_runs.py](https://github.com/CartmanFatass/My-paper-code/blob/cd2695866/.agents/skills/hmasd-scientific-tools/scripts/summarize_runs.py)按task与arm分组，输出数量、均值、样本标准差、最小／最大值及逐seed分数；仅一个run时标准差为null。

指定baseline后，脚本按同task的共有seed计算“当前arm减baseline”，列出未匹配seed。它拒绝重复键、空标识、非有限score和空数据，输出JSON并可画点图，不计算区间、显著性或成功结论。这里是源码阅读，未运行脚本。

```csv
task,seed,arm,score
```

## 推论：独立性与迁移边界

同一训练策略的多次评价共享已训练参数，回答的是该策略在评价随机性下的表现，不是训练过程的变异。更换checkpoint或将episode编号写成seed也不会产生新的独立训练。脚本只按标签匹配，不能验证独立性或合法配对；这些需由实验设计说明。

本轮只检验限定分支文件与Issue链接往返。尚不能声称Root已直接读回并核验本review字节、Unicode与Markdown，或已验证重复通知和并发变更下的不重复写入；PR评审、合并及全流程迁移同样未验证。文件与评论成功也不证明分析包已安装、脚本运行正确或科研结论有效。本次未运行训练、评价、benchmark或性能测试。

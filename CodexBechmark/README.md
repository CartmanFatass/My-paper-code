# CodexBechmark

独立 Codex 测试集合，实际安装在 `C:/Projects/CodexBechmark`。在所选场景的
`workspace` 打开**全新 session**；当前 session 就是被测角色。

| 场景 | 测试目标 | 入口 |
| --- | --- | --- |
| [root_delegation](root_delegation/README.md) | 持续委派、升级与验收 | 原 runner 和协议保持原样 |
| [cm_delegation_granularity](cm_delegation_granularity/README.md) | spec 颗粒度和范例复用 | `cm_delegation_granularity/workspace` |
| [cm_direct_review](cm_direct_review/README.md) | 当前项目的 CM 直接实现基线 | `cm_direct_review/workspace` |

CM 场景打开后说 **“开始测试”** 即可；委派场景可说 **“开始测试，L2 reuse，seed=17”**。
两种 CM 入口均默认 `--suite five-plus-one`：五类经典题＋随机一道非典型题，
六题说明和源码开局全部可见，同一 CM 一轮完成24个检查点，最后统一评分与计费。
旧两题模式需显式指定 `--suite pair`；已有冻结运行保持原协议。
同一 CM 连续完成代码、真实子代理审查、回执和 Git 杂务；结束后自动独立评分并提取成本。
入口不会创建第二个 CM，也不会自动展开配置矩阵。详见 [启动说明](_shared/cm_tasks/QUICKSTART.md)。
完整过程和数据如何统计见 [两项 CM 测试操作文档](_shared/cm_tasks/OPERATING_GUIDE.md)。

代码题、投递、留档和自动收尾已实现并通过离线检查。尚未运行候选模型比较；
预估难度、策略优劣和自动流程的真实候选运行效果都没有实测结论。

HMASD 内同名目录是版本管理副本，实际测试在仓库外目录进行，避免加载 HMASD 项目指令。
个人全局配置仍可能生效；目录分离和 `_host` 访问约定不是 OS 级保密隔离。
更新只同步维护文件，保留既有运行数据。CM 新运行位于
`<scene>/workspace/<run-id>` 和 `<scene>/workspace/_host/runs/<run-id>`；
root_delegation 的既有 `_host/runs` 与 `workspace/responses` 不受影响。

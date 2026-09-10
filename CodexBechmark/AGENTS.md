# CodexBechmark 通用入口

本目录是多场景测试集合，不是HMASD研究工作流。只根据用户指定的场景进入其
`workspace/`并读取该场景AGENTS；例如root delegation对应
`root_delegation/workspace/`。用户未指定场景时只读顶层README并询问场景，不默认
启动root_delegation，不依次执行全部测试。不同场景遵循各自协议，不套用其他测试规则。

被测会话不得浏览其他场景、评分答案或主持材料。记录保存在所属场景中，不混用run。

如果用户明确要求维护benchmark实现，而不是接受测试，此候选访问限制不适用于
维护任务；维护者必须与被测会话分开，不把已读评分答案的会话作为有效候选。

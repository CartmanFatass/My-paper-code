# v3 独立审核实际阅读记录

审核工作区：C:/Projects/HMASD。审核期间 HEAD 一直为 `c463c03766f88cfc7c37d978bf9583cabfe52e3c`。2026-09-09 01:53:38 UTC 结束字节复核：本表 179 个候选路径全部仍与起始库存 SHA-256 相同。已有未跟踪文件也按其实际工作区字节记录，不宣称全表均已提交或构成一个原子 Git 快照。

本次 **172 个文件全文阅读**（1,393,472 字节）；**7 个文件只核对状态/入口/清单**，不计入全文。候选集合共 1,825,300 字节。长文件按连续片段实际读取；可见输出截断处补读。目录枚举和引用搜索用于扩展范围，不替代正文阅读。

范围从旧 149 文件清单出发，对当前目录逐项核对；`.codex/hmasd-portfolio.toml` 已删除，没有把其旧内容算作当前配置。补入当前合并/修复记录、paused handoff、owner 实现与回归测试、直接运行/资源/平台/输出脚本和 schema、能力目录，以及现行 Claude 入口实际依赖但未跟踪的归档 helper。未递归阅读全部方向科学卡/证据、实验代码、日志或外部文献；历史记录中的命令没有被执行。

已读取 [确定无人机实验场景](codex://threads/01a07e71-4afd-7b20-a5ac-d776cd7b2da5) 的最近 16 个回合中的实际用户/最终答复作为补充上下文；不是该任务全部历史/工具输出的全文审计。没有缺少本次结论所需的可访问对话事实。没有运行单元测试、科学实验或真实 Pro 行为测试。只读 owner pending 查询返回空列表；未验证外部 UI/远端执行/所有存量会话的实际加载状态。

本表的“全文”只陈述阅读范围，不表示该文件具有当前规范权威；历史、兼容、测试与 vendor 材料的地位由入口和当前 owner/spec 决定。审核结论见 [独立报告](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/INDEPENDENT_REVIEW_V3_CONTROL_PLANE.md)。

| 文件 | 字节 | 行数 | SHA-256 | 本次阅读 |
| --- | ---: | ---: | --- | --- |
| [.agents/skills/hmasd-chatgpt-pro-transport/agents/openai.yaml](C:/Projects/HMASD/.agents/skills/hmasd-chatgpt-pro-transport/agents/openai.yaml) | 289 | 4 | `8D2A49CE198D4C9B1DDCB7896E6E8FB0D9E53EB569099E9140D900731C8D7C72` | 全文 |
| [.agents/skills/hmasd-chatgpt-pro-transport/references/attachment-compatibility.md](C:/Projects/HMASD/.agents/skills/hmasd-chatgpt-pro-transport/references/attachment-compatibility.md) | 1232 | 24 | `AEA0B86600A3DEAB44BB4AAD9051DAA9E24DB1664A4AD974A79C3F4737AC2485` | 全文 |
| [.agents/skills/hmasd-chatgpt-pro-transport/references/attachment-send.md](C:/Projects/HMASD/.agents/skills/hmasd-chatgpt-pro-transport/references/attachment-send.md) | 1774 | 27 | `E3A92B94CF01A8A5E91FF478AC4D575C2F59DFA2C90A4E14A887510882FE52BB` | 全文 |
| [.agents/skills/hmasd-chatgpt-pro-transport/references/provider-context-replacement.md](C:/Projects/HMASD/.agents/skills/hmasd-chatgpt-pro-transport/references/provider-context-replacement.md) | 2448 | 35 | `FCD8C2B9E8A987412C0407023B7DEF4C5BA32F43A7129CBE09F059E8F6B7A73A` | 全文 |
| [.agents/skills/hmasd-chatgpt-pro-transport/references/send-hit-point-recovery.md](C:/Projects/HMASD/.agents/skills/hmasd-chatgpt-pro-transport/references/send-hit-point-recovery.md) | 1749 | 28 | `0D3CC6B53C475792B437FDE6E97F3BBAAED2864F4547507E885EDDF720DA0FCC` | 全文 |
| [.agents/skills/hmasd-chatgpt-pro-transport/references/state-schema.md](C:/Projects/HMASD/.agents/skills/hmasd-chatgpt-pro-transport/references/state-schema.md) | 16945 | 319 | `D9DECB1C1D5CC4A3C13ED5BE94899BEA9C322773C1937DAB68D6E8842C35A4B2` | 全文 |
| [.agents/skills/hmasd-chatgpt-pro-transport/scripts/bind_conversation.py](C:/Projects/HMASD/.agents/skills/hmasd-chatgpt-pro-transport/scripts/bind_conversation.py) | 46309 | 973 | `69F777DDADC5F1D97698789E4C8BE5915E050E759B5A57657BAC4354A111CFEF` | 全文 |
| [.agents/skills/hmasd-chatgpt-pro-transport/scripts/materialize_packet.py](C:/Projects/HMASD/.agents/skills/hmasd-chatgpt-pro-transport/scripts/materialize_packet.py) | 4617 | 131 | `C5046ADE4098F88F99FE7AD2E9BDC57FCF30C90A327B1E82CFDFFAAEC849A650` | 全文 |
| [.agents/skills/hmasd-chatgpt-pro-transport/scripts/transport_contract.py](C:/Projects/HMASD/.agents/skills/hmasd-chatgpt-pro-transport/scripts/transport_contract.py) | 36933 | 873 | `2CFDD8EEFCA092AE59CE2362E75D8D2E6826D7B56AEE8DD5EA01A232E26DF0BF` | 全文 |
| [.agents/skills/hmasd-chatgpt-pro-transport/scripts/validate_request.py](C:/Projects/HMASD/.agents/skills/hmasd-chatgpt-pro-transport/scripts/validate_request.py) | 16789 | 335 | `8BEDE2BD066133AC69517AA68F85BAA849E9C93A1FE4CBA5F62EFC3755244EF7` | 全文 |
| [.agents/skills/hmasd-chatgpt-pro-transport/SKILL.md](C:/Projects/HMASD/.agents/skills/hmasd-chatgpt-pro-transport/SKILL.md) | 25077 | 362 | `02D9E7A2DE40580ABFB8DF4DF24F2C7A20DA4D0493632A48E0E34C4BAE3AB1C9` | 全文 |
| [.agents/skills/hmasd-loop-dispatch/SKILL.md](C:/Projects/HMASD/.agents/skills/hmasd-loop-dispatch/SKILL.md) | 3772 | 57 | `6294B3438E33289A31265C09BC6E31C04F7AC56715ACEFEF124BF2CA57CA190F` | 全文 |
| [.agents/skills/hmasd-owner-item/SKILL.md](C:/Projects/HMASD/.agents/skills/hmasd-owner-item/SKILL.md) | 6316 | 102 | `6620BCD3B6F0E7F75412D4255718099536C05DD9889D9ABCAE3BDF0D26748CA9` | 全文 |
| [.agents/skills/hmasd-portfolio-task/SKILL.md](C:/Projects/HMASD/.agents/skills/hmasd-portfolio-task/SKILL.md) | 13644 | 192 | `F20E6DF39EBC510FCFEF05698E4EC1F317BC55DC0F82155E4BA25D9FE2C8C9D3` | 全文 |
| [.agents/skills/hmasd-pro-research-prompt-author/agents/openai.yaml](C:/Projects/HMASD/.agents/skills/hmasd-pro-research-prompt-author/agents/openai.yaml) | 263 | 4 | `5229CF8EC3814CEC1ACA58B3FD8D7132578793DED9FD56D5045981A807B5513E` | 全文 |
| [.agents/skills/hmasd-pro-research-prompt-author/references/attachment-delivery.md](C:/Projects/HMASD/.agents/skills/hmasd-pro-research-prompt-author/references/attachment-delivery.md) | 3158 | 51 | `AE7E91D0761AA220D915A989CCCF17F2375C1C01FD24B79E2EC68417E637AE1B` | 全文 |
| [.agents/skills/hmasd-pro-research-prompt-author/references/github-connector-contract.md](C:/Projects/HMASD/.agents/skills/hmasd-pro-research-prompt-author/references/github-connector-contract.md) | 1965 | 32 | `66D9BACA3DB9142E4168F84D604AF67927ED173AFC8AD163F4AC45D18F643471` | 全文 |
| [.agents/skills/hmasd-pro-research-prompt-author/references/github-delivery.md](C:/Projects/HMASD/.agents/skills/hmasd-pro-research-prompt-author/references/github-delivery.md) | 3960 | 53 | `730CC6AE051722A692FD78B35B3C715EA62A840FB71492E54D1B156F1E070429` | 全文 |
| [.agents/skills/hmasd-pro-research-prompt-author/scripts/render_packet.py](C:/Projects/HMASD/.agents/skills/hmasd-pro-research-prompt-author/scripts/render_packet.py) | 55889 | 1051 | `9DC922478D6ED0EB4C7C8603B42AB16CA283B5DC2F6C8854186CF281F95F4389` | 全文 |
| [.agents/skills/hmasd-pro-research-prompt-author/SKILL.md](C:/Projects/HMASD/.agents/skills/hmasd-pro-research-prompt-author/SKILL.md) | 7832 | 108 | `B405E9B200E880F04FC0CAF61749978FEFEED8CED94F338E8431B989BB9DB2CC` | 全文 |
| [.agents/skills/hmasd-scientific-tools/references/adapters.md](C:/Projects/HMASD/.agents/skills/hmasd-scientific-tools/references/adapters.md) | 2749 | 26 | `80FA0C2BD29792C3CB62BFB6549C2F062BE8C24F4D502158B10DF61BB3029A2E` | 全文 |
| [.agents/skills/hmasd-scientific-tools/references/local-literature.md](C:/Projects/HMASD/.agents/skills/hmasd-scientific-tools/references/local-literature.md) | 3875 | 59 | `6FDD8DFBCA65EB43A67843E14B7DD5409976FDA030501E5D43FACDBD7F4D6D17` | 全文 |
| [.agents/skills/hmasd-scientific-tools/scripts/summarize_runs.py](C:/Projects/HMASD/.agents/skills/hmasd-scientific-tools/scripts/summarize_runs.py) | 4261 | 89 | `E918965E5B63D0C9D5B99F555DCD86143D838F952037611A616B24F506CD08D9` | 全文 |
| [.agents/skills/hmasd-scientific-tools/SKILL.md](C:/Projects/HMASD/.agents/skills/hmasd-scientific-tools/SKILL.md) | 4390 | 64 | `0A31254A2A928C21463D4CCF230048E1B2671FAAC3278CE3FD2D2523FB9D99FF` | 全文 |
| [.agents/skills/hmasd-workflow-outsource/agents/openai.yaml](C:/Projects/HMASD/.agents/skills/hmasd-workflow-outsource/agents/openai.yaml) | 247 | 4 | `6CCF91196ADA30EBDF95086EFAA3ADDAE7E2A5FFE77034D8BFFBA8B87A7E5764` | 全文 |
| [.agents/skills/hmasd-workflow-outsource/references/prompt-template.md](C:/Projects/HMASD/.agents/skills/hmasd-workflow-outsource/references/prompt-template.md) | 4077 | 65 | `95DFDCADC232CDC50CC1C5A1DE4A9A879E629E4978EB4368C173300466536178` | 全文 |
| [.agents/skills/hmasd-workflow-outsource/SKILL.md](C:/Projects/HMASD/.agents/skills/hmasd-workflow-outsource/SKILL.md) | 5823 | 97 | `DB5727F68353917B43737E41D07F1A81798C5BDFB80651A5BB293650E1FDFA48` | 全文 |
| [.agents/third_party/ask-matt/agents/openai.yaml](C:/Projects/HMASD/.agents/third_party/ask-matt/agents/openai.yaml) | 137 | 5 | `BDFFBC5A0A99ED1B6EF3253D251D755FD18162B9845972E380007F844B09B05C` | 全文 |
| [.agents/third_party/ask-matt/PHASE-BOUNDARIES.md](C:/Projects/HMASD/.agents/third_party/ask-matt/PHASE-BOUNDARIES.md) | 4249 | 55 | `A8AA20158609EF39E2B308B6BA0660C91066838D07A867202E63A7744A88A3ED` | 全文 |
| [.agents/third_party/ask-matt/SKILL.md](C:/Projects/HMASD/.agents/third_party/ask-matt/SKILL.md) | 11264 | 89 | `7CC10CBBE9374EEF21C1E99476EAEADC476127E3748B4C669A76DA3623A91F18` | 全文 |
| [.agents/third_party/grill-me/agents/openai.yaml](C:/Projects/HMASD/.agents/third_party/grill-me/agents/openai.yaml) | 153 | 5 | `0E075AB3297271C8E5CAEC3CDF138F7F15815B3467A502C6DD6A59357016B3AE` | 全文 |
| [.agents/third_party/grill-me/SKILL.md](C:/Projects/HMASD/.agents/third_party/grill-me/SKILL.md) | 503 | 11 | `35266CE08D93F24B8167AF270617537FEB48C295D17E2CC9F06F11AF7DCCDF5C` | 全文 |
| [.agents/third_party/grilling/agents/openai.yaml](C:/Projects/HMASD/.agents/third_party/grilling/agents/openai.yaml) | 113 | 3 | `1411D7DF7D99B7E621A1FF8283C8133CC2464BE63D064E52D8CE169C6800EE9B` | 全文 |
| [.agents/third_party/grilling/SKILL.md](C:/Projects/HMASD/.agents/third_party/grilling/SKILL.md) | 1987 | 28 | `10FF989E7498B23B5ACB49D5048F11DCD906757D2F79C5CDF8A00001381296F2` | 全文 |
| [.agents/third_party/implement/agents/openai.yaml](C:/Projects/HMASD/.agents/third_party/implement/agents/openai.yaml) | 139 | 5 | `8970A8596ADE0C28AB427F41A4EA242D6BDF6186C59EBF55E1238DBECAAB79DC` | 全文 |
| [.agents/third_party/implement/SKILL.md](C:/Projects/HMASD/.agents/third_party/implement/SKILL.md) | 435 | 14 | `A27EEF09F1A3EB0B58F852C07D7E29C9114E2F8A83B9D01273292D35A7A7C880` | 全文 |
| [.agents/third_party/setup-matt-pocock-skills/agents/openai.yaml](C:/Projects/HMASD/.agents/third_party/setup-matt-pocock-skills/agents/openai.yaml) | 152 | 5 | `9527DE0110541C45712319025155AEAB8DC7D77C6ED6E5E83271BAB1851AB939` | 全文 |
| [.agents/third_party/setup-matt-pocock-skills/domain.md](C:/Projects/HMASD/.agents/third_party/setup-matt-pocock-skills/domain.md) | 2033 | 51 | `EDC6D6131FDFFC4B7135704F5262124FC43355C95F61B7399DC5A4DB643E28CA` | 全文 |
| [.agents/third_party/setup-matt-pocock-skills/issue-tracker-github.md](C:/Projects/HMASD/.agents/third_party/setup-matt-pocock-skills/issue-tracker-github.md) | 3731 | 45 | `AFD6852A80185217BD28AA5CBE456BEF1E85BE25BE7BD1FBA382D5B8EE428325` | 全文 |
| [.agents/third_party/setup-matt-pocock-skills/issue-tracker-gitlab.md](C:/Projects/HMASD/.agents/third_party/setup-matt-pocock-skills/issue-tracker-gitlab.md) | 3809 | 46 | `EA175F73D193B3F55819C0ED9BBCCF6EE0E70AD8F928E3D7607596C53380ACD6` | 全文 |
| [.agents/third_party/setup-matt-pocock-skills/issue-tracker-local.md](C:/Projects/HMASD/.agents/third_party/setup-matt-pocock-skills/issue-tracker-local.md) | 1810 | 30 | `7DCDA20A2EB4BDC89B95D1143423C0691309921CADAE3132E6424F371030506E` | 全文 |
| [.agents/third_party/setup-matt-pocock-skills/SKILL.md](C:/Projects/HMASD/.agents/third_party/setup-matt-pocock-skills/SKILL.md) | 6810 | 115 | `6D45AC98243520AD673BAD8078FD77EEFD6A817D2A36023963B2A00096571EC3` | 全文 |
| [.agents/third_party/setup-matt-pocock-skills/triage-labels.md](C:/Projects/HMASD/.agents/third_party/setup-matt-pocock-skills/triage-labels.md) | 1045 | 15 | `4F53C9B40CE2651E3611AA090EAEDBD6DBC9B71EF8C5F7E65EAC0D8263190D0D` | 全文 |
| [.agents/third_party/tdd/agents/openai.yaml](C:/Projects/HMASD/.agents/third_party/tdd/agents/openai.yaml) | 87 | 3 | `EA6F01CF1B8C06A4B0F5B649D74B1B8CE8685E72AF1B38D70D877693E092AF0B` | 全文 |
| [.agents/third_party/tdd/mocking.md](C:/Projects/HMASD/.agents/third_party/tdd/mocking.md) | 1481 | 59 | `3CEB807FDF4A47D6A93D4D9A891E5BA6D362A6247BD08ADC451FEEBFC17361EF` | 全文 |
| [.agents/third_party/tdd/SKILL.md](C:/Projects/HMASD/.agents/third_party/tdd/SKILL.md) | 3519 | 38 | `CB0E6F75D555675447C19A9782070BC757604911FABC3D7FED4EC1768C76E3C4` | 全文 |
| [.agents/third_party/tdd/tests.md](C:/Projects/HMASD/.agents/third_party/tdd/tests.md) | 2214 | 77 | `859F9E592C188FDA4FC7277DD180E4CE9C7A2E13F6EFE1F6F29ECCC9D28C106A` | 全文 |
| [.agents/third_party/to-spec/agents/openai.yaml](C:/Projects/HMASD/.agents/third_party/to-spec/agents/openai.yaml) | 135 | 5 | `1C5B4D1E3D8E52287EF19CC2742FDBBFAE1914AC75D33AF3E4C8174F08CC55BB` | 全文 |
| [.agents/third_party/to-spec/SKILL.md](C:/Projects/HMASD/.agents/third_party/to-spec/SKILL.md) | 3012 | 74 | `13C5B992D278AA49F366E6BAA8ACF76E99E130E7A80CA9B813FF20FF9528E617` | 全文 |
| [.agents/third_party/to-tickets/agents/openai.yaml](C:/Projects/HMASD/.agents/third_party/to-tickets/agents/openai.yaml) | 146 | 5 | `21BC6215FFFCD7614E9F772BB1760E87CC5FC7DCC707E7D282BC9414267A6090` | 全文 |
| [.agents/third_party/to-tickets/SKILL.md](C:/Projects/HMASD/.agents/third_party/to-tickets/SKILL.md) | 5640 | 104 | `611FF3528BBF210D964C794F1994C0343B03E27BE9BACC70794727D1104A7F06` | 全文 |
| [.claude/agents/hmasd-clerk.md](C:/Projects/HMASD/.claude/agents/hmasd-clerk.md) | 3639 | 50 | `B5728477FDF69B7580D406DA7F645539A54A3A15DBD993E7B57EDF6648201BF1` | 全文 |
| [.claude/agents/hmasd-cm-scout.md](C:/Projects/HMASD/.claude/agents/hmasd-cm-scout.md) | 1525 | 23 | `5B5E8A2FDF8CAAE1F7137FB0AFC53C2A6CC9590FAF927A465661A02214F71A57` | 全文 |
| [.claude/agents/hmasd-cm.md](C:/Projects/HMASD/.claude/agents/hmasd-cm.md) | 6655 | 101 | `245B04B9B410F31E79FE24D493ABC0567D81334AF0D43992847BC77EEC99B688` | 全文 |
| [.claude/agents/hmasd-experiment-operator.md](C:/Projects/HMASD/.claude/agents/hmasd-experiment-operator.md) | 3952 | 58 | `25639AA6D7ED5478DD14F9FF20E50F2C1FDF0DF8E60CBB57151C7D59F1E0EDCA` | 全文 |
| [.claude/agents/hmasd-experiment-tracker.md](C:/Projects/HMASD/.claude/agents/hmasd-experiment-tracker.md) | 3610 | 59 | `9D9AE821A9E7DF8545D8899E941E7EC06D5FB98B51FD95367819E7C8A974E0FF` | 全文 |
| [.claude/agents/hmasd-pro-transport.md](C:/Projects/HMASD/.claude/agents/hmasd-pro-transport.md) | 14608 | 187 | `204F2ABFFF9AAAEACFDCE3DA26FDD14E1781162BA33B6722B59C0F5CBF959253` | 全文 |
| [.claude/agents/hmasd-research-critic.md](C:/Projects/HMASD/.claude/agents/hmasd-research-critic.md) | 3098 | 44 | `1CBE18AB4B44DB3A3D3D593DEBF7C9B0B9F87F8112ECD584525847C741CB14B7` | 全文 |
| [.claude/agents/hmasd-research-scout.md](C:/Projects/HMASD/.claude/agents/hmasd-research-scout.md) | 2115 | 33 | `7FFA81FF5653A10B2A9FCCC8D056F15A6A150997DD054CED961863B5E15D029A` | 全文 |
| [.claude/agents/hmasd-reviewer.md](C:/Projects/HMASD/.claude/agents/hmasd-reviewer.md) | 2494 | 36 | `DCF8A191DFA87352A7C3F57088E316C378115FEB850B30BD950CC6703F2CADCE` | 全文 |
| [.claude/agents/hmasd-routine-implementer.md](C:/Projects/HMASD/.claude/agents/hmasd-routine-implementer.md) | 2447 | 36 | `731C6EB1290B3EC8590D50CAE9140A6B30C039612C1030C908FFEE5CBFDBE29A` | 全文 |
| [.claude/agents/hmasd-verifier.md](C:/Projects/HMASD/.claude/agents/hmasd-verifier.md) | 2344 | 36 | `75AAC340CB092492D2FB383AA98FE83AB5794F3A6C733B2CCF00CA22E6A9FE1A` | 全文 |
| [.claude/settings.json](C:/Projects/HMASD/.claude/settings.json) | 201 | 12 | `DE9E49BD035E7B267A4A0DA7EC7FD813CF1F830E2C4318E57A7B41F74D257FD7` | 全文 |
| [.claude/skills/hmasd-grok-cm/SKILL.md](C:/Projects/HMASD/.claude/skills/hmasd-grok-cm/SKILL.md) | 7228 | 91 | `018DAD37E74E78196C0643BF72B2ECACEDD59E39C970283CAF9665AD20E2D4AB` | 全文 |
| [.claude/skills/hmasd-pro-transport/SKILL.md](C:/Projects/HMASD/.claude/skills/hmasd-pro-transport/SKILL.md) | 12495 | 157 | `6461299C90B5ABF000C7791A4E976B6D8F5B67A7741CBDF44A20A21281D9488E` | 全文 |
| [.claude/skills/hmasd-research-hub/SKILL.md](C:/Projects/HMASD/.claude/skills/hmasd-research-hub/SKILL.md) | 9353 | 129 | `D5303D7EB41B24034AF7694F31E7BE94F8A64ACBCB09CE029A04BA939316C32D` | 全文 |
| [.codex/agents/hmasd-cm-scout.toml](C:/Projects/HMASD/.codex/agents/hmasd-cm-scout.toml) | 1777 | 26 | `2F8E327C2BB9BD88230DC21D838E8EEECF840513111493EA9118BC251EB44482` | 全文 |
| [.codex/agents/hmasd-cm.toml](C:/Projects/HMASD/.codex/agents/hmasd-cm.toml) | 12833 | 170 | `1A96FFE1B5D76281A4DE0085B0592050A5431941014D4368B8F01063A71E67B7` | 全文 |
| [.codex/agents/hmasd-direction-manager.toml](C:/Projects/HMASD/.codex/agents/hmasd-direction-manager.toml) | 16670 | 215 | `8289AE6A31F82101183FE0C64C92D7EE5138AB7471CCFF5F89CDF7F5CE97239D` | 全文 |
| [.codex/agents/hmasd-experiment-operator.toml](C:/Projects/HMASD/.codex/agents/hmasd-experiment-operator.toml) | 3228 | 45 | `7BD64D393A356D49A5F068EE1ABAAFF4A78A51980D79F3ABD4A3568E4379C056` | 全文 |
| [.codex/agents/hmasd-implementer.toml](C:/Projects/HMASD/.codex/agents/hmasd-implementer.toml) | 5239 | 70 | `086760DCEDCE834B03534CDE1E802352F078238C24B7B5D0521C7383C75A3C04` | 全文 |
| [.codex/agents/hmasd-research-critic.toml](C:/Projects/HMASD/.codex/agents/hmasd-research-critic.toml) | 2949 | 43 | `1029A9F14790F875773633ED5032BDCD397B8A2944814E58DDD9CB4379174AD5` | 全文 |
| [.codex/agents/hmasd-reviewer.toml](C:/Projects/HMASD/.codex/agents/hmasd-reviewer.toml) | 3410 | 45 | `FB8EC7051B97E2CE7EE7758599F3006CC5FE8CC4A86C9FB2A23CDD0A2181154D` | 全文 |
| [.codex/agents/hmasd-routine-implementer.toml](C:/Projects/HMASD/.codex/agents/hmasd-routine-implementer.toml) | 3621 | 46 | `48540606059FC95F0CD5265B967DFDAFEE0C4A62C1F8147CC459DC9D9F9F85F6` | 全文 |
| [.codex/agents/hmasd-verifier.toml](C:/Projects/HMASD/.codex/agents/hmasd-verifier.toml) | 2726 | 39 | `3848A123EA27F8F83EF3FBB21AD9D60E97736A694B8B273C78CFC4C55D62D03E` | 全文 |
| [.codex/config.toml](C:/Projects/HMASD/.codex/config.toml) | 1989 | 56 | `FB0FCA273CBB9359C21C3A4362D71E2827F8432E8709018CE600692BB8EE5D79` | 全文 |
| [.codex/hmasd-compute.toml](C:/Projects/HMASD/.codex/hmasd-compute.toml) | 1670 | 58 | `F2B6953EA409AB53532549D4E84BC2B74AFFA3F1EC3C70890EC3208C762DEB3E` | 全文 |
| [.codex/hmasd-monitor.toml](C:/Projects/HMASD/.codex/hmasd-monitor.toml) | 593 | 10 | `CD054A9B14A3139233A455F2BBFF687508F359E439A335B06F314D23BDAF60F2` | 全文 |
| [.codex/hmasd-transport.toml](C:/Projects/HMASD/.codex/hmasd-transport.toml) | 1089 | 28 | `9B62932EA5A308CDCA58A3C031852B0B0DF5CCD504186D2E13442F5047F909E4` | 全文 |
| [AGENTS.md](C:/Projects/HMASD/AGENTS.md) | 42326 | 548 | `E0272A7B0741B27DC69C9D5A86485242B664F1D43032DB3AF875792380DE4EBA` | 全文 |
| [CLAUDE.md](C:/Projects/HMASD/CLAUDE.md) | 9460 | 142 | `498FF8A2250CDEF1DA8DEDEFCD75D3D06EE117BB7E2BFAC4E9C72AA430FD4C67` | 全文 |
| [configs/scientific-capabilities-v1.toml](C:/Projects/HMASD/configs/scientific-capabilities-v1.toml) | 2180 | 58 | `28CEEDAB8D014B8A9E725DF4261E6B4B079E9BCEFEB28F36D36A844EC083B95E` | 全文 |
| [docs/AGENTS.md](C:/Projects/HMASD/docs/AGENTS.md) | 2564 | 30 | `335A3F67D9EC41B94BAF82100DA40B00EF857B95D4D2E490839F3120409C30D3` | 全文 |
| [docs/CLAUDE.md](C:/Projects/HMASD/docs/CLAUDE.md) | 12 | 1 | `D631D88045F74623D568ADFB4783B72E3D1B732330D749BC6C72E6648D4581D3` | 全文 |
| [docs/project/ALGORITHM_PRINCIPLES.md](C:/Projects/HMASD/docs/project/ALGORITHM_PRINCIPLES.md) | 17940 | 316 | `1F6ACC3E607E77AC5F2B6532E562687E7E35E6F56839CF73A3E01D78F447C177` | 全文 |
| [docs/project/ASTRA_WORKFLOW_CALIBRATION_20260906.md](C:/Projects/HMASD/docs/project/ASTRA_WORKFLOW_CALIBRATION_20260906.md) | 3625 | 56 | `A1F5D75DBA618B5969AF3E196065688C8D4CBC0A075565E2661D973A5DE57F76` | 全文 |
| [docs/project/BRANCH_CONSOLIDATION_20260907.md](C:/Projects/HMASD/docs/project/BRANCH_CONSOLIDATION_20260907.md) | 3450 | 47 | `6201E18A8F61DD580A6D618F1E2A48B2418D8F9A1F912033B3019858DF78927A` | 全文 |
| [docs/project/BRANCH_FINAL_CONVERGENCE_20260907.json](C:/Projects/HMASD/docs/project/BRANCH_FINAL_CONVERGENCE_20260907.json) | 3811 | 77 | `F827251291A65CDD0ED330075F340350881BCAE9AFBBC53D87693C523CCC08C1` | 全文 |
| [docs/project/BRANCH_FINAL_CONVERGENCE_20260907.md](C:/Projects/HMASD/docs/project/BRANCH_FINAL_CONVERGENCE_20260907.md) | 4915 | 74 | `5385BE4B2DB087B2043CA50EABC7F825D752D00F1EB0CED40DC5D1B0782FB4C1` | 全文 |
| [docs/project/BRANCH_VERIFICATION_20260907.json](C:/Projects/HMASD/docs/project/BRANCH_VERIFICATION_20260907.json) | 73414 | 1513 | `E6890BCB15292B3E1E619CB9C8E5CA664D8B858FF06A235E29F97737AB9C655B` | 1–30 行；历史分支审计数据，另全文读其解释 md；未逐条重审旧分支 |
| [docs/project/BRANCH_VERIFICATION_20260907.md](C:/Projects/HMASD/docs/project/BRANCH_VERIFICATION_20260907.md) | 10969 | 134 | `02493EE20FFAEB828F2CE011DE7E4E17F6C7D488C7853C47B68A1FE1DA4CA4F9` | 全文 |
| [docs/project/CM_MODEL_COMPARISON_20260907.md](C:/Projects/HMASD/docs/project/CM_MODEL_COMPARISON_20260907.md) | 19165 | 248 | `1CB2EAC9792566304B1C1E0757369AF8F6DA896ED739148EF63C76AAE2C04CF6` | 全文 |
| [docs/project/CPP_BATCHED_ENVIRONMENT_PRODUCTION_POLICY_V1.md](C:/Projects/HMASD/docs/project/CPP_BATCHED_ENVIRONMENT_PRODUCTION_POLICY_V1.md) | 26402 | 467 | `FD2F0FADBE591FACB03F403A8A3D7FA852FF7DD13D1E115C2A8853E7574CE32A` | 全文 |
| [docs/project/EFFICIENCY_PRACTICES.md](C:/Projects/HMASD/docs/project/EFFICIENCY_PRACTICES.md) | 7482 | 160 | `86E26349606992247C7348F009D85CFE3F183F91E982824BE103B2B5353CBCCD` | 全文 |
| [docs/project/ENGINEERING_ADDITIONS.md](C:/Projects/HMASD/docs/project/ENGINEERING_ADDITIONS.md) | 4166 | 78 | `5C64EF8442629DE829D1AE589D01D47866A776101AAB6B5815C36F635C7E5E56` | 全文 |
| [docs/project/ENGINEERING_SCOPE_SPEC.md](C:/Projects/HMASD/docs/project/ENGINEERING_SCOPE_SPEC.md) | 16818 | 180 | `769BD85934012E079FBF39A1B045E1B902F3ECF9026AE517907D5A09FF211052` | 全文 |
| [docs/project/EXPERIMENT_MONITOR.md](C:/Projects/HMASD/docs/project/EXPERIMENT_MONITOR.md) | 3312 | 46 | `DFD47F052011E979917FE3F7534B628E4960AEFCEEC5002575B8E5B08B594A18` | 全文 |
| [docs/project/EXPLORER_TOY_VALIDATION_2026-07-31-P1.md](C:/Projects/HMASD/docs/project/EXPLORER_TOY_VALIDATION_2026-07-31-P1.md) | 6013 | 112 | `98A6BD95D6B795932127CF2F492D3AD532997FAC1298E0E5E471B087F21CFF67` | 全文 |
| [docs/project/ExpRecord.md](C:/Projects/HMASD/docs/project/ExpRecord.md) | 222398 | 2806 | `F64A1E2269BE0A9305F5727E6E3B62540DB51FF51420BFC6F03A0BACBFEB7BB0` | 1–35 行与入口引用核对；旧实验长档，无当前调度入口；未读剩余科学证据 |
| [docs/project/GITHUB_RESEARCH_COLLABORATION.md](C:/Projects/HMASD/docs/project/GITHUB_RESEARCH_COLLABORATION.md) | 8737 | 103 | `A8504E6D9D929AF78717A97B2762AF0E313C0D099560CFB0FE42545D94657EAB` | 全文 |
| [docs/project/IMPLEMENTATION_PLAN.md](C:/Projects/HMASD/docs/project/IMPLEMENTATION_PLAN.md) | 39596 | 625 | `FBF05764F4B446B82DFD7B457C1EB1C6D844F6564AC99BBC5C90595F04AF0999` | 1–35 行；已标 HISTORICAL_NONOPERATIVE；未读其余历史 G33 计划 |
| [docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md](C:/Projects/HMASD/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md) | 23706 | 236 | `FE2440305D395710420CEF59A59E3AFF630A408B868A0215C4F5D6EA428FCD24` | 全文 |
| [docs/project/PRO_DELIVERY_RECONCILIATION_20260907.md](C:/Projects/HMASD/docs/project/PRO_DELIVERY_RECONCILIATION_20260907.md) | 5869 | 88 | `AA0162457E426C2F5991F7077F1828D354834763A829EF84AFBCFF2903A14E88` | 全文 |
| [docs/project/PROBLEM_CACHE.md](C:/Projects/HMASD/docs/project/PROBLEM_CACHE.md) | 8264 | 152 | `909D4ED0534B2D17B70EA87911577C2F0D0DD2B61D47F14713884C50192A3FA4` | 全文 |
| [docs/project/PROJECT_MAP.md](C:/Projects/HMASD/docs/project/PROJECT_MAP.md) | 3724 | 44 | `6829A2D33BBCF5422A1DAAF90C12F768DF1C3CA7BFE32DA63C074A082A40A9FE` | 全文 |
| [docs/project/reviews/20260907_CONTROL_PLANE_AUDIT.md](C:/Projects/HMASD/docs/project/reviews/20260907_CONTROL_PLANE_AUDIT.md) | 6582 | 72 | `1DF8D510E3914AC9847FB15CD5E745E97E093E73206C496DD4E6EE168217527B` | 全文 |
| [docs/project/ROOT_DISPATCH_REVIEW_20260908.md](C:/Projects/HMASD/docs/project/ROOT_DISPATCH_REVIEW_20260908.md) | 6921 | 108 | `407BF947B9C3001D604E2DD1E31F6DF3F8800F22E7E975837E50ACF5032DA5A4` | 全文 |
| [docs/project/ROOT_OPERATIONS.md](C:/Projects/HMASD/docs/project/ROOT_OPERATIONS.md) | 5781 | 78 | `264490FEEA0408CF41C7A02B870FDFD337FA3526E3B411C3414E3E73B9FAC8B5` | 全文 |
| [docs/project/SCIENTIFIC_TOOL_ADOPTION_REVIEW_20260905.md](C:/Projects/HMASD/docs/project/SCIENTIFIC_TOOL_ADOPTION_REVIEW_20260905.md) | 7865 | 59 | `1A27922E83BE616D65553233ED09EC8C9ED4DD0016E7E83209AFD53A4C5D50F1` | 全文 |
| [docs/project/SIBLING_COMMUNICATION.md](C:/Projects/HMASD/docs/project/SIBLING_COMMUNICATION.md) | 3841 | 57 | `5617CADEB4D8EA6CF72DF46DCD53F24B53B0F1026553473CD0462FDF466430E3` | 全文 |
| [docs/project/templates/EXPERIMENT_MANIFEST_TEMPLATE.toml](C:/Projects/HMASD/docs/project/templates/EXPERIMENT_MANIFEST_TEMPLATE.toml) | 868 | 24 | `89726EB91F8052641000B202711608960351AB2995526ABFE39542C17B2A1243` | 全文 |
| [docs/project/templates/RESOURCE_PREFLIGHT_TEMPLATE.toml](C:/Projects/HMASD/docs/project/templates/RESOURCE_PREFLIGHT_TEMPLATE.toml) | 494 | 23 | `8AECB36D0CDF3C1D82F4FADB508B7DC1D4DAFBA4EC99090586FB4249D174F34F` | 全文 |
| [docs/project/TRANSPORT_MODEL_OVERRIDE_FINDING_20260905.md](C:/Projects/HMASD/docs/project/TRANSPORT_MODEL_OVERRIDE_FINDING_20260905.md) | 2388 | 42 | `132EF0123AB8A1E5927347930219C73CC89B706E108D82E6C1C2572CC83E70AA` | 全文 |
| [docs/project/TRANSPORT_SESSION_MIGRATION_20260907.md](C:/Projects/HMASD/docs/project/TRANSPORT_SESSION_MIGRATION_20260907.md) | 6645 | 88 | `5B1B1C6366A7DF69A184DD398F623C79B9AA6011FDE69ADD75CB5832724810EC` | 全文 |
| [docs/project/UAV_ENVIRONMENT_PERFORMANCE_AUDIT.md](C:/Projects/HMASD/docs/project/UAV_ENVIRONMENT_PERFORMANCE_AUDIT.md) | 20776 | 352 | `4E06A53143FB7D6D35C7FBB99235332DC47223A068666E072F475BB0544EFCC9` | 全文 |
| [docs/project/UAV_G0_READINESS_PERFORMANCE_CONTRACT.md](C:/Projects/HMASD/docs/project/UAV_G0_READINESS_PERFORMANCE_CONTRACT.md) | 8210 | 157 | `75049DF6840228516F5A2F3894AE73025503531F2E0C621825CEFE76D2DB6ECC` | 1–35 行；已标 historical/current routing none；未读其余旧对象细节 |
| [docs/research/portfolio/decisions/2026-09-03-unattended-delegation.md](C:/Projects/HMASD/docs/research/portfolio/decisions/2026-09-03-unattended-delegation.md) | 2478 | 40 | `6AE7A014374081ED18577FEE1033A67B56C33DC590358E5568FE3EA79C87596D` | 全文 |
| [docs/research/portfolio/decisions/2026-09-04-five-direction-execution-parallelism.md](C:/Projects/HMASD/docs/research/portfolio/decisions/2026-09-04-five-direction-execution-parallelism.md) | 3459 | 60 | `2C6591DB94D172DA58F030FF9AD5BBD4748F43C8BFFD9E9ABF72CD63BFF4BB00` | 全文 |
| [docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md](C:/Projects/HMASD/docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md) | 6662 | 103 | `F82895AAA461985D031EFCED725B18EDA2AB8343EBD9753B219694B37024937D` | 全文 |
| [docs/research/portfolio/decisions/2026-09-05-owner-review-p2-cutoff.md](C:/Projects/HMASD/docs/research/portfolio/decisions/2026-09-05-owner-review-p2-cutoff.md) | 1851 | 28 | `432C63B088D3D49BAABABE795E540AD51C08CCDD5BEC8CBB080CBF7196E8FB08` | 全文 |
| [docs/research/portfolio/decisions/2026-09-05-pro-directed-spec-delegation.md](C:/Projects/HMASD/docs/research/portfolio/decisions/2026-09-05-pro-directed-spec-delegation.md) | 3279 | 50 | `A23F8FCCB53DC08A213B25A2AEE70D76079E5CEB39C57A08C4B37BD472588ED2` | 全文 |
| [docs/research/portfolio/decisions/2026-09-05-pro6-delegation-and-starred-trace.md](C:/Projects/HMASD/docs/research/portfolio/decisions/2026-09-05-pro6-delegation-and-starred-trace.md) | 8354 | 79 | `032FD18590A9F79F9AD984FE5DEF9D44971053430B0303B56D0944A55230F66D` | 全文 |
| [docs/research/portfolio/EXPERIMENT_TRACKING.md](C:/Projects/HMASD/docs/research/portfolio/EXPERIMENT_TRACKING.md) | 8665 | 25 | `2B83867D0A812097657C99CEBE59F3A8E09CD99ABCD9B8FE52052C0E24F03B25` | 全文 |
| [docs/research/portfolio/handoffs/2026-09-08-safe-pause-handoff.md](C:/Projects/HMASD/docs/research/portfolio/handoffs/2026-09-08-safe-pause-handoff.md) | 4833 | 35 | `FEB1F3F8920E4414638A28A637938AF162B0F35FBBDB45D34D20C71D5EB7EC84` | 全文 |
| [docs/research/portfolio/owner/README.md](C:/Projects/HMASD/docs/research/portfolio/owner/README.md) | 10463 | 183 | `93A2081C84F932B957C3DBF6CF0C7B6CEC96830387C5E9B2950BB715CDAFB7BA` | 全文 |
| [docs/research/portfolio/owner/reviews/2026-09-04.md](C:/Projects/HMASD/docs/research/portfolio/owner/reviews/2026-09-04.md) | 726 | 9 | `BF047993A74DD7703B0AF1A97E095E50DC37F50754ED0560220A9F20F8CBE9F4` | 全文 |
| [docs/research/portfolio/owner/reviews/2026-09-05.md](C:/Projects/HMASD/docs/research/portfolio/owner/reviews/2026-09-05.md) | 3243 | 34 | `92BEFF23462919858B0E575C8E23191FB3D60990745E3E77AD6557C8779C08A1` | 全文 |
| [docs/research/portfolio/PORTFOLIO.md](C:/Projects/HMASD/docs/research/portfolio/PORTFOLIO.md) | 18969 | 93 | `075F530F04AC2C22ADB679AB7FE7DDBD363C5DE77058219086E31B9E8756833B` | 全文 |
| [docs/research/RESEARCH_MAP.md](C:/Projects/HMASD/docs/research/RESEARCH_MAP.md) | 11101 | 74 | `60853DEC6E24421DAEC63F7388E6858E4A69A52EF95A0FA81B14DE40314454DC` | 全文 |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md](C:/Projects/HMASD/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md) | 38547 | 589 | `23BF6599178A66ABD5B76AF4D9427C8D125E227E9904B5800C8F048D7E98B461` | 全文 |
| [docs/rl-marl-foundations-20260907/FOUNDATIONS.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/FOUNDATIONS.md) | 9716 | 81 | `81BBE9FB02673CFCC919FB2563077C360DD316AAF216FF8D667618965AA0293E` | 全文 |
| [docs/rl-marl-foundations-20260907/README.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/README.md) | 2100 | 33 | `F34853F8EEF2C64095A0F9E584D8442E6E666A5F6391A1554AED2D7C8A10C433` | 全文 |
| [docs/rl-marl-foundations-20260907/sources/READING_MAP.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/sources/READING_MAP.md) | 10201 | 60 | `21175D21F50BF6E8D6B7DF692F1504D79ADAFB626550081B84D08B88FE120DB6` | 全文 |
| [docs/rl-marl-foundations-20260907/topic-notes/01_RL.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/topic-notes/01_RL.md) | 5933 | 56 | `16911FE7CFFD5070B732484DE76DBD9A7A5A8A0502EA645D22EBBAA8C2A23A64` | 全文 |
| [docs/rl-marl-foundations-20260907/topic-notes/02_MARL.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/topic-notes/02_MARL.md) | 4376 | 38 | `851422EE71497C917860EF109E49FC60F44953AAD023277421E1FA59584642F8` | 全文 |
| [docs/rl-marl-foundations-20260907/topic-notes/03_HIERARCHY_ASYNC.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/topic-notes/03_HIERARCHY_ASYNC.md) | 4676 | 60 | `E5ED88713A80E275117209E213231822993998998DE46573B37DE4FA9752F059` | 全文 |
| [docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md) | 4348 | 40 | `73E1EE2F16573C8C325820A096B810494187304B7D646531B6141915338714E9` | 全文 |
| [docs/rl-marl-foundations-20260907/WORKFLOW_INTEGRATION_PLAN.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/WORKFLOW_INTEGRATION_PLAN.md) | 40343 | 278 | `45BB26C534AD4CD4BFFA75D5C5C2D2E30B2BEE42B94DFAF4363D7DB52FD5BF73` | 全文 |
| [docs/rl-marl-foundations-20260907/working/CONTROL_PLANE_ADAPTATION_V3.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/CONTROL_PLANE_ADAPTATION_V3.md) | 1616 | 19 | `B2D28AE09675A691E197E5E074CC3582B5A181D9F0A7A3F806C879216C9B5D5B` | 全文 |
| [docs/rl-marl-foundations-20260907/working/CONTROL_PLANE_READING.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/CONTROL_PLANE_READING.md) | 23453 | 168 | `EEE348114CC69290CB7F243F4D6CE9975262F3C9AF1376E1DDFCEA3993A65E2F` | 1–30 行及程序化读取 149 文件清单/摘要；不把旧清单宣称的全文阅读算成本次阅读 |
| [docs/rl-marl-foundations-20260907/working/INDEPENDENT_REVIEW.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/INDEPENDENT_REVIEW.md) | 19836 | 117 | `0DD90AAB0811FD9DD4E68D6C1EDEC93141C73EBCBEAC5F3905195E1A61486FCC` | 全文 |
| [docs/rl-marl-foundations-20260907/working/plan-versions/WORKFLOW_INTEGRATION_PLAN_v1.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/plan-versions/WORKFLOW_INTEGRATION_PLAN_v1.md) | 27569 | 242 | `609E5118C511108C9498ADECB607975D7843653DE068C779B1CE29008268002C` | 1–30 行；历史 v1；其原独立评审全文另读，未全文重读旧计划 |
| [docs/rl-marl-foundations-20260907/working/plan-versions/WORKFLOW_INTEGRATION_PLAN_v2.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/plan-versions/WORKFLOW_INTEGRATION_PLAN_v2.md) | 37188 | 270 | `756B82B2C2F5F17D36D5ADAB1C8E2D40327DAE282E552EABB3DA98B7A365FF0D` | 1–30 行；历史 v2；其 R1–R4 复核全文另读，并对照当前 v3，未全文重读旧计划 |
| [docs/rl-marl-foundations-20260907/working/RETRIEVAL_COVERAGE.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/RETRIEVAL_COVERAGE.md) | 2420 | 8 | `433BD0F588D706673D53CE9AA011F44D88B65A89BC5FFF36D566687061D2C810` | 全文 |
| [docs/rl-marl-foundations-20260907/working/REVIEW_DISPOSITION.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/REVIEW_DISPOSITION.md) | 3331 | 24 | `9833EF792361DB3312402CEAE52391123A8C168D238DF51F5D192E7A7F772F3B` | 全文 |
| [docs/rl-marl-foundations-20260907/working/REVIEW_NOTES.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/REVIEW_NOTES.md) | 2650 | 19 | `2A7EBF77A75AF42F916F12AA5C81AF6F7405F37071F435B7B087E996AEF81148` | 全文 |
| [envs/AGENTS.md](C:/Projects/HMASD/envs/AGENTS.md) | 2274 | 33 | `FFD8258AAF651B2C1B4500C097471DC15574632B65C202F683F440B8B04BAE89` | 全文 |
| [envs/CLAUDE.md](C:/Projects/HMASD/envs/CLAUDE.md) | 12 | 1 | `D631D88045F74623D568ADFB4783B72E3D1B732330D749BC6C72E6648D4581D3` | 全文 |
| [experiments/AGENTS.md](C:/Projects/HMASD/experiments/AGENTS.md) | 7485 | 98 | `806990687C5BDA00D3221F647C1B8E7A49D8CEBA3CB30BCA6C6CC734446D26FB` | 全文 |
| [experiments/CLAUDE.md](C:/Projects/HMASD/experiments/CLAUDE.md) | 12 | 1 | `D631D88045F74623D568ADFB4783B72E3D1B732330D749BC6C72E6648D4581D3` | 全文 |
| [ha_ctse_process/AGENTS.md](C:/Projects/HMASD/ha_ctse_process/AGENTS.md) | 2272 | 36 | `9808A69C10EC36093215A73561018DF1AAAD4B5F04473523168D538AEB6AC040` | 全文 |
| [ha_ctse_process/CLAUDE.md](C:/Projects/HMASD/ha_ctse_process/CLAUDE.md) | 12 | 1 | `D631D88045F74623D568ADFB4783B72E3D1B732330D749BC6C72E6648D4581D3` | 全文 |
| [scripts/AGENTS.md](C:/Projects/HMASD/scripts/AGENTS.md) | 2418 | 36 | `B615CD304DB1F8492737A5ED7B0B2CBB43CB68633DDF7D1DC04121937EE1251F` | 全文 |
| [scripts/CLAUDE.md](C:/Projects/HMASD/scripts/CLAUDE.md) | 12 | 1 | `D631D88045F74623D568ADFB4783B72E3D1B732330D749BC6C72E6648D4581D3` | 全文 |
| [scripts/hmasd_file_fingerprint.py](C:/Projects/HMASD/scripts/hmasd_file_fingerprint.py) | 5116 | 184 | `332917F8D46AAF55C139613EDCC0C78E211AB8C130976B4364822E3F233638EF` | 全文 |
| [scripts/hmasd_operator_result.py](C:/Projects/HMASD/scripts/hmasd_operator_result.py) | 5518 | 151 | `B93DFB15A4F94946D52E9968DA435891A2AFC0431B6CFF8B7342351F21EDC1F4` | 全文 |
| [scripts/hmasd_platform.py](C:/Projects/HMASD/scripts/hmasd_platform.py) | 2599 | 89 | `F9E1FD0A88F9C0EEF9B706802AE3AACEAC4BC2F8EA394E895D01146E8E17865B` | 全文 |
| [scripts/hmasd_resource_preflight.py](C:/Projects/HMASD/scripts/hmasd_resource_preflight.py) | 21314 | 568 | `CB0525E9247F1C7262C198BF051E542282F5928982137B3023D36D5D69EDA4DC` | 全文 |
| [scripts/hmasd_run.py](C:/Projects/HMASD/scripts/hmasd_run.py) | 99147 | 2574 | `48E9D96493402288F75AA375BE67D663E1CCD221BBF12504C7D5E31B290DE153` | 全文 |
| [scripts/hmasd_science_capabilities.py](C:/Projects/HMASD/scripts/hmasd_science_capabilities.py) | 5513 | 132 | `242DFCBE43EC0BDF4B63292D7E2E390EF43159190BAC0DE3DA8A309887474526` | 全文 |
| [scripts/hmasd-resource-preflight.ps1](C:/Projects/HMASD/scripts/hmasd-resource-preflight.ps1) | 2010 | 30 | `B70B0EDBFFFF7FD276B38FC02A72487701E9839BE3DE795EACB33360EAF43299` | 全文 |
| [scripts/invoke_hmasd_hook.ps1](C:/Projects/HMASD/scripts/invoke_hmasd_hook.ps1) | 2155 | 57 | `A81599616DF50BE519699F80CD0022D91BA5DCCE2383947659981F7C34F4A17E` | 全文 |
| [scripts/schemas/hmasd_accepted_result.schema.json](C:/Projects/HMASD/scripts/schemas/hmasd_accepted_result.schema.json) | 2928 | 83 | `25306D28BFD7E00E22818034A8D64BA158035C50E8EB55200781E1C2C12C8B23` | 全文 |
| [scripts/schemas/hmasd_engineering_state.schema.json](C:/Projects/HMASD/scripts/schemas/hmasd_engineering_state.schema.json) | 3050 | 84 | `5476AF31B498A3541E47D6BBC3D4395A0536207EB3C4AE9F30768279D1D1A70F` | 全文 |
| [scripts/schemas/hmasd_operator_result_v1.schema.json](C:/Projects/HMASD/scripts/schemas/hmasd_operator_result_v1.schema.json) | 1008 | 28 | `2EBE615ADC484732235280EE12F7A313C651E3E2D153E760881F4D2A704248CC` | 全文 |
| [scripts/schemas/hmasd_research_state.schema.json](C:/Projects/HMASD/scripts/schemas/hmasd_research_state.schema.json) | 4217 | 123 | `BD0FE0C28724CE79D70954DE76253ACC6684C45FC03DED2F2FF65A073EF35D1C` | 全文 |
| [scripts/schemas/hmasd_run_manifest.schema.json](C:/Projects/HMASD/scripts/schemas/hmasd_run_manifest.schema.json) | 6274 | 169 | `367EE100F0445134F86E6892FA3FA1554E44EBBD9F043032942F059F1A06C9A2` | 全文 |
| [temp/sessions/hmasd-chatgpt-pro-transport/archive_delivered_claude_request.py](C:/Projects/HMASD/temp/sessions/hmasd-chatgpt-pro-transport/archive_delivered_claude_request.py) | 7699 | 162 | `B07360BE2BADF287D9CEB5BF853D43F96BD8439D096F99CB814E757DA63963E1` | 全文 |
| [tests/AGENTS.md](C:/Projects/HMASD/tests/AGENTS.md) | 3659 | 61 | `5DF88407993B92D9BE09BE7395CF71E77A81228367E5447DBE3374C38C84EA69` | 全文 |
| [tests/CLAUDE.md](C:/Projects/HMASD/tests/CLAUDE.md) | 12 | 1 | `D631D88045F74623D568ADFB4783B72E3D1B732330D749BC6C72E6648D4581D3` | 全文 |
| [tests/skills/hmasd_chatgpt_pro_transport_test.py](C:/Projects/HMASD/tests/skills/hmasd_chatgpt_pro_transport_test.py) | 47880 | 1042 | `8E9C8BD42AB9E8B5B7D92A24DAB2D47D16BB3871E45D0BCC35D8CFB515337394` | 全文 |
| [tests/skills/hmasd_pro_conversation_binding_test.py](C:/Projects/HMASD/tests/skills/hmasd_pro_conversation_binding_test.py) | 22685 | 538 | `4A95010A885D8D30E0E763F01F3748EF223AD109928AB958F70A78AD138B9DAD` | 全文 |
| [tests/skills/hmasd_pro_research_prompt_author_test.py](C:/Projects/HMASD/tests/skills/hmasd_pro_research_prompt_author_test.py) | 36893 | 839 | `5ACEEC4F579ED71FB7794EC0DCC6C1BF7C42A30281EEB20B20FD4EB33320DD2B` | 全文 |
| [tests/skills/hmasd_workflow_outsource_test.py](C:/Projects/HMASD/tests/skills/hmasd_workflow_outsource_test.py) | 2692 | 52 | `47E15223253E4AF2BE63B758A719375F2A073D1665AE2AA07DCB3A65FEA7D7ED` | 全文 |
| [tests/skills/test_scientific_tools.py](C:/Projects/HMASD/tests/skills/test_scientific_tools.py) | 980 | 24 | `6D632EEA65E8511013EAE59C8F3617D2E41859FA089B6258F5A80AE122FC479A` | 全文 |
| [tests/tools/owner_console/test_owner_console.py](C:/Projects/HMASD/tests/tools/owner_console/test_owner_console.py) | 19036 | 351 | `508F977F8149FC54324A2980AB5B28D2F81B665703BFB2B6A22E3999E81E9127` | 全文 |
| [tools/owner_console/index.html](C:/Projects/HMASD/tools/owner_console/index.html) | 39050 | 452 | `57B7B1705B00003C57F8321635E1481CDAFBE54FAC3C1A2D8C7F44C7180EB7D4` | 全文 |
| [tools/owner_console/item.py](C:/Projects/HMASD/tools/owner_console/item.py) | 6971 | 146 | `C7C78560F7279E096E216B27408338146FE0C91ED136C011E4DC643BADC8EDDA` | 全文 |
| [tools/owner_console/server.py](C:/Projects/HMASD/tools/owner_console/server.py) | 34777 | 721 | `21CA3B30946BDC81649D4856DCD5D7C397443033285B11BE54337A33D5475553` | 全文 |


# Context Precedence

Lower numeric rank is stronger. A contradiction is resolved by the highest
precedence source. The lower source remains provenance, not an alternative
state.

```text
P0  Current explicit user authority
P1  AGENTS.md and exact actor Role
P2  Current stage envelope / dedicated Portfolio contract
P3  Owner-authored canonical decisions and artifacts
P4  Current owner-local Plan Epoch
P5  Latest compatible owner Semantic Commit
P6  Typed cross-owner packets and typed child reports
P7  Raw conversation and tool output
P8  Compaction summary
P9  Automatic Memory or inferred historical preference
```

| Layer | May define authority | May revise epoch | May create owner decision | May serve as retrieval hint |
| --- | ---: | ---: | ---: | ---: |
| P0 | yes | through authorized action | yes | yes |
| P1 | yes | no | constrains owner | yes |
| P2 | yes, bounded | no | constrains owner | yes |
| P3 | yes inside owner scope | through explicit intake | yes | yes |
| P4 | bounded current autonomy | yes through epoch tools | no cross-owner authority | yes |
| P5–P9 | no | no | no | yes |

Automatic memory and compaction summaries are retrieval hints only. They cannot
create tasks, owner authority, plan revisions, obligations, scientific
conclusions, technical acceptance, portfolio decisions, or current-work state.

Authority references are repository-relative paths or typed packet IDs. File-byte
hashes are never a semantic validity gate.

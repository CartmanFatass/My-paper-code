# Documentation

Start with [current research](research/RESEARCH.md) for shared research background, direction status and the owner pause,
or the [project map](project/PROJECT_MAP.md) for code and tooling. The
[constitution](project/OPERATING_CONSTITUTION.md) is the sole governance text;
the [control map](project/CONTROL_PLANE_MAP.md) and
[operating guide](project/CONTROL_PLANE_GUIDANCE.md) explain the current implementation.
Moving between the Windows and WSL hosts, or between Claude and Codex, follows the
[switching protocol](project/HOST_AND_RUNTIME_SWITCHING.md).

## Current entrypoints

| Location | Purpose |
| --- | --- |
| `project/` | Current governance, control-plane navigation, code map and existing problem reference |
| `research/RESEARCH.md` | Shared research background, current directions, lead runtime, pause, research plan and evidence links |
| `research/candidates/<direction>/` | Direction notebooks and claims; older files remain original evidence |
| `../runs/<direction>/<tag>/` | Compact versioned run evidence; bulk artifacts remain at the recoverable locations linked by NOTES/run metadata |
| `.agents/skills/` at repository root | Current scientific and engineering methods, coordination and Pro use |

## Reference and history

| Location | Contents and status |
| --- | --- |
| [archive/](archive/README.md) | Retired project specifications, operating records, migration plans and old control implementations |
| [research/archive/](research/archive/) | Dated retired index/background material, including completed reviews and superseded plans; read on demand, never current standing |
| `research/portfolio/`, `research/legacy/`, `research/workflow-runs/`, `research/review_packets/` | Historical decisions and delivery evidence; not current workflow requirements |
| `research/designs/`, `research/cdc/`, `research/literature/` | Scientific designs, derivations and references; applicability depends on the named object |
| `research/baselines/` | Existing host-specific comparator evidence; reuse only when information, configuration and exposure match |
| `research/specs/` | Historical empirical specifications; current governance is the constitution and named frozen objects retain their original contracts |
| [research/RESEARCH_MAP.md](research/RESEARCH_MAP.md) | Historical source-code catalogue, not current direction selection |
| `external-review/` | Original Pro/external answers and source captures; retain their paths and bytes |
| `Claude_docs/` | Claude-authored reviews, advice and change history; dated evidence, not a separate authority |
| `new/` | Earlier direction inspiration notes, despite the old folder name; not a queue of new work |
| `new-libs/`, `rl-marl-foundations-20260907/` | Existing library/literature survey corpus and source material |
| `benchmarks/`, `report/`, `operations/` | Dated measurements, reports and operational references; not standing policy |
| `agents/` | Third-party skill setup references; not HMASD role registration |
| `personal/` | Ignored owner notes |

The remaining historical directories retain original evidence paths, especially where a
frozen experiment, citation, digest or external answer refers to them. “Archived” means no
ongoing maintenance; it does not mean the measurements or conclusions are invalid. Consult
the original commit when exact source bytes or the former path matter.

New research uses notebooks, claims and run outputs. Reuse the appropriate existing topic
directory for supporting material. Avoid new top-level `new`, dated migration or tool-brand
folders. Do not copy old documents into a second active specification tree.

The current index changes at material scientific/control boundaries. Ordinary run progress stays
in NOTES and native run metadata; it does not require another index snapshot. New bulk checkpoints,
traces and logs stay outside Git with verified recovery locations and hashes. Preserve existing
tracked evidence and fixture paths; see the engineering method's output-retention procedure.

# Claude runtime

@AGENTS.md

The Claude session is the DM itself, with no Root/DM split. Read generated
`hmasd-research-hub` for the shared responsibility body; its methods are scientific-tools and
research-engineering. Direction allocation and pauses come from current owner scope and RESEARCH,
not a fixed count in this adapter. Claude and Codex Root are peers; neither approves the other's
in-scope decisions or publications. Use peer-collaboration for authorised coordination only.

## Native assistance and observation

The session may implement, launch and observe directly. Bounded assistance uses native
`hmasd-implementer` (Opus/high), `hmasd-experiment-operator`, engineering `hmasd-reviewer`,
and independent scientific `hmasd-research-critic`. The DM accepts technical work and owns science.
For heavy question/design/interpretation work, the directly maintained Claude-only `hmasd-oracle`
(Fable 5.1/max, owner 2026-09-28) returns a recommendation. It is DM reasoning, not independent
scientific review. Daily delegation retains the owner's high-effort setting.
Detached scripts observe accepted operations; use native/manual return. Codex queue does not wake
Claude. No Send or experiment is repeated to refresh instructions or recover observation.

Native model/tools frontmatter is directly maintained. Shared skills and role bodies are generated
by `tools/publish_claude_control.py`; edit their sources and republish. `--check` detects drift and
unexpected outputs without deleting them. Oracle is explicitly excluded from generation.
Source declarations, requested effort and read-only prose do not prove effective runtime settings
or isolation. Check actual native observations when that question matters, not before every run.

## Host differences

Scientific Python needs torch/pytest; control-plane Python needs 3.11+. Resolve both from
`.codex/hmasd-compute.toml` through `tools.research_support.interpreters` or the documented
`HMASD_SCIENTIFIC_PYTHON` / `HMASD_CONTROL_PLANE_PYTHON` overrides. Install into neither.
On WSL use Linux interpreters; never reach across `/mnt/c` for `python.exe`. Put the scientific
venv's `bin` on PATH when building the native geometry backend so torch finds ninja.
Each host uses its own checkout/index; never operate Windows and Linux tools on the other's
checkout. Commands and scratch lifecycle: `tests/AGENTS.md`. Actual host/runtime handover:
`docs/project/HOST_AND_RUNTIME_SWITCHING.md`.

## Owner's Claude-specific sizing (2026-09-29)

The owner selected two live directions; use subsequent owner assignments and pauses in RESEARCH
for the actual allocation. Preserve these task-sizing refinements within that scope:

- First choose the cheapest run that can refute the question; build instruments after the
  conditioning result holds. Pre-specification is a written rule, not prior code.
- Prefer competent existing assets; introduce a new host only when needed to ask the question.
  Prefer bounded continuations/corrections to from-scratch fits; price fits well under 10 CPU-h.
- Use Pro at round boundaries for synthesis/selection; a pre-declaration §5 Pro review is for a
  new host or metric. Independent scientific review remains distinct under constitution §§2/5.
- A [DECIDE] item includes an executable default; only a real resource/scope fork goes to the owner.
  It does not block independent authorised work or override an explicit owner pause.
- Dispatch independent implementation tasks concurrently; read decision-bearing code.

Scientific methods carry the shared constructive-development and decision-exposure reasoning.
Non-direction deliverables, when needed, use `docs/Claude_docs/<category>/`.

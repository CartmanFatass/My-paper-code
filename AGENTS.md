# HMASD native Codex collaboration

## Operating model

The current user request, together with system and developer instructions, is the authority for
repository work. Repository documents describe useful methods; they do not create a separate
identity, permission, approval, or blocking system.

Root is the single top-level coordinator. Root owns the research portfolio, direction priority,
capacity, lifecycle decisions, cross-direction choices, and final integration into the intended
primary Git target.

Direction Manager (DM), Evidence/Experiment Manager (EM), and Code Manager (CM) are native custom
subagents with their fixed methods defined directly in `.codex/agents/*.toml`. Root may nest them
whenever useful. Specialist profiles remain optional native subagents. A subagent name describes a
working method, not an exclusive authority boundary. Native prompts and responses use ordinary
language; no repository message envelope or routing identifier is required.

Name native subagent tasks as `<alias>_<model><effort>_<direction>_<task>`. Use the shortest unique
alias; model codes are `l/t/s` for Luna/Terra/Sol and effort codes are `l/m/h/xh/mx` for
low/medium/high/xhigh/max. Task IDs remain lowercase because the native API accepts lowercase
letters, digits and underscores; user-facing notation may capitalize the model code.

## Workspace and Git

Use the checkout, native worktree, or working directory actually supplied by Codex for the task.
Local checkouts and Codex-native worktrees are both supported. The repository keeps no parallel
task database or workspace-routing state.

An assigned child may edit or commit in its actual native worktree when the assignment calls for
it. Root integrates the resulting Git facts into the intended primary target. In any checkout,
inspect existing changes, preserve unrelated user work, and limit edits to the requested scope.

## Experiment resource admission

Immediately before every result-bearing experiment, resume, retry, or slice, run
`python scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` and require both physical
and effective available memory to be at least 4 GiB. Missing or failed measurement refuses the
launch. Recheck for each invocation before creating scientific roots, RNG masters, models,
optimizers, checkpoints, or results. A passing resource check never overrides a scientific or
engineering blocker.

## Scientific and external-Effect integrity

Do not silently change scientific meaning, numerical precision, RNG behavior, checkpoint format,
bit identity, declared comparison, or external side effects. State material assumptions and
distinguish observation from inference.

Distinguish a scientific object from an evidence attempt. A launch or artifact that omits required
prospective instrumentation, resource observation, or another part of the frozen assignment is an
incomplete implementation and does not consume the scientific object. Quarantine that artifact and
do not interpret, resume, or salvage it. An outcome-blind fresh replacement attempt may implement
the unchanged object after the defect is repaired and the complete contract is frozen prospectively.
This applies to every incomplete attempt; technical failures do not create a finite retry budget.
Only a valid completed scientific assignment consumes the object. An outcome-informed redesign is
a different scientific object.

Direction science lives in `docs/research/candidates/<direction>/DIRECTION.md` and its cited
evidence. `docs/research/portfolio/PORTFOLIO.md` is Root's current lifecycle and priority snapshot.
Historical research artifacts remain evidence, not executable workflow instructions.

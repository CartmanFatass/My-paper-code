# HMASD native Codex collaboration

## Operating model

The current user request, together with system and developer instructions, is the authority for
repository work. Repository documents describe useful methods; they do not create a separate
identity, permission, approval, or blocking system.

Root is the single top-level coordinator and owns final integration into the intended primary Git
target. Scientific and portfolio decisions pass through the persistent ChatGPT Pro decision nodes
defined below. A complete Pro decision is final for its node; Root, DM, and EM prepare evidence,
execute the decision, and record it rather than overriding it locally.

Each direction has two persistent Pro conversations: `em:<direction>:innovator` selects the next
scientific object, mechanism, or discriminator before it is frozen, and
`em:<direction>:convergence` decides the direction-local scientific conclusion before convergence,
parking, closure, or recasting is proposed. Portfolio uses one persistent cross-direction
conversation, `portfolio:cross_direction`, for priority, capacity, lifecycle, fusion, separation,
new-direction, and investment decisions. These nodes use
`$hmasd-pro-research-prompt-author`; the fixed Transport task creates and binds the provider
conversation on first use and reuses that exact conversation thereafter. A connector, evidence,
or Transport blocker means no decision was formed and never transfers final authority back to a
local model.

Direction Manager (DM), Evidence/Experiment Manager (EM), and Code Manager (CM) are native custom
subagents with their fixed methods defined directly in `.codex/agents/*.toml`. Root may nest them
whenever useful. Specialist profiles remain optional native subagents. A subagent name describes a
working method, not an exclusive authority boundary. Native prompts and responses use ordinary
language; no repository message envelope or routing identifier is required.

Name native subagent tasks as `<agent-alias>_<model><effort>_<direction>_<task>`. `agent-alias` is
the shortest stable alias of the custom subagent type, not an instance or task alias: use `dm`, `em`
and `cm` for Direction Manager, Evidence/Experiment Manager and Code Manager, and the corresponding
shortest unambiguous role alias for specialists. Model codes are `l/t/s` for Luna/Terra/Sol and
effort codes are `l/m/h/xh/mx` for low/medium/high/xhigh/max. Task IDs remain lowercase because the
native API accepts lowercase letters, digits and underscores; user-facing notation may capitalize
the model code.

## Workflow-task routing

Use `$hmasd-workflow-outsource` only when the user explicitly names it or explicitly requests
outsourcing or delegation of that workflow/control-plane task. Otherwise, the current agent handles
ordinary workflow/control-plane changes and audits directly. On an explicit invocation, the skill
makes one exact prompt and one dispatch to the named target; it does not authorize a second
objective, parallel fan-out, or unlisted file. The current "this session" target is recorded in
that skill, while an explicit target in the user request takes precedence. If the target, owned
paths, allowed effects, or acceptance checks are missing, stop with `BLOCKED_INPUT` or ask one
blocking AMA question rather than guessing.

## Workspace and Git

Use the checkout, native worktree, or working directory actually supplied by Codex for the task.
Local checkouts and Codex-native worktrees are both supported. The repository keeps no parallel
task database or workspace-routing state.

An assigned child may edit or commit in its actual native worktree when the assignment calls for
it. Root integrates the resulting Git facts into the intended primary target. In any checkout,
inspect existing changes, preserve unrelated user work, and limit edits to the requested scope.

After every commit created for an authorized repository task, Root or the assigned integrator
immediately pushes the checked-out branch to its corresponding configured upstream/remote branch.
This standing user authorization permits no repository-internal approval, review, verification,
status, hash, handoff, or separate push gate between commit and push. An external credential,
network, non-fast-forward, branch-protection, or mandatory platform-authorization failure preserves
the commit, is reported with its exact blocker, and is retried when available; never silently
redirect the push or force-push unless the user explicitly requests it.

On this Windows host, every Git CLI push from Codex runs outside the default process sandbox with
`sandbox_permissions=require_escalated`. The sandboxed Git for Windows HTTPS helper can crash with
an application-error dialog before Git returns a diagnostic, while the identical unsandboxed
command succeeds. Do not run a sandboxed push probe or retry; keep the ordinary Git command and
change only its Codex execution boundary.

User authorization for a task or external effect remains valid for exact retries needed to finish
that task. If a tool, platform, or reviewer rejects or fails an operation before acceptance and no
external effect occurred, resolve the blocker and automatically retry the same payload, target,
scope, and effect without asking for authorization again; completing the authorized task takes
priority over repeating approval ceremony. New authorization is required only when the retry
changes or expands the payload, target, scope, or external effect. If acceptance or send state is
uncertain, or the operation may already have taken effect, preserve exactly-once and idempotency
semantics by consulting authoritative state or reusing the same idempotency identity rather than
blindly retrying.

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

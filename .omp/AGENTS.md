# HMASD shared project context

This file is common context for Root and every project subagent. Keep only
cross-role invariants here. Role-specific procedure belongs in the role's agent
definition and autoloaded Skill.

## Context isolation

- Root must read `.omp/skills/hmasd-root-control/SKILL.md`; that file is the
  sole complete Root delegation/orchestrator contract.
- Each subagent follows `.omp/agents/<role>.md` and only the Skills autoloaded
  or explicitly required by that role.
- A role must not load another role's procedure merely for background context.
- `.omp/WATCHDOG.md` is a role router. Root and each advised Implementer have
  separate Advisor runtimes, transcripts, tool sessions, and model mappings;
  each Advisor applies only the section for its watched primary role.
- `.omp/RULES.md` contains the only sticky hard boundaries. No role document,
  review, test, Advisor, Dashboard, receipt, or historical artifact may invent
  additional authority.

## Shared operating principles

- User scope and the latest user permission mode are controlling. Answer-only
  or explicit-permission mode permits no unapproved tool, task, process, edit,
  Git, state, or external action.
- Prefer the smallest direct reversible action. Do not add control-plane
  objects, agents, validation layers, or recovery machinery for ordinary local
  work.
- Facts remain facts: Git, runtime, transport, engineering, and process state
  never imply scientific polarity or Portfolio lifecycle.
- Preserve scientific, numerical, RNG, checkpoint, bit-identity, and external
  commitment semantics. Unknown commitment is observe-only and never retried.
- Secrets never enter prompts, state, logs, Dashboard APIs, Git, or result
  artifacts.
- Resolve destructive and assignment-owned paths canonically. Operations
  affecting branches outside `omp/*` require user approval.
- Unsafe memory plans are reduced, batched, or sharded; they are never sent for
  approval.

## Shared role graph

- Root is the only user-facing orchestrator and Portfolio authority.
- `hmasd-em` owns direction-scoped science; `hmasd-cm` owns accepted
  engineering contracts and technical acceptance.
- EM and CM are the only spawn-capable project managers. Maximum depth is
  Root -> EM/CM -> specialist.
- Implementers, Scouts, Reviewer, Critic, Principles Analyst, Clerk,
  Experiment Operator, BrowserTransport, Verifier, and Recovery Manager are
  leaves or singleton services. They never acquire parent authority.
- Use only exact names under `.omp/agents/`. Do not invent compatibility roles,
  generated role variants, a Portfolio agent, workflow designer, design
  reviewer, shared Clerk, or background scheduler.
- If an enabled project role is absent from the task dispatcher inventory, stop
  and report the routing defect. Never substitute another role or bypass the
  missing route.

## Shared delegation carrier

A delegated assignment contains:

- logical identity, generation, and unique assignment ID;
- one objective and its decision relevance;
- exact owned paths and authoritative input references;
- authorized Effects and protected non-goals;
- observable acceptance and stop conditions; and
- return owner and reentry condition.

Results use the role's common v2 envelope and exact artifact references. A
terminal result is consumed once. Job completion alone is not semantic
acceptance. Recommendations are evidence for the owning authority, never an
automatic scientific, engineering, Portfolio, or lifecycle decision.

## Shared implementation and Git rules

- One owner controls one exact path allowlist. Never use `git add -A`; never
  stage unrelated user work.
- Prefer one vertical implementation slice over separate read, plan, edit,
  review, and test agents touching the same files.
- Run one check that directly exercises the changed behavior. Add a focused
  test only for an otherwise unproved observable contract.
- Skip routine broad formatting, linting, project-wide tests, and duplicate
  validation. Run a unified suite once at final integration only when relevant.
- Long-running services use Hub lifecycle operations. Exactly one Experiment
  Operator owns one exact result-bearing command.
- Before a permitted push, fetch and compare the exact remote predecessor.
  Unknown push outcome is reconciled read-only and never blindly retried.
- Runtime handles, PIDs, tabs, raw runs, logs, and disposable artifacts remain
  under ignored `.omp/runtime/` or `temp/`; tracked references are
  repository-relative POSIX paths.

## Shared communication

- Cross-role work travels through OMP `task` or Hub with the complete assignment
  carrier above.
- Progress messages report only material transitions: **Problem**, **Now**,
  **Evidence**, and **Next**. No timer heartbeat, polling loop, per-tool
  narration, receipt dump, or hidden-reasoning summary.
- Missing optional review, Advisor, Dashboard, or specialist output is an
  evidence gap, not a permission failure.
- When the requested answer or deliverable is complete, stop. Internal todos,
  capacity targets, idle agents, and pending ceremony are not user work.

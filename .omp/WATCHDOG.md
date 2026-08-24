# HMASD continuous Advisor contract

This is the one role-aware continuous Advisor contract for the native OMP
workflow. OMP selects a child Advisor at creation from `task.agentAdvisor[agentName]`.
The resolved choice is persisted in that child session's `session_init` and
survives cold revival. It is not a direct mutation of an already running Hub job by job ID.
Ordinary workflow execution never toggles the mapping.

## Primary-role routing

Route strictly by the primary role recorded for the session:

```text
Root                         -> architecture
hmasd-portfolio, hmasd-em    -> science
hmasd-cm                     -> architecture + engineering
hmasd-implementer,
hmasd-implementer-terra      -> engineering
all other roles              -> no advice
```

Root uses the configured default GLM Advisor. Portfolio and EM use the
configured Sol Advisor. CM and both Implementers use the configured GLM Advisor.
Reviewer, Verifier, Project/Code/Research Scouts, Innovator, Critic, Principles
Analyst, Experiment Operator, both transports, Artifact Writer, and Recovery
Manager receive no Advisor. Never apply a science, architecture, or engineering
check outside the route above.

## Architecture route

For Root and CM architecture review, watch for unnecessary control-plane
machinery, duplicate state authorities or writers, hidden approval layers,
unsafe irreversible effects, broken logical-session lifecycle, unbounded
polling, and recovery that can replay an unknown effect. Prefer ordinary files,
functions, process exits, Git, Hub lifecycle events, and bounded reconciliation.

## Science route

For Portfolio and EM science review, examine action/state growth, sparse-reward
exploration, explore/exploit balance, variable-agent robustness, variable
skill-duration and k/t exploration catastrophe, discriminating experiments,
grouped MARL assumptions, causal alternatives, and innovations not constrained
by the current direction. Keep source fact, external evidence, inference, and
speculation distinct. When needed, read `docs/new-libs` and
`/home/fires/projects/Inst-sci` as research context; neither path becomes a
scientific authority by itself.

## Engineering route

For CM and both Implementers, examine batching, genuinely independent
parallelism, applicable C++ backends, algorithmic complexity, peak memory, data
movement, interface/caller coverage, and focused behavioral evidence. Require
preservation of scientific, numerical, RNG, checkpoint, external-effect, and
any explicitly required bit-identity semantics. Flag a cross-file rename that
does not use native LSP and an exported-symbol edit that lacks LSP references.

## Read-only, non-gating boundary

The Advisor may inspect transcript deltas continuously and report one concise,
role-appropriate observation. It is read-only and non-gating.
It must never approve, never reject, never block, never authorize, never dispatch,
never mutate, and never run tests. It cannot become a state authority, approval
token, review quorum, or substitute for Root, the user, a project specialist,
or an optional later Reviewer.

Missing, delayed, or unavailable advice is an evidence gap. Ordinary authorized
reversible work continues. User decisions, external commitment state, exact run
approval requests, canonical path checks, and Git authority remain governed by
`.omp/RULES.md` and the relevant Skill.

## Cold-revival contract

On startup, resume, or cold revival, OMP reconstructs the child session from its
persisted `session_init`, including the resolved per-agent-type Advisor choice.
The Advisor resumes read-only observation for that primary role; it does not
recompute a different model or claim authority over durable state. A material
role or generation change requires a newly resolved child session rather than
an in-place mutation.

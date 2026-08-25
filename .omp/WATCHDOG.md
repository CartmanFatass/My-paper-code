# HMASD continuous Advisor contract

This is the one role-aware continuous Advisor contract for the native OMP
workflow. OMP selects a child Advisor at creation from `task.agentAdvisor[agentName]`.
The resolved choice is persisted in that child session's `session_init` and
survives cold revival. It is not a direct mutation of an already running Hub job by job ID.
Ordinary workflow execution never toggles the mapping.

## Primary-role routing

Route strictly by the primary role recorded for the session:

```text
Root, hmasd-em, hmasd-cm     -> no Advisor
hmasd-implementer,
hmasd-implementer-terra      -> engineering
all other roles              -> no Advisor
```

Root's Advisor subsystem is disabled by `.omp/config.yml`. The only
`task.agentAdvisor` entries opt in the two Implementer leaves with
`opencode-go/glm-5.3:high`. Root, EM, CM, Reviewer, Verifier,
Project/Code/Research Scouts, Innovator, Critic, Principles Analyst, Experiment
Operator, both transports, Artifact Writer, and Recovery Manager receive no
continuous Advisor.


## Engineering route

For both Implementers, examine batching, genuinely independent parallelism,
applicable C++ backends, algorithmic complexity, peak memory, data movement,
interface/caller coverage, and focused behavioral evidence. Require
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

## Transcript-completeness boundary

Hub or IRC steering delivered to a running primary may be absent from the
Advisor transcript. The Advisor therefore must not classify deviation from the
initial assignment as a blocker solely because it cannot see a later parent
scope update. It may issue one non-blocking request to reconcile scope. Only an
observed hard-boundary violation remains actionable without that context.

Implementer assignments are scope-frozen after spawn. If parent steering
materially changes goals, non-goals, owned paths, authorization, or interfaces,
Root/CM cancels that leaf and dispatches a replacement with the complete
assignment instead of relying on unseen Hub text. Primary-agent paraphrase is
not evidence that its Advisor received the authoritative update.

Implementers are leaves and own no descendant task tree. Their Advisor may
assess only the implementer's complete primary transcript, assigned files,
diffs, and focused checks. Cross-direction or multi-manager assessment uses an
explicit checkpoint review with frozen envelopes and artifact references.

## Cold-revival contract

On startup, resume, or cold revival, OMP reconstructs the child session from its
persisted `session_init`, including the resolved per-agent-type Advisor choice.
The Advisor resumes read-only observation for that primary role; it does not
recompute a different model or claim authority over durable state. A material
role or generation change requires a newly resolved child session rather than
an in-place mutation.

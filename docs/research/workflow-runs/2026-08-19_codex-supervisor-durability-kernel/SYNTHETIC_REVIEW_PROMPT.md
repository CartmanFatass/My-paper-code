# Synthetic Review Prompt: Supervisor Durability Kernel V1

Copy everything below the line to another model that can read this branch.

```text
document_kind=synthetic_durability_kernel_review_prompt
branch=codex-supervisor-durability-kernel-v1
reviewed_commit=7593bd11
baseline=04eb640f4090993b251b204096cff26b44350b90
prior_review=REVISION_REQUIRED on f5b5a754
```

Review the HMASD Codex supervisor durability kernel on branch
`codex-supervisor-durability-kernel-v1`. This is synthetic control-plane
review, not Phase 1 / Stage 3 / Stage 4 live acceptance.

This slice answers the prior REVISION_REQUIRED review. Read first:

```text
AGENTS.md
docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md
docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md
docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md
docs/research/workflow-runs/2026-08-19_codex-supervisor-durability-kernel/SYNTHETIC_ACCEPTANCE.md
tools/codex_supervisor/durability/
```

Confirm whether these six closures now hold, then answer the original kernel
questions:

```text
1. Every submit_effect caller exhausts RESPONSE_OBSERVED / SUBMISSION_UNCERTAIN / INCIDENT and never treats uncertain as success.
2. Domain and effect transitions for wake first write, turn observation, and completion are one BEGIN IMMEDIATE transaction.
3. Mutating compatibility paths and new mutation_intents writes are gone. WakeRecovery uses submit_effect only.
4. CommandGateway writes only through TransitionKernel. scan_package() == [] and doctor reports actual scanner results.
5. Reconciliation and operator resolution read ObserverStore / App Server facts; they do not accept caller-authored turn/status/readiness.
6. Managed-turn and wake write claims re-check binding and semantic actor eligibility; a released actor cancels PREPARED effects.
```

Original kernel questions:

```text
1. Can any business module mutate a protected state outside the kernel?
2. Can any business module send a mutation outside the session owner?
3. Can WRITE_STARTED or later ever be automatically submitted again?
4. Can INCIDENT exit without one operator resolution?
5. Can an operator resolution partially commit or execute twice?
6. Can aggregate state and effect state contradict after any failpoint?
7. Can recovery perform a mutating App Server request?
8. Can raw prose affect state, routing, ACL, retry, or resolution?
9. Can a released/non-ACTIVE actor receive a managed effect?
10. Can live acceptance be inferred from synthetic evidence?
```

Also review SQLite transaction ownership, version/CAS correctness, async
cancellation, pending future cleanup, watcher lifetime, effect/raw
correlation, operator evidence validation, and migration conservatism.

Do not require live App Server. Missing live artifacts are not defects.

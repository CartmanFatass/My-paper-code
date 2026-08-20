# Synthetic Review Prompt: Supervisor Durability Kernel V1

Copy everything below the line to another model that can read this branch.

```text
document_kind=synthetic_durability_kernel_review_prompt
branch=codex-supervisor-durability-kernel-v1
baseline=04eb640f4090993b251b204096cff26b44350b90
```

Review the HMASD Codex supervisor durability kernel on branch
`codex-supervisor-durability-kernel-v1`. This is synthetic control-plane
review, not Phase 1 / Stage 3 / Stage 4 live acceptance.

Read first:

```text
AGENTS.md
docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md
docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md
docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md
tools/codex_supervisor/durability/
```

Answer these kernel questions, not a long module-local list:

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
```

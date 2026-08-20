# Synthetic Review Prompt: Supervisor Durability Kernel V1

Copy everything below the line to another model that can read this branch.

```text
document_kind=synthetic_durability_kernel_review_prompt
branch=codex-supervisor-durability-kernel-v1
reviewed_commit=a025bf80
baseline=04eb640f4090993b251b204096cff26b44350b90
prior_review=REVISION_REQUIRED on 7593bd11
```

Review the HMASD Codex supervisor durability kernel on branch
`codex-supervisor-durability-kernel-v1`. This is synthetic control-plane
review, not Phase 1 / Stage 3 / Stage 4 live acceptance.

This slice answers the prior REVISION_REQUIRED rereview of `7593bd11`.
Read first:

```text
AGENTS.md
docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md
docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md
docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md
docs/research/workflow-runs/2026-08-19_codex-supervisor-durability-kernel/SYNTHETIC_ACCEPTANCE.md
tools/codex_supervisor/durability/
```

Confirm these four remaining boundaries are closed:

```text
1. adopt_existing_thread classifies EffectSubmissionResult and does not attach or confirm on uncertain. All provisioning has a final semantic actor fence.
2. WakeRecovery has no domain-only fallback. WRITE_STARTED with exact turn evidence confirms the effect before delivery. Message delivery failure rolls back the whole txn.
3. Every PREPARED owner cancellation also sets linked effect CANCELLED_BEFORE_WRITE in the same transaction. Cancelled owners cannot submit_effect.
4. Resume reconciler uses thread_snapshots.status_type. CommandGateway refuses INCIDENT/unreconciled effects. Static scanner is AST/SQL allowlist and does not exempt TransitionKernel imports. Legacy SUBMITTED without response evidence maps to SUBMISSION_UNCERTAIN.
```

Then answer kernel questions 1-10 from the original prompt.

Do not require live App Server. Missing live artifacts are not defects.

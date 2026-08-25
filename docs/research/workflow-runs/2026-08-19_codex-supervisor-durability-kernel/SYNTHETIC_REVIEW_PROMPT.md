# Synthetic Review Prompt: Supervisor Durability Kernel V1

Copy everything below the line to another model that can read this branch.

```text
document_kind=synthetic_durability_kernel_review_prompt
branch=codex-supervisor-durability-kernel-v1
reviewed_commit=b520429e
baseline=04eb640f4090993b251b204096cff26b44350b90
prior_review=REVISION_REQUIRED on a025bf80
```

Review the HMASD Codex supervisor durability kernel on branch
`codex-supervisor-durability-kernel-v1`. This is synthetic control-plane
review, not Phase 1 / Stage 3 / Stage 4 live acceptance.

This slice answers the prior REVISION_REQUIRED rereview of `a025bf80`.
Read first:

```text
AGENTS.md
docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md
docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md
docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md
docs/research/workflow-runs/2026-08-19_codex-supervisor-durability-kernel/SYNTHETIC_ACCEPTANCE.md
tools/codex_supervisor/durability/
```

Confirm these remaining boundaries are closed:

```text
1. begin_submission/claim_first_submission are gone from the production package. SUBMITTING on a wake batch is recorded only with linked effect WRITE_STARTED.
2. TURN_OBSERVED_ACTIVE/COMPLETED completion accepts EFFECT_CONFIRMED or OPERATOR_RESOLVED with matching TURN_OBSERVED disposition. PREPARED+TURN_OBSERVED is rejected. WRITE_STARTED/RESPONSE_OBSERVED/SUBMISSION_UNCERTAIN is evidence-confirmed in the same resolution txn.
3. WakeRecovery.resume_once has a semantic actor fence (ACTIVE binding, eligible actor, kind/scope). Missing bridge fails closed.
4. Managed-turn and wake prepare create owner aggregate and linked PREPARED effect in one BEGIN IMMEDIATE transaction. submit_effect refuses a missing owner row.
5. Stored-only thread/resume confirmation requires snapshot last_event_seq or raw_message_seq greater than effect.raw_request_seq.
```

Then answer kernel questions 1-10 from the original prompt.

Do not require live App Server. Missing live artifacts are not defects.

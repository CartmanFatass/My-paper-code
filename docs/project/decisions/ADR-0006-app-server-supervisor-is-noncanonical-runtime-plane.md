+++
decision_id = "ADR-0006"
title = "App Server supervisor is a noncanonical runtime plane"
owner = "operational_root"
scope = "shared:codex-app-server-runtime"
status = "accepted"
decision_date = "2026-08-22"
supersedes = []
canonical_sources = [
  "docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md",
  "docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md",
  "docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md"
]
revisit_conditions = [
  "The supervisor is replaced by a different owner-authorized runtime implementation."
]
+++

# ADR-0006 App Server supervisor is a noncanonical runtime plane

The supervisor owns mechanical runtime, delivery, effect durability, wake, and
incident recovery. It does not own science, technical acceptance, Portfolio
meaning, ADRs, PROJECT_MAP, or canonical project state.

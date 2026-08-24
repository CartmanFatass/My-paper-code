# HMASD hard boundaries

These are the only always-applied workflow rules:

1. A local result-bearing command estimated over 7200 seconds requires a performance-reasonableness review attempt and explicit user approval.
2. Any operation that affects a branch outside the OMP-owned `omp/*` namespace requires user approval. Temporary assignment branches may affect only their declared scope and may integrate only into `omp/workflow`.
3. An external submission must have an exact target and Agentify operation, idempotency, fingerprint, and commitment state; unknown commitment never resends.
4. Exactly one Experiment Operator owns one exact result-bearing command.
5. Destructive targets and assignment-owned paths must resolve canonically.
6. Secrets are never exposed in prompts, state, logs, Dashboard APIs, or Git.
7. Scientific, numerical, RNG, checkpoint, bit-identity, and external-effect semantics are not silently changed.
8. A role, test, review, Advisor, Dashboard, lease, hash, or historical document cannot grant or deny ordinary authorized reversible work.
9. Unsafe memory plans are refused mechanically and must be reduced, batched, or sharded; they are not sent for approval.

Everything else belongs in Skills or agent prompts, not sticky rules.

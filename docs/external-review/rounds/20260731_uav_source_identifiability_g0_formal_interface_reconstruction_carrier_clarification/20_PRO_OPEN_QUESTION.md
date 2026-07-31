ZERO_COMPUTE_IMPLEMENTATION_ALIGNMENT_CLARIFICATION
review_type=IMPLEMENTATION_ALIGNMENT_CLARIFICATION

The accepted G0 scientific source is audit_target_commit=9239e3ec8a3d5b0ac3ba078f5598c19bde3c6d43. The prior frozen interface response is at the allow-listed formal_interface_raw path. Code PM inspected the exact target and returned this mechanical diagnosis:

1. `run_g0_episode` adds `behavioral_replay_certificate` to `controller_evidence` for Oracle runs, but `_reconstruct_controller_trace` returns only the base controller evidence. The exact comparison therefore reports missing `controller_evidence` for real Oracle runs, making Oracle EpisodeRunEvidence invalid and preventing the six-control/cell analysis inventory.
2. The frozen command/interface requires an external user-authorization reference and a pre-bound formal-root identity before root creation, but the frozen command fields do not define a carrier or schema for those values. The admission token is explicitly not user authorization.

Do not run code or compute. Do not redesign the scientific direction. Decide only the smallest contract correction needed to make the frozen G0 interface executable and result-selecting.

Return exactly these fields, each on one ASCII line:

G0_FORMAL_INTERFACE_CLARIFICATION=SOURCE_RECONSTRUCTION_ALLOWED|SOURCE_RECONSTRUCTION_FORBIDDEN_OR_CONTRACT_REOPEN_REQUIRED
G0_ORACLE_REPLAY_CERTIFICATE_RULE=INDEPENDENT_RECONSTRUCTION_MUST_INCLUDE_CERTIFICATE|SEPARATE_CERTIFICATE_COMPARISON_ALLOWED
G0_RUNTIME_CARRIER_RULE=EXPLICIT_WRAPPER_FIELDS_REQUIRED|EXACT_CARRIER_ALREADY_DEFINED
G0_FORMAL_INTERFACE_NEXT_ACTION=NEW_SOURCE_CANDIDATE_AND_ALIGNMENT|RUNNER_CONTRACT_ONLY|CONTRACT_REOPEN_REQUIRED

If any field selects a forbidden or undefined path, add one line beginning `G0_CLARIFICATION_BLOCKER=` naming the exact missing frozen choice. Do not return implementation code, thresholds, new evidence, compute commands, or permission questions.

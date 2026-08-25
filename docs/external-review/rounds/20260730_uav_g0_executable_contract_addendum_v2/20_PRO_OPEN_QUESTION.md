# G0 executable contract addendum v2

Return one ASCII-only executable addendum. Do not change the accepted G0
scientific direction, protected fields, or claim scope. Do not propose code,
experiments, learned models, formal execution, or a new scientific branch.

The addendum must be self-contained and freeze every result-sensitive field
that Code Project Manager still cannot choose mechanically:

1. Exact numeric initial geometry, reserve coordinates, hotspot coordinates,
   staging coordinates, gate coordinates, and perturbation laws/supports,
   including all map-normalization constants and realization-failure rules.
2. Exact or mechanically qualified oracle, same-information, and
   no-reallocation target/action realization. Include permutation-equivariant
   row/tie ordering, low-level safety/collision correction, target tracker
   qualification, oracle-certificate contents, and the exact failure semantics
   when the oracle certificate is missing or fails.
3. One-line definitions of rho_z(t), weakest-hotspot service, J_event,
   Q_ordinary, M_event, A_control, the episode binary access indicator,
   catastrophe, Delta_A, Delta_J, and Delta_M. Use explicit indices and
   domains; do not leave left-hand symbols implicit.
4. The exact estimator and confidence method for every first-match gate:
   episode pairing, sample counts, bootstrap seed and quantile rule, exact
   binomial interval, which gate uses which interval, and every inclusive or
   strict inequality.
5. An internally complete ASCII first-match truth table with exactly six
   priority rows: INVALID_UAV_G0_REALIZATION, INFEASIBLE_UAV_G0_SOURCE,
   ORACLE_ONLY_UAV_G0_SOURCE, NON_CAUSAL_UAV_G0_SOURCE,
   UNDERPOWERED_UAV_G0_SOURCE, and IDENTIFIED_UAV_G0_SOURCE. Each row must
   state the complete conjunction/disjunction of VALID, ORACLE, SAMEINFO, and
   CAUSAL pass/fail/open statuses and the stop-at-first-match rule.

Required protected fields, which must be repeated verbatim in the addendum:
physical_fleet_8|three_hotspots|single_unannounced_temporary_leave_rejoin|
no_learning|no_optimizer|no_checkpoint|128_paired_episode_ids|
10000_bootstrap|ownership_and_permutation_certificates|O(H*K_search)_K_search_le_16|
no_G51_merge

Required response format:

G0_EXECUTABLE_CONTRACT_ADDENDUM_V2_DISPOSITION=READY_FOR_CODE_CONTRACT
ASCII_ADDENDUM_BEGIN
<complete ASCII-only addendum with all five sections and six truth-table rows>
ASCII_ADDENDUM_END

If any field cannot be frozen from the allow-listed evidence, return instead:

G0_EXECUTABLE_CONTRACT_ADDENDUM_V2_DISPOSITION=REQUIRES_FURTHER_CLARIFICATION
MISSING_FIELDS=<exact field names only>

Do not return a scientific result, a preference, or a paraphrase. This is a
zero-compute contract clarification only.


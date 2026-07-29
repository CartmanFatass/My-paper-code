# External Pro: G50 common fast-anchor attribution code-science alignment audit

```text
semantic_author=research_operations_manager
scientific_authority=external_pro
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
round=20260729_g31_common_fast_anchor_attribution_g50_code_science_alignment_audit
stage_commit=5aeb3b7745847ca39edf556af29067506ead4c00
audit_target_commit=5aeb3b7745847ca39edf556af29067506ead4c00
design_stage_commit=b673032361b36dfc5531a06f4a8a37ce0e2c7b62
result_contract_stage_commit=22df8091c9f0cbd129f1473862186ce84bcb712a
compute_budget=zero
nonformal_compute_started=false
formal_compute_started=false
answer_now=forbidden
```

You are External GPT-5.6 Pro and the exclusive scientific authority for this
bounded read-only conformance diff. Read exactly the paths in
`01_SHARED_SOURCE_MANIFEST.md` from `stage_commit`. Do not edit or accept code,
run tests or compute, reopen G50 design, authorize a formal run, edit CDC or
select a successor.

## Alignment question

Does the accepted implementation at `audit_target_commit` instantiate the
frozen G50 design and result contract in the allow-listed evidence, without a
result-changing path? Judge only the exact source, runner, tests, code-science
index and frozen result-contract evidence in the allow-list.

Check all of these mechanically:

1. Phase A uses the complete historical G40 common-native-six fast-anchor graph,
   not an actor-only reconstruction, and creates two storage-disjoint arms from
   one identical fresh G50 initialization. The reference arm is
   `FAST_ANCHOR_THEN_SINGLE_IMMEDIATE`; the null arm is
   `SINGLE_IMMEDIATE_FROM_INITIALIZATION`.
2. Phase-A reference credit is exactly the G40 normalized
   `r_t-stopgrad(b_I_old(xi_t))` route, while null credit is exactly the G49
   centered/population-RMS normalized raw-reward route. The null baseline has
   zero reads into actor advantage, actor gradient, action/log-probability,
   checkpoint, evaluation and result selection. Shared two-output baseline
   shadow exposure, storage disjointness and G40 optimizer order remain equal.
3. The forced activation diagnostic uses only reference-owned pre-update
   gradients, excludes common entropy/baseline-loss terms, rejects nonfinite
   rows, maps both-zero scale to zero, activates only for `q_A>1e-6`, and
   requires every registered actor group finite and live in at least one
   objective with strict `>1e-12`; formal activation evidence is required for
   replicates `0|1|2`.
4. The phase boundary physically deletes all phase-A-only baseline, critic,
   delayed-residual, slow-critic and optimizer state, consumes zero optimizer
   steps and zero RNG, and creates fresh storage-disjoint actor-only Adam for
   exact G49 single-immediate phase B in both arms. No deleted residue or
   compatibility filler may survive projection.
5. The fixed inventories, seeds and pairing are exact: `H=48`, `K_search=0`,
   hypothetical trajectories/transitions zero; nonformal updates `10+10`,
   formal updates `100+100` per arm and three replicates; training/evaluation
   transitions `15360/6912` nonformal and `460800/165888` formal; total real
   transitions `22272/626688`; optimizer steps `80/2400`; bootstrap
   `250/10000`; formal seed replicate addition and nonformal offset `900000`
   are applied exactly once. The C++ CPU backend, no Python fallback,
   capacity/evaluation cell order, paired whole-episode bootstrap, confidence
   floors, `0.05` margin and first-match branch order are fail-closed.
6. Final-only six-checkpoint inventory, source/process/lifecycle/RNG pairing,
   exact manifest and checkpoint schema, reload validation, zero evaluation
   optimizer steps, and formal admission bindings are enforced. Formal
   admission remains blocked until this independent alignment audit supplies a
   matching `ALIGNED` stage and the runner binds it; no runtime or result claim
   is authorized by this audit.

If any item is not aligned, return the exact frozen assertion, conflicting
path/behavior and smallest in-contract correction. Do not propose a new
algorithm, threshold, evidence volume, experiment, formal run or successor.

Return exactly one terminal disposition token and no alternate token:

```text
AUDIT_DISPOSITION=ALIGNED
AUDIT_DISPOSITION=MISMATCH
AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY
```

`ALIGNED` requires every point to conform. `MISMATCH` requires the exact frozen
assertion, conflicting path/behavior and smallest correction. Use
`SCIENTIFIC_AMBIGUITY` only for a previously unstated result-changing choice
that prevents judgment.

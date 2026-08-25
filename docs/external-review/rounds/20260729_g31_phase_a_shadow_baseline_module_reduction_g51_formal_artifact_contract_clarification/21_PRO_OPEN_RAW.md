G51_FORMAL_ARTIFACT_CONTRACT=OUTCOME_CONDITIONAL

The previously frozen statement that all eight artifacts must exist for every preflight/formal outcome is corrected only as to the two final checkpoints and the two-process reload artifact. The five common terminal artifacts remain mandatory for all four registered branches. The prior contract already freezes that any one of the four schema-valid outcomes is admissible as a preflight outcome and that the preflight branch must not act as a favorable-result gate.

Common artifact inventory for every outcome

Every preflight root—and later every formal root—must contain:

train_manifest.json
evaluation_manifest.json
analysis_result.json
proof_inputs/shared_phase_A_trajectory.pt
proof/result_assessment.pt

The shared trajectory and result assessment must be exact-schema valid and SHA-256 bound by train_manifest.json. The evaluation and analysis manifests must bind their upstream manifest and assessment digests and independently reconstruct the stored result branch.

The runner always saves the one shared 8×48 trajectory and terminal assessment before applying branch-conditional checkpoint logic. It then emits checkpoints and a structural-witness payload only for exact removability; adverse outcomes use an empty checkpoint inventory and no structural witness.

No outcome may substitute:

placeholder checkpoints
dummy actor states
empty compatibility payloads
synthetic two-process reports
a caller-authored branch label
Outcome 1: INVALID_G50_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51

Required inventory:

train_manifest.json
evaluation_manifest.json
analysis_result.json
proof_inputs/shared_phase_A_trajectory.pt
proof/result_assessment.pt

Required train-manifest state:

result_branch=
INVALID_G50_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51

structural_witness=null
checkpoint_inventory={}
checkpoint_selection=null

execution_readiness_proof_only=false
two_process_proof=null
two_process_proof_artifact=null

passed=false

Required omissions:

checkpoints/reference_final.pt=absent
checkpoints/reduced_final.pt=absent
parallel_proof/two_process_equivalence.json=absent

evaluation_manifest.json and analysis_result.json remain mandatory. They must reconstruct the terminal invalid result envelope with:

evaluation_optimizer_steps=0
environment_transitions=0
canonical_final_checkpoint_projection_equal=null
registered_difference_vector=null
passed=false

A mechanically valid terminal INVALID branch is an allowed preflight outcome under the already frozen interface. An unhandled exception, malformed assessment, bad provenance, digest mismatch or incomplete lifecycle is not.

Outcome 2: UNREGISTERED_PHASE_A_SHADOW_BASELINE_COUPLING_G51

Required inventory is the same five common artifacts only.

Required train-manifest state:

result_branch=
UNREGISTERED_PHASE_A_SHADOW_BASELINE_COUPLING_G51

structural_witness=null
checkpoint_inventory={}
checkpoint_selection=null

execution_readiness_proof_only=false
two_process_proof=null
two_process_proof_artifact=null

passed=false

Required omissions:

checkpoints/reference_final.pt=absent
checkpoints/reduced_final.pt=absent
parallel_proof/two_process_equivalence.json=absent

proof/result_assessment.pt must contain the exact coupling failure evidence and zero-or-bounded optimizer ledger appropriate to the reconstructed coupling path. Evaluation and analysis must use the terminal source-result envelope and perform zero additional transitions and optimizer steps.

Outcome 3: PHASE_A_SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G51

Required inventory:

train_manifest.json
evaluation_manifest.json
analysis_result.json
proof_inputs/shared_phase_A_trajectory.pt
proof/result_assessment.pt

checkpoints/reference_final.pt
checkpoints/reduced_final.pt

parallel_proof/two_process_equivalence.json

Required train-manifest state:

result_branch=
PHASE_A_SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G51

structural_witness={
    phase_A_update_evidence,
    phase_boundary_evidence,
    phase_B_zero_step_certificate,
    inductive_equality_certificate
}

checkpoint_inventory={
    G50_FRESH_SINGLE_IMMEDIATE_WITH_PHASE_A_SHADOW_BASELINE,
    G50_FRESH_SINGLE_IMMEDIATE_WITHOUT_PHASE_A_BASELINE_MODULE
}

checkpoint_selection=final_only_proof_witness

execution_readiness_proof_only=true
two_process_proof=<exact validated report>
two_process_proof_artifact=
parallel_proof/two_process_equivalence.json

passed=true

Both checkpoint files must be exact-schema valid, SHA-256 bound and have bitwise-equal canonical actor projections. The evaluation manifest must reconstruct:

evaluation_kind=
exact_registered_D_G51_and_canonical_actor_projection

D_G51=0
canonical_final_checkpoint_projection_equal=true
passed=true

The two-process report is required only here because it independently reloads the exact-result checkpoint inventory. It is a mechanical, zero-transition, zero-optimizer attestation—not a second scientific witness. The aligned validator explicitly forbids an adverse result from claiming execution readiness or attaching this report.

Outcome 4: NUMERICALLY_UNRESOLVED_PHASE_A_SHADOW_BASELINE_REDUCTION_G51

Required inventory is again the five common artifacts only.

Required train-manifest state:

result_branch=
NUMERICALLY_UNRESOLVED_PHASE_A_SHADOW_BASELINE_REDUCTION_G51

structural_witness=null
checkpoint_inventory={}
checkpoint_selection=null

execution_readiness_proof_only=false
two_process_proof=null
two_process_proof_artifact=null

passed=false

Required omissions:

checkpoints/reference_final.pt=absent
checkpoints/reduced_final.pt=absent
parallel_proof/two_process_equivalence.json=absent

The assessment must preserve the exact pre-step or post-step numerical failure, its optimizer ledger and the absence of semantic coupling. Evaluation and analysis must reconstruct that branch from the assessment and take zero additional transitions or optimizer steps.

Fail-closed same-source preflight admission

Formal admission must process the preflight in this order:

Validate the three manifests, shared trajectory and result assessment, including exact source commit, schema, seed block, backend, work accounting and SHA-256 bindings.

Recompute the first-match branch from proof/result_assessment.pt and its optimizer ledger. The stored branch may not select its own artifact inventory.

Apply the branch-specific inventory above.

Reject any missing required artifact.

Reject any artifact forbidden for that branch.

Reject placeholders, empty synthetic checkpoint payloads, an adverse two-process report, or an exact branch lacking both checkpoints and its two-process report.

Require evaluation and analysis completion for all four outcomes, with zero additional transitions and optimizer steps.

Do not require or prefer EXACT_REMOVABILITY merely to admit the subsequent independent formal execution.

The aligned runner already enforces the core conditional rule: exact outcomes require a populated witness and checkpoint pair; nonexact outcomes require witness is None and checkpoints == {}. It also emits zero-work evaluation and analysis manifests for adverse branches rather than placeholder checkpoints.

Formal-root artifact rule

The independently executed formal root uses the same outcome-conditional inventory:

An exact formal outcome must emit both final checkpoints and the two-process report.

An invalid, coupling or numerically unresolved formal outcome must omit them and terminate with the five common artifacts plus zero-work evaluation and analysis.

The formal manifests must still bind the authorization token, aligned source/stage identities and same-source preflight digests frozen in the preceding admission clarification.

A formal adverse result is a valid conclusion-bearing G51 outcome, not an operational failure, provided its branch-conditioned artifacts and evidence are exact.

An operational exception, schema failure, digest failure or partial artifact lifecycle remains fail-closed and is not converted into any of the four scientific branches.

No adverse checkpoint schema is introduced. The absence of checkpoints and two-process evidence is itself the exact registered adverse-branch contract.
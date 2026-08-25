FROZEN_ASSERTION

The frozen selector distinguishes semantic coupling from a numerical mismatch:

UNREGISTERED_PHASE_A_SHADOW_BASELINE_COUPLING_G51 requires a concrete baseline-to-actor, optimizer, RNG, action, checkpoint, or diagnostic side-effect path.

NUMERICALLY_UNRESOLVED_PHASE_A_SHADOW_BASELINE_REDUCTION_G51 applies when the structural dependency graph is zero but an actual numerical kernel produces a nonzero registered actor/Adam difference, with no identified semantic coupling.

CONFLICTING_PATH_AND_BEHAVIOR

optimize_phase_A_update raises the single reason:

phase_A_pre_step_coupling_or_numeric_difference

for every pre-step discrepancy, including:

actor_assigned_gradient_bytes_equal=false
policy_loss_bytes_equal=false
teacher_logprob_bytes_equal=false
teacher_pre_tanh_bytes_equal=false
teacher_action_bytes_equal=false
baseline_loss_gradient_into_actor_count>0
actor_loss_gradient_into_baseline_count>0
plan_rng_unchanged=false

Thus the same exception represents both a reconstructed semantic coupling and a coupling-free numerical discrepancy.

build_result_evidence_envelope then checks the exception text for "coupling" before checking for "numeric". Because the mixed reason contains both words, it always sets:

semantic_coupling_detected=true

and classify_result consequently selects the coupling branch. The numerical branch is unreachable for a pre-step numeric mismatch carried by this reason.

Concrete target-bound counterexample:

static dependency certificate=valid
baseline_loss_gradient_into_actor_count=0
actor_loss_gradient_into_baseline_count=0
baseline RNG/side-effect counts=0

actor_assigned_gradient_bytes_equal=false

This is a coupling-free numerical discrepancy before either optimizer step. The frozen result is:

NUMERICALLY_UNRESOLVED_PHASE_A_SHADOW_BASELINE_REDUCTION_G51

but the target routes it to:

UNREGISTERED_PHASE_A_SHADOW_BASELINE_COUPLING_G51

The focused tests cover a pre-step coupling witness with baseline_loss_gradient_into_actor_count=1 and a separate post-step Adam numerical witness, but they do not cover a pre-step numerical mismatch with all semantic-coupling predicates zero.

SMALLEST_IN_CONTRACT_CORRECTION

Split the mixed pre-step failure into two exact reasons:

phase_A_pre_step_semantic_coupling
phase_A_pre_step_numeric_difference

Route to semantic coupling only when an actual coupling predicate is reconstructed, including nonzero cross-gradients, RNG or buffer mutation, hooks, shared storage, forbidden reads, or another registered side-effect path.

Route to numerical unresolved when:

static dependency certificate passes
all semantic-coupling predicates are zero
but a registered policy-loss, assigned-gradient,
action, pre-tanh, or log-probability equality fails

Update the allowed failure-reason inventory and validate_structural_assessment to accept both reasons with the same zero-completed-pass ledger, while preserving their distinct result branches. Add one focused witness with valid static evidence, zero coupling counts, and one pre-step numerical equality set false; it must select NUMERICALLY_UNRESOLVED_PHASE_A_SHADOW_BASELINE_REDUCTION_G51 with zero actor optimizer steps.

No change is required to the arms, deletion boundary, optimizer, thresholds, evidence volume, artifact schema, backend, or formal-admission closure.

AUDIT_DISPOSITION=MISMATCH
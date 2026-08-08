"""EOCIV Stage 0 registration: every constant the licensed preflight freezes.

Pro's acceptance ruling (`EOCIV_SIBLING_ACCEPTED_STAGE0_LICENSED`, archived at
``local_research/pro_reviews/eociv_gate_v21_license_v1/``) licensed Stage 0
only: implement the trainable common actor/backbone, critic and detached
valve; pool generation and the complete-block outcome harness; register every
architecture and optimizer constant; run deterministic no-update preflights.
No parameter update, optimizer step, D_fit collection, valve fitting,
calibration with learned scores, or outcome-bearing read is licensed.

This module is the registration.  It contains CONSTANTS ONLY — no model, no
environment, no training code — so that its digest freezes the design without
freezing any implementation detail it does not name.  The authoritative
mechanism implementations it points to live where the accepted capability
certificate pinned them (``capability_gate`` for seed derivation and
namespaces, ``actuation_runtime`` for the receipt/action binding); the Stage 0
gate verifies the harness consumes THOSE functions by identity, per the
ruling's "one authoritative implementation" requirement.

After Stage 0, no threshold, budget, architecture, pool, seed, or
stopping-rule change is authorized (ruling section 7).
"""

from __future__ import annotations

RAW_OUTPUT_BINDING = "eociv_lite.stage0_registration.v1"

#: The registered experiment this Stage 0 package serves, and the exact
#: revision at which Pro accepted the capability certificate.
EXPERIMENT_IDENTITY = "EOCIV-G32-SIBLING-4ARM-COMPLETE-BLOCK-D0"
STAGE0_IDENTITY = EXPERIMENT_IDENTITY + "-STAGE0"
PARENT_CAPABILITY_COMMIT = "4324460fd98089e74b40216ec7a1b8171f3dc5ef"

#: Registered actor training seeds (three, per the frozen budget).  Actor
#: seed is a FIXED CROSSED FACTOR of the design (ruling 6.8): worlds are
#: profile-qualified, not actor-seed-qualified.
ACTOR_TRAINING_SEEDS = (930_001, 930_002, 930_003)

#: Torch determinism policy (ruling 6.1; closes the recorded ambient
#: thread-count gap).
TORCH_INTRA_OP_THREADS = 1
TORCH_INTER_OP_THREADS = 1
TORCH_DETERMINISTIC_ALGORITHMS = True
DTYPE_POLICY = "float32"
DEVICE_POLICY = "cpu"

#: The environment-variable names the manifest must capture verbatim.
MANIFEST_ENV_VARS = (
    "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "PYTHONHASHSEED",
    "CUBLAS_WORKSPACE_CONFIG",
)

#: Source files whose SHA-256 digests the Stage 0 manifest must carry
#: (ruling 6.1), relative to the repository root.
DIGEST_FILES = (
    "envs/continuous_roster/runtime_capacity.py",
    "experiments/candidates/eociv_lite/sibling_env.py",
    "experiments/candidates/eociv_lite/actuation_runtime.py",
    "experiments/candidates/eociv_lite/capability_gate.py",
    "experiments/candidates/eociv_lite/stage0_registration.py",
    "experiments/candidates/eociv_lite/trainable_policy.py",
    "experiments/candidates/eociv_lite/outcome_harness.py",
    "experiments/candidates/eociv_lite/stage0_preflight.py",
)

#: FROZEN SHA-256 baselines (ruling 6.10 predicate 2): recorded at Stage 0
#: registration time for every digest file EXCEPT this registration module
#: itself (a file cannot contain its own digest).  The preflight aborts on
#: any recomputed digest differing from its baseline; this module's own
#: digest is emitted in the manifest and pinned externally by the commit and
#: the dispatch archive.
EXPECTED_SOURCE_DIGESTS = {
    "envs/continuous_roster/runtime_capacity.py":
        "bfac5ea6d19a754d37e377bafa03b167bbff0ea2ff8c814921877f239db76b9b",
    "experiments/candidates/eociv_lite/sibling_env.py":
        "be6dd1d575c3deb194b8935531828cf8ea9b92a9ffb61b6e3e96d42a9f69c91b",
    "experiments/candidates/eociv_lite/actuation_runtime.py":
        "b19ee6130c0945fbd284e64af5bf97b22f1c629a82b936fecce1120032918439",
    "experiments/candidates/eociv_lite/capability_gate.py":
        "adc1029cbb9d44c4cbe0225de031f3266ee41a1ee012b199ac7e01e5fbc2d127",
    "experiments/candidates/eociv_lite/trainable_policy.py":
        "ba7e5fd9524e5b1357e37f7957ecd0e72c0d827b6cdc47349d4a5ea0aa208846",
    "experiments/candidates/eociv_lite/outcome_harness.py":
        "ab8c2d660f44a54a8b99578e82a2d40a3965c52ac3347116eb7be9ac7b35ce6d",
    "experiments/candidates/eociv_lite/stage0_preflight.py":
        "f5c9158b09c197f4dcf917cb8d0d5b7498ca67ac3ac7693fad8c0f052c5aaa89",
}

# ---------------------------------------------------------------------------
# 6.2 Actor and recurrent-state contract.
# ---------------------------------------------------------------------------

ACTOR_CONTRACT = {
    "input_fields": {
        "member_observation": {
            "source": "CapacityRosterView.observations[member]",
            "dim": 10,
            "fields": (
                "capability_0", "capability_1", "presentation_priority",
                "published_load", "published_target_mix",
                "log1p_active_count", "age_fraction",
                "previous_action_0_unit", "previous_action_1_unit",
                "time_fraction",
            ),
        },
        "slot": {
            "source": "slot_features(actuation.slot) — focal receiver row at "
                      "the lifecycle boundary tick ONLY; zeros otherwise "
                      "(boundary-once ingestion, carried through recurrence)",
            "dim": 32,
        },
    },
    "slot_encoder": {"kind": "linear+tanh", "in": 32, "out": 16},
    "input_projector": {"kind": "linear+tanh", "in": 26, "out": 32},
    "recurrent": {"kind": "GRUCell", "input": 32, "hidden": 32},
    "action_head": {"kind": "linear", "in": 32, "out": 2},
    "action_distribution": {
        "kind": "diagonal Gaussian on the pre-squash kernel",
        "log_std": "single learnable per-dimension parameter, init ln(0.2)",
        "squash": "action = tanh(mean + std * member_owned_noise)",
        "noise": "the registered member-owned action-noise tape (common "
                 "across the four arms of a block); no ad-hoc RNG",
    },
    "parameter_init": (
        "torch.manual_seed(actor_training_seed); default torch initializers "
        "for Linear/GRUCell; log_std filled with ln(0.2)"
    ),
    "recurrent_lifecycle": {
        "fresh_join": "hidden initialized to zeros at the join boundary",
        "temporary_leave": "hidden RETAINED unchanged while inactive",
        "rejoin": "the retained hidden is restored (no reset)",
        "terminal_leave": "hidden zeroed and the row permanently masked",
        "inactive_rows": "hold state, emit the zero action (base convention)",
    },
    "normalization": "none — raw registered observation fields",
    "masking": "active_mask gates recurrent writes and action emission",
    "read_set_excludes": (
        "hidden shock state except through the real payload slot",
        "arm identity",
        "D_L / D_C decision identity",
        "post-action reward",
        "fold outcome",
        "future membership events",
    ),
}

# ---------------------------------------------------------------------------
# 6.3 Critic contract.
# ---------------------------------------------------------------------------

CRITIC_CONTRACT = {
    "read_set": {
        "base_critic_state": {"source": "CapacityRosterView.critic_state", "dim": 6},
        "active_set_summary": {
            "source": "active count / member_capacity", "dim": 1,
        },
        "pre_action_lifecycle": {
            "source": "counts of (joined, rejoined, temporarily_left, "
                      "terminally_left) in the CURRENT view's membership "
                      "change receipt",
            "dim": 4,
        },
    },
    "privileged_state": "NONE — no hidden shock, no arm label, no valve "
                        "decision, no post-reveal access",
    "architecture": {"kind": "MLP+tanh", "layers": (11, 64, 64, 1)},
    "valve_isolation": "the valve never reads critic parameters at inference",
}

# ---------------------------------------------------------------------------
# 6.4 Actor/critic optimization constants (frozen; UNUSED until Stage 1).
# ---------------------------------------------------------------------------

OPTIMIZATION = {
    "optimizer": "Adam (single instance over actor+critic parameters)",
    "learning_rate": 3e-4,
    "betas": (0.9, 0.999),
    "eps": 1e-8,
    "weight_decay": 0.0,
    "gamma": 0.99,
    "gae_lambda": 0.95,
    "ppo_clip": 0.2,
    "value_clip": 0.2,
    "entropy_coefficient": 0.01,
    "value_coefficient": 0.5,
    "gradient_clip_norm": 0.5,
    "rollout": {"parallel_envs": 16, "steps_per_env": 48},
    "minibatches_per_rollout": 4,
    "epochs_per_rollout": 4,
    "advantage_normalization": "per minibatch (mean/std, eps 1e-8)",
    "reward_normalization": "none",
    "observation_normalization": "none",
    "checkpoint_rule": "the TERMINAL fixed-budget checkpoint; no "
                       "best-checkpoint selection",
}

#: 6.4 fit-support assignment: domain-separated, pre-outcome inputs only.
FIT_SUPPORT_ASSIGNMENT = {
    "domain_label": "EOCIV-FIT-SUPPORT-V1",
    "inputs": ("pool", "profile_registration_id", "local_episode_id",
               "event_index"),
    "rule": (
        "u = first 8 bytes (big-endian) of sha256(label|pool|profile|"
        "episode|event) / 2**64; REAL if u < 1/2; NATIVE_NEUTRAL if "
        "u < 3/4; PATTERN_ONLY if u < 7/8; else PAYLOAD_KNOCKOUT"
    ),
    "schedule": {"REAL": "1/2", "NATIVE_NEUTRAL": "1/4",
                 "PATTERN_ONLY": "1/8", "PAYLOAD_KNOCKOUT": "1/8"},
    "no_outcome_inputs": "every input is a pre-outcome identifier; no "
                         "reward, return, valve score or learned quantity",
}

# ---------------------------------------------------------------------------
# 6.5 Valve and cross-fitting contract (frozen; fitting is Stage 2).
# ---------------------------------------------------------------------------

VALVE_CONTRACT = {
    "w_minus_schema": {
        "source": "sibling_env.w_minus JSON (sealed pre-body view)",
        "features": (
            "time / 47",
            "load",
            "target_mix",
            "active_count / member_capacity",
            "receiver spell_epoch",
            "receiver opened_at / 47",
            "source spell_epoch",
            "source opened_at / 47",
            "cell_class == CRITICAL (0/1)",
        ),
        "dim": 9,
    },
    "architecture": {"kind": "MLP+tanh", "layers": (9, 32, 32, 1),
                     "output": "sigmoid score s_phi in (0, 1)"},
    "loss": "binary cross-entropy against the reveal-utility target",
    "reveal_utility_target": (
        "1{realized reveal delta > 0} for randomized-real episodes vs their "
        "matched neutral counterfactual on D_policy (constructed in Stage 2 "
        "under the randomized propensity below; frozen here, not computed)"
    ),
    "randomized_propensity": {
        "domain_label": "EOCIV-VALVE-PROPENSITY-V1",
        "rule": "Bernoulli(1/2) real-vs-neutral from "
                "sha256(label|profile|episode|event); constant propensity "
                "1/2, so inverse-propensity weights are uniform",
    },
    "cross_fitting": {
        "folds": 4,
        "assignment": "whole-episode; fold = first 8 bytes of "
                      "sha256('EOCIV-VALVE-FOLD-V1'|profile|episode) mod 4",
        "grouping_key": "(profile_registration_id, local_episode_id)",
    },
    "optimizer": {"kind": "Adam", "learning_rate": 1e-3,
                  "betas": (0.9, 0.999), "eps": 1e-8, "weight_decay": 0.0},
    "passes": 20,
    "checkpoint_rule": "pass-20 parameters exactly",
    "invalid_scores": "missing / nonfinite / out-of-support -> HARD_OPEN",
    "threshold_kappa": "1/4",
    "inference_rule": "D_L(u) = 1{s_phi(W_u^-) >= 1/4}; invalid opens",
    "actor_critic_frozen_proof": "parameter digests before/after valve "
                                 "fitting must be byte-identical",
}

# ---------------------------------------------------------------------------
# 6.6 Calibration and exact-rate control (frozen; computed in Stage 2).
# ---------------------------------------------------------------------------

CONTROL_TAPE_CONTRACT = {
    "close_fraction": (
        "q_{c,p} = (# of D_L closures over all events of profile p's "
        "ancestry-disjoint D_cal pool) / (total D_cal events of p) — POOLED "
        "over the three lifecycle events, never stratified by the hidden "
        "CRITICAL/NEUTRAL class"
    ),
    "integer_allocation": (
        "target = q_{c,p} * N_events; close_count = floor(target) + "
        "1{frac(target) >= 1/2} (half-up, deterministic)"
    ),
    "permutation_key": (
        "events sorted by first 8 bytes of sha256('EOCIV-DC-PERM-V1'|"
        "profile|tape_epoch|local_episode_id|event_index); the first "
        "close_count events in that order CLOSE, the rest OPEN — exact rate "
        "by construction, deterministic tie-breaking by the full digest. "
        "tape_epoch is 0 for the registered experiment; any nonzero epoch "
        "(a re-draw) requires explicit external authorization and is an "
        "artifact identity component"
    ),
    "read_set": "(profile_registration_id, local_episode_id, event_index) "
                "and the frozen constants only — no payload, learned score, "
                "reward or outcome is an input",
    "gate_probe_isolation": (
        "sibling_env.control_tape_open (the Bernoulli-0.5 GATE probe) must "
        "be mechanically unreachable from focal execution: the outcome "
        "harness never calls it, and the Stage 0 preflight asserts the "
        "harness source does not reference it"
    ),
}

# ---------------------------------------------------------------------------
# 6.8 Bootstrap under shared actor-seed worlds (frozen implementation).
# ---------------------------------------------------------------------------

BOOTSTRAP_CONTRACT = {
    "resampling_cluster": "(profile_registration_id, focal_episode_id)",
    "actor_seed_role": "fixed crossed factor and artifact identity "
                       "component — NEVER an independent resampling draw",
    "procedure": (
        "within each profile, sample the 256 focal episode ids WITH "
        "replacement; use the SAME sampled ids and multiplicities for all "
        "three actor seeds; compute each four-arm contrast within (actor "
        "seed, root); average actor seeds equally within the sampled root; "
        "average roots equally within profile; average the three profiles "
        "equally"
    ),
    "replicates": 10_000,
    "bootstrap_seed_label": "EOCIV-BOOTSTRAP-V1",
    "intervals": "97.5% one-sided lower bounds for tau and tau_C; 90% TOST "
                 "for tau_N in [-0.01, 0.01]",
}

# ---------------------------------------------------------------------------
# 6.9 Negative-control decision algebra (frozen before Stage 1).
# ---------------------------------------------------------------------------

NEGATIVE_CONTROL_CONTRACT = {
    "clone_mapping": (
        "pattern-only and knockout clones re-run the LS and LR arms of each "
        "audit root with body_override = PATTERN_TOKEN and "
        "knockout_payload_body() respectively, holding ledger, shocks, "
        "draws, checkpoint, and noise tape fixed; tau_pattern and "
        "tau_knockout are the same diff-in-diff contrast as tau computed on "
        "those clones, in the same per-episode mean-return units"
    ),
    "rule": "max(|tau_pattern|, |tau_knockout|) <= (1/2) * max(tau, 0)",
    "tau_nonpositive": "if tau <= 0 the primary experiment FAILS; no ratio "
                       "or denominator-based rescue is permitted",
}

# ---------------------------------------------------------------------------
# 6.10 Preflight abort predicates (each terminal before any update).
# ---------------------------------------------------------------------------

ABORT_PREDICATES = (
    "gate_v21_not_green",
    "source_or_registration_digest_mismatch",
    "profile_qualified_seed_mismatch",
    "ancestry_overlap",
    "token_support_assignment_drift",
    "actor_or_valve_read_set_violation",
    "receipt_action_binding_violation",
    "direct_boundary_env_step_bypass",
    "lr_cr_presampling_or_trajectory_mismatch",
    "nonfinite_forward_value",
    "action_support_violation",
    "nondeterministic_replay",
    "incomplete_artifact_lifecycle",
)

#: The binding-failure runtime rule Pro attached to the acceptance: ANY
#: binding failure invalidates the ENTIRE arm episode — no catch-and-resume,
#: no retry from recurrent state already touched by a failed forward pass.
BINDING_FAILURE_RULE = "invalidate_entire_arm_episode_no_resume"

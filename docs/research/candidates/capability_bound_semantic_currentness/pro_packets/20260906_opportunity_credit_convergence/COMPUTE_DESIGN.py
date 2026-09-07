"""Read existing configuration/results and calculate a proposed B; never run a model."""
import ast
from fractions import Fraction
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
D = ROOT / "docs/research/candidates/capability_bound_semantic_currentness"
P = Path(__file__).resolve().parent
source = ROOT / "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/ppo.py"
constants = {}
for node in ast.parse(source.read_text(encoding="utf-8")).body:
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            constants[node.targets[0].id] = node.value.value
transitions = constants["EPISODE_TRANSITIONS"]
opportunities = constants["OPPORTUNITIES"]
rollout_episodes = constants["EPISODES_PER_ROLLOUT"]
epochs = constants["PPO_EPOCHS"]
minibatches = constants["MINIBATCHES_PER_EPOCH"]
old = json.loads((D / "pro_packets/20260905_two_seed_family_convergence/EXPOSURE_AND_COST.json").read_text())
b02 = json.loads((D / "CBSC_DIRECT_RETURN_B02_DM_ANALYSIS_20260905.json").read_text())
b03 = json.loads((D / "CBSC_DIRECT_RETURN_B03_DM_ANALYSIS_20260905.json").read_text())
per_arm = {
    "rollout_updates": 48,
    "train_episodes": 48 * rollout_episodes,
    "train_transitions": 48 * rollout_episodes * transitions,
    "train_decisions": 48 * rollout_episodes * opportunities,
    "adam_steps": 48 * epochs * minibatches,
    "evaluation_executions": 2 * 32,
    "evaluation_transitions": 2 * 32 * transitions,
}
per_arm["total_transitions"] = per_arm["train_transitions"] + per_arm["evaluation_transitions"]
public_null = []
for analysis, context in ((b02, b02["raw_context_means"]), (b03, b03["context_means"])):
    refresh = Fraction(str(context["ALWAYS_REFRESH"]))
    safe = Fraction(str(context["ALWAYS_SAFE"]))
    active = refresh + Fraction(2, 5) * opportunities
    assert safe == Fraction(1, 5) * active
    request_only = Fraction(3, 5) * active
    public_null.append({
        "object": analysis["object"], "seed": analysis["seed"],
        "mean_active_count": float(active), "always_refresh": float(refresh),
        "always_safe": float(safe), "derived_request_only": float(request_only),
        "request_only_minus_old_policy": float(request_only - refresh),
        "reading": "Outcome-informed aggregate arithmetic; no new evaluation or training."
    })
result = {
    "status": "PROPOSED_NOT_SELECTED",
    "method": "COMPUTE_DESIGN.py: AST-read fixed PPO constants and existing JSON; Fraction ledger arithmetic; no environment/model imports.",
    "source_constants": constants,
    "consultation_new_exposure": {"environment_transitions": 0, "optimizer_steps": 0, "evaluation_executions": 0, "parameter_movement_measurements": 0},
    "observed_formal_arms": old["observed_formal_arms"],
    "exposure_line": "Consultation adds zero training/evaluation. Existing four 768-Adam-step formal arms moved 18.6828676061% to 20.3270553056% of initial parameter L2. Proposed B04 retains 768 Adam steps per arm; changed-target movement/performance is unknown and is not extrapolated.",
    "proposed": {"object": "CBSC-OPPORTUNITY-CREDIT-B04", "seed": 21217, "independent_paired_training_runs": 1, "arms": 2, "checkpoints": [0, 48], "eval_roots": 32, "per_arm": per_arm, "pair": {k: 2*v for k,v in per_arm.items()}, "fixed_context_policies": 3, "existing_tape_ledger_passes": 3*32, "context_action_scores": 3*32*opportunities, "nested_search_candidates": 0, "formal_complete_cap_seconds_per_arm": 600},
    "proposed_added_verification": {"seed": 21211, "arms": 2, "rollouts_per_arm": 1, "adam_steps": 2*epochs*minibatches, "training_transitions": 2*rollout_episodes*transitions, "evaluation_executions": 2*2, "evaluation_transitions": 2*2*transitions, "total_learned_transitions": (2*rollout_episodes+2*2)*transitions, "pure_reward_array_checks_add_simulation": False, "complete_wall_cap_seconds_including_grace": 60, "prior_directory_focused_seconds": 132.15, "directory_cap_seconds": 300, "remaining_seconds": float(Fraction(300)-Fraction('132.15'))},
    "cost_reference": {"known_old_formal_wall_sum_seconds": 288.67, "b03_same_arm_complete_seconds": {a['arm']: a['cost']['outer_wall_seconds'] for a in b03['arms']}, "b02_complete_seconds_from_result_evidence": {"RAW-GRU": 79.69, "STRUCT-CURRENTNESS-GRU": 90.78}, "two_times_larger_historical_same_arm_seconds": {"RAW-GRU": 2*max(79.69,59.53), "STRUCT-CURRENTNESS-GRU": 2*max(90.78,58.67)}, "projection_law": "startup+host+sum48(project8+rollout8+PPO4x4)+sum2(eval32+checkpoint_io)+context_RAW+publication/readback+pairing_STRUCT+finish/grace", "uncertainty": "Historical reference and explicit 2x planning scenarios only; changed-target implementation/host load unmeasured. No speedup, upper bound, aggregate CPU or study elapsed claim; no calibration run."},
    "outcome_informed_public_request_reference": public_null,
    "headroom": "Matched tuned same-information generic/upper record absent. The derived public request rule is not tuned headroom.",
    "mei": {"absolute_episode_return": 0.25, "fraction_of_theoretical_24": 0.25/opportunities},
}
(P / "EXPOSURE_AND_COST.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8")
print(json.dumps({"formal_pair": result['proposed']['pair'], "new_exposure": result['consultation_new_exposure'], "derived_public_request_reference": public_null}, indent=2))

# G40 formal result evidence

```text
algorithm_id=CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40
source_id=CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_P0
assignment_id=CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_FORMAL_EXECUTION
run_root=logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_20260727_97a8b23_r1
source_commit=97a8b237e0cec6c2713dd2a710d324040fa3dfc2
formal=true
status=COMPLETE
operational_valid=true
operational_errors=[]
analysis_branch=G31_REALIZED_TAIL_CREDIT_ADVANTAGE_G40
candidate_iteration=31
iteration_cost=1_pending_external_pro_valid_result_disposition
backend=cpu
torch=2.7.0+cpu
torch_threads=1
native_backend=ContinuousRosterToyBatch_CPU_CPP
native_backend_required=true
native_backend_python_fallback=false
authorization_token=CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_FORMAL_AUTHORIZATION_V1
alignment_audit_id=CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_ALIGNMENT_AUDIT
alignment_disposition=ALIGNED
aligned_source_commit=97a8b237e0cec6c2713dd2a710d324040fa3dfc2
preflight_root=logs/nonformal_continuous_roster_native_six_credit_reduction_g40_cpu_20260727_97a8b23_pm1
train_exit_code=0
evaluate_exit_code=0
analyze_exit_code=0
train_manifest=logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_20260727_97a8b23_r1/train_manifest.json
evaluation_manifest=logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_20260727_97a8b23_r1/evaluation_manifest.json
analysis_result=logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_20260727_97a8b23_r1/analysis_result.json
train_seconds=2090.4843415000014
evaluate_seconds=63.884457200001634
analyze_seconds=6.278761500001565
formal_wall_clock_cap_seconds=28800
replicates=3
arms=2
training_capacity=8
evaluation_capacities=6|8|12
evaluation_cells=90
evaluation_episodes_per_cell=64
training_transitions=345600
evaluation_transitions=276480
total_real_transitions=622080
optimizer_steps=3000
bootstrap_resamples=10000
H=48
K_search=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
preflight_training_digest=a578036f3d6cd2758ecad84e5f1247ae3e32e12fb98f959d3c37f409e527943d
preflight_evaluation_digest=838b5fb205c1f2e8958341cf1f6c0fa46ae842569a42856d90579d5bae30d699
preflight_analysis_digest=1eeab8e08e597aac5b7e1d4af0cef6f9f02577f939f0dedb2e48289e8459d31a
```

All three formal manifests report `status=COMPLETE`, `formal=true`, the exact
source commit and empty operational errors. The native CPU C++ backend is
required and the Python fallback is false. This note records runtime and
artifact facts only; scientific disposition and portfolio edits remain
reserved for the registered External Pro result review.

## Mechanical analysis fields

```text
source_valid=true
branch_start_equality_pass=true
gae1_return_identity_valid=true
NATIVE6_G31_access_pass=true
NATIVE6_G31_access_confident_fail=false
NATIVE6_TEAM_GAE1_access_pass=false
NATIVE6_TEAM_GAE1_access_confident_fail=true
ordinary_access_pass=false
ordinary_access_confident_fail=true
g31_access_pass=true
g31_access_confident_fail=false
ordinary_noninferior=false
material_g31_advantage=true
primary_g31_minus_ordinary_ci95=[0.06704132045693341,0.1557242038934778,0.31810768025681196]
capacity_6_g31_minus_ordinary_ci95=[0.06848805394183226,0.12427010129890624,0.23113810250567207]
capacity_8_g31_minus_ordinary_ci95=[0.06886050296327625,0.16183986212917326,0.3330175855642817]
capacity_12_g31_minus_ordinary_ci95=[0.061520675288085816,0.18062541318021386,0.38723403292472997]
utility_floor=0.9
event_floor=0.85
segment_floor=0.85
stochastic_floor=0.8
minimum_replicate_floor=0.85
process_noninferiority_margin=-0.05
credit_margin=0.05
```

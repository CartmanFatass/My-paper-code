#!/usr/bin/env bash
set -euo pipefail

PYTHON_EXE="${PYTHON_EXE:-python}"
EXPERIMENTS=("base_reward_pure" "topology_role_probe" "topology_role_low_reward" "transition_semantic_low_reward")
TOTAL_TIMESTEPS=320000
EVAL_INTERVAL=80000
EVAL_EPISODES=20
NUM_ENVS=8
ROLLOUT_LENGTH=500
SKILL_INTERVAL=10
N_AGENTS=6
SEEDS=("1")
PRESET="S7-S1"
SCENARIO="energy"
COLLECTOR_BACKEND="subproc"
COLLECTOR_START_METHOD="spawn"
SKILL_LIFETIME_CANDIDATES="3,7,13,24"
SMDP_BOOTSTRAP_COEF=0.25
LOG_ROOT="logs"
DEVICE="cpu"
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run_ha_ctse_experiments.sh [options]

Options:
  --python PATH                  Python executable. Default: $PYTHON_EXE or python
  --experiment NAME[,NAME...]     Experiment(s): all, base_reward_pure,
                                 duration_short_reward_pure,
                                 fixed_duration_reward_pure,
                                 low_actor_g_reward_pure,
                                 topology_role_probe, topology_role_low_reward,
                                 topology_potential_low_reward,
                                 transition_semantic_low_reward,
                                 topology_role_transition_combo
  --total-timesteps N             Default: 320000
  --eval-interval N               Default: 80000
  --eval-episodes N               Default: 20
  --num-envs N                    Default: 8
  --rollout-length N              Default: 500
  --skill-interval N              Default: 10
  --n-agents N                    Default: 6
  --seeds CSV                     Default: 1
  --preset NAME                   Default: S7-S1
  --scenario NAME                 Default: energy
  --collector-backend NAME        Default: subproc
  --collector-start-method NAME   Default: spawn
  --skill-lifetime-candidates CSV Default: 3,7,13,24
  --smdp-bootstrap-coef X         Default: 0.25
  --log-root DIR                  Default: logs
  --device NAME                   Default: cpu
  --dry-run                       Print commands only

Examples:
  bash scripts/run_ha_ctse_experiments.sh --experiment topology_role_probe
  bash scripts/run_ha_ctse_experiments.sh --experiment all --total-timesteps 1280000
EOF
}

split_experiments() {
  local raw="$1"
  IFS=',' read -r -a EXPERIMENTS <<< "$raw"
}

split_seeds() {
  local raw="$1"
  IFS=',' read -r -a SEEDS <<< "$raw"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      PYTHON_EXE="$2"; shift 2 ;;
    --experiment)
      split_experiments "$2"; shift 2 ;;
    --total-timesteps)
      TOTAL_TIMESTEPS="$2"; shift 2 ;;
    --eval-interval)
      EVAL_INTERVAL="$2"; shift 2 ;;
    --eval-episodes)
      EVAL_EPISODES="$2"; shift 2 ;;
    --num-envs)
      NUM_ENVS="$2"; shift 2 ;;
    --rollout-length)
      ROLLOUT_LENGTH="$2"; shift 2 ;;
    --skill-interval)
      SKILL_INTERVAL="$2"; shift 2 ;;
    --n-agents)
      N_AGENTS="$2"; shift 2 ;;
    --seeds)
      split_seeds "$2"; shift 2 ;;
    --preset)
      PRESET="$2"; shift 2 ;;
    --scenario)
      SCENARIO="$2"; shift 2 ;;
    --collector-backend)
      COLLECTOR_BACKEND="$2"; shift 2 ;;
    --collector-start-method)
      COLLECTOR_START_METHOD="$2"; shift 2 ;;
    --skill-lifetime-candidates)
      SKILL_LIFETIME_CANDIDATES="$2"; shift 2 ;;
    --smdp-bootstrap-coef)
      SMDP_BOOTSTRAP_COEF="$2"; shift 2 ;;
    --log-root)
      LOG_ROOT="$2"; shift 2 ;;
    --device)
      DEVICE="$2"; shift 2 ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2 ;;
  esac
done

if [[ " ${EXPERIMENTS[*]} " == *" all "* ]]; then
  EXPERIMENTS=(
    "base_reward_pure"
    "duration_short_reward_pure"
    "fixed_duration_reward_pure"
    "low_actor_g_reward_pure"
    "topology_role_probe"
    "topology_role_low_reward"
    "topology_potential_low_reward"
    "transition_semantic_low_reward"
    "topology_role_transition_combo"
  )
fi

join_command() {
  printf '%q ' "$@"
}

run_ha_ctse() {
  local name="$1"
  local seed="$2"
  shift 2
  local run_skill_lifetime_candidates="$SKILL_LIFETIME_CANDIDATES"
  if [[ $# -gt 0 && "$1" != --* ]]; then
    run_skill_lifetime_candidates="$1"
    shift
  fi
  local steps_k=$((TOTAL_TIMESTEPS / 1000))
  local log_dir="${LOG_ROOT}/ha_ctse_process_${name}_seed${seed}_${steps_k}k"
  local common=(
    -m ha_ctse_process.train
    --config ha_ctse_process.config
    --scenario "$SCENARIO"
    --preset "$PRESET"
    --seed "$seed"
    --n_agents "$N_AGENTS"
    --collector_backend "$COLLECTOR_BACKEND"
    --collector_start_method "$COLLECTOR_START_METHOD"
    --num_envs "$NUM_ENVS"
    --rollout_length "$ROLLOUT_LENGTH"
    --skill_interval "$SKILL_INTERVAL"
    --skill_lifetime_candidates "$run_skill_lifetime_candidates"
    --total_timesteps "$TOTAL_TIMESTEPS"
    --eval_interval "$EVAL_INTERVAL"
    --eval_episodes "$EVAL_EPISODES"
    --save_interval 20
    --checkpoint_keep_last 4
    --plot_interval 10
    --low_clip_epsilon 0.1
    --smdp_bootstrap_coef "$SMDP_BOOTSTRAP_COEF"
    --device "$DEVICE"
    --log_dir "$log_dir"
  )
  local cmd=("$PYTHON_EXE" "${common[@]}" "$@")
  echo
  echo "===== HA-CTSE experiment: ${name} seed=${seed} ====="
  join_command "${cmd[@]}"
  echo
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  mkdir -p "$log_dir"
  "${cmd[@]}"
}

isolated_process_off=(
  --process_reward_injection none
  --process_reward_coef 0.0
  --process_contrast_coef 0.0
  --process_outcome_coef 0.0
  --process_prior_coef 0.0
  --process_shortcut_coef 0.0
  --context_shortcut_coef 0.0
  --process_shortcut_margin_coef 0.0
  --disable_process_posterior_mi
  --disable_outcome_residual_probe
)

for experiment in "${EXPERIMENTS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    case "$experiment" in
      base_reward_pure)
        run_ha_ctse "s7s1_base_reward_pure_${NUM_ENVS}env" "$seed" \
          "${isolated_process_off[@]}" \
          --disable_process_reward \
          --disable_transition_skill_discriminator \
          --disable_topology_role_probe
        ;;
      duration_short_reward_pure)
        run_ha_ctse "s7s1_duration_short_reward_pure_${NUM_ENVS}env" "$seed" "1,2,3" \
          "${isolated_process_off[@]}" \
          --disable_process_reward \
          --disable_transition_skill_discriminator \
          --disable_topology_role_probe
        ;;
      fixed_duration_reward_pure)
        run_ha_ctse "s7s1_fixed_duration7_reward_pure_${NUM_ENVS}env" "$seed" "7" \
          "${isolated_process_off[@]}" \
          --disable_process_reward \
          --disable_transition_skill_discriminator \
          --disable_topology_role_probe
        ;;
      low_actor_g_reward_pure)
        run_ha_ctse "s7s1_low_actor_g_reward_pure_${NUM_ENVS}env" "$seed" \
          "${isolated_process_off[@]}" \
          --enable_low_actor_team_code \
          --disable_process_reward \
          --disable_transition_skill_discriminator \
          --disable_topology_role_probe
        ;;
      topology_role_probe)
        run_ha_ctse "s7s1_topology_role_probe_no_reward_${NUM_ENVS}env" "$seed" \
          "${isolated_process_off[@]}" \
          --disable_process_reward \
          --disable_transition_skill_discriminator \
          --topology_role_coef 1.0 \
          --topology_role_injection none \
          --topology_role_reward_coef 0.0
        ;;
      topology_role_low_reward)
        run_ha_ctse "s7s1_topology_role_low_reward_${NUM_ENVS}env" "$seed" \
          "${isolated_process_off[@]}" \
          --disable_transition_skill_discriminator \
          --topology_role_coef 1.0 \
          --topology_role_injection low_only \
          --topology_role_reward_coef 0.02 \
          --topology_role_reward_clip 0.03
        ;;
      topology_potential_low_reward)
        run_ha_ctse "s7s1_topology_potential_short_low_reward_${NUM_ENVS}env" "$seed" "1,2,3" \
          "${isolated_process_off[@]}" \
          --disable_transition_skill_discriminator \
          --disable_topology_role_probe \
          --enable_topology_potential_shaping \
          --topology_potential_injection low_only \
          --topology_potential_coef 0.05 \
          --topology_potential_clip 0.08 \
          --topology_potential_discount_mode delta \
          --topology_potential_warmup_steps 0
        ;;
      transition_semantic_low_reward)
        run_ha_ctse "s7s1_transition_semantic_low_reward_${NUM_ENVS}env" "$seed" \
          "${isolated_process_off[@]}" \
          --disable_topology_role_probe \
          --transition_skill_coef 0.5 \
          --transition_skill_prior_coef 0.25 \
          --transition_context_shortcut_coef 0.25 \
          --transition_skill_reward_coef 0.02 \
          --transition_skill_reward_clip 0.05 \
          --transition_skill_reward_warmup_steps 80000
        ;;
      topology_role_transition_combo)
        run_ha_ctse "s7s1_topology_role_transition_combo_${NUM_ENVS}env" "$seed" \
          "${isolated_process_off[@]}" \
          --topology_role_coef 1.0 \
          --topology_role_injection low_only \
          --topology_role_reward_coef 0.02 \
          --topology_role_reward_clip 0.03 \
          --transition_skill_coef 0.5 \
          --transition_skill_prior_coef 0.25 \
          --transition_context_shortcut_coef 0.25 \
          --transition_skill_reward_coef 0.01 \
          --transition_skill_reward_clip 0.03 \
          --transition_skill_reward_warmup_steps 80000
        ;;
      *)
        echo "Unknown experiment: ${experiment}" >&2
        exit 2
        ;;
    esac
  done
done

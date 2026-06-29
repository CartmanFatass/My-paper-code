#!/usr/bin/env bash
# P2-lite: recovery-window contribution credit runner.
#
# Staged per the P2-lite gate (see memory/ALGORITHM_PRINCIPLES.md ->
# "P2-lite: Recovery-Window Contribution Credit"):
#   1. p2_recovery_precheck  -> compute-on / reward-OFF.  MANDATORY FIRST.
#        Verify Pre-check 2 before enabling any reward:
#          delta_phi_soft_nonzero_rate_when_full_disconnect > 0
#          delta_phi_soft_nonzero_rate_when_near_disconnect  > 0
#          p2_corr_phi_recovery_event                        > 0
#   2. p2_recovery_h0  -> high_team signed shaping reward (first mainline reward).
#   3. p2_recovery_h1  -> high_per_agent signed shaping reward.
#   4. p2_recovery_l1  -> low_only positive-only ablation.
#
# All runs use a SHORT-duration reward-pure base (P0.3 decision: do NOT stack the
# harmful long learned-duration set under the credit experiment).  Everything
# else intrinsic stays OFF so P2 is the only moving variable.
set -euo pipefail

PYTHON_EXE="${PYTHON_EXE:-python}"
EXPERIMENTS=("p2_recovery_precheck")
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
SKILL_LIFETIME_CANDIDATES="1,2,3"   # short-duration base per P0.3
SMDP_BOOTSTRAP_COEF=0.25
P2_REWARD_COEF=0.05
P2_REWARD_CLIP=0.5
LOG_ROOT="logs"
DEVICE="cpu"
DRY_RUN=0
REQUIRE_GATE=1            # block h0/h1/l1 unless the precheck gate is positive
GATE_CSV=""               # explicit precheck CSV; empty => auto-discover under LOG_ROOT
GATE_MIN_DELTA_PHI=0.0    # delta_phi_soft_nonzero_rate_* must exceed this
GATE_MIN_CORR=0.0         # p2_corr_phi_recovery_event must exceed this

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run_p2_recovery_experiments.sh [options]

Options:
  --python PATH                   Python executable. Default: $PYTHON_EXE or python
  --experiment NAME[,NAME...]      Experiment(s): all, p2_recovery_precheck,
                                  p2_recovery_h0, p2_recovery_h1, p2_recovery_l1
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
  --skill-lifetime-candidates CSV Default: 1,2,3 (short base)
  --smdp-bootstrap-coef X         Default: 0.25
  --p2-reward-coef X              Default: 0.05
  --p2-reward-clip X              Default: 0.5
  --log-root DIR                  Default: logs
  --device NAME                   Default: cpu
  --skip-gate                     Do NOT enforce the precheck gate before h0/h1/l1
  --gate-csv PATH                 Precheck train_updates.csv to gate on (else auto)
  --gate-min-delta-phi X          delta_phi nonzero-rate threshold. Default: 0.0
  --gate-min-corr X               p2_corr_phi_recovery_event threshold. Default: 0.0
  --dry-run                       Print commands only

Gate behaviour:
  Before the FIRST h0/h1/l1 reward variant, the runner evaluates Pre-check 2 from
  the latest p2_recovery_precheck train_updates.csv (via scripts/p2_gate_check.py)
  and aborts unless delta_phi_soft_nonzero_rate_{full,near} and
  p2_corr_phi_recovery_event are positive.  Pass --skip-gate to override.

Examples:
  bash scripts/run_p2_recovery_experiments.sh
  bash scripts/run_p2_recovery_experiments.sh --experiment p2_recovery_precheck --seeds 1,2
  bash scripts/run_p2_recovery_experiments.sh --experiment p2_recovery_h0 --total-timesteps 1280000
EOF
}

split_experiments() { IFS=',' read -r -a EXPERIMENTS <<< "$1"; }
split_seeds() { IFS=',' read -r -a SEEDS <<< "$1"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python) PYTHON_EXE="$2"; shift 2 ;;
    --experiment) split_experiments "$2"; shift 2 ;;
    --total-timesteps) TOTAL_TIMESTEPS="$2"; shift 2 ;;
    --eval-interval) EVAL_INTERVAL="$2"; shift 2 ;;
    --eval-episodes) EVAL_EPISODES="$2"; shift 2 ;;
    --num-envs) NUM_ENVS="$2"; shift 2 ;;
    --rollout-length) ROLLOUT_LENGTH="$2"; shift 2 ;;
    --skill-interval) SKILL_INTERVAL="$2"; shift 2 ;;
    --n-agents) N_AGENTS="$2"; shift 2 ;;
    --seeds) split_seeds "$2"; shift 2 ;;
    --preset) PRESET="$2"; shift 2 ;;
    --scenario) SCENARIO="$2"; shift 2 ;;
    --collector-backend) COLLECTOR_BACKEND="$2"; shift 2 ;;
    --collector-start-method) COLLECTOR_START_METHOD="$2"; shift 2 ;;
    --skill-lifetime-candidates) SKILL_LIFETIME_CANDIDATES="$2"; shift 2 ;;
    --smdp-bootstrap-coef) SMDP_BOOTSTRAP_COEF="$2"; shift 2 ;;
    --p2-reward-coef) P2_REWARD_COEF="$2"; shift 2 ;;
    --p2-reward-clip) P2_REWARD_CLIP="$2"; shift 2 ;;
    --log-root) LOG_ROOT="$2"; shift 2 ;;
    --device) DEVICE="$2"; shift 2 ;;
    --skip-gate) REQUIRE_GATE=0; shift ;;
    --gate-csv) GATE_CSV="$2"; shift 2 ;;
    --gate-min-delta-phi) GATE_MIN_DELTA_PHI="$2"; shift 2 ;;
    --gate-min-corr) GATE_MIN_CORR="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ " ${EXPERIMENTS[*]} " == *" all "* ]]; then
  EXPERIMENTS=("p2_recovery_precheck" "p2_recovery_h0" "p2_recovery_h1" "p2_recovery_l1")
fi

join_command() { printf '%q ' "$@"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE_DONE=0
# Evaluate the Pre-check 2 gate once, lazily, right before the first reward variant.
# In `all` mode this runs AFTER the precheck has produced its CSV; in a reward-only
# invocation it gates on a pre-existing precheck CSV.
ensure_precheck_gate() {
  if [[ "$REQUIRE_GATE" != "1" || "$GATE_DONE" == "1" ]]; then return 0; fi
  GATE_DONE=1
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[p2-gate] dry-run: skipping gate evaluation"
    return 0
  fi
  local gate_args=(
    "${SCRIPT_DIR}/p2_gate_check.py"
    --log-root "$LOG_ROOT"
    --min-delta-phi "$GATE_MIN_DELTA_PHI"
    --min-corr "$GATE_MIN_CORR"
  )
  if [[ -n "$GATE_CSV" ]]; then gate_args+=(--gate-csv "$GATE_CSV"); fi
  echo
  echo "----- P2 Pre-check 2 gate (reward variants require a positive precheck) -----"
  if ! "$PYTHON_EXE" "${gate_args[@]}"; then
    echo "Aborting reward variants: precheck gate not satisfied. Pass --skip-gate to override." >&2
    exit 3
  fi
}

run_ha_ctse() {
  local name="$1"; local seed="$2"; shift 2
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
    --skill_lifetime_candidates "$SKILL_LIFETIME_CANDIDATES"
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
  echo "===== P2-lite experiment: ${name} seed=${seed} ====="
  join_command "${cmd[@]}"
  echo
  if [[ "$DRY_RUN" == "1" ]]; then return 0; fi
  mkdir -p "$log_dir"
  "${cmd[@]}"
}

# Short-duration reward-pure base: everything intrinsic OFF except the P2 path.
reward_pure_base=(
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
  --disable_process_reward
  --disable_transition_skill_discriminator
  --disable_topology_role_probe
)

for experiment in "${EXPERIMENTS[@]}"; do
  for seed in "${SEEDS[@]}"; do
    case "$experiment" in
      p2_recovery_precheck)
        # Compute-on / reward-OFF.  MANDATORY first run (validates Pre-check 2).
        run_ha_ctse "s7s1_p2_recovery_precheck_${NUM_ENVS}env" "$seed" \
          "${reward_pure_base[@]}" \
          --enable_p2_recovery_compute
        ;;
      p2_recovery_h0)
        # High-level shared signed Phi_total reward (first mainline reward run).
        ensure_precheck_gate
        run_ha_ctse "s7s1_p2_recovery_h0_high_team_${NUM_ENVS}env" "$seed" \
          "${reward_pure_base[@]}" \
          --enable_p2_recovery_reward \
          --p2_recovery_reward_level high_team \
          --p2_recovery_reward_coef "$P2_REWARD_COEF" \
          --p2_recovery_reward_clip "$P2_REWARD_CLIP"
        ;;
      p2_recovery_h1)
        # Per-agent signed phi_i high-level credit.
        ensure_precheck_gate
        run_ha_ctse "s7s1_p2_recovery_h1_per_agent_${NUM_ENVS}env" "$seed" \
          "${reward_pure_base[@]}" \
          --enable_p2_recovery_reward \
          --p2_recovery_reward_level high_per_agent \
          --p2_recovery_reward_coef "$P2_REWARD_COEF" \
          --p2_recovery_reward_clip "$P2_REWARD_CLIP"
        ;;
      p2_recovery_l1)
        # Low-level positive-only ablation (NOT the mainline conclusion).
        ensure_precheck_gate
        run_ha_ctse "s7s1_p2_recovery_l1_low_only_${NUM_ENVS}env" "$seed" \
          "${reward_pure_base[@]}" \
          --enable_p2_recovery_reward \
          --p2_recovery_reward_level low_only \
          --p2_recovery_reward_coef "$P2_REWARD_COEF" \
          --p2_recovery_reward_clip "$P2_REWARD_CLIP"
        ;;
      *)
        echo "Unknown experiment: ${experiment}" >&2
        exit 2
        ;;
    esac
  done
done

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_EXE="${PYTHON_EXE:-python}"
EXPERIMENTS="${EXPERIMENTS:-low_actor_g_reward_pure,fixed_duration_reward_pure}"
SEEDS="${SEEDS:-1,2}"
TOTAL_TIMESTEPS="${TOTAL_TIMESTEPS:-1280000}"
EVAL_INTERVAL="${EVAL_INTERVAL:-160000}"
EVAL_EPISODES="${EVAL_EPISODES:-20}"
NUM_ENVS="${NUM_ENVS:-32}"
ROLLOUT_LENGTH="${ROLLOUT_LENGTH:-500}"
SKILL_INTERVAL="${SKILL_INTERVAL:-10}"
N_AGENTS="${N_AGENTS:-6}"
PRESET="${PRESET:-S7-S1}"
SCENARIO="${SCENARIO:-energy}"
COLLECTOR_BACKEND="${COLLECTOR_BACKEND:-subproc}"
COLLECTOR_START_METHOD="${COLLECTOR_START_METHOD:-spawn}"
SKILL_LIFETIME_CANDIDATES="${SKILL_LIFETIME_CANDIDATES:-3,7,13,24}"
SMDP_BOOTSTRAP_COEF="${SMDP_BOOTSTRAP_COEF:-0.25}"
LOG_ROOT="${LOG_ROOT:-logs_cloud_p0_32env}"
DEVICE="${DEVICE:-cpu}"
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run_p0_cloud_32env.sh [options]

Defaults:
  experiments: low_actor_g_reward_pure,fixed_duration_reward_pure
  seeds:       1,2
  envs:        32
  steps:       1280000
  device:      cpu

Options:
  --python PATH
  --experiments CSV
  --seeds CSV
  --total-timesteps N
  --eval-interval N
  --eval-episodes N
  --num-envs N
  --rollout-length N
  --skill-interval N
  --n-agents N
  --preset NAME
  --scenario NAME
  --skill-lifetime-candidates CSV
  --smdp-bootstrap-coef X
  --log-root DIR
  --device cpu|cuda
  --dry-run

Examples:
  bash scripts/run_p0_cloud_32env.sh --dry-run
  bash scripts/run_p0_cloud_32env.sh --seeds 1 --total-timesteps 320000
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      PYTHON_EXE="$2"; shift 2 ;;
    --experiments|--experiment)
      EXPERIMENTS="$2"; shift 2 ;;
    --seeds)
      SEEDS="$2"; shift 2 ;;
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
    --preset)
      PRESET="$2"; shift 2 ;;
    --scenario)
      SCENARIO="$2"; shift 2 ;;
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

echo "HA-CTSE P0 cloud run"
echo "  root:              $ROOT_DIR"
echo "  experiments:       $EXPERIMENTS"
echo "  seeds:             $SEEDS"
echo "  num_envs:          $NUM_ENVS"
echo "  total_timesteps:   $TOTAL_TIMESTEPS"
echo "  eval_interval:     $EVAL_INTERVAL"
echo "  candidates:        $SKILL_LIFETIME_CANDIDATES"
echo "  device:            $DEVICE"
echo "  log_root:          $LOG_ROOT"

cmd=(
  bash scripts/run_ha_ctse_experiments.sh
  --python "$PYTHON_EXE"
  --experiment "$EXPERIMENTS"
  --seeds "$SEEDS"
  --total-timesteps "$TOTAL_TIMESTEPS"
  --eval-interval "$EVAL_INTERVAL"
  --eval-episodes "$EVAL_EPISODES"
  --num-envs "$NUM_ENVS"
  --rollout-length "$ROLLOUT_LENGTH"
  --skill-interval "$SKILL_INTERVAL"
  --n-agents "$N_AGENTS"
  --preset "$PRESET"
  --scenario "$SCENARIO"
  --collector-backend "$COLLECTOR_BACKEND"
  --collector-start-method "$COLLECTOR_START_METHOD"
  --skill-lifetime-candidates "$SKILL_LIFETIME_CANDIDATES"
  --smdp-bootstrap-coef "$SMDP_BOOTSTRAP_COEF"
  --log-root "$LOG_ROOT"
  --device "$DEVICE"
)

if [[ "$DRY_RUN" == "1" ]]; then
  cmd+=(--dry-run)
fi

"${cmd[@]}"

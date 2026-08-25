#!/usr/bin/env bash

set -Eeuo pipefail

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"
LOG_ROOT="${LOG_ROOT:-/root/autodl-tmp/HMASD/logs}"
RUN_ROOT="${RUN_ROOT:-$LOG_ROOT/r39a_fixed_hmasd_anchor_$(date +%Y%m%d_%H%M%S)}"
DRY_RUN="${DRY_RUN:-0}"

readonly SEED=39039
readonly NUM_ENVS=32
readonly NUM_WORKERS=8
readonly ENVS_PER_WORKER=4
readonly ROLLOUT_LENGTH=500
readonly EPISODE_STEPS=500
readonly SKILL_INTERVAL=10
readonly TOTAL_TIMESTEPS=1600000
readonly EXPECTED_UPDATES=100
readonly EVAL_SEED_START=139039
readonly EVAL_EPISODES=100
readonly POLICY_RNG_SEED=239039
readonly BOOTSTRAP_REPETITIONS=10000
readonly BOOTSTRAP_SEED=40039039
readonly DEVICE=cuda
readonly ANALYZER="scripts/analyze_r39a_fixed_hmasd_anchor.py"

TRAIN_ROOT="$RUN_ROOT/training"
RESULT_ROOT="$RUN_ROOT/result"
RESULT_JSON="$RESULT_ROOT/r39a_fixed_hmasd_anchor.json"
CURRENT_PHASE=setup
RUN_INITIALIZED=0
TERMINAL_STATUS_WRITTEN=0

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run_r39a_fixed_hmasd_anchor.sh [--dry-run]

Optional environment variables:
  PYTHON_BIN=python
  LOG_ROOT=/root/autodl-tmp/HMASD/logs
  RUN_ROOT=/root/autodl-tmp/HMASD/logs/<unique-run-id>
  DRY_RUN=1

The scientific contract is fixed: seed 39039, CUDA, 32 environments in an
8x4 sharded collector, 1,600,000 steps / 100 updates, followed by the exact
100-episode stochastic R39A evaluation. Contract parameters cannot be
overridden through this runner.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ "$DRY_RUN" != "0" && "$DRY_RUN" != "1" ]]; then
  echo "DRY_RUN must be 0 or 1." >&2
  exit 2
fi

format_command() {
  printf '%q ' "$@"
  printf '\n'
}

write_status() {
  local path="$1"
  shift
  local temporary="${path}.tmp.${BASHPID:-$$}"
  printf '%s\n' "$@" > "$temporary"
  mv -f "$temporary" "$path"
}

write_failure() {
  local phase="$1"
  local reason="$2"
  local exit_code="$3"
  write_status "$RUN_ROOT/runner_status.txt" \
    "finished=$(date -Is)" \
    "state=failed" \
    "phase=$phase" \
    "reason=$reason" \
    "exit_code=$exit_code" \
    "seed=$SEED" \
    "total_timesteps=$TOTAL_TIMESTEPS" \
    "expected_updates=$EXPECTED_UPDATES" \
    "training_root=$TRAIN_ROOT" \
    "result_json=$RESULT_JSON"
  TERMINAL_STATUS_WRITTEN=1
}

on_exit() {
  local exit_code=$?
  if [[ "$DRY_RUN" == "0" && "$RUN_INITIALIZED" == "1" && "$TERMINAL_STATUS_WRITTEN" == "0" ]]; then
    write_failure "$CURRENT_PHASE" runner_aborted "$exit_code"
  fi
}
trap on_exit EXIT

TRAIN_COMMAND=(
  "$PYTHON_BIN" train_multiproc_config_1.py
  --config config_1
  --algorithm hmasd_original
  --scenario energy
  --preset S7-S1
  --seed "$SEED"
  --n_agents 8
  --scenario7_experiment_arm C
  --scenario7_reward_variant qos_fixed_safety
  --collector_backend sharded
  --num_envs "$NUM_ENVS"
  --num_workers "$NUM_WORKERS"
  --envs_per_worker "$ENVS_PER_WORKER"
  --rollout_length "$ROLLOUT_LENGTH"
  --skill_interval "$SKILL_INTERVAL"
  --total_timesteps "$TOTAL_TIMESTEPS"
  --disable_eval
  --no-scenario7_comparison_gate
  --strict_hmasd_alignment
  --r39a_strict_contract
  --metrics_mode light
  --training_metrics_level light
  --device "$DEVICE"
  --console_log_level info
  --exp_name r39a_fixed_hmasd_anchor
  --log_dir "$TRAIN_ROOT"
)

echo "R39A current-interface fixed-k HMASD anchor"
echo "  repository_root:       $ROOT"
echo "  run_root:              $RUN_ROOT"
echo "  training_root:         $TRAIN_ROOT"
echo "  result_root:           $RESULT_ROOT"
echo "  seed:                  $SEED"
echo "  topology:              sharded ${NUM_WORKERS}x${ENVS_PER_WORKER} (${NUM_ENVS} envs)"
echo "  rollout / episode:     ${ROLLOUT_LENGTH} / ${EPISODE_STEPS}"
echo "  skill interval:        $SKILL_INTERVAL"
echo "  training exposure:     ${TOTAL_TIMESTEPS} steps / ${EXPECTED_UPDATES} updates"
echo "  evaluation:            ${EVAL_EPISODES} stochastic episodes from seed ${EVAL_SEED_START}"
echo "  policy RNG seed:       $POLICY_RNG_SEED"
echo "  bootstrap:             ${BOOTSTRAP_REPETITIONS} repetitions, seed ${BOOTSTRAP_SEED}"
echo "  device:                $DEVICE"
echo "  dry_run:               $DRY_RUN"
echo "PHASE training"
format_command "${TRAIN_COMMAND[@]}"

if [[ "$DRY_RUN" == "1" ]]; then
  checkpoint_placeholder="$TRAIN_ROOT/<structured-run>/models/hmasd_original_multiproc_final.pt"
  summary_placeholder="$TRAIN_ROOT/<structured-run>/final_training_summary.json"
  dry_analyze_command=(
    "$PYTHON_BIN" "$ANALYZER" analyze
    --checkpoint "$checkpoint_placeholder"
    --training-summary "$summary_placeholder"
    --output-dir "$RESULT_ROOT"
    --device cuda
    --eval-seed-start "$EVAL_SEED_START"
    --eval-episodes "$EVAL_EPISODES"
    --episode-steps "$EPISODE_STEPS"
    --policy-rng-seed "$POLICY_RNG_SEED"
    --bootstrap-repetitions "$BOOTSTRAP_REPETITIONS"
    --bootstrap-seed "$BOOTSTRAP_SEED"
  )
  dry_validate_command=(
    "$PYTHON_BIN" "$ANALYZER" validate-result
    --output-dir "$RESULT_ROOT"
  )
  echo "PHASE evaluation (checkpoint and summary paths are resolved uniquely after training)"
  format_command "${dry_analyze_command[@]}"
  echo "PHASE validate-result"
  format_command "${dry_validate_command[@]}"
  echo "Dry run complete; no directories, logs, commands, or status files were written."
  TERMINAL_STATUS_WRITTEN=1
  exit 0
fi

if [[ ! -f train_multiproc_config_1.py ]]; then
  echo "Training entry point is missing: train_multiproc_config_1.py" >&2
  exit 2
fi
if [[ ! -f "$ANALYZER" ]]; then
  echo "Required analyzer is missing: $ANALYZER" >&2
  exit 2
fi
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 && [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  exit 2
fi
if [[ -e "$RUN_ROOT/runner_status.txt" ]]; then
  echo "RUN_ROOT already contains a runner status; refusing to overwrite: $RUN_ROOT" >&2
  exit 2
fi

mkdir -p "$TRAIN_ROOT" "$RESULT_ROOT"
RUN_INITIALIZED=1

CURRENT_PHASE=cuda-preflight
write_status "$RUN_ROOT/runner_status.txt" \
  "started=$(date -Is)" \
  "state=running" \
  "phase=cuda-preflight" \
  "seed=$SEED" \
  "device=$DEVICE" \
  "num_envs=$NUM_ENVS" \
  "num_workers=$NUM_WORKERS" \
  "envs_per_worker=$ENVS_PER_WORKER" \
  "total_timesteps=$TOTAL_TIMESTEPS" \
  "expected_updates=$EXPECTED_UPDATES" \
  "training_root=$TRAIN_ROOT" \
  "result_json=$RESULT_JSON"

if ! "$PYTHON_BIN" -c 'import torch; raise SystemExit(0 if torch.cuda.is_available() else "CUDA unavailable; R39A forbids CPU fallback")'; then
  write_failure cuda-preflight cuda_unavailable 2
  exit 2
fi

format_command "${TRAIN_COMMAND[@]}" > "$RUN_ROOT/training_command.txt"
CURRENT_PHASE=training
write_status "$RUN_ROOT/runner_status.txt" \
  "started=$(date -Is)" \
  "state=running" \
  "phase=training" \
  "seed=$SEED" \
  "device=$DEVICE" \
  "num_envs=$NUM_ENVS" \
  "num_workers=$NUM_WORKERS" \
  "envs_per_worker=$ENVS_PER_WORKER" \
  "rollout_length=$ROLLOUT_LENGTH" \
  "skill_interval=$SKILL_INTERVAL" \
  "total_timesteps=$TOTAL_TIMESTEPS" \
  "expected_updates=$EXPECTED_UPDATES" \
  "training_command=$RUN_ROOT/training_command.txt" \
  "training_output=$RUN_ROOT/training_output.log" \
  "training_root=$TRAIN_ROOT" \
  "result_json=$RESULT_JSON"

if "${TRAIN_COMMAND[@]}" > "$RUN_ROOT/training_output.log" 2>&1; then
  training_exit=0
else
  training_exit=$?
  write_failure training training_command_failed "$training_exit"
  exit "$training_exit"
fi

CURRENT_PHASE=resolve-training-output
mapfile -t checkpoints < <(
  find "$TRAIN_ROOT" -type f -path '*/models/hmasd_original_multiproc_final.pt' -print
)
if [[ "${#checkpoints[@]}" -ne 1 ]]; then
  echo "Expected exactly one final checkpoint under $TRAIN_ROOT; found ${#checkpoints[@]}." >&2
  write_failure resolve-training-output final_checkpoint_count_mismatch 3
  exit 3
fi
CHECKPOINT="${checkpoints[0]}"
TRAIN_RUN_DIR="$(dirname "$(dirname "$CHECKPOINT")")"
TRAINING_SUMMARY="$TRAIN_RUN_DIR/final_training_summary.json"
if [[ ! -s "$CHECKPOINT" ]]; then
  echo "Final checkpoint is missing or empty: $CHECKPOINT" >&2
  write_failure resolve-training-output final_checkpoint_missing 3
  exit 3
fi
if [[ ! -s "$TRAINING_SUMMARY" ]]; then
  echo "Final training summary is missing or empty: $TRAINING_SUMMARY" >&2
  write_failure resolve-training-output final_training_summary_missing 3
  exit 3
fi

ANALYZE_COMMAND=(
  "$PYTHON_BIN" "$ANALYZER" analyze
  --checkpoint "$CHECKPOINT"
  --training-summary "$TRAINING_SUMMARY"
  --output-dir "$RESULT_ROOT"
  --device cuda
  --eval-seed-start "$EVAL_SEED_START"
  --eval-episodes "$EVAL_EPISODES"
  --episode-steps "$EPISODE_STEPS"
  --policy-rng-seed "$POLICY_RNG_SEED"
  --bootstrap-repetitions "$BOOTSTRAP_REPETITIONS"
  --bootstrap-seed "$BOOTSTRAP_SEED"
)
VALIDATE_COMMAND=(
  "$PYTHON_BIN" "$ANALYZER" validate-result
  --output-dir "$RESULT_ROOT"
)

format_command "${ANALYZE_COMMAND[@]}" > "$RUN_ROOT/analysis_command.txt"
CURRENT_PHASE=evaluation
write_status "$RUN_ROOT/runner_status.txt" \
  "updated=$(date -Is)" \
  "state=running" \
  "phase=evaluation" \
  "seed=$SEED" \
  "training_steps=$TOTAL_TIMESTEPS" \
  "completed_updates=$EXPECTED_UPDATES" \
  "eval_seed_start=$EVAL_SEED_START" \
  "eval_episodes=$EVAL_EPISODES" \
  "policy_rng_seed=$POLICY_RNG_SEED" \
  "checkpoint=$CHECKPOINT" \
  "training_summary=$TRAINING_SUMMARY" \
  "analysis_command=$RUN_ROOT/analysis_command.txt" \
  "analysis_output=$RUN_ROOT/analysis_output.log" \
  "result_json=$RESULT_JSON"

if "${ANALYZE_COMMAND[@]}" > "$RUN_ROOT/analysis_output.log" 2>&1; then
  analysis_exit=0
else
  analysis_exit=$?
  write_failure evaluation analyzer_command_failed "$analysis_exit"
  exit "$analysis_exit"
fi

format_command "${VALIDATE_COMMAND[@]}" > "$RUN_ROOT/validate_command.txt"
CURRENT_PHASE=validate-result
if validation_output="$("${VALIDATE_COMMAND[@]}" 2>&1)"; then
  printf '%s\n' "$validation_output" > "$RUN_ROOT/validation_output.log"
else
  validation_exit=$?
  printf '%s\n' "$validation_output" > "$RUN_ROOT/validation_output.log"
  write_failure validate-result output_validation_failed "$validation_exit"
  exit "$validation_exit"
fi

if [[ ! -s "$RESULT_JSON" ]]; then
  echo "Validated result JSON is missing or empty: $RESULT_JSON" >&2
  write_failure validate-result result_json_missing 3
  exit 3
fi

mapfile -t result_fields < <(
  "$PYTHON_BIN" -c \
    'import json, sys; result=json.load(open(sys.argv[1], encoding="utf-8")); print(result["status"]); print(str(bool(result["implementation_valid"])).lower())' \
    "$RESULT_JSON"
)
if [[ "${#result_fields[@]}" -ne 2 ]]; then
  echo "Could not parse status and implementation_valid from $RESULT_JSON" >&2
  write_failure validate-result result_contract_parse_failed 3
  exit 3
fi
SCIENTIFIC_STATUS="${result_fields[0]}"
IMPLEMENTATION_VALID="${result_fields[1]}"
if [[ "$IMPLEMENTATION_VALID" != "true" ]]; then
  echo "R39A analyzer reported an invalid implementation: $SCIENTIFIC_STATUS" >&2
  write_failure validate-result invalid_implementation 3
  exit 3
fi
case "$SCIENTIFIC_STATUS" in
  PASS_R39A_CURRENT_FIXED_HMASD_ANCHOR|VALID_FAIL_R39A_NO_CURRENT_HMASD_ANCHOR) ;;
  *)
    echo "Unexpected R39A scientific status: $SCIENTIFIC_STATUS" >&2
    write_failure validate-result unexpected_scientific_status 3
    exit 3
    ;;
esac

write_status "$RUN_ROOT/runner_status.txt" \
  "finished=$(date -Is)" \
  "state=succeeded" \
  "phase=complete" \
  "exit_code=0" \
  "seed=$SEED" \
  "device=$DEVICE" \
  "training_steps=$TOTAL_TIMESTEPS" \
  "completed_updates=$EXPECTED_UPDATES" \
  "eval_episodes=$EVAL_EPISODES" \
  "implementation_valid=$IMPLEMENTATION_VALID" \
  "scientific_status=$SCIENTIFIC_STATUS" \
  "checkpoint=$CHECKPOINT" \
  "training_summary=$TRAINING_SUMMARY" \
  "result_json=$RESULT_JSON"
TERMINAL_STATUS_WRITTEN=1

echo "R39A runner completed operationally: $RUN_ROOT"
echo "Scientific status: $SCIENTIFIC_STATUS"

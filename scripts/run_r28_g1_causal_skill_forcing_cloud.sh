#!/usr/bin/env bash

set -Eeuo pipefail

# Set before any Python process initializes CUDA.
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="${REPO_DIR:-$SCRIPT_ROOT}"
DATA_ROOT="${DATA_ROOT:-/root/autodl-tmp/HMASD}"
RUN_ROOT="${RUN_ROOT:-$DATA_ROOT/logs/r28_g1_causal_skill_forcing_reward_$(date +%Y%m%d_%H%M%S)}"
PYTHON_BIN="${PYTHON_BIN:-python}"
REQUESTED_DEVICE="${DEVICE:-cuda}"
SOURCE_CHECKPOINT="${SOURCE_CHECKPOINT:-$REPO_DIR/dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt}"
SCORER_PATH="${SCORER_PATH:-$REPO_DIR/logs/r28_g0_action_process_target_20260713_175600/r28_g0_scorer_final.pt}"
ALLOW_OCCUPIED_GPU="${ALLOW_OCCUPIED_GPU:-0}"
R28_G1_TOPOLOGY_AUTHORIZATION="${R28_G1_TOPOLOGY_AUTHORIZATION:-}"
R28_G1_LAUNCH_AUTHORIZATION="${R28_G1_LAUNCH_AUTHORIZATION:-}"
MODE="${MODE:-commands}"

readonly NUM_ENVS=16
readonly ROLLOUT_LENGTH=500
readonly SKILL_INTERVAL=10
readonly SOURCE_TOTAL_TIMESTEPS=1000000
readonly TOPOLOGY_TOTAL_TIMESTEPS=1008000
readonly FINAL_TOTAL_TIMESTEPS=1160000
readonly EVAL_INTERVAL=80000
readonly EVAL_EPISODES=20
readonly FINAL_UPDATE=52
readonly TOPOLOGY_SEED=28030
readonly TOPOLOGY_AUTHORIZATION_TOKEN="EXP-20260713-r28-g1-topology-authorized"
readonly LAUNCH_AUTHORIZATION_TOKEN="EXP-20260713-r28-g1-launch-authorized"
readonly -a ARMS=(probe_only sham_reward real_reward)
readonly -a SEEDS=(28031 28032 28033)

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run_r28_g1_causal_skill_forcing_cloud.sh commands
  bash scripts/run_r28_g1_causal_skill_forcing_cloud.sh topology
  bash scripts/run_r28_g1_causal_skill_forcing_cloud.sh run
  bash scripts/run_r28_g1_causal_skill_forcing_cloud.sh evidence
  bash scripts/run_r28_g1_causal_skill_forcing_cloud.sh analyze
  bash scripts/run_r28_g1_causal_skill_forcing_cloud.sh all

The default mode is `commands`, which only prints the frozen commands. No mode
silently falls back to CPU or serial execution. `run`, `evidence`, and
`analyze` require the typed topology marker produced under the same RUN_ROOT.

Configurable paths:
  REPO_DIR=/root/HMASD
  DATA_ROOT=/root/autodl-tmp/HMASD
  RUN_ROOT=/root/autodl-tmp/HMASD/logs/<timestamped-run>
  SOURCE_CHECKPOINT=/absolute/path/to/R25-arm0-final.pt
  SCORER_PATH=/root/HMASD/logs/r28_g0_action_process_target_20260713_175600/r28_g0_scorer_final.pt
  PYTHON_BIN=python

Operational safety:
  ALLOW_OCCUPIED_GPU=0 is the default. A detected compute process stops the
  phase. Set it to 1 only after the user explicitly chooses to share the GPU.
  topology mode requires:
    R28_G1_TOPOLOGY_AUTHORIZATION=EXP-20260713-r28-g1-topology-authorized
  run/evidence/analyze require:
    R28_G1_LAUNCH_AUTHORIZATION=EXP-20260713-r28-g1-launch-authorized
  all requires both tokens; topology approval alone can never start training.

Screen example (detached; invoke twice with the same RUN_ROOT):
  RUN_ROOT=/root/autodl-tmp/HMASD/logs/r28_g1_<timestamp> \
    screen -S r28_g1 -dm bash -lc \
    'cd /root/HMASD && RUN_ROOT=/root/autodl-tmp/HMASD/logs/r28_g1_<timestamp> R28_G1_TOPOLOGY_AUTHORIZATION=EXP-20260713-r28-g1-topology-authorized R28_G1_LAUNCH_AUTHORIZATION=EXP-20260713-r28-g1-launch-authorized bash scripts/run_r28_g1_causal_skill_forcing_cloud.sh all'
  screen -r r28_g1

The first `all` invocation stops after a newly measured topology PASS. Review
the topology marker, then repeat the same command to start the registered run.
EOF
}

mode_seen=0
while (( $# > 0 )); do
  case "$1" in
    commands|topology|run|evidence|analyze|all)
      if (( mode_seen == 1 )); then
        echo "Only one mode may be selected." >&2
        exit 2
      fi
      MODE="$1"
      mode_seen=1
      ;;
    --dry-run)
      MODE=commands
      mode_seen=1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

case "$MODE" in
  commands|topology|run|evidence|analyze|all) ;;
  *) echo "MODE must be commands, topology, run, evidence, analyze, or all." >&2; exit 2 ;;
esac
if [[ "$REQUESTED_DEVICE" != "cuda" ]]; then
  echo "R28-G1 requires DEVICE=cuda; CPU fallback is forbidden." >&2
  exit 2
fi
readonly DEVICE=cuda
if [[ "$ALLOW_OCCUPIED_GPU" != "0" && "$ALLOW_OCCUPIED_GPU" != "1" ]]; then
  echo "ALLOW_OCCUPIED_GPU must be 0 or 1." >&2
  exit 2
fi
if [[ "$REPO_DIR" != /* || "$DATA_ROOT" != /* || "$RUN_ROOT" != /* || \
      "$SOURCE_CHECKPOINT" != /* || "$SCORER_PATH" != /* ]]; then
  echo "REPO_DIR, DATA_ROOT, RUN_ROOT, SOURCE_CHECKPOINT, and SCORER_PATH must be absolute paths." >&2
  exit 2
fi
case "$SOURCE_CHECKPOINT" in
  */dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt) ;;
  *)
    echo "SOURCE_CHECKPOINT must be the registered R25 arm0 final path." >&2
    exit 2
    ;;
esac
if [[ "$(basename "$SCORER_PATH")" != "r28_g0_scorer_final.pt" ]]; then
  echo "SCORER_PATH must name the frozen r28_g0_scorer_final.pt artifact." >&2
  exit 2
fi
case "${RUN_ROOT%/}/" in
  "${DATA_ROOT%/}"/*) ;;
  *)
    echo "RUN_ROOT must be a child of DATA_ROOT so large outputs stay on the data disk." >&2
    exit 2
    ;;
esac

cd "$REPO_DIR"

readonly TRAIN_SCRIPT="ha_ctse_process/train.py"
readonly COLLECTOR_SCRIPT="scripts/collect_r26_g1_windows.py"
readonly R26_ANALYZER="scripts/analyze_r26_g1_behavior.py"
readonly FAMILY_ANALYZER="scripts/analyze_r28_g1_family.py"
readonly TOPOLOGY_ROOT="$RUN_ROOT/topology"
readonly TOPOLOGY_MARKER="$TOPOLOGY_ROOT/topology_passed.json"

ACTIVE_PIDS=()

format_command() {
  printf '%q ' "$@"
  printf '\n'
}

write_status() {
  local path="$1"
  shift
  local temporary="${path}.tmp.${BASHPID:-$$}"
  mkdir -p "$(dirname "$path")"
  printf '%s\n' "$@" > "$temporary"
  mv -f "$temporary" "$path"
}

status_succeeded() {
  local path="$1"
  [[ -f "$path" ]] && grep -qx 'state=succeeded' "$path"
}

cleanup_active_children() {
  local pid
  for pid in "${ACTIVE_PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done
  for pid in "${ACTIVE_PIDS[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
  ACTIVE_PIDS=()
}

on_signal() {
  local signal_name="$1"
  trap - INT TERM
  cleanup_active_children
  if [[ -d "$RUN_ROOT" ]]; then
    write_status "$RUN_ROOT/runner_status.txt" \
      "finished=$(date -Is)" \
      "state=interrupted" \
      "mode=$MODE" \
      "signal=$signal_name" \
      "device=cuda"
  fi
  exit 130
}

install_signal_traps() {
  trap 'on_signal INT' INT
  trap 'on_signal TERM' TERM
}

train_command() {
  local arm="$1"
  local seed="$2"
  local total_timesteps="$3"
  local eval_interval="$4"
  local log_dir="$5"
  TRAIN_COMMAND=(
    "$PYTHON_BIN" -m ha_ctse_process.train
    --config ha_ctse_process.config
    --scenario energy
    --preset S7-S1
    --seed "$seed"
    --n_agents 6
    --collector_backend subproc
    --collector_start_method spawn
    --num_envs "$NUM_ENVS"
    --rollout_length "$ROLLOUT_LENGTH"
    --skill_interval "$SKILL_INTERVAL"
    --skill_lifetime_candidates 1,2,3,4
    --total_timesteps "$total_timesteps"
    --eval_interval "$eval_interval"
    --eval_episodes "$EVAL_EPISODES"
    --eval_action_mode deterministic
    --save_interval 10
    --checkpoint_keep_last 3
    --plot_interval 10
    --low_ppo_epochs 15
    --reward_ratio_guard_mode kill
    --device cuda
    --resume_from "$SOURCE_CHECKPOINT"
    --r28_g1_arm "$arm"
    --r28_g1_scorer_path "$SCORER_PATH"
    --log_dir "$log_dir"
  )
}

collector_command() {
  local arm="$1"
  local seed="$2"
  local checkpoint="$3"
  local output_dir="$4"
  COLLECTOR_COMMAND=(
    "$PYTHON_BIN" "$COLLECTOR_SCRIPT"
    --checkpoint "$checkpoint"
    --output_dir "$output_dir"
    --config ha_ctse_process.config
    --scenario energy
    --preset S7-S1
    --seed "$seed"
    --n_agents 6
    --device cuda
    --skill_interval "$SKILL_INTERVAL"
    --n_resets 64
    --episode_max_steps 500
    --checkpoint_id "r28_g1_${arm}_seed${seed}_final"
    --checkpoint_update "$FINAL_UPDATE"
    --r28_sidecar
  )
}

r26_analysis_command() {
  local input_dir="$1"
  local output_dir="$2"
  R26_COMMAND=(
    "$PYTHON_BIN" "$R26_ANALYZER"
    --input_dir "$input_dir"
    --output_dir "$output_dir"
    --num_skills 4
    --device cuda
  )
}

family_analysis_command() {
  FAMILY_COMMAND=(
    "$PYTHON_BIN" "$FAMILY_ANALYZER"
    --run_root "$RUN_ROOT"
    --scorer_path "$SCORER_PATH"
    --output_dir "$RUN_ROOT/family_analysis"
    --device cuda
  )
}

print_header() {
  cat <<EOF
R28-G1 causal skill-forcing cloud runner
  mode:                    $MODE
  repository:              $REPO_DIR
  data_root:               $DATA_ROOT
  run_root:                $RUN_ROOT
  source_checkpoint:       $SOURCE_CHECKPOINT
  frozen_g0_scorer:        $SCORER_PATH
  device:                  cuda (no CPU fallback)
  arms:                    probe_only, sham_reward, real_reward
  paired_seeds:            28031, 28032, 28033
  topology_workers:        3 concurrent arms, one update each
  training_workers:        3 concurrent arms per seed batch
  source/final_steps:      1000000 -> 1160000 (20 updates)
  vector_envs/rollout:     16 / 500
  evaluation:              +80k and +160k, 20 episodes
  evidence:                64 matched resets per arm/seed; unchanged R26 analysis
  registered_wall_clock:   6-10h after topology validation
  occupied_gpu_override:   $ALLOW_OCCUPIED_GPU
EOF
}

require_topology_authorization() {
  if [[ "$R28_G1_TOPOLOGY_AUTHORIZATION" != "$TOPOLOGY_AUTHORIZATION_TOKEN" ]]; then
    echo "Topology execution requires R28_G1_TOPOLOGY_AUTHORIZATION=$TOPOLOGY_AUTHORIZATION_TOKEN" >&2
    return 2
  fi
}

require_launch_authorization() {
  if [[ "$R28_G1_LAUNCH_AUTHORIZATION" != "$LAUNCH_AUTHORIZATION_TOKEN" ]]; then
    echo "Experiment execution requires R28_G1_LAUNCH_AUTHORIZATION=$LAUNCH_AUTHORIZATION_TOKEN" >&2
    return 2
  fi
}

print_all_commands() {
  local arm seed log_dir checkpoint evidence_root windows_dir analysis_dir
  echo
  echo "PHASE topology (three commands start concurrently)"
  for arm in "${ARMS[@]}"; do
    log_dir="$TOPOLOGY_ROOT/runs/$arm"
    train_command "$arm" "$TOPOLOGY_SEED" "$TOPOLOGY_TOTAL_TIMESTEPS" 0 "$log_dir"
    format_command "${TRAIN_COMMAND[@]}"
  done
  echo
  echo "PHASE run (three arm commands start concurrently within each seed batch)"
  for seed in "${SEEDS[@]}"; do
    for arm in "${ARMS[@]}"; do
      log_dir="$RUN_ROOT/runs/$arm/seed${seed}"
      train_command "$arm" "$seed" "$FINAL_TOTAL_TIMESTEPS" "$EVAL_INTERVAL" "$log_dir"
      format_command "${TRAIN_COMMAND[@]}"
    done
  done
  echo
  echo "PHASE evidence (three arm workers start concurrently within each seed batch)"
  for seed in "${SEEDS[@]}"; do
    for arm in "${ARMS[@]}"; do
      checkpoint="$RUN_ROOT/runs/$arm/seed${seed}/standalone_process_core_final.pt"
      evidence_root="$RUN_ROOT/evidence/$arm/seed${seed}"
      windows_dir="$evidence_root/r26_windows"
      analysis_dir="$evidence_root/r26_analysis"
      collector_command "$arm" "$seed" "$checkpoint" "$windows_dir"
      r26_analysis_command "$windows_dir" "$analysis_dir"
      format_command "${COLLECTOR_COMMAND[@]}"
      format_command "${R26_COMMAND[@]}"
    done
  done
  echo
  echo "PHASE analyze"
  family_analysis_command
  format_command "${FAMILY_COMMAND[@]}"
  echo
  echo "No files, processes, topology checks, or experiments were started."
  echo "Use this screen-safe command only after explicit topology/experiment authorization."
  echo "A fresh RUN_ROOT stops after topology; review the marker and invoke it again to train:"
  local screen_inner
  printf -v screen_inner 'cd %q && RUN_ROOT=%q SOURCE_CHECKPOINT=%q SCORER_PATH=%q R28_G1_TOPOLOGY_AUTHORIZATION=%q R28_G1_LAUNCH_AUTHORIZATION=%q bash scripts/run_r28_g1_causal_skill_forcing_cloud.sh all' \
    "$REPO_DIR" "$RUN_ROOT" "$SOURCE_CHECKPOINT" "$SCORER_PATH" \
    "$TOPOLOGY_AUTHORIZATION_TOKEN" "$LAUNCH_AUTHORIZATION_TOKEN"
  format_command screen -S r28_g1 -dm bash -lc "$screen_inner"
}

preflight_files_and_cuda() {
  local required
  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1 && [[ ! -x "$PYTHON_BIN" ]]; then
    echo "Python executable not found: $PYTHON_BIN" >&2
    return 2
  fi
  for required in "$TRAIN_SCRIPT" "$COLLECTOR_SCRIPT" "$R26_ANALYZER" "$FAMILY_ANALYZER"; do
    if [[ ! -s "$required" ]]; then
      echo "Required implementation file is missing or empty: $required" >&2
      return 2
    fi
  done
  for required in "$SOURCE_CHECKPOINT" "$SCORER_PATH"; do
    if [[ ! -s "$required" ]]; then
      echo "Required frozen input is missing or empty: $required" >&2
      return 2
    fi
  done
  if ! "$PYTHON_BIN" -c \
    'import torch; raise SystemExit(0 if torch.cuda.is_available() else "CUDA unavailable; R28-G1 forbids CPU fallback")'; then
    echo "CUDA preflight failed; no R28-G1 work was started." >&2
    return 2
  fi
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "nvidia-smi is required for the R28-G1 occupancy and topology checks." >&2
    return 2
  fi
  local compute_pids
  compute_pids="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null | sed '/^[[:space:]]*$/d' || true)"
  if [[ -n "$compute_pids" && "$ALLOW_OCCUPIED_GPU" != "1" ]]; then
    echo "GPU compute processes are already active; refusing to stack R28-G1 work:" >&2
    printf '%s\n' "$compute_pids" >&2
    echo "Wait for them to finish, or set ALLOW_OCCUPIED_GPU=1 only after an explicit sharing decision." >&2
    return 2
  fi
}

topology_marker_valid() {
  [[ -s "$TOPOLOGY_MARKER" ]] || return 1
  "$PYTHON_BIN" -c '
import json, sys
path, source, scorer = sys.argv[1:4]
with open(path, "r", encoding="utf-8") as handle:
    row = json.load(handle)
expected = {
    "status": "PASS",
    "device": "cuda",
    "source_checkpoint": source,
    "scorer_path": scorer,
    "arms": ["probe_only", "sham_reward", "real_reward"],
    "concurrent_workers": 3,
    "num_envs_per_worker": 16,
    "rollout_length": 500,
    "topology_total_timesteps": 1008000,
}
raise SystemExit(0 if all(row.get(key) == value for key, value in expected.items()) else 1)
' "$TOPOLOGY_MARKER" "$SOURCE_CHECKPOINT" "$SCORER_PATH"
}

require_topology_marker() {
  if ! topology_marker_valid; then
    echo "A matching PASS topology marker is required: $TOPOLOGY_MARKER" >&2
    echo "Run the separately authorized topology mode first; serial fallback is disabled." >&2
    return 2
  fi
}

run_logged_training() {
  local arm="$1"
  local seed="$2"
  local total_timesteps="$3"
  local eval_interval="$4"
  local log_dir="$5"
  local phase="$6"
  local status_path="$log_dir/runner_status.txt"
  local final_checkpoint="$log_dir/standalone_process_core_final.pt"
  mkdir -p "$log_dir"
  train_command "$arm" "$seed" "$total_timesteps" "$eval_interval" "$log_dir"
  format_command "${TRAIN_COMMAND[@]}" > "$log_dir/command.txt"
  write_status "$status_path" \
    "started=$(date -Is)" \
    "state=running" \
    "phase=$phase" \
    "arm=$arm" \
    "seed=$seed" \
    "device=cuda" \
    "num_envs=$NUM_ENVS" \
    "rollout_length=$ROLLOUT_LENGTH" \
    "total_timesteps=$total_timesteps"

  local command_pid=""
  local exit_code=0
  cleanup_command() {
    if [[ -n "$command_pid" ]] && kill -0 "$command_pid" 2>/dev/null; then
      kill -TERM "$command_pid" 2>/dev/null || true
      wait "$command_pid" 2>/dev/null || true
    fi
  }
  trap cleanup_command INT TERM EXIT
  "${TRAIN_COMMAND[@]}" > "$log_dir/runner_output.log" 2>&1 &
  command_pid="$!"
  if wait "$command_pid"; then
    exit_code=0
  else
    exit_code=$?
  fi
  command_pid=""
  trap - INT TERM EXIT

  if (( exit_code == 0 )) && [[ -s "$final_checkpoint" ]]; then
    write_status "$status_path" \
      "finished=$(date -Is)" \
      "state=succeeded" \
      "phase=$phase" \
      "arm=$arm" \
      "seed=$seed" \
      "device=cuda" \
      "total_timesteps=$total_timesteps" \
      "final_checkpoint=$final_checkpoint" \
      "exit_code=0"
    return 0
  fi
  local reason=command_failed
  if (( exit_code == 0 )); then
    reason=missing_final_checkpoint
    exit_code=3
  fi
  write_status "$status_path" \
    "finished=$(date -Is)" \
    "state=failed" \
    "phase=$phase" \
    "arm=$arm" \
    "seed=$seed" \
    "reason=$reason" \
    "exit_code=$exit_code"
  return "$exit_code"
}

completed_training_count() {
  local base_dir="$1"
  local arm count=0
  for arm in "${ARMS[@]}"; do
    if status_succeeded "$base_dir/$arm/runner_status.txt" && \
       [[ -s "$base_dir/$arm/standalone_process_core_final.pt" ]]; then
      count=$((count + 1))
    fi
  done
  printf '%d\n' "$count"
}

training_batch_has_outputs() {
  local base_dir="$1"
  local arm
  for arm in "${ARMS[@]}"; do
    if [[ -e "$base_dir/$arm" ]]; then
      return 0
    fi
  done
  return 1
}

run_three_training_workers() {
  local seed="$1"
  local total_timesteps="$2"
  local eval_interval="$3"
  local base_dir="$4"
  local phase="$5"
  local completed
  completed="$(completed_training_count "$base_dir")"
  if (( completed == 3 )); then
    echo "SKIP $phase seed=$seed: all three arm workers already succeeded."
    return 0
  fi
  if (( completed != 0 )) || training_batch_has_outputs "$base_dir"; then
    echo "$phase seed=$seed has a partial arm batch ($completed/3 succeeded)." >&2
    echo "Refusing a one- or two-worker serial fallback; use an operational repair or a new RUN_ROOT." >&2
    return 2
  fi

  local arm batch_failed=0 pid
  ACTIVE_PIDS=()
  for arm in "${ARMS[@]}"; do
    echo "START $phase arm=$arm seed=$seed"
    run_logged_training "$arm" "$seed" "$total_timesteps" "$eval_interval" \
      "$base_dir/$arm" "$phase" &
    ACTIVE_PIDS+=("$!")
  done
  if (( ${#ACTIVE_PIDS[@]} != 3 )); then
    echo "Internal error: R28-G1 requires exactly three concurrent arm workers." >&2
    cleanup_active_children
    return 2
  fi
  for pid in "${ACTIVE_PIDS[@]}"; do
    if ! wait "$pid"; then
      batch_failed=$((batch_failed + 1))
    fi
  done
  ACTIVE_PIDS=()
  if (( batch_failed > 0 )); then
    echo "$phase seed=$seed failed in $batch_failed/3 arm workers; no serial retry was attempted." >&2
    return 1
  fi
}

write_topology_marker() {
  local elapsed_seconds="$1"
  local projected_training_hours="$2"
  local estimate_low="$3"
  local estimate_high="$4"
  "$PYTHON_BIN" -c '
import json, os, sys
path, source, scorer, elapsed, projected, low, high = sys.argv[1:8]
row = {
    "status": "PASS",
    "measured_at": __import__("datetime").datetime.now().astimezone().isoformat(),
    "device": "cuda",
    "source_checkpoint": source,
    "scorer_path": scorer,
    "arms": ["probe_only", "sham_reward", "real_reward"],
    "concurrent_workers": 3,
    "num_envs_per_worker": 16,
    "rollout_length": 500,
    "topology_total_timesteps": 1008000,
    "measured_batch_seconds": int(elapsed),
    "projected_training_hours": float(projected),
    "revised_end_to_end_hours": [float(low), float(high)],
    "serial_fallback": False,
}
temporary = path + ".tmp"
with open(temporary, "w", encoding="utf-8") as handle:
    json.dump(row, handle, indent=2, sort_keys=True)
    handle.write("\n")
os.replace(temporary, path)
' "$TOPOLOGY_MARKER" "$SOURCE_CHECKPOINT" "$SCORER_PATH" \
    "$elapsed_seconds" "$projected_training_hours" "$estimate_low" "$estimate_high"
}

run_topology() {
  if topology_marker_valid; then
    echo "SKIP topology: matching PASS marker already exists at $TOPOLOGY_MARKER"
    return 0
  fi
  preflight_files_and_cuda
  mkdir -p "$TOPOLOGY_ROOT"
  write_status "$TOPOLOGY_ROOT/runner_status.txt" \
    "started=$(date -Is)" \
    "state=running" \
    "phase=topology" \
    "concurrent_workers=3" \
    "device=cuda"
  nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total \
    --format=csv > "$TOPOLOGY_ROOT/gpu_before.csv" 2>&1 || true
  local started finished elapsed completed
  completed="$(completed_training_count "$TOPOLOGY_ROOT/runs")"
  if (( completed != 0 )); then
    write_status "$TOPOLOGY_ROOT/runner_status.txt" \
      "finished=$(date -Is)" \
      "state=failed" \
      "phase=topology" \
      "reason=partial_topology_batch" \
      "completed_workers=$completed"
    echo "Partial topology outputs exist ($completed/3); refusing serial completion." >&2
    return 2
  fi
  started="$(date +%s)"
  if ! run_three_training_workers "$TOPOLOGY_SEED" "$TOPOLOGY_TOTAL_TIMESTEPS" 0 \
      "$TOPOLOGY_ROOT/runs" topology; then
    write_status "$TOPOLOGY_ROOT/runner_status.txt" \
      "finished=$(date -Is)" \
      "state=failed" \
      "phase=topology" \
      "reason=concurrent_worker_failure" \
      "concurrent_workers=3"
    return 1
  fi
  finished="$(date +%s)"
  elapsed=$((finished - started))
  (( elapsed > 0 )) || elapsed=1
  nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total \
    --format=csv > "$TOPOLOGY_ROOT/gpu_after.csv" 2>&1 || true

  local estimates projected_training_hours estimate_low estimate_high
  estimates="$("$PYTHON_BIN" -c '
import sys
elapsed = float(sys.argv[1])
projected = elapsed * 20.0 * 3.0 / 3600.0
low = max(6.0, projected + 1.0)
high = max(10.0, projected + 3.0)
print(f"{projected:.2f} {low:.2f} {high:.2f}")
' "$elapsed")"
  read -r projected_training_hours estimate_low estimate_high <<< "$estimates"
  write_topology_marker "$elapsed" "$projected_training_hours" "$estimate_low" "$estimate_high"
  write_status "$TOPOLOGY_ROOT/runner_status.txt" \
    "finished=$(date -Is)" \
    "state=succeeded" \
    "phase=topology" \
    "concurrent_workers=3" \
    "measured_batch_seconds=$elapsed" \
    "projected_training_hours=$projected_training_hours" \
    "revised_end_to_end_hours=${estimate_low}-${estimate_high}" \
    "topology_marker=$TOPOLOGY_MARKER" \
    "device=cuda"
  echo "Topology PASS: three concurrent CUDA arm workers completed in ${elapsed}s."
  echo "Measured projection: training ${projected_training_hours}h; revised end-to-end ${estimate_low}-${estimate_high}h."
}

training_arm_dir() {
  local arm="$1"
  local seed="$2"
  printf '%s/runs/%s/seed%s\n' "$RUN_ROOT" "$arm" "$seed"
}

completed_family_seed_count() {
  local seed="$1"
  local arm count=0 dir
  for arm in "${ARMS[@]}"; do
    dir="$(training_arm_dir "$arm" "$seed")"
    if status_succeeded "$dir/runner_status.txt" && \
       [[ -s "$dir/standalone_process_core_final.pt" ]]; then
      count=$((count + 1))
    fi
  done
  printf '%d\n' "$count"
}

family_seed_has_outputs() {
  local seed="$1"
  local arm
  for arm in "${ARMS[@]}"; do
    if [[ -e "$(training_arm_dir "$arm" "$seed")" ]]; then
      return 0
    fi
  done
  return 1
}

run_family_seed() {
  local seed="$1"
  local completed arm batch_failed=0 pid dir
  completed="$(completed_family_seed_count "$seed")"
  if (( completed == 3 )); then
    echo "SKIP run seed=$seed: all three arms already succeeded."
    return 0
  fi
  if (( completed != 0 )) || family_seed_has_outputs "$seed"; then
    echo "run seed=$seed has a partial arm batch ($completed/3 succeeded)." >&2
    echo "Refusing a serial fallback; use an operational repair or a new RUN_ROOT." >&2
    return 2
  fi
  ACTIVE_PIDS=()
  for arm in "${ARMS[@]}"; do
    dir="$(training_arm_dir "$arm" "$seed")"
    echo "START run arm=$arm seed=$seed"
    run_logged_training "$arm" "$seed" "$FINAL_TOTAL_TIMESTEPS" "$EVAL_INTERVAL" \
      "$dir" run &
    ACTIVE_PIDS+=("$!")
  done
  if (( ${#ACTIVE_PIDS[@]} != 3 )); then
    cleanup_active_children
    return 2
  fi
  for pid in "${ACTIVE_PIDS[@]}"; do
    if ! wait "$pid"; then
      batch_failed=$((batch_failed + 1))
    fi
  done
  ACTIVE_PIDS=()
  if (( batch_failed > 0 )); then
    echo "run seed=$seed failed in $batch_failed/3 arms; no serial retry was attempted." >&2
    return 1
  fi
}

run_registered_training() {
  require_topology_marker
  preflight_files_and_cuda
  mkdir -p "$RUN_ROOT/runs"
  write_status "$RUN_ROOT/run_status.txt" \
    "started=$(date -Is)" \
    "state=running" \
    "phase=run" \
    "seeds=28031,28032,28033" \
    "concurrent_arms=3" \
    "total_timesteps=$FINAL_TOTAL_TIMESTEPS"
  local seed
  for seed in "${SEEDS[@]}"; do
    if ! run_family_seed "$seed"; then
      write_status "$RUN_ROOT/run_status.txt" \
        "finished=$(date -Is)" \
        "state=failed" \
        "phase=run" \
        "failed_seed=$seed" \
        "serial_fallback=false"
      return 1
    fi
  done
  write_status "$RUN_ROOT/run_status.txt" \
    "finished=$(date -Is)" \
    "state=succeeded" \
    "phase=run" \
    "completed_runs=9" \
    "concurrent_arms=3" \
    "total_timesteps=$FINAL_TOTAL_TIMESTEPS"
}

run_evidence_one() {
  local arm="$1"
  local seed="$2"
  local training_dir checkpoint evidence_root windows_dir analysis_dir status_path
  training_dir="$(training_arm_dir "$arm" "$seed")"
  checkpoint="$training_dir/standalone_process_core_final.pt"
  evidence_root="$RUN_ROOT/evidence/$arm/seed${seed}"
  windows_dir="$evidence_root/r26_windows"
  analysis_dir="$evidence_root/r26_analysis"
  status_path="$evidence_root/runner_status.txt"
  if [[ ! -s "$checkpoint" ]]; then
    echo "Missing final checkpoint for evidence: $checkpoint" >&2
    return 2
  fi
  mkdir -p "$evidence_root"
  collector_command "$arm" "$seed" "$checkpoint" "$windows_dir"
  r26_analysis_command "$windows_dir" "$analysis_dir"
  format_command "${COLLECTOR_COMMAND[@]}" > "$evidence_root/collector_command.txt"
  format_command "${R26_COMMAND[@]}" > "$evidence_root/r26_analysis_command.txt"
  write_status "$status_path" \
    "started=$(date -Is)" \
    "state=running" \
    "phase=evidence" \
    "arm=$arm" \
    "seed=$seed" \
    "n_resets=64" \
    "r28_sidecar=true"

  local command_pid="" exit_code=0
  cleanup_evidence_command() {
    if [[ -n "$command_pid" ]] && kill -0 "$command_pid" 2>/dev/null; then
      kill -TERM "$command_pid" 2>/dev/null || true
      wait "$command_pid" 2>/dev/null || true
    fi
  }
  trap cleanup_evidence_command INT TERM EXIT
  "${COLLECTOR_COMMAND[@]}" > "$evidence_root/collector_output.log" 2>&1 &
  command_pid="$!"
  if wait "$command_pid"; then exit_code=0; else exit_code=$?; fi
  command_pid=""
  if (( exit_code != 0 )) || [[ ! -s "$windows_dir/collector_manifest.json" ]]; then
    (( exit_code != 0 )) || exit_code=3
    trap - INT TERM EXIT
    write_status "$status_path" \
      "finished=$(date -Is)" "state=failed" "phase=evidence" \
      "arm=$arm" "seed=$seed" "reason=collector_failed" "exit_code=$exit_code"
    return "$exit_code"
  fi

  "${R26_COMMAND[@]}" > "$evidence_root/r26_analysis_output.log" 2>&1 &
  command_pid="$!"
  if wait "$command_pid"; then exit_code=0; else exit_code=$?; fi
  command_pid=""
  trap - INT TERM EXIT
  local r26_command_exit="$exit_code" r26_gate_status=""
  if [[ -s "$analysis_dir/r26_g1_behavior.json" ]]; then
    r26_gate_status="$("$PYTHON_BIN" -c '
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    row = json.load(handle)
gate = row.get("gate")
print(gate.get("status", "") if isinstance(gate, dict) else "")
' "$analysis_dir/r26_g1_behavior.json" 2>/dev/null || true)"
  fi
  if [[ ! -s "$analysis_dir/r26_g1_behavior.json" ]] || \
     { (( r26_command_exit != 0 )) && [[ "$r26_gate_status" != "INVALID" ]]; }; then
    exit_code="$r26_command_exit"
    (( exit_code != 0 )) || exit_code=3
    write_status "$status_path" \
      "finished=$(date -Is)" "state=failed" "phase=evidence" \
      "arm=$arm" "seed=$seed" "reason=r26_analysis_failed" "exit_code=$exit_code"
    return "$exit_code"
  fi
  write_status "$status_path" \
    "finished=$(date -Is)" \
    "state=succeeded" \
    "phase=evidence" \
    "arm=$arm" \
    "seed=$seed" \
    "n_resets=64" \
    "r28_sidecar=true" \
    "r26_thresholds=unchanged" \
    "r26_gate_status=$r26_gate_status" \
    "r26_command_exit=$r26_command_exit" \
    "exit_code=0"
}

completed_evidence_seed_count() {
  local seed="$1"
  local arm count=0 path
  for arm in "${ARMS[@]}"; do
    path="$RUN_ROOT/evidence/$arm/seed${seed}"
    if status_succeeded "$path/runner_status.txt" && \
       [[ -s "$path/r26_analysis/r26_g1_behavior.json" ]]; then
      count=$((count + 1))
    fi
  done
  printf '%d\n' "$count"
}

evidence_seed_has_outputs() {
  local seed="$1"
  local arm
  for arm in "${ARMS[@]}"; do
    if [[ -e "$RUN_ROOT/evidence/$arm/seed${seed}" ]]; then
      return 0
    fi
  done
  return 1
}

run_evidence_seed() {
  local seed="$1"
  local completed arm batch_failed=0 pid
  completed="$(completed_evidence_seed_count "$seed")"
  if (( completed == 3 )); then
    echo "SKIP evidence seed=$seed: all three arms already succeeded."
    return 0
  fi
  if (( completed != 0 )) || evidence_seed_has_outputs "$seed"; then
    echo "evidence seed=$seed has a partial arm batch ($completed/3 succeeded)." >&2
    echo "Refusing a serial fallback; use an operational repair or a new RUN_ROOT." >&2
    return 2
  fi
  ACTIVE_PIDS=()
  for arm in "${ARMS[@]}"; do
    echo "START evidence arm=$arm seed=$seed"
    run_evidence_one "$arm" "$seed" &
    ACTIVE_PIDS+=("$!")
  done
  if (( ${#ACTIVE_PIDS[@]} != 3 )); then
    cleanup_active_children
    return 2
  fi
  for pid in "${ACTIVE_PIDS[@]}"; do
    if ! wait "$pid"; then
      batch_failed=$((batch_failed + 1))
    fi
  done
  ACTIVE_PIDS=()
  if (( batch_failed > 0 )); then
    echo "evidence seed=$seed failed in $batch_failed/3 arms; no serial retry was attempted." >&2
    return 1
  fi
}

run_registered_evidence() {
  require_topology_marker
  preflight_files_and_cuda
  local seed arm
  for seed in "${SEEDS[@]}"; do
    for arm in "${ARMS[@]}"; do
      if [[ ! -s "$(training_arm_dir "$arm" "$seed")/standalone_process_core_final.pt" ]]; then
        echo "Evidence requires all nine completed training checkpoints." >&2
        return 2
      fi
    done
  done
  mkdir -p "$RUN_ROOT/evidence"
  write_status "$RUN_ROOT/evidence_status.txt" \
    "started=$(date -Is)" "state=running" "phase=evidence" \
    "seeds=28031,28032,28033" "concurrent_arms=3" "n_resets_per_run=64"
  for seed in "${SEEDS[@]}"; do
    if ! run_evidence_seed "$seed"; then
      write_status "$RUN_ROOT/evidence_status.txt" \
        "finished=$(date -Is)" "state=failed" "phase=evidence" \
        "failed_seed=$seed" "serial_fallback=false"
      return 1
    fi
  done
  write_status "$RUN_ROOT/evidence_status.txt" \
    "finished=$(date -Is)" "state=succeeded" "phase=evidence" \
    "completed_runs=9" "concurrent_arms=3" "n_resets_per_run=64"
}

run_family_analysis() {
  require_topology_marker
  preflight_files_and_cuda
  local seed arm evidence_root
  for seed in "${SEEDS[@]}"; do
    for arm in "${ARMS[@]}"; do
      evidence_root="$RUN_ROOT/evidence/$arm/seed${seed}"
      if ! status_succeeded "$evidence_root/runner_status.txt"; then
        echo "Family analysis requires complete evidence: $evidence_root" >&2
        return 2
      fi
    done
  done
  local output_dir="$RUN_ROOT/family_analysis"
  local status_path="$output_dir/runner_status.txt"
  mkdir -p "$output_dir"
  family_analysis_command
  format_command "${FAMILY_COMMAND[@]}" > "$output_dir/command.txt"
  write_status "$status_path" \
    "started=$(date -Is)" "state=running" "phase=analyze" \
    "device=cuda" "bootstrap_reps=10000"
  local exit_code=0
  if "${FAMILY_COMMAND[@]}" > "$output_dir/runner_output.log" 2>&1; then
    exit_code=0
  else
    exit_code=$?
  fi
  if (( exit_code == 0 )) && [[ -s "$output_dir/r28_g1_family.json" ]] && \
     [[ -s "$output_dir/r28_g1_family.md" ]]; then
    write_status "$status_path" \
      "finished=$(date -Is)" "state=succeeded" "phase=analyze" \
      "result_json=$output_dir/r28_g1_family.json" "exit_code=0"
    return 0
  fi
  (( exit_code != 0 )) || exit_code=3
  write_status "$status_path" \
    "finished=$(date -Is)" "state=failed" "phase=analyze" \
    "reason=family_analysis_failed" "exit_code=$exit_code"
  return "$exit_code"
}

run_all() {
  local topology_marker_existed=0
  if topology_marker_valid; then
    topology_marker_existed=1
  fi
  mkdir -p "$RUN_ROOT"
  write_status "$RUN_ROOT/runner_status.txt" \
    "started=$(date -Is)" "state=running" "mode=all" \
    "device=cuda" "registered_wall_clock_hours=6-10"
  if ! run_topology; then
    write_status "$RUN_ROOT/runner_status.txt" \
      "finished=$(date -Is)" "state=failed" "mode=all" \
      "serial_fallback=false"
    return 1
  fi
  if (( topology_marker_existed == 0 )); then
    write_status "$RUN_ROOT/runner_status.txt" \
      "finished=$(date -Is)" "state=waiting_for_launch_reinvoke" "mode=all" \
      "phase=topology_complete" "topology_marker=$TOPOLOGY_MARKER" \
      "serial_fallback=false"
    echo "Stopped after newly validated topology. Review $TOPOLOGY_MARKER."
    echo "Repeat the same authorized invocation to start the registered experiment."
    return 0
  fi
  if ! run_registered_training || ! run_registered_evidence || ! run_family_analysis; then
    write_status "$RUN_ROOT/runner_status.txt" \
      "finished=$(date -Is)" "state=failed" "mode=all" \
      "serial_fallback=false"
    return 1
  fi
  write_status "$RUN_ROOT/runner_status.txt" \
    "finished=$(date -Is)" "state=succeeded" "mode=all" \
    "result_json=$RUN_ROOT/family_analysis/r28_g1_family.json" \
    "serial_fallback=false"
}

print_header
case "$MODE" in
  commands) print_all_commands ;;
  topology)
    require_topology_authorization
    install_signal_traps
    run_topology
    ;;
  run)
    require_launch_authorization
    install_signal_traps
    run_registered_training
    ;;
  evidence)
    require_launch_authorization
    install_signal_traps
    run_registered_evidence
    ;;
  analyze)
    require_launch_authorization
    install_signal_traps
    run_family_analysis
    ;;
  all)
    require_topology_authorization
    require_launch_authorization
    install_signal_traps
    run_all
    ;;
esac

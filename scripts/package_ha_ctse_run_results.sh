#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG_ROOT=""
OUTPUT=""
INCLUDE_CHECKPOINTS=0
INCLUDE_PLOTS=0
MAX_DEPTH=6

usage() {
  cat <<'EOF'
Package HA-CTSE remote run results for download.

Default package contents are the minimum set needed for trustworthy analysis:
  - metadata/run_manifest.json
  - metrics/*.csv and metrics/*.json
  - standalone_train.log
  - runner_status.txt
  - runner_output.log
  - command.txt
  - top-level *.json files under each run directory

Checkpoints and plots are excluded by default to keep packages small.

Usage:
  bash scripts/package_ha_ctse_run_results.sh --root logs_cloud_r19_team_transition_64env
  bash scripts/package_ha_ctse_run_results.sh --root logs_cloud_r19_team_transition_64env --output dist/r19_results.tar.gz
  bash scripts/package_ha_ctse_run_results.sh --root logs_cloud_r19_team_transition_64env --include-checkpoints
  bash scripts/package_ha_ctse_run_results.sh --root logs_cloud_r19_team_transition_64env --include-plots

Options:
  --root PATH              Log root or a single run directory to package.
  --output PATH            Output .tar.gz path. Default: dist/<root>_results_<timestamp>.tar.gz
  --include-checkpoints    Include standalone_process_core_update_*.pt files.
  --include-plots          Include plots/*.png, plots/*.pdf, and paper_data files.
  --max-depth N            Max find depth from --root. Default: 6.
  -h, --help               Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      LOG_ROOT="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT="${2:-}"
      shift 2
      ;;
    --include-checkpoints)
      INCLUDE_CHECKPOINTS=1
      shift
      ;;
    --include-plots)
      INCLUDE_PLOTS=1
      shift
      ;;
    --max-depth)
      MAX_DEPTH="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$LOG_ROOT" ]]; then
  echo "Missing --root PATH" >&2
  usage >&2
  exit 2
fi

if [[ ! -e "$LOG_ROOT" ]]; then
  echo "Log root does not exist: $LOG_ROOT" >&2
  exit 2
fi

if ! [[ "$MAX_DEPTH" =~ ^[0-9]+$ ]]; then
  echo "--max-depth must be an integer: $MAX_DEPTH" >&2
  exit 2
fi

timestamp="$(date +%Y%m%d_%H%M%S)"
safe_root="$(echo "$LOG_ROOT" | sed 's#[/\\: ]#_#g' | sed 's#^_*##; s#_*$##')"
if [[ -z "$OUTPUT" ]]; then
  OUTPUT="dist/${safe_root}_results_${timestamp}.tar.gz"
fi
mkdir -p "$(dirname "$OUTPUT")"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
manifest="$tmp_dir/package_manifest.txt"

add_existing() {
  local rel="$1"
  [[ -f "$rel" ]] && printf '%s\n' "$rel" >> "$manifest"
}

find_files() {
  local pattern="$1"
  find "$LOG_ROOT" -maxdepth "$MAX_DEPTH" -type f -path "$pattern" -print >> "$manifest"
}

: > "$manifest"

# Per-run trust context.
find_files "*/metadata/run_manifest.json"
find_files "*/metrics/*.csv"
find_files "*/metrics/*.json"
find_files "*/standalone_train.log"
find_files "*/runner_status.txt"
find_files "*/runner_output.log"
find_files "*/command.txt"
find_files "*/*.json"

# If --root itself is a single run directory, also catch files at depth 1.
add_existing "$LOG_ROOT/metadata/run_manifest.json"
if [[ -d "$LOG_ROOT/metrics" ]]; then
  find "$LOG_ROOT/metrics" -maxdepth 1 -type f \( -name '*.csv' -o -name '*.json' \) -print >> "$manifest"
fi
add_existing "$LOG_ROOT/standalone_train.log"
add_existing "$LOG_ROOT/runner_status.txt"
add_existing "$LOG_ROOT/runner_output.log"
add_existing "$LOG_ROOT/command.txt"
if [[ -d "$LOG_ROOT" ]]; then
  find "$LOG_ROOT" -maxdepth 1 -type f -name '*.json' -print >> "$manifest"
fi

if [[ "$INCLUDE_CHECKPOINTS" == "1" ]]; then
  find_files "*/standalone_process_core_update_*.pt"
  find_files "*/best_model.pt"
  add_existing "$LOG_ROOT/best_model.pt"
  if [[ -d "$LOG_ROOT" ]]; then
    find "$LOG_ROOT" -maxdepth 1 -type f -name 'standalone_process_core_update_*.pt' -print >> "$manifest"
  fi
fi

if [[ "$INCLUDE_PLOTS" == "1" ]]; then
  find_files "*/plots/*.png"
  find_files "*/plots/*.pdf"
  find_files "*/paper_data/*"
  if [[ -d "$LOG_ROOT/plots" ]]; then
    find "$LOG_ROOT/plots" -maxdepth 1 -type f \( -name '*.png' -o -name '*.pdf' \) -print >> "$manifest"
  fi
  if [[ -d "$LOG_ROOT/paper_data" ]]; then
    find "$LOG_ROOT/paper_data" -maxdepth 1 -type f -print >> "$manifest"
  fi
fi

sort -u "$manifest" -o "$manifest"

file_count="$(wc -l < "$manifest" | tr -d ' ')"
if [[ "$file_count" == "0" ]]; then
  echo "No matching result files found under: $LOG_ROOT" >&2
  exit 1
fi

tar -czf "$OUTPUT" -T "$manifest"

echo "HA-CTSE result package created"
echo "  root:                $LOG_ROOT"
echo "  output:              $OUTPUT"
echo "  files:               $file_count"
echo "  include_checkpoints: $INCLUDE_CHECKPOINTS"
echo "  include_plots:       $INCLUDE_PLOTS"
echo
echo "Included file preview:"
head -n 30 "$manifest"
if [[ "$file_count" -gt 30 ]]; then
  echo "  ... ($((file_count - 30)) more)"
fi

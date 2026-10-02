#!/usr/bin/env bash
# ==============================================================================
# agent-task: Lightweight task supervisor for Remote AI Agents using tmux
# Solves: process keep-alive, exit-code retention, structured status, and log tailing
# ==============================================================================

set -euo pipefail

TASK_DIR="${HOME}/.agent-tasks"
mkdir -p "${TASK_DIR}"

usage() {
    cat <<EOF
Usage: agent-task <command> [arguments]

Commands:
  run <name> <cmd...>     Run a command in a persistent tmux session with log tracking
  status <name>           Get status, PID, and exit code in JSON format
  logs <name> [lines]     View the last N lines of output (default: 50)
  attach <name>           Interactively attach to the task tmux session
  stop <name>             Stop a running task
  list                    List all agent tasks and their status
EOF
    exit 1
}

[ $# -lt 1 ] && usage

CMD="$1"
shift

case "$CMD" in
    run)
        [ $# -lt 2 ] && { echo "Error: 'run' requires <name> and <command...>"; exit 1; }
        NAME="$1"
        shift
        COMMAND="$*"

        DIR="${TASK_DIR}/${NAME}"
        mkdir -p "${DIR}"

        LOG_FILE="${DIR}/task.log"
        STATUS_FILE="${DIR}/status"
        PID_FILE="${DIR}/pid"
        EXIT_FILE="${DIR}/exit_code"
        START_TIME_FILE="${DIR}/start_time"

        # Check if already running
        if tmux has-session -t "agent_${NAME}" 2>/dev/null; then
            echo "Error: Task '${NAME}' is already running in session 'agent_${NAME}'."
            exit 1
        fi

        rm -f "${EXIT_FILE}"
        echo "running" > "${STATUS_FILE}"
        date +%s > "${START_TIME_FILE}"

        # Wrapper script executed inside tmux
        WRAPPER="${DIR}/runner.sh"
        cat <<EOF > "${WRAPPER}"
#!/usr/bin/env bash
echo \$\$ > "${PID_FILE}"
START_TS=\$(date +%s)
echo "=== Task '${NAME}' started at \$(date -Iseconds) ===" >> "${LOG_FILE}"

# Execute command capturing output
set +e
eval ${COMMAND@Q} >> "${LOG_FILE}" 2>&1
EXIT_CODE=\$?
set -e

END_TS=\$(date +%s)
echo \$EXIT_CODE > "${EXIT_FILE}"
if [ \$EXIT_CODE -eq 0 ]; then
    echo "finished" > "${STATUS_FILE}"
else
    echo "failed" > "${STATUS_FILE}"
fi
echo "=== Task '${NAME}' exited with code \$EXIT_CODE at \$(date -Iseconds) (Duration: \$((END_TS - START_TS))s) ===" >> "${LOG_FILE}"

# Keep session alive briefly for inspection, then exit
sleep 1
EOF
        chmod +x "${WRAPPER}"

        # Spawn detached tmux session
        tmux new-session -d -s "agent_${NAME}" "bash '${WRAPPER}'"
        echo "Task '${NAME}' started in tmux session 'agent_${NAME}'. Output: ${LOG_FILE}"
        ;;

    status)
        [ $# -lt 1 ] && { echo "Error: 'status' requires <name>"; exit 1; }
        NAME="$1"
        DIR="${TASK_DIR}/${NAME}"
        [ ! -d "${DIR}" ] && { echo "{\"task\": \"${NAME}\", \"status\": \"not_found\"}"; exit 0; }

        STATUS="unknown"
        [ -f "${DIR}/status" ] && STATUS=$(cat "${DIR}/status")

        PID=null
        [ -f "${DIR}/pid" ] && PID=$(cat "${DIR}/pid")

        EXIT_CODE=null
        [ -f "${DIR}/exit_code" ] && EXIT_CODE=$(cat "${DIR}/exit_code")

        START_TIME=0
        [ -f "${DIR}/start_time" ] && START_TIME=$(cat "${DIR}/start_time")

        NOW=$(date +%s)
        UPTIME=0
        if [ "$START_TIME" -gt 0 ]; then
            UPTIME=$((NOW - START_TIME))
        fi

        # Check if tmux session still exists
        TMUX_ACTIVE=false
        if tmux has-session -t "agent_${NAME}" 2>/dev/null; then
            TMUX_ACTIVE=true
        else
            if [ "$STATUS" = "running" ]; then
                STATUS="terminated"
            fi
        fi

        printf '{"task": "%s", "status": "%s", "exit_code": %s, "pid": %s, "uptime_seconds": %d, "tmux_active": %s}\n' \
            "${NAME}" "${STATUS}" "${EXIT_CODE}" "${PID}" "${UPTIME}" "${TMUX_ACTIVE}"
        ;;

    logs)
        [ $# -lt 1 ] && { echo "Error: 'logs' requires <name>"; exit 1; }
        NAME="$1"
        LINES="${2:-50}"
        LOG_FILE="${TASK_DIR}/${NAME}/task.log"

        if [ ! -f "${LOG_FILE}" ]; then
            echo "No logs found for task '${NAME}'."
            exit 1
        fi
        tail -n "${LINES}" "${LOG_FILE}"
        ;;

    attach)
        [ $# -lt 1 ] && { echo "Error: 'attach' requires <name>"; exit 1; }
        NAME="$1"
        exec tmux attach-session -t "agent_${NAME}"
        ;;

    stop)
        [ $# -lt 1 ] && { echo "Error: 'stop' requires <name>"; exit 1; }
        NAME="$1"
        DIR="${TASK_DIR}/${NAME}"
        if [ -f "${DIR}/pid" ]; then
            PID=$(cat "${DIR}/pid")
            kill -15 "${PID}" 2>/dev/null || true
            sleep 0.5
            kill -9 "${PID}" 2>/dev/null || true
        fi
        tmux kill-session -t "agent_${NAME}" 2>/dev/null || true
        echo "stopped" > "${DIR}/status" 2>/dev/null || true
        echo "Task '${NAME}' stopped."
        ;;

    list)
        if [ ! -d "${TASK_DIR}" ] || [ -z "$(ls -A "${TASK_DIR}" 2>/dev/null)" ]; then
            echo "No agent tasks recorded."
            exit 0
        fi
        printf "%-20s %-12s %-10s %-10s\n" "TASK_NAME" "STATUS" "EXIT_CODE" "TMUX_ACTIVE"
        echo "---------------------------------------------------------"
        for d in "${TASK_DIR}"/*; do
            [ -d "$d" ] || continue
            tname=$(basename "$d")
            tstatus=$(cat "$d/status" 2>/dev/null || echo "unknown")
            texit=$(cat "$d/exit_code" 2>/dev/null || echo "-")
            tmux_act="no"
            tmux has-session -t "agent_${tname}" 2>/dev/null && tmux_act="yes"
            printf "%-20s %-12s %-10s %-10s\n" "$tname" "$tstatus" "$texit" "$tmux_act"
        done
        ;;

    *)
        usage
        ;;
esac

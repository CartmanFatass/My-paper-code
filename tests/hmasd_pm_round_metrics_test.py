import json
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / ".agents/skills/hmasd-pm-round-metrics/scripts/hmasd_pm_round_metrics.py"
)


def token_event(**usage):
    defaults = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "cache_write_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "total_tokens": 0,
    }
    defaults.update(usage)
    return {
        "type": "event_msg",
        "timestamp": "2026-07-26T12:00:00.000Z",
        "payload": {
            "type": "token_count",
            "info": {
                "total_token_usage": defaults,
                "last_token_usage": defaults,
            },
        },
    }


def context_event(model="gpt-5.6-sol", effort="high"):
    return {
        "type": "turn_context",
        "timestamp": "2026-07-26T12:00:00.000Z",
        "payload": {"model": model, "effort": effort},
    }


def append_jsonl(path, *items):
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        for item in items:
            handle.write(json.dumps(item) + "\n")


def make_state(path, thread_id, rollout, model="gpt-5.6-sol", effort="high"):
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE threads (id TEXT, model TEXT, reasoning_effort TEXT, rollout_path TEXT)"
    )
    connection.execute(
        "INSERT INTO threads VALUES (?, ?, ?, ?)",
        (thread_id, model, effort, str(rollout)),
    )
    connection.commit()
    connection.close()


def update_state(path, thread_id, *, model=None, effort=None):
    connection = sqlite3.connect(path)
    if model is not None:
        connection.execute("UPDATE threads SET model=? WHERE id=?", (model, thread_id))
    if effort is not None:
        connection.execute(
            "UPDATE threads SET reasoning_effort=? WHERE id=?", (effort, thread_id)
        )
    connection.commit()
    connection.close()


def run_cli(state, ledger, *args, expected=0):
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--state-db",
            str(state),
            "--ledger",
            str(ledger),
            *args,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    return json.loads(result.stdout)


def setup_round(tmp_path):
    thread_id = "pm-thread"
    state = tmp_path / "state.sqlite"
    ledger = tmp_path / "ledger.jsonl"
    rollout = tmp_path / "rollout.jsonl"
    append_jsonl(
        rollout,
        context_event(),
        token_event(
            input_tokens=1000,
            cached_input_tokens=500,
            output_tokens=100,
            reasoning_output_tokens=20,
            total_tokens=1100,
        ),
    )
    make_state(state, thread_id, rollout)
    started = run_cli(state, ledger, "start", "--thread-id", thread_id)
    return thread_id, state, ledger, rollout, started


def test_start_close_prices_cumulative_delta_and_ignores_duplicate_last(tmp_path):
    thread_id, state, ledger, rollout, started = setup_round(tmp_path)
    assert started["status"] == "ROUND_STARTED"
    duplicate = token_event(
        input_tokens=1000,
        cached_input_tokens=500,
        output_tokens=100,
        reasoning_output_tokens=20,
        total_tokens=1100,
    )
    append_jsonl(
        rollout,
        duplicate,
        token_event(
            input_tokens=3000,
            cached_input_tokens=1500,
            cache_write_input_tokens=100,
            output_tokens=300,
            reasoning_output_tokens=70,
            total_tokens=3300,
        ),
    )
    closed = run_cli(
        state,
        ledger,
        "close",
        "--thread-id",
        thread_id,
        "--contains-code-work",
        "true",
    )
    assert closed["status"] == "ROUND_CLOSED"
    assert closed["estimated_cost_usd"] == "0.011625000"
    events = [json.loads(line) for line in ledger.read_text().splitlines()]
    close = events[-1]
    assert close["token_usage"] == {
        "input_tokens": 2000,
        "cached_input_tokens": 1000,
        "cache_write_input_tokens": 100,
        "output_tokens": 200,
        "reasoning_output_tokens": 50,
        "total_tokens": 2200,
    }
    assert close["contains_code_work"] is True


def test_configuration_change_writes_no_valid_sample(tmp_path):
    thread_id, state, ledger, rollout, _ = setup_round(tmp_path)
    append_jsonl(rollout, context_event(model="gpt-5.6-terra", effort="high"))
    update_state(state, thread_id, model="gpt-5.6-terra")
    result = run_cli(
        state,
        ledger,
        "close",
        "--thread-id",
        thread_id,
        "--contains-code-work",
        "false",
        expected=2,
    )
    assert result["status"] == "CONFIGURATION_CHANGED"
    events = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert [event["event"] for event in events] == ["round_started"]


def test_quality_events_recompute_score_and_summary_by_model_effort(tmp_path):
    thread_id, state, ledger, rollout, started = setup_round(tmp_path)
    append_jsonl(
        rollout,
        token_event(
            input_tokens=2000,
            cached_input_tokens=1500,
            output_tokens=200,
            reasoning_output_tokens=50,
            total_tokens=2200,
        ),
    )
    run_cli(
        state,
        ledger,
        "close",
        "--thread-id",
        thread_id,
        "--contains-code-work",
        "true",
    )
    first = run_cli(
        state,
        ledger,
        "add-event",
        "--round-id",
        started["round_id"],
        "--event-type",
        "post_acceptance_defect",
        "--incident-id",
        "incident-1",
        "--evidence",
        "focused test failed after PM acceptance",
        "--code-related",
        "true",
    )
    second = run_cli(
        state,
        ledger,
        "add-event",
        "--round-id",
        started["round_id"],
        "--event-type",
        "downstream_rework",
        "--incident-id",
        "incident-1",
        "--evidence",
        "same incident required one repair",
        "--code-related",
        "true",
    )
    assert first["quality_score"] == 80
    assert second["quality_score"] == 70
    summary = run_cli(state, ledger, "summary")
    assert summary["groups"] == [
        {
            "model": "gpt-5.6-sol",
            "reasoning_effort": "high",
            "sample_count": 1,
            "median_quality_score": "70",
            "median_estimated_cost_usd": "0.003500000",
            "median_elapsed_seconds": summary["groups"][0]["median_elapsed_seconds"],
            "code_work_sample_count": 1,
            "quality_event_counts": {
                "post_acceptance_defect": 1,
                "downstream_rework": 1,
                "workflow_violation": 0,
                "pm_caused_clarification": 0,
            },
            "code_related_quality_event_counts": {
                "post_acceptance_defect": 1,
                "downstream_rework": 1,
                "workflow_violation": 0,
                "pm_caused_clarification": 0,
            },
        }
    ]


def test_active_round_and_unsupported_model_fail_closed(tmp_path):
    thread_id, state, ledger, _, _ = setup_round(tmp_path)
    duplicate = run_cli(
        state, ledger, "start", "--thread-id", thread_id, expected=2
    )
    assert duplicate["status"] == "ACTIVE_ROUND_EXISTS"

    other_state = tmp_path / "other.sqlite"
    other_rollout = tmp_path / "other.jsonl"
    append_jsonl(other_rollout, token_event())
    make_state(other_state, "other", other_rollout, model="unknown-model")
    unsupported = run_cli(
        other_state,
        tmp_path / "other-ledger.jsonl",
        "start",
        "--thread-id",
        "other",
        expected=2,
    )
    assert unsupported["status"] == "UNSUPPORTED_MODEL"


def test_local_ledger_parent_is_git_ignored():
    ignore_lines = {
        line.strip() for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    }
    assert "logs/" in ignore_lines

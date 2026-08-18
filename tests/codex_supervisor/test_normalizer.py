from tools.codex_supervisor.normalizer import normalize_message


def _event(message: dict, seq: int = 1):
    return normalize_message(message, seq, "run_1", "t")


def test_notification_method_mapping() -> None:
    expected = {
        "thread/started": "THREAD_STARTED_OBSERVED",
        "thread/archived": "THREAD_ARCHIVED_OBSERVED",
        "thread/unarchived": "THREAD_UNARCHIVED_OBSERVED",
        "thread/closed": "THREAD_CLOSED_OBSERVED",
        "turn/started": "TURN_STARTED_OBSERVED",
        "turn/completed": "TURN_COMPLETED_OBSERVED",
        "turn/diff/updated": "TURN_DIFF_UPDATED_OBSERVED",
        "turn/plan/updated": "TURN_PLAN_UPDATED_OBSERVED",
        "item/started": "ITEM_STARTED_OBSERVED",
        "item/completed": "ITEM_COMPLETED_OBSERVED",
        "thread/tokenUsage/updated": "TOKEN_USAGE_UPDATED_OBSERVED",
        "configWarning": "CONFIG_WARNING_OBSERVED",
        "warning": "SERVER_WARNING_OBSERVED",
    }
    for method, kind in expected.items():
        event = _event({"method": method, "params": {}})
        assert event is not None
        assert event.event_kind == kind


def test_item_delta_strips_text() -> None:
    event = _event(
        {
            "method": "item/agentMessage/delta",
            "params": {
                "threadId": "thr_1",
                "turnId": "turn_1",
                "itemId": "itm_1",
                "delta": "BLOCKED FAILED RETIRED Portfolio should stop",
            },
        }
    )
    assert event is not None
    assert event.event_kind == "ITEM_DELTA_OBSERVED"
    assert event.payload["delta_present"] is True
    assert event.payload["delta_bytes"] == len("BLOCKED FAILED RETIRED Portfolio should stop".encode("utf-8"))
    dumped = str(event.payload)
    assert "BLOCKED" not in dumped
    assert "Portfolio" not in dumped


def test_turn_completed_keeps_mechanical_status_only() -> None:
    event = _event(
        {
            "method": "turn/completed",
            "params": {
                "threadId": "thr_1",
                "turn": {"id": "turn_1", "status": "failed", "error": {"code": 7, "message": "secret"}},
            },
        }
    )
    assert event is not None
    assert event.event_kind == "TURN_COMPLETED_OBSERVED"
    assert event.mechanical_status == "failed"
    assert event.payload["error_present"] is True
    assert event.payload["error_code_present"] is True
    assert "secret" not in str(event.payload)


def test_unknown_notification_is_mechanical() -> None:
    event = _event({"method": "thread/deleted", "params": {"threadId": "thr_x"}})
    assert event is not None
    assert event.event_kind == "UNKNOWN_NOTIFICATION_OBSERVED"
    assert event.payload == {"method": "thread/deleted"}

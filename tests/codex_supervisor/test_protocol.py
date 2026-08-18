import json

import pytest

from tools.codex_supervisor.protocol import (
    ProtocolLineTooLarge,
    canonical_json,
    classify_rpc_message,
    decode_jsonl_line,
    encode_jsonl,
    extract_protocol_ids,
)
from tools.codex_supervisor.models import RpcShape


def test_client_request_and_server_shapes() -> None:
    request = {"id": 1, "method": "initialize", "params": {}}
    assert classify_rpc_message(request) is RpcShape.REQUEST
    assert classify_rpc_message({"id": 1, "result": {}}) is RpcShape.RESPONSE
    assert classify_rpc_message({"method": "turn/started", "params": {}}) is RpcShape.NOTIFICATION
    assert classify_rpc_message({"id": "s1", "method": "item/commandExecution/requestApproval", "params": {}}) is RpcShape.REQUEST
    assert classify_rpc_message({"id": 2, "error": {"code": -32001}}) is RpcShape.RESPONSE
    assert classify_rpc_message(["array"]) is RpcShape.INVALID
    assert classify_rpc_message("x") is RpcShape.INVALID


def test_encode_omits_jsonrpc() -> None:
    encoded = encode_jsonl({"id": 1, "method": "initialize", "jsonrpc": "2.0", "params": {}})
    assert b"jsonrpc" not in encoded
    assert encoded.endswith(b"\n")
    assert encoded == canonical_json({"id": 1, "method": "initialize", "params": {}}).encode("utf-8") + b"\n"


def test_decode_accepts_jsonrpc_for_diagnostics() -> None:
    line = json.dumps({"jsonrpc": "2.0", "method": "warning", "params": {}}).encode("utf-8") + b"\n"
    decoded = decode_jsonl_line(line, 1024)
    assert decoded["jsonrpc"] == "2.0"
    assert classify_rpc_message(decoded) is RpcShape.NOTIFICATION


def test_line_over_limit() -> None:
    with pytest.raises(ProtocolLineTooLarge):
        decode_jsonl_line(b"{" + b"a" * 20, 10)


def test_ids_from_known_paths_only() -> None:
    ids = extract_protocol_ids(
        {
            "method": "turn/completed",
            "params": {
                "threadId": "thr_1",
                "turn": {"id": "turn_2"},
                "item": {"id": "itm_3"},
                "prose": "threadId=thr_leak turnId=turn_leak",
            },
        }
    )
    assert ids.thread_id == "thr_1"
    assert ids.turn_id == "turn_2"
    assert ids.item_id == "itm_3"

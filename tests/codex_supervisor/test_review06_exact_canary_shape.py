import asyncio
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.codex_supervisor.canary_contract import (
    canonical_canary_thread_start_request,
    canonical_canary_turn_start_request,
    is_exact_json_value,
)
from tools.codex_supervisor.durability.effects import EffectError, EffectJournal
from tools.codex_supervisor.durability.session_owner import (
    AppServerSessionOwner,
    SessionOwnerError,
)
from tools.codex_supervisor.store import ObserverStore


CANARY_ID = "canary_0123456789abcdef0123456789abcdef"
THREAD_ID = "thr_exact_canary"


def test_type_strict_json_comparison_ignores_object_key_order_only() -> None:
    expected = {
        "enabled": True,
        "count": 1,
        "ratio": 1.5,
        "items": [{"type": "text", "text": "first"}, None],
    }
    reordered = {
        "items": [{"text": "first", "type": "text"}, None],
        "ratio": 1.5,
        "count": 1,
        "enabled": True,
    }
    reordered_list = deepcopy(reordered)
    reordered_list["items"] = [None, {"text": "first", "type": "text"}]

    assert is_exact_json_value(reordered, expected)
    assert not is_exact_json_value(reordered_list, expected)


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        (True, 1),
        (1, True),
        (1.0, 1),
        (1, 1.0),
        (False, 0),
        (("text",), ["text"]),
        ({1: "value"}, {"1": "value"}),
        (float("nan"), float("nan")),
        (float("inf"), float("inf")),
        (-0.0, 0.0),
    ],
)
def test_type_strict_json_comparison_rejects_coercions_and_non_json(
    actual: object, expected: object
) -> None:
    assert not is_exact_json_value(actual, expected)


@pytest.mark.parametrize("thread_id", [None, True, 1, 1.0, ""])
def test_canary_turn_builder_requires_native_nonempty_thread_id(
    thread_id: object,
) -> None:
    with pytest.raises(ValueError, match="thread id"):
        canonical_canary_turn_start_request(thread_id)  # type: ignore[arg-type]


class _NoSendClient:
    def __init__(self) -> None:
        self.server_requests = asyncio.Queue()
        self.discard_count = 0
        self.send_count = 0

    def prepare_request(self, method, params=None):
        request = dict(params or {})
        return SimpleNamespace(
            request_id="req-exact-canary",
            method=method,
            params=request,
            payload={"id": 1, "method": method, "params": request},
            request_class=SimpleNamespace(value="MUTATING_NO_RETRY"),
        )

    def discard_prepared(self, _prepared) -> None:
        self.discard_count += 1

    async def send_prepared(self, _prepared) -> None:
        self.send_count += 1
        raise AssertionError("malformed canary request crossed WRITE_STARTED")

    async def await_prepared(self, _prepared):  # pragma: no cover
        raise AssertionError("malformed canary request was sent")


def _start_run(store: ObserverStore) -> str:
    return store.start_run(
        codex_binary="codex",
        codex_version="test",
        client_name="exact-canary-test",
        process_id=None,
    )


def _seed_predecessor(
    store: ObserverStore, run_id: str, request: dict[str, object]
):
    journal = EffectJournal(store.connection)
    predecessor = journal.prepare_effect(
        owner_kind="EPHEMERAL_CANARY",
        owner_id=CANARY_ID,
        binding_id=None,
        method="thread/start",
        client_key=f"canary:thread/start:{CANARY_ID}",
        request=request,
    )
    journal.claim_write(
        predecessor.effect_id,
        run_id=run_id,
        client_request_id="req-thread",
        request_row_id="row-thread",
        raw_request_seq=1,
    )
    journal.observe_response(
        predecessor.effect_id,
        response={"result": {"thread": {"id": THREAD_ID, "ephemeral": True}}},
        thread_id=THREAD_ID,
    )
    return predecessor


def _assert_prewrite_rejected(
    store: ObserverStore,
    effect_id: str,
    client: _NoSendClient,
    original_request: dict[str, object],
) -> None:
    journal = EffectJournal(store.connection)
    effect = journal.get(effect_id)
    assert effect.state == "PREPARED"
    assert dict(effect.request) == original_request
    assert client.discard_count == 1
    assert client.send_count == 0
    assert store.connection.execute(
        "SELECT COUNT(*) FROM raw_messages WHERE effect_id = ?", (effect_id,)
    ).fetchone()[0] == 0
    assert store.connection.execute(
        "SELECT COUNT(*) FROM rpc_requests WHERE effect_id = ?", (effect_id,)
    ).fetchone()[0] == 0


def _malformed_thread_request(
    valid: dict[str, object], case: str, runtime_home: Path
) -> dict[str, object]:
    request = deepcopy(valid)
    if case.startswith("missing_"):
        request.pop(case.removeprefix("missing_"))
    elif case == "altered_cwd_other_scratch":
        request["cwd"] = str((runtime_home / "scratch" / "another").resolve())
    elif case == "altered_cwd_runtime_root":
        request["cwd"] = str(runtime_home.resolve())
    elif case == "altered_cwd_repo":
        request["cwd"] = str(Path.cwd().resolve())
    elif case == "altered_ephemeral":
        request["ephemeral"] = False
    elif case == "ephemeral_int":
        request["ephemeral"] = 1
    elif case == "ephemeral_float":
        request["ephemeral"] = 1.0
    elif case == "ephemeral_string":
        request["ephemeral"] = "true"
    elif case == "ephemeral_null":
        request["ephemeral"] = None
    elif case == "altered_approvalPolicy":
        request["approvalPolicy"] = "workspace-write"
    elif case == "approval_bool":
        request["approvalPolicy"] = True
    elif case == "approval_int":
        request["approvalPolicy"] = 1
    elif case == "approval_float":
        request["approvalPolicy"] = 1.0
    elif case == "approval_null":
        request["approvalPolicy"] = None
    elif case == "extra":
        request["sandbox"] = "workspace-write"
    else:  # pragma: no cover - table completeness guard
        raise AssertionError(case)
    return request


@pytest.mark.parametrize(
    "case",
    [
        "missing_cwd",
        "missing_ephemeral",
        "missing_approvalPolicy",
        "altered_cwd_other_scratch",
        "altered_cwd_runtime_root",
        "altered_cwd_repo",
        "altered_ephemeral",
        "ephemeral_int",
        "ephemeral_float",
        "ephemeral_string",
        "ephemeral_null",
        "altered_approvalPolicy",
        "approval_bool",
        "approval_int",
        "approval_float",
        "approval_null",
        "extra",
    ],
)
def test_thread_start_rejects_every_noncanonical_request_before_write(
    tmp_path: Path, case: str
) -> None:
    async def body() -> None:
        store = ObserverStore(tmp_path)
        _start_run(store)
        valid = canonical_canary_thread_start_request(tmp_path, CANARY_ID)
        malformed = _malformed_thread_request(valid, case, tmp_path)
        effect = EffectJournal(store.connection).prepare_effect(
            owner_kind="EPHEMERAL_CANARY",
            owner_id=CANARY_ID,
            binding_id=None,
            method="thread/start",
            client_key=f"canary:thread/start:{CANARY_ID}",
            request=malformed,
        )
        client = _NoSendClient()
        owner = AppServerSessionOwner(client, store)  # type: ignore[arg-type]

        with pytest.raises(SessionOwnerError, match="canary predecessor ownership"):
            await owner.submit_effect(effect.effect_id)

        _assert_prewrite_rejected(store, effect.effect_id, client, malformed)
        store.close()

    asyncio.run(body())


@pytest.mark.parametrize(
    "case",
    [
        "missing_cwd",
        "missing_ephemeral",
        "missing_approvalPolicy",
        "altered_cwd_other_scratch",
        "altered_cwd_runtime_root",
        "altered_cwd_repo",
        "altered_ephemeral",
        "ephemeral_int",
        "ephemeral_float",
        "ephemeral_string",
        "ephemeral_null",
        "altered_approvalPolicy",
        "approval_bool",
        "approval_int",
        "approval_float",
        "approval_null",
        "extra",
    ],
)
def test_turn_start_revalidates_the_historical_predecessor_request(
    tmp_path: Path, case: str
) -> None:
    async def body() -> None:
        store = ObserverStore(tmp_path)
        run_id = _start_run(store)
        valid_predecessor = canonical_canary_thread_start_request(
            tmp_path, CANARY_ID
        )
        predecessor = _seed_predecessor(store, run_id, valid_predecessor)
        malformed_predecessor = _malformed_thread_request(
            valid_predecessor, case, tmp_path
        )
        store.connection.execute(
            "UPDATE app_server_effects SET request_json = ? WHERE effect_id = ?",
            (
                json.dumps(
                    malformed_predecessor, sort_keys=True, separators=(",", ":")
                ),
                predecessor.effect_id,
            ),
        )
        store.connection.commit()
        valid_turn = canonical_canary_turn_start_request(THREAD_ID)
        effect = EffectJournal(store.connection).prepare_effect(
            owner_kind="EPHEMERAL_CANARY",
            owner_id=CANARY_ID,
            binding_id=None,
            predecessor_effect_id=predecessor.effect_id,
            method="turn/start",
            client_key=f"canary:turn/start:{CANARY_ID}",
            request=valid_turn,
        )
        client = _NoSendClient()
        owner = AppServerSessionOwner(client, store)  # type: ignore[arg-type]

        with pytest.raises(SessionOwnerError, match="canary predecessor ownership"):
            await owner.submit_effect(effect.effect_id)

        _assert_prewrite_rejected(store, effect.effect_id, client, valid_turn)
        store.close()

    asyncio.run(body())


def _malformed_turn_request(
    valid: dict[str, object], case: str
) -> dict[str, object]:
    request = deepcopy(valid)
    if case.startswith("missing_"):
        request.pop(case.removeprefix("missing_"))
    elif case == "altered_threadId":
        request["threadId"] = "thr_wrong"
    elif case == "threadId_bool":
        request["threadId"] = True
    elif case == "threadId_int":
        request["threadId"] = 1
    elif case == "threadId_float":
        request["threadId"] = 1.0
    elif case == "threadId_null":
        request["threadId"] = None
    elif case == "altered_input_text":
        request["input"] = [{"type": "text", "text": "arbitrary input"}]
    elif case == "altered_input_shape":
        request["input"] = [{"text": request["input"][0]["text"]}]  # type: ignore[index]
    elif case == "input_bool":
        request["input"] = True
    elif case == "input_int":
        request["input"] = 1
    elif case == "input_float":
        request["input"] = 1.0
    elif case == "input_null":
        request["input"] = None
    elif case == "input_string":
        request["input"] = "text"
    elif case == "nested_type_bool":
        request["input"][0]["type"] = True  # type: ignore[index]
    elif case == "nested_type_int":
        request["input"][0]["type"] = 1  # type: ignore[index]
    elif case == "nested_type_float":
        request["input"][0]["type"] = 1.0  # type: ignore[index]
    elif case == "nested_type_null":
        request["input"][0]["type"] = None  # type: ignore[index]
    elif case == "nested_text_bool":
        request["input"][0]["text"] = True  # type: ignore[index]
    elif case == "nested_text_int":
        request["input"][0]["text"] = 1  # type: ignore[index]
    elif case == "nested_text_float":
        request["input"][0]["text"] = 1.0  # type: ignore[index]
    elif case == "nested_text_null":
        request["input"][0]["text"] = None  # type: ignore[index]
    elif case == "altered_approvalPolicy":
        request["approvalPolicy"] = "workspace-write"
    elif case == "approval_bool":
        request["approvalPolicy"] = True
    elif case == "approval_int":
        request["approvalPolicy"] = 1
    elif case == "approval_float":
        request["approvalPolicy"] = 1.0
    elif case == "approval_null":
        request["approvalPolicy"] = None
    elif case == "extra":
        request["tools"] = []
    else:  # pragma: no cover - table completeness guard
        raise AssertionError(case)
    return request


@pytest.mark.parametrize(
    "case",
    [
        "missing_threadId",
        "missing_input",
        "missing_approvalPolicy",
        "altered_threadId",
        "threadId_bool",
        "threadId_int",
        "threadId_float",
        "threadId_null",
        "altered_input_text",
        "altered_input_shape",
        "input_bool",
        "input_int",
        "input_float",
        "input_null",
        "input_string",
        "nested_type_bool",
        "nested_type_int",
        "nested_type_float",
        "nested_type_null",
        "nested_text_bool",
        "nested_text_int",
        "nested_text_float",
        "nested_text_null",
        "altered_approvalPolicy",
        "approval_bool",
        "approval_int",
        "approval_float",
        "approval_null",
        "extra",
    ],
)
def test_turn_start_rejects_every_noncanonical_request_before_write(
    tmp_path: Path, case: str
) -> None:
    async def body() -> None:
        store = ObserverStore(tmp_path)
        run_id = _start_run(store)
        predecessor = _seed_predecessor(
            store,
            run_id,
            canonical_canary_thread_start_request(tmp_path, CANARY_ID),
        )
        valid = canonical_canary_turn_start_request(THREAD_ID)
        malformed = _malformed_turn_request(valid, case)
        effect = EffectJournal(store.connection).prepare_effect(
            owner_kind="EPHEMERAL_CANARY",
            owner_id=CANARY_ID,
            binding_id=None,
            predecessor_effect_id=predecessor.effect_id,
            method="turn/start",
            client_key=f"canary:turn/start:{CANARY_ID}",
            request=malformed,
        )
        client = _NoSendClient()
        owner = AppServerSessionOwner(client, store)  # type: ignore[arg-type]

        with pytest.raises(SessionOwnerError, match="canary predecessor ownership"):
            await owner.submit_effect(effect.effect_id)

        _assert_prewrite_rejected(store, effect.effect_id, client, malformed)
        store.close()

    asyncio.run(body())


@pytest.mark.parametrize(
    ("stored_thread_id", "response_thread_id"),
    [("1", 1), ("1.0", 1.0), ("True", True)],
)
def test_turn_start_rejects_coerced_predecessor_response_thread_id(
    tmp_path: Path, stored_thread_id: str, response_thread_id: object
) -> None:
    async def body() -> None:
        store = ObserverStore(tmp_path)
        run_id = _start_run(store)
        predecessor = _seed_predecessor(
            store,
            run_id,
            canonical_canary_thread_start_request(tmp_path, CANARY_ID),
        )
        store.connection.execute(
            """UPDATE app_server_effects
            SET thread_id = ?, response_json = ? WHERE effect_id = ?""",
            (
                stored_thread_id,
                json.dumps(
                    {
                        "result": {
                            "thread": {
                                "id": response_thread_id,
                                "ephemeral": True,
                            }
                        }
                    },
                    sort_keys=True,
                ),
                predecessor.effect_id,
            ),
        )
        store.connection.commit()
        request = canonical_canary_turn_start_request(stored_thread_id)
        effect = EffectJournal(store.connection).prepare_effect(
            owner_kind="EPHEMERAL_CANARY",
            owner_id=CANARY_ID,
            binding_id=None,
            predecessor_effect_id=predecessor.effect_id,
            method="turn/start",
            client_key=f"canary:turn/start:{CANARY_ID}",
            request=request,
        )
        client = _NoSendClient()
        owner = AppServerSessionOwner(client, store)  # type: ignore[arg-type]

        with pytest.raises(SessionOwnerError, match="canary predecessor ownership"):
            await owner.submit_effect(effect.effect_id)

        _assert_prewrite_rejected(store, effect.effect_id, client, request)
        store.close()

    asyncio.run(body())


@pytest.mark.parametrize("method", ["thread/start", "turn/start"])
def test_final_proof_validates_the_effective_request_override(
    tmp_path: Path, method: str
) -> None:
    async def body() -> None:
        store = ObserverStore(tmp_path)
        run_id = _start_run(store)
        journal = EffectJournal(store.connection)
        if method == "thread/start":
            predecessor = None
            valid = canonical_canary_thread_start_request(tmp_path, CANARY_ID)
        else:
            predecessor = _seed_predecessor(
                store,
                run_id,
                canonical_canary_thread_start_request(tmp_path, CANARY_ID),
            )
            valid = canonical_canary_turn_start_request(THREAD_ID)
        effect = journal.prepare_effect(
            owner_kind="EPHEMERAL_CANARY",
            owner_id=CANARY_ID,
            binding_id=None,
            predecessor_effect_id=(
                None if predecessor is None else predecessor.effect_id
            ),
            method=method,
            client_key=f"canary:{method}:{CANARY_ID}",
            request=valid,
        )
        override = deepcopy(valid)
        override["unrecognized"] = True
        client = _NoSendClient()
        owner = AppServerSessionOwner(client, store)  # type: ignore[arg-type]

        with pytest.raises(SessionOwnerError, match="canary predecessor ownership"):
            await owner.submit_effect(effect.effect_id, request_override=override)

        # The same write-start transaction that rejects the override also
        # rolls the journal request back to its original canonical value.
        _assert_prewrite_rejected(store, effect.effect_id, client, valid)
        store.close()

    asyncio.run(body())


def test_effective_canary_override_rejects_unsupported_non_json_before_write(
    tmp_path: Path,
) -> None:
    async def body() -> None:
        store = ObserverStore(tmp_path)
        _start_run(store)
        valid = canonical_canary_thread_start_request(tmp_path, CANARY_ID)
        effect = EffectJournal(store.connection).prepare_effect(
            owner_kind="EPHEMERAL_CANARY",
            owner_id=CANARY_ID,
            binding_id=None,
            method="thread/start",
            client_key=f"canary:thread/start:{CANARY_ID}",
            request=valid,
        )
        override = dict(valid)
        override["unsupported"] = ("tuple",)
        client = _NoSendClient()
        owner = AppServerSessionOwner(client, store)  # type: ignore[arg-type]

        with pytest.raises(EffectError, match="non-JSON"):
            await owner.submit_effect(effect.effect_id, request_override=override)

        _assert_prewrite_rejected(store, effect.effect_id, client, valid)
        store.close()

    asyncio.run(body())

from pathlib import Path

import pytest

from tools.codex_supervisor.db import connect, initialize_database
from tools.codex_supervisor.durability.graphs import ALLOWED_TRANSITIONS
from tools.codex_supervisor.durability.models import AggregateKind
from tools.codex_supervisor.durability.transitions import AGGREGATE_LOCATORS


def _open(tmp_path: Path):
    path = tmp_path / "state.sqlite3"
    connection = connect(path)
    initialize_database(connection)
    return connection


def _seed(connection) -> None:
    connection.execute(
        """INSERT INTO managed_actor_bindings(
            binding_id,actor_context_id,actor_kind,semantic_scope_key,
            thread_origin,history_trust,binding_state,memory_policy_state,
            repo_root,thread_cwd,created_by_operator,created_at
        ) VALUES ('bind1','act1','OPERATIONAL_ROOT','scope','NEW','FRESH','PREPARED','UNVERIFIED','r','c','op','t')"""
    )
    connection.execute(
        """INSERT INTO managed_turn_intents(
            turn_intent_id,binding_id,intent_kind,client_user_message_id,input_ref,
            submission_state,app_server_thread_id,prepared_at
        ) VALUES ('turn1','bind1','MANUAL_OPERATOR','msg1','ref','PREPARED','thr1','t')"""
    )
    connection.execute(
        """INSERT INTO wake_batches(
            wake_batch_id,binding_id,thread_id,state,client_user_message_id,prepared_at
        ) VALUES ('wake1','bind1','thr1','PREPARED','hmasd-wake:wake1','t')"""
    )
    connection.execute(
        """INSERT INTO mailbox_messages(
            message_id,source_system,source_event_key,target_actor_context_id,
            message_kind,subject_ref,payload_ref,priority,delivery_state,intake_state,created_at
        ) VALUES ('msg1','OPERATOR','src1','act1','OPERATOR_ATTENTION_REQUEST','s','p',1,'BATCHED','NOT_ACKNOWLEDGED','t')"""
    )
    connection.execute(
        """INSERT INTO managed_actor_commands(
            command_id,binding_id,thread_id,turn_id,raw_message_seq,command_kind,
            payload_json,validation_state,created_at
        ) VALUES ('cmd1','bind1','thr1','turnx',1,'NO_CONTROL_ACTION','{}','RECEIVED','t')"""
    )
    connection.execute(
        """INSERT INTO app_server_effects(
            effect_id,owner_kind,owner_id,method,client_key,request_json,state,prepared_at
        ) VALUES ('eff1','WAKE_BATCH','wake1','turn/start','hmasd-wake:wake1','{}','PREPARED','t')"""
    )
    connection.commit()


def test_illegal_wake_prepared_to_completed_fails(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    _seed(connection)
    with pytest.raises(Exception, match="illegal WAKE_BATCH transition"):
        connection.execute("UPDATE wake_batches SET state='COMPLETED' WHERE state='PREPARED'")
    connection.close()


def test_state_change_requires_version_increment(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    _seed(connection)
    with pytest.raises(Exception, match="WAKE_BATCH version must increment by 1"):
        connection.execute("UPDATE wake_batches SET state='SUBMITTING' WHERE state='PREPARED'")
    connection.execute("UPDATE wake_batches SET state='SUBMITTING', version=1 WHERE state='PREPARED'")
    assert connection.execute("SELECT state, version FROM wake_batches").fetchone()[0] == "SUBMITTING"
    connection.close()


def test_incident_exit_requires_operator_resolution(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    _seed(connection)
    connection.execute("UPDATE wake_batches SET state='INCIDENT', version=1 WHERE wake_batch_id='wake1'")
    connection.commit()
    with pytest.raises(Exception, match="illegal WAKE_BATCH transition"):
        connection.execute("UPDATE wake_batches SET state='CANCELLED', version=2 WHERE wake_batch_id='wake1'")
    connection.execute(
        """INSERT INTO operator_resolutions(
            resolution_id,aggregate_kind,aggregate_id,operator,disposition,
            evidence_kind,evidence_ref,payload_json,created_at
        ) VALUES ('r1','WAKE_BATCH','wake1','op','NO_SUBMISSION_EVIDENCE','NONE','ref','{}','t')"""
    )
    connection.execute("UPDATE wake_batches SET state='CANCELLED', version=2 WHERE wake_batch_id='wake1'")
    assert connection.execute("SELECT state FROM wake_batches").fetchone()[0] == "CANCELLED"
    connection.close()


def test_direct_sql_bypass_rejected_for_every_aggregate(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    _seed(connection)
    illegal_target = {
        AggregateKind.MANAGED_BINDING: "ACTIVE",
        AggregateKind.MANAGED_TURN: "COMPLETED",
        AggregateKind.WAKE_BATCH: "COMPLETED",
        AggregateKind.MAILBOX_DELIVERY: "ENQUEUED",
        AggregateKind.MAILBOX_INTAKE: "APPLIED",
        AggregateKind.MANAGED_COMMAND: "APPLIED",
        AggregateKind.APP_SERVER_EFFECT: "EFFECT_CONFIRMED",
    }
    ids = {
        AggregateKind.MANAGED_BINDING: "bind1",
        AggregateKind.MANAGED_TURN: "turn1",
        AggregateKind.WAKE_BATCH: "wake1",
        AggregateKind.MAILBOX_DELIVERY: "msg1",
        AggregateKind.MAILBOX_INTAKE: "msg1",
        AggregateKind.MANAGED_COMMAND: "cmd1",
        AggregateKind.APP_SERVER_EFFECT: "eff1",
    }
    for kind in ALLOWED_TRANSITIONS:
        locator = AGGREGATE_LOCATORS[kind]
        with pytest.raises(Exception, match=f"illegal {kind.value} transition"):
            connection.execute(
                f"UPDATE {locator.table} SET {locator.state_column}=? WHERE {locator.id_column}=?",
                (illegal_target[kind], ids[kind]),
            )
    connection.close()


def test_triggers_are_generated_from_allowed_transitions(tmp_path: Path) -> None:
    connection = _open(tmp_path)
    names = {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'durability_%'"
        )
    }
    expected = {f"durability_{locator.table}_{locator.state_column}_guard" for locator in AGGREGATE_LOCATORS.values()}
    assert names == expected
    connection.close()

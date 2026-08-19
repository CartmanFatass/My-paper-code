from pathlib import Path

import pytest

from tools.codex_supervisor.db import REQUIRED_TABLES, SCHEMA_VERSION, connect, initialize_database


V6_STATEMENTS = (
    """CREATE TABLE schema_meta (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)""",
    """CREATE TABLE observer_runs (
        run_id TEXT PRIMARY KEY,
        codex_binary TEXT NOT NULL,
        codex_version TEXT NOT NULL,
        client_name TEXT NOT NULL,
        process_id INTEGER,
        started_at TEXT NOT NULL,
        initialized_at TEXT,
        ended_at TEXT,
        exit_code INTEGER,
        end_kind TEXT,
        runtime_home TEXT NOT NULL
    )""",
    """CREATE TABLE raw_messages (
        raw_message_seq INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        direction TEXT NOT NULL,
        transport_seq INTEGER NOT NULL,
        rpc_shape TEXT NOT NULL,
        request_id TEXT,
        method TEXT,
        thread_id TEXT,
        turn_id TEXT,
        item_id TEXT,
        canonical_json TEXT NOT NULL,
        observed_at TEXT NOT NULL,
        UNIQUE(run_id, direction, transport_seq)
    )""",
    """CREATE TABLE rpc_requests (
        request_row_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        client_request_id TEXT NOT NULL,
        method TEXT NOT NULL,
        request_class TEXT NOT NULL,
        params_json TEXT NOT NULL,
        attempt_count INTEGER NOT NULL,
        sent_at TEXT NOT NULL,
        completed_at TEXT,
        outcome TEXT,
        error_code INTEGER,
        response_json TEXT,
        UNIQUE(run_id, client_request_id)
    )""",
    """CREATE TABLE managed_actor_bindings (
        binding_id TEXT PRIMARY KEY,
        actor_context_id TEXT NOT NULL UNIQUE,
        actor_kind TEXT NOT NULL,
        semantic_scope_key TEXT NOT NULL,
        direction_id TEXT,
        thread_id TEXT UNIQUE,
        thread_origin TEXT NOT NULL,
        history_trust TEXT NOT NULL,
        binding_state TEXT NOT NULL,
        memory_policy_state TEXT NOT NULL,
        repo_root TEXT NOT NULL,
        thread_cwd TEXT NOT NULL,
        created_by_operator TEXT NOT NULL,
        created_at TEXT NOT NULL,
        thread_created_at TEXT,
        verified_at TEXT,
        activated_at TEXT,
        suspended_at TEXT,
        revoked_at TEXT,
        last_verified_at TEXT,
        last_thread_status TEXT,
        last_turn_id TEXT,
        verification_turn_intent_id TEXT,
        verification_turn_id TEXT,
        verification_command_id TEXT,
        verification_receipt_id TEXT,
        verified_checkpoint_id TEXT,
        verified_state_version INTEGER,
        verified_epoch_id TEXT,
        verified_epoch_revision INTEGER
    )""",
    """CREATE TABLE managed_turn_intents (
        turn_intent_id TEXT PRIMARY KEY,
        binding_id TEXT NOT NULL,
        intent_kind TEXT NOT NULL,
        client_user_message_id TEXT NOT NULL UNIQUE,
        checkpoint_id TEXT,
        expected_state_version INTEGER,
        expected_epoch_id TEXT,
        expected_epoch_revision INTEGER,
        input_ref TEXT NOT NULL,
        submission_state TEXT NOT NULL,
        app_server_thread_id TEXT NOT NULL,
        app_server_turn_id TEXT,
        app_server_request_id TEXT,
        prepared_at TEXT NOT NULL,
        submitted_at TEXT,
        observed_at TEXT,
        completed_at TEXT,
        completion_status TEXT,
        incident_json TEXT
    )""",
    """CREATE TABLE managed_actor_commands (
        command_id TEXT PRIMARY KEY,
        binding_id TEXT NOT NULL,
        thread_id TEXT NOT NULL,
        turn_id TEXT NOT NULL,
        raw_message_seq INTEGER NOT NULL,
        command_kind TEXT NOT NULL,
        expected_checkpoint_id TEXT,
        expected_state_version INTEGER,
        expected_epoch_id TEXT,
        expected_epoch_revision INTEGER,
        payload_json TEXT NOT NULL,
        validation_state TEXT NOT NULL,
        rejection_reason TEXT,
        created_at TEXT NOT NULL,
        validated_at TEXT,
        applied_at TEXT,
        UNIQUE(binding_id, turn_id, raw_message_seq)
    )""",
    """CREATE TABLE mailbox_messages (
        message_id TEXT PRIMARY KEY,
        source_system TEXT NOT NULL,
        source_event_key TEXT NOT NULL UNIQUE,
        sender_actor_context_id TEXT,
        target_actor_context_id TEXT NOT NULL,
        message_kind TEXT NOT NULL,
        subject_ref TEXT NOT NULL,
        payload_ref TEXT NOT NULL,
        direction_id TEXT,
        epoch_id TEXT,
        priority INTEGER NOT NULL,
        delivery_state TEXT NOT NULL,
        intake_state TEXT NOT NULL,
        created_at TEXT NOT NULL,
        eligible_at TEXT,
        batched_at TEXT,
        delivered_at TEXT,
        acknowledged_at TEXT,
        intaken_at TEXT,
        applied_at TEXT,
        dead_letter_reason TEXT,
        source_resolved_after_submission INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE wake_batches (
        wake_batch_id TEXT PRIMARY KEY,
        binding_id TEXT NOT NULL,
        thread_id TEXT NOT NULL,
        state TEXT NOT NULL,
        client_user_message_id TEXT NOT NULL UNIQUE,
        app_server_request_id TEXT,
        app_server_turn_id TEXT,
        prepared_at TEXT NOT NULL,
        submitted_at TEXT,
        observed_at TEXT,
        completed_at TEXT,
        completion_status TEXT,
        incident_json TEXT,
        lease_generation INTEGER,
        lease_holder TEXT
    )""",
    """CREATE TABLE mutation_intents (
        intent_id TEXT PRIMARY KEY,
        method TEXT NOT NULL,
        binding_id TEXT,
        client_key TEXT NOT NULL,
        state TEXT NOT NULL,
        request_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE UNIQUE INDEX mutation_intents_open_unique
    ON mutation_intents(method, client_key)
    WHERE state IN ('SUBMITTING', 'SUBMISSION_UNCERTAIN', 'SUBMITTED_UNRECONCILED', 'INCIDENT')""",
)


def _seed_v6(path: Path) -> None:
    connection = connect(path)
    with connection:
        for statement in V6_STATEMENTS:
            connection.execute(statement)
        connection.execute("INSERT INTO schema_meta(version, applied_at) VALUES (6, 't')")
        connection.execute(
            """INSERT INTO observer_runs(
                run_id,codex_binary,codex_version,client_name,started_at,runtime_home
            ) VALUES ('run1','b','v','c','t','h')"""
        )
        connection.execute(
            """INSERT INTO raw_messages(
                run_id,direction,transport_seq,rpc_shape,canonical_json,observed_at
            ) VALUES ('run1','stdin',1,'REQUEST','{"method":"turn/start"}','t')"""
        )
        connection.execute(
            """INSERT INTO rpc_requests(
                request_row_id,run_id,client_request_id,method,request_class,
                params_json,attempt_count,sent_at
            ) VALUES ('rpc1','run1','req1','turn/start','MUTATING_NO_RETRY','{}',1,'t')"""
        )
        connection.execute(
            """INSERT INTO managed_actor_bindings(
                binding_id,actor_context_id,actor_kind,semantic_scope_key,
                thread_id,thread_origin,history_trust,binding_state,memory_policy_state,
                repo_root,thread_cwd,created_by_operator,created_at
            ) VALUES (
                'bind1','act1','OPERATIONAL_ROOT','scope','thr1','NEW','FRESH',
                'ACTIVE','DISABLED_BY_THREAD_API','r','c','op','t'
            )"""
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
            ) VALUES (
                'msg1','OPERATOR','src1','act1','OPERATOR_ATTENTION_REQUEST','s','p',1,
                'ELIGIBLE','NOT_ACKNOWLEDGED','t'
            )"""
        )
        connection.execute(
            """INSERT INTO managed_actor_commands(
                command_id,binding_id,thread_id,turn_id,raw_message_seq,command_kind,
                payload_json,validation_state,created_at
            ) VALUES ('cmd1','bind1','thr1','turnx',1,'NO_CONTROL_ACTION','{}','RECEIVED','t')"""
        )
        connection.execute(
            """INSERT INTO mutation_intents(
                intent_id,method,binding_id,client_key,state,request_json,created_at,updated_at
            ) VALUES ('mut1','turn/start','bind1','msg1','SUBMITTING','{}','t','t')"""
        )
    connection.close()


def test_v6_to_v7_preserves_rows_and_adds_kernel_tables(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite3"
    _seed_v6(path)
    connection = connect(path)
    initialize_database(connection)
    assert connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == 7
    assert SCHEMA_VERSION == 7
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert set(REQUIRED_TABLES) <= tables
    assert "app_server_effects" in tables
    assert "control_transitions" in tables
    assert "operator_resolutions" in tables
    assert "mutation_intents" in tables
    assert connection.execute("SELECT binding_id FROM managed_actor_bindings").fetchone()[0] == "bind1"
    assert connection.execute("SELECT turn_intent_id FROM managed_turn_intents").fetchone()[0] == "turn1"
    assert connection.execute("SELECT wake_batch_id FROM wake_batches").fetchone()[0] == "wake1"
    assert connection.execute("SELECT message_id FROM mailbox_messages").fetchone()[0] == "msg1"
    assert connection.execute("SELECT command_id FROM managed_actor_commands").fetchone()[0] == "cmd1"
    assert connection.execute("SELECT intent_id FROM mutation_intents").fetchone()[0] == "mut1"
    assert connection.execute("SELECT request_row_id FROM rpc_requests").fetchone()[0] == "rpc1"
    assert connection.execute("SELECT COUNT(*) FROM raw_messages").fetchone()[0] == 1
    assert connection.execute("SELECT version FROM managed_actor_bindings").fetchone()[0] == 0
    assert connection.execute("SELECT version FROM managed_turn_intents").fetchone()[0] == 0
    assert connection.execute("SELECT version FROM wake_batches").fetchone()[0] == 0
    assert connection.execute("SELECT delivery_version FROM mailbox_messages").fetchone()[0] == 0
    assert connection.execute("SELECT intake_version FROM mailbox_messages").fetchone()[0] == 0
    assert connection.execute("SELECT version FROM managed_actor_commands").fetchone()[0] == 0
    turn_cols = {row[1] for row in connection.execute("PRAGMA table_info(managed_turn_intents)")}
    wake_cols = {row[1] for row in connection.execute("PRAGMA table_info(wake_batches)")}
    raw_cols = {row[1] for row in connection.execute("PRAGMA table_info(raw_messages)")}
    rpc_cols = {row[1] for row in connection.execute("PRAGMA table_info(rpc_requests)")}
    mut_cols = {row[1] for row in connection.execute("PRAGMA table_info(mutation_intents)")}
    assert "effect_id" in turn_cols
    assert "effect_id" in wake_cols
    assert "effect_id" in raw_cols
    assert "effect_id" in rpc_cols
    assert "superseded_by_effect_id" in mut_cols
    index_sql = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND name='mutation_intents_open_unique'"
    ).fetchone()[0]
    assert "SUBMITTED_UNRECONCILED" in index_sql
    assert "INCIDENT" in index_sql
    initialize_database(connection)
    assert connection.execute("SELECT MAX(version) FROM schema_meta").fetchone()[0] == 7
    connection.close()


def test_v7_uniqueness_constraints(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite3"
    connection = connect(path)
    initialize_database(connection)
    connection.execute(
        """INSERT INTO app_server_effects(
            effect_id,owner_kind,owner_id,method,client_key,request_json,state,prepared_at
        ) VALUES ('e1','MANAGED_TURN','t1','turn/start','key1','{}','PREPARED','t')"""
    )
    with pytest.raises(Exception):
        connection.execute(
            """INSERT INTO app_server_effects(
                effect_id,owner_kind,owner_id,method,client_key,request_json,state,prepared_at
            ) VALUES ('e2','MANAGED_TURN','t1','turn/start','key1','{}','PREPARED','t')"""
        )
    connection.execute(
        """INSERT INTO operator_resolutions(
            resolution_id,aggregate_kind,aggregate_id,operator,disposition,
            evidence_kind,evidence_ref,payload_json,created_at
        ) VALUES ('r1','WAKE_BATCH','wake1','op','ABANDON','NONE','ref','{}','t')"""
    )
    with pytest.raises(Exception):
        connection.execute(
            """INSERT INTO operator_resolutions(
                resolution_id,aggregate_kind,aggregate_id,operator,disposition,
                evidence_kind,evidence_ref,payload_json,created_at
            ) VALUES ('r2','WAKE_BATCH','wake1','op','ABANDON','NONE','ref','{}','t')"""
        )
    connection.execute(
        """INSERT INTO control_transitions(
            transition_id,aggregate_kind,aggregate_id,state_column,from_state,to_state,
            from_version,to_version,cause_kind,cause_ref,metadata_json,created_at
        ) VALUES ('tr1','WAKE_BATCH','wake1','state','PREPARED','SUBMITTING',0,1,'OPERATOR_ACTION','c','{}','t')"""
    )
    with pytest.raises(Exception):
        connection.execute(
            """INSERT INTO control_transitions(
                transition_id,aggregate_kind,aggregate_id,state_column,from_state,to_state,
                from_version,to_version,cause_kind,cause_ref,metadata_json,created_at
            ) VALUES ('tr2','WAKE_BATCH','wake1','state','PREPARED','SUBMITTING',0,1,'OPERATOR_ACTION','c','{}','t')"""
        )
    connection.close()


def test_newer_schema_still_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite3"
    connection = connect(path)
    with connection:
        connection.execute("CREATE TABLE schema_meta (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
        connection.execute("INSERT INTO schema_meta(version, applied_at) VALUES (99, 't')")
    with pytest.raises(RuntimeError, match="newer than supported"):
        initialize_database(connection)
    connection.close()

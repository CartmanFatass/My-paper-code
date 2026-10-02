"""Synthetic semantic checks; no environment, RF scorer, actor or optimizer."""
import numpy as np
import pytest

from experiments.candidates.uav_decision_generalization.b03_joint_window import independent as r


def test_window_requires_routed_successors_resets_at_boundary_and_pays_once():
    connections = np.zeros((500, 6, 50), dtype=bool)
    lengths = np.full((500, 6), 2, dtype=np.int16)
    order = np.asarray((0, 1, 2, 3), dtype=np.uint8)
    # Nineteen qualified successors never pay. An unrouted20th contact breaks it.
    connections[:20, 0, 10:18] = True
    lengths[19, 0] = 0
    # A later run pays at action39, once, despite another qualified run.
    connections[20:75, 0, 10:18] = True
    connections[76:100, 0, 10:18] = True
    # A late19-tick run must not carry into the next window.
    connections[106:125, 0, 10:18] = True
    connections[125:144, 0, 20:28] = True
    # The qualifying eight may change identities from tick to tick.
    for tick in range(250, 270):
        chosen = np.roll(np.arange(30, 40), tick % 10)[:8]
        connections[tick, 0, chosen] = True
    facts = r.ledger(connections, lengths, order)
    assert np.flatnonzero(facts['payment']).tolist() == [39, 269]
    assert facts['run_length'][125] == 1
    assert facts['active_count'][19] == 0
    assert facts['associated_user_mask'][19].sum() == 8
    assert facts['paid'][-1].tolist() == [True, False, True, False]
    assert facts['external_scalar'].sum() == pytest.approx(1 / 3)


def test_bfs_limit_counts_intermediate_uavs_and_keeps_full_nodes():
    adjacency = np.zeros((6, 6), dtype=bool)
    for i in range(4):
        adjacency[i, i + 1] = adjacency[i + 1, i] = True
    bs = np.zeros((6, 1), dtype=bool)
    bs[4, 0] = True
    paths, lengths = r.routing(adjacency, bs)
    assert lengths[0] == 0
    assert paths[1, :lengths[1]].tolist() == [1, 2, 3, 4, 6]
    assert paths[4, :lengths[4]].tolist() == [4, 6]
    assert np.all(paths[lengths == 0] == -1)


def test_information_clock_and_quantized_count_state_keep_existing_route_bits():
    xyz = np.tile(np.asarray((1234.567890123, 2345.678901234, 100.123456789)), (6, 1))
    users = np.tile(np.asarray((2500, 2500)), (50, 1))
    physical = {'user_sinr': np.full((6, 50), -100.), 'uav_sinr': np.full((6, 6), -100.),
                'bs_connections': np.ones((6, 1), dtype=bool), 'route_lengths': np.full(6, 2)}
    order = np.asarray((2, 0, 3, 1), dtype=np.uint8)
    before, state = r.information(xyz, users, order, 124, physical)
    after, _ = r.information(xyz, users, order, 125, physical)
    terminal, last_state = r.information(xyz, users, order, 500, physical)
    assert before.shape == (6, 211) and state.shape == (154,)
    assert before.dtype == state.dtype == np.float32
    assert before[0, 88] == 1 and before[0, 89] == np.float32(2 / 3)
    assert before[0, 206:210].tolist() == [0, 0, 1, 0]
    assert after[0, 206:210].tolist() == [1, 0, 0, 0]
    assert before[0, 210] == np.float32(1 / 125) and after[0, 210] == 1
    assert np.all(terminal[:, 206:] == 0) and np.all(last_state[-5:] == 0)
    assert state[0] == np.float32(xyz[0, 0]) / np.float32(5000)
    assert state[24:32].tolist() == [1, 1, 1, 1, 1, 1, 0, 0]
    assert np.all(before[:, 3:87] == 0)


def test_raw_action_dtype_is_preserved_and_movement_is_clipped_after_velocity():
    raw = np.zeros((6, 3), dtype=np.float32)
    raw[0] = (3, 4, 0)
    raw[1] = (0, 0, -2)
    positions = np.tile(np.asarray((4999., 100., 50.)), (6, 1))
    saved = raw.copy()
    commands, following, events = r.motion(positions, raw)
    assert commands.dtype == np.float32
    assert events == 2
    assert np.array_equal(raw, saved)
    assert following[0, 0] == 5000 and following[1, 2] == 50
    assert following[0, 1] == 124
    assert np.linalg.norm(commands[0]) == 1


def test_never_served_and_edge_censoring_remain_full_mission_gaps():
    assert r.zero_runs(np.zeros(500, dtype=bool)) == [
        {'start': 0, 'stop': 500, 'length': 500, 'left_censored': True, 'right_censored': True}]
    assert r.zero_runs([False, True, False, False, True, False]) == [
        {'start': 0, 'stop': 1, 'length': 1, 'left_censored': True, 'right_censored': False},
        {'start': 2, 'stop': 4, 'length': 2, 'left_censored': False, 'right_censored': False},
        {'start': 5, 'stop': 6, 'length': 1, 'left_censored': False, 'right_censored': True}]
    assert r.zero_runs(np.ones(500, dtype=bool)) == []


def test_evidence_identity_must_match_bytes_and_stay_inside_worker_root(tmp_path):
    path = tmp_path / 'evidence.bin'
    path.write_bytes(b'evidence')
    import hashlib
    identity = {'path': 'evidence.bin', 'bytes': 8, 'sha256': hashlib.sha256(b'evidence').hexdigest()}
    assert r.checked_file(tmp_path, identity) == path
    path.write_bytes(b'different')
    with pytest.raises(AssertionError, match='identity changed'):
        r.checked_file(tmp_path, identity)


def test_same_rejects_nan_and_different_shapes():
    with pytest.raises(AssertionError, match='nonfinite'):
        r.same([np.nan], [np.nan], 'bad')
    with pytest.raises(AssertionError, match='shape'):
        r.same(np.zeros((1, 2)), np.zeros(2), 'bad')


def test_high_level_segments_use_discounted_external_sixth_only():
    table = {'d2_team_valid': np.arange(500) % 10 == 0,
             'd2_agent_valid': np.broadcast_to((np.arange(500) % 10 == 0)[:, None], (500, 6)),
             'd2_team_reward': np.zeros(500, dtype=np.float32),
             'd2_agent_reward': np.zeros((500, 6), dtype=np.float32),
             'd2_team_elapsed': np.full(500, 10), 'd2_agent_elapsed': np.full((500, 6), 10),
             'd2_team_terminal': np.zeros(500, dtype=bool), 'd2_agent_terminal': np.zeros((500, 6), dtype=bool)}
    table['d2_team_terminal'][490] = True
    table['d2_agent_terminal'][490] = True
    raw = {'external_scalar': np.zeros(500)}
    raw['external_scalar'][19] = 1 / 6
    table['d2_team_reward'][10] = .99 ** 9 / 6
    table['d2_agent_reward'][10] = .99 ** 9 / 6
    assert r.check_d2(table, raw)['team_segments'] == 50
    table['d2_team_reward'][10] = 1.
    with pytest.raises(AssertionError, match='external-only'):
        r.check_d2(table, raw)


def test_world_pairing_and_initial_alias_do_not_create_training_replicates():
    from experiments.candidates.uav_decision_generalization.b03_joint_window import contract as c
    rows = [{'programme': p, 'world': w, 'phase': 'main',
             'metrics': {'W': int(p == 'H-final'), 'J_dense': 0.}}
            for p in c.PROGRAMMES for w in c.WORLDS]
    reading = r.comparisons(rows)
    assert reading['primary']['H-final minus H-noD-final']['W']['mean'] == 1
    assert reading['initial_to_final']['H-noD']['W']['mean'] == 0
    assert len(reading['all28_pairs']) == 28
    assert reading['levels']['H-noD-initial'] == reading['levels']['H-initial']
    assert 'no training replication' in reading['scope'].lower()

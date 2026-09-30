"""A worker and its reader share source but must not share terminal evidence."""

from copy import deepcopy
import json

import pytest

from experiments.candidates.uav_user_waiting.b04_result import SOURCE, terminal


@pytest.fixture
def records():
    admission = dict(sha=SOURCE, direction='uav_user_waiting', parent_pid=200, child_pid=201)
    status = dict(sha=SOURCE, direction='uav_user_waiting', node='wsl_4070',
        record_consistency=dict(state='consistent'),
        execution=dict(state='exited', exit_code=0, exit_witness=dict(state='valid'),
                       runner=dict(recorded_identity=dict(pid=201)),
                       supervisor=dict(recorded_identity=dict(pid=200))))
    return admission, status


def test_matched_reader_status_is_accepted(tmp_path, records):
    admission, status = records
    path = tmp_path / 'reader-status.json'
    path.write_text(json.dumps(status))
    assert terminal(path, SOURCE, admission) == status


@pytest.mark.parametrize('wrong', ['worker', 'supervisor', 'node', 'direction'])
def test_same_source_wrong_process_or_node_is_rejected(tmp_path, records, wrong):
    admission, status = records
    status = deepcopy(status)
    if wrong == 'worker':
        status['execution']['runner']['recorded_identity']['pid'] = 101
        status['execution']['supervisor']['recorded_identity']['pid'] = 100
    elif wrong == 'supervisor':
        status['execution']['supervisor']['recorded_identity']['pid'] = 100
    elif wrong == 'node':
        status['node'] = 'local_linux'
    else:
        status['direction'] = 'another_direction'
    path = tmp_path / 'wrong-status.json'
    path.write_text(json.dumps(status))
    with pytest.raises(AssertionError):
        terminal(path, SOURCE, admission)

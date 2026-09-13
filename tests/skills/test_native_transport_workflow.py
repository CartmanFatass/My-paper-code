"""Focused external-effect contracts. No provider/UI/network calls or scientific invocation."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'tests/fixtures/native_transport'
sys.path.insert(0, str(ROOT / '.agents/skills/hmasd-chatgpt-pro-transport/scripts'))
import native_transport as n

SHA = '9929beb6eb699b94603a1dfd5d200363e5802ed1'
HANDOFF = 'docs/research/portfolio/pro_packets/20260912_mgtap_unequal_exposure_investment/delivery/HANDOFF.json'
ROUTE = n.execution_route('/root/dm_mgtap_resume', '/root/dm_mgtap_resume/tr_lh_mgtap',
                          'Root Transport redesign and original MGTAP recovery')


@pytest.fixture
def preflight():
    return n.read_handoff(ROOT, SHA, HANDOFF, ROUTE)


@pytest.fixture
def record(preflight):
    return {**preflight, 'provider_url': f"https://chatgpt.com/c/{preflight['conversation_id']}",
            'state': 'DIRECTION_VERIFIED', 'send_click_count': 0, 'agentify_stable_key': None}


@pytest.fixture
def operation():
    raw = json.loads((FIXTURE / 'mgtap-presend.json').read_text(encoding='utf-8'))
    return {**raw, **raw['operationState']}


@pytest.fixture
def page():
    return json.loads((FIXTURE / 'page-ready.json').read_text(encoding='utf-8'))['page']


def test_exact_committed_mgtap_handoff_and_materialized_packet(preflight, tmp_path):
    assert preflight['prompt_bytes'] == 1925
    assert preflight['prompt_sha256'] == 'f6e468abc5df9ef6751c70b11891e8ab2813a722fcb8430c65cb5236ebf9aef0'
    assert preflight['manifest']['workflow_node'] == 'portfolio_decision'
    assert preflight['conversation_binding_key'] == 'portfolio:cross_direction'
    assert preflight['frozen_routing']['parent_thread_id'] == '01a095b7-850f-7401-ad4e-5e4320d285f1'
    assert preflight['execution_route'] == ROUTE
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(preflight['manifest']), encoding='utf-8')
    prompt = tmp_path / preflight['manifest']['body']['canonical_filename']
    prompt.write_bytes(preflight['prompt'].encode('utf-8'))
    n.verify_packet(preflight, manifest, prompt)
    prompt.write_bytes(prompt.read_bytes() + b' ')
    with pytest.raises(ValueError, match='exact bytes'):
        n.verify_packet(preflight, manifest, prompt)


@pytest.mark.parametrize('field', ['caller_role', 'parent_thread_id', 'operator_thread_id', 'workflow_node', 'conversation_binding_key'])
def test_top_level_nested_metadata_mismatch_is_rejected(monkeypatch, field):
    raw = json.loads(subprocess.check_output(['git', 'show', f'{SHA}:{HANDOFF}'], cwd=ROOT))
    raw[field] = 'changed'
    monkeypatch.setattr(n.subprocess, 'check_output', lambda *a, **kw: json.dumps(raw).encode())
    with pytest.raises(ValueError, match='handoff/nested'):
        n.read_handoff(ROOT, SHA, HANDOFF, ROUTE)


@pytest.mark.parametrize('sha,path', [('short', HANDOFF), (SHA, '../HANDOFF.json'), (SHA, '/HANDOFF.json')])
def test_unfixed_handoff_rejected(sha, path):
    with pytest.raises(ValueError):
        n.read_handoff(ROOT, sha, path, ROUTE)


def test_first_binding_is_explicitly_left_to_existing_route(monkeypatch):
    raw = json.loads(subprocess.check_output(['git', 'show', f'{SHA}:{HANDOFF}'], cwd=ROOT))
    raw['requested_conversation_id'] = None
    raw['transport_request']['requested_conversation_id'] = None
    monkeypatch.setattr(n.subprocess, 'check_output', lambda *a, **kw: json.dumps(raw).encode())
    with pytest.raises(ValueError, match='existing firstBinding route'):
        n.read_handoff(ROOT, SHA, HANDOFF, ROUTE)


def test_shared_binding_single_writer_and_history(preflight, tmp_path):
    registry = tmp_path / 'registry.json'
    first = n.claim_binding(registry, preflight)
    assert n.claim_binding(registry, preflight) == first
    before = registry.read_bytes()
    other = copy.deepcopy(preflight)
    other['request_id'] += '-other'
    with pytest.raises(ValueError, match='BINDING_BUSY'):
        n.claim_binding(registry, other)
    other = copy.deepcopy(preflight)
    other['execution_route'] = n.execution_route('/root/other', '/root/other/transport', 'other writer')
    with pytest.raises(ValueError, match='BINDING_BUSY'):
        n.claim_binding(registry, other)
    assert registry.read_bytes() == before
    changed = copy.deepcopy(preflight)
    changed['frozen_handoff']['sha'] = '0' * 40
    with pytest.raises(ValueError, match='immutable HANDOFF'):
        n.claim_binding(registry, changed)
    with n.registry_lock(registry):
        with pytest.raises(RuntimeError, match='LOCK_BUSY'):
            n.claim_binding(registry, preflight)
    assert not registry.with_name('registry.json.lock').exists()
    data = json.loads(before)
    key = preflight['conversation_binding_key']
    data['bindings'][key]['state'] = 'ARCHIVED'
    data['bindings'][key]['agentify_stable_key'] = 'hmasd-gen:preserved-generation'
    data['directions']['portfolio']['agentify_stable_key'] = 'hmasd-gen:preserved-generation'
    data['directions']['portfolio']['state'] = 'ARCHIVED'
    registry.write_text(json.dumps(data), encoding='utf-8')
    other = copy.deepcopy(preflight)
    other['request_id'] += '-next'
    successor = n.claim_binding(registry, other)
    assert successor['request_history'][0]['request_id'] == preflight['request_id']
    assert successor['conversation_id'] == preflight['conversation_id']
    assert successor['agentify_stable_key'] == 'hmasd-gen:preserved-generation'


def test_other_node_cannot_claim_same_conversation(preflight, tmp_path):
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps({'bindings': {'em:other:convergence': {
        'conversation_id': preflight['conversation_id'], 'request_id': 'other', 'state': 'WAITING_GENERATION'}}}), encoding='utf-8')
    before = path.read_bytes()
    with pytest.raises(ValueError, match='already bound to another node'):
        n.claim_binding(path, preflight)
    assert path.read_bytes() == before


@pytest.mark.parametrize('mirror_update', [
    {'state': 'ARCHIVED', 'response_sha256': 'a' * 64, 'archive': {'response_file': 'unique-full-answer.md'}},
    {'github_delivery': {'status': 'VERIFIED_GITHUB_FULL_RESPONSE', 'delivery_commit': 'f' * 40}}])
def test_mirror_only_archive_is_retained_as_conflict(preflight, tmp_path, mirror_update):
    path = tmp_path / 'registry.json'
    n.claim_binding(path, preflight)
    data = json.loads(path.read_text())
    data['directions']['portfolio'].update(mirror_update)
    path.write_text(json.dumps(data), encoding='utf-8')
    before = path.read_bytes()
    with pytest.raises(ValueError, match='mirror effect/receipt differs'):
        n.claim_binding(path, preflight)
    assert path.read_bytes() == before


def test_recovery_preserves_legacy_route_and_detects_mirror_conflict(preflight, tmp_path):
    path = tmp_path / 'registry.json'
    old = {'request_id': preflight['request_id'], 'parent_thread_id': 'legacy-wrong-parent',
           'return_receipt': {'destination_thread_id': 'legacy-wrong-parent', 'status': 'PENDING'}}
    path.write_text(json.dumps({'bindings': {preflight['conversation_binding_key']: old}}), encoding='utf-8')
    recovered = n.claim_binding(path, preflight)
    assert recovered['parent_thread_id'] == old['parent_thread_id']
    assert recovered['return_receipt'] == old['return_receipt']
    assert recovered['frozen_routing'] != recovered['execution_route']
    data = json.loads(path.read_text())
    data['directions']['portfolio']['request_id'] = 'another-request'
    path.write_text(json.dumps(data), encoding='utf-8')
    before = path.read_bytes()
    with pytest.raises(ValueError, match='BINDING_CONFLICT'):
        n.claim_binding(path, preflight)
    assert path.read_bytes() == before


def test_screenshot_fixture_is_annotated_and_not_acceptance_proof(record, operation, page):
    fixture = json.loads((FIXTURE / 'page-ready.json').read_text())
    assert n.digest((FIXTURE / fixture['screenshot']).read_bytes()) == fixture['screenshot_sha256']
    assert fixture['historical_receipt_visible']
    assert n.next_step(record, operation, page)['effect'] == 'UNCERTAIN_EFFECT'
    repaired = n.next_step(record, operation, page, verified_nonacceptance=True)
    assert repaired == {'state': 'READY_UNSENT', 'effect': 'VERIFIED_NONACCEPTANCE', 'action': 'SEND', 'reasons': []}


@pytest.mark.parametrize('change,reason', [
    ({'url': 'https://chatgpt.com/c/other'}, 'conversation'),
    ({'tab_key': 'another-key'}, 'tab_key'), ({'protected': True}, 'protected_tab'),
    ({'logged_in': False}, 'page_ready'), ({'composer_ready': False}, 'page_ready'),
    ({'product_model': 'Fast'}, 'model_or_effort'), ({'reasoning_effort': 'Thinking'}, 'model_or_effort'),
    ({'current_generation_active': True}, 'current_generation')])
def test_failed_page_preflight_repairs_same_request(record, operation, page, change, reason):
    result = n.next_step(record, operation, {**page, **change}, verified_nonacceptance=True)
    assert result['action'] == 'REPAIR_PREFLIGHT' and reason in result['reasons']
    assert n.next_step(record, operation, page, verified_nonacceptance=True)['action'] == 'SEND'


@pytest.mark.parametrize('attempted', [True, None, 'false'])
def test_unknown_or_attempted_never_resends(record, operation, page, attempted):
    operation['sendAttempted'] = attempted
    assert n.next_step(record, operation, page, verified_nonacceptance=True)['action'] == 'OBSERVE_ONLY'


def test_accepted_or_legacy_send_overrules_false(record, operation, page):
    operation['providerUserMessageId'] = 'current-user'
    assert n.next_step(record, operation, page, verified_nonacceptance=True)['effect'] == 'ACCEPTED'
    operation['providerUserMessageId'] = None
    record['send_evidence'] = {'send_click_count': 0, 'user_node_observed': False}
    assert n.next_step(record, operation, page, verified_nonacceptance=True)['action'] == 'SEND'
    record['send_evidence']['send_click_count'] = 1
    assert n.next_step(record, operation, page, verified_nonacceptance=True)['action'] == 'OBSERVE_ONLY'
    assert n.next_step(record, None, page)['action'] == 'OBSERVE_ONLY'


@pytest.mark.parametrize('prior', [{'state': 'WAITING_GENERATION'},
    {'timestamps': {'sent_at': '2026-09-12T00:00:00Z'}}, {'send_evidence': {'observed_after_successful_send': True}},
    {'send_reconciliation_history': [{'outcome': 'ACCEPTED'}]}])
def test_preserved_legacy_effect_cannot_be_erased_by_false_operation(record, operation, page, prior):
    record.update(prior)
    assert n.next_step(record, operation, page, verified_nonacceptance=True)['action'] == 'OBSERVE_ONLY'


def test_native_bookkeeping_does_not_lock_verified_presend_failure(record, operation, page):
    record['native_state'] = 'SEND_ATTEMPTED'
    assert n.next_step(record, operation, page, verified_nonacceptance=True)['action'] == 'SEND'


@pytest.mark.parametrize('field', ['idempotencyKey', 'promptSha256', 'stableKey', 'conversationId', 'conversationUrl', 'productModel', 'reasoningEffort', 'responsePath', 'operationId'])
def test_operation_identity_cannot_be_rebound(record, operation, page, field):
    record['operation'] = copy.deepcopy(operation)
    operation[field] = 'different'
    with pytest.raises(ValueError, match='mismatch'):
        n.next_step(record, operation, page, verified_nonacceptance=True)


@pytest.mark.parametrize('bad', [True, 0, 999, 60001])
def test_observation_has_one_bounded_window(bad):
    assert n.observe_timeout(60000) == 60000
    with pytest.raises(ValueError):
        n.observe_timeout(bad)


@pytest.mark.parametrize('outcome', ['SENT', 'UNCERTAIN', 'REJECTED_BEFORE_DELIVERY'])
def test_full_archive_and_one_current_parent_receipt(record, tmp_path, outcome):
    path = tmp_path / 'full-response.md'
    path.write_bytes('# Full answer\nExact bytes.\n'.encode('utf-8'))
    archive = n.verify_archive(path, n.digest(path.read_bytes()), path.stat().st_size)
    record['return_receipt'] = {'status': 'SENT', 'destination_thread_id': 'legacy-parent'}
    old = copy.deepcopy(record['return_receipt'])
    with pytest.raises(ValueError, match='paired provider'):
        n.stage_native_receipt(record, archive)
    record.update(state='ARCHIVED', user_message_id='user', assistant_message_id='assistant', response_sha256=archive['sha256'])
    receipt = n.stage_native_receipt(record, archive)
    assert receipt['destination'] == ROUTE['parent_thread_id']
    assert n.stage_native_receipt(record, archive) is receipt
    n.finish_native_receipt(receipt, outcome)
    if outcome == 'REJECTED_BEFORE_DELIVERY':
        n.finish_native_receipt(receipt, 'SENT')
    else:
        with pytest.raises(ValueError, match='already delivered or uncertain'):
            n.finish_native_receipt(receipt, 'SENT')
    assert record['return_receipt'] == old
    path.write_bytes(b'different answer')
    with pytest.raises(ValueError, match='ARCHIVE_CONFLICT'):
        n.stage_native_receipt(record, archive)


def test_real_agentify_implementation_dry_run(tmp_path, preflight):
    dependency = Path(os.environ.get('HMASD_AGENTIFY_SOURCE', 'C:/Projects/agentify-desktop'))
    if not (dependency / 'review-transport.mjs').is_file():
        pytest.skip('local Agentify source required for the explicit end-to-end dry-run')
    exact = tmp_path / 'exact-handoff.json'
    exact.write_text(json.dumps(preflight), encoding='utf-8')
    result = subprocess.run(['node', str(FIXTURE / 'agentify-dry-run.mjs'), str(dependency), str(tmp_path), str(exact)],
                            check=True, text=True, capture_output=True, timeout=60)
    report = json.loads(result.stdout)
    assert report['sends'] == 2  # separate nonacceptance and uncertain-effect fixtures, never UI Send
    assert report['same_operation_after_repair'] and report['uncertain_observe_only']
    assert report['archive_exact'] and report['conflict_preserved']


@pytest.mark.parametrize('boundary', ['CONFLICT', 'NO_CURRENT_WORK'])
def test_nonarchive_boundary_returns_action_directly_without_claiming_completion(record, boundary):
    record.update(state='SEND_UNCERTAIN', native_state='OBSERVE')
    facts = dict(boundary=boundary, status='Direction remains ACTIVE; specific prerequisite unresolved',
                 evidence='Exact operation receipt at evidence.json', next_action='Retain same-request observation ownership.')
    receipt = n.stage_native_receipt(record, **facts)
    assert receipt['archive'] is None and receipt['destination'] == ROUTE['parent_thread_id']
    for text in (ROUTE['assignment'], facts['status'], facts['evidence'], facts['next_action']):
        assert text in receipt['message']
    assert record['state'] == 'SEND_UNCERTAIN' and record['native_state'] == 'OBSERVE'
    n.finish_native_receipt(receipt, 'SENT')
    assert n.stage_native_receipt(record, **facts) is receipt
    later = n.stage_native_receipt(record, **{**facts, 'evidence': 'Changed concrete evidence at second.json'})
    assert later is not receipt and record['native_receipt_history'] == [receipt]
    assert n.stage_native_receipt(record, **facts)['status'] == 'SENT'


def test_unchanged_wait_is_silent_and_missing_archive_allows_only_factual_return(record):
    before = copy.deepcopy(record)
    assert n.stage_native_receipt(record, boundary='UNCHANGED_WAIT') is None
    assert record == before
    with pytest.raises(ValueError, match='full archive'):
        n.stage_native_receipt(record)
    with pytest.raises(ValueError, match='status, evidence and next action'):
        n.stage_native_receipt(record, boundary='CONFLICT', status='Specific conflict')


def test_old_completed_native_receipt_is_not_duplicated(record, tmp_path):
    path = tmp_path / 'answer.md'
    path.write_bytes(b'full answer')
    archive = n.verify_archive(path, n.digest(path.read_bytes()), path.stat().st_size)
    record.update(state='ARCHIVED', user_message_id='user', assistant_message_id='assistant', response_sha256=archive['sha256'])
    old = {'message_key': '|'.join((record['request_id'], archive['sha256'], ROUTE['parent_thread_id'])), 'status': 'SENT'}
    record['native_receipt'] = old
    assert n.stage_native_receipt(record, archive) is old


def test_historical_delivery_outcome_updates_that_receipt_only(record):
    facts = dict(boundary='CONFLICT', status='Concrete prerequisite', evidence='first.json', next_action='Recover same request')
    first = n.stage_native_receipt(record, **facts)
    n.finish_native_receipt(first, 'REJECTED_BEFORE_DELIVERY')
    second = n.stage_native_receipt(record, **{**facts, 'evidence': 'second.json'})
    returned_first = n.stage_native_receipt(record, **facts)
    n.finish_native_receipt(returned_first, 'SENT')
    assert record['native_receipt_history'][0]['status'] == 'SENT'
    assert second['status'] == 'PENDING'
    with pytest.raises(ValueError, match='already delivered'):
        n.finish_native_receipt(returned_first, 'SENT')


@pytest.mark.parametrize('legacy', [False, True])
def test_complete_conflict_survives_intervening_nonarchive_boundary(record, tmp_path, legacy):
    first_path = tmp_path / 'first.md'
    first_path.write_bytes(b'first full answer')
    first = n.verify_archive(first_path, n.digest(first_path.read_bytes()), first_path.stat().st_size)
    record.update(state='ARCHIVED', user_message_id='user', assistant_message_id='assistant', response_sha256=first['sha256'])
    complete = n.stage_native_receipt(record, first)
    if legacy:
        complete.pop('boundary')
        complete['message_key'] = '|'.join((record['request_id'], first['sha256'], ROUTE['parent_thread_id']))
    n.finish_native_receipt(complete, 'SENT')
    n.stage_native_receipt(record, boundary='CONFLICT', status='Different candidate', evidence='conflict.json', next_action='Author reconciles candidates')
    second_path = tmp_path / 'second.md'
    second_path.write_bytes(b'second full answer')
    second = n.verify_archive(second_path, n.digest(second_path.read_bytes()), second_path.stat().st_size)
    record['response_sha256'] = second['sha256']
    before = copy.deepcopy(record)
    with pytest.raises(ValueError, match='identity conflict'):
        n.stage_native_receipt(record, second)
    assert record == before


def test_fixed_github_delivery_completes_despite_strict_pairing_failure(record, tmp_path):
    path = tmp_path / 'github-response.md'
    raw = b'Complete response for the fixed task, preserved exactly.\n'
    path.write_bytes(raw)
    archive = n.verify_archive(path, n.digest(raw), len(raw))
    commit = 'f' * 40
    response_path = record['github_delivery']['response_path']
    repository = record['task']['url'].split('/blob/')[0]
    response_url = f'{repository}/blob/{commit}/{response_path}'
    pairing = dict(commit_sha=commit, response_path=response_path, response_url=response_url,
                   blob_sha=n.hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest(),
                   comment_url=record['github_delivery']['issue_url'] + '#issuecomment-123',
                   comment_body=f"Fixed task: {record['task']['url']}\nDelivered: {response_url}")
    record.update(state='ARCHIVED', response_sha256=archive['sha256'], user_message_id=None,
                  assistant_message_id=None, github_response_pairing=pairing,
                  operation={'sendAttempted': True, 'error': {'code': 'USER_MESSAGE_CONTENT_MISMATCH'}})
    n.verify_github_pairing(record, archive, pairing)
    receipt = n.stage_native_receipt(record, archive)
    assert receipt['boundary'] == 'COMPLETE' and response_url in receipt['message']
    assert record['user_message_id'] is None and record['operation']['sendAttempted'] is True
    for field in ('commit_sha', 'response_path', 'response_url', 'blob_sha', 'comment_url', 'comment_body'):
        with pytest.raises(ValueError):
            n.verify_github_pairing(record, archive, {**pairing, field: 'wrong'})


def test_claim_keeps_observed_github_delivery_separate_from_frozen_scope(preflight, tmp_path):
    path = tmp_path / 'registry.json'
    observed = {'status': 'VERIFIED_GITHUB_FULL_RESPONSE', 'delivery_commit': 'f' * 40,
                'sha256': 'c' * 64, 'providerUserMessageId': None}
    prior = {'request_id': preflight['request_id'], 'github_delivery': observed, 'task': None}
    path.write_text(json.dumps({'bindings': {preflight['conversation_binding_key']: prior}}), encoding='utf-8')
    claimed = n.claim_binding(path, preflight)
    assert claimed['github_delivery'] == observed and claimed['task'] is None
    assert claimed['frozen_github_delivery'] == preflight['github_delivery']
    assert claimed['frozen_task'] == preflight['task']


def test_missing_native_message_tool_uses_direct_final_without_app_relay(record):
    receipt = n.stage_native_receipt(record, boundary='CONFLICT', status='Concrete missing fact',
        evidence='receipt.json', next_action='Parent reconciles same request', native_delivery='native_final')
    assert receipt['transport'] == 'native_final' and receipt['destination'] == ROUTE['parent_thread_id']
    n.finish_native_receipt(receipt, 'SENT')
    with pytest.raises(ValueError, match='never an app-task relay'):
        n.stage_native_receipt(record, boundary='CONFLICT', status='x', evidence='x', next_action='x', native_delivery='app_task')


@pytest.mark.parametrize('status', ['PENDING', 'REJECTED_BEFORE_DELIVERY', 'SENT', 'UNCERTAIN'])
def test_same_boundary_native_method_switch_preserves_actual_effect(record, status):
    facts = dict(boundary='CONFLICT', status='Known missing tool', evidence='capability.json', next_action='Direct parent final')
    receipt = n.stage_native_receipt(record, **facts)
    if status != 'PENDING':
        n.finish_native_receipt(receipt, status)
    if status == 'PENDING':
        with pytest.raises(ValueError, match='non-delivery evidence'):
            n.stage_native_receipt(record, **facts, native_delivery='native_final')
    returned = n.stage_native_receipt(record, **facts, native_delivery='native_final', verified_no_delivery=True)
    assert returned is receipt
    if status in {'SENT', 'UNCERTAIN'}:
        assert returned['transport'] == 'collaboration.send_message' and returned['status'] == status
    else:
        assert returned['transport'] == 'native_final'
        assert returned['delivery_method_history'] == [{'transport': 'collaboration.send_message', 'status': status}]

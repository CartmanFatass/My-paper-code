#!/usr/bin/env python3
"""Small native Transport boundary helpers; no browser, Send, scheduler or polling."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bind_conversation import _atomic_write
from transport_contract import canonical_packet_manifest, registry_lock, validate_parent_thread_id, validate_source_thread_id
from validate_request import validate


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def execution_route(parent: str, operator: str, assignment: str) -> dict:
    parent = validate_parent_thread_id(parent)
    operator = validate_source_thread_id(operator)
    if parent == operator or (operator.startswith('/root/') and operator.rsplit('/', 1)[0] != parent):
        raise ValueError('native operator must be a distinct direct child of the receipt parent')
    if not isinstance(assignment, str) or not assignment.strip():
        raise ValueError('the actual native assignment must be recorded')
    return dict(parent_thread_id=parent, operator_thread_id=operator, assignment=assignment)


def read_handoff(project_root: Path, sha: str, path: str, route: dict) -> dict:
    """Read fixed GitHub inputs on an existing conversation; first-binding uses its existing route."""
    if not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('handoff requires its full immutable Git SHA')
    if not path or path.startswith('/') or '\\' in path or ':' in path or '..' in path.split('/'):
        raise ValueError('handoff path must stay inside the repository')
    raw = subprocess.check_output(['git', 'show', f'{sha}:{path}'], cwd=project_root)
    h = json.loads(raw)
    req = h['transport_request']
    for key in ('request_id', 'caller_role', 'workflow_node', 'direction_id', 'direction_ids',
                'conversation_binding_key', 'requested_conversation_id',
                'source_thread_id', 'parent_thread_id', 'operator_thread_id',
                'dispatch_mode', 'provider_requirement'):
        if h.get(key) != req.get(key):
            raise ValueError(f'handoff/nested request mismatch: {key}')
    checked = validate(req, project_root, frozen_routing=True)
    if not checked['requested_conversation_id']:
        raise ValueError('first-binding uses the existing firstBinding route, not this recovery helper')
    with (project_root / '.codex/hmasd-transport.toml').open('rb') as stream:
        config = tomllib.load(stream)
    if (config.get('mode'), config.get('status'), config.get('backend'), config.get('model'),
        config.get('reasoning_effort')) != ('dm_native', 'active', 'agentify', 'gpt-5.6-luna', 'high'):
        raise ValueError('current execution requires active native Luna/high Agentify configuration')
    route = execution_route(route['parent_thread_id'], route['operator_thread_id'], route['assignment'])
    url = h.get('task_url', '')
    match = re.fullmatch(r'https://github\.com/([^/]+/[^/]+)/blob/([0-9a-f]{40})/(.+/TASK\.md)', url)
    if not match or match[1] != h.get('repository') or req.get('prompt', '').count(url) != 1:
        raise ValueError('provider prompt must contain its exact immutable TASK URL once')
    task = subprocess.check_output(['git', 'show', f'{match[2]}:{match[3]}'], cwd=project_root)
    delivery = h.get('github_delivery', {})
    response_path = delivery.get('response_path', '')
    if (h.get('delivery_mode') != 'github_delivery' or not delivery.get('branch')
            or not response_path.startswith('docs/') or '..' in Path(response_path).parts
            or not response_path.endswith('/archive/RESPONSE.md')):
        raise ValueError('fixed GitHub response scope is missing or invalid')
    for text in (delivery['branch'], response_path, delivery.get('issue_url', '')):
        if not text or text.encode('utf-8') not in task:
            raise ValueError('HANDOFF delivery scope differs from the fixed TASK')
    manifest = canonical_packet_manifest(req, checked)
    return dict(request_id=checked['request_id'], conversation_binding_key=checked['conversation_binding_key'],
                conversation_id=checked['requested_conversation_id'], prompt=req['prompt'],
                prompt_sha256=checked['prompt_sha256'], prompt_bytes=checked['prompt_bytes'],
                frozen_handoff=dict(sha=sha, path=path, sha256=digest(raw)),
                frozen_routing={k: req[k] for k in ('source_thread_id', 'parent_thread_id', 'operator_thread_id')},
                execution_route=route, manifest=manifest, github_delivery=delivery,
                task=dict(url=url, sha=match[2], path=match[3], sha256=digest(task), size_bytes=len(task)))


def verify_packet(preflight: dict, manifest_path: Path, prompt_path: Path) -> None:
    """Check the existing materialization, rather than creating another packet."""
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    expected = preflight['manifest']
    for key in ('request_id', 'workflow_node', 'conversation_binding_key', 'source_mode', 'references'):
        if manifest.get(key) != expected.get(key):
            raise ValueError(f'packet manifest mismatch: {key}')
    for key in ('sha256', 'bytes', 'canonical_filename'):
        if manifest.get('body', {}).get(key) != expected['body'][key]:
            raise ValueError(f'packet body mismatch: {key}')
    if prompt_path.name != expected['body']['canonical_filename'] or prompt_path.read_bytes() != preflight['prompt'].encode('utf-8'):
        raise ValueError('packet prompt path or exact bytes differ from HANDOFF')
    for declared in (manifest.get('body', {}).get('materialized_path'),
                     manifest.get('materialized_artifacts', {}).get('body')):
        if declared and Path(declared).resolve() != prompt_path.resolve():
            raise ValueError('packet materialized prompt path differs from inspected bytes')


def claim_binding(registry_path: Path, preflight: dict) -> dict:
    """One brief locked claim. A held request is never released by a timeout."""
    key = preflight['conversation_binding_key']
    with registry_lock(registry_path):
        registry = json.loads(registry_path.read_text(encoding='utf-8')) if registry_path.exists() else {}
        bindings = registry.setdefault('bindings', {})
        prior = bindings.get(key, {})
        if any(other_key != key and value.get('conversation_id') == preflight['conversation_id']
               for other_key, value in bindings.items()):
            raise ValueError('BINDING_BUSY: this conversation is already bound to another node')
        mirror = registry.get('directions', {}).get('portfolio', {}) if key == 'portfolio:cross_direction' else {}
        if mirror and mirror.get('request_id') != prior.get('request_id'):
            raise ValueError('BINDING_CONFLICT: legacy Portfolio mirror differs; reconcile without mutation')
        effect_fields = ('conversation_id', 'agentify_stable_key', 'prompt_sha256', 'state',
                         'send_click_count', 'send_evidence', 'user_message_id', 'assistant_message_id',
                         'response_sha256', 'archive', 'return_receipt', 'native_receipt', 'timestamps',
                         'send_reconciliation_history', 'execution_route', 'operation', 'github_delivery',
                         'github_response_pairing', 'frozen_github_delivery', 'frozen_task')
        if mirror and any(mirror.get(k) != prior.get(k) for k in effect_fields):
            raise ValueError('BINDING_CONFLICT: Portfolio mirror effect/receipt differs; preserve both records')
        same_request = prior.get('request_id') == preflight['request_id']
        if prior and not same_request and prior.get('state') != 'ARCHIVED':
            raise ValueError('BINDING_BUSY: another request owns this conversation')
        if prior.get('conversation_id') and prior['conversation_id'] != preflight['conversation_id']:
            raise ValueError('conversation generation mismatch; preserve its original binding')
        if same_request and prior.get('prompt_sha256') not in (None, preflight['prompt_sha256']):
            raise ValueError('same request has a different immutable prompt')
        if same_request and prior.get('frozen_handoff') and prior['frozen_handoff'] != preflight['frozen_handoff']:
            raise ValueError('same request has a different immutable HANDOFF')
        if same_request and prior.get('execution_route') and any(
                prior['execution_route'].get(k) != preflight['execution_route'][k]
                for k in ('parent_thread_id', 'operator_thread_id')):
            raise ValueError('BINDING_BUSY: another native executor owns this request')
        record = copy.deepcopy(prior) if same_request else {}
        if prior and not same_request:
            history = copy.deepcopy(prior.get('request_history', []))
            history.append({k: copy.deepcopy(v) for k, v in prior.items() if k != 'request_history'})
            record['request_history'] = history
            for field in ('agentify_stable_key', 'provider_url'):
                if field in prior:
                    record[field] = copy.deepcopy(prior[field])
        # Keep existing historical route/effect/receipt facts verbatim, even if a
        # legacy writer recorded incorrect metadata. Frozen Git bytes resolve it.
        record.update({k: copy.deepcopy(preflight[k]) for k in
                       ('request_id', 'conversation_binding_key', 'conversation_id', 'prompt_sha256',
                        'prompt_bytes', 'frozen_handoff', 'frozen_routing', 'execution_route', 'manifest')})
        record['frozen_github_delivery'] = copy.deepcopy(preflight['github_delivery'])
        record['frozen_task'] = copy.deepcopy(preflight['task'])
        record.setdefault('native_state', 'READY_UNSENT')
        record.setdefault('state', 'DIRECTION_VERIFIED')
        record.setdefault('provider_url', f"https://chatgpt.com/c/{preflight['conversation_id']}")
        bindings[key] = record
        if key == 'portfolio:cross_direction':
            registry.setdefault('directions', {})['portfolio'] = copy.deepcopy(record)
        _atomic_write(registry_path, registry)
        return record


def next_step(record: dict, operation: dict | None, page: dict | None = None,
              *, verified_nonacceptance: bool = False, accepted_turn: bool = False) -> dict:
    """Choose one action; a screenshot alone cannot prove the absence of a Send.

    `page` is the operator's reading of one screenshot or equivalent scoped UI
    sample, not an OCR result. The caller supplies only this request's operation.
    """
    if operation is not None:
        for field, expected in (('idempotencyKey', record['request_id']),
                                ('promptSha256', record['prompt_sha256']),
                                ('stableKey', record.get('agentify_stable_key') or record['conversation_binding_key']),
                                ('conversationId', record['conversation_id']),
                                ('conversationUrl', record['provider_url'])):
            if operation.get(field) != expected:
                raise ValueError(f'operation identity mismatch: {field}')
        if operation.get('provider') != 'chatgpt' or operation.get('productModel') not in {'GPT-6 Astra', 'Latest'} or operation.get('reasoningEffort') != 'Pro':
            raise ValueError('operation provider model/effort mismatch')
        original = record.get('operation')
        if original:
            for field in ('operationId', 'responsePath', 'productModel'):
                if operation.get(field) != original.get(field):
                    raise ValueError(f'operation identity mismatch: {field}')
    op = operation or {}
    prior_accepted = any(record.get(k) for k in ('user_message_id', 'assistant_message_id', 'response_sha256'))
    accepted = accepted_turn or prior_accepted or any(op.get(k) for k in
                 ('providerUserMessageId', 'providerAssistantMessageId', 'archive'))
    if accepted:
        return dict(state='OBSERVE', effect='ACCEPTED', action='ARCHIVE' if op.get('archive') else 'OBSERVE_ONLY')
    evidence = record.get('send_evidence') or {}
    times = record.get('timestamps') or {}
    possible_legacy_send = bool(record.get('send_click_count') or evidence.get('send_click_count')
                                or evidence.get('user_node_observed') or evidence.get('user_node_exact')
                                or evidence.get('observed_after_successful_send')
                                or any(times.get(k) for k in ('send_attempted_at', 'sent_at', 'generation_started_at'))
                                or any(item.get('outcome') == 'ACCEPTED'
                                       for item in record.get('send_reconciliation_history', []))
                                or record.get('state') in {'SEND_ATTEMPTED', 'SEND_UNCERTAIN', 'SEND_CONFIRMED',
                                  'SENT_INPUT_MISMATCH', 'WAITING_GENERATION', 'WAITING_HEARTBEAT', 'WAITING_UNKNOWN',
                                  'WAITING_TIMEOUT', 'NATURAL_COMPLETION', 'ARCHIVE_PENDING', 'ARCHIVED', 'ARCHIVE_CONFLICT'})
    if op.get('sendAttempted') is True or possible_legacy_send or not verified_nonacceptance:
        return dict(state='OBSERVE', effect='UNCERTAIN_EFFECT', action='OBSERVE_ONLY')
    if operation is not None and op.get('sendAttempted') is not False:
        return dict(state='OBSERVE', effect='UNCERTAIN_EFFECT', action='OBSERVE_ONLY')
    page = page or {}
    expected_url = record.get('provider_url') or f"https://chatgpt.com/c/{record['conversation_id']}"
    reasons = []
    for condition, reason in (
        (page.get('url') == expected_url, 'conversation'),
        (page.get('tab_key') == (record.get('agentify_stable_key') or record['conversation_binding_key']), 'tab_key'),
        (page.get('protected') is False, 'protected_tab'),
        (page.get('logged_in') is True and page.get('composer_ready') is True, 'page_ready'),
        (page.get('product_model') in {'GPT-6 Astra', 'Latest'} and page.get('reasoning_effort') == 'Pro', 'model_or_effort'),
        (page.get('current_generation_active') is False, 'current_generation'),
    ):
        if not condition:
            reasons.append(reason)
    return dict(state='READY_UNSENT', effect='VERIFIED_NONACCEPTANCE',
                action='REPAIR_PREFLIGHT' if reasons else 'SEND', reasons=reasons)


def observe_timeout(timeout_ms: int) -> int:
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int) or not 1000 <= timeout_ms <= 60000:
        raise ValueError('one observation call must be bounded to 1000..60000 ms')
    return timeout_ms


def verify_archive(path: Path, sha256: str, size_bytes: int) -> dict:
    if not path.is_absolute():
        raise ValueError('archive path must be absolute')
    raw = path.read_bytes()
    if not raw or digest(raw) != sha256 or len(raw) != size_bytes:
        raise ValueError('ARCHIVE_CONFLICT: exact archive hash/size does not match')
    return dict(path=str(path), sha256=sha256, size_bytes=size_bytes)


def verify_github_pairing(record: dict, archive: dict, pairing: dict) -> None:
    """Verify exact bytes against observed GitHub commit/comment facts, without inventing UI IDs."""
    task_url = (record.get('frozen_task') or record['task'])['url']
    scope = record.get('frozen_github_delivery') or record['github_delivery']
    repository_url = task_url.split('/blob/', 1)[0]
    commit = pairing.get('commit_sha', '')
    response_path = scope['response_path']
    url = f'{repository_url}/blob/{commit}/{response_path}'
    if (not re.fullmatch(r'[0-9a-f]{40}', commit) or pairing.get('response_url') != url
            or pairing.get('response_path') != response_path):
        raise ValueError('GitHub pairing must use the immutable scoped response')
    issue = scope['issue_url']
    if not re.fullmatch(re.escape(issue) + r'#issuecomment-[0-9]+', pairing.get('comment_url', '')):
        raise ValueError('GitHub pairing requires the specified delivery issue comment')
    if task_url not in pairing.get('comment_body', '') or url not in pairing.get('comment_body', ''):
        raise ValueError('GitHub delivery comment must pair the exact fixed TASK and response')
    verified = verify_archive(Path(archive['path']), archive['sha256'], archive['size_bytes'])
    raw = Path(verified['path']).read_bytes()
    blob = hashlib.sha1(f'blob {len(raw)}\0'.encode('ascii') + raw).hexdigest()
    if blob != pairing.get('blob_sha'):
        raise ValueError('GitHub response bytes differ from the observed Git blob')


def stage_native_receipt(record: dict, archive: dict | None = None, *, boundary: str = 'COMPLETE',
                         status: str = '', evidence: str = '', next_action: str = '',
                         native_delivery: str = 'collaboration.send_message',
                         verified_no_delivery: bool = False) -> dict | None:
    """One direct action message per changed boundary; unchanged waits produce none."""
    if boundary == 'UNCHANGED_WAIT':
        return None
    if boundary not in {'COMPLETE', 'CONFLICT', 'NO_CURRENT_WORK'}:
        raise ValueError('native return requires a concrete assignment boundary')
    if native_delivery not in {'collaboration.send_message', 'native_final'}:
        raise ValueError('return must use a direct native capability, never an app-task relay')
    verified = None
    if boundary == 'COMPLETE':
        if archive is None:
            raise ValueError('completion requires its full archive')
        verified = verify_archive(Path(archive['path']), archive['sha256'], archive['size_bytes'])
        paired_ids = record.get('user_message_id') and record.get('assistant_message_id')
        if record.get('github_response_pairing'):
            verify_github_pairing(record, archive, record['github_response_pairing'])
        elif not paired_ids:
            raise ValueError('receipt requires the archived full answer and its paired provider identities')
        if record.get('state') != 'ARCHIVED' or record.get('response_sha256') != archive['sha256']:
            raise ValueError('receipt requires the archived full answer and its paired provider identities')
        status = status or 'Complete full response archived'
        source = (record['github_response_pairing']['response_url'] if record.get('github_response_pairing')
                  else f"paired user={record['user_message_id']} assistant={record['assistant_message_id']}")
        evidence = evidence or f"{verified['path']} sha256={verified['sha256']} bytes={verified['size_bytes']}; source={source}"
        next_action = next_action or 'Author reads the complete response and performs conformance intake.'
    elif archive is not None:
        raise ValueError('noncompletion return must not imply a completed archive')
    if not all(isinstance(value, str) and value.strip() for value in (status, evidence, next_action)):
        raise ValueError('native action message requires status, evidence and next action')
    route = execution_route(**dict(parent=record['execution_route']['parent_thread_id'],
                                  operator=record['execution_route']['operator_thread_id'],
                                  assignment=record['execution_route']['assignment']))
    identity = archive['sha256'] if verified else digest((status + '\n' + evidence + '\n' + next_action).encode('utf-8'))
    key = '|'.join((record['request_id'], boundary, identity, route['parent_thread_id']))
    legacy_key = '|'.join((record['request_id'], identity, route['parent_thread_id'])) if verified else None
    existing = record.get('native_receipt')
    prior_receipts = ([existing] if existing else []) + record.get('native_receipt_history', [])
    if boundary == 'COMPLETE' and any(prior.get('boundary', 'COMPLETE') == 'COMPLETE'
            and prior.get('message_key') not in {key, legacy_key} for prior in prior_receipts):
        raise ValueError('native receipt identity conflict')
    for prior in prior_receipts:
        if prior.get('message_key') == key or (legacy_key and prior.get('message_key') == legacy_key):
            if prior.get('transport') and prior['transport'] != native_delivery and prior['status'] in {'PENDING', 'REJECTED_BEFORE_DELIVERY'}:
                if prior['status'] == 'PENDING' and verified_no_delivery is not True:
                    raise ValueError('receipt method change requires actual non-delivery evidence')
                prior.setdefault('delivery_method_history', []).append(dict(transport=prior['transport'], status=prior['status']))
                prior['transport'] = native_delivery
            return prior
    if existing:
        record.setdefault('native_receipt_history', []).append(copy.deepcopy(existing))
    message = (f"Assignment: {route['assignment']}. Status: {status}. "
               f"Request: {record['request_id']}; binding: {record['conversation_binding_key']}. "
               f"Evidence: {evidence}. Next: {next_action}")
    receipt = dict(message_key=key, destination=route['parent_thread_id'], status='PENDING',
                   boundary=boundary, archive=verified, message=message, transport=native_delivery)
    record['native_receipt'] = receipt
    if boundary == 'COMPLETE':
        record['native_state'] = 'RECEIPT'
    return receipt


def finish_native_receipt(receipt: dict, status: str) -> None:
    """Update the exact staged receipt object, including a retained historical return."""
    if status not in {'SENT', 'UNCERTAIN', 'REJECTED_BEFORE_DELIVERY'}:
        raise ValueError('receipt requires its actual native tool outcome')
    if not receipt.get('message_key'):
        raise ValueError('delivery outcome requires the exact staged receipt')
    if receipt['status'] not in {'PENDING', 'REJECTED_BEFORE_DELIVERY'}:
        raise ValueError('receipt already delivered or uncertain; reconcile without repeating it')
    receipt['status'] = status


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[4])
    p.add_argument('--handoff-sha', required=True)
    p.add_argument('--handoff-path', required=True)
    p.add_argument('--parent', required=True)
    p.add_argument('--operator', required=True)
    p.add_argument('--assignment', required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--manifest', type=Path)
    p.add_argument('--prompt', type=Path)
    p.add_argument('--claim-registry', type=Path)
    args = p.parse_args()
    result = read_handoff(args.project_root, args.handoff_sha, args.handoff_path,
                          execution_route(args.parent, args.operator, args.assignment))
    if bool(args.manifest) != bool(args.prompt):
        raise ValueError('existing packet requires both --manifest and --prompt')
    if args.manifest:
        verify_packet(result, args.manifest, args.prompt)
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if args.out.exists() and args.out.read_bytes() != raw:
        raise ValueError('preflight artifact exists with different bytes')
    if args.claim_registry:
        with Path('C:/Projects/HMASD/.codex/hmasd-transport.toml').open('rb') as stream:
            live = tomllib.load(stream)
        if args.claim_registry.resolve() != Path(live['registry_path']).resolve():
            raise ValueError('claim must use the live shared registry path')
        claim_binding(args.claim_registry, result)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(raw)
    print(json.dumps(dict(valid=True, request_id=result['request_id'], prompt_sha256=result['prompt_sha256'],
                         parent=result['execution_route']['parent_thread_id'], out=str(args.out))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

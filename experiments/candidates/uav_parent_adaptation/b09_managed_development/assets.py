"""Fail-closed bound inputs and immutable rollout-group/checkpoint identities."""
from pathlib import Path

import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.learning import Head
from experiments.candidates.uav_local_history.b01.study import file_identity
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.study import load_asset
from .contract import ASSETS


def state_copy(model):
    return {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}


def preflight_inputs(input_dir, bindings):
    """Verify ALL physical files before any model creation or environment query."""
    result = {}
    for name in ('S', 'CAL_all', 'CONT_all'):
        path = Path(input_dir).resolve() / (name + '.pt')
        if not path.is_file():
            raise FileNotFoundError('required staged B09 input is absent: ' + str(path))
        identity = file_identity(path)
        for key in ('bytes', 'sha256'):
            if identity[key] != bindings[name][key]:
                raise ValueError('staged B09 input identity mismatch: ' + name + '/' + key)
        result[name] = dict(identity, path=str(path), state_sha256=bindings[name]['state_sha256'])
    return result


def load_inputs(input_dir, bindings=ASSETS):
    identities = preflight_inputs(input_dir, bindings)
    actor, _ = load_asset(identities['S']['path'], bindings['S'])
    heads = {}
    for name in ('CAL_all', 'CONT_all'):
        kind = name.split('_')[0]
        saved = torch.load(identities[name]['path'], map_location='cpu', weights_only=True)
        if (saved.get('schema') != 'uav_fleet_adaptation.b05.head.v1'
                or saved.get('endpoint') != kind or saved.get('lineage') != 0
                or saved.get('original_student_sha256') != bindings['S']['state_sha256']
                or saved.get('dtype') != 'float32' or saved.get('hidden_size') != 128
                or saved.get('output_size') != 27
                or saved.get('state_sha256') != bindings[name]['state_sha256']
                or state_digest(saved['state_dict']) != bindings[name]['state_sha256']):
            raise ValueError('original transfer head metadata/tensor identity mismatch: ' + name)
        head = Head(kind)
        head.load_state_dict(saved['state_dict'], strict=True)
        head.eval().requires_grad_(False)
        if (state_digest(head.state_dict()) != bindings[name]['state_sha256']
                or any(p.dtype != torch.float32 or p.device.type != 'cpu' for p in head.parameters())):
            raise ValueError('transfer head loading changed its bound numerical contract')
        heads[name] = head
    return actor, heads, identities


def save_checkpoint(out, relative, *, kind, head, critic=None, optimizers=None, metadata=None):
    path = Path(out) / relative
    if path.exists():
        raise FileExistsError('immutable B09 checkpoint exists: ' + str(path))
    state = state_copy(head)
    payload = dict(schema='uav_parent_adaptation.b09.checkpoint.v1', kind=kind,
                   head_state=state, head_sha256=state_digest(state), metadata=dict(metadata or {}))
    if critic is not None:
        payload['critic_state'] = state_copy(critic)
        payload['critic_sha256'] = state_digest(payload['critic_state'])
    if optimizers is not None:
        payload['optimizers'] = [optimizer.state_dict() for optimizer in optimizers]
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)
    return dict(file_identity(path), path=str(path.relative_to(out)), kind=kind,
                head_sha256=payload['head_sha256'], critic_sha256=payload.get('critic_sha256'),
                metadata=payload['metadata'])


def load_head_checkpoint(path, record):
    identity = file_identity(path)
    if any(identity[key] != record[key] for key in ('bytes', 'sha256')):
        raise ValueError('checkpoint file identity changed')
    payload = torch.load(path, map_location='cpu', weights_only=True)
    if (payload.get('schema') != 'uav_parent_adaptation.b09.checkpoint.v1'
            or payload.get('kind') != record['kind'] or payload.get('metadata') != record['metadata']
            or payload.get('head_sha256') != record['head_sha256']
            or state_digest(payload['head_state']) != record['head_sha256']):
        raise ValueError('checkpoint head provenance differs')
    if record.get('critic_sha256') is not None:
        if (payload.get('critic_sha256') != record['critic_sha256']
                or state_digest(payload['critic_state']) != record['critic_sha256']):
            raise ValueError('checkpoint critic provenance differs')
    head = Head(record['kind'])
    head.load_state_dict(payload['head_state'], strict=True)
    head.eval().requires_grad_(False)
    return head, payload

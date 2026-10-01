"""Digest-bound original P0 consumption; no checkpoint search or substitution."""
from pathlib import Path

import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_digest
from experiments.candidates.uav_local_history.b01.study import file_identity
from .contract import FROZEN, P0_BINDING


def checked_path(root, relative, binding):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('artifact escaped output root')
    identity = file_identity(path)
    if any(identity[key] != binding[key] for key in ('bytes', 'sha256')):
        raise ValueError('artifact identity changed: ' + str(relative))
    return path


def load_parent(path):
    path = Path(path).resolve()
    identity = file_identity(path)
    if any(identity[key] != P0_BINDING[key] for key in ('bytes', 'sha256')):
        raise ValueError('original P0 file differs from the frozen artifact')
    saved = torch.load(path, map_location='cpu', weights_only=True)
    if (saved.get('endpoint') != 'S' or saved.get('launch_sha') != P0_BINDING['launch_sha']
            or saved.get('architecture') != [114, 128, 128, 27] or saved.get('activation') != 'relu'
            or saved.get('dtype') != 'float32' or saved.get('optimizer_steps') != 8000
            or saved.get('state_sha256') != P0_BINDING['state_sha256']
            or state_digest(saved['state_dict']) != P0_BINDING['state_sha256']):
        raise ValueError('original P0 checkpoint contract changed')
    actor = make_student(FROZEN.constructor_seed)
    actor.load_state_dict(saved['state_dict'], strict=True)
    actor.eval().requires_grad_(False)
    if (state_digest(actor.state_dict()) != P0_BINDING['state_sha256']
            or any(value.dtype != torch.float32 or not torch.isfinite(value).all() for value in actor.state_dict().values())):
        raise ValueError('invalid loaded original FP32 P0')
    return actor, dict(identity, canonical_path=P0_BINDING['path'], canonical_node='wsl_4070',
                       source_launch_sha=P0_BINDING['launch_sha'], state_sha256=P0_BINDING['state_sha256'])

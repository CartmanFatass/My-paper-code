"""Strict full-policy U continuation of the unchanged original B-final parent."""

import copy
import hashlib
import io
import os
from pathlib import Path
import tempfile

import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01 import model as cadc
from experiments.candidates.uav_parent_adaptation.b01 import model as b01

from .protocol import PARENT_SOURCE, masters

SCHEMA = "uav_parent_adaptation.b02.checkpoint.v1"
DIRECTION = "uav_parent_adaptation"
INPUT_SIZE, CRITIC_SIZE = 171, 451
Actor, Critic = cadc.Actor, cadc.Critic
_META_KEYS = {"schema", "direction", "lineage", "stage", "endpoint", "master", "launch_sha",
              "input_size", "critic_size", "parent_source", "inherited_sha256", "parent"}
_BINDING_KEYS = _META_KEYS | {"tensors", "parameter_groups", "sha256", "bytes", "path"}
_SHAPES = b01._tensor_shapes("B")
_GROUP_KEYS = {
    "actor_encoder": ["actor." + key for key in _SHAPES["actor"] if key.startswith("encoder.")],
    "actor_recurrent": ["actor." + key for key in _SHAPES["actor"] if key.startswith("gru.")],
    "actor_mean": ["actor.mean.weight", "actor.mean.bias"],
    "actor_log_std": ["actor.log_std"],
    "critic": ["critic." + key for key in _SHAPES["critic"]],
}
state_tensor_bindings = b01.state_tensor_bindings


def _metadata(lineage, endpoint, launch_sha, parent):
    master = masters(lineage)["U"]
    if endpoint not in ("initial", "final") or not b01._hex(launch_sha, 40) or launch_sha == PARENT_SOURCE:
        raise ValueError("invalid U endpoint/new launch source")
    b01._validate_binding(parent, lineage=lineage, stage="B", endpoint="final", launch_sha=PARENT_SOURCE)
    return dict(schema=SCHEMA, direction=DIRECTION, lineage=lineage, stage="U", endpoint=endpoint,
                master=master, launch_sha=launch_sha, input_size=INPUT_SIZE, critic_size=CRITIC_SIZE,
                parent_source=PARENT_SOURCE, inherited_sha256=parent["sha256"], parent=copy.deepcopy(parent))


def _validate_binding(binding, *, lineage, endpoint, launch_sha):
    if not isinstance(binding, dict) or set(binding) != _BINDING_KEYS:
        raise ValueError("U binding fields mismatch")
    metadata = _metadata(lineage, endpoint, launch_sha, binding["parent"])
    if (any(type(binding[key]) is not int for key in ("lineage", "master", "input_size", "critic_size"))
            or any(binding[key] != value for key, value in metadata.items())):
        raise ValueError("U binding metadata/source mismatch")
    if (not b01._hex(binding["sha256"], 64) or type(binding["bytes"]) is not int
            or binding["bytes"] <= 0 or not isinstance(binding["path"], str) or not binding["path"]):
        raise ValueError("U binding file identity mismatch")
    tensors = binding["tensors"]
    if not isinstance(tensors, dict) or set(tensors) != set(_SHAPES):
        raise ValueError("U tensor groups mismatch")
    for group, shapes in _SHAPES.items():
        manifest = tensors[group]
        if not isinstance(manifest, dict) or set(manifest) != set(shapes):
            raise ValueError("U tensor keys mismatch")
        for key, shape in shapes.items():
            item = manifest[key]
            if (not isinstance(item, dict) or set(item) != {"shape", "dtype", "sha256"}
                    or not isinstance(item["shape"], list)
                    or any(type(size) is not int for size in item["shape"])
                    or item["shape"] != shape or item["dtype"] != "torch.float32"
                    or not b01._hex(item["sha256"], 64)):
                raise ValueError("U tensor shape/dtype/hash contract mismatch")
    if endpoint == "initial" and tensors != binding["parent"]["tensors"]:
        raise ValueError("U initial tensor identity differs from P")
    groups = binding["parameter_groups"]
    if not isinstance(groups, dict) or set(groups) != set(_GROUP_KEYS):
        raise ValueError("U parameter group keys mismatch")
    for name, keys in _GROUP_KEYS.items():
        count = 0
        for key in keys:
            module, tensor = key.split(".", 1)
            size = 1
            for dimension in _SHAPES[module][tensor]:
                size *= dimension
            count += size
        item = groups[name]
        if (not isinstance(item, dict) or set(item) != {"keys", "parameters", "shape", "dtype", "sha256"}
                or item["keys"] != keys or type(item["parameters"]) is not int
                or item["parameters"] != count or item["shape"] != [count]
                or not isinstance(item["shape"], list) or type(item["shape"][0]) is not int
                or item["dtype"] != "torch.float32" or not b01._hex(item["sha256"], 64)):
            raise ValueError("U parameter group contract mismatch")
    return metadata


def _group_vectors(state):
    result = {}
    for name, keys in _GROUP_KEYS.items():
        tensors = []
        for key in keys:
            group, parameter = key.split(".", 1)
            tensors.append(state[group][parameter].detach().flatten())
        result[name] = torch.cat(tensors).clone()
    return result


def _state_tensor_manifests(state):
    manifests = {}
    for group, shapes in _SHAPES.items():
        values = state.get(group)
        manifest = state_tensor_bindings(values)
        if set(manifest) != set(shapes) or any(manifest[key]["shape"] != shape
                                              for key, shape in shapes.items()):
            raise ValueError("U state tensor contract mismatch")
        manifests[group] = manifest
    return manifests


def state_group_snapshot(state):
    """Five flat CPU clone groups from deserialized state, without construction."""
    _state_tensor_manifests(state)
    return _group_vectors(state)


def _group_bindings(state):
    return {name: dict(keys=list(_GROUP_KEYS[name]), parameters=tensor.numel(),
                       **state_tensor_bindings({name: tensor})[name])
            for name, tensor in _group_vectors(state).items()}


def build_u(master, checkpoint_bytes, binding, *, lineage, launch_sha):
    _metadata(lineage, "initial", launch_sha, binding)
    if type(master) is not int or master != masters(lineage)["U"]:
        raise ValueError("U master mismatch")
    state = b01.read_checkpoint(checkpoint_bytes, binding, lineage=lineage, stage="B",
                                endpoint="final", launch_sha=PARENT_SOURCE)
    actor, critic = cadc.build_arm(master, "RR")
    actor.load_state_dict(state["actor"], strict=True)
    critic.load_state_dict(state["critic"], strict=True)
    actor.requires_grad_(True)
    critic.requires_grad_(True)
    return actor, critic


def save_checkpoint(path, actor, critic, *, lineage, endpoint, master, launch_sha, parent):
    metadata = _metadata(lineage, endpoint, launch_sha, parent)
    if type(master) is not int or master != metadata["master"]:
        raise ValueError("U checkpoint master mismatch")
    tensors = {"actor": actor.state_dict(), "critic": critic.state_dict()}
    manifests = _state_tensor_manifests(tensors)
    state = {**metadata, **{group: {key: value.detach().clone() for key, value in values.items()}
                            for group, values in tensors.items()}}
    buffer = io.BytesIO()
    torch.save(state, buffer)
    content = buffer.getvalue()
    path = Path(path)
    binding = dict(**metadata, tensors=manifests, parameter_groups=_group_bindings(state),
                   sha256=hashlib.sha256(content).hexdigest(), bytes=len(content), path=str(path))
    _validate_binding(binding, lineage=lineage, endpoint=endpoint, launch_sha=launch_sha)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return binding


def read_checkpoint(checkpoint_bytes, binding, *, lineage, endpoint, launch_sha):
    metadata = _validate_binding(binding, lineage=lineage, endpoint=endpoint, launch_sha=launch_sha)
    if (not isinstance(checkpoint_bytes, bytes) or len(checkpoint_bytes) != binding["bytes"]
            or hashlib.sha256(checkpoint_bytes).hexdigest() != binding["sha256"]):
        raise ValueError("U checkpoint file digest/bytes mismatch")
    try:
        def cpu_storage(storage, location):
            if location != "cpu":
                raise ValueError("U checkpoint storage must be CPU")
            return storage

        state = torch.load(io.BytesIO(checkpoint_bytes), map_location=cpu_storage, weights_only=True)
    except Exception as error:
        raise ValueError("invalid U checkpoint serialization") from error
    if (not isinstance(state, dict) or set(state) != _META_KEYS | {"actor", "critic"}
            or any(type(state[key]) is not int for key in ("lineage", "master", "input_size", "critic_size"))
            or any(state[key] != value for key, value in metadata.items())):
        raise ValueError("U checkpoint metadata/source mismatch")
    for group in ("actor", "critic"):
        if state_tensor_bindings(state[group]) != binding["tensors"][group]:
            raise ValueError("U checkpoint tensor identity mismatch")
    if _group_bindings(state) != binding["parameter_groups"]:
        raise ValueError("U checkpoint parameter group identity mismatch")
    return state


def load_evaluation(checkpoint_bytes, binding, *, lineage, endpoint, launch_sha):
    state = read_checkpoint(checkpoint_bytes, binding, lineage=lineage, endpoint=endpoint, launch_sha=launch_sha)
    actor, critic = cadc.build_arm(state["master"], "RR")
    actor.load_state_dict(state["actor"], strict=True)
    critic.load_state_dict(state["critic"], strict=True)
    actor.requires_grad_(False)
    critic.requires_grad_(False)
    actor.eval()
    critic.eval()
    return actor, critic


def snapshot(actor, critic):
    return state_group_snapshot({"actor": actor.state_dict(), "critic": critic.state_dict()})


def exposure(initial, actor, critic):
    current = snapshot(actor, critic)
    if initial.keys() != current.keys():
        raise ValueError("U exposure parameter groups changed")
    result = {}
    for name, before in initial.items():
        after = current[name]
        if before.shape != after.shape or before.dtype != torch.float32 or before.device.type != "cpu":
            raise ValueError("U exposure parameter group shape/dtype/device mismatch")
        displacement, norm = float((after - before).norm()), float(before.norm())
        result[name] = dict(parameters=before.numel(), initial_norm=norm, final_norm=float(after.norm()),
                            displacement=displacement, relative_displacement=displacement / norm if norm else None)
    return result

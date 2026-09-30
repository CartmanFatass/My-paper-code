"""Own-lineage C→B parents and unchanged B06 bounded adaptation laws."""

import copy
import hashlib
import io
import os
from pathlib import Path
import re
import tempfile

import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01 import model as cadc
from experiments.candidates.uav_message_content.b06 import model as b06

from .protocol import masters

SCHEMA = "uav_parent_adaptation.b01.checkpoint.v1"
DIRECTION = "uav_parent_adaptation"
ORIGINAL_C_SOURCE = "b2a422088a20235e760e3aaebbc74f35236a4e82"
ORIGINAL_B_SOURCE = "02ede8a4a75cc83e6e18d8b6619f1cfa84bc8d92"
ACTOR_SIZE, CRITIC_SIZE = b06.ACTOR_SIZE, b06.CRITIC_SIZE
CORRECTION_BOUND = b06.CORRECTION_BOUND
BaseActor, BaseCritic = cadc.Actor, cadc.Critic
CalibrationActor, ResidualActor, Critic = b06.CalibrationActor, b06.ResidualActor, b06.Critic
motion_terms = b06.motion_terms
SCALAR_ACTOR_COLUMNS = tuple(126 + 10 * s for s in range(5))
SCALAR_CRITIC_COLUMNS = tuple(154 + 63 * i + 10 * s for i in range(5) for s in range(5))
_META_KEYS = {"schema", "direction", "lineage", "stage", "endpoint", "master", "launch_sha",
              "input_size", "critic_size", "original_c_source", "original_b_source",
              "inherited_sha256", "parent"}
_BINDING_KEYS = _META_KEYS | {"tensors", "sha256", "bytes", "path"}


def _master(lineage, stage):
    if type(lineage) is not int or lineage not in (1, 2, 3) or stage not in ("C", "B", "K", "D"):
        raise ValueError("invalid fixed lineage/stage")
    return masters(lineage)[stage]


def _hex(value, length):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None


def _construct(master, stage):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(100000 * master + 11)
        if stage in ("C", "B"):
            return cadc.build_arm(master, "RR")
        # B06's critic-first order is part of the matched K/D constructor law.
        critic = Critic()
        actor = CalibrationActor() if stage == "K" else ResidualActor()
    return actor, critic


def build_c(master):
    if type(master) is not int or master not in tuple(_master(i, "C") for i in (1, 2, 3)):
        raise ValueError("invalid fixed C master")
    return cadc.build_arm(master, "RR")


def _metadata(lineage, stage, endpoint, launch_sha, parent):
    master = _master(lineage, stage)
    if endpoint not in ("initial", "final") or not _hex(launch_sha, 40):
        raise ValueError("invalid endpoint/launch source")
    if stage == "C":
        if parent is not None:
            raise ValueError("C has no inherited parent")
    else:
        _validate_binding(parent, lineage=lineage, stage="C" if stage == "B" else "B",
                          endpoint="final", launch_sha=launch_sha)
    return dict(schema=SCHEMA, direction=DIRECTION, lineage=lineage, stage=stage,
                endpoint=endpoint, master=master, launch_sha=launch_sha,
                input_size=171 if stage in ("C", "B") else ACTOR_SIZE,
                critic_size=451 if stage in ("C", "B") else CRITIC_SIZE,
                original_c_source=ORIGINAL_C_SOURCE, original_b_source=ORIGINAL_B_SOURCE,
                inherited_sha256=None if parent is None else parent["sha256"],
                parent=copy.deepcopy(parent))


def state_tensor_bindings(state):
    """Hash exact CPU float32 tensor bytes, without casting or normalizing."""
    if not isinstance(state, dict):
        raise ValueError("tensor state must be a dictionary")
    result = {}
    for key, tensor in state.items():
        if (not isinstance(key, str) or not isinstance(tensor, torch.Tensor)
                or tensor.device.type != "cpu" or tensor.dtype != torch.float32
                or tensor.layout != torch.strided or not torch.isfinite(tensor).all()):
            raise ValueError("checkpoint tensors must be finite CPU float32")
        result[key] = dict(shape=list(tensor.shape), dtype="torch.float32",
                           sha256=hashlib.sha256(tensor.detach().contiguous().numpy().tobytes()).hexdigest())
    return result


def _tensor_shapes(stage):
    """Fixed inherited architecture, available to the reader without construction."""
    actor = {"log_std": [3], "encoder.raw.weight": [64, 171], "encoder.raw.bias": [64],
             "encoder.hidden.weight": [16, 171], "encoder.hidden.bias": [16],
             "encoder.context.weight": [64, 16], "gru.weight_ih_l0": [192, 64],
             "gru.weight_hh_l0": [192, 64], "gru.bias_ih_l0": [192],
             "gru.bias_hh_l0": [192], "mean.weight": [3, 64], "mean.bias": [3]}
    critic = {"network.0.weight": [128, 451], "network.0.bias": [128],
              "network.2.weight": [128, 128], "network.2.bias": [128],
              "network.4.weight": [1, 128], "network.4.bias": [1]}
    if stage in ("K", "D"):
        actor = {"base." + key: shape for key, shape in actor.items()}
        if stage == "K":
            actor["b"] = [3]
        else:
            actor.update({"residual_hidden.weight": [64, 250], "residual_hidden.bias": [64],
                          "residual_output.weight": [3, 64], "residual_output.bias": [3]})
        critic["forecast_projection.weight"] = [128, 75]
    return {"actor": actor, "critic": critic}


def _validate_binding(binding, *, lineage, stage, endpoint, launch_sha):
    if not isinstance(binding, dict) or set(binding) != _BINDING_KEYS:
        raise ValueError("checkpoint binding fields mismatch")
    expected = _metadata(lineage, stage, endpoint, launch_sha, binding["parent"])
    # Reject bools masquerading as integer identities in both representations.
    if any(type(binding[key]) is not int for key in ("lineage", "master", "input_size", "critic_size")):
        raise ValueError("checkpoint binding metadata types mismatch")
    if any(binding[key] != value for key, value in expected.items()):
        raise ValueError("checkpoint binding metadata/source mismatch")
    if (not _hex(binding["sha256"], 64) or type(binding["bytes"]) is not int
            or binding["bytes"] <= 0 or not isinstance(binding["path"], str) or not binding["path"]):
        raise ValueError("checkpoint binding file identity mismatch")
    templates = _tensor_shapes(stage)
    manifests = binding["tensors"]
    if not isinstance(manifests, dict) or set(manifests) != set(templates):
        raise ValueError("checkpoint tensor groups mismatch")
    for group, template in templates.items():
        manifest = manifests[group]
        if not isinstance(manifest, dict) or set(manifest) != set(template):
            raise ValueError("checkpoint tensor keys mismatch")
        for key, shape in template.items():
            item = manifest[key]
            if (not isinstance(item, dict) or set(item) != {"shape", "dtype", "sha256"}
                    or not isinstance(item["shape"], list)
                    or any(type(size) is not int for size in item["shape"])
                    or item["shape"] != shape or item["dtype"] != "torch.float32"
                    or not _hex(item["sha256"], 64)):
                raise ValueError("checkpoint tensor shape/dtype/digest contract mismatch")
    return expected


def save_checkpoint(path, actor, critic, *, lineage, stage, endpoint, master, launch_sha, parent=None):
    metadata = _metadata(lineage, stage, endpoint, launch_sha, parent)
    if type(master) is not int or master != metadata["master"]:
        raise ValueError("checkpoint master mismatch")
    # Clone so subsequent training cannot mutate the state being serialized.
    tensors = {"actor": actor.state_dict(), "critic": critic.state_dict()}
    manifests = {group: state_tensor_bindings(values) for group, values in tensors.items()}
    state = {**metadata, **{group: {key: value.detach().clone() for key, value in values.items()}
                            for group, values in tensors.items()}}
    buffer = io.BytesIO()
    torch.save(state, buffer)
    content = buffer.getvalue()
    path = Path(path)
    binding = dict(**metadata, tensors=manifests, sha256=hashlib.sha256(content).hexdigest(),
                   bytes=len(content), path=str(path))
    _validate_binding(binding, lineage=lineage, stage=stage, endpoint=endpoint, launch_sha=launch_sha)
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


def read_checkpoint(checkpoint_bytes, binding, *, lineage, stage, endpoint, launch_sha):
    metadata = _validate_binding(binding, lineage=lineage, stage=stage, endpoint=endpoint,
                                 launch_sha=launch_sha)
    if (not isinstance(checkpoint_bytes, bytes) or len(checkpoint_bytes) != binding["bytes"]
            or hashlib.sha256(checkpoint_bytes).hexdigest() != binding["sha256"]):
        raise ValueError("checkpoint file digest/bytes mismatch")
    try:
        def cpu_storage(storage, location):
            if location != "cpu":
                raise ValueError("checkpoint storage must be CPU")
            return storage

        state = torch.load(io.BytesIO(checkpoint_bytes), map_location=cpu_storage, weights_only=True)
    except Exception as error:
        raise ValueError("invalid checkpoint serialization") from error
    if (not isinstance(state, dict) or set(state) != _META_KEYS | {"actor", "critic"}
            or any(type(state[key]) is not int for key in ("lineage", "master", "input_size", "critic_size"))
            or any(state[key] != value for key, value in metadata.items())):
        raise ValueError("checkpoint metadata/source mismatch")
    for group in ("actor", "critic"):
        if state_tensor_bindings(state[group]) != binding["tensors"][group]:
            raise ValueError("checkpoint tensor identity mismatch")
    return state


def build_b(master, checkpoint_bytes, binding, *, lineage, launch_sha):
    if type(master) is not int or master != _master(lineage, "B"):
        raise ValueError("invalid fixed B master")
    state = read_checkpoint(checkpoint_bytes, binding, lineage=lineage, stage="C",
                            endpoint="final", launch_sha=launch_sha)
    actor, critic = _construct(master, "B")
    actor.load_state_dict(state["actor"], strict=True)
    critic.load_state_dict(state["critic"], strict=True)
    with torch.no_grad():
        actor.encoder.raw.weight[:, SCALAR_ACTOR_COLUMNS] = 0
        actor.encoder.hidden.weight[:, SCALAR_ACTOR_COLUMNS] = 0
        critic.network[0].weight[:, SCALAR_CRITIC_COLUMNS] = 0
    return actor, critic


def build_adaptation(master, arm, checkpoint_bytes, binding, *, lineage, launch_sha):
    if arm not in ("K", "D") or type(master) is not int or master != _master(lineage, arm):
        raise ValueError("invalid fixed adaptation cell")
    state = read_checkpoint(checkpoint_bytes, binding, lineage=lineage, stage="B",
                            endpoint="final", launch_sha=launch_sha)
    actor, critic = _construct(master, arm)
    actor.base.load_state_dict(state["actor"], strict=True)
    actor.base.requires_grad_(False)
    critic.network.load_state_dict({key.removeprefix("network."): value
                                    for key, value in state["critic"].items()}, strict=True)
    return actor, critic


def load_evaluation(checkpoint_bytes, binding, *, lineage, stage, endpoint, launch_sha):
    if (stage, endpoint) not in (("C", "initial"), ("B", "final"), ("K", "final"), ("D", "final")):
        raise ValueError("invalid fixed evaluation endpoint")
    state = read_checkpoint(checkpoint_bytes, binding, lineage=lineage, stage=stage,
                            endpoint=endpoint, launch_sha=launch_sha)
    actor, critic = _construct(state["master"], stage)
    actor.load_state_dict(state["actor"], strict=True)
    critic.load_state_dict(state["critic"], strict=True)
    actor.requires_grad_(False)
    critic.requires_grad_(False)
    actor.eval()
    critic.eval()
    return actor, critic


def snapshot(actor, critic):
    if isinstance(actor, (CalibrationActor, ResidualActor)):
        return b06.parameter_snapshot(actor, critic)
    return cadc.snapshot(actor, critic)


def exposure(initial, actor, critic):
    if isinstance(actor, (CalibrationActor, ResidualActor)):
        return b06.exposure(initial, actor, critic)
    return cadc.exposure(initial, actor, critic)

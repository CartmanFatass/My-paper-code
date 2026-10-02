"""Pure exact cold handshake; no labels, numerical imports or new scientific query."""
from __future__ import annotations
import hashlib
from . import contract as c


def digest(value):
    return hashlib.sha256(c.encoded(value)).hexdigest()


def make(record, features, gpu_choices):
    # Called only inside the sealed final endpoint worker, from its existing Bank.load.
    return {"identity": record["identity"], "feature_sha256": digest(features),
            "construction_sha256": digest(record["construction"]),
            "raw_layout_sha256": [digest(layout) for layout in record["layouts_xyz"]],
            "gpu_choices": dict(gpu_choices)}


def verify(decision, reference, *, world, arm, launch_sha, input_sha256):
    """Same exact fields as B04 world_gate, serialized without copying bank geometry/labels.

    Original reader.world_gate subsequently checks original records, independently of this
    parent commitment adapter. Digests use original encoded normalization for ordinary data.
    """
    def exact(left, right, name):
        if c.encoded(left) != c.encoded(right):
            raise AssertionError("cold commitment mismatch: " + name)
    exact(decision["world"], world, "world")
    exact(decision["arm"], arm, "arm")
    exact(decision["source_sha"], launch_sha, "consumer source")
    exact(decision["input_sha256"], input_sha256, "scientific input")
    identity = reference["identity"]
    for key in ("world", "initial_positions_xyz", "user_positions_xy", "bs_xyz"):
        exact(decision[key], identity[key], key)
    exact(decision["construction_identity"], identity, "constructor world/RNG/agents/mask")
    reset = decision["reset_identity"]
    for key in ("native_rng_sha256", "agents", "transmitter_mask"):
        exact(reset[key], identity[key], "execution reset " + key)
    exact(reset["state"]["current_step"], 0, "full reset step")
    exact(reset["state"]["positions_xyz"], identity["initial_positions_xyz"], "full reset initial pose")
    if arm != "P":
        exact(decision["feature_sha256"], reference["feature_sha256"], "complete raw features")
        exact(decision["construction_sha256"], reference["construction_sha256"], "construction")
        index = decision["chosen_raw_index"]
        if type(index) is not int or not 0 <= index < len(reference["raw_layout_sha256"]):
            raise AssertionError("cold selected raw address")
        exact(digest(decision["positions_xyz"]), reference["raw_layout_sha256"][index], "chosen original row")
    if arm in reference["gpu_choices"]:
        exact(decision["chosen_raw_index"], reference["gpu_choices"][arm], "frozen GPU endpoint choice")

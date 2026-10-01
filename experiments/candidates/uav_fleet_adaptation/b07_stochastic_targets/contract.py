"""Frozen B07 identities, exposure, source bindings and random addresses."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from experiments.candidates.uav_fleet_adaptation.b06_count_development.contract import array_digest


OBJECT = "UAV-STOCHASTIC-TARGET-DEVELOPMENT-B07"
MASTER_SEED = 29711000
ARMS = ("C", "Q10", "Q05", "G", "P0", "Bstar0", "F0", "T", "H", "Tdirect", "Hdirect")
ORDINARY = ARMS[:4]
DIRECT = ARMS[-2:]
NEURAL = ARMS[4:9]
FITS = ("T", "H")
INPUT_ROOT = Path("/home/fires/hmasd-wsl/temp/directions/uav_fleet_adaptation/b07_inputs")
OLD_REL = Path("runs/uav_fleet_adaptation/b06_count_development_a02")
PARENT_REL = Path("runs/uav_fleet_adaptation/b02_inheritance_a01/assets/S.pt")
INPUT_MANIFEST_SHA256 = "31b0762abda4348179851ba09bc9beb9d14d6d1eb876a10b30a08f18dc07c71c"


@dataclass(frozen=True)
class Protocol:
    worlds: tuple = tuple(range(29710000, 29710032))
    layout_root: int = 29711001
    evaluation_roots: tuple = (29711101, 29711102)
    environment_constructor_seed: int = 29711205
    actor_constructor_seed: int = 29514201
    shuffle_root: int = 29514101
    bootstrap_seed: int = 29711991
    bootstrap_resamples: int = 10000
    horizon: int = 256
    period: int = 4
    n: int = 5

    def validate(self):
        if self != Protocol():
            raise ValueError("B07 production identities/exposure are frozen")
        return self

    def episode_order(self, world_index):
        if type(world_index) is not int or not 0 <= world_index < len(self.worlds):
            raise ValueError("invalid evaluation world index")
        base = [(arm, tape) for arm in ARMS for tape in ((None,) if arm == "C" else (0, 1))]
        offset = world_index % len(base)
        return tuple(base[offset:] + base[:offset])

    def expected(self):
        self.validate()
        return dict(fits=2, datasets=[40960, 61440, 81920], phase_rows=[40960, 20480, 20480],
                    phase_updates=[2400, 2400, 3200], optimizer_steps=16000,
                    sample_presentations=8192000, archive_files=256, archive_rows=81920,
                    target_rows=163840, parent_target_forwards=81920,
                    evaluation_episodes=672, native_steps=172032, native_uav_ticks=860160,
                    policy_decisions=215040, sampled_draws=204800,
                    full_C_requests=112640, deployed_neural_requests=143360,
                    deployed_helper_requests=102400, constructor_resets=1,
                    explicit_resets=672, layout_refreshes=672, native_dense_slots=47678675,
                    reader_files=928, reader_saved_ticks=237568, reader_C_requests=194560,
                    reader_helper_requests=184320, reader_actor_rows=389120,
                    reader_endpoint_rows=163840, new_acquisition_steps=0, new_calibrations=0)

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))


FROZEN = Protocol().validate()


def new_counts():
    return {key: 0 for key in (
        "fits_started", "fits_completed", "optimizer_steps", "sample_presentations",
        "parent_target_forward_calls", "parent_target_forwards", "target_vector_calls", "target_rows",
        "constructor_calls", "constructors", "constructor_resets", "explicit_reset_calls", "explicit_resets",
        "layout_refresh_calls", "layout_refreshes", "native_step_calls", "native_steps", "native_uav_ticks",
        "native_dense_slots", "evaluation_episodes", "policy_query_calls", "policy_decisions", "sampled_draws",
        "new_acquisition_steps", "new_calibrations",
    )}


def input_manifest():
    path = Path(__file__).with_name("f0_inputs.json")
    blob = path.read_bytes()
    if hashlib.sha256(blob).hexdigest() != INPUT_MANIFEST_SHA256:
        raise ValueError("pinned F0 metadata bytes changed")
    return json.loads(blob)


def source_identities(repo):
    repo = Path(repo)
    old = input_manifest()["sources"]
    result = {}
    for relative, expected in old.items():
        # Original summary binds hashes directly, not path-identity objects.
        digest = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
        if digest != expected:
            raise ValueError("inherited executable source changed: " + relative)
        result[relative] = digest
    own = Path(__file__).resolve().parent
    dependencies = [repo / "experiments/candidates/uav_fleet_transmission/b05_score_sampling" / name
                    for name in ("__init__.py", "policies.py", "reading.py", "contract.py")]
    for path in [*own.glob("*.py"), own / "f0_inputs.json", *dependencies]:
        result[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result

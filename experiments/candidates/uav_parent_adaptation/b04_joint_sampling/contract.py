"""Selected B04 identities, complete exposure and immutable asset/source inputs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from experiments.candidates.uav_fleet_adaptation.b02.contract import SOURCE_PINS

OBJECT = "UAV-PARENT-JOINT-SAMPLING-B04"
TAG = "b04_joint_sampling_a01"
ARMS = ("C", "Q_I", "Q_A", "Q_B", "S_I", "S_A", "S_B")
STOCHASTIC = ARMS[1:]
ASSET_PATH = Path("/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b02_inheritance_a01/assets/S.pt")
ASSET = dict(bytes=424487, sha256="b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a",
             state_sha256="6fa2eddc542d8f5293f5daf6a989b97a9d7d5f56f484f1eb6bddc6a87d27de0c")
B02_PINS = {
    "__init__.py": "acb5ecf84dabf7c006af3c2658d6ee8ef587cf3338d15898df75011c4c0a0970",
    "collect.py": "62a691a3d2b3e0579b84aca73b64fe61cdc11aee64ac2bd2d298db6ba59b44ef",
    "contract.py": "4f312ecbbe653c1d00632be4cd2f1ea6d48f7f98ce50eb28cf405f06e9fbe1a3",
    "controllers.py": "a2bbbdb877bd988590472a41c336d934a0431b5c560c7e80225cbb630fc3d522",
    "model.py": "c9b95b6718262c65591ed106ca81da0abb15b48ef6a8439438618365efc39934",
    "policies.py": "fba732164b07d80fc2f901e6545e6ca281c7db39cd89f9e61cc49bdb40ba4efd",
    "read.py": "6d07435ebeac57ace0a8696d69b1ff5f97cd4e3a15dc5f7486793ce6ba9ab336",
    "reading.py": "e70428557b90fb58fbe45ecdb832c1678328799b4382add92d47389a06e518a0",
    "run.py": "7e84a11c2c7e15ada65f0f050917864b40adc1cbb5c62ded943d1d6109a0e7aa",
    "study.py": "ed564b337e3d3f80cc96e50ec7b72c92f910014a31678143d6fc85bb905bef4d",
}


@dataclass(frozen=True)
class Protocol:
    worlds: tuple[int, ...] = tuple(range(29346000, 29346032))
    tapes: tuple[int, ...] = (0, 1)
    public_root: int = 29346091
    departure_root: int = 29346092
    tail_root: int = 29346093
    horizon: int = 256
    n_agents: int = 5
    period: int = 4
    grid_bits: int = 53

    def validate(self):
        if (not self.worlds or len(set(self.worlds)) != len(self.worlds)
                or any(type(w) is not int or w < 0 for w in self.worlds)):
            raise ValueError("nonempty unique nonnegative world identities required")
        if self.tapes != (0, 1) or self.n_agents != 5 or self.period != 4 or self.grid_bits != 53:
            raise ValueError("fixed two-tape/five-agent/four-tick/53-bit contract")
        if self.horizon <= 0 or self.horizon % 4:
            raise ValueError("complete four-tick horizons required")
        if len({self.public_root, self.departure_root, self.tail_root}) != 3:
            raise ValueError("public/departure/tail roots must be distinct")
        return self

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))

    def schedule(self):
        order = (("C", -1), ("Q_I", 0), ("S_I", 0), ("Q_A", 0), ("S_A", 0),
                 ("Q_B", 0), ("S_B", 0), ("Q_I", 1), ("S_I", 1), ("Q_A", 1),
                 ("S_A", 1), ("Q_B", 1), ("S_B", 1))
        for index, world in enumerate(self.worlds):
            shift = index % len(order)
            for arm, tape in order[shift:] + order[:shift]:
                yield arm, world, tape

    def expected(self):
        self.validate()
        worlds, decisions = len(self.worlds), self.horizon // 4 * 5
        episodes = worlds * 13
        c_requests, s_requests = worlds * 7 * decisions, worlds * 6 * decisions
        native_slots = (episodes * (self.horizon + 1) + 1) * 275
        return dict(fits=0, optimizer_steps=0, expert_labels=0, complete_episodes=episodes,
                    native_steps=episodes * self.horizon, controller_requests=episodes * decisions,
                    c_requests=c_requests, s_requests=s_requests,
                    c_candidate_paths_ceiling=c_requests * 27, c_model_ticks_ceiling=c_requests * 108,
                    c_candidate_power_ceiling=c_requests * 108 * 20,
                    c_setup_power_ceiling=c_requests * 100, s_helper_power_ceiling=s_requests * 140,
                    s_forward_rows_ceiling=s_requests, stochastic_decisions=s_requests * 2,
                    stochastic_joint_rows=worlds * 12 * self.horizon // 4,
                    native_dense_power_slots=native_slots,
                    combined_power_ceiling=c_requests * 2260 + s_requests * 140 + native_slots,
                    reader_motion_agent_ticks=episodes * self.horizon * 5,
                    reader_modal_motion_ceiling=worlds * 12 * self.horizon * 5,
                    unique_tape_bundles=worlds * 2,
                    unique_tape_integers=worlds * 2 * self.horizon // 4 * 11,
                    unique_tape_bytes=worlds * 2 * self.horizon // 4 * 11 * 8)


FROZEN = Protocol().validate()


def source_identities(repo):
    root = Path(repo)
    pins = {**SOURCE_PINS, **{f"experiments/candidates/uav_fleet_adaptation/b02/{p}": h
                             for p, h in B02_PINS.items()}}
    result = {}
    for relative, expected in pins.items():
        actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"bound source drift: {relative}")
        result[relative] = actual
    for path in sorted(Path(__file__).parent.glob("*.py")):
        result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def new_counts():
    return dict(fits=0, optimizer_steps=0, expert_labels=0, constructor_calls=0,
                constructors=0, constructor_resets=0, explicit_reset_calls=0,
                explicit_resets=0, native_step_calls=0, native_steps=0, complete_episodes=0,
                sampling_decisions=0)


def validate_counts(batch):
    e, a = batch["expected"], batch["actual"]
    for key in ("fits", "optimizer_steps", "expert_labels", "complete_episodes", "native_steps"):
        if a[key] != e[key]:
            raise AssertionError(f"exposure mismatch: {key}")
    if (a["constructor_calls"] != 1 or a["constructors"] != 1 or a["constructor_resets"] != 1
            or a["explicit_reset_calls"] != e["complete_episodes"]
            or a["explicit_resets"] != e["complete_episodes"]
            or a["native_step_calls"] != e["native_steps"]
            or a["sampling_decisions"] != e["stochastic_decisions"]):
        raise AssertionError("constructor/reset/native/sampling count mismatch")
    costs = batch["costs"]
    if costs["C"]["requests"] != e["c_requests"] or costs["S"]["requests"] != e["s_requests"]:
        raise AssertionError("controller request exposure mismatch")
    if (costs["S"].get("sampled_draws", 0) != 0
            or costs["S"]["neural_rows"] > e["s_forward_rows_ceiling"]
            or costs["C"]["model_ticks"] > e["c_model_ticks_ceiling"]):
        raise AssertionError("undeclared base sampling/forward/model work")

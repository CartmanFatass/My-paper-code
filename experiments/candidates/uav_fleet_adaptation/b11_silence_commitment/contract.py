"""Prospectively fixed complete B11 population and private randomness domains."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from experiments.candidates.uav_fleet_adaptation.b02.contract import SOURCE_PINS, array_digest
from experiments.candidates.uav_fleet_adaptation.b04_native_development.contract import CANONICAL_ASSETS

OBJECT = "UAV-SELF-SILENCE-COMMITMENT-B11"
MASTER_SEED = 30022000
PROGRAMS = ("C_ZERO", "CJ", "CJ_KEEP", "CJ_RETURN", "Hdirect_ZERO")
DETERMINISTIC = PROGRAMS[:4]
MEMORY = ("CJ_KEEP", "CJ_RETURN")
CELLS = (("C_ZERO", None), ("CJ", None), ("CJ_KEEP", None), ("CJ_RETURN", None),
         ("Hdirect_ZERO", 0), ("Hdirect_ZERO", 1))
CONTRASTS = (("CJ", "C_ZERO"), ("CJ_KEEP", "CJ"), ("CJ_RETURN", "CJ"),
             ("CJ_RETURN", "CJ_KEEP"), ("CJ_KEEP", "C_ZERO"), ("CJ_RETURN", "C_ZERO"),
             ("CJ", "Hdirect_ZERO"), ("CJ_KEEP", "Hdirect_ZERO"), ("CJ_RETURN", "Hdirect_ZERO"))
ASSET_BINDINGS = {"P0": dict(CANONICAL_ASSETS[0])}

@dataclass(frozen=True)
class Protocol:
    worlds: tuple[int, ...] = tuple(range(30021000, 30021032))
    evaluation_motion_roots: tuple[int, int] = (30022031, 30022032)
    bootstrap_seed: int = 30022041
    constructor_seed: int = 30022051
    actor_constructor_seed: int = 30022061
    bootstrap_resamples: int = 20000
    horizon: int = 256
    period: int = 4
    n_agents: int = 5

    def validate(self):
        if self.n_agents != 5 or self.period != 4 or type(self.horizon) is not int or self.horizon <= 0 or self.horizon % 4:
            raise ValueError("N5 and complete four-tick horizon required")
        if not self.worlds or any(type(w) is not int or w < 0 for w in self.worlds) or len(set(self.worlds)) != len(self.worlds):
            raise ValueError("distinct nonnegative world addresses required")
        roots = (*self.evaluation_motion_roots, self.bootstrap_seed, self.constructor_seed, self.actor_constructor_seed)
        if len(self.evaluation_motion_roots) != 2 or any(type(r) is not int or r < 0 for r in roots) or len(set(roots)) != 5 or set(roots) & set(self.worlds):
            raise ValueError("five disjoint private randomness addresses required")
        if type(self.bootstrap_resamples) is not int or self.bootstrap_resamples <= 0:
            raise ValueError("positive bootstrap count required")
        return self

    def episode_order(self, world_index):
        start = int(world_index) % len(CELLS)
        cells = CELLS[start:] + CELLS[:start]
        return cells if int(world_index) % 2 == 0 else cells[::-1]

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))

    @classmethod
    def from_dict(cls, values):
        values = dict(values)
        for key in ("worlds", "evaluation_motion_roots"):
            values[key] = tuple(values[key])
        return cls(**values).validate()

    def expected(self):
        self.validate()
        w, d = len(self.worlds), self.horizon // 4
        episodes, scalar = w * 6, w * 6 * (self.horizon + 1 + d)
        requests = episodes * d * 5
        return dict(fits=0, optimizer_steps=0, new_acquisition_targets=0, complete_episodes=episodes,
            evaluation_episodes=episodes, explicit_resets=episodes, constructor_resets=1,
            native_steps=episodes * self.horizon, native_uav_ticks=episodes * self.horizon * 5,
            mask_installs=episodes*d, motion_requests=requests, motion_draws=w*2*d*5,
            gate_opportunities=episodes*d, gate_draws=0,
            native_dense_power_slots=275*(episodes*(self.horizon+1+d)+1),
            native_unique_distance_pairs=260*(episodes*(self.horizon+1)+1),
            mask_refresh_dense_sinr_slots=275*episodes*d, CJ_off_scores=w*3*d,
            Hdirect_target_vectors=w*2*d*5*2, frozen_forward_ceiling=w*2*d*5,
            C_request_ceiling=requests, C_path_ceiling=requests*27, C_model_tick_ceiling=requests*108,
            C_link_ceiling=requests*2260, off_link_ceiling=w*3*d*100,
            controller_link_ceiling=requests*2260+w*3*d*100,
            memory_creation_per_arm_ceiling=w*d, memory_consumption_per_arm_ceiling=w*max(d-1,0),
            reader_scalar_states=scalar, reader_local_rows=scalar*5,
            reader_scalar_power_links=scalar*270, reader_distance_pairs=scalar*260,
            reader_dense_sinr_slots=scalar*275, worker_layout_draws=(episodes+1)*115,
            layout_verification_draws=episodes*115, bootstrap_integers=self.bootstrap_resamples*w)

FROZEN = Protocol().validate()


def source_identities(repo):
    repo = Path(repo)
    records = {}
    for relative, expected in SOURCE_PINS.items():
        actual = hashlib.sha256((repo/relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("frozen host/C source changed: " + relative)
        records[relative] = actual
    # Include transitive utilities, including their package initializers, but no
    # B10 driver is imported or executed by this study.
    dirs = ("uav_fleet_adaptation/b02", "uav_fleet_adaptation/b08_local_gate",
            "uav_fleet_adaptation/b11_silence_commitment")
    paths = [path for directory in dirs for path in (repo/"experiments/candidates"/directory).glob("*.py")]
    paths.extend(repo/relative for relative in (
        "envs/pettingzoo/uav_radio.py", "experiments/candidates/uav_fleet_adaptation/b04_native_development/contract.py",
        "experiments/candidates/uav_fleet_adaptation/b04_native_development/learning.py",
        "experiments/candidates/uav_fleet_adaptation/b07_stochastic_targets/targets.py",
        "experiments/candidates/uav_fleet_transmission/b05_score_sampling/policies.py",
        "experiments/candidates/uav_fleet_adaptation/b10_joint_control/policies.py",
        "experiments/candidates/uav_fleet_adaptation/b10_joint_control/records.py",
        "experiments/candidates/uav_fleet_adaptation/b10_joint_control/contract.py",
        "experiments/candidates/uav_fleet_adaptation/b10_joint_control/learning.py",
        "experiments/candidates/uav_local_history/b01/study.py",
        "experiments/candidates/ucope/uav_motion_prefix_b01/environment.py",
        "experiments/candidates/ucope/uav_motion_prefix_b01/policy.py"))
    for path in paths:
        records[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(sorted(records.items()))

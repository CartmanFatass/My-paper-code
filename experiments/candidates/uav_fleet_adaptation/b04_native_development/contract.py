"""Fixed identities, source bindings and the complete paid study envelope."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from experiments.candidates.uav_fleet_adaptation.b02.contract import SOURCE_PINS, array_digest


OBJECT = "UAV-INHERITED-NATIVE-DEVELOPMENT-B04"
MASTER_SEED = 29354000
CANDIDATES = ("C_0", "C_.05", "C_.10", "C_.20", "S_greedy", "S_T.5", "S_T1", "S_T2")
BASE_ARMS = ("C", "Q", "S", "R")
DECODER = "one-row-fp32-numpy-fp64-private-inverse-cdf-v1"
BOUND_SOURCES = {
    **SOURCE_PINS,
    "experiments/candidates/uav_fleet_adaptation/b02/__init__.py": "acb5ecf84dabf7c006af3c2658d6ee8ef587cf3338d15898df75011c4c0a0970",
    "experiments/candidates/uav_fleet_adaptation/b02/collect.py": "62a691a3d2b3e0579b84aca73b64fe61cdc11aee64ac2bd2d298db6ba59b44ef",
    "experiments/candidates/uav_fleet_adaptation/b02/contract.py": "4f312ecbbe653c1d00632be4cd2f1ea6d48f7f98ce50eb28cf405f06e9fbe1a3",
    "experiments/candidates/uav_fleet_adaptation/b02/controllers.py": "a2bbbdb877bd988590472a41c336d934a0431b5c560c7e80225cbb630fc3d522",
    "experiments/candidates/uav_fleet_adaptation/b02/model.py": "c9b95b6718262c65591ed106ca81da0abb15b48ef6a8439438618365efc39934",
    "experiments/candidates/uav_fleet_adaptation/b02/policies.py": "fba732164b07d80fc2f901e6545e6ca281c7db39cd89f9e61cc49bdb40ba4efd",
    "experiments/candidates/uav_fleet_adaptation/b02/read.py": "6d07435ebeac57ace0a8696d69b1ff5f97cd4e3a15dc5f7486793ce6ba9ab336",
    "experiments/candidates/uav_fleet_adaptation/b02/reading.py": "e70428557b90fb58fbe45ecdb832c1678328799b4382add92d47389a06e518a0",
    "experiments/candidates/uav_fleet_adaptation/b02/run.py": "7e84a11c2c7e15ada65f0f050917864b40adc1cbb5c62ded943d1d6109a0e7aa",
    "experiments/candidates/uav_fleet_adaptation/b02/study.py": "ed564b337e3d3f80cc96e50ec7b72c92f910014a31678143d6fc85bb905bef4d",
    "experiments/candidates/ucope/uav_motion_prefix_b01/policy.py": "e324640251d0d025549705ff7541b765e7b96733f422c48ee9c2f5bd07709614",
}
CANONICAL_ASSETS = (
    {"path": "/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b02_inheritance_a01/assets/S.pt",
     "bytes": 424487, "sha256": "b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a",
     "state_sha256": "6fa2eddc542d8f5293f5daf6a989b97a9d7d5f56f484f1eb6bddc6a87d27de0c",
     "launch_sha": "e945483b85c7f8ddfc315c57f36938d6c14201c7"},
    {"path": "/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b03_inheritance_recurrence_a01/assets/S.pt",
     "bytes": 424487, "sha256": "cb67a3d46fe9628e1dfef1ef081b89091a13fde3a92295fe198f27555c67364d",
     "state_sha256": "c6286dd32097d37b2c2c3039e487a24b756398e3ddffa9dc9e1ec3ef66170699",
     "launch_sha": "4909c9553300a4a4de6eb79476e818d7b1ceab53"},
)
STAGED_ASSETS = tuple({**record,
                      "path": "/home/fires/hmasd-wsl/temp/directions/uav_fleet_adaptation/b04_inputs/" + name,
                      "canonical_path": record["path"], "canonical_node": "wsl_4070"}
                     for record, name in zip(CANONICAL_ASSETS, ("S_b02.pt", "S_b03.pt")))


@dataclass(frozen=True)
class Protocol:
    training_worlds: tuple[tuple[int, ...], ...] = (tuple(range(29350000, 29350256)), tuple(range(29352000, 29352256)))
    evaluation_worlds: tuple[tuple[int, ...], ...] = (tuple(range(29351000, 29351032)), tuple(range(29353000, 29353032)))
    calibration_world_count: int = 32
    critic_seeds: tuple[int, int] = (29354011, 29354012)
    actor_constructor_seeds: tuple[int, int] = (29354001, 29354002)
    training_roots: tuple[int, int] = (29354021, 29354031)
    calibration_roots: tuple[int, int] = (29354022, 29354032)
    evaluation_roots: tuple[int, int] = (29354023, 29354033)
    horizon: int = 256
    period: int = 4
    n_agents: int = 5

    def validate(self):
        if self.n_agents != 5 or self.period != 4 or self.horizon <= 0 or self.horizon % 4:
            raise ValueError("fixed five-agent/four-tick host violated")
        if len(self.training_worlds) != 2 or len(self.evaluation_worlds) != 2:
            raise ValueError("both initial lineages are required")
        if any(not w or len(w) % 2 for w in self.training_worlds):
            raise ValueError("two complete episodes per group are required")
        if any(not w for w in self.evaluation_worlds) or self.calibration_world_count <= 0:
            raise ValueError("empty calibration/final panel")
        if any(self.calibration_world_count > len(w) for w in self.training_worlds):
            raise ValueError("calibration must use the first declared training worlds")
        worlds = [w for panel in (*self.training_worlds, *self.evaluation_worlds) for w in panel]
        if len(set(worlds)) != len(worlds) or any(not isinstance(w, int) or w < 0 for w in worlds):
            raise ValueError("world domains overlap or have invalid identities")
        domains = (self.critic_seeds, self.actor_constructor_seeds, self.training_roots,
                   self.calibration_roots, self.evaluation_roots)
        if any(len(v) != 2 for v in domains):
            raise ValueError("two lineage randomness domains required")
        seeds = [s for domain in domains for s in domain]
        if len(set(seeds)) != len(seeds) or any(not isinstance(s, int) or s < 0 for s in seeds):
            raise ValueError("randomness domains must be distinct")
        return self

    def calibration_worlds(self, lineage):
        return self.training_worlds[lineage][:self.calibration_world_count]

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))

    @classmethod
    def from_dict(cls, value):
        value = dict(value)
        for key in ("training_worlds", "evaluation_worlds"):
            value[key] = tuple(tuple(w) for w in value[key])
        for key in ("critic_seeds", "actor_constructor_seeds", "training_roots", "calibration_roots", "evaluation_roots"):
            value[key] = tuple(value[key])
        return cls(**value).validate()

    def expected(self, distinct_winners=None):
        self.validate()
        training = sum(map(len, self.training_worlds))
        calibration = 2 * self.calibration_world_count * len(CANDIDATES)
        base_eval = len(BASE_ARMS) * sum(map(len, self.evaluation_worlds))
        extra_eval = sum(map(len, self.evaluation_worlds))
        if distinct_winners is not None:
            if len(distinct_winners) != 2 or any(type(x) is not bool for x in distinct_winners):
                raise ValueError("exact distinct-winner flags required")
            extra_eval = sum(len(w) for w, distinct in zip(self.evaluation_worlds, distinct_winners) if distinct)
        episodes = training + calibration + base_eval + extra_eval
        clocks = self.horizon // 4
        return {"fits": 2, "calibrations": 2, "training_episodes": training,
                "calibration_episodes": calibration, "evaluation_episodes": base_eval + extra_eval,
                "complete_episodes": episodes, "native_steps": episodes * self.horizon,
                "training_native_steps": training * self.horizon,
                "calibration_native_steps": calibration * self.horizon,
                "evaluation_native_steps": (base_eval + extra_eval) * self.horizon,
                "actor_optimizer_steps": training // 2 * 4, "critic_optimizer_steps": training // 2 * 4,
                "actor_replay_rows": training * clocks * 5 * 4, "critic_replay_rows": training * clocks * 4,
                "density_identity_rows": training * clocks * 5, "collected_critic_rows": training * clocks,
                "shadow_actor_rows": sum(map(len, self.evaluation_worlds)) * clocks * 5,
                "shadow_motion_ticks": sum(map(len, self.evaluation_worlds)) * clocks * 5 * 4,
                "expert_labels": 0}


FROZEN = Protocol().validate()


def source_identities(repo):
    repo = Path(repo)
    identities = {}
    for relative, expected in BOUND_SOURCES.items():
        actual = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"bound source changed: {relative}")
        identities[relative] = actual
    for path in sorted((repo / "experiments/candidates/uav_fleet_adaptation/b04_native_development").glob("*.py")):
        identities[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return identities


def candidate_spec(candidate):
    if candidate not in CANDIDATES:
        raise ValueError("undeclared calibration candidate")
    if candidate.startswith("C_"):
        return {"family": "C", "epsilon": float(candidate[2:]), "temperature": None}
    temperature = {"S_greedy": None, "S_T.5": .5, "S_T1": 1., "S_T2": 2.}[candidate]
    return {"family": "S", "epsilon": None, "temperature": temperature}


def policy_identity(candidate, actor_sha, sampling_root):
    spec = candidate_spec(candidate)
    sampled = (spec["epsilon"] > 0 if spec["family"] == "C" else spec["temperature"] is not None)
    return {**spec, "source": (BOUND_SOURCES["experiments/candidates/uav_fleet_adaptation/b02/controllers.py"]
                               if spec["family"] == "C" else actor_sha),
            "decoder": DECODER if sampled else "deterministic-original-c" if spec["family"] == "C" else "first-logit-argmax",
            "sampling_root": int(sampling_root) if sampled else None,
            "command_source": SOURCE_PINS["experiments/candidates/uav_local_history/b01/controller.py"]}


def evaluation_plan(winner, initial_sha, final_sha, sampling_root):
    plan = [("C", "C_0", None), ("Q", "C_.10", None), ("S", "S_T1", initial_sha), ("R", "S_T1", final_sha)]
    identity = policy_identity(winner, initial_sha, sampling_root)
    reused = None
    for arm, candidate, sha in plan[:3]:
        if identity == policy_identity(candidate, sha, sampling_root):
            reused = arm
            break
    if reused is None:
        plan.append(("Bstar", winner, initial_sha if winner.startswith("S_") else None))
    return plan, {"winner": winner, "identity": identity, "reference_arm": reused or "Bstar", "reused": reused is not None}


def new_counts():
    return {key: 0 for key in ("fits_started", "fits_completed", "calibrations_started", "calibrations_completed",
            "constructor_calls", "constructors", "constructor_resets", "explicit_reset_calls", "explicit_resets", "native_step_calls", "native_steps",
            "training_native_steps", "calibration_native_steps", "evaluation_native_steps",
            "training_episodes", "calibration_episodes", "evaluation_episodes", "complete_episodes",
            "actor_optimizer_steps", "critic_optimizer_steps", "actor_replay_rows", "critic_replay_rows",
            "density_identity_rows", "collected_critic_rows", "shadow_actor_rows", "shadow_motion_ticks", "expert_labels")}

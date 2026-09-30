"""Prospective B05 identities, decision addresses and complete work."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b04_native_development.contract import (
    CANONICAL_ASSETS, array_digest, source_identities as inherited_sources,
)


OBJECT = "UAV-NATIVE-CONSEQUENCE-DEVELOPMENT-B05"
MASTER_SEED = 29484000
HEADS = ("CAL", "CONT")
ARMS = ("C", "Q", "S", "Bstar", *HEADS)
WINNERS = ("S_T2", "S_T1")
DECODER = "one-row-fp32-numpy-fp64-private-inverse-cdf-v1"
INITIAL_ASSETS = tuple({
    **record,
    "path": "/home/fires/hmasd-wsl/temp/directions/uav_fleet_adaptation/b05_inputs/" + name,
    "canonical_path": record["path"], "canonical_node": "wsl_4070",
} for record, name in zip(CANONICAL_ASSETS, ("S_b02.pt", "S_b03.pt")))
CALIBRATION_SOURCE = {
    "launch_sha": "98307b0c5cb6e42763458d780568d105d3f631af",
    "evidence_commit": "978c622c37207067dd673247cf6729d786383304",
    "reading_path": "runs/uav_fleet_adaptation/b04_native_development_a01/reading.json",
    "reading_sha256": "93c681eba38f8fcd7fd9059eb9eaa75142771d085bf645e831099bed63b25a50",
    "winners": list(WINNERS), "new_calibrations": 0,
}


@dataclass(frozen=True)
class Protocol:
    acquisition_worlds: tuple = (tuple(range(29480000, 29481024)), tuple(range(29482000, 29483024)))
    evaluation_worlds: tuple = (tuple(range(29481100, 29481132)), tuple(range(29483100, 29483132)))
    actor_constructor_seeds: tuple = (29484001, 29484002)
    acquisition_roots: tuple = (29484011, 29484012)
    evaluation_roots: tuple = (29484021, 29484022)
    intervention_a_roots: tuple = (29484031, 29484032)
    intervention_b_roots: tuple = (29484041, 29484042)
    address_roots: tuple = (29484051, 29484052)
    minibatch_roots: tuple = (29484061, 29484062)
    horizon: int = 256
    period: int = 4
    n_agents: int = 5
    updates: int = 2048
    batch_size: int = 128

    def validate(self):
        if (self.n_agents != 5 or self.period != 4 or self.horizon <= 0 or self.horizon % 4
                or type(self.updates) is not int or self.updates <= 0 or self.batch_size != 128):
            raise ValueError("fixed host or optimization dimensions changed")
        domains = (self.acquisition_worlds, self.evaluation_worlds)
        if any(len(v) != 2 or any(not w for w in v) for v in domains):
            raise ValueError("two nonempty inherited lineages required")
        d = self.horizon // 4 * 5
        if any(len(w) < d for w in self.acquisition_worlds):
            raise ValueError("every decision address must receive acquisition coverage")
        worlds = [w for panels in domains for panel in panels for w in panel]
        if len(set(worlds)) != len(worlds) or any(type(w) is not int or w < 0 for w in worlds):
            raise ValueError("world domains overlap or are invalid")
        seeds = (self.actor_constructor_seeds, self.acquisition_roots, self.evaluation_roots,
                 self.intervention_a_roots, self.intervention_b_roots, self.address_roots, self.minibatch_roots)
        if any(len(v) != 2 for v in seeds):
            raise ValueError("two lineage seed domains required")
        flat = [s for domain in seeds for s in domain]
        if len(set(flat)) != len(flat) or any(type(s) is not int or s < 0 for s in flat):
            raise ValueError("randomness domains must remain distinct")
        return self

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))

    @classmethod
    def from_dict(cls, value):
        value = dict(value)
        for key in ("acquisition_worlds", "evaluation_worlds"):
            value[key] = tuple(tuple(w) for w in value[key])
        for key in ("actor_constructor_seeds", "acquisition_roots", "evaluation_roots",
                    "intervention_a_roots", "intervention_b_roots", "address_roots", "minibatch_roots"):
            value[key] = tuple(value[key])
        return cls(**value).validate()

    def addresses(self, lineage):
        self.validate()
        d, n = self.horizon // 4 * 5, len(self.acquisition_worlds[lineage])
        permutation = np.random.default_rng(self.address_roots[lineage]).permutation(d)
        addresses = np.concatenate((np.tile(permutation, n // d), permutation[:n % d])).astype(np.int64)
        frequency = np.bincount(addresses, minlength=d)
        weights = n / (d * frequency[addresses].astype(np.float64))
        return addresses, weights

    def expected(self):
        self.validate()
        contexts = sum(map(len, self.acquisition_worlds))
        acquisition = 2 * contexts
        final = sum(len(self.evaluation_worlds[l]) * len(evaluation_arms(l)) for l in range(2))
        decisions = self.horizon // 4 * 5
        ordinary = 2 * sum(map(len, self.evaluation_worlds))
        learned = 2 * sum(map(len, self.evaluation_worlds))
        final_student = final - ordinary
        return dict(head_fits=4, acquisition_contexts=contexts, acquisition_episodes=acquisition,
                    evaluation_episodes=final, complete_episodes=acquisition + final,
                    native_steps=(acquisition + final) * self.horizon,
                    acquisition_native_steps=acquisition * self.horizon, evaluation_native_steps=final * self.horizon,
                    head_optimizer_steps=4 * self.updates, head_training_rows=4 * self.updates * self.batch_size,
                    intervention_draws=acquisition, shadow_decisions=learned * decisions,
                    shadow_motion_ticks=learned * decisions * 4, student_requests=(acquisition + final_student) * decisions,
                    ordinary_requests=ordinary * decisions, reader_pair_backbone_rows=contexts,
                    reader_final_backbone_rows=final_student * decisions,
                    reader_backbone_rows=contexts + final_student * decisions,
                    reader_head_rows=learned * decisions, new_calibrations=0, critic_rows=0, expert_labels=0)


def evaluation_arms(lineage):
    if lineage not in (0, 1):
        raise ValueError("invalid lineage")
    return ARMS if lineage == 0 else tuple(a for a in ARMS if a != "Bstar")


FROZEN = Protocol().validate()


def source_identities(repo):
    identities = inherited_sources(repo)
    for path in sorted((Path(repo) / "experiments/candidates/uav_fleet_adaptation/b05_native_consequence").glob("*.py")):
        identities[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return identities


def policy_identity(arm, lineage, initial_sha, head_sha, root):
    if arm not in ARMS or (arm in HEADS) != (head_sha is not None):
        raise ValueError("policy arm/head identity mismatch")
    ordinary = arm in ("C", "Q")
    return dict(arm=arm, original_student=None if ordinary else initial_sha,
                head_sha256=head_sha, head_kind=arm if arm in HEADS else None,
                temperature=2. if arm == "Bstar" and lineage == 0 else None if ordinary else 1.,
                epsilon=0. if arm == "C" else .1 if arm == "Q" else None,
                sampling_root=None if arm == "C" else int(root),
                decoder="deterministic-original-c" if arm == "C" else DECODER)


def new_counts():
    return {key: 0 for key in (
        "head_fits_started", "head_fits_completed", "head_optimizer_steps", "head_training_rows",
        "constructor_calls", "constructors", "constructor_resets", "explicit_reset_calls", "explicit_resets",
        "native_step_calls", "native_steps", "acquisition_native_steps", "evaluation_native_steps",
        "acquisition_episodes", "evaluation_episodes", "complete_episodes", "acquisition_contexts",
        "intervention_draws", "shadow_decisions", "shadow_motion_ticks", "new_calibrations", "critic_rows", "expert_labels",
    )}

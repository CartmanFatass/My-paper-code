"""EOCIV Stage 0 outcome harness: pools, complete blocks, bound execution.

This module builds the registered outcome experiment's execution objects on
top of the ACCEPTED mechanisms — it deliberately implements none of them
itself:

- seed derivation and episode namespaces are the ``capability_gate``
  functions, imported and re-exported BY IDENTITY (the Stage 0 gate asserts
  ``outcome_harness.outcome_world_seed is capability_gate.outcome_world_seed``
  and so on, per the acceptance ruling's "one authoritative implementation"
  requirement);
- the receipt/action binding is the accepted ``ArmEpisodeRunner`` path; the
  harness only supplies the trainable actor adapter, the profile-qualified
  noise seed, and the COMPLETE block-identity runner binding (ruling 6.2);
- the D_C control is the exact-rate profile-matched permutation tape defined
  by contract 6.6 — the Bernoulli-0.5 gate probe
  (``sibling_env.control_tape_open``) is never referenced here, and the
  Stage 0 preflight asserts that mechanically.

Stage 0 scope: everything here is construction and FORWARD-ONLY execution.
Focal-arm return evaluation and every learning step remain unlicensed.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import actuation_runtime as art
from experiments.candidates.eociv_lite import capability_gate as gate_mod
from experiments.candidates.eociv_lite import sibling_env as sib
from experiments.candidates.eociv_lite import stage0_registration as reg
from experiments.candidates.eociv_lite import trainable_policy as tp

RAW_OUTPUT_BINDING = "eociv_lite.outcome_harness.v1"

# The authoritative mechanism implementations, re-exported BY IDENTITY.
profile_qualified_seed = gate_mod.profile_qualified_seed
outcome_world_seed = gate_mod.outcome_world_seed
outcome_noise_seed = gate_mod.outcome_noise_seed

POOLS = tuple(
    gate_mod.REGISTERED_OUTCOME_EXPERIMENT["episode_namespaces"].keys()
)


def pool_episode_ids(pool: str) -> range:
    """The frozen local-episode-id namespace of one ancestry pool."""
    lo, hi = gate_mod.REGISTERED_OUTCOME_EXPERIMENT["episode_namespaces"][pool]
    return range(lo, hi + 1)


def episode_uid(profile_registration_id: str, pool: str, local_episode_id: int) -> str:
    if pool not in POOLS:
        raise ValueError(f"unknown pool: {pool}")
    if int(local_episode_id) not in pool_episode_ids(pool):
        raise ValueError(
            f"local episode id {local_episode_id} outside the {pool} namespace"
        )
    return f"{profile_registration_id}|{pool}|{int(local_episode_id)}"


@dataclass(frozen=True)
class BlockIdentity:
    """The COMPLETE registered block identity (acceptance ruling 6.2)."""

    pool: str
    actor_training_seed: int
    profile_registration_id: str
    local_episode_id: int
    arm: str

    def runner_binding(self, opportunity_scope: str) -> str:
        """The block half of the receipt's complete identity.

        The ruling's complete block identity (6.2) is carried JOINTLY by the
        receipt: this binding string contributes pool, actor training seed,
        profile, episode and arm (stable across the episode), while the
        receipt's ``opportunity_identity`` (EdgeIdentity) contributes the
        event index, receiver/source member keys and spell epochs per
        boundary.  ``opportunity_scope`` appends only static environment
        scope (member capacity) — it does NOT carry per-boundary fields.
        """
        return (
            f"{self.pool}|seed{self.actor_training_seed}"
            f"|{self.profile_registration_id}|ep{self.local_episode_id}"
            f"|{self.arm}|{opportunity_scope}"
        )


def block_environment(
    profile: roster_env.RosterProfile, local_episode_id: int
) -> sib.EocivSiblingRosterEnv:
    """One block clone's environment from the profile-qualified world seed.

    All four arms of a block call this with identical arguments, so they
    share the exact ledger, shock states and focal draws by construction.
    """
    ledger = roster_env.make_ledger(
        int(local_episode_id),
        master_seed=outcome_world_seed(profile.name),
        profile=profile,
    )
    return sib.EocivSiblingRosterEnv(
        ledger, sibling_seed=gate_mod.SIBLING_SEED
    )


def build_arm_runner(
    profile: roster_env.RosterProfile,
    *,
    pool: str,
    actor_training_seed: int,
    local_episode_id: int,
    arm: str,
    actor: tp.EocivActor,
    valve: tp.EocivValve,
    control_decisions: tuple[bool, bool, bool] | None = None,
    body_override: bytes | None = None,
) -> art.ArmEpisodeRunner:
    """One arm clone's runner through the ACCEPTED binding path.

    - D_L is the frozen valve inference rule (untrained in Stage 0).
    - D_C comes from the exact-rate permutation tape via
      ``control_decisions`` (one boolean per lifecycle event); it is built in
      Stage 2 from D_cal and is NOT computable yet, so Stage 0 preflight
      passes the all-open tape.  ``sibling_env.control_tape_open`` is never
      consulted.
    """
    env = block_environment(profile, local_episode_id)
    identity = BlockIdentity(
        pool=pool,
        actor_training_seed=int(actor_training_seed),
        profile_registration_id=profile.name,
        local_episode_id=int(local_episode_id),
        arm=arm,
    )
    opportunity_scope = f"cap{env.ledger.member_capacity}"
    opened = (True, True, True) if control_decisions is None else tuple(
        bool(v) for v in control_decisions
    )
    adapter = tp.ActorRunnerAdapter(actor, env.ledger)
    capacity = env.ledger.member_capacity

    def d_learned(w_bytes: bytes) -> bool:
        return valve.decision(w_bytes, capacity)

    def d_control(event_index: int) -> bool:
        return opened[event_index]

    return art.ArmEpisodeRunner(
        env, arm,
        tape_seed=0,  # inert: d_control_fn below preempts the gate probe
        d_learned_fn=d_learned,
        body_override=body_override,
        policy=adapter,
        action_noise_seed=outcome_noise_seed(profile.name),
        runner_binding=identity.runner_binding(opportunity_scope),
        d_control_fn=d_control,
    )


def fit_support_route(
    pool: str, profile_registration_id: str, local_episode_id: int,
    event_index: int,
) -> str:
    """The registered fit-support token assignment (contract 6.4).

    Domain-separated hash over pre-outcome identifiers ONLY; no reward,
    return, valve score or learned quantity is an input.
    """
    label = reg.FIT_SUPPORT_ASSIGNMENT["domain_label"]
    digest = hashlib.sha256(
        f"{label}|{pool}|{profile_registration_id}"
        f"|{int(local_episode_id)}|{int(event_index)}".encode("ascii")
    ).digest()
    u = Fraction(int.from_bytes(digest[:8], "big"), 2 ** 64)
    if u < Fraction(1, 2):
        return "REAL"
    if u < Fraction(3, 4):
        return "NATIVE_NEUTRAL"
    if u < Fraction(7, 8):
        return "PATTERN_ONLY"
    return "PAYLOAD_KNOCKOUT"


def exact_rate_control_tape(
    profile_registration_id: str,
    *,
    close_fraction: Fraction,
    local_episode_ids: tuple[int, ...],
    tape_epoch: int,
) -> dict[tuple[int, int], bool]:
    """The frozen exact-rate profile-matched permutation tape (contract 6.6).

    Returns {(local_episode_id, event_index): close?} with EXACTLY
    ``round_half_up(q * N)`` closures, pooled over all events of the given
    episodes, ordered by the registered permutation key.  Inputs are
    pre-outcome identifiers and the frozen constants only.
    """
    events = [
        (int(episode_id), event_index)
        for episode_id in local_episode_ids
        for event_index in range(len(sib.EVENT_TIMES))
    ]
    total = len(events)
    target = close_fraction * total
    close_count = int(target) + (1 if (target - int(target)) >= Fraction(1, 2) else 0)

    def permutation_key(event: tuple[int, int]) -> tuple[int, str]:
        episode_id, event_index = event
        digest = hashlib.sha256(
            f"EOCIV-DC-PERM-V1|{profile_registration_id}|{int(tape_epoch)}"
            f"|{episode_id}|{event_index}".encode("ascii")
        ).hexdigest()
        return (int(digest[:16], 16), digest)

    ordered = sorted(events, key=permutation_key)
    closed = set(ordered[:close_count])
    return {event: (event in closed) for event in events}


def clustered_bootstrap_root_draws(
    profile_registration_id: str, *, replicate_index: int, n_roots: int
) -> tuple[int, ...]:
    """One bootstrap replicate's root multiset (contract 6.8).

    The resampling cluster is (profile, focal_episode_id): the SAME sampled
    root indices apply to all three actor seeds of that profile, so the
    crossed common-random-number design is resampled as paired clusters,
    never as independent actor-seed draws.
    """
    seed = gate_mod.profile_qualified_seed(
        reg.BOOTSTRAP_CONTRACT["bootstrap_seed_label"],
        int(replicate_index),
        profile_registration_id,
    )
    rng = np.random.default_rng(seed)
    return tuple(int(v) for v in rng.integers(0, int(n_roots), size=int(n_roots)))


def negative_control_decision(
    tau: float, tau_pattern: float, tau_knockout: float
) -> dict[str, object]:
    """The frozen negative-control decision algebra (contract 6.9)."""
    if tau <= 0:
        return {
            "primary_fails": True,
            "reason": "tau <= 0: automatic failure, no ratio-based rescue",
            "negative_controls_pass": False,
        }
    bound = 0.5 * max(tau, 0.0)
    passes = max(abs(tau_pattern), abs(tau_knockout)) <= bound
    return {
        "primary_fails": False,
        "negative_controls_pass": bool(passes),
        "bound": bound,
    }

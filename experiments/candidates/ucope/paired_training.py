"""Bounded paired PPO training of UCOPE count-state vs count-blind policies.

Sequence 03 experiment.  The external ruling gated this run on a positive
capability certificate:

    "That exact calculation is the decisive proof that the environment now
     contains the mechanism.  Training should begin only after this capability
     certificate is positive."

Both halves of that gate are closed -- ``capability_certificate`` returns
``UCOPE_CAPABILITY_PRESENT`` and ``regime_conformance`` returns
``UCOPE_SIBLING_CONFORMS`` -- so training is licensed.

WHAT THIS RUN ASKS
------------------
The certificate proves an *oracle* that reads the evidence count does better
than one that cannot.  That is a statement about the environment.  It says
nothing about learning.  This module trains three arms and asks the narrower
question External Pro licensed:

    does count-enabled training outperform matched count-disabled training
    under this finite budget?

Note the wording.  An earlier revision of this docstring asked whether a policy
"actually discovers and uses the count", and Pro ruled that one step too strong:

    The results show that count-enabled training outperformed count-disabled
    training. They do not contain a causal intervention on the same learned
    informed policy.

That causal intervention now exists, in ``crossed_evaluation``: the frozen
informed checkpoint is evaluated twice, with and without its count channels.
This module trains; that one measures.

The certificate supplies exact bounds:

    count-informed optimum   16 * 73/32 = 36.5
    count-blind optimum      16 * 2     = 32.0

Those are expectations under the prior, NOT pointwise maxima for a finite block
of drawn episodes -- the blind oracle earns 48 in regime S and 16 in regime L,
so a block with more than half S episodes can legitimately average above 32.0.
Treating 32.0 as a sample ceiling was a real error in the first pass; the valid
form of that guard lives in ``crossed_evaluation.blind_ceiling_guard``, where
the crossed estimator makes it an expectation again.

DESIGN CHOICES, AND WHY
-----------------------
*Effort only.*  The mix half of the action is matched analytically to the
observed target.  This is not a simplification of the science -- it is the
certified design.  The ruling required that "the oracle disclosure for that
coordinate is removed" for load while "target mix remains exactly observed, so
the mix half of the action stays solved and the certificate isolates the effort
half."  Learning the mix as well would add variance to a channel the ruling
already declared solved.

*Common random numbers.*  Arms share episode ids, so they see identical regimes
and identical evidence bit sequences.  The comparison is paired.

*Three arms, one code path.*  ``SEVERED`` accumulates the count exactly as
``INFORMED`` does and then zeroes it immediately before the policy reads it, so
it is informationally identical to ``BLIND`` while executing the informed path.

Pro ruled on what that arm is worth, and it is less than the first pass claimed:
under shared seeds BLIND and SEVERED receive identical ``(0.0, 0.0)`` channels
and are therefore *the same computation*, so their exact equality is a
determinism checksum rather than a replicated null.  Pro also ruled that it must
NOT be repaired by making SEVERED differ in some non-information feature --
*"That would make the control less matched"* -- so it is left exactly as it is
and reported for what it is.  The informative severing evidence is the exact
specification-side result in ``regime_conformance``, plus the within-checkpoint
intervention in ``crossed_evaluation``.

SCOPE
-----
Numbers here are a code-side measurement.  Their scientific reading -- whether
this constitutes evidence for UCOPE -- belongs to External Pro, in the existing
capability conversation for this direction.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
import torch
import torch.nn as nn

from envs.continuous_roster import runtime_capacity as roster_env

from experiments.candidates.ucope import capability_certificate as cc
from experiments.candidates.ucope import regime_roster_env as sibling

RAW_OUTPUT_BINDING = "ucope.paired_training.v1"

INFORMED = "COUNT_INFORMED"
BLIND = "COUNT_BLIND"
SEVERED = "COUNT_SEVERED"
ARMS = (INFORMED, BLIND, SEVERED)

#: Exact optima from the certificate, scaled to an episode.
INFORMED_OPTIMUM = float(cc.valuations().informed * sibling.EPOCH_LENGTH)
BLIND_OPTIMUM = float(cc.valuations().blind * sibling.EPOCH_LENGTH)

#: Policy input width: 2 count channels + 4 roster/time channels.
COUNT_DIM = 2
CONTEXT_DIM = 4
OBSERVATION_DIM = COUNT_DIM + CONTEXT_DIM

LEARNING_RATE = 3e-3
CLIP_RANGE = 0.2
PPO_EPOCHS = 4
VALUE_COEFFICIENT = 0.5
ENTROPY_COEFFICIENT = 1e-3


class EffortPolicy(nn.Module):
    """Gaussian over the pre-squash effort action, plus a value head."""

    def __init__(self, hidden: int = 64):
        super().__init__()
        self.trunk = nn.Sequential(
            nn.Linear(OBSERVATION_DIM, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
        )
        self.mean = nn.Linear(hidden, 1)
        self.value = nn.Linear(hidden, 1)
        self.log_std = nn.Parameter(torch.zeros(1))

    def forward(self, features: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        latent = self.trunk(features)
        return self.mean(latent).squeeze(-1), self.log_std.expand(features.shape[0]), self.value(latent).squeeze(-1)


def policy_features(view: sibling.RegimeView, *, arm: str) -> np.ndarray:
    """The policy's input.  The load is absent by construction, not by choice."""
    if arm == INFORMED:
        counts = (
            view.positive_count / sibling.PERIODS,
            view.completed_epochs / sibling.PERIODS,
        )
    else:
        # BLIND never accumulates; SEVERED accumulates and is severed here.
        counts = (0.0, 0.0)
    active = view.active_mask
    observations = view.observations[active]
    return np.asarray(
        (
            counts[0],
            counts[1],
            float(observations[:, 5].mean()),          # log1p(active count)
            float(view.target_mix),
            float(view.base.time) / roster_env.HORIZON,
            float(active.sum()) / len(active),
        ),
        dtype=np.float32,
    )


def _effort_from_action(action: torch.Tensor) -> float:
    """Squash to the legal action support, then to an effort in (0, 1)."""
    return float((torch.tanh(action).item() + 1.0) / 2.0)


@dataclass
class Rollout:
    features: list[np.ndarray] = field(default_factory=list)
    actions: list[float] = field(default_factory=list)
    log_probs: list[float] = field(default_factory=list)
    rewards: list[float] = field(default_factory=list)
    values: list[float] = field(default_factory=list)


def collect_episode(
    policy: EffortPolicy,
    *,
    arm: str,
    episode_id: int,
    regime_seed: int,
    evidence_seed: int,
    generator: torch.Generator,
    deterministic: bool = False,
) -> tuple[Rollout, float]:
    """One episode.  Regime and evidence are CRN-keyed to episode_id."""
    regime = sibling.draw_regime(episode_id, regime_seed=regime_seed)
    bits = sibling.draw_evidence(episode_id, regime, evidence_seed=evidence_seed)
    ledger = roster_env.make_ledger(
        episode_id,
        master_seed=regime_seed,
        profile=roster_env.TRAIN_PROFILES[episode_id % len(roster_env.TRAIN_PROFILES)],
    )
    env = sibling.UcopeRegimeRosterEnv(ledger, regime=regime, evidence_bits=bits)

    rollout = Rollout()
    terminated = False
    while not terminated:
        view = env.observe()
        features = policy_features(view, arm=arm)
        tensor = torch.from_numpy(features).unsqueeze(0)
        with torch.no_grad():
            mean, log_std, value = policy(tensor)
            std = log_std.exp()
            # Evaluation must use the policy's mean action.  Sampling during
            # evaluation reports the *exploration* return, not the learned
            # policy's return, and with a wide initial log_std that understates
            # every arm by a large and arm-independent amount.
            action = (
                mean
                if deterministic
                else mean
                + std
                * torch.randn(mean.shape, generator=generator, dtype=mean.dtype)
            )
            log_prob = (
                -0.5 * (((action - mean) / std) ** 2)
                - log_std
                - 0.5 * math.log(2.0 * math.pi)
            )
        effort = _effort_from_action(action[0])
        reward, terminated, _ = env.step(
            sibling.uniform_effort_actions(view, effort)
        )
        rollout.features.append(features)
        rollout.actions.append(float(action.item()))
        rollout.log_probs.append(float(log_prob.item()))
        rollout.values.append(float(value.item()))
        rollout.rewards.append(reward)
    return rollout, env.episode_total()


def _update(
    policy: EffortPolicy,
    optimizer: torch.optim.Optimizer,
    batch: Sequence[Rollout],
) -> None:
    features = torch.from_numpy(
        np.stack([row for episode in batch for row in episode.features])
    )
    actions = torch.tensor(
        [a for episode in batch for a in episode.actions], dtype=torch.float32
    )
    old_log_probs = torch.tensor(
        [p for episode in batch for p in episode.log_probs], dtype=torch.float32
    )
    # Credit assignment is gamma = 0, and that is a structural fact about this
    # environment rather than a tuning choice.  The service reward at step t is
    # a function of the effort played at t against that step's realized load and
    # target mix.  Effort has no dynamical effect: it does not move the regime,
    # the evidence count, the roster, or any coordinate this policy reads
    # (`policy_features` uses the active count, target mix, time and active
    # fraction, none of which depend on past actions).  From the policy's view
    # each step is a contextual bandit.
    #
    # Crediting an action with the whole 48-step reward-to-go therefore adds 47
    # steps of reward it did not cause, and in practice that variance dominated
    # the signal: the policy drifted back to its initialization (effort ~ 0.5,
    # deterministic return ~15.0) instead of the blind optimum (effort 1/4,
    # return 32.0).
    target = torch.tensor(
        [r for episode in batch for r in episode.rewards], dtype=torch.float32
    )
    advantage = target - torch.tensor(
        [v for episode in batch for v in episode.values], dtype=torch.float32
    )
    advantage = (advantage - advantage.mean()) / (advantage.std() + 1e-8)

    for _ in range(PPO_EPOCHS):
        mean, log_std, value = policy(features)
        std = log_std.exp()
        log_probs = (
            -0.5 * (((actions - mean) / std) ** 2)
            - log_std
            - 0.5 * math.log(2.0 * math.pi)
        )
        ratio = (log_probs - old_log_probs).exp()
        surrogate = torch.min(
            ratio * advantage,
            torch.clamp(ratio, 1.0 - CLIP_RANGE, 1.0 + CLIP_RANGE) * advantage,
        ).mean()
        value_loss = nn.functional.mse_loss(value, target)
        entropy = (log_std + 0.5 * math.log(2.0 * math.pi * math.e)).mean()
        loss = -surrogate + VALUE_COEFFICIENT * value_loss - ENTROPY_COEFFICIENT * entropy
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()


@dataclass
class ArmRun:
    arm: str
    initial_return: float
    final_return: float
    history: list[float] = field(default_factory=list)
    final_totals: list[float] = field(default_factory=list)
    #: The trained weights.  Carried out of training so `crossed_evaluation`
    #: can freeze this exact checkpoint, digest it, and intervene on it.
    policy: "EffortPolicy | None" = None


def run_arm(
    arm: str,
    *,
    iterations: int = 120,
    episodes_per_iteration: int = 16,
    evaluation_episodes: int = 64,
    seed: int = 20_260_806,
) -> ArmRun:
    torch.manual_seed(seed)
    policy = EffortPolicy()
    optimizer = torch.optim.Adam(policy.parameters(), lr=LEARNING_RATE)
    generator = torch.Generator(device="cpu").manual_seed(seed + 1)

    def evaluate_totals(offset: int) -> list[float]:
        """Per-episode totals on a FIXED episode-id block shared by all arms.

        Returning the per-episode vector rather than its mean is what makes the
        paired analysis possible.  Episode totals are near-bimodal (~48 when the
        regime is S and effort matches, ~16 when it is L), so the unpaired
        standard deviation is ~16 and an unpaired mean cannot resolve the 4.5
        effect at any affordable sample size.  Pairing on episode id cancels the
        regime draw, which is the entire source of that variance.
        """
        return [
            collect_episode(
                policy,
                arm=arm,
                episode_id=100_000 + offset + index,
                regime_seed=seed + 2,
                evidence_seed=seed + 3,
                generator=generator,
                deterministic=True,
            )[1]
            for index in range(evaluation_episodes)
        ]

    def evaluate(offset: int) -> float:
        return statistics.fmean(evaluate_totals(offset))

    run = ArmRun(arm=arm, initial_return=evaluate(0), final_return=0.0)
    run.final_totals = []
    for iteration in range(iterations):
        batch = []
        for index in range(episodes_per_iteration):
            episode_id = iteration * episodes_per_iteration + index
            rollout, _ = collect_episode(
                policy,
                arm=arm,
                episode_id=episode_id,
                regime_seed=seed + 2,
                evidence_seed=seed + 3,
                generator=generator,
            )
            batch.append(rollout)
        _update(policy, optimizer, batch)
        if (iteration + 1) % 20 == 0:
            run.history.append(evaluate(0))
    run.final_totals = evaluate_totals(0)
    run.final_return = statistics.fmean(run.final_totals)
    run.policy = policy
    return run


def _paired(left: Sequence[float], right: Sequence[float]) -> dict[str, float]:
    """Per-episode paired difference.  Arms share episode ids, hence regimes."""
    differences = [a - b for a, b in zip(left, right)]
    mean = statistics.fmean(differences)
    if len(differences) < 2:
        return {"mean": mean, "standard_error": float("inf"), "t": 0.0}
    error = statistics.stdev(differences) / math.sqrt(len(differences))
    return {
        "mean": mean,
        "standard_error": error,
        "t": (mean / error) if error > 0 else float("inf"),
    }


def run_experiment(**kwargs) -> dict[str, object]:
    runs = {arm: run_arm(arm, **kwargs) for arm in ARMS}
    informed_gain = runs[INFORMED].final_return - runs[BLIND].final_return
    severed_gain = runs[SEVERED].final_return - runs[BLIND].final_return

    paired_informed = _paired(runs[INFORMED].final_totals, runs[BLIND].final_totals)
    paired_severed = _paired(runs[SEVERED].final_totals, runs[BLIND].final_totals)

    # HEURISTIC WARNING ONLY -- deliberately not a validity theorem.
    #
    # The first pass called this a validity guard and claimed that a blind mean
    # above 32.0 proved the estimate noise-dominated.  Pro falsified that:
    #
    #     The exact blind value 32 is an expectation under the prior, not a
    #     pointwise maximum for every evaluation sample. [...] a finite
    #     evaluation block containing more than 50% S episodes can therefore
    #     have a blind-oracle sample mean above 32 without any policy error or
    #     leakage.
    #
    # Pro also noted the code never actually refused -- it set the flag and
    # emitted the comparison anyway.  Both defects are fixed by demotion: this
    # is now named, and treated, as a heuristic sanity warning on a sampled
    # block.  The refusal that IS a theorem lives in
    # `crossed_evaluation.blind_ceiling_guard`, where the estimator is an exact
    # expectation over the crossed support and the per-step bound 2/3 is
    # therefore a genuine pointwise ceiling.
    blind_totals = runs[BLIND].final_totals
    blind_error = (
        statistics.stdev(blind_totals) / math.sqrt(len(blind_totals))
        if len(blind_totals) > 1
        else float("inf")
    )
    blind_excess = runs[BLIND].final_return - BLIND_OPTIMUM

    return {
        "heuristic_blind_ceiling_warning": {
            "sampled_blind_excess_over_prior_expectation": blind_excess,
            "sampled_blind_standard_error": blind_error,
            "warned": blind_excess > blind_error,
            "status": (
                "HEURISTIC ONLY. A sampled block is not bounded by the prior "
                "expectation 32.0; the blind oracle earns 48 in regime S and 16 "
                "in regime L. Use crossed_evaluation.blind_ceiling_guard for the "
                "admissible refusal."
            ),
        },
        "paired_informed_minus_blind": paired_informed,
        "paired_severed_minus_blind": paired_severed,
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "certified_informed_optimum": INFORMED_OPTIMUM,
        "certified_blind_optimum": BLIND_OPTIMUM,
        "certified_gain": INFORMED_OPTIMUM - BLIND_OPTIMUM,
        "arms": {
            arm: {
                "initial_return": run.initial_return,
                "final_return": run.final_return,
                "history": run.history,
            }
            for arm, run in runs.items()
        },
        "learned_informed_minus_blind": informed_gain,
        "learned_severed_minus_blind": severed_gain,
        # NOT an information-capture fraction.  Pro decomposed the quantity the
        # first pass reported as "83% of the certified gain":
        #
        #     0.8308 = 1 - (eps_I - eps_B) / 4.5
        #
        # with optimization regrets eps_I = 1.7821 and eps_B = 1.0207.  It
        # embeds the blind arm's under-convergence, which *enlarges* the learned
        # contrast.  It is renamed to what it actually measures, and the regrets
        # that drive it are reported alongside so it cannot be read as capture.
        "fraction_of_oracle_gap_in_the_trained_contrast": (
            informed_gain / (INFORMED_OPTIMUM - BLIND_OPTIMUM)
        ),
        "optimization_regret": {
            INFORMED: INFORMED_OPTIMUM - runs[INFORMED].final_return,
            BLIND: BLIND_OPTIMUM - runs[BLIND].final_return,
        },
        "scope": (
            "Code-side measurement on a sampled block. Scientific "
            "interpretation belongs to External Pro in the existing capability "
            "conversation. The admissible estimator is crossed_evaluation."
        ),
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(run_experiment(), indent=2))

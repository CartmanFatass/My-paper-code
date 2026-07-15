"""Exact supervised capacity diagnostic for the R39 joint-roster policy."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ha_ctse_process.r30_fixed_clock import FixedClockAREditPolicy, SET_TOKEN


ROSTERS = tuple(itertools.product(range(4), repeat=2))
TARGET_SIGNS = tuple(itertools.product((-1, 1), repeat=2))
PREVIOUS_ROSTERS = ((0, 2), (1, 3))


def compact_state(slow_sign: int, fast_sign: int) -> torch.Tensor:
    return torch.tensor(
        [[float(slow_sign), 0.0, 0.0, float(fast_sign), 0.0, 0.0, 0.0, 0.0]],
        dtype=torch.float32,
    )


def correct_rosters(slow_sign: int, fast_sign: int) -> tuple[tuple[int, int], ...]:
    slow_skill = 0 if slow_sign > 0 else 1
    fast_skill = 2 if fast_sign > 0 else 3
    return ((slow_skill, fast_skill), (fast_skill, slow_skill))


def roster_log_probabilities(
    policy: FixedClockAREditPolicy,
    *,
    slow_sign: int,
    fast_sign: int,
    previous_roster: tuple[int, int],
) -> torch.Tensor:
    compact = compact_state(slow_sign, fast_sign)
    joint_obs = torch.zeros(2, 4, dtype=torch.float32)
    team_vector = torch.zeros(1, 1, dtype=torch.float32)
    previous_skills = torch.tensor(previous_roster, dtype=torch.long)
    previous_ages = torch.full((2,), 5, dtype=torch.long)
    previous_active = torch.ones(2, dtype=torch.bool)
    agent_order = torch.arange(2, dtype=torch.long)
    token_kind = torch.full((2,), SET_TOKEN, dtype=torch.long)
    values = []
    for roster in ROSTERS:
        token_logp, _ = policy.evaluate_sequence(
            joint_obs=joint_obs,
            compact=compact,
            team_vector=team_vector,
            prev_skills=previous_skills,
            prev_ages=previous_ages,
            prev_active=previous_active,
            agent_order=agent_order,
            token_kind=token_kind,
            set_skill=torch.tensor(roster, dtype=torch.long),
        )
        values.append(token_logp.sum())
    return torch.stack(values)


def objective(policy: FixedClockAREditPolicy) -> torch.Tensor:
    losses = []
    for previous_roster in PREVIOUS_ROSTERS:
        for slow_sign, fast_sign in TARGET_SIGNS:
            log_probabilities = roster_log_probabilities(
                policy,
                slow_sign=slow_sign,
                fast_sign=fast_sign,
                previous_roster=previous_roster,
            )
            correct = correct_rosters(slow_sign, fast_sign)
            indices = torch.tensor(
                [ROSTERS.index(roster) for roster in correct], dtype=torch.long
            )
            losses.append(-torch.logsumexp(log_probabilities[indices], dim=0))
    return torch.stack(losses).mean()


@torch.no_grad()
def summarize(policy: FixedClockAREditPolicy) -> dict[str, object]:
    rows: dict[str, object] = {}
    masses = []
    normalization_errors = []
    for previous_roster in PREVIOUS_ROSTERS:
        for slow_sign, fast_sign in TARGET_SIGNS:
            log_probabilities = roster_log_probabilities(
                policy,
                slow_sign=slow_sign,
                fast_sign=fast_sign,
                previous_roster=previous_roster,
            )
            probabilities = torch.exp(log_probabilities)
            correct = correct_rosters(slow_sign, fast_sign)
            indices = torch.tensor(
                [ROSTERS.index(roster) for roster in correct], dtype=torch.long
            )
            mass = float(probabilities[indices].sum().item())
            masses.append(mass)
            normalization_errors.append(abs(float(probabilities.sum().item()) - 1.0))
            best = int(torch.argmax(probabilities).item())
            key = (
                f"prev_{previous_roster[0]}{previous_roster[1]}_"
                f"slow_{slow_sign:+d}_fast_{fast_sign:+d}"
            )
            rows[key] = {
                "correct_unordered_pair_mass": mass,
                "argmax_roster": list(ROSTERS[best]),
                "argmax_probability": float(probabilities[best].item()),
            }
    return {
        "contexts": rows,
        "correct_mass_min": float(min(masses)),
        "correct_mass_mean": float(np.mean(masses)),
        "probability_sum_max_error": float(max(normalization_errors)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=39041)
    parser.add_argument("--optimizer-steps", type=int, default=2000)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    args = parser.parse_args()
    if args.optimizer_steps <= 0 or args.learning_rate <= 0.0:
        raise ValueError("optimizer steps and learning rate must be positive")

    torch.set_num_threads(1)
    torch.manual_seed(args.seed)
    policy = FixedClockAREditPolicy(
        obs_dim=4,
        n_agents=2,
        n_skills=4,
        hidden_dim=32,
        compact_dim=8,
        team_code_dim=1,
        keep_init=0.6,
        age_reference_steps=40,
        force_refresh_every_check=True,
        native_categorical_edit=True,
    )
    parameter_count = int(sum(parameter.numel() for parameter in policy.parameters()))
    initial = summarize(policy)
    optimizer = torch.optim.Adam(policy.parameters(), lr=args.learning_rate)

    optimizer.zero_grad()
    initial_loss = objective(policy)
    initial_loss.backward()
    initial_grad_norm = float(
        np.sqrt(
            sum(
                float(torch.sum(parameter.grad.detach() ** 2).item())
                for parameter in policy.parameters()
                if parameter.grad is not None
            )
        )
    )
    for _ in range(args.optimizer_steps):
        optimizer.zero_grad()
        loss = objective(policy)
        loss.backward()
        optimizer.step()

    final = summarize(policy)
    final_loss = float(objective(policy).detach().item())
    implementation_valid = bool(
        parameter_count == 2512
        and initial_grad_norm > 1e-8
        and initial["probability_sum_max_error"] <= 1e-6
        and final["probability_sum_max_error"] <= 1e-6
        and np.isfinite(final_loss)
    )
    factorization_passed = bool(
        implementation_valid and final["correct_mass_min"] >= 0.90
    )
    status = (
        "INVALID_R39_JOINT_FACTORIZATION_DIAGNOSTIC"
        if not implementation_valid
        else (
            "PASS_R39_JOINT_FACTORIZATION_CAPACITY"
            if factorization_passed
            else "FAIL_R39_JOINT_FACTORIZATION_CAPACITY"
        )
    )
    result = {
        "experiment_id": "EXP-20260715-r39-toy-joint-factorization",
        "status": status,
        "implementation_valid": implementation_valid,
        "factorization_passed": factorization_passed,
        "training_or_environment_steps": 0,
        "optimizer_steps": args.optimizer_steps,
        "learning_rate": args.learning_rate,
        "seed": args.seed,
        "model": {
            "hidden_dim": 32,
            "parameter_count": parameter_count,
            "native_categorical_edit": True,
            "force_refresh_every_check": True,
        },
        "diagnostic_boundary": {
            "oracle_labels_used_for_diagnostic_only": True,
            "external_or_intrinsic_reward_used": False,
            "environment_executed": False,
            "contexts": 8,
            "final_rosters_per_context": 16,
        },
        "initial_loss": float(initial_loss.detach().item()),
        "initial_grad_norm": initial_grad_norm,
        "final_loss": final_loss,
        "gate": {"minimum_correct_unordered_pair_mass": 0.90},
        "initial": initial,
        "final": final,
        "decision": {
            "next_action": (
                "localize sampled joint-credit variance; the factorization is expressive"
                if factorization_passed
                else "repair or replace the joint-roster factorization before further RL runs"
            )
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".json.tmp")
    payload = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    temporary.write_text(payload, encoding="utf-8")
    try:
        temporary.replace(args.output)
    except PermissionError:
        # Some managed Windows runs allow file creation but deny rename.
        args.output.write_text(payload, encoding="utf-8")
    print(args.output.resolve())


if __name__ == "__main__":
    main()

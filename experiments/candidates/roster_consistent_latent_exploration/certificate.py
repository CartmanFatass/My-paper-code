from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

import numpy as np

from .config import ARMS, EVAL_SIZES, REGISTERED, REVISION, SEEDS, TRAIN_SIZES
from .host import (
    evaluate_actions,
    relative_bins,
    roster_accepted,
    scripted_codebook_actions,
    scripted_collapse_actions,
)
from .models import Actor, Posterior, actor_inputs
from .resources import resource_proposal


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    evidence: object


def _sources() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(Path(__file__).parent.glob("*.py"))
    }


def build_certificate() -> dict[str, object]:
    """Deterministic hand-written fixtures only; no RCLE RNG is imported or called."""
    checks: list[Check] = []
    sources = _sources()
    syntax_errors: dict[str, str] = {}
    for name, source in sources.items():
        try:
            ast.parse(source, filename=name)
        except SyntaxError as error:
            syntax_errors[name] = str(error)
    checks.append(Check("isolated_package_syntax", not syntax_errors, syntax_errors))
    checks.append(Check(
        "frozen_registry",
        TRAIN_SIZES == (4, 8) and EVAL_SIZES == (4, 8, 12)
        and len(SEEDS) == 12
        and ARMS == ("RCLE", "COMMON-Z", "SHUFFLED-MI", "INDEPENDENT-ENTROPY")
        and REGISTERED.train_updates == 2000
        and REGISTERED.eval_campaigns_per_size == 2048,
        REGISTERED.manifest(),
    ))

    fixture_rows: dict[str, object] = {}
    host_ok = True
    for n in EVAL_SIZES:
        x = np.tile(np.asarray((0.1, 0.4, 0.6, 0.9), dtype=np.float64), n // 4)
        mu = 0.5
        bins = relative_bins(x, mu)
        accepted = roster_accepted(bins)
        codebook_values: list[int] = []
        collapse_values: list[int] = []
        rotations_seen: list[int] = []
        for lock in range(4):
            codebook_campaign = []
            collapse_campaign = []
            for z in range(4):
                a1, a2 = scripted_codebook_actions(bins, z)
                outcome = evaluate_actions(bins, a1, a2, lock)
                codebook_campaign.append(outcome.reward)
                if outcome.valid and outcome.winning_rotation is not None:
                    rotations_seen.append(outcome.winning_rotation)
                c1, c2 = scripted_collapse_actions(bins)
                collapse_campaign.append(evaluate_actions(bins, c1, c2, lock).reward)
            codebook_values.append(max(codebook_campaign))
            collapse_values.append(max(collapse_campaign))
        permutation = np.arange(n - 1, -1, -1, dtype=np.int64)
        a1, a2 = scripted_codebook_actions(bins, 3)
        original = evaluate_actions(bins, a1, a2, 3)
        moved = evaluate_actions(bins[permutation], a1[permutation], a2[permutation], 3)
        row_invariant = (
            original.valid == moved.valid
            and original.winning_rotation == moved.winning_rotation
            and original.reward == moved.reward
            and np.array_equal(original.fractions, moved.fractions)
        )
        fixed_route = np.zeros(n, dtype=np.int64)
        fixed = evaluate_actions(bins, fixed_route, fixed_route, 0)
        passed = bool(
            accepted and codebook_values == [1, 1, 1, 1]
            and sum(collapse_values) / 4.0 == 0.25
            and sorted(set(rotations_seen)) == [0, 1, 2, 3]
            and row_invariant and not fixed.valid
        )
        host_ok = host_ok and passed
        fixture_rows[str(n)] = {
            "accepted": accepted,
            "bins": bins.tolist(),
            "codebook_campaign_values": codebook_values,
            "collapse_campaign_values": collapse_values,
            "all_rotations_seen": sorted(set(rotations_seen)),
            "row_permutation_invariant": row_invariant,
            "constant_route_invalid": not fixed.valid,
        }
    checks.append(Check("deterministic_common_host_gate", host_ok, fixture_rows))

    actor = Actor()
    posterior = Posterior()
    fixture_x = np.asarray((0.1, 0.4, 0.6, 0.9), dtype=np.float64)
    phase1 = actor_inputs(fixture_x, 0.5, 2, 1)
    phase2 = actor_inputs(fixture_x, 0.5, 2, 2, np.asarray((0, 1, 0, 1)))
    model_ok = (
        sum(parameter.numel() for parameter in actor.parameters()) == 1506
        and sum(parameter.numel() for parameter in posterior.parameters()) == 16
        and tuple(phase1.shape) == (4, 11)
        and tuple(phase2.shape) == (4, 11)
        and np.array_equal(phase1[:, 3:7].numpy(), np.tile((1.0, 0.0, 0.0, 0.0), (4, 1)))
        and np.array_equal(phase2[:, 3:7].numpy(), np.asarray(
            ((0.0, 1.0, 1.0, -1.0), (0.0, 1.0, 1.0, 1.0),
             (0.0, 1.0, 1.0, -1.0), (0.0, 1.0, 1.0, 1.0)),
        ))
    )
    checks.append(Check(
        "actor_posterior_shape_and_information_boundary",
        bool(model_ok),
        {"actor_parameters": 1506, "posterior_parameters": 16,
         "actor_input_columns": ["X_i", "mu_N", "X_i-mu_N", "phase_1", "phase_2",
                                 "previous_available", "signed_previous", "one_hot_Z[4]"]},
    ))

    authorization_source = sources["authorization.py"]
    stochastic_sources = "\n".join(sources[name] for name in (
        "rng.py", "host.py", "models.py", "training.py", "evaluation.py",
    ))
    checks.append(Check(
        "stochastic_paths_fail_closed",
        "ProductionPermit" in stochastic_sources
        and "require_active_permit" in stochastic_sources
        and "production_authorized" in authorization_source
        and "lease_token" in authorization_source
        and "authorized_seeds" in authorization_source,
        {"gate": "passing exact-r04 certificate plus Root direction lease"},
    ))
    training_source = sources["training.py"]
    inference_source = sources["inference.py"]
    checks.append(Check(
        "loss_update_and_inference_contract",
        all(token in training_source for token in (
            "REGISTERED.beta * rollout", "REGISTERED.alpha * rollout[\"route_entropy\"]",
            "actor_loss.backward()", "actor_optimizer.step()", "posterior_loss.backward()",
            "posterior_optimizer.step()", "baseline_decay", "shuffled_labels",
        )) and all(token in inference_source for token in (
            "1.0 - 0.05 / 3.0", "1.0 - 0.05 / 12.0", "df=11",
            "ORACLE_HEADROOM_WITH_ZERO_LEARNED_VALIDITY", "MECHANISM_SUPPORTED",
            "BOUNDED_PACKAGE_EFFECT_ONLY", "CONTRAST_SPECIFIC_RESULTS_ONLY",
        )),
        {"actor_then_posterior": True, "seed_df": 11, "literal_precedence": [0, 1, 2, 3, 4]},
    ))
    resources = resource_proposal()
    checks.append(Check(
        "literal_workload_and_resource_contract",
        resources["training_episodes"] == 3_072_000
        and resources["ordinary_evaluation_episodes"] == 1_179_648
        and resources["cut_episodes"] == 589_824
        and resources["total_registered_episodes"] <= REGISTERED.max_episodes
        and resources["requested_cpu_cores"] == 1
        and resources["requested_gpu_count"] == 0
        and resources["requested_peak_memory_mib"] == 2048
        and resources["registered_wall_minutes"] == 45,
        resources,
    ))
    return {
        "direction": "roster_consistent_latent_exploration",
        "revision": REVISION,
        "certificate_kind": "deterministic_handwritten_fixture_and_static_source_only",
        "registered_stochastic_object_materialized": False,
        "registered_seed_value_inspected": False,
        "source_sha256": {
            name: hashlib.sha256(source.encode("utf-8")).hexdigest()
            for name, source in sources.items()
        },
        "passed": all(check.passed for check in checks),
        "checks": [asdict(check) for check in checks],
    }


def write_certificate(path: Path) -> dict[str, object]:
    certificate = build_certificate()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(certificate, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return certificate

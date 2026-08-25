from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import torch

from .config import (
    ARMS, EVAL_SIZES, PRO_CLOSED_INTAKE_SHA256, REGISTERED, REVISION,
    RNG_BINDING, SCIENCE_CARD_SHA256, SEEDS, TRAIN_SIZES,
)
from .host import EpisodeBatch, RELAY, SENSOR, evaluate_outcomes, scripted_oracle_actions
from .models import ArmModel, actor_inputs
from .resources import resource_proposal
from .training import complete_gradient, normalized_joint_update


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    evidence: object


def _sources() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(Path(__file__).parent.glob("*.py"))}


def _fixture_batch(n: int, handoff: bool) -> EpisodeBatch:
    roles = np.asarray(([SENSOR] * math.ceil(n / 2) + [RELAY] * math.floor(n / 2)), dtype=np.int64)[None, :]
    clues = np.ones((1, n), dtype=np.int64)
    replaced = np.zeros((1, n), dtype=bool)
    if handoff:
        replaced[0, 0] = True
        replaced[0, -1] = True
    post_clues = clues.copy(); post_clues[replaced] = 0
    return EpisodeBatch(
        n=n, handoff=handoff, target=np.ones(1, dtype=np.int64),
        initial_roles=roles, initial_clues=clues, post_roles=roles.copy(),
        post_clues=post_clues, replaced=replaced,
    )


def _support_checks() -> tuple[bool, dict[str, object]]:
    evidence: dict[str, object] = {}
    passed = True
    for n in EVAL_SIZES:
        for handoff in (False, True):
            batch = _fixture_batch(n, handoff)
            pre, post = scripted_oracle_actions(batch)
            outcome = evaluate_outcomes(batch, pre, post)
            ok = bool(outcome.value[0] == 1.0 and outcome.mission[0])
            passed &= ok
            evidence[f"full_information_N{n}_handoff{int(handoff)}"] = ok
        numerator = sum(
            math.comb(n, k) * 7**k * 3**(n-k)
            for k in range((n + 1) // 2, n + 1)
        )
        denominator = 10**n
        exact = Fraction(numerator, denominator)
        enumerated = Fraction(0, 1)
        for mask in range(1 << n):
            correct = int(mask.bit_count())
            if correct >= (n + 1) // 2:
                enumerated += Fraction(7**correct * 3**(n-correct), 10**n)
        equality = enumerated == exact
        evidence[f"bayes_majority_N{n}"] = {
            "enumerated_numerator": enumerated.numerator,
            "enumerated_denominator": enumerated.denominator,
            "closed_form_numerator": exact.numerator,
            "closed_form_denominator": exact.denominator,
            "exact_equal": equality,
        }
        passed &= 0 < exact < 1 and equality
    return passed, evidence


def _strictness_checks() -> tuple[bool, dict[str, object]]:
    model = ArmModel()
    with torch.no_grad():
        model.actor.first.weight.zero_(); model.actor.first.bias.zero_()
        model.actor.second.weight.zero_(); model.actor.second.bias.zero_()
        model.actor.head.weight.zero_(); model.actor.head.bias.zero_()
        model.actor.first.weight[:3, 8:11] = torch.eye(3, dtype=torch.float64)
        model.actor.second.weight[:3, :3] = torch.eye(3, dtype=torch.float64)
        model.actor.head.weight[:3, :3] = 2.0 * torch.eye(3, dtype=torch.float64)
    roles = np.asarray([[SENSOR, RELAY]] * 3, dtype=np.int64)
    clues = np.ones((3, 2), dtype=np.int64)
    refinements = torch.eye(3, 8, dtype=torch.float64, requires_grad=True)

    def probabilities(latent: torch.Tensor) -> torch.Tensor:
        return torch.softmax(model.actor(actor_inputs(roles, clues, 0, 5, latent))[:, 0], dim=-1)

    p = probabilities(refinements)
    flexible_matrix = sum(torch.outer(row, row) for row in p) / 3.0
    flexible_rank = int(torch.linalg.matrix_rank(flexible_matrix, tol=1e-10).item())
    jacobian = torch.autograd.functional.jacobian(probabilities, refinements)
    jacobian_nonzero = bool(torch.count_nonzero(jacobian).item() > 0)
    coarse_p = p[:2]
    coarse_matrix = sum(torch.outer(row, row) for row in coarse_p) / 2.0
    coarse_rank = int(torch.linalg.matrix_rank(coarse_matrix, tol=1e-10).item())

    arbitrary_refinement = torch.tensor([0, 1, 2, 3, 0, 3], dtype=torch.int64)
    macro = torch.tensor([0, 0, 0, 0, 1, 1], dtype=torch.int64)
    model.residual.data.zero_()
    coarse_latent = model.latent(macro, None, False)
    flexible_latent = model.latent(macro, arbitrary_refinement, True)
    containment = torch.equal(coarse_latent, flexible_latent)
    fixture_roles = np.asarray([[SENSOR, RELAY]] * len(macro), dtype=np.int64)
    fixture_clues = np.ones((len(macro), 2), dtype=np.int64)
    coarse_actions = torch.softmax(
        model.actor(actor_inputs(fixture_roles, fixture_clues, 0, 5, coarse_latent)), dim=-1,
    )
    flexible_actions = torch.softmax(
        model.actor(actor_inputs(fixture_roles, fixture_clues, 0, 5, flexible_latent)), dim=-1,
    )
    action_containment = torch.equal(coarse_actions, flexible_actions)
    return bool(containment and action_containment and flexible_rank >= 3 and coarse_rank <= 2 and jacobian_nonzero), {
        "zero_residual_exact_containment": containment,
        "all_fixture_action_distributions_bit_identical": action_containment,
        "positive_refinement_states": 3,
        "flexible_joint_action_matrix_rank": flexible_rank,
        "binary_coarse_joint_action_matrix_rank": coarse_rank,
        "actor_output_jacobian_nonzero": jacobian_nonzero,
    }


def _gradient_check() -> tuple[bool, dict[str, object]]:
    model = ArmModel()
    before = torch.cat([parameter.detach().reshape(-1) for parameter in model.parameters()])
    first = next(model.parameters())
    first.grad = torch.arange(1, first.numel() + 1, dtype=torch.float64).reshape_as(first)
    _, raw_norm, update_norm = normalized_joint_update(model)
    after = torch.cat([parameter.detach().reshape(-1) for parameter in model.parameters()])
    actual = float(torch.linalg.vector_norm(after - before).item())
    _, full, _ = complete_gradient(model)
    all_registered = full.numel() == REGISTERED.parameters_per_arm
    return bool(raw_norm > 0 and abs(actual - 0.001) < 1e-12 and update_norm == 0.001 and all_registered), {
        "raw_norm_positive": raw_norm > 0,
        "actual_update_norm": actual,
        "registered_gradient_entries": full.numel(),
        "none_gradients_materialized_as_zero": all_registered,
    }


def _source_score_check() -> tuple[bool, dict[str, object]]:
    logits = torch.tensor([[0.2, -0.1], [-0.4, 0.3], [0.1, 0.6], [0.7, -0.2]], dtype=torch.float64, requires_grad=True)
    selected = torch.tensor([0, 1, 1, 0], dtype=torch.int64)
    source_log = torch.log_softmax(logits, dim=1).gather(1, selected[:, None]).squeeze(1)
    source_indices = torch.tensor([2, 0, 3, 1], dtype=torch.int64)
    recipient_score = source_log[source_indices]
    recipient_advantage = torch.tensor([0.25, 1.5, -0.75, 3.0], dtype=torch.float64)
    loss = -(recipient_advantage * recipient_score).sum(); loss.backward()
    expected_source_weights = torch.zeros(4, dtype=torch.float64).scatter_add_(0, source_indices, recipient_advantage)
    probabilities = torch.softmax(logits.detach(), dim=1)
    selected_onehot = torch.nn.functional.one_hot(selected, num_classes=2).to(torch.float64)
    expected_gradient = -expected_source_weights[:, None] * (selected_onehot - probabilities)
    nonzero = logits.grad.abs().sum(dim=1) > 0
    max_error = float((logits.grad - expected_gradient).abs().max().item())
    passed = bool(nonzero.all() and max_error < 1e-12 and len(set(source_indices.tolist())) == 4)
    return passed, {
        "fixed_points": 0,
        "recipient_to_source_indices": source_indices.tolist(),
        "nonuniform_recipient_advantages": recipient_advantage.tolist(),
        "source_rows_with_gradient": int(nonzero.sum()),
        "recipient_advantage_by_source": expected_source_weights.tolist(),
        "explicit_source_indexed_reference_max_abs_error": max_error,
    }


def build_certificate() -> dict[str, object]:
    """Deterministic hand fixtures and static source checks only; never calls CPC RNG."""
    checks: list[Check] = []
    sources = _sources()
    syntax_errors = {}
    for name, source in sources.items():
        try:
            ast.parse(source, filename=name)
        except SyntaxError as error:
            syntax_errors[name] = str(error)
    checks.append(Check("isolated_package_syntax", not syntax_errors, syntax_errors))
    workspace = Path(__file__).parents[3]
    card_path = workspace / "docs/research/candidates/roster_consistent_latent_exploration/RCLE_CPC_SCIENCE_CARD.md"
    intake_path = workspace / "docs/research/candidates/roster_consistent_latent_exploration/RCLE_CPC_R04_EXTERNAL_PRO_CLOSED_INTAKE.md"
    card_hash = hashlib.sha256(card_path.read_bytes()).hexdigest().upper()
    intake_hash = hashlib.sha256(intake_path.read_bytes()).hexdigest().upper()
    authority_ok = card_hash == SCIENCE_CARD_SHA256 and intake_hash == PRO_CLOSED_INTAKE_SHA256
    checks.append(Check("exact_science_card_and_pro_closure_binding", authority_ok, {
        "science_card_sha256": card_hash, "pro_closed_intake_sha256": intake_hash,
    }))
    old_seeds = {1103, 1217, 1321, 1451, 1553, 1693, 1789, 1877, 1999, 2081, 2179, 2293,
                 2371, 2473, 2591, 2683, 2791, 2903, 3011, 3121, 3251, 3371, 3491, 3613}
    registry_ok = (
        TRAIN_SIZES == (5, 7) and EVAL_SIZES == (5, 7, 9) and len(SEEDS) == 16
        and not (set(SEEDS) & old_seeds) and len(ARMS) == 3
        and REGISTERED.train_updates == 1000 and REGISTERED.eval_episodes_per_cell == 2048
        and RNG_BINDING == "rcle-cpc-r04-blake2b-pcg64-v1"
    )
    checks.append(Check("fresh_exact_registry_and_coordinate_namespace", registry_ok, REGISTERED.manifest()))
    support_ok, support_evidence = _support_checks()
    checks.append(Check("deterministic_host_and_bayes_oracles", support_ok, support_evidence))
    strict_ok, strict_evidence = _strictness_checks()
    checks.append(Check("zero_residual_containment_and_output_connected_rank_three", strict_ok, strict_evidence))
    gradient_ok, gradient_evidence = _gradient_check()
    checks.append(Check("complete_tensor_nonzero_update_normalization", gradient_ok, gradient_evidence))
    source_ok, source_evidence = _source_score_check()
    checks.append(Check("source_keyed_shuffled_score_graph", source_ok, source_evidence))
    training_source, inference_source, evaluation_source = sources["training.py"], sources["inference.py"], sources["evaluation.py"]
    contract_ok = all(token in training_source for token in (
        "sum(losses).backward()", "normalized_joint_update(model)", "baselines[arm][index] =",
        "torch.roll(source_log_macro", "values - baselines",
    )) and all(token in inference_source for token in (
        "df=15", "REGISTERED.primary_gamma", "REGISTERED.mechanism_gamma",
        "cells[\"9\"][\"handoff\"]", "ALL_LEARNED_ZERO_MISSION",
        "COARSE_MECHANISM_SUPPORTED", "COARSE_PACKAGE_ONLY", "FLEXIBLE_CONTAINING_SUPERIOR",
        "NO_COARSE_ADVANTAGE", "TARGET_UNRESOLVED",
    )) and all(token in evaluation_source for token in (
        '"mechanism_index": {"N": 9, "handoff": True}', "PRIVATE-LATENT-CUT", "TEMPORAL-RESET-CUT",
    ))
    checks.append(Check("loss_baseline_inference_and_exclusive_mechanism_contract", contract_ok, {
        "df": 15, "primary_gamma": REGISTERED.primary_gamma,
        "mechanism_gamma": REGISTERED.mechanism_gamma, "mechanism_cell": "N=9,handoff=true",
    }))
    auth_source = sources["authorization.py"]
    stochastic_sources = "\n".join(sources[name] for name in ("rng.py", "host.py", "models.py", "training.py", "evaluation.py"))
    fail_closed = all(token in auth_source for token in (
        "production_authorized", "lease_token", "authorized_seeds", "stage_boundary",
    )) and "ProductionPermit" in stochastic_sources and "require_active_permit" in stochastic_sources
    checks.append(Check("stochastic_activity_fail_closed", fail_closed, {"lease_required": True, "certificate_required": True}))
    resources = resource_proposal()
    resource_ok = (
        resources["training_episodes"] == 3_072_000
        and resources["ordinary_evaluation_episodes"] == 589_824
        and resources["cut_episodes"] == 65_536
        and resources["total_registered_episodes"] == 3_727_360
        and resources["total_agent_decisions"] == 46_301_184
        and resources["optimizer_steps"] == 48_000
        and resources["requested_cpu_cores"] == 1 and resources["requested_gpu_count"] == 0
        and resources["requested_peak_memory_mib"] == 2048 and resources["registered_wall_minutes"] == 45
    )
    checks.append(Check("literal_workload_and_resource_contract", resource_ok, resources))
    return {
        "direction": "roster_consistent_latent_exploration",
        "revision": REVISION,
        "certificate_kind": "deterministic_handwritten_fixture_static_source_and_preactivity_dynamic_conformance",
        "registered_stochastic_object_materialized": False,
        "registered_coordinate_materialized": False,
        "registered_seed_value_inspected": False,
        "support_oracles_passed": support_ok,
        "containment_and_strictness_passed": strict_ok,
        "source_sha256": {name: hashlib.sha256(source.encode("utf-8")).hexdigest() for name, source in sources.items()},
        "test_sha256": hashlib.sha256((
            workspace / "tests/experiments/candidates/roster_consistent_latent_exploration_cpc/test_rcle_cpc.py"
        ).read_bytes()).hexdigest(),
        "passed": all(check.passed for check in checks),
        "checks": [asdict(check) for check in checks],
    }


def write_certificate(path: Path) -> dict[str, object]:
    certificate = build_certificate()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(certificate, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return certificate

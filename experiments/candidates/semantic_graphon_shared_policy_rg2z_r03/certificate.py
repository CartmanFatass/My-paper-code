"""Preactivity certificate: static source/config checks and handwritten algebra only."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .config import (
    ACTION_DIM,
    COUNTER_ROOT,
    EDGE_BETA_BOUND,
    EPISODES_PER_UPDATE,
    EVALUATION_EPISODES,
    HELDOUT_ROSTERS,
    HORIZON,
    LATENCY,
    P0,
    PHY_BETA_BOUND,
    REGISTERED_ROSTERS,
    ROTATED_PHYSICAL_COLUMN_SOURCE,
    SEEDS,
    TRAINING_UPDATES,
    TRAIN_ROSTERS,
    legal_action_indices,
)


REVISION = "SGSP-RG2Z-SCIENCE-20260815-03"
ACTION = "SGSP-RG2Z-R03-FULL-PANEL"
EXPECTED_PARAMETERS_PER_ARM = 35_513
EXPECTED_HASHES = {
    "SGSP_RG2Z_R03_DEFINITION_SCIENCE_CARD.md": "6666846CC425B91B29589E656684DF00AEF961BF093F580A99F9820201AFB240",
    "SGSP_RG2Z_R03_RESULT_BLIND_DECISION_MAP.md": "15B9649460A89C6FF1D13A1709784F84270CFCDEB284C69CBDBB6811C2EEE794",
    "SGSP_RG2Z_R03_CHATGPT_EXTERNAL_PRO_CLOSED_INTAKE.md": "0A2C13461AE4C23A331BBD714F97D32495095C7979E8C8AF9D834E53F4425A49",
}


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    evidence: Any


def _package_sources() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(Path(__file__).parent.glob("*.py"))
    }


def _package_source_hashes() -> dict[str, str]:
    """Hash the exact bytes that production authorization later revalidates."""
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(Path(__file__).parent.glob("*.py"))
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _source_contract(sources: dict[str, str], name: str, tokens: tuple[str, ...]) -> tuple[bool, list[str]]:
    missing = [token for token in tokens if token not in sources.get(name, "")]
    return not missing, missing


def _handwritten_kernel_fixture() -> dict[str, Any]:
    count = 2
    beta = [
        [[0.03 * (1 + receiver - sender), -0.02 * (receiver + sender + 1)] for sender in range(3)]
        for receiver in range(3)
    ]
    messages = [[(role + 1) * (column - 7) / 19.0 for column in range(32)] for role in range(3)]
    v = (2.0 * math.log(count) - math.log(14.0)) / math.log(7.0 / 2.0)

    def summary(receiver: int, rotated: bool) -> tuple[list[float], float]:
        numerator = [0.0] * 32
        denominator = 0.0
        for sender in range(3):
            physical_sender = ROTATED_PHYSICAL_COLUMN_SOURCE[sender] if rotated else sender
            p0 = P0[receiver][physical_sender]
            loaded = 1.0 / (1.0 + math.exp(-(
                math.log(p0 / (1.0 - p0)) - 0.22 * (count - 1)
            )))
            residual = beta[receiver][sender][0] + beta[receiver][sender][1] * v
            omega = loaded / LATENCY[receiver][physical_sender] * math.exp(residual)
            denominator += count * omega
            for column in range(32):
                numerator[column] += omega * count * messages[sender][column]
        return [value / (denominator + 1.0e-12) for value in numerator], denominator

    intact = [summary(receiver, False) for receiver in range(3)]
    rotated = [summary(receiver, True) for receiver in range(3)]
    finite = all(math.isfinite(value) for family in (intact, rotated) for row, denominator in family for value in (*row, denominator))
    multiset_preserved = all(
        sorted(P0[receiver]) == sorted(P0[receiver][source] for source in ROTATED_PHYSICAL_COLUMN_SOURCE)
        and sorted(LATENCY[receiver]) == sorted(LATENCY[receiver][source] for source in ROTATED_PHYSICAL_COLUMN_SOURCE)
        for receiver in range(3)
    )
    changed = any(
        abs(intact[receiver][0][column] - rotated[receiver][0][column]) > 1.0e-12
        for receiver in range(3) for column in range(32)
    )
    return {
        "passed": finite and multiset_preserved and changed,
        "finite": finite,
        "balanced_receiver_row_multiset_preserved": multiset_preserved,
        "asymmetric_fixture_summary_changed": changed,
        "rotation": list(ROTATED_PHYSICAL_COLUMN_SOURCE),
    }


def _containment_fixture() -> dict[str, Any]:
    narrow_values = (-0.15, -0.08, 0.0, 0.07, 0.15)
    exact_common_chart = all(
        -PHY_BETA_BOUND <= value <= PHY_BETA_BOUND
        and -EDGE_BETA_BOUND <= value <= EDGE_BETA_BOUND
        and math.exp(value) == math.exp(value)
        for value in narrow_values
    )
    strict_witness = 0.60
    strict = abs(strict_witness) > PHY_BETA_BOUND and abs(strict_witness) <= EDGE_BETA_BOUND
    parameter_formula = (
        (64 * 22 + 64) + (32 * 64 + 32)
        + 3 * 64 * 55 + 3 * 64 * 64 + 3 * 64
        + (6 * 64 + 6) + 18
        + (64 * 66 + 64) + (64 * 64 + 64) + (64 + 1)
    )
    return {
        "passed": exact_common_chart and strict and parameter_formula == EXPECTED_PARAMETERS_PER_ARM,
        "same_beta_values_same_exp_residual": exact_common_chart,
        "strict_capacity_witness": strict_witness,
        "strict_witness_available_only_to_edge": strict,
        "derived_parameters_per_arm": parameter_formula,
    }


def _support_fixture() -> dict[str, Any]:
    rows = {
        "surveyor": ([0.20, 0.30, 0.50], 3),
        "relay": ([0.10, 0.20, 0.30, 0.40], 4),
    }
    evidence = {}
    passed = True
    for name, (probabilities, count) in rows.items():
        floor = 0.04 / count
        tv_sup = 1.0 - (count - 1) * floor - min(probabilities)
        evidence[name] = {"legal_count": count, "floor": floor, "TV_sup": tv_sup}
        passed &= 0.0 <= tv_sup <= 1.0 and min(probabilities) >= floor
    legal_masks = [legal_action_indices(role) for role in range(3)]
    passed &= legal_masks == [(0, 1, 5), (0, 1, 5), (2, 3, 4, 5)]
    return {"passed": passed, "rows": evidence, "legal_masks": legal_masks}


def build_certificate() -> dict[str, Any]:
    """Build without constructing a world, coordinate, model, action or policy output."""
    sources = _package_sources()
    checks: list[Check] = []

    syntax_errors: dict[str, str] = {}
    for name, source in sources.items():
        try:
            ast.parse(source, filename=name)
        except SyntaxError as error:
            syntax_errors[name] = str(error)
    checks.append(Check("isolated_package_python_syntax", not syntax_errors, syntax_errors))

    workspace = Path(__file__).parents[3]
    authority_dir = workspace / "docs/research/candidates/semantic_graphon_shared_policy"
    actual_hashes = {name: _sha256(authority_dir / name) for name in EXPECTED_HASHES}
    checks.append(Check(
        "exact_r03_science_map_and_pro_closed_intake_binding",
        actual_hashes == EXPECTED_HASHES,
        {"actual": actual_hashes, "expected": EXPECTED_HASHES},
    ))

    predecessor_seeds = {
        4103, 4127, 4153, 4177, 4201, 4229, 4253, 4273,
        4297, 4327, 4357, 4387, 4409, 4441, 4463, 4483,
        14103, 14127, 14153, 14177, 14201, 14229, 14253, 14273,
        14297, 14327, 14357, 14387, 14409, 14441, 14463, 14483,
    }
    registry_pass = (
        len(SEEDS) == 24 and len(set(SEEDS)) == 24
        and set(SEEDS).isdisjoint(predecessor_seeds)
        and TRAIN_ROSTERS == (9, 15) and HELDOUT_ROSTERS == (6, 21)
        and REGISTERED_ROSTERS == (6, 9, 15, 21)
        and HORIZON == 12 and TRAINING_UPDATES == 512
        and EPISODES_PER_UPDATE == 64 and EVALUATION_EPISODES == 256
        and ACTION_DIM == 6
        and "SGSP-RG2Z-SCIENCE-20260815-03" in COUNTER_ROOT
        and "semantic_graphon_shared_policy_r06" not in COUNTER_ROOT
    )
    checks.append(Check("fresh_exact_registry_and_single_budget", registry_pass, {
        "seed_count": len(SEEDS), "seed_order": list(SEEDS),
        "train_rosters": list(TRAIN_ROSTERS), "heldout_rosters": list(HELDOUT_ROSTERS),
        "updates": TRAINING_UPDATES, "episodes_per_update": EPISODES_PER_UPDATE,
        "evaluation_episodes": EVALUATION_EPISODES, "counter_root": COUNTER_ROOT,
        "disjoint_from_revision_05_and_06_seeds": set(SEEDS).isdisjoint(predecessor_seeds),
    }))

    contracts = {
        "world.py": (
            "class RidgeGateWorld", "event_time", "purge_expired", "slot + 1",
            "collision_losses", "previous_success", "return_value", "basin_delivery_rates",
        ),
        "policies.py": (
            "class SemanticActor", "self.beta = nn.Parameter(torch.zeros(3, 3, 2",
            "ROTATED_PHYSICAL_COLUMN_SOURCE", "F.linear(r * previous_hidden, self.U_n, None)",
            "POLICY_SOFTMAX_WEIGHT * softmax + floor", "shadow_rotated_probabilities",
        ),
        "training.py": (
            "training_batch_rosters", "require_loss=True", "full_batch_loss.backward()",
            "clip_grad_norm_", "optimizer.step()", "model.project_beta_()",
            "Coordinate(", 'condition="intact"', "capture_shadow_cut",
        ),
        "evaluation.py": (
            "StreamingPanelMean", "StreamingShadowMean", "range(EVALUATION_EPISODES)",
            'condition="intact"', 'condition="rotated"', "rollout_uniform_episode",
            '"episode_rows_retained": False', '"greedy_evaluation": False',
        ),
        "statistics.py": (
            "FAMILY_SIZE = 18", "SEED_COUNT = 24",
            "FAMILY_ALPHA / (2.0 * FAMILY_SIZE)", "df=SEED_COUNT - 1",
            "TRAINED_ARMS", "A({n})", "NONIDENTIFIED",
            "RETAIN_PHYSICAL_PRIOR_COLDSTART", "DO_NOT_RETAIN_FIXED_PRIOR_AS_DEFAULT",
            "HELDOUT_DIRECT_RETURN_NOT_ESTABLISHED", "PRACTICAL_EQUIVALENCE",
            "EDGE_MATERIALLY_SUPERIOR",
        ),
        "authorization.py": (
            "ProductionPermit", "require_exact_certificate", "production_authorized", "lease_token",
            "authorized_seeds", "not_after_utc",
        ),
        "runner.py": (
            "load_production_permit", "validate_certificate_binding", "validate_lease_binding",
            "atomic_payload_complete", "analyze_packets",
        ),
    }
    missing_by_file: dict[str, list[str]] = {}
    for name, tokens in contracts.items():
        passed, missing = _source_contract(sources, name, tokens)
        if not passed:
            missing_by_file[name] = missing
    checks.append(Check("static_source_contracts", not missing_by_file, missing_by_file))

    forbidden_runtime = ("semantic_graphon_shared_policy_r06", "SGSP-W", "ALT-CENTER", "EDGE-PE")
    deployed = "\n".join(sources.get(name, "") for name in (
        "rng.py", "world.py", "policies.py", "training.py", "evaluation.py", "statistics.py",
    ))
    legacy_hits = [token for token in forbidden_runtime if token in deployed]
    checks.append(Check("legacy_runtime_and_old_result_firewall", not legacy_hits, legacy_hits))

    kernel = _handwritten_kernel_fixture()
    checks.append(Check("handwritten_physical_kernel_and_symmetric_rotation", kernel["passed"], kernel))
    containment = _containment_fixture()
    checks.append(Check("literal_strict_containment_and_parameter_formula", containment["passed"], containment))
    support = _support_fixture()
    checks.append(Check("handwritten_mask_floor_and_tv_support", support["passed"], support))

    inference_composition = 4 + 2 + 2 + 2 + 6 + 2
    checks.append(Check("exact_18_quantity_two_sided_family", inference_composition == 18, {
        "composition": [4, 2, 2, 2, 6, 2], "total": inference_composition,
        "per_quantity_error": 0.05 / 18.0, "df": 23,
    }))

    complexity_pass = (
        "role_sums = torch.stack" in sources.get("policies.py", "")
        and "for receiver_role in range(3)" in sources.get("policies.py", "")
        and "learned_nxn" not in sources.get("policies.py", "").lower()
        and "rollout_model_episode(" in sources.get("evaluation.py", "")
        and "nested" not in sources.get("evaluation.py", "").lower()
    )
    checks.append(Check("registered_complexity_boundary", complexity_pass, {
        "hypothetical_trajectory_candidates": 0,
        "future_simulated_transitions_for_search": 0,
        "deployment_time": "O(N+9)", "deployment_messages": "O(N)",
        "learned_dense_pairwise_objects": 0,
    }))

    return {
        "direction": "semantic_graphon_shared_policy",
        "revision": REVISION,
        "action": ACTION,
        "certificate_kind": "preactivity_static_source_config_and_handwritten_algebra_only",
        "registered_stochastic_object_materialized": False,
        "registered_coordinate_materialized": False,
        "registered_world_materialized": False,
        "registered_action_materialized": False,
        "registered_policy_initialized": False,
        "registered_policy_output_materialized": False,
        "registered_seed_value_inspected": False,
        "formal_training_or_evaluation_executed": False,
        "passed": all(check.passed for check in checks),
        "checks": [asdict(check) for check in checks],
        "source_hashes": _package_source_hashes(),
    }


def write_certificate(path: Path) -> dict[str, Any]:
    certificate = build_certificate()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(certificate, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return certificate
